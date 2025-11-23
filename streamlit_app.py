import streamlit as st
import google.generativeai as genai
from streamlit_mic_recorder import mic_recorder
import tempfile
import os

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Jarvis 2.5", page_icon="⚡", layout="centered")

# --- 2. MOBILE OLED STYLE ---
st.markdown("""
    <style>
    /* Deep Black Background */
    .stApp { background-color: #000000; color: #E0E0E0; }
    
    /* Hide Streamlit Bars */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* User Chat Bubble (Right) */
    .user-msg {
        background-color: #1E1E1E; color: white; padding: 12px 18px;
        border-radius: 18px 18px 4px 18px; margin: 8px 0; float: right; clear: both; max-width: 85%;
        border: 1px solid #333;
    }
    
    /* Jarvis Chat Bubble (Left) */
    .ai-msg {
        background-color: #7000FF; /* Neon Purple */
        color: white; padding: 12px 18px;
        border-radius: 18px 18px 18px 4px; margin: 8px 0; float: left; clear: both; max-width: 90%;
        box-shadow: 0 0 15px rgba(112, 0, 255, 0.3);
    }
    
    /* Fix Input Bar to Bottom */
    .stTextInput { position: fixed; bottom: 0; left: 0; width: 100%; background: black; z-index: 100; padding: 10px; }
    </style>
""", unsafe_allow_html=True)

# --- 3. MEMORY SYSTEM ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 4. MODEL LOADER (Gemini 2.5 Force) ---
def get_model(api_key):
    genai.configure(api_key=api_key)
    # Try to load Gemini 2.5, fallback to 1.5 if not available in region
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        return model, "Gemini 2.5 ⚡"
    except:
        return genai.GenerativeModel("gemini-1.5-flash-latest"), "Gemini 1.5 (Backup)"

# --- 5. AUDIO PROCESSOR ---
def process_audio(audio_bytes, api_key):
    # Create temp file for audio
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
        temp_audio.write(audio_bytes)
        temp_path = temp_audio.name

    try:
        model, name = get_model(api_key)
        myfile = genai.upload_file(temp_path)
        
        prompt = "You are JARVIS. Listen to this audio. Be concise, intelligent, and helpful."
        
        response = model.generate_content([prompt, myfile])
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        os.remove(temp_path)

# --- 6. TEXT PROCESSOR ---
def process_text(text_input, api_key):
    model, name = get_model(api_key)
    
    # Send History for context
    chat_history = []
    for msg in st.session_state.messages:
        role = "user" if msg['role'] == "user" else "model"
        chat_history.append({"role": role, "parts": [msg['content']]})
    
    chat = model.start_chat(history=chat_history)
    response = chat.send_message("You are JARVIS. " + text_input)
    return response.text

# --- 7. UI LAYOUT ---
if "GOOGLE_API_KEY" in st.secrets:
    _, model_name = get_model(st.secrets["GOOGLE_API_KEY"])
    st.markdown(f"<h3 style='text-align: center; color: white;'>🎙️ JARVIS <br><span style='font-size: 12px; color: #7000FF;'>{model_name}</span></h3>", unsafe_allow_html=True)

# Display Chat History
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f"<div class='user-msg'>{msg['content']}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='ai-msg'>{msg['content']}</div>", unsafe_allow_html=True)

# Spacing for bottom bar
st.markdown("<div style='margin-bottom: 120px;'></div>", unsafe_allow_html=True)

# --- 8. INPUT CONTROLS ---
col1, col2 = st.columns([1, 4])
with col1:
    # Voice Button
    audio_data = mic_recorder(start_prompt="🎤", stop_prompt="🟥", just_once=True, key='recorder')
with col2:
    # Text Input
    text_input = st.chat_input("Type or Speak...")

# --- 9. LOGIC EXECUTION ---
if audio_data:
    st.session_state.messages.append({"role": "user", "content": "🎤 [Voice Command]"})
    if "GOOGLE_API_KEY" in st.secrets:
        with st.spinner("Processing..."):
            reply = process_audio(audio_data['bytes'], st.secrets["GOOGLE_API_KEY"])
            st.session_state.messages.append({"role": "ai", "content": reply})
            st.rerun()

elif text_input:
    st.session_state.messages.append({"role": "user", "content": text_input})
    if "GOOGLE_API_KEY" in st.secrets:
        with st.spinner("Thinking..."):
            reply = process_text(text_input, st.secrets["GOOGLE_API_KEY"])
            st.session_state.messages.append({"role": "ai", "content": reply})
            st.rerun()
