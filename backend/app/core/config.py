from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    env: str = "local"
    ollama_url: str = "http://ollama:11434"
    ollama_model: str = "qwen3:8b"
    chroma_path: str = "./chroma_db"
    libro_path: str = "./data/libro/libro_radicacion.xlsx"
    bandeja_path: str = "./data/bandeja"
    maestro_path: str = "./data/maestro/maestro_proveedores.xlsx"

    class Config:
        env_file = ".env.example"

settings = Settings()
