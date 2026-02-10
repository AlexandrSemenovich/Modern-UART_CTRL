import serial
import serial.tools.list_ports
from PySide6.QtCore import QObject, Signal, QTimer
from src.models.com_port_model import ComPortModel
from src.utils.translator import tr

class ComPortsManager(QObject):
    """Менеджер для управления несколькими COM портами"""
    
    # Сигналы
    port_discovered = Signal(list)  # Сигнал при обнаружении портов
    port_connected = Signal(str)    # Сигнал при подключении к порту
    port_disconnected = Signal(str)  # Сигнал при отключении от порту
    data_received = Signal(str, str)  # Сигнал при получении данных (port_name, data)
    error_occurred = Signal(str, str)  # Сигнал при ошибке (port_name, error_message)
    
    def __init__(self):
        super().__init__()
        self.com_ports = {}  # Словарь для хранения моделей портов
        self.serial_connections = {}  # Словарь для хранения соединений
        self.monitoring_timers = {}  # Словарь для хранения таймеров мониторинга
        
        # Таймер для автоматического обнаружения портов
        self.discovery_timer = QTimer()
        self.discovery_timer.timeout.connect(self.discover_ports)
        self.discovery_timer.start(5000)  # Обнаружение каждые 5 секунд
        
        # Начальное обнаружение портов
        self.discover_ports()
    
    def discover_ports(self):
        """Обнаружение доступных COM портов"""
        available_ports = serial.tools.list_ports.comports()
        port_names = [port.device for port in available_ports]
        
        # Обновляем список портов
        for port_name in port_names:
            if port_name not in self.com_ports:
                # Создаем новую модель порта
                model = ComPortModel()
                model.set_port_name(port_name)
                self.com_ports[port_name] = model
        
        # Удаляем порты, которые больше не доступны
        ports_to_remove = []
        for port_name in self.com_ports:
            if port_name not in port_names:
                ports_to_remove.append(port_name)
        
        for port_name in ports_to_remove:
            self.disconnect_port(port_name)
            del self.com_ports[port_name]
        
        # Эмитируем сигнал об обнаружении портов
        self.port_discovered.emit(port_names)
    
    def get_available_ports(self):
        """Получение списка доступных портов"""
        return list(self.com_ports.keys())
    
    def get_port_model(self, port_name):
        """Получение модели порта"""
        return self.com_ports.get(port_name)
    
    def connect_port(self, port_name, baud_rate=115200, data_bits=8, parity='N', stop_bits=1):
        """Подключение к COM порту"""
        if port_name in self.serial_connections:
            self.error_occurred.emit(
                port_name,
                tr("manager_port_already_connected", "Port already connected")
            )
            return False
        
        try:
            # Создаем соединение
            ser = serial.Serial(
                port=port_name,
                baudrate=baud_rate,
                bytesize=data_bits,
                parity=parity,
                stopbits=stop_bits,
                timeout=1
            )
            
            # Обновляем модель порта
            if port_name in self.com_ports:
                model = self.com_ports[port_name]
                model.set_baud_rate(baud_rate)
                model.set_data_bits(data_bits)
                model.set_parity(parity)
                model.set_stop_bits(stop_bits)
                model.set_open(True)
            
            # Сохраняем соединение
            self.serial_connections[port_name] = ser
            
            # Запускаем мониторинг порта
            self.start_monitoring(port_name)
            
            # Эмитируем сигнал
            self.port_connected.emit(port_name)
            return True
            
        except Exception as e:
            error_msg = tr("manager_failed_connect", "Failed to connect to {port}: {error}").format(
                port=port_name,
                error=str(e)
            )
            self.error_occurred.emit(port_name, error_msg)
            return False
    
    def disconnect_port(self, port_name):
        """Отключение от COM порта"""
        if port_name not in self.serial_connections:
            return False
        
        try:
            # Останавливаем мониторинг
            self.stop_monitoring(port_name)
            
            # Закрываем соединение
            ser = self.serial_connections[port_name]
            ser.close()
            del self.serial_connections[port_name]
            
            # Обновляем модель порта
            if port_name in self.com_ports:
                model = self.com_ports[port_name]
                model.set_open(False)
                model.set_received_data("")
            
            # Эмитируем сигнал
            self.port_disconnected.emit(port_name)
            return True
            
        except Exception as e:
            error_msg = tr("manager_failed_disconnect", "Failed to disconnect from {port}: {error}").format(
                port=port_name,
                error=str(e)
            )
            self.error_occurred.emit(port_name, error_msg)
            return False
    
    def send_data(self, port_name, data):
        """Отправка данных в COM порт"""
        if port_name not in self.serial_connections:
            self.error_occurred.emit(
                port_name,
                tr("manager_port_not_connected", "Port not connected")
            )
            return False
        
        try:
            ser = self.serial_connections[port_name]
            
            # Если данные в строковом формате, кодируем их в байты
            if isinstance(data, str):
                data = data.encode('utf-8')
            
            # Отправляем данные
            ser.write(data)
            
            return True
            
        except Exception as e:
            error_msg = tr("manager_failed_send", "Failed to send data to {port}: {error}").format(
                port=port_name,
                error=str(e)
            )
            self.error_occurred.emit(port_name, error_msg)
            return False
    
    def start_monitoring(self, port_name):
        """Запуск мониторинга порта"""
        if port_name in self.monitoring_timers:
            return
        
        timer = QTimer()
        timer.timeout.connect(lambda: self.monitor_port(port_name))
        timer.start(100)  # Мониторинг каждые 100ms
        self.monitoring_timers[port_name] = timer
    
    def stop_monitoring(self, port_name):
        """Остановка мониторинга порта"""
        if port_name in self.monitoring_timers:
            timer = self.monitoring_timers[port_name]
            timer.stop()
            del self.monitoring_timers[port_name]
    
    def monitor_port(self, port_name):
        """Мониторинг порта на предмет входящих данных"""
        if port_name not in self.serial_connections:
            return
        
        try:
            ser = self.serial_connections[port_name]
            
            # Проверяем есть ли данные для чтения
            if ser.in_waiting > 0:
                # Читаем данные
                data = ser.read(ser.in_waiting)
                
                # Декодируем данные
                try:
                    text_data = data.decode('utf-8')
                except UnicodeDecodeError:
                    # Если не удалось декодировать как UTF-8, используем hex
                    text_data = data.hex()
                
                # Обновляем модель порта
                if port_name in self.com_ports:
                    model = self.com_ports[port_name]
                    current_data = model.received_data
                    model.set_received_data(current_data + text_data)
                
                # Эмитируем сигнал
                self.data_received.emit(port_name, text_data)
                
        except Exception as e:
            error_msg = tr("manager_monitor_error", "Error monitoring {port}: {error}").format(
                port=port_name,
                error=str(e)
            )
            self.error_occurred.emit(port_name, error_msg)
            self.stop_monitoring(port_name)
    
    def get_port_info(self, port_name):
        """Получение информации о порте"""
        if port_name not in self.com_ports:
            return None
        
        model = self.com_ports[port_name]
        return {
            'port_name': model.port_name,
            'is_open': model.is_open,
            'baud_rate': model.baud_rate,
            'data_bits': model.data_bits,
            'parity': model.parity,
            'stop_bits': model.stop_bits,
            'received_data': model.received_data
        }
    
    def clear_received_data(self, port_name):
        """Очистка полученных данных"""
        if port_name in self.com_ports:
            model = self.com_ports[port_name]
            model.set_received_data("")
    
    def set_port_parameters(self, port_name, baud_rate=None, data_bits=None, parity=None, stop_bits=None):
        """Установка параметров порта"""
        if port_name not in self.com_ports:
            return False
        
        model = self.com_ports[port_name]
        
        # Если порт открыт, нужно перезапустить соединение с новыми параметрами
        if model.is_open:
            # Получаем текущие параметры
            current_baud = model.baud_rate
            current_data = model.data_bits
            current_parity = model.parity
            current_stop = model.stop_bits
            
            # Отключаем порт
            self.disconnect_port(port_name)
            
            # Устанавливаем новые параметры
            if baud_rate is not None:
                model.set_baud_rate(baud_rate)
            if data_bits is not None:
                model.set_data_bits(data_bits)
            if parity is not None:
                model.set_parity(parity)
            if stop_bits is not None:
                model.set_stop_bits(stop_bits)
            
            # Подключаем порт с новыми параметрами
            self.connect_port(port_name, 
                            baud_rate or current_baud,
                            data_bits or current_data,
                            parity or current_parity,
                            stop_bits or current_stop)
        else:
            # Если порт закрыт, просто обновляем параметры
            if baud_rate is not None:
                model.set_baud_rate(baud_rate)
            if data_bits is not None:
                model.set_data_bits(data_bits)
            if parity is not None:
                model.set_parity(parity)
            if stop_bits is not None:
                model.set_stop_bits(stop_bits)
        
        return True
    
    def cleanup(self):
        """Очистка ресурсов"""
        # Останавливаем таймер обнаружения
        self.discovery_timer.stop()
        
        # Отключаем все порты
        ports_to_disconnect = list(self.serial_connections.keys())
        for port_name in ports_to_disconnect:
            self.disconnect_port(port_name)
        
        # Очищаем словари
        self.com_ports.clear()
        self.serial_connections.clear()
        self.monitoring_timers.clear()
