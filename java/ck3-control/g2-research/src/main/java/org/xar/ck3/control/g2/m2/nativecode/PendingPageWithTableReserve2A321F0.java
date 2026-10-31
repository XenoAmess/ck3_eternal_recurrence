package org.xar.ck3.control.g2.m2.nativecode;

public final class PendingPageWithTableReserve2A321F0 {
    private PendingPageWithTableReserve2A321F0() { }

    public interface Memory extends PendingPageReserve2A321F0.Memory, PendingPageTableReserve2A32620.Memory { }

    public interface Calls {
        void call3F7AA40(Memory memory, long rcx, int edx, long fifth);
        long allocate(Memory memory, long target, long rcx, long rdx, int r8d);
        void release(Memory memory, long target, long rcx, long rdx, int r8d);
        void call4226F10(Memory memory, long rcx, int edx, long r8);
        void call4223F44(Memory memory, long rcx, int edx);
        long call4223B94(Memory memory, int ecx);
    }

    public static boolean ensure(Memory memory, Calls calls, PendingPageReserve2A321F0.Input input) {
        PendingPageReserve2A321F0.Calls pageCalls = new PendingPageReserve2A321F0.Calls() {
            @Override
            public void call3F7AA40(PendingPageReserve2A321F0.Memory m, long rcx, int edx, long fifth) {
                calls.call3F7AA40(memory, rcx, edx, fifth);
            }
            @Override
            public void call2A32620(PendingPageReserve2A321F0.Memory m, long rcx, int edx) {
                PendingPageTableReserve2A32620.reserve(memory, new PendingPageTableReserve2A32620.Calls() {
                    @Override
                    public long allocate(PendingPageTableReserve2A32620.Memory mm, long target, long rcc, long rdd, int r8d) {
                        return calls.allocate(memory, target, rcc, rdd, r8d);
                    }
                    @Override
                    public void release(PendingPageTableReserve2A32620.Memory mm, long target, long rcc, long rdd, int r8d) {
                        calls.release(memory, target, rcc, rdd, r8d);
                    }
                    @Override
                    public void call4223F44(PendingPageTableReserve2A32620.Memory mm, long rcc, int rdd) {
                        calls.call4223F44(memory, rcc, rdd);
                    }
                }, rcx, edx);
            }
            @Override
            public void call4226F10(PendingPageReserve2A321F0.Memory m, long rcx, int edx, long r8) {
                calls.call4226F10(memory, rcx, edx, r8);
            }
            @Override
            public void call4223F44(PendingPageReserve2A321F0.Memory m, long rcx, int edx) {
                calls.call4223F44(memory, rcx, edx);
            }
            @Override
            public long call4223B94(PendingPageReserve2A321F0.Memory m, int ecx) {
                return calls.call4223B94(memory, ecx);
            }
        };
        return PendingPageReserve2A321F0.ensure(memory, pageCalls, input);
    }
}