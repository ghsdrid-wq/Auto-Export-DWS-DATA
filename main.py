import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import configparser
import threading
import time
from datetime import datetime, timedelta
import os
import pymysql
import pandas as pd
import sys
import pystray
from PIL import Image, ImageDraw

class DWSExporterApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Auto Export DWS Data")
        self.resizable(False, False)

        # ======================
        # Load config.ini
        # ======================
        BASE_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))
        CONFIG_PATH = os.path.join(BASE_DIR, "config.ini")

        self.cfg = configparser.ConfigParser()

        if os.path.exists(CONFIG_PATH):
            self.cfg.read(CONFIG_PATH, encoding="utf-8")
        else:
            # ถ้าไม่มีไฟล์ ให้สร้าง config.ini เปล่า ๆ ไว้ข้าง exe
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                f.write("")
            self.cfg.read(CONFIG_PATH, encoding="utf-8")
        
        self.cfg.setdefault("DATABASE", {
            "host": "localhost",
            "port": "1111",
            "user": "abc",
            "password": "abc",
            "database": "abc",
            "charset": "utf8"
        })
        self.cfg.setdefault("EXPORT", {})
        self.cfg.setdefault("TIME", {})
        
        # ======================
        # Variables
        # ======================
        self.interval_var = tk.StringVar(value=self.cfg["EXPORT"].get("interval_hours", "1"))
        self.export_folder_var = tk.StringVar(value=self.cfg["EXPORT"].get("export_folder", "C:/DWS_EXPORT"))
        self.file_prefix_var = tk.StringVar(value=self.cfg["EXPORT"].get("file_prefix", "DWS_EXPORT"))

        self.time_mode_var = tk.StringVar(value=self.cfg["TIME"].get("mode", "24h"))
        self.end_mode_var = tk.StringVar(value=self.cfg["TIME"].get("end_mode", "now"))
        self.start_time_var = tk.StringVar(value=self.cfg["TIME"].get("start_time", "13:00"))
        self.end_time_var = tk.StringVar(value=self.cfg["TIME"].get("end_time", "07:00"))

        self.running = False

        self.create_widgets()
        self.toggle_time_mode()

        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.after(1000, self.start_job)
        self.after(500, self.hide_window)
        self.after(500, self.create_tray_icon)

        self.withdraw()   # ซ่อนตั้งแต่เปิด

        self.db_retry_count = 3      # จำนวนครั้งที่ retry
        self.db_retry_delay = 10     # หน่วงวินาทีต่อครั้ง

        self.consecutive_errors = 0
        self.max_consecutive_errors = 5   # ปรับได้ เช่น 3 / 5 / 10

        self.write_log("Program launched")   # FIX: log ตอนเปิดโปรแกรม
    # ======================================================
    # UI
    # ======================================================
    def create_widgets(self):
        row = 0

        ttk.Label(self, text="Export Interval (Hours)").grid(row=row, column=0, sticky="w", padx=8, pady=6)
        ttk.Entry(self, textvariable=self.interval_var, width=10).grid(row=row, column=1, sticky="w")
        row += 1

        ttk.Label(self, text="Time Range").grid(row=row, column=0, sticky="w", padx=8)
        ttk.Radiobutton(self, text="Last 24 Hours", variable=self.time_mode_var,
                        value="24h", command=self.toggle_time_mode).grid(row=row, column=1, sticky="w")
        ttk.Radiobutton(self, text="Custom", variable=self.time_mode_var,
                        value="custom", command=self.toggle_time_mode).grid(row=row, column=2, sticky="w")
        row += 1

        ttk.Label(self, text="Start Time (HH:MM)").grid(row=row, column=0, sticky="w", padx=8)
        self.start_time_entry = ttk.Entry(self, textvariable=self.start_time_var, width=12)
        self.start_time_entry.grid(row=row, column=1, sticky="w")
        row += 1

        ttk.Label(self, text="End Time").grid(row=row, column=0, sticky="w", padx=8)
        self.end_now_radio = ttk.Radiobutton(self, text="Now",
                                             variable=self.end_mode_var,
                                             value="now", command=self.toggle_end_time)
        self.end_now_radio.grid(row=row, column=1, sticky="w")
        self.end_custom_radio = ttk.Radiobutton(self, text="Custom",
                                                variable=self.end_mode_var,
                                                value="custom", command=self.toggle_end_time)
        self.end_custom_radio.grid(row=row, column=2, sticky="w")
        row += 1

        self.end_time_entry = ttk.Entry(self, textvariable=self.end_time_var, width=12)
        self.end_time_entry.grid(row=row, column=1, sticky="w")
        row += 1

        ttk.Label(self, text="File Name").grid(row=row, column=0, sticky="w", padx=8)
        ttk.Entry(self, textvariable=self.file_prefix_var, width=25).grid(row=row, column=1, columnspan=2, sticky="w")
        row += 1

        ttk.Label(self, text="Export Folder").grid(row=row, column=0, sticky="w", padx=8)
        ttk.Entry(self, textvariable=self.export_folder_var, width=30).grid(row=row, column=1, columnspan=2, sticky="w")
        ttk.Button(self, text="Browse", command=self.browse_folder).grid(row=row, column=3, padx=5)
        row += 1

        self.start_btn = ttk.Button(self, text="Start", command=self.start_job)
        self.stop_btn = ttk.Button(self, text="Stop", command=self.stop_job)
        self.start_btn.grid(row=row, column=1, pady=12, sticky="ew")
        self.stop_btn.grid(row=row, column=1, pady=12, sticky="ew")
        self.stop_btn.grid_remove()

    # ======================================================
    # UI Logic
    # ======================================================
    def toggle_time_mode(self):
        if self.time_mode_var.get() == "24h":
            self.start_time_entry.config(state="disabled")
            self.end_time_entry.config(state="disabled")
            self.end_now_radio.config(state="disabled")
            self.end_custom_radio.config(state="disabled")
        else:
            self.start_time_entry.config(state="normal")
            self.end_now_radio.config(state="normal")
            self.end_custom_radio.config(state="normal")
            self.toggle_end_time()

    def toggle_end_time(self):
        self.end_time_entry.config(
            state="normal" if self.end_mode_var.get() == "custom" else "disabled"
        )

    # ======================================================
    # Actions
    # ======================================================
    def browse_folder(self):
        path = filedialog.askdirectory()
        if path:
            self.export_folder_var.set(path)

    def start_job(self):
        if self.running:        # FIX: กัน start ซ้ำ
            return
        try:
            self.export_interval_hours = int(float(self.interval_var.get()))
        except ValueError:
            messagebox.showerror("Error", "Interval must be numeric")
            return

        self.write_log("Start job")
        self.save_config()
        self.running = True

        for w in self.winfo_children():
            if isinstance(w, (ttk.Entry, ttk.Radiobutton, ttk.Button)):
                w.config(state="disabled")

        self.stop_btn.config(state="normal")
        self.stop_btn.grid()
        self.start_btn.grid_remove()

        threading.Thread(target=self.run_loop, daemon=True).start()

    def stop_job(self):
        self.write_log("Stop job")
        self.running = False
        for w in self.winfo_children():
            if isinstance(w, (ttk.Entry, ttk.Radiobutton, ttk.Button)):
                w.config(state="normal")

        self.start_btn.grid()
        self.stop_btn.grid_remove()
        self.toggle_time_mode()

    # ======================================================
    # Worker
    # ======================================================
    def run_loop(self):
        self.write_log("Worker thread started")

        # 🔥 EXPORT ทันทีเมื่อโปรแกรม start (ไม่สนเวลา)
        try:
            self.write_log("Force export on startup")
            self.export_database()
            self.write_log("Startup export finished")
        except Exception as e:
            self.write_log(f"Startup export error: {e}")

        while self.running:
            self.write_log("Waiting until next hour")
            self.sleep_until_next_hour()

            if not self.running:
                break

            self.write_log("Scheduled export")
            self.export_database()
            
            '''if self.is_in_working_time():
                self.write_log("In working time → export")
                self.export_database()
            else:
                self.write_log("Out of working time → skip export")'''

            for _ in range(self.export_interval_hours - 1):
                if not self.running:
                    break
                time.sleep(3600)


    def write_log(self, msg):
        try:
            BASE_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))  # FIX (optional)
            log_dir = os.path.join(BASE_DIR, "logs")                   # FIX (optional)
            os.makedirs(log_dir, exist_ok=True)

            today = datetime.now().strftime("%Y-%m-%d")
            log_file = os.path.join(log_dir, f"dws_{today}.log")

            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"{datetime.now():%Y-%m-%d %H:%M:%S} - {msg}\n")
        except:
            pass


    def sleep_until_next_hour(self):
        now = datetime.now()
        next_hour = (now + timedelta(hours=1)).replace(
            minute=0,
            second=0,
            microsecond=0
        )
        time.sleep((next_hour - now).total_seconds())

    def create_tray_icon(self):
        image = Image.new("RGB", (64, 64), "white")
        draw = ImageDraw.Draw(image)
        draw.rectangle((16, 16, 48, 48), fill="black")

        menu = pystray.Menu(
            pystray.MenuItem("Show", self.show_window),
            pystray.MenuItem("Exit", self.exit_app)
        )

        self.tray = pystray.Icon("DWS Export", image, "DWS Export", menu)
        threading.Thread(target=self.tray.run, daemon=True).start()

    def hide_window(self):
        self.withdraw()

    def show_window(self):
        self.deiconify()

    def exit_app(self):
        self.running = False
        self.tray.stop()
        self.destroy()

    def on_close(self):
        self.withdraw()

    '''
    def is_in_working_time(self):
        
        #ตรวจสอบว่าเวลาปัจจุบันอยู่ในช่วงเวลาทำงานหรือไม่
        #รองรับกรณีข้ามวัน เช่น 14:00 -> 09:00     
        now = datetime.now().time()

        start_h, start_m = map(int, self.start_time_var.get().split(":"))
        end_h, end_m = map(int, self.end_time_var.get().split(":"))

        start_time = datetime.strptime(
            f"{start_h}:{start_m}", "%H:%M"
        ).time()

        end_time = datetime.strptime(
            f"{end_h}:{end_m}", "%H:%M"
        ).time()

        if start_time <= end_time:
            # ไม่ข้ามวัน (เช่น 08:00 - 18:00)
            return start_time <= now <= end_time
        else:
            # 🔥 ข้ามวัน (เช่น 14:00 - 09:00)
            return now >= start_time or now <= end_time
    '''
    def restart_self(self):
        self.write_log("!!! Restarting application due to consecutive errors !!!")
        time.sleep(10)   # FIX: กัน restart loop
        try:
            python = sys.executable
            os.execv(python, [python] + sys.argv)
        except Exception as e:
            self.write_log(f"Restart failed: {e}")



    # ======================================================
    # DATABASE EXPORT (REAL)
    # ======================================================
    def export_database(self):
        now = datetime.now()

        if self.time_mode_var.get() == "24h":
            start_dt = now - timedelta(hours=24)
            end_dt = now
        else:
            start_h, start_m = map(int, self.start_time_var.get().split(":"))
            end_h, end_m = map(int, self.end_time_var.get().split(":"))

            today = now.date()

            # ค่าเริ่มต้น (สมมติวันเดียวกันก่อน)
            start_dt = datetime.combine(today, datetime.min.time()).replace(
                hour=start_h, minute=start_m
            )

            if self.end_mode_var.get() == "now":
                end_dt = now

                # 🔴 FIX สำคัญ: ถ้า now < start → start เป็น "เมื่อวาน"
                if now < start_dt:
                    start_dt -= timedelta(days=1)
            else:
                end_dt = datetime.combine(today, datetime.min.time()).replace(
                    hour=end_h, minute=end_m
                )
                # end < start → end ข้ามวัน
                if end_dt <= start_dt:
                    # ถ้า end < ตอนนี้ → แปลว่า end คือ "วันนี้"
                    if end_dt.time() <= now.time():
                        start_dt -= timedelta(days=1)
                    else:
                        end_dt += timedelta(days=1)
                if start_dt > now:
                    start_dt -= timedelta(days=1)
                    
        db_cfg = self.cfg["DATABASE"]
        conn = None
        for attempt in range(1, self.db_retry_count + 1):
            try:
                self.write_log(f"DB connect attempt {attempt}")
                conn = pymysql.connect(
                    host=db_cfg.get("host"),
                    port=int(db_cfg.get("port")),
                    user=db_cfg.get("user"),
                    password=db_cfg.get("password"),
                    database=db_cfg.get("database"),
                    charset=db_cfg.get("charset"),
                    connect_timeout=5
                )
                self.write_log("DB connected")
                break
            except Exception as e:
                self.write_log(f"DB connect failed ({attempt}): {e}")
                time.sleep(self.db_retry_delay)

        if conn is None:
            self.write_log("DB connect failed - give up this round")

            self.consecutive_errors += 1              # FIX
            self.write_log(f"Consecutive errors = {self.consecutive_errors}")  # FIX

            if self.running and self.consecutive_errors >= self.max_consecutive_errors:
                self.restart_self()

            return
        try:
            sql = """
            SELECT
                barcode AS '单号',
                taskNo AS 'taskNo',
                weight AS '重量(kg)',
                length AS '长度(cm)',
                width AS '宽度(cm)',
                height AS '高度(cm)',
                volume AS '体积(cm³)',
                sortTime AS '出秤时间',
                sortingPort AS '分拣口',

                CASE sortingState
                    WHEN 1 THEN '分拣成功'
                    WHEN 5 THEN '回流'
                    ELSE '未知'
                END AS '分拣状态',

                CASE uploadState
                    WHEN 1 THEN 'Uploaded'
                    ELSE '未上传'
                END AS '上传状态',

                '' AS '异常详情'

            FROM packagesinfos
            WHERE sortTime BETWEEN %s AND %s
            ORDER BY sortTime;
            """
            df = pd.read_sql(sql, conn, params=[start_dt, end_dt])
            self.write_log(f"Query success: {len(df)} rows")

        except Exception as e:
            self.write_log(f"Query failed: {e}")

            self.consecutive_errors += 1              # FIX
            self.write_log(f"Consecutive errors = {self.consecutive_errors}")  # FIX

            if self.running and self.consecutive_errors >= self.max_consecutive_errors:
                self.restart_self()

            return

        finally:
            conn.close()

        # ======================
        # 🔥 FORCE FORMAT
        # ======================

        # 1) แปลง datetime → string format ที่กำหนด
        try:
            if "出秤时间" in df.columns:
                df["出秤时间"] = pd.to_datetime(
                    df["出秤时间"], errors="coerce"
                ).apply(
                    lambda x: (
                        f"{x.year}/{x.month}/{x.day} "
                        f"{x.hour}:{x.minute:02d}:{x.second:02d}"
                        if pd.notna(x) else ""
                    )
                )
        
            # 🔒 บังคับทุก column เป็น string
            df = df.astype(str)

            # ======================
            # Export Excel
            # ======================
            os.makedirs(self.export_folder_var.get(), exist_ok=True)
            filename = f"{self.file_prefix_var.get()}.xlsx"
            filepath = os.path.join(self.export_folder_var.get(), filename)

            with pd.ExcelWriter(filepath, engine="xlsxwriter") as writer:
                df.to_excel(writer, index=False, sheet_name="sheet1")

            self.write_log(f"Export success → {filepath}")
            self.consecutive_errors = 0   # FIX: reset error counter

        except Exception as e:
            self.write_log(f"Export failed: {e}")

            self.consecutive_errors += 1              # FIX
            self.write_log(f"Consecutive errors = {self.consecutive_errors}")  # FIX

            if self.running and self.consecutive_errors >= self.max_consecutive_errors:
                self.restart_self()

    # ======================================================
    # Config
    # ======================================================
    def save_config(self):
        self.cfg["EXPORT"]["interval_hours"] = self.interval_var.get()
        self.cfg["EXPORT"]["export_folder"] = self.export_folder_var.get()
        self.cfg["EXPORT"]["file_prefix"] = self.file_prefix_var.get()

        self.cfg["TIME"]["mode"] = self.time_mode_var.get()
        self.cfg["TIME"]["start_time"] = self.start_time_var.get()
        self.cfg["TIME"]["end_time"] = self.end_time_var.get()
        self.cfg["TIME"]["end_mode"] = self.end_mode_var.get()

        with open("config.ini", "w", encoding="utf-8") as f:
            self.cfg.write(f)


if __name__ == "__main__":
    DWSExporterApp().mainloop()
