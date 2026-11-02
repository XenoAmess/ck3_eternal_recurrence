package org.xar.ck3.research.m3.manualhash252;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m3.hash188.HashInsert188Api;
import org.xar.ck3.research.m3.hash188.HashInsertC39C60;
import org.xar.ck3.research.m3.hash208.HashRecordBinding208;
import org.xar.ck3.research.m3.hash208.HashTerminalBinding208;
import org.xar.ck3.research.m3.terminal207.Terminal207Api;

/** Finite supplied-storage witness only; no native execution or hardware semantics. */
public final class HashErrorBoundaryValidation252 {
    private HashErrorBoundaryValidation252() { }
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
            events.add(event(role,args)); HashErrorBoundaryValidation252.events++;
            char kind=role.charAt(0);
            if(kind=='R'||kind=='W') ramEvents++;
            else if(kind=='H'||kind=='T') portEvents++;
            else if(kind=='E') opaqueEffects++;
        }
    }
    private static final class Ram implements HashTerminalBinding208.SharedMemory {
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
    private static final class TerminalPorts implements Terminal207Api.Ports {
        final Plan p;
        TerminalPorts(Plan p) { this.p=p; }
        @Override public long call4246fb4(Terminal207Api.Memory m,long s) { return p.take("T.first2",m,s); }
        @Override public long call4246fb4(Terminal207Api.Memory m,long s,long e) { return p.take("T.first3",m,s,e); }
        @Override public void call4247004(Terminal207Api.Memory m,long s,int c) { p.take("T.handler3",m,s,c); }
        @Override public void call4247004(Terminal207Api.Memory m,long s,int c,long e) { p.take("T.handler4",m,s,c,e); }
        @Override public int call43da258(Terminal207Api.Memory m,long s,long code,int c) { return (int)p.take("T.iat",m,s,code,c); }
        @Override public void call423283c(Terminal207Api.Memory m,long s,int c,int d,int r) { p.take("T.signal5",m,s,c,d,r); }
        @Override public void call423283c(Terminal207Api.Memory m,long s,int c,int d,int r,long e) { p.take("T.signal6",m,s,c,d,r,e); }
        @Override public void call4242354(Terminal207Api.Memory m,long s,int c) { p.take("T.tail3",m,s,c); }
        @Override public void call4242354(Terminal207Api.Memory m,long s,int c,long e) { p.take("T.tail4",m,s,c,e); }
    }

    // Owner-complete methods after two rejected complete model candidates per role.
    private static void directBoundary252() {
        {
            Trace t=new Trace(); Ram m=new Ram(t); Plan p=new Plan(t);
            HashInsert188Api.Ports bound=HashRecordBinding208.bind(m,new HashPorts(p));
            m.seed(0x7FFFL,1,0x5A); m.seed(0x8008L,1,0xA5);
            bound.overflow86f210(m,0xC39F83L,0x8000L,0xFEDCBA9876543210L);
            trace(t,"W64:8000:fedcba9876543210");
            eq(0xFEDCBA9876543210L,m.peek(0x8000L,8),"record full64");
            eq(0x5A,m.peek(0x7FFFL,1),"record leading canary");
            eq(0xA5,m.peek(0x8008L,1),"record trailing canary");
            eq(10,m.bytes.size(),"only exact record width added"); p.done();
        }
        {
            Trace t=new Trace(); Ram captured=new Ram(t),foreign=new Ram(t); Plan p=new Plan(t);
            captured.seed(0x80L,1,0x61); foreign.seed(0x80L,1,0x72);
            Map<Long,Byte> before=captured.snapshot(),foreignBefore=foreign.snapshot();
            HashPorts fallback=new HashPorts(p);
            HashInsert188Api.Ports record=HashRecordBinding208.bind(captured,fallback);
            HashInsert188Api.Ports terminal=HashTerminalBinding208.bind(captured,0L,new TerminalPorts(p),fallback);
            thrown(IllegalArgumentException.class,()->record.overflow86f210(foreign,0xC39F83L,0x80L,4L));
            thrown(IllegalArgumentException.class,()->record.overflow86f210(captured,0xC39F82L,0x80L,4L));
            thrown(IllegalArgumentException.class,()->terminal.terminal4232cf4(foreign,0xC39F88L));
            thrown(IllegalArgumentException.class,()->terminal.terminal4232cf4(captured,0xC39F87L));
            thrown(IllegalArgumentException.class,()->terminal.terminal4232cf4(foreign,0xC39F88L,0x9876543210L));
            thrown(IllegalArgumentException.class,()->terminal.terminal4232cf4(captured,0xC39F89L,0x9876543210L));
            trace(t); p.done();
            yes(before.equals(captured.snapshot()),"guards preserve captured bytes");
            yes(foreignBefore.equals(foreign.snapshot()),"guards preserve foreign bytes");
        }
        for(int kind=0;kind<2;kind++) {
            Trace t=new Trace(); Ram captured=new Ram(t),foreign=new Ram(t); Plan p=new Plan(t);
            HashPorts fallback=new HashPorts(p);
            HashInsert188Api.Ports bound=kind==0?HashRecordBinding208.bind(captured,fallback):
                HashTerminalBinding208.bind(captured,0L,new TerminalPorts(p),fallback);
            long site=0xEEDDBBCCAA998877L,a=0xFEDCBA9876543210L,b=0x8123456789ABCDEFL,c=0x123456789ABCDEFL;
            List<String> expected=new ArrayList<>();
            p.add("H.equal",foreign,0xFFFFFFFFL,null,null,site,a,b);
            eq(-1,bound.equal3f6d2b0(foreign,site,a,b),"passive equal fullint");
            expected.add(event("H.equal",site,a,b));
            p.add("H.copy",foreign,0,null,null,site,a,b); bound.copy855f00(foreign,site,a,b);
            expected.add(event("H.copy",site,a,b));
            p.add("H.assign",foreign,0,null,null,site,a,b,c); bound.assign855db0(foreign,site,a,b,c);
            expected.add(event("H.assign",site,a,b,c));
            p.add("H.rehash",foreign,0,null,null,site,a); bound.rehashC3a400(foreign,site,a);
            expected.add(event("H.rehash",site,a));
            p.add("H.insert",foreign,0,null,null,site,a,b,0x80000001,c);
            bound.insertC3b960(foreign,site,a,b,0x80000001,c);
            expected.add(event("H.insert",site,a,b,0x80000001,c));
            p.add("H.destroy",foreign,0,null,null,site,a); bound.destroy856050(foreign,site,a);
            expected.add(event("H.destroy",site,a));
            p.add("H.capacity",foreign,0x80000005L,null,null,site,0x80000002,0xFEDCBA98);
            eq(0x80000005,bound.capacity86e160(foreign,site,0x80000002,0xFEDCBA98),"passive capacity fullint");
            expected.add(event("H.capacity",site,0x80000002,0xFEDCBA98));
            p.add("H.reserve",foreign,0,null,null,site,a,0x87654321); bound.reserveC3b700(foreign,site,a,0x87654321);
            expected.add(event("H.reserve",site,a,0x87654321));
            if(kind==0) {
                p.add("H.terminal2",foreign,0,null,null,site); bound.terminal4232cf4(foreign,site);
                expected.add(event("H.terminal2",site));
                p.add("H.terminal3",foreign,0,null,null,site,c); bound.terminal4232cf4(foreign,site,c);
                expected.add(event("H.terminal3",site,c));
            } else {
                p.add("H.overflow",foreign,0,null,null,site,a,b); bound.overflow86f210(foreign,site,a,b);
                expected.add(event("H.overflow",site,a,b));
            }
            RuntimeException opaque=new IllegalStateException("passive opaque "+kind);
            p.add("H.copy",foreign,0,null,opaque,site,b,a);
            same(opaque,thrown(RuntimeException.class,()->bound.copy855f00(foreign,site,b,a)),"passive exception identity");
            expected.add(event("H.copy",site,b,a));
            trace(t,expected.toArray(String[]::new)); p.done();
            yes(captured.bytes.isEmpty()&&foreign.bytes.isEmpty(),"passives do not touch either RAM");
        }
        {
            Trace t=new Trace(); Ram m=new Ram(t); Plan p=new Plan(t);
            long base=0x100000000L,flag=base+0x542F208L,iat=base+0x43DA258L,code=0xA123456789ABCDEFL;
            m.seed(flag,1,0); m.seed(iat,8,0x1111222233334444L);
            HashInsert188Api.Ports bound=HashTerminalBinding208.bind(m,base,new TerminalPorts(p),new HashPorts(p));
            p.add("T.first2",m,0x100000000L,null,null,0x4232CF8L);
            p.add("T.handler3",m,0,()->{
                t.add("E.handler",flag,2,iat,code); m.seed(flag,1,2); m.seed(iat,8,code);
            },null,0x4232D07L,0x16);
            p.add("T.iat",m,0,null,null,0x4232D1AL,code,0x17);
            p.add("T.signal5",m,0,null,null,0x4232D3AL,3,0x40000015,1);
            p.add("T.tail3",m,0,null,null,0x4232D44L,3);
            UnsupportedOperationException stop=thrown(UnsupportedOperationException.class,()->bound.terminal4232cf4(m,0xC39F88L));
            yes(stop.getMessage().contains("INT3_4232D49"),"full86 legacy stop");
            trace(t,event("T.first2",0x4232CF8L),event("T.handler3",0x4232D07L,0x16),
                event("E.handler",flag,2,iat,code),event("R8",flag,2),event("R64",iat,code),
                event("T.iat",0x4232D1AL,code,0x17),event("T.signal5",0x4232D3AL,3,0x40000015,1),
                event("T.tail3",0x4232D44L,3)); p.done();
            eq(2,m.peek(flag,1),"handler effect flag"); eq(code,m.peek(iat,8),"handler effect IAT full64");
            eq(9,m.bytes.size(),"no unspecified legacy scratch writes");
        }
        {
            Trace t=new Trace(); Ram m=new Ram(t); Plan p=new Plan(t);
            RuntimeException opaque=new IllegalArgumentException("first lower opaque");
            p.add("T.first2",m,0,null,opaque,0x4232CF8L);
            HashInsert188Api.Ports bound=HashTerminalBinding208.bind(m,0L,new TerminalPorts(p),new HashPorts(p));
            same(opaque,thrown(RuntimeException.class,()->bound.terminal4232cf4(m,0xC39F88L)),"terminal exception identity");
            trace(t,"T.first2:4232cf8"); p.done(); yes(m.bytes.isEmpty(),"terminal throw prefix no later memory");
        }
        groups++;
    }

    private static void actualOverflow252() {
        Trace t=new Trace(); Ram m=new Ram(t); Plan p=new Plan(t);
        long base=0x200000000L,map=0x1000L,data=0x2000L,output=0x3000L,descriptor=0x4000L;
        long flag=base+0x542F208L,iat=base+0x43DA258L,code=0xF23456789ABCDEF0L;
        m.seed(map+0x14,4,0xF); m.seed(map+8,8,data); m.seed(map+0x18,1,0); m.seed(data+4,1,0);
        m.seed(output,8,0x8877665544332211L); m.seed(output+8,1,0xA6); m.seed(descriptor,1,0xB7);
        m.seed(0x90AFL,1,0xC8); m.seed(0x90B8L,1,0xD9); m.seed(0xB0AFL,1,0xEA); m.seed(0xB0B8L,1,0xFB);
        m.seed(flag,1,0); m.seed(iat,8,0x1020304050607080L);
        Map<Long,Byte> expectedBytes=new HashMap<>(m.snapshot());
        HashInsert188Api.Ports bound=HashRecordBinding208.bind(m,
            HashTerminalBinding208.bind(m,base,new TerminalPorts(p),new HashPorts(p)));
        p.add("H.capacity",m,31,null,null,0xC39F2FL,0x10,1);
        p.add("T.first3",m,0,()->{
            t.add("E.first",flag,2,iat,code); m.seed(flag,1,2); m.seed(iat,8,code);
        },null,0x4232CF8L,0x8FC8L);
        p.add("T.iat",m,0xFFFFFFFFL,null,null,0x4232D1AL,code,0x17);
        HashInsert188Api.Input input1=new HashInsert188Api.Input(base,map,output,0,descriptor,new HashInsert188Api.Scratch(0x9000L));
        UnsupportedOperationException stop1=thrown(UnsupportedOperationException.class,()->HashInsertC39C60.execute(input1,m,bound));
        yes(stop1.getMessage().contains("INT29_ECX7"),"actual Hash INT29 classified stop");
        p.done();
        trace(t,"R32:1014:f","R64:1008:2000","R8:2004:0","R8:1018:0", "H.capacity:c39f2f:10:1",
            "W64:90b0:1000","T.first3:4232cf8:8fc8",event("E.first",flag,2,iat,code),
            event("R8",flag,2),event("R64",iat,code),event("T.iat",0x4232D1AL,code,0x17));
        eq(map,m.peek(0x90B0L,8),"first current-frame record");
        eq(0xC8,m.peek(0x90AFL,1),"first record leading canary"); eq(0xD9,m.peek(0x90B8L,1),"first record trailing canary");
        eq(0x8877665544332211L,m.peek(output,8),"Hash first output not published");
        eq(0xA6,m.peek(output+8,1),"Hash first flag not published"); eq(0xB7,m.peek(descriptor,1),"descriptor first unchanged");
        t.events.clear();
        p.add("H.capacity",m,31,null,null,0xC39F2FL,0x10,1);
        p.add("T.first3",m,0x100000000L,null,null,0x4232CF8L,0xAFC8L);
        p.add("T.handler4",m,0,()->{
            t.add("E.handler",flag,0); m.seed(flag,1,0);
        },null,0x4232D07L,0x16,0xAFC8L);
        p.add("T.tail4",m,0,null,null,0x4232D44L,3,0xAFC8L);
        HashInsert188Api.Input input2=new HashInsert188Api.Input(base,map,output,0,descriptor,new HashInsert188Api.Scratch(0xB000L));
        UnsupportedOperationException stop2=thrown(UnsupportedOperationException.class,()->HashInsertC39C60.execute(input2,m,bound));
        yes(stop2.getMessage().contains("INT3_4232D49"),"actual Hash INT3 classified stop");
        p.done();
        trace(t,"R32:1014:f","R64:1008:2000","R8:2004:0","R8:1018:0","H.capacity:c39f2f:10:1",
            "W64:b0b0:1000","T.first3:4232cf8:afc8","T.handler4:4232d07:16:afc8",
            event("E.handler",flag,0),event("R8",flag,0),"T.tail4:4232d44:3:afc8");
        eq(map,m.peek(0x90B0L,8),"first record retained"); eq(map,m.peek(0xB0B0L,8),"second current-frame record");
        eq(0xEA,m.peek(0xB0AFL,1),"second record leading canary"); eq(0xFB,m.peek(0xB0B8L,1),"second record trailing canary");
        eq(0x8877665544332211L,m.peek(output,8),"Hash second output not published");
        eq(0xA6,m.peek(output+8,1),"Hash second flag not published"); eq(0xB7,m.peek(descriptor,1),"descriptor second unchanged");
        for(int i=0;i<8;i++) {
            expectedBytes.put(0x90B0L+i,(byte)(map>>>(8*i)));
            expectedBytes.put(0xB0B0L+i,(byte)(map>>>(8*i)));
            expectedBytes.put(iat+i,(byte)(code>>>(8*i)));
        }
        expectedBytes.put(flag,(byte)0);
        yes(expectedBytes.equals(m.snapshot()),"exact final RAM including both controlled effects");
        groups++;
    }

    public static void main(String[] args) {
        directBoundary252();
        actualOverflow252();
        System.out.println("groups="+groups+" events="+events+" RAM="+ramEvents+" ports="+portEvents+" opaqueEffects="+opaqueEffects+" mixedChecks="+checks);
    }
}
