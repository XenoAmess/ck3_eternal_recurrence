"""Pure RAM composer. Caller owns input reads, admission, materialization and build."""
import hashlib
PINS={
"src/bridge.cpp":("f96ac18c2be47a0a6fc1ed3e8642b5a084053efb",1605122,"975cad765a74c388cfa9dd5849d82b0dbe3091e4b6aa39273138a50279970a7e"),
"src/ck3_12002_commands.cpp":("b6603bf6b3bb851efd25df963e44a2feb566560d",7628,"8d5806d2b57dc8d115bc6cb52ca7e4b6374e6be4b546ab813ea3b3b889324c2a"),
"CMakeLists.txt":("3a5b0f9506e3aacbc74879bde20486845562a82f",453519,"abeae6aec614db664faca9dfc6fb4f115f20865fa0faf6deebee15d690e2445f"),
"cmake/native30-runtime-source-macro-restore.cmake":("D:/codex-ck3-demos/2026-10-19-robert-v20261019-native30-camera01/attempt02/runtime-source-macro-restore.cmake",807,"e99511202bab46b24e37b9cf4b1e9d31eb6e9ce3612bf8f078dba131f05d2e02")}
MACRO="XAR_CK3_ENABLE_NATIVE_TIME_OBSERVER31"
NS="xar::ck3_12004::time_observer31"
HEADER='#include "xar_bridge/native_time_command_observer_12004.hpp"\n'
def guarded(text):
 return "#if defined("+MACRO+")\n"+text+"#endif\n"
def one(text,anchor,replacement):
 if text.count(anchor)!=1:raise ValueError("nonunique frozen anchor: "+repr(anchor))
 return text.replace(anchor,replacement,1)
def compose(inputs,leaves):
 for name,(_,size,digest) in PINS.items():
  b=inputs[name]
  if len(b)!=size or hashlib.sha256(b).hexdigest()!=digest:
   raise ValueError("frozen input drift: "+name)
 out={name:(value.encode("utf-8") if isinstance(value,str) else value)
      for name,value in leaves.items()}
 b=inputs["src/bridge.cpp"].decode("utf-8")
 b=one(b,"#include <chrono>\n","#include <chrono>\n"+guarded(HEADER))
 a="  previous_snapshot.reset();\n  published_checkpoint_sequence = 0;\n"
 b=one(b,a,a+guarded("  const auto time_observer_connection = "+NS+"::BeginConnection();\n"))
 for name,paused in (("pause-map","true"),("resume-map","false")):
  a=('        if (step == "pause-map") {\n' if paused=="true" else
     '          } else if (step == "resume-map") {\n')
  b=one(b,a,a+guarded("          "+NS+"::RequestScope time_request(\n"
      "              time_observer_connection, request_id, "+paused+");\n"))
 a='        trace_command_entry("step_parse_returned");\n'
 b=one(b,a,a+guarded(
  '        if (!early_step_dispatched && step == "observe-time-command-journal-v1") {\n'
  '          connected = write_frame(pipe, '+NS+'::DiagnosticFrame(request_id));\n'
  '          early_step_dispatched = true;\n'
  '        }\n'))
 a='#if defined(XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_PRIVATE_CANDIDATE_V1)\n    if (!xar::ck3_12002::InstallSwayCompletionExecution12004('
 before=guarded(
  '    '+NS+'::Environment time_observer_environment{};\n'
  '    time_observer_environment.image_base = base;\n'
  '    time_observer_environment.exact_build_admitted = true;\n'
  '    if ('+NS+'::Install(time_observer_environment, sha, true) !=\n'
  '        '+NS+'::InstallResult::active) return FALSE;\n')
 b=one(b,a,before+a);out["src/bridge.cpp"]=b.encode("utf-8")
 c=inputs["src/ck3_12002_commands.cpp"].decode("utf-8")
 a='#include "xar_bridge/ck3_12002_commands.hpp"\n'
 c=one(c,a,a+guarded(HEADER))
 a='  void *clone_storage = nullptr;\n'
 c=one(c,a,guarded('  '+NS+'::BridgeCloneScope time_clone_source(command);\n')+a)
 a='  *returned_storage = nullptr;\n'
 c=one(c,a,a+guarded(
  '  const auto time_queue_ticket = '+NS+'::IsPauseObject(queued_command) ?\n'
  '      '+NS+'::Enter('+NS+'::Kind::queue_enter,\n'
  '          queued_command, 0, channel_flags, true) : '+NS+'::Ticket{};\n'))
 a='      bindings.command_manager, &queued_command, channel_flags);\n'
 c=one(c,a,a+guarded('  '+NS+'::Return('+NS+'::Kind::queue_return,\n'
   '      time_queue_ticket, 0, true, accepted);\n'))
 out["src/ck3_12002_commands.cpp"]=c.encode("utf-8")
 m=inputs["CMakeLists.txt"].decode("utf-8")
 m+='\noption(XAR_ENABLE_NATIVE_TIME_OBSERVER31 "Observe CPause natural execution only" OFF)\n'
 m+='if(XAR_ENABLE_NATIVE_TIME_OBSERVER31)\n'
 m+='  target_sources(xar_ck3_12002_runtime PRIVATE\n'
 m+='    src/native_time_command_observer_12004.cpp\n'
 m+='    src/native_time_command_observer_12004_install.cpp)\n'
 for target in ("xar_ck3_12002_runtime","xar_ck3_bridge"):
  m+='  target_compile_definitions('+target+' PRIVATE '+MACRO+'=1)\n'
 m+='endif()\n'
 m+='\nif(NOT COMMAND xar_native30_restore_historical_main_source_defines)\n'
 m+='  include("${CMAKE_CURRENT_SOURCE_DIR}/cmake/native30-runtime-source-macro-restore.cmake")\nendif()\n'
 out["cmake/native30-runtime-source-macro-restore.cmake"]=inputs["cmake/native30-runtime-source-macro-restore.cmake"]
 out["CMakeLists.txt"]=m.encode("utf-8")
 return out
