# AutoGluon 101 — notebook setup

Start with [01_autogluon_basics.ipynb](01_autogluon_basics.ipynb). This standalone, ungraded learning exercise uses scikit-learn's built-in toy breast-cancer dataset, not the HighRev customer data or a medical decision system. It uses AutoGluon Tabular **1.3.1**, matching the Lab 07 starter, with Python **3.11**. The quick path uses the starter's installed model dependencies; LightGBM and CatBoost are optional extras, not assumed to be installed. Students do their own work in a separate disposable directory; never create model files in the course checkout, instructor reference project, or a retained rehearsal.

## 1. Create a separate working directory

Use Git Bash. Replace both example paths with your real absolute paths. `$course` is the course checkout containing `sessions/07_autogluon/`; `$work` must be a **new** directory outside that checkout, the reference project and any existing exercise or rehearsal. The guard refuses an existing directory rather than overwriting it. If it stops, choose another `$work` path; do not delete previous work.

```bash
course='/d/4.Teaching/ASI/highrev-mlops-course'
work='/d/4.Teaching/ASI/lecture-07/autogluon-101-your-name'

test -f "$course/sessions/07_autogluon/01_autogluon_basics.ipynb" || { echo 'Notebook missing.' >&2; exit 1; }
test -f "$course/sessions/07_autogluon/AUTOGLUON_101_SETUP.md" || { echo 'Setup guide missing.' >&2; exit 1; }
test -f "$course/sessions/07_autogluon/starter/pyproject.toml" || { echo 'Manifest missing.' >&2; exit 1; }
test -f "$course/sessions/07_autogluon/starter/uv.lock" || { echo 'Lock missing.' >&2; exit 1; }
test ! -e "$work" || { echo 'Working directory exists; preserve it and choose another.' >&2; exit 1; }
mkdir -p "$(dirname "$work")" &&
mkdir "$work" &&
cp "$course/sessions/07_autogluon/01_autogluon_basics.ipynb" "$work/" &&
cp "$course/sessions/07_autogluon/AUTOGLUON_101_SETUP.md" "$work/" &&
cp "$course/sessions/07_autogluon/starter/pyproject.toml" "$work/" &&
cp "$course/sessions/07_autogluon/starter/uv.lock" "$work/" &&
cd "$work" || { echo 'Setup copy failed; preserve it and inspect the error.' >&2; exit 1; }
```

The guard's `exit 1` ends an interactive Bash session if it fires. Open another terminal, redefine both paths and choose a new destination. The supplied manifest and lock are **copies**; the Lab 07 project and its lock remain untouched.

## 2. Install into this copy only

Python 3.11 and `uv` are required. Installation needs network access or a suitable pre-populated cache and enough disk space for the model libraries and Jupyter. AutoGluon 1.3.1 [documents Windows installation](https://auto.gluon.ai/1.3.1/install.html) and recommends an Anaconda environment there; the separate Git Bash/uv route below has not yet been rehearsed on Windows. If using WSL, select Linux paths such as `/mnt/d/...` and create a separate Linux environment rather than sharing a Windows `.venv`. Do not assume newer AutoGluon releases have the same Python or dependency requirements.

```bash
cd "$work"
uv sync --locked --python 3.11 || { echo 'Locked sync failed; stop and inspect.' >&2; exit 1; }
uv export --locked --no-hashes --no-emit-project --output-file core-constraints.txt >/dev/null || { echo 'Lock export failed; stop and inspect.' >&2; exit 1; }
if [ -f .venv/Scripts/python.exe ]; then
  py="$work/.venv/Scripts/python.exe"
elif [ -x .venv/bin/python ]; then
  py="$work/.venv/bin/python"
else
  echo 'No interpreter in this working copy; inspect uv sync output.' >&2
  exit 1
fi
"$py" -c 'import sys; print(sys.executable); print(sys.version)' || { echo 'Interpreter check failed.' >&2; exit 1; }
```

The initial sync uses the copied Lab 07 lock. The export creates a constraints file in the disposable working copy to keep the Lab 07 packages constrained while adding notebook tooling. Next install the two **supplemental** pinned tools into this copy's `.venv` only:

```bash
cd "$work"
uv pip install --python "$py" --constraint core-constraints.txt \
  'jupyterlab==4.4.6' 'ipykernel==6.30.1' || { echo 'Jupyter install failed; stop and inspect.' >&2; exit 1; }
uv pip check --python "$py" || { echo 'Dependency check failed; stop and inspect.' >&2; exit 1; }
"$py" -c 'import sys, importlib.metadata as m; from autogluon.tabular import TabularPredictor; import sklearn; v=m.version("autogluon.tabular"); print("Python:",sys.executable); print("AutoGluon:",v); print("scikit-learn:",sklearn.__version__); assert v == "1.3.1"' || { echo 'Kernel readiness check failed.' >&2; exit 1; }
```

All three commands must succeed and show AutoGluon `1.3.1`. JupyterLab and ipykernel are pinned here, but their supplemental transitive dependencies are **not** in the Lab 07 lock; this is not a fully locked notebook environment. The extra install does not edit either lockfile. Continue with the copied interpreter directly: an automatic `uv run` or `uv sync` may remove the supplemental tools from the environment. If dependencies conflict or installation fails, retain the error and stop; do not edit the course lock, install into the reference environment, or silently switch versions. This exact fresh Windows installation and browser/kernel path have not yet been independently rehearsed.

## 3. Register a local kernel and start JupyterLab

The following registers the kernel **inside the working directory**, not in your global user Jupyter configuration. It selects the same interpreter used above. `cygpath -m` makes a Windows-native path for Git Bash; the fallback is for native Linux/macOS Bash. The first readiness command stops if a kernel with this name already exists in the local prefix so prior work is preserved.

```bash
cd "$work"
test ! -e jupyter-local/share/jupyter/kernels/lab07-autogluon101 || { echo 'Local kernel already exists; inspect and preserve it.' >&2; exit 1; }
if command -v cygpath >/dev/null 2>&1; then
  local_prefix=$(cygpath -m "$work/jupyter-local")
  native_work=$(cygpath -m "$work")
else
  local_prefix="$work/jupyter-local"
  native_work="$work"
fi
"$py" -m ipykernel install --prefix "$local_prefix" \
  --name lab07-autogluon101 --display-name 'Lab 07 AutoGluon 1.3.1' || { echo 'Kernel registration failed.' >&2; exit 1; }
export JUPYTER_PATH="$local_prefix/share/jupyter"
"$py" -m jupyter kernelspec list || { echo 'Kernel inspection failed.' >&2; exit 1; }
"$py" -m jupyter lab --no-browser --ServerApp.root_dir="$native_work"
```

Open the local URL printed by JupyterLab in your browser. It may contain a Jupyter token: **do not paste the URL into chat or commit it**. Open the copied notebook and select **Lab 07 AutoGluon 1.3.1** as its kernel. In the notebook, check `sys.executable` points to this working directory's `.venv` and `importlib.metadata.version('autogluon.tabular')` is `1.3.1` before training. A Jupyter browser connecting successfully alone does not prove the selected kernel uses that interpreter.

Keep the Jupyter terminal open while working. Stop the server using Ctrl+C and confirm shutdown if prompted. After reopening Git Bash, redefine `$work`, `cd "$work"`, restore `$py` using the platform check above, set `$local_prefix` and `JUPYTER_PATH` as above, and launch the final Jupyter command. Do **not** repeat kernel installation or initialization into an existing working copy without inspecting it.

## 4. Run and preserve results

Run the notebook cells in order. The notebook uses a new model directory for each attempt; retain previously created models and any errors. A model artifact must only be loaded from a trusted source because AutoGluon uses pickle; training and inference must use compatible package/Python versions. Preserve your own notes outside the team project. Notebook completion and the self-check are ungraded.

The notebook is a focused starting point, not the complete four-week specialization or a deployment. For the applied HighRev/Kedro → FastAPI → Docker → GitHub Actions → Render path, return to `sessions/07-autogluon-to-render.md` in your course checkout. Consult the version-matched [AutoGluon 1.3.1 installation](https://auto.gluon.ai/1.3.1/install.html), [Tabular quick start](https://auto.gluon.ai/1.3.1/tutorials/tabular/tabular-quick-start.html), and [predictor load](https://auto.gluon.ai/1.3.1/api/autogluon.tabular.TabularPredictor.load.html) documentation.
