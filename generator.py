import re
from collections import Counter

from models.quiz import Question
from services.gemini import enabled, extract_json, generate_text


def _topic_for_question(index: int, topics: list[str]) -> str:
    return topics[index % len(topics)] if topics else "General"


def _local_generate(text: str, topics: list[str], count: int, difficulty: str):
    sentences = [
        s.strip()
        for s in re.split(r"(?<=[.!?])\s+", text)
        if len(s.strip()) >= 45
    ]

    questions = []
    used = set()

    for sentence in sentences:
        words = re.findall(r"\b[A-Za-z][A-Za-z'-]{4,}\b", sentence)
        if len(words) < 5:
            continue
        answer = max(words, key=len)
        prompt = re.sub(
            rf"\b{re.escape(answer)}\b",
            "_____",
            sentence,
            count=1,
            flags=re.I,
        )
        if prompt in used:
            continue
        used.add(prompt)
        pool = [w for w in words if w.lower() != answer.lower()]
        distractors = []
        for w in pool:
            if w not in distractors:
                distractors.append(w)
            if len(distractors) == 3:
                break
        while len(distractors) < 3:
            distractors.append("Not specified")
        options = [answer] + distractors[:3]
        questions.append(
            Question(
                prompt=f"Complete the statement from the study material:\n\n{prompt}",
                options=options,
                answer=answer,
                explanation="The answer is taken directly from the uploaded study material.",
                topic=_topic_for_question(len(questions), topics),
                difficulty=difficulty,
            )
        )
        if len(questions) >= count:
            break

    return questions


def generate_quiz(text: str, topics: list[str], count: int, difficulty: str):
    if not enabled():
        return _local_generate(text, topics, count, difficulty), "Local fallback"

    context = text[:50000]
    topic_text = ", ".join(topics) if topics else "All important topics"

    prompt = f"""
You are QuizForge AI, an expert assessment designer.

Create exactly {count} high-quality multiple-choice questions from the study material below.
Difficulty: {difficulty}
Focus topics: {topic_text}

Rules:
- Questions must be answerable from the material.
- Test understanding, application, relationships, definitions, or important details.
- Avoid trivial wording and duplicate questions.
- Exactly four options per question.
- Exactly one correct option.
- Correct answer must be represented by its full option text.
- Provide a concise explanation grounded in the material.
- Assign a short topic label to every question.
- Do not reveal the answer inside the question.
- Return ONLY valid JSON. No Markdown.

JSON format:
{{
  "questions": [
    {{
      "question": "...",
      "options": ["...", "...", "...", "..."],
      "correct_answer": "...",
      "explanation": "...",
      "topic": "..."
    }}
  ]
}}

STUDY MATERIAL:
----------------
{context}
----------------
"""

    raw = generate_text(prompt)
    data = extract_json(raw)
    raw_questions = data.get("questions", []) if isinstance(data, dict) else []

    result = []
    seen = set()

    for item in raw_questions:
        if not isinstance(item, dict):
            continue
        question = str(item.get("question", "")).strip()
        options = item.get("options")
        answer = str(item.get("correct_answer", "")).strip()
        explanation = str(item.get("explanation", "")).strip()
        topic = str(item.get("topic", "General")).strip() or "General"

        if not question or not isinstance(options, list) or len(options) != 4:
            continue
        options = [str(x).strip() for x in options]
        if len(set(x.lower() for x in options)) != 4:
            continue
        if answer not in options:
            # Be tolerant of case-only differences.
            match = next((x for x in options if x.lower() == answer.lower()), None)
            if match:
                answer = match
            else:
                continue
        key = question.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(
            Question(
                prompt=question,
                options=options,
                answer=answer,
                explanation=explanation,
                topic=topic,
                difficulty=difficulty,
            )
        )
        if len(result) == count:
            break

    if len(result) < count:
        raise RuntimeError(
            f"Gemini returned only {len(result)} valid questions out of {count}. Please generate again."
        )

    return result, "Gemini AI"


def analyze_material(text: str, filename: str):
    words = re.findall(r"\b\w+\b", text)
    sentences = [s for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
    common = Counter(
        w.lower()
        for w in words
        if len(w) >= 5 and w.isalpha()
    )
    keywords = [w for w, _ in common.most_common(12)]
    title = re.sub(r"\.[^.]+$", "", filename).replace("_", " ").replace("-", " ").strip().title()
    if not title:
        title = "Study Material"
    return {
        "title": title,
        "topics": keywords[:8] or ["General"],
        "concepts": keywords[:10],
        "words": len(words),
        "sentences": len(sentences),
        "difficulty": "Adaptive",
    }
