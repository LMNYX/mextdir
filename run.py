from pdfminer.high_level import extract_pages, extract_text
from pdfminer.layout import LTTextContainer, LTTextBoxHorizontal, LTImage, LTFigure
import os
import zlib
from io import BytesIO
from PIL import Image
import re
import math

def euclidean_distance(x1, y1, x2, y2):
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

def closest_element_to_coordinates(pdf_path, target_x, target_y, page_index):
    closest_element = None
    closest_distance = float('inf')

    # Use page_numbers to only extract the desired page
    for page_layout in extract_pages(pdf_path, page_numbers=[page_index]):
        for element in page_layout:
            if isinstance(element, LTTextBoxHorizontal):
                x0, y0, x1, y1 = element.bbox
                center_x = (x0 + x1) / 2
                center_y = (y0 + y1) / 2
                distance = euclidean_distance(center_x, center_y, target_x, target_y)

                if distance < closest_distance:
                    closest_distance = distance
                    closest_element = element

    return closest_element, closest_distance

def determine_image_type(filters):
    if not filters:
        return None

    if isinstance(filters, (list, tuple)):
        first = filters[0]
    else:
        first = filters

    if isinstance(first, tuple):
        filter_name = first[0]
    else:
        filter_name = first

    if hasattr(filter_name, 'name'):
        filter_name = filter_name.name
    elif not isinstance(filter_name, str):
        filter_name = str(filter_name)

    if filter_name == "DCTDecode":
        return "jpg"
    elif filter_name == "JPXDecode":
        return "jp2"
    elif filter_name == "FlateDecode":
        return "png"  # We'll handle this separately
    else:
        return None

def save_image(lt_image, page_number, images_folder):
    saved_files = []  # List to store saved files

    if not lt_image.stream:
        print(f"Skipping {lt_image.name}: no stream found.")
        return saved_files

    filters = lt_image.stream.get_filters()
    img_type = determine_image_type(filters)

    if img_type is None:
        print(f"Skipping {lt_image.name}: unsupported image type.")
        return saved_files

    try:
        raw_data = lt_image.stream.get_data()

        # Handling FlateDecode (compressed raw image data)
        if img_type == "png" and filters[0] == "FlateDecode":
            raw_data = zlib.decompress(raw_data)  # Decompress the data
            image = Image.open(BytesIO(raw_data))
            filename = f"page_{page_number}_{lt_image.name}.png"
            filepath = os.path.join(images_folder, filename)
            image.save(filepath)
            saved_files.append(filepath)
        
        # Handling DCTDecode (JPEG)
        elif img_type == "jpg":
            filename = f"page_{page_number}_{lt_image.name}.jpg"
            filepath = os.path.join(images_folder, filename)
            with open(filepath, "wb") as f:
                f.write(raw_data)
            saved_files.append(filepath)
        
    except Exception as e:
        print(f"Error saving image {lt_image.name}: {e}")

    return saved_files

def extract_images_from_page(pdf_path, target_page, images_folder="extracted_images"):
    os.makedirs(images_folder, exist_ok=True)
    all_saved_files = []  # List to store all saved files for the page

    for page_number, layout in enumerate(extract_pages(pdf_path), start=1):
        if page_number != target_page:
            continue

        for element in layout:
            if isinstance(element, LTFigure):
                for sub_element in element:
                    if isinstance(sub_element, LTImage):
                        saved_files = save_image(sub_element, page_number, images_folder)
                        all_saved_files.extend(saved_files)
                    elif isinstance(sub_element, LTFigure):
                        # Handle nested figures
                        for nested in sub_element:
                            if isinstance(nested, LTImage):
                                saved_files = save_image(nested, page_number, images_folder)
                                all_saved_files.extend(saved_files)

    return all_saved_files

extracted_data = []

for pidx, page_layout in enumerate(extract_pages("test.pdf")):
    print(f"Page {pidx+1} -----")


    page_extraction = {
        "prefecture": "", #
        "city": "", # 
        "name": "", #
        "address": "", #
        "contact_company": "", #
        "contact_data": "", #
        "zoning": "",
        "size": "",
        "structure": "",
        "completion_year": "",
        "facility_category": "",
        "building_area": "",
        "floor_area": "",
        "floors_n": "",
        "recruitment_details": "",
        "transfer_conditions": "",
        "remarks": "",
        "images": [], #
        "tags": [] #
    }
    text_elements = [el for el in page_layout if isinstance(el, LTTextContainer)]
    
    page_extraction['prefecture'] = text_elements[0].get_text().strip()
    page_extraction['city'] = text_elements[1].get_text().strip()
    page_extraction['name'] = text_elements[2].get_text().strip()
    page_extraction['address'] = text_elements[3].get_text().strip()
    page_extraction['contact_company'] = text_elements[6].get_text().strip()
    offset = 0

    if (re.match(r'^(0\d{1,4})[-\s]?\d{2,4}[-\s]?\d{2,4}|\d{10}$', text_elements[7].get_text().strip())):
        page_extraction['contact_data'] = text_elements[7].get_text().strip()
    else:
        test = closest_element_to_coordinates("test.pdf", 777, 525, pidx+1)
        if test and len(test) > 0 and test[0] is not None:
            page_extraction['contact_data'] = test[0].get_text().strip()
            page_extraction['tags'].append("CONTACT_DATA_OCR")
        else:
            page_extraction['contact_data'] = '無し'

    l = [303.19780000000003, 74.88]

    zoning_info_probable = closest_element_to_coordinates("test.pdf", 74.88, 303.1978, pidx)
    if zoning_info_probable and len(zoning_info_probable) > 0 and zoning_info_probable[0] is not None:
        page_extraction['zoning'] = zoning_info_probable[0].get_text().strip()
        page_extraction['tags'].append("ZONING_DATA_OCR")
    else:
        page_extraction['zoning'] = '無し'

    size_info_probable = closest_element_to_coordinates("test.pdf", 190, 325, pidx)
    if size_info_probable and len(size_info_probable) > 0 and size_info_probable[0] is not None:
        page_extraction['size'] = size_info_probable[0].get_text().strip()
        page_extraction['tags'].append("SIZE_DATA_OCR")
    else:
        page_extraction['size'] = '無し'
    


    # Images
    page_extraction['images'] = extract_images_from_page('test.pdf', pidx)


    # for idx, element in enumerate(text_elements):
    #     if isinstance(element, LTTextContainer):
    #         print(f"{idx}: {element.get_text().strip()} [{element.y0}, {element.x0}]")
    print(page_extraction)
