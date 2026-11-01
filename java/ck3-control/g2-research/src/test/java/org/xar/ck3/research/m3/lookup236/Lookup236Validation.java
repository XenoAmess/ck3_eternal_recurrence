package org.xar.ck3.research.m3.lookup236;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m3.lookup221.ModuleLookup221Api;
import org.xar.ck3.research.m3.lookup221.ModuleLookup42422D0;

public final class Lookup236Validation {
    private Lookup236Validation() { }
    private static int fixturesDone;
    private static int targetMemory;
    private static int opaqueMemory;
    private static int portsObserved;
    private static int suppliersObserved;

    @FunctionalInterface
    private interface Action {
        void run(Fixture owner, ModuleLookup221Api.Memory callbackMemory, long[] callbackArguments);
    }
    private record Step(String kind, ModuleLookup221Api.Memory memory, long result,
                        Action action, RuntimeException failure, long[] arguments) { }

    private static final class Fixture implements ModuleLookup221Api.Memory,
            ModuleLookup221Api.Ports, Lookup236Api.DispatchSupplier {
        private final Map<Long,Integer> bytes = new HashMap<>();
        private final List<Step> expected = new ArrayList<>();
        private int cursor;
        private int pMemory;
        private int cMemory;
        private int portCount;
        private int supplierCount;
        private boolean opaque;
        private boolean finished;

        Fixture() { }
        void seed64(long address, long value) {
            for (int i=0;i<8;i++) bytes.put(address+i,(int)(value >>> (i*8)) & 255);
        }
        void seedBytes(long address, int... values) {
            for (int i=0;i<values.length;i++) {
                if ((values[i] & ~255) != 0) throw new AssertionError("seed byte range");
                bytes.put(address+i,values[i]);
            }
        }
        int peek8(long address) {
            Integer value=bytes.get(address);
            if (value==null) throw new AssertionError("unregistered byte " + Long.toHexString(address));
            return value;
        }
        private long peek(long address,int width) {
            long value=0;
            for (int i=0;i<width;i++) value |= ((long)peek8(address+i)) << (i*8);
            return value;
        }
        long peek64(long address) { return peek(address,8); }
        void expectMemory(String kind,long address,long value) {
            expected.add(new Step(kind,this,0L,null,null,new long[]{address,value}));
        }
        void expectPort(String kind,ModuleLookup221Api.Memory memoryIdentity,long returnBits,
                        Action actionOrNull,RuntimeException exceptionOrNull,long... arguments) {
            expected.add(new Step(kind,memoryIdentity,returnBits,actionOrNull,exceptionOrNull,arguments.clone()));
        }
        private Step take(String kind,ModuleLookup221Api.Memory memory,long... arguments) {
            if (finished || cursor==expected.size()) throw new AssertionError("unexpected " + kind + Arrays.toString(arguments));
            Step step=expected.get(cursor++);
            if (!step.kind().equals(kind) || step.memory()!=memory || !Arrays.equals(step.arguments(),arguments)) {
                throw new AssertionError("step " + (cursor-1) + " wanted " + step.kind() + Arrays.toString(step.arguments())
                        + " got " + kind + Arrays.toString(arguments) + " identity=" + (step.memory()==memory));
            }
            return step;
        }
        private void memoryEvent(String operation,long address,long value) {
            take((opaque ? "C." : "P.")+operation,this,address,value);
            if (opaque) cMemory++; else pMemory++;
        }
        @Override public long readPointer(long address) {
            long value=peek(address,8); memoryEvent("R64",address,value); return value;
        }
        @Override public void writeInt64(long address,long value) {
            memoryEvent("W64",address,value); seed64(address,value);
        }
        @Override public int readInt32(long address) {
            int value=(int)peek(address,4); memoryEvent("R32",address,Integer.toUnsignedLong(value)); return value;
        }
        @Override public void writeInt32(long address,int value) {
            memoryEvent("W32",address,Integer.toUnsignedLong(value));
            for (int i=0;i<4;i++) bytes.put(address+i,(value >>> (i*8)) & 255);
        }
        private long port(String kind,ModuleLookup221Api.Memory memory,long... arguments) {
            Step step=take(kind,memory,arguments); portCount++;
            if (kind.equals("SUP")) supplierCount++;
            boolean previous=opaque; opaque=true;
            try {
                if (step.action()!=null) step.action().run(this,memory,arguments.clone());
                if (step.failure()!=null) throw step.failure();
                return step.result();
            } finally { opaque=previous; }
        }
        @Override public int call43da458(ModuleLookup221Api.Memory memory,long siteRva,long codeTarget,long rcx,long rdx,long r8) {
            return (int)port("F458",memory,siteRva,codeTarget,rcx,rdx,r8);
        }
        @Override public long call43da680(ModuleLookup221Api.Memory memory,long siteRva,long codeTarget,long rcx,long rdx) {
            return port("F680",memory,siteRva,codeTarget,rcx,rdx);
        }
        @Override public void call43dbba8(ModuleLookup221Api.Memory memory,long siteRva,long codeTarget,int ecx,long rax) {
            port("FBBA8",memory,siteRva,codeTarget,Integer.toUnsignedLong(ecx),rax);
        }
        @Override public void call43da7c0(ModuleLookup221Api.Memory memory,long siteRva,long codeTarget,long rcx) {
            port("F7C0",memory,siteRva,codeTarget,rcx);
        }
        @Override public int jumpRax(ModuleLookup221Api.Memory memory,long siteRva,long targetRax,long knownRcx) {
            return (int)port("SUP",memory,siteRva,targetRax,knownRcx);
        }
        void done() {
            if (finished || cursor!=expected.size()) throw new AssertionError("unfinished/repeated fixture " + cursor + "/" + expected.size());
            finished=true; fixturesDone++; targetMemory+=pMemory; opaqueMemory+=cMemory;
            portsObserved+=portCount; suppliersObserved+=supplierCount;
        }
    }
    private static void eq(long expected,long actual,String label) {
        if (expected!=actual) throw new AssertionError(label + ": " + Long.toHexString(expected) + " != " + Long.toHexString(actual));
    }
    private static void same(Object expected,Object actual,String label) {
        if (expected!=actual) throw new AssertionError(label);
    }
    private static void check(boolean condition,String label) {
        if (!condition) throw new AssertionError(label);
    }
    private static void expectIAE(Runnable action) {
        try { action.run(); } catch (IllegalArgumentException expected) { return; }
        throw new AssertionError("expected IllegalArgumentException");
    }
    private static void expectSame(RuntimeException expected,Runnable action) {
        try { action.run(); } catch (RuntimeException actual) { same(expected,actual,"exception identity"); return; }
        throw new AssertionError("expected exact opaque exception");
    }

    private static void directProtocol236() {
        long base=0x10000000L, active=base+0x4267630L, site=0x424230FL;
        long rax=0xFEDCBA9876543210L;
        Fixture f=new Fixture(), foreign=new Fixture();
        RuntimeException supplierFailure=new RuntimeException("236 supplier");
        RuntimeException foreignFailure=new RuntimeException("236 foreign fallback");
        RuntimeException passiveFailure=new RuntimeException("236 passive long");
        f.expectPort("SUP",f,0x80000011L,null,null,site,rax,0xFFFFFFFFL);
        f.expectPort("SUP",f,0L,null,null,site,0L,0x80000000L);
        f.expectPort("FBBA8",foreign,0L,null,null,0x55L,active+1L,0x87654321L,0x1122334455667788L);
        f.expectPort("F458",foreign,0x80000022L,null,null,0x61L,0x8877665544332211L,0x1111222233334444L,0x5555666677778888L,0x9999AAAABBBBCCCCL);
        f.expectPort("F680",foreign,0xFEDCBA9800000000L,null,null,0x62L,0x1020304050607080L,0xFFEEDDCCBBAA9988L,0x7766554433221100L);
        f.expectPort("F7C0",foreign,0L,null,null,0x63L,0xABCDABCD12341234L,0xF0E0D0C0B0A09080L);
        f.expectPort("SUP",f,0L,null,supplierFailure,site,0x8000000000000000L,0x89ABCDEFL);
        f.expectPort("FBBA8",foreign,0L,null,foreignFailure,0x64L,active-1L,0x80000001L,0xABCDEF1200000000L);
        f.expectPort("F680",foreign,0L,null,passiveFailure,0x65L,0x9988776655443322L,0x1111111122222222L,0x3333333344444444L);
        ModuleLookup221Api.Ports p=Lookup236Binding.bind(base,f,f,f);
        expectIAE(()->p.call43dbba8(foreign,site,active,-1,rax));
        expectIAE(()->p.call43dbba8(f,site+1L,active,-1,rax));
        p.call43dbba8(f,site,active,-1,rax);
        p.call43dbba8(f,site,active,Integer.MIN_VALUE,0L);
        p.call43dbba8(foreign,0x55L,active+1L,0x87654321,0x1122334455667788L);
        eq(0x80000022L,Integer.toUnsignedLong(p.call43da458(foreign,0x61L,0x8877665544332211L,
                0x1111222233334444L,0x5555666677778888L,0x9999AAAABBBBCCCCL)),"passive int bits");
        eq(0xFEDCBA9800000000L,p.call43da680(foreign,0x62L,0x1020304050607080L,
                0xFFEEDDCCBBAA9988L,0x7766554433221100L),"passive full long");
        p.call43da7c0(foreign,0x63L,0xABCDABCD12341234L,0xF0E0D0C0B0A09080L);
        expectSame(supplierFailure,()->p.call43dbba8(f,site,active,0x89ABCDEF,0x8000000000000000L));
        expectSame(foreignFailure,()->p.call43dbba8(foreign,0x64L,active-1L,0x80000001,0xABCDEF1200000000L));
        expectSame(passiveFailure,()->p.call43da680(foreign,0x65L,0x9988776655443322L,
                0x1111111122222222L,0x3333333344444444L));
        f.done(); foreign.done();
    }

    private static void actualLookup236() {
        {
            long base=0x10000000L, e=0x20001000L, slot=e+0x10L;
            long a458=base+0x43DA458L, a680=base+0x43DA680L;
            long abba8=base+0x43DBBA8L, a7c0=base+0x43DA7C0L;
            long t458=0x1212121200000041L, t680=0x2323232300000068L;
            long next680=0x3434343400000068L, next7c0=0x454545450000007CL;
            long before=0x8877665544332211L, first=0x1111222233334444L;
            long after=0x9999AAAABBBBCCCCL, live=0x8000000000000000L;
            Fixture f=new Fixture();
            f.seed64(slot,before); f.seedBytes(slot-1,0xA5); f.seedBytes(slot+8,0x5A);
            f.seed64(a458,t458); f.seed64(a680,t680);
            f.seed64(abba8,0x56565656000000BBL); f.seed64(a7c0,0x676767670000007CL);
            f.expectMemory("P.R64",slot,before); f.expectMemory("P.W64",slot,0L);
            f.expectMemory("P.R64",a458,t458);
            f.expectPort("F458",f,0x80000000L,(owner,m,args)->{
                same(f,m,"458 Memory");
                m.writeInt64(slot,first);
                m.writeInt64(a680,next680);
                m.writeInt64(abba8,base+0x4267630L);
            },null,0x42422ECL,t458,0L,base+0x4423EB8L,slot);
            f.expectMemory("C.W64",slot,first);
            f.expectMemory("C.W64",a680,next680);
            f.expectMemory("C.W64",abba8,base+0x4267630L);
            f.expectMemory("P.R64",slot,first); f.expectMemory("P.R64",a680,next680);
            f.expectPort("F680",f,live,null,null,0x4242302L,next680,first,base+0x4423ED0L);
            f.expectMemory("P.R64",abba8,base+0x4267630L);
            f.expectPort("SUP",f,0x80000001L,(owner,m,args)->{
                same(f,m,"supplier Memory");
                m.writeInt64(slot,after); m.writeInt64(a7c0,next7c0);
            },null,0x424230FL,live,0x89ABCDEFL);
            f.expectMemory("C.W64",slot,after); f.expectMemory("C.W64",a7c0,next7c0);
            f.expectMemory("P.R64",slot,after); f.expectMemory("P.R64",a7c0,next7c0);
            f.expectPort("F7C0",f,0L,null,null,0x424231FL,next7c0,after);
            new ModuleLookup42422D0().execute(f,Lookup236Binding.bind(base,f,f,f),
                    new ModuleLookup221Api.Input(base,0x89ABCDEF,new ModuleLookup221Api.Scratch(e)));
            f.done();
            eq(after,f.peek64(slot),"source success fresh cleanup slot");
            eq(next680,f.peek64(a680),"callback changed second IAT");
            eq(base+0x4267630L,f.peek64(abba8),"callback changed dispatch IAT");
            eq(next7c0,f.peek64(a7c0),"supplier changed cleanup IAT");
            eq(0xA5,f.peek8(slot-1),"slot left byte"); eq(0x5A,f.peek8(slot+8),"slot right byte");
        }
        {
            long base=0x30000000L, e=0x40002000L, slot=e+0x10L;
            long t458=0x7878787800000045L, t680=0x8989898900000068L;
            long before=0xAABBCCDDEEFF0011L, module=0x1020304050607080L;
            Fixture f=new Fixture();
            f.seed64(slot,before); f.seedBytes(slot-1,0xB6); f.seedBytes(slot+8,0x6B);
            f.seed64(base+0x43DA458L,t458); f.seed64(base+0x43DA680L,t680);
            f.expectMemory("P.R64",slot,before); f.expectMemory("P.W64",slot,0L);
            f.expectMemory("P.R64",base+0x43DA458L,t458);
            f.expectPort("F458",f,1L,(owner,m,args)->m.writeInt64(slot,module),null,
                    0x42422ECL,t458,0L,base+0x4423EB8L,slot);
            f.expectMemory("C.W64",slot,module);
            f.expectMemory("P.R64",slot,module); f.expectMemory("P.R64",base+0x43DA680L,t680);
            f.expectPort("F680",f,0L,(owner,m,args)->m.writeInt64(slot,0L),null,
                    0x4242302L,t680,module,base+0x4423ED0L);
            f.expectMemory("C.W64",slot,0L); f.expectMemory("P.R64",slot,0L);
            new ModuleLookup42422D0().execute(f,Lookup236Binding.bind(base,f,f,f),
                    new ModuleLookup221Api.Input(base,-7,new ModuleLookup221Api.Scratch(e)));
            f.done(); eq(0L,f.peek64(slot),"zero lookup fresh slot skips cleanup");
            eq(0xB6,f.peek8(slot-1),"zero lookup left byte"); eq(0x6B,f.peek8(slot+8),"zero lookup right byte");
        }
        {
            long base=0x50000000L, e=0x60003000L, slot=e+0x10L;
            long t458=0x9A9A9A9A00000045L, t7c0=0xABABABAB0000007CL;
            long before=0x1234567800000000L, handle=0xBCBCBCBCDEDEDEDEL;
            Fixture f=new Fixture();
            f.seed64(slot,before); f.seedBytes(slot-1,0xC7); f.seedBytes(slot+8,0x7C);
            f.seed64(base+0x43DA458L,t458); f.seed64(base+0x43DA7C0L,t7c0);
            f.expectMemory("P.R64",slot,before); f.expectMemory("P.W64",slot,0L);
            f.expectMemory("P.R64",base+0x43DA458L,t458);
            f.expectPort("F458",f,0L,(owner,m,args)->m.writeInt64(slot,handle),null,
                    0x42422ECL,t458,0L,base+0x4423EB8L,slot);
            f.expectMemory("C.W64",slot,handle);
            f.expectMemory("P.R64",slot,handle); f.expectMemory("P.R64",base+0x43DA7C0L,t7c0);
            f.expectPort("F7C0",f,0L,null,null,0x424231FL,t7c0,handle);
            new ModuleLookup42422D0().execute(f,Lookup236Binding.bind(base,f,f,f),
                    new ModuleLookup221Api.Input(base,7,new ModuleLookup221Api.Scratch(e)));
            f.done(); eq(handle,f.peek64(slot),"first failure still fresh cleanup");
            eq(0xC7,f.peek8(slot-1),"first failure left byte"); eq(0x7C,f.peek8(slot+8),"first failure right byte");
        }
    }


    public static void main(String[] args) {
        directProtocol236();
        actualLookup236();
        System.out.println("Lookup236Validation methods=2 fixtures="+fixturesDone+" targetMemory="+targetMemory
                +" opaqueMemory="+opaqueMemory+" ports="+portsObserved+" suppliers="+suppliersObserved);
    }
}
