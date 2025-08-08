import random
import colorsys
from PIL import Image
import os

def hsl_to_rgb(h, s, l):
    """
    Hàm chuyển đổi màu HSL sang RGB.
    h (hue) từ 0-360, s (saturation) và l (lightness) từ 0-100.
    Trả về một tuple (R, G, B) trong khoảng 0-255.
    """
    # Thư viện colorsys làm việc với các giá trị trong khoảng [0, 1]
    r, g, b = colorsys.hls_to_rgb(h / 360.0, l / 100.0, s / 100.0)
    return int(r * 255), int(g * 255), int(b * 255)

def process_template_image(template_path, output_dir, common_hue):
    """
    Tạo một slide bằng cách đặt ảnh template lên trên một lớp nền với một màu Hue cố định.
    Màu Hue này (common_hue) được truyền vào và áp dụng cho tất cả ảnh.
    """
    # 1. Xác định màu nền dựa trên common_hue đã cho
    background_color_rgb = hsl_to_rgb(common_hue, 100, 41) # S=100%, L=41%
    
    print(f"🎨 Đang xử lý '{os.path.basename(template_path)}' với Hue chung: {common_hue}, RGB: {background_color_rgb}")

    # 2. Mở ảnh template
    try:
        template_image = Image.open(template_path)
    except FileNotFoundError:
        print(f"❌ LỖI: Không tìm thấy file tại '{template_path}'. Bỏ qua.")
        return
    except Exception as e:
        print(f"❌ LỖI khi mở file '{template_path}': {e}. Bỏ qua.")
        return

    # Đảm bảo ảnh có kênh alpha (trong suốt) để ghép nền
    if template_image.mode != 'RGBA':
        template_image = template_image.convert('RGBA')
        # print("  ℹ️  Ảnh template đã được chuyển sang chế độ RGBA.")

    # 3. Tạo nền và ghép ảnh
    final_image_size = template_image.size
    background_layer = Image.new('RGB', final_image_size, color=background_color_rgb)

    # Dán ảnh template lên trên lớp nền, sử dụng kênh alpha làm mask
    background_layer.paste(template_image, (0, 0), mask=template_image)

    # 4. Lưu ảnh kết quả
    # Tạo tên file đầu ra
    base_name = os.path.basename(template_path)
    name_without_ext = os.path.splitext(base_name)[0]
    # Không thêm hue vào tên file riêng lẻ, vì hue này là chung cho cả bộ
    output_filename = f"{name_without_ext}_colorized.png" 
    output_path = os.path.join(output_dir, output_filename)

    # Đảm bảo thư mục output tồn tại
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    background_layer.save(output_path, 'PNG')
    print(f"✅ Đã lưu ảnh vào: '{output_path}'")


# --- PHẦN THỰC THI CHÍNH ---
if __name__ == "__main__":
    print("--- Chương trình tạo nền màu ngẫu nhiên thống nhất cho tất cả templates ---")
    
    # 1. TẠO MỘT GIÁ TRỊ HUE NGẪU NHIÊN DUY NHẤT CHO TOÀN BỘ QUÁ TRÌNH
    global_random_hue = random.randint(0, 360)
    print(f"🌈 Màu nền chung (Hue) được chọn ngẫu nhiên là: {global_random_hue}")

    # 2. Cấu hình thư mục
    template_directory = 'template' 
    output_directory = f'output_uniform_hue_{global_random_hue}' # Tên thư mục output có kèm hue chung

    if not os.path.exists(template_directory):
        print(f"❌ LỖI: Thư mục '{template_directory}' không tồn tại. Vui lòng kiểm tra lại đường dẫn.")
    else:
        # Lặp qua tất cả các file trong thư mục template
        for filename in os.listdir(template_directory):
            if filename.lower().endswith('.png'): # Chỉ xử lý các file PNG
                full_template_path = os.path.join(template_directory, filename)
                # Gọi hàm xử lý cho từng file, TRUYỀN common_hue đã tạo ngẫu nhiên
                process_template_image(full_template_path, output_directory, common_hue=global_random_hue)
        print(f"\n--- Hoàn thành quá trình xử lý tất cả hình ảnh với màu nền chung (Hue {global_random_hue}). ---")