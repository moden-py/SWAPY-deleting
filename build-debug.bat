set home=%cd%
C:\Python27\Scripts\pyinstaller.exe --clean swapy-debug.spec
copy dist\swapy-debug.exe %home%\swapy32bit-debug.exe

C:\Python27x64\Scripts\pyinstaller.exe --clean swapy-debug.spec
copy dist\swapy-debug.exe %home%\swapy64bit-debug.exe
