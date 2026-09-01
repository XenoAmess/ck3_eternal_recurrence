package com.xenoamess.kaishek.runtime;

import static org.junit.jupiter.api.Assertions.*;

import java.util.List;
import org.junit.jupiter.api.Test;

/** Acceptance contract for the finite, replayable random source.
 *
 * The test deliberately checks the recorded draw positions as well as values:
 * a matching final value without a matching tape consumption trace is not a
 * valid replay.
 */
class DrawTapeContractTest {
    @Test
    void sameTapeProducesSameValuesAndDrawRecords() {
        DrawTape first = DrawTape.of(7, -1, Integer.MIN_VALUE, 12);
        DrawTape second = DrawTape.of(7, -1, Integer.MIN_VALUE, 12);

        // floorMod(Integer.MIN_VALUE, 3) is 1; keeping this explicit guards
        // against accidentally switching to a truncating remainder or an
        // unseeded system RNG during replay.
        assertEquals(List.of(2, 3, 1),
                List.of(first.drawInt(5, "grade"), first.drawInt(4, "route"), first.drawInt(3, "coin")));
        assertEquals(List.of(2, 3, 1),
                List.of(second.drawInt(5, "grade"), second.drawInt(4, "route"), second.drawInt(3, "coin")));
        assertEquals(first.records(), second.records());
        assertEquals(3, first.position());
        assertEquals(1, first.remaining());
        assertEquals("grade", first.records().get(0).purpose());
        assertEquals(-1, first.records().get(1).rawValue());
    }

    @Test
    void floorModHandlesNegativeAndMinIntegerWithoutSystemRandomFallback() {
        DrawTape tape = DrawTape.of(-1, Integer.MIN_VALUE);
        assertEquals(4, tape.drawInt(5));
        assertEquals(Math.floorMod(Integer.MIN_VALUE, 7), tape.drawInt(7));
        assertThrows(DrawTapeExhaustedException.class, () -> tape.drawInt(2));
        assertEquals(2, tape.position());
        assertEquals(2, tape.records().size());
    }

    @Test
    void booleanAndChooseConsumeExactlyOneTapeCell() {
        DrawTape tape = DrawTape.of(1, 0);
        assertTrue(tape.drawBoolean("coin-flip"));
        assertEquals("a", tape.choose(List.of("a", "b"), "pick"));
        assertEquals(2, tape.position());
        assertEquals("coin-flip", tape.records().get(0).purpose());
        assertEquals("pick", tape.records().get(1).purpose());
    }

    @Test
    void invalidBoundsAndEmptyCandidatesAreRejected() {
        DrawTape tape = DrawTape.of(1);
        assertThrows(IllegalArgumentException.class, () -> tape.drawInt(0));
        assertThrows(IllegalArgumentException.class, () -> tape.choose(List.of(), "empty"));
        assertEquals(0, tape.position(), "failed validation must not consume tape");
    }

    @Test
    void boundedDrawPropertyHoldsForAdversarialIntegerCorpus() {
        int[] corpus = {Integer.MIN_VALUE, -1001, -1, 0, 1, 2, 1001, Integer.MAX_VALUE};
        for (int raw : corpus) {
            for (int bound : new int[] {1, 2, 3, 7, 31, Integer.MAX_VALUE}) {
                DrawTape tape = DrawTape.of(raw);
                int actual = tape.drawInt(bound, "property");
                assertTrue(actual >= 0 && actual < bound);
                assertEquals(Math.floorMod(raw, bound), actual);
                assertEquals(1, tape.position());
            }
        }
    }
}
