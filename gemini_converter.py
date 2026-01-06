import fitz  # PyMuPDF
import os
import google.generativeai as genai
import shutil
import re

# -------------------- CONFIGURATION --------------------
INPUT_FOLDER = "./input_pdfs"
OUTPUT_FOLDER = "./output_tex"
API_KEY = "AIzaSyC3RQ-85UgnNjcFqyPzUFlUUwyo9gtth1M"  # Hardcoded as per user request
# -------------------------------------------------------

def setup_gemini():
    genai.configure(api_key=API_KEY)

def extract_content_with_layout(pdf_path, images_output_dir):
    """
    Extracts text and saves images, attempting to keep them in order.
    Returns a single string containing text and [IMAGE: filename] markers.
    """
    doc = fitz.open(pdf_path)
    full_content = []
    
    if not os.path.exists(images_output_dir):
        os.makedirs(images_output_dir)

    print(f"Analyzing {pdf_path}...")

    section_id = 0

    for page_num, page in enumerate(doc):
        # 1. Get Text Blocks
        text_blocks = page.get_text("blocks")
        # Format: (x0, y0, x1, y1, "text", block_no, block_type)
        
        # 2. Get Images
        image_list = page.get_images(full=True)
        
        # We need to interleave text and images based on vertical position (y0)
        # Creating a unified list of (y0, x0, type, content)
        
        page_elements = []
        
        # Add text blocks
        for b in text_blocks:
            # b[4] is text, b[1] is y0
            page_elements.append({
                "y": b[1],
                "x": b[0],
                "type": "text",
                "content": b[4]
            })
            
        # Add images
        for img_index, img in enumerate(image_list):
            xref = img[0]
            # Get image rect to find its position
            # Some PDFs wrap images in XObjects which might not have simple rects on page
            # We try to find where it is drawn
            try:
                rects = page.get_image_rects(xref)
                if not rects:
                    continue # Image present but not displayed?
                
                # Use the first rect (usually images appear once)
                rect = rects[0]
                
                # Extract image bytes
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                ext = base_image["ext"]
                image_filename = f"image_p{page_num+1}_{img_index+1}.{ext}"
                image_path = os.path.join(images_output_dir, image_filename)
                
                with open(image_path, "wb") as f:
                    f.write(image_bytes)
                
                page_elements.append({
                    "y": rect.y0,
                    "x": rect.x0,
                    "type": "image",
                    "content": f"[IMAGE_MARKER: {image_filename}]"
                })
                
            except Exception as e:
                print(f"Warning: Could not extract image {xref} on page {page_num}: {e}")

        # Sort elements primarily by Y position (top to bottom), then X (left to right)
        # Note: Multi-column layouts might need smarter sorting, but simple sorting is a good start for Gemini to figure out context
        page_elements.sort(key=lambda item: (item["y"], item["x"]))
        
        for el in page_elements:
            full_content.append(el["content"])
            
    return "\n".join(full_content)

def generate_latex_with_gemini(text_content):
    """
    Sends the text content to Gemini and asks for IEEE LaTeX.
    """
    model = genai.GenerativeModel('gemini-2.0-flash')
    
    prompt_template = """
    You are an expert LaTeX typesetter.
    Convert the following text (extracted from a PDF) into a professional IEEE Conference format LaTeX document.
    
    STRICT REQUIREMENTS:
    1. **Content Fidelity**: READ EACH AND EVERY WORD. Do not summarize. Do not skip citations. Include the full abstract, introduction, methodology, results, conclusion, and references.
    2. **Images**: I have inserted markers like `[IMAGE_MARKER: filename.png]` in the text where images were detected. You must replace these markers with a proper LaTeX figure environment:
       ```latex
       \\begin{figure}[htbp]
       \\centerline{\\includegraphics[width=\\columnwidth]{filename.png}}
       \\caption{Place caption here if found nearby, else 'Figure'}
       \\label{fig}
       \\end{figure}
       ```
       Place the images as close as possible to their marker in the text flow.
    3. **Citations**: Identify citations in the text (e.g., [1], [2]) and ensure they link to the bibliography.
    4. **Bibliography**: Format the references section using standard IEEE `\\bibitem` format.
    5. **Structure**: Use `\\section{}`, `\\subsection{}` appropriately.
    6. **Hyperlinks**: You MUST include `\\usepackage{hyperref}` and `\\usepackage{url}` in the preamble.
    7. **Safety**: You MUST include `\\DeclareUnicodeCharacter{2002}{ }` and `\\DeclareUnicodeCharacter{0301}{\\'{e}}` (and similar common fixes) in the preamble to prevent compilation errors from unicode spaces.
    8. **Output**: Return ONLY the raw LaTeX code. Do not use markdown code blocks (```latex ... ```). Start directly with `\\documentclass`.
    
    Here is the content:
    HTML_CONTENT_PLACEHOLDER
    """
    
    prompt = prompt_template.replace("HTML_CONTENT_PLACEHOLDER", text_content)
    
    print("Generating LaTeX with Gemini 1.5 Pro (this may take a minute)...")
    import time
    for attempt in range(3):
        try:
            response = model.generate_content(prompt)
            text = response.text
            # Clean up if Gemini adds markdown code blocks despite instructions
            if text.startswith("```latex"):
                text = text[8:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            
            # --- AGGRESSIVE SANITIZATION ---
            # Use regex to replace ALL variants of unicode spaces with a standard ASCII space
            import re
            # Matches \u2000-\u200B (various widths), \u202F (narrow no-break), \u00A0 (NBSP)
            text = re.sub(r'[\u2000-\u200B\u202F\u00A0]', ' ', text)
            
            # Replace smart quotes with LaTeX equivalents
            text = text.replace('“', "``").replace('”', "''").replace('‘', "`").replace('’', "'")
            
            return text.strip()
        except Exception as e:
            print(f"Error calling Gemini API (Attempt {attempt+1}/3): {e}")
            if "429" in str(e) or "Resource has been exhausted" in str(e):
                print("Rate limit hit. Waiting 20 seconds...")
                time.sleep(20)
            else:
                break
    return None

def main():
    setup_gemini()
    
    if not os.path.exists(INPUT_FOLDER):
        os.makedirs(INPUT_FOLDER)
        print(f"Please put PDFs in {INPUT_FOLDER}")
        return

    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)

    files = [f for f in os.listdir(INPUT_FOLDER) if f.lower().endswith(".pdf")]
    
    if not files:
        print(f"No PDFs found in {INPUT_FOLDER}")
        return

    for pdf_file in files:
        input_path = os.path.join(INPUT_FOLDER, pdf_file)
        # Use a simple, short directory name to avoid Windows/Zip path length issues
        project_dir = os.path.join(OUTPUT_FOLDER, "latex_project")
        images_dir = project_dir 
        
        if os.path.exists(project_dir):
            shutil.rmtree(project_dir)
        os.makedirs(project_dir)
        
        print(f"Processing {pdf_file}...")
        
        try:
            # 1. Extract Text & Images
            raw_text = extract_content_with_layout(input_path, images_dir)
            
            # 2. Convert to LaTeX
            latex_code = generate_latex_with_gemini(raw_text)
            
            if latex_code:
                output_tex_path = os.path.join(project_dir, "main.tex")
                with open(output_tex_path, "w", encoding="utf-8") as f:
                    f.write(latex_code)
                print(f"SUCCESS: Saved project to {project_dir}")
                print(f" - Main tex file: {output_tex_path}")
                print(f" - Images extracted: {len(os.listdir(images_dir)) - 1}") # -1 for the tex file itself
                
                # 3. Create Zip file for Overleaf
                shutil.make_archive(project_dir, 'zip', project_dir)
                print(f"SUCCESS: Created zip file for Overleaf: {project_dir}.zip")
            else:
                print("FAILED: Gemini did not return valid LaTeX.")
                
        except Exception as e:
            print(f"CRITICAL ERROR processing {pdf_file}: {e}")

if __name__ == "__main__":
    main()
