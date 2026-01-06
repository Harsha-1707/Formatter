import fitz  # PyMuPDF
import os
import re

# -------------------- CONFIGURATION --------------------
INPUT_FOLDER = "./input_pdfs"   # Folder containing your PDFs
OUTPUT_FOLDER = "./output_tex"  # Folder where .tex files will be saved
# -------------------------------------------------------

def escape_latex(text):
    """Escapes characters that break LaTeX."""
    if not text: return ""
    replacements = {
        '&': r'\&', '%': r'\%', '$': r'\$', '#': r'\#', '_': r'\_',
        '{': r'\{', '}': r'\}', '~': r'\textasciitilde{}', '^': r'\textasciicircum{}',
        '\\': r'\textbackslash{}'
    }
    # Naive replacement; for robust handling, regex is better but this suffices for plain text
    return "".join(replacements.get(c, c) for c in text)

def analyze_pdf_structure(pdf_path):
    """
    Parses a PDF and attempts to identify structure based on font size.
    Returns a dictionary with title, abstract, and body sections.
    """
    doc = fitz.open(pdf_path)
    
    # Store all text blocks with their font sizes
    blocks = []
    
    for page in doc:
        # get_text("dict") returns detailed layout info including font sizes
        page_dict = page.get_text("dict")
        for block in page_dict["blocks"]:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"].strip()
                        if len(text) > 1: # Ignore tiny artifacts
                            blocks.append({
                                "text": text,
                                "size": span["size"],
                                "font": span["font"] # flags can detect bold
                            })

    if not blocks:
        return None

    # HEURISTICS
    # 1. Find the most common font size -> This is likely Body Text
    sizes = [b["size"] for b in blocks]
    body_size = max(set(sizes), key=sizes.count)
    
    # 2. Find the largest font size -> This is likely the Title
    max_size = max(sizes)
    
    structured_data = {
        "title": [],
        "abstract": [],
        "body": [],
        "references": []
    }
    
    # State machine to track where we are
    current_section = "preamble" # preamble, abstract, body, references
    
    for block in blocks:
        text = block["text"]
        size = block["size"]
        
        # --- Title Detection ---
        if size == max_size and current_section == "preamble":
            structured_data["title"].append(text)
            continue
            
        # --- Abstract Detection ---
        if "Abstract" in text and len(text) < 20:
            current_section = "abstract"
            continue
        
        # --- Reference Detection ---
        if "References" in text and size > body_size:
            current_section = "references"
            continue
            
        # --- Section Header Detection (Simple Heuristic) ---
        # If text is larger than body but smaller than title, OR is bold
        # And it looks like a header (short, maybe numbered)
        is_header = (size > body_size) or (size == body_size and text.isupper() and len(text) < 50)
        
        if is_header and current_section != "references":
            current_section = "body"
            # Mark this as a section in the body list
            structured_data["body"].append(f"\n\\section{{{escape_latex(text)}}}\n")
            continue

        # --- Content Allocation ---
        clean_text = escape_latex(text)
        
        if current_section == "preamble":
            # Stuff before abstract but not title is usually authors/affil
            # We skip adding it to body, maybe store for authors if needed
            pass 
        elif current_section == "abstract":
            structured_data["abstract"].append(clean_text)
        elif current_section == "body":
            structured_data["body"].append(clean_text + " ")
        elif current_section == "references":
            # Try to format references as items
            if re.match(r'\[\d+\]', text) or re.match(r'\d+\.', text):
                structured_data["references"].append(f"\n\\bibitem{{ref}} {clean_text}")
            else:
                structured_data["references"].append(clean_text)

    # Join lists into strings
    return {
        "title": " ".join(structured_data["title"]) if structured_data["title"] else "Unknown Title",
        "abstract": " ".join(structured_data["abstract"]),
        "body": "".join(structured_data["body"]),
        "references": "".join(structured_data["references"])
    }

def create_tex_file(data, filename):
    template = r"""
\documentclass[10pt,twocolumn]{article}
\usepackage[margin=1.6cm]{geometry}
\setlength{\columnsep}{22pt}
\usepackage{microtype}
\usepackage[T1]{fontenc}
\usepackage{lmodern}
\usepackage{graphicx}
\usepackage{amsmath,amssymb}
\usepackage{cite}
\usepackage{titlesec}
\usepackage{authblk}

% Section formatting
\titleformat{\section}{\normalfont\bfseries\large}{\thesection.}{0.5em}{}
\titlespacing*{\section}{0pt}{10pt}{6pt}

\title{\vspace{-8pt}VAR_TITLE\vspace{-6pt}}
\author{Converted from PDF}
\affil{Automated Extraction}
\date{}

\begin{document}

\twocolumn[
  \maketitle
  \begin{center}
    \vspace{-6pt}
    \begin{minipage}{0.9\textwidth}
      \begin{abstract}
        VAR_ABSTRACT
      \end{abstract}
    \end{minipage}
    \vspace{8pt}
  \end{center}
]

% -------------------- Main Content --------------------
VAR_BODY

% -------------------- References --------------------
\begin{thebibliography}{99}
VAR_REFERENCES
\end{thebibliography}

\end{document}
"""
    content = template.replace("VAR_TITLE", data['title'])
    content = content.replace("VAR_ABSTRACT", data['abstract'])
    content = content.replace("VAR_BODY", data['body'])
    content = content.replace("VAR_REFERENCES", data['references'])
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)

def main():
    if not os.path.exists(INPUT_FOLDER):
        os.makedirs(INPUT_FOLDER)
        print(f"Created '{INPUT_FOLDER}'. Please put your PDFs there and run again.")
        return

    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)

    files = [f for f in os.listdir(INPUT_FOLDER) if f.lower().endswith(".pdf")]
    
    if not files:
        print(f"No PDFs found in {INPUT_FOLDER}")
        return

    print(f"Found {len(files)} PDFs. Starting conversion...")

    for pdf_file in files:
        input_path = os.path.join(INPUT_FOLDER, pdf_file)
        output_filename = os.path.splitext(pdf_file)[0] + ".tex"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)
        
        try:
            print(f"Processing {pdf_file}...")
            data = analyze_pdf_structure(input_path)
            if data:
                create_tex_file(data, output_path)
                print(f" -> Saved to {output_path}")
            else:
                print(f" -> Failed to extract text from {pdf_file}")
        except Exception as e:
            print(f" -> Error processing {pdf_file}: {e}")

    print("\nBatch conversion complete!")

if __name__ == "__main__":
    main()