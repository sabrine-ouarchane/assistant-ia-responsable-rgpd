def mode_degrade(question: str):
    """Retourne une reponse de secours si Groq est indisponible."""
    print('[Mode degrade] Groq indisponible...')

    q = question.lower()

    # Dictionnaire : mot-cle -> reponse contextualisee
    reponses = [
        (["résume", "resume", "resumé", "synthèse", "synthese"],
         "Je ne suis pas en mesure de produire un résumé sur ce sujet pour le moment, "
         "car le service IA est temporairement indisponible. "
         "Je vous recommande de consulter vos supports de cours ou de réessayer dans quelques minutes."),

        (["explique", "expliquer", "c'est quoi", "qu'est-ce que", "definition", "définition", "définir"],
         "Je ne peux pas vous fournir d'explication détaillée sur ce sujet en ce moment, "
         "le service IA est temporairement hors ligne. "
         "Consultez vos notes de cours ou votre manuel, et réessayez un peu plus tard."),

        (["aide", "aider", "aidez", "besoin", "comment faire", "comment"],
         "Je ne suis pas en mesure de vous aider sur cette demande pour l'instant, "
         "le service IA rencontre une interruption temporaire. "
         "Vous pouvez consulter vos ressources pédagogiques ou réessayer dans quelques minutes."),

        (["calcul", "calculer", "formule", "équation", "equation", "résoudre", "resoudre"],
         "Je ne peux pas effectuer ce calcul ou résoudre cette équation pour le moment, "
         "le service IA est temporairement indisponible. "
         "Référez-vous à votre cours de mathématiques ou réessayez plus tard."),

        (["programme", "code", "algorithme", "algo", "fonction", "python", "java", "c++"],
         "Je ne suis pas en mesure de générer ou corriger du code en ce moment, "
         "le service IA est temporairement hors ligne. "
         "Consultez la documentation officielle du langage concerné ou réessayez plus tard."),

        (["définition", "definition", "signifie", "signification", "veut dire"],
         "Je ne peux pas vous fournir cette définition pour le moment, "
         "le service IA est temporairement indisponible. "
         "Consultez votre glossaire de cours ou réessayez dans quelques minutes."),

        (["compare", "comparer", "différence", "difference", "versus", " vs "],
         "Je ne suis pas en mesure d'effectuer cette comparaison pour le moment, "
         "le service IA rencontre une interruption temporaire. "
         "Consultez vos supports de cours ou réessayez plus tard."),

        (["réseau", "reseau", "protocole", "tcp", "ip", "http", "dns"],
         "Je ne peux pas répondre à cette question sur les réseaux pour le moment, "
         "le service IA est temporairement indisponible. "
         "Consultez votre cours de réseaux informatiques ou réessayez dans quelques minutes."),

        (["base de données", "base de donnees", "sql", "requête", "requete", "table", "sgbd"],
         "Je ne suis pas en mesure de répondre à cette question sur les bases de données pour l'instant, "
         "le service IA est hors ligne temporairement. "
         "Référez-vous à votre cours de bases de données ou réessayez plus tard."),
    ]

    for mots_cles, reponse in reponses:
        if any(mot in q for mot in mots_cles):
            return reponse, "degrade_local"

    # Réponse générique améliorée si aucun mot-clé reconnu
    sujet = question.strip().rstrip("?").strip()
    if len(sujet) > 60:
        sujet = sujet[:57] + "..."
    return (
        f"Je ne suis pas en mesure de répondre à votre question concernant "
        f"\"{sujet}\" pour le moment, car le service IA est temporairement indisponible. "
        f"Veuillez consulter vos supports de cours ou réessayer dans quelques minutes."
    ), "degrade_fallback"
