import html
from src.viewmodels.main_viewmodel import MainViewModel
from src.models.serial_worker import SerialWorker


def test_main_viewmodel_format_rx_tx_system():
    vm = MainViewModel()

    # Default: show_time and show_source True
    rx_html = vm.format_rx('CPU1', 'OK\r\n')
    assert 'RX(CPU1):' in rx_html
    assert 'OK' in rx_html

    tx_html = vm.format_tx('CPU2', 'PING')
    assert 'TX(CPU2):' in tx_html
    assert 'PING' in tx_html

    sys_html = vm.format_system('CPU1', 'Connected')
    assert 'SYS(CPU1):' in sys_html
    assert 'Connected' in sys_html

    # Hide time and source
    vm.set_display_options(False, False)
    rx_no_meta = vm.format_rx('CPU1', 'LINE')
    assert 'RX(' not in rx_no_meta
    assert '[' not in rx_no_meta  # no timestamp


def test_main_viewmodel_cache_and_filter():
    vm = MainViewModel()
    vm.clear_cache()

    html1 = "<span>hello</span><br>"
    plain1 = vm.strip_html(html1)
    vm.cache_log_line('cpu1', html1, plain1)

    html2 = "<span>world</span><br>"
    plain2 = vm.strip_html(html2)
    vm.cache_log_line('cpu1', html2, plain2)

    # No filter
    content = vm.filter_cache('cpu1', '')
    assert 'hello' in content and 'world' in content

    # Filter matching one
    filtered = vm.filter_cache('cpu1', 'world')
    assert 'world' in filtered and 'hello' not in filtered


def test_serial_worker_configure_and_write_queue():
    worker = SerialWorker('CPU1')
    worker.configure('COM1', 115200)
    assert getattr(worker, '_port_name', None) == 'COM1'
    assert getattr(worker, '_baud', None) == 115200

    # Test write enqueues data
    worker.write('TEST')
    # internal queue should have the item
    item = worker._write_q.get_nowait()
    assert item == 'TEST'
