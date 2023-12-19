# -*- coding: utf-8 -*-

import sys
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QComboBox, QLineEdit, QMessageBox, \
    QMainWindow, QHBoxLayout, QListWidget, QFormLayout, QDialog, QSpinBox, QDialogButtonBox, QInputDialog

import sqlite3

class AuctionDatabase:
    def __init__(self, db_file):
        self.connection = sqlite3.connect(db_file)
        self.cursor = self.connection.cursor()

    def create_table(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                login TEXT NOT NULL,
                password TEXT NOT NULL,
                user_type TEXT NOT NULL
            );
        ''')
        self.connection.commit()

    def create_auction_table(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                auctioneer_id INTEGER,
                item_name TEXT NOT NULL,
                start_bid REAL NOT NULL,
                FOREIGN KEY (auctioneer_id) REFERENCES users(id)
            );
        ''')
        self.connection.commit()

    def create_bid_table(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS bids (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                item_id INTEGER,
                bid_value REAL NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (item_id) REFERENCES items(id)
            );
        ''')
        self.connection.commit()

    def get_item_details(self, item_id):
        self.cursor.execute('SELECT item_name, start_bid FROM items WHERE id=?', (item_id,))
        item_name, start_bid = self.cursor.fetchone()

        # Получение текущей ставки для товара
        self.cursor.execute('SELECT MAX(bid_value) FROM bids WHERE item_id=?', (item_id,))
        current_bid = self.cursor.fetchone()[0] or start_bid

        return item_name, start_bid, current_bid

    def place_bid(self, item_id, bid_value):
        user_id = self.get_user_id(self.logged_in_user_login)
        self.cursor.execute('INSERT INTO bids (user_id, item_id, bid_value) VALUES (?, ?, ?)',
                            (user_id, item_id, bid_value))
        self.connection.commit()

    def add_user(self, login, password, user_type):
        self.cursor.execute('INSERT INTO users (login, password, user_type) VALUES (?, ?, ?)', (login, password, user_type))
        self.connection.commit()

    def check_user_login(self, login, password):
        self.cursor.execute('SELECT * FROM users WHERE login=? AND password=?', (login, password))
        return self.cursor.fetchone() is not None

    def check_auctioneer_login(self, login, password):
        self.cursor.execute('SELECT * FROM users WHERE login=? AND password=? AND user_type="Аукционер"', (login, password))
        return self.cursor.fetchone() is not None

    def add_item(self, auctioneer_id, item_name, start_bid):
        self.cursor.execute('INSERT INTO items (auctioneer_id, item_name, start_bid) VALUES (?, ?, ?)', (auctioneer_id, item_name, start_bid))
        self.connection.commit()

    def get_user_id(self, login):
        self.cursor.execute('SELECT id FROM users WHERE login=?', (login,))
        user_id = self.cursor.fetchone()
        return user_id[0] if user_id else None

    def get_auctioneer_items(self, auctioneer_login):
        auctioneer_id = self.get_user_id(auctioneer_login)
        self.cursor.execute('SELECT item_name, start_bid FROM items WHERE auctioneer_id=?', (auctioneer_id,))
        items = self.cursor.fetchall()
        return [f'{item_name} - Начальная цена: {start_bid}' for item_name, start_bid in items]


class RegisterWindow(QWidget):
    def __init__(self, parent, user_type, database):
        super().__init__()

        self.parent = parent
        self.user_type = user_type
        self.db = database

        register_layout = QVBoxLayout()

        user_type_combo = QComboBox()
        user_type_combo.addItem("Пользователь")
        user_type_combo.addItem("Аукционер")
        register_layout.addWidget(user_type_combo)

        login_label = QLabel("Логин:")
        register_layout.addWidget(login_label)

        login_line = QLineEdit()
        register_layout.addWidget(login_line)

        password_label = QLabel("Пароль:")
        register_layout.addWidget(password_label)

        password_line = QLineEdit()
        password_line.setEchoMode(QLineEdit.EchoMode.Password)
        register_layout.addWidget(password_line)

        register_button = QPushButton("Зарегистрироваться")
        register_button.clicked.connect(lambda: self.parent.register(self, user_type_combo.currentText(), login_line.text(), password_line.text()))
        register_layout.addWidget(register_button)

        exit_button = QPushButton("Выйти")
        exit_button.clicked.connect(self.close)
        register_layout.addWidget(exit_button)

        self.setLayout(register_layout)
        self.setWindowTitle("Регистрация")


class LoginWindow(QWidget):
    def __init__(self, parent, user_type, database):
        super().__init__()

        self.parent = parent
        self.user_type = user_type
        self.db = database

        login_layout = QVBoxLayout()

        user_type_combo = QComboBox()
        user_type_combo.addItem("Пользователь")
        user_type_combo.addItem("Аукционер")
        login_layout.addWidget(user_type_combo)

        login_label = QLabel("Логин:")
        login_layout.addWidget(login_label)

        login_line = QLineEdit()
        login_layout.addWidget(login_line)

        password_label = QLabel("Пароль:")
        login_layout.addWidget(password_label)

        password_line = QLineEdit()
        password_line.setEchoMode(QLineEdit.EchoMode.Password)
        login_layout.addWidget(password_line)

        login_button = QPushButton("Войти")
        login_button.clicked.connect(lambda: self.parent.login(self, user_type_combo.currentText(), login_line.text(), password_line.text()))
        login_layout.addWidget(login_button)

        exit_button = QPushButton("Выйти")
        exit_button.clicked.connect(self.close)
        login_layout.addWidget(exit_button)

        self.setLayout(login_layout)
        self.setWindowTitle("Вход")

    def show_register_window(self):
        register_window = RegisterWindow(self, self.user_type, self.db)
        register_window.show()

class AuctioneerWindow(QMainWindow):
    def __init__(self, parent, database):
        super().__init__(parent)
        self.setWindowTitle('Интерфейс аукционера')
        self.setGeometry(100, 100, 600, 400)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.parent = parent
        self.db = database

        main_layout = QVBoxLayout()

        # Создаем QDialog для отображения товаров
        self.item_dialog = QDialog(self)
        self.item_dialog.setWindowTitle('Лоты аукционера')
        self.item_dialog.setGeometry(200, 200, 400, 300)

        item_dialog_layout = QVBoxLayout()
        self.item_list_dialog = QListWidget()
        item_dialog_layout.addWidget(self.item_list_dialog)
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        button_box.accepted.connect(self.item_dialog.accept)
        item_dialog_layout.addWidget(button_box)
        self.item_dialog.setLayout(item_dialog_layout)

        self.item_list_button = QPushButton('Показать лоты')
        self.item_list_button.clicked.connect(self.show_item_dialog)
        main_layout.addWidget(self.item_list_button)

        self.item_list = QListWidget()
        main_layout.addWidget(self.item_list)

        item_info_layout = QVBoxLayout()

        self.item_name_label = QLabel('Наименование лота:')
        item_info_layout.addWidget(self.item_name_label)

        self.item_name_input = QLineEdit()
        item_info_layout.addWidget(self.item_name_input)

        self.start_bid_label = QLabel('Начальная цена:')
        item_info_layout.addWidget(self.start_bid_label)

        self.start_bid_input = QLineEdit()
        item_info_layout.addWidget(self.start_bid_input)

        self.add_item_button = QPushButton('Добавить лот')
        self.add_item_button.clicked.connect(self.add_item)
        item_info_layout.addWidget(self.add_item_button)

        main_layout.addLayout(item_info_layout)

        self.central_widget.setLayout(main_layout)

    def show_item_dialog(self):
        # Получаем товары аукционера из базы данных и обновляем список товаров в диалоге
        items = self.db.get_auctioneer_items(self.parent.logged_in_user_login)
        self.item_list_dialog.clear()
        self.item_list_dialog.addItems(items)
        result = self.item_dialog.exec()

        if result == QDialog.DialogCode.Accepted:
            selected_item = self.item_list_dialog.currentItem()
            if selected_item:
                item_id = selected_item.data(0)
                self.show_edit_delete_dialog(item_id)

    def show_edit_delete_dialog(self, item_id):
        edit_delete_dialog = QDialog(self)
        edit_delete_dialog.setWindowTitle('Редактирование/Удаление лота')
        edit_delete_dialog.setGeometry(200, 200, 300, 150)

        edit_delete_layout = QVBoxLayout()

        edit_button = QPushButton('Редактировать')
        edit_button.clicked.connect(lambda: self.edit_item(item_id))
        edit_delete_layout.addWidget(edit_button)

        delete_button = QPushButton('Удалить')
        delete_button.clicked.connect(lambda: self.delete_item(item_id))
        edit_delete_layout.addWidget(delete_button)

        edit_delete_dialog.setLayout(edit_delete_layout)
        edit_delete_dialog.exec()

    def edit_item(self, item_id):
        new_name, ok_name = QInputDialog.getText(self, 'Редактировать лот', 'Введите новое наименование:')
        new_start_bid, ok_start_bid = QInputDialog.getDouble(self, 'Редактировать лот',
                                                             'Введите новую начальную цену:')

        if ok_name and ok_start_bid:
            self.db.cursor.execute('UPDATE items SET item_name=?, start_bid=? WHERE id=?',
                                   (new_name, new_start_bid, item_id))
            self.db.connection.commit()
            self.show_item_dialog()

    def delete_item(self, item_id):
        reply = QMessageBox.question(self, 'Удаление лота', 'Вы уверены, что хотите удалить этот лот?',
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            self.db.cursor.execute('DELETE FROM items WHERE id=?', (item_id,))
            self.db.connection.commit()
            self.show_item_dialog()

    def add_item(self):
        item_name = self.item_name_input.text()
        start_bid = self.start_bid_input.text()

        if item_name and start_bid:
            auctioneer_id = self.db.get_user_id(self.parent.logged_in_user_login)  # Получение ID аукционера
            self.db.add_item(auctioneer_id, item_name, start_bid)
            self.item_list.addItem(f'{item_name} - Начальная цена: {start_bid}')
            self.item_name_input.clear()
            self.start_bid_input.clear()
        else:
            QMessageBox.critical(self, 'Ошибка', 'Пожалуйста, введите наименование лота и начальную цену')

class UserInterface(QDialog):
    def __init__(self, parent, database):
        super().__init__(parent)

        self.setWindowTitle('Интерфейс пользователя')
        self.setGeometry(100, 100, 600, 400)

        self.parent = parent
        self.db = database

        main_layout = QVBoxLayout()

        self.item_list_label = QLabel('Доступные лоты:')
        main_layout.addWidget(self.item_list_label)

        self.item_list = QListWidget()
        main_layout.addWidget(self.item_list)

        item_info_layout = QFormLayout()

        self.selected_item_label = QLabel('Выбранный лот:')
        item_info_layout.addRow(self.selected_item_label, QLabel(''))

        self.min_bid_label = QLabel('Минимальная цена:')
        item_info_layout.addRow(self.min_bid_label, QLabel(''))

        self.bid_label = QLabel('Ваша ставка:')
        item_info_layout.addRow(self.bid_label, QSpinBox())

        self.place_bid_button = QPushButton('Сделать ставку')
        self.place_bid_button.clicked.connect(self.place_bid)
        item_info_layout.addRow(self.place_bid_button)

        main_layout.addLayout(item_info_layout)

        self.setLayout(main_layout)

    def place_bid(self):
        selected_item = self.item_list.currentItem()

        if selected_item:
            item_id = selected_item.data(0)  # Get the item ID from data
            item_name, start_bid, current_bid = self.db.get_item_details(item_id)

            min_bid_label = self.min_bid_label.parent().itemAt(1).widget()
            min_bid_label.setText(f'{start_bid} (Текущая ставка: {current_bid})')

            bid_value = self.bid_label.parent().itemAt(1).widget().value()

            if bid_value > current_bid:
                self.db.place_bid(item_id, bid_value)
                QMessageBox.information(self, 'Ставка размещена',
                                        f'Вы разместили ставку {bid_value} на лот "{item_name}"')
            else:
                QMessageBox.warning(self, 'Ошибка', 'Ставка должна быть выше текущей ставки')
        else:
            QMessageBox.warning(self, 'Ошибка', 'Пожалуйста, выберите лот, на который хотите сделать ставку')

class AuctionApp(QWidget):
    def __init__(self):
        super().__init__()

        # Инициализация базы данных и создание таблиц
        self.db = AuctionDatabase('auction.db')
        self.db.create_table()
        self.db.create_auction_table()

        self.setWindowTitle("Аукцион")
        self.login_register_layout = QVBoxLayout()

        label = QLabel("Пожалуйста, выберите действие:")
        self.login_register_layout.addWidget(label)

        self.login_button = QPushButton("Войти")
        self.login_button.clicked.connect(self.show_login_window)
        self.login_register_layout.addWidget(self.login_button)

        register_button = QPushButton("Зарегистрироваться")
        register_button.clicked.connect(self.show_register_window)
        self.login_register_layout.addWidget(register_button)

        exit_button = QPushButton("Выйти")
        exit_button.clicked.connect(self.close)
        self.login_register_layout.addWidget(exit_button)

        self.setLayout(self.login_register_layout)

        self.logged_in_user_login = None  # Добавлено для хранения логина пользователя

    def show_login_window(self):
        login_window = LoginWindow(self, "Пользователь", self.db)
        login_window.show()

    def show_register_window(self):
        register_window = RegisterWindow(self, "Пользователь", self.db)
        register_window.show()

    def login(self, window, user_type, login, password):
        if user_type == "Пользователь":
            if self.db.check_user_login(login, password):
                self.show_user_interface(login)
                window.close()
                self.logged_in_user_login = login
            else:
                QMessageBox.warning(window, "Ошибка", "Неверный логин или пароль")
        elif user_type == "Аукционер":
            if self.db.check_auctioneer_login(login, password):
                self.show_auctioneer_interface()
                window.close()
                self.logged_in_user_login = login
            else:
                QMessageBox.warning(window, "Ошибка", "Неверный логин или пароль")

    def register(self, window, user_type, login, password):
        # Регистрация нового пользователя или аукционера в базе данных
        if user_type == "Пользователь":
            self.db.add_user(login, password, user_type)
            QMessageBox.information(window, "Успех", "Пользователь успешно зарегистрирован")
            window.close()
            self.logged_in_user_login = login
        elif user_type == "Аукционер":
            self.db.add_user(login, password, user_type)
            QMessageBox.information(window, "Успех", "Аукционер успешно зарегистрирован")
            window.close()
            self.logged_in_user_login = login

    def show_user_interface(self, login):
        user_interface = UserInterface(self, self.db)
        user_interface.show()

    def show_auctioneer_interface(self):
        # Отображение интерфейса для аукционера
        auctioneer_window = AuctioneerWindow(self, self.db)
        auctioneer_window.show()

class UserInterface(QDialog):
    def __init__(self, parent, database):
        super().__init__(parent)

        self.setWindowTitle('Интерфейс пользователя')
        self.setGeometry(100, 100, 600, 400)

        self.parent = parent
        self.db = database

        main_layout = QVBoxLayout()

        self.item_list_label = QLabel('Доступные лоты:')
        main_layout.addWidget(self.item_list_label)

        self.item_list = QListWidget()
        main_layout.addWidget(self.item_list)

        item_info_layout = QFormLayout()

        self.selected_item_label = QLabel('Выбранный лот:')
        item_info_layout.addRow(self.selected_item_label, QLabel(''))

        self.min_bid_label = QLabel('Минимальная цена:')
        item_info_layout.addRow(self.min_bid_label, QLabel(''))

        self.bid_label = QLabel('Ваша ставка:')
        item_info_layout.addRow(self.bid_label, QSpinBox())

        self.place_bid_button = QPushButton('Сделать ставку')
        self.place_bid_button.clicked.connect(self.place_bid)
        item_info_layout.addRow(self.place_bid_button)

        main_layout.addLayout(item_info_layout)

        self.setLayout(main_layout)

    def place_bid(self):
        selected_item = self.item_list.currentItem()

        if selected_item:
            item_id = selected_item.data(0)  # Get the item ID from data
            item_name, start_bid, current_bid = self.db.get_item_details(item_id)

            min_bid_label = self.min_bid_label.parent().itemAt(1).widget()
            min_bid_label.setText(f'{start_bid} (Текущая ставка: {current_bid})')

            bid_value = self.bid_label.parent().itemAt(1).widget().value()

            if bid_value > current_bid:
                self.db.place_bid(item_id, bid_value)
                QMessageBox.information(self, 'Ставка размещена',
                                        f'Вы разместили ставку {bid_value} на лот "{item_name}"')
            else:
                QMessageBox.warning(self, 'Ошибка', 'Ставка должна быть выше текущей ставки')
        else:
            QMessageBox.warning(self, 'Ошибка', 'Пожалуйста, выберите лот, на который хотите сделать ставку')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    auction_app = AuctionApp()
    auction_app.show()
    sys.exit(app.exec())