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

Each heuristic is implemented as an ast-grep rule bundled with the plugin, plus a plain-grep fallback for environments without ast-grep installed. The hunter runs both and dedupes results by `(file, line)`.

### H7.a — Supabase `{ data }` destructured without `error`

**Rule file:** `rules/silent-failures/supabase-data-without-error.yml`

**What it catches:**
```typescript
// BUG — error silently dropped
const { data: contentItems } = await supabase
  .from('content_items')
  .select('id, title')
  .in('id', matchedIds);
// If the query errored, contentItems is null. The next line:
const matched = (contentItems ?? []).map(...);
// treats failure as "no rows found" and the route returns a 200.
```

**Ecosystem scope:** Supabase/PostgREST in TypeScript. Also applies to any library returning a Result-shaped tuple without sum-type enforcement (AWS SDK v3, Go's `(value, err)` idiom translated to TS wrappers).

**Detection strategy:**

1. **Primary (ast-grep):** Pattern `const { data: $X } = await $EXPR` where `$EXPR` is NOT matched by `const { data: $X, error: ... } = await ...`.
2. **Fallback (POSIX grep):**
   ```bash
   grep -rnE 'const [[:space:]]*\{[[:space:]]*data([[:space:]]*:[[:space:]]*[a-zA-Z_]+)?[[:space:]]*\}[[:space:]]*=[[:space:]]*await' . \
     --include="*.ts" --include="*.tsx" 2>/dev/null \
     | grep -v node_modules | grep -v '\.test\.\|\.spec\.'
   ```

**Confidence:** Very High in Supabase codebases. The audit found 30+ instances with near-zero false positive rate.

**Severity guidance:**
- **Critical** when the query result drives AI input, user-visible content, or authorisation decisions (e.g. `lib/auth.ts` role lookup, bid drafting pipeline content fetch).
- **High** when the query result drives dashboard/list views or response payloads.
- **Medium** when the result is logged but not rendered.

**False positives to filter:**
- TanStack Query hooks: `const { data } = useQuery(...)` — error state via `isError`/`isLoading` fields.
- Supabase auth destructure: `const { data: { user } } = await supabase.auth.getUser()` — `user === null` is the expected auth-fail signal. Low severity even if flagged.
- Test file destructures in `*.test.*`, `*.spec.*`, `__tests__/` — mock clients.

**Fix template (fail-fast):**
```typescript
const { data: contentItems, error } = await supabase
  .from('content_items')
  .select('id, title')
  .in('id', matchedIds);
if (error) {
  return NextResponse.json({ error: error.message }, { status: 500 });
}
// Now contentItems is guaranteed non-null.
```

**Fix template (if codebase has `sb()` wrapper):**
```typescript
const contentItems = await sb(
  supabase.from('content_items').select('id, title').in('id', matchedIds),
  'content_items.byIds'
);
```

---

### H7.b — Supabase mutation with discarded return

**Rule file:** `rules/silent-failures/supabase-mutation-discarded.yml`

**What it catches:**
```typescript
// BUG — update result discarded
await supabase.from('content_items').update({ layer: 'foo' }).eq('id', id);
// Route returns 200 with the updated row SELECTed back,
// so the user sees "saved successfully" even on RLS denial.
```

**Ecosystem scope:** Supabase/PostgREST. The PostgREST PATCH-on-wrong-UUID silent no-op is a known quirk: the query "succeeds" with zero rows affected, but the discarded return is the only signal.

**Detection strategy:**

1. **Primary (ast-grep):** Match `expression_statement` wrapping an `await_expression` of `$CLIENT.from($_).$METHOD(...)` where `$METHOD` is one of `update|insert|upsert|delete`.
2. **Fallback (POSIX grep):**
   ```bash
   grep -rnE 'await [a-zA-Z_]+\.from\([^)]+\)\.(update|insert|upsert|delete)' . \
     --include="*.ts" --include="*.tsx" 2>/dev/null \
     | grep -v node_modules | grep -v 'const\|=\s*await\|return'
   ```

**Confidence:** High. Any await-mutation whose return is discarded is either a bug or a comment-justified best-effort (which should still be telemetered).

**False positives:** Mutations inside `Promise.all([...])` where the array result is destructured later. Explicit fire-and-forget cleanup paths in cron jobs (should still push to a `pipeline_runs` audit table).

**Fix template:**
```typescript
const { error } = await supabase
  .from('content_items')
  .update({ layer: 'foo' })
  .eq('id', id);
if (error) {
  return NextResponse.json({ error: 'update failed', detail: error.message }, { status: 500 });
}
```

---

### H3 — Loop with `console.error`, no `failed[]` array

**Rule file:** `rules/silent-failures/catch-only-logs-in-loop.yml` (TypeScript)
**Python variant:** `rules/silent-failures/python-except-log-only-in-loop.yml`

**What it catches:**
```typescript
// BUG — response shape has { results } but no failed[] parallel
const results: Result[] = [];
for (const item of items) {
  try {
    results.push(await processItem(item));
  } catch (err) {
    console.error(`Failed ${item.id}:`, err);
    // No push to failed[], no increment of failure counter
  }
}
return NextResponse.json({ results });  // undercount is invisible
```

**Ecosystem scope:** Universal. Any language with loops and exception handling has an equivalent pattern.

**Detection strategy:** Find a `try_statement` inside a `for_statement`/`for_in_statement`/`while_statement`/`do_statement` where the catch clause contains `console.$_($$$)` (or `logger.$_` in Python) AND does NOT contain `$_.push(...)` (or `$_.append(...)` in Python) AND does NOT contain `throw_statement` (or `raise_statement`).

**Confidence:** Medium. Some cleanup loops legitimately don't need to report per-iteration failures.

**False positives to filter:**
- Cleanup loops where iteration success/failure is genuinely irrelevant (e.g. deleting old temp files).
- Loops that logged but also incremented a metric counter (still acceptable if the counter feeds an alert).

**Fix template:**
```typescript
const results: Result[] = [];
const failed: Array<{ id: string; error: string }> = [];
for (const item of items) {
  try {
    results.push(await processItem(item));
  } catch (err) {
    failed.push({ id: item.id, error: (err as Error).message });
  }
}
return NextResponse.json({ results, failed });
// Caller can now render "N of M items failed" banner.
```

See Knowledge Hub `app/api/freshness/calculate/route.ts` post-fix (commit `f338ddf`) for the canonical fix shape.

---

### H4 — Bare empty catch

**Primary rule:** `rules/empty-catch-block.yml` (existing, TypeScript — not in `silent-failures/` subdir)
**Python variant:** `rules/silent-failures/python-except-pass.yml`
**Go variants:** `rules/silent-failures/go-err-nil-empty.yml`, `rules/silent-failures/go-err-discarded.yml`

**What it catches:**
```typescript
try { riskyOp(); } catch { }                      // TS
try: risky_op()
except: pass                                       # Python
_ = riskyOp()                                     // Go
if err != nil { }                                 // Go
```

**Important note to hunter:** H4 in TypeScript is covered by the existing `empty-catch-block.yml` rule (part of the general pattern-checker toolkit). The silent-failure-hunter does NOT re-flag TypeScript empty catches — that would duplicate the pattern-checker's findings. The hunter only reports H4 via the Python and Go language variants.

**Ecosystem scope:** Universal.

**Confidence:** High — empty catches are almost always a smell, even if the smell is acceptable in context.

**False positives:**
- Top-level cleanup paths that functionally replace `finally` blocks.
- Polyfill detection probes: `try { new Proxy(...) } catch { }` at module top level.
- Specific-exception `pass` cases in Python where the exception is explicitly expected: `except ImportError: optional_module = None`.

**Fix template:**
```typescript
try { riskyOp(); } catch (err) {
  console.warn('cleanup failed (best-effort)', err);
  metrics.increment('cleanup.failed');
}
```

---

### H5 — `.then(...).catch(() => fallback)` ignoring error parameter

**Rule file:** `rules/silent-failures/then-catch-ignores-error-param.yml`

**What it catches:**
```typescript
// BUG — error silently becomes null, no telemetry
const data = await fetch(url)
  .then(r => r.json())
  .catch(() => null);
```

**Ecosystem scope:** TypeScript/JavaScript Promise chains. Not applicable to `async/await + try/catch` — that's covered by `catch-ignores-error.yml`.

**Detection strategy:** Match `$_.catch(() => $$$)` pattern where the arrow function has no parameters.

**Confidence:** High. This idiom is almost always a bug — if the fallback is intentional, the comment should say so and the error should at least be logged.

**False positives:**
- Promise utilities with documented sentinel fallbacks: `p.catch(() => cacheMiss)` where `cacheMiss` is the documented intent.
- `.catch((_) => fallback)` — the underscore IS a parameter, so the rule doesn't match.

**Fix template:**
```typescript
const data = await fetch(url)
  .then(r => r.json())
  .catch((err) => {
    console.error('fetch failed', err);
    metrics.increment('fetch.fallback');
    return null;
  });
```

---

### H6 — Mock data behind env-var conditional

**Rule file:** `rules/silent-failures/mock-data-on-missing-env.yml`

**What it catches:**
```typescript
// BUG — production fallback to fake data
async function getEmbeddings(text: string) {
  if (!process.env.OPENAI_API_KEY) {
    return mockEmbeddings;  // silent prod fallback
  }
  return await realEmbed(text);
}
```

**Detection strategy:** Match `if (!process.env.$_) { ... return $MOCK }` where `$MOCK` matches the regex `(?i)(mock|fake|sample|fixture|placeholder)`.

**Confidence:** High when the identifier regex matches. Lower when the mock data is inlined as an object literal without a naming hint.

**False positives:**
- `NODE_ENV !== 'production'` gates (different conditional, not caught by the rule).
- Return of `null` or a real default value (not a "mock" identifier).
- Return of a 503 error response.

**Fix template (fail-fast):**
```typescript
async function getEmbeddings(text: string) {
  if (!process.env.OPENAI_API_KEY) {
    throw new Error('OPENAI_API_KEY is required — embeddings cannot be generated');
  }
  return await realEmbed(text);
}
```

**Fix template (503):**
```typescript
async function getEmbeddings(text: string): Promise<Response> {
  if (!process.env.OPENAI_API_KEY) {
    return new Response(
      JSON.stringify({ error: 'embedding service not configured' }),
      { status: 503, headers: { 'Content-Type': 'application/json' } }
    );
  }
  // ... real path
}
```

---

### H-Resolver — Helper returns `T | null` conflating error with not-found

**Rule file:** `rules/silent-failures/resolver-null-conflation.yml`

**What it catches:**
```typescript
// BUG — DB error becomes 404 "not found" on caller side
export async function resolveGuideId(slug: string): Promise<string | null> {
  const { data } = await supabase
    .from('guides')
    .select('id')
    .eq('slug', slug)
    .single();
  return data?.id ?? null;
}
```

**Caller pattern:**
```typescript
const id = await resolveGuideId(slug);
if (!id) return new Response('Not Found', { status: 404 });
// But: DB error also took this branch, and 404 does not page oncall.
```

**Detection strategy:** Match `async function $NAME($$$): Promise<$T | null> { ... }` where the body has `const { data } = await ...` AND does NOT have a `const { data, error } = ...` or `const { error } = ...` destructure elsewhere.

**Confidence:** Medium-High. The pattern is structurally distinctive.

**False positives:** Helpers that wrap a known-safe in-memory lookup (no DB call). The rule only matches when there's an `await` inside.

**Fix template:**
```typescript
export async function resolveGuideId(slug: string): Promise<string | null> {
  const { data, error } = await supabase
    .from('guides')
    .select('id')
    .eq('slug', slug)
    .single();
  if (error && error.code !== 'PGRST116') {  // PGRST116 = "no rows"
    throw new ResolverError(`guide lookup failed: ${error.message}`);
  }
  return data?.id ?? null;
}
```

---

### H-Composite — Fan-out endpoint without `warnings[]` envelope

**Not an ast-grep rule — implemented as a structural check in the hunter body.**

**What it catches:**
```typescript
// BUG — 7 parallel queries, any single failure is invisible to the UI
export async function GET() {
  const [items, stats, users, /* ... */] = await Promise.all([
    supabase.from('items').select('*'),
    supabase.from('stats').select('*'),
    supabase.from('users').select('*'),
    // ...
  ]);
  return NextResponse.json({ items: items.data, stats: stats.data, users: users.data });
  // A failure in any query collapses to `null` in the response,
  // and the UI cannot distinguish "nothing to show" from "failed to load".
}
```

**Detection algorithm** (deterministic, not freeform reasoning):

1. The hunter reads `composite_routes` from the inlined api-surface context (files with ≥3 `await <client>.from(...)` calls).
2. For each file, Read the full file.
3. Identify handler function declarations: `export async function GET|POST|PUT|PATCH|DELETE`.
4. For each handler, scan its function body top-to-bottom for `return` statements. Stop at nested function/arrow declarations (those are closures, not handler returns).
5. For each `return` statement, inspect the returned expression:
   - `return NextResponse.json({...})` — parse the object literal
   - `return Response.json({...})` — parse the object literal
   - `return new Response(JSON.stringify({...}))` — parse the stringified object
6. Check whether the returned object literal contains any of: `warnings`, `errors`, `partial`, `degraded`, or a spread from a variable named with one of those substrings.
7. If ≥2 return statements exist AND none contain a warnings-like field, flag the handler at Medium severity with pattern_id `H-Composite`.

**Fallback grep** (used when step 6 is ambiguous):
```bash
grep -E 'warnings\s*:|errors\s*:\s*\[|partial\s*:|degraded\s*:' "$file"
```

If zero matches, treat as flagged. If ≥1 match, downgrade to Low confidence (may be the right pattern in a different location).

**Confidence:** Medium. The algorithm is deterministic but the "2+ returns without envelope" heuristic has legitimate exceptions — routes that fail-fast on any error by design.

**Severity guidance:** Cap at Medium. Add a note to the finding: "Verify whether this route's UX requires partial-failure semantics. If yes, apply warnings envelope; if no, document the fail-fast decision."

**Fix template:**
```typescript
export async function GET(): Promise<Response> {
  const warnings: string[] = [];
  const [items, stats] = await Promise.all([
    supabase.from('items').select('*').then(r => {
      if (r.error) warnings.push(`items: ${r.error.message}`);
      return r.data ?? [];
    }),
    supabase.from('stats').select('*').then(r => {
      if (r.error) warnings.push(`stats: ${r.error.message}`);
      return r.data ?? [];
    }),
  ]);
  return NextResponse.json({
    items,
    stats,
    ...(warnings.length > 0 && { warnings }),
  });
}
```

Knowledge Hub canonical exemplar: `app/api/items/[id]/route.ts` lines 200-388.

---

### H-Helper-Cascade — Silent failure in a helper called by ≥3 routes

**Not a standalone pattern — a severity modifier applied to H7.a, H7.b, and H-Resolver findings in helper files.**

**Rationale:** The S151 clean-routes re-audit found that `lib/auth.ts` had a Pattern 7 instance which was the root cause of two separate Medium findings in route files. Helpers are force multipliers for silent failures: fixing at the helper level is higher leverage than fixing per-route, and the helper-level bug has wider blast radius.

**Detection logic (hunter runtime, not an ast-grep rule):**

1. When the hunter finds H7.a, H7.b, or H-Resolver in a file listed under `helper_paths` in the inlined context:
2. Count how many route files import that helper (use the route inventory from api-surface).
3. If ≥3 routes import it, bump severity by one level:
   - Low → Medium
   - Medium → High
   - High → Critical
4. Add a "cascade_impact" field to the finding listing all affected routes.

**Example:**
```
[HIGH] Silent failure in lib/auth.ts:getAuthorisedClient
Cascade impact: 12 routes (app/api/admin/*, app/api/items/*, ...)
Original severity: Medium (H7.a)
Bumped severity: High (H-Helper-Cascade, ≥3 callers)
```

**Fix guidance:** Fix at the helper level. Don't patch individual routes. Use a discriminated-union return type (`{ success: true; client } | { success: false; reason }`) so all callers are forced to handle the error path via type-system.

See Knowledge Hub `lib/auth.ts` post-fix (the `'role_lookup_failed'` variant of `AuthorisedResult`) for the canonical shape.

---

## Canonical Remediation Patterns

These are the shapes the hunter should cite in its fix suggestions. When api-surface.md records that an exemplar exists in the target codebase, the hunter should point to it directly.

### The `sb()` wrapper

Drop-in replacement for direct Supabase calls. Throws `SupabaseError` on any error, returns `data` directly on success. Makes it impossible to destructure `data` without error handling.

```typescript
// lib/supabase/safe.ts
import type { PostgrestError, PostgrestSingleResponse } from '@supabase/supabase-js';

export class SupabaseError extends Error {
  readonly name = 'SupabaseError';
  constructor(public readonly cause: PostgrestError, context?: string) {
    const prefix = context ? `[${context}] ` : '';
    super(`${prefix}${cause.message}`);
  }
}

type PostgrestLike<T> = PromiseLike<PostgrestSingleResponse<T>>;

export async function sb<T>(query: PostgrestLike<T>, context?: string): Promise<T> {
  const result = await query;
  if (result.error) throw new SupabaseError(result.error, context);
  return result.data as T;
}

// Usage — impossible to forget the error check
const items = await sb(
  supabase.from('items').select('*').in('id', ids),
  'items.byIds'
);
```

### The `warnings[]` envelope

Composite responses that may partially succeed. The warnings field is omitted when empty and present-with-content when something failed — the UI renders a banner when `warnings.length > 0`.

```typescript
// Route handler shape
type ResponseWithWarnings<T> = T & { warnings?: readonly string[] };

export async function GET(): Promise<Response> {
  const warnings: string[] = [];

  // Each sub-query pushes to warnings on failure
  const itemsResult = await supabase.from('items').select('*');
  if (itemsResult.error) warnings.push(`items: ${itemsResult.error.message}`);

  const statsResult = await supabase.from('stats').select('*');
  if (statsResult.error) warnings.push(`stats: ${statsResult.error.message}`);

  const response: ResponseWithWarnings<{ items: any[]; stats: any[] }> = {
    items: itemsResult.data ?? [],
    stats: statsResult.data ?? [],
    ...(warnings.length > 0 && { warnings }),
  };

  return NextResponse.json(response);
}
```

**UI integration (load-bearing):** The consuming component must render `warnings.length > 0` as a banner. Without UI integration this pattern is "build the thing, forget to turn it on" — the envelope exists but no one reads it.

```tsx
function Dashboard({ data }: { data: ResponseWithWarnings<DashboardData> }) {
  return (
    <>
      {data.warnings && data.warnings.length > 0 && (
        <Banner variant="warning">
          Some data could not be loaded: {data.warnings.join('; ')}
        </Banner>
      )}
      <DashboardContent data={data} />
    </>
  );
}
```

### `Result<T, E>` for partial failures

Discriminated union return type. Callers MUST check `ok` before accessing `data`, so the error path cannot be accidentally skipped.

```typescript
export type Result<T, E = SupabaseError> =
  | { ok: true; data: T }
  | { ok: false; error: E };

export async function tryQuery<T>(query: PostgrestLike<T>, context?: string): Promise<Result<T>> {
  const result = await query;
  if (result.error) return { ok: false, error: new SupabaseError(result.error, context) };
  return { ok: true, data: result.data as T };
}

// Usage in composite responses
const itemsResult = await tryQuery(supabase.from('items').select('*'), 'items.all');
if (!itemsResult.ok) {
  warnings.push(`items: ${itemsResult.error.message}`);
}
```

### Comment-driven best-effort → telemetered best-effort

Replace `// best-effort: ignore failures` with a Sentry breadcrumb or metric counter so "best-effort" becomes observable in production.

```typescript
// BEFORE
try {
  await sendNotification(userId, 'owner-assigned');
} catch (err) {
  // best-effort: don't fail the request
  console.warn(err);
}

// AFTER
try {
  await sendNotification(userId, 'owner-assigned');
} catch (err) {
  Sentry.addBreadcrumb({
    category: 'notification.best-effort',
    message: 'owner-assigned notification failed',
    level: 'warning',
    data: { userId, error: String(err) },
  });
  metrics.increment('notification.best_effort_failed', { type: 'owner-assigned' });
}
```

The Sentry breadcrumb doesn't fail the request, but it DOES give ops a signal. A spike in `notification.best_effort_failed` metrics will page someone.

---

## Language Variants

### Python

| Pattern | Example |
|---------|---------|
| Bare except | `try: x() \n except: pass` |
| Exception as | `try: x() \n except Exception as e: pass` |
| Log-only in loop | `for i in items: try: process(i) \n except: logger.error("%s", e)` |
| Null-returning resolver | `def find(id) -> Optional[T]: row = db.query(...).first(); return row.id if row else None` (no exception distinction) |

**SQLAlchemy note:** Unlike Supabase, SQLAlchemy raises `SQLAlchemyError` subclasses on DB errors. The Pattern-7 footgun does not apply directly. But the loop-with-log and resolver patterns still do.

### Go

| Pattern | Example |
|---------|---------|
| Empty if err | `if err != nil { }` |
| Discarded err | `_ = db.Exec(...)`, `_, _ = file.Write(...)` |
| Sink to nil | `row, _ := db.QueryRow(...)` (throw err away on read) |

**GORM note:** `.Error` field on the chain. `db.Find(&users).Error` must be checked, not just `db.Find(&users)`.

### Ruby (documentation only — no rules in v1.6.0)

- `rescue nil` — shorthand for `rescue StandardError => e; nil; end` with the error swallowed. Universal Ruby anti-pattern.
- `begin ... rescue ... end` without a `raise` in the rescue block.

### Rust (documentation only)

- `.unwrap_or_default()` on `Result<T, E>` — turns error into default value. Same root cause as JavaScript fallback-to-null.
- `let _ = result` — discards a `Result` entirely.
- `.ok()` conversion — converts `Result<T, E>` to `Option<T>`, losing error detail.

---

## Framework-Specific Notes

### Supabase / PostgREST

- **RLS silent no-op on PATCH:** PostgREST returns 204 with zero affected rows when RLS denies a PATCH. The `update()` call "succeeds" from the client's perspective. Always destructure `{ data, error, count }` and check `count` if RLS is expected to pass on the intended row set.
- **PGRST116 = "no rows":** When using `.single()`, an empty result set becomes error code `PGRST116`. This is usually *not* an error from the application's perspective — it's legitimate "not found." Treat PGRST116 as `data = null` in resolver helpers; treat all other errors as real failures.
- **`.maybeSingle()`:** Returns `data: null | T` without PGRST116 on empty. Prefer for resolvers.

### Prisma / Drizzle / TypeORM

- **These throw on DB error.** The Pattern-7 footgun (silent destructure) does NOT apply because there's no `{ data, error }` tuple — failed queries raise. The hunter should NOT run H7.a against Prisma/Drizzle/TypeORM codebases.
- **Still check for:** catch-all wrapping that swallows the thrown error (H4, H5 patterns), and resolver helpers that return `T | null` without distinguishing thrown-error from found-nothing.

### Raw `fetch()`

- **Check `response.ok`, not just `response.status`.** `fetch()` does not throw on 4xx/5xx — it resolves with `response.ok === false`. Destructuring `.json()` without checking `ok` is a silent-failure equivalent:
  ```typescript
  // BUG
  const data = await fetch(url).then(r => r.json());

  // FIX
  const r = await fetch(url);
  if (!r.ok) throw new Error(`fetch failed: ${r.status} ${r.statusText}`);
  const data = await r.json();
  ```

---

## False Positive Catalogue

Cases where the heuristic fires but the code is correct. The hunter should NOT flag these.

- **TanStack Query / React Query hooks:** `const { data } = useQuery(...)` — error state via `isError`/`isLoading`/`error` fields. Not a Supabase call.
- **Supabase auth destructure:** `const { data: { user } } = await supabase.auth.getUser()` — `user === null` is the expected auth-fail signal. The audit classifies this as a Low-severity acceptable false positive.
- **Test file destructures:** Any file matching `*.test.*`, `*.spec.*`, `__tests__/`, `e2e/`. Mock clients legitimately destructure data without error checks.
- **Polyfill detection probes:** `try { new Proxy({}, {}) } catch { }` at module top level. These check for runtime features; an empty catch is the correct shape.
- **Best-effort catches with sentinel comment:** `catch { /* best-effort: cache miss, safe to ignore */ }`. The comment is the signal that a human has decided the swallow is acceptable.
- **Known-infallible stdlib calls in Go:** `_ = buf.WriteString("literal")` on a `bytes.Buffer` cannot fail. Acceptable.
- **Resolver helpers that wrap in-memory lookups:** `function resolveLocal(key): T | null` that doesn't await a DB call. The rule only matches when there's an `await` inside.
- **Specific-exception pass in Python:** `except ImportError: optional_module = None`. The exception is explicitly expected; the null is the documented intent.

---

## Integration Points

### How the `silent-failure-hunter` agent uses this file

The hunter locates this playbook at runtime via:

```bash
PLAYBOOK=$(find ~/.claude/plugins -path "*/codebase-review/references/silent-failure-playbook.md" -type f 2>/dev/null | head -1)
```

It reads the full file on startup, applies the heuristics in the order listed in the Quick Reference table, and cites rule file paths + fix templates from this playbook in its findings.

Specifically, every finding the hunter emits should include:
1. A `pattern_id` field matching one of the Quick Reference row IDs (H7.a, H7.b, H3, H4, H5, H6, H-Resolver, H-Composite, H-Helper-Cascade).
2. A reference to the relevant Detection Heuristics subsection by name.
3. A fix suggestion drawn from the Canonical Remediation Patterns section, preferring the target codebase's own exemplar (from `api-surface.md` canonical_patterns) when one exists.

### How the `spec-writer` agent uses this file (future — v1.6.1+)

Deferred. In v1.6.0, `spec-writer` receives playbook content via the existing "Reference Implementation" field of its spawn prompt, populated by the orchestrator's Wave 6 logic. Direct integration is tracked for v1.6.1+.

---

**Version:** 1.0 (v1.6.0 release)
**Last updated:** 2026-04-09
**Source audits:** Knowledge Hub S151 (silent failure audit, root cause analysis, clean routes re-audit, silent failure prevention spec)
