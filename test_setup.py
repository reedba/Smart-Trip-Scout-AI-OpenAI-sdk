#!/usr/bin/env python3
"""
Test script for Smart Trip Scout AI

This script tests the basic functionality of the application
without requiring API keys.
"""

import sys
import os

def test_imports():
    """Test if all required modules can be imported."""
    print("🧪 Testing imports...")
    
    try:
        import gradio as gr
        print("✅ Gradio imported successfully")
    except ImportError as e:
        print(f"❌ Gradio import failed: {e}")
        return False
    
    try:
        import openai
        print("✅ OpenAI imported successfully")
    except ImportError as e:
        print(f"❌ OpenAI import failed: {e}")
        return False
    
    try:
        from dotenv import load_dotenv
        print("✅ python-dotenv imported successfully")
    except ImportError as e:
        print(f"❌ python-dotenv import failed: {e}")
        return False
    
    try:
        import sendgrid
        print("✅ SendGrid imported successfully")
    except ImportError as e:
        print(f"❌ SendGrid import failed: {e}")
        return False
    
    try:
        import requests
        print("✅ Requests imported successfully")
    except ImportError as e:
        print(f"❌ Requests import failed: {e}")
        return False
    
    try:
        from bs4 import BeautifulSoup
        print("✅ BeautifulSoup imported successfully")
    except ImportError as e:
        print(f"❌ BeautifulSoup import failed: {e}")
        return False
    
    return True

def test_modules():
    """Test if our custom modules can be imported."""
    print("\n🔧 Testing custom modules...")
    
    try:
        from planner import TripPlanner
        print("✅ TripPlanner imported successfully")
        
        # Test initialization without API keys
        planner = TripPlanner()
        print("✅ TripPlanner initialized successfully")
        return True
    except Exception as e:
        print(f"❌ TripPlanner test failed: {e}")
        return False

def test_env_file():
    """Test if .env file exists."""
    print("\n📁 Testing environment setup...")
    
    if os.path.exists('.env'):
        print("✅ .env file found")
        return True
    elif os.path.exists('.env.example'):
        print("⚠️  .env.example found but .env is missing")
        print("   Please copy .env.example to .env and add your API keys")
        return False
    else:
        print("❌ No environment files found")
        return False

def main():
    """Run all tests."""
    print("🌟 Smart Trip Scout AI - Test Suite")
    print("=" * 50)
    
    tests_passed = 0
    total_tests = 3
    
    if test_imports():
        tests_passed += 1
    
    if test_modules():
        tests_passed += 1
    
    if test_env_file():
        tests_passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! You're ready to run the application.")
        print("   Run: python trip_scout.py")
    else:
        print("⚠️  Some tests failed. Please check the output above and:")
        print("   1. Install missing dependencies: pip install -r requirements.txt")
        print("   2. Set up your .env file with API keys")
    
    return tests_passed == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
