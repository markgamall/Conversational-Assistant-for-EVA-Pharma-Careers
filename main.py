import re
import os
from flask import Flask, request, jsonify
from agents.langgraph_agent import get_agent
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

agent = get_agent()

def prettify_text_for_postman(content: str) -> str:
    """
    Cleans and converts markdown-like text into plain readable text for Postman.
    - Removes markdown symbols (**, *, etc.)
    - Converts line breaks properly.
    """
    content = content.strip()
    content = content.replace('\\n', '\n')  
    content = content.replace('\r\n', '\n')
    content = re.sub(r'\*\*(.*?)\*\*', r'\1', content)  
    content = re.sub(r'\*(.*?)\*', r'\1', content)    
    content = re.sub(r'^[-*]\s+', '• ', content, flags=re.MULTILINE)  
    return content

@app.route('/query', methods=['POST'])
def handle_query():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
            
        query = data.get('query', '')
        if not query:
            return jsonify({"error": "No query provided"}), 400
        
        initial_state = {
            "messages": [{
                "role": "user",
                "content": query
            }]
        }
        
        config = {"configurable": {"thread_id": "main_session"}}
        
        result = agent.invoke(initial_state, config)
        messages = result.get("messages", [])

        print("All messages:")
        for i, msg in enumerate(messages):
            print(f"Message {i}: {msg}")
        
        if messages:
            for msg in reversed(messages):
                if isinstance(msg, dict) and msg.get("role") == "assistant":
                    content = msg.get("content", "")
                    if content and content.strip():
                        return jsonify({"response": content})
            
            for msg in reversed(messages):
                if isinstance(msg, dict):
                    content = msg.get("content", "")
                    if content and content.strip() and msg.get("role") != "user":
                        return jsonify({"response": content})
        
        return jsonify({
            "error": "No response generated",
            "debug": {
                "total_messages": len(messages),
                "message_roles": [msg.get("role", "unknown") if isinstance(msg, dict) else type(msg).__name__ for msg in messages],
                "last_message": messages[-1] if messages else None
            }
        }), 200
        
    except Exception as e:
        print(f"Error in handle_query: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"})


if __name__ == '__main__':
    if not os.getenv("GOOGLE_API_KEY"):
        print("Warning: GOOGLE_API_KEY not found in environment variables")
    
    app.run(debug=True, host='0.0.0.0', port=5000)