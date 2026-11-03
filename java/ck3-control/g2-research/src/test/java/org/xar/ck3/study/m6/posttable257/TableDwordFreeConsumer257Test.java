package org.xar.ck3.study.m6.posttable257;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.KnownAllocateErrorFp625;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.study.m6.posterror256.Error32PostState256;
import org.xar.ck3.study.m6.posterror256.FreeKnownError256;
import org.xar.ck3.study.m6.postfree251.FreePostState251;
import org.xar.ck3.study.m6.postfree251.FreePostState251Api;
import org.xar.ck3.study.m6.poststate240.PostState240Api;

/**
 * One source-only new consumer witness, derived before any257 candidate implementation was read.
 * TableDwordLeaf257/FreeKnownTable257 refer to the parent's fixed future public output contracts;
 * those sources/classes were NOT_HELD when this manual was authored. No shadow implementation.
 * Opaque child Outcomes/RAM effects and all table values are explicit artificial protocol inputs.
 */
public final class TableDwordFreeConsumer257Test {
    private static final long IMAGE=0x140000000L, S=0x9008L, P=0x8FE0L, C=0x8FD8L;
    private static final long INNER_PRE=0x8FB0L, INNER_CHILD=0x8FA8L;
    private static final long BLOCK=0xB100L, HEAP=0xB2570000L, CELL=0x7000L;
    private static final long FIRST_TARGET=0x70000000E2570001L, THIRD_TARGET=0x70000000E2570003L;
    private static final long TABLE=IMAGE+0x4423A60L;
    private static final long SAVED_RBX=0x1020304050607080L;
    private static final long FRESH_RBX=0x0F0E0D0C0B0A0908L;
    private static final long OLD_RET=0x1111222233334444L, FRESH_RET=0x123456789ABCDEF0L;
    private static final long ROOT_ORIGIN=0x2570ABCDL;
    private static final QueueFp604Api.Mxcsr MX0=new QueueFp604Api.Mxcsr(0x1000,0xF0F0);
    private static final QueueFp604Api.Mxcsr MX1=new QueueFp604Api.Mxcsr(0x00A5,0x00FF);
    private static final QueueFp604Api.Mxcsr MX2=new QueueFp604Api.Mxcsr(0x0202,0x0F0F);
    private static final QueueFp604Api.Mxcsr MX3=new QueueFp604Api.Mxcsr(0x0041,0x00C1);
    private static final NonvolatileBits N0=n(SAVED_RBX), NC=n(CELL), NF=n(FRESH_RBX);
    private static final VolatileBits V0=v(0x10,0xDEADBEEF87654321L,BLOCK,
            0xD000000000000000L,0x8000000000000000L,0x9000000000000000L);
    private static final VolatileBits FIRST_INPUT=v(0x10,0L,HEAP,0L,BLOCK,0x9000000000000000L);
    private static final VolatileBits V1=v(0x21,0xABCDEF1200000000L,0x1111222233334444L,
            0x2222333344445555L,0x3333444455556666L,0x4444555566667777L);
    private static final VolatileBits V2=v(0x32,0x6FE0L,0x5152535455565758L,
            0x6162636465666768L,0x7172737475767778L,0x8182838485868788L);
    private static final VolatileBits AFTER_ERROR=v(0x32,CELL,0x5152535455565758L,
            0x6162636465666768L,0x7172737475767778L,0x8182838485868788L);
    private static final VolatileBits V3=v(0x43,0x76543210F1234567L,0xFEDCBA9876543210L,
            0x9192939495969798L,0xA1A2A3A4A5A6A7A8L,0xB1B2B3B4B5B6B7B8L);
    private static final VolatileBits TABLE_INPUT=v(0x43,0x76543210F1234567L,0xF1234567L,
            0x9192939495969798L,0xA1A2A3A4A5A6A7A8L,0xB1B2B3B4B5B6B7B8L);
    private static final VolatileBits TABLE_POST=v(0x43,0x89ABCDEFL,0xF1234567L,TABLE+0x10L,8L,TABLE);

    private TableDwordFreeConsumer257Test() { }

    public static void main(String[] args) {
        if(args.length>1 || (args.length==1
                && !args[0].equals("whole251FourthCallThroughActualError32")))
            throw new IllegalArgumentException("Exactly the one new whole251 consumer selector");
        whole251FourthCallThroughActualError32();
    }

    public static void whole251FourthCallThroughActualError32() {
        Ram ram=new Ram();
        ram.seed64(S,OLD_RET);
        ram.seed64(S+0x10L,0xA1B2C3D4FFFFFFFFL);
        ram.seed64(CELL,0xCAFEBABE11223344L);
        ram.seed64(IMAGE+0x5C5DE30L,HEAP);
        ram.seed64(IMAGE+0x43DA748L,FIRST_TARGET);
        ram.seed64(IMAGE+0x43DA738L,THIRD_TARGET);
        ram.seed32(TABLE,0x01111111);
        ram.seed32(TABLE+8L,0x02222222);
        ram.seed32(TABLE+0x10L,0xF1234567);
        ram.seed32(TABLE+0x14L,0x89ABCDEF);
        Counts counts=new Counts();
        List<Long> reachedSites=new ArrayList<>();
        FreePostState251Api.AlreadyPushedCallFrame[] activeFrame={null};
        QueueFp604Api.Outcome[] errorOffer={null},tableOffer={null};

        KnownAllocateErrorFp625.ErrorCalls fc74=frame -> {
            counts.fc74++;
            eq(counts.fc74,1,"FC74 exactly once");
            reachedSites.add(0x423B190L);
            var call=frame.original();
            eq(call.callSiteRva(),0x423B190L,"actual inner CALL site");
            eq(call.kind(),GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,"inner CALL kind");
            eq(call.targetBits(),0x424FC74L,"inner CALL target");
            eq(call.rspBits(),INNER_PRE,"inner pre-CALL SP");
            eq(call.volatileBits(),V1,"inner full V");
            eq(call.nonvolatileBits(),N0,"inner full N");
            entry(frame.childEntry(),INNER_CHILD,V1,N0,"inner child");
            eq(frame.directionFlagSet(),true,"inner incoming DF");
            eq(frame.preMxcsr(),MX1,"inner incoming partial MXCSR");
            eq(frame.returnRipBits(),IMAGE+0x423B195L,"inner actual RET address");
            eq(ram.peek64(INNER_CHILD),IMAGE+0x423B195L,"single already-owned inner push");
            ram.expectPrefix(8);
            // Explicit opaque complete outcome; no fabricated FC74 kernel/RET implementation.
            return normal(V2,N0,false,MX2,IMAGE+0x423B195L,INNER_PRE);
        };
        PostState240Api.EntryExecutor actualError=new Error32PostState256(fc74);
        PostState240Api.EntryExecutor watchedError=(input,memory) -> {
            counts.generic++;
            eq(counts.generic,1,"generic32 exactly once");
            same(memory,ram,"generic must consume caller RAM");
            same(input,activeFrame[0].childInput(),"error binder must pass original child Input");
            input(input,C,V1,N0,true,MX1,0x424E384L,"generic entry");
            ram.expectPrefix(7);
            QueueFp604Api.Outcome offered=actualError.execute(input,memory);
            fullNormal(offered,AFTER_ERROR,N0,false,MX2,IMAGE+0x424E389L,P,"generic complete post");
            ram.expectPrefix(9);
            errorOffer[0]=offered;
            return offered;
        };

        // These are fixed future output contracts, not locally implemented substitutes.
        PostState240Api.EntryExecutor actualTable=new TableDwordLeaf257();
        PostState240Api.EntryExecutor watchedTable=(input,memory) -> {
            counts.table++;
            eq(counts.table,1,"actual table leaf exactly once");
            same(memory,ram,"table must consume caller RAM");
            same(input,activeFrame[0].childInput(),"table binder must pass original child Input");
            input(input,C,TABLE_INPUT,NC,true,MX3,0x424E394L,"table entry");
            eq(ram.peek64(C),IMAGE+0x424E399L,"caller already owns fourth push");
            ram.expectPrefix(14);
            QueueFp604Api.Outcome offered=actualTable.execute(input,memory);
            QueueFp604Api.Normal returned=fullNormal(offered,TABLE_POST,NC,true,MX3,
                    IMAGE+0x424E399L,P,"table complete post");
            // Additional explicit future core contract: same supplied partial-MXCSR object.
            same(returned.postMxcsr(),input.mxcsr(),"table must retain supplied partial knowledge object");
            ram.expectPrefix(19);
            tableOffer[0]=offered;
            return offered;
        };

        FreePostState251Api.Children explicitOpaque=(frame,memory) -> {
            same(memory,ram,"opaque must receive caller RAM");
            same(frame,activeFrame[0],"unmatched table/error routes must retain original frame");
            long site=frame.call().callSiteRva();
            if(site==0x424E37AL) {
                counts.opaque++;
                ram.expectPrefix(6);
                return normal(V1,N0,true,MX1,IMAGE+0x424E380L,P);
            }
            if(site==0x424E38CL) {
                counts.opaque++;
                ram.expectPrefix(11);
                // Explicit supplier effects, not Memory callbacks that manufacture a table path.
                ram.writeQword(S-8L,FRESH_RBX);
                ram.writeQword(S,FRESH_RET);
                return normal(V3,NC,true,MX3,IMAGE+0x424E392L,P);
            }
            throw new AssertionError("No opaque implementation for actual site "+Long.toHexString(site));
        };
        FreePostState251Api.Children bound=FreeKnownTable257.bind(watchedTable,
                FreeKnownError256.bind(watchedError,explicitOpaque));
        FreePostState251Api.Children audited=(frame,memory) -> {
            same(memory,ram,"whole child RAM identity");
            int ordinal=++counts.wholeCalls;
            long site=switch(ordinal) {
                case 1 -> 0x424E37AL;
                case 2 -> 0x424E384L;
                case 3 -> 0x424E38CL;
                case 4 -> 0x424E394L;
                default -> throw new AssertionError("Unexpected fifth whole61 CALL");
            };
            reachedSites.add(site);
            VolatileBits expectedV=switch(ordinal) {
                case 1 -> FIRST_INPUT;
                case 2 -> V1;
                case 3 -> AFTER_ERROR;
                default -> TABLE_INPUT;
            };
            NonvolatileBits expectedN=ordinal<=2?N0:NC;
            boolean expectedDf=ordinal==2 || ordinal==4;
            QueueFp604Api.Mxcsr expectedMx=switch(ordinal) {
                case 1 -> MX0;
                case 2 -> MX1;
                case 3 -> MX2;
                default -> MX3;
            };
            int length=(ordinal==1 || ordinal==3)?6:5;
            long target=switch(ordinal) {
                case 1 -> FIRST_TARGET;
                case 2 -> 0x423B18CL;
                case 3 -> THIRD_TARGET;
                default -> 0x423B0D4L;
            };
            var kind=(ordinal==1 || ordinal==3)
                    ?GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE
                    :GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA;
            eq(frame.ownerEntryRva(),0x424E364L,"whole61 source owner");
            eq(frame.imageBaseBits(),IMAGE,"whole61 image");
            eq(frame.call().callSiteRva(),site,"whole61 actual site");
            eq(frame.call().kind(),kind,"whole61 actual kind");
            eq(frame.call().targetBits(),target,"whole61 actual target");
            eq(frame.call().rspBits(),P,"whole61 pre-CALL SP");
            eq(frame.call().volatileBits(),expectedV,"whole61 full call V");
            eq(frame.call().nonvolatileBits(),expectedN,"whole61 full call N");
            eq(frame.instructionLength(),length,"whole61 actual instruction length");
            eq(frame.returnRipBits(),IMAGE+site+length,"whole61 actual return RIP");
            input(frame.childInput(),C,expectedV,expectedN,expectedDf,expectedMx,site,"whole61 child");
            eq(ram.peek64(C),IMAGE+site+length,"actual unique caller RET write");
            activeFrame[0]=frame;
            QueueFp604Api.Outcome offered=bound.invoke(frame,memory);
            if(ordinal==2)same(offered,errorOffer[0],"error binder must forward complete offered object");
            if(ordinal==4)same(offered,tableOffer[0],"table binder must forward complete offered object");
            return offered;
        };
        PostState240Api.Input root=new PostState240Api.Input(
                new GovernmentCrtBoundary185Api.Entry(IMAGE,S,V0,N0),false,MX0,ROOT_ORIGIN);
        QueueFp604Api.Outcome result=new FreePostState251(audited).execute(root,ram);
        fullNormal(result,TABLE_POST,NF,true,MX3,FRESH_RET,S+8L,"whole251 final complete state");
        eq(counts.wholeCalls,4,"four actual whole61 CALLs");
        eq(counts.opaque,2,"only first/third use opaque normal suppliers");
        eq(counts.generic,1,"one actual generic32 entry");
        eq(counts.fc74,1,"one explicit FC74 fullOutcome");
        eq(counts.table,1,"one actual table entry");
        eq(reachedSites,List.of(0x424E37AL,0x424E384L,0x423B190L,0x424E38CL,0x424E394L),
                "actual nested call order");
        ram.expectPrefix(22);
        eq(ram.peek64(CELL),0xCAFEBABE89ABCDEFL,"61 stores DWORD only");
        eq(ram.peek64(S+0x10L),0xA1B2C3D400000000L,"17-byte home DWORD preserves high bytes");
        eq(ram.peek64(S-8L),FRESH_RBX,"saved RBX RAM changed by explicit supplier");
        eq(ram.peek64(S),FRESH_RET,"fresh root RET RAM");
        eq(ram.peek64(C),IMAGE+0x424E399L,"last outer RET slot");
        eq(ram.peek64(INNER_CHILD),IMAGE+0x423B195L,"single inner RET slot");
    }

    private static VolatileBits v(long e,long a,long c,long d,long r8,long r9) {
        return new VolatileBits(a,c,d,r8,r9,0x1000000000000000L+e,0x1100000000000000L+e,
                x(e,0),x(e,1),x(e,2),x(e,3),x(e,4),x(e,5));
    }
    private static Bits128 x(long e,long lane) {
        return new Bits128(0x2000000000000000L+0x100L*e+lane,
                0x3000000000000000L+0x100L*e+lane);
    }
    private static NonvolatileBits n(long rbx) {
        return new NonvolatileBits(rbx,0xB0B1B2B3B4B5B6B7L,0xC0C1C2C3C4C5C6C7L,
                0xD0D1D2D3D4D5D6D7L,0xE0E1E2E3E4E5E6E7L,0x8182838485868788L,
                0x9192939495969798L,0xA1A2A3A4A5A6A7A8L,
                new Bits128(0x6A6B6C6D6E6F7071L,0x7A7B7C7D7E7F8081L));
    }
    private static QueueFp604Api.Normal normal(VolatileBits v,NonvolatileBits n,boolean df,
            QueueFp604Api.Mxcsr mx,long ret,long callerSp) {
        return new QueueFp604Api.Normal(new FullCopy437Api.CallResult(
                new GovernmentCrtBoundary185Api.NormalReturn(v,ret,callerSp,n),df),mx);
    }
    private static QueueFp604Api.Normal fullNormal(QueueFp604Api.Outcome outcome,VolatileBits v,
            NonvolatileBits n,boolean df,QueueFp604Api.Mxcsr mx,long ret,long callerSp,String label) {
        if(!(outcome instanceof QueueFp604Api.Normal result))throw new AssertionError(label+": expected Normal");
        eq(result,normal(v,n,df,mx,ret,callerSp),label);
        return result;
    }
    private static void entry(GovernmentCrtBoundary185Api.Entry actual,long sp,VolatileBits v,
            NonvolatileBits n,String label) {
        eq(actual,new GovernmentCrtBoundary185Api.Entry(IMAGE,sp,v,n),label);
    }
    private static void input(PostState240Api.Input actual,long sp,VolatileBits v,NonvolatileBits n,
            boolean df,QueueFp604Api.Mxcsr mx,long origin,String label) {
        entry(actual.entry(),sp,v,n,label+" all represented registers");
        eq(actual.directionFlagSet(),df,label+" DF");
        eq(actual.mxcsr(),mx,label+" partial MXCSR");
        eq(actual.originCallSiteRva(),origin,label+" actual origin");
    }
    private static void eq(Object actual,Object expected,String label) {
        if(!Objects.equals(actual,expected))throw new AssertionError(label+": actual="+actual+", expected="+expected);
    }
    private static void same(Object actual,Object expected,String label) {
        if(actual!=expected)throw new AssertionError(label);
    }
    private static final class Counts { int wholeCalls,opaque,generic,fc74,table; }
    private record Access(String op,long address,long bits) { }

    /** Byte-addressed artificial RAM. Observer peeks do not execute machine Memory operations. */
    private static final class Ram implements GovernmentCrtBoundary185Api.Memory {
        private final Map<Long,Integer> bytes=new HashMap<>();
        private final List<Access> trace=new ArrayList<>();
        private static final List<Access> EXPECTED=List.of(
                new Access("W32",S+0x10L,0L),
                new Access("R32",S+0x10L,0L),
                new Access("W64",S-8L,SAVED_RBX),
                new Access("R64",IMAGE+0x5C5DE30L,HEAP),
                new Access("R64",IMAGE+0x43DA748L,FIRST_TARGET),
                new Access("W64",C,IMAGE+0x424E380L),
                new Access("W64",C,IMAGE+0x424E389L),
                new Access("W64",INNER_CHILD,IMAGE+0x423B195L),
                new Access("R64",C,IMAGE+0x424E389L),
                new Access("R64",IMAGE+0x43DA738L,THIRD_TARGET),
                new Access("W64",C,IMAGE+0x424E392L),
                new Access("W64",S-8L,FRESH_RBX),
                new Access("W64",S,FRESH_RET),
                new Access("W64",C,IMAGE+0x424E399L),
                new Access("R32",TABLE,0x01111111L),
                new Access("R32",TABLE+8L,0x02222222L),
                new Access("R32",TABLE+0x10L,0xF1234567L),
                new Access("R32",TABLE+0x14L,0x89ABCDEFL),
                new Access("R64",C,IMAGE+0x424E399L),
                new Access("W32",CELL,0x89ABCDEFL),
                new Access("R64",S-8L,FRESH_RBX),
                new Access("R64",S,FRESH_RET));
        private void store(long address,long value,int count) {
            for(int i=0;i<count;i++)bytes.put(address+i,(int)(value>>>(i*8))&0xFF);
        }
        private long load(long address,int count) {
            long result=0L;
            for(int i=0;i<count;i++) {
                Integer b=bytes.get(address+i);
                if(b==null)throw new AssertionError("Unspecified artificial RAM byte "+Long.toHexString(address+i));
                result|=(long)b<<(i*8);
            }
            return result;
        }
        private void event(String operation,long address,long value) {
            Access actual=new Access(operation,address,value);
            int index=trace.size();
            if(index>=EXPECTED.size() || !actual.equals(EXPECTED.get(index)))
                throw new AssertionError("RAM event "+(index+1)+": actual="+actual
                        +", expected="+(index<EXPECTED.size()?EXPECTED.get(index):"no additional effect"));
            trace.add(actual);
        }
        private void seed64(long a,long value) { store(a,value,8); }
        private void seed32(long a,int value) { store(a,Integer.toUnsignedLong(value),4); }
        private long peek64(long a) { return load(a,8); }
        private void expectPrefix(int count) {
            eq(trace,EXPECTED.subList(0,count),"complete RAM prefix of "+count+" events");
        }
        @Override public int readDword(long a) {
            long value=load(a,4);event("R32",a,value);return (int)value;
        }
        @Override public long readQword(long a) {
            long value=load(a,8);event("R64",a,value);return value;
        }
        @Override public void writeDword(long a,int value) {
            event("W32",a,Integer.toUnsignedLong(value));store(a,Integer.toUnsignedLong(value),4);
        }
        @Override public void writeQword(long a,long value) {
            event("W64",a,value);store(a,value,8);
        }
        @Override public int readUnsignedByte(long a) { throw new AssertionError("Unexpected byte read"); }
        @Override public void writeByte(long a,int b) { throw new AssertionError("Unexpected byte write"); }
        @Override public int lockedXaddDword(long a,int add) { throw new AssertionError("Unexpected locked operation"); }
        @Override public Bits128 read128(long a) { throw new AssertionError("Unexpected vector read"); }
        @Override public void write128(long a,Bits128 v) { throw new AssertionError("Unexpected vector write"); }
    }
}
