from fastapi import FastAPI, Request
from twilio.twiml.voice_response import VoiceResponse
import openai, os
from dotenv import load_dotenv

from app.prompts import SYSTEM_PROMPT
from app.utils import is_working_hours

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()

@app.post("/voice")
async def voice():
    print(">>> Incoming call hit /voice <<<")
    vr = VoiceResponse()
    
async def voice():
    vr = VoiceResponse()


    vr.say(
        "Hi, I am Debanjan Bhowmick. "
        "I’m unavailable right now, so my assistant is speaking on my behalf. "
        "Please go ahead.",
        voice="alice"
    )
    vr.gather(input="speech", action="/process", timeout=6)
    return str(vr)

@app.post("/process")
async def process(request: Request):
    form = await request.form()
    user_input = form.get("SpeechResult", "").strip()

    vr = VoiceResponse()

    if not user_input:
        vr.say("Just checking. Please let me know how I can help.", voice="alice")
        vr.gather(input="speech", action="/process", timeout=6)
        return str(vr)

    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_input}
        ]
    )

    reply = response.choices[0].message.content
    vr.say(reply, voice="alice")

    if any(word in reply.lower() for word in ["next round", "connect", "call back"]):
        vr.say("Thank you for your time. Debanjan will connect with you.", voice="alice")
        vr.hangup()
    else:
        vr.gather(input="speech", action="/process", timeout=6)

    return str(vr)
