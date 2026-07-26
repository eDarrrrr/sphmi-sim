import sys
from PyQt5.QtWidgets import (QApplication, QGraphicsEllipseItem, QMainWindow, QGraphicsView, 
                             QGraphicsScene, QFrame, QLabel, QVBoxLayout, QPushButton, QGridLayout,
                             QGraphicsTextItem, QMenu)
from PyQt5.QtGui import QBrush, QColor, QPainterPath, QPen, QPolygonF, QCursor
from PyQt5.QtCore import QPointF, Qt, QTimer
from master_node_withoutesp import IecMasterThread
from log_window import LogWindow

class ClickableTextItem(QGraphicsTextItem):
    def __init__(self, text, callback=None):
        super().__init__(text)
        self.callback = callback 

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            if self.callback:

                self.callback(self) 
                
        super().mousePressEvent(event)

class ZoomableView(QGraphicsView):
    def __init__(self, scene):
        super().__init__(scene)
        
        # Pengaturan dasar yang Anda miliki sebelumnya dipindah ke sini
        self.setDragMode(QGraphicsView.ScrollHandDrag) 
        self.setStyleSheet("background-color: #0c0c0c; border: none;")
        
        # [FITUR PENTING] Ini membuat zoom terfokus tepat ke arah kursor mouse Anda!
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)

    def wheelEvent(self, event):
        # Tentukan persentase seberapa cepat/besar zoomnya (1.15 = 15% per putaran)
        zoom_in_factor = 1.15
        zoom_out_factor = 1 / zoom_in_factor

        # Cek apakah roda mouse diputar ke depan (Zoom In) atau ke belakang (Zoom Out)
        if event.angleDelta().y() > 0:
            zoom_factor = zoom_in_factor
        else:
            zoom_factor = zoom_out_factor

        # Eksekusi perbesaran/pengecilan kanvas
        self.scale(zoom_factor, zoom_factor)

class ScadaMapWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        global scene
        # Pengaturan Jendela Utama
        self.setWindowTitle("PROCESS REAL MAP")
        self.setGeometry(275, 200, 2000, 1200)
        
        self.status = "Not Connected"

        self.jendela_log = LogWindow()

        self.master_thread = IecMasterThread()
        self.master_thread.data_received.connect(self.update_telemetri)

        self.master_thread.log_human_signal.connect(self.jendela_log.tambah_log_human)
        self.master_thread.log_raw_signal.connect(self.jendela_log.tambah_log_raw)

        # self.jendela_log.show()
        
        self.master_thread.start()

        self.watchdog_timer = QTimer()
        self.watchdog_timer.setInterval(5000)           # 2 detik
        self.watchdog_timer.timeout.connect(self.koneksi_putus)

        # 1. MEMBUAT DUNIA PETA (QGraphicsScene)
        # Menentukan seberapa luas peta Anda (X, Y, Lebar, Tinggi)
        self.scene = QGraphicsScene(-2000, -2000, 10000, 10000)
        scene = self.scene  # Agar bisa diakses oleh ScadaShapesBuilder

        pen_putus = QPen(Qt.white, 2, Qt.DashLine) # Garis kuning putus-putus
        self.kotak_highlight = self.scene.addRect(0, 0, 10, 10, pen_putus, QBrush(Qt.transparent))
        self.kotak_highlight.hide()

        # 2. MEMBUAT KACA KAMERA PETA (QGraphicsView)
        self.view = ZoomableView(self.scene)
        
        # Memasang view ini ke tengah jendela utama
        self.setCentralWidget(self.view)

        # 3. MEMBUAT PANEL INFORMASI (UI murni dengan Python)
        self.info_panel = QFrame()
        self.info_panel.setFixedSize(600, 200) # Ukuran panel (Lebar x Tinggi)
        
        # Desain panel: Background hitam transparan, kotak membulat (border-radius)
        self.info_panel.setStyleSheet("""
            QFrame {
                background-color: rgba(0, 0, 255, 255);
                border: 2px solid rgba(0, 0, 255, 200);
                border-radius: 0px;
            }
            QLabel {
                color: white;
                font-family: Consolas;
                font-size: 14px;
                border: none;
                background: transparent;
            }
        """)
        
        self.btn_eksekusi = QPushButton("GITET")
        
        # Desain tombol agar cocok dengan tema gelap (Hover & Pressed effect)
        self.btn_eksekusi.setStyleSheet("""
            QPushButton {
                background-color: #2a2a2a;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 6px;
                padding: 8px;
                font-family: Consolas;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #444444; /* Berubah abu-abu saat mouse lewat */
            }
            QPushButton:pressed {
                background-color: #cc0000; /* Berubah merah saat diklik */
            }
        """)

        cell_style = """
            QLabel {
                color: white;
                font-family: Consolas;
                font-size: 14px;
                border: 1px solid #444444;
                background: transparent;
            }
        """

        self.btn_TRACE = QPushButton("TRACE")
        self.btn_TRACE.setStyleSheet("""
            QPushButton {
                background-color: #2a2a2a;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 6px;
                padding: 8px;
                font-family: Consolas;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #444444; /* Berubah abu-abu saat mouse lewat */
            }
            QPushButton:pressed {
                background-color: #cc0000; /* Berubah merah saat diklik */
            }
        """)


        # Mengisi Panel dengan Layout vertikal (Susun ke bawah)
        layout = QVBoxLayout(self.info_panel)
        
        # Membuat tulisan-tulisannya
        title = QLabel("INDRAMAYU 500kV")
        title.setStyleSheet(" font-size: 40px; color: #5fcce2; background: black")
        title.setAlignment(Qt.AlignCenter)

        self.grid = QGridLayout()
        self.grid.setHorizontalSpacing(5)
        self.grid.setVerticalSpacing(5)

        self.grid2 = QGridLayout()
        self.grid2.setHorizontalSpacing(5)
        self.grid2.setVerticalSpacing(5)

        self.poll = QLabel("🟦IN POLL")
        self.service = QLabel("🟦IN SERVICE")
        self.poll.setStyleSheet(cell_style)
        self.service.setStyleSheet(cell_style)

        self.statusconnect = QLabel("Not Connected")
        self.statusconnect.setStyleSheet("font-weight: bold; font-size: 18px; color: #ffffff;")
        self.statusconnect.setAlignment(Qt.AlignLeft)
        self.poll.setText("🟥OUT OF POLL")

        # Memasukkan tulisan ke dalam layout panel
        layout.addWidget(title)
        layout.addSpacing(5) # Jarak pemisah
        layout.addLayout(self.grid2)
        self.btn_eksekusi.clicked.connect(self.openingGITET)
        self.btn_TRACE.clicked.connect(lambda: self.jendela_log.show())
        self.grid2.addWidget(self.btn_eksekusi, 0, 0)
        self.grid2.addWidget(self.btn_TRACE, 0, 1)
        layout.addLayout(self.grid)
        self.grid.addWidget(self.poll, 0, 2) #
        self.grid.addWidget(self.service, 1, 2)
        layout.addWidget(self.statusconnect)
        layout.addStretch() # Mendorong teks agar rapi ke atas


        # 4. MENANAMKAN PANEL KE DALAM PETA
        # Ini yang membuat panel ikut tergeser saat peta ditarik
        self.proxy_panel = self.scene.addWidget(self.info_panel)
        
        # Letakkan panel di koordinat tertentu (misal di samping lingkaran biru)
        self.proxy_panel.setPos(100, -350)


        # ================================ BAGIAN SINGLE LINE DIAGRAM 
        self.deltamas1TEXT = self.scene.addText("DELTAMAS 1")
        self.deltamas1TEXT.setDefaultTextColor(QColor("white"))
        self.deltamas1TEXT.setPos(-50, -50)

        # ================= bagian sebelah kiri
        self.pwrDeltamas1 = self.scene.addPolygon(QPolygonF([QPointF(0, -14), QPointF(10, 6), QPointF(-10, 6)]), QPen(Qt.transparent), QBrush(QColor("aqua")))
        # self.kotak_cb = self.scene.addRect(-1, -1, 2, 2, QPen(Qt.transparent), QBrush(QColor("red")))

        self.deltmsTOcb1 = self.scene.addLine(0, 0, 0, 100, QPen(QColor("aqua"), 4))

        self.cb1 = self.scene.addRect(-25, 100, 50, 50, QPen(Qt.transparent), QBrush(QColor("aqua")))

        self.cb1TOdiameter1and3 = self.buat_kabel_belok([(0, 150), (0, 600), (-200, 600), (-200, 200)])

        self.diameter1pms1 = self.scene.addPolygon(QPolygonF([QPointF(-200, 550), QPointF(-200-35, 550-35), QPointF(-200, 550-70), QPointF(-200+35, 550-35)]), QPen(Qt.transparent), QBrush(QColor("aqua")))
        self.diameter1cb = self.scene.addRect(-225, 460, 50, -50, QPen(Qt.transparent), QBrush(QColor("aqua")))
        self.diameter1pms2 = self.scene.addPolygon(QPolygonF([QPointF(-200, 390), QPointF(-200-35, 390-35), QPointF(-200, 390-70), QPointF(-200+35, 390-35)]), QPen(Qt.transparent), QBrush(QColor("aqua")))

        self.diameter3to5 = self.buat_kabel_belok([(-200, 600), (-200, 930)])

        self.diameter3pms1 = self.scene.addPolygon(QPolygonF([QPointF(-200, 650), QPointF(-200-35, 650+35), QPointF(-200, 650+70), QPointF(-200+35, 650+35)]), QPen(Qt.transparent), QBrush(QColor("aqua")))
        self.diameter3cb = self.scene.addRect(-225, 740, 50, 50, QPen(Qt.transparent), QBrush(QColor("aqua")))
        self.diameter3pms2 = self.scene.addPolygon(QPolygonF([QPointF(-200, 810), QPointF(-200-35, 810+35), QPointF(-200, 810+70), QPointF(-200+35, 810+35)]), QPen(Qt.transparent), QBrush(QColor("aqua")))

        self.diameter3and5TOcb3 = self.buat_kabel_belok([(-200, 1330), (-200, 930), (0, 930), (0, 1380)])

        self.diameter5pms1 = self.scene.addPolygon(QPolygonF([QPointF(-200, 980), QPointF(-200-35, 980+35), QPointF(-200, 980+70), QPointF(-200+35, 980+35)]), QPen(Qt.transparent), QBrush(QColor("aqua")))
        self.diameter5cb = self.scene.addRect(-225, 1070, 50, 50, QPen(Qt.transparent), QBrush(QColor("aqua")))
        self.diameter5pms2 = self.scene.addPolygon(QPolygonF([QPointF(-200, 1140), QPointF(-200-35, 1140+35), QPointF(-200, 1140+70), QPointF(-200+35, 1140+35)]), QPen(Qt.transparent), QBrush(QColor("aqua")))


        self.cb3 = self.scene.addRect(-25, 1380, 50, 50, QPen(Qt.transparent), QBrush(QColor("aqua")))
        self.cb3tomandirancan1 = self.buat_kabel_belok([(0, 1430), (0, 1530)])

        self.pwrMandirancan1 = self.scene.addPolygon(QPolygonF([QPointF(0, 1550), QPointF(10, 1530), QPointF(-10, 1530)]), QPen(Qt.transparent), QBrush(QColor("aqua")))
        
        self.mandirancan1TEXT = self.scene.addText("MANDIRANCAN 1")
        self.mandirancan1TEXT.setDefaultTextColor(QColor("white"))
        self.mandirancan1TEXT.setPos(-62, 1550)

        # ================ sebelah kanan

        self.deltamas2TEXT = self.scene.addText("DELTAMAS 2")
        self.deltamas2TEXT.setDefaultTextColor(QColor("white"))
        self.deltamas2TEXT.setPos(-50+800, -50)

        self.pwrDeltamas2 = self.scene.addPolygon(QPolygonF([QPointF(0+800, -14), QPointF(10+800, 6), QPointF(-10+800, 6)]), QPen(Qt.transparent), QBrush(QColor("aqua")))
        # self.kotak_cb = self.scene.addRect(-1, -1, 2, 2, QPen(Qt.transparent), QBrush(QColor("red")))

        self.deltms2TOcb2 = self.scene.addLine(800, 0, 800, 100, QPen(QColor("aqua"), 4))

        self.cb2 = self.scene.addRect(-25+800, 100, 50, 50, QPen(Qt.transparent), QBrush(QColor("aqua")))

        self.cb2TOdiameter2and3 = self.buat_kabel_belok([(800, 150), (800, 600), (-200+800, 600), (-200+800, 200)])

        self.diameter2pms1 = self.scene.addPolygon(QPolygonF([QPointF(-200+800, 550), QPointF(-200-35+800, 550-35), QPointF(-200+800, 550-70), QPointF(-200+35+800, 550-35)]), QPen(Qt.transparent), QBrush(QColor("aqua")))
        self.diameter2cb = self.scene.addRect(-225+800, 460, 50, -50, QPen(Qt.transparent), QBrush(QColor("aqua")))
        self.diameter2pms2 = self.scene.addPolygon(QPolygonF([QPointF(-200+800, 390), QPointF(-200-35+800, 390-35), QPointF(-200+800, 390-70), QPointF(-200+35+800, 390-35)]), QPen(Qt.transparent), QBrush(QColor("aqua")))

        self.diameter4to5 = self.buat_kabel_belok([(-200+800, 600), (-200+800, 930)])

        self.diameter4pms1 = self.scene.addPolygon(QPolygonF([QPointF(-200+800, 650), QPointF(-200-35+800, 650+35), QPointF(-200+800, 650+70), QPointF(-200+35+800, 650+35)]), QPen(Qt.transparent), QBrush(QColor("aqua")))
        self.diameter4cb = self.scene.addRect(-225+800, 740, 50, 50, QPen(Qt.transparent), QBrush(QColor("aqua")))
        self.diameter4pms2 = self.scene.addPolygon(QPolygonF([QPointF(-200+800, 810), QPointF(-200-35+800, 810+35), QPointF(-200+800, 810+70), QPointF(-200+35+800, 810+35)]), QPen(Qt.transparent), QBrush(QColor("aqua")))

        self.diameter4and6TOcb4 = self.buat_kabel_belok([(-200+800, 1330), (-200+800, 930), (0+800, 930), (0+800, 1380)])

        self.diameter6pms1 = self.scene.addPolygon(QPolygonF([QPointF(-200+800, 980), QPointF(-200-35+800, 980+35), QPointF(-200+800, 980+70), QPointF(-200+35+800, 980+35)]), QPen(Qt.transparent), QBrush(QColor("aqua")))
        self.diameter6cb = self.scene.addRect(-225+800, 1070, 50, 50, QPen(Qt.transparent), QBrush(QColor("aqua")))
        self.diameter6pms2 = self.scene.addPolygon(QPolygonF([QPointF(-200+800, 1140), QPointF(-200-35+800, 1140+35), QPointF(-200+800, 1140+70), QPointF(-200+35+800, 1140+35)]), QPen(Qt.transparent), QBrush(QColor("aqua")))
        self.cb4 = self.scene.addRect(-25+800, 1380, 50, 50, QPen(Qt.transparent), QBrush(QColor("aqua")))
        self.cb4tomandirancan2 = self.buat_kabel_belok([(800, 1430), (800, 1530)])

        self.pwrMandirancan1 = self.scene.addPolygon(QPolygonF([QPointF(800, 1550), QPointF(10+800, 1530), QPointF(-10+800, 1530)]), QPen(Qt.transparent), QBrush(QColor("aqua")))
        
        self.bus2_shadow = self.scene.addLine(-500, 1330, 1250, 1330, QPen(QColor("black"), 15))
        self.bus2 = self.scene.addLine(-500, 1330, 1250, 1330, QPen(QColor("aqua"), 8))

        self.bus1_shadow = self.scene.addLine(-500, 200, 1250, 200, QPen(QColor("black"), 15))
        self.bus1 = self.scene.addLine(-500, 200, 1250, 200, QPen(QColor("aqua"), 8))

        self.mandirancan1TEXT = self.scene.addText("MANDIRANCAN 2")
        self.mandirancan1TEXT.setDefaultTextColor(QColor("white"))
        self.mandirancan1TEXT.setPos(-62+800, 1550)

        # TEXT HASIL NYA

        # DELTAMAS 1
        self.dayadeltamas1        = self.buat_teks_klik("0", -125, 25, "Deltamas 1 - Daya Aktif (MW)", "000011")
        self.dayaReaktifdeltamas1 = self.buat_teks_klik("0", -125, 50, "Deltamas 1 - Daya Reaktif", "000012")
        self.voltagedeltamas1     = self.buat_teks_klik("0", -125, 75, "Deltamas 1 - Tegangan (kV)", "000013")
        self.arusdeltamas1        = self.buat_teks_klik("0", -125, 100, "Deltamas 1 - Arus (A)", "000014")

        # DELTAMAS 2
        self.dayadeltamas2        = self.buat_teks_klik("0", -125+800, 25, "Deltamas 2 - Daya Aktif (MW)", "000021")
        self.dayaReaktifdeltamas2 = self.buat_teks_klik("0", -125+800, 50, "Deltamas 2 - Daya Reaktif", "000022")
        self.voltagedeltamas2     = self.buat_teks_klik("0", -125+800, 75, "Deltamas 2 - Tegangan (kV)", "000023")
        self.arusdeltamas2        = self.buat_teks_klik("0", -125+800, 100, "Deltamas 2 - Arus (A)", "000024")

        # MANDIRANCAN 1
        self.dayamandarican1        = self.buat_teks_klik("0", -125, 1550-150, "Mandirancan 1 - Daya Aktif (MW)", "000031")
        self.dayaReaktifmandarican1 = self.buat_teks_klik("0", -125, 1575-150, "Mandirancan 1 - Daya Reaktif", "000032")
        self.voltagemandarican1     = self.buat_teks_klik("0", -125, 1600-150, "Mandirancan 1 - Tegangan (kV)", "000033")
        self.arusmandarican1        = self.buat_teks_klik("0", -125, 1625-150, "Mandirancan 1 - Arus (A)", "000034")

        # MANDIRANCAN 2
        self.dayamandarican2        = self.buat_teks_klik("0", -125+800, 1550-150, "Mandirancan 2 - Daya Aktif (MW)", "000041")
        self.dayaReaktifmandarican2 = self.buat_teks_klik("0", -125+800, 1575-150, "Mandirancan 2 - Daya Reaktif", "000042")
        self.voltagemandarican2     = self.buat_teks_klik("0", -125+800, 1600-150, "Mandirancan 2 - Tegangan (kV)", "000043")
        self.arusmandarican2        = self.buat_teks_klik("0", -125+800, 1625-150, "Mandirancan 2 - Arus (A)", "000044")

        self.daftar_perangkat = [
            self.cb1, self.cb2, self.cb3, self.cb4,
            self.diameter1cb, self.diameter2cb, self.diameter3cb,
            self.diameter4cb, self.diameter5cb, self.diameter6cb,
            self.diameter1pms1, self.diameter1pms2,
            self.diameter2pms1, self.diameter2pms2,
            self.diameter3pms1, self.diameter3pms2,
            self.diameter4pms1, self.diameter4pms2,
            self.diameter5pms1, self.diameter5pms2,
            self.diameter6pms1, self.diameter6pms2,
        ]

        self.daftar_teks = [
            self.dayadeltamas1, self.dayaReaktifdeltamas1, self.voltagedeltamas1, self.arusdeltamas1,
            self.dayadeltamas2, self.dayaReaktifdeltamas2, self.voltagedeltamas2, self.arusdeltamas2,
            self.dayamandarican1, self.dayaReaktifmandarican1, self.voltagemandarican1, self.arusmandarican1,
            self.dayamandarican2, self.dayaReaktifmandarican2, self.voltagemandarican2, self.arusmandarican2,
        ]

        if self.status == "Not Connected":
            for item in self.daftar_perangkat:
                item.setBrush(QBrush(QColor("orange")))
            self.statusconnect.setText(self.status)
            self.poll.setText("🟥OUT OF POLL")

    def buat_kabel_belok(self, daftar_titik, warna="aqua", tebal=4):
        """Fungsi ajaib untuk membuat kabel belok hanya dengan 1 baris"""
        jalur = QPainterPath()
        
        # Taruh pena di koordinat pertama
        jalur.moveTo(daftar_titik[0][0], daftar_titik[0][1])
        
        # Looping untuk menarik garis ke koordinat-koordinat berikutnya
        for x, y in daftar_titik[1:]:
            jalur.lineTo(x, y)
            
        # Masukkan ke peta dan langsung kembalikan sebagai variabel
        return self.scene.addPath(jalur, QPen(QColor(warna), tebal))
    
    def openingGITET(self):
            from map_jamali import PetaGarduInduk
            self.petagardu = PetaGarduInduk()
            self.petagardu.show()
            self.close() 

    def update_telemetri(self, ioa, nilai):
        self.status = "Connected"
        self.statusconnect.setText(self.status)
        self.statusconnect.setStyleSheet("color: green")
        self.poll.setText("🟦IN POLL")

        for item in self.daftar_perangkat:
            item.setBrush(QBrush(QColor("aqua")))

        for text in self.daftar_teks:
            text.setDefaultTextColor((QColor("white"))) 
    
        # Reset watchdog — setiap ada data, timer di-reset
        self.watchdog_timer.start()   # restart hitungan 2 detik



        if ioa == 0x000011:
            self.dayadeltamas1.setPlainText(f"{nilai} MW")
        if ioa == 0x000012:
            self.voltagedeltamas1.setPlainText(f"{nilai} V")
        if ioa == 0x000013:
            self.arusdeltamas1.setPlainText(f"{nilai} A")
        if ioa == 0x000014:
            self.dayaReaktifdeltamas1.setPlainText(f"{nilai} MVAR")

        if ioa == 0x000021:
            self.dayadeltamas2.setPlainText(f"{nilai} MW")
        if ioa == 0x000022:
            self.voltagedeltamas2.setPlainText(f"{nilai} V")
        if ioa == 0x000023:
            self.arusdeltamas2.setPlainText(f"{nilai} A")
        if ioa == 0x000024:
            self.dayaReaktifdeltamas2.setPlainText(f"{nilai} MVAR")

        if ioa == 0x000031:
            self.dayamandarican1.setPlainText(f"{nilai} MW")
        if ioa == 0x000032:
            self.voltagemandarican1.setPlainText(f"{nilai} V")
        if ioa == 0x000033:
            self.arusmandarican1.setPlainText(f"{nilai} A")
        if ioa == 0x000034:
            self.dayaReaktifmandarican1.setPlainText(f"{nilai} MVAR")

        if ioa == 0x000041:
            self.dayamandarican2.setPlainText(f"{nilai} MW")
        if ioa == 0x000042:
            self.voltagemandarican2.setPlainText(f"{nilai} V")
        if ioa == 0x000043:
            self.arusmandarican2.setPlainText(f"{nilai} A")
        if ioa == 0x000044:
            self.dayaReaktifmandarican2.setPlainText(f"{nilai} MVAR")

    def aksi_klik_kanan(self, item_teks, identitas_sensor, address_hex):
        """Fungsi ajaib yang memunculkan kotak putus-putus dan Menu Opsi"""
        
        # 1. BIKIN KOTAK PUTUS-PUTUS MENGELILINGI TEKS
        # Ambil ukuran asli teksnya (X, Y, Lebar, Tinggi) di dalam peta
        ukuran_teks = item_teks.sceneBoundingRect()
        self.kotak_highlight.setRect(ukuran_teks)
        self.kotak_highlight.show() # Tampilkan kotaknya!

        # 2. BUAT MENU OPSI (QMenu)
        menu = QMenu(self.view)
        # Desain menunya biar ala SCADA (Gelap)
        menu.setStyleSheet("""
            QMenu { background-color: #2a2a2a; color: white; border: 1px solid #555; font-family: Consolas; }
            QMenu::item { padding: 5px 20px 5px 20px; }
            QMenu::item:selected { background-color: #0078d7; }
        """)

        # 3. ISI MENU OPSINYA
        menu.addAction(f"Info Sensor : {identitas_sensor}")
        menu.addAction(f"Alamat IOA  : {address_hex}")
        menu.addSeparator() # Garis pembatas
        aksi_tutup = menu.addAction("Tutup Menu")

        # 4. TAMPILKAN MENU TEPAT DI KURSOR MOUSE
        # Program akan 'berhenti' sejenak di sini sampai user mengklik salah satu opsi menu
        pilihan = menu.exec_(QCursor.pos())

        # 5. BERSIHKAN KEMBALI
        # Begitu menu ditutup/diklik, sembunyikan lagi kotak putus-putusnya
        self.kotak_highlight.hide()

        # (Opsional) Kalau mau mengeksekusi sesuatu berdasarkan klik menu:
        if pilihan == aksi_tutup:
            print("Menu ditutup.")


    def buat_teks_klik(self, teks_awal, x, y, identitas_sensor, address_hex):
        """Fungsi helper ditambah untuk menerima data address_hex"""
        
        # Kita masukkan item, identitas, dan address ke dalam lambda
        teks_item = ClickableTextItem(teks_awal, lambda item: self.aksi_klik_kanan(item, identitas_sensor, address_hex))
        
        teks_item.setDefaultTextColor(QColor("white"))
        teks_item.setPos(x, y)
        self.scene.addItem(teks_item)
        return teks_item

    def koneksi_putus(self):
        self.status = "Not Connected"
        self.statusconnect.setText(self.status)
        self.statusconnect.setStyleSheet("color: white")
        for item in self.daftar_perangkat:
            item.setBrush(QBrush(QColor("orange")))
        for teks in self.daftar_teks:
            teks.setDefaultTextColor(QColor("orange"))
        
        self.poll.setText("🟥OUT OF POLL")

if __name__ == '__main__':
    QApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
    app = QApplication(sys.argv)
    window = ScadaMapWindow()
    window.show()
    
    # Fokuskan layar kamera langsung ke koordinat panel saat aplikasi baru dibuka
    window.view.centerOn(380, 150) 
    
    sys.exit(app.exec_())