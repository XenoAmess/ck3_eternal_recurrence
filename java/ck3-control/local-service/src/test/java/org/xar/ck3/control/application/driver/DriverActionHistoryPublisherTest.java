package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Base64;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;

/** Actual software endpoint/coordinator/writer/archive/Driver path, without actual Game or business completion credit.
 * The fixture rejection material tests the generic publisher protocol. Installed domain policies are a separate Root product. */
final class DriverActionHistoryPublisherTest {
    @TempDir Path directory;
    private static final OperationKey DIRECT=new OperationKey("fixture-direct-history-rejection");
    private static final String NATIVE_SHA="eedcd633cf10b0797c331662507d276f8140195b37c1ed0b605da996ee205603";
    private static final String ORIGINAL="""
        import ast,base64,copy,hashlib,json,pathlib,sys,threading,types
        path=pathlib.Path(sys.argv[1]); raw=path.read_bytes()
        assert hashlib.sha256(raw).hexdigest()==sys.argv[2]
        tree=ast.parse(raw.decode('utf-8-sig'))
        matches=[n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='_record_command']
        assert len(matches)==1
        env={'copy':copy,'_RESTORE_CHECKPOINT_STEP':'restore-checkpoint','QUERY_ARMY_STRENGTHS_STEP':'query-army-strengths-v1',
             'CONTINUE_AS_RECONCILED_SUCCESSOR_STEP':'continue-as-reconciled-successor',
             '_is_deferred_read_only_history_step':lambda step:False,'is_life_advance_step':lambda step:False}
        exec(compile(ast.fix_missing_locations(ast.Module(body=matches,type_ignores=[])),str(path),'exec'),env)
        body=json.loads(base64.b64decode(sys.argv[3])); history=[]
        state=types.SimpleNamespace(_history_lock=threading.RLock(),_command_history=history,state_dir=None,
            _route_horizon_wal_eligible_v1=lambda step,result:False,_persist_driver_state=lambda **kw:None)
        for item in body:
            # Only original recorder semantics are exercised. SAVE/restore/Strengths special routes and execute_step selection are excluded.
            assert item['step'] not in {'save-checkpoint','restore-checkpoint','query-army-strengths-v1'}
            env['_record_command'](state,item['step'],ok=item['ok'],result=item.get('result'),error=item.get('error'))
        print(json.dumps(history,separators=(',',':'),sort_keys=True,allow_nan=False))
        """;

    @Test void actualDirectRejectionPublishesCanonicalCoverageAndReopensItsSourceWithoutInventingALegacyRow() throws Exception {
        try(var fixture=fixture("canonical")) {
            var materials=new ActualRejectionMaterials(fixture);
            fixture.bindAdditionalArchivedVerifier(materials.binding());
            var publisher=new DriverActionHistoryPublisher(fixture.driverAuthority(),fixture.journal,fixture.archive,materials,List.of(fixture.observationSource().sourceRef()));
            fixture.bindAdditionalTransitionAuthority(WriterContracts.DRIVER_ACTION_HISTORY_KIND,publisher);
            var command=fixture.command("direct-canonical-history");
            var actual=fixture.coordinator.execute(command);assertTrue(actual.settled());assertTrue(actual.applied().isEmpty());
            assertEquals(ActionReceipt.Outcome.REJECTED_CONFIRMED,actual.outcome());
            var savedSource=new AtomicReference<ExactRef>();var event=new AtomicReference<ExactRef>();
            fixture.writer.locked(same->{
                try {
                    var before=known(fixture,same);byte[] full=before.driver().encode();int writes=fixture.nativeActionWrites(),reads=fixture.nativeReadWrites();
                    long sequence=same.head().state().sequence();
                    assertInstanceOf(DriverStateSnapshot.Incomplete.class,DriverStateAssembler.project(before,fixture.journal.locked(same,ActionJournal.LockedJournal::snapshot),Optional.empty()));
                    var published=assertInstanceOf(DriverActionHistoryPublisher.Published.class,publisher.completed(same,actual));
                    assertTrue(published.legacyRow().isEmpty());assertEquals(sequence+1,same.head().state().sequence());
                    var after=known(fixture,same);assertArrayEquals(full,after.driver().encode());assertEquals(before.driver().commandHistory(),after.driver().commandHistory());
                    assertEquals(before.stamp().driverVersion()+1,after.stamp().driverVersion());
                    assertInstanceOf(DriverSnapshotFacts.CanonicalOnly.class,after.actionRows().getLast().coverageSource());
                    assertThrows(IllegalStateException.class,()->after.actionRows().getLast().historyIndex());
                    assertInstanceOf(DriverStateSnapshot.Complete.class,DriverStateAssembler.project(after,fixture.journal.locked(same,ActionJournal.LockedJournal::snapshot),Optional.empty()));
                    var committed=DriverActionHistoryState.findCommittedCoverage(same,actual,fixture.archive.withSession(same)).orElseThrow();
                    assertEquals(published.originalSource(),committed.originalSource());assertTrue(committed.legacyRow().isEmpty());
                    assertEquals(after.stamp().driverVersion(),committed.afterVersion());savedSource.set(committed.originalSource());event.set(committed.canonicalEvent());
                    String head=same.head().digest();
                    assertEquals(new DriverActionHistoryPublisher.Unchanged(DriverActionHistoryPublisher.Reason.ALREADY_COVERED),publisher.completed(same,actual));
                    assertEquals(head,same.head().digest());assertFalse(publisher.hasPending(same));
                    assertEquals(writes,fixture.nativeActionWrites());assertEquals(reads,fixture.nativeReadWrites());return null;
                } catch(IOException failure){throw new java.io.UncheckedIOException(failure);}
            });
            // A new reader/session uses retained canonical event pins, not publisher memory or an artifact-directory scan.
            fixture.writer.locked(same->{
                try {
                    String head=same.head().digest();int reads=fixture.nativeReadWrites(),writes=fixture.nativeActionWrites();
                    var restored=DriverActionHistoryState.findCommittedCoverage(same,actual,fixture.archive.withSession(same)).orElseThrow();
                    assertEquals(savedSource.get(),restored.originalSource());assertEquals(event.get(),restored.canonicalEvent());
                    DriverActionHistoryCodec.verifyCanonicalOnly(same,actual,restored.originalSource(),fixture.archive.withSession(same));
                    assertEquals(head,same.head().digest());assertEquals(reads,fixture.nativeReadWrites());assertEquals(writes,fixture.nativeActionWrites());return null;
                }catch(IOException failure){throw new java.io.UncheckedIOException(failure);}
            });
        }
    }

    @Test void originalPythonRecorderAgreesWithReturnedAcceptedAndRaisedDataWithoutTreatingOkAsApplied() throws Exception {
        try(var fixture=fixture("legacy-data")) {
            var materials=new ActualRejectionMaterials(fixture);fixture.bindAdditionalArchivedVerifier(materials.binding());
            var actual=fixture.coordinator.execute(fixture.command("legacy-recorder-data"));
            fixture.writer.locked(same->{
                try {
                    var originals=fixture.archive.withSession(same);var evidence=materials.material(actual).evidence();var producers=materials.sources();
                    var proposal=new Obj(Map.of("marriage_action",new Obj(Map.of("status",new Text("proposal_submitted")))));
                    var declined=new Obj(Map.of("accepted",new Bool(false),"source_fixture",new Bool(true)));
                    var variants=List.of(
                        new DriverActionHistoryCodec.Legacy(DriverActionHistoryCodec.Recording.RETURNED,Optional.of(originals.preserveMaterial(raw(proposal))),Optional.empty(),evidence,producers),
                        new DriverActionHistoryCodec.Legacy(DriverActionHistoryCodec.Recording.ACCEPTED_RETURN,Optional.of(originals.preserveMaterial(raw(declined))),Optional.empty(),evidence,producers),
                        new DriverActionHistoryCodec.Legacy(DriverActionHistoryCodec.Recording.RAISED,Optional.of(originals.preserveMaterial(raw(declined))),Optional.of("RuntimeError: controlled original recorder exception"),evidence,producers));
                    var projected=new ArrayList<Value>();var oracleInput=new ArrayList<Value>();long index=0;
                    for(var material:variants) {
                        var source=DriverActionHistoryCodec.source(actual,ContinuityActionJournal.requireHistoricalReceipt(same.head().state(),actual,originals),originals.receiptReferenceOf(actual),material);
                        assertEquals(source,DriverActionHistoryCodec.decode(DriverActionHistoryCodec.encode(source)));
                        var row=DriverActionHistoryCodec.legacyRow(++index,actual,source,originals);DriverActionHistoryCodec.verifyLegacy(same,actual,row,originals);
                        var plain=new java.util.LinkedHashMap<>(row.members());plain.remove(DriverActionHistoryCodec.SOURCE_FIELD);projected.add(new Obj(plain));
                        var input=new java.util.LinkedHashMap<String,Value>();input.put("step",new Text(actual.command().operation().value()));input.put("ok",new Bool(index==1));
                        if(row.members().containsKey("result"))input.put("result",row.get("result"));if(row.members().containsKey("error"))input.put("error",row.get("error"));oracleInput.add(new Obj(input));
                        var changed=row.with("ok",new Bool(!bool(row.get("ok"),"ok")));assertThrows(IllegalArgumentException.class,()->DriverActionHistoryCodec.verifyLegacy(actual,changed,originals));
                    }
                    assertEquals(new Bool(true),object(projected.getFirst(),"returned").get("ok"));assertTrue(actual.applied().isEmpty());
                    assertEquals(new Bool(false),object(projected.get(1),"accepted-return").get("ok"));
                    assertEquals(new Bool(false),object(projected.get(2),"raised").get("ok"));
                    assertEquals(new Arr(projected),python(new Arr(oracleInput)));
                    // These are recorder DATA projections, deliberately not installed-domain policies or a private Publisher token.
                    var complete=known(fixture,same).driver();var history=new ArrayList<>(complete.commandHistory());
                    for(Value row:projected){Obj item=object(row,"legacy recorder row");history.add(new DriverStateSnapshot.HistoryEntry(integer(item.get("index"),"index").longValueExact(),new DriverStateSnapshot.Value(DriverJson.encode(item))));}
                    var roundtrip=new DriverStateSnapshot.Complete(complete.session(),history,complete.lastCheckpoint(),complete.rollbackWarFailure(),complete.managedRestoreTransaction(),
                            complete.successionExpectation(),complete.successionLifecycle(),complete.campaignGoal(),complete.rollbackWarFailures());
                    assertArrayEquals(roundtrip.encode(),DriverStateSnapshot.decodeComplete(roundtrip.encode()).encode());return null;
                }catch(IOException failure){throw new java.io.UncheckedIOException(failure);}
            });
        }
    }

    @Test void actualUnknownSubmissionDoesNotCaptureMaterialPublishHistoryOrReplayNative() throws Exception {
        try(var fixture=fixture("unknown",true)) {
            var materials=new ActualRejectionMaterials(fixture);
            var publisher=new DriverActionHistoryPublisher(fixture.driverAuthority(),fixture.journal,fixture.archive,materials,List.of(fixture.observationSource().sourceRef()));
            fixture.bindAdditionalTransitionAuthority(WriterContracts.DRIVER_ACTION_HISTORY_KIND,publisher);
            var actual=fixture.coordinator.execute(fixture.command("unknown-history-no-replay"));assertFalse(actual.settled());
            fixture.writer.locked(same->{
                try {
                    String head=same.head().digest();int writes=fixture.nativeActionWrites(),reads=fixture.nativeReadWrites();
                    assertEquals(new DriverActionHistoryPublisher.Unchanged(DriverActionHistoryPublisher.Reason.UNRESOLVED),publisher.completed(same,actual));
                    assertEquals(0,materials.captures);assertEquals(head,same.head().digest());assertFalse(publisher.hasPending(same));
                    assertEquals(writes,fixture.nativeActionWrites());assertEquals(reads,fixture.nativeReadWrites());
                    assertThrows(IllegalArgumentException.class,()->DriverActionHistoryCodec.source(actual,fixture.observationSource().sourceRef(),fixture.observationSource().sourceRef(),materials.material(actual)));return null;
                }catch(IOException failure){throw new java.io.UncheckedIOException(failure);}
            });
        }
    }

    @Test void closedSourceAndCanonicalReducerRejectWrongFieldsTypesUnknownAndUnrelatedStateChanges() throws Exception {
        try(var fixture=fixture("negative-data")) {
            var materials=new ActualRejectionMaterials(fixture);fixture.bindAdditionalArchivedVerifier(materials.binding());
            var actual=fixture.coordinator.execute(fixture.command("negative-action-source"));
            fixture.writer.locked(same->{
                try {
                    var originals=fixture.archive.withSession(same);var source=DriverActionHistoryCodec.source(actual,ContinuityActionJournal.requireHistoricalReceipt(same.head().state(),actual,originals),originals.receiptReferenceOf(actual),materials.material(actual));
                    Obj row=DriverJson.object(DriverActionHistoryCodec.encode(source).bytes(),DriverActionHistoryCodec.MAX_SOURCE_BYTES);
                    assertThrows(IllegalArgumentException.class,()->DriverActionHistoryCodec.decode(raw(row.with("durable_sequence",new Bool(true)))));
                    assertThrows(IllegalArgumentException.class,()->DriverActionHistoryCodec.decode(raw(row.with("outcome",new Text("UNRESOLVED")))));
                    assertThrows(IllegalArgumentException.class,()->DriverActionHistoryCodec.decode(raw(row.with("unowned_alias",Nil.INSTANCE))));
                    assertThrows(IllegalArgumentException.class,()->DriverActionHistoryCodec.decode(raw(row.with("result",row.get("receipt")))));
                    assertThrows(IllegalArgumentException.class,()->DriverActionHistoryCodec.decode(raw(row.with("evidence",new Arr(List.of())))));
                    var before=known(fixture,same);var ref=originals.materialReferenceOf(new RawJson(before.driver().encode()));
                    var data=new DriverActionHistoryState.Publication("negative-pure-data",actual.command(),actual.bodySha256(),actual.sequence(),same.head().digest(),
                            before.stamp().driverVersion(),before.stamp().driverVersion()+1,before.stamp().episodeEpoch(),ref,ref,originals.preserveMaterial(DriverActionHistoryCodec.encode(source)),Optional.empty());
                    var request=data.request(List.of(ref,data.originalSource()));var state=same.head().state();
                    assertEquals(data,DriverActionHistoryState.decode(request.detailsObject(),actual));
                    var reduced=DriverActionHistoryState.reduce(state,request);DriverActionHistoryState.requireReduction(state,reduced,request,false);
                    var changed=reduced.toJson();changed.put("next_sequence",99);
                    assertThrows(IllegalArgumentException.class,()->DriverActionHistoryState.requireReduction(state,ContinuityState.fromJson(changed,state.machineId()),request,false));
                    assertThrows(IllegalArgumentException.class,()->DriverActionHistoryState.requireReduction(state,reduced,request,true));
                    assertTrue(DriverActionHistoryState.findCommittedCoverage(same,actual,originals).isEmpty(),"an archived source or pure reducer result is not a canonical publication");return null;
                }catch(IOException failure){throw new java.io.UncheckedIOException(failure);}
            });
        }
    }

    private ActionWriterIntegrationFixture fixture(String label)throws Exception {return fixture(label,false);}
    private ActionWriterIntegrationFixture fixture(String label,boolean loseAck)throws Exception {
        var held=new AtomicReference<ActionWriterIntegrationFixture>();
        var scenario=new ActionWriterIntegrationFixture.SoftwareActionScenario(DIRECT,"game.command."+DIRECT.value(),(command,attempt,dispatch)->{
            var actual=held.get();var ack=assertInstanceOf(NativeActionPort.AckReceived.class,dispatch);
            assertEquals(new Bool(false),DriverJson.object(ack.originalResultToken().orElseThrow().bytes(),DriverJson.MAX_NATIVE_BYTES).get("accepted"));
            return new ActionPorts.RejectionObserved(new ActionState.Rejected(attempt.requestId(),"source-qualified software rejection",actual.archive.referenceOf(dispatch)));
        },()->{},()->raw(new Obj(Map.of("accepted",new Bool(false),"fixture_direct_api",new Bool(true)))));
        var fixture=new ActionWriterIntegrationFixture(directory.resolve(label),loseAck,scenario);held.set(fixture);return fixture;
    }
    private static DriverSnapshotFacts.Known known(ActionWriterIntegrationFixture fixture,Session same)throws IOException {
        return fixture.driverAuthority().withFrozenFacts(same,frozen->assertInstanceOf(DriverSnapshotFacts.Known.class,frozen.state()));
    }
    private static final class ActualRejectionMaterials implements DriverActionHistoryPublisher.MaterialSource {
        private final ActionWriterIntegrationFixture fixture;private int captures;
        ActualRejectionMaterials(ActionWriterIntegrationFixture actual){fixture=actual;}
        NativeRecordedEvidenceVerifier.Binding binding(){return new NativeRecordedEvidenceVerifier.Binding(DIRECT,fixture.observationSource().sourceRef(),(head,receipt,originals)->requireRejected(receipt,originals));}
        @Override public List<ExactRef> sources(){return List.of(fixture.observationSource().sourceRef());}
        @Override public void requireOwner(DriverStateAssembler authority,ActionJournal journal,ActionPorts.OutcomeArchive archive){assertSame(fixture.driverAuthority(),authority);assertSame(fixture.journal,journal);assertSame(fixture.archive,archive);}
        DriverActionHistoryCodec.CanonicalOnly material(ActionReceipt actual){
            var attempt=ActionTransitions.attempt(actual.state()).orElseThrow();var dispatch=ActionTransitions.dispatch(actual.state()).orElseThrow();
            return new DriverActionHistoryCodec.CanonicalOnly(DriverActionHistoryCodec.CanonicalReason.DIRECT_API_WITHOUT_LEGACY_RECORDER,
                    List.of(new DriverActionHistoryCodec.Evidence(DriverActionHistoryCodec.EvidenceKind.NATIVE_FRAME,attempt.guard().nativeEvidence()),
                            new DriverActionHistoryCodec.Evidence(DriverActionHistoryCodec.EvidenceKind.MATERIAL,fixture.archive.referenceOf(dispatch))),sources());
        }
        @Override public DriverActionHistoryCodec.OriginalMaterial capture(Session same,ActionReceipt actual,ActionPorts.OutcomeArchive originals)throws IOException {
            captures++;requireOriginal(same,actual,material(actual),originals);return material(actual);
        }
        @Override public void requireOriginal(Session same,ActionReceipt actual,DriverActionHistoryCodec.OriginalMaterial material,ActionPorts.OutcomeArchive originals)throws IOException {
            fixture.writer.requireSession(same);assertEquals(material(actual),material);
            var verifier=new NativeRecordedEvidenceVerifier(fixture.archive,fixture.journal::borrowedWriterSession,
                    (borrowed,ref,maximum)->fixture.archive.readArtifact(borrowed,ref,maximum),fixture.frameLoader(),List.of(binding()));
            verifier.verify(same.head(),actual);requireRejected(actual,originals);
        }
        private static void requireRejected(ActionReceipt actual,ActionPorts.OutcomeArchive originals){
            assertEquals(DIRECT,actual.command().operation());var state=assertInstanceOf(ActionState.Settled.class,actual.state());
            var rejected=assertInstanceOf(ActionState.Rejected.class,state.settlement());var ack=assertInstanceOf(NativeActionPort.AckReceived.class,state.dispatch());
            assertEquals(ack.requestId(),rejected.requestId());assertEquals(originals.referenceOf(ack),rejected.originalEvidence());
            assertEquals(ack,originals.load(rejected.originalEvidence()));assertEquals(new Bool(false),DriverJson.object(ack.originalResultToken().orElseThrow().bytes(),DriverJson.MAX_NATIVE_BYTES).get("accepted"));
        }
    }
    private static RawJson raw(Value value){return new RawJson(DriverJson.encode(value));}
    private static Arr python(Arr input)throws IOException {
        String checkout=System.getProperty("xar.original.checkout"),python=System.getProperty("xar.python.executable");
        StrictJson.require(checkout!=null&&python!=null,"original checkout and independent Python executable are required; missing configuration is not a pass");
        Path original=Path.of(checkout).resolve("ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py");
        StrictJson.require(Files.size(original)==1658471&&DriverJson.sha256(Files.readAllBytes(original)).equals(NATIVE_SHA),"original Python producer pin differs");
        Process child=new ProcessBuilder(python,"-X","utf8","-c",ORIGINAL,original.toString(),NATIVE_SHA,Base64.getEncoder().encodeToString(DriverJson.encode(input))).redirectErrorStream(true).start();
        try {if(!child.waitFor(20,TimeUnit.SECONDS)){child.destroyForcibly();throw new IOException("original recorder process timed out");}}
        catch(InterruptedException interrupted){Thread.currentThread().interrupt();child.destroyForcibly();throw new IOException(interrupted);}
        byte[] output=child.getInputStream().readAllBytes();StrictJson.require(child.exitValue()==0,"original recorder failed: "+new String(output,StandardCharsets.UTF_8));
        return assertInstanceOf(Arr.class,DriverJson.object(("{\"rows\":"+new String(output,StandardCharsets.UTF_8).strip()+"}").getBytes(StandardCharsets.UTF_8),DriverJson.MAX_NATIVE_BYTES).get("rows"));
    }
}
