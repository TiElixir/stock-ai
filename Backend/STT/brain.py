import os
import google.generativeai as genai
from dotenv import load_dotenv

# --- CONFIGURATION ---
load_dotenv()
GEMINI_API_KEY = os.getenv('GEMINI_API')

if not GEMINI_API_KEY:
    print("❌ ERROR: GEMINI_API key missing in .env file")

genai.configure(api_key=GEMINI_API_KEY)

# --- SETUP MODEL ---
model = genai.GenerativeModel(
    model_name='gemini-2.5-flash',  # Fast & Cheap
    system_instruction="""
    You are a friendly and helpful AI voice assistant.
    1. Keep your answers SHORT and CONCISE (1-2 sentences max).
    2. Do not use special formatting like bolding or markdown, as this is for voice.
    3. Be conversational and natural.
    """
)

# Start a chat session (This stores history for context)
chat_session = model.start_chat(history=[])

# --- MAIN FUNCTION ---
def process_user_input(user_text):
    """
    Sends user text to Gemini and gets a text response.
    """
    if not user_text:
        return ""

    try:
        # Send message to Gemini
        response = chat_session.send_message(user_text)
        
        # Clean up text (remove * or # symbols that TTS hates)
        clean_text = response.text.replace("*", "").replace("#", "")
        return clean_text
        
    except Exception as e:
        print(f"❌ Gemini Error: {e}")
        return "I am having trouble thinking right now."

# --- TEST IT LOCALLY ---
if __name__ == "__main__":
    print("--- Simple Brain Test (Type 'q' to quit) ---")
    while True:
        user = input("You: ")
        if user.lower() == "q": break
        response = process_user_input(user)
        print(f"Bot: {response}")