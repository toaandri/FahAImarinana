const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');
const ts = require('typescript');

function load(filename, modules, globals = {}) {
  modules = { './media': {}, ...modules };
  const code = ts.transpileModule(fs.readFileSync(filename, 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022, esModuleInterop: true },
  }).outputText;
  const module = { exports: {} };
  vm.runInNewContext(code, {
    module, exports: module.exports, Headers, Response, URL, __DEV__: false,
    require: (id) => { if (!(id in modules)) throw new Error('Unexpected dependency: ' + id); return modules[id]; },
    ...globals,
  }, { filename });
  return module.exports;
}

test('mobile registers with email/password and stores the returned session', async () => {
  const calls = [];
  const tokens = [];
  const service = load(path.join(__dirname, '../src/services/mockData.ts'), {
    './api': {
      apiRequest: async (route, init) => {
        calls.push({ route, body: JSON.parse(init.body) });
        return { access_token: 'access-session', refresh_token: 'refresh-session' };
      },
      clearTokens() {},
      setTokens: (value) => tokens.push(value),
    },
  });

  await service.register('user@example.test', 'password123');

  assert.deepEqual(calls, [{
    route: '/auth/register',
    body: { email: 'user@example.test', mot_de_passe: 'password123' },
  }]);
  assert.deepEqual(tokens, [{ access_token: 'access-session', refresh_token: 'refresh-session' }]);
});

test('mobile reads submitted articles in the editorial news list', async () => {
  const calls = [];
  const service = load(path.join(__dirname, '../src/services/mockData.ts'), {
    './api': { apiRequest: async (path) => { calls.push(path); return [{ id: 1, content: '[Sport] Un titre\n\nUn texte', status: 'submitted' }]; } },
  });
  const articles = await service.getEditorialContributions();
  const parsed = service.parseContribution(articles[0].content);
  assert.equal(calls[0], '/editorial/contributions');
  assert.equal(parsed.title, 'Un titre');
  assert.equal(parsed.category, 'Sport');
  assert.equal(parsed.body, 'Un texte');
});

test('mobile deletes a contribution through the authenticated API client', async () => {
  let call;
  const service = load(path.join(__dirname, '../src/services/mockData.ts'), {
    './api': { apiRequest: async (path, init) => { call = { path, method: init.method }; } },
  });
  await service.deleteContribution(42);
  assert.equal(call.path, '/contributions/42');
  assert.equal(call.method, 'DELETE');
});

test('mobile forwards the chosen language and keeps source references without inventing a confidence score', async () => {
  const calls = [];
  const service = load(path.join(__dirname, '../src/services/mockData.ts'), {
    './api': { apiRequest: async (route, init) => {
      calls.push({ route, body: init?.body && JSON.parse(init.body) });
      if (route === '/copilot/research') return { reponse: 'Valiny', citations: [{ titre: 'Source originale', url: 'https://example.invalid/source' }] };
      if (route === '/auth/me') return { response_language: 'mg' };
      if (route === '/auth/me/language') return { language: 'fr' };
      if (route === '/copilot/credibility') return { corroboration_percent: 50, supports: 1, contradicts: 1, inconclusive: 0, source_groups: 2, excluded_duplicates: 0 };
      return { text: 'Dikanteny', language: 'mg', provider: 'openrouter' };
    }, clearTokens() {}, setTokens() {} },
  });
  const result = await service.sendMessageToAI('Inona ny vaovao?', 'mg');
  const analysis = service.articleAnalysisQuestion({ title: 'Un titre', excerpt: 'Un extrait', url: 'https://news.example/article' });
  assert.match(analysis, /Un titre/);
  assert.match(analysis, /Un extrait/);
  assert.match(analysis, /https:\/\/news.example\/article/);
  assert.match(analysis, /sources indépendantes/);
  assert.ok(service.articleAnalysisQuestion({ title: 't'.repeat(1000), excerpt: 'e'.repeat(2000), url: 'https://example.invalid/' + 'x'.repeat(1000) }).length <= 2000);
  assert.equal(calls[0].body.language, 'mg');
  assert.equal(result.confidence, null);
  assert.equal(result.sources[0], 'Source originale — https://example.invalid/source');
  await service.translateAnswer(result.summary, 'mg');
  assert.equal(calls[1].body.text, 'Valiny');
  assert.equal(calls[1].body.target_language, 'mg');
  assert.equal(result.summary, 'Valiny');
  assert.equal(await service.getResponseLanguage(), 'mg');
  await service.saveResponseLanguage('fr');
  assert.equal(calls.at(-1).body.language, 'fr');
  const statistics = await service.calculateCorroboration('Une affirmation', [
    { url: 'https://example.org/a', assessment: 'supports' },
    { url: 'https://example.net/b', assessment: 'contradicts' },
  ]);
  assert.equal(calls.at(-1).route, '/copilot/credibility');
  assert.equal(calls.at(-1).body.sources[1].assessment, 'contradicts');
  assert.equal(statistics.corroboration_percent, 50);
});

test('web sends authenticated bilingual questions and translations through the backend', async () => {
  const calls = [];
  const service = load(path.resolve(__dirname, '../../../Frontends/Web/src/services/api.ts'), {
    'expo-constants': { __esModule: true, default: { expoConfig: { extra: { apiUrl: 'http://localhost:18000/api/v1' } } } },
  }, { fetch: async (url, init) => {
    calls.push({ url, init, body: init.body && JSON.parse(init.body) });
    if (url.endsWith('/auth/login')) return Response.json({ access_token: 'session-only', refresh_token: 'refresh-only' });
    if (url.endsWith('/copilot/translate')) return Response.json({ detail: 'Traduction indisponible' }, { status: 503 });
    if (url.endsWith('/copilot/credibility')) return Response.json({ corroboration_percent: null, supports: 1, contradicts: 0, inconclusive: 0 });
    return Response.json({ reponse: 'Valiny', citations: [{ url: 'https://example.invalid/source' }], chronologie: [] });
  } });
  await service.login('journalist@example.invalid', 'password123');
  assert.match(service.articleAnalysisQuestion({ title: 'Un titre', url: 'https://news.example/article' }), /sources indépendantes/);
  const result = await service.sendMessageToAI('Inona ny vaovao?', 'auto');
  assert.equal(calls[1].body.language, 'auto');
  assert.equal(calls[1].init.headers.get('Authorization'), 'Bearer session-only');
  await assert.rejects(service.translateAnswer(result.reponse, 'mg'), /Traduction indisponible/);
  assert.equal(result.reponse, 'Valiny');
  assert.equal(result.citations[0].url, 'https://example.invalid/source');
  const insufficient = await service.calculateCorroboration('Une affirmation', [{ url: 'https://example.org/a', assessment: 'supports' }]);
  assert.equal(insufficient.corroboration_percent, null);
  assert.equal(calls.at(-1).init.headers.get('Authorization'), 'Bearer session-only');
});
