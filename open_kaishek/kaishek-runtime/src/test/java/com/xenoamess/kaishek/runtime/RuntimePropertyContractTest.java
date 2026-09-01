package com.xenoamess.kaishek.runtime;

import static org.junit.jupiter.api.Assertions.*;

import java.util.Map;
import java.util.concurrent.atomic.AtomicInteger;
import com.xenoamess.kaishek.profile.OpcodeRegistry;
import org.junit.jupiter.api.Test;

/** Small state-machine/property checks for stale guards and resource receipts. */
class RuntimePropertyContractTest {
    private static final ScopeRef OWNER = new ScopeRef(ScopeType.CHARACTER, "owner");
    private static final ScopeRef SUBJECT = new ScopeRef(ScopeType.CHARACTER, "subject");

    @Test
    void deadlineRejectsStaleSerialRevisionAndScopeAndAcceptsOnlyDueFreshCase() {
        CaseRegistry registry = new CaseRegistry();
        CaseBinding opened = registry.open("case", OWNER, SUBJECT);
        DeadlineTicket ticket = new DeadlineTicket("case", opened.serial(), opened.revision(), 100, OWNER, SUBJECT);

        assertEquals(ExecutionStatus.INVALID, ticket.validate(opened, 99));
        assertEquals(ExecutionStatus.SUCCESS, ticket.validate(opened, 100));
        assertEquals(ExecutionStatus.STALE, ticket.validate(opened.nextRevision(), 100));
        CaseBinding rebound = registry.open("case", OWNER, new ScopeRef(ScopeType.CHARACTER, "other"));
        assertEquals(ExecutionStatus.STALE, ticket.validate(rebound, 100));
        assertFalse(registry.matches(opened), "opening the same id must invalidate the prior serial");
    }

    @Test
    void unknownHookFailsClosedAndLeavesNoWriteSideEffects() {
        HookDispatcher dispatcher = new HookDispatcher();
        ScopeContext context = new ScopeContext(OWNER, OWNER, null);
        ExecutionTrace trace = new ExecutionTrace();
        ExecutionResult<?> result = dispatcher.dispatch("xar.unknown", context, Map.of(), trace);
        assertEquals(ExecutionStatus.UNSUPPORTED, result.status());
        assertNull(result.value());
        assertTrue(result.reason().contains("unregistered"));
        assertEquals(1, result.trace().entries().size());
        assertEquals("unsupported", result.trace().entries().get(0).phase());
        assertTrue(result.trace().readWriteSet().writes().isEmpty());
    }

    @Test
    void nullHookNameFailsClosedWithoutMapLookupException() {
        HookDispatcher dispatcher = new HookDispatcher();
        ScopeContext context = new ScopeContext(OWNER, OWNER, null);
        ExecutionTrace trace = new ExecutionTrace();

        ExecutionResult<?> result = dispatcher.dispatch(null, context, Map.of(), trace);

        assertEquals(ExecutionStatus.UNSUPPORTED, result.status());
        assertTrue(result.reason().contains("unregistered"));
        assertEquals("<null>", result.trace().entries().get(0).operation());
        assertFalse(dispatcher.contains(null));
    }

    @Test
    void hookExceptionsBecomeExplicitUnsupportedOrInvalidResults() {
        HookDispatcher dispatcher = new HookDispatcher();
        ScopeContext context = new ScopeContext(OWNER, OWNER, null);
        ExecutionTrace trace = new ExecutionTrace();
        dispatcher.register("unsupported", (invocation, ignored) -> {
            throw new UnsupportedOperationException("native hook unavailable");
        });
        dispatcher.register("invalid", (invocation, ignored) -> {
            throw new IllegalArgumentException("bad hook payload");
        });

        ExecutionResult<?> unsupported = dispatcher.dispatch("unsupported", context, Map.of(), trace);
        assertEquals(ExecutionStatus.UNSUPPORTED, unsupported.status());
        assertTrue(unsupported.reason().contains("native hook unavailable"));

        ExecutionResult<?> invalid = dispatcher.dispatch("invalid", context, Map.of(), trace);
        assertEquals(ExecutionStatus.INVALID, invalid.status());
        assertTrue(invalid.reason().contains("bad hook payload"));
    }

    @Test
    void unknownOpcodeFailsClosedWithoutInvokingAHandler() {
        RuntimeKernel kernel = new RuntimeKernel(OpcodeRegistry.empty());
        ExecutionContext context = new ExecutionContext(
                new ScopeContext(OWNER, OWNER, null), 10, DrawTape.of(1));
        ExecutionResult<Object> result = kernel.execute("effect.not_registered", context, Map.of());
        assertEquals(ExecutionStatus.UNSUPPORTED, result.status());
        assertTrue(result.reason().contains("unknown opcode"));
        assertTrue(context.variables().isEmpty());
        assertEquals(0, context.drawTape().position());
    }

    @Test
    void invalidHandlerRegistrationsAndNullEventContextAreRejectedExplicitly() {
        RuntimeKernel kernel = new RuntimeKernel(OpcodeRegistry.empty());

        assertThrows(IllegalArgumentException.class, () -> kernel.register(null, invocation -> null));
        assertThrows(IllegalArgumentException.class, () -> kernel.register("", invocation -> null));
        assertThrows(IllegalArgumentException.class, () -> kernel.register("missing", null));
        assertThrows(NullPointerException.class, () -> kernel.dispatchDueEvents(null));
    }

    @Test
    void compatibilityScopeBridgePreservesScopeKind() {
        ScopeRef performance = new ScopeRef(ScopeType.PERFORMANCE_DOMAIN, "pd");
        ScopeRef caseScope = new ScopeRef(ScopeType.CASE, "case");
        ScopeRef saved = new ScopeRef(ScopeType.SAVED, "saved");

        assertEquals(com.xenoamess.kaishek.profile.ScopeType.PERFORMANCE_DOMAIN, performance.type());
        assertEquals(com.xenoamess.kaishek.profile.ScopeType.CASE, caseScope.type());
        assertEquals(com.xenoamess.kaishek.profile.ScopeType.SAVED, saved.type());
    }

    @Test
    void receiptRefundIsCappedAndConservesResourcesAcrossReplay() {
        ReceiptJournal journal = new ReceiptJournal(Map.of("player\u0000gold", 100L));
        Receipt charged = journal.debit("tx-1", "player", "gold", 40);
        assertEquals(60, journal.balance("player", "gold"));
        assertSame(charged, journal.debit("tx-1", "player", "gold", 40), "same transaction is idempotent");
        assertEquals(60, journal.balance("player", "gold"));

        Receipt refunded = journal.refund("tx-1", 15);
        assertEquals(75, journal.balance("player", "gold"));
        assertEquals(15, refunded.refunded());
        assertEquals(25, refunded.net());
        assertEquals(100, journal.balance("player", "gold") + refunded.net(),
                "debit/refund must conserve the resource total");
        assertThrows(IllegalArgumentException.class, () -> journal.refund("tx-1", 26));
        assertEquals(75, journal.balance("player", "gold"), "rejected over-refund is atomic");
        assertThrows(IllegalStateException.class, () -> journal.debit("tx-1", "player", "gold", 41));
        assertEquals(75, journal.balance("player", "gold"));
    }

    @Test
    void refundOverflowAndInvalidDebitAreAtomic() {
        ReceiptJournal journal = new ReceiptJournal(Map.of("player\u0000gold", Long.MAX_VALUE));
        Receipt charged = journal.debit("tx-overflow", "player", "gold", 1);
        journal.credit("player", "gold", 1);
        assertEquals(Long.MAX_VALUE, journal.balance("player", "gold"));

        // The refund would overflow the balance. Neither the receipt nor the
        // balance may be published when that arithmetic fails.
        assertThrows(ArithmeticException.class, () -> journal.refund("tx-overflow", 1));
        assertSame(charged, journal.get("tx-overflow"));
        assertEquals(Long.MAX_VALUE, journal.balance("player", "gold"));

        assertThrows(IllegalArgumentException.class,
                () -> journal.debit("tx-invalid", null, "gold", 1));
        assertEquals(Long.MAX_VALUE, journal.balance("player", "gold"));
        assertNull(journal.get("tx-invalid"));
    }

    @Test
    void queuedEventWithReopenedCaseIsStaleAndHandlerIsNotCalled() {
        CaseRegistry cases = new CaseRegistry();
        CaseBinding original = cases.open("case", OWNER, SUBJECT);
        HookDispatcher hooks = new HookDispatcher();
        AtomicInteger calls = new AtomicInteger();
        hooks.register("case.complete", (invocation, trace) -> {
            calls.incrementAndGet();
            return ExecutionResult.success("called", trace);
        });
        RuntimeKernel kernel = new RuntimeKernel(OpcodeRegistry.empty(), hooks, cases);
        ExecutionContext context = new ExecutionContext(new ScopeContext(OWNER, OWNER, null), 1, DrawTape.of());
        context.schedule("case.complete", 2, original, Map.of());
        cases.open("case", OWNER, SUBJECT); // increments serial, invalidating queued ticket
        context.advanceTo(2);
        var results = kernel.dispatchDueEvents(context);
        assertEquals(1, results.size());
        assertEquals(ExecutionStatus.STALE, results.get(0).status());
        assertEquals(0, calls.get());
    }
}
