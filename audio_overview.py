from generate_audio import generate as generate_audio
from generate_text import generate as generate_text
from dotenv import load_dotenv
from google import genai
import os

load_dotenv()

def ask_yes_no(message):
    ans = input(message).strip().lower()
    return ans == "yes"

print("===== Audio Overview Generation =====")
print("WARNING: If you're using Google's Gemini API on the *free plan*, your content *might* be used to help improve their models.\n"
      "If you prefer not to share your content, use another API or service.\n")
if not ask_yes_no("Do you want to continue? (yes/no): "):
    print("Exiting the program as per user request.")
    exit()

# Nhập phần tùy chỉnh
customize_text = input("Enter customization text (optional): ").strip()
customize_audio = input("Enter customization audio (optional): ").strip()
print(f"[DEBUG] Customize Text: {customize_text}")
print(f"[DEBUG] Customize Audio: {customize_audio}")

print("Uploading files...")
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
documents = [os.path.join("sources", f) for f in os.listdir("sources") if os.path.isfile(os.path.join("sources", f))]
uploaded_documents = []

for document in documents:
    try:
        uploaded_doc = client.files.upload(file=document)
        uploaded_documents.append(uploaded_doc)
        print(f"[UPLOAD] {document} uploaded successfully.")
    except Exception as e:
        print(f"[ERROR] Failed to upload {document}: {e}")

if not uploaded_documents:
    print("[ERROR] No documents were uploaded. Exiting.")
    exit()

# Generate text overview
text_overview, name = generate_text(uploaded_documents, customize_text)
if not text_overview or not name:
    print("[ERROR] Failed to generate text overview.")
    exit()
print(f"[SUCCESS] Text overview generated successfully. File name: {name} Overview.txt")

# Generate audio overview
audio_file = generate_audio(text_overview, customize_audio, name)
if audio_file:
    print(f"[SUCCESS] Audio overview saved as {audio_file}")
else:
    print("[ERROR] Failed to generate audio.")