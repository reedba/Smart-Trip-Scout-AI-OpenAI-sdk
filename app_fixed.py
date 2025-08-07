import gradio as gr
import asyncio
from datetime import datetime, timedelta
from planner import TripPlanner
import threading
import time

# Initialize the trip planner
planner = TripPlanner()

def plan_trip_gradio(destination, start_date, end_date, interests_text, email, enable_push):
    """
    Gradio interface function for trip planning with streaming updates.
    """
    if not destination or not start_date or not end_date:
        return "Please fill in all required fields (destination and dates)."
    
    # Parse interests
    interests = [interest.strip() for interest in interests_text.split(',') if interest.strip()]
    if not interests:
        interests = ['general']
    
    def run_async_planning():
        """Run the async planning in a separate thread."""
        try:
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            async def execute_planning():
                all_updates = []
                formatted_plan = ""
                
                # Execute the planning and collect updates
                planning_gen = planner.plan_trip(destination, start_date, end_date, interests)
                async for update in planning_gen:
                    all_updates.append(update)
                    # Check if this is the formatted trip plan (contains detailed markdown)
                    if "Smart Trip Scout Plan for" in update and len(update) > 200:
                        formatted_plan = update
                
                # For display, use the formatted plan if available
                display_result = formatted_plan if formatted_plan else '\n'.join(all_updates)
                
                # For email, include both status updates and the plan
                email_content = '\n'.join(all_updates)
                if formatted_plan:
                    email_content += f"\n\n{formatted_plan}"
                
                return display_result, email_content
            
            display_result, email_content = loop.run_until_complete(execute_planning())
            
            # Handle email and push notifications
            if email and email.strip():
                try:
                    email_sent = planner.send_email(email.strip(), email_content)
                    if email_sent:
                        display_result += "\n\n📧 Trip plan sent to your email!"
                    else:
                        display_result += "\n\n❌ Failed to send email. Please check your email settings."
                except Exception as e:
                    display_result += f"\n\n❌ Email error: {str(e)}"
            
            if enable_push:
                try:
                    push_sent = planner.send_push_notification("Your Smart Trip Scout plan is ready!")
                    if push_sent:
                        display_result += "\n\n📱 Push notification sent!"
                    else:
                        display_result += "\n\n❌ Failed to send push notification. Please check your Pushover settings."
                except Exception as e:
                    display_result += f"\n\n❌ Push notification error: {str(e)}"
            
            return display_result
            
        except Exception as e:
            return f"❌ Error planning trip: {str(e)}"
        finally:
            if 'loop' in locals():
                loop.close()
    
    # Run the planning
    return run_async_planning()

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
                
                gr.Markdown("## 📬 Notifications (Optional)")
                
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
            inputs=[destination, start_date, end_date, interests, email, enable_push],
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
        - **Confidence Scoring**: Indicates how confident the AI is in the recommendations
        - **Email & Push Notifications**: Get your plan delivered directly to you
        
        ### 📝 Example Usage
        
        - **Destination**: Tokyo, Japan
        - **Dates**: 2025-08-15 to 2025-08-20
        - **Interests**: food, culture, technology, anime
        """)
    
    return demo

def main():
    """Main function to launch the Gradio app."""
    demo = create_gradio_interface()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=True,
        debug=True
    )

if __name__ == "__main__":
    main()
