package org.xar.ck3.research.m3.index183;
import org.xar.ck3.research.m3.RegistryConsumerApi176;
/** Full397B normal storage/EAX projection; no CPU ABI/EH or comparator body claim. */
public final class RegistrationIndex183Api {
    private RegistrationIndex183Api() { }
    public record Bytes16(long low, long high) { }
    public interface Memory extends RegistryConsumerApi176.Memory {
        Bytes16 read128(long address);
        void write128(long address, Bytes16 value);
    }
    public record Scratch(long bodyRsp) {
        public long entryRsp() { return bodyRsp + 0x78L; }
    }
    public record Input(long receiver, long keyDescriptor, Scratch scratch) { }
    /** Only explicit source arguments: R8 is MOVSXD signed length; EAX is consumed, no library algorithm guessed. */
    public interface Ports {
        int compare42270b0(Memory memory, long callSiteRva, long rcx, long rdx, long signedR8);
    }
}
