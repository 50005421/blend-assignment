import os

DEFAULT_MODEL_TYPE = "azure"

os.environ["AZURE_OPENAI_ENDPOINT"] = f"""https://{os.environ["AZURE_RESOURCE_NAME"]}.openai.azure.com/"""
os.environ["AZURE_OPENAI_API_VERSION"] = "2024-05-01-preview"
AZURE_DEPLOYMENT_NAME = "gpt-4o"

OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_EMBEDDING_MODEL = "embeddinggemma:latest"

DB_USER = "postgres"
DB_PASSWORD = "root"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "blend_retails"
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"