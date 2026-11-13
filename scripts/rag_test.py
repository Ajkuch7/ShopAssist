"""Print policy retrieval results for a question."""

import sys
from pathlib import Path

if __package__ in (None, ""):
	sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.rag.retriever import search_policy


def main() -> None:
	question = " ".join(sys.argv[1:]).strip()
	if not question:
		raise SystemExit('Usage: python -m scripts.rag_test "<question>"')
	for index, result in enumerate(search_policy(question), start=1):
		print(f"{index}. {result['source']} (score={result['score']:.4f})")
		print(result["content"])
		print()


if __name__ == "__main__":
	main()