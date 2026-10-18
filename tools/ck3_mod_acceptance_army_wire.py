"""Recover an already executed Army query from the existing host wire only.

mark() runs before the existing CaseClient request; recover() reads its bounded
new range. The returned object is the native result, not a fabricated Driver
packet. Callers use production expansion/normalization and their own fences.
"""
from pathlib import Path
import hashlib, json, os, stat

MAX_RANGE=32*1024*1024
STEP='query-army-strengths-v1'

def need(ok,why):
 if not ok:raise ValueError(why)

def identity(s):return (s.st_dev,s.st_ino)

def mark(path):
 p=Path(path).resolve(strict=True);need(p.is_file() and not p.is_symlink(),'actual regular host wire required')
 with p.open('rb') as stream:
  s=os.fstat(stream.fileno());need(stat.S_ISREG(s.st_mode),'regular host wire')
  if s.st_size:
   stream.seek(s.st_size-1);need(stream.read(1)==b'\n','wire append in progress; no query submitted by this reader')
 return {'path':str(p),'file_identity':list(identity(s)),'offset':s.st_size}

def recover(bookmark,compact,*,native_revision,army_ids,profile):
 need(type(compact) is dict and compact.get('accepted') is True and type(compact.get('query_sequence')) is int
  and 0<compact['query_sequence']<(1<<64),'actual accepted compact query sequence')
 need(profile in ('ordinary_core_v1','observed_history_full_v1') and compact.get('army_strengths_profile')==profile,
  'same actual query profile')
 need(type(native_revision) is int and native_revision>=0 and type(army_ids) is list
  and army_ids and all(type(i) is int and -(1<<31)<=i<(1<<31) and i!=-1 for i in army_ids)
  and len(set(army_ids))==len(army_ids),'typed actual native revision and Army IDs, including zero')
 p=Path(bookmark['path']);offset=bookmark['offset']
 need(type(offset) is int and offset>=0 and not p.is_symlink(),'actual wire bookmark')
 with p.open('rb') as stream:
  before=os.fstat(stream.fileno());size=before.st_size
  need(list(identity(before))==bookmark['file_identity'] and 0<=size-offset<=MAX_RANGE,'same wire file; bounded append range')
  stream.seek(offset);raw=stream.read(size-offset);after=os.fstat(stream.fileno())
  need(identity(before)==identity(after) and after.st_size>=size and len(raw)==size-offset,'wire replaced/truncated during bounded read')
 end=raw.rfind(b'\n')+1;complete=raw[:end];records=[];position=offset
 for line in complete.splitlines(keepends=True):
  value=json.loads(line);need(type(value) is dict,'actual wire JSON object')
  records.append((value,position,position+len(line),hashlib.sha256(line).hexdigest()));position+=len(line)
 responses=[r for r in records if r[0].get('direction')=='dll-to-python'
  and type(r[0].get('message')) is dict and r[0]['message'].get('type')=='command_result'
  and type(r[0]['message'].get('result')) is dict
  and r[0]['message']['result'].get('step')==STEP
  and type(r[0]['message']['result'].get('query_sequence')) is int
  and r[0]['message']['result']['query_sequence']==compact['query_sequence']]
 need(len(responses)==1,'unique already executed query result unavailable; never resubmit')
 response=responses[0];message=response[0]['message'];request_id=message.get('request_id')
 need(type(request_id) is str and request_id and message.get('protocol_version')==1 and message.get('ok') is True,
  'actual successful protocol response')
 requests=[r for r in records if r[0].get('direction')=='python-to-dll' and type(r[0].get('message')) is dict
  and r[0]['message'].get('type')=='execute_step' and r[0]['message'].get('request_id')==request_id]
 need(len(requests)==1 and requests[0][1]<response[1],'unique original request preceding response')
 request=requests[0];sent=request[0]['message'];result=message['result']
 need(sent.get('protocol_version')==1 and sent.get('step')==STEP
  and type(sent.get('expected_revision')) is int and sent['expected_revision']==native_revision
  and sent.get('army_strengths_profile')==profile and sent.get('army_ids')==army_ids,'original request scope/profile/native revision differs')
 for k in ('accepted','status','query_sequence','army_strengths_profile','army_observed_phase_coverage'):
  need(type(result.get(k)) is type(compact.get(k)) and result.get(k)==compact.get(k),'native/compact '+k)
 proof={'path':str(p),'file_identity':bookmark['file_identity'],'begin':offset,'end':offset+end,
  'bytes':end,'sha256':hashlib.sha256(complete).hexdigest(),'native_request_id':request_id,
  'query_sequence':compact['query_sequence'],'request_line':{'begin':request[1],'end':request[2],'sha256':request[3]},
  'response_line':{'begin':response[1],'end':response[2],'sha256':response[3]},
  'source':'existing shared host native-wire original range','complete_Driver_packet':False,'query_reissued':False}
 return result,proof
