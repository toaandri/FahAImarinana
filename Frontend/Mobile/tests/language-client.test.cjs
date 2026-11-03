const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');
const ts = require('typescript');

function load(filename, modules, globals = {}) {
  const code = ts.transpileModule(fs.readFileSync(filename, 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022, esModuleInterop: true },
  }).outputText;
  const module = { exports: {} };
  vm.runInNewContext(code, {
    module, exports: module.exports, Headers, Response,
    require: (id) => { if (!(id in modules)) throw new Error('Unexpected dependency: ' + id); return modules[id]; },
    ...globals,
  }, { filename });
  return module.exports;
}

test('mobile forwards the chosen language and keeps source references without inventing a confidence score', async () => {
  const calls = [];
  const service = load(path.join(__dirname, '../src/services/mockData.ts'), {
    './api': { apiRequest: async (route, init) => {
      calls.push({ route, body: init?.body && JSON.parse(init.body) });
      if (route === '/copilot/research') return { reponse: 'Valiny', citations: [{ titre: 'Source originale', url: 'https://example.invalid/source' }] };
      if (route === '/auth/me') return { response_language: 'mg' };
      if (route === '/auth/me/language') return { language: 'fr' };
      return { text: 'Dikanteny', language: 'mg', provider: 'openrouter' };
    }, clearTokens() {}, setTokens() {} },
  });
  const result = await service.sendMessageToAI('Inona ny vaovao?', 'mg');
  assert.equal(calls[0].body.language, 'mg');
  assert.equal(result.confidence, 0);
  assert.equal(result.sources[0], 'Source originale — https://example.invalid/source');
  await service.translateAnswer(result.summary, 'mg');
  assert.equal(calls[1].body.text, 'Valiny');
  assert.equal(calls[1].body.target_language, 'mg');
  assert.equal(result.summary, 'Valiny');
  assert.equal(await service.getResponseLanguage(), 'mg');
  await service.saveResponseLanguage('fr');
  assert.equal(calls.at(-1).body.language, 'fr');
});

test('web sends authenticated bilingual questions and translations through the backend', async () => {
  const calls = [];
  const service = load(path.resolve(__dirname, '../../../Frontends/Web/src/services/api.ts'), {
    'expo-constants': { __esModule: true, default: { expoConfig: { extra: { apiUrl: 'http://localhost:18000/api/v1' } } } },
  }, { fetch: async (url, init) => {
    calls.push({ url, init, body: init.body && JSON.parse(init.body) });
    if (url.endsWith('/auth/login')) return Response.json({ access_token: 'session-only', refresh_token: 'refresh-only' });
    if (url.endsWith('/copilot/translate')) return Response.json({ detail: 'Traduction indisponible' }, { status: 503 });
    return Response.json({ reponse: 'Valiny', citations: [{ url: 'https://example.invalid/source' }], chronologie: [] });
  } });
  await service.login('journalist@example.invalid', 'password123');
  const result = await service.sendMessageToAI('Inona ny vaovao?', 'auto');
  assert.equal(calls[1].body.language, 'auto');
  assert.equal(calls[1].init.headers.get('Authorization'), 'Bearer session-only');
  await assert.rejects(service.translateAnswer(result.reponse, 'mg'), /Traduction indisponible/);
  assert.equal(result.reponse, 'Valiny');
  assert.equal(result.citations[0].url, 'https://example.invalid/source');
});
