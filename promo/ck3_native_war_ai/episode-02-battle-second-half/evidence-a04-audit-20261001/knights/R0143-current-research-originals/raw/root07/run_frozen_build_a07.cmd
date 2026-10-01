@echo off
setlocal
if "%~4"=="" exit /b 2
call "C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvars64.bat"
if errorlevel 1 exit /b 3
set PYTHONUTF8=0
set PYTHONIOENCODING=utf-8
set VSLANG=1033
"D:\workspace\ck3_eternal_recurrence\tools\.venv\Scripts\python.exe" -X utf8=0 -B "C:\Users\1\ck3-e2-six-gap-research-20261001\root-attempt-07-trace-diagnostic\build_frozen_research_a03.py" --source "%~1" --source-commit "%~2" --attempt "%~3" --targets-json "%~4"
exit /b %errorlevel%
