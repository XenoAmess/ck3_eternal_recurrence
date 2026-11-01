package org.xar.ck3.research.m3.fc74238;

import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import org.xar.ck3.research.m3.terminal214.Terminal4247004Api214;
import org.xar.ck3.research.m3.fc74238.Fc74Api238;

/**
 * Binding for the actual 214 consumer to the new FC74 producer.
 * Captures moduleBase, identical Memory, child Ports, and fallback Ports.
 * Owned call424fc74 checks identity and site before invoking the producer.
 * All other 214 Ports methods delegate exactly to fallback.
 */
public final class Fc74FromHandlerBinding238 {
    private Fc74FromHandlerBinding238() { }

    public static Terminal4247004Api214.Ports bind(long moduleBase, Terminal4247004Api214.Memory capturedMemory, Fc74Api238.Ports child, Terminal4247004Api214.Ports fallback) {
        if (capturedMemory == null) throw new NullPointerException("capturedMemory");
        if (child == null) throw new NullPointerException("child");
        if (fallback == null) throw new NullPointerException("fallback");

        return new Terminal4247004Api214.Ports() {
            @Override
            public long call424fc74(Terminal4247004Api214.Memory memory, long siteRva, int ecxBits) {
                if (memory != capturedMemory) {
                    throw new IllegalArgumentException("Memory identity mismatch");
                }
                if (siteRva != 0x424707DL) {
                    throw new IllegalArgumentException("Site mismatch");
                }
                // Invoke the producer exactly once with captured base and received ECX
                // The producer class Fc74Target424FC74 is assumed to exist in the same package
                // as per the contract "New producer class: org.xar.ck3.research.m3.fc74238.Fc74Target424FC74"
                // We call its static execute method directly.
                return Fc74Target424FC74.execute(memory, child, new Fc74Api238.Input(moduleBase, ecxBits));
            }

            @Override
            public long call423b18c(Terminal4247004Api214.Memory memory, long siteRva) {
                return fallback.call423b18c(memory, siteRva);
            }

            @Override
            public void call4232a50(Terminal4247004Api214.Memory memory, long siteRva) {
                fallback.call4232a50(memory, siteRva);
            }

            @Override
            public void call4247ffc(Terminal4247004Api214.Memory memory, long siteRva, int ecxBits) {
                fallback.call4247ffc(memory, siteRva, ecxBits);
            }

            @Override
            public long call424faf8(Terminal4247004Api214.Memory memory, long siteRva) {
                return fallback.call424faf8(memory, siteRva);
            }

            @Override
            public void call4248050(Terminal4247004Api214.Memory memory, long siteRva, int ecxBits) {
                fallback.call4248050(memory, siteRva, ecxBits);
            }

            @Override
            public void call4242354(Terminal4247004Api214.Memory memory, long siteRva, int ecxBits) {
                fallback.call4242354(memory, siteRva, ecxBits);
            }

            @Override
            public void callIndirectR8(Terminal4247004Api214.Memory memory, Terminal4247004Api214.DispatchR8 call) {
                fallback.callIndirectR8(memory, call);
            }

            @Override
            public void callIndirectRdx(Terminal4247004Api214.Memory memory, Terminal4247004Api214.DispatchRdx call) {
                fallback.callIndirectRdx(memory, call);
            }
        };
    }
}