const POSTS_DIR = "site_src/data/admin_posts";
const CATALOG_PATH = "site_src/data/admin_posts_catalog.json";
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

function timestampSlug(date = new Date()) {
  const pad = (value) => String(value).padStart(2, "0");
  return `post-${date.getUTCFullYear()}${pad(date.getUTCMonth() + 1)}${pad(date.getUTCDate())}-${pad(date.getUTCHours())}${pad(date.getUTCMinutes())}${pad(date.getUTCSeconds())}`;
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
      keyword: String(post.keyword || ""),
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

function githubApiUrl(repo, path) {
  return `https://api.github.com/repos/${repo}/${path.replace(/^\/+/, "")}`;
}

function encodedRepoPath(path) {
  return path.split("/").map((part) => encodeURIComponent(part)).join("/");
}

function postPath(slug) {
  return `${POSTS_DIR}/${slug[0]}/${slug}.json`;
}

function catalogPost(post) {
  return {
    id: post.id,
    slug: post.slug,
    title: post.title,
    status: post.status,
    updatedAt: post.updatedAt,
    publishedAt: post.publishedAt,
  };
}

function normalizeCatalog(data) {
  const normalized = normalizeData(data);
  return {
    version: 2,
    updatedAt: normalized.updatedAt,
    posts: normalized.posts.map(catalogPost),
  };
}

async function githubJson(config, path, options = {}) {
  const response = await fetch(githubApiUrl(config.repo, path), {
    ...options,
    headers: { ...githubHeaders(config.token), ...(options.headers || {}) },
  });
  if (!response.ok) {
    const error = new Error(`GitHub request failed: ${response.status}`);
    error.status = response.status;
    throw error;
  }
  return response.json();
}

async function branchHead(config) {
  const ref = await githubJson(config, `git/ref/heads/${encodeURIComponent(config.branch)}`);
  return ref.object.sha;
}

async function readTextFile(config, path, ref, missingValue = null) {
  const url = `${githubApiUrl(config.repo, `contents/${encodedRepoPath(path)}`)}?ref=${encodeURIComponent(ref)}`;
  const response = await fetch(url, {
    headers: { ...githubHeaders(config.token), accept: "application/vnd.github.raw+json" },
  });
  if (response.status === 404) {
    return missingValue;
  }
  if (!response.ok) {
    throw new Error(`GitHub raw read failed: ${response.status}`);
  }
  const text = await response.text();
  if (!text.trim()) {
    throw new Error(`GitHub returned empty content for ${path}`);
  }
  return text;
}

async function readCatalog(config, ref) {
  const text = await readTextFile(config, CATALOG_PATH, ref, "");
  return text ? normalizeCatalog(JSON.parse(text)) : normalizeCatalog({});
}

async function commitFiles(config, expectedHead, fileMap, message) {
  const currentHead = await branchHead(config);
  if (currentHead !== expectedHead) {
    const error = new Error("main branch changed; refresh and retry");
    error.status = 409;
    throw error;
  }
  const parentCommit = await githubJson(config, `git/commits/${expectedHead}`);
  const tree = [];
  for (const [path, content] of Object.entries(fileMap)) {
    const blob = await githubJson(config, "git/blobs", {
      method: "POST",
      body: JSON.stringify({ content, encoding: "utf-8" }),
    });
    tree.push({ path, mode: "100644", type: "blob", sha: blob.sha });
  }
  const nextTree = await githubJson(config, "git/trees", {
    method: "POST",
    body: JSON.stringify({ base_tree: parentCommit.tree.sha, tree }),
  });
  const nextCommit = await githubJson(config, "git/commits", {
    method: "POST",
    body: JSON.stringify({ message, tree: nextTree.sha, parents: [expectedHead] }),
  });
  await githubJson(config, `git/refs/heads/${encodeURIComponent(config.branch)}`, {
    method: "PATCH",
    body: JSON.stringify({ sha: nextCommit.sha, force: false }),
  });
  return nextCommit;
}

function postFromPayload(payload, existing) {
  const timestamp = nowIso();
  const title = String(payload.title || existing?.title || "").trim();
  const slug = slugify(payload.slug || existing?.slug) || slugify(title) || timestampSlug();
  if (!title) {
    throw new Error("title is required");
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

async function handleGet(request, env) {
  const config = githubConfig(env);
  if (!config.token) {
    throw new Error("missing GITHUB_TOKEN");
  }
  const head = await branchHead(config);
  const requestedSlug = slugify(new URL(request.url).searchParams.get("slug") || "");
  if (requestedSlug) {
    const text = await readTextFile(config, postPath(requestedSlug), head, null);
    if (text === null) {
      return jsonResponse({ error: "post not found" }, 404);
    }
    const post = normalizeData({ posts: [JSON.parse(text)] }).posts[0];
    return jsonResponse({ post });
  }
  const data = await readCatalog(config, head);
  const posts = [...data.posts].sort((a, b) => String(b.updatedAt).localeCompare(String(a.updatedAt)));
  return jsonResponse({ ...data, posts });
}

async function handleWrite(request, env) {
  const payload = await request.json().catch(() => ({}));
  const action = String(payload.action || "save");
  const config = githubConfig(env);
  if (!config.token) {
    throw new Error("missing GITHUB_TOKEN");
  }
  const head = await branchHead(config);
  const data = await readCatalog(config, head);
  const posts = data.posts;
  const index = posts.findIndex((post) => post.id === payload.id || (payload.slug && post.slug === payload.slug));
  const existingMetadata = index >= 0 ? posts[index] : null;
  let existing = null;
  if (existingMetadata) {
    const text = await readTextFile(config, postPath(existingMetadata.slug), head, null);
    if (text === null) {
      throw new Error(`post file missing: ${existingMetadata.slug}`);
    }
    existing = normalizeData({ posts: [JSON.parse(text)] }).posts[0];
  }

  let saved;

  if (action === "archive") {
    if (!existing) {
      return jsonResponse({ error: "post not found" }, 404);
    }
    saved = { ...existing, status: "archived", updatedAt: nowIso() };
    posts[index] = catalogPost(saved);
  } else {
    const nextPayload = { ...payload };
    if (action === "publish") {
      nextPayload.status = "published";
    } else if (action === "draft") {
      nextPayload.status = "draft";
    }

    const nextPost = postFromPayload(nextPayload, existing);
    if (existing && nextPost.slug !== existing.slug) {
      return jsonResponse({ error: "published slug is immutable; create a new post instead" }, 409);
    }
    const duplicate = posts.find((post) => post.slug === nextPost.slug && post.id !== nextPost.id);
    if (duplicate) {
      return jsonResponse({ error: "slug already exists" }, 409);
    }

    if (index >= 0) {
      posts[index] = catalogPost(nextPost);
    } else {
      posts.unshift(catalogPost(nextPost));
    }
    saved = nextPost;
  }

  data.updatedAt = nowIso();
  await commitFiles(
    config,
    head,
    {
      [postPath(saved.slug)]: JSON.stringify(saved, null, 2) + "\n",
      [CATALOG_PATH]: JSON.stringify(data, null, 2) + "\n",
    },
    `admin publish: update ${postPath(saved.slug)}`
  );
  const publicUrl = saved?.slug ? `/blog/${saved.slug}/` : "/blog/";
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
      return handleGet(context.request, context.env);
    }
    return handleWrite(context.request, context.env);
  } catch (error) {
    const status = Number(error.status) === 409 ? 409 : 500;
    return jsonResponse({ error: error.message || "admin api failed" }, status);
  }
}
