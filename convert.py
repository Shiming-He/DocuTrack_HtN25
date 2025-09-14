import subprocess
import os

def latex_to_pdf(latex_code, output_filename="output.pdf", out_dir="out"):
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

    # Run pdflatex with out_dir as working directory
    try:
        subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", base_name + ".tex"],
            check=True,
            cwd=out_dir,  # run inside out/
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
    except subprocess.CalledProcessError as e:
        print("Error compiling LaTeX:", e.stderr.decode())
        return None

    # Rename/move result
    # aaaa
    
    if os.path.exists(pdf_path):
        os.rename(pdf_path, final_pdf_path)

        # Cleanup auxiliary files
        for ext in [".aux", ".log", ".tex"]:
            aux_file = os.path.join(out_dir, base_name + ext)
            if os.path.exists(aux_file):
                os.remove(aux_file)

        return final_pdf_path

    return None