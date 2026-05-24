import os


class Settings:
	openai_api_key: str | None
	gemini_api_key: str | None
	llm_provider: str
	ollama_base_url: str
	ollama_model: str

	def __init__(self):
		self.openai_api_key = os.environ.get("OPENAI_API_KEY")
		self.gemini_api_key = os.environ.get("GEMINI_API_KEY")
		self.llm_provider = os.environ.get("LLM_PROVIDER", "ollama").strip().lower()
		self.ollama_base_url = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
		self.ollama_model = os.environ.get("OLLAMA_MODEL", "qwen2.5-coder:7b")
		# Allow disabling LLM usage even if key present
		self.use_llm = os.environ.get("USE_LLM", "1") not in ("0", "false", "False")
		# Allow using structured output / function-calling when supported
		self.use_structured_output = os.environ.get("USE_STRUCTURED_OUTPUT", "0") not in ("0", "false", "False")
		# Use a local LLM mock for offline testing (no network)
		self.use_local_llm_mock = os.environ.get("USE_LOCAL_LLM_MOCK", "0") not in ("0", "false", "False")
		self.gemini_model = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
		self.openai_model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")


settings = Settings()

