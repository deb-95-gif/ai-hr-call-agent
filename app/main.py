from fastapi import FastAPI, Request, Response
from twilio.twiml.voice_response import VoiceResponse

app = FastAPI()


def rule_based_reply(text: str) -> str:
    t = text.lower()

    if "role" in t or "position" in t:
        return "Thanks. Could you please share the team and tech stack?"

    if "experience" in t or "years" in t:
        return "He has five point six years total, with over five years in data engineering."

    if "current company" in t or "working" in t:
        return "He is currently working as a Data Engineer at Globus Info Services."

    if "ctc" in t or "salary" in t or "package" in t:
        return "Current CTC is seven point five LPA. Expected is around sixteen LPA."

    if "notice" in t or "joining" in t:
        return "His last working day would be 9th Jan 2025."

    if "why" in t and ("change" in t or "switch" in t):
        return "Early switches were for learning. Now he is focused on long term stability."

    if "aws" in t or "sql" in t or "python" in t:
        return "Yes, he has around five years experience in AWS, SQL, Python, and data engineering."

    if "infosys" in t or "interview" in t or "next round" in t:
        return "That sounds good. Could you please share the next steps?"

    return "Thanks for the details. Debanjan will personally connect with you shortly."


@app.post("/voice")
async def voice():
    vr = VoiceResponse()

    vr.say(
        "Hi, I am Debanjan Bhowmick. "
        "I’m unavailable right now, so my assistant is speaking on my behalf. "
        "Please go ahead.",
        voice="alice"
    )

    vr.gather(
        input="speech",
        action="/process",
        timeout=6,
        speechTimeout="auto"
    )

    return Response(content=str(vr), media_type="application/xml")


@app.post("/process")
async def process(request: Request):
    form = await request.form()
    user_input = form.get("SpeechResult", "").strip()

    vr = VoiceResponse()

    if not user_input:
        vr.say(
            "Sorry, I didn’t catch that. Could you please repeat?",
            voice="alice"
        )
        vr.gather(
            input="speech",
            action="/process",
            timeout=6,
            speechTimeout="auto"
        )
        return Response(content=str(vr), media_type="application/xml")

    reply = rule_based_reply(user_input)

    vr.say(reply, voice="alice")

    if "connect" in reply.lower() or "next steps" in reply.lower():
        vr.say(
            "Thank you for your time. Debanjan will connect with you.",
            voice="alice"
        )
        vr.hangup()
    else:
        vr.gather(
            input="speech",
            action="/process",
            timeout=6,
            speechTimeout="auto"
        )

    return Response(content=str(vr), media_type="application/xml")
