# Smart Trip Scout AI - OpenAI SDK Implementation

A smart travel planning application that uses AI to create personalized itineraries based on user preferences, weather conditions, and real-time information.

## 🌟 Features

- **AI-Powered Planning**: Uses OpenAI SDK to create intelligent itineraries
- **Weather Integration**: Plans activities based on weather conditions  
- **Interest Matching**: Recommends activities and restaurants based on your preferences
- **Confidence Scoring**: Indicates how confident the AI is in the recommendations
- **Email & Push Notifications**: Get your plan delivered directly to you
- **Streaming Updates**: See real-time progress as your trip is being planned

## 🚀 Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/reedba/Smart-Trip-Scout-AI-OpenAI-sdk.git
   cd Smart-Trip-Scout-AI-OpenAI-sdk
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your API keys:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   SENDGRID_API_KEY=your_sendgrid_api_key_here  # Optional: for email
   PUSHOVER_USER_KEY=your_pushover_user_key_here  # Optional: for push notifications
   PUSHOVER_API_TOKEN=your_pushover_api_token_here  # Optional: for push notifications
   ```

4. **Run the application**
   ```bash
   python trip_scout.py
   ```

5. **Open your browser**
   - The app will start on `http://localhost:7860`
   - A shareable link will also be provided

## 🎯 How It Works

The Smart Trip Scout follows these AI-powered stages:

### Stage 1: Information Gathering
- Uses `@websearch_tool` to search for:
  - Current weather in the destination for the given dates
  - Best restaurants based on user interests  
  - Best activities or events happening during that time

### Stage 2: Evaluation
- Uses `@function_tool` evaluator to:
  - Score each activity and restaurant based on interest alignment and weather
  - Yields status messages like "Evaluating activities..."

### Stage 3: Optimization  
- Uses `@function_tool` optimizer to:
  - Build a daily itinerary (morning, afternoon, evening)
  - Replace activities with better alternatives if needed
  - Yields progress messages during optimization

### Stage 4: Quality Check
- If confidence is below 0.7, yields "Low confidence in plan – suggest user review"
- Otherwise confirms high confidence in the recommendations

### Stage 5: Delivery (Optional)
- Send final plan via email (SendGrid)
- Send push notification (Pushover)

## 📝 Example Usage

**Input:**
- **Destination**: Tokyo, Japan
- **Dates**: 2025-08-15 to 2025-08-20  
- **Interests**: food, culture, technology, anime

**Output:**
The app will generate a comprehensive itinerary with:
- Daily schedules (morning, afternoon, evening activities)
- Weather-appropriate recommendations
- Restaurant suggestions matching your food interests
- Cultural and tech-related activities
- Confidence scoring for each recommendation

## 🔧 File Structure

```
Smart-Trip-Scout-AI-OpenAI-sdk/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── .env.example             # Environment variables template
├── trip_scout.py            # Main entry point
├── app.py                   # Gradio web interface
└── planner.py              # Core trip planning logic with OpenAI integration
```

## 🛠️ API Keys Setup

### Required:
- **OpenAI API Key**: Get from [OpenAI Platform](https://platform.openai.com/api-keys)

### Optional:
- **SendGrid API Key**: Get from [SendGrid](https://sendgrid.com/) for email functionality
- **Pushover Credentials**: Get from [Pushover](https://pushover.net/) for push notifications

## 📱 Usage Tips

1. **Date Format**: Use YYYY-MM-DD format (e.g., 2025-08-15)
2. **Interests**: Separate multiple interests with commas
3. **Weather Integration**: The app considers weather when recommending outdoor vs indoor activities
4. **Confidence Score**: Higher scores (>0.7) indicate more reliable recommendations

## 🔒 Privacy & Security

- API keys are stored locally in `.env` file
- No user data is permanently stored
- All communications use secure APIs

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)  
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙋‍♂️ Support

If you encounter any issues or have questions:
1. Check the [Issues](https://github.com/reedba/Smart-Trip-Scout-AI-OpenAI-sdk/issues) page
2. Create a new issue with detailed information
3. Include error messages and steps to reproduce

---

**Happy Travels! 🌍✈️**
