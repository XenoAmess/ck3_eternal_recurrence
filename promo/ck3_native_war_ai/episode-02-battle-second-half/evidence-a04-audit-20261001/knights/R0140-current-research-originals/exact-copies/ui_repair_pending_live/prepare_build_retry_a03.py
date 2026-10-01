from pathlib import Path
here=Path(__file__).parent
text=(here/'build_and_test_a02.py').read_text(encoding='utf-8')
text=text.replace('build-attempt-02-paused-original-ui-owner','build-attempt-03-paused-original-ui-owner')
with (here/'build_and_test_a03.py').open('x',encoding='utf-8',newline='\n') as f:f.write(text)
print('a02 actual compile PASS and test RED preserved; a03 will verify corrected fixture inputs.')
