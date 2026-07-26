import socket
import time
import random
from datetime import datetime
import struct
from PyQt5.QtCore import QThread, pyqtSignal
import serial

class IecMasterThread(QThread):
    # =======================================================
    # BIKIN "PEMANCAR SINYAL" (Mengirim 2 data: IOA dan Nilai)
    # =======================================================
    data_received = pyqtSignal(int, float) 
    log_human_signal = pyqtSignal(str, int, float)
    log_raw_signal = pyqtSignal(str, str, str)

    def __init__(self):
        super().__init__()
        self.running = True

    def calculate_checksum(self, data_bytes):
        return sum(data_bytes) % 256

    def decode_rx_message(self, rx_bytes, rx_timestamp):
        try:
            if len(rx_bytes) > 4 and rx_bytes[0] == 0x68 and rx_bytes[3] == 0x68:
                type_id = rx_bytes[7]
                if type_id == 0x0D:
                    vsq = rx_bytes[8]
                    num_objects = vsq & 0x7F  
                    
                    idx = 12
                    for _ in range(num_objects):
                        ioa = rx_bytes[idx] + (rx_bytes[idx+1] << 8) + (rx_bytes[idx+2] << 16)
                        idx += 3
                        
                        float_bytes = rx_bytes[idx : idx+4]
                        value = struct.unpack('<f', float_bytes)[0]
                        value = round(value, 2)
                        idx += 5 # 4 byte float + 1 byte QDS
                        
                        # 2. HAPUS KATA "self." PADA rx_timestamp DI SINI
                        self.log_human_signal.emit(rx_timestamp, ioa, value)

                        # =======================================================
                        # TEMBAKKAN SINYAL KE GUI SLD INDRAMAYU!
                        # =======================================================
                        self.data_received.emit(ioa, value)

        except Exception as e:
            print(f"[!] Gagal men-decrypt pesan: {e}")

    # def run(self):
    #     """Fungsi ini otomatis berjalan di latar belakang (Background) dengan Auto-Reconnect"""
    #     host = '127.0.0.1' 
    #     port = 5000        
        
    #     # master_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #     # master_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    #     # master_socket.bind((host, port))
    #     # master_socket.listen(1)

    #     master_socket = serial.Serial('COM4', 115200, timeout=1.0)
        
    #     # Set timeout 1 detik pada Master Socket. 
    #     # Ini berguna agar saat Anda menutup GUI, Thread tidak "nge-hang" menunggu accept().
    #     master_socket.settimeout(1.0) 
        
    #     print("[*] Master Node Latar Belakang Aktif.")
        
    #     # =======================================================
    #     # LOOP LUAR: Bertugas menunggu dan menerima koneksi baru
    #     # =======================================================
    #     while self.running:
    #         try:
    #             # Program akan nyangkut di sini sampai ada Slave yang konek
    #             conn, addr = master_socket.accept()
    #             print(f"\n[*] ======================================")
    #             print(f"[*] Slave BERHASIL terhubung dari: {addr}")
    #             print(f"[*] ======================================")
                
    #             fcb_toggle = True 
    #             link_address = [0x01, 0x00]
                
    #             # =======================================================
    #             # LOOP DALAM: Bertugas ngobrol (Tx/Rx) selama koneksi hidup
    #             # =======================================================
    #             try:
    #                 while self.running:
    #                     left_digit = 0x50 if fcb_toggle else 0x70
    #                     right_digit = random.choice([0x0A, 0x0B]) 
    #                     control_field = left_digit | right_digit
    #                     fcb_toggle = not fcb_toggle
                        
    #                     frame_body = [control_field] + link_address
    #                     checksum = self.calculate_checksum(frame_body)
                        
    #                     tx_frame = [0x10] + frame_body + [checksum, 0x16]
    #                     tx_bytes = bytes(tx_frame)
    #                     tx_hex_str = '-'.join(f'{b:02X}' for b in tx_bytes)

    #                     timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    #                     print(f"[{timestamp}] [Tx] : {tx_hex_str}")
    #                     self.log_raw_signal.emit(timestamp, "Tx", tx_hex_str)
    #                     # --- KIRIM PESAN (Tx) ---
    #                     try:
    #                         # conn.send(tx_bytes)
    #                         master_socket.write(tx_bytes)
    #                     except (ConnectionResetError, BrokenPipeError):
    #                         # Jika Slave dimatikan paksa saat Master mau ngirim
    #                         print("[!] Gagal mengirim pesan. Slave terputus tiba-tiba.")
    #                         break # Hancurkan Loop Dalam, kembali ke Loop Luar
                        
    #                     # --- TERIMA PESAN (Rx) ---
    #                     try:
    #                         conn.settimeout(0.5) 
    #                         buffer = b""
                            
    #                         while True: 
    #                             try:
    #                                 # chunk = conn.recv(1024)
    #                                 chunk = master_socket.read(1024)
    #                                 # Jika chunk kosong, artinya koneksi diputus secara normal oleh Slave
    #                                 if not chunk:
    #                                     print("[!] Koneksi ditutup oleh Slave.")
    #                                     raise ConnectionAbortedError("Slave Disconnected")
                                    
    #                                 buffer += chunk
                                    
    #                                 # Proses pemotong gerbong
    #                                 while len(buffer) > 0:
    #                                     if buffer[0] == 0x68 and len(buffer) >= 2:
    #                                         isi_len = buffer[1]
    #                                         total_len = isi_len + 6 
                                            
    #                                         if len(buffer) >= total_len:
    #                                             single_frame = buffer[:total_len]
                                                
    #                                             rx_hex_str = '-'.join(f'{b:02X}' for b in single_frame)
    #                                             rx_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    #                                             print(f"[{rx_timestamp}] [Rx] : {rx_hex_str}")
    #                                             self.log_raw_signal.emit(rx_timestamp, "Rx", rx_hex_str)
                                                
    #                                             self.decode_rx_message(single_frame, rx_timestamp)
    #                                             buffer = buffer[total_len:]
    #                                         else:
    #                                             break 
    #                                     else:
    #                                         buffer = buffer[1:]
                                            
    #                             except socket.timeout:
    #                                 print() 
    #                                 break 
                                    
    #                     except ConnectionAbortedError:
    #                         break # Hancurkan Loop Dalam, kembali ke Loop Luar
    #                     except Exception as e:
    #                         print(f"[!] Error saat Rx: {e}")
    #                         break
                        
    #                     # Jeda 3 detik sebelum Tx berikutnya
    #                     time.sleep(3)
                        
    #             finally:
    #                 # Kalau Loop Dalam hancur (Slave mati), pastikan socket lama ditutup
    #                 # agar port-nya siap dipakai accept() lagi oleh Loop Luar.
    #                 conn.close()
    #                 print("[*] Membersihkan sisa koneksi... Kembali mode mendengarkan jaringan.")
                    
    #         except socket.timeout:
    #             # Wajar terjadi setiap 1 detik jika belum ada Slave yang konek (biarkan saja pass)
    #             pass
    #         except Exception as e:
    #             print(f"[!] Master Socket Error: {e}")
    #             break
                
    #     # Menutup socket utama jika aplikasi GUI benar-benar dimatikan
    #     master_socket.close()

    def run(self):
        """Fungsi ini otomatis berjalan di latar belakang (Background) untuk koneksi USB/Serial ESP32"""
        import serial
        import time
        
        print("[*] Master Node Latar Belakang Aktif. Mencari ESP32 di COM4...")
        
        # =======================================================
        # LOOP LUAR: Bertugas mencari dan membuka port COM4
        # =======================================================
        while self.running:
            try:
                # Buka port serial (Otomatis nyambung ke ESP32)
                # Pastikan 'COM4' sesuai dengan port yang ada di komputer Anda
                master_serial = serial.Serial('COM4', 115200, timeout=1.0)
                
                print(f"\n[*] ======================================")
                print(f"[*] ESP32 BERHASIL terhubung di COM4!")
                print(f"[*] ======================================")
                
                fcb_toggle = True 
                link_address = [0x01, 0x00]
                
                # =======================================================
                # LOOP DALAM: Bertugas ngobrol (Tx/Rx) selama kabel tertancap
                # =======================================================
                try:
                    while self.running:
                        left_digit = 0x50 if fcb_toggle else 0x70
                        right_digit = random.choice([0x0A, 0x0B]) 
                        control_field = left_digit | right_digit
                        fcb_toggle = not fcb_toggle
                        
                        frame_body = [control_field] + link_address
                        checksum = self.calculate_checksum(frame_body)
                        
                        tx_frame = [0x10] + frame_body + [checksum, 0x16]
                        tx_bytes = bytes(tx_frame)
                        tx_hex_str = '-'.join(f'{b:02X}' for b in tx_bytes)

                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                        print(f"[{timestamp}] [Tx] : {tx_hex_str}")
                        self.log_raw_signal.emit(timestamp, "Tx", tx_hex_str)
                        
                        # --- KIRIM PESAN (Tx) VIA SERIAL ---
                        try:
                            master_serial.write(tx_bytes) # <-- Menggunakan WRITE
                        except serial.SerialException:
                            print("[!] Gagal mengirim pesan. Kabel USB terputus?")
                            break # Hancurkan Loop Dalam, kembali ke Loop Luar
                        
                        # --- TERIMA PESAN (Rx) VIA SERIAL ---
                        try:
                            # Cara mengatur timeout di Serial (bukan settimeout)
                            master_serial.timeout = 0.5 
                            buffer = b""
                            
                            while True: 
                                try:
                                    chunk = master_serial.read(1024) # <-- Menggunakan READ
                                    
                                    # Jika chunk kosong (timeout 0.5 detik tercapai dan ga ada data)
                                    if not chunk:
                                        break # Keluar dari loop baca buffer, masuk ke jeda 3 detik
                                    
                                    buffer += chunk
                                    
                                    # Proses pemotong gerbong (Frame Slicer)
                                    while len(buffer) > 0:
                                        if buffer[0] == 0x68 and len(buffer) >= 2:
                                            isi_len = buffer[1]
                                            total_len = isi_len + 6 
                                            
                                            if len(buffer) >= total_len:
                                                single_frame = buffer[:total_len]
                                                
                                                rx_hex_str = '-'.join(f'{b:02X}' for b in single_frame)
                                                rx_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                                                print(f"[{rx_timestamp}] [Rx] : {rx_hex_str}")
                                                self.log_raw_signal.emit(rx_timestamp, "Rx", rx_hex_str)
                                                
                                                self.decode_rx_message(single_frame, rx_timestamp)
                                                buffer = buffer[total_len:]
                                            else:
                                                break 
                                        else:
                                            buffer = buffer[1:]
                                            
                                except Exception as e:
                                    print(f"[!] Error saat membaca Serial: {e}")
                                    break 
                                    
                        except serial.SerialException:
                            print("[!] Kabel USB sepertinya dicabut mendadak.")
                            break
                        
                        # Jeda 3 detik sebelum Master bertanya (polling) lagi ke ESP32
                        time.sleep(3)
                        
                finally:
                    # Tutup port jika Loop Dalam hancur (Kabel dicabut)
                    master_serial.close()
                    print("[*] Port COM4 dibersihkan. Bersiap mencari ulang...")
                    time.sleep(2) # Jeda sebelum mencoba reconnect
                    
            except serial.SerialException:
                # Jika Master gagal membuka port (Karena sedang dipakai Serial Monitor / Kabel belum dicolok)
                print(f"[!] Gagal terhubung ke COM4 (Port sedang dipakai atau kabel belum dicolok).")
                print("    Mencoba lagi dalam 3 detik...")
                time.sleep(3)
            except Exception as e:
                print(f"[!] Master Serial Error Utama: {e}")
                break
            
    def stop(self):
        self.running = False
        self.wait()

if __name__ == '__main__':
    ICT = IecMasterThread()
    ICT.run()