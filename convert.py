import pypandoc
import os

def latex_to_pdf(latex_code, output_filename="output.pdf", out_dir="out"):
    latex_code = latex_code.replace("```latex", "")
    # Ensure out/ exists
    os.makedirs(out_dir, exist_ok=True)

    # Paths
    base_name = "temp"
    tex_path = os.path.join(out_dir, base_name + ".tex")
    pdf_path = os.path.join(out_dir, base_name + ".pdf")
    final_pdf_path = os.path.join(out_dir, output_filename)

    # Write LaTeX code to temp.tex inside out/
    with open(tex_path, "w") as f:
        f.write(latex_code)

    pdf_path = "out/output.pdf"
    pypandoc.convert_file(tex_path, "pdf", outputfile=pdf_path, extra_args=["--standalone"])

    print(f"PDF saved at: {pdf_path}")


def download_md(md_text, output_filename="output.md", out_dir="out"):

    with open(os.path.join(out_dir, "README.md"), "w", encoding="utf-8") as f:
        f.write(md_text)
