# 部署验收记录（2026-10-18）

仓库：https://github.com/weijieyang951-ux/WJ （public）。开始时本地 work 分支无提交；远程无已有分支；仓库源码可写。

## 已通过
- Python 3.12.14，15 个 pytest 用例通过。
- 2026-10-16 mock：360 合格候选中去重 Top300，300 份各自 JSON/CSV/HTML。
- 25 张英文 PNG 均为 1080×1920，英文文字、边界、成员、ZIP 验证通过；黑金海报目视检查通过。
- 三套程序渲染模板，结构化报告保留中文。
- 限速、429/503 重试、缓存、URL 白名单、凭据不写缓存和异常脱敏测试通过。
- Actions 支持 push mock、手动 mock/polygon、UTC schedule + ET/NYSE 门控、Artifacts 90 天、历史恢复与可选 Telegram 通知。
- requirements.lock 仅锁定项目及传递依赖，未包含环境专属 file:// 包。

## 未完成的外部验收
- 本地 API 冒烟测试停止：POLYGON_API_KEY 未注入本地运行环境（未发起真实行情请求）。
- 本地 gh 认证不可用，Secrets 列表 Forbidden，无法判断仓库是否已配置所需 Secret；不得把这个结果写成 Secret 已缺失。
- 云端真实 API 完整运行尚待确认。
- 社交/财报源、历史时点股票池回测和长期外部归档仍是既有待办；没有经过校准的概率模型。

## 输出权限
- runs/ 与 output/ 在仓库工作区可写，配置 --out 可切换可写输出路径。
- 当前执行环境根目录不允许创建 /codex，无法修复聊天平台指定下载目录的系统权限；不影响 GitHub runner 的 Artifacts 产出。

## 所需配置
- 必需 GitHub Actions Secret：POLYGON_API_KEY。
- 可选 Secret：TELEGRAM_BOT_TOKEN、TELEGRAM_CHAT_ID。
- Variable：POLYGON_RPM，按套餐配置；默认 5 RPM 仅适合保守探测，不适合全市场时限。
- 禁止把密钥写进代码、参数 URL、日志、缓存或提交。

部署提交 7c8fac7 已非强制推送到 main；首个云端运行： https://github.com/weijieyang951-ux/WJ/actions/runs/39116819147 。追加 push 后的 live-acceptance 作业在 mock 成功后执行真实 API 冒烟测试并独立上传报告。
