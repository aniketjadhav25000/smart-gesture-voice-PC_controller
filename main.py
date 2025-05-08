import cv2

import time
import mediapipe as mp
import pyautogui
import math
import numpy as np
from pynput.keyboard import Controller
from tkinter import Tk, Button, Label, Frame
import threading
import speech_recognition as sr

# Import our new VoiceCommandManager
from voice_command_manager import VoiceCommandManager

# Initialize Mediapipe
mpHands = mp.solutions.hands
hands = mpHands.Hands(static_image_mode=False, max_num_hands=1,
                      min_detection_confidence=0.7, min_tracking_confidence=0.7)
mpDraw = mp.solutions.drawing_utils

keyboard = Controller()
cap = cv2.VideoCapture(0)
cap.set(3, 1280)
cap.set(4, 720)
screen_width, screen_height = pyautogui.size()

# Initialize voice command manager
voice_manager = VoiceCommandManager()

class ButtonObj:
    def __init__(self, pos, text, size=[70, 70]):
        self.pos = pos
        self.size = size
        self.text = text

keys = [["Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P", "CL"],
        ["A", "S", "D", "F", "G", "H", "J", "K", "L", ";", "SP"],
        ["Z", "X", "C", "V", "B", "N", "M", ",", ".", "/", "APR"],
        ["MIC", "CLR"]]  

button_list = [ButtonObj([100 * j + 10, 100 * i + 10], key)
               for i in range(len(keys)) for j, key in enumerate(keys[i])]

def draw_keyboard_buttons(img, button_list):
    for button in button_list:
        x, y = button.pos
        w, h = button.size
        cv2.rectangle(img, button.pos, (x + w, y + h), (96, 96, 96), cv2.FILLED)
        cv2.putText(img, button.text, (x + 10, y + 60),
                    cv2.FONT_HERSHEY_PLAIN, 2, (255, 255, 255), 2)
    return img

def calculate_distance(point1, point2):
    x1, y1 = point1
    x2, y2 = point2
    return math.hypot(x2 - x1, y2 - y1)

def switch_mode_callback(mode_name):
    """Callback function for voice command mode switching"""
    if mode_name == "mouse":
        cv2.destroyAllWindows()
        mouse_mode()
    elif mode_name == "keyboard":
        cv2.destroyAllWindows()
        keyboard_mode()

def main_menu():
    # Set the callback function for mode switching
    voice_manager.set_mode_switch_callback(switch_mode_callback)
    
    root = Tk()
    root.title("Smart Controller for Computer")
    root.geometry("500x400")
    root.configure(bg="#2E3B4E")

    def set_mode_to_mouse():
        root.destroy()
        mouse_mode()

    def set_mode_to_keyboard():
        root.destroy()
        keyboard_mode()
        
    def toggle_voice_commands():
        if voice_manager.listening:
            voice_manager.stop_listening()
            voice_cmd_btn.configure(text="Enable Voice Commands", bg="#4CAF50")
        else:
            voice_manager.start_listening()
            voice_cmd_btn.configure(text="Disable Voice Commands", bg="#F44336")

    Label(root, text="smart-gesture-voice-PC_controller", font=("Arial", 20, "bold"),
          bg="#2E3B4E", fg="white").pack(pady=20)

    Label(root, text="Select Your Control Mode:", font=("Arial", 14),
          bg="#2E3B4E", fg="white").pack(pady=10)

    Button(root, text="Mouse Control", command=set_mode_to_mouse, width=20, height=2,
           bg="#4CAF50", fg="white", font=("Arial", 12)).pack(pady=10)

    Button(root, text="Keyboard Control", command=set_mode_to_keyboard, width=20, height=2,
           bg="#2196F3", fg="white", font=("Arial", 12)).pack(pady=10)
           
    voice_cmd_btn = Button(root, text="Enable Voice Commands", command=toggle_voice_commands, 
                  width=20, height=2, bg="#4CAF50", fg="white", font=("Arial", 12))
    voice_cmd_btn.pack(pady=20)

    Label(root, text="Voice commands let you control your computer with voice", 
          font=("Arial", 10), bg="#2E3B4E", fg="#BBBBBB").pack(pady=5)

    root.mainloop()

def mouse_mode():
    last_left_click_time = 0
    last_right_click_time = 0
    click_threshold = 40
    smoothening = 5
    prev_loc_x, prev_loc_y = 0, 0
    
    # Pre-defined help text for mouse mode
    help_text = ["Mouse Mode Controls: ",
                "- Move index finger to move cursor",
                "- Pinch index & middle fingers for left click",
                "- Pinch thumb & index finger for right click",
                "- Say 'switch to keyboard' to change modes",
                "- Press ESC for main menu"]

    while True:
        success, frame = cap.read()
        if not success:
            break

        frame = cv2.flip(frame, 1)
        frame_height, frame_width, _ = frame.shape
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb)

        if results.multi_hand_landmarks:
            hand_landmarks = results.multi_hand_landmarks[0]
            mpDraw.draw_landmarks(frame, hand_landmarks, mpHands.HAND_CONNECTIONS)
            landmarks = [(lm.x * frame_width, lm.y * frame_height) for lm in hand_landmarks.landmark]

            index_finger = landmarks[8]
            middle_finger = landmarks[12]
            thumb = landmarks[4]

            screen_x = np.interp(index_finger[0], (0, frame_width), (0, screen_width))
            screen_y = np.interp(index_finger[1], (0, frame_height), (0, screen_height))

            loc_x = prev_loc_x + (screen_x - prev_loc_x) / smoothening
            loc_y = prev_loc_y + (screen_y - prev_loc_y) / smoothening
            pyautogui.moveTo(loc_x, loc_y)
            prev_loc_x, prev_loc_y = loc_x, loc_y

            dist_index_middle = calculate_distance(index_finger, middle_finger)
            dist_thumb_index = calculate_distance(thumb, index_finger)

            if dist_index_middle < click_threshold:
                if time.time() - last_left_click_time > 0.5:
                    pyautogui.click(button="left")
                    last_left_click_time = time.time()

            if dist_thumb_index < click_threshold:
                if time.time() - last_right_click_time > 0.5:
                    pyautogui.click(button="right")
                    last_right_click_time = time.time()

        # Display help text
        y_pos = 100
        for line in help_text:
            cv2.putText(frame, line, (20, y_pos), cv2.FONT_HERSHEY_PLAIN, 1.5, (255, 255, 255), 2)
            y_pos += 30
            
        # Display voice command status
        if voice_manager.listening:
            status_color = (0, 255, 0)  # Green when active
            cv2.putText(frame, f"Voice: {voice_manager.status_message}", (20, 50), 
                      cv2.FONT_HERSHEY_PLAIN, 1.5, status_color, 2)
        else:
            status_color = (0, 0, 255)  # Red when inactive
            cv2.putText(frame, "Voice commands disabled", (20, 50), 
                      cv2.FONT_HERSHEY_PLAIN, 1.5, status_color, 2)

        cv2.imshow("Mouse Control", frame)

        key = cv2.waitKey(1)
        if key == 27:  # ESC key
            cv2.destroyAllWindows()
            main_menu()
            break

listening = False
mic_feedback = ""
transcribed = []

def speech_to_text_worker():
    global listening, mic_feedback
    r = sr.Recognizer()
    retries = 1
    with sr.Microphone() as source:
        try:
            mic_feedback = "Listening... adjusting noise"
            r.adjust_for_ambient_noise(source, duration=1.5)
            mic_feedback = "Speak now..."
            audio = r.listen(source, timeout=6, phrase_time_limit=6)
            mic_feedback = "Transcribing..."
            result = r.recognize_google(audio)
            transcribed.append(result)
        except sr.WaitTimeoutError:
            if retries:
                retries -= 1
                mic_feedback = "Retrying, speak again..."
                try:
                    audio = r.listen(source, timeout=6, phrase_time_limit=6)
                    mic_feedback = "Transcribing..."
                    result = r.recognize_google(audio)
                    transcribed.append(result)
                except:
                    mic_feedback = "No voice detected."
            else:
                mic_feedback = "No speech detected."
        except sr.UnknownValueError:
            mic_feedback = "Couldn't understand you."
        except sr.RequestError:
            mic_feedback = "Connection error."

    listening = False
    time.sleep(1)
    mic_feedback = ""

def keyboard_mode():
    global listening, mic_feedback
    text = ""
    delay = 0
    capitalize = False
    typing_allowed = False
    last_button_press = None
    
    # Add help for voice commands
    help_text = ["Keyboard Controls:",
                "- Pinch over letter to type",
                "- 'SP': Space, 'CL': Backspace",
                "- 'APR': Toggle CAPS, 'CLR': Clear text",
                "- 'MIC': Voice dictation, 'CMD': Toggle voice commands",
                "- Say 'switch to mouse' to change modes"]

    while True:
        success, frame = cap.read()
        if not success:
            break

        frame = cv2.flip(frame, 1)
        frame_height, frame_width, _ = frame.shape
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb)

        frame = draw_keyboard_buttons(frame, button_list)

        if results.multi_hand_landmarks:
            hand_landmarks = results.multi_hand_landmarks[0]
            mpDraw.draw_landmarks(frame, hand_landmarks, mpHands.HAND_CONNECTIONS)
            landmarks = [(lm.x * frame_width, lm.y * frame_height) for lm in hand_landmarks.landmark]

            thumb = landmarks[4]
            index_finger = landmarks[8]
            distance = calculate_distance(thumb, index_finger)

            if distance < 50:
                typing_allowed = True
                cv2.circle(frame, (int(thumb[0]), int(thumb[1])), 15, (0, 255, 0), cv2.FILLED)
                cv2.circle(frame, (int(index_finger[0]), int(index_finger[1])), 15, (0, 255, 0), cv2.FILLED)
            else:
                typing_allowed = False
                last_button_press = None

            if typing_allowed and delay == 0:
                for i, button in enumerate(button_list):
                    x, y = button.pos
                    w, h = button.size
                    if x < index_finger[0] < x + w and y < index_finger[1] < y + h:
                        cv2.rectangle(frame, (x - 5, y - 5), (x + w + 5, y + h + 5), (255, 255, 255), cv2.FILLED)
                        cv2.putText(frame, button.text, (x + 20, y + 65),
                                    cv2.FONT_HERSHEY_PLAIN, 4, (0, 0, 0), 4)

                        if last_button_press != i:
                            if button.text == "SP":
                                text += " "
                                keyboard.press(' ')
                                keyboard.release(' ')
                            elif button.text == "CL":
                                if len(text) > 0:
                                    text = text[:-1]
                                    keyboard.press('\b')
                                    keyboard.release('\b')
                            elif button.text == "APR":
                                capitalize = not capitalize
                            elif button.text == "CLR":
                                text = ""
                            elif button.text == "MIC":
                                if not listening:
                                    listening = True
                                    mic_feedback = "Starting mic..."
                                    threading.Thread(target=speech_to_text_worker).start()
                            elif button.text == "CMD":
                                # Toggle voice commands
                                if voice_manager.listening:
                                    voice_manager.stop_listening()
                                else:
                                    voice_manager.start_listening()
                            else:
                                letter = button.text.upper() if capitalize else button.text.lower()
                                text += letter
                                keyboard.press(letter)
                                keyboard.release(letter)

                            last_button_press = i
                            delay = 1

        if delay > 0:
            delay += 1
            if delay > 10:
                delay = 0

        if mic_feedback:
            cv2.putText(frame, mic_feedback, (450, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)

        if transcribed:
            text += " " + transcribed.pop(0)

        # Display help text in top left
        y_pos = 100
        for line in help_text:
            cv2.putText(frame, line, (20, y_pos), cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 255), 1)
            y_pos += 25

        # Display voice command status
        if voice_manager.listening:
            status_color = (0, 255, 0)  # Green when active
            cv2.putText(frame, f"Voice: {voice_manager.status_message}", (800, 50), 
                      cv2.FONT_HERSHEY_PLAIN, 1.5, status_color, 2)
        else:
            status_color = (0, 0, 255)  # Red when inactive
            cv2.putText(frame, "Voice commands disabled", (800, 50), 
                      cv2.FONT_HERSHEY_PLAIN, 1.5, status_color, 2)

        height = 80 if len(text) < 40 else 120
        cv2.rectangle(frame, (20, 400), (1200, 400 + height), (255, 255, 255), cv2.FILLED)
        cv2.putText(frame, text[-80:], (30, 400 + height - 20), cv2.FONT_HERSHEY_PLAIN, 3, (0, 0, 0), 3)

        if capitalize:
            cv2.putText(frame, "CAPS ON", (1050, 50), cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 255), 2)

        cv2.imshow("Keyboard Control", frame)

        key = cv2.waitKey(1)
        if key == 27:
            cv2.destroyAllWindows()
            main_menu()
            break

if __name__ == "__main__":
    try:
        # Set up callback for voice command mode switching
        voice_manager.set_mode_switch_callback(switch_mode_callback)
        main_menu()
    finally:
        # Clean up resources
        if voice_manager.listening:
            voice_manager.stop_listening()
        cap.release()
        cv2.destroyAllWindows()