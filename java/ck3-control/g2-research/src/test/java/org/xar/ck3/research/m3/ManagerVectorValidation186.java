package org.xar.ck3.research.m3;

import java.util.List;
import org.xar.ck3.research.m3.ManagerVectorApi186.Memory;
import org.xar.ck3.research.m3.ManagerVectorApi186.Ports;
import org.xar.ck3.research.m3.ManagerVectorBook186.Kind;
import org.xar.ck3.research.m3.ManagerVectorBook186.Step;
import org.xar.ck3.research.m3.ManagerVectorBook186.Scenario;

public final class ManagerVectorValidation186 {
    private ManagerVectorValidation186() { }

    public static void main(String[] args) {
        List<Scenario> scenarios = ManagerVectorBook186.cases();
        int totalScenarios = 0;
        int totalSteps = 0;
        for (Scenario scenario : scenarios) {
            totalScenarios++;
            Script script = new Script(scenario.expectedSteps());
            ManagerVector186.collect(script, script, scenario.moduleBase(), scenario.manager(), scenario.output());
            script.assertExhausted();
            totalSteps += scenario.expectedSteps().size();
            System.out.println("Scenario " + scenario.id() + " consumed " + scenario.expectedSteps().size() + " steps");
        }
        System.out.println("Total scenarios: " + totalScenarios);
        System.out.println("Total steps: " + totalSteps);
    }

    private static final class Script implements Memory, Ports {
        private final List<Step> steps;
        private int cursor = 0;

        Script(List<Step> steps) {
            this.steps = List.copyOf(steps);
        }

        private long take(Kind kind, long address, long a, long b, long c) {
            if (cursor >= steps.size()) {
                throw new IllegalStateException("Missing step: expected " + kind + " at address " + address);
            }
            Step step = steps.get(cursor);
            if (step.kind() != kind) {
                throw new IllegalStateException("Kind mismatch: expected " + kind + " got " + step.kind());
            }
            if (step.address() != address) {
                throw new IllegalStateException("Address mismatch: expected " + address + " got " + step.address());
            }
            if (step.a() != a) {
                throw new IllegalStateException("a mismatch: expected " + a + " got " + step.a());
            }
            if (step.b() != b) {
                throw new IllegalStateException("b mismatch: expected " + b + " got " + step.b());
            }
            if (step.c() != c) {
                throw new IllegalStateException("c mismatch: expected " + c + " got " + step.c());
            }
            cursor++;
            return step.result();
        }

        private void assertExhausted() {
            if (cursor != steps.size()) {
                throw new IllegalStateException("Extra steps: consumed " + cursor + " of " + steps.size());
            }
        }

        @Override
        public int readUnsigned8(long address) {
            long result = take(Kind.READ_BYTE, address, 0L, 0L, 0L);
            if (result < 0L || result > 255L) {
                throw new IllegalStateException("READ_BYTE result out of range: " + result);
            }
            return (int) result;
        }

        @Override
        public int readInt32(long address) {
            long result = take(Kind.READ_DWORD, address, 0L, 0L, 0L);
            if (result < 0L || result > 0xFFFFFFFFL) {
                throw new IllegalStateException("READ_DWORD result out of range: " + result);
            }
            return (int) result;
        }

        @Override
        public long readPointer(long address) {
            return take(Kind.READ_POINTER, address, 0L, 0L, 0L);
        }

        @Override
        public void write8(long address, int value) {
            long written = value & 0xffL;
            long result = take(Kind.WRITE_BYTE, address, written, 0L, 0L);
            if (result != 0L) {
                throw new IllegalStateException("WRITE_BYTE result not 0: " + result);
            }
        }

        @Override
        public void writeInt32(long address, int value) {
            long written = Integer.toUnsignedLong(value);
            long result = take(Kind.WRITE_DWORD, address, written, 0L, 0L);
            if (result != 0L) {
                throw new IllegalStateException("WRITE_DWORD result not 0: " + result);
            }
        }

        @Override
        public void writeInt64(long address, long value) {
            long result = take(Kind.WRITE_QWORD, address, value, 0L, 0L);
            if (result != 0L) {
                throw new IllegalStateException("WRITE_QWORD result not 0: " + result);
            }
        }

        @Override
        public void incrementInt32(long address) {
            long result = take(Kind.INCREMENT_DWORD, address, 0L, 0L, 0L);
            if (result != 0L) {
                throw new IllegalStateException("INCREMENT_DWORD result not 0: " + result);
            }
        }

        @Override
        public long objectSlot08(Memory memory, long code, long receiver) {
            if (memory != this) {
                throw new IllegalStateException("objectSlot08 memory identity mismatch");
            }
            return take(Kind.OBJECT08, code, receiver, 0L, 0L);
        }

        @Override
        public int growthCvtt32(Memory memory, int capacityBits, int multiplierBits) {
            if (memory != this) {
                throw new IllegalStateException("growthCvtt32 memory identity mismatch");
            }
            long cap = Integer.toUnsignedLong(capacityBits);
            long mult = Integer.toUnsignedLong(multiplierBits);
            long result = take(Kind.GROWTH_CVTT32, 0L, cap, mult, 0L);
            if (result < 0L || result > 0xFFFFFFFFL) {
                throw new IllegalStateException("GROWTH_CVTT32 result out of range: " + result);
            }
            return (int) result;
        }

        @Override
        public long allocatorSlot08(Memory memory, long code, long allocator, long bytes, int alignment) {
            if (memory != this) {
                throw new IllegalStateException("allocatorSlot08 memory identity mismatch");
            }
            long align = Integer.toUnsignedLong(alignment);
            return take(Kind.ALLOCATOR08, code, allocator, bytes, align);
        }

        @Override
        public void objectSlot00(Memory memory, long code, long receiver, int flag) {
            if (memory != this) {
                throw new IllegalStateException("objectSlot00 memory identity mismatch");
            }
            long unsignedFlag = Integer.toUnsignedLong(flag);
            long result = take(Kind.OBJECT00, code, receiver, unsignedFlag, 0L);
            if (result != 0L) {
                throw new IllegalStateException("OBJECT00 result not 0: " + result);
            }
        }

        @Override
        public void allocatorSlot10(Memory memory, long code, long allocator, long block, int alignment) {
            if (memory != this) {
                throw new IllegalStateException("allocatorSlot10 memory identity mismatch");
            }
            long align = Integer.toUnsignedLong(alignment);
            long result = take(Kind.ALLOCATOR10, code, allocator, block, align);
            if (result != 0L) {
                throw new IllegalStateException("ALLOCATOR10 result not 0: " + result);
            }
        }
    }
}