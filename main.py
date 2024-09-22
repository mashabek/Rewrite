import keyboard
import threading
import time
import sys
from ui import RewriterApp
from text_processor import TextProcessor

IS_MAC = sys.platform == "darwin"
MODIFIER_KEY = "command" if IS_MAC else "ctrl"

class Rewriter:
    def __init__(self):
        self.ui = RewriterApp()
        self.text_processor = TextProcessor(self.ui)
        self.running = True

    def register_hotkeys(self):
        while self.running:
            try:
                correction_hotkey = self.ui.settings.get("correction_hotkey", f"{MODIFIER_KEY}+D")
                quit_hotkey = self.ui.settings.get("quit_hotkey", f"{MODIFIER_KEY}+Q")
                keyboard.add_hotkey(correction_hotkey, self.text_processor.get_selected_text)
                keyboard.add_hotkey(quit_hotkey, self.stop)
                print("Hotkeys registered")
                break
            except keyboard.InvalidKeyError:
                print("Failed to register hotkeys. Retrying in 1 second...")
                time.sleep(1)

    def run(self):
        print("Starting Rewriter...")
        print(f"Press {MODIFIER_KEY}+d to rewrite text.")
        print(f"Press {MODIFIER_KEY}+q to quit the app.")
        
        # Register hotkeys in a separate thread
        hotkey_thread = threading.Thread(target=self.register_hotkeys)
        hotkey_thread.daemon = True
        hotkey_thread.start()
        
        # Run the UI
        self.ui.run()

    def stop(self):
        self.running = False
        self.text_processor.stop()
        self.ui.quit_app()
        print("Shutting down Rewriter...")
        keyboard.unhook_all()  # Remove all keyboard hooks
        self.ui.root.quit()  # Force quit the Tkinter root
        self.ui.root.destroy()  # Destroy the Tkinter root
        sys.exit(0)

if __name__ == "__main__":
    app = Rewriter()
    app.run()