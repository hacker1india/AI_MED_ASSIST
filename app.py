import streamlit as st
import pandas as pd
import os
import hashlib
import google.generativeai as genai
from gtts import gTTS
import time
import tempfile

# -------------------------
# BASIC CONFIGURATION
# -------------------------
st.set_page_config(page_title="💚 MediScan AI", layout="wide")

api_key = "YOUR_API_KEY"  # Replace with your Gemini API key
genai.configure(api_key=api_key)

generation_config = {
    "temperature": 0.7,
    "top_p": 1,
    "top_k": 50,
    "max_output_tokens": 4096,
}

# -------------------------
# SESSION STATE INITIALIZATION
# -------------------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "page" not in st.session_state:
    st.session_state.page = "login"
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "last_lang" not in st.session_state:
    st.session_state.last_lang = "English"
if "image_result" not in st.session_state:
    st.session_state.image_result = ""

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
# LOGIN / SIGNUP PAGE
# -------------------------
if not st.session_state.authenticated:
    st.title("💚 MediScan AI - Smart Health Assistant")
    st.markdown("### Login or Sign Up to continue")

    if st.session_state.page == "signup":
        st.subheader("📝 Create Account")
        new_user = st.text_input("👤 Username", key="signup_user")
        new_email = st.text_input("📧 Email", key="signup_email")
        new_pass = st.text_input("🔑 Password", type="password", key="signup_pass")
        conf_pass = st.text_input("✅ Confirm Password", type="password", key="signup_conf")

        if st.button("Sign Up", key="signup_btn"):
            if new_pass != conf_pass:
                st.error("❌ Passwords do not match.")
            elif len(new_user.strip()) == 0 or len(new_pass.strip()) == 0:
                st.warning("⚠️ Please fill all fields.")
            else:
                if save_user(new_user, new_pass, new_email):
                    st.success("✅ Account created successfully! Please log in.")
                    st.session_state.page = "login"
                    st.experimental_rerun()
                else:
                    st.error("⚠️ Username already exists.")

        if st.button("🔑 Go to Login", key="signup_login"):
            st.session_state.page = "login"
            st.experimental_rerun()
        st.stop()

    elif st.session_state.page == "login":
        st.subheader("🔐 Login")
        username = st.text_input("👤 Username", key="login_user")
        password = st.text_input("🔑 Password", type="password", key="login_pass")

        if st.button("Login", key="login_btn"):
            if validate_user(username, password):
                st.session_state.authenticated = True
                st.session_state.username = username
                st.success(f"✅ Welcome, {username}!")
                time.sleep(1)
                st.experimental_rerun()
            else:
                st.error("❌ Invalid username or password.")

        if st.button("🆕 Create New Account", key="login_signup"):
            st.session_state.page = "signup"
            st.experimental_rerun()
        st.stop()

# -------------------------
# MAIN APP
# -------------------------
st.sidebar.success(f"👋 Logged in as {st.session_state.username}")
st.sidebar.markdown("### 🔖 Navigation")
page = st.sidebar.radio("Select:", ["🏠 Home", "💬 Chat Assistant", "📷 Image Analysis", "🩸 Diabetes Prediction"])

st.markdown("""
<style>
@keyframes glow {
  0% { text-shadow: 0 0 5px #138808; }
  50% { text-shadow: 0 0 20px #00FF00; }
  100% { text-shadow: 0 0 5px #138808; }
}
h1 {
  animation: glow 2s infinite alternate;
  color: #138808;
  text-align:center;
}
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
    - 💬 Multilingual Chatbot with voice & stop  
    - 📷 Image Analyzer with multilingual AI explanations  
    - 🩸 Diabetes risk prediction with age factor  
    """)

# -------------------------
# CHATBOT PAGE
# -------------------------
elif page == "💬 Chat Assistant":
    st.subheader("💬 Multilingual Medical Chatbot")

    col1, col2, col3 = st.columns([3,1,1])
    with col1:
        lang = st.selectbox("🌐 Choose Language", ["English", "Telugu", "Hindi", "Tamil", "Malayalam"], key="chat_lang")
    with col2:
        speak_btn = st.button("🔊 Speak Response", key="chat_speak")
    with col3:
        clear_btn = st.button("🛑 Clear Chat", key="chat_clear")

    if clear_btn:
        st.session_state.chat_history = []
        st.experimental_rerun()

    user_input = st.text_input("💬 Ask a health question:", key="chat_input")

    if st.button("Send", key="chat_send") and user_input.strip():
        chat_model = genai.GenerativeModel(model_name="gemini-2.0-flash", generation_config=generation_config)
        with st.spinner("Thinking... 🤖"):
            try:
                response = chat_model.generate_content([
                    f"You are a multilingual medical assistant. Reply in {lang}. Keep it friendly, safe, and helpful. Avoid diagnosis.",
                    user_input
                ])
                answer = response.text
            except Exception as e:
                answer = f"⚠️ AI Error: {e}"

        # Replace English answer if language is selected
        if lang != "English":
            st.session_state.last_lang = lang
        st.session_state.chat_history.append(("user", user_input))
        st.session_state.chat_history.append(("assistant", answer))
        st.experimental_rerun()

    # Display chat
    for role, msg in st.session_state.chat_history:
        if role == "user":
            st.info(f"🧑‍⚕️ You: {msg}")
        else:
            st.success(f"🤖 MediScan AI: {msg}")

    # Speak last message
    if speak_btn and st.session_state.chat_history:
        last_msg = [msg for role, msg in st.session_state.chat_history if role=="assistant"][-1]
        tts = gTTS(last_msg, lang={"English":"en","Telugu":"te","Hindi":"hi","Tamil":"ta","Malayalam":"ml"}[lang])
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            tts.save(fp.name)
            st.audio(fp.name, format="audio/mp3")

# -------------------------
# IMAGE ANALYSIS PAGE
# -------------------------
elif page == "📷 Image Analysis":
    st.subheader("📷 Upload and Analyze Medical Image")

    col1, col2, col3 = st.columns([3,1,1])
    with col1:
        img_lang = st.selectbox("🌐 Choose Language", ["English","Telugu","Hindi","Tamil","Malayalam"], key="img_lang")
    with col2:
        img_speak_btn = st.button("🔊 Speak Analysis", key="img_speak")
    with col3:
        img_clear_btn = st.button("🛑 Clear Result", key="img_clear")

    if img_clear_btn:
        st.session_state.image_result = ""
        st.experimental_rerun()

    uploaded_file = st.file_uploader("📤 Choose a medical image...", type=["png","jpg","jpeg"], key="img_upload")

    if uploaded_file and st.button("🔍 Analyze", key="img_analyze"):
        st.image(uploaded_file, use_column_width=True)
        model = genai.GenerativeModel(model_name="gemini-2.0-flash", generation_config=generation_config)
        with st.spinner("Analyzing image... 🧠"):
            try:
                image_data = {"mime_type": uploaded_file.type, "data": uploaded_file.getvalue()}
                response = model.generate_content([
                    f"You are a multilingual medical assistant. Explain this medical image in {img_lang}. Give safe, simple advice.",
                    image_data
                ])
                st.session_state.image_result = response.text
                st.success(st.session_state.image_result)
            except Exception as e:
                st.error(f"⚠️ AI Error: {e}")

    if img_speak_btn and st.session_state.image_result:
        tts = gTTS(st.session_state.image_result, lang={"English":"en","Telugu":"te","Hindi":"hi","Tamil":"ta","Malayalam":"ml"}[img_lang])
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            tts.save(fp.name)
            st.audio(fp.name, format="audio/mp3")

# -------------------------
# DIABETES PREDICTION PAGE
# -------------------------
elif page == "🩸 Diabetes Prediction":
    st.subheader("🩸 Check Your Diabetes Risk")
    age = st.number_input("Enter your age:", min_value=1, max_value=120, step=1, key="age_input")
    glu_val = st.number_input("Enter your glucometer reading (mg/dL):", min_value=0, step=1, key="glu_input")

    if st.button("Predict", key="predict_btn"):
        if glu_val < 140:
            result = "Normal"
            suggestion = "Your sugar level is within the normal range. Maintain a healthy lifestyle."
        elif 140 <= glu_val < 200:
            result = "Prediabetic"
            suggestion = "You may be prediabetic. Watch diet and exercise."
        else:
            result = "Diabetic"
            suggestion = "High sugar levels detected. Consult a doctor."

        if age > 45 and result != "Normal":
            suggestion += " Age above 45 increases risk. Please take care."

        st.markdown(f"### 🧠 Result: **{result}**")
        st.info(suggestion)

# -------------------------
# FOOTER
# -------------------------
st.markdown("---")
st.markdown("<p style='text-align:center;color:gray;'>Developed by <b>Pasumarthi Bhanu Prakash</b></p>", unsafe_allow_html=True)
