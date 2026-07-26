import socket
import struct
import random
import time 
from datetime import datetime

def calculate_checksum(data_bytes):
    return sum(data_bytes) % 256

def float_to_hex_bytes(value):
    return list(struct.pack('<f', value))

def start_slave():
    host = '127.0.0.1' 
    port = 5000        
    
    print("=======================================")
    print(" SLAVE NODE (IEC 60870-5-101) AKTIF")
    print("=======================================")

    # Menangkap aksi Ctrl+C agar aplikasi tertutup rapi
    try:
        # =======================================================
        # LOOP LUAR: Terus mencoba konek ke Master jika terputus
        # =======================================================
        while True:
            slave_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            print(f"[*] Mencoba terhubung ke Master di {host}:{port}...")
            
            try:
                slave_socket.connect((host, port))
                print("[*] Berhasil terhubung ke Master! Menunggu perintah...\n")
            except ConnectionRefusedError:
                # Jika Master belum dijalankan, tunggu 3 detik lalu coba lagi
                print("[!] Master belum aktif. Mencoba lagi dalam 3 detik...")
                time.sleep(3)
                continue 

            # =======================================================
            # LOOP DALAM: Ngobrol (Tx/Rx) selama koneksi hidup
            # =======================================================
            try:
                while True:
                    # 1. BACA PERINTAH (Tahan banting jika Master mati saat idle)
                    try:
                        req_bytes = slave_socket.recv(1024)
                    except (ConnectionResetError, ConnectionAbortedError):
                        print("[!] Koneksi terputus paksa oleh Master.")
                        break # Hancurkan Loop Dalam

                    if not req_bytes:
                        print("[!] Koneksi diputus secara wajar oleh Master.")
                        break

                    if req_bytes[0] == 0x10:
                        
                        # =========================================================
                        # LOOPING 4 KALI UNTUK MENGIRIM 4 PESAN BERBEDA
                        # =========================================================
                        try:
                            for i in range(1, 5):
                                val1 = round(random.uniform(10.0, 50.0), 2)   
                                val2 = round(random.uniform(140.0, 150.0), 2) 
                                val3 = round(random.uniform(100.0, 200.0), 2) 
                                val4 = round(random.uniform(100.0, 200.0), 2) 
                                
                                byte1 = float_to_hex_bytes(val1)
                                byte2 = float_to_hex_bytes(val2)
                                byte3 = float_to_hex_bytes(val3)
                                byte4 = float_to_hex_bytes(val4)

                                base_ioa = i * 0x10 

                                obj1 = [base_ioa + 0x01, 0x00, 0x00] + byte1 + [0x00]
                                obj2 = [base_ioa + 0x02, 0x00, 0x00] + byte2 + [0x00]
                                obj3 = [base_ioa + 0x03, 0x00, 0x00] + byte3 + [0x00]
                                obj4 = [base_ioa + 0x04, 0x00, 0x00] + byte4 + [0x00]
                                
                                control_field = 0x08        
                                link_address = [0x01, 0x00] 
                                type_id = 0x0D              
                                vsq = 0x04                  
                                cot = 0x03                  
                                common_address = [0x01, 0x00] 
                                
                                frame_body = [control_field] + link_address + [type_id, vsq, cot] + common_address + obj1 + obj2 + obj3 + obj4
                                
                                length = len(frame_body) 
                                checksum = calculate_checksum(frame_body)
                                
                                rx_frame = [0x68, length, length, 0x68] + frame_body + [checksum, 0x16]
                                rx_bytes = bytes(rx_frame)
                                
                                rx_hex_str = '-'.join(f'{b:02X}' for b in rx_bytes)
                                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                                
                                print(f"[{timestamp}] [Rx Pesan {i}] : {rx_hex_str}")
                                print(f"       -> (Address {base_ioa+1:02X}-{base_ioa+4:02X}) | {val1}MW, {val2}kV, {val3}A, {val4}A")
                                
                                # 2. KIRIM BALASAN (Tahan banting jika Master mati pas lagi ngirim)
                                try:
                                    slave_socket.send(rx_bytes)
                                except (ConnectionAbortedError, ConnectionResetError):
                                    print("[!] Master ditutup mendadak saat Slave mencoba membalas.")
                                    # Lempar pesan error untuk menghancurkan Loop Dalam
                                    raise ConnectionError 
                                
                                time.sleep(0.1) 
                                
                            print("-" * 60)
                            
                        except ConnectionError:
                            break # Hancurkan Loop Dalam jika error saat send terjadi
                            
            finally:
                # Pastikan colokan lama dicabut sebelum mencoba colokan baru
                slave_socket.close()
                print("[*] Membersihkan koneksi lama. Bersiap mencari Master lagi...\n")
                time.sleep(2) # Kasih nafas 2 detik sebelum nyari Master lagi
                
    except KeyboardInterrupt:
        print("\n[*] Script Slave dihentikan secara manual oleh user (Ctrl+C).")

if __name__ == '__main__':
    start_slave()