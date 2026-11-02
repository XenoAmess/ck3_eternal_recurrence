package org.xar.ck3.study.m6.vtable221;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.study.m6.vtable221.VirtualForward221Api.Input;
import org.xar.ck3.study.m6.vtable221.VirtualForward221Api.Invocation;

/** Five new logical-body scenes; scripted virtual outcomes are not real allocation, Native ABI or Game. */
public final class StaticVirtualForward221Test {
    private StaticVirtualForward221Test() { }
    private static int checks;
    private record Read(long address) { }
    private record Call(boolean tail, Invocation invocation) { }
    private static final class Ram implements VirtualForward221Api.Memory {
        final Map<Long,Long> words = new HashMap<>();
        final List<Object> events = new ArrayList<>();
        Ram put(long key,long value) { words.put(key,value); return this; }
        @Override public long read64(long address) {
            events.add(new Read(address));
            Long value=words.get(address);
            if(value==null)throw new AssertionError("unseeded logical RAM read: "+Long.toHexString(address));
            return value.longValue();
        }
        @Override public int read32(long address) { throw new AssertionError("unexpected32read"); }
        @Override public int read8(long address) { throw new AssertionError("unexpected8read"); }
        @Override public void write64(long address,long value) { throw new AssertionError("unexpectedlogicalbodywrite"); }
        @Override public void write32(long address,int value) { throw new AssertionError("unexpected32write"); }
        @Override public void write8(long address,int value) { throw new AssertionError("unexpected8write"); }
    }
    private static final class Script implements VirtualForward221Api.Calls {
        final Ram memory;
        final long firstResult,lastResult;
        final Map<Long,Long> firstWrites;
        final RuntimeException firstFailure;
        int calls;
        Script(Ram memory,long firstResult,long lastResult,Map<Long,Long> firstWrites,RuntimeException firstFailure) {
            this.memory=memory;this.firstResult=firstResult;this.lastResult=lastResult;
            this.firstWrites=firstWrites;this.firstFailure=firstFailure;
        }
        private long invoke(boolean tail,Invocation actual) {
            memory.events.add(new Call(tail,actual));
            int index=calls++;
            if(index==0) {
                if(firstFailure!=null)throw firstFailure;
                memory.words.putAll(firstWrites);
                return firstResult;
            }
            if(index==1)return lastResult;
            throw new AssertionError("morethan2virtualedges");
        }
        @Override public long call(Invocation actual) { return invoke(false,actual); }
        @Override public long tailJump(Invocation actual) { return invoke(true,actual); }
    }
    private static void check(boolean value,String label) {
        checks++;
        if(!value)throw new AssertionError(label);
    }
    private static Call call(boolean tail,int site,long function,long rax,long rcx,long rdx,long r8,long r9) {
        return new Call(tail,new Invocation(site,function,rax,rcx,rdx,r8,r9));
    }
    private static void slot08Fresh() {
        Ram m=new Ram().put(0x1000,0x2000).put(0x2038,0x3000).put(0x4000,0x5000).put(0x5008,0x6000).put(0x5108,0x6100);
        Script script=new Script(m,0x4000,0xFEDCBA9876543210L,Map.of(0x1000L,0xDEADL,0x2038L,0xBADL,0x4000L,0x5100L),null);
        long d=0xF000000000000011L,a=0x8000000000000012L,r9=0x9000000000000013L;
        long returned=StaticVirtualForward221.fromSlot08(new Input(0x1000,d,a,r9),m,script);
        check(returned==0xFEDCBA9876543210L,"tailopaqueRAXnotreturned");
        check(m.events.equals(List.of(new Read(0x1000),new Read(0x2038),call(false,0x855883,0x3000,0x2000,0x1000,d,a,r9),
                new Read(0x4000),new Read(0x5108),call(true,0x8558A0,0x6100,0x4000,0x4000,d,a,0x6100))),"08freshorderedregistertrace");
        check(script.calls==2,"08exact2edges");
        check(m.words.get(0x1000L)==0xDEADL&&m.words.get(0x4000L)==0x5100L,"08controlledcallbackRAMretained");
        System.out.println("PASS slot08-fresh");
    }
    private static void slot10Self(boolean wrapped) {
        Ram m=new Ram(); Script script=new Script(m,0,0,Map.of(),null);
        long object=wrapped?0xFFFFFFFFFFFFFFF8L:0x1000;
        long pointer=wrapped?0:0x1008;
        long returned=StaticVirtualForward221.fromSlot10(new Input(object,pointer,0xFFFF000000000012L,0xABCD),m,script);
        check(returned==pointer,"10selfleaRAX");check(m.events.isEmpty(),"10self0RAMedges");check(script.calls==0,"10self0ports");
        System.out.println("PASS "+(wrapped?"slot10-wrapped-self":"slot10-self"));
    }
    private static void slot10Fresh() {
        Ram m=new Ram().put(0x1100,0x2100).put(0x2138,0x3100).put(0x4100,0x5200).put(0x5210,0x6200).put(0x5310,0x6300);
        Script script=new Script(m,0x4100,0x8000000000000055L,Map.of(0x1100L,0xDEADL,0x4100L,0x5300L),null);
        long d=0xF000000000000021L,a=0x8000000000000022L,r9=0x9000000000000023L;
        long returned=StaticVirtualForward221.fromSlot10(new Input(0x1100,d,a,r9),m,script);
        check(returned==0x8000000000000055L,"10secondopaqueRAX");
        check(m.events.equals(List.of(new Read(0x1100),new Read(0x2138),call(false,0x85584C,0x3100,0x2100,0x1100,d,a,r9),
                new Read(0x4100),new Read(0x5310),call(false,0x85585B,0x6300,0x4100,0x4100,d,a,0x5300))),"10freshCALLtableR9notfunction");
        check(script.calls==2,"10exact2calls");
        System.out.println("PASS slot10-fresh");
    }
    private static void slot08FirstThrows() {
        Ram m=new Ram().put(0x1200,0x2200).put(0x2238,0x3200);
        RuntimeException sentinel=new IllegalStateException("controlled-source221-first-callback");
        Script script=new Script(m,0,0,Map.of(),sentinel); boolean caught=false;
        try {StaticVirtualForward221.fromSlot08(new Input(0x1200,0x22,0x33,0x44),m,script);}
        catch(RuntimeException actual) {caught=true;check(actual==sentinel,"sameopaqueexceptionidentity");}
        check(caught,"opaqueexceptionpropagated");
        check(m.events.equals(List.of(new Read(0x1200),new Read(0x2238),call(false,0x855883,0x3200,0x2200,0x1200,0x22,0x33,0x44))),"throwstopsbeforefreshreadsTAIL");
        check(script.calls==1,"throwonlyfirstport");
        System.out.println("PASS slot08-first-throws");
    }
    public static void main(String[] args) {
        slot08Fresh();slot10Self(false);slot10Self(true);slot10Fresh();slot08FirstThrows();
        System.out.println("PASS 5 newlogicalscenes "+checks+" checks;0NativeABI_RSP_GPRFLAGS_allocator_Gamecredit;no216R9defaultbinding");
    }
}
