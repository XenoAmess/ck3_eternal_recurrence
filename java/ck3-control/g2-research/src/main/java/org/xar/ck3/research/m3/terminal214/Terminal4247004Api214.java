package org.xar.ck3.research.m3.terminal214;

import java.util.Objects;
import org.xar.ck3.research.m3.terminal207.Terminal207Api;

/**
 * Declaration proposal for the supplied-memory normal business CFG of 4247004.
 * This does not represent CPU saves, physical CALL/RET, full registers, or EH.
 * All addresses and pointer values are raw bits in one caller-owned storage view.
 */
public final class Terminal4247004Api214 {
    private Terminal4247004Api214() { }

    /** Existing Native widths and unsigned-byte reads are inherited unchanged. */
    public interface Memory extends Terminal207Api.Memory {
        void write8(long address, int value);
    }

    /** Actual post-CALL handler entry H; body B is H minus five pushes and 40h. */
    public record Scratch(long entryRsp) {
        public long bodyRsp() { return entryRsp - 0x68L; }
    }

    /** codeBits is the source's 32-bit incoming ECX, not an invented pointer. */
    public record Input(long moduleBase, int codeBits, Scratch scratch) {
        public Input {
            Objects.requireNonNull(scratch, "scratch");
        }
    }

    public sealed interface Outcome permits NormalReturn, Trap { }

    /** Source writes EAX, hence both supported results have zero upper 32 bits. */
    public record NormalReturn(long raxBits) implements Outcome {
        public NormalReturn {
            if (raxBits != 0L && raxBits != 0xFFFF_FFFFL) {
                throw new IllegalArgumentException("not a source normal-return value");
            }
        }
    }

    /** Reached only if the source abort callback returns normally. */
    public enum Trap implements Outcome {
        INT3_424726D
    }

    /**
     * CALL R8 at 4247218; 3 bytes, continuation 424721B.
     * targetBits is fresh [targetSlotAddress]; handlerBits is source RAX.
     * ECX and EDX are 32-bit writes, each zero extended in the native register.
     */
    public record DispatchR8(long siteRva, long targetSlotAddress, long targetBits,
                             long handlerBits, int ecxBits, int edxBits) { }

    /**
     * CALL RDX at 4247229; 2 bytes, continuation 424722B.
     * RDX contains targetBits, distinct from handlerBits in RAX.
     * ECX is a 32-bit write, zero extended in the native register.
     */
    public record DispatchRdx(long siteRva, long targetSlotAddress, long targetBits,
                              long handlerBits, int ecxBits) { }

    /**
     * These are known-argument business ports, not complete machine call frames.
     * Each receives the identical Memory object. A void port may return normally;
     * neither its declaration nor a normal return proves native V/N preservation.
     * No newly prepared formal arguments are invented for the no-argument ports.
     * Exceptions or nonreturning behavior of an opaque port are not caught here.
     */
    public interface Ports {
        /** Low32 ECX is still incoming code4/8/11; a known observation, not a guessed formal argument. */
        long call424fc74(Memory memory, long siteRva, int ecxBits);
        long call423b18c(Memory memory, long siteRva);
        void call4232a50(Memory memory, long siteRva);
        void call4247ffc(Memory memory, long siteRva, int ecxBits);
        long call424faf8(Memory memory, long siteRva);
        void call4248050(Memory memory, long siteRva, int ecxBits);
        void call4242354(Memory memory, long siteRva, int ecxBits);
        void callIndirectR8(Memory memory, DispatchR8 call);
        void callIndirectRdx(Memory memory, DispatchRdx call);
    }

}
