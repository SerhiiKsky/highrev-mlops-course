"""Deterministic, customer-disjoint membership for the Lab 06 comparison."""

import hashlib
import json

import numpy as np
import pandas as pd
from pandas.api.types import is_numeric_dtype
from sklearn.model_selection import StratifiedKFold, train_test_split

FEATURES = [
    "pages_visited",
    "age_first_order",
    "gender",
    "campaign",
    "ip_address_country",
    "browser",
    "os",
]
TARGET = "high_revenue"
MEMBERSHIP_COLUMNS = [
    "row_id",
    "source_customer_row",
    "customer_id",
    TARGET,
    "outer_partition",
    "inner_partition",
    "inner_cv_fold",
]


def _canonical(value):
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def protocol_digest(protocol):
    return hashlib.sha256(
        _canonical({k: v for k, v in protocol.items() if k != "protocol_id"})
    ).hexdigest()


def membership_bytes(membership):
    return (
        membership[MEMBERSHIP_COLUMNS]
        .to_csv(index=False, lineterminator="\n")
        .encode("utf-8")
    )


def make_bundle(labeled, config):
    if (
        not isinstance(labeled, pd.DataFrame)
        or not labeled.index.is_unique
        or labeled.index.hasnans
    ):
        raise ValueError("Source row index must be unique and non-null")
    if any(not isinstance(i, (int, np.integer)) or i < 0 for i in labeled.index):
        raise ValueError("Source row index must contain nonnegative CSV row ordinals")
    if not set(FEATURES + [TARGET, "customerID"]).issubset(labeled.columns):
        raise ValueError("Labeled data is missing required columns")
    if (
        labeled.customerID.isna().any()
        or labeled.customerID.astype(str).str.strip().eq("").any()
    ):
        raise ValueError("Customer IDs must be non-null and non-empty")
    if any(not is_numeric_dtype(labeled[c]) for c in FEATURES[:2]):
        raise ValueError("Numeric features must have numeric dtype")
    if labeled[TARGET].isna().any() or set(labeled[TARGET].unique()) != {0, 1}:
        raise ValueError("Target must contain both binary labels 0 and 1")
    ids = labeled.customerID.astype(str)
    if (
        ids.groupby(ids).size().empty
        or labeled.assign(_id=ids).groupby("_id")[TARGET].nunique().max() != 1
    ):
        raise ValueError("Customer has inconsistent labels")
    try:
        seed = config["seed"]
        provenance = config["provenance"]
        source_hash = provenance["raw_customers_sha256"]
        for key in (
            "git_commit",
            "data_hash",
            "raw_customers_sha256",
            "raw_orders_sha256",
            "original_lock_sha256",
        ):
            if not isinstance(provenance[key], str) or not provenance[key]:
                raise ValueError(f"Missing provenance: {key}")
        if len(source_hash) != 64 or any(
            c not in "0123456789abcdef" for c in source_hash
        ):
            raise ValueError("raw_customers_sha256 must be lowercase SHA256")
        preparation, comparison = config["preparation"], config["comparison"]
        _canonical(config)
    except (KeyError, TypeError) as exc:
        raise ValueError(f"Incomplete protocol configuration: {exc}") from exc
    rows = pd.DataFrame(
        {
            "row_id": [f"customers:{source_hash}:{i}" for i in labeled.index],
            "source_customer_row": labeled.index.to_numpy(),
            "customer_id": ids.to_numpy(),
            TARGET: labeled[TARGET].astype(int).to_numpy(),
        }
    )
    groups = (
        rows[["customer_id", TARGET]]
        .drop_duplicates()
        .sort_values("customer_id")
        .reset_index(drop=True)
    )

    def split(frame, size):
        return train_test_split(
            frame, test_size=size, stratify=frame[TARGET], random_state=seed
        )

    try:
        train, remainder = split(groups, 0.4)
        validation, test = split(remainder.sort_values("customer_id"), 0.5)
        fit, holdout = split(train.sort_values("customer_id"), 0.2)
        fit = fit.sort_values("customer_id").reset_index(drop=True)
        rows["outer_partition"] = ""
        rows["inner_partition"] = "not_applicable"
        rows["inner_cv_fold"] = -1
        for name, part in (
            ("train", train),
            ("validation", validation),
            ("test", test),
        ):
            rows.loc[rows.customer_id.isin(part.customer_id), "outer_partition"] = name
        for name, part in (("fit", fit), ("holdout", holdout)):
            rows.loc[rows.customer_id.isin(part.customer_id), "inner_partition"] = name
        cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=seed)
        for fold, (_, valid) in enumerate(cv.split(fit, fit[TARGET])):
            rows.loc[
                rows.customer_id.isin(fit.iloc[valid].customer_id), "inner_cv_fold"
            ] = fold
    except ValueError as exc:
        raise ValueError(
            f"Insufficient groups or class support for grouped splits: {exc}"
        ) from exc
    protocol = {
        "schema_version": 1,
        "features": FEATURES,
        "target": TARGET,
        "positive_label": 1,
        "seed": seed,
        "strategy": "stratified customer groups: 60/20/20, train 80/20, three inner folds",
        "metric": "roc_auc",
        "weighting": "row",
        "provenance": provenance,
        "preparation": preparation,
        "comparison": comparison,
        "membership_sha256": hashlib.sha256(membership_bytes(rows)).hexdigest(),
    }
    protocol["protocol_id"] = protocol_digest(protocol)
    data = labeled[FEATURES + [TARGET]].copy()
    data.index = rows.row_id
    bundle = {"protocol": protocol, "membership": rows}
    for name, mask in (
        ("fit", rows.inner_partition.eq("fit")),
        ("holdout", rows.inner_partition.eq("holdout")),
        ("validation", rows.outer_partition.eq("validation")),
        ("test", rows.outer_partition.eq("test")),
    ):
        bundle[name] = data.loc[mask.to_numpy()].copy()
    bundle["folds"] = (
        rows.loc[rows.inner_partition.eq("fit"), "inner_cv_fold"].astype(int).tolist()
    )
    validate_bundle(bundle)
    return bundle


def validate_bundle(bundle):
    try:
        p, m = bundle["protocol"], bundle["membership"]
        if (
            p["protocol_id"] != protocol_digest(p)
            or p["membership_sha256"] != hashlib.sha256(membership_bytes(m)).hexdigest()
        ):
            raise ValueError("Protocol or membership digest differs")
        if (
            m.empty
            or m.row_id.duplicated().any()
            or m.source_customer_row.duplicated().any()
            or m.customer_id.isna().any()
        ):
            raise ValueError("Membership row identity is invalid")
        if set(m.outer_partition) != {"train", "validation", "test"} or set(
            m[TARGET]
        ) != {0, 1}:
            raise ValueError("Incomplete outer partitions or labels")
        if (
            m.groupby("customer_id")[
                ["outer_partition", "inner_partition", "inner_cv_fold", TARGET]
            ]
            .nunique()
            .gt(1)
            .any()
            .any()
        ):
            raise ValueError(
                "A customer crosses partitions/folds or has inconsistent labels"
            )
        train = m.outer_partition.eq("train")
        if (
            not m.loc[train, "inner_partition"].isin(["fit", "holdout"]).all()
            or not m.loc[~train, "inner_partition"].eq("not_applicable").all()
        ):
            raise ValueError("Invalid inner partition")
        fit = m.inner_partition.eq("fit")
        if (
            set(m.loc[fit, "inner_cv_fold"]) != {0, 1, 2}
            or not m.loc[~fit, "inner_cv_fold"].eq(-1).all()
        ):
            raise ValueError("Invalid inner fold membership")
        for name, mask in (
            ("fit", fit),
            ("holdout", m.inner_partition.eq("holdout")),
            ("validation", m.outer_partition.eq("validation")),
            ("test", m.outer_partition.eq("test")),
        ):
            expected = m.loc[mask]
            frame = bundle[name]
            if (
                frame.index.tolist() != expected.row_id.tolist()
                or list(frame.columns) != FEATURES + [TARGET]
                or frame[TARGET].astype(int).tolist() != expected[TARGET].tolist()
                or set(frame[TARGET]) != {0, 1}
            ):
                raise ValueError(f"Invalid {name} membership, schema or class support")
        if bundle["folds"] != m.loc[fit, "inner_cv_fold"].tolist():
            raise ValueError("Fold order differs from fit rows")
        for fold in range(3):
            if set(m.loc[fit & m.inner_cv_fold.eq(fold), TARGET]) != {0, 1} or set(
                m.loc[fit & m.inner_cv_fold.ne(fold), TARGET]
            ) != {0, 1}:
                raise ValueError("CV fold lacks both classes")
    except (KeyError, TypeError, AttributeError) as exc:
        raise ValueError(f"Invalid protocol bundle: {exc}") from exc
