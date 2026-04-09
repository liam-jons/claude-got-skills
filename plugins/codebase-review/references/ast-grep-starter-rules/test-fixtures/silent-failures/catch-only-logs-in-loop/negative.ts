// Fixture for catch-only-logs-in-loop — negative cases

declare const items: any[];
declare function processItem(x: any): Promise<any>;

// --- Case 1: Loop with failed[] array — correct pattern ---
async function correctWithFailed() {
  const results: any[] = [];
  const failed: any[] = [];
  for (const item of items) {
    try {
      results.push(await processItem(item));
    } catch (err) {
      failed.push({ id: item.id, error: (err as Error).message });
    }
  }
  return { results, failed };
}

// --- Case 2: Try/catch not inside a loop ---
async function singleTry(item: any) {
  try {
    return await processItem(item);
  } catch (err) {
    console.error(err);
    return null;
  }
}

// --- Case 3: Loop with re-throw in catch ---
async function loopRethrow() {
  const results: any[] = [];
  for (const item of items) {
    try {
      results.push(await processItem(item));
    } catch (err) {
      console.error(err);
      throw err;
    }
  }
  return results;
}

// --- Case 4: Loop with no try/catch ---
async function loopNoCatch() {
  const results: any[] = [];
  for (const item of items) {
    results.push(await processItem(item));
  }
  return results;
}
