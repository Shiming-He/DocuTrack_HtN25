## 💡 Inspiration  
Many of us, whether for work or projects, are tasked with creating detailed documentation with text and screenshots for things like software setup. It takes a long time and slows down progress. We thought, what if an AI tool could watch us set it up, then build documentation with screenshots and text that is easy to follow, and can format it in LaTeX or Markdown?

---

## ⚙️ What it does  
DocuTrack watches your screen, keyboard, and mouse as you set up software, then uses Cohere to write clean step-by-step setup docs in seconds. It:  
- 🖥️ Captures screenshots every few seconds, with extra captures when keystrokes happen  
- ✍️ Uses Cohere to read screenshots from before, during, and after a keystroke to figure out what action was taken  
- 📄 Writes documentation with screenshots and explanations step by step, then outputs in LaTeX (main format), Markdown, or plain text  
- 🧠 Offers privacy controls like pause, redact fields, or ignore certain apps  

---
## 💻 Use Cases
- **Setting up a local dev environment**  
  Installing Node.js, VS Code extensions, and configuring environment variables

- **Onboarding new engineers**  
  Showing how to clone a repo, run tests, and deploy to staging

- **Documenting a robotics build**  
  Recording wiring steps, flashing firmware, and calibrating a new robot

- **Classroom lab instructions**  
  Guiding students through Python package installs and running their first scripts

- **Server setup guides**  
  Provisioning a Linux VM, setting up Nginx, and deploying a web app

and a lot more...
--
## 🛠️ How we built it  
We built a desktop recorder with a Tkinter GUI that lets you start and stop recording, similar to Cluey. While recording, it:  
- Takes screenshots every few seconds  
- Flags keystrokes as significant triggers for potential setup steps  
- Groups screenshots before, during, and after each keystroke  
- Sends these grouped screenshots to Cohere, which interprets what happened on screen and writes it as LaTeX with the related screenshot saved alongside  

When the user stops recording, the tool compiles all steps and exports a documentation file in LaTeX (main), Markdown, or plain text.  

We also built:  
- A backend to handle Cohere generation and export formatting  
- A VS Code extension that lets you record directly inside your editor  

---

## 🧩 Challenges we ran into  
- Deciding how often to capture screenshots without creating too much data  
- Getting Cohere to interpret grouped screenshots reliably  
- Making sure the generated steps were accurate and readable  

---

## 🏅 Accomplishments that we're proud of  
- Built a full pipeline from raw screen captures to polished LaTeX docs  
- Created an editor extension that works inside VS Code  
- Made the output look good enough to publish directly in GitHub repos  

---

## 📚 What we learned  
We learned how to:  
- Structure prompts for predictable AI output  
- Link screenshots and keystrokes into logical steps  
- Use embeddings for step deduplication and linking  
- Build privacy safe recorders that users can trust  

---

## 🚀 What's next for DocuTrack: Turn Screen Recordings Into Perfect Documentation  
We plan to:  
- Add team workspaces with shared cloud storage  
- Sync directly to GitHub, Confluence, and Notion  
- Build a browser extension for recording web based setup flows  
- Support real time doc previews while recording  

---

## 🏆 Awards & Tracks We Qualify For  
- **Warp:** Best Developer Tool – Tools that improve developer experience  
- **Y Combinator (Unicorn Prize):** Startup-potential projects  
- **Cohere:** Best Use of Cohere API – Multimodal AI apps (text, images, workflows)  
- **Cua:** Best Computer-Use Agent – Build an agent for desktop/browser control  
- **Graphite:** Engineering Dream Team – Showcase great engineering practices and teamwork  
