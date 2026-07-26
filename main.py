import sys, os, json
from PyQt5.QtWidgets import QMainWindow, QApplication, QMessageBox, QPushButton, QGraphicsDropShadowEffect, QDialog
from PyQt5 import uic, QtWidgets
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QSpacerItem, QSizePolicy, QTableWidgetItem, QHeaderView, QInputDialog
from PyQt5.QtCore import Qt, QSize, QTimer
from PyQt5.QtGui import QCursor, QColor, QIcon, QStandardItemModel, QStandardItem
from PyQt5.QtCore import pyqtSignal

import time
import pandas as pd
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt

from pathlib import Path
from datetime import datetime
import resources
from map_jamali import PetaGarduInduk

class loginpage(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("ui/login.ui", self)
        self.btn_gitet.clicked.connect(self.open_map)

    def open_map(self):
        print("Opening map...")
        self.map_window = PetaGarduInduk()
        self.map_window.show()

def main():
    app = QApplication(sys.argv)

    window = loginpage()

    window.show()
    app.exec()


if __name__ == "__main__":
    main()