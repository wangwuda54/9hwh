const enc = new TextEncoder();
const dec = new TextDecoder();
const PUBLIC_DIR = 'site/public';

export async function onRequestGet(context) {
  const auth = await requireAuth(context.request, context.env);
  if (!auth) return json({ message: '未登录。' }, 401);
  return json(await readStore(context.env));
}

export async function onRequestPost(context) {
  const auth = await requireAuth(context.request, context.env);
  if (!auth) return json({ message: '未登录。' }, 401);
  const body = await readJson(context.request);
  const action = body.action === 'publish' ? 'publish' : 'save';
  const now = new Date().toISOString();
  const store = await readStore(context.env);
  const post = buildPost(body.post || {}, action, now, store.posts || []);
  const posts = [post, ...(store.posts || []).filter((x) => x.id !== post.id && x.slug !== post.slug)];
  const commits = [];
  if (action === 'publish') {
    commits.push(await putFile(context.env, `${PUBLIC_DIR}/posts/${post.slug}.html`, renderPost(post), `Publish post: ${post.slug}`));
    commits.push(await putFile(context.env, `${PUBLIC_DIR}/blog/index.html`, renderBlog(posts), 'Update blog index'));
  }
  commits.push(await putFile(context.env, 'data/published-posts.json', JSON.stringify({ version: 1, updatedAt: now, posts }, null, 2) + '\n', action === 'publish' ? `Update publish store: ${post.slug}` : `Save draft: ${post.slug}`));
  return json({ post, posts, commits, publicUrl: action === 'publish' ? `/posts/${post.slug}.html` : null });
}

async function readStore(env) {
  const file = await getFile(env, 'data/published-posts.json');
  if (!file.exists) return { posts: [], updatedAt: null };
  const data = JSON.parse(file.content || '{"posts":[]}');
  return { posts: Array.isArray(data.posts) ? data.posts : [], updatedAt: data.updatedAt || null };
}

function buildPost(input, action, now, posts) {
  const slug = cleanSlug(input.slug);
  const old = posts.find((x) => x.id === input.id || x.slug === slug) || {};
  const post = {
    id: old.id || input.id || `post-${Date.now()}`,
    slug,
    title: String(input.title || '').trim(),
    summary: String(input.summary || '').trim(),
    content: String(input.content || '').trim(),
    tags: splitTags(input.tags),
    status: action === 'publish' ? 'published' : (old.status === 'published' ? 'published' : 'draft'),
    createdAt: old.createdAt || now,
    updatedAt: now,
    publishedAt: action === 'publish' ? (old.publishedAt || now) : (old.publishedAt || null)
  };
  if (!post.slug) throw new Error('URL Slug 不能为空。');
  if (!post.title) throw new Error('标题不能为空。');
  if (!post.summary) throw new Error('摘要不能为空。');
  if (!post.content) throw new Error('正文不能为空。');
  return post;
}

async function getFile(env, path) {
  const repo = env.GITHUB_REPO || 'wangwuda54/9hwh';
  const branch = env.GITHUB_BRANCH || 'main';
  const url = `https://api.github.com/repos/${repo}/contents/${path.split('/').map(encodeURIComponent).join('/')}?ref=${encodeURIComponent(branch)}`;
  const res = await fetch(url, gh(env));
  if (res.status === 404) return { exists: false, sha: null, content: '' };
  const data = await ghData(res);
  return { exists: true, sha: data.sha, content: fromBase64(data.content || '') };
}

async function putFile(env, path, content, message) {
  const repo = env.GITHUB_REPO || 'wangwuda54/9hwh';
  const branch = env.GITHUB_BRANCH || 'main';
  const old = await getFile(env, path);
  if (old.exists && old.content === content) return { path, sha: 'no-change' };
  const body = { message, content: toBase64(content), branch };
  if (old.sha) body.sha = old.sha;
  const url = `https://api.github.com/repos/${repo}/contents/${path.split('/').map(encodeURIComponent).join('/')}`;
  const data = await ghData(await fetch(url, gh(env, 'PUT', body)));
  return { path, sha: data.commit && data.commit.sha ? data.commit.sha : null };
}

function gh(env, method = 'GET', body) {
  return { method, headers: { Accept: 'application/vnd.github+json', Authorization: `Bearer ${env.GITHUB_TOKEN}`, 'Content-Type': 'application/json', 'User-Agent': '9hwh-admin', 'X-GitHub-Api-Version': '2022-11-28' }, body: body ? JSON.stringify(body) : undefined };
}
async function ghData(res) {
  const text = await res.text();
  const data = text ? JSON.parse(text) : {};
  if (!res.ok) throw new Error(`GitHub API 错误：${data.message || res.status}`);
  return data;
}

async function requireAuth(request, env) {
  const token = cookie(request, 'admin_session');
  if (!token || !env.SESSION_SECRET) return null;
  const parts = token.split('.');
  if (parts.length !== 2) return null;
  const sig = await signPart(parts[0], env.SESSION_SECRET);
  if (sig !== parts[1]) return null;
  const data = JSON.parse(dec.decode(unbase64url(parts[0])));
  if (!data.exp || data.exp < Math.floor(Date.now() / 1000)) return null;
  return data.user || null;
}
async function signPart(value, secret) {
  const key = await crypto.subtle.importKey('raw', enc.encode(secret), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']);
  const sig = await crypto.subtle.sign('HMAC', key, enc.encode(value));
  return base64url(new Uint8Array(sig));
}
function cookie(request, name) { const raw = request.headers.get('Cookie') || ''; const item = raw.split(';').map((x) => x.trim()).find((x) => x.startsWith(name + '=')); return item ? decodeURIComponent(item.slice(name.length + 1)) : ''; }

function renderBlog(posts) {
  const items = posts.filter((p) => p.status === 'published').map((p) => `<article class="post-card"><div>${esc(day(p.publishedAt || p.updatedAt))}</div><h2><a href="/posts/${esc(p.slug)}.html">${esc(p.title)}</a></h2><p>${esc(p.summary)}</p></article>`).join('\n') || '<p>暂无已发布内容。</p>';
  return `<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>发布内容 - 9HWH</title><style>body{font-family:Arial,'Microsoft YaHei',sans-serif;background:#f7f8fb;color:#121826;line-height:1.7;margin:0}header,main,footer{max-width:980px;margin:0 auto;padding:24px}nav{display:flex;justify-content:space-between}.post-card{background:#fff;border:1px solid #e6e8ef;border-radius:18px;padding:22px;margin:18px 0}a{color:#111827;font-weight:700;text-decoration:none}p,footer{color:#5b6475}</style></head><body><header><nav><a href="/">9HWH</a><a href="/admin/">发布后台</a></nav></header><main><h1>发布内容</h1>${items}</main><footer>© 2026 9HWH</footer></body></html>`;
}
function renderPost(p) {
  return `<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${esc(p.title)} - 9HWH</title><meta name="description" content="${esc(p.summary)}"><style>body{font-family:Arial,'Microsoft YaHei',sans-serif;background:#f7f8fb;color:#121826;line-height:1.8;margin:0}header,main,footer{max-width:900px;margin:0 auto;padding:24px}nav{display:flex;justify-content:space-between}article{background:#fff;border:1px solid #e6e8ef;border-radius:22px;padding:36px;margin-top:24px}a{color:#111827;font-weight:700;text-decoration:none}.summary,footer{color:#5b6475}</style></head><body><header><nav><a href="/">9HWH</a><a href="/blog/">发布内容</a></nav></header><main><a href="/blog/">← 返回发布列表</a><article><h1>${esc(p.title)}</h1><p class="summary">${esc(p.summary)}</p>${paras(p.content)}</article></main><footer>© 2026 9HWH</footer></body></html>`;
}

async function readJson(request) { try { return await request.json(); } catch (_) { return {}; } }
function json(data, status = 200) { return new Response(JSON.stringify(data), { status, headers: { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store' } }); }
function cleanSlug(v) { return String(v || '').trim().toLowerCase().replace(/[^a-z0-9-]+/g, '-').replace(/^-+|-+$/g, '').replace(/-{2,}/g, '-'); }
function splitTags(v) { return Array.isArray(v) ? v.map(String).map((x) => x.trim()).filter(Boolean) : String(v || '').split(/[,，\n]/).map((x) => x.trim()).filter(Boolean); }
function esc(v) { return String(v || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;'); }
function paras(v) { return String(v || '').trim().split(/\n{2,}/).filter(Boolean).map((x) => `<p>${esc(x).replace(/\n/g, '<br>')}</p>`).join(''); }
function day(v) { const d = new Date(v || Date.now()); return Number.isNaN(d.getTime()) ? '' : d.toISOString().slice(0, 10); }
function toBase64(v) { let s = ''; for (const b of enc.encode(v)) s += String.fromCharCode(b); return btoa(s); }
function fromBase64(v) { const s = atob(String(v || '').replace(/\s/g, '')); return dec.decode(Uint8Array.from(s, (c) => c.charCodeAt(0))); }
function base64url(bytes) { let s = ''; for (const b of bytes) s += String.fromCharCode(b); return btoa(s).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/g, ''); }
function unbase64url(v) { const p = v.replace(/-/g, '+').replace(/_/g, '/') + '='.repeat((4 - v.length % 4) % 4); return Uint8Array.from(atob(p), (c) => c.charCodeAt(0)); }
