/**
 * Cloudflare Workers - 静态资源服务
 *
 * 使用 Workers Assets 绑定提供静态文件服务，
 * 无需 KV/R2，直接从 Workers 内置资源目录读取文件。
 *
 * 配套 wrangler.toml 中的 [assets] 配置使用。
 * 若使用 Cloudflare Pages 部署则不需要此文件。
 */

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname;

    // 安全：阻止目录遍历
    if (path.includes('..')) {
      return new Response('Bad Request', { status: 400 });
    }

    // Assets 绑定会自动处理静态文件请求
    // 这里只处理需要特殊逻辑的路由

    // API: 获取统计信息
    if (path === '/api/stats') {
      try {
        const resp = await env.ASSETS.fetch(new URL('data/pages/stats.json', url.origin));
        if (resp.ok) {
          const data = await resp.json();
          return new Response(JSON.stringify(data), {
            headers: { 'Content-Type': 'application/json', 'Cache-Control': 'public, max-age=300' }
          });
        }
      } catch (e) { /* fall through */ }
    }

    // API: 获取语料条数
    if (path === '/api/count') {
      try {
        const resp = await env.ASSETS.fetch(new URL('data/pages/metadata.json', url.origin));
        if (resp.ok) {
          const meta = await resp.json();
          return new Response(JSON.stringify({ total: meta.total_items, pages: meta.total_pages }), {
            headers: { 'Content-Type': 'application/json', 'Cache-Control': 'public, max-age=300' }
          });
        }
      } catch (e) { /* fall through */ }
    }

    // 其余请求交给 Assets 绑定处理（静态文件）
    return env.ASSETS.fetch(request);
  }
};
