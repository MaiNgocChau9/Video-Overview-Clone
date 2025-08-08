import os
import re
from google import genai
from dotenv import load_dotenv

def sanitize_filename(name):
    """Loại bỏ ký tự không hợp lệ và giới hạn độ dài"""
    name = re.sub(r'[\\/*?:"<>|]', "_", name)
    return name.strip()[:50]

def generate(document=[], customize=""):
    load_dotenv()
    client = genai.Client(
        api_key=os.environ.get("GEMINI_API_KEY"),
    )

    model = "gemini-2.5-flash-lite"
    
    # Đọc prompt và thay [Language]
    lang = str(os.environ.get("LANGUAGE"))
    prompt_content = open("prompt_content.txt", "r", encoding="utf-8").read().replace("[Language]", lang)
    prompt_text = open("prompt_text.txt", "r", encoding="utf-8").read().replace("[Language]", lang)
    
    final_prompt = f"{customize}\n{prompt_content}\n{prompt_text}"
    contents = [final_prompt] + document
    
    try:
        response = client.models.generate_content(model=model, contents=contents)
    except Exception as e:
        print(f"[ERROR] Failed to generate text: {e}")
        return None, None

    # Lấy tên file từ AI
    try:
        name_res = client.models.generate_content(
            model=model,
            contents=[f"Give me a short and clear title for this overview in {lang}, using normal spacing between words.\nDo NOT join words together, do NOT use underscores, and do NOT add any punctuation.\nReturn ONLY the title text, nothing else:\n\n" + response.text],
        )
        raw_name = name_res.text.strip()
        safe_name = sanitize_filename(raw_name)
        file_path = f"{safe_name} Overview.txt"

        if os.path.exists(file_path):
            print(f"[WARNING] File {file_path} already exists. Renaming.")
            file_path = f"{safe_name}_1 Overview.txt"

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(response.text)

        return response.text, safe_name
    except Exception as e:
        print(f"[ERROR] Failed to name or save file: {e}")
        return response.text, "Overview"