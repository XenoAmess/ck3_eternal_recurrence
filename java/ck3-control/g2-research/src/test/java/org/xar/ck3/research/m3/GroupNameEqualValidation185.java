package org.xar.ck3.research.m3;

import java.util.List;
import org.xar.ck3.research.m3.GroupNameEqualApi185.Memory;
import org.xar.ck3.research.m3.GroupNameEqualApi185.Scratch;
import org.xar.ck3.research.m3.GroupNameEqualApi185.Vector128;
import org.xar.ck3.research.m3.GroupNameEqualBook185.Kind;
import org.xar.ck3.research.m3.GroupNameEqualBook185.Step;
import org.xar.ck3.research.m3.GroupNameEqualBook185.Scenario;

public final class GroupNameEqualValidation185 {
    private GroupNameEqualValidation185() { }

    public static void main(String[] args) {
        List<Scenario> cases = GroupNameEqualBook185.cases();
        int totalScenarios = cases.size();
        int passedCases = 0;
        int topLevelAssertions = 0;

        for (Scenario scenario : cases) {
            List<Step> expectedSteps = scenario.expectedSteps();
            Script script = new Script(expectedSteps);
            Scratch scratch = new Scratch(scenario.sourceEntryRsp());

            int actualAl = GroupNameEqual185.equalAl(
                script,
                scenario.moduleBase(),
                scenario.left(),
                scenario.right(),
                scratch
            );

            if (script.cursor != expectedSteps.size()) {
                throw new AssertionError("Step consumption mismatch for " + scenario.id());
            }
            if (actualAl != scenario.expectedAl()) {
                throw new AssertionError("AL mismatch for " + scenario.id());
            }
            if (actualAl != 0 && actualAl != 1) {
                throw new AssertionError("Invalid AL domain for " + scenario.id());
            }

            topLevelAssertions += 3;
            passedCases++;
            System.out.println("Case " + scenario.id() + " passed with " + script.cursor + " steps consumed.");
        }

        System.out.println("Total scenarios: " + totalScenarios);
        System.out.println("Passed cases: " + passedCases);
        System.out.println("Top-level assertions: " + topLevelAssertions);
    }

    private static final class Script implements Memory {
        private final List<Step> steps;
        private int cursor;

        Script(List<Step> steps) {
            this.steps = List.copyOf(steps);
            this.cursor = 0;
        }

        private Step take(Kind kind, long address) {
            if (cursor >= steps.size()) {
                throw new AssertionError("Missing step: expected " + kind + " at " + Long.toHexString(address));
            }
            Step step = steps.get(cursor);
            if (step.kind() != kind) {
                throw new AssertionError("Kind mismatch: expected " + kind + " got " + step.kind());
            }
            if (step.address() != address) {
                throw new AssertionError("Address mismatch: expected " + Long.toHexString(address) + " got " + Long.toHexString(step.address()));
            }
            cursor++;
            return step;
        }

        @Override
        public int readUnsigned16(long address) {
            Step step = take(Kind.READ_WORD, address);
            long low = step.low();
            long high = step.high();
            if (low < 0 || low > 0xFFFF || high != 0) {
                throw new AssertionError("Invalid READ_WORD payload");
            }
            return (int) low;
        }

        @Override
        public void write16(long address, int value) {
            Step step = take(Kind.WRITE_WORD, address);
            long low = step.low();
            long high = step.high();
            if (low < 0 || low > 0xFFFF || high != 0) {
                throw new AssertionError("Invalid WRITE_WORD payload");
            }
            if ((value & 0xFFFF) != low) {
                throw new AssertionError("WRITE_WORD value mismatch");
            }
        }

        @Override
        public Vector128 read128(long address) {
            Step step = take(Kind.READ_VECTOR128, address);
            return new Vector128(step.low(), step.high());
        }

        @Override
        public int readUnsigned8(long address) {
            Step step = take(Kind.READ_BYTE, address);
            long low = step.low();
            long high = step.high();
            if (low < 0 || low > 0xFF || high != 0) {
                throw new AssertionError("Invalid READ_BYTE payload");
            }
            return (int) low;
        }

        @Override
        public long readPointer(long address) {
            throw new AssertionError("Unsupported operation: readPointer");
        }

        @Override
        public int readInt32(long address) {
            throw new AssertionError("Unsupported operation: readInt32");
        }

        @Override
        public void write8(long address, int value) {
            throw new AssertionError("Unsupported operation: write8");
        }

        @Override
        public void writeInt32(long address, int value) {
            throw new AssertionError("Unsupported operation: writeInt32");
        }

        @Override
        public void writeInt64(long address, long value) {
            throw new AssertionError("Unsupported operation: writeInt64");
        }
    }
}