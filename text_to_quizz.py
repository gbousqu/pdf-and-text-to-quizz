import asyncio
from quizz_generator import generate_quizz
from ui_utils import transform
import streamlit as st


def split_text_into_pages(text, page_length):
    # Découper le texte en pages
    return [text[i:i+page_length] for i in range(0, len(text), page_length)]

async def txt_to_quizz(content):
    # Découper le contenu en pages
    pages = split_text_into_pages(content, 1000)  # Découpe le contenu en pages de 1000 caractères

    sem = asyncio.Semaphore(10)  # Set the maximum number of parallel tasks

    async def process_page(page):
        async with sem:
            try:
                #c'est là qu'on appelle la fonction qui génère les questions
                questions_page= await generate_quizz(page)
                print(f"\n questions_page: {questions_page}")
                return questions_page
            except ValueError as e:
                print(f"Error generating quiz: {e}")
                return None

    tasks = []
    for page in pages:
        task = process_page(page)
        tasks.append(task)

    all_questions = []

    questions = await asyncio.gather(*tasks)   

    print(f"questions: {questions}") 
    
    for question in questions:
        if question is not None:
            transformed_question = transform(question[0])
            print(f"\n transformed_question: {transformed_question}")
            all_questions.extend(transformed_question)

    print(f"all_questions: {all_questions}")

    st.session_state['questions'] = all_questions

    return all_questions