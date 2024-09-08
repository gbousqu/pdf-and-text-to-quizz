"""LLM Chain specifically for generating examples for QCM (Question Choix Multiples) answering."""
from __future__ import annotations

from typing import Any

from langchain.chains.llm import LLMChain
from langchain.llms.base import BaseLLM
from langchain.output_parsers.regex import RegexParser

from langchain.prompts import PromptTemplate

import streamlit as st

import re


#DERNIERE VERSION FONCTIONNELLE
# template = """You are a university professor preparing questions for a quiz for undergraduate students. Given the following document, please generate exactly {num_questions_per_page} multiple-choice question (MCQs) with 4 options based on the document.
# Among the 4 options, exactly 2 or 3 must be corrects. The answer should be a string of the correct options, separated by a comma. For example, if the correct options are A and B, the answer should be A,B.
# Example question:

# Question 1,2, ... : question here  (the number of the question should be specified)
# CHOICE_A: choice here
# CHOICE_B: choice here
# CHOICE_C: choice here
# CHOICE_D: choice here
# Answer: correct options here (eg: A,C or A,B,C or ...)

# Each question should be detailed. You can propose a question that is not directly answered in the document or use information which is not directly in the document but can be inferred from it.
# The question and the choice should be in French (but keep the word CHOICE_X and Answer in english).
# the majority of the questions must have two or three correct answers, not just one.
# <Begin Document>
# {doc}
# <End Document>"""

# FIN DE LA DERNIERE VERSION FONCTIONNELLE


# Générer le parser

# output_keys = []
# for i in range(1, num_questions_per_page+1):
#     output_keys.extend([f"question{i}", f"A_{i}", f"B_{i}", f"C_{i}", f"D_{i}", f"reponse{i}"])

# chaine_regex = r"\n".join(f"Question {i}:\n?(.*?)\n ?CHOICE_A:(.*?)\nCHOICE_B:(.*?)\nCHOICE_C:(.*?)\nCHOICE_D:(.*?)\n\n?Answer: ?(.*?)" for i in range(1, num_questions_per_page+1))
# print("\n chaine regex: \n", repr(chaine_regex))
# print("\n output_keys: \n", output_keys)


# output_parser = RegexParser(
#     regex=chaine_regex,
#     output_keys=output_keys
# )

# print("\n output_parser:\n ", output_parser)



# PROMPT = PromptTemplate(
#     input_variables=["doc","num_questions_per_page"], template=template, output_parser=output_parser
# )

class QCMGenerateChain(LLMChain):
    """LLM Chain specifically for generating examples for QCM answering."""

    @classmethod
    def from_llm(cls, llm: BaseLLM, **kwargs: Any) -> QCMGenerateChain:
        """Load QA Generate Chain from LLM."""
        # Accéder à num_questions_per_page (nombre de questions à générer par page du pdf) dans la session de l'utilisateur (interface web streamlit)
        if "num_questions_per_page" not in st.session_state:
            st.session_state["num_questions_per_page"] = 2  # or any default value
        num_questions_per_page = st.session_state["num_questions_per_page"]     
       
        #on crée le parser adapté au nombre de questions générées par page
        type_question = st.session_state['type_question']  #on récupère le type de la question choisi par l'utilisateur via l'interface web streamlit

        if (type_question == "QCM avec une réponse correcte" or type_question == "QCM avec 1,2 ou 3 réponses correctes"):   
        
            output_keys = []

            for i in range(1, num_questions_per_page+1):
                output_keys.extend([f"question{i}", f"A_{i}", f"B_{i}", f"C_{i}", f"D_{i}", f"reponse{i}"])
                chaine_regex = r"\n\n?".join(rf"Question {i} *:\n*(.*?)\n+CHOICE_A:(.*?)\nCHOICE_B:(.*?)\nCHOICE_C:(.*?)\nCHOICE_D:(.*?)\n\n?Answer: ?(.*?)" for i in range(1, num_questions_per_page+1))
                chaine_regex += "$" #pour être sûr de récupérer la réponse de la dernière question

        elif (type_question == "Vrai/Faux"):
            output_keys = []

            for i in range(1, num_questions_per_page+1):
                output_keys.extend([f"question{i}", f"reponse{i}", f"explication{i}"])
                chaine_regex = r"\n\n?".join([rf"Question {i} *: *\n*([\s\S]*?)\n\n?Answer: *([\s\S]*?)\n\n?Explanation: *([\s\S]*?)" for i in range(1, num_questions_per_page+1)])
                chaine_regex += "$" #pour être sûr de récupérer la réponse de la dernière question
                # Supprimez les doubles barres obliques

        chaine_regex_temp = chaine_regex.replace("\n", "<br>")
        chaine_regex_repr = repr(chaine_regex_temp)
        chaine_regex_repr = chaine_regex_repr.replace("<br>", "\\n")
        chaine_regex_repr = chaine_regex_repr.replace("\\\\", "\\")
        print(f"chaine regex: \n{chaine_regex_repr}")

        print("\n output_keys: \n", output_keys)
        print("\n")        


        output_parser = RegexParser(
            regex=chaine_regex,
            output_keys=output_keys
        )
        #on utilise le prompt choisi par l'utilisateur via l'interface web streamlit
        contexte = st.session_state['contexte']

        fin_prompt = """
            <Begin Document>
            {doc}
            <End Document>"""
        
        format_question=st.session_state['format_question']

        template = contexte + format_question + fin_prompt
        PROMPT = PromptTemplate(
            input_variables=["doc","num_questions_per_page"], template=template, output_parser=output_parser
        )
        
        return cls(llm=llm, prompt=PROMPT, **kwargs)