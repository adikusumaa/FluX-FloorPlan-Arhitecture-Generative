# rag/chunker.py
import pymupdf  # atau import fitz
import re

CHUNK_SIZE = 512
CHUNK_OVERLAP = 50

def extract_sections_from_pdf(pdf_path: str) -> dict:
    """Ekstrak teks per halaman, lalu deteksi heading berdasarkan pola."""
    doc = pymupdf.open(pdf_path)
    sections = {}
    current_section = "Abstract"
    current_text = ""
    
    for page in doc:
        text = page.get_text()
        lines = text.split('\n')
        for line in lines:
            # Deteksi heading: angka diikuti titik (1., 2., 3.1, dst)
            if re.match(r'^(\d+\.\d+|\d+)\.?\s+[A-Z]', line.strip()):
                if current_text:
                    sections[current_section] = current_text.strip()
                current_section = line.strip()
                current_text = ""
            else:
                current_text += " " + line.strip()
    
    if current_text:
        sections[current_section] = current_text.strip()
    
    return sections

def section_based_chunking(sections: dict, chunk_size: int = 512, overlap: int = 50) -> list[str]:
    """Potong per section, lalu split lebih lanjut jika terlalu panjang."""
    chunks = []
    for section_title, content in sections.items():
        # Jika content pendek, simpan utuh
        if len(content) <= chunk_size:
            chunks.append(f"[{section_title}]\n{content}")
        else:
            # Split berdasarkan kalimat
            sentences = re.split(r'(?<=[.!?])\s+', content)
            current_chunk = f"[{section_title}] "
            for sent in sentences:
                if len(current_chunk) + len(sent) <= chunk_size:
                    current_chunk += sent + " "
                else:
                    chunks.append(current_chunk.strip())
                    # Overlap: ambil beberapa kata terakhir
                    words = current_chunk.split()
                    overlap_text = " ".join(words[-overlap:]) if len(words) > overlap else ""
                    current_chunk = f"[{section_title}] " + overlap_text + " " + sent + " "
            if current_chunk:
                chunks.append(current_chunk.strip())
    return chunks