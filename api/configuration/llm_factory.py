import os
from langchain_openai import ChatOpenAI, AzureChatOpenAI, OpenAIEmbeddings, AzureOpenAIEmbeddings
from langchain_ollama import OllamaEmbeddings
from api.configuration.configuration import (
    AZURE_DEPLOYMENT_NAME,
    OLLAMA_BASE_URL,
    OLLAMA_EMBEDDING_MODEL
)


class LLMFactory:
    _llm_instance = None
    _embed_instance = None

    @classmethod
    def get_llm(cls):
        cls._llm_instance = AzureChatOpenAI(
            azure_deployment=AZURE_DEPLOYMENT_NAME,
            api_version=os.environ.get("AZURE_OPENAI_API_VERSION"),
            temperature=0
        )
        return cls._llm_instance

    @classmethod
    def get_embeddings(cls):
        if cls._embed_instance:
            return cls._embed_instance

        print(f"Connecting to Ollama for Embeddings (Model: {OLLAMA_EMBEDDING_MODEL})...")
        try:
            cls._embed_instance = OllamaEmbeddings(
                base_url=OLLAMA_BASE_URL,
                model=OLLAMA_EMBEDDING_MODEL
            )
        except Exception as e:
            print(f"Failed to connect to Ollama: {e}")
            cls._embed_instance = OpenAIEmbeddings()

        return cls._embed_instance