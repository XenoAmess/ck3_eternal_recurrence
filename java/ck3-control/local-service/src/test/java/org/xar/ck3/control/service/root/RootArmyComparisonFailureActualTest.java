package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.*;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsService;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Genuine installed inputs only. Missing private Root inputs fail explicitly; no replacement Source is fabricated. */
public final class RootArmyComparisonFailureActualTest {
    public enum Stage { EXPECTED_REVISION, CURRENT_ACQUISITION, QUALIFICATION, POST_KNOWN_CURRENT, COMPARISON, SIDECAR_POLICY }
    public record Input(Stage stage,RootApplicationSession root,RootInstalledCatalog installed,
            ArmyStrengthsService service,Optional<BigInteger> expectedRevision,Instant deadline,
            ArmyStrengthsService.HistoryDisposition disposition) {
        public Input {Objects.requireNonNull(stage);Objects.requireNonNull(root);Objects.requireNonNull(installed);
            Objects.requireNonNull(service);Objects.requireNonNull(expectedRevision);Objects.requireNonNull(deadline);Objects.requireNonNull(disposition);}
    }
    public interface InputsProducer {List<Input> actualFailureInputs()throws Exception;}
    @Test void everyOriginalQueryTryFailurePublishesOneFalseNoResultRowThroughTheSameRoot()throws Exception {
        var providers=ServiceLoader.load(InputsProducer.class).stream().map(ServiceLoader.Provider::get).toList();
        if(providers.size()!=1)throw new IOException("MISSING_NOT_RUN: one genuine installed Army comparison failure InputsProducer required");
        var seen=EnumSet.noneOf(Stage.class);
        for(var input:providers.getFirst().actualFailureInputs()) {
            assertTrue(seen.add(input.stage()));var context=input.installed().context();
            var before=context.withSession(same->context.adopted().authority().withFrozenFacts(same,
                    frozen->assertInstanceOf(DriverSnapshotFacts.Known.class,frozen.state())));
            var error=assertThrows(RuntimeException.class,()->input.root().withPublicObservation(input.deadline(),(frame,known,same)->{
                try{return RootPublicStepFailureOriginals.executeArmyComparisonQuery(
                        input.root(),input.installed(),input.service(),input.expectedRevision(),input.deadline());}
                catch(InterruptedException interrupted){Thread.currentThread().interrupt();throw new IOException("Army comparison query interrupted",interrupted);}
            }));
            assertThrows(IllegalArgumentException.class,()->input.service().takeInvocationFailure(error),"sole Root catch must consume its exact private token once");
            context.withSession(same->{context.adopted().authority().withFrozenFacts(same,frozen->{
                var after=assertInstanceOf(DriverSnapshotFacts.Known.class,frozen.state());
                assertEquals(before.actionRows(),after.actionRows());assertEquals(before.driver().session(),after.driver().session());
                if(input.disposition()==ArmyStrengthsService.HistoryDisposition.STORAGE_DIAGNOSTIC) {
                    assertEquals(before.driver().commandHistory().size(),after.driver().commandHistory().size());
                    assertTrue(context.readHistoryPublisher().statusSnapshot().driverStateError().isPresent());
                } else {
                    assertEquals(before.driver().commandHistory().size()+1,after.driver().commandHistory().size());
                    var row=DriverJson.object(after.driver().commandHistory().getLast().originalRow().json(),64<<20);
                    assertEquals(new OpportunityJson.Text("query-army-strengths-v1"),row.get("command"));
                    assertEquals(new OpportunityJson.Bool(false),row.get("ok"));
                    assertFalse(row.members().containsKey("result"));assertInstanceOf(OpportunityJson.Text.class,row.get("error"));
                    assertArrayEquals(after.driver().encode(),org.xar.ck3.control.application.checkpoint.DriverStateSnapshot.decodeComplete(after.driver().encode()).encode());
                }
                return null;
            });return null;});
        }
        assertEquals(EnumSet.allOf(Stage.class),seen,"all exact original query try-body failure stages are mandatory");
    }
    @Test void originalPythonQueryBoundaryRecordsEachRealInjectedFailureOnceWithoutAResult()throws Exception {
        Path original=Path.of(required("xar.native.producer.source"));byte[] bytes=Files.readAllBytes(original);
        assertEquals(1658471,bytes.length);assertEquals("eedcd633cf10b0797c331662507d276f8140195b37c1ed0b605da996ee205603",ActionCodec.sha256(bytes));
        Process process=new ProcessBuilder(required("xar.native.producer.python"),"-X","utf8","-c",PYTHON,original.toString())
                .redirectErrorStream(true).start();
        if(!process.waitFor(30,java.util.concurrent.TimeUnit.SECONDS)){process.destroyForcibly();throw new IOException("original Python query-boundary oracle timed out");}
        String output=new String(process.getInputStream().readAllBytes(),StandardCharsets.UTF_8);
        assertEquals(0,process.exitValue(),output);assertEquals("ORIGINAL_QUERY_TRY_FAILURES_6_PASS",output.strip());
    }
    private static String required(String name)throws IOException {
        String value=System.getProperty(name);if(value==null||value.isBlank())throw new IOException("MISSING_NOT_RUN: "+name);return value;
    }
    /** Executes the exact original query method. Controlled callback failures test its catch scope, not Native gameplay or gate qualification. */
    private static final String PYTHON="""
import ast, pathlib, sys, types
source=ast.parse(pathlib.Path(sys.argv[1]).read_text(encoding='utf-8-sig'))
owner=next(n for n in source.body if isinstance(n,ast.ClassDef) and any(isinstance(x,ast.FunctionDef) and x.name=='query_army_strengths' for x in n.body))
method=next(n for n in owner.body if isinstance(n,ast.FunctionDef) and n.name=='query_army_strengths')
method.decorator_list=[]
for a in method.args.kwonlyargs: a.annotation=None
for a in method.args.args: a.annotation=None
method.returns=None
class Fault(RuntimeError): pass
module=types.ModuleType('xar_autoplayer.bridge.private_auto_scalar_ab_control_v1')
module.selected_mode=lambda self,snapshot:'compare'
module.mark_compared=lambda self,snapshot:None
module.disable=lambda self:setattr(self,'disabled',True)
for name in ('xar_autoplayer','xar_autoplayer.bridge'):
    package=types.ModuleType(name);package.__path__=[];sys.modules[name]=package
sys.modules[module.__name__]=module
g={'__name__':'xar_autoplayer.bridge.native_driver','__package__':'xar_autoplayer.bridge',
   'ORDINARY_CORE_PROFILE':'ordinary_core_v1','QUERY_ARMY_STRENGTHS_STEP':'query-army-strengths-v1','BridgeUnavailableError':Fault,
   'require_army_strengths_profile':lambda p:p,'start_army_timing':lambda *a,**k:None,'finish_army_timing':lambda *a,**k:None}
def revision(value,name):
    if type(value) is not int or value<=0: raise Fault('expected_revision failure')
g['_validate_revision']=revision
tree=ast.fix_missing_locations(ast.Module(body=[ast.ClassDef(name='Subject',bases=[],keywords=[],body=[method],decorator_list=[])],type_ignores=[]))
exec(compile(tree,'actual-original-query','exec'),g)
class Lock:
    def __enter__(self): return self
    def __exit__(self,*args): pass
for stage in ('expected','current','qualification','postKnown','comparison','sidecar'):
    subject=g['Subject']();subject._driver_state_lock=Lock();subject.rows=[];subject.calls=0
    def snap():
        if stage=='current': raise Fault('actual current failure')
        return {'revision':7}
    subject.take_internal_semantic_snapshot=snap
    def query(**kw):
        subject.calls+=1
        if stage in ('qualification','postKnown','sidecar'): raise Fault(stage+' actual callback failure')
        result={k:7 for k in ('queried_revision','queried_native_revision','queried_date_raw','queried_connection_generation')}
        result.update(status='available',army_strengths=[],queried_snapshot_id='same',queried_episode_run_id='same')
        if stage=='comparison' and subject.calls==2: result['status']='different'
        return result
    subject._execute_army_strength_query=query
    subject._record_command=lambda command,**row:subject.rows.append((command,row))
    try: subject.query_army_strengths(expected_revision=0 if stage=='expected' else 7,_auto_core_only=True)
    except (Fault,RuntimeError): pass
    else: raise AssertionError(stage+' did not execute original catch')
    assert len(subject.rows)==1,(stage,subject.rows)
    command,row=subject.rows[0]
    assert command=='query-army-strengths-v1' and row['ok'] is False and row['result'] is None and isinstance(row['error'],str),(stage,row)
print('ORIGINAL_QUERY_TRY_FAILURES_6_PASS')
""";
}
