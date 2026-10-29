package org.xar.ck3.control.governance.lifestylesource;

import java.math.BigInteger;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.StrictJson;

/** Copied optional source diagnostics and independent output facts. None grants native parent legality. */
public final class LifestyleSourceFacts {
    private LifestyleSourceFacts() { }
    public enum Presence { MISSING, NULL }
    public enum Truth {
        UNKNOWN, KNOWN_FALSE, KNOWN_TRUE;
        public static Truth of(Boolean value) { return value == null ? UNKNOWN : value ? KNOWN_TRUE : KNOWN_FALSE; }
    }
    public enum Status {
        DECODED("decoded"), INVALID("invalid");
        private final String wire;
        Status(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }
    public enum CaptureScope {
        UNAVAILABLE("unavailable"), OWNED_MEMORY_FIXTURE("owned_memory_fixture"), ACTUAL_APPLICATION_QUERY("actual_application_query");
        private final String wire;
        CaptureScope(String wire) { this.wire = wire; }
        public String wire() { return wire; }
        public static CaptureScope from(String wire) {
            for (var value : values()) if (value.wire.equals(wire)) return value;
            throw new IllegalArgumentException("inputs:capture_scope_not_admitted");
        }
    }
    public enum ResultSource {
        UNAVAILABLE("unavailable"), CLOSED_PURE_TARGET_SOURCE("closed_pure_target_source"), NATURAL_ORIGINAL_ONCE("natural_original_once");
        private final String wire;
        ResultSource(String wire) { this.wire = wire; }
        public String wire() { return wire; }
        public static ResultSource from(String wire) {
            for (var value : values()) if (value.wire.equals(wire)) return value;
            throw new IllegalArgumentException("lane:result_source_not_admitted");
        }
    }
    /** Existing caller values only. An unbound diagnostic cannot earn actual-response credit. */
    public record Binding(Optional<String> snapshotIdentity, Optional<BigInteger> nativeRevision,
            Optional<Integer> dateRaw, Optional<BigInteger> playedCharacterId, Optional<String> targetKey) {
        public Binding {
            snapshotIdentity = Objects.requireNonNull(snapshotIdentity);
            nativeRevision = Objects.requireNonNull(nativeRevision);
            dateRaw = Objects.requireNonNull(dateRaw);
            playedCharacterId = Objects.requireNonNull(playedCharacterId);
            targetKey = Objects.requireNonNull(targetKey);
            snapshotIdentity.ifPresent(value -> { Objects.requireNonNull(value); });
            nativeRevision.ifPresent(value -> range(value, 64));
            playedCharacterId.ifPresent(value -> range(value, 32));
            targetKey.ifPresent(value -> { Objects.requireNonNull(value); });
        }
        public static Binding exact(String nativeSnapshotId, BigInteger nativeRevision, int dateRaw,
                BigInteger playedCharacterId, Optional<String> targetKey) {
            return new Binding(Optional.of(nativeSnapshotId), Optional.of(nativeRevision), Optional.of(dateRaw),
                    Optional.of(playedCharacterId), targetKey);
        }
        public static Binding unbound() { return new Binding(Optional.empty(), Optional.empty(), Optional.empty(), Optional.empty(), Optional.empty()); }
        public boolean completeFrame() { return snapshotIdentity.isPresent() && nativeRevision.isPresent() && dateRaw.isPresent() && playedCharacterId.isPresent(); }
    }
    /** Original native packet's exact JSON type domain, immutable and distinct from encoded fact JSON. */
    public record CopiedPacket(byte[] canonicalNativeJson) {
        public CopiedPacket {
            canonicalNativeJson = Objects.requireNonNull(canonicalNativeJson).clone();
            StrictJson.require(canonicalNativeJson.length > 0 && canonicalNativeJson.length <= StrictJson.INPUT_MAX_BYTES, "bounded copied source packet");
        }
        @Override public byte[] canonicalNativeJson() { return canonicalNativeJson.clone(); }
        @Override public boolean equals(Object other) { return other instanceof CopiedPacket value && Arrays.equals(canonicalNativeJson, value.canonicalNativeJson); }
        @Override public int hashCode() { return Arrays.hashCode(canonicalNativeJson); }
    }
    public record SourceFrame(String snapshotIdentity, BigInteger nativeRevision, Optional<Integer> dateRaw,
            Optional<BigInteger> playedCharacterId, BigInteger moduleBase, Optional<BigInteger> frameIdentity,
            Optional<BigInteger> querySequence, BigInteger proofEpoch, BigInteger publicRevision, boolean callerSnapshotConfirmed) {
        public SourceFrame {
            Objects.requireNonNull(snapshotIdentity); range(nativeRevision, 64); Objects.requireNonNull(dateRaw);
            playedCharacterId = Objects.requireNonNull(playedCharacterId); playedCharacterId.ifPresent(value -> range(value, 32));
            range(moduleBase, 64); frameIdentity = Objects.requireNonNull(frameIdentity); frameIdentity.ifPresent(value -> range(value, 64));
            querySequence = Objects.requireNonNull(querySequence); querySequence.ifPresent(value -> range(value, 64));
            range(proofEpoch, 64); range(publicRevision, 64);
        }
    }
    public sealed interface PredicateResult permits PredicateAbsent, PredicateInvalid, PredicateDecoded { }
    public record PredicateAbsent(Presence presence) implements PredicateResult { public PredicateAbsent { Objects.requireNonNull(presence); } }
    public record PredicateInvalid(String reason) implements PredicateResult { public PredicateInvalid { StrictJson.text(reason); } }
    public record PredicateDecoded(String targetKey, SourceFrame frame, Truth value, String unavailableReason,
            Truth prefixValue, Optional<Truth> tailValue, CopiedPacket original) implements PredicateResult {
        public PredicateDecoded {
            Objects.requireNonNull(targetKey); Objects.requireNonNull(frame); Objects.requireNonNull(value);
            Objects.requireNonNull(unavailableReason); Objects.requireNonNull(prefixValue);
            tailValue = Objects.requireNonNull(tailValue); Objects.requireNonNull(original);
        }
        public boolean wholeParentLegalityDecoded() { return false; }
    }
    public record Outputs(Optional<Integer> rawU8, Optional<Integer> rawU16, Optional<BigInteger> qword0, Optional<BigInteger> qword1) {
        public Outputs {
            rawU8 = Objects.requireNonNull(rawU8); rawU16 = Objects.requireNonNull(rawU16);
            qword0 = Objects.requireNonNull(qword0); qword1 = Objects.requireNonNull(qword1);
            rawU8.ifPresent(value -> { StrictJson.require(value >= 0 && value <= 255, "returned u8 range"); });
            rawU16.ifPresent(value -> { StrictJson.require(value >= 0 && value <= 65535, "returned u16 range"); });
            qword0.ifPresent(value -> range(value, 64)); qword1.ifPresent(value -> range(value, 64));
        }
        public static Outputs unknown() { return new Outputs(Optional.empty(), Optional.empty(), Optional.empty(), Optional.empty()); }
        public boolean empty() { return rawU8.isEmpty() && rawU16.isEmpty() && qword0.isEmpty() && qword1.isEmpty(); }
    }
    public record LaneFacts(Optional<Status> status, boolean rawTargetReady, boolean sourceValueReady, Outputs outputs,
            Optional<ResultSource> resultSource, Optional<String> unavailableReason,
            boolean actualTargetSourceClaimReady, boolean actualSourceValueReady) {
        public LaneFacts {
            status = Objects.requireNonNull(status); Objects.requireNonNull(outputs);
            resultSource = Objects.requireNonNull(resultSource); unavailableReason = Objects.requireNonNull(unavailableReason);
            StrictJson.require(sourceValueReady || outputs.empty(), "unqualified outputs must remain unknown");
            StrictJson.require(!actualTargetSourceClaimReady || rawTargetReady, "actual target requires copied raw target");
            StrictJson.require(!actualSourceValueReady || sourceValueReady && actualTargetSourceClaimReady, "actual source requires independently qualified output");
        }
    }
    public record Lanes(LaneFacts descriptorAl, LaneFacts rootKindAx, LaneFacts rootMaskQwords, LaneFacts finalC8Al) {
        public Lanes { Objects.requireNonNull(descriptorAl); Objects.requireNonNull(rootKindAx); Objects.requireNonNull(rootMaskQwords); Objects.requireNonNull(finalC8Al); }
        public List<LaneFacts> all() { return List.of(descriptorAl, rootKindAx, rootMaskQwords, finalC8Al); }
    }
    public sealed interface FrontierResult permits FrontierAbsent, FrontierInvalid, FrontierDecoded { }
    public record FrontierAbsent(Presence presence) implements FrontierResult { public FrontierAbsent { Objects.requireNonNull(presence); } }
    public record FrontierInvalid(String reason, Lanes lanes) implements FrontierResult {
        public FrontierInvalid { StrictJson.text(reason); Objects.requireNonNull(lanes); }
    }
    public record FrontierDecoded(String targetKey, SourceFrame frame, CaptureScope captureScope, boolean copiedInputBindingReady,
            boolean actualApplicationResponseBound, Lanes lanes, CopiedPacket original) implements FrontierResult {
        public FrontierDecoded {
            Objects.requireNonNull(targetKey); Objects.requireNonNull(frame); Objects.requireNonNull(captureScope);
            Objects.requireNonNull(lanes); Objects.requireNonNull(original);
        }
        public boolean wholeParentLegalityDecoded() { return false; }
    }
    private static void range(BigInteger value, int bits) {
        StrictJson.require(value != null && value.signum() >= 0 && value.bitLength() <= bits, "unsigned exact source range");
    }
}
