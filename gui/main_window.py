"""
Главное окно приложения
"""
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QPushButton, QFileDialog, QMessageBox, QToolBar,
                               QLabel, QComboBox, QSpinBox, QDoubleSpinBox, QGroupBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QIcon
from gui.pdf_viewer import PDFViewer
from core.pdf_handler import PDFHandler


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.pdf_handler = PDFHandler()
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Division Draw - Разделение PDF чертежей")
        self.setGeometry(100, 100, 1400, 900)
        
        # Создаем меню
        self.create_menu()
        
        # Создаем центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Основной layout
        main_layout = QHBoxLayout(central_widget)
        
        # Левая панель управления
        left_panel = self.create_control_panel()
        main_layout.addWidget(left_panel)
        
        # Viewer для PDF
        self.pdf_viewer = PDFViewer()
        self.pdf_viewer.pdf_handler = self.pdf_handler
        main_layout.addWidget(self.pdf_viewer, stretch=1)
        
        # Правая панель с настройками масок
        right_panel = self.create_mask_panel()
        main_layout.addWidget(right_panel)
        
    def create_menu(self):
        menubar = self.menuBar()
        
        # Меню Файл
        file_menu = menubar.addMenu("&Файл")
        
        open_action = QAction("&Открыть PDF...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_pdf)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("&Выход", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Меню Помощь
        help_menu = menubar.addMenu("&Помощь")
        
        about_action = QAction("&О программе", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def create_control_panel(self):
        panel = QWidget()
        panel.setMaximumWidth(300)
        layout = QVBoxLayout(panel)
        
        # Группа: Файл
        file_group = QGroupBox("Документ")
        file_layout = QVBoxLayout()
        
        self.open_btn = QPushButton("Открыть PDF")
        self.open_btn.clicked.connect(self.open_pdf)
        file_layout.addWidget(self.open_btn)
        
        self.file_label = QLabel("Файл не загружен")
        self.file_label.setWordWrap(True)
        file_layout.addWidget(self.file_label)
        
        self.page_label = QLabel("Страница: -")
        file_layout.addWidget(self.page_label)
        
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)
        
        # Группа: Формат чертежа
        format_group = QGroupBox("Формат чертежа")
        format_layout = QVBoxLayout()
        
        self.format_combo = QComboBox()
        self.format_combo.addItems([
            "Авто-определение",
            "A0 (841 × 1189 мм)",
            "A0×2К (1189 × 1682 мм)",
            "A0×3К (1189 × 2523 мм)",
            "A1 (594 × 841 мм)",
            "A2 (420 × 594 мм)",
            "A3 (297 × 420 мм)",
            "A4 (210 × 297 мм)"
        ])
        format_layout.addWidget(QLabel("Формат:"))
        format_layout.addWidget(self.format_combo)
        
        format_group.setLayout(format_layout)
        layout.addWidget(format_group)
        
        # Группа: Параметры разделения
        split_group = QGroupBox("Параметры разделения")
        split_layout = QVBoxLayout()
        
        # Формат маски
        format_mask_layout = QHBoxLayout()
        format_mask_layout.addWidget(QLabel("Формат:"))
        self.mask_format_combo = QComboBox()
        self.mask_format_combo.addItems(["A4", "A3"])
        format_mask_layout.addWidget(self.mask_format_combo)
        split_layout.addLayout(format_mask_layout)
        
        # Ориентация
        orientation_layout = QHBoxLayout()
        orientation_layout.addWidget(QLabel("Ориентация:"))
        self.orientation_combo = QComboBox()
        self.orientation_combo.addItems(["Книжная", "Альбомная"])
        orientation_layout.addWidget(self.orientation_combo)
        split_layout.addLayout(orientation_layout)
        
        # Перекрытие
        overlap_layout = QHBoxLayout()
        overlap_layout.addWidget(QLabel("Перекрытие:"))
        self.overlap_spin = QDoubleSpinBox()
        self.overlap_spin.setRange(0, 50)
        self.overlap_spin.setValue(15)
        self.overlap_spin.setSuffix("%")
        overlap_layout.addWidget(self.overlap_spin)
        split_layout.addLayout(overlap_layout)
        
        self.generate_btn = QPushButton("Сгенерировать маски")
        self.generate_btn.clicked.connect(self.generate_masks)
        self.generate_btn.setEnabled(False)
        split_layout.addWidget(self.generate_btn)
        
        self.clear_masks_btn = QPushButton("Очистить все маски")
        self.clear_masks_btn.clicked.connect(self.clear_all_masks)
        self.clear_masks_btn.setEnabled(False)
        split_layout.addWidget(self.clear_masks_btn)
        
        self.masks_label = QLabel("Масок: 0")
        split_layout.addWidget(self.masks_label)
        
        split_group.setLayout(split_layout)
        layout.addWidget(split_group)
        
        # Группа: Разделение
        divide_group = QGroupBox("Разделение")
        divide_layout = QVBoxLayout()
        
        self.divide_btn = QPushButton("Разделить PDF")
        self.divide_btn.clicked.connect(self.divide_pdf)
        self.divide_btn.setEnabled(False)
        divide_layout.addWidget(self.divide_btn)
        
        divide_group.setLayout(divide_layout)
        layout.addWidget(divide_group)
        
        layout.addStretch()
        
        return panel
    
    def create_mask_panel(self):
        panel = QWidget()
        panel.setMaximumWidth(250)
        layout = QVBoxLayout(panel)
        
        # Группа: Выбранная маска
        mask_group = QGroupBox("Выбранная маска")
        mask_layout = QVBoxLayout()
        
        self.mask_info_label = QLabel("Маска не выбрана")
        self.mask_info_label.setWordWrap(True)
        mask_layout.addWidget(self.mask_info_label)
        
        self.rotate_btn = QPushButton("Повернуть (90°)")
        self.rotate_btn.clicked.connect(self.rotate_selected_mask)
        self.rotate_btn.setEnabled(False)
        mask_layout.addWidget(self.rotate_btn)
        
        self.delete_btn = QPushButton("Удалить маску")
        self.delete_btn.clicked.connect(self.delete_selected_mask)
        self.delete_btn.setEnabled(False)
        mask_layout.addWidget(self.delete_btn)
        
        mask_group.setLayout(mask_layout)
        layout.addWidget(mask_group)
        
        # Группа: Добавить маску
        add_group = QGroupBox("Добавить маску")
        add_layout = QVBoxLayout()
        
        self.add_a4_portrait_btn = QPushButton("Добавить А4 (книжная)")
        self.add_a4_portrait_btn.clicked.connect(lambda: self.add_mask('A4', False))
        self.add_a4_portrait_btn.setEnabled(False)
        add_layout.addWidget(self.add_a4_portrait_btn)
        
        self.add_a4_landscape_btn = QPushButton("Добавить А4 (альбомная)")
        self.add_a4_landscape_btn.clicked.connect(lambda: self.add_mask('A4', True))
        self.add_a4_landscape_btn.setEnabled(False)
        add_layout.addWidget(self.add_a4_landscape_btn)
        
        self.add_a3_portrait_btn = QPushButton("Добавить А3 (книжная)")
        self.add_a3_portrait_btn.clicked.connect(lambda: self.add_mask('A3', False))
        self.add_a3_portrait_btn.setEnabled(False)
        add_layout.addWidget(self.add_a3_portrait_btn)
        
        self.add_a3_landscape_btn = QPushButton("Добавить А3 (альбомная)")
        self.add_a3_landscape_btn.clicked.connect(lambda: self.add_mask('A3', True))
        self.add_a3_landscape_btn.setEnabled(False)
        add_layout.addWidget(self.add_a3_landscape_btn)
        
        add_group.setLayout(add_layout)
        layout.addWidget(add_group)
        
        layout.addStretch()
        
        return panel
    
    def open_pdf(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Открыть PDF", "", "PDF файлы (*.pdf)"
        )
        
        if file_path:
            try:
                self.pdf_handler.load_pdf(file_path)
                self.pdf_viewer.load_pdf()
                
                # Обновляем UI
                import os
                self.file_label.setText(f"Файл: {os.path.basename(file_path)}")
                self.page_label.setText(f"Страниц: {self.pdf_handler.page_count}")
                self.generate_btn.setEnabled(True)
                self.add_a4_portrait_btn.setEnabled(True)
                self.add_a4_landscape_btn.setEnabled(True)
                self.add_a3_portrait_btn.setEnabled(True)
                self.add_a3_landscape_btn.setEnabled(True)
                
                QMessageBox.information(self, "Успех", 
                    f"PDF загружен успешно!\nСтраниц: {self.pdf_handler.page_count}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить PDF:\n{str(e)}")
    
    def generate_masks(self):
        if not self.pdf_handler.is_loaded():
            QMessageBox.warning(self, "Предупреждение", "Сначала загрузите PDF файл")
            return
        
        try:
            overlap_percent = self.overlap_spin.value()
            format_text = self.format_combo.currentText()
            mask_format = self.mask_format_combo.currentText()
            is_landscape = self.orientation_combo.currentText() == "Альбомная"
            
            # Генерируем маски
            masks = self.pdf_handler.generate_masks(
                overlap_percent=overlap_percent,
                format_hint=format_text,
                mask_format=mask_format,
                mask_landscape=is_landscape
            )
            
            self.pdf_viewer.set_masks(masks)
            self.masks_label.setText(f"Масок: {len(masks)}")
            self.divide_btn.setEnabled(len(masks) > 0)
            self.clear_masks_btn.setEnabled(len(masks) > 0)
            
            orientation_text = "альбомных" if is_landscape else "книжных"
            QMessageBox.information(self, "Успех", 
                f"Сгенерировано {len(masks)} {orientation_text} масок {mask_format}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", 
                f"Не удалось сгенерировать маски:\n{str(e)}")
    
    def divide_pdf(self):
        if not self.pdf_handler.is_loaded():
            QMessageBox.warning(self, "Предупреждение", "Сначала загрузите PDF файл")
            return
        
        masks = self.pdf_viewer.get_masks()
        if not masks:
            QMessageBox.warning(self, "Предупреждение", "Нет масок для разделения")
            return
        
        # Выбираем папку для сохранения
        output_dir = QFileDialog.getExistingDirectory(
            self, "Выберите папку для сохранения разделенных файлов"
        )
        
        if output_dir:
            try:
                output_files = self.pdf_handler.divide_pdf(masks, output_dir)
                QMessageBox.information(self, "Успех", 
                    f"PDF успешно разделен!\nСоздано файлов: {len(output_files)}\nПапка: {output_dir}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", 
                    f"Не удалось разделить PDF:\n{str(e)}")
    
    def rotate_selected_mask(self):
        self.pdf_viewer.rotate_selected_mask()
    
    def delete_selected_mask(self):
        self.pdf_viewer.delete_selected_mask()
        masks = self.pdf_viewer.get_masks()
        self.masks_label.setText(f"Масок: {len(masks)}")
        self.divide_btn.setEnabled(len(masks) > 0)
        self.clear_masks_btn.setEnabled(len(masks) > 0)
    
    def clear_all_masks(self):
        """Очистка всех масок"""
        self.pdf_viewer.clear_all_masks()
        self.masks_label.setText("Масок: 0")
        self.divide_btn.setEnabled(False)
        self.clear_masks_btn.setEnabled(False)
    
    def add_mask(self, mask_format='A4', landscape=False):
        self.pdf_viewer.add_mask(mask_format, landscape)
        masks = self.pdf_viewer.get_masks()
        self.masks_label.setText(f"Масок: {len(masks)}")
        self.divide_btn.setEnabled(len(masks) > 0)
        self.clear_masks_btn.setEnabled(len(masks) > 0)
    
    def update_mask_info(self, mask_info):
        """Обновление информации о выбранной маске"""
        if mask_info:
            self.mask_info_label.setText(mask_info)
            self.rotate_btn.setEnabled(True)
            self.delete_btn.setEnabled(True)
        else:
            self.mask_info_label.setText("Маска не выбрана")
            self.rotate_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)
    
    def show_about(self):
        QMessageBox.about(self, "О программе",
            "<h3>Division Draw</h3>"
            "<p>Приложение для разделения больших PDF чертежей на форматы А4</p>"
            "<p>Версия 1.0</p>"
            "<p>Используемые технологии: PySide6, PyMuPDF</p>")

