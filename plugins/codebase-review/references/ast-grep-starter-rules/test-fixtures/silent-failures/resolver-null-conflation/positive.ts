// Fixture for resolver-null-conflation — positive cases
// Source: Knowledge Hub S151 audit M6.

declare const supabase: any;

// --- Case 1: M6 pattern — resolveGuideId ---
export async function resolveGuideId(slug: string): Promise<string | null> {
  const { data } = await supabase
    .from('guides')
    .select('id')
    .eq('slug', slug)
    .single();
  return data?.id ?? null;
}

// --- Case 2: Variant — resolveUserRoleByEmail ---
export async function resolveUserRoleByEmail(email: string): Promise<string | null> {
  const { data } = await supabase
    .from('user_roles')
    .select('role')
    .eq('email', email)
    .single();
  return data?.role ?? null;
}

// --- Case 3: Variant with nullable maybeSingle ---
export async function findProfileSlug(userId: string): Promise<string | null> {
  const { data } = await supabase
    .from('profiles')
    .select('slug')
    .eq('id', userId)
    .maybeSingle();
  return data?.slug ?? null;
}
