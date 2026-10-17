"""Isolate exact production pure function bodies; never rewrite an envelope."""
from pathlib import Path
import argparse,datetime,hashlib,json,re

def end_of_function(text,start):
 pos=text.index('{',start);depth=0;state='code';i=pos
 while i<len(text):
  c=text[i];n=text[i+1:i+2]
  if state=='line':
   if c=='\n':state='code'
  elif state=='block':
   if c=='*' and n=='/':state='code';i+=1
  elif state in ('string','char'):
   if c=='\\':i+=1
   elif c==('"' if state=='string' else "'"):state='code'
  elif c=='/' and n=='/':state='line';i+=1
  elif c=='/' and n=='*':state='block';i+=1
  elif c=='"':state='string'
  elif c=="'":state='char'
  elif c=='{':depth+=1
  elif c=='}':
   depth-=1
   if depth==0:return i+1
  i+=1
 raise ValueError('Unclosed production function')

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--repo',type=Path,required=True);p.add_argument('--overlay',type=Path,required=True)
 p.add_argument('--output',type=Path,required=True);p.add_argument('--manifest',type=Path,required=True)
 a=p.parse_args();manifest=[]
 def source(relative):
  path=a.overlay/relative
  return path if path.is_file() else a.repo/relative
 def extract(relative,name,constant=False):
  path=source(relative);raw=path.read_bytes();bom=3 if raw.startswith(b'\xef\xbb\xbf') else 0;text=raw[bom:].decode('utf-8')
  prefix=r'^(?:constexpr\s+)?(?:bool|void|std::string|std::string_view|std::uint32_t)\s+'
  pattern=prefix+re.escape(name)+(r'\s*=' if constant else r'\s*\(')
  matches=list(re.finditer(pattern,text,re.MULTILINE))
  if len(matches)!=1:raise ValueError(f'{relative} {name}: {len(matches)} declarations')
  start=matches[0].start();end=text.index(';',matches[0].end())+1 if constant else end_of_function(text,start)
  body=text[start:end];begin_byte=bom+len(text[:start].encode('utf-8'));end_byte=bom+len(text[:end].encode('utf-8'))
  if raw[begin_byte:end_byte]!=body.encode('utf-8'):raise ValueError('exact source-byte extraction drift')
  manifest.append(dict(path=str(path),source_file_sha256=hashlib.sha256(raw).hexdigest(),symbol=name,begin_byte=begin_byte,end_exclusive_byte=end_byte,bytes_sha256=hashlib.sha256(raw[begin_byte:end_byte]).hexdigest(),byte_identical=True))
  return body+'\n'
 nav='ck3_autonomous_player/native_bridge/src/ingame_ui_navigation_v1.cpp'
 army='ck3_autonomous_player/native_bridge/src/army_tooltip_v1.inc'
 app='ck3_autonomous_player/native_bridge/src/appointment_window_snapshot_v1.cpp'
 mailbox='ck3_autonomous_player/native_bridge/src/ingame_ui_mailbox_v1.cpp'
 output='''// GENERATED from exact production function bodies; fixture only. Do not edit.
#include "xar_bridge/ingame_ui_mailbox_v1.hpp"
#include "xar_bridge/holy_site_relic_request12004.hpp"
#include "xar_bridge/ck3_12003.hpp"
#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/protocol.hpp"
#include <algorithm>
#include <array>
#include <iomanip>
#include <limits>
#include <sstream>
#include <string>
namespace xar::ck3_11906 {
namespace {
'''
 for relative,name,constant in [(nav,'IsModernArmyUiV1',False),(nav,'JsonEscape',False),(nav,'kStockCombatGuiSha256',True),(army,'ArmyTooltipNonceValid',False),(army,'SerializeArmyTooltip',False),(app,'kMaximumPool',True),(app,'Escape',False),(app,'TreeJson',False)]:output+=extract(relative,name,constant)
 output+='}\n'
 for relative,name in [(app,'ValidateAppointmentWindowRequestV1'),(app,'SerializeAppointmentWindowSnapshotV1'),(nav,'ValidateIngameUiRequestV1'),(nav,'IsIngameUiRequestSupportedV1'),(nav,'ParseIngameUiRequestV1'),(nav,'IngameUiWindowNameV1'),(nav,'SerializeIngameUiResultV1'),(mailbox,'IngameUiCommandResultFrameV1')]:output+=extract(relative,name)
 output+='}\n';a.output.parent.mkdir(parents=True,exist_ok=True)
 with a.output.open('x',encoding='utf-8',newline='') as f:f.write(output)
 value=dict(machine_id='4-8e1c2f1861',observed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
  status='EXACT_SOURCE_PURE_FUNCTION_ISOLATION',production_function_logic_changed=False,fixture_wrapper_admission_injected=True,
  full_dll_linked=False,game_engine_code_executed=False,source_spans=manifest,
  generated_path=str(a.output),generated_sha256=hashlib.sha256(a.output.read_bytes()).hexdigest())
 with a.manifest.open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,indent=2);f.write('\n')
 print(json.dumps(dict(functions=len(manifest),generated_sha256=value['generated_sha256'])))

if __name__=='__main__':main()
