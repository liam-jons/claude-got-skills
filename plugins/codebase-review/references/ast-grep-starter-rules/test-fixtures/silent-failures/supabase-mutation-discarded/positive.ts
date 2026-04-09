// Fixture for supabase-mutation-discarded
// Source: Knowledge Hub S151 audit finding H5 (and variants)
// All 4+ mutations below should be flagged.

declare const supabase: any;

// --- H5: app/api/items/[id]/metadata/route.ts:64 — update discarded ---
async function updateMetadata(id: string, columnUpdates: any) {
  await supabase.from('content_items').update(columnUpdates).eq('id', id);
  return { id, updated: true };
}

// --- insert discarded ---
async function logAction(userId: string, action: string) {
  await supabase.from('audit_log').insert({ user_id: userId, action });
  return { ok: true };
}

// --- upsert discarded ---
async function upsertProfile(userId: string, data: any) {
  await supabase.from('profiles').upsert({ id: userId, ...data });
  return { profile: userId };
}

// --- delete discarded ---
async function deleteItem(id: string) {
  await supabase.from('content_items').delete().eq('id', id);
  return { deleted: id };
}

// --- chained eq() after update, result still discarded ---
async function markComplete(id: string) {
  await supabase.from('tasks').update({ status: 'done' }).eq('id', id).eq('owner', 'self');
  return true;
}
