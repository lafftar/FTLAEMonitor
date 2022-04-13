# FTLAEMonitor
 
 Monitor that bypasses all WAF to monitor the entire stock information of FTL.AE and all Arab regions.

Compile to .exe and supporting files:
```bash
pyinstaller --clean -n FTLAEMonitor -i distro_assets/icon.ico --upx-dir C:\Users\lafft\Downloads\upx-3.96-win64\ --hidden-import colorama --hidden-import pywin32 --hidden-import win32file --onefile sku_monitor.py


pyinstaller --clean -n FTLAEBackendMonitor -i distro_assets/icon.ico --upx-dir C:\Users\lafft\Downloads\upx-3.96-win64\ --hidden-import colorama --hidden-import pywin32 --hidden-import win32file --onefile main.py


# remove cached stuff, like, in committed but newly added to the gitignore
git ls-files -i -c --exclude-from=.gitignore | %{git rm --cached $_}
```
