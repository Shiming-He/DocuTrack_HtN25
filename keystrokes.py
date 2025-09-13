# pip3 install pynput
# must allow vscode in input monitoring settings


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

# collect events until released
with Listener(on_press=on_press, on_release=on_release) as listener:
    listener.join()
