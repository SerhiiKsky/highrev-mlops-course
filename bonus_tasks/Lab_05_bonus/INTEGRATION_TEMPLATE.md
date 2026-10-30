# Pizza Panic integration worksheet

Complete four code/configuration tasks in a clone of your completed Session 05
project, then record your choices in the evidence template.

## Copy map

Starter paths are relative to this `student` folder; destinations are relative
to your bonus project's root. Create missing parent directories.

| Starter | Destination |
| --- | --- |
| `starter/src/highrev/pipelines/pizza_panic/` (all three files) | `src/highrev/pipelines/pizza_panic/` |
| `starter/src/highrev/pizza_run.py` | `src/highrev/pizza_run.py` |
| `starter/conf/pizza/catalog_pizza.yml` | `conf/pizza/catalog_pizza.yml` |
| `starter/conf/pizza/parameters_pizza.yml` | `conf/pizza/parameters_pizza.yml` |
| `starter/gitignore-snippet.txt` | Merge into `.gitignore` |

Keep your completed `track_run.py` and `tracking_support.py`. Do not copy the
unfinished Session 05 starter over your solutions.

Create the dedicated environment folder `conf/pizza/` and commit its files.
Kedro loads shared `conf/base/` configuration first, then overlays `conf/pizza/`
when you select `--env pizza`. Keep the existing HighRev base files unchanged.
Pizza uses distinct catalog and parameter names, so both sets can coexist.
The supplied tracking adapter explicitly selects `env="pizza"` and logs that
environment in MLflow. Use lowercase `pizza` consistently, including on Linux.

An environment selects configuration; it does not create a separate Git
repository, virtual environment, or data directory. Continue using the separate
bonus clone and the documented DVC paths.

## K1 — construct the graph

Fill `create_pipeline()` in `pipelines/pizza_panic/pipeline.py`, using `node`
and `Pipeline` as in Session 04. These are function contracts:

| Function | Python arguments, in order | Kedro output name(s) |
| --- | --- | --- |
| `prepare_features` | `orders`, `restaurants` | `pizza_features` |
| `split_data` | `features`, `settings` | `pizza_split` |
| `search_candidates` | `split`, `settings`, `selection` | `pizza_results`, `pizza_models` |

Catalog inputs: `pizza_orders`, `pizza_restaurants`.
Parameter inputs: `params:pizza_settings`, `params:pizza_selection`.

Connect each argument to the appropriate input. The final function returns a
tuple: declare both output names in the correct order. Give every node a unique
name. `pizza_features` and `pizza_split` are in-memory intermediates.

## K2 — complete the catalog and parameter wiring

Replace every `FILL_ME` in `catalog_pizza.yml`. Use the CSV/pickle dataset types
already present in your lesson catalog.

| Dataset | Object | Required path |
| --- | --- | --- |
| `pizza_orders` | DataFrame loaded from CSV | `data/01_raw/orders.csv` |
| `pizza_restaurants` | DataFrame loaded from CSV | `data/01_raw/restaurants.csv` |
| `pizza_results` | DataFrame saved as CSV without index | `data/08_reporting/pizza_comparison.csv` |
| `pizza_models` | Dictionary of fitted sklearn pipelines saved with pickle | `data/06_models/pizza_models.pickle` |

The parameter file is complete. Feed its mappings through `params:` inputs;
do not hard-code replacement values. The validation fraction is 0.25 of the
remaining 80%, giving 20% of the original dataset.

## K3 — register the pipeline

Edit your **existing** `src/highrev/pipeline_registry.py`:

1. Import the new pipeline factory under a distinct alias.
2. Add a `pizza_panic` entry that calls the factory.
3. Preserve the existing named pipelines and `__default__`.

Do not replace the registry with another project's example. Execute
`pizza_panic` explicitly: the old default graph still expects customer data.

## K4 — connect the tracking adapter

Complete `run_pizza_pipeline(session)` in `src/highrev/pizza_run.py`. Use the
session's `run` method and its `pipeline_name` keyword to select your registered
graph. This is the adapter's only missing step.

Do not call `search_candidates` directly, load raw CSVs in the adapter, or
launch a standalone script. Kedro must control the experiment execution. The
supplied adapter calls your completed Session 05 functions to log its outputs.

## Completion checks

- [ ] K1: three named nodes, connected inputs and correctly ordered outputs.
- [ ] K2: four real dataset entries; configuration passed through parameters.
- [ ] K3: `pizza_panic` registered alongside existing pipelines.
- [ ] K4: adapter executes the named graph through Kedro.
- [ ] No `FILL_ME` or `NotImplementedError` remains in the bonus implementation.
- [ ] `uv run --locked kedro run --env pizza --pipeline pizza_panic` saves 15 result rows
      and three fitted models for the default search.
- [ ] The tracked search records 15 children and the comparison artifacts.

If debugging changes your source, commit the fix and rerun the search before
recovery. The original and recovered candidate need the same commit.
