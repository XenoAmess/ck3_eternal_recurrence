package org.xar.ck3.control.g2.m2.nativecode;
import org.xar.ck3.control.g2.m2.nativecode.PendingContextChildWitness259Api.*;
import java.util.List;
import java.util.ArrayList;

public final class PendingContextChildWitnessBook259 {
    public static Scene scene() {
        long receiver = 0x100000000L;
        long moduleBase = 0x200000000L;
        long vtableA = moduleBase + 0x451A430L;
        long vtableB = 0x300000000L;
        long target10 = 0x400000000L;
        long target20 = 0x500000000L;
        long rdx = 0L;
        long r8d = 1L;
        long r8 = receiver + 0x8L;

        List<Cell> initial = new ArrayList<>();
        initial.add(new Cell(receiver, 8, 0L));
        initial.add(new Cell(receiver + 0x8L, 8, 0L));
        initial.add(new Cell(receiver + 0x10L, 8, 0L));
        initial.add(new Cell(receiver + 0x18L, 8, vtableA));
        initial.add(new Cell(receiver + 0x20L, 8, 0L));
        initial.add(new Cell(receiver + 0x28L, 8, 0L));
        initial.add(new Cell(vtableA + 0x10L, 8, target10));
        initial.add(new Cell(vtableB + 0x20L, 8, target20));

        List<Step> steps = new ArrayList<>();
        steps.add(new Step(Kind.W64, receiver, 0L, List.of(), List.of()));
        steps.add(new Step(Kind.W32, receiver + 0x8L, 0, List.of(), List.of()));
        steps.add(new Step(Kind.W64, receiver + 0x10L, receiver + 0x18L, List.of(), List.of()));
        steps.add(new Step(Kind.W64, receiver + 0x18L, vtableA, List.of(), List.of()));
        steps.add(new Step(Kind.W64, receiver + 0x28L, moduleBase + 0x54E0530L, List.of(), List.of()));
        steps.add(new Step(Kind.R64, receiver, 0L, List.of(), List.of()));
        steps.add(new Step(Kind.W32, receiver + 0xCL, 0, List.of(), List.of()));
        steps.add(new Step(Kind.R64, receiver + 0x10L, receiver + 0x18L, List.of(), List.of()));
        steps.add(new Step(Kind.R64, receiver + 0x18L, vtableA, List.of(), List.of()));
        steps.add(new Step(Kind.R64, vtableA + 0x10L, target10, List.of(), List.of()));
        steps.add(new Step(Kind.CALL10, 0L, 0L, List.of(target10, receiver + 0x18L, rdx, r8d), List.of(new Cell(receiver + 0x18L, 8, vtableB), new Cell(receiver, 8, 0x1111111111111111L), new Cell(receiver + 0x8L, 8, 0x2222222222222222L))));
        steps.add(new Step(Kind.R64, receiver + 0x18L, vtableB, List.of(), List.of()));
        steps.add(new Step(Kind.W64, receiver, 0L, List.of(), List.of()));
        steps.add(new Step(Kind.W64, receiver + 0x8L, 0L, List.of(), List.of()));
        steps.add(new Step(Kind.R64, vtableB + 0x20L, target20, List.of(), List.of()));
        steps.add(new Step(Kind.CALL20, 0L, 0L, List.of(target20, receiver + 0x18L, receiver, r8), List.of()));

        List<Cell> finalCells = new ArrayList<>();
        finalCells.add(new Cell(receiver, 8, 0L));
        finalCells.add(new Cell(receiver + 0x8L, 8, 0L));
        finalCells.add(new Cell(receiver + 0x10L, 8, receiver + 0x18L));
        finalCells.add(new Cell(receiver + 0x18L, 8, vtableB));
        finalCells.add(new Cell(receiver + 0x28L, 8, moduleBase + 0x54E0530L));

        return new Scene("normal127B", receiver, moduleBase, initial, steps, receiver, finalCells);
    }
}