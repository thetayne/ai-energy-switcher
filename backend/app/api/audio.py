import os
from dotenv import load_dotenv
load_dotenv()

from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import httpx
import logging

router = APIRouter()

logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_WHISPER_URL = "https://api.openai.com/v1/audio/transcriptions"

@router.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    logger.info("/transcribe endpoint called")
    logger.info(f"OPENAI_API_KEY loaded: {'yes' if OPENAI_API_KEY else 'no'}")
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
            result = response.json()
        logger.info(f"Transcription result: {result}")
        return JSONResponse({"transcription": result.get("text", "")})
    except Exception as e:
        logger.error(f"Transcription failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}") 
        