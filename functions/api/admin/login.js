const SESSION_COOKIE = "admin_session";
const SESSION_TTL_SECONDS = 60 * 60 * 8;

const jsonHeaders = {
  "content-type": "application/json; charset=utf-8",
  "cache-control": "no-store",
};

function jsonResponse(data, status = 200, headers = {}) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { ...jsonHeaders, ...headers },
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

async function createSession(username, secret) {
  const payload = {
    u: username,
    exp: Math.floor(Date.now() / 1000) + SESSION_TTL_SECONDS,
  };
  const payloadPart = base64UrlEncode(JSON.stringify(payload));
  const signaturePart = await signValue(payloadPart, secret);
  return `${payloadPart}.${signaturePart}`;
}

function sessionCookie(token) {
  return `${SESSION_COOKIE}=${token}; HttpOnly; Secure; SameSite=Strict; Path=/; Max-Age=${SESSION_TTL_SECONDS}`;
}

export async function onRequest(context) {
  if (context.request.method.toUpperCase() !== "POST") {
    return jsonResponse({ error: "method not allowed" }, 405);
  }

  try {
    const { ADMIN_USERNAME, ADMIN_PASSWORD, SESSION_SECRET } = context.env;
    if (!ADMIN_USERNAME || !ADMIN_PASSWORD || !SESSION_SECRET) {
      return jsonResponse({ error: "admin auth is not configured" }, 500);
    }

    const payload = await context.request.json().catch(() => ({}));
    const username = String(payload.username || "");
    const password = String(payload.password || "");
    const valid = safeEqual(username, ADMIN_USERNAME) && safeEqual(password, ADMIN_PASSWORD);
    if (!valid) {
      return jsonResponse({ error: "用户名或密码错误" }, 401);
    }

    const token = await createSession(username, SESSION_SECRET);
    return jsonResponse({ authenticated: true }, 200, { "set-cookie": sessionCookie(token) });
  } catch (error) {
    return jsonResponse({ error: error.message || "login failed" }, 500);
  }
}
