import io

import fitz  # PyMuPDF
from PIL import Image


def pdf_to_images_with_pymupdf(pdf_path):
    pdf_document = fitz.open(pdf_path)
    images = []

    for page_num in range(pdf_document.page_count):
        page = pdf_document[page_num]
        # 페이지를 이미지로 렌더링
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x 해상도
        img_data = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_data))
        images.append(img)

    pdf_document.close()
    return images
