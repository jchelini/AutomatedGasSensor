import numpy as np
import os
import sys
import math
import time

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

import pyqtgraph as pg

import RPi.GPIO as GPIO

app = QApplication(sys.argv)
GPIO.setmode(GPIO.BOARD)

class valve:
	def __init__(self, pin):
		self.pin = pin
		GPIO.setup(self.pin, GPIO.OUT)
		GPIO.output(self.pin, GPIO.LOW)

	def enable(self):
		GPIO.output(self.pin, GPIO.HIGH)

	def disable(self):
		GPIO.output(self.pin, GPIO.LOW)


class button(QPushButton):
	def __init__(self, name):
		super(button, self).__init__()
		self.setText(name)

	def setButtonColor(self, color):
		self.setStyleSheet('background-color: {}'.format(color))

	def setButtonText(self, text):
		self.setText(text)


class csSpinBox(QSpinBox):
	def __init__(self, value=0, max=1000, min=0, step=10, suffix="ppm"):
		super(csSpinBox, self).__init__()
		self.setValue(value)
		self.setRange(min, max)
		self.setSingleStep(step)
		self.setSuffix(suffix)


class graph(pg.PlotWidget):
	def __init__(self):
		super(graph, self).__init__()
		self.setStyleSheet("pg.PlotWidget {border-style: outset; max-height: 50}")


class sensor(QObject):
	mainSignal = pyqtSignal(object)

	def __init__(self, shift=None, adc=None, channel=None):
		super(sensor, self).__init__()
		self.shift = shift

		self.adc = adc
		self.channel = channel
		self.GAIN = 2 / 3

		self.signalArray = [0 for _ in range(200)]
		self.timer = QTimer()
		self.timer.timeout.connect(lambda: self.update())
		#self.loadADCSettings()
		self.counter = 0
		self.timer.start(1)

	# def updateTest(self):
	# 	self.signalArray = self.signalArray[1:]
	# 	try:
	# 		self.signalArray.append(math.sin(self.counter + self.shift))
	# 	except:
	# 		self.signalArray.append(self.signalArray[-1])
	# 	self.mainSignal.emit(self.signalArray)
	# 	self.counter += 0.01

	def update(self):
		self.signalArray = self.signalArray[1:]
		try:
			self.signalArray.append(round((self.adc.read_adc(self.channel, gain=self.GAIN) / pow(2, 15)) * 6.144), 3)
		except:
			self.signalArray.append(self.signalArray[-1])

		self.mainSignal.emit(self.signalArray)

	def startSensor(self):
		if not self.timer.isActive():
			self.timer.start(100)

	def stopSensor(self):
		if self.timer.isActive():
			self.timer.stop()


class fillBox(QObject):
	doneFillSignal = pyqtSignal()

	def __init__(self, valve):
		super(fillBox, self).__init__()
		self.valve = valve
		self.rate = 30
		self.chamberVolume = 2.5 * 1000  # L in cubic centimeters


	def conc2Time(self, value):
		return 2 * value * self.chamberVolume / 10e6

	def fill(self, value):
		self.time = self.conc2Time(value)
		self.valve.enable()
		time.sleep(self.time)
		self.valve.disable()
		self.doneFillSignal.emit()


class mainWindow(QWidget):
	def __init__(self):
		super(mainWindow, self).__init__()
		self.loadWindowSettings()
		self.loadGraphSettings()
		self.loadComponents()
		self.loadThread()
		self.loadButtons()
		self.loadUI()

	def loadWindowSettings(self):
		self.width = 700
		self.height = 520
		self.bg_color = '#e3e1dc'
		self.setStyleSheet('background-color: {}'.format(self.bg_color))
		self.setGeometry(0, 0, self.width, self.height)
		print("Window Settings Loaded")

	def loadGraphSettings(self):
		self.graph = graph()

		self.timeArray = list(range(200))
		self.sensor1Array = [0 for _ in range(200)]
		self.sensor2Array = [0 for _ in range(200)]

		self.chicken = pg.mkPen(color=(47, 209, 214), width=2)
		self.sensor1Plot = self.graph.plot(self.timeArray, self.sensor1Array, pen=self.chicken)
		self.sensor2Plot = self.graph.plot(self.timeArray, self.sensor2Array, pen='r')

		self.graph.setYRange(-1.5, 1.5)

	def loadComponents(self):
		# self.adc = adc.ADS1115(0x48)
		self.v1 = valve(16)  #G1
		self.v2 = valve(18)  #G2
		self.v3 = valve(22)  #AIR
		self.v4 = valve(24)  #EXHAUST

	def loadThread(self):
		self.sensor1Thread = QThread()
		self.sensor1 = sensor(0.1)
		self.sensor1.moveToThread(self.sensor1Thread)
		self.sensor1.mainSignal.connect(self.update)
		self.sensor1Thread.start()

		self.sensor2Thread = QThread()
		self.sensor2 = sensor(1)
		self.sensor2.moveToThread(self.sensor1Thread)
		self.sensor2.mainSignal.connect(self.update2)
		self.sensor2Thread.start()

		self.fillBox_v1 = fillBox(self.v1)
		self.fillBox_v2 = fillBox(self.v2)

		self.G1Thread = QThread()
		self.G2Thread = QThread()
		self.fillBox_v1.moveToThread(self.G1Thread)
		self.fillBox_v2.moveToThread(self.G2Thread)
		self.fillBox_v1.doneFillSignal.connect(self.fill_g1)
		self.fillBox_v2.doneFillSignal.connect(self.fill_g2)


	def loadButtons(self):
		self.b1 = button("Fill")
		self.b2 = button("Vent")
		self.b3 = button ("Stop")
		self.b4 = button("Gas 1")
		self.b5 = button("Gas 2")
		self.b6 = button("Air")
		self.b7 = button("Exhaust")

		self.b1.clicked.connect(lambda: self.fill())
		self.b2.clicked.connect(lambda: self.vent())
		self.b3.clicked.connect(lambda: self.stop())
		self.b4.pressed.connect(lambda: self.v1.enable())
		self.b4.released.connect(lambda: self.v1.disable())
		self.b5.pressed.connect(lambda: self.v2.enable())
		self.b5.released.connect(lambda: self.v2.disable())
		self.b6.pressed.connect(lambda: self.v3.enable())
		self.b6.released.connect(lambda: self.v3.disable())
		self.b7.pressed.connect(lambda: self.v4.enable())
		self.b7.released.connect(lambda: self.v4.disable())

		self.g1box = csSpinBox()
		self.g2box = csSpinBox()

	def loadUI(self):
		self.layout = QGridLayout()

		self.layout.addWidget(self.graph, 0, 0, 3, 3)
		self.layout.addWidget(self.g1box, 4, 0, 1, 1)
		self.layout.addWidget(self.g2box, 4, 1, 1, 1)
		self.layout.addWidget(self.b1, 5, 0, 1, 1)
		self.layout.addWidget(self.b2, 5, 1, 1, 1)
		self.layout.addWidget(self.b3, 5, 2, 1, 1)
		self.layout.addWidget(self.b4, 4, 4, 1, 1)
		self.layout.addWidget(self.b5, 4, 5, 1, 1)
		self.layout.addWidget(self.b6, 5, 4, 1, 1)
		self.layout.addWidget(self.b7, 5, 5, 1, 1)

		self.setLayout(self.layout)

	@pyqtSlot(object)
	def update(self, sensArray):
		self.sensor1Plot.setData(self.timeArray, sensArray)

	@pyqtSlot(object)
	def update2(self, sensArray):
		self.sensor2Plot.setData(self.timeArray, sensArray)

	def fill(self):
		self.g1Val = self.g1box.value()
		self.g2Val = self.g2box.value()
		self.fillBox_v1.fill(self.g1Val)
		self.fillBox_v2.fill(self.g2Val)

	@pyqtSlot()
	def fill_g1(self):
		print("Done Filling G1")

	@pyqtSlot()
	def fill_g2(self, value):
		print("Done Filling G2")

	def stop(self):
		self.v1.disable()
		self.v2.disable()
		self.v3.disable()
		self.v4.disable()

	def vent(self):
		self.v3.enable()


def main():
	window = mainWindow()
	window.show()
	sys.exit(app.exec_())
	GPIO.cleanup()


if __name__ == "__main__":
	main()
