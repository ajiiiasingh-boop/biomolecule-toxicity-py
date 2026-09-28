"""Quiz: ten questions, marked by grade_quiz(), +10 points per correct answer."""

import streamlit as st

from btd import progress as prog
from btd import ui
from btd.analysis import quiz_frame
from btd.data import QUIZ
from btd.scoring import grade_quiz

ui.page_header("Knowledge check", "Quiz",
               f"{len(QUIZ)} questions across the whole series. Each correct answer adds "
               "10 points to your detective score.")

result = st.session_state.get("quiz_result")

if result is None:
    with st.form("quiz"):
        for number, question in enumerate(QUIZ, start=1):
            st.caption(question["topic"].upper())
            st.radio(
                f"**{number}. {question['question']}**",
                range(len(question["options"])),
                index=None,
                format_func=lambda i, q=question: q["options"][i],
                key=f"quiz-{question['id']}",
            )
            st.space("small")
        submitted = st.form_submit_button("Submit answers", type="primary", icon=":material/send:")

    if submitted:
        answers = {q["id"]: st.session_state.get(f"quiz-{q['id']}") for q in QUIZ}
        missing = [str(n) for n, q in enumerate(QUIZ, start=1) if answers[q["id"]] is None]
        if missing:
            st.warning(f"Answer every question first. Still open: {', '.join(missing)}.",
                       icon=":material/edit:")
        else:
            result = grade_quiz(QUIZ, answers)
            prog.record_quiz(ui.progress(), result)
            st.session_state.quiz_result = result
            if result["score"] == result["total"]:
                st.session_state.celebrate_quiz = True
            st.rerun()
else:
    if st.session_state.pop("celebrate_quiz", False):
        st.balloons()
    m1, m2, m3 = st.columns(3)
    m1.metric("Score", f"{result['score']} / {result['total']}", border=True)
    m2.metric("Percentage", f"{result['percentage']}%", border=True)
    m3.metric("Points added", f"+{result['points']}", border=True)

    st.dataframe(quiz_frame(result), hide_index=True,
                 column_config={"Correct": st.column_config.CheckboxColumn("Correct")})

    st.subheader("Answers explained", anchor=False)
    for number, r in enumerate(result["results"], start=1):
        mark = ":green[:material/check_circle:]" if r["correct"] else ":orange[:material/cancel:]"
        with st.expander(f"{mark} {number}. {r['question']}", expanded=not r["correct"]):
            if not r["correct"]:
                st.markdown(f"Your answer: **{r['options'][r['chosen']]}**")
            st.markdown(f"Correct answer: **{r['options'][r['answer']]}**")
            st.write(r["explanation"])

    if st.button("Retake the quiz", icon=":material/replay:"):
        del st.session_state.quiz_result
        for q in QUIZ:
            st.session_state.pop(f"quiz-{q['id']}", None)
        st.rerun()

ui.disclaimer()
