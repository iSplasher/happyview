from enum import Enum

from PyQt5.QtCore import Qt, QSize, QRect, QPoint, pyqtSignal, QObject
from PyQt5.QtGui import (QBrush, QColor, QPainter, QPen, QBrush,
						 QPolygon, QIcon)
from PyQt5.QtWidgets import (QToolBar, QPushButton, QFileDialog, QWidget,
							 QSizePolicy, QMenu, QToolButton, QActionGroup)

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
	#viewModeChanged = pyqtSignal()
	imageModeChanged = pyqtSignal(int)
	imageDirectionChanged = pyqtSignal()
	diasshowStateChanged = pyqtSignal(int)
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
		self._fromFile.setToolTip("Load image")
		self._fromFolder = self.addAction(QIcon("icons/folder-open.svg"), "", self.chooseFolder) # load images from folder
		self._fromFolder.setToolTip("Load from directory")

		# View in native size, fit width, fit height or fit image
		self._imageMode = QToolButton(self)
		self._imageMode.setIcon(QIcon("icons/eye-outline.svg"))
		self._imageMode.setToolTip("Image view mode")
		self._imageMode.setPopupMode(QToolButton.InstantPopup)
		self.addWidget(self._imageMode)
		
		# imageMode menu
		imageModeMenu = QMenu(self)
		imageModeActions = QActionGroup(imageModeMenu)
		imModeAct1 = imageModeActions.addAction("Native size")
		imModeAct1.setCheckable(True)
		imModeAct1.triggered.connect(lambda: self.imageModeChanged.emit(0))
		imModeAct2 = imageModeActions.addAction("Fit in view")
		imModeAct2.setCheckable(True)
		imModeAct2.triggered.connect(lambda: self.imageModeChanged.emit(1))
		imModeAct3 = imageModeActions.addAction("Fit width")
		imModeAct3.setCheckable(True)
		imModeAct3.triggered.connect(lambda: self.imageModeChanged.emit(2))
		imModeAct4 = imageModeActions.addAction("Fit height")
		imModeAct4.setCheckable(True)
		imModeAct4.triggered.connect(lambda: self.imageModeChanged.emit(3))
		imageModeActions.setExclusive(True)
		imageModeMenu.addActions(imageModeActions.actions())
		self._imageMode.setMenu(imageModeMenu)

		
		self._imgDirection = self.addAction(QIcon("icons/arrow-move-outline.svg"), "", self.imageDirectionChanged.emit) # Horizontal or Vertical
		self._imgDirection.setToolTip("Toggle image direction")

		# start or stop diasshow
		self._playDias = self.addAction(QIcon("icons/media-play-outline.svg"), "", self.diasshowState)
		self._playDias.setToolTip("Start/stop diasshow")

		#diasshow menu
		self._diasMenu = QMenu(self)
		self._diasMenu.addAction("5 seconds", lambda: self.diasshowState(5))
		self._diasMenu.addAction("10 seconds", lambda: self.diasshowState(10))
		self._diasMenu.addAction("30 seconds", lambda: self.diasshowState(30))
		self._diasMenu.addAction("5 minutes", lambda: self.diasshowState(60*5))
		self._diasMenu.addAction("10 minutes", lambda: self.diasshowState(600))
		self._playDias.setMenu(self._diasMenu)


		self._zoomIn = self.addAction(QIcon("icons/zoom-in-outline.svg"), "", lambda: self.zoomChanged.emit(True))
		self._zoomOut = self.addAction(QIcon("icons/zoom-out-outline.svg"), "", lambda: self.zoomChanged.emit(False))
		self._rotateCW = self.addAction(QIcon("icons/rotate-cw-outline.svg"), "", self.rotateChanged.emit) # Clockwise
		self._rotateCW.setToolTip("Rotate Clockwise")
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

	def diasshowState(self, secs=3):
		"Changes the diasshow icon and emits signal"
		if self._diasshowRunning:
			i = "icons/media-play-outline.svg"
			self._diasshowRunning = False
		else:
			i = "icons/media-pause-outline.svg"
			self._diasshowRunning = True
		self._playDias.setIcon(QIcon(i))
		self.diasshowStateChanged.emit(secs)

# NavControls
class NavControl(QPushButton):
	"Arrow"

	def __init__(self, direction, orientation, parent=None):
		super().__init__(parent)
		self._direction = direction
		self._orientation = orientation
		self._thickness = 15 # arrow thickness
		self._brushColor = QColor(240, 240, 240, 200) # default arrow color
		self.resize(35, 35) # default size

	def paintEvent(self, ev):

		# setup

		rect = self.rect()
		x, y, w, h = rect.getRect()
		
		if self._orientation == Qt.Vertical:
			x = w//4
			w = w*0.4
		else:
			y = h//4
			h = h*0.4

		painter = QPainter(self)
		painter.setRenderHint(painter.Antialiasing)
		penColor = QColor(0,0,0)
		painter.setPen(QPen(penColor))
		painter.setBrush(QBrush(self._brushColor))

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
		if orientation == Qt.Horizontal:
			size = (50, 300,)
		else:
			size = (300, 50,)

		self._forward.resize(*size)
		self._backward.resize(*size)

		self.ensureEgdes()

	def ensureEgdes(self):
		"Makes sure the nav controls stays at the edges and has the right size"
		if self._orientation == Qt.Horizontal:
			_margin = 15
			# ensure positioning
			self._forward.move(self._view.width() - self._forward.width() - _margin,
				self._view.height() // 2 - self._forward.height() // 2)

			self._backward.move(_margin,
				self._view.height() // 2 - self._backward.height() // 2)
		else:
			# ensure positioning
			_margin = 10
			self._forward.move(self._view.width() // 2 - self._forward.width() // 2,
				self._view.height() - self._forward.height() - _margin)

			self._backward.move(self._view.width() // 2 - self._backward.width() // 2,
				_margin)


