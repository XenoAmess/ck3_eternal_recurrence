package org.xar.ck3.control.application.planning.sway;

import static org.junit.jupiter.api.Assertions.*;

import java.util.List;
import java.util.ArrayList;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.PlanningReadResult;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/**
 * Diagnostic propagation test for SwaySelectedFinish.sourceUnavailable.
 * Verifies that Unavailable.reason is appended to legacy detail, capped at 2048 codepoints,
 * and serialized via SwayPublicCodec.retained without altering evidence or status.
 */
public class SwaySelectedFinishUnavailable207Test {

    private static final String PHASE_TARGET = "actual current target quote unavailable";
    private static final String PHASE_COMPLETION = "actual original full-instance completion read unavailable";
    private static final String PHASE_OPINION = "actual independent named benefit read unavailable";

    private static ExactRef ref(String path) {
        return new ExactRef(path, 10, "0000000000000000000000000000000000000000000000000000000000000000");
    }

    private static PlanningReadResult.Unavailable<String> unavailable(String reason) {
        return new PlanningReadResult.Unavailable<>(reason, Optional.empty(), Optional.empty(), Optional.empty());
    }

    @Test
    void threeLegacyPhasesAndEvidenceSizes() {
        // Phase 1: Target, 0 refs
        var actual1 = unavailable("reason1");
        List<ExactRef> refs1 = List.of();
        var result1 = SwaySelectedFinish.sourceUnavailable(actual1, PHASE_TARGET, refs1);
        assertEquals(SwaySelectedFinish.Reason.CURRENT_SOURCE_UNAVAILABLE, result1.reason());
        assertEquals(PHASE_TARGET + ": reason1", result1.detail());
        assertEquals(0, result1.evidence().size());

        // Phase 2: Completion, 1 ref
        var actual2 = unavailable("reason2");
        var refs2 = List.of(ref("target-read-1"));
        var result2 = SwaySelectedFinish.sourceUnavailable(actual2, PHASE_COMPLETION, refs2);
        assertEquals(SwaySelectedFinish.Reason.CURRENT_SOURCE_UNAVAILABLE, result2.reason());
        assertEquals(PHASE_COMPLETION + ": reason2", result2.detail());
        assertEquals(1, result2.evidence().size());
        assertEquals("target-read-1", result2.evidence().get(0).path());

        // Phase 3: Opinion, 2 refs
        var actual3 = unavailable("reason3");
        var refs3 = List.of(ref("target-read-1"), ref("completion-read-1"));
        var result3 = SwaySelectedFinish.sourceUnavailable(actual3, PHASE_OPINION, refs3);
        assertEquals(SwaySelectedFinish.Reason.CURRENT_SOURCE_UNAVAILABLE, result3.reason());
        assertEquals(PHASE_OPINION + ": reason3", result3.detail());
        assertEquals(2, result3.evidence().size());
        assertEquals("target-read-1", result3.evidence().get(0).path());
        assertEquals("completion-read-1", result3.evidence().get(1).path());

        // Verify codec serialization for one case
        var json = SwayPublicCodec.retained(result3);
        var node = StrictJson.parse(json.bytes());
        assertEquals("current_source_unavailable", node.get("status").asText());
        assertEquals(false, node.get("postcondition_verified").asBoolean());
        assertEquals(PHASE_OPINION + ": reason3", node.get("detail").asText());
        assertEquals(2, node.get("evidence").size());
    }

    @Test
    void nullFallbackAndImmutablePriorRefCopy() {
        // Null actual retains legacy detail
        var refs = List.of(ref("read-1"));
        var resultNull = SwaySelectedFinish.sourceUnavailable(null, PHASE_TARGET, refs);
        assertEquals(SwaySelectedFinish.Reason.CURRENT_SOURCE_UNAVAILABLE, resultNull.reason());
        assertEquals(PHASE_TARGET, resultNull.detail());
        assertEquals(1, resultNull.evidence().size());

        // Known actual (not Unavailable) retains legacy detail
        // Note: Cannot construct Known with nulls due to contract, but we can test null path which covers "not Unavailable"
        // The helper checks `if (actual instanceof PlanningReadResult.Unavailable)`.
        // If we pass null, it is not Unavailable.

        // Immutability check
        var mutableRefs = new ArrayList<ExactRef>();
        mutableRefs.add(ref("read-1"));
        var actual = unavailable("reason");
        var result = SwaySelectedFinish.sourceUnavailable(actual, PHASE_TARGET, mutableRefs);

        // Modify original list
        mutableRefs.add(ref("read-2"));

        // Result should still have only 1 ref (Retained constructor copies)
        assertEquals(1, result.evidence().size());
        assertEquals("read-1", result.evidence().get(0).path());
    }

    @Test
    void boundary2048_2049_Supplementary_MaxValid() {
        // 2048 codepoints: No ellipsis
        var reason2048 = "a".repeat(2048);
        var actual2048 = unavailable(reason2048);
        var result2048 = SwaySelectedFinish.sourceUnavailable(actual2048, PHASE_TARGET, List.of());
        assertEquals(PHASE_TARGET + ": " + reason2048, result2048.detail());

        // 2049 codepoints: Ellipsis added, truncated to 2048
        var reason2049 = "a".repeat(2049);
        var actual2049 = unavailable(reason2049);
        var result2049 = SwaySelectedFinish.sourceUnavailable(actual2049, PHASE_TARGET, List.of());
        assertEquals(PHASE_TARGET + ": " + "a".repeat(2048) + "...", result2049.detail());

        // Exercise the actual supplementary-codepoint cut, not a below-limit UTF16 length.
        String emoji = Character.toString(0x1f600);
        String emojiReason = emoji.repeat(2049);
        var resultEmoji = SwaySelectedFinish.sourceUnavailable(unavailable(emojiReason), PHASE_TARGET, List.of());
        assertEquals(PHASE_TARGET + ": " + emoji.repeat(2048) + "...", resultEmoji.detail());
        assertEquals(resultEmoji.detail(), StrictJson.parse(SwayPublicCodec.retained(resultEmoji).bytes()).get("detail").textValue());

        // Max valid reason length (32768 codepoints)
        var maxReason = emoji.repeat(32768);
        var actualMax = unavailable(maxReason);
        var resultMax = SwaySelectedFinish.sourceUnavailable(actualMax, PHASE_TARGET, List.of());
        assertEquals(PHASE_TARGET + ": " + emoji.repeat(2048) + "...", resultMax.detail());
        assertEquals(resultMax.detail(), StrictJson.parse(SwayPublicCodec.retained(resultMax).bytes()).get("detail").textValue());
    }

    @Test
    void actualNewlineQuoteUTF8JsonRoundtrip() {
        // Actual newline and quote characters in reason
        String reason = "line1" + (char) 10 + "line2" + (char) 34 + "quoted" + (char) 34;
        var actual = unavailable(reason);
        var result = SwaySelectedFinish.sourceUnavailable(actual, PHASE_TARGET, List.of());

        assertEquals(PHASE_TARGET + ": " + reason, result.detail());

        var json = SwayPublicCodec.retained(result);
        var node = StrictJson.parse(json.bytes());

        assertEquals(PHASE_TARGET + ": " + reason, node.get("detail").asText());
    }
}