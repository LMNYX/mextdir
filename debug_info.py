from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextBox, LTChar, LTImage, LTFigure, LTLine, LTRect, LTCurve, LTTextContainer
import fitz
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

for pidx, page_layout in enumerate(extract_pages("test.pdf")):
    text_elements = [el for el in page_layout if isinstance(el, LTTextContainer)]
    for idx, element in enumerate(text_elements):
        if isinstance(element, LTTextContainer):
            element.vdistance
            print(f"{idx}: {element.get_text().strip()} [{element.x0}, {element.y0}, {element.x1}, {element.y1}]")




progress_lock = threading.Lock()
drawn_pages = 0  # global counter for drawing progress

def extract_elements_for_page(page_layout, page_number):
    elements = []
    for element in page_layout:
        if isinstance(element, (LTTextBox, LTChar, LTImage, LTFigure, LTLine, LTRect, LTCurve)):
            x0, y0, x1, y1 = element.bbox
            elements.append({
                "bbox": (x0, y0, x1, y1)
            })
    print(f"[✓] Extracted page {page_number}")
    return (page_number, elements)

def get_elements_multithreaded(pdf_path):
    pages = list(enumerate(extract_pages(pdf_path)))
    results = [None] * len(pages)
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(extract_elements_for_page, layout, idx) for idx, layout in pages]
        for future in as_completed(futures):
            idx, result = future.result()
            results[idx] = result
    return results

def draw_on_page(doc, page_index, elements, total_pages):
    global drawn_pages
    page = doc[page_index]
    height = page.rect.height
    for elindex, el in enumerate(elements):
        print(f"{page_index+1}/{len(doc)}:: Drawing {elindex}/{len(elements)} <{el}>")
        x0, y0, x1, y1 = el["bbox"]
        fitz_rect = fitz.Rect(x0, height - y1, x1, height - y0)
        page.draw_rect(fitz_rect, color=(1, 0, 0), width=0.5)

        corners = {
            "x0,y0": (x0, y0),
            "x0,y1": (x0, y1),
            "x1,y0": (x1, y0),
            "x1,y1": (x1, y1)
        }

        for _, (x, y) in corners.items():
            fx, fy = x, height - y
            page.draw_circle(fitz.Point(fx, fy), radius=2, color=(1, 0, 0), fill=(1, 0, 0))
            label = f"({x:.1f}, {y:.1f})"
            page.insert_text(fitz.Point(fx + 2, fy - 6), label, fontsize=6, color=(1, 0, 0))

    with progress_lock:
        drawn_pages += 1
        print(f"[✓] Drawn page {page_index} ({drawn_pages}/{total_pages})")

def draw_debug_overlay_multithreaded(input_pdf, output_pdf, elements_by_page):
    doc = fitz.open(input_pdf)
    total_pages = len(doc)
    with ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(draw_on_page, doc, idx, elements_by_page[idx], total_pages)
            for idx in range(total_pages)
        ]
        for f in as_completed(futures):
            f.result()
    doc.save(output_pdf)

if __name__ == "__main__":
    input_pdf = "test.pdf"
    output_pdf = "test_debug.pdf"

    print("Starting PDF element extraction...")
    elements_by_page = get_elements_multithreaded(input_pdf)

    print("\nStarting overlay drawing...")
    draw_debug_overlay_multithreaded(input_pdf, output_pdf, elements_by_page)

    print(f"\n[✓] Done. Saved debug file as '{output_pdf}'")