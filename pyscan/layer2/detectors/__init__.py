"""
Layer 2 检测器集合
"""

from .base import BaseDetector
from .resource_leak import ResourceLeakDetector

__all__ = ['BaseDetector', 'ResourceLeakDetector']
