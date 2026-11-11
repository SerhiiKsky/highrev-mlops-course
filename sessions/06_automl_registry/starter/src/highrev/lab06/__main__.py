"""CLI for a disposable comparison, lifecycle decisions and final audit."""

import argparse
import json
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=["run", "register", "promote", "rollback", "predict", "audit"],
    )
    parser.add_argument("--config", required=True)
    parser.add_argument("--framework", choices=["baseline", "pycaret"])
    parser.add_argument("--version")
    parser.add_argument("--input")
    parser.add_argument("--result")
    parser.add_argument("--decision")
    args = parser.parse_args()
    config = json.loads(Path(args.config).read_text(encoding="utf-8-sig"))
    root = Path(config["output_dir"]).resolve()
    # Keep the registry commands independent of pandas and the data pipeline.
    import mlflow
    from mlflow.tracking import MlflowClient

    mlflow.set_tracking_uri(config["tracking_uri"])
    client = MlflowClient(tracking_uri=config["tracking_uri"])
    if args.command == "run":
        from .execution import prepare_bundle, run_comparison

        if root.exists():
            raise FileExistsError(f"Use a new output directory: {root}")
        result = run_comparison(prepare_bundle(config), config)
    elif args.command == "audit":
        from .audit import final_audit

        result = final_audit(config)
    elif args.command == "predict":
        from .execution import call_worker
        from .lifecycle import resolve_champion

        if not args.input or not args.result:
            parser.error("predict requires --input and --result")
        champion = resolve_champion(client, config["model_name"])
        if not champion:
            raise ValueError("No champion")
        result_path = Path(args.result).resolve()
        request = {
            "model_uri": champion["model_uri"],
            "tracking_uri": config["tracking_uri"],
            "input_csv": str(Path(args.input).resolve()),
            "result_path": str(result_path),
        }
        result = call_worker(
            config,
            "predict",
            request,
            str(result_path) + ".request.json",
            str(result_path) + ".log",
        )
    else:
        if (root / "test-consumed.json").exists():
            raise ValueError(
                "Final test consumed: lifecycle decisions are closed for this comparison"
            )
        if args.command in ("register", "promote"):
            from .lifecycle import promote, register_candidate

            if not args.framework:
                parser.error(f"{args.command} requires --framework")
            candidate = json.loads(
                (root / f"{args.framework}-result.json").read_text(encoding="utf-8")
            )
            if args.command == "register":
                result = {
                    "version": register_candidate(
                        candidate, client, config["model_name"]
                    )
                }
            else:
                if not args.decision:
                    parser.error("promote requires --decision")
                result = promote(
                    candidate,
                    client,
                    config["model_name"],
                    config["policy"],
                    args.decision,
                )
        else:
            from .lifecycle import rollback

            if not args.version or not args.decision:
                parser.error("rollback requires --version and --decision")
            result = rollback(client, config["model_name"], args.version, args.decision)
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
