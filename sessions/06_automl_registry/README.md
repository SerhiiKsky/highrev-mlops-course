# Lab 06 supplied assets

Start with the [student lesson](../06-automl-and-registry.md). Copy `starter/` to a new `lab06/` directory in your individual exercise project, as shown there. Do not overwrite an existing copy.

| Asset | Purpose | Student responsibility |
|---|---|---|
| `starter/lab06_worker/` | Train, package, reload and serve models in the isolated worker | Implement the two functions in `learning_tasks.py` |
| `starter/src/highrev/lab06/` | Fixed protocol, execution, registry, policy and final audit | Implement `gate_reasons` in `learning_tasks.py` |
| `starter/worker-env/` | Existing locked PyCaret and MLflow environment | Sync this environment separately from the project |
| `starter/new_config.sh` and `new_config.py` | Create a fresh local run configuration | Supply real paths/identities and review thresholds |
| `starter/tests/` | Learning-function behavior tests | Make them pass and add a boundary test |
| `Call_the_model_API.ipynb` | HTTP client for your running service | Run requests, interpret errors and verify the served version after restart |

The service is supplied plumbing. Read `serve.py` in order: request fields, startup loader, health route, prediction route, response. Explain why it loads a complete pipeline once rather than fitting per request. The notebook client requires only HTTP access and `requests`, not PyCaret.

Source `starter/shell_helpers.sh` from Bash to locate virtual-environment Python and read JSON fields. `new_config.sh` calls the small Python JSON writer using `PYTHON_BIN`; it refuses existing run directories.
