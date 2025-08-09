import os
import random
import colorsys
from PIL import Image, ImageDraw, ImageFont
import textwrap
import re

# ==============================================================================
# --- HÀM TIỆN ÍCH ---
# ==============================================================================

def hsl_to_rgb(h, s, l):
    r, g, b = colorsys.hls_to_rgb(h / 360.0, l / 100.0, s / 100.0)
    return int(r * 255), int(g * 255), int(b * 255)

# Bộ đếm toàn cục
slide_counter = 0
chapter_count = 0

def get_next_filename_with_suffix(output_dir, template_name):
    """Tạo tên file theo dạng: số_thứ_tự_tên_template.png"""
    global slide_counter
    slide_counter += 1
    filename = f"{slide_counter}_{template_name}.png"
    return os.path.join(output_dir, filename)

def load_font(font_dir, font_name, size):
    try:
        font_path = os.path.join(font_dir, font_name)
        return ImageFont.truetype(font_path, size=size)
    except (FileNotFoundError, OSError):
        print(f"⚠️ Không tìm thấy font '{font_name}', dùng font mặc định.")
        return ImageFont.load_default()

def parse_markdown_bold(text):
    """Parse text và tách phần **bold** ra"""
    parts = []
    pattern = r'\*\*(.*?)\*\*'
    last_end = 0
    
    for match in re.finditer(pattern, text):
        # Thêm text trước phần bold
        if match.start() > last_end:
            parts.append({'text': text[last_end:match.start()], 'bold': False})
        # Thêm phần bold
        parts.append({'text': match.group(1), 'bold': True})
        last_end = match.end()
    
    # Thêm phần text còn lại
    if last_end < len(text):
        parts.append({'text': text[last_end:], 'bold': False})
    
    # Nếu không có bold nào, trả về toàn bộ text
    if not parts:
        parts = [{'text': text, 'bold': False}]
    
    return parts

def draw_rounded_rectangle(draw, coords, fill, radius=15):
    """Vẽ hình chữ nhật bo góc"""
    x1, y1, x2, y2 = coords
    
    # Vẽ hình chữ nhật chính (không có góc)
    draw.rectangle([x1 + radius, y1, x2 - radius, y2], fill=fill)
    draw.rectangle([x1, y1 + radius, x2, y2 - radius], fill=fill)
    
    # Vẽ 4 góc bo tròn
    draw.ellipse([x1, y1, x1 + 2*radius, y1 + 2*radius], fill=fill)
    draw.ellipse([x2 - 2*radius, y1, x2, y1 + 2*radius], fill=fill)
    draw.ellipse([x1, y2 - 2*radius, x1 + 2*radius, y2], fill=fill)
    draw.ellipse([x2 - 2*radius, y2 - 2*radius, x2, y2], fill=fill)

def draw_text_with_markdown(draw, position, text, font, text_color="black", bg_color=(255, 235, 59), padding=10, anchor="lt"):
    """Vẽ text với markdown support - chỉ phần **bold** mới có nền vàng"""
    parts = parse_markdown_bold(text)
    x, y = position
    current_x = x
    
    for part in parts:
        part_text = part['text']
        
        if part['bold']:
            # Tính kích thước text
            bbox = draw.textbbox((current_x, y), part_text, font=font, anchor=anchor)
            
            # Vẽ background màu vàng cho phần bold
            bg_x1 = bbox[0] - padding
            bg_y1 = bbox[1] - padding
            bg_x2 = bbox[2] + padding
            bg_y2 = bbox[3] + padding
            
            draw_rounded_rectangle(draw, [bg_x1, bg_y1, bg_x2, bg_y2], fill=bg_color, radius=10)
        
        # Vẽ text (không bold, font vẫn giữ nguyên)
        draw.text((current_x, y), part_text, fill=text_color, font=font, anchor=anchor)
        
        # Cập nhật vị trí x cho phần text tiếp theo
        text_width = draw.textbbox((current_x, y), part_text, font=font, anchor=anchor)[2] - current_x
        current_x += text_width

def wrap_text_to_fit_width(text, font, max_width):
    """Wrap text và giữ nguyên markdown"""
    draw_temp = ImageDraw.Draw(Image.new('RGB', (1, 1)))
    
    # Loại bỏ markdown để tính toán độ rộng
    clean_text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text_width = draw_temp.textbbox((0, 0), clean_text, font=font)[2]
    
    if text_width <= max_width:
        text_height = draw_temp.textbbox((0, 0), clean_text, font=font)[3]
        return [text], text_height
    
    # Split theo từ nhưng giữ markdown
    words = text.split()
    lines = []
    current_line = ""
    
    for word in words:
        test_line = current_line + (" " if current_line else "") + word
        # Loại bỏ markdown để test độ rộng
        clean_test = re.sub(r'\*\*(.*?)\*\*', r'\1', test_line)
        test_width = draw_temp.textbbox((0, 0), clean_test, font=font)[2]
        
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
        # Tính toán để căn giữa
        clean_line = re.sub(r'\*\*(.*?)\*\*', r'\1', line)
        line_width = draw.textbbox((0, 0), clean_line, font=font_for_title)[2]
        start_x = text_position_x - (line_width / 2)
        draw_text_with_markdown(draw, (start_x, line_y), line, font_for_title, anchor="lt")
    
    return image_to_draw_on

def paste_emoji_image(base_img, emoji_char, pos, size, emoji_dir):
    """Dán emoji PNG vào vị trí (pos) với kích thước (size)."""
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
    
    font_for_term = load_font(font_dir, "NotoSans-Bold.ttf", 100)
    font_for_definition = load_font(font_dir, "NotoSans-Regular.ttf", 60)
    draw = ImageDraw.Draw(image_to_draw_on)

    emoji_char = data.get('emoji', '😀')
    emoji_dir = "emojis"
    emoji_size = 300
    emoji_x = 1900
    emoji_y = int(image_to_draw_on.height / 2 - 300)
    image_to_draw_on = paste_emoji_image(image_to_draw_on, emoji_char, (emoji_x, emoji_y), emoji_size, emoji_dir)

    term_x = 250
    term_y = 300
    draw_text_with_markdown(draw, (term_x, term_y), term, font_for_term, anchor="lt")

    def_x = 250
    def_y = 500
    max_width = 1400
    def_lines, _ = wrap_text_to_fit_width(definition_text, font_for_definition, max_width)
    line_height = draw.textbbox((0, 0), "Aa", font=font_for_definition)[3] * 1.3
    
    for i, line in enumerate(def_lines):
        line_y = def_y + (i * line_height)
        draw_text_with_markdown(draw, (def_x, line_y), line, font_for_definition, anchor="lt")
    
    return image_to_draw_on

def add_data_for_chapter(image_to_draw_on, data, font_dir):
    title_text = data['title']
    font_for_title = load_font(font_dir, "NotoSans-Bold.ttf", 180)
    draw = ImageDraw.Draw(image_to_draw_on)
    text_position_x = image_to_draw_on.width / 2 - image_to_draw_on.width / 6
    text_position_y = image_to_draw_on.height / 2
    max_width = 1500
    text_lines, total_height = wrap_text_to_fit_width(title_text, font_for_title, max_width)
    start_y = text_position_y - (total_height / 2 - 50)
    line_height = draw.textbbox((0, 0), "Aa", font=font_for_title)[3] * 1.2
    
    for i, line in enumerate(text_lines):
        line_y = start_y + (i * line_height)
        draw_text_with_markdown(draw, (text_position_x, line_y), line, font_for_title, anchor="lt")
    
    return image_to_draw_on

def add_data_for_quote(image_to_draw_on, data, font_dir):
    title_text = data['title']
    font_for_title = load_font(font_dir, "NotoSans-Regular.ttf", 120)
    draw = ImageDraw.Draw(image_to_draw_on)
    text_position_x = image_to_draw_on.width / 4
    text_position_y = 390
    max_width = 1500
    text_lines, total_height = wrap_text_to_fit_width(title_text, font_for_title, max_width)
    start_y = text_position_y
    line_height = draw.textbbox((0, 0), "Aa", font=font_for_title)[3] * 1.2
    
    for i, line in enumerate(text_lines):
        line_y = start_y + (i * line_height)
        draw_text_with_markdown(draw, (text_position_x, line_y), line, font_for_title, anchor="lt")
    
    return image_to_draw_on

def add_data_for_question(image_to_draw_on, data, font_dir):
    title_text = data['title']
    font_for_title = load_font(font_dir, "NotoSans-Bold.ttf", 150)
    draw = ImageDraw.Draw(image_to_draw_on)
    text_position_x = image_to_draw_on.width / 2
    text_position_y = 450
    max_width = 2000
    text_lines,_ = wrap_text_to_fit_width(title_text, font_for_title, max_width)
    line_height = draw.textbbox((0, 0), "Aa", font=font_for_title)[3] * 1.2
    
    for i, line in enumerate(text_lines):
        line_y = text_position_y + (i * line_height)
        # Tính toán để căn giữa
        clean_line = re.sub(r'\*\*(.*?)\*\*', r'\1', line)
        line_width = draw.textbbox((0, 0), clean_line, font=font_for_title)[2]
        start_x = text_position_x - (line_width / 2)
        draw_text_with_markdown(draw, (start_x, line_y), line, font_for_title, anchor="lt")
    
    return image_to_draw_on

def add_data_for_side_by_side(image_to_draw_on, data, font_dir):
    left_data = data.get('left', {})
    right_data = data.get('right', {})

    font_for_content = load_font(font_dir, "NotoSans-Regular.ttf", 70)
    draw = ImageDraw.Draw(image_to_draw_on)

    # Left side
    left_emoji_char = left_data.get('emoji', '😀')
    left_content_text = left_data.get('content', '')
    
    emoji_dir = "emojis"
    emoji_size = 200
    emoji_x_left = 200
    emoji_y_left = 500
    image_to_draw_on = paste_emoji_image(image_to_draw_on, left_emoji_char, (emoji_x_left, emoji_y_left), emoji_size, emoji_dir)
    
    content_x_left = 200
    content_y_left = 800
    max_width_left = 950
    content_lines_left, _ = wrap_text_to_fit_width(left_content_text, font_for_content, max_width_left)
    line_height = draw.textbbox((0, 0), "Aa", font=font_for_content)[3] * 1.3
    
    for i, line in enumerate(content_lines_left):
        line_y = content_y_left + (i * line_height)
        draw_text_with_markdown(draw, (content_x_left, line_y), line, font_for_content, anchor="lt")

    # Right side
    right_emoji_char = right_data.get('emoji', '😀')
    right_content_text = right_data.get('content', '')

    emoji_x_right = 1400
    emoji_y_right = 500
    image_to_draw_on = paste_emoji_image(image_to_draw_on, right_emoji_char, (emoji_x_right, emoji_y_right), emoji_size, emoji_dir)

    content_x_right = 1400
    content_y_right = 800
    max_width_right = 950
    content_lines_right, _ = wrap_text_to_fit_width(right_content_text, font_for_content, max_width_right)
    
    for i, line in enumerate(content_lines_right):
        line_y = content_y_right + (i * line_height)
        draw_text_with_markdown(draw, (content_x_right, line_y), line, font_for_content, anchor="lt")

    return image_to_draw_on


# ==============================================================================
# --- XỬ LÝ SLIDE ---
# ==============================================================================

def process_slide(template_file, data, template_dir, font_dir, output_dir, random_hue=random.randint(0, 360)):
    global chapter_count

    template_name_no_ext = os.path.splitext(template_file)[0]

    # Nếu là chapter thì thay bằng chapter_X.png
    if template_name_no_ext == "chapter":
        chapter_count += 1
        chapter_img_name = f"chapter_{chapter_count}.png"
        template_path = os.path.join(template_dir, chapter_img_name)
    else:
        template_path = os.path.join(template_dir, template_file)

    try:
        template_img = Image.open(template_path).convert('RGBA')
    except FileNotFoundError:
        print(f"❌ Không tìm thấy template '{template_path}'")
        return False

    image_with_background = apply_background(template_img, random_hue)

    if template_name_no_ext == "opening":
        final_image = add_data_for_opening(image_with_background, data, font_dir)
    elif template_name_no_ext == "definition":
        final_image = add_data_for_definition(image_with_background, data, font_dir)
    elif template_name_no_ext == "chapter":
        final_image = add_data_for_chapter(image_with_background, data, font_dir)
    elif template_name_no_ext == "quote":
        final_image = add_data_for_quote(image_with_background, data, font_dir)
    elif template_name_no_ext == "question":
        final_image = add_data_for_question(image_with_background, data, font_dir)
    elif template_name_no_ext == "side_by_side":
        final_image = add_data_for_side_by_side(image_with_background, data, font_dir)
    else:
        final_image = image_with_background

    os.makedirs(output_dir, exist_ok=True)
    output_filename = get_next_filename_with_suffix(output_dir, template_name_no_ext)
    final_image.save(output_filename)
    print(f"✅ Đã lưu '{output_filename}'")
    return True

# ==============================================================================
# --- CHẠY CHÍNH ---
# ==============================================================================

if __name__ == "__main__":
    TEMPLATE_DIR = "templates"
    OUTPUT_DIR = "output"
    FONT_DIR = "fonts"

    slides_data = [
        {
            "template": "opening.png",
            "data": {
                "title": "**Computer Vision** Overview",
            }
        },
        {
            "template": "chapter.png",
            "data": {
                "title": "Giới thiệu về **Computer Vision**",
            }
        },
        {
            "template": "definition.png",
            "data": {
                "emoji": "😀",
                "term": "**Nội dung**",
                "definition": "định nghĩa **bla bla** và thêm nội dung"
            }
        },
        {
            "template": "chapter.png",
            "data": {
                "title": "Các **kỹ thuật**",
            }
        },
        {
            "template": "quote.png",
            "data": {
                "title": "The task is to build a **CNN model** to classify handwritten images into the **digits 0 through 9**.",
            }
        },
        {
            "template": "question.png",
            "data": {
                "title": "Làm thế nào để cải thiện **độ chính xác** của mô hình **CNN**?",
            }
        },
        {
            "template": "side_by_side.png",
            "data": {
                "left": {
                    "emoji": "🔢",
                    "content": "Vòng lặp **for**: Use when the number of repetitions is **known**"
                },
                "right": {
                    "emoji": "🧐",
                    "content": "Vòng lặp **while**: Use when the number of repetitions is **unknown**"
                }
            }
        },
    ]

    successful_slides = 0
    random_hue = random.randint(0, 360)
    for slide_config in slides_data:
        if process_slide(slide_config["template"], slide_config["data"], TEMPLATE_DIR, FONT_DIR, OUTPUT_DIR, random_hue):
            successful_slides += 1

    print(f"Hoàn tất: {successful_slides}/{len(slides_data)} slide.")