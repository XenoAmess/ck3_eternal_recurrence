package org.xar.ck3.research.m3.manualfc74238;

import java.util.ArrayDeque;
import java.util.Arrays;
import java.util.Deque;
import java.util.HashMap;
import java.util.Map;
import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import org.xar.ck3.research.m3.fc74238.Fc74Api238;
import org.xar.ck3.research.m3.fc74238.Fc74Target424FC74;

/** Independent finite supplied-storage witness; no native execution. */
public final class Fc74Validation238 {
    private Fc74Validation238() { }
    private static int checks;
    private static int scenes;
    private static int orderedEvents;

    private static void check(boolean condition,String message) {
        checks++;
        if(!condition) throw new AssertionError(message);
    }
    private static long u(int value) { return Integer.toUnsignedLong(value); }
    private record Step(String op,long[] args,long value,Runnable after) { }
    private static Step row(String op,long value,long... args) {
        return new Step(op,args.clone(),value,null);
    }
    private static Step rowAfter(String op,long value,Runnable after,long... args) {
        return new Step(op,args.clone(),value,after);
    }
    private static final class Ram implements NativeTaskMemory {
        private final Map<Long,Byte> bytes=new HashMap<>();
        private final Deque<Step> expected=new ArrayDeque<>();
        private int consumed;
        void expect(Step... rows) { expected.addAll(Arrays.asList(rows)); }
        Step take(String op,long... args) {
            Step next=expected.pollFirst();
            check(next!=null,"unexpected "+op+Arrays.toString(args));
            check(next.op().equals(op)&&Arrays.equals(next.args(),args),
                    "expected "+next.op()+Arrays.toString(next.args())+" received "+op+Arrays.toString(args));
            consumed++;
            return next;
        }
        private void rawWrite(long address,long value,int width) {
            for(int i=0;i<width;i++) bytes.put(address+i,(byte)(value>>>(8*i)));
        }
        private long rawRead(long address,int width) {
            long value=0;
            for(int i=0;i<width;i++) {
                Byte actual=bytes.get(address+i);
                if(actual==null) throw new AssertionError("unseeded byte "+Long.toUnsignedString(address+i,16));
                value|=(long)(actual&255)<<(8*i);
            }
            return value;
        }
        void seed8(long address,int value) { rawWrite(address,value,1); }
        void seed32(long address,int value) { rawWrite(address,u(value),4); }
        void seed64(long address,long value) { rawWrite(address,value,8); }
        int peek8(long address) { return (int)rawRead(address,1); }
        int peek32(long address) { return (int)rawRead(address,4); }
        long peek64(long address) { return rawRead(address,8); }
        Map<Long,Byte> snapshot() { return Map.copyOf(bytes); }
        private void effect(String op,long address,long value,int width) {
            Step next=take(op,address);
            check(next.value()==value,"opaque effect value "+op);
            rawWrite(address,value,width);
        }
        void effect32(long address,int value) { effect("E32",address,u(value),4); }
        void effect64(long address,long value) { effect("E64",address,value,8); }
        @Override public long readPointer(long address) {
            Step next=take("R64",address);long value=rawRead(address,8);
            check(next.value()==value,"R64 value");return value;
        }
        @Override public int readInt32(long address) {
            Step next=take("R32",address);int value=(int)rawRead(address,4);
            check(next.value()==u(value),"R32 unsigned encoded tuple");return value;
        }
        @Override public void writeInt32(long address,int value) {
            Step next=take("W32",address);check(next.value()==u(value),"W32 value");rawWrite(address,u(value),4);
        }
        @Override public void writeInt64(long address,long value) {
            Step next=take("W64",address);check(next.value()==value,"W64 value");rawWrite(address,value,8);
        }
        void finish(String label) {
            check(expected.isEmpty(),label+" unused events="+expected.size());
            scenes++;orderedEvents+=consumed;
        }
    }
    private static final class ScriptPorts implements Fc74Api238.Ports {
        private final Ram ram;
        ScriptPorts(Ram ram) { this.ram=ram; }
        private long call(NativeTaskMemory memory,String op,long... args) {
            check(memory==ram,"identical Memory for "+op);
            Step next=ram.take(op,args);
            if(next.after()!=null) next.after().run();
            return next.value();
        }
        @Override public int callIat43da738(NativeTaskMemory memory,long site,long target,int ecx) {
            return (int)call(memory,"P738",site,target,u(ecx));
        }
        @Override public long call424e900(NativeTaskMemory memory,long site,int ecx) {
            return call(memory,"PE900",site,u(ecx));
        }
        @Override public int call424e948(NativeTaskMemory memory,long site,int ecx,long rdx) {
            return (int)call(memory,"PE948",site,u(ecx),rdx);
        }
        @Override public long call424e2ec(NativeTaskMemory memory,long site,long rcx,long rdx) {
            return call(memory,"PE2EC",site,rcx,rdx);
        }
        @Override public void call424e364(NativeTaskMemory memory,long site,long rcx) {
            call(memory,"PE364",site,rcx);
        }
        @Override public void call424f8a8(NativeTaskMemory memory,long site,long rcx) {
            call(memory,"PF8A8",site,rcx);
        }
        @Override public void callIat43da420(NativeTaskMemory memory,long site,long target,int ecx) {
            call(memory,"P420",site,target,u(ecx));
        }
    }
    private static void sameException(Runnable work,RuntimeException expected,String label) {
        try { work.run(); }
        catch(RuntimeException actual) { check(actual==expected,label+" exception identity");return; }
        throw new AssertionError(label+" no exception");
    }

    private static void pointerPaths238() {
        {
            Ram ram=new Ram();
            ScriptPorts ports=new ScriptPorts(ram);
            long base=0x0000000010000000L;
            long index=base+0x542F328L,first=base+0x43DA738L,last=base+0x43DA420L;
            ram.seed64(index,0xBADC0FFE00000001L);
            ram.seed64(first,0xE123456789ABCDE0L);
            ram.seed64(last,0xE222222233333330L);
            ram.seed8(index-1,0xA5);ram.seed8(index+8,0x5A);
            ram.seed8(first-1,0xA6);ram.seed8(first+8,0x6A);
            ram.seed8(last-1,0xC3);ram.seed8(last+8,0x3C);
            ram.expect(
                row("R64",0xE123456789ABCDE0L,0x00000000143DA738L),
                rowAfter("P738",0x0000000089ABCDEFL,()->{ram.effect32(0x000000001542F328L, (int)0x0000000000000007L);},0x000000000424FC83L,0xE123456789ABCDE0L,0x00000000AABBCCDDL),
                row("E32",0x0000000000000007L,0x000000001542F328L),
                row("R32",0x0000000000000007L,0x000000001542F328L),
                rowAfter("PE900",0x8123456789ABCDEFL,()->{ram.effect64(0x00000000143DA420L,0xAABBCCDDEEFF0011L);},0x000000000424FC96L,0x0000000000000007L),
                row("E64",0xAABBCCDDEEFF0011L,0x00000000143DA420L),
                row("R64",0xAABBCCDDEEFF0011L,0x00000000143DA420L),
                row("P420",0x0000000000000000L,0x000000000424FD21L,0xAABBCCDDEEFF0011L,0x0000000089ABCDEFL)
            );
            long returned=Fc74Target424FC74.execute(ram,ports,new Fc74Api238.Input(base,0xAABBCCDD));
            check(returned==0x8123456789ABCDEFL,"valid_cached_high64_firstcall_index_and_E900_lastIAT_mutation raw64 result");
            check(ram.peek64(index)==0xBADC0FFE00000007L,"index low32/high32 exact");
            check(ram.peek64(first)==0xE123456789ABCDE0L,"first IAT bytes retained");
            check(ram.peek64(last)==0xAABBCCDDEEFF0011L,"last IAT bytes exact");
            check(ram.peek8(index-1)==0xA5&&ram.peek8(index+8)==0x5A,"index adjacent canaries");
            check(ram.peek8(first-1)==0xA6&&ram.peek8(first+8)==0x6A,"first IAT adjacent canaries");
            check(ram.peek8(last-1)==0xC3&&ram.peek8(last+8)==0x3C,"last IAT adjacent canaries");
            ram.finish("valid_cached_high64_firstcall_index_and_E900_lastIAT_mutation");
        }
        {
            Ram ram=new Ram();
            ScriptPorts ports=new ScriptPorts(ram);
            long base=0x0000000010000000L;
            long index=base+0x542F328L,first=base+0x43DA738L,last=base+0x43DA420L;
            ram.seed64(index,0xBADC0FFE0000000BL);
            ram.seed64(first,0xE123456789ABCDE0L);
            ram.seed64(last,0xE222222233333330L);
            ram.seed8(index-1,0xA5);ram.seed8(index+8,0x5A);
            ram.seed8(first-1,0xA6);ram.seed8(first+8,0x6A);
            ram.seed8(last-1,0xC3);ram.seed8(last+8,0x3C);
            ram.expect(
                row("R64",0xE123456789ABCDE0L,0x00000000143DA738L),
                row("P738",0x0000000089ABCDEFL,0x000000000424FC83L,0xE123456789ABCDE0L,0x00000000AABBCCDDL),
                row("R32",0x000000000000000BL,0x000000001542F328L),
                row("PE900",0xFFFFFFFFFFFFFFFFL,0x000000000424FC96L,0x000000000000000BL),
                row("R64",0xE222222233333330L,0x00000000143DA420L),
                row("P420",0x0000000000000000L,0x000000000424FD21L,0xE222222233333330L,0x0000000089ABCDEFL)
            );
            long returned=Fc74Target424FC74.execute(ram,ports,new Fc74Api238.Input(base,0xAABBCCDD));
            check(returned==0x0000000000000000L,"cached_minus1_clears_both_pointer_roles raw64 result");
            check(ram.peek64(index)==0xBADC0FFE0000000BL,"index low32/high32 exact");
            check(ram.peek64(first)==0xE123456789ABCDE0L,"first IAT bytes retained");
            check(ram.peek64(last)==0xE222222233333330L,"last IAT bytes exact");
            check(ram.peek8(index-1)==0xA5&&ram.peek8(index+8)==0x5A,"index adjacent canaries");
            check(ram.peek8(first-1)==0xA6&&ram.peek8(first+8)==0x6A,"first IAT adjacent canaries");
            check(ram.peek8(last-1)==0xC3&&ram.peek8(last+8)==0x3C,"last IAT adjacent canaries");
            ram.finish("cached_minus1_clears_both_pointer_roles");
        }
        {
            Ram ram=new Ram();
            ScriptPorts ports=new ScriptPorts(ram);
            long base=0x0000000010000000L;
            long index=base+0x542F328L,first=base+0x43DA738L,last=base+0x43DA420L;
            ram.seed64(index,0xBADC0FFE00000003L);
            ram.seed64(first,0xE123456789ABCDE0L);
            ram.seed64(last,0xE222222233333330L);
            ram.seed8(index-1,0xA5);ram.seed8(index+8,0x5A);
            ram.seed8(first-1,0xA6);ram.seed8(first+8,0x6A);
            ram.seed8(last-1,0xC3);ram.seed8(last+8,0x3C);
            ram.expect(
                row("R64",0xE123456789ABCDE0L,0x00000000143DA738L),
                row("P738",0x0000000089ABCDEFL,0x000000000424FC83L,0xE123456789ABCDE0L,0x00000000AABBCCDDL),
                row("R32",0x0000000000000003L,0x000000001542F328L),
                rowAfter("PE900",0x0000000000000000L,()->{ram.effect32(0x000000001542F328L, (int)0x000000000000000DL);},0x000000000424FC96L,0x0000000000000003L),
                row("E32",0x000000000000000DL,0x000000001542F328L),
                row("R32",0x000000000000000DL,0x000000001542F328L),
                row("PE948",0x0000000000000000L,0x000000000424FCB9L,0x000000000000000DL,0xFFFFFFFFFFFFFFFFL),
                row("R64",0xE222222233333330L,0x00000000143DA420L),
                row("P420",0x0000000000000000L,0x000000000424FD21L,0xE222222233333330L,0x0000000089ABCDEFL)
            );
            long returned=Fc74Target424FC74.execute(ram,ports,new Fc74Api238.Input(base,0xAABBCCDD));
            check(returned==0x0000000000000000L,"cached_zero_second_fresh_index_gate_false raw64 result");
            check(ram.peek64(index)==0xBADC0FFE0000000DL,"index low32/high32 exact");
            check(ram.peek64(first)==0xE123456789ABCDE0L,"first IAT bytes retained");
            check(ram.peek64(last)==0xE222222233333330L,"last IAT bytes exact");
            check(ram.peek8(index-1)==0xA5&&ram.peek8(index+8)==0x5A,"index adjacent canaries");
            check(ram.peek8(first-1)==0xA6&&ram.peek8(first+8)==0x6A,"first IAT adjacent canaries");
            check(ram.peek8(last-1)==0xC3&&ram.peek8(last+8)==0x3C,"last IAT adjacent canaries");
            ram.finish("cached_zero_second_fresh_index_gate_false");
        }
        {
            Ram ram=new Ram();
            ScriptPorts ports=new ScriptPorts(ram);
            long base=0x0000000010000000L;
            long index=base+0x542F328L,first=base+0x43DA738L,last=base+0x43DA420L;
            ram.seed64(index,0xBADC0FFEFFFFFFFFL);
            ram.seed64(first,0xE123456789ABCDE0L);
            ram.seed64(last,0xE222222233333330L);
            ram.seed8(index-1,0xA5);ram.seed8(index+8,0x5A);
            ram.seed8(first-1,0xA6);ram.seed8(first+8,0x6A);
            ram.seed8(last-1,0xC3);ram.seed8(last+8,0x3C);
            ram.expect(
                row("R64",0xE123456789ABCDE0L,0x00000000143DA738L),
                row("P738",0x0000000089ABCDEFL,0x000000000424FC83L,0xE123456789ABCDE0L,0x00000000AABBCCDDL),
                row("R32",0x00000000FFFFFFFFL,0x000000001542F328L),
                row("PE948",0x0000000000000000L,0x000000000424FCB9L,0x00000000FFFFFFFFL,0xFFFFFFFFFFFFFFFFL),
                row("R64",0xE222222233333330L,0x00000000143DA420L),
                row("P420",0x0000000000000000L,0x000000000424FD21L,0xE222222233333330L,0x0000000089ABCDEFL)
            );
            long returned=Fc74Target424FC74.execute(ram,ports,new Fc74Api238.Input(base,0xAABBCCDD));
            check(returned==0x0000000000000000L,"initial_index_minus1_skips_E900_gate_false raw64 result");
            check(ram.peek64(index)==0xBADC0FFEFFFFFFFFL,"index low32/high32 exact");
            check(ram.peek64(first)==0xE123456789ABCDE0L,"first IAT bytes retained");
            check(ram.peek64(last)==0xE222222233333330L,"last IAT bytes exact");
            check(ram.peek8(index-1)==0xA5&&ram.peek8(index+8)==0x5A,"index adjacent canaries");
            check(ram.peek8(first-1)==0xA6&&ram.peek8(first+8)==0x6A,"first IAT adjacent canaries");
            check(ram.peek8(last-1)==0xC3&&ram.peek8(last+8)==0x3C,"last IAT adjacent canaries");
            ram.finish("initial_index_minus1_skips_E900_gate_false");
        }
    }
    private static void allocationPaths238() {
        {
            Ram ram=new Ram();
            ScriptPorts ports=new ScriptPorts(ram);
            long base=0x0000000010000000L;
            long index=base+0x542F328L,first=base+0x43DA738L,last=base+0x43DA420L;
            ram.seed64(index,0xBADC0FFEFFFFFFFFL);
            ram.seed64(first,0xE123456789ABCDE0L);
            ram.seed64(last,0xE222222233333330L);
            ram.seed8(index-1,0xA5);ram.seed8(index+8,0x5A);
            ram.seed8(first-1,0xA6);ram.seed8(first+8,0x6A);
            ram.seed8(last-1,0xC3);ram.seed8(last+8,0x3C);
            ram.expect(
                row("R64",0xE123456789ABCDE0L,0x00000000143DA738L),
                row("P738",0x0000000089ABCDEFL,0x000000000424FC83L,0xE123456789ABCDE0L,0x00000000AABBCCDDL),
                row("R32",0x00000000FFFFFFFFL,0x000000001542F328L),
                row("PE948",0x0000000000000001L,0x000000000424FCB9L,0x00000000FFFFFFFFL,0xFFFFFFFFFFFFFFFFL),
                rowAfter("PE2EC",0x0000000000000000L,()->{ram.effect32(0x000000001542F328L, (int)0x0000000080000005L);},0x000000000424FCCCL,0x0000000000000001L,0x00000000000003C8L),
                row("E32",0x0000000080000005L,0x000000001542F328L),
                row("R32",0x0000000080000005L,0x000000001542F328L),
                row("PE948",0x0000000080000000L,0x000000000424FCE1L,0x0000000080000005L,0x0000000000000000L),
                rowAfter("PE364",0x0000000000000000L,()->{ram.effect64(0x00000000143DA420L,0xAABBCCDDEEFF0011L);},0x000000000424FCE8L,0x0000000000000000L),
                row("E64",0xAABBCCDDEEFF0011L,0x00000000143DA420L),
                row("R64",0xAABBCCDDEEFF0011L,0x00000000143DA420L),
                row("P420",0x0000000000000000L,0x000000000424FD21L,0xAABBCCDDEEFF0011L,0x0000000089ABCDEFL)
            );
            long returned=Fc74Target424FC74.execute(ram,ports,new Fc74Api238.Input(base,0xAABBCCDD));
            check(returned==0x0000000000000000L,"allocation_zero_still_fresh_index_before_test_ignored_E948_then_free0 raw64 result");
            check(ram.peek64(index)==0xBADC0FFE80000005L,"index low32/high32 exact");
            check(ram.peek64(first)==0xE123456789ABCDE0L,"first IAT bytes retained");
            check(ram.peek64(last)==0xAABBCCDDEEFF0011L,"last IAT bytes exact");
            check(ram.peek8(index-1)==0xA5&&ram.peek8(index+8)==0x5A,"index adjacent canaries");
            check(ram.peek8(first-1)==0xA6&&ram.peek8(first+8)==0x6A,"first IAT adjacent canaries");
            check(ram.peek8(last-1)==0xC3&&ram.peek8(last+8)==0x3C,"last IAT adjacent canaries");
            ram.finish("allocation_zero_still_fresh_index_before_test_ignored_E948_then_free0");
        }
        {
            Ram ram=new Ram();
            ScriptPorts ports=new ScriptPorts(ram);
            long base=0x0000000010000000L;
            long index=base+0x542F328L,first=base+0x43DA738L,last=base+0x43DA420L;
            ram.seed64(index,0xBADC0FFE00000002L);
            ram.seed64(first,0xE123456789ABCDE0L);
            ram.seed64(last,0xE222222233333330L);
            ram.seed8(index-1,0xA5);ram.seed8(index+8,0x5A);
            ram.seed8(first-1,0xA6);ram.seed8(first+8,0x6A);
            ram.seed8(last-1,0xC3);ram.seed8(last+8,0x3C);
            ram.expect(
                row("R64",0xE123456789ABCDE0L,0x00000000143DA738L),
                row("P738",0x0000000089ABCDEFL,0x000000000424FC83L,0xE123456789ABCDE0L,0x00000000AABBCCDDL),
                row("R32",0x0000000000000002L,0x000000001542F328L),
                row("PE900",0x0000000000000000L,0x000000000424FC96L,0x0000000000000002L),
                row("R32",0x0000000000000002L,0x000000001542F328L),
                row("PE948",0x0000000000000001L,0x000000000424FCB9L,0x0000000000000002L,0xFFFFFFFFFFFFFFFFL),
                rowAfter("PE2EC",0xFEDCBA9876543210L,()->{ram.effect32(0x000000001542F328L, (int)0x0000000000000009L);},0x000000000424FCCCL,0x0000000000000001L,0x00000000000003C8L),
                row("E32",0x0000000000000009L,0x000000001542F328L),
                row("R32",0x0000000000000009L,0x000000001542F328L),
                rowAfter("PE948",0x0000000000000000L,()->{ram.effect32(0x000000001542F328L, (int)0x0000000080000005L);},0x000000000424FCF2L,0x0000000000000009L,0xFEDCBA9876543210L),
                row("E32",0x0000000080000005L,0x000000001542F328L),
                row("R32",0x0000000080000005L,0x000000001542F328L),
                row("PE948",0x0000000000000001L,0x000000000424FD03L,0x0000000080000005L,0x0000000000000000L),
                row("PE364",0x0000000000000000L,0x000000000424FCE8L,0xFEDCBA9876543210L),
                row("R64",0xE222222233333330L,0x00000000143DA420L),
                row("P420",0x0000000000000000L,0x000000000424FD21L,0xE222222233333330L,0x0000000089ABCDEFL)
            );
            long returned=Fc74Target424FC74.execute(ram,ports,new Fc74Api238.Input(base,0xAABBCCDD));
            check(returned==0x0000000000000000L,"allocation_nonnull_association_false_fresh_index_then_free_allocated raw64 result");
            check(ram.peek64(index)==0xBADC0FFE80000005L,"index low32/high32 exact");
            check(ram.peek64(first)==0xE123456789ABCDE0L,"first IAT bytes retained");
            check(ram.peek64(last)==0xE222222233333330L,"last IAT bytes exact");
            check(ram.peek8(index-1)==0xA5&&ram.peek8(index+8)==0x5A,"index adjacent canaries");
            check(ram.peek8(first-1)==0xA6&&ram.peek8(first+8)==0x6A,"first IAT adjacent canaries");
            check(ram.peek8(last-1)==0xC3&&ram.peek8(last+8)==0x3C,"last IAT adjacent canaries");
            ram.finish("allocation_nonnull_association_false_fresh_index_then_free_allocated");
        }
        {
            Ram ram=new Ram();
            ScriptPorts ports=new ScriptPorts(ram);
            long base=0x0000000010000000L;
            long index=base+0x542F328L,first=base+0x43DA738L,last=base+0x43DA420L;
            ram.seed64(index,0xBADC0FFEFFFFFFFFL);
            ram.seed64(first,0xE123456789ABCDE0L);
            ram.seed64(last,0xE222222233333330L);
            ram.seed8(index-1,0xA5);ram.seed8(index+8,0x5A);
            ram.seed8(first-1,0xA6);ram.seed8(first+8,0x6A);
            ram.seed8(last-1,0xC3);ram.seed8(last+8,0x3C);
            ram.expect(
                row("R64",0xE123456789ABCDE0L,0x00000000143DA738L),
                row("P738",0x0000000089ABCDEFL,0x000000000424FC83L,0xE123456789ABCDE0L,0x00000000AABBCCDDL),
                row("R32",0x00000000FFFFFFFFL,0x000000001542F328L),
                row("PE948",0x0000000080000000L,0x000000000424FCB9L,0x00000000FFFFFFFFL,0xFFFFFFFFFFFFFFFFL),
                rowAfter("PE2EC",0x8123456789ABCDEFL,()->{ram.effect32(0x000000001542F328L, (int)0x000000000000004DL);},0x000000000424FCCCL,0x0000000000000001L,0x00000000000003C8L),
                row("E32",0x000000000000004DL,0x000000001542F328L),
                row("R32",0x000000000000004DL,0x000000001542F328L),
                rowAfter("PE948",0x0000000000000001L,()->{ram.effect64(0x00000000143DA420L,0xAABBCCDDEEFF0011L);},0x000000000424FCF2L,0x000000000000004DL,0x8123456789ABCDEFL),
                row("E64",0xAABBCCDDEEFF0011L,0x00000000143DA420L),
                rowAfter("PF8A8",0x0000000000000000L,()->{ram.effect32(0x000000001542F328L, (int)0x0000000000000063L);},0x000000000424FD10L,0x8123456789ABCDEFL),
                row("E32",0x0000000000000063L,0x000000001542F328L),
                row("PE364",0x0000000000000000L,0x000000000424FD17L,0x0000000000000000L),
                row("R64",0xAABBCCDDEEFF0011L,0x00000000143DA420L),
                row("P420",0x0000000000000000L,0x000000000424FD21L,0xAABBCCDDEEFF0011L,0x0000000089ABCDEFL)
            );
            long returned=Fc74Target424FC74.execute(ram,ports,new Fc74Api238.Input(base,0xAABBCCDD));
            check(returned==0x8123456789ABCDEFL,"allocation_nonnull_association_true_initialize_then_free0_keep_pointer raw64 result");
            check(ram.peek64(index)==0xBADC0FFE00000063L,"index low32/high32 exact");
            check(ram.peek64(first)==0xE123456789ABCDE0L,"first IAT bytes retained");
            check(ram.peek64(last)==0xAABBCCDDEEFF0011L,"last IAT bytes exact");
            check(ram.peek8(index-1)==0xA5&&ram.peek8(index+8)==0x5A,"index adjacent canaries");
            check(ram.peek8(first-1)==0xA6&&ram.peek8(first+8)==0x6A,"first IAT adjacent canaries");
            check(ram.peek8(last-1)==0xC3&&ram.peek8(last+8)==0x3C,"last IAT adjacent canaries");
            ram.finish("allocation_nonnull_association_true_initialize_then_free0_keep_pointer");
        }
        {
            Ram ram=new Ram();
            ScriptPorts ports=new ScriptPorts(ram);
            long base=0x0000000010000000L;
            long index=base+0x542F328L,first=base+0x43DA738L,last=base+0x43DA420L;
            ram.seed64(index,0xBADC0FFE00000001L);
            ram.seed64(first,0xE123456789ABCDE0L);
            ram.seed64(last,0xE222222233333330L);
            ram.seed8(index-1,0xA5);ram.seed8(index+8,0x5A);
            ram.seed8(first-1,0xA6);ram.seed8(first+8,0x6A);
            ram.seed8(last-1,0xC3);ram.seed8(last+8,0x3C);
            RuntimeException failure=new IllegalStateException("association238");
            ram.expect(
                row("R64",0xE123456789ABCDE0L,0x00000000143DA738L),
                row("P738",0x0000000089ABCDEFL,0x000000000424FC83L,0xE123456789ABCDE0L,0x00000000AABBCCDDL),
                row("R32",0x0000000000000001L,0x000000001542F328L),
                row("PE900",0x0000000000000000L,0x000000000424FC96L,0x0000000000000001L),
                row("R32",0x0000000000000001L,0x000000001542F328L),
                row("PE948",0x0000000000000001L,0x000000000424FCB9L,0x0000000000000001L,0xFFFFFFFFFFFFFFFFL),
                row("PE2EC",0xFEDCBA9876543210L,0x000000000424FCCCL,0x0000000000000001L,0x00000000000003C8L),
                row("R32",0x0000000000000001L,0x000000001542F328L),
                rowAfter("PE948",0x0000000000000001L,()->{throw failure;},0x000000000424FCF2L,0x0000000000000001L,0xFEDCBA9876543210L)
            );
            sameException(()->Fc74Target424FC74.execute(ram,ports,new Fc74Api238.Input(base,0xAABBCCDD)),failure,"throw_association_prefix_no_free_initialize_or_finalIAT");
            check(ram.peek64(index)==0xBADC0FFE00000001L,"index low32/high32 exact");
            check(ram.peek64(first)==0xE123456789ABCDE0L,"first IAT bytes retained");
            check(ram.peek64(last)==0xE222222233333330L,"last IAT bytes exact");
            check(ram.peek8(index-1)==0xA5&&ram.peek8(index+8)==0x5A,"index adjacent canaries");
            check(ram.peek8(first-1)==0xA6&&ram.peek8(first+8)==0x6A,"first IAT adjacent canaries");
            check(ram.peek8(last-1)==0xC3&&ram.peek8(last+8)==0x3C,"last IAT adjacent canaries");
            ram.finish("throw_association_prefix_no_free_initialize_or_finalIAT");
        }
    }

    public static void main(String[] args) {
        pointerPaths238();allocationPaths238();
        System.out.println("FC74_238_PASS scenes="+scenes+" orderedEvents="+orderedEvents+" mixedChecks="+checks+" Native=0 Game=0");
    }
}
