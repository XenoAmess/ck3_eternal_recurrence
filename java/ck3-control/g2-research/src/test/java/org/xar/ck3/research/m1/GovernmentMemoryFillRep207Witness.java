package org.xar.ck3.research.m1;

import java.util.ArrayList;
import java.util.List;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Entry;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Tail;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Call;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.TargetKind;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import static org.xar.ck3.research.m1.GovernmentSharedComposition168Fixture.bits;
import static org.xar.ck3.research.m1.GovernmentSharedComposition168Fixture.vector;

/** Independent original16B literals; explicit owned DF, no nativeDF/EH qualification. */
public final class GovernmentMemoryFillRep207Witness {
    private GovernmentMemoryFillRep207Witness() { }
    private static final long B=0x100000000L,S=0xC0000008L,D=0x60001003L,RET=0x11223344778899AAL;
    private static final long DX=0xFEDCBA98765432A7L,R11=0xDEAD123456789033L;
    private static final VolatileBits BASE=bits(0x1000L,0xAAAA000011112222L,D,DX);
    private static final NonvolatileBits N=new NonvolatileBits(
            0x2222000022220000L,0x2222000022220001L,0x2222000022220002L,0x2222000022220003L,
            0x2222000022220004L,0x2222000022220005L,0x2222000022220006L,0x2222000022220007L,
            vector(0x2222000022220008L));
    private static int assertions,scenes,normals,actualConsumers,rejections,forwardings;
    private static int budgets,byteWrites,qwordWrites,qwordReads,flagReads;
    private record Event(String kind,long address,long low,long high) { }
    private record Cell(String width,long address,long value) { }
    private static Event e(String kind,long address,long low) { return new Event(kind,address,low,0L); }
    private static Event ev(String kind,long address,long low,long high) { return new Event(kind,address,low,high); }
    private static Cell b(long address,long expected) { return new Cell("B",address,expected); }
    private static Cell q(long address,long expected) { return new Cell("Q",address,expected); }
    private static void equal(Object expected,Object actual,String label) {
        assertions++;GovernmentSharedComposition168Fixture.equal(expected,actual,label);
    }
    private static VolatileBits state(long ax,long cx,long dx,long r8,long r9,long r10,long r11,Bits128 x0) {
        return new VolatileBits(ax,cx,dx,r8,r9,r10,r11,x0,BASE.xmm1(),BASE.xmm2(),BASE.xmm3(),BASE.xmm4(),BASE.xmm5());
    }
    private static Entry in(long dest,long count) {
        return new Entry(B,S,state(BASE.raxBits(),dest,DX,count,BASE.r9Bits(),BASE.r10Bits(),R11,BASE.xmm0()),N);
    }
    private static NonvolatileBits withRdi(long di) {
        return new NonvolatileBits(N.rbxBits(),N.rbpBits(),N.rsiBits(),di,N.r12Bits(),N.r13Bits(),N.r14Bits(),N.r15Bits(),N.xmm6());
    }
    private static NormalReturn nr(VolatileBits vv,NonvolatileBits nn,long rip) { return new NormalReturn(vv,rip,S+8,nn); }
    private static final class Mem implements GovernmentMemoryFill206Api.Memory {
        final GovernmentSharedComposition168Fixture.MemoryImage raw=new GovernmentSharedComposition168Fixture.MemoryImage();
        final List<Event> events=new ArrayList<>();
        @Override public int readUnsignedByte(long a) { int v=raw.readUnsignedByte(a);events.add(e("R8",a,v));flagReads++;return v; }
        @Override public int readDword(long a) { int v=raw.readDword(a);events.add(e("R32",a,Integer.toUnsignedLong(v)));return v; }
        @Override public long readQword(long a) { long v=raw.readQword(a);events.add(e("R64",a,v));qwordReads++;return v; }
        @Override public Bits128 read128(long a) { Bits128 v=raw.read128(a);events.add(ev("R128",a,v.lowBits(),v.highBits()));return v; }
        @Override public void writeByte(long a,int v) { events.add(e("W8",a,v&255));raw.writeByte(a,v);byteWrites++; }
        @Override public void writeWord(long a,int v) { events.add(e("W16",a,v&65535));raw.writeByte(a,v);raw.writeByte(a+1,v>>>8); }
        @Override public void writeDword(long a,int v) { events.add(e("W32",a,Integer.toUnsignedLong(v)));raw.writeDword(a,v); }
        @Override public void writeQword(long a,long v) { events.add(e("W64",a,v));raw.writeQword(a,v);qwordWrites++; }
        @Override public void write128(long a,Bits128 v) { events.add(ev("W128",a,v.lowBits(),v.highBits()));raw.write128(a,v); }
        @Override public void write128NonTemporal(long a,Bits128 v) { events.add(ev("NT128",a,v.lowBits(),v.highBits()));raw.write128(a,v); }
        @Override public void sfence() { events.add(e("FENCE",0L,0L)); }
        @Override public int lockedXaddDword(long a,int addend) {
            int old=raw.lockedXaddDword(a,addend);events.add(ev("XADD32",a,Integer.toUnsignedLong(addend),Integer.toUnsignedLong(old)));return old;
        }
        GovernmentCrtBoundary185Api.LoopBudget budget() {
            return (header,cursor)->{events.add(e("BUDGET",header,cursor));budgets++;};
        }
    }
    private static Mem seeded() {
        Mem memory=new Mem();
        for (long a=D-4;a<=D+132;a++) memory.raw.writeByte(a,0xA5);
        for (long a=S-9;a<=S+8;a++) memory.raw.writeByte(a,0xA5);
        memory.raw.writeQword(S,RET);return memory;
    }
    /** Fixed-data effect encoding; no DF/count/target-register simulation. */
    private static List<Event> expectedEffects(Entry input,NormalReturn expected,long[] addresses,boolean prefix206) {
        List<Event> effects=new ArrayList<>();
        if (prefix206) effects.add(e("R8",B+0x5C5CBB0L,2L));
        effects.add(e("W64",S-8,input.nonvolatileBits().rdiBits()));
        for (long address:addresses) {effects.add(e("BUDGET",0x4226EF9L,address));effects.add(e("W8",address,0xA7));}
        effects.add(e("R64",S-8,expected.nonvolatileBits().rdiBits()));effects.add(e("R64",S,expected.returnRipBits()));
        return effects;
    }
    private static void after(Mem memory,List<Cell> cells,String name) {
        for (Cell c:cells) {
            long actual;
            if (c.width().equals("B")) actual=memory.raw.readUnsignedByte(c.address());
            else if (c.width().equals("Q")) actual=memory.raw.readQword(c.address());
            else throw new AssertionError("unknown fixture cell width "+c.width());
            equal(c.value(),actual,name+" owned cell "+Long.toHexString(c.address()));
        }
    }
    private static void normal(String name,Entry input,boolean direction,NormalReturn expected,long[] addresses,List<Cell> cells) {
        Mem memory=seeded();
        NormalReturn actual=GovernmentMemoryFillRep207.execute(input,memory,direction,memory.budget());
        equal(expected,actual,name+" full normal return");equal(expectedEffects(input,expected,addresses,false),memory.events,name+" exact effects");
        for (long address:addresses) equal(0xA7,memory.raw.readUnsignedByte(address),name+" actual written byte");
        after(memory,cells,name);scenes++;normals++;
    }
    private static void rejection(String name,Entry input,boolean direction,int rejectAt,List<Event> events,List<Cell> cells) {
        Mem memory=seeded();UnsupportedOperationException sentinel=new UnsupportedOperationException("owned admission rejection");
        int[] calls={0};boolean returned=false,caught=false;
        GovernmentCrtBoundary185Api.LoopBudget budget=(header,cursor)->{
            memory.events.add(e("BUDGET",header,cursor));budgets++;calls[0]++;
            if (calls[0]==rejectAt) throw sentinel;
        };
        try { GovernmentMemoryFillRep207.execute(input,memory,direction,budget);returned=true; }
        catch (UnsupportedOperationException failure) {caught=true;equal(true,failure==sentinel,name+" exact thrown object");}
        equal(true,caught,name+" admission rejected");equal(false,returned,name+" no normal return");
        equal(events,memory.events,name+" exact prethrow effects");after(memory,cells,name);scenes++;rejections++;
    }
    private static GovernmentCrtBoundary185Api.Calls unexpected() {
        return new GovernmentCrtBoundary185Api.Calls() {
            @Override public VolatileBits invoke(Call call) {throw new AssertionError("unexpected normal CALL "+call);}
            @Override public NormalReturn tail(Tail tail) {throw new AssertionError("unexpected tail "+tail);}
            @Override public long readGsQword58() {throw new AssertionError("unexpected GS");}
        };
    }
    private static void actual206(String name,Entry input,NormalReturn expected,long[] addresses,List<Cell> cells) {
        Mem memory=seeded();memory.raw.writeByte(B+0x5C5CBB0L,2);
        var bound=GovernmentMemoryFillRep207Calls.bind(memory,unexpected(),false,memory.budget());
        NormalReturn actual=GovernmentMemoryFill206.execute(input,memory,bound,memory.budget());
        equal(expected,actual,name+" actual206 to207 full return");equal(expectedEffects(input,expected,addresses,true),memory.events,name+" combined actual source effects");
        for (long address:addresses) equal(0xA7,memory.raw.readUnsignedByte(address),name+" real206 to207 byte");
        after(memory,cells,name);scenes++;actualConsumers++;
    }
    private static void forwarding(String name,Tail foreign,Call ordinary) {
        Mem memory=new Mem();int[] counts={0,0,0};
        VolatileBits answerV=bits(0x6000L,0x6000000011112222L,0x3333444455556666L,0x777788889999AAAAL);
        NormalReturn answer=new NormalReturn(bits(0x5000L,0x5000000011112222L,0x2222333344445555L,0x6666777788889999L),
                0xABCDEFFEDCBA9876L,0x1234000056780000L,new NonvolatileBits(
                0x5555000055550000L,0x5555000055550001L,0x5555000055550002L,0x5555000055550003L,
                0x5555000055550004L,0x5555000055550005L,0x5555000055550006L,0x5555000055550007L,vector(0x5555000055550008L)));
        var fallback=new GovernmentCrtBoundary185Api.Calls() {
            @Override public VolatileBits invoke(Call call) {counts[0]++;equal(ordinary,call,name+" full delegated CALL");equal(true,ordinary==call,name+" same CALL object");return answerV;}
            @Override public NormalReturn tail(Tail tail) {counts[1]++;equal(foreign,tail,name+" full delegated tail");equal(true,foreign==tail,name+" same tail object");return answer;}
            @Override public long readGsQword58() {counts[2]++;return 0x76543210ABCDEF01L;}
        };
        var bound=GovernmentMemoryFillRep207Calls.bind(memory,fallback,false,(header,cursor)->{throw new AssertionError(name+" delegated operation used REP budget");});
        NormalReturn tailResult=bound.tail(foreign);equal(answer,tailResult,name+" full delegated return");equal(true,answer==tailResult,name+" same normal return object");
        VolatileBits callResult=bound.invoke(ordinary);equal(answerV,callResult,name+" full delegated V");equal(true,answerV==callResult,name+" same V object");
        equal(0x76543210ABCDEF01L,bound.readGsQword58(),name+" actual GS delegate");
        equal(1,counts[0],name+" CALL count");equal(1,counts[1],name+" tail count");equal(1,counts[2],name+" GS count");
        equal(List.of(),memory.events,name+" no memory effects");scenes++;forwardings++;
    }

    /* Append only complete independently reviewed model methods. */
    private static void basicCases() {
        // ZERO case
        {
            long B = 0x0000000100000000L;
            long S = 0x00000000C0000008L;
            long D = 0x60001003L;
            long DX = 0xFEDCBA98765432A7L;
            long R11 = 0xDEAD123456789033L;
            long RET = 0x11223344778899AAL;
            
            Entry entry = in(D, 0L);
            boolean direction = false;
            
            VolatileBits v = state(R11, 0L, DX, 0L, 0x1009L, 0x100AL, R11, vector(0x1010L));
            NonvolatileBits n = N;
            NormalReturn expected = nr(v, n, RET);
            
            long[] addresses = new long[] {};
            List<Cell> after = List.of(
                b(D, 0xA5L),
                q(S - 8L, 0x2222000022220003L),
                q(S, RET)
            );
            
            normal("ZERO", entry, direction, expected, addresses, after);
        }

        // SHORT_DF0 case
        {
            long B = 0x0000000100000000L;
            long S = 0x00000000C0000008L;
            long D = 0x60001003L;
            long DX = 0xFEDCBA98765432A7L;
            long R11 = 0xDEAD123456789033L;
            long RET = 0x11223344778899AAL;
            
            Entry entry = in(D, 3L);
            boolean direction = false;
            
            VolatileBits v = state(R11, 0L, DX, 3L, 0x1009L, 0x100AL, R11, vector(0x1010L));
            NonvolatileBits n = N;
            NormalReturn expected = nr(v, n, RET);
            
            long[] addresses = new long[] {
                0x0000000060001003L,
                0x0000000060001004L,
                0x0000000060001005L
            };
            List<Cell> after = List.of(
                b(D - 1L, 0xA5L),
                b(D + 3L, 0xA5L),
                q(S - 8L, 0x2222000022220003L),
                q(S, RET)
            );
            
            normal("SHORT_DF0", entry, direction, expected, addresses, after);
        }

        // SHORT_DF1 case
        {
            long B = 0x0000000100000000L;
            long S = 0x00000000C0000008L;
            long D = 0x60001003L;
            long DX = 0xFEDCBA98765432A7L;
            long R11 = 0xDEAD123456789033L;
            long RET = 0x11223344778899AAL;
            
            Entry entry = in(D, 3L);
            boolean direction = true;
            
            VolatileBits v = state(R11, 0L, DX, 3L, 0x1009L, 0x100AL, R11, vector(0x1010L));
            NonvolatileBits n = N;
            NormalReturn expected = nr(v, n, RET);
            
            long[] addresses = new long[] {
                0x0000000060001003L,
                0x0000000060001002L,
                0x0000000060001001L
            };
            List<Cell> after = List.of(
                b(D + 1L, 0xA5L),
                b(D - 3L, 0xA5L),
                q(S - 8L, 0x2222000022220003L),
                q(S, RET)
            );
            
            normal("SHORT_DF1", entry, direction, expected, addresses, after);
        }
    }

    private static void aliasCases() {
        
        normal("SAVED_RDI_ALIAS",
            in(0x00000000C0000000L, 2L),
            false,
            nr(state(0xDEAD123456789033L, 0x0000000000000000L, 0xFEDCBA98765432A7L, 0x0000000000000002L, 0x0000000000001009L, 0x000000000000100AL, 0xDEAD123456789033L, vector(0x1010L)),
               withRdi(0x222200002222A7A7L),
               0x11223344778899AAL),
            new long[] {0x00000000C0000000L, 0x00000000C0000001L},
            List.of(
                q(0x00000000C0000000L, 0x222200002222A7A7L),
                q(0x00000000C0000008L, 0x11223344778899AAL),
                b(0x00000000BFFFFFFFL, 0xA5L),
                b(0x00000000C0000010L, 0xA5L)
            )
        );

        
        normal("RET_ALIAS",
            in(0x00000000C0000009L, 2L),
            false,
            nr(state(0xDEAD123456789033L, 0x0000000000000000L, 0xFEDCBA98765432A7L, 0x0000000000000002L, 0x0000000000001009L, 0x000000000000100AL, 0xDEAD123456789033L, vector(0x1010L)),
               withRdi(0x2222000022220003L),
               0x1122334477A7A7AAL),
            new long[] {0x00000000C0000009L, 0x00000000C000000AL},
            List.of(
                q(0x00000000C0000000L, 0x2222000022220003L),
                q(0x00000000C0000008L, 0x1122334477A7A7AAL),
                b(0x00000000BFFFFFFFL, 0xA5L),
                b(0x00000000C0000010L, 0xA5L)
            )
        );

        
        normal("BACKWARD_STACK_ALIAS",
            in(0x00000000C0000008L, 2L),
            true,
            nr(state(0xDEAD123456789033L, 0x0000000000000000L, 0xFEDCBA98765432A7L, 0x0000000000000002L, 0x0000000000001009L, 0x000000000000100AL, 0xDEAD123456789033L, vector(0x1010L)),
               withRdi(0xA722000022220003L),
               0x11223344778899A7L),
            new long[] {0x00000000C0000008L, 0x00000000C0000007L},
            List.of(
                q(0x00000000C0000000L, 0xA722000022220003L),
                q(0x00000000C0000008L, 0x11223344778899A7L),
                b(0x00000000BFFFFFFFL, 0xA5L),
                b(0x00000000C0000010L, 0xA5L)
            )
        );
    }

    private static void boundaryCases() {
        // Case 1: BUDGET_REJECT
        // Entry construction using fixture helpers
        long B = 0x0000000100000000L;
        long S = 0x00000000C0000008L;
        long D = 0x0000000060001003L;
        long DX = 0xFEDCBA98765432A7L;
        long R11 = 0xDEAD123456789033L;
        
        // V bits from frozen matrix
        long vRax = 0xAAAA000011112222L;
        long vRcx = 0x0000000060001003L;
        long vRdx = 0xFEDCBA98765432A7L;
        long vR8 = 0x0000000000000003L;
        long vR9 = 0x0000000000001009L;
        long vR10 = 0x000000000000100AL;
        long vR11 = 0xDEAD123456789033L;
        
        // XMM0 from frozen matrix (low, high)
        Bits128 xmm0 = new Bits128(0x0000000000001010L, 0xFFFFFFFFFFFFEFEFL);
        
        // N bits from frozen matrix
        long nBx = 0x2222000022220000L;
        long nBp = 0x2222000022220001L;
        long nSi = 0x2222000022220002L;
        long nDi = 0x2222000022220003L;
        long n12 = 0x2222000022220004L;
        long n13 = 0x2222000022220005L;
        long n14 = 0x2222000022220006L;
        long n15 = 0x2222000022220007L;
        Bits128 nXmm6 = new Bits128(0x2222000022220008L, 0xDDDDFFFFDDDDFFF7L);
        
        // Construct Entry
        VolatileBits v = new VolatileBits(vRax, vRcx, vRdx, vR8, vR9, vR10, vR11, 
            xmm0, vector(0x1020L), vector(0x1030L), vector(0x1040L), vector(0x1050L), vector(0x1060L));
        NonvolatileBits n = new NonvolatileBits(nBx, nBp, nSi, nDi, n12, n13, n14, n15, nXmm6);
        Entry entry1 = new Entry(B, S, v, n);
        
        // Events for rejection
        List<Event> events1 = List.of(
            e("W64", 0x00000000C0000000L, 0x2222000022220003L),
            e("BUDGET", 0x0000000004226EF9L, 0x0000000060001003L),
            e("W8", 0x0000000060001003L, 0x00000000000000A7L),
            e("BUDGET", 0x0000000004226EF9L, 0x0000000060001004L)
        );
        
        // After cells
        List<Cell> after1 = List.of(
            b(0x0000000060001002L, 0x00000000000000A5L),
            b(0x0000000060001003L, 0x00000000000000A7L),
            b(0x0000000060001004L, 0x00000000000000A5L),
            b(0x0000000060001005L, 0x00000000000000A5L),
            q(0x00000000C0000000L, 0x2222000022220003L),
            q(0x00000000C0000008L, 0x11223344778899AAL)
        );
        
        // Write address order for normal helper (not used in rejection, but required by signature if we were calling normal)
        // For rejection, we call rejection helper directly.
        rejection("BUDGET_REJECT", entry1, false, 2, events1, after1);

        // Case 2: FOREIGN_KIND_CALL_GS
        // Construct foreign Tail
        long tailSite = 0x0000000004226F57L;
        long tailTarget = 0x0000000004226EF0L;
        TargetKind tailKind = TargetKind.INDIRECT_ABSOLUTE;
        
        // Entry for tail (same as entry1 essentially, but constructed via in() helper if available or manually)
        // The protocol says use in(destination, count) for Entry construction in some cases, 
        // but here we have explicit V/N. Let's construct Entry manually to match frozen data.
        // Actually, the protocol says 'Use its exact Entry in execute207'. The tail entry in the matrix is identical to entry1.
        Entry tailEntry = new Entry(B, S, v, n);
        Tail foreignTail = new Tail(tailSite, tailKind, tailTarget, tailEntry);
        
        // Construct ordinary Call
        long callSite = 0x0000000004226F57L;
        long callTarget = 0x0000000004226EF0L;
        TargetKind callKind = TargetKind.DIRECT_RVA;
        long callPreSP = 0x00000000C0000010L;
        
        // Call V/N are same as entry1
        Call ordinaryCall = new Call(callSite, callKind, callTarget, callPreSP, v, n);
        
        // Forwarding helper
        forwarding("FOREIGN_KIND_CALL_GS", foreignTail, ordinaryCall);
    }

    private static void actual206Case() {
        long B = 0x0000000100000000L;
        long S = 0x00000000C0000008L;
        long D = 0x0000000060001003L;
        long DX = 0xFEDCBA98765432A7L;
        long R11 = 0xDEAD123456789033L;
        long RET = 0x11223344778899AAL;

        Bits128 x0 = new Bits128(0x0000000000001010L, 0xFFFFFFFFFFFFEFEFL);
        Bits128 x1 = new Bits128(0x0000000000001020L, 0xFFFFFFFFFFFFEFDFL);
        Bits128 x2 = new Bits128(0x0000000000001030L, 0xFFFFFFFFFFFFEFCFL);
        Bits128 x3 = new Bits128(0x0000000000001040L, 0xFFFFFFFFFFFFEFBFL);
        Bits128 x4 = new Bits128(0x0000000000001050L, 0xFFFFFFFFFFFFEFAFL);
        Bits128 x5 = new Bits128(0x0000000000001060L, 0xFFFFFFFFFFFFEF9FL);

        VolatileBits v = new VolatileBits(
            0xAAAA000011112222L, D, DX, 0x81L, 0x1009L, 0x100AL, R11,
            x0, x1, x2, x3, x4, x5
        );

        NonvolatileBits n = new NonvolatileBits(
            0x2222000022220000L, 0x2222000022220001L, 0x2222000022220002L, 0x2222000022220003L,
            0x2222000022220004L, 0x2222000022220005L, 0x2222000022220006L, 0x2222000022220007L,
            new Bits128(0x2222000022220008L, 0xDDDDFFFFDDDDFFF7L)
        );

        Entry entry = new Entry(B, S, v, n);

        Bits128 expectedX0 = new Bits128(0xA7A7A7A7A7A7A7A7L, 0xA7A7A7A7A7A7A7A7L);
        VolatileBits expectedV = new VolatileBits(
            D, 0L, 0xA7L, 0x81L, 0xA7A7A7A7A7A7A7A7L, 0x100AL, D,
            expectedX0, x1, x2, x3, x4, x5
        );
        NormalReturn expected = nr(expectedV, n, RET);

        long[] addresses = {
            0x0000000060001003L, 0x0000000060001004L, 0x0000000060001005L, 0x0000000060001006L,
            0x0000000060001007L, 0x0000000060001008L, 0x0000000060001009L, 0x000000006000100AL,
            0x000000006000100BL, 0x000000006000100CL, 0x000000006000100DL, 0x000000006000100EL,
            0x000000006000100FL, 0x0000000060001010L, 0x0000000060001011L, 0x0000000060001012L,
            0x0000000060001013L, 0x0000000060001014L, 0x0000000060001015L, 0x0000000060001016L,
            0x0000000060001017L, 0x0000000060001018L, 0x0000000060001019L, 0x000000006000101AL,
            0x000000006000101BL, 0x000000006000101CL, 0x000000006000101DL, 0x000000006000101EL,
            0x000000006000101FL, 0x0000000060001020L, 0x0000000060001021L, 0x0000000060001022L,
            0x0000000060001023L, 0x0000000060001024L, 0x0000000060001025L, 0x0000000060001026L,
            0x0000000060001027L, 0x0000000060001028L, 0x0000000060001029L, 0x000000006000102AL,
            0x000000006000102BL, 0x000000006000102CL, 0x000000006000102DL, 0x000000006000102EL,
            0x000000006000102FL, 0x0000000060001030L, 0x0000000060001031L, 0x0000000060001032L,
            0x0000000060001033L, 0x0000000060001034L, 0x0000000060001035L, 0x0000000060001036L,
            0x0000000060001037L, 0x0000000060001038L, 0x0000000060001039L, 0x000000006000103AL,
            0x000000006000103BL, 0x000000006000103CL, 0x000000006000103DL, 0x000000006000103EL,
            0x000000006000103FL, 0x0000000060001040L, 0x0000000060001041L, 0x0000000060001042L,
            0x0000000060001043L, 0x0000000060001044L, 0x0000000060001045L, 0x0000000060001046L,
            0x0000000060001047L, 0x0000000060001048L, 0x0000000060001049L, 0x000000006000104AL,
            0x000000006000104BL, 0x000000006000104CL, 0x000000006000104DL, 0x000000006000104EL,
            0x000000006000104FL, 0x0000000060001050L, 0x0000000060001051L, 0x0000000060001052L,
            0x0000000060001053L, 0x0000000060001054L, 0x0000000060001055L, 0x0000000060001056L,
            0x0000000060001057L, 0x0000000060001058L, 0x0000000060001059L, 0x000000006000105AL,
            0x000000006000105BL, 0x000000006000105CL, 0x000000006000105DL, 0x000000006000105EL,
            0x000000006000105FL, 0x0000000060001060L, 0x0000000060001061L, 0x0000000060001062L,
            0x0000000060001063L, 0x0000000060001064L, 0x0000000060001065L, 0x0000000060001066L,
            0x0000000060001067L, 0x0000000060001068L, 0x0000000060001069L, 0x000000006000106AL,
            0x000000006000106BL, 0x000000006000106CL, 0x000000006000106DL, 0x000000006000106EL,
            0x000000006000106FL, 0x0000000060001070L, 0x0000000060001071L, 0x0000000060001072L,
            0x0000000060001073L, 0x0000000060001074L, 0x0000000060001075L, 0x0000000060001076L,
            0x0000000060001077L, 0x0000000060001078L, 0x0000000060001079L, 0x000000006000107AL,
            0x000000006000107BL, 0x000000006000107CL, 0x000000006000107DL, 0x000000006000107EL,
            0x000000006000107FL, 0x0000000060001080L, 0x0000000060001081L, 0x0000000060001082L,
            0x0000000060001083L
        };

        List<Cell> after = List.of(
            b(0x0000000060001002L, 0xA5L),
            b(0x0000000060001084L, 0xA5L),
            q(0x00000000C0000000L, 0x2222000022220003L),
            q(0x00000000C0000008L, RET)
        );

        actual206("ACTUAL206_TO207_129", entry, expected, addresses, after);
    }

    public static void main(String[] args) {
        if (args.length!=0) throw new IllegalArgumentException("manual witness takes no arguments");
        basicCases();aliasCases();boundaryCases();actual206Case();
        equal(9,scenes,"new scenes");equal(6,normals,"normal207 scenes");equal(1,actualConsumers,"actual206 consumer");
        equal(1,rejections,"admission rejection");equal(1,forwardings,"foreign forwarding scene");
        equal(143,budgets,"actual byte admissions");equal(142,byteWrites,"actual byte writes");equal(8,qwordWrites,"mandatory pushes");
        equal(14,qwordReads,"fresh POP and RET reads");equal(1,flagReads,"new206 branch flag read");
        System.out.println("OK: "+scenes+" new scenes (6 normal207 + rejection + forwarding + actual206), "+budgets+
                " budgets, "+byteWrites+" byte stores; "+assertions+" explicit assertions; owned DF only");
    }
}
