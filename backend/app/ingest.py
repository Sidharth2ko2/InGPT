from PyPDF2 import PdfReader
from app.db import cur, conn

def ingest_text(name: str, text: str):
    cur.execute("INSERT INTO documents (name, content) VALUES (?, ?)", (name, text))
    conn.commit()

def ingest_pdf(file):
    reader = PdfReader(file)
    text = "".join(page.extract_text() for page in reader.pages)
    ingest_text(file.filename, text)