package org.xar.ck3.control.application.action;

import static org.junit.jupiter.api.Assertions.*;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.Function;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.effects.EventMaterialQuerySource;
import org.xar.ck3.control.application.effects.NativeEventEffects;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Same issued contract and exact original request, with separate live and pure archival interpretation. */
final class EventMaterialQuerySourceTest {
    private static final OperationKey OP = new OperationKey("query-event-material-test");
    private static final RawJson VALUE = new RawJson(new byte[]{'{','}'});
    private static ActionCommand command() { return ActionCoordinatorTest.command("material-contract", OP.value()); }
    private static PlanningReadRequest request() {
        var command = command(); return new PlanningReadRequest(command.before(), command.source(), command.sessionId(), OP,
            new OpportunityJson.Obj(Map.of()), command.deadline());
    }
    private static EventMaterialQuerySource.Frame frame(PlanningReadRequest request) {
        return new EventMaterialQuerySource.Frame(request.before(), request.source(), request.sessionId(), new OpportunityJson.Obj(Map.of()), request.deadline());
    }
    private static PlanningReadReceipt receipt(PlanningReadRequest request, String contractId) {
        var guard = new PlanningReadGuard(ActionCoordinatorTest.guard(command(), ActionCoordinatorTest.NOW), true, true, true, "d".repeat(64));
        var ack = new NativeActionPort.AckReceived("material-original-read", true, Optional.of(VALUE), VALUE, new byte[]{1});
        return new PlanningReadReceipt(request, contractId, ack.requestId(), guard, guard, ack);
    }
    private static ReadContract<RawJson> contract(AtomicInteger live, AtomicInteger replay) {
        return new ReadContract<>("material-contract-test", OP, Optional.empty(), "test-only-material",
            ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE, ReadContract.WireProfile.EXECUTE_STEP,
            ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP, ActionCoordinatorTest.REF,
            (request, id) -> { throw new AssertionError("this contract test cannot submit"); },
            original -> { live.incrementAndGet(); return VALUE; }, original -> { replay.incrementAndGet(); return VALUE; });
    }
    @Test void replayUsesOnlyTheExplicitPureDecoder() {
        var live = new AtomicInteger(); var replay = new AtomicInteger(); var contract = contract(live, replay);
        var request = request(); var resolved = new EventMaterialQuerySource.Resolved<>(contract, request, Function.identity(), Optional.empty());
        var original = receipt(request, contract.contractId());
        assertEquals(VALUE, resolved.decode(original)); assertEquals(1, live.get()); assertEquals(0, replay.get());
        assertEquals(VALUE, resolved.replay(original)); assertEquals(1, live.get()); assertEquals(1, replay.get());
        var legacy = new ReadContract<RawJson>(contract.contractId(), OP, Optional.empty(), "test-only-material",
            ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE, ReadContract.WireProfile.EXECUTE_STEP, ActionCoordinatorTest.REF,
            requestValue -> { throw new AssertionError("no submit"); }, originalValue -> { live.incrementAndGet(); return VALUE; });
        var withoutReplay = new EventMaterialQuerySource.Resolved<>(legacy, request, Function.identity(), Optional.empty());
        assertThrows(IllegalStateException.class, () -> withoutReplay.replay(original)); assertEquals(1, live.get());
    }
    @Test void issuedSelectionRejectsFrameDeadlineArgumentsAndContractSubstitution() {
        var contract = contract(new AtomicInteger(), new AtomicInteger()); var request = request();
        var resolved = new EventMaterialQuerySource.Resolved<>(contract, request, Function.identity(), Optional.of(ActionCoordinatorTest.REF));
        assertDoesNotThrow(() -> resolved.requireFrame(frame(request), OP));
        var later = new PlanningReadRequest(request.before(), request.source(), request.sessionId(), OP, request.arguments(), request.deadline().plusSeconds(30));
        assertThrows(IllegalArgumentException.class, () -> resolved.requireFrame(frame(later), OP));
        assertThrows(IllegalArgumentException.class, () -> resolved.replay(receipt(later, contract.contractId())));
        assertThrows(IllegalArgumentException.class, () -> resolved.replay(receipt(request, "different-installed-selection")));
        var otherArguments = new PlanningReadRequest(request.before(), request.source(), request.sessionId(), OP,
            new OpportunityJson.Obj(Map.of("other", new OpportunityJson.Bool(true))), request.deadline());
        assertThrows(IllegalArgumentException.class, () -> resolved.decode(receipt(otherArguments, contract.contractId())));
    }
    @Test void fixedSourceRetainsTheInstalledTypedContractAndProducesEachCurrentRequest() {
        var contract = contract(new AtomicInteger(), new AtomicInteger()); var current = frame(request());
        var source = new NativeEventEffects.MaterialQuery<>(contract, Function.identity(), semantic -> new OpportunityJson.Obj(Map.of()));
        var first = source.resolve(current); first.requireFrame(current, source.operation());
        assertSame(contract, first.contract()); assertTrue(first.replayContext().isEmpty());
        var later = new EventMaterialQuerySource.Frame(current.before(), current.source(), current.sessionId(), current.semantic(), current.deadline().plusSeconds(30));
        var second = source.resolve(later); second.requireFrame(later, source.operation());
        assertSame(contract, second.contract()); assertNotEquals(first.request(), second.request());
        assertEquals(current.deadline(), first.request().deadline()); assertEquals(later.deadline(), second.request().deadline());
    }
}
