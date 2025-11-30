"""
PDF Division Draw Application
Приложение для разделения больших PDF чертежей на форматы А4
"""
import sys
from PySide6.QtWidgets import QApplication
from gui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Division Draw")
    app.setOrganizationName("PDFTools")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

