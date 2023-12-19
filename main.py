# This code created By Alişan Çelik
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox
from arayuzqt import Ui_MainWindow
import http.client
import json
import sqlite3
import os
from PyQt5.QtGui import QColor

from PyQt5.QtWidgets import QInputDialog, QTableWidgetItem, QTableWidget, QVBoxLayout, QWidget
from PyQt5.QtWidgets import QLineEdit, QPushButton
from PyQt5 import QtCore

class StockApp(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.pushButton.clicked.connect(self.fetch_stock_data)
        self.pushButton_3.clicked.connect(self.close_application)
        self.pushButton_4.clicked.connect(self.show_table)
        self.pushButton_2.clicked.connect(self.update_stock_prices)  # Yeni butonun sinyali
        self.pushButton_5.clicked.connect(self.calculate_profit_loss)
        self.initialize_database()
        self.sort_column = None
        self.sort_order_descending = False

        # Kar/Zarar tablosunu göstermek için yeni bir pencere oluştur
        self.profit_loss_window = QMainWindow()
        self.profit_loss_window.setWindowTitle("Kar/Zarar Tablosu")
        self.profit_loss_table = QTableWidget()
        self.profit_loss_window.setCentralWidget(QWidget())
        self.profit_loss_window.centralWidget().setLayout(QVBoxLayout())
        self.profit_loss_window.centralWidget().layout().addWidget(self.profit_loss_table)
        self.search_line_edit = QLineEdit(self.centralwidget)
        self.search_line_edit.setGeometry(QtCore.QRect(600, 150, 113, 32))
        self.search_line_edit.setObjectName("search_line_edit")

        self.search_button = QPushButton(self.centralwidget)
        self.search_button.setGeometry(QtCore.QRect(720, 150, 75, 31))
        self.search_button.setObjectName("search_button")
        self.search_button.setText("Ara")
        self.search_button.clicked.connect(self.search_stock)
        self.pushButton_6.clicked.connect(self.add_stock_to_database)  # Yeni eklenen satır
        self.populate_stock_symbols()

    def populate_stock_symbols(self):
        try:
            conn = http.client.HTTPSConnection("api.collectapi.com")
            headers = {
                'content-type': "application/json",
                'authorization': "apikey 2SJZNSOth9GYznj2wPB2Yp:31V2L183PuARI9EW2g4cuS"
            }
            conn.request("GET", "/economy/hisseSenedi", headers=headers)
            res = conn.getresponse()
            data = json.loads(res.read().decode("utf-8"))

            stock_symbols = []
            if isinstance(data.get('result'), list):
                stock_symbols = [stock_data.get('code', '') for stock_data in data['result']]

            self.comboBox.addItems(stock_symbols)

        except Exception as e:
            print("API Hatası:", e)

    def add_stock_to_database(self):
        stock_name = self.comboBox.currentText()
        stock_quantity = self.lineEdit_4.text()

        if not stock_name or not stock_quantity:
            QMessageBox.warning(self, "Uyarı", "Lütfen hisse adı ve adet bilgilerini girin.")
            return

        # API'den veri çekme
        stock_data = self.fetch_api_data(stock_name)

        if stock_data:
            stock_price = stock_data.get("lastprice")
            stock_volume = stock_data.get("hacim")

            # Veritabanına kaydetme
            self.save_to_database(stock_name, stock_quantity, stock_price, stock_volume)

            QMessageBox.information(self, "Bilgi", f"{stock_name} hissesi başarıyla eklendi.\n"
                                                   f"Adet: {stock_quantity}\n"
                                                   f"Fiyat: {stock_price}\n"
                                                   f"Hacim: {stock_volume}")
        else:
            QMessageBox.warning(self, "Hata", "Hisse senedi bilgileri alınamadı.")

    def initialize_database(self):
        if os.path.exists("stock_database.db"):
            os.remove("stock_database.db")

        try:
            connection = sqlite3.connect("stock_database.db")
            cursor = connection.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS stocks
                              (id INTEGER PRIMARY KEY AUTOINCREMENT,
                               stock_name TEXT,
                               quantity INTEGER,
                               price TEXT,
                               volume TEXT)''')
            connection.commit()
            connection.close()
        except Exception as e:
            print("Veritabanı Hatası:", e)

        if os.path.exists("updated_stock_prices.db"):
            os.remove("updated_stock_prices.db")
    def fetch_stock_data(self):
        stock_name = self.lineEdit_2.text()
        stock_quantity = self.lineEdit.text()

        if not stock_name or not stock_quantity:
            QMessageBox.warning(self, "Uyarı", "Lütfen hisse adı ve adet bilgilerini girin.")
            return

        stock_data = self.fetch_api_data(stock_name)

        if stock_data:
            stock_price = stock_data.get("lastprice")
            stock_volume = stock_data.get("hacim")

            self.save_to_database(stock_name, stock_quantity, stock_price, stock_volume)

            QMessageBox.information(self, "Bilgi", f"{stock_name} hissesi başarıyla eklendi.\n"
                                                   f"Adet: {stock_quantity}\n"
                                                   f"Fiyat: {stock_price}\n"
                                                   f"Hacim: {stock_volume}")
        else:
            QMessageBox.warning(self, "Hata", "Hisse senedi bilgileri alınamadı.")

    def fetch_api_data(self, stock_name):
        try:
            conn = http.client.HTTPSConnection("api.collectapi.com")
            headers = {
                'content-type': "application/json",
                'authorization': "apikey 2SJZNSOth9GYznj2wPB2Yp:31V2L183PuARI9EW2g4cuS"
            }
            conn.request("GET", f"/economy/hisseSenedi", headers=headers)
            res = conn.getresponse()
            data = json.loads(res.read().decode("utf-8"))

            if isinstance(data.get('result'), list):
                for stock_data in data['result']:
                    stock_name_from_api = stock_data.get('code', '')
                    if stock_name_from_api == stock_name:
                        return stock_data
            else:
                return data.get('result', {}).get(stock_name, {})
        except Exception as e:
            print("API Hatası:", e)
            return None

    def update_stock_prices(self):
        if os.path.exists("updated_stock_prices.db"):
            os.remove("updated_stock_prices.db")

        try:
            connection_updated = sqlite3.connect("updated_stock_prices.db")
            cursor_updated = connection_updated.cursor()
            cursor_updated.execute('''CREATE TABLE IF NOT EXISTS updated_stocks
                                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                                      stock_name TEXT,
                                      price TEXT,
                                      volume TEXT)''')
            connection_updated.commit()

            conn = http.client.HTTPSConnection("api.collectapi.com")
            headers = {
                'content-type': "application/json",
                'authorization': "apikey 2SJZNSOth9GYznj2wPB2Yp:31V2L183PuARI9EW2g4cuS"
            }
            conn.request("GET", "/economy/hisseSenedi", headers=headers)
            res = conn.getresponse()
            data = json.loads(res.read().decode("utf-8"))

            if isinstance(data.get('result'), list):
                for stock_data in data['result']:
                    stock_name = stock_data.get('code', '')
                    stock_price = stock_data.get('lastprice')
                    stock_volume = stock_data.get('hacim')

                    # Veriyi tabloya ekleme
                    cursor_updated.execute("INSERT INTO updated_stocks (stock_name, price, volume) "
                                           "VALUES (?, ?, ?)", (stock_name, stock_price, stock_volume))

            connection_updated.commit()
            connection_updated.close()

            QMessageBox.information(self, "Bilgi", "Güncel hisse fiyatları başarıyla alındı ve kaydedildi.")
        except Exception as e:
            print("API veya Veritabanı Hatası:", e)

    def calculate_profit_loss(self):
        # Hesaplanan kar/zarar bilgilerini tutmak için bir liste
        profit_loss_list = []

        connection_stock = sqlite3.connect("stock_database.db")
        cursor_stock = connection_stock.cursor()
        cursor_stock.execute("SELECT * FROM stocks")
        stocks = cursor_stock.fetchall()
        connection_stock.close()

        connection_updated = sqlite3.connect("updated_stock_prices.db")
        cursor_updated = connection_updated.cursor()
        cursor_updated.execute("SELECT * FROM updated_stocks")
        updated_stocks = cursor_updated.fetchall()
        connection_updated.close()

        for stock in stocks:
            stock_id, stock_name, _, old_price, _ = stock
            for updated_stock in updated_stocks:
                updated_stock_id, updated_stock_name, new_price, _ = updated_stock
                if stock_name == updated_stock_name:
                    old_price = float(old_price)
                    new_price = float(new_price)
                    quantity = int(stock[2])
                    total_amount = new_price * quantity
                    profit_loss = (new_price - old_price) * quantity
                    profit_loss_list.append((stock_name, old_price, new_price, quantity, total_amount, profit_loss))

        # Sıralama tercihi al
        items = ["Hisse Adı", "Eski Fiyat", "Yeni Fiyat", "Adet", "Toplam Tutar", "Kar/Zarar"]
        item, ok = QInputDialog.getItem(self, "Sıralama", "Sıralama tercihi:", items, 0, False)

        if ok and item:
            # Sıralama tercihine göre indeks belirle
            sort_index = items.index(item)

            # Eğer aynı sütuna tekrar tıklanırsa sıralama türünü tersine çevir
            if self.sort_column == sort_index:
                self.sort_order_descending = not self.sort_order_descending
            else:
                self.sort_order_descending = False

            # Sıralama türünü belirle
            reverse_sort = self.sort_order_descending

            # Kar/Zarar tablosunu sırala
            profit_loss_list.sort(key=lambda x: x[sort_index], reverse=reverse_sort)

            # Tabloyu temizle
            self.profit_loss_table.clear()

            # Sütun başlıklarını ekle
            self.profit_loss_table.setColumnCount(6)
            self.profit_loss_table.setHorizontalHeaderLabels(
                ["Hisse Adı", "Eski Fiyat", "Yeni Fiyat", "Adet", "Toplam Tutar", "Kar/Zarar"])

            self.profit_loss_table.setRowCount(len(profit_loss_list) + 1)  # +1, başlık için
            self.profit_loss_table.setMinimumWidth(800)
            self.profit_loss_table.setMinimumHeight(400)

            # Tabloya verileri ekle
            for i, entry in enumerate(profit_loss_list):
                self.profit_loss_table.insertRow(i)
                for j, value in enumerate(entry):
                    item = QTableWidgetItem(str(value))
                    if j == 5:  # Kar/Zarar sütunu
                        if value > 0:
                            item.setBackground(QColor(0, 255, 0))  # Yeşil
                        elif value < 0:
                            item.setBackground(QColor(255, 0, 0))  # Kırmızı
                    self.profit_loss_table.setItem(i, j, item)

            # Güncellenen sıralama sütununu kaydet
            self.sort_column = sort_index

            # Kar/Zarar penceresini göster
            self.profit_loss_window.show()

    def save_to_database(self, stock_name, stock_quantity, stock_price, stock_volume):
        try:
            connection = sqlite3.connect("stock_database.db")
            cursor = connection.cursor()

            cursor.execute("INSERT INTO stocks (stock_name, quantity, price, volume) "
                           "VALUES (?, ?, ?, ?)", (stock_name, stock_quantity, stock_price, stock_volume))

            connection.commit()
            connection.close()
        except Exception as e:
            print("Veritabanı Hatası:", e)

    def search_stock(self):
        # Arama butonuna tıklandığında çalışacak fonksiyon
        stock_name_to_search = self.search_line_edit.text()

        if not stock_name_to_search:
            QMessageBox.warning(self, "Uyarı", "Lütfen aramak istediğiniz hisse senedi adını girin.")
            return

        # Veritabanından hisse senedi bilgilerini çekme
        connection_stock = sqlite3.connect("stock_database.db")
        cursor_stock = connection_stock.cursor()
        cursor_stock.execute("SELECT * FROM stocks WHERE stock_name=?", (stock_name_to_search,))
        stock_info = cursor_stock.fetchone()
        connection_stock.close()

        if stock_info:
            # Hisse senedi bulundu, tabloda göster
            self.show_stock_table(stock_info)
        else:
            QMessageBox.warning(self, "Uyarı", f"{stock_name_to_search} hisse senedi bulunamadı.")

    def show_stock_table(self, stock_info):
        # Hisse senedi bilgilerini tabloda gösterme
        headers = ["ID", "Hisse Adı", "Adet", "Fiyat", "Hacim"]

        # Maksimum uzunluğu bul
        max_lengths = [len(header) for header in headers]
        for i, value in enumerate(stock_info):
            max_lengths[i] = max(max_lengths[i], len(str(value)))

        # Tablo metnini oluştur
        table_text = ""
        for i, header in enumerate(headers):
            table_text += f"{header.center(max_lengths[i] + 2)}\t"

        table_text += "\n" + "-" * (sum(max_lengths) + 10) + "\n"

        for i, value in enumerate(stock_info):
            table_text += f"{str(value).ljust(max_lengths[i] + 2)}\t"
        table_text += "\n"

        QMessageBox.information(self, "Hisse Senedi Bilgileri", table_text)
    def show_table(self):
        connection = sqlite3.connect("stock_database.db")
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM stocks")
        data = cursor.fetchall()
        connection.close()

        headers = ["ID", "Hisse Adı", "Adet", "Fiyat", "Hacim"]

        max_lengths = [len(header) for header in headers]
        for row in data:
            for i, value in enumerate(row):
                max_lengths[i] = max(max_lengths[i], len(str(value)))

        table_text = ""
        for i, header in enumerate(headers):
            table_text += f"{header.center(max_lengths[i] + 2)}\t"

        table_text += "\n" + "-" * (sum(max_lengths) + 10) + "\n"

        for row in data:
            for i, value in enumerate(row):
                table_text += f"{str(value).ljust(max_lengths[i] + 2)}\t"
            table_text += "\n"

        QMessageBox.information(self, "Tablo", table_text)

    def close_application(self):
        sys.exit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = StockApp()
    window.show()
    sys.exit(app.exec_())
# This code created By Alişan Çelik