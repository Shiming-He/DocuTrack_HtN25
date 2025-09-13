import cohere
import base64

# Initialize Cohere client
co = cohere.Client("g7RUPaPLEX9HWzrORaU1PJkTZHSVRx0Uu8eOVLPY")

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
        caption = generate_text(action["path"], "Concisely describe the mouse/keyboard action performed in this image as if it is part of a tutorial.")
        processed_actions.append(f"{caption}\n\\includegraphics[width=0.9\\textwidth]{{{action['path']}}}")

instructions_latex = "\\begin{enumerate}\n"
for step in processed_actions:
    instructions_latex += f"  \\item {step}\n"
instructions_latex += "\\end{enumerate}"

# Ask Cohere to output latex documentation
message = f"""
Fill in this LaTeX template using the provided instructions.

Instructions (already ordered and processed):{instructions_latex}

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
{instructions_latex}

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
