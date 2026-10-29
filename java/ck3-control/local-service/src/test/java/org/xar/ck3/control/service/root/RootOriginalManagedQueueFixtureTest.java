package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.util.EnumSet;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.driver.InitialEpisodePolicy;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.platform.NativeBridgeLaunchEvidence;
import org.xar.ck3.control.platform.NativeLaunchPlan;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.ObjectValue;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.StringValue;

/** Original Python reader versus the genuine private physical issuer, using only pre-existing signed-census fixtures. */
final class RootOriginalManagedQueueFixtureTest {
    private static final String ORACLE="""
import ast,hashlib,json,sys,types
from pathlib import Path
source=Path(sys.argv[1]);raw=source.read_bytes();tree=ast.parse(raw.decode('utf-8-sig'))
methods={}
for node in ast.walk(tree):
    if isinstance(node,ast.FunctionDef) and node.name in {'_managed_restore_request_state','_native_session_queue_dir'}:
        if node.name in methods:raise RuntimeError('ambiguous original reader')
        methods[node.name]=node
constant=next(node for node in tree.body if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='_NATIVE_SESSION_QUEUE_DIRNAME' for t in node.targets))
namespace={'Path':Path,'json':json,'UnsupportedStepError':RuntimeError,'_NATIVE_SESSION_QUEUE_DIRNAME':ast.literal_eval(constant.value)}
if namespace['_NATIVE_SESSION_QUEUE_DIRNAME']!='native-session':raise RuntimeError('original layout changed')
exec(compile(ast.Module(body=list(methods.values()),type_ignores=[]),str(source),'exec'),namespace)
actual=types.SimpleNamespace(state_dir=Path(sys.argv[2]))
actual._native_session_queue_dir=types.MethodType(namespace['_native_session_queue_dir'],actual)
transaction=json.loads(sys.stdin.read())
state=namespace['_managed_restore_request_state'](actual,transaction)
print(json.dumps({'state':state,'source_sha256':hashlib.sha256(raw).hexdigest()},separators=(',',':')))
""";
    @Test void allThreePhysicalStatesMatchTheOriginalReaderWithoutCreatingQueueFilesOrAnotherWriter()throws Exception {
        var fixture=RootOriginalDriverColdFixture.readRequiredSystemProperties();
        String python=required("xar.python"),repository=required("xar.repository.root");
        Path originalSource=Path.of(repository).resolve("ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py");
        var source=SharedSourceFiles.observe(originalSource);var covered=EnumSet.noneOf(RootOriginalDriverJournal.ManagedQueueStatus.class);
        for(var test:fixture.cases()) {
            var plan=NativeLaunchPlan.readExact(test.launchPlan(),new NativeBridgeLaunchEvidence());
            Clock clock=Clock.systemUTC();RootOriginalDriverColdFixture.requirePrelaunch(plan,clock);
            var policy=InitialEpisodePolicy.readExact(test.episodePolicy(),plan.preparedProfile().environmentManifest());
            var profile=RootFrozenRunProfile.readExact(test.runRequest(),plan,policy,clock);
            try(var scope=RootOriginalDriverColdFixture.openReadOnlyScope(test.control(),test.storageLease(),fixture.machineId(),clock)) {
            var writer=scope.writer();var storage=scope.storage();var files=scope.files();
            RootOriginalDriverColdFixture.requireStorage(plan,test.control(),storage);
            var prepared=new RootOriginalDriverJournal.Prepared(files,storage,plan,profile,clock);
            RootOriginalDriverJournal.ManagedQueueObservation[] retained=new RootOriginalDriverJournal.ManagedQueueObservation[1];
            RootOriginalDriverJournal.OriginalJournalLoad[] loaded=new RootOriginalDriverJournal.OriginalJournalLoad[1];
            writer.locked(same->{
                String head=same.head().digest();var actual=prepared.load(writer,same,plan);
                assertEquals(plan.profileDirectory(),actual.profileDirectory());actual.requireActualProfile(same,plan.profileDirectory());
                assertThrows(java.io.IOException.class,()->actual.requireActualProfile(same,plan.profileDirectory().resolve("foreign-profile")));
                if(actual.status()==RootOriginalDriverJournal.Status.MISSING||actual.status()==RootOriginalDriverJournal.Status.JOURNAL_INVALID)return null;
                if(!(actual.fullPayload().get("managed_restore_transaction") instanceof ObjectValue marker))return null;
                if(!(marker.get("request_id") instanceof StringValue id))fail("fixture managed marker needs its actual request ID");
                String request=((StringValue)marker.get("request_id")).value();
                var observed=RootOriginalDriverJournal.probeManagedQueue(same,actual,request);observed.requireCurrent(same,actual);
                var process=new ProcessBuilder(python,"-B","-c",ORACLE,originalSource.toString(),plan.stateDirectory().toString()).start();
                process.getOutputStream().write(OriginalDriverJournal.canonical(marker,65536).bytes());process.getOutputStream().close();
                try {
                    if(!process.waitFor(30,TimeUnit.SECONDS)){process.destroyForcibly();fail("original queue oracle timed out");}
                }catch(InterruptedException interrupted){process.destroyForcibly();Thread.currentThread().interrupt();throw new java.io.IOException("original queue oracle interrupted",interrupted);}
                byte[] output=process.getInputStream().readNBytes(4097),error=process.getErrorStream().readNBytes(4097);
                assertEquals(0,process.exitValue(),new String(error,java.nio.charset.StandardCharsets.UTF_8));assertTrue(output.length<=4096);
                var expected=StrictJson.parse(output,4096);
                assertEquals(source.source().sha256(),expected.path("source_sha256").textValue());
                assertEquals(expected.path("state").textValue().toUpperCase(java.util.Locale.ROOT),observed.status().name());
                assertEquals(request,observed.requestId());assertFalse(observed.originalReferences().isEmpty());
                observed.requireCurrent(same,actual);assertEquals(head,same.head().digest());
                retained[0]=observed;loaded[0]=actual;covered.add(observed.status());return null;
            });
            if(retained[0]!=null)writer.locked(other->{
                assertThrows(java.io.IOException.class,()->retained[0].requireCurrent(other,loaded[0]));
                var fresh=prepared.load(writer,other,plan);fresh.requireRetained(other);
                var observed=RootOriginalDriverJournal.probeManagedQueue(other,fresh,retained[0].requestId());observed.requireCurrent(other,fresh);
                assertEquals(retained[0].identityDigest(),observed.identityDigest(),"fresh private scopes retain equal immutable DATA only for identical physical queue facts");
                assertTrue(observed.identityDigest().matches("[0-9a-f]{64}"));return null;
            });
            }
        }
        SharedSourceFiles.assertUnchanged(source);
        assertEquals(EnumSet.allOf(RootOriginalDriverJournal.ManagedQueueStatus.class),covered,
                "the complete cold fixture must contain real MISSING/PRESENT/FAILED queue cases; missing vectors are not a pass");
    }
    private static String required(String property){String value=System.getProperty(property);assertNotNull(value,"mandatory original oracle input missing: "+property);assertFalse(value.isBlank());return value;}
}
