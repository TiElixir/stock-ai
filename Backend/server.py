from fastapi import FastAPI, BackgroundTasks # Import BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import main  
import ai    

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/reset-chat")
async def reset_chat():
    print("🔄 UI REFRESH: Clearing AI Context...")
    try:
        # Assuming you have a reset function in your ai.py
        ai.reset_session() 
        return {"status": "success", "message": "Context cleared."}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/run-agent")
async def run_agent(background_tasks: BackgroundTasks):
    print("\n⚡ API CALL: Processing Voice Request...")
    
    # 1. Record
    audio_data = main.record_manual_api(duration=5)
    
    if len(audio_data) == 0:
        return {"bot_text": "I didn't hear anything.", "type": None, "items": []}

    # 2. Transcribe 
    # MAKE SURE THIS VARIABLE NAME IS 'user_text'
    user_text = main.transcribe(audio_data) 
    print(f"👤 User: {user_text}")

    # 3. Brain
    # Now 'user_text' exists and can be passed here
    structured_response = ai.process_user_input(user_text)

    structured_response["user_text"] = user_text
    
    # 4. Background Audio
    bot_message_text = structured_response.get("bot_text", "")
    if bot_message_text:
        background_tasks.add_task(main.speak, bot_message_text)
    
    return structured_response