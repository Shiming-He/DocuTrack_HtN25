import cohere
import base64



def validate_latex(latex_code: str) -> str:
    '''check if the latex has a begining and end'''
    if "\\begin{document}" not in latex_code:
        latex_code = "\\begin{document}\n" + latex_code
    if "\\end{document}" not in latex_code:
        latex_code += "\n\\end{document}"
    return latex_code

def convert_image_to_base64(image_path):
    '''converts the image to something cohere can take'''
    with open(image_path, "rb") as img_file:
        base64_image = f"data:image/jpeg;base64,{base64.b64encode(img_file.read()).decode('utf-8')}"
    return base64_image


class CohereAgent:
    
    def __init__(self, API_KEY, model = "c4ai-aya-vision-8b"):
        # init cohere client
        self.co_client = cohere.ClientV2(API_KEY)
        self.list_of_messages = [
            {"role": "system", "content": '''You are given one or more sets of user actions, each consisting of two screenshots taken about 0.5 seconds apart and a record of recent mouse clicks and keyboard input. Each set is presented in chronological order, earliest screenshot first, latest screenshot second.

Your role: You are tasked with writing documentation for your team. Use the recorded user actions to generate clear and concise documentation, but do not produce any output until explicitly asked to generate a LaTeX document.

Task: Process each set sequentially, recording and interpreting all visual and input changes internally for later inclusion in LaTeX documentation. Do not produce output sentences or LaTeX for individual sets at this stage.

Step 1 – Earliest screenshot:
Record internally only observable facts: cursor position/icon, active window/app, highlighted/focused UI, caret presence/location, scrollbar position/content, visible text or terminal output, open menus/dialogs/tooltips. Do not infer actions yet.

Step 2 – Latest screenshot:
Compare to the first. Record differences and plausible causes for quick actions (clicks, gestures, keyboard shortcuts, scrolls). Consider prior input for that set: did any recent click or keystroke plausibly trigger the change? Observe and store:
- Cursor movement: direction/target, icon changes
- Active window/tab changes, proximity of cursor
- New highlights, tabs, windows, dialogs
- Text changes: per-character, whole-block, paste/autocomplete
- Selection changes, dragged items
- Scrollbar/content shift without cursor movement
- Context menus, tooltips, delayed UI
- If no cursor visible, note “no cursor movement visible” and allow touch/gesture

Checklist (in order): movement, icon, active window, new text, new tab, content shift, menu/tooltip, drag, no cursor, delayed UI, prior mouse/keyboard input.

Timing rules: favor quick actions unless evidence shows drag/multi-step; instant text = paste/autocomplete; new tab without content switch = background tab.

Processing rules:
- Maintain chronological order of sets.
- Do not produce any immediate output per set.
- Store all observed facts, inferred actions, and causal links internally.
- Later, when prompted, generate a full LaTeX document documenting all sets and actions based on this internal analysis.
'''}
            ] # add the system preset
        self.model = model

    def add_keystroke_action_set(self, action, action_num):

        if action_num > 0:
            # add the set of messages that correspond to the actions that occured
            self.list_of_messages += [
                {"role": "user", 
                    "content": [
                        {"type": "text", "text": f"SET {action_num}:"},
                        {"type": "text", "text": "- Earliest Screenshot: "},
                        {
                            "type": "image_url",
                            "image_url": {"url": convert_image_to_base64(action[2])},
                        },
                        {"type": "text", "text": "- Latest Screenshot: "},
                        {
                            "type": "image_url",
                            "image_url": {"url": convert_image_to_base64(action[3])},
                        },
                        {
                            "type": "text", "text": f"- Recent Input: {action[0]} and {action[1]}"
                        }
                    ],
                }
            ]


    def return_final_LATEX(self):
        message = """
        Now fill in this LaTeX template with the sets that you have recieved:

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

        self.list_of_messages.append(message)




        # Call Cohere chat
        response = self.co_client.chat(
            message=self.list_of_messages,
            #model="command",
            model=self.model,
            temperature=0.25
        )

        response.text = validate_latex(response.text)

        # Print the explanation
        print(response.text)



