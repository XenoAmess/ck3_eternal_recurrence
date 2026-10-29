package org.xar.ck3.control.wave3.governance.focusread;

import java.math.BigInteger;
import java.util.Arrays;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.governance.lifestyle.LifestyleMinPolicy;
import org.xar.ck3.control.governance.lifestyle.LifestyleMinPolicy.Field;
import org.xar.ck3.control.governance.lifestyle.LifestyleMinPolicy.FocusProgress;
import org.xar.ck3.control.wave2.governance.focusscope.EducationFocusScope.NativeSourceFrame;
import org.xar.ck3.control.wave2.governance.focusscope.EducationFocusScope.SemanticSnapshot;

/** Fixed wealth/martial readonly source parser. It never transports a pointer or authorizes a submit. */
public final class FocusReadPolicy {
    private FocusReadPolicy() { }
    public enum Target {
        WEALTH("private-query-player-lifestyle-stock-focus-v1", "stewardship_wealth_focus", "stewardship_lifestyle"),
        MARTIAL("private-query-player-lifestyle-martial-authority-v1", "martial_authority_focus", "martial_lifestyle");
        private final String step;
        private final String key;
        private final String lifestyle;
        Target(String step, String key, String lifestyle) { this.step = step; this.key = key; this.lifestyle = lifestyle; }
        public String step() { return step; }
        public String key() { return key; }
        public String lifestyle() { return lifestyle; }
    }
    /** Boundary-owned immutable original JSON, retaining unknown progress fields and decimal values. */
    public static final class RawJson {
        private final byte[] bytes;
        RawJson(byte[] bytes) { this.bytes = bytes.clone(); }
        public byte[] bytes() { return bytes.clone(); }
        @Override public boolean equals(Object other) { return other instanceof RawJson value && Arrays.equals(bytes, value.bytes); }
        @Override public int hashCode() { return Arrays.hashCode(bytes); }
    }
    public enum ProgressNumber {
        XP_TOTAL_RAW, XP_WITHIN_LEVEL_RAW, XP_PER_LEVEL, UNSPENT_PERK_POINTS, USED_PERK_POINTS;
        public String wire() { return name().toLowerCase(java.util.Locale.ROOT); }
    }
    public sealed interface ProgressSource permits Progress, InvalidProgress {
        String presence(); String source(); String reason(); RawJson originalObject();
        boolean hasAnyNumericProperty(); Optional<FocusProgress> observedNumbers();
    }
    /** Invalid numeric tokens remain explicit original evidence; no number is coerced to null or zero. */
    public record InvalidProgress(String presence, String source, String reason,
            Set<ProgressNumber> invalidNumberTypes, RawJson originalObject) implements ProgressSource {
        public InvalidProgress {
            invalidNumberTypes = Set.copyOf(invalidNumberTypes);
            StrictJson.require(!invalidNumberTypes.isEmpty(), "invalid progress needs explicit wrong number types");
            Objects.requireNonNull(originalObject);
        }
        @Override public boolean hasAnyNumericProperty() { return true; }
        @Override public Optional<FocusProgress> observedNumbers() { return Optional.empty(); }
    }
    public record Progress(String presence, String source, String reason, Field<BigInteger> xpTotalRaw,
            Field<BigInteger> xpWithinLevelRaw, Field<BigInteger> xpPerLevel, Field<BigInteger> unspentPoints,
            Field<BigInteger> usedPoints, RawJson originalObject) implements ProgressSource {
        public Progress { Objects.requireNonNull(xpTotalRaw); Objects.requireNonNull(xpWithinLevelRaw);
            Objects.requireNonNull(xpPerLevel); Objects.requireNonNull(unspentPoints); Objects.requireNonNull(usedPoints); Objects.requireNonNull(originalObject); }
        public boolean hasAnyNumericProperty() { return xpTotalRaw.state() != LifestyleMinPolicy.FieldState.MISSING
                || xpWithinLevelRaw.state() != LifestyleMinPolicy.FieldState.MISSING || xpPerLevel.state() != LifestyleMinPolicy.FieldState.MISSING
                || unspentPoints.state() != LifestyleMinPolicy.FieldState.MISSING || usedPoints.state() != LifestyleMinPolicy.FieldState.MISSING; }
        public Optional<FocusProgress> observedNumbers() {
            if (!(xpTotalRaw.present() && xpWithinLevelRaw.present() && xpPerLevel.present() && unspentPoints.present() && usedPoints.present())) { return Optional.empty(); }
            return Optional.of(new FocusProgress(xpTotalRaw.value(), xpWithinLevelRaw.value(), xpPerLevel.value(), unspentPoints.value(), usedPoints.value()));
        }
    }
    public record NativeResult(String step, Boolean privateBuild, Boolean advertised, Boolean readOnly, Boolean policyScoped,
            String snapshotId, String episodeRunId, String targetKey, String status, Field<Boolean> nativeLegal,
            BigInteger scannedRows, String targetLifestyleKey, Field<ProgressSource> progress) {
        public NativeResult { Objects.requireNonNull(nativeLegal); Objects.requireNonNull(progress); }
    }
    public record Response(String type, BigInteger protocolVersion, String requestId, Boolean ok, NativeResult result) { }
    public static final class ResponseEvidence {
        private final RawJson original;
        private final Response response;
        ResponseEvidence(RawJson original, Response response) { this.original = original; this.response = response; }
        public RawJson original() { return original; }
        public Response response() { return response; }
        @Override public boolean equals(Object other) { return other instanceof ResponseEvidence value && original.equals(value.original) && Objects.equals(response, value.response); }
        @Override public int hashCode() { return Objects.hash(original, response); }
    }
    public record Input(Target target, String expectedRequestId, NativeSourceFrame sourceFrame,
            NativeSourceFrame independentAfterFrame, ResponseEvidence response) {
        public Input { Objects.requireNonNull(target); Objects.requireNonNull(sourceFrame); Objects.requireNonNull(independentAfterFrame); Objects.requireNonNull(response); }
    }
    public enum Issue {
        PAUSED_FOCUS_FRAME_DRIFT_OR_INVALID, NATIVE_FOCUS_QUERY_FAILED, NATIVE_FOCUS_BINDING_INVALID,
        NATIVE_FOCUS_UNAVAILABLE_PROMOTED, NATIVE_FOCUS_SOURCE_UNAVAILABLE, NATIVE_FOCUS_LEGALITY_UNTYPED,
        TARGET_LIFESTYLE_PROGRESS_UNTYPED, TARGET_PROGRESS_UNKNOWN_PROMOTED, TARGET_PROGRESS_VALUES_INVALID,
        PAUSED_FOCUS_PUBLIC_FRAME_DRIFT;
        public String wire() { return name().toLowerCase(java.util.Locale.ROOT); }
    }
    public sealed interface Outcome permits Red, ProgressUnavailable, Observed { }
    public record Red(Issue issue, String nativeStatus) implements Outcome {
        public Red { Objects.requireNonNull(issue); StrictJson.require((issue == Issue.NATIVE_FOCUS_SOURCE_UNAVAILABLE) == (nativeStatus != null), "only native source unavailable carries native_status"); }
    }
    public record ProgressUnavailable(Target target, boolean nativeLegal) implements Outcome { public ProgressUnavailable { Objects.requireNonNull(target); } }
    public record Observed(Target target, boolean nativeLegal, FocusProgress progress, RawJson originalProgress, NativeSourceFrame sourceFrame) implements Outcome {
        public Observed { Objects.requireNonNull(target); Objects.requireNonNull(progress); Objects.requireNonNull(originalProgress); Objects.requireNonNull(sourceFrame);
            StrictJson.require(progress.valid() && validFrame(sourceFrame), "observed focus needs exact valid getters and bound source"); }
    }
    private static Red red(Issue issue) { return new Red(issue, null); }
    public static Outcome parse(Input input) {
        Objects.requireNonNull(input); NativeSourceFrame source = input.sourceFrame();
        if (!validFrame(source) || !Boolean.TRUE.equals(input.independentAfterFrame().paused())
                || !source.equals(input.independentAfterFrame())) { return red(Issue.PAUSED_FOCUS_FRAME_DRIFT_OR_INVALID); }
        Response response = input.response().response();
        if (input.expectedRequestId() == null || input.expectedRequestId().isEmpty() || response == null
                || !"command_result".equals(response.type()) || !BigInteger.ONE.equals(response.protocolVersion())
                || !input.expectedRequestId().equals(response.requestId()) || !Boolean.TRUE.equals(response.ok())) { return red(Issue.NATIVE_FOCUS_QUERY_FAILED); }
        NativeResult result = response.result(); Target target = input.target();
        if (result == null || !target.step().equals(result.step()) || !Boolean.TRUE.equals(result.privateBuild())
                || !Boolean.FALSE.equals(result.advertised()) || !Boolean.TRUE.equals(result.readOnly()) || !Boolean.TRUE.equals(result.policyScoped())
                || !Objects.equals(source.snapshotId(), result.snapshotId()) || !Objects.equals(source.episodeRunId(), result.episodeRunId())
                || !target.key().equals(result.targetKey())) { return red(Issue.NATIVE_FOCUS_BINDING_INVALID); }
        if (result.status() != null && result.status().startsWith("unavailable_")) {
            return result.nativeLegal().state() != LifestyleMinPolicy.FieldState.MISSING || result.progress().state() != LifestyleMinPolicy.FieldState.MISSING
                    ? red(Issue.NATIVE_FOCUS_UNAVAILABLE_PROMOTED) : new Red(Issue.NATIVE_FOCUS_SOURCE_UNAVAILABLE, result.status());
        }
        boolean legal = "observed_native_legal".equals(result.status());
        if (!(legal || "observed_native_illegal".equals(result.status())) || !result.nativeLegal().is(legal)
                || result.scannedRows() == null || result.scannedRows().signum() <= 0 || !target.lifestyle().equals(result.targetLifestyleKey())) {
            return red(Issue.NATIVE_FOCUS_LEGALITY_UNTYPED);
        }
        if (!result.progress().present()) { return red(Issue.TARGET_LIFESTYLE_PROGRESS_UNTYPED); }
        ProgressSource progress = result.progress().value();
        if ("unavailable".equals(progress.presence())) {
            return !"target_native_getters_unavailable".equals(progress.reason()) || progress.hasAnyNumericProperty()
                    ? red(Issue.TARGET_PROGRESS_UNKNOWN_PROMOTED) : new ProgressUnavailable(target, legal);
        }
        Optional<FocusProgress> numbers = progress.observedNumbers();
        if (!"present".equals(progress.presence()) || !"exact_native_getters".equals(progress.source())
                || numbers.isEmpty() || !numbers.orElseThrow().valid()) { return red(Issue.TARGET_PROGRESS_VALUES_INVALID); }
        return new Observed(target, legal, numbers.orElseThrow(), progress.originalObject(), source);
    }
    public static boolean validFrame(NativeSourceFrame frame) {
        return Boolean.TRUE.equals(frame.paused()) && frame.nativeRevision() != null && frame.nativeRevision().signum() > 0
                && ("native:" + frame.nativeRevision()).equals(frame.snapshotId()) && frame.dateRaw() != null && frame.dateRaw().signum() >= 0
                && frame.controllerFullId() != null && frame.controllerFullId().signum() > 0 && frame.episodeRunId() != null
                && frame.episodeRunId().startsWith("native-" + frame.controllerFullId() + "-");
    }
    /** Explicit conversion between the existing semantic actor and this wire's played_character_id. */
    public static NativeSourceFrame frame(SemanticSnapshot snapshot) {
        Objects.requireNonNull(snapshot);
        return new NativeSourceFrame(snapshot.snapshotId(), snapshot.episodeRunId(), snapshot.nativeRevision(), snapshot.dateRaw(),
                snapshot.playedCharacter() == null ? null : snapshot.playedCharacter().characterId(), snapshot.paused());
    }
    /** The original post-read query guard; an observation cannot escape public revision/map readiness drift. */
    public static Outcome finishQuery(Outcome parsed, BigInteger startingPublicRevision, BigInteger endingPublicRevision, Boolean endingMapReady) {
        Objects.requireNonNull(parsed);
        return !Objects.equals(startingPublicRevision, endingPublicRevision) || !Boolean.TRUE.equals(endingMapReady)
                ? red(Issue.PAUSED_FOCUS_PUBLIC_FRAME_DRIFT) : parsed;
    }
    public static Field<LifestyleMinPolicy.FocusObservation> forFirstFocus(Outcome outcome) {
        Objects.requireNonNull(outcome);
        return switch (outcome) {
            case Red ignored -> Field.nullValue();
            case ProgressUnavailable unavailable -> Field.of(new LifestyleMinPolicy.FocusObservation("target_progress_unavailable", Field.of(unavailable.nativeLegal()),
                    unavailable.target().key(), unavailable.target().lifestyle(), "unavailable", Field.missing()));
            case Observed observed -> Field.of(new LifestyleMinPolicy.FocusObservation("observed", Field.of(observed.nativeLegal()),
                    observed.target().key(), observed.target().lifestyle(), "present", Field.of(observed.progress())));
        };
    }
    public static LifestyleMinPolicy.FirstFocusDecision chooseFirstFocus(Outcome wealth, Outcome martial,
            Field<LifestyleMinPolicy.Traits> traits, boolean atPeace) {
        Objects.requireNonNull(wealth); Objects.requireNonNull(martial); Objects.requireNonNull(traits);
        if (wealth instanceof Observed left && martial instanceof Observed right) {
            StrictJson.require(left.target() == Target.WEALTH && right.target() == Target.MARTIAL
                    && left.sourceFrame().equals(right.sourceFrame()), "focus alternatives must belong to one actual actor frame");
        }
        return LifestyleMinPolicy.chooseFirstFocus(new LifestyleMinPolicy.FirstFocusRequest(forFirstFocus(wealth), forFirstFocus(martial), traits, atPeace));
    }
    public enum ResearchStatus { OBSERVED, NATIVE_UNAVAILABLE, RED }
    public record ResearchView(ResearchStatus status, String nativeStatus, String basis, Issue issue, RawJson progress) {
        public ResearchView { Objects.requireNonNull(status);
            StrictJson.require((status == ResearchStatus.RED) == (issue != null), "research red must retain parser issue");
            StrictJson.require((status == ResearchStatus.OBSERVED) == (progress != null), "research progress is present only for observed getters"); }
    }
    /** Only the existing research consumer's post-parser projection; its independent outer checks stay upstream. */
    public static ResearchView researchAfterParser(Outcome outcome, String originalNativeStatus) {
        Objects.requireNonNull(outcome);
        return switch (outcome) {
            case Observed observed -> new ResearchView(ResearchStatus.OBSERVED, originalNativeStatus, null, null, observed.originalProgress());
            case ProgressUnavailable ignored -> new ResearchView(ResearchStatus.NATIVE_UNAVAILABLE, "target_progress_unavailable", "same_frame_exact_target_getters_unavailable", null, null);
            case Red red -> new ResearchView(ResearchStatus.RED, red.nativeStatus() == null ? originalNativeStatus : red.nativeStatus(), null, red.issue(), null);
        };
    }
}
