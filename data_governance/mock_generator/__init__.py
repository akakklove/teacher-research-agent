"""
Mock Data Generator - 根据 Schema 生成模拟科研数据
保证表间外键一致性，数据符合业务逻辑
"""
from .generator import MockDataGenerator
from .config import MockConfig

__all__ = ['MockDataGenerator', 'MockConfig']
