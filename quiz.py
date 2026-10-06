def reset_answers(questions):
    for question in questions:
        question.user_answer = None


def score(questions):
    if not questions:
        return 0.0
    correct = sum(q.user_answer == q.answer for q in questions if q.user_answer is not None)
    return round(correct / len(questions) * 100, 1)


def correct_count(questions):
    return sum(q.user_answer == q.answer for q in questions if q.user_answer is not None)


def answered_count(questions):
    return sum(q.user_answer is not None for q in questions)


def unanswered_count(questions):
    return sum(q.user_answer is None for q in questions)
