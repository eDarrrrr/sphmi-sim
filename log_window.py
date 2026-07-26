from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView, QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QBrush, QColor, QPainterPath, QPen, QPolygonF, QCursor
from PyQt5.QtCore import QPointF, Qt, QTimer
import sys

class LogWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Data Logger")
        self.resize(900, 600)
        
        # Desain dasar tema gelap
        self.setStyleSheet("""
            QWidget { background-color: #1e1e1e; color: white; font-family: Consolas; }
            QTableWidget { background-color: #2b2b2b; gridline-color: #555555; }
            QHeaderView::section { background-color: #333333; padding: 4px; border: 1px solid #555; }
        """)

        layout = QVBoxLayout(self)

        # 1. BIKIN TAB WIDGET (Ala Google Chrome)
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabBar::tab { background: #333; color: white; padding: 10px 20px; border-top-left-radius: 4px; border-top-right-radius: 4px; }
            QTabBar::tab:selected { background: #0078d7; font-weight: bold; }
        """)
        layout.addWidget(self.tabs)

        # ==========================================
        # TAB 1: DATA TERJEMAHAN (Human Readable)
        # ==========================================
        self.tab_human = QWidget()
        layout_human = QVBoxLayout(self.tab_human)
        
        self.table_human = QTableWidget(0, 3) # 0 Baris, 3 Kolom
        self.table_human.setHorizontalHeaderLabels(["Waktu (Timestamp)", "Alamat IOA (Hex)", "Nilai Sensor"])
        self.table_human.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout_human.addWidget(self.table_human)
        
        self.tabs.addTab(self.tab_human, "Processed Data")

        # ==========================================
        # TAB 2: DATA MENTAH (Raw Hex)
        # ==========================================
        self.tab_raw = QWidget()
        layout_raw = QVBoxLayout(self.tab_raw)
        
        self.table_raw = QTableWidget(0, 3) # 0 Baris, 3 Kolom
        self.table_raw.setHorizontalHeaderLabels(["Waktu (Timestamp)", "Tx / Rx", "Data Heksadesimal"])
        # Kolom Hex dibuat menyesuaikan isi agar tidak terpotong
        self.table_raw.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents) 
        layout_raw.addWidget(self.table_raw)
        
        self.tabs.addTab(self.tab_raw, "HEX Data")


    # ==========================================
    # FUNGSI UNTUK MENAMBAH BARIS KE TABEL
    # ==========================================
    def tambah_log_human(self, waktu, ioa, nilai):
        row = self.table_human.rowCount()
        self.table_human.insertRow(row)
        self.table_human.setItem(row, 0, QTableWidgetItem(waktu))
        self.table_human.setItem(row, 1, QTableWidgetItem(f"0x{ioa:06X}"))
        self.table_human.setItem(row, 2, QTableWidgetItem(str(nilai)))
        
        self.table_human.scrollToBottom() # Otomatis scroll ke bawah

    def tambah_log_raw(self, waktu, arah, hex_data):
        row = self.table_raw.rowCount()
        self.table_raw.insertRow(row)
        
        item_arah = QTableWidgetItem(arah)
        # Bikin teks Tx warna biru, Rx warna hijau biar gampang dibaca
        if arah == "Tx":
            item_arah.setForeground(QBrush(QColor("#00aaff")))
        else:
            item_arah.setForeground(QBrush(QColor("#00ff00")))

        self.table_raw.setItem(row, 0, QTableWidgetItem(waktu))
        self.table_raw.setItem(row, 1, item_arah)
        self.table_raw.setItem(row, 2, QTableWidgetItem(hex_data))
        
        self.table_raw.scrollToBottom()

if __name__ == '__main__':
    QApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
    app = QApplication(sys.argv)
    window = LogWindow()
    window.show()
    
    sys.exit(app.exec_())