// Fixture for supabase-data-without-error — negative cases
// Source: Knowledge Hub S151 silent-failure-recheck.md §2 false positives
// None of these should be flagged by the rule.

declare const supabase: any;
declare function useQuery(arg: any): any;

// --- Case 1: Correct destructure with error (the canonical fix) ---
async function correctDestructure(id: string) {
  const { data, error } = await supabase.from('content_items').select('*').eq('id', id);
  if (error) throw error;
  return data;
}

// --- Case 2: Correct destructure with aliased error ---
async function correctAliased(id: string) {
  const { data: items, error: itemsError } = await supabase.from('content_items').select('*').eq('id', id);
  if (itemsError) throw itemsError;
  return items;
}

// --- Case 3: TanStack Query useQuery hook (NOT a Supabase call) ---
function MyComponent() {
  const { data } = useQuery({ queryKey: ['items'], queryFn: () => fetch('/api/items') });
  return data;
}

// --- Case 4: Supabase auth destructure (data: { user } is the standard pattern) ---
// NOTE: Low severity per clean-routes re-audit; acceptable either way.
async function getUser() {
  const { data: { user } } = await supabase.auth.getUser();
  return user;
}

// --- Case 5: Assignment to later-checked variable (not a destructure) ---
async function noDestructure(id: string) {
  const result = await supabase.from('content_items').select('*').eq('id', id);
  if (result.error) throw result.error;
  return result.data;
}
