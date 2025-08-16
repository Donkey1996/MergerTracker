"""
Database adapters for MergerTracker backend

This module provides a flexible database abstraction layer that supports
multiple database backends (PostgreSQL/TimescaleDB, Supabase, Firebase).
"""

from .base import (
    DatabaseAdapter, 
    DatabaseConfig, 
    DatabaseError, 
    ConnectionError, 
    ValidationError, 
    NotFoundError, 
    DuplicateError
)
from .postgresql_adapter import PostgreSQLAdapter
from .supabase_adapter import SupabaseAdapter

__all__ = [
    'DatabaseAdapter',
    'DatabaseConfig',
    'DatabaseError',
    'ConnectionError',
    'ValidationError',
    'NotFoundError',
    'DuplicateError',
    'PostgreSQLAdapter', 
    'SupabaseAdapter'
]