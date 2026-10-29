package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.file.Path;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.RootGuardEvidence;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;

/** Controlled software packets exercise the actual writer/archive scope. This test supplies no live Native qualification. */
final class NativeOrdinaryWarAdmissionSessionTest {
    @TempDir Path temporary;
    @Test void actualWriterSessionFlowsIntoThePublicPreIntentGateAndArchiveScopeIsRestored() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(temporary.resolve("same-writer-gate"), false)) {
            var retained = fixture.coordinator.execute(fixture.command("source-session-frame"));
            var attempt = ActionTransitions.attempt(retained.state()).orElseThrow();
            var admission = new NativeOrdinaryWarAdmission(fixture.writer, fixture.archive, fixture.frameLoader());
            var declaration = new ArmyCalls.Declaration(PublicMethod.DECLARE_WAR,
                    new ArmyCalls.Revision(new ArmyTypes.Present<>(retained.command().before().frame().revision())), "42-8--1");
            var arguments = new ArmyOrdinaryActionArguments(ArmyOrdinaryActionArguments.Kind.DECLARE_WAR,
                    ArmyCallCodec.encode(declaration), List.of());
            var primitive = new NativeRequest("declare-war-42-8--1", Optional.of("game.command.declare-war-N"),
                    new RawJson(new byte[]{'{','}'}));
            var originalBasis = attempt.guard().supportingEvidence().getFirst();
            var calls = new AtomicInteger(); long originalSequence = fixture.sequence(); int originalWrites = fixture.nativeActionWrites();
            fixture.writer.locked(same -> {
                var bound = fixture.archive.withSession(same);
                var before = RootGuardEvidence.loadFrame(attempt.guard(), bound, fixture.frameLoader());
                var gates = admission.finalGates((current, selected, request) -> {
                    assertEquals(before, current); assertEquals(arguments, selected); assertEquals(primitive, request);
                    // The actual public prepare call has no inherited coordinator/archive ThreadLocal.
                    assertEquals(bound.loadMaterial(originalBasis), fixture.archive.loadMaterial(originalBasis));
                    calls.incrementAndGet();
                });
                assertThrows(IllegalStateException.class, () -> gates.verify(before, arguments, primitive));
                assertDoesNotThrow(() -> gates.verify(same, before, arguments, primitive));
                assertThrows(IllegalStateException.class, () -> admission.verify(before, BigInteger.valueOf(23), List.of()));
                fixture.writer.requireSession(same);
                return null;
            });
            assertEquals(1, calls.get()); assertEquals(originalSequence, fixture.sequence()); assertEquals(originalWrites, fixture.nativeActionWrites());
            assertDoesNotThrow(() -> fixture.archive.loadMaterial(originalBasis), "read-only archive access must not retain an expired writer Session");
        }
    }
}
