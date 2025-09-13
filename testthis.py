import tkinter as tk
from tkinter import ttk
from pynput.keyboard import Key, Listener

def on_press(key):
    try:
        print(f"Alphanumeric key pressed: {key.char}")
    except AttributeError: # special keys (space, shift, etc.)
        print(f"Special key pressed: {key}")

def on_release(key):
    print(f"Key released: {key}")
    if key == Key.esc: # quit
        return False

def start_action():
    global keyboard_listener
    if not keyboard_listener:
        keyboard_listener = Listener(on_press=on_press, on_release=on_release)
        keyboard_listener.start()
    print("Hello (Start pressed)")

def stop_action():
    global keyboard_listener
    if keyboard_listener:
        keyboard_listener.stop()
        keyboard_listener.join()
        keyboard_listener = None

    print("Hello (Stop pressed)")

keyboard_listener = None

root = tk.Tk()
root.overrideredirect(True)
root.attributes("-topmost", True)
root.geometry("135x50+1200+50")

bar_bg = "#000000"
btn_bg = "#333333"
btn_fg = "#ffffff"
btn_hover = "#444444"
btn_pressed = "#666666"  # doesnt work lol

frame = tk.Frame(root, bg=bar_bg, padx=5, pady=5)
frame.pack(fill="both", expand=True)

# ttk style
style = ttk.Style()
style.theme_use('clam')  # ensure custom colors apply

style.configure("Dark.TButton",
                background=btn_bg,
                foreground=btn_fg,
                borderwidth=0,
                focusthickness=0,
                padding=5)

# background for hover (active) and pressed states
style.map("Dark.TButton",
          background=[('active', btn_hover), ('pressed', btn_pressed)],
          foreground=[('active', btn_fg), ('pressed', btn_fg)])

# buttons
start_btn = ttk.Button(frame, text="▶", command=start_action, style="Dark.TButton", width=3)
start_btn.pack(side="left", padx=3)

stop_btn = ttk.Button(frame, text="■", command=stop_action, style="Dark.TButton", width=3)
stop_btn.pack(side="left", padx=3)

quit_btn = ttk.Button(frame, text="✕", command=root.destroy, style="Dark.TButton", width=3)
quit_btn.pack(side="left", padx=3)

root.mainloop()

if keyboard_listener:
    print("stopping listener")
    keyboard_listener.stop()
    keyboard_listener.join()
