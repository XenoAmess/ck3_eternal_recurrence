from pathlib import Path

root = Path(__file__).resolve().parent
old = root / 'root_adjudicate_r11_a01.py'
source = old.read_text(encoding='utf8')
for before, after in (("body = (json.dumps(record,", "payload = (json.dumps(record,"),
                      (" + len(body) < 262144", " + len(payload) < 262144"),
                      ("stream.write(body)", "stream.write(payload)")):
    if source.count(before) != 1:
        raise ValueError('Expected one exact local-variable correction')
    source = source.replace(before, after)
target = root / 'root_adjudicate_r11_a02.py'
with target.open('x', encoding='utf8', newline='\n') as stream:
    stream.write(source)
print(str(target))
