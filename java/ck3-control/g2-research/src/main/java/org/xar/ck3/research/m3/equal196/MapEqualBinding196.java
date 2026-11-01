package org.xar.ck3.research.m3.equal196;

import org.xar.ck3.research.m3.map191.MapInsert191Api;
import org.xar.ck3.research.m3.RegistryConsumerApi176;
import org.xar.ck3.research.m3.GroupNameEqualApi185;
import org.xar.ck3.research.m3.GroupNameEqual185;

/**
 * Explicit normal storage/known-argument projection of complete C3B960;
 * not a CPU/ABI/EH emulator.
 */
public final class MapEqualBinding196 {
    private MapEqualBinding196() { }

    /**
     * Bytes16 read128 inherited only from 191; never extends 185.Memory with conflicting Vector128 return.
     */
    public interface Memory extends MapInsert191Api.Memory, RegistryConsumerApi176.Memory {
        int readUnsigned16(long address);
        void write16(long address, int value);
    }

    public static MapInsert191Api.Ports bind(long moduleBase, Memory sharedMemory, MapInsert191Api.Ports fallback) {
        return new BoundPorts(moduleBase, sharedMemory, fallback);
    }

    private static final class BoundPorts implements MapInsert191Api.Ports {
        private final long moduleBase;
        private final Memory sharedMemory;
        private final MapInsert191Api.Ports fallback;

        BoundPorts(long moduleBase, Memory sharedMemory, MapInsert191Api.Ports fallback) {
            this.moduleBase = moduleBase;
            this.sharedMemory = sharedMemory;
            this.fallback = fallback;
        }

        @Override
        public int equal3f6d2b0(MapInsert191Api.Memory memory, long siteRva, long rcx, long rdx) {
            return fallback.equal3f6d2b0(memory, siteRva, rcx, rdx);
        }

        @Override
        public int equal3f6d2b0(MapInsert191Api.Memory memory, long siteRva, long rcx, long rdx, long sourceEntryRsp) {
            if (memory != sharedMemory || siteRva != 0xC3B9CAL) {
                throw new IllegalArgumentException("UNWRITTEN_COMPAT196");
            }
            GroupNameEqualApi185.Memory view = new View185(sharedMemory);
            GroupNameEqualApi185.Scratch scratch = new GroupNameEqualApi185.Scratch(sourceEntryRsp);
            return GroupNameEqual185.equalAl(view, moduleBase, rcx, rdx, scratch);
        }

        @Override
        public void insertSlotC3cf10(MapInsert191Api.Memory memory, long siteRva, long bucket, int probe, int hash, long descriptor) {
            fallback.insertSlotC3cf10(memory, siteRva, bucket, probe, hash, descriptor);
        }

        @Override
        public void rehashC3a400(MapInsert191Api.Memory memory, long siteRva, long map) {
            fallback.rehashC3a400(memory, siteRva, map);
        }

        @Override
        public void rehashC3a400(MapInsert191Api.Memory memory, long siteRva, long map, long sourceEntryRsp) {
            fallback.rehashC3a400(memory, siteRva, map, sourceEntryRsp);
        }

        @Override
        public void insertC3a5f0(MapInsert191Api.Memory memory, long siteRva, long map, long result, int hash, long descriptor) {
            fallback.insertC3a5f0(memory, siteRva, map, result, hash, descriptor);
        }

        @Override
        public void destroy856050(MapInsert191Api.Memory memory, long siteRva, long descriptor) {
            fallback.destroy856050(memory, siteRva, descriptor);
        }

        @Override
        public int capacity86e160(MapInsert191Api.Memory memory, long siteRva, int ecx, int edx) {
            return fallback.capacity86e160(memory, siteRva, ecx, edx);
        }

        @Override
        public void reserveC3b700(MapInsert191Api.Memory memory, long siteRva, long map, int edx) {
            fallback.reserveC3b700(memory, siteRva, map, edx);
        }

        @Override
        public void reserveC3b700(MapInsert191Api.Memory memory, long siteRva, long map, int edx, long sourceEntryRsp) {
            fallback.reserveC3b700(memory, siteRva, map, edx, sourceEntryRsp);
        }

        @Override
        public void overflow86f210(MapInsert191Api.Memory memory, long siteRva, long rcx, long rdx) {
            fallback.overflow86f210(memory, siteRva, rcx, rdx);
        }

        @Override
        public void terminal4232cf4(MapInsert191Api.Memory memory, long siteRva) {
            fallback.terminal4232cf4(memory, siteRva);
        }

        @Override
        public void terminal4232cf4(MapInsert191Api.Memory memory, long siteRva, long terminalEntryRsp) {
            fallback.terminal4232cf4(memory, siteRva, terminalEntryRsp);
        }
    }

    private static final class View185 implements GroupNameEqualApi185.Memory {
        private final Memory backing;

        View185(Memory backing) {
            this.backing = backing;
        }

        @Override
        public int readUnsigned8(long address) {
            return backing.readUnsigned8(address);
        }

        @Override
        public void write8(long address, int value) {
            backing.write8(address, value);
        }

        @Override
        public int readUnsigned16(long address) {
            return backing.readUnsigned16(address);
        }

        @Override
        public void write16(long address, int value) {
            backing.write16(address, value);
        }

        @Override
        public GroupNameEqualApi185.Vector128 read128(long address) {
            MapInsert191Api.Bytes16 bytes = backing.read128(address);
            return new GroupNameEqualApi185.Vector128(bytes.low(), bytes.high());
        }

        @Override
        public long readPointer(long address) {
            return backing.readPointer(address);
        }

        @Override
        public int readInt32(long address) {
            return backing.readInt32(address);
        }

        @Override
        public void writeInt32(long address, int value) {
            backing.writeInt32(address, value);
        }

        @Override
        public void writeInt64(long address, long value) {
            backing.writeInt64(address, value);
        }
    }
}
