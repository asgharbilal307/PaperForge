import streamlit as st
import requests
import json
import html

API_BASE = "http://localhost:8000/api/v1"

st.set_page_config(
    page_title="AI QuizCraft",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Styles ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* App background and font */
.stApp {
    background: linear-gradient(135deg, #181c2f 0%, #23263a 100%);
    font-family: 'Inter', 'Segoe UI', Arial, sans-serif;
    color: #e5e7ef;
}

/* Custom header */
.custom-header {
    font-size: 2.2rem;
    font-weight: 800;
    letter-spacing: -1px;
    color: #a5b4fc;
    margin-bottom: 0.5em;
    text-shadow: 0 2px 12px #23263a44;
}

/* Chat bubbles */
.bubble-user {
    background: linear-gradient(90deg, #6366f1 60%, #818cf8 100%);
    color: #fff;
    border-radius: 18px 18px 6px 18px;
    padding: 14px 20px;
    margin: 6px 0 6px auto;
    max-width: 70%;
    width: fit-content;
    font-size: 1.02rem;
    line-height: 1.7;
    box-shadow: 0 2px 12px #6366f133;
    transition: box-shadow 0.2s;
}
.bubble-user:hover {
    box-shadow: 0 4px 24px #6366f155;
}
.bubble-assistant {
    background: linear-gradient(90deg, #23263a 60%, #181c2f 100%);
    color: #e0e7ef;
    border-radius: 18px 18px 18px 6px;
    padding: 14px 20px;
    margin: 6px auto 6px 0;
    max-width: 80%;
    width: fit-content;
    font-size: 1.02rem;
    line-height: 1.7;
    border: 1px solid #353a5c;
    box-shadow: 0 2px 12px #23263a33;
    transition: box-shadow 0.2s;
}
.bubble-assistant:hover {
    box-shadow: 0 4px 24px #23263a55;
}

/* Intent badges */
.intent-badge {
    display: inline-block;
    font-size: 0.75rem;
    padding: 3px 10px;
    border-radius: 20px;
    margin-top: 8px;
    font-weight: 700;
    letter-spacing: 0.07em;
    text-transform: uppercase;
    box-shadow: 0 1px 4px #23263a22;
}
.badge-retrieve { background: #1e3a8a; color: #60a5fa; }
.badge-generate { background: #166534; color: #34d399; }
.badge-clarify  { background: #854d0e; color: #fbbf24; }

/* Result card */
.result-card {
    background: linear-gradient(90deg, #23263a 60%, #181c2f 100%);
    border: 1.5px solid #353a5c;
    border-left: 4px solid #6366f1;
    border-radius: 10px;
    padding: 16px 20px;
    margin: 12px 0;
    font-size: 0.95rem;
    box-shadow: 0 2px 16px #23263a22;
    transition: box-shadow 0.2s;
}
.result-card:hover {
    box-shadow: 0 6px 32px #23263a44;
}
.result-meta {
    color: #a5b4fc;
    font-size: 0.82rem;
    margin-bottom: 8px;
    font-weight: 600;
}
.result-score {
    float: right;
    background: #23263a;
    padding: 3px 10px;
    border-radius: 14px;
    color: #a78bfa;
    font-size: 0.78rem;
    font-weight: 700;
    box-shadow: 0 1px 4px #23263a22;
}

/* Sidebar styling */
section[data-testid="stSidebar"] {
    background: linear-gradient(135deg, #181c2f 0%, #23263a 100%);
    border-right: 2px solid #353a5c;
    box-shadow: 2px 0 16px #23263a22;
}
.stSidebar .stButton>button {
    background: #6366f1;
    color: #fff;
    border-radius: 8px;
    font-weight: 700;
    transition: background 0.2s;
}
.stSidebar .stButton>button:hover {
    background: #818cf8;
}

/* General tweaks */
.stTextInput>div>input, .stSelectbox>div>div>div>input {
    background: #23263a;
    color: #e0e7ef;
    border-radius: 8px;
    border: 1.5px solid #353a5c;
    font-size: 1rem;
    padding: 8px 12px;
}
.stSlider>div>div>div {
    background: #23263a;
}
.stNumberInput>div>input {
    background: #23263a;
    color: #e0e7ef;
    border-radius: 8px;
    border: 1.5px solid #353a5c;
    font-size: 1rem;
    padding: 8px 12px;
}
.stMarkdown h2 {
    color: #a5b4fc;
    font-weight: 800;
    margin-bottom: 0.5em;
}
.stMarkdown h3 {
    color: #818cf8;
    font-weight: 700;
    margin-bottom: 0.4em;
}
.stMarkdown code {
    background: #23263a;
    color: #fbbf24;
    border-radius: 6px;
    padding: 2px 6px;
}
.stButton>button {
    background: linear-gradient(90deg, #6366f1 60%, #818cf8 100%);
    color: #fff;
    border-radius: 8px;
    font-weight: 700;
    transition: background 0.2s;
    box-shadow: 0 1px 4px #23263a22;
}
.stButton>button:hover {
    background: linear-gradient(90deg, #818cf8 60%, #6366f1 100%);
}
.stCheckbox>div>label {
    color: #a5b4fc;
    font-weight: 600;
}
.stNumberInput>div>input:focus, .stTextInput>div>input:focus {
    border-color: #6366f1;
    outline: none;
}
.stSelectbox>div>div>div>input:focus {
    border-color: #6366f1;
    outline: none;
}
.stSlider>div>div>div:focus {
    border-color: #6366f1;
    outline: none;
}
.stMarkdown a {
    color: #60a5fa;
    text-decoration: underline;
    transition: color 0.2s;
}
.stMarkdown a:hover {
    color: #fbbf24;
}
</style>
""", unsafe_allow_html=True)


# ── Session state ─────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Hi! I'm your **UniStudy RAG assistant** 📚\n\n"
                "I can:\n"
                "- 🔍 **Find** past quizzes, mids, and finals — *'Give me Quiz 1 of Data Structures'*\n"
                "- ✨ **Generate** new exams — *'Create a mid-term for OOP covering inheritance'*\n\n"
                "What do you need?"
            ),
            "intent": None,
        }
    ]

if "courses" not in st.session_state:
    st.session_state.courses = []


# ── Helpers ───────────────────────────────────────────────────────────────────
def fetch_courses():
    try:
        r = requests.get(f"{API_BASE}/courses", timeout=5)
        st.session_state.courses = r.json().get("courses", [])
    except Exception:
        st.session_state.courses = []


def call_chat(message: str) -> dict:
    r = requests.post(
        f"{API_BASE}/chat",
        json={"message": message, "history": []},
        timeout=60,
    )
    r.raise_for_status()
    return r.json()


def call_generate(payload: dict) -> dict:
    r = requests.post(f"{API_BASE}/generate", json=payload, timeout=120)
    r.raise_for_status()
    return r.json()


def call_retrieve(query: str, course: str, doc_type: str, year: str, top_k: int) -> dict:
    r = requests.post(
        f"{API_BASE}/retrieve",
        json={
            "query": query,
            "course": course or None,
            "doc_type": doc_type or None,
            "year": year or None,
            "top_k": top_k,
        },
        timeout=30,
    )
    r.raise_for_status()
    return r.json()


def render_message(msg: dict):
    if msg["role"] == "user":
        st.markdown(
            f'<div class="bubble-user">{msg["content"]}</div>',
            unsafe_allow_html=True,
        )
    else:
        badge = ""
        if msg.get("intent") == "retrieve":
            badge = '<span class="intent-badge badge-retrieve">retrieve</span>'
        elif msg.get("intent") == "generate":
            badge = '<span class="intent-badge badge-generate">generate</span>'
        elif msg.get("intent") == "clarify":
            badge = '<span class="intent-badge badge-clarify">clarify</span>'

        st.markdown(
            f'<div class="bubble-assistant">{msg["content"]}{badge}</div>',
            unsafe_allow_html=True,
        )

        # Show structured retrieve results as cards
        if msg.get("intent") == "retrieve" and msg.get("results"):
            for res in msg["results"]:
                score_pct = int(res["score"] * 100)
                source_link = (
                    f'<a href="{res["source_url"]}" target="_blank" style="color:#818cf8">↗ GitHub</a>'
                    if res.get("source_url") else ""
                )
                st.markdown(
                    f"""<div class="result-card">
                        <div class="result-meta">
                            📁 <b>{html.escape(res['course'])}</b> &nbsp;·&nbsp; {res['doc_type'].upper()} &nbsp;·&nbsp; {html.escape(res['filename'])}
                            {f"&nbsp;·&nbsp;{res['year']}" if res.get('year') else ""}
                            {f"&nbsp;·&nbsp;{source_link}" if source_link else ""}
                            <span class="result-score">{score_pct}% match</span>
                        </div>
                                <div style="color:#cbd5e1;font-size:0.85rem;white-space:pre-wrap">{html.escape(res['content'])}</div>
                    </div>""",
                    unsafe_allow_html=True,
                )



# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="custom-header">📚 UniStudy RAG</div>', unsafe_allow_html=True)
    st.caption("AI-powered study assistant")

    st.divider()

    # Backend status
    try:
        requests.get("http://localhost:8000/health", timeout=2)
        st.success("Backend connected", icon="✅")
    except Exception:
        st.error("Backend offline — run `uvicorn app.main:app --reload`", icon="🔴")

    st.divider()

    # ── Generate form ──────────────────────────────────────────────────────────
    st.markdown("### ✨ Generate Exam")

    course_names = [c["name"] for c in st.session_state.courses]
    gen_course = st.selectbox(
        "Course",
        options=[""] + course_names,
        format_func=lambda x: "Select a course..." if x == "" else x,
    )
    if not gen_course:
        gen_course = st.text_input("Or type course name", placeholder="e.g. Data Structures")

    gen_type = st.selectbox("Exam type", ["quiz", "mid", "final"])
    gen_difficulty = st.select_slider("Difficulty", ["easy", "medium", "hard"], value="medium")
    gen_qtype = st.selectbox("Question types", ["mixed", "mcq", "short", "long"])
    gen_num = st.slider("Number of questions", 3, 30, 10)
    gen_topics = st.text_input(
        "Focus topics (optional)",
        placeholder="e.g. linked lists, recursion",
    )
    gen_key = st.checkbox("Include answer key", value=True)
    gen_duration = st.number_input("Duration (minutes, optional)", min_value=0, value=0, step=15)

    if st.button("🚀 Generate", use_container_width=True, type="primary"):
        if not gen_course:
            st.warning("Please enter a course name.")
        else:
            payload = {
                "course": gen_course,
                "doc_type": gen_type,
                "difficulty": gen_difficulty,
                "question_type": gen_qtype,
                "num_questions": gen_num,
                "include_answer_key": gen_key,
                "topics": [t.strip() for t in gen_topics.split(",") if t.strip()] or None,
                "duration_minutes": gen_duration if gen_duration > 0 else None,
            }
            st.session_state.messages.append({
                "role": "user",
                "content": f"Generate a **{gen_type}** for **{gen_course}** ({gen_difficulty}, {gen_num} questions)",
                "intent": None,
            })
            st.session_state._pending_generate = payload
            st.rerun()

    st.divider()

    # ── Retrieve form ──────────────────────────────────────────────────────────
    st.markdown("### 🔍 Search Documents")

    ret_query = st.text_input("Search query", placeholder="e.g. binary trees quiz")
    ret_course = st.selectbox(
        "Filter by course",
        options=[""] + course_names,
        format_func=lambda x: "All courses" if x == "" else x,
        key="ret_course",
    )
    ret_type = st.selectbox(
        "Filter by type",
        options=["", "quiz", "mid", "final", "notes", "assignment"],
        format_func=lambda x: "All types" if x == "" else x,
    )
    ret_year = st.text_input("Filter by year", placeholder="e.g. 2023")
    ret_topk = st.slider("Max results", 1, 20, 10)

    if st.button("🔎 Search", use_container_width=True):
        if not ret_query:
            st.warning("Enter a search query.")
        else:
            st.session_state.messages.append({
                "role": "user",
                "content": f"Search: *{ret_query}*"
                + (f" · course: {ret_course}" if ret_course else "")
                + (f" · type: {ret_type}" if ret_type else ""),
                "intent": None,
            })
            st.session_state._pending_retrieve = {
                "query": ret_query,
                "course": ret_course,
                "doc_type": ret_type,
                "year": ret_year,
                "top_k": ret_topk,
            }
            st.rerun()

    st.divider()

    if st.button("🔄 Refresh courses", use_container_width=True):
        fetch_courses()
        st.rerun()

    if st.button("🗑️ Clear chat", use_container_width=True):
        st.session_state.messages = st.session_state.messages[:1]
        st.rerun()


# ── Main chat area ────────────────────────────────────────────────────────────
st.markdown("## 💬 Chat")

# Render all messages
for msg in st.session_state.messages:
    render_message(msg)

# Handle pending generate
if hasattr(st.session_state, "_pending_generate"):
    payload = st.session_state._pending_generate
    del st.session_state._pending_generate
    with st.spinner(f"Generating {payload['doc_type'].upper()} for {payload['course']}..."):
        try:
            data = call_generate(payload)
            content = f"### 📄 {data['doc_type'].upper()} — {data['course']}\n\n"
            content += data["exam_markdown"]
            if data.get("answer_key_markdown"):
                content += "\n\n---\n\n### ✅ Answer Key\n\n" + data["answer_key_markdown"]
            st.session_state.messages.append({
                "role": "assistant",
                "content": content,
                "intent": "generate",
            })
        except Exception as e:
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"❌ Generation failed: {e}",
                "intent": None,
            })
    st.rerun()

# Handle pending retrieve
if hasattr(st.session_state, "_pending_retrieve"):
    params = st.session_state._pending_retrieve
    del st.session_state._pending_retrieve
    with st.spinner("Searching..."):
        try:
            data = call_retrieve(**params)
            results = data.get("results", [])
            if results:
                summary = f"Found **{len(results)}** result(s) for *{params['query']}*"
            else:
                summary = f"No results found for *{params['query']}*. Try different keywords or filters."
            st.session_state.messages.append({
                "role": "assistant",
                "content": summary,
                "intent": "retrieve",
                "results": results,
            })
        except Exception as e:
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"❌ Search failed: {e}",
                "intent": None,
            })
    st.rerun()

# ── Chat input ────────────────────────────────────────────────────────────────
st.markdown("---")
col1, col2 = st.columns([5, 1])

with col1:
    user_input = st.chat_input("Ask anything — e.g. 'Give me Quiz 2 of OOP' or 'Generate a final for AI'")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input, "intent": None})
    with st.spinner("Thinking..."):
        try:
            response = call_chat(user_input)
            st.session_state.messages.append({
                "role": "assistant",
                "content": response["response"],
                "intent": response["intent"],
                "results": response.get("structured_data", {}).get("results"),
            })
        except requests.exceptions.ConnectionError:
            st.session_state.messages.append({
                "role": "assistant",
                "content": "❌ Cannot reach the backend. Make sure `uvicorn app.main:app --reload` is running.",
                "intent": None,
            })
        except Exception as e:
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"❌ Error: {e}",
                "intent": None,
            })
    st.rerun()

# Load courses on first run
if not st.session_state.courses:
    fetch_courses()
