from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextBox, LTChar, LTImage, LTFigure, LTLine, LTRect, LTCurve, LTTextContainer
import fitz

for pidx, page_layout in enumerate(extract_pages("test.pdf")):
    text_elements = [el for el in page_layout if isinstance(el, LTTextContainer)]
    for idx, element in enumerate(text_elements):
        if isinstance(element, LTTextContainer):
            element.vdistance
            print(f"{idx}: {element.get_text().strip()} [{element.x0}, {element.y0}, {element.x1}, {element.y1}]")


from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextBox, LTChar, LTImage, LTFigure, LTLine, LTRect, LTCurve
import fitz  # PyMuPDF

def get_elements_per_page(pdf_path):
    layout_data = []
    for page_layout in extract_pages(pdf_path):
        elements = []
        for element in page_layout:
            if isinstance(element, (LTTextBox, LTChar, LTImage, LTFigure, LTLine, LTRect, LTCurve)):
                x0, y0, x1, y1 = element.bbox
                center_x = (x0 + x1) / 2
                center_y = (y0 + y1) / 2
                elements.append({
                    "bbox": (x0, y0, x1, y1),
                    "center": (center_x, center_y)
                })
        layout_data.append(elements)
    return layout_data

def draw_debug_overlay(input_pdf, output_pdf, elements_by_page):
    doc = fitz.open(input_pdf)
    for page_index, elements in enumerate(elements_by_page):
        page = doc[page_index]
        height = page.rect.height
        for el in elements:
            x0, y0, x1, y1 = el["bbox"]
            cx, cy = el["center"]
            
            # Convert coordinates to fitz coordinate system
            fitz_rect = fitz.Rect(x0, height - y1, x1, height - y0)
            fitz_cx = cx
            fitz_cy = height - cy
            
            # Draw red rectangle
            page.draw_rect(fitz_rect, color=(1, 0, 0), width=0.5)
            
            # Draw red circle at center
            radius = 2
            page.draw_circle(fitz.Point(fitz_cx, fitz_cy), radius, color=(1, 0, 0), fill=(1, 0, 0))
            
            # Draw center coordinates text slightly above rectangle
            label = f"({cx:.1f}, {cy:.1f})"
            text_pos = fitz.Point(cx, height - y1 - 5)
            page.insert_text(text_pos, label, fontsize=6, color=(1, 0, 0))
    
    doc.save(output_pdf)

if __name__ == "__main__":
    input_pdf = "test.pdf"
    output_pdf = "test_debug.pdf"

    print("Extracting elements...")
    elements_by_page = get_elements_per_page(input_pdf)

    print("Drawing debug info...")
    draw_debug_overlay(input_pdf, output_pdf, elements_by_page)

    print(f"Done. Debug file saved as '{output_pdf}'")
