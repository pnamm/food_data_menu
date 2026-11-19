import openpyxl
import os
import shutil

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

        # Replace template dish rows with the web record, clearing unused rows.
        dish_tables = (
            ("MẪU 2 - BƯỚC 2", step2, (
                "stt", "ca", "dish_name", "main_ingredient", "portions", "prep_time",
                "cook_time", "hygiene_person", "hygiene_equipment", "hygiene_environment",
                "sensory_passed", "sensory_failed", "note",
            )),
            ("MẪU 3 - BƯỚC 3", step3, (
                "stt", "ca", "dish_name", "portions", "dispense_time", "eating_time",
                "container", "sensory_passed", "sensory_failed", "note",
            )),
            ("MẪU 5 - LƯU HỦY", sampling, (
                "stt", "ca", "dish_name", "portions", "sample_amount", "container",
                "temperature", "time_sampled", "time_destroyed", "sample_condition_on_destroy",
                "sampler", "destroyer",
            )),
        )
        for sheet_name, items, fields in dish_tables:
            if sheet_name not in wb.sheetnames:
                continue
            ws = wb[sheet_name]
            for index in range(24):
                item = items[index] if index < len(items) else {}
                for column, field in enumerate(fields, 1):
                    value = item.get(field)
                    if field == "sensory_failed":
                        value = "✓" if item.get("sensory_passed") is False else None
                    elif field == "sensory_passed":
                        value = "✓" if value is True else None
                    elif field.startswith("hygiene_") and value is not None:
                        value = "Đạt" if value else "Không đạt"
                    cell = ws.cell(row=9 + index, column=column)
                    cell.value = value
                    if isinstance(value, str):
                        cell.data_type = "s"

        if "MẪU 4 - NHÃN" in wb.sheetnames:
            ws = wb["MẪU 4 - NHÃN"]
            for ca, first_row in (("TRƯA", 9), ("CHIỀU", 41), ("TỐI", 79)):
                items = [item for item in sampling if item.get("ca") == ca]
                for index in range(10):
                    item = items[index] if index < len(items) else {}
                    row = first_row + (index // 2) * 6
                    column = 2 if index % 2 == 0 else 7
                    for offset, field in enumerate(("ca", "dish_name", "time_sampled", "sampler"), 1):
                        cell = ws.cell(row=row + offset, column=column)
                        cell.value = item.get(field)
                        if isinstance(cell.value, str):
                            cell.data_type = "s"

        wb.save(output_path)
        return output_path

    return None
