// Fixture for supabase-data-without-error
// Source: Knowledge Hub S151 audit Critical findings C1-C4
// All 4 of these should be flagged by the rule.

declare const supabase: any;

// --- C1: app/api/bids/[id]/responses/draft/route.ts:156 ---
async function draftC1(question: any, matchedIds: string[], model_tier: string) {
  if (matchedIds.length > 0) {
    const { data: contentItems } = await supabase
      .from('content_items')
      .select('id, suggested_title, content, content_type, ai_summary')
      .in('id', matchedIds);

    const matchedContent = (contentItems ?? []).map((item: any) => ({ id: item.id }));
    return matchedContent;
  }
  return [];
}

// --- C2: app/api/bids/[id]/responses/draft-all/route.ts:174 ---
async function draftC2(matchedIds: string[]) {
  const { data: contentItems } = await supabase
    .from('content_items')
    .select('id, suggested_title, content, content_type, ai_summary')
    .in('id', matchedIds);
  return contentItems;
}

// --- C3: app/api/bids/[id]/responses/draft-stream/route.ts:116 ---
async function draftC3(matchedIds: string[]) {
  const { data: contentItems } = await supabase
    .from('content_items')
    .select('id, suggested_title, content, content_type, ai_summary')
    .in('id', matchedIds);
  return contentItems;
}

// --- C4a: app/api/bids/[id]/outcome/integrate/route.ts:75 ---
async function integrateC4a(id: string, questionIds: string[]) {
  const { data: questions } = await supabase
    .from('bid_questions')
    .select('id, question_text')
    .eq('project_id', id)
    .in('id', questionIds);

  return new Map((questions ?? []).map((q: any) => [q.id, q.question_text]));
}

// --- C4b: app/api/bids/[id]/outcome/integrate/route.ts:85 ---
async function integrateC4b(questionIds: string[]) {
  const { data: responses } = await supabase
    .from('bid_responses')
    .select('question_id, response_text')
    .in('question_id', questionIds);

  return responses;
}
