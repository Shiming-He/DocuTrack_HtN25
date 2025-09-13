import cohere
import base64
import json
import sqlite3



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
    
    def __init__(self, API_KEY, model = "c4ai-aya-vision-32b"):
        # init cohere client
        self.co_client = cohere.ClientV2(API_KEY)
        self.model = model
        inital_message = {
            "role" :"system", "content" : '''You have received a series of detailed explanations describing user actions from multiple sets of screenshots and prior input. Your task is to generate a full LaTeX document documenting all sets in chronological order, based on these explanations.

Instructions:
- Use the explanations as the authoritative source for each set.
- Maintain chronological order of the sets.
- Clearly label each set in the document (e.g., "Set 1", "Set 2", etc.).
- Include all relevant details about cursor movements, selections, text input, scrolls, menu/dialog interactions, and inferred user actions.
- Ensure the LaTeX document is well-structured, clear, and concise.
- Include sections, enumerated lists, or subsections for readability.
- Format code blocks, terminal output, or text input using appropriate LaTeX environments (e.g., verbatim or lstlisting) if mentioned in the explanations.
- Avoid adding information not present in the explanations.
- Produce the complete LaTeX output in one response.
- Do not reference screenshots directly; rely entirely on the provided explanations.
'''
         } # add the system preset
        

        # message save json file
        db_conn = sqlite3.connect("message_database.db")
        db_cursor = db_conn.cursor()
        # create a table
        db_cursor.execute("DROP TABLE IF EXISTS agent_messages")
        db_cursor.execute("""
        CREATE TABLE agent_messages (
                               id INTEGER PRIMARY KEY,
                               messages TEXT NOT NULL
                               
                               )
                               """)
        # add some data in 
        print(json.dumps([inital_message]))
        db_cursor.execute("INSERT INTO agent_messages (messages) VALUES (?)", (json.dumps(inital_message),))

        db_conn.commit()
        db_conn.close()
    

    def save_message(self, message):

        # get all of the new stuff in db
        db_conn = sqlite3.connect("message_database.db")
        db_cursor = db_conn.cursor()
        
        db_cursor.execute("INSERT INTO agent_messages (messages) VALUES (?)", (json.dumps(message),))
        db_conn.commit()
        db_conn.close()

    def get_messages(self):
        db_conn = sqlite3.connect("message_database.db")
        db_cursor = db_conn.cursor()
        db_cursor.execute("SELECT messages FROM agent_messages")
        return_val = [json.loads(row[0]) for row in db_cursor.fetchall()]
        
        db_conn.close()
        return return_val


    def add_keystroke_action_set(self, action, action_num):

        if action_num > 0:
            print('hi')
            # add the set of messages that correspond to the actions that occured
            system_message = {
                "role" : "system",
                "content" : """You are given a single set of user actions, consisting of two screenshots taken about 0.5 seconds apart and a record of recent mouse clicks and keyboard input. The first screenshot is the earliest, the second is the latest.

Your role: Analyze this set to produce a detailed and structured explanation of what occurred, including all relevant context, so it can be used later to generate a LaTeX document. The explanation should be clear, concise, and complete enough for someone else to understand the sequence of user actions and their effects.

Instructions:
- Compare earliest and latest screenshots carefully to identify changes.
- Include all relevant observations:
  - Cursor movements: starting/ending positions, icon changes
  - Active window/tab changes
  - Text changes: per-character typing, block insertion, paste, or autocomplete
  - Selections or dragged items
  - Scrolling or content shifts
  - Menus, dialogs, tooltips, or hover states
  - Prior mouse or keyboard input that likely caused the changes
- Include your inference of the most likely user action(s) and any timing/plausibility notes.
- Present the explanation as a concise paragraph or structured sentences (3–6 sentences recommended).
- Do not generate LaTeX at this stage.
- Focus only on this single set; do not reference other sets."""
            }
            
            single_set_messgae = {"role" : "user", "content" :
                     [
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
                    ]
                }
            

            response = self.co_client.chat(
                messages=[system_message, single_set_messgae],
                #model="command",
                model=self.model,
                temperature=0.2
            )


            self.save_message(response)
            # print(len(self.list_of_messages))


    def return_final_LATEX(self):
        message = {"role" : "user", "content" : """
        Now fill in this LaTeX template based on the sets that you have recieved from the user. This is documentation based on what the user completed:

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

        """}

        self.save_message(message)

        # print(len(self.list_of_messages))




        # Call Cohere chat
        # print(self.get_messages())
        response = self.co_client.chat(
            messages=self.get_messages(),
            #model="command",
            model=self.model,
            temperature=0.25
        )

        response.text = validate_latex(response.message.content[0].text)

        # Print the explanation
        print(response.text)



