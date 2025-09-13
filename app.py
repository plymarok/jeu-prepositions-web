import streamlit as st
import json
import random
from typing import List, Dict, Any

# -----------------------------
# Sécurité : mot de passe via Streamlit Secrets
# -----------------------------
def check_password() -> bool:
    """
    Protéger l'app avec un mot de passe stocké dans st.secrets["password"].
    - Si bon mot de passe -> l'app s'affiche.
    - Sinon -> formulaire de connexion bloquant.
    """
    SECRET = st.secrets.get("password", "")  # définir dans Settings > Secrets (Streamlit Cloud)

    # Si aucun mot de passe n'est défini côté secrets, on ne bloque pas l'accès.
    if not SECRET:
        return True

    # État d'authentification
    if "auth_ok" not in st.session_state:
        st.session_state.auth_ok = False

    if st.session_state.auth_ok:
        return True

    # Formulaire de connexion
    st.set_page_config(page_title="Accès protégé", page_icon="🔒", layout="centered")
    st.markdown("## 🔒 Accès protégé")
    st.write("Cette application est protégée. Entrez le **mot de passe** pour continuer.")

    with st.form("login", clear_on_submit=False):
        pw = st.text_input("Mot de passe", type="password")
        submit = st.form_submit_button("Entrer")

    if submit:
        if pw == SECRET:
            st.session_state.auth_ok = True
            st.experimental_rerun()
        else:
            st.error("Mot de passe incorrect.")
    st.stop()  # Bloque l'app tant que non authentifié


# -----------------------------
# Données : chargement des cartes
# -----------------------------
def load_cards() -> List[Dict[str, Any]]:
    """
    Charge les cartes depuis :
    1) st.secrets["cards_json"] si présent (JSON sous forme de texte)  -> pratique pour cacher les données.
    2) sinon depuis le fichier local 'cards.json' (format JSON).
    """
    # Option 1 : cartes dans les Secrets (texte JSON)
    if "cards_json" in st.secrets:
        try:
            data = json.loads(st.secrets["cards_json"])
            if isinstance(data, list):
                random.shuffle(data)
                return data
        except Exception as e:
            st.warning(f"Impossible de lire 'cards_json' dans les Secrets : {e}")

    # Option 2 : fichier local
    try:
        with open("cards.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            raise ValueError("Le contenu de cards.json doit être une liste d'objets.")
        random.shuffle(data)
        return data
    except FileNotFoundError:
        st.error("❌ Fichier 'cards.json' introuvable. Place-le à la racine du dépôt ou fournis 'cards_json' dans les Secrets.")
        st.stop()
    except Exception as e:
        st.error(f"❌ Erreur en lisant 'cards.json' : {e}")
        st.stop()


# -----------------------------
# Utilitaires d'affichage
# -----------------------------
def render_sentence_progress(sentence_it: str, answers: List[List[str]], blank_index: int) -> str:
    """
    Affiche la phrase avec les blancs :
    - Blancs déjà trouvés : remplis avec la bonne préposition (1re option).
    - Blanc courant : [___]
    - Blancs futurs : ___
    """
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


def init_state(cards: List[Dict[str, Any]]) -> None:
    if "cards" not in st.session_state:
        st.session_state.cards = cards
        st.session_state.i = 0
        st.session_state.blank_i = 0
        st.session_state.score_ok = 0
        st.session_state.score_tot = 0
        st.session_state.show_fr = False
        st.session_state.feedback = "Clique la bonne préposition."
        st.session_state.finished = False


def next_card() -> None:
    st.session_state.i += 1
    st.session_state.blank_i = 0
    st.session_state.feedback = "Clique la bonne préposition."
    if st.session_state.i >= len(st.session_state.cards):
        random.shuffle(st.session_state.cards)
        st.session_state.i = 0
        st.session_state.finished = True


def reset_game() -> None:
    random.shuffle(st.session_state.cards)
    st.session_state.i = 0
    st.session_state.blank_i = 0
    st.session_state.score_ok = 0
    st.session_state.score_tot = 0
    st.session_state.feedback = "Clique la bonne préposition."
    st.session_state.finished = False


# -----------------------------
# Application
# -----------------------------
PREPS = ["DI", "A", "DA", "IN", "SU", "CON", "PER", "TRA", "FRA"]

def main():
    # Sécurité
    if not check_password():
        return

    st.set_page_config(page_title="Jeu des prépositions italiennes", page_icon="🇮🇹", layout="centered")
    st.title("Jeu des prépositions italiennes — version web")
    st.caption("DI · A · DA · IN · SU · CON · PER · TRA/FRA — clique la bonne préposition pour remplir la phrase.")

    cards = load_cards()
    init_state(cards)

    # Barre haute
    c1, c2, c3, c4 = st.columns([1, 1, 1, 1])
    with c1:
        if st.button("🔁 Mélanger / Rejouer", use_container_width=True):
            reset_game()
    with c2:
        st.metric("Correct", st.session_state.score_ok)
    with c3:
        st.metric("Total", st.session_state.score_tot)
    with c4:
        st.session_state.show_fr = st.toggle("Afficher la traduction FR", value=st.session_state.show_fr)

    # Carte courante
    card = st.session_state.cards[st.session_state.i]
    it: str = card["it"]
    fr: str = card["fr"]
    answers: List[List[str]] = card["answers"]       # ex: [["A"],["IN"]] ; pour TRA/FRA -> ["TRA","FRA"]
    exps: List[str] = card["explanations"]

    st.markdown("### Phrase")
    st.write(render_sentence_progress(it, answers, st.session_state.blank_i))
    if st.session_state.show_fr:
        st.info("FR : " + fr)

    # Grille de boutons (prépositions)
    cols = st.columns(5)
    for idx, prep in enumerate(PREPS):
        def make_onclick(p=prep):
            def _():
                bi = st.session_state.blank_i
                if bi >= len(answers):  # rien à faire si tous les blancs de la carte sont remplis
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

    # Pied de page : progression + actions
    st.markdown(f"**Progression :** {st.session_state.i+1} / {len(st.session_state.cards)}  —  "
                f"**Score :** {st.session_state.score_ok} / {st.session_state.score_tot}")
    st.markdown(st.session_state.feedback)

    st.divider()
    a, b = st.columns(2)
    with a:
        if st.button("Carte suivante ▶", use_container_width=True):
            next_card()
    with b:
        if st.button("Recommencer ce jeu", use_container_width=True):
            reset_game()

    if st.session_state.finished:
        st.success("Bravo 🎉 le paquet a été rejoué et mélangé !")


if __name__ == "__main__":
    main()
