import sys
from pathlib import Path
from PyPDF2 import PdfReader


def extract_text(pdf_path: str, out_path: str):
    reader = PdfReader(pdf_path)
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open('w', encoding='utf-8') as f:
        for i, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ''
            f.write(text)
            f.write('\n\n--- PAGE %d ---\n\n' % i)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python extract_pdf.py <pdf-path> [out.txt]')
        sys.exit(1)
    pdf = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else pdf + '.txt'
    extract_text(pdf, out)
    print('Wrote', out)
