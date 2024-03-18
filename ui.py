import streamlit as st
from ui_utils import check_password
from pdf_to_quizz import pdf_to_quizz
from text_to_quizz import txt_to_quizz
from generate_pdf import generate_pdf_quiz
import json
import asyncio
import os
from datetime import datetime
import json
import streamlit as st



openai_api_key = st.text_input("Entrez votre clé OpenAI", type="password")
os.environ['OPENAI_API_KEY'] = openai_api_key

# openai_api_key = os.getenv('OPENAI_API_KEY')
# st.write("OPENAI_API_KEY: ", openai_api_key)


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
type_question = st.radio("", ("QCM avec une réponse correcte", "QCM avec 1,2 ou 3 réponses correctes", "Vrai/Faux"))
# if "type_question" not in st.session_state:
#             st.session_state["type_question"] = "QCM avec une réponse correcte"
# else :
st.session_state["type_question"]=type_question
print("\n type_question: ", type_question)

if type_question == "QCM avec une réponse correcte": 
        print("QCM avec une réponse correcte")
        format_question ="""
    Les questions seront de type QCM avec quatre options. Parmi les quatre options proposées, une seule option est vraie, les autres sont fausses.
    La réponse (answer) devra être la lettre correspondant à la réponse correcte.
    Voici le modèle pour chaque question :

    Question 1,2, ... : énoncé de la question ici (le numéro de la question doit être spécifié)
    CHOICE_A: une option
    CHOICE_B: une autre option
    CHOICE_C: une autre option
    CHOICE_D: une autre option
    Answer: options correctes (exemple : A ou B ou C ou D)
    Chaque question doit être détaillée 
    La question et les options seront en français, mais garde en anglais les mots CHOICE et answer dans le modèle ci-dessus."""

elif type_question == "QCM avec 1,2 ou 3 réponses correctes":
    print("QCM avec plusieurs réponses correctes")
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
    Answer: options correctes (exemple : A,C ou A,B,C ou  ...)

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

# Charger les données à partir du fichier JSON
with open('prompts.json', 'r') as f:
    data = json.load(f)

# Créer une liste des noms des prompts
prompt_names = [prompt['name'] for prompt in data]

# Sélectionner un nom de prompt à partir de la liste déroulante
selected_prompt_name = st.selectbox('', prompt_names, key='select_prompt')

# Trouver le prompt correspondant
selected_prompt = next(prompt for prompt in data if prompt['name'] == selected_prompt_name)

selected_prompt_content = selected_prompt['content']

# Remplacer les caractères < et > par leurs entités HTML correspondantes
selected_prompt_content = selected_prompt_content.replace('<', '&lt;').replace('>', '&gt;')
# Remplacer \n par <br/> dans selected_prompt_content
selected_prompt_content = selected_prompt_content.replace('\n', '<br/>')

# Afficher le contenu du prompt sélectionné dans une zone de texte
st.markdown(f'<div class="prompt">{selected_prompt_content}</div>', unsafe_allow_html=True)


########################################################################################
# Ajouter un bouton "Modifier le prompt ci-dessus"
if st.button('Modifier ce contexte', key='edit_above_prompt'):
    #ce drapeau editing est utilisé pour qu'au rechargement de la page, le formulaire d'édition soit affiché
    st.session_state['editing'] = True

if st.session_state.get('editing', False):
    # print("ouverture du formulaire d'édition du prompt sélectionné")

    with st.form(key='edit_form'):

        # Ajouter un bouton "Enregistrer"
        save_button = st.form_submit_button('Enregistrer les modifications')

        # Ajouter un bouton "Annuler"
        cancel_button = st.form_submit_button('Fermer le formulaire sans enregistrer les modifications')
       # Ajouter un nouveau nom de prompt
        st.session_state['new_prompt_name'] = st.text_input('Modifier le nom du contexte', value=selected_prompt['name'], key='edit_prompt_name')

        # Ajouter un nouveau contenu de prompt
        st.session_state['new_prompt_content'] = st.text_area('Modifier le contexte', value=selected_prompt['content'], key='edit_prompt_content', height=500)

    
        ########################################################################################

        if cancel_button:
            print("cancel edited prompt")
            st.session_state['editing'] = False
            st.experimental_rerun()

        # Sauvegarder les modifications apportées au prompt sélectionné
        if save_button:
            print("save edited prompt")
            new_prompt_name = st.session_state.get('new_prompt_name')
            new_prompt_content = st.session_state.get('new_prompt_content')
            # print(new_prompt_name)

            if new_prompt_name.strip() and new_prompt_content.strip():
                # Mettre à jour data
                # print("mise à jour de data [liste des prompts] et du fichier prompts.json")
                for prompt in data:
                    if prompt['name'] == selected_prompt_name :
                        prompt['name'] = new_prompt_name
                        prompt['content'] = new_prompt_content
                        break

                # Sauvegarder les prompts dans le fichier JSON
                with open('prompts.json', 'w') as f:
                    json.dump(data, f)
                
                print("mise à jour de selected_prompt")
                # Mettre à jour le prompt sélectionné
                selected_prompt['name'] = new_prompt_name
                selected_prompt['content'] = new_prompt_content
                #sortir de l'édition du prompt
                # print("mise à jour de st.session_state['editing'] à false")
                st.session_state['editing'] = False
                st.experimental_rerun()


########################################################################################

# Ajouter un bouton "Supprimer" seulement s'il y a au moins deux prompts
if len(data) > 1:
    if st.button('Supprimer ce contexte', key='delete_prompt'):
        st.session_state['confirm_delete'] = True  # Change this to True

# Si le bouton "Supprimer" a été cliqué, afficher une case à cocher pour la confirmation
if st.session_state.get('confirm_delete', False): # (false : valeur par défaut)
    confirm = st.checkbox('Confirmer la suppression', key='confirm_delete_checkbox')
    if confirm:
        # Supprimer le prompt de la liste des prompts
        data.remove(selected_prompt)

        # Sauvegarder les données dans le fichier JSON
        with open('prompts.json', 'w') as f:
            json.dump(data, f)

        # Mettre à jour la liste des noms de prompts
        prompt_names = [prompt['name'] for prompt in data]

        # Sélectionner le premier prompt
        selected_prompt = data[0] if data else None

        # se rappeler que la case à cocher de confirmation doit etre masquée
        st.session_state['confirm_delete'] = False

        st.experimental_rerun()
    

########################################################################################
if st.button('Créer un nouveau contexte', key="add_new_prompt"):
    #ce drapeau editing est utilisé pour qu'au rechargement de la page, le formulaire d'édition soit affiché
    st.session_state['form_new_prompt'] = True

if st.session_state.get('form_new_prompt', False):

    with st.form(key='new_form'):

        # Ajouter un bouton "Enregistrer"
        save_button_new_prompt = st.form_submit_button('Enregistrer ce nouveau prompt')

        # Ajouter un bouton "Annuler"
        cancel_button_new_prompt = st.form_submit_button('Annuler la création du nouveau prompt')
       # Ajouter un nouveau nom de prompt
        st.session_state['new_prompt_name'] = st.text_input('Nom du prompt', value=selected_prompt['name'], key='edit_new_prompt_name')

        # Ajouter un nouveau contenu de prompt
        st.session_state['new_prompt_content'] = st.text_area('Contenu du prompt', value=selected_prompt['content'], key='edit_new_prompt_content', height=500)

    
        ########################################################################################

        if cancel_button_new_prompt:
            st.session_state['form_new_prompt'] = False
            st.experimental_rerun()

        # Sauvegarder le nouveau prompt
        if save_button_new_prompt:
            new_prompt_name = st.session_state.get('new_prompt_name')
            new_prompt_content = st.session_state.get('new_prompt_content')
            # print(new_prompt_name)

            if new_prompt_name.strip() and new_prompt_content.strip():
               
                # Ajouter le nouveau prompt à la liste des prompts
                data.append({'name': new_prompt_name, 'content': new_prompt_content})

                # Sauvegarder les données dans le fichier JSON
                with open('prompts.json', 'w') as f:
                    json.dump(data, f)
                st.session_state['form_new_prompt'] = False
                st.experimental_rerun() #forcr le rechargement de la page pour masquer le formulaire de création de prompt




########################################################################################
st.subheader("Générer un quiz avec ces paramètres")

num_questions_per_page = st.number_input('Nombre de questions à générer, par page du pdf ou du texte', min_value=1, max_value=10, value=1, step=1)
st.session_state['num_questions_per_page'] = num_questions_per_page

# Create radio button for selecting input method
input_method = st.radio("Sélectionnez la méthode d'entrée:", ("Upload de fichier", "Texte"))

if input_method == "Upload de fichier":
    # Upload PDF file

    uploaded_file = st.file_uploader(":female-student:", type=["pdf"])
    if st.button("Générer Quiz à partir du pdf", key=f"button_generer_from_pdf"):
        # if uploaded_file is not None:          
            with st.spinner("Génération du quizz..."):
                with open(f"data/{uploaded_file.name}", "wb") as f:
                    f.write(uploaded_file.getvalue())        
                    st.session_state['contexte']=selected_prompt['content']
                    st.session_state['questions'] = asyncio.run(pdf_to_quizz(f"data/{uploaded_file.name}",))

else:
    # Text input
    txt = st.text_area('Taper le texte à partir duquel vous voulez générer le quiz')
    if (st.button("Générer Quiz à partir du texte", key=f"button_generer_from_text")):
        if txt is not None:
            with st.spinner("Génération du quizz..."):
                st.session_state['contexte']=selected_prompt['content']
                st.session_state['questions'] = asyncio.run(txt_to_quizz(txt))

# def build_question(count, json_question):

#     if json_question.get(f"question") is not None:
#         st.write("Question: ", json_question.get(f"question", ""))
#         choices = ['A', 'B', 'C', 'D']
#         selected_answer = st.selectbox(f"Selectionnez votre réponse:", choices, key=f"select_{count}")
#         for choice in choices:
#             choice_str = json_question.get(f"{choice}", "None")
#             st.write(f"{choice} {choice_str}")
                    
#         color = ""
#         if st.button("Soumettre", key=f"button_{count}"):
#             rep = json_question.get(f"reponse")
#             if selected_answer == rep:
#                 color = ":green"
#                 st.write(f":green[Bonne réponse: {rep}]")
                
#             else:
#                 color = ":red"
#                 st.write(f":red[Mauvaise réponse. La bonne réponse est {rep}].")                

#         st.write(f"{color}[Votre réponse: {selected_answer}]")

#         count += 1

#     return count


if ('questions' in st.session_state):
#les questions ont été générées      

    # Display question   #neutralisé pour l'instant (bousquet)
    # count = 0
    # for json_question in st.session_state['questions']:
    #     build_question(count, json_question)
        
        with st.spinner("Génération du quizz ..."):
            json_questions = st.session_state['questions']
            # save into a file
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


            # remove extension .pdf from file name
            if file_name.endswith(".pdf"):
                file_name = file_name[:-4]

           #sauvegarde des questions au format json
            with open(f"data/quiz-{file_name}-{date_suffix}.json", "w", encoding='latin-1', errors='ignore') as f:
                str = json.dumps(json_questions)
                f.write(str)

           #génération d'un pdf avec questions et réponses (pour l'instant on se passe de cette option)
            # generate_pdf_quiz(f"data/quiz-{file_name}-{date_suffix}.json", json_questions)
            
            st.write("Quiz généré avec succès! (sauvegarde json dans le dossier data)")        

        #     quiz_text = generate_text_quiz(json_questions)
            
        #    # Split the text into lines
        #     lines = quiz_text.split('\n')

        #     # Count the number of lines, adding extra lines for long lines
        #     num_lines = sum((len(line) // 80 + 1) for line in lines)

        #     # Use num_lines as the height of the textarea
        #     st.text_area("Quiz", quiz_text, height=num_lines*20)
            
            line_height = 55 # Adjust this value to change the height of each line
            num_charac_per_line = 90 # Adjust this value to change the number of characters per line
            with st.form(key='edit_quiz'):
                for i, question_data in enumerate(json_questions):
                    st.checkbox(f"Sélectionner cette question", key=f"checkbox_{i+1}")
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
                
                submit_button = st.form_submit_button(label='Submit')