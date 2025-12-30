from fastapi import FastAPI, Request, Response
from twilio.twiml.voice_response import VoiceResponse
from dotenv import load_dotenv
import os

from openai import OpenAI
from app.prompts import SYSTEM_PROMPT

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = FastAPI()


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

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_input}
            ],
            timeout=10
        )

        reply = completion.choices[0].message.content.strip()

    except Exception as e:
        print("OpenAI error:", e)

        vr.say(
            "Thank you for sharing the details. "
            "Debanjan will personally connect with you shortly.",
            voice="alice"
        )
        vr.hangup()

        return Response(content=str(vr), media_type="application/xml")

    vr.say(reply, voice="alice")

    if any(
        keyword in reply.lower()
        for keyword in ["next round", "connect", "call back", "follow up"]
    ):
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
