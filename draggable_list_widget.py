# pinpoint/draggable_list_widget.py

from PySide6.QtWidgets import QListWidget
from PySide6.QtCore import Qt, QMimeData
from PySide6.QtGui import QDrag

# This is our custom MIME type to ensure we're dropping our own tiles
TILE_ID_MIME_TYPE = "application/x-pinpoint-tile-id"

class DraggableListWidget(QListWidget):
    """A QListWidget that starts a drag with custom MIME data."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        # We only want to drag from this list, not drop onto it
        self.setAcceptDrops(False)
        self.setFlow(QListWidget.Flow.TopToBottom) # Default vertical list

    def startDrag(self, supportedActions):
        """Overrides the default drag behavior to insert our custom data."""
        item = self.currentItem()
        if not item:
            return

        tile_id = item.data(Qt.ItemDataRole.UserRole)
        if not tile_id:
            return
        
        # Create MIME data to hold our tile ID
        mime_data = QMimeData()
        # We encode the string ID into bytes to store it
        mime_data.setData(TILE_ID_MIME_TYPE, tile_id.encode())

        drag = QDrag(self)
        drag.setMimeData(mime_data)
        
        # This starts the drag operation
        drag.exec(Qt.DropAction.CopyAction)