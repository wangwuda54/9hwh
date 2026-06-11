const SESSION_COOKIE = "admin_session";

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

function clearCookie() {
  return `${SESSION_COOKIE}=; HttpOnly; Secure; SameSite=Strict; Path=/; Max-Age=0; Expires=Thu, 01 Jan 1970 00:00:00 GMT`;
}

export function onRequest(context) {
  if (!["GET", "POST"].includes(context.request.method.toUpperCase())) {
    return jsonResponse({ error: "method not allowed" }, 405);
  }
  return jsonResponse({ authenticated: false }, 200, { "set-cookie": clearCookie() });
}
