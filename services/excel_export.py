import openpyxl
import os
import shutil
from datetime import datetime

# Find template file in current project directory or parent directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_PATH = os.path.join(BASE_DIR, "LƯU_MẪU_MASTER.xlsx")
if not os.path.exists(TEMPLATE_PATH):
    # Try looking in food_data_menu subfolder
    sub_path = os.path.join(BASE_DIR, "food_data_menu", "LƯU_MẪU_MASTER.xlsx")
    if os.path.exists(sub_path):
        TEMPLATE_PATH = sub_path

def export_daily_excel(date_str, daily_record_data, output_path):
    """
    Tạo file Excel chuẩn từ template LƯU_MẪU_MASTER.xlsx hoặc tạo workbook xuất dữ liệu chi tiết
    """
    if os.path.exists(TEMPLATE_PATH):
        # Sao chép template ra file mới
        shutil.copyfile(TEMPLATE_PATH, output_path)
        wb = openpyxl.load_workbook(output_path)
        
        # Cập nhật thông tin vào template nếu muốn
        # Sheet MẪU 1, 2, 3, 5, DỰ TRÙ
        step1 = daily_record_data.get("step1", [])
        step2 = daily_record_data.get("step2", [])
        step3 = daily_record_data.get("step3", [])
        sampling = daily_record_data.get("sampling", [])
        estimations = daily_record_data.get("estimations", [])

        # Ghi đè thực nhận vào sheet DỰ TRÙ
        if 'DỰ TRÙ' in wb.sheetnames:
            ws_dt = wb['DỰ TRÙ']
            for i, est in enumerate(estimations[:50]):
                r = 9 + i
                ws_dt.cell(row=r, column=12, value=est.get("actual_received"))

        # Ghi vào Mẫu 1
        if 'MẪU 1 - BƯỚC 1' in wb.sheetnames:
            ws1 = wb['MẪU 1 - BƯỚC 1']
            for i, s1 in enumerate(step1[:20]):
                r = 10 + i
                ws1.cell(row=r, column=4, value=s1.get("time_in"))
                ws1.cell(row=r, column=7, value=s1.get("supplier_name"))
                if s1.get("sensory_passed"):
                    ws1.cell(row=r, column=13, value="✓")

        # Ghi vào Mẫu 2
        if 'MẪU 2 - BƯỚC 2' in wb.sheetnames:
            ws2 = wb['MẪU 2 - BƯỚC 2']
            for i, s2 in enumerate(step2[:24]):
                r = 9 + i
                ws2.cell(row=r, column=6, value=s2.get("prep_time"))
                ws2.cell(row=r, column=7, value=s2.get("cook_time"))
                if s2.get("hygiene_person"):
                    ws2.cell(row=r, column=8, value="Đạt")
                if s2.get("sensory_passed"):
                    ws2.cell(row=r, column=11, value="✓")

        # Ghi vào Mẫu 3
        if 'MẪU 3 - BƯỚC 3' in wb.sheetnames:
            ws3 = wb['MẪU 3 - BƯỚC 3']
            for i, s3 in enumerate(step3[:24]):
                r = 9 + i
                ws3.cell(row=r, column=5, value=s3.get("dispense_time"))
                if s3.get("sensory_passed"):
                    ws3.cell(row=r, column=8, value="✓")

        # Ghi vào Mẫu 5
        if 'MẪU 5 - LƯU HỦY' in wb.sheetnames:
            ws5 = wb['MẪU 5 - LƯU HỦY']
            for i, s5 in enumerate(sampling[:24]):
                r = 9 + i
                ws5.cell(row=r, column=10, value="Bình thường")
                ws5.cell(row=r, column=11, value=s5.get("sampler"))
                ws5.cell(row=r, column=12, value=s5.get("destroyer"))

        wb.save(output_path)
        return output_path

    return None
