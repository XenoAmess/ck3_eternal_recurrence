package org.xar.ck3.research.m1;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.research.m1.GovernmentSharedComposition168Fixture.MemoryImage;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Call;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Calls;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Entry;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Tail;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.TargetKind;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import static org.xar.ck3.research.m1.GovernmentSharedComposition168Fixture.bits;
import static org.xar.ck3.research.m1.GovernmentSharedComposition168Fixture.vector;

/** Independent source-only literals for new full-state protocols, not another arithmetic oracle. */
public final class GovernmentIndexedTails198Witness {
    private static final long B=0x140000000L;
    private static int assertions;
    private GovernmentIndexedTails198Witness() { }
    private static void equal(Object expected,Object actual,String what) {
        assertions++;
        if (!Objects.equals(expected,actual)) throw new AssertionError(what+" expected="+expected+" actual="+actual);
    }
    private static void same(Object expected,Object actual,String what) {
        assertions++;
        if (expected!=actual) throw new AssertionError(what+" identity changed");
    }
    private static NonvolatileBits n(long seed) {
        return new NonvolatileBits(seed+1,seed+2,seed+3,seed+4,seed+5,seed+6,seed+7,seed+8,vector(seed+9));
    }
    private static VolatileBits tailV(VolatileBits in,long literalRcx) {
        return new VolatileBits(0x145C5D330L,literalRcx,in.rdxBits(),in.r8Bits(),in.r9Bits(),
                in.r10Bits(),in.r11Bits(),in.xmm0(),in.xmm1(),in.xmm2(),in.xmm3(),in.xmm4(),in.xmm5());
    }
    private record Access(String operation,long address,long value) { }
    /** Exactly the nine185.Memory methods. All storage remains in the existing byte fixture. */
    private static final class ObservedMemory implements GovernmentCrtBoundary185Api.Memory {
        private final MemoryImage bytes;
        private final List<Access> accesses=new ArrayList<>();
        private ObservedMemory(MemoryImage bytes) { this.bytes=bytes; }
        @Override public int readDword(long address) {
            accesses.add(new Access("readDword",address,0));return bytes.readDword(address);
        }
        @Override public long readQword(long address) {
            accesses.add(new Access("readQword",address,0));return bytes.readQword(address);
        }
        @Override public int readUnsignedByte(long address) {
            accesses.add(new Access("readUnsignedByte",address,0));return bytes.readUnsignedByte(address);
        }
        @Override public void writeDword(long address,int value) {
            accesses.add(new Access("writeDword",address,value));bytes.writeDword(address,value);
        }
        @Override public int lockedXaddDword(long address,int addend) {
            accesses.add(new Access("lockedXaddDword",address,addend));return bytes.lockedXaddDword(address,addend);
        }
        @Override public void writeQword(long address,long value) {
            accesses.add(new Access("writeQword",address,value));bytes.writeQword(address,value);
        }
        @Override public void writeByte(long address,int value) {
            accesses.add(new Access("writeByte",address,value));bytes.writeByte(address,value);
        }
        @Override public Bits128 read128(long address) {
            accesses.add(new Access("read128",address,0));return bytes.read128(address);
        }
        @Override public void write128(long address,Bits128 value) {
            accesses.add(new Access("write128",address,0));bytes.write128(address,value);
        }
    }
    private static void rawFirstSignedThree() {
        MemoryImage bytes=new MemoryImage();ObservedMemory memory=new ObservedMemory(bytes);
        VolatileBits in=bits(0x1100,0x1111222233334444L,0x7654321000000003L,0x2222333344445555L);
        NonvolatileBits incoming=n(0x1000000000000000L);
        Entry entry=new Entry(B,0x71000008L,in,incoming);
        VolatileBits post=bits(0x2200,0x9999AAAABBBBCCCCL,0x88889999AAAABBBBL,0x777788889999AAAAL);
        NormalReturn arbitrary=new NormalReturn(post,0xFEDCBA9876543210L,0x8011223344556677L,n(0x9000000000000000L));
        bytes.writeQword(0x1443DA500L,0xFFFF111122223333L);
        int[] tails={0};
        Calls fallback=new Calls() {
            @Override public VolatileBits invoke(Call call) { throw new AssertionError("raw tail became CALL"); }
            @Override public long readGsQword58() { throw new AssertionError("raw tail read GS"); }
            @Override public NormalReturn tail(Tail transfer) {
                equal(0,tails[0]++,"one first raw tail");
                equal(new Tail(0x424800EL,TargetKind.INDIRECT_ABSOLUTE,0xFFFF111122223333L,
                        new Entry(B,0x71000008L,tailV(in,0x145C5D3A8L),incoming)),transfer,"first signed3 complete tail");
                equal(List.of(new Access("readQword",0x1443DA500L,0)),memory.accesses,"only first IAT read; stack/table unseeded");
                return arbitrary;
            }
        };
        NormalReturn actual=GovernmentIndexedTails198.tail4247ffc(entry,memory,fallback);
        same(arbitrary,actual,"raw first complete arbitrary return");
        equal(1,tails[0],"first raw tail count");
        equal(List.of(new Access("readQword",0x1443DA500L,0)),memory.accesses,"first raw no later memory effect");
    }
    private static void rawSecondSignedMinusTwo() {
        MemoryImage bytes=new MemoryImage();ObservedMemory memory=new ObservedMemory(bytes);
        VolatileBits in=bits(0x3300,0x5555666677778888L,0x76543210FFFFFFFEL,0x6666777788889999L);
        NonvolatileBits incoming=n(0x2000000000000000L);
        Entry entry=new Entry(B,0x72000008L,in,incoming);
        NormalReturn arbitrary=new NormalReturn(bits(0x4400,0x1011121314151617L,0x2021222324252627L,
                0x3031323334353637L),0x89ABCDEF01234567L,0x9988776655443322L,n(0xA000000000000000L));
        bytes.writeQword(0x1443DA4F0L,0xEEEE444455556666L);
        int[] tails={0};
        Calls fallback=new Calls() {
            @Override public VolatileBits invoke(Call call) { throw new AssertionError("raw second tail became CALL"); }
            @Override public long readGsQword58() { throw new AssertionError("raw second tail read GS"); }
            @Override public NormalReturn tail(Tail transfer) {
                equal(0,tails[0]++,"one second raw tail");
                equal(new Tail(0x4248062L,TargetKind.INDIRECT_ABSOLUTE,0xEEEE444455556666L,
                        new Entry(B,0x72000008L,tailV(in,0x145C5D2E0L),incoming)),transfer,"second signed-2 complete tail/live RBX");
                equal(List.of(new Access("readQword",0x1443DA4F0L,0)),memory.accesses,"only second IAT read; stack/table unseeded");
                return arbitrary;
            }
        };
        same(arbitrary,GovernmentIndexedTails198.tail4248050(entry,memory,fallback),"raw second complete arbitrary return");
        equal(1,tails[0],"second raw tail count");
        equal(List.of(new Access("readQword",0x1443DA4F0L,0)),memory.accesses,"second raw no later memory effect");
    }
    private static void binderFirstAlreadyPushed() {
        MemoryImage bytes=new MemoryImage();ObservedMemory memory=new ObservedMemory(bytes);
        VolatileBits in=bits(0x5500,0x1111333355557777L,0xAABBCCDD00000003L,0x2222444466668888L);
        NonvolatileBits incoming=n(0x3000000000000000L);
        VolatileBits post=bits(0x6600,0x123456789ABCDEF0L,0x23456789ABCDEF01L,0x3456789ABCDEF012L);
        Call call=new Call(0x424DB4FL,TargetKind.DIRECT_RVA,0x4247FFCL,0x73000100L,in,incoming);
        bytes.writeQword(0x1443DA500L,0x1111000011110000L);
        int[] tails={0};
        Calls fallback=new Calls() {
            @Override public VolatileBits invoke(Call actual) { throw new AssertionError("first bound pair not consumed"); }
            @Override public long readGsQword58() { throw new AssertionError("first bound pair read GS"); }
            @Override public NormalReturn tail(Tail transfer) {
                equal(0,tails[0]++,"one first bound tail");
                equal(new Tail(0x424800EL,TargetKind.INDIRECT_ABSOLUTE,0xDDDD111122223333L,
                        new Entry(B,0x730000F8L,tailV(in,0x145C5D3A8L),incoming)),transfer,"first bound dynamic target/actual childSP");
                equal(List.of(new Access("writeQword",0x730000F8L,0x14424DB54L),
                        new Access("readQword",0x1443DA500L,0)),memory.accesses,"source push once; no qualification stack read");
                long actualRip=memory.readQword(0x730000F8L);
                equal(0x14424DB54L,actualRip,"actual first source CALL return");
                return new NormalReturn(post,actualRip,0x73000100L,incoming);
            }
        };
        Calls bound=GovernmentIndexedTails198.bind(B,memory,fallback);
        equal(List.of(),memory.accesses,"bind first performs no qualification pre-read");
        bytes.writeQword(0x1443DA500L,0xDDDD111122223333L);
        memory.writeQword(0x730000F8L,0x14424DB54L); // physical push by the source producer before invoke
        same(post,bound.invoke(call),"first binder actual fullV object");
        equal(1,tails[0],"first binder tail count");
        equal(List.of(new Access("writeQword",0x730000F8L,0x14424DB54L),
                new Access("readQword",0x1443DA500L,0),new Access("readQword",0x730000F8L,0)),
                memory.accesses,"first complete source write/IAT/fallbackRET read order");
    }
    private static void binderSecondAlreadyPushed() {
        MemoryImage bytes=new MemoryImage();ObservedMemory memory=new ObservedMemory(bytes);
        VolatileBits in=bits(0x7700,0xAAAABBBBCCCCDDDDL,0xAABBCCDDFFFFFFFEL,0xBBBBCCCCDDDDEEEEL);
        NonvolatileBits incoming=n(0x4000000000000000L);
        VolatileBits post=bits(0x8800,0x456789ABCDEF0123L,0x56789ABCDEF01234L,0x6789ABCDEF012345L);
        Call call=new Call(0x424DB61L,TargetKind.DIRECT_RVA,0x4248050L,0x74000100L,in,incoming);
        bytes.writeQword(0x1443DA4F0L,0x2222000022220000L);
        int[] tails={0};
        Calls fallback=new Calls() {
            @Override public VolatileBits invoke(Call actual) { throw new AssertionError("second bound pair not consumed"); }
            @Override public long readGsQword58() { throw new AssertionError("second bound pair read GS"); }
            @Override public NormalReturn tail(Tail transfer) {
                equal(0,tails[0]++,"one second bound tail");
                equal(new Tail(0x4248062L,TargetKind.INDIRECT_ABSOLUTE,0xCCCC444455556666L,
                        new Entry(B,0x740000F8L,tailV(in,0x145C5D2E0L),incoming)),transfer,"second bound dynamic target/actual childSP");
                equal(List.of(new Access("writeQword",0x740000F8L,0x14424DB66L),
                        new Access("readQword",0x1443DA4F0L,0)),memory.accesses,"second source push once; no qualification stack read");
                long actualRip=memory.readQword(0x740000F8L);
                equal(0x14424DB66L,actualRip,"actual second source CALL return");
                return new NormalReturn(post,actualRip,0x74000100L,incoming);
            }
        };
        Calls bound=GovernmentIndexedTails198.bind(B,memory,fallback);
        equal(List.of(),memory.accesses,"bind second performs no qualification pre-read");
        bytes.writeQword(0x1443DA4F0L,0xCCCC444455556666L);
        memory.writeQword(0x740000F8L,0x14424DB66L); // physical push by the source producer before invoke
        same(post,bound.invoke(call),"second binder actual fullV object");
        equal(1,tails[0],"second binder tail count");
        equal(List.of(new Access("writeQword",0x740000F8L,0x14424DB66L),
                new Access("readQword",0x1443DA4F0L,0),new Access("readQword",0x740000F8L,0)),
                memory.accesses,"second complete source write/IAT/fallbackRET read order");
    }
    private static void exactForeignTransparency() {
        MemoryImage bytes=new MemoryImage();ObservedMemory memory=new ObservedMemory(bytes);
        VolatileBits in=bits(0x9900,0x100000001L,0x200000002L,0x300000003L);
        NonvolatileBits incoming=n(0x5000000000000000L);
        VolatileBits post=bits(0xAA00,0x400000004L,0x500000005L,0x600000006L);
        Call[] foreign={new Call(0x424DB4FL,TargetKind.INDIRECT_ABSOLUTE,0x4247FFCL,0x75000100L,in,incoming),
                new Call(0x424DB50L,TargetKind.DIRECT_RVA,0x4247FFCL,0x75000100L,in,incoming),
                new Call(0x424DB4FL,TargetKind.DIRECT_RVA,0x4248050L,0x75000100L,in,incoming),
                new Call(0x424DB58L,TargetKind.DIRECT_RVA,0x424DBB0L,0x75000100L,in,incoming)};
        Tail foreignTail=new Tail(0x12345678L,TargetKind.INDIRECT_ABSOLUTE,0xF123456789ABCDEFL,
                new Entry(B,0x76000008L,in,incoming));
        NormalReturn postTail=new NormalReturn(post,0x9988AABBCCDDEEFFL,0x8877665544332211L,n(0x6000000000000000L));
        int[] invoked={0},tails={0},gs={0};
        Calls fallback=new Calls() {
            @Override public VolatileBits invoke(Call actual) {
                same(foreign[invoked[0]++],actual,"foreign kind/site/target/DBB0 original Call");return post;
            }
            @Override public NormalReturn tail(Tail actual) {
                tails[0]++;same(foreignTail,actual,"foreign Tail object");return postTail;
            }
            @Override public long readGsQword58() { gs[0]++;return 0xFEDCBA9876543210L; }
        };
        Calls bound=GovernmentIndexedTails198.bind(B,memory,fallback);
        for (Call call:foreign) same(post,bound.invoke(call),"foreign fullV object");
        same(postTail,bound.tail(foreignTail),"foreign complete NormalReturn object");
        equal(0xFEDCBA9876543210L,bound.readGsQword58(),"transparent GS bits");
        equal(4,invoked[0],"four foreign invokes");equal(1,tails[0],"one foreign tail");equal(1,gs[0],"one delegated GS");
        equal(List.of(),memory.accesses,"all foreign operations have no local memory access");
    }
    public static void main(String[] args) {
        rawFirstSignedThree();rawSecondSignedMinusTwo();binderFirstAlreadyPushed();binderSecondAlreadyPushed();
        exactForeignTransparency();
        System.out.println("{\"raw_paths\":2,\"binder_paths\":2,\"foreign_invokes\":4,\"foreign_tails\":1,\"delegated_GS\":1,\"assertions\":"
                +assertions+",\"old_endpoint_runs\":0,\"Native\":0,\"Game\":0}");
    }
}
