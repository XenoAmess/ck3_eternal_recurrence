package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;

import java.math.BigInteger;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.effects.NativeWarExitEffects;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyWarExitTruceReads;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.service.root.RootReconciliationAuthority;
import org.xar.ck3.control.wave2.military.exitresult.OrdinaryWarExitObservation;

/** Actual native family -> strict Root descriptor DATA boundary. Synthetic frames never grant a Root lease or Game qualification. */
final class WarExitTruceFamilyAdmissionTest {
    private static final Instant NOW = Instant.parse("2026-10-24T01:00:00Z"), DEADLINE = NOW.plusSeconds(60);
    private static final ExactRef SOURCE = ref("data-source");
    private static final G2Source BUILD = new G2Source("war-truce-data-only", NOW.toString(), "1.20.0.4", SOURCE);
    private record Issued(ArmyWarExitTruceReads.Selection selection, ArmyWarExitTruceReads.Issued issued) { }
    private static Issued actual(String literal) {
        Complete before = frame(true), after = frame(false); var operation = new OperationKey(literal);
        var expected = new ExpectedPostcondition(1, before.identity(), BUILD, OrdinaryWarExitObservation.SCHEMA,
                List.of(new ExpectedInteger(new FieldKey("war_id"), BigInteger.valueOf(7)), new ExpectedBoolean(new FieldKey("war_absence_observed"), true)));
        var original = new ActionCommand("original-war-exit", before.identity(), BUILD, "session", operation, new OpportunityJson.Obj(Map.of()),
                expected, new JointBudgetSelector.Claims(Set.of(), Set.of(), Set.of(), Set.of()), DEADLINE);
        var guard = new GuardEvidence(before.identity(), BUILD, "session", BigInteger.ONE, operation, before.originalEvidence(), ref("hello"),
                "data-only-no-authority", NOW, DEADLINE);
        var attempt = new ActionState.Attempt("original-request", NOW, guard, new NativeRequest(operation.value(), Optional.empty(), raw("{}")));
        var pending = new ReconciliationIdentity.Pending(original.actionId(), ActionCodec.bodySha256(original), attempt.requestId(), before.identity(), ref("receipt"), ref("driver"));
        var evidence = new ReconciliationIdentity.Evidence(after.originalEvidence(), ref("hello"), ref("heartbeat"), ref("manifest"), ref("driver"), ref("source-proof"));
        var identity = new ReconciliationIdentity(after.identity(), BUILD, "session", BigInteger.ONE, pending, evidence, NOW.plusSeconds(1));
        var selected = new ArmyWarExitTruceReads.Selection(identity, original, attempt, before, after, DEADLINE);
        PlanningReadPort noIo = new PlanningReadPort() {
            @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract, PlanningReadRequest request) { throw new AssertionError("descriptor construction cannot query Native"); }
        };
        var family = new ArmyWarExitTruceReads(new ArmyWarExitTruceReads.Sources(SOURCE, SOURCE), noIo);
        var catalog = new RootReadContractCatalog(List.of(), family.families());
        return new Issued(selected, family.issue(catalog, selected));
    }
    private static RootReconciliationAuthority.AllowedRead allowed(ReadContract<?> contract, OpportunityJson.Obj args) {
        return new RootReconciliationAuthority.AllowedRead(contract, args, RootReconciliationAuthority.QueryKind.WAR_EXIT_TRUCE);
    }
    private static ReadContract<Object> copy(ReadContract<?> original, String id, OperationKey operation, Optional<String> capability,
            String permission, ReadContract.PermissionMode mode, ReadContract.WireProfile wire, ReadContract.GuardMode guard, boolean replay) {
        java.util.function.BiFunction<PlanningReadRequest, String, NativeRequest> preparer = original::prepare;
        if (!replay) return new ReadContract<>(id, operation, capability, permission, mode, wire, guard, original.sourceRef(), preparer,
                receipt -> { throw new AssertionError("descriptor-only copy cannot decode"); });
        return new ReadContract<>(id, operation, capability, permission, mode, wire, guard, original.sourceRef(), preparer,
                receipt -> { throw new AssertionError("descriptor-only copy cannot decode"); },
                receipt -> { throw new AssertionError("descriptor-only copy cannot replay"); });
    }
    @Test void threeActualWarExitFactoriesIssueOnlyTheirIndependentReconDescriptor() {
        for (String operation : List.of("enforce-demands-7", "offer-white-peace-7", "surrender-war-7")) {
            var fixture = actual(operation); var issued = fixture.issued();
            assertSame(issued.contract(), allowed(issued.contract(), issued.request().arguments()).contract());
            assertTrue(issued.contract().hasPureReplay());
            NativeWarExitEffects.requireOriginalRequest(issued.request(), fixture.selection().original(), fixture.selection().attempt(),
                    fixture.selection().originalBefore(), fixture.selection().actualAfter());
        }
    }
    @Test void wrongProfileOperationCapabilityPermissionGuardWireAndMissingReplayCannotBecomeWarTruceDescriptors() {
        var f = actual("surrender-war-7"); var c = f.issued().contract(); var a = f.issued().request().arguments();
        assertThrows(IllegalArgumentException.class, () -> allowed(copy(c, "ordinary-truce", c.operation(), c.requiredCapability(), c.permissionKey(), c.permissionMode(), c.wireProfile(), c.guardMode(), true), a));
        assertThrows(IllegalArgumentException.class, () -> allowed(copy(c, c.contractId(), new OperationKey("query-raiktor-actual-truce-expiry-v1-0"), c.requiredCapability(), c.permissionKey(), c.permissionMode(), c.wireProfile(), c.guardMode(), true), a));
        assertThrows(IllegalArgumentException.class, () -> allowed(copy(c, c.contractId(), c.operation(), Optional.empty(), c.permissionKey(), c.permissionMode(), c.wireProfile(), c.guardMode(), true), a));
        assertThrows(IllegalArgumentException.class, () -> allowed(copy(c, c.contractId(), c.operation(), c.requiredCapability(), "another-permission", c.permissionMode(), c.wireProfile(), c.guardMode(), true), a));
        assertThrows(IllegalArgumentException.class, () -> allowed(copy(c, c.contractId(), c.operation(), c.requiredCapability(), c.permissionKey(), ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE, c.wireProfile(), c.guardMode(), true), a));
        assertThrows(IllegalArgumentException.class, () -> allowed(copy(c, c.contractId(), c.operation(), c.requiredCapability(), c.permissionKey(), c.permissionMode(), ReadContract.WireProfile.G2_PRIVATE_QUERY, c.guardMode(), true), a));
        assertThrows(IllegalArgumentException.class, () -> allowed(copy(c, c.contractId(), c.operation(), c.requiredCapability(), c.permissionKey(), c.permissionMode(), c.wireProfile(), ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP, true), a));
        assertThrows(IllegalArgumentException.class, () -> allowed(copy(c, c.contractId(), c.operation(), c.requiredCapability(), c.permissionKey(), c.permissionMode(), c.wireProfile(), c.guardMode(), false), a));
    }
    @Test void sharedOriginalBinderRejectsChangedOriginalAttemptBeforeFrameAndTargetType() {
        var f = actual("surrender-war-7"); var s = f.selection(); var request = f.issued().request();
        var wrong = new ActionState.Attempt("different-original", s.attempt().submittedAt(), s.attempt().guard(), s.attempt().preparedRequest());
        assertThrows(IllegalArgumentException.class, () -> NativeWarExitEffects.requireOriginalRequest(request, s.original(), wrong, s.originalBefore(), s.actualAfter()));
        assertThrows(IllegalArgumentException.class, () -> NativeWarExitEffects.requireOriginalRequest(request, s.original(), s.attempt(), s.actualAfter(), s.actualAfter()));
        var changed = PlanningReadRequest.newReconciliation(s.identity(), request.operation(), request.arguments().with("toward_character_id", new OpportunityJson.Bool(true)), DEADLINE);
        assertThrows(IllegalArgumentException.class, () -> NativeWarExitEffects.requireOriginalRequest(changed, s.original(), s.attempt(), s.originalBefore(), s.actualAfter()));
    }
    private static Complete frame(boolean before) {
        int revision = before ? 21 : 22, nativeRevision = before ? 31 : 32;
        var key = new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(101), BigInteger.valueOf(nativeRevision), BigInteger.valueOf(77)),
                "native:" + nativeRevision, BigInteger.valueOf(revision), "war-truce-data");
        var identity = new ObservationIdentity(BUILD.machineId(), new GameGeneration(42, new PythonOnlyUInt64(BigInteger.ONE)), key, 1);
        var n = StrictJson.object().put("paused", true).put("map_ready", true).put("snapshot_id", "native:" + nativeRevision)
                .put("revision", revision).put("native_revision", nativeRevision).put("date_raw", 77).put("episode_run_id", "war-truce-data");
        n.putObject("played_character").put("character_id", 101).put("alive", true);
        n.putObject("diagnostics").put("bridge_pid", 42).put("connection_generation", 1).putObject("hello")
                .put("expected_ck3_version", "1.20.0.4").put("expected_ck3_sha256", OrdinaryWarExitObservation.EXE_SHA256);
        var wars = n.putArray("active_wars"); if (before) wars.addObject().put("war_id", 7).put("player_side", "attacker")
                .put("primary_opponent_character_id", 202).putArray("targeted_title_ids").add(17);
        for (String resource : List.of("gold", "prestige", "piety")) n.putObject("played_character_" + resource).put("raw", before ? 1000000 : 900000).put("scale", 100000);
        return new Complete(identity, BUILD, "session", BigInteger.ONE, DriverJson.object(StrictJson.canonical(n), DriverJson.MAX_NATIVE_BYTES),
                ref(before ? "before-native" : "after-native"), NOW.plusSeconds(before ? 0 : 1), (before ? "b" : "c").repeat(64));
    }
    private static RawJson raw(String text) { return new RawJson(text.getBytes(java.nio.charset.StandardCharsets.UTF_8)); }
    private static ExactRef ref(String value) { return new ExactRef("data-only/" + value, 1, ActionCodec.sha256(value.getBytes(java.nio.charset.StandardCharsets.UTF_8))); }
}
