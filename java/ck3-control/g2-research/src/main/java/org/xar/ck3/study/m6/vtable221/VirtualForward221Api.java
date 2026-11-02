package org.xar.ck3.study.m6.vtable221;

/** Logical normal-body forwarding projection; not saved GPR/RSP/RFLAGS, native allocation or full ABI. */
public final class VirtualForward221Api {
    private VirtualForward221Api() { }
    /** Caller must supply the actual incoming R9; the mature216 three-argument port cannot invent it. */
    public record Input(long rcxRaw64, long rdxRaw64, long r8Raw64, long r9Raw64) { }
    public interface Memory extends org.xar.ck3.study.m6.element150.Element150Inputs.Memory { }
    /** These are only the five GPR values actively assigned/forwarded by the selected body. */
    public record Invocation(int callsiteRva, long functionRaw64, long raxRaw64,
            long rcxRaw64, long rdxRaw64, long r8Raw64, long r9Raw64) { }
    /** Unknown virtual bodies may change the same RAM and return RAX or throw. No invented side effect. */
    public interface Calls {
        long call(Invocation actual);
        long tailJump(Invocation actual);
    }
}
