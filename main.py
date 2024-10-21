import threading
import sys
from ui import RewriterApp
from text_processor import TextProcessor
from logger import default_logger, log_stream
from pynput import keyboard

IS_MAC = sys.platform == "darwin"
MODIFIER_KEY = keyboard.Key.cmd if IS_MAC else keyboard.Key.ctrl

class Rewriter:
    def __init__(self):
        self.ui = RewriterApp(log_stream)
        self.text_processor = TextProcessor(self.ui)
        self.running = True
        self.listener = None

    def setup_hotkeys(self):
        def on_activate_correction():
            self.text_processor.get_selected_text()

        def on_activate_quit():
            self.stop()

        correction_key = self.ui.settings.get("correction_hotkey", "d")
        quit_key = self.ui.settings.get("quit_hotkey", "q")

        self.listener = keyboard.GlobalHotKeys({
            f'<ctrl>+<alt>+h': on_activate_correction,
            f'<ctrl>+<alt>+q': on_activate_quit
        })
        self.listener.start()
        default_logger.info(f"Hotkeys registered: Correction: {MODIFIER_KEY}+alt+{correction_key}, Quit: {MODIFIER_KEY}+alt+{quit_key}")

    def run(self):
        default_logger.info("Starting Rewriter...")
        default_logger.info(f"Press {MODIFIER_KEY}+alt+d to rewrite text.")
        default_logger.info(f"Press {MODIFIER_KEY}+alt+q to quit the app.")
        
        self.setup_hotkeys()
        
        # Run the UI
        self.ui.run()

    def stop(self):
        self.running = False
        if self.listener:
            self.listener.stop()
        self.text_processor.stop()
        self.ui.quit_app()
        default_logger.info("Shutting down Rewriter...")
        self.ui.root.quit()  # Force quit the Tkinter root
        self.ui.root.destroy()  # Destroy the Tkinter root
        sys.exit(0)

if __name__ == "__main__":
    default_logger.info("Starting Rewriter application")
    app = Rewriter()
    app.run()