package org.xar.ck3.control.wave2.runtime.savedproof;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FileStatIdentity;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.recovery.RecoveryEvidence;

/** Actual Java-to-fixed-worker metadata transport. This test stops before any SDK import or body operation. */
final class FixedSdkSourceInventoryTest {
    @TempDir Path temporary;
    private static ExactRef write(Path path,byte[] bytes) throws Exception {
        Files.write(path,bytes);return new ExactRef(path.toString(),bytes.length,RecoveryEvidence.sha256(bytes));
    }
    @Test void javaInventoryAndRequestsReachActualWorkerConsumerBeforeAnySdkOrPersistenceRead() throws Exception {
        Path sdk=Files.createDirectory(temporary.resolve("sdk"));
        Path packageRoot=Files.createDirectory(sdk.resolve("xar_autoplayer"));
        ExactRef validator=write(packageRoot.resolve("cold_checkpoint_validator.py"),"# source fixture only\n".getBytes(java.nio.charset.StandardCharsets.UTF_8));
        // The worker consumes the Java projection. Derived business validation remains in SdkDerivedSource32.
        ExactRef freeze=write(temporary.resolve("lineage.json"),"{\"schema\":\"source-fixture-not-a-qualified-lineage\"}".getBytes(java.nio.charset.StandardCharsets.UTF_8));
        var identity=new FileStatIdentity(BigInteger.ONE,"1","1");
        Path missingDriver=temporary.resolve("never-open-driver-state.json");
        Path save=temporary.resolve("profile/save games/xar_checkpoint.ck3");
        var release=new RecoveryEvidence(new ExactRef(temporary.resolve("release.json").toString(),2,RecoveryEvidence.sha256(new byte[]{'{','}'})),new byte[]{'{','}'});
        var ticket=new SavedProofReadTicket(release,"synthetic-source-fixture","a".repeat(32),Instant.now().minusSeconds(1),Instant.now().plusSeconds(60),
                missingDriver,identity,new ExactRef(save.toString(),1,"b".repeat(64)),identity,sdk,freeze,validator,"fixture-pipe",
                temporary.resolve("never-started-ticket-python.exe"),temporary,1024,96L<<20,20);
        byte[] inventory=FixedSdkTransport.sourceInventory(ticket,Map.of("xar_autoplayer/cold_checkpoint_validator.py",validator));
        ExactRef inventoryRef=write(temporary.resolve("java-inventory.json"),inventory);
        write(temporary.resolve("closed-request.json"),FixedSdkTransport.request(ticket,false,inventoryRef));
        write(temporary.resolve("cold-request.json"),FixedSdkTransport.request(ticket,true,inventoryRef));
        Path worker=temporary.resolve("fixed-worker.py");Files.writeString(worker,FixedSdkTransport.PROGRAM);
        Path probe=temporary.resolve("metadata-probe.py");Files.writeString(probe,PROBE);
        Path repo=Path.of(System.getProperty("xar.repo",System.getenv().getOrDefault("XAR_REPO_ROOT","."))).toRealPath();
        Path python=Path.of(System.getProperty("xar.python",repo.resolve("tools/.venv/Scripts/python.exe").toString())).toRealPath();
        var environment=new java.util.HashMap<>(System.getenv());environment.put("PYTHONDONTWRITEBYTECODE","1");environment.put("PYTHONIOENCODING","utf-8");
        var spec=new WindowsJobProcess.CommandSpec(python,List.of("-B","-X","utf8",probe.toString(),worker.toString(),temporary.toString()),
                temporary,environment,temporary.resolve("stdout.log"),temporary.resolve("stderr.log"),96L<<20);
        try(var process=WindowsJobProcess.start(spec,WindowsJobProcess.ConsoleMode.NO_WINDOW)) {
            var actual=process.await(Duration.ofSeconds(20),Instant.now().plusSeconds(20),()->{});
            assertTrue(actual.passed(),Files.readString(temporary.resolve("stderr.log")));
            assertEquals(0,actual.accounting().activeProcesses());
        }
        assertTrue(Files.readString(temporary.resolve("stdout.log")).trim().endsWith("INVENTORY_CASES_PASS:6:DRIVER0:SAVE0:SDK_IMPORT0"));
        assertFalse(Files.exists(missingDriver));assertFalse(Files.exists(save));
    }
    private static final String PROBE="""
import ast,copy,hashlib,json,sys
from pathlib import Path
worker,root=map(Path,sys.argv[1:])
tree=ast.parse(worker.read_text(encoding='utf-8'))
found=0
for node in ast.walk(tree):
    if isinstance(node,ast.Try):
        for index,statement in enumerate(node.body):
            if isinstance(statement,ast.ImportFrom) and statement.module=='xar_autoplayer.cold_checkpoint_validator':
                node.body[index:index+1]=[ast.Raise(exc=ast.Call(func=ast.Name(id='InventoryReached',ctx=ast.Load()),args=[ast.Name(id='pins',ctx=ast.Load()),ast.Name(id='counts',ctx=ast.Load())],keywords=[]),cause=None)]
                found+=1
assert found==1
program=compile(ast.fix_missing_locations(tree),str(worker),'exec')
class InventoryReached(BaseException): pass
def write(name,value):
    path=root/name;raw=json.dumps(value,separators=(',',':')).encode();path.write_bytes(raw)
    return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def run(value,expected):
    request=write('probe-request.json',value);sys.argv=[str(worker),request['path']]
    namespace={'InventoryReached':InventoryReached,'__name__':'__main__'}
    try: exec(program,namespace)
    except InventoryReached as actual:
        assert expected and len(actual.args[0])==1
    except SystemExit as actual:
        assert not expected and actual.code==1
    else: raise AssertionError('actual worker did not stop at its expected boundary')
    assert namespace['counts']['driver_physical_body_reads']==0 and namespace['counts']['save_sha256_calls']==0
    assert not any(name=='xar_autoplayer' or name.startswith('xar_autoplayer.') for name in sys.modules)
closed=json.loads((root/'closed-request.json').read_bytes());cold=json.loads((root/'cold-request.json').read_bytes())
assert closed['schema']==cold['schema']=='xar.fixed-original-sdk-measurement-request/v3'
run(closed,True);run(cold,True)
wrong=copy.deepcopy(cold);wrong['source_inventory_ref']['sha256']='f'*64;run(wrong,False)
inventory=json.loads((root/'java-inventory.json').read_bytes())
bad=copy.deepcopy(inventory);bad['files'][0]['source_ref']['bytes']=True
wrong=copy.deepcopy(cold);wrong['source_inventory_ref']=write('bool-inventory.json',bad);run(wrong,False)
bad=copy.deepcopy(inventory);bad['sdk_freeze_ref']['sha256']='f'*64
wrong=copy.deepcopy(cold);wrong['source_inventory_ref']=write('wrong-freeze-inventory.json',bad);run(wrong,False)
bad=copy.deepcopy(inventory);bad['sdk_root']=str(root)
wrong=copy.deepcopy(cold);wrong['source_inventory_ref']=write('wrong-root-inventory.json',bad);run(wrong,False)
print('INVENTORY_CASES_PASS:6:DRIVER0:SAVE0:SDK_IMPORT0')
""";
}
