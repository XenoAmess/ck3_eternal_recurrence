package org.xar.ck3.research.m1;

import java.util.ArrayList;
import java.util.List;
import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.OpaqueCall;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import static org.xar.ck3.research.m1.GovernmentSharedComposition168Fixture.bits;
import static org.xar.ck3.research.m1.GovernmentSharedComposition168Fixture.vector;

/** Independent literals from the original400B/table, frozen before any206 implementation visibility. */
public final class GovernmentMemoryFill206Witness {
    private GovernmentMemoryFill206Witness() { }
    private static final long B=0x100000000L, D=0x60001003L, S=0xC0000008L;
    private static final long RET=0x11223344778899AAL, REP=0xABABABABABABABABL, TABLE=0x60900B0L;
    private static final VolatileBits BASE=bits(0x1000L,0xAAAA000011112222L,D,0xFACE1234567890ABL);
    private static final NonvolatileBits N=new NonvolatileBits(
            0x2222000022220000L,0x2222000022220001L,0x2222000022220002L,0x2222000022220003L,
            0x2222000022220004L,0x2222000022220005L,0x2222000022220006L,0x2222000022220007L,
            vector(0x2222000022220008L));
    private static final Bits128 REPEATED=new Bits128(REP,REP), ZERO=new Bits128(0L,0L);
    private static final GovernmentCrtBoundary185Api.NormalReturn TAIL_RESULT=
            new GovernmentCrtBoundary185Api.NormalReturn(
                    bits(0xF000L,0x123456789ABCDEF0L,0x445566778899AABBL,0x66778899AABBCCDDL),
                    0x8877665544332211L,0x7766554433221100L,new NonvolatileBits(
                    0x4444000044440000L,0x4444000044440001L,0x4444000044440002L,0x4444000044440003L,
                    0x4444000044440004L,0x4444000044440005L,0x4444000044440006L,0x4444000044440007L,
                    vector(0x4444000044440008L)));
    private static int assertions, scenes, coreScenes, compositionScenes, budgetEffects;
    private static int ntEffects, fenceEffects, tails, opaquePorts, physicalPushes, fillBindings;

    private record Event(String kind,long address,long low,long high) { }
    private record Port(OpaqueCall call,VolatileBits post) { }
    private static Event e(String kind,long address,long low) { return new Event(kind,address,low,0L); }
    private static Event ev(String kind,long address,long low,long high) { return new Event(kind,address,low,high); }
    private static void equal(Object expected,Object actual,String label) {
        assertions++;
        GovernmentSharedComposition168Fixture.equal(expected,actual,label);
    }
    private static VolatileBits v(VolatileBits x,long ax,long cx,long dx,long r8,long r9,long r10,long r11,Bits128 x0) {
        return new VolatileBits(ax,cx,dx,r8,r9,r10,r11,x0,x.xmm1(),x.xmm2(),x.xmm3(),x.xmm4(),x.xmm5());
    }
    private static NonvolatileBits n(long bx,long bp,long si,long di) {
        return new NonvolatileBits(bx,bp,si,di,N.r12Bits(),N.r13Bits(),N.r14Bits(),N.r15Bits(),N.xmm6());
    }
    private static OpaqueCall oc(long site,long target,VolatileBits vv,NonvolatileBits nn) {
        return new OpaqueCall(site,target,S-0x28L,vv,nn);
    }
    private static final class Mem implements GovernmentMemoryFill206Api.Memory {
        final GovernmentSharedComposition168Fixture.MemoryImage raw=new GovernmentSharedComposition168Fixture.MemoryImage();
        final List<Event> events=new ArrayList<>();
        @Override public int readUnsignedByte(long a) { int value=raw.readUnsignedByte(a);events.add(e("R8",a,value));return value; }
        @Override public int readDword(long a) { int value=raw.readDword(a);events.add(e("R32",a,Integer.toUnsignedLong(value)));return value; }
        @Override public long readQword(long a) { long value=raw.readQword(a);events.add(e("R64",a,value));return value; }
        @Override public Bits128 read128(long a) { Bits128 value=raw.read128(a);events.add(ev("R128",a,value.lowBits(),value.highBits()));return value; }
        @Override public void writeByte(long a,int value) { events.add(e("W8",a,value&255));raw.writeByte(a,value); }
        @Override public void writeWord(long a,int value) {
            events.add(e("W16",a,value&65535));raw.writeByte(a,value);raw.writeByte(a+1,value>>>8);
        }
        @Override public void writeDword(long a,int value) { events.add(e("W32",a,Integer.toUnsignedLong(value)));raw.writeDword(a,value); }
        @Override public void writeQword(long a,long value) { events.add(e("W64",a,value));raw.writeQword(a,value); }
        @Override public void write128(long a,Bits128 value) { events.add(ev("W128",a,value.lowBits(),value.highBits()));raw.write128(a,value); }
        @Override public void write128NonTemporal(long a,Bits128 value) {
            events.add(ev("NT128",a,value.lowBits(),value.highBits()));ntEffects++;raw.write128(a,value);
        }
        @Override public void sfence() { events.add(e("FENCE",0L,0L));fenceEffects++; }
        @Override public int lockedXaddDword(long a,int addend) {
            int old=raw.lockedXaddDword(a,addend);events.add(ev("XADD32",a,Integer.toUnsignedLong(addend),Integer.toUnsignedLong(old)));return old;
        }
        GovernmentCrtBoundary185Api.LoopBudget budget() {
            return (header,cursor)->{ events.add(e("BUDGET",header,cursor));budgetEffects++; };
        }
    }
    private static void seedTable(Mem memory) {
        int[] observed={0x0422704E,0x0422704B,0x04227077,0x04227047,0x04227054,0x04227064,
                0x04227074,0x04227044,0x0422707C,0x04227058,0x04227090,0x04227080,0x04227050,
                0x04227060,0x04227070,0x04227040,0x04227098};
        for (int i=0;i<observed.length;i++) memory.raw.writeDword(B+TABLE+4L*i,observed[i]);
    }
    private static void seedBytes(Mem memory,long start,int count) {
        for (int i=-1;i<=count;i++) memory.raw.writeByte(start+i,0xA5);
    }
    private static void bytes(Mem memory,long start,int retained,int total,int value,String label) {
        equal(0xA5,memory.raw.readUnsignedByte(start-1),label+" before guard");
        for (int i=0;i<total;i++) equal(i<retained?0xA5:value,memory.raw.readUnsignedByte(start+i),label+" byte "+i);
        equal(0xA5,memory.raw.readUnsignedByte(start+total),label+" after guard");
    }
    private static GovernmentCrtBoundary185Api.Calls unexpected185() {
        return new GovernmentCrtBoundary185Api.Calls() {
            @Override public VolatileBits invoke(GovernmentCrtBoundary185Api.Call call) { throw new AssertionError("unexpected185 CALL "+call); }
            @Override public GovernmentCrtBoundary185Api.NormalReturn tail(GovernmentCrtBoundary185Api.Tail transfer) { throw new AssertionError("unexpected185 Tail "+transfer); }
            @Override public long readGsQword58() { throw new AssertionError("unexpected185 GS"); }
        };
    }
    private static VolatileBits incoming(long ptr,long count,long element) {
        return v(BASE,BASE.raxBits(),ptr,count,element,BASE.r9Bits(),BASE.r10Bits(),BASE.r11Bits(),BASE.xmm0());
    }
    private static void core(String name,int count,Integer flag,Long threshold,VolatileBits expected,List<Event> events) {
        Mem memory=new Mem();seedTable(memory);seedBytes(memory,D,count);memory.raw.writeQword(S,RET);
        if (flag!=null) memory.raw.writeByte(B+0x5C5CBB0L,flag);
        if (threshold!=null) memory.raw.writeQword(B+0x542F0A8L,threshold);
        VolatileBits offered=v(BASE,BASE.raxBits(),D,BASE.rdxBits(),count,BASE.r9Bits(),BASE.r10Bits(),BASE.r11Bits(),BASE.xmm0());
        var actual=GovernmentMemoryFill206.execute(new GovernmentCrtBoundary185Api.Entry(B,S,offered,N),memory,unexpected185(),memory.budget());
        equal(new GovernmentCrtBoundary185Api.NormalReturn(expected,RET,S+8,N),actual,name+" full normal return");
        equal(events,memory.events,name+" exact effects");bytes(memory,D,0,count,0xAB,name);scenes++;coreScenes++;
    }
    private static void rawTail(String name,int count,VolatileBits expectedOffered,List<Event> events) {
        Mem memory=new Mem();seedTable(memory);seedBytes(memory,D,count);memory.raw.writeByte(B+0x5C5CBB0L,2);
        memory.raw.writeQword(S,RET);
        var expectedTail=new GovernmentCrtBoundary185Api.Tail(0x4226F57L,GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,
                0x4226EF0L,new GovernmentCrtBoundary185Api.Entry(B,S,expectedOffered,N));
        var ports=new GovernmentCrtBoundary185Api.Calls() {
            @Override public VolatileBits invoke(GovernmentCrtBoundary185Api.Call call) { throw new AssertionError("raw Tail made CALL"); }
            @Override public GovernmentCrtBoundary185Api.NormalReturn tail(GovernmentCrtBoundary185Api.Tail transfer) {
                equal(expectedTail,transfer,name+" full raw Tail");tails++;
                memory.events.add(ev("TAIL",transfer.jumpSiteRva(),transfer.targetBits(),transfer.entry().rspBits()));
                return TAIL_RESULT;
            }
            @Override public long readGsQword58() { throw new AssertionError("raw Tail read GS"); }
        };
        VolatileBits offered=v(BASE,BASE.raxBits(),D,BASE.rdxBits(),count,BASE.r9Bits(),BASE.r10Bits(),BASE.r11Bits(),BASE.xmm0());
        var actual=GovernmentMemoryFill206.execute(new GovernmentCrtBoundary185Api.Entry(B,S,offered,N),memory,ports,memory.budget());
        equal(TAIL_RESULT,actual,name+" arbitrary full return");equal(true,actual==TAIL_RESULT,name+" exact return object");
        equal(events,memory.events,name+" only actual Tail effects");bytes(memory,D,count,count,0xA5,name);scenes++;coreScenes++;
    }
    private static void composition(String name,long originalPtr,long count,long element,long allocation,
            int totalBytes,int retainedBytes,List<Port> expectedPorts,OpaqueCall expectedFill,VolatileBits expected,List<Event> events) {
        Mem memory=new Mem();seedTable(memory);seedBytes(memory,allocation,totalBytes);memory.raw.writeQword(S,RET);
        if (totalBytes==256) { memory.raw.writeByte(B+0x5C5CBB0L,0);memory.raw.writeQword(B+0x542F0A8L,1); }
        int[] index={0},fillCount={0};
        GovernmentPrimaryTail155Api.Calls fallback=new GovernmentPrimaryTail155Api.Calls() {
            @Override public long readGsQword58() { throw new AssertionError(name+" unexpected GS"); }
            @Override public VolatileBits invoke(OpaqueCall call) {
                if (index[0]>=expectedPorts.size()) throw new AssertionError(name+" unexpected opaque call "+call);
                Port port=expectedPorts.get(index[0]++);equal(port.call(),call,name+" full opaque port "+index[0]);
                equal(B+call.callSiteRva()+5,memory.raw.readQword(call.rspBits()-8),name+" physical opaque push");
                memory.events.add(ev("PORT",call.callSiteRva(),call.targetRva(),call.rspBits()));opaquePorts++;physicalPushes++;
                return port.post();
            }
        };
        var bound=GovernmentMemoryFill206Calls.bindTail(B,memory,fallback,unexpected185(),memory.budget());
        GovernmentPrimaryTail155Api.Calls observer=new GovernmentPrimaryTail155Api.Calls() {
            @Override public long readGsQword58() { return bound.readGsQword58(); }
            @Override public VolatileBits invoke(OpaqueCall call) {
                if (call.callSiteRva()==0x425B87CL && call.targetRva()==0x4226F10L) {
                    equal(expectedFill,call,name+" full actual fill frame");
                    equal(B+0x425B881L,memory.raw.readQword(call.rspBits()-8),name+" actual fill push");
                    fillCount[0]++;fillBindings++;physicalPushes++;
                    memory.events.add(ev("FILL",call.callSiteRva(),call.targetRva(),call.rspBits()));
                }
                return bound.invoke(call);
            }
        };
        var actual=GovernmentRegistryResize201.execute(new GovernmentCallee164Api.Entry(B,S,incoming(originalPtr,count,element),N),memory,observer);
        equal(new GovernmentCallee164Api.NormalReturn(expected,N,RET,S+8),actual,name+" full actual201 return");
        equal(expectedPorts.size(),index[0],name+" port count");equal(1,fillCount[0],name+" actual206 binding count");
        equal(events,memory.events,name+" combined source effects");bytes(memory,allocation,retainedBytes,totalBytes,0,name);
        scenes++;compositionScenes++;
    }

    /* Whole model stop methods are appended after independent source review. */
    private static void small0_7() {
        // SMALL_0
        core("SMALL_0", 0, null, null,
            new VolatileBits(0x0000000060001003L, 0x0000000060001003L, 0xABABABABABABABABL, 0x0000000000000000L, 0x000000010422704EL, 0x000000000000100AL, 0x0000000060001003L,
                new Bits128(0x0000000000001010L, 0xFFFFFFFFFFFFEFEFL),
                new Bits128(0x0000000000001020L, 0xFFFFFFFFFFFFEFDFL),
                new Bits128(0x0000000000001030L, 0xFFFFFFFFFFFFEFCFL),
                new Bits128(0x0000000000001040L, 0xFFFFFFFFFFFFEFBFL),
                new Bits128(0x0000000000001050L, 0xFFFFFFFFFFFFEFAFL),
                new Bits128(0x0000000000001060L, 0xFFFFFFFFFFFFEF9FL)),
            List.of(
                e("R32", 0x00000001060900B0L, 0x000000000422704EL),
                e("R64", 0x00000000C0000008L, 0x11223344778899AAL)
            ));

        // SMALL_1
        core("SMALL_1", 1, null, null,
            new VolatileBits(0x0000000060001003L, 0x0000000060001004L, 0xABABABABABABABABL, 0x0000000000000001L, 0x000000010422704BL, 0x000000000000100AL, 0x0000000060001003L,
                new Bits128(0x0000000000001010L, 0xFFFFFFFFFFFFEFEFL),
                new Bits128(0x0000000000001020L, 0xFFFFFFFFFFFFEFDFL),
                new Bits128(0x0000000000001030L, 0xFFFFFFFFFFFFEFCFL),
                new Bits128(0x0000000000001040L, 0xFFFFFFFFFFFFEFBFL),
                new Bits128(0x0000000000001050L, 0xFFFFFFFFFFFFEFAFL),
                new Bits128(0x0000000000001060L, 0xFFFFFFFFFFFFEF9FL)),
            List.of(
                e("R32", 0x00000001060900B4L, 0x000000000422704BL),
                e("W8", 0x0000000060001003L, 0x00000000000000ABL),
                e("R64", 0x00000000C0000008L, 0x11223344778899AAL)
            ));

        // SMALL_2
        core("SMALL_2", 2, null, null,
            new VolatileBits(0x0000000060001003L, 0x0000000060001005L, 0xABABABABABABABABL, 0x0000000000000002L, 0x0000000104227077L, 0x000000000000100AL, 0x0000000060001003L,
                new Bits128(0x0000000000001010L, 0xFFFFFFFFFFFFEFEFL),
                new Bits128(0x0000000000001020L, 0xFFFFFFFFFFFFEFDFL),
                new Bits128(0x0000000000001030L, 0xFFFFFFFFFFFFEFCFL),
                new Bits128(0x0000000000001040L, 0xFFFFFFFFFFFFEFBFL),
                new Bits128(0x0000000000001050L, 0xFFFFFFFFFFFFEFAFL),
                new Bits128(0x0000000000001060L, 0xFFFFFFFFFFFFEF9FL)),
            List.of(
                e("R32", 0x00000001060900B8L, 0x0000000004227077L),
                e("W16", 0x0000000060001003L, 0x000000000000ABABL),
                e("R64", 0x00000000C0000008L, 0x11223344778899AAL)
            ));

        // SMALL_3
        core("SMALL_3", 3, null, null,
            new VolatileBits(0x0000000060001003L, 0x0000000060001006L, 0xABABABABABABABABL, 0x0000000000000003L, 0x0000000104227047L, 0x000000000000100AL, 0x0000000060001003L,
                new Bits128(0x0000000000001010L, 0xFFFFFFFFFFFFEFEFL),
                new Bits128(0x0000000000001020L, 0xFFFFFFFFFFFFEFDFL),
                new Bits128(0x0000000000001030L, 0xFFFFFFFFFFFFEFCFL),
                new Bits128(0x0000000000001040L, 0xFFFFFFFFFFFFEFBFL),
                new Bits128(0x0000000000001050L, 0xFFFFFFFFFFFFEFAFL),
                new Bits128(0x0000000000001060L, 0xFFFFFFFFFFFFEF9FL)),
            List.of(
                e("R32", 0x00000001060900BCL, 0x0000000004227047L),
                e("W16", 0x0000000060001003L, 0x000000000000ABABL),
                e("W8", 0x0000000060001005L, 0x00000000000000ABL),
                e("R64", 0x00000000C0000008L, 0x11223344778899AAL)
            ));

        // SMALL_4
        core("SMALL_4", 4, null, null,
            new VolatileBits(0x0000000060001003L, 0x0000000060001007L, 0xABABABABABABABABL, 0x0000000000000004L, 0x0000000104227054L, 0x000000000000100AL, 0x0000000060001003L,
                new Bits128(0x0000000000001010L, 0xFFFFFFFFFFFFEFEFL),
                new Bits128(0x0000000000001020L, 0xFFFFFFFFFFFFEFDFL),
                new Bits128(0x0000000000001030L, 0xFFFFFFFFFFFFEFCFL),
                new Bits128(0x0000000000001040L, 0xFFFFFFFFFFFFEFBFL),
                new Bits128(0x0000000000001050L, 0xFFFFFFFFFFFFEFAFL),
                new Bits128(0x0000000000001060L, 0xFFFFFFFFFFFFEF9FL)),
            List.of(
                e("R32", 0x00000001060900C0L, 0x0000000004227054L),
                e("W32", 0x0000000060001003L, 0x00000000ABABABABL),
                e("R64", 0x00000000C0000008L, 0x11223344778899AAL)
            ));

        // SMALL_5
        core("SMALL_5", 5, null, null,
            new VolatileBits(0x0000000060001003L, 0x0000000060001008L, 0xABABABABABABABABL, 0x0000000000000005L, 0x0000000104227064L, 0x000000000000100AL, 0x0000000060001003L,
                new Bits128(0x0000000000001010L, 0xFFFFFFFFFFFFEFEFL),
                new Bits128(0x0000000000001020L, 0xFFFFFFFFFFFFEFDFL),
                new Bits128(0x0000000000001030L, 0xFFFFFFFFFFFFEFCFL),
                new Bits128(0x0000000000001040L, 0xFFFFFFFFFFFFEFBFL),
                new Bits128(0x0000000000001050L, 0xFFFFFFFFFFFFEFAFL),
                new Bits128(0x0000000000001060L, 0xFFFFFFFFFFFFEF9FL)),
            List.of(
                e("R32", 0x00000001060900C4L, 0x0000000004227064L),
                e("W32", 0x0000000060001003L, 0x00000000ABABABABL),
                e("W8", 0x0000000060001007L, 0x00000000000000ABL),
                e("R64", 0x00000000C0000008L, 0x11223344778899AAL)
            ));

        // SMALL_6
        core("SMALL_6", 6, null, null,
            new VolatileBits(0x0000000060001003L, 0x0000000060001009L, 0xABABABABABABABABL, 0x0000000000000006L, 0x0000000104227074L, 0x000000000000100AL, 0x0000000060001003L,
                new Bits128(0x0000000000001010L, 0xFFFFFFFFFFFFEFEFL),
                new Bits128(0x0000000000001020L, 0xFFFFFFFFFFFFEFDFL),
                new Bits128(0x0000000000001030L, 0xFFFFFFFFFFFFEFCFL),
                new Bits128(0x0000000000001040L, 0xFFFFFFFFFFFFEFBFL),
                new Bits128(0x0000000000001050L, 0xFFFFFFFFFFFFEFAFL),
                new Bits128(0x0000000000001060L, 0xFFFFFFFFFFFFEF9FL)),
            List.of(
                e("R32", 0x00000001060900C8L, 0x0000000004227074L),
                e("W32", 0x0000000060001003L, 0x00000000ABABABABL),
                e("W16", 0x0000000060001007L, 0x000000000000ABABL),
                e("R64", 0x00000000C0000008L, 0x11223344778899AAL)
            ));

        // SMALL_7
        core("SMALL_7", 7, null, null,
            new VolatileBits(0x0000000060001003L, 0x000000006000100AL, 0xABABABABABABABABL, 0x0000000000000007L, 0x0000000104227044L, 0x000000000000100AL, 0x0000000060001003L,
                new Bits128(0x0000000000001010L, 0xFFFFFFFFFFFFEFEFL),
                new Bits128(0x0000000000001020L, 0xFFFFFFFFFFFFEFDFL),
                new Bits128(0x0000000000001030L, 0xFFFFFFFFFFFFEFCFL),
                new Bits128(0x0000000000001040L, 0xFFFFFFFFFFFFEFBFL),
                new Bits128(0x0000000000001050L, 0xFFFFFFFFFFFFEFAFL),
                new Bits128(0x0000000000001060L, 0xFFFFFFFFFFFFEF9FL)),
            List.of(
                e("R32", 0x00000001060900CCL, 0x0000000004227044L),
                e("W32", 0x0000000060001003L, 0x00000000ABABABABL),
                e("W16", 0x0000000060001007L, 0x000000000000ABABL),
                e("W8", 0x0000000060001009L, 0x00000000000000ABL),
                e("R64", 0x00000000C0000008L, 0x11223344778899AAL)
            ));
    }

    private static void small8_16() {
        // SMALL_8
        core("SMALL_8", 8, null, null,
            new VolatileBits(0x0000000060001003L, 0x000000006000100BL, 0xABABABABABABABABL, 0x0000000000000008L, 0x000000010422707CL, 0x000000000000100AL, 0x0000000060001003L,
                new Bits128(0x0000000000001010L, 0xFFFFFFFFFFFFEFEFL),
                new Bits128(0x0000000000001020L, 0xFFFFFFFFFFFFEFDFL),
                new Bits128(0x0000000000001030L, 0xFFFFFFFFFFFFEFCFL),
                new Bits128(0x0000000000001040L, 0xFFFFFFFFFFFFEFBFL),
                new Bits128(0x0000000000001050L, 0xFFFFFFFFFFFFEFAFL),
                new Bits128(0x0000000000001060L, 0xFFFFFFFFFFFFEF9FL)),
            List.of(
                e("R32", 0x00000001060900D0L, 0x000000000422707CL),
                e("W64", 0x0000000060001003L, 0xABABABABABABABABL),
                e("R64", 0x00000000C0000008L, 0x11223344778899AAL)
            ));

        // SMALL_9
        core("SMALL_9", 9, null, null,
            new VolatileBits(0x0000000060001003L, 0x000000006000100CL, 0xABABABABABABABABL, 0x0000000000000009L, 0x0000000104227058L, 0x000000000000100AL, 0x0000000060001003L,
                new Bits128(0x0000000000001010L, 0xFFFFFFFFFFFFEFEFL),
                new Bits128(0x0000000000001020L, 0xFFFFFFFFFFFFEFDFL),
                new Bits128(0x0000000000001030L, 0xFFFFFFFFFFFFEFCFL),
                new Bits128(0x0000000000001040L, 0xFFFFFFFFFFFFEFBFL),
                new Bits128(0x0000000000001050L, 0xFFFFFFFFFFFFEFAFL),
                new Bits128(0x0000000000001060L, 0xFFFFFFFFFFFFEF9FL)),
            List.of(
                e("R32", 0x00000001060900D4L, 0x0000000004227058L),
                e("W64", 0x0000000060001003L, 0xABABABABABABABABL),
                e("W8", 0x000000006000100BL, 0x00000000000000ABL),
                e("R64", 0x00000000C0000008L, 0x11223344778899AAL)
            ));

        // SMALL_10
        core("SMALL_10", 10, null, null,
            new VolatileBits(0x0000000060001003L, 0x000000006000100DL, 0xABABABABABABABABL, 0x000000000000000AL, 0x0000000104227090L, 0x000000000000100AL, 0x0000000060001003L,
                new Bits128(0x0000000000001010L, 0xFFFFFFFFFFFFEFEFL),
                new Bits128(0x0000000000001020L, 0xFFFFFFFFFFFFEFDFL),
                new Bits128(0x0000000000001030L, 0xFFFFFFFFFFFFEFCFL),
                new Bits128(0x0000000000001040L, 0xFFFFFFFFFFFFEFBFL),
                new Bits128(0x0000000000001050L, 0xFFFFFFFFFFFFEFAFL),
                new Bits128(0x0000000000001060L, 0xFFFFFFFFFFFFEF9FL)),
            List.of(
                e("R32", 0x00000001060900D8L, 0x0000000004227090L),
                e("W64", 0x0000000060001003L, 0xABABABABABABABABL),
                e("W16", 0x000000006000100BL, 0x000000000000ABABL),
                e("R64", 0x00000000C0000008L, 0x11223344778899AAL)
            ));

        // SMALL_11
        core("SMALL_11", 11, null, null,
            new VolatileBits(0x0000000060001003L, 0x000000006000100EL, 0xABABABABABABABABL, 0x000000000000000BL, 0x0000000104227080L, 0x000000000000100AL, 0x0000000060001003L,
                new Bits128(0x0000000000001010L, 0xFFFFFFFFFFFFEFEFL),
                new Bits128(0x0000000000001020L, 0xFFFFFFFFFFFFEFDFL),
                new Bits128(0x0000000000001030L, 0xFFFFFFFFFFFFEFCFL),
                new Bits128(0x0000000000001040L, 0xFFFFFFFFFFFFEFBFL),
                new Bits128(0x0000000000001050L, 0xFFFFFFFFFFFFEFAFL),
                new Bits128(0x0000000000001060L, 0xFFFFFFFFFFFFEF9FL)),
            List.of(
                e("R32", 0x00000001060900DCL, 0x0000000004227080L),
                e("W64", 0x0000000060001003L, 0xABABABABABABABABL),
                e("W16", 0x000000006000100BL, 0x000000000000ABABL),
                e("W8", 0x000000006000100DL, 0x00000000000000ABL),
                e("R64", 0x00000000C0000008L, 0x11223344778899AAL)
            ));

        // SMALL_12
        core("SMALL_12", 12, null, null,
            new VolatileBits(0x0000000060001003L, 0x000000006000100FL, 0xABABABABABABABABL, 0x000000000000000CL, 0x0000000104227050L, 0x000000000000100AL, 0x0000000060001003L,
                new Bits128(0x0000000000001010L, 0xFFFFFFFFFFFFEFEFL),
                new Bits128(0x0000000000001020L, 0xFFFFFFFFFFFFEFDFL),
                new Bits128(0x0000000000001030L, 0xFFFFFFFFFFFFEFCFL),
                new Bits128(0x0000000000001040L, 0xFFFFFFFFFFFFEFBFL),
                new Bits128(0x0000000000001050L, 0xFFFFFFFFFFFFEFAFL),
                new Bits128(0x0000000000001060L, 0xFFFFFFFFFFFFEF9FL)),
            List.of(
                e("R32", 0x00000001060900E0L, 0x0000000004227050L),
                e("W64", 0x0000000060001003L, 0xABABABABABABABABL),
                e("W32", 0x000000006000100BL, 0x00000000ABABABABL),
                e("R64", 0x00000000C0000008L, 0x11223344778899AAL)
            ));

        // SMALL_13
        core("SMALL_13", 13, null, null,
            new VolatileBits(0x0000000060001003L, 0x0000000060001010L, 0xABABABABABABABABL, 0x000000000000000DL, 0x0000000104227060L, 0x000000000000100AL, 0x0000000060001003L,
                new Bits128(0x0000000000001010L, 0xFFFFFFFFFFFFEFEFL),
                new Bits128(0x0000000000001020L, 0xFFFFFFFFFFFFEFDFL),
                new Bits128(0x0000000000001030L, 0xFFFFFFFFFFFFEFCFL),
                new Bits128(0x0000000000001040L, 0xFFFFFFFFFFFFEFBFL),
                new Bits128(0x0000000000001050L, 0xFFFFFFFFFFFFEFAFL),
                new Bits128(0x0000000000001060L, 0xFFFFFFFFFFFFEF9FL)),
            List.of(
                e("R32", 0x00000001060900E4L, 0x0000000004227060L),
                e("W64", 0x0000000060001003L, 0xABABABABABABABABL),
                e("W32", 0x000000006000100BL, 0x00000000ABABABABL),
                e("W8", 0x000000006000100FL, 0x00000000000000ABL),
                e("R64", 0x00000000C0000008L, 0x11223344778899AAL)
            ));

        // SMALL_14
        core("SMALL_14", 14, null, null,
            new VolatileBits(0x0000000060001003L, 0x0000000060001011L, 0xABABABABABABABABL, 0x000000000000000EL, 0x0000000104227070L, 0x000000000000100AL, 0x0000000060001003L,
                new Bits128(0x0000000000001010L, 0xFFFFFFFFFFFFEFEFL),
                new Bits128(0x0000000000001020L, 0xFFFFFFFFFFFFEFDFL),
                new Bits128(0x0000000000001030L, 0xFFFFFFFFFFFFEFCFL),
                new Bits128(0x0000000000001040L, 0xFFFFFFFFFFFFEFBFL),
                new Bits128(0x0000000000001050L, 0xFFFFFFFFFFFFEFAFL),
                new Bits128(0x0000000000001060L, 0xFFFFFFFFFFFFEF9FL)),
            List.of(
                e("R32", 0x00000001060900E8L, 0x0000000004227070L),
                e("W64", 0x0000000060001003L, 0xABABABABABABABABL),
                e("W32", 0x000000006000100BL, 0x00000000ABABABABL),
                e("W16", 0x000000006000100FL, 0x000000000000ABABL),
                e("R64", 0x00000000C0000008L, 0x11223344778899AAL)
            ));

        // SMALL_15
        core("SMALL_15", 15, null, null,
            new VolatileBits(0x0000000060001003L, 0x0000000060001012L, 0xABABABABABABABABL, 0x000000000000000FL, 0x0000000104227040L, 0x000000000000100AL, 0x0000000060001003L,
                new Bits128(0x0000000000001010L, 0xFFFFFFFFFFFFEFEFL),
                new Bits128(0x0000000000001020L, 0xFFFFFFFFFFFFEFDFL),
                new Bits128(0x0000000000001030L, 0xFFFFFFFFFFFFEFCFL),
                new Bits128(0x0000000000001040L, 0xFFFFFFFFFFFFEFBFL),
                new Bits128(0x0000000000001050L, 0xFFFFFFFFFFFFEFAFL),
                new Bits128(0x0000000000001060L, 0xFFFFFFFFFFFFEF9FL)),
            List.of(
                e("R32", 0x00000001060900ECL, 0x0000000004227040L),
                e("W64", 0x0000000060001003L, 0xABABABABABABABABL),
                e("W32", 0x000000006000100BL, 0x00000000ABABABABL),
                e("W16", 0x000000006000100FL, 0x000000000000ABABL),
                e("W8", 0x0000000060001011L, 0x00000000000000ABL),
                e("R64", 0x00000000C0000008L, 0x11223344778899AAL)
            ));

        // SMALL_16
        core("SMALL_16", 16, null, null,
            new VolatileBits(0x0000000060001003L, 0x0000000060001013L, 0xABABABABABABABABL, 0x0000000000000010L, 0x0000000104227098L, 0x000000000000100AL, 0x0000000060001003L,
                new Bits128(0x0000000000001010L, 0xFFFFFFFFFFFFEFEFL),
                new Bits128(0x0000000000001020L, 0xFFFFFFFFFFFFEFDFL),
                new Bits128(0x0000000000001030L, 0xFFFFFFFFFFFFEFCFL),
                new Bits128(0x0000000000001040L, 0xFFFFFFFFFFFFEFBFL),
                new Bits128(0x0000000000001050L, 0xFFFFFFFFFFFFEFAFL),
                new Bits128(0x0000000000001060L, 0xFFFFFFFFFFFFEF9FL)),
            List.of(
                e("R32", 0x00000001060900F0L, 0x0000000004227098L),
                e("W64", 0x0000000060001003L, 0xABABABABABABABABL),
                e("W64", 0x000000006000100BL, 0xABABABABABABABABL),
                e("R64", 0x00000000C0000008L, 0x11223344778899AAL)
            ));
    }

    private static void largeCases() {
        // DIRECT17
        core("DIRECT17", 17, null, null,
            v(BASE, 0x0000000060001003L, 0x0000000060001013L, 0x00000000000000ABL, 0x0000000000000001L, 0x0000000000000000L, 0x000000000000100AL, 0x0000000060001003L, REPEATED),
            List.of(
                e("BUDGET", 0x0000000004226FC0L, 0x0000000060001003L),
                ev("W128", 0x0000000060001003L, 0xABABABABABABABABL, 0xABABABABABABABABL),
                ev("W128", 0x0000000060001004L, 0xABABABABABABABABL, 0xABABABABABABABABL),
                e("R64", 0x00000000C0000008L, 0x11223344778899AAL)
            ));

        // UNALIGNED129
        core("UNALIGNED129", 129, 0, null,
            v(BASE, 0x0000000060001003L, 0x0000000060001080L, 0x00000000000000ABL, 0x0000000000000004L, 0x0000000000000000L, 0x000000000000100AL, 0x0000000060001003L, REPEATED),
            List.of(
                e("R8", 0x0000000105C5CBB0L, 0x0000000000000000L),
                ev("W128", 0x0000000060001003L, 0xABABABABABABABABL, 0xABABABABABABABABL),
                e("BUDGET", 0x0000000004226FC0L, 0x0000000060001010L),
                ev("W128", 0x0000000060001010L, 0xABABABABABABABABL, 0xABABABABABABABABL),
                e("BUDGET", 0x0000000004226FC0L, 0x0000000060001020L),
                ev("W128", 0x0000000060001020L, 0xABABABABABABABABL, 0xABABABABABABABABL),
                e("BUDGET", 0x0000000004226FC0L, 0x0000000060001030L),
                ev("W128", 0x0000000060001030L, 0xABABABABABABABABL, 0xABABABABABABABABL),
                e("BUDGET", 0x0000000004226FC0L, 0x0000000060001040L),
                ev("W128", 0x0000000060001040L, 0xABABABABABABABABL, 0xABABABABABABABABL),
                e("BUDGET", 0x0000000004226FC0L, 0x0000000060001050L),
                ev("W128", 0x0000000060001050L, 0xABABABABABABABABL, 0xABABABABABABABABL),
                e("BUDGET", 0x0000000004226FC0L, 0x0000000060001060L),
                ev("W128", 0x0000000060001060L, 0xABABABABABABABABL, 0xABABABABABABABABL),
                e("BUDGET", 0x0000000004226FC0L, 0x0000000060001070L),
                ev("W128", 0x0000000060001070L, 0xABABABABABABABABL, 0xABABABABABABABABL),
                ev("W128", 0x0000000060001074L, 0xABABABABABABABABL, 0xABABABABABABABABL),
                e("R64", 0x00000000C0000008L, 0x11223344778899AAL)
            ));

        // CACHED240
        core("CACHED240", 240, 0, 1L,
            v(BASE, 0x0000000060001003L, 0x00000000600010F0L, 0x00000000000000ABL, 0x0000000000000003L, 0x0000000000000000L, 0x000000000000100AL, 0x0000000060001003L, REPEATED),
            List.of(
                e("R8", 0x0000000105C5CBB0L, 0x0000000000000000L),
                ev("W128", 0x0000000060001003L, 0xABABABABABABABABL, 0xABABABABABABABABL),
                e("R64", 0x000000010542F0A8L, 0x0000000000000001L),
                e("BUDGET", 0x0000000004226F80L, 0x0000000060001010L),
                ev("W128", 0x0000000060001010L, 0xABABABABABABABABL, 0xABABABABABABABABL),
                ev("W128", 0x0000000060001020L, 0xABABABABABABABABL, 0xABABABABABABABABL),
                ev("W128", 0x0000000060001030L, 0xABABABABABABABABL, 0xABABABABABABABABL),
                ev("W128", 0x0000000060001040L, 0xABABABABABABABABL, 0xABABABABABABABABL),
                ev("W128", 0x0000000060001050L, 0xABABABABABABABABL, 0xABABABABABABABABL),
                ev("W128", 0x0000000060001060L, 0xABABABABABABABABL, 0xABABABABABABABABL),
                ev("W128", 0x0000000060001070L, 0xABABABABABABABABL, 0xABABABABABABABABL),
                ev("W128", 0x0000000060001080L, 0xABABABABABABABABL, 0xABABABABABABABABL),
                e("BUDGET", 0x0000000004226FC0L, 0x0000000060001090L),
                ev("W128", 0x0000000060001090L, 0xABABABABABABABABL, 0xABABABABABABABABL),
                e("BUDGET", 0x0000000004226FC0L, 0x00000000600010A0L),
                ev("W128", 0x00000000600010A0L, 0xABABABABABABABABL, 0xABABABABABABABABL),
                e("BUDGET", 0x0000000004226FC0L, 0x00000000600010B0L),
                ev("W128", 0x00000000600010B0L, 0xABABABABABABABABL, 0xABABABABABABABABL),
                e("BUDGET", 0x0000000004226FC0L, 0x00000000600010C0L),
                ev("W128", 0x00000000600010C0L, 0xABABABABABABABABL, 0xABABABABABABABABL),
                e("BUDGET", 0x0000000004226FC0L, 0x00000000600010D0L),
                ev("W128", 0x00000000600010D0L, 0xABABABABABABABABL, 0xABABABABABABABABL),
                e("BUDGET", 0x0000000004226FC0L, 0x00000000600010E0L),
                ev("W128", 0x00000000600010E0L, 0xABABABABABABABABL, 0xABABABABABABABABL),
                ev("W128", 0x00000000600010E3L, 0xABABABABABABABABL, 0xABABABABABABABABL),
                e("R64", 0x00000000C0000008L, 0x11223344778899AAL)
            ));

        // NT144
        core("NT144", 144, 0, 0L,
            v(BASE, 0x0000000060001003L, 0x0000000060001090L, 0x00000000000000ABL, 0x0000000000000003L, 0x0000000000000000L, 0x000000000000100AL, 0x0000000060001003L, REPEATED),
            List.of(
                e("R8", 0x0000000105C5CBB0L, 0x0000000000000000L),
                ev("W128", 0x0000000060001003L, 0xABABABABABABABABL, 0xABABABABABABABABL),
                e("R64", 0x000000010542F0A8L, 0x0000000000000000L),
                e("BUDGET", 0x0000000004226FE0L, 0x0000000060001010L),
                ev("NT128", 0x0000000060001010L, 0xABABABABABABABABL, 0xABABABABABABABABL),
                ev("NT128", 0x0000000060001020L, 0xABABABABABABABABL, 0xABABABABABABABABL),
                ev("NT128", 0x0000000060001030L, 0xABABABABABABABABL, 0xABABABABABABABABL),
                ev("NT128", 0x0000000060001040L, 0xABABABABABABABABL, 0xABABABABABABABABL),
                ev("NT128", 0x0000000060001050L, 0xABABABABABABABABL, 0xABABABABABABABABL),
                ev("NT128", 0x0000000060001060L, 0xABABABABABABABABL, 0xABABABABABABABABL),
                ev("NT128", 0x0000000060001070L, 0xABABABABABABABABL, 0xABABABABABABABABL),
                ev("NT128", 0x0000000060001080L, 0xABABABABABABABABL, 0xABABABABABABABABL),
                e("FENCE", 0L, 0L),
                ev("W128", 0x0000000060001083L, 0xABABABABABABABABL, 0xABABABABABABABABL),
                e("R64", 0x00000000C0000008L, 0x11223344778899AAL)
            ));

        // CPU_EXTERNAL_TAIL
        rawTail("CPU_EXTERNAL_TAIL", 240,
            v(BASE, 0xAAAA000011112222L, 0x0000000060001003L, 0x00000000000000ABL, 0x00000000000000F0L, 0xABABABABABABABABL, 0x000000000000100AL, 0x0000000060001003L, REPEATED),
            List.of(
                e("R8", 0x0000000105C5CBB0L, 0x0000000000000002L),
                ev("TAIL", 0x0000000004226F57L, 0x0000000004226EF0L, 0x00000000C0000008L)
            ));
    }

    private static void actual201Cases() {
        composition("ACTUAL201_NULL32",0x0000000000000000L,0x4L,0x8L,0x0000000070001003L,32,0,
            List.of(
                new Port(oc(0x000000000425B85EL,0x0000000004251F4CL,new VolatileBits(0x3FFFFFFFFFFFFFF8L,0x0000000000000000L,0x0000000000000020L,0x0000000000000008L,0x0000000000001009L,0x000000000000100AL,0x000000000000100BL,new Bits128(0x0000000000001010L,0xFFFFFFFFFFFFEFEFL),new Bits128(0x0000000000001020L,0xFFFFFFFFFFFFEFDFL),new Bits128(0x0000000000001030L,0xFFFFFFFFFFFFEFCFL),new Bits128(0x0000000000001040L,0xFFFFFFFFFFFFEFBFL),new Bits128(0x0000000000001050L,0xFFFFFFFFFFFFEFAFL),new Bits128(0x0000000000001060L,0xFFFFFFFFFFFFEF9FL)),n(0x0000000000000020L,0x0000000000000008L,0x0000000000000000L,0x0000000000000000L)),new VolatileBits(0x0000000070001003L,0x0000000000009011L,0x0000000000009022L,0x0000000000009008L,0x0000000000009009L,0x000000000000900AL,0x000000000000900BL,new Bits128(0x0000000000009010L,0xFFFFFFFFFFFF6FEFL),new Bits128(0x0000000000009020L,0xFFFFFFFFFFFF6FDFL),new Bits128(0x0000000000009030L,0xFFFFFFFFFFFF6FCFL),new Bits128(0x0000000000009040L,0xFFFFFFFFFFFF6FBFL),new Bits128(0x0000000000009050L,0xFFFFFFFFFFFF6FAFL),new Bits128(0x0000000000009060L,0xFFFFFFFFFFFF6F9FL)))
            ),
            oc(0x000000000425B87CL,0x0000000004226F10L,new VolatileBits(0x0000000070001003L,0x0000000070001003L,0x0000000000000000L,0x0000000000000020L,0x0000000000009009L,0x000000000000900AL,0x000000000000900BL,new Bits128(0x0000000000009010L,0xFFFFFFFFFFFF6FEFL),new Bits128(0x0000000000009020L,0xFFFFFFFFFFFF6FDFL),new Bits128(0x0000000000009030L,0xFFFFFFFFFFFF6FCFL),new Bits128(0x0000000000009040L,0xFFFFFFFFFFFF6FBFL),new Bits128(0x0000000000009050L,0xFFFFFFFFFFFF6FAFL),new Bits128(0x0000000000009060L,0xFFFFFFFFFFFF6F9FL)),n(0x0000000000000020L,0x0000000000000008L,0x0000000070001003L,0x0000000000000000L)),
            new VolatileBits(0x0000000070001003L,0x0000000070001023L,0x0000000000000000L,0x0000000000000000L,0x0000000000000000L,0x000000000000900AL,0x0000000070001003L,new Bits128(0x0000000000000000L,0x0000000000000000L),new Bits128(0x0000000000009020L,0xFFFFFFFFFFFF6FDFL),new Bits128(0x0000000000009030L,0xFFFFFFFFFFFF6FCFL),new Bits128(0x0000000000009040L,0xFFFFFFFFFFFF6FBFL),new Bits128(0x0000000000009050L,0xFFFFFFFFFFFF6FAFL),new Bits128(0x0000000000009060L,0xFFFFFFFFFFFF6F9FL)),
            List.of(
                ev("W64",0x00000000C0000010L,0x2222000022220000L,0x0000000000000000L),
                ev("W64",0x00000000C0000018L,0x2222000022220001L,0x0000000000000000L),
                ev("W64",0x00000000C0000020L,0x2222000022220002L,0x0000000000000000L),
                ev("W64",0x00000000C0000000L,0x2222000022220003L,0x0000000000000000L),
                ev("W64",0x00000000BFFFFFD8L,0x000000010425B863L,0x0000000000000000L),
                ev("PORT",0x000000000425B85EL,0x0000000004251F4CL,0x00000000BFFFFFE0L),
                ev("W64",0x00000000BFFFFFD8L,0x000000010425B881L,0x0000000000000000L),
                ev("FILL",0x000000000425B87CL,0x0000000004226F10L,0x00000000BFFFFFE0L),
                ev("BUDGET",0x0000000004226FC0L,0x0000000070001003L,0x0000000000000000L),
                ev("W128",0x0000000070001003L,0x0000000000000000L,0x0000000000000000L),
                ev("BUDGET",0x0000000004226FC0L,0x0000000070001013L,0x0000000000000000L),
                ev("W128",0x0000000070001013L,0x0000000000000000L,0x0000000000000000L),
                ev("R64",0x00000000BFFFFFD8L,0x000000010425B881L,0x0000000000000000L),
                ev("R64",0x00000000C0000010L,0x2222000022220000L,0x0000000000000000L),
                ev("R64",0x00000000C0000018L,0x2222000022220001L,0x0000000000000000L),
                ev("R64",0x00000000C0000020L,0x2222000022220002L,0x0000000000000000L),
                ev("R64",0x00000000C0000000L,0x2222000022220003L,0x0000000000000000L),
                ev("R64",0x00000000C0000008L,0x11223344778899AAL,0x0000000000000000L)
            ));
        composition("ACTUAL201_GROW240",0x0000000060002000L,0x20L,0x8L,0x0000000070002003L,256,16,
            List.of(
                new Port(oc(0x000000000425B848L,0x0000000004259250L,new VolatileBits(0x07FFFFFFFFFFFFFFL,0x0000000060002000L,0x0000000000000000L,0x0000000000000008L,0x0000000000001009L,0x000000000000100AL,0x000000000000100BL,new Bits128(0x0000000000001010L,0xFFFFFFFFFFFFEFEFL),new Bits128(0x0000000000001020L,0xFFFFFFFFFFFFEFDFL),new Bits128(0x0000000000001030L,0xFFFFFFFFFFFFEFCFL),new Bits128(0x0000000000001040L,0xFFFFFFFFFFFFEFBFL),new Bits128(0x0000000000001050L,0xFFFFFFFFFFFFEFAFL),new Bits128(0x0000000000001060L,0xFFFFFFFFFFFFEF9FL)),n(0x0000000000000020L,0x0000000000000008L,0x0000000060002000L,0x2222000022220003L)),new VolatileBits(0x0000000000000010L,0x1020304050607080L,0x2030405060708090L,0x0000000000008008L,0x0000000000008009L,0x000000000000800AL,0x000000000000800BL,new Bits128(0x0000000000008010L,0xFFFFFFFFFFFF7FEFL),new Bits128(0x0000000000008020L,0xFFFFFFFFFFFF7FDFL),new Bits128(0x0000000000008030L,0xFFFFFFFFFFFF7FCFL),new Bits128(0x0000000000008040L,0xFFFFFFFFFFFF7FBFL),new Bits128(0x0000000000008050L,0xFFFFFFFFFFFF7FAFL),new Bits128(0x0000000000008060L,0xFFFFFFFFFFFF7F9FL))),
                new Port(oc(0x000000000425B85EL,0x0000000004251F4CL,new VolatileBits(0x0000000000000010L,0x0000000060002000L,0x0000000000000100L,0x0000000000008008L,0x0000000000008009L,0x000000000000800AL,0x000000000000800BL,new Bits128(0x0000000000008010L,0xFFFFFFFFFFFF7FEFL),new Bits128(0x0000000000008020L,0xFFFFFFFFFFFF7FDFL),new Bits128(0x0000000000008030L,0xFFFFFFFFFFFF7FCFL),new Bits128(0x0000000000008040L,0xFFFFFFFFFFFF7FBFL),new Bits128(0x0000000000008050L,0xFFFFFFFFFFFF7FAFL),new Bits128(0x0000000000008060L,0xFFFFFFFFFFFF7F9FL)),n(0x0000000000000100L,0x0000000000000008L,0x0000000060002000L,0x0000000000000010L)),new VolatileBits(0x0000000070002003L,0x0000000000009011L,0x0000000000009022L,0x0000000000009008L,0x0000000000009009L,0x000000000000900AL,0x000000000000900BL,new Bits128(0x0000000000009010L,0xFFFFFFFFFFFF6FEFL),new Bits128(0x0000000000009020L,0xFFFFFFFFFFFF6FDFL),new Bits128(0x0000000000009030L,0xFFFFFFFFFFFF6FCFL),new Bits128(0x0000000000009040L,0xFFFFFFFFFFFF6FBFL),new Bits128(0x0000000000009050L,0xFFFFFFFFFFFF6FAFL),new Bits128(0x0000000000009060L,0xFFFFFFFFFFFF6F9FL)))
            ),
            oc(0x000000000425B87CL,0x0000000004226F10L,new VolatileBits(0x0000000070002003L,0x0000000070002013L,0x0000000000000000L,0x00000000000000F0L,0x0000000000009009L,0x000000000000900AL,0x000000000000900BL,new Bits128(0x0000000000009010L,0xFFFFFFFFFFFF6FEFL),new Bits128(0x0000000000009020L,0xFFFFFFFFFFFF6FDFL),new Bits128(0x0000000000009030L,0xFFFFFFFFFFFF6FCFL),new Bits128(0x0000000000009040L,0xFFFFFFFFFFFF6FBFL),new Bits128(0x0000000000009050L,0xFFFFFFFFFFFF6FAFL),new Bits128(0x0000000000009060L,0xFFFFFFFFFFFF6F9FL)),n(0x00000000000000F0L,0x0000000000000008L,0x0000000070002003L,0x0000000000000010L)),
            new VolatileBits(0x0000000070002003L,0x0000000070002100L,0x0000000000000000L,0x0000000000000003L,0x0000000000000000L,0x000000000000900AL,0x0000000070002013L,new Bits128(0x0000000000000000L,0x0000000000000000L),new Bits128(0x0000000000009020L,0xFFFFFFFFFFFF6FDFL),new Bits128(0x0000000000009030L,0xFFFFFFFFFFFF6FCFL),new Bits128(0x0000000000009040L,0xFFFFFFFFFFFF6FBFL),new Bits128(0x0000000000009050L,0xFFFFFFFFFFFF6FAFL),new Bits128(0x0000000000009060L,0xFFFFFFFFFFFF6F9FL)),
            List.of(
                ev("W64",0x00000000C0000010L,0x2222000022220000L,0x0000000000000000L),
                ev("W64",0x00000000C0000018L,0x2222000022220001L,0x0000000000000000L),
                ev("W64",0x00000000C0000020L,0x2222000022220002L,0x0000000000000000L),
                ev("W64",0x00000000C0000000L,0x2222000022220003L,0x0000000000000000L),
                ev("W64",0x00000000BFFFFFD8L,0x000000010425B84DL,0x0000000000000000L),
                ev("PORT",0x000000000425B848L,0x0000000004259250L,0x00000000BFFFFFE0L),
                ev("W64",0x00000000BFFFFFD8L,0x000000010425B863L,0x0000000000000000L),
                ev("PORT",0x000000000425B85EL,0x0000000004251F4CL,0x00000000BFFFFFE0L),
                ev("W64",0x00000000BFFFFFD8L,0x000000010425B881L,0x0000000000000000L),
                ev("FILL",0x000000000425B87CL,0x0000000004226F10L,0x00000000BFFFFFE0L),
                ev("R8",0x0000000105C5CBB0L,0x0000000000000000L,0x0000000000000000L),
                ev("W128",0x0000000070002013L,0x0000000000000000L,0x0000000000000000L),
                ev("R64",0x000000010542F0A8L,0x0000000000000001L,0x0000000000000000L),
                ev("BUDGET",0x0000000004226F80L,0x0000000070002020L,0x0000000000000000L),
                ev("W128",0x0000000070002020L,0x0000000000000000L,0x0000000000000000L),
                ev("W128",0x0000000070002030L,0x0000000000000000L,0x0000000000000000L),
                ev("W128",0x0000000070002040L,0x0000000000000000L,0x0000000000000000L),
                ev("W128",0x0000000070002050L,0x0000000000000000L,0x0000000000000000L),
                ev("W128",0x0000000070002060L,0x0000000000000000L,0x0000000000000000L),
                ev("W128",0x0000000070002070L,0x0000000000000000L,0x0000000000000000L),
                ev("W128",0x0000000070002080L,0x0000000000000000L,0x0000000000000000L),
                ev("W128",0x0000000070002090L,0x0000000000000000L,0x0000000000000000L),
                ev("BUDGET",0x0000000004226FC0L,0x00000000700020A0L,0x0000000000000000L),
                ev("W128",0x00000000700020A0L,0x0000000000000000L,0x0000000000000000L),
                ev("BUDGET",0x0000000004226FC0L,0x00000000700020B0L,0x0000000000000000L),
                ev("W128",0x00000000700020B0L,0x0000000000000000L,0x0000000000000000L),
                ev("BUDGET",0x0000000004226FC0L,0x00000000700020C0L,0x0000000000000000L),
                ev("W128",0x00000000700020C0L,0x0000000000000000L,0x0000000000000000L),
                ev("BUDGET",0x0000000004226FC0L,0x00000000700020D0L,0x0000000000000000L),
                ev("W128",0x00000000700020D0L,0x0000000000000000L,0x0000000000000000L),
                ev("BUDGET",0x0000000004226FC0L,0x00000000700020E0L,0x0000000000000000L),
                ev("W128",0x00000000700020E0L,0x0000000000000000L,0x0000000000000000L),
                ev("BUDGET",0x0000000004226FC0L,0x00000000700020F0L,0x0000000000000000L),
                ev("W128",0x00000000700020F0L,0x0000000000000000L,0x0000000000000000L),
                ev("W128",0x00000000700020F3L,0x0000000000000000L,0x0000000000000000L),
                ev("R64",0x00000000BFFFFFD8L,0x000000010425B881L,0x0000000000000000L),
                ev("R64",0x00000000C0000010L,0x2222000022220000L,0x0000000000000000L),
                ev("R64",0x00000000C0000018L,0x2222000022220001L,0x0000000000000000L),
                ev("R64",0x00000000C0000020L,0x2222000022220002L,0x0000000000000000L),
                ev("R64",0x00000000C0000000L,0x2222000022220003L,0x0000000000000000L),
                ev("R64",0x00000000C0000008L,0x11223344778899AAL,0x0000000000000000L)
            ));
    }


    public static void main(String[] args) {
        if (args.length!=0) throw new IllegalArgumentException("manual witness takes no arguments");
        small0_7();small8_16();largeCases();actual201Cases();
        equal(24,scenes,"new scenes");equal(22,coreScenes,"core scenes");equal(2,compositionScenes,"actual201 scenes");
        equal(25,budgetEffects,"source loop admissions");equal(8,ntEffects,"distinct NT stores");equal(1,fenceEffects,"source SFENCE");
        equal(1,tails,"raw CPU Tail");equal(3,opaquePorts,"other fullV ports");equal(5,physicalPushes,"actual physical push observations");
        equal(2,fillBindings,"actual201 to206 bindings");
        System.out.println("OK: "+scenes+" new scenes (22 core + 2 actual201), "+budgetEffects+
                " budgets, "+ntEffects+" NT128, "+fenceEffects+" SFENCE; "+assertions+" explicit assertions; lower ports opaque");
    }
}
