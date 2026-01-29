import asyncio
import os
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import pygame
from dotenv import load_dotenv
from deepgram import DeepgramClient, PrerecordedOptions
import edge_tts

# Load environment variables
load_dotenv()

# --- CONFIGURATION ---
DEEPGRAM_API_KEY = os.getenv('DEEPGRAM_API')
INPUT_FILENAME = "input.wav"
OUTPUT_FILENAME = "response.mp3"
RECORD_SECONDS = 5  # Duration to record user input
SAMPLE_RATE = 44100

# Initialize Deepgram
try:
    deepgram = DeepgramClient(DEEPGRAM_API_KEY)
except Exception as e:
    print(f"Error initializing Deepgram: {e}")
    print("Make sure DEEPGRAM_API is set in your .env file")
    exit(1)

# --- 1. RECORDING FUNCTION (SoundDevice) ---
def record_audio(filename, duration, fs=44100):
    print(f"🎤 Listening for {duration} seconds...")
    
    # Record audio into a NumPy array
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
    sd.wait()  # Wait until recording is finished
    
    # Save as WAV file
    wav.write(filename, fs, recording)
    print("✅ Recording complete.")

# --- 2. TRANSCRIPTION FUNCTION (Deepgram) ---
def transcribe_audio(file_path):
    if not os.path.exists(file_path):
        return None
        
    with open(file_path, "rb") as buffer:
        payload = {"buffer": buffer}
        options = PrerecordedOptions(
            model="nova-2",      # Fast model
            smart_format=True,   # Adds punctuation
            language="en-US"
        )
        response = deepgram.listen.prerecorded.v("1").transcribe_file(payload, options)
        return response.results.channels[0].alternatives[0].transcript

# --- 3. TTS FUNCTION (Edge TTS) ---
async def generate_speech(text, output_file):
    # Voices: "en-US-AriaNeural" (Female), "en-US-GuyNeural" (Male)
    communicate = edge_tts.Communicate(text, "en-US-AriaNeural")
    await communicate.save(output_file)

# --- 4. PLAYBACK FUNCTION (Pygame) ---
def play_audio(file_path):
    pygame.mixer.init()
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play()
    
    # Wait for playback to finish
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)
        
    pygame.mixer.quit() # Release the file so it can be overwritten next turn

# --- MAIN LOOP ---
async def run_turn():
    # A. Record User
    record_audio(INPUT_FILENAME, RECORD_SECONDS, SAMPLE_RATE)
    
    # B. Transcribe
    print("Thinking...")
    user_text = transcribe_audio(INPUT_FILENAME)
    
    if not user_text:
        print("No speech detected.")
        return

    print(f"👤 User said: {user_text}")
    
    # C. Logic (Placeholder for your Agent Core)
    # response_text = agent_core(user_text) 
    response_text = f"I heard you say: {user_text}. I am checking the database for you now." 
    
    # D. Text-to-Speech
    await generate_speech(response_text, OUTPUT_FILENAME)
    print(f"🤖 Agent: {response_text}")
    
    # E. Play Response
    play_audio(OUTPUT_FILENAME)

# Run the async loop
if __name__ == "__main__":
    while True:
        input("Press Enter to start talking (or Ctrl+C to quit)...")
        asyncio.run(run_turn())