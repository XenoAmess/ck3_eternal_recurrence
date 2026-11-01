package org.xar.ck3.research.m3.lookup236;

import org.xar.ck3.research.m3.lookup221.ModuleLookup221Api;
import org.xar.ck3.control.g2.common.nativecore.task.captured.RequestStaticDispatch4267630;

public final class Lookup236Binding {

    private Lookup236Binding() { }

    public static ModuleLookup221Api.Ports bind(long moduleBase, ModuleLookup221Api.Memory capturedMemory, Lookup236Api.DispatchSupplier supplier, ModuleLookup221Api.Ports fallback) {
        long expectedCodeTarget = moduleBase + 0x4267630L;

        return new ModuleLookup221Api.Ports() {
            @Override
            public int call43da458(ModuleLookup221Api.Memory memory, long siteRva, long codeTarget, long rcx, long rdx, long r8) {
                return fallback.call43da458(memory, siteRva, codeTarget, rcx, rdx, r8);
            }

            @Override
            public long call43da680(ModuleLookup221Api.Memory memory, long siteRva, long codeTarget, long rcx, long rdx) {
                return fallback.call43da680(memory, siteRva, codeTarget, rcx, rdx);
            }

            @Override
            public void call43dbba8(ModuleLookup221Api.Memory memory, long siteRva, long codeTarget, int ecx, long rax) {
                if (codeTarget != expectedCodeTarget) {
                    fallback.call43dbba8(memory, siteRva, codeTarget, ecx, rax);
                    return;
                }

                if (memory != capturedMemory || siteRva != 0x424230FL) {
                    throw new IllegalArgumentException("Mismatched identity or site for 43DBBA8");
                }

                long knownRcx = Integer.toUnsignedLong(ecx);
                RequestStaticDispatch4267630.execute(knownRcx, rax, new RequestStaticDispatch4267630.TailTarget() {
                    @Override
                    public int jumpRax(long targetRax, long knownRcx) {
                        return supplier.jumpRax(capturedMemory, 0x424230FL, targetRax, knownRcx);
                    }
                });
            }

            @Override
            public void call43da7c0(ModuleLookup221Api.Memory memory, long siteRva, long codeTarget, long rcx) {
                fallback.call43da7c0(memory, siteRva, codeTarget, rcx);
            }
        };
    }
}