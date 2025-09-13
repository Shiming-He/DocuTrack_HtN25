# pip3 install pynput
# must allow vscode in input monitoring settings


from pynput.keyboard import Key, Listener
from pynput import mouse
import pyautogui # allow to take screenshot
import glob
import os
import time
import threading


# create a keylogger class
class KeyTracker:
    '''KeyTracker'''

    def __init__(self):
        # init variables
        self.actions_set = [] # this stores action set, seperate by screen shots format [["actions...", "screenshot.png"], ...]
        self.action_num = 0
        self.present_action = ""
        self.last_image_time = time.time()
        
        self.past_2_screenshots = []
        constant_image_taker = ConstantPhotoTacker(self)
        constant_image_taker.start()

        # get screen size
        self.screen_width, self.screen_height = pyautogui.size()

        self.remove_all_images()
        self.seperatable_actions("Initial State")


        mouse_listener =  mouse.Listener(on_click=self.on_click)

        mouse_listener.start()
            

        # collect events until released
        keyboard_listener = Listener(on_press=self.on_press, on_release=self.on_release)


        keyboard_listener.start()
        keyboard_listener.join()
        mouse_listener.join()
        constant_image_taker.join()







    def remove_all_images(self, first_part = "image_files/*actions_"):
        # print(str(first_part + "*.png")
        for file in glob.glob(first_part + "*.png"):
            os.remove(file)



    def seperatable_actions(self, important_action):
        '''this means the action is large enough that seperates previous inputs with present input
        requires image'''
        time_stamp = time.time()
        image_name = f"image_files/actions_{self.action_num}.png"

        self.take_screenshot(image_name)

        # get the before image time between 300ms and 800ms
        if len(self.past_2_screenshots):
            if self.past_2_screenshots[-1][1] > 0.3:
                pre_image = self.past_2_screenshots[-1][0]
            else:
                pre_image = self.past_2_screenshots[0][0]

            # save the past image
            pre_image_name = f"image_files/pre_actions_{self.action_num}.png"
            pre_image.save(pre_image_name)
        else:
            pre_image_name = "None"


        # end actions up this point
        self.actions_set.append(["TYPE: " + self.present_action, important_action, pre_image_name , image_name])

        print(self.action_num, self.actions_set[-1]) # print statement and number

        self.present_action = ""
        self.action_num += 1








    def take_screenshot(self, file_name = "test_screenshot.png"):
        screen_shot = pyautogui.screenshot()

        screen_shot.save(file_name)
        print("Taken screenshot")

    # keyboard check
    def on_press(self, key):
        try:
            # print(f"Alphanumeric key pressed: {key.char}")

            print(key)
            self.present_action += str(key.char)
        except AttributeError: # special keys (space, shift, etc.
            # check for enter key
            if key == Key.enter:
                self.seperatable_actions("PRESS: " + str(key))
            elif key == Key.backspace:
                if len(self.present_action) > 0:
                    self.present_action = self.present_action[:-1]

            # print(f"Special key pressed: {key}")

        

    def on_release(self, key):
        # print(f"Key released: {key}")
        if key == Key.esc: # quit
            return False
        





    # check mouse click
    def on_click(self, x, y, button, pressed):
        # print("mouse_interaction")

        if pressed:

            print("mouse_click", button)
            self.seperatable_actions("MOUSE ClICK: " + str(button) + f" ({x/self.screen_width}, {y/self.screen_height})")


    def get_action_num(self):
        return self.action_num
    
    def regular_interval_screenshot(self):
        
        screen_shot = pyautogui.screenshot()
        if len(self.past_2_screenshots) == 2:
            self.past_2_screenshots = self.past_2_screenshots[1:] + [[screen_shot, time.time()]]
        else:
            self.past_2_screenshots.append([screen_shot, time.time()])


class ConstantPhotoTacker(threading.Thread):

    def __init__(self, key_tracker: KeyTracker):
        super().__init__()
        self.key_tracker = key_tracker
        # self.past_2_screenshots = []


    


    def run(self):
        time.sleep(0.5)
        self.key_tracker.regular_interval_screenshot()
            


KeyTracker()