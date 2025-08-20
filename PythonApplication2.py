import tkinter as tk
from tkinter import ttk, messagebox
import requests

# Доступные валюты
CURRENCIES = ["USD", "EUR", "RUB", "GBP", "JPY"]

API_URL = "https://api.exchangerate-api.com/v4/latest/{}"  # Бесплатное API

def get_exchange_rates(base):
    try:
        response = requests.get(API_URL.format(base))
        response.raise_for_status()
        data = response.json()
        return data["rates"]
    except requests.RequestException:
        messagebox.showerror("Ошибка сети", "Проблемы с подключением к Интернету или API.")
        return None

def convert():
    try:
        amount = float(amount_entry.get())
    except ValueError:
        messagebox.showerror("Ошибка ввода", "Введите корректное числовое значение суммы.")
        return
    
    from_currency = from_currency_var.get()
    to_currency = to_currency_var.get()
    
    rates = get_exchange_rates(from_currency)
    if rates is None:
        return
    
    if to_currency not in rates:
        messagebox.showerror("Ошибка", f"Курс для {to_currency} недоступен.")
        return
    
    result = amount * rates[to_currency]
    result_var.set(f"{result:.2f} {to_currency}")

def swap_currencies():
    from_curr = from_currency_var.get()
    to_curr = to_currency_var.get()
    from_currency_var.set(to_curr)
    to_currency_var.set(from_curr)

# Создание окна
root = tk.Tk()
root.title("Конвертер валют")

frame = ttk.Frame(root, padding="10")
frame.grid(row=0, column=0)

# Ввод суммы
ttk.Label(frame, text="Сумма:").grid(row=0, column=0, sticky="w")
amount_entry = ttk.Entry(frame)
amount_entry.grid(row=0, column=1, sticky="ew")

# Выбор исходной валюты
ttk.Label(frame, text="Из:").grid(row=1, column=0, sticky="w")
from_currency_var = tk.StringVar(value=CURRENCIES[0])
from_currency_combo = ttk.Combobox(frame, textvariable=from_currency_var, values=CURRENCIES, state="readonly")
from_currency_combo.grid(row=1, column=1, sticky="ew")

# Выбор целевой валюты
ttk.Label(frame, text="В:").grid(row=2, column=0, sticky="w")
to_currency_var = tk.StringVar(value=CURRENCIES[1])
to_currency_combo = ttk.Combobox(frame, textvariable=to_currency_var, values=CURRENCIES, state="readonly")
to_currency_combo.grid(row=2, column=1, sticky="ew")

# Кнопка поменять валюты местами
swap_button = ttk.Button(frame, text="↔", command=swap_currencies)
swap_button.grid(row=1, column=2, padx=5)

# Кнопка конвертировать
convert_button = ttk.Button(frame, text="Конвертировать", command=convert)
convert_button.grid(row=3, column=0, columnspan=3, pady=10, sticky="ew")

# Вывод результата
result_var = tk.StringVar()
result_label = ttk.Label(frame, textvariable=result_var, font=("Arial", 14))
result_label.grid(row=4, column=0, columnspan=3)

# Растяжение колонок
frame.columnconfigure(1, weight=1)

root.mainloop()

