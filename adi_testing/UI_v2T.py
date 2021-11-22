import numpy as np
import os
import sys
import math
import time
#import board
import busio
#why please please please

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

import pyqtgraph as pg

import RPi.GPIO as GPIO
import Adafruit_ADS1x15 as adc

#i2c = busio.I2C(board.SCL, board.SDA)


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


class sensor(QThread):
	mainSignal = pyqtSignal(object)

	def __init__(self, shift=None, adc1=None, channel=None):
		super(sensor, self).__init__()
		self.shift = shift

		self.adc1 = adc1
		self.channel = channel
		self.GAIN = 2 / 3

		self.signalArray = [0 for _ in range(200)]
		self.timer = QTimer()
		self.timer.timeout.connect(lambda: self.update())
		#self.loadADCSettings()
		self.counter = 0
		self.timer.start(10)

	def update(self):
		self.signalArray = self.signalArray[1:]
		#try:
		#self.signalArray.append(round(((self.adc1.read_adc(self.channel, gain=self.GAIN) / pow(2, 15)) * 6.144), 3))
		self.signalArray.append(self.sVal2PPM())
		#self.signalArray.append(self.signalArray[-1])

		self.mainSignal.emit(self.signalArray)

	def sVal2PPM(self):
		return ((self.adc1.read_adc(self.channel, gain=self.GAIN) / pow(2, 15)) * 6.144) #  * 100
		return ((self.adc1.read_adc(self.channel, gain=self.GAIN) / pow(2, 15)) * 6.144) #  * 100

	def startSensor(self):
		if not self.timer.isActive():
			self.timer.start(10)

	def stopSensor(self):
		if self.timer.isActive():
			self.timer.stop()

	def getAvg(self, val):
		self.val = 0
		for i in range(val):
			self.val += self.sVal2PPM()

		return self.val/val


class fillBox(QThread):
	doneFillSignal = pyqtSignal()

	def __init__(self, valve):
		super(fillBox, self).__init__()
		self.valve = valve
		self.rate = 5
		self.chamberVolume = 6.79423 * 1000  # L in cubic centimeters

	def conc2Time(self, value):
		'''
		THIS FUNCTION FOLLOWS THE FOLLOWING CALCULATION:
		60 (s/min) * desired value (ppm) * chamber volume (L *1000) (cc) / (flow rate (cc/min) * 10e5 (ppm/cc))
		probably something else

		:param value:
		:return:
		'''

		return 60 * value * self.chamberVolume / (10e5 * self.rate)

	def fill(self, value):
		self.time = self.conc2Time(value)
		print("\n{} sec".format(self.time))
		self.valve.enable()
		QTimer.singleShot(self.time*1000, lambda: self.endFill())

	def endFill(self):
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
		self.setBaseline()
		self.loadUI()

	def loadWindowSettings(self):
		self.width = 800
		self.height = 600
		self.bg_color = '#e3e1dc'
		self.setStyleSheet('background-color: {}'.format(self.bg_color))
		self.setGeometry(0, 0, self.width, self.height)
		print("Window Settings Loaded")

	def loadGraphSettings(self):
		self.graph = graph()

		self.timeArray = list(range(200))
		self.sensor1Array = [0 for _ in range(200)]
		self.sensor2Array = [0 for _ in range(200)]
		self.baselineArray = [0 for _ in range(200)]

		self.chicken = pg.mkPen(color=(47, 209, 214), width=2)
		self.redPanda = pg.mkPen(color=(127, 83, 181), width=2, style=QtCore.Qt.DotLine)
		self.sensor1Plot = self.graph.plot(self.timeArray, self.sensor1Array, pen=self.chicken)
		self.sensor2Plot = self.graph.plot(self.timeArray, self.sensor2Array, pen='r')
		self.baselinePlot = self.graph.plot(self.timeArray, self.baselineArray, pen=self.redPanda)

		self.graph.setYRange(0, 5)

		self.sensor1Label = QLabel()
		self.sensor2Label = QLabel()

	def loadComponents(self):
		self.adc1 = adc.ADS1115(0x48)
		self.adc2 = adc.ADS1115(0x49)
		self.v1 = valve(24)  #G1 (methanol)
		self.v2 = valve(22)  #G2 (ethane)
		self.v3 = valve(18)  #AIR
		self.v4 = valve(16)  #EXHAUST
		self.LEDButton1 = LEDButton(adc2=self.adc2,channel= 0)
		self.LEDButton2 = LEDButton(adc2=self.adc2,channel= 1)

		print(self.adc2.read_adc(channel=0, gain=1))
		if self.adc2.read_adc(channel=0, gain=1) > 15000:
			print("White button is pushed")
			self.v1.enable()
			# time.sleep(7)
			# self.v1.disable()
		else:
			print("White button is not pushed")
			self.v1.disable()

		# while self.adc2.read_adc(channel=0, gain=1) < 15000:
		# 	self.v1.enable()
		# else:
		# 	self.v1.disable()

		print(self.adc2.read_adc(channel=1, gain=1))
		if self.adc2.read_adc(channel=1, gain=1) < 15000:
			print("Red button is not pushed")
		else:
			print("Red button is pushed")

	def loadThread(self):
		self.sensor1Thread = QThread()
		self.sensor1 = sensor(adc1=self.adc1, channel=0)
		self.sensor1.moveToThread(self.sensor1Thread)
		self.sensor1.mainSignal.connect(self.update)
		self.sensor1Thread.start()

		self.sensor2Thread = QThread()
		self.sensor2 = sensor(adc1=self.adc1, channel=1)
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
		self.b4 = button("Gas 1 (m)")
		self.b5 = button("Gas 2 (e)")
		self.b6 = button("Air")
		self.b7 = button("Exhaust")
		self.b8 = button("Set Baseline")

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
		self.b8.clicked.connect(lambda: self.setBaseline())

		self.g1box = csSpinBox(max=3000)
		self.g2box = csSpinBox()

		self.g1L = QLabel("GAS 1 (m)")
		self.g2L = QLabel("GAS 2 (e)")

	def loadUI(self):
		self.layout = QGridLayout()

		self.layout.addWidget(self.graph, 0, 0, 3, 3)
		self.layout.addWidget(self.g1L, 3, 0, 1, 1)
		self.layout.addWidget(self.g2L, 3, 1, 1, 1)
		self.layout.addWidget(self.sensor1Label, 1, 3, 1, 1)
		self.layout.addWidget(self.sensor2Label, 2, 3, 1, 1)
		self.layout.addWidget(self.g1box, 4, 0, 1, 1)
		self.layout.addWidget(self.g2box, 4, 1, 1, 1)
		self.layout.addWidget(self.b1, 5, 0, 1, 1)
		self.layout.addWidget(self.b2, 5, 1, 1, 1)
		self.layout.addWidget(self.b3, 5, 2, 1, 1)
		self.layout.addWidget(self.b4, 4, 3, 1, 1)
		self.layout.addWidget(self.b5, 4, 4, 1, 1)
		self.layout.addWidget(self.b6, 5, 3, 1, 1)
		self.layout.addWidget(self.b7, 5, 4, 1, 1)
		self.layout.addWidget(self.b8, 4, 2, 1, 1)


		self.setLayout(self.layout)

	@pyqtSlot(object)
	def update(self, sensArray):
		self.sensor1Plot.setData(self.timeArray, sensArray)
		self.sensor1Label.setText("Sensor 1 Average: {:.3f}".format(np.mean(sensArray)))


	@pyqtSlot(object)
	def update2(self, sensArray):
		self.sensor2Plot.setData(self.timeArray, sensArray)
		self.sensor2Label.setText("Sensor 2 Average: {:.3f}".format(np.mean(sensArray)))

	def setBaseline(self):
		self.mergedVal = (self.sensor1.getAvg(5) + self.sensor2.getAvg(5))/2
		self.baselineArray = [self.mergedVal for _ in range(200)]
		self.baselinePlot.setData(self.timeArray, self.baselineArray)

	def fill(self):
		self.g1Val = self.g1box.value()
		self.g2Val = self.g2box.value()
		self.fillBox_v1.fill(self.g1Val)
		self.fillBox_v2.fill(self.g2Val)

	@pyqtSlot()
	def fill_g1(self):
		print("Done Filling G1")

	@pyqtSlot()
	def fill_g2(self):
		print("Done Filling G2")

	def stop(self):
		self.v1.disable()
		self.v2.disable()
		self.v3.disable()
		self.v4.disable()

	def vent(self):
		self.v3.enable()
		self.v4.enable()
		print("Starting Venting")
		QTimer.singleShot(100000, lambda: self.ventOff())

	def ventOff(self):
		self.v3.disable()
		self.v4.disable()
		print("Venting Done")

class LEDButton:

	def __init__(self, shift=None, adc2=None, channel=None):
		super(LEDButton, self).__init__()
		self.shift = shift

		self.adc2 = adc2
		self.channel = channel
		self.gain = 1

def main():
	window = mainWindow()
	window.show()
	sys.exit(app.exec_())
	GPIO.cleanup()


if __name__ == "__main__":
	main()
