from PySide6.QtCore import QObject, Signal
from src.models.com_ports_manager import ComPortsManager
from src.models.com_port_model import ComPortModel
from src.viewmodels.com_port_viewmodel import ComPortViewModel

class ComPortsManagerViewModel(QObject):
    """ViewModel для управления несколькими COM портами"""
    
    # Сигналы
    ports_discovered = Signal(list)  # Сигнал при обнаружении портов
    port_connected = Signal(str)      # Сигнал при подключении к порту
    port_disconnected = Signal(str)    # Сигнал при отключении от порту
    data_received = Signal(str, str)  # Сигнал при получении данных
    error_occurred = Signal(str, str)  # Сигнал при ошибке
    
    def __init__(self):
        super().__init__()
        self.com_ports_manager = ComPortsManager()
        self.port_viewmodels = {}  # Словарь для хранения ViewModel портов
        
        # Подключаем сигналы менеджера портов
        self.com_ports_manager.port_discovered.connect(self.on_ports_discovered)
        self.com_ports_manager.port_connected.connect(self.on_port_connected)
        self.com_ports_manager.port_disconnected.connect(self.on_port_disconnected)
        self.com_ports_manager.data_received.connect(self.on_data_received)
        self.com_ports_manager.error_occurred.connect(self.on_error_occurred)
    
    def on_ports_discovered(self, port_names):
        """Обработка обнаружения портов"""
        self.ports_discovered.emit(port_names)
    
    def on_port_connected(self, port_name):
        """Обработка подключения к порту"""
        self.port_connected.emit(port_name)
    
    def on_port_disconnected(self, port_name):
        """Обработка отключения от порту"""
        self.port_disconnected.emit(port_name)
    
    def on_data_received(self, port_name, data):
        """Обработка получения данных"""
        self.data_received.emit(port_name, data)
    
    def on_error_occurred(self, port_name, error_message):
        """Обработка ошибки"""
        self.error_occurred.emit(port_name, error_message)
    
    def get_available_ports(self):
        """Получение списка доступных портов"""
        return self.com_ports_manager.get_available_ports()
    
    def get_port_viewmodel(self, port_name):
        """Получение ViewModel порта"""
        if port_name not in self.port_viewmodels:
            # Создаем новую ViewModel для порта
            model = self.com_ports_manager.get_port_model(port_name)
            if model:
                viewmodel = ComPortViewModel(model)
                self.port_viewmodels[port_name] = viewmodel
        return self.port_viewmodels.get(port_name)
    
    def connect_port(self, port_name, baud_rate=9600, data_bits=8, parity='N', stop_bits=1):
        """Подключение к COM порту"""
        return self.com_ports_manager.connect_port(port_name, baud_rate, data_bits, parity, stop_bits)
    
    def disconnect_port(self, port_name):
        """Отключение от COM порта"""
        return self.com_ports_manager.disconnect_port(port_name)
    
    def send_data(self, port_name, data):
        """Отправка данных в COM порт"""
        return self.com_ports_manager.send_data(port_name, data)
    
    def get_port_info(self, port_name):
        """Получение информации о порте"""
        return self.com_ports_manager.get_port_info(port_name)
    
    def clear_received_data(self, port_name):
        """Очистка полученных данных"""
        return self.com_ports_manager.clear_received_data(port_name)
    
    def set_port_parameters(self, port_name, baud_rate=None, data_bits=None, parity=None, stop_bits=None):
        """Установка параметров порта"""
        return self.com_ports_manager.set_port_parameters(port_name, baud_rate, data_bits, parity, stop_bits)
    
    def get_all_ports_info(self):
        """Получение информации обо всех портах"""
        ports_info = {}
        for port_name in self.com_ports_manager.get_available_ports():
            ports_info[port_name] = self.get_port_info(port_name)
        return ports_info
    
    def get_connected_ports(self):
        """Получение списка подключенных портов"""
        connected_ports = []
        for port_name, info in self.get_all_ports_info().items():
            if info and info['is_open']:
                connected_ports.append(port_name)
        return connected_ports
    
    def get_disconnected_ports(self):
        """Получение списка отключенных портов"""
        disconnected_ports = []
        for port_name, info in self.get_all_ports_info().items():
            if info and not info['is_open']:
                disconnected_ports.append(port_name)
        return disconnected_ports
    
    def connect_all_ports(self, baud_rate=9600, data_bits=8, parity='N', stop_bits=1):
        """Подключение ко всем доступным портам"""
        results = {}
        for port_name in self.get_available_ports():
            results[port_name] = self.connect_port(port_name, baud_rate, data_bits, parity, stop_bits)
        return results
    
    def disconnect_all_ports(self):
        """Отключение всех портов"""
        results = {}
        for port_name in self.get_connected_ports():
            results[port_name] = self.disconnect_port(port_name)
        return results
    
    def send_data_to_all(self, data):
        """Отправка данных во все подключенные порты"""
        results = {}
        for port_name in self.get_connected_ports():
            results[port_name] = self.send_data(port_name, data)
        return results
    
    def clear_all_received_data(self):
        """Очистка полученных данных во всех портах"""
        results = {}
        for port_name in self.get_available_ports():
            results[port_name] = self.clear_received_data(port_name)
        return results
    
    def get_port_statistics(self, port_name):
        """Получение статистики порта"""
        info = self.get_port_info(port_name)
        if not info:
            return None
        
        # Подсчет количества полученных байт
        received_data = info.get('received_data', '')
        byte_count = len(received_data)
        
        # Подсчет строк
        line_count = received_data.count('\n') if '\n' in received_data else 1
        
        return {
            'port_name': port_name,
            'is_connected': info.get('is_open', False),
            'baud_rate': info.get('baud_rate', 0),
            'data_bits': info.get('data_bits', 0),
            'parity': info.get('parity', 'N'),
            'stop_bits': info.get('stop_bits', 0),
            'received_bytes': byte_count,
            'received_lines': line_count,
            'last_activity': 'Unknown'  # TODO: Добавить отслеживание времени последней активности
        }
    
    def get_all_ports_statistics(self):
        """Получение статистики по всем портам"""
        statistics = {}
        for port_name in self.get_available_ports():
            statistics[port_name] = self.get_port_statistics(port_name)
        return statistics
    
    def cleanup(self):
        """Очистка ресурсов"""
        self.com_ports_manager.cleanup()
        self.port_viewmodels.clear()