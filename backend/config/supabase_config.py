"""
Supabase configuration utilities for MergerTracker

This module provides configuration utilities specifically for Supabase
database adapter including connection validation, environment variable
handling, and configuration templates.
"""

import os
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


@dataclass
class SupabaseConfig:
    """Supabase configuration container"""
    
    url: str
    anon_key: Optional[str] = None
    service_key: Optional[str] = None
    jwt_secret: Optional[str] = None
    project_id: Optional[str] = None
    
    # Connection options
    timeout: int = 30
    retry_count: int = 3
    
    # Feature flags
    enable_realtime: bool = True
    enable_auth: bool = True
    enable_storage: bool = False
    
    # Schema settings
    schema: str = "public"
    auto_refresh_token: bool = True
    
    def __post_init__(self):
        """Validate configuration after initialization"""
        self.validate()
        
        # Extract project ID from URL if not provided
        if not self.project_id and self.url:
            parsed_url = urlparse(self.url)
            if parsed_url.hostname:
                # Extract project ID from Supabase URL format
                # e.g., https://projectid.supabase.co
                hostname_parts = parsed_url.hostname.split('.')
                if len(hostname_parts) >= 3 and hostname_parts[1] == 'supabase':
                    self.project_id = hostname_parts[0]
    
    def validate(self) -> None:
        """Validate the Supabase configuration"""
        if not self.url:
            raise ValueError("Supabase URL is required")
        
        if not self.url.startswith(('http://', 'https://')):
            raise ValueError("Supabase URL must include protocol (http:// or https://)")
        
        if not self.service_key:
            logger.warning(
                "Service key not provided. Database operations will use anon key with limited permissions."
            )
        
        if not self.anon_key and not self.service_key:
            raise ValueError("At least one of anon_key or service_key must be provided")
        
        # Validate timeout values
        if self.timeout <= 0:
            raise ValueError("Timeout must be positive")
        
        if self.retry_count < 0:
            raise ValueError("Retry count must be non-negative")
    
    def get_connection_params(self) -> Dict[str, Any]:
        """Get connection parameters for the Supabase adapter"""
        return {
            'url': self.url,
            'anon_key': self.anon_key,
            'service_key': self.service_key,
            'timeout': self.timeout,
            'retry_count': self.retry_count,
            'schema': self.schema,
            'auto_refresh_token': self.auto_refresh_token
        }
    
    def get_client_options(self) -> Dict[str, Any]:
        """Get client options for Supabase client initialization"""
        return {
            'postgrest_client_timeout': self.timeout,
            'storage_client_timeout': self.timeout if self.enable_storage else None,
            'schema': self.schema,
            'auto_refresh_token': self.auto_refresh_token,
            'persist_session': True,
            'detect_session_in_url': self.enable_auth,
            'headers': {
                'User-Agent': 'MergerTracker/1.0'
            }
        }
    
    @property
    def is_production(self) -> bool:
        """Check if this is a production Supabase instance"""
        return 'supabase.co' in self.url
    
    @property
    def is_local(self) -> bool:
        """Check if this is a local Supabase instance"""
        return 'localhost' in self.url or '127.0.0.1' in self.url


def create_supabase_config_from_env() -> SupabaseConfig:
    """Create Supabase configuration from environment variables"""
    
    # Required environment variables
    url = os.getenv('SUPABASE_URL')
    if not url:
        raise ValueError("SUPABASE_URL environment variable is required")
    
    # Optional environment variables
    anon_key = os.getenv('SUPABASE_ANON_KEY')
    service_key = os.getenv('SUPABASE_SERVICE_KEY')
    jwt_secret = os.getenv('SUPABASE_JWT_SECRET')
    
    # Connection settings
    timeout = int(os.getenv('SUPABASE_TIMEOUT', '30'))
    retry_count = int(os.getenv('SUPABASE_RETRY_COUNT', '3'))
    
    # Feature flags
    enable_realtime = os.getenv('SUPABASE_ENABLE_REALTIME', 'true').lower() == 'true'
    enable_auth = os.getenv('SUPABASE_ENABLE_AUTH', 'true').lower() == 'true'
    enable_storage = os.getenv('SUPABASE_ENABLE_STORAGE', 'false').lower() == 'true'
    
    # Schema settings
    schema = os.getenv('SUPABASE_SCHEMA', 'public')
    auto_refresh_token = os.getenv('SUPABASE_AUTO_REFRESH_TOKEN', 'true').lower() == 'true'
    
    return SupabaseConfig(
        url=url,
        anon_key=anon_key,
        service_key=service_key,
        jwt_secret=jwt_secret,
        timeout=timeout,
        retry_count=retry_count,
        enable_realtime=enable_realtime,
        enable_auth=enable_auth,
        enable_storage=enable_storage,
        schema=schema,
        auto_refresh_token=auto_refresh_token
    )


def validate_supabase_connection(config: SupabaseConfig) -> Dict[str, Any]:
    """Validate Supabase connection and return status information"""
    validation_result = {
        'valid': False,
        'project_id': config.project_id,
        'url_valid': False,
        'keys_valid': False,
        'features': {
            'realtime': config.enable_realtime,
            'auth': config.enable_auth,
            'storage': config.enable_storage
        },
        'warnings': [],
        'errors': []
    }
    
    try:
        # Validate URL format
        parsed_url = urlparse(config.url)
        if parsed_url.scheme in ('http', 'https') and parsed_url.netloc:
            validation_result['url_valid'] = True
        else:
            validation_result['errors'].append("Invalid URL format")
        
        # Validate keys
        if config.service_key or config.anon_key:
            validation_result['keys_valid'] = True
        else:
            validation_result['errors'].append("No API keys provided")
        
        # Check for development vs production
        if config.is_local:
            validation_result['warnings'].append("Using local Supabase instance")
        elif not config.is_production:
            validation_result['warnings'].append("Using non-standard Supabase URL")
        
        # Validate key formats (basic check)
        if config.service_key and not config.service_key.startswith('sbp_'):
            validation_result['warnings'].append("Service key format looks incorrect")
        
        if config.anon_key and not config.anon_key.startswith('eyJ'):
            validation_result['warnings'].append("Anon key format looks incorrect")
        
        # Overall validation
        validation_result['valid'] = (
            validation_result['url_valid'] and 
            validation_result['keys_valid'] and 
            len(validation_result['errors']) == 0
        )
        
    except Exception as e:
        validation_result['errors'].append(f"Validation error: {str(e)}")
    
    return validation_result


def get_supabase_environment_template() -> str:
    """Get a template for Supabase environment variables"""
    return """
# Supabase Configuration
# ======================

# Required: Your Supabase project URL
SUPABASE_URL=https://your-project.supabase.co

# Required: Service role key (for backend operations)
SUPABASE_SERVICE_KEY=sbp_your_service_role_key_here

# Optional: Anonymous key (for client-side operations)
SUPABASE_ANON_KEY=eyJ...your_anon_key_here

# Optional: JWT secret (for token verification)
SUPABASE_JWT_SECRET=your-jwt-secret

# Connection Settings
SUPABASE_TIMEOUT=30
SUPABASE_RETRY_COUNT=3

# Feature Toggles
SUPABASE_ENABLE_REALTIME=true
SUPABASE_ENABLE_AUTH=true
SUPABASE_ENABLE_STORAGE=false

# Schema Settings
SUPABASE_SCHEMA=public
SUPABASE_AUTO_REFRESH_TOKEN=true

# Database Adapter Selection
DATABASE_ADAPTER=supabase
"""


def create_connection_string(config: SupabaseConfig) -> str:
    """Create a connection string for logging/monitoring purposes"""
    # Don't include sensitive information in connection string
    return f"supabase://{config.project_id or 'unknown'}@{urlparse(config.url).netloc}"


def log_supabase_config(config: SupabaseConfig) -> None:
    """Log Supabase configuration for debugging (without sensitive data)"""
    logger.info("Supabase Configuration:")
    logger.info(f"  Project ID: {config.project_id}")
    logger.info(f"  URL: {config.url}")
    logger.info(f"  Schema: {config.schema}")
    logger.info(f"  Timeout: {config.timeout}s")
    logger.info(f"  Retry Count: {config.retry_count}")
    logger.info(f"  Features: realtime={config.enable_realtime}, auth={config.enable_auth}, storage={config.enable_storage}")
    logger.info(f"  Environment: {'production' if config.is_production else 'development'}")
    
    # Log key availability without exposing the keys
    logger.info(f"  Service Key: {'provided' if config.service_key else 'not provided'}")
    logger.info(f"  Anon Key: {'provided' if config.anon_key else 'not provided'}")


def get_supabase_migration_info() -> Dict[str, str]:
    """Get information about Supabase migrations"""
    return {
        'migration_method': 'Supabase Dashboard or CLI',
        'schema_file': '/database/scripts/supabase_schema.sql',
        'documentation': 'https://supabase.com/docs/guides/database/migrations',
        'cli_command': 'supabase db push',
        'dashboard_url': 'https://app.supabase.com/project/_/sql',
        'note': 'Run the schema file in the Supabase SQL editor or use the CLI'
    }


# Utility functions for specific Supabase operations
def format_supabase_error(error: Exception) -> str:
    """Format Supabase errors for better logging"""
    error_msg = str(error)
    
    # Common Supabase error patterns
    if "JWT expired" in error_msg:
        return "Authentication token expired - please refresh"
    elif "Invalid API key" in error_msg:
        return "Invalid Supabase API key"
    elif "relation does not exist" in error_msg:
        return "Database table not found - check if migrations have been run"
    elif "permission denied" in error_msg:
        return "Permission denied - check Row Level Security policies"
    elif "duplicate key value" in error_msg:
        return "Duplicate record - record already exists"
    else:
        return f"Supabase error: {error_msg}"


def check_required_env_vars() -> Dict[str, bool]:
    """Check if required Supabase environment variables are set"""
    required_vars = {
        'SUPABASE_URL': bool(os.getenv('SUPABASE_URL')),
        'SUPABASE_SERVICE_KEY': bool(os.getenv('SUPABASE_SERVICE_KEY'))
    }
    
    optional_vars = {
        'SUPABASE_ANON_KEY': bool(os.getenv('SUPABASE_ANON_KEY')),
        'SUPABASE_JWT_SECRET': bool(os.getenv('SUPABASE_JWT_SECRET'))
    }
    
    return {
        'required': required_vars,
        'optional': optional_vars,
        'all_required_present': all(required_vars.values())
    }