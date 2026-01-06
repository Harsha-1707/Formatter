import fitz  # PyMuPDF
import os
import shutil
import re
import time
from mistralai import Mistral

# -------------------- CONFIGURATION --------------------
INPUT_FOLDER = "./input_pdfs"
OUTPUT_FOLDER = "./output_tex"
API_KEY = "t4ruQxwCrtVFvHghf58u0huQb3vYPdiG" 
MODEL_NAME = "mistral-large-latest"
# -------------------------------------------------------

def setup_mistral():
    return Mistral(api_key=API_KEY)

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

    for page_num, page in enumerate(doc):
        # 1. Get Text Blocks
        text_blocks = page.get_text("blocks")
        # Format: (x0, y0, x1, y1, "text", block_no, block_type)
        
        # 2. Get Images
        image_list = page.get_images(full=True)
        
        page_elements = []
        
        # Add text blocks
        for b in text_blocks:
            page_elements.append({
                "y": b[1],
                "x": b[0],
                "type": "text",
                "content": b[4]
            })
            
        # Add images
        for img_index, img in enumerate(image_list):
            xref = img[0]
            try:
                rects = page.get_image_rects(xref)
                if not rects:
                    continue 
                
                rect = rects[0]
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

        # Sort elements primarily by Y position
        page_elements.sort(key=lambda item: (item["y"], item["x"]))
        
        for el in page_elements:
            full_content.append(el["content"])
            
    return "\n".join(full_content)

def generate_latex_with_mistral(client, text_content):
    """
    Sends the text content to Mistral and asks for IEEE LaTeX.
    """
    prompt_template = """
    You are an expert LaTeX typesetter.
    Convert the following text (extracted from a PDF) into a professional IEEE Conference format LaTeX document.
    
    STRICT REQUIREMENTS:
    1. **VERBATIM CONTENT (CRITICAL)**: You are a conversion engine, not an editor. You MUST NOT rephrase, summarize, or "improve" the text. Keep every single word, sentence structure, and grammatical quirk EXACTLY as found in the source text. Your job is ONLY to add LaTeX markup.
    
    2. **SMART CITATION INJECTION**: 
       - The extracted text might lack explicit citation markers (like `[1]`). 
       - You must analyze the **References/Bibliography** section at the end of the text.
       - As you process the body text, if you see a mention of a specific author, paper title, or unique concept that clearly matches one of the references, **INSERT** a citation command `\\cite{refN}` at that location.
       - Example: If text says "Smith showed..." and Reference 3 is "Smith et al...", change text to "Smith showed... \\cite{ref3}".
       - Also convert existing `[1]` to `\\cite{ref1}`.

    3. **Images**: Replace `[IMAGE_MARKER: filename]` with:
       ```latex
       \\begin{figure}[htbp]
       \\centerline{\\includegraphics[width=\\columnwidth]{filename}}
       \\caption{Figure} 
       \\end{figure}
       ```

    4. **Bibliography & Reliability**:
       - Create `\\begin{thebibliography}{99}` at the end.
       - **Validation**: ONLY include references that are valid (real papers/books). DISCARD obvious OCR errors or junk lines.
       - Format as `\\bibitem{refN} Author, "Title", Source, Year.` matching the N used in your citations.

    5. **Formatting**: Use `\\section{}`, `\\subsection{}` based on the layout, but primarily preserve the structure.
    
    6. **Preamble**: Start with `\\documentclass[conference]{IEEEtran}`. Include `\\usepackage{cite}`, `\\usepackage{hyperref}`, `\\usepackage{url}`, `\\usepackage{graphicx}`. Add `\\DeclareUnicodeCharacter{2002}{ }`.

    7. **Output**: Return ONLY the raw LaTeX code. No markdown blocks.

    Here is the content:
    HTML_CONTENT_PLACEHOLDER
    """
    
    prompt = prompt_template.replace("HTML_CONTENT_PLACEHOLDER", text_content)
    
    print(f"Generating LaTeX with Mistral ({MODEL_NAME})...")
    
    for attempt in range(3):
        try:
            chat_response = client.chat.complete(
                model=MODEL_NAME,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ]
            )
            
            text = chat_response.choices[0].message.content
            
            # Clean up markdown
            if text.startswith("```latex"):
                text = text[8:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            
            # --- SANITIZATION ---
            # Replace common unicode spaces causing LaTeX errors
            text = re.sub(r'[\u2000-\u200B\u202F\u00A0]', ' ', text)
            
            # Replace smart quotes with LaTeX equivalents
            text = text.replace('“', "``").replace('”', "''").replace('‘', "`").replace('’', "'")
            
            return text.strip()
            
        except Exception as e:
            print(f"Error calling Mistral API (Attempt {attempt+1}/3): {e}")
            time.sleep(5) # Brief wait for network blips
    return None

def main():
    client = setup_mistral()
    
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
        
        # Use simple directory name
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
            latex_code = generate_latex_with_mistral(client, raw_text)
            
            if latex_code:
                output_tex_path = os.path.join(project_dir, "main.tex")
                with open(output_tex_path, "w", encoding="utf-8") as f:
                    f.write(latex_code)
                print(f"SUCCESS: Saved project to {project_dir}")
                print(f" - Images extracted: {len(os.listdir(images_dir)) - 1}")
                
                # 3. Create Zip file
                shutil.make_archive(project_dir, 'zip', project_dir)
                print(f"SUCCESS: Created zip file for Overleaf: {project_dir}.zip")
            else:
                print("FAILED: Mistral did not return valid LaTeX.")
                
        except Exception as e:
            print(f"CRITICAL ERROR processing {pdf_file}: {e}")

if __name__ == "__main__":
    main()
