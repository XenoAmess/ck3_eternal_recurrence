package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;

/** Real software action/writer publication plus readonly full-material DATA replay. No new Known or Native permit is minted. */
final class DriverActionFullMaterialTest {
    @TempDir Path directory;
    private static final OperationKey DIRECT=new OperationKey("fixture-full-material-rejection");
    @Test void declaredMaterialUsesTheFullLaneWhileNativeAckAndCurrentDriverRemainUnchanged()throws Exception {
        var held=new AtomicReference<ActionWriterIntegrationFixture>();
        var scenario=new ActionWriterIntegrationFixture.SoftwareActionScenario(DIRECT,"game.command."+DIRECT.value(),(command,attempt,dispatch)->{
            var actual=held.get();var ack=assertInstanceOf(NativeActionPort.AckReceived.class,dispatch);
            return new ActionPorts.RejectionObserved(new ActionState.Rejected(attempt.requestId(),"actual software rejection",actual.archive.referenceOf(ack)));
        },()->{},()->new RawJson(DriverJson.encode(new Obj(Map.of("accepted",new Bool(false))))));
        try(var fixture=new ActionWriterIntegrationFixture(directory.resolve("actual-material"),false,scenario)) {
            held.set(fixture);var large=RawJson.fullMaterial(("{\"opaque\":"+"9".repeat(70_000)+"}").getBytes(java.nio.charset.StandardCharsets.UTF_8));
            assertThrows(IllegalArgumentException.class,()->new RawJson(large.bytes()));
            var witness=fixture.writer.locked(same->fixture.archive.withSession(same).preserveMaterial(large));var materials=new ActualMaterials(fixture,witness);
            fixture.bindAdditionalArchivedVerifier(materials.binding());
            var publisher=new DriverActionHistoryPublisher(fixture.driverAuthority(),fixture.journal,fixture.archive,materials,List.of(fixture.observationSource().sourceRef()));
            fixture.bindAdditionalTransitionAuthority(WriterContracts.DRIVER_ACTION_HISTORY_KIND,publisher);
            var receipt=fixture.coordinator.execute(fixture.command("full-material-action"));assertTrue(receipt.settled());assertTrue(receipt.applied().isEmpty());
            fixture.writer.locked(same->{
                var before=fixture.driverAuthority().withFrozenFacts(same,frozen->assertInstanceOf(DriverSnapshotFacts.Known.class,frozen.state()));
                int writes=fixture.nativeActionWrites(),reads=fixture.nativeReadWrites();
                var published=assertInstanceOf(DriverActionHistoryPublisher.Published.class,publisher.completed(same,receipt));
                var committed=DriverActionHistoryState.findCommittedCoverage(same,receipt,fixture.archive.withSession(same)).orElseThrow();
                assertEquals(published.originalSource(),committed.originalSource());assertTrue(committed.legacyRow().isEmpty());
                assertEquals(large,fixture.archive.withSession(same).loadFullMaterial(witness));
                assertThrows(RuntimeException.class,()->fixture.archive.withSession(same).loadMaterial(witness));
                // A large immutable Driver is DATA for this decoder exercise. It is never installed as current or claimed to be the canonical publication.
                var rows=new ArrayList<>(before.driver().commandHistory());
                var opaque=new Obj(Map.of("index",new IntegerValue(BigInteger.valueOf(rows.size()+1L)),"command",new Text("opaque-codec-boundary"),"ok",new Bool(true),"result",DriverJson.object(large.bytes(),RawJson.MAXIMUM_BYTES)));
                rows.add(new DriverStateSnapshot.HistoryEntry(rows.size()+1L,new DriverStateSnapshot.Value(DriverJson.encode(opaque))));
                var original=before.driver();var data=new DriverStateSnapshot.Complete(original.session(),rows,original.lastCheckpoint(),original.rollbackWarFailure(),original.managedRestoreTransaction(),original.successionExpectation(),original.successionLifecycle(),original.campaignGoal(),original.rollbackWarFailures());
                var dataRef=fixture.archive.preserveMaterial(RawJson.fullMaterial(data.encode()));
                assertArrayEquals(data.encode(),DriverStateSnapshot.decodeComplete(fixture.archive.withSession(same).loadFullMaterial(dataRef).bytes()).encode());
                var actual=committed.publication();var codecOnly=new DriverActionHistoryState.Publication("full-material-codec-only",actual.command(),actual.bodySha256(),actual.actionSequence(),actual.predecessor(),actual.beforeVersion(),actual.afterVersion(),actual.episodeEpoch(),dataRef,dataRef,actual.originalSource(),Optional.empty());
                String head=same.head().digest();
                DriverActionHistoryState.requireOriginal(same,codecOnly,receipt,fixture.archive.withSession(same));
                assertNotEquals(dataRef,DriverActionHistoryState.findCommittedCoverage(same,receipt,fixture.archive.withSession(same)).orElseThrow().beforeDriver());
                var current=fixture.driverAuthority().withFrozenFacts(same,frozen->assertInstanceOf(DriverSnapshotFacts.Known.class,frozen.state()));
                assertArrayEquals(original.encode(),current.driver().encode());assertEquals(before.stamp().driverVersion()+1,current.stamp().driverVersion());
                assertEquals(head,same.head().digest());assertEquals(writes,fixture.nativeActionWrites());assertEquals(reads,fixture.nativeReadWrites());return null;
            });
        }
    }
    private static final class ActualMaterials implements DriverActionHistoryPublisher.MaterialSource {
        private final ActionWriterIntegrationFixture fixture;private final ExactRef witness;
        ActualMaterials(ActionWriterIntegrationFixture fixture,ExactRef witness){this.fixture=fixture;this.witness=witness;}
        NativeRecordedEvidenceVerifier.Binding binding(){return new NativeRecordedEvidenceVerifier.Binding(DIRECT,fixture.observationSource().sourceRef(),(head,receipt,originals)->requireRejection(receipt,originals));}
        @Override public List<ExactRef> sources(){return List.of(fixture.observationSource().sourceRef());}
        @Override public void requireOwner(DriverStateAssembler authority,ActionJournal journal,ActionPorts.OutcomeArchive archive){assertSame(fixture.driverAuthority(),authority);assertSame(fixture.journal,journal);assertSame(fixture.archive,archive);}
        private DriverActionHistoryCodec.CanonicalOnly material(ActionReceipt actual){
            var attempt=ActionTransitions.attempt(actual.state()).orElseThrow();
            return new DriverActionHistoryCodec.CanonicalOnly(DriverActionHistoryCodec.CanonicalReason.DIRECT_API_WITHOUT_LEGACY_RECORDER,
                    List.of(new DriverActionHistoryCodec.Evidence(DriverActionHistoryCodec.EvidenceKind.NATIVE_FRAME,attempt.guard().nativeEvidence()),
                            new DriverActionHistoryCodec.Evidence(DriverActionHistoryCodec.EvidenceKind.MATERIAL,witness)),sources());
        }
        @Override public DriverActionHistoryCodec.OriginalMaterial capture(Session same,ActionReceipt actual,ActionPorts.OutcomeArchive originals)throws IOException {
            var material=material(actual);requireOriginal(same,actual,material,originals);return material;
        }
        @Override public void requireOriginal(Session same,ActionReceipt actual,DriverActionHistoryCodec.OriginalMaterial material,ActionPorts.OutcomeArchive originals)throws IOException {
            fixture.writer.requireSession(same);assertEquals(material(actual),material);
            var verifier=new NativeRecordedEvidenceVerifier(fixture.archive,fixture.journal::borrowedWriterSession,
                    (borrowed,ref,maximum)->fixture.archive.readArtifact(borrowed,ref,maximum),fixture.frameLoader(),List.of(binding()));
            verifier.verify(same.head(),actual);requireRejection(actual,originals);
            var raw=originals.loadFullMaterial(witness);assertEquals(witness.bytes(),raw.bytes().length);assertEquals(witness.sha256(),DriverJson.sha256(raw.bytes()));
        }
        private static void requireRejection(ActionReceipt actual,ActionPorts.OutcomeArchive originals){
            assertEquals(DIRECT,actual.command().operation());var settled=assertInstanceOf(ActionState.Settled.class,actual.state());
            var rejected=assertInstanceOf(ActionState.Rejected.class,settled.settlement());var ack=assertInstanceOf(NativeActionPort.AckReceived.class,settled.dispatch());
            assertEquals(ack.requestId(),rejected.requestId());assertEquals(originals.referenceOf(ack),rejected.originalEvidence());assertEquals(ack,originals.load(rejected.originalEvidence()));
            assertEquals(new Bool(false),DriverJson.object(ack.originalResultToken().orElseThrow().bytes(),DriverJson.MAX_NATIVE_BYTES).get("accepted"));
        }
    }
}
