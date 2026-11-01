package org.xar.ck3.research.m3.out224;
import java.util.*;
import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import org.xar.ck3.research.m3.gs223.GsFlag223Api;
import org.xar.ck3.research.m3.gs223.GsFlag42591F8;
/** Owner mechanical bytes/typedstubs only, no expected before firstPOST. */
public final class OutHelperBindingValidation224 {
    static int checks,groups,eventCount,memoryEvents,portEvents;
    static String h(long v){return Long.toUnsignedString(v,16);}
    static void check(boolean v,String why){checks++;if(!v)throw new AssertionError(why);}
    static void equal(long a,long b,String why){check(a==b,why+" actual="+h(a)+" expected="+h(b));}
    static void same(Object a,Object b){check(a==b,"identity");}
    static void iae(Runnable r){checks++;try{r.run();}catch(IllegalArgumentException expected){return;}throw new AssertionError("expectedIAE");}
    static void events(List<String> actual,String... expected){check(actual.equals(List.of(expected)),"trace actual="+actual+" expected="+List.of(expected));for(String e:actual){eventCount++;if(e.startsWith("R")||e.startsWith("W"))memoryEvents++;else portEvents++;}}
    static void done(String s){groups++;System.out.println("PASS "+s);}
    static final class Mem implements NativeTaskMemory {
        final Map<Long,Byte> bytes=new HashMap<>();final List<String> log;Mem(List<String> l){log=l;}
        void seed(long a,int n,long v){for(int i=0;i<n;i++)bytes.put(a+i,(byte)(v >>> (i*8)));}
        void seed8(long a,int v){seed(a,1,v);}void seed32(long a,int v){seed(a,4,v);}void seed64(long a,long v){seed(a,8,v);}
        long peek(long a,int n){long v=0;for(int i=0;i<n;i++){Byte b=bytes.get(a+i);if(b==null)throw new AssertionError("unmapped "+h(a+i));v|=(long)(b&255) << (i*8);}return v;}
        long get(long a,int n){long v=peek(a,n);log.add("R"+(8*n)+"@"+h(a)+"="+h(v));return v;}
        void put(long a,int n,long v){seed(a,n,v);log.add("W"+(8*n)+"@"+h(a)+"="+h(n==8?v:v&0xffffffffL));}
        @Override public long readPointer(long a){return get(a,8);}@Override public int readInt32(long a){return (int)get(a,4);}
        @Override public void writeInt32(long a,int v){put(a,4,v);}@Override public void writeInt64(long a,long v){put(a,8,v);}
    }
    static class Child implements OutHelper224Api.Ports {
        @Override public long call424e448(NativeTaskMemory m,long site,int ecx,long rdx,long r8,long r9){throw new AssertionError("unexpected direct");}
        @Override public long tail43dbba8(NativeTaskMemory m,long site,long target,long rax,long rcx,long rdx){throw new AssertionError("unexpected tail");}
    }
    static class GsFallback implements GsFlag223Api.Ports {
        @Override public long readGs60(NativeTaskMemory m,long site){throw new AssertionError("unexpected GS");}
        @Override public void call424e620(NativeTaskMemory m,long site,long rcx){throw new AssertionError("active fallback replay");}
    }
    public static void main(String[] args){guards();boundFlow();System.out.println("GROUPS="+groups+" EVENTS="+eventCount+" MEMORY="+memoryEvents+" PORTS="+portEvents+" MIXED_CHECKS="+checks);}
static void guards() {
    List<String> a=new ArrayList<>();Mem m=new Mem(a),foreign=new Mem(a);
    GsFallback fallback=new GsFallback() {
        @Override public long readGs60(NativeTaskMemory q,long site) {
            same(q,foreign);equal(site,0x9999L,"GSfallback exactsite");a.add("PGSfallback:"+h(site));return 0xf123456789abcdefL;
        }
    };
    GsFlag223Api.Ports bound=OutHelperFromGsBinding224.bind(m,0x10000000L,new Child(),fallback);
    iae(()->bound.call424e620(foreign,0x425921bL,0x5008L));events(a);
    iae(()->bound.call424e620(m,0x425921cL,0x5008L));events(a);
    check(m.bytes.isEmpty()&&foreign.bytes.isEmpty(),"wrong Memory/site reject beforeeffects");
    equal(bound.readGs60(foreign,0x9999L),0xf123456789abcdefL,"GSfallback actualfull64return");
    events(a,"PGSfallback:9999");
    check(m.bytes.isEmpty()&&foreign.bytes.isEmpty(),"passive GS noextraMemoryeffect");
    done("guards");
}

static void boundFlow() {
    List<String> log = new ArrayList<>();
    Mem m = new Mem(log);
    long base = 0x10000000L;
    long iatAddr = base + 0x43DBBA8L;

    // Seed IAT and canaries
    m.seed64(iatAddr, 0L);
    m.seed8(0x5007L, 0x11);
    m.seed8(0x500CL, 0x22);
    m.seed8(0x7007L, 0x33);
    m.seed8(0x700CL, 0x44);

    // Seed GS structures
    m.seed64(0x1000L + 0x20L, 0x3000L);
    m.seed64(0x2000L + 0x20L, 0x4000L);
    m.seed32(0x3000L + 8L, 0);
    m.seed32(0x4000L + 8L, 0x7FFFFFFF);

    int[] gsCount = new int[1];
    int[] edgeCount = new int[1];
    int[] directCount = new int[1];
    int[] tailCount = new int[1];

    OutHelper224Api.Ports child = new OutHelper224Api.Ports() {
        @Override public long call424e448(NativeTaskMemory memory, long siteRva, int ecx, long rdx, long r8, long r9) {
            directCount[0]++;
            check(memory == m, "direct same memory");
            check(siteRva == 0x424E643L, "direct site");
            check(ecx == 0x1C, "direct ecx");
            check(rdx == 0x14427010L, "direct rdx");
            check(r8 == 0x1442700CL, "direct r8");
            check(r9 == 0x14427010L, "direct r9");
            check(rdx == r9, "direct rdx==r9");

            long rax = directCount[0] == 1 ? 0xF111111100000000L : 0xF222222200000000L;
            long target = directCount[0] == 1 ? 0xE111111111111111L : 0xE222222222222222L;

            log.add("P424E448@424e643 ecx=1c rdx=14427010 r8=1442700c r9=14427010 rax=" + h(rax));
            memory.writeInt64(iatAddr, target);
            return rax;
        }
        @Override public long tail43dbba8(NativeTaskMemory memory, long siteRva, long actualTarget, long liveRaxArg, long rcx, long rdx) {
            tailCount[0]++;
            check(memory == m, "tail same memory");
            check(siteRva == 0x424E65CL, "tail site");
            check(rcx == 0xFFFFFFFFFFFFFFFAL, "tail rcx");
            check(rdx == (tailCount[0] == 1 ? 0x5008L : 0x7008L), "tail rdx");

            long expectedTarget = tailCount[0] == 1 ? 0xE111111111111111L : 0xE222222222222222L;
            long expectedRax = tailCount[0] == 1 ? 0xF111111100000000L : 0xF222222200000000L;
            check(actualTarget == expectedTarget, "tail target");
            check(liveRaxArg == expectedRax, "tail rax");

            long post = tailCount[0] == 1 ? 0xF123456700000002L : 0x8000000100000001L;
            log.add("P43DBBA8@424e65c target=" + h(actualTarget) + " rax=" + h(liveRaxArg) + " rcx=fffffffffffffffa rdx=" + h(rdx));
            memory.writeInt32(rdx, tailCount[0] == 1 ? 1 : 2);
            return post;
        }
    };

    GsFlag223Api.Ports fallback = new GsFlag223Api.Ports() {
        @Override public long readGs60(NativeTaskMemory memory, long siteRva) {
            check(memory == m, "fallback gs same memory");
            check(siteRva == 0x4259204L, "fallback gs site");
            gsCount[0]++;
            log.add("PreadGs60@4259204");
            return gsCount[0] == 1 ? 0x1000L : 0x2000L;
        }
        @Override public void call424e620(NativeTaskMemory memory, long siteRva, long rcx) {
            throw new AssertionError("unexpected fallback child");
        }
    };

    GsFlag223Api.Ports bound = OutHelperFromGsBinding224.bind(m, base, child, fallback);

    GsFlag223Api.Ports observer = new GsFlag223Api.Ports() {
        @Override public long readGs60(NativeTaskMemory memory, long siteRva) {
            return bound.readGs60(memory, siteRva);
        }
        @Override public void call424e620(NativeTaskMemory memory, long siteRva, long rcx) {
            edgeCount[0]++;
            check(memory == m, "edge same memory");
            check(siteRva == 0x425921BL, "edge site");
            check(rcx == (edgeCount[0] == 1 ? 0x5008L : 0x7008L), "edge rcx");
            log.add("PEDGE@425921b rcx=" + h(rcx));
            bound.call424e620(memory, siteRva, rcx);
        }
    };

    GsFlag223Api.Scratch s1 = new GsFlag223Api.Scratch(0x5000L);
    int r1 = GsFlag42591F8.execute(m, observer, s1);
    check(r1 == 0, "first gs result");

    GsFlag223Api.Scratch s2 = new GsFlag223Api.Scratch(0x7000L);
    int r2 = GsFlag42591F8.execute(m, observer, s2);
    check(r2 == 1, "second gs result");

    check(directCount[0] == 2, "direct count");
    check(tailCount[0] == 2, "tail count");
    check(gsCount[0] == 2, "gs count");
    check(edgeCount[0] == 2, "edge count");

    check(m.peek(0x5008L, 4) == 1L, "slot 1 final");
    check(m.peek(0x7008L, 4) == 2L, "slot 2 final");
    check(m.peek(0x5007L, 1) == 0x11L, "canary 5007");
    check(m.peek(0x500CL, 1) == 0x22L, "canary 500C");
    check(m.peek(0x7007L, 1) == 0x33L, "canary 7007");
    check(m.peek(0x700CL, 1) == 0x44L, "canary 700C");
    check(m.peek(iatAddr, 8) == 0xE222222222222222L, "IAT final");

    String[] expected = {
        "W32@5008=0",
        "PreadGs60@4259204",
        "R64@1020=3000",
        "R32@3008=0",
        "PEDGE@425921b rcx=5008",
        "P424E448@424e643 ecx=1c rdx=14427010 r8=1442700c r9=14427010 rax=f111111100000000",
        "W64@143dbba8=e111111111111111",
        "R64@143dbba8=e111111111111111",
        "P43DBBA8@424e65c target=e111111111111111 rax=f111111100000000 rcx=fffffffffffffffa rdx=5008",
        "W32@5008=1",
        "R32@5008=1",
        "W32@7008=0",
        "PreadGs60@4259204",
        "R64@2020=4000",
        "R32@4008=7fffffff",
        "PEDGE@425921b rcx=7008",
        "P424E448@424e643 ecx=1c rdx=14427010 r8=1442700c r9=14427010 rax=f222222200000000",
        "W64@143dbba8=e222222222222222",
        "R64@143dbba8=e222222222222222",
        "P43DBBA8@424e65c target=e222222222222222 rax=f222222200000000 rcx=fffffffffffffffa rdx=7008",
        "W32@7008=2",
        "R32@7008=2"
    };
    events(log, expected);
    done("boundFlow");
}
}
