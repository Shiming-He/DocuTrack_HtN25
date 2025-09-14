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
        self.API_KEY = API_KEY

        self.actions_system_message = {
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
- Focus only on this single set; do not reference other sets.
- Do not describe anything that has not changed from before and after the images (for example existing code, background applications, etc.)"""
            }


        self.inital_message = {
            "role" :"system", "content" : '''You have received a series of detailed explanations describing user actions from multiple sets of screenshots and prior input. Your task is to generate a full LaTeX document documenting all sets in chronological order, based on these explanations.

Instructions:
- Use the explanations as the authoritative source for each set.
- Maintain chronological order of the sets.
- Clearly label each set in the document (e.g., "Set 1", "Set 2", etc.).
- Include all relevant details about cursor movements, selections, text input, scrolls, menu/dialog interactions, and inferred user actions.
- Ensure the generated document is well-structured, clear, and concise.
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
        #print(json.dumps([inital_message]))
        # db_cursor.execute("INSERT INTO agent_messages (messages) VALUES (?)", (json.dumps(inital_message),))

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
    

    # def get_single_messages


    def add_keystroke_action_set(self, action, action_num):

        if action_num > 0:
            #print('hi')
            # add the set of messages that correspond to the actions that occured
#             system_message = {
#                 "role" : "system",
#                 "content" : """You are given a single set of user actions, consisting of two screenshots taken about 0.5 seconds apart and a record of recent mouse clicks and keyboard input. The first screenshot is the earliest, the second is the latest.

# Your role: Analyze this set to produce a detailed and structured explanation of what occurred, including all relevant context, so it can be used later to generate a LaTeX document. The explanation should be clear, concise, and complete enough for someone else to understand the sequence of user actions and their effects.

# Instructions:
# - Compare earliest and latest screenshots carefully to identify changes.
# - Include all relevant observations:
#   - Cursor movements: starting/ending positions, icon changes
#   - Active window/tab changes
#   - Text changes: per-character typing, block insertion, paste, or autocomplete
#   - Selections or dragged items
#   - Scrolling or content shifts
#   - Menus, dialogs, tooltips, or hover states
#   - Prior mouse or keyboard input that likely caused the changes
# - Include your inference of the most likely user action(s) and any timing/plausibility notes.
# - Present the explanation as a concise paragraph or structured sentences (3–6 sentences recommended).
# - Do not generate LaTeX at this stage.
# - Focus only on this single set; do not reference other sets."""
#             }
            
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
            
            # co_client = cohere.ClientV2(self.API_KEY)

            # response = co_client.chat(
            #     messages=[self.actions_system_message, single_set_messgae],
            #     #model="command",
            #     model=self.model,
            #     temperature=0.8
            # )


            # self.save_message({"role": "user", "content" : response.message.content[0].text})
            self.save_message(single_set_messgae)
            # print(len(self.list_of_messages))

    def get_context(self):
        return_message = []
        for message in self.get_messages():
            co_client = cohere.ClientV2(self.API_KEY)

            response = co_client.chat(
                messages=[self.actions_system_message, message],
                #model="command",
                model=self.model,
                temperature=0.5
            )
            return_message.append({"role": "user", "content" : response.message.content[0].text})
        return return_message


    def return_final_LATEX(self, difficulty = "intermediate"):


        # run the context generation cohere model
        single_context_message = self.get_context()



        message = {"role" : "user", "content" : f"""
        Now fill in this LaTeX template based on the sets that you have recieved from the user. This is documentation based on what the user completed:

        The following parameter is the difficulty. You should structure the documentation based on how knowledgable the intended reader is. 
        For example beginner will be descriptive, and cover more trivial concepts, and hard will be more concise and short, while intermediate will be between the two:{difficulty}

        Here are some specific custom requests for the document
        - Make sure to only output the latex docuemntation with nothing else.
        - For Instructions section, use the enumerate environment to make an ordered list for each action.
        - You can provide useful images if needed for a clearer explanation
        - Do not just simply list the actions, provide concise explanation/interpretation for what each step means.
        - Conclusion should be only about the instructions, not this program. 
        - Write as if informing the reader (2nd person)
        - Do not state mouse coordinates, just describe the item the mouse is interacting with if needed

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
        <write instructions here>

        \\section*{{Conclusion}}
        <write conclusion here>

        \\end{{document}}

        """}

        # self.save_message(message)

        # print(len(self.list_of_messages))

        # Call Cohere chat
        # print(self.get_messages())
        # co_client = cohere.ClientV2(API_KEY)
        response = self.co_client.chat(
            messages=[self.inital_message] + single_context_message + [message],
            #model="command",
            model=self.model,
            temperature=0.3
        )

        response.text = validate_latex(response.message.content[0].text)

        # Print the explanation
        print(response.text)
        return response.text

    def return_final_MD(self, difficulty = "intermediate"):
        message = {"role" : "user", "content" : f"""
        You are an AI assistant that generates concise, professional, and well-formatted README.md documentation.


        The following parameter is the difficulty. You should structure the documentation based on how knowledgable the intended reader is. 
        For example beginner will be descriptive, and cover more trivial concepts, and hard will be more concise and short, while intermediate will be between the two:{difficulty}

        Custom requests:
        - Write as if informing the reader (2nd person)
        - Do not state mouse coordinates, just describe the item the mouse is interacting with if needed

        Write a README.md file in Markdown format that summarizes the steps. Follow this structure:

        # Project Overview
        A short description of what the actions accomplish.

        # Requirements
        List any tools, libraries, or prerequisites.

        # Steps Performed
        Summarize the actions into numbered steps.
        If any step references a screenshot or image, include it using Markdown image syntax:
        `![Description](filename.png)`
        Use interpreted instructions here as well.

        # Notes
        Optional tips, troubleshooting, or clarifications.

        # Example Output
        (Optional) A short code snippet, command, or screenshot of final result.

        Formatting Rules:
        - Always use Markdown headers.
        - Use bullet points (-) for unordered lists and 1., 2., 3. for ordered steps.
        - Insert images where appropriate using relative paths like `images/step1.png`.
        - Keep explanations short and professional.
        - Make sure to only output the md. 

        Now, generate the README.md. 
        """}

        # Call Cohere chat
        response = self.co.chat(
            message=message,
            #model="command",
            model="c4ai-aya-vision-8b",
            temperature=0.3
        ) 

        # Print the explanation
        print(response.text)
        return response.text