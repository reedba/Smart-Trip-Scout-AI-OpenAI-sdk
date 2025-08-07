import os
import json
import asyncio
from typing import Dict, List, Any, AsyncGenerator
from datetime import datetime, timedelta
from dataclasses import dataclass
import requests
from bs4 import BeautifulSoup
import openai
from openai import OpenAI
from dotenv import load_dotenv
import sendgrid
from sendgrid.helpers.mail import Mail

# Load environment variables
load_dotenv()

@dataclass
class TripPlan:
    destination: str
    start_date: str
    end_date: str
    interests: List[str]
    weather_info: Dict[str, Any]
    restaurants: List[Dict[str, Any]]
    activities: List[Dict[str, Any]]
    festivals_events: List[Dict[str, Any]]
    itinerary: Dict[str, List[Dict[str, Any]]]
    confidence_score: float
    budget_level: str
    num_travelers: int
    include_lodging: bool
    cost_breakdown: Dict[str, float]
    total_estimated_cost: float
    origin_city: str
    travel_comparison: Dict[str, Any]

class TripPlanner:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.sendgrid_client = sendgrid.SendGridAPIClient(api_key=os.getenv("SENDGRID_API_KEY"))
        
    def websearch_tool(self, query: str) -> Dict[str, Any]:
        """
        Simulated web search tool that would normally search the web.
        In a real implementation, this would use actual web search APIs.
        """
        # This is a placeholder - in production you'd use actual search APIs
        # like Google Custom Search, Bing Search API, etc.
        return {
            "query": query,
            "results": f"Search results for: {query}",
            "timestamp": datetime.now().isoformat()
        }
    
    def get_price_estimates(self, destination: str, budget_level: str) -> Dict[str, Dict[str, float]]:
        """
        Get price estimates based on destination and budget level.
        Returns pricing for different categories in different budget tiers.
        """
        # Base prices (per person per day) - these would ideally come from a pricing API
        base_prices = {
            # Meals (per person per day)
            "meals": {
                "low": 25,      # Budget dining, street food, simple restaurants
                "mid": 50,      # Mid-range restaurants, some fine dining
                "luxury": 100   # High-end restaurants, fine dining experiences
            },
            # Activities (per person per day)
            "activities": {
                "low": 15,      # Free/cheap attractions, walking tours
                "mid": 40,      # Museums, paid attractions, some tours
                "luxury": 80    # Premium experiences, private tours, shows
            },
            # Local transport (per person per day)
            "transport": {
                "low": 10,      # Public transport, walking
                "mid": 25,      # Mix of public transport and taxis/rideshare
                "luxury": 60    # Private transport, premium services
            },
            # Lodging (per person per night)
            "lodging": {
                "low": 40,      # Hostels, budget hotels
                "mid": 100,     # Mid-range hotels, nice B&Bs
                "luxury": 250   # Luxury hotels, resorts
            }
        }
        
        # Regional multipliers based on destination cost of living
        regional_multipliers = {
            # High-cost destinations
            "paris": 1.4, "london": 1.3, "new york": 1.3, "tokyo": 1.2, "sydney": 1.2,
            "zurich": 1.5, "oslo": 1.4, "copenhagen": 1.3, "stockholm": 1.2,
            
            # Medium-cost destinations  
            "rome": 1.0, "madrid": 0.9, "berlin": 0.9, "amsterdam": 1.1, "barcelona": 0.9,
            "prague": 0.7, "budapest": 0.6, "lisbon": 0.8, "athens": 0.7,
            
            # Lower-cost destinations
            "bangkok": 0.4, "mexico city": 0.5, "istanbul": 0.5, "cairo": 0.4,
            "delhi": 0.3, "lima": 0.5, "marrakech": 0.5, "prague": 0.6
        }
        
        # Get multiplier for destination (default to 1.0 if not found)
        destination_key = destination.lower().split(',')[0].strip()
        multiplier = regional_multipliers.get(destination_key, 1.0)
        
        # Apply regional multiplier to base prices
        adjusted_prices = {}
        for category, budget_prices in base_prices.items():
            adjusted_prices[category] = {
                budget: price * multiplier 
                for budget, price in budget_prices.items()
            }
        
        return adjusted_prices
    
    def calculate_trip_cost(self, destination: str, start_date: str, end_date: str, 
                          budget_level: str, num_travelers: int, include_lodging: bool) -> Dict[str, float]:
        """
        Calculate total trip cost breakdown.
        """
        # Calculate number of days
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        days = (end - start).days + 1
        nights = days - 1
        
        # Get price estimates for destination
        prices = self.get_price_estimates(destination, budget_level)
        
        # Calculate costs
        cost_breakdown = {
            "meals": prices["meals"][budget_level] * days * num_travelers,
            "activities": prices["activities"][budget_level] * days * num_travelers,
            "transport": prices["transport"][budget_level] * days * num_travelers,
        }
        
        if include_lodging:
            cost_breakdown["lodging"] = prices["lodging"][budget_level] * nights * num_travelers
        
        # Add some miscellaneous costs (10% of total)
        subtotal = sum(cost_breakdown.values())
        cost_breakdown["miscellaneous"] = subtotal * 0.1
        
        return cost_breakdown
    
    def get_driving_distance(self, origin: str, destination: str) -> Dict[str, Any]:
        """
        Use websearch_tool to get driving distance and time from origin to destination.
        In a real implementation, this would use Google Maps API or similar.
        """
        query = f"driving distance from {origin} to {destination}"
        search_result = self.websearch_tool(query)
        
        # Simulate driving distance data based on common city pairs
        # In production, this would parse actual search results or use a maps API
        distance_data = {
            # Common distance estimates (in miles)
            "new york-washington dc": {"miles": 225, "hours": 4.5},
            "los angeles-san francisco": {"miles": 380, "hours": 6.0},
            "chicago-detroit": {"miles": 280, "hours": 4.5},
            "miami-orlando": {"miles": 235, "hours": 3.5},
            "seattle-portland": {"miles": 173, "hours": 3.0},
            "boston-philadelphia": {"miles": 300, "hours": 5.0},
            "dallas-houston": {"miles": 240, "hours": 3.5},
            "atlanta-charlotte": {"miles": 245, "hours": 4.0},
        }
        
        # Create search key
        search_key = f"{origin.lower()}-{destination.lower()}"
        reverse_key = f"{destination.lower()}-{origin.lower()}"
        
        if search_key in distance_data:
            return distance_data[search_key]
        elif reverse_key in distance_data:
            return distance_data[reverse_key]
        else:
            # Default estimate based on rough calculation
            # In production, this would always use actual API data
            estimated_miles = 300  # Default assumption
            estimated_hours = estimated_miles / 65  # Average highway speed
            return {"miles": estimated_miles, "hours": estimated_hours}
    
    def calculate_driving_cost(self, distance_miles: float, num_travelers: int, 
                             mpg: float = 25, gas_price: float = 3.50) -> Dict[str, float]:
        """
        Calculate the cost of driving to the destination.
        """
        # Round trip distance
        total_miles = distance_miles * 2
        
        # Calculate gas cost
        gallons_needed = total_miles / mpg
        total_gas_cost = gallons_needed * gas_price
        
        # Additional driving costs (wear, tolls, parking)
        wear_cost = total_miles * 0.10  # $0.10 per mile for wear and tear
        estimated_tolls = min(50, distance_miles * 0.05)  # Estimated tolls
        parking_cost = 25 * (distance_miles / 200)  # Parking estimate based on distance
        
        return {
            "gas_cost": total_gas_cost,
            "wear_and_tear": wear_cost,
            "tolls": estimated_tolls,
            "parking": parking_cost,
            "total_per_group": total_gas_cost + wear_cost + estimated_tolls + parking_cost,
            "total_per_person": (total_gas_cost + wear_cost + estimated_tolls + parking_cost) / num_travelers
        }
    
    def get_flight_cost(self, origin: str, destination: str, num_travelers: int) -> Dict[str, Any]:
        """
        Use websearch_tool to get average airfare from origin to destination.
        In a real implementation, this would use flight APIs like Skyscanner or Google Flights.
        """
        query = f"average flight cost from {origin} to {destination}"
        search_result = self.websearch_tool(query)
        
        # Simulate flight cost data based on common routes and distance
        # In production, this would use actual flight APIs
        flight_data = {
            # Major routes with typical costs
            "new york-washington dc": {"price": 180, "duration": 1.5},
            "los angeles-san francisco": {"price": 120, "duration": 1.5},
            "chicago-detroit": {"price": 160, "duration": 1.2},
            "miami-orlando": {"price": 90, "duration": 1.0},
            "seattle-portland": {"price": 110, "duration": 1.0},
            "boston-philadelphia": {"price": 150, "duration": 1.5},
            "dallas-houston": {"price": 140, "duration": 1.2},
            "atlanta-charlotte": {"price": 130, "duration": 1.0},
        }
        
        # Create search key
        search_key = f"{origin.lower()}-{destination.lower()}"
        reverse_key = f"{destination.lower()}-{origin.lower()}"
        
        if search_key in flight_data:
            base_price = flight_data[search_key]["price"]
            duration = flight_data[search_key]["duration"]
        elif reverse_key in flight_data:
            base_price = flight_data[reverse_key]["price"]
            duration = flight_data[reverse_key]["duration"]
        else:
            # Default estimate - longer distances generally cost more
            base_price = 200  # Default flight cost
            duration = 2.5    # Default flight duration
        
        # Calculate total costs (round trip)
        round_trip_price = base_price * 2
        total_cost = round_trip_price * num_travelers
        
        return {
            "price_per_person": round_trip_price,
            "total_cost": total_cost,
            "flight_duration": duration,
            "total_travel_time": duration + 2  # Add airport time
        }
    
    def get_festivals_and_events(self, destination: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """
        Search for festivals and special events happening during the trip dates.
        In production, this would use event APIs like Eventbrite, local tourism boards, or news APIs.
        """
        from datetime import datetime, timedelta
        import random
        
        # Parse dates
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        
        # Sample festivals and events database (in production, this would be real data)
        festival_templates = [
            {
                "name": "{destination} Food Festival",
                "type": "Food Festival",
                "description": "Annual celebration of local cuisine",
                "tags": ["food", "outdoor", "culture", "festival"],
                "rating": 4.5,
                "duration_days": 3
            },
            {
                "name": "Summer Music Festival",
                "type": "Music Festival", 
                "description": "Multi-day outdoor music event",
                "tags": ["music", "outdoor", "entertainment", "festival"],
                "rating": 4.6,
                "duration_days": 2
            },
            {
                "name": "Art & Culture Week",
                "type": "Cultural Event",
                "description": "Galleries, museums, and art installations",
                "tags": ["art", "culture", "indoor", "outdoor", "festival"],
                "rating": 4.3,
                "duration_days": 7
            },
            {
                "name": "Historic Heritage Days",
                "type": "Heritage Festival",
                "description": "Celebration of local history and traditions",
                "tags": ["history", "culture", "outdoor", "festival"],
                "rating": 4.2,
                "duration_days": 2
            },
            {
                "name": "Night Market Festival",
                "type": "Night Market",
                "description": "Evening street food and shopping market",
                "tags": ["food", "shopping", "outdoor", "evening", "festival"],
                "rating": 4.4,
                "duration_days": 1
            },
            {
                "name": "Seasonal Flower Festival",
                "type": "Nature Festival",
                "description": "Beautiful seasonal flower displays",
                "tags": ["nature", "outdoor", "photography", "festival"],
                "rating": 4.1,
                "duration_days": 14
            }
        ]
        
        # Randomly determine if festivals are happening (simulate real-world variability)
        festivals_events = []
        
        # 40% chance of having festivals during the trip
        if random.random() < 0.4:
            # Select 1-2 festivals randomly
            num_festivals = random.randint(1, 2)
            selected_templates = random.sample(festival_templates, min(num_festivals, len(festival_templates)))
            
            for template in selected_templates:
                # Generate random dates within the trip period
                trip_days = (end - start).days + 1
                if trip_days >= template["duration_days"]:
                    # Festival can fit within trip
                    max_start_day = trip_days - template["duration_days"]
                    festival_start_offset = random.randint(0, max_start_day)
                    festival_start = start + timedelta(days=festival_start_offset)
                    festival_end = festival_start + timedelta(days=template["duration_days"] - 1)
                    
                    festival = template.copy()
                    festival["name"] = template["name"].replace("{destination}", destination.split(",")[0])
                    festival["start_date"] = festival_start.strftime("%Y-%m-%d")
                    festival["end_date"] = festival_end.strftime("%Y-%m-%d")
                    festival["dates_during_trip"] = True
                    
                    festivals_events.append(festival)
        
        return festivals_events
    
    def compare_travel_options(self, origin: str, destination: str, num_travelers: int) -> Dict[str, Any]:
        """
        Compare driving vs flying options and return comprehensive analysis.
        """
        # Get driving information
        driving_info = self.get_driving_distance(origin, destination)
        driving_costs = self.calculate_driving_cost(driving_info["miles"], num_travelers)
        
        # Get flight information
        flight_info = self.get_flight_cost(origin, destination, num_travelers)
        
        # Create comparison
        comparison = {
            "driving": {
                "distance_miles": driving_info["miles"],
                "drive_time_hours": driving_info["hours"],
                "total_time_hours": driving_info["hours"] * 2,  # Round trip
                "cost_breakdown": driving_costs,
                "total_cost": driving_costs["total_per_group"],
                "cost_per_person": driving_costs["total_per_person"],
                "convenience_score": 7,  # Out of 10
                "pros": ["Door-to-door travel", "Flexible schedule", "Can bring luggage", "Split costs among travelers"],
                "cons": ["Longer travel time", "Driver fatigue", "Wear on vehicle", "Weather dependent"]
            },
            "flying": {
                "flight_duration_hours": flight_info["flight_duration"],
                "total_time_hours": flight_info["total_travel_time"] * 2,  # Round trip with airport time
                "cost_per_person": flight_info["price_per_person"],
                "total_cost": flight_info["total_cost"],
                "convenience_score": 8,  # Out of 10
                "pros": ["Fast travel time", "No driving fatigue", "Weather independent", "Professional service"],
                "cons": ["Airport security", "Baggage restrictions", "Fixed schedule", "Extra transportation to/from airport"]
            }
        }
        
        # Determine recommendation
        cost_difference = abs(comparison["driving"]["total_cost"] - comparison["flying"]["total_cost"])
        time_difference = abs(comparison["driving"]["total_time_hours"] - comparison["flying"]["total_time_hours"])
        
        if comparison["driving"]["total_cost"] < comparison["flying"]["total_cost"] - 100:
            recommendation = "driving"
            reason = "significantly cheaper"
        elif comparison["flying"]["total_cost"] < comparison["driving"]["total_cost"] - 100:
            recommendation = "flying"
            reason = "significantly cheaper"
        elif comparison["flying"]["total_time_hours"] < comparison["driving"]["total_time_hours"] - 4:
            recommendation = "flying"
            reason = "much faster"
        elif num_travelers >= 3:
            recommendation = "driving"
            reason = "better value for larger groups"
        else:
            recommendation = "flying"
            reason = "better convenience and time savings"
        
        comparison["recommendation"] = {
            "preferred": recommendation,
            "reason": reason,
            "cost_difference": cost_difference,
            "time_difference": time_difference
        }
        
        return comparison
    
    def function_tool_evaluator(self, items: List[Dict], interests: List[str], weather: Dict) -> List[Dict]:
        """
        Function tool to evaluate and score activities/restaurants based on interests and weather.
        """
        scored_items = []
        for item in items:
            # Simple scoring algorithm based on interest matching and weather compatibility
            base_score = 0.5
            interest_bonus = 0.0
            weather_bonus = 0.0
            
            # Check interest alignment
            item_tags = item.get('tags', [])
            for interest in interests:
                if any(interest.lower() in tag.lower() for tag in item_tags):
                    interest_bonus += 0.2
            
            # Weather compatibility (simplified)
            if weather.get('condition') == 'sunny' and 'outdoor' in item_tags:
                weather_bonus = 0.1
            elif weather.get('condition') == 'rainy' and 'indoor' in item_tags:
                weather_bonus = 0.1
                
            final_score = min(1.0, base_score + interest_bonus + weather_bonus)
            
            scored_item = item.copy()
            scored_item['score'] = final_score
            scored_items.append(scored_item)
            
        return sorted(scored_items, key=lambda x: x['score'], reverse=True)
    
    def function_tool_optimizer(self, activities: List[Dict], restaurants: List[Dict], 
                              start_date: str, end_date: str) -> Dict[str, List[Dict]]:
        """
        Function tool to optimize and build daily itineraries without repeating activities.
        """
        from datetime import datetime, timedelta
        import random
        
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        days = (end - start).days + 1
        
        itinerary = {}
        
        # Create copies to avoid modifying original lists
        available_activities = activities.copy()
        available_restaurants = restaurants.copy()
        
        # Track used activities and restaurants to avoid repetition
        used_activities = set()
        used_restaurants = set()
        
        for day in range(days):
            current_date = start + timedelta(days=day)
            date_str = current_date.strftime("%Y-%m-%d")
            
            # Get unused activities for morning and afternoon
            unused_activities = [act for act in available_activities if act['name'] not in used_activities]
            unused_restaurants = [rest for rest in available_restaurants if rest['name'] not in used_restaurants]
            
            # If we've used all activities, reset the pool (but shuffle for variety)
            if not unused_activities and available_activities:
                used_activities.clear()
                unused_activities = available_activities.copy()
                random.shuffle(unused_activities)
            
            # If we've used all restaurants, reset the pool
            if not unused_restaurants and available_restaurants:
                used_restaurants.clear()
                unused_restaurants = available_restaurants.copy()
                random.shuffle(unused_restaurants)
            
            # Select activities for the day
            morning_activity = None
            afternoon_activity = None
            evening_restaurant = None
            
            # Check for festivals/events happening on this specific date
            festivals_today = [act for act in unused_activities 
                             if act.get('type') in ['Food Festival', 'Music Festival', 'Cultural Event', 'Heritage Festival', 'Night Market', 'Nature Festival'] 
                             and act.get('start_date') <= date_str <= act.get('end_date', date_str)]
            
            # Morning activity - prioritize festivals if available
            if festivals_today and unused_activities:
                morning_activity = festivals_today[0]
                used_activities.add(morning_activity['name'])
                unused_activities.remove(morning_activity)
            elif unused_activities:
                # Prefer outdoor activities in the morning if weather is good
                outdoor_morning = [act for act in unused_activities if 'outdoor' in act.get('tags', [])]
                if outdoor_morning:
                    morning_activity = outdoor_morning[0]
                else:
                    morning_activity = unused_activities[0]
                used_activities.add(morning_activity['name'])
                unused_activities.remove(morning_activity)
            
            # Afternoon activity (different from morning)
            # Check for remaining festivals first
            remaining_festivals = [act for act in festivals_today if act['name'] not in used_activities]
            if remaining_festivals and unused_activities:
                afternoon_activity = remaining_festivals[0]
                used_activities.add(afternoon_activity['name'])
                if afternoon_activity in unused_activities:
                    unused_activities.remove(afternoon_activity)
            elif unused_activities:
                afternoon_activity = unused_activities[0]
                used_activities.add(afternoon_activity['name'])
                unused_activities.remove(afternoon_activity)
            elif morning_activity:
                # If no more unique activities, find a different type
                different_type = [act for act in available_activities 
                                if act['name'] != morning_activity['name'] and 
                                   act.get('type') != morning_activity.get('type')]
                if different_type:
                    afternoon_activity = different_type[0]
            
            # Evening restaurant
            if unused_restaurants:
                evening_restaurant = unused_restaurants[0]
                used_restaurants.add(evening_restaurant['name'])
                unused_restaurants.remove(evening_restaurant)
            
            day_plan = {
                "morning": morning_activity,
                "afternoon": afternoon_activity,
                "evening": evening_restaurant
            }
            
            itinerary[date_str] = day_plan
            
        return itinerary
    
    async def plan_trip(self, destination: str, start_date: str, end_date: str, 
                       interests: List[str], budget_level: str = "mid", 
                       num_travelers: int = 1, include_lodging: bool = False,
                       origin_city: str = "") -> AsyncGenerator[str, None]:
        """
        Main trip planning function that yields status updates.
        """
        yield f"🚀 Starting trip planning for {destination}..."
        
        # Stage 1: Web search for information
        yield "🔍 Searching for weather information..."
        weather_query = f"weather {destination} {start_date} to {end_date}"
        weather_info = self.websearch_tool(weather_query)
        
        # Simulate weather data
        weather_data = {
            "condition": "sunny",
            "temperature": "22°C",
            "humidity": "65%",
            "forecast": "Partly cloudy with occasional sunshine"
        }
        
        yield "🍽️ Searching for restaurants based on your interests..."
        restaurant_query = f"best restaurants {destination} {' '.join(interests)}"
        restaurant_results = self.websearch_tool(restaurant_query)
        
        # Simulate restaurant data with more variety
        restaurants = [
            {"name": "Local Bistro", "cuisine": "French", "rating": 4.5, "tags": ["food", "fine dining"]},
            {"name": "Street Food Market", "cuisine": "Various", "rating": 4.2, "tags": ["food", "casual", "outdoor"]},
            {"name": "Historic Tavern", "cuisine": "Traditional", "rating": 4.3, "tags": ["history", "food", "indoor"]},
            {"name": "Rooftop Restaurant", "cuisine": "Contemporary", "rating": 4.6, "tags": ["food", "fine dining", "outdoor", "views"]},
            {"name": "Ethnic Fusion Cafe", "cuisine": "Fusion", "rating": 4.1, "tags": ["food", "casual", "culture"]},
            {"name": "Seafood Grill", "cuisine": "Seafood", "rating": 4.4, "tags": ["food", "fine dining", "fresh"]},
            {"name": "Local Pizza Joint", "cuisine": "Italian", "rating": 4.0, "tags": ["food", "casual", "family"]}
        ]
        
        yield "🎯 Searching for activities and events..."
        activity_query = f"activities events {destination} {start_date} {' '.join(interests)}"
        activity_results = self.websearch_tool(activity_query)
        
        # Search for festivals and special events during the trip dates
        yield "🎪 Searching for festivals and special events..."
        festival_query = f"festivals events {destination} {start_date} {end_date}"
        festival_results = self.websearch_tool(festival_query)
        
        # Simulate festival and event data
        festivals_events = self.get_festivals_and_events(destination, start_date, end_date)
        
        # Simulate activity data with more variety
        activities = [
            {"name": "City Museum", "type": "Cultural", "rating": 4.4, "tags": ["history", "indoor", "culture"]},
            {"name": "Food Walking Tour", "type": "Tour", "rating": 4.6, "tags": ["food", "outdoor", "walking"]},
            {"name": "Concert Hall", "type": "Entertainment", "rating": 4.3, "tags": ["music", "indoor", "entertainment"]},
            {"name": "Local Market", "type": "Shopping", "rating": 4.1, "tags": ["food", "outdoor", "culture"]},
            {"name": "Art Gallery", "type": "Cultural", "rating": 4.5, "tags": ["art", "indoor", "culture"]},
            {"name": "Scenic Park", "type": "Nature", "rating": 4.2, "tags": ["nature", "outdoor", "walking"]},
            {"name": "Historic Architecture Tour", "type": "Tour", "rating": 4.3, "tags": ["history", "outdoor", "culture"]},
            {"name": "Cooking Class", "type": "Experience", "rating": 4.7, "tags": ["food", "indoor", "hands-on"]},
            {"name": "Boat Tour", "type": "Tour", "rating": 4.4, "tags": ["water", "outdoor", "scenic"]},
            {"name": "Local Brewery", "type": "Entertainment", "rating": 4.2, "tags": ["drinks", "indoor", "social"]},
            {"name": "Shopping District", "type": "Shopping", "rating": 3.9, "tags": ["shopping", "indoor", "variety"]},
            {"name": "Observatory", "type": "Educational", "rating": 4.3, "tags": ["science", "indoor", "views"]}
        ]
        
        # Stage 2: Evaluate and score items
        yield "📊 Evaluating activities based on your interests and weather..."
        scored_restaurants = self.function_tool_evaluator(restaurants, interests, weather_data)
        
        yield "📊 Evaluating restaurants..."
        scored_activities = self.function_tool_evaluator(activities, interests, weather_data)
        
        # Evaluate festivals and events if any are found
        if festivals_events:
            yield f"🎪 Found {len(festivals_events)} festival(s)/event(s) during your trip!"
            scored_festivals = self.function_tool_evaluator(festivals_events, interests, weather_data)
            # Boost festival scores since they're special time-limited events
            for festival in scored_festivals:
                festival['score'] = min(1.0, festival['score'] + 0.2)  # Boost by 0.2
            # Add festivals to activities for itinerary planning
            scored_activities.extend(scored_festivals)
        else:
            yield "🎪 No special festivals or events found during your trip dates"
        
        # Stage 3: Optimize itinerary
        yield "🗓️ Building your daily itinerary..."
        itinerary = self.function_tool_optimizer(scored_activities, scored_restaurants, start_date, end_date)
        
        yield "🔄 Optimizing schedule for better alternatives..."
        # Simulate optimization process
        await asyncio.sleep(1)  # Simulate processing time
        
        # Calculate confidence score
        avg_activity_score = sum(item['score'] for item in scored_activities) / len(scored_activities) if scored_activities else 0
        avg_restaurant_score = sum(item['score'] for item in scored_restaurants) / len(scored_restaurants) if scored_restaurants else 0
        confidence_score = (avg_activity_score + avg_restaurant_score) / 2
        
        # Stage 4: Calculate budget and cost breakdown
        yield f"💰 Calculating trip costs for {budget_level} budget level..."
        cost_breakdown = self.calculate_trip_cost(
            destination, start_date, end_date, budget_level, num_travelers, include_lodging
        )
        total_cost = sum(cost_breakdown.values())
        
        yield f"💳 Estimated total cost: ${total_cost:.2f} for {num_travelers} traveler(s)"
        
        # Stage 5: Travel comparison (if origin city provided)
        travel_comparison = None
        if origin_city:
            yield "🚗 Comparing driving vs flying options..."
            travel_comparison = self.compare_travel_options(origin_city, destination, num_travelers)
            if travel_comparison:
                recommended = travel_comparison["recommendation"]["preferred"]
                yield f"✈️ Travel analysis complete - {recommended} recommended!"
        
        # Stage 6: Check confidence
        if confidence_score < 0.7:
            yield "⚠️ Low confidence in plan – suggest user review and provide feedback"
        else:
            yield "✅ High confidence in trip plan!"
        
        # Create final trip plan
        trip_plan = TripPlan(
            destination=destination,
            start_date=start_date,
            end_date=end_date,
            interests=interests,
            weather_info=weather_data,
            restaurants=scored_restaurants,
            activities=scored_activities,
            festivals_events=festivals_events,
            itinerary=itinerary,
            confidence_score=confidence_score,
            budget_level=budget_level,
            num_travelers=num_travelers,
            include_lodging=include_lodging,
            cost_breakdown=cost_breakdown,
            total_estimated_cost=total_cost,
            origin_city=origin_city,
            travel_comparison=travel_comparison
        )
        
        yield "🎉 Trip planning complete!"
        yield self.format_trip_plan(trip_plan)
    
    def format_trip_plan(self, plan: TripPlan) -> str:
        """Format the trip plan for display with improved formatting."""
        from datetime import datetime
        
        # Create properly formatted destination
        destination_formatted = plan.destination.title()
        
        # Calculate trip duration
        start = datetime.strptime(plan.start_date, "%Y-%m-%d")
        end = datetime.strptime(plan.end_date, "%Y-%m-%d")
        duration_days = (end - start).days + 1
        
        # Create confidence indicator
        confidence_indicator = "🟢 High" if plan.confidence_score >= 0.7 else "🟡 Medium" if plan.confidence_score >= 0.5 else "🔴 Low"
        
        output = f"""
╔══════════════════════════════════════════════════════════════╗
║                    🌟 SMART TRIP SCOUT PLAN                  ║
║                      {destination_formatted.center(42)}                     ║
╚══════════════════════════════════════════════════════════════╝

📋 TRIP OVERVIEW
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📅 Travel Dates:    {plan.start_date} → {plan.end_date} ({duration_days} days)
👥 Travelers:       {plan.num_travelers} person{'s' if plan.num_travelers != 1 else ''}
💰 Budget Tier:     {plan.budget_level.title()} Level
🎯 Interests:       {', '.join([interest.title() for interest in plan.interests])}
📊 Confidence:      {confidence_indicator} ({plan.confidence_score:.1%})

🌤️  WEATHER FORECAST
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🌡️  Temperature:    {plan.weather_info['temperature']}
☀️  Conditions:     {plan.weather_info['condition'].title()}
🌈  Forecast:       {plan.weather_info['forecast']}

🗓️  DAILY ITINERARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""
        
        for date, day_plan in plan.itinerary.items():
            # Format the date nicely
            date_obj = datetime.strptime(date, "%Y-%m-%d")
            formatted_date = date_obj.strftime("%A, %B %d, %Y")
            
            output += f"\n\n📍 {formatted_date}\n"
            output += "─" * 65 + "\n"
            
            if day_plan.get('morning'):
                morning = day_plan['morning']
                rating_stars = "⭐" * int(morning['rating']) + "☆" * (5 - int(morning['rating']))
                output += f"🌅 MORNING     │ {morning['name']}\n"
                output += f"              │ {morning['type']} • {rating_stars} ({morning['rating']}/5)\n"
            
            if day_plan.get('afternoon'):
                afternoon = day_plan['afternoon']
                rating_stars = "⭐" * int(afternoon['rating']) + "☆" * (5 - int(afternoon['rating']))
                output += f"☀️  AFTERNOON  │ {afternoon['name']}\n"
                output += f"              │ {afternoon['type']} • {rating_stars} ({afternoon['rating']}/5)\n"
            
            if day_plan.get('evening'):
                evening = day_plan['evening']
                rating_stars = "⭐" * int(evening['rating']) + "☆" * (5 - int(evening['rating']))
                cuisine = evening.get('cuisine', evening.get('type', ''))
                output += f"🌙 EVENING     │ {evening['name']}\n"
                output += f"              │ {cuisine} • {rating_stars} ({evening['rating']}/5)\n"
        
        # Add festivals and events section if any are found
        if plan.festivals_events:
            output += f"\n\n� FESTIVALS & SPECIAL EVENTS\n"
            output += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            for event in plan.festivals_events:
                if event['start_date'] == event.get('end_date', event['start_date']):
                    event_dates = datetime.strptime(event['start_date'], "%Y-%m-%d").strftime("%B %d")
                else:
                    start_formatted = datetime.strptime(event['start_date'], "%Y-%m-%d").strftime("%B %d")
                    end_formatted = datetime.strptime(event.get('end_date', event['start_date']), "%Y-%m-%d").strftime("%B %d")
                    event_dates = f"{start_formatted} - {end_formatted}"
                
                rating_stars = "⭐" * int(event['rating']) + "☆" * (5 - int(event['rating']))
                output += f"🎊 {event['name']}\n"
                output += f"   📅 {event_dates} • {event['type']}\n"
                output += f"   📝 {event['description']}\n"
                output += f"   {rating_stars} ({event['rating']}/5)\n\n"
        
        output += f"\n🍽️  RECOMMENDED RESTAURANTS\n"
        output += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        for i, restaurant in enumerate(plan.restaurants[:5], 1):
            score_bar = "█" * int(restaurant['score'] * 10) + "░" * (10 - int(restaurant['score'] * 10))
            output += f"{i}. {restaurant['name']} • {restaurant['cuisine']}\n"
            output += f"   Match Score: {score_bar} {restaurant['score']:.0%}\n\n"
        
        output += f"🎯 RECOMMENDED ACTIVITIES\n"
        output += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        # Filter out festivals from activities for this section
        regular_activities = [act for act in plan.activities if act.get('type') not in ['Food Festival', 'Music Festival', 'Cultural Event', 'Heritage Festival', 'Night Market', 'Nature Festival']]
        for i, activity in enumerate(regular_activities[:5], 1):
            score_bar = "█" * int(activity['score'] * 10) + "░" * (10 - int(activity['score'] * 10))
            output += f"{i}. {activity['name']} • {activity['type']}\n"
            output += f"   Match Score: {score_bar} {activity['score']:.0%}\n\n"
        
        # Add budget breakdown with better formatting
        output += f"💰 COST BREAKDOWN\n"
        output += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        output += f"Budget Level: {plan.budget_level.title()} • Group Size: {plan.num_travelers} traveler{'s' if plan.num_travelers != 1 else ''}\n\n"
        
        category_details = {
            "meals": {"emoji": "🍽️", "name": "Meals & Dining", "desc": "All food costs per day"},
            "activities": {"emoji": "🎯", "name": "Activities & Tours", "desc": "Attractions and experiences"},
            "transport": {"emoji": "🚗", "name": "Local Transport", "desc": "Getting around destination"},
            "lodging": {"emoji": "🏨", "name": "Accommodation", "desc": "Hotels and lodging"},
            "miscellaneous": {"emoji": "💼", "name": "Miscellaneous", "desc": "Tips, souvenirs, extras"}
        }
        
        total_cost = plan.total_estimated_cost
        for category, cost in plan.cost_breakdown.items():
            if category in category_details:
                details = category_details[category]
                percentage = (cost / total_cost) * 100
                cost_bar = "█" * int(percentage / 5) + "░" * (20 - int(percentage / 5))
                output += f"{details['emoji']} {details['name']:<20} │ ${cost:>8,.2f} │ {cost_bar} {percentage:.1f}%\n"
        
        output += f"\n{'─' * 65}\n"
        output += f"💳 TOTAL ESTIMATED COST: ${total_cost:,.2f}\n"
        output += f"💵 Cost per person: ${total_cost / plan.num_travelers:,.2f}\n"
        
        if not plan.include_lodging:
            output += f"\n⚠️  Note: Lodging costs not included in this estimate\n"
        
        # Add travel comparison if available
        if plan.travel_comparison:
            tc = plan.travel_comparison
            output += f"\n\n🚗✈️  TRAVEL OPTIONS: {plan.origin_city.title()} → {destination_formatted}\n"
            output += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            
            # Driving section
            driving = tc["driving"]
            output += f"🚗 DRIVING OPTION\n"
            output += f"   Distance:     {driving['distance_miles']:.0f} miles ({driving['drive_time_hours']:.1f} hours each way)\n"
            output += f"   Total Cost:   ${driving['total_cost']:.2f} (${driving['cost_per_person']:.2f} per person)\n"
            output += f"   Round Trip:   {driving['drive_time_hours'] * 2:.1f} hours total driving time\n"
            output += f"   Pros:         Flexible schedule, door-to-door, split costs\n"
            output += f"   Cons:         Longer travel time, driver fatigue\n\n"
            
            # Flying section
            flying = tc["flying"]
            output += f"✈️  FLYING OPTION\n"
            output += f"   Flight Time:  {flying['flight_duration_hours']:.1f} hours each way\n"
            output += f"   Total Cost:   ${flying['total_cost']:.2f} (${flying['cost_per_person']:.2f} per person)\n"
            output += f"   Travel Time:  {flying['total_time_hours']:.1f} hours (including airport time)\n"
            output += f"   Pros:         Fast travel, no driving fatigue, weather independent\n"
            output += f"   Cons:         Airport procedures, baggage limits, fixed schedule\n\n"
            
            # Recommendation
            rec = tc["recommendation"]
            cost_savings = abs(driving['total_cost'] - flying['total_cost'])
            output += f"🎯 RECOMMENDATION\n"
            output += f"   {rec['preferred'].upper()} RECOMMENDED\n"
            output += f"   Reason: {rec['reason'].title()}\n"
            output += f"   Cost difference: ${cost_savings:.2f}\n"
        
        output += f"\n\n{'═' * 65}\n"
        output += f"🤖 Generated by Smart Trip Scout AI • Have an amazing trip! ✈️🌍\n"
        output += f"{'═' * 65}"
        
        return output
    
    def send_email(self, to_email: str, trip_plan: str) -> bool:
        """Send trip plan via email using SendGrid with improved formatting."""
        try:
            # Parse the trip plan to extract structured data
            lines = trip_plan.split('\n')
            
            # Extract key information
            destination = ""
            dates = ""
            travelers = ""
            budget = ""
            total_cost = ""
            
            for line in lines:
                if "Smart Trip Scout Plan for" in line:
                    destination = line.replace("# 🌟 Smart Trip Scout Plan for ", "").strip()
                elif "**Dates**:" in line:
                    dates = line.replace("- **Dates**: ", "").strip()
                elif "**Travelers**:" in line:
                    travelers = line.replace("- **Travelers**: ", "").strip()
                elif "**Budget Level**:" in line:
                    budget = line.replace("- **Budget Level**: ", "").strip()
                elif "**💳 Total Estimated Cost**:" in line:
                    total_cost = line.replace("**💳 Total Estimated Cost**: ", "").strip()
            
            # Create beautiful HTML email
            html_content = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Your Smart Trip Scout Plan</title>
            </head>
            <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f7f9fc;">
                <div style="max-width: 800px; margin: 0 auto; background-color: #ffffff; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                    
                    <!-- Header -->
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center;">
                        <h1 style="margin: 0; font-size: 28px; font-weight: 600;">🌟 Your Smart Trip Scout Plan</h1>
                        <p style="margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">AI-powered travel planning at your fingertips</p>
                    </div>
                    
                    <!-- Trip Overview Card -->
                    <div style="padding: 30px; background-color: #f8f9fa; border-bottom: 1px solid #e9ecef;">
                        <h2 style="color: #2c3e50; margin: 0 0 20px 0; font-size: 24px;">📍 Trip Overview</h2>
                        <div style="display: flex; flex-wrap: wrap; gap: 20px;">
                            <div style="background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); flex: 1; min-width: 200px;">
                                <h3 style="color: #667eea; margin: 0 0 8px 0; font-size: 14px; text-transform: uppercase; letter-spacing: 1px;">🗺️ Destination</h3>
                                <p style="margin: 0; font-size: 18px; font-weight: 600; color: #2c3e50;">{destination}</p>
                            </div>
                            <div style="background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); flex: 1; min-width: 200px;">
                                <h3 style="color: #667eea; margin: 0 0 8px 0; font-size: 14px; text-transform: uppercase; letter-spacing: 1px;">📅 Dates</h3>
                                <p style="margin: 0; font-size: 18px; font-weight: 600; color: #2c3e50;">{dates}</p>
                            </div>
                        </div>
                        <div style="display: flex; flex-wrap: wrap; gap: 20px; margin-top: 20px;">
                            <div style="background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); flex: 1; min-width: 200px;">
                                <h3 style="color: #667eea; margin: 0 0 8px 0; font-size: 14px; text-transform: uppercase; letter-spacing: 1px;">👥 Travelers</h3>
                                <p style="margin: 0; font-size: 18px; font-weight: 600; color: #2c3e50;">{travelers}</p>
                            </div>
                            <div style="background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); flex: 1; min-width: 200px;">
                                <h3 style="color: #667eea; margin: 0 0 8px 0; font-size: 14px; text-transform: uppercase; letter-spacing: 1px;">💳 Budget</h3>
                                <p style="margin: 0; font-size: 18px; font-weight: 600; color: #2c3e50;">{budget}</p>
                            </div>
                        </div>
                        {f'''<div style="background: linear-gradient(135deg, #28a745, #20c997); color: white; padding: 20px; border-radius: 8px; text-align: center; margin-top: 20px;">
                            <h3 style="margin: 0 0 5px 0; font-size: 16px; opacity: 0.9;">💰 Estimated Total Cost</h3>
                            <p style="margin: 0; font-size: 28px; font-weight: 700;">{total_cost}</p>
                        </div>''' if total_cost else ''}
                    </div>
                    
                    <!-- Detailed Plan -->
                    <div style="padding: 30px;">
                        <h2 style="color: #2c3e50; margin: 0 0 20px 0; font-size: 24px;">📋 Complete Trip Details</h2>
                        <div style="background-color: #f8f9fa; padding: 25px; border-radius: 12px; border-left: 4px solid #667eea;">
                            <pre style="white-space: pre-wrap; font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; margin: 0; color: #2c3e50; font-size: 14px;">{trip_plan}</pre>
                        </div>
                    </div>
                    
                    <!-- Call to Action -->
                    <div style="background-color: #f8f9fa; padding: 30px; text-align: center; border-top: 1px solid #e9ecef;">
                        <h3 style="color: #2c3e50; margin: 0 0 15px 0;">Ready for your adventure? 🎒</h3>
                        <p style="color: #6c757d; margin: 0 0 20px 0; font-size: 16px;">Save this email for easy reference during your trip!</p>
                        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 12px 30px; border-radius: 25px; display: inline-block; font-weight: 600; text-decoration: none;">
                            ✈️ Have an Amazing Trip!
                        </div>
                    </div>
                    
                    <!-- Footer -->
                    <div style="background-color: #2c3e50; color: #ecf0f1; padding: 20px; text-align: center;">
                        <p style="margin: 0 0 10px 0; font-size: 16px; font-weight: 600;">🤖 Generated by Smart Trip Scout AI</p>
                        <p style="margin: 0; font-size: 14px; opacity: 0.8;">Intelligent travel planning powered by artificial intelligence</p>
                        <div style="margin-top: 15px;">
                            <span style="color: #3498db;">🌍</span>
                            <span style="color: #e74c3c;">✈️</span>
                            <span style="color: #f39c12;">🏨</span>
                            <span style="color: #2ecc71;">�️</span>
                            <span style="color: #9b59b6;">🎯</span>
                        </div>
                    </div>
                    
                </div>
            </body>
            </html>
            """
            
            message = Mail(
                from_email='brandon.andrew.reed@gmail.com',
                to_emails=to_email,
                subject='🌟 Your Smart Trip Scout Plan is Ready!',
                html_content=html_content
            )
            
            response = self.sendgrid_client.send(message)
            return response.status_code == 202
        except Exception as e:
            print(f"Email sending failed: {e}")
            return False
    
    def send_push_notification(self, message: str) -> bool:
        """Send push notification via Pushover API using requests."""
        try:
            user_key = os.getenv("PUSHOVER_USER_KEY")
            api_token = os.getenv("PUSHOVER_API_TOKEN")
            
            if not user_key or not api_token:
                return False
            
            url = "https://api.pushover.net/1/messages.json"
            data = {
                "token": api_token,
                "user": user_key,
                "message": message,
                "title": "Smart Trip Scout"
            }
            
            response = requests.post(url, data=data)
            return response.status_code == 200
        except Exception as e:
            print(f"Push notification failed: {e}")
            return False
