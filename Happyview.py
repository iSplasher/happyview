from enum import Enum

from PyQt5.QtCore import (Qt, QRectF, QObject, pyqtSignal, QThread,
						  QPointF, QSizeF, QTimeLine)
from PyQt5.QtGui import (QBrush, QColor, QPixmap, QPainter, QTransform, QCursor)
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

class Gallery(QObject):
	"Represents and manages a list of images"
	imageLoaded = pyqtSignal(list)

	def __init__(self):
		super().__init__()

		self._images = []
		self._currentIdx = -1
		self._loaded = False


	def first(self):
		""
		if self._images:
			return self._images[0]

	def last(self):
		if self._images:
			return self._images[len(self._images)-1]

	def currentImage(self):
		""
		try:
			return self._images[self._currentIdx]
		except IndexError:
			return None

	def prevImage(self):
		""
		try:
			img = self._images[self._currentIdx-1]
			self._currentIdx -= 1
			return img
		except IndexError:
			return None

	def nextImage(self):
		""
		try:
			img = self._images[self._currentIdx+1]
			self._currentIdx += 1
			return img
		except IndexError:
			return None

	def addImages(self, paths):
		for img in paths:
			i = QGraphicsPixmapItem(QPixmap(img))
			i.setTransformationMode(Qt.SmoothTransformation)
			self._images.append(i)

	def setOrientation(self, ori):
		""
		self._layout.setOrientation(ori)

class Happyview(QGraphicsView):
	""

	def __init__(self):
		super().__init__()
		self.setViewportMargins(0, 0, 0, 0)
		self._orientation = Qt.Vertical # which way to go for the next image
		self._readingDirection = ReadingDirection.LeftToRight
		self._imageMode = None
		self._viewMode = ViewMode.SingleView
		self._backgroundColor = "#404244"
		self._backgroundBrush = QBrush(QColor(self._backgroundColor))

		self._mainScene = QGraphicsScene(self)
		self._mainScene.setBackgroundBrush(self._backgroundBrush)

		# init controls
		self._mainControls = controls.MainControls("*.jpg *.png *.zip *.cbz", self)
		self._navControls = controls.NavControls(self)

		self._mainControls.imagesSelected.connect(self.load)
		self._navControls.forwardClicked.connect(self.requestNext)
		self._navControls.backwardClicked.connect(self.requestPrev)

		self._currentGallery = None
		self._currentPixmap = None

		# animation
		self._imageAnimation = QTimeLine(500, self)
		self._imageAnimation.frameChanged.connect(self._moveTo)

		self.setScene(self._mainScene)
		self.setMinimumSize(100, 100)
		self.setImageDirection(self._orientation)
		self.setImageMode(ImageMode.FitWidth)

	def requestNext(self):
		""
		if self._currentGallery:
			if self._currentPixmap:
				self._mainScene.removeItem(self._currentGallery.currentImage())
			item = self._currentGallery.nextImage()
			if item:
				self._mainScene.addItem(item)
				self._currentPixmap = item.pixmap()
				self.updateView()

	def requestPrev(self):
		""
		if self._currentGallery:
			if self._currentPixmap:
				self._mainScene.removeItem(self._currentGallery.currentImage())
			item = self._currentGallery.prevImage()
			if item:
				self._mainScene.addItem(item)
				self._currentPixmap = item.pixmap()
				self.updateView()

	def centerMiddle(self, rect):
		""
		if self._orientation == Qt.Horizontal:
			_from = self.sceneRect().x()
			_to = rect.x() + rect.width()//2
		else:
			_from = self.sceneRect().y()
			r = self._mainScene._middlePix.geometry()
			_to = rect.y() + rect.height()//2
		self._imageAnimation.setFrameRange(_from, _to)
		self._imageAnimation.start()

	def _moveTo(self, p):
		""
		if self._orientation == Qt.Horizontal:
			self.centerOn(p, self.sceneRect().y())
		else:
			self.centerOn(self.sceneRect().x(), p)

	def updateView(self):
		""
		if self._currentPixmap:
			item = self._currentGallery.currentImage()
			if self._imageMode in (ImageMode.FitInView, ImageMode.FitHeight, ImageMode.FitWidth):
				# skalerings matrice
				# [1, 0, 0]
				# [0, 1, 0]
				# [0, 0, 1]
				matrix = QTransform(1,0,0,0,1,0,0,0,1)

				xscale = max(1, self.width())/max(1, item.boundingRect().size().width()+2)
				yscale = max(1, self.height())/max(1, item.boundingRect().size().height()+2)

				if self._imageMode == ImageMode.FitWidth:
					yscale = xscale
				elif self._imageMode == ImageMode.FitHeight:
					xscale = yscale
				else:
					xscale = yscale = min(xscale, yscale)
				matrix.scale(xscale,yscale)
				self.setTransform(matrix)
		self.setSceneRect(item.boundingRect())

	def load(self, sources):
		"""
		params:
			sources - list of image paths
		"""
		assert isinstance(sources, list)
		g = Gallery()
		g.addImages(sources)
		self.setGallery(g)

	def setGallery(self, g):
		""
		assert isinstance(g, Gallery)
		if self._currentGallery:
			self._mainScene.removeItem(self._currentGallery.currentImage())
			self._currentPixmap = None

		self._currentGallery = g
		self.requestNext()

	def setImageDirection(self, ori):
		"Change image direction"
		self._orientation = ori
		self._mainControls.setOrientation(ori)
		self._navControls.changeOrientation(ori)

	def setImageMode(self, mode):
		""
		self._imageMode = mode
		if mode == ImageMode.NativeSize:
			self.setDragMode(self.ScrollHandDrag)
		else:
			self.setDragMode(self.NoDrag)

	def toggleViewMode(self):
		"Toggle view mode"
		if self._viewMode == ViewMode.SingleView:
			self._viewMode = ViewMode.DoubleView
		else:
			self._viewMode = ViewMode.SingleView

	def resizeEvent(self, ev):
		# center controls
		self._navControls.ensureEgdes()
		self._mainControls.move(0, 0)
		if self._orientation == Qt.Horizontal:
			self._mainControls.resize(ev.size().width(), self._mainControls.iconSize().height()//2)
		else:
			self._mainControls.resize(self._mainControls.iconSize().width()//2, ev.size().height())

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