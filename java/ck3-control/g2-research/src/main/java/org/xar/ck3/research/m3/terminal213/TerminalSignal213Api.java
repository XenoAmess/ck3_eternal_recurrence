package org.xar.ck3.research.m3.terminal213;

import org.xar.ck3.research.m3.terminal207.Terminal207Api.Memory;

/** Proposal declarations only; no347B body or shared source adoption. */
public final class TerminalSignal213Api {
    private TerminalSignal213Api() { }

    /** Raw address bits plus only the incoming low32 business register roles. */
    public record Input(long moduleBase, long calleeEntryRsp, int ecx, int edx, int r8d) { }

    /**
     * Same supplied Memory may be changed by any port. Site is the actual CALL PC.
     * Code is the actual fresh64 IAT load, never an imported-routine identity.
     * These Java parameters are known-source observations, not complete native signatures.
     * If a port needs unrepresented registers/CPU/stack effects it must remain unsupported.
     */
    public interface Ports {
        void call4224800Initial(Memory memory, long siteRva, int ecx, int edx, int r8d);
        void call4226f10(Memory memory, long siteRva, long rcx, int edx, int r8d);
        void call43da418(Memory memory, long siteRva, long code, long rcx);
        long call43da2a0(Memory memory, long siteRva, long code, long rcx, long rdx, int r8d);
        /** callerBodyRsp is source storage context, not an additional native argument. */
        void call43da2a8(Memory memory, long siteRva, long code,
                long rcx, long rdx, long r8, long r9, long callerBodyRsp);
        /** No known argument register is projected; this is NOT a proven native zero-arg function. */
        int call43da6a0(Memory memory, long siteRva, long code);
        void call43da770(Memory memory, long siteRva, long code, int ecx);
        int call43da2b0(Memory memory, long siteRva, long code, long rcx);
        /** Only ECX is newly established here; initial-call EDX/R8D are not reused. */
        void call4224800Repeat(Memory memory, long siteRva, int ecx);
        void call4224700(Memory memory, long siteRva, long rcx);
    }
}
