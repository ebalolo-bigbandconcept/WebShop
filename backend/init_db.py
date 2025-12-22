#!/usr/bin/env python
"""
Database initialization script.
Run this after migrations to populate default data.
"""
from app import app, init_default_data

if __name__ == "__main__":
    print("Initializing default data...")
    init_default_data()
    print("Default data initialized successfully!")
