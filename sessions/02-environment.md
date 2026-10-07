# Session 02: Reproducible Environment

**Incident.** "Works on Alice's laptop, fails on Bob's." This time the class supplies it.
Session 1 ended with everyone running `baseline.py` and recording the Python version, the
pandas and scikit-learn versions, and the three metrics. Put the records side by side: a
class told to install "any way that works" rarely agrees. Nobody did anything wrong.
`pip install pandas scikit-learn user-agents` means "whatever is newest today, for whichever
Python comes first on the PATH," so the same command builds a different environment on
another day or another machine. The script has carried the question since day one:
`COURSE NOTE (session 2): which versions?`

If every record in the room matches, the incident still stands. How could anyone prove next
month that 0.764 came from these versions? Nothing in the repository says.

**Goal.** By the end of the session the repository holds three new files, `pyproject.toml`,
`uv.lock`, and `.python-version`. A fresh clone rebuilds with one command and prints ROC AUC
0.764, accuracy 0.721, f1 0.302 along with the versions that produced them. `baseline.py` is
checked and formatted by a linter whose version is locked. And a machine nobody in the room
configured has been asked to do the same.

This is component 1 of [PROJECT.md](../PROJECT.md) and the first half of the rubric row
"Reproducibility of environment, data, and run."

## Before Class

Install uv and check it, in a new terminal:

```bash
uv --version          # 0.11 or newer; otherwise: uv self update
```

On Windows, install from PowerShell with
`powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"` or
`winget install --id=astral-sh.uv -e`, then open a new Git Bash window so `uv` is on the
PATH. On macOS and Linux, `curl -LsSf https://astral.sh/uv/install.sh | sh`.

Commit any loose session 1 work in `intro/`, and bring the session 1 homework record.

## Words For Today

| Term | Meaning in this course |
|---|---|
| Environment | An interpreter plus the exact set of installed package versions. Together they decide what `import` returns. `.venv/` is one environment on one machine. |
| Platform | The operating system and CPU. The lockfile gives the same *versions* on every platform; the downloaded *binaries* (wheels) differ. |
| Dependency | A package the project needs. **Direct** if declared in `pyproject.toml`, **transitive** if pulled in by another package. **Runtime** if the code needs it to run, **development** if only its authors need it. |
| `pyproject.toml` | The standard file for project metadata, dependencies, and tool settings. Written by people, read by tools. |
| `requires-python` | The Python range the project accepts. uv resolves the lockfile for every version in the range. |
| `.python-version` | One line telling uv which interpreter to use. `3.12` fixes the minor version, not the patch. |
| Bound | A range in `pyproject.toml`, such as `pandas>=3.0.6`. `uv add` writes a lower bound equal to today's choice, not an exact pin. |
| Pin | An exact version recorded in `uv.lock`, such as pandas 3.0.6. |
| Resolution | Finding one version of every package, direct and transitive, that satisfies every bound at once. |
| Lockfile (`uv.lock`) | The result of resolution: every package, its exact version, and its source, for every supported platform. Committed; never edited by hand. It does not pin the Python patch version or uv itself. |
| Sync | Making `.venv/` match the lockfile: installing what is missing, removing what is extra. |
| `--locked` | Fail if the lockfile no longer matches `pyproject.toml`. |
| `--frozen` | Install exactly what the lockfile says, without checking it against `pyproject.toml`. |
| Generated artifact | Anything a command produces from committed inputs: `.venv/`, `model.pickle`, caches. |
| Linter, formatter | A linter (`ruff check`) reports code that is likely wrong or inconsistent. A formatter (`ruff format`) rewrites layout and nothing else. |
| Workflow, runner | A workflow is a file in `.github/workflows/` listing commands; a runner is a fresh machine owned by GitHub that runs them on every push. |

## Why The Same Code Behaves Differently

Three things vary between Alice and Bob:

1. **The interpreter.** Python 3.11, 3.12, or 3.13.
2. **The packages, including the ones nobody asked for.** pandas brings numpy; scikit-learn
   brings scipy, joblib, and threadpoolctl. The starter's three requests become 14
   installed packages, and a `pip install` next month chooses different versions of all of
   them.
3. **The platform.** Some package versions ship no prebuilt wheel for some platforms. The
   lockfile is resolved for every platform at once, but only a second machine proves it
   installs there.

The sentence to remember: **bounds live in `pyproject.toml`, pins live in `uv.lock`.** A
bound lets the project accept fixes later; the lockfile makes today's choice exact.
Upgrading becomes a decision (`uv lock --upgrade`, commit, rerun) instead of an accident.

**Why not `pip freeze`.** A frozen list like session 1's records one machine's result,
Windows-only packages included. A uv lockfile is resolved for every platform the project
supports, so one file serves Windows laptops and a Linux runner. conda's `environment.yml`
and Poetry's `poetry.lock` solve the same problem; the idea transfers.

**Why `requires-python = ">=3.12,<3.13"`.** `uv init` writes `>=3.12`, and uv then resolves
for every future Python too. A conflict that exists only on some Python the project never
runs still blocks the lock, and uv's own hint says to limit the range. This project is an
application that runs on one interpreter, not a library that must support many, so the range
is one minor version wide.

## What Belongs In Git

One rule:

> **Commit what cannot be regenerated from committed inputs, or what a brief asks for as
> evidence. Ignore everything else.**

| Path | In Git? | Why |
|---|---|---|
| `pyproject.toml`, `uv.lock`, `.python-version` | yes | the inputs that rebuild the environment |
| `baseline.py` | yes | code |
| `data/01_raw/*.csv` | yes, **until session 5** | Git is the only place the data lives today. Do not add `data/01_raw` to `.gitignore`: a clone without the CSVs cannot run the baseline. |
| `.venv/`, `model.pickle` | no | rebuilt by `uv sync` and `uv run python baseline.py`; the starter already ignores both |
| `.ruff_cache/` | no | created by Ruff in Ex 5 |
| `.venv-automl/` and other scratch environments | no | see the PyCaret section |
| `intro/` evidence (`model.joblib`, the lock file, captured responses) | yes | session 1 asked for it: the rule's second clause |
| `sessions/`, `data/`, `checks/` | yes, owned by the course | arrive in weekly drops; leave them unchanged |
| `.gitattributes` | yes, owned by the course | keeps line endings LF on every OS; without it Git on Windows warns "LF will be replaced by CRLF" for every file |

**From this session on, `.gitignore` belongs to the student.** Each later brief that creates
a new generated artifact says what to add; course drops never edit it.

Today's clean clone works only because 3 MB of CSV sits in Git. Session 5 gives the data its
own version history with DVC, and the clean-clone proof will then need one more command.

The three new files sit at the repository root next to `baseline.py`. Nothing moves into
`src/` today; that is session 3.

## Code Quality Is Part Of The Environment

Two people format the same file differently, so every diff mixes real changes with
whitespace. Worse, a linter installed globally at different versions on different laptops
gives different findings on the same file. Ruff arrives today as part of the environment,
not as a gate:

- **Its version is locked.** `uv add --dev ruff` puts Ruff in the `dev` dependency group and
  `uv.lock` pins it. Every machine that syncs runs the same Ruff.
- **Its settings are committed.** `[tool.ruff]` in `pyproject.toml` replaces "the settings
  in my editor."
- **So its findings are reproducible.** Same version, same settings, same file: the same
  findings on the laptop, in a clone, and on Linux. Whether the code *should* pass every
  check is session 3's question.
- **Runtime and development dependencies are different things.** The baseline never needs
  Ruff. `uv sync --no-dev` removes it, and a service image installs only the runtime list.
  Session 1's image carried JupyterLab because one list mixed both; the `dev` group is the
  separation session 9 relies on.

Ruff runs on `baseline.py`. The configuration excludes `sessions/` (course-owned files) and
`intro/` (the graded session 1 record), so "fixing" either is never on the table.

### pyproject.toml At The End Of The Session

```toml
[project]
name = "highrev-mlops-course"
version = "0.1.0"
requires-python = ">=3.12,<3.13"
dependencies = [
    "pandas>=3.0.6",
    "scikit-learn>=1.9.1",
    "user-agents>=2.2.0",
]

[dependency-groups]
dev = [
    "ruff>=0.16.10",
]

[tool.ruff]
line-length = 100
extend-exclude = ["sessions", "intro"]

[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP"]
```

`name` comes from the folder name. The lower bounds are whatever was current on the day of
`uv add`, so later numbers are normal; the lockfile, not the bounds, makes the run
repeatable. Everything for Ruff goes in **one** `[tool.ruff]` table: a second
`[tool.ruff]` header is a TOML "duplicate key" error.

## A Heavy Dependency: PyCaret

PyCaret compares a dozen models in one call (session 7). It is also one of the heaviest
dependencies a project can take on. The instructor demonstrates one request with three
outcomes:

| Request | Resolver outcome | What happens next | Lesson |
|---|---|---|---|
| `uv add pycaret` (no bound) | **succeeds**: picks pycaret 2.2.2, a 2020 release; 175 packages; `.venv` grows to 1.4 GB | `from pycaret.classification import setup` fails: `ImportError: cannot import name '_print_elapsed_time' from 'sklearn.utils'` | a successful lock is not a working environment. Old releases declared loose requirements, so the resolver backtracks to them. |
| `uv add "pycaret>=3.3"` | **fails**: pycaret 3.3 needs pandas<2.2.0, the project needs pandas>=3.0.6 | nothing changes; `pyproject.toml` and `uv.lock` stay as they were | a readable conflict is the good outcome: it names the two bounds that collide |
| a separate Python 3.11 environment with `pycaret>=3.3` | **succeeds**: pycaret 3.3.2, pandas 2.1.4, scikit-learn 1.4.2 | the import works; the environment is 760 MB | a tool with different needs gets its own environment |

PyCaret 3.3.2 on Python 3.12 installs but refuses at import with `RuntimeError: Pycaret only
supports python 3.9, 3.10, 3.11`. Hence Python 3.11 in the third row.

The project environment says pandas 3.0.6; the AutoML environment says pandas 2.1.4. Two
environments, two answers, each correct for its purpose. Ruff went into the project's `dev`
group; PyCaret stays out of the project lockfile entirely. Session 7 builds on that rule.

**Do not run `uv add pycaret` without a bound in the project.** Ex 6 runs only the second
row, which downloads metadata, not gigabytes.

## The Runner Is Bob

A clone on the same laptop proves the commit is complete. It shares the laptop's OS, uv
cache, and Python download, so it does not prove another machine can rebuild. GitHub
Actions gives every repository a machine nobody in the room configured: an Ubuntu runner
that clones the repository, runs listed commands, and reports green or red.

Today's workflow, [`02_environment/reproduce.yml`](02_environment/reproduce.yml), asks one
question: can a clean Linux machine rebuild the environment from the lockfile and run the
baseline? Every command in it is run by hand in Ex 4 and Ex 5 first.

- **`--locked`, everywhere.** After `pyproject.toml` changes without `uv lock`,
  `uv sync --locked` fails with a hint to run `uv lock`. `uv sync --frozen` succeeds
  silently with the old lockfile, and a plain `uv run` quietly rewrites `uv.lock` and
  carries on. On a laptop that is a convenience; in an automated check it hides the mistake
  the check exists to catch. PROJECT.md's final proof uses `uv sync --frozen` on a clean
  clone, which stays correct for installing exactly what is committed. `--locked` also
  proves the committed lockfile is current.
- **Printed versions.** Matching metrics do not prove matching environments. A Linux
  rebuild printed the same three numbers with Python 3.12.15 against 3.12.13 on a laptop.
  The log shows what was built, so a difference is visible before it matters.
- **Intentionally incomplete.** Session 3 adds Ruff and pytest as gates; session 10 adds the
  pipeline, the quality gate, caching, a release workflow, and actions pinned to commit SHAs.
- **Action versions.** `actions/checkout@v7` and `astral-sh/setup-uv@v10.2.0`. setup-uv
  publishes only full release tags from v8 on, so `@v10` does not exist. Older tutorials
  show `@v4` and `@v5`; don't copy them.

## In Class

Commands are for a POSIX shell (Git Bash on Windows), from the repository root unless
stated. Stage files by name; never `git add .` in this session, because `intro/` may hold
uncommitted session 1 work.

### Ex 1: Build The Environment From The Starter

1. Leave any active environment:

   ```bash
   deactivate 2>/dev/null || true
   ```

2. Turn the folder into a uv project and fix the Python minor version:

   ```bash
   uv init --bare
   uv python pin 3.12
   ```

3. Close the Python range. Edit `pyproject.toml` so the line reads:

   ```toml
   requires-python = ">=3.12,<3.13"
   ```

4. Declare the three dependencies, then run the baseline inside the environment:

   ```bash
   uv add pandas scikit-learn user-agents
   uv run python baseline.py
   ```

5. Read the three files. Find pandas's bound in `pyproject.toml` and its pin in `uv.lock`:

   ```bash
   cat .python-version pyproject.toml
   grep -n -A1 '^name = "pandas"$' uv.lock
   grep -n -A1 '^name = "numpy"$' uv.lock
   ```

   numpy is in the lockfile, but nobody asked for it. Who did?

6. Commit, so Ex 2 has something to restore to:

   ```bash
   git add pyproject.toml uv.lock .python-version
   git commit -m "Fix Python at 3.12 and lock dependencies with uv"
   git log --oneline -1
   ```

### Ex 2: Three Ways To Fail

1. **A conflict.** Ask for a scikit-learn that needs an old numpy:

   ```bash
   uv add "scikit-learn==1.3.2"
   git status --short
   ```

   Which two packages collide, and over which third one? What did the failed `uv add` do to
   the two files?

2. **A stale lockfile.** Edit `pyproject.toml` by hand: change `"user-agents>=2.2.0"` to
   `"user-agents>=2.1"`. **Run nothing else yet.** Then:

   ```bash
   uv lock --check
   uv sync --locked
   uv sync --frozen
   ```

   Two fail with the same hint; one succeeds without a word. Which one is silent, and why is
   that the dangerous one when nobody is watching?

3. **A quiet relock.** With the edit still in place:

   ```bash
   uv run python -c "print('ran')"
   git status --short
   ```

   What happened to `uv.lock`, and who changed it?

4. Put everything back and confirm:

   ```bash
   git restore pyproject.toml uv.lock
   uv lock --check
   ```

### Ex 3: Ignore, Then Commit

1. Append to `.gitignore`; the existing entries stay:

   ```gitignore
   # session 2: tool caches and scratch environments
   .ruff_cache/
   .venv-*/
   ```

2. Look at what Git sees, then commit the change on its own:

   ```bash
   git status --ignored --short
   git add .gitignore
   git commit -m "Ignore ruff cache and scratch environments"
   git ls-files
   ```

   `git ls-files` is exactly what a clone receives.

### Ex 4: The Clean-Clone Proof

1. Push, then clone the committed state next to the working copy:

   ```bash
   git push origin main
   git clone . ../highrev-clean
   cd ../highrev-clean
   ls -a                                  # no .venv, no model.pickle
   uv sync --locked
   uv run --locked python -c "import sys, pandas, sklearn; print('python', sys.version.split()[0], '| pandas', pandas.__version__, '| scikit-learn', sklearn.__version__)"
   uv run --locked python baseline.py
   ```

2. Compare the version line and the metrics with the working copy and with the session 1
   record. Write the comparison down; the homework uses it.
3. What does this prove, and what doesn't it? Ex 7 answers the second half.
4. Return and remove the clone: `cd - && rm -rf ../highrev-clean`.

### Ex 5: Ruff On baseline.py

1. Add Ruff as a development dependency and confirm which Ruff runs:

   ```bash
   uv add --dev ruff
   uv run ruff --version
   grep -n -A1 '^name = "ruff"$' uv.lock
   ```

2. Run it with Ruff's defaults and record both outputs:

   ```bash
   uv run ruff check baseline.py
   uv run ruff format --check baseline.py
   ```

3. Add the `[tool.ruff]` and `[tool.ruff.lint]` tables from
   [pyproject.toml At The End Of The Session](#pyprojecttoml-at-the-end-of-the-session) to
   `pyproject.toml`, as one block at the end, then run `uv run ruff check .` again. Why did
   the first finding disappear, and where did the new ones come from? Why don't `sessions/`
   or `intro/` appear?

4. Format, and check the formatter's promise not to change behavior:

   ```bash
   uv run python baseline.py | tail -n 4 > /tmp/before.txt
   uv run ruff format baseline.py
   uv run ruff check .
   uv run python baseline.py | tail -n 4 > /tmp/after.txt
   diff /tmp/before.txt /tmp/after.txt && echo "metrics identical"
   ```

   `tail -n 4` skips the first line, which carries a timestamp. In Git Bash, `/tmp` maps to
   the user's temp folder.

5. Update the run instructions in the `baseline.py` docstring. Replace the
   `pip install ...   # COURSE NOTE (session 2): which versions?` line and the
   `python baseline.py` line with:

   ```text
       uv sync                      # versions: uv.lock (session 2)
       uv run python baseline.py
   ```

6. Runtime and development, in two commands:

   ```bash
   uv sync --no-dev
   uv sync
   ```

   Read what each one removes or installs.

7. Commit in two steps, so the format-only change can be reviewed on its own:

   ```bash
   git add pyproject.toml uv.lock
   git commit -m "Add ruff as a locked dev tool with project settings"
   git add baseline.py
   git commit -m "Format baseline.py with ruff and run it with uv; metrics unchanged"
   ```

### Ex 6: Read The PyCaret Conflict

```bash
uv add "pycaret>=3.3"
git status --short
```

Find the line that names pandas. Which of the project's own bounds would have to change for
PyCaret 3.3 to fit, and what would that cost the baseline?

### Ex 7: Ask A Different Machine

1. Copy the workflow from the drop and commit it:

   ```bash
   mkdir -p .github/workflows
   cp sessions/02_environment/reproduce.yml .github/workflows/reproduce.yml
   git add .github/workflows/reproduce.yml
   git commit -m "Add a minimal workflow: rebuild from uv.lock on Linux and run the baseline"
   git push origin main
   ```

2. Open the repository on GitHub, then **Actions**, then the run. Read "Record what was
   built" and "Run the baseline". Compare the versions and metrics with Ex 4. Find the line
   where uv downloads Python 3.12: that is `.python-version` at work on a machine nobody set
   up.

3. Break it on purpose. Repeat the Ex 2 stale-lockfile edit, and **run nothing**, not even
   `uv run`, because that would quietly relock:

   ```bash
   # edit pyproject.toml: "user-agents>=2.2.0" -> "user-agents>=2.1"
   git add pyproject.toml
   git commit -m "Loosen user-agents bound (lockfile deliberately not updated)"
   git push origin main
   ```

   Watch which step fails, and read its message.

4. Fix it the right way and watch it go green:

   ```bash
   uv lock
   git add uv.lock
   git commit -m "Update uv.lock after loosening user-agents"
   git push origin main
   ```

## What To See After Each Exercise

Version numbers come from the day the brief was tested. Later dates give later versions,
which is fine as long as the lockfile and the printed versions agree.

| Exercise | Expected |
|---|---|
| Ex 1, step 2 | `Initialized project ...`; `Pinned .python-version to 3.12` |
| Ex 1, step 4 | 14 packages installed, including pandas, scikit-learn, and numpy; then a timestamp line, `ROC AUC  0.764`, `accuracy 0.721`, `f1       0.302`, `saved model.pickle` |
| Ex 1, step 5 | a `>=` bound in `pyproject.toml`; an exact `version = "..."` under pandas in `uv.lock`; numpy present though never requested |
| Ex 1, step 6 | one commit with three files |
| Ex 2, step 1 | a message ending in `your project's requirements are unsatisfiable`; `git status` shows nothing changed |
| Ex 2, step 2 | two commands fail with `hint: To update the lockfile, run uv lock`; one succeeds |
| Ex 2, step 3 | `ran`; `git status` shows `uv.lock` modified |
| Ex 2, step 4 | `uv lock --check` succeeds; `git status` is empty |
| Ex 3 | `.venv/` and `model.pickle` in the ignored list; `git ls-files` lists the three environment files and `.gitignore` |
| Ex 4 | `uv sync --locked` succeeds; a `python 3.12.x \| pandas ... \| scikit-learn ...` line; the same three metrics |
| Ex 5, step 1 | the Ruff version printed matches the lockfile entry |
| Ex 5, step 2 | one finding about `datetime.datetime.now()`; the format check says the file would be reformatted |
| Ex 5, step 3 | three `E501 Line too long` findings in `baseline.py`; nothing from `sessions/` or `intro/` |
| Ex 5, step 4 | `1 file reformatted`; `All checks passed!`; `metrics identical` |
| Ex 5, step 7 | two commits |
| Ex 6 | a conflict that names pandas; `git status` empty |
| Ex 7, step 2 | a green "reproduce" run with versions and the three metrics in its log |
| Ex 7, step 3 | a red run |
| Ex 7, step 4 | green again |

## Troubleshooting

| Observation | First thing to inspect |
|---|---|
| `uv: command not found` | open a new terminal after installing; read the installer's PATH message |
| `warning: VIRTUAL_ENV=... does not match the project environment path .venv` | a session 1 environment is still active; `deactivate` |
| resolution fails "for other Python versions supported by your project" | `requires-python` still reads `>=3.12`; close it with `<3.13` |
| `uv sync --locked` fails with "To update the lockfile, run `uv lock`" | `pyproject.toml` changed without `uv lock`; run it and commit both files together |
| `Failed to build ...` during `uv sync` | a bound pushed the resolver to a version with no wheel for this platform: resolving is not installing |
| metrics differ from the README | was the script started with `uv run`? Compare the version line from Ex 4 with a classmate's |
| `ruff --version` differs from the lockfile | a Ruff from somewhere else is answering; use `uv run ruff`, and `deactivate` other environments |
| TOML error "duplicate key" | `[tool.ruff]` appears twice in `pyproject.toml`; merge into one table |
| Ruff reports files under `sessions/` or `intro/` | `extend-exclude` is missing from `[tool.ruff]` |
| Git warns "LF will be replaced by CRLF" | `.gitattributes` is missing or edited; restore the starter's |
| the workflow fails with "unable to resolve action" | an action tag was shortened; `astral-sh/setup-uv` needs the full `v10.2.0` |
| no run appears under Actions | the file must sit in `.github/workflows/` on `main`, and Actions must be enabled in the repository settings |
| the push of the workflow file is refused | the Git credential lacks the `workflow` scope; sign in again through the credential manager or `gh auth login` |

## Reading

- uv: [managing dependencies](https://docs.astral.sh/uv/concepts/projects/dependencies/),
  [locking and syncing](https://docs.astral.sh/uv/concepts/projects/sync/), and
  [using uv in GitHub Actions](https://docs.astral.sh/uv/guides/integration/github/).
- Ruff: [configuration](https://docs.astral.sh/ruff/configuration/) and
  [the formatter](https://docs.astral.sh/ruff/formatter/).
- GitHub: [Actions quickstart](https://docs.github.com/en/actions/writing-workflows/quickstart)
  and the [setup-uv README](https://github.com/astral-sh/setup-uv).
- ASI module 3 portability tutorials: the same problem solved with conda's
  `environment.yml`.

## Homework

The homework is the same step on the student's own project. The proposal is due by the
session 3 deadline ([PROJECT.md](../PROJECT.md)), so this week doubles as proposal groundwork.

1. **Finish the in-class work** if anything is open: the clean clone (Ex 4) and a workflow
   run (Ex 7). A red run with a written reason counts; no run at all does not.
2. **Close the session 1 incident.** In `notes/session-02.md`, compare the session 1 record
   (versions and metrics on the other machine) with the locked versions and the runner's
   log. Name the difference that most likely explains any mismatch, or say why the numbers
   matched anyway, given that the Python patch version and uv's own version may still
   differ.
3. **Load the candidate dataset inside the locked environment.** For the dataset considered
   for `PROPOSAL.md`, write a short script that loads it and prints its shape and the
   target's distribution. Add every library it needs with `uv add` (a Parquet or Excel
   reader, for example), never `pip install`. Commit `pyproject.toml` and `uv.lock` with the
   loader. Keep data over a few megabytes out of Git; session 5 gives it a home with DVC.
4. **Prove it again.** Clean-clone the repository and rerun the loader and the baseline. Push
   and confirm the workflow is still green.
5. **Draft `PROPOSAL.md`** from the PROJECT.md template. Under "Data", note the format and
   the libraries the loader needed; under "Risks", note any dependency that conflicted or
   failed to install.
6. **Tag once, at the end:**

   ```bash
   git tag session-02-done
   git push origin main --tags
   ```

Tests don't exist until session 3, so today's proof is "clean clone, then the same three
metrics." The final demonstration keeps PROJECT.md's wording: `uv sync --frozen` on a clean
clone, then the tests pass.

## Checklist

- [ ] `pyproject.toml`, `uv.lock`, and `.python-version` are committed
- [ ] `requires-python` is `>=3.12,<3.13` and `.python-version` says `3.12`
- [ ] `uv run python baseline.py` prints ROC AUC 0.764, accuracy 0.721, f1 0.302
- [ ] The student can say what a bound is, what a pin is, and where each lives
- [ ] A resolver conflict was read and the colliding packages named
- [ ] The student can say what `--locked` checks, what `--frozen` skips, and what a plain `uv run` does to a stale lockfile
- [ ] `.gitignore` includes `.ruff_cache/` and `.venv-*/`; `data/01_raw` is not ignored
- [ ] A clean clone rebuilt with `uv sync --locked` and printed the same versions and metrics
- [ ] Ruff is in the `dev` group, configured in `pyproject.toml`, and its version matches the lockfile
- [ ] `baseline.py` is formatted in its own commit, its docstring runs with uv, and its metrics are unchanged
- [ ] `.github/workflows/reproduce.yml` is pushed and has at least one run
- [ ] The project's own run instructions use uv, not `pip install`; `intro/` stays as the session 1 record
- [ ] The candidate dataset loads inside the locked environment
- [ ] `notes/session-02.md` closes the session 1 incident
- [ ] The last commit is tagged `session-02-done`
