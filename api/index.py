from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from groq import Groq
import os
from dotenv import load_dotenv

# Load local environment variables (useful for local testing)
load_dotenv()

# Vercel requires the app variable to be clearly defined
app = Flask(__name__)
# Enable CORS so the frontend html can securely call this API
CORS(app)

# Explicitly serve the frontend HTML if Vercel misroutes the root to Flask
@app.route('/')
def serve_index():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    index_path = os.path.join(base_dir, 'index.html')
    try:
        with open(index_path, 'r', encoding='utf-8') as f:
            return Response(f.read(), mimetype='text/html')
    except Exception as e:
        return f"Error loading UI: {e}"

# The Groq API connection
def get_groq_client():
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("API Key is missing!")
    return Groq(api_key=api_key)

# The single endpoint our frontend will call
@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({'reply': 'Empty message received.'}), 400
        
    user_message = data['message']
    
    try:
        client = get_groq_client()
        
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful, smart, and concise AI voice assistant named Jarvis. Always reply in exactly 1 or 2 short sentences because your answers will be spoken out loud."
                },
                {
                    "role": "user",
                    "content": user_message,
                }
            ],
            # Use the active available Llama 3 model
            model="llama-3.1-8b-instant",
            temperature=0.7,
            max_tokens=150,
        )
        
        response_text = chat_completion.choices[0].message.content
        return jsonify({'reply': response_text})
        
    except Exception as e:
        print(f"Error communicating with Brain: {e}")
        return jsonify({'reply': 'Sorry, the brain module encountered an API error.'}), 500

# This allows running the server locally for testing Phase 4
if __name__ == '__main__':
    app.run(debug=True, port=5000)
