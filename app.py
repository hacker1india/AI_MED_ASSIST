import streamlit as st
import pandas as pd
import os
import hashlib
import google.generativeai as genai
from gtts import gTTS
import tempfile
import time

# -------------------------
# CONFIGURATION
# -------------------------
st.set_page_config(page_title="💚 MediScan AI", layout="wide")
api_key = "AIzaSyAgMYQjWh6wSe8GBoZHz4HiHWnZ27RxPVI"
genai.configure(api_key=api_key)

generation_config = {
    "temperature": 0.7,
    "top_p": 1,
    "top_k": 50,
    "max_output_tokens": 4096,
}

# -------------------------
# USER AUTHENTICATION
# -------------------------
USER_DB = "users.csv"

def make_hash(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hash(password, hashed):
    return make_hash(password) == hashed

def init_user_db():
    if not os.path.exists(USER_DB) or os.path.getsize(USER_DB) == 0:
        df = pd.DataFrame(columns=["username", "password", "email"])
        df.to_csv(USER_DB, index=False)

def save_user(username, password, email):
    init_user_db()
    df = pd.read_csv(USER_DB)
    if username.lower() in df["username"].astype(str).str.lower().values:
        return False
    new_user = pd.DataFrame([[username.strip(), make_hash(password), email.strip()]],
                            columns=["username", "password", "email"])
    df = pd.concat([df, new_user], ignore_index=True)
    df.to_csv(USER_DB, index=False)
    return True

def validate_user(username, password):
    init_user_db()
    df = pd.read_csv(USER_DB)
    if df.empty or "username" not in df.columns:
        return False
    df["username"] = df["username"].astype(str)
    user = df[df["username"].str.lower() == username.lower()]
    if not user.empty:
        stored_hash = str(user.iloc[0]["password"])
        return check_hash(password, stored_hash)
    return False

# -------------------------
# LOGIN / SIGNUP
# -------------------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "page" not in st.session_state:
    st.session_state.page = "login"

if not st.session_state.authenticated:
    st.title("💚 MediScan AI - Smart Health Assistant")
    st.markdown("### Login or Sign Up to continue")

    if st.session_state.page == "signup":
        st.subheader("📝 Create Account")
        new_user = st.text_input("👤 Username")
        new_email = st.text_input("📧 Email")
        new_pass = st.text_input("🔑 Password", type="password")
        conf_pass = st.text_input("✅ Confirm Password", type="password")

        if st.button("Sign Up"):
            if new_pass != conf_pass:
                st.error("❌ Passwords do not match.")
            elif len(new_user.strip()) == 0 or len(new_pass.strip()) == 0:
                st.warning("⚠️ Please fill all fields.")
            else:
                if save_user(new_user, new_pass, new_email):
                    st.success("✅ Account created successfully! Please log in.")
                    st.session_state.page = "login"
                else:
                    st.error("⚠️ Username already exists. Try a different one.")

        if st.button("🔑 Go to Login"):
            st.session_state.page = "login"
        st.stop()

    elif st.session_state.page == "login":
        st.subheader("🔐 Login")
        username = st.text_input("👤 Username")
        password = st.text_input("🔑 Password", type="password")

        if st.button("Login"):
            if validate_user(username, password):
                st.session_state.authenticated = True
                st.session_state.username = username
                st.success(f"✅ Welcome, {username}!")
                time.sleep(1)
            else:
                st.error("❌ Invalid username or password.")

        if st.button("🆕 Create New Account"):
            st.session_state.page = "signup"
        st.stop()

# -------------------------
# MAIN APP
# -------------------------
st.sidebar.success(f"👋 Logged in as {st.session_state.username}")
st.sidebar.markdown("### 🔖 Navigation")
page = st.sidebar.radio("Select:", ["🏠 Home", "💬 Chat Assistant", "📷 Image Analysis", "🩸 Diabetes Prediction"])

# --- Header ---
st.markdown("""
<style>
@keyframes glow {
  0% { text-shadow: 0 0 5px #138808; }
  50% { text-shadow: 0 0 20px #00FF00; }
  100% { text-shadow: 0 0 5px #138808; }
}
h1 { animation: glow 2s infinite alternate; color: #138808; text-align:center; }
</style>
""", unsafe_allow_html=True)
st.markdown("<h1>💚 MediScan AI - Smart Health Assistant</h1>", unsafe_allow_html=True)

# -------------------------
# HOME PAGE
# -------------------------
if page == "🏠 Home":
    st.write("👋 Welcome to MediScan AI! Choose a feature from the sidebar.")
    st.markdown("""
    **Features:**
    - 💬 Multilingual Chatbot (English default, translation available)  
    - 📷 Image Analyzer (English default, translated output)  
    - 🩸 Diabetes risk prediction with age factor  
    """)

# -------------------------
# CHATBOT PAGE (EN + TRANSLATION)
# -------------------------
elif page == "💬 Chat Assistant":
    st.subheader("💬 Multilingual Medical Chatbot")
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "chat_lang" not in st.session_state:
        st.session_state.chat_lang = "English"

    col1, col2, col3 = st.columns(3)
    with col1:
        lang = st.selectbox("🌐 Choose Language", ["English","Telugu","Hindi","Tamil","Malayalam"], key="chat_lang_select")
    with col2:
        speak_btn = st.button("🔊 Speak Response")
    with col3:
        clear_btn = st.button("🛑 Clear Chat")

    if clear_btn:
        st.session_state.chat_history = []

    # Chat input
    user_input = st.text_input("💬 Ask a health question:", key="chat_input")

    if st.button("Send"):
        chat_model = genai.GenerativeModel(model_name="models/gemini-2.0-flash", generation_config=generation_config)
        with st.spinner("Thinking... 🤖"):
            # First, English response
            response = chat_model.generate_content([
                "You are a friendly medical assistant. Answer in English. Keep it safe and clear, no diagnosis.",
                user_input
            ])
            english_answer = response.text

            # If selected language is not English, translate
            if lang != "English":
                trans_response = chat_model.generate_content([
                    f"Translate the following English text into {lang} accurately for non-medical users:",
                    english_answer
                ])
                final_answer = trans_response.text
            else:
                final_answer = english_answer

        st.session_state.chat_history.append(("user", user_input))
        st.session_state.chat_history.append(("assistant", final_answer))
        st.session_state.chat_lang = lang

    # Display chat
    for role, msg in st.session_state.chat_history:
        if role=="user":
            st.info(f"🧑‍⚕️ You: {msg}")
        else:
            st.success(f"🤖 MediScan AI: {msg}")

    # Voice output
    if speak_btn and st.session_state.chat_history:
        last_msg = [msg for role, msg in st.session_state.chat_history if role=="assistant"][-1]
        tts = gTTS(last_msg, lang={"English":"en","Telugu":"te","Hindi":"hi","Tamil":"ta","Malayalam":"ml"}[st.session_state.chat_lang])
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            tts.save(fp.name)
            st.audio(open(fp.name,"rb").read(), format="audio/mp3")

# -------------------------
# IMAGE ANALYSIS PAGE (EN + TRANSLATION)
# -------------------------
elif page == "📷 Image Analysis":
    st.subheader("📷 Upload and Analyze Medical Image")

    col1, col2, col3 = st.columns(3)
    with col1:
        lang_img = st.selectbox("🌐 Choose Language", ["English","Telugu","Hindi","Tamil","Malayalam"], key="img_lang_select")
    with col2:
        speak_btn_img = st.button("🔊 Speak Analysis")
    with col3:
        clear_btn_img = st.button("🛑 Clear Result")

    if clear_btn_img:
        st.session_state.image_result = ""

    uploaded_file = st.file_uploader("📤 Choose a medical image...", type=["png","jpg","jpeg"])
    if uploaded_file and st.button("🔍 Analyze"):
        st.image(uploaded_file, use_column_width=True)
        model = genai.GenerativeModel(model_name="models/gemini-2.0-flash", generation_config=generation_config)
        with st.spinner("Analyzing image... 🧠"):
            image_data = {"mime_type": uploaded_file.type, "data": uploaded_file.getvalue()}
            # English description
            response = model.generate_content([
                "You are a medical assistant AI. Analyze this image and explain in English for non-medical users.",
                image_data
            ])
            english_result = response.text
            # Translate if needed
            if lang_img != "English":
                trans_resp = model.generate_content([
                    f"Translate the following English text into {lang_img}:",
                    english_result
                ])
                final_result = trans_resp.text
            else:
                final_result = english_result

            st.session_state.image_result = final_result
            st.success(final_result)

    if speak_btn_img and "image_result" in st.session_state and st.session_state.image_result:
        tts = gTTS(st.session_state.image_result, lang={"English":"en","Telugu":"te","Hindi":"hi","Tamil":"ta","Malayalam":"ml"}[lang_img])
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            tts.save(fp.name)
            st.audio(open(fp.name,"rb").read(), format="audio/mp3")

# -------------------------
# DIABETES PREDICTION
# -------------------------
elif page == "🩸 Diabetes Prediction":
    st.subheader("🩸 Check Your Diabetes Risk")
    age = st.number_input("Enter your age:", min_value=1, max_value=120, step=1)
    glu_val = st.number_input("Enter your glucometer reading (mg/dL):", min_value=0, step=1)

    if st.button("Predict"):
        if glu_val < 140:
            result = "Normal"
            suggestion = "Your sugar level is within normal range. Keep up a healthy lifestyle."
        elif 140 <= glu_val < 200:
            result = "Prediabetic"
            suggestion = "You may be prediabetic. Maintain diet and regular exercise."
        else:
            result = "Diabetic"
            suggestion = "High sugar levels detected. Consult a doctor."

        if age > 45 and result != "Normal":
            suggestion += " Age above 45 increases risk. Please be careful."

        st.markdown(f"### 🧠 Result: **{result}**")
        st.info(suggestion)

# -------------------------
# FOOTER
# -------------------------
st.markdown("---")
st.markdown("<p style='text-align:center;color:gray;'>Developed by <b>Pasumarthi Bhanu Prakash</b></p>", unsafe_allow_html=True)
