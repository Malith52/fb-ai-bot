import os
import requests
from flask import Flask, request, jsonify
import google.generativeai as genai

app = Flask(__name__)

# Environment Variables වලින් Tokens ලබාගැනීම
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "my_custom_verify_token_123")
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Gemini AI Configure කිරීම
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

@app.route('/', methods=['GET'])
def home():
    return "Facebook Messenger AI Bot is Running Successfully!", 200

# 1. Facebook Webhook Verification (Meta Verification සඳහා)
@app.route('/webhook', methods=['GET'])
def verify_webhook():
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')

    if mode and token:
        if mode == 'subscribe' and token == VERIFY_TOKEN:
            print("WEBHOOK_VERIFIED")
            return challenge, 200
        else:
            return "Verification failed", 403
    return "Missing parameters", 400

# 2. Incoming Messages Handle කිරීම
@app.route('/webhook', methods=['POST'])
def webhook_event():
    data = request.get_json()

    if data.get("object") == "page":
        for entry in data.get("entry", []):
            for messaging_event in entry.get("messaging", []):
                sender_id = messaging_event.get("sender", {}).get("id")
                
                # Message එකක් පැමිණ ඇත්නම් පමණක්
                if messaging_event.get("message") and "text" in messaging_event["message"]:
                    user_message = messaging_event["message"]["text"]
                    print(f"User ({sender_id}): {user_message}")

                    # Gemini හරහා පිළිතුර සකසා ගැනීම
                    ai_response = get_gemini_response(user_message)

                    # පිළිතුර Facebook Messenger වෙත යැවීම
                    send_facebook_message(sender_id, ai_response)

        return "EVENT_RECEIVED", 200
    else:
        return "Not Found", 404

# Gemini AI එකෙන් පිළිතුර ලබාගන්නා function එක
def get_gemini_response(user_text):
    try:
        # AI එක හැසිරිය යුතු ආකාරය (System Prompt)
        prompt = f"You are a helpful customer support assistant for a Facebook Page. Reply politely and concisely in Sinhala or English based on the user's input.\n\nUser: {user_text}\nAssistant:"
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Gemini Error: {e}")
        return "ස්තූතියි පණිවිඩයට! මොහොතකින් ඔබට පිළිතුරක් ලබා දෙන්නම්."

# Facebook Graph API හරහා Message එකක් යවන function එක
def send_facebook_message(recipient_id, response_text):
    url = f"https://graph.facebook.com/v19.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": response_text}
    }
    headers = {"Content-Type": "application/json"}
    
    res = requests.post(url, json=payload, headers=headers)
    if res.status_code != 200:
        print(f"Message Send Failed: {res.text}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))

