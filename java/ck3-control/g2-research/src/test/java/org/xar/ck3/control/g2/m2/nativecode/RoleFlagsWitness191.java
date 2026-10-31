package org.xar.ck3.control.g2.m2.nativecode;

import java.util.List;

public final class RoleFlagsWitness191 {
    public static void main(String[] args) {
        int passCount = verify();
        System.out.println(passCount);
    }

    public static int verify() {
        int passCount = 0;
        List<RoleFlagsScenario191.Scene> scenes = RoleFlagsCases191.scenes();
        for (int i = 0; i < scenes.size(); i++) {
            RoleFlagsScenario191.Scene scene = scenes.get(i);
            try {
                runScene(scene);
                passCount++;
            } catch (AssertionError e) {
                throw new AssertionError("Scene " + scene.name() + " index " + i + " failed: " + e.getMessage());
            }
        }
        return passCount;
    }

    private static void runScene(RoleFlagsScenario191.Scene scene) {
        List<RoleFlagsScenario191.Step> steps = scene.steps();
        int[] cursor = new int[]{0};

        PendingComponentRoleFlags275669C.Memory memory = new PendingComponentRoleFlags275669C.Memory() {
            @Override
            public int read8(long address) {
                checkNext(steps, cursor, RoleFlagsScenario191.Op.R8, address, 0);
                return (int) steps.get(cursor[0] - 1).value();
            }

            @Override
            public int read32(long address) {
                checkNext(steps, cursor, RoleFlagsScenario191.Op.R32, address, 0);
                return (int) steps.get(cursor[0] - 1).value();
            }

            @Override
            public long read64(long address) {
                checkNext(steps, cursor, RoleFlagsScenario191.Op.R64, address, 0);
                return steps.get(cursor[0] - 1).value();
            }

            @Override
            public void write8(long address, int value) {
                checkNext(steps, cursor, RoleFlagsScenario191.Op.W8, address, value & 0xFF);
            }
        };

        PendingComponentRoleFlags275669C.Calls calls = new PendingComponentRoleFlags275669C.Calls() {
            @Override
            public boolean call2BAA6F0(PendingComponentRoleFlags275669C.Memory mem, int ecx) {
                checkNext(steps, cursor, RoleFlagsScenario191.Op.CALL, Integer.toUnsignedLong(ecx), 0);
                return steps.get(cursor[0] - 1).value() != 0;
            }
        };

        PendingComponentRoles27563E1.Resolved roles = new PendingComponentRoles27563E1.Resolved(
                scene.r14(), scene.r15(), scene.rdi()
        );

        PendingComponentRoleFlags275669C.apply(memory, calls, scene.component(), scene.context(), roles);

        if (cursor[0] != steps.size()) {
            throw new AssertionError("Unconsumed script steps: " + (steps.size() - cursor[0]));
        }
    }

    private static void checkNext(List<RoleFlagsScenario191.Step> steps, int[] cursor,
            RoleFlagsScenario191.Op expectedOp, long expectedAddress, int expectedValue) {
        if (cursor[0] >= steps.size()) {
            throw new AssertionError("Read past end of script");
        }
        RoleFlagsScenario191.Step step = steps.get(cursor[0]);
        if (step.op() != expectedOp) {
            throw new AssertionError("Op mismatch at index " + cursor[0] + ": expected " + expectedOp + " got " + step.op());
        }
        if (step.address() != expectedAddress) {
            throw new AssertionError("Address mismatch at index " + cursor[0] + ": expected " + expectedAddress + " got " + step.address());
        }
        if (expectedOp == RoleFlagsScenario191.Op.W8) {
            if ((step.value() & 0xFF) != (expectedValue & 0xFF)) {
                throw new AssertionError("Value mismatch at index " + cursor[0] + ": expected " + (expectedValue & 0xFF) + " got " + (step.value() & 0xFF));
            }
        }
        cursor[0]++;
    }
}