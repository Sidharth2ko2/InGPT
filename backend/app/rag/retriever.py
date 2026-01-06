from chromadb import Client
from ollama import embeddings

client = Client()
collection = client.get_or_create_collection("docs")

def add_doc(doc_id: str, text: str):
    emb = embeddings(model="nomic-embed-text", prompt=text)["embedding"]
    collection.add(ids=[doc_id], embeddings=[emb], documents=[text])

def retrieve(query: str):
    qemb = embeddings(model="nomic-embed-text", prompt=query)["embedding"]
    res = collection.query(query_embeddings=[qemb], n_results=3)
    return res["documents"], res["distances"]