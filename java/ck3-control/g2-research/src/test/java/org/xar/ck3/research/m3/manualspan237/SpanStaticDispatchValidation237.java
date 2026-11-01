package org.xar.ck3.research.m3.manualspan237;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m3.span228.CallbackSpan228Api;
import org.xar.ck3.research.m3.span228.CallbackSpan424E1AC;
import org.xar.ck3.research.m3.span237.SpanStaticDispatch237Api;
import org.xar.ck3.research.m3.span237.SpanStaticDispatchBinding237;

public final class SpanStaticDispatchValidation237 {
    private SpanStaticDispatchValidation237() { }
    private static int checks,groups,events;
    private static void check(boolean ok,String label) { checks++;if(!ok)throw new AssertionError(label); }
    private static String h(long value) { return Long.toUnsignedString(value,16); }
    private static String mem(CallbackSpan228Api.Memory memory) {
        if(memory instanceof Ram ram)return ram.name;throw new AssertionError("unlabelled Memory");
    }
    private static String args(CallbackSpan228Api.Arguments value) {
        if(value==null)return "null";
        if(value==CallbackSpan228Api.AfterOpaqueReturn.UNKNOWN)return "unknown";
        if(value instanceof CallbackSpan228Api.EntryArguments entry)return "entry:"+h(entry.rcx())+":"+h(entry.rdx());
        throw new AssertionError("unknown Arguments type");
    }
    private static String rw(String kind,long address,long value) { return kind+":"+h(address)+":"+h(value); }
    private static String i(CallbackSpan228Api.Memory memory,long site,long target,long rax,CallbackSpan228Api.Arguments value) {
        return "I:"+mem(memory)+":"+h(site)+":"+h(target)+":"+h(rax)+":"+args(value);
    }
    private static String t(CallbackSpan228Api.Memory memory,long site,long rax,long rcx,CallbackSpan228Api.EntryArguments value) {
        return "T:"+mem(memory)+":"+h(site)+":"+h(rax)+":"+h(rcx)+":"+args(value);
    }
    private static final class Ram implements CallbackSpan228Api.Memory {
        final String name;final List<String> trace=new ArrayList<>();final Map<Long,Byte> bytes=new HashMap<>();
        Ram(String name) {this.name=name;}
        private long raw(long address,int width) {
            long result=0;for(int index=0;index<width;index++){Byte value=bytes.get(address+index);if(value==null)throw new AssertionError("unmapped "+name+":"+h(address+index));result|=(value.longValue()&255L)<<(8*index);}return result;
        }
        private void store(long address,int width,long value) {for(int index=0;index<width;index++)bytes.put(address+index,(byte)(value>>>(8*index)));}
        void seed8(long address,int value) {check((value&~255)==0,"seed8 range");store(address,1,value);}
        void seed32(long address,int value) {store(address,4,Integer.toUnsignedLong(value));}
        void seed64(long address,long value) {store(address,8,value);}
        void effect8(long address,int value) {check((value&~255)==0,"effect8 range");trace.add(rw("E8",address,value));store(address,1,value);}
        void effect64(long address,long value) {trace.add(rw("E64",address,value));store(address,8,value);}
        long peek64(long address) {return raw(address,8);}
        int peek8(long address) {return (int)raw(address,1);}
        Map<Long,Byte> snapshot() {return Map.copyOf(bytes);}
        @Override public long readPointer(long address) {long value=raw(address,8);trace.add(rw("R64",address,value));return value;}
        @Override public int readInt32(long address) {long value=raw(address,4);trace.add(rw("R32",address,value));return (int)value;}
        @Override public int readUnsigned8(long address) {int value=(int)raw(address,1);trace.add(rw("R8",address,value));return value;}
        @Override public int readUnsigned16(long address) {int value=(int)raw(address,2);trace.add(rw("R16",address,value));return value;}
        @Override public void write8(long address,int value) {check((value&~255)==0,"W8 range");trace.add(rw("W8",address,value));store(address,1,value);}
        @Override public void writeInt32(long address,int value) {trace.add(rw("W32",address,Integer.toUnsignedLong(value)));store(address,4,Integer.toUnsignedLong(value));}
        @Override public void writeInt64(long address,long value) {trace.add(rw("W64",address,value));store(address,8,value);}
        @Override public void exchangeInt32(long address,int value) {trace.add(rw("X32",address,Integer.toUnsignedLong(value)));store(address,4,Integer.toUnsignedLong(value));}
    }
    @FunctionalInterface private interface FallbackHook {
        void call(CallbackSpan228Api.Memory memory,long site,long actualTarget,long rax,CallbackSpan228Api.Arguments arguments);
    }
    @FunctionalInterface private interface JumpHook {
        int call(CallbackSpan228Api.Memory memory,long site,long rax,long rcx,CallbackSpan228Api.EntryArguments arguments);
    }
    private static final class Fallback implements CallbackSpan228Api.Ports {
        final Ram recorder;final FallbackHook hook;int calls;
        Fallback(Ram recorder,FallbackHook hook) {this.recorder=recorder;this.hook=hook;}
        @Override public void call43dbba8(CallbackSpan228Api.Memory memory,long site,long actualTarget,long rax,CallbackSpan228Api.Arguments arguments) {
            calls++;recorder.trace.add(i(memory,site,actualTarget,rax,arguments));hook.call(memory,site,actualTarget,rax,arguments);
        }
    }
    private static final class Target implements SpanStaticDispatch237Api.TailPort {
        final Ram recorder;final JumpHook hook;final List<Integer> normalResults=new ArrayList<>();int calls;
        Target(Ram recorder,JumpHook hook) {this.recorder=recorder;this.hook=hook;}
        @Override public int jumpRax(CallbackSpan228Api.Memory memory,long site,long rax,long rcx,CallbackSpan228Api.EntryArguments arguments) {
            calls++;recorder.trace.add(t(memory,site,rax,rcx,arguments));int result=hook.call(memory,site,rax,rcx,arguments);normalResults.add(result);return result;
        }
    }
    private static void rejected(Runnable work,String label) {try{work.run();}catch(IllegalArgumentException expected){checks++;return;}throw new AssertionError("no rejection "+label);}
    private static void sameException(Runnable work,RuntimeException expected,String label) {try{work.run();}catch(RuntimeException actual){check(actual==expected,label);return;}throw new AssertionError("no exception "+label);}
    private static void complete(Ram memory,List<String> expected,String label) {check(memory.trace.equals(expected),label+" full trace\nexpected="+expected+"\nactual="+memory.trace);groups++;events+=memory.trace.size();}
    private static void directProtocol() {
        final Ram memory=new Ram("direct"),foreign=new Ram("foreign");
        memory.seed8(0x10L,0xa5);foreign.seed8(-1L,0x5a);
        final Map<Long,Byte> before=memory.snapshot(),foreignBefore=foreign.snapshot();
        final long base=0x100000000L,qualified=base+0x4267630L,site=0x424e1e9L;
        final CallbackSpan228Api.EntryArguments entry=new CallbackSpan228Api.EntryArguments(0xfedcba9876543210L,0x8123456789abcdefL);
        final CallbackSpan228Api.Arguments unknown=CallbackSpan228Api.AfterOpaqueReturn.UNKNOWN;
        final long[] activeRax={0xdeadbeef01234567L,0x8000000000000001L,0xcafebabef00d1234L};
        final RuntimeException targetFailure=new RuntimeException("target marker"),fallbackFailure=new RuntimeException("fallback marker");
        final int[] activeIndex={0},passiveIndex={0};
        final long[] passiveSites={0x11L,0x22L,0x33L,0x44L};
        final long[] passiveTargets={qualified,qualified,0x8877665544332211L,0x9988776655443322L};
        final long[] passiveRax={0xf123456789abcdefL,0xe23456789abcdef0L,0xd3456789abcdef01L,0xc456789abcdef012L};
        final CallbackSpan228Api.Arguments[] passiveArguments={unknown,null,entry,entry};
        final Target target=new Target(memory,(actual,s,r,rcx,arguments)->{
            final int index=activeIndex[0]++;
            check(index<3,"active no replay");check(actual==memory,"active same Memory");
            check(s==site,"active exact site");check(r==activeRax[index],"active full liveRAX");
            check(rcx==entry.rcx(),"full entry RCX");check(arguments==entry,"original Entry object");
            check(arguments.rdx()==0x8123456789abcdefL,"full entry RDX");
            if(index==2)throw targetFailure;
            return index==0?0:0x80000001;
        });
        final Fallback fallback=new Fallback(memory,(actual,s,targetRax,r,arguments)->{
            final int index=passiveIndex[0]++;
            check(index<4,"passive once");check(actual==foreign,"passive original foreign Memory");
            check(s==passiveSites[index],"passive exact site");check(targetRax==passiveTargets[index],"passive exact IAT target");
            check(r==passiveRax[index],"passive full liveRAX");check(arguments==passiveArguments[index],"passive original Arguments object");
            if(index==3)throw fallbackFailure;
        });
        final CallbackSpan228Api.Ports bound=SpanStaticDispatchBinding237.bind(base,memory,target,fallback);
        final CallbackSpan228Api.Ports passiveOnly=SpanStaticDispatchBinding237.bind(base,memory,null,fallback);
        final List<String> expected=List.of(
            t(memory,site,activeRax[0],entry.rcx(),entry),
            t(memory,site,activeRax[1],entry.rcx(),entry),
            t(memory,site,activeRax[2],entry.rcx(),entry),
            i(foreign,passiveSites[0],passiveTargets[0],passiveRax[0],unknown),
            i(foreign,passiveSites[1],passiveTargets[1],passiveRax[1],null),
            i(foreign,passiveSites[2],passiveTargets[2],passiveRax[2],entry),
            i(foreign,passiveSites[3],passiveTargets[3],passiveRax[3],entry));
        bound.call43dbba8(memory,site,qualified,activeRax[0],entry);
        bound.call43dbba8(memory,site,qualified,activeRax[1],entry);
        sameException(()->bound.call43dbba8(memory,site,qualified,activeRax[2],entry),targetFailure,"active original exception");
        final int eventsBeforeGuard=memory.trace.size();
        rejected(()->bound.call43dbba8(foreign,site,qualified,1L,entry),"active foreign");
        rejected(()->bound.call43dbba8(memory,site+1L,qualified,2L,entry),"active wrong site");
        check(memory.trace.size()==eventsBeforeGuard&&target.calls==3&&fallback.calls==0,"guards before effects");
        passiveOnly.call43dbba8(foreign,passiveSites[0],passiveTargets[0],passiveRax[0],unknown);
        passiveOnly.call43dbba8(foreign,passiveSites[1],passiveTargets[1],passiveRax[1],null);
        passiveOnly.call43dbba8(foreign,passiveSites[2],passiveTargets[2],passiveRax[2],entry);
        sameException(()->bound.call43dbba8(foreign,passiveSites[3],passiveTargets[3],passiveRax[3],entry),fallbackFailure,"passive original exception");
        check(activeIndex[0]==3&&target.calls==3,"three active calls");
        check(passiveIndex[0]==4&&fallback.calls==4,"four passive calls");
        check(target.normalResults.equals(List.of(0,0x80000001)),"real normal int results");
        check(memory.snapshot().equals(before)&&foreign.snapshot().equals(foreignBefore),"direct complete Memory unchanged");
        check(memory.peek8(0x10L)==0xa5&&foreign.peek8(-1L)==0x5a,"direct byte canaries");
        check(foreign.trace.isEmpty(),"foreign no Memory methods");
        complete(memory,expected,"direct protocol");
    }
    private static void actualCaller() {
        final Ram memory=new Ram("caller");
        final long base=0x100000000L,iat=base+0x43dbba8L,qualified=base+0x4267630L,other=0x8877665544332211L,site=0x424e1e9L;
        final long pa=0xfedcba9876543210L,pb=0x8123456789abcdefL,pc=0xaabbccddeeff0011L;
        final long pd=0xdeadbeef01234567L,pe=0x8000000000000001L,pf=0xcafebabef00d1234L;
        memory.seed64(iat,other);
        memory.seed64(0x1000L,0L);memory.seed64(0x1008L,pa);memory.seed64(0x1010L,0L);memory.seed64(0x1018L,pc);
        memory.seed64(0x2000L,pd);memory.seed64(0x2008L,pe);memory.seed64(0x3000L,pf);
        final long[] canaryAddresses={0xfffL,0x1020L,0x1fffL,0x2010L,0x2fffL,0x3008L,iat-1L,iat+8L};
        for(int index=0;index<canaryAddresses.length;index++)memory.seed8(canaryAddresses[index],0xa0+index);
        final Map<Long,Byte> before=memory.snapshot();
        final Map<Long,Byte> expectedBytes=new HashMap<>(before);
        for(int index=0;index<8;index++) {
            expectedBytes.put(0x1010L+index,(byte)(pb>>>(index*8)));
            expectedBytes.put(iat+index,(byte)(qualified>>>(index*8)));
        }
        final CallbackSpan228Api.EntryArguments[] activeEntries=new CallbackSpan228Api.EntryArguments[3];
        final CallbackSpan228Api.EntryArguments[] passiveEntry=new CallbackSpan228Api.EntryArguments[1];
        final int[] activeIndex={0},passiveIndex={0};
        final Target target=new Target(memory,(actual,s,rax,knownRcx,arguments)->{
            final int index=activeIndex[0]++;
            check(index<3,"caller target once per qualified invocation");
            check(actual==memory&&s==site,"caller target identity/site");
            check(arguments!=null,"caller target Entry");
            activeEntries[index]=arguments;
            if(index==0) {
                check(rax==pa,"leading zero keeps first nonzero full RAX");
                check(knownRcx==0x1000L&&arguments.rcx()==0x1000L&&arguments.rdx()==0x1020L,"leadingzero original start/end");
                check(arguments!=passiveEntry[0],"different execute fresh Entry after passive");
                memory.effect64(0x1010L,pb);
                memory.effect64(iat,other);
                return 0;
            }
            check(rax==pf,"reset invocation full RAX");
            check(knownRcx==0x3000L&&arguments.rcx()==0x3000L&&arguments.rdx()==0x3008L,"reset independent start/end");
            check(arguments!=activeEntries[0]&&arguments!=passiveEntry[0],"reset no initial capture");
            if(index==2)check(arguments!=activeEntries[1],"same input second execute new Entry object");
            return index==1?0x80000001:-1;
        });
        final Fallback fallback=new Fallback(memory,(actual,s,actualTarget,rax,arguments)->{
            final int index=passiveIndex[0]++;
            check(index<4,"caller fallback once per opaque dispatch");
            check(actual==memory&&s==site,"caller fallback original identity/site");
            if(index==0) {
                check(rax==pd&&actualTarget==other,"first passive original RAX/target");
                check(arguments instanceof CallbackSpan228Api.EntryArguments,"first passive Entry");
                final CallbackSpan228Api.EntryArguments entry=(CallbackSpan228Api.EntryArguments)arguments;
                passiveEntry[0]=entry;
                check(entry.rcx()==0x2000L&&entry.rdx()==0x2010L,"passive original start/end");
                memory.effect64(iat,qualified);
            } else {
                check(arguments==CallbackSpan228Api.AfterOpaqueReturn.UNKNOWN,"all later callbacks exact UNKNOWN");
                if(index==1)check(rax==pe&&actualTarget==qualified,"passive normal then matching target still fallback");
                if(index==2) {
                    check(rax==pb&&actualTarget==other,"fresh changed future cell and IAT");
                    memory.effect64(iat,qualified);
                }
                if(index==3)check(rax==pc&&actualTarget==qualified,"matching final target with UNKNOWN stays fallback");
            }
        });
        final CallbackSpan228Api.Ports bound=SpanStaticDispatchBinding237.bind(base,memory,target,fallback);
        final CallbackSpan228Api.EntryArguments expectedB=new CallbackSpan228Api.EntryArguments(0x2000L,0x2010L);
        final CallbackSpan228Api.EntryArguments expectedA=new CallbackSpan228Api.EntryArguments(0x1000L,0x1020L);
        final CallbackSpan228Api.EntryArguments expectedC=new CallbackSpan228Api.EntryArguments(0x3000L,0x3008L);
        final CallbackSpan228Api.Arguments unknown=CallbackSpan228Api.AfterOpaqueReturn.UNKNOWN;
        final List<String> expected=List.of(
            rw("R64",0x2000L,pd),rw("R64",iat,other),i(memory,site,other,pd,expectedB),rw("E64",iat,qualified),
            rw("R64",0x2008L,pe),rw("R64",iat,qualified),i(memory,site,qualified,pe,unknown),
            rw("R64",0x1000L,0L),rw("R64",0x1008L,pa),rw("R64",iat,qualified),t(memory,site,pa,0x1000L,expectedA),
            rw("E64",0x1010L,pb),rw("E64",iat,other),
            rw("R64",0x1010L,pb),rw("R64",iat,other),i(memory,site,other,pb,unknown),rw("E64",iat,qualified),
            rw("R64",0x1018L,pc),rw("R64",iat,qualified),i(memory,site,qualified,pc,unknown),
            rw("R64",0x3000L,pf),rw("R64",iat,qualified),t(memory,site,pf,0x3000L,expectedC),
            rw("R64",0x3000L,pf),rw("R64",iat,qualified),t(memory,site,pf,0x3000L,expectedC));
        CallbackSpan424E1AC.execute(memory,bound,new CallbackSpan228Api.Input(base,0x2000L,0x2010L));
        CallbackSpan424E1AC.execute(memory,bound,new CallbackSpan228Api.Input(base,0x1000L,0x1020L));
        final CallbackSpan228Api.Input resetInput=new CallbackSpan228Api.Input(base,0x3000L,0x3008L);
        CallbackSpan424E1AC.execute(memory,bound,resetInput);
        CallbackSpan424E1AC.execute(memory,bound,resetInput);
        check(target.calls==3&&activeIndex[0]==3,"caller three active callbacks");
        check(fallback.calls==4&&passiveIndex[0]==4,"caller four passive callbacks");
        check(target.normalResults.equals(List.of(0,0x80000001,-1)),"caller real int results only void ignored");
        check(memory.peek64(iat)==qualified&&memory.peek64(0x1010L)==pb,"opaque final words");
        check(memory.snapshot().equals(expectedBytes),"caller complete final bytes");
        for(int index=0;index<canaryAddresses.length;index++)check(memory.peek8(canaryAddresses[index])==0xa0+index,"caller exact byte canary "+index);
        final int eventsBeforeEmpty=memory.trace.size();
        final Map<Long,Byte> beforeEmpty=memory.snapshot();
        CallbackSpan424E1AC.execute(memory,bound,new CallbackSpan228Api.Input(base,0x5000L,0x5000L));
        CallbackSpan424E1AC.execute(memory,bound,new CallbackSpan228Api.Input(base,0x8000L,0x7000L));
        CallbackSpan424E1AC.execute(memory,bound,new CallbackSpan228Api.Input(base,0L,-1L));
        check(memory.trace.size()==eventsBeforeEmpty&&target.calls==3&&fallback.calls==4,"bounded count0/reverse/wrap no observation");
        check(memory.snapshot().equals(beforeEmpty),"zero-count complete bytes unchanged");
        complete(memory,expected,"actual100 caller");
    }
    public static void main(String[] ignored) {directProtocol();actualCaller();System.out.println("SPAN_STATIC237_PASS groups="+groups+" orderedEvents="+events+" mixedChecks="+checks+" Native=0 Game=0");}
}
