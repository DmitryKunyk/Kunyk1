@echo off
setlocal
python -m pip install --upgrade pip
python -m pip install -r requirements.txt pyinstaller
pyinstaller --noconfirm dynsys_pro.spec
echo Done. EXE is in dist\DynSysPro.exe
endlocal
