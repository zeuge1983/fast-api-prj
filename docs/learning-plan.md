# From Python to AI Engineering — a plan built on this repo

Every exercise below changes code that already exists in `fast-api-prj`. Nothing is a
toy example, nothing is hypothetical, and each step leaves the project working better
than it was.

Three phases, in order. Do not skip ahead: phase 2 assumes you can read every line of
`app/`, and phase 3 assumes you can write a test that fails for the right reason.

| Phase | Theme | Exercises | Rough time |
|---|---|---|---|
| **1** | Python that holds up | P1 – P9 | 3–5 weeks |
| **2** | Pytest as a craft | T1 – T8 | 2–4 weeks |
| **3** | AI engineering | A1 – A9 | 6–10 weeks |

A companion document, [ai-testing-roadmap.md](ai-testing-roadmap.md), goes deeper on
*testing non-deterministic output* specifically. It slots in between phases 2 and 3;
this plan tells you when.

---

## Where the project actually stands

Read this honestly before starting — the gaps are the curriculum.

**What exists and works:**

- 10 HTTP endpoints in [app/main.py](../app/main.py), all synchronous
- Pydantic models with an enum and a `classmethod` constructor — [app/models.py](../app/models.py)
- Pure functions over lists of dicts — [app/processor.py](../app/processor.py)
- A bearer-token dependency with role logic — [app/auth.py](../app/auth.py)
- An LLM call with structured output and defensive parsing — [app/ai.py](../app/ai.py)
- 33 unit tests + 1 live HTTP test, marker-separated, fast by default
- Real hallucination detectors in [tests/grounding.py](../tests/grounding.py)

**What's missing, in the order it will hurt:**

| Gap | Where | Phase |
|---|---|---|
| 9 of 10 endpoints have zero tests | only `GET /tickets/{id}` is covered | 2 |
| No type hints outside `models.py` / `ai.py` | [processor.py](../app/processor.py), [api.py](../app/api.py), [utils.py](../app/utils.py) | 1 |
| Scripts live inside the app package and run on import | [app/muse.py](../app/muse.py), [app/muse_tests.py](../app/muse_tests.py) | 1 |
| `requirements.txt` is wrong — missing `pytest`/`httpx`, lists stdlib `asyncio` | [requirements.txt](../requirements.txt) | 1 |
| No error handling if the CSV is missing or malformed | [api.py:8](../app/api.py#L8) | 1 |
| CSV re-read from disk on every single request | [api.py:7](../app/api.py#L7) | 1 |
| `Ticket` model silently drops customer fields | [models.py:10](../app/models.py#L10) | 1 |
| Tests that call `/analyze` would write to the real `output/` | [utils.py:10](../app/utils.py#L10) | 2 |
| Nothing is async; one LLM call blocks the whole worker | everywhere | 3 |
| No retries, no token accounting, no streaming | [ai.py](../app/ai.py) | 3 |

---

# Phase 1 · Python that holds up

The goal is not "learn syntax." It's to reach the point where you can look at
`summarize_tickets` and see three different Python features that would make it
shorter *and* clearer.

## P1 · Fix the dependency file — priority: do this first

**Files:** [requirements.txt](../requirements.txt)

`pytest` and `httpx` are installed in your `.venv` but absent from the file, so a
fresh clone cannot run the tests. `asyncio` is listed but is part of the standard
library — installing it from PyPI gets you an abandoned backport. `aiohttp` and
`requests` are both there; find out whether anything still imports each one.

Split runtime deps from dev deps. Pin versions with `pip freeze` and understand why
`fastapi` and `fastapi>=0.110` mean different things.

- **Concepts:** virtualenvs, stdlib vs PyPI, transitive dependencies, `pip freeze`, `pip install -e .`, why `pyproject.toml` is the modern home for all of this
- **Done when:** a fresh venv installing `requirements-dev.txt` can run `pytest` green, and a fresh venv installing only `requirements.txt` can serve the app but *cannot* run the tests — that asymmetry is the proof the split is real
- **Trap:** don't pin everything to exact versions and then never update. Learn the difference between an application (pin hard) and a library (pin loose).


Now that I have pip-tools set up, I never need to use

`pip install <package>`
or
`pip freeze manually again.`

My workflow is now a 3-step loop:

- Edit: Add or remove top-level packages directly in requirements.in or requirements-dev.in.

- Compile: Run pip-compile requirements.in (and -dev.in) to regenerate the locked .txt files.

`pip-compile requirements.in`
`pip-compile requirements-dev.in`

- Run pip-sync requirements-dev.txt to instantly apply those changes to your local machine.
`pip-sync requirements-dev.txt
pytest

## P2 · Move the scripts out of the app package

**Files:** [app/muse.py](../app/muse.py), [app/muse_tests.py](../app/muse_tests.py) → `scripts/`

Open [app/muse.py](../app/muse.py) and notice that the LLM call is at module level.
Anything that does `import app.muse` fires a real network request as a side effect.
That is the single most important thing to understand about Python modules: **import
executes the file.**

Move both to `scripts/`, wrap the body in `def main():`, and add the
`if __name__ == "__main__":` guard. Explain to yourself out loud what `__name__` is
and why the guard works.

- **Concepts:** modules vs scripts, import side effects, `__name__`, `__init__.py`, `sys.path`, absolute vs relative imports, entry points
- **Done when:** `python -c "import sys; sys.path.insert(0, 'scripts'); import muse"` produces no output and makes no network call, while `python scripts/muse.py` still prints the test plan. Prove the difference to yourself first: write a two-line file with a `print()` at top level, import it, then move the `print()` inside a `main()` and import it again.
- **Trap:** the `Path(__file__).parent.parent` in `muse_tests.py` survives this particular move — `app/` and `scripts/` are both one level under the root, so it still resolves to the same place. The fragility is elsewhere: it counts directory levels, so moving the file to `scripts/llm/` would silently point at `scripts/tests/` instead, and `mkdir(exist_ok=True)` would create that wrong directory rather than error. Add `.resolve()` so symlinked checkouts count real levels, and note why `__file__`-relative beats a cwd-relative `Path("tests/...")`: the script then works from any directory you run it in.

## P3 · Type hints everywhere, then let a checker prove you right

**Files:** [app/processor.py](../app/processor.py), [app/api.py](../app/api.py), [app/utils.py](../app/utils.py)

Not one function in `processor.py` has a signature. Add them —
`list[dict[str, Any]]` to start, then ask whether `Any` is honest. Install `mypy` and
run it; fix what it finds.

Then go further: define a `TypedDict` or a `Ticket` dataclass for the row shape and
watch `get_ticket(tickets, ticket_id)` become self-documenting.

- **Concepts:** `list[T]` / `dict[K, V]`, `Optional[T]` vs `T | None`, `Any` as an escape hatch, `TypedDict`, `Protocol`, gradual typing, `mypy --strict`
- **Done when:** `mypy app/` is clean without a single `# type: ignore`
- **Trap:** type hints are not enforced at runtime. `def f(x: int)` accepts a string happily. Knowing exactly what they do and don't buy you is the actual lesson.

## P4 · Rewrite `summarize_tickets` three ways

**Files:** [app/processor.py:4-24](../app/processor.py#L4-L24)

The current version is 20 lines of manual dict-key checking. Write it again as:

1. `collections.defaultdict(int)` — removes the `if key not in` dance
2. `collections.Counter` with a generator expression — removes the loop
3. One dict comprehension per grouping

Keep the version you find clearest and delete the rest. Then generalize: write
`group_by(tickets, field)` so `by_priority` and `by_category` are one call each, and
adding `by_status` costs one line.

- **Concepts:** `collections.Counter` / `defaultdict`, comprehensions, generator expressions, `dict.setdefault`, higher-order functions, `operator.itemgetter`
- **Done when:** the function is under 8 lines, all tests still pass, and adding a fourth grouping is a one-line change
- **Trap:** the shortest version is not automatically the best. Write all three, read them a day later, and pick deliberately.

## P5 · Files, JSON and the errors they throw

**Files:** [app/utils.py](../app/utils.py), [app/api.py](../app/api.py)

Three things to fix here.

**Encoding.** `open(path, "w")` uses the platform default. A ticket description with
an emoji or Cyrillic text will crash on some machines and not others. Add
`encoding="utf-8"` and make `json.dump` use `ensure_ascii=False`, then write a ticket
with non-ASCII text and see the difference in the output file.

**Missing input.** [api.py:8](../app/api.py#L8) assumes the CSV exists. Delete it
temporarily and look at the traceback your API returns. Catch `FileNotFoundError` and
raise something the caller can act on — then decide whether `app/api.py` should know
about `HTTPException` at all, or whether it should raise its own exception type that
`main.py` translates.

**Round-tripping.** Write `load_report()` next to `save_report_json`, and handle the
case where the file is absent or contains invalid JSON.

- **Concepts:** `pathlib`, context managers (`with`), text vs binary mode, encodings, `json.dump` vs `dumps`, `json.JSONDecodeError`, exception hierarchies, custom exception classes, `raise ... from exc`
- **Done when:** deleting `data/support_tickets.csv` produces a clear 503 with a useful message instead of a 500 stack trace, and a ticket titled `Проблема с оплатой 💳` survives a save/load round trip
- **Trap:** `except Exception: pass` is how you lose a week. Catch the specific class, and never swallow without either logging or re-raising.

## P6 · Drop pandas from the read path

**Files:** [app/api.py](../app/api.py)

`pandas` is a 60 MB dependency being used for one `read_csv` of a 12-row file.
Rewrite `load_tickets()` with `csv.DictReader` from the standard library.

You'll immediately hit the interesting part: `DictReader` gives you strings for
everything, so `ticket_id` arrives as `"123"` and `t["ticket_id"] == ticket_id` stops
matching. Fix it by converting types explicitly, and notice that pandas had been doing
that silently — which is convenient right up until it guesses wrong.

- **Concepts:** `csv.DictReader`, stdlib vs third-party trade-offs, explicit type coercion, `int()` and its exceptions, why implicit type inference is a liability in a data pipeline
- **Done when:** `pandas` is gone from `requirements.txt`, every test still passes, and `GET /tickets/123` still returns a JSON `id` of `123` and not `"123"`
- **Trap:** run the tests *before* you believe it works. This change silently alters types across the whole app, and [models.py:45](../app/models.py#L45) already has `int(row["ticket_id"])` papering over it in one place only.

## P7 · Classes: make a Ticket an object

**Files:** new `app/domain.py`, then [app/processor.py](../app/processor.py)

Everything in this app is a raw `dict`, so `t["prioroty"]` is a typo that fails at
runtime rather than a name that fails immediately. Build a `Ticket` class and give it
behaviour, not just fields:

```python
@dataclass(frozen=True)
class Ticket:
    ticket_id: int
    title: str
    priority: Priority
    ...

    @property
    def is_urgent(self) -> bool: ...

    @classmethod
    def from_row(cls, row: dict) -> "Ticket": ...
```

Compare it with `@dataclass`, with `NamedTuple`, and with the Pydantic model already
in [models.py](../app/models.py). Understand why the project has three plausible
options and what each one costs.

- **Concepts:** `class`, `__init__`, `self`, `@property`, `@classmethod` vs `@staticmethod`, `__repr__` / `__eq__`, `@dataclass`, `frozen=True` and hashability, inheritance vs composition, dunder methods
- **Done when:** `filter_high_priority` reads `[t for t in tickets if t.is_urgent]`, and a typo in an attribute name is caught before the code runs
- **Trap:** don't build a class hierarchy. One class is the exercise; `class UrgentTicket(Ticket)` is a wrong turn you'll spend a week unwinding.

## P8 · Pydantic properly

**Files:** [app/models.py](../app/models.py)

The models are doing about a third of what Pydantic offers. Add, in order:

1. **`Field` constraints** — `ticket_id: int = Field(gt=0)`, `title: str = Field(min_length=1, max_length=200)`. Watch the auto-generated docs at `/docs` update themselves.
2. **Enums for `status`** — `Priority` is an enum but `status` is a bare `str`, so `"Opne"` is accepted today. Fix the asymmetry.
3. **A field validator** — normalize `priority` so `"high"` and `"HIGH"` both work, using `@field_validator(mode="before")`.
4. **A model validator** — reject a ticket that is `status="Closed"` with `priority="High"`, or whatever cross-field rule you think is right.
5. **The missing customer fields** — `Ticket` has no `customer_id`, so `POST /analyze` silently discards them via `normalize_tickets`, and [grounding.py:30](../tests/grounding.py#L30) checks a `customer_name` that can never be there. Decide whether to add the fields or to drop that check, and write down why.
6. **`model_config`** — try `extra="forbid"` and see which existing request bodies break.

- **Concepts:** `Field` constraints, `@field_validator` / `@model_validator`, `mode="before"` vs `"after"`, `model_dump` vs `model_dump_json`, `model_config`, `Annotated`, computed fields, how Pydantic v2 differs from v1
- **Done when:** `POST /analyze` rejects `{"status": "Opne"}` with a 400 naming the field, and the Swagger schema documents every constraint without you writing docs
- **Trap:** validators run in a defined order and a `mode="before"` validator receives raw input of *any* type, including `None`. Write a test for the weird input before you trust the validator.

## P9 · FastAPI structure — routers, dependencies, responses

**Files:** [app/main.py](../app/main.py) → `app/routers/`

`main.py` is 125 lines and will not survive doubling. Refactor:

**Split into routers.** `tickets.py`, `reports.py`, `analysis.py`, each an
`APIRouter`, wired up with `app.include_router(...)`. Use `prefix` and `tags` and
watch `/docs` organize itself.

**Use the dependency you already wrote.** `get_tickets()` at
[main.py:28](../app/main.py#L28) is called directly by seven handlers. Make it
`tickets: list = Depends(get_tickets)` instead, and then — the payoff — override it in
a test with `app.dependency_overrides` so tests don't touch the real CSV.

**Add `response_model` to every route.** Only `GET /tickets/{ticket_id}` has one
today. Every other endpoint returns undocumented shapes.

**Understand route ordering.** `/tickets/high` is declared at line 47 and
`/tickets/{ticket_id}` at line 95. Swap them and watch `/tickets/high` start returning
a 400. Then you'll never forget why.

**Add query parameters.** Give `GET /tickets` `limit`, `offset`, and an optional
`priority` filter, with validation via `Query(ge=1, le=100)`.

- **Concepts:** `APIRouter`, `include_router`, `Depends` and the DI graph, `dependency_overrides`, `response_model` and `response_model_exclude_none`, `status_code`, `Query` / `Path` / `Body`, exception handlers, startup/shutdown via `lifespan`
- **Done when:** `main.py` is under 30 lines, `/docs` groups endpoints by tag, and a test can swap in fake ticket data without monkeypatching a module
- **Trap:** `Depends(get_tickets)` re-reads the CSV per request just as the direct call did. Caching it in a `lifespan` startup handler is the natural follow-up — and the natural next question is what happens when the file changes while the server runs.

---

# Phase 2 · Pytest as a craft

You have 34 tests, and they are good ones. The gap is coverage breadth and the pytest
features you haven't needed yet.

## T1 · Measure before you write — priority: do this first

**Files:** `pyproject.toml`

Install `pytest-cov` and run `pytest --cov=app --cov-report=term-missing`. You will
find that 9 of 10 endpoints are untested and that whole modules
([utils.py](../app/utils.py), [api.py](../app/api.py)) are barely touched.

Do not chase 100%. Use the report to decide *what to write next* in T2.

- **Concepts:** `pytest-cov`, statement vs branch coverage, `--cov-branch`, `# pragma: no cover`, why coverage is a floor and never a goal
- **Done when:** you can name the three least-tested modules from memory
- **Trap:** coverage measures lines executed, not assertions made. A test with no `assert` still shows green coverage. It is a map of what you've *run*, not what you've *checked*.

## T2 · Test the nine untested endpoints

**Files:** new `tests/test_endpoints.py`

Straight volume work, and the fastest way to internalize the `client` fixture. One
test per endpoint, then negative cases: `POST /analyze` with an empty list, with a bad
priority, with a missing field; `POST /tickets/filter` with a filter matching nothing.

- **Concepts:** `TestClient` for POST bodies, `response.json()`, asserting on status *and* shape, arrange/act/assert as a habit
- **Done when:** every route in `main.py` has at least one passing and one failing-input test
- **Trap:** `POST /analyze` calls `save_report_json`, which writes to the real [output/report.json](../output/report.json). Your test suite is currently capable of overwriting project files. That's T3.

## T3 · `tmp_path` and `monkeypatch` — stop tests touching the real filesystem

**Files:** [app/utils.py](../app/utils.py), `conftest.py`

`OUTPUT_DIR` is a module-level constant, so tests cannot redirect it. Two ways out:
monkeypatch the constant, or make the output directory a parameter with a default.
Do both, then argue with yourself about which is better design.

Then use `monkeypatch.setenv` to test the `LLM_*` configuration in
[ai.py](../app/ai.py) — including a regression test for the bug where `load_dotenv()`
ran after the constants were evaluated.

- **Concepts:** `tmp_path`, `tmp_path_factory`, `monkeypatch.setattr` / `setenv` / `delenv`, automatic teardown, `importlib.reload` and why module-level config is hard to test
- **Done when:** `git status` is clean after a full test run, every time
- **Trap:** that config test is harder than it looks. Module constants are read once at import, so `monkeypatch.setenv` after import changes nothing — which is *exactly* the lesson, and the reason lazily-read config is more testable than constants.

## T4 · Collapse the boundary tests into a table

**Files:** [tests/test_tickets_generated.py](../tests/test_tickets_generated.py)

TC-B01 through TC-B05 are five near-identical functions. Collapse them into one
`@pytest.mark.parametrize` with `pytest.param(..., id="TC-B03-negative")` so the spec
IDs survive into the test report and `pytest -k TC-B03` runs exactly one case.

- **Concepts:** `parametrize`, `pytest.param`, `id=`, `-k` expressions, stacked parametrize (cartesian product), `marks=` on a single case
- **Done when:** a sixth boundary case is one line of data
- **Trap:** don't parametrize tests whose bodies genuinely differ. If the test body needs `if expected == 400:` branches, you've merged two tests into one and made both harder to read.

## T5 · Fixtures that build things

**Files:** `conftest.py`

Your fakes in `conftest.py` are already good. Add:

- A **factory fixture** — `make_ticket(priority="High", **overrides)` so tests declare only what they care about
- A **fixture with `yield` teardown** that clears `app.dependency_overrides`
- **Scope experiments** — make one fixture `scope="session"` and one `scope="function"`, print inside each, and watch when they run

Then override the auth dependency instead of hardcoding `Bearer valid-token`, and
parametrize the whole permission matrix: agent / owning customer / other customer ×
tickets 1 and 123.

- **Concepts:** factory fixtures, `yield` fixtures, fixture scopes, `autouse`, fixture composition, `request` object, `app.dependency_overrides`
- **Done when:** adding a fourth role costs one line in a parametrize list
- **Trap:** forgetting `dependency_overrides.clear()` leaks the override into every later test. The signature symptom: files pass individually, the suite fails as a whole.

## T6 · Property-based testing with Hypothesis

**Files:** new `tests/test_processor_properties.py`

`filter_tickets` and `summarize_tickets` are pure functions over lists — ideal
Hypothesis targets. Let it generate ticket lists and assert properties:

- `sum(summary["by_priority"].values()) == summary["total_tickets"]`
- filtering by a priority yields only tickets with that priority
- filtering by nothing returns the input unchanged
- `filter_tickets` is order-independent

Hypothesis will find the empty list, the single-element list, and the duplicate-ID
case without you thinking of them.

- **Concepts:** `@given`, `strategies.lists` / `builds` / `sampled_from`, shrinking, `@example`, `assume`, invariants vs examples
- **Done when:** Hypothesis finds at least one input you would not have written by hand
- **Trap:** a property test that just reimplements the function is circular. Assert *relationships*, not recomputed values.

## T7 · Real end-to-end, and what `TestClient` cannot see

**Files:** [tests/test_tickets_live.py](../tests/test_tickets_live.py)

Extend the one live test into a small suite that starts `uvicorn` itself as a
subprocess fixture rather than requiring a second terminal, then walks a full user
journey: list tickets → filter → fetch one → analyze.

- **Concepts:** `subprocess.Popen` in a session fixture, waiting for readiness (poll, don't `sleep`), port allocation, cleanup on failure, marker-gated slow tests, what an ASGI-level client structurally cannot catch
- **Done when:** `pytest -m live` passes on a machine with nothing running
- **Trap:** a fixture that leaks a uvicorn process on failure will leave your port occupied and the next run will fail confusingly. `try/finally` in the fixture, and kill the process group, not the process.

## T8 · Contract tests against the real model

**Files:** new `tests/test_ai_contract.py`

You'd started this one yourself. Mark it `contract`, call `POST /tickets/analyze-ai`
with LM Studio running, and assert only what must hold across every run: the four
schema keys are present, types are right, lists are non-empty when tickets exist,
`top_categories` ⊆ input categories.

Then reflect on the finding: given the `json_schema` response format in
[ai.py:49](../app/ai.py#L49), a shape assertion can barely fail. That tells you a
contract test is guarding the *serving setup* — a wrong model name, a changed API, a
provider that ignores `response_format` — not the model's intelligence.

- **Concepts:** marker-gated integration tests, shape-only assertions, `pytest.skip` vs `pytest.fail` for missing infrastructure, timeouts, what "contract" means as distinct from "unit" and "eval"
- **Done when:** `pytest -m contract` passes with LM Studio up and fails with a clear message when it's down
- **Trap:** don't assert on wording, ever. Not `"Billing" in summary`, not a minimum length. Every such assertion will fail on a rephrasing that was perfectly correct.

> **Stop here and read [ai-testing-roadmap.md](ai-testing-roadmap.md).** Exercises 4–8
> of that document (cassettes, grounding, metamorphic relations, golden datasets,
> LLM-as-judge) are the natural continuation, and they're already written against this
> codebase. Come back for phase 3 afterwards.

---

# Phase 3 · AI engineering

Everything above was groundwork. This is the part that maps onto the job you're
aiming at.

## A1 · Async — the concept, then the rewrite

**Files:** [app/ai.py](../app/ai.py), [app/main.py](../app/main.py)

Right now `analyze_tickets_with_ai` blocks for up to 300 seconds
([ai.py:22](../app/ai.py#L22)). In a sync `def` endpoint FastAPI runs that in a
threadpool; in an `async def` endpoint it would block the entire event loop. You need
to understand exactly why before touching anything.

The work, in order:

1. Read about the event loop until you can explain why `time.sleep(1)` inside
   `async def` is a bug and `await asyncio.sleep(1)` isn't
2. Swap `OpenAI` for `AsyncOpenAI` and make `analyze_tickets_with_ai` a coroutine
3. Make the endpoint `async def` and `await` it
4. Install `pytest-asyncio` (or use `anyio`, already a transitive dep) and fix the
   tests — your `FakeClient` needs async methods now
5. Benchmark: fire 5 concurrent requests at the sync version and the async version,
   and measure

- **Concepts:** `async` / `await`, coroutines vs functions, the event loop, `asyncio.gather`, `asyncio.to_thread`, blocking calls in async contexts, `AsyncOpenAI`, `httpx.AsyncClient`, `@pytest.mark.asyncio`, async fixtures
- **Done when:** 5 concurrent `/tickets/analyze-ai` requests take roughly as long as 1, and you can explain the result
- **Trap:** `async` is not a speedup. A single request gets no faster, and CPU-bound code gets *slower*. If you can't say precisely what it buys you here, you've copied a pattern rather than learned one.

## A2 · Parse the LLM response into a Pydantic model

**Files:** [app/ai.py:99](../app/ai.py#L99), [app/models.py](../app/models.py)

`_parse_json` returns a bare `dict`, or `{"raw": text}` on failure — so every consumer
has to guess the shape. Define `TicketAnalysis(BaseModel)` with the four fields, parse
into it with `model_validate`, and let Pydantic reject malformed output.

Then the real design question: when the model returns valid JSON with the wrong shape,
is that a 502, a 422, or a retry? Decide, implement, and write the test.

- **Concepts:** `model_validate` / `model_validate_json`, `ValidationError` handling, `response_model` on the endpoint, the single `RESPONSE_FORMAT` schema as the source of truth for both the request and the parse, structured outputs as a general technique
- **Done when:** the endpoint declares `response_model=TicketAnalysis` and `/docs` shows the real analysis schema
- **Trap:** deleting the `{"raw": text}` fallback loses your only diagnostic when a model misbehaves. Keep the raw text — log it, or attach it to the error — rather than dropping it.

## A3 · Retries, timeouts and partial failure

**Files:** [app/ai.py](../app/ai.py)

One transient 503 currently fails the whole request. Add bounded retry with
exponential backoff and jitter — write it by hand first with a loop and
`asyncio.sleep`, then compare against `tenacity` and against the OpenAI SDK's own
`max_retries`.

Decide which errors are retryable. A timeout: yes. A 400 for a malformed request: no,
retrying it is just slower failure.

- **Concepts:** exponential backoff, jitter, idempotency, retry budgets, `tenacity`, circuit breakers, distinguishing transient from permanent errors, `asyncio.timeout`
- **Done when:** a fake client that fails twice then succeeds produces one successful response, and a fake that returns a 400 is not retried at all
- **Trap:** retrying a 300-second timeout three times is a 15-minute request. Cap total elapsed time, not just attempt count.

## A4 · Tokens, cost and context limits

**Files:** [app/ai.py](../app/ai.py), new `app/usage.py`

The prompt embeds every ticket as JSON ([ai.py:113](../app/ai.py#L113)). With 12
tickets that's fine. At 10,000 it exceeds any context window, and the failure mode is
silent truncation or a confusing API error.

Count tokens before sending (`tiktoken`, or the model's own tokenizer), log
`response.usage` from every call, and raise a clear error when the prompt won't fit.

- **Concepts:** tokenization, context windows, input vs output tokens, `response.usage`, cost per 1M tokens, why token count ≠ character count ÷ 4 for non-English text
- **Done when:** the endpoint refuses an oversized batch with a message naming the limit and the actual count
- **Trap:** tokenizers are model-specific. A count from one model's tokenizer is an estimate for another, and non-Latin scripts blow up the ratio badly.

## A5 · Chunk and map-reduce over large ticket sets

**Files:** [app/ai.py](../app/ai.py)

The fix for A4's limit. Split tickets into batches, analyze each concurrently with
`asyncio.gather`, then run a second "reduce" call that merges the partial analyses
into one.

This is the first genuinely non-trivial LLM pipeline you'll build, and every issue in
it is representative: how to merge overlapping insights, whether counts survive the
reduce step (they usually don't — check with your grounding functions), and what
happens when one chunk fails.

- **Concepts:** map-reduce over LLM calls, `asyncio.gather(return_exceptions=True)`, concurrency limits with `asyncio.Semaphore`, prompt design for a merge step, error aggregation, partial results
- **Done when:** 200 synthetic tickets produce one coherent analysis, and [tests/grounding.py](../tests/grounding.py) still reports the counts as grounded
- **Trap:** grounding almost certainly breaks here — the reduce step sees summaries, not tickets, so it invents totals. Finding that with your own detector is the best possible outcome of this exercise.

## A6 · Streaming

**Files:** [app/main.py](../app/main.py), [app/ai.py](../app/ai.py)

A 2-minute wait with no output is an acceptance failure regardless of correctness.
Stream tokens with `stream=True` and serve them over Server-Sent Events via FastAPI's
`StreamingResponse`.

Then hit the genuine conflict: you cannot validate JSON against a schema until it's
complete. Decide what to stream — the summary text as prose, with structured fields
delivered at the end, is one reasonable answer.

- **Concepts:** `stream=True`, async generators, `yield` in async functions, `StreamingResponse`, SSE format, chunked transfer, partial-JSON parsing, testing streams
- **Done when:** `curl -N` shows text appearing progressively
- **Trap:** a streamed error is not an HTTP error. Once the first byte is sent the status code is already 200, so failures mid-stream need an in-band error event your client understands.

## A7 · LangChain — port, then judge it

**Files:** new `app/chains.py`

Rebuild `analyze_tickets_with_ai` with LangChain: `ChatOpenAI` pointed at your LM
Studio base URL, a `ChatPromptTemplate`, `PydanticOutputParser` using the model from
A2, composed with LCEL (`prompt | llm | parser`).

Then do the thing most tutorials skip: compare the two implementations side by side
and write down what LangChain added and what it cost you. You'll be qualified to judge
that, because you wrote the raw version first. That answer is worth more in an
interview than the ability to wire up a chain.

- **Concepts:** LCEL and the `Runnable` protocol, `ChatPromptTemplate`, output parsers, `.batch()` / `.astream()`, callbacks and LangSmith tracing, retries at the chain level, the abstraction-vs-control trade-off
- **Done when:** both implementations pass the same contract test, and you have a written verdict on which this project should keep
- **Trap:** LangChain changes fast and much published example code no longer runs. Work from the current docs, and prefer LCEL over the deprecated `LLMChain` style you'll find in older tutorials.

## A8 · Tools and a small agent

**Files:** new `app/agent.py`

The step from "LLM that summarizes" to "LLM that acts." Expose your existing pure
functions as tools — `filter_tickets`, `get_ticket`, `summarize_tickets` — and let the
model choose which to call for a question like *"which billing tickets are still open,
and who reported them?"*

Build it twice: once with raw OpenAI tool-calling (a `while` loop dispatching on
`tool_calls`), then with LangGraph. The raw version is what makes the framework
version comprehensible.

- **Concepts:** tool/function calling, JSON schema for tools, the agent loop, `tool_choice`, multi-turn message state, loop limits, LangGraph state machines, human-in-the-loop checkpoints
- **Done when:** a natural-language question returns an answer that required at least two tool calls, and a malicious question cannot make the agent call a tool with unvalidated arguments
- **Trap:** an agent loop without an iteration cap is an infinite spend. Cap it, and log every tool call with its arguments — you cannot debug an agent you can't see.

## A9 · Retrieval over ticket history

**Files:** new `app/retrieval.py`

The last piece, and the one most product work actually needs. Embed the ticket
descriptions, store the vectors (start with an in-memory list and cosine similarity by
hand — 12 tickets don't need a database), and answer *"have we seen this problem
before?"* by retrieving the nearest tickets and passing only those to the model.

Hand-roll the similarity search before reaching for FAISS or Chroma. It's about
fifteen lines of NumPy and it removes all the mystery.

- **Concepts:** embeddings, cosine similarity, chunking strategies, top-k retrieval, the RAG pattern, hybrid search (keyword + vector), re-ranking, why retrieval quality dominates generation quality
- **Done when:** a query about a login problem retrieves login tickets and not billing ones, and the model's answer cites the ticket IDs it was given
- **Trap:** RAG failures are usually retrieval failures, not model failures. Evaluate the retrieval step in isolation — precision and recall on a hand-labelled set — before blaming the LLM for a bad answer.

---

## Priority order

If you do nothing else, do these eight, in this sequence:

| # | Exercise | Why it's first |
|---|---|---|
| 1 | **P1** — fix requirements | Everything else assumes a reproducible environment |
| 2 | **P2** — scripts out of the package | Teaches import semantics, the most common Python confusion |
| 3 | **T1** — coverage report | You cannot prioritize tests without seeing the gaps |
| 4 | **P4** — rewrite `summarize_tickets` | Idiomatic Python lands hard when it's your own code shrinking |
| 5 | **T2** — test the untested endpoints | Volume builds fluency faster than cleverness |
| 6 | **P8** — Pydantic properly | The highest-leverage single skill for FastAPI work |
| 7 | **P9** — routers and dependencies | The structure every real FastAPI codebase uses |
| 8 | **A1** — async | The dividing line between scripting and backend engineering |

## Suggested pace

| Weeks | Focus |
|---|---|
| 1–2 | P1, P2, P3, P4 |
| 3–4 | P5, P6, P7 |
| 5–6 | P8, P9 |
| 7–8 | T1, T2, T3, T4 |
| 9–10 | T5, T6, T7, T8 |
| 11–13 | [ai-testing-roadmap.md](ai-testing-roadmap.md) exercises 4–8 |
| 14–16 | A1, A2, A3 |
| 17–19 | A4, A5, A6 |
| 20–24 | A7, A8, A9 |

Slower is fine. Skipping is not — each phase is load-bearing for the next.

## How to work an exercise

1. Read the existing code until you can explain what it does without running it
2. Write the test first where a test is possible
3. Make the change
4. Run `pytest -m ""` — all of it, not just the file you touched
5. Commit with a message that says *why*, not *what*
6. Write two sentences in a log file about what surprised you

Step 6 is not optional filler. The surprises are where the learning is, and you will
not remember them in three months.

## Concept → where it lives in this repo

| Concept | Read this first |
|---|---|
| Pure functions | [app/processor.py](../app/processor.py) |
| Classmethod constructor | [models.py:41](../app/models.py#L41) |
| Enum as a type | [models.py:5](../app/models.py#L5) |
| Dependency injection | [auth.py:16](../app/auth.py#L16), [main.py:98](../app/main.py#L98) |
| Custom exception handler | [main.py:20](../app/main.py#L20) |
| Module-level config from env | [ai.py:15-25](../app/ai.py#L15-L25) |
| Defensive parsing | [ai.py:92](../app/ai.py#L92) |
| Dependency-injected test double | [ai.py:104](../app/ai.py#L104) |
| Structured LLM output | [ai.py:48](../app/ai.py#L48) |
| Fixtures and fakes | [conftest.py](../conftest.py) |
| Marker-based test selection | [pyproject.toml](../pyproject.toml) |
| Invariant assertions | [tests/grounding.py](../tests/grounding.py) |

---

Written against `fast-api-prj` at commit `d064700`, 23 September 2026 — 34 tests,
10 endpoints, one local LLM.
