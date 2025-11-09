from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os, json, base64, time, uuid, requests
import snowflake.connector
from dotenv import load_dotenv

# ----------------------------
# LOAD ENVIRONMENT
# ----------------------------
load_dotenv()

app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)

# ----------------------------
# CONFIGURATION
# ----------------------------
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL_NAME = "meta-llama/llama-3.1-70b-instruct"

SNOWFLAKE_ACCOUNT = os.getenv("SNOWFLAKE_ACCOUNT")
SNOWFLAKE_USER = os.getenv("SNOWFLAKE_USER")
SNOWFLAKE_PASSWORD = os.getenv("SNOWFLAKE_PASSWORD")
SNOWFLAKE_WAREHOUSE = os.getenv("SNOWFLAKE_WAREHOUSE")
SNOWFLAKE_DATABASE = os.getenv("SNOWFLAKE_DATABASE")
SNOWFLAKE_SCHEMA = os.getenv("SNOWFLAKE_SCHEMA")

# ----------------------------
# SNOWFLAKE HELPERS
# ----------------------------
def get_conn():
    return snowflake.connector.connect(
        account=SNOWFLAKE_ACCOUNT,
        user=SNOWFLAKE_USER,
        password=SNOWFLAKE_PASSWORD,
        warehouse=SNOWFLAKE_WAREHOUSE,
        database=SNOWFLAKE_DATABASE,
        schema=SNOWFLAKE_SCHEMA,
    )


def save_session(session):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO chat_sessions(session_id, ts, question, sections_json, answers_json)
            VALUES(%s, %s, %s, %s, %s)
            """,
            (
                session["id"],
                session["ts"],
                session["question"],
                json.dumps(session["sections"]),
                json.dumps(session["answers"]),
            ),
        )
        conn.commit()
    finally:
        cur.close()
        conn.close()


def get_history(limit=50):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT session_id, ts, question FROM chat_sessions ORDER BY ts DESC LIMIT %s", (limit,)
        )
        rows = cur.fetchall()
        return [
            {"id": r[0], "ts": r[1], "title": r[2][:60] + ("..." if len(r[2]) > 60 else "")}
            for r in rows
        ]
    finally:
        cur.close()
        conn.close()


def get_session(session_id):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT session_id, ts, question, sections_json, answers_json
            FROM chat_sessions WHERE session_id=%s
            """,
            (session_id,),
        )
        row = cur.fetchone()
        if not row:
            return None
        return {
            "id": row[0],
            "ts": row[1],
            "question": row[2],
            "sections": json.loads(row[3]),
            "answers": json.loads(row[4]),
        }
    finally:
        cur.close()
        conn.close()

# ----------------------------
# ROUTES
# ----------------------------
@app.route("/")
def home():
    return render_template("index.html")


@app.post("/api/run")
def run_query():
    data = request.get_json(force=True)
    question = data.get("question", "").strip()
    sections = data.get("sections", ["Answer", "Explanation", "Why this"])

    if not question:
        return jsonify({"error": "No question provided"}), 400

    # Dynamic prompts for better alignment
    system_prompt = (
        "You are PromptForge, a structured reasoning assistant. "
        "Always reply in Markdown and use the exact section headers provided."
    )
    user_prompt = f"Question: {question}\n\nPlease structure your answer clearly using these sections: {', '.join(sections)}."

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    ai_text = ""
    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": MODEL_NAME,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 600,
        }

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=60,
        )
        data_out = response.json()
        if "choices" in data_out and len(data_out["choices"]) > 0:
            ai_text = data_out["choices"][0]["message"].get("content", "").strip()
        else:
            ai_text = f"Unexpected response: {data_out}"
    except Exception as e:
        ai_text = f"Error contacting OpenRouter: {str(e)}"

    # --- Section parsing (robust version) ---
    answers = {}
    ai_text = ai_text.replace("**:", "**")  # normalize colon formatting
    lower_text = ai_text.lower()

    for section in sections:
        marker = f"**{section.strip().lower()}**"
        start = lower_text.find(marker)
        if start == -1:
            answers[section] = "(no response)"
            continue
        start += len(marker)

        # Find next marker regardless of order
        next_positions = [
            lower_text.find(f"**{s.strip().lower()}**", start)
            for s in sections
            if s != section
        ]
        next_positions = [p for p in next_positions if p != -1]
        next_marker = min(next_positions) if next_positions else None

        part = ai_text[start:next_marker].strip() if next_marker else ai_text[start:].strip()
        answers[section] = part or "(no content)"

    # Save to Snowflake
    session = {
        "id": str(uuid.uuid4()),
        "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
        "question": question,
        "sections": sections,
        "answers": answers,
    }
    save_session(session)

    return jsonify({"sections": answers, "session_id": session["id"]})


@app.get("/api/history")
def history_list():
    return jsonify({"sessions": get_history()})


@app.get("/api/history/<sid>")
def history_get(sid):
    session = get_session(sid)
    if not session:
        return jsonify({"error": "not found"}), 404
    return jsonify(session)


@app.post("/api/stt")
def stt():
    try:
        ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
        if "audio" not in request.files:
            return jsonify({"error": "No audio uploaded"}), 400

        audio_file = request.files["audio"]
        headers = {"xi-api-key": ELEVENLABS_API_KEY}
        files = {"file": (audio_file.filename, audio_file, "audio/wav")}

        response = requests.post(
            "https://api.elevenlabs.io/v1/speech-to-text",
            headers=headers,
            files=files,
        )

        if response.status_code != 200:
            return jsonify({"error": response.text}), 500

        return jsonify(response.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
