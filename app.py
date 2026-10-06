import streamlit as st

from config import APP_NAME, APP_TAGLINE
from services.document import extract_text
from services.generator import analyze_material, generate_quiz
from services.quiz import score, correct_count, answered_count, unanswered_count, reset_answers
from models.quiz import Question


st.set_page_config(
    page_title=APP_NAME,
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ------------------------- state -------------------------
def init_state():
    defaults = {
        "document_name": None,
        "document_text": "",
        "page_count": 0,
        "analysis": None,
        "questions": [],
        "quiz_title": "",
        "quiz_difficulty": "Medium",
        "generation_source": None,
        "index": 0,
        "finished": False,
        "score": None,
        "page": "Dashboard",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_state()


# ------------------------- theme -------------------------
st.markdown(
    """
    <style>
    .block-container { max-width: 1180px; padding-top: 2rem; padding-bottom: 3rem; }
    .hero { padding: 2.2rem 2.4rem; border-radius: 24px; background: linear-gradient(135deg, #0f766e 0%, #134e4a 55%, #172554 100%); color: white; margin-bottom: 1.5rem; }
    .hero h1 { font-size: 2.7rem; margin: 0 0 .5rem 0; }
    .hero p { font-size: 1.08rem; opacity: .9; margin: 0; }
    .card { padding: 1.25rem; border: 1px solid rgba(127,127,127,.2); border-radius: 18px; background: rgba(127,127,127,.05); min-height: 125px; }
    .timerless-badge { display: inline-block; padding: .35rem .7rem; border-radius: 999px; background: rgba(15,118,110,.12); font-weight: 700; font-size: .85rem; }
    .question-card { padding: 1.1rem 1.25rem; border-radius: 18px; border: 1px solid rgba(127,127,127,.18); margin: 1rem 0; }
    .score-box { padding: 1.5rem; border-radius: 20px; background: rgba(15,118,110,.09); border: 1px solid rgba(15,118,110,.2); }
    </style>
    """,
    unsafe_allow_html=True,
)


def hero(title, subtitle):
    st.markdown(
        f'<div class="hero"><h1>{title}</h1><p>{subtitle}</p></div>',
        unsafe_allow_html=True,
    )


def reset_quiz():
    reset_answers(st.session_state.questions)
    st.session_state.index = 0
    st.session_state.finished = False
    st.session_state.score = None


def dashboard():
    hero("Forge smarter practice.", APP_TAGLINE)

    if st.session_state.document_text:
        a, b, c, d = st.columns(4)
        a.metric("Words", len(st.session_state.document_text.split()))
        b.metric("Pages", st.session_state.page_count)
        c.metric("Topics", len(st.session_state.analysis.get("topics", [])))
        d.metric("Questions", len(st.session_state.questions))

        st.markdown("### Your workspace")
        st.success(f"Active material: {st.session_state.document_name}")

        x, y, z = st.columns(3)
        with x:
            st.markdown('<div class="card"><h3>📄 Material</h3><p>Your uploaded study content is ready.</p></div>', unsafe_allow_html=True)
        with y:
            st.markdown('<div class="card"><h3>🧠 Quiz Forge</h3><p>Generate focused MCQs from your material.</p></div>', unsafe_allow_html=True)
        with z:
            st.markdown('<div class="card"><h3>📊 Analytics</h3><p>Review accuracy, weak topics and answers.</p></div>', unsafe_allow_html=True)
    else:
        st.markdown("### Start in three steps")
        a, b, c = st.columns(3)
        with a:
            st.markdown('<div class="card"><h3>1. Upload</h3><p>Add a PDF, DOCX or TXT study file.</p></div>', unsafe_allow_html=True)
        with b:
            st.markdown('<div class="card"><h3>2. Forge</h3><p>Generate a custom multiple-choice quiz.</p></div>', unsafe_allow_html=True)
        with c:
            st.markdown('<div class="card"><h3>3. Practice</h3><p>Answer questions and inspect your performance.</p></div>', unsafe_allow_html=True)


def upload_page():
    hero("Upload & Analyze", "Give QuizForge the material you actually need to study.")
    uploaded = st.file_uploader("Upload study material", type=["pdf", "docx", "txt"])
    if uploaded is not None:
        if st.button("Analyze material", type="primary", use_container_width=True):
            try:
                with st.spinner("Reading and analyzing your material..."):
                    text, pages = extract_text(uploaded)
                    if len(text.strip()) < 100:
                        raise ValueError("The file contains too little extractable text. Try a text-based PDF, DOCX or TXT file.")
                    analysis = analyze_material(text, uploaded.name)
                    st.session_state.document_name = uploaded.name
                    st.session_state.document_text = text
                    st.session_state.page_count = pages
                    st.session_state.analysis = analysis
                    st.session_state.questions = []
                    st.session_state.quiz_title = ""
                    reset_quiz()
                st.success("Material analyzed successfully.")
            except Exception as exc:
                st.error(str(exc))

    if st.session_state.document_text:
        analysis = st.session_state.analysis
        st.divider()
        a, b, c, d = st.columns(4)
        a.metric("Words", len(st.session_state.document_text.split()))
        b.metric("Pages", st.session_state.page_count)
        c.metric("Topics", len(analysis["topics"]))
        st.markdown(f"### {analysis['title']}")
        st.write("**Detected topics:**")
        st.write(", ".join(analysis["topics"]))
        with st.expander("Preview extracted material"):
            st.text(st.session_state.document_text[:8000])


def builder_page():
    hero("Quiz Forge", "Create a practice assessment from the material you uploaded.")
    if not st.session_state.document_text:
        st.warning("Upload study material first.")
        return

    analysis = st.session_state.analysis
    count = st.slider("Number of questions", 3, 25, 10)
    difficulty = st.select_slider("Difficulty", ["Easy", "Medium", "Hard"], value="Medium")
    topics = st.multiselect("Focus topics", analysis["topics"], default=analysis["topics"][:min(4, len(analysis["topics"]))])



    if st.button("🚀 Forge my quiz", type="primary", use_container_width=True):
        try:
            with st.spinner("Creating your assessment..."):
                questions, source = generate_quiz(
                    st.session_state.document_text,
                    topics,
                    count,
                    difficulty,
                )
                st.session_state.questions = questions
                st.session_state.quiz_title = f"{analysis['title']} Practice"
                st.session_state.quiz_difficulty = difficulty
                st.session_state.generation_source = source
                reset_quiz()
            st.success(f"Created {len(questions)} questions using {source}.")
        except Exception as exc:
            st.error(str(exc))

    if st.session_state.questions:
        st.markdown(
            f'<span class="timerless-badge">{len(st.session_state.questions)} questions · {st.session_state.quiz_difficulty} · {st.session_state.generation_source}</span>',
            unsafe_allow_html=True,
        )


def practice_page():
    hero("Practice", "Answer your generated questions and learn from every result.")
    questions = st.session_state.questions
    if not questions:
        st.warning("Forge a quiz first.")
        return

    if st.session_state.finished:
        st.markdown('<div class="score-box">', unsafe_allow_html=True)
        st.subheader("Practice complete")
        st.metric("Score", f"{st.session_state.score}%")
        st.markdown('</div>', unsafe_allow_html=True)
        st.info("Open Results for the detailed review.")
        if st.button("Practice again", type="primary", use_container_width=True):
            reset_quiz()
            st.rerun()
        return

    index = st.session_state.index
    question = questions[index]
    st.progress((index + 1) / len(questions))
    a, b, c = st.columns(3)
    a.caption(f"QUESTION {index + 1}/{len(questions)}")
    b.caption(f"📚 {question.topic}")
    c.caption(f"🎯 {question.difficulty}")
    st.markdown(f"### {question.prompt}")

    key = f"answer_{index}"
    current = question.options.index(question.user_answer) if question.user_answer in question.options else None
    answer = st.radio("Choose one", question.options, index=current, key=key)
    question.user_answer = answer

    left, right = st.columns(2)
    with left:
        if index > 0 and st.button("← Previous", use_container_width=True):
            st.session_state.index -= 1
            st.rerun()
    with right:
        label = "🏁 Finish Practice" if index == len(questions) - 1 else "Next →"
        if st.button(label, type="primary", use_container_width=True):
            if index == len(questions) - 1:
                st.session_state.score = score(questions)
                st.session_state.finished = True
            else:
                st.session_state.index += 1
            st.rerun()


def analytics_page():
    hero("Analytics", "See where you are strong and where your next revision should go.")
    questions = st.session_state.questions
    if not questions:
        st.info("Generate a quiz first.")
        return

    answered = [q for q in questions if q.user_answer is not None]
    correct = correct_count(questions)
    total = len(questions)
    attempted = len(answered)
    accuracy = round(correct / attempted * 100, 1) if attempted else 0

    a, b, c, d = st.columns(4)
    a.metric("Accuracy", f"{accuracy}%")
    b.metric("Attempted", attempted)
    c.metric("Correct", correct)
    d.metric("Unanswered", unanswered_count(questions))

    if not answered:
        st.info("Answer some questions to unlock performance insights.")
        return

    by_topic = {}
    for q in answered:
        topic = q.topic or "General"
        by_topic.setdefault(topic, [0, 0])
        by_topic[topic][1] += 1
        if q.user_answer == q.answer:
            by_topic[topic][0] += 1

    st.subheader("Topic performance")
    for topic, (right, attempted_topic) in by_topic.items():
        pct = round(right / attempted_topic * 100, 1)
        st.write(f"**{topic}** — {right}/{attempted_topic} ({pct}%)")
        st.progress(pct / 100)

    weak = [topic for topic, (right, attempted_topic) in by_topic.items() if right / attempted_topic < .70]
    if weak:
        st.warning("Focus your next revision on: " + ", ".join(weak))
    else:
        st.success("You are performing strongly across your attempted topics.")


def results_page():
    hero("Results & Review", "Understand every answer, not just the final percentage.")
    questions = st.session_state.questions
    if not questions:
        st.info("Complete a quiz first.")
        return

    if st.session_state.score is not None:
        st.metric("Final Score", f"{st.session_state.score}%")

    a, b, c, d = st.columns(4)
    a.metric("Questions", len(questions))
    b.metric("Correct", correct_count(questions))
    c.metric("Incorrect", sum(q.user_answer is not None and q.user_answer != q.answer for q in questions))
    d.metric("Unanswered", unanswered_count(questions))

    st.divider()
    for i, q in enumerate(questions, 1):
        if q.user_answer is None:
            icon = "⚪"
        elif q.user_answer == q.answer:
            icon = "✅"
        else:
            icon = "❌"
        with st.expander(f"{icon} Question {i} · {q.topic}"):
            st.write(q.prompt)
            st.write(f"**Your answer:** {q.user_answer or 'Not answered'}")
            st.write(f"**Correct answer:** {q.answer}")
            st.write(f"**Why:** {q.explanation}")

    if st.button("🔄 Start this quiz again", type="primary", use_container_width=True):
        reset_quiz()
        st.rerun()


# ------------------------- sidebar -------------------------
with st.sidebar:
    st.markdown("# 🧠 QuizForge AI")
    st.caption("AI-powered study material → MCQ practice")
    st.divider()
    page = st.radio(
        "Navigate",
        ["Dashboard", "Upload & Analyze", "Quiz Forge", "Practice", "Analytics", "Results"],
        label_visibility="collapsed",
    )
    st.divider()
    if st.session_state.document_name:
        st.caption(f"📄 {st.session_state.document_name}")
    

pages = {
    "Dashboard": dashboard,
    "Upload & Analyze": upload_page,
    "Quiz Forge": builder_page,
    "Practice": practice_page,
    "Analytics": analytics_page,
    "Results": results_page,
}

pages[page]()
