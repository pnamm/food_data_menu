import os
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

from fastapi import FastAPI, HTTPException, Query, Body, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import database
from services.core_logic import (
    extract_main_ingredient,
    determine_sample_type,
    map_ingredient_to_norm_group,
    calculate_daily_estimations,
    generate_daily_auto_fill,
    audit_24_checklist
)
from services.excel_export import export_daily_excel

app = FastAPI(title="Hệ Thống Quản Lý Thực Đơn & Kiểm Thực 3 Bước", version="2.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize DB on startup
database.init_db()

# --- Helper Functions ---
def get_config_dict():
    conn = database.get_connection()
    rows = conn.execute("SELECT key, value FROM system_config").fetchall()
    conn.close()
    return {r["key"]: r["value"] for r in rows}

def get_dishes_cache():
    conn = database.get_connection()
    rows = conn.execute("SELECT name, main_ingredient, sample_type, step1_group, norm_group FROM dishes").fetchall()
    conn.close()
    return {r["name"]: dict(r) for r in rows}

def get_norms_cache():
    conn = database.get_connection()
    rows = conn.execute("SELECT group_name, unit, standard FROM norms").fetchall()
    conn.close()
    return {r["group_name"]: dict(r) for r in rows}

def get_soup_recipes_cache():
    conn = database.get_connection()
    rows = conn.execute("SELECT id, dish, ingredient, category, norm, unit, waste_rate, note FROM soup_recipes ORDER BY dish ASC, id ASC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_suppliers_list():
    conn = database.get_connection()
    rows = conn.execute("SELECT id, name, address, phone, delivery_person FROM suppliers").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_day_name_from_date(date_str: str) -> str:
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    weekday = dt.weekday() # 0 = Monday
    days = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ nhật"]
    return days[weekday]

def get_week_monday(date_str: str) -> str:
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    monday = dt - timedelta(days=dt.weekday())
    return monday.strftime("%Y-%m-%d")

# --- API Endpoints ---

@app.get("/api/config")
def get_config():
    return get_config_dict()

@app.post("/api/config")
def update_config(data: Dict[str, str] = Body(...)):
    conn = database.get_connection()
    for k, v in data.items():
        conn.execute("INSERT OR REPLACE INTO system_config (key, value) VALUES (?, ?)", (k, v))
    conn.commit()
    conn.close()
    return {"status": "success", "message": "Đã lưu cấu hình"}

@app.get("/api/dishes")
def get_dishes():
    conn = database.get_connection()
    rows = conn.execute("SELECT * FROM dishes ORDER BY name ASC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.post("/api/dishes")
def add_dish(data: Dict[str, Any] = Body(...)):
    conn = database.get_connection()
    try:
        conn.execute("""
        INSERT INTO dishes (name, main_ingredient, sample_type, step1_group, norm_group)
        VALUES (?, ?, ?, ?, ?)
        """, (data["name"], data.get("main_ingredient", ""), data.get("sample_type", "Đặc"), data.get("step1_group", "I"), data.get("norm_group", "")))
        conn.commit()
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=400, detail=str(e))
    conn.close()
    return {"status": "success"}

@app.delete("/api/dishes/{dish_id}")
def delete_dish(dish_id: int):
    conn = database.get_connection()
    conn.execute("DELETE FROM dishes WHERE id = ?", (dish_id,))
    conn.commit()
    conn.close()
    return {"status": "success"}

@app.get("/api/suppliers")
def get_suppliers():
    return get_suppliers_list()

@app.post("/api/suppliers")
def save_supplier(data: Dict[str, Any] = Body(...)):
    conn = database.get_connection()
    supp_id = data.get("id")
    if supp_id:
        conn.execute("""
        UPDATE suppliers SET name = ?, address = ?, phone = ?, delivery_person = ? WHERE id = ?
        """, (data["name"], data.get("address", ""), data.get("phone", ""), data.get("delivery_person", ""), supp_id))
    else:
        conn.execute("""
        INSERT INTO suppliers (name, address, phone, delivery_person) VALUES (?, ?, ?, ?)
        """, (data["name"], data.get("address", ""), data.get("phone", ""), data.get("delivery_person", "")))
    conn.commit()
    conn.close()
    return {"status": "success"}

@app.delete("/api/suppliers/{supp_id}")
def delete_supplier(supp_id: int):
    conn = database.get_connection()
    conn.execute("DELETE FROM suppliers WHERE id = ?", (supp_id,))
    conn.commit()
    conn.close()
    return {"status": "success"}

@app.get("/api/norms")
def get_norms():
    conn = database.get_connection()
    rows = conn.execute("SELECT * FROM norms ORDER BY stt ASC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.post("/api/norms")
def update_norm(data: Dict[str, Any] = Body(...)):
    conn = database.get_connection()
    norm_id = data.get("id")
    if norm_id:
        conn.execute("""
        UPDATE norms SET standard = ?, unit = ?, min_val = ?, max_val = ? WHERE id = ?
        """, (data.get("standard"), data.get("unit"), data.get("min_val"), data.get("max_val"), norm_id))
        conn.commit()
    conn.close()
    return {"status": "success"}

@app.get("/api/soup-recipes")
def get_soup_recipes():
    return get_soup_recipes_cache()

@app.post("/api/soup-recipes")
def save_soup_recipe(data: Dict[str, Any] = Body(...)):
    conn = database.get_connection()
    recipe_id = data.get("id")
    if recipe_id:
        conn.execute("""
        UPDATE soup_recipes 
        SET dish = ?, ingredient = ?, category = ?, norm = ?, unit = ?, waste_rate = ?, note = ?
        WHERE id = ?
        """, (data["dish"], data["ingredient"], data.get("category", "Đạm"), data.get("norm", 50), data.get("unit", "g"), data.get("waste_rate", 0), data.get("note", ""), recipe_id))
    else:
        conn.execute("""
        INSERT INTO soup_recipes (dish, ingredient, category, norm, unit, waste_rate, note)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (data["dish"], data["ingredient"], data.get("category", "Đạm"), data.get("norm", 50), data.get("unit", "g"), data.get("waste_rate", 0), data.get("note", "")))
    conn.commit()
    conn.close()
    return {"status": "success", "message": "Đã lưu công thức nguyên liệu món nước"}

@app.delete("/api/soup-recipes/{recipe_id}")
def delete_soup_recipe(recipe_id: int):
    conn = database.get_connection()
    conn.execute("DELETE FROM soup_recipes WHERE id = ?", (recipe_id,))
    conn.commit()
    conn.close()
    return {"status": "success"}

@app.get("/api/soup-config")
def get_soup_config():
    config = get_config_dict()
    bowls_per_kg = float(config.get("Định lượng sợi: số tô/kg", 6))
    return {
        "bowls_per_kg": bowls_per_kg,
        "grams_per_bowl": round(1000.0 / bowls_per_kg, 1),
        "noodle_mapping": [
            {"keyword": "Bánh Canh", "noodle_type": "Bánh canh tươi"},
            {"keyword": "Hủ Tiếu", "noodle_type": "Hủ tiếu sợi tươi"},
            {"keyword": "Phở", "noodle_type": "Bánh phở tươi"},
            {"keyword": "Miến", "noodle_type": "Miến"},
            {"keyword": "Mì", "noodle_type": "Mì trứng tươi"},
            {"keyword": "Bún", "noodle_type": "Bún tươi"}
        ]
    }

@app.post("/api/soup-config")
def update_soup_config(data: Dict[str, Any] = Body(...)):
    bowls = data.get("bowls_per_kg", 6)
    conn = database.get_connection()
    conn.execute("INSERT OR REPLACE INTO system_config (key, value) VALUES (?, ?)", ("Định lượng sợi: số tô/kg", str(bowls)))
    conn.commit()
    conn.close()
    return {"status": "success", "message": "Đã lưu định lượng sợi"}

@app.get("/api/menu/week")
def get_weekly_menu(week_start: Optional[str] = Query(None)):
    if not week_start:
        week_start = get_week_monday(datetime.now().strftime("%Y-%m-%d"))

    conn = database.get_connection()
    rows = conn.execute("SELECT * FROM weekly_menus WHERE week_start_date = ?", (week_start,)).fetchall()
    
    # If this week doesn't have menu yet, fallback to the default template week "2026-11-02"
    if not rows:
        rows = conn.execute("SELECT * FROM weekly_menus WHERE week_start_date = '2026-11-02'").fetchall()

    menu_structure = {
        "Thứ 2": {"lunch": {}, "afternoon": {}, "dinner": {}, "vegetarian_lunch": {}, "vegetarian_afternoon": {}},
        "Thứ 3": {"lunch": {}, "afternoon": {}, "dinner": {}, "vegetarian_lunch": {}, "vegetarian_afternoon": {}},
        "Thứ 4": {"lunch": {}, "afternoon": {}, "dinner": {}, "vegetarian_lunch": {}, "vegetarian_afternoon": {}},
        "Thứ 5": {"lunch": {}, "afternoon": {}, "dinner": {}, "vegetarian_lunch": {}, "vegetarian_afternoon": {}},
        "Thứ 6": {"lunch": {}, "afternoon": {}, "dinner": {}, "vegetarian_lunch": {}, "vegetarian_afternoon": {}},
        "Thứ 7": {"lunch": {}, "afternoon": {}, "dinner": {}, "vegetarian_lunch": {}, "vegetarian_afternoon": {}},
        "Chủ nhật": {"lunch": {}, "afternoon": {}, "dinner": {}, "vegetarian_lunch": {}, "vegetarian_afternoon": {}}
    }

    for r in rows:
        d = r["day_of_week"]
        m = r["meal_type"]
        dt = r["dish_type"]
        if d in menu_structure and m in menu_structure[d]:
            menu_structure[d][m][dt] = r["dish_name"]

    conn.close()
    return {"week_start": week_start, "menu": menu_structure}

@app.post("/api/menu/week")
def save_weekly_menu(data: Dict[str, Any] = Body(...)):
    week_start = data.get("week_start")
    menu = data.get("menu", {})
    if not week_start:
        raise HTTPException(status_code=400, detail="Missing week_start")

    conn = database.get_connection()
    for day_of_week, meals in menu.items():
        for meal_type, dishes_dict in meals.items():
            for dish_type, dish_name in dishes_dict.items():
                conn.execute("""
                INSERT OR REPLACE INTO weekly_menus (week_start_date, day_of_week, meal_type, dish_type, dish_name)
                VALUES (?, ?, ?, ?, ?)
                """, (week_start, day_of_week, meal_type, dish_type, dish_name or ""))
    conn.commit()
    conn.close()
    return {"status": "success", "message": "Đã lưu thực đơn tuần"}

@app.get("/api/portions/{date}")
def get_portions(date: str):
    conn = database.get_connection()
    row = conn.execute("SELECT * FROM daily_portions WHERE date = ?", (date,)).fetchone()
    day_name = get_day_name_from_date(date)
    
    if row:
        res = dict(row)
    else:
        # Defaults
        res = {
            "date": date,
            "day_of_week": day_name,
            "lunch_portions": 300,
            "afternoon_portions": 100,
            "dinner_portions": 200,
            "afternoon_soup_portions": 100,
            "has_overtime": 1,
            "has_dinner": 1
        }
    conn.close()
    return res

@app.post("/api/portions/{date}")
def save_portions(date: str, data: Dict[str, Any] = Body(...)):
    conn = database.get_connection()
    day_name = get_day_name_from_date(date)
    conn.execute("""
    INSERT OR REPLACE INTO daily_portions 
    (date, day_of_week, lunch_portions, afternoon_portions, dinner_portions, afternoon_soup_portions, has_overtime, has_dinner)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        date,
        day_name,
        data.get("lunch_portions", 0),
        data.get("afternoon_portions", 0),
        data.get("dinner_portions", 0),
        data.get("afternoon_soup_portions", 0),
        1 if data.get("has_overtime") else 0,
        1 if data.get("has_dinner") else 0
    ))
    conn.commit()
    conn.close()
    return {"status": "success"}

@app.get("/api/daily/{date}")
def get_daily_record(date: str):
    conn = database.get_connection()
    row = conn.execute("SELECT * FROM daily_records WHERE date = ?", (date,)).fetchone()
    day_name = get_day_name_from_date(date)
    config = get_config_dict()
    
    # If record exists in database
    if row and row["step1_data"] and row["step2_data"]:
        conn.close()
        step1 = json.loads(row["step1_data"])
        step2 = json.loads(row["step2_data"])
        step3 = json.loads(row["step3_data"])
        sampling = json.loads(row["sampling_data"])
        estimations = json.loads(row["estimation_data"])
        
        # Build labels
        facility = config.get("Tên cơ sở", "Công ty TNHH Thương mại Dịch vụ Tân Hồ Tây")
        labels = []
        for s in sampling:
            labels.append({
                "facility_name": facility,
                "ca": s.get("ca", "TRƯA"),
                "date": date,
                "dish_name": s.get("dish_name", ""),
                "sample_time": s.get("time_sampled", "").split(" ")[-1],
                "sampler": s.get("sampler", "")
            })

        return {
            "date": date,
            "day_of_week": day_name,
            "is_saved": True,
            "status": row["status"],
            "step1": step1,
            "step2": step2,
            "step3": step3,
            "sampling": sampling,
            "estimations": estimations,
            "labels": labels
        }
    
    conn.close()

    # Otherwise generate auto-filled data from menu
    week_start = get_week_monday(date)
    week_menu_res = get_weekly_menu(week_start)
    portions = get_portions(date)
    suppliers = get_suppliers_list()
    norms_cache = get_norms_cache()
    soup_cache = get_soup_recipes_cache()
    dishes_cache = get_dishes_cache()

    port_info = {
        "lunch": portions.get("lunch_portions", 300),
        "afternoon": portions.get("afternoon_portions", 100),
        "dinner": portions.get("dinner_portions", 200),
        "afternoon_soup": portions.get("afternoon_soup_portions", 100),
        "has_overtime": bool(portions.get("has_overtime", 1)),
        "has_dinner": bool(portions.get("has_dinner", 1))
    }

    generated = generate_daily_auto_fill(
        date, day_name, week_menu_res["menu"], port_info, suppliers, config, norms_cache, soup_cache, dishes_cache
    )
    generated["is_saved"] = False
    return generated

@app.post("/api/daily/{date}")
def save_daily_record(date: str, data: Dict[str, Any] = Body(...)):
    conn = database.get_connection()
    day_name = get_day_name_from_date(date)
    
    step1_json = json.dumps(data.get("step1", []), ensure_ascii=False)
    step2_json = json.dumps(data.get("step2", []), ensure_ascii=False)
    step3_json = json.dumps(data.get("step3", []), ensure_ascii=False)
    sampling_json = json.dumps(data.get("sampling", []), ensure_ascii=False)
    estimations_json = json.dumps(data.get("estimations", []), ensure_ascii=False)
    
    conn.execute("""
    INSERT OR REPLACE INTO daily_records (date, day_of_week, status, step1_data, step2_data, step3_data, sampling_data, estimation_data, updated_at)
    VALUES (?, ?, 'completed', ?, ?, ?, ?, ?, datetime('now'))
    """, (date, day_name, step1_json, step2_json, step3_json, sampling_json, estimations_json))
    
    conn.commit()
    conn.close()
    return {"status": "success", "message": f"Đã lưu thành công hồ sơ ngày {date}!"}

@app.post("/api/daily/{date}/autofill")
def autofill_daily_record(date: str):
    """
    Sinh lại toàn bộ dữ liệu tự động cho ngày này và lưu luôn vào database
    """
    day_name = get_day_name_from_date(date)
    week_start = get_week_monday(date)
    week_menu_res = get_weekly_menu(week_start)
    portions = get_portions(date)
    suppliers = get_suppliers_list()
    config = get_config_dict()
    norms_cache = get_norms_cache()
    soup_cache = get_soup_recipes_cache()
    dishes_cache = get_dishes_cache()

    port_info = {
        "lunch": portions.get("lunch_portions", 300),
        "afternoon": portions.get("afternoon_portions", 100),
        "dinner": portions.get("dinner_portions", 200),
        "afternoon_soup": portions.get("afternoon_soup_portions", 100),
        "has_overtime": bool(portions.get("has_overtime", 1)),
        "has_dinner": bool(portions.get("has_dinner", 1))
    }

    generated = generate_daily_auto_fill(
        date, day_name, week_menu_res["menu"], port_info, suppliers, config, norms_cache, soup_cache, dishes_cache
    )

    save_daily_record(date, generated)
    generated["is_saved"] = True
    return generated

@app.get("/api/audit/{date}")
def audit_day(date: str):
    record = get_daily_record(date)
    day_name = get_day_name_from_date(date)
    portions = get_portions(date)
    config = get_config_dict()

    port_info = {
        "lunch": portions.get("lunch_portions", 0),
        "afternoon": portions.get("afternoon_portions", 0),
        "dinner": portions.get("dinner_portions", 0),
        "has_overtime": bool(portions.get("has_overtime", 1)),
        "has_dinner": bool(portions.get("has_dinner", 1))
    }

    checklist = audit_24_checklist(
        date,
        day_name,
        port_info,
        record.get("step1", []),
        record.get("step2", []),
        record.get("step3", []),
        record.get("sampling", []),
        record.get("estimations", []),
        config
    )

    passed_count = sum(1 for c in checklist if c["status"] == "OK")
    warn_count = sum(1 for c in checklist if c["status"] in ["CẢNH BÁO", "KHUYẾN NGHỊ", "THÔNG TIN"])
    error_count = sum(1 for c in checklist if c["status"] in ["LỖI", "CHƯA NHẬP"])

    return {
        "date": date,
        "day_of_week": day_name,
        "total_items": len(checklist),
        "passed_count": passed_count,
        "warn_count": warn_count,
        "error_count": error_count,
        "checklist": checklist
    }

@app.get("/api/history")
def get_history():
    conn = database.get_connection()
    rows = conn.execute("SELECT date, day_of_week, status, updated_at FROM daily_records ORDER BY date DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.get("/api/export-excel/{date}")
def download_excel(date: str):
    record = get_daily_record(date)
    export_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "exports")
    os.makedirs(export_dir, exist_ok=True)
    filename = f"Kiem_thuc_{date}.xlsx"
    out_file = os.path.join(export_dir, filename)

    export_daily_excel(date, record, out_file)
    if os.path.exists(out_file):
        return FileResponse(out_file, filename=filename, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    raise HTTPException(status_code=500, detail="Không thể tạo file Excel")

# Mount Static directory
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
def read_index():
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "Hệ thống quản lý thực đơn đang khởi động..."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
