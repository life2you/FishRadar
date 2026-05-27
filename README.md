# CatchYu / FishRadar

[中文] ｜ [English](README_EN.md)

`CatchYu` 是面向闲鱼场景的监控与分析系统，包含两套界面：

- `CatchYu` 租户端：创建监控任务、查看扫描结果、配置自己的通知方式
- `CatchYu Console` 管理端：租户管理、卡密管理、账号池管理、运行日志、平台设置

项目当前已经完成多租户改造，并且运行时主数据统一落在 `MySQL`。

## 当前能力

- 多租户登录、注册、卡密激活、到期控制
- 管理员控制租户是否可用 AI 分析
- 任务监控：AI 模式、关键词模式、价格/区域/发布时间等筛选
- 结果页：推荐筛选、黑名单、导出、管理员重分析
- AI 账号池：多账号、图片/文本能力区分、失败切换
- 登录态账号池：账号主数据入库，运行时临时落盘供 Playwright 使用
- 通知：平台控制租户可用通知方式，租户单独配置自己的渠道
- 定时调度、失败熔断、日志清理

## 当前数据落点

### 已入库

- 任务
- 结果
- 价格快照
- Prompt 文档与任务 Prompt 快照
- 登录态主数据
- 用户、租户、会话、卡密
- AI 账号池
- 租户通知配置
- 任务失败熔断状态
- 平台级业务配置
  - 通知配置
  - 轮换配置
  - AI 运行参数
  - 失败熔断阈值

### 仍保留文件系统

- `logs/`：任务运行日志
- `images/`：商品图片与任务临时图片
- `state/`：运行时兼容目录，主数据已在数据库
- `dist/`：前端构建产物
- `static/`：静态资源

说明：

- `config.json`、`SQLite`、运行时 prompt 文件，已经不是主链路依赖
- 旧目录 `jsonl/`、`price_history/` 仅保留给历史迁移或排查，不作为当前主存储

## 运行架构

- 后端：`FastAPI`
- 前端：`Vue 3 + Vite`
- 任务执行：独立 Python 子进程运行 `spider_v2.py`
- 浏览器自动化：`Playwright`
- 数据库：仅支持 `MySQL`

更详细的结构见：

- [docs/architecture.md](/Users/life2you/vibeCodes/github/FishRadar/docs/architecture.md)
- [docs/operations.md](/Users/life2you/vibeCodes/github/FishRadar/docs/operations.md)
- [docs/multi-tenant-portal-foundation.md](/Users/life2you/vibeCodes/github/FishRadar/docs/multi-tenant-portal-foundation.md)

## 快速开始

### 环境要求

- Python `3.10+`
- Node.js `20+`
- MySQL `8+`
- Playwright 与 Chromium

### 关键前提

当前版本只支持 `MySQL`。  
如果你要使用 AI 分析，**不再依赖 `.env` 里的全局 AI 配置**，而是登录管理员后台后在 `平台设置 -> AI 账号池` 中创建 AI 账号。

### 最少环境变量

`.env` 里真正需要保留的，主要是启动级配置：

| 变量 | 说明 | 必填 |
|------|------|------|
| `APP_DATABASE_URL` | MySQL 连接串 | 是 |
| `SERVER_PORT` | 服务端口，默认 `8000` | 否 |
| `WEB_USERNAME` / `WEB_PASSWORD` | 首次管理员引导账号 | 否 |
| `RUN_HEADLESS` | Playwright 是否无头运行 | 否 |
| `LOGIN_IS_EDGE` | 本地是否走 Edge 通道 | 否 |

说明：

- 业务级配置已经迁入数据库，不建议再把通知、轮换、AI 运行参数长期维护在 `.env`
- `.env.example` 里仍保留了一些示例项，主要用于首次导入和参考

## 本地启动

### 后端

```bash
python -m src.app
```

或：

```bash
uvicorn src.app:app --host 0.0.0.0 --port 8000 --reload
```

### 前端

```bash
cd web-ui
npm install
npm run dev
```

### 一键启动

```bash
bash start.sh
```

## Docker 启动

```bash
cp .env.example .env
docker compose up --build -d
docker compose logs -f app
docker compose down
```

默认地址：

- Web：`http://127.0.0.1:8000`
- API 文档：`http://127.0.0.1:8000/docs`

补充说明：

- `docker-compose.yaml` 默认会启动一个 MySQL 8 服务
- 生产或长期环境建议固定自己的数据库与卷
- 当前镜像已内置 Chromium
- 默认应用镜像地址为 `ghcr.io/life2you/fishradar:latest`
- 仓库内置的 GitHub Actions 会在 `master` 分支 push 或手动触发时构建并推送 GHCR 镜像

### Docker + Nginx 反向代理

如果你要部署到服务器，推荐使用 Docker 版 Nginx 做统一入口：

```bash
cp .env.example .env
docker compose -f docker-compose.yaml -f docker-compose.nginx.yml up --build -d
```

此时：

- `app` 只在容器网络内暴露 `8000`
- 对外由 `nginx` 容器统一暴露 `80`
- 反向代理配置在 [deploy/nginx/default.conf](/Users/life2you/vibeCodes/github/FishRadar/deploy/nginx/default.conf)
- HTTPS 示例在 [deploy/nginx/default-ssl.conf.example](/Users/life2you/vibeCodes/github/FishRadar/deploy/nginx/default-ssl.conf.example)

生产环境建议：

- 将 `.env` 中 `APP_ENV=production`
- 使用 HTTPS 证书，并把 `default.conf` 替换为 SSL 示例配置
- 只开放 `80/443`，不要把应用容器的 `8000` 直接暴露到公网

## 第一次使用建议流程

1. 启动服务并登录管理员后台
2. 在 `账号池管理` 导入闲鱼登录态
3. 在 `平台设置 -> AI 账号池` 配置 AI 账号
4. 在 `租户管理` 创建或管理租户、卡密、AI 权限
5. 使用租户账号登录 `CatchYu`，创建任务并查看结果

## 租户与管理员边界

### 管理员

- 平台总览
- 租户管理
- 账号池管理
- 运行日志
- 平台设置
- 按租户查看任务与结果

### 租户

- 任务工作台
- 结果情报台
- 通知中心

租户端不会暴露管理员能力，也不会看到别的租户数据。

## AI 路由逻辑

当前 AI 执行不再依赖单一全局账号，而是：

- `AI + 图片分析开启`：从支持图片分析的 AI 账号池选账号
- `AI + 图片分析关闭`：从支持文本分析的 AI 账号池选账号
- 失败后自动尝试下一个候选账号

每个任务自身持有独立的 prompt 快照，所以不同任务之间不会共用一份运行时 prompt。

## 任务一致性说明

- 任务启动时会从数据库读取一次任务配置
- 本轮扫描会一直使用这次启动时的任务快照
- 如果任务运行中被编辑：
  - 当前这一轮继续使用旧配置
  - 下一轮重新启动后才会使用新配置

这能保证同一轮扫描内部不会出现“前半段旧标准、后半段新标准”的漂移。

## 常用开发命令

### 测试

```bash
pytest
```

定向测试：

```bash
pytest tests/integration/test_api_settings.py
```

### 前端构建

```bash
cd web-ui && npm run build
```

### 清理测试数据库

当前仓库已内置脚本：

```bash
bash scripts/cleanup_test_dbs.sh
```

默认会保留：

- `fishradar_feature_time_test`

其余 `fishradar*` 测试库会被清掉。

## 当前文档范围

这份 README 以“当前系统怎么工作”为准。  
如果你发现代码行为和文档不一致，应优先相信代码，并更新文档，而不是继续参考旧的 `config.json / prompt 文件 / SQLite` 时代说明。
