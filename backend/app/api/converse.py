from fastapi import APIRouter, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse
from fastapi import Request
import os
import httpx
import uuid
from app.core import config
from app.services.energy_agent import run_agent
import logging
import re

# Placeholder imports for LangChain and ElevenLabs
# from langchain_agent import run_agent
# from elevenlabs_tts import synthesize_speech

router = APIRouter()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_WHISPER_URL = "https://api.openai.com/v1/audio/transcriptions"
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_TTS_URL = "https://api.elevenlabs.io/v1/text-to-speech/<voice_id>"  # Replace <voice_id> as needed
AUDIO_SAVE_DIR = "audio_responses"
os.makedirs(AUDIO_SAVE_DIR, exist_ok=True)

logger = logging.getLogger(__name__)

@router.post("/converse")
async def converse(request: Request, file: UploadFile = File(...)):
    # Parse state from form-data if present
    form = await request.form()
    state = None
    if 'state' in form:
        import json
        try:
            state = json.loads(form['state'])
        except Exception:
            state = None
    # 1. Transcribe audio with Whisper
    if not OPENAI_API_KEY:
        logger.error("OpenAI API key not set.")
        raise HTTPException(status_code=500, detail="OpenAI API key not set.")
    try:
        contents = await file.read()
        files = {'file': (file.filename, contents, file.content_type or 'audio/wav')}
        data = {'model': 'whisper-1'}
        headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
        async with httpx.AsyncClient() as client:
            response = await client.post(OPENAI_WHISPER_URL, data=data, files=files, headers=headers, timeout=60)
            response.raise_for_status()
            whisper_result = response.json()
        transcription = whisper_result.get("text", "")
        logger.info(f"Transcription: {transcription}")
    except Exception as e:
        logger.error(f"Transcription failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

    # 2. Run LangChain agent with state
    try:
        agent_result = run_agent(transcription, state)
        agent_response = agent_result["agent_response"]
        state = agent_result["state"]
        done = agent_result["done"]
        logger.info(f"Agent state: {state}")
        logger.info(f"Agent response: {agent_response}")
    except Exception as e:
        logger.error(f"Agent error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")

    # 3. Synthesize with ElevenLabs
    if not ELEVENLABS_API_KEY:
        logger.error("ElevenLabs API key not set.")
        raise HTTPException(status_code=500, detail="ElevenLabs API key not set.")
    try:
        tts_headers = {
            "xi-api-key": ELEVENLABS_API_KEY,
            "Content-Type": "application/json"
        }
        tts_data = {
            "text": agent_response,
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.5}
        }
        voice_id = "EXAVITQu4vr4xnSDxMaL"  # Default ElevenLabs voice
        tts_url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        async with httpx.AsyncClient() as client:
            tts_resp = await client.post(tts_url, headers=tts_headers, json=tts_data)
            tts_resp.raise_for_status()
            audio_bytes = tts_resp.content
        audio_filename = f"{uuid.uuid4()}.mp3"
        audio_path = os.path.join(AUDIO_SAVE_DIR, audio_filename)
        with open(audio_path, "wb") as f:
            f.write(audio_bytes)
        audio_url = f"/audio/{audio_filename}"
        logger.info(f"TTS audio saved: {audio_url}")
    except Exception as e:
        logger.error(f"TTS failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"TTS failed: {str(e)}")

    return JSONResponse({
        "transcription": transcription,
        "agent_response": agent_response,
        "audio_url": audio_url,
        "state": state,
        "done": done
    }) 