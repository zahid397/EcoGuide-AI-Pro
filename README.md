🌍 EcoGuide AI Pro — Next-Gen Sustainable Travel Planner
EcoGuide AI Pro is an intelligent, adaptive, and sustainable travel planning assistant powered by Google Gemini 1.5 Flash and Qdrant Vector Database (RAG). It goes beyond simple planning by offering real-time plan analysis, cost leakage detection, carbon footprint estimation, and hyper-personalized recommendations.
Built for the Future of Eco-Tourism. 🌿
🚀 Key Features (Why this stands out)
🧠 AI-Powered Core
RAG Engine (Retrieval-Augmented Generation): Uses Vector Search to find real hotels, activities, and hidden gems from a curated dataset.
Smart "Refine" Logic: Modify plans instantly (e.g., "Make it cheaper", "Add more adventure").
Fail-Safe Architecture: Works even if the database or API temporarily fails (uses intelligent fallbacks).
📊 Pro SaaS Analytics
Plan Health Score: A calculated score (0-100) based on budget, eco-friendliness, and time management.
Cost Leakage Detector: AI identifies missing costs (e.g., "Lunch cost not included").
Time Stress Detector: Warns if the schedule is too packed.
Sustainability Dashboard: Interactive Radar Charts visualizing Eco Score vs. Carbon Savings.
✨ User Experience
Voice Assistant: Listen to your itinerary with built-in Text-to-Speech (TTS).
PDF Export: Download a clean, professionally formatted PDF of your trip.
Interactive Map: Visualizes trip locations dynamically.
AI Chatbot: Ask follow-up questions about the trip (e.g., "Is Dubai safe at night?").
🛠️ Tech Stack
Frontend: Streamlit (Custom UI with Tabs & Sidebar)
LLM: Google Gemini 1.5 Flash (via google-generativeai)
Vector Database: Qdrant (Cloud/Local)
Embeddings: Sentence Transformers (all-MiniLM-L6-v2)
Visualization: Plotly
Utilities: FPDF (PDF Generation), gTTS (Audio), Pandas (Data Processing)
⚙️ Installation & Setup
Follow these steps to run the app locally:
1. Clone the Repository
   git clone https://github.com/yourusername/ecoguide-ai-pro.git
cd ecoguide-ai-pro
2.Create Virtual Environment (Recommended)
python -m venv venv
# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate
3.Install Dependencies

pip install -r requirements.txt
4. Set Up Environment Variables
Create a .env file in the root directory and add your API keys:
# Required: Google Gemini API Key
GEMINI_API_KEY="your_google_api_key_here"

# Required: Qdrant Configuration
# Use ":memory:" for local testing without server setup
QDRANT_URL=":memory:"
# OR for Cloud:
# QDRANT_URL="https://your-cluster-url.qdrant.tech"
# QDRANT_API_KEY="your_qdrant_api_key"
5. Run the App
   streamlit run app.py
   📂 Project Structure
The project follows a modular, production-ready structure:
EcoGuide-Pro/
├── app.py                # Main Entry Point
├── backend/              # AI & Database Logic
│   ├── agent_workflow.py # Gemini AI Logic & Prompts
│   ├── rag_engine.py     # Qdrant Vector Search
│   └── utils.py          # JSON Parsers
├── ui/                   # User Interface Components
│   ├── sidebar.py        # Sidebar Input Logic
│   ├── main_content.py   # Main Dashboard Logic
│   └── tabs/             # Individual Tab Modules
├── utils/                # Helper Functions
│   ├── pdf.py            # PDF Generator
│   ├── tts.py            # Text-to-Speech
│   ├── schemas.py        # Pydantic Validators
│   └── ...
├── data/                 # CSV Datasets (Hotels, Places)
├── prompts/              # AI Prompt Templates
└── logs/                 # Error Logs
📸 Screenshots
Dashboard Analysis Tab PDF Export
https://drive.google.com/drive/folders/1zSgFIpZGdQk7JB3DsFRePbKJjvZNExRq
🔮 Future Roadmap
Live API Integration: Real-time flight and hotel booking prices.
Social Sharing: Share itineraries directly to social media via link.
Collaborative Planning: Allow multiple users to edit the same plan
🤝 Contributing
Contributions are welcome! Please fork the repository and submit a pull request.
📄 License
This project is licensed under the MIT License.
Made with ❤️ by [zahid Hasan]
