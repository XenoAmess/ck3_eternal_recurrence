package org.xar.ck3.control.g2.m2.nativecode;

import java.util.List;

public final class RoleResolutionWitness187 {
    public static void main(String[] args) {
        List<RoleResolutionScenario187.Scene> scenes = RoleResolutionCases187.scenes();
        int count = 0;
        for (RoleResolutionScenario187.Scene scene : scenes) {
            count++;
            List<RoleResolutionScenario187.Step> steps = scene.steps();
            final int[] cursor = {0};

            PendingComponentRoles27563E1.Memory memory = new PendingComponentRoles27563E1.Memory() {
                public int read32(long address) {
                    if (cursor[0] >= steps.size()) {
                        throw new AssertionError("Extra read32 at address " + Long.toHexString(address));
                    }
                    RoleResolutionScenario187.Step step = steps.get(cursor[0]);
                    if (step.op() != RoleResolutionScenario187.Op.R32) {
                        throw new AssertionError("Wrong op for read32 at address " + Long.toHexString(address) + ": expected R32, got " + step.op());
                    }
                    if (step.address() != address) {
                        throw new AssertionError("Wrong address for read32: expected " + Long.toHexString(step.address()) + ", got " + Long.toHexString(address));
                    }
                    cursor[0]++;
                    return (int) step.value();
                }

                public long read64(long address) {
                    if (cursor[0] >= steps.size()) {
                        throw new AssertionError("Extra read64 at address " + Long.toHexString(address));
                    }
                    RoleResolutionScenario187.Step step = steps.get(cursor[0]);
                    if (step.op() != RoleResolutionScenario187.Op.R64) {
                        throw new AssertionError("Wrong op for read64 at address " + Long.toHexString(address) + ": expected R64, got " + step.op());
                    }
                    if (step.address() != address) {
                        throw new AssertionError("Wrong address for read64: expected " + Long.toHexString(step.address()) + ", got " + Long.toHexString(address));
                    }
                    cursor[0]++;
                    return step.value();
                }

                public void write32(long address, int value) {
                    if (cursor[0] >= steps.size()) {
                        throw new AssertionError("Extra write32 at address " + Long.toHexString(address));
                    }
                    RoleResolutionScenario187.Step step = steps.get(cursor[0]);
                    if (step.op() != RoleResolutionScenario187.Op.W32) {
                        throw new AssertionError("Wrong op for write32 at address " + Long.toHexString(address) + ": expected W32, got " + step.op());
                    }
                    if (step.address() != address) {
                        throw new AssertionError("Wrong address for write32: expected " + Long.toHexString(step.address()) + ", got " + Long.toHexString(address));
                    }
                    long expected = step.value();
                    long actual = Integer.toUnsignedLong(value);
                    if (expected != actual) {
                        throw new AssertionError("Wrong write32 value at address " + Long.toHexString(address) + ": expected " + Long.toHexString(expected) + ", got " + Long.toHexString(actual));
                    }
                    cursor[0]++;
                }
            };

            PendingComponentRoles27563E1.Resolved resolved = PendingComponentRoles27563E1.resolve(
                memory, scene.component(), scene.context(), scene.moduleBase()
            );

            if (resolved.r14() != scene.r14()) {
                throw new AssertionError("Scene " + scene.name() + ": r14 mismatch: expected " + Long.toHexString(scene.r14()) + ", got " + Long.toHexString(resolved.r14()));
            }
            if (resolved.r15() != scene.r15()) {
                throw new AssertionError("Scene " + scene.name() + ": r15 mismatch: expected " + Long.toHexString(scene.r15()) + ", got " + Long.toHexString(resolved.r15()));
            }
            if (resolved.rdi() != scene.rdi()) {
                throw new AssertionError("Scene " + scene.name() + ": rdi mismatch: expected " + Long.toHexString(scene.rdi()) + ", got " + Long.toHexString(resolved.rdi()));
            }
            if (cursor[0] != steps.size()) {
                throw new AssertionError("Scene " + scene.name() + ": steps not fully consumed: expected " + steps.size() + ", got " + cursor[0]);
            }
        }
        System.out.println("PASS: " + count + " scenes");
    }
}
