import streamlit as st
import pandas as pd
import os
import hashlib
import google.generativeai as genai
from gtts import gTTS
import time
import tempfile

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

USER_DB = "users.csv"

# -------------------------
# AUTH FUNCTIONS
# -------------------------
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
            elif len(new_user.strip())==0 or len(new_pass.strip())==0:
                st.warning("⚠️ Fill all fields")
            else:
                if save_user(new_user, new_pass, new_email):
                    st.success("✅ Account created! Please log in.")
                    st.session_state.page = "login"
                    st.experimental_rerun()
                else:
                    st.error("⚠️ Username exists. Try another.")

        if st.button("🔑 Go to Login"):
            st.session_state.page = "login"
            st.experimental_rerun()
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
                st.experimental_rerun()
            else:
                st.error("❌ Invalid username or password.")

        if st.button("🆕 Create New Account"):
            st.session_state.page = "signup"
            st.experimental_rerun()
        st.stop()

# -------------------------
# MAIN APP
# -------------------------
st.sidebar.success(f"👋 Logged in as {st.session_state.username}")
st.sidebar.markdown("### 🔖 Navigation")
page = st.sidebar.radio("Select:", ["🏠 Home","💬 Chat Assistant","📷 Image Analysis","🩸 Diabetes Prediction"])

# --- GLOW ANIMATION ---
st.markdown("""
<style>
@keyframes glow {
  0% { text-shadow: 0 0 5px #138808; }
  50% { text-shadow: 0 0 20px #00FF00; }
  100% { text-shadow: 0 0 5px #138808; }
}
h1 {animation: glow 2s infinite alternate;color:#138808;text-align:center;}
</style>
""", unsafe_allow_html=True)
st.markdown("<h1>💚 MediScan AI - Smart Health Assistant</h1>", unsafe_allow_html=True)

# -------------------------
# HOME
# -------------------------
if page=="🏠 Home":
    st.write("👋 Welcome! Use the sidebar to navigate.")
    st.markdown("""
    **Features:**
    - 💬 Multilingual Chatbot with voice & stop  
    - 📷 Image Analyzer with multilingual AI explanations  
    - 🩸 Diabetes risk prediction with age factor  
    """)

# -------------------------
# CHATBOT (Multilingual + Dynamic)
# -------------------------
elif page=="💬 Chat Assistant":
    st.subheader("💬 Multilingual Medical Chatbot")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "last_lang" not in st.session_state:
        st.session_state.last_lang = "English"

    col1, col2, col3 = st.columns([2,1,1])
    with col1:
        lang = st.selectbox("🌐 Language", ["English","Telugu","Hindi","Tamil","Malayalam"], key="chat_lang")
    with col2:
        speak_btn = st.button("🔊 Speak Response")
    with col3:
        clear_btn = st.button("🛑 Clear Chat")

    if clear_btn:
        st.session_state.chat_history=[]
        st.experimental_rerun()

    user_input = st.text_input("💬 Ask a health question:")

    if st.button("Send") and user_input.strip() != "":
        chat_model = genai.GenerativeModel(model_name="models/gemini-2.0-flash",
                                           generation_config=generation_config)
        prompt = f"You are a multilingual medical assistant. Respond in {lang} with bullet points or numbered steps. Safe advice, no diagnosis."
        with st.spinner("Thinking... 🤖"):
            response = chat_model.generate_content([prompt, user_input])
        answer = response.text
        st.session_state.chat_history.append(("user", user_input))
        st.session_state.chat_history.append(("assistant", answer))
        st.session_state.last_lang = lang
        st.experimental_rerun()

    # Render chat
    for role,msg in st.session_state.chat_history:
        if role=="user":
            st.info(f"🧑‍⚕️ You: {msg}")
        else:
            st.success(f"🤖 MediScan AI: {msg}")

    # Dynamic translation
    if st.session_state.chat_history:
        last_index = max(i for i,(r,_) in enumerate(st.session_state.chat_history) if r=="assistant")
        if lang != st.session_state.last_lang:
            chat_model = genai.GenerativeModel(model_name="models/gemini-2.0-flash",
                                               generation_config=generation_config)
            with st.spinner(f"Translating to {lang}... 🌐"):
                translation_prompt = f"Translate this medical response to {lang}, keep bullet points or numbered steps:\n\n"
                response = chat_model.generate_content([translation_prompt, st.session_state.chat_history[last_index][1]])
            st.session_state.chat_history[last_index] = ("assistant", response.text)
            st.session_state.last_lang = lang
            st.experimental_rerun()

    # Speech
    if speak_btn and st.session_state.chat_history:
        last_msg = [msg for r,msg in st.session_state.chat_history if r=="assistant"][-1]
        tts = gTTS(last_msg, lang={"English":"en","Telugu":"te","Hindi":"hi","Tamil":"ta","Malayalam":"ml"}[lang])
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            tts.save(fp.name)
            st.audio(open(fp.name,"rb").read(), format="audio/mp3")

# -------------------------
# IMAGE ANALYSIS (Multilingual + Voice)
# -------------------------
elif page=="📷 Image Analysis":
    st.subheader("📷 Upload and Analyze Medical Image")
    col1, col2, col3 = st.columns([2,1,1])
    with col1:
        lang = st.selectbox("🌐 Language", ["English","Telugu","Hindi","Tamil","Malayalam"], key="img_lang")
    with col2:
        speak_btn = st.button("🔊 Speak Analysis")
    with col3:
        clear_btn = st.button("🛑 Clear Result")

    if clear_btn:
        if "image_result" in st.session_state:
            st.session_state.image_result=""
        st.experimental_rerun()

    uploaded_file = st.file_uploader("📤 Choose a medical image...", type=["png","jpg","jpeg"])
    if uploaded_file and st.button("🔍 Analyze"):
        st.image(uploaded_file, use_column_width=True)
        model = genai.GenerativeModel(model_name="models/gemini-2.0-flash",
                                      generation_config=generation_config)
        with st.spinner("Analyzing image... 🧠"):
            image_data = {"mime_type": uploaded_file.type, "data": uploaded_file.getvalue()}
            response = model.generate_content([f"Explain this medical image in {lang} simply.", image_data])
        st.session_state.image_result = response.text
        st.success(st.session_state.image_result)

    if speak_btn and "image_result" in st.session_state and st.session_state.image_result:
        tts = gTTS(st.session_state.image_result,
                   lang={"English":"en","Telugu":"te","Hindi":"hi","Tamil":"ta","Malayalam":"ml"}[lang])
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            tts.save(fp.name)
            st.audio(open(fp.name,"rb").read(), format="audio/mp3")

# -------------------------
# DIABETES PREDICTION
# -------------------------
elif page=="🩸 Diabetes Prediction":
    st.subheader("🩸 Diabetes Risk Prediction")
    age = st.number_input("Enter age:", min_value=1, max_value=120, step=1)
    glu_val = st.number_input("Glucometer reading (mg/dL):", min_value=0, step=1)
    if st.button("Predict"):
        if glu_val < 140:
            result="Normal"
            suggestion="Sugar level is normal. Maintain a healthy lifestyle."
        elif 140 <= glu_val <200:
            result="Prediabetic"
            suggestion="Prediabetic range. Control diet and exercise."
        else:
            result="Diabetic"
            suggestion="High sugar detected. Consult a doctor."
        if age>45 and result!="Normal":
            suggestion+=" Age above 45 increases risk."
        st.markdown(f"### 🧠 Result: **{result}**")
        st.info(suggestion)

# -------------------------
# FOOTER
# -------------------------
st.markdown("---")
st.markdown("<p style='text-align:center;color:gray;'>Developed by <b>Pasumarthi Bhanu Prakash</b></p>", unsafe_allow_html=True)
