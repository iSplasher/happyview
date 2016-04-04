from PyQt5.QtCore import Qt
from PyQt5.QtGui import (QBrush, QColor)
from PyQt5.QtWidgets import QGraphicsWidget, QGraphicsLinearLayout

# Main Controls

class FromFile(QGraphicsWidget):
	"Load images from file"
	pass

class FromFolder(QGraphicsWidget):
	"Load images from folder"
	pass

class ViewMode(QGraphicsWidget):
	"View single image or 2 images like a book"
	pass

class ImageDirection(QGraphicsWidget):
	"LeftToRight or RightToLeft"
	pass

class PlayDiasshow(QGraphicsWidget):
	"Start diasshow"
	pass

class MainControls(QGraphicsWidget):
	"Main controls for things like loading images, "
	
	def __init__(self, parent=None):
		super().__init__(parent)
		self._mainLayout = QGraphicsLinearLayout(Qt.Vertical, self)

# ImageControls

class ZoomIn(QGraphicsWidget):
	"Zoom in"
	pass

class ZoomOut(QGraphicsWidget):
	"Zoom out"
	pass

class RotateClockwise(QGraphicsWidget):
	"Rotate image clockwise"
	pass

class RotateCounterClockwise(QGraphicsWidget):
	"Rotate image counter clockwise"
	pass

class ImageControls:
	"Image controls"

	def __init__(self, parent=None):
		super().__init__(parent)
		self._mainLayout = QGraphicsLinearLayout(Qt.Horizontal, self)

# NavControls


class Forward(QGraphicsWidget):
	"Go to next image"
	pass

class Backward(QGraphicsWidget):
	"Go to previous image"
	pass

class NavControls:
	"Navigation controls"

	def __init__(self, parent=None):
		super().__init__(parent)
		self._mainLayout = QGraphicsLinearLayout(Qt.Horizontal, self)

