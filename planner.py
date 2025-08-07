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
        Function tool to optimize and build daily itineraries.
        """
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        days = (end - start).days + 1
        
        itinerary = {}
        
        for day in range(days):
            current_date = start + timedelta(days=day)
            date_str = current_date.strftime("%Y-%m-%d")
            
            # Simple optimization: distribute top-rated items across days
            day_plan = {
                "morning": activities[day % len(activities)] if activities else None,
                "afternoon": activities[(day + 1) % len(activities)] if len(activities) > 1 else activities[0] if activities else None,
                "evening": restaurants[day % len(restaurants)] if restaurants else None
            }
            
            itinerary[date_str] = day_plan
            
        return itinerary
    
    async def plan_trip(self, destination: str, start_date: str, end_date: str, 
                       interests: List[str]) -> AsyncGenerator[str, None]:
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
        
        # Simulate restaurant data
        restaurants = [
            {"name": "Local Bistro", "cuisine": "French", "rating": 4.5, "tags": ["food", "fine dining"]},
            {"name": "Street Food Market", "cuisine": "Various", "rating": 4.2, "tags": ["food", "casual", "outdoor"]},
            {"name": "Historic Tavern", "cuisine": "Traditional", "rating": 4.3, "tags": ["history", "food", "indoor"]}
        ]
        
        yield "🎯 Searching for activities and events..."
        activity_query = f"activities events {destination} {start_date} {' '.join(interests)}"
        activity_results = self.websearch_tool(activity_query)
        
        # Simulate activity data
        activities = [
            {"name": "City Museum", "type": "Cultural", "rating": 4.4, "tags": ["history", "indoor", "culture"]},
            {"name": "Food Walking Tour", "type": "Tour", "rating": 4.6, "tags": ["food", "outdoor", "walking"]},
            {"name": "Concert Hall", "type": "Entertainment", "rating": 4.3, "tags": ["music", "indoor", "entertainment"]},
            {"name": "Local Market", "type": "Shopping", "rating": 4.1, "tags": ["food", "outdoor", "culture"]}
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
        
        # Stage 4: Check confidence
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
            confidence_score=confidence_score
        )
        
        yield "🎉 Trip planning complete!"
        yield self.format_trip_plan(trip_plan)
    
    def format_trip_plan(self, plan: TripPlan) -> str:
        """Format the trip plan for display."""
        output = f"""
# 🌟 Smart Trip Scout Plan for {plan.destination}

## 📅 Trip Details
- **Dates**: {plan.start_date} to {plan.end_date}
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
