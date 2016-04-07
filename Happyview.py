from enum import Enum

from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import (QBrush, QColor)
from PyQt5.QtWidgets import (QGraphicsView, QGraphicsScene)

import controls

class ReadingDirection(Enum):
	LeftToRight = 0
	RightToLeft = 1

class ImageList:
	"Represents and manages a list of images"

	def __init__(self, scene):
		self._scene = scene
		self._images = []
		self._currentIdx = 0

	@property
	def current(self):
		""
		pass

	def forward(self):
		""
		pass

	def backwards(self):
		""
		pass

	def addImage(self, img_path):
		pass

class Happyview(QGraphicsView):
	""

	def __init__(self):
		super().__init__()
		self._orientation = Qt.Horizontal # which way to go for the next image
		self._readingDirection = ReadingDirection.LeftToRight
		self._preloadCount = 3 # amount of images to load at a time
		self._backgroundColor = "#404244"
		self._backgroundBrush = QBrush(QColor(self._backgroundColor))

		self._mainScene = QGraphicsScene(self)
		self._mainScene.setBackgroundBrush(self._backgroundBrush)
		self._imageList = ImageList(self._mainScene)

		# init controls
		self._mainControls = controls.MainControls(self._mainScene, self)
		self._navControls = controls.NavControls(self)
		self.setScene(self._mainScene)
		self.setMinimumSize(100, 100)

	def forward(self):
		"Show next image"
		pass

	def backward(self):
		"Show previous image"
		pass

	def load(self, list_of_items):
		""
		pass

	def resizeEvent(self, ev):
		if self._orientation == Qt.Horizontal:
			sRect = QRectF(0, 0, 2000, ev.size().height())
		else:
			sRect = QRectF(0, 0, ev.size().width(), 2000)
		self._mainScene.setSceneRect(sRect)

		# center controls

		self._navControls.ensureEgdes()
		self._mainControls.move(self.width()*0.1, 0)

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