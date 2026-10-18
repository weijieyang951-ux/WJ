# 美股每日研究系统

Python 3.12；使用可复现量化指标和中文规则摘要。默认模拟模式，模拟代码 SIMxxxx 不代表真实证券。真实行情接入 Polygon，需要具备全市场、历史日线和股票详情权限的套餐。本版本是经过模拟验收的部署基础，尚未实盘验收，不宣称已满足所有生产条件。

## 本地运行

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
# Ubuntu: sudo apt-get install fonts-noto-cjk
python -m research.pipeline --provider mock --date 2026-10-16
pytest -q
# 设置环境变量 POLYGON_API_KEY 后
python -m research.pipeline --provider polygon --date 2026-10-16
```

默认输出 `runs/{mock|polygon}/{交易日}/`：300 份各自 JSON/CSV/HTML、汇总 reports.json/csv、25 张 PNG、posters.zip、market.html/json、ranking.csv、backtest.json、prediction-history.csv、resolved-predictions.json、layout.json、成本与日志。失败仅保留 .partial，成功后才写完成标记。不要把生成数据或 .env 提交 Git。

## 方法和缺失数据

股票仅限活跃美国交易所普通股 CS，排除 ETF、权证和其他证券类型。至少 220 根有效日线；剔除陈旧行情、重复日期、零成交量、异常 OHLC、低价或低流动性证券。不能获取 300 只有效证券时直接失败。

评分在合格股票横截面内作百分位标准化。权重在 config/settings.json 配置，缺失项重新分配权重，coverage 记录有效权重；应注意缺失模式不同的证券可比性受限。momentum 为 20 日动量绝对值与 ATR/价格，technical 为 RSI 偏离及 MACD 差幅度。成交额是收盘价乘成交量近似值。

新闻获取不到不会补造。社交和财报事件接口尚未接入，明确标记缺失。主题采用 config/themes.json 人工维护，不将行业等同于已验证主题；未知证券可无主题，空海报明确提示。科技七巨头最多七只符合资格的成员，允许不足八只。

RSI/MACD/ATR 使用 ta 库，均线 20/50/200。下一交易日判断使用收盘价相对 MA20 与 MACD 相对信号线的固定规则。三种情景为条件式水平判断，不是概率预测。当前未部署任何概率模型，因此永远不输出上涨概率。无 LLM 调用，成本记录 LLM=0，供应商订阅成本未知而非零。

回测每只股票使用逐步扩大的训练前缀、40 日测试块和下一日收益，10bp 换仓成本；规则预先固定，不拟合。回测有当前股票池幸存者偏差，不是历史 Top300 策略回测；未建模借券和完整滑点，不作为上线交易依据。历史预测只用实际可得的下一交易日收盘价结算。

## GitHub 部署

1. 将源代码提交并推送到目标仓库默认分支（当前环境仓库没有初始提交）。
2. Settings → Secrets and variables → Actions：添加 POLYGON_API_KEY。可选 TELEGRAM_BOT_TOKEN 和 TELEGRAM_CHAT_ID；只在配置后发送通知。
3. Actions → Daily US equity analysis → Run workflow，先选 mock，下载 research-* Artifact 验收。
4. 用 polygon 手动跑指定交易日，确认行情套餐、耗时和数据质量，再使用定时任务。

UTC cron 多次唤醒，由 America/New_York 和 NYSE 日历判断 17:30 ET，覆盖夏令时、节假日、提前收市和次日 09:00 前的触发延迟。更长延迟用手工交易日补跑。concurrency 串行；state 完成标记防重复。历史 SQLite 和完成标记使用独立 Actions Artifact 逐次恢复；上传失败会使 workflow 失败。Artifact 保留 90 天，需长期外部存储归档；首次运行或历史过期会明确记录，无法保证无限期保存。仓库禁用 Actions 或排程长期不活跃时无法自动执行。

真实全市场逐只拉取 800 日行情和证券详情成本较高；默认 300 RPM，免费 5 RPM 不适合全市场日更，应使用有足够额度的订阅并调整适配器。缓存带 TTL 和限速重试。运行超时仍会上传 .partial 和日志，不能当完整报告。

## 模板与测试

black_gold 黑金、navy 深蓝、ivory 象牙三套程序模板，1080×1920 PNG。Pillow 用实际字体测量每段文字边界，溢出缩字号，仍溢出则失败。每张海报最多 15 只，不为凑数补股票。布局与成员清单支持自动核验。测试涵盖时间门控、夏令时、节假日、提前收市、权重标准化、缺失降级、指标无未来数据、三套模板与全部产出计数。

## 上线前尚需完成

实盘 API 联调、供应商字段与权限验证；更完整可审计的主题分类；真实财报与社交源接入；按历史时点复原股票池回测；外部持久存储与告警演练。LLM 中文摘要为可选后续功能，应只接收验证后的结构化事实。不要将模拟测试或技术指标方向称为已校准预测。

## 本次部署更新

海报已经改成英文，25 个英文标题在 `config/settings.json` 的 poster_titles 配置。结构化研究报告仍为中文。默认字体使用 DejaVu Sans，三套模板的配色和排版在 research/render.py 纳入版本控制。

海报采用参考图风格的日期徽标、金色标题、抽象行情背景、彩色股票卡片和 Market View 面板；背景图形是装饰，并非实际行情走势。默认 black_gold，另保留 navy/ivory 配色。科技七巨头最多七只，其他主题最多十五只，较多成员自动排列成卡片网格。显示收盘价、当日涨跌幅和规则信号；单排卡片还显示支撑/阻力，不生成未经验证的预测涨跌幅。模拟数据明确标注 SIMULATED DATA。新增回归测试覆盖七列窄卡、最长股票代码、数值一致性及文字无重叠。

独立复测且保留旧输出：

```bash
python -m research.pipeline --provider mock --date 2026-10-16 --out runs/reference-style --state state/reference-style
python scripts/validate_outputs.py runs/reference-style/mock/2026-10-16
pytest -q
```

本地输出到可写的 runs/，可用 --out 指定其他可写目录；不要使用当前机器没有权限创建的 /codex 路径。云端使用 GitHub runner 工作区，无需对系统目录 chmod。

Actions 会先执行 300 只 mock 端到端验收，再在 polygon 模式执行 AAPL 真实 API 冒烟测试，之后执行完整股票池。每次 push main/work 会运行 mock；workflow_dispatch 可选 mock/polygon；定时模式为 polygon。Secrets 只在 runner 内注入，GitHub 不提供下载 Secret 明文的 API。

运行前设置 Repository Variables `POLYGON_RPM` 为供应商套餐允许的每分钟请求数（未配置时保守使用 5）；全市场逐只历史接口在免费额度下可能超时。请先用真实冒烟测试确认权限，再为全市场运行配置足够额度。不要为了加速设置超过套餐的限额。

手动：Actions → Daily US equity analysis → Run workflow → provider=mock（或 polygon），session 可留空自动选择最近已结束交易日，template 可选 black_gold/navy/ivory。结果下载 research-{run_id}，保留 90 天；独立 research-state 保存跨日历史。可选 Telegram 配置后会发送成功或失败通知。
