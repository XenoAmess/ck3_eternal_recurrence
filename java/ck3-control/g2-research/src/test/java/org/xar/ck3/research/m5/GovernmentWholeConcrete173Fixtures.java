package org.xar.ck3.research.m5;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.OpaqueCall;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155WitnessApi.MemorySeed;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155WitnessApi.SeedByte;
import org.xar.ck3.research.m5.GovernmentWhole4798WitnessApi.BudgetStep;
import org.xar.ck3.research.m5.GovernmentWhole4798WitnessApi.Failure;
import org.xar.ck3.research.m5.GovernmentWhole4798WitnessApi.OrdinaryStep;
import org.xar.ck3.research.m5.GovernmentWhole4798WitnessApi.Phase;
import org.xar.ck3.research.m5.GovernmentWholeConcrete173WitnessApi.AtomicStep;
import org.xar.ck3.research.m5.GovernmentWholeConcrete173WitnessApi.Branch;
import org.xar.ck3.research.m5.GovernmentWholeConcrete173WitnessApi.DeepStep;
import org.xar.ck3.research.m5.GovernmentWholeConcrete173WitnessApi.GsPort;
import org.xar.ck3.research.m5.GovernmentWholeConcrete173WitnessApi.GsStep;
import org.xar.ck3.research.m5.GovernmentWholeConcrete173WitnessApi.HashStep;
import org.xar.ck3.research.m5.GovernmentWholeConcrete173WitnessApi.ResultStep;
import org.xar.ck3.research.m5.GovernmentWholeConcrete173WitnessApi.Witness;

/** Owner literal full-primary book after two source-rejected model rounds. */
public final class GovernmentWholeConcrete173Fixtures implements GovernmentWholeConcrete173WitnessApi.Book {
    private static final long I=0x140000000L,G=0x600000L,S0=0xc00008L,S=0xbfecd0L,B=0xbfedd0L;
    private static final long GS=0x700000L,TLS=0x710000L,C1=0x720000L,C0=0x730000L,ROWS=0x740000L;
    private static final long EARLY=0x750000L,LOOK=0x760000L,T1=0x770000L,T0=0x780000L;
    private static final long HIT1=0x790000L,HIT0=0x7a0000L,ARRAY=0x7b0000L,Q=0x7b0020L;
    private static final long MAGIC=0x7c0000L,TABLE=0x7d0000L,DEF=0x7e0000L,TAIL1=0x7f0000L,TAIL2=0x7f1000L;
    private static final long M=I+0x5dc1390L,LIT=I+0x448d018L,L12=I+0x45d1a30L,L13=I+0x45d26f0L;
    private static final long ROW_LABEL=I+0x48b7dc0L,D1=I+0x46d67b0L,D2=I+0x46d97e8L;
    private static final long RET=0x7ff0173abcdefabcL,RAW=0x969594939291908fL;
    private static final long N1=0x6173000011223344L,N2=0x7173000000000002L;
    private static final Bits128 X0=new Bits128(0x100,0x101),X1=new Bits128(0x110,0x111);
    private static final Bits128 X2=new Bits128(0x120,0x121),X3=new Bits128(0x130,0x131);
    private static final Bits128 X4=new Bits128(0x140,0x141),X5=new Bits128(0x150,0x151);
    private static final Bits128 X6=new Bits128(0x9696000000000006L,0xabab000000000006L);
    private static final NonvolatileBits ORIGINAL=new NonvolatileBits(0xb1b1000000000003L,0xb2b2000000000004L,
            0x5151000000000002L,0xd1d1000000000001L,0x1212000000000012L,0x1313000000000013L,
            0x1414000000000014L,0x1515000000000015L,X6);
    private static final GovernmentLookupLoop580Api.Mxcsr32 MX=new GovernmentLookupLoop580Api.Mxcsr32(0x1f80);
    private static final GovernmentWhole4798Api.AvailableMxcsr INITIAL_FP=new GovernmentWhole4798Api.AvailableMxcsr(MX);
    private static final GovernmentWhole4798Api.AvailableMxcsr FINAL_FP=new GovernmentWhole4798Api.AvailableMxcsr(new GovernmentLookupLoop580Api.Mxcsr32(0x9fc0));

    @Override public List<Witness> witnesses() {
        return List.of(make("whole173-both-real-inline90-unlocked-hits",false,1,0x48ee4298,0x90000001,
                        0xffffffffL,0xfffffffeL,0x3f7e1b0L,Q,0x90),
                make("whole173-both-real-inline2d8000e3-reader-hits",true,4,0xba1efe2f,0,
                        0,2,0x3f7e180L,0x7b0024L,0x2d,0x80,0x00,0xe3));
    }
    private static Witness make(String name,boolean locked,int length,int hash,int packed,long resultR8,
            long resultR11,long hashHeader,long hashEnd,int... data) {
        Seed seed=seed(locked,length,hash,data);
        Bits128 rowDesc=descriptor(ROW_LABEL,0x20,0xa7);
        var initial=initial();
        VolatileBits lookupV=v(LOOK,LIT,0x222,0x333,0x444,0x555,0x666,X0,X1);
        var lookup=new GovernmentLookupLoop580Api.Join(0x30a33c2L,
                new GovernmentCompaction160Api.Entry(I,S,lookupV,n(LOOK,0,0x158,0,TABLE)),MX);
        var earlier=new GovernmentEarlierRows161Api.Join(0x30a35a4L,I,S,lookupV,n(L13,EARLY,EARLY,0,TABLE));
        VolatileBits rowV=v(ROW_LABEL,0,1,resultR8,0,T1,resultR11,rowDesc,X1);
        var rows=new GovernmentRows461Api.Join(0x30a376eL,
                new GovernmentCompaction160Api.Entry(I,S,rowV,n(L13,ROWS+16,ROWS+16,0,G+0x18)));
        VolatileBits compactV=v(ROW_LABEL,0,1,resultR8,EARLY,0,resultR11,rowDesc,X1);
        var compact=new GovernmentCompaction160Api.Join(0x30a38cfL,I,S,compactV,n(0,ROWS+16,ROWS+16,1,0x158));
        var prelude=new GovernmentPreprefix159Api.Entry(I,GovernmentPreprefix159Api.EntryPoint.AT_30A3BBA,S,
                compactV,n(0,G+0x18,ROWS+16,L13,0x158));
        var joined=new GovernmentPreprefix159Api.Join(0x30a3eb3L,I,S,post(N2),n(0,G+0x18,0x158,L13,0x158));
        var tail=new GovernmentPrimaryTail155Api.NormalReturn(0,RET,0xc00010L,ORIGINAL);
        var suffixResult=new GovernmentPrimarySuffix155Api.Result(GovernmentCaller153Api.Outcome.SKIPPED_SIGNED_GUARD,tail);
        var middle=new GovernmentMiddle166Api.Result(compact,prelude,new GovernmentJoined159Api.Result(joined,suffixResult));
        var wholeResult=new GovernmentWhole4798Api.Result(initial,INITIAL_FP,lookup,earlier,rows,middle,FINAL_FP);
        var suffixEntry=new GovernmentPrimarySuffix155Api.Entry(I,G,0x158,G+0x18,1,B,S,L13,0x158,X6);
        var post153=new GovernmentMiddle166WitnessApi.BoundaryStep(suffixEntry,GovernmentCaller153Api.Outcome.SKIPPED_SIGNED_GUARD,
                0x158,new GovernmentPrimarySuffix155Api.AvailableVolatile(post(0xfeed00000000faceL)));
        var whole=new GovernmentWhole4798WitnessApi.Witness(name,input(),seed.memory(),GS,initialCalls(),normalizations(resultR11),
                List.of(),List.of(),List.of(new BudgetStep(Phase.ROWS,0x30a35d0L,ROWS,ROWS+16,false)),
                new GovernmentWhole4798WitnessApi.InitialMxcsrStep(initial,INITIAL_FP),
                new GovernmentWhole4798WitnessApi.FinalMxcsrStep(middle,FINAL_FP),List.of(post153),
                finalBytes(length,packed).m,wholeResult,Failure.NONE);
        List<DeepStep> deep=List.of(new HashStep(Branch.M1_2D1B7F0,hashHeader,Q,length,hashEnd,false),
                new ResultStep(Branch.M1_2D1B7F0,0xabf8b8L,T1,false),
                new HashStep(Branch.M0_2D0B490,hashHeader,Q,length,hashEnd,false),
                new ResultStep(Branch.M0_2D0B490,0x16f4178L,T0,false));
        List<AtomicStep> atomics=new ArrayList<>();
        lookupAtomics(atomics);lookupAtomics(atomics);
        if(locked)readerAtomics(atomics,C1);
        lookupAtomics(atomics);lookupAtomics(atomics);
        if(locked)readerAtomics(atomics,C0);
        return new Witness(whole,new GovernmentLookupLoop580Api.Mxcsr32(0x9fc1),
                new GovernmentLookupLoop580Api.Mxcsr32(0x1fa0),deep,atomics,
                List.of(new GsStep(GsPort.ORDINARY,GS),new GsStep(GsPort.ORDINARY,GS),
                        new GsStep(GsPort.ORDINARY,GS),new GsStep(GsPort.ORDINARY,GS)));
    }
    private static void lookupAtomics(List<AtomicStep> values) {
        values.add(new AtomicStep(32,M+0x48,2,0,2));values.add(new AtomicStep(32,M+0x48,-2,2,0));
    }
    private static void readerAtomics(List<AtomicStep> values,long context) {
        values.add(new AtomicStep(32,context+0xea0,2,0,2));values.add(new AtomicStep(32,context+0xea0,-2,2,0));
    }
    private static GovernmentInitialFrame162Api.Entry input() {
        return new GovernmentInitialFrame162Api.Entry(I,S0,v(0xe173,0x610000,0x222,0x333,0x444,0x555,0x666,X0,X1),ORIGINAL);
    }
    private static GovernmentInitialFrame162Api.Join initial() {
        return new GovernmentInitialFrame162Api.Join(0x30a3162L,I,S,post(0),n(ORIGINAL.rbxBits(),0,0x158,0,TABLE));
    }
    private static NonvolatileBits n(long bx,long si,long r12,long r13,long r14) {
        return new NonvolatileBits(bx,B,si,G,r12,r13,r14,1,X6);
    }
    private static VolatileBits v(long a,long c,long d,long r8,long r9,long r10,long r11,Bits128 x0,Bits128 x1) {
        return new VolatileBits(a,c,d,r8,r9,r10,r11,x0,x1,X2,X3,X4,X5);
    }
    private static VolatileBits post(long a) {return v(a,0x111,0x222,0x333,0x444,0x555,0x666,X0,X1);}
    private static Bits128 descriptor(long label,int length,int pad) {
        return new Bits128(label,((long)pad<<56)|((long)pad<<48)|((long)pad<<40)|Integer.toUnsignedLong(length));
    }
    private static OrdinaryStep ordinary(long site,long target,VolatileBits before,NonvolatileBits nv,
            Map<Long,Integer> bytes,List<SeedByte> mutation,VolatileBits after) {
        return new OrdinaryStep(new OpaqueCall(site,target,S,before,nv),bytes,mutation,after,false);
    }
    private static List<OrdinaryStep> initialCalls() {
        NonvolatileBits pushed=new NonvolatileBits(ORIGINAL.rbxBits(),B,ORIGINAL.rsiBits(),ORIGINAL.rdiBits(),
                ORIGINAL.r12Bits(),ORIGINAL.r13Bits(),ORIGINAL.r14Bits(),ORIGINAL.r15Bits(),X6);
        var probe=new OrdinaryStep(new OpaqueCall(0x30a2f2aL,0x42247b0L,S0-64,
                v(0x12f8,0x610000,0x222,0x333,0x444,0x555,0x666,X0,X1),pushed),savedPushes().m,List.of(),
                v(0x12f8,G,0x222,0x333,0x444,0x555,0x666,X0,X1),false);
        Bits128 desc=new Bits128(I+0x9d09e0L,0),scalar=new Bits128(RAW,0);
        VolatileBits before=v(I+0x9d09e0L,TABLE,TABLE,B+0xe0,0x444,0x555,0x666,desc,scalar);
        NonvolatileBits nv=new NonvolatileBits(ORIGINAL.rbxBits(),B,0,G,ORIGINAL.r12Bits(),0,TABLE,TABLE,X6);
        Map<Long,Integer> bytes=new Seed().x(S+0x12e0,X6).x(B+0xe0,desc).q(B+0xf0,RAW).d(G+0x48,0).m;
        return List.of(probe,ordinary(0x30a2fe7L,0x2be3690L,before,nv,bytes,List.of(),post(0xa173)));
    }
    private static List<OrdinaryStep> normalizations(long r11) {
        NonvolatileBits nv=n(0,G+0x18,L12,L13,0x158);
        Bits128 d1=descriptor(D1,0x18,0xc5),d2=descriptor(D2,0x1b,0xc6);
        return List.of(ordinary(0x30a3e67L,0x30a2cc0L,
                        v(D1,G,B+0x1a0,0x29,0,T0,r11,d1,X1),nv,
                        new Seed().desc(B+0x1a0,D1,0x18,0xc5).m,
                        new Seed().d(G+0x4c8,0xf0000001).bytes(),post(N1)),
                ordinary(0x30a3ea5L,0x30a2cc0L,
                        v(D2,G,B+0x1b0,0xf0000001L,0x444,0x555,0x666,d2,X1),nv,
                        new Seed().desc(B+0x1b0,D2,0x1b,0xc6).m,List.of(),post(N2)));
    }
    private static Seed seed(boolean locked,int length,int hash,int... data) {
        Seed s=new Seed().fill(S-0x80,0x13e0,0xcc).q(S0,RET).q(S+0x50,RAW)
                .d(G+0x48,-7).q(G+0x418,MAGIC).d(MAGIC+0x38,0).q(G+0x420,TABLE).d(G+0x42c,0).d(G+0x4bc,0)
                .q(G+0x498,LOOK).d(G+0x4a4,0).q(G+0x450,EARLY).d(G+0x45c,0).q(G+0x468,ROWS).d(G+0x474,1)
                .q(I+0x5d1e388,DEF).b(DEF+0x1520,1).b(G+0x7fc,0).b(G+0x80c,0).b(G+0x81c,0)
                .q(I+0x5c67190,C1).q(I+0x5d21358,C0).q(G+0x820,0x1730000000000001L)
                .d(G+0x828,1).d(G+0x82c,0xd4e5f601).b(G+0xdb4,0).d(G+0x4cc,0x29).d(G+0x4c8,0x2a).d(G+0x4d0,2)
                .q(ROWS,0x1730000000000002L).d(ROWS+8,1).d(ROWS+12,0xa1b2c301)
                .fill(B-0x50,16,0xa7).fill(B+0x50,16,0xc5).fill(B+0x60,16,0xc6)
                .q(GS,TLS).d(TLS+0x10,5).b(TLS+0x158,1).d(I+0x5dc1388,-3)
                .q(M+0x30,ARRAY).d(M+0x3c,2).d(M+0x48,0).fill(Q,32,0xa9).q(Q+0x10,length).q(Q+0x18,15)
                .d(I+0x54582e4,5).d(G+0xd98,4).b(G+0x4d7,0)
                .q(G+0xdb8,TAIL1).d(G+0xdc4,0).q(G+0xdd0,TAIL2).d(G+0xddc,0).q(G+0x40,0);
        for(int j=0;j<data.length;j++)s.b(Q+j,data[j]);
        context(s,C1,T1,HIT1,locked,hash);context(s,C0,T0,HIT0,locked,hash);
        return s;
    }
    private static void context(Seed s,long context,long table,long hit,boolean locked,int hash) {
        s.q(context+0x180,table).d(context+0x18c,0).b(context+0x190,0x5a).b(context+0xee0,locked?0:1)
                .d(context+0xea0,0).fill(table,24,0x7b).b(table+4,1).d(table+8,hash).q(table+0x10,hit).d(hit+0x38,0x4744624f);
    }
    private static Seed savedPushes() {
        return new Seed().q(S0-8,ORIGINAL.rbpBits()).q(S0-16,ORIGINAL.rbxBits()).q(S0-24,ORIGINAL.rsiBits())
                .q(S0-32,ORIGINAL.rdiBits()).q(S0-40,ORIGINAL.r12Bits()).q(S0-48,ORIGINAL.r13Bits())
                .q(S0-56,ORIGINAL.r14Bits()).q(S0-64,ORIGINAL.r15Bits());
    }
    private static Seed finalBytes(int length,int packed) {
        Seed s=savedPushes().x(S+0x12e0,X6).d(B+0x1240,0).d(G+0x48,0)
                .q(S+0x40,I+0x9d09e0).q(S+0x48,0).x(B+0xe0,new Bits128(I+0x9d09e0,0)).q(B+0xf0,RAW)
                .q(S+0x68,LOOK).desc(B-0x50,ROW_LABEL,0x20,0xa7).desc(B+0xa0,ROW_LABEL,0x20,0xa7)
                .q(ROWS,HIT1).b(ROWS+12,2).q(G+0x820,HIT0).b(G+0x82c,2)
                .q(S-0x68,I+0x3f7e24b).q(S-0x60,length).q(S-0x58,C0).q(S-0x50,G+0x820).q(S-0x48,0x158)
                .q(S-0x40,1).q(S-0x38,I+0x2d0b50d).q(S-0x30,1).d(S-0x20,packed)
                .q(S-0x10,G).q(S-8,I+0x30a3c17).q(S,0).q(S+8,G+0x18)
                .desc(B+0x50,D1,0x18,0xc5).desc(B+0x1a0,D1,0x18,0xc5)
                .desc(B+0x60,D2,0x1b,0xc6).desc(B+0x1b0,D2,0x1b,0xc6)
                .d(G+0x4cc,0x11223344).d(G+0x4c8,2);
        return s;
    }
    private static final class Seed {
        final Map<Long,Integer> m=new LinkedHashMap<>();
        Seed b(long a,int value){m.put(a,value&255);return this;}
        Seed d(long a,int value){for(int j=0;j<4;j++)b(a+j,value>>>(8*j));return this;}
        Seed q(long a,long value){for(int j=0;j<8;j++)b(a+j,(int)(value>>>(8*j)));return this;}
        Seed fill(long a,int length,int value){for(int j=0;j<length;j++)b(a+j,value);return this;}
        Seed x(long a,Bits128 value){return q(a,value.lowBits()).q(a+8,value.highBits());}
        Seed desc(long a,long label,int length,int pad){return fill(a,16,pad).q(a,label).d(a+8,length).b(a+12,0);}
        List<SeedByte> bytes(){return m.entrySet().stream().map(e->new SeedByte(e.getKey(),e.getValue())).toList();}
        MemorySeed memory(){return new MemorySeed(bytes());}
    }
}
