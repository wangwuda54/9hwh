export async function onRequestGet() {
  const candidates = [
    'site/public/blog/index.html',
    'blog/index.html'
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

  return new Response('Blog index not found.', {
    status: 404,
    headers: {
      'Content-Type': 'text/plain; charset=utf-8',
      'Cache-Control': 'no-store'
    }
  });
}

async function fetchRaw(path) {
  return fetch(`https://raw.githubusercontent.com/wangwuda54/9hwh/main/${path}`, {
    headers: { Accept: 'text/html' }
  });
}
