import fitz  # PyMuPDF
import os
import re

# -------------------- CONFIGURATION --------------------
INPUT_FOLDER = "./input_pdfs"
OUTPUT_FOLDER = "./output_tex"
# -------------------------------------------------------

def escape_latex(text):
    """Escapes characters that break LaTeX."""
    if not text: return ""
    replacements = {
        '&': r'\&', '%': r'\%', '$': r'\$', '#': r'\#', '_': r'\_',
        '{': r'\{', '}': r'\}', '~': r'\textasciitilde{}', '^': r'\textasciicircum{}',
        '\\': r'\textbackslash{}'
    }
    return "".join(replacements.get(c, c) for c in text)

def clean_header(text):
    """
    Removes the 'I.' or 'II.' from the start of a header string 
    so LaTeX can handle the numbering automatically.
    """
    # Matches "I. INTRODUCTION" -> returns "INTRODUCTION"
    match = re.match(r'^[IVX]+\.\s*(.*)', text)
    if match:
        return match.group(1)
    return text

def analyze_pdf_structure(pdf_path):
    """
    Parses PDF to find Title (largest), Abstract, and Roman-Numeral Sections.
    """
    doc = fitz.open(pdf_path)
    blocks = []
    
    # 1. Extract all text blocks with font sizes
    for page in doc:
        page_dict = page.get_text("dict")
        for block in page_dict["blocks"]:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"].strip()
                        if len(text) > 1:
                            blocks.append({
                                "text": text,
                                "size": span["size"],
                                "font": span["font"]
                            })

    if not blocks:
        return None

    # 2. Heuristics setup
    sizes = [b["size"] for b in blocks]
    if not sizes: return None
    
    body_size = max(set(sizes), key=sizes.count) # Most common size = body
    title_candidates = sorted([b for b in blocks if b["size"] > body_size * 1.2], key=lambda x: x["size"], reverse=True)
    
    structured_data = {
        "title": "",
        "abstract": [],
        "body": [],
        "references": []
    }

    # 3. Detect Title (Largest text block)
    if title_candidates:
        structured_data["title"] = escape_latex(title_candidates[0]["text"])
        # Remove title from processing list to avoid duplication
        blocks.remove(title_candidates[0])

    # 4. Process the rest
    current_section = "preamble" # preamble -> abstract -> body -> references
    
    # Regex for IEEE Headers: "I. INTRODUCTION", "IV. EXPERIMENTS"
    section_regex = re.compile(r'^[IVX]+\.\s+[A-Z\s]+$')
    
    for block in blocks:
        text = block["text"]
        size = block["size"]
        clean_txt = escape_latex(text)
        
        # --- Transition Detectors ---
        
        # Abstract Detection
        if current_section == "preamble" and ("Abstract" in text or "ABSTRACT" in text):
            current_section = "abstract"
            # Remove the word "Abstract-" if it's attached
            text_content = re.sub(r'^Abstract\s*[-–—]?\s*', '', clean_txt, flags=re.IGNORECASE)
            structured_data["abstract"].append(text_content)
            continue

        # Reference Detection
        if "REFERENCES" in text.upper() and size > body_size:
            current_section = "references"
            continue

        # Section Header Detection (Roman Numerals)
        # Check if it matches "I. SOMETHING" or is just Bold/Large uppercase
        is_roman_header = section_regex.match(text)
        is_style_header = (size > body_size) and (text.isupper()) and (len(text) < 60)
        
        if (is_roman_header or is_style_header) and current_section != "references":
            current_section = "body"
            header_title = clean_header(clean_txt) # Remove "I." let LaTeX do it
            structured_data["body"].append(f"\n\\section{{{header_title}}}\n")
            continue

        # --- Content Allocation ---
        
        if current_section == "abstract":
            structured_data["abstract"].append(clean_txt)
        
        elif current_section == "body":
            structured_data["body"].append(clean_txt + " ")
            
        elif current_section == "references":
            # Heuristic for IEEE refs like "[1] Author..."
            if re.match(r'\[\d+\]', text):
                structured_data["references"].append(f"\n\\bibitem{{ref}} {clean_txt}")
            else:
                structured_data["references"].append(clean_txt)

    return {
        "title": structured_data["title"] if structured_data["title"] else "Unknown Title",
        "abstract": " ".join(structured_data["abstract"]),
        "body": "".join(structured_data["body"]),
        "references": "".join(structured_data["references"])
    }

def create_tex_file(data, filename):
    # This template is tweaked to match the Roman Numeral style of Paper6
    template = r"""
\documentclass[10pt,twocolumn]{article}

% -------------------- IEEE-Like Styling --------------------
\usepackage[margin=1.6cm]{geometry}
\setlength{\columnsep}{20pt}
\usepackage{times} % Use Times font like standard IEEE
\usepackage[T1]{fontenc}
\usepackage{graphicx}
\usepackage{amsmath,amssymb}
\usepackage{cite}
\usepackage{titlesec}
\usepackage{authblk}

% Section formatting: Roman Numerals (I, II, III)
\renewcommand{\thesection}{\Roman{section}} 
\titleformat{\section}{\normalfont\bfseries\large\centering}{\thesection.}{0.5em}{}
\titlespacing*{\section}{0pt}{12pt}{6pt}

\title{\vspace{-10pt}\huge\bfseries VAR_TITLE \vspace{-6pt}}
\author{\textit{Converted Author Placeholder}} 
\date{}

\begin{document}

\twocolumn[
  \maketitle
  \begin{center}
    \vspace{-6pt}
    \begin{minipage}{0.9\textwidth}
      \textbf{\textit{Abstract}---} VAR_ABSTRACT
    \end{minipage}
    \vspace{12pt}
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
        print(f"Created '{INPUT_FOLDER}'. Place PDFs here.")
        return

    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)

    files = [f for f in os.listdir(INPUT_FOLDER) if f.lower().endswith(".pdf")]
    
    print(f"Found {len(files)} PDFs. converting to IEEE format...")

    for pdf_file in files:
        try:
            input_path = os.path.join(INPUT_FOLDER, pdf_file)
            output_filename = os.path.splitext(pdf_file)[0] + ".tex"
            output_path = os.path.join(OUTPUT_FOLDER, output_filename)
            
            print(f"Processing {pdf_file}...")
            data = analyze_pdf_structure(input_path)
            
            if data:
                create_tex_file(data, output_path)
                print(f" -> Success! Saved to {output_path}")
            else:
                print(f" -> Skipped (Empty/Unreadable)")
        except Exception as e:
            print(f" -> Error: {e}")

if __name__ == "__main__":
    main()