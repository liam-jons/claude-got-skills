// Fixture for supabase-mutation-discarded — negative cases
declare const supabase: any;

// --- Case 1: Destructure { error } and check ---
async function correctDestructureError(id: string, updates: any) {
  const { error } = await supabase.from('content_items').update(updates).eq('id', id);
  if (error) throw error;
  return { ok: true };
}

// --- Case 2: Assign to variable and check .error ---
async function correctAssign(id: string, updates: any) {
  const result = await supabase.from('content_items').update(updates).eq('id', id);
  if (result.error) throw result.error;
  return { ok: true };
}

// --- Case 3: Return the await expression directly (caller handles) ---
async function returnDirect(id: string, updates: any) {
  return await supabase.from('content_items').update(updates).eq('id', id);
}

// --- Case 4: SELECT is not a mutation ---
async function selectRows(id: string) {
  const { data, error } = await supabase.from('content_items').select('*').eq('id', id);
  if (error) throw error;
  return data;
}

// --- Case 5: Destructure { data, error } from a mutation ---
async function correctDataError(id: string, updates: any) {
  const { data, error } = await supabase.from('content_items').update(updates).eq('id', id).select().single();
  if (error) throw error;
  return data;
}
