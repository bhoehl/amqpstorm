# Pamqp 2–5 compatibility Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Support `pamqp` versions 2 through 5 with a single `amqpstorm` codebase by routing all pamqp usage through one compatibility module, and validate with CI across Python 3.11–3.13 and pamqp 2.x, 3.x, 4.x, and 5.x.

**Architecture:** Add `amqpstorm/pamqp_compat.py` as the **only** module that imports `pamqp` packages. It exposes stable names (`specification`, `frame`, `header`, `body`, `exceptions`, `heartbeat`, `ContentHeader`, `ProtocolHeader`, and `specification` sub-APIs such as `Queue`, `Exchange`, `Basic`, `Connection`) mapped from whichever layout the installed pamqp uses. Application code and tests import from `amqpstorm.pamqp_compat` instead of `pamqp.*`. CI gains a `pamqp-version` matrix with pinned releases; a separate lint job avoids running flake8 on every matrix cell.

**Tech Stack:** Python 3.11+, pytest, flake8, Docker (RabbitMQ test image), GitHub Actions, pamqp 2–5.

**Related design:** Brainstorming session (2026-04-20): single facade, CI-only matrix, pamqp 2–5 in tests, no tox.

---

## File structure

| File | Responsibility |
|------|----------------|
| `amqpstorm/pamqp_compat.py` | **Create.** Try/import/version-detect pamqp; re-export normalized API used by the rest of the package. |
| `requirements.txt` | **Modify.** `pamqp>=2.0.0,<=5` (or equivalent PEP 440). |
| `setup.py` | **Modify.** `install_requires` pamqp range to match `requirements.txt`. |
| `amqpstorm/basic.py` | **Modify.** Imports from `pamqp_compat`. |
| `amqpstorm/channel.py` | **Modify.** Same. |
| `amqpstorm/channel0.py` | **Modify.** Same. |
| `amqpstorm/connection.py` | **Modify.** Same. |
| `amqpstorm/exchange.py` | **Modify.** Same. |
| `amqpstorm/queue.py` | **Modify.** Same. |
| `amqpstorm/tx.py` | **Modify.** Same. |
| `amqpstorm/tests/unit/**/*.py` (see task list) | **Modify.** Replace `pamqp` imports with `pamqp_compat`; fix monkeypatches to target compat’s `frame` object. |
| `.github/workflows/testing.yml` | **Modify.** Matrix `pamqp-version`; `pip install "pamqp==${{ matrix.pamqp-version }}"` after requirements; optional `exclude` for unsupported Python/pamqp pairs; split `lint` job. |

**Do not** rename or overload `amqpstorm/compatibility.py` (that module is Python 2/3 glue).

---

## Upstream constraints (verify before pinning)

Before choosing exact matrix pins, check PyPI and each pamqp release:

- **pamqp 4.x** requires **Python ≥ 3.11** (per pamqp 4.0.0 release notes).
- **pamqp 5.x** — confirm minimum Python; add `matrix.exclude` entries if e.g. pamqp 5 requires 3.12+.

Document chosen pins in the workflow and in a short comment in `pamqp_compat.py`.

---

### Task 1: Discovery — pamqp APIs per major version

**Files:**

- Read: pamqp changelogs / installed packages in a throwaway venv
- Modify: none

- [ ] **Step 1:** In four venvs (or `pip install pamqp==X` sequentially), confirm import paths for:
  - `specification` (or `commands` + helpers in 3+)
  - `frame.marshal` / `frame.unmarshal`
  - `exceptions.UnmarshalingException`
  - `header.ContentHeader`, `header.ProtocolHeader`
  - `body.ContentBody`
  - `heartbeat.Heartbeat`
  - `specification.Connection`, `Basic`, `Queue`, `Exchange` (or equivalents)
  - `specification.AMQPFrameError` (or new location in 3+)

- [ ] **Step 2:** Note any **behavioral** differences (timestamp decoding, `ContentBody` value type) that affect existing tests.

- [ ] **Step 3:** Commit nothing yet; capture findings in a scratch note used for Task 2.

**Run:** N/A (research).

---

### Task 2: Implement `amqpstorm/pamqp_compat.py`

**Files:**

- Create: `amqpstorm/pamqp_compat.py`
- Test: import smoke — covered in Task 3 after wiring

- [ ] **Step 1:** Implement the module to export at minimum (match current call sites):

```python
# Intended public surface (names may be re-exported from pamqp or adapters):
# - specification  (module-like object with Connection, Channel, Basic, Queue, Exchange, TX, ... nested classes)
# - frame            (with marshal, unmarshal)
# - exceptions       (as pamqp_exception; at least UnmarshalingException)
# - header           (ContentHeader, ProtocolHeader constructors)
# - body             (ContentBody)
# - heartbeat        (Heartbeat)
# - ContentHeader    (class, for "from amqpstorm.pamqp_compat import ContentHeader")
```

- [ ] **Step 2:** If pamqp 3+ uses `pamqp.commands` **functions** instead of `specification.Queue.Declare` classes, provide **adapter namespaces** (e.g. a small class with `Declare` as a `@staticmethod` that calls the real command builder) so `queue.py` / `exchange.py` keep the same call pattern **or** document in Task 4 that those call sites must call helper functions (prefer minimal churn — match v2 style).

- [ ] **Step 3:** At module import failure, raise `ImportError` with text: supported pamqp range `>=2,<=5` and the underlying exception.

- [ ] **Step 4:** Run a quick smoke test:

```bash
python -c "from amqpstorm import pamqp_compat as p; print(p.specification, p.frame)"
```

**Expected:** No import error with pamqp 2 installed.

- [ ] **Step 5: Commit**

```bash
git add amqpstorm/pamqp_compat.py
git commit -m "feat: add pamqp_compat facade for multi-version pamqp"
```

---

### Task 3: Wire library modules to `pamqp_compat`

**Files:**

- Modify: `amqpstorm/basic.py`, `channel.py`, `channel0.py`, `connection.py`, `exchange.py`, `queue.py`, `tx.py`

- [ ] **Step 1:** Replace imports as follows (adjust if your facade uses shorter aliases):

| Old | New |
|-----|-----|
| `from pamqp import body as pamqp_body` | `from amqpstorm.pamqp_compat import body as pamqp_body` |
| `from pamqp import header as pamqp_header` | `from amqpstorm.pamqp_compat import header as pamqp_header` |
| `from pamqp import specification` | `from amqpstorm.pamqp_compat import specification` |
| `from pamqp import exceptions as pamqp_exception` | `from amqpstorm.pamqp_compat import exceptions as pamqp_exception` |
| `from pamqp import frame as pamqp_frame` | `from amqpstorm.pamqp_compat import frame as pamqp_frame` |
| `from pamqp.specification import Queue as pamqp_queue` | `from amqpstorm.pamqp_compat.specification import Queue as pamqp_queue` **or** `from amqpstorm.pamqp_compat import specification as spec; pamqp_queue = spec.Queue` |
| `from pamqp.specification import Exchange as pamqp_exchange` | Same pattern |
| `from pamqp.heartbeat import Heartbeat` | `from amqpstorm.pamqp_compat import Heartbeat` (export from compat) |
| `from pamqp.header import ContentHeader` | `from amqpstorm.pamqp_compat import ContentHeader` |

- [ ] **Step 2:** Run unit tests (Docker RabbitMQ not required for many unit tests):

```bash
pytest amqpstorm/tests/unit/ -q --tb=short -x
```

**Expected:** Fix import errors until tests collect; some may fail until tests are updated (Task 4).

- [ ] **Step 3: Commit**

```bash
git add amqpstorm/basic.py amqpstorm/channel.py amqpstorm/channel0.py amqpstorm/connection.py amqpstorm/exchange.py amqpstorm/queue.py amqpstorm/tx.py
git commit -m "refactor: import pamqp via pamqp_compat in library code"
```

---

### Task 4: Update unit tests to use `pamqp_compat`

**Files:**

- Modify:
  - `amqpstorm/tests/unit/basic/test_basic.py`
  - `amqpstorm/tests/unit/basic/test_basic_exception.py`
  - `amqpstorm/tests/unit/channel/test_channel.py`
  - `amqpstorm/tests/unit/channel/test_channel_exception.py`
  - `amqpstorm/tests/unit/channel/test_channel_frame.py`
  - `amqpstorm/tests/unit/channel/test_channel_message_handling.py`
  - `amqpstorm/tests/unit/channel0/test_channel0.py`
  - `amqpstorm/tests/unit/channel0/test_channel0_frame.py`
  - `amqpstorm/tests/unit/connection/test_connection.py`
  - `amqpstorm/tests/unit/exchange/test_exchange.py`
  - `amqpstorm/tests/unit/test_tx.py`

- [ ] **Step 1:** Replace every `from pamqp...` with the matching `from amqpstorm.pamqp_compat...` (same mapping as Task 3).

- [ ] **Step 2:** In `test_connection.py`, monkeypatch **`pamqp_frame.unmarshal`** where `pamqp_frame` is imported from **`amqpstorm.pamqp_compat`** (not the `pamqp` package). This keeps patches on the same object `connection.py` uses.

- [ ] **Step 3:** Replace `spec_basic = pamqp.specification.Basic` with `from amqpstorm.pamqp_compat.specification import Basic as spec_basic` (or `specification.Basic` after importing `specification` from compat).

- [ ] **Step 4:** Run:

```bash
pytest amqpstorm/tests/unit/ -q
```

**Expected:** All unit tests pass under **one** pamqp version (e.g. 2.3.0) before CI matrix.

- [ ] **Step 5:** If `test_message.py` or IO tests fail only on Windows due to timing, do not change in this task unless failures appear on Linux CI.

- [ ] **Step 6: Commit**

```bash
git add amqpstorm/tests/unit/
git commit -m "test: use pamqp_compat in unit tests"
```

---

### Task 5: Packaging — `requirements.txt` and `setup.py`

**Files:**

- Modify: `requirements.txt`, `setup.py`

- [ ] **Step 1:** Set pamqp constraint consistently, e.g.:

```text
pamqp>=2.0.0,<=5.0.0
```

(use the exact upper bound style the project prefers; avoid conflicting with `install_requires`).

- [ ] **Step 2:** Update `setup.py`:

```python
install_requires=['pamqp>=2.0.0,<=5.0.0'],
```

(match line 35 exactly with `requirements.txt`).

- [ ] **Step 3:** Commit.

```bash
git add requirements.txt setup.py
git commit -m "build: allow pamqp 2 through 5"
```

---

### Task 6: GitHub Actions — matrix, pins, lint split

**Files:**

- Modify: `.github/workflows/testing.yml`

- [ ] **Step 1:** Add **`pamqp-version` as a second matrix axis** alongside the existing **`python-version`** (keep `[3.11.13, 3.12.10, 3.13.7]`). The result is the Cartesian product: **Python × pamqp** (12 cells if no exclusions). Example:

```yaml
strategy:
  matrix:
    python-version: [3.11.13, 3.12.10, 3.13.7]
    pamqp-version: ['2.3.0', '3.3.0', '4.0.0', '5.0.0']
```

(Replace pamqp pins with versions verified on PyPI during Task 1; use patch versions that exist.)

- [ ] **Step 2:** After installing from `requirements.txt`, **force** the matrix version:

```bash
pip install "pamqp==${{ matrix.pamqp-version }}"
```

- [ ] **Step 3:** Add `matrix.exclude` (or `include`) if e.g. pamqp 4/5 does not support Python 3.11 — follow pamqp metadata.

- [ ] **Step 4:** Extract **`lint`** to a separate job:

```yaml
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: actions/setup-python@v6
        with:
          python-version: '3.11.13'
      - run: pip install -r test-requirements.txt
      - run: flake8 .
  test:
    needs: []
    # ... existing docker + pytest with matrix
```

Run **flake8 only in `lint`**, remove duplicate flake8 step from `test` job.

- [ ] **Step 5:** Pass `pamqp-version` into the job name for readability:

```yaml
name: test (py ${{ matrix.python-version }}, pamqp ${{ matrix.pamqp-version }})
```

- [ ] **Step 6:** Commit.

```bash
git add .github/workflows/testing.yml
git commit -m "ci: matrix pamqp 2–5; lint in separate job"
```

---

### Task 7: Full verification (local)

**Files:** none

- [ ] **Step 1:** With Docker RabbitMQ (see `run_ci_locally.sh` or workflow commands), run:

```bash
pip install -r requirements.txt -r test-requirements.txt
pip install "pamqp==2.3.0"
pytest
pip install "pamqp==3.3.0"
pytest
# repeat for 4 and 5
```

**Expected:** All pass on Linux-like env; on Windows, known IO/message flakes may remain out of scope unless they also fail on CI.

- [ ] **Step 2:** Push branch and confirm GHA green.

- [ ] **Step 3:** Final commit only if fixes needed.

- [ ] **Step 4 (fast follow):** If `run_ci_locally.sh` or README/docs still describe `pamqp<3` or old pins, update them so local instructions match `requirements.txt` and CI matrix pins.

---

## Plan review

After saving this file, dispatch **plan-document-reviewer** (per superpowers) with:

- Plan path: `docs/superpowers/plans/2026-04-20-pamqp-multi-version.md`
- Spec path: *none filed* — reference brainstorming decisions (pamqp 2–5, CI-only, single facade).

Fix any reviewer issues; re-dispatch until approved (max 3 iterations).

---

## Execution handoff

**Plan complete and saved to `docs/superpowers/plans/2026-04-20-pamqp-multi-version.md`. Two execution options:**

**1. Subagent-Driven (recommended)** — Dispatch a fresh subagent per task, review between tasks, fast iteration. **REQUIRED SUB-SKILL:** superpowers:subagent-driven-development.

**2. Inline Execution** — Execute tasks in this session using superpowers:executing-plans; batch execution with checkpoints.

**Which approach?**
