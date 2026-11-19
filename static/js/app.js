const { createApp, ref, computed, onMounted, watch } = Vue;

const createEmptyWeeklyMenu = () => {
  const res = {};
  const days = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ nhật"];
  for (const d of days) {
    res[d] = {
      lunch: { main: "", sub: "", sub2: "", stir: "", soup: "", dessert: "" },
      afternoon: { main: "", sub: "", sub2: "", stir: "", soup: "", dessert: "", soup_dish: "" },
      dinner: { main: "", sub: "", sub2: "", stir: "", soup: "", dessert: "" },
      vegetarian_lunch: { main: "", sub: "", stir: "", soup: "" },
      vegetarian_afternoon: { main: "", sub: "", stir: "", soup: "" }
    };
  }
  return res;
};

createApp({
  setup() {
    // Current date selection
    const selectedDate = ref("2026-11-02");
    const currentTab = ref("dashboard");
    const isLoading = ref(true);
    const loadedDate = ref("");
    const toast = ref({ show: false, message: "", type: "success" });

    // Core Data
    const config = ref({
      "Tên cơ sở": "Công ty TNHH Thương mại Dịch vụ Tân Hồ Tây",
      "Địa chỉ / địa điểm kiểm tra": "Thửa đất số 44, Tờ bản đồ số 11, Đường Hùng Vương, Tổ 12, Khu phố Rạch Bắp, Phường Tây Nam, Thành phố Hồ Chí Minh, Việt Nam",
      "Điện thoại": "0913 144 74",
      "Người kiểm tra / lấy mẫu / lưu mẫu": "NGUYỄN VĂN QUYỆN",
      "Người hủy mẫu": "TRẦN VĂN HẢI",
      "Nhiệt độ bảo quản mẫu": "5°C",
      "Khối lượng mẫu thức ăn đặc (g)": "100",
      "Thể tích mẫu thức ăn lỏng (ml)": "150",
      "Thời gian lưu mẫu tối thiểu (giờ)": "24",
      "Dung sai định lượng cho phép (± %)": "5"
    });

    const dailyData = ref({
      is_saved: false,
      estimations: [],
      step1: [],
      step2: [],
      step3: [],
      sampling: [],
      labels: []
    });

    const portions = ref({
      lunch_portions: 300,
      afternoon_portions: 100,
      dinner_portions: 200,
      afternoon_soup_portions: 100,
      has_overtime: true,
      has_dinner: true
    });

    const weeklyMenu = ref(createEmptyWeeklyMenu());
    const weekStartDate = ref("");
    const dishes = ref([]);
    const suppliers = ref([]);
    const norms = ref([]);
    const auditData = ref({
      passed_count: 24,
      warn_count: 0,
      error_count: 0,
      checklist: []
    });
    const historyList = ref([]);

    // Soup recipes data
    const soupRecipes = ref([]);
    const soupConfig = ref({
      bowls_per_kg: 6,
      grams_per_bowl: 166.7,
      noodle_mapping: []
    });
    const selectedSoupDish = ref("ALL");
    const newSoupIngredient = ref({
      dish: "Hủ Tiếu",
      ingredient: "",
      category: "Đạm",
      norm: 50,
      unit: "g",
      waste_rate: 0,
      note: ""
    });

    // UI state for search/modals
    const dishSearchQuery = ref("");
    const newDish = ref({ name: "", main_ingredient: "", sample_type: "Đặc", step1_group: "I", norm_group: "" });
    const newSupplier = ref({ name: "", address: "", phone: "", delivery_person: "" });
    const labelFilterCa = ref("ALL");

    // Days list
    const daysOfWeek = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ nhật"];

    const showToast = (message, type = "success") => {
      toast.value = { show: true, message, type };
      setTimeout(() => { toast.value.show = false; }, 3500);
    };

    // Calculate day name
    const currentDayName = computed(() => {
      if (!selectedDate.value) return "Thứ 2";
      const d = new Date(selectedDate.value);
      const dayIndex = (d.getUTCDay() + 6) % 7; // Monday = 0
      return daysOfWeek[dayIndex] || "Thứ 2";
    });

    // Today's afternoon soup dish
    const todaySoupDish = computed(() => {
      const d = currentDayName.value;
      if (weeklyMenu.value[d] && weeklyMenu.value[d].afternoon) {
        return weeklyMenu.value[d].afternoon.soup_dish || "";
      }
      return "";
    });

    // Unique list of soup dishes
    const soupDishesList = computed(() => {
      const set = new Set();
      soupRecipes.value.forEach(r => { if (r.dish) set.add(r.dish); });
      return Array.from(set).sort();
    });

    // Filtered soup recipes
    const filteredSoupRecipes = computed(() => {
      if (selectedSoupDish.value === "ALL") return soupRecipes.value;
      return soupRecipes.value.filter(r => r.dish === selectedSoupDish.value);
    });

    // Filtered dishes
    const filteredDishes = computed(() => {
      if (!dishSearchQuery.value) return dishes.value;
      const q = dishSearchQuery.value.toLowerCase();
      return dishes.value.filter(d => d.name.toLowerCase().includes(q) || (d.main_ingredient && d.main_ingredient.toLowerCase().includes(q)));
    });

    // Total Portions
    const totalDayPortions = computed(() => {
      const l = parseInt(portions.value.lunch_portions || 0);
      const a = portions.value.has_overtime ? parseInt(portions.value.afternoon_portions || 0) : 0;
      const d = portions.value.has_dinner ? parseInt(portions.value.dinner_portions || 0) : 0;
      return l + a + d;
    });

    // Filtered labels (Mẫu 4)
    const filteredLabels = computed(() => {
      if (!dailyData.value.labels) return [];
      if (labelFilterCa.value === "ALL") return dailyData.value.labels;
      return dailyData.value.labels.filter(l => l.ca === labelFilterCa.value);
    });

    // --- API Calls ---

    const loadConfig = async () => {
      try {
        const res = await fetch("/api/config");
        if (res.ok) {
          const data = await res.json();
          config.value = { ...config.value, ...data };
        }
      } catch (err) {
        console.error("Lỗi tải cấu hình:", err);
      }
    };

    const loadDishes = async () => {
      try {
        const res = await fetch("/api/dishes");
        if (res.ok) dishes.value = await res.json();
      } catch (err) {
        console.error("Lỗi tải món:", err);
      }
    };

    const loadSuppliers = async () => {
      try {
        const res = await fetch("/api/suppliers");
        if (res.ok) suppliers.value = await res.json();
      } catch (err) {
        console.error("Lỗi tải NCC:", err);
      }
    };

    const loadNorms = async () => {
      try {
        const res = await fetch("/api/norms");
        if (res.ok) norms.value = await res.json();
      } catch (err) {
        console.error("Lỗi tải định mức:", err);
      }
    };

    const loadSoupRecipes = async () => {
      try {
        const res = await fetch("/api/soup-recipes");
        if (res.ok) soupRecipes.value = await res.json();
      } catch (err) {
        console.error("Lỗi tải công thức món nước:", err);
      }
    };

    const loadSoupConfig = async () => {
      try {
        const res = await fetch("/api/soup-config");
        if (res.ok) soupConfig.value = await res.json();
      } catch (err) {
        console.error("Lỗi tải định lượng sợi:", err);
      }
    };

    const getWeekStart = (date) => {
      const monday = new Date(date);
      monday.setUTCDate(monday.getUTCDate() - (monday.getUTCDay() + 6) % 7);
      return monday.toISOString().slice(0, 10);
    };

    const loadWeeklyMenu = async (weekStart) => {
      try {
        const res = await fetch(`/api/menu/week?week_start=${weekStart}`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        const base = createEmptyWeeklyMenu();
        if (data.menu) {
          for (const d of daysOfWeek) {
            if (data.menu[d]) {
              base[d] = {
                lunch: { ...base[d].lunch, ...data.menu[d].lunch },
                afternoon: { ...base[d].afternoon, ...data.menu[d].afternoon },
                dinner: { ...base[d].dinner, ...data.menu[d].dinner },
                vegetarian_lunch: { ...base[d].vegetarian_lunch, ...data.menu[d].vegetarian_lunch },
                vegetarian_afternoon: { ...base[d].vegetarian_afternoon, ...data.menu[d].vegetarian_afternoon }
              };
            }
          }
        }
        weeklyMenu.value = base;
        if (data.week_start) weekStartDate.value = data.week_start;
      } catch (err) {
        weeklyMenu.value = createEmptyWeeklyMenu();
        weekStartDate.value = "";
        showToast("Lỗi tải thực đơn tuần: " + err.message, "danger");
      }
    };

    const loadPortions = async (date) => {
      const res = await fetch(`/api/portions/${date}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      portions.value = {
        ...data,
        has_overtime: Boolean(data.has_overtime),
        has_dinner: Boolean(data.has_dinner)
      };
    };

    const loadDailyRecord = async (date) => {
      isLoading.value = true;
      loadedDate.value = "";
      auditData.value = null;
      try {
        const weekStart = getWeekStart(date);
        if (weekStartDate.value !== weekStart) await loadWeeklyMenu(weekStart);
        await loadPortions(date);
        const res = await fetch(`/api/daily/${date}`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        dailyData.value = await res.json();
        loadedDate.value = date;
        await runAudit(date);
      } catch (err) {
        dailyData.value = { is_saved: false, estimations: [], step1: [], step2: [], step3: [], sampling: [], labels: [] };
        showToast("Lỗi tải hồ sơ ngày: " + err.message, "danger");
      } finally {
        isLoading.value = false;
      }
    };

    const runAudit = async (date) => {
      try {
        const res = await fetch(`/api/audit/${date}`);
        if (res.ok) {
          auditData.value = await res.json();
        }
      } catch (err) {
        console.error("Lỗi kiểm tra an toàn:", err);
      }
    };

    const loadHistory = async () => {
      try {
        const res = await fetch("/api/history");
        if (res.ok) historyList.value = await res.json();
      } catch (err) {
        console.error("Lỗi tải lịch sử:", err);
      }
    };

    // --- Actions ---

    const changeDate = (days) => {
      const d = new Date(selectedDate.value);
      d.setUTCDate(d.getUTCDate() + days);
      selectedDate.value = d.toISOString().split("T")[0];
    };

    const triggerAutoFill = async () => {
      if (dailyData.value.is_saved && !confirm("Điền tự động sẽ thay thế hồ sơ đã lưu của ngày này. Bạn muốn tiếp tục?")) return;
      isLoading.value = true;
      try {
        const res = await fetch(`/api/daily/${selectedDate.value}/autofill`, { method: "POST" });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        dailyData.value = {
          is_saved: true,
          estimations: data.estimations || [],
          step1: data.step1 || [],
          step2: data.step2 || [],
          step3: data.step3 || [],
          sampling: data.sampling || [],
          labels: data.labels || []
        };
        await runAudit(selectedDate.value);
        await loadHistory();
        showToast("Đã tạo và lưu hồ sơ từ thực đơn tuần.", "success");
      } catch (err) {
        showToast("Lỗi khi tự động điền: " + err.message, "danger");
      } finally {
        isLoading.value = false;
      }
    };

    const saveDailyRecord = async () => {
      isLoading.value = true;
      try {
        // Save daily record
        const res = await fetch(`/api/daily/${selectedDate.value}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(dailyData.value)
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const result = await res.json();
        dailyData.value.is_saved = true;
        await runAudit(selectedDate.value);
        await loadHistory();
        showToast(result.message || "Đã lưu hồ sơ thành công!", "success");
      } catch (err) {
        showToast("Lỗi lưu hồ sơ: " + err.message, "danger");
      } finally {
        isLoading.value = false;
      }
    };

    const saveSelectedPortions = async () => {
      isLoading.value = true;
      try {
        const res = await fetch(`/api/portions/${selectedDate.value}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(portions.value)
        });
        if (!res.ok) {
          const error = await res.json();
          throw new Error(error.detail || `HTTP ${res.status}`);
        }
        if (!dailyData.value.is_saved) {
          await loadDailyRecord(selectedDate.value);
        } else {
          await runAudit(selectedDate.value);
        }
        showToast("Đã lưu số suất và ca.");
      } catch (err) {
        showToast("Lỗi lưu số suất: " + err.message, "danger");
      } finally {
        isLoading.value = false;
      }
    };

    const saveWeeklyMenu = async () => {
      isLoading.value = true;
      try {
        const res = await fetch("/api/menu/week", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            week_start: weekStartDate.value,
            menu: weeklyMenu.value
          })
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const result = await res.json();
        showToast(result.message || "Đã lưu thực đơn tuần thành công!", "success");
        if (!dailyData.value.is_saved) await loadDailyRecord(selectedDate.value);
      } catch (err) {
        showToast("Lỗi lưu thực đơn: " + err.message, "danger");
      } finally {
        isLoading.value = false;
      }
    };

    const saveConfig = async () => {
      try {
        const res = await fetch("/api/config", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(config.value)
        });
        if (res.ok) {
          const result = await res.json();
          showToast(result.message || "Đã lưu cấu hình", "success");
        }
      } catch (err) {
        showToast("Lỗi: " + err.message, "danger");
      }
    };

    const updateActualReceived = (item, val) => {
      const num = parseFloat(val) || 0;
      item.actual_received = num;
      if (item.need_amount > 0) {
        const diff = (num - item.need_amount) / item.need_amount;
        item.diff_percent = Math.round(diff * 1000) / 10;
        const tolerance = parseFloat(config.value["Dung sai định lượng cho phép (± %)"] || 5);
        if (Math.abs(item.diff_percent) <= tolerance) {
          item.evaluation = "✓ Trong dung sai";
        } else {
          item.evaluation = diff > 0 ? `⚠ Thừa ${Math.abs(item.diff_percent)}%` : `⚠ Thiếu ${Math.abs(item.diff_percent)}%`;
        }
      }
    };

    const exportExcel = () => {
      window.open(`/api/export-excel/${selectedDate.value}`, "_blank");
    };

    const printCurrent = () => {
      window.print();
    };

    // Dish CRUD
    const addDish = async () => {
      if (!newDish.value.name.trim()) return;
      try {
        const res = await fetch("/api/dishes", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(newDish.value)
        });
        if (res.ok) {
          showToast(`Đã thêm món "${newDish.value.name}"`);
          newDish.value = { name: "", main_ingredient: "", sample_type: "Đặc", step1_group: "I", norm_group: "" };
          await loadDishes();
        }
      } catch (err) {
        showToast("Lỗi thêm món: " + err.message, "danger");
      }
    };

    const deleteDish = async (id, name) => {
      if (!confirm(`Bạn có chắc muốn xóa món "${name}"?`)) return;
      try {
        const res = await fetch(`/api/dishes/${id}`, { method: "DELETE" });
        if (res.ok) {
          showToast(`Đã xóa món "${name}"`);
          await loadDishes();
        }
      } catch (err) {
        showToast("Lỗi xóa: " + err.message, "danger");
      }
    };

    // Supplier CRUD
    const saveSupplier = async () => {
      if (!newSupplier.value.name.trim()) return;
      try {
        const res = await fetch("/api/suppliers", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(newSupplier.value)
        });
        if (res.ok) {
          showToast(`Đã lưu nhà cung cấp`);
          newSupplier.value = { name: "", address: "", phone: "", delivery_person: "" };
          await loadSuppliers();
        }
      } catch (err) {
        showToast("Lỗi: " + err.message, "danger");
      }
    };

    const deleteSupplier = async (id, name) => {
      if (!confirm(`Bạn có chắc muốn xóa nhà cung cấp "${name}"?`)) return;
      try {
        const res = await fetch(`/api/suppliers/${id}`, { method: "DELETE" });
        if (res.ok) {
          showToast(`Đã xóa nhà cung cấp`);
          await loadSuppliers();
        }
      } catch (err) {
        showToast("Lỗi: " + err.message, "danger");
      }
    };

    // Soup recipes CRUD
    const saveSoupRecipe = async (item) => {
      try {
        const res = await fetch("/api/soup-recipes", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(item)
        });
        if (res.ok) {
          showToast(`Đã cập nhật định mức ${item.ingredient} (${item.dish})`);
        }
      } catch (err) {
        showToast("Lỗi lưu: " + err.message, "danger");
      }
    };

    const saveNewSoupIngredient = async () => {
      if (!newSoupIngredient.value.dish.trim() || !newSoupIngredient.value.ingredient.trim()) {
        showToast("Vui lòng điền tên món nước và tên nguyên liệu", "danger");
        return;
      }
      try {
        const res = await fetch("/api/soup-recipes", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(newSoupIngredient.value)
        });
        if (res.ok) {
          showToast(`Đã thêm ${newSoupIngredient.value.ingredient} vào món ${newSoupIngredient.value.dish}`);
          newSoupIngredient.value.ingredient = "";
          newSoupIngredient.value.note = "";
          await loadSoupRecipes();
        }
      } catch (err) {
        showToast("Lỗi thêm: " + err.message, "danger");
      }
    };

    const deleteSoupIngredient = async (id, dish, ingredient) => {
      if (!confirm(`Bạn có chắc muốn xóa nguyên liệu "${ingredient}" khỏi món "${dish}"?`)) return;
      try {
        const res = await fetch(`/api/soup-recipes/${id}`, { method: "DELETE" });
        if (res.ok) {
          showToast(`Đã xóa "${ingredient}"`);
          await loadSoupRecipes();
        }
      } catch (err) {
        showToast("Lỗi: " + err.message, "danger");
      }
    };

    const updateSoupConfig = async () => {
      try {
        const res = await fetch("/api/soup-config", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ bowls_per_kg: soupConfig.value.bowls_per_kg })
        });
        if (res.ok) {
          soupConfig.value.grams_per_bowl = Math.round((1000.0 / soupConfig.value.bowls_per_kg) * 10) / 10;
          showToast("Đã lưu định lượng sợi!");
        }
      } catch (err) {
        showToast("Lỗi: " + err.message, "danger");
      }
    };

    // Watch date change
    watch(selectedDate, loadDailyRecord);

    onMounted(async () => {
      await loadConfig();
      await loadDishes();
      await loadSuppliers();
      await loadNorms();
      await loadSoupRecipes();
      await loadSoupConfig();
      await loadDailyRecord(selectedDate.value);
      await loadHistory();
    });

    return {
      selectedDate,
      currentTab,
      isLoading,
      loadedDate,
      toast,
      config,
      dailyData,
      portions,
      weeklyMenu,
      weekStartDate,
      dishes,
      suppliers,
      norms,
      auditData,
      historyList,
      soupRecipes,
      soupConfig,
      selectedSoupDish,
      newSoupIngredient,
      soupDishesList,
      filteredSoupRecipes,
      todaySoupDish,
      daysOfWeek,
      currentDayName,
      totalDayPortions,
      dishSearchQuery,
      filteredDishes,
      newDish,
      newSupplier,
      labelFilterCa,
      filteredLabels,
      changeDate,
      triggerAutoFill,
      saveDailyRecord,
      saveWeeklyMenu,
      saveSelectedPortions,
      saveConfig,
      updateActualReceived,
      exportExcel,
      printCurrent,
      addDish,
      deleteDish,
      saveSupplier,
      deleteSupplier,
      saveSoupRecipe,
      saveNewSoupIngredient,
      deleteSoupIngredient,
      updateSoupConfig,
      loadDailyRecord
    };
  }
}).mount("#app");
