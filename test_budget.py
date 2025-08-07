#!/usr/bin/env python3
"""
Test budget comparison for different budget levels
"""

import asyncio
from planner import TripPlanner

async def test_budget_comparison():
    """Test different budget levels"""
    planner = TripPlanner()
    
    print("💰 Smart Trip Scout - Budget Comparison Test")
    print("=" * 60)
    
    # Test parameters
    destination = "Paris, France"
    start_date = "2025-09-01"
    end_date = "2025-09-05"
    interests = ["food", "art", "culture"]
    num_travelers = 2
    include_lodging = True
    
    budget_levels = ["low", "mid", "luxury"]
    
    print(f"📍 Destination: {destination}")
    print(f"📅 Dates: {start_date} to {end_date}")
    print(f"👥 Travelers: {num_travelers}")
    print(f"🏨 Include Lodging: {include_lodging}")
    print("\n" + "=" * 60)
    
    for budget_level in budget_levels:
        print(f"\n💳 {budget_level.upper()} BUDGET BREAKDOWN:")
        print("-" * 40)
        
        cost_breakdown = planner.calculate_trip_cost(
            destination, start_date, end_date, budget_level, num_travelers, include_lodging
        )
        
        total_cost = sum(cost_breakdown.values())
        
        for category, cost in cost_breakdown.items():
            category_emoji = {
                "meals": "🍽️",
                "activities": "🎯", 
                "transport": "🚗",
                "lodging": "🏨",
                "miscellaneous": "💼"
            }
            emoji = category_emoji.get(category, "💵")
            print(f"{emoji} {category.title()}: ${cost:.2f}")
        
        print(f"\n💳 Total: ${total_cost:.2f}")
        print(f"💸 Per person: ${total_cost/num_travelers:.2f}")
    
    print("\n" + "=" * 60)
    print("📊 Budget comparison complete!")

if __name__ == "__main__":
    asyncio.run(test_budget_comparison())
