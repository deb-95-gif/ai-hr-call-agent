from fastapi import FastAPI, Request, Response
from twilio.twiml.voice_response import VoiceResponse
from twilio.rest import Client
from collections import defaultdict
from datetime import datetime, timedelta
import os

app = FastAPI()

call_memory = defaultdict(dict)

def get_lwd_text():
    today = datetime.today()
    days_to_friday = 4 - today.weekday()
    current_week_friday = today + timedelta(days=days_to_friday)
    lwd = current_week_friday + timedelta(days=7)
    day = lwd.day
    suffix = "th" if 11 <= day <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
    return f"{day}{suffix} {lwd.strftime('%B')}"

def rule_based_reply(text: str) -> str:
    t = text.lower()
    if "role" in t or "position" in t:
        return "Yes, he is open to Data Engineer roles."
    if "experience" in t or "years" in t:
        return "He has five point six years of total experience, with over five years in data engineering."
    if "current company" in t or "working" in t:
        return "He is currently working as a Data Engineer at Globus Info Services."
    if any(word in t for word in ["aws", "sql", "python", "spark", "pyspark", "etl", "data"]):
        return "Yes, he has strong experience in AWS, SQL, Python, PySpark, ETL, and data warehousing."
    if "ctc" in t or "salary" in t or "package" in t:
        return "His current CTC is seven point five LPA, and his expected CTC is sixteen LPA."
    if "notice" in t or "joining" in t or "lwd" in t:
        return f"His last working day would be {get_lwd_text()}."
    if "why" in t and ("change" in t or "switch" in t):
        return "Earlier changes were for learning. He is now focused on long term growth and stability."
    if "how many" in t and "company" in t:
        return "This is his fifth organization since starting his career in January two thousand twenty."
    if "interested" in t or "open to" in t:
        return "Yes, he is actively exploring relevant opportunities."
    return "I’m afraid I don’t have that information. Debanjan can clarify this directly."

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
    summary = call_memory.get(call_sid, {})
    message = (
        "📞 HR Call Summary\n\n"
        f"Company: {summary.get('company', 'Not mentioned')}\n"
        f"Role: {summary.get('role', 'Not mentioned')}\n"
        f"Tech: {summary.get('tech', 'Not mentioned')}\n"
        f"Next step: {summary.get('next_step', 'Not mentioned')}"
    )
    client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
    client.messages.create(
        from_="whatsapp:+14155238886",
        to=f"whatsapp:{os.getenv('OWNER_WHATSAPP')}",
        body=message
    )

@app.post("/voice")
async def voice():
    vr = VoiceResponse()
    vr.say("Hi, I am Debanjan Bhowmick. I’m unavailable right now, so my assistant is speaking on my behalf.", voice="alice")
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
    reply = rule_based_reply(user_input)
    vr.say(reply, voice="alice")

    if any(word in user_input.lower() for word in ["thank you", "bye", "goodbye"]):
        send_whatsapp_summary(call_sid)
        vr.say("Thank you for your time. Debanjan will connect with you.", voice="alice")
        vr.hangup()
        return Response(content=str(vr), media_type="application/xml")

    vr.gather(input="speech", action="/process", timeout=6, speechTimeout="auto")
    return Response(content=str(vr), media_type="application/xml")
