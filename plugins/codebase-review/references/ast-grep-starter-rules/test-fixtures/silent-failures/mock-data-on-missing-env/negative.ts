// Fixture for mock-data-on-missing-env — negative cases
declare const process: { env: Record<string, string | undefined> };

// --- Case 1: Fail-fast throw on missing env (the correct pattern) ---
function getKey() {
  if (!process.env.API_KEY) {
    throw new Error('API_KEY is required');
  }
  return process.env.API_KEY;
}

// --- Case 2: Return null, not mock data (ambiguous but not the flagged pattern) ---
async function optionalService() {
  if (!process.env.OPTIONAL_URL) {
    return null;
  }
  return await fetch(process.env.OPTIONAL_URL);
}

// --- Case 3: Return real fallback (not named mock/sample/fake) ---
function getEnvValue() {
  if (!process.env.MY_VAR) {
    return 'default';
  }
  return process.env.MY_VAR;
}

// --- Case 4: Return 503 error response ---
async function apiHandler() {
  if (!process.env.DOWNSTREAM_URL) {
    return new Response(JSON.stringify({ error: 'not configured' }), { status: 503 });
  }
  return await fetch(process.env.DOWNSTREAM_URL);
}

// --- Case 5: NODE_ENV-gated mock (the correct dev shim pattern) ---
async function devOrReal() {
  if (process.env.NODE_ENV !== 'production') {
    return mockEmbeddings;
  }
  return await realEmbed('hello');
}

const mockEmbeddings = [[0.1]];
declare function fetch(url: string): Promise<any>;
declare function realEmbed(s: string): Promise<any>;
