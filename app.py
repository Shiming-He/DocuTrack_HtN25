import tkinter as tk
from tkinter import ttk
import multiprocessing
import glob
import os 
import time
import threading
from pynput.keyboard import Key, Listener
from pynput import mouse
import pyautogui
from PIL import Image
from CohereAgent import CohereAgent
from convert import latex_to_pdf, download_md
import customtkinter
from dotenv import load_dotenv


class InputTracker:
    def __init__(self, queue, cohere_agent: CohereAgent):
        self.out_dir = "out"
        self.cohere_agent = cohere_agent
        self.queue = queue
        self.actions_set = []
        self.action_num = 0
        self.present_action = ""
        self.last_image_time = time.time()
        self.past_2_screenshots = []
        self.shortcut_keys = []


        # set the cursor
        #self.cursor_img = Image.open("cursor.png")

        self.screen_width, self.screen_height = pyautogui.size()
        self.remove_all_images()
        self.seperatable_actions("Initial State")


    def start_listeners(self):
        # Send status update to GUI
        self.queue.put(("status", "recording"))
        
        # constant screenshot thread
        self.constant_image_taker = ConstantPhotoTacker(self)
        self.constant_image_taker.start()

        # mouse + keyboard listeners
        self.mouse_listener = mouse.Listener(on_click=self.on_click)
        self.mouse_listener.start()

        self.keyboard_listener = Listener(on_press=self.on_press, on_release=self.on_release)
        self.keyboard_listener.start()

        # Wait for threads to finish
        self.keyboard_listener.join()
        self.mouse_listener.join()
        self.constant_image_taker.join()

    def remove_all_images(self, first_part=None):
        if first_part is None:
            first_part = f"{self.out_dir}/*actions_"
        for file in glob.glob(first_part + "*.png"):
            os.remove(file)

    def seperatable_actions(self, important_action):
        time_stamp = time.time()
        image_name = f"{self.out_dir}/actions_{self.action_num}.png"
        self.take_screenshot(image_name)

        if len(self.past_2_screenshots):
            if time_stamp - self.past_2_screenshots[-1][1] > 0.3:
                pre_image = self.past_2_screenshots[-1][0]
            else:
                pre_image = self.past_2_screenshots[0][0]

            pre_image_name = f"{self.out_dir}/pre_actions_{self.action_num}.png"
            low_res_pre_image = pre_image.resize((pre_image.width//2, pre_image.height//2), Image.LANCZOS)
            low_res_pre_image.save(pre_image_name, quality = 1)
        else:
            pre_image_name = "None"

        action  = [
            "TYPE: " + self.present_action,
            important_action,
            pre_image_name,
            image_name
        ]
        print(f"{self.action_num}. {action}")

        self.cohere_agent.add_keystroke_action_set(action, self.action_num)

        # self.queue.put(f"{self.action_num}: {action}")
        self.present_action = ""
        self.action_num += 1
        self.shortcut_keys = []

    def take_screenshot(self, file_name="test_screenshot.png"):

        cursor_pos = pyautogui.position()
        screen_shot = pyautogui.screenshot()
        screen_shot.save(file_name, quality = 1)


        # screen_shot.paste(self.cursor_img, (cursor_pos[0] + 100, cursor_pos[1] + 100), self.cursor_img)

        low_res_screen_shot = screen_shot.resize((screen_shot.width//2, screen_shot.height//2), Image.LANCZOS)
        low_res_screen_shot.save(file_name, quality = 1)

        
        # self.queue.put("Taken screenshot")
        print("Taken screenshot")
        # print(self.queue.get())

    def on_press(self, key):
        try:
            if self.shortcut_keys and self.shortcut_keys != [Key.shift]:
                self.seperatable_actions("SHORTCUT: " + "+".join(self.shortcut_keys) + "+" + str(key.char))
            else:
                self.present_action += str(key.char)
        except AttributeError:
            if key in [Key.enter]:
                self.seperatable_actions("PRESS: " + str(key))
            elif key in [Key.cmd, Key.ctrl]:
                if self.present_action:
                    self.seperatable_actions("PRESS: " + str(key))
                self.shortcut_keys.append(str(key))
            elif key == Key.shift:
                self.shortcut_keys.append(str(key))
            elif key == Key.backspace:
                if len(self.present_action) > 0:
                    self.present_action = self.present_action[:-1]

    def on_release(self, key):
        pass

    def on_click(self, x, y, button, pressed):
        if pressed:
            self.seperatable_actions(f"MOUSE CLICK: {button} ({x/self.screen_width}, {y/self.screen_height})")

    def regular_interval_screenshot(self):
        cursor_pos = pyautogui.position()
        screen_shot = pyautogui.screenshot()

        # screen_shot.paste(self.cursor_img, cursor_pos, self.cursor_img)

        if len(self.past_2_screenshots) == 2:
            self.past_2_screenshots = self.past_2_screenshots[1:] + [[screen_shot, time.time()]]
        else:
            self.past_2_screenshots.append([screen_shot, time.time()])

# hello world
class ConstantPhotoTacker(threading.Thread):
    def __init__(self, input_tracker: InputTracker):
        super().__init__()
        self.input_tracker = input_tracker

        # set the cursor
        # self.cursor_img = Image.open("cursor.png")

    def run(self):
        while True:
            self.input_tracker.regular_interval_screenshot()
            time.sleep(0.5)

# process wrapper
def input_listener(queue):
    cohere_agent = CohereAgent(os.getenv("COHERE_API_KEY"))
    tracker = InputTracker(queue, cohere_agent)
    tracker.start_listeners()  # Start all threads inside the child process

# GUI
class Tracker:
    def __init__(self, root, queue, cohere_agent: CohereAgent):
        self.root = root
        self.queue = queue
        self.process = None
        self.out_dir = "out"
        self.current_status = "idle"
        self.res = None

        self.cohere_agent = cohere_agent

        # Drag functionality variables
        self.drag_data = {"x": 0, "y": 0}
        self.is_dragging = False

        root.overrideredirect(True)
        root.attributes("-topmost", True)

        # Increased window width to accommodate the new download button
        window_width = 500
        window_height = 50
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = (screen_width - window_width) // 2  # Center horizontally
        y = screen_height - window_height - 70  # 60px margin from bottom
        root.geometry(f"{window_width}x{window_height}+{x}+{y}")

        root.attributes("-alpha", 0.95)  # Set window transparency to 85%
        
        bar_bg = "#555555"      # Bar background: pure black
        btn_bg = "#0b796f"      # Button background: dark gray
        btn_fg = "#ffffff"      # Button foreground (text): white
        btn_hover = "#026359"   # Button background on hover: slightly lighter dark gray
        btn_pressed = "#013d37" # Button background when pressed: medium gray

        # Main frame with drag functionality
        self.frame = tk.Frame(root, bg=bar_bg, padx=5, pady=5, cursor="hand2")
        self.frame.pack(fill="both", expand=True)

        # Bind drag events to the main frame
        self.frame.bind("<Button-1>", self.start_drag)
        self.frame.bind("<B1-Motion>", self.on_drag)
        self.frame.bind("<ButtonRelease-1>", self.stop_drag)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Dark.TButton",
                        background=btn_bg,
                        foreground=btn_fg,
                        borderwidth=0,
                        focusthickness=0,
                        padding=5)

        style.map("Dark.TButton",
                  background=[("active", btn_hover), ("pressed", btn_pressed)],
                  foreground=[("active", btn_fg), ("pressed", btn_fg)])

        # Left side frame for buttons
        button_frame = tk.Frame(self.frame, bg=bar_bg)
        button_frame.pack(side="left")

        # Bind drag events to button frame too
        button_frame.bind("<Button-1>", self.start_drag)
        button_frame.bind("<B1-Motion>", self.on_drag)
        button_frame.bind("<ButtonRelease-1>", self.stop_drag)

        start_btn = ttk.Button(button_frame, text="▶", command=self.start_listening, style="Dark.TButton", width=3)
        start_btn.pack(side="left", padx=3)

        stop_btn = ttk.Button(button_frame, text="■", command=self.stop_listening, style="Dark.TButton", width=3)
        stop_btn.pack(side="left", padx=3)

        download_btn = ttk.Button(button_frame, text="⬇", command=self.download_results, style="Dark.TButton", width=3)
        download_btn.pack(side="left", padx=3)

        quit_btn = ttk.Button(button_frame, text="✕", command=root.destroy, style="Dark.TButton", width=3)
        quit_btn.pack(side="left", padx=3)

        # Status text widget with drag functionality
        self.status_text = tk.Text(self.frame, 
                                   height=1, 
                                   width=10,
                                   bg="#333333", 
                                   fg="#ffffff",
                                   font=("Arial", 10),
                                   relief="flat",
                                   bd=0,
                                   padx=5,
                                   pady=8,
                                   wrap="none",
                                   cursor="hand2")
        self.status_text.pack(side="left", padx=(10, 5), fill="y")
        self.status_text.insert("1.0", "idle")
        self.status_text.config(state="disabled")  # Make it read-only

        # Bind drag events to status text
        self.status_text.bind("<Button-1>", self.start_drag)
        self.status_text.bind("<B1-Motion>", self.on_drag)
        self.status_text.bind("<ButtonRelease-1>", self.stop_drag)

        # Dropdown menu
        options = ["Beginner", "Intermediate", "Advanced"]
        self.selected_option = tk.StringVar(root)
        self.selected_option.set(options[0])  # Set a default value

        self.dropdown = tk.OptionMenu(self.frame, self.selected_option, *options)
        self.dropdown.pack(side="left", padx=(5, 0))
        
        # Bind drag events to dropdown (though it's less intuitive to drag from here)
        self.dropdown.bind("<Button-1>", self.start_drag_dropdown)
        self.dropdown.bind("<B1-Motion>", self.on_drag)
        self.dropdown.bind("<ButtonRelease-1>", self.stop_drag)

        # file type Dropdown menu
        file_options = ["LATEX", ".md"]
        self.selected_file_option = tk.StringVar(root)
        self.selected_file_option.set(file_options[0])  # Set a default value

        file_dropdown = tk.OptionMenu(self.frame, self.selected_file_option, *file_options)
        file_dropdown.pack(side="left", padx=(5, 0))

        # Keyboard shortcuts
        def on_shortcut(event):
            if (event.state & 0x04) and (event.state & 0x08):  # Command + Option (on Mac)
                if event.keysym.lower() == "r":
                    self.start_listening()
                elif event.keysym.lower() == "p":
                    self.stop_listening()
                elif event.keysym.lower() == "d":
                    self.download_results()
                elif event.keysym.lower() == "q":
                    root.destroy()

        root.bind_all("<KeyPress>", on_shortcut)

        self.poll_queue()
    
    def start_drag(self, event):
        """Start dragging the window"""
        self.is_dragging = True
        self.drag_data["x"] = event.x_root
        self.drag_data["y"] = event.y_root
        # Change cursor to indicate dragging
        self.frame.config(cursor="fleur")

    def start_drag_dropdown(self, event):
        """Special handler for dropdown to prevent conflicts"""
        # Only start drag if clicking on the dropdown button area, not the menu
        if not hasattr(event.widget, 'tk') or event.widget.winfo_class() == 'Menubutton':
            self.start_drag(event)

    def on_drag(self, event):
        """Handle window dragging"""
        if self.is_dragging:
            # Calculate the new position
            delta_x = event.x_root - self.drag_data["x"]
            delta_y = event.y_root - self.drag_data["y"]
            
            # Get current window position
            current_x = self.root.winfo_x()
            current_y = self.root.winfo_y()
            
            # Calculate new position
            new_x = current_x + delta_x
            new_y = current_y + delta_y
            
            # Get screen dimensions to prevent moving window off screen
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            window_width = self.root.winfo_width()
            window_height = self.root.winfo_height()
            
            # Keep window within screen bounds
            new_x = max(0, min(new_x, screen_width - window_width))
            new_y = max(0, min(new_y, screen_height - window_height))
            
            # Move the window
            self.root.geometry(f"+{new_x}+{new_y}")
            
            # Update drag data
            self.drag_data["x"] = event.x_root
            self.drag_data["y"] = event.y_root

    def stop_drag(self, event):
        """Stop dragging the window"""
        self.is_dragging = False

    # Example function to get the selected value (you can use this elsewhere)
    def get_selection(self):
        return self.selected_option.get()

    def update_status(self, status):
        """Update the status text widget with new status"""
        self.current_status = status
        self.status_text.config(state="normal")
        self.status_text.delete("1.0", "end")
        self.status_text.insert("1.0", status)
        self.status_text.config(state="disabled")
        
        # Optional: Change color based on status
        color_map = {
            "idle": "#ffffff",
            "recording": "#00ff00",
            "processing": "#ffaa00",
            "downloading": "#00aaff"
        }
        if status in color_map:
            self.status_text.config(fg=color_map[status])

    def start_listening(self):
        if not self.process:
            self.update_status("starting...")
            os.makedirs(self.out_dir, exist_ok=True)
            for f in glob.glob(os.path.join(self.out_dir, "*")):
                if os.path.isfile(f):
                    os.remove(f)
            self.process = multiprocessing.Process(target=input_listener, args=(self.queue,))
            self.process.start()
            print("InputTracker started.")

    def stop_listening(self):
        if self.process:
            self.update_status("processing")
            self.process.terminate()
            self.process = None
            print("InputTracker stopped.")
            
            # Run processing in a separate thread to avoid blocking the GUI
            processing_thread = threading.Thread(target=self._process_results)
            processing_thread.start()

    def download_results(self):
        """Handle download button click"""
        self.update_status("downloading")
        
        # Run download in a separate thread to avoid blocking the GUI
        download_thread = threading.Thread(target=self._download_results)
        download_thread.start()

    def _download_results(self):
        """Download results in a separate thread"""
        try:
            # You can customize this function based on what you want to download
            # For example, you might want to:
            # 1. Generate and save the LaTeX/PDF
            # 2. Open a file dialog to let user choose save location
            # 3. Copy files to a specific download folder
            # 4. Export screenshots or processed data
            
            # Example implementation:
            if self.res:
                # res = self.cohere_agent.return_final_LATEX(self.get_selection())
                if self.selected_file_option.get() == "LATEX":
                    latex_to_pdf(self.res)
                elif self.selected_file_option.get() == ".md":
                    download_md(self.res)

            
            # You could also add file dialog functionality:
            # from tkinter import filedialog
            # save_path = filedialog.asksaveasfilename(defaultextension=".pdf")
            # if save_path:
            #     # Save your file to the chosen location
            
            print("Download completed successfully")
            # Update status back to idle when download is complete
            self.root.after(0, lambda: self.update_status("idle"))
        except Exception as e:
            print(f"Error during download: {e}")
            self.root.after(0, lambda: self.update_status("error"))

    def _process_results(self):
        """Process results in a separate thread"""
        try:
            files = [f for f in glob.glob(os.path.join(self.out_dir, "*.png"))]
            print(files)
            if self.selected_file_option.get() == "LATEX":
                self.res = self.cohere_agent.return_final_LATEX(files)
            elif self.selected_file_option.get() == ".md":
                self.res = self.cohere_agent.return_final_MD()
            
            # latex_to_pdf(res)
            # Update status back to idle when processing is complete
            self.root.after(0, lambda: self.update_status("idle"))
        except Exception as e:
            print(f"Error processing results: {e}")
            self.root.after(0, lambda: self.update_status("error"))

    def poll_queue(self):
        while not self.queue.empty():
            try:
                msg = self.queue.get_nowait()
                if isinstance(msg, tuple) and len(msg) == 2:
                    msg_type, content = msg
                    if msg_type == "status":
                        self.update_status(content)
                else:
                    print(msg)
            except:
                break
        
        self.root.after(100, self.poll_queue)

if __name__ == "__main__":
    load_dotenv()
    multiprocessing.set_start_method("spawn")  # macOS requirement
    queue = multiprocessing.Manager().Queue()

    root = tk.Tk()
    app = Tracker(root, queue, CohereAgent(os.getenv("COHERE_API_KEY")))
    root.mainloop()