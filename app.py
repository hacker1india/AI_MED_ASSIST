# --- MediScan AI: Image + Chat + Voice Output with Auto-Telugu ---

import streamlit as st
import google.generativeai as genai
from gtts import gTTS
import tempfile
import os

# --- API Key ---
api_key = "AIzaSyAK9B5Y90Yeokur9htpNd6Ed8lvQmaqpVw"  
genai.configure(api_key=api_key)

# --- Model Config ---
generation_config = {
    "temperature": 0.5,
    "top_p": 0.9,
    "top_k": 40,
    "max_output_tokens": 4096,
}

safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]

# --- Streamlit Config ---
st.set_page_config(page_title="MediScan AI", page_icon="🩺", layout="wide")

# --- CSS Styling ---
st.markdown("""
<style>
body, h1, h2, h3, h4, h5, h6 { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
.card { padding:20px; border-radius:15px; box-shadow:0 5px 15px rgba(0,0,0,0.1); margin-bottom:15px; }
.stButton>button { background-color:#138808;color:white;font-size:16px;font-weight:bold;border-radius:10px;padding:10px 20px;margin:5px 0px;border:none;transition: all 0.2s ease-in-out; }
.stButton>button:hover { background-color:#0f6c06; transform:scale(1.05);}
.response-text { font-size:18px;color:#000000; }
.tab-header { color:#138808; font-weight:bold; }
</style>
""", unsafe_allow_html=True)

# --- Header ---
col1, col2 = st.columns([1,5])
with col1:
    st.image("MediScanAI.png", width=100)
with col2:
    st.markdown("<h1 class='tab-header'>💚 MediScan AI</h1>", unsafe_allow_html=True)
    st.markdown("<h3>Your Smart Medical Assistant 🤖</h3>", unsafe_allow_html=True)
st.markdown("---")

# --- Tabs ---
tab1, tab2 = st.tabs(["📷 Image Analysis", "💬 Chat Assistant"])

# --------------------------------
# TAB 1: Image Analysis
# --------------------------------
with tab1:
    st.subheader("📤 Upload a medical image for AI-based analysis")
    uploaded_file = st.file_uploader("Upload Image", type=["jpg", "jpeg", "png"])
    analyze_btn = st.button("🔍 Analyze Image")

    if "image_result" not in st.session_state:
        st.session_state.image_result = ""
        st.session_state.image_lang = "en"

    if analyze_btn and uploaded_file:
        st.image(uploaded_file, caption="Uploaded Image", use_column_width=True)
        model = genai.GenerativeModel(
            "gemini-1.5-flash",
            generation_config=generation_config,
            safety_settings=safety_settings
        )
        image_data = {"mime_type": uploaded_file.type, "data": uploaded_file.getvalue()}
        with st.spinner("Analyzing image... ⏳"):
            response = model.generate_content([
                "You are a medical AI assistant. Analyze this image carefully and describe possible causes, symptoms, or recommendations clearly for a non-medical person. Avoid medical diagnosis and suggest consulting a doctor.",
                image_data
            ])
        st.session_state.image_result = response.text
        st.session_state.image_lang = "en"

    if st.session_state.image_result:
        st.markdown(f"<div class='card response-text' style='background-color:#e8ffe8'>{st.session_state.image_result}</div>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        with col1:
            translate = st.button("🌐 Translate to Telugu")
        with col2:
            st.download_button("📥 Download as TXT", st.session_state.image_result, file_name="MediScan_Analysis.txt")
        with col3:
            speak = st.button("🔊 Speak Response")

        if translate:
            trans_model = genai.GenerativeModel(
                "gemini-1.5-flash",
                generation_config=generation_config
            )
            with st.spinner("Translating..."):
                trans = trans_model.generate_content([
                    "Translate the following text into smooth, clear Telugu (simple terms for non-medical people):",
                    st.session_state.image_result
                ])
            st.session_state.image_result = trans.text
            st.session_state.image_lang = "te"
            st.experimental_rerun()

        if speak:
            lang = "te" if st.session_state.image_lang == "te" else "en"
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmpfile:
                tts = gTTS(st.session_state.image_result, lang=lang)
                tts.save(tmpfile.name)
                st.audio(tmpfile.name, format="audio/mp3")

# --------------------------------
# TAB 2: Chat Assistant
# --------------------------------
with tab2:
    st.subheader("💬 Ask health-related questions (general guidance only)")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
        st.session_state.chat_lang = "en"

    # Display chat
    for role, text in st.session_state.chat_history:
        bg = "#f0f0f0" if role == "assistant" else "#d9f2ff"
        st.markdown(f"<div class='card response-text' style='background-color:{bg}'>{text}</div>", unsafe_allow_html=True)

    user_input = st.text_input("Type your question:")
    send_btn, reset_btn, trans_btn, speak_btn = st.columns(4)

    if send_btn.button("Send") and user_input.strip():
        st.session_state.chat_history.append(("user", user_input))
        chat_model = genai.GenerativeModel(
            "gemini-1.5-flash",
            generation_config=generation_config,
            safety_settings=safety_settings
        )

        with st.spinner("Thinking..."):
            reply = chat_model.generate_content([
                "You are a kind and informative medical assistant AI. Provide easy-to-understand, structured, and friendly guidance. Avoid giving medical diagnosis. Always suggest visiting a doctor if necessary.",
                user_input
            ])
        st.session_state.chat_history.append(("assistant", reply.text))
        st.session_state.chat_lang = "en"
        st.experimental_rerun()

    if reset_btn.button("⏹ Clear Chat"):
        st.session_state.chat_history = []
        st.experimental_rerun()

    if trans_btn.button("🌐 Translate Last Reply to Telugu") and st.session_state.chat_history:
        last = len(st.session_state.chat_history) - 1
        if st.session_state.chat_history[last][0] == "assistant":
            trans_model = genai.GenerativeModel("gemini-1.5-flash", generation_config=generation_config)
            with st.spinner("Translating..."):
                trans = trans_model.generate_content([
                    "Translate the following text into natural Telugu for general users:",
                    st.session_state.chat_history[last][1]
                ])
            st.session_state.chat_history[last] = ("assistant", trans.text)
            st.session_state.chat_lang = "te"
            st.experimental_rerun()

    if speak_btn.button("🔊 Speak Last Reply") and st.session_state.chat_history:
        last = len(st.session_state.chat_history) - 1
        if st.session_state.chat_history[last][0] == "assistant":
            lang = "te" if st.session_state.chat_lang == "te" else "en"
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmpfile:
                tts = gTTS(st.session_state.chat_history[last][1], lang=lang)
                tts.save(tmpfile.name)
                st.audio(tmpfile.name, format="audio/mp3")

# --- Footer ---
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: gray;'>Developed by <b>Pasumarthi Bhanu Prakash</b> | 📧 pbp309@gmail.com</p>",
    unsafe_allow_html=True
)
