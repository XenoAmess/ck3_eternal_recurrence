package org.xar.ck3.research.m3.terminal207;
import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
/** Supplied-storage business CFG of exact86B4232CF4; no CPU/stack/EH or native execution. */
public final class Terminal207Api {
    private Terminal207Api() { }
    public interface Memory extends NativeTaskMemory {
        int readUnsigned8(long address);
    }
    /** Only source-established arguments. Missing machine context must remain unsupported at the port. */
    public interface Ports {
        long call4246fb4(Memory memory, long siteRva);
        default long call4246fb4(Memory memory, long siteRva, long calleeEntryRsp) {
            return call4246fb4(memory, siteRva);
        }
        void call4247004(Memory memory, long siteRva, int ecx);
        default void call4247004(Memory memory, long siteRva, int ecx, long calleeEntryRsp) {
            call4247004(memory, siteRva, ecx);
        }
        int call43da258(Memory memory, long siteRva, long code, int ecx);
        void call423283c(Memory memory, long siteRva, int ecx, int edx, int r8d);
        default void call423283c(Memory memory, long siteRva, int ecx, int edx, int r8d, long calleeEntryRsp) {
            call423283c(memory, siteRva, ecx, edx, r8d);
        }
        void call4242354(Memory memory, long siteRva, int ecx);
        default void call4242354(Memory memory, long siteRva, int ecx, long calleeEntryRsp) {
            call4242354(memory, siteRva, ecx);
        }
    }
    public enum Stop { INT29_ECX7, INT3_4232D49 }
}
