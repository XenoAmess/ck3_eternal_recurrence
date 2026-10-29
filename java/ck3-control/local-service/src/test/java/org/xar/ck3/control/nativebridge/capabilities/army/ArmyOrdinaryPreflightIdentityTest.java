package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.ActionTransitions;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.effects.RootGuardEvidence;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;

/** Controlled packets exercise the real writer/read/archive producer; no Game qualification is implied. */
final class ArmyOrdinaryPreflightIdentityTest {
    @TempDir Path temporary;
    @Test void originalReadCannotMoveToAnotherDriverSessionConnectionFrameOrEvidenceIdentity() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(temporary.resolve("army-original-binding"), false)) {
            var result = fixture.coordinator.execute(fixture.command("original-source-binding"));
            var original = fixture.lastNestedRead.get(); assertNotNull(original);
            var attempt = ActionTransitions.attempt(result.state()).orElseThrow();
            long sequence = fixture.sequence(); int writes = fixture.nativeActionWrites();
            fixture.writer.locked(same -> {
                var before = RootGuardEvidence.loadFrame(attempt.guard(), fixture.archive.withSession(same), fixture.frameLoader());
                assertDoesNotThrow(() -> ArmyOrdinaryPreflight.bind(original, before));
                var identity = before.identity();
                var changedVersion = new ObservationIdentity(identity.machineId(), identity.game(), identity.frame(), identity.observationVersion() + 1);
                List<Complete> drifted = List.of(
                        new Complete(before.identity(), before.source(), before.sessionId() + "-other", before.connectionGeneration(), before.semantic(), before.originalEvidence(), before.observedAt(), before.fullBindingSha256()),
                        new Complete(before.identity(), before.source(), before.sessionId(), before.connectionGeneration().add(java.math.BigInteger.ONE), before.semantic(), before.originalEvidence(), before.observedAt(), before.fullBindingSha256()),
                        new Complete(changedVersion, before.source(), before.sessionId(), before.connectionGeneration(), before.semantic(), before.originalEvidence(), before.observedAt(), before.fullBindingSha256()),
                        new Complete(before.identity(), before.source(), before.sessionId(), before.connectionGeneration(), before.semantic(), new ExactRef("D:/controlled-fixture-only/other-source.json", 1, "a".repeat(64)), before.observedAt(), before.fullBindingSha256()),
                        new Complete(before.identity(), before.source(), before.sessionId(), before.connectionGeneration(), before.semantic(), before.originalEvidence(), before.observedAt(), before.fullBindingSha256().equals("a".repeat(64)) ? "b".repeat(64) : "a".repeat(64)));
                for (Complete drift : drifted) assertThrows(IllegalArgumentException.class, () -> ArmyOrdinaryPreflight.bind(original, drift));
                fixture.writer.requireSession(same); return null;
            });
            assertEquals(sequence, fixture.sequence()); assertEquals(writes, fixture.nativeActionWrites());
        }
    }
}
