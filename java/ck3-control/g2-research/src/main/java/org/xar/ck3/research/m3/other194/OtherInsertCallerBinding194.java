package org.xar.ck3.research.m3.other194;
import org.xar.ck3.research.m3.map191.MapInsert191Api;
import org.xar.ck3.research.m3.map191.MapInsert191Api.Memory;
import org.xar.ck3.research.m3.map191.MapInsert191Api.Ports;
import org.xar.ck3.research.m3.map191.MapInsert191Api.Bytes16;
import org.xar.ck3.research.m3.map191.MapInsert191Api.Scratch;
import org.xar.ck3.research.m3.map191.MapInsert191Api.Input;
import org.xar.ck3.research.m3.map191.MapInsert191Api.UnprojectedInt3;
import org.xar.ck3.research.m3.map191.MapInsertC3B960;

/** Only actual191 C3BBC1 insertOther edge is qualified; eight other callbacks exactdelegate. */
public final class OtherInsertCallerBinding194 {
    private OtherInsertCallerBinding194() { }

    public static Ports bind(long moduleBase, Memory sharedMemory, Ports fallback) {
        return new PortsImpl(moduleBase, sharedMemory, fallback);
    }

    private static final class PortsImpl implements Ports {
        private final long moduleBase;
        private final Memory sharedMemory;
        private final Ports fallback;

        PortsImpl(long moduleBase, Memory sharedMemory, Ports fallback) {
            this.moduleBase = moduleBase;
            this.sharedMemory = sharedMemory;
            this.fallback = fallback;
        }

        @Override
        public int equal3f6d2b0(Memory memory, long siteRva, long rcx, long rdx) {
            return fallback.equal3f6d2b0(memory, siteRva, rcx, rdx);
        }

        @Override
        public int equal3f6d2b0(Memory memory, long siteRva, long rcx, long rdx, long sourceEntryRsp) {
            return fallback.equal3f6d2b0(memory, siteRva, rcx, rdx, sourceEntryRsp);
        }

        @Override
        public void insertSlotC3cf10(Memory memory, long siteRva, long bucket, int probe, int hash, long descriptor) {
            fallback.insertSlotC3cf10(memory, siteRva, bucket, probe, hash, descriptor);
        }

        @Override
        public void rehashC3a400(Memory memory, long siteRva, long map) {
            fallback.rehashC3a400(memory, siteRva, map);
        }

        @Override
        public void insertC3a5f0(Memory memory, long siteRva, long map, long result, int hash, long descriptor) {
            if (memory != sharedMemory) {
                throw new IllegalArgumentException("Foreign Memory");
            }
            if (siteRva != 0xC3BBC1L) {
                throw new IllegalArgumentException("Foreign site");
            }
            // Derive wrapperBodyRsp from actual resultRDX per CONTRACT194
            // resultRDX = currentBody + 0x30 => currentBody = result - 0x30
            // wrapperBody = currentBody - 0x40 = result - 0x70
            long wrapperBodyRsp = result - 0x70L;
            OtherInsertC3A5F0.execute(moduleBase, map, result, hash, descriptor, wrapperBodyRsp, memory, this);
        }

        @Override
        public void destroy856050(Memory memory, long siteRva, long descriptor) {
            fallback.destroy856050(memory, siteRva, descriptor);
        }

        @Override
        public int capacity86e160(Memory memory, long siteRva, int ecx, int edx) {
            return fallback.capacity86e160(memory, siteRva, ecx, edx);
        }

        @Override
        public void reserveC3b700(Memory memory, long siteRva, long map, int edx) {
            fallback.reserveC3b700(memory, siteRva, map, edx);
        }

        @Override
        public void overflow86f210(Memory memory, long siteRva, long rcx, long rdx) {
            fallback.overflow86f210(memory, siteRva, rcx, rdx);
        }

        @Override
        public void terminal4232cf4(Memory memory, long siteRva) {
            fallback.terminal4232cf4(memory, siteRva);
        }
    }
}