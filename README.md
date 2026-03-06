# Robowrist-client

Robowrist-client is a cross‑platform desktop tool (Windows / macOS / Linux) built with PyQt5.  
It lets you:

- synchronize the RV1106 hardware RTC with host network time (NTP or system time)
- browse, upload, download, rename and delete files under `/mnt/sdcard` on the device
- format the SD card on the device (with explicit confirmation)

It is designed for end users: you can ship a prebuilt package that does not require Python or adb to be installed on the target machine.

---

## 1. System requirements

- Python 3.7+ (for development and building only)
- A Robowrist device (RV1106) with adb enabled (USB or network)
- On the device: `date`, `hwclock`, `ls`, `mount`, `umount`, `mkfs.vfat`

---

## 2. Running from source (for developers)

```bash
# clone or enter the project directory
cd robowrist-controlcenter

# create local virtual environment (recommended)
python -m venv .venv
.venv\Scripts\activate           # Windows
# source .venv/bin/activate      # macOS / Linux

# install dependencies
pip install -r requirements.txt

# run the app from project root
python -m src.main
```

The app will use the bundled `adb` binaries under `adb/windows`, `adb/macos`, or `adb/linux` if present;  
otherwise it falls back to the `adb` found in your system `PATH`.

You can download the official Android platform‑tools from the Android developer site and drop the `adb` binary into the corresponding folder.

---

## 3. Building a one‑click package

Each platform must be built on its own OS. All build artifacts stay inside the project directory:

- dependencies go into `.venv/`
- adb binaries go into `adb/`
- build cache goes into `build/`
- final output executables go into `dist/`

### Windows

```bash
build_win.bat
```

### macOS / Linux

```bash
chmod +x build_mac.sh build_linux.sh
./build_mac.sh
./build_linux.sh
```

The scripts perform these steps:

1. create `.venv` under the project (if not present)
2. install Python dependencies into `.venv`
3. automatically download Android platform‑tools (`adb`) into `adb/`
4. run PyInstaller and place executables into `dist/`
5. copy `adb/` into `dist/adb/`

Resulting layout:

```text
dist/
  RobowristControlCenter.exe    # or macOS / Linux executable
  adb/
    windows/ | macos/ | linux/
      adb.exe / adb             # plus Windows DLLs if applicable
```

You can zip the entire `dist` directory and distribute it to end users.  
They can simply unpack and run the executable without installing Python or adb.

---

## 4. Using the tool

1. Connect your Robowrist device via USB or configure network adb.
2. Start **Robowrist Control Center**.
3. Click **Refresh devices** and select your device from the list.

### 4.1 Time synchronization

1. Go to the **Time sync** tab.
2. Click **Sync time to RTC**.
3. The app will fetch host network time (NTP if available, otherwise system time) and run:
   - `date -s "YYYY-MM-DD HH:MM:SS"`
   - `hwclock -w`

Your device must allow these commands (typically root or properly configured sudo).

### 4.2 Device storage (/mnt/sdcard)

1. Go to the **Device storage (/mnt/sdcard)** tab.
2. Use the toolbar to:
   - **New folder**: create a folder in the current directory
   - **Upload**: select files on the host and upload to the current directory
   - **Download**: download selected files/folders to a directory on the host
   - **Delete**: remove selected files/folders
   - **Rename**: rename a single selected item
   - **Format SD card**: unmount `/mnt/sdcard`, format `/dev/mmcblk0p1` as FAT32
     with label `RoboWrist`, then mount it back on `/mnt/sdcard`

Formatting the SD card permanently erases its contents. The UI asks for confirmation before running the command.

---

## 5. Project layout

```text
robowrist-controlcenter/
├── src/
│   ├── main.py              # application entry point
│   ├── ui/
│   │   ├── main_window.py   # main window with tabs
│   │   └── sdcard_panel.py  # /mnt/sdcard “USB‑like” file manager
│   └── core/
│       ├── config.py        # platform and adb configuration
│       ├── adb.py           # AdbClient and helper functions
│       ├── time_sync.py     # TimeSyncService
│       └── sdcard_fs.py     # SD card filesystem helpers
├── adb/
│   ├── windows/
│   ├── macos/
│   └── linux/
├── requirements.txt
├── build.spec
├── build_win.bat / build_mac.sh / build_linux.sh
└── README.md
```

---

## 6. License

Choose and add a license that matches your project’s needs (for example MIT, Apache‑2.0, etc.).
