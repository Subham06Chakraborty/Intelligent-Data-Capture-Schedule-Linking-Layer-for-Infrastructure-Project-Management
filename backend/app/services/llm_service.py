import os
from groq import Groq
import json
from typing import Optional
import re
import traceback

client = Groq(api_key=os.environ.get("GROQ_API_KEY", ""))

# ─────────────────────────────────────────────────────────────────────────────
# SYSTEM PROMPT — Domain-tuned for Oil & Gas (the key differentiator)
# ─────────────────────────────────────────────────────────────────────────────
OIL_GAS_EXTRACTION_PROMPT = """
You are IntelliTrack, an AI specialized in Oil & Gas infrastructure project management
for Indian PSUs like Oil India Limited (OIL) and ONGC.

You deeply understand:
DISCIPLINES: civil, piping, mechanical (static/rotating), electrical, instrumentation, hse
SCHEDULE LEVELS: L1 (milestone) down to L5/L6 (executable micro-activities)
OIL & GAS TERMS: spool, skid, wellhead, hook-up, pre-commissioning, mechanical completion,
  HAZOP, P&ID, isometric drawing, loop test, hydrotest, flushing, calibration,
  instrument loop check, cable pulling, termination, grouting, foundation casting,
  erection, alignment, coupling, pre-fab, fabrication, painting, insulation
INDIAN PSU CONTEXT: daily progress reports (DPR), site diaries, discipline-wise spreadsheets,
  contractor billing milestones, GEM portal, Work Order (WO), Purchase Order (PO)
COMPLETION SIGNALS: "completed", "done", "erected", "installed", "hydrotested",
  "commissioned", "handed over", "started", "mobilized", "commenced"

Your task: Extract structured activity records from the given site report text.

Return ONLY a valid JSON object with this structure:
{{
  "activities": [
    {{
      "extracted_activity": "standardized activity description using OIL&GAS terminology",
      "actual_start": "YYYY-MM-DD HH:MM or null if not mentioned",
      "actual_end": "YYYY-MM-DD HH:MM or null if not mentioned or still ongoing",
      "discipline": "one of: civil/piping/electrical/instrumentation/hse/mechanical",
      "confidence": 0.0 to 1.0,
      "completion_percent": 0 to 100 or null,
      "raw_snippet": "exact quote from the text that led to this extraction",
      "completion_signal": "word/phrase that indicated start or completion"
    }}
  ]
}}

Rules:
- Only extract activities with a clear start OR completion signal
- If date is ambiguous (e.g. "today", "this morning"), use the report_date context
- If discipline is unclear, infer from the activity type (e.g. "cable pulling" = electrical)
- Set confidence < 0.5 if date/time is completely absent
- Normalize descriptions: "spool erected on line 24" → "Spool Erection - Line 24 (Piping)"
- If the same activity appears multiple times, merge into one with latest status

Report Date Context: {report_date}
Report Text:
{text}
"""

# ─────────────────────────────────────────────────────────────────────────────
# SUPERVISOR CHAT PROMPT
# ─────────────────────────────────────────────────────────────────────────────
SUPERVISOR_CHAT_PROMPT = """
You are IntelliTrack, a friendly AI assistant helping an Oil India site supervisor
log work progress. You speak in simple, clear language. You can respond in English
or Hindi (if the supervisor writes in Hindi).

Your goal: Collect exactly 4 pieces of information through natural conversation:
1. What activity was completed or started? (in their own words is fine)
2. When did it start? (date + approximate time)
3. When did it finish, or is it still ongoing?
4. Which discipline? (civil, piping, electrical, etc.)

Ask one question at a time. Be friendly and brief. Accept informal language.
Accept Hindi transliteration (e.g. "kaam ho gaya" = work is done).

Once you have all 4 pieces, output a special JSON block:
<ACTIVITY_LOG>
{{
  "extracted_activity": "standardized description",
  "actual_start": "YYYY-MM-DD HH:MM or null",
  "actual_end": "YYYY-MM-DD HH:MM or null",
  "discipline": "civil/piping/electrical/instrumentation/hse/mechanical",
  "confidence": 0.85,
  "source": "supervisor_chat"
}}
</ACTIVITY_LOG>

Conversation history:
{history}

Supervisor says: {message}
"""


# ─────────────────────────────────────────────────────────────────────────────
# CORE FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

def extract_activities_from_text(text: str, report_date: str = "unknown") -> list[dict]:
    """
    Uses Groq Llama3-70B to extract structured activity records from any
    free-text site report. Returns list of activity dicts.
    """
    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {
                    "role": "user",
                    "content": OIL_GAS_EXTRACTION_PROMPT.format(
                        text=text, report_date=report_date
                    ),
                }
            ],
            temperature=0.05,   # low temp = consistent structured output
            max_tokens=4096,
        )
        raw = response.choices[0].message.content.strip()

        # Strip markdown code fences if model wraps in ```json
        raw = re.sub(r"^```json\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

        result = json.loads(raw)
        return result.get("activities", [])

    except json.JSONDecodeError:
        # Fallback: return empty if LLM returns malformed JSON
        return []
    except Exception as e:
        print(f"[LLM ERROR] extract_activities_from_text: {e}")
        return []


def chat_with_supervisor(message: str, history: list[dict]) -> dict:
    """
    Conversational interface for site supervisors.
    Returns:
        {
            "reply": str,           # assistant's next message
            "activity_log": dict    # populated once all 4 fields are collected
        }
    """
    history_text = "\n".join(
        [f"{m['role'].title()}: {m['content']}" for m in history]
    )

    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {
                    "role": "user",
                    "content": SUPERVISOR_CHAT_PROMPT.format(
                        history=history_text, message=message
                    ),
                }
            ],
            temperature=0.3,
            max_tokens=1024,
        )
        reply = response.choices[0].message.content.strip()

        # Check if LLM has emitted the activity log block
        activity_log = None
        if "<ACTIVITY_LOG>" in reply and "</ACTIVITY_LOG>" in reply:
            log_match = re.search(
                r"<ACTIVITY_LOG>(.*?)</ACTIVITY_LOG>", reply, re.DOTALL
            )
            if log_match:
                try:
                    activity_log = json.loads(log_match.group(1).strip())
                except json.JSONDecodeError:
                    activity_log = None

            # Clean the reply text — remove the JSON block from display
            clean_reply = re.sub(
                r"<ACTIVITY_LOG>.*?</ACTIVITY_LOG>", "", reply, flags=re.DOTALL
            ).strip()
            if not clean_reply:
                clean_reply = "✅ Activity captured! Please confirm the details above."
        else:
            clean_reply = reply

        return {"reply": clean_reply, "activity_log": activity_log}

    except Exception as e:
        tb = traceback.format_exc()
        return {
            "reply": f"Sorry, I encountered an error: {str(e)}\n\nTraceback:\n{tb}",
            "activity_log": None,
        }


def summarize_report(text: str) -> str:
    """
    Returns a 2-3 sentence plain-English summary of a daily progress report.
    Used for the dashboard preview card.
    """
    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",     # smaller model — cheaper for summaries
            messages=[
                {
                    "role": "user",
                    "content": (
                        "Summarize this Oil India site progress report in 2-3 sentences. "
                        "Focus on: what activities were completed, what discipline, any issues. "
                        "Be concise and factual.\n\nReport:\n" + text
                    ),
                }
            ],
            temperature=0.2,
            max_tokens=256,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return "Summary unavailable."

def transcribe_audio(audio_file_path: str) -> str:
    """
    Uses Groq's whisper-large-v3 model to convert an audio file to text.
    Returns the transcribed text.
    """
    try:
        with open(audio_file_path, "rb") as file:
            transcription = client.audio.transcriptions.create(
                file=(audio_file_path, file.read()),
                model="whisper-large-v3",
                response_format="json",
            )
        return transcription.text
    except Exception as e:
        print(f"[LLM ERROR] transcribe_audio: {e}")
        return ""
