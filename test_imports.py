#!/usr/bin/env python3
"""
Simple test script to verify browser-use imports work correctly
"""

import sys
import os

# Add browser-use directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'browser-use'))

try:
    print("Testing browser-use imports...")
    
    # Test basic imports
    from browser_use import Agent, Browser, BrowserConfig, BrowserProfile
    print("✓ Core browser-use imports successful")
    
    # Test viewport size import
    from playwright._impl._api_structures import ViewportSize
    print("✓ ViewportSize import successful")
    
    # Test creating a browser profile
    browser_profile = BrowserProfile(
        headless=True,
        window_size=ViewportSize(width=1920, height=1080)
    )
    print("✓ BrowserProfile creation successful")
    
    print("\n🎉 All imports and basic functionality working correctly!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    sys.exit(1)