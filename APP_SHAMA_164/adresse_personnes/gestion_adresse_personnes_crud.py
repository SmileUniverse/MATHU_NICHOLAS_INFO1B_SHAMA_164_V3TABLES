"""
    Fichier : gestion_adresse_personnes_crud.py
    Auteur : OM 2021.05.01
    Gestions des "routes" FLASK et des données pour l'association entre les adresse et les genres.
"""
from pathlib import Path

from flask import redirect
from flask import request
from flask import session
from flask import url_for

from APP_SHAMA_164.database.database_tools import DBconnection
from APP_SHAMA_164.erreurs.exceptions import *

"""
    Nom : adresse_personnes_afficher
    Auteur : OM 2021.05.01
    Définition d'une "route" /adresse_personnes_afficher
    
    But : Afficher les adresse avec les genres associés pour chaque film.
    
    Paramètres : id_genre_sel = 0 >> tous les adresse.
                 id_genre_sel = "n" affiche le film dont l'id est "n"
                 
"""


@app.route("/adresse_personnes_afficher/<int:id_adresse_sel>", methods=['GET', 'POST'])
def adresse_personnes_afficher(id_adresse_sel):
    print(" adresse_personnes_afficher id_adresse_sel ", id_adresse_sel)
    if request.method == "GET":
        try:
            with DBconnection() as mc_afficher:
                strsql_personnes_adresse_afficher_data = """SELECT id_adresse, Rue, Numero, Localite, 
                                                            GROUP_CONCAT(nom_personnes) as PersonnesAdresse FROM t_pers_adresse
                                                            RIGHT JOIN t_adresse ON t_adresse.id_adresse = t_pers_adresse.fk_adresse
                                                            LEFT JOIN t_personnes ON t_personnes.id_personnes = t_pers_adresse.fk_personnes
                                                            GROUP BY id_adresse"""
                if id_adresse_sel == 0:
                    # le paramètre 0 permet d'afficher tous les adresse
                    # Sinon le paramètre représente la valeur de l'id du film
                    mc_afficher.execute(strsql_personnes_adresse_afficher_data)
                else:
                    # Constitution d'un dictionnaire pour associer l'id du film sélectionné avec un nom de variable
                    valeur_id_adresse_selected_dictionnaire = {"value_id_adresse_selected": id_adresse_sel}
                    # En MySql l'instruction HAVING fonctionne comme un WHERE... mais doit être associée à un GROUP BY
                    # L'opérateur += permet de concaténer une nouvelle valeur à la valeur de gauche préalablement définie.
                    strsql_personnes_adresse_afficher_data += """ HAVING id_adresse= %(value_id_adresse_selected)s"""

                    mc_afficher.execute(strsql_personnes_adresse_afficher_data, valeur_id_adresse_selected_dictionnaire)

                # Récupère les données de la requête.
                data_personnes_adresse_afficher = mc_afficher.fetchall()
                print("data_personnes ", data_personnes_adresse_afficher, " Type : ", 
                      type(data_personnes_adresse_afficher))

                # Différencier les messages.
                if not data_personnes_adresse_afficher and id_adresse_sel == 0:
                    flash("""La table "t_adresse" est vide. !""", "warning")
                elif not data_personnes_adresse_afficher and id_adresse_sel > 0:
                    # Si l'utilisateur change l'id_adresse dans l'URL et qu'il ne correspond à aucun film
                    flash(f"L'adresse' {id_adresse_sel} demandé n'existe pas !!", "warning")
                else:
                    flash(f"Données adresse et personnes affichés !!", "success")

        except Exception as Exception_adresse_personnes_afficher:
            raise ExceptionAdressePersonnesAfficher(f"fichier : {Path(__file__).name}  ;  "
                                                    f"{adresse_personnes_afficher.__name__} ;"
                                                    f"{Exception_adresse_personnes_afficher}")

    print("adresse_personnes_afficher  ", data_personnes_adresse_afficher)
    # Envoie la page "HTML" au serveur.
    return render_template("adresse_personnes/adresse_personnes_afficher.html", data=data_personnes_adresse_afficher)


"""
    nom: edit_personnes_adresse_selected
    On obtient un objet "objet_dumpbd"

    Récupère la liste de tous les genres du film sélectionné par le bouton "MODIFIER" de "adresse_personnes_afficher.html"
    
    Dans une liste déroulante particulière (tags-selector-tagselect), on voit :
    1) Tous les genres contenus dans la "t_genre".
    2) Les genres attribués au film selectionné.
    3) Les genres non-attribués au film sélectionné.

    On signale les erreurs importantes

"""


@app.route("/edit_personnes_adresse_selected", methods=['GET', 'POST'])
def edit_personnes_adresse_selected():
    if request.method == "GET":
        try:
            with DBconnection() as mc_afficher:
                strsql_personnes_afficher = """SELECT id_personnes, nom_personnes 
                                               FROM t_personnes ORDER BY id_personnes ASC"""
                mc_afficher.execute(strsql_personnes_afficher)
            data_personnes_all = mc_afficher.fetchall()
            print("dans edit_personnes_adresse_selected ---> data_personnes_all", data_personnes_all)

            # Récupère la valeur de "id_adresse" du formulaire html "adresse_personnes_afficher.html"
            # l'utilisateur clique sur le bouton "Modifier" et on récupère la valeur de "id_adresse"
            # grâce à la variable "id_adresse_personnes_edit_html" dans le fichier "adresse_personnes_afficher.html"
            # href="{{ url_for('edit_personnes_adresse_selected', id_adresse_personnes_edit_html=row.id_adresse) }}"
            id_adresse_personnes_edit = request.values['id_adresse_personnes_edit_html']

            # Mémorise l'id du film dans une variable de session
            # (ici la sécurité de l'application n'est pas engagée)
            # il faut éviter de stocker des données sensibles dans des variables de sessions.
            session['session_id_adresse_personnes_edit'] = id_adresse_personnes_edit

            # Constitution d'un dictionnaire pour associer l'id du film sélectionné avec un nom de variable
            valeur_id_adresse_selected_dictionnaire = {"value_id_adresse_selected": id_adresse_personnes_edit}

            # Récupère les données grâce à 3 requêtes MySql définie dans la fonction personnes_adresse_afficher_data
            # 1) Sélection du film choisi
            # 2) Sélection des genres "déjà" attribués pour le film.
            # 3) Sélection des genres "pas encore" attribués pour le film choisi.
            # ATTENTION à l'ordre d'assignation des variables retournées par la fonction "personnes_adresse_afficher_data"
            data_personnes_adresse_selected, data_personnes_adresse_non_attribues, data_personnes_adresse_attribues = \
                personnes_adresse_afficher_data(valeur_id_adresse_selected_dictionnaire)

            print(data_personnes_adresse_selected)
            lst_data_adresse_selected = [item['id_adresse'] for item in data_personnes_adresse_selected]
            print("lst_data_adresse_selected  ", lst_data_adresse_selected,
                  type(lst_data_adresse_selected))

            # Dans le composant "tags-selector-tagselect" on doit connaître
            # les genres qui ne sont pas encore sélectionnés.
            lst_data_personnes_adresse_non_attribues = [item['id_personnes'] for item in data_personnes_adresse_non_attribues]
            session['session_lst_data_personnes_adresse_non_attribues'] = lst_data_personnes_adresse_non_attribues
            print("lst_data_personnes_adresse_non_attribues  ", lst_data_personnes_adresse_non_attribues,
                  type(lst_data_personnes_adresse_non_attribues))

            # Dans le composant "tags-selector-tagselect" on doit connaître
            # les genres qui sont déjà sélectionnés.
            lst_data_personnes_adresse_old_attribues = [item['id_personnes'] for item in data_personnes_adresse_attribues]
            session['session_lst_data_personnes_adresse_old_attribues'] = lst_data_personnes_adresse_old_attribues
            print("lst_data_personnes_adresse_old_attribues  ", lst_data_personnes_adresse_old_attribues,
                  type(lst_data_personnes_adresse_old_attribues))

            print(" data data_personnes_adresse_selected", data_personnes_adresse_selected, "type ", type(data_personnes_adresse_selected))
            print(" data data_personnes_adresse_non_attribues ", data_personnes_adresse_non_attribues, "type ",
                  type(data_personnes_adresse_non_attribues))
            print(" data_personnes_adresse_attribues ", data_personnes_adresse_attribues, "type ",
                  type(data_personnes_adresse_attribues))

            # Extrait les valeurs contenues dans la table "t_genres", colonne "nom_personnes"
            # Le composant javascript "tagify" pour afficher les tags n'a pas besoin de l'id_genre
            lst_data_personnes_adresse_non_attribues = [item['nom_personnes'] for item in data_personnes_adresse_non_attribues]
            print("lst_all_genres gf_edit_personnes_adresse_selected ", lst_data_personnes_adresse_non_attribues,
                  type(lst_data_personnes_adresse_non_attribues))

        except Exception as Exception_edit_personnes_adresse_selected:
            raise ExceptionEditPersonnesAdresseSelected(f"fichier : {Path(__file__).name}  ;  "
                                                 f"{edit_personnes_adresse_selected.__name__} ; "
                                                 f"{Exception_edit_personnes_adresse_selected}")

    return render_template("adresse_personnes/adresse_personnes_modifier_tags_dropbox.html",
                           data_personnes=data_personnes_all,
                           data_adresse_selected=data_personnes_adresse_selected,
                           data_personnes_attribues=data_personnes_adresse_attribues,
                           data_personnes_non_attribues=data_personnes_adresse_non_attribues)


"""
    nom: update_personnes_adresse_selected

    Récupère la liste de tous les genres du film sélectionné par le bouton "MODIFIER" de "adresse_personnes_afficher.html"
    
    Dans une liste déroulante particulière (tags-selector-tagselect), on voit :
    1) Tous les genres contenus dans la "t_genre".
    2) Les genres attribués au film selectionné.
    3) Les genres non-attribués au film sélectionné.

    On signale les erreurs importantes
"""


@app.route("/update_personnes_adresse_selected", methods=['GET', 'POST'])
def update_personnes_adresse_selected():
    if request.method == "POST":
        try:
            # Récupère l'id du film sélectionné
            id_adresse_selected = session['session_id_adresse_personnes_edit']
            print("session['session_id_adresse_personnes_edit'] ", session['session_id_adresse_personnes_edit'])

            # Récupère la liste des genres qui ne sont pas associés au film sélectionné.
            old_lst_data_personnes_adresse_non_attribues = session['session_lst_data_personnes_adresse_non_attribues']
            print("old_lst_data_personnes_adresse_non_attribues ", old_lst_data_personnes_adresse_non_attribues)

            # Récupère la liste des genres qui sont associés au film sélectionné.
            old_lst_data_personnes_adresse_attribues = session['session_lst_data_personnes_adresse_old_attribues']
            print("old_lst_data_personnes_adresse_old_attribues ", old_lst_data_personnes_adresse_attribues)

            # Effacer toutes les variables de session.
            session.clear()

            # Récupère ce que l'utilisateur veut modifier comme genres dans le composant "tags-selector-tagselect"
            # dans le fichier "genres_films_modifier_tags_dropbox.html"
            new_lst_str_personnes_adresse = request.form.getlist('name_select_tags')
            print("new_lst_str_personnes_adresse ", new_lst_str_personnes_adresse)

            # OM 2021.05.02 Exemple : Dans "name_select_tags" il y a ['4','65','2']
            # On transforme en une liste de valeurs numériques. [4,65,2]
            new_lst_int_personnes_adresse_old = list(map(int, new_lst_str_personnes_adresse))
            print("new_lst_personnes_adresse ", new_lst_int_personnes_adresse_old, "type new_lst_personnes_adresse ",
                  type(new_lst_int_personnes_adresse_old))

            # Pour apprécier la facilité de la vie en Python... "les ensembles en Python"
            # https://fr.wikibooks.org/wiki/Programmation_Python/Ensembles
            # OM 2021.05.02 Une liste de "id_genre" qui doivent être effacés de la table intermédiaire "t_genre_film".
            lst_diff_personnes_delete_b = list(set(old_lst_data_personnes_adresse_attribues) -
                                            set(new_lst_int_personnes_adresse_old))
            print("lst_diff_personnes_delete_b ", lst_diff_personnes_delete_b)

            # Une liste de "id_genre" qui doivent être ajoutés à la "t_genre_film"
            lst_diff_personnes_insert_a = list(
                set(new_lst_int_personnes_adresse_old) - set(old_lst_data_personnes_adresse_attribues))
            print("lst_diff_personnes_insert_a ", lst_diff_personnes_insert_a)

            # SQL pour insérer une nouvelle association entre
            # "fk_film"/"id_adresse" et "fk_genre"/"id_genre" dans la "t_genre_film"
            strsql_insert_personnes_adresse = """INSERT INTO t_pers_adresse (id_pers_adresse, fk_personnes, fk_adresse)
                                                    VALUES (NULL, %(value_fk_personnes)s, %(value_fk_adresse)s)"""

            # SQL pour effacer une (des) association(s) existantes entre "id_adresse" et "id_genre" dans la "t_genre_film"
            strsql_delete_personnes_adresse = """DELETE FROM t_pers_adresse WHERE fk_personnes = %(value_fk_personnes)s AND fk_adresse = %(value_fk_adresse)s"""

            with DBconnection() as mconn_bd:
                # Pour le film sélectionné, parcourir la liste des genres à INSÉRER dans la "t_genre_film".
                # Si la liste est vide, la boucle n'est pas parcourue.
                for id_personnes_ins in lst_diff_personnes_insert_a:
                    # Constitution d'un dictionnaire pour associer l'id du film sélectionné avec un nom de variable
                    # et "id_personnes_ins" (l'id du genre dans la liste) associé à une variable.
                    valeurs_adresse_sel_personnes_sel_dictionnaire = {"value_fk_adresse": id_adresse_selected,
                                                                      "value_fk_personnes": id_personnes_ins}

                    mconn_bd.execute(strsql_insert_personnes_adresse, valeurs_adresse_sel_personnes_sel_dictionnaire)

                # Pour le film sélectionné, parcourir la liste des genres à EFFACER dans la "t_genre_film".
                # Si la liste est vide, la boucle n'est pas parcourue.
                for id_personnes_del in lst_diff_personnes_delete_b:
                    # Constitution d'un dictionnaire pour associer l'id du film sélectionné avec un nom de variable
                    # et "id_personnes_del" (l'id du genre dans la liste) associé à une variable.
                    valeurs_adresse_sel_personnes_sel_dictionnaire = {"value_fk_adresse": id_adresse_selected,
                                                                      "value_fk_personnes": id_personnes_del}

                    # Du fait de l'utilisation des "context managers" on accède au curseur grâce au "with".
                    # la subtilité consiste à avoir une méthode "execute" dans la classe "DBconnection"
                    # ainsi quand elle aura terminé l'insertion des données le destructeur de la classe "DBconnection"
                    # sera interprété, ainsi on fera automatiquement un commit
                    mconn_bd.execute(strsql_delete_personnes_adresse, valeurs_adresse_sel_personnes_sel_dictionnaire)

        except Exception as Exception_update_personnes_adresse_selected:
            raise ExceptionUpdatePersonnesAdresseSelected(f"fichier : {Path(__file__).name}  ;  "
                                                   f"{update_personnes_adresse_selected.__name__} ; "
                                                   f"{Exception_update_personnes_adresse_selected}")

    # Après cette mise à jour de la table intermédiaire "t_genre_film",
    # on affiche les adresse et le(urs) genre(s) associé(s).
    return redirect(url_for('adresse_personnes_afficher', id_adresse_sel=id_adresse_selected))


"""
    nom: personnes_adresse_afficher_data

    Récupère la liste de tous les genres du film sélectionné par le bouton "MODIFIER" de "adresse_personnes_afficher.html"
    Nécessaire pour afficher tous les "TAGS" des genres, ainsi l'utilisateur voit les genres à disposition

    On signale les erreurs importantes
"""


def personnes_adresse_afficher_data(valeur_id_adresse_selected_dict):
    print("valeur_id_adresse_selected_dict...", valeur_id_adresse_selected_dict)
    try:

        strsql_adresse_selected = """SELECT id_adresse, Rue, Numero, Localite, GROUP_CONCAT(id_personnes) as PersonnesAdresse FROM t_pers_adresse
                                        INNER JOIN t_adresse ON t_adresse.id_adresse = t_pers_adresse.fk_adresse
                                        INNER JOIN t_personnes ON t_personnes.id_personnes = t_pers_adresse.fk_personnes
                                        WHERE id_adresse = %(value_id_adresse_selected)s"""

        strsql_personnes_adresse_non_attribues = """SELECT id_personnes, nom_personnes FROM t_personnes WHERE id_personnes not in(SELECT id_personnes as idPersonnesAdresse FROM t_pers_adresse
                                                    INNER JOIN t_adresse ON t_adresse.id_adresse = t_pers_adresse.fk_adresse
                                                    INNER JOIN t_personnes ON t_personnes.id_personnes = t_pers_adresse.fk_personnes
                                                    WHERE id_adresse = %(value_id_adresse_selected)s)"""

        strsql_personnes_adresse_attribues = """SELECT id_adresse, id_personnes, Rue FROM t_pers_adresse
                                            INNER JOIN t_adresse ON t_adresse.id_adresse = t_pers_adresse.fk_adresse
                                            INNER JOIN t_personnes ON t_personnes.id_personnes = t_pers_adresse.fk_personnes
                                            WHERE id_adresse = %(value_id_adresse_selected)s"""

        # Du fait de l'utilisation des "context managers" on accède au curseur grâce au "with".
        with DBconnection() as mc_afficher:
            # Envoi de la commande MySql
            mc_afficher.execute(strsql_personnes_adresse_non_attribues, valeur_id_adresse_selected_dict)
            # Récupère les données de la requête.
            data_personnes_adresse_non_attribues = mc_afficher.fetchall()
            # Affichage dans la console
            print("personnes_adresse_afficher_data ----> data_personnes_adresse_non_attribues ", data_personnes_adresse_non_attribues,
                  " Type : ",
                  type(data_personnes_adresse_non_attribues))

            # Envoi de la commande MySql
            mc_afficher.execute(strsql_adresse_selected, valeur_id_adresse_selected_dict)
            # Récupère les données de la requête.
            data_adresse_selected = mc_afficher.fetchall()
            # Affichage dans la console
            print("data_adresse_selected  ", data_adresse_selected, " Type : ", type(data_adresse_selected))

            # Envoi de la commande MySql
            mc_afficher.execute(strsql_personnes_adresse_attribues, valeur_id_adresse_selected_dict)
            # Récupère les données de la requête.
            data_personnes_adresse_attribues = mc_afficher.fetchall()
            # Affichage dans la console
            print("data_personnes_adresse_attribues ", data_personnes_adresse_attribues, " Type : ",
                  type(data_personnes_adresse_attribues))

            # Retourne les données des "SELECT"
            return data_adresse_selected, data_personnes_adresse_non_attribues, data_personnes_adresse_attribues

    except Exception as Exception_personnes_adresse_afficher_data:
        raise ExceptionPersonnesAdresseAfficherData(f"fichier : {Path(__file__).name}  ;  "
                                               f"{personnes_adresse_afficher_data.__name__} ; "
                                               f"{Exception_personnes_adresse_afficher_data}")
