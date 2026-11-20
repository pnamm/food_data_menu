from copy import copy
from datetime import date, timedelta
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.cell.cell import MergedCell
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.print_settings import PrintArea


TEMPLATE_PATH = Path(__file__).resolve().parent.parent / "LƯU_MẪU_MASTER.xlsx"

ESTIMATE_FIELDS = (
    "stt", "ingredient", "norm_group", "norm_per_portion", "norm_unit",
    "waste_rate", "portions", "need_amount", "unit", "min_amount", "max_amount",
    "actual_received", "diff_ratio", "evaluation",
)
FRESH_FIELDS = (
    "stt", "ingredient", "date_in", "time_in", "quantity", "unit",
    "supplier_name", "supplier_address", "delivery_person", "certificate",
    None, None, "sensory_passed", "sensory_failed", None, None, "action",
)
DRY_FIELDS = (
    "stt", "ingredient", None, None, None, "date_in", "time_in", "quantity_with_unit",
    "supplier_name", "supplier_address", "delivery_person", None, "storage_condition",
    "certificate", "sensory_passed", "sensory_failed", None, "action",
)
DISH_TABLES = (
    ("MẪU 2 - BƯỚC 2", "step2", (
        "stt", "ca", "dish_name", "main_ingredient", "portions", "prep_time", "cook_time",
        "hygiene_person", "hygiene_equipment", "hygiene_environment",
        "sensory_passed", "sensory_failed", "note",
    ), 39, 8),
    ("MẪU 3 - BƯỚC 3", "step3", (
        "stt", "ca", "dish_name", "portions", "dispense_time", "eating_time", "container",
        "sensory_passed", "sensory_failed", "note",
    ), 39, 7),
    ("MẪU 5 - LƯU HỦY", "sampling", (
        "stt", "ca", "dish_name", "portions", "sample_amount", "container", "temperature",
        "time_sampled", "time_destroyed", "sample_condition_on_destroy", "sampler", "destroyer",
    ), 40, 9),
)


def write_cell(cell, value):
    cell.value = value
    if isinstance(value, str):
        cell.data_type = "s"


def report_value(item, field):
    if field in ("sensory_passed", "sensory_failed"):
        expected = field == "sensory_passed"
        return "✓" if item.get("sensory_passed") is expected else None
    value = item.get(field)
    if field == "diff_ratio" and item.get("diff_percent") is not None:
        return item["diff_percent"] / 100
    if field == "quantity_with_unit" and item.get("quantity") is not None:
        return f'{item["quantity"]} {item.get("unit") or ""}'.strip()
    if field and field.startswith("hygiene_") and isinstance(value, bool):
        return "Đạt" if value else "Không đạt"
    return value


def expand_section(ws, end, extra, columns):
    if extra <= 0:
        return
    area = next(iter(PrintArea.from_string(ws.print_area).ranges), None) if ws.print_area else None
    merges = [copy(span) for span in ws.merged_cells.ranges if span.min_row > end]
    row_styles = [(row, copy(style)) for row, style in ws.row_dimensions.items() if row > end]
    for span in merges:
        ws.unmerge_cells(str(span))
    for row, _ in row_styles:
        del ws.row_dimensions[row]
    ws.insert_rows(end + 1, extra)
    for span in merges:
        span.shift(row_shift=extra)
        ws.merge_cells(str(span))
    for row, style in row_styles:
        style.index = row + extra
        ws.row_dimensions[row + extra] = style
    for row in range(end + 1, end + extra + 1):
        ws.row_dimensions[row].height = ws.row_dimensions[end].height
        for column in range(1, columns + 1):
            ws.cell(row, column)._style = copy(ws.cell(end, column)._style)
    if area:
        ws.print_area = f"{get_column_letter(area.min_col)}{area.min_row}:{get_column_letter(area.max_col)}{area.max_row + extra}"


def write_section(ws, first, last, fields, items):
    extra = max(0, len(items) - (last - first + 1))
    expand_section(ws, last, extra, len(fields))
    for index, row in enumerate(range(first, last + extra + 1)):
        item = items[index] if index < len(items) else {}
        for column, field in enumerate(fields, 1):
            cell = ws.cell(row, column)
            if field is None and isinstance(cell, MergedCell):
                continue
            write_cell(cell, report_value(item, field))
            if field in ("quantity", "need_amount", "min_amount", "max_amount", "actual_received"):
                cell.number_format = "#,##0.##"
    return extra


def write_menu(ws, report_date, week_start, week_menu, week_portions, config):
    write_cell(ws["C1"], config.get("Tên cơ sở"))
    write_cell(ws["C2"], config.get("Địa chỉ / địa điểm kiểm tra"))
    write_cell(ws["C3"], f'ĐT: {config.get("Điện thoại", "")}')
    week_end = week_start + timedelta(days=6)
    write_cell(ws["C4"], f"THỰC ĐƠN TỪ {week_start:%d/%m/%Y} ĐẾN {week_end:%d/%m/%Y}")
    for cell in ("D7", "F7", "G7", "I10"):
        ws[cell].number_format = "dd/mm/yyyy"
    for cell, value in {"D7": week_start, "F7": week_end, "G7": None, "I10": report_date,
                        "I8": list(week_menu)[report_date.weekday()], "I12": None, "I13": None}.items():
        write_cell(ws[cell], value)
    for index, (day, meals) in enumerate(week_menu.items()):
        first = 12 + index * 5
        write_cell(ws.cell(first, 7), meals.get("afternoon", {}).get("soup_dish") or None)
        write_cell(ws.cell(first + 1, 2), "Món phụ 1 / 2")
        for column, meal in enumerate(("lunch", "afternoon", "dinner"), 3):
            slots = meals.get(meal, {})
            for offset, role in enumerate(("main", "sub", "stir", "soup", "dessert")):
                value = slots.get(role)
                cell = ws.cell(first + offset, column)
                if role == "sub" and slots.get("sub2"):
                    value = f"{value or '—'}\n{slots['sub2']}"
                    alignment = copy(cell.alignment)
                    alignment.wrap_text = True
                    cell.alignment = alignment
                    ws.row_dimensions[first + offset].height = max(
                        ws.row_dimensions[first + offset].height or 0, 34
                    )
                write_cell(cell, value or None)
        portions = week_portions[index]
        values = (day, "Có" if portions["has_overtime"] else "Không", portions["lunch_portions"],
                  portions["dinner_portions"], portions["afternoon_portions"],
                  "Có" if portions["has_dinner"] else "Không", portions["afternoon_soup_portions"])
        for column, value in enumerate(values, 9):
            write_cell(ws.cell(17 + index, column), value)
    selected = week_portions[report_date.weekday()]
    write_cell(ws["I11"], " | ".join((("Có" if selected["has_overtime"] else "Không") + " tăng ca chiều",
                                        ("Có" if selected["has_dinner"] else "Không") + " ca tối")))


def write_labels(ws, sampling, date_str):
    for ca, header, first, capacity in (("TRƯA", 1, 3, 12), ("CHIỀU", 39, 41, 12), ("TỐI", 77, 79, 12)):
        write_cell(ws.cell(header, 1), f"Mẫu số 4: NHÃN MẪU THỨC ĂN LƯU – CA {ca} – {date_str}")
        items = [item for item in sampling if item.get("ca") == ca]
        for index in range(capacity):
            item = items[index] if index < len(items) else {}
            row = first + (index // 2) * 6
            column = 2 if index % 2 == 0 else 7
            title = "NHÃN MẪU THỨC ĂN LƯU"
            if item.get("sample_amount"):
                title += f' – {item["sample_amount"]}'
            write_cell(ws.cell(row, column - 1), title if item else None)
            for offset, field in enumerate(("ca", "dish_name", "time_sampled", "sampler"), 1):
                write_cell(ws.cell(row + offset, column), item.get(field))


def export_daily_excel(date_str, daily_record_data, output_path, *, week_menu, week_portions, config, checklist):
    report_date = date.fromisoformat(date_str)
    week_start = report_date - timedelta(days=report_date.weekday())
    wb = load_workbook(TEMPLATE_PATH)
    record = daily_record_data
    menu = wb["THỰC ĐƠN"]
    write_menu(menu, report_date, week_start, week_menu, week_portions, config)
    settings = wb["CẤU HÌNH"]
    for row in (4, 5, 6, 7, 9, 10, 11, 17, 18, 19, 20, 21, 23, 24, 25):
        key = settings.cell(row, 1).value
        write_cell(settings.cell(row, 2), config.get(key))
    write_cell(settings["A2"], "Thông tin cơ sở tại thời điểm xuất từ web.")

    facility = config.get("Tên cơ sở")
    inspector = config.get("Người kiểm tra / lấy mẫu / lưu mẫu")
    manager = config.get("Quản lý xác nhận")
    location = config.get("Địa chỉ / địa điểm kiểm tra")
    report_title = f'{record["day_of_week"]} ngày {report_date:%d/%m/%Y}'
    step1 = wb["MẪU 1 - BƯỚC 1"]
    fresh = [item for item in record["step1"] if item.get("type") != "II"]
    dry = [item for item in record["step1"] if item.get("type") == "II"]
    extra_fresh = write_section(step1, 10, 29, FRESH_FIELDS, fresh)
    extra_dry = write_section(step1, 34 + extra_fresh, 47 + extra_fresh, DRY_FIELDS, dry)
    footer = extra_fresh + extra_dry
    write_cell(step1.cell(54 + footer, 2), inspector)
    write_cell(step1.cell(54 + footer, 13), manager)
    write_cell(step1.cell(55 + footer, 1), "Khối lượng thực nhận theo hồ sơ web của ngày đã chọn.")

    estimate = wb["DỰ TRÙ"]
    ingredients = [item for item in record["estimations"] if item.get("type") != "II"]
    common = [item for item in record["estimations"] if item.get("type") == "II"]
    extra_items = write_section(estimate, 9, 38, ESTIMATE_FIELDS, ingredients)
    extra_common = write_section(estimate, 40 + extra_items, 45 + extra_items, ESTIMATE_FIELDS, common)
    footer = extra_items + extra_common
    write_cell(estimate["A8"], "A. NGUYÊN LIỆU THEO MÓN")
    write_cell(estimate.cell(46 + footer, 1), None)
    estimate.row_dimensions[46 + footer].hidden = True
    for row in range(47 + footer, 62 + footer):
        for column in range(1, 15):
            write_cell(estimate.cell(row, column), None)
        estimate.row_dimensions[row].hidden = True
    write_cell(estimate.cell(62 + footer, 1), "Khối lượng và đánh giá lấy từ bảng Dự trù trên web.")
    write_cell(estimate.cell(69 + footer, 2), inspector)
    write_cell(estimate.cell(69 + footer, 10), manager)

    for sheet, key, fields, footer_row, manager_column in DISH_TABLES:
        ws = wb[sheet]
        extra = write_section(ws, 9, 32, fields, record[key])
        write_cell(ws.cell(footer_row + extra, 2), inspector)
        write_cell(ws.cell(footer_row + extra, manager_column), manager)

    write_labels(wb["MẪU 4 - NHÃN"], record["sampling"], date_str)
    audit = wb["KIỂM TRA"]
    write_cell(audit["A2"], report_title)
    write_section(audit, 4, 27, ("id", "title", "value", "status", "action"), checklist)

    for sheet in (step1, estimate, *(wb[table[0]] for table in DISH_TABLES)):
        for cell, value in (("C1", facility), ("C2", inspector), ("C3", report_title), ("C4", location)):
            write_cell(sheet[cell], value)

    visible = {menu.title, settings.title, step1.title, estimate.title, audit.title,
               "MẪU 4 - NHÃN", *(table[0] for table in DISH_TABLES)}
    for sheet in wb:
        if sheet.title not in visible:
            sheet.sheet_state = "hidden"
            continue
        sheet.data_validations.dataValidation.clear()
        for row in sheet.iter_rows():
            for cell in row:
                if cell.data_type in ("f", "e"):
                    cell.value = None
    for column in range(17, menu.max_column + 1):
        menu.column_dimensions[get_column_letter(column)].hidden = True

    wb.active = wb.index(menu)
    wb.save(output_path)
    return output_path
