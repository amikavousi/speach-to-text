import hashlib
import time
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
import speech_recognition as sr
from pydub import AudioSegment
import os

app = FastAPI()


@app.get("/")
async def root():
    return {"Hello": "World"}


@app.post("/audio-to-text/")
async def audio_to_text(source: str = Form(default=None),
                        source_user_id: int = Form(default=None),
                        file: UploadFile = File(...)):

    if file.content_type not in ["audio/wav", "audio/mpeg", "audio/mp4"]:
        raise HTTPException(status_code=400, detail="Invalid file type. Only wav and mp3 are supported.")

    audio_file, hashed_file_name = convert_to_wav(source.replace(' ', ''), source_user_id, file)

    sp = sr.Recognizer()
    with sr.AudioFile(audio_file) as source:
        # load audio to memory
        audio_data = sp.record(source)
        # convert speech to text
        text = sp.recognize_google(audio_data, language="fa-FA")
        return {
            "original_name": file.filename,
            "hashed_name": hashed_file_name,
            "text": text
        }


def generate_hashed_filename(original_filename: str) -> str:
    # Get the current time in seconds
    current_time = str(time.time()).encode()  # Current time as bytes
    # Combine the original filename and current time
    hash_input = f"{original_filename}{current_time}".encode()
    # Generate a hash
    hashed_name = hashlib.sha256(hash_input).hexdigest()  # Use SHA-256 for hashing
    return hashed_name


def convert_to_wav(source: str, source_user_id: int, file: UploadFile) -> tuple[str, str]:
    dri = f"uploads/{source}/{source_user_id}/"
    os.makedirs(dri, exist_ok=True)

    filename = file.filename.split('.')[0]
    hashed_filename = generate_hashed_filename(filename)

    wav_file_path = f"{dri}{hashed_filename}.wav"

    # Ensure that the audio file is saved in a temporary location
    audio_file_path = f"/tmp/{hashed_filename}"

    # Save the uploaded file
    with open(audio_file_path, "wb") as f:
        f.write(file.file.read())

    # Convert to WAV format
    sound = AudioSegment.from_file(audio_file_path)
    sound.export(wav_file_path, format="wav")

    # Clean up the temporary file
    os.remove(audio_file_path)

    return wav_file_path, wav_file_path
