# Silent Failure Detection Playbook

This playbook is the authoritative reference for the `silent-failure-hunter` agent. It defines the detection heuristics, canonical remediation patterns, language variants, and known false positives for silent-failure bugs — cases where code appears to succeed (returns 200, no exception, no log) but actually produced degraded, empty, or wrong output because an error was silently swallowed.

**Primary source:** Knowledge Hub S151 audit (39 findings: 4 Critical, 14 High, 17 Medium, 4 Low). 30 of 39 were the same Pattern 7 bug — Supabase `{ data }` destructured without `error`.

---

## Quick Reference

| Pattern ID | Name | Language | Confidence | Fix type |
|-----------|------|----------|-----------|----------|
| H7.a | Supabase `{ data }` destructured without `error` | typescript | Very High | `sb()` wrapper or explicit error check |
| H7.b | Supabase mutation with discarded return | typescript | High | Destructure `{ error }`, check before return |
| H3 | Loop with `console.error`, no `failed[]` array | universal | Medium | Add parallel `failed[]` array to response |
| H4 | Bare empty catch (`catch {}`) | universal | High | Log and re-throw, or telemeter + comment |
| H5 | `.then(...).catch(() => fallback)` ignoring error | typescript | High | Named error parameter + log or re-throw |
| H6 | Mock data behind env-var conditional | typescript | High | Fail fast on missing env, or return 503 |
| H-Resolver | Helper returns `T \| null` conflating error with not-found | typescript | Medium-High | Return `Result<T \| null, Error>` or throw on error |
| H-Composite | Fan-out endpoint without `warnings[]` envelope | typescript | Medium | Adopt warnings envelope or document fail-fast |
| H-Helper-Cascade | Silent failure in a helper called by ≥3 routes | universal | severity +1 | Fix at helper level, not per-route |

---

## The Root Cause

Silent failures are not a "developer skill" problem — they are architecturally enabled by libraries that return optional-tuple results instead of discriminated unions, by framework conventions that treat "best-effort" as an acceptable comment-level annotation, and by response shapes that conflate "partial success" with "complete success."

The Knowledge Hub S151 audit surfaced six distinct root causes, ordered by frequency in the audit:

### RC-7 — Discriminated-union-by-convention with no type-system enforcement

**Ecosystem:** `supabase-js` (`PostgrestResponse<T>`). Returns `{ data: T | null; error: PostgrestError | null; count; status; statusText }`. Both fields are nullable independently, **not** as a discriminated union. TypeScript compiles `const { data } = await supabase.from(...).select()` with no warning that `error` exists and was dropped.

**What the developer intended vs what the code does:** They wanted "fetch a list; if none, default to empty array and continue." `(data ?? []).map(...)` reads as a defensive idiom. It actually collapses three distinct states — success-with-rows, success-with-zero-rows, failure — into one branch, and the failure branch is indistinguishable from "empty result."

**30+ findings in the S151 audit.**

### RC-3 — Catch-with-only-console.error as the JavaScript "best-effort" idiom

**Ecosystem:** JavaScript / Node convention. `try { ... } catch (err) { console.error(err) }` is the lowest-friction way to "not crash." It looks responsible (something was logged!) but produces no user-facing signal and no telemetry.

**Developer intended:** "don't let this loop iteration kill the whole batch." **What the code does:** silently drops iterations from the response — `results.push(...)` only runs in the success branch, so the response shape `{ results }` undercounts and there is no `failed[]` counterpart.

### RC-4 — Comment-driven "best-effort" without escalation path

**Ecosystem:** Convention. A comment like `// best-effort notification, don't fail the request` is treated as permission to swallow. The comment is true at write time but the swallow is forever — no metric, no alert, no degradation path.

**Developer intended:** notifications should be non-blocking. **What the code does:** the *capability* (e.g. owner-assignment notification) is silently dead in production and nobody notices until support is contacted.

### RC-8 — Fire-and-forget mutation with discarded return value

**Ecosystem:** `supabase-js` mutations return `{ data, error, count }` even when the developer "doesn't need the data." `await supabase.from(...).update(...).eq(...)` is syntactically valid; the discarded return contains the only signal that the update failed (RLS denial, CHECK constraint, wrong UUID).

**Developer intended:** "fire the update, move on." **What the code does:** treats all updates as successful, including the silent-no-op-on-RLS case which is a known PostgREST quirk.

### RC-Composite — Responses that conflate "partial" with "complete"

**Ecosystem:** Next.js API route convention of returning a single JSON blob that aggregates multiple sub-queries (`Promise.all(...)`). When some sub-queries fail and others succeed, the response shape doesn't have a slot for "this section failed to load" — so failures collapse into empty arrays and the UI cannot tell the difference.

### RC-Resolver — Helpers that conflate "not found" with "lookup failed"

**Ecosystem:** Helper functions like `resolveGuideId(slug): Promise<string | null>` use `null` as both the "not found" signal and the "DB error" signal. Callers branch on `=== null` and produce a 404. A transient DB error becomes a misleading "Guide not found" page, silently turning 5xx into 4xx and suppressing ops alerting.

---

## Detection Heuristics

Each heuristic is implemented as an ast-grep rule (or rules) bundled with the plugin, plus a plain-grep fallback for environments without ast-grep installed. The hunter runs both and dedupes results by `(file, line)`.

### H7.a — Supabase `{ data }` destructured without `error`

*See `rules/silent-failures/supabase-data-without-error.yml`.*

Full detection detail, false positives, and fix template populated in Phase 3 of the implementation plan. Until then, refer to the source document `docs/audits/s151-silent-failure-root-cause-analysis.md §3 H7.a` in the Knowledge Hub repo.

### H7.b — Supabase mutation with discarded return

*See `rules/silent-failures/supabase-mutation-discarded.yml`.*

Stub — populated in Phase 3.

### H3 — Loop with `console.error`, no `failed[]` array

*See `rules/silent-failures/catch-only-logs-in-loop.yml`.*

Stub — populated in Phase 3.

### H4 — Bare empty catch

*See existing `rules/empty-catch-block.yml` (already bundled) + `rules/silent-failures/python-except-pass.yml` (Python) + `rules/silent-failures/go-err-nil-empty.yml` (Go).*

**Note to hunter:** H4 is pattern-checker territory in TypeScript. The hunter does NOT re-flag TS empty catches — that's the job of `empty-catch-block.yml`. The hunter only reports H4 via the Python and Go language variants.

Stub — populated in Phase 3.

### H5 — `.then(...).catch(() => fallback)` ignoring error parameter

*See `rules/silent-failures/then-catch-ignores-error-param.yml`.*

**Note to hunter:** Similar to H4 — the existing `catch-ignores-error.yml` covers `try/catch` cases. The new rule is specifically for `.then().catch()` chains. Hunter flags this only when it occurs inside an API route handler body.

Stub — populated in Phase 3.

### H6 — Mock data behind env-var conditional

*See `rules/silent-failures/mock-data-on-missing-env.yml`.*

Stub — populated in Phase 3.

### H-Resolver — Helper returns `T | null` conflating error with not-found

*See `rules/silent-failures/resolver-null-conflation.yml`.*

Stub — populated in Phase 3.

### H-Composite — Fan-out endpoint without `warnings[]` envelope

This heuristic is structural — not implemented as an ast-grep rule. The hunter walks the composite route list from `api-surface.md`, reads each handler function, and checks whether any return statement contains a warnings-like field (`warnings`, `errors`, `partial`, `degraded`). The detection algorithm is defined in the hunter's `<heuristics>` section.

Stub — populated in Phase 3.

### H-Helper-Cascade — Silent failure in a helper called by ≥3 routes

This heuristic is a severity modifier, not a separate pattern. When the hunter finds H7.a, H7.b, or H-Resolver inside a file listed under `helper_paths` in `api-surface.md`, it counts how many routes import that helper. If ≥3, severity is bumped by one level (Medium→High→Critical).

**Rationale:** The S151 clean-routes re-audit found that `lib/auth.ts` had a Pattern 7 instance that was the root cause of two separate Medium findings in routes. Helpers are force multipliers for silent failures — fixing at the helper level is higher leverage than fixing per-route.

Stub — populated in Phase 3.

---

## Canonical Remediation Patterns

Stub — populated in Phase 3. Will include runnable code examples for:

- **The `sb()` wrapper** (from `silent-failure-prevention-spec.md §5.1`)
- **The `warnings[]` envelope** (from `app/api/items/[id]/route.ts` Knowledge Hub exemplar)
- **`Result<T, E>` for partial failures**
- **Comment-driven best-effort → telemetered best-effort** (Sentry breadcrumbs)

---

## Language Variants

Stub — populated in Phase 3. Will cover:

- **Python:** `except: pass`, `except Exception: pass`, `raise` variants, SQLAlchemy patterns
- **Go:** `if err != nil {}`, `_ = fn()`, `gorm` patterns
- **Ruby:** `rescue nil`, `begin/rescue/end` (documentation only — no ast-grep rules in v1.6.0)
- **Rust:** `.unwrap_or_default()`, `.ok()`, `let _ = result` (documentation only)

---

## Framework-Specific Notes

Stub — populated in Phase 3. Will cover:

- **Supabase / PostgREST** — RLS silent no-op on PATCH, PGRST116 = "no rows" legitimate null
- **Prisma / Drizzle / TypeORM** — throw on DB error, so H7.a does not apply; still check catch-all wrapping
- **Raw `fetch()`** — check `response.ok`, not just `response.status`

---

## False Positive Catalogue

Stub — populated in Phase 3. Will list:

- TanStack Query hooks: `const { data } = useQuery(...)` — error state via `isError`/`isLoading`
- Supabase auth destructure: `const { data: { user } } = await supabase.auth.getUser()` — `user === null` is the expected signal
- Test file destructures — always exclude `*.test.*`, `*.spec.*`, `__tests__/`
- Polyfill detection probes — `try { new Proxy(...) } catch { }` at module top level
- Best-effort catches with sentinel comment — `/* best-effort: cache miss */` is documented intent

---

## Integration Points

### How the `silent-failure-hunter` agent uses this file

The hunter locates this playbook at runtime via:

```bash
find ~/.claude/plugins -path "*/codebase-review/references/silent-failure-playbook.md" -type f
```

It reads the full file on startup, applies the heuristics in the order listed in the Quick Reference table, and cites rule file paths + fix templates in its findings.

### How the `spec-writer` agent uses this file (future — v1.6.1+)

Deferred. In v1.6.0, spec-writer receives playbook content via the existing "Reference Implementation" field of its spawn prompt. Direct integration is tracked for v1.6.1+.

---

**Skeleton status:** Phase 1 complete. Heuristic detail sections, canonical patterns, language variants, framework notes, and false positive catalogue are populated in Phase 3 of the implementation plan.
