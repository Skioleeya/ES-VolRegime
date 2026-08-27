# ES VolRegime 推进方案

## 目标

将已验证的 ES 5 分钟历史轮询链路推进为可回放、可解释的波动状态测量系统。系统只回答当前市场处于何种波动状态，不直接产生交易指令。

## 架构决策

- 实时输入采用 IBKR Historical API 轮询已完成 5 分钟 bar；不做 Tick 合成。
- 启动和每轮调度使用 IBKR server time，5 分钟边界后等待 7 秒。
- 数据库以 UTC 为规范时间，展示和交易时段判断使用 `America/New_York`。
- 所有分析只消费 completed bars；缺失、未完成、时间错位和合约不一致都显式失败。
- 模块单一职责：ingestion、metrics、benchmark、regime、replay、presentation 分离；禁止反向依赖和隐式 fallback。

## 分阶段计划

### A. 数据入口与完整性

已完成：合约确认、历史回填、服务器时间校准、单根轮询、UTC 标准化、SQLite 幂等写入、as-of replay。验收是 Linux Paper Gateway 单次请求成功且 bar 为 completed。

### B. 基础指标

当前阶段实现 Close-to-Close log return、phase 累计 realized variance、realized volatility、独立 high-low range。Overnight 为 20:15-04:00，Pre-market 为 04:00-09:30，Cash 为 09:30-12:00；elapsed key 为 phase 加分钟数。

### C. 历史基准

按同一 phase 和 elapsed key 汇总过去交易日样本。样本少于 20 时 percentile 必须为 unavailable，禁止填零、插值或跨 phase 借样本。

### D. 状态与转移

已实现 Overnight NORMAL/WEAK_COMPRESSION/STRONG_COMPRESSION、Pre-market range、breakout、acceptance、failed breakout、RV change/slope/acceleration、Cash Opening Range，以及要求 Opening Range 突破、acceptance 和 Expansion 同时满足的 Cash 方向判定。Expansion 判定器已参数化；默认 `RV percentile >= 80` 且 `RV change > 0` 是待回测的工作假设，不是最终研究结论。下一步用分层回放评估配置并编排完整状态机。确认 bars 和 hysteresis 独立配置。

### E. 回放、CLI 与展示

以 as-of replay 验证无未来数据泄漏，再接入轮询结果和分析 CLI，最后才建设 dashboard。当前只读 CLI 为 `scripts/analyze_latest.py`，Expansion 评估 CLI 为 `scripts/evaluate_expansion.py`。评估逐 session 推进，只使用更早日期样本。每阶段必须有固定数据、边界/DST、缺失数据和回放测试。

轮询运行方式：`scripts/poll_ibkr_latest.py --max-polls 1` 用于一次完整的边界对齐验收；省略 `--max-polls` 才进入持续运行。两种模式都先校准 IBKR server time，且不使用本地时间或替代数据源。Linux 部署要求见 `docs/operations.md`。

## 当前验收门槛

基础指标必须通过 20 个交易日回放；同一 elapsed key 的历史比较必须可复现；未完成 bar 不得进入指标或状态层；Cash RV 不得延续 Overnight 累计值；所有关键数值必须能追溯至 bar 和合约。Expansion 阈值在按 Phase、session 和 elapsed 分层评估前不得视为验证结论。

## 官方依据

请求和完成回调遵循 [IBKR historical bars](https://www.interactivebrokers.com/docs/tws-api/doc/market-data-historical/historical-bars/requesting-historical-bars)，服务器时间遵循 [IBKR current time](https://www.interactivebrokers.com/docs/tws-api/doc/synchronous-api/current-time)。
