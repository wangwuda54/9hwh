export async function onRequestGet() {
  return new Response(HTML, {
    status: 200,
    headers: {
      'Content-Type': 'text/html; charset=utf-8',
      'Cache-Control': 'no-store'
    }
  });
}

const HTML = `<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>9HWH 发布后台</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#f4f6fb;color:#111827;font-family:Arial,"Microsoft YaHei",sans-serif;line-height:1.6}.wrap{max-width:1100px;margin:0 auto;padding:24px}.card{background:#fff;border:1px solid #e5e7eb;border-radius:16px;padding:20px;margin:16px 0;box-shadow:0 8px 30px rgba(15,23,42,.06)}.login{max-width:440px;margin:12vh auto}.top{display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap}h1,h2,h3{margin:0 0 12px}.muted{color:#64748b}.grid{display:grid;grid-template-columns:minmax(0,1.35fr) minmax(300px,.65fr);gap:18px;align-items:start}label{display:block;font-weight:700;margin:12px 0 6px}input,textarea{width:100%;padding:10px 12px;border:1px solid #d1d5db;border-radius:10px;font:inherit}textarea{min-height:260px;resize:vertical}.summary{min-height:90px}.row{display:grid;grid-template-columns:1fr 1fr;gap:12px}.actions{display:flex;gap:10px;flex-wrap:wrap;margin-top:14px}button{border:0;border-radius:10px;padding:10px 14px;background:#111827;color:white;font-weight:700;cursor:pointer}button.secondary{background:#e5e7eb;color:#111827}button.ghost{background:white;color:#111827;border:1px solid #d1d5db}button:disabled{opacity:.55;cursor:not-allowed}.status{min-height:22px;margin-top:12px;white-space:pre-wrap;color:#64748b}.error{color:#b91c1c}.ok{color:#166534}.hide{display:none}.post{border:1px solid #e5e7eb;border-radius:12px;padding:12px;margin:10px 0}.badge{display:inline-block;font-size:12px;border-radius:999px;background:#f1f5f9;color:#475569;padding:2px 8px;margin:3px 6px 8px 0}.badge.pub{background:#dcfce7;color:#166534}.keep{display:flex;align-items:center;gap:8px;font-weight:400;color:#64748b}.keep input{width:auto}@media(max-width:850px){.wrap{padding:16px}.grid,.row{grid-template-columns:1fr}}
</style>
</head>
<body>
<main class="wrap">
  <section id="loginBox" class="card login">
    <h1>9HWH 发布后台</h1>
    <p class="muted">输入后台账号密码登录。勾选保持登录后，同一浏览器 30 天内不用再次登录。</p>
    <form id="loginForm">
      <label for="username">用户名</label>
      <input id="username" autocomplete="username" required>
      <label for="password">密码</label>
      <input id="password" type="password" autocomplete="current-password" required>
      <label class="keep"><input id="remember" type="checkbox" checked>保持登录 30 天</label>
      <div class="actions"><button type="submit">登录</button></div>
      <div id="loginMsg" class="status"></div>
    </form>
  </section>

  <section id="adminBox" class="hide">
    <div class="top">
      <div><h1>9HWH 发布后台</h1><div class="muted">发布会写入 GitHub，并触发 Cloudflare 自动部署。</div></div>
      <div class="actions"><a href="/" target="_blank">首页</a><a href="/blog/" target="_blank">发布列表</a><button id="reloadBtn" class="ghost" type="button">刷新</button><button id="logoutBtn" class="ghost" type="button">退出</button></div>
    </div>
    <div class="grid">
      <section class="card">
        <h2 id="formTitle">新建内容</h2>
        <form id="postForm">
          <input id="postId" type="hidden">
          <div class="row">
            <div><label for="slug">URL Slug</label><input id="slug" placeholder="test-post" required><div class="muted">发布地址：/posts/&lt;slug&gt;.html</div></div>
            <div><label for="tags">标签</label><input id="tags" placeholder="推广, 获客"></div>
          </div>
          <label for="title">标题</label><input id="title" required>
          <label for="summary">摘要</label><textarea id="summary" class="summary" required></textarea>
          <label for="content">正文</label><textarea id="content" required></textarea>
          <div class="actions"><button id="draftBtn" class="secondary" type="button">保存草稿</button><button id="publishBtn" type="button">发布 / 更新发布</button><button id="clearBtn" class="ghost" type="button">清空</button></div>
          <div id="formMsg" class="status"></div>
        </form>
      </section>
      <aside class="card">
        <h2>内容列表</h2>
        <div id="postsBox" class="muted">登录后读取内容。</div>
      </aside>
    </div>
  </section>
</main>
<script>
(function(){
  var state={posts:[]};
  function id(x){return document.getElementById(x)}
  function msg(el,text,type){el.textContent=text||'';el.className='status '+(type||'')}
  function showLogin(){id('adminBox').classList.add('hide');id('loginBox').classList.remove('hide')}
  function showAdmin(){id('loginBox').classList.add('hide');id('adminBox').classList.remove('hide')}
  function setBusy(v){['draftBtn','publishBtn','clearBtn','reloadBtn'].forEach(function(x){id(x).disabled=v})}
  async function api(url,method,body){
    var opt={method:method||'GET',credentials:'same-origin'};
    if(body){opt.headers={'Content-Type':'application/json'};opt.body=JSON.stringify(body)}
    var res=await fetch(url,opt);var text=await res.text();var data={};
    try{data=text?JSON.parse(text):{}}catch(e){data={message:text?text.slice(0,200):'接口返回非 JSON'}}
    if(!res.ok){throw new Error(data.message||('请求失败：HTTP '+res.status))}
    return data;
  }
  async function boot(){
    showLogin();
    try{var s=await api('/api/admin/session','GET');if(s.authenticated){showAdmin();await loadPosts()}}catch(e){}
  }
  async function login(e){
    e.preventDefault();msg(id('loginMsg'),'登录中...');
    try{await api('/api/admin/login','POST',{username:id('username').value.trim(),password:id('password').value,remember:id('remember').checked});id('password').value='';msg(id('loginMsg'),'登录成功。','ok');showAdmin();await loadPosts()}catch(err){msg(id('loginMsg'),err.message,'error')}
  }
  async function logout(){try{await api('/api/admin/logout','POST')}catch(e){} state.posts=[];renderPosts();showLogin()}
  async function loadPosts(){
    msg(id('formMsg'),'正在读取内容列表...');
    try{var data=await api('/api/admin/posts','GET');state.posts=data.posts||[];renderPosts();msg(id('formMsg'),'内容列表已更新。','ok')}catch(err){msg(id('formMsg'),'已经进入后台，但内容列表读取失败：'+err.message+'\n如果这里提示未登录，请刷新页面或重新登录。','error')}
  }
  function postData(){return{id:id('postId').value,slug:id('slug').value,title:id('title').value,summary:id('summary').value,content:id('content').value,tags:id('tags').value}}
  async function submit(action){
    if(!id('postForm').reportValidity())return;
    setBusy(true);msg(id('formMsg'),action==='publish'?'正在发布...':'正在保存草稿...');
    try{var data=await api('/api/admin/posts','POST',{action:action,post:postData()});state.posts=data.posts||[];renderPosts();if(data.post)edit(data.post);msg(id('formMsg'),'操作成功。'+(data.publicUrl?'\n公开地址：'+data.publicUrl:''),'ok')}catch(err){msg(id('formMsg'),err.message,'error')}finally{setBusy(false)}
  }
  function renderPosts(){
    var box=id('postsBox');box.innerHTML='';
    if(!state.posts.length){box.textContent='暂无内容。';return}
    state.posts.forEach(function(p){
      var div=document.createElement('div');div.className='post';
      var h=document.createElement('h3');h.textContent=p.title||p.slug;div.appendChild(h);
      var s=document.createElement('p');s.textContent=p.summary||'';div.appendChild(s);
      var b=document.createElement('span');b.className='badge '+(p.status==='published'?'pub':'');b.textContent=p.status==='published'?'已发布':'草稿';div.appendChild(b);
      var slug=document.createElement('span');slug.className='badge';slug.textContent=p.slug||'';div.appendChild(slug);
      var row=document.createElement('div');row.className='actions';
      var btn=document.createElement('button');btn.type='button';btn.className='secondary';btn.textContent='编辑';btn.onclick=function(){edit(p)};row.appendChild(btn);
      if(p.status==='published'){var a=document.createElement('a');a.href='/posts/'+p.slug+'.html';a.target='_blank';a.textContent='查看';row.appendChild(a)}
      div.appendChild(row);box.appendChild(div);
    });
  }
  function edit(p){id('postId').value=p.id||'';id('slug').value=p.slug||'';id('title').value=p.title||'';id('summary').value=p.summary||'';id('content').value=p.content||'';id('tags').value=Array.isArray(p.tags)?p.tags.join(', '):'';id('formTitle').textContent='编辑：'+(p.title||p.slug);window.scrollTo({top:0,behavior:'smooth'})}
  function clearForm(){id('postForm').reset();id('postId').value='';id('formTitle').textContent='新建内容';msg(id('formMsg'),'')}
  document.addEventListener('DOMContentLoaded',boot);
  id('loginForm').addEventListener('submit',login);
  id('logoutBtn').addEventListener('click',logout);
  id('reloadBtn').addEventListener('click',loadPosts);
  id('draftBtn').addEventListener('click',function(){submit('save')});
  id('publishBtn').addEventListener('click',function(){submit('publish')});
  id('clearBtn').addEventListener('click',clearForm);
})();
</script>
</body>
</html>`;
