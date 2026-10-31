package org.xar.ck3.research.m5;

import java.util.List;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentWholeCrt189PortsApi.MemoryImage;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Calls;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.LoopBudget;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Call;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Tail;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185WitnessApi.Event;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185WitnessApi.CallStep;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185WitnessApi.TailStep;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185WitnessApi.GsStep;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185WitnessApi.LoopStep;

public final class GovernmentWholeCrt189Ports implements Calls, LoopBudget {
    private final MemoryImage memory;
    private final List<Event> events;
    private int cursor = 0;

    public GovernmentWholeCrt189Ports(MemoryImage memory, List<Event> events) {
        this.memory = Objects.requireNonNull(memory);
        this.events = List.copyOf(Objects.requireNonNull(events));
    }

    private <T extends Event> T next(Class<T> type) {
        if (cursor >= events.size()) throw new IllegalStateException("Event list exhausted");
        Event e = events.get(cursor++);
        if (!type.isInstance(e)) throw new IllegalStateException("Expected " + type.getSimpleName() + " but got " + e.getClass().getSimpleName());
        return type.cast(e);
    }

    @Override
    public VolatileBits invoke(Call call) {
        CallStep step = next(CallStep.class);
        if (!step.expected().equals(call)) throw new IllegalStateException("Call mismatch");
        Map<Long, Integer> snapshot = memory.snapshot();
        if (!snapshot.equals(step.expectedMemoryBefore())) throw new IllegalStateException("Memory before mismatch");
        for (int v : step.mutation().values()) {
            if (v < 0 || v > 255) throw new IllegalStateException("Invalid mutation byte");
        }
        memory.mutate(step.mutation());
        return step.normalPost();
    }

    @Override
    public NormalReturn tail(Tail transfer) {
        TailStep step = next(TailStep.class);
        if (!step.expected().equals(transfer)) throw new IllegalStateException("Tail mismatch");
        Map<Long, Integer> snapshot = memory.snapshot();
        if (!snapshot.equals(step.expectedMemoryBefore())) throw new IllegalStateException("Memory before mismatch");
        for (int v : step.mutation().values()) {
            if (v < 0 || v > 255) throw new IllegalStateException("Invalid mutation byte");
        }
        memory.mutate(step.mutation());
        return step.normalPost();
    }

    @Override
    public long readGsQword58() {
        GsStep step = next(GsStep.class);
        return step.returnedBits();
    }

    @Override
    public void beforeStep(long loopHeaderRva, long guardAddressBits) {
        LoopStep step = next(LoopStep.class);
        if (step.loopHeaderRva() != loopHeaderRva || step.guardAddressBits() != guardAddressBits) {
            throw new IllegalStateException("Loop step mismatch");
        }
    }

    public void verifyComplete() {
        if (cursor != events.size()) throw new IllegalStateException("Events not fully consumed");
    }
}
