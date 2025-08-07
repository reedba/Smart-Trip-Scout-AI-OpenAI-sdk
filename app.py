import gradio as gr
import asyncio
from datetime import datetime, timedelta
from planner import TripPlanner
import threading
import time

# Initialize the trip planner
planner = TripPlanner()

def plan_trip_gradio(destination, origin_city, start_date, end_date, interests_text, budget_level, num_travelers, include_lodging, email, enable_push):
    """
    Gradio interface function for trip planning with streaming updates.
    """
    if not destination or not start_date or not end_date:
        yield "Please fill in all required fields (destination and dates)."
        return
    
    # Parse interests
    interests = [interest.strip() for interest in interests_text.split(',') if interest.strip()]
    if not interests:
        interests = ['general']
    
    # Validate number of travelers
    try:
        num_travelers = int(num_travelers) if num_travelers else 1
        if num_travelers < 1:
            num_travelers = 1
    except ValueError:
        num_travelers = 1
    
    try:
        # Create new event loop for this thread  
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        all_updates = []
        formatted_plan = ""
        current_display = ""
        
        # Execute the planning step by step
        planning_gen = planner.plan_trip(destination, start_date, end_date, interests, budget_level, num_travelers, include_lodging, origin_city)
        
        # Process updates one by one
        try:
            while True:
                update = loop.run_until_complete(planning_gen.__anext__())
                all_updates.append(update)
                
                # Check if this is the formatted trip plan (contains detailed markdown)
                if "Smart Trip Scout Plan for" in update and len(update) > 200:
                    formatted_plan = update
                    yield formatted_plan
                else:
                    # Stream progress updates
                    current_display += f"{update}\n"
                    yield current_display
        except StopAsyncIteration:
            pass
        
        # Use the formatted plan as final result if available
        final_result = formatted_plan if formatted_plan else current_display
        
        # Handle email and push notifications
        if email and email.strip():
            try:
                email_content = '\n'.join(all_updates)
                if formatted_plan:
                    email_content += f"\n\n{formatted_plan}"
                
                final_result += "\n\n📧 Sending email..."
                yield final_result
                
                email_sent = planner.send_email(email.strip(), email_content)
                if email_sent:
                    final_result = final_result.replace("\n\n📧 Sending email...", "\n\n📧 Trip plan sent to your email!")
                else:
                    final_result = final_result.replace("\n\n📧 Sending email...", "\n\n❌ Failed to send email. Please check your email settings.")
                yield final_result
            except Exception as e:
                final_result = final_result.replace("\n\n📧 Sending email...", f"\n\n❌ Email error: {str(e)}")
                yield final_result
        
        if enable_push:
            try:
                final_result += "\n\n📱 Sending push notification..."
                yield final_result
                
                push_sent = planner.send_push_notification("Your Smart Trip Scout plan is ready!")
                if push_sent:
                    final_result = final_result.replace("\n\n📱 Sending push notification...", "\n\n📱 Push notification sent!")
                else:
                    final_result = final_result.replace("\n\n📱 Sending push notification...", "\n\n❌ Failed to send push notification. Please check your Pushover settings.")
                yield final_result
            except Exception as e:
                final_result = final_result.replace("\n\n📱 Sending push notification...", f"\n\n❌ Push notification error: {str(e)}")
                yield final_result
            
    except Exception as e:
        yield f"❌ Error planning trip: {str(e)}"
    finally:
        if 'loop' in locals():
            loop.close()

def create_gradio_interface():
    """Create the Gradio interface for Smart Trip Scout."""
    
    with gr.Blocks(title="Smart Trip Scout", theme=gr.themes.Soft()) as demo:
        gr.Markdown("""
        # 🌟 Smart Trip Scout AI
        
        Plan your perfect trip with AI-powered recommendations based on weather, your interests, and real-time data!
        """)
        
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("## 📋 Trip Details")
                
                destination = gr.Textbox(
                    label="🗺️ Destination",
                    placeholder="e.g., Paris, France",
                    info="Where would you like to go?"
                )
                
                origin_city = gr.Textbox(
                    label="🏠 Origin City (Optional)",
                    placeholder="e.g., New York, NY",
                    info="Your starting location for travel cost comparison"
                )
                
                with gr.Row():
                    start_date = gr.Textbox(
                        label="📅 Start Date",
                        placeholder="YYYY-MM-DD",
                        info="Trip start date"
                    )
                    end_date = gr.Textbox(
                        label="📅 End Date", 
                        placeholder="YYYY-MM-DD",
                        info="Trip end date"
                    )
                
                interests = gr.Textbox(
                    label="🎯 Your Interests",
                    placeholder="food, history, music, art, nature",
                    info="Separate interests with commas",
                    lines=2
                )
                
                gr.Markdown("## � Budget & Travel Details")
                
                with gr.Row():
                    budget_level = gr.Dropdown(
                        choices=["low", "mid", "luxury"],
                        value="mid",
                        label="💳 Budget Level",
                        info="Choose your budget preference"
                    )
                    num_travelers = gr.Number(
                        label="👥 Number of Travelers",
                        value=1,
                        minimum=1,
                        maximum=20,
                        step=1,
                        info="How many people?"
                    )
                
                include_lodging = gr.Checkbox(
                    label="🏨 Include Lodging Costs",
                    value=False,
                    info="Add hotel/accommodation costs to budget estimate"
                )
                
                gr.Markdown("## �📬 Notifications (Optional)")
                
                email = gr.Textbox(
                    label="📧 Email Address",
                    placeholder="your@email.com",
                    info="Send trip plan to email"
                )
                
                enable_push = gr.Checkbox(
                    label="📱 Enable Push Notifications",
                    info="Get notified when your plan is ready"
                )
                
                plan_button = gr.Button(
                    "🚀 Plan My Trip!",
                    variant="primary",
                    size="lg"
                )
            
            with gr.Column(scale=2):
                gr.Markdown("## 🗓️ Your Trip Plan")
                
                output = gr.Markdown(
                    value="Click 'Plan My Trip!' to start planning your adventure! ✨",
                    height=600
                )
        
        # Set up the event handler
        plan_button.click(
            fn=plan_trip_gradio,
            inputs=[destination, origin_city, start_date, end_date, interests, budget_level, num_travelers, include_lodging, email, enable_push],
            outputs=output
        )
        
        gr.Markdown("""
        ---
        
        ### 🔧 Setup Instructions
        
        1. Copy `.env.example` to `.env` and fill in your API keys:
           - `OPENAI_API_KEY`: Your OpenAI API key
           - `SENDGRID_API_KEY`: Your SendGrid API key (for email)
           - `PUSHOVER_USER_KEY` & `PUSHOVER_API_TOKEN`: Your Pushover credentials (for push notifications)
        
        2. Install dependencies: `pip install -r requirements.txt`
        
        ### 🎯 Features
        
        - **AI-Powered Planning**: Uses OpenAI to create intelligent itineraries
        - **Weather Integration**: Plans activities based on weather conditions
        - **Interest Matching**: Recommends activities and restaurants based on your preferences
        - **Festival & Event Detection**: Automatically finds local festivals and events during your trip
        - **Budget Estimation**: Get detailed cost breakdowns for low, mid, and luxury budgets
        - **Travel Cost Comparison**: Compare driving vs flying costs and get recommendations
        - **Multi-Traveler Support**: Plan for 1-20 travelers with accurate cost calculations
        - **Lodging Options**: Include or exclude accommodation costs
        - **Confidence Scoring**: Indicates how confident the AI is in the recommendations
        - **Email & Push Notifications**: Get your plan delivered directly to you
        
        ### 📝 Example Usage
        
        - **Destination**: Tokyo, Japan
        - **Origin City**: Los Angeles, CA
        - **Dates**: 2025-08-15 to 2025-08-20
        - **Travelers**: 2 people
        - **Budget**: Mid-range
        - **Interests**: food, culture, technology, anime
        - **Include Lodging**: Yes
        """)
    
    return demo

def main():
    """Main function to launch the Gradio app."""
    demo = create_gradio_interface()
    
    # Try multiple ports in case 7860 is busy
    ports_to_try = [7860, 7861, 7862, 7863, 7864]
    
    for port in ports_to_try:
        try:
            demo.launch(
                server_name="0.0.0.0",
                server_port=port,
                share=True,
                debug=True
            )
            break  # If successful, stop trying other ports
        except OSError as e:
            if "bind on address" in str(e) or "Cannot find empty port" in str(e):
                print(f"⚠️  Port {port} is busy, trying next port...")
                continue
            else:
                raise  # Re-raise if it's a different error
    else:
        print("❌ Could not find an available port. Please stop other instances or specify a different port.")

if __name__ == "__main__":
    main()
