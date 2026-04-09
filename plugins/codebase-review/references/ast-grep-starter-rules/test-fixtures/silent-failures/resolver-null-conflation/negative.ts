// Fixture for resolver-null-conflation — negative cases

declare const supabase: any;

// --- Case 1: Correct — checks error explicitly ---
export async function correctResolver(slug: string): Promise<string | null> {
  const { data, error } = await supabase
    .from('guides')
    .select('id')
    .eq('slug', slug)
    .single();
  if (error) throw new Error(`guide lookup failed: ${error.message}`);
  return data?.id ?? null;
}

// --- Case 2: Throws on error, destructures separately ---
export async function throwingResolver(slug: string): Promise<string | null> {
  const result = await supabase
    .from('guides')
    .select('id')
    .eq('slug', slug)
    .single();
  if (result.error) throw result.error;
  return result.data?.id ?? null;
}

// --- Case 3: Not a resolver — returns Promise<T>, not T | null ---
export async function listGuides(): Promise<string[]> {
  const { data, error } = await supabase.from('guides').select('*');
  if (error) throw error;
  return data ?? [];
}

// --- Case 4: Returns Result<T | null, Error> — discriminated union ---
type Result<T, E> = { ok: true; data: T } | { ok: false; error: E };
export async function safeResolver(slug: string): Promise<Result<string | null, Error>> {
  const { data, error } = await supabase.from('guides').select('id').eq('slug', slug).single();
  if (error) return { ok: false, error: new Error(error.message) };
  return { ok: true, data: data?.id ?? null };
}
