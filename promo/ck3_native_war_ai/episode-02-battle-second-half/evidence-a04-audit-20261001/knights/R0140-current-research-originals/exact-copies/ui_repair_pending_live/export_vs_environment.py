import json, os, pathlib, shutil
path=pathlib.Path(os.environ['CK3_UI_REPAIR_VS_ENV_PATH'])
keys=['PATH','INCLUDE','LIB','LIBPATH','SystemRoot','TEMP','TMP','VCToolsInstallDir','WindowsSdkDir','VSLANG']
payload={key:os.environ[key] for key in keys if key in os.environ}
assert shutil.which('cl')
with path.open('x',encoding='utf-8') as f:json.dump(payload,f,indent=2)
print('Verified VS environment exported; no inherited credential variables recorded.')
