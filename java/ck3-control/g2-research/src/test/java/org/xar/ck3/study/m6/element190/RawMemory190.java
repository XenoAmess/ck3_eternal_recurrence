package org.xar.ck3.study.m6.element190;

import java.util.HashMap;
import java.util.Map;

public class RawMemory190 implements org.xar.ck3.study.m6.element172.Element172Inputs.Memory,
        org.xar.ck3.study.m6.element150.Element150Inputs.Memory {
    public record Access(String operation,long address,int bytes,long bits) { }
    private final Map<Long,Integer> memory=new HashMap<>();
    protected void observed(Access access) { }
    public final void fill(long address,int count,int value) { for(int i=0;i<count;++i)put8(address+i,value); }
    public final void put8(long address,int value) { memory.put(address,value&255); }
    public final void put32(long address,int value) { for(int i=0;i<4;++i)put8(address+i,value >>> (i*8)); }
    public final void put64(long address,long value) { for(int i=0;i<8;++i)put8(address+i,(int)(value >>> (i*8))); }
    public final int peek8(long address) {
        Integer value=memory.get(address);if(value==null)throw new IllegalStateException("unseeded byte "+Long.toUnsignedString(address,16));return value;
    }
    public final long peek64(long address) { long v=0;for(int i=0;i<8;++i)v|=(long)peek8(address+i) << (i*8);return v; }
    public final int peek32(long address) { int v=0;for(int i=0;i<4;++i)v|=peek8(address+i) << (i*8);return v; }
    @Override public final int read32(long address) { int v=peek32(address);observed(new Access("r32",address,4,Integer.toUnsignedLong(v)));return v; }
    @Override public final long read64(long address) { long v=peek64(address);observed(new Access("r64",address,8,v));return v; }
    @Override public final int read8(long address) { int v=peek8(address);observed(new Access("r8",address,1,v));return v; }
    @Override public final void write32(long address,int value) { observed(new Access("w32",address,4,Integer.toUnsignedLong(value)));put32(address,value); }
    @Override public final void write64(long address,long value) { observed(new Access("w64",address,8,value));put64(address,value); }
    @Override public final void write8(long address,int value) { observed(new Access("w8",address,1,value&255));put8(address,value); }
}
