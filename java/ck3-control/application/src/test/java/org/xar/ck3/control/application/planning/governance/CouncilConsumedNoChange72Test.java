package org.xar.ck3.control.application.planning.governance;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.planning.governance.GovernanceFixtures.*;
import static org.xar.ck3.control.application.planning.governance.GovernanceObservationSupplier.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import java.lang.reflect.Proxy;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.ArrayList;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.OrdinaryPolicy;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;

/** Synthetic public policy DATA only: no canonical writer, archived pin, private Root or Native permission. */
final class CouncilConsumedNoChange72Test {
    private static final ExactRef AFTER = new ExactRef("unit-council72-after.json", 1, "b".repeat(64));

    @Test void consumedNoChangeReusesOnlyItsRoleAndKeepsOtherReadsFresh() {
        var request = request(); var previous = advance(request);
        for (var role : CouncilSelection.Position.values()) {
            var fixture = new DataSupplier(request, role, true, false, false);
            var policy = new GovernancePolicies.Council(fixture.port, REF);
            var draft = assertInstanceOf(OrdinaryPolicy.Replace.class, policy.evaluate(request, previous)).draft();
            assertEquals(previous.command(), draft.command(), "NO_CHANGE must retain the original life command");
            for (var queried : CouncilSelection.Position.values()) assertEquals(1, fixture.count(queried));
            assertEquals(1, fixture.rootReads);
            Obj first = fixture.originals.get(role).getFirst();
            String field = "council_" + role.name().toLowerCase(java.util.Locale.ROOT) + "_query";
            assertEquals(first, draft.detail().get(field));
            assertEquals(first, object(draft.detail().get("council_receipt_consumed"), "consumed DATA").get("current_query"));
            assertTrue(GovernanceCadencePublication.fromDetail(draft.detail()).isPresent());
            var next = assertInstanceOf(OrdinaryPolicy.Replace.class, policy.evaluate(request, previous)).draft();
            assertEquals(previous.command(), next.command());
            for (var queried : CouncilSelection.Position.values()) assertEquals(2, fixture.count(queried), "another evaluate must query again");
            assertEquals(2, fixture.rootReads);
            assertEquals(fixture.originals.get(role).getLast(), next.detail().get(field));
        }

        // The first actionable query must never be reused to construct a command. Its fresh replacement is decisive.
        var fresh = new DataSupplier(request, CouncilSelection.Position.STEWARD, true, true, false);
        var unchanged = assertInstanceOf(OrdinaryPolicy.Replace.class,
                new GovernancePolicies.Council(fresh.port, REF).evaluate(request, previous)).draft();
        assertEquals(previous.command(), unchanged.command());
        assertEquals(2, fresh.count(CouncilSelection.Position.STEWARD));
        assertEquals(1, fresh.count(CouncilSelection.Position.CHANCELLOR));
        assertEquals(1, fresh.count(CouncilSelection.Position.CHAPLAIN));
        assertEquals(fresh.originals.get(CouncilSelection.Position.STEWARD).getLast(), unchanged.detail().get("council_steward_query"));
        assertNotEquals(fresh.originals.get(CouncilSelection.Position.STEWARD).getFirst(), unchanged.detail().get("council_steward_query"));
        assertEquals(fresh.originals.get(CouncilSelection.Position.STEWARD).getFirst(),
                object(unchanged.detail().get("council_receipt_consumed"), "earlier receipt observation").get("current_query"));

        var crossed = new DataSupplier(request, CouncilSelection.Position.CHANCELLOR, true, false, true);
        var wait = assertInstanceOf(OrdinaryPolicy.Wait.class,
                new GovernancePolicies.Council(crossed.port, REF).evaluate(request, previous));
        assertEquals("independent current root and council position do not agree on the applied seat", wait.reason());
        assertEquals(1, crossed.count(CouncilSelection.Position.CHANCELLOR));
        assertEquals(0, crossed.count(CouncilSelection.Position.STEWARD));
        assertEquals(0, crossed.count(CouncilSelection.Position.CHAPLAIN));
        assertEquals(1, crossed.rootReads);

        var noApplied = new DataSupplier(request, CouncilSelection.Position.STEWARD, false, false, false);
        var original = assertInstanceOf(OrdinaryPolicy.Replace.class,
                new GovernancePolicies.Council(noApplied.port, REF).evaluate(request, previous)).draft();
        assertEquals(previous.command(), original.command());
        for (var role : CouncilSelection.Position.values()) assertEquals(1, noApplied.count(role));
        assertNull(original.detail().get("council_receipt_consumed"));
        System.out.println("COUNCIL_NOCHANGE_DATA_PASS roles=3 oneReadEach=true nextEvaluateFresh=true actionableSecondFresh=true "
                + "rootMismatchWait=true noAppliedOriginalPath=true commandPreserved=true privateRoot=false nativeCustody=false");
    }

    /** This source constructs only public unit DTOs; consume is the real validator, never mocked or bypassed. */
    private static ActionReceipt applied(CouncilSelection.Position role, PlanningRequest current) {
        var before = request(7, false, List.of());
        var expected = new ExpectedPostcondition(1, before.before(), before.source(), "unit-council72-effect/v1",
                List.of(new ExpectedInteger(new FieldKey("council.incumbent_character_id"), BigInteger.valueOf(20))));
        var args = new Obj(Map.of()).with("position_key", new Text(role.key())).with("candidate_character_id", n(20));
        var command = new ActionCommand("unit-council72-" + role.name(), before.before(), before.source(), before.sessionId(),
                GovernancePolicies.COUNCIL, args, expected, new JointBudgetSelector.Claims(Set.of(), Set.of(), Set.of(), Set.of()), before.deadline());
        String requestId = "unit-council72-original-" + role.name();
        var guard = new GuardEvidence(before.before(), before.source(), before.sessionId(), BigInteger.ONE,
                command.operation(), REF, REF, "unit-data-only", NOW, NOW.plusSeconds(20));
        var attempt = new ActionState.Attempt(requestId, NOW, guard,
                new NativeRequest(command.operation().value(), "unit-data-only", new RawJson(encode(new Obj(Map.of())))));
        Obj ackNode = new Obj(Map.of()).with("type", new Text("command_result")).with("protocol_version", n(1))
                .with("request_id", new Text(requestId)).with("ok", new Bool(true)).with("result", new Obj(Map.of()));
        byte[] ack = encode(ackNode);
        byte[] frame = ByteBuffer.allocate(ack.length + 4).order(ByteOrder.LITTLE_ENDIAN).putInt(ack.length).put(ack).array();
        var dispatch = new NativeActionPort.AckReceived(requestId, true, Optional.of(new RawJson(encode(new Obj(Map.of())))), new RawJson(ack), frame);
        var effect = new ActionState.EffectObservation(identity(8), before.source(), before.sessionId(), expected.observerSchema(),
                expected.values(), "unit-council72-independent-read", NOW.plusSeconds(1), AFTER);
        var receipt = new ActionReceipt(1, 1, command, ActionCodec.bodySha256(command), new ActionState.Settled(attempt, dispatch, new ActionState.Applied(effect)));
        assertEquals(GovernanceReceipts.Status.CONSUMED, GovernanceReceipts.consume(receipt, current, Optional.empty(), false).status());
        return receipt;
    }

    private static final class DataSupplier {
        private final EnumMap<CouncilSelection.Position, List<Obj>> originals = new EnumMap<>(CouncilSelection.Position.class);
        private final GovernanceObservationSupplier port;
        private int rootReads;
        private DataSupplier(PlanningRequest request, CouncilSelection.Position appliedRole, boolean hasApplied,
                boolean firstActionable, boolean rootMismatch) {
            var delegate = new GovernanceFixtures.Supplier(request);
            var old = durable(request);
            var council = hasApplied ? new DomainState(DomainStatus.KNOWN_CLEAR, Optional.of(applied(appliedRole, request)),
                    Optional.empty(), new Obj(Map.of())) : old.council().orElseThrow();
            var data = new Durable(old.observed(), old.sessionId(), old.cadence(), old.opening(), Optional.of(council), old.crown());
            port = (GovernanceObservationSupplier) Proxy.newProxyInstance(GovernanceObservationSupplier.class.getClassLoader(),
                    new Class<?>[]{GovernanceObservationSupplier.class}, (proxy, method, arguments) -> {
                        assertSame(request, arguments[0]);
                        return switch (method.getName()) {
                            case "durable" -> new Known<>(data, List.of(REF));
                            case "councilRoot" -> { rootReads++; yield delegate.councilRoot(request); }
                            case "council" -> {
                                var role = (CouncilSelection.Position) arguments[1];
                                var observed = originals.computeIfAbsent(role, ignored -> new ArrayList<>());
                                boolean actionable = firstActionable && role == appliedRole && observed.isEmpty();
                                Obj raw = councilRaw(request, role, 10, actionable ? 20 : 9, 8)
                                        .with("unit_read_marker", new Text(role.name() + ":" + observed.size()));
                                if (rootMismatch && role == appliedRole) {
                                    Obj payload = object(raw.get("council_composition_candidates"), "query DATA");
                                    Obj seat = object(payload.get("position"), "seat DATA").with("incumbent_character_id", n(21));
                                    raw = raw.with("council_composition_candidates", payload.with("position", seat));
                                }
                                var query = CouncilSelection.decode(request, role, raw);
                                if (actionable) assertEquals(CouncilSelection.Outcome.REPLACE_REQUIRED, CouncilSelection.choose(query).outcome());
                                observed.add(raw); yield new Known<>(query, List.of(REF));
                            }
                            default -> throw new AssertionError("unrelated DATA supplier call: " + method.getName());
                        };
                    });
        }
        private int count(CouncilSelection.Position role) { return originals.getOrDefault(role, List.of()).size(); }
    }
}
