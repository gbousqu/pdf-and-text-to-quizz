
#A FAIRE
# - ajouter une zone de texte, une zone pour url d'image, une zone pour url de lien hypertexte avant la génération du sql
#   pour ajouter des informations supplémentaires à chaque question (texte, image, lien hypertexte)

import streamlit as st
from pdf_to_quizz import pdf_to_quizz
from text_to_quizz import txt_to_quizz
from generate_pdf import generate_pdf_quiz
import json
import asyncio
import os
from datetime import datetime
import json
import streamlit as st
from datetime import datetime
from google.cloud import bigquery
from google.oauth2 import service_account
import time
import html
import re

temps_d_attente = 2 #pour attendre que bigquery se mette à jour après modification, création, suppression de données et avant de recharger la page

if "bigquery_client" not in st.session_state:
    # credentials = service_account.Credentials.from_service_account_file("test-big-query-janv-2019-b5e01a71ad8e.json")
    # Charger les informations du compte de service à partir des secrets de Streamlit

    #Les informations du compte de service Google Permettant d'accéder  à la base de données bigquery 
    # ces informations sont stockées dans le fichier secrets.toml du dossier .streamlit
    # Elles sont récupérées et stockées dans la variable gcp_service_account
    #et ensuite utilisées pour créer un client BigQuery
    #et le fichier secrets.toml est invisible dans la version en ligne sur github car son nom est dans .gitignore

    #dans bigquery, on a une table qcm_prompts_openai qui contient les contextes et les prompts
    #les contextes sont les textes à partir desquels on génère les questions sont propres à chaque utilisateur de l'appli
    #ou peuvent être publics

    gcp_service_account = st.secrets["gcp_service_account"]
    service_account_info = json.loads(gcp_service_account)
    # Créer des identifiants à partir des informations du compte de service
    credentials = service_account.Credentials.from_service_account_info(service_account_info)
    # Créer un client BigQuery avec ces identifiants
    client = bigquery.Client(credentials=credentials)
    st.session_state.bigquery_client = bigquery.Client(credentials=credentials)


client = st.session_state.bigquery_client

# Déterminer si l'application est en cours d'exécution sur Streamlit Sharing
# is_streamlit_sharing = st.secrets.get("is_streamlit_sharing", False)

#secrets.toml contient une ligne avec un objet secret_json qui contient les informations de connexion des utilisateurs autorisés à utiliser l'application
json_string = st.secrets["secret_json"].replace('\\\\', '\\')
secret_data = json.loads(json_string)


# if is_streamlit_sharing:
#     # Si l'application est en cours d'exécution sur Streamlit Sharing,
#     json_string = st.secrets["secret_json"].replace('\\\\', '\\')
#     secret_data = json.loads(json_string)
# else:        
#     # Charger les données de connexion à partir du fichier secret.json
#     with open('secret.json', 'r') as f:
#         secret_data = json.load(f)


# Si l'utilisateur n'est pas encore connecté
if not st.session_state.get('logged_in', False):
    # Créer un formulaire de connexion
    with st.form(key='login_form'):
        username = st.text_input('Nom d\'utilisateur')
        password = st.text_input('Mot de passe', type='password')
        submit_button = st.form_submit_button(label='Se connecter')

        # Lorsque le bouton de soumission est cliqué
        if submit_button:
            # Parcourir chaque élément dans secret_data
            for data in secret_data:
                # Vérifier si le nom d'utilisateur et le mot de passe sont corrects
                if username == data['name'] and password == data['pw']:
                    # Si c'est le cas, définir 'logged_in' à True dans l'état de session
                    st.session_state['username'] = username
                    st.session_state['logged_in'] = True
                    st.experimental_rerun()
            if st.session_state.get('logged_in', False) == False:
                # Si aucune correspondance n'a été trouvée, afficher un message d'erreur
                st.error('Nom d\'utilisateur ou mot de passe incorrect.')
else:

    username = st.session_state['username']

    st.markdown('[Obtenir une clé API OpenAI](https://platform.openai.com/api-keys)', unsafe_allow_html=True)
    openai_api_key = st.text_input("Entrez votre clé OpenAI", type="password")
    os.environ['OPENAI_API_KEY'] = openai_api_key

    # Lire le contenu du fichier CSS
    with open('styles_streamlit.css', 'r') as f:
        css = f.read()

    # Inclure le CSS dans le script Streamlit
    st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)
    # Définir une valeur par défaut les variables de session
    if 'editing' not in st.session_state:
        st.session_state['editing'] = False
        st.session_state['confirm_delete'] = False

    ###########################################
    # choisir un type de question
    st.subheader("Choisir un type de question")
    type_question = st.radio("type de question", ("QCM avec une réponse correcte", "QCM avec 1,2 ou 3 réponses correctes", "Vrai/Faux"),label_visibility='hidden')
    # if "type_question" not in st.session_state:
    #             st.session_state["type_question"] = "QCM avec une réponse correcte"
    # else :
    st.session_state["type_question"]=type_question
    # print("\n type_question: ", type_question)

    if type_question == "QCM avec une réponse correcte": 
            # print("QCM avec une réponse correcte")
            format_question ="""
Les questions seront de type QCM avec quatre options. Parmi les quatre options proposées, une seule option est vraie, les autres sont fausses.
La réponse (answer) devra être la lettre correspondant à la réponse correcte.
Voici le modèle pour chaque question :

Question 1,2, ... : énoncé de la question ici (le numéro de la question doit être spécifié)
CHOICE_A: une option
CHOICE_B: une autre option
CHOICE_C: une autre option
CHOICE_D: une autre option
Answer: l'unique option correcte (exemple : A ou B ou C ou D)
Chaque question doit être détaillée 
La question et les options seront en français, mais garde en anglais les mots CHOICE et answer dans le modèle ci-dessus."""

    elif type_question == "QCM avec 1,2 ou 3 réponses correctes":
        # print("QCM avec plusieurs réponses correctes")
        format_question = """
Les question seront de type QCM avec quatre options .
Parmi les quatre options, deux ou trois doivent être correctes.
La réponse (answer) devra être une chaine de caractères avec les lettres des options correctes, séparées par une virgule. Par exemple, si les options correctes sont A et C, alors la réponse sera A,C.
Voici le modèle pour chaque question :

Question 1,2, ... : énoncé de la question ici (le numéro de la question doit être spécifié)
CHOICE_A: une option
CHOICE_B: une autre option
CHOICE_C: une autre option
CHOICE_D: une autre option
Answer: la ou les options correctes (exemple : A,C ou A,B,C ou  ...)

Chaque question doit être détaillée.
La question et les options seront en français, mais garde en anglais les mots CHOICE et answer dans le modèle ci-dessus
            """
        
    else:
        print("Vrai/Faux")
        format_question = """
Les questions seront de type Vrai/Faux.
La réponse (answer) devra être soit Vrai soit Faux.
Voici le modèle pour chaque question :

Question 1,2, ... : énoncé de la question ici (le numéro de la question doit être spécifié)
Answer: Vrai ou Faux
Explanation: explication de la réponse
Chaque question doit être détaillée.
La question sera en français, mais garde en anglais les mots Answer et Explanation dans le modèle ci-dessus
"""

    st.session_state['format_question'] = format_question
    # print("\n format_question: ", format_question)        
    ##########################################    

    st.subheader("Choisir un contexte")

    # Exécuter la requête pour récupérer les données de la table qcm_prompts_openai
    #on ne récupère que les lignes qui ont été créées par l'utilisateur connecté ou les lignes qui n'ont pas de user
    query = "SELECT name, content, user, visibility,description  FROM qcm.qcm_prompts_openai WHERE user='"+ username +"' OR visibility='public'"
   
    query_job = client.query(query)

    # Convertir le résultat de la requête en un DataFrame pandas
    df = query_job.to_dataframe()

    # Convertir le DataFrame en une liste de dictionnaires
    rows = df.to_dict('records')

    # Créer une liste des noms des contextes
    contexte_names = [contexte['name'] for contexte in rows]

    # Sélectionner un nom de contexte à partir de la liste déroulante
    selected_contexte_name = st.selectbox('choisir un contexte', contexte_names, key='select_contexte',label_visibility='hidden')

    # Trouver le contenu et le créateur (user) du contexte correspondant dans les données récupérées de la base de données
    #selected_contexte est un tableau à deux éléments :le name et le content du contexte
    selected_contexte = next(contexte for contexte in rows if contexte['name'] == selected_contexte_name)

    selected_contexte_content = selected_contexte['content']
    selected_contexte_user = selected_contexte['user']
    selected_contexte_description = selected_contexte['description']
    selected_contexte_visibility = selected_contexte['visibility']

    if selected_contexte_user != username:
        st.write("Ce contexte est en lecture seule, vous pouvez cliquer sur 'créer un nouveau contexte' pour en faire une copie éditable.")
    else:
        st.write("Créé par : ", selected_contexte_user)

    st.write("Visibilité : ", selected_contexte_visibility)

    if selected_contexte_description is not None:
        selected_contexte_description = html.escape(selected_contexte_description)
    st.markdown("Description du contexte:")
    st.markdown(f'<div class="contexte" style="white-space: pre-wrap; margin-bottom:20px">{selected_contexte_description}</div>', unsafe_allow_html=True)


    # Remplacer les caractères < et > par leurs entités HTML correspondantes
    selected_contexte_content = selected_contexte_content.replace('<', '&lt;').replace('>', '&gt;')
    # Remplacer \n par <br/> dans selected_contexte_content
    selected_contexte_content = selected_contexte_content.replace('\n', '<br/>')

    # Afficher le contenu du contexte sélectionné dans une zone de texte    
    st.markdown("Contenu du contexte:")
    st.markdown(f'<div class="contexte">{selected_contexte_content}</div>', unsafe_allow_html=True)
    st.markdown("---")

    ########################################################################################
    # Ajouter un bouton "Modifier le contexte"
    if selected_contexte_user == username: #seul le créateur du contexte peut le modifier
        if st.button('Modifier ce contexte', key='edit_above_contexte'):
            #ce drapeau editing est utilisé pour qu'au rechargement de la page, le formulaire d'édition soit affiché
            st.session_state['editing'] = True

        if st.session_state.get('editing', False):  #false = valeur par défaut
            # print("ouverture du formulaire d'édition du contexte sélectionné")

            with st.form(key='edit_form'):

                # Ajouter un bouton "Enregistrer"
                save_button = st.form_submit_button('Enregistrer les modifications')

                # Ajouter un bouton "Annuler"
                cancel_button = st.form_submit_button('Fermer le formulaire sans enregistrer les modifications')
                # Ajouter un nouveau nom de contexte
                st.session_state['new_contexte_name'] = st.text_input('Modifier le nom du contexte', value=selected_contexte['name'], key='edit_contexte_name')

                #ajouter un choix de visibilité (public ou privé)
                st.session_state['new_contexte_visibility'] = st.radio("Visibilité du contexte", ("public", "private"), key='edit_modify_contexte_visibility',label_visibility='hidden', index=("public", "private").index(selected_contexte['visibility']))

                #ajouter une description du contexte
                st.session_state['new_contexte_description'] = st.text_area('Description du contexte', value=selected_contexte['description'], key='edit_contexte_description',height=500)
                
                # Ajouter un nouveau contenu de contexte
                st.session_state['new_contexte_content'] = st.text_area('Modifier le contexte', value=selected_contexte['content'], key='edit_contexte_content', height=500)

            
                ########################################################################################

                if cancel_button:
                    # print("cancel edited contexte")
                    st.session_state['editing'] = False
                    st.experimental_rerun()

                # Sauvegarder les modifications apportées au contexte sélectionné
                if save_button:
                    # print("save edited contexte")
                    new_contexte_name = st.session_state.get('new_contexte_name')
                    new_contexte_content = st.session_state.get('new_contexte_content')
                    new_contexte_visibility = st.session_state.get('new_contexte_visibility')
                    new_contexte_description = st.session_state.get('new_contexte_description')
                    
                    # print(new_contexte_name)

                    if new_contexte_name.strip() and new_contexte_content.strip():
                            
                        # Mettre à jour la table qcm_prompts_openai de la base de données qcm dans bigquery
                        query = """
                            UPDATE `qcm.qcm_prompts_openai`
                            SET name = @new_contexte_name, content = @new_contexte_content, visibility = @new_contexte_visibility, description = @new_contexte_description
                            WHERE name = @selected_contexte_name AND user = @username
                        """
                        params = [
                            bigquery.ScalarQueryParameter('new_contexte_name', 'STRING', new_contexte_name),
                            bigquery.ScalarQueryParameter('new_contexte_content', 'STRING', new_contexte_content),
                            bigquery.ScalarQueryParameter('new_contexte_visibility', 'STRING', new_contexte_visibility),
                            bigquery.ScalarQueryParameter('new_contexte_description', 'STRING', new_contexte_description),
                            bigquery.ScalarQueryParameter('selected_contexte_name', 'STRING', selected_contexte_name),
                            bigquery.ScalarQueryParameter('username', 'STRING', username),
                        ]
                        job_config = bigquery.QueryJobConfig()
                        job_config.query_parameters = params
                        client.query(query, job_config=job_config)

                        
                        # print("mise à jour de selected_contexte")
      
                        st.session_state['editing'] = False
                        with st.spinner('Mise à jour des données...'):
                            time.sleep(temps_d_attente)
                        st.experimental_rerun()


    ########################################################################################

    # Ajouter un bouton "Supprimer" seulement s'il y a au moins deux contextes et si on est le créateur du contexte
    if len(rows) > 1 and selected_contexte_user != "":
        if st.button('Supprimer ce contexte (n\'oubliez pas de cocher la confirmation)', key='delete_contexte'):
            st.session_state['confirm_delete'] = True  # Change this to True

    # Si le bouton "Supprimer" a été cliqué, afficher une case à cocher pour la confirmation
    if st.session_state.get('confirm_delete', False): # (false : valeur par défaut)
        confirm = st.checkbox('Confirmer la suppression', key='confirm_delete_checkbox')
        if confirm:

            # Supprimer le contexte sélectionné de la table
            query = """
                DELETE FROM `qcm.qcm_prompts_openai`
                WHERE name = @selected_contexte_name AND user = @username
            """
            params = [
                bigquery.ScalarQueryParameter('selected_contexte_name', 'STRING', selected_contexte_name),
                bigquery.ScalarQueryParameter('username', 'STRING', username),
            ]
            job_config = bigquery.QueryJobConfig()
            job_config.query_parameters = params
            client.query(query, job_config=job_config)

            # se rappeler que la case à cocher de confirmation doit etre masquée
            st.session_state['confirm_delete'] = False
            with st.spinner('Mise à jour des données...'):
                time.sleep(temps_d_attente)
            st.experimental_rerun() 
        

    ########################################################################################
    if st.button('Créer un nouveau contexte à partir de celui-là', key="add_new_contexte"):
        #ce drapeau editing est utilisé pour qu'au rechargement de la page, le formulaire d'édition soit affiché
        st.session_state['form_new_contexte'] = True

    if st.session_state.get('form_new_contexte', False):

        with st.form(key='new_form'):

            # Ajouter un bouton "Enregistrer"
            save_button_new_contexte = st.form_submit_button('Enregistrer ce nouveau contexte')

            # Ajouter un bouton "Annuler"
            cancel_button_new_contexte = st.form_submit_button('Annuler la création du nouveau contexte')

           # Ajouter un nouveau nom de contexte (par défaut celui du contexte sélectionné, pour simplifier la duplication)
            selected_contexte_name = selected_contexte_name + " [copie " + username + "]"
            # Ajouter un nouveau nom de contexte
            st.session_state['new_contexte_name'] = st.text_input('nom du contexte', value=selected_contexte['name'], key='edit_new_contexte_name')


            #ajouter un choix de visibilité (public ou privé)
            st.session_state['new_contexte_visibility'] = st.radio("Visibilité du contexte", ("public", "private"), key='edit_new_contexte_visibility',label_visibility='hidden', index=("public", "private").index(selected_contexte['visibility']))

            #ajouter une description du contexte
            st.session_state['new_contexte_description'] = st.text_area('Description du contexte', value=selected_contexte['description'], key='edit_contexte_description',height=500)
            
            # Ajouter un nouveau contenu de contexte
            st.session_state['new_contexte_content'] = st.text_area('Modifier le contexte', value=selected_contexte['content'], key='edit_contexte_content', height=500)

           
            ########################################################################################

            if cancel_button_new_contexte:
                st.session_state['form_new_contexte'] = False
                st.experimental_rerun()

            # Sauvegarder le nouveau contexte
            if save_button_new_contexte:
                new_contexte_name = st.session_state.get('new_contexte_name')
                new_contexte_content = st.session_state.get('new_contexte_content')
                new_contexte_visibility = st.session_state.get('new_contexte_visibility')
                new_contexte_description = st.session_state.get('new_contexte_description')
                # print(new_contexte_name)

                # Vérifier si une entrée avec le même name et user existe déjà
                query = """
                    SELECT * FROM `qcm.qcm_prompts_openai`
                    WHERE name = @new_contexte_name 
                """
                params = [
                    bigquery.ScalarQueryParameter('new_contexte_name', 'STRING', new_contexte_name),                    
                ]
                job_config = bigquery.QueryJobConfig()
                job_config.query_parameters = params
                
                results = client.query(query, job_config=job_config)
                rows = list(results.result())
                existing_entry = rows[0] if rows else None

                if new_contexte_name.strip() and new_contexte_content.strip() and not existing_entry:
                
                    # # Ajouter le nouveau contexte à la liste des contextes
                    # data.append({'name': new_contexte_name, 'content': new_contexte_content})

                    # # Sauvegarder les données dans le fichier JSON
                    # with open('contextes.json', 'w') as f:
                    #     json.dump(data, f)

                    query = """
                        INSERT INTO `test-big-query-janv-2019.qcm.qcm_prompts_openai` (name, content, user, visibility, description)
                        VALUES (@new_contexte_name, @new_contexte_content, @username, @new_contexte_visibility, @new_contexte_description)
                    """
                    params = [
                        bigquery.ScalarQueryParameter('new_contexte_name', 'STRING', new_contexte_name),
                        bigquery.ScalarQueryParameter('new_contexte_content', 'STRING', new_contexte_content),
                        bigquery.ScalarQueryParameter('username', 'STRING', username),
                        bigquery.ScalarQueryParameter('new_contexte_visibility', 'STRING', new_contexte_visibility),
                        bigquery.ScalarQueryParameter('new_contexte_description', 'STRING', new_contexte_description),
                    ]
                    job_config = bigquery.QueryJobConfig()
                    job_config.query_parameters = params
                    client.query(query, job_config=job_config)

                    st.session_state['form_new_contexte'] = False
                    with st.spinner('Mise à jour des données...'):
                        time.sleep(temps_d_attente)
                    st.experimental_rerun() #forcer le rechargement de la page pour masquer le formulaire de création de contexte




    ########################################################################################
    st.markdown("---")
    st.subheader("Générer un quiz avec ces paramètres")

    num_questions_per_page = st.number_input('Nombre de questions à générer, par page du pdf ou du texte', min_value=1, max_value=10, value=1, step=1)
    st.session_state['num_questions_per_page'] = num_questions_per_page

    # Initialiser le choix de la méthode d'entrée dans le session state si ce n'est pas déjà fait
    if 'input_method' not in st.session_state:
        st.session_state['input_method'] = "Upload de fichier"

    # Utiliser la valeur du session state pour le radio button
    input_method = st.radio("Sélectionnez la méthode d'entrée pour le document à partir duquel on générera le quiz :", ("Upload de fichier", "Ou collage direct du texte"))

    # Mettre à jour la valeur du session state si le choix de l'utilisateur a changé
    if st.session_state['input_method'] != input_method:
        st.session_state['input_method'] = input_method

    if st.session_state['input_method'] == "Upload de fichier":
        # Upload PDF file

        uploaded_file = st.file_uploader(":female-student:", type=["pdf"])
        if st.button("Générer Quiz à partir du pdf", key=f"button_generer_from_pdf"):
            # if uploaded_file is not None:          
                with st.spinner("Génération du quizz..."):
                    with open(f"data/{uploaded_file.name}", "wb") as f:
                        f.write(uploaded_file.getvalue())        
                        st.session_state['contexte']=selected_contexte['content']
                        st.session_state['questions'] = asyncio.run(pdf_to_quizz(f"data/{uploaded_file.name}",))

    else:
        # Text input
        # Initialiser une variable txt  du session_state si ce n'est pas déjà fait
        if 'txt' not in st.session_state:
            st.session_state['txt'] = ''

        # Utiliser la valeur du text_area pour renseigner la variable txt
        txt = st.text_area('Taper le texte à partir duquel vous voulez générer le quiz', value=st.session_state['txt'])

        # Mettre à jour la valeur du session_state lorsque le texte est modifié
        st.session_state['txt'] = txt

        if st.button("Générer le Quiz à partir du texte", key=f"button_generer_from_text"):
            if txt != "":
                with st.spinner("Génération du quizz..."):
                    st.session_state['contexte']=selected_contexte_content
                    #c'est là qu'on appelle la fonction qui génère les questions avec openAI
                    asyncio.run(txt_to_quizz(txt))
                    # st.session_state['questions'] = asyncio.run(txt_to_quizz(txt))


    if ('questions' in st.session_state) :
    #les questions ont été générées      
            # st.write("Les questions ont été générées avec succès.")
            st.write("voici les questions :", st.session_state['questions'])
           
            with st.spinner("Génération du quizz ..."):
                json_questions = st.session_state['questions']

              # Debug: Afficher le contenu de json_questions
                # st.write("Contenu de json_questions:", json_questions)

                 # Pour la Sauvegarde des questions dans un fichier
                now = datetime.now()
                date_suffix = now.strftime("%Y_%m_%d_%H_%M_%S") 
                if 'uploaded_file' in globals() or 'uploaded_file' in locals():
                    if uploaded_file is not None:
                        file_name = uploaded_file.name #cas où on a uploadé un fichier pdf
                    else:
                        now = datetime.now()
                        file_name = date_suffix  #  pour le cas où on fournit du texte
                else:
                    now = datetime.now()
                    file_name = date_suffix  #  pour le cas où on fournit du texte

                # Retirer l'extension .pdf du nom de fichier
                if file_name.endswith(".pdf"):
                    file_name = file_name[:-4]   

               
                line_height = 60  # Ajuster cette valeur pour changer la hauteur de chaque ligne
                num_charac_per_line = 90  # Ajuster cette valeur pour changer le nombre de caractères par ligne

                with st.form(key='edit_quiz'):
                    for i, question_data in enumerate(json_questions):
                        # Debug: Afficher l'indice et le contenu de chaque question
                        # st.write(f"Indice: {i}, Question: {question_data}")
        
                        st.checkbox(f"Sélectionner cette question", key=f"checkbox_{i+1}",value=True)
                        num_lines_question = len(question_data["question"]) // num_charac_per_line + 1


                        st.text_area(f"Question {i+1}", question_data["question"], key=f"question_{i+1}", height=num_lines_question*line_height)
                       
                        if type_question in ["QCM avec une réponse correcte", "QCM avec 1,2 ou 3 réponses correctes"]:
                            col1, col2 = st.columns([1,10])
                            with col2:
                                num_lines_option_A = len(question_data["A"]) // num_charac_per_line + 1
                                st.text_area(f"Option A", question_data["A"], key=f"option_A_{i+1}", height=num_lines_option_A*line_height)
                                num_lines_option_B = len(question_data["B"]) // num_charac_per_line + 1
                                st.text_area(f"Option B", question_data["B"], key=f"option_B_{i+1}", height=num_lines_option_B*line_height)
                                num_lines_option_C = len(question_data["C"]) // num_charac_per_line + 1
                                st.text_area(f"Option C", question_data["C"], key=f"option_C_{i+1}", height=num_lines_option_C*line_height)
                                num_lines_option_D = len(question_data["D"]) // num_charac_per_line + 1
                                st.text_area(f"Option D", question_data["D"], key=f"option_D_{i+1}", height=num_lines_option_D*line_height)
                                num_lines_reponse = len(question_data["reponse"]) // num_charac_per_line + 1
                                st.text_area(f"Réponse", question_data["reponse"], key=f"reponse_{i+1}", height=num_lines_reponse*line_height)
                        elif type_question == "Vrai/Faux":
                            col1, col2 = st.columns([1,10])
                            with col2:
                                num_lines_reponse = len(question_data["reponse"]) // num_charac_per_line + 1
                                st.text_area(f"Réponse", question_data["reponse"], key=f"reponse_{i+1}", height=num_lines_reponse*line_height)
                                num_lines_explication = len(question_data["explication"]) // num_charac_per_line + 1
                                st.text_area(f"Explication", question_data["explication"], key=f"explication_{i+1}", height=num_lines_explication*line_height)
                        st.markdown("---")
                    
                    submit_button = st.form_submit_button(label='Générer le sql d\'importation des questions dans la base de données')
                    if submit_button:
                        # Obtenir la date actuelle au format datetime de MySQL
                        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                        # Créer une liste pour stocker les valeurs (qti) à insérer
                        values = []
                        # Parcourir toutes les questions
                        for i, question_data in enumerate(json_questions):
                            # Vérifier si la case à cocher pour cette question est sélectionnée
                            if st.session_state.get(f"checkbox_{i+1}"):

                                if type_question=="QCM avec une réponse correcte" or type_question =="QCM avec 1,2 ou 3 réponses correctes": 
                                # Obtenir les valeurs des zones de texte pour cette question
                                    option_A = st.session_state.get(f"option_A_{i+1}")
                                    option_B = st.session_state.get(f"option_B_{i+1}")
                                    option_C = st.session_state.get(f"option_C_{i+1}")
                                    option_D = st.session_state.get(f"option_D_{i+1}")
                                    reponse = st.session_state.get(f"reponse_{i+1}")
                                    
                                    # Convertir la réponse en une liste de lettres
                                    correct_responses_letters = reponse.split(',')
                                    # Créer un dictionnaire pour mapper les lettres aux nombres
                                    letter_to_number = {'A': '1', 'B': '2', 'C': '3', 'D': '4'}
                                    # Convertir les lettres en nombres
                                    correct_responses = [letter_to_number[letter] for letter in correct_responses_letters]

                                    question = st.session_state.get(f"question_{i+1}")

                                    question = html.escape(question)
                                    option_A = html.escape(option_A)
                                    option_B = html.escape(option_B)
                                    option_C = html.escape(option_C)
                                    option_D = html.escape(option_D)

                                    # Construire le QTI pour cette question
                                    qti = f'<assessmentItem label="qcm"><responseDeclaration identifier="RESPONSE" cardinality="multiple" baseType="identifier"><correctResponse>{"".join([f"<value>{value}</value>" for value in correct_responses])}</correctResponse></responseDeclaration><itemBody><choiceInteraction responseIdentifier="RESPONSE" shuffle="false" maxChoices="0"><prompt>{question}</prompt><simpleChoice identifier="1">{option_A}</simpleChoice><simpleChoice identifier="2">{option_B}</simpleChoice><simpleChoice identifier="3">{option_C}</simpleChoice><simpleChoice identifier="4">{option_D}</simpleChoice></choiceInteraction></itemBody></assessmentItem>'

                                    # Échapper les apostrophes dans le QTI
                                    qti = qti.replace("'", "\\'")

                                    # Ajouter les valeurs à la liste
                                    values.append(f"('', '{qti}', '{now}', '{now}')")
                                else: #cas du V/F
                                    reponse = st.session_state.get(f"reponse_{i+1}")
                                    explication = st.session_state.get(f"explication_{i+1}")
                                    question = st.session_state.get(f"question_{i+1}")
                                    question = html.escape(question)
                                    reponse = reponse.lower().replace("vrai", "1").replace("faux", "2")      
                                    explication = html.escape(explication)

                                    # Construire le QTI pour cette question

                                    qti = f'<assessmentItem label="qcm"><responseDeclaration identifier="RESPONSE" cardinality="multiple" baseType="identifier"><correctResponse><value>{reponse}</value></correctResponse></responseDeclaration><itemBody><choiceInteraction responseIdentifier="RESPONSE" shuffle="false" maxChoices="0"><prompt>{question}</prompt><simpleChoice identifier="1">V</simpleChoice><simpleChoice identifier="2">F</simpleChoice></choiceInteraction></itemBody></assessmentItem>'                                    # Échapper les apostrophes dans le QTI
                                    qti = qti.replace("'", "\\'")

                                    # Ajouter les valeurs à la liste
                                    values.append(f"('', '{qti}', '{now}', '{now}')")
                        # Créer la requête SQL
                        query = f"INSERT INTO questions (image, qti, date_creation, date_modification) VALUES {', '.join(values)};"

                        # Afficher les requêtes SQL dans une textarea
                        st.text_area("SQL à exécuter pour importer les questions", query, height=500)
                                
