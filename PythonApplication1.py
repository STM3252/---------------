import sys
import json
import requests
from datetime import datetime, timedelta
import pandas as pd

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QTabWidget,
                             QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
                             QComboBox, QLineEdit, QTableWidget, QTableWidgetItem,
                             QMessageBox, QHeaderView, QAbstractItemView)
from PyQt6.QtCore import QTimer

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class CurrencyConverterApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Сложный Конвертер Валют")
        self.resize(700, 500)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Инициализация вкладок
        self.converter_tab = ConverterTab()
        self.history_tab = HistoryTab()
        self.graph_tab = GraphTab()

        self.tabs.addTab(self.converter_tab, "Конвертер")
        self.tabs.addTab(self.history_tab, "История")
        self.tabs.addTab(self.graph_tab, "График")

        # Связь для обновления графика после конвертаций
        self.converter_tab.conversion_done.connect(self.update_history_graph)

    def update_history_graph(self):
        self.history_tab.load_history()
        self.graph_tab.plot(self.history_tab.get_rates_for_graph())

# Далее – классы для каждой вкладки, история и график

# Пример класса конвертера с сигналом конвертации
from PyQt6.QtCore import pyqtSignal

class ConverterTab(QWidget):
    conversion_done = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.history_file = "history.json"
        self.load_rates()

    def init_ui(self):
        layout = QVBoxLayout()

        hlayout1 = QHBoxLayout()
        self.amount_input = QLineEdit()
        self.from_currency = QComboBox()
        self.from_currency.addItems(['USD','EUR','RUB','GBP','JPY'])
        self.to_currency = QComboBox()
        self.to_currency.addItems(['USD','EUR','RUB','GBP','JPY'])

        hlayout1.addWidget(QLabel("Сумма:"))
        hlayout1.addWidget(self.amount_input)
        hlayout1.addWidget(QLabel("Из:"))
        hlayout1.addWidget(self.from_currency)
        swap_btn = QPushButton("↔")
        swap_btn.clicked.connect(self.swap_currencies)
        hlayout1.addWidget(swap_btn)
        hlayout1.addWidget(QLabel("В:"))
        hlayout1.addWidget(self.to_currency)

        layout.addLayout(hlayout1)

        self.result_label = QLabel("")
        layout.addWidget(self.result_label)

        convert_btn = QPushButton("Конвертировать")
        convert_btn.clicked.connect(self.convert_currency)
        layout.addWidget(convert_btn)

        self.setLayout(layout)

    def load_rates(self):
        # Получаем актуальные курсы (например, с open.er-api.com)
        base = self.from_currency.currentText()
        url = f"https://open.er-api.com/v6/latest/{base}"
        try:
            r = requests.get(url, timeout=5)
            data = r.json()
            if data['result'] == "success":
                self.rates = data["rates"]
            else:
                self.rates = None
                QMessageBox.warning(self, "Ошибка API", "Не удалось получить курсы валют.")
        except Exception:
            self.rates = None
            QMessageBox.warning(self, "Ошибка", "Ошибка соединения с интернетом")

    def convert_currency(self):
        if not self.rates:
            self.load_rates()
            if not self.rates:
                return
        try:
            amount = float(self.amount_input.text().replace(',','.'))
            if amount < 0:
                raise ValueError()
        except ValueError:
            QMessageBox.warning(self, "Ошибка ввода", "Введите корректное положительное число")
            return

        to_cur = self.to_currency.currentText()
        rate = self.rates.get(to_cur)
        if not rate:
            QMessageBox.warning(self, "Ошибка", "Курс для выбранной валюты недоступен")
            return

        result = amount * rate
        self.result_label.setText(f"{amount} {self.from_currency.currentText()} = {result:.4f} {to_cur}")

        # Сохраняем в историю
        self.save_history(amount, self.from_currency.currentText(), to_cur, result)
        self.conversion_done.emit()

    def save_history(self, amount, from_cur, to_cur, result):
        entry = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "amount": amount,
            "from_currency": from_cur,
            "to_currency": to_cur,
            "result": result
        }
        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                history = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            history = []
        history.append(entry)
        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=4)

    def swap_currencies(self):
        from_curr = self.from_currency.currentText()
        to_curr = self.to_currency.currentText()
        self.from_currency.setCurrentText(to_curr)
        self.to_currency.setCurrentText(from_curr)
        self.result_label.clear()

class HistoryTab(QWidget):
    def __init__(self):
        super().__init__()
        self.history_file = "history.json"
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Дата", "Сумма", "Из валюты", "В валюту", "Результат"])
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск по истории (введите валюту или дату)")
        self.search_input.textChanged.connect(self.search_history)
        layout.addWidget(self.search_input)

        self.setLayout(layout)
        self.load_history()

    def load_history(self):
        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                self.history = json.load(f)
        except:
            self.history = []

        self.display_history(self.history)

    def display_history(self, data):
        self.table.setRowCount(0)
        for entry in reversed(data):
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(entry.get("date", "")))
            self.table.setItem(row, 1, QTableWidgetItem(str(entry.get("amount", ""))))
            self.table.setItem(row, 2, QTableWidgetItem(entry.get("from_currency", "")))
            self.table.setItem(row, 3, QTableWidgetItem(entry.get("to_currency", "")))
            self.table.setItem(row, 4, QTableWidgetItem(f"{entry.get('result', ''):.4f}"))

    def search_history(self, text):
        filtered = [e for e in self.history if text.lower() in str(e).lower()]
        self.display_history(filtered)

    def get_rates_for_graph(self):
        # Для графика можно агрегировать из истории
        df = pd.DataFrame(self.history)
        return df if not df.empty else pd.DataFrame(columns=["date", "result", "from_currency", "to_currency"])

class GraphTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.figure = Figure(figsize=(5,4), tight_layout=True)
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        self.setLayout(layout)

    def plot(self, df):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        if df.empty:
            ax.text(0.5, 0.5, "Нет данных для построения графика", ha='center')
        else:
            df['date'] = pd.to_datetime(df['date'])
            grouped = df.groupby(['date']).mean()
            ax.plot(grouped.index, grouped['result'])
            ax.set_title("Изменение курса")
            ax.set_xlabel("Дата")
            ax.set_ylabel("Результат")
        self.canvas.draw()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CurrencyConverterApp()
    window.show()
    sys.exit(app.exec())

