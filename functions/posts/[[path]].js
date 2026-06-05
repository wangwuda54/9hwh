export async function onRequestGet(context) {
  const parts = context.params && context.params.path ? context.params.path : [];
  const requested = Array.isArray(parts) ? parts.join('/') : String(parts || '');
  const safePath = requested.replace(/^\/+/, '');

  if (!safePath || safePath.includes('..') || !safePath.endsWith('.html')) {
    return notFound();
  }

  const candidates = [
    `site/public/posts/${safePath}`,
    `posts/${safePath}`
  ];

  for (const path of candidates) {
    const response = await fetchRaw(path);
    if (response.ok) {
      return new Response(await response.text(), {
        status: 200,
        headers: {
          'Content-Type': 'text/html; charset=utf-8',
          'Cache-Control': 'no-store'
        }
      });
    }
  }

  return notFound();
}

async function fetchRaw(path) {
  return fetch(`https://raw.githubusercontent.com/wangwuda54/9hwh/main/${path}`, {
    headers: { Accept: 'text/html' }
  });
}

function notFound() {
  return new Response('Post not found.', {
    status: 404,
    headers: {
      'Content-Type': 'text/plain; charset=utf-8',
      'Cache-Control': 'no-store'
    }
  });
}
