const SESSION_COOKIE = "admin_session";

const jsonHeaders = {
  "content-type": "application/json; charset=utf-8",
  "cache-control": "no-store",
};

function jsonResponse(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: jsonHeaders,
  });
}

function base64UrlEncode(value) {
  const bytes = typeof value === "string" ? new TextEncoder().encode(value) : value;
  let binary = "";
  for (const byte of bytes) {
    binary += String.fromCharCode(byte);
  }
  return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/g, "");
}

function base64UrlDecode(value) {
  const base64 = value.replace(/-/g, "+").replace(/_/g, "/").padEnd(Math.ceil(value.length / 4) * 4, "=");
  const binary = atob(base64);
  return Uint8Array.from(binary, (char) => char.charCodeAt(0));
}

function safeEqual(a, b) {
  if (a.length !== b.length) {
    return false;
  }
  let diff = 0;
  for (let index = 0; index < a.length; index += 1) {
    diff |= a.charCodeAt(index) ^ b.charCodeAt(index);
  }
  return diff === 0;
}

async function signValue(value, secret) {
  const key = await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"]
  );
  const signature = await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(value));
  return base64UrlEncode(new Uint8Array(signature));
}

function readCookie(request, name) {
  const cookie = request.headers.get("cookie") || "";
  for (const part of cookie.split(";")) {
    const [key, ...rest] = part.trim().split("=");
    if (key === name) {
      return rest.join("=");
    }
  }
  return "";
}

async function isAuthenticated(request, env) {
  if (!env.SESSION_SECRET) {
    return false;
  }
  const token = readCookie(request, SESSION_COOKIE);
  const [payloadPart, signaturePart] = token.split(".");
  if (!payloadPart || !signaturePart) {
    return false;
  }
  const expected = await signValue(payloadPart, env.SESSION_SECRET);
  if (!safeEqual(signaturePart, expected)) {
    return false;
  }
  try {
    const payload = JSON.parse(new TextDecoder().decode(base64UrlDecode(payloadPart)));
    return Boolean(payload.exp && payload.exp > Math.floor(Date.now() / 1000));
  } catch {
    return false;
  }
}

export async function onRequest(context) {
  if (context.request.method.toUpperCase() !== "GET") {
    return jsonResponse({ error: "method not allowed" }, 405);
  }
  return jsonResponse({ authenticated: await isAuthenticated(context.request, context.env) });
}
