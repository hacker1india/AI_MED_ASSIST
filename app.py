# import modules
import streamlit as st
import google.generativeai as genai


# --- API KEY ---
api_key = "AIzaSyCDDf8t7hYsjP1jE_3NALM3r7OUzaaZqF8"

# configure API
genai.configure(api_key=api_key)

# setup model config
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

# set page config
st.set_page_config(page_title="MediScan AI", page_icon="MediScanAI.png", layout="wide")

# header section with logo and title
col1, col2 = st.columns([1, 5])
with col1:
    st.image("MediScanAI.png", width=120)
with col2:
    st.markdown("<h1 style='color:#138808;'>💚 MediScan AI</h1>", unsafe_allow_html=True)
    st.markdown("<h3>Your Smart Medical Assistant 🤖</h3>", unsafe_allow_html=True)

st.markdown("---")

# create tabs
tab1, tab2 = st.tabs(["📷 Image Analysis", "💬 Chat Assistant"])

# --- TAB 1 : Image Analysis ---
with tab1:
    st.subheader("📤 Upload a medical image for analysis")

    uploaded_file = st.file_uploader("Upload medical image", type=['png', 'jpg', 'jpeg'])
    if st.button("🔍 Generate Analysis"):
        if uploaded_file:
            st.image(uploaded_file, caption="Uploaded Medical Image", use_column_width=True)

            model = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                generation_config=generation_config,
                safety_settings=safety_settings
            )

            image_data = {
                "mime_type": uploaded_file.type,
                "data": uploaded_file.getvalue()
            }

            with st.spinner("Analyzing image... ⏳"):
                response = model.generate_content(
                    [
                        "You are a medical assistant AI. Analyze this image and provide possible observations, "
                        "potential concerns, and general recommendations. Make it clear, structured, and easy "
                        "for a non-medical person to understand. Avoid giving a final diagnosis. Always "
                        "recommend consulting a certified doctor for confirmation.",
                        image_data
                    ]
                )

            st.success("✅ Analysis Complete")
            st.subheader("📋 AI Analysis & Recommendations")
            st.write(response.text)

            # --- Download Options ---
            st.download_button("📥 Download as TXT", response.text, file_name="MediScan_Analysis.txt")

        else:
            st.warning("⚠️ Please upload an image first.")

# --- TAB 2 : Chat Assistant ---
with tab2:
    st.subheader("💬 Chat with MediScan AI")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # display chat history
    for role, message in st.session_state.chat_history:
        if role == "user":
            st.markdown(f"👤 **You:** {message}")
        else:
            st.markdown(f"🤖 **MediScan AI:** {message}")

    # chat input + buttons on same row
    col_input, col_send, col_stop = st.columns([6, 1, 1])
    with col_input:
        user_input = st.text_input("Ask me anything about your health (general suggestions only):")
    
        send_btn = st.button("Send")

        stop_btn = st.button("⏹ Stop")
    
    # handle send
    if send_btn and user_input.strip():
        st.session_state.chat_history.append(("user", user_input))

        chat_model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config=generation_config,
            safety_settings=safety_settings
        )

        with st.spinner("Thinking..."):
            response = chat_model.generate_content(
                [
                    "You are a helpful medical assistant AI. Provide friendly, structured, and clear "
                    "suggestions based on the user's query. Do not give a final diagnosis. Always remind "
                    "them to consult a certified doctor for confirmation.",
                    user_input
                ]
            )

        bot_reply = response.text
        st.session_state.chat_history.append(("assistant", bot_reply))
        st.rerun()

    # handle stop (clears chat)
    if stop_btn:
        st.session_state.chat_history = []
        st.rerun()

    # --- Download Chat History ---
    if st.session_state.chat_history:
        chat_text = "\n".join(
            [f"You: {m}" if r == "user" else f"MediScan AI: {m}" for r, m in st.session_state.chat_history]
        )
        st.download_button("📥 Download Chat as TXT", chat_text, file_name="MediScan_Chat.txt")

# --- Footer Credits ---
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: gray;'>"
    "Developed by <b>Pasumarthi Bhanu Prakash</b> | 📧 pbp309@gmail.com"
    "</p>",
    unsafe_allow_html=True
)
