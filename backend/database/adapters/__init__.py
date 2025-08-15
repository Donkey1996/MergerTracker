"""
Database adapters for MergerTracker backend

This module provides a flexible database abstraction layer that supports
multiple database backends (PostgreSQL/TimescaleDB, Supabase, Firebase).
"""

from .base import DatabaseAdapter
from .postgresql_adapter import PostgreSQLAdapter
from .supabase_adapter import SupabaseAdapter
from .firebase_adapter import FirebaseAdapter

__all__ = [
    'DatabaseAdapter',
    'PostgreSQLAdapter', 
    'SupabaseAdapter',
    'FirebaseAdapter'
]