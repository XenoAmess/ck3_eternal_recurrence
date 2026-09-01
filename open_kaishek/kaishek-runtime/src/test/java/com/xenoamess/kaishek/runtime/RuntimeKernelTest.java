package com.xenoamess.kaishek.runtime;

import com.xenoamess.kaishek.profile.*;
import org.junit.jupiter.api.Test;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;

class RuntimeKernelTest {
    private static ScopeRef scope(String id) { return new ScopeRef(com.xenoamess.kaishek.profile.ScopeType.CHARACTER, id); }

    @Test void drawTapeIsFiniteAndReplayable() {
        var tape = DrawTape.of(-1, 4); assertEquals(2, tape.drawInt(3)); assertEquals(0, tape.drawInt(2));
        assertThrows(DrawTapeExhaustedException.class, () -> tape.drawInt(2));
    }

    @Test void receiptConservationAndRefundCap() {
        var j = new ReceiptJournal(Map.of("alice\u0000gold", 10L));
        var r = j.debit("tx", "alice", "gold", 6); assertEquals(4, j.balance("alice", "gold"));
        assertSame(r, j.debit("tx", "alice", "gold", 6));
        j.refund("tx", 2); assertEquals(6, j.balance("alice", "gold"));
        assertThrows(IllegalArgumentException.class, () -> j.refund("tx", 5));
    }

    @Test void staleDeadlineAndBindingAreRejected() {
        var owner = scope("o"); var subject = scope("s"); var registry = new CaseRegistry();
        var binding = registry.open("c", owner, subject); var ticket = new DeadlineTicket("c", binding.serial(), 0, 10, owner, subject);
        assertEquals(ExecutionStatus.INVALID, ticket.validate(binding, 9)); assertEquals(ExecutionStatus.SUCCESS, ticket.validate(binding, 10));
        var newer = registry.open("c", owner, subject); assertEquals(ExecutionStatus.STALE, ticket.validate(newer, 10));
    }

    @Test void unknownOpcodeFailsClosed() {
        var descriptor = new OpcodeDescriptor("known", "p", OpcodeKind.EFFECT, InputType.NONE,
                com.xenoamess.kaishek.profile.ScopeType.CHARACTER, List.of(), RandomnessClass.DETERMINISTIC, false, false, true);
        var kernel = new RuntimeKernel(new OpcodeRegistry(List.of(descriptor)));
        var ctx = new ExecutionContext(new ScopeContext(scope("r"), scope("c"), null), 0, DrawTape.of(1));
        assertEquals(ExecutionStatus.UNSUPPORTED, kernel.execute("missing", ctx, Map.of()).status());
    }
}
