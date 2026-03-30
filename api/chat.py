import os
import requests
import base64
from flask import Flask, request, jsonify
from flask_cors import CORS
from groq import Groq

app = Flask(__name__)
CORS(app)

def get_groq_client():
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY is missing from Vercel Environment Variables!")
    return Groq(api_key=api_key)

def generate_elevenlabs_audio(text):
    eleven_key = os.environ.get("ELEVEN_API_KEY")
    if not eleven_key:
        return None
        
    # Allows user to set their exact preferred Voice ID from ElevenLabs Voice Library
    # Defaulting to Adam if no custom ID is provided
    voice_id = os.environ.get("ELEVEN_VOICE_ID", "pNInz6obpgDQGcFmaJcg") 
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": eleven_key
    }
    
    data = {
        "text": text,
        "model_id": "eleven_turbo_v2_5", # THE "TOP VERSION": Zero latency, flawless Hindi & English
        "voice_settings": {
            "stability": 0.45,
            "similarity_boost": 0.85
        }
    }
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=10) # 10s max for vercel limits
        if (response.status_code == 200):
            # Encode mp3 audio buffer into base64 for instant frontend playback
            return base64.b64encode(response.content).decode('utf-8')
    except Exception as e:
        print(f"ElevenLabs TTS Error: {str(e)}")
        
    return None

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({'reply': 'Empty message received.'}), 400
        
    user_message = data['message']
    usr_context = data.get('context', {})
    c_time = usr_context.get('time', 'Unknown Time')
    c_date = usr_context.get('date', 'Unknown Date')
    c_loc = usr_context.get('location', 'Unknown Location')
    
    try:
        client = get_groq_client()
        
        base_prompt = f"""You are Jarvis, an incredibly smart, highly concise, and highly professional AI assistant developed by Aman Dhaka (an aspiring AI Software Developer / Vibe coder). 
Your responses must be directly under 2-3 short sentences. Speak in very clear, fluent, conversational language. You can respond in English or a stylish Hinglish depending on what the user speaks.

CURRENT USER CONTEXT:
- Local Time: {c_time}
- Current Date: {c_date}
- Approximate Location: {c_loc}

Use this context ONLY if relevant to the user's prompt (e.g. if they ask the time, or location). Do not blindly announce or repeat the location unless asked."""
        
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": base_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=150,
            top_p=1,
            stream=False
        )
        
        response_text = completion.choices[0].message.content
        
        # Parallel Audio Processing Magic
        audio_payload = generate_elevenlabs_audio(response_text)
        
        return jsonify({
            'reply': response_text,
            'audioBase64': audio_payload
        })
        
    except Exception as e:
        print(f"Groq API Error: {str(e)}")
        return jsonify({'reply': f'Vercel Backend Error: {str(e)}'}), 500
