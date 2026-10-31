package org.xar.ck3.research.m3;

/** Exact observations for held212B+14B normal source; no native CPU execution. */
public final class GroupNameEqualApi185 {
    private GroupNameEqualApi185() { }
    public record Vector128(long low, long high) { }
    public record Scratch(long sourceEntryRsp) { }
    public interface Memory extends RegistryConsumerApi176.Memory {
        int readUnsigned16(long address);
        void write16(long address, int value);
        /** One16-byte source observation, low-address little-endian bits first. No hardware atomicity claim. */
        Vector128 read128(long address);
    }
}
