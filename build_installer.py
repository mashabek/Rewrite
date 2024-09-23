import PyInstaller.__main__
import os

# Get the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# Define the path to your main script
main_script = os.path.join(current_dir, 'main.py')

# Define additional data files to include
additional_files = [
    ('prompt.md', '.'),
    ('settings.json', '.'),
    ('ui.py', '.'),
    ('text_processor.py', '.'),
]

# Define PyInstaller arguments
pyinstaller_args = [
    '--name=RewriterApp',
    '--onefile',
    '--windowed',
    '--add-data=prompt.md:.',
    '--add-data=settings.json:.',
    '--icon=favicon.ico',  # Make sure to create an app_icon.ico file
    '--hidden-import=keyring.backends',
    main_script
]

# Add additional files to PyInstaller arguments
for src, dst in additional_files:
    pyinstaller_args.append(f'--add-data={src}:{dst}')

# Run PyInstaller
PyInstaller.__main__.run(pyinstaller_args)