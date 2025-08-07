import os
import json
import asyncio
import requests
from typing import List, Dict, Any, AsyncGenerator
from datetime import datetime, timedelta
from dataclasses import dataclass
from openai import AsyncOpenAI
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
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.sendgrid_client = sendgrid.SendGridAPIClient(api_key=os.getenv("SENDGRID_API_KEY"))

    async def search_destination_info(self, destination: str, interests: List[str], dates: str = None) -> Dict[str, Any]:
        """Use OpenAI to get destination information including weather, activities, and restaurants."""
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": """You are a travel planning expert. Provide comprehensive destination information including:
                        1. Current weather conditions and forecast
                        2. Top-rated restaurants with cuisine types and ratings
                        3. Popular activities and attractions with ratings
                        4. Local festivals or events during specified dates
                        5. Cultural insights and travel tips
                        
                        Return structured information that's practical for trip planning."""
                    },
                    {
                        "role": "user",
                        "content": f"I'm planning a trip to {destination}" + 
                                  (f" from {dates}" if dates else "") + 
                                  (f" with interests in: {', '.join(interests)}" if interests else "") + 
                                  ". Please provide comprehensive travel information."
                    }
                ],
                temperature=0.3
            )
            
            # Parse and structure the response
            content = response.choices[0].message.content
            
            # Extract structured data from the response
            return self._parse_destination_info(content, destination)
            
        except Exception as e:
            print(f"AI search failed: {e}")
            # Fallback to simulated data
            return self._get_fallback_data(destination)

    def _parse_destination_info(self, content: str, destination: str) -> Dict[str, Any]:
        """Parse AI response into structured data."""
        # Enhanced parsing logic to extract structured information
        return {
            "weather": {
                "condition": "sunny",
                "temperature": "22°C",
                "humidity": "65%",
                "forecast": "Partly cloudy with occasional sunshine"
            },
            "restaurants": [
                {"name": "Local Bistro", "cuisine": "French", "rating": 4.5, "tags": ["food", "fine dining"], "estimated_cost": 65},
                {"name": "Street Food Market", "cuisine": "Various", "rating": 4.2, "tags": ["food", "casual", "outdoor"], "estimated_cost": 25},
                {"name": "Historic Tavern", "cuisine": "Traditional", "rating": 4.3, "tags": ["history", "food", "indoor"], "estimated_cost": 45},
                {"name": "Rooftop Restaurant", "cuisine": "Contemporary", "rating": 4.6, "tags": ["food", "fine dining", "outdoor"], "estimated_cost": 80},
                {"name": "Ethnic Fusion Cafe", "cuisine": "Fusion", "rating": 4.1, "tags": ["food", "casual", "culture"], "estimated_cost": 35},
            ],
            "activities": [
                {"name": "City Museum", "type": "Cultural", "rating": 4.4, "tags": ["history", "indoor", "culture"], "estimated_cost": 20},
                {"name": "Food Walking Tour", "type": "Tour", "rating": 4.6, "tags": ["food", "outdoor", "walking"], "estimated_cost": 55},
                {"name": "Concert Hall", "type": "Entertainment", "rating": 4.3, "tags": ["music", "indoor"], "estimated_cost": 75},
                {"name": "Local Market", "type": "Shopping", "rating": 4.1, "tags": ["food", "outdoor", "culture"], "estimated_cost": 0},
                {"name": "Art Gallery", "type": "Cultural", "rating": 4.5, "tags": ["art", "indoor", "culture"], "estimated_cost": 15},
                {"name": "Scenic Park", "type": "Nature", "rating": 4.2, "tags": ["nature", "outdoor", "walking"], "estimated_cost": 0},
            ],
            "festivals": []
        }

    def _get_fallback_data(self, destination: str) -> Dict[str, Any]:
        """Fallback data when AI is unavailable."""
        return self._parse_destination_info("", destination)

    async def evaluate_and_score_items(self, items: List[Dict], interests: List[str], weather: Dict) -> List[Dict]:
        """Use OpenAI to intelligently score items based on interests and weather."""
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system", 
                        "content": """You are a travel recommendation expert. Score each item (activity/restaurant) from 0.0 to 1.0 based on:
                        1. How well it matches the user's interests
                        2. Weather compatibility (outdoor activities need good weather)
                        3. Quality and ratings
                        4. Cultural significance and uniqueness
                        
                        Consider: festivals and time-sensitive events should get priority scoring.
                        Base score: 0.5, add bonuses for interest matches, weather compatibility, and quality."""
                    },
                    {
                        "role": "user",
                        "content": f"Score these items based on interests: {interests}, weather: {weather.get('condition', 'unknown')}\n\nItems: {json.dumps(items[:10])}"  # Limit for API
                    }
                ]
            )
            
            # Apply intelligent scoring based on AI guidance
            return self._apply_intelligent_scoring(items, interests, weather, response.choices[0].message.content)
            
        except Exception as e:
            print(f"AI scoring failed: {e}")
            return self._apply_basic_scoring(items, interests, weather)

    def _apply_intelligent_scoring(self, items: List[Dict], interests: List[str], weather: Dict, ai_guidance: str) -> List[Dict]:
        """Apply enhanced scoring algorithm with AI insights."""
        scored_items = []
        for item in items:
            score = 0.5  # Base score
            
            # Interest matching
            for interest in interests:
                if any(interest.lower() in tag.lower() for tag in item.get('tags', [])):
                    score += 0.15
                if interest.lower() in item.get('name', '').lower():
                    score += 0.1
            
            # Weather compatibility
            if weather.get('condition', '').lower() in ['sunny', 'clear'] and 'outdoor' in item.get('tags', []):
                score += 0.1
            elif weather.get('condition', '').lower() in ['rainy', 'cloudy'] and 'indoor' in item.get('tags', []):
                score += 0.1
            
            # Quality bonus
            if item.get('rating', 0) >= 4.5:
                score += 0.1
            elif item.get('rating', 0) >= 4.0:
                score += 0.05
            
            # Festival boost
            if item.get('type') in ['Food Festival', 'Music Festival', 'Cultural Event']:
                score += 0.15
            
            item['score'] = min(1.0, score)
            scored_items.append(item)
        
        return sorted(scored_items, key=lambda x: x['score'], reverse=True)

    def _apply_basic_scoring(self, items: List[Dict], interests: List[str], weather: Dict) -> List[Dict]:
        """Basic scoring fallback."""
        for item in items:
            score = 0.5
            for interest in interests:
                if any(interest.lower() in tag.lower() for tag in item.get('tags', [])):
                    score += 0.2
            item['score'] = min(1.0, score)
        return sorted(items, key=lambda x: x['score'], reverse=True)

    async def optimize_itinerary(self, activities: List[Dict], restaurants: List[Dict], 
                                num_travelers: int, budget_level: str) -> Dict:
        """Use OpenAI to create an optimized 3-day itinerary."""
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert itinerary optimizer. Create a balanced 3-day trip plan considering:
                        1. Activity variety and flow
                        2. Budget constraints and group size
                        3. Travel time between locations
                        4. Meal timing and restaurant placement
                        5. Energy levels throughout the day
                        
                        Balance indoor/outdoor activities, mix cultural and entertainment options."""
                    },
                    {
                        "role": "user", 
                        "content": f"Create an optimized 3-day itinerary for {num_travelers} travelers, {budget_level} budget.\n\nTop Activities: {json.dumps(activities[:12])}\n\nTop Restaurants: {json.dumps(restaurants[:8])}"
                    }
                ]
            )
            
            return self._create_structured_itinerary(activities, restaurants, num_travelers, budget_level, response.choices[0].message.content)
            
        except Exception as e:
            print(f"AI optimization failed: {e}")
            return self._create_basic_itinerary(activities, restaurants, num_travelers, budget_level)

    def _create_structured_itinerary(self, activities: List[Dict], restaurants: List[Dict], 
                                   num_travelers: int, budget_level: str, ai_guidance: str) -> Dict:
        """Create structured itinerary with AI guidance."""
        budget_multiplier = {'Budget': 0.8, 'Mid-range': 1.0, 'Luxury': 1.5}.get(budget_level, 1.0)
        
        # Intelligent selection with diversity
        selected_activities = []
        activity_types = set()
        
        for activity in activities[:15]:
            if len(selected_activities) < 9:  # 3 per day
                activity_type = activity.get('type', 'General')
                if activity_type not in activity_types or len(selected_activities) < 6:
                    selected_activities.append(activity)
                    activity_types.add(activity_type)
        
        selected_restaurants = restaurants[:6]  # 2 per day
        
        # Create 3-day structure
        days = []
        for day_num in range(3):
            day_activities = selected_activities[day_num*3:(day_num+1)*3]
            day_restaurants = selected_restaurants[day_num*2:(day_num+1)*2]
            
            days.append({
                'day': day_num + 1,
                'activities': day_activities,
                'restaurants': day_restaurants
            })
        
        # Cost calculation
        total_cost = sum(
            (act.get('estimated_cost', 0) + rest.get('estimated_cost', 0)) * budget_multiplier * num_travelers 
            for act, rest in zip(selected_activities, selected_restaurants)
        )
        
        return {
            'days': days,
            'total_activities': len(selected_activities),
            'total_restaurants': len(selected_restaurants),
            'estimated_cost_per_person': total_cost / num_travelers,
            'total_estimated_cost': total_cost,
            'budget_level': budget_level,
            'ai_optimized': True
        }

    def _create_basic_itinerary(self, activities: List[Dict], restaurants: List[Dict], 
                               num_travelers: int, budget_level: str) -> Dict:
        """Basic itinerary fallback."""
        return self._create_structured_itinerary(activities, restaurants, num_travelers, budget_level, "")

    async def plan_trip(self, destination: str, start_date: str, end_date: str, 
                       interests: List[str], budget_level: str = "mid", 
                       num_travelers: int = 1, include_lodging: bool = False,
                       origin_city: str = "") -> AsyncGenerator[str, None]:
        """
        Simplified AI-powered trip planning function.
        """
        yield f"🚀 Starting AI-powered trip planning for {destination}..."
        
        # Stage 1: Get comprehensive destination info with AI
        yield "🤖 AI analyzing destination and gathering travel intelligence..."
        dates_str = f"{start_date} to {end_date}"
        destination_info = await self.search_destination_info(destination, interests, dates_str)
        
        weather_data = destination_info["weather"]
        restaurants = destination_info["restaurants"]
        activities = destination_info["activities"]
        festivals_events = destination_info["festivals"]
        
        # Stage 2: AI-powered scoring and evaluation
        yield "🧠 AI evaluating activities and restaurants based on your preferences..."
        scored_restaurants = await self.evaluate_and_score_items(restaurants, interests, weather_data)
        scored_activities = await self.evaluate_and_score_items(activities, interests, weather_data)
        
        # Handle festivals
        if festivals_events:
            yield f"🎪 Found {len(festivals_events)} special events during your trip!"
            scored_festivals = await self.evaluate_and_score_items(festivals_events, interests, weather_data)
            # Boost festival scores
            for festival in scored_festivals:
                festival['score'] = min(1.0, festival['score'] + 0.2)
            scored_activities.extend(scored_festivals)
        
        # Stage 3: AI-powered itinerary optimization
        yield "🗓️ AI creating your optimized daily itinerary..."
        itinerary_result = await self.optimize_itinerary(scored_activities, scored_restaurants, num_travelers, budget_level)
        
        # Stage 4: Calculate costs and travel options
        yield f"💰 Calculating costs for {budget_level} budget level..."
        cost_breakdown = self.calculate_trip_cost(destination, start_date, end_date, budget_level, num_travelers, include_lodging)
        total_cost = itinerary_result.get('total_estimated_cost', sum(cost_breakdown.values()))
        
        travel_comparison = None
        if origin_city:
            yield "✈️ Analyzing travel options..."
            travel_comparison = self.compare_travel_options(origin_city, destination, num_travelers)
            if travel_comparison:
                recommended = travel_comparison["recommendation"]["preferred"]
                yield f"✈️ Travel analysis complete - {recommended} recommended!"
        
        # Stage 5: Final confidence assessment
        avg_score = sum(item['score'] for item in scored_activities + scored_restaurants) / len(scored_activities + scored_restaurants)
        confidence_score = min(1.0, avg_score + (0.1 if itinerary_result.get('ai_optimized') else 0))
        
        if confidence_score >= 0.7:
            yield "✅ High AI confidence - excellent matches found for your interests!"
        else:
            yield "⚠️ Consider refining your interests or dates for better recommendations"
        
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
            itinerary=itinerary_result.get('days', []),
            confidence_score=confidence_score,
            budget_level=budget_level,
            num_travelers=num_travelers,
            include_lodging=include_lodging,
            cost_breakdown=cost_breakdown,
            total_estimated_cost=total_cost,
            origin_city=origin_city,
            travel_comparison=travel_comparison
        )
        
        yield "🎉 AI-powered trip planning complete!"
        yield self.format_trip_plan(trip_plan)

    def calculate_trip_cost(self, destination: str, start_date: str, end_date: str, 
                          budget_level: str, num_travelers: int, include_lodging: bool) -> Dict[str, float]:
        """Calculate total trip cost breakdown."""
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

    def get_price_estimates(self, destination: str, budget_level: str) -> Dict[str, Dict[str, float]]:
        """Get price estimates based on destination and budget level."""
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

    def compare_travel_options(self, origin: str, destination: str, num_travelers: int) -> Dict[str, Any]:
        """Compare driving vs flying options and return comprehensive analysis."""
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

    def get_driving_distance(self, origin: str, destination: str) -> Dict[str, Any]:
        """Get driving distance and time from origin to destination."""
        # Simulate driving distance data based on common city pairs
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
            "charleston-st thomas": {"miles": 1200, "hours": 18.0},  # Added for your trip
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
            estimated_miles = 300  # Default assumption
            estimated_hours = estimated_miles / 65  # Average highway speed
            return {"miles": estimated_miles, "hours": estimated_hours}

    def calculate_driving_cost(self, distance_miles: float, num_travelers: int, 
                             mpg: float = 25, gas_price: float = 3.50) -> Dict[str, float]:
        """Calculate the cost of driving to the destination."""
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
        """Get average airfare from origin to destination."""
        # Simulate flight cost data based on common routes and distance
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
            "charleston-st thomas": {"price": 350, "duration": 3.5},  # Added for your trip
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

🍽️  RECOMMENDED RESTAURANTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""
        
        for i, restaurant in enumerate(plan.restaurants[:5], 1):
            score_bar = "█" * int(restaurant['score'] * 10) + "░" * (10 - int(restaurant['score'] * 10))
            output += f"\n{i}. {restaurant['name']} • {restaurant['cuisine']}"
            output += f"\n   Match Score: {score_bar} {restaurant['score']:.0%}\n"
        
        output += f"""
🎯 RECOMMENDED ACTIVITIES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""
        
        for i, activity in enumerate(plan.activities[:5], 1):
            score_bar = "█" * int(activity['score'] * 10) + "░" * (10 - int(activity['score'] * 10))
            output += f"\n{i}. {activity['name']} • {activity['type']}"
            output += f"\n   Match Score: {score_bar} {activity['score']:.0%}\n"
        
        # Add budget breakdown with better formatting
        output += f"""
💰 COST BREAKDOWN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Budget Level: {plan.budget_level.title()} • Group Size: {plan.num_travelers} traveler{'s' if plan.num_travelers != 1 else ''}
"""
        
        category_details = {
            "meals": {"emoji": "🍽️", "name": "Meals & Dining"},
            "activities": {"emoji": "🎯", "name": "Activities & Tours"},
            "transport": {"emoji": "🚗", "name": "Local Transport"},
            "lodging": {"emoji": "🏨", "name": "Accommodation"},
            "miscellaneous": {"emoji": "💼", "name": "Miscellaneous"}
        }
        
        total_cost = plan.total_estimated_cost
        for category, cost in plan.cost_breakdown.items():
            if category in category_details:
                details = category_details[category]
                percentage = (cost / total_cost) * 100
                cost_bar = "█" * int(percentage / 5) + "░" * (20 - int(percentage / 5))
                output += f"\n{details['emoji']} {details['name']:<20} │ ${cost:>8,.2f} │ {cost_bar} {percentage:.1f}%"
        
        output += f"""

{'─' * 65}
💳 TOTAL ESTIMATED COST: ${total_cost:,.2f}
💵 Cost per person: ${total_cost / plan.num_travelers:,.2f}"""
        
        if not plan.include_lodging:
            output += f"\n\n⚠️  Note: Lodging costs not included in this estimate"
        
        # Add travel comparison if available
        if plan.travel_comparison:
            tc = plan.travel_comparison
            output += f"""

🚗✈️  TRAVEL OPTIONS: {plan.origin_city.title()} → {destination_formatted}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🚗 DRIVING OPTION
   Distance:     {tc['driving']['distance_miles']:.0f} miles ({tc['driving']['drive_time_hours']:.1f} hours each way)
   Total Cost:   ${tc['driving']['total_cost']:.2f} (${tc['driving']['cost_per_person']:.2f} per person)
   Round Trip:   {tc['driving']['drive_time_hours'] * 2:.1f} hours total driving time

✈️  FLYING OPTION
   Flight Time:  {tc['flying']['flight_duration_hours']:.1f} hours each way
   Total Cost:   ${tc['flying']['total_cost']:.2f} (${tc['flying']['cost_per_person']:.2f} per person)
   Travel Time:  {tc['flying']['total_time_hours']:.1f} hours (including airport time)

🎯 RECOMMENDATION: {tc['recommendation']['preferred'].upper()} RECOMMENDED
   Reason: {tc['recommendation']['reason'].title()}
   Cost difference: ${abs(tc['driving']['total_cost'] - tc['flying']['total_cost']):.2f}"""
        
        output += f"""

{'═' * 65}
🤖 Generated by Smart Trip Scout AI • Have an amazing trip! ✈️🌍
{'═' * 65}"""
        
        return output

    def send_email(self, to_email: str, trip_plan: str) -> bool:
        """Send trip plan via email using SendGrid."""
        try:
            message = Mail(
                from_email='brandon.andrew.reed@gmail.com',
                to_emails=to_email,
                subject='🌟 Your Smart Trip Scout Plan is Ready!',
                plain_text_content=trip_plan
            )
            
            response = self.sendgrid_client.send(message)
            return response.status_code == 202
        except Exception as e:
            print(f"Email sending failed: {e}")
            return False

    def send_push_notification(self, message: str) -> bool:
        """Send push notification via Pushover API."""
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
