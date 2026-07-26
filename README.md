# SCADA HMI Simulation — Java Bali Control Center

A desktop-based SCADA HMI (Human-Machine Interface) simulation for monitoring GITET (*Gardu Induk Tegangan Ekstra Tinggi* — 500 kV extra-high-voltage substations) across the Java–Madura–Bali (JAMALI) power grid. Built with Python, PyQt5, and Folium, it simulates Master–Slave communication using the **IEC 60870-5-101** protocol (fixed-length frames `0x10`, variable-length frames `0x68`, ASDU type 13 / M_ME_NC_1 — measured values, short float).

The telemetry source can be swapped between:

- **Software slave** (`slave_node.py`, TCP) — pure software simulation, no hardware needed.
- **Physical ESP32** (`simulasiHMISCADA.ino`, USB serial) — real hardware in the loop.

## Features

- Interactive substation map of the JAMALI grid (Folium + PyQtWebEngine)
- Real-time Single Line Diagram (SLD) of GITET Indramayu
- IEC 60870-5-101 Master polling loop with auto-reconnect
- Data logger (TRACE window): human-readable telemetry + raw hex frames
- Pluggable telemetry backend: TCP software slave or ESP32 over USB serial

## Requirements

- Python 3.11 (developed on 3.11.0)
- pip + venv
- *(Optional, Mode 2 only)* ESP32 dev board + Arduino IDE with the ESP32 board package

## Installation

1. Clone this repository and enter the folder:

   ```bash
   git clone <repo-url>
   cd sphmi-sim
   ```

2. Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   ```

   - **Windows:** `.venv\Scripts\activate`
   - **Linux / macOS:** `source .venv/bin/activate`

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Mode 1 — Without ESP32 (Software Slave, default)

This is the default state of the repository: `sld_indramayu.py` imports `master_node_withoutesp`, so the Master listens on TCP `127.0.0.1:5000` and waits for a software slave to connect.

1. **Terminal 1** — run the HMI:

   ```bash
   python main.py
   ```

2. In the login window (*SIMULASI HMI*), click **GITET**.
3. On the map, click the cyan **GITET INDRAMAYU** marker. The SLD window opens and the Master thread starts listening on port 5000.
4. **Terminal 2** (with the venv activated) — run the software slave:

   ```bash
   python slave_node.py
   ```

5. Random telemetry starts flowing into the SLD. Click the **TRACE** button in the side panel to open the Data Logger (human-readable values + raw hex frames).

> The slave retries the connection every 3 seconds, so the launch order is flexible — just make sure both are running at the same time.

## Mode 2 — With ESP32 (Hardware Slave)

### Step 1 — Flash the firmware

1. Open `simulasiHMISCADA.ino` in the Arduino IDE.
2. Install the **ESP32 board package** via *Tools → Board → Boards Manager* if you haven't already.
3. Select your ESP32 board and the correct port, then click **Upload**.
4. **Close the Serial Monitor** after uploading — the COM port must be free for Python to use.

### Step 2 — Change two things in the code

1. **`sld_indramayu.py` line 7** — swap the Master import:

   ```python
   # from master_node_withoutesp import IecMasterThread   # Mode 1 (TCP, default)
   from master_node import IecMasterThread                 # Mode 2 (Serial / ESP32)
   ```

2. **`master_node.py`** — adjust the serial port (default is `'COM4'` for Windows):

   - **Windows:** check Device Manager (e.g. `COM4`)
   - **Linux:** usually `'/dev/ttyUSB0'` (check with `ls /dev/ttyUSB*`)
   - Baud rate must stay `115200`, matching `Serial.begin(115200)` in the `.ino` file.

### Step 3 — Run

1. Plug the ESP32 into a USB port.
2. Run the HMI and open the SLD:

   ```bash
   python main.py
   ```

   → click **GITET** → click the **GITET INDRAMAYU** marker.

3. The Master automatically polls the ESP32 every 3 seconds and telemetry appears on the SLD.
4. **Do NOT run `slave_node.py`** in this mode — the ESP32 acts as the slave.

## Master Node Comparison

| | `master_node_withoutesp.py` (default) | `master_node.py` (ESP32) |
|---|---|---|
| Transport | TCP socket `127.0.0.1:5000` | USB Serial `COM4` / `/dev/ttyUSB0` @ 115200 baud |
| Slave | `slave_node.py` (software, random data) | ESP32 flashed with `simulasiHMISCADA.ino` |
| Extra terminal/process | Yes — must run `slave_node.py` | No — just plug in the ESP32 |
| Code changes needed | None (repo default) | ① Import line in `sld_indramayu.py` ② Serial port in `master_node.py` |

## Project Structure

```
main.py                          Entry point — login window (ui/login.ui)
├── resources.py / resources.qrc Compiled Qt resources (login background)
├── assets/                      Images referenced by the resources
└── map_jamali.py                Interactive JAMALI substation map
    │                            (reads indonesia.geojson)
    └── sld_indramayu.py         SLD window of GITET Indramayu
        ├── master_node_withoutesp.py   IEC-101 Master via TCP   (Mode 1, default)
        ├── master_node.py              IEC-101 Master via Serial (Mode 2, ESP32)
        └── log_window.py               TRACE / data logger window

slave_node.py                    Software slave for Mode 1 (run separately)
simulasiHMISCADA.ino             ESP32 firmware for Mode 2 (flash via Arduino IDE)
indonesia.geojson                Map geometry, must stay next to the scripts
```

## Troubleshooting

- **`ModuleNotFoundError: No module named 'serial'`** → run `pip install pyserial` (already listed in `requirements.txt`).
- **`Gagal terhubung ke COM4` / port errors (Mode 2)** → the Arduino Serial Monitor is still open, the port name is wrong, or the cable is unplugged. The Master retries every 3 seconds — fix the issue and wait.
- **Slave prints `Master belum aktif`** → open the GITET Indramayu SLD window first; the Master only starts listening once that window opens. The slave retries every 3 seconds.
- **Port 5000 already in use** → change `port = 5000` in **both** `master_node_withoutesp.py` and `slave_node.py` (they must match).
- **Blank map** → make sure `indonesia.geojson` is in the same folder as the scripts.
- **No data on the SLD** → check the terminal for Tx/Rx hex frames, and open the **TRACE** logger to see whether frames are being decoded.

## Notes

- Protocol flow: the Master sends a fixed-length request frame (`0x10 ... 0x16`) every 3 seconds; the slave replies with four variable-length ASDU frames (`0x68 LEN LEN 0x68 ... CS 0x16`), each carrying 4 measurement points (type ID `0x0D`, short-float values).
- `server_api.py`, `databasemaker.py`, `gitet_dummy.db`, and report documents are excluded via `.gitignore` — they are **not** needed to run this simulation.
