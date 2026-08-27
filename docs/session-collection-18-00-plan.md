# ES 18:00-12:00 持续采集完整方案

## 1. 目标

对每个 CME Equity 正确交易日，完整采集前一日 18:00 ET 至当日 12:00 ET 的 ES 5 分钟已完成 bar，并持久化到 SQLite。系统必须在进程重启、短暂断线和跨 DST、周末、节假日时识别缺口并补齐。

本方案只改变采集窗口，不改变 RV、压缩、扩张或交易信号的研究含义。

## 2. 统一时间与交易日定义

- `session_start = 18:00 ET`，`session_end = 12:00 ET`。
- `session_date = D` 表示 `D-1 18:00 ET <= bar_start < D 12:00 ET`。
- Overnight 改为 `18:00-04:00 ET`；Pre-market 为 `04:00-09:30 ET`；Cash 为 `09:30-12:00 ET`。
- 边界使用 `America/New_York` 计算，数据库使用 UTC；禁止固定 UTC-4/UTC-5。
- 交易日由 `CME_Equity` 日历产生，不以自然日或本地星期判断。

## 3. 配置改造

必须建立唯一配置源，例如 `src/config/settings.py` 的不可变 `Settings` 对象；环境变量只负责覆盖明确的部署参数。时间、bar 间隔、轮询延迟、回看天数、最小样本和状态阈值全部从该配置读取，禁止业务模块定义自己的默认常量或重复解析环境变量：

```text
session_start_et=18:00
overnight_end_et=04:00
premarket_start_et=04:00
premarket_end_et=09:30
cash_start_et=09:30
session_end_et=12:00
bar_interval_minutes=5
poll_finalize_delay_seconds=7
lookback_days=60
minimum_history_samples=20
```

白皮书、`request_plan.py`、`report.py`、`metrics.py` 和运维文档必须使用同一配置来源。

配置加载在进程启动时完成并校验：时区必须为 `America/New_York`，阶段必须连续且不重叠，窗口起止必须有效，bar 间隔必须整除阶段边界。缺少配置或配置非法时立即失败，不提供隐式 fallback。测试必须验证所有模块收到同一个配置实例，并验证 18:00 改动只需修改配置即可传播到请求、分段、质量报告和调度。

## 4. 采集器生命周期

实现按交易日运行的 session scheduler：

1. 使用 IBKR server time 校准当前时间。
2. 根据 CME 日历找到下一个有效 `session_date`。
3. 前一日 18:00 ET 前不请求研究 bar，边界后每 5 分钟请求一次。
4. 每次只接受唯一的已完成目标 bar，目标区间为 `[boundary-5m, boundary)`。
5. 当日 12:00 ET 停止该 session，不请求窗口外数据。
6. 等待下一个有效交易日；周末、节假日和非研究时段不轮询。

每个 session 记录 `STARTED`、`RUNNING`、`COMPLETE` 或 `DEGRADED` 状态。

## 5. 重启、断线与补缺

新增 session 进度和请求审计：session 标签、窗口起止、最后成功 bar、状态、错误、请求目标时间和返回范围。

启动、重连或恢复时：

1. 读取当前 session 窗口和数据库已有 bar。
2. 按 5 分钟网格计算缺口。
3. 通过历史 API 分块补齐缺口，遵守 IBKR pacing 限制。
4. 通过质量检查后恢复实时轮询。
5. 无法补齐时标记 `DEGRADED` 或 `DATA_INSUFFICIENT`，不得伪造 bar、使用未完成 bar 或切换数据源。

重试必须有限、可审计并有退避；失败必须显式暴露。

## 6. 持久化与幂等

继续使用 `(con_id, bar_start_utc)` 作为 bar 主键并 upsert。增加 session coverage 表，记录预期数量、实际数量、首尾时间和缺口。合约身份必须包含 `con_id`、`local_symbol`、`contract_month`；换月不得覆盖旧合约。只有 `is_complete=1` 的 bar 才能进入指标层。

## 7. 完整性规则

每个正常 session 覆盖 18:00 至 12:00 的 5 分钟网格，采用左闭右开区间；预期数量由实际 CME 日历和特殊时段决定。必须检查：时间戳在窗口内且对齐 5 分钟、无重复、无未来 bar、无未完成 bar、合约一致，并能审计缺口、DST、周末和节假日边界。只有 `COMPLETE` session 才进入 RV、百分位和 regime。

## 8. 实施顺序

### Phase A: 时间语义

统一配置、session label、18:00 分段和请求边界；更新白皮书和文档。

### Phase B: 数据模型与覆盖检查

增加 session progress/coverage、缺口计算器和完整性报告。

### Phase C: 受控轮询

将 `poll_ibkr_latest.py` 改为 session scheduler，支持一次运行、指定交易日、持续模式和 12:00 停止。

### Phase D: 恢复与补数

实现启动补缺、断线重连、有限重试、pacing 保护和失败状态。

### Phase E: 回放与指标接入

用固定历史数据验证每日 coverage，再让指标和 regime 只消费完整 session；重新验证 elapsed key、as-of replay 和 20 日历史基准。

### Phase F: 部署

使用 systemd 或等价 supervisor 自动拉起进程，配置日志轮转、健康检查、磁盘告警和 Gateway 依赖检查。部署前完成完整交易日和人为断线恢复验收。

## 9. 验收标准

- 连续至少 5 个正常交易日，每个 session 为 `COMPLETE`；
- 18:00、04:00、09:30、12:00 的 ET/UTC 边界正确；
- 停止后重启能自动补齐且无重复；
- 断线恢复后 coverage 完整；
- 周末、假日和 DST 切换不生成错误 session；
- 合约换月不混淆历史数据；
- 测试、固定 replay、质量报告和 `git diff --check` 通过；
- 任何缺口或样本不足都显式暴露，不产生伪造 RV 或 regime。
- 删除或修改统一配置中的窗口值后，不能仍有模块使用旧的硬编码 20:15 值；配置扫描和测试必须阻止回归。

## 10. 当前结论

现有系统已有 completed-bar 获取、UTC/ET 模型和 SQLite 幂等写入基础，但尚不能直接满足上述保证。必须先完成 Phase A-D，才可宣称每个正确交易日完整采集 18:00-次日 12:00 并可靠持久化。
