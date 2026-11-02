package org.xar.ck3.research.m4;

import org.xar.ck3.research.m5.GovernmentRoot178Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;

/** Test-only nominal view; all storage and tracing remain in the existing byte fixture. */
class RoleMemory284 implements GovernmentRoot178Api.Memory {
    final Gate47Fixture273.Memory backing = new Gate47Fixture273.Memory();
    @Override public int readUnsignedByte(long p) { return backing.readUnsignedByte(p); }
    @Override public int readDword(long p) { return backing.readDword(p); }
    @Override public long readQword(long p) { return backing.readQword(p); }
    @Override public Bits128 read128(long p) { return backing.read128(p); }
    @Override public void writeByte(long p,int v) { backing.writeByte(p,v); }
    @Override public void writeDword(long p,int v) { backing.writeDword(p,v); }
    @Override public void writeQword(long p,long v) { backing.writeQword(p,v); }
    @Override public void write128(long p,Bits128 v) { backing.write128(p,v); }
    @Override public int lockedXaddDword(long p,int v) { return backing.lockedXaddDword(p,v); }
}
