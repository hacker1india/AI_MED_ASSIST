# --- MediScan AI: Image + Chat + Voice Output with Auto-Telugu ---

# --- MediScan AI: Image + Chat + Voice Output with Auto-Telugu ---

import streamlit as st
import google.generativeai as genai
from gtts import gTTS

# --- API Key ---
api_key = "AIzaSyDylTQRIOLjVojNI13JTw4YKZ8y_TxVgfk"
genai.configure(api_key=api_key)

generation_config = {
    "temperature": 0.3,
    "top_p": 0.8,
    "top_k": 40,
    "max_output_tokens": 512,
}

safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]

# --- Choose Gemini Model ---
# Try gemini-2.5-flash if available, else fallback to gemini-1.5-flash
MODEL_NAME = "models/gemini-2.5-flash"  # ✅ new version
# If you still get 404, change to:
# MODEL_NAME = "models/gemini-1.5-flash"

# --- Streamlit Page ---
st.set_page_config(page_title="MediScan AI", page_icon="🩺", layout="wide")

st.title("🩺 MediScan AI")
st.markdown("Upload **medical image** + Chat with AI. Get text, Telugu translation, and speech.")

# --- Session State ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "chat_lang" not in st.session_state:
    st.session_state.chat_lang = "en"

# --- Input ---
user_input = st.chat_input("Type your medical question...")

# --- Display Chat ---
for role, content in st.session_state.chat_history:
    with st.chat_message(role):
        st.write(content)

# --- Process User Input ---
if user_input:
    with st.chat_message("user"):
        st.write(user_input)

    # Add to history
    st.session_state.chat_history.append(("user", user_input))

    # Gemini Response
    chat_model = genai.GenerativeModel(
        model_name=MODEL_NAME,
        generation_config=generation_config,
        safety_settings=safety_settings
    )

    with st.spinner("AI thinking..."):
        response = chat_model.generate_content([
            "You are a helpful medical assistant AI. Provide friendly, clear, structured advice. "
            "Do not give final diagnosis. Remind user to consult a doctor.",
            user_input
        ])

    ai_response = response.text
    with st.chat_message("assistant"):
        st.write(ai_response)

    st.session_state.chat_history.append(("assistant", ai_response))
    st.session_state.chat_lang = "en"

# --- Action Buttons ---
col1, col2 = st.columns(2)
with col1:
    translate_btn = st.button("🌐 Translate to Telugu")
with col2:
    speak_btn = st.button("🔊 Speak Response")

# --- Translate Button ---
if translate_btn and st.session_state.chat_history:
    if st.session_state.chat_history[-1][0] == "assistant":
        chat_model = genai.GenerativeModel(
            model_name=MODEL_NAME,
            generation_config=generation_config,
            safety_settings=safety_settings
        )
        with st.spinner("Translating..."):
            translation = chat_model.generate_content([
                "Translate the following text to Telugu accurately for non-medical users:",
                st.session_state.chat_history[-1][1]
            ])
        translated_text = translation.text
        st.session_state.chat_history[-1] = ("assistant", translated_text)
        st.session_state.chat_lang = "te"
        st.experimental_rerun()

# --- Speak Button ---
if speak_btn and st.session_state.chat_history:
    if st.session_state.chat_history[-1][0] == "assistant":
        lang_code = "te" if st.session_state.chat_lang == "te" else "en"
        tts = gTTS(st.session_state.chat_history[-1][1], lang=lang_code)
        tts.save("response.mp3")
        with open("response.mp3", "rb") as audio_file:
            st.audio(audio_file.read(), format="audio/mp3")


# --- Footer ---
st.markdown("---")
st.markdown("<p style='text-align: center; color: gray;'>Developed by <b>Pasumarthi Bhanu Prakash</b> | 📧 pbp309@gmail.com</p>", unsafe_allow_html=True)

