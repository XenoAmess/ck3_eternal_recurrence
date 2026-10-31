package org.xar.ck3.research.m3;

import java.util.List;
import org.xar.ck3.research.m3.ByteCompareApi184.Memory;
import org.xar.ck3.research.m3.ByteCompareBook184.Kind;
import org.xar.ck3.research.m3.ByteCompareBook184.Step;
import org.xar.ck3.research.m3.ByteCompareBook184.Scenario;

public final class ByteCompareValidation184 {
    private ByteCompareValidation184() { }

    public static void main(String[] args) {
        List<Scenario> scenarios = ByteCompareBook184.cases();
        int totalScenarios = 0;
        int totalAssertions = 0;

        for (Scenario scenario : scenarios) {
            totalScenarios++;
            List<Step> expectedSteps = List.copyOf(scenario.expectedSteps());
            Script script = new Script(expectedSteps);

            int result = ByteCompare184.compare(script, scenario.left(), scenario.right(), scenario.lengthBits());

            if (script.cursor() != expectedSteps.size()) {
                throw new IllegalStateException("Missing reads: expected " + expectedSteps.size() + " got " + script.cursor());
            }
            if (result != scenario.expectedReturned()) {
                throw new IllegalStateException("Return mismatch: expected " + scenario.expectedReturned() + " got " + result);
            }

            totalAssertions += 2;
            System.out.println("Scenario " + scenario.id() + ": consumed " + script.cursor() + " steps, return " + result);
        }

        System.out.println("Total scenarios: " + totalScenarios + ", total assertions: " + totalAssertions);
    }

    private static final class Script implements Memory {
        private final List<Step> steps;
        private int cursor;

        Script(List<Step> steps) {
            this.steps = steps;
            this.cursor = 0;
        }

        int cursor() {
            return cursor;
        }

        @Override
        public int readUnsigned8(long address) {
            if (cursor >= steps.size()) {
                throw new IllegalStateException("Extra read: no expected step");
            }
            Step step = steps.get(cursor);
            if (step.kind() != Kind.READ_BYTE) {
                throw new IllegalStateException("Kind mismatch: expected READ_BYTE");
            }
            if (step.address() != address) {
                throw new IllegalStateException("Address mismatch: expected " + step.address() + " got " + address);
            }
            long bits = step.returned();
            if (bits < 0 || bits > 255) {
                throw new IllegalStateException("Invalid byte value: " + bits);
            }
            cursor++;
            return (int) bits;
        }

        @Override
        public long readPointer(long address) {
            if (cursor >= steps.size()) {
                throw new IllegalStateException("Extra read: no expected step");
            }
            Step step = steps.get(cursor);
            if (step.kind() != Kind.READ_QWORD) {
                throw new IllegalStateException("Kind mismatch: expected READ_QWORD");
            }
            if (step.address() != address) {
                throw new IllegalStateException("Address mismatch: expected " + step.address() + " got " + address);
            }
            long bits = step.returned();
            cursor++;
            return bits;
        }

        @Override
        public int readInt32(long address) {
            throw new UnsupportedOperationException("Unexpected readInt32");
        }

        @Override
        public void write8(long address, int value) {
            throw new UnsupportedOperationException("Unexpected write8");
        }

        @Override
        public void writeInt32(long address, int value) {
            throw new UnsupportedOperationException("Unexpected writeInt32");
        }

        @Override
        public void writeInt64(long address, long value) {
            throw new UnsupportedOperationException("Unexpected writeInt64");
        }
    }
}