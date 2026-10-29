package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.BattleResponses.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.BattleAfterStateObservation.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.HexFormat;
import java.util.HashSet;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Real C++ factory/shared readers/serializers over owned memory (actual=0).
 * Request/authority envelopes below are fixture bookkeeping, never live reads. */
final class BattleCurrentObservation12004ProducerTest {
    private static final ObjectMapper JSON = new ObjectMapper();
    private static final BigInteger REVISION = BigInteger.TWO;
    private static final Instant NOW = Instant.parse("2026-10-23T20:00:00Z");

    @Test void currentFactoryOutputReachesStrictTypedAndIndependentAfterstate() throws Exception {
        String configured = System.getProperty("xar.battleCurrent12004.nativeWire");
        String expectedSha = System.getProperty("xar.battleCurrent12004.nativeWireSha256");
        assertNotNull(configured, "required actual4 C++ factory fixture output; no skip/fallback");
        assertNotNull(expectedSha, "required fresh native producer SHA-256");
        assertTrue(expectedSha.matches("[0-9a-f]{64}"), "canonical lowercase SHA-256 required");
        Path path = Path.of(configured);
        assertTrue(path.isAbsolute() && Files.isRegularFile(path));
        assertTrue(Files.size(path) > 0 && Files.size(path) <= RawJson.MAXIMUM_BYTES);
        byte[] bytes = Files.readAllBytes(path);
        assertTrue(bytes.length > 0 && bytes.length <= RawJson.MAXIMUM_BYTES);
        assertEquals(expectedSha, HexFormat.of().formatHex(
                MessageDigest.getInstance("SHA-256").digest(bytes)));
        ExactRef nativeRef = new ExactRef(path.toString(), bytes.length, expectedSha);
        ObjectNode top = closed(JSON.readTree(bytes),
                "schema_version", "actual", "executable_sha256", "cases");
        assertEquals(1, i32(top.get("schema_version")));
        assertEquals(0, i32(top.get("actual")));
        assertEquals("98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518",
                text(top.get("executable_sha256")));
        Set<String> required = Set.of("current_positive", "current_zero_combat_public_zero",
                "current_highbit_public_zero", "current_highbit_positive_public",
                "current_invalid_main_flag", "current_invalid_soft",
                "current_wrong_regiment_owner", "current_negative_participant_hard");
        Set<String> seen = new HashSet<>();
        for (JsonNode raw : array(top.get("cases"), ArmyJson::object)) {
            ObjectNode row = closed(raw, "name", "before_control", "after_transition", "current_expected_available");
            String name = text(row.get("name"));
            assertTrue(required.contains(name) && seen.add(name), "unknown/duplicate source case");
            ObjectNode control = object(row.get("before_control"));
            ObjectNode transition = object(row.get("after_transition"));
            int subject = i32(control.get("subject_public_cunit_id"));
            int combat = i32(control.get("combat_id"));
            long date = i64(control.get("observed_date_raw"));
            ObjectNode before = envelope(control, true, subject, combat);
            ObjectNode after = envelope(transition, false, subject, combat);
            CurrentBattle observed = assertInstanceOf(CurrentBattle.class,
                    observe(before, after, name, subject, date, nativeRef));
            assertEquals(combat, observed.original().combat().value());
            CurrentObservation current = current(observed.current());
            if (bool(row.get("current_expected_available"))) {
                assertEquals(Availability.AVAILABLE, current.status());
                assertEquals(new Present<>(12), current.baseWidth());
                assertEquals(new Present<>(24), current.finalWidth());
                assertEquals(new Present<>(1L << 40), current.baseAdvantageRaw());
                assertEquals(new Present<>((1L << 40) + 17), current.resolvedAdvantageRaw());
                CurrentSide attacker = side(current.attacker());
                assertEquals(7000000, attacker.currentRaw());
                assertEquals(2000000, attacker.softRaw());
                assertEquals(1000000, attacker.hardRaw());
                assertEquals(500000, attacker.participantHardRaw());
            } else {
                assertEquals(Availability.UNAVAILABLE, current.status());
                assertInstanceOf(Present.class, current.unavailableReason());
                assertInstanceOf(NullValue.class, current.attacker());
                assertInstanceOf(NullValue.class, current.defender());
            }
            assertFalse(observed.dispatchAllowed());
            assertFalse(observed.replayAllowed());
            assertFalse(observed.commandCausationVerified());
            assertFalse(observed.warOutcomeVerified());
            assertFalse(observed.completeBattleConsequencesVerified());
            ObjectNode roundtrip = object(JSON.readTree(JSON.writeValueAsBytes(after)));
            CurrentBattle restored = assertInstanceOf(CurrentBattle.class,
                    observe(before, roundtrip, name, subject, date, nativeRef));
            assertEquals(observed.current(), restored.current(),
                    "all typed current values and original frame must survive JSON roundtrip");
            assertEquals(JSON.readTree(BattleAfterStateObservation.toJson(observed).toString()),
                    JSON.readTree(BattleAfterStateObservation.toJson(restored).toString()));
            ObjectNode malformed = transition.deepCopy();
            object(malformed.get("current_observation")).put("scale", true);
            assertThrows(IllegalArgumentException.class, () ->
                    observe(before, envelope(malformed, false, subject, combat),
                            name, subject, date, nativeRef));
        }
        assertEquals(required, seen, "incomplete actual C++ producer/Java consumer case join");
    }
    private static CurrentObservation current(Transition value) {
        if (value.current() instanceof Present<CurrentObservation> present) return present.value();
        throw new AssertionError("actual4 factory must attach the demanded current observation");
    }
    private static CurrentSide side(Field<CurrentSide> value) {
        if (value instanceof Present<CurrentSide> present) return present.value();
        throw new AssertionError("available current source lost actual side ledger");
    }
    private static ObjectNode envelope(ObjectNode leaf, boolean before, int subject, int combat) {
        ObjectNode value = JSON.createObjectNode();
        value.put("accepted", true);
        value.put("step", before ? "query-battle-control-snapshot-v1-" + subject
                : "query-battle-transition-v1-" + combat);
        value.put("snapshot_revision", REVISION);
        value.put("query_sequence", before ? 1 : 2);
        value.set(before ? "battle_control_snapshot" : "battle_transition_snapshot", leaf);
        return value;
    }
    private static Result observe(ObjectNode before, ObjectNode after, String name,
            int subject, long date, ExactRef nativeRef) {
        return BattleAfterStateObservation.transition(
                receipt(before, name + "-before", 7, date, nativeRef), nativeRef,
                receipt(after, name + "-after", 8, date, nativeRef), nativeRef,
                new PublicUnitId(subject));
    }
    private static PlanningReadReceipt receipt(ObjectNode raw, String requestId,
            long publicRevision, long date, ExactRef nativeRef) {
        var frame = new JointBudgetSelector.ProposalFrame(
                new JointBudgetSelector.Frame(BigInteger.valueOf(0x1000001), REVISION,
                        BigInteger.valueOf(date)),
                "factory-fixture-" + publicRevision, BigInteger.valueOf(publicRevision),
                "owned-memory-current-factory");
        var observed = new ObservationIdentity("fixture-owned-memory",
                new GameGeneration(42, new PythonOnlyUInt64(BigInteger.ONE)), frame, 1);
        var source = new G2Source("fixture-owned-memory", NOW.toString(),
                "ck3-1.20.0.4-current-factory-owned-memory-actual0", nativeRef);
        var operation = new OperationKey("query-battle");
        var request = new PlanningReadRequest(observed, source, "fixture-session", operation,
                new OpportunityJson.Obj(Map.of()), NOW.plusSeconds(60));
        var evidence = new GuardEvidence(observed, source, "fixture-session", BigInteger.ONE,
                operation, nativeRef, nativeRef, "fixture-authority", NOW, NOW.plusSeconds(60));
        var guard = new PlanningReadGuard(evidence, true, true, true, "2".repeat(64));
        var token = new RawJson(raw.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8));
        var ack = new NativeActionPort.AckReceived(requestId, true, Optional.of(token),
                new RawJson("{}".getBytes(java.nio.charset.StandardCharsets.UTF_8)),
                "{}".getBytes(java.nio.charset.StandardCharsets.UTF_8));
        return new PlanningReadReceipt(request, "owned-memory-factory", requestId, guard, guard, ack);
    }
}
