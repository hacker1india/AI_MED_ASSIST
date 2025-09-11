# import modules
import streamlit as st
import google.generativeai as genai

# --- API KEY ---
api_key = "AIzaSyCDDf8t7hYsjP1jE_3NALM3r7OUzaaZqF8"
genai.configure(api_key=api_key)

# --- Model Config ---
generation_config = {
    "temperature": 0.4,
    "top_p": 1,
    "top_k": 32,
    "max_output_tokens": 4096,
}

safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]

# --- Page Config ---
st.set_page_config(page_title="MediScan AI", page_icon="MediScanAI.png", layout="wide")

# --- CSS Styling ---
st.markdown("""
    <style>
    body, h1, h2, h3, h4, h5, h6 {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .card {
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        margin-bottom: 15px;
    }
    .stButton>button {
        background-color: #138808;
        color: white;
        font-size: 16px;
        font-weight: bold;
        border-radius: 10px;
        padding: 10px 20px;
        margin: 5px 0px;
        border: none;
        transition: all 0.2s ease-in-out;
    }
    .stButton>button:hover {
        background-color: #0f6c06;
        transform: scale(1.05);
    }
    .response-text {
        font-size: 18px;
        color: #000000;
    }
    .tab-header {
        color: #138808;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# --- Header ---
col1, col2 = st.columns([1,5])
with col1:
    st.image("MediScanAI.png", width=120)
with col2:
    st.markdown("<h1 class='tab-header'>💚 MediScan AI</h1>", unsafe_allow_html=True)
    st.markdown("<h3>Your Smart Medical Assistant 🤖</h3>", unsafe_allow_html=True)

st.markdown("---")

# --- Tabs ---
tab1, tab2 = st.tabs(["📷 Image Analysis", "💬 Chat Assistant"])

# --- TAB 1: Image Analysis ---
with tab1:
    st.subheader("📤 Upload a medical image for analysis")
    uploaded_file = st.file_uploader("", type=['png','jpg','jpeg'])
    generate_btn = st.button("🔍 Generate Analysis")

    if "image_response" not in st.session_state:
        st.session_state.image_response = ""
        st.session_state.image_lang = "en"

    if generate_btn:
        if uploaded_file:
            st.image(uploaded_file, caption="Uploaded Medical Image", use_column_width=True)

            model = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            image_data = {"mime_type": uploaded_file.type, "data": uploaded_file.getvalue()}

            with st.spinner("Analyzing image... ⏳"):
                response = model.generate_content([
                    "You are a medical assistant AI. Analyze this image and provide possible observations, "
                    "potential concerns, and general recommendations. Make it clear, structured, and easy "
                    "for a non-medical person to understand. Avoid giving a final diagnosis. Always "
                    "recommend consulting a certified doctor for confirmation.",
                    image_data
                ])
            st.session_state.image_response = response.text
            st.session_state.image_lang = "en"

    # Display card with response
    if st.session_state.image_response:
        st.markdown(
            f"<div class='card response-text' style='background-color:#e0ffe0'>{st.session_state.image_response}</div>",
            unsafe_allow_html=True
        )

        # Buttons: Translate / Download
        col1_btn, col2_btn = st.columns([1,1])
        with col1_btn:
            translate_btn = st.button("🌐 Translate to Telugu")
        with col2_btn:
            st.download_button("📥 Download as TXT", st.session_state.image_response, file_name="MediScan_Analysis.txt")

        if translate_btn:
            model = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            with st.spinner("Translating..."):
                translation_response = model.generate_content([
                    "Translate the following text to Telugu accurately, preserving meaning and clarity for non-medical users:",
                    st.session_state.image_response
                ])
            st.session_state.image_response = translation_response.text
            st.session_state.image_lang = "te"
            st.experimental_rerun()

# --- TAB 2: Chat Assistant ---
with tab2:
    st.subheader("💬 Chat with MediScan AI")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "chat_lang" not in st.session_state:
        st.session_state.chat_lang = "en"

    # Display chat in cards
    for i, (role, message) in enumerate(st.session_state.chat_history):
        color = "#f0f0f0" if role=="assistant" else "#d9f2ff"
        st.markdown(f"<div class='card response-text' style='background-color:{color}'>{message}</div>", unsafe_allow_html=True)

    # Input box
    user_input = st.text_input("Ask anything about your health (general suggestions only):")

    # Buttons under input box
    col_send, col_stop, col_translate = st.columns([1,1,1])
    with col_send:
        send_btn = st.button("Send")
    with col_stop:
        stop_btn = st.button("⏹ Stop")
    with col_translate:
        translate_btn = st.button("🌐 Telugu")

    # Handle Send
    if send_btn and user_input.strip():
        st.session_state.chat_history.append(("user", user_input))
        chat_model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config=generation_config,
            safety_settings=safety_settings
        )
        with st.spinner("Thinking..."):
            response = chat_model.generate_content([
                "You are a helpful medical assistant AI. Provide friendly, structured, and clear "
                "suggestions based on the user's query. Do not give a final diagnosis. Always remind "
                "them to consult a certified doctor for confirmation.",
                user_input
            ])
        st.session_state.chat_history.append(("assistant", response.text))
        st.session_state.chat_lang = "en"
        st.experimental_rerun()

    # Handle Stop
    if stop_btn:
        st.session_state.chat_history = []
        st.session_state.chat_lang = "en"
        st.experimental_rerun()

    # Handle Translate
    if translate_btn and st.session_state.chat_history:
        last_index = len(st.session_state.chat_history)-1
        if st.session_state.chat_history[last_index][0]=="assistant":
            chat_model = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            with st.spinner("Translating..."):
                translation = chat_model.generate_content([
                    "Translate the following text to Telugu accurately, preserving meaning and clarity for non-medical users:",
                    st.session_state.chat_history[last_index][1]
                ])
            st.session_state.chat_history[last_index] = ("assistant", translation.text)
            st.session_state.chat_lang = "te"
            st.experimental_rerun()

    # Download chat
    if st.session_state.chat_history:
        chat_text = "\n".join([f"You: {m}" if r=="user" else f"MediScan AI: {m}" for r,m in st.session_state.chat_history])
        st.download_button("📥 Download Chat as TXT", chat_text, file_name="MediScan_Chat.txt")

# --- Footer ---
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: gray;'>"
    "Developed by <b>Pasumarthi Bhanu Prakash</b> | 📧 pbp309@gmail.com"
    "</p>", unsafe_allow_html=True
)
