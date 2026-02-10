"""
Legacy prototype moved to examples/pyqt_app.py

This file is kept as a small wrapper to avoid duplicate source and
to point developers to the canonical example location.
"""
import sys
import os
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXAMPLE = os.path.join(ROOT, 'examples', 'pyqt_app.py')

if __name__ == '__main__':
    if os.path.exists(EXAMPLE):
        sys.exit(subprocess.run([sys.executable, EXAMPLE], cwd=ROOT).returncode)
    else:
        print('Example pyqt_app not found. See examples/ directory.')
        sys.exit(1)
        left_v.setContentsMargins(10, 10, 10, 10)

        # CPU1 Port Settings
        grp1 = QtWidgets.QGroupBox('CPU 1')
        grp1.setObjectName('grp_cpu1')
        grp1.setMinimumHeight(140)
        g1_layout = QtWidgets.QFormLayout()
        g1_layout.setSpacing(8)
        g1_layout.setContentsMargins(8, 8, 8, 8)
        self.cb_port_1 = QtWidgets.QComboBox(); self.cb_port_1.setObjectName('cb_port_1')
        self.cb_port_1.setMinimumHeight(28)
        self.btn_scan_1 = QtWidgets.QPushButton('Scan'); self.btn_scan_1.setObjectName('btn_scan_1')
        self.btn_scan_1.setMinimumHeight(28)
        self.btn_scan_1.setMaximumWidth(70)
        h1 = QtWidgets.QHBoxLayout(); h1.setSpacing(5)
        h1.addWidget(self.cb_port_1, 1)
        h1.addWidget(self.btn_scan_1, 0)
        g1_layout.addRow('Port:', h1)
        self.cb_baud_1 = QtWidgets.QComboBox(); self.cb_baud_1.setObjectName('cb_baud_1')
        self.cb_baud_1.setMinimumHeight(28)
        self.cb_baud_1.addItems(['9600','19200','38400','57600','115200'])
        g1_layout.addRow('Baud:', self.cb_baud_1)
        self.btn_connect_1 = QtWidgets.QPushButton('Connect'); self.btn_connect_1.setObjectName('btn_connect_1')
        self.btn_connect_1.setMinimumHeight(35)
        g1_layout.addRow(self.btn_connect_1)
        grp1.setLayout(g1_layout)
        left_v.addWidget(grp1, 0)

        # CPU2 Port Settings
        grp2 = QtWidgets.QGroupBox('CPU 2')
        grp2.setObjectName('grp_cpu2')
        grp2.setMinimumHeight(140)
        g2_layout = QtWidgets.QFormLayout()
        g2_layout.setSpacing(8)
        g2_layout.setContentsMargins(8, 8, 8, 8)
        self.cb_port_2 = QtWidgets.QComboBox(); self.cb_port_2.setObjectName('cb_port_2')
        self.cb_port_2.setMinimumHeight(28)
        self.btn_scan_2 = QtWidgets.QPushButton('Scan'); self.btn_scan_2.setObjectName('btn_scan_2')
        self.btn_scan_2.setMinimumHeight(28)
        self.btn_scan_2.setMaximumWidth(70)
        h2 = QtWidgets.QHBoxLayout(); h2.setSpacing(5)
        h2.addWidget(self.cb_port_2, 1)
        h2.addWidget(self.btn_scan_2, 0)
        g2_layout.addRow('Port:', h2)
        self.cb_baud_2 = QtWidgets.QComboBox(); self.cb_baud_2.setObjectName('cb_baud_2')
        self.cb_baud_2.setMinimumHeight(28)
        self.cb_baud_2.addItems(['9600','19200','38400','57600','115200'])
        g2_layout.addRow('Baud:', self.cb_baud_2)
        self.btn_connect_2 = QtWidgets.QPushButton('Connect'); self.btn_connect_2.setObjectName('btn_connect_2')
        self.btn_connect_2.setMinimumHeight(35)
        g2_layout.addRow(self.btn_connect_2)
        grp2.setLayout(g2_layout)
        left_v.addWidget(grp2, 0)

        # Input area for manual commands
        input_group = QtWidgets.QGroupBox(tr('data_transmission', 'Data Transmission'))
        input_group.setObjectName('grp_input')
        input_group.setMinimumHeight(150)
        in_layout = QtWidgets.QVBoxLayout()
        in_layout.setSpacing(8)
        in_layout.setContentsMargins(8, 8, 8, 8)
        self.le_command = QtWidgets.QLineEdit(); self.le_command.setObjectName('le_command')
        self.le_command.setMinimumHeight(32)
        self.le_command.setPlaceholderText("Enter command...")
        btns = QtWidgets.QHBoxLayout()
        btns.setSpacing(5)
        self.btn_send_cpu1 = QtWidgets.QPushButton(tr('send_to_cpu1', 'CPU1')); self.btn_send_cpu1.setObjectName('btn_send_cpu1')
        self.btn_send_cpu1.setMinimumHeight(32)
        self.btn_send_cpu2 = QtWidgets.QPushButton(tr('send_to_cpu2', 'CPU2')); self.btn_send_cpu2.setObjectName('btn_send_cpu2')
        self.btn_send_cpu2.setMinimumHeight(32)
        self.btn_send_both = QtWidgets.QPushButton(tr('send_to_both', '1+2')); self.btn_send_both.setObjectName('btn_send_both')
        self.btn_send_both.setMinimumHeight(32)
        btns.addWidget(self.btn_send_cpu1, 1)
        btns.addWidget(self.btn_send_cpu2, 1)
        btns.addWidget(self.btn_send_both, 1)
        in_layout.addWidget(self.le_command)
        in_layout.addLayout(btns)
        input_group.setLayout(in_layout)

        left_v.addWidget(input_group, 0)

        # counters and LED state
        self.tx_counts = [0, 0, 0]
        self.rx_counts = [0, 0, 0]

        left_v.addStretch()

        # CENTER: logs area
        logs_widget = QtWidgets.QWidget()
        logs_widget.setObjectName('logs_area')
        logs_widget.setMinimumWidth(400)
        logs_layout = QtWidgets.QVBoxLayout(logs_widget)
        logs_layout.setSpacing(5)
        logs_layout.setContentsMargins(5, 5, 5, 5)

        # Logging toolbar
        log_toolbar = QtWidgets.QHBoxLayout()
        log_toolbar.setSpacing(5)
        log_toolbar.setContentsMargins(0, 0, 0, 0)
        
        # Search field
        self.le_log_search = QtWidgets.QLineEdit()
        self.le_log_search.setObjectName('le_log_search')
        self.le_log_search.setPlaceholderText('Search logs...')
        self.le_log_search.setMaximumWidth(200)
        self.le_log_search.textChanged.connect(self._filter_logs)
        
        # Display options checkboxes
        self.chk_show_time = QtWidgets.QCheckBox('Time')
        self.chk_show_time.setObjectName('chk_show_time')
        self.chk_show_time.setChecked(True)
        self.chk_show_time.stateChanged.connect(self._on_display_options_changed)
        
        self.chk_show_source = QtWidgets.QCheckBox('Source')
        self.chk_show_source.setObjectName('chk_show_source')
        self.chk_show_source.setChecked(True)
        self.chk_show_source.stateChanged.connect(self._on_display_options_changed)
        
        # Clear button
        self.btn_clear_log = QtWidgets.QPushButton('Clear')
        self.btn_clear_log.setObjectName('btn_clear_log')
        self.btn_clear_log.setMaximumWidth(80)
        self.btn_clear_log.clicked.connect(self._clear_current_log)
        
        # Save button
        self.btn_save_log = QtWidgets.QPushButton('Save')
        self.btn_save_log.setObjectName('btn_save_log')
        self.btn_save_log.setMaximumWidth(80)
        self.btn_save_log.clicked.connect(self._save_logs)
        
        log_toolbar.addWidget(QtWidgets.QLabel('Search:'))
        log_toolbar.addWidget(self.le_log_search)
        log_toolbar.addWidget(QtWidgets.QLabel('Show:'))
        log_toolbar.addWidget(self.chk_show_time)
        log_toolbar.addWidget(self.chk_show_source)
        log_toolbar.addStretch()
        log_toolbar.addWidget(self.btn_clear_log)
        log_toolbar.addWidget(self.btn_save_log)
        
        logs_layout.addLayout(log_toolbar)
        
        self.tab_logs = QtWidgets.QTabWidget(); self.tab_logs.setObjectName('tab_logs')

        # main log widgets - for Tab 1 (1+2 side-by-side)
        self.txt_log_cpu1_tab1 = QtWidgets.QTextEdit(); self.txt_log_cpu1_tab1.setObjectName('console_log_cpu1_tab1')
        self.txt_log_cpu2_tab1 = QtWidgets.QTextEdit(); self.txt_log_cpu2_tab1.setObjectName('console_log_cpu2_tab1')
        
        # log widgets for individual tabs (Tab 2 and Tab 3)
        self.txt_log_cpu1 = QtWidgets.QTextEdit(); self.txt_log_cpu1.setObjectName('console_log_cpu1')
        self.txt_log_cpu2 = QtWidgets.QTextEdit(); self.txt_log_cpu2.setObjectName('console_log_cpu2')
        
        # legacy all logs widget
        self.txt_log_all = QtWidgets.QTextEdit(); self.txt_log_all.setObjectName('console_log_main')
        
        # Set monospace font for all log widgets
        monospace_font = QtGui.QFont()
        monospace_font.setFamily("Courier New")
        monospace_font.setPointSize(9)
        monospace_font.setStyleStrategy(QtGui.QFont.PreferAntialias)
        
        for t in (self.txt_log_cpu1_tab1, self.txt_log_cpu2_tab1, self.txt_log_cpu1, self.txt_log_cpu2, self.txt_log_all):
            t.setReadOnly(True)
            t.setFont(monospace_font)

        # Tab 1: CPU1 and CPU2 side-by-side
        tab1_widget = QtWidgets.QWidget()
        tab1_layout = QtWidgets.QHBoxLayout(tab1_widget)
        tab1_layout.setSpacing(5)
        tab1_layout.setContentsMargins(5, 5, 5, 5)
        tab1_layout.addWidget(self.txt_log_cpu1_tab1, 1)
        tab1_layout.addWidget(self.txt_log_cpu2_tab1, 1)

        # Tab 2: CPU1 only
        # Tab 3: CPU2 only
        
        self.tab_logs.addTab(tab1_widget, '1+2')
        self.tab_logs.addTab(self.txt_log_cpu1, 'CPU1')
        self.tab_logs.addTab(self.txt_log_cpu2, 'CPU2')

        logs_layout.addWidget(self.tab_logs)

        # RIGHT: status / aux panel
        right_panel = QtWidgets.QWidget()
        right_panel.setObjectName('right_panel')
        right_panel.setMinimumWidth(200)
        right_panel.setMaximumWidth(350)
        right_v = QtWidgets.QVBoxLayout(right_panel)
        right_v.setSpacing(8)
        right_v.setContentsMargins(5, 5, 5, 5)

        # top: device status group
        status_grp = QtWidgets.QGroupBox('Device Status')
        status_grp.setObjectName('grp_status')
        status_grp.setMinimumHeight(60)
        st_layout = QtWidgets.QVBoxLayout()
        st_layout.setSpacing(5)
        st_layout.setContentsMargins(5, 5, 5, 5)
        self.lbl_overall = QtWidgets.QLabel('System: OK'); self.lbl_overall.setObjectName('lbl_overall')
        self.lbl_overall.setMinimumHeight(24)
        st_layout.addWidget(self.lbl_overall)
        status_grp.setLayout(st_layout)
        right_v.addWidget(status_grp, 0)

        # per-port counters and LED indicators
        counters_grp = QtWidgets.QGroupBox(tr('port_counters', 'Port Counters'))
        counters_grp.setObjectName('grp_counters')
        counters_grp.setMinimumHeight(140)
        cnt_layout = QtWidgets.QGridLayout()
        cnt_layout.setSpacing(8)
        cnt_layout.setContentsMargins(8, 8, 8, 8)

        # CPU1 indicators
        lbl1 = QtWidgets.QLabel('CPU1:')
        lbl1.setMinimumHeight(24)
        self.led_cpu1_rx = QtWidgets.QFrame(); self.led_cpu1_rx.setObjectName('led_cpu1_rx')
        self.led_cpu1_rx.setFixedSize(14,14)
        self.led_cpu1_tx = QtWidgets.QFrame(); self.led_cpu1_tx.setObjectName('led_cpu1_tx')
        self.led_cpu1_tx.setFixedSize(14,14)
        self.lbl_cpu1_rx_count = QtWidgets.QLabel('RX: 0'); self.lbl_cpu1_rx_count.setObjectName('lbl_cpu1_rx_count')
        self.lbl_cpu1_rx_count.setMinimumHeight(20)
        self.lbl_cpu1_tx_count = QtWidgets.QLabel('TX: 0'); self.lbl_cpu1_tx_count.setObjectName('lbl_cpu1_tx_count')
        self.lbl_cpu1_tx_count.setMinimumHeight(20)
        cnt_layout.addWidget(lbl1, 0, 0)
        cnt_layout.addWidget(self.led_cpu1_rx, 0, 1)
        cnt_layout.addWidget(self.led_cpu1_tx, 0, 2)
        cnt_layout.addWidget(self.lbl_cpu1_rx_count, 0, 3)
        cnt_layout.addWidget(self.lbl_cpu1_tx_count, 0, 4)

        # CPU2 indicators
        lbl2 = QtWidgets.QLabel('CPU2:')
        lbl2.setMinimumHeight(24)
        self.led_cpu2_rx = QtWidgets.QFrame(); self.led_cpu2_rx.setObjectName('led_cpu2_rx')
        self.led_cpu2_rx.setFixedSize(14,14)
        self.led_cpu2_tx = QtWidgets.QFrame(); self.led_cpu2_tx.setObjectName('led_cpu2_tx')
        self.led_cpu2_tx.setFixedSize(14,14)
        self.lbl_cpu2_rx_count = QtWidgets.QLabel('RX: 0'); self.lbl_cpu2_rx_count.setObjectName('lbl_cpu2_rx_count')
        self.lbl_cpu2_rx_count.setMinimumHeight(20)
        self.lbl_cpu2_tx_count = QtWidgets.QLabel('TX: 0'); self.lbl_cpu2_tx_count.setObjectName('lbl_cpu2_tx_count')
        self.lbl_cpu2_tx_count.setMinimumHeight(20)
        cnt_layout.addWidget(lbl2, 1, 0)
        cnt_layout.addWidget(self.led_cpu2_rx, 1, 1)
        cnt_layout.addWidget(self.led_cpu2_tx, 1, 2)
        cnt_layout.addWidget(self.lbl_cpu2_rx_count, 1, 3)
        cnt_layout.addWidget(self.lbl_cpu2_tx_count, 1, 4)

        # AUX indicators
        lbl3 = QtWidgets.QLabel('AUX:')
        lbl3.setMinimumHeight(24)
        self.led_cpu3_rx = QtWidgets.QFrame(); self.led_cpu3_rx.setObjectName('led_cpu3_rx')
        self.led_cpu3_rx.setFixedSize(14,14)
        self.led_cpu3_tx = QtWidgets.QFrame(); self.led_cpu3_tx.setObjectName('led_cpu3_tx')
        self.led_cpu3_tx.setFixedSize(14,14)
        self.lbl_cpu3_rx_count = QtWidgets.QLabel('RX: 0'); self.lbl_cpu3_rx_count.setObjectName('lbl_cpu3_rx_count')
        self.lbl_cpu3_rx_count.setMinimumHeight(20)
        self.lbl_cpu3_tx_count = QtWidgets.QLabel('TX: 0'); self.lbl_cpu3_tx_count.setObjectName('lbl_cpu3_tx_count')
        self.lbl_cpu3_tx_count.setMinimumHeight(20)
        cnt_layout.addWidget(lbl3, 2, 0)
        cnt_layout.addWidget(self.led_cpu3_rx, 2, 1)
        cnt_layout.addWidget(self.led_cpu3_tx, 2, 2)
        cnt_layout.addWidget(self.lbl_cpu3_rx_count, 2, 3)
        cnt_layout.addWidget(self.lbl_cpu3_tx_count, 2, 4)

        counters_grp.setLayout(cnt_layout)
        right_v.addWidget(counters_grp, 0)

        # aux log in right panel
        aux_grp = QtWidgets.QGroupBox('Aux Log')
        aux_grp.setObjectName('grp_aux_log')
        aux_grp.setMinimumHeight(100)
        aux_layout = QtWidgets.QVBoxLayout()
        aux_layout.setSpacing(5)
        aux_layout.setContentsMargins(5, 5, 5, 5)
        self.txt_log_aux = QtWidgets.QTextEdit(); self.txt_log_aux.setObjectName('console_log_aux')
        self.txt_log_aux.setReadOnly(True)
        self.txt_log_aux.setFont(monospace_font)  # Use same monospace font
        aux_layout.addWidget(self.txt_log_aux)
        aux_grp.setLayout(aux_layout)
        right_v.addWidget(aux_grp, 1)

        right_v.addStretch()

        # assemble splitter with proper stretch factors
        hsplit.addWidget(layout_left)
        hsplit.addWidget(logs_widget)
        hsplit.addWidget(right_panel)
        hsplit.setStretchFactor(0, 0)
        hsplit.setStretchFactor(1, 1)
        hsplit.setStretchFactor(2, 0)

        left_container = QtWidgets.QVBoxLayout()
        left_container.addWidget(hsplit)
        tab1.setLayout(left_container)

        # Tab 2: Aux Device (port 3)
        tab2 = QtWidgets.QWidget()
        tab2.setObjectName('tab_aux_device')
        tabs.addTab(tab2, 'Aux Device')
        t2_layout = QtWidgets.QVBoxLayout(tab2)

        grp3 = QtWidgets.QGroupBox('Aux Device')
        grp3.setObjectName('grp_aux')
        g3 = QtWidgets.QFormLayout()
        self.cb_port_3 = QtWidgets.QComboBox(); self.cb_port_3.setObjectName('cb_port_3')
        self.cb_baud_3 = QtWidgets.QComboBox(); self.cb_baud_3.setObjectName('cb_baud_3')
        self.cb_baud_3.addItems(['9600','19200','38400','57600','115200'])
        self.btn_connect_3 = QtWidgets.QPushButton('Connect'); self.btn_connect_3.setObjectName('btn_connect_3')
        self.lbl_status_3 = QtWidgets.QLabel('Disconnected'); self.lbl_status_3.setObjectName('lbl_status_3')
        g3.addRow('Port:', self.cb_port_3)
        g3.addRow('Baud:', self.cb_baud_3)
        g3.addRow(self.btn_connect_3)
        g3.addRow('Status:', self.lbl_status_3)
        grp3.setLayout(g3)

        t2_layout.addWidget(grp3)

        # Aux logs
        self.txt_log_aux = QtWidgets.QTextEdit(); self.txt_log_aux.setObjectName('console_log_aux')
        self.txt_log_aux.setReadOnly(True)
        self.txt_log_aux.setFont(monospace_font)  # Use same monospace font
        t2_layout.addWidget(self.txt_log_aux)

        # Populate port combo boxes with placeholder values
        common_ports = ['COM1','COM2','COM3','COM4','COM5']
        self.cb_port_1.addItems(common_ports)
        self.cb_port_2.addItems(common_ports)
        self.cb_port_3.addItems(common_ports)

        # populate ports at startup
        try:
            self.scan_ports(0)
        except Exception:
            pass

        # Connect signals for port management
        self.btn_scan_1.clicked.connect(lambda: self.scan_ports(1))
        self.btn_scan_2.clicked.connect(lambda: self.scan_ports(2))
        self.btn_connect_1.clicked.connect(self._toggle_conn_1)
        self.btn_connect_2.clicked.connect(self._toggle_conn_2)

        # Manual send buttons
        self.btn_send_cpu1.clicked.connect(lambda: self._send_to(1))
        self.btn_send_cpu2.clicked.connect(lambda: self._send_to(2))
        self.btn_send_both.clicked.connect(lambda: self._send_to(0))

        # initial language apply
        self._update_texts()

    # ---------- connection handling ----------
    

    def _toggle_conn_3(self):
        if not self.worker3 or not self.worker3.isRunning():
            self.worker3 = SerialWorker('AUX')
            port = self.cb_port_3.currentText()
            baud = int(self.cb_baud_3.currentText())
            self.worker3.configure(port, baud)
            self.worker3.rx.connect(self._on_rx_aux)
            self.worker3.status.connect(self._on_status)
            self.worker3.error.connect(self._on_error)
            self.worker3.start()
            self.btn_connect_3.setText('Disconnect')
        else:
            self.worker3.stop()
            self.btn_connect_3.setText('Connect')

    # ---------- logging and handlers ----------
    def _on_rx(self, port_label, data):
        html = self._fmt_rx(port_label, data)
        if not html:  # Skip empty logs
            return
        self._append_log(self.txt_log_all, html)
        if port_label == 'CPU1':
            self._append_log(self.txt_log_cpu1_tab1, html)
            self._append_log(self.txt_log_cpu1, html)
            self._inc_rx(1)
            self._flash_led(1, 'rx')
        elif port_label == 'CPU2':
            self._append_log(self.txt_log_cpu2_tab1, html)
            self._append_log(self.txt_log_cpu2, html)
            self._inc_rx(2)
            self._flash_led(2, 'rx')

    def _on_rx_aux(self, port_label, data):
        html = self._fmt_rx(port_label, data)
        if not html:
            return
        self._append_log(self.txt_log_aux, html)
        self._append_log(self.txt_log_all, html)

    def _on_status(self, port_label, message):
        html = self._fmt_system(port_label, message)
        # Append system status to logs. UI views update themselves via VM signals.
        self._append_log(self.txt_log_all, html)

    # ---------- connection handling for CPU1/CPU2 ----------
    def _toggle_conn_1(self):
        if not self.worker1 or not self.worker1.isRunning():
            self.worker1 = SerialWorker('CPU1')
            port = self.cb_port_1.currentText()
            baud = int(self.cb_baud_1.currentText())
            self.worker1.configure(port, baud)
            self.worker1.rx.connect(self._on_rx)
            self.worker1.status.connect(self._on_status)
            self.worker1.error.connect(self._on_error)
            self.worker1.start()
            self.btn_connect_1.setText('Disconnect')
        else:
            self.worker1.stop()
            self.btn_connect_1.setText('Connect')

    def _toggle_conn_2(self):
        if not self.worker2 or not self.worker2.isRunning():
            self.worker2 = SerialWorker('CPU2')
            port = self.cb_port_2.currentText()
            baud = int(self.cb_baud_2.currentText())
            self.worker2.configure(port, baud)
            self.worker2.rx.connect(self._on_rx)
            self.worker2.status.connect(self._on_status)
            self.worker2.error.connect(self._on_error)
            self.worker2.start()
            self.btn_connect_2.setText('Disconnect')
        else:
            self.worker2.stop()
            self.btn_connect_2.setText('Connect')

    def _on_theme_changed(self, theme):
        # theme_manager already applies palettes globally; update labels if needed
        try:
            self.lbl_overall.setText(tr('theme', 'Theme') + f": {theme}")
        except Exception:
            pass

    def _on_language_changed(self, language):
        self._update_texts()

    def _update_texts(self):
        # Window and tab titles
        try:
            self.setWindowTitle(tr('app_name', 'UART Controller'))
        except Exception:
            pass
        try:
            self.tab_logs.setTabText(0, tr('send_to_both', '1+2'))
            self.tab_logs.setTabText(1, tr('send_to_cpu1', 'CPU1'))
            self.tab_logs.setTabText(2, tr('send_to_cpu2', 'CPU2'))
        except Exception:
            pass

        # Group titles
        g = self.findChild(QtWidgets.QGroupBox, 'grp_cpu1')
        if g:
            g.setTitle(tr('port_settings', 'Port Settings'))
        g = self.findChild(QtWidgets.QGroupBox, 'grp_cpu2')
        if g:
            g.setTitle(tr('port_settings', 'Port Settings'))
        g = self.findChild(QtWidgets.QGroupBox, 'grp_aux')
        if g:
            g.setTitle(tr('port_settings', 'Port Settings'))
        g = self.findChild(QtWidgets.QGroupBox, 'grp_input')
        if g:
            g.setTitle(tr('data_transmission', 'Data Transmission'))
        g = self.findChild(QtWidgets.QGroupBox, 'grp_status')
        if g:
            g.setTitle(tr('status', 'Status'))

        # Buttons
        try:
            # update VM-backed views' connect button text if present
            vb1 = getattr(self, 'view_cpu1', None)
            vb2 = getattr(self, 'view_cpu2', None)
            if vb1 and hasattr(vb1, 'connect_btn'):
                vb1.connect_btn.setText(tr('open_port', 'Connect'))
            if vb2 and hasattr(vb2, 'connect_btn'):
                vb2.connect_btn.setText(tr('open_port', 'Connect'))
            self.btn_connect_3.setText(tr('open_port', 'Connect'))
        except Exception:
            pass
        try:
            self.btn_send_cpu1.setText(tr('send_to_cpu1', 'CPU1'))
            self.btn_send_cpu2.setText(tr('send_to_cpu2', 'CPU2'))
            self.btn_send_both.setText(tr('send_to_both', '1+2'))
        except Exception:
            pass

    def _on_error(self, port_label, message):
        html = self._fmt_system(port_label, message)
        self._append_log(self.txt_log_all, html)

    def _send_to(self, which:int):
        """which: 1->CPU1, 2->CPU2, 0->both"""
        text = self.le_command.text()
        if not text:
            return
        # TX log
        if which == 1 and self.worker1:
            self.worker1.write(text)
            self._append_log(self.txt_log_all, self._fmt_tx('CPU1', text))
            self._append_log(self.txt_log_cpu1_tab1, self._fmt_tx('CPU1', text))
            self._append_log(self.txt_log_cpu1, self._fmt_tx('CPU1', text))
            self._inc_tx(1)
            self._flash_led(1, 'tx')
        elif which == 2 and self.worker2:
            self.worker2.write(text)
            self._append_log(self.txt_log_all, self._fmt_tx('CPU2', text))
            self._append_log(self.txt_log_cpu2_tab1, self._fmt_tx('CPU2', text))
            self._append_log(self.txt_log_cpu2, self._fmt_tx('CPU2', text))
            self._inc_tx(2)
            self._flash_led(2, 'tx')
        elif which == 0:
            if self.worker1:
                self.worker1.write(text)
                self._append_log(self.txt_log_cpu1_tab1, self._fmt_tx('CPU1', text))
                self._append_log(self.txt_log_cpu1, self._fmt_tx('CPU1', text))
                self._inc_tx(1)
                self._flash_led(1, 'tx')
            if self.worker2:
                self.worker2.write(text)
                self._append_log(self.txt_log_cpu2_tab1, self._fmt_tx('CPU2', text))
                self._append_log(self.txt_log_cpu2, self._fmt_tx('CPU2', text))
                self._inc_tx(2)
                self._flash_led(2, 'tx')
            self._append_log(self.txt_log_all, self._fmt_tx('BOTH', text))

        # clear input
        self.le_command.clear()

    # ---------- counter and LED helpers ----------
    def _inc_tx(self, idx:int):
        i = idx - 1
        self.tx_counts[i] += 1
        lbl = getattr(self, f'lbl_cpu{idx}_tx_count', None)
        if lbl:
            lbl.setText(f'TX: {self.tx_counts[i]}')

    def _inc_rx(self, idx:int):
        i = idx - 1
        self.rx_counts[i] += 1
        lbl = getattr(self, f'lbl_cpu{idx}_rx_count', None)
        if lbl:
            lbl.setText(f'RX: {self.rx_counts[i]}')

    def _flash_led(self, idx:int, kind:str):
        # kind: 'rx' or 'tx'
        led = getattr(self, f'led_cpu{idx}_{kind}', None)
        if not led:
            return
        # set active style (assumes QSS will style .active)
        prev = led.styleSheet()
        if kind == 'rx':
            led.setStyleSheet('background: #4caf50; border-radius: 7px;')
        else:
            led.setStyleSheet('background: #ffcc33; border-radius: 7px;')
        QtCore.QTimer.singleShot(150, lambda: led.setStyleSheet(prev))

    def _append_log(self, widget, html_text):
        """Append HTML text to a log widget and update cache."""
        if not html_text or not html_text.strip():  # Skip empty logs
            return
            
        # Move cursor to end and insert HTML without extra line breaks
        cursor = widget.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        widget.setTextCursor(cursor)
        widget.insertHtml(html_text)
        
        # Update cache for filtering - store both HTML and plain text
        plain_text = self._strip_html(html_text)
        cache_key = self._get_cache_key(widget)
        if cache_key:
            if cache_key not in self.log_cache:
                self.log_cache[cache_key] = {'html': [], 'plain': []}
            # Store each line as separate item for easier filtering
            self.log_cache[cache_key]['html'].append(html_text)
            self.log_cache[cache_key]['plain'].append(plain_text)
    
    def _get_cache_key(self, widget):
        """Get cache key for a given widget."""
        if widget == self.txt_log_cpu1_tab1:
            return 'cpu1_tab1'
        elif widget == self.txt_log_cpu2_tab1:
            return 'cpu2_tab1'
        elif widget == self.txt_log_cpu1:
            return 'cpu1'
        elif widget == self.txt_log_cpu2:
            return 'cpu2'
        elif widget == self.txt_log_all:
            return 'all'
        return None
    
    @staticmethod
    def _strip_html(html_text):
        """Remove HTML tags from text for plain text filtering."""
        import re
        clean = re.compile('<.*?>')
        clean_text = re.sub(clean, '', html_text)
        # Also decode HTML entities
        return clean_text.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')

    # ---------- formatting helpers ----------
    def _fmt_rx(self, src, text):
        """Format RX message. Each complete line gets its own timestamp and source."""
        if not text or not text.strip():
            return ""
            
        ts = QtCore.QDateTime.currentDateTime().toString('hh:mm:ss')
        time_part = f"<span style='color:gray'>[{ts}]</span> " if self.show_time else ""
        source_part = f"<b style='color:green'>RX({src}):</b> " if self.show_source else ""
        
        # Remove trailing line endings
        text = text.rstrip('\r\n')
        
        escaped_text = escape(text)
        return f"{time_part}{source_part}<span style='color:#c7f0c7; white-space:pre'>{escaped_text}</span><br>"

    def _fmt_tx(self, src, text):
        """Format TX message. Each complete line gets its own timestamp and source."""
        if not text or not text.strip():
            return ""
            
        ts = QtCore.QDateTime.currentDateTime().toString('hh:mm:ss')
        time_part = f"<span style='color:gray'>[{ts}]</span> " if self.show_time else ""
        source_part = f"<b style='color:#ffdd57'>TX({src}):</b> " if self.show_source else ""
        
        text = text.rstrip('\r\n')
        
        escaped_text = escape(text)
        return f"{time_part}{source_part}<span style='color:#fff7d6; white-space:pre'>{escaped_text}</span><br>"

    def _fmt_system(self, src, text):
        """Format system message. Each complete line gets its own timestamp and source."""
        if not text or not text.strip():
            return ""
            
        ts = QtCore.QDateTime.currentDateTime().toString('hh:mm:ss')
        time_part = f"<span style='color:gray'>[{ts}]</span> " if self.show_time else ""
        source_part = f"<b style='color:lightgray'>SYS({src}):</b> " if self.show_source else ""
        
        text = text.rstrip('\r\n')
        
        escaped_text = escape(text)
        return f"{time_part}{source_part}<span style='color:lightgray; white-space:pre'>{escaped_text}</span><br>"

    def scan_ports(self, which:int=0):
        """Scan available serial ports and populate the requested combo box.
        which: 1->cb_port_1, 2->cb_port_2, 3->cb_port_3, 0->all
        """
        ports = []
        if HAS_PYSERIAL:
            try:
                from serial.tools import list_ports
                ports = [p.device for p in list_ports.comports()]
            except Exception:
                ports = []
        if not ports:
            # fallback to common placeholders
            ports = ['COM1','COM2','COM3','COM4','COM5']

        if which in (0,1):
            self.cb_port_1.clear(); self.cb_port_1.addItems(ports)
        if which in (0,2):
            self.cb_port_2.clear(); self.cb_port_2.addItems(ports)
        if which in (0,3):
            self.cb_port_3.clear(); self.cb_port_3.addItems(ports)

    def _on_display_options_changed(self):
        """Handle changes to display options (time/source visibility)."""
        self.show_time = self.chk_show_time.isChecked()
        self.show_source = self.chk_show_source.isChecked()
        
        # Rebuild all logs by re-rendering cached content
        # For each widget, clear and rebuild from cache
        for cache_key, cache_data in list(self.log_cache.items()):
            if isinstance(cache_data, dict) and 'html' in cache_data:
                widget = self._get_widget_by_cache_key(cache_key)
                if widget:
                    # Reconstruct and display
                    content = ''.join(cache_data['html'])
                    widget.blockSignals(True)
                    widget.clear()
                    cursor = widget.textCursor()
                    cursor.movePosition(cursor.MoveOperation.Start)
                    widget.setTextCursor(cursor)
                    widget.insertHtml(content)
                    widget.blockSignals(False)

    def _get_widget_by_cache_key(self, cache_key):
        """Get widget for a given cache key."""
        if cache_key == 'cpu1_tab1':
            return self.txt_log_cpu1_tab1
        elif cache_key == 'cpu2_tab1':
            return self.txt_log_cpu2_tab1
        elif cache_key == 'cpu1':
            return self.txt_log_cpu1
        elif cache_key == 'cpu2':
            return self.txt_log_cpu2
        elif cache_key == 'all':
            return self.txt_log_all
        return None

    # ---------- Logging toolbar methods ----------
    def _clear_current_log(self):
        """Clear all logs everywhere."""
        # Clear all text widgets
        self.txt_log_cpu1_tab1.clear()
        self.txt_log_cpu2_tab1.clear()
        self.txt_log_cpu1.clear()
        self.txt_log_cpu2.clear()
        self.txt_log_all.clear()
        
        # Clear all cache
        self.log_cache.clear()
        
        # Clear search field
        self.le_log_search.blockSignals(True)
        self.le_log_search.clear()
        self.le_log_search.blockSignals(False)

    def _save_logs(self):
        """Save logs from current tab to file."""
        import datetime
        idx = self.tab_logs.currentIndex()
        
        # Determine which text widget and filename
        if idx == 0:  # 1+2 tab - save both
            text1 = self.txt_log_cpu1_tab1.toPlainText()
            text2 = self.txt_log_cpu2_tab1.toPlainText()
            text = f"=== CPU1 ===\n{text1}\n\n=== CPU2 ===\n{text2}"
            default_name = f"logs_1+2_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        elif idx == 1:  # CPU1 tab
            text = self.txt_log_cpu1.toPlainText()
            default_name = f"logs_CPU1_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        elif idx == 2:  # CPU2 tab
            text = self.txt_log_cpu2.toPlainText()
            default_name = f"logs_CPU2_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        else:
            return
        
        # Save dialog
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save Logs", default_name, "Text Files (*.txt);;All Files (*.*)"
        )
        if path:
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(text)
                QtWidgets.QMessageBox.information(self, "Success", f"Logs saved to:\n{path}")
            except Exception as e:
                QtWidgets.QMessageBox.warning(self, "Error", f"Failed to save logs:\n{str(e)}")

    def _filter_logs(self, search_text):
        """Filter logs based on search text, preserving HTML formatting."""
        idx = self.tab_logs.currentIndex()
        
        # Get the appropriate text widget(s) and cache key(s)
        if idx == 0:  # 1+2 tab
            widgets = [(self.txt_log_cpu1_tab1, 'cpu1_tab1'), (self.txt_log_cpu2_tab1, 'cpu2_tab1')]
        elif idx == 1:  # CPU1 tab
            widgets = [(self.txt_log_cpu1, 'cpu1')]
        elif idx == 2:  # CPU2 tab
            widgets = [(self.txt_log_cpu2, 'cpu2')]
        else:
            return
        
        for widget, cache_key in widgets:
            # Initialize cache if not present
            if cache_key not in self.log_cache or 'html' not in self.log_cache[cache_key]:
                self.log_cache[cache_key] = {'html': [], 'plain': []}
            
            html_lines = self.log_cache[cache_key]['html']
            plain_lines = self.log_cache[cache_key]['plain']
            
            # Filter lines
            if search_text.strip():
                search_lower = search_text.lower()
                filtered_html = [html for html, plain in zip(html_lines, plain_lines) 
                               if search_lower in plain.lower()]
            else:
                filtered_html = html_lines
            
            # Reconstruct HTML and update widget
            filtered_content = ''.join(filtered_html)
            
            widget.blockSignals(True)
            widget.clear()
            cursor = widget.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            widget.setTextCursor(cursor)
            widget.insertHtml(filtered_content)
            widget.blockSignals(False)


def run_app():
    try:
        app = QtWidgets.QApplication(sys.argv)
        # try to apply QSS from project if exists
        try:
            import os
            qss_path = os.path.join(os.path.dirname(__file__), '..', 'styles', 'app.qss')
            qss_path = os.path.abspath(qss_path)
            if os.path.exists(qss_path):
                with open(qss_path, 'r', encoding='utf-8') as f:
                    app.setStyleSheet(f.read())
        except Exception:
            pass

        w = MainWindow()
        w.show()
        return app.exec()
    except Exception as e:
        tb = traceback.format_exc()
        print('Unhandled exception in GUI startup:')
        print(tb)
        try:
            QtWidgets.QMessageBox.critical(None, 'Startup Error', f'Exception:\n{tb}')
        except Exception:
            pass
        return 1


if __name__ == '__main__':
    run_app()
