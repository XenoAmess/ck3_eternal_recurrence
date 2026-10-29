package org.xar.ck3.control.wave3.development.constructionquery;

import java.math.BigInteger;
import java.util.Objects;
import org.xar.ck3.control.wave2.development.constructionscene.ConstructionSceneModel.Field;
import org.xar.ck3.control.wave2.development.constructionscene.ConstructionSceneModel.Presence;
import org.xar.ck3.control.wave2.development.constructionscene.ConstructionSceneModel.Snapshot;
import org.xar.ck3.control.wave2.development.constructionvalue.ConstructionValueModel;
import org.xar.ck3.control.wave2.development.constructionvalue.ConstructionValueModel.Build;
import org.xar.ck3.control.wave2.development.constructionvalue.ConstructionValueModel.Candidate;

/** Declared immutable observations from the original single read provider, never a native submit port. */
public final class ConstructionQueryModel {
    private ConstructionQueryModel() { }
    public record Frame(Snapshot core, Field<Boolean> mapReady, Field<Boolean> actorAlive, Field<Integer> armyCount,
            Presence activeEvent, Presence pendingInteraction, Field<String> episode) {
        public Frame {
            Objects.requireNonNull(core); Objects.requireNonNull(mapReady); Objects.requireNonNull(actorAlive); Objects.requireNonNull(armyCount);
            Objects.requireNonNull(activeEvent); Objects.requireNonNull(pendingInteraction); Objects.requireNonNull(episode);
        }
    }
    /** Exact version/hash copied identity; this is metadata validation rather than physical source qualification. */
    public record SourceBuild(Build build, String sha256) {
        public SourceBuild {
            Objects.requireNonNull(build); Objects.requireNonNull(sha256);
            if (!sha256.equals(expectedSha(build))) { throw new IllegalArgumentException("private nonwar source lacks a frozen exact native build"); }
        }
    }
    public static String expectedSha(Build build) {
        return switch (build) {
            case V11906 -> "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";
            case V12002 -> "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D";
            case V12003 -> "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6";
            case V12004 -> "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
            case UNSUPPORTED -> throw new IllegalArgumentException("private nonwar source lacks a frozen exact native build");
        };
    }
    public record SourceWorld(Field<String> status, Field<BigInteger> revision, Field<BigInteger> dateRaw,
            Field<BigInteger> actorId, Field<Boolean> nativeFinalLegalityEvaluated, Field<Boolean> nativeCostEvaluated,
            ConstructionValueModel.World values) {
        public SourceWorld {
            Objects.requireNonNull(status); Objects.requireNonNull(revision); Objects.requireNonNull(dateRaw); Objects.requireNonNull(actorId);
            Objects.requireNonNull(nativeFinalLegalityEvaluated); Objects.requireNonNull(nativeCostEvaluated); Objects.requireNonNull(values);
        }
    }
    public record Probe(Field<Boolean> advertised, Field<BigInteger> revision, Field<BigInteger> dateRaw,
            Field<BigInteger> proofEpoch, Field<SourceWorld> world) {
        public Probe { Objects.requireNonNull(advertised); Objects.requireNonNull(revision); Objects.requireNonNull(dateRaw); Objects.requireNonNull(proofEpoch); Objects.requireNonNull(world); }
    }
    /** A returned mapping may be a source-red admission result, not a missing transport packet. */
    public sealed interface ReturnedResult permits NativeResult, NativeAdmissionMismatch { }
    public enum AdmissionField { STEP, ACCEPTED }
    public record NativeAdmissionMismatch(AdmissionField field) implements ReturnedResult {
        public NativeAdmissionMismatch { Objects.requireNonNull(field); }
    }
    public record NativeResult(Field<String> step, Field<Boolean> accepted, Field<Probe> probe) implements ReturnedResult {
        public NativeResult { Objects.requireNonNull(step); Objects.requireNonNull(accepted); Objects.requireNonNull(probe); }
    }
    public record Envelope(Field<String> type, Field<BigInteger> protocolVersion, Field<String> requestId,
            Field<Boolean> ok, Field<ReturnedResult> result) {
        public Envelope { Objects.requireNonNull(type); Objects.requireNonNull(protocolVersion); Objects.requireNonNull(requestId); Objects.requireNonNull(ok); Objects.requireNonNull(result); }
    }
    public record Observation(Frame starting, Frame ending, Envelope envelope, BigInteger expectedRevision,
            String requestId, boolean materialReceipt, boolean wartimeObservation, SourceBuild build) {
        public Observation {
            Objects.requireNonNull(starting); Objects.requireNonNull(ending); Objects.requireNonNull(envelope);
            Objects.requireNonNull(expectedRevision); Objects.requireNonNull(requestId); Objects.requireNonNull(build);
        }
    }
    public enum Rejection {
        SOURCE_MODES("construction source modes cannot be combined"),
        UNBOUND_FRAME("construction trial lacks a stable admitted paused actor frame"),
        NATIVE_READ_RETURN("g2_player_construction_view_probe_v1 native result missing/rejected; keep action pending if submitted");
        private final String wire;
        Rejection(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }
    public enum ReadyKind { MATERIAL_SOURCE, SELECTED, NO_LEGAL_BUDGETED_BUILDING, EVIDENCE_INSUFFICIENT }
    public sealed interface Result permits Rejected, SourceRed, Ready { }
    public record Rejected(Rejection reason) implements Result { public Rejected { Objects.requireNonNull(reason); } }
    public record SourceRed() implements Result { }
    public record Ready(ReadyKind kind, Candidate candidate) implements Result {
        public Ready {
            Objects.requireNonNull(kind);
            if ((kind == ReadyKind.SELECTED) != (candidate != null)) { throw new IllegalArgumentException("only selected source carries an authored candidate"); }
        }
    }
}
