"""
Layer 4: 验证和融合层

Layer 4 负责交叉验证和融合来自不同层的分析结果，提高检测的准确性。

主要功能：
1. 交叉验证：Layer 1（静态工具）+ Layer 3（LLM）的结果验证
2. 置信度评分：基于多层证据链计算置信度
3. 误报过滤：通过多层验证过滤误报

组件：
- CrossValidator: 交叉验证引擎
"""

from pyscan.layer4.cross_validator import CrossValidator

__all__ = ['CrossValidator']
