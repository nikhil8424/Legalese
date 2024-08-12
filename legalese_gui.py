import os
import time
import tkinter as tk
from tkinter import filedialog, Text, messagebox
import PyPDF2
from pdf2image import convert_from_path
from PIL import Image
import pytesseract
from deep_translator import GoogleTranslator

# Function to extract text from image using pytesseract
def extract_text_from_image(image_path, language):
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    image = Image.open(image_path)
    text = pytesseract.image_to_string(image, lang=language)
    return text

# Function to extract text from PDF using PyPDF2
def pdf_to_text(pdf_path):
    text = ''
    with open(pdf_path, 'rb') as pdf_file:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text

# Function to convert PDF to images and then extract text
def pdf_to_images_and_text(pdf_path, language):
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    images = convert_from_path(pdf_path)
    text = ""
    for image in images:
        text += pytesseract.image_to_string(image, lang=language)
    return text

# Function to handle file upload and text extraction
def extract_text(file_path, language_code):
    if file_path.lower().endswith('.pdf'):
        if language_code == "eng":
            return pdf_to_text(file_path)
        else:
            return pdf_to_images_and_text(file_path, language_code)
    elif file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
        return extract_text_from_image(file_path, language_code)
    else:
        raise ValueError("Only PDF and image files are supported.")

# Function to translate extracted text to English


def translate_to_english(text, retries=3, delay=2):
    try:
        translator = GoogleTranslator(target='en')
        
        # Split the text into smaller chunks for translation
        lines = text.split('\n')
        batch_size = 100  # Number of lines per batch
        translated_text = ""
        
        for i in range(0, len(lines), batch_size):
            batch = lines[i:i + batch_size]
            batch_text = "\n".join(batch)
            
            # Implementing retry logic
            for attempt in range(retries):
                try:
                    translated_batch = translator.translate(batch_text)
                    translated_text += translated_batch + "\n"
                    break  # If successful, break out of the retry loop
                except Exception as e:
                    if attempt < retries - 1:
                        time.sleep(delay)  # Wait before retrying
                    else:
                        return f"Failed after {retries} attempts: {e}"
        
        return translated_text.strip()
    
    except Exception as e:
        return f"An error occurred: {e}"



# Function to be called on upload button click
def upload_file():
    file_path = filedialog.askopenfilename(filetypes=[("Image files", ".png;.jpg;.jpeg"), ("PDF files", ".pdf")])
    if file_path:
        language_code = language_dict.get(language_var.get())
        if not language_code:
            messagebox.showerror("Error", "Please select a valid language.")
            return
        
        try:
            # Extract text from the selected file
            extracted_text = extract_text(file_path, language_code)
            
            # Translate the extracted text to English
            translated_text = translate_to_english(extracted_text)
            
            # Display the translated text in the upload box
            upload_box.delete(1.0, tk.END)  # Clear the box before inserting new text
            upload_box.insert(tk.END, translated_text)
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")

# Main window
root = tk.Tk()
root.title("Legalize Application")
root.geometry("1024x768")  # Set a window size similar to your desired layout
root.configure(bg="white")

# Container frame
container = tk.Frame(root, bg="white")
container.pack(expand=True, fill="both", padx=20, pady=20)

# Left pane
left_pane = tk.Frame(container, bg="white", width=300, borderwidth=1, relief="solid", padx=20, pady=20)
left_pane.pack(side="left", fill="y")

# Add content to the left pane
welcome_text = [
    ("hey buddy!!!", 16),
    ("Welcome", 42),
    ("Having trouble with legal documents? Don’t worry, we’ve got your back!", 16),
    ("The Legalese Assistance Application, developed as part of the Field Project 2024-25, is designed to revolutionize the way legal documents are managed and interpreted.", 16),
    ("Simple easy steps and your problem is solved", 16),
    ("Upload -> convert -> choose Function", 16),
    ("And there you go…..", 16),
    ("Thank us later…", 16)
]

for text, size in welcome_text:
    label = tk.Label(left_pane, text=text, font=("Arial", size), bg="white", anchor="w", justify="left", wraplength=260)
    label.pack(anchor="w", pady=5)

# Right pane
right_pane = tk.Frame(container, bg="white", width=700, padx=20, pady=20)
right_pane.pack(side="left", fill="both", expand=True)

# Title in the right pane
right_title = tk.Label(right_pane, text="Legalize Application", font=("Arial", 24), bg="white")
right_title.pack(pady=10)

# Language selection dropdown
language_var = tk.StringVar(value="English")
language_label = tk.Label(right_pane, text="Select Language:", font=("Arial", 14), bg="white")
language_label.pack(pady=5)
language_options = ["English", "Marathi", "Hindi", "Tamil"]
language_menu = tk.OptionMenu(right_pane, language_var, *language_options)
language_menu.config(font=("Arial", 14), bg="white")
language_menu.pack(pady=5)

# Language dictionary for mapping language names to Tesseract codes
language_dict = {
    "Marathi": "mar",
    "English": "eng",
    "Hindi": "hin",
    "Tamil": "tam"
}

# Upload section
upload_section = tk.Frame(right_pane, bg="white")
upload_section.pack(fill="x", pady=10)

upload_label = tk.Label(upload_section, text="Upload your File here (png, jpg, pdf)", font=("Arial", 14), bg="white")
upload_label.pack()

upload_button = tk.Button(upload_section, text="Upload", font=("Arial", 16), bg="#007bff", fg="white", 
                          padx=20, pady=10, relief="raised", command=upload_file)
upload_button.pack(pady=10)

# Labels section
labels_frame = tk.Frame(right_pane, bg="white")
labels_frame.pack(fill="x", pady=10)

buttons = ["Key Points", "Identify", "Plain Language", "Summary", "Kuch aur?"]

for btn_text in buttons:
    btn = tk.Button(labels_frame, text=btn_text, font=("Arial", 16), bg="#f8f8f8", fg="#333", relief="raised", 
                    padx=10, pady=10, cursor="hand2")
    btn.pack(side="left", expand=True, fill="x", padx=5)

# Upload box
upload_box = Text(right_pane, height=15, bg="#f0f0f0", borderwidth=1, relief="solid", wrap="word")
upload_box.pack(fill="both", expand=True, pady=10, padx=10)

root.mainloop()