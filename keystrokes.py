# pip3 install pynput
# must allow vscode in input monitoring settings


from pynput.keyboard import Key, Listener
from pynput import mouse
import pyautogui # allow to take screenshot


def take_screenshot(file_name = "test_screenshot.png"):
    screen_short = pyautogui.screenshot()

    screen_short.save(file_name)
    print("Taken screenshot")

# keyboard check
def on_press(key):
    try:
        print(f"Alphanumeric key pressed: {key.char}")
    except AttributeError: # special keys (space, shift, etc.
        # check for enter key
        if key == Key.enter:
            take_screenshot()
        print(f"Special key pressed: {key}")

    

def on_release(key):
    print(f"Key released: {key}")
    if key == Key.esc: # quit
        return False
    





# check mouse click
def on_click(x, y, button, pressed):
    print("mouse_interaction")

    if pressed:

        print("mouse_click")
        take_screenshot()



mouse_listener =  mouse.Listener(on_click=on_click)

mouse_listener.start()
    

# collect events until released
keyboard_listener = Listener(on_press=on_press, on_release=on_release)


keyboard_listener.start()
keyboard_listener.join()
mouse_listener.join()
