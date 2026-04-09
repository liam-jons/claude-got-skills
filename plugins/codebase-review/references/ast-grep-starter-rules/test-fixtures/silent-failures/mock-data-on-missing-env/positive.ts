// Fixture for mock-data-on-missing-env
declare const process: { env: Record<string, string | undefined> };

const mockEmbeddings = [[0.1, 0.2]];
const sampleUsers = [{ id: 1, name: 'sample' }];
const fakeInvoices: any[] = [];
const placeholderContent = 'lorem ipsum';
const fixtureData = { stubbed: true };

// --- Case 1: Direct early return with mock identifier ---
async function getEmbeddings(text: string) {
  if (!process.env.OPENAI_API_KEY) {
    return mockEmbeddings;
  }
  return await realEmbed(text);
}

// --- Case 2: Multi-statement body, returns sample ---
async function getUsers() {
  if (!process.env.AUTH_URL) {
    console.log('Auth disabled, returning sample users');
    return sampleUsers;
  }
  return await fetchUsers();
}

// --- Case 3: fakeX variable ---
async function getInvoices() {
  if (!process.env.STRIPE_KEY) {
    return fakeInvoices;
  }
  return [];
}

// --- Case 4: placeholderContent ---
function getContent() {
  if (!process.env.CMS_URL) {
    return placeholderContent;
  }
  return 'real';
}

// --- Case 5: fixtureData ---
async function getData() {
  if (!process.env.DB_URL) {
    return fixtureData;
  }
  return {};
}

declare function realEmbed(s: string): Promise<any>;
declare function fetchUsers(): Promise<any>;
