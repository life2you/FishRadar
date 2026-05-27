# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

基于 Playwright + AI 的闲鱼监控与分析系统。FastAPI 后端 + Vue 3 前端，当前包含 `CatchYu` 租户端和 `CatchYu Console` 管理端，支持多租户任务监控、多 AI 账号路由、卡密激活、结果重分析和多渠道通知。

## 核心架构

```
API层 (src/api/routes/)
    ↓
服务层 (src/services/)
    ↓
领域层 (src/domain/)
    ↓
基础设施层 (src/infrastructure/)
```

关键入口：
- `src/app.py` - FastAPI 应用主入口
- `spider_v2.py` - 爬虫 CLI 入口
- `src/scraper.py` - Playwright 爬虫核心逻辑

服务层：
- `TaskService` - 任务 CRUD
- `ProcessService` - 爬虫子进程管理
- `SchedulerService` - APScheduler 定时调度
- `AIAnalysisService` - 多模态 AI 分析
- `NotificationService` - 多渠道通知（ntfy/Bark/企业微信/Telegram/Webhook）

前端 (`web-ui/`)：Vue 3 + Vite + shadcn-vue + Tailwind CSS

## 开发命令

```bash
# 后端开发
python -m src.app
# 或
uvicorn src.app:app --host 0.0.0.0 --port 8000 --reload

# 前端开发
cd web-ui && npm install && npm run dev

# 前端构建
cd web-ui && npm run build

# 一键本地启动（构建前端 + 启动后端）
bash start.sh

# Docker 部署
docker compose up --build -d
```

## 爬虫命令

```bash
python spider_v2.py                          # 运行所有启用任务
python spider_v2.py --task-name "MacBook"    # 运行指定任务
python spider_v2.py --debug-limit 3          # 调试模式，限制商品数
```

## 测试

```bash
pytest                              # 运行所有测试
pytest --cov=src                    # 覆盖率报告
pytest tests/unit/test_utils.py    # 运行单个测试文件
pytest tests/unit/test_utils.py::test_safe_get  # 运行单个测试函数
```

测试规范：文件 `tests/**/test_*.py`，函数 `test_*`

## 配置

环境变量 (`.env`) 现在主要只保留启动级配置：
- 数据库：`APP_DATABASE_URL`
- 服务启动：`SERVER_PORT`
- 浏览器运行：`RUN_HEADLESS`, `LOGIN_IS_EDGE`, `STATE_FILE`
- 首次管理员引导：`WEB_USERNAME`, `WEB_PASSWORD`

业务级配置已迁入 MySQL，并应通过管理员后台维护：
- AI 账号池与能力路由
- 平台通知配置
- 轮换配置
- AI 运行参数
- 失败熔断阈值
- Prompt 文档与任务 Prompt 快照

## 数据流

1. 管理端或租户端通过 Web UI 创建任务
2. 任务和 Prompt 快照写入 MySQL
3. SchedulerService 按 cron 触发或手动启动
4. ProcessService 启动 `spider_v2.py` 子进程
5. `scraper.py` 使用 Playwright 抓取商品
6. `AIAnalysisService` 按任务模式与图片开关，从 AI 账号池中路由合适账号分析
7. 结果写回 MySQL；`logs/` 和 `images/` 仅保留运行时产物

## 注意事项

- 当前数据库只支持 MySQL
- AI 任务的当前运行批次使用“启动时快照”，运行中编辑任务不会影响已启动的这轮任务
- 登录态主数据已经入库，Docker 部署通过 Web UI 导入账号即可；`state/` 只是运行时兼容目录
- 遇到滑动验证码时设置 `RUN_HEADLESS=false` 手动处理
- 生产环境务必修改默认 Web 认证密码
