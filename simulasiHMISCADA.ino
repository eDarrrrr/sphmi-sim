#include <Arduino.h>

// =======================================================
// FUNGSI BANTUAN
// =======================================================

// 1. Fungsi untuk menghitung checksum (Modulo 256)
uint8_t calculate_checksum(uint8_t *data, int length) {
    uint16_t sum = 0;
    for (int i = 0; i < length; i++) {
        sum += data[i];
    }
    // Casting ke uint8_t otomatis memotong jadi 8-bit terbawah (mod 256)
    return (uint8_t)(sum & 0xFF); 
}

// 2. Fungsi mengubah float menjadi 4 byte Hex (IEEE 754 Little Endian)
void float_to_hex_bytes(float val, uint8_t *bytes_array) {
    memcpy(bytes_array, &val, 4);
}

// =======================================================
// PROGRAM UTAMA
// =======================================================
void setup() {
    // Membuka jalur komunikasi Serial dengan PC (Master)
    // Pastikan baudrate ini sama dengan baudrate di Python Master nantinya
    Serial.begin(115200);
    
    // Memberikan seed agar nilai random benar-benar acak
    randomSeed(analogRead(0));
    
    // Jeda sebentar sebelum mulai
    delay(1000);
    
    // Catatan: Di ESP32, kita tidak perlu print "Menunggu koneksi"
    // karena jalur Serial lewat USB selalu terbuka begitu kabel dicolok.
}

void loop() {
    // 1. SLAVE DIAM DAN MENUNGGU PERINTAH MASTER VIA SERIAL
    if (Serial.available() > 0) {
        
        // Baca byte pertama yang masuk
        uint8_t first_byte = Serial.read();
        
        // Mengecek apakah byte awal adalah 0x10 (Format Fixed Frame Master)
        if (first_byte == 0x10) {
            
            // Opsional: Bersihkan sisa byte perintah master yang masih nyangkut di buffer 
            // (karena master mengirim 10 - CTRL - LINK - LINK - CS - 16)
            delay(10); // Tunggu sebentar agar sisa byte sampai ke ESP32
            while(Serial.available() > 0) {
                Serial.read(); // Buang sisa byte agar buffer bersih untuk perintah selanjutnya
            }

            // =========================================================
            // LOOPING 4 KALI UNTUK MENGIRIM 4 PESAN BERBEDA
            // =========================================================
            for (int i = 1; i <= 4; i++) {
                
                // 1. BUAT DATA DUMMY (Random)
                // random(min, max) di Arduino hanya menghasilkan integer,
                // jadi kita akali dengan membaginya 100.0
                float val1 = random(30000, 65000) / 100.0; // Daya Aktif (300.00 - 650.00 MW)
                float val2 = random(49500, 51500) / 100.0; // Tegangan (495.00 - 515.00 kV)
                float val3 = random(40000, 80000) / 100.0; // Arus (400.00 - 800.00 A)
                float val4 = random(5000, 25000) / 100.0;  // Daya Reaktif (50.00 - 250.00 MVAR)
                
                uint8_t byte1[4], byte2[4], byte3[4], byte4[4];
                float_to_hex_bytes(val1, byte1);
                float_to_hex_bytes(val2, byte2);
                float_to_hex_bytes(val3, byte3);
                float_to_hex_bytes(val4, byte4);

                // 2. LOGIKA MATEMATIKA ADDRESS (IOA)
                uint8_t base_ioa = i * 0x10;

                // 3. SUSUN BUNGKUSAN PESAN (FRAME BODY)
                // Karena di C++ kita tidak bisa menggabung List semudah di Python,
                // kita masukkan bytenya satu per satu ke dalam array menggunakan index.
                uint8_t frame_body[50]; // Siapkan array berukuran cukup besar
                int idx = 0;
                
                frame_body[idx++] = 0x08; // control_field
                frame_body[idx++] = 0x01; // link_address LSB
                frame_body[idx++] = 0x00; // link_address MSB
                frame_body[idx++] = 0x0D; // type_id (13)
                frame_body[idx++] = 0x04; // vsq (4 objek)
                frame_body[idx++] = 0x03; // cot
                frame_body[idx++] = 0x01; // common_address LSB
                frame_body[idx++] = 0x00; // common_address MSB

                // Susun Objek 1
                frame_body[idx++] = base_ioa + 0x01; frame_body[idx++] = 0x00; frame_body[idx++] = 0x00;
                for(int j=0; j<4; j++) frame_body[idx++] = byte1[j];
                frame_body[idx++] = 0x00; // QDS

                // Susun Objek 2
                frame_body[idx++] = base_ioa + 0x02; frame_body[idx++] = 0x00; frame_body[idx++] = 0x00;
                for(int j=0; j<4; j++) frame_body[idx++] = byte2[j];
                frame_body[idx++] = 0x00;

                // Susun Objek 3
                frame_body[idx++] = base_ioa + 0x03; frame_body[idx++] = 0x00; frame_body[idx++] = 0x00;
                for(int j=0; j<4; j++) frame_body[idx++] = byte3[j];
                frame_body[idx++] = 0x00;

                // Susun Objek 4
                frame_body[idx++] = base_ioa + 0x04; frame_body[idx++] = 0x00; frame_body[idx++] = 0x00;
                for(int j=0; j<4; j++) frame_body[idx++] = byte4[j];
                frame_body[idx++] = 0x00;

                // 4. MENGHITUNG LENGTH DAN CHECKSUM
                uint8_t length = idx; // Panjang isi (harusnya sekitar 40 byte / 0x28)
                uint8_t checksum = calculate_checksum(frame_body, length);

                // 5. MENYUSUN FRAME FINAL (Awalan 68)
                uint8_t rx_frame[60];
                int f_idx = 0;
                
                rx_frame[f_idx++] = 0x68;
                rx_frame[f_idx++] = length;
                rx_frame[f_idx++] = length;
                rx_frame[f_idx++] = 0x68;
                
                // Masukkan isi frame_body ke tengah-tengah
                for(int j=0; j<length; j++) {
                    rx_frame[f_idx++] = frame_body[j];
                }
                
                rx_frame[f_idx++] = checksum;
                rx_frame[f_idx++] = 0x16;

                // 6. KIRIM KE MASTER VIA SERIAL (Bentuk Heksadesimal Mentah)
                // write() akan mengirim byte mentah (bukan teks string),
                // sehingga Python Master bisa menangkapnya persis seperti socket.recv()
                Serial.write(rx_frame, f_idx);

                // MEMBERI JEDA WAKTU (PENTING!)
                delay(100); 
            }
        }
    }
}