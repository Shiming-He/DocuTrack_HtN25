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
        temperature=0.3,
    )

    print(response.message.content[0].text)


# Example sequence of keystrokes (you can change this to test)
actions = [
    "Open browser",
    "Move cursor to email field",
    "Type: sampleemail@gmail.com",
    
    "Press ENTER",
    "Type: samplepassword123",
    "Move cursor to login button",
    "Left Click",
    "Press Ctrl+C",
    "Press Ctrl+V"
]

# Join into a single string
action_sequence = ", ".join(actions)

# Ask Cohere to output latex documentation
message = f"""
Fill in this LaTeX template explaining the following actions performed in professional documentation format: {action_sequence}

Here are some specific custom requests for the document
- Make sure to only output the latex docuemntation with nothing else.
- For Instructions section, use the enumerate environment to make an ordered list for each action.
- Do not just simply list the actions, provide concise explanation/interpretation for what each step means.
- Conclusion should be only about the instructions, not this program. 

TEMPLATE:
\\documentclass[12pt]{{article}}
\\usepackage{{geometry}}
\\geometry{{margin=1in}}
\\title{{Automatic Documentation}}
\\author{{AI Assistant}}
\\date{{\\today}}

\\begin{{document}}
\\maketitle

\\section*{{Introduction}}
<write intro here>

\\section*{{Instructions}}
<write instructions here>

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
