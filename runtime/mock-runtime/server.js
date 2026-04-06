const http = require("http");

const host = process.env.OPENCLAW_BIND_HOST || "127.0.0.1";
const port = Number.parseInt(process.env.OPENCLAW_PORT || "18789", 10);
const providerName = process.env.OPENCLAW_PROVIDER_NAME || "未配置 Provider";
const model = process.env.OPENCLAW_MODEL || "未配置模型";
const offlineMode = process.env.OPENCLAW_OFFLINE_MODE === "1";
const startedAt = new Date().toISOString();

const html = `<!DOCTYPE html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>OpenClaw Portable Mock Runtime</title>
    <style>
      :root {
        color-scheme: light;
        --bg: #f4f7fb;
        --panel: rgba(255, 255, 255, 0.88);
        --text: #122033;
        --muted: #5d6b82;
        --line: rgba(18, 32, 51, 0.08);
        --brand: #0f6cbd;
        --brand-soft: rgba(15, 108, 189, 0.12);
        --ok: #0f7b0f;
      }
      * { box-sizing: border-box; }
      body {
        margin: 0;
        min-height: 100vh;
        font-family: "Segoe UI Variable Text", "Segoe UI", sans-serif;
        background:
          radial-gradient(circle at top left, rgba(15, 108, 189, 0.14), transparent 30%),
          radial-gradient(circle at top right, rgba(0, 120, 212, 0.12), transparent 26%),
          linear-gradient(180deg, #fbfdff 0%, var(--bg) 100%);
        color: var(--text);
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 24px;
      }
      .shell {
        width: min(920px, 100%);
        border: 1px solid var(--line);
        border-radius: 28px;
        overflow: hidden;
        background: var(--panel);
        box-shadow: 0 32px 80px rgba(16, 30, 54, 0.10);
        backdrop-filter: blur(14px);
      }
      .hero {
        padding: 32px;
        border-bottom: 1px solid var(--line);
        display: flex;
        justify-content: space-between;
        gap: 20px;
      }
      .eyebrow {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 8px 12px;
        border-radius: 999px;
        background: var(--brand-soft);
        color: var(--brand);
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 0.04em;
      }
      h1 {
        margin: 14px 0 10px;
        font-size: clamp(30px, 5vw, 42px);
        line-height: 1.05;
      }
      p {
        margin: 0;
        color: var(--muted);
        line-height: 1.7;
      }
      .status {
        min-width: 260px;
        padding: 20px;
        border-radius: 22px;
        background: rgba(255, 255, 255, 0.8);
        border: 1px solid rgba(15, 108, 189, 0.12);
      }
      .status strong {
        display: block;
        font-size: 14px;
        color: var(--muted);
        margin-bottom: 12px;
      }
      .status-value {
        font-size: 30px;
        font-weight: 700;
        margin-bottom: 16px;
      }
      .grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 16px;
        padding: 24px 32px 32px;
      }
      .card {
        padding: 18px;
        border-radius: 20px;
        background: rgba(255, 255, 255, 0.92);
        border: 1px solid var(--line);
      }
      .card-label {
        color: var(--muted);
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 10px;
      }
      .card-value {
        font-size: 20px;
        font-weight: 700;
      }
      .badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        color: var(--ok);
        font-weight: 600;
      }
      .dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background: currentColor;
      }
    </style>
  </head>
  <body>
    <main class="shell">
      <section class="hero">
        <div>
          <div class="eyebrow">OpenClaw Portable / Mock Runtime</div>
          <h1>运行时已接通，本地 WebUI 占位页正常。</h1>
          <p>这是一套开发版运行时外壳，用来验证启动器、端口、配置和健康检查流程。后续接入真实 OpenClaw 时，桌面端不需要整体返工。</p>
        </div>
        <aside class="status">
          <strong>当前状态</strong>
          <div class="status-value">运行中</div>
          <div class="badge"><span class="dot"></span>健康检查可用</div>
        </aside>
      </section>
      <section class="grid">
        <article class="card">
          <div class="card-label">Provider</div>
          <div class="card-value">${providerName}</div>
        </article>
        <article class="card">
          <div class="card-label">模型</div>
          <div class="card-value">${model}</div>
        </article>
        <article class="card">
          <div class="card-label">访问地址</div>
          <div class="card-value">${host}:${port}</div>
        </article>
        <article class="card">
          <div class="card-label">模式</div>
          <div class="card-value">${offlineMode ? "离线占位模式" : "已提供 API Key"}</div>
        </article>
      </section>
    </main>
  </body>
</html>`;

const server = http.createServer((req, res) => {
  if (req.url === "/health") {
    res.writeHead(200, { "Content-Type": "application/json; charset=utf-8" });
    res.end(
      JSON.stringify({
        ok: true,
        host,
        port,
        providerName,
        model,
        offlineMode,
        startedAt,
      }),
    );
    return;
  }

  res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
  res.end(html);
});

server.listen(port, host, () => {
  process.stdout.write(`Mock runtime listening on http://${host}:${port}\n`);
});

const shutdown = () => {
  server.close(() => {
    process.exit(0);
  });
};

process.on("SIGTERM", shutdown);
process.on("SIGINT", shutdown);
