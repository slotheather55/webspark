"""
SQLAlchemy import utilities
"""
# Re-export common imports to avoid import errors
try:
    from sqlalchemy import (
        Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey, JSON, Table,
        create_engine, MetaData, select, insert, update, delete
    )
    from sqlalchemy.orm import (
        relationship, Session, sessionmaker, declarative_base, mapped_column, Mapped
    )
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.sql import func
    from sqlalchemy.dialects.postgresql import UUID, JSONB

    # Make these imports available through this module
    __all__ = [
        'Column', 'Integer', 'String', 'Text', 'DateTime', 'Boolean', 'Float', 'ForeignKey', 
        'JSON', 'Table', 'create_engine', 'MetaData', 'select', 'insert', 'update', 'delete',
        'relationship', 'Session', 'sessionmaker', 'declarative_base', 'mapped_column', 'Mapped',
        'func', 'UUID', 'JSONB'
    ]
except ImportError:
    print("SQLAlchemy not installed. Please run 'webspark activate' and then 'pip install sqlalchemy'") 