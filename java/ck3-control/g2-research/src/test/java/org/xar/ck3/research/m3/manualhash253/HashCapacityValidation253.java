package org.xar.ck3.research.m3.manualhash253;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m3.hash188.HashInsert188Api;
import org.xar.ck3.research.m3.hash188.HashInsertC39C60;
import org.xar.ck3.research.m3.hash209.HashCapacityBinding209;

/** Finite supplied-storage witness only; no native execution or hardware semantics. */
public final class HashCapacityValidation253 {
    private HashCapacityValidation253() { }
    private static int checks;
    private static int groups;
    private static int events,ramEvents,portEvents,opaqueEffects;
    private static void eq(long expected, long actual, String label) {
        checks++;
        if(expected!=actual) throw new AssertionError(label+" expected="+hex(expected)+" actual="+hex(actual));
    }
    private static void same(Object expected, Object actual, String label) {
        checks++;
        if(expected!=actual) throw new AssertionError(label+" identity");
    }
    private static void yes(boolean condition, String label) {
        checks++;
        if(!condition) throw new AssertionError(label);
    }
    private static String hex(long value) { return Long.toUnsignedString(value,16); }
    private static String event(String role, long... args) {
        StringBuilder b=new StringBuilder(role);
        for(long x:args) b.append(':').append(hex(x));
        return b.toString();
    }
    private static <T extends Throwable> T thrown(Class<T> type,Runnable run) {
        checks++;
        try { run.run(); } catch(Throwable t) {
            if(type.isInstance(t)) return type.cast(t);
            throw new AssertionError("wrong exception; wanted "+type.getName(),t);
        }
        throw new AssertionError("missing exception "+type.getName());
    }
    private static void trace(Trace t,String... expected) {
        checks++;
        if(!t.events.equals(List.of(expected))) throw new AssertionError("trace expected="+List.of(expected)+" actual="+t.events);
    }
    private static final class Trace {
        final List<String> events=new ArrayList<>();
        void add(String role,long... args) {
            events.add(event(role,args)); HashCapacityValidation253.events++;
            char kind=role.charAt(0);
            if(kind=='R'||kind=='W') ramEvents++;
            else if(kind=='H'||kind=='T') portEvents++;
            else if(kind=='E') opaqueEffects++;
        }
    }
    private static final class Ram implements HashInsert188Api.Memory {
        final Trace trace;
        final Map<Long,Byte> bytes=new HashMap<>();
        Ram(Trace trace) { this.trace=trace; }
        void seed(long address,int width,long value) {
            for(int i=0;i<width;i++) bytes.put(address+i,(byte)(value>>>(8*i)));
        }
        long peek(long address,int width) {
            long value=0;
            for(int i=0;i<width;i++) {
                Byte b=bytes.get(address+i);
                if(b==null) throw new AssertionError("unmapped byte "+hex(address+i));
                value|=(long)(b&255)<<(8*i);
            }
            return value;
        }
        Map<Long,Byte> snapshot() { return Map.copyOf(bytes); }
        @Override public int readUnsigned8(long a) {
            int v=(int)peek(a,1); trace.add("R8",a,v); return v;
        }
        @Override public int readInt32(long a) {
            int v=(int)peek(a,4); trace.add("R32",a,Integer.toUnsignedLong(v)); return v;
        }
        @Override public long readPointer(long a) {
            long v=peek(a,8); trace.add("R64",a,v); return v;
        }
        @Override public HashInsert188Api.Bytes16 read128(long a) {
            long low=peek(a,8),high=peek(a+8,8); trace.add("R128",a,low,high);
            return new HashInsert188Api.Bytes16(low,high);
        }
        @Override public void write8(long a,int v) { trace.add("W8",a,v&255); seed(a,1,v); }
        @Override public void writeInt32(long a,int v) { trace.add("W32",a,Integer.toUnsignedLong(v)); seed(a,4,v); }
        @Override public void writeInt64(long a,long v) { trace.add("W64",a,v); seed(a,8,v); }
        @Override public void write128(long a,HashInsert188Api.Bytes16 v) {
            trace.add("W128",a,v.low(),v.high()); seed(a,8,v.low()); seed(a+8,8,v.high());
        }
    }
    private record Call(String role,Object memory,long result,Runnable effect,RuntimeException error,long[] args) { }
    private static final class Plan {
        final Trace trace;
        final ArrayDeque<Call> calls=new ArrayDeque<>();
        Plan(Trace trace) { this.trace=trace; }
        Plan add(String role,Object memory,long result,Runnable effect,RuntimeException error,long... args) {
            calls.add(new Call(role,memory,result,effect,error,args.clone())); return this;
        }
        long take(String role,Object memory,long... args) {
            Call c=calls.poll();
            if(c==null) throw new AssertionError("unexpected callback "+event(role,args));
            checks++;
            if(!c.role().equals(role)) throw new AssertionError("callback expected="+c.role()+" actual="+role);
            same(c.memory(),memory,"callback Memory");
            checks++;
            if(!Arrays.equals(c.args(),args)) throw new AssertionError("callback args expected="+Arrays.toString(c.args())+" actual="+Arrays.toString(args));
            trace.add(role,args);
            if(c.effect()!=null) c.effect().run();
            if(c.error()!=null) throw c.error();
            return c.result();
        }
        void done() { eq(0,calls.size(),"all planned callbacks consumed"); }
    }
    private static final class HashPorts implements HashInsert188Api.Ports {
        final Plan p;
        HashPorts(Plan p) { this.p=p; }
        @Override public int equal3f6d2b0(HashInsert188Api.Memory m,long s,long a,long b) { return (int)p.take("H.equal",m,s,a,b); }
        @Override public void copy855f00(HashInsert188Api.Memory m,long s,long a,long b) { p.take("H.copy",m,s,a,b); }
        @Override public void assign855db0(HashInsert188Api.Memory m,long s,long a,long b,long c) { p.take("H.assign",m,s,a,b,c); }
        @Override public void rehashC3a400(HashInsert188Api.Memory m,long s,long a) { p.take("H.rehash",m,s,a); }
        @Override public void insertC3b960(HashInsert188Api.Memory m,long s,long a,long b,int h,long d) { p.take("H.insert",m,s,a,b,h,d); }
        @Override public void destroy856050(HashInsert188Api.Memory m,long s,long a) { p.take("H.destroy",m,s,a); }
        @Override public int capacity86e160(HashInsert188Api.Memory m,long s,int a,int b) { return (int)p.take("H.capacity",m,s,a,b); }
        @Override public void reserveC3b700(HashInsert188Api.Memory m,long s,long a,int b) { p.take("H.reserve",m,s,a,b); }
        @Override public void overflow86f210(HashInsert188Api.Memory m,long s,long a,long b) { p.take("H.overflow",m,s,a,b); }
        @Override public void terminal4232cf4(HashInsert188Api.Memory m,long s) { p.take("H.terminal2",m,s); }
        @Override public void terminal4232cf4(HashInsert188Api.Memory m,long s,long e) { p.take("H.terminal3",m,s,e); }
    }
    // Owner-complete source-derived methods after two complete rejected model candidates per role.
    private static void directCapacity253() {
        Trace t=new Trace(); Ram first=new Ram(t),second=new Ram(t); Plan p=new Plan(t);
        first.seed(0x51L,1,0xA1); second.seed(0x52L,1,0xB2);
        Map<Long,Byte> beforeFirst=first.snapshot(),beforeSecond=second.snapshot();
        HashInsert188Api.Ports bound=HashCapacityBinding209.bind(new HashPorts(p));
        eq(0x12345678,bound.capacity86e160(first,0x91L,0x80000006,0x12345678),"signed negative count shortcut");
        eq(3,bound.capacity86e160(null,-1L,-7,-12),"negative count and bias clamp");
        eq(0x7FFFFFFE,bound.capacity86e160(second,Long.MIN_VALUE,1,0x7FFFFFFE),"count1 full int result");
        eq(3,bound.capacity86e160(first,0L,2,Integer.MAX_VALUE),"DWORD add wraps negative before clamp");
        eq(31,bound.capacity86e160(null,0xABCDL,0x40000001,0),"positive count above power two");
        eq(5,bound.capacity86e160(second,0xFEDCBA9876543210L,257,-4),"positive nonpower with negative bias");
        trace(t); p.done();
        yes(beforeFirst.equals(first.snapshot()),"pure capacity first RAM unchanged");
        yes(beforeSecond.equals(second.snapshot()),"pure capacity second RAM unchanged");

        long site=0x0101010101010101L,a=0x8081828384858687L,b=0xF0E0D0C0B0A09080L,c=0x0102030405060708L;
        p.add("H.equal",second,0x89ABCDEFL,null,null,site,a,b);
        eq(0x89ABCDEF,bound.equal3f6d2b0(second,site,a,b),"fallback equal intbits");
        p.add("H.copy",second,0,null,null,site,a,b); bound.copy855f00(second,site,a,b);
        p.add("H.assign",second,0,null,null,site,a,b,c); bound.assign855db0(second,site,a,b,c);
        p.add("H.rehash",second,0,null,null,site,a); bound.rehashC3a400(second,site,a);
        p.add("H.insert",second,0,null,null,site,a,b,0x8A8B8C8D,c);
        bound.insertC3b960(second,site,a,b,0x8A8B8C8D,c);
        p.add("H.destroy",second,0,null,null,site,a); bound.destroy856050(second,site,a);
        p.add("H.reserve",second,0,null,null,site,a,0x9A9B9C9D);
        bound.reserveC3b700(second,site,a,0x9A9B9C9D);
        p.add("H.overflow",second,0,null,null,site,a,b); bound.overflow86f210(second,site,a,b);
        p.add("H.terminal2",second,0,null,null,site); bound.terminal4232cf4(second,site);
        p.add("H.terminal3",null,0,null,null,site,c); bound.terminal4232cf4(null,site,c);
        RuntimeException opaque=new IllegalStateException("supplied fallback exception");
        p.add("H.copy",second,0,null,opaque,site,b,a);
        same(opaque,thrown(RuntimeException.class,()->bound.copy855f00(second,site,b,a)),"fallback exception identity");
        p.done();
        trace(t,event("H.equal",site,a,b),event("H.copy",site,a,b),event("H.assign",site,a,b,c),
            event("H.rehash",site,a),event("H.insert",site,a,b,0x8A8B8C8D,c),event("H.destroy",site,a),
            event("H.reserve",site,a,0x9A9B9C9D),event("H.overflow",site,a,b),event("H.terminal2",site),
            event("H.terminal3",site,c),event("H.copy",site,b,a));
        yes(beforeFirst.equals(first.snapshot()),"all callbacks preserve first RAM");
        yes(beforeSecond.equals(second.snapshot()),"all callbacks preserve second RAM");
        groups++;
    }

    private static void actualGrowth253() {
        Trace t=new Trace(); Ram m=new Ram(t); Plan p=new Plan(t);
        long map=0x1000L,data=0x2000L,output=0x3000L,descriptor=0x4000L;
        m.seed(map+0x14,4,7); m.seed(map+8,8,data); m.seed(map+0x18,1,0); m.seed(data+4,1,0);
        m.seed(output,8,0x91A2B3C4D5E6F708L); m.seed(output+8,1,0x39); m.seed(descriptor,1,0x4A);
        Map<Long,Byte> beforeFirst=m.snapshot();
        HashInsert188Api.Ports bound=HashCapacityBinding209.bind(new HashPorts(p));
        RuntimeException reserveException=new IllegalArgumentException("supplied reserve boundary");
        p.add("H.reserve",m,0,null,reserveException,0xC39F3EL,map,4);
        HashInsert188Api.Input first=new HashInsert188Api.Input(0L,map,output,0,descriptor,new HashInsert188Api.Scratch(0x5000L));
        same(reserveException,thrown(RuntimeException.class,()->HashInsertC39C60.execute(first,m,bound)),"actual reserve exception identity");
        trace(t,"R32:1014:7","R64:1008:2000","R8:2004:0","R8:1018:0","H.reserve:c39f3e:1000:4");
        p.done(); yes(beforeFirst.equals(m.snapshot()),"reserve throw before every write/recursive call");
        eq(0x91A2B3C4D5E6F708L,m.peek(output,8),"reserve prefix output unchanged");
        eq(0x39,m.peek(output+8,1),"reserve prefix flag unchanged"); eq(0x4A,m.peek(descriptor,1),"reserve prefix descriptor unchanged");

        t.events.clear();
        m.seed(map+0x14,4,0x3FFFFFFF);
        Map<Long,Byte> beforeSecond=m.snapshot();
        RuntimeException terminalException=new UnsupportedOperationException("supplied terminal boundary");
        p.add("H.overflow",m,0,null,null,0xC39F83L,0xA0B0L,map);
        p.add("H.terminal3",m,0,null,terminalException,0xC39F88L,0x9FF8L);
        HashInsert188Api.Input second=new HashInsert188Api.Input(0L,map,output,0,descriptor,new HashInsert188Api.Scratch(0xA000L));
        same(terminalException,thrown(RuntimeException.class,()->HashInsertC39C60.execute(second,m,bound)),"actual terminal exception identity");
        trace(t,"R32:1014:3fffffff","R64:1008:2000","R8:2004:0","R8:1018:0",
            "H.overflow:c39f83:a0b0:1000","H.terminal3:c39f88:9ff8");
        p.done(); yes(beforeSecond.equals(m.snapshot()),"error prefix no writes/Hash INT3 fallthrough");
        eq(0x91A2B3C4D5E6F708L,m.peek(output,8),"error prefix output unchanged");
        eq(0x39,m.peek(output+8,1),"error prefix flag unchanged"); eq(0x4A,m.peek(descriptor,1),"error prefix descriptor unchanged");
        groups++;
    }

    public static void main(String[] args) {
        directCapacity253();
        actualGrowth253();
        System.out.println("groups="+groups+" events="+events+" RAM="+ramEvents+" ports="+portEvents+" opaqueEffects="+opaqueEffects+" mixedChecks="+checks);
    }
}
