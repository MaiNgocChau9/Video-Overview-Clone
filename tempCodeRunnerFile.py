import os
import random
import colorsys
import re
from PIL import Image, ImageDraw, ImageFont
import textwrap

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

def parse_markdown_text(text):
    """
    Tách text có markdown bold thành các phần
    Trả về list các tuple (text, is_bold)
    """
    parts = []
    current_pos = 0
    
    # Tìm tất cả các pattern **text**
    bold_pattern = re.compile(r'\*\*(.*?)\*\*')
    
    for match in bold_pattern.finditer(text):
        # Thêm text trước phần bold
        if match.start() > current_pos:
            normal_text = text[current_pos:match.start()]
            if normal_text:
                parts.append((normal_text, False))
        
        # Thêm phần bold
        bold_text = match.group(1)
        parts.append((bold_text, True))
        
        current_pos = match.end()
    
    # Thêm phần text còn lại
    if current_pos < len(text):
        remaining_text = text[current_pos:]
        if remaining_text:
            parts.append((remaining_text, False))
    
    # Nếu không có bold text, trả về text gốc
    if not parts:
        parts.append((text, False))
    
    return parts

def get_text_width(text, font):
    """Tính độ rộng của text với font cho trước"""
    draw_temp = ImageDraw.Draw(Image.new('RGB', (1, 1)))
    return draw_temp.textbbox((0, 0), text, font=font)[2]

def get_text_height(text, font):
    """Tính độ cao của text với font cho trước"""
    draw_temp = ImageDraw.Draw(Image.new('RGB', (1, 1)))
    return draw_temp.textbbox((0, 0), text, font=font)[3]

def draw_rounded_rectangle(draw, coords, radius, fill_color):
    """Vẽ hình chữ nhật bo góc"""
    x1, y1, x2, y2 = coords
    
    # Vẽ hình chữ nhật chính (giữa)
    draw.rectangle([x1 + radius, y1, x2 - radius, y2], fill=fill_color)
    draw.rectangle([x1, y1 + radius, x2, y2 - radius], fill=fill_color)
    
    # Vẽ các góc bo tròn
    draw.ellipse([x1, y1, x1 + 2*radius, y1 + 2*radius], fill=fill_color)  # Góc trên trái
    draw.ellipse([x2 - 2*radius, y1, x2, y1 + 2*radius], fill=fill_color)  # Góc trên phải
    draw.ellipse([x1, y2 - 2*radius, x1 + 2*radius, y2], fill=fill_color)  # Góc dưới trái
    draw.ellipse([x2 - 2*radius, y2 - 2*radius, x2, y2], fill=fill_color)  # Góc dưới phải

def wrap_markdown_text_to_fit_width(text, regular_font, bold_font, max_width):
    """
    Wrap text có markdown bold để fit trong width
    Trả về list các dòng, mỗi dòng là list các tuple (text, is_bold)
    """
    words_with_format = []
    
    # Tách text thành các từ nhưng giữ lại thông tin bold
    parts = parse_markdown_text(text)
    for part_text, is_bold in parts:
        words = part_text.split()
        for word in words:
            words_with_format.append((word, is_bold))
    
    lines = []
    current_line = []
    current_width = 0
    
    for word, is_bold in words_with_format:
        font_to_use = bold_font if is_bold else regular_font
        word_width = get_text_width(word, font_to_use)
        space_width = get_text_width(" ", font_to_use)
        
        # Tính width của từ + khoảng trắng (trừ từ cuối dòng)
        total_word_width = word_width + (space_width if current_line else 0)
        
        if current_width + total_word_width <= max_width or not current_line:
            current_line.append((word, is_bold))
            current_width += total_word_width
        else:
            lines.append(current_line)
            current_line = [(word, is_bold)]
            current_width = word_width
    
    if current_line:
        lines.append(current_line)
    
    return lines

def draw_markdown_text(image, text, x, y, regular_font, bold_font, max_width, color="black", anchor="lt", 
                      bold_bg_color=(255, 255, 0, 200), border_radius=8):
    """
    Vẽ text có markdown bold lên image với nền màu vàng cho text bold
    """
    lines = wrap_markdown_text_to_fit_width(text, regular_font, bold_font, max_width)
    line_height = max(get_text_height("Aa", regular_font), get_text_height("Aa", bold_font)) * 1.3
    
    total_height = len(lines) * line_height
    
    # Điều chỉnh y dựa trên anchor
    if anchor == "mt":
        start_y = y
    elif anchor == "lt":
        start_y = y
    else:
        start_y = y - total_height / 2
    
    # Padding cho background
    bg_padding_x = 8
    bg_padding_y = 4
    
    # Đảm bảo image ở chế độ RGBA
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    
    draw = ImageDraw.Draw(image)
    
    for line_idx, line in enumerate(lines):
        current_x = x
        line_y = start_y + (line_idx * line_height)
        
        for word_idx, (word, is_bold) in enumerate(line):
            font_to_use = bold_font if is_bold else regular_font
            word_width = get_text_width(word, font_to_use)
            word_height = get_text_height(word, font_to_use)
            
            # Vẽ background màu vàng cho text bold
            if is_bold:
                # Tính toạ độ background
                bg_x1 = int(current_x - bg_padding_x)
                bg_y1 = int(line_y - bg_padding_y)
                bg_x2 = int(current_x + word_width + bg_padding_x)
                bg_y2 = int(line_y + word_height + bg_padding_y)
                
                # Tạo layer tạm cho background
                overlay = Image.new('RGBA', image.size, (0, 0, 0, 0))
                overlay_draw = ImageDraw.Draw(overlay)
                
                # Vẽ background bo góc với màu có alpha
                draw_rounded_rectangle(overlay_draw, (bg_x1, bg_y1, bg_x2, bg_y2), 
                                     border_radius, bold_bg_color)
                
                # Blend overlay vào image chính
                image = Image.alpha_composite(image, overlay)
                
                # Tạo lại draw object sau khi blend
                draw = ImageDraw.Draw(image)
            
            # Vẽ từ
            draw.text((current_x, line_y), word, fill=color, font=font_to_use, anchor="lt")
            current_x += word_width
            
            # Thêm khoảng trắng nếu không phải từ cuối cùng
            if word_idx < len(line) - 1:
                space_width = get_text_width(" ", font_to_use)
                current_x += space_width
    
    return image, total_height

def wrap_text_to_fit_width(text, font, max_width):
    """Hàm wrap text gốc cho text không có markdown"""
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

def add_data_for_opening(image_to_draw_on, data, font_dir):
    title_text = data['title']
    font_for_title = load_font(font_dir, "NotoSans-Bold.ttf", 150)
    draw = ImageDraw.Draw(image_to_draw_on)
    text_position_x = image_to_draw_on.width / 2
    text_position_y = 450
    max_width = 2000
    text_lines, total_height = wrap_text_to_fit_width(title_text, font_for_title, max_width)
    start_y = text_position_y - (total_height / 2)
    line_height = draw.textbbox((0, 0), "Aa", font_for_title)[3] * 1.2
    for i, line in enumerate(text_lines):
        line_y = start_y + (i * line_height)
        draw.text((text_position_x, line_y), line, fill="black", font=font_for_title, anchor="mt")
    return image_to_draw_on

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
    draw.text((term_x, term_y), term, fill="black", font=font_for_term, anchor="lt")

    def_x = 250
    def_y = 500
    max_width = 1400
    def_lines, _ = wrap_text_to_fit_width(definition_text, font_for_definition, max_width)
    line_height = draw.textbbox((0, 0), "Aa", font_for_definition)[3] * 1.3
    
    for i, line in enumerate(def_lines):
        line_y = def_y + (i * line_height)
        draw.text((def_x, line_y), line, fill="black", font=font_for_definition, anchor="lt")
    
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
    line_height = draw.textbbox((0, 0), "Aa", font_for_title)[3] * 1.2
    for i, line in enumerate(text_lines):
        line_y = start_y + (i * line_height)
        draw.text((text_position_x, line_y), line, fill="black", font=font_for_title, anchor="lt")
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
    line_height = draw.textbbox((0, 0), "Aa", font_for_title)[3] * 1.2
    for i, line in enumerate(text_lines):
        line_y = start_y + (i * line_height)
        draw.text((text_position_x, line_y), line, fill="black", font=font_for_title, anchor="lt")
    return image_to_draw_on

def add_data_for_question(image_to_draw_on, data, font_dir):
    title_text = data['title']
    font_for_title = load_font(font_dir, "NotoSans-Bold.ttf", 150)
    draw = ImageDraw.Draw(image_to_draw_on)
    text_position_x = image_to_draw_on.width / 2
    text_position_y = 450
    max_width = 2000
    text_lines,_ = wrap_text_to_fit_width(title_text, font_for_title, max_width)
    line_height = draw.textbbox((0, 0), "Aa", font_for_title)[3] * 1.2
    for i, line in enumerate(text_lines):
        line_y = text_position_y + (i * line_height)
        draw.text((text_position_x, line_y), line, fill="black", font=font_for_title, anchor="mt")
    return image_to_draw_on

def add_data_for_side_by_side(image_to_draw_on, data, font_dir):
    left_data = data.get('left', {})
    right_data = data.get('right', {})

    font_regular = load_font(font_dir, "NotoSans-Regular.ttf", 70)
    font_bold = load_font(font_dir, "NotoSans-Bold.ttf", 70)
    
    # Chuyển đổi image sang RGBA để hỗ trợ alpha blending
    if image_to_draw_on.mode != 'RGBA':
        image_to_draw_on = image_to_draw_on.convert('RGBA')
    
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
    max_width_left = 950  # Giới hạn width cho cột trái
    
    # Sử dụng hàm draw_markdown_text với nền màu vàng
    draw_markdown_text(draw, left_content_text, content_x_left, content_y_left, 
                      font_regular, font_bold, max_width_left, color="black", anchor="lt",
                      bold_bg_color=(255, 255, 0, 200), border_radius=8)

    # Right side
    right_emoji_char = right_data.get('emoji', '😀')
    right_content_text = right_data.get('content', '')

    emoji_x_right = 1400
    emoji_y_right = 500
    image_to_draw_on = paste_emoji_image(image_to_draw_on, right_emoji_char, (emoji_x_right, emoji_y_right), emoji_size, emoji_dir)

    content_x_right = 1400
    content_y_right = 800
    max_width_right = 950  # Giới hạn width cho cột phải
    
    # Sử dụng hàm draw_markdown_text với nền màu vàng
    draw_markdown_text(draw, right_content_text, content_x_right, content_y_right, 
                      font_regular, font_bold, max_width_right, color="black", anchor="lt",
                      bold_bg_color=(255, 255, 0, 200), border_radius=8)

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
                "title": "Computer Vision Overview",
            }
        },
        {
            "template": "chapter.png",
            "data": {
                "title": "Giới thiệu về Computer Vision",
            }
        },
        {
            "template": "definition.png",
            "data": {
                "emoji": "😀",
                "term": "Nội dung",
                "definition": "định nghĩa bla bla "
            }
        },
        {
            "template": "chapter.png",
            "data": {
                "title": "Các kỹ thuật",
            }
        },
        {
            "template": "quote.png",
            "data": {
                "title": "The task is to build a CNN model to classify handwritten images into the digits 0 through 9.",
            }
        },
        {
            "template": "question.png",
            "data": {
                "title": "Làm thế nào để cải thiện độ chính xác của mô hình CNN?",
            }
        },
        {
            "template": "side_by_side.png",
            "data": {
                "left": {
                    "emoji": "🔢",
                    "content": "**Vòng lặp for:** Use when the number of repetitions is **known,**"
                },
                "right": {
                    "emoji": "🧐",
                    "content": "**Vòng lặp while**: Use when the number of repetitions is **unknown**"
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