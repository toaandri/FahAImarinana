const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');
const ts = require('typescript');

function loadService(name, modules, extra = {}) {
  modules = { 'react-native': { Platform: { OS: 'web' } }, 'expo-secure-store': {}, './media': {}, ...modules };
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

test('native session is restored securely before an analysis request', async () => {
  let stored = null;
  let authorization;
  const secureStore = {
    setItemAsync: async (_key, value) => { stored = value; },
    getItemAsync: async () => stored,
    deleteItemAsync: async () => { stored = null; },
  };
  const modules = {
    'react-native': { Platform: { OS: 'android' } },
    'expo-secure-store': secureStore,
    'expo-constants': { __esModule: true, default: {} },
    './video-session': { setVideoReport() {} },
  };
  const first = loadService('api', modules);
  first.setTokens({ access_token: 'access-test', refresh_token: 'refresh-test' });
  await first.restoreTokens();
  const second = loadService('api', modules, { fetch: async (_url, init) => {
    authorization = init.headers.get('Authorization');
    return Response.json({});
  } });
  await second.restoreTokens();
  await second.apiRequest('/copilot/precompute');
  assert.equal(authorization, 'Bearer access-test');
});

test('publication image is sent to the private analysis endpoint', async () => {
  let call;
  const service = loadService('vision', {
    'expo-file-system': { File: class {} },
    './media': { readMediaBase64: async () => 'cGljdHVyZQ==' },
    './api': { apiRequest: async (path, options) => {
      call = { path, body: JSON.parse(options.body) };
      return { labels: ['Tree'], text: '', notice: 'À vérifier' };
    } },
  });
  const result = await service.analyzePublicationMedia({ uri: 'file:///photo.png', type: 'image' });
  assert.equal(call.path, '/vision/image');
  assert.equal(call.body.image_base64, 'cGljdHVyZQ==');
  assert.equal(result.labels[0], 'Tree');
  assert.equal(result.score, undefined);
});

test('native publication media uses local filesystem and checks size before reading', async () => {
  let reads = 0;
  class FakeFile {
    constructor(uri) { this.exists = true; this.size = uri.includes('large') ? 101 : 100; }
    async base64() { reads++; return 'cGljdHVyZQ=='; }
  }
  const media = loadService('media', { 'expo-file-system': { File: FakeFile }, 'react-native': { Platform: { OS: 'android' } } });
  assert.equal(await media.readMediaBase64('file:///photo.png', 100), 'cGljdHVyZQ==');
  await assert.rejects(media.readMediaBase64('file:///large.png', 100), /dépasse/);
  assert.equal(reads, 1);
});

test('simultaneous expired requests share one refresh and retain the new session', async () => {
  let refreshCalls = 0;
  const api = loadService('api', {
    'expo-constants': { __esModule: true, default: {} },
    './video-session': { setVideoReport() {} },
  }, { fetch: async (url, init) => {
    if (url.endsWith('/auth/refresh')) {
      refreshCalls++;
      await new Promise((resolve) => setTimeout(resolve, 10));
      return Response.json({ access_token: 'new-access', refresh_token: 'new-refresh' });
    }
    return init.headers.get('Authorization') === 'Bearer new-access'
      ? Response.json({ ok: true }) : Response.json({ detail: 'expired' }, { status: 401 });
  } });
  api.setTokens({ access_token: 'expired', refresh_token: 'old-refresh' });
  const responses = await Promise.all([api.apiRequest('/auth/me'), api.apiRequest('/copilot/precompute')]);
  assert.equal(refreshCalls, 1);
  assert.ok(responses.every((response) => response.ok));
});

test('editorial photo uses authenticated media endpoint and restores expired session', async () => {
  let attempts = 0;
  class FakeReader {
    readAsDataURL(blob) { this.result = `data:${blob.type};base64,cGhvdG8=`; this.onload(); }
  }
  const api = loadService('api', {
    'expo-constants': { __esModule: true, default: {} },
    './video-session': { setVideoReport() {} },
  }, { FileReader: FakeReader, fetch: async (url, init) => {
    if (url.endsWith('/auth/refresh')) return Response.json({ access_token: 'new-access', refresh_token: 'new-refresh' });
    assert.ok(url.endsWith('/editorial/contributions/12/media'));
    attempts++;
    if (init.headers.get('Authorization') !== 'Bearer new-access') return Response.json({}, { status: 401 });
    return new Response('photo', { headers: { 'Content-Type': 'image/png' } });
  } });
  api.setTokens({ access_token: 'expired', refresh_token: 'old-refresh' });
  assert.equal(await api.editorialImageDataUrl(12), 'data:image/png;base64,cGhvdG8=');
  assert.equal(attempts, 2);
});

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
