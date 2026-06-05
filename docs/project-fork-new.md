# Project Fork New

## a89b0a3 - feat: add forwarding group labels and project map

本次提交新增了邮件转发的“附加邮箱分组”能力。

- 在“邮件转发设置”中新增“附加邮箱分组”开关，默认关闭。
- 新增设置项 `forward_include_account_group`，通过设置 API 读写并持久化到 SQLite `settings` 表。
- 转发轮询读取账号时关联 `groups` 表，拿到账号所属分组名。
- 开启后，Telegram 和企业微信转发文本会在时间后追加 `分组: xxx`。
- 开启后，SMTP 转发只在转发邮件的顶部元信息区追加分组行，不修改原邮件正文内容。
- 增加转发相关测试，覆盖默认关闭不输出分组、开启后输出账号分组的行为。
- 补充 `docs/project-map.md`，记录项目结构、技术栈、数据库表和二开注意点。
