import streamlit as st
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import requests
import json

# ========== SETTING UP OCR ==========
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# ========== API CONFIGURATION ==========
st.sidebar.subheader("🔑 Enter Your Groq API Key")
api_key = st.sidebar.text_input("API Key:", type="password")

if not api_key:
    st.warning("Please enter your Groq API Key to use the chatbot.")
    st.stop()

# Initialize session state for chat history and persistent responses
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []  # ✅ Stores conversation history

if "solution" not in st.session_state:
    st.session_state.solution = None  # ✅ Store the generated solution

if "hint" not in st.session_state:
    st.session_state.hint = None  # ✅ Store the generated hint

if "answer_feedback" not in st.session_state:
    st.session_state.answer_feedback = None  # ✅ Store the answer checking feedback

# Function to call the Groq API
def query_groq_api(prompt, history):
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    data = {
        "messages": history + [{"role": "user", "content": prompt}],  # ✅ Adds history for context
        "model": "llama3-8b-8192"
    }

    try:
        response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data)
        if response.status_code == 200:
            reply = response.json()["choices"][0]["message"]["content"]
            history.append({"role": "assistant", "content": reply})  # ✅ Add AI response to history
            return reply
        else:
            return f"Error: {response.json()}"
    except Exception as e:
        return f"API Request Failed: {str(e)}"

# ========== TITLE ==========
st.title("🧮 AI-Powered Math Tutor")

# ========== IMAGE UPLOAD & OCR ==========
st.subheader("Upload a math problem image")
uploaded_file = st.file_uploader("Drag and drop file here", type=["png", "jpg", "jpeg"])

def preprocess_image(image):
    """Enhance image for better OCR accuracy"""
    image = image.convert("L")  # Convert to grayscale
    image = image.filter(ImageFilter.MedianFilter())  # Remove noise
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2)  # Increase contrast
    return image

extracted_text = ""

if uploaded_file is not None:
    st.image(uploaded_file, caption="Uploaded Image")
    try:
        img = Image.open(uploaded_file)
        img = preprocess_image(img)
        extracted_text = pytesseract.image_to_string(img, config="--psm 6").strip()
        if extracted_text:
            st.success("✅ Math Problem Extracted from Image (Not added to text area)")
            
        else:
            st.error("❌ Could not extract readable text. Try uploading a clearer image.")
    except Exception as e:
        st.error(f"❌ OCR Extraction Failed: {str(e)}")

# ========== MANUAL INPUT ==========
st.subheader("Enter your math question (if not uploaded):")
math_question = st.text_area("Type your question here (Manual Entry):")

# Ensure extracted text is NOT put in the text area
final_question = math_question.strip() if math_question.strip() else extracted_text  # ✅ FIXED

# ========== SHOW SOLUTION ==========
if st.button("Show Solution"):
    if final_question:
        prompt = f"""
        You are a **math expert tutor** helping a student. The student has asked for a **step-by-step solution** for the following math problem:

        **Problem:** {final_question}

        ✅ **Instructions:**
        - **Break down the solution into clear logical steps.**
        - **Explain every mathematical operation.**
        - If relevant, **mention multiple methods** to solve the problem.
        - Make the explanation **interactive** by suggesting what the student should think about at each step.

        Provide an **expert-level detailed solution** with explanations that a student can easily understand.
        """
        st.session_state.solution = query_groq_api(prompt, st.session_state.chat_history)
        st.session_state.chat_history.append({"role": "user", "content": f"Problem: {final_question}"})  # ✅ Store problem
        st.session_state.chat_history.append({"role": "assistant", "content": st.session_state.solution})  # ✅ Store solution

# Display the stored solution
if st.session_state.solution:
    st.subheader("📝 Solution:")
    st.write(st.session_state.solution)

# ========== GENERATE HINT ==========
if st.button("Generate Hint"):
    if final_question:
        prompt = f"""
        You are a **friendly and engaging math tutor**. A student is solving the following problem:

        **Problem:** {final_question}

        ✅ **Instructions:**
        - **Do NOT provide the full solution.**
        - Instead, **give a logical hint** to **guide the student towards solving it.**
        - If applicable, **suggest a formula or concept they should use.**
        - Ask **leading questions** to help them think critically.
        - Keep the response **encouraging and motivational**.

        Provide a useful **hint without revealing the answer**.
        """
        st.session_state.hint = query_groq_api(prompt, st.session_state.chat_history)

# Display the stored hint
if st.session_state.hint:
    st.subheader("💡 Hint:")
    st.write(st.session_state.hint)

# ========== CHECK ANSWER ==========
user_answer = st.text_input("Enter your answer:")
if st.button("Check Answer"):
    if final_question and user_answer.strip():
        prompt = f"""
        You are an **interactive math tutor** helping a student. They attempted to solve this problem:

        **Question:** {final_question}  
        **Student's Answer:** {user_answer}

        ✅ **Instructions:**
        - First, **check if the student's answer is correct**.
        - If the answer is **correct**, praise them and reinforce their understanding.
        - If the answer is **wrong**, do NOT just say "wrong." Instead:
          - **Find the mistake.**
          - **Explain why it is incorrect.**
          - Guide the student towards the **correct answer** without giving it away.
        - If the answer is **partially correct**, acknowledge the correct part and guide them to fix the mistake.
        - Ask if the student wants to **retry or see the full solution**.

        Provide **constructive, engaging, and logical feedback**.
        """
        st.session_state.answer_feedback = query_groq_api(prompt, st.session_state.chat_history)

# Display the stored answer feedback
if st.session_state.answer_feedback:
    st.subheader("✅ Answer Feedback:")
    st.write(st.session_state.answer_feedback)

# ========== CHAT SECTION ==========
st.subheader("💬 Chat with AI Tutor")
chat_input = st.text_input("Ask follow-up questions:")

if st.button("Send"):
    if chat_input.strip():
        chat_response = query_groq_api(chat_input, st.session_state.chat_history)
        st.session_state.chat_history.append({"role": "user", "content": chat_input})
        st.session_state.chat_history.append({"role": "assistant", "content": chat_response})
        st.subheader("🗨️ AI Response:")
        st.write(chat_response)
