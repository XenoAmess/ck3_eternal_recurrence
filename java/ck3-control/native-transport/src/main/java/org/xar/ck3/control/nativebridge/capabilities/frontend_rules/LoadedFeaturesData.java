package org.xar.ck3.control.nativebridge.capabilities.frontend_rules;

import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import static org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesData.*;

/** Effective flags and script keys are observable; ownership/entitlement remains provenance-unclosed. */
public final class LoadedFeaturesData {
    private LoadedFeaturesData() { }
    public enum UnavailableReason {
        UNSUPPORTED_BUILD, REQUIRES_APPLICATION_MAIN, REQUIRES_PAUSED, MAP_NOT_READY, FEATURE_ROOT_UNAVAILABLE,
        FEATURE_COUNTER_MISMATCH, FEATURE_REGISTRY_DRIFT, SCRIPT_DLC_SET_UNAVAILABLE, SCRIPT_DLC_KEY_INVALID, STATE_CHANGED, INTERNAL_ERROR;
        public String wire() { return name().toLowerCase(java.util.Locale.ROOT); }
        public static UnavailableReason require(String value) {
            for (UnavailableReason reason : values()) if (reason.wire().equals(value)) return reason;
            throw new IllegalArgumentException("unknown loaded-feature unavailability reason");
        }
    }
    public record Feature(int nativeIndex, long cstringId, String key, boolean enabled) {
        public Feature { require(nativeIndex >= 0 && nativeIndex < 44 && cstringId > 0 && cstringId <= 0xffff_ffffL, "feature native ID invalid"); stableKey(key); }
    }
    public sealed interface Flags permits AvailableFlags, UnavailableFlags { }
    public record AvailableFlags(List<Feature> items) implements Flags { public AvailableFlags { items = List.copyOf(items); require(items.size() == 44, "complete exact-build feature registry required"); } }
    public record UnavailableFlags(UnavailableReason reason) implements Flags { public UnavailableFlags { Objects.requireNonNull(reason); } }
    public sealed interface ScriptDlcs permits AvailableScriptDlcs, UnavailableScriptDlcs { }
    public record AvailableScriptDlcs(List<String> keys) implements ScriptDlcs {
        public AvailableScriptDlcs {
            keys = List.copyOf(keys); byte[] previous = null;
            for (String key : keys) {
                stableKey(key); byte[] next = key.getBytes(java.nio.charset.StandardCharsets.UTF_8);
                require(previous == null || java.util.Arrays.compareUnsigned(previous, next) < 0, "script DLC keys must be unique UTF-8 bytewise sorted"); previous = next;
            }
        }
    }
    public record UnavailableScriptDlcs(UnavailableReason reason) implements ScriptDlcs { public UnavailableScriptDlcs { Objects.requireNonNull(reason); } }
    public record Readiness(boolean effectiveFeatureFlagsReady, boolean scriptDlcKeysReady, boolean entitlementsReady,
            boolean sameFrameReady, boolean actionableReady) {
        public Readiness { require(!entitlementsReady && effectiveFeatureFlagsReady == actionableReady && scriptDlcKeysReady == actionableReady && sameFrameReady == actionableReady, "loaded-feature readiness contradiction"); }
    }
    public record Provenance(String featureRootSlotRva, String featureBitsetRva, String featureEnumTableRva, String scriptDlcSetRva, String backendId) {
        public Provenance { Objects.requireNonNull(featureRootSlotRva); Objects.requireNonNull(featureBitsetRva); Objects.requireNonNull(featureEnumTableRva); Objects.requireNonNull(scriptDlcSetRva); Objects.requireNonNull(backendId); }
    }
    public record Manifest(Build build, BigInteger nativeRevision, int dateRaw, Optional<UnavailableReason> unavailableReason,
            Flags flags, ScriptDlcs scriptDlcKeys, Readiness readiness, Provenance provenance) {
        public Manifest {
            Objects.requireNonNull(build); positiveU64(nativeRevision); Objects.requireNonNull(unavailableReason); Objects.requireNonNull(flags); Objects.requireNonNull(scriptDlcKeys); Objects.requireNonNull(readiness); Objects.requireNonNull(provenance);
            require(unavailableReason.isEmpty() == readiness.actionableReady(), "manifest availability/readiness contradiction");
            require((flags instanceof AvailableFlags) == readiness.actionableReady() && (scriptDlcKeys instanceof AvailableScriptDlcs) == readiness.actionableReady(), "manifest collection availability contradiction");
            if (unavailableReason.isPresent()) {
                require(flags instanceof UnavailableFlags value && value.reason() == unavailableReason.get(), "unavailable flags reason drift");
                require(scriptDlcKeys instanceof UnavailableScriptDlcs value && value.reason() == unavailableReason.get(), "unavailable DLC reason drift");
            }
        }
        public boolean entitlementsProven() { return false; }
    }
    public record Observation(Manifest manifest, BigInteger querySequence, String snapshotId, BigInteger revision,
            String sourceBackendId, Optional<String> episodeRunId) {
        public Observation { Objects.requireNonNull(manifest); positiveU64(querySequence); require(snapshotId != null && !snapshotId.isEmpty(), "snapshot source required"); require(revision != null && revision.signum() >= 0, "public revision required"); require(sourceBackendId != null && !sourceBackendId.isEmpty(), "source backend required"); Objects.requireNonNull(episodeRunId); }
    }
    public static void stableKey(String key) {
        require(key != null && !key.isEmpty() && key.codePoints().noneMatch(code -> code < 0x20)
                && key.getBytes(java.nio.charset.StandardCharsets.UTF_8).length <= 1024, "bounded stable native key required");
    }
}
