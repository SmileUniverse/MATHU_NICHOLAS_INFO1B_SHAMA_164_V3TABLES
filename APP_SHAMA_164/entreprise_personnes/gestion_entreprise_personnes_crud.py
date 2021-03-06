"""
    Fichier : gestion_entreprise_personnes_crud.py
    Auteur : OM 2021.05.01
    Gestions des "routes" FLASK et des données pour l'association entre les entreprise et les personnes.
"""
from pathlib import Path

from flask import redirect
from flask import request
from flask import session
from flask import url_for

from APP_SHAMA_164.database.database_tools import DBconnection
from APP_SHAMA_164.erreurs.exceptions import *

"""
    Nom : entreprise_personnes_afficher
    Auteur : OM 2021.05.01
    Définition d'une "route" /entreprise_personnes_afficher
    
    But : Afficher les entreprise avec les personnes associés pour chaque film.
    
    Paramètres : id_personnes_sel = 0 >> tous les entreprise.
                 id_personnes_sel = "n" affiche le film dont l'id est "n"
                 
"""


@app.route("/entreprise_personnes_afficher/<int:id_entreprise_sel>", methods=['GET', 'POST'])
def entreprise_personnes_afficher(id_entreprise_sel):
    print(" entreprise_personnes_afficher id_entreprise_sel ", id_entreprise_sel)
    if request.method == "GET":
        try:
            with DBconnection() as mc_afficher:
                strsql_personnes_entreprise_afficher_data = """SELECT id_entreprise, nom_entreprise, num_entreprise, email_entreprise,
                                                        GROUP_CONCAT(nom_personnes) as EntreprisePersonnes FROM  t_e_personnes
                                                        Right JOIN t_entreprise ent ON ent.id_entreprise = t_e_personnes.fk_entreprise 
                                                        Left JOIN t_personnes pers ON pers.id_personnes = t_e_personnes.fk_personnes
                                                        GROUP BY id_entreprise"""
                if id_entreprise_sel == 0:
                    # le paramètre 0 permet d'afficher tous les entreprise
                    # Sinon le paramètre représente la valeur de l'id du film
                    mc_afficher.execute(strsql_personnes_entreprise_afficher_data)
                else:
                    # Constitution d'un dictionnaire pour associer l'id du film sélectionné avec un nom de variable
                    valeur_id_entreprise_selected_dictionnaire = {"value_id_entreprise_selected": id_entreprise_sel}
                    # En MySql l'instruction HAVING fonctionne comme un WHERE... mais doit être associée à un GROUP BY
                    # L'opérateur += permet de concaténer une nouvelle valeur à la valeur de gauche préalablement définie.
                    strsql_personnes_entreprise_afficher_data += """ HAVING id_entreprise= %(value_id_entreprise_selected)s"""

                    mc_afficher.execute(strsql_personnes_entreprise_afficher_data, valeur_id_entreprise_selected_dictionnaire)

                # Récupère les données de la requête.
                data_personnes_entreprise_afficher = mc_afficher.fetchall()
                print("data_personnes ", data_personnes_entreprise_afficher, " Type : ", type(data_personnes_entreprise_afficher))

                # Différencier les messages.
                if not data_personnes_entreprise_afficher and id_entreprise_sel == 0:
                    flash("""La table "t_entreprise" est vide. !""", "warning")
                elif not data_personnes_entreprise_afficher and id_entreprise_sel > 0:
                    # Si l'utilisateur change l'id_adresse dans l'URL et qu'il ne correspond à aucun film
                    flash(f"L'Entreprise {id_entreprise_sel} demandé n'existe pas !!", "warning")
                else:
                    flash(f"Les Entreprises et leur personnel son affichés !!", "success")

        except Exception as Exception_entreprise_personnes_afficher:
            raise ExceptionEntreprisePersonnesAfficher(f"fichier : {Path(__file__).name}  ;  {entreprise_personnes_afficher.__name__} ;"
                                               f"{Exception_entreprise_personnes_afficher}")

    print("entreprise_personnes_afficher  ", data_personnes_entreprise_afficher)
    # Envoie la page "HTML" au serveur.
    return render_template("entreprise_personnes/entreprise_personnes_afficher.html", data=data_personnes_entreprise_afficher)


"""
    nom: edit_entreprise_personnes_selected
    On obtient un objet "objet_dumpbd"

    Récupère la liste de tous les personnes du film sélectionné par le bouton "MODIFIER" de "entreprise_personnes_afficher.html"
    
    Dans une liste déroulante particulière (tags-selector-tagselect), on voit :
    1) Tous les personnes contenus dans la "t_genre".
    2) Les personnes attribués au film selectionné.
    3) Les personnes non-attribués au film sélectionné.

    On signale les erreurs importantes

"""


@app.route("/edit_entreprise_personnes_selected", methods=['GET', 'POST'])
def edit_entreprise_personnes_selected():
    if request.method == "GET":
        try:
            with DBconnection() as mc_afficher:
                strsql_personnes_afficher = """SELECT id_personnes, nom_personnes
                                            FROM t_personnes ORDER BY id_personnes ASC"""
                mc_afficher.execute(strsql_personnes_afficher)
            data_personnes_all = mc_afficher.fetchall()
            print("dans edit_entreprise_personnes_selected ---> data_personnes_all", data_personnes_all)

            # Récupère la valeur de "id_adresse" du formulaire html "entreprise_personnes_afficher.html"
            # l'utilisateur clique sur le bouton "Modifier" et on récupère la valeur de "id_adresse"
            # grâce à la variable "id_entreprise_personnes_edit_html" dans le fichier "entreprise_personnes_afficher.html"
            # href="{{ url_for('edit_entreprise_personnes_selected', id_entreprise_personnes_edit_html=row.id_adresse) }}"
            id_entreprise_personnes_edit = request.values['id_entreprise_personnes_edit_html']

            # Mémorise l'id du film dans une variable de session
            # (ici la sécurité de l'application n'est pas engagée)
            # il faut éviter de stocker des données sensibles dans des variables de sessions.
            session['session_id_entreprise_personnes_edit'] = id_entreprise_personnes_edit

            # Constitution d'un dictionnaire pour associer l'id du film sélectionné avec un nom de variable
            valeur_id_entreprise_selected_dictionnaire = {"value_id_entreprise_selected": id_entreprise_personnes_edit}

            # Récupère les données grâce à 3 requêtes MySql définie dans la fonction personnes_entreprise_afficher_data
            # 1) Sélection du film choisi
            # 2) Sélection des personnes "déjà" attribués pour le film.
            # 3) Sélection des personnes "pas encore" attribués pour le film choisi.
            # ATTENTION à l'ordre d'assignation des variables retournées par la fonction "personnes_entreprise_afficher_data"
            data_personnes_entreprise_selected, data_personnes_entreprise_non_attribues, data_personnes_entreprise_attribues = \
                personnes_entreprise_afficher_data(valeur_id_entreprise_selected_dictionnaire)

            print(data_personnes_entreprise_selected)
            lst_data_entreprise_selected = [item['id_entreprise'] for item in data_personnes_entreprise_selected]
            print("lst_data_entreprise_selected  ", lst_data_entreprise_selected,
                  type(lst_data_entreprise_selected))

            # Dans le composant "tags-selector-tagselect" on doit connaître
            # les personnes qui ne sont pas encore sélectionnés.
            lst_data_personnes_entreprise_non_attribues = [item['id_personnes'] for item in data_personnes_entreprise_non_attribues]
            session['session_lst_data_personnes_entreprise_non_attribues'] = lst_data_personnes_entreprise_non_attribues
            print("lst_data_personnes_entreprise_non_attribues  ", lst_data_personnes_entreprise_non_attribues,
                  type(lst_data_personnes_entreprise_non_attribues))

            # Dans le composant "tags-selector-tagselect" on doit connaître
            # les personnes qui sont déjà sélectionnés.
            lst_data_personnes_entreprise_old_attribues = [item['id_personnes'] for item in data_personnes_entreprise_attribues]
            session['session_lst_data_personnes_entreprise_old_attribues'] = lst_data_personnes_entreprise_old_attribues
            print("lst_data_personnes_entreprise_old_attribues  ", lst_data_personnes_entreprise_old_attribues,
                  type(lst_data_personnes_entreprise_old_attribues))

            print(" data data_personnes_entreprise_selected", data_personnes_entreprise_selected, "type ", type(data_personnes_entreprise_selected))
            print(" data data_personnes_entreprise_non_attribues ", data_personnes_entreprise_non_attribues, "type ",
                  type(data_personnes_entreprise_non_attribues))
            print(" data_personnes_entreprise_attribues ", data_personnes_entreprise_attribues, "type ",
                  type(data_personnes_entreprise_attribues))

            # Extrait les valeurs contenues dans la table "t_genres", colonne "nom_personnes"
            # Le composant javascript "tagify" pour afficher les tags n'a pas besoin de l'id_genre
            lst_data_personnes_entreprise_non_attribues = [item['nom_personnes'] for item in data_personnes_entreprise_non_attribues]
            print("lst_all_personnes gf_edit_entreprise_personnes_selected ", lst_data_personnes_entreprise_non_attribues,
                  type(lst_data_personnes_entreprise_non_attribues))

        except Exception as Exception_edit_entreprise_personnes_selected:
            raise ExceptionEditPersonnesEntrepriseSelected(f"fichier : {Path(__file__).name}  ;  "
                                                 f"{edit_entreprise_personnes_selected.__name__} ; "
                                                 f"{Exception_edit_entreprise_personnes_selected}")

    return render_template("entreprise_personnes/entreprise_personnes_modifier_tags_dropbox.html",
                           data_personnes=data_personnes_all,
                           data_entreprise_selected=data_personnes_entreprise_selected,
                           data_personnes_attribues=data_personnes_entreprise_attribues,
                           data_personnes_non_attribues=data_personnes_entreprise_non_attribues)


"""
    nom: update_personnes_entreprise_selected

    Récupère la liste de tous les personnes du film sélectionné par le bouton "MODIFIER" de "entreprise_personnes_afficher.html"
    
    Dans une liste déroulante particulière (tags-selector-tagselect), on voit :
    1) Tous les personnes contenus dans la "t_genre".
    2) Les personnes attribués au film selectionné.
    3) Les personnes non-attribués au film sélectionné.

    On signale les erreurs importantes
"""


@app.route("/update_personnes_entreprise_selected", methods=['GET', 'POST'])
def update_personnes_entreprise_selected():
    if request.method == "POST":
        try:
            # Récupère l'id du film sélectionné
            id_entreprise_selected = session['session_id_entreprise_personnes_edit']
            print("session['session_id_entreprise_personnes_edit'] ", session['session_id_entreprise_personnes_edit'])

            # Récupère la liste des personnes qui ne sont pas associés au film sélectionné.
            old_lst_data_personnes_entreprise_non_attribues = session['session_lst_data_personnes_entreprise_non_attribues']
            print("old_lst_data_personnes_entreprise_non_attribues ", old_lst_data_personnes_entreprise_non_attribues)

            # Récupère la liste des personnes qui sont associés au film sélectionné.
            old_lst_data_personnes_entreprise_attribues = session['session_lst_data_personnes_entreprise_old_attribues']
            print("old_lst_data_personnes_entreprise_old_attribues ", old_lst_data_personnes_entreprise_attribues)

            # Effacer toutes les variables de session.
            session.clear()

            # Récupère ce que l'utilisateur veut modifier comme personnes dans le composant "tags-selector-tagselect"
            # dans le fichier "genres_films_modifier_tags_dropbox.html"
            new_lst_str_personnes_entreprise = request.form.getlist('name_select_tags')
            print("new_lst_str_personnes_entreprise ", new_lst_str_personnes_entreprise)

            # OM 2021.05.02 Exemple : Dans "name_select_tags" il y a ['4','65','2']
            # On transforme en une liste de valeurs numériques. [4,65,2]
            new_lst_int_personnes_entreprise_old = list(map(int, new_lst_str_personnes_entreprise))
            print("new_lst_personnes_entreprise ", new_lst_int_personnes_entreprise_old, "type new_lst_personnes_entreprise ",
                  type(new_lst_int_personnes_entreprise_old))

            # Pour apprécier la facilité de la vie en Python... "les ensembles en Python"
            # https://fr.wikibooks.org/wiki/Programmation_Python/Ensembles
            # OM 2021.05.02 Une liste de "id_genre" qui doivent être effacés de la table intermédiaire "t_genre_film".
            lst_diff_personnes_delete_b = list(set(old_lst_data_personnes_entreprise_attribues) -
                                            set(new_lst_int_personnes_entreprise_old))
            print("lst_diff_personnes_delete_b ", lst_diff_personnes_delete_b)

            # Une liste de "id_genre" qui doivent être ajoutés à la "t_genre_film"
            lst_diff_personnes_insert_a = list(
                set(new_lst_int_personnes_entreprise_old) - set(old_lst_data_personnes_entreprise_attribues))
            print("lst_diff_personnes_insert_a ", lst_diff_personnes_insert_a)

            # SQL pour insérer une nouvelle association entre
            # "fk_film"/"id_adresse" et "fk_genre"/"id_genre" dans la "t_genre_film"
            strsql_insert_personnes_entreprise = """INSERT INTO t_e_personnes (id_e_personnes, fk_personnes, fk_entreprise)
                                                    VALUES (NULL, %(value_fk_personnes)s, %(value_fk_entreprise)s)"""

            # SQL pour effacer une (des) association(s) existantes entre "id_adresse" et "id_genre" dans la "t_genre_film"
            strsql_delete_personnes_entreprise = """DELETE FROM t_e_personnes WHERE fk_personnes = %(value_fk_personnes)s AND fk_entreprise = %(value_fk_entreprise)s"""

            with DBconnection() as mconn_bd:
                # Pour le film sélectionné, parcourir la liste des personnes à INSÉRER dans la "t_genre_film".
                # Si la liste est vide, la boucle n'est pas parcourue.
                for id_personnes_ins in lst_diff_personnes_insert_a:
                    # Constitution d'un dictionnaire pour associer l'id du film sélectionné avec un nom de variable
                    # et "id_personnes_ins" (l'id du genre dans la liste) associé à une variable.
                    valeurs_entreprise_sel_personnes_sel_dictionnaire = {"value_fk_entreprise": id_entreprise_selected,
                                                               "value_fk_personnes": id_personnes_ins}

                    mconn_bd.execute(strsql_insert_personnes_entreprise, valeurs_entreprise_sel_personnes_sel_dictionnaire)

                # Pour le film sélectionné, parcourir la liste des personnes à EFFACER dans la "t_genre_film".
                # Si la liste est vide, la boucle n'est pas parcourue.
                for id_personnes_del in lst_diff_personnes_delete_b:
                    # Constitution d'un dictionnaire pour associer l'id du film sélectionné avec un nom de variable
                    # et "id_personnes_del" (l'id du genre dans la liste) associé à une variable.
                    valeurs_entreprise_sel_personnes_sel_dictionnaire = {"value_fk_entreprise": id_entreprise_selected,
                                                               "value_fk_personnes": id_personnes_del}

                    # Du fait de l'utilisation des "context managers" on accède au curseur grâce au "with".
                    # la subtilité consiste à avoir une méthode "execute" dans la classe "DBconnection"
                    # ainsi quand elle aura terminé l'insertion des données le destructeur de la classe "DBconnection"
                    # sera interprété, ainsi on fera automatiquement un commit
                    mconn_bd.execute(strsql_delete_personnes_entreprise, valeurs_entreprise_sel_personnes_sel_dictionnaire)

        except Exception as Exception_update_personnes_entreprise_selected:
            raise ExceptionUpdatePersonnesEntrepriseSelected(f"fichier : {Path(__file__).name}  ;  "
                                                   f"{update_personnes_entreprise_selected.__name__} ; "
                                                   f"{Exception_update_personnes_entreprise_selected}")

    # Après cette mise à jour de la table intermédiaire "t_genre_film",
    # on affiche les entreprise et le(urs) genre(s) associé(s).
    return redirect(url_for('entreprise_personnes_afficher', id_entreprise_sel=id_entreprise_selected))


"""
    nom: personnes_entreprise_afficher_data

    Récupère la liste de tous les personnes du film sélectionné par le bouton "MODIFIER" de "entreprise_personnes_afficher.html"
    Nécessaire pour afficher tous les "TAGS" des personnes, ainsi l'utilisateur voit les personnes à disposition

    On signale les erreurs importantes
"""


def personnes_entreprise_afficher_data(valeur_id_entreprise_selected_dict):
    print("valeur_id_entreprise_selected_dict...", valeur_id_entreprise_selected_dict)
    try:

        strsql_entreprise_selected = """SELECT id_entreprise, nom_entreprise, num_entreprise, email_entreprise, GROUP_CONCAT(id_personnes) as EntreprisePersonnes FROM t_e_personnes
                                    INNER JOIN t_entreprise ON t_entreprise.id_entreprise = t_e_personnes.fk_entreprise
                                    INNER JOIN t_personnes ON t_personnes.id_personnes = t_e_personnes.fk_personnes
                                    WHERE id_entreprise = %(value_id_entreprise_selected)s"""

        strsql_personnes_entreprise_non_attribues = """SELECT id_personnes, nom_personnes FROM t_personnes WHERE id_personnes not in(SELECT id_personnes as idEntreprisePersonnes FROM t_e_personnes
                                    INNER JOIN t_entreprise ON t_entreprise.id_entreprise = t_e_personnes.fk_entreprise
                                    INNER JOIN t_personnes ON t_personnes.id_personnes = t_e_personnes.fk_personnes
                                    WHERE id_entreprise = %(value_id_entreprise_selected)s)"""

        strsql_personnes_entreprise_attribues = """SELECT id_entreprise, id_personnes, nom_entreprise FROM t_e_personnes
                                            INNER JOIN t_entreprise ON t_entreprise.id_entreprise = t_e_personnes.fk_entreprise
                                            INNER JOIN t_personnes ON t_personnes.id_personnes = t_e_personnes.fk_personnes
                                            WHERE id_entreprise = %(value_id_entreprise_selected)s"""

        # Du fait de l'utilisation des "context managers" on accède au curseur grâce au "with".
        with DBconnection() as mc_afficher:
            # Envoi de la commande MySql
            mc_afficher.execute(strsql_personnes_entreprise_non_attribues, valeur_id_entreprise_selected_dict)
            # Récupère les données de la requête.
            data_personnes_entreprise_non_attribues = mc_afficher.fetchall()
            # Affichage dans la console
            print("personnes_entreprise_afficher_data ----> data_personnes_entreprise_non_attribues ", data_personnes_entreprise_non_attribues,
                  " Type : ",
                  type(data_personnes_entreprise_non_attribues))

            # Envoi de la commande MySql
            mc_afficher.execute(strsql_entreprise_selected, valeur_id_entreprise_selected_dict)
            # Récupère les données de la requête.
            data_entreprise_selected = mc_afficher.fetchall()
            # Affichage dans la console
            print("data_entreprise_selected  ", data_entreprise_selected, " Type : ", type(data_entreprise_selected))

            # Envoi de la commande MySql
            mc_afficher.execute(strsql_personnes_entreprise_attribues, valeur_id_entreprise_selected_dict)
            # Récupère les données de la requête.
            data_personnes_entreprise_attribues = mc_afficher.fetchall()
            # Affichage dans la console
            print("data_personnes_entreprise_attribues ", data_personnes_entreprise_attribues, " Type : ",
                  type(data_personnes_entreprise_attribues))

            # Retourne les données des "SELECT"
            return data_entreprise_selected, data_personnes_entreprise_non_attribues, data_personnes_entreprise_attribues

    except Exception as Exception_personnes_entreprise_afficher_data:
        raise ExceptionEntreprisePersonnesAfficherData(f"fichier : {Path(__file__).name}  ;  "
                                               f"{personnes_entreprise_afficher_data.__name__} ; "
                                               f"{Exception_personnes_entreprise_afficher_data}")
