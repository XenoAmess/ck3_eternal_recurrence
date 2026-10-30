package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import java.nio.file.Path;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.governance.GovernanceOpeningDocument;
import org.xar.ck3.control.application.planning.governance.GovernanceObservationSupplier.OpeningStage;
import org.xar.ck3.control.application.planning.governance.GovernancePolicies;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;

/** The actual archive/canonical lookup feeds both real Opening consumer and pending DATA producer seams. */
final class OpeningPreparedOnlyRecoveryTest {
    @TempDir Path root;
    private ActionWriterIntegrationFixture fixture(String name) throws Exception {
        var action=new ActionWriterIntegrationFixture.SoftwareActionScenario(GovernancePolicies.FOCUS,
                "game.command.pause-map",(command,attempt,dispatch)->new ActionPorts.Pending("actual software focus remains unresolved",List.of(attempt.guard().nativeEvidence())),
                ()->{},Optional.empty(),Optional.empty(),true,Optional.empty());
        var reads=new ActionWriterIntegrationFixture.SoftwareReadScenario("d".repeat(64),"opening-prepared-only",source->List.of(),
                request->{throw new AssertionError("Opening recovery cannot issue a planning query");});
        return new ActionWriterIntegrationFixture(root.resolve(name),false,reads,List.of(action),java.time.Duration.ofSeconds(60));
    }
    private static ActionCommand fresh(ActionCommand old,String id,Instant deadline) {
        return new ActionCommand(id,old.origin(),old.source(),old.sessionId(),old.operation(),old.arguments(),old.expectation(),old.claims(),deadline,old.protocolIdentity());
    }
    private static GovernanceOpeningDocument.Document document(ActionCommand command,ExactRef original) {
        return new GovernanceOpeningDocument.Document(command.before(),command.source(),command.sessionId(),OpeningStage.AWAIT_RECEIPT,
                Optional.empty(),Optional.empty(),List.of(original),Optional.of(original),Optional.empty());
    }
    @Test void preparedOnlyArchiveBuildsFreshPlanningGateWithoutMutatingItsOriginal() throws Exception {
        try(var actual=fixture("planning")) {
            var old=fresh(actual.command("prepared-before-intent"),"prepared-before-intent",Instant.now().minusSeconds(10));
            actual.writer.locked(same->{
                var archive=actual.archive.withSession(same);
                var original=archive.preserveMaterial(new RawJson(ActionCodec.encodeCommand(old)));
                var pending=document(old,original);byte[] bytes=GovernanceOpeningDocument.encode(pending);
                String head=same.head().digest();int writes=actual.nativeActionWrites(),reads=actual.nativeReadWrites();
                var action=RootGovernanceOpeningInputs.actualAction(archive,same.head().state(),pending);
                assertTrue(action.isEmpty());
                assertDoesNotThrow(()->OpeningTransitions.requireExisting(pending,action));
                var gate=RootGovernanceOpeningInputs.openingGate(pending,old.before(),action);
                assertEquals(OpeningStage.AWAIT_SUBMIT,gate.stage());assertTrue(gate.action().isEmpty());
                assertEquals(OpeningStage.AWAIT_RECEIPT,pending.stage());assertEquals(Optional.of(original),pending.preparedCommand());
                assertArrayEquals(bytes,GovernanceOpeningDocument.encode(pending));
                assertEquals(head,same.head().digest());assertEquals(writes,actual.nativeActionWrites());assertEquals(reads,actual.nativeReadWrites());
                return null;
            });
        }
    }
    @Test void freshPreparedReplacementRetainsTheOldOriginalAndUsesTheCurrentCommand() throws Exception {
        try(var actual=fixture("replacement")) {
            var observed=actual.command("prepared-before-intent");
            var old=fresh(observed,observed.actionId(),Instant.now().minusSeconds(10));
            var current=fresh(observed,"fresh-ordinary-plan",Instant.now().plusSeconds(30));
            actual.writer.locked(same->{
                var archive=actual.archive.withSession(same);
                var original=archive.preserveMaterial(new RawJson(ActionCodec.encodeCommand(old)));
                var replacement=archive.preserveMaterial(new RawJson(ActionCodec.encodeCommand(current)));
                var pending=document(old,original);String head=same.head().digest();
                var previous=ContinuityActionJournal.lookup(same.head().state(),old.actionId(),archive);
                var next=ContinuityActionJournal.lookup(same.head().state(),current.actionId(),archive);
                byte[] changed=OpeningTransitions.pending(pending,current,replacement,new ArrayList<>(pending.originals()),previous,next);
                var retained=GovernanceOpeningDocument.decode(changed);
                assertEquals(OpeningStage.AWAIT_RECEIPT,retained.stage());assertEquals(Optional.of(replacement),retained.preparedCommand());
                assertTrue(retained.originals().contains(original));assertTrue(retained.originals().contains(replacement));
                assertTrue(retained.actionReceipt().isEmpty());assertTrue(retained.checkpoint().isEmpty());
                assertEquals(old,ActionCodec.decodeCommand(archive.loadMaterial(original).bytes()));
                assertEquals(current,ActionCodec.decodeCommand(archive.loadMaterial(replacement).bytes()));
                assertTrue(current.deadline().isAfter(Instant.now()));assertTrue(old.deadline().isBefore(Instant.now()));
                assertEquals(head,same.head().digest());assertEquals(0,actual.nativeActionWrites());return null;
            });
        }
    }
    @Test void actualUnknownKeepsItsCommandAndCannotBeSuperseded() throws Exception {
        try(var actual=fixture("unknown")) {
            var command=actual.command("original-unknown");
            var unknown=actual.coordinator.execute(command);
            assertEquals(ActionReceipt.Outcome.UNRESOLVED,unknown.outcome());
            int writes=actual.nativeActionWrites();long sequence=actual.sequence();
            actual.writer.locked(same->{
                var archive=actual.archive.withSession(same);
                var original=archive.preserveMaterial(new RawJson(ActionCodec.encodeCommand(command)));
                var pending=document(command,original);String head=same.head().digest();
                var canonical=RootGovernanceOpeningInputs.actualAction(archive,same.head().state(),pending);
                assertEquals(Optional.of(unknown),canonical);
                assertThrows(IllegalArgumentException.class,()->OpeningTransitions.requireExisting(pending,canonical));
                var gate=RootGovernanceOpeningInputs.openingGate(pending,command.before(),canonical);
                assertEquals(OpeningStage.AWAIT_RECEIPT,gate.stage());assertEquals(Optional.of(unknown),gate.action());
                var forbidden=fresh(command,"cannot-replace-unknown",Instant.now().plusSeconds(30));
                var nextRef=archive.preserveMaterial(new RawJson(ActionCodec.encodeCommand(forbidden)));
                assertThrows(IllegalArgumentException.class,()->OpeningTransitions.pending(pending,forbidden,nextRef,
                        new ArrayList<>(pending.originals()),canonical,Optional.empty()));
                assertEquals(Optional.of(original),pending.preparedCommand());assertEquals(head,same.head().digest());return null;
            });
            assertEquals(unknown,actual.coordinator.execute(command));
            assertEquals(writes,actual.nativeActionWrites());assertEquals(sequence,actual.sequence());
        }
    }
}
