export async function onRequestGet() {
  return new Response('<!doctype html><meta charset="utf-8"><title>9HWH admin</title><h1>9HWH 发布后台</h1><p>后台页面已加载。</p>', {
    status: 200,
    headers: {
      'Content-Type': 'text/html; charset=utf-8',
      'Cache-Control': 'no-store'
    }
  });
}
