package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;

import java.io.UncheckedIOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.application.planning.sway.*;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.continuity.writer.WriterContracts.FileIdentity;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Physical sidecar custody of strictly recorded DATA, without claiming a canonical Sway publication.
 * The Sway owner's producer/writer replay tests must establish actual event and child membership.
 */
final class NativeArchiveSwaySidecarTest {
    @TempDir Path root;
    @Test void recordedSchedulerSidecarIsPreservedBeforeSoleReceiptCodecAndCannotGrantBusinessOrRepairOriginals() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(root.resolve("archive"), false)) {
            var ready = fixture.ready(); var base = ready.request(); var archive = fixture.archive;
            var received = NativeArchiveSupportingMaterialsTest.frame(base, 17, false, Instant.now());
            var sem = ready.semanticEvidence().orElseThrow(); var full = archive.loadMaterial(sem.originalDriver());
            var facts = NativeArchiveSupportingMaterialsTest.actualFacts(received, base.source(), sem.originalDriver(), full, archive);
            var frame = assertInstanceOf(DriverObservationAssembler.Complete.class,
                    new DriverObservationAssembler().assemble(received, facts, archive.preserveNativeFrame(received)));
            var operation = OrdinarySwayPolicy.OPERATION;
            var expected = new ProposalLifecycle.ExpectedPostcondition(1, frame.identity(), frame.source(), "controlled-recorded-sway-data/v1",
                    List.of(new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("sway.scheduler_completed"), true)));
            var parent = new ActionCommand("recorded-sway-parent", frame.identity(), frame.source(), frame.sessionId(), operation,
                    new OpportunityJson.Obj(Map.of()), expected, new JointBudgetSelector.Claims(Set.of(), Set.of(), Set.of(), Set.of()), Instant.now().plusSeconds(20));
            var guard = new GuardEvidence(frame.identity(), frame.source(), frame.sessionId(), frame.connectionGeneration(), operation,
                    frame.originalEvidence(), frame.originalEvidence(), "controlled-recorded-data", frame.observedAt(), parent.deadline());
            var execution = new CompositeExecution("controlled-recorded-sway-handler", frame.observedAt(), guard, List.of());
            byte[] external = "{\"recorded_data_only\":true,\"canonical_publication_proven\":false}".getBytes(StandardCharsets.UTF_8);
            Path externalPath = root.resolve("ordinary-external-original.json"); Files.write(externalPath, external);
            var outside = new ExactRef(externalPath.toAbsolutePath().toString(), external.length, ActionCodec.sha256(external));
            // Deliberately recorded-only identity tokens: an archive must neither open these as its
            // own material locators nor interpret constructed tokens as writer/domain membership.
            var body = new DomainBodies.BodyRef(DomainBodies.Slot.SWAY, SwayFormalState.SCHEMA, outside,
                    new FileIdentity("1", "2", "3", Instant.now().toString(), external.length), List.of(base.source().sourceRef()));
            var witness = new SwayCanonicalDomain.PublicationWitness(outside, body, body, outside, 1, "a".repeat(64), "b".repeat(64));
            var read = fixture.lastNestedRead.get(); ExactRef readRef = archive.preserveRead(read);
            var proof = new SwaySchedulerCompletion(parent.actionId(), ActionCodec.bodySha256(parent), outside, witness,
                    NativeEffectEvidence.basis(frame), List.of(readRef), List.of(), Optional.empty(), Optional.empty(),
                    SwaySchedulerCompletion.Continuation.FRESH_FULL_PLAN_REQUIRED, new SwaySchedulerCompletion.NoNewBusiness());
            var receipt = new ActionReceipt(1, 1, parent, ActionCodec.bodySha256(parent), new ActionState.CompositeSettled(execution, new ActionState.SwaySchedulerCompleted(proof)));
            var rawProof = new RawJson(proof.encode()); byte[] ledger = fixture.ledgerBytes();
            assertThrows(UncheckedIOException.class, () -> archive.materialReferenceOf(rawProof));
            ExactRef kept = archive.preserveReceipt(receipt), sidecar = archive.materialReferenceOf(rawProof);
            var cold = archive.loadReceipt(kept); assertEquals(receipt, cold);
            assertArrayEquals(proof.encode(), archive.loadMaterial(sidecar).bytes());
            assertArrayEquals(proof.encode(), ((ActionState.SwaySchedulerCompleted) ((ActionState.CompositeSettled) cold.state()).settlement()).proof().encode());
            assertEquals(ActionReceipt.Outcome.APPLIED_CONFIRMED, cold.outcome()); assertFalse(cold.visibleGameplay()); assertFalse(cold.eligibleAdvance());
            var otherParent = new ActionCommand("different-sway-parent", parent.before(), parent.source(), parent.sessionId(), parent.operation(), parent.arguments(), parent.expected(), parent.claims(), parent.deadline());
            var crossed = new ActionReceipt(1, 1, otherParent, ActionCodec.bodySha256(otherParent), receipt.state());
            assertThrows(IllegalArgumentException.class, () -> archive.preserveReceipt(crossed));
            Files.writeString(Path.of(sidecar.path()), "{\"corrupt\":true}");
            assertThrows(UncheckedIOException.class, () -> archive.loadReceipt(kept));
            assertEquals("{\"corrupt\":true}", Files.readString(Path.of(sidecar.path())));
            assertArrayEquals(external, Files.readAllBytes(externalPath)); assertArrayEquals(ledger, fixture.ledgerBytes());
        }
    }
}
