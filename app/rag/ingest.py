"""Build persistent Chroma collections from synthetic policies and products."""

from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sqlalchemy import select

from app.core.config import PROJECT_ROOT, get_settings
from app.core.llm import get_embeddings
from app.db.models import Product
from app.db.session import session_scope


POLICY_COLLECTION = "policies"
PRODUCT_COLLECTION = "products"


def _store(collection: str) -> Chroma:
	return Chroma(
		collection_name=collection,
		persist_directory=str((PROJECT_ROOT / get_settings().chroma.path).resolve()),
		embedding_function=get_embeddings(),
	)


def _replace_source(store: Chroma, documents: list[Document], source: str) -> None:
	"""Delete prior source chunks before adding deterministic replacements."""

	collection = store._collection
	existing = collection.get(where={"source": source})
	if existing.get("ids"):
		collection.delete(ids=existing["ids"])
	if documents:
		ids = [f"{source}:{index}" for index in range(len(documents))]
		store.add_documents(documents, ids=ids)


def ingest_policies() -> int:
	"""Chunk and embed every policy markdown file."""

	splitter = RecursiveCharacterTextSplitter(chunk_size=700, chunk_overlap=80)
	store = _store(POLICY_COLLECTION)
	count = 0
	for path in sorted((PROJECT_ROOT / "data" / "policies").glob("*.md")):
		source = path.relative_to(PROJECT_ROOT).as_posix()
		documents = splitter.create_documents(
			[path.read_text(encoding="utf-8")],
			metadatas=[{"source": source, "kind": "policy", "filename": path.name}],
		)
		_replace_source(store, documents, source)
		count += len(documents)
	return count


def ingest_products() -> int:
	"""Embed products currently stored in SQLite with searchable metadata."""

	store = _store(PRODUCT_COLLECTION)
	with session_scope() as session:
		products = session.scalars(select(Product)).all()
	documents = [
		Document(
			page_content=f"{product.name}. {product.description}",
			metadata={"source": f"product:{product.product_id}", "kind": "product", "product_id": product.product_id, "name": product.name, "category": product.category, "price": product.price},
		)
		for product in products
	]
	for document in documents:
		_replace_source(store, [document], document.metadata["source"])
	return len(documents)


def ingest_all() -> tuple[int, int]:
	"""Ingest policies and products, replacing prior source records."""

	return ingest_policies(), ingest_products()


if __name__ == "__main__":
	print(f"Ingested policies={ingest_policies()} products={ingest_products()}")