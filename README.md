# FTLAEMonitor
 

Compile to .exe and supporting files:
```bash
pyinstaller --clean -n FTLAEMonitor -i distro_assets/icon.ico --upx-dir C:\Users\lafft\Downloads\upx-3.96-win64\ --hidden-import colorama --hidden-import pywin32 --hidden-import win32file --onefile sku_monitor.py
pyinstaller --clean -n FTLAEBackendMonitor -i distro_assets/icon.ico --upx-dir C:\Users\lafft\Downloads\upx-3.96-win64\ --hidden-import colorama --hidden-import pywin32 --hidden-import win32file --onefile backend_monitor.py
```

- Product can be either regular or discounted.
- 