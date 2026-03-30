from flask import Flask, request, jsonify
from flask_cors import CORS
from groq import Groq
import os

app = Flask(__name__)
CORS(app)

def get_groq_client():
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY is missing from Vercel Environment Variables!")
    return Groq(api_key=api_key)

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
                    "content": "You are a helpful, smart, and concise AI voice assistant named Jarvis. Always reply in exactly 1 or 2 short sentences."
                },
                {
                    "role": "user",
                    "content": user_message,
                }
            ],
            model="llama-3.1-8b-instant",
            temperature=0.7,
            max_tokens=150,
        )
        
        response_text = chat_completion.choices[0].message.content
        return jsonify({'reply': response_text})
        
    except Exception as e:
        print(f"Groq API Error: {e}")
        return jsonify({'reply': 'Vercel Backend Error: Could not connect to Groq Brain.'}), 500
