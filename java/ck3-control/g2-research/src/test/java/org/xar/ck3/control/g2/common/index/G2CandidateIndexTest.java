package org.xar.ck3.control.g2.common.index;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.index.OrderedCandidateIndex;
import org.xar.ck3.control.contracts.observation.ObservationReuse;
import org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.EvidenceDocument;
import org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.FrameBinding;
import org.xar.ck3.control.g2.common.G2Exception;
import org.xar.ck3.control.g2.common.G2HttpError;
import org.xar.ck3.control.g2.common.G2Source;

/** Real common DTO/cache/index join; fixture source references are never opened. */
final class G2CandidateIndexTest {
    private static G2Source source(String sha) {
        return new G2Source("synthetic-index-fixture", "2026-10-23T00:00:00Z", "synthetic-no-game",
                new ExactRef("fixture-source-not-opened.json", 1, sha.repeat(64)));
    }
    private static FrameBinding frame(String snapshot, BigInteger publicRevision) {
        return new FrameBinding(1, BigInteger.ONE, publicRevision, new BigInteger("18446744073709551615"),
                BigInteger.ZERO, BigInteger.ONE, "synthetic-episode", snapshot, new EvidenceDocument("{}"));
    }
    private static ObservationReuse.WriterVersion version(int value) {
        return new ObservationReuse.WriterVersion("synthetic-original-writer", BigInteger.valueOf(value));
    }
    @Test void exactG2SourceAndOriginalFrameTokenGuardEveryCompleteCandidateLookup() {
        G2Source source = source("a"); FrameBinding frame = frame("snapshot-1", BigInteger.ONE);
        var owner = new ObservationReuse<G2Source, FrameBinding, EvidenceDocument>("synthetic-original-writer", 2);
        var token = owner.bindFresh(new ObservationReuse.Scope<>(source, frame, version(1)));
        var values = List.of("first", "second", "first");
        var index = G2CandidateIndex.build(source, token, owner, values,
                value -> new OrderedCandidateIndex.Present<>("same display name"));
        assertEquals(List.of(0, 1, 2), index.slots().stream().map(OrderedCandidateIndex.Slot::position).toList());
        assertEquals(3, index.matching(new OrderedCandidateIndex.Present<>("same display name")).size());
        assertSame(values.get(0), index.slots().getFirst().value());
        var projected = new AtomicInteger();
        G2Exception mismatch = assertThrows(G2Exception.class, () -> G2CandidateIndex.build(source("b"), token, owner, values,
                value -> { projected.incrementAndGet(); return new OrderedCandidateIndex.Present<>(value); }));
        assertEquals(G2HttpError.Code.SOURCE_MISMATCH, mismatch.code());
        assertEquals(0, projected.get(), "wrong request source fails before source projection");
        owner.beforeSubmit(version(1));
        assertThrows(IllegalStateException.class, index::slots);
        assertThrows(IllegalStateException.class, () -> owner.bindFresh(new ObservationReuse.Scope<>(source, frame, version(1))));
        var token2 = owner.bindFresh(new ObservationReuse.Scope<>(source, frame, version(2)));
        var index2 = G2CandidateIndex.build(source, token2, owner, values, value -> new OrderedCandidateIndex.Present<>(value));
        owner.unknownOutcome(version(2));
        assertThrows(IllegalStateException.class, index2::slots);
        assertThrows(IllegalStateException.class, () -> owner.bindFresh(new ObservationReuse.Scope<>(source, frame, version(3))));
        owner.ownerSettledUnknown(version(3));
        var token3 = owner.bindFresh(new ObservationReuse.Scope<>(source, frame, version(3)));
        var index3 = G2CandidateIndex.build(source, token3, owner, values, value -> new OrderedCandidateIndex.Present<>(value));
        owner.bindFresh(new ObservationReuse.Scope<>(source, frame("snapshot-2", BigInteger.TWO), version(3)));
        assertThrows(IllegalStateException.class, index3::slots);
        assertThrows(IllegalStateException.class, index::slots, "fresh binding never revives old catalogue");
        owner.close();
        assertThrows(IllegalStateException.class, index2::slots);
    }
}
