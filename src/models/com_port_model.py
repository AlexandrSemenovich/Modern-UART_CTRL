from PySide6.QtCore import QObject, Signal, Property
from src.models.base_model import BaseModel

class ComPortModel(BaseModel):
    """Модель для управления одним COM портом"""
    
    port_name_changed = Signal()
    open_changed = Signal()
    baud_rate_changed = Signal()
    data_bits_changed = Signal()
    parity_changed = Signal()
    stop_bits_changed = Signal()
    received_data_changed = Signal()
    
    def __init__(self):
        super().__init__()
        self._port_name = ""
        self._is_open = False
        self._baud_rate = 9600
        self._data_bits = 8
        self._parity = "N"
        self._stop_bits = 1
        self._received_data = ""
    
    def set_port_name(self, name):
        """Установка имени порта"""
        if self._port_name != name:
            self._port_name = name
            self.port_name_changed.emit()
    
    def set_open(self, open_state):
        """Установка состояния открытия порта"""
        if self._is_open != open_state:
            self._is_open = open_state
            self.open_changed.emit()
    
    def set_baud_rate(self, rate):
        """Установка скорости передачи"""
        if self._baud_rate != rate:
            self._baud_rate = rate
            self.baud_rate_changed.emit()
    
    def set_data_bits(self, bits):
        """Установка количества бит данных"""
        if self._data_bits != bits:
            self._data_bits = bits
            self.data_bits_changed.emit()
    
    def set_parity(self, parity):
        """Установка четности"""
        if self._parity != parity:
            self._parity = parity
            self.parity_changed.emit()
    
    def set_stop_bits(self, bits):
        """Установка количества стоп-битов"""
        if self._stop_bits != bits:
            self._stop_bits = bits
            self.stop_bits_changed.emit()
    
    def set_received_data(self, data):
        """Установка полученных данных"""
        if self._received_data != data:
            self._received_data = data
            self.received_data_changed.emit()
    
    @Property(str, notify=port_name_changed)
    def port_name(self):
        return self._port_name
    
    @port_name.setter
    def port_name(self, value):
        self.set_port_name(value)
    
    @Property(bool, notify=open_changed)
    def is_open(self):
        return self._is_open
    
    @is_open.setter
    def is_open(self, value):
        self.set_open(value)
    
    @Property(int, notify=baud_rate_changed)
    def baud_rate(self):
        return self._baud_rate
    
    @baud_rate.setter
    def baud_rate(self, value):
        self.set_baud_rate(value)
    
    @Property(int, notify=data_bits_changed)
    def data_bits(self):
        return self._data_bits
    
    @data_bits.setter
    def data_bits(self, value):
        self.set_data_bits(value)
    
    @Property(str, notify=parity_changed)
    def parity(self):
        return self._parity
    
    @parity.setter
    def parity(self, value):
        self.set_parity(value)
    
    @Property(int, notify=stop_bits_changed)
    def stop_bits(self):
        return self._stop_bits
    
    @stop_bits.setter
    def stop_bits(self, value):
        self.set_stop_bits(value)
    
    @Property(str, notify=received_data_changed)
    def received_data(self):
        return self._received_data
    
    @received_data.setter
    def received_data(self, value):
        self.set_received_data(value)