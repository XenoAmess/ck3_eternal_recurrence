package org.xar.ck3.control.g2.common.nativecore.task.captured.m4cleanup.lower61;
import java.util.List;
import java.util.ArrayList;
import java.util.Collections;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.g2.common.nativecore.task.captured.m4cleanup.b374.B374Inputs;
import org.xar.ck3.control.g2.common.nativecore.task.captured.m4cleanup.b374.B374Candidate;
import org.xar.ck3.control.g2.common.nativecore.task.captured.m4cleanup.B374ReleaseGraph;
import static org.junit.jupiter.api.Assertions.*;
public final class B374ReleaseGraphTest {
@Test void testB374ReleaseGraphWithOpaqueSlotEffects() {
    var f = ArrayGraphFixture.create();
    f.firstEffect = known -> {
        if (known.r8Raw() == ArrayGraphFixture.FIRST) {
            f.qwords.put(FourGraphSeed.T54 + 8L, 0x220000002L);
            f.qwords.put(FourGraphSeed.T54 + 0x148L, 0x330000003L);
        }
    };
    var calls = B374ReleaseGraph.assemble(FourGraphSeed.BASE, f, f, f);
    B374Candidate.execute(new B374Inputs.CallInput(FourGraphSeed.BASE, FourGraphSeed.OBJECT), f, calls);

    var expectedEdges = new ArrayList<>();
    expectedEdges.add(new Lower61Fixture.Edge(false, ArrayGraphFixture.FIRST));
    expectedEdges.add(new Lower61Fixture.Edge(false, 0x220000002L));
    expectedEdges.addAll(Collections.nCopies(38, new Lower61Fixture.Edge(false, ArrayGraphFixture.COMMON)));
    expectedEdges.add(new Lower61Fixture.Edge(false, 0x210000001L));
    expectedEdges.add(new Lower61Fixture.Edge(false, 0x330000003L));
    expectedEdges.add(new Lower61Fixture.Edge(false, 0x210000003L));
    expectedEdges.addAll(Collections.nCopies(40, new Lower61Fixture.Edge(false, ArrayGraphFixture.COMMON)));
    expectedEdges.add(new Lower61Fixture.Edge(false, 0x210000004L));
    expectedEdges.add(new Lower61Fixture.Edge(false, 0x210000005L));
    expectedEdges.add(new Lower61Fixture.Edge(false, 0x210000006L));
    expectedEdges.add(new Lower61Fixture.Edge(false, 0x210000007L));
    expectedEdges.add(new Lower61Fixture.Edge(false, FourGraphSeed.T54));
    expectedEdges.add(new Lower61Fixture.Edge(true, FourGraphSeed.OBJECT));
    assertEquals(expectedEdges, f.edges);

    var sourceReads = f.events.stream().filter(e -> e instanceof Lower61Fixture.Read64)
        .map(e -> (Lower61Fixture.Read64)e)
        .filter(r -> r.address() >= FourGraphSeed.T54 && r.address() <= FourGraphSeed.T54 + 0x2B8L)
        .toList();
    assertEquals(87, sourceReads.size());
    assertEquals(new Lower61Fixture.Read64(FourGraphSeed.T54, ArrayGraphFixture.FIRST), sourceReads.get(0));
    assertEquals(new Lower61Fixture.Read64(FourGraphSeed.T54 + 8L, 0x220000002L), sourceReads.get(1));
    assertTrue(sourceReads.contains(new Lower61Fixture.Read64(FourGraphSeed.T54 + 0x148L, 0x330000003L)));
    assertFalse(sourceReads.contains(new Lower61Fixture.Read64(FourGraphSeed.T54 + 0x148L, 0x210000002L)));

    assertEquals(89, f.firstCalls.size());
    for (int i = 0; i < 89; i++) {
        assertEquals(f.edges.get(i).rcxRaw(), f.firstCalls.get(i).r8Raw());
        assertEquals(101L, f.firstCalls.get(i).rcxRaw());
        assertEquals(0L, f.firstCalls.get(i).rdxRaw());
    }

    assertEquals(1L, sourceReads.stream().filter(read -> read.address() == FourGraphSeed.T54 + 0x148L).count());
    assertTrue(f.remainingCalls.isEmpty());
    assertFalse(f.events.contains(Lower61Fixture.Opaque.POINTER));
    assertFalse(f.events.contains(Lower61Fixture.Opaque.ERROR));
    assertTrue(f.writes32.isEmpty());
    assertEquals(0x12345678, f.dwords.get(FourGraphSeed.UNRELATED));
}
}
