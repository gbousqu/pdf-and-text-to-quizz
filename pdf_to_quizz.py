import asyncio
from langchain.document_loaders import PyPDFLoader
from quizz_generator import generate_quizz
from ui_utils import transform

async def pdf_to_quizz(pdf_file_name):


    loader = PyPDFLoader(pdf_file_name)
    pages = loader.load_and_split()

    sem = asyncio.Semaphore(10)  # Set the maximum number of parallel tasks

    async def process_page(page):
        async with sem:
            try:
                return await generate_quizz(page.page_content)
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
  
