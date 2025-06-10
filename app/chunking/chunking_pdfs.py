from client import es, pp
from PyPDF2 import PdfReader
from sliding_window_chunking import chunk, display_chunks

pdf_dir = "../../pdfs"
pdf_index = "chunked-pdf-index"


def convert_pdf_to_text(pdf_file):
    reader = PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text.strip()


def sample_run():
    long_text = convert_pdf_to_text(pdf_dir + "/WAC_246_-341_-0640.pdf")

    print(len(long_text))

    chunks = chunk(long_text, chunk_size=1000, overlap_ratio=0.5)
    print(f"Number of chunks: {len(chunks)}")
    display_chunks(chunks)
