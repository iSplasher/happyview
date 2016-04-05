from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import (QBrush, QColor)
from PyQt5.QtWidgets import (QWidget, QToolBar)

class BaseControl(QToolBar):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.setIconSize(QSize(50, 50))
		self.setAutoFillBackground(True)

	@property
	def halfWidth(self):
		return self.width()//2

	@property
	def halfHeight(self):
		return self.height()//2

# Main Controls

class FromFile(BaseControl):
	"Load images from file"
	
	def __init__(self, parent=None):
		super().__init__(parent)

class FromFolder(BaseControl):
	"Load images from folder"

	def __init__(self, parent=None):
		super().__init__(parent)

class ViewMode(BaseControl):
	"View single image or 2 images like a book"
	
	def __init__(self, parent=None):
		super().__init__(parent)

class ImageDirection(BaseControl):
	"LeftToRight or RightToLeft"
	
	def __init__(self, parent=None):
		super().__init__(parent)

class PlayDiasshow(BaseControl):
	"Start diasshow"
	
	def __init__(self, parent=None):
		super().__init__(parent)

class MainControls(BaseControl):
	"Main controls for things like loading images, "
	
	def __init__(self, scene, parent=None):
		super().__init__(parent)
		self.setOrientation(Qt.Horizontal)
		self._scene = scene
		self._fromFile = self.addAction("From File")
		self._fromFolder = self.addAction("From Folder")

# ImageControls

class ZoomIn(BaseControl):
	"Zoom in"
	pass

class ZoomOut(BaseControl):
	"Zoom out"
	pass

class RotateClockwise(BaseControl):
	"Rotate image clockwise"
	pass

class RotateCounterClockwise(BaseControl):
	"Rotate image counter clockwise"
	pass

class ImageControls(QToolBar):
	"Image controls"

	def __init__(self, scene, parent=None):
		super().__init__(parent)
		self._mainLayout = QGraphicsLinearLayout(Qt.Horizontal, self)

# NavControls


class Forward(BaseControl):
	"Go to next image"
	pass

class Backward(BaseControl):
	"Go to previous image"
	pass

class NavControls(QToolBar):
	"Navigation controls"

	def __init__(self, scene, parent=None):
		super().__init__(parent)
		self._mainLayout = QGraphicsLinearLayout(Qt.Horizontal, self)

