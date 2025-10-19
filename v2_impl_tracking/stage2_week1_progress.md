# Stage 2 Week 1 进度记录

## 时间线
- **开始时间**: 2025-10-20 00:00
- **当前时间**: 2025-10-20 00:50
- **状态**: Layer 4 核心实现已完成，待集成测试

---

## 已完成工作 ✅

### 1. Layer 4 交叉验证模块创建

**新增文件：**
```
pyscan/layer4/
├── __init__.py              # 模块初始化，导出 CrossValidator
└── cross_validator.py       # 交叉验证核心实现 (105 行)

tests/test_layer4/
├── __init__.py              # 测试模块标记
└── test_cross_validator.py  # 完整单元测试 (370 行，10 个测试)
```

**提交信息：**
- Commit: `7e5f8df2e885b642bc35ae9e717348a9802b0768`
- Message: `feat: 实现 Layer 4 交叉验证引擎 (Stage 2 Week 1)`
- 变更: 6 files changed, 497 insertions(+)

### 2. CrossValidator 核心功能

**交叉验证策略：**
```python
# 策略 1: mypy error + LLM 确认 → 高置信度
confidence = 0.95 if llm_confirmed else 0.75

# 策略 2: mypy error + LLM 未确认 → 中等置信度
# 策略 3: mypy warning → 不报告（仅处理 error 级别）
```

**关键特性：**
- ✅ 位置匹配：支持 ±2 行容忍度
- ✅ 关键字匹配：检查 `bug_type` 和 `description` 中的 'type' 关键字
- ✅ 行号转换：正确处理绝对行号和相对行号
- ✅ 修复建议：根据 mypy 错误信息生成针对性建议

**实现细节：**
```python
# 行号转换逻辑
# mypy 使用文件绝对行号
# BugReport 使用函数相对行号
relative_line = issue.line - static_facts.function_start_line + 1

# LLM 确认检查
bug_absolute_line = bug.function_start_line + bug.start_line - 1
if abs(bug_absolute_line - mypy_issue.line) <= 2:
    # 位置匹配
    if 'type' in bug.bug_type.lower() or 'type' in bug.description.lower():
        return True  # 确认匹配
```

### 3. BugReport 数据类扩展

**修改文件：** `pyscan/bug_detector.py`

**新增字段：**
```python
@dataclass
class BugReport:
    # ... existing fields ...
    confidence: float = 1.0  # 置信度 (0.0-1.0)，默认为 1.0
    evidence: Dict[str, Any] = field(default_factory=dict)  # 证据链
```

**设计考虑：**
- 使用默认值保证向后兼容性
- `confidence=1.0` 表示传统 LLM 检测的默认置信度
- `evidence` 用于记录检测来源和交叉验证信息

### 4. 测试覆盖

**单元测试（10 个全部通过）：**
1. ✅ `test_validate_type_safety_with_llm_confirmation` - LLM 确认场景
2. ✅ `test_validate_type_safety_without_llm_confirmation` - LLM 未确认场景
3. ✅ `test_validate_type_safety_llm_position_tolerance` - 位置匹配容忍度
4. ✅ `test_validate_type_safety_llm_keyword_match` - 关键字匹配
5. ✅ `test_validate_type_safety_no_errors` - 无错误场景
6. ✅ `test_validate_type_safety_only_warnings` - 仅警告场景
7. ✅ `test_generate_fix_suggestion_incompatible_types` - 修复建议：类型不兼容
8. ✅ `test_generate_fix_suggestion_no_attribute` - 修复建议：属性错误
9. ✅ `test_generate_fix_suggestion_none` - 修复建议：None/Optional
10. ✅ `test_multiple_type_errors` - 多错误混合场景

**修复旧测试：**
- ✅ `test_bug_report_dataclass` - 添加 `function_end_line` 参数
- ✅ `test_bug_report_with_callers` - 添加 `function_end_line` 参数

**测试结果：**
```bash
============================= 92 passed in 23.78s =============================
```
- 完整测试套件：92 passed
- Layer 4 单元测试：10 passed
- 无破坏性变更

---

## 待完成工作 📋

### Phase 1: 集成到主流程（优先级：高）

**任务清单：**
- [ ] 在 `BugDetector` 或主扫描流程中调用 `CrossValidator`
- [ ] 确定集成点（在 LLM 检测后、报告生成前）
- [ ] 传递 `static_facts` 和 `llm_bugs` 给验证器
- [ ] 合并验证后的 bugs 到最终报告

**技术方案待讨论：**
1. 集成位置选择
   - 选项 A：在 `BugDetector.detect()` 中集成
   - 选项 B：在 `main.py` 扫描流程中集成
   - 选项 C：在 `context_builder` 中集成

2. 报告合并策略
   - LLM 原始 bugs + Layer 4 验证的 bugs
   - 还是仅输出 Layer 4 验证后的 bugs？
   - 如何去重？

### Phase 2: 端到端测试（优先级：中）

**任务清单：**
- [ ] 创建 `tests/test_e2e_layer4.py`
- [ ] 编写包含类型错误的示例代码
- [ ] 验证完整流程：Layer 1 → Layer 3 → Layer 4
- [ ] 验证置信度评分正确性

### Phase 3: Benchmark 验证（优先级：高）

**任务清单：**
- [ ] 在 type safety 基准测试上运行
- [ ] 对比 Recall 提升效果
- [ ] 目标：Type Safety Recall 0% → 70%+
- [ ] 记录 Precision 是否受影响

**验证命令：**
```bash
# 运行 type safety 基准测试
python -m pyscan benchmark/categories/type_safety -o type_safety_layer4_result.json

# 评估结果
python scripts/evaluate_benchmark.py type_safety_layer4_result.json
```

### Phase 4: 文档更新（优先级：低）

**任务清单：**
- [ ] 更新 `README.md` - 添加 Layer 4 说明
- [ ] 更新 `docs/architecture.md` - 架构图
- [ ] 创建 `docs/layer4_cross_validation.md` - 详细设计文档

---

## 技术债务和优化点 🔧

### 当前实现的限制：

1. **仅支持类型安全验证**
   - 当前只实现了 `validate_type_safety()`
   - 未来可扩展到其他类别（security, logic, resource）

2. **简单的关键字匹配**
   - 当前使用 `'type' in description.lower()`
   - 可能需要更智能的语义匹配

3. **固定的置信度阈值**
   - 当前硬编码 0.95 / 0.75
   - 未来可以配置化

4. **未处理 mypy warnings**
   - 当前只处理 error 级别
   - 策略 3（warning + LLM 确认）未实现

### 潜在优化方向：

1. **引入配置项**
   ```yaml
   layer4:
     confidence_threshold: 0.7
     position_tolerance: 2
     enable_warning_validation: false
   ```

2. **更智能的位置匹配**
   - 考虑代码行的语义相似度
   - 使用 AST 级别的匹配

3. **证据链可视化**
   - 在 HTML 报告中展示证据来源
   - 显示 mypy + LLM 的检测对比

---

## 预期效果 🎯

### Benchmark 目标：

**Type Safety:**
- Recall: 0% → 70%+
- Precision: 保持在 60%+ （不降低）

**整体效果：**
- 通过交叉验证减少误报
- 通过 mypy 覆盖补充 LLM 未检测到的类型错误

### 风险评估：

- ✅ **低风险**: 向后兼容，不影响现有功能
- ⚠️ **中风险**: 集成后可能需要调整参数（阈值、容忍度）
- ✅ **可回滚**: 如果效果不佳，可以快速禁用 Layer 4

---

## 下一步计划（上午继续）

### 优先级排序：

1. **[P0] 讨论集成方案** - 确定技术路线
2. **[P0] 实现集成代码** - 连接 Layer 1/3/4
3. **[P1] 运行 Benchmark** - 验证效果
4. **[P2] 端到端测试** - 确保质量
5. **[P3] 文档更新** - 记录设计

### 决策点：

需要你决策以下问题：

1. **集成位置选择**（见上文"技术方案待讨论"）
2. **报告合并策略**
   - 是否保留 LLM 原始 bugs？
   - 如何去重和标识来源？

---

## 参考文档

- 原始计划: `stage2_plan_v2.md`
- Stage 1 结果: `stage1_result.md`
- Benchmark 评估: `benchmark_evaluation_*.json`

---

**记录时间**: 2025-10-20 00:50
**下次更新**: 2025-10-20 上午（集成完成后）
