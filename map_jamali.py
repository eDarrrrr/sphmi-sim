import sys
import io
import folium
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt5.QtWebEngineWidgets import QWebEnginePage, QWebEngineView
from folium.plugins import MousePosition
from branca.element import MacroElement
from jinja2 import Template
from PyQt5.QtCore import QUrl

class ClickableCircleMarker(folium.CircleMarker):
    _template = Template("""
        {% macro script(this, kwargs) %}
            var {{ this.get_name() }} = L.circleMarker(
                [{{ this.location[0] }}, {{ this.location[1] }}],
                {{ this.options | tojson }}
            ).addTo({{ this._parent.get_name() }});
            
            // INI KODE AJAIBNYA: Saat diklik, langsung pindah ke URL palsu
            {{ this.get_name() }}.on('click', function(e) {
                window.location.href = 'scada://' + '{{ this.target_id }}';
            });
        {% endmacro %}
        """)

    def __init__(self, location, target_id, **kwargs):
        super().__init__(location, **kwargs)
        self.target_id = target_id

class ScadaWebPage(QWebEnginePage):
    def acceptNavigationRequest(self, url, _type, isMainFrame):
        # Cek apakah link yang diklik berawalan "scada://"
        if url.scheme() == "scada":
            target = url.host() # Mengambil kata targetnya
            
            # Jika targetnya adalah gitet_indramayu
            if target == "gitet_indramayu":
                from sld_indramayu import ScadaMapWindow
                self.sld_window = ScadaMapWindow()
                self.sld_window.show()
                self.sld_window.view.centerOn(380, 150) 
                self.view().window().close() 
            return False # Kembalikan False agar browser tidak beneran loading halaman baru
            
        return super().acceptNavigationRequest(url, _type, isMainFrame)

class ClickToCopy(MacroElement):
    _template = Template("""
        {% macro script(this, kwargs) %}
            var {{ this.get_name() }} = L.popup();
            function clickToCopyPop(e) {
                var lat = e.latlng.lat.toFixed(5);
                var lng = e.latlng.lng.toFixed(5);
                var coord_str = "[" + lat + ", " + lng + "]";
                
                var content = '<div style="text-align: center; color: black; font-family: Arial;">' +
                              '<b style="font-size: 14px;">Koordinat (Lat, Lng)</b><br>' +
                              '<input type="text" id="coordInput" value="' + coord_str + '" style="margin: 8px 0; padding: 4px; text-align: center; border: 1px solid #999; width: 140px; border-radius: 4px;" readonly><br>' +
                              '<button onclick="document.getElementById(\\'coordInput\\').select(); document.execCommand(\\'copy\\'); this.innerText=\\'Tercopy!\\'; this.style.background=\\'#28a745\\'; this.style.color=\\'white\\';" style="cursor: pointer; padding: 6px 12px; border: none; background: #007bff; color: white; border-radius: 4px; font-weight: bold;">Copy</button>' +
                              '</div>';
                              
                {{ this.get_name() }}
                    .setLatLng(e.latlng)
                    .setContent(content)
                    .openOn({{ this._parent.get_name() }});
            }
            
            // --- BAGIAN YANG DIGANTI ---
            // Mengubah event 'click' menjadi 'dblclick'
            {{ this._parent.get_name() }}.on('dblclick', clickToCopyPop);
            
        {% endmacro %}
        """)

    def __init__(self):
        super().__init__()
        self._name = 'ClickToCopy'

# ==========================================
# MAIN WINDOW APP
# ==========================================
class PetaGarduInduk(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Interactive Map - Advance Control Center")
        self.setGeometry(200, 200, 2000, 1200)

        self.setStyleSheet("background-color: black;")

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self.browser = QWebEngineView()
        self.browser.setPage(ScadaWebPage(self.browser))
        layout.addWidget(self.browser)

        self.generate_map()

    def generate_map(self):
        map_indo = folium.Map(location=[-7.250445, 110.114450], zoom_start=8, tiles=None, doubleClickZoom=False)

        background_css = """
        <style>
            html, body {
                margin: 0;
                padding: 0;
                overflow: hidden !important; 
                background-color: black !important;
            }
            .leaflet-container {
                background-color: #1e3a8a !important; 
            }
        </style>
        """
        map_indo.get_root().header.add_child(folium.Element(background_css))

        geojson_url = "indonesia.geojson"
        
        folium.GeoJson(
            geojson_url,
            name="Indonesia",
            style_function=lambda feature: {
                'fillColor': '#000000', 
                'color': '#ffffff',     
                'weight': 1,            
                'fillOpacity': 1,
                'interactive': False  # <--- INI PENTING! Agar klik mouse tembus ke layer map
            }
        ).add_to(map_indo)

        gardu_induk = {

            "GITET DELTAMAS" : [-6.43540, 107.37900],
            "GITET INDRAMAYU" : [-6.33441, 108.15765],
            "GITET MANDIRANCAN" : [-6.87871, 108.43094],
            "GITET CIREBON" : [-6.79690, 108.82370],
            "GITET PEMALANG" : [-6.94279, 109.43069],
            "GITET BATANG" : [-6.82553, 109.51172],

            "GITET BANDUNG SELATAN" : [-7.15949, 107.38861],
            "GITET UJUNG BERUNG" : [-7.02048, 107.68936],
            "GITET SAGULING" : [-6.92506, 106.95053],
            "GITET CIRATA" : [-6.69461, 107.17163],
        }


        jalur_transmisi = [
            {"nama": "SUTET 500KV", "rute": [gardu_induk["GITET DELTAMAS"], gardu_induk["GITET INDRAMAYU"], gardu_induk["GITET MANDIRANCAN"]]},
            {"nama": "SUTET 500KV", "rute": [gardu_induk["GITET DELTAMAS"], gardu_induk["GITET CIRATA"], gardu_induk["GITET SAGULING"], gardu_induk["GITET BANDUNG SELATAN"], gardu_induk["GITET UJUNG BERUNG"], gardu_induk["GITET MANDIRANCAN"]]},
            {"nama": "SUTET 500KV", "rute": [gardu_induk["GITET MANDIRANCAN"], gardu_induk["GITET CIREBON"], gardu_induk["GITET PEMALANG"]]},
            {"nama": "SUTET 500KV", "rute": [gardu_induk["GITET MANDIRANCAN"], gardu_induk["GITET PEMALANG"]]},
            ]

        for jalur in jalur_transmisi:
            if jalur["nama"] == "SUTET 500KV":
                folium.PolyLine(
                    locations=jalur["rute"],
                    color='#00FFFF',      # Warna outline (Cyan)
                    weight=8,            # Ukuran tebal
                    opacity=0.8,          
                    tooltip=jalur["nama"] # Tooltip ditaruh di garis tebal agar area hover/kliknya lebih luas
                ).add_to(map_indo)

                # 2. GARIS ATAS (Berfungsi sebagai Fill Hitam)
                folium.PolyLine(
                    locations=jalur["rute"],
                    color='#000000',      # Warna dalam (Hitam)
                    weight=6,             # Lebih tipis dari outline (12 - 6 = sisa margin outline 3px di tiap sisi)
                    opacity=1.0           # Solid hitam
                ).add_to(map_indo)

            else:
                folium.PolyLine(
                    locations=jalur["rute"],
                    color='#00FFFF',      # Warna outline (Cyan)
                    weight=2,            # Ukuran tebal
                    opacity=0.8,          
                    tooltip=jalur["nama"] # Tooltip ditaruh di garis tebal agar area hover/kliknya lebih luas
                ).add_to(map_indo)
        
        formatter = "function(num) {return L.Util.formatNum(num, 5) + ' &deg;';};"
        
        for nama, lokasi in gardu_induk.items():
            
            if nama == "GITET INDRAMAYU":
                # 1A. GUNAKAN CUSTOM MARKER UNTUK INDRAMAYU (TANPA POPUP)
                ClickableCircleMarker(
                    location=lokasi,
                    target_id="gitet_indramayu", # Kata kunci yang akan dibaca oleh Satpam Python
                    radius=8,                   # Sengaja dibesarkan sedikit agar gampang diklik
                    color='#00FFFF',             # Kasih warna beda (merah) sebagai penanda
                    weight=2,                  
                    fill=True,                 
                    fill_color='#00FFFF',         
                    fill_opacity=1.0,          
                    tooltip=f"<b>{nama}</b><br>" # Pake tooltip (muncul saat mouse hover)
                ).add_to(map_indo)
                
            else:
                # 1B. GUNAKAN MARKER BIASA UNTUK GARDU LAIN
                folium.CircleMarker(
                    location=lokasi,
                    radius=8,                  
                    color='#00FFFF',              
                    weight=2,                  
                    fill=True,                 
                    fill_color='#00FFFF',         
                    fill_opacity=1.0,          
                    popup=f"<b>{nama}</b>"
                ).add_to(map_indo)

            # 2. Gambar Teks Permanen (Label) di Sebelah Titik
            folium.Marker(
                location=lokasi,
                icon=folium.DivIcon(
                    # icon_anchor: (geser_x, geser_y). 
                    # Angka negatif di geser_x bikin teksnya pindah ke kanan titik.
                    icon_anchor=(-10, 8), 
                    html=f'''
                        <div style="
                            font-size: 10pt; 
                            color: white; 
                            font-weight: bold; 
                            font-family: Arial; 
                            white-space: nowrap; 
                            text-shadow: 1px 1px 2px black, -1px -1px 2px black;
                        ">
                            {nama}
                        </div>
                    '''
                )
            ).add_to(map_indo)

        MousePosition(
            position='bottomleft',       
            separator=' | ',           
            empty_string='Tunggu...',  
            lng_first=False,           
            num_digits=5,
            prefix='Koordinat:',
            lat_formatter=formatter,
            lng_formatter=formatter,
        ).add_to(map_indo)
        
        watermark_html = """
        <div style="
            position: fixed; 
            top: 50px; 
            left: 750px; 
            z-index: 9999; 
            font-size: 24pt; 
            font-weight: bold; 
            color: yellow; 
            font-family: Arial, sans-serif;
            pointer-events: none;
            ">
            JAWA BALI CONTROL CENTER
        </div>
        """

        blackbar_html = """
        <div style="
            position: fixed; 
            top: 0; 
            left: 0; 
            width: 100%; 
            height: 140px; 
            background-color: black; 
            z-index: 9998;
        ">
        </div>
        """

        map_indo.get_root().html.add_child(folium.Element(watermark_html))
        map_indo.get_root().html.add_child(folium.Element(blackbar_html))

        # ==========================================
        # PASANG PLUGIN CLICK-TO-COPY KE MAP
        # ==========================================
        ClickToCopy().add_to(map_indo)

        data = io.BytesIO()
        map_indo.save(data, close_file=False)
        html_content = data.getvalue().decode()

        self.browser.setHtml(html_content)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PetaGarduInduk()
    window.show()
    sys.exit(app.exec_())