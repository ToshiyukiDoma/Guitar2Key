import pygame
import threading
import time
from pynput.keyboard import Controller
import tkinter as tk
from tkinter import ttk
import os

# Init
pygame.init()
pygame.joystick.init()

keyboard = Controller()

# Constants for HAT inputs
HAT_UP = 100
HAT_DOWN = 101
HAT_LEFT = 102
HAT_RIGHT = 103

# Input config
string_inputs = [1, 2, 0, 3, 4]
strum_up_input = 100
strum_down_input = 101
mapped_keys = ['s', 'd', 'f', 'g', 'h']
enabled = False

held_strings = [False] * 5
active_keys = [False] * 5
selected_joystick_index = 0
joystick = None

# Settings file
settings_file = "settings.txt"

# Define get_button_state function
def get_button_state(input_index, buttons, hats):
    """Check the state of a button or hat input."""
    if input_index < 10:  # For buttons (up to Button 9)
        return buttons[input_index]
    elif input_index == HAT_UP:
        return hats[0][1] == 1  # Hat Up
    elif input_index == HAT_DOWN:
        return hats[0][1] == -1  # Hat Down
    elif input_index == HAT_LEFT:
        return hats[0][0] == -1  # Hat Left
    elif input_index == HAT_RIGHT:
        return hats[0][0] == 1  # Hat Right
    return False

# Loading settings from a file
def load_settings():
    if os.path.exists(settings_file):
        with open(settings_file, "r") as f:
            lines = f.readlines()

        for line in lines:
            if line.startswith("Selected Gamepad:"):
                selected_gamepad = line.split(":")[1].strip()
                joystick_dropdown.set(selected_gamepad)
            elif line.startswith("Strum Up Input:"):
                global strum_up_input
                strum_up_input = int(line.split(":")[1].strip())
            elif line.startswith("Strum Down Input:"):
                global strum_down_input
                strum_down_input = int(line.split(":")[1].strip())
            elif line.startswith("String"):
                parts = line.split(":")[1].split("->")
                string_input = int(parts[0].strip())
                key_output = parts[1].strip()
                string_inputs[string_input] = string_input
                mapped_keys[string_input] = key_output

# Monitor the gamepad input and trigger the appropriate actions
def monitor_gamepad():
    global enabled, joystick

    last_strum_state = False

    while True:
        if joystick is None or not joystick.get_init():
            time.sleep(0.5)
            continue

        pygame.event.pump()
        buttons = [joystick.get_button(i) for i in range(joystick.get_numbuttons())]
        hats = [joystick.get_hat(i) for i in range(joystick.get_numhats())]

        current_strum = get_button_state(strum_up_input, buttons, hats) or get_button_state(strum_down_input, buttons, hats)
        strum_pressed = current_strum and not last_strum_state  # detect rising edge
        last_strum_state = current_strum

        if enabled:
            for i in range(5):
                held = get_button_state(string_inputs[i], buttons, hats)

                if not held and held_strings[i]:
                    held_strings[i] = False
                    if active_keys[i]:
                        keyboard.release(mapped_keys[i])
                        active_keys[i] = False

                if held and not held_strings[i]:
                    held_strings[i] = True

                if held_strings[i] and strum_pressed:
                    if active_keys[i]:
                        keyboard.release(mapped_keys[i])
                        time.sleep(0.01)
                    keyboard.press(mapped_keys[i])
                    active_keys[i] = True

        time.sleep(0.01)

# Start the GUI and handle input settings
def start_gui():
    load_settings()

    def toggle_enabled():
        nonlocal btn_toggle
        global enabled
        enabled = not enabled
        btn_toggle.config(text="Disable" if enabled else "Enable")

    # Save the mappings to global variables
    def save_mappings():
        global strum_up_input, strum_down_input
        for i in range(5):
            # Convert the selected input string into the correct integer index
            string_input = cmb_strings[i].get()
            string_inputs[i] = input_to_index(string_input)  # Convert string to index
            mapped_keys[i] = entry_keys[i].get().lower()

        strum_up_input = input_to_index(cmb_strum_up.get())  # Convert strum up input to index
        strum_down_input = input_to_index(cmb_strum_down.get())  # Convert strum down input to index

    def select_joystick(event=None):
        global joystick, selected_joystick_index
        selected_joystick_index = joystick_dropdown.current()
        joystick = pygame.joystick.Joystick(selected_joystick_index)
        joystick.init()

    def get_input_choices():
        normal_buttons = [f"Button {i}" for i in range(20)]
        hat_options = ["Hat Up", "Hat Down", "Hat Left", "Hat Right"]
        return normal_buttons + hat_options

    # Map input string (Button or Hat) to the correct index value
    def input_to_index(name):
        if name.startswith("Button "):
            return int(name.split(" ")[1])  # Convert 'Button 1' to index 1
        elif name == "Hat Up":
            return HAT_UP
        elif name == "Hat Down":
            return HAT_DOWN
        elif name == "Hat Left":
            return HAT_LEFT
        elif name == "Hat Right":
            return HAT_RIGHT
        return 0  # Default to Button 0 if no match

    def index_to_input(index):
        if index < 100:
            return f"Button {index}"
        elif index == HAT_UP:
            return "Hat Up"
        elif index == HAT_DOWN:
            return "Hat Down"
        elif index == HAT_LEFT:
            return "Hat Left"
        elif index == HAT_RIGHT:
            return "Hat Right"
        return "Button 0"

    root = tk.Tk()
    root.title("Gamepad Guitar Mapper")
    root.geometry("400x500")

    tk.Label(root, text="Select Gamepad:").pack()
    joystick_names = [pygame.joystick.Joystick(i).get_name() for i in range(pygame.joystick.get_count())]
    joystick_dropdown = ttk.Combobox(root, values=joystick_names, state="readonly")
    joystick_dropdown.current(0)
    joystick_dropdown.pack()
    joystick_dropdown.bind("<<ComboboxSelected>>", select_joystick)

    if pygame.joystick.get_count() > 0:
        joystick = pygame.joystick.Joystick(0)
        joystick.init()

    input_choices = get_input_choices()

    tk.Label(root, text="Strum Inputs:").pack()
    cmb_strum_up = ttk.Combobox(root, values=input_choices)
    cmb_strum_up.set(index_to_input(strum_up_input))
    cmb_strum_up.pack()

    cmb_strum_down = ttk.Combobox(root, values=input_choices)
    cmb_strum_down.set(index_to_input(strum_down_input))
    cmb_strum_down.pack()

    tk.Label(root, text="String Inputs and Mapped Keys:").pack()
    cmb_strings = []
    entry_keys = []
    for i in range(5):
        frame = tk.Frame(root)
        frame.pack()
        cmb = ttk.Combobox(frame, values=input_choices)
        cmb.set(index_to_input(string_inputs[i]))
        cmb.pack(side=tk.LEFT)
        entry = tk.Entry(frame)
        entry.insert(0, mapped_keys[i])
        entry.pack(side=tk.LEFT)
        cmb_strings.append(cmb)
        entry_keys.append(entry)

    def save_wrapper():
        save_mappings()
        save_settings()  # Save settings to file
        for i in range(5):
            string_inputs[i] = input_to_index(cmb_strings[i].get())
        global strum_up_input, strum_down_input
        strum_up_input = input_to_index(cmb_strum_up.get())
        strum_down_input = input_to_index(cmb_strum_down.get())

    btn_save = tk.Button(root, text="Save Mapping", command=save_wrapper)
    btn_save.pack(pady=10)

    btn_toggle = tk.Button(root, text="Enable", command=toggle_enabled)
    btn_toggle.pack(pady=10)

    root.mainloop()

# Start everything
threading.Thread(target=monitor_gamepad, daemon=True).start()
start_gui()
