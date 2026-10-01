@echo off
call "C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvars64.bat"
if errorlevel 1 exit /b 1
"D:\workspace\ck3_eternal_recurrence\tools\.venv\Scripts\python.exe" -X utf8 -B "C:\Users\1\ck3-a04-mechanism-evidence-20261001\R0141-ui-hidden-modal-repair-other-a01\build_and_test_a01.py"
exit /b %errorlevel%
