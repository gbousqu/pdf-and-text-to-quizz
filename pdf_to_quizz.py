import asyncio
from langchain.document_loaders import PyPDFLoader
from quizz_generator import generate_quizz
from ui_utils import transform


async def pdf_to_quizz(pdf_file_name):


    loader = PyPDFLoader(pdf_file_name)

    #ancienne  avec load_and_split : 
    pages = loader.load_and_split()

    sem = asyncio.Semaphore(10)  # Set the maximum number of parallel tasks


#CODE FONCTIONNEL, MAIS QUI PERD LES QUESTIONS EN CAS d'ERREUR (dépassement du rate limit)
    # async def process_page(page):
    #     async with sem:
    #         try:
    #             questions_page = await generate_quizz(page.page_content)
    #             print(f"questions_page: {questions_page}")
    #             return questions_page
    #         except ValueError as e:
    #             print(f"Error generating quiz: {e}")
    #             return None

    # tasks = []
    # for page in pages:
    #     task = process_page(page)
    #     tasks.append(task)

    # all_questions = []

    # questions = await asyncio.gather(*tasks)    
    
    # for question in questions:
    #     if question is not None:
    #         all_questions.extend(transform(question[0]))
    # return all_questions
  
    all_questions = []

    async def process_page(page):
        async with sem:
            try:
                questions_page = await generate_quizz(page.page_content)
                print(f"questions_page: {questions_page}")
                if questions_page is not None:
                    all_questions.extend(transform(questions_page[0]))
                return questions_page
            except ValueError as e:
                print(f"Error generating quiz: {e}")
                return None

    tasks = [process_page(page) for page in pages]

    for future in asyncio.as_completed(tasks):
        try:
            await future
        except Exception as e:
            print(f"Error: {e}")

    return all_questions