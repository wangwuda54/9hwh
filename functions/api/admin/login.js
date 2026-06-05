export async function onRequestPost(context) {
  const env = context.env || {};
  const body = await readJson(context.request);
  const ok = String(body.username || '') === String(env.ADMIN_USERNAME || '') && String(body.password || '') === String(env.ADMIN_PASSWORD || '');
  if (!ok) return json({ authenticated: false, message: '用户名或密码错误。' }, 401);

  const maxAge = body.remember === false ? 21600 : 2592000;
  const token = await sign({ user: body.username, exp: Math.floor(Date.now() / 1000) + maxAge }, String(env.SESSION_SECRET || ''));
  return json({ authenticated: true, remember: maxAge > 21600 }, 200, {
    'Set-Cookie': `admin_session=${encodeURIComponent(token)}; Path=/; HttpOnly; Secure; SameSite=Strict; Max-Age=${maxAge}`
  });
}

async function readJson(request) {
  try { return await request.json(); } catch (_) { return {}; }
}
function json(data, status = 200, headers = {}) {
  return new Response(JSON.stringify(data), { status, headers: { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store', ...headers } });
}
async function sign(payload, secret) {
  const enc = new TextEncoder();
  const data = b64(enc.encode(JSON.stringify(payload)));
  const key = await crypto.subtle.importKey('raw', enc.encode(secret), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']);
  const sig = await crypto.subtle.sign('HMAC', key, enc.encode(data));
  return `${data}.${b64(new Uint8Array(sig))}`;
}
function b64(bytes) {
  let s = '';
  for (const b of bytes) s += String.fromCharCode(b);
  return btoa(s).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/g, '');
}
