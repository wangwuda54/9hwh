const DATA_PATH = "site_src/data/admin_posts.json";
const DEFAULT_REPO = "wangwuda54/9hwh";
const DEFAULT_BRANCH = "main";
const VALID_STATUSES = new Set(["draft", "published", "archived"]);
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

async function verifySession(request, env) {
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

async function requireAuth(request, env) {
  const authenticated = await verifySession(request, env);
  if (!authenticated) {
    return jsonResponse({ error: "unauthorized" }, 401);
  }
  return null;
}

function nowIso() {
  return new Date().toISOString();
}

function slugify(value) {
  return String(value || "")
    .trim()
    .toLowerCase()
    .replace(/['"]/g, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 80);
}

function normalizeTags(value) {
  if (Array.isArray(value)) {
    return value.map((tag) => String(tag).trim()).filter(Boolean);
  }
  return String(value || "")
    .split(",")
    .map((tag) => tag.trim())
    .filter(Boolean);
}

function normalizeData(data) {
  const posts = Array.isArray(data?.posts) ? data.posts : [];
  return {
    version: 1,
    updatedAt: data?.updatedAt || "",
    posts: posts.map((post) => ({
      id: String(post.id || ""),
      slug: String(post.slug || ""),
      title: String(post.title || ""),
      summary: String(post.summary || ""),
      content: String(post.content || ""),
      tags: normalizeTags(post.tags),
      status: VALID_STATUSES.has(post.status) ? post.status : "draft",
      createdAt: String(post.createdAt || ""),
      updatedAt: String(post.updatedAt || ""),
      publishedAt: String(post.publishedAt || ""),
    })),
  };
}

function githubConfig(env) {
  return {
    repo: env.GITHUB_REPO || DEFAULT_REPO,
    branch: env.GITHUB_BRANCH || env.CF_PAGES_BRANCH || DEFAULT_BRANCH,
    token: env.GITHUB_TOKEN || env.GH_TOKEN,
  };
}

function githubHeaders(token) {
  return {
    accept: "application/vnd.github+json",
    authorization: `Bearer ${token}`,
    "content-type": "application/json",
    "user-agent": "9hwh-admin-publisher",
    "x-github-api-version": "2022-11-28",
  };
}

function githubFileUrl(repo) {
  return `https://api.github.com/repos/${repo}/contents/${DATA_PATH}`;
}

function decodeBase64(value) {
  return decodeURIComponent(
    Array.from(Uint8Array.from(atob(value), (char) => char.charCodeAt(0)))
      .map((byte) => `%${byte.toString(16).padStart(2, "0")}`)
      .join("")
  );
}

function encodeBase64(value) {
  const bytes = new TextEncoder().encode(value);
  let binary = "";
  for (const byte of bytes) {
    binary += String.fromCharCode(byte);
  }
  return btoa(binary);
}

async function readGitHubData(env) {
  const { repo, branch, token } = githubConfig(env);
  if (!token) {
    throw new Error("missing GITHUB_TOKEN");
  }

  const url = `${githubFileUrl(repo)}?ref=${encodeURIComponent(branch)}`;
  const response = await fetch(url, { headers: githubHeaders(token) });
  if (response.status === 404) {
    return { repo, branch, token, sha: null, data: normalizeData({}) };
  }
  if (!response.ok) {
    throw new Error(`GitHub read failed: ${response.status}`);
  }

  const file = await response.json();
  const text = decodeBase64(String(file.content || "").replace(/\s/g, ""));
  return { repo, branch, token, sha: file.sha, data: normalizeData(JSON.parse(text)) };
}

async function writeGitHubData(context, data, message) {
  const body = {
    message,
    branch: context.branch,
    content: encodeBase64(JSON.stringify(data, null, 2) + "\n"),
  };
  if (context.sha) {
    body.sha = context.sha;
  }

  const response = await fetch(githubFileUrl(context.repo), {
    method: "PUT",
    headers: githubHeaders(context.token),
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw new Error(`GitHub write failed: ${response.status}`);
  }
  return response.json();
}

function postFromPayload(payload, existing) {
  const timestamp = nowIso();
  const title = String(payload.title || existing?.title || "").trim();
  const slug = slugify(payload.slug || existing?.slug || title);
  if (!title) {
    throw new Error("title is required");
  }
  if (!slug) {
    throw new Error("slug is required");
  }

  const requestedStatus = payload.status || existing?.status || "draft";
  const status = VALID_STATUSES.has(requestedStatus) ? requestedStatus : "draft";
  const wasPublished = existing?.status === "published";

  return {
    id: existing?.id || String(payload.id || `post-${Date.now()}`),
    slug,
    title,
    summary: String(payload.summary || ""),
    content: String(payload.content || ""),
    tags: normalizeTags(payload.tags),
    status,
    createdAt: existing?.createdAt || timestamp,
    updatedAt: timestamp,
    publishedAt: status === "published" ? existing?.publishedAt || timestamp : wasPublished ? existing?.publishedAt || "" : "",
  };
}

async function handleGet(env) {
  const context = await readGitHubData(env);
  const posts = [...context.data.posts].sort((a, b) => String(b.updatedAt).localeCompare(String(a.updatedAt)));
  return jsonResponse({ ...context.data, posts });
}

async function handleWrite(request, env) {
  const payload = await request.json().catch(() => ({}));
  const action = String(payload.action || "save");
  const context = await readGitHubData(env);
  const data = context.data;
  const posts = data.posts;
  const index = posts.findIndex((post) => post.id === payload.id || (payload.slug && post.slug === payload.slug));
  const existing = index >= 0 ? posts[index] : null;

  if (action === "archive") {
    if (!existing) {
      return jsonResponse({ error: "post not found" }, 404);
    }
    posts[index] = { ...existing, status: "archived", updatedAt: nowIso() };
  } else {
    const nextPayload = { ...payload };
    if (action === "publish") {
      nextPayload.status = "published";
    } else if (action === "draft") {
      nextPayload.status = "draft";
    }

    const nextPost = postFromPayload(nextPayload, existing);
    const duplicate = posts.find((post) => post.slug === nextPost.slug && post.id !== nextPost.id);
    if (duplicate) {
      return jsonResponse({ error: "slug already exists" }, 409);
    }

    if (index >= 0) {
      posts[index] = nextPost;
    } else {
      posts.unshift(nextPost);
    }
  }

  data.updatedAt = nowIso();
  await writeGitHubData(context, data, `admin publish: update ${DATA_PATH}`);
  const saved = index >= 0 ? posts[index] : posts[0];
  const publicUrl = saved?.slug ? `/publish/${saved.slug}/` : "/publish/";
  return jsonResponse({
    ok: true,
    post: saved,
    publicUrl,
    message: `已保存到 GitHub。等待 Cloudflare 自动部署完成后，访问 ${publicUrl}。`,
  });
}

export async function onRequest(context) {
  try {
    const method = context.request.method.toUpperCase();
    if (!["GET", "POST", "PUT"].includes(method)) {
      return jsonResponse({ error: "method not allowed" }, 405);
    }

    const authError = await requireAuth(context.request, context.env);
    if (authError) {
      return authError;
    }

    if (method === "GET") {
      return handleGet(context.env);
    }
    return handleWrite(context.request, context.env);
  } catch (error) {
    return jsonResponse({ error: error.message || "admin api failed" }, 500);
  }
}
