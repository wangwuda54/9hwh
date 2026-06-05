const enc = new TextEncoder();
const dec = new TextDecoder();

export async function onRequestGet(context) {
  const user = await requireAuth(context.request, context.env || {});
  return json({ authenticated: Boolean(user), user: user || null });
}

async function requireAuth(request, env) {
  const token = readCookie(request, 'admin_session');
  if (!token || !env.SESSION_SECRET) return null;
  const parts = token.split('.');
  if (parts.length !== 2) return null;
  const expected = await signPart(parts[0], env.SESSION_SECRET);
  if (expected !== parts[1]) return null;
  try {
    const payload = JSON.parse(dec.decode(unbase64url(parts[0])));
    if (!payload.exp || payload.exp < Math.floor(Date.now() / 1000)) return null;
    return payload.user || null;
  } catch (_) {
    return null;
  }
}

async function signPart(value, secret) {
  const key = await crypto.subtle.importKey('raw', enc.encode(secret), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']);
  const sig = await crypto.subtle.sign('HMAC', key, enc.encode(value));
  return base64url(new Uint8Array(sig));
}

function readCookie(request, name) {
  const raw = request.headers.get('Cookie') || '';
  const item = raw.split(';').map((x) => x.trim()).find((x) => x.startsWith(name + '='));
  return item ? decodeURIComponent(item.slice(name.length + 1)) : '';
}

function base64url(bytes) {
  let text = '';
  for (const byte of bytes) text += String.fromCharCode(byte);
  return btoa(text).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/g, '');
}

function unbase64url(value) {
  const padded = value.replace(/-/g, '+').replace(/_/g, '/') + '='.repeat((4 - (value.length % 4)) % 4);
  return Uint8Array.from(atob(padded), (char) => char.charCodeAt(0));
}

function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      'Content-Type': 'application/json; charset=utf-8',
      'Cache-Control': 'no-store'
    }
  });
}
