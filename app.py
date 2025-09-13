import streamlit as st
import json
import random

PREPS = ["DI","A","DA","IN","SU","CON","PER","TRA","FRA"]

@st.cache_data
def load_cards():
    with open("cards.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    random.shuffle(data)
    return data

def render_sentence_progress(sentence_it, answers, blank_index):
    parts = sentence_it.split("___")
    out = []
    for i, part in enumerate(parts):
        out.append(part)
        if i < len(parts) - 1:
            if i < blank_index:
                out.append(" " + answers[i][0] + " ")
            else:
                out.append(" [___] " if i == blank_index else " ___ ")
    return "".join(out).replace("  ", " ")

def init_state(cards):
    if "cards" not in st.session_state:
        st.session_state.cards = cards
        st.session_state.i = 0
        st.session_state.blank_i = 0
        st.session_state.score_ok = 0
        st.session_state.score_tot = 0
        st.session_state.show_fr = False
        st.session_state.feedback = "Clique la bonne préposition."
        st.session_state.finished = False

def next_card():
    st.session_state.i += 1
    st.session_state.blank_i = 0
    st.session_state.feedback = "Clique la bonne préposition."
    if st.session_state.i >= len(st.session_state.cards):
        random.shuffle(st.session_state.cards)
        st.session_state.i = 0
        st.session_state.finished = True

def reset_game():
    random.shuffle(st.session_state.cards)
    st.session_state.i = 0
    st.session_state.blank_i = 0
    st.session_state.score_ok = 0
    st.session_state.score_tot = 0
    st.session_state.feedback = "Clique la bonne préposition."
    st.session_state.finished = False

def main():
    st.set_page_config(page_title="Jeu des prépositions italiennes", page_icon="🇮🇹", layout="centered")
    st.title("Jeu des prépositions italiennes — version web")
    st.caption("DI · A · DA · IN · SU · CON · PER · TRA/FRA — clique la bonne préposition pour remplir la phrase.")

    cards = load_cards()
    init_state(cards)

    top = st.columns([1,1,1,1])
    with top[0]:
        if st.button("🔁 Mélanger / Rejouer", use_container_width=True):
            reset_game()
    with top[1]:
        st.metric("Correct", st.session_state.score_ok)
    with top[2]:
        st.metric("Total", st.session_state.score_tot)
    with top[3]:
        st.session_state.show_fr = st.toggle("Afficher la traduction FR", value=st.session_state.show_fr)

    card = st.session_state.cards[st.session_state.i]
    it = card["it"]; fr = card["fr"]
    answers = card["answers"]; exps = card["explanations"]

    st.markdown("### Phrase")
    st.write(render_sentence_progress(it, answers, st.session_state.blank_i))
    if st.session_state.show_fr:
        st.info("FR : " + fr)

    cols = st.columns(5)
    for idx, prep in enumerate(PREPS):
        def make_onclick(p=prep):
            def _():
                bi = st.session_state.blank_i
                if bi >= len(answers):
                    return
                st.session_state.score_tot += 1
                accepted = [x.upper() for x in answers[bi]]
                if p.upper() in accepted:
                    st.session_state.score_ok += 1
                    st.session_state.feedback = f"✅ Correct : **{p.upper()}** — {exps[bi]}"
                    st.session_state.blank_i += 1
                    if st.session_state.blank_i == len(answers):
                        st.session_state.feedback += "  ↪ Clique **Carte suivante**."
                else:
                    bonne = "/".join(accepted)
                    st.session_state.feedback = f"❌ Faux. Bonne réponse : **{bonne}**. Raison : {exps[bi]}"
            return _
        with cols[idx % 5]:
            st.button(prep, on_click=make_onclick(), use_container_width=True)

    st.markdown(f"**Progression :** {st.session_state.i+1} / {len(st.session_state.cards)}  —  "
                f"**Score :** {st.session_state.score_ok} / {st.session_state.score_tot}")
    st.markdown(st.session_state.feedback)

    st.divider()
    b1, b2 = st.columns(2)
    with b1:
        if st.button("Carte suivante ▶", use_container_width=True):
            next_card()
    with b2:
        if st.button("Recommencer ce jeu", use_container_width=True):
            reset_game()

    if st.session_state.finished:
        st.success("Bravo 🎉 le paquet a été rejoué et mélangé !")

if __name__ == "__main__":
    main()
