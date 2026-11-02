const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');
const ts = require('typescript');

function loadService(name, modules, extra = {}) {
  const filename = path.join(__dirname, '../src/services', name + '.ts');
  const code = ts.transpileModule(fs.readFileSync(filename, 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022, esModuleInterop: true },
  }).outputText;
  const module = { exports: {} };
  vm.runInNewContext(code, { module, exports: module.exports,
    require: (id) => { if (!(id in modules)) throw new Error('Unexpected dependency: ' + id); return modules[id]; },
    URL, Headers, Response, AbortController, setTimeout, clearTimeout,
    process: { env: {} }, __DEV__: true, ...extra }, { filename });
  return module.exports;
}

test('physical phone resolves localhost against the private Metro host and sends only the session token', async () => {
  const requests = [];
  const cleared = [];
  const api = loadService('api', {
    'expo-constants': { __esModule: true, default: { expoConfig: {
      extra: { apiUrl: 'http://localhost:18000/api/v1' }, hostUri: '192.168.1.12:8081' } } },
    './video-session': { setVideoReport: (value) => cleared.push(value) },
  }, { fetch: async (url, init) => { requests.push({ url, init }); return Response.json({ configured: true }); } });
  api.setTokens({ access_token: 'session-only', refresh_token: 'refresh-only' });
  await api.apiRequest('/vision/status');
  assert.equal(requests[0].url, 'http://192.168.1.12:18000/api/v1/vision/status');
  assert.equal(requests[0].init.headers.get('Authorization'), 'Bearer session-only');
  assert.equal(requests[0].init.headers.get('x-goog-api-key'), null);
  api.clearTokens(); assert.equal(cleared.at(-1), null);
});

test('explicit public API URL overrides app configuration without changing a non-local host', async () => {
  let address;
  const api = loadService('api', {
    'expo-constants': { __esModule: true, default: { expoConfig: { hostUri: '192.168.1.12:8081' } } },
    './video-session': { setVideoReport() {} },
  }, { process: { env: { EXPO_PUBLIC_API_URL: 'https://backend.example.invalid/api/v1' } },
    fetch: async (url) => { address = url; return Response.json({ configured: true }); } });
  await api.apiRequest('/vision/status');
  assert.equal(address, 'https://backend.example.invalid/api/v1/vision/status');
});

test('aborting an upload cancels the actual fetch and leaves no hanging request', async () => {
  const api = loadService('api', {
    'expo-constants': { __esModule: true, default: {} }, './video-session': { setVideoReport() {} },
  }, { fetch: (_url, init) => new Promise((_resolve, reject) => {
    init.signal.addEventListener('abort', () => reject(new Error('aborted')));
  }) });
  const abort = new AbortController();
  const pending = api.apiRequest('/vision/video', { method: 'POST', signal: abort.signal });
  abort.abort(); await assert.rejects(pending, /interrompue/);
});

test('video input preserves capture metadata and maps camera MOV files without a Google key', async () => {
  let request;
  class FakeFile {
    constructor() { this.exists = true; this.size = 128; }
    async base64() { return 'explicit-test-container'; }
  }
  const vision = loadService('vision', {
    'expo-file-system': { File: FakeFile },
    './api': { apiRequest: async (route, init) => { request = { route, body: JSON.parse(init.body) }; return { status: 'completed' }; } },
  });
  await vision.analyzeVideoClip('test-capture', { sequence: 2, uri: 'file:///private/test.mov',
    capturedAt: '2026-11-03T10:00:00Z', durationSeconds: 6 }, 4 * 1024 * 1024);
  assert.equal(request.route, '/vision/video');
  assert.equal(request.body.mime_type, 'video/quicktime');
  assert.equal(request.body.sequence, 2); assert.equal(request.body.video_base64, 'explicit-test-container');
  assert.equal('GEMINI_API_KEY' in request.body, false);
});

test('oversized local videos are rejected before reading base64 or sending a request', async () => {
  class FakeFile {
    constructor() { this.exists = true; this.size = 5 * 1024 * 1024; }
    async base64() { throw new Error('Must not read oversized footage'); }
  }
  const vision = loadService('vision', { 'expo-file-system': { File: FakeFile },
    './api': { apiRequest() { throw new Error('Must not upload'); } } });
  await assert.rejects(vision.analyzeVideoClip('capture', { uri: 'file:///large.mp4' }, 4 * 1024 * 1024), /4 Mio/);
});
