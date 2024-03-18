"""LLM Chain specifically for generating examples for QCM (Question Choix Multiples) answering."""
from __future__ import annotations

from typing import Any

from langchain.chains.llm import LLMChain
from langchain.llms.base import BaseLLM
from langchain.output_parsers.regex import RegexParser

from langchain.prompts import PromptTemplate


#cas d'une seule question généré par page du pdf
# template = """You are a teacher preparing questions for a quiz. Given the following document, please generate one multiple-choice question (MCQs) with 4 options based on the document.
# Among the 4 options, exactly 2 or 3 must be corrects. The answer should be a string of the correct options, separated by a comma. For example, if the correct options are A and B, the answer should be A,B.
# Example question:

# Question: question here
# CHOICE_A: choice here
# CHOICE_B: choice here
# CHOICE_C: choice here
# CHOICE_D: choice here
# Answer: correct options here (eg: A,C or A,B,C or ...)

# These questions should be detailed and solely based on the information provided in the document.
# The question and the choice should be in French (but keep the word CHOICE_X and Answer in english).

# <Begin Document>
# {doc}
# <End Document>"""

#cas de deux questions générées par page du pdf, sous forme de qcm

# template = """You are a teacher preparing questions for a quiz. Given the following document, please generate 2 multiple-choice questions (MCQs) with 4 options based on the document.
# Among the 4 options, only one is correct. The answer should be the letter of the correct option. For example, if the correct option is A, the answer should be A.
# Example question:

# Question: question here
# CHOICE_A: choice here
# CHOICE_B: choice here
# CHOICE_C: choice here
# CHOICE_D: choice here
# Answer: A or B or C or D (only one letter)

# These questions should be detailed and solely based on the information provided in the document.
# The ouput language is French.

# <Begin Document>
# {doc}
# <End Document>"""

# output_parser = RegexParser(
#     regex=r"Question\s?\d?:\n?(.*?)\n\s?CHOICE_A:(.*?)\nCHOICE_B:(.*?)\nCHOICE_C:(.*?)\nCHOICE_D:(.*?)\n\n?Answer:\s?(.*?)$",
#     output_keys=["question1", "A_1", "B_1", "C_1", "D_1", "reponse1"]
# )

########################################
#cas de deux questions générés par page
# template = """You are a teacher preparing questions for a quiz. Given the following document, please generate exactly TWO multiple-choice question (MCQs) with 4 options based on the document.
# Among the 4 options, exactly 2 or 3 must be corrects. The answer should be a string of the correct options, separated by a comma. For example, if the correct options are A and B, the answer should be A,B.
# Example question:

# Question 1 (or 2): question here
# CHOICE_A: choice here
# CHOICE_B: choice here
# CHOICE_C: choice here
# CHOICE_D: choice here
# Answer: correct options here (eg: A,C or A,B,C or ...)

# These questions should be detailed and solely based on the information provided in the document.
# The question and the choice should be in French (but keep the word CHOICE_X and Answer in english).

# <Begin Document>
# {doc}
# <End Document>"""

#variante avec deux questions générées par page
template = """You are a university professor preparing questions for a quiz for undergraduate students. Given the following document, please generate exactly TWO multiple-choice question (MCQs) with 4 options based on the document.
Among the 4 options, exactly 2 or 3 must be corrects. The answer should be a string of the correct options, separated by a comma. For example, if the correct options are A and B, the answer should be A,B.
Example question:

Question 1 (or 2): question here
CHOICE_A: choice here
CHOICE_B: choice here
CHOICE_C: choice here
CHOICE_D: choice here
Answer: correct options here (eg: A,C or A,B,C or ...)

Each question should be detailed. You can propose a question that is not directly answered in the document au use information which is not directly in the document but can be inferred from it.
The question and the choice should be in French (but keep the word CHOICE_X and Answer in english).


<Begin Document>
{doc}
<End Document>"""
output_parser = RegexParser(
    regex=r"Question\s?\d?:\n?(.*?)\n\s?CHOICE_A:(.*?)\nCHOICE_B:(.*?)\nCHOICE_C:(.*?)\nCHOICE_D:(.*?)\n\n?Answer:\s?(.*?)\n\n?Question\s?\d?:\n?(.*?)\n\s?CHOICE_A:(.*?)\nCHOICE_B:(.*?)\nCHOICE_C:(.*?)\nCHOICE_D:(.*?)\n\n?Answer:\s?(.*?)$",
    output_keys=["question1", "A_1", "B_1", "C_1", "D_1", "reponse1", "question2", "A_2", "B_2", "C_2", "D_2", "reponse2"]
)





# output_parser = RegexParser(
#     regex=r"Question\s?\d?:\n?(.*?)\n\s?CHOICE_A:(.*?)\nCHOICE_B:(.*?)\nCHOICE_C:(.*?)\nCHOICE_D:(.*?)\n\n?Answer:\s?(.*?)(?:\n\n?Question\s?\d?:\n?(.*?)\n\s?CHOICE_A:(.*?)\nCHOICE_B:(.*?)\nCHOICE_C:(.*?)\nCHOICE_D:(.*?)\n\n?Answer:\s?(.*?))?",
#     output_keys=["question1", "A_1", "B_1", "C_1", "D_1", "reponse1", "question2", "A_2", "B_2", "C_2", "D_2", "reponse2"]
# )



PROMPT = PromptTemplate(
    input_variables=["doc"], template=template, output_parser=output_parser
)

class QCMGenerateChain(LLMChain):
    """LLM Chain specifically for generating examples for QCM answering."""

    @classmethod
    def from_llm(cls, llm: BaseLLM, **kwargs: Any) -> QCMGenerateChain:
        """Load QA Generate Chain from LLM."""
        return cls(llm=llm, prompt=PROMPT, **kwargs)