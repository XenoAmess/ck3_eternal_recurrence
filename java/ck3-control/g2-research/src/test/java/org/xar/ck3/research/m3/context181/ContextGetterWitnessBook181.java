package org.xar.ck3.research.m3.context181;

import java.util.List;
import org.xar.ck3.research.m3.context181.ContextGetter181Api.*;
import org.xar.ck3.research.m3.context181.ContextGetterWitness181Api.*;

/** Owner source-literal DATA after model rejection; owner had reviewed the target candidate. */
public final class ContextGetterWitnessBook181 {
    private static final long BASE = 0x0000000140000000L;
    private static final long RSP = 0x0000000180100000L;
    private static final long GLOBAL = BASE + 0x5D1E2C8L;
    private static final long DESCRIPTOR = RSP + 0x20L;
    private static final long DATA = BASE + 0x448D018L;
    private static final long INITIAL_LOW = 0x1122334455667788L;
    private static final long INITIAL_HIGH = 0xE3D2C1B0A5968778L;
    private static final long FINAL_HIGH = 0xE3D2C1000000001EL;
    private ContextGetterWitnessBook181() { }
    private static Cell cell(long address, int width, long low, long high) { return new Cell(address, width, low, high); }
    private static Step step(Kind kind, long address, long low, long high) {
        return new Step(kind, address, low, high, List.of(), 0, List.of());
    }
    private static Input input() { return new Input(BASE, new Scratch(RSP)); }
    public static List<Scene> scenes() {
        long existing = 0xF123456700000000L;
        Scene fast = new Scene("nonzero-upper32-low32-zero", input(),
                List.of(cell(GLOBAL, 8, existing, 0), cell(DESCRIPTOR, 16, INITIAL_LOW, INITIAL_HIGH)),
                List.of(step(Kind.R64, GLOBAL, existing, 0)), existing,
                List.of(cell(GLOBAL, 8, existing, 0), cell(DESCRIPTOR, 16, INITIAL_LOW, INITIAL_HIGH)));
        return List.of(fast, slow("null-publish-fresh", 0xFEDCBA9876543210L, 0x1111222233334444L),
                slow("null-stays-null-ignore-opaque-return", 0, 0xDEADBEEF00000001L));
    }
    private static Scene slow(String name, long published, long ignoredReturn) {
        Step call = new Step(Kind.CALL, 0, 0, 0,
                List.of(0xA92EF6L, 1L, DESCRIPTOR, 0L, 0x64L), ignoredReturn,
                published == 0 ? List.of() : List.of(cell(GLOBAL, 8, published, 0)));
        return new Scene(name, input(),
                List.of(cell(GLOBAL, 8, 0, 0), cell(DESCRIPTOR, 16, INITIAL_LOW, INITIAL_HIGH)),
                List.of(step(Kind.R64, GLOBAL, 0, 0), step(Kind.W32, RSP + 0x28L, 0x1E, 0),
                        step(Kind.W64, DESCRIPTOR, DATA, 0), step(Kind.W8, RSP + 0x2CL, 0, 0),
                        step(Kind.R128, DESCRIPTOR, DATA, FINAL_HIGH), step(Kind.W128, DESCRIPTOR, DATA, FINAL_HIGH),
                        call, step(Kind.R64, GLOBAL, published, 0)), published,
                List.of(cell(GLOBAL, 8, published, 0), cell(DESCRIPTOR, 16, DATA, FINAL_HIGH),
                        cell(RSP + 0x2DL, 1, 0xC1, 0), cell(RSP + 0x2EL, 1, 0xD2, 0), cell(RSP + 0x2FL, 1, 0xE3, 0)));
    }
}
