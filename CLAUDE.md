1. 如果我要求先讨论方案时不要着急修改代码，直到方案确定才可以修改代码。

2. 方案讨论需要在我们双方都没疑问的情况下才可以输出具体方案文档。

3. 方案评估请主动思考需求边界，合理质疑当下方案的完善性，方案需包含：重要逻辑的实现思路、需求按技术实现的依赖关系拆解并排序，便于后续渐进式开发、输出修改或新增文件的路径、输出测试要点利于需求完成后的自动化测试。

4. 方案讨论或代码编写时，如果遇到了争议或不确定性请主动告知我，请牢记让我决策而不是默认采用一种方案实现，重点强调。

5. 开发项目必须严格按步骤执行，每次只专注当前讨论的步骤，要求：不允许跨步骤实现功能或"顺便"完成其他步骤任务、实现前必须先确认技术方案和实现细节、每个步骤完成后必须明确汇报，等待 Review 确认后才能进入下一步。

6. 进行代码提交时，请先给我梳理提交的内容，等待 Review 确认后才能进行提交。

7. 与第五,六点类似，任何代码修改请始终遵守最小改动原则，除非我主动要求优化或者重构。

8. 代码实现请先思考哪些业务可以参考或复用，尽可能参考现有业务的实现风格，如果你不明确可让我为你提供，避免重复造轮子。

9. 不要在源码中插入mock的硬编码数据。

10. 同步更新相关文档。

11. 使用TDD开发模式开发。

12. 小步快跑，对一步都进行测试，并保证不影响现有用例。

13. 使用中文回答

14. 记得每次测试完后，清理下测试文件。

15. 在 bug 修复时如果超过 2 次修复失败，请主动添加关键日志后再进行尝试修复，在我反馈修复后主动清除之前的日志信息。

16. 项目中的重试过2次以上环境配置问题或其他重复犯错的问题，请在项目的CLAUDE.md中做记录。常用的命令，请记录在项目的CLAUDE.md中。

---

## 常见问题记录

### Windows 路径解析问题

**问题**：在 Windows 环境下，使用简单的 `split(':')` 解析包含文件路径的工具输出会失败。

**原因**：Windows 绝对路径包含盘符（如 `C:\`），冒号会干扰基于冒号的分割逻辑。

**示例**：
```
mypy 输出: C:\Users\hwuu\file.py:3:12: error: Message
简单分割: ['C', '\Users\hwuu\file.py', '3', '12', ' error: Message']  # 错误！
```

**解决方案**：使用正则表达式匹配关键信息，绕开路径部分：
```python
import re
match = re.search(r':(\d+):(\d+):\s*(\w+):\s*(.+)', line)
if match:
    line_num = int(match.group(1))
    col_num = int(match.group(2))
    severity = match.group(3)
    message = match.group(4)
```

**影响模块**：`pyscan/layer1/mypy_analyzer.py`

---

## 常用命令

### 测试命令
```bash
# 运行所有测试
python -m pytest tests/ -v

# 运行特定测试文件
python -m pytest tests/test_layer1/test_mypy_analyzer.py -v

# 运行特定测试（显示输出）
python -m pytest tests/test_e2e_layer1.py::TestLayer1E2E::test_analyze_code_with_type_errors -v -s

# 运行测试并查看覆盖率
python -m pytest tests/ --cov=pyscan --cov-report=html
```

### 开发命令
```bash
# 安装依赖
pip install -r requirements.txt

# 运行 pyscan
python -m pyscan <目录> --config config.yaml
```
