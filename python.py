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
    FIXED: Giữ nguyên các cụm từ bold không bị tách rời
    """
    # Parse text thành các phần (text, is_bold)
    parts = parse_markdown_text(text)
    
    lines = []
    current_line = []
    current_width = 0
    
    for part_text, is_bold in parts:
        font_to_use = bold_font if is_bold else regular_font
        
        # Nếu là bold text, cố gắng giữ nguyên cả cụm
        if is_bold:
            part_width = get_text_width(part_text, font_to_use)
            space_width = get_text_width(" ", font_to_use) if current_line else 0
            
            # Nếu cả cụm bold fit được trong dòng hiện tại
            if current_width + space_width + part_width <= max_width or not current_line:
                current_line.append((part_text, is_bold))
                current_width += space_width + part_width
            else:
                # Nếu không fit, xuống dòng mới
                if current_line:
                    lines.append(current_line)
                
                # Kiểm tra cụm bold có fit trong một dòng không
                if part_width <= max_width:
                    current_line = [(part_text, is_bold)]
                    current_width = part_width
                else:
                    # Nếu cụm bold quá dài, mới tách thành từng từ
                    words = part_text.split()
                    current_line = []
                    current_width = 0
                    
                    for word in words:
                        word_width = get_text_width(word, font_to_use)
                        space_width = get_text_width(" ", font_to_use) if current_line else 0
                        
                        if current_width + space_width + word_width <= max_width or not current_line:
                            current_line.append((word, is_bold))
                            current_width += space_width + word_width
                        else:
                            lines.append(current_line)
                            current_line = [(word, is_bold)]
                            current_width = word_width
        else:
            # Với text thường, tách theo từ như cũ
            words = part_text.split()
            for word in words:
                word_width = get_text_width(word, font_to_use)
                space_width = get_text_width(" ", font_to_use) if current_line else 0
                
                if current_width + space_width + word_width <= max_width or not current_line:
                    current_line.append((word, is_bold))
                    current_width += space_width + word_width
                else:
                    lines.append(current_line)
                    current_line = [(word, is_bold)]
                    current_width = word_width
    
    if current_line:
        lines.append(current_line)
    
    return lines

def draw_markdown_text(image, text, x, y, regular_font, bold_font, max_width, color="black", anchor="lt", 
                      bold_bg_color=(239, 209, 0, 255), border_radius=20):
    """
    Vẽ text có markdown bold lên image với nền màu vàng cho text bold
    FIXED: Xử lý đúng anchor, đặc biệt là "mt" (middle-top) để căn giữa
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
    bg_padding_x = 15
    bg_padding_y_top = 25
    bg_padding_y_bottom = 0
    
    # Đảm bảo image ở chế độ RGBA
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    
    draw = ImageDraw.Draw(image)
    
    for line_idx, line in enumerate(lines):
        line_y = start_y + (line_idx * line_height)
        
        # FIXED: Tính toán vị trí x cho từng dòng dựa trên anchor
        if anchor == "mt":
            # Căn giữa: tính tổng width của dòng và bắt đầu từ giữa
            total_line_width = 0
            for word, is_bold in line:
                font_to_use = bold_font if is_bold else regular_font
                total_line_width += get_text_width(word, font_to_use)
                if word != line[-1][0]:  # Không phải từ cuối
                    total_line_width += get_text_width(" ", font_to_use)
            
            current_x = x - (total_line_width / 2)  # Bắt đầu từ nửa trái của tổng width
        else:
            # Left align
            current_x = x
        
        # Nhóm các từ liên tiếp cùng định dạng (bold/normal)
        grouped_parts = []
        if line:
            current_group = [line[0]]
            current_is_bold = line[0][1]
            
            for word, is_bold in line[1:]:
                if is_bold == current_is_bold:
                    current_group.append((word, is_bold))
                else:
                    grouped_parts.append(current_group)
                    current_group = [(word, is_bold)]
                    current_is_bold = is_bold
            
            grouped_parts.append(current_group)
        
        # Vẽ từng nhóm
        for group in grouped_parts:
            if not group:
                continue
                
            is_bold = group[0][1]
            font_to_use = bold_font if is_bold else regular_font
            
            # Tạo text từ nhóm các từ
            group_text = " ".join(word for word, _ in group)
            group_width = get_text_width(group_text, font_to_use)
            group_height = get_text_height(group_text, font_to_use)
            
            # Vẽ background cho cả nhóm nếu là bold
            if is_bold:
                bg_x1 = int(current_x - bg_padding_x)
                bg_y1 = int(line_y - bg_padding_y_top)
                bg_x2 = int(current_x + group_width + bg_padding_x)
                bg_y2 = int(line_y + group_height + bg_padding_y_bottom)
                
                # Tạo layer tạm cho background
                overlay = Image.new('RGBA', image.size, (0, 0, 0, 0))
                overlay_draw = ImageDraw.Draw(overlay)
                
                # Vẽ background bo góc với màu có alpha
                draw_rounded_rectangle(overlay_draw, (bg_x1, bg_y1, bg_x2, bg_y2), 
                                     border_radius, bold_bg_color)
                
                # Blend overlay vào image chính
                image = Image.alpha_composite(image, overlay)
                draw = ImageDraw.Draw(image)
            
            # Vẽ text của nhóm với anchor="lt" vì đã tính toán vị trí x rồi
            draw.text((current_x, line_y), group_text, fill=color, font=font_to_use, anchor="lt")
            current_x += group_width
            
            # Thêm khoảng trắng giữa các nhóm
            if group != grouped_parts[-1]:  # Không phải nhóm cuối
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

def draw_mixed_text_with_markdown(image, text, x, y, regular_font, bold_font, max_width, color="black", anchor="lt"):
    """
    Hàm mới: Vẽ text với tự động detect markdown và fallback về text thường
    FIXED: Xử lý đúng anchor cho cả trường hợp có và không có markdown
    """
    # Kiểm tra xem có markdown không
    if '**' in text:
        # Có markdown, dùng draw_markdown_text
        return draw_markdown_text(image, text, x, y, regular_font, bold_font, max_width, color, anchor)
    else:
        # Không có markdown, dùng cách cũ nhưng FIXED anchor
        lines, total_height = wrap_text_to_fit_width(text, regular_font, max_width)
        draw = ImageDraw.Draw(image)
        
        # Điều chỉnh y dựa trên anchor - FIXED LOGIC
        if anchor == "mt":
            # Với "mt", text được căn giữa theo chiều ngang tại x
            start_y = y
        elif anchor == "lt":
            start_y = y
        else:
            start_y = y - total_height / 2
        
        line_height = draw.textbbox((0, 0), "Aa", font=regular_font)[3] * 1.2
        
        for i, line in enumerate(lines):
            line_y = start_y + (i * line_height)
            # FIXED: Sử dụng đúng anchor được truyền vào
            draw.text((x, line_y), line, fill=color, font=regular_font, anchor=anchor)
        
        return image, total_height
    
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
    """UPDATED: Giữ nguyên layout gốc nhưng hỗ trợ markdown"""
    title_text = data['title']
    font_regular = load_font(font_dir, "NotoSans-Regular.ttf", 150)
    font_bold = load_font(font_dir, "NotoSans-Bold.ttf", 150)
    
    # Chuyển đổi sang RGBA nếu cần
    if image_to_draw_on.mode != 'RGBA':
        image_to_draw_on = image_to_draw_on.convert('RGBA')
    
    text_position_x = image_to_draw_on.width / 2
    text_position_y = 450
    max_width = 2000
    
    # Sử dụng hàm mixed để tự động detect markdown
    image_to_draw_on, _ = draw_mixed_text_with_markdown(
        image_to_draw_on, title_text, text_position_x, text_position_y,
        font_bold, font_bold, max_width, color="black", anchor="mt"
    )
    
    return image_to_draw_on

def add_data_for_definition(image_to_draw_on, data, font_dir):
    """UPDATED: Giữ nguyên layout gốc nhưng hỗ trợ markdown"""
    definition_text = data.get('definition', '')
    term = data.get('term', '')
    
    font_term_regular = load_font(font_dir, "NotoSans-Regular.ttf", 100)
    font_term_bold = load_font(font_dir, "NotoSans-Bold.ttf", 100)
    font_def_regular = load_font(font_dir, "NotoSans-Regular.ttf", 60)
    font_def_bold = load_font(font_dir, "NotoSans-Bold.ttf", 60)
    
    # Chuyển đổi sang RGBA nếu cần
    if image_to_draw_on.mode != 'RGBA':
        image_to_draw_on = image_to_draw_on.convert('RGBA')
    
    draw = ImageDraw.Draw(image_to_draw_on)

    emoji_char = data.get('emoji', '😀')
    emoji_dir = "emojis"
    emoji_size = 300
    emoji_x = 1900
    emoji_y = int(image_to_draw_on.height / 2 - 300)
    image_to_draw_on = paste_emoji_image(image_to_draw_on, emoji_char, (emoji_x, emoji_y), emoji_size, emoji_dir)

    # Term với markdown support
    term_x = 250
    term_y = 300
    max_width_term = 1400
    image_to_draw_on, _ = draw_mixed_text_with_markdown(
        image_to_draw_on, term, term_x, term_y,
        font_term_regular, font_term_bold, max_width_term, color="black", anchor="lt"
    )

    # Definition với markdown support  
    def_x = 250
    def_y = 500
    max_width_def = 1400
    image_to_draw_on, _ = draw_mixed_text_with_markdown(
        image_to_draw_on, definition_text, def_x, def_y,
        font_def_regular, font_def_bold, max_width_def, color="black", anchor="lt"
    )
    
    return image_to_draw_on

def add_data_for_chapter(image_to_draw_on, data, font_dir):
    """UPDATED: Giữ nguyên layout gốc nhưng hỗ trợ markdown"""
    title_text = data['title']
    font_regular = load_font(font_dir, "NotoSans-Regular.ttf", 180)
    font_bold = load_font(font_dir, "NotoSans-Bold.ttf", 180)
    
    # Chuyển đổi sang RGBA nếu cần
    if image_to_draw_on.mode != 'RGBA':
        image_to_draw_on = image_to_draw_on.convert('RGBA')
    
    text_position_x = image_to_draw_on.width / 2 - image_to_draw_on.width / 6
    text_position_y = image_to_draw_on.height / 2
    max_width = 1500
    
    # Điều chỉnh start_y như code gốc
    lines_temp, total_height = wrap_text_to_fit_width(title_text.replace('**', ''), font_regular, max_width)
    start_y = text_position_y - (total_height / 2 - 50)
    
    image_to_draw_on, _ = draw_mixed_text_with_markdown(
        image_to_draw_on, title_text, text_position_x, start_y,
        font_regular, font_bold, max_width, color="black", anchor="lt"
    )
    
    return image_to_draw_on

def add_data_for_quote(image_to_draw_on, data, font_dir):
    """UPDATED: Giữ nguyên layout gốc nhưng hỗ trợ markdown"""
    title_text = data['title']
    font_regular = load_font(font_dir, "NotoSans-Regular.ttf", 120)
    font_bold = load_font(font_dir, "NotoSans-Bold.ttf", 120)
    
    # Chuyển đổi sang RGBA nếu cần
    if image_to_draw_on.mode != 'RGBA':
        image_to_draw_on = image_to_draw_on.convert('RGBA')
    
    text_position_x = image_to_draw_on.width / 4
    text_position_y = 390
    max_width = 1500
    
    image_to_draw_on, _ = draw_mixed_text_with_markdown(
        image_to_draw_on, title_text, text_position_x, text_position_y,
        font_regular, font_bold, max_width, color="black", anchor="lt"
    )
    
    return image_to_draw_on

def add_data_for_question(image_to_draw_on, data, font_dir):
    """FIXED: Căn giữa text đúng cách"""
    title_text = data['title']
    font_regular = load_font(font_dir, "NotoSans-Regular.ttf", 150) 
    font_bold = load_font(font_dir, "NotoSans-Bold.ttf", 150)
    
    # Chuyển đổi sang RGBA nếu cần
    if image_to_draw_on.mode != 'RGBA':
        image_to_draw_on = image_to_draw_on.convert('RGBA')
    
    text_position_x = image_to_draw_on.width / 2  # Vị trí giữa theo chiều ngang
    text_position_y = 450
    max_width = 2000
    
    # Kiểm tra có markdown không
    if '**' in title_text:
        # Có markdown - sử dụng hàm draw_markdown_text
        image_to_draw_on, _ = draw_markdown_text(
            image_to_draw_on, title_text, text_position_x, text_position_y,
            font_regular, font_bold, max_width, color="black", anchor="mt"
        )
    else:
        # Không có markdown - vẽ text thường và căn giữa thủ công
        lines, total_height = wrap_text_to_fit_width(title_text, font_regular, max_width)
        draw = ImageDraw.Draw(image_to_draw_on)
        
        line_height = draw.textbbox((0, 0), "Aa", font=font_regular)[3] * 1.2
        start_y = text_position_y
        
        for i, line in enumerate(lines):
            line_y = start_y + (i * line_height)
            # Căn giữa từng dòng
            draw.text((text_position_x, line_y), line, fill="black", font=font_regular, anchor="mt")
    
    return image_to_draw_on

def add_data_for_side_by_side(image_to_draw_on, data, font_dir):
    """UPDATED: Giữ nguyên layout gốc nhưng hỗ trợ markdown"""
    left_data = data.get('left', {})
    right_data = data.get('right', {})

    font_regular = load_font(font_dir, "NotoSans-Regular.ttf", 70)
    font_bold = load_font(font_dir, "NotoSans-Bold.ttf", 70)
    
    # Chuyển đổi image sang RGBA để hỗ trợ alpha blending
    if image_to_draw_on.mode != 'RGBA':
        image_to_draw_on = image_to_draw_on.convert('RGBA')

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
    image_to_draw_on, _ = draw_markdown_text(image_to_draw_on, left_content_text, content_x_left, content_y_left, 
                      font_regular, font_bold, max_width_left, color="black", anchor="lt",
                      bold_bg_color=(239, 209, 0, 255), border_radius=20)

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
    image_to_draw_on, _ = draw_markdown_text(image_to_draw_on, right_content_text, content_x_right, content_y_right, 
                      font_regular, font_bold, max_width_right, color="black", anchor="lt",
                      bold_bg_color=(239, 209, 0, 255), border_radius=20)

    return image_to_draw_on

def add_data_for_blank(image_to_draw_on, data, font_dir):
    """
    Template blank: Có title và content (list hoặc plain text)
    Hỗ trợ markdown highlight
    """
    title_text = data.get('title', '')
    content_data = data.get('content', '')

    # Font
    font_title_regular = load_font(font_dir, "NotoSans-Regular.ttf", 120)
    font_title_bold = load_font(font_dir, "NotoSans-Bold.ttf", 120)
    font_content_regular = load_font(font_dir, "NotoSans-Regular.ttf", 70)
    font_content_bold = load_font(font_dir, "NotoSans-Bold.ttf", 70)

    # Chuyển đổi sang RGBA nếu cần
    if image_to_draw_on.mode != 'RGBA':
        image_to_draw_on = image_to_draw_on.convert('RGBA')

    # --- Vẽ Title ---
    title_x = 200
    title_y = 300
    max_width_title = 2000

    image_to_draw_on, title_height = draw_mixed_text_with_markdown(
        image_to_draw_on, title_text, title_x, title_y,
        font_title_bold, font_title_bold, max_width_title,
        color="black", anchor="lt"
    )

    # --- Vẽ Content ---
    content_start_y = title_y + title_height + 100
    content_x = 200
    max_width_content = image_to_draw_on.width - 400

    if isinstance(content_data, list):
        # Content dạng list
        current_y = content_start_y
        for idx, item in enumerate(content_data, start=1):
            # Bạn có thể đổi "•" thành f"{idx}." nếu muốn số thứ tự
            line_text = f"• {item}"
            image_to_draw_on, line_height = draw_mixed_text_with_markdown(
                image_to_draw_on, line_text, content_x, current_y,
                font_content_regular, font_content_bold, max_width_content,
                color="black", anchor="lt"
            )
            current_y += line_height + 20
    else:
        # Content dạng plain text
        image_to_draw_on, _ = draw_mixed_text_with_markdown(
            image_to_draw_on, str(content_data), content_x, content_start_y,
            font_content_regular, font_content_bold, max_width_content,
            color="black", anchor="lt"
        )

    return image_to_draw_on

# Thêm biến đếm toàn cục cho text_with_emoji (giống như chapter_count)
text_with_emoji_count = 0

def add_data_for_text_with_emoji(image_to_draw_on, data, font_dir, emoji_dir="emojis"):
    """
    Template: Văn bản ở giữa, emoji ở góc.
    Luân phiên vị trí: lần lẻ trên trái & dưới phải, lần chẵn trên phải & dưới trái
    """
    global text_with_emoji_count
    text_with_emoji_count += 1
    
    # Load font
    font_text_regular = load_font(font_dir, "NotoSans-Regular.ttf", 130)
    font_text_bold = load_font(font_dir, "NotoSans-Bold.ttf", 130)

    # Emoji chars
    emoji_chars = data.get("emoji_chars", [])
    if not isinstance(emoji_chars, list):
        emoji_chars = [emoji_chars]

    # Nếu chỉ 1 emoji → nhân đôi
    if len(emoji_chars) == 1:
        emoji_chars = emoji_chars * 2

    # Size emoji
    emoji_size = 250
    margin = 50

    # === Vẽ emoji vào góc ===
    for idx, char in enumerate(emoji_chars[:2]):
        # Tạo ảnh tạm để xoay
        tmp_img = Image.new("RGBA", image_to_draw_on.size, (0, 0, 0, 0))
        
        # Chọn vị trí dựa trên số lần đã dùng
        if text_with_emoji_count % 2 == 1:
            # Lần lẻ (1, 3, 5...): trái trên - phải dưới
            if idx == 0:  # Trái trên
                pos = (100, 100)
            else:  # Phải dưới
                pos = (2200, 1100)
        else:
            # Lần chẵn (2, 4, 6...): phải trên - trái dưới
            if idx == 0:  # Phải trên
                pos = (2200, 100)
            else:  # Trái dưới
                pos = (100, 1100)

        # Dán emoji vào ảnh tạm
        paste_emoji_image(tmp_img, char, pos, emoji_size, emoji_dir)

        # Xoay nhẹ
        angle = 0
        tmp_img = tmp_img.rotate(angle, resample=Image.BICUBIC)

        # Ghép vào ảnh gốc
        image_to_draw_on = Image.alpha_composite(image_to_draw_on.convert("RGBA"), tmp_img)

    # === Vẽ text giữa ảnh ===
    text = data.get("text", "")
    center_x = 400
    center_y = 440
    max_width_text = 1900

    image_to_draw_on, _ = draw_mixed_text_with_markdown(
        image_to_draw_on, text,
        center_x, center_y,
        font_text_regular, font_text_regular, max_width_text,
        color="black", anchor="lt"
    )

    return image_to_draw_on

def add_data_for_3_steps(image_to_draw_on, data, font_dir):
    """
    Template 3_steps: Title tổng + 3 bước với vị trí cố định trong code
    - Main title: ở trên cùng bên trái (vị trí cố định)
    - Steps: 3 vị trí cố định trong code
    """
    # Main title và steps data
    main_title = data.get('title', '')
    steps_data = data.get('steps', [])
    
    # Font
    font_main_title = load_font(font_dir, "NotoSans-Bold.ttf", 100)  # Main title
    font_step_title = load_font(font_dir, "NotoSans-Bold.ttf", 80)   # Step title in hoa
    font_content = load_font(font_dir, "NotoSans-Regular.ttf", 50)   # Content in thường
    
    # Chuyển đổi sang RGBA nếu cần
    if image_to_draw_on.mode != 'RGBA':
        image_to_draw_on = image_to_draw_on.convert('RGBA')
    
    draw = ImageDraw.Draw(image_to_draw_on)
    
    # === VỊ TRÍ CỐ ĐỊNH ===
    # Main title position
    main_title_x = 100
    main_title_y = 100
    main_title_max_width = 2000
    
    # 3 step positions (cố định trong code)
    step_positions = [
        {"x": 310, "y": 655, "max_width": 600},    # Step 1: Trái
        {"x": 1060, "y": 655, "max_width": 600},   # Step 2: Giữa  
        {"x": 1810, "y": 655, "max_width": 500}    # Step 3: Phải
    ]
    
    # === Vẽ Main Title (trên cùng bên trái) ===
    if main_title:
        title_lines, _ = wrap_text_to_fit_width(main_title, font_main_title, main_title_max_width)
        current_y = main_title_y
        
        for line in title_lines:
            draw.text((main_title_x, current_y), line, fill="black", font=font_main_title, anchor="lt")
            current_y += get_text_height(line, font_main_title) * 1.3
    
    # === Vẽ từng Step với vị trí cố định ===
    for i, step in enumerate(steps_data[:3]):  # Chỉ lấy tối đa 3 step
        if i >= len(step_positions):
            break
            
        pos = step_positions[i]
        step_x = pos["x"]
        step_y = pos["y"]
        max_width = pos["max_width"]
        
        # Step title (in hoa)
        step_title = step.get('title', '')
        if step_title:
            title_lines, _ = wrap_text_to_fit_width(step_title, font_step_title, max_width)
            current_y = step_y
            
            for line in title_lines:
                draw.text((step_x, current_y), line, fill="black", font=font_step_title, anchor="lt")
                current_y += get_text_height(line, font_step_title) * 1.3
            
            # Vị trí cho content (cách title một khoảng)
            content_y = current_y-30
        else:
            content_y = step_y
        
        # Step content (in thường)
        step_content = step.get('content', '')
        if step_content:
            content_lines, _ = wrap_text_to_fit_width(step_content, font_content, max_width)
            current_content_y = content_y
            
            for line in content_lines:
                draw.text((step_x, current_content_y), line, fill="black", font=font_content, anchor="lt")
                current_content_y += get_text_height(line, font_content) * 1.3
    
    return image_to_draw_on

def add_data_for_4_steps(image_to_draw_on, data, font_dir):
    """
    Template 3_steps: Title tổng + 3 bước với vị trí cố định trong code
    - Main title: ở trên cùng bên trái (vị trí cố định)
    - Steps: 3 vị trí cố định trong code
    """
    # Main title và steps data
    main_title = data.get('title', '')
    steps_data = data.get('steps', [])
    
    # Font
    font_main_title = load_font(font_dir, "NotoSans-Bold.ttf", 100)  # Main title
    font_step_title = load_font(font_dir, "NotoSans-Bold.ttf", 80)   # Step title in hoa
    font_content = load_font(font_dir, "NotoSans-Regular.ttf", 50)   # Content in thường
    
    # Chuyển đổi sang RGBA nếu cần
    if image_to_draw_on.mode != 'RGBA':
        image_to_draw_on = image_to_draw_on.convert('RGBA')
    
    draw = ImageDraw.Draw(image_to_draw_on)
    
    # === VỊ TRÍ CỐ ĐỊNH ===
    # Main title position
    main_title_x = 100
    main_title_y = 100
    main_title_max_width = 2000
    
    # 3 step positions (cố định trong code)
    step_positions = [
        {"x": 60, "y": 655, "max_width": 600},
        {"x": 740, "y": 655, "max_width": 600},
        {"x": 1420, "y": 655, "max_width": 500},
        {"x": 2100, "y": 655, "max_width": 500}
    ]
    
    # === Vẽ Main Title (trên cùng bên trái) ===
    if main_title:
        title_lines, _ = wrap_text_to_fit_width(main_title, font_main_title, main_title_max_width)
        current_y = main_title_y
        
        for line in title_lines:
            draw.text((main_title_x, current_y), line, fill="black", font=font_main_title, anchor="lt")
            current_y += get_text_height(line, font_main_title) * 1.3
    
    # === Vẽ từng Step với vị trí cố định ===
    for i, step in enumerate(steps_data[:4]):  # Chỉ lấy tối đa 3 step
        if i >= len(step_positions):
            break
            
        pos = step_positions[i]
        step_x = pos["x"]
        step_y = pos["y"]
        max_width = pos["max_width"]
        
        # Step title (in hoa)
        step_title = step.get('title', '')
        if step_title:
            title_lines, _ = wrap_text_to_fit_width(step_title, font_step_title, max_width)
            current_y = step_y
            
            for line in title_lines:
                draw.text((step_x, current_y), line, fill="black", font=font_step_title, anchor="lt")
                current_y += get_text_height(line, font_step_title) * 1.3
            
            # Vị trí cho content (cách title một khoảng)
            content_y = current_y-30
        else:
            content_y = step_y
        
        # Step content (in thường)
        step_content = step.get('content', '')
        if step_content:
            content_lines, _ = wrap_text_to_fit_width(step_content, font_content, max_width)
            current_content_y = content_y
            
            for line in content_lines:
                draw.text((step_x, current_content_y), line, fill="black", font=font_content, anchor="lt")
                current_content_y += get_text_height(line, font_content) * 1.3
    
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
    elif template_name_no_ext == "blank":
        final_image = add_data_for_blank(image_with_background, data, font_dir)
    elif template_name_no_ext == "text_with_emoji":
        final_image = add_data_for_text_with_emoji(image_with_background, data, font_dir)
    elif template_name_no_ext == "3_steps":
        final_image = add_data_for_3_steps(image_with_background, data, font_dir)
    elif template_name_no_ext == "4_steps":
        final_image = add_data_for_4_steps(image_with_background, data, font_dir)
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
            "template": "4_steps.png",
            "data": {
                "title": "Quy trình xử lý ảnh",
                "steps": [
                    {
                        "title": "Bước 1",      # Sẽ tự động chuyển thành IN HOA
                        "content": "Nội dung"   # Giữ nguyên in thường
                    },
                    {
                        "title": "Bước 2",
                        "content": "Nội dung"
                    },
                    {
                        "title": "Bước 3",
                        "content": "Nội dung"
                    },
                    {
                        "title": "Bước 4",
                        "content": "Nội dung"
                    }
                ]
            }
        }
    ]

    successful_slides = 0
    random_hue = random.randint(0, 360)
    for slide_config in slides_data:
        if process_slide(slide_config["template"], slide_config["data"], TEMPLATE_DIR, FONT_DIR, OUTPUT_DIR, random_hue):
            successful_slides += 1

    print(f"Hoàn tất: {successful_slides}/{len(slides_data)} slide.")