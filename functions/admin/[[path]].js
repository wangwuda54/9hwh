export async function onRequestGet() {
  const source = await fetch('https://raw.githubusercontent.com/wangwuda54/9hwh/main/admin/index.html', {
    headers: { Accept: 'text/html' }
  });

  if (!source.ok) {
    return new Response('Admin HTML source unavailable.', {
      status: 502,
      headers: {
        'Content-Type': 'text/plain; charset=utf-8',
        'Cache-Control': 'no-store'
      }
    });
  }

  let html = await source.text();
  html = html.replace('session && session.ok', 'session && session.authenticated');
  html = html.replace('password: fields.password.value }', 'password: fields.password.value, remember: true }');

  return new Response(html, {
    status: 200,
    headers: {
      'Content-Type': 'text/html; charset=utf-8',
      'Cache-Control': 'no-store'
    }
  });
}
