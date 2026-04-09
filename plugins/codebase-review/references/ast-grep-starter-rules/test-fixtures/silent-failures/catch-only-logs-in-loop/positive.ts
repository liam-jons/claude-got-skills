// Fixture for catch-only-logs-in-loop — positive cases
// Source: Knowledge Hub S151 audit H13 and variants.
// All cases below should be flagged by the rule.

declare const items: any[];
declare function processItem(x: any): Promise<any>;

// --- Case 1: H13 pattern — for...of loop, try/catch, console.error only ---
async function processAllV1() {
  const results: any[] = [];
  for (const item of items) {
    try {
      const result = await processItem(item);
      results.push(result);
    } catch (err) {
      console.error(`Failed ${item.id}:`, err);
    }
  }
  return { results };
}

// --- Case 2: Variant with console.warn ---
async function processAllV2() {
  const results: any[] = [];
  for (const item of items) {
    try {
      results.push(await processItem(item));
    } catch (err) {
      console.warn('skipping', item, err);
    }
  }
  return results;
}

// --- Case 3: While loop variant ---
async function processWhile() {
  const results: any[] = [];
  let i = 0;
  while (i < items.length) {
    try {
      results.push(await processItem(items[i]));
    } catch (err) {
      console.error(err);
    }
    i++;
  }
  return results;
}

// --- Case 4: Classic for loop ---
async function processForLoop() {
  const results: any[] = [];
  for (let i = 0; i < items.length; i++) {
    try {
      results.push(await processItem(items[i]));
    } catch (err) {
      console.error(`item ${i} failed`, err);
    }
  }
  return results;
}
