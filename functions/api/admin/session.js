export function onRequestGet(context) {
  const env = context.env || {};
  return new Response(JSON.stringify({
    ok: true,
    functionReady: true,
    variables: {
      ADMIN_USERNAME: Boolean(env.ADMIN_USERNAME),
      ADMIN_PASSWORD: Boolean(env.ADMIN_PASSWORD),
      GITHUB_BRANCH: Boolean(env.GITHUB_BRANCH),
      GITHUB_REPO: Boolean(env.GITHUB_REPO),
      GITHUB_TOKEN: Boolean(env.GITHUB_TOKEN),
      SESSION_SECRET: Boolean(env.SESSION_SECRET)
    }
  }), {
    status: 200,
    headers: {
      'Content-Type': 'application/json; charset=utf-8',
      'Cache-Control': 'no-store'
    }
  });
}
