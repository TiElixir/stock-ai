import asyncio
import os
import numpy as np
import sounddevice as sd
import queue
import edge_tts
import pygame
import scipy.io.wavfile as wav
from faster_whisper import WhisperModel
from dotenv import load_dotenv

# --- CONFIGURATION ---
load_dotenv()
MODEL_SIZE = "base.en"
SAMPLE_RATE = 16000

# 🔴 FIX: USE DEVICE 0 (Raw Hardware)
MIC_DEVICE_ID = 9

# --- IMPORT BRAIN ---
try:
    from brain import process_user_input
except ImportError:
    def process_user_input(text): return f"I heard: {text} (Brain not connected)"

# --- STATE ---
print("⏳ Loading Whisper Model...")
model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8") 
print("✅ Model Loaded!")

audio_queue = queue.Queue()

def audio_callback(indata, frames, time, status):
    if status:
        print(status, flush=True)
    audio_queue.put(indata.copy())

# --- 1. RECORD MANUAL (PUSH-TO-TALK) ---
def record_manual():
    print("\n" + "="*40)
    print(f"🎤 SELECTED MIC: Device {MIC_DEVICE_ID} (Raw Hardware)")
    input("👉 Press ENTER to START recording...")
    print("🔴 RECORDING... (Speak now!)")
    
    with audio_queue.mutex:
        audio_queue.queue.clear()
        
    try:
        # 🔴 CRITICAL: Raw Hardware 'hw:0,0' REQUIRES 2 channels
        stream = sd.InputStream(
            device=MIC_DEVICE_ID, 
            samplerate=SAMPLE_RATE, 
            channels=2,             # <--- FORCE STEREO
            dtype='int16', 
            callback=audio_callback
        )
        
        with stream:
            input("👉 Press ENTER to STOP...") # Waits for you
            
    except Exception as e:
        print(f"❌ Error opening mic: {e}")
        return np.array([])

    print("✅ Stopped. Processing...")
    
    # Collect audio
    audio_data = []
    while not audio_queue.empty():
        audio_data.append(audio_queue.get())
    
    if not audio_data:
        return np.array([])
        
    combined = np.concatenate(audio_data)
    
    # 🔴 FIX: WHISPER NEEDS MONO
    # We select Channel 0 (Left) and ignore Channel 1
    if combined.ndim > 1 and combined.shape[1] == 2:
        combined = combined[:, 0]
    
    # --- DEBUG SAVER ---
    # If this file is silent, your PHYSICAL mic switch is off
    wav.write("debug_audio.wav", SAMPLE_RATE, combined)
    # -------------------
    
    return combined

# --- 2. TRANSCRIPTION ---
def transcribe(audio_data):
    if len(audio_data) == 0:
        return ""
    
    # Normalize
    audio_float = audio_data.astype(np.float32) / 32768.0
    segments, info = model.transcribe(audio_float, beam_size=5)
    
    full_text = ""
    for segment in segments:
        full_text += segment.text
    return full_text.strip()

# --- 3. TTS ---
async def speak(text):
    print(f"🤖 Agent: {text}")
    communicate = edge_tts.Communicate(text, "en-US-AriaNeural")
    await communicate.save("response.mp3")
    
    pygame.mixer.init()
    pygame.mixer.music.load("response.mp3")
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)
    pygame.mixer.quit()

# --- MAIN LOOP ---
async def main_loop():
    while True:
        # A. Record
        audio_data = record_manual()
        
        if len(audio_data) == 0:
            print("⚠️ No audio data captured.")
            continue

        # B. Transcribe
        print("🧠 Transcribing...")
        user_text = transcribe(audio_data)
        print(f"👤 User: {user_text}")
        
        if len(user_text) < 1:
            print("... (Silence detected)")
            continue

        # C. Brain
        response = process_user_input(user_text)
        
        # D. Speak
        await speak(response)

if __name__ == "__main__":
    try:
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        print("\nGoodbye!")