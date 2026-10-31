package org.xar.ck3.research.m3.context181;

import org.xar.ck3.research.m3.RegistryConsumerApi176;

/** Exact normal-path storage projection of held87B, without CPU ABI or exception-unwind claims. */
public final class ContextGetter181Api {
    private ContextGetter181Api() { }
    public record Bytes16(long low, long high) { }
    public interface Memory extends RegistryConsumerApi176.Memory {
        Bytes16 read128(long address);
        void write128(long address, Bytes16 value);
    }
    /** Caller owns this existing aligned descriptor scratch and all its initial bytes. No native allocation. */
    public record Scratch(long bodyRsp) { }
    public record Input(long moduleBase, Scratch scratch) { }
    /** This is the only call role. It may mutate Memory; its returned bits are not consumed by this source. */
    public interface Ports {
        long initialize3f8b640(Memory memory, long callSiteRva, int ecx, long descriptor, int r8d, int r9d);
    }
}
