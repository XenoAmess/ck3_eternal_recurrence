from pathlib import Path
p=Path(__file__).parent
raw=(p/'static_hover_target_RTTI_a01.py').read_text('utf-8')
raw=raw.replace("OUT/'exact'/rel", "OUT/'exact-a02'/rel")
raw=raw.replace("==body['native_ui_raw_return_receipt']['sha256']", "==body['native_ui_raw_return_receipt']['sha256'].upper()")
raw=raw.replace("'native-hover-static-RTTI-diagnosis-a01.json'", "'native-hover-static-RTTI-diagnosis-a02.json'")
with (p/'static_hover_target_RTTI_a02.py').open('x',encoding='utf-8',newline='\n') as f:f.write(raw)
