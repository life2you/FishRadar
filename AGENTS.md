# Repository Guidelines

## 项目结构与模块组织
- 后端位于 `src/`，入口 `src/app.py`，API 路由在 `src/api/routes/`，服务层在 `src/services/`，领域模型在 `src/domain/`，基础设施在 `src/infrastructure/`。
- 前端在 `web-ui/`（Vue 3 + Vite），视图放于 `web-ui/src/views/`，组件在 `web-ui/src/components/`，构建产物会复制到根目录 `dist/`。
- 测试位于 `tests/`，命名遵循 `test_*.py` 或 `tests/*/test_*.py`。
- 运行时目录主要保留 `logs/`、`images/`、`state/`、`static/`、`dist/`。任务、结果、Prompt、登录态主数据、AI 账号池、平台业务配置已统一落在 MySQL。

## 构建、测试与本地开发
- 后端开发：`python -m src.app` 或 `uvicorn src.app:app --host 0.0.0.0 --port 8000 --reload`。
- 爬虫任务：`python spider_v2.py --task-name "MacBook Air M1" --debug-limit 3`。
- 前端开发：`cd web-ui && npm install && npm run dev`；构建：`cd web-ui && npm run build`（产物复制到根目录 `dist/`）。
- 一键本地启动：`bash start.sh`（自动安装依赖、前端构建并启动后端）。
- Docker：`docker compose up --build -d`，查看日志 `docker compose logs -f app`，停止 `docker compose down`。

## 编码风格与命名约定
- 保持分层：API → services → domain → infrastructure，避免跨层耦合，模块保持精简。
- Python 测试函数命名为 `test_*`，文件与路径遵循上述测试目录规范。
- 使用描述性、任务导向的命名（如爬虫任务名、配置键），与业务含义对应。

## 架构与运行时
- 后端使用 FastAPI 提供 API 与静态资源，租户端与管理员端共用同一后端，任务与 AI 推理在独立子进程中协作。
- 当前只支持 MySQL。任务、结果、价格快照、Prompt、登录态主数据、AI 账号池、失败熔断状态和平台业务配置均由数据库驱动。
- 任务运行仍会在 `logs/` 留存运行日志、在 `images/` 下载图片；`state/` 仅作为 Playwright 运行时兼容目录，不再是登录态主数据来源。
- 默认监听 8000 端口，前端构建后静态文件可由后端或 Docker 镜像直接提供。

## 测试指南
- 测试框架：`pytest`（默认同步测试，无需 `pytest-asyncio`）。
- 运行全部测试：`pytest`；覆盖率：`pytest --cov=src` 或 `coverage run -m pytest`；定向测试：`pytest tests/test_utils.py::test_safe_get`。
- 优先覆盖核心服务、爬虫管道的异常分支与重试逻辑，避免回归。
- PR 前请运行相关测试，新增逻辑补充针对性用例。

## 提交与 PR 规范
- Commit 采用类 Conventional Commits：`feat(...)`、`fix(...)`、`refactor(...)`、`chore(...)`、`docs(...)` 等。
- PR 需说明变更范围与影响模块；UI 变更在 `web-ui/` 提供截图；关联相关 Issue；提及配置或迁移步骤。

## 安全与配置提示
- 复制 `.env.example` 为 `.env`，至少配置 `APP_DATABASE_URL`。AI 账号、通知、轮换和失败熔断等业务配置应优先通过管理员后台维护。
- 不要提交真实凭据或登录态数据；Playwright 需本地浏览器，Docker 镜像已预装 Chromium。
- `WEB_USERNAME / WEB_PASSWORD` 仅用于首次管理员引导，生产环境务必修改，并建议后续以数据库中的管理员体系为准。
