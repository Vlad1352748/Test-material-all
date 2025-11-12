import pandas as pd
import os , sys
import math
import json
import tkinter as tk
from tkinter import ttk, messagebox


# === Шляхи ===

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS  # PyInstaller временная папка
    except AttributeError:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

ICON = resource_path("ico64.ico")

# === Директория для конфигов ===
CONFIG_DIR = os.path.join(os.getenv("APPDATA"), "PrintHUB")
os.makedirs(CONFIG_DIR, exist_ok=True)

# === Базовые шаблоны ===
TEMPLATES = {
    "Академ": {
        "material": [
            {
                "Код": "1",
                "Назва товару": "Офісний папір А4",
                "Кількість (залишок)": 500,
                "Кількість до замовлення": 0,
                "Необхідно": 25000,
                "Упаковка": 1,
                "Пачка": 5,
                "Штука": 500
            },
            {
                "Код": "2",
                "Назва товару": "Офісний папір А3",
                "Кількість (залишок)": 300,
                "Кількість до замовлення": 0,
                "Необхідно": 15000,
                "Упаковка": 1,
                "Пачка": 5,
                "Штука": 500
            }
        ]
    },
    "Аркадія": {"material": []},
    "Дарниця": {"material": []},
    "Почайна": {"material": []},
    "Оазис": {"material": []}
}


# ====== Работа с JSON ======
def get_config_path(branch_name):
    safe_name = branch_name.replace(" ", "_")
    return os.path.join(CONFIG_DIR, f"{safe_name}_file.json")


def ensure_config(branch_name):
    path = get_config_path(branch_name)
    if not os.path.exists(path):
        data = TEMPLATES.get(branch_name, {"material": []})
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    return path


def load_config(branch_name):
    path = ensure_config(branch_name)
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("material", [])
    except Exception as e:
        messagebox.showerror("Помилка", f"Не вдалося зчитати {path}:\n{e}")
        return []


def save_config(branch_name, m_list):
    path = get_config_path(branch_name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"material": m_list}, f, indent=4, ensure_ascii=False)


# ====== Расчёты ======
def check_left(branch_name):
    m = load_config(branch_name)
    kod, nazv, kleft, kbox, kpack, ksht = [], [], [], [], [], []

    for mat in m:
        name = mat.get("Назва товару")
        left = mat.get("Кількість (залишок)", 0)
        need = mat.get("Необхідно", 0)
        box = mat.get("Упаковка", 1)
        pack = mat.get("Пачка", 5)
        shtuk = mat.get("Штука", 100)

        if left < need:
            order1 = math.ceil((need - left) / (pack * shtuk))
            print(order1)
            order2 = order1*pack
            print(order2)
            order3 = order2*shtuk
            print(order3)
            if order1 < pack:
                order1 = box
            if order1 > 0:
                mat["Кількість до замовлення"] = order1
                kod.append(mat.get("Код"))
                nazv.append(name)
                kleft.append(left)
                kbox.append(order1)
                kpack.append(order2)
                ksht.append(order3)

    save_config(branch_name, m)

    if kod:
        df = pd.DataFrame({
            "Код": kod,
            "Назва товару": nazv,
            "Кількість (залишок)": kleft,
            "Замовити - коробок": kbox,
            "Замовити - упаковок": kpack,
            "Замовити - штук": ksht,
        })
        out_path = os.path.join(os.path.expanduser("~/Desktop"), f"{branch_name}.xlsx")
        df.to_excel(out_path, index=False)
        messagebox.showinfo("Готово", f"Таблиця для '{branch_name}' збережена на Робочий стіл!")
    else:
        messagebox.showinfo("Все добре", f"Для '{branch_name}' нічого замовляти не потрібно.")


# ====== Редактирование товаров ======
def open_left(branch_name):
    m_list = load_config(branch_name)
    root = tk.Toplevel()
    root.title(f"Оновити залишки ({branch_name})")
    root.geometry("950x600")

    container = ttk.Frame(root)
    container.pack(fill="both", expand=True)

    canvas = tk.Canvas(container)
    scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas)

    scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    entries = []

    header = ["Код", "Назва товару", "Залишок", "Необхідно", "Упаковка", "Пачка", "Штука"]
    for j, h in enumerate(header):
        tk.Label(scrollable_frame, text=h, font=("Segoe UI", 10, "bold")).grid(row=0, column=j, padx=5, pady=5)

    def refresh_table():
        for widget in scrollable_frame.winfo_children()[len(header):]:
            widget.destroy()
        entries.clear()

        for i, mat in enumerate(m_list):
            row_entries = []
            values = [
                mat.get("Код", ""),
                mat.get("Назва товару", ""),
                mat.get("Кількість (залишок)", 0),
                mat.get("Необхідно", 0),
                mat.get("Упаковка", 1),
                mat.get("Пачка", 1),
                mat.get("Штука", 1)
            ]
            for j, val in enumerate(values):
                if j == 1:
                    a = 25
                elif j == 2 or j == 3:
                    a = 15
                else:
                    a = 7
                e = tk.Entry(scrollable_frame, width=a)
                e.insert(0, val)
                e.grid(row=i+1, column=j, padx=3, pady=3)
                row_entries.append(e)

            # кнопка удаления
            btn_del = tk.Button(scrollable_frame, text="🗑", command=lambda idx=i: delete_item(idx))
            btn_del.grid(row=i+1, column=len(values), padx=3)
            entries.append(row_entries)

    def delete_item(index):
        if 0 <= index < len(m_list):
            del m_list[index]
            refresh_table()

    def add_item():
        new_item = {
            "Код": str(len(m_list) + 1),
            "Назва товару": "Новий товар",
            "Кількість (залишок)": 0,
            "Кількість до замовлення": 0,
            "Необхідно": 0,
            "Упаковка": 1,
            "Пачка": 1,
            "Штука": 1
        }
        m_list.append(new_item)
        refresh_table()

    def save_all():
        for i, row in enumerate(entries):
            try:
                m_list[i]["Код"] = str(row[0].get())
                m_list[i]["Назва товару"] = row[1].get()
                m_list[i]["Кількість (залишок)"] = int(row[2].get())
                m_list[i]["Необхідно"] = int(row[3].get())
                m_list[i]["Упаковка"] = int(row[4].get())
                m_list[i]["Пачка"] = int(row[5].get())
                m_list[i]["Штука"] = int(row[6].get())
            except ValueError:
                messagebox.showerror("Помилка", "Будь ласка, введіть лише числа у відповідні поля.")
                return

        save_config(branch_name, m_list)
        messagebox.showinfo("✅ Успішно", f"Дані для '{branch_name}' збережено!")
        root.destroy()

    refresh_table()

    bottom = ttk.Frame(root)
    bottom.pack(pady=10)
    ttk.Button(bottom, text="➕ Додати товар", command=add_item).pack(side="left", padx=5)
    ttk.Button(bottom, text="💾 Зберегти всі", command=save_all).pack(side="left", padx=5)

    root.mainloop()


# ====== Главное окно ======
def main_window():
    root = tk.Tk()
    root.title("Відстежити залишки")
    root.iconbitmap(ICON)

    frame = ttk.Frame(root, padding=10)
    frame.pack(fill="both", expand=True)

    tk.Label(frame, text="Відстежити залишки відділення:", font=("Arial", 14, "bold")).pack(pady=(0, 15))

    selected = tk.StringVar(value="Академ")

    options = ["Академ", "Аркадія", "Дарниця", "Почайна", "Оазис"]
    row_frame = ttk.Frame(frame)
    row_frame.pack(anchor="center")

    for t in options:
        ttk.Radiobutton(row_frame, text=t, value=t, variable=selected).pack(side="left", padx=5)

    tk.Button(frame, text="📦 Замовити необхідне", width=30,
              command=lambda: check_left(selected.get())).pack(pady=5)

    tk.Button(frame, text="✏️ Змінити залишок",
              command=lambda: open_left(selected.get()), width=20).pack(pady=10)

    root.mainloop()


if __name__ == "__main__":
    main_window()
