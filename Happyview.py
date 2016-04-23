from enum import Enum, IntEnum

from PyQt5.QtCore import (Qt, QRectF, QObject, pyqtSignal, QThread,
						  QPointF, QSizeF, QTimeLine, QPoint, QTimer, QEvent)
from PyQt5.QtGui import (QBrush, QColor, QPixmap, QPainter, QTransform, QCursor)
from PyQt5.QtWidgets import (QGraphicsView, QGraphicsScene, QGraphicsLayoutItem,
							 QGraphicsItem, QGraphicsLinearLayout, QGraphicsWidget,
							 QGraphicsPixmapItem, QPinchGesture)

import controls
import math

class ReadingDirection(Enum):
	LeftToRight = 0
	RightToLeft = 1

class ViewMode(Enum):
	SingleView = 0
	DoubleView = 1

class ImageMode(IntEnum):
	NativeSize = 0
	FitInView = 1
	FitWidth = 2
	FitHeight = 3

class Gallery(QObject):
	"""Represents and manages a list of images

	When next or previous are loaded <ImageLoaded> signal is emitted with the item
	"""
	imageLoaded = pyqtSignal(object)

	def __init__(self):
		super().__init__()

		self._images = []
		self._currentIdx = -1
		self._loadCount = 2 # amount of images to keep loaded

	def first(self):
		"Loads first image"
		if self._images:
			self._currentIdx = 0
			self.imageLoaded.emit(self._getImage(self._currentIdx))

	def last(self):
		"Loads last image"
		if self._images:
			self._currentIdx = len(self._images)-1
			self.imageLoaded.emit(self._getImage(self._currentIdx))

	def prevImage(self):
		"Loads prev image"
		nextIdx = max(0, self._currentIdx-1) # to avoid going below 0
		img = self._getImage(nextIdx)
		if img:
			self._currentIdx = nextIdx
			self.imageLoaded.emit(img)

	def nextImage(self):
		"Loads next image"
		img = self._getImage(self._currentIdx+1)
		if img:
			self._currentIdx += 1
			self.imageLoaded.emit(img)

	def _getImage(self, idx):
		"Returns images in an efficient way"
		try:
			img = self._images[idx]
			# save item if for future use
			if not isinstance(img, tuple):
				i = QGraphicsPixmapItem(QPixmap(img))
				i.setTransformationMode(Qt.SmoothTransformation)
				self._images[idx] = (i, img,)
				img = self._images[idx]

			# only keep x amounts of items loaded by unloading everything before
			try:
				prevItem = self._images[idx-self._loadCount]
				if isinstance(prevItem, tuple):
					self._images[idx-self._loadCount] = prevItem[1]
			except IndexError:
				pass

			return img[0]
		except IndexError:
			return None

	def addImages(self, paths):
		self._images.extend(paths)

class Happyview(QGraphicsView):
	""

	def __init__(self):
		super().__init__()
		self.setViewportMargins(0, 0, 0, 0)
		self.setMouseTracking(True) # we need to know where the mouse is
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
		self._currentPixmapItem = None

		# animations
		self._zoomAnimation = QTimeLine(200, self)
		self._zoomAnimation.setFrameRange(0, 10)
		self._zoomAnimation.frameChanged.connect(self._doZoom)

		self._rotationAnimation = QTimeLine(200, self)
		self._rotationAnimation.setFrameRange(0, 10)
		self._rotationAnimation.frameChanged.connect(self._doRotate)

		self._diasshowTimer = QTimer(self)
		self._diasshowTimer.timeout.connect(self.requestNext)

		# connect the main actions signals
		self._mainControls.imagesSelected.connect(self.load)
		self._mainControls.imageDirectionChanged.connect(self.toggleDirection)
		self._mainControls.zoomChanged.connect(self._startZoom)
		self._mainControls.rotateChanged.connect(self._rotationAnimation.start)
		self._mainControls.diasshowStateChanged.connect(self.toggleDiasshow)
		self._mainControls.imageModeChanged.connect(self.setImageMode)

		# connect the nav arrows
		self._navControls.forwardClicked.connect(self.requestNext)
		self._navControls.backwardClicked.connect(self.requestPrev)

		self.setScene(self._mainScene)
		self.setMinimumSize(350, 350)
		self.setImageMode(ImageMode.FitWidth)
		self.toggleDirection()
		self.resize(1000, 600)
		self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
		self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
		self._navControls.ensureEgdes()

	def requestNext(self):
		"Attempts to show next image in line"
		if self._currentGallery:
			self._currentGallery.nextImage()

	def requestPrev(self):
		"Attempts to show previous image in line"
		if self._currentGallery:
			self._currentGallery.prevImage()

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

	def updateView(self):
		""
		if self._currentPixmapItem:
			item = self._currentPixmapItem
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
			elif self._imageMode == ImageMode.FitInView:
				xscale = yscale = min(xscale, yscale)
			else:
				xscale = yscale = 1
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
			self._currentGallery.imageLoaded.disconnect()
		if self._currentPixmapItem:
			self._mainScene.removeItem(self._currentPixmapItem)
			self._currentPixmapItem = None

		self._currentGallery = g
		g.imageLoaded.connect(self._setItem)
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

	def toggleDiasshow(self, secs=5):
		"Play or Pause the diasshow"
		print(secs, "secs wtf")
		if self._diasshowTimer.isActive():
			self._diasshowTimer.stop()
		else:
			self._diasshowTimer.start(secs*1000)

	def setImageMode(self, mode):
		""
		if mode == ImageMode.NativeSize:
			self._imageMode = ImageMode.NativeSize
			self.setDragMode(self.ScrollHandDrag)
		else:
			self.setDragMode(self.NoDrag)

		if mode == ImageMode.FitInView:
			self._imageMode = ImageMode.FitInView
		elif mode == ImageMode.FitWidth:
			self._imageMode = ImageMode.FitWidth
		elif mode == ImageMode.FitHeight:
			self._imageMode = ImageMode.FitHeight

		self.updateView()

	#def toggleViewMode(self):
	#	"Toggle view mode"
	#	if self._viewMode == ViewMode.SingleView:
	#		self._viewMode = ViewMode.DoubleView
	#	else:
	#		self._viewMode = ViewMode.SingleView

	def toggleFullscreen(self):
		"Toggle fullscreen"
		if self.isFullScreen():
			self.showNormal()
		else:
			self.showFullScreen()
		self.updateView()

	def resizeEvent(self, ev):
		# center controls
		self._navControls.ensureEgdes()
		self._mainControls.ensureDirection(self._orientation)

		super().resizeEvent(ev)

	def wheelEvent(self, ev):
		super().wheelEvent(ev)

	def _setItem(self, item):
		"Recieves a QGraphicsPixmapItem by the Gallery class"
		if self._currentPixmapItem:
			self._mainScene.removeItem(self._currentPixmapItem)
		if item:
			self._mainScene.addItem(item)
			self._currentPixmapItem = item
		self.updateView()

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

	def mouseMoveEvent(self, ev):
		# automatically show maincontrols when near mouse position
		if self._mainControls.geometry().adjusted(0, 0, 50, 50).contains(ev.pos()):
			self._mainControls.show()
		else:
			self._mainControls.hide()

		# automatically show nav arrows when near mouse position
		if self._navControls._forward.geometry().contains(ev.pos()):
			self._navControls._forward.show()
		else:
			self._navControls._forward.hide()
		if self._navControls._backward.geometry().contains(ev.pos()):
			self._navControls._backward.show()
		else:
			self._navControls._backward.hide()

		return super().mouseMoveEvent(ev)

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

	def mouseDoubleClickEvent(self, ev):
		self.toggleFullscreen()
		return super().mouseDoubleClickEvent(ev)

if __name__ == '__main__':
	from PyQt5.QtWidgets import QApplication
	import os, sys

	app = QApplication(sys.argv)
	view = Happyview()
	view.setWindowTitle("Happyview")
	view.show()

	sys.exit(app.exec())