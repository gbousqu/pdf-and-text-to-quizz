import streamlit as st
from ui_utils import check_password
from pdf_to_quizz import pdf_to_quizz
from text_to_quizz import txt_to_quizz
from generate_pdf import generate_pdf_quiz
import json

import asyncio

import os
from datetime import datetime

# Get OpenAI API key
# openai_api_key = "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"

os.environ['OPENAI_API_KEY'] = "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"

openai_api_key = os.getenv('OPENAI_API_KEY')
st.write("OPENAI_API_KEY: ", openai_api_key)


st.title("PDF to Quiz (:-)(-: )")

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

# Upload PDF file
uploaded_file = st.file_uploader(":female-student:", type=["pdf"])
txt = st.text_area('Taper le texte à partir duquel vous voulez générer le quiz')

if st.button("Générer Quiz", key=f"button_generer"):
    if txt is not None:
        with st.spinner("Génération du quizz..."):
            st.session_state['questions'] = asyncio.run(txt_to_quizz(txt))
            st.write("Quizz généré avec succès!")

if uploaded_file is not None:    
    old_file_name = st.session_state.get('uploaded_file_name', None)
    if (old_file_name != uploaded_file.name):
        # Convert PDF to text
        with st.spinner("Génération du quizz..."):

            with open(f"data/{uploaded_file.name}", "wb") as f:
                f.write(uploaded_file.getvalue())        

            # Initialize session state
            st.session_state['uploaded_file_name'] = uploaded_file.name
            st.session_state['questions'] = asyncio.run(pdf_to_quizz(f"data/{uploaded_file.name}"))

            st.write("Quizz généré avec succès!")

if ('questions' in st.session_state):
    # Display question   #neutralisé pour l'instant (bousquet)
    # count = 0
    # for json_question in st.session_state['questions']:
    #     build_question(count, json_question)
        
    # generate pdf quiz
    if st.button("Générer PDF Quiz", key=f"button_generer_quiz"):
        with st.spinner("Génération du quizz en PDF..."):
            json_questions = st.session_state['questions']
            # save into a file
            now = datetime.now()
            date_suffix = now.strftime("%Y_%m_%d_%H_%M_%S") 
            if uploaded_file is not None:
                file_name = uploaded_file.name
            else:
                now = datetime.now()
                file_name = date_suffix #ajout bousquet, pour le cas où on fournit du texte

            # remove extension .pdf from file name
            if file_name.endswith(".pdf"):
                file_name = file_name[:-4]

            with open(f"data/quiz-{file_name}-{date_suffix}.json", "w", encoding='latin-1', errors='ignore') as f:
                str = json.dumps(json_questions)
                f.write(str)

            generate_pdf_quiz(f"data/quiz-{file_name}-{date_suffix}.json", json_questions)
            
            st.write("PDF Quiz généré avec succès!")        