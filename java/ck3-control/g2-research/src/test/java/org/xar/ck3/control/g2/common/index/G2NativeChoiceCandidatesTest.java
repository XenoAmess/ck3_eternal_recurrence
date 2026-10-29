package org.xar.ck3.control.g2.common.index;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.index.OrderedCandidateIndex;
import org.xar.ck3.control.contracts.observation.ObservationReuse;
import org.xar.ck3.control.events.mandatorychoice.IndexedNativeChoices;
import org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceCodec;
import org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.EvidenceDocument;
import org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.FrameBinding;
import org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.Mode;
import org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.NativeChoice;
import org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.NativeWindow;
import org.xar.ck3.control.events.mandatorychoice.MandatoryChoicePolicy;
import org.xar.ck3.control.g2.common.G2Exception;
import org.xar.ck3.control.g2.common.G2HttpError;
import org.xar.ck3.control.g2.common.G2Source;

/** Real G2 source/owner -> native codec -> original policy -> persisted decision consumer. No Game I/O. */
final class G2NativeChoiceCandidatesTest {
    private static final ObjectMapper JSON = new ObjectMapper();
    private static final String WRITER = "synthetic-original-writer";

    private static G2Source source(String digest) {
        return new G2Source("synthetic-index-fixture", "2026-10-23T00:00:00Z", "synthetic-no-game",
                new ExactRef("fixture-source-not-opened.json", 1, digest.repeat(64)));
    }

    private static ObservationReuse.WriterVersion version(int value) {
        return new ObservationReuse.WriterVersion(WRITER, BigInteger.valueOf(value));
    }

    private static JsonNode originalFixture() throws Exception {
        try (var input = G2NativeChoiceCandidatesTest.class.getResourceAsStream(
                "/mandatorychoice/producer-golden-v1.json")) {
            assertNotNull(input, "actual retained producer fixture required; absence is a failure");
            return JSON.readTree(input);
        }
    }

    private static ObservationReuse<G2Source, FrameBinding, EvidenceDocument> owner() {
        return new ObservationReuse<>(WRITER, 2);
    }

    private static IndexedNativeChoices<ObservationReuse.Token<G2Source, FrameBinding>> join(
            G2Source source, ObservationReuse<G2Source, FrameBinding, EvidenceDocument> owner,
            NativeWindow window) {
        var token = owner.bindFresh(new ObservationReuse.Scope<>(source, window.frame(), version(1)));
        return G2CandidateIndex.nativeChoices(source, token, owner, window);
    }

    @Test void everyOriginalProducerDecisionTraversesG2AndItsExistingSerializationConsumer() throws Exception {
        JsonNode golden = originalFixture();
        assertEquals(17, golden.get("cases").size(), "complete original corpus, no sample cap");
        for (JsonNode vector : golden.get("cases")) {
            var window = MandatoryChoiceCodec.decode(JSON.writeValueAsBytes(vector.get("input")));
            var owner = owner();
            try {
                var candidates = join(source("a"), owner, window);
                assertEquals(window.choices().size(), candidates.entries().size());
                for (int position = 0; position < window.choices().size(); position++) {
                    assertSame(window.choices().get(position), candidates.entries().get(position).value());
                    assertEquals(position, candidates.entries().get(position).position());
                }
                Optional<FrameBinding> expected = vector.get("expected_frame").isNull() ? Optional.empty()
                        : Optional.of(MandatoryChoiceCodec.decodeFrame(
                                JSON.writeValueAsBytes(vector.get("expected_frame"))));
                Mode mode = vector.get("mode").asText().equals("unknown")
                        ? Mode.UNKNOWN_MANDATORY : Mode.EXISTING_NATIVE_DOMAIN;
                byte[] decision = MandatoryChoiceCodec.encodeDecision(candidates.select(expected, mode));
                assertEquals(vector.get("output"), JSON.readTree(decision), vector.get("name").asText());
                assertArrayEquals(MandatoryChoiceCodec.encodeDecision(
                        MandatoryChoicePolicy.select(window, expected, mode)), decision);
                var restoredWindow = MandatoryChoiceCodec.decode(MandatoryChoiceCodec.encodeWindow(window));
                assertArrayEquals(decision, MandatoryChoiceCodec.encodeDecision(
                        MandatoryChoicePolicy.select(restoredWindow, expected, mode)));
            } finally {
                owner.close();
            }
        }
    }

    @Test void g2RankingEquatesSignedZerosWithoutChangingOriginalBitsOrSourceOrder() throws Exception {
        JsonNode golden = originalFixture();
        for (String axis : List.of("top", "left")) {
            ObjectNode input = golden.get("cases").get(0).get("input").deepCopy();
            ((ObjectNode) input.get("choices").get(0).get("bounds")).put(axis, 0.0);
            ((ObjectNode) input.get("choices").get(1).get("bounds")).put(axis, -0.0);
            var window = MandatoryChoiceCodec.decode(JSON.writeValueAsBytes(input));
            var first = (NativeChoice) window.choices().get(0);
            var second = (NativeChoice) window.choices().get(1);
            var owner = owner();
            try {
                var candidates = join(source("a"), owner, window);
                var decision = candidates.select(Optional.empty(), Mode.UNKNOWN_MANDATORY);
                assertSame(first, decision.selectedChoice().orElseThrow(), axis);
                assertEquals(List.of(first.identity(), second.identity()),
                        decision.evidence().orderedEligibleChoiceIds(), axis);
                assertEquals(List.of(0, 1), candidates.entries().stream()
                        .map(OrderedCandidateIndex.Slot::position).toList());
                assertSame(second, candidates.entries().get(1).value());
                assertEquals(Long.MIN_VALUE, Double.doubleToRawLongBits(axis.equals("top")
                        ? second.geometry().orElseThrow().top() : second.geometry().orElseThrow().left()));
                var restored = MandatoryChoiceCodec.decode(MandatoryChoiceCodec.encodeWindow(window));
                var restoredSecond = (NativeChoice) restored.choices().get(1);
                assertEquals(Long.MIN_VALUE, Double.doubleToRawLongBits(axis.equals("top")
                        ? restoredSecond.geometry().orElseThrow().top() : restoredSecond.geometry().orElseThrow().left()));
                byte[] persisted = MandatoryChoiceCodec.encodeDecision(decision);
                assertArrayEquals(MandatoryChoiceCodec.encodeDecision(MandatoryChoicePolicy.selectUnknownMandatory(
                        restored, Optional.empty())), persisted);
            } finally {
                owner.close();
            }
        }
    }

    @Test void wrongSourceFrameRevocationAndUnknownCannotReachRanking() throws Exception {
        ObjectNode input = originalFixture().get("cases").get(0).get("input").deepCopy();
        var window = MandatoryChoiceCodec.decode(JSON.writeValueAsBytes(input));
        var owner = owner();
        try {
            G2Source source = source("a");
            var token = owner.bindFresh(new ObservationReuse.Scope<>(source, window.frame(), version(1)));
            var mismatch = assertThrows(G2Exception.class,
                    () -> G2CandidateIndex.nativeChoices(source("b"), token, owner, window));
            assertEquals(G2HttpError.Code.SOURCE_MISMATCH, mismatch.code());
            ((ObjectNode) input.get("frame_binding")).put("snapshot_id", "different-frame");
            var differentFrame = MandatoryChoiceCodec.decode(JSON.writeValueAsBytes(input));
            mismatch = assertThrows(G2Exception.class,
                    () -> G2CandidateIndex.nativeChoices(source, token, owner, differentFrame));
            assertEquals(G2HttpError.Code.SOURCE_MISMATCH, mismatch.code());
            var candidates = G2CandidateIndex.nativeChoices(source, token, owner, window);
            owner.beforeSubmit(version(1));
            assertThrows(IllegalStateException.class,
                    () -> candidates.select(Optional.empty(), Mode.UNKNOWN_MANDATORY));
            var next = owner.bindFresh(new ObservationReuse.Scope<>(source, window.frame(), version(2)));
            var nextCandidates = G2CandidateIndex.nativeChoices(source, next, owner, window);
            owner.unknownOutcome(version(2));
            assertThrows(IllegalStateException.class, nextCandidates::entries);
            assertThrows(IllegalStateException.class,
                    () -> nextCandidates.select(Optional.empty(), Mode.UNKNOWN_MANDATORY));
            assertThrows(IllegalStateException.class,
                    () -> owner.bindFresh(new ObservationReuse.Scope<>(source, window.frame(), version(3))));
        } finally {
            owner.close();
        }
    }
}
