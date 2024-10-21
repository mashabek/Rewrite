import customtkinter as ctk
import tkinter as tk
from PIL import Image, ImageDraw, ImageFont
from pystray import Icon, Menu, MenuItem
import threading
import pyautogui
import queue
import pyperclip
import keyboard
import json
import os
import keyring
import sys
import traceback
from logger import default_logger, log_stream
from screeninfo import get_monitors

MODIFIER_KEY = "ctrl"

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class RewriterApp:
    def __init__(self, log_stream):
        self.root = ctk.CTk()
        self.root.withdraw()
        self.popup = None
        self.icon = None
        self.settings = self.load_settings()
        self.setup_tray_icon()
        self.queue = queue.Queue()
        self.root.after(100, self.check_queue)
        self.log_stream = log_stream
        self.log_window = None
        
        # Add this line to redirect stdout to our log stream
        sys.stdout = log_stream
        
        # Set up custom Tkinter exception handler
        ctk.CTk.report_callback_exception = self.handle_tk_exception

    def handle_tk_exception(self, exc, val, tb):
        err_msg = f"Tkinter Error:\n{''.join(traceback.format_exception(exc, val, tb))}"
        default_logger.error(err_msg)
        # Optionally, you can show an error message to the user
        # tk.messagebox.showerror("Error", f"An error occurred:\n{str(val)}")

    def setup_tray_icon(self):
        image = self.create_image()
        menu = Menu(
            MenuItem('Settings', self.show_settings),
            MenuItem('About', self.show_about),
            MenuItem('Show Logs', self.show_logs),  # Add this line
            MenuItem('Quit', self.quit_app)
        )
        self.icon = Icon("Grammar Correction", image, "Grammar Correction", menu)

    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        threading.Thread(target=self.icon.run, daemon=True).start()
        try:
            self.root.mainloop()
        except Exception as e:
            default_logger.error(f"Error in main loop: {str(e)}")
            default_logger.error(traceback.format_exc())

    def check_queue(self):
        try:
            task = self.queue.get_nowait()
            if task[0] == "show_popup":
                self.show_popup(task[1])
            elif task[0] == "update_popup":
                self.update_popup(task[1])
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.check_queue)

    def show_popup(self, original_text):
        if self.popup and self.popup.winfo_exists():
            self.on_popup_close()  # Close existing popup if it exists
        
        x, y = self.position_popup()
        popup_width = 600
        initial_height = 300  # Increased from 200
        self.popup = ctk.CTkToplevel(self.root)
        self.popup.title("")
        self.popup.geometry(f"{popup_width}x{initial_height}+{x}+{y}")
        self.popup.resizable(False, False)
        self.popup.overrideredirect(True)
        
        # Add these lines to make the popup stay on top and grab focus
        self.popup.attributes('-topmost', True)
        self.popup.lift()
        self.popup.focus_force()

        # Add this line to bind the focus-out event
        self.popup.bind("<FocusOut>", lambda e: self.on_popup_close())

        frame = ctk.CTkFrame(self.popup, fg_color="#1E1E1E")
        frame.pack(fill="both", expand=True)  # Changed from place to pack

        self.progress_bar = ctk.CTkProgressBar(frame, height=2, corner_radius=0)
        self.progress_bar.pack(fill="x", padx=30, pady=(20, 0))
        self.progress_bar.set(0)
        self.progress_bar.start()

        self.status_label = ctk.CTkLabel(frame, text="Rewriting text...", font=("SF Pro Text", 14))
        self.status_label.pack(pady=(10, 0))

        self.original_text_widget = ctk.CTkTextbox(frame, font=("SF Pro Text", 14), fg_color="#2A2A2A", 
                                                   border_width=0, wrap="word", height=70)
        self.original_text_widget.pack(fill="both", expand=True, padx=30, pady=(10, 5))
        self.original_text_widget.insert("1.0", original_text)
        self.original_text_widget.configure(state="disabled")

        self.text_widget = ctk.CTkTextbox(frame, font=("SF Pro Text", 16), fg_color="#1E1E1E", 
                                          border_width=0, wrap="word", height=80)
        self.text_widget.pack(fill="both", expand=True, padx=30, pady=(5, 10))
        self.text_widget.insert("1.0", "Correcting grammar...")

        button_frame = ctk.CTkFrame(frame, fg_color="#1E1E1E")
        button_frame.pack(fill="x", padx=30, pady=(0, 15))

        cancel_btn = ctk.CTkButton(button_frame, text="Cancel", width=100, height=30, 
                                   command=self.popup.destroy, fg_color="#2E2E2E", hover_color="#3E3E3E",
                                   corner_radius=15)
        cancel_btn.pack(side="left", padx=(0, 10))

        self.paste_btn = ctk.CTkButton(button_frame, text="Paste", width=100, height=30, 
                                       command=self.paste_and_close, fg_color="#2E2E2E", hover_color="#3E3E3E",
                                       state="disabled", corner_radius=15)
        self.paste_btn.pack(side="right")

        # After setting up all widgets, adjust the height based on content
        self.adjust_popup_height(original_text)

        # Ensure the popup stays on top even after adjusting height
        self.popup.after(10, lambda: self.popup.lift())

        # Add this line at the end of the method
        #self.popup.protocol("WM_DELETE_WINDOW", self.on_popup_close)

    def on_popup_close(self):
        if self.popup:
            try:
                self.popup.destroy()
            except tk.TclError as e:
                default_logger.error(f"Error while closing popup: {e}")
            finally:
                self.popup = None

    def adjust_popup_height(self, text):
        # Calculate required height based on text length
        text_length = len(text)
        required_height = max(200, min(300, 200 + text_length // 10))  # Adjust as needed
        
        # Update popup geometry
        x = self.popup.winfo_x()
        y = self.popup.winfo_y()
        self.popup.geometry(f"600x{required_height}+{x}+{y}")

    def position_popup(self):
        mouse_x, mouse_y = pyautogui.position()
        current_monitor = self.get_current_monitor(mouse_x, mouse_y)
        
        popup_width = 600
        popup_height = 200  # Initial height, will be adjusted later
        x = current_monitor.x + (current_monitor.width - popup_width) // 2
        y = current_monitor.y + 100
        
        return x, y

    def update_popup(self, corrected_text):
        if self.popup and self.popup.winfo_exists():
            if hasattr(self, 'progress_bar') and self.progress_bar.winfo_exists():
                self.progress_bar.stop()
                self.progress_bar.set(1)
            if hasattr(self, 'status_label') and self.status_label.winfo_exists():
                self.status_label.configure(text="Text rewritten:")
            if hasattr(self, 'original_text_widget') and self.original_text_widget.winfo_exists():
                self.original_text_widget.pack_forget()
            if hasattr(self, 'text_widget') and self.text_widget.winfo_exists():
                self.text_widget.delete("1.0", "end")
                self.text_widget.insert("1.0", corrected_text)
            if hasattr(self, 'paste_btn') and self.paste_btn.winfo_exists():
                self.paste_btn.configure(state="normal")
            self.popup.bind("<Shift-Return>", lambda event: self.paste_and_close())

    def paste_and_close(self):
        if self.popup and self.popup.winfo_exists():
            text = self.text_widget.get("1.0", "end-1c")
            self.on_popup_close()
            pyperclip.copy(text)
            keyboard.press_and_release(f'{MODIFIER_KEY}+v')
            return text
        return None

    def on_closing(self):
        self.root.quit()
        self.quit_app()

    def quit_app(self):
        if self.icon:
            self.icon.stop()
        self.root.quit()

    @staticmethod
    def create_image():
        # Path to your favicon file
        favicon_path = os.path.join(os.path.dirname(__file__), 'favicon.ico')
        
        if os.path.exists(favicon_path):
            # Open the favicon file
            with Image.open(favicon_path) as img:
                # Convert to RGBA if it's not already
                img = img.convert('RGBA')
                
                # Resize to 128x128 if needed
                if img.size != (128, 128):
                    img = img.resize((128, 128), Image.LANCZOS)
                
                return img
        else:
            # Fallback to the original image creation if favicon is not found
            return RewriterApp.create_default_image()

    @staticmethod
    def create_default_image():
        # Move the original image creation code here
        width = 128
        height = 128
        background_color = (52, 152, 219)  # A nice blue color
        r_color = (255, 255, 255)  # White color for the "R"

        image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)

        # Draw a circle as the background
        draw.ellipse([0, 0, width, height], fill=background_color)

        # Draw the "R"
        font_size = 80
        font = ImageFont.truetype("arial.ttf", font_size)
        text = "R"
        left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
        text_width = right - left
        text_height = bottom - top
        position = ((width - text_width) / 2, (height - text_height) / 2 - 5)
        draw.text(position, text, font=font, fill=r_color)

        return image

    @staticmethod
    def get_current_monitor(x, y):
        monitors = get_monitors()
        for monitor in monitors:
            if (monitor.x <= x < monitor.x + monitor.width and
                monitor.y <= y < monitor.y + monitor.height):
                return monitor
        return monitors[0]

    # Add these new methods for thread-safe operations
    def queue_show_popup(self, original_text):
        self.queue.put(("show_popup", original_text))

    def queue_update_popup(self, corrected_text):
        self.queue.put(("update_popup", corrected_text))

    def show_settings(self):
        settings_window = ctk.CTkToplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("400x300")
        settings_window.resizable(False, False)

        frame = ctk.CTkFrame(settings_window)
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(frame, text="API Token:").pack(anchor="w", pady=(0, 5))
        api_token_entry = ctk.CTkEntry(frame, width=300, show="*")
        api_token_entry.pack(anchor="w", pady=(0, 10))
        api_token_entry.insert(0, keyring.get_password("RewriterApp", "api_token") or "")

        ctk.CTkLabel(frame, text="Hotkey for Rewriting:").pack(anchor="w", pady=(0, 5))
        hotkey_entry = ctk.CTkEntry(frame, width=300)
        hotkey_entry.pack(anchor="w", pady=(0, 10))
        hotkey_entry.insert(0, self.settings.get("correction_hotkey", f"{MODIFIER_KEY}+D"))

        ctk.CTkLabel(frame, text="Hotkey for Quitting:").pack(anchor="w", pady=(0, 5))
        quit_hotkey_entry = ctk.CTkEntry(frame, width=300)
        quit_hotkey_entry.pack(anchor="w", pady=(0, 10))
        quit_hotkey_entry.insert(0, self.settings.get("quit_hotkey", f"{MODIFIER_KEY}+Q"))
        def save_settings():
            keyring.set_password("RewriterApp", "api_token", api_token_entry.get())
            self.settings["correction_hotkey"] = hotkey_entry.get()
            self.settings["quit_hotkey"] = quit_hotkey_entry.get()
            self.save_settings()
            settings_window.destroy()

        save_button = ctk.CTkButton(frame, text="Save", command=save_settings)
        save_button.pack(pady=(10, 0))

    def show_about(self):
        about_window = ctk.CTkToplevel(self.root)
        about_window.title("About")
        about_window.geometry("400x300")
        about_window.resizable(False, False)

        frame = ctk.CTkFrame(about_window)
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(frame, text="Rewriter using Anthropic API").pack(pady=(0, 10))
        ctk.CTkLabel(frame, text="Version 1.0").pack(pady=(0, 10))
        ctk.CTkLabel(frame, text="Author: @mashabek").pack(pady=(0, 10))

    def show_logs(self):
        if self.log_window is None or not self.log_window.winfo_exists():
            self.log_window = ctk.CTkToplevel(self.root)
            self.log_window.title("Logs")
            self.log_window.geometry("800x600")
            self.log_window.protocol("WM_DELETE_WINDOW", self.on_log_window_close)

            frame = ctk.CTkFrame(self.log_window)
            frame.pack(fill="both", expand=True, padx=20, pady=20)

            self.log_text = ctk.CTkTextbox(frame, wrap="word", state="disabled")
            self.log_text.pack(fill="both", expand=True)

            refresh_button = ctk.CTkButton(frame, text="Refresh", command=self.refresh_logs)
            refresh_button.pack(pady=(10, 0))

        self.refresh_logs()
        self.log_window.lift()
        self.log_window.focus_force()

    def refresh_logs(self):
        if self.log_text:
            self.log_text.configure(state="normal")
            self.log_text.delete("1.0", "end")
            self.log_text.insert("end", self.log_stream.getvalue())
            self.log_text.configure(state="disabled")
            self.log_text.see("end")

    def on_log_window_close(self):
        self.log_window.destroy()
        self.log_window = None

    def load_settings(self):
        try:
            with open("settings.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def save_settings(self):
        with open("settings.json", "w") as f:
            json.dump(self.settings, f)