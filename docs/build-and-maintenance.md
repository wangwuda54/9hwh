# 构建与维护说明

## 1. 常用命令

```powershell
cd E:\9HWH
python scripts/build_site.py
python scripts/check_static_site.py
```

## 2. 如何构建

构建命令：

```powershell
python scripts/build_site.py
```

构建器会读取 `site_src/data/` 和 `site_src/templates/`，然后生成 `site/public/`。

## 3. 如何检查

检查命令：

```powershell
python scripts/check_static_site.py
```

检查内容包括：

- 关键页面是否存在。
- HTML 是否包含 title、description、viewport、canonical。
- 每页是否只有一个 h1。
- 是否出现 `service_`。
- 是否出现禁止高风险承诺。
- sitemap 是否包含旧页面或归档路径。
- robots 是否保持允许抓取并指向 sitemap。

## 4. 如何本地预览

```powershell
cd E:\9HWH\site\public
python -m http.server 8080
```

浏览器访问：

```text
http://127.0.0.1:8080/
```

## 5. 如何新增 service

修改：

```text
site_src/data/services.json
```

新增服务后运行：

```powershell
python scripts/build_site.py
python scripts/check_static_site.py
```

## 6. 如何新增 topic

修改：

```text
site_src/data/topics.json
```

新增 topic 时必须保持克制表达，不写高风险承诺，不创建成人 / 色粉专题页。

## 7. 如何改 contact

优先修改：

```text
site_src/data/site.json
site_src/data/pages.json
```

联系方式占位字段在 `site.json` 中。

## 8. 如何避免直接手改 site/public

`site/public/` 是生成结果。长期维护时应优先修改：

- `site_src/data/`
- `site_src/templates/`
- `site_src/assets/css/styles.css`
- `scripts/build_site.py`

然后重新构建。

## 9. 什么时候才进入 Cloudflare Pages

只有当站内内容结构、联系方式、视觉基线、sitemap 和旧 service 页面盘点策略都稳定后，才进入 Cloudflare Pages 部署准备。

当前阶段不做：

- `_headers`
- `_redirects`
- Cloudflare Pages 配置
- push
- 旧 service 页面处理
