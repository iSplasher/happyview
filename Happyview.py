from enum import Enum

from PyQt5.QtCore import (Qt, QRectF, QObject, pyqtSignal, QThread,
						  QPointF, QSizeF)
from PyQt5.QtGui import (QBrush, QColor, QPixmap, QPainter, QTransform)
from PyQt5.QtWidgets import (QGraphicsView, QGraphicsScene, QGraphicsLayoutItem,
							 QGraphicsItem, QGraphicsLinearLayout, QGraphicsWidget,
							 QGraphicsPixmapItem )

import controls

class ReadingDirection(Enum):
	LeftToRight = 0
	RightToLeft = 1

class ViewMode(Enum):
	SingleView = 0
	DoubleView = 1

class ImageMode(Enum):
	FitInView = 0
	FitWidth = 1
	FitHeight = 2
	NativeSize = 3

class ImageList(QObject):
	"Represents and manages a list of images"
	imagesLoaded = pyqtSignal(list)

	def __init__(self):
		super().__init__()
		self._images = []
		self._currentIdx = 0
		self.preloadCount = 3 # amount of images to load at a time

	@property
	def current(self):
		""
		pass

	def loadNext(self):
		""
		try:
			self.imagesLoaded.emit(self._images[self._currentIdx])
			self._currentIdx += 1
		except IndexError:
			self.imagesLoaded.emit([])

	def loadPrev(self):
		""
		pass

	def addImage(self, img_path):
		self._images.append(QPixmap(img_path))

class ImageItem(QGraphicsLayoutItem):
	""
	def __init__(self, img):
		QGraphicsLayoutItem.__init__(self)
		QGraphicsItem.__init__(self)
		self._pixmapItem = QGraphicsPixmapItem(img)
		self._pixmapItem.setTransformationMode(Qt.SmoothTransformation)
		self.setGraphicsItem(self._pixmapItem)

	def setGeometry(self, rect):
		super().setGeometry(rect)
		self._pixmapItem.setPos(rect.topLeft())

	def sizeHint(self, hint, constraint = QSizeF()):
		return self._pixmapItem.boundingRect().size()


class ImageScene(QGraphicsScene):
	""

	def __init__(self, parent, orientation):
		super().__init__(parent)
		self._mainItem = QGraphicsWidget()
		self._layout = QGraphicsLinearLayout(orientation, self._mainItem)
		self._mainItem.setLayout(self._layout)
		self.addItem(self._mainItem)
		self._mainItem.moveBy(0, 0)
		self._mainItem.geometryChanged.connect(lambda: self.setSceneRect(self._mainItem.geometry()))

	def setOrientation(self, ori):
		""
		self._layout.setOrientation(ori)

	def showImages(self, imagelist):
		""
		for i in imagelist:
			self._layout.addItem(ImageItem(i))

class Happyview(QGraphicsView):
	""
	loadImages = pyqtSignal(str)
	requestPrev = pyqtSignal()
	requestNext = pyqtSignal()

	def __init__(self):
		super().__init__()
		self.setViewportMargins(0, 0, 0, 0)
		self._orientation = Qt.Horizontal # which way to go for the next image
		self._readingDirection = ReadingDirection.LeftToRight
		self._viewMode = ViewMode.SingleView
		self._imageMode = ImageMode.NativeSize
		self._backgroundColor = "#404244"
		self._backgroundBrush = QBrush(QColor(self._backgroundColor))

		self._mainScene = ImageScene(self, self._orientation)
		self._mainScene.setBackgroundBrush(self._backgroundBrush)

		# init image manager
		self._imageList = ImageList()
		self._imageThread = QThread(self)
		self._imageList.moveToThread(self._imageThread)
		# connect the signals
		self._imageList.imagesLoaded.connect(self._mainScene.showImages)
		self.requestNext.connect(self._imageList.loadNext)
		self.requestPrev.connect(self._imageList.loadPrev)
		self.loadImages.connect(self._imageList.addImage)

		# init controls
		self._mainControls = controls.MainControls("*.jpg *.png", self)
		self._imageControls = controls.ImageControls(self)
		self._navControls = controls.NavControls(self)

		self._mainControls.imagesSelected.connect(self.load)
		self._navControls.forwardClicked.connect(self.forward)
		self._navControls.backwardClicked.connect(self.backward)

		self.setScene(self._mainScene)
		self.setMinimumSize(100, 100)
		self.setImageDirection(self._orientation)
		#self.setImageMode(ImageMode.FitInView)
		self._imageThread.start()

	def forward(self):
		"Show next image"
		self.requestNext.emit()
		print("Scene Rect", self.sceneRect())
		print("Item Rect", self._mainScene._mainItem.geometry())

	def backward(self):
		"Show previous image"
		self.requestPrev.emit()

	def load(self, sources):
		"""
		params:
			sources - list of image paths
		"""
		assert isinstance(sources, list)
		self._mainScene.showImages([QPixmap(x) for x in sources])

	def setImageDirection(self, ori):
		"Change image direction"
		self._orientation = ori
		self._mainControls.setOrientation(ori)
		self._imageControls.setOrientation(ori)
		self._navControls.changeOrientation(ori)

	def setImageMode(self, immode):
		"Change image mode"
		self._imageMode = immode
		#if immode == ImageMode.FitInView:
		#	self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
		#	self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
		#else:
		#	self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
		#	self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

	def toggleViewMode(self):
		"Toggle view mode"
		if self._viewMode == ViewMode.SingleView:
			self._viewMode = ViewMode.DoubleView
		else:
			self._viewMode = ViewMode.SingleView

	def resizeEvent(self, ev):
		# center controls
		self._navControls.ensureEgdes()
		if self._orientation == Qt.Horizontal:
			self._mainControls.move(0, 0)
			self._mainControls.resize(ev.size().width(), self._mainControls.iconSize().height()//2)
			self._imageControls.move(0, self.height()-self._imageControls.height()//2-self.horizontalScrollBar().height())
			self._imageControls.resize(ev.size().width(), self._imageControls.iconSize().height()//2)
		else:
			self._mainControls.move(0, self.height()//2-self._mainControls.halfHeight)
			self._imageControls.move(self.width()-self._imageControls.width(),
						   self.height()//2-self._imageControls.halfHeight)

		super().resizeEvent(ev)
		if self._imageMode == ImageMode.FitInView:
			self.fitInView(self.sceneRect(), Qt.KeepAspectRatio)
			#matrix = QTransform(1,0,0,0,1,0,0,0,1)
			#xscale = max(1, self.width())/max(1, self.sceneRect().width())
			#yscale = max(1, self.height())/max(1, self.sceneRect().height())
			#xscale = yscale = min(xscale, yscale)
			#matrix.scale(xscale,yscale)
			#self.setTransform(matrix)

if __name__ == '__main__':
	from PyQt5.QtWidgets import QApplication
	import os, sys

	app = QApplication(sys.argv)
	view = Happyview()
	view.setWindowTitle("Happyview")
	view.resize(1000, 600)
	view.show()

	sys.exit(app.exec())