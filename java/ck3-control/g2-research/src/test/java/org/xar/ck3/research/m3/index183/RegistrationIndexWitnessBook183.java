package org.xar.ck3.research.m3.index183;

import java.util.ArrayList;
import java.util.List;
import org.xar.ck3.research.m3.index183.RegistrationIndex183Api.Input;
import org.xar.ck3.research.m3.index183.RegistrationIndex183Api.Scratch;
import org.xar.ck3.research.m3.index183.RegistrationIndexWitness183Api.Cell;
import org.xar.ck3.research.m3.index183.RegistrationIndexWitness183Api.Kind;
import org.xar.ck3.research.m3.index183.RegistrationIndexWitness183Api.Scene;
import org.xar.ck3.research.m3.index183.RegistrationIndexWitness183Api.Step;

/** Independent finite normal397B observation literals. Comparator results stay opaque. */
public final class RegistrationIndexWitnessBook183 {
    private static final long FILL = 0xa1b2c3d4e5f60718L;
    private RegistrationIndexWitnessBook183() { }

    private static Cell c(long address, int width, long low) {
        return new Cell(address, width, low, 0L);
    }

    private static Cell v(long address, long low, long high) {
        return new Cell(address, 16, low, high);
    }

    private static Step s(Kind kind, long address, long low) {
        return new Step(kind, address, low, 0L, List.of(), 0, List.of());
    }

    private static Step x(Kind kind, long address, long low, long high) {
        return new Step(kind, address, low, high, List.of(), 0, List.of());
    }

    private static Step compare(long site, long rcx, long rdx, long signedR8,
                                int eax, Cell... effects) {
        return new Step(Kind.COMPARE, 0L, 0L, 0L,
                List.of(site, rcx, rdx, signedR8), eax, List.of(effects));
    }

    private static ArrayList<Cell> scratch(long bodyRsp) {
        ArrayList<Cell> result = new ArrayList<>();
        for (int offset = 0; offset < 0xa0; offset += 16) {
            result.add(v(bodyRsp + offset, FILL, FILL));
        }
        return result;
    }

    private static Scene empty() {
        long rsp = 0x100000L;
        long receiver = 0x0000011100001100L;
        long base = 0x0000012200001200L;
        long key = 0x0000013300001300L;
        ArrayList<Cell> initial = scratch(rsp);
        initial.addAll(List.of(c(receiver, 8, base), c(receiver + 0xcL, 4, 0L)));
        return new Scene("empty-count-no-key-read-or-compare",
                new Input(receiver, key, new Scratch(rsp)), List.copyOf(initial), List.of(
                s(Kind.W64, rsp + 0x88L, key),
                s(Kind.R64, receiver, base),
                s(Kind.R32, receiver + 0xcL, 0L),
                s(Kind.W64, rsp + 0x90L, base)), -1, List.of(
                c(rsp + 0x88L, 8, key), c(rsp + 0x90L, 8, base),
                v(rsp + 0x20L, FILL, FILL), v(rsp + 0x30L, FILL, FILL)));
    }

    private static Scene negativeCountTail() {
        long rsp = 0x200000L;
        long receiver = 0x0000021100002100L;
        long base = 0x8000022200002200L;
        long key = 0x0000023300002300L;
        long recordData = 0x8000024400002400L;
        long keyData = 0x0000025500002500L;
        long keyHigh = 0x50607080fffffffbL;
        long descriptorHigh = 0xa1b2c300fffffffcL;
        ArrayList<Cell> initial = scratch(rsp);
        initial.addAll(List.of(c(receiver, 8, base), c(receiver + 0xcL, 4, 0xffffffffL),
                c(base + 0x18L, 8, 0x8000000000000000L),
                c(base + 0x10L, 4, 0xfffffffcL), c(base, 8, recordData),
                v(key, keyData, keyHigh)));
        return new Scene("negative-count-still-tail-heap-and-signed-length",
                new Input(receiver, key, new Scratch(rsp)), List.copyOf(initial), List.of(
                s(Kind.W64, rsp + 0x88L, key),
                s(Kind.R64, receiver, base),
                s(Kind.R32, receiver + 0xcL, 0xffffffffL),
                s(Kind.W64, rsp + 0x90L, base - 64L),
                s(Kind.R64, base + 0x18L, 0x8000000000000000L),
                s(Kind.R32, base + 0x10L, 0xfffffffcL),
                s(Kind.R64, base, recordData),
                x(Kind.R128, key, keyData, keyHigh),
                s(Kind.W64, rsp + 0x20L, recordData),
                s(Kind.W32, rsp + 0x28L, 0xfffffffcL),
                s(Kind.W8, rsp + 0x2cL, 0L),
                x(Kind.R128, rsp + 0x20L, recordData, descriptorHigh),
                x(Kind.W128, rsp + 0x20L, recordData, descriptorHigh),
                x(Kind.W128, rsp + 0x30L, keyData, keyHigh),
                s(Kind.R32, rsp + 0x38L, 0xfffffffbL),
                compare(0x3f5441cL, keyData, recordData, -5L, 0)), -1, List.of(
                c(rsp + 0x88L, 8, key), c(rsp + 0x90L, 8, base - 64L),
                v(rsp + 0x20L, recordData, descriptorHigh),
                v(rsp + 0x30L, keyData, keyHigh)));
    }

    private static Scene singleCountFreshHomeAndEnd() {
        long rsp = 0x300000L;
        long receiver = 0x0000031100003100L;
        long base = 0x0000032200003200L;
        long second = base + 64L;
        long key = 0x0000033300003300L;
        long freshKey = 0x0000034400003400L;
        long keyData = 0x0000035500003500L;
        long freshKeyData = 0x8000036600003600L;
        long secondData = 0x8000037700003700L;
        long keyHigh = 0x88776655fffffffdL;
        long freshHigh = 0x99aabbcc0000000aL;
        long descriptorHigh = 0x8877fa0000000004L;
        ArrayList<Cell> initial = scratch(rsp);
        initial.addAll(List.of(c(receiver, 8, base), c(receiver + 0xcL, 4, 1L),
                c(base + 0x18L, 8, 15L), c(base + 0x10L, 4, 7L),
                c(second + 0x18L, 8, 0x8000000000000000L),
                c(second + 0x10L, 4, 4L), c(second, 8, secondData),
                v(key, keyData, keyHigh), v(freshKey, freshKeyData, freshHigh)));
        return new Scene("count-one-captured-key-fresh-end-home-and-tail",
                new Input(receiver, key, new Scratch(rsp)), List.copyOf(initial), List.of(
                s(Kind.W64, rsp + 0x88L, key),
                s(Kind.R64, receiver, base),
                s(Kind.R32, receiver + 0xcL, 1L),
                s(Kind.W64, rsp + 0x90L, base + 64L),
                x(Kind.R128, key, keyData, keyHigh),
                x(Kind.W128, rsp + 0x20L, keyData, keyHigh),
                s(Kind.R32, rsp + 0x28L, 0xfffffffdL),
                s(Kind.R64, rsp + 0x20L, keyData),
                s(Kind.R64, base + 0x18L, 15L),
                s(Kind.R32, base + 0x10L, 7L),
                compare(0x3f5436aL, base, keyData, -3L, -7,
                        c(rsp + 0x88L, 8, freshKey), c(rsp + 0x90L, 8, base + 128L),
                        c(rsp + 0x2dL, 1, 0xfaL),
                        v(key, 0x0bad0bad0bad0badL, 0xdeadbeef00000011L)),
                s(Kind.R64, rsp + 0x90L, base + 128L),
                s(Kind.R64, rsp + 0x88L, freshKey),
                s(Kind.R64, second + 0x18L, 0x8000000000000000L),
                s(Kind.R32, second + 0x10L, 4L),
                s(Kind.R64, second, secondData),
                x(Kind.R128, freshKey, freshKeyData, freshHigh),
                s(Kind.W64, rsp + 0x20L, secondData),
                s(Kind.W32, rsp + 0x28L, 4L),
                s(Kind.W8, rsp + 0x2cL, 0L),
                x(Kind.R128, rsp + 0x20L, secondData, descriptorHigh),
                x(Kind.W128, rsp + 0x20L, secondData, descriptorHigh),
                x(Kind.W128, rsp + 0x30L, freshKeyData, freshHigh),
                s(Kind.R32, rsp + 0x28L, 4L),
                compare(0x3f5441cL, freshKeyData, secondData, 4L, 1)), 1, List.of(
                c(rsp + 0x88L, 8, freshKey), c(rsp + 0x90L, 8, base + 128L),
                v(rsp + 0x20L, secondData, descriptorHigh),
                v(rsp + 0x30L, freshKeyData, freshHigh),
                v(key, 0x0bad0bad0bad0badL, 0xdeadbeef00000011L)));
    }

    private static Scene multiIterationCapturedLocals() {
        long rsp = 0x400000L;
        long receiver = 0x0000041100004100L;
        long base = 0x0000042200004200L;
        long middle = base + 64L;
        long last = base + 128L;
        long key = 0x0000043300004300L;
        long keyData = 0x0000044400004400L;
        long freshKeyData = 0x8000045500004500L;
        long middleData = 0x8000046600004600L;
        long alternateBase = 0x8000047700004700L;
        long poisonData = 0x8000048800004800L;
        long keyHigh = 0x1122334400000005L;
        long freshHigh = 0x778899aa00000009L;
        long poisonHigh = 0xdeadbeef11223344L;
        long descriptorHigh = 0xdeadbe0000000008L;
        ArrayList<Cell> initial = scratch(rsp);
        initial.addAll(List.of(c(receiver, 8, base), c(receiver + 0xcL, 4, 3L),
                c(middle + 0x18L, 8, 16L), c(middle + 0x10L, 4, 3L),
                c(middle, 8, middleData), c(last + 0x18L, 8, 15L),
                c(last + 0x10L, 4, 8L), v(key, keyData, keyHigh)));
        return new Scene("count-three-both-search-branches-captured-locals-index-two",
                new Input(receiver, key, new Scratch(rsp)), List.copyOf(initial), List.of(
                s(Kind.W64, rsp + 0x88L, key),
                s(Kind.R64, receiver, base),
                s(Kind.R32, receiver + 0xcL, 3L),
                s(Kind.W64, rsp + 0x90L, base + 192L),
                x(Kind.R128, key, keyData, keyHigh),
                x(Kind.W128, rsp + 0x20L, keyData, keyHigh),
                s(Kind.R32, rsp + 0x28L, 5L),
                s(Kind.R64, rsp + 0x20L, keyData),
                s(Kind.R64, middle + 0x18L, 16L),
                s(Kind.R32, middle + 0x10L, 3L),
                s(Kind.R64, middle, middleData),
                compare(0x3f5436aL, middleData, keyData, 3L, 0,
                        v(key, freshKeyData, freshHigh), v(rsp + 0x20L, poisonData, poisonHigh),
                        c(receiver, 8, alternateBase), c(receiver + 0xcL, 4, 0L)),
                s(Kind.R64, last + 0x18L, 15L),
                s(Kind.R32, last + 0x10L, 8L),
                compare(0x3f5436aL, last, keyData, 5L, 1),
                s(Kind.R64, rsp + 0x90L, base + 192L),
                s(Kind.R64, rsp + 0x88L, key),
                s(Kind.R64, last + 0x18L, 15L),
                s(Kind.R32, last + 0x10L, 8L),
                x(Kind.R128, key, freshKeyData, freshHigh),
                s(Kind.W64, rsp + 0x20L, last),
                s(Kind.W32, rsp + 0x28L, 8L),
                s(Kind.W8, rsp + 0x2cL, 0L),
                x(Kind.R128, rsp + 0x20L, last, descriptorHigh),
                x(Kind.W128, rsp + 0x20L, last, descriptorHigh),
                x(Kind.W128, rsp + 0x30L, freshKeyData, freshHigh),
                s(Kind.R32, rsp + 0x28L, 8L),
                compare(0x3f5441cL, freshKeyData, last, 8L, 0)), 2, List.of(
                c(receiver, 8, alternateBase), c(receiver + 0xcL, 4, 0L),
                v(key, freshKeyData, freshHigh), c(rsp + 0x88L, 8, key),
                c(rsp + 0x90L, 8, base + 192L),
                v(rsp + 0x20L, last, descriptorHigh), v(rsp + 0x30L, freshKeyData, freshHigh)));
    }

    public static List<Scene> scenes() {
        return List.of(empty(), negativeCountTail(), singleCountFreshHomeAndEnd(), multiIterationCapturedLocals());
    }
}
