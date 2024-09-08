# from langchain.llms import OpenAI
from langchain_openai import ChatOpenAI  # Mise à jour de l'import

from callback import MyCallbackHandler
from langchain.callbacks.base import BaseCallbackManager


class QaLlm():

    def __init__(self) -> None:
        manager = BaseCallbackManager([MyCallbackHandler()])
        self.llm = ChatOpenAI(temperature=0, callback_manager=manager, model_name="gpt-3.5-turbo")  #c'est celui par défaut (pas cher)

    def get_llm(self):
        return self.llm