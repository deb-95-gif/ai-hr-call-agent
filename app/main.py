from fastapi import FastAPI, Request, Response
from twilio.twiml.voice_response import VoiceResponse
from twilio.rest import Client
from collections import defaultdict
from datetime import datetime, timedelta
from openai import OpenAI
import os

from app.prompts import SYSTEM_PROMPT

app = FastAPI()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

call_memory = defaultdict(dict)

# -------- Helpers --------

def get_lwd_text():
    today = datetime.today()
    days_to_friday = 4 - today.weekday()
    friday = today + timedelta(days=days_to_friday)
    lwd = friday + timedelta(days=7)

    d = lwd.day
    suffix = "th" if 11 <= d <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(d % 10, "th")
    return f"{d}{suffix} {lwd.strftime('%B')}"

def ai_reply(text: str) -> str:
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text}
        ],
        max_tokens=80,
        temperature=0.2
    )
    return completion.choices[0].message.content.strip()

def capture_call_details(call_sid: str, text: str):
    t = text.lower()
    if "infosys" in t:
        call_memory[call_sid]["company"] = "Infosys"
    if "data engineer" in t:
        call_memory[call_sid]["role"] = "Data Engineer"
    if any(k in t for k in ["aws", "sql", "python", "spark"]):
        call_memory[call_sid]["tech"] = "AWS / SQL / Python / Spark"
    if "interview" in t or "next round" in t:
        call_memory[call_sid]["next_step"] = "Interview discussion"

def send_whatsapp_summary(call_sid: str):
    s = call_memory.get(call_sid, {})
    msg = (
        "📞 HR Call Summary\n\n"
        f"Company: {s.get('company', 'Not mentioned')}\n"
        f"Role: {s.get('role', 'Not mentioned')}\n"
        f"Tech: {s.get('tech', 'Not mentioned')}\n"
        f"Next step: {s.get('next_step', 'Not mentioned')}"
    )

    twilio = Client(
        os.getenv("TWILIO_ACCOUNT_SID"),
        os.getenv("TWILIO_AUTH_TOKEN")
    )

    twilio.messages.create(
        from_="whatsapp:+14155238886",
        to=f"whatsapp:{os.getenv('OWNER_WHATSAPP')}",
        body=msg
    )

# -------- Routes --------

@app.post("/voice")
async def voice():
    vr = VoiceResponse()
    vr.say(
        "Hi, this is Debanjan Bhowmick’s assistant. Please go ahead.",
        voice="alice"
    )
    vr.gather(input="speech", action="/process", timeout=6, speechTimeout="auto")
    return Response(content=str(vr), media_type="application/xml")

@app.post("/process")
async def process(request: Request):
    form = await request.form()
    user_input = form.get("SpeechResult", "").strip()
    call_sid = form.get("CallSid")

    vr = VoiceResponse()

    if not user_input:
        vr.say("Sorry, I didn’t catch that. Please repeat.", voice="alice")
        vr.gather(input="speech", action="/process", timeout=6, speechTimeout="auto")
        return Response(content=str(vr), media_type="application/xml")

    capture_call_details(call_sid, user_input)

    try:
        reply = ai_reply(user_input)
    except Exception:
        reply = "I don’t have that information right now."

    vr.say(reply, voice="alice")

    if any(w in user_input.lower() for w in ["thank you", "bye", "goodbye"]):
        send_whatsapp_summary(call_sid)
        vr.say("Thank you for your time. Debanjan will connect with you.", voice="alice")
        vr.hangup()
        return Response(content=str(vr), media_type="application/xml")

    vr.gather(input="speech", action="/process", timeout=6, speechTimeout="auto")
    return Response(content=str(vr), media_type="application/xml")
