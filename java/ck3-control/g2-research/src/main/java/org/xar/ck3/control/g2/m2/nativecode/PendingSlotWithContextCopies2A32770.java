package org.xar.ck3.control.g2.m2.nativecode;

/** Actual known 2A32770 -> 3076B60 -> twice373ACF0 call composition. */
public final class PendingSlotWithContextCopies2A32770 {
    private PendingSlotWithContextCopies2A32770() { }
    public interface Memory extends PendingSlotProducer2A32770.Memory,
            PendingEmbeddedCopy373ACF0.Memory { }
    public interface Calls extends PendingEmbeddedCopy373ACF0.Calls {
        boolean call1ACDFB0(PendingSlotProducer2A32770.Memory memory, long rcx, int edx);
        boolean call2A321F0(PendingSlotProducer2A32770.Memory memory, long rcx, int edx);
        void call105D2D0(PendingContextCopy3076B60.Memory memory, long rcx);
        void callBCB7C0(PendingContextCopy3076B60.Memory memory, long rcx,
                int edx, long r8, long r9);
        void call2503880(PendingContextCopy3076B60.Memory memory, long rcx, long rdx);
    }
    public static long produce(Memory memory, Calls calls,
            PendingSlotProducer2A32770.Input input) {
        PendingSlotProducer2A32770.Memory outerMemory = memory;
        PendingSlotProducer2A32770.Calls outerCalls = new PendingSlotProducer2A32770.Calls() {
            @Override
            public boolean call1ACDFB0(PendingSlotProducer2A32770.Memory m, long rcx, int edx) {
                return calls.call1ACDFB0(m, rcx, edx);
            }
            @Override
            public boolean call2A321F0(PendingSlotProducer2A32770.Memory m, long rcx, int edx) {
                return calls.call2A321F0(m, rcx, edx);
            }
            @Override
            public void call3076B60(PendingSlotProducer2A32770.Memory m, long rcx, long rdx) {
                PendingContextCopy3076B60.Memory contextMemory = memory;
                PendingContextCopy3076B60.Calls contextCalls = new PendingContextCopy3076B60.Calls() {
                    @Override
                    public void call373ACF0(PendingContextCopy3076B60.Memory cm, long cr, long cd) {
                        PendingEmbeddedCopy373ACF0.Memory embeddedMemory = memory;
                        PendingEmbeddedCopy373ACF0.Calls embeddedCalls = new PendingEmbeddedCopy373ACF0.Calls() {
                            @Override
                            public void call8895D0(PendingEmbeddedCopy373ACF0.Memory em, long er, long ed) {
                                calls.call8895D0(em, er, ed);
                            }
                            @Override
                            public void call37282B0(PendingEmbeddedCopy373ACF0.Memory em, long er, long ed) {
                                calls.call37282B0(em, er, ed);
                            }
                            @Override
                            public void call260E040(PendingEmbeddedCopy373ACF0.Memory em, long er, long ed) {
                                calls.call260E040(em, er, ed);
                            }
                            @Override
                            public void call3727180(PendingEmbeddedCopy373ACF0.Memory em, long er, long ed) {
                                calls.call3727180(em, er, ed);
                            }
                        };
                        PendingEmbeddedCopy373ACF0.copy(embeddedMemory, embeddedCalls, cr, cd, input.moduleBase());
                    }
                    @Override
                    public void call105D2D0(PendingContextCopy3076B60.Memory cm, long cr) {
                        calls.call105D2D0(cm, cr);
                    }
                    @Override
                    public void callBCB7C0(PendingContextCopy3076B60.Memory cm, long cr, int cd, long c8, long c9) {
                        calls.callBCB7C0(cm, cr, cd, c8, c9);
                    }
                    @Override
                    public void call2503880(PendingContextCopy3076B60.Memory cm, long cr, long cd) {
                        calls.call2503880(cm, cr, cd);
                    }
                };
                PendingContextCopy3076B60.copy(contextMemory, contextCalls, rcx, rdx);
            }
        };
        return PendingSlotProducer2A32770.produce(outerMemory, outerCalls, input);
    }
}
