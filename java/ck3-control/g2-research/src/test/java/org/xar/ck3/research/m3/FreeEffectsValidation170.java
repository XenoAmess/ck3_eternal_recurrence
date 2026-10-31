package org.xar.ck3.research.m3;

import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import java.util.List;
import java.util.ArrayList;
import java.util.Map;
import java.util.HashMap;
import org.xar.ck3.control.g2.common.nativecore.task.captured.cleanup.Free83Inputs;

public final class FreeEffectsValidation170 {
    private static int checks;
    private FreeEffectsValidation170() { }
    public static void main(String[] args) {
        List<FreeEffectsCasesApi170.Scenario> cases=FreeEffectsCases170.cases();
        check(cases.size()==6,"case count");
        for (FreeEffectsCasesApi170.Scenario s:cases) validate(s);
        System.out.println("6 source effects cases; checks="+checks);
    }
    private static void validate(FreeEffectsCasesApi170.Scenario s) {
        List<String> events = new ArrayList<>();
        Memory memory = new Memory(s.initialWords(), events);
        Map<Long,Byte> before = memory.snapshot();
        Probe probe = new Probe(s, events);
        FreeEffectsApi170.Outcome outcome = SelectedFreeEffects170.release(
            memory, s.moduleBase(), s.receiver(), s.rows(), s.alignment(), s.targets(), probe);
        check(outcome.equals(s.expectedOutcome()), "outcome mismatch for " + s.id());
        check(events.equals(s.expectedEvents()), "event order mismatch for " + s.id());
        check(probe.cell.value == s.expectedFinalCell(), "cell value mismatch for " + s.id());
        check(memory.snapshot().equals(before), "memory changed for " + s.id());
        System.out.println(s.id() + " pass");
    }
    private static void check(boolean condition,String message) {
        checks++;
        if (!condition) throw new AssertionError(message);
    }
    private static String h(long value) { return Long.toUnsignedString(value,16); }
    private static final class Probe implements Free83Inputs.Calls {
        private final FreeEffectsCasesApi170.Scenario scenario;
        private final List<String> events;
        private final Free83Inputs.Cell32 cell;
        private int heapCount,cellCount,errorCount,mapCount;
        private Probe(FreeEffectsCasesApi170.Scenario scenario,List<String> events) {
            this.scenario=scenario;
            this.events=events;
            cell=new Free83Inputs.Cell32(scenario.initialCell());
        }
        public int heapFree(long handle,int flags,long block) {
            check(++heapCount==1,"heap callback bound");
            events.add("HEAP:"+h(handle)+":"+Integer.toUnsignedString(flags,16)+":"+h(block));
            return scenario.heapFreeReturn();
        }
        public Free83Inputs.Cell32 failureCell() {
            check(++cellCount==1,"cell callback bound");
            events.add("FAILURE_CELL");
            return cell;
        }
        public int lastErrorBits() {
            check(++errorCount==1,"error callback bound");
            events.add("LAST_ERROR");
            return scenario.lastErrorBits();
        }
        public int mapCode(long error) {
            check(++mapCount==1,"map callback bound");
            events.add("MAP:"+h(error));
            return scenario.mappedBits();
        }
    }
    private static final class Memory implements NativeTaskMemory {
        private final Map<Long,Byte> bytes=new HashMap<>();
        private final List<String> events;
        private Memory(List<FreeEffectsCasesApi170.Word> words,List<String> events) {
            this.events=events;
            for (FreeEffectsCasesApi170.Word word:words) {
                for (int i=0;i<8;i++) {
                    if (bytes.putIfAbsent(word.address()+i,(byte)(word.value() >>> (8*i)))!=null) {
                        throw new AssertionError("overlapping fixture word");
                    }
                }
            }
        }
        private long read(long address,int width) {
            long value=0L;
            for (int i=0;i<width;i++) {
                Byte one=bytes.get(address+i);
                if (one==null) throw new AssertionError("unmapped read "+h(address+i));
                value |= (one & 255L) << (8*i);
            }
            return value;
        }
        public long readPointer(long address) { events.add("R64:"+h(address)); return read(address,8); }
        public int readInt32(long address) { events.add("R32:"+h(address)); return (int)read(address,4); }
        public int readUnsigned8(long address) { events.add("R8:"+h(address)); return (int)read(address,1); }
        public void writeInt64(long address,long value) { throw new AssertionError("unexpected Memory write64"); }
        public void writeInt32(long address,int value) { throw new AssertionError("unexpected Memory write32"); }
        public void write8(long address,int value) { throw new AssertionError("unexpected Memory write8"); }
        private Map<Long,Byte> snapshot() { return Map.copyOf(bytes); }
    }
}
