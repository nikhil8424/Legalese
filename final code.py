import os
import tkinter as tk
from tkinter import filedialog, Text, messagebox
import PyPDF2
from pdf2image import convert_from_path
from PIL import Image
import pytesseract
from deep_translator import GoogleTranslator
from collections import defaultdict
import re
from sumy.parsers.plaintext import PlaintextParser
from sumy.summarizers.lsa import LsaSummarizer
from sumy.nlp.tokenizers import Tokenizer
import spacy
import nltk
from nltk.corpus import wordnet
from transformers import pipeline
from collections import Counter
from textblob import TextBlob
os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'

# Download necessary NLTK data
nltk.download('punkt')
nltk.download('wordnet')
nltk.download('averaged_perceptron_tagger')

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

# Function to summarize text using Sumy
def summarize_text(text):
    parser = PlaintextParser.from_string(text, Tokenizer("english"))
    summarizer = LsaSummarizer()
    summary = summarizer(parser.document, 3)  # Adjust the number of sentences in the summary
    summary_text = "\n".join([str(sentence) for sentence in summary])
    return summary_text


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
            text += page.extract_text() or ''  # Handle None if text extraction fails
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
def translate_to_english(text):
    try:
        translator = GoogleTranslator(target='en')
        lines = text.split('\n')
        batch_size = 100
        translated_text = ""
        for i in range(0, len(lines), batch_size):
            batch = lines[i:i + batch_size]
            batch_text = "\n".join(batch)
            translated_batch = translator.translate(batch_text)
            translated_text += translated_batch + "\n"
        return translated_text.strip()
    except Exception as e:
        return f"An error occurred: {e}"

# Function to extract laws and sections from the text
def extract_laws_and_sections(text):
    pattern = re.compile(r'\bSection\s+\d+\b', re.IGNORECASE)
    sections = pattern.findall(text)
    return sections

# Function to identify document type and extract sections
def identify_document_type(text):
    text = text.lower()
    keyword_counts = defaultdict(int)
    for doc_type, keywords in legal_keywords.items():
        for keyword in keywords:
            if keyword.lower() in text:
                keyword_counts[doc_type] += 1
    
    sections = extract_laws_and_sections(text)
    
    if keyword_counts:
        max_type = max(keyword_counts, key=keyword_counts.get)
        return max_type, sections, keyword_counts
    else:
        return 'Unknown Document Type', sections, keyword_counts

# Function to handle identifying document type and keyword count
def identify_document():
    if not upload_box.get(1.0, tk.END).strip():
        messagebox.showwarning("No Text", "Please upload and extract text from a file first.")
        return
    
    doc_type, sections, keyword_counts = identify_document_type(upload_box.get(1.0, tk.END))
    sections_text = "\n".join(sections) if sections else "No sections found."
    
    # Create a detailed keyword count message
    keyword_count_details = "\n".join([f"{keyword}: {count}" for keyword, count in keyword_counts.items()])
    result_message = (f"The document type is: {doc_type}\n\n"
                      f"Sections Found:\n{sections_text}\n\n"
                      f"Keyword Counts:\n{keyword_count_details}")
    
    messagebox.showinfo("Document Type and Sections", result_message)

# Function to handle file upload and text extraction
def upload_file():
    file_path = filedialog.askopenfilename(filetypes=[("Image files", ".png;.jpg;.jpeg"), ("PDF files", ".pdf")])
    if file_path:
        language_code = language_dict.get(language_var.get())
        if not language_code:
            messagebox.showerror("Error", "Please select a valid language.")
            return
        
        try:
            extracted_text = extract_text(file_path, language_code)
            translated_text = translate_to_english(extracted_text)
            upload_box.delete(1.0, tk.END)
            upload_box.insert(tk.END, translated_text)
            identify_button.config(state=tk.NORMAL)  # Enable the "Identify Document Type" button
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")

# Legal keywords dictionary
legal_keywords = {
    'Contract': ['Payment Terms', 'Confidentiality', 'Agreement', 'Breach', 'Term', 'Consideration', 'Covenant', 'Obligations', 'Execution', 'Termination'],
    'Non-Disclosure Agreement': ['Confidentiality', 'Non-Disclosure', 'Proprietary Information', 'Trade Secrets', 'Disclosure', 'Recipient', 'Restricted', 'Confidential Information'],
    'Lease Agreement': ['Lease Term', 'Rent', 'Landlord', 'Tenant', 'Deposit', 'Premises', 'Maintenance', 'Utilities', 'Renewal', 'Termination'],
    'Employment Contract': ['Employment', 'Salary', 'Benefits', 'Job Title', 'Termination', 'Probation', 'Non-Compete', 'Work Hours', 'Duties', 'Confidentiality'],
    'Partnership Agreement': ['Partnership', 'Profit Sharing', 'Responsibilities', 'Contributions', 'Duties', 'Liabilities', 'Term', 'Dispute Resolution', 'Dissolution'],
    'Loan Agreement': ['Loan Amount', 'Interest Rate', 'Repayment Terms', 'Collateral', 'Default', 'Lender', 'Borrower', 'Principal', 'Amortization', 'Term'],
    'Service Agreement': ['Services', 'Deliverables', 'Scope of Work', 'Compensation', 'Performance', 'Terms', 'Termination', 'Liability', 'Indemnification', 'Warranties'],
    'Settlement Agreement': ['Settlement', 'Claims', 'Dispute', 'Compensation', 'Release', 'Terms', 'Agreement', 'Confidentiality', 'Payment', 'Resolution'],
    'Privacy Policy': ['Personal Data', 'Privacy', 'Data Collection', 'Usage', 'Disclosure', 'Security', 'Rights', 'Cookies', 'Third Parties', 'Compliance'],
    'Power of Attorney': ['Authority', 'Agent', 'Principal', 'Powers', 'Representation', 'Decision-Making', 'Legal', 'Termination', 'Revocation', 'Duties'],
    'Criminal Case': ['Defendant', 'Plaintiff', 'Charges', 'Evidence', 'Trial', 'Verdict', 'Prosecution', 'Defense', 'Sentencing', 'Appeal'],
    'Civil Case': ['Plaintiff', 'Defendant', 'Complaint', 'Evidence', 'Trial', 'Judgment', 'Settlement', 'Damages', 'Appeal', 'Liability'],
    'Divorce Case': ['Petitioner', 'Respondent', 'Custody', 'Alimony', 'Division of Assets', 'Settlement', 'Support', 'Visitation', 'Child Support', 'Dissolution'],
    'Property Case': ['Plaintiff', 'Defendant', 'Property Title', 'Lease', 'Possession', 'Easement', 'Boundary', 'Transfer', 'Sale', 'Ownership'],
    'Intellectual Property': ['Patent', 'Trademark', 'Copyright', 'Infringement', 'Licensing', 'Royalty', 'Patent Application', 'Trademark Registration', 'Creative Works', 'Protection'],
    'Bankruptcy': ['Debtor', 'Creditor', 'Filing', 'Discharge', 'Repayment Plan', 'Trustee', 'Chapter 7', 'Chapter 11', 'Chapter 13', 'Liquidation'],
    'Family Law': ['Custody', 'Support', 'Adoption', 'Guardianship', 'Marriage', 'Divorce', 'Paternity', 'Child Welfare', 'Protective Orders', 'Family Mediation'],
    'Immigration': ['Visa', 'Residency', 'Citizenship', 'Deportation', 'Green Card', 'Asylum', 'Work Permit', 'Naturalization', 'Immigration Status', 'Application'],
    'Contract Dispute': ['Breach', 'Enforcement', 'Remedies', 'Damages', 'Settlement', 'Negotiation', 'Contract Terms', 'Performance', 'Dispute Resolution', 'Mediation'],
    'Insurance Claim': ['Policy', 'Claim', 'Coverage', 'Exclusions', 'Premiums', 'Deductibles', 'Settlement', 'Claim Denial', 'Evidence', 'Payout'],
    'Traffic Violation': ['Citation', 'Ticket', 'Fine', 'Court Appearance', 'Violation', 'Penalty', 'Evidence', 'Defendant', 'Judge', 'Appeal'],
}

def extract_dates(text):
    date_patterns = [
        r"(?:January|February|March|April|May|June|July|August|September|October|November|December)[\s\n]*\d{1,2},[\s\n]*\d{4}",
        r"\d{1,2}[\s\n]*(?:January|February|March|April|May|June|July|August|September|October|November|December)[,\s\n]*\d{4}",
        r"\d{4}[-/]\d{2}[-/]\d{2}",
        r"\d{1,2}[-/]\d{2}[-/]\d{4}",
        r"\d{2}[-/]\d{2}[-/]\d{4}",
        r"\d{1,2}[\s\n]*(?:January|February|March|April|May|June|July|August|September|October|November|December)[\s\n]*\d{4}",
    ]
    
    dates_found = set()
    for pattern in date_patterns:
        dates_found.update(match.group() for match in re.finditer(pattern, text))

    return list(dates_found)

def extract_organization_names(text):
    organization_suffixes = [
        r"Pvt\.? Ltd\.?", r"Ltd\.?", r"LLP", r"LP", r"PA", r"PC", r"NPO", r"NGO", r"Foundation", r"Properties",
        r"Co-op", r"Cooperative Society", r"Trust", r"Section 8 Company", r"Inc\.?", r"Corp\.?", r"LLC", r"PLC",
        r"GmbH", r"S\.A\.", r"S\.R\.L\.", r"A\.G\.", r"KGaA"
    ]

    organization_pattern = r"\b[A-Z][A-Za-z\s&'-]*?\b(?:\s(?:'|\b[A-Z][A-Za-z\s&'-]+?\b))*(?:" + "|".join(organization_suffixes) + r")\b"
    
    cleaned_text = clean_text(text)
    
    organizations = set()
    for match in re.finditer(organization_pattern, cleaned_text):
        org_name = match.group().strip()
        if len(org_name.split()) <= 6 and not re.search(r'\b(?:dispute|arising|relating|agreement|binding|arbitration|rules|association|remainder|document|omitted|brevity|terms|ownership|website|code|warranty|defects|limitations|liability|witness|whereof|parties|executed|date|first|written|above|inc)\b', org_name, re.IGNORECASE):
            organizations.add(org_name)
    
    return list(organizations)

def extract_city_names(text, MAHARASHTRA_CITIES):
    city_pattern = r'\b(?:' + '|'.join(re.escape(city) for city in MAHARASHTRA_CITIES) + r')\b'
    cities_found = set()
    
    cleaned_text = clean_text(text)
    
    for match in re.finditer(city_pattern, cleaned_text, re.IGNORECASE):
        city_name = match.group().strip()
        if city_name in MAHARASHTRA_CITIES and len(city_name) > 1:
            cities_found.add(city_name)
    
    return list(cities_found)

def extract_names(text):
    doc = nlp(text)
    filtered_names = set()  # Use a set to avoid duplicates

    # Extract names using NER
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            name = ent.text.strip()
            # Normalize and clean names
            normalized_name = ' '.join(name.split())
            if len(normalized_name.split()) > 1 and not re.match(r'\b(?:This|Witness|Whereof|Sealed|Witnesseth|Principal|a|b|c|d)\b', normalized_name):
                filtered_names.add(normalized_name)

    # Convert set to list
    filtered_names = list(filtered_names)
    
    # Additional cleaning to remove unusual cases
    filtered_names = [name for name in filtered_names if re.match(r'^[A-Za-z\s]+$', name)]

    return filtered_names

def key_points():
     if not upload_box.get(1.0, tk.END).strip():
        messagebox.showwarning("No Text", "Please upload and extract text from a file first.")
        return

     extracted_text = upload_box.get(1.0, tk.END)
    
     dates = extract_dates(extracted_text)
     organizations = extract_organization_names(extracted_text)
     city_names = extract_city_names(extracted_text, MAHARASHTRA_CITIES)
     names = extract_names(extracted_text)

     # Create detailed messages for each extracted item
     dates_text = "\n".join([f"{i}. Date: {date}" for i, date in enumerate(dates, start=1)]) if dates else "No dates found."
     organizations_text = "\n".join([f"{i}. Organization: {org}" for i, org in enumerate(organizations, start=1)]) if organizations else "No organization names found."
     cities_text = "\n".join([f"{i}. Location: {city}" for i, city in enumerate(city_names, start=1)]) if city_names else "No city names found."
     names_text = "\n".join([f"{i}. Name: {name}" for i, name in enumerate(names, start=1)]) if names else "No human names found."

     # Combine all results into a single message
     result_message = (f"Dates Extracted:\n{dates_text}\n\n"
                      f"Organization Names Extracted:\n{organizations_text}\n\n"
                      f"City Names Extracted:\n{cities_text}\n\n"
                      f"People Involved:\n{names_text}")

     # Show the result in a message box
     messagebox.showinfo("Extracted Information", result_message)

def clean_text(text):
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)  # Remove punctuation
    return text
    
    
MAHARASHTRA_CITIES = [
   "Visakhapatnam", "Vijayawada", "Guntur", "Tirupati", "Kakinada", "Rajahmundry", "Nellore", "Delhi",
        "Anantapur", "Kadapa", "Chittoor", "Eluru", "Srikakulam", "Prakasam", "Kurnool", 
        "Vijayanagaram", "Bhimavaram", "Machilipatnam", "Palnadu", "Narsipatnam", "Tanuku", 
        "Yemmiganur", "Tadipatri", "Jammalamadugu", "Peddaganjam", "Araku Valley",
        "Itanagar", "Tawang", "Bomdila", "Ziro", "Naharlagun", "Pasighat", "Roing", "Changlang", 
        "Tezu", "Daporijo",
        "Guwahati", "Dibrugarh", "Silchar", "Jorhat", "Nagaon", "Tezpur", "Haflong", "Karimganj", 
        "Barpeta", "Dhemaji", "Bongaigaon", "Sonitpur", "Sivasagar", "Golaghat", "Cachar", 
        "Kokrajhar", "Lakhimpur", "Nalbari", "Darrang", "Kamrup", "Dhubri",
        "Patna", "Gaya", "Bhagalpur", "Muzaffarpur", "Darbhanga", "Munger", "Purnia", "Arrah", 
        "Siwan", "Sasaram", "Nalanda", "Katihar", "Begusarai", "Jehanabad", "Samastipur", "Chhapra", 
        "Buxar", "Kishanganj", "Madhubani", "Saran", "Gopalganj", "Bettiah",
        "Raipur", "Bilaspur", "Korba", "Durg", "Jagdalpur", "Raigarh", "Ambikapur", "Rajnandgaon", 
        "Janjgir-Champa", "Kanker", "Dhamtari", "Bemetara", "Kabirdham", "Baloda Bazar", "Gariaband", 
        "Surguja", "Mungeli", "Sukma", "Bijapur", "Balrampur",
        "Panaji", "Margao", "Vasco da Gama", "Mapusa", "Ponda", "Quepem", "Cortalim", "Bicholim", 
        "Sanquelim", "Pernem", "Canacona", "Sanguem", "Kankon",
        "Ahmedabad", "Surat", "Vadodara", "Rajkot", "Junagadh", "Bhavnagar", "Gandhinagar", 
        "Anand", "Nadiad", "Mehsana", "Vapi", "Navsari", "Amreli", "Porbandar", "Kutch", "Patan", 
        "Jamnagar", "Bharuch", "Valsad", "Gir Somnath", "Dahod", "Surendranagar", "Aravalli", 
        "Kheda", "Mahesana", "Sabarkantha", "Palitana", "Modasa", "Narmada",
        "Faridabad", "Gurgaon", "Hisar", "Rohtak", "Ambala", "Karnal", "Panipat", "Yamunanagar", 
        "Jind", "Sirsa", "Kurukshetra", "Panchkula", "Mahendragarh", "Bhiwani", "Fatehabad", 
        "Rewari", "Nuh", "Palwal", "Kaithal", "Pehowa", "Tosham", "Hansi",
        "Shimla", "Manali", "Dharamshala", "Kullu", "Solan", "Hamirpur", "Mandi", "Kangra", 
        "Bilaspur", "Una", "Nahan", "Chamba", "Palampur", "Sundernagar",
        "Srinagar", "Jammu", "Udhampur", "Rajouri", "Kathua", "Anantnag", "Pulwama", "Baramulla", 
        "Kargil", "Leh", "Samba", "Doda", "Reasi", "Poonch", "Kupwara", "Bandipora",
        "Ranchi", "Jamshedpur", "Dhanbad", "Hazaribagh", "Giridih", "Bokaro", "Deoghar", 
        "Chaibasa", "Medininagar", "Koderma", "Daltonganj", "Jhumri Telaiya", "Raghubar Nagar", 
        "Ramgarh", "Jamtara", "Pakur", "Godda", "Sahebganj", "Dumka", "Palamu", "Giridih", 
        "Hazaribagh",
        "Bengaluru", "Mysuru", "Hubli", "Dharwad", "Mangalore", "Belgaum", "Shimoga", "Tumkur", 
        "Chitradurga", "Kolar", "Udupi", "Hassan", "Bagalkot", "Bijapur", "Bidar", "Raichur", 
        "Bellary", "Gulbarga", "Devadurga", "Yadgir", "Chikkamagalur", "Chikkaballapur", 
        "Mandya", "Haveri", "Kodagu", "Karwar", "Davangere", "Puttur", "Sagara", "Bantwal", 
        "Koppal", "Hospet", "Gadag", "Haveri", "Srinivaspur",
        "Thiruvananthapuram", "Kochi", "Kozhikode", "Kannur", "Palakkad", "Alappuzha", 
        "Malappuram", "Kottayam", "Idukki", "Ernakulam", "Wayanad", "Pathanamthitta", 
        "Kasaragod", "Ponnani", "Perinthalmanna", "Thrissur", "Changanassery", "Muvattupuzha", 
        "Attingal", "Varkala", "Sreekariyam",
        "Bhopal", "Indore", "Gwalior", "Jabalpur", "Ujjain", "Sagar", "Satna", "Rewa", 
        "Ratlam", "Burhanpur", "Dewas", "Khargone", "Hoshangabad", "Shivpuri", "Mandsaur", 
        "Chhindwara", "Datiya", "Tikamgarh", "Ujjain", "Sehore", "Betul", "Jhabua", "Agar Malwa", 
        "Shahdol", "Anuppur", "Pachmarhi", "Khandwa",
        "Mumbai", "Pune", "Nagpur", "Aurangabad", "Nashik", "Thane", "Kolhapur", "Solapur", 
        "Amravati", "Jalgaon", "Latur", "Satara", "Ratnagiri", "Sindhudurg", "Raigad", "Palghar", 
        "Wardha", "Buldhana", "Akola", "Washim", "Yavatmal", "Osmanabad", "Jalna", "Parbhani", 
        "Beed", "Nanded", "Hingoli", "Dhule", "Jalgaon", "Nashik",
        "Imphal", "Shillong", "Aizawl", "Kohima", "Agartala", "Itanagar", "Dimapur", 
        "Lunglei", "Tura", "Churachandpur", "Silchar", "Kohima", "Mon", "Wokha",
        "Guwahati", "Silchar", "Dibrugarh", "Tezpur", "Jorhat", "Nagaon", "Karimganj", 
        "Hailakandi", "Kokrajhar", "Bongaigaon", "Dhemaji", "Golaghat", "Sivasagar", 
        "Barpeta", "Dhubri", "Nalbari", "Kamrup", "Kokrajhar", "Sonitpur", "Lakhimpur", 
        "Cachar", "Darrang", "Mikir Hills",
        "Lucknow", "Kanpur", "Agra", "Varanasi", "Allahabad", "Meerut", "Ghaziabad", "Noida", 
        "Aligarh", "Bareilly", "Mathura", "Moradabad", "Saharanpur", "Faizabad", "Ambedkar Nagar", 
        "Sultanpur", "Rae Bareli", "Etawah", "Mainpuri", "Unnao", "Mau", "Basti", "Jaunpur", 
        "Deoria", "Gorakhpur", "Firozabad", "Shahjahanpur", "Rampur", "Azamgarh", "Ballia", 
        "Bahraich", "Sitapur", "Hardoi", "Lakhimpur Kheri", "Gonda", "Siddharth Nagar", "Pilibhit",
        "Dehradun", "Haridwar", "Nainital", "Mussoorie", "Roorkee", "Haldwani", "Rudrapur", 
        "Kashipur", "Rishikesh", "Pauri", "Almora", "Bageshwar", "Champawat", "Uttarkashi", 
        "Tehri", "Pithoragarh", "Udham Singh Nagar",
        "Kolkata", "Howrah", "Darjeeling", "Siliguri", "Asansol", "Durgapur", "Kalyani", 
        "Bankura", "Murarai", "Haldia", "Malda", "Bardhaman", "Jamshedpur", "Durgapur", 
        "Purulia", "Krishnanagar", "Bongaigaon", "Jalpaiguri", "Midnapore", "Cooch Behar", 
        "Alipurduar"
]

#function to convert legal language into simple english language
class TextSimplifier:
    def __init__(self):
        self.pos_map = {'NOUN': 'n', 'VERB': 'v', 'ADJ': 'a', 'ADV': 'r'}

        try:
            self.paraphraser = pipeline("text2text-generation", model="t5-small")
            print("Model initialized successfully.")
        except Exception as e:
            print(f"Error initializing model: {e}")

    def find_simple_synonym(self, word, pos_tag):
        synonyms = wordnet.synsets(word)
        if synonyms:
            filtered_synonyms = [lemma.name().replace('_', ' ') for syn in synonyms 
                                 for lemma in syn.lemmas() if syn.pos() == self.pos_map.get(pos_tag, 'n')]
            if filtered_synonyms:
                common_synonym = Counter(filtered_synonyms).most_common(1)[0][0]
                return common_synonym
        return word

    def paraphrase_sentence(self, sentence):
        try:
            paraphrased = self.paraphraser(sentence, max_length=100, num_return_sequences=1)
            return paraphrased[0]['generated_text']
        except Exception as e:
            print(f"Paraphrasing error: {e}")
            return sentence

    def simplify_sentence(self, sentence):
        simplified_sentence = []
        for token in sentence:
            pos_tag = token.pos_
            if pos_tag in ['NOUN', 'VERB', 'ADJ', 'ADV']:
                simplified_word = self.find_simple_synonym(token.text, pos_tag)
                simplified_sentence.append(simplified_word)
            else:
                simplified_sentence.append(token.text)
        return ' '.join(simplified_sentence)

    def simplify_text(self, text):
        doc = nlp(text)
        simplified_sentences = []

        for sentence in doc.sents:
            simplified_sentence = self.simplify_sentence(sentence)
            simplified_text = self.paraphrase_sentence(simplified_sentence)
            simplified_sentences.append(simplified_text)

        return ' '.join(simplified_sentences)
    
def simplify_analyze_text(legal_text):
    # Simplify the legal text
    simplifier = TextSimplifier()
    simplified_text = simplifier.simplify_text(legal_text)
    
    # Return the results
    return simplified_text

#function to display the messagebox on click  
def on_button_click():
    # Get input from the user
    legal_text = upload_box.get("1.0", tk.END)
    
    # Call the combined function
    simplified_text = simplify_analyze_text(legal_text)
    
    # Display the results
    result_message = (
        f"Simplified Text: {simplified_text}\n\n"
    )
    messagebox.showinfo("Analysis Result", result_message)

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

# Function to generate summary
def generate_summary():
    if not upload_box.get(1.0, tk.END).strip():
        messagebox.showwarning("No Text", "Please upload and extract text from a file first.")
        return
    
    summary = summarize_text(upload_box.get(1.0, tk.END))
    if summary:
        messagebox.showinfo("Summary", summary)
    else:
        messagebox.showinfo("Summary", "No summary available.")

# Define the identify_button here
identify_button = tk.Button(labels_frame, text="Identify", font=("Arial", 16), bg="#f8f8f8", fg="#333", relief="raised", 
                            padx=10, pady=10, cursor="hand2", command=identify_document)
identify_button.pack(side="left", expand=True, fill="x", padx=5)

keypoints_button = tk.Button(labels_frame, text="Key Points", font=("Arial", 16), bg="#f8f8f8", fg="#333", relief="raised", 
                         padx=10, pady=10, cursor="hand2", command=key_points)
keypoints_button.pack(side="left", expand=True, fill="x", padx=5)

#define the lang conversion button here
plain_lang_btn = tk.Button(labels_frame, text="Plain Language", font=("Arial", 16), bg="#f8f8f8", fg="#333", relief="raised", 
                         padx=10, pady=10, cursor="hand2", command=on_button_click)
plain_lang_btn.pack(side="left", expand=True, fill="x", padx=5)


buttons = ["Summary", "Kuch aur?"]

for btn_text in buttons:
    if btn_text == "Identify":
        continue  # Skip the 'Identify' button here, as it's already defined separately
    elif btn_text == "Summary":
        btn = tk.Button(labels_frame, text=btn_text, font=("Arial", 16), bg="#f8f8f8", fg="#333", relief="raised", 
                        padx=10, pady=10, cursor="hand2", command=generate_summary)
    else:
        btn = tk.Button(labels_frame, text=btn_text, font=("Arial", 16), bg="#f8f8f8", fg="#333", relief="raised", 
                        padx=10, pady=10, cursor="hand2")
    btn.pack(side="left", expand=True, fill="x", padx=5)


# Upload box
upload_box = Text(right_pane, height=15, bg="#f0f0f0", borderwidth=1, relief="solid", wrap="word")
upload_box.pack(fill="both", expand=True, pady=10, padx=10)

root.mainloop()
