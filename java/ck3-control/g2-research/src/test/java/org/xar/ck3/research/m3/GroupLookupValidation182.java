package org.xar.ck3.research.m3;

import java.util.List;
import org.xar.ck3.research.m3.GroupLookupApi182.Memory;
import org.xar.ck3.research.m3.GroupLookupApi182.Ports;
import org.xar.ck3.research.m3.GroupLookupBook182.Kind;
import org.xar.ck3.research.m3.GroupLookupBook182.Step;
import org.xar.ck3.research.m3.GroupLookupBook182.Scenario;

public final class GroupLookupValidation182 {
    private GroupLookupValidation182() { }

    public static void main(String[] args) {
        List<Scenario> scenarios = GroupLookupBook182.cases();
        int totalScenes = scenarios.size();
        int assertionCount = 0;

        for (Scenario scenario : scenarios) {
            Script script = new Script(scenario.expectedSteps());
            long actualReturned = GroupLookup182.find(script, script, scenario.moduleBase(), scenario.receiver(), scenario.hash32());

            if (script.cursor != scenario.expectedSteps().size()) {
                throw new AssertionError("Steps not fully consumed for scenario " + scenario.id());
            }
            if (actualReturned != scenario.expectedReturned()) {
                throw new AssertionError("Return mismatch for scenario " + scenario.id());
            }

            assertionCount += 2;
            System.out.println("Scenario " + scenario.id() + ": consumed " + script.cursor + " steps");
        }

        System.out.println("Total scenes: " + totalScenes);
        System.out.println("Total assertions: " + assertionCount);
    }

    private static final class Script implements Memory, Ports {
        private final List<Step> steps;
        private int cursor = 0;

        Script(List<Step> steps) {
            this.steps = List.copyOf(steps);
        }

        private Step take(Kind kind, long address, int delta) {
            if (cursor >= steps.size()) {
                throw new AssertionError("Unexpected operation: " + kind + " at address " + address);
            }
            Step step = steps.get(cursor++);
            if (step.kind() != kind) {
                throw new AssertionError("Kind mismatch: expected " + step.kind() + " got " + kind);
            }
            if (step.address() != address) {
                throw new AssertionError("Address mismatch: expected " + step.address() + " got " + address);
            }
            if (step.delta() != delta) {
                throw new AssertionError("Delta mismatch: expected " + step.delta() + " got " + delta);
            }
            return step;
        }

        @Override
        public int readUnsigned8(long address) {
            Step step = take(Kind.READ_BYTE, address, 0);
            long val = step.returned();
            if (val < 0 || val > 255) {
                throw new AssertionError("Byte out of range: " + val);
            }
            return (int) val;
        }

        @Override
        public void write8(long address, int value) {
            throw new AssertionError("Unexpected write8");
        }

        @Override
        public int readInt32(long address) {
            Step step = take(Kind.READ_DWORD, address, 0);
            long val = step.returned();
            if (val < 0 || val > 4294967295L) {
                throw new AssertionError("DWORD out of range: " + val);
            }
            return (int) val;
        }

        @Override
        public void writeInt32(long address, int value) {
            throw new AssertionError("Unexpected writeInt32");
        }

        @Override
        public void writeInt64(long address, long value) {
            throw new AssertionError("Unexpected writeInt64");
        }

        @Override
        public long readPointer(long address) {
            Step step = take(Kind.READ_POINTER, address, 0);
            return step.returned();
        }

        @Override
        public int atomicXadd32(Memory memory, long address, int delta) {
            if (memory != this) {
                throw new AssertionError("Memory identity mismatch");
            }
            Step step = take(Kind.XADD32, address, delta);
            return (int) step.returned();
        }

        @Override
        public void pause(Memory memory) {
            if (memory != this) {
                throw new AssertionError("Memory identity mismatch");
            }
            Step step = take(Kind.PAUSE, 0L, 0);
            if (step.returned() != 0L) {
                throw new AssertionError("PAUSE returned non-zero: " + step.returned());
            }
        }
    }
}