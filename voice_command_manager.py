import speech_recognition as sr
import threading
import time
import pyautogui
import subprocess
import webbrowser
import sys
import os

class VoiceCommandManager:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.listening = False
        self.status_message = ""
        self.command_thread = None
        self.continue_listening = False
        
        # Voice command mappings
        self.commands = {
            # System controls
            "scroll up": self.scroll_up,
            "scroll down": self.scroll_down,
            "volume up": self.volume_up,
            "volume down": self.volume_down,
            "mute": self.mute_audio,
            "screenshot": self.take_screenshot,
            
            # Application controls
            "open browser": self.open_browser,
            "open notepad": self.open_notepad,
            "close window": self.close_current_window,
            
            # Browser specific
            "search for": self.search_web,
            "go back": self.browser_back,
            "refresh page": self.refresh_page,
            
            # Mode switching
            "switch to mouse": self.switch_to_mouse_mode,
            "switch to keyboard": self.switch_to_keyboard_mode,
            
            # System commands
            "lock computer": self.lock_computer,
            "sleep computer": self.sleep_computer
        }
        
        # Command callback function for mode switching
        self.mode_switch_callback = None
        
    def set_mode_switch_callback(self, callback):
        """Set callback function for mode switching"""
        self.mode_switch_callback = callback
        
    def start_listening(self):
        """Start the voice command listener in a separate thread"""
        if not self.listening:
            self.listening = True
            self.continue_listening = True
            self.status_message = "Voice commands activated"
            self.command_thread = threading.Thread(target=self._listen_for_commands)
            self.command_thread.daemon = True
            self.command_thread.start()
    
    def stop_listening(self):
        """Stop the voice command listener"""
        self.continue_listening = False
        self.status_message = "Voice commands deactivated"
        if self.command_thread:
            self.command_thread.join(timeout=1)
        self.listening = False
    
    def _listen_for_commands(self):
        """Background thread function to continuously listen for commands"""
        with sr.Microphone() as source:
            # Adjust for ambient noise once at the beginning
            self.status_message = "Adjusting for ambient noise..."
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            
            while self.continue_listening:
                try:
                    self.status_message = "Listening for commands..."
                    audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=5)
                    self.status_message = "Processing command..."
                    
                    # Use Google's speech recognition
                    text = self.recognizer.recognize_google(audio).lower()
                    self.status_message = f"Heard: {text}"
                    print(f"Command heard: {text}")
                    
                    # Check for direct command matches
                    command_executed = False
                    for command, action in self.commands.items():
                        if command in text:
                            # For commands that need parameters (like "search for")
                            if command == "search for" and command in text:
                                query = text.split("search for", 1)[1].strip()
                                if query:
                                    action(query)
                                    command_executed = True
                            else:
                                action()
                                command_executed = True
                    
                    if not command_executed:
                        self.status_message = "Command not recognized"
                    
                    time.sleep(0.5)  # Small delay to prevent processing the same command multiple times
                    
                except sr.WaitTimeoutError:
                    self.status_message = "Listening..."
                except sr.UnknownValueError:
                    self.status_message = "Could not understand audio"
                except sr.RequestError:
                    self.status_message = "Could not request results"
                except Exception as e:
                    self.status_message = f"Error: {str(e)}"
                
                time.sleep(0.1)  # Small delay to prevent high CPU usage
    
    # Command action methods
    def scroll_up(self):
        pyautogui.scroll(300)
        self.status_message = "Scrolled up"
    
    def scroll_down(self):
        pyautogui.scroll(-300)
        self.status_message = "Scrolled down"
    
    def volume_up(self):
        for _ in range(3):  # Press the volume up key 3 times
            pyautogui.press('volumeup')
        self.status_message = "Volume increased"
    
    def volume_down(self):
        for _ in range(3):  # Press the volume down key 3 times
            pyautogui.press('volumedown')
        self.status_message = "Volume decreased"
    
    def mute_audio(self):
        pyautogui.press('volumemute')
        self.status_message = "Audio muted/unmuted"
    
    def take_screenshot(self):
        screenshot_path = os.path.join(os.path.expanduser("~"), "Pictures", f"screenshot_{int(time.time())}.png")
        pyautogui.screenshot(screenshot_path)
        self.status_message = f"Screenshot saved"
    
    def open_browser(self):
        try:
            if sys.platform == 'win32':
                webbrowser.get('windows-default').open('https://www.google.com')
            else:
                webbrowser.open('https://www.google.com')
            self.status_message = "Browser opened"
        except Exception as e:
            self.status_message = f"Could not open browser: {str(e)}"
    
    def open_notepad(self):
        try:
            if sys.platform == 'win32':
                subprocess.Popen(['notepad.exe'])
            elif sys.platform == 'darwin':  # macOS
                subprocess.Popen(['open', '-a', 'TextEdit'])
            else:  # Linux
                subprocess.Popen(['gedit'])
            self.status_message = "Notepad opened"
        except Exception as e:
            self.status_message = f"Could not open notepad: {str(e)}"
    
    def close_current_window(self):
        if sys.platform == 'win32':
            pyautogui.hotkey('alt', 'f4')
        else:
            pyautogui.hotkey('command', 'w')  # For macOS
        self.status_message = "Window closed"
    
    def search_web(self, query):
        # Open a web browser with the search query
        safe_query = query.replace(' ', '+')
        try:
            webbrowser.open(f'https://www.google.com/search?q={safe_query}')
            self.status_message = f"Searching for: {query}"
        except Exception as e:
            self.status_message = f"Search failed: {str(e)}"
    
    def browser_back(self):
        pyautogui.hotkey('alt', 'left')  # Works in most browsers
        self.status_message = "Navigated back"
    
    def refresh_page(self):
        pyautogui.press('f5')
        self.status_message = "Page refreshed"
    
    def switch_to_mouse_mode(self):
        if self.mode_switch_callback:
            self.mode_switch_callback("mouse")
        self.status_message = "Switching to mouse mode"
    
    def switch_to_keyboard_mode(self):
        if self.mode_switch_callback:
            self.mode_switch_callback("keyboard")
        self.status_message = "Switching to keyboard mode"
    
    def lock_computer(self):
        if sys.platform == 'win32':
            os.system('rundll32.exe user32.dll,LockWorkStation')
        elif sys.platform == 'darwin':  # macOS
            subprocess.call(['pmset', 'displaysleepnow'])
        else:  # Linux
            os.system('gnome-screensaver-command --lock')
        self.status_message = "Computer locked"
    
    def sleep_computer(self):
        if sys.platform == 'win32':
            os.system('rundll32.exe powrprof.dll,SetSuspendState 0,1,0')
        elif sys.platform == 'darwin':  # macOS
            os.system('pmset sleepnow')
        else:  # Linux
            os.system('systemctl suspend')
        self.status_message = "Computer sleeping"