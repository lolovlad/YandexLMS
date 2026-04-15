import sqlite3
import sys
from pathlib import Path

from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QTableWidgetItem


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "coffee.sqlite"
UI_PATH = BASE_DIR / "main.ui"


class CoffeeCatalogWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        uic.loadUi(str(UI_PATH), self)
        self.setWindowTitle("Каталог кофе")
        self.refresh_button.clicked.connect(self.load_data)
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


def main() -> None:
    app = QApplication(sys.argv)
    window = CoffeeCatalogWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
