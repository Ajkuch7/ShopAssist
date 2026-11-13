"""Send a small test message to the configured Ollama model."""

from app.core.llm import get_llm


def main() -> None:
    """Invoke the configured chat model with a simple greeting."""

    response = get_llm().invoke("hello")
    print(response.content)


if __name__ == "__main__":
    main()
