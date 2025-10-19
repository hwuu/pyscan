"""
PoC: 基于 Astroid 的上下文管理器检测

验证 Astroid 能否检测以下问题:
1. 资源未使用 with 语句管理
2. 实现了 __enter__/__exit__ 但未使用
3. 资源可能泄露
"""

import astroid
from typing import List, Dict, Any
from pathlib import Path


# 已知的资源类型（实现了上下文管理器协议）
RESOURCE_TYPES = {
    'open',  # 文件
    'ThreadPoolExecutor',
    'ProcessPoolExecutor',
    'Lock',
    'RLock',
    'Semaphore',
    'Condition',
    'socket',
    'urlopen',
    'Session',  # requests.Session
    'connection',  # 数据库连接
    'cursor',  # 数据库游标
}


class ContextManagerDetector:
    """检测上下文管理器使用问题"""

    def __init__(self):
        self.issues: List[Dict[str, Any]] = []

    def analyze_file(self, file_path: str) -> List[Dict[str, Any]]:
        """分析单个 Python 文件"""
        self.issues = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()

            module = astroid.parse(code, path=file_path)

            # 检测所有函数
            for func in module.nodes_of_class(astroid.FunctionDef):
                self._analyze_function(func, file_path)

        except Exception as e:
            print(f"解析失败 {file_path}: {e}")

        return self.issues

    def _analyze_function(self, func_node: astroid.FunctionDef, file_path: str):
        """分析单个函数中的资源使用"""

        # 收集所有赋值语句
        for assign in func_node.nodes_of_class(astroid.Assign):
            self._check_assignment(assign, func_node, file_path)

        # 检查函数调用（直接使用，未赋值）
        for call in func_node.nodes_of_class(astroid.Call):
            # 跳过赋值语句中的调用（已经在上面处理）
            if isinstance(call.parent, astroid.Assign):
                continue

            self._check_direct_call(call, func_node, file_path)

    def _check_assignment(self, assign: astroid.Assign, func_node: astroid.FunctionDef, file_path: str):
        """检查赋值语句中的资源创建"""

        if not isinstance(assign.value, astroid.Call):
            return

        call = assign.value

        # 检查是否是资源类型
        if not self._is_resource_call(call):
            return

        # 检查是否在 with 语句中
        if self._is_in_with_statement(assign):
            return  # 安全，在 with 中使用

        # 获取变量名
        var_names = [target.as_string() for target in assign.targets]

        # 检查是否有显式的清理调用
        has_cleanup = self._has_cleanup_call(func_node, var_names, call)

        if not has_cleanup:
            resource_type = self._get_resource_type_name(call)
            self.issues.append({
                'type': 'ResourceLeakRisk',
                'severity': 'high',
                'file': file_path,
                'function': func_node.name,
                'line': assign.lineno,
                'col': assign.col_offset,
                'description': f"资源 {resource_type} 未使用 with 语句管理，可能导致资源泄露",
                'variable': ', '.join(var_names),
                'resource_type': resource_type,
                'suggestion': f"建议使用 'with {call.as_string()} as {var_names[0]}:' 来管理资源"
            })

    def _check_direct_call(self, call: astroid.Call, func_node: astroid.FunctionDef, file_path: str):
        """检查直接调用（未赋值给变量）"""

        if not self._is_resource_call(call):
            return

        # 检查是否在 with 语句中
        if self._is_in_with_statement(call):
            return

        # 直接调用资源但未保存引用，可能立即被回收（依赖 __del__）
        resource_type = self._get_resource_type_name(call)
        self.issues.append({
            'type': 'ResourceImplicitCleanup',
            'severity': 'medium',
            'file': file_path,
            'function': func_node.name,
            'line': call.lineno,
            'col': call.col_offset,
            'description': f"资源 {resource_type} 直接调用未保存引用，依赖隐式清理（__del__）可能不可靠",
            'resource_type': resource_type,
            'suggestion': f"建议使用 'with {call.as_string()}:' 或显式管理资源"
        })

    def _is_resource_call(self, call: astroid.Call) -> bool:
        """判断调用是否创建了资源对象"""

        # 方法 1: 检查函数名
        func_name = self._get_call_name(call)
        if func_name in RESOURCE_TYPES:
            return True

        # 方法 2: 使用 Astroid 推断，检查返回类型是否实现了上下文管理器协议
        try:
            for inferred in call.infer():
                if isinstance(inferred, astroid.Instance):
                    cls = inferred._proxied
                    if self._has_context_manager_protocol(cls):
                        return True
        except (astroid.InferenceError, AttributeError):
            pass

        return False

    def _get_call_name(self, call: astroid.Call) -> str:
        """获取调用的函数名"""
        if isinstance(call.func, astroid.Name):
            return call.func.name
        elif isinstance(call.func, astroid.Attribute):
            return call.func.attrname
        return ""

    def _get_resource_type_name(self, call: astroid.Call) -> str:
        """获取资源类型名称（用于显示）"""
        return call.func.as_string()

    def _has_context_manager_protocol(self, cls: astroid.ClassDef) -> bool:
        """检查类是否实现了上下文管理器协议（__enter__ 和 __exit__）"""
        try:
            has_enter = '__enter__' in cls.locals or any(
                '__enter__' in base.locals for base in cls.ancestors() if isinstance(base, astroid.ClassDef)
            )
            has_exit = '__exit__' in cls.locals or any(
                '__exit__' in base.locals for base in cls.ancestors() if isinstance(base, astroid.ClassDef)
            )
            return has_enter and has_exit
        except Exception:
            return False

    def _is_in_with_statement(self, node: astroid.NodeNG) -> bool:
        """检查节点是否在 with 语句的上下文表达式中"""
        parent = node.parent

        # 向上遍历 AST，检查是否是 with 语句的 items
        while parent:
            if isinstance(parent, astroid.With):
                # 检查节点是否在 with 的 items 中
                for item_expr, _ in parent.items:
                    if node in item_expr.nodes_of_class(type(node)):
                        return True
            parent = parent.parent

        return False

    def _has_cleanup_call(self, func_node: astroid.FunctionDef, var_names: List[str], resource_call: astroid.Call) -> bool:
        """检查函数中是否有显式的清理调用"""

        # 获取资源类型对应的清理方法
        cleanup_methods = self._get_cleanup_methods(resource_call)

        if not cleanup_methods:
            return False

        # 在函数中查找对变量的方法调用
        for call in func_node.nodes_of_class(astroid.Call):
            if isinstance(call.func, astroid.Attribute):
                # 检查是否是 var_name.cleanup_method() 形式
                if isinstance(call.func.expr, astroid.Name):
                    if call.func.expr.name in var_names:
                        if call.func.attrname in cleanup_methods:
                            return True

        return False

    def _get_cleanup_methods(self, resource_call: astroid.Call) -> List[str]:
        """获取资源类型对应的清理方法名"""
        func_name = self._get_call_name(resource_call)

        cleanup_map = {
            'open': ['close'],
            'ThreadPoolExecutor': ['shutdown'],
            'ProcessPoolExecutor': ['shutdown'],
            'Lock': ['release'],
            'RLock': ['release'],
            'Semaphore': ['release'],
            'socket': ['close'],
            'Session': ['close'],
            'connection': ['close'],
            'cursor': ['close'],
        }

        return cleanup_map.get(func_name, [])


def analyze_sample_code():
    """分析示例代码"""

    # 创建测试样本
    sample_code = '''
def bad_example1():
    """不好的例子：ThreadPoolExecutor 未使用 with"""
    executor = ThreadPoolExecutor(max_workers=4)
    executor.submit(task)
    # 缺少 executor.shutdown()

def bad_example2():
    """不好的例子：文件未使用 with"""
    f = open("data.txt", "r")
    content = f.read()
    # 缺少 f.close()

def good_example1():
    """好的例子：使用 with 语句"""
    with ThreadPoolExecutor(max_workers=4) as executor:
        executor.submit(task)

def good_example2():
    """好的例子：显式清理"""
    executor = ThreadPoolExecutor(max_workers=4)
    try:
        executor.submit(task)
    finally:
        executor.shutdown()

def bad_example3():
    """不好的例子：直接调用未保存引用"""
    open("log.txt", "w").write("message")
'''

    # 保存到临时文件
    temp_file = Path("temp_sample.py")
    temp_file.write_text(sample_code, encoding='utf-8')

    try:
        # 运行检测
        detector = ContextManagerDetector()
        issues = detector.analyze_file(str(temp_file))

        # 输出结果
        print("=" * 80)
        print("PoC: 上下文管理器检测结果")
        print("=" * 80)
        print(f"\n发现 {len(issues)} 个问题:\n")

        for i, issue in enumerate(issues, 1):
            print(f"问题 {i}:")
            print(f"  类型: {issue['type']}")
            print(f"  严重程度: {issue['severity']}")
            print(f"  函数: {issue['function']}")
            print(f"  位置: 第 {issue['line']} 行, 第 {issue['col']} 列")
            print(f"  描述: {issue['description']}")
            print(f"  建议: {issue['suggestion']}")
            print()

    finally:
        # 清理临时文件
        if temp_file.exists():
            temp_file.unlink()


def analyze_real_code():
    """分析真实代码（GaussMaster 中的 bug）"""

    print("\n" + "=" * 80)
    print("分析真实代码样本")
    print("=" * 80)

    # BUG_0010 的简化版本
    real_sample = '''
async def run_in_thread_pool(func, *args, **kwargs):
    """Run function in thread pool (BUG_0010 simplified)"""
    executor = ThreadPoolExecutor(max_workers=1)
    loop = asyncio.get_event_loop()
    return await run_in_executor(executor, func, *args, **kwargs)
'''

    temp_file = Path("temp_real_sample.py")
    temp_file.write_text(real_sample, encoding='utf-8')

    try:
        detector = ContextManagerDetector()
        issues = detector.analyze_file(str(temp_file))

        print(f"\n发现 {len(issues)} 个问题:\n")

        for i, issue in enumerate(issues, 1):
            print(f"问题 {i}:")
            print(f"  函数: {issue['function']}")
            print(f"  位置: 第 {issue['line']} 行")
            print(f"  资源类型: {issue['resource_type']}")
            print(f"  描述: {issue['description']}")
            print(f"  建议: {issue['suggestion']}")
            print()

            # 验证是否匹配 BUG_0010
            if issue['resource_type'] == 'ThreadPoolExecutor':
                print("  [SUCCESS] 成功检测到 BUG_0010 类型的问题!")
            print()

    finally:
        if temp_file.exists():
            temp_file.unlink()


if __name__ == '__main__':
    print("开始 PoC 测试...\n")

    # 测试示例代码
    analyze_sample_code()

    # 测试真实代码
    analyze_real_code()

    print("=" * 80)
    print("PoC 测试完成!")
    print("=" * 80)
