"""
Toast notification widget for non-blocking user feedback.
Provides temporary notifications that auto-dismiss.

Features:
- Multiple toast types: info, warning, error, success
- Auto-positioning in bottom-right of parent window
- Theme-aware styling (light/dark)
- Auto-dismiss with configurable timeout
"""

from PySide6 import QtWidgets, QtCore, QtGui
from typing import Optional
import logging

from src.styles.constants import ToastConfig

logger = logging.getLogger(__name__)


class ToastNotification(QtWidgets.QFrame):
    """
    Non-blocking toast notification widget.
    Appears at the bottom-right of the parent window and auto-dismisses.
    """
    
    # Toast types
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    
    def __init__(
        self,
        message: str,
        toast_type: str = INFO,
        duration_ms: int = ToastConfig.TOAST_DURATION_MS,
        parent: Optional[QtWidgets.QWidget] = None
    ):
        super().__init__(parent)
        self._message = message
        self._toast_type = toast_type
        self._duration_ms = duration_ms
        
        self._setup_ui()
        self._apply_style()
        
    def _setup_ui(self) -> None:
        """Create and layout the toast UI."""
        self.setFixedWidth(300)  # Compact width
        self.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        
        # Use Popup window type for proper positioning
        self.setWindowFlags(
            QtCore.Qt.WindowType.Popup |
            QtCore.Qt.WindowType.FramelessWindowHint
        )
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        
        # Main layout
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(10)
        
        # Icon label
        self._icon_label = QtWidgets.QLabel()
        self._icon_label.setFixedSize(20, 20)
        self._icon_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self._icon_label)
        
        # Message label (compact - just the message)
        self._message_label = QtWidgets.QLabel(self._message)
        self._message_label.setObjectName("toast_message")
        self._message_label.setWordWrap(False)
        self._message_label.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Fixed
        )
        self._message_label.setMaximumWidth(200)
        layout.addWidget(self._message_label)
        
        # Close button (single)
        self._close_btn = QtWidgets.QPushButton("×")
        self._close_btn.setFixedSize(20, 20)
        self._close_btn.setObjectName("toast_close")
        self._close_btn.setCursor(QtCore.Qt.PointingHandCursor)
        self._close_btn.clicked.connect(self._close)
        self._close_btn.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        layout.addWidget(self._close_btn)
        
    def _apply_style(self) -> None:
        """Apply styling based on toast type and theme."""
        is_dark = False
        if self.window():
            try:
                from src.utils.theme_manager import theme_manager
                is_dark = theme_manager.is_dark_theme()
            except Exception:
                pass
        
        if self._toast_type == self.INFO:
            bg_color = "#2563eb" if is_dark else "#3b82f6"
            text_color = "#ffffff"
        elif self._toast_type == self.SUCCESS:
            bg_color = "#16a34a" if is_dark else "#22c55e"
            text_color = "#ffffff"
        elif self._toast_type == self.WARNING:
            bg_color = "#d97706" if is_dark else "#f59e0b"
            text_color = "#ffffff"
        elif self._toast_type == self.ERROR:
            bg_color = "#dc2626" if is_dark else "#ef4444"
            text_color = "#ffffff"
        else:
            bg_color = "#6b7280"
            text_color = "#ffffff"
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                color: {text_color};
                border-radius: 6px;
            }}
            #toast_message {{
                color: {text_color};
                font-size: 11px;
                font-weight: normal;
            }}
            #toast_close {{
                background: transparent;
                border: none;
                color: {text_color};
                font-size: 16px;
                font-weight: bold;
                padding: 0px;
            }}
            #toast_close:hover {{
                background: rgba(255, 255, 255, 0.2);
                border-radius: 4px;
            }}
        """)
        
        # Set icon based on type
        icon_map = {
            self.INFO: "ℹ",
            self.SUCCESS: "✓",
            self.WARNING: "⚠",
            self.ERROR: "✕"
        }
        self._icon_label.setText(icon_map.get(self._toast_type, "ℹ"))
        
    def showEvent(self, event: QtCore.QEvent) -> None:
        """Start auto-dismiss timer when shown."""
        super().showEvent(event)
        if self._duration_ms > 0:
            QtCore.QTimer.singleShot(self._duration_ms, self._close)
    
    def _close(self) -> None:
        """Close and delete the toast."""
        self.hide()
        self.deleteLater()
        # Notify manager to remove from list
        if hasattr(self, '_manager'):
            self._manager._on_toast_closed(self)
        


class ToastManager(QtCore.QObject):
    """
    Manager for toast notifications.
    Handles positioning in bottom-right of parent window.
    """
    
    def __init__(self, parent: QtWidgets.QWidget):
        super().__init__(parent)
        self._parent = parent
        self._toasts: list[ToastNotification] = []
        self._margin = 10
        self._spacing = 8
        
        # Install event filter to handle parent resize/move
        if parent:
            parent.installEventFilter(self)
        
    def show_toast(
        self,
        message: str,
        toast_type: str = ToastNotification.INFO,
        duration_ms: int = ToastConfig.TOAST_DURATION_MS
    ) -> ToastNotification:
        """Show a toast notification in bottom-right of parent window."""
        toast = ToastNotification(message, toast_type, duration_ms, self._parent)
        toast._manager = self  # Reference for cleanup
        self._toasts.append(toast)
        
        # First show to get geometry, then position
        toast.show()
        self._reposition_toasts()
        
        return toast
    
    def show_info(
        self,
        message: str,
        title: Optional[str] = None,
        duration_ms: int = ToastConfig.TOAST_DURATION_MS
    ) -> ToastNotification:
        """Show info toast."""
        return self.show_toast(message, ToastNotification.INFO, duration_ms)
    
    def show_success(
        self,
        message: str,
        title: Optional[str] = None,
        duration_ms: int = ToastConfig.TOAST_DURATION_MS
    ) -> ToastNotification:
        """Show success toast."""
        return self.show_toast(message, ToastNotification.SUCCESS, duration_ms)
    
    def show_warning(
        self,
        message: str,
        title: Optional[str] = None,
        duration_ms: int = ToastConfig.TOAST_DURATION_MS
    ) -> ToastNotification:
        """Show warning toast."""
        return self.show_toast(message, ToastNotification.WARNING, duration_ms)
    
    def show_error(
        self,
        message: str,
        title: Optional[str] = None,
        error_code: Optional[int] = None,
        duration_ms: int = 5000
    ) -> ToastNotification:
        """Show error toast."""
        display_msg = message
        if error_code is not None:
            display_msg = f"{message} (code: {error_code})"
        return self.show_toast(display_msg, ToastNotification.ERROR, duration_ms)
    
    def _reposition_toasts(self) -> None:
        """Position all toasts at bottom-right of parent window, staying inside bounds."""
        # Safely handle case where parent is None or destroyed
        try:
            if not self._parent or not self._parent.isVisible():
                return
        except RuntimeError:
            # Parent widget was destroyed
            self._toasts.clear()
            return
        
        # Filter out hidden/deleted toasts safely
        valid_toasts = []
        for toast in self._toasts:
            try:
                # Check if C++ object is still valid and visible
                if toast and toast.isVisible():
                    valid_toasts.append(toast)
            except RuntimeError:
                # Toast was deleted, skip it
                continue
        self._toasts = valid_toasts
        
        if not self._toasts:
            return
        
        try:
            # Get parent geometry in screen coordinates (global)
            parent_geo = self._parent.frameGeometry()
        except RuntimeError:
            # Parent was destroyed
            return
        
        # Parent bounds in global coordinates
        parent_right = parent_geo.right()
        parent_bottom = parent_geo.bottom()
        parent_left = parent_geo.left()
        parent_top = parent_geo.top()
        
        # Calculate position for each toast (stacked from bottom-right, going up)
        y_offset = self._margin
        for toast in reversed(self._toasts):
            try:
                # Use fixed toast dimensions
                toast_width = 300  # Fixed width set in ToastNotification
                toast_height = max(toast.sizeHint().height(), 32)  # Get actual height
                
                # Ensure minimum height
                if toast_height < 36:
                    toast_height = 36
                
                # Position: bottom-right corner of parent, inside bounds
                x = parent_right - toast_width - self._margin
                y = parent_bottom - toast_height - y_offset
                
                # Clamp to stay inside parent window
                x = max(parent_left + self._margin, min(x, parent_right - self._margin))
                y = max(parent_top + self._margin, min(y, parent_bottom - self._margin))
                
                toast.move(x, y)
                y_offset += toast_height + self._spacing
            except RuntimeError:
                # Toast was deleted, skip it
                continue
    
    def clear_all(self) -> None:
        """Clear all visible toasts."""
        for toast in self._toasts:
            try:
                if toast.isVisible():
                    toast.hide()
                    toast.deleteLater()
            except RuntimeError:
                # Toast was already deleted
                pass
        self._toasts.clear()

    def _on_toast_closed(self, toast: ToastNotification) -> None:
        """Handle toast closed event - remove from list safely."""
        try:
            if toast in self._toasts:
                self._toasts.remove(toast)
                self._reposition_toasts()
        except (RuntimeError, ValueError):
            # Toast was already deleted or not in list
            pass
    
    def eventFilter(self, obj: QtCore.QObject, event: QtCore.QEvent) -> bool:
        """Handle parent window resize/move events to reposition toasts."""
        if obj == self._parent:
            event_type = event.type()
            if event_type in (QtCore.QEvent.Type.Resize, QtCore.QEvent.Type.Move):
                # Reposition toasts when parent window changes
                self._reposition_toasts()
        return super().eventFilter(obj, event)


# Global toast manager instance
_toast_manager: Optional[ToastManager] = None


def get_toast_manager(parent: QtWidgets.QWidget) -> ToastManager:
    """Get or create the global toast manager."""
    global _toast_manager
    if _toast_manager is None:
        _toast_manager = ToastManager(parent)
    return _toast_manager


def reset_toast_manager() -> None:
    """Reset the global toast manager (useful for testing)."""
    global _toast_manager
    if _toast_manager:
        _toast_manager.clear_all()
        _toast_manager.deleteLater()
        _toast_manager = None
