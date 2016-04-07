from enum import Enum

from PyQt5.QtCore import Qt, QSize, QRect, QPoint, pyqtSignal, QObject
from PyQt5.QtGui import (QBrush, QColor, QPainter, QPen, QBrush,
						 QPolygon)
from PyQt5.QtWidgets import (QToolBar, QPushButton)

class Direction(Enum):
	Forward = 0
	Backward = 1

class BaseControl(QToolBar):
	def __init__(self, scene, parent=None):
		super().__init__(parent)
		self.setOrientation(Qt.Horizontal)
		self.setIconSize(QSize(50, 50))
		self.setAutoFillBackground(True)
		self._scene = scene

	@property
	def halfWidth(self):
		return self.width() // 2

	@property
	def halfHeight(self):
		return self.height() // 2

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
		super().__init__(scene, parent)
		self._fromFile = self.addAction("From File")
		self._fromFolder = self.addAction("From Folder")

# ImageControls
class ImageControls(BaseControl):
	"Image controls"

	def __init__(self, scene, parent=None):
		super().__init__(scene, parent)
		self._zoomIn = self.addAction("Zoom In")
		self._zoomOut = self.addAction("Zoom Out")
		self._rotateCW = self.addAction("Rotate Right") # Clockwise
		self._rotateCCW = self.addAction("Rotate Left") # Counter clockwise

# NavControls
class NavControl(QPushButton):
	"Arrow"

	def __init__(self, direction, orientation, parent=None):
		super().__init__(parent)
		self._direction = direction
		self._orientation = orientation
		self._thickness = 10
		self.resize(50, 50) # default size

	def paintEvent(self, ev):

		# setup

		rect = self.rect()
		x, y, w, h = rect.getRect()
		painter = QPainter(self)
		painter.setRenderHint(painter.Antialiasing)
		painter.setPen(QPen(Qt.red))
		painter.setBrush(QBrush(Qt.white))

		# figure out the arrow points.
		arrowPoints = []

		if self._direction == Direction.Backward:
			if self._orientation == Qt.Horizontal:
				arrowPoints.extend(
					[QPoint(x + w, y),
					QPoint(x + w - self._thickness, y),
					QPoint(x, y + h // 2),
					QPoint(x + w - self._thickness, y + h),
					QPoint(x + w, y + h),
					QPoint(x + self._thickness, y + h // 2),
					QPoint(x + w, y)])
			else:
				arrowPoints.extend(
					[QPoint(x, y + h),
					QPoint(x + w // 2, y),
					QPoint(x + w, y + h),
					QPoint(x + w - self._thickness, y + h),
					QPoint(x + w // 2, y + self._thickness),
					QPoint(x + self._thickness, y + h),
					QPoint(x, y + h)])

		else:
			if self._orientation == Qt.Horizontal:
				arrowPoints.extend(
					[QPoint(x, y),
					QPoint(x + self._thickness, y),
					QPoint(x + w, y + h // 2),
					QPoint(x + self._thickness, y + h),
					QPoint(x, y + h),
					QPoint(x + w - self._thickness, y + h // 2),
					QPoint(x, y)])
			else:
				arrowPoints.extend(
					[QPoint(x, y),
					QPoint(x + self._thickness, y),
					QPoint(x + w//2, y + h - self._thickness),
					QPoint(x + w - self._thickness, y),
					QPoint(x + w, y),
					QPoint(x + w//2, y + h),
					QPoint(x, y)])

		# now draw!
		painter.drawPolygon(QPolygon(arrowPoints))


class NavControls(QObject):
	"Navigation controls"

	forwardClicked = pyqtSignal()
	backwardClicked = pyqtSignal()

	def __init__(self, view, orientation=Qt.Vertical):
		super().__init__(view)
		self._view = view
		self._orientation = orientation
		self._forward = NavControl(Direction.Forward, orientation, view) # Go to next image
		self._forward.clicked.connect(self.forwardClicked.emit)
		self._backward = NavControl(Direction.Backward, orientation, view) # go to previous image
		self._backward.clicked.connect(self.backwardClicked.emit)

	def changeOrientation(self, orientation):
		self._orientation = orientation
		self._forward._orientation = orientation
		self._backward._orientation = orientation
		self.ensureEgdes()

	def ensureEgdes(self):
		"Makes sure the nav controls stays at the edges and has the right size"
		if self._orientation == Qt.Horizontal:
			_margin = self._view.verticalScrollBar().width()
			self._forward.move(self._view.width() - self._forward.width() - _margin - 5,
				self._view.height() // 2 - self._forward.height() // 2)

			self._backward.move(_margin,
				self._view.height() // 2 - self._backward.height() // 2)

			# ensure relative size
			h = self._view.height() * 0.2
			w = h * 0.4

		else:
			_margin = self._view.horizontalScrollBar().height()
			self._forward.move(self._view.width() // 2 - self._forward.width() // 2,
				self._view.height() - self._forward.height() - _margin - 5)

			self._backward.move(self._view.width() // 2 - self._backward.width() // 2,
				_margin)

			# ensure relative size
			w = self._view.width() * 0.15
			h = w * 0.25

		self._forward.resize(w, h)
		self._backward.resize(w, h)

