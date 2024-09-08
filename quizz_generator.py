from qcm_chain import QCMGenerateChain
from qa_llm import QaLlm
import asyncio
import streamlit as st

async def llm_call(qa_chain: QCMGenerateChain, text: str):
    
    print(f"llm call running...")
    # batch_examples = await asyncio.gather(qa_chain.aapply_and_parse(text))

        # Supposons que qa_chain soit déjà initialisé avec un output_parser
    output_parser = qa_chain.prompt.output_parser
    
    # Utilisation de qa_chain pour obtenir la sortie brute
    raw_outputs = await asyncio.gather(qa_chain.aapply(text))

       # Aplatir la liste si nécessaire
    if isinstance(raw_outputs[0], list):
        raw_outputs = [item for sublist in raw_outputs for item in sublist]
    
    
    # Application manuelle du output_parser
    batch_examples = [output_parser.parse(output['text']) for output in raw_outputs]

    print(f"llm call done.")

    return batch_examples

async def generate_quizz(content:str):
    """
    Generates a quizz from the given content.
    """
    num_questions_per_page = st.session_state["num_questions_per_page"]
   
    qa_llm = QaLlm()
    qa_chain = QCMGenerateChain.from_llm(qa_llm.get_llm())

    return await llm_call(qa_chain, [{"doc": content, "num_questions_per_page": num_questions_per_page}])

    
