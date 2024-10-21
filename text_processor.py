import pyperclip
import threading
import time
from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT
import os
from dotenv import load_dotenv
import sys
import keyring
from logger import default_logger
from pynput import keyboard

IS_MAC = sys.platform == "darwin"
MODIFIER_KEY = '<ctrl>'

load_dotenv()


class TextProcessor:
    def __init__(self, ui):
        self.ui = ui
        self.running = True
        self.anthropic = None
        self.update_api_key()
        self.keyboard_controller = keyboard.Controller()
        default_logger.info("TextProcessor initialized")

    def update_api_key(self):
        api_key = keyring.get_password("RewriterApp", "api_token")
        if api_key:
            self.anthropic = Anthropic(api_key=api_key)

    def release_all_modifiers(self):
        modifier_keys = [
            keyboard.Key.alt,
            keyboard.Key.alt_l,
            keyboard.Key.alt_r,
            keyboard.Key.ctrl,
            keyboard.Key.ctrl_l,
            keyboard.Key.ctrl_r,
            keyboard.Key.cmd,
            keyboard.Key.cmd_l,
            keyboard.Key.cmd_r,
            keyboard.Key.shift,
            keyboard.Key.shift_l,
            keyboard.Key.shift_r
        ]
        for key in modifier_keys:
            self.keyboard_controller.release(key)

    def get_selected_text(self):
        time.sleep(0.5)
        default_logger.info("Getting selected text")
        original_clipboard = pyperclip.paste()
        
        self.release_all_modifiers()
        
        self.keyboard_controller.press(keyboard.Key.ctrl)
        self.keyboard_controller.press('c')
        self.keyboard_controller.release('c')
        self.keyboard_controller.release(keyboard.Key.ctrl)
        
        time.sleep(0.1)
        new_clipboard = pyperclip.paste()
        print(new_clipboard)
        threading.Timer(0.0001, self.get_clipboard_content, args=(original_clipboard, new_clipboard)).start()

    def get_clipboard_content(self, original_clipboard, new_clipboard):
        if new_clipboard != original_clipboard:
            threading.Thread(target=self.process_text, args=(new_clipboard,)).start()
        else:
            print("No text selected.")
        pyperclip.copy(original_clipboard)

    def process_text(self, text):
        self.ui.queue_show_popup(text)
        corrected_text = self.correct_grammar(text)
        self.ui.queue_update_popup(corrected_text)

    def correct_grammar(self, text):
        if not self.anthropic:
            self.update_api_key()
        if not self.anthropic:
            default_logger.error("API key not set. Please update in settings.")
            return "Error: API key not set. Please update in settings."

        # Read the prompt from the file
        prompt_file_path = os.path.join(os.path.dirname(__file__), 'prompt.md')
        with open(prompt_file_path, 'r') as file:
            prompt_template = file.read()

        messages = [
            {
                "role": "user",
                "content": f"{prompt_template}\n\nText to improve:\n{text}"
            }
        ]

        try:
            response = self.anthropic.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=300,
                temperature=0.4,
                messages=messages
            )
            default_logger.info("Grammar correction completed successfully")
            return response.content[0].text.strip()
        except Exception as e:
            default_logger.error(f"Error in correct_grammar: {str(e)}")
            return text

    def paste_correction(self):
        corrected_text = self.ui.paste_and_close()
        if corrected_text:
            self.paste_text(corrected_text)

    def paste_text(self, text):
        pyperclip.copy(text)
        with self.keyboard_controller.pressed(MODIFIER_KEY):
            self.keyboard_controller.press('v')
            self.keyboard_controller.release('v')

    def stop(self):
        self.running = False