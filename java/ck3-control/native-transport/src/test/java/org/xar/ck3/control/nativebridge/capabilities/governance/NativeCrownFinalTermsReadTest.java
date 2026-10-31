package org.xar.ck3.control.nativebridge.capabilities.governance;

import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.governance.council.CouncilCodec;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave3.governance.crowncooldown.*;
import org.xar.ck3.control.wave3.governance.crownfinalterms.*;
import static org.junit.jupiter.api.Assertions.*;

/** Retained native law rows plus explicitly synthetic .4 clock data are value tests, never native/runtime qualification. */
final class NativeCrownFinalTermsReadTest {
    private static final Instant NOW = Instant.parse("2026-10-23T19:00:00Z");
    private static final ExactRef REF = new ExactRef("synthetic-clock-test-source-no-runtime-qualification", 1, "a".repeat(64));
    private static NativeCrownFinalTermsRead definition() { return new NativeCrownFinalTermsRead(REF, "1.20.0.4", CrownFinalTerms.Build.CK3_12004.sha256()); }
    private static ObjectNode payload() throws Exception {
        String repository = System.getProperty("xar.repository.root"); assertNotNull(repository);
        ObjectNode payload = CouncilCodec.object(StrictJson.parse(Files.readAllBytes(Path.of(repository,
                "ck3_autonomous_player/native_bridge/research/fixtures/ck3_12002_realm_law_final_terms_wire.json"))));
        // The retained .2 native fixture predates these .4 profile/clock fields; additions are deliberately synthetic.
        for (var row : payload.at("/groups/1/candidates")) ((ObjectNode) row).put("succession_profile_status", "absent").putNull("succession_profile");
        var raw = new CrownCooldown.RawObservation(true, true, true, 28, 7, 21, BigInteger.valueOf(53169072 + 11 * 24), CrownCooldown.EXPIRY_TYPE, CrownCooldown.PROJECTED_UNIT);
        var tick = new CrownCooldown.TurnTick(true, BigInteger.TWO, true, true, true, null, CrownCooldown.TICK_SOURCE);
        payload.set("crown_authority_cooldown", StrictJson.parse(CrownCooldownCodec.encode(raw)));
        payload.set("crown_authority_cooldown_turn_tick", StrictJson.parse(CrownCooldownCodec.encode(tick))); return payload;
    }
    private static PlanningReadReceipt receipt(NativeCrownFinalTermsRead definition, ObjectNode payload) throws Exception {
        return receipt(definition,payload,"1.20.0.4");
    }
    private static PlanningReadReceipt receipt(NativeCrownFinalTermsRead definition,ObjectNode payload,String version)throws Exception {
        var source = new G2Source("xenoamess-full-tower-eb9d2c1186", NOW.toString(), version, REF);
        var before = new ObservationIdentity(source.machineId(), new GameGeneration(12, new PythonOnlyUInt64(new BigInteger("133700000000000001"))),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(29829), BigInteger.valueOf(74), BigInteger.valueOf(53169072)),
                        "public:174", BigInteger.valueOf(174), "native-29829-synthetic-clock"), 1);
        var query = new PlanningReadRequest(before, source, "synthetic-clock-session", definition.contract().operation(), new OpportunityJson.Obj(java.util.Map.of()), NOW.plusSeconds(30));
        var binding = new GuardEvidence(before, source, query.sessionId(), BigInteger.ONE, query.operation(), REF, REF, "synthetic-clock-authority", NOW, NOW.plusSeconds(30));
        var guard = new PlanningReadGuard(binding, true, true, true, "b".repeat(64));
        ObjectNode result = StrictJson.object().put("step", CrownFinalTerms.STEP).put("accepted", true).put("status", "available").put("private_build", true)
                .put("read_only", true).put("advertised", false).put("backend_id", "native-headless").put("snapshot_revision", 74); result.set("realm_law_final_terms", payload);
        ObjectNode full = StrictJson.object().put("type", "command_result").put("protocol_version", 1).put("request_id", "synthetic-clock-read-1").put("ok", true); full.set("result", result);
        byte[] frame = StrictJson.canonical(full);
        var ack = new NativeActionPort.AckReceived("synthetic-clock-read-1", true, Optional.of(new RawJson(StrictJson.canonical(result))), new RawJson(frame), NativeWire.packet(frame));
        return new PlanningReadReceipt(query, definition.contract().contractId(), ack.requestId(), guard, guard, ack);
    }
    @Test void completeLawReadTraversesActualRegisteredDecoderAndKeepsPublicNativeRevisionsSeparate() throws Exception {
        var definition = definition(); var receipt = receipt(definition, payload());
        var clock = definition.contract().decode(receipt).clock().orElseThrow(); assertTrue(CrownCooldown.interpret(clock.observation(), clock.dateRaw(), clock.turnTick()).calendarDeadlineReady());
        var consumed = definition.consume(receipt); assertEquals(2, consumed.readback().payload().groups().size());
        var input = StrictJson.parse(consumed.completeConsume().bytes()); assertEquals(174, input.get("expected_revision").intValue());
        assertEquals(74, consumed.readback().queriedNativeRevision().intValue());
        var prepared = definition.contract().prepare(receipt.request(), "synthetic-clock-wire-2"); assertEquals(0, StrictJson.parse(prepared.additionalFields().bytes()).size());
        var wire = NativeWire.decodeExecuteRequest(NativeWire.execute("synthetic-clock-wire-2", prepared.step(), BigInteger.valueOf(74), prepared.additionalFields().bytes()));
        assertEquals(Optional.of(BigInteger.valueOf(74)), wire.expectedRevision()); assertTrue(wire.expectedSnapshotRevision().isEmpty());
    }
    @Test void clockCannotBeDetachedFromSecondLawGroupSourceFrameOrStrictMembershipTokens() throws Exception {
        var definition = definition(); var missing = payload(); ((ArrayNode) missing.get("groups")).remove(1);
        assertThrows(IllegalArgumentException.class, () -> definition.consume(receipt(definition, missing)));
        var bool = payload(); ((ObjectNode) bool.get("crown_authority_cooldown_turn_tick")).put("manager_contains_context", 1);
        assertThrows(IllegalArgumentException.class, () -> definition.consume(receipt(definition, bool)));
        var drift = payload().put("snapshot_revision", 174);
        assertThrows(IllegalArgumentException.class, () -> definition.consume(receipt(definition, drift)));
    }
    @Test void retainedCompleteStockLawTermsRemainAvailableWithoutTheOptionalLaterCalendarObserver()throws Exception {
        String repository=System.getProperty("xar.repository.root");assertNotNull(repository);
        var raw=CouncilCodec.object(StrictJson.parse(Files.readAllBytes(Path.of(repository,"ck3_autonomous_player/native_bridge/research/fixtures/ck3_12002_realm_law_final_terms_wire.json"))));
        var definition=new NativeCrownFinalTermsRead(REF,"1.20.0.2",CrownFinalTerms.Build.CK3_12002.sha256());var original=receipt(definition,raw,"1.20.0.2");
        var observed=definition.contract().decode(original);assertEquals(2,observed.readback().payload().groups().size());assertTrue(observed.clock().isEmpty());
        assertThrows(IllegalArgumentException.class,()->definition.consume(original));
        assertArrayEquals(observed.completeConsume().bytes(),definition.consumeTerms(original).completeConsume().bytes());
    }
    @Test void crownFinalTermsContractHasPureReplayAndMatchesDecode() throws Exception {
        var definition = definition();
        var receipt = receipt(definition, payload());
        assertTrue(definition.contract().hasPureReplay(), "Crown final-terms contract must have pure replay");
        var decoded = definition.contract().decode(receipt);
        var replayed = definition.contract().replay(receipt);
        assertEquals(decoded.readback(), replayed.readback());
        assertArrayEquals(decoded.completeConsume().bytes(), replayed.completeConsume().bytes());
        assertEquals(decoded.clock(), replayed.clock());
    }
}
