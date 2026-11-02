package org.xar.ck3.control.g2.common.nativecore.task.captured;

import static org.junit.jupiter.api.Assertions.*;
import java.io.ByteArrayInputStream;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;

/** One controlled whole199 nested rebuild. Original-ASM expectations, not a Java captured trace.
 * No Native CPU/allocator/EH/physical Game or natural M7 acceptance qualification. */
public final class LoadRowReferenceNestedProbe254Test {
    private static final String GOLDEN_WRITES="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";
    private static final String GOLDEN_OPAQUE="H4sIAAAAAAAC/32RWw6EIAxF/2ct/bgtD8tyFGH/SxhKEB9jhiYNBi/nhDq3ZJZCCWAQQ0oCiZKiLcoK0nFm5XlBPwC56nNbO+GnBBT6X9z7Rm5kRn3cE7rHdncaUI77SeUR9Vz1IJfk1yDphexB8ULW9hXW1iuZkm0nvmQjyMQr90TPxZmORZu93SxLnvwWU+EXvgXuCiaAU8MeOP91sfe/uoThEhC9ktSni5O8ydsUAkTvg5Dej2EM/y9YRjtxAQIAAA==";
    private static final String GOLDEN_FLOAT="H4sIAAAAAAAC/43VzXKEIAwH8Ps+jSSoeOxsX4SN8dRTP248fKNhiTuUoqc/4vyGmMxwT5S888P+3O5pk8Wsi/fyvrxLuHmSZ729lbgH3fz+/GEh3G5sIYNO9sMTfMbyQcJ18OCGsIM5GrjFj69ahKTbesQcz2IwMVwSURhvoq9EmtAFOkSNPdELE0ysqmarmq9VPQoTTYyVCCMsPh6ixp44CUMmUiX6UnWOPXEWhk3kSpxmXIgPUWNPDLKwXruq12y95mu9XmThTHSVKH9Oft8haqxFFBFm+n/C8wcJKcAQwO1ijj2xMeFFXIci5tgTGxNuoseBUEWNPbEx4SZa1eu1qhsTbmKEELUzOfbExoSbSFY1Xaq6MeEmMgZGPaPGntiY8CKy9Zqv9box4SY68AuMh6ixJ0ZhwESoRCidybEnPoRBE7ESEegBxzWTYy2+3Ftn/nxxmWgTzn9O+C8k0sYfCQcAAA==";
    private static final String FINAL_V="20000,0,20000,8,30000,2f,0,427c0000,0,3e430c31,0,0,0,0,0,0,0,0,0";

    @Test
    public void whole199CompletesSecondC7cfNested64AndDeferredEntry() throws Exception {
        List<Region> initial=initial();
        List<Region> expected=new ArrayList<>();
        for(Region r:initial) expected.add(new Region(r.base,r.bytes));
        List<String> goldenWrites=lines(GOLDEN_WRITES);
        for(String line:goldenWrites) {
            String[] cells=line.split("\\|",-1);
            patch(expected,Long.parseUnsignedLong(cells[1],16),HexFormat.of().parseHex(cells[2]));
        }
        Mem memory=new Mem(initial);
        List<GovernmentCrtBoundary185Api.Call> goldenCalls=new ArrayList<>();
        for(String line:lines(GOLDEN_OPAQUE)) goldenCalls.add(parseCall(line));
        int[] callCursor={0},gsCount={0},budgetSteps={0};
        List<String> actualFloat=new ArrayList<>();
        GovernmentCrtBoundary185Api.Calls external=new GovernmentCrtBoundary185Api.Calls() {
            @Override public VolatileBits invoke(GovernmentCrtBoundary185Api.Call c) {
                assertTrue(callCursor[0]<goldenCalls.size(),"unexpected external call");
                assertEquals(goldenCalls.get(callCursor[0]),c,"full source-derived opaque Call");
                assertEquals(c.callSiteRva()+3,memory.readQword(c.rspBits()-8));
                int index=callCursor[0]++;
                long result=c.targetBits()==0x90010L?(index==0?0x60000L:0x70000L):0xf1f2f3f4L;
                return withRax(c.volatileBits(),result);
            }
            @Override public GovernmentCrtBoundary185Api.NormalReturn tail(GovernmentCrtBoundary185Api.Tail t) {
                throw new AssertionError("known Tail must remain in actual mature246 graph: "+t);
            }
            @Override public long readGsQword58() { gsCount[0]++; return 0xa0000L; }
        };
        var floating=new LoadRowReferenceCallee337b7e0199Api.Float32() {
            @Override public int convertSignedDwordToFloatBits(int input) {
                int value=Float.floatToRawIntBits((float)input);
                actualFloat.add("C|"+Integer.toHexString(input)+"|"+Integer.toHexString(value));return value;
            }
            @Override public int divideScalarFloatBits(int a,int b) {
                int value=Float.floatToRawIntBits(Float.intBitsToFloat(a)/Float.intBitsToFloat(b));
                actualFloat.add("D|"+Integer.toHexString(a)+"|"+Integer.toHexString(b)+"|"+Integer.toHexString(value));return value;
            }
            @Override public boolean orderedAbove(int a,int b) {
                float x=Float.intBitsToFloat(a),y=Float.intBitsToFloat(b);
                boolean above=!Float.isNaN(x)&&!Float.isNaN(y)&&x>y;
                actualFloat.add("A|"+Integer.toHexString(a)+"|"+Integer.toHexString(b)+"|"+above);return above;
            }
        };
        GovernmentCrtBoundary185Api.LoopBudget budget=(pc,address)-> {
            assertTrue(++budgetSteps[0]<=2000,"finite controlled source loop bound");
            memory.readBytes(address,1); // owned guard address, no fabricated loop memory
        };
        var initialV=new VolatileBits(0,0x10000L,0x20000L,8,0x30000L,0,0,Z,Z,Z,Z,Z,Z);
        var initialNV=new NonvolatileBits(0,0,0,0,0,0,0,0,Z);
        var entry=new GovernmentCrtBoundary185Api.Entry(0,0x103008L,initialV,initialNV);
        var graph=LoadRowReferenceMigration246Calls.bind(0,memory,external,budget,floating);
        memory.startRecording();
        var result=LoadRowReferenceCallee337b7e0199.execute(entry,memory,graph,budget,floating);

        assertEquals(parseV(FINAL_V.split(","),0),result.volatileBits());
        assertEquals(initialNV,result.nonvolatileBits());
        assertEquals(0xdeadbeef0000L,result.returnRipBits());assertEquals(0x103010L,result.callerRspBits());
        assertEquals(4,callCursor[0]);assertEquals(4,gsCount[0]);assertTrue(budgetSteps[0]>0);
        assertEquals(lines(GOLDEN_FLOAT),actualFloat,"all88 explicit finite FP port outcomes");
        List<String> actualWrites=new ArrayList<>();
        for(Mem.AccessEvent event:memory.getEvents()) {
            int width=switch(event.operation()) {case 2->8;case 4->4;case 6->1;case 8->16;default->0;};
            if(width!=0)actualWrites.add(width+"|"+Long.toHexString(event.address())+"|"+event.valueHex());
        }
        assertEquals(694,goldenWrites.size());assertEquals(goldenWrites,actualWrites,"entire source-derived ordered RAM-write trace");
        for(Region r:expected)assertArrayEquals(r.bytes,memory.readBytes(r.base,r.bytes.length),"all owned bytes including retired arrays/padding/stack "+Long.toHexString(r.base));
        assertEquals(0x70000L,memory.readQword(0x10008L));assertEquals(12,memory.readDword(0x10010L));
        assertEquals(63,memory.readDword(0x10014L));assertEquals(8,memory.readUnsignedByte(0x10018L));
    }

    private static final Bits128 Z=new Bits128(0,0);
    private static VolatileBits withRax(VolatileBits v,long value) {
        return new VolatileBits(value,v.rcxBits(),v.rdxBits(),v.r8Bits(),v.r9Bits(),v.r10Bits(),v.r11Bits(),v.xmm0(),v.xmm1(),v.xmm2(),v.xmm3(),v.xmm4(),v.xmm5());
    }
    private static long h(String x) { return Long.parseUnsignedLong(x,16); }
    private static VolatileBits parseV(String[] a,int i) {
        return new VolatileBits(h(a[i]),h(a[i+1]),h(a[i+2]),h(a[i+3]),h(a[i+4]),h(a[i+5]),h(a[i+6]),
            new Bits128(h(a[i+7]),h(a[i+8])),new Bits128(h(a[i+9]),h(a[i+10])),new Bits128(h(a[i+11]),h(a[i+12])),
            new Bits128(h(a[i+13]),h(a[i+14])),new Bits128(h(a[i+15]),h(a[i+16])),new Bits128(h(a[i+17]),h(a[i+18])));
    }
    private static GovernmentCrtBoundary185Api.Call parseCall(String line) {
        String[] a=line.split(",");int n=22;
        var nv=new NonvolatileBits(h(a[n]),h(a[n+1]),h(a[n+2]),h(a[n+3]),h(a[n+4]),h(a[n+5]),h(a[n+6]),h(a[n+7]),new Bits128(h(a[n+8]),h(a[n+9])));
        return new GovernmentCrtBoundary185Api.Call(h(a[0]),GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,h(a[1]),h(a[2]),parseV(a,3),nv);
    }
    private static List<String> lines(String compressed) throws Exception {
        try(var stream=new GZIPInputStream(new ByteArrayInputStream(Base64.getDecoder().decode(compressed)))) {
            return new String(stream.readAllBytes(),StandardCharsets.UTF_8).lines().toList();
        }
    }
    private static final class Region {
        final long base;final byte[] bytes;
        Region(long base,byte[] bytes) {this.base=base;this.bytes=bytes.clone();}
    }
    private static void patch(List<Region> regions,long address,byte[] bytes) {
        for(Region r:regions)if(r.base<=address&&address+bytes.length<=r.base+r.bytes.length) {
            System.arraycopy(bytes,0,r.bytes,(int)(address-r.base),bytes.length);return;
        }
        throw new AssertionError("unowned expected patch");
    }
    private static void seed(List<Region> regions,long at,int width,long value) {
        byte[] bytes=ByteBuffer.allocate(8).order(ByteOrder.LITTLE_ENDIAN).putLong(value).array();
        patch(regions,at,Arrays.copyOf(bytes,width));
    }
    private static List<Region> initial() {
        List<Region> r=new ArrayList<>();
        {byte[] a=new byte[64];Arrays.fill(a,(byte)0xcd);r.add(new Region(0x10000L,a));}
        {byte[] a=new byte[16];Arrays.fill(a,(byte)0xcd);r.add(new Region(0x20000L,a));}
        {byte[] a=new byte[80];Arrays.fill(a,(byte)0xcd);r.add(new Region(0x30000L,a));}
        {byte[] a=new byte[64];Arrays.fill(a,(byte)0xcd);r.add(new Region(0x40000L,a));}
        {byte[] a=new byte[1840];Arrays.fill(a,(byte)0xcd);r.add(new Region(0x50000L,a));}
        {byte[] a=new byte[3200];Arrays.fill(a,(byte)0xcd);r.add(new Region(0x60000L,a));}
        {byte[] a=new byte[5840];Arrays.fill(a,(byte)0xcd);r.add(new Region(0x70000L,a));}
        {byte[] a=new byte[32];Arrays.fill(a,(byte)0xcd);r.add(new Region(0x80000L,a));}
        {byte[] a=new byte[24];Arrays.fill(a,(byte)0xcd);r.add(new Region(0x81000L,a));}
        {byte[] a=new byte[8];Arrays.fill(a,(byte)0xcd);r.add(new Region(0xa0000L,a));}
        {byte[] a=new byte[20];Arrays.fill(a,(byte)0xcd);r.add(new Region(0xa1000L,a));}
        {byte[] a=new byte[112];Arrays.fill(a,(byte)0xcd);r.add(new Region(0x5c673d0L,a));}
        {byte[] a=new byte[16384];Arrays.fill(a,(byte)0xcd);r.add(new Region(0x100000L,a));}
        seed(r,0x103008L,8,0xdeadbeef0000L);
        seed(r,0x103038L,8,0x40000L);
        seed(r,0x10008L,8,0x50000L);
        seed(r,0x10020L,8,0x80000L);
        seed(r,0x80000L,8,0x81000L);
        seed(r,0x81008L,8,0x90010L);
        seed(r,0x81010L,8,0x90020L);
        seed(r,0xa0000L,8,0xa1000L);
        seed(r,0x30000L,8,0xabcd0008L);
        seed(r,0x30040L,8,0x0L);
        seed(r,0x40038L,8,0x0L);
        seed(r,0x10010L,4,0xbL);
        seed(r,0x10014L,4,0xfL);
        seed(r,0x1001cL,4,0x3f400000L);
        seed(r,0xa1010L,4,0x0L);
        seed(r,0x5c673d0L,4,0x0L);
        seed(r,0x10018L,1,0x6L);
        for(int i=0;i<22;i++)seed(r,0x50000L+i*80L+4,1,0);
        seed(r,0x50000L+22*80L+4,1,255);
        seed(r,0x50000L,4,0x10L);
        seed(r,0x50004L,1,0x1L);
        seed(r,0x50008L,8,0xabcd0010L);
        seed(r,0x50048L,8,0x0L);
        seed(r,0x50050L,4,0x30L);
        seed(r,0x50054L,1,0x2L);
        seed(r,0x50058L,8,0xabcd0030L);
        seed(r,0x50098L,8,0x0L);
        seed(r,0x500a0L,4,0x50L);
        seed(r,0x500a4L,1,0x3L);
        seed(r,0x500a8L,8,0xabcd0050L);
        seed(r,0x500e8L,8,0x0L);
        seed(r,0x500f0L,4,0x70L);
        seed(r,0x500f4L,1,0x4L);
        seed(r,0x500f8L,8,0xabcd0070L);
        seed(r,0x50138L,8,0x0L);
        seed(r,0x50140L,4,0x90L);
        seed(r,0x50144L,1,0x5L);
        seed(r,0x50148L,8,0xabcd0090L);
        seed(r,0x50188L,8,0x0L);
        seed(r,0x504b0L,4,0xfL);
        seed(r,0x504b4L,1,0x1L);
        seed(r,0x504b8L,8,0xabcd000fL);
        seed(r,0x504f8L,8,0x0L);
        seed(r,0x50500L,4,0x2fL);
        seed(r,0x50504L,1,0x2L);
        seed(r,0x50508L,8,0xabcd002fL);
        seed(r,0x50548L,8,0x0L);
        seed(r,0x50550L,4,0x4fL);
        seed(r,0x50554L,1,0x3L);
        seed(r,0x50558L,8,0xabcd004fL);
        seed(r,0x50598L,8,0x0L);
        seed(r,0x505a0L,4,0x6fL);
        seed(r,0x505a4L,1,0x4L);
        seed(r,0x505a8L,8,0xabcd006fL);
        seed(r,0x505e8L,8,0x0L);
        seed(r,0x505f0L,4,0x8fL);
        seed(r,0x505f4L,1,0x5L);
        seed(r,0x505f8L,8,0xabcd008fL);
        seed(r,0x50638L,8,0x0L);
        seed(r,0x50640L,4,0xafL);
        seed(r,0x50644L,1,0x6L);
        seed(r,0x50648L,8,0xabcd00afL);
        seed(r,0x50688L,8,0x0L);
        return r;
    }


private static final class Mem implements GovernmentCrtBoundary185Api.Memory {
    private static final int OP_READ_QWORD = 1;
    private static final int OP_WRITE_QWORD = 2;
    private static final int OP_READ_DWORD = 3;
    private static final int OP_WRITE_DWORD = 4;
    private static final int OP_READ_BYTE = 5;
    private static final int OP_WRITE_BYTE = 6;
    private static final int OP_READ_128 = 7;
    private static final int OP_WRITE_128 = 8;

    private final java.util.List<java.util.AbstractMap.SimpleEntry<Long, byte[]>> regions;
    private boolean recording = false;
    private final java.util.List<AccessEvent> events = new java.util.ArrayList<>();

    Mem(java.util.List<Region> initialRegions) {
        this.regions = new java.util.ArrayList<>();
        for (Region e : initialRegions) {
            long base = e.base;
            byte[] bytes = e.bytes;
            if (bytes == null) throw new IllegalArgumentException("Null region bytes");
            if (base < 0) throw new IllegalArgumentException("Negative base");
            if (bytes.length == 0) throw new IllegalArgumentException("Empty region");
            if (base + bytes.length < base) throw new IllegalArgumentException("Wraparound");
            this.regions.add(new java.util.AbstractMap.SimpleEntry<>(base, bytes.clone()));
        }
        // Sort by base for deterministic overlap check
        this.regions.sort(java.util.Comparator.comparing(e -> e.getKey()));
        for (int i = 0; i < this.regions.size() - 1; i++) {
            long b1 = this.regions.get(i).getKey();
            int l1 = this.regions.get(i).getValue().length;
            long b2 = this.regions.get(i + 1).getKey();
            if (b1 + l1 > b2) throw new IllegalArgumentException("Overlap");
        }
    }

    public void startRecording() {
        this.recording = true;
    }

    public java.util.List<AccessEvent> getEvents() {
        return java.util.Collections.unmodifiableList(new java.util.ArrayList<>(this.events));
    }

    private void record(int op, long address, byte[] valueBytes) {
        if (this.recording) {
            this.events.add(new AccessEvent(op, address, java.util.HexFormat.of().formatHex(valueBytes)));
        }
    }

    private byte[] readBytes(long address, int length) {
        if (address < 0) throw new IllegalArgumentException("Negative address");
        if (address + length < address) throw new IllegalArgumentException("Wraparound");
        for (java.util.AbstractMap.SimpleEntry<Long, byte[]> e : this.regions) {
            long base = e.getKey();
            byte[] bytes = e.getValue();
            if (address >= base && address + length <= base + bytes.length) {
                return java.util.Arrays.copyOfRange(bytes, (int)(address - base), (int)(address - base + length));
            }
        }
        throw new UnsupportedOperationException("Unowned or crossing access");
    }

    private void writeBytes(long address, byte[] value) {
        if (address < 0) throw new IllegalArgumentException("Negative address");
        if (address + value.length < address) throw new IllegalArgumentException("Wraparound");
        for (java.util.AbstractMap.SimpleEntry<Long, byte[]> e : this.regions) {
            long base = e.getKey();
            byte[] bytes = e.getValue();
            if (address >= base && address + value.length <= base + bytes.length) {
                System.arraycopy(value, 0, bytes, (int)(address - base), value.length);
                return;
            }
        }
        throw new UnsupportedOperationException("Unowned or crossing access");
    }

    @Override
    public long readQword(long addressBits) {
        byte[] b = readBytes(addressBits, 8);
        long v = 0;
        for (int i = 7; i >= 0; i--) {
            v = (v << 8) | (b[i] & 0xFFL);
        }
        if (this.recording) record(OP_READ_QWORD, addressBits, b);
        return v;
    }

    @Override
    public void writeQword(long addressBits, long valueBits) {
        byte[] b = new byte[8];
        for (int i = 0; i < 8; i++) {
            b[i] = (byte)((valueBits >> (i * 8)) & 0xFF);
        }
        writeBytes(addressBits, b);
        if (this.recording) record(OP_WRITE_QWORD, addressBits, b);
    }

    @Override
    public int readDword(long addressBits) {
        byte[] b = readBytes(addressBits, 4);
        int v = 0;
        for (int i = 3; i >= 0; i--) {
            v = (v << 8) | (b[i] & 0xFF);
        }
        if (this.recording) record(OP_READ_DWORD, addressBits, b);
        return v;
    }

    @Override
    public void writeDword(long addressBits, int valueBits) {
        byte[] b = new byte[4];
        for (int i = 0; i < 4; i++) {
            b[i] = (byte)((valueBits >> (i * 8)) & 0xFF);
        }
        writeBytes(addressBits, b);
        if (this.recording) record(OP_WRITE_DWORD, addressBits, b);
    }

    @Override
    public int readUnsignedByte(long addressBits) {
        byte[] b = readBytes(addressBits, 1);
        if (this.recording) record(OP_READ_BYTE, addressBits, b);
        return b[0] & 0xFF;
    }

    @Override
    public void writeByte(long addressBits, int lowByteBits) {
        byte[] b = new byte[1];
        b[0] = (byte)(lowByteBits & 0xFF);
        writeBytes(addressBits, b);
        if (this.recording) record(OP_WRITE_BYTE, addressBits, b);
    }

    @Override
    public GovernmentPrimaryTail155Api.Bits128 read128(long addressBits) {
        byte[] b = readBytes(addressBits, 16);
        long low = 0;
        for (int i = 7; i >= 0; i--) {
            low = (low << 8) | (b[i] & 0xFFL);
        }
        long high = 0;
        for (int i = 15; i >= 8; i--) {
            high = (high << 8) | (b[i] & 0xFFL);
        }
        if (this.recording) record(OP_READ_128, addressBits, b);
        return new GovernmentPrimaryTail155Api.Bits128(low, high);
    }

    @Override
    public void write128(long addressBits, GovernmentPrimaryTail155Api.Bits128 valueBits) {
        byte[] b = new byte[16];
        long low = valueBits.lowBits();
        long high = valueBits.highBits();
        for (int i = 0; i < 8; i++) {
            b[i] = (byte)((low >> (i * 8)) & 0xFF);
        }
        for (int i = 0; i < 8; i++) {
            b[8 + i] = (byte)((high >> (i * 8)) & 0xFF);
        }
        writeBytes(addressBits, b);
        if (this.recording) record(OP_WRITE_128, addressBits, b);
    }

    @Override
    public int lockedXaddDword(long addressBits, int addendBits) {
        throw new UnsupportedOperationException("Atomic xadd not supported");
    }

    private record AccessEvent(int operation, long address, String valueHex) { }
}
}
