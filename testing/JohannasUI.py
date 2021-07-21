import numpy as np
import os
import sys

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

import pyqtgraph as pg
from datetime import datetime
import Adafruit_ADS1x15 as adc

app = QApplication(sys.argv)


class button(QPushButton):
    def __init__(self, name):
        super(button, self).__init__()
        self.setText(name)

    def setButtonColor(self, color):
        self.setStyleSheet('background-color: {}'.format(color))

    def setButtonText(self, text):
        self.setText(text)


class graph(pg.PlotWidget):
     def __init__(self):
         super(graph, self).__init__()
         self.setStyleSheet("pg.PlotWidget {border-style: outset; max-height: 50}")

# class SpinBox(QSpinBox):
#     def __init__(self):
#         super(SpinBox, self).__init__()

class MOS:
	def __init__(self, adc, channel):
		super(MOS, self).__init__()
		self.GAIN = 2 / 3
		self.adc = adc
		self.channel = channel

	def read(self):
		return (self.adc.read_adc(self.channel, gain=self.GAIN) / pow(2, 15)) * 6.144

	def read_avg(self, val):
		self.val = 0
		for i in range(val):
			self.val += self.read()
		return self.val / val

class bubbles(QWidget):

    def __init__(self):
        super(bubbles, self).__init__()
        self.setWindowTitle("JohannasUI")
        self.loadWindowSettings()

        self.adc = adc.ADS1114(0x48)
        self.sensor1 = MOS(self.adc, 0)
        self.sensor2 = MOS(self.adc, 1)

        self.loadGraphSettings()

        self.b1 = button("Run")
        self.b1.clicked.connect(lambda: self.run())

        self.b2 = button("Stop")
        self.b2.clicked.connect(lambda: self.stop())

        self.b3 = button("Fill Box")
        self.b3.clicked.connect(lambda: self.fill())

        self.b4 = button("Pump To Exhaust")
        self.b4.clicked.connect(lambda: self.exhaust())

        self.b5 = button("Expose Sensor")
        self.b5.clicked.connect(lambda: self.sensor())

        self.b6 = button("Emergency Stop")
        self.b6.clicked.connect(lambda: self.EmergencyStop())

        self.spinBox1 = QSpinBox(self, value=10, maximum=100, minimum=0, singleStep=5, suffix="ppm")
        self.spinBox2 = QSpinBox(self, value=10, maximum=100, minimum=0, singleStep=5, suffix="ppm")

        self.flowGraphLabel = QLabel("MFC FLow Status")
        self.sensorGraphLabel = QLabel("Box Concentration Sensor")


        self.spinLabel1 = QLabel("Gas 1 Concentration", self)
        self.spinLabel2 = QLabel("Gas 2 Concentration", self)

        self.sensorReading = QLabel()
        self.sensor2Reading = QLabel()

        self.sensor1Reading.setText('Sensor 1 Concentration: \n{} ppm'.format(self.sensor1Array[-1]))
        self.sensor2Reading.setText('Sensor 2 Concentration: \n{} ppm'.format(self.sensor2Array[-1]))


        self.graphTimer = QTimer()
        self.graphTimer.timeout.connect(lambda: self.liveGraph())

        self.labelTimer = QTimer()
        self.labelTimer.timeout.connect(lambda: self.updateLabel())



        self.loadUI()

    def loadGraphSettings(self):
        self.sensorGraph = graph()
        self.flowGraph = graph()

        self.timeArray = list(range(200))
        self.sensor1Array = [0 for _ in range(200)]
        self.sensor2Array = [0 for _ in range(200)]
        self.flowArray = [0 for _ in range(200)]


        self.ydashed = pg.mkPen('y', width=2, style=QtCore.Qt.DotLine)
        self.chicken = pg.mkPen(color=(47, 209, 214), width=2)
        self.sensor1Plot = self.sensorGraph.plot(self.timeArray, self.sensor1Array, pen="r")
        self.sensor2Plot = self.sensorGraph.plot(self.timeArray, self.sensor2Array, pen=self.chicken)
        self.sensorGraph.setYRange(0, 100)
        self.flowPlot = self.flowGraph.plot(self.timeArray, self.flowArray, pen=self.chicken)
        self.flowGraph.setYRange(0, 100)

    def liveGraph(self):
        self.sensor1Array = self.sensor1Array[1:]
        self.sensor1Array.append(self.sensor1.read())

        self.sensor2Array = self.sensor2Array[1:]
        self.sensor2Array.append(self.sensor2.read())

        self.sensor1Plot.setData(self.timeArray, self.sensor1Array)
        self.sensor2Plot.setData(self.timeArray, self.sensor2Array)

        self.flowArray = self.flowArray[1:]
        self.flowArray.append(int(np.random.randint(1, 100, 1)))
        self.flowPlot.setData(self.timeArray, self.flowArray)

    def updateLabel(self):
        self.sensor1Reading.setText('Sensor 1 Concentration:\n{} ppm'.format(self.sensor1Array[-1]))
        self.sensor2Reading.setText('Sensor 2 Concentration:\n{} ppm'.format(self.sensor2Array[-1]))

    def loadUI(self):
        self.layout = QGridLayout()

        self.layout.addWidget(self.sensorGraph, 1, 0, 4, 3)
        self.layout.addWidget(self.flowGraph, 6, 0, 4, 3)
        self.layout.addWidget(self.b1)
        self.layout.addWidget(self.b2)
        self.layout.addWidget(self.b3, 6, 3,1, 1)
        self.layout.addWidget(self.b4, 6, 4, 1,1)
        self.layout.addWidget(self.b5, 7, 3, 1, 1)
        self.layout.addWidget(self.b6, 7, 4, 1, 1)
        self.layout.addWidget(self.spinBox1,1,4,1,1)
        self.layout.addWidget(self.spinBox2, 3,4,1,1)
        self.layout.addWidget(self.flowGraphLabel, 0,0,1,1)
        self.layout.addWidget(self.sensorGraphLabel, 5,0,1,1)


        self.layout.addWidget(self.spinLabel1, 1,3,1,1)
        self.layout.addWidget(self.spinLabel2,3,3,1,1)
        self.layout.addWidget(self.sensor1Reading, 8,3,1,1)
        self.layout.addWidget(self.sensor2Reading,9,3,1,1)


        self.setLayout(self.layout)

    def run(self):
        self.graphTimer.start(100)
        self.labelTimer.start(500)

    def stop(self):
        self.graphTimer.stop()
        self.labelTimer.stop()

    def fill(self):
        print("filling box")

    def exhaust(self):
        print("pumping to exhaust")

    def sensor(self):
        print("exposing sensor")

    def EmergencyStop(self):
        print("stopping")

    def loadWindowSettings(self):
        self.width = 700
        self.height = 520
        self.bg_color = '#484848'
        self.setStyleSheet('background-color: {}'.format(self.bg_color))
        self.setGeometry(0, 0, self.width, self.height)
        print("Window Settings Loaded")





def main():
    app = QApplication(sys.argv)
    window = bubbles()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
