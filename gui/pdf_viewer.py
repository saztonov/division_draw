"""
PDF Viewer с поддержкой интерактивных масок
"""
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsPixmapItem
from PySide6.QtCore import Qt, QRectF, Signal, QPointF
from PySide6.QtGui import QPixmap, QImage, QPen, QColor, QBrush, QPainter
import fitz  # PyMuPDF


class MaskItem(QGraphicsRectItem):
    """Интерактивная маска А4"""
    
    def __init__(self, rect, mask_id, is_landscape=False):
        super().__init__(rect)
        self.mask_id = mask_id
        self.is_landscape = is_landscape
        self.is_selected = False
        
        # Стиль маски
        self.setFlags(
            QGraphicsRectItem.ItemIsMovable | 
            QGraphicsRectItem.ItemIsSelectable |
            QGraphicsRectItem.ItemSendsGeometryChanges
        )
        
        self.update_style()
        
    def update_style(self):
        """Обновление визуального стиля маски"""
        if self.is_selected:
            pen = QPen(QColor(0, 120, 215), 3, Qt.SolidLine)
            brush = QBrush(QColor(0, 120, 215, 40))
        else:
            pen = QPen(QColor(255, 0, 0), 2, Qt.DashLine)
            brush = QBrush(QColor(255, 0, 0, 20))
        
        self.setPen(pen)
        self.setBrush(brush)
    
    def set_selected(self, selected):
        """Установка состояния выделения"""
        self.is_selected = selected
        self.update_style()
    
    def rotate_90(self):
        """Поворот маски на 90 градусов"""
        rect = self.rect()
        center = rect.center()
        
        # Меняем ширину и высоту местами
        new_width = rect.height()
        new_height = rect.width()
        
        # Создаем новый прямоугольник с центром в той же точке
        new_rect = QRectF(
            center.x() - new_width / 2,
            center.y() - new_height / 2,
            new_width,
            new_height
        )
        
        self.setRect(new_rect)
        self.is_landscape = not self.is_landscape
    
    def get_mask_data(self):
        """Получение данных маски для разделения PDF"""
        rect = self.rect()
        pos = self.pos()
        
        return {
            'id': self.mask_id,
            'x': pos.x() + rect.x(),
            'y': pos.y() + rect.y(),
            'width': rect.width(),
            'height': rect.height(),
            'is_landscape': self.is_landscape
        }


class PDFViewer(QGraphicsView):
    """Виджет для отображения PDF и работы с масками"""
    
    mask_selected = Signal(str)  # Сигнал при выборе маски
    
    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        
        self.pdf_handler = None
        self.current_page = 0
        self.render_zoom = 2.0  # Zoom для рендеринга PDF
        self.pdf_pixmap_item = None
        self.masks = []
        self.selected_mask = None
        self.next_mask_id = 1
        
        # Настройки view
        self.setDragMode(QGraphicsView.NoDrag)  # Изначально без драга
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        
        # Для управления режимом перетаскивания
        self.is_panning = False
        
    def load_pdf(self, page_num=0):
        """Загрузка и отображение страницы PDF"""
        if not self.pdf_handler or not self.pdf_handler.is_loaded():
            return
        
        self.current_page = page_num
        
        # Очищаем сцену
        self.scene.clear()
        self.masks.clear()
        self.selected_mask = None
        
        # Получаем изображение страницы с нужным zoom
        pixmap = self.pdf_handler.render_page(page_num, zoom=self.render_zoom)
        
        # Добавляем изображение на сцену
        self.pdf_pixmap_item = QGraphicsPixmapItem(pixmap)
        self.scene.addItem(self.pdf_pixmap_item)
        
        # Устанавливаем размер сцены
        self.scene.setSceneRect(self.pdf_pixmap_item.boundingRect())
        
        # Подгоняем под размер окна
        self.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
    
    def set_masks(self, masks_data):
        """Установка масок на основе данных"""
        # Удаляем старые маски
        for mask in self.masks:
            self.scene.removeItem(mask)
        
        self.masks.clear()
        self.selected_mask = None
        
        # Создаем новые маски с учетом zoom фактора
        for mask_data in masks_data:
            mask_item = MaskItem(
                QRectF(
                    mask_data['x'] * self.render_zoom, 
                    mask_data['y'] * self.render_zoom, 
                    mask_data['width'] * self.render_zoom, 
                    mask_data['height'] * self.render_zoom
                ),
                self.next_mask_id,
                mask_data.get('is_landscape', False)
            )
            self.next_mask_id += 1
            
            self.scene.addItem(mask_item)
            self.masks.append(mask_item)
    
    def add_mask(self, mask_format='A4', landscape=False):
        """Добавление новой маски"""
        if not self.pdf_handler or not self.pdf_handler.is_loaded():
            return
        
        # Получаем размеры маски в пикселях PDF и применяем zoom
        mask_width, mask_height = self.pdf_handler.get_format_size_in_points(mask_format)
        mask_width *= self.render_zoom
        mask_height *= self.render_zoom
        
        if landscape:
            mask_width, mask_height = mask_height, mask_width
        
        # Размещаем в центре видимой области
        view_center = self.mapToScene(self.viewport().rect().center())
        
        mask_rect = QRectF(
            view_center.x() - mask_width / 2,
            view_center.y() - mask_height / 2,
            mask_width,
            mask_height
        )
        
        mask_item = MaskItem(mask_rect, self.next_mask_id, landscape)
        self.next_mask_id += 1
        
        self.scene.addItem(mask_item)
        self.masks.append(mask_item)
    
    def get_masks(self):
        """Получение данных всех масок (в оригинальных координатах PDF)"""
        masks_data = []
        for mask in self.masks:
            data = mask.get_mask_data()
            # Конвертируем обратно в координаты PDF
            masks_data.append({
                'id': data['id'],
                'x': data['x'] / self.render_zoom,
                'y': data['y'] / self.render_zoom,
                'width': data['width'] / self.render_zoom,
                'height': data['height'] / self.render_zoom,
                'is_landscape': data['is_landscape']
            })
        return masks_data
    
    def mousePressEvent(self, event):
        """Обработка нажатия мыши для выбора масок"""
        # Получаем позицию в координатах сцены
        scene_pos = self.mapToScene(event.pos())
        
        # Получаем объект под курсором в сцене
        item = self.scene.itemAt(scene_pos, self.transform())
        
        # Сбрасываем предыдущее выделение
        if self.selected_mask:
            self.selected_mask.set_selected(False)
            self.selected_mask = None
        
        # Если это маска, выделяем её
        if isinstance(item, MaskItem):
            self.selected_mask = item
            item.set_selected(True)
            
            # Временно отключаем ScrollHandDrag для перемещения маски
            self.setDragMode(QGraphicsView.NoDrag)
            
            # Отправляем сигнал с информацией о маске
            mask_info = (f"Маска #{item.mask_id}\n"
                        f"Ориентация: {'альбомная' if item.is_landscape else 'книжная'}\n"
                        f"Размер: {item.rect().width():.1f} × {item.rect().height():.1f}")
            
            main_window = self.window()
            if hasattr(main_window, 'update_mask_info'):
                main_window.update_mask_info(mask_info)
        else:
            # Если кликнули не на маску, включаем ScrollHandDrag
            self.setDragMode(QGraphicsView.ScrollHandDrag)
            
            # Сбрасываем выделение
            main_window = self.window()
            if hasattr(main_window, 'update_mask_info'):
                main_window.update_mask_info(None)
        
        super().mousePressEvent(event)
    
    def rotate_selected_mask(self):
        """Поворот выбранной маски"""
        if self.selected_mask:
            self.selected_mask.rotate_90()
            
            # Обновляем информацию о маске
            mask_info = (f"Маска #{self.selected_mask.mask_id}\n"
                        f"Ориентация: {'альбомная' if self.selected_mask.is_landscape else 'книжная'}\n"
                        f"Размер: {self.selected_mask.rect().width():.1f} × {self.selected_mask.rect().height():.1f}")
            
            main_window = self.window()
            if hasattr(main_window, 'update_mask_info'):
                main_window.update_mask_info(mask_info)
    
    def delete_selected_mask(self):
        """Удаление выбранной маски"""
        if self.selected_mask:
            self.scene.removeItem(self.selected_mask)
            self.masks.remove(self.selected_mask)
            self.selected_mask = None
            
            # Обновляем информацию
            main_window = self.window()
            if hasattr(main_window, 'update_mask_info'):
                main_window.update_mask_info(None)
    
    def clear_all_masks(self):
        """Очистка всех масок"""
        for mask in self.masks:
            self.scene.removeItem(mask)
        
        self.masks.clear()
        self.selected_mask = None
        
        # Обновляем информацию
        main_window = self.window()
        if hasattr(main_window, 'update_mask_info'):
            main_window.update_mask_info(None)
    
    def mouseReleaseEvent(self, event):
        """Обработка отпускания кнопки мыши"""
        super().mouseReleaseEvent(event)
        # Восстанавливаем ScrollHandDrag если маска не выбрана
        if not self.selected_mask:
            self.setDragMode(QGraphicsView.ScrollHandDrag)
    
    def wheelEvent(self, event):
        """Обработка колеса мыши для масштабирования"""
        # Zoom factor
        zoom_in_factor = 1.15
        zoom_out_factor = 1 / zoom_in_factor
        
        # Сохраняем старую позицию
        old_pos = self.mapToScene(event.position().toPoint())
        
        # Zoom
        if event.angleDelta().y() > 0:
            zoom_factor = zoom_in_factor
        else:
            zoom_factor = zoom_out_factor
        
        self.scale(zoom_factor, zoom_factor)
        
        # Получаем новую позицию
        new_pos = self.mapToScene(event.position().toPoint())
        
        # Корректируем позицию
        delta = new_pos - old_pos
        self.translate(delta.x(), delta.y())
    
    def keyPressEvent(self, event):
        """Обработка нажатий клавиш"""
        if event.key() == Qt.Key_Delete and self.selected_mask:
            self.delete_selected_mask()
        elif event.key() == Qt.Key_R and self.selected_mask:
            self.rotate_selected_mask()
        else:
            super().keyPressEvent(event)

