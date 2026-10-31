package org.xar.ck3.research.m3;

import java.util.List;
import java.util.ArrayList;

public final class StringHashValidation187 {
    private StringHashValidation187() { }

    public static void main(String[] args) {
        List<StringHashBook187.Scenario> scenarios = StringHashBook187.cases();
        int totalCases = 0;
        int passedCases = 0;
        int totalSteps = 0;
        int consumedSteps = 0;

        for (StringHashBook187.Scenario scenario : scenarios) {
            totalCases++;
            List<StringHashBook187.Step> steps = List.copyOf(scenario.expectedSteps());
            Script script = new Script(steps);

            int result = StringHash187.hash(
                script,
                scenario.data(),
                scenario.lengthBits(),
                new StringHashApi187.Scratch(scenario.sourceEntryRsp())
            );

            if (result != scenario.expectedEax()) {
                throw new AssertionError("EAX mismatch for scenario " + scenario.id() + ": expected " + Integer.toHexString(scenario.expectedEax()) + " got " + Integer.toHexString(result));
            }

            if (script.cursor != steps.size()) {
                throw new AssertionError("Steps not fully consumed for scenario " + scenario.id() + ": expected " + steps.size() + " consumed " + script.cursor);
            }

            passedCases++;
            totalSteps += steps.size();
            consumedSteps += script.cursor;

            System.out.println("Scenario " + scenario.id() + ": Consumed " + script.cursor + " steps, EAX bits: " + Integer.toHexString(result));
        }

        System.out.println("Total cases: " + totalCases + ", Passed: " + passedCases + ", Total steps: " + totalSteps + ", Consumed steps: " + consumedSteps);
    }

    private static final class Script implements StringHashApi187.Memory {
        private final List<StringHashBook187.Step> steps;
        private int cursor;

        Script(List<StringHashBook187.Step> steps) {
            this.steps = steps;
            this.cursor = 0;
        }

        @Override
        public int readUnsigned8(long address) {
            if (cursor >= steps.size()) {
                throw new AssertionError("Underflow: no more steps");
            }
            StringHashBook187.Step step = steps.get(cursor);
            if (step.kind() != StringHashBook187.Kind.READ_BYTE) {
                throw new AssertionError("Expected READ_BYTE, got " + step.kind());
            }
            if (step.address() != address) {
                throw new AssertionError("Address mismatch: expected " + step.address() + ", got " + address);
            }
            long bits = step.bits();
            if (bits < 0 || bits > 255) {
                throw new AssertionError("Invalid byte bits: " + bits);
            }
            cursor++;
            return (int) bits;
        }

        @Override
        public int readInt32(long address) {
            if (cursor >= steps.size()) {
                throw new AssertionError("Underflow: no more steps");
            }
            StringHashBook187.Step step = steps.get(cursor);
            if (step.kind() != StringHashBook187.Kind.READ_DWORD) {
                throw new AssertionError("Expected READ_DWORD, got " + step.kind());
            }
            if (step.address() != address) {
                throw new AssertionError("Address mismatch: expected " + step.address() + ", got " + address);
            }
            long bits = step.bits();
            if (bits < 0 || bits > 0xFFFFFFFFL) {
                throw new AssertionError("Invalid DWORD bits: " + bits);
            }
            cursor++;
            return (int) bits;
        }

        @Override
        public void writeInt32(long address, int value) {
            if (cursor >= steps.size()) {
                throw new AssertionError("Underflow: no more steps");
            }
            StringHashBook187.Step step = steps.get(cursor);
            if (step.kind() != StringHashBook187.Kind.WRITE_DWORD) {
                throw new AssertionError("Expected WRITE_DWORD, got " + step.kind());
            }
            if (step.address() != address) {
                throw new AssertionError("Address mismatch: expected " + step.address() + ", got " + address);
            }
            long bits = step.bits();
            if (bits < 0 || bits > 0xFFFFFFFFL) {
                throw new AssertionError("Invalid DWORD bits: " + bits);
            }
            if (bits != Integer.toUnsignedLong(value)) {
                throw new AssertionError("Value mismatch: expected bits " + bits + ", got value " + value);
            }
            cursor++;
        }

        @Override
        public void write8(long address, int value) {
            throw new AssertionError("Unprojected method: write8");
        }

        @Override
        public long readPointer(long address) {
            throw new AssertionError("Unprojected method: readPointer");
        }

        @Override
        public void writeInt64(long address, long value) {
            throw new AssertionError("Unprojected method: writeInt64");
        }
    }
}