# Auto-Export-DWS-DATA
<img width="419" height="230" alt="image" src="https://github.com/user-attachments/assets/59fec8c2-c8b6-4841-b2e7-d9492429abfe" />

# Auto Export DWS Data

Python application สำหรับ export ข้อมูล DWS (Dimension Weight Scanner) จาก MySQL Database อัตโนมัติ พร้อมระบบ Auto Schedule, System Tray, Retry Recovery และ Export เป็น Excel (`.xlsx`)

รองรับการทำงานแบบ background service บน Windows และสามารถ build เป็น `.exe` เพื่อใช้งานจริงใน production environment ได้

---

# Features

- Auto export ข้อมูลจาก MySQL Database
- Export เป็น Excel (`.xlsx`)
- ตั้งเวลา export อัตโนมัติทุก X ชั่วโมง
- รองรับ Time Range แบบ:
  - Last 24 Hours
  - Custom Time Range
- System Tray Mode
- Auto hide window เมื่อเปิดโปรแกรม
- Config ผ่าน `config.ini`
- Auto create log file
- Auto reconnect database
- Retry connection เมื่อ DB หลุด
- Auto restart application เมื่อ error ต่อเนื่อง
- Multi-threaded worker
- GUI ด้วย Tkinter
- รองรับ build เป็น Windows EXE

---

# Application Overview

โปรแกรมนี้ถูกออกแบบมาเพื่อดึงข้อมูล package sorting จากระบบ DWS ผ่าน MySQL Database และ export ออกเป็นไฟล์ Excel แบบอัตโนมัติ

เหมาะสำหรับ:

- Warehouse
- Logistics Hub
- Parcel Sorting Center
- DWS Machine Integration
- Internal Data Collection System

---

# Tech Stack

- Python
- Tkinter
- Pandas
- PyMySQL
- XlsxWriter
- PyStray
- Pillow

---

# Project Structure

```text
project/
│
├── main.py
├── config.ini
├── logs/
│   └── dws_YYYY-MM-DD.log
│
└── export/
    └── DWS_EXPORT.xlsx
```

---

# Database Query

โปรแกรมจะ query ข้อมูลจาก table:

```sql
packagesinfos
```

ข้อมูลที่ export:

| Column | Description |
|---|---|
| barcode | Tracking Number |
| taskNo | Task Number |
| weight | Weight |
| length | Length |
| width | Width |
| height | Height |
| volume | Volume |
| sortTime | Sort Time |
| sortingPort | Sorting Port |
| sortingState | Sorting Status |
| uploadState | Upload Status |

---

# Working Logic

## Startup Flow

```text
Program Start
    ↓
Load config.ini
    ↓
Create Tray Icon
    ↓
Hide Main Window
    ↓
Start Worker Thread
    ↓
Force Export Immediately
    ↓
Wait Until Next Hour
    ↓
Scheduled Export Loop
```

---

# Time Range Modes

## 1. Last 24 Hours

โปรแกรมจะ export ข้อมูลย้อนหลัง 24 ชั่วโมงจากเวลาปัจจุบัน

```text
NOW - 24 HOURS → NOW
```

---

## 2. Custom Time Range

สามารถกำหนดช่วงเวลาเองได้ เช่น:

```text
13:00 → 07:00
```

รองรับกรณี "ข้ามวัน" อัตโนมัติ

ตัวอย่าง:

| Start | End | Result |
|---|---|---|
| 08:00 | 18:00 | Same Day |
| 14:00 | 09:00 | Cross Day |

---

# Auto Retry System

เมื่อ Database Connection ล้มเหลว:

- Retry อัตโนมัติ
- Default Retry Count = 3
- Delay ระหว่าง Retry = 10 วินาที

```python
self.db_retry_count = 3
self.db_retry_delay = 10
```

---

# Auto Recovery System

หากเกิด error ต่อเนื่องเกินจำนวนที่กำหนด:

```python
self.max_consecutive_errors = 5
```

โปรแกรมจะ:

- restart ตัวเองอัตโนมัติ
- ป้องกัน worker dead
- ลดปัญหา long-running process crash

---

# Log System

ระบบจะสร้าง log อัตโนมัติที่:

```text
logs/dws_YYYY-MM-DD.log
```

ตัวอย่าง:

```text
2026-05-17 10:00:00 - Program launched
2026-05-17 10:00:01 - DB connected
2026-05-17 10:00:05 - Export success
```

---

# Excel Export

ไฟล์ export จะถูกสร้างเป็น:

```text
DWS_EXPORT.xlsx
```

โดยใช้:

```python
pandas + xlsxwriter
```

และมีการ force format datetime เพื่อป้องกัน Excel แปลง format อัตโนมัติ

---

# Configuration

## config.ini

```ini
[DATABASE]
host=localhost
port=3306
user=root
password=1234
database=test
charset=utf8

[EXPORT]
interval_hours=1
export_folder=C:/DWS_EXPORT
file_prefix=DWS_EXPORT

[TIME]
mode=24h
start_time=13:00
end_time=07:00
end_mode=now
```

---

# ▶️ Installation

## 1. Clone Repository

```bash
git clone https://github.com/yourname/dws-exporter.git
```

---

## 2. Install Dependencies

```bash
pip install pandas pymysql xlsxwriter pillow pystray
```

---

## 3. Run Application

```bash
python main.py
```

---

# Build EXE

ใช้ PyInstaller:

```bash
pyinstaller --onefile --noconsole main.py
```

หรือ:

```bash
pyinstaller --onefile --windowed main.py
```

---

# GUI Features

- Start / Stop Export
- Export Interval Setting
- Time Range Selection
- Export Folder Browser
- File Name Setting
- Tray Minimize
- Auto Background Running

---

# Threading Design

โปรแกรมใช้:

```python
threading.Thread()
```

เพื่อแยก GUI Thread ออกจาก Worker Thread

ข้อดี:

- GUI ไม่ค้าง
- Export background ได้
- รองรับ long-running process

---

# Important Notes

- โปรแกรมถูกออกแบบสำหรับ Windows
- รองรับการทำงานแบบ background
- เหมาะสำหรับเครื่องที่เปิดใช้งานตลอดเวลา
- แนะนำให้ใช้งานร่วมกับ UPS สำหรับ production environment

---

# Future Improvements

- Multi Export Profiles
- CSV Export
- Email Notification
- Auto Upload FTP
- Database Health Monitor
- GUI Log Viewer
- Schedule Calendar
- Multi Database Support

---

# License

MIT License

---

# Author

Developed for warehouse automation and DWS export workflow optimization.
