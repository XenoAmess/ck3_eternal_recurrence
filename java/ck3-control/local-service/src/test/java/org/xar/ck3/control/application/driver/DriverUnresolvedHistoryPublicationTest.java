package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.action.ActionPorts.OutcomeArchive;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.effects.RootGuardEvidence;
import org.xar.ck3.control.application.history.DriverPublicExecuteFailureMaterial;
import org.xar.ck3.control.application.history.DriverPublicExecuteFailureRowProducer;
import org.xar.ck3.control.application.history.DriverReturnedControlHistoryRowProducer;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Negatives use the real software writer. Positive assertion entry points require the actual installed private Root issuers;
 * this test creates neither issuer, Known, receipt nor Native custody. Missing Root inputs are not a software positive. */
public final class DriverUnresolvedHistoryPublicationTest {
    @TempDir Path directory;
    private static final OperationKey OP=new OperationKey("fixture-unresolved-history-source");
    @Test void noInstalledIssuerCanBeReplacedByAnInvocationLambda()throws Exception {
        var scenario=new ActionWriterIntegrationFixture.SoftwareActionScenario(OP,"game.command."+OP.value(),
                (command,attempt,dispatch)->new ActionPorts.Pending("real software unresolved postcondition",List.of()),()->{},
                ()->new RawJson(DriverJson.encode(new OpportunityJson.Obj(Map.of("accepted",new OpportunityJson.Bool(false))))));
        try(var fixture=new ActionWriterIntegrationFixture(directory.resolve("uninstalled"),false,scenario)){
            var publisher=publisher(fixture);fixture.ready();
            fixture.writer.locked(same->{
                var before=known(fixture.driverAuthority(),same);String head=same.head().digest();
                assertThrows(IllegalArgumentException.class,()->publisher.enqueuePublicExecuteFailure(same,()->null));
                assertThrows(IllegalArgumentException.class,()->publisher.enqueueReturnedControl(same,()->null));
                assertFalse(publisher.hasPending(same));assertTrue(publisher.flushActualReads(same).isEmpty());
                assertArrayEquals(before.driver().encode(),known(fixture.driverAuthority(),same).driver().encode());assertEquals(head,same.head().digest());
                assertEquals(0,fixture.nativeActionWrites());return null;
            });
        }
    }
    @Test void actualUnknownWithoutAnyHistorySuffixCannotMintLiveOrHistoricalException()throws Exception {
        var scenario=new ActionWriterIntegrationFixture.SoftwareActionScenario(OP,"game.command."+OP.value(),
                (command,attempt,dispatch)->new ActionPorts.Pending("no confirmed postcondition",List.of()),()->{},
                ()->new RawJson(DriverJson.encode(new OpportunityJson.Obj(Map.of("accepted",new OpportunityJson.Bool(false))))));
        try(var fixture=new ActionWriterIntegrationFixture(directory.resolve("no-suffix"),false,scenario)){
            var publisher=publisher(fixture);var action=fixture.coordinator.execute(fixture.command("unresolved-no-row"));
            assertInstanceOf(ActionState.Unknown.class,action.state());assertFalse(action.settled());
            fixture.writer.locked(same->{
                var current=known(fixture.driverAuthority(),same);var bound=fixture.archive.withSession(same);
                var original=RootGuardEvidence.originalDriverSource(((ActionState.Unknown)action.state()).attempt().orElseThrow().guard(),bound).driverRef();
                var target=bound.materialReferenceOf(RawJson.fullMaterial(current.driver().encode()));String head=same.head().digest();
                assertThrows(IllegalArgumentException.class,()->publisher.requireUnresolvedHistoryExtension(same,action,original,current));
                assertThrows(IllegalArgumentException.class,()->publisher.requireHistoricalUnresolvedHistoryExtension(same,action,original,target,same.head()));
                assertEquals(head,same.head().digest());assertEquals(1,fixture.nativeActionWrites());assertFalse(publisher.hasPending(same));return null;
            });
        }
    }
    public record Published(DriverSnapshotFacts.Known actualCurrent,ExactRef row,WriterContracts.Head actualTarget) { }
    /** Called only by a genuine installed NT Root source fixture, after its immutable physical scope has closed. */
    public static Published assertActualReturnedPublication(Session same,DriverStateAssembler authority,DriverReadHistoryPublisher publisher,
            OutcomeArchive archive,RootReadContractCatalog catalog,DriverReturnedControlHistoryRowProducer.Source actualSource,
            DriverReturnedControlHistoryRowProducer.OriginalReturned actual)throws Exception {
        publisher.requireOwner(authority,archive,catalog);assertSame(actualSource,actual.issuer());var bound=archive.withSession(same);
        var originals=actualSource.requireOriginal(same,authority,bound,actual);var before=known(authority,same);
        var queued=assertInstanceOf(DriverReturnedControlHistoryRowProducer.Queued.class,publisher.enqueueReturnedControl(same,actual));
        assertEquals(queued,publisher.enqueueReturnedControl(same,actual));assertArrayEquals(before.driver().encode(),known(authority,same).driver().encode());
        publisher.flushActualReads(same).orElseThrow();var after=known(authority,same);assertOneHistory(before,after);
        var row=DriverReturnedControlHistoryRowProducer.decode(after.driver().commandHistory().getLast().originalRow().json());
        assertFalse(row.ok());assertFalse(row.toJson().members().containsKey("error"));assertEquals(queued.originalRow(),bound.materialReferenceOf(RawJson.fullMaterial(row.encode())));
        int count=after.driver().commandHistory().size();String head=same.head().digest();
        DriverReturnedControlHistoryRowProducer.replayOriginals(bound,catalog,actualSource,row);
        var unresolved=ContinuityActionJournal.lookup(same.head().state(),originals.actual().command().actionId(),bound).orElseThrow();
        assertInstanceOf(ActionState.Unknown.class,unresolved.state());assertFalse(unresolved.settled());
        var proof=publisher.requireUnresolvedHistoryExtension(same,unresolved,originals.beforeDriver(),after);proof.requireCurrent(same);
        assertEquals(queued.originalRow(),bound.materialReferenceOf(RawJson.fullMaterial(row.encode())));
        assertFalse(proof.eventReferences().isEmpty());assertEquals(head,same.head().digest());assertEquals(count,known(authority,same).driver().commandHistory().size());
        return new Published(after,queued.originalRow(),same.head());
    }
    /** The original typed Root catch is supplied; this helper never manufactures a failure invocation or Throwable. */
    public static Published assertActualFailurePublication(Session same,DriverStateAssembler authority,DriverReadHistoryPublisher publisher,
            OutcomeArchive archive,RootReadContractCatalog catalog,DriverPublicExecuteFailureMaterial.Source actualSource,
            DriverPublicExecuteFailureMaterial.OriginalInvocation actual)throws Exception {
        publisher.requireOwner(authority,archive,catalog);assertSame(actualSource,actual.issuer());var bound=archive.withSession(same);
        var originals=actualSource.requireOriginal(same,authority,bound,actual);var before=known(authority,same);
        var queued=assertInstanceOf(DriverPublicExecuteFailureMaterial.Queued.class,publisher.enqueuePublicExecuteFailure(same,actual));assertEquals(queued,publisher.enqueuePublicExecuteFailure(same,actual));
        publisher.flushActualReads(same).orElseThrow();var after=known(authority,same);assertOneHistory(before,after);
        var row=DriverPublicExecuteFailureRowProducer.decode(after.driver().commandHistory().getLast().originalRow().json());
        assertFalse(row.ok());assertEquals(originals.error().recorded(),row.error());assertEquals(originals.result().isPresent(),row.result().isPresent());
        String head=same.head().digest();DriverPublicExecuteFailureRowProducer.replayOriginals(bound,row);assertEquals(head,same.head().digest());
        if(originals.unresolvedAction().isPresent()){
            var action=bound.loadReceipt(originals.unresolvedAction().orElseThrow());var proof=publisher.requireUnresolvedHistoryExtension(same,action,originals.beforeDriver(),after);proof.requireCurrent(same);
        }
        assertEquals(queued.originalRow(),bound.materialReferenceOf(RawJson.fullMaterial(row.encode())));return new Published(after,queued.originalRow(),same.head());
    }
    /** Uses an actual recorded history point; no historical Known is constructed. */
    public static void assertActualHistoricalPublication(Session same,DriverReadHistoryPublisher publisher,ActionReceipt originalUnknown,
            ExactRef originalBeforeDriver,ExactRef actualCurrentDriver,WriterContracts.Head actualTarget)throws Exception {
        String current=same.head().digest();var proof=publisher.requireHistoricalUnresolvedHistoryExtension(same,originalUnknown,originalBeforeDriver,actualCurrentDriver,actualTarget);
        proof.requireHistorical(same);assertEquals(originalBeforeDriver,proof.originalDriver());assertEquals(actualCurrentDriver,proof.currentDriver());assertFalse(proof.eventReferences().isEmpty());assertEquals(current,same.head().digest());
    }
    public static void assertActualFullSnapshot(PublicSnapshotCodec.FullSnapshotOriginals actual)throws Exception {
        var wire=PublicSnapshotCodec.encode(PublicSnapshotCodec.exportFull(actual,true));assertEquals(actual.actual().semantic(),PublicSnapshotCodec.decode(wire));
    }
    public static void assertActualOperatorWithoutRebind(Session same,DriverStateAssembler authority,
            DriverActionHistoryPublisher publisher,ActionReceipt actual)throws Exception {
        var before=known(authority,same);String head=same.head().digest();
        var result=assertInstanceOf(DriverActionHistoryPublisher.Unchanged.class,publisher.completed(same,actual));
        assertEquals(DriverActionHistoryPublisher.Reason.OPERATOR_NO_REBIND_RECEIPT_VERIFIED,result.reason());
        var after=known(authority,same);assertEquals(before.stamp(),after.stamp());assertArrayEquals(before.driver().encode(),after.driver().encode());
        assertEquals(before.actionRows(),after.actionRows());assertEquals(head,same.head().digest());
    }
    private static void assertOneHistory(DriverSnapshotFacts.Known before,DriverSnapshotFacts.Known after){
        assertEquals(before.stamp().driverVersion()+1,after.stamp().driverVersion());assertEquals(before.stamp().episodeEpoch(),after.stamp().episodeEpoch());
        assertEquals(before.driver().commandHistory().size()+1,after.driver().commandHistory().size());assertEquals(before.actionRows(),after.actionRows());assertTrue(after.observation().isEmpty());
        assertEquals(OpportunityJson.Nil.INSTANCE,after.auxiliary().get("capability_observed_native_source"));
        assertArrayEquals(after.driver().encode(),DriverStateSnapshot.decodeComplete(after.driver().encode()).encode());
    }
    private static DriverSnapshotFacts.Known known(DriverStateAssembler authority,Session same)throws java.io.IOException {return authority.withFrozenFacts(same,frozen->assertInstanceOf(DriverSnapshotFacts.Known.class,frozen.state()));}
    private static DriverReadHistoryPublisher publisher(ActionWriterIntegrationFixture fixture)throws java.io.IOException {
        var publisher=new DriverReadHistoryPublisher(fixture.driverAuthority(),fixture.archive,fixture.reads.catalog(),List.of(fixture.observationSource().sourceRef()));
        fixture.bindAdditionalTransitionAuthority(WriterContracts.DRIVER_READ_HISTORY_KIND,publisher);return publisher;
    }
}
