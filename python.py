import os
import random
import colorsys
from PIL import Image, ImageDraw, ImageFont
import textwrap

# ==============================================================================
# --- CÁC HÀM TIỆN ÍCH (HELPER FUNCTIONS) ---
# ==============================================================================

def hsl_to_rgb(h, s, l):
    """Chuyển đổi màu HSL (0-360, 0-100, 0-100) sang RGB (0-255)."""
    # Thư viện colorsys làm việc với các giá trị trong khoảng [0, 1]
    r, g, b = colorsys.hls_to_rgb(h / 360.0, l / 100.0, s / 100.0)
    return int(r * 255), int(g * 255), int(b * 255)

def get_next_filename(output_dir):
    """
    Tìm tên file số tiếp theo trong thư mục output (ví dụ: 1.png, 2.png, ...).
    """
    try:
        # Lấy danh sách các file số nguyên hiện có trong thư mục
        existing_files = [f for f in os.listdir(output_dir) if f.lower().endswith('.png')]
        existing_numbers = [int(os.path.splitext(f)[0]) for f in existing_files if os.path.splitext(f)[0].isdigit()]

        if not existing_numbers:
            # Nếu không có file số nào, bắt đầu từ 1
            return os.path.join(output_dir, "1.png")
        else:
            # Lấy số lớn nhất và cộng thêm 1
            next_number = max(existing_numbers) + 1
            return os.path.join(output_dir, f"{next_number}.png")
            
    except FileNotFoundError:
        # Nếu thư mục output chưa tồn tại, file đầu tiên sẽ là 1.png
        return os.path.join(output_dir, "1.png")

def load_font(font_dir, font_name, size):
    """
    Tải font với kích thước được chỉ định.
    Trả về font mặc định nếu không tìm thấy font được yêu cầu.
    """
    try:
        font_path = os.path.join(font_dir, font_name)
        return ImageFont.truetype(font_path, size=size)
    except (FileNotFoundError, OSError):
        print(f"⚠️  Không tìm thấy font '{font_name}', sử dụng font mặc định.")
        return ImageFont.load_default()

def wrap_text_to_fit_width(text, font, max_width):
    """
    Chia văn bản thành nhiều dòng nếu độ rộng vượt quá max_width.
    Trả về danh sách các dòng và tổng chiều cao của text block.
    """
    # Đo độ rộng của text gốc
    draw_temp = ImageDraw.Draw(Image.new('RGB', (1, 1)))
    text_width = draw_temp.textbbox((0, 0), text, font=font)[2]
    
    if text_width <= max_width:
        # Nếu text ngắn hơn max_width, trả về nguyên text
        text_height = draw_temp.textbbox((0, 0), text, font=font)[3]
        return [text], text_height
    
    # Nếu text dài hơn, chia thành nhiều dòng
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
                # Trường hợp từ đơn lẻ quá dài
                lines.append(word)
    
    if current_line:
        lines.append(current_line)
    
    # Tính tổng chiều cao (số dòng * line height)
    line_height = draw_temp.textbbox((0, 0), "Aa", font=font)[3]
    total_height = len(lines) * line_height * 1.2  # 1.2 là line spacing
    
    return lines, int(total_height)

# ==============================================================================
# --- CÁC HÀM XỬ LÝ CHÍNH (CORE PROCESSING FUNCTIONS) ---
# ==============================================================================

def apply_background(template_image, hue):
    """
    Bước 2: Thêm một lớp nền màu vào dưới template.
    Template phải là ảnh PNG có nền trong suốt.
    """
    # Tạo màu nền từ Hue (S=100%, L=41% theo yêu cầu)
    background_color = hsl_to_rgb(hue, 100, 41)
    
    # Tạo một ảnh nền mới với màu đã tính
    background = Image.new('RGB', template_image.size, color=background_color)
    
    # Dán template lên trên nền, sử dụng kênh alpha của template làm mask
    # Đây là bước quan trọng để giữ lại phần trong suốt
    background.paste(template_image, (0, 0), mask=template_image)
    
    return background

def add_data_for_opening(image_to_draw_on, data, font_dir):
    """
    Bước 3 (cho template 'opening'): Vẽ dữ liệu (văn bản) lên ảnh.
    Hàm này chỉ dành riêng cho template 'opening'.
    """
    # Lấy dữ liệu cần thiết từ dictionary `data`
    title_text = data['title']
    
    # Tải font với kích thước phù hợp cho template opening
    font_for_title = load_font(font_dir, "NotoSans-Bold.ttf", 150)
    
    # Chuẩn bị để vẽ
    draw = ImageDraw.Draw(image_to_draw_on)
    
    # Vị trí (x, y) để vẽ text
    text_position_x = image_to_draw_on.width / 2
    text_position_y = 450  # Có thể tinh chỉnh nếu cần
    
    # Kiểm tra và chia dòng nếu text quá dài (> 1500px)
    max_width = 2000
    text_lines, total_height = wrap_text_to_fit_width(title_text, font_for_title, max_width)
    
    # Điều chỉnh vị trí y để text được căn giữa theo chiều dọc
    start_y = text_position_y - (total_height / 2)
    line_height = draw.textbbox((0, 0), "Aa", font=font_for_title)[3] * 1.2
    
    # Vẽ từng dòng text
    for i, line in enumerate(text_lines):
        line_y = start_y + (i * line_height)
        draw.text(
            (text_position_x, line_y), 
            line, 
            fill="black", 
            font=font_for_title, 
            anchor="mt"  # "mt" = middle-top anchor
        )
    
    return image_to_draw_on

def add_data_for_definition(image_to_draw_on, data, font_dir):
    """
    Bước 3 (cho template 'definition'): Vẽ dữ liệu lên ảnh.
    Template cho định nghĩa/khái niệm.
    """
    # Lấy dữ liệu
    definition_text = data.get('definition', '')
    term = data.get('term', '')
    
    # Tải font phù hợp cho template definition
    font_for_term = load_font(font_dir, "NotoSans-Bold.ttf", 120)
    font_for_definition = load_font(font_dir, "NotoSans-Regular.ttf", 60)
    
    draw = ImageDraw.Draw(image_to_draw_on)

    em_x = 500
    em_y = image_to_draw_on.height/2 - 200

    draw.text(
        (em_x, em_y), 
        data.get('emoji', '😀'), 
        fill="black", 
        font=font_for_term, 
        anchor="lt"
    )
    
    # Vẽ term (từ/khái niệm)
    term_x = 250
    term_y = 200
    
    draw.text(
        (term_x, term_y), 
        term, 
        fill="black", 
        font=font_for_term, 
        anchor="lt"
    )
    
    # Vẽ definition (định nghĩa) - có thể chia dòng
    def_x = 250
    def_y = 400
    max_width = 1400
    
    def_lines, _ = wrap_text_to_fit_width(definition_text, font_for_definition, max_width)
    line_height = draw.textbbox((0, 0), "Aa", font=font_for_definition)[3] * 1.3
    
    for i, line in enumerate(def_lines):
        line_y = def_y + (i * line_height)
        draw.text(
            (def_x, line_y), 
            line, 
            fill="black", 
            font=font_for_definition, 
            anchor="lt"
        )
    
    return image_to_draw_on

# Thêm các hàm add_data_... khác ở đây khi cần

# ==============================================================================
# --- CHƯƠNG TRÌNH CHÍNH (MAIN EXECUTION BLOCK) ---
# ==============================================================================

def process_slide(template_file, data, template_dir, font_dir, output_dir):
    """
    Hàm xử lý một slide với template và data được chỉ định.
    """
    # BƯỚC 1: Tải file template
    template_path = os.path.join(template_dir, template_file)
    try:
        template_img = Image.open(template_path).convert('RGBA')
        print(f"✅ Bước 1: Đã tải template '{template_file}'.")
    except FileNotFoundError:
        print(f"❌ LỖI: Không tìm thấy file template tại '{template_path}'. Bỏ qua slide này.")
        return False

    # BƯỚC 2: Thêm nền màu ngẫu nhiên
    random_hue = random.randint(0, 360)
    image_with_background = apply_background(template_img, random_hue)
    print(f"✅ Bước 2: Đã thêm nền màu với Hue = {random_hue}.")

    # BƯỚC 3: Thêm dữ liệu (chữ, emoji, v.v.)
    template_name = os.path.splitext(template_file)[0]
    
    if template_name == "opening":
        final_image = add_data_for_opening(image_with_background, data, font_dir)
        print("✅ Bước 3: Đã thêm dữ liệu cho template 'opening'.")
    elif template_name == "definition":
        final_image = add_data_for_definition(image_with_background, data, font_dir)
        print("✅ Bước 3: Đã thêm dữ liệu cho template 'definition'.")
    else:
        # Nếu không có hàm add_data, cứ dùng ảnh có nền
        final_image = image_with_background
        print(f"⚠️  Lưu ý: Không có hàm 'add_data' cho template '{template_name}', chỉ xuất ảnh với nền màu.")

    # BƯỚC 4: Xuất file ảnh cuối cùng với tên tuần tự
    os.makedirs(output_dir, exist_ok=True)
    output_filename = get_next_filename(output_dir)
    final_image.save(output_filename)
    print(f"✅ Bước 4: Đã lưu ảnh hoàn thiện vào '{output_filename}'.")
    
    return True

if __name__ == "__main__":
    print("--- Bắt đầu quy trình tạo slide tự động ---")

    # --- 1. CẤU HÌNH BAN ĐẦU ---
    TEMPLATE_DIR = "templates"
    OUTPUT_DIR = "output"
    FONT_DIR = "fonts"

    # --- 2. XÁC ĐỊNH INPUT (Sau này sẽ đọc từ file JSON) ---
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

    # --- 3. XỬ LÝ TỪNG SLIDE ---
    successful_slides = 0
    for i, slide_config in enumerate(slides_data, 1):
        print(f"\n--- Xử lý slide {i}/{len(slides_data)} ---")
        template_file = slide_config["template"]
        slide_data = slide_config["data"]
        
        success = process_slide(template_file, slide_data, TEMPLATE_DIR, FONT_DIR, OUTPUT_DIR)
        if success:
            successful_slides += 1

    print(f"\n--- ✨ Quy trình hoàn tất! ✨ ---")
    print(f"Đã tạo thành công {successful_slides}/{len(slides_data)} slide(s).")