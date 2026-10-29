package org.xar.ck3.control.service.mcp;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.io.IOException;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;

/** Actual software coordinator -> writer/archive -> sole history publisher -> current Known -> AUTO consumer.
 * This direct rejection is protocol DATA, not a Game/domain success or a replacement for Root AUTO qualification. */
final class McpAutoHistoryCoverageTest {
    @TempDir Path directory;
    private static final OperationKey DIRECT=new OperationKey("fixture-auto-original-history-rejection");
    @Test void actualCanonicalOnlyPublisherReopensWithoutLegacyOrdinalAndAutoRetainsUnavailableBusiness()throws Exception{
        try(var fixture=fixture("canonical",false)){
            var material=new Materials(fixture,Optional.empty());install(fixture,material);
            var publisher=publisher(fixture,material);var actual=fixture.coordinator.execute(fixture.command("actual-canonical-only-auto"));
            assertEquals(ActionReceipt.Outcome.REJECTED_CONFIRMED,actual.outcome());
            fixture.writer.locked(same->{try{
                var published=assertInstanceOf(DriverActionHistoryPublisher.Published.class,publisher.completed(same,actual));assertTrue(published.legacyRow().isEmpty());
                var known=known(fixture,same);assertInstanceOf(DriverSnapshotFacts.CanonicalOnly.class,known.actionRows().getLast().coverageSource());
                assertThrows(IllegalStateException.class,()->known.actionRows().getLast().historyIndex());
                int writes=fixture.nativeActionWrites(),reads=fixture.nativeReadWrites();String head=same.head().digest();
                assertTrue(McpAutoTurnEncoder.originalBusiness(actual,known,fixture.archive.withSession(same)).isEmpty());
                assertEquals(head,same.head().digest());assertEquals(writes,fixture.nativeActionWrites());assertEquals(reads,fixture.nativeReadWrites());return null;
            }catch(IOException failure){throw new java.io.UncheckedIOException(failure);}});
            fixture.writer.locked(same->{try{
                var source=DriverActionHistoryState.findCommittedCoverage(same,actual,fixture.archive.withSession(same)).orElseThrow();
                DriverActionHistoryCodec.verifyCanonicalOnly(same,actual,source.originalSource(),fixture.archive.withSession(same));
                assertTrue(source.legacyRow().isEmpty());assertTrue(McpAutoTurnEncoder.originalBusiness(actual,known(fixture,same),fixture.archive.withSession(same)).isEmpty());return null;
            }catch(IOException failure){throw new java.io.UncheckedIOException(failure);}});
        }
    }
    @Test void returnedAndAcceptedRecorderStatusAreNotAppliedAndOriginalQuerySelectorRemainsIntact()throws Exception{
        for(var mode:List.of(DriverActionHistoryCodec.Recording.RETURNED,DriverActionHistoryCodec.Recording.ACCEPTED_RETURN)){
            try(var fixture=fixture(mode.name(),false)){
                var material=new Materials(fixture,Optional.of(mode));install(fixture,material);var publisher=publisher(fixture,material);
                var actual=fixture.coordinator.execute(fixture.command("actual-recording-"+mode.name()));assertTrue(actual.applied().isEmpty());
                fixture.writer.locked(same->{try{
                    var published=assertInstanceOf(DriverActionHistoryPublisher.Published.class,publisher.completed(same,actual));assertTrue(published.legacyRow().isPresent());
                    var known=known(fixture,same);var coverage=known.actionRows().getLast();
                    assertInstanceOf(DriverSnapshotFacts.LegacyHistoryRow.class,coverage.coverageSource());
                    var row=DriverJson.object(fixture.archive.withSession(same).loadMaterial(coverage.originalResult()).bytes(),DriverJson.MAX_NATIVE_BYTES);
                    DriverActionHistoryCodec.verifyLegacy(same,actual,row,fixture.archive.withSession(same));
                    boolean recorded=DriverActionHistoryCodec.recordedOk(actual,row);assertEquals(mode==DriverActionHistoryCodec.Recording.RETURNED,recorded);
                    assertEquals(new Bool(recorded),row.get("ok"));
                    int writes=fixture.nativeActionWrites(),reads=fixture.nativeReadWrites();String head=same.head().digest();
                    var original=McpAutoTurnEncoder.originalBusiness(actual,known,fixture.archive.withSession(same)).orElseThrow();
                    assertArrayEquals(material.result.bytes(),original.bytes());
                    assertEquals(new Text("fixture-original-query-selector"),DriverJson.object(original.bytes(),65536).get("step"));
                    assertEquals(new Bool(false),DriverJson.object(original.bytes(),65536).get("accepted"));
                    assertEquals(head,same.head().digest());assertEquals(writes,fixture.nativeActionWrites());assertEquals(reads,fixture.nativeReadWrites());
                    var changed=row.with("ok",new Bool(!recorded));assertThrows(IllegalArgumentException.class,()->DriverActionHistoryCodec.verifyLegacy(actual,changed,fixture.archive.withSession(same)));return null;
                }catch(IOException failure){throw new java.io.UncheckedIOException(failure);}});
            }
        }
    }
    @Test void unknownActualSubmissionCannotMintCoverageAndAutoDoesNotResolveItThroughAnotherNativeCall()throws Exception{
        try(var fixture=fixture("unknown",true)){
            var material=new Materials(fixture,Optional.empty());var publisher=publisher(fixture,material);
            var actual=fixture.coordinator.execute(fixture.command("actual-unknown-auto-history"));assertFalse(actual.settled());
            fixture.writer.locked(same->{try{
                int writes=fixture.nativeActionWrites(),reads=fixture.nativeReadWrites();String head=same.head().digest();
                assertInstanceOf(DriverActionHistoryPublisher.Unchanged.class,publisher.completed(same,actual));
                assertTrue(McpAutoTurnEncoder.originalBusiness(actual,known(fixture,same),fixture.archive.withSession(same)).isEmpty());assertEquals(0,material.captures);
                assertEquals(head,same.head().digest());assertEquals(writes,fixture.nativeActionWrites());assertEquals(reads,fixture.nativeReadWrites());return null;
            }catch(IOException failure){throw new java.io.UncheckedIOException(failure);}});
        }
    }
    private ActionWriterIntegrationFixture fixture(String label,boolean loseAck)throws Exception{
        var held=new AtomicReference<ActionWriterIntegrationFixture>();
        var scenario=new ActionWriterIntegrationFixture.SoftwareActionScenario(DIRECT,"game.command."+DIRECT.value(),(command,attempt,dispatch)->{
            var actual=held.get();var ack=assertInstanceOf(NativeActionPort.AckReceived.class,dispatch);
            assertEquals(new Bool(false),DriverJson.object(ack.originalResultToken().orElseThrow().bytes(),65536).get("accepted"));
            return new ActionPorts.RejectionObserved(new ActionState.Rejected(attempt.requestId(),"actual controlled rejection",actual.archive.referenceOf(dispatch)));
        },()->{},()->raw(new Obj(Map.of("accepted",new Bool(false)))));
        var fixture=new ActionWriterIntegrationFixture(directory.resolve(label),loseAck,scenario);held.set(fixture);return fixture;
    }
    private static DriverSnapshotFacts.Known known(ActionWriterIntegrationFixture fixture,Session same)throws IOException{
        return fixture.driverAuthority().withFrozenFacts(same,frozen->assertInstanceOf(DriverSnapshotFacts.Known.class,frozen.state()));
    }
    private static void install(ActionWriterIntegrationFixture fixture,Materials material)throws IOException{fixture.bindAdditionalArchivedVerifier(material.binding());}
    private static DriverActionHistoryPublisher publisher(ActionWriterIntegrationFixture fixture,Materials material)throws IOException{
        var publisher=new DriverActionHistoryPublisher(fixture.driverAuthority(),fixture.journal,fixture.archive,material,List.of(fixture.observationSource().sourceRef()));
        fixture.bindAdditionalTransitionAuthority(WriterContracts.DRIVER_ACTION_HISTORY_KIND,publisher);return publisher;
    }
    private static final class Materials implements DriverActionHistoryPublisher.MaterialSource{
        private final ActionWriterIntegrationFixture fixture;private final Optional<DriverActionHistoryCodec.Recording> mode;private int captures;
        private final RawJson result=new RawJson("{\"accepted\":false,\"fraction\":1.0,\"step\":\"fixture-original-query-selector\"}".getBytes(java.nio.charset.StandardCharsets.UTF_8));
        Materials(ActionWriterIntegrationFixture fixture,Optional<DriverActionHistoryCodec.Recording> mode){this.fixture=fixture;this.mode=mode;}
        NativeRecordedEvidenceVerifier.Binding binding(){return new NativeRecordedEvidenceVerifier.Binding(DIRECT,fixture.observationSource().sourceRef(),(head,receipt,archive)->requireRejected(receipt,archive));}
        public List<ExactRef> sources(){return List.of(fixture.observationSource().sourceRef());}
        public void requireOwner(DriverStateAssembler authority,ActionJournal journal,ActionPorts.OutcomeArchive archive){assertSame(fixture.driverAuthority(),authority);assertSame(fixture.journal,journal);assertSame(fixture.archive,archive);}
        private List<DriverActionHistoryCodec.Evidence> evidence(ActionReceipt actual){
            var attempt=ActionTransitions.attempt(actual.state()).orElseThrow();var dispatch=ActionTransitions.dispatch(actual.state()).orElseThrow();
            return List.of(new DriverActionHistoryCodec.Evidence(DriverActionHistoryCodec.EvidenceKind.NATIVE_FRAME,attempt.guard().nativeEvidence()),
                    new DriverActionHistoryCodec.Evidence(DriverActionHistoryCodec.EvidenceKind.MATERIAL,fixture.archive.referenceOf(dispatch)));
        }
        public DriverActionHistoryCodec.OriginalMaterial capture(Session same,ActionReceipt actual,ActionPorts.OutcomeArchive archive)throws IOException{
            captures++;DriverActionHistoryCodec.OriginalMaterial material=mode.isPresent()?new DriverActionHistoryCodec.Legacy(mode.orElseThrow(),Optional.of(archive.preserveMaterial(result)),Optional.empty(),evidence(actual),sources()):
                    new DriverActionHistoryCodec.CanonicalOnly(DriverActionHistoryCodec.CanonicalReason.DIRECT_API_WITHOUT_LEGACY_RECORDER,evidence(actual),sources());
            requireOriginal(same,actual,material,archive);return material;
        }
        public void requireOriginal(Session same,ActionReceipt actual,DriverActionHistoryCodec.OriginalMaterial material,ActionPorts.OutcomeArchive archive)throws IOException{
            fixture.writer.requireSession(same);assertEquals(evidence(actual),material.evidence());assertEquals(sources(),material.producers());
            if(mode.isPresent()){
                var legacy=assertInstanceOf(DriverActionHistoryCodec.Legacy.class,material);assertEquals(mode.orElseThrow(),legacy.recording());assertArrayEquals(result.bytes(),archive.loadMaterial(legacy.result().orElseThrow()).bytes());
            }else assertInstanceOf(DriverActionHistoryCodec.CanonicalOnly.class,material);
            var verifier=new NativeRecordedEvidenceVerifier(fixture.archive,fixture.journal::borrowedWriterSession,(borrowed,ref,maximum)->fixture.archive.readArtifact(borrowed,ref,maximum),fixture.frameLoader(),List.of(binding()));
            verifier.verify(same.head(),actual);requireRejected(actual,archive);
        }
        private static void requireRejected(ActionReceipt actual,ActionPorts.OutcomeArchive archive){
            assertEquals(DIRECT,actual.command().operation());var settled=assertInstanceOf(ActionState.Settled.class,actual.state());var rejected=assertInstanceOf(ActionState.Rejected.class,settled.settlement());
            var ack=assertInstanceOf(NativeActionPort.AckReceived.class,settled.dispatch());assertEquals(ack.requestId(),rejected.requestId());assertEquals(archive.referenceOf(ack),rejected.originalEvidence());assertEquals(ack,archive.load(rejected.originalEvidence()));
        }
    }
    private static RawJson raw(Value value){return new RawJson(DriverJson.encode(value));}
}
