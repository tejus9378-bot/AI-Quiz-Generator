from pathlib import Path


def extract_text(uploaded_file) -> tuple[str, int]:
    name = uploaded_file.name
    suffix = Path(name).suffix.lower()
    data = uploaded_file.getvalue()

    if suffix == ".txt":
        return data.decode("utf-8", errors="ignore"), 1

    if suffix == ".pdf":
        from pypdf import PdfReader
        import io
        reader = PdfReader(io.BytesIO(data))
        pages = []
        for page in reader.pages:
            pages.append(page.extract_text() or "")
        return "\n\n".join(pages), len(reader.pages)

    if suffix == ".docx":
        from docx import Document
        import io
        doc = Document(io.BytesIO(data))
        text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        return text, 1

    raise ValueError("Unsupported file type. Use PDF, DOCX, or TXT.")
