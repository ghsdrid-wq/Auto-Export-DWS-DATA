# STRUCTURE — Auto-Export-DWS-DATA

> ⚠️ **กฎการดูแลไฟล์นี้ (สำคัญ)**
> ทุกครั้งที่แก้ไขโค้ดใน repo นี้ — เปลี่ยน SQL/คอลัมน์, เปลี่ยน config key, เปลี่ยน logic ช่วงเวลา/retry/restart, หรือเพิ่มไฟล์ — **ต้องอัปเดต STRUCTURE.md นี้ให้ตรงกับโค้ดเสมอ**

## ภาพรวม
แอป GUI (**Tkinter**) ชื่อ *"Auto Export DWS Data"* — ดึงข้อมูล **DWS (packagesinfos)** จาก MySQL ออกเป็นไฟล์ Excel ตามรอบ (interval ชั่วโมง / ช่วง 24h หรือ custom) อัตโนมัติ รันใน system tray มี retry + auto-restart เมื่อ error ติดกันหลายครั้ง

## วิธีรัน / Entry point
- รัน: `python main.py` → คลาส `DWSExporterApp(tk.Tk)` เริ่มแบบซ่อนหน้าต่าง + tray, export ทันทีตอน start แล้ววนตามชั่วโมง
- รองรับ frozen exe (path อิง `sys.argv[0]`)

## โครงสร้างไฟล์
| ไฟล์ | หน้าที่ |
|------|---------|
| `main.py` | ทั้งโปรแกรม — UI, config, tray, `export_database()`, `run_loop()`, `restart_self()` |

## Logic สำคัญ
- `export_database()` — query ตาราง `packagesinfos` (barcode/weight/length/width/height/volume/sortTime/sortingPort + แปลง `sortingState`/`uploadState` เป็นข้อความจีน) ช่วง `sortTime BETWEEN start AND end` → เซฟ `<file_prefix>.xlsx` (xlsxwriter, ทุกคอลัมน์เป็น string)
- ช่วงเวลา: โหมด `24h` = ย้อนหลัง 24 ชม.; โหมด `custom` = ตาม start/end time (รองรับข้ามวัน)
- `run_loop()` — export ทันทีตอน start → จากนั้นทุกต้นชั่วโมง (`sleep_until_next_hour`) เว้นตาม `interval_hours`
- retry DB connect (`db_retry_count=3`, delay 10s); ถ้า error ติดกัน ≥ `max_consecutive_errors` (5) → `restart_self()` (`os.execv`)

## Config (`config.ini`)
- `[DATABASE]`: `host`, `port`, `user`, `password`, `database`, `charset`
- `[EXPORT]`: `interval_hours`, `export_folder` (default `C:/DWS_EXPORT`), `file_prefix` (DWS_EXPORT)
- `[TIME]`: `mode` (24h/custom), `start_time`, `end_time`, `end_mode` (now/custom)

## Dependencies
- `pymysql`, `pandas`, `xlsxwriter`, `pystray`, `Pillow`, `tkinter`

## ข้อควรระวัง
- SQL hardcode ตาราง/คอลัมน์ DWS (`packagesinfos`) — แก้ที่ `export_database()` ถ้า schema เปลี่ยน
- log รายวันที่ `logs/dws_<วันที่>.log`
- `is_in_working_time()` ถูกคอมเมนต์ไว้ (ปัจจุบัน export ทุกชั่วโมงไม่กรองช่วงเวลาทำงาน)
