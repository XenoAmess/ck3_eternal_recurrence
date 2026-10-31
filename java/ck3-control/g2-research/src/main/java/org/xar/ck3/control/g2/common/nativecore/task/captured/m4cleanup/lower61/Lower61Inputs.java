package org.xar.ck3.control.g2.common.nativecore.task.captured.m4cleanup.lower61;

import org.xar.ck3.control.g2.common.nativecore.task.captured.m4cleanup.b374.B374Inputs;

/** Effects consumed by the complete 61B body; named IAT roles remain unresolved. */
public final class Lower61Inputs {
    private Lower61Inputs() { }

    /** Entry RDX/R8 are overwritten before use; only the entry RCX value is needed. */
    public record CallInput(long moduleBaseRaw, long rcxRaw) { }
    public record FirstCall(long rcxRaw, long rdxRaw, long r8Raw) { }

    public interface Memory extends B374Inputs.Memory {
    }

    /** Only return bits actually consumed by this body are exposed. */
    public interface Calls {
        int callSlot43DA748(FirstCall known);
        long call423B18C();
        int callSlot43DA738();
        /** Full RCX is the unsigned zero extension of the previous EAX. */
        int call423B0D4(long knownRcxRaw);
    }

    /** Observation only; distinct upper normal and tail edges must remain visible. */
    public interface EdgeObserver {
        void normal(long knownRcxRaw);
        void tail(long knownRcxRaw);
    }
}
