// Fixture for then-catch-ignores-error-param — negative cases
declare function fetch(url: string): Promise<Response>;

// --- Case 1: .catch with named error param ---
async function correctNamed(url: string) {
  return fetch(url).then(r => r.json()).catch((err) => {
    console.error('fetch failed', err);
    return null;
  });
}

// --- Case 2: .catch with destructured error ---
async function correctDestructured(url: string) {
  return fetch(url).then(r => r.json()).catch(({ message }) => {
    console.error(message);
    return null;
  });
}

// --- Case 3: .catch with _ placeholder (still receives the error) ---
// This is arguably a FALSE POSITIVE filter — the `_` identifier IS a parameter name.
// Acceptable if the rule flags this case; it's a low-severity catch.
async function underscorePlaceholder(url: string) {
  return fetch(url).then(r => r.json()).catch((_) => null);
}

// --- Case 4: try/catch (covered by different rule) ---
async function tryNotThen(url: string) {
  try {
    const r = await fetch(url);
    return await r.json();
  } catch (err) {
    console.error(err);
    return null;
  }
}

// --- Case 5: .catch with handler function reference (not an inline arrow) ---
const handleError = (err: Error) => { console.error(err); return null; };
async function referencedHandler(url: string) {
  return fetch(url).then(r => r.json()).catch(handleError);
}
