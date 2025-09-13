import cohere
import base64
import os
import shutil
import aspose.pdf as ap

# Initialize Cohere client
co = cohere.Client("g7RUPaPLEX9HWzrORaU1PJkTZHSVRx0Uu8eOVLPY")
options = ap.TeXLoadOptions()

OUTPUT_DIR = "doc_output"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def validate_latex(latex_code: str) -> str:
    if "\\begin{document}" not in latex_code:
        latex_code = "\\begin{document}\n" + latex_code
    if "\\end{document}" not in latex_code:
        latex_code += "\n\\end{document}"
    return latex_code

def generate_text(image_path, message):
    model = "c4ai-aya-vision-8b"
    co = cohere.ClientV2("g7RUPaPLEX9HWzrORaU1PJkTZHSVRx0Uu8eOVLPY")

    with open(image_path, "rb") as img_file:
        base64_image_url = f"data:image/jpeg;base64,{base64.b64encode(img_file.read()).decode('utf-8')}"

    response = co.chat(
        model=model,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": message},
                    {
                        "type": "image_url",
                        "image_url": {"url": base64_image_url},
                    },
                ],
            }
        ],
        temperature=0.15,
    )
    return response.message.content[0].text.strip()

# Example sequence of keystrokes (you can change this to test)
actions = [
    {"type": "text", "content": "Open browser"},
    {"type": "image", "path": "actions.png"},
    {"type": "text", "content": "Type: sampleemail@gmail.com"},
    {"type": "text", "content": "Press ENTER"},
    {"type": "text", "content": "Type: samplepassword123"},
    {"type": "text", "content": "Press Ctrl+C"},
]

# Step 1: Process all actions into rich descriptions
processed_actions = []
for action in actions:
    if action["type"] == "text":
        processed_actions.append(action["content"])
    elif action["type"] == "image":
        filename = os.path.basename(action["path"])
        out_path = os.path.join(OUTPUT_DIR, filename)
        shutil.copy(action["path"], out_path)   # copy image to output folder
        
        caption = generate_text(action["path"], "Concisely describe the mouse/keyboard action performed in this image as if it is part of a tutorial.")
        processed_actions.append(f"{caption}\n\\includegraphics[width=0.9\\textwidth]{{{action['path']}}}")

instructions = "\\begin{enumerate}\n"
for step in processed_actions:
    instructions += f"  \\item {step}\n"
instructions += "\\end{enumerate}"

doctype = "md"

if(doctype == "Latex"):
    # Ask Cohere to output latex documentation
    message = f"""
    Fill in this LaTeX template using the provided instructions.

    Instructions (already ordered and processed):{instructions}

    Here are some specific custom requests for the document
    - Make sure to only output the latex docuemntation with nothing else.
    - For Instructions section, use the enumerate environment to make an ordered list for each action.
    - Do not just simply list the actions, provide concise explanation/interpretation for what each step means.
    - Conclusion should be only about the instructions, not this program. 

    TEMPLATE:
    \\documentclass[12pt]{{article}}
    \\usepackage{{geometry}}
    \\usepackage{{graphicx}}
    \\geometry{{margin=1in}}


    \\title{{Automatic Documentation}}
    \\author{{AI Assistant}}
    \\date{{\\today}}

    \\begin{{document}}
    \\maketitle

    \\section*{{Introduction}}
    <write intro here>

    \\section*{{Instructions}}
    {instructions}

    \\section*{{Conclusion}}
    <write conclusion here>

    \\end{{document}}

    """

    # Call Cohere chat
    response = co.chat(
        message=message,
        #model="command",
        model="c4ai-aya-vision-8b",
        temperature=0.25
    )

    response.text = validate_latex(response.text)

    # Print the explanation
    print(response.text)

    tex_path = os.path.join(OUTPUT_DIR, "output.tex")
    with open(tex_path, "w", encoding="utf-8") as f:
        f.write(response.text)

    # Create a Document class object
    document = ap.Document(tex_path , options)

    # Convert Latex to PDF
    document.save("tex-to-pdf.pdf")

elif(doctype == "md"):

# Ask Cohere to output latex documentation
    message = f"""
        You are an AI assistant that generates concise, professional, and well-formatted README.md documentation.

        Given the following action information:{instructions}

        Write a README.md file in Markdown format that summarizes the steps. Follow this structure:

        # Project Overview
        A short description of what the actions accomplish. Explain the purpose in 2–4 sentences.

        # Requirements
        List any tools, libraries, or prerequisites the user needs to reproduce the actions. Use bullet points.

        # Steps Performed
        Summarize the recorded user actions into clear, sequential steps. Use a numbered list. Each step should be 1–2 sentences maximum, written in simple, professional language.

        # Notes
        Optional remarks, tips, or troubleshooting points (if relevant).

        # Example Output
        (Optional) Provide a small code snippet, command, or screenshot description that represents the final result.

        Formatting Rules:
        - Always use Markdown headers (#, ##).
        - Use bullet points (-) for lists and numbered lists (1., 2., 3.) for ordered steps.
        - Keep explanations clear and concise.
        - Do not include raw action logs — only polished descriptions.
        - Make sure to only output the md. 

        Now, generate the README.md. 
    """

    # Call Cohere chat
    response = co.chat(
        message=message,
        #model="command",
        model="c4ai-aya-vision-8b",
        temperature=0.25
    ) 

    # Print the explanation
    print(response.text)

    with open(os.path.join(OUTPUT_DIR, "README.md"), "w", encoding="utf-8") as f:
        f.write(response.text)
