#!/usr/bin/env python3
"""
Smart Trip Scout AI - OpenAI SDK Implementation

A smart travel planning application that uses AI to create personalized itineraries
based on user preferences, weather conditions, and real-time information.

Usage:
    python trip_scout.py

Features:
- AI-powered trip planning with OpenAI
- Weather-based activity recommendations
- Interest-based restaurant and activity suggestions
- Email and push notification support
- Confidence scoring for recommendations
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import main

if __name__ == "__main__":
    print("🌟 Welcome to Smart Trip Scout AI!")
    print("Starting the Gradio web interface...")
    main()
