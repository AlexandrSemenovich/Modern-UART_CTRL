# Стили жидкого стекла для PyQt6

# Основные цвета
class GlassColors:
    # Цвета для темной темы (по умолчанию)
    DARK_PRIMARY = "#1e1e1e"
    DARK_SECONDARY = "#2d2d2d"
    DARK_ACCENT = "#007aff"
    DARK_TEXT_PRIMARY = "#ffffff"
    DARK_TEXT_SECONDARY = "#b0b0b0"
    DARK_GLASS_COLOR = "rgba(255, 255, 255, 0.1)"
    DARK_GLASS_BORDER = "rgba(255, 255, 255, 0.2)"
    DARK_SHADOW_COLOR = "rgba(0, 0, 0, 0.3)"
    
    # Цвета для светлой темы
    LIGHT_PRIMARY = "#ffffff"
    LIGHT_SECONDARY = "#f5f5f5"
    LIGHT_ACCENT = "#007aff"
    LIGHT_TEXT_PRIMARY = "#000000"
    LIGHT_TEXT_SECONDARY = "#666666"
    LIGHT_GLASS_COLOR = "rgba(0, 0, 0, 0.05)"
    LIGHT_GLASS_BORDER = "rgba(0, 0, 0, 0.1)"
    LIGHT_SHADOW_COLOR = "rgba(0, 0, 0, 0.1)"

# Стили для виджетов
class GlassStyles:
    @staticmethod
    def get_glass_style():
        return """
        QWidget {
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 12px;
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }
        """
    
    @staticmethod
    def get_button_style():
        return """
        QPushButton {
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 8px;
            padding: 10px 20px;
            color: #ffffff;
            font-weight: 500;
            font-size: 14px;
        }
        QPushButton:hover {
            background: rgba(255, 255, 255, 0.2);
            transform: translateY(-2px);
        }
        QPushButton:pressed {
            transform: translateY(0);
        }
        """
    
    @staticmethod
    def get_group_box_style():
        return """
        QGroupBox {
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 12px;
            padding: 15px;
            margin-top: 10px;
        }
        QGroupBox::title {
            color: #ffffff;
            font-weight: 600;
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 5px;
        }
        """
    
    @staticmethod
    def get_text_edit_style():
        return """
        QTextEdit {
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 8px;
            padding: 10px 15px;
            color: #ffffff;
            font-size: 14px;
        }
        """
    
    @staticmethod
    def get_combo_box_style():
        return """
        QComboBox {
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 8px;
            padding: 10px 15px;
            color: #ffffff;
            font-size: 14px;
        }
        QComboBox::drop-down {
            border: none;
            padding-right: 10px;
        }
        QComboBox::down-arrow {
            image: url(down_arrow.png);
            width: 12px;
            height: 12px;
        }
        """
    
    @staticmethod
    def get_label_style():
        return """
        QLabel {
            color: #ffffff;
            font-weight: 600;
        }
        """
    
    @staticmethod
    def get_light_theme_style():
        return """
        QWidget {
            background: rgba(0, 0, 0, 0.05);
            border: 1px solid rgba(0, 0, 0, 0.1);
            border-radius: 12px;
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }
        QPushButton {
            background: rgba(0, 0, 0, 0.05);
            border: 1px solid rgba(0, 0, 0, 0.1);
            color: #000000;
        }
        QPushButton:hover {
            background: rgba(0, 0, 0, 0.1);
        }
        QGroupBox {
            background: rgba(0, 0, 0, 0.05);
            border: 1px solid rgba(0, 0, 0, 0.1);
        }
        QGroupBox::title {
            color: #000000;
        }
        QTextEdit {
            background: rgba(0, 0, 0, 0.05);
            border: 1px solid rgba(0, 0, 0, 0.1);
            color: #000000;
        }
        QComboBox {
            background: rgba(0, 0, 0, 0.05);
            border: 1px solid rgba(0, 0, 0, 0.1);
            color: #000000;
        }
        QLabel {
            color: #000000;
        }
        """