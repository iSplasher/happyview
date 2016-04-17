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

class ReadingMode(Enum):
	Discontinuous = 0
	Continuous = 1

class ViewMode(Enum):
	SingleView = 0
	DoubleView = 1

class ImageMode(Enum):
	FitInView = 0
	FitWidth = 1
	FitHeight = 2
	NativeSize = 3

#class ImageList(QObject):
#	"Represents and manages a list of images"
#	imageLoaded = pyqtSignal(list)

#	def __init__(self):
#		super().__init__()
#		self._images = []
#		self._currentIdx = -1
#		self.preloadCount = 3 # amount of images to load at a time

#	@property
#	def current(self):
#		""
#		try:
#			return self._images[self._currentIdx]
#		except IndexError:
#			return None

#	def addImage(self, paths):
#		for img in paths:
#			self._images.append(QPixmap(img))
#		self.loadNext()

class ImageItem(QGraphicsLayoutItem):
	""
	def __init__(self, img, view):
		super().__init__()
		self.view = view
		self._pixmapItem = QGraphicsPixmapItem(img)
		self._pixmapItem.setTransformationMode(Qt.SmoothTransformation)
		self.setGraphicsItem(self._pixmapItem)

	def setGeometry(self, rect):
		super().setGeometry(rect)
		self._pixmapItem.setPos(rect.topLeft())

	def sizeHint(self, hint, constraint = QSizeF()):
		#if hint == Qt.MinimumSize:
		#	return QSizeF(self.view.size())
		return self._pixmapItem.boundingRect().size()


class ImageScene(QGraphicsScene):
	""
	loadImages = pyqtSignal(list)
	requestPrev = pyqtSignal()
	requestNext = pyqtSignal()

	def __init__(self, parent, orientation):
		super().__init__(parent)
		self._view = parent
		self._mainItem = QGraphicsWidget()
		self._layout = QGraphicsLinearLayout(orientation, self._mainItem)
		self._mainItem.setLayout(self._layout)
		self.addItem(self._mainItem)
		self._mainItem.moveBy(0, 0)
		self._mainItem.geometryChanged.connect(lambda: self.setSceneRect(self._mainItem.geometry()))
		self._currentItem = -1
		self._items = []

		## init image manager
		#self._imageList = ImageList()
		#self._imageThread = QThread(self)
		#self._imageList.moveToThread(self._imageThread)
		## connect the signals
		#self._imageList.imagesLoaded.connect(self.showImages)
		#self.requestNext.connect(self._imageList.loadNext)
		#self.requestPrev.connect(self._imageList.loadPrev)
		#self.loadImages.connect(self._imageList.addImages)

		#self._imageThread.start()

	def requestCurrent(self):
		return self._items[self._currentItem]

	def requestNext(self):
		""
		self._currentItem += 1
		item = self._items[self._currentItem]
		return item.graphicsItem()

	def requestPrev(self):
		""
		self._currentItem -= 1
		item = self._items[self._currentItem]
		return item.graphicsItem()

	def setOrientation(self, ori):
		""
		self._layout.setOrientation(ori)

	def addImages(self, imagelist):
		""
		for i in imagelist:
			t = ImageItem(QPixmap(i), self._view)
			self._layout.addItem(t)
			self._items.append(t)

class Happyview(QGraphicsView):
	""

	def __init__(self):
		super().__init__()
		self.setViewportMargins(0, 0, 0, 0)
		self._orientation = Qt.Horizontal # which way to go for the next image
		self._readMode = ReadingMode.Discontinuous
		self._readingDirection = ReadingDirection.LeftToRight
		self._imageMode = ImageMode.FitInView
		self._viewMode = ViewMode.SingleView
		self._backgroundColor = "#404244"
		self._backgroundBrush = QBrush(QColor(self._backgroundColor))

		self._mainScene = ImageScene(self, self._orientation)
		self._mainScene.setBackgroundBrush(self._backgroundBrush)

		# init controls
		self._mainControls = controls.MainControls("*.jpg *.png", self)
		self._imageControls = controls.ImageControls(self)
		self._navControls = controls.NavControls(self)

		self._mainControls.imagesSelected.connect(self.load)
		self._navControls.forwardClicked.connect(self.showNext)
		self._navControls.backwardClicked.connect(self.showPrev)

		self.setScene(self._mainScene)
		self.setMinimumSize(100, 100)
		self.setImageDirection(self._orientation)

	def _applyTransformation(self):
		""
		item = self._mainScene.requestCurrent()
		if item:
			if self._imageMode in (ImageMode.FitInView, ImageMode.FitHeight, ImageMode.FitWidth):
				# skalerings matrice
				# [1, 0, 0]
				# [0, 1, 0]
				# [0, 0, 1]
				matrix = QTransform(1,0,0,0,1,0,0,0,1)

				xscale = max(1, self.width())/max(1, item.geometry().size().width()+2)
				yscale = max(1, self.height())/max(1, item.geometry().size().height()+2)

				if self._imageMode == ImageMode.FitWidth:
					yscale = xscale
				elif self._imageMode == ImageMode.FitHeight:
					xscale = yscale
				else:
					xscale = yscale = min(xscale, yscale)
				matrix.scale(xscale,yscale)
				self.setTransform(matrix)
		if self._readMode == ReadingMode.Discontinuous:
			self.setSceneRect(item.geometry())

	def showNext(self):
		""
		item = self._mainScene.requestNext()
		self.centerOn(item)
		self._applyTransformation()

	def showPrev(self):
		""
		item = self._mainScene.requestPrev()
		self.centerOn(item)
		self._applyTransformation()

	def load(self, sources):
		"""
		params:
			sources - list of image paths
		"""
		assert isinstance(sources, list)
		self._mainScene.addImages(sources)
		self.showNext()

	def setImageDirection(self, ori):
		"Change image direction"
		self._orientation = ori
		self._mainControls.setOrientation(ori)
		self._imageControls.setOrientation(ori)
		self._navControls.changeOrientation(ori)

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


if __name__ == '__main__':
	from PyQt5.QtWidgets import QApplication
	import os, sys

	app = QApplication(sys.argv)
	view = Happyview()
	view.setWindowTitle("Happyview")
	view.resize(1000, 600)
	view.show()

	sys.exit(app.exec())