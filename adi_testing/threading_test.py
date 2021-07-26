import numpy as np
import os
import sys
import math

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

import pyqtgraph as pg

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


class sensor(QObject):
    mainSignal = pyqtSignal(object)

    def __init__(self, shift):
        super(sensor, self).__init__()
        self.shift = shift
        self.signalArray = [0 for _ in range(200)]
        self.counter = 0
        self.timer = QTimer()
        self.timer.timeout.connect(lambda: self.update())
        self.timer.start(100)

    def update(self):
        self.signalArray = self.signalArray[1:]
        self.signalArray.append(math.sin(self.counter + self.shift))
        self.mainSignal.emit(self.signalArray)
        self.counter += 0.1

    def startSensor(self):
        if not self.timer.isActive():
            self.timer.start(100)

    def stopSensor(self):
        if self.timer.isActive():
            self.timer.stop()


    # def run(self):
    #     self.timer.start(100)


class simpleWindow(QWidget):
    def __init__(self):
        super(simpleWindow, self).__init__()
        self.loadWindowSettings()
        self.loadGraph()
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

    def loadButtons(self):
        self.b1 = button("Start")
        self.b2 = button("Stop")

        self.b1.clicked.connect(lambda: self.startGraph())
        self.b2.clicked.connect(lambda: self.stopGraph())

    def startGraph(self):
        self.sensor1.startSensor()
        self.sensor2.startSensor()

    def stopGraph(self):
        self.sensor1.stopSensor()
        self.sensor2.stopSensor()

    def loadGraph(self):
        self.sensorGraph = graph()

        self.timeArray = list(range(200))
        self.sensor1Array = [0 for _ in range(200)]
        self.sensor2Array = [0 for _ in range(200)]
        self.chicken = pg.mkPen(color=(47, 209, 214), width=2)
        self.sensor1Plot = self.sensorGraph.plot(self.timeArray, self.sensor1Array, pen=self.chicken)
        self.sensor2Plot = self.sensorGraph.plot(self.timeArray, self.sensor2Array, pen='r')

    @pyqtSlot(object)
    def update(self, sensArray):
        self.sensor1Plot.setData(self.timeArray, sensArray)

    @pyqtSlot(object)
    def update2(self, sensArray):
        self.sensor2Plot.setData(self.timeArray, sensArray)

    def loadUI(self):
        self.layout = QGridLayout()
        self.layout.addWidget(self.sensorGraph, 0, 0, 5, 5)
        self.layout.addWidget(self.b1, 5, 0, 1, 1)
        self.layout.addWidget(self.b2, 5, 1, 1, 1)
        self.setLayout(self.layout)


def main():
    A = simpleWindow()
    A.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()


