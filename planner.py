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
            
            # Morning activity
            if unused_activities:
                # Prefer outdoor activities in the morning if weather is good
                outdoor_morning = [act for act in unused_activities if 'outdoor' in act.get('tags', [])]
                if outdoor_morning:
                    morning_activity = outdoor_morning[0]
                else:
                    morning_activity = unused_activities[0]
                used_activities.add(morning_activity['name'])
                unused_activities.remove(morning_activity)
            
            # Afternoon activity (different from morning)
            if unused_activities:
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
        """Format the trip plan for display."""
        output = f"""
# 🌟 Smart Trip Scout Plan for {plan.destination}

## 📅 Trip Details
- **Dates**: {plan.start_date} to {plan.end_date}
- **Travelers**: {plan.num_travelers} person(s)
- **Budget Level**: {plan.budget_level.title()}
- **Interests**: {', '.join(plan.interests)}
- **Confidence Score**: {plan.confidence_score:.2f}/1.00

## 🌤️ Weather Information
- **Condition**: {plan.weather_info['condition']}
- **Temperature**: {plan.weather_info['temperature']}
- **Forecast**: {plan.weather_info['forecast']}

## 🗓️ Daily Itinerary
"""
        
        for date, day_plan in plan.itinerary.items():
            output += f"\n### {date}\n"
            
            if day_plan.get('morning'):
                morning = day_plan['morning']
                output += f"**🌅 Morning**: {morning['name']} ({morning['type']}) - Rating: {morning['rating']}/5\n"
            
            if day_plan.get('afternoon'):
                afternoon = day_plan['afternoon']
                output += f"**☀️ Afternoon**: {afternoon['name']} ({afternoon['type']}) - Rating: {afternoon['rating']}/5\n"
            
            if day_plan.get('evening'):
                evening = day_plan['evening']
                output += f"**🌙 Evening**: {evening['name']} ({evening.get('cuisine', evening.get('type', ''))}') - Rating: {evening['rating']}/5\n"
        
        output += f"\n## 🍽️ Top Restaurants\n"
        for restaurant in plan.restaurants[:3]:
            output += f"- **{restaurant['name']}** ({restaurant['cuisine']}) - Score: {restaurant['score']:.2f}\n"
        
        output += f"\n## 🎯 Top Activities\n"
        for activity in plan.activities[:3]:
            output += f"- **{activity['name']}** ({activity['type']}) - Score: {activity['score']:.2f}\n"
        
        # Add budget breakdown
        output += f"\n## 💰 Cost Breakdown ({plan.budget_level.title()} Budget for {plan.num_travelers} traveler(s))\n"
        
        for category, cost in plan.cost_breakdown.items():
            category_emoji = {
                "meals": "🍽️",
                "activities": "🎯", 
                "transport": "🚗",
                "lodging": "🏨",
                "miscellaneous": "💼"
            }
            emoji = category_emoji.get(category, "💵")
            output += f"- **{emoji} {category.title()}**: ${cost:.2f}\n"
        
        output += f"\n**💳 Total Estimated Cost**: ${plan.total_estimated_cost:.2f}\n"
        
        if not plan.include_lodging:
            output += f"\n*Note: Lodging costs not included. Add lodging to get complete budget estimate.*\n"
        
        # Add travel comparison if available
        if plan.travel_comparison:
            tc = plan.travel_comparison
            output += f"\n## 🚗✈️ Travel Comparison: {plan.origin_city} → {plan.destination}\n"
            
            # Driving section
            driving = tc["driving"]
            output += f"\n### 🚗 Driving Option\n"
            output += f"- **Distance**: {driving['distance_miles']:.0f} miles\n"
            output += f"- **Duration**: {driving['drive_time_hours']:.1f} hours (one way)\n"
            output += f"- **Total Cost**: ${driving['total_cost']:.2f}\n"
            output += f"  - Cost breakdown: ${driving['cost_breakdown']['total_per_group']:.2f}\n"
            output += f"- **Cost per person**: ${driving['cost_per_person']:.2f}\n"
            output += f"- **Convenience**: Flexible schedule, door-to-door\n"
            
            # Flying section
            flying = tc["flying"]
            output += f"\n### ✈️ Flying Option\n"
            output += f"- **Flight Cost per person**: ${flying['cost_per_person']:.2f}\n"
            output += f"- **Total Cost**: ${flying['total_cost']:.2f}\n"
            output += f"- **Flight Duration**: ~{flying['flight_duration_hours']:.1f} hours (one way)\n"
            output += f"- **Total Travel Time**: ~{flying['total_time_hours']:.1f} hours (incl. airport time)\n"
            output += f"- **Convenience**: Faster, requires airport procedures\n"
            
            # Recommendation
            rec = tc["recommendation"]
            output += f"\n### 🎯 Recommendation\n"
            output += f"**{rec['preferred'].title()} recommended** - {rec['reason']}\n"
        
        return output
    
    def send_email(self, to_email: str, trip_plan: str) -> bool:
        """Send trip plan via email using SendGrid."""
        try:
            # Create HTML version of the trip plan
            html_content = f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 800px; margin: 0 auto; padding: 20px;">
                        <h1 style="color: #2c3e50; text-align: center;">🌟 Your Smart Trip Scout Plan</h1>
                        <hr style="border: 1px solid #eee; margin: 20px 0;">
                        <pre style="white-space: pre-wrap; background-color: #f8f9fa; padding: 20px; border-radius: 8px; font-family: 'Courier New', monospace;">{trip_plan}</pre>
                        <hr style="border: 1px solid #eee; margin: 20px 0;">
                        <p style="text-align: center; color: #7f8c8d; font-size: 14px;">
                            Generated by Smart Trip Scout AI<br>
                            Have an amazing trip! ✈️🌍
                        </p>
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
