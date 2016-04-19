from enum import Enum

from PyQt5.QtCore import Qt, QSize, QRect, QPoint, pyqtSignal, QObject
from PyQt5.QtGui import (QBrush, QColor, QPainter, QPen, QBrush,
						 QPolygon, QIcon)
from PyQt5.QtWidgets import (QToolBar, QPushButton, QFileDialog, QWidget,
							 QSizePolicy)

import zipfile, os

class Direction(Enum):
	Forward = 0
	Backward = 1

class BaseControl(QToolBar):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.setOrientation(Qt.Horizontal)
		self.setIconSize(QSize(50, 50))
		self.setAutoFillBackground(True)

		self.setStyleSheet(self.styleSheet()+
					 """
					 background-color: rgba(255, 255, 255, 0.4);
					 """)

	def centerToolActions(self):
		""
		pass
	@property
	def halfWidth(self):
		return self.width() // 2

	@property
	def halfHeight(self):
		return self.height() // 2

# Main Controls

class MainControls(BaseControl):
	"Main controls for changes general settings"
	imagesSelected = pyqtSignal(list)
	viewModeChanged = pyqtSignal()
	imageDirectionChanged = pyqtSignal()
	diasshowStateChanged = pyqtSignal()
	zoomChanged = pyqtSignal(bool)
	rotateChanged = pyqtSignal()
	
	def __init__(self, supported_exts, parent=None):
		super().__init__(parent)

		self._diasshowRunning = False

		# a dummy widget to center actions
		spacer1 = QWidget()
		spacer1.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
		self.addWidget(spacer1)

		self.supportedImages = supported_exts
		self._fromFile = self.addAction(QIcon("icons/image-outline.svg"), "", self.chooseFile) # load images from file
		self._fromFolder = self.addAction(QIcon("icons/folder-open.svg"), "", self.chooseFolder) # load images from folder
		self._viewMode = self.addAction(QIcon("icons/eye-outline.svg"), "", self.viewModeChanged.emit) # View single image or 2 images like a book
		self._imgDirection = self.addAction(QIcon("icons/arrow-move-outline.svg"), "", self.imageDirectionChanged.emit) # Horizontal or Vertical
		self._playDias = self.addAction(QIcon("icons/media-play-outline.svg"), "", self.diasshowState) # start diasshow
		self._zoomIn = self.addAction(QIcon("icons/zoom-in-outline.svg"), "", lambda: self.zoomChanged.emit(True))
		self._zoomOut = self.addAction(QIcon("icons/zoom-out-outline.svg"), "", lambda: self.zoomChanged.emit(False))
		self._rotateCW = self.addAction(QIcon("icons/rotate-cw-outline.svg"), "", self.rotateChanged.emit) # Clockwise
		#self._rotateCCW = self.addAction("Rotate Left") # Counter clockwise

		# a dummy widget to center actions
		spacer2 = QWidget()
		spacer2.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
		self.addWidget(spacer2)

	def chooseFolder(self):
		folder = QFileDialog.getExistingDirectory(self.parentWidget(), "Choose folder")
		if folder:
			self.imagesSelected.emit(
				[os.path.join(folder, x) for x in os.listdir(folder) if x.endswith((".jpg", ".png", ".zip", ".cbz"))])

	def chooseFile(self):
		files, _ = QFileDialog.getOpenFileNames(self.parentWidget(), "Select image", filter=self.supportedImages)
		if files: # if a file was chosen
			images = []
			for f in files:
				if f.endswith((".zip", ".cbz")):
					continue
				images.append(f)
			self.imagesSelected.emit(images)

	def ensureDirection(self, ori):
		""
		self.move(0, 0)
		pSize = self.parentWidget().size()
		if ori == Qt.Horizontal:
			self.resize(pSize.width(), self.iconSize().height()//2)
		else:
			self.resize(self.iconSize().width()//2, pSize.height())

	def diasshowState(self):
		"Changes the diasshow icon and emits signal"
		if self._diasshowRunning:
			i = "icons/media-play-outline.svg"
			self._diasshowRunning = False
		else:
			i = "icons/media-pause-outline.svg"
			self._diasshowRunning = True
		self._playDias.setIcon(QIcon(i))
		self.diasshowStateChanged.emit()

# NavControls
class NavControl(QPushButton):
	"Arrow"

	def __init__(self, direction, orientation, parent=None):
		super().__init__(parent)
		self._direction = direction
		self._orientation = orientation
		self._thickness = 15
		self.resize(35, 35) # default size

	def paintEvent(self, ev):

		# setup

		rect = self.rect()
		x, y, w, h = rect.getRect()
		painter = QPainter(self)
		painter.setRenderHint(painter.Antialiasing)
		if self.underMouse():
			penColor = QColor(0,0,0)
			brushColor = QColor(240, 240, 240, 200)
		else:
			penColor = QColor(0,0,0)
			brushColor = QColor(240, 240, 240, 100)
		painter.setPen(QPen(penColor))
		painter.setBrush(QBrush(brushColor))

		# figure out the arrow points.
		arrowPoints = []

		if self._direction == Direction.Backward:
			if self._orientation == Qt.Horizontal:
				arrowPoints.extend(
					[QPoint(x + w, y),
					#QPoint(x + w - self._thickness, y),
					QPoint(x, y + h // 2),
					#QPoint(x + w - self._thickness, y + h),
					QPoint(x + w, y + h),
					QPoint(x + self._thickness, y + h // 2),
					QPoint(x + w, y)])
			else:
				arrowPoints.extend(
					[QPoint(x, y + h),
					QPoint(x + w // 2, y),
					QPoint(x + w, y + h),
					#QPoint(x + w - self._thickness, y + h),
					QPoint(x + w // 2, y + self._thickness),
					#QPoint(x + self._thickness, y + h),
					QPoint(x, y + h)])

		else:
			if self._orientation == Qt.Horizontal:
				arrowPoints.extend(
					[QPoint(x, y),
					#QPoint(x + self._thickness, y),
					QPoint(x + w, y + h // 2),
					#QPoint(x + self._thickness, y + h),
					QPoint(x, y + h),
					QPoint(x + w - self._thickness, y + h // 2),
					QPoint(x, y)])
			else:
				arrowPoints.extend(
					[QPoint(x, y),
					#QPoint(x + self._thickness, y),
					QPoint(x + w//2, y + h - self._thickness),
					#QPoint(x + w - self._thickness, y),
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
		self._view = view.viewport()
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
			# ensure positioning
			_margin = 15
			self._forward.move(self._view.width() - self._forward.width() - _margin,
				self._view.height() // 2 - self._forward.height() // 2)

			self._backward.move(_margin,
				self._view.height() // 2 - self._backward.height() // 2)

			# ensure relative size
			h = self._view.height() * 0.12
			w = h * 0.4

		else:
			# ensure positioning
			_margin = 10
			self._forward.move(self._view.width() // 2 - self._forward.width() // 2,
				self._view.height() - self._forward.height() - _margin)

			self._backward.move(self._view.width() // 2 - self._backward.width() // 2,
				_margin)

			# ensure relative size
			w = self._view.width() * 0.12
			h = w * 0.4

		self._forward.resize(w, h)
		self._backward.resize(w, h)

