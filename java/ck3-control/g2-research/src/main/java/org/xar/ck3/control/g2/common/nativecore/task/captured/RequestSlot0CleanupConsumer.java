package org.xar.ck3.control.g2.common.nativecore.task.captured;

import org.xar.ck3.control.g2.common.nativecore.task.captured.cleanup.StorageCleanupFree83Consumer;
import org.xar.ck3.control.g2.common.nativecore.task.captured.cleanup.Free83Candidate;
import org.xar.ck3.control.g2.common.nativecore.task.captured.cleanup.Free83Inputs;

public final class RequestSlot0CleanupConsumer {
    private RequestSlot0CleanupConsumer() { }

    public static final class UnsupportedCleanupPath extends RuntimeException {
        private static final long serialVersionUID = 1L;
        private final transient StorageCleanupFree83Consumer.Outcome outcome;

        public UnsupportedCleanupPath(StorageCleanupFree83Consumer.Outcome outcome) {
            this.outcome = outcome;
        }

        public StorageCleanupFree83Consumer.Outcome outcome() {
            return outcome;
        }
    }

    public static long invoke(long moduleBase, long receiver, int rawEdx, long heapHandleRaw,
            RequestE92780.Memory memory, Free83Inputs.Calls calls) {
        RequestSlot0E91d90.Ports ports = new RequestSlot0E91d90.Ports() {
            @Override
            public void call856050(long rcx) {
                StorageCleanupFree83Consumer.Outcome outcome = RequestCleanup856050.cleanup(
                    rcx, heapHandleRaw, memory, calls);
                if (outcome.completion() != StorageCleanupFree83Consumer.Completion.RESET_INLINE &&
                    outcome.completion() != StorageCleanupFree83Consumer.Completion.RESET_AFTER_CALLEE_RETURN) {
                    throw new UnsupportedCleanupPath(outcome);
                }
            }

            @Override
            public void call4223f44(long rcx, int edx) {
                Free83Candidate.release(rcx, heapHandleRaw, calls);
            }
        };
        return RequestSlot0E91d90.invoke(moduleBase, receiver, rawEdx, memory, ports);
    }
}