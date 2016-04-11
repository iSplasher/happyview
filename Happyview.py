from enum import Enum

from PyQt5.QtCore import Qt, QRectF, QObject, pyqtSignal, QThread
from PyQt5.QtGui import (QBrush, QColor, QPixmap)
from PyQt5.QtWidgets import (QGraphicsView, QGraphicsScene)

import controls

class ReadingDirection(Enum):
	LeftToRight = 0
	RightToLeft = 1

class ViewMode(Enum):
	SingleView = 0
	DoubleView = 1

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

class ImageScene(QGraphicsScene):
	""

	def __init__(self, parent):
		super().__init__(parent)

class Happyview(QGraphicsView):
	""
	loadImages = pyqtSignal(str)
	requestPrev = pyqtSignal()
	requestNext = pyqtSignal()

	def __init__(self):
		super().__init__()
		self._orientation = Qt.Horizontal # which way to go for the next image
		self._readingDirection = ReadingDirection.LeftToRight
		self._viewMode = ViewMode.SingleView
		self._backgroundColor = "#404244"
		self._backgroundBrush = QBrush(QColor(self._backgroundColor))

		self._mainScene = QGraphicsScene(self)
		self._mainScene.setBackgroundBrush(self._backgroundBrush)

		# init image manager
		self._imageList = ImageList()
		self._imageThread = QThread(self)
		self._imageList.moveToThread(self._imageThread)
		# connect the signals
		self._imageList.imagesLoaded.connect(self.setImage)
		self.requestNext.connect(self._imageList.loadNext)
		self.requestPrev.connect(self._imageList.loadPrev)
		self.loadImages.connect(self._imageList.addImage)

		# init controls
		self._mainControls = controls.MainControls("*.jpg *.png", self)
		self._imageControls = controls.ImageControls(self)
		self._navControls = controls.NavControls(self)
		self.setScene(self._mainScene)
		self.setMinimumSize(100, 100)
		self.setImageDirection(self._orientation)
		self._imageThread.start()
		self.resize(600, 500)

	def forward(self):
		"Show next image"
		self.requestNext.emit()

	def backward(self):
		"Show previous image"
		self.requestPrev.emit()

	def load(self, sources):
		"""
		params:
			sources - list of image paths
		"""
		assert isinstance(sources, list)
		for img in sources:
			self.loadImages.emit(img)

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


	def setImage(self, pixmap_list):
		""
		assert isinstance(pixmap_list, list)
		if pixmap_list:
			assert isinstance(pixmap_list[0], QPixmap)
			# calculate required rect

	def resizeEvent(self, ev):
		# center controls
		self._navControls.ensureEgdes()
		if self._orientation == Qt.Horizontal:
			self._mainControls.move(self.width()//2-self._mainControls.halfWidth, 0)
			self._imageControls.move(self.width()//2-self._imageControls.halfWidth,
							self.height()-self._imageControls.height()//2-self.horizontalScrollBar().height())
		else:
			self._mainControls.move(0, self.height()//2-self._mainControls.halfHeight)
			self._imageControls.move(self.width()-self._imageControls.width(),
						   self.height()//2-self._imageControls.halfHeight)

		return super().resizeEvent(ev)

if __name__ == '__main__':
	from PyQt5.QtWidgets import QApplication
	import os, sys

	app = QApplication(sys.argv)
	view = Happyview()
	view.setWindowTitle("Happyview")
	view.resize(1000, 600)
	view.show()

	sys.exit(app.exec())