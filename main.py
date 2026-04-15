import sqlite3
import sys
from pathlib import Path

from PyQt5 import uic
from PyQt5.QtWidgets import (
    QApplication,
    QDialog,
    QMainWindow,
    QMessageBox,
    QTableWidgetItem,
)


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "coffee.sqlite"
MAIN_UI_PATH = BASE_DIR / "main.ui"
ADD_EDIT_UI_PATH = BASE_DIR / "addEditCoffeeForm.ui"


class AddEditCoffeeForm(QDialog):
    def __init__(self, parent: QMainWindow, coffee_id: int | None = None) -> None:
        super().__init__(parent)
        uic.loadUi(str(ADD_EDIT_UI_PATH), self)
        self.coffee_id = coffee_id
        self.save_button.clicked.connect(self.save_coffee)
        self.cancel_button.clicked.connect(self.reject)

        if self.coffee_id is None:
            self.setWindowTitle("Добавление кофе")
        else:
            self.setWindowTitle("Редактирование кофе")
            self.fill_fields()

    def fill_fields(self) -> None:
        try:
            with sqlite3.connect(DB_PATH) as connection:
                cursor = connection.cursor()
                cursor.execute(
                    """
                    SELECT sort_name, roast_degree, form_type, taste_description,
                           price, package_volume
                    FROM coffee
                    WHERE id = ?
                    """,
                    (self.coffee_id,),
                )
                row = cursor.fetchone()
        except sqlite3.Error as error:
            QMessageBox.critical(self, "Ошибка базы данных", f"Не удалось загрузить запись:\n{error}")
            self.reject()
            return

        if row is None:
            QMessageBox.warning(self, "Ошибка", "Выбранная запись не найдена.")
            self.reject()
            return

        self.sort_name_input.setText(str(row[0]))
        self.roast_degree_input.setText(str(row[1]))
        self.form_type_input.setText(str(row[2]))
        self.taste_description_input.setPlainText(str(row[3]))
        self.price_input.setText(str(row[4]))
        self.package_volume_input.setText(str(row[5]))

    def save_coffee(self) -> None:
        sort_name = self.sort_name_input.text().strip()
        roast_degree = self.roast_degree_input.text().strip()
        form_type = self.form_type_input.text().strip()
        taste_description = self.taste_description_input.toPlainText().strip()
        price_text = self.price_input.text().strip().replace(",", ".")
        package_volume = self.package_volume_input.text().strip()

        if not all([sort_name, roast_degree, form_type, taste_description, price_text, package_volume]):
            QMessageBox.warning(self, "Ошибка", "Заполните все поля формы.")
            return

        try:
            price = float(price_text)
            if price <= 0:
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Цена должна быть положительным числом.")
            return

        try:
            with sqlite3.connect(DB_PATH) as connection:
                cursor = connection.cursor()
                if self.coffee_id is None:
                    cursor.execute(
                        """
                        INSERT INTO coffee (
                            sort_name, roast_degree, form_type, taste_description,
                            price, package_volume
                        ) VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (sort_name, roast_degree, form_type, taste_description, price, package_volume),
                    )
                else:
                    cursor.execute(
                        """
                        UPDATE coffee
                        SET sort_name = ?, roast_degree = ?, form_type = ?, taste_description = ?,
                            price = ?, package_volume = ?
                        WHERE id = ?
                        """,
                        (
                            sort_name,
                            roast_degree,
                            form_type,
                            taste_description,
                            price,
                            package_volume,
                            self.coffee_id,
                        ),
                    )
                connection.commit()
        except sqlite3.Error as error:
            QMessageBox.critical(self, "Ошибка базы данных", f"Не удалось сохранить запись:\n{error}")
            return

        self.accept()


class CoffeeCatalogWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        uic.loadUi(str(MAIN_UI_PATH), self)
        self.setWindowTitle("Каталог кофе")
        self.refresh_button.clicked.connect(self.load_data)
        self.add_button.clicked.connect(self.add_coffee)
        self.edit_button.clicked.connect(self.edit_selected_coffee)
        self.load_data()

    def load_data(self) -> None:
        if not DB_PATH.exists():
            QMessageBox.critical(self, "Ошибка", "Файл базы данных coffee.sqlite не найден.")
            return

        try:
            with sqlite3.connect(DB_PATH) as connection:
                cursor = connection.cursor()
                cursor.execute(
                    """
                    SELECT id, sort_name, roast_degree, form_type, taste_description,
                           price, package_volume
                    FROM coffee
                    ORDER BY id
                    """
                )
                rows = cursor.fetchall()
        except sqlite3.Error as error:
            QMessageBox.critical(self, "Ошибка базы данных", f"Не удалось загрузить данные:\n{error}")
            return

        self.coffee_table.setRowCount(len(rows))
        self.coffee_table.setColumnCount(7)
        self.coffee_table.setHorizontalHeaderLabels(
            [
                "ID",
                "Название сорта",
                "Степень обжарки",
                "Молотый/в зернах",
                "Описание вкуса",
                "Цена",
                "Объем упаковки",
            ]
        )

        for row_index, row_data in enumerate(rows):
            for column_index, value in enumerate(row_data):
                self.coffee_table.setItem(row_index, column_index, QTableWidgetItem(str(value)))

        self.coffee_table.resizeColumnsToContents()

    def add_coffee(self) -> None:
        form = AddEditCoffeeForm(self)
        if form.exec_():
            self.load_data()

    def edit_selected_coffee(self) -> None:
        selected_row = self.coffee_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Внимание", "Выберите запись для редактирования.")
            return

        coffee_id_item = self.coffee_table.item(selected_row, 0)
        if coffee_id_item is None:
            QMessageBox.warning(self, "Ошибка", "Не удалось определить ID выбранной записи.")
            return

        try:
            coffee_id = int(coffee_id_item.text())
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Некорректный ID выбранной записи.")
            return

        form = AddEditCoffeeForm(self, coffee_id=coffee_id)
        if form.exec_():
            self.load_data()


def main() -> None:
    app = QApplication(sys.argv)
    window = CoffeeCatalogWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
