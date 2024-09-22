import keyboard
import pyperclip
import threading
import time
from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT
import os
from dotenv import load_dotenv
import sys
import logging
import keyring

load_dotenv()


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

IS_MAC = sys.platform == "darwin"
MODIFIER_KEY = "command" if IS_MAC else "ctrl"

class TextProcessor:
    def __init__(self, ui):
        self.ui = ui
        self.running = True
        self.anthropic = None
        self.update_api_key()

    def update_api_key(self):
        api_key = keyring.get_password("RewriterApp", "api_token")
        if api_key:
            self.anthropic = Anthropic(api_key=api_key)

    def get_selected_text(self):
        original_clipboard = pyperclip.paste()
        for i in range(5):
            keyboard.press_and_release(f'{MODIFIER_KEY}+c')
        time.sleep(0.2)
        
        threading.Timer(0.0001, self.get_clipboard_content, args=(original_clipboard,)).start()

    def get_clipboard_content(self, original_clipboard):
        selected_text = pyperclip.paste()
        if selected_text != original_clipboard:
            threading.Thread(target=self.process_text, args=(selected_text,)).start()
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
            return "Error: API key not set. Please update in settings."

        # Read the prompt from the file
        prompt_file_path = os.path.join(os.path.dirname(__file__), 'prompt.md')
        with open(prompt_file_path, 'r') as file:
            prompt_template = file.read()

        prompt = f"""
{HUMAN_PROMPT}{prompt_template}

Text to improve:
{text}

{AI_PROMPT}Improved version:"""

        try:
            completion = self.anthropic.completions.create(
                model="claude-2.1",
                max_tokens_to_sample=300,
                temperature=0.4,
                prompt=prompt
            )
            return completion.completion.strip()
        except Exception as e:
            logging.error(f"Error in correct_grammar: {str(e)}")
            return text

    def paste_correction(self):
        corrected_text = self.ui.paste_and_close()
        if corrected_text:
            self.paste_text(corrected_text)

    @staticmethod
    def paste_text(text):
        pyperclip.copy(text)
        keyboard.press_and_release(f'{MODIFIER_KEY}+v')

    def stop(self):
        self.running = False
        keyboard.unhook_all()