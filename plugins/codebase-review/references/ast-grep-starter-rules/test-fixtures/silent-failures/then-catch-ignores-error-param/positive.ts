// Fixture for then-catch-ignores-error-param
declare function fetch(url: string): Promise<Response>;

// --- Chained .then().catch(() => fallback) ---
async function fetchWithFallback1(url: string) {
  const data = await fetch(url).then(r => r.json()).catch(() => null);
  return data;
}

// --- .catch(() => ({})) ---
async function fetchObj(url: string) {
  return await fetch(url).then(r => r.json()).catch(() => ({}));
}

// --- .catch(() => []) array fallback ---
async function fetchList(url: string) {
  return await fetch(url).then(r => r.json()).catch(() => []);
}

// --- Multi-line arrow body with no param ---
async function fetchMulti(url: string) {
  return fetch(url)
    .then(r => r.json())
    .catch(() => {
      return { error: true };
    });
}

// --- .catch(() => undefined) ---
async function fetchOpt(url: string) {
  return fetch(url).then(r => r.json()).catch(() => undefined);
}
