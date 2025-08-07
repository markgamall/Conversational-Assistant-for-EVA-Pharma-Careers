import streamlit as st
import sys
import os
from dotenv import load_dotenv

# Add the current directory to Python path to import from main.py
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the agent directly from main.py
try:
    from main import agent, prettify_text_for_postman
except ImportError as e:
    st.error(f"Error importing from main.py: {str(e)}")
    st.stop()

load_dotenv()

st.set_page_config(
    page_title="EVA Pharma Career Assistant",
    page_icon="💼",
    layout="wide"
)

st.title("EVA Pharma Career Assistant")
st.write(
    "Welcome to EVA Pharma's intelligent career assistant! I can help you explore job opportunities, "
    "compare positions, and find the perfect role for your career journey."
)

def create_tts_button(text: str, key: str):
    """Create a TTS button using browser's Web Speech API with play/stop toggle"""
    clean_text = text.replace("*", "").replace("#", "").replace("_", "").replace("\n", " ")
    
    js_code = f"""
    <script>
    let isPlaying_{key} = false;
    let currentUtterance_{key} = null;
    
    function toggleSpeech_{key}() {{
        const button = document.getElementById('tts_btn_{key}');
        
        if (isPlaying_{key}) {{
            window.speechSynthesis.cancel();
            isPlaying_{key} = false;
            button.innerHTML = '🔊';
            button.style.background = '#ff6b6b';
            button.title = 'Listen to response';
        }} else {{
            if ('speechSynthesis' in window) {{
                window.speechSynthesis.cancel();
                
                currentUtterance_{key} = new SpeechSynthesisUtterance(`{clean_text.replace('`', "'")}`);
                currentUtterance_{key}.rate = 0.9;
                currentUtterance_{key}.pitch = 1.0;
                currentUtterance_{key}.volume = 1.0;
                currentUtterance_{key}.lang = 'en-US';
                
                currentUtterance_{key}.onstart = function() {{
                    isPlaying_{key} = true;
                    button.innerHTML = '⏸️';
                    button.style.background = '#4CAF50';
                    button.title = 'Stop speaking';
                }};
                
                currentUtterance_{key}.onend = function() {{
                    isPlaying_{key} = false;
                    button.innerHTML = '🔊';
                    button.style.background = '#ff6b6b';
                    button.title = 'Listen to response';
                }};
                
                currentUtterance_{key}.onerror = function() {{
                    isPlaying_{key} = false;
                    button.innerHTML = '🔊';
                    button.style.background = '#ff6b6b';
                    button.title = 'Listen to response';
                }};
                
                window.speechSynthesis.speak(currentUtterance_{key});
            }} else {{
                alert('Text-to-speech not supported in this browser');
            }}
        }}
    }}
    </script>
    <button id="tts_btn_{key}" onclick="toggleSpeech_{key}()" style="
        background: #ff6b6b;
        color: white;
        border: none;
        padding: 5px 10px;
        border-radius: 5px;
        cursor: pointer;
        font-size: 14px;
        transition: background-color 0.3s;
    " title="Listen to response">🔊</button>
    """
    
    return js_code

if "messages" not in st.session_state:
    st.session_state.messages = []
    welcome_message = {
        "role": "assistant", 
        "content": """Hello! I'm here to help you explore career opportunities at EVA Pharma. You can ask me about:

- Available job positions
- Job requirements and qualifications  
- Positions in specific locations
- Comparing different roles
- Summary of job descriptions

What would you like to know?"""
    }
    st.session_state.messages.append(welcome_message)

st.subheader("Quick Questions")
col1, col2, col3 = st.columns(3)

predefined_messages = [
    "What jobs are available right now?",     
    "Show me jobs in my city or region.",            
    "What do I need to apply for these jobs?",        
    "Are there remote jobs available?",              
    "What are the potential career advancement opportunities and progression paths?",
    "Can you recommend positions aligned with my qualifications and background?"
]

with col1:
    if st.button("🔍 Explore Jobs"):
        st.session_state.selected_message = predefined_messages[0]
    if st.button("📍 Jobs Near Me"):
        st.session_state.selected_message = predefined_messages[1]

with col2:
    if st.button("📋 What You Need"):
        st.session_state.selected_message = predefined_messages[2]
    if st.button("🏡 Remote Jobs"):
        st.session_state.selected_message = predefined_messages[3]
with col3:
    if st.button("🔄 Career Growth"):
        st.session_state.selected_message = predefined_messages[4]
    if st.button("🎯 Job Match"):
        st.session_state.selected_message = predefined_messages[5]


def get_chatbot_response(query):
    """
    Directly call the agent logic instead of making HTTP requests
    """
    try:
        # Check if agent is available
        if not agent:
            return "❌ **Error**: Agent not initialized. Please check your environment variables."
        
        # Create the initial state similar to Flask app
        initial_state = {
            "messages": [{
                "role": "user",
                "content": query
            }]
        }
        
        # Configure the agent
        config = {"configurable": {"thread_id": "streamlit_session"}}
        
        # Invoke the agent
        result = agent.invoke(initial_state, config)
        messages = result.get("messages", [])

        # Extract the response similar to Flask app logic
        if messages:
            # First try to find assistant messages
            for msg in reversed(messages):
                if isinstance(msg, dict) and msg.get("role") == "assistant":
                    content = msg.get("content", "")
                    if content and content.strip():
                        return content
            
            # Fallback to any non-user message
            for msg in reversed(messages):
                if isinstance(msg, dict):
                    content = msg.get("content", "")
                    if content and content.strip() and msg.get("role") != "user":
                        return content
        
        return "Sorry, I couldn't generate a response. Please try again."
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error in get_chatbot_response: {str(e)}")
        print(f"Full traceback: {error_details}")
        
        # Check for common issues
        if "GOOGLE_API_KEY" in str(e) or "API key" in str(e):
            return "❌ **API Key Error**: Please make sure your GOOGLE_API_KEY is properly set in your environment variables."
        elif "agents.langgraph_agent" in str(e):
            return "❌ **Import Error**: Unable to load the agent. Please make sure all required files are present."
        else:
            return f"❌ **Error**: {str(e)}"


st.subheader("Chat")
for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        if message["role"] == "assistant":
            col1, col2 = st.columns([1, 10])
            with col1:
                tts_html = create_tts_button(message["content"], f"msg_{i}")
                st.components.v1.html(tts_html, height=40)


chat_placeholder = "Type your question here or use the quick questions above..."

if "selected_message" in st.session_state:
    default_value = st.session_state.selected_message
    del st.session_state.selected_message  
else:
    default_value = ""

if prompt := st.chat_input(chat_placeholder):
    user_message = prompt
elif default_value:
    user_message = default_value
else:
    user_message = None

if user_message:
    st.session_state.messages.append({"role": "user", "content": user_message})

    with st.chat_message("user"):
        st.markdown(user_message)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = get_chatbot_response(user_message)
        st.markdown(response)
        
        col1, col2 = st.columns([1, 10])
        with col1:
            tts_html = create_tts_button(response, "new_msg")
            st.components.v1.html(tts_html, height=40)

    st.session_state.messages.append({"role": "assistant", "content": response})
    
    if default_value:
        st.rerun()

