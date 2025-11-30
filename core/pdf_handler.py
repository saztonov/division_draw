"""
Обработчик PDF файлов
"""
import fitz  # PyMuPDF
from PySide6.QtGui import QPixmap, QImage
import os


class PDFHandler:
    """Класс для работы с PDF файлами"""
    
    # Размеры форматов в мм
    FORMAT_SIZES_MM = {
        'A0': (841, 1189),
        'A0x2': (1189, 1682),
        'A0x3': (1189, 2523),
        'A1': (594, 841),
        'A2': (420, 594),
        'A3': (297, 420),
        'A4': (210, 297),
    }
    
    # Размеры форматов в мм
    A4_WIDTH_MM = 210
    A4_HEIGHT_MM = 297
    A3_WIDTH_MM = 297
    A3_HEIGHT_MM = 420
    MM_TO_POINTS = 2.83465  # 1 мм = 2.83465 points в PDF
    
    def __init__(self):
        self.document = None
        self.file_path = None
        self.page_count = 0
        self.current_page = None
        
    def load_pdf(self, file_path):
        """Загрузка PDF файла"""
        try:
            self.document = fitz.open(file_path)
            self.file_path = file_path
            self.page_count = len(self.document)
            
            if self.page_count > 0:
                self.current_page = self.document[0]
            
            return True
        except Exception as e:
            raise Exception(f"Ошибка загрузки PDF: {str(e)}")
    
    def is_loaded(self):
        """Проверка, загружен ли PDF"""
        return self.document is not None
    
    def get_page(self, page_num=0):
        """Получение страницы PDF"""
        if not self.is_loaded() or page_num >= self.page_count:
            return None
        return self.document[page_num]
    
    def render_page(self, page_num=0, zoom=2.0):
        """Рендеринг страницы PDF в QPixmap"""
        page = self.get_page(page_num)
        if not page:
            return None
        
        # Создаем матрицу трансформации для масштабирования
        mat = fitz.Matrix(zoom, zoom)
        
        # Рендерим страницу
        pix = page.get_pixmap(matrix=mat)
        
        # Конвертируем в QImage
        img_data = pix.samples
        qimage = QImage(
            img_data,
            pix.width,
            pix.height,
            pix.stride,
            QImage.Format_RGB888
        )
        
        # Конвертируем в QPixmap
        return QPixmap.fromImage(qimage)
    
    def get_page_size_mm(self, page_num=0):
        """Получение размера страницы в мм"""
        page = self.get_page(page_num)
        if not page:
            return None
        
        rect = page.rect
        width_mm = rect.width / self.MM_TO_POINTS
        height_mm = rect.height / self.MM_TO_POINTS
        
        return (width_mm, height_mm)
    
    def get_page_size_points(self, page_num=0):
        """Получение размера страницы в points (единицах PDF)"""
        page = self.get_page(page_num)
        if not page:
            return None
        
        rect = page.rect
        return (rect.width, rect.height)
    
    def detect_format(self, page_num=0):
        """Автоматическое определение формата чертежа"""
        size_mm = self.get_page_size_mm(page_num)
        if not size_mm:
            return None
        
        width_mm, height_mm = size_mm
        
        # Нормализуем (больший размер всегда первый)
        if width_mm < height_mm:
            width_mm, height_mm = height_mm, width_mm
        
        # Ищем ближайший формат с точностью 5%
        tolerance = 0.05
        
        for format_name, (w, h) in self.FORMAT_SIZES_MM.items():
            # Нормализуем размеры формата
            if w < h:
                w, h = h, w
            
            # Проверяем соответствие с учетом допуска
            if (abs(width_mm - w) / w < tolerance and 
                abs(height_mm - h) / h < tolerance):
                return format_name
        
        return None
    
    def get_a4_size_in_points(self):
        """Получение размера А4 в points (единицах PDF)"""
        width_points = self.A4_WIDTH_MM * self.MM_TO_POINTS
        height_points = self.A4_HEIGHT_MM * self.MM_TO_POINTS
        return (width_points, height_points)
    
    def get_a3_size_in_points(self):
        """Получение размера А3 в points (единицах PDF)"""
        width_points = self.A3_WIDTH_MM * self.MM_TO_POINTS
        height_points = self.A3_HEIGHT_MM * self.MM_TO_POINTS
        return (width_points, height_points)
    
    def get_format_size_in_points(self, format_name='A4'):
        """Получение размера формата в points"""
        if format_name == 'A3':
            return self.get_a3_size_in_points()
        else:
            return self.get_a4_size_in_points()
    
    def generate_masks(self, page_num=0, overlap_percent=15, format_hint=None, 
                      mask_format='A4', mask_landscape=False):
        """
        Генерация масок с перекрытием для страницы
        
        Args:
            page_num: номер страницы
            overlap_percent: процент перекрытия
            format_hint: подсказка о формате чертежа
            mask_format: формат маски ('A4' или 'A3')
            mask_landscape: ориентация маски (True - альбомная, False - книжная)
        
        Returns:
            list: список словарей с данными масок
        """
        page_size = self.get_page_size_points(page_num)
        if not page_size:
            return []
        
        page_width, page_height = page_size
        
        # Получаем размеры маски
        mask_width, mask_height = self.get_format_size_in_points(mask_format)
        
        # Применяем ориентацию
        if mask_landscape:
            mask_width, mask_height = mask_height, mask_width
        
        # Вычисляем перекрытие
        overlap = overlap_percent / 100.0
        
        # Эффективный шаг с учетом перекрытия
        step_width = mask_width * (1 - overlap)
        step_height = mask_height * (1 - overlap)
        
        masks = []
        
        # Вычисляем количество масок по вертикали и горизонтали
        cols = max(1, int((page_width - mask_width) / step_width) + 2)
        rows = max(1, int((page_height - mask_height) / step_height) + 2)
        
        # Генерируем сетку масок
        for row in range(rows):
            for col in range(cols):
                # Вычисляем позицию маски
                x = col * step_width
                y = row * step_height
                
                # Прерываем если маска полностью за пределами страницы
                if x >= page_width or y >= page_height:
                    continue
                
                # Определяем размеры текущей маски
                current_mask_width = min(mask_width, page_width - x)
                current_mask_height = min(mask_height, page_height - y)
                
                # Добавляем маску всегда (даже если частично выходит за границы)
                masks.append({
                    'x': x,
                    'y': y,
                    'width': current_mask_width,
                    'height': current_mask_height,
                    'is_landscape': mask_landscape,
                    'format': mask_format,
                    'row': row,
                    'col': col
                })
        
        return masks
    
    def divide_pdf(self, masks, output_dir, page_num=0):
        """
        Разделение PDF на части согласно маскам
        
        Args:
            masks: список данных масок
            output_dir: директория для сохранения
            page_num: номер страницы
        
        Returns:
            list: список путей к созданным файлам
        """
        if not self.is_loaded():
            raise Exception("PDF не загружен")
        
        page = self.get_page(page_num)
        if not page:
            raise Exception(f"Страница {page_num} не найдена")
        
        output_files = []
        base_name = os.path.splitext(os.path.basename(self.file_path))[0]
        
        for i, mask in enumerate(masks, 1):
            # Создаем новый PDF документ
            output_pdf = fitz.open()
            
            # Создаем новую страницу с размером маски
            new_page = output_pdf.new_page(
                width=mask['width'],
                height=mask['height']
            )
            
            # Копируем область из исходной страницы
            # Определяем область для копирования
            src_rect = fitz.Rect(
                mask['x'],
                mask['y'],
                mask['x'] + mask['width'],
                mask['y'] + mask['height']
            )
            
            # Целевая область (вся новая страница)
            dest_rect = fitz.Rect(0, 0, mask['width'], mask['height'])
            
            # Копируем содержимое с сохранением качества
            new_page.show_pdf_page(
                dest_rect,
                self.document,
                page_num,
                clip=src_rect
            )
            
            # Сохраняем файл
            output_file = os.path.join(
                output_dir,
                f"{base_name}_part_{i:03d}.pdf"
            )
            
            output_pdf.save(output_file)
            output_pdf.close()
            
            output_files.append(output_file)
        
        return output_files
    
    def close(self):
        """Закрытие документа"""
        if self.document:
            self.document.close()
            self.document = None
            self.file_path = None
            self.page_count = 0
            self.current_page = None

