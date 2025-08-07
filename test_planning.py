#!/usr/bin/env python3
"""
Test the Smart Trip Scout planning functionality without the UI
"""

import asyncio
from planner import TripPlanner

async def test_trip_planning():
    """Test the trip planning functionality"""
    planner = TripPlanner()
    
    print("🧪 Testing Smart Trip Scout Planning Engine")
    print("=" * 50)
    
    # Test parameters
    destination = "Charleston, SC"
    start_date = "2025-08-15"
    end_date = "2025-08-17"
    interests = ["food", "history", "culture"]
    budget_level = "mid"
    num_travelers = 2
    include_lodging = True
    
    print(f"📍 Destination: {destination}")
    print(f"📅 Dates: {start_date} to {end_date}")
    print(f"🎯 Interests: {', '.join(interests)}")
    print(f"💳 Budget Level: {budget_level}")
    print(f"👥 Travelers: {num_travelers}")
    print(f"🏨 Include Lodging: {include_lodging}")
    print("\n" + "=" * 50)
    
    # Run the planning
    all_updates = []
    async for update in planner.plan_trip(destination, start_date, end_date, interests, budget_level, num_travelers, include_lodging):
        print(update)
        all_updates.append(update)
        
        # Add a small delay to simulate real-time updates
        if not update.startswith("#"):  # Don't delay for the formatted plan
            await asyncio.sleep(0.5)
    
    print("\n" + "=" * 50)
    print("🎉 Planning complete! Check the detailed plan above.")
    
    return all_updates

if __name__ == "__main__":
    asyncio.run(test_trip_planning())
