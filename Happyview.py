from enum import Enum

from PyQt5.QtCore import (Qt, QRectF, QObject, pyqtSignal, QThread,
						  QPointF, QSizeF, QTimeLine, QPoint, QTimer)
from PyQt5.QtGui import (QBrush, QColor, QPixmap, QPainter, QTransform, QCursor)
from PyQt5.QtWidgets import (QGraphicsView, QGraphicsScene, QGraphicsLayoutItem,
							 QGraphicsItem, QGraphicsLinearLayout, QGraphicsWidget,
							 QGraphicsPixmapItem)

import controls
import math

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

		# for zooming animation
		self._scalingFactor = 0.09

		# for rotate animation
		self._rotateAngleFactor = 2 # vinkel i grader

		# to determine if we should pan the image or move the window
		self._canPan = True
		# current zooming direction
		self._zoomIn = True

		self._mainScene = QGraphicsScene(self)
		self._mainScene.setBackgroundBrush(self._backgroundBrush)

		# init controls
		self._mainControls = controls.MainControls("*.jpg *.png *.zip *.cbz", self)
		self._navControls = controls.NavControls(self)

		self._currentGallery = None
		self._currentPixmap = None

		# animations
		self._imageAnimation = QTimeLine(500, self)
		self._imageAnimation.frameChanged.connect(self._moveTo)

		self._zoomAnimation = QTimeLine(200, self)
		self._zoomAnimation.setFrameRange(0, 10)
		self._zoomAnimation.frameChanged.connect(self._doZoom)

		self._rotationAnimation = QTimeLine(200, self)
		self._rotationAnimation.setFrameRange(0, 10)
		self._rotationAnimation.frameChanged.connect(self._doRotate)

		self._diasshowInterval = 2 # in seconds
		self._diasshowTimer = QTimer(self)
		self._diasshowTimer.timeout.connect(self.requestNext)

		# connect the main actions signals
		self._mainControls.imagesSelected.connect(self.load)
		self._mainControls.imageDirectionChanged.connect(self.toggleDirection)
		self._mainControls.zoomChanged.connect(self._startZoom)
		self._mainControls.rotateChanged.connect(self._rotationAnimation.start)
		self._mainControls.diasshowStateChanged.connect(self.toggleDiasshow)

		# connect the nav arrows
		self._navControls.forwardClicked.connect(self.requestNext)
		self._navControls.backwardClicked.connect(self.requestPrev)

		self.setScene(self._mainScene)
		self.setMinimumSize(100, 100)
		self.setImageMode(ImageMode.FitWidth)
		self.toggleDirection()
		self.resize(1000, 600)
		self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
		self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
		self._navControls.ensureEgdes()

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

	def setScalingFactor(self, f):
		""
		self._scalingFactor = f

	def toggleDirection(self):
		"Change image direction"
		if self._orientation == Qt.Vertical:
			ori = Qt.Horizontal
		else:
			ori = Qt.Vertical
		self._mainControls.setOrientation(ori)
		self._navControls.changeOrientation(ori)
		self._mainControls.ensureDirection(ori)
		self._navControls.ensureEgdes()
		
		self._orientation = ori

	def toggleDiasshow(self):
		"Play or Pause the diasshow"
		if self._diasshowTimer.isActive():
			self._diasshowTimer.stop()
		else:
			self._diasshowTimer.start(self._diasshowInterval*1000)

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
		self._mainControls.ensureDirection(self._orientation)

		super().resizeEvent(ev)

	def wheelEvent(self, ev):
		super().wheelEvent(ev)

	def _startZoom(self, _in):
		""
		self._zoomIn = _in
		if self._zoomAnimation.Running:
			self._zoomAnimation.stop()
		self._zoomAnimation.start()

	def _doZoom(self):
		""
		self.setTransformationAnchor(self.AnchorViewCenter)
		if self._zoomIn:
			zoomScale = 1+self._scalingFactor
		else:
			zoomScale = 1-self._scalingFactor
		self.scale(zoomScale, zoomScale)

	def _doRotate(self):
		"Rotere vores billede"
		self.setTransformationAnchor(self.NoAnchor)
		# grader til radianer
		radians = (self._rotateAngleFactor/360)*2*math.pi

		# rotations matrice
		# [cos, -sin, 0]
		# [sin,  cos, 0]
		# [0,    0,   1]

		matrix = QTransform(
			math.cos(radians), math.sin(radians), 0,
			-math.sin(radians), math.cos(radians), 0,
			0, 0, 1)

		# vi ganger på den nuværende matrice
		matrix = self.transform()*matrix
		self.setTransform(matrix)

	def mousePressEvent(self, ev):
		if ev.button() == Qt.LeftButton:
			if self._canPan:
				self.setDragMode(self.ScrollHandDrag)
		super().mousePressEvent(ev)

	def mouseReleaseEvent(self, ev):
		if ev.button() == Qt.LeftButton:
			if self._canPan:
				self.setDragMode(self.NoDrag)
		super().mouseReleaseEvent(ev)

if __name__ == '__main__':
	from PyQt5.QtWidgets import QApplication
	import os, sys

	app = QApplication(sys.argv)
	view = Happyview()
	view.setWindowTitle("Happyview")
	view.show()

	sys.exit(app.exec())