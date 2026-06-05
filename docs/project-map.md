# 项目 Map

本文档用于二次开发前快速建立项目全局视图。当前项目是一个以 Flask 为核心的多邮箱管理 Web 应用，带本地/打包桌面运行能力、Docker 运行方式和 Chrome/Edge 浏览器扩展入口。

## 技术栈

### 后端

- Python 3，生产 Docker 镜像基于 `python:3.11-slim`。
- Flask 提供 Web 页面、登录会话和 JSON API。
- Flask-WTF CSRFProtect 提供 CSRF 防护；缺失时会降级运行。
- 标准库 `sqlite3` 直接访问数据库，没有 SQLAlchemy/Django ORM。
- `requests[socks]` 访问 Microsoft Graph、OAuth、临时邮箱服务、WebDAV、Telegram/企业微信等外部接口，并支持代理。
- APScheduler + croniter 负责定时刷新 Token、转发轮询和 WebDAV 备份。
- bcrypt 负责登录密码哈希。
- cryptography/Fernet 负责敏感字段加密。
- PyInstaller spec 支持 Windows/macOS 桌面版打包。
- Docker 生产入口使用 gunicorn，固定单 worker + 多线程。

### 前端

- 服务端模板使用 Jinja2：`templates/index.html`、`templates/login.html` 和 `templates/partials/index/*.html`。
- 主界面是原生 HTML/CSS/JavaScript，没有 React/Vue/Angular 打包工程。
- `static/index.css` 通过 `@import` 汇总 `static/css/index/*.css`。
- `static/index.js` 仅保留历史占位，真实逻辑拆在 `static/js/index/*.js`。
- 邮件 HTML 内容在前端使用 CDN 引入的 DOMPurify 进行净化。

### 浏览器扩展

- `browser-extension/manifest.json` 是 Manifest V3。
- 扩展提供 popup 和 side panel，用保存的服务地址/密码登录或嵌入打开 Web 控制台。

### 数据库

- 数据库是 SQLite。
- 默认开发运行路径：`data/outlook_accounts.db`。
- 打包运行路径：系统用户数据目录下的 `OutlookEmail/data/outlook_accounts.db`。
- 可用环境变量 `DATABASE_PATH` 覆盖数据库文件路径。
- 初始化、迁移、默认数据、索引创建集中在 `outlook_web/segments/01_bootstrap.py` 的 `init_db()`。

## 运行入口与加载方式

- `web_outlook_app.py`：主入口。按固定顺序读取并 `exec` 加载 `outlook_web/segments/*.py`，导出 Flask `app`，并提供本地桌面服务器启动逻辑。
- `outlook_web/app.py`：兼容入口，导入 `web_outlook_app` 后把公开符号转出。
- `outlook_web/runtime.py`：运行时路径、打包态判断、数据库默认路径、Secret Key 持久化、启动错误日志。
- `outlook_web/windows_tray.py`：桌面版托盘菜单封装。
- `outlookEmail.spec`：PyInstaller 打包配置，包含 templates、static、segments 和 VERSION。
- `Dockerfile`：生产镜像构建，运行 `gunicorn -k gthread -w 1`。

`web_outlook_app.py` 加载 segment 的顺序很重要：

1. `01_bootstrap.py`
2. `02_groups_accounts.py`
3. `03_mail_helpers.py`
4. `04_routes_groups_accounts.py`
5. `05_routes_refresh_mail.py`
6. `06_routes_temp_email.py`
7. `07_routes_oauth_settings_external.py`
8. `08_forwarding_scheduler_errors.py`
9. `09_routes_system_update.py`

这些 segment 共用同一个全局命名空间，因此后加载文件可以直接使用前面文件定义的 `app`、`get_db()`、业务 helper 等函数。二开时要注意命名冲突和加载顺序。

## 后端文件职责

- `outlook_web/segments/01_bootstrap.py`：创建 Flask app、配置 session/CSRF、版本检查、登录限流、密码哈希、敏感数据加密、SQLite 连接、建表迁移、默认设置、应用初始化。
- `outlook_web/segments/02_groups_accounts.py`：分组、账号、标签、账号别名、代理配置、账号搜索、项目运行态的业务函数。
- `outlook_web/segments/03_mail_helpers.py`：代理请求、Microsoft Graph、OAuth/IMAP 读取、邮件解析、附件处理、对外 API 鉴权等底层邮件 helper。
- `outlook_web/segments/04_routes_groups_accounts.py`：登录/退出、首页、版本状态、CSRF Token、分组 API、账号 API、导入导出、标签 API、项目 API。
- `outlook_web/segments/05_routes_refresh_mail.py`：Token 刷新、批量/流式刷新、刷新日志、邮件列表、邮件详情、标记已读、删除邮件、附件下载、普通邮箱本地保留写入。
- `outlook_web/segments/06_routes_temp_email.py`：GPTMail、DuckMail、Cloudflare Temp Email 的生成、导入、列表、详情、删除和刷新 API。
- `outlook_web/segments/07_routes_oauth_settings_external.py`：OAuth 授权链接和换取 Token、系统设置读写、Cron 校验、普通邮箱本地保留状态/清理、对外邮件 API。
- `outlook_web/segments/08_forwarding_scheduler_errors.py`：APScheduler 初始化、定时刷新、自动转发、SMTP/Telegram/企业微信推送、WebDAV 备份、错误处理，以及部分邮件 API 的增强实现。
- `outlook_web/segments/09_routes_system_update.py`：Docker 在线更新状态和触发接口，直接通过 Docker Unix Socket 创建/启动 Watchtower 容器。
- `outlook_web/mail_datetime.py`：邮件日期字符串解析工具。
- `outlook_mail_reader.py`：独立的 Outlook/Graph/IMAP 读取测试脚本，不是 Web 服务运行入口。

## 前端文件职责

- `templates/index.html`：主页面壳，加载局部模板、CSS 和 10 个拆分 JS 文件。
- `templates/login.html`：登录页，内联 CSS 和简单 fetch 登录逻辑。
- `templates/partials/index/layout.html`：主页面四栏布局、导航、分组面板、账号面板、邮件列表和详情区骨架。
- `templates/partials/index/dialogs-primary.html`：常用弹窗。
- `templates/partials/index/dialogs-management.html`：管理类弹窗，例如标签、批量操作、设置等。
- `templates/partials/index/dialogs-oauth.html`：OAuth/Token 相关弹窗。
- `static/index.css`：CSS 汇总入口。
- `static/css/index/01-base.css`：基础变量、通用元素、表单/按钮基础样式。
- `static/css/index/02-navbar.css`：顶部导航、版本弹层、导航操作区。
- `static/css/index/03-layout.css`：主界面布局、分组/账号/内容区域结构。
- `static/css/index/04-account-panel.css`：账号列表、账号工具栏、账号卡片、批量栏相关样式。
- `static/css/index/05-email-content.css`：邮件列表、邮件详情、全屏查看、原始邮件查看。
- `static/css/index/06-modals-toast.css`：弹窗、Toast、遮罩层。
- `static/css/index/07-meta.css`：元信息、状态、标签等辅助视觉样式。
- `static/css/index/08-responsive.css`：移动端和窄屏响应式布局。
- `static/js/index/01-core.js`：全局状态、通用格式化、请求、Toast、版本检查、初始化流程等核心工具。
- `static/js/index/02-groups.js`：分组加载、渲染、创建、更新、删除、排序。
- `static/js/index/03-temp-emails.js`：临时邮箱列表、生成/导入、消息读取、Cloudflare 全部邮件视图。
- `static/js/index/04-accounts.js`：账号列表、搜索、导入、编辑、删除、别名、代理等账号交互。
- `static/js/index/05-emails.js`：普通邮箱邮件列表、详情、附件、正文净化、已读/删除、本地保留交互。
- `static/js/index/06-utils-oauth.js`：工具函数和 OAuth/Refresh Token 获取流程。
- `static/js/index/07-settings.js`：系统设置、Cron 校验、转发/WebDAV/本地保留设置 UI。
- `static/js/index/08-refresh.js`：Token 刷新管理、批量刷新、SSE 流式刷新状态。
- `static/js/index/09-tags.js`：标签管理、标签筛选、账号/临时邮箱打标。
- `static/js/index/10-batch-actions.js`：账号批量选择、复制、导出、刷新、删除、批量移动、批量代理、批量打标。

## 浏览器扩展文件职责

- `browser-extension/manifest.json`：MV3 manifest、权限、side panel、快捷键。
- `browser-extension/storage.js`：扩展配置读写。
- `browser-extension/api-client.js`：和 Web 后端通信、登录、CSRF、流式请求、打开控制台。
- `browser-extension/popup.html/css/js`：扩展弹窗配置页和快捷入口。
- `browser-extension/sidepanel.html/css/js`：侧边栏控制台容器。
- `browser-extension/background.js`：扩展后台 service worker。

## SQLite 表结构

以下是 `init_db()` 初始化后的有效业务表。部分旧库迁移列通过 `ALTER TABLE` 补齐，下面按当前代码期望的最终字段列出。

### settings

键值配置表。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| key | TEXT PRIMARY KEY | 设置键 |
| value | TEXT | 设置值 |
| updated_at | TIMESTAMP | 更新时间，默认当前时间 |

常见 key：`login_password`、`gptmail_api_key`、`duckmail_base_url`、`duckmail_api_key`、`cloudflare_worker_domain`、`cloudflare_email_domains`、`cloudflare_admin_password`、`refresh_interval_days`、`refresh_delay_seconds`、`refresh_cron`、`use_cron_schedule`、`enable_scheduled_refresh`、`app_timezone`、`normal_mail_local_retention_enabled`、`forward_include_account_group`、转发 SMTP/Telegram/企业微信配置、WebDAV 备份配置等。

### groups

邮箱分组表。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | INTEGER PRIMARY KEY AUTOINCREMENT | 分组 ID |
| name | TEXT UNIQUE NOT NULL | 分组名 |
| description | TEXT | 描述 |
| color | TEXT | 颜色，默认 `#1a1a1a` |
| sort_order | INTEGER | 排序值 |
| is_system | INTEGER | 是否系统分组 |
| proxy_url | TEXT | 主代理 |
| fallback_proxy_url_1 | TEXT | 备用代理 1 |
| fallback_proxy_url_2 | TEXT | 备用代理 2 |
| created_at | TIMESTAMP | 创建时间 |

默认创建 `默认分组` 和系统分组 `临时邮箱`。

### accounts

普通邮箱账号表。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | INTEGER PRIMARY KEY AUTOINCREMENT | 账号 ID |
| email | TEXT UNIQUE NOT NULL | 主邮箱地址 |
| password | TEXT | 邮箱密码或授权密码，加密保存 |
| client_id | TEXT | OAuth Client ID |
| refresh_token | TEXT | OAuth Refresh Token，加密保存 |
| group_id | INTEGER | 所属分组，外键到 groups.id |
| sort_order | INTEGER | 排序值 |
| remark | TEXT | 备注 |
| status | TEXT | 账号状态，默认 `active` |
| account_type | TEXT | 账号类型，默认 `outlook` |
| provider | TEXT | 邮箱提供商，默认 `outlook` |
| imap_host | TEXT | 自定义 IMAP 主机 |
| imap_port | INTEGER | IMAP 端口，默认 993 |
| imap_password | TEXT | IMAP 密码，加密保存 |
| forward_enabled | INTEGER | 是否开启自动转发 |
| forward_last_checked_at | TIMESTAMP | 转发轮询游标 |
| proxy_url | TEXT | 账号级主代理 |
| fallback_proxy_url_1 | TEXT | 账号级备用代理 1 |
| fallback_proxy_url_2 | TEXT | 账号级备用代理 2 |
| last_refresh_at | TIMESTAMP | 最近刷新时间 |
| last_refresh_status | TEXT | 最近刷新状态，默认 `never` |
| last_refresh_error | TEXT | 最近刷新错误 |
| refresh_token_updated_at | TIMESTAMP | Refresh Token 更新时间 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

### temp_emails

临时邮箱账号表。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | INTEGER PRIMARY KEY AUTOINCREMENT | 临时邮箱 ID |
| email | TEXT UNIQUE NOT NULL | 邮箱地址 |
| status | TEXT | 状态，默认 `active` |
| provider | TEXT | 提供商，默认 `gptmail` |
| duckmail_token | TEXT | DuckMail token |
| duckmail_account_id | TEXT | DuckMail account id |
| duckmail_password | TEXT | DuckMail password |
| cloudflare_jwt | TEXT | Cloudflare JWT |
| cloudflare_address_id | TEXT | Cloudflare address id |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

### temp_email_messages

临时邮箱邮件缓存表。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | INTEGER PRIMARY KEY AUTOINCREMENT | 消息 ID |
| message_id | TEXT UNIQUE NOT NULL | 外部消息 ID |
| email_address | TEXT NOT NULL | 临时邮箱地址，外键到 temp_emails.email |
| from_address | TEXT | 发件人 |
| subject | TEXT | 主题 |
| content | TEXT | 文本内容 |
| html_content | TEXT | HTML 内容 |
| has_html | INTEGER | 是否有 HTML |
| timestamp | INTEGER | 外部时间戳 |
| raw_content | TEXT | 原始内容 |
| created_at | TIMESTAMP | 创建时间 |

### account_refresh_logs

账号 Token 刷新日志。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | INTEGER PRIMARY KEY AUTOINCREMENT | 日志 ID |
| account_id | INTEGER NOT NULL | 账号 ID，外键到 accounts.id，级联删除 |
| account_email | TEXT NOT NULL | 账号邮箱快照 |
| refresh_type | TEXT | 刷新类型，默认 `manual` |
| status | TEXT NOT NULL | 刷新状态 |
| error_message | TEXT | 错误信息 |
| created_at | TIMESTAMP | 创建时间 |

### token_refresh_state

全局/范围刷新任务状态。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| scope_key | TEXT PRIMARY KEY | 刷新范围键，例如 `all_outlook` |
| trigger_type | TEXT | 触发类型 |
| status | TEXT | 状态，默认 `idle` |
| started_at | TIMESTAMP | 开始时间 |
| finished_at | TIMESTAMP | 结束时间 |
| total_count | INTEGER | 总数 |
| success_count | INTEGER | 成功数 |
| failed_count | INTEGER | 失败数 |
| error_summary | TEXT | 错误摘要 |
| updated_at | TIMESTAMP | 更新时间 |

### forward_logs

自动转发去重表。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | INTEGER PRIMARY KEY AUTOINCREMENT | 日志 ID |
| account_id | INTEGER NOT NULL | 账号 ID，外键到 accounts.id，级联删除 |
| message_id | TEXT NOT NULL | 邮件消息 ID |
| channel | TEXT NOT NULL | 转发渠道 |
| created_at | TIMESTAMP | 创建时间 |

唯一约束：`account_id + message_id + channel`。

### retained_normal_mail_messages

普通邮箱本地保留表，保存列表元数据和已缓存正文，不保存附件二进制。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | INTEGER PRIMARY KEY AUTOINCREMENT | 本地行 ID |
| account_id | INTEGER NOT NULL | 账号 ID，外键到 accounts.id，级联删除 |
| folder | TEXT NOT NULL | 文件夹，默认 `inbox` |
| provider_message_id | TEXT NOT NULL | 提供商消息 ID |
| id_mode | TEXT NOT NULL | ID 模式，例如 UID/sequence |
| subject | TEXT | 主题 |
| sender | TEXT | 发件人 |
| recipients | TEXT | 收件人 |
| cc | TEXT | 抄送 |
| received_at | TEXT | 接收时间文本 |
| received_at_sort | REAL | 可排序时间戳 |
| is_read | INTEGER NOT NULL | 是否已读 |
| has_attachments | INTEGER NOT NULL | 是否有附件 |
| body_preview | TEXT | 正文预览 |
| body | TEXT | 缓存正文 |
| body_type | TEXT | 正文类型，默认 `text` |
| attachments_json | TEXT | 附件元数据 JSON |
| list_cached | INTEGER NOT NULL | 是否缓存列表元数据 |
| body_cached | INTEGER NOT NULL | 是否缓存正文 |
| list_cached_at | TIMESTAMP | 列表缓存时间 |
| body_cached_at | TIMESTAMP | 正文缓存时间 |
| last_synced_at | TIMESTAMP | 最近同步时间 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

唯一索引：`account_id + folder + provider_message_id + id_mode`。

### forwarding_logs

转发执行结果日志。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | INTEGER PRIMARY KEY AUTOINCREMENT | 日志 ID |
| account_id | INTEGER NOT NULL | 账号 ID，外键到 accounts.id，级联删除 |
| account_email | TEXT NOT NULL | 账号邮箱快照 |
| message_id | TEXT NOT NULL | 邮件消息 ID |
| channel | TEXT NOT NULL | 渠道 |
| status | TEXT NOT NULL | 状态 |
| error_message | TEXT | 错误信息 |
| created_at | TIMESTAMP | 创建时间 |

### audit_logs

审计日志。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | INTEGER PRIMARY KEY AUTOINCREMENT | 日志 ID |
| action | TEXT NOT NULL | 操作 |
| resource_type | TEXT NOT NULL | 资源类型 |
| resource_id | TEXT | 资源 ID |
| user_ip | TEXT | 用户 IP |
| details | TEXT | 详情 |
| created_at | TIMESTAMP | 创建时间 |

### tags

标签表。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | INTEGER PRIMARY KEY AUTOINCREMENT | 标签 ID |
| name | TEXT UNIQUE NOT NULL | 标签名 |
| color | TEXT NOT NULL | 颜色 |
| created_at | TIMESTAMP | 创建时间 |

### account_tags

普通账号与标签关联表。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| account_id | INTEGER NOT NULL | 账号 ID，外键到 accounts.id，级联删除 |
| tag_id | INTEGER NOT NULL | 标签 ID，外键到 tags.id，级联删除 |
| created_at | TIMESTAMP | 创建时间 |

主键：`account_id + tag_id`。

### temp_email_tags

临时邮箱与标签关联表。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| temp_email_id | INTEGER NOT NULL | 临时邮箱 ID，外键到 temp_emails.id，级联删除 |
| tag_id | INTEGER NOT NULL | 标签 ID，外键到 tags.id，级联删除 |
| created_at | TIMESTAMP | 创建时间 |

主键：`temp_email_id + tag_id`。

### account_aliases

普通账号别名邮箱表。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | INTEGER PRIMARY KEY AUTOINCREMENT | 别名 ID |
| account_id | INTEGER NOT NULL | 账号 ID，外键到 accounts.id，级联删除 |
| alias_email | TEXT UNIQUE NOT NULL | 别名邮箱 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

### projects

项目表，用于外部任务按项目领取/处理邮箱。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | INTEGER PRIMARY KEY AUTOINCREMENT | 项目 ID |
| name | TEXT NOT NULL | 项目名 |
| project_key | TEXT UNIQUE NOT NULL | 项目标识 |
| description | TEXT | 描述 |
| scope_mode | TEXT NOT NULL | 范围模式，默认 `all` |
| use_alias_email | INTEGER NOT NULL | 是否使用别名邮箱 |
| status | TEXT NOT NULL | 状态，默认 `active` |
| last_scope_synced_at | TIMESTAMP | 最近范围同步时间 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

### project_group_scopes

项目限定分组表。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| project_id | INTEGER NOT NULL | 项目 ID |
| group_id | INTEGER NOT NULL | 分组 ID |
| created_at | TIMESTAMP | 创建时间 |

主键：`project_id + group_id`。

### project_accounts

项目内账号运行态表。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | INTEGER PRIMARY KEY AUTOINCREMENT | 项目账号行 ID |
| project_id | INTEGER NOT NULL | 项目 ID |
| account_id | INTEGER | 账号 ID |
| normalized_email | TEXT NOT NULL | 规范化邮箱 |
| email_snapshot | TEXT NOT NULL | 邮箱快照 |
| status | TEXT NOT NULL | 状态，默认 `toClaim` |
| deleted_from_status | TEXT | 删除前状态 |
| source_group_id | INTEGER | 来源分组 ID |
| caller_id | TEXT | 调用方 ID |
| task_id | TEXT | 外部任务 ID |
| claim_token | TEXT | 领取 token |
| claimed_at | TIMESTAMP | 领取时间 |
| lease_expires_at | TIMESTAMP | 租约过期时间 |
| last_result | TEXT | 最近结果 |
| last_result_detail | TEXT | 最近结果详情 |
| claim_count | INTEGER NOT NULL | 领取次数 |
| first_claimed_at | TIMESTAMP | 首次领取时间 |
| last_claimed_at | TIMESTAMP | 最近领取时间 |
| done_at | TIMESTAMP | 完成时间 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

唯一约束：`project_id + normalized_email`。

### project_account_events

项目账号事件日志。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | INTEGER PRIMARY KEY AUTOINCREMENT | 事件 ID |
| project_id | INTEGER NOT NULL | 项目 ID |
| account_id | INTEGER | 账号 ID |
| normalized_email | TEXT NOT NULL | 规范化邮箱 |
| project_account_id | INTEGER | 项目账号行 ID |
| action | TEXT NOT NULL | 动作 |
| from_status | TEXT | 原状态 |
| to_status | TEXT | 新状态 |
| caller_id | TEXT | 调用方 ID |
| task_id | TEXT | 外部任务 ID |
| claim_token | TEXT | 领取 token |
| detail | TEXT | 详情 JSON/文本 |
| created_at | TIMESTAMP | 创建时间 |

## 重要索引

- `accounts`：按刷新时间、刷新状态、状态、排序值、分组+创建时间、分组+排序、分组+邮箱、分组+邮箱大小写无关查询建索引。
- `account_refresh_logs`：按 `account_id` 查询。
- `forward_logs`：按 `account_id + message_id + channel` 去重/查询。
- `retained_normal_mail_messages`：唯一键和列表分页、正文补齐索引。
- `forwarding_logs`：按账号+创建时间、状态+创建时间查询。
- `account_aliases`：按账号 ID 和别名邮箱查询。
- `project_accounts`：按项目+状态、项目+租约、账号 ID、项目+邮箱查询。
- `project_group_scopes`：按分组 ID 查询。
- `project_account_events`：按项目+创建时间查询。

## 测试与文档

- `tests/`：pytest 测试，覆盖项目运行态、刷新账号判断、普通邮箱本地保留、IMAP 文件夹解析、Docker 更新、前端行为片段等。
- `docs/api.md`：API 文档。
- `docs/deployment.md`：部署说明。
- `docs/security.md`：安全说明。
- `docs/local-mail-retention.md`：普通邮箱本地保留设计与行为。
- `docs/PROJECT_KEY_STATUS_DESIGN.md`：项目 Key/状态机设计文档。
- `docs/troubleshooting.md`：常见问题。
- `docs/upgrade.md`：升级说明。
- `openspec/`：OpenSpec 设计和变更归档。

## 二开注意点

- 这是“分片 exec 到同一全局命名空间”的架构，不是包内模块显式 import 架构；新增函数名要避免和已有全局函数撞名。
- 新增数据库字段应放在 `init_db()` 的建表 SQL 和对应迁移补列逻辑中，确保新库和旧库升级一致。
- 敏感字段需要复用 `encrypt_data()` / `decrypt_data()` 或设置表的加密读写 helper。
- 生产环境保持单 worker；部分 SSE、短期任务状态、导出验证 token 是进程内状态，多 worker 会出问题。
- 普通邮箱读取链路同时涉及 Graph、Outlook IMAP、标准 IMAP、本地保留和前端缓存，改邮件列表/详情时要同时检查 `05_routes_refresh_mail.py`、`08_forwarding_scheduler_errors.py` 和 `static/js/index/05-emails.js`。
- 前端 JS 是按文件顺序加载的全局脚本，新增跨文件函数时要确认加载顺序和 `/* global ... */` 声明。
