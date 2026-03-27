"""
Karo — Chainlit chat app.

Entry point: chainlit run app.py
Calls get_agent() from backend.agent and streams responses via astream_events().
Voice input is handled natively by Chainlit's audio pipeline + faster-whisper STT.
"""

import array
import asyncio
import io
import json
import logging
import os
import re
import tempfile
import traceback
import wave
from typing import Optional

logger = logging.getLogger(__name__)

import chainlit as cl
from faster_whisper import WhisperModel
from langchain_core.messages import ToolMessage

from backend.agent import get_agent
from backend.helpers import serialize_docs

# backend/config.py captures DATABASE_URL at import time via load_dotenv().
# Chainlit lazily checks os.environ["DATABASE_URL"] to auto-activate its own
# Postgres persistence layer (Thread/Step tables). We don't need that — LangGraph
# handles conversation persistence — so remove the var from the environment now,
# after the backend has already read it.
os.environ.pop("DATABASE_URL", None)
os.environ.pop("CHECKPOINT_DB_URL", None)

# ---------------------------------------------------------------------------
# Whisper singleton (loaded once, reused across sessions)
# ---------------------------------------------------------------------------
_whisper: Optional[WhisperModel] = None


def _get_whisper() -> WhisperModel:
    global _whisper
    if _whisper is None:
        _whisper = WhisperModel("small", device="auto", compute_type="int8")
    return _whisper


# ---------------------------------------------------------------------------
# Utility — extract a download URL from an API response string
# ---------------------------------------------------------------------------
def _find_download_url(api_response_str: str) -> Optional[str]:
    match = re.search(r"Success \(\d+\):\s*(\{.*\}|\[.*\])", api_response_str, re.S)
    if not match:
        return None
    try:
        data = json.loads(match.group(1))
    except (json.JSONDecodeError, ValueError):
        return None
    if isinstance(data, list) and data:
        data = data[0]
    if not isinstance(data, dict):
        return None
    for key in ["download_url", "file_url", "report_url", "url", "link", "file_link"]:
        url = data.get(key)
        if url and isinstance(url, str) and url.startswith("http"):
            return url
    return None


# ---------------------------------------------------------------------------
# Session lifecycle
# ---------------------------------------------------------------------------
@cl.on_chat_start
async def on_chat_start() -> None:
    """Initialise per-session state and warm up the agent."""
    thread_id = cl.context.session.id
    cl.user_session.set("thread_id", thread_id)
    cl.user_session.set("audio_buffer", bytearray())

    # Warm up — catches DB/config errors before the first message
    try:
        await get_agent()
    except Exception:
        logger.error("Agent initialisation failed:\n%s", traceback.format_exc())
        await cl.Message(
            content="⚠️ Failed to connect to the agent backend. Check server logs."
        ).send()
        return

    settings = await cl.ChatSettings(
        [
            cl.input_widget.Switch(
                id="show_debug", label="Show debug / raw response", initial=False,
            ),
        ]
    ).send()
    cl.user_session.set("show_debug", settings.get("show_debug", False))


@cl.on_settings_update
async def on_settings_update(settings: dict) -> None:
    cl.user_session.set("show_debug", settings.get("show_debug", False))


# ---------------------------------------------------------------------------
# Voice input — continuous conversation with server-side silence detection
# ---------------------------------------------------------------------------

# Silence detection tunables
_SILENCE_THRESHOLD_RMS = 300  # Int16 RMS below this = silence (~1% of ±32768)
_SILENCE_TIMEOUT_MS = 1500  # ms of continuous silence → trigger processing
_MIN_SPEECH_MS = 400  # ignore utterances shorter than this (clicks/noise)


def _pcm_to_wav(
    pcm_bytes: bytes, sample_rate: int, channels: int = 1, sampwidth: int = 2
) -> bytes:
    """Wrap raw Int16 PCM bytes in a WAV container."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sampwidth)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_bytes)
    return buf.getvalue()


def _rms_int16(data: bytes) -> float:
    """RMS energy of raw Int16 PCM bytes. Returns 0 for empty input."""
    samples = array.array("h", data)
    return (sum(s * s for s in samples) / len(samples)) ** 0.5 if samples else 0.0


def _audio_sample_rate() -> int:
    from chainlit import config as cl_config

    return getattr(
        getattr(cl_config.config.features, "audio", None), "sample_rate", 24000
    )


# Magic-byte signatures for encoded container formats
_CONTAINER_MAGIC = {
    b"\x1a\x45\xdf\xa3": ".webm",  # EBML / WebM / MKV
    b"OggS": ".ogg",  # Ogg
    b"\x00\x00\x00\x20ftyp": ".mp4",  # MP4 (common variant)
    b"\x00\x00\x00\x18ftyp": ".mp4",
    b"RIFF": ".wav",  # WAV (already has header)
    b"ID3": ".mp3",  # MP3 with ID3 tag
    b"\xff\xfb": ".mp3",  # MP3 without ID3
}


async def _transcribe_and_respond(raw: bytes, mime: str) -> None:
    """Transcribe audio bytes and route the text to the agent.

    Always releases the processing lock (audio_processing = False) on exit,
    even if transcription or the agent call raises an exception.
    """
    try:
        async with cl.Step(name="Transcribing…", type="tool", show_input=False) as step:
            whisper = await asyncio.to_thread(_get_whisper)

            # Detect format from magic bytes — mimeType strings can't be trusted
            # (Chrome reports "audio/webm" even when sending raw PCM).
            suffix = None
            for magic, ext in _CONTAINER_MAGIC.items():
                if raw[: len(magic)] == magic:
                    suffix = ext
                    break

            if suffix:
                audio_bytes = raw
                logger.info(
                    "Audio: container %s (%d bytes, mimeType=%r)",
                    suffix,
                    len(raw),
                    mime,
                )
            else:
                sr = _audio_sample_rate()
                audio_bytes = _pcm_to_wav(raw, sample_rate=sr)
                suffix = ".wav"
                logger.info(
                    "Audio: PCM→WAV %d Hz (%d bytes, mimeType=%r)", sr, len(raw), mime
                )

            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                tmp.write(audio_bytes)
                tmp_path = tmp.name
            try:
                segments, _ = await asyncio.to_thread(
                    whisper.transcribe, tmp_path, beam_size=5
                )
                prompt = " ".join(seg.text for seg in segments).strip()
            finally:
                os.unlink(tmp_path)
            step.output = prompt or "(no speech detected)"

        if not prompt:
            await cl.Message(
                content="I couldn't make out any speech — please try again."
            ).send()
            return

        await cl.Message(content=prompt, author="You", type="user_message").send()
        await _handle_question(prompt)

    except Exception:
        logger.error("Voice processing error:\n%s", traceback.format_exc())
        await cl.Message(content="⚠️ Voice processing failed. Please try again.").send()
    finally:
        cl.user_session.set("audio_processing", False)


@cl.on_audio_start
async def on_audio_start() -> bool:
    """Called when the user activates the mic. Resets all conversation state."""
    cl.user_session.set("audio_buffer", bytearray())
    cl.user_session.set("audio_mime_type", "")
    cl.user_session.set("audio_processing", False)
    cl.user_session.set("audio_speech_detected", False)
    cl.user_session.set("audio_silence_ms", 0.0)
    return True


@cl.on_audio_chunk
async def on_audio_chunk(chunk: cl.InputAudioChunk) -> None:
    """Accumulate audio + server-side silence detection for continuous conversation.

    Flow: user presses mic once → speaks → 1.5 s silence → auto-processes utterance
    → agent responds in text → listening resumes automatically (mic still active).
    """
    if chunk.isStart:
        cl.user_session.set("audio_buffer", bytearray())
        cl.user_session.set("audio_mime_type", chunk.mimeType)
        cl.user_session.set("audio_speech_detected", False)
        cl.user_session.set("audio_silence_ms", 0.0)

    if cl.user_session.get("audio_processing"):
        return  # discard chunks while the agent is thinking

    buf: bytearray = cl.user_session.get("audio_buffer") or bytearray()
    buf.extend(chunk.data)
    cl.user_session.set("audio_buffer", buf)

    # --- silence detection ---
    sr = _audio_sample_rate()
    bytes_per_ms = sr * 2 / 1000
    chunk_ms = len(chunk.data) / bytes_per_ms

    rms = _rms_int16(chunk.data)
    if rms >= _SILENCE_THRESHOLD_RMS:
        cl.user_session.set("audio_speech_detected", True)
        cl.user_session.set("audio_silence_ms", 0.0)
    else:
        silence_ms = cl.user_session.get("audio_silence_ms", 0.0) + chunk_ms
        cl.user_session.set("audio_silence_ms", silence_ms)

        speech_detected = cl.user_session.get("audio_speech_detected", False)
        min_bytes = _MIN_SPEECH_MS * bytes_per_ms
        if (
            silence_ms >= _SILENCE_TIMEOUT_MS
            and speech_detected
            and len(buf) >= min_bytes
        ):
            # Snap the current buffer, reset state, fire transcription in background.
            # The mic stays active on the client — new chunks will be discarded until
            # audio_processing is cleared by _transcribe_and_respond's finally block.
            utterance = bytes(buf)
            mime = cl.user_session.get("audio_mime_type") or ""
            cl.user_session.set("audio_buffer", bytearray())
            cl.user_session.set("audio_speech_detected", False)
            cl.user_session.set("audio_silence_ms", 0.0)
            cl.user_session.set("audio_processing", True)
            asyncio.create_task(_transcribe_and_respond(utterance, mime))


@cl.on_audio_end
async def on_audio_end() -> None:
    """User manually stopped the mic — flush any remaining buffered speech."""
    if cl.user_session.get("audio_processing"):
        return
    buf: bytearray = cl.user_session.get("audio_buffer") or bytearray()
    speech_detected = cl.user_session.get("audio_speech_detected", False)
    cl.user_session.set("audio_buffer", bytearray())
    if buf and speech_detected:
        mime = cl.user_session.get("audio_mime_type") or ""
        cl.user_session.set("audio_processing", True)
        await _transcribe_and_respond(bytes(buf), mime)


# ---------------------------------------------------------------------------
# Text input
# ---------------------------------------------------------------------------
@cl.on_message
async def on_message(message: cl.Message) -> None:
    await _handle_question(message.content)


# ---------------------------------------------------------------------------
# Core agent call — streaming
# ---------------------------------------------------------------------------
async def _handle_question(question: str) -> None:
    """Stream the agent response and surface any download links / debug info."""
    thread_id: str = cl.user_session.get("thread_id")
    show_debug: bool = cl.user_session.get("show_debug", False)
    agent = await get_agent()

    response_msg = cl.Message(content="")
    await response_msg.send()

    final_output: Optional[dict] = None

    try:
        async for event in agent.astream_events(
            {"messages": [{"role": "user", "content": question}]},
            config={"configurable": {"thread_id": thread_id}},
            version="v2",
        ):
            kind = event["event"]

            # Capture full graph output for artifact extraction
            if kind == "on_chain_end":
                output = event.get("data", {}).get("output")
                if isinstance(output, dict) and "messages" in output:
                    final_output = output

            # Stream text tokens — skips tool-call chunks (they have no .content)
            elif kind == "on_chat_model_stream":
                token: str = event["data"]["chunk"].content
                if token:
                    await response_msg.stream_token(token)

    except Exception as exc:  # noqa: BLE001
        tb = traceback.format_exc()
        logger.error("Agent error for question %r:\n%s", question, tb)
        await response_msg.update()
        err_detail = str(exc) or type(exc).__name__
        await cl.Message(content=f"⚠️ Error: {err_detail}\n\n```\n{tb}\n```").send()
        return

    await response_msg.update()

    # --- Post-process artifacts ---
    if not final_output:
        return

    api_responses: list[str] = []
    for msg in final_output.get("messages", []):
        if isinstance(msg, ToolMessage):
            tool_name = (
                getattr(msg, "name", None)
                or getattr(msg, "tool", None)
                or getattr(msg, "tool_name", None)
            )
            if tool_name == "APIInput" and msg.content:
                api_responses.append(str(msg.content))

    # Surface download links
    for raw in api_responses:
        url = _find_download_url(raw)
        if url:
            await cl.Message(
                content=f"📥 **Download your report:** [Click here to download]({url})"
            ).send()

    # Debug panel
    if show_debug:
        try:
            debug_text = json.dumps(final_output, indent=2, default=str)
        except Exception:
            debug_text = str(final_output)

        debug_elements = [
            cl.Text(name="Raw result", content=debug_text, language="json")
        ]

        semantic_docs = []
        for msg in final_output.get("messages", []):
            if isinstance(msg, ToolMessage):
                artifact = getattr(msg, "artifact", None)
                tool_name = getattr(msg, "name", None) or getattr(msg, "tool", None)
                if tool_name == "semantic_search_tool" and isinstance(artifact, list):
                    semantic_docs.extend(artifact)

        if semantic_docs:
            docs_text = json.dumps(serialize_docs(semantic_docs), indent=2)
            debug_elements.append(
                cl.Text(
                    name="Retrieved knowledge chunks",
                    content=docs_text,
                    language="json",
                )
            )

        await cl.Message(
            content="🔍 **Debug info** (expand below)", elements=debug_elements,
        ).send()
