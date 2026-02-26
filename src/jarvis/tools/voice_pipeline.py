"""
Voice Pipeline for integrating OpenAI Speech-To-Text (Whisper) and Text-To-Speech.
Implements the Sandwich Architecture: STT -> Agent -> TTS.
"""
import asyncio
import io
from typing import AsyncIterator
from openai import AsyncOpenAI
import websockets
from pydub import AudioSegment
import json

from jarvis.tools.events import VoiceAgentEvent
from jarvis.config import OPENAI_API_KEY
from jarvis.deepagent import create_jarvis_agent

# Initialize OpenAI Client
client = AsyncOpenAI(api_key=OPENAI_API_KEY)

async def _process_audio_chunk_to_text(audio_bytes: bytes) -> str:
    """
    Helper function to send a chunk of PCM audio to OpenAI Whisper for STT.
    OpenAI Whisper requires a file-like object (e.g. WAV/MP3).
    We convert the raw PCM stream to an in-memory WAV file temporarily.
    """
    try:
        # Assuming audio from the browser is 16kHz, 1-channel, 16-bit PCM
        audio_segment = AudioSegment(
            data=audio_bytes,
            sample_width=2,
            frame_rate=16000,
            channels=1
        )
        wav_io = io.BytesIO()
        audio_segment.export(wav_io, format="wav")
        wav_io.name = "audio.wav"
        wav_io.seek(0)
        
        # Call Whisper
        transcription = await client.audio.transcriptions.create(
            model="whisper-1",
            file=wav_io,
            response_format="text"
        )
        return transcription.strip()
    except Exception as e:
        print(f"[STT Error] {e}")
        return ""


async def stt_stream(audio_stream: AsyncIterator[bytes]) -> AsyncIterator[VoiceAgentEvent]:
    """
    Transform stream: Audio (Bytes) -> Voice Events (STT output)
    We batch incoming audio bytes until a silence or a fixed time window,
    then send it to STT. For simplicity in this demo, we can just grab chunk by chunk.
    """
    # A real production system would use silence detection or continuous WebSockets. 
    # For this implementation, we will accumulate a few chunks to form a coherent phrase before sending.
    
    buffer = bytearray()
    CHUNK_ACCUMULATION_THRESHOLD = 16000 * 2 * 1 * 3 # 3 seconds of 16k 16-bit audio
    
    async for audio_chunk in audio_stream:
        buffer.extend(audio_chunk)
        
        if len(buffer) >= CHUNK_ACCUMULATION_THRESHOLD:
            # Yield partial/final
            transcript = await _process_audio_chunk_to_text(bytes(buffer))
            if transcript:
                yield VoiceAgentEvent.stt_output(transcript)
            buffer.clear()
            
    # Process remaining buffer
    if len(buffer) > 0:
        transcript = await _process_audio_chunk_to_text(bytes(buffer))
        if transcript:
            yield VoiceAgentEvent.stt_output(transcript)


async def agent_stream(event_stream: AsyncIterator[VoiceAgentEvent], session_id: str) -> AsyncIterator[VoiceAgentEvent]:
    """
    Transform stream: STT Events -> Agent Text Chunks
    """
    agent = create_jarvis_agent()
    config = {"configurable": {"thread_id": session_id}}

    async for event in event_stream:
        yield event # Pass through STT events

        if event.type == "stt_output" and event.transcript:
            print(f"[Agent] Received Transcript: {event.transcript}")
            try:
                # Stream agent response
                stream = agent.astream_events(
                    {"messages": [("user", event.transcript)]},
                    config,
                    version="v1"
                )
                
                async for agent_event in stream:
                    # Capture tokens as they stream out
                    if agent_event["event"] == "on_chat_model_stream":
                        chunk = agent_event["data"]["chunk"]
                        if chunk.content:
                            yield VoiceAgentEvent.agent_chunk(chunk.content)
            except Exception as e:
               print(f"[Agent Error] {e}")


async def tts_stream(event_stream: AsyncIterator[VoiceAgentEvent]) -> AsyncIterator[VoiceAgentEvent]:
    """
    Transform stream: Agent Text Chunks -> TTS Audio (Bytes)
    OpenAI's TTS doesn't currently support streaming *websockets* for input text, 
    but we can send chunks of text and stream the resulting audio response.
    """
    text_buffer = ""
    # We yield audio as we get sentences to prevent delay
    
    async def synthesize(text_to_speak: str):
        if not text_to_speak.strip():
            return
        print(f"[TTS] Synthesizing: {text_to_speak}")
        try:
            response = await client.audio.speech.create(
                model="tts-1",
                voice="alloy",
                input=text_to_speak,
                response_format="pcm"
            )
            # OpenAI speech streams the bytes back
            async for audio_bytes in response.response.aiter_bytes():
                yield VoiceAgentEvent.tts_chunk(audio_bytes)
        except Exception as e:
            print(f"[TTS Error] {e}")

    async for event in event_stream:
        yield event # Pass through
        
        if event.type == "agent_chunk" and event.text:
            text_buffer += event.text
            # Basic sentence boundary detection
            if any(char in text_buffer for char in ['.', '!', '?', '\n']):
                async for chunk in synthesize(text_buffer):
                    yield chunk
                text_buffer = ""
                
    # Process any leftover text
    if text_buffer.strip():
         async for chunk in synthesize(text_buffer):
            yield chunk

