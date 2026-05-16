# Auto-Export-DWS-DATA
<img width="419" height="230" alt="image" src="https://github.com/user-attachments/assets/59fec8c2-c8b6-4841-b2e7-d9492429abfe" />

Python automation system for exporting DWS sorting data from MySQL database into formatted Excel files automatically.

The application is designed for warehouse operation environments where sorting machine data must be periodically exported for reporting, analysis, auditing, or downstream processing.

---

## Features

- Automatic MySQL data export
- Scheduled hourly export
- Custom time range support
- Cross-day time handling
- Excel export automation
- UTF-8 / Chinese text support
- System tray background mode
- Auto restart protection
- Database retry system
- Consecutive error recovery
- Config persistence
- Hidden background operation
- Daily log generation
- EXE deployment ready

---

## System Workflow

```text
MySQL Database
        ↓
Query Sorting Data
        ↓
Process Time Range
        ↓
Format Export Data
        ↓
Generate Excel File
        ↓
Save to Export Folder


