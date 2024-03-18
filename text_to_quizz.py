import asyncio
from quizz_generator import generate_quizz
from ui_utils import transform

# async def txt_to_quizz(content):

#     quizz = await generate_quizz(content)
#     if quizz is not None:
#         transformed_quizz = transform(quizz[0])
#         return transformed_quizz

#     return ''

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
                questions_page= await generate_quizz(page)
                print(f"questions_page: {questions_page}")
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
    
    for question in questions:
        if question is not None:
            all_questions.extend(transform(question[0]))
    return all_questions