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

from dotenv import load_dotenv


class InputTracker:
    def __init__(self, queue, cohere_agent: CohereAgent):
        self.cohere_agent = cohere_agent
        self.queue = queue
        self.actions_set = []
        self.action_num = 0
        self.present_action = ""
        self.last_image_time = time.time()
        self.past_2_screenshots = []
        self.shortcut_keys = []

        self.screen_width, self.screen_height = pyautogui.size()
        self.remove_all_images()
        self.seperatable_actions("Initial State")

    def start_listeners(self):
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


    def remove_all_images(self, first_part="image_files/*actions_"):
        for file in glob.glob(first_part + "*.png"):
            os.remove(file)

    def seperatable_actions(self, important_action):
        time_stamp = time.time()
        image_name = f"image_files/actions_{self.action_num}.png"
        self.take_screenshot(image_name)

        if len(self.past_2_screenshots):
            if time_stamp - self.past_2_screenshots[-1][1] > 0.3:
                pre_image = self.past_2_screenshots[-1][0]
            else:
                pre_image = self.past_2_screenshots[0][0]

            pre_image_name = f"image_files/pre_actions_{self.action_num}.png"
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
        screen_shot = pyautogui.screenshot()
        screen_shot.save(file_name, quality = 1)
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
        screen_shot = pyautogui.screenshot()
        if len(self.past_2_screenshots) == 2:
            self.past_2_screenshots = self.past_2_screenshots[1:] + [[screen_shot, time.time()]]
        else:
            self.past_2_screenshots.append([screen_shot, time.time()])


class ConstantPhotoTacker(threading.Thread):
    def __init__(self, input_tracker: InputTracker):
        super().__init__()
        self.input_tracker = input_tracker

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

        self.cohere_agent = cohere_agent

        root.overrideredirect(True)
        root.attributes("-topmost", True)
        root.geometry("135x50+1200+50")

        bar_bg = "#000000"
        btn_bg = "#333333"
        btn_fg = "#ffffff"
        btn_hover = "#444444"
        btn_pressed = "#666666"

        frame = tk.Frame(root, bg=bar_bg, padx=5, pady=5)
        frame.pack(fill="both", expand=True)

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

        start_btn = ttk.Button(frame, text="▶", command=self.start_listening, style="Dark.TButton", width=3)
        start_btn.pack(side="left", padx=3)

        stop_btn = ttk.Button(frame, text="■", command=self.stop_listening, style="Dark.TButton", width=3)
        stop_btn.pack(side="left", padx=3)

        quit_btn = ttk.Button(frame, text="✕", command=root.destroy, style="Dark.TButton", width=3)
        quit_btn.pack(side="left", padx=3)

        self.poll_queue()

    def start_listening(self):
        if not self.process:
            os.makedirs("image_files", exist_ok=True)
            self.process = multiprocessing.Process(target=input_listener, args=(self.queue,))
            self.process.start()
            print("InputTracker started.")

    def stop_listening(self):
        if self.process:
            self.process.terminate()
            self.process = None
            print("InputTracker stopped.")
            self.cohere_agent.return_final_LATEX()

    def poll_queue(self):
        while not self.queue.empty():
            # msg = self.queue.get()
            print(msg)
        self.root.after(100, self.poll_queue)



if __name__ == "__main__":
    load_dotenv()
    multiprocessing.set_start_method("spawn")  # macOS requirement
    queue = multiprocessing.Manager().Queue()


    root = tk.Tk()
    app = Tracker(root, queue, CohereAgent(os.getenv("COHERE_API_KEY")))
    root.mainloop()

    # process = multiprocessing.Process(target=input_listener, args=(queue,))
    # process.start()
    

    # input_listener(queue, CohereAgent(os.getenv("COHERE_API_KEY")) )

