package org.xar.ck3.control.application.action;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Archived receipts use an explicitly installed pure decoder, never the live cache producer. */
final class ReadContractReplayTest {
    private static final Instant NOW = Instant.parse("2026-10-24T00:00:00Z");
    private static final OperationKey OPERATION = new OperationKey("query-replay-fixture-v1");
    private static ExactRef ref(String name, char hash) {
        return new ExactRef("D:/replay-fixture/" + name, 10, String.valueOf(hash).repeat(64));
    }
    private static final G2Source SOURCE = new G2Source("replay-fixture", NOW.toString(), "1.20.0.4", ref("source.java", 'a'));
    private static PlanningReadReceipt receipt(String contractId) {
        var identity = new FrontendIdentity(SOURCE.machineId(), new GameGeneration(123,
                new PythonOnlyUInt64(new BigInteger("133700000000000001"))), "session", BigInteger.ONE, 123,
                new FrontendFrame.Menu(BigInteger.ONE), ref("route.packet", 'b'), ref("hello.packet", 'c'));
        var origin = new CommandOrigin.Frontend(identity);
        var request = new PlanningReadRequest(origin, SOURCE, "session", OPERATION, new OpportunityJson.Obj(Map.of()), NOW.plusSeconds(30));
        var evidence = new GuardEvidence(origin, SOURCE, "session", BigInteger.ONE, OPERATION, identity.nativeEvidence(),
                identity.capabilityEvidence(), "source-bound-fixture", NOW, NOW.plusSeconds(30), List.of(ref("source-proof.json", 'd')));
        var guard = new PlanningReadGuard(evidence, "e".repeat(64));
        var raw = new RawJson("{}".getBytes(StandardCharsets.UTF_8));
        return new PlanningReadReceipt(request, contractId, "independent-query", guard, guard,
                new NativeActionPort.AckReceived("independent-query", true, Optional.of(raw), raw, new byte[] {1}));
    }
    private static ReadContract<String> contract(AtomicInteger live, AtomicInteger replay) {
        return new ReadContract<>("exact-replay/v1", OPERATION, Optional.of("game.command." + OPERATION.value()), "actual-query",
                ReadContract.PermissionMode.ADVERTISED_CAPABILITY, ReadContract.WireProfile.EXECUTE_STEP,
                ReadContract.GuardMode.FRONTEND_SESSION, SOURCE.sourceRef(),
                (request, requestId) -> new NativeRequest(OPERATION.value(), "game.command." + OPERATION.value(),
                        new RawJson("{}".getBytes(StandardCharsets.UTF_8))),
                original -> { live.incrementAndGet(); return "live"; },
                original -> { replay.incrementAndGet(); return "archived"; });
    }
    @Test void pureReplayNeverMutatesTheInstalledLiveDecoderAndRetainsTheExactReceipt() {
        var live = new AtomicInteger(); var replay = new AtomicInteger(); var contract = contract(live, replay);
        var original = receipt("exact-replay/v1");
        assertTrue(contract.hasPureReplay());
        assertEquals("archived", contract.replay(original)); assertEquals("archived", contract.replay(original));
        assertEquals(0, live.get()); assertEquals(2, replay.get());
        assertEquals("live", contract.decode(original)); assertEquals(1, live.get()); assertEquals(2, replay.get());
        assertEquals("independent-query", original.original().requestId());
    }
    @Test void historicalConstructorDoesNotAliasItsPotentiallyMutatingDecoderIntoReplay() {
        var calls = new AtomicInteger();
        var contract = new ReadContract<String>("exact-replay/v1", OPERATION, Optional.of("game.command." + OPERATION.value()), "actual-query",
                ReadContract.PermissionMode.ADVERTISED_CAPABILITY, ReadContract.WireProfile.EXECUTE_STEP,
                ReadContract.GuardMode.FRONTEND_SESSION, SOURCE.sourceRef(),
                (request, requestId) -> new NativeRequest(OPERATION.value(), "game.command." + OPERATION.value(),
                        new RawJson("{}".getBytes(StandardCharsets.UTF_8))),
                original -> { calls.incrementAndGet(); return "mutating"; });
        assertFalse(contract.hasPureReplay());
        assertThrows(IllegalStateException.class, () -> contract.replay(receipt("exact-replay/v1")));
        assertEquals(0, calls.get());
    }
    @Test void wrongContractRejectsBeforeEitherProducerAndNullReplayIsNeverAccepted() {
        var live = new AtomicInteger(); var replay = new AtomicInteger(); var contract = contract(live, replay);
        assertThrows(IllegalArgumentException.class, () -> contract.replay(receipt("other-contract/v1")));
        assertThrows(IllegalArgumentException.class, () -> contract.decode(receipt("other-contract/v1")));
        assertEquals(0, live.get()); assertEquals(0, replay.get());
        assertThrows(NullPointerException.class, () -> new ReadContract<String>("exact-replay/v1", OPERATION,
                Optional.of("game.command." + OPERATION.value()), "actual-query",
                ReadContract.PermissionMode.ADVERTISED_CAPABILITY, ReadContract.WireProfile.EXECUTE_STEP,
                ReadContract.GuardMode.FRONTEND_SESSION, SOURCE.sourceRef(),
                (request, requestId) -> new NativeRequest(OPERATION.value(), "game.command." + OPERATION.value(),
                        new RawJson("{}".getBytes(StandardCharsets.UTF_8))), original -> "live",
                (java.util.function.Function<PlanningReadReceipt, String>) null));
    }
    @Test void originalContractEscrowReturnsOnlyTheActualTypedOldInstanceAndBindsOnce() {
        var old = contract(new AtomicInteger(), new AtomicInteger());
        var current = contract(new AtomicInteger(), new AtomicInteger());
        assertTrue(current.originalContract(old.contractId()).isEmpty());
        current.bindOriginalContracts(id -> id.equals(old.contractId()) ? Optional.of(old) : Optional.empty());
        assertSame(old, current.originalContract(old.contractId()).orElseThrow());
        assertNotSame(current, current.originalContract(old.contractId()).orElseThrow());
        assertTrue(current.originalContract("not-an-original").isEmpty());
        assertThrows(IllegalStateException.class, () -> current.bindOriginalContracts(id -> Optional.empty()));
        var wrong = contract(new AtomicInteger(), new AtomicInteger());
        wrong.bindOriginalContracts(id -> Optional.of(old));
        assertThrows(IllegalArgumentException.class, () -> wrong.originalContract("changed-id"));
    }
    @Test void noOwnerPredicateMeansNoGenericDroppingOfDeadlineOrDriverWrapper() {
        var contract = contract(new AtomicInteger(), new AtomicInteger()); var original = receipt("exact-replay/v1");
        var semantic = new OpportunityJson.Obj(Map.of());
        assertDoesNotThrow(() -> contract.requireCanonicalReuse(original, "archived", original.request(), semantic));
        var later = new PlanningReadRequest(original.request().origin(), original.request().source(), original.request().sessionId(),
                original.request().operation(), original.request().arguments(), original.request().deadline().plusSeconds(1));
        assertThrows(IllegalArgumentException.class, () -> contract.requireCanonicalReuse(original, "archived", later, semantic));
    }
    @Test void onlyAnExplicitSourcePredicateMayQualifyAChangedBudgetAndItDoesNotInvokeLiveDecode() {
        var invoked = new AtomicInteger(); var live = new AtomicInteger();
        var contract = new ReadContract<String>("exact-replay/v1", OPERATION, Optional.of("game.command." + OPERATION.value()), "actual-query",
                ReadContract.PermissionMode.ADVERTISED_CAPABILITY, ReadContract.WireProfile.EXECUTE_STEP,
                ReadContract.GuardMode.FRONTEND_SESSION, SOURCE.sourceRef(),
                (request, requestId) -> new NativeRequest(OPERATION.value(), "game.command." + OPERATION.value(), new RawJson("{}".getBytes(StandardCharsets.UTF_8))),
                original -> { live.incrementAndGet(); return "live"; }, original -> "archived",
                (original, value, current, semantic) -> {
                    invoked.incrementAndGet();
                    org.xar.ck3.control.contracts.StrictJson.require(value.equals("archived") && original.request().origin().equals(current.origin())
                            && original.request().source().equals(current.source()) && original.request().sessionId().equals(current.sessionId())
                            && original.request().arguments().equals(current.arguments())
                            && new OpportunityJson.IntegerValue(BigInteger.ONE).equals(semantic.get("fixture_native_epoch")),
                            "explicit source predicate did not prove semantic equivalence");
                });
        var original = receipt("exact-replay/v1");
        var current = new PlanningReadRequest(original.request().origin(), SOURCE, original.request().sessionId(), OPERATION,
                original.request().arguments(), original.request().deadline().plusSeconds(1));
        var semantic = new OpportunityJson.Obj(Map.of("fixture_native_epoch", new OpportunityJson.IntegerValue(BigInteger.ONE)));
        assertDoesNotThrow(() -> contract.requireCanonicalReuse(original, contract.replay(original), current, semantic));
        var changed = new PlanningReadRequest(current.origin(), SOURCE, current.sessionId(), OPERATION,
                new OpportunityJson.Obj(Map.of("changed_argument", new OpportunityJson.Bool(true))), current.deadline());
        assertThrows(IllegalArgumentException.class, () -> contract.requireCanonicalReuse(original, "archived", changed, semantic));
        assertEquals(2, invoked.get()); assertEquals(0, live.get());
    }

}
