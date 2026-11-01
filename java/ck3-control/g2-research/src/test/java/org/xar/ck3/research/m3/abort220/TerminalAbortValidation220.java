package org.xar.ck3.research.m3.abort220;

import java.util.*;
import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import org.xar.ck3.research.m3.tail217.TerminalTailTarget217Api;


/** Owner mechanical byte fixture; only appended test methods supply semantic literals. */
public final class TerminalAbortValidation220 {
    static int checks, groups, eventCount, memoryEvents, portEvents;
    static String h(long value) { return Long.toUnsignedString(value,16); }
    static void check(boolean value,String why) { checks++; if(!value)throw new AssertionError(why); }
    static void equal(long actual,long expected,String why) { check(actual==expected,why+" actual="+h(actual)+" expected="+h(expected)); }
    static void same(Object actual,Object expected) { check(actual==expected,"memory identity"); }
    static void iae(Runnable action) { checks++;try { action.run(); } catch(IllegalArgumentException expected) {return;}throw new AssertionError("expected IAE"); }
    static void events(List<String> actual,String... expected) {
        check(actual.equals(List.of(expected)),"complete ordered events actual="+actual+" expected="+List.of(expected));
        for(String value:actual) {eventCount++;if(value.startsWith("R")||value.startsWith("W"))memoryEvents++;else portEvents++;}
    }
    static void done(String name) {groups++;System.out.println("PASS "+name);}
    static final class Mem implements TerminalAbort220Api.Memory {
        final Map<Long,Byte> data=new HashMap<>();
        final List<String> log;
        Mem(List<String> log) {this.log=log;}
        void seed(long a,int n,long v) {for(int i=0;i<n;i++)data.put(a+i,(byte)(v >>> (8*i)));}
        void seed8(long a,int v) {seed(a,1,v);}
        void seed16(long a,int v) {seed(a,2,v);}
        void seed32(long a,int v) {seed(a,4,v);}
        void seed64(long a,long v) {seed(a,8,v);}
        long peek(long a,int n) {long v=0;for(int i=0;i<n;i++){Byte b=data.get(a+i);if(b==null)throw new AssertionError("unmapped "+h(a+i));v|=(long)(b&255) << (i*8);}return v;}
        long get(long a,int n) {long v=peek(a,n);log.add("R"+(n*8)+"@"+h(a)+"="+h(v));return v;}
        void put(long a,int n,long v) {seed(a,n,v);log.add("W"+(n*8)+"@"+h(a)+"="+h(n==8?v:v&((1L << (8*n))-1)));}
        @Override public long readPointer(long a) {return get(a,8);}
        @Override public int readInt32(long a) {return (int)get(a,4);}
        @Override public int readUnsigned8(long a) {return (int)get(a,1);}
        @Override public int readUnsigned16(long a) {return (int)get(a,2);}
        @Override public void writeInt32(long a,int v) {put(a,4,v);}
        @Override public void writeInt64(long a,long v) {put(a,8,v);}
        @Override public void write8(long a,int v) {put(a,1,v);}
    }
    static class Calls implements TerminalAbort220Api.Ports {
        @Override public int call42591f8(TerminalAbort220Api.Memory m,long site,int ecx) {throw new AssertionError("unexpected first");}
        @Override public long readGs60(TerminalAbort220Api.Memory m,long site) {throw new AssertionError("unexpected GS60");}
        @Override public long call43da798(TerminalAbort220Api.Memory m,long site,long target,long rax,int edx) {throw new AssertionError("unexpected pair first");}
        @Override public void call43da778(TerminalAbort220Api.Memory m,long site,long target,long rcx,int edx) {throw new AssertionError("unexpected pair second");}
        @Override public void call42422d0(TerminalAbort220Api.Memory m,long site,int ecx,long childEntry) {throw new AssertionError("unexpected child");}
        @Override public void call43da558(TerminalAbort220Api.Memory m,long site,long target,int ecx) {throw new AssertionError("unexpected final");}
    }
    public static void main(String[] args) {
        skipPaths();
        gsClearFresh();
        bindingCompatibility();
        System.out.println("GROUPS="+groups+" EVENTS="+eventCount+" MEMORY="+memoryEvents+" PORTS="+portEvents+" MIXED_CHECKS="+checks);
    }
static void uoe(Runnable action) {
    checks++;try {action.run();}catch(UnsupportedOperationException expected){return;}throw new AssertionError("expected softwareTrap stop");
}

static void skipPaths() {
    List<String> a=new ArrayList<>();Mem m=new Mem(a);
    m.seed64(0x143da558L,0x1111111111111111L);m.seed8(0x143da557L,0xa5);m.seed8(0x143da560L,0x5a);
    Calls skip=new Calls() {
        @Override public int call42591f8(TerminalAbort220Api.Memory q,long site,int ecx) {
            same(q,m);equal(site,0x424228cL,"skip firstsite");equal(ecx,-2,"skip entryECX");a.add("Pfirst:"+h(Integer.toUnsignedLong(ecx)));return 1;
        }
        @Override public void call42422d0(TerminalAbort220Api.Memory q,long site,int ecx,long childE) {
            same(q,m);equal(site,0x42422c0L,"skip childsite");equal(ecx,-2,"skip childECX");equal(childE,0x4fd0L,"skip childE");
            a.add("Pchild:"+h(Integer.toUnsignedLong(ecx))+":"+h(childE));q.writeInt64(0x143da558L,0xf123456789abcdefL);
        }
        @Override public void call43da558(TerminalAbort220Api.Memory q,long site,long target,int ecx) {
            same(q,m);equal(site,0x42422c7L,"skip finalsite");equal(target,0xf123456789abcdefL,"skip freshfinaltarget");equal(ecx,-2,"skip finalECX");
            a.add("Pfinal:"+h(target)+":"+h(Integer.toUnsignedLong(ecx)));
        }
    };
    check(TerminalAbort4242284.execute(m,skip,new TerminalAbort220Api.Input(0x10000000L,-2,new TerminalAbort220Api.Scratch(0x5000L)))==TerminalAbort220Api.Trap.INT3_42422CD,"skip softwareTrap");
    events(a,"Pfirst:fffffffe","Pchild:fffffffe:4fd0","W64@143da558=f123456789abcdef","R64@143da558=f123456789abcdef","Pfinal:f123456789abcdef:fffffffe");
    equal(m.peek(0x143da558L,8),0xf123456789abcdefL,"skip finalslot");equal(m.peek(0x143da557L,1),0xa5,"skip qwordbefore");equal(m.peek(0x143da560L,1),0x5a,"skip qwordafter");
    check(!m.data.containsKey(0x143da798L)&&!m.data.containsKey(0x143da778L),"skip pair IATs unmapped");
    a.clear();Mem n=new Mem(a);
    n.seed32(0xf0000000000040bcL,0x80000100);n.seed8(0xf0000000000040bbL,0xc3);n.seed8(0xf0000000000040c0L,0x3c);
    n.seed64(0x243da558L,0x8000000012345678L);
    Calls bitset=new Calls() {
        @Override public int call42591f8(TerminalAbort220Api.Memory q,long site,int ecx) {
            same(q,n);equal(site,0x424228cL,"bitset firstsite");equal(ecx,Integer.MIN_VALUE,"bitset entryECX");a.add("Pfirst:"+h(Integer.toUnsignedLong(ecx)));return 0;
        }
        @Override public long readGs60(TerminalAbort220Api.Memory q,long site) {
            same(q,n);equal(site,0x4242296L,"typed GS60 site");a.add("Pgs60:f000000000004000");return 0xf000000000004000L;
        }
        @Override public void call42422d0(TerminalAbort220Api.Memory q,long site,int ecx,long childE) {
            same(q,n);equal(site,0x42422c0L,"bitset childsite");equal(ecx,Integer.MIN_VALUE,"bitset childECX");equal(childE,0x5fd0L,"bitset childE");
            a.add("Pchild:"+h(Integer.toUnsignedLong(ecx))+":"+h(childE));
        }
        @Override public void call43da558(TerminalAbort220Api.Memory q,long site,long target,int ecx) {
            same(q,n);equal(site,0x42422c7L,"bitset finalsite");equal(target,0x8000000012345678L,"bitset actualtarget");equal(ecx,Integer.MIN_VALUE,"bitset finalECX");
            a.add("Pfinal:"+h(target)+":"+h(Integer.toUnsignedLong(ecx)));
        }
    };
    check(TerminalAbort4242284.execute(n,bitset,new TerminalAbort220Api.Input(0x20000000L,Integer.MIN_VALUE,new TerminalAbort220Api.Scratch(0x6000L)))==TerminalAbort220Api.Trap.INT3_42422CD,"bitset softwareTrap");
    events(a,"Pfirst:80000000","Pgs60:f000000000004000","R32@f0000000000040bc=80000100","Pchild:80000000:5fd0","R64@243da558=8000000012345678","Pfinal:8000000012345678:80000000");
    equal(n.peek(0xf0000000000040bcL,4),0x80000100L,"bitset GSdata");equal(n.peek(0xf0000000000040bbL,1),0xc3,"bitset DWORDbefore");equal(n.peek(0xf0000000000040c0L,1),0x3c,"bitset DWORDafter");
    check(!n.data.containsKey(0x243da798L)&&!n.data.containsKey(0x243da778L),"bitset pair IATs unmapped");
    done("skipPaths");
}

static void bindingCompatibility() {
    List<String> a=new ArrayList<>();Mem m=new Mem(a),foreign=new Mem(a);
    TerminalTailTarget217Api.Ports fallback=new TerminalTailTarget217Api.Ports() {
        @Override public long call43da620(TerminalTailTarget217Api.Memory q,long site,long target,int ecx) {
            same(q,foreign);a.add("Plookup:"+h(site)+":"+h(target)+":"+h(Integer.toUnsignedLong(ecx)));return 0xf123456789abcdefL;
        }
        @Override public void call42422d0(TerminalTailTarget217Api.Memory q,long site,int ecx) {
            same(q,foreign);a.add("PoldFirst:"+h(site)+":"+h(Integer.toUnsignedLong(ecx)));
        }
        @Override public long call42420c0(TerminalTailTarget217Api.Memory q,long site,long rcx,long rdx,long r8,long r9) {
            same(q,foreign);a.add("Phelper:"+h(site)+":"+h(rcx)+":"+h(rdx)+":"+h(r8)+":"+h(r9));return 0x8000000000000042L;
        }
        @Override public void call4242284(TerminalTailTarget217Api.Memory q,long site,int ecx) {
            same(q,foreign);a.add("PoldAbort:"+h(site)+":"+h(Integer.toUnsignedLong(ecx)));
        }
        @Override public void call42422d0(TerminalTailTarget217Api.Memory q,long site,int ecx,long childE) {
            same(q,foreign);a.add("PnewFirst:"+h(site)+":"+h(Integer.toUnsignedLong(ecx))+":"+h(childE));
        }
        @Override public void call4242284(TerminalTailTarget217Api.Memory q,long site,int ecx,long childE) {throw new AssertionError("active newabort fallback replay");}
    };
    int[] first={0};
    Calls child=new Calls() {
        @Override public int call42591f8(TerminalAbort220Api.Memory q,long site,int ecx) {
            same(q,m);equal(site,0x424228cL,"bound firstsite");check(first[0]<2,"bound exactlytwoinvocations");
            equal(ecx,first[0]==0?-5:Integer.MIN_VALUE,"bound actualECX");first[0]++;
            a.add("Pfirst:"+h(Integer.toUnsignedLong(ecx)));return 1;
        }
        @Override public void call42422d0(TerminalAbort220Api.Memory q,long site,int ecx,long childE) {
            same(q,m);equal(site,0x42422c0L,"bound childsite");equal(ecx,first[0]==1?-5:Integer.MIN_VALUE,"bound childECX");
            equal(childE,first[0]==1?0x8fd0L:0xffffffffffffffe0L,"bound per-call E-30 withwrap");
            a.add("Pchild:"+h(Integer.toUnsignedLong(ecx))+":"+h(childE));
        }
        @Override public void call43da558(TerminalAbort220Api.Memory q,long site,long target,int ecx) {
            same(q,m);equal(site,0x42422c7L,"bound finalsite");equal(target,0xfedcba9801234567L,"bound actualtarget");equal(ecx,first[0]==1?-5:Integer.MIN_VALUE,"bound finalECX");
            a.add("Pfinal:"+h(target)+":"+h(Integer.toUnsignedLong(ecx)));
        }
    };
    TerminalTailTarget217Api.Ports bound=TerminalAbortFromTailBinding220.bind(m,0x30000000L,child,fallback);
    iae(()->bound.call4242284(foreign,0x424227eL,-1,0x9000L));events(a);
    iae(()->bound.call4242284(m,0x424227fL,-1,0x9000L));events(a);
    check(m.data.isEmpty()&&foreign.data.isEmpty(),"active guardseffects0");equal(first[0],0,"guard firstcall0");
    equal(bound.call43da620(foreign,0x6001L,0xfedcba9876543210L,-123),0xf123456789abcdefL,"old lookup exactreturn");
    bound.call42422d0(foreign,0x6002L,Integer.MIN_VALUE);
    equal(bound.call42420c0(foreign,0x6003L,0xf000000000000001L,2,3,4),0x8000000000000042L,"old helper exactreturn");
    bound.call4242284(foreign,0x6004L,Integer.MAX_VALUE);
    bound.call42422d0(foreign,0x6005L,-7,0xffff000000000010L);
    events(a,"Plookup:6001:fedcba9876543210:ffffff85","PoldFirst:6002:80000000","Phelper:6003:f000000000000001:2:3:4","PoldAbort:6004:7fffffff","PnewFirst:6005:fffffff9:ffff000000000010");a.clear();
    m.seed64(0x343da558L,0xfedcba9801234567L);
    uoe(()->bound.call4242284(m,0x424227eL,-5,0x9000L));
    uoe(()->bound.call4242284(m,0x424227eL,Integer.MIN_VALUE,0x10L));
    events(a,"Pfirst:fffffffb","Pchild:fffffffb:8fd0","R64@343da558=fedcba9801234567","Pfinal:fedcba9801234567:fffffffb",
        "Pfirst:80000000","Pchild:80000000:ffffffffffffffe0","R64@343da558=fedcba9801234567","Pfinal:fedcba9801234567:80000000");
    equal(first[0],2,"bound two distinct sourceentryE");equal(m.peek(0x343da558L,8),0xfedcba9801234567L,"bound finalslot");
    done("bindingCompatibility");
}

static void gsClearFresh() {
    List<String> log = new ArrayList<>();
    Mem m = new Mem(log);
    long base = 0x10000000L;
    long entryE = 0x7000L;
    int ecx = 0x80000001;
    long gsPtr = 0xf000000000003000L;
    long gsBCAddr = gsPtr + 0xBC;

    long iat798Addr = base + 0x43DA798L;
    long iat778Addr = base + 0x43DA778L;
    long iat558Addr = base + 0x43DA558L;

    // Seed initial IAT targets
    long oldTarget798 = 0x1111111111111111L;
    long newTarget798 = 0x2222222222222222L;
    long oldTarget778 = 0x3333333333333333L;
    long newTarget778 = 0x4444444444444444L;
    long oldTarget558 = 0x5555555555555555L;
    long newTarget558 = 0x6666666666666666L;
    long finalTarget558 = 0x7777777777777777L;

    m.seed64(iat798Addr, oldTarget798);
    m.seed64(iat778Addr, oldTarget778);
    m.seed64(iat558Addr, oldTarget558);


    // Seed GS+BC raw data (will be overwritten by callback)
    m.seed32(gsBCAddr, 0xdeadbeef);

    m.seed8(gsBCAddr-1,0xa5);m.seed8(gsBCAddr+4,0x5a);
    m.seed8(iat798Addr-1,0xc3);m.seed8(iat798Addr+8,0x3c);
    m.seed8(iat558Addr-1,0x69);m.seed8(iat558Addr+8,0x96);
    // Input
    TerminalAbort220Api.Input input = new TerminalAbort220Api.Input(base, ecx, new TerminalAbort220Api.Scratch(entryE));

    // Ports
    TerminalAbort220Api.Ports ports = new TerminalAbort220Api.Ports() {
        @Override public int call42591f8(TerminalAbort220Api.Memory memory, long siteRva, int entryEcx) {
            same(memory, m);
            equal(siteRva, 0x424228CL, "site 42591F8");
            equal(entryEcx, ecx, "entryEcx 42591F8");
            log.add("Pfirst:"+h(siteRva)+":"+h(Integer.toUnsignedLong(entryEcx)));
            // Change IAT 43DA798
            memory.writeInt64(iat798Addr, newTarget798);
            return -7;
        }
        @Override public long readGs60(TerminalAbort220Api.Memory memory, long siteRva) {
            same(memory, m);
            equal(siteRva, 0x4242296L, "site GS60");
            log.add("PGS60:"+h(siteRva)+":"+h(gsPtr));
            // Write raw DWORD at gs+BC
            memory.writeInt32(gsBCAddr, 0xfedcba00);
            return gsPtr;
        }
        @Override public long call43da798(TerminalAbort220Api.Memory memory, long siteRva, long actualTarget, long liveRax, int liveEdx) {
            same(memory, m);
            equal(siteRva, 0x42422ADL, "site 43DA798");
            equal(actualTarget, newTarget798, "target 43DA798");
            equal(liveRax, gsPtr, "liveRax 43DA798");
            equal(liveEdx, 0x00fedcba, "liveEdx 43DA798");
            log.add("P798:"+h(siteRva)+":"+h(actualTarget)+":"+h(liveRax)+":"+h(Integer.toUnsignedLong(liveEdx)));
            // Change IAT 43DA778
            memory.writeInt64(iat778Addr, newTarget778);
            return 0x9999999999999999L;
        }
        @Override public void call43da778(TerminalAbort220Api.Memory memory, long siteRva, long actualTarget, long rcx, int edx) {
            same(memory, m);
            equal(siteRva, 0x42422B8L, "site 43DA778");
            equal(actualTarget, newTarget778, "target 43DA778");
            equal(rcx, 0x9999999999999999L, "rcx 43DA778");
            equal(edx, ecx, "edx 43DA778");
            log.add("P778:"+h(siteRva)+":"+h(actualTarget)+":"+h(rcx)+":"+h(Integer.toUnsignedLong(edx)));
            // Change IAT 43DA558 to intermediate
            memory.writeInt64(iat558Addr, newTarget558);
        }
        @Override public void call42422d0(TerminalAbort220Api.Memory memory, long siteRva, int ecx, long childEntryRsp) {
            same(memory, m);
            equal(siteRva, 0x42422C0L, "site 42422D0");
            equal(ecx, 0x80000001, "saved entryECX 42422D0");
            equal(childEntryRsp, entryE - 0x30L, "childEntry 42422D0");
            log.add("Pchild:"+h(siteRva)+":"+h(Integer.toUnsignedLong(ecx))+":"+h(childEntryRsp));
            // Change IAT 43DA558 again
            memory.writeInt64(iat558Addr, finalTarget558);
        }
        @Override public void call43da558(TerminalAbort220Api.Memory memory, long siteRva, long actualTarget, int ecx) {
            same(memory, m);
            equal(siteRva, 0x42422C7L, "site 43DA558");
            equal(actualTarget, finalTarget558, "target 43DA558");
            equal(ecx, 0x80000001, "saved entryECX 43DA558");
            log.add("Pfinal:"+h(siteRva)+":"+h(actualTarget)+":"+h(Integer.toUnsignedLong(ecx)));
        }
    };

    // Execute
    TerminalAbort220Api.Trap result = TerminalAbort4242284.execute(m, ports, input);

    // Verify Trap
    check(result == TerminalAbort220Api.Trap.INT3_42422CD, "trap INT3_42422CD");

    // Verify Events
    String[] expected = {
        "Pfirst:424228c:80000001",
        "W64@" + Long.toUnsignedString(iat798Addr, 16) + "=" + Long.toUnsignedString(newTarget798, 16),
        "PGS60:4242296:f000000000003000",
        "W32@" + Long.toUnsignedString(gsBCAddr, 16) + "=" + "fedcba00",
        "R32@" + Long.toUnsignedString(gsBCAddr, 16) + "=" + "fedcba00",
        "R64@"+h(iat798Addr)+"="+h(newTarget798),
        "P798:42422ad:2222222222222222:f000000000003000:fedcba",
        "W64@" + Long.toUnsignedString(iat778Addr, 16) + "=" + Long.toUnsignedString(newTarget778, 16),
        "R64@"+h(iat778Addr)+"="+h(newTarget778),
        "P778:42422b8:4444444444444444:9999999999999999:80000001",
        "W64@" + Long.toUnsignedString(iat558Addr, 16) + "=" + Long.toUnsignedString(newTarget558, 16),
        "Pchild:42422c0:80000001:6fd0",
        "W64@" + Long.toUnsignedString(iat558Addr, 16) + "=" + Long.toUnsignedString(finalTarget558, 16),
        "R64@"+h(iat558Addr)+"="+h(finalTarget558),
        "Pfinal:42422c7:7777777777777777:80000001"
    };
    events(log, expected);

    // Silent peek final states
    equal(m.peek(iat798Addr, 8), newTarget798, "final iat798");
    equal(m.peek(iat778Addr, 8), newTarget778, "final iat778");
    equal(m.peek(iat558Addr, 8), finalTarget558, "final iat558");
    equal(m.peek(gsBCAddr, 4), 0xfedcba00L, "final gsBC");

    equal(m.peek(gsBCAddr-1,1),0xa5,"GS DWORDbefore");equal(m.peek(gsBCAddr+4,1),0x5a,"GS DWORDafter");
    equal(m.peek(iat798Addr-1,1),0xc3,"first IATbefore");equal(m.peek(iat798Addr+8,1),0x3c,"first IATafter");
    equal(m.peek(iat558Addr-1,1),0x69,"last IATbefore");equal(m.peek(iat558Addr+8,1),0x96,"last IATafter");
    done("gsClearFresh");
}
}
