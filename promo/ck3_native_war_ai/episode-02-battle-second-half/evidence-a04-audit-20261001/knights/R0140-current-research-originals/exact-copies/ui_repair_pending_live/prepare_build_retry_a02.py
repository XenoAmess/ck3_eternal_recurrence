from pathlib import Path
here=Path(__file__).parent
old=here/'build_and_test_a01.py'
text=old.read_text(encoding='utf-8')
text=text.replace("build-attempt-01-paused-original-ui-owner","build-attempt-02-paused-original-ui-owner")
text=text.replace("phase('vs-environment',['cmd.exe','/d','/s','/c',vscommand],env=env)",
                  "phase('vs-environment',['cmd.exe','/d','/c',str(HERE/'enter_vs_environment_a02.cmd')],env=env)")
with (here/'build_and_test_a02.py').open('x',encoding='utf-8',newline='\n') as f:f.write(text)
cmd='@echo off\ncall "C:\\Program Files\\Microsoft Visual Studio\\18\\Community\\VC\\Auxiliary\\Build\\vcvars64.bat"\nif errorlevel 1 exit /b 1\n"D:\\workspace\\ck3_eternal_recurrence\\tools\\.venv\\Scripts\\python.exe" -X utf8 "'+str(here/'export_vs_environment.py')+'"\n'
with (here/'enter_vs_environment_a02.cmd').open('x',encoding='utf-8',newline='\r\n') as f:f.write(cmd)
failure=(here/'build-attempt-01-paused-original-ui-owner/vs-environment-stderr.bin').read_bytes()
print(failure.decode('gb18030',errors='replace'))
print('New a02 wrapper created. Original environment RED preserved unchanged.')
