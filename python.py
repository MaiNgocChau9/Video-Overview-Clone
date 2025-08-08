import os
import random
import colorsys
from PIL import Image, ImageDraw, ImageFont
import textwrap

# ==============================================================================
# --- HÀM TIỆN ÍCH ---
# ==============================================================================

def hsl_to_rgb(h, s, l):
    r, g, b = colorsys.hls_to_rgb(h / 360.0, l / 100.0, s / 100.0)
    return int(r * 255), int(g * 255), int(b * 255)

def get_next_filename(output_dir):
    try:
        existing_files = [f for f in os.listdir(output_dir) if f.lower().endswith('.png')]
        existing_numbers = [int(os.path.splitext(f)[0]) for f in existing_files if os.path.splitext(f)[0].isdigit()]
        if not existing_numbers:
            return os.path.join(output_dir, "1.png")
        else:
            next_number = max(existing_numbers) + 1
            return os.path.join(output_dir, f"{next_number}.png")
    except FileNotFoundError:
        return os.path.join(output_dir, "1.png")

def load_font(font_dir, font_name, size):
    try:
        font_path = os.path.join(font_dir, font_name)
        return ImageFont.truetype(font_path, size=size)
    except (FileNotFoundError, OSError):
        print(f"⚠️ Không tìm thấy font '{font_name}', dùng font mặc định.")
        return ImageFont.load_default()

def wrap_text_to_fit_width(text, font, max_width):
    draw_temp = ImageDraw.Draw(Image.new('RGB', (1, 1)))
    text_width = draw_temp.textbbox((0, 0), text, font=font)[2]
    if text_width <= max_width:
        text_height = draw_temp.textbbox((0, 0), text, font=font)[3]
        return [text], text_height
    
    words = text.split()
    lines = []
    current_line = ""
    
    for word in words:
        test_line = current_line + (" " if current_line else "") + word
        test_width = draw_temp.textbbox((0, 0), test_line, font=font)[2]
        if test_width <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
                current_line = word
            else:
                lines.append(word)
    
    if current_line:
        lines.append(current_line)
    
    line_height = draw_temp.textbbox((0, 0), "Aa", font=font)[3]
    total_height = len(lines) * line_height * 1.2
    return lines, int(total_height)

# ==============================================================================
# --- HÀM CHÍNH ---
# ==============================================================================

def apply_background(template_image, hue):
    background_color = hsl_to_rgb(hue, 100, 41)
    background = Image.new('RGB', template_image.size, color=background_color)
    background.paste(template_image, (0, 0), mask=template_image)
    return background

def add_data_for_opening(image_to_draw_on, data, font_dir):
    title_text = data['title']
    font_for_title = load_font(font_dir, "NotoSans-Bold.ttf", 150)
    draw = ImageDraw.Draw(image_to_draw_on)
    text_position_x = image_to_draw_on.width / 2
    text_position_y = 450
    max_width = 2000
    text_lines, total_height = wrap_text_to_fit_width(title_text, font_for_title, max_width)
    start_y = text_position_y - (total_height / 2)
    line_height = draw.textbbox((0, 0), "Aa", font=font_for_title)[3] * 1.2
    for i, line in enumerate(text_lines):
        line_y = start_y + (i * line_height)
        draw.text((text_position_x, line_y), line, fill="black", font=font_for_title, anchor="mt")
    return image_to_draw_on

def paste_emoji_image(base_img, emoji_char, pos, size, emoji_dir):
    # Lấy mã Unicode hex (VD: 😀 => 1f600.png)
    codepoints = "-".join(f"{ord(c):x}" for c in emoji_char)
    emoji_file = os.path.join(emoji_dir, f"{codepoints}.png")
    if not os.path.exists(emoji_file):
        print(f"⚠️ Không tìm thấy emoji '{emoji_char}' ({emoji_file})")
        return base_img
    emoji_img = Image.open(emoji_file).convert("RGBA")
    emoji_img = emoji_img.resize((size, size), Image.LANCZOS)
    base_img.paste(emoji_img, pos, emoji_img)
    return base_img

def add_data_for_definition(image_to_draw_on, data, font_dir):
    definition_text = data.get('definition', '')
    term = data.get('term', '')
    font_for_term = load_font(font_dir, "NotoSans-Bold.ttf", 120)
    font_for_definition = load_font(font_dir, "NotoSans-Regular.ttf", 60)
    draw = ImageDraw.Draw(image_to_draw_on)

    # Emoji màu từ Twemoji
    emoji_char = data.get('emoji', '😀')
    emoji_dir = "emojis"  # thư mục chứa PNG emoji
    image_to_draw_on = paste_emoji_image(image_to_draw_on, emoji_char, (500, int(image_to_draw_on.height/2 - 200)), 200, emoji_dir)

    # Term
    term_x = 250
    term_y = 200
    draw.text((term_x, term_y), term, fill="black", font=font_for_term, anchor="lt")

    # Definition
    def_x = 250
    def_y = 400
    max_width = 1400
    def_lines, _ = wrap_text_to_fit_width(definition_text, font_for_definition, max_width)
    line_height = draw.textbbox((0, 0), "Aa", font=font_for_definition)[3] * 1.3
    for i, line in enumerate(def_lines):
        line_y = def_y + (i * line_height)
        draw.text((def_x, line_y), line, fill="black", font=font_for_definition, anchor="lt")
    return image_to_draw_on

# ==============================================================================
# --- CHƯƠNG TRÌNH CHÍNH ---
# ==============================================================================

def process_slide(template_file, data, template_dir, font_dir, output_dir):
    template_path = os.path.join(template_dir, template_file)
    try:
        template_img = Image.open(template_path).convert('RGBA')
    except FileNotFoundError:
        print(f"❌ Không tìm thấy template '{template_path}'")
        return False

    random_hue = random.randint(0, 360)
    image_with_background = apply_background(template_img, random_hue)

    template_name = os.path.splitext(template_file)[0]
    if template_name == "opening":
        final_image = add_data_for_opening(image_with_background, data, font_dir)
    elif template_name == "definition":
        final_image = add_data_for_definition(image_with_background, data, font_dir)
    else:
        final_image = image_with_background

    os.makedirs(output_dir, exist_ok=True)
    output_filename = get_next_filename(output_dir)
    final_image.save(output_filename)
    print(f"✅ Đã lưu '{output_filename}'")
    return True

if __name__ == "__main__":
    TEMPLATE_DIR = "templates"
    OUTPUT_DIR = "output"
    FONT_DIR = "fonts"

    slides_data = [
        {
            "template": "opening.png",
            "data": {
                "title": "Computer Vision Overview",
            }
        },
        {
            "template": "definition.png",
            "data": {
                "emoji": "🤖",
                "term": "Artificial Intelligence",
                "definition": "Artificial Intelligence (AI) refers to the simulation of human intelligence in machines that are programmed to think and learn like humans. This technology encompasses various subfields including machine learning, natural language processing, and computer vision."
            }
        }
    ]

    successful_slides = 0
    for slide_config in slides_data:
        if process_slide(slide_config["template"], slide_config["data"], TEMPLATE_DIR, FONT_DIR, OUTPUT_DIR):
            successful_slides += 1

    print(f"Hoàn tất: {successful_slides}/{len(slides_data)} slide.")
