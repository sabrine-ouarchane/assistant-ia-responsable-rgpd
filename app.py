from flask import Flask, render_template, request, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from groq import Groq
from degrade import mode_degrade
import database
import rgpd
import os
import datetime

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY must be set in .env for Flask session security")

app = Flask(__name__)
app.secret_key = SECRET_KEY
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

database.init_db()


def demarrer_chat_session():
    """Démarre une nouvelle session de chat — réinitialise le timestamp."""
    session["chat_started_at"] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def demander_ia(question, historique_conversation=None):
    messages = [
        {
            "role": "system",
            "content": (
                "Tu es un assistant pedagogique pour etudiants de l'ENSA "
                "Beni Mellal. Reponds en francais, de maniere claire et concise."
            ),
        }
    ]

    for row in historique_conversation or []:
        messages.append({"role": "user", "content": row[1]})
        messages.append({"role": "assistant", "content": row[2]})

    messages.append({"role": "user", "content": question})

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            max_tokens=500,
        )
        return response.choices[0].message.content, "groq_cloud"
    except Exception as e:
        print("ERREUR Groq :", e)
        reponse, source = mode_degrade(question)
        return reponse, source


def conditions_acceptees():
    user = utilisateur_courant()
    if user is None:
        return False
    acceptees = bool(user["terms_accepted"])
    session["terms_accepted"] = acceptees
    return acceptees


def utilisateur_courant():
    email = session.get("user_email")
    if not email:
        return None
    return database.get_utilisateur_par_email(email)


def est_admin():
    user = utilisateur_courant()
    return user is not None and user["role"] == "admin"


# ── Nouvelle discussion ──────────────────────────────────────────────────
@app.route("/new-chat")
def new_chat():
    """Réinitialise le timestamp de session → chat vide."""
    if "user" not in session:
        return redirect(url_for("login"))
    demarrer_chat_session()
    return redirect(url_for("index"))


# ── Admin ────────────────────────────────────────────────────────────────
@app.route("/admin")
def admin():
    if "user" not in session:
        return redirect(url_for("login"))
    if not est_admin():
        return redirect(url_for("index"))
    stats = database.get_user_stats()
    return render_template("admin.html", stats=stats)


# ── Index / Chat ─────────────────────────────────────────────────────────
@app.route("/", methods=["GET", "POST"])
def index():
    if "user" not in session:
        return redirect(url_for("login"))
    if not conditions_acceptees():
        return redirect(url_for("conditions"))

    reponse = None
    alerte_rgpd = False
    user = utilisateur_courant()
    if user is None:
        session.clear()
        return redirect(url_for("login"))

    # Initialiser le chat si absent (session persistée sans login)
    if not session.get("chat_started_at"):
        demarrer_chat_session()

    historique = database.get_historique_chronologique(user["id"])
    chat_started_at = session.get("chat_started_at")
    conversation = (
        database.get_historique_depuis(user["id"], chat_started_at)
        if chat_started_at
        else []
    )

    if request.method == "POST":
        question = request.form.get("question", "").strip()
        type_donnee = rgpd.detecter_donnee_sensible(question)

        if not question:
            pass
        elif type_donnee:
            alerte_rgpd = True
            reponse = (
                f"Votre demande contient une donnee sensible detectee "
                f"({type_donnee}). Veuillez reformuler sans inclure de donnees "
                f"personnelles."
            )
            database.sauvegarder(question, reponse, "alerte_rgpd", user["id"])
        else:
            contexte_recent = conversation[-8:]
            reponse, source = demander_ia(question, contexte_recent)
            database.sauvegarder(question, reponse, source, user["id"])

        return redirect(url_for("index"))

    return render_template(
        "index.html",
        alerte_rgpd=alerte_rgpd,
        conversation=conversation,
        historique_sidebar=list(reversed(historique[-6:])),
        is_admin=est_admin(),
    )


@app.route("/historique")
def historique():
    if "user" not in session:
        return redirect(url_for("login"))
    if not conditions_acceptees():
        return redirect(url_for("conditions"))
    user = utilisateur_courant()
    data = database.get_historique(user["id"])
    return render_template("historique.html", historique=data)


@app.route("/discussion/<int:discussion_id>/supprimer", methods=["POST"])
def supprimer_discussion(discussion_id):
    if "user" not in session:
        return redirect(url_for("login"))
    if not conditions_acceptees():
        return redirect(url_for("conditions"))
    user = utilisateur_courant()
    database.supprimer_discussion(discussion_id, user["id"])
    destination = request.form.get("next")
    if destination == "historique":
        return redirect(url_for("historique"))
    return redirect(url_for("index"))


@app.route("/profil", methods=["GET", "POST"])
def profil():
    if "user" not in session:
        return redirect(url_for("login"))
    if not conditions_acceptees():
        return redirect(url_for("conditions"))

    user = utilisateur_courant()
    if user is None:
        session.clear()
        return redirect(url_for("login"))

    erreur = None
    succes = None

    if request.method == "POST":
        nom = request.form.get("nom", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")

        if not nom or not email:
            erreur = "Le nom et l'email sont obligatoires."
        elif password and len(password) < 8:
            erreur = "Le mot de passe doit contenir au moins 8 caracteres."
        elif password and password != confirm:
            erreur = "Les mots de passe ne correspondent pas."
        else:
            password_hash = generate_password_hash(password) if password else None
            success = database.mettre_a_jour_utilisateur(user["id"], nom, email, password_hash)
            if success:
                session["user"] = nom
                session["user_email"] = email
                succes = "Votre profil a ete mis a jour."
                user = utilisateur_courant()
            else:
                erreur = "Cet email est deja utilise."

    return render_template("profil.html", user=user, erreur=erreur, succes=succes)


@app.route("/conditions", methods=["GET", "POST"])
def conditions():
    if "user" not in session:
        return redirect(url_for("login"))

    erreur = None
    conditions_list = [
        "Utiliser l'assistant uniquement dans un cadre pedagogique et academique.",
        "Ne jamais saisir de donnees personnelles sensibles, mots de passe ou informations confidentielles.",
        "Verifier les reponses de l'IA avant toute reutilisation dans un devoir, rapport ou decision importante.",
        "Respecter la legislation marocaine, le RGPD et les regles internes de l'ENSA Beni Mellal.",
        "Ne pas utiliser la plateforme pour generer du contenu illicite, offensant ou trompeur.",
        "Accepter que les echanges soient journalises localement pour le suivi et l'historique.",
    ]

    if request.method == "POST":
        if request.form.get("accept_terms") == "yes":
            user_id = session.get("user_id")
            if user_id:
                database.definir_acceptation_conditions(user_id, True)
            session["terms_accepted"] = True
            demarrer_chat_session()
            return redirect(url_for("index"))
        erreur = "Vous devez accepter les conditions d'utilisation pour acceder a l'application."

    return render_template("conditions.html", erreur=erreur, conditions_list=conditions_list)


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user" in session:
        return redirect(url_for("index" if conditions_acceptees() else "conditions"))
    erreur = None
    email_saisi = ""
    if request.method == "POST":
        email_saisi = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = database.get_utilisateur_par_email(email_saisi)
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["user"] = user["nom"]
            session["user_email"] = email_saisi
            session["terms_accepted"] = bool(user["terms_accepted"])
            demarrer_chat_session()
            return redirect(url_for("index" if session["terms_accepted"] else "conditions"))
        erreur = "Email ou mot de passe incorrect."
    return render_template("login.html", erreur=erreur, email_saisi=email_saisi)


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if "user" in session:
        return redirect(url_for("index" if conditions_acceptees() else "conditions"))
    erreur = None
    nom_saisi = ""
    email_saisi = ""
    if request.method == "POST":
        nom_saisi = request.form.get("nom", "").strip()
        email_saisi = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")
        if not nom_saisi or not email_saisi or not password:
            erreur = "Tous les champs sont obligatoires."
        elif len(password) < 8:
            erreur = "Le mot de passe doit contenir au moins 8 caracteres."
        elif password != confirm:
            erreur = "Les mots de passe ne correspondent pas."
        else:
            password_hash = generate_password_hash(password)
            success = database.creer_utilisateur(nom_saisi, email_saisi, password_hash)
            if success:
                user = database.get_utilisateur_par_email(email_saisi)
                if user:
                    session["user_id"] = user["id"]
                session["user"] = nom_saisi
                session["user_email"] = email_saisi
                session["terms_accepted"] = False
                demarrer_chat_session()
                return redirect(url_for("conditions"))
            erreur = "Cet email est deja utilise."
    return render_template("signup.html", erreur=erreur, nom_saisi=nom_saisi, email_saisi=email_saisi)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)
