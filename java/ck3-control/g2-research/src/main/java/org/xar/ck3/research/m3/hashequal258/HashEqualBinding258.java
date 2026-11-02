package org.xar.ck3.research.m3.hashequal258;

import org.xar.ck3.research.m3.hash188.HashInsert188Api;
import org.xar.ck3.research.m3.GroupNameEqualApi185;
import org.xar.ck3.research.m3.GroupNameEqual185;

public final class HashEqualBinding258 {

    public interface Memory extends HashInsert188Api.Memory {
        int readUnsigned16(long address);
        void write16(long address, int value);
    }

    public static HashInsert188Api.Ports bind(long moduleBase, Memory memory, HashInsert188Api.Ports fallback) {
        if (memory == null) throw new NullPointerException("memory");
        if (fallback == null) throw new NullPointerException("fallback");

        return new HashInsert188Api.Ports() {
            @Override
            public int equal3f6d2b0(HashInsert188Api.Memory m, long siteRva, long rcx, long rdx) {
                return fallback.equal3f6d2b0(m, siteRva, rcx, rdx);
            }

            @Override
            public int equal3f6d2b0(HashInsert188Api.Memory m, long siteRva, long rcx, long rdx, long sourceEntryRsp) {
                if (siteRva == 0xC39CCAL && m == memory) {
                    return GroupNameEqual185.equalAl(
                        new View(memory),
                        moduleBase,
                        rcx,
                        rdx,
                        new GroupNameEqualApi185.Scratch(sourceEntryRsp)
                    );
                }
                return fallback.equal3f6d2b0(m, siteRva, rcx, rdx, sourceEntryRsp);
            }

            @Override
            public void copy855f00(HashInsert188Api.Memory m, long siteRva, long rcx, long rdx) {
                fallback.copy855f00(m, siteRva, rcx, rdx);
            }

            @Override
            public void assign855db0(HashInsert188Api.Memory m, long siteRva, long rcx, long rdx, long r8) {
                fallback.assign855db0(m, siteRva, rcx, rdx, r8);
            }

            @Override
            public void rehashC3a400(HashInsert188Api.Memory m, long siteRva, long map) {
                fallback.rehashC3a400(m, siteRva, map);
            }

            @Override
            public void insertC3b960(HashInsert188Api.Memory m, long siteRva, long map, long result, int hash, long descriptor) {
                fallback.insertC3b960(m, siteRva, map, result, hash, descriptor);
            }

            @Override
            public void destroy856050(HashInsert188Api.Memory m, long siteRva, long descriptor) {
                fallback.destroy856050(m, siteRva, descriptor);
            }

            @Override
            public int capacity86e160(HashInsert188Api.Memory m, long siteRva, int ecx, int edx) {
                return fallback.capacity86e160(m, siteRva, ecx, edx);
            }

            @Override
            public void reserveC3b700(HashInsert188Api.Memory m, long siteRva, long map, int edx) {
                fallback.reserveC3b700(m, siteRva, map, edx);
            }

            @Override
            public void overflow86f210(HashInsert188Api.Memory m, long siteRva, long rcx, long rdx) {
                fallback.overflow86f210(m, siteRva, rcx, rdx);
            }

            @Override
            public void terminal4232cf4(HashInsert188Api.Memory m, long siteRva) {
                fallback.terminal4232cf4(m, siteRva);
            }

            @Override
            public void terminal4232cf4(HashInsert188Api.Memory m, long siteRva, long terminalEntryRsp) {
                fallback.terminal4232cf4(m, siteRva, terminalEntryRsp);
            }
        };
    }

    private static final class View implements GroupNameEqualApi185.Memory {
        private final Memory backing;

        View(Memory backing) {
            this.backing = backing;
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
            HashInsert188Api.Bytes16 b = backing.read128(address);
            return new GroupNameEqualApi185.Vector128(b.low(), b.high());
        }
    }
}