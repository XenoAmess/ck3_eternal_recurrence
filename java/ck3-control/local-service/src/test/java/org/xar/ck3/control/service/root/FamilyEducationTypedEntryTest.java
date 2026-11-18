package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;

import java.math.BigInteger;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Exercises the same configured selector and held callback as the reader; no physical Root/Installed is fabricated. */
final class FamilyEducationTypedEntryTest {
    private static final ExactRef REF = new ExactRef("D:/fixture/education-typed-source", 1, "a".repeat(64));
    private static final Instant NOW = Instant.parse("2026-11-18T00:00:00Z");
    private static final Instant DEADLINE = NOW.plusSeconds(10);
    private static final ExactCk3Build FLORIN = ExactCk3Build.CK3_1210;
    private record Scene(PlanningRequest request,Complete held) { }

    @Test void configuredFlorinConstructorSelectorDoesNotRequireOrManufactureALegacyBuild() throws Exception {
        var build = configured();
        assertFalse(build.qualified());
        assertTrue(KnownInteractionsRuntimeInstaller.configuredProjection(build).isEmpty());
        var source = RootFamilyEducationRead.configuredContext(build);
        assertThrows(IllegalStateException.class, source::requireProjection);
        var scene = scene(FLORIN.executableSha256().toUpperCase(java.util.Locale.ROOT));
        var calls = new AtomicInteger();
        Obj flat = new Obj(Map.of("recipient_id", new IntegerValue(BigInteger.valueOf(74))));
        var result = RootFamilyEducationRead.projectHeld(source, scene.request(), scene.held(), flat, (context,intent) -> {
            calls.incrementAndGet();throw new AssertionError("unmigrated getter must not enter the legacy ordinary query");
        });
        assertSame(flat, result.canonicalArguments());
        var unavailable = missing(result.result());
        assertEquals("interaction_native_contract_unmigrated", unavailable.reason());
        assertTrue(unavailable.original().isEmpty());
        assertTrue(unavailable.decodeFailure().isEmpty());
        assertTrue(unavailable.observedFailure().isEmpty());
        assertEquals(0, calls.get());
        assertEquals(FLORIN.executableSha256().toUpperCase(java.util.Locale.ROOT), scene.held().source().exactBuild());
    }

    @Test void bothExistingExactSourceSpellingsUseTheSameUnavailableEntry() throws Exception {
        var gate = RootFamilyEducationRead.configuredContext(configured());
        for (String identity : List.of(FLORIN.executableSha256(), FLORIN.version()+"@sha256:"+FLORIN.executableSha256())) {
            var scene = scene(identity);
            var result = RootFamilyEducationRead.projectHeld(gate, scene.request(), scene.held(), new Obj(Map.of()),
                    (context,intent) -> { throw new AssertionError("no known getter for this configured source"); });
            assertEquals("interaction_native_contract_unmigrated", missing(result.result()).reason());
        }
    }

    @Test void wrongExactSourceCannotBorrowTheConfiguredNegativeContract() {
        var scene = scene("0".repeat(64));
        assertThrows(IllegalArgumentException.class, () -> RootFamilyEducationRead.projectHeld(
                RootFamilyEducationRead.configuredContext(configured()), scene.request(), scene.held(), new Obj(Map.of()),
                (context,intent) -> { throw new AssertionError("foreign source must not enter Known"); }));
    }

    @Test void staleDeadlineAndDifferentHeldSessionFailBeforeEitherAvailabilityBranch() {
        var scene = scene(FLORIN.executableSha256());
        var gate = RootFamilyEducationRead.configuredContext(configured());
        var foreign = new Complete(scene.held().identity(), scene.held().source(), "another-session",
                scene.held().connectionGeneration(), scene.held().semantic(), REF, NOW, "b".repeat(64));
        assertThrows(IllegalArgumentException.class, () -> RootFamilyEducationRead.projectHeld(gate,
                scene.request(), foreign, new Obj(Map.of()), (context,intent) -> { throw new AssertionError(); }));
        var expired = new PlanningRequest(scene.request().before(), scene.request().source(), scene.request().sessionId(),
                NOW, scene.request().observations());
        assertThrows(IllegalArgumentException.class, () -> RootFamilyEducationRead.projectHeld(gate,
                expired, scene.held(), new Obj(Map.of()), (context,intent) -> { throw new AssertionError(); }));
    }

    @Test void legacyConfiguredSelectorKeepsItsRealProjectionAndRejectsUnknownTuples() {
        var old = ExactCk3Build.CK3_12004;
        var build = KnownInteractionsRuntimeInstaller.ConfiguredBuild.select(old.version(), old.executableSha256());
        assertTrue(build.qualified());
        assertTrue(KnownInteractionsRuntimeInstaller.configuredProjection(build).isPresent());
        assertNotNull(RootFamilyEducationRead.configuredContext(build).requireProjection());
        assertThrows(IllegalArgumentException.class, () -> KnownInteractionsRuntimeInstaller.ConfiguredBuild.select(
                FLORIN.version(), old.executableSha256()));
    }

    private static KnownInteractionsRuntimeInstaller.ConfiguredBuild configured() {
        return KnownInteractionsRuntimeInstaller.ConfiguredBuild.select(FLORIN.version(), FLORIN.executableSha256());
    }
    private static PlanningReadResult.Unavailable<Obj> missing(PlanningReadResult<Obj> result) {
        if (result instanceof PlanningReadResult.Unavailable<Obj> unavailable) return unavailable;
        throw new AssertionError("unmigrated context was promoted to Known");
    }
    private static Scene scene(String exactSource) {
        var source = new G2Source("education-software", NOW.toString(), exactSource, REF);
        var frame = new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(73),
                BigInteger.valueOf(17), BigInteger.valueOf(123456)), "education-snapshot", BigInteger.valueOf(19), "education-episode");
        var before = new ObservationIdentity(source.machineId(), new GameGeneration(123, new PythonOnlyUInt64(BigInteger.ONE)), frame, 1);
        Obj semantic = new Obj(Map.of("snapshot_id", new Text(frame.snapshotId()), "revision", new IntegerValue(frame.revision()),
                "native_revision", new IntegerValue(frame.identity().nativeRevision()), "date_raw", new IntegerValue(frame.identity().dateRaw()),
                "episode_run_id", new Text(frame.episodeRunId()), "played_character", new Obj(Map.of("character_id", new IntegerValue(frame.identity().player()))),
                "paused",new Bool(true),"map_ready",new Bool(true),"active_wars",new Arr(List.of()),"player_armies",new Arr(List.of())));
        var held = new Complete(before, source, "education-session", BigInteger.ONE, semantic, REF, NOW, "b".repeat(64));
        var request = new PlanningRequest(before, source, held.sessionId(), DEADLINE,
                new PlanningObservation(semantic, List.of(), Set.of(), Set.of(), Optional.empty(), List.of(), Optional.empty(), Optional.empty(), false));
        return new Scene(request,held);
    }
}
