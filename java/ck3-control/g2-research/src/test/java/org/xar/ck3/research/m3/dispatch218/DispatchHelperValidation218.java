package org.xar.ck3.research.m3.dispatch218;

import java.util.*;
import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import org.xar.ck3.research.m3.tail217.TerminalTailTarget217Api;
import org.xar.ck3.research.m3.tail217.TerminalTailTarget217;

/** Owner mechanical byte fixture; only appended test methods supply semantic literals. */
public final class DispatchHelperValidation218 {
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
    static final class Mem implements TerminalTailTarget217Api.Memory {
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
    static class Child implements DispatchHelper218Api.Ports {
        @Override public void enter(NativeTaskMemory m,long site,int ecx) {throw new AssertionError("unexpected enter");}
        @Override public void call42420f8(NativeTaskMemory m,long site,long rcx) {throw new AssertionError("unexpected middle");}
        @Override public long leave(NativeTaskMemory m,long site,int ecx,long rbx) {throw new AssertionError("unexpected leave");}
    }
    static class Caller implements TerminalTailTarget217Api.Ports {
        @Override public long call43da620(TerminalTailTarget217Api.Memory m,long site,long target,int ecx) {throw new AssertionError("unexpected lookup");}
        @Override public void call42422d0(TerminalTailTarget217Api.Memory m,long site,int ecx) {throw new AssertionError("unexpected header");}
        @Override public long call42420c0(TerminalTailTarget217Api.Memory m,long site,long rcx,long rdx,long r8,long r9) {throw new AssertionError("unexpected helper");}
        @Override public void call4242284(TerminalTailTarget217Api.Memory m,long site,int ecx) {throw new AssertionError("unexpected terminal");}
    }
    public static void main(String[] args) {
        directFreshAndAlias();
        tailsReturn();
        guardsAndDelegates();
        actualCaller();
        System.out.println("GROUPS="+groups+" EVENTS="+eventCount+" MEMORY="+memoryEvents+" PORTS="+portEvents+" MIXED_CHECKS="+checks);
    }
static void directFreshAndAlias() {
    List<String> a = new ArrayList<>();
    Mem m = new Mem(a);
    m.seed32(0x1000L,0x80000001); m.seed32(0x2000L,0x10203040);
    m.seed8(0xfffL,0xa5); m.seed8(0x1004L,0x5a);
    m.seed8(0x1fffL,0xc3); m.seed8(0x2004L,0x3c);
    Child child = new Child() {
        @Override public void enter(NativeTaskMemory q,long site,int ecx) {
            same(q,m);equal(site,0x42420d7L,"enter site");equal(ecx,0x80000001,"enter signed");
            a.add("Penter:"+h(Integer.toUnsignedLong(ecx)));q.writeInt32(0x2000L,-1);
        }
        @Override public void call42420f8(NativeTaskMemory q,long site,long rcx) {
            same(q,m);equal(site,0x42420e0L,"middle site");equal(rcx,0x3000L,"saved R8");
            a.add("Pmiddle:"+h(rcx));q.writeInt32(0x2000L,0x81234567);
        }
        @Override public long leave(NativeTaskMemory q,long site,int ecx,long rbx) {
            same(q,m);equal(site,0x42420e8L,"leave site");equal(ecx,0x81234567,"fresh signed ECX");equal(rbx,0x2000L,"saved R9 address");
            a.add("Pleave:"+h(Integer.toUnsignedLong(ecx))+":"+h(rbx));return 0xfedcba9876543210L;
        }
    };
    equal(DispatchHelper42420C0.execute(m,child,new DispatchHelper218Api.Input(0x1000L,0x3000L,0x2000L)),0xfedcba9876543210L,"last full64 RAX");
    events(a,"R32@1000=80000001","Penter:80000001","W32@2000=ffffffff","Pmiddle:3000","W32@2000=81234567","R32@2000=81234567","Pleave:81234567:2000");
    equal(m.peek(0x1000L,4),0x80000001L,"first data unchanged");equal(m.peek(0x2000L,4),0x81234567L,"final second data");
    equal(m.peek(0xfffL,1),0xa5,"first before");equal(m.peek(0x1004L,1),0x5a,"first after");
    equal(m.peek(0x1fffL,1),0xc3,"second before");equal(m.peek(0x2004L,1),0x3c,"second after");
    List<String> b = new ArrayList<>(); Mem n = new Mem(b);
    n.seed32(0x4000L,-7);n.seed8(0x3fffL,0x69);n.seed8(0x4004L,0x96);
    Child alias = new Child() {
        @Override public void enter(NativeTaskMemory q,long site,int ecx) {
            same(q,n);equal(site,0x42420d7L,"alias enter site");equal(ecx,-7,"alias first ECX");
            b.add("Penter:"+h(Integer.toUnsignedLong(ecx)));q.writeInt32(0x4000L,Integer.MIN_VALUE);
        }
        @Override public void call42420f8(NativeTaskMemory q,long site,long rcx) {
            same(q,n);equal(site,0x42420e0L,"alias middle site");equal(rcx,0xf000000000006000L,"full saved R8");
            b.add("Pmiddle:"+h(rcx));q.writeInt32(0x4000L,Integer.MAX_VALUE);
        }
        @Override public long leave(NativeTaskMemory q,long site,int ecx,long rbx) {
            same(q,n);equal(site,0x42420e8L,"alias leave site");equal(ecx,Integer.MAX_VALUE,"alias second ECX");equal(rbx,0x4000L,"alias R9 address");
            b.add("Pleave:"+h(Integer.toUnsignedLong(ecx))+":"+h(rbx));return 0x8000000000000042L;
        }
    };
    equal(DispatchHelper42420C0.execute(n,alias,new DispatchHelper218Api.Input(0x4000L,0xf000000000006000L,0x4000L)),0x8000000000000042L,"alias post full64");
    events(b,"R32@4000=fffffff9","Penter:fffffff9","W32@4000=80000000","Pmiddle:f000000000006000","W32@4000=7fffffff","R32@4000=7fffffff","Pleave:7fffffff:4000");
    equal(n.peek(0x4000L,4),0x7fffffffL,"alias final data");equal(n.peek(0x3fffL,1),0x69,"alias before");equal(n.peek(0x4004L,1),0x96,"alias after");
    done("directFreshAndAlias");
}

static void tailsReturn() {
    List<String> a=new ArrayList<>();Mem m=new Mem(a);int[] post={0};
    DispatchHelper218Api.ResultTails tails=new DispatchHelper218Api.ResultTails() {
        @Override public void jump43da500(NativeTaskMemory q,long rcx,long rax) {
            same(q,m);a.add("PtailEnter:"+h(rcx)+":"+h(rax));
        }
        @Override public long jump43da4f0(NativeTaskMemory q,long rcx,long rax,long rbx) {
            same(q,m);a.add("PtailLeave:"+h(rcx)+":"+h(rax)+":"+h(rbx));
            int invocation=post[0]++;check(invocation<2,"only two post calls");
            return invocation==0?0xf123456789abcdefL:0x8000000100000055L;
        }
    };
    Child fallback=new Child() {
        @Override public void call42420f8(NativeTaskMemory q,long site,long rcx) {
            same(q,m);equal(site,0x42420e0L,"tail middle site");a.add("Pmiddle:"+h(rcx));
        }
    };
    DispatchHelper218Api.Ports bound=DispatchIndexedTailBinding218.bind(m,0x10000000L,tails,fallback);
    m.seed32(0x5000L,-1);m.seed32(0x6000L,Integer.MIN_VALUE);
    m.seed8(0x4fffL,0xaa);m.seed8(0x5004L,0xbb);m.seed8(0x5fffL,0xcc);m.seed8(0x6004L,0xdd);
    equal(DispatchHelper42420C0.execute(m,bound,new DispatchHelper218Api.Input(0x5000L,0x7000L,0x6000L)),0xf123456789abcdefL,"first actual result-tail RAX");
    events(a,"R32@5000=ffffffff","PtailEnter:15c5d308:15c5d330","Pmiddle:7000","R32@6000=80000000","PtailLeave:ffffffec15c5d330:15c5d330:6000");
    a.clear();m.seed32(0x5000L,Integer.MAX_VALUE);m.seed32(0x6000L,-2);
    equal(DispatchHelper42420C0.execute(m,bound,new DispatchHelper218Api.Input(0x5000L,0x9000L,0x6000L)),0x8000000100000055L,"second fresh result-tail RAX");
    events(a,"R32@5000=7fffffff","PtailEnter:1415c5d308:15c5d330","Pmiddle:9000","R32@6000=fffffffe","PtailLeave:15c5d2e0:15c5d330:6000");
    equal(post[0],2,"exactly two post callbacks");equal(m.peek(0x5000L,4),0x7fffffffL,"last input");equal(m.peek(0x6000L,4),0xfffffffeL,"last leave input");
    equal(m.peek(0x4fffL,1),0xaa,"tail before first");equal(m.peek(0x5004L,1),0xbb,"tail after first");equal(m.peek(0x5fffL,1),0xcc,"tail before second");equal(m.peek(0x6004L,1),0xdd,"tail after second");
    done("tailsReturn");
}

static void guardsAndDelegates() {
    List<String> a=new ArrayList<>();Mem m=new Mem(a),foreign=new Mem(a);
    Caller fallback=new Caller() {
        @Override public long call43da620(TerminalTailTarget217Api.Memory q,long site,long target,int ecx) {
            same(q,foreign);a.add("Plookup:"+h(site)+":"+h(target)+":"+h(Integer.toUnsignedLong(ecx)));return 0xf123456789abcdefL;
        }
        @Override public void call42422d0(TerminalTailTarget217Api.Memory q,long site,int ecx) {
            same(q,m);a.add("Pheader:"+h(site)+":"+h(Integer.toUnsignedLong(ecx)));
        }
        @Override public void call4242284(TerminalTailTarget217Api.Memory q,long site,int ecx) {
            same(q,foreign);a.add("Pterminal:"+h(site)+":"+h(Integer.toUnsignedLong(ecx)));
        }
    };
    TerminalTailTarget217Api.Ports caller=DispatchHelperBinding218.bind(m,new Child(),fallback);
    equal(caller.call43da620(foreign,0x6001L,0xfedcba9876543210L,-123),0xf123456789abcdefL,"lookup delegate full64");
    caller.call42422d0(m,0x7777L,Integer.MIN_VALUE);caller.call4242284(foreign,0x8888L,Integer.MAX_VALUE);
    events(a,"Plookup:6001:fedcba9876543210:ffffff85","Pheader:7777:80000000","Pterminal:8888:7fffffff");a.clear();
    iae(()->caller.call42420c0(foreign,0x4242266L,1,2,3,4));events(a);
    iae(()->caller.call42420c0(m,0x4242267L,1,2,3,4));events(a);
    check(m.data.isEmpty()&&foreign.data.isEmpty(),"caller guards before byte effects");
    DispatchHelper218Api.ResultTails tails=new DispatchHelper218Api.ResultTails() {
        @Override public void jump43da500(NativeTaskMemory q,long rcx,long rax) {throw new AssertionError("rejected enter reached tail");}
        @Override public long jump43da4f0(NativeTaskMemory q,long rcx,long rax,long rbx) {throw new AssertionError("rejected leave reached tail");}
    };
    Child middle=new Child() {
        @Override public void call42420f8(NativeTaskMemory q,long site,long rcx) {
            same(q,m);a.add("PmiddleDelegate:"+h(site)+":"+h(rcx));
        }
    };
    DispatchHelper218Api.Ports adapter=DispatchIndexedTailBinding218.bind(m,0x10000000L,tails,middle);
    iae(()->adapter.enter(foreign,0x42420d7L,-1));events(a);
    iae(()->adapter.enter(m,0x42420d8L,-1));events(a);
    iae(()->adapter.leave(foreign,0x42420e8L,-2,0xf000000000006000L));events(a);
    iae(()->adapter.leave(m,0x42420e9L,-2,0xf000000000006000L));events(a);
    check(m.data.isEmpty()&&foreign.data.isEmpty(),"tail guards before byte effects");
    adapter.call42420f8(m,0x9000L,0xffffffffabcdef01L);
    events(a,"PmiddleDelegate:9000:ffffffffabcdef01");
    done("guardsAndDelegates");
}

static void actualCaller() {
    List<String> a=new ArrayList<>();Mem m=new Mem(a);
    m.seed8(0x700fL,0xa1);m.seed8(0x7014L,0xa2);m.seed8(0x701cL,0xa3);
    m.seed8(0x7021L,0xa4);m.seed8(0x6fd4L,0xb1);m.seed8(0x6ff0L,0xb2);
    Child child=new Child() {
        @Override public void enter(NativeTaskMemory q,long site,int ecx) {
            same(q,m);equal(site,0x42420d7L,"chain enter site");equal(ecx,2,"chain first local");
            a.add("Penter:"+h(Integer.toUnsignedLong(ecx)));
        }
        @Override public void call42420f8(NativeTaskMemory q,long site,long rcx) {
            same(q,m);equal(site,0x42420e0L,"chain middle site");equal(rcx,0x6fd8L,"chain saved R8");
            a.add("Pmiddle:"+h(rcx));q.writeInt32(0x7018L,0x87654321);q.writeInt32(0x6fccL,-3);
        }
        @Override public long leave(NativeTaskMemory q,long site,int ecx,long rbx) {
            same(q,m);equal(site,0x42420e8L,"chain leave site");equal(ecx,-3,"chain fresh R9 data");equal(rbx,0x6fccL,"chain R9 address");
            a.add("Pleave:"+h(Integer.toUnsignedLong(ecx))+":"+h(rbx));return 0xfedcba9801234567L;
        }
    };
    TerminalTailTarget217Api.Ports bound=DispatchHelperBinding218.bind(m,child,new Caller());
    Caller observed=new Caller() {
        @Override public long call42420c0(TerminalTailTarget217Api.Memory q,long site,long rcx,long rdx,long r8,long r9) {
            same(q,m);equal(site,0x4242266L,"actual helper site");equal(rcx,0x6fc8L,"actual RCX");equal(rdx,0x6fd0L,"actual RDX");equal(r8,0x6fd8L,"actual R8");equal(r9,0x6fccL,"actual R9");
            a.add("Pactual:"+h(site)+":"+h(rcx)+":"+h(rdx)+":"+h(r8)+":"+h(r9));
            return bound.call42420c0(q,site,rcx,rdx,r8,r9);
        }
    };
    TerminalTailTarget217Api.Outcome result=TerminalTailTarget217.execute(m,observed,
        new TerminalTailTarget217Api.Input(0x180000000L,0x2468ace0,0xf7654321,0x80000001,new TerminalTailTarget217Api.Scratch(0x7000L)));
    check(result instanceof TerminalTailTarget217Api.NormalReturn,"chain normal return");
    equal(((TerminalTailTarget217Api.NormalReturn)result).rawRax(),0xfedcba9801234567L,"actual217 consumes final postRAX");
    events(a,"W32@7018=80000001","W32@7010=f7654321","W8@7020=0",
        "W64@6fd8=7010","W64@6fe0=7018","W64@6fe8=7020","W32@6fcc=2","W32@6fd0=2",
        "Pactual:4242266:6fc8:6fd0:6fd8:6fcc","R32@6fd0=2","Penter:2","Pmiddle:6fd8",
        "W32@7018=87654321","W32@6fcc=fffffffd","R32@6fcc=fffffffd","Pleave:fffffffd:6fcc","R32@7018=87654321");
    equal(m.peek(0x7010L,4),0xf7654321L,"actual EDX home");equal(m.peek(0x7018L,4),0x87654321L,"fresh R8 home");equal(m.peek(0x7020L,1),0,"actual flag byte");
    equal(m.peek(0x6fd8L,8),0x7010L,"first pointer local");equal(m.peek(0x6fe0L,8),0x7018L,"second pointer local");equal(m.peek(0x6fe8L,8),0x7020L,"third pointer local");
    equal(m.peek(0x6fccL,4),0xfffffffdL,"actual second local effects");equal(m.peek(0x6fd0L,4),2,"actual first local");
    equal(m.peek(0x700fL,1),0xa1,"home preceding byte");equal(m.peek(0x7014L,1),0xa2,"between homes byte");equal(m.peek(0x701cL,1),0xa3,"after second home byte");
    equal(m.peek(0x7021L,1),0xa4,"after flag byte");equal(m.peek(0x6fd4L,1),0xb1,"local gap byte");equal(m.peek(0x6ff0L,1),0xb2,"after local pointers byte");
    check(!m.data.containsKey(0x6fc8L),"unused helper RCX remains unmapped");
    done("actualCaller");
}

}
