import sqlite3
import os
import json
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "menu_sampling.db")
SEED_DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "extracted_master_data.json")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # 1. System Config
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS system_config (
        key TEXT PRIMARY KEY,
        value TEXT,
        description TEXT
    )
    """)

    # 2. Suppliers
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS suppliers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        address TEXT,
        phone TEXT,
        delivery_person TEXT
    )
    """)

    # 3. Dishes
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS dishes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        main_ingredient TEXT,
        sample_type TEXT DEFAULT 'Đặc',
        step1_group TEXT DEFAULT 'I',
        norm_group TEXT
    )
    """)

    # 4. Norms (Định mức)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS norms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        stt INTEGER,
        group_name TEXT NOT NULL UNIQUE,
        unit TEXT DEFAULT 'g',
        apply_to TEXT,
        min_val REAL,
        max_val REAL,
        standard REAL
    )
    """)

    # 5. Soup Recipes (Công thức món nước)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS soup_recipes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dish TEXT NOT NULL,
        ingredient TEXT NOT NULL,
        category TEXT,
        norm REAL,
        unit TEXT DEFAULT 'g',
        waste_rate REAL DEFAULT 0,
        note TEXT
    )
    """)

    # 6. Weekly Menus (Lưu theo tuần: week_start_date: YYYY-MM-DD là Thứ 2)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS weekly_menus (
        week_start_date TEXT NOT NULL,
        day_of_week TEXT NOT NULL, -- 'Thứ 2', 'Thứ 3', ...
        meal_type TEXT NOT NULL,   -- 'lunch', 'afternoon', 'dinner', 'vegetarian_lunch', 'vegetarian_afternoon'
        dish_type TEXT NOT NULL,   -- 'main', 'sub', 'stir', 'soup', 'dessert', 'soup_dish'
        dish_name TEXT,
        PRIMARY KEY (week_start_date, day_of_week, meal_type, dish_type)
    )
    """)

    # 7. Daily Portions (Số suất & tăng ca theo ngày)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS daily_portions (
        date TEXT PRIMARY KEY, -- YYYY-MM-DD
        day_of_week TEXT,      -- 'Thứ 2', 'Thứ 3', ...
        lunch_portions INTEGER DEFAULT 0,
        afternoon_portions INTEGER DEFAULT 0,
        dinner_portions INTEGER DEFAULT 0,
        afternoon_soup_portions INTEGER DEFAULT 0,
        has_overtime INTEGER DEFAULT 1,
        has_dinner INTEGER DEFAULT 1
    )
    """)

    # 8. Daily Records (Chi tiết kiểm thực & lưu mẫu theo từng ngày)
    # Lưu JSON chứa chi tiết các bước Step1, Step2, Step3, Sampling (Mẫu 5), Estimation (Dự trù)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS daily_records (
        date TEXT PRIMARY KEY, -- YYYY-MM-DD
        day_of_week TEXT,
        status TEXT DEFAULT 'draft',
        step1_data TEXT, -- JSON
        step2_data TEXT, -- JSON
        step3_data TEXT, -- JSON
        sampling_data TEXT, -- JSON (Mẫu 5)
        estimation_data TEXT, -- JSON (Dự trù & thực nhận)
        updated_at TEXT
    )
    """)

    conn.commit()

    # Kiểm tra xem đã có dữ liệu ban đầu chưa
    cursor.execute("SELECT COUNT(*) FROM dishes")
    dish_count = cursor.fetchone()[0]

    if dish_count == 0 and os.path.exists(SEED_DATA_PATH):
        print("Seeding initial data from extracted JSON...")
        with open(SEED_DATA_PATH, "r", encoding="utf-8") as f:
            seed = json.load(f)

        # Config
        for k, v in seed.get("config", {}).items():
            if k:
                cursor.execute("INSERT OR REPLACE INTO system_config (key, value) VALUES (?, ?)", (k, v))
        
        # Suppliers
        for s in seed.get("suppliers", []):
            cursor.execute("""
            INSERT INTO suppliers (name, address, phone, delivery_person)
            VALUES (?, ?, ?, ?)
            """, (s["name"], s.get("address", ""), s.get("phone", ""), s.get("delivery_person", "")))

        # Dishes
        for d in seed.get("dishes", []):
            cursor.execute("""
            INSERT OR IGNORE INTO dishes (name, main_ingredient, sample_type, step1_group, norm_group)
            VALUES (?, ?, ?, ?, ?)
            """, (d["name"], d.get("main_ingredient", ""), d.get("sample_type", "Đặc"), d.get("step1_group", "I"), d.get("norm_group", "")))

        # Norms
        for n in seed.get("norms", []):
            cursor.execute("""
            INSERT OR IGNORE INTO norms (stt, group_name, unit, apply_to, min_val, max_val, standard)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (n.get("stt"), n["group"], n.get("unit", "g"), n.get("apply_to", ""), n.get("min"), n.get("max"), n.get("standard")))

        # Soup Recipes
        for sr in seed.get("soup_recipes", []):
            cursor.execute("""
            INSERT INTO soup_recipes (dish, ingredient, category, norm, unit, waste_rate, note)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (sr["dish"], sr["ingredient"], sr.get("category", ""), sr.get("norm"), sr.get("unit", "g"), sr.get("waste_rate", 0), sr.get("note", "")))

        # Default weekly menu (Week 2026-11-02)
        default_week = "2026-11-02"
        weekly_menu = seed.get("weekly_menu", {})
        for day_name, meals in weekly_menu.items():
            for meal_type, dishes_dict in meals.items():
                for dish_type, dish_name in dishes_dict.items():
                    if dish_name:
                        cursor.execute("""
                        INSERT OR REPLACE INTO weekly_menus (week_start_date, day_of_week, meal_type, dish_type, dish_name)
                        VALUES (?, ?, ?, ?, ?)
                        """, (default_week, day_name, meal_type, dish_type, dish_name))

        # Default portions
        portions = seed.get("portions", {})
        day_dates = {
            "Thứ 2": "2026-11-02",
            "Thứ 3": "2026-11-03",
            "Thứ 4": "2026-11-04",
            "Thứ 5": "2026-11-05",
            "Thứ 6": "2026-11-06",
            "Thứ 7": "2026-11-07",
            "Chủ nhật": "2026-11-08"
        }
        for day_name, port_data in portions.items():
            dt = day_dates.get(day_name)
            if dt:
                cursor.execute("""
                INSERT OR REPLACE INTO daily_portions (date, day_of_week, lunch_portions, afternoon_portions, dinner_portions, afternoon_soup_portions, has_overtime, has_dinner)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    dt,
                    day_name,
                    port_data.get("lunch", 0),
                    port_data.get("afternoon", 0),
                    port_data.get("dinner", 0),
                    port_data.get("afternoon_soup", 0),
                    1 if port_data.get("overtime") else 0,
                    1 if port_data.get("has_dinner") else 0
                ))

        conn.commit()
        print("Database initialized and seeded successfully!")

    conn.close()

if __name__ == "__main__":
    init_db()
