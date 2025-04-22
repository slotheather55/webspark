"""
Test SQLAlchemy imports
"""
try:
    from sqlalchemy import Column, Integer, String
    print("SQLAlchemy import successful!")
except ImportError as e:
    print(f"SQLAlchemy import failed: {e}") 