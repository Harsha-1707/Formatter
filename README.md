# 📄 PDF to LaTeX Converter

<div align="center">

![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-active-success.svg)
![Contributions Welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg)

**A powerful toolkit to convert PDF research papers into IEEE-formatted LaTeX documents using AI**

[Features](#-features) • [Installation](#-installation) • [Usage](#-usage) • [Examples](#-examples) • [Contributing](#-contributing)

</div>

---

## 🌟 Features

### 🤖 **Multiple AI Engines**

- **Gemini AI Converter**: Leverages Google's Gemini 2.0 Flash for intelligent document conversion
- **Mistral AI Converter**: Uses Mistral Large for high-quality LaTeX generation
- **Local Parser**: Traditional rule-based conversion without AI dependencies

### 📋 **Smart Document Processing**

- ✅ **Automatic Structure Detection**: Identifies titles, abstracts, sections, and references
- ✅ **Image Extraction & Placement**: Preserves images with proper LaTeX figure environments
- ✅ **Citation Management**: Smart citation detection and linking to bibliography
- ✅ **IEEE Format Compliance**: Generates professional IEEE conference-style documents
- ✅ **Unicode Handling**: Robust sanitization to prevent LaTeX compilation errors

### 🎯 **Output Quality**

- Two-column IEEE format layout
- Proper section hierarchy (`\section`, `\subsection`)
- Automated bibliography generation
- Ready-to-upload Overleaf ZIP packages
- Preserved document structure and content fidelity

---

## 🚀 Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Setup

1. **Clone the repository**

   ```bash
   git clone https://github.com/Harsha-1707/Formatter.git
   cd Formatter
   ```

2. **Create a virtual environment** (recommended)

   ```bash
   python -m venv env

   # Windows
   .\env\Scripts\activate

   # macOS/Linux
   source env/bin/activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure API Keys** (for AI converters)

   Edit the converter files with your API keys:

   - `gemini_converter.py` - Add your Google AI API key
   - `mistral_converter.py` - Add your Mistral API key

---

## 📖 Usage

### Method 1: Local Parser (No API Required)

Best for quick conversions without AI enhancement.

```bash
python app.py
```

**Features:**

- Font-size based structure detection
- Section header identification
- Basic reference parsing
- No API costs

### Method 2: Gemini AI Converter

Recommended for best quality and comprehensive document understanding.

```bash
python gemini_converter.py
```

**Advantages:**

- Deep content understanding
- Smart citation injection
- Better handling of complex layouts
- Automatic image captioning

### Method 3: Mistral AI Converter

Alternative AI engine with excellent LaTeX formatting.

```bash
python mistral_converter.py
```

**Advantages:**

- Verbatim content preservation
- Smart citation analysis
- Reliable bibliography validation
- Fast processing

### 📁 File Organization

```
Formatter/
├── input_pdfs/          # Place your PDF files here
├── output_tex/          # Generated LaTeX projects appear here
│   └── latex_project/
│       ├── main.tex     # Main LaTeX file
│       ├── image_*.png  # Extracted images
│       └── latex_project.zip  # Ready for Overleaf
├── app.py              # Local parser
├── gemini_converter.py # Gemini AI converter
└── mistral_converter.py # Mistral AI converter
```

---

## 💡 Examples

### Basic Workflow

1. **Add PDFs to input folder**

   ```bash
   # Copy your research papers to input_pdfs/
   cp my_paper.pdf input_pdfs/
   ```

2. **Run conversion**

   ```bash
   python gemini_converter.py
   ```

3. **Check output**

   ```
   Processing my_paper.pdf...
   Analyzing my_paper.pdf...
   Generating LaTeX with Gemini...
   SUCCESS: Saved project to ./output_tex/latex_project
   - Images extracted: 5
   SUCCESS: Created zip file: ./output_tex/latex_project.zip
   ```

4. **Upload to Overleaf**
   - Go to [Overleaf](https://www.overleaf.com)
   - New Project → Upload Project
   - Select `latex_project.zip`
   - Compile and edit!

### Sample Output Structure

The generated LaTeX includes:

```latex
\documentclass[conference]{IEEEtran}
\usepackage{graphicx}
\usepackage{cite}
\usepackage{hyperref}

\title{Your Paper Title}
\author{...}

\begin{document}
\maketitle

\begin{abstract}
Your abstract here...
\end{abstract}

\section{Introduction}
Content with citations \cite{ref1}...

\begin{figure}[htbp]
\includegraphics[width=\columnwidth]{image_p1_1.png}
\caption{Figure caption}
\end{figure}

\begin{thebibliography}{99}
\bibitem{ref1} First reference...
\end{thebibliography}

\end{document}
```

---

## 🛠️ Utilities

### Test ZIP Creation

```bash
python zip_test.py
```

Creates a test ZIP archive for verification.

### Check Models

```bash
python check_models.py
```

Verifies AI model availability and credentials.

---

## 📊 Comparison Matrix

| Feature            | Local Parser | Gemini AI | Mistral AI |
| ------------------ | ------------ | --------- | ---------- |
| Cost               | Free         | API costs | API costs  |
| Speed              | Fast         | Moderate  | Moderate   |
| Accuracy           | Good         | Excellent | Excellent  |
| Citation Detection | Basic        | Smart     | Smart      |
| Image Handling     | Yes          | Yes       | Yes        |
| Complex Layouts    | Limited      | Excellent | Excellent  |
| API Key Required   | ❌           | ✅        | ✅         |

---

## 🔧 Configuration

### Customizing Output Format

Edit the converter files to modify:

- Document class (article, IEEEtran, etc.)
- Page margins and column spacing
- Citation style
- Figure placement rules

### API Rate Limits

Both AI converters include retry logic:

- 3 automatic retries on failure
- 20-second delay for rate limits (Gemini)
- 5-second delay for network issues (Mistral)

---

## 🐛 Troubleshooting

### Common Issues

**Problem**: `ModuleNotFoundError: No module named 'fitz'`

```bash
Solution: pip install pymupdf
```

**Problem**: Unicode characters causing LaTeX errors

```
Solution: Already handled! Both AI converters sanitize unicode automatically.
```

**Problem**: Images not appearing in LaTeX

```
Solution: Ensure images are in the same directory as main.tex
```

**Problem**: API rate limit exceeded

```
Solution: Wait a few minutes or upgrade your API plan
```

---

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Commit your changes**
   ```bash
   git commit -m "Add amazing feature"
   ```
4. **Push to the branch**
   ```bash
   git push origin feature/amazing-feature
   ```
5. **Open a Pull Request**

### Development Ideas

- [ ] Support for more document formats (DOCX, HTML)
- [ ] GUI interface
- [ ] Batch processing optimization
- [ ] Custom LaTeX templates
- [ ] Table extraction and conversion
- [ ] Mathematical equation detection

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **PyMuPDF** - PDF processing library
- **Google Gemini AI** - Advanced document understanding
- **Mistral AI** - High-quality text generation
- **LaTeX Community** - For the amazing typesetting system

---

## 📮 Contact

**Harsha**  
GitHub: [@Harsha-1707](https://github.com/Harsha-1707)

---

<div align="center">

**Made with ❤️ for the research community**

⭐ Star this repo if you find it helpful!

</div>
