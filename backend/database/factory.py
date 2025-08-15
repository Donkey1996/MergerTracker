"""
Database adapter factory for MergerTracker

This module provides a factory pattern for creating database adapters
based on configuration settings.
"""

import logging
from typing import Dict, Any
from .adapters.base import DatabaseAdapter, DatabaseConfig
from .adapters.postgresql_adapter import PostgreSQLAdapter

logger = logging.getLogger(__name__)


class DatabaseFactory:
    """Factory for creating database adapters"""
    
    _adapters = {
        'postgresql': PostgreSQLAdapter,
        'timescale': PostgreSQLAdapter,  # TimescaleDB uses PostgreSQL adapter
        # 'supabase': SupabaseAdapter,     # To be implemented
        # 'firebase': FirebaseAdapter,     # To be implemented
    }
    
    @classmethod
    def create_adapter(cls, config: DatabaseConfig) -> DatabaseAdapter:
        """Create a database adapter based on configuration"""
        adapter_type = config.adapter_type.lower()
        
        if adapter_type not in cls._adapters:
            raise ValueError(f"Unsupported database adapter type: {adapter_type}")
        
        adapter_class = cls._adapters[adapter_type]
        return adapter_class(config.connection_params)
    
    @classmethod
    def get_supported_adapters(cls) -> list:
        """Get list of supported adapter types"""
        return list(cls._adapters.keys())
    
    @classmethod
    def register_adapter(cls, adapter_type: str, adapter_class):
        """Register a new adapter type"""
        cls._adapters[adapter_type] = adapter_class
        logger.info(f"Registered new adapter type: {adapter_type}")


def create_database_adapter(
    adapter_type: str,
    connection_params: Dict[str, Any],
    **kwargs
) -> DatabaseAdapter:
    """Convenience function to create a database adapter"""
    config = DatabaseConfig(
        adapter_type=adapter_type,
        connection_params=connection_params,
        **kwargs
    )
    
    return DatabaseFactory.create_adapter(config)


def get_database_config_from_env() -> DatabaseConfig:
    """Get database configuration from environment variables"""
    import os
    
    adapter_type = os.getenv('DATABASE_ADAPTER', 'postgresql')
    
    if adapter_type.lower() in ['postgresql', 'timescale']:
        connection_params = {
            'host': os.getenv('DATABASE_HOST', 'localhost'),
            'port': int(os.getenv('DATABASE_PORT', 5432)),
            'database': os.getenv('DATABASE_NAME', 'mergertracker'),
            'username': os.getenv('DATABASE_USER', 'postgres'),
            'password': os.getenv('DATABASE_PASSWORD', ''),
        }
    elif adapter_type.lower() == 'supabase':
        connection_params = {
            'url': os.getenv('SUPABASE_URL'),
            'key': os.getenv('SUPABASE_ANON_KEY'),
            'service_key': os.getenv('SUPABASE_SERVICE_KEY'),
        }
    elif adapter_type.lower() == 'firebase':
        connection_params = {
            'project_id': os.getenv('FIREBASE_PROJECT_ID'),
            'credentials_path': os.getenv('FIREBASE_CREDENTIALS_PATH'),
            'database_url': os.getenv('FIREBASE_DATABASE_URL'),
        }
    else:
        raise ValueError(f"Unknown adapter type: {adapter_type}")
    
    return DatabaseConfig(
        adapter_type=adapter_type,
        connection_params=connection_params,
        pool_size=int(os.getenv('DATABASE_POOL_SIZE', 10)),
        max_overflow=int(os.getenv('DATABASE_MAX_OVERFLOW', 20)),
        pool_timeout=int(os.getenv('DATABASE_POOL_TIMEOUT', 30)),
        echo=os.getenv('DATABASE_ECHO', '').lower() == 'true'
    )