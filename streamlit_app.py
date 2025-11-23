import streamlit as st
import google.generativeai as genai
from streamlit_mic_recorder import mic_recorder
import tempfile
import os
import re

# --- 1. CONFIG ---
st.set_page_config(page_title="Jarvis OS", page_icon="🔓", layout="centered")

# --- 2. STYLE ---
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #E0E0E0; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .user-msg {
        background-color: #1E1E1E; color: white; padding: 12px 18px;
        border-radius: 18px 18px 4px 18px; margin: 8px 0; float: right; clear: both; max-width: 85%;
    }
    .ai-msg {
        background-color: #00CC00; /* Hacker Green */
        color: black; padding: 12px 18px; font-weight: bold;
        border-radius: 18px 18px 18px 4px; margin: 8px 0; float: left; clear: both; max-width: 90%;
    }
    .stTextInput { position: fixed; bottom: 0; width: 100%; background: black; z-index: 100; }
    </style>
""", unsafe_allow_html=True)

# --- 3. THE "DEEP LINK" DATABASE ---
# This maps App Names to their secret phone commands
APP_LINKS = {
    "youtube": "vnd.youtube://",
    "whatsapp": "whatsapp://",
    "instagram": "instagram://",
    "twitter": "twitter://",
    "x": "twitter://",
    "spotify": "spotify://",
    "gmail": "googlegmail://",
    "maps": "comgooglemaps://",
    "camera": "camera:", # Works on some devices
    "photos": "photos-redirect://",
    "calculator": "calculator://"
}

# --- 4. SYSTEM PROMPT (The Brain) ---
SYSTEM_PROMPT = """
You are JARVIS.
If the user says "Open [App Name]", you MUST respond with EXACTLY: [[OPEN:appname]].
Example: User "Open YouTube" -> You: "[[OPEN:youtube]] Opening YouTube sir."
Example: User "Open WhatsApp" -> You: "[[OPEN:whatsapp]] Accessing WhatsApp."

For any other request, just answer normally and briefly.
"""

if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 5. FUNCTIONS ---
def get_model(api_key):
    genai.configure(api_key=api_key)
    return genai.GenerativeModel("gemini-2.5-flash") # Or 1.5-flash-latest

def process_logic(response_text):
    # Check if Gemini wants to open an app
    match = re.search(r"\[\[OPEN:(.*?)\]\]", response_text.lower())
    if match:
        app_name = match.group(1)
        clean_text = response_text.replace(match.group(0), "") # Remove the tag from display
        
        # Get the deep link
        link = APP_LINKS.get(app_name)
        
        if link:
            # MAGICAL JAVASCRIPT REDIRECT
            # This forces the mobile browser to switch apps
            html_code = f"""
                <script>
                setTimeout(function() {{
                    window.location.href = "{link}";
                }}, 1000);
                </script>
                <span style="color: #00FF00;">🚀 Launching {app_name}...</span>
            """
            st.components.v1.html(html_code, height=0)
            return clean_text
        else:
            return f"I don't know the link for {app_name}, sir."
    return response_text

def process_audio(audio_bytes, api_key):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
        temp_audio.write(audio_bytes)
        temp_path = temp_audio.name
    try:
        model, _ = get_model(api_key), "Gemini"
        myfile = genai.upload_file(temp_path)
        response = model.generate_content([SYSTEM_PROMPT, "Listen and obey.", myfile])
        return process_logic(response.text)
    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        os.remove(temp_path)

def process_text(text, api_key):
    model, _ = get_model(api_key), "Gemini"
    chat = model.start_chat(history=[])
    response = chat.send_message(SYSTEM_PROMPT + "\nUser: " + text)
    return process_logic(response.text)

# --- 6. UI ---
st.markdown("<h3 style='text-align: center;'>🔓 JARVIS <span style='font-size:12px'>OS</span></h3>", unsafe_allow_html=True)

for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f"<div class='user-msg'>{msg['content']}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='ai-msg'>{msg['content']}</div>", unsafe_allow_html=True)

st.markdown("<div style='margin-bottom: 100px;'></div>", unsafe_allow_html=True)

col1, col2 = st.columns([1, 4])
with col1:
    audio_data = mic_recorder(start_prompt="🎤", stop_prompt="🟥", just_once=True, key='recorder')
with col2:
    text_input = st.chat_input("Command...")

if audio_data:
    st.session_state.messages.append({"role": "user", "content": "🎤 [Voice]"})
    if "GOOGLE_API_KEY" in st.secrets:
        with st.spinner("Processing..."):
            reply = process_audio(audio_data['bytes'], st.secrets["GOOGLE_API_KEY"])
            st.session_state.messages.append({"role": "ai", "content": reply})
            st.rerun()

elif text_input:
    st.session_state.messages.append({"role": "user", "content": text_input})
    if "GOOGLE_API_KEY" in st.secrets:
        with st.spinner("Executing..."):
            reply = process_text(text_input, st.secrets["GOOGLE_API_KEY"])
            st.session_state.messages.append({"role": "ai", "content": reply})
            st.rerun()
