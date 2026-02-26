"""
Event types for the Voice Agent pipeline.
"""
from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel, Field

class EventType(str, Enum):
    STT_CHUNK = "stt_chunk"
    STT_OUTPUT = "stt_output"
    AGENT_CHUNK = "agent_chunk"
    TTS_CHUNK = "tts_chunk"
    ERROR = "error"

class VoiceAgentEvent(BaseModel):
    type: EventType
    # Fields depend on the event type
    transcript: Optional[str] = None
    text: Optional[str] = None
    audio: Optional[bytes] = None
    message: Optional[str] = None

    @classmethod
    def stt_chunk(cls, transcript: str) -> "VoiceAgentEvent":
        return cls(type=EventType.STT_CHUNK, transcript=transcript)

    @classmethod
    def stt_output(cls, transcript: str) -> "VoiceAgentEvent":
        return cls(type=EventType.STT_OUTPUT, transcript=transcript)

    @classmethod
    def agent_chunk(cls, text: str) -> "VoiceAgentEvent":
        return cls(type=EventType.AGENT_CHUNK, text=text)

    @classmethod
    def tts_chunk(cls, audio: bytes) -> "VoiceAgentEvent":
        return cls(type=EventType.TTS_CHUNK, audio=audio)
        
    @classmethod
    def error(cls, message: str) -> "VoiceAgentEvent":
        return cls(type=EventType.ERROR, message=message)
