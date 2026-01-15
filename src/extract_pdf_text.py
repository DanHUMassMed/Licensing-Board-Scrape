import fitz  # PyMuPDF
from pathlib import Path

PDF_DIR = Path("./voting_minutes_pdfs")
OUTPUT_DIR = Path("./voting_minutes_txt")
OUTPUT_DIR.mkdir(exist_ok=True)

def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extracts text from a PDF, preserving page order."""
    doc = fitz.open(pdf_path)
    all_text = []

    for page_num, page in enumerate(doc, start=1):
        text = page.get_text()
        # Preserve page breaks explicitly
        if text.strip():
            all_text.append(text.strip())
            all_text.append("\n-------------------------\n")
    doc.close()
    return "\n".join(all_text)

def process_pdf_directory(pdf_dir: Path, output_dir: Path):
    pdf_files = sorted(pdf_dir.glob("*.pdf"))  # sort by filename
    for pdf_file in pdf_files:
        text = extract_text_from_pdf(pdf_file)
        output_file = output_dir / f"{pdf_file.stem}.txt"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"Extracted {pdf_file.name} → {output_file.name}")

if __name__ == "__main__":
    process_pdf_directory(PDF_DIR, OUTPUT_DIR)
