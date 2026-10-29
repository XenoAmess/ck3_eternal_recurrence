package org.xar.ck3.control.wave3.development.constructionidentity;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.util.Base64;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Duration;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.finance.capture.PythonStdinCapture;

/** Executes unchanged original-source functions and their actual transport consumer with synthetic observations. */
public final class ConstructionIdentityGoldenCapture {
    private ConstructionIdentityGoldenCapture() { }

    /** repository, interpreter, selected golden-inputs.json, fresh output, actual machine ID. */
    public static void main(String[] arguments) throws IOException, InterruptedException {
        if (arguments.length != 5) { throw new IllegalArgumentException("repository python input-spec fresh-output machine-id required"); }
        Path repository = existing(arguments[0], true), python = existing(arguments[1], false);
        Path input = existing(arguments[2], false), output = Path.of(arguments[3]);
        String machine = arguments[4];
        StrictJson.require(machine.matches("[a-z0-9][a-z0-9-]{0,95}"), "explicit machine ID required");
        StrictJson.require(output.isAbsolute() && !Files.exists(output), "absolute fresh output required");
        existing(output.getParent().toString(), true);
        PythonStdinCapture.requireCompiledLauncher(ConstructionIdentityGoldenCapture.class,
                Path.of(property(PythonStdinCapture.CLASS_ROOT_PROPERTY)), Path.of(property("xar.capture.helperRoot")));
        if (Files.size(input) != 10_463) { throw new IOException("exact retained original input required"); }
        JsonNode spec = StrictJson.parse(Files.readAllBytes(input));
        StrictJson.require(spec.path("schema").asText().equals("xar.ck3.constructionidentity-golden-inputs/v1")
                && spec.path("match_cases").isArray() && spec.path("match_cases").size() == 10
                && spec.path("read_cases").isArray() && spec.path("read_cases").size() == 15,
                "original ten-match/fifteen-read input required");
        var pins = com.fasterxml.jackson.databind.node.JsonNodeFactory.instance.arrayNode();
        pins.add(pin(repository, "ck3_autonomous_player/src/xar_autoplayer/bridge/construction_process_identity_v1.py", 4733,
                "31f0f776d5b9790f4c4b2c972ddb696d186e53e09a63b1c943c979cd48473da9").toJson());
        pins.add(pin(repository, "ck3_autonomous_player/src/xar_autoplayer/environment.py", 58031,
                "5d29d19d44c83a5425fb75b97ddb118a6c51a1e1f1f98184570850ad94a6a582").toJson());
        pins.add(pin(repository, "ck3_autonomous_player/src/xar_autoplayer/bridge/domain_construction_private_transport_v1.py", 66026,
                "c36fd21d16b897304c08cd8f0a9b9d26b19178c2fbeb3e1fbcc7a4f0d456dd2e").toJson());
        pins.add(pin(repository, "ck3_autonomous_player/src/xar_autoplayer/bridge/driver.py", 20803,
                "eed449063debf1a84216a350f0178d64a9a6602bbfcc266298a810a9bb736fb6").toJson());
        pins.add(pin(repository, "tools/ck3_live_run_id.py", 18178,
                "8f95f3d24a9b853c38d6fe056bb04c006fce78fbf3cfd47e48f48f211979f4c1").toJson());
        pins.add(new ExactRef(input.toString(), 10_463, "65084ad53bfe7ec2e12677d7b903f5298b9fdbb5a248dc1cde1a537677f7700e").toJson());
        byte[] raw = PythonStdinCapture.run(new PythonStdinCapture.Invocation(python, repository, PROGRAM,
                List.of(repository.toString(), input.toString(), Base64.getEncoder().encodeToString(StrictJson.canonical(pins)), machine),
                Duration.ofSeconds(90), 65_536)).stdout();
        validateOutput(raw, machine);
        Files.write(output, raw, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE);
        System.out.println("constructionidentity: match_cases=10 read_cases=15 synthetic_only output_created");
    }

    static void validateOutput(byte[] raw, String machine) {
        JsonNode document = StrictJson.parse(raw);
        StrictJson.require(document.path("schema").asText().equals("xar.ck3.constructionidentity-golden/v1")
                && document.path("machine_id").asText().equals(machine)
                && document.path("synthetic_kernel_claims_not_live_measurement").isBoolean()
                && document.path("synthetic_kernel_claims_not_live_measurement").booleanValue()
                && StrictJson.integer(document.get("native_process_reads"), 0, 0) == 0
                && StrictJson.integer(document.get("game_calls"), 0, 0) == 0
                && StrictJson.integer(document.get("ledger_writes"), 0, 0) == 0
                && document.path("match_cases").isArray() && document.path("match_cases").size() == 10
                && document.path("read_cases").isArray() && document.path("read_cases").size() == 15
                && document.path("source_refs").isArray() && document.path("source_refs").size() == 6,
                "actual original synthetic-only producer document required");
        for (JsonNode row : document.path("source_refs")) { ExactRef.fromJson(row); }
        StrictJson.require(document.path("source_refs").get(0).path("sha256").asText()
                .equals("31f0f776d5b9790f4c4b2c972ddb696d186e53e09a63b1c943c979cd48473da9"), "original producer source required");
    }

    private static ExactRef pin(Path root, String relative, long bytes, String sha) { return new ExactRef(root.resolve(relative).toString(), bytes, sha); }
    private static String property(String name) {
        String value = System.getProperty(name);
        if (value == null || value.isBlank()) { throw new IllegalArgumentException("explicit " + name + " required"); }
        return value;
    }
    private static Path existing(String value, boolean directory) throws IOException {
        Path path = Path.of(value);
        StrictJson.require(path.isAbsolute(), "absolute capture path required");
        Path actual = path.toRealPath();
        if (directory ? !Files.isDirectory(actual) : !Files.isRegularFile(actual)) { throw new IOException("capture path role differs"); }
        return actual;
    }

    // Retained CONSTRUCTIONIDENTITY-CAPTURE-REQUEST06 script; exact source extraction is the oracle.
    private static final String PROGRAM = """
import sys,json,hashlib,datetime,copy,ast,types,os,re,base64
from datetime import datetime as Datetime,timedelta,timezone
from dataclasses import dataclass
from typing import Callable,Mapping
from pathlib import Path
root=Path(sys.argv[1])
pins=json.loads(base64.b64decode(sys.argv[3],validate=True))
for pin in pins:
 path=Path(pin['path'])
 if path.stat().st_size!=pin['bytes'] or hashlib.sha256(path.read_bytes()).hexdigest()!=pin['sha256']: raise RuntimeError('capture pin drift')
sys.path.insert(0,str(root/'tools'))
import ck3_live_run_id
machine=ck3_live_run_id.current_machine_id()
if machine!=sys.argv[4]: raise RuntimeError('capture machine drift')
module=types.ModuleType('construction_identity_original_oracle')
sys.modules[module.__name__]=module
ns=module.__dict__
ns.update(dataclass=dataclass,datetime=Datetime,timedelta=timedelta,timezone=timezone,os=os,re=re,Mapping=Mapping,Callable=Callable)
def extract(relative,names,kinds):
 tree=ast.parse((root/relative).read_text(encoding='utf-8-sig'))
 nodes=[node for node in tree.body if isinstance(node,kinds) and node.name in names]
 if len(nodes)!=len(names): raise RuntimeError('source extraction drift')
 exec(compile(ast.Module(body=nodes,type_ignores=[]),relative+':exact-extraction','exec'),ns)
extract('ck3_autonomous_player/src/xar_autoplayer/environment.py',{'process_creation_utc'},(ast.FunctionDef,))
extract('ck3_autonomous_player/src/xar_autoplayer/bridge/driver.py',{'BridgeUnavailableError'},(ast.ClassDef,))
extract('ck3_autonomous_player/src/xar_autoplayer/bridge/construction_process_identity_v1.py',{'_KernelIdentity','_ConstructionIdentityPin','_try_kernel_identity','_matches_wmi','read_construction_process_identity_v1'},(ast.FunctionDef,ast.ClassDef))
extract('ck3_autonomous_player/src/xar_autoplayer/bridge/domain_construction_private_transport_v1.py',{'_positive','_identity'},(ast.FunctionDef,))
def expand(value):
 if isinstance(value,str) and value.startswith('$CWD/'): return str(Path.cwd()/value[5:])
 if isinstance(value,dict): return {key:expand(item) for key,item in value.items()}
 if isinstance(value,list): return [expand(item) for item in value]
 return value
def kernel(value):
 if value is None: return None
 return ns['_KernelIdentity'](value['pid'],int(value['creation_filetime_decimal']),os.path.normcase(os.path.abspath(expand(value['executable']))))
class SlotDriver:
 __slots__=('_session_bridge_pid',)
 def __init__(self,pid): self._session_bridge_pid=pid
data=json.loads(Path(sys.argv[2]).read_text(encoding='utf-8'))
for case in data['match_cases']: case['expected']=ns['_matches_wmi'](expand(case['identity']),kernel(case['kernel']))
for case in data['read_cases']:
 driver=SlotDriver(case['session_pid']) if case['slot_only'] else types.SimpleNamespace(_session_bridge_pid=case['session_pid'])
 old_pin=None
 if case['pin'] is not None:
  old_pin=ns['_ConstructionIdentityPin'](kernel(case['pin']['kernel']),case['pin']['creation_date'])
  driver._construction_process_identity_pin_v1=old_pin
 values=iter([kernel(case['before']),kernel(case['after'])])
 counts={'kernel':0,'producer':0}
 def fixture_kernel(pid):
  counts['kernel']+=1
  value=next(values,None)
  if value is None: raise PermissionError('synthetic unavailable observation')
  return value
 def original_producer(pid):
  counts['producer']+=1
  if case['producer_error'] is not None: raise RuntimeError(case['producer_error'])
  return copy.deepcopy(expand(case['identity']))
 ns['_kernel_process_identity']=fixture_kernel
 ns['_process_identity']=original_producer
 try:
  result=ns['_identity'](driver) if case['transport'] else ns['read_construction_process_identity_v1'](driver,case['session_pid'],original_producer)
  expected={'kind':'returned','result':result}
 except Exception as error: expected={'kind':'error','error_type':type(error).__name__,'message':str(error)}
 retained=getattr(driver,'_construction_process_identity_pin_v1',None)
 expected.update(kernel_calls=counts['kernel'],producer_calls=counts['producer'],pin_learned=retained is not None and retained is not old_pin,retained_creation_date=retained.creation_date if retained is not None else None)
 if expected['kind']=='error' and expected.get('message')=='construction process generation or image changed': expected['before_decision']='REJECT_GENERATION_CHANGE'
 elif counts['producer']==0 and expected['kind']=='returned': expected['before_decision']='USE_EXISTING_PIN'
 else: expected['before_decision']='READ_ORIGINAL_PRODUCER'
 case['expected']=expected
data.update(schema='xar.ck3.constructionidentity-golden/v1',machine_id=machine,observed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_refs=pins,synthetic_kernel_claims_not_live_measurement=True,native_process_reads=0,game_calls=0,ledger_writes=0,scope='Unchanged original dataclasses/functions and actual transport _identity consumer; only kernel/WMI producer fixture seams are synthetic. These vectors do not qualify any live identity or construct Java VerifiedPin.')
raw=(json.dumps(data,sort_keys=True,separators=(',',':'))+'\\n').encode('utf-8')
if len(raw)>65536: raise RuntimeError('cache capture exceeds cap')
for pin in pins:
 path=Path(pin['path'])
 if path.stat().st_size!=pin['bytes'] or hashlib.sha256(path.read_bytes()).hexdigest()!=pin['sha256']: raise RuntimeError('capture pin drift after producer')
sys.stdout.buffer.write(raw)

""";
}
