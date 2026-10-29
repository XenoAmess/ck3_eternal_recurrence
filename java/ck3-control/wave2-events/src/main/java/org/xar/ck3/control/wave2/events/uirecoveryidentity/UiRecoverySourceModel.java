package org.xar.ck3.control.wave2.events.uirecoveryidentity;

import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.ChoiceIdentity;
import org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.Field;

/** Stable widget identity is distinct from a live window/token and from a reviewed business effect. */
public final class UiRecoverySourceModel {
    private UiRecoverySourceModel() { }
    public sealed interface RelativeAddress permits NumericAddress, SymbolicAddress { }
    public record NumericAddress(BigInteger value) implements RelativeAddress {
        public NumericAddress {
            Objects.requireNonNull(value);
            if (value.signum() <= 0 || value.bitLength() > 64) { throw new IllegalArgumentException("positive uint64 RVA required"); }
        }
    }
    public record SymbolicAddress(String value) implements RelativeAddress {
        public SymbolicAddress { Objects.requireNonNull(value); if (value.isEmpty()) { throw new IllegalArgumentException("nonempty symbolic RVA"); } }
    }
    public record Callback(RelativeAddress vtable, RelativeAddress function) {
        public Callback { Objects.requireNonNull(vtable); Objects.requireNonNull(function); }
    }
    public record DisplayedChoice(ChoiceIdentity identity, Optional<String> label, Optional<String> role) {
        public DisplayedChoice { Objects.requireNonNull(identity); Objects.requireNonNull(label); Objects.requireNonNull(role); }
    }
    public record CatalogueChoice(Field<ChoiceIdentity> choiceId, String runtimeName, RelativeAddress widgetVtable,
            Field<String> role, List<Callback> callbacks) {
        public CatalogueChoice {
            Objects.requireNonNull(choiceId); Objects.requireNonNull(runtimeName); Objects.requireNonNull(widgetVtable);
            Objects.requireNonNull(role); callbacks = List.copyOf(callbacks);
            if (runtimeName.isEmpty() || callbacks.isEmpty()) { throw new IllegalArgumentException("runtime name and callbacks required"); }
        }
    }
    public record SourceIdentity(String gameExeSha256, Optional<String> backendSha256, String nativeAdapterId,
            String rootRuntimeName, String rootType, RelativeAddress rootVtable, List<CatalogueChoice> catalogue) {
        public SourceIdentity {
            Objects.requireNonNull(gameExeSha256); Objects.requireNonNull(backendSha256); Objects.requireNonNull(nativeAdapterId);
            Objects.requireNonNull(rootRuntimeName); Objects.requireNonNull(rootType); Objects.requireNonNull(rootVtable);
            catalogue = List.copyOf(catalogue);
            if (nativeAdapterId.isEmpty() || rootRuntimeName.isEmpty() || rootType.isEmpty()) {
                throw new IllegalArgumentException("stable source runtime identity must be nonempty");
            }
        }
    }
    public record Input(String backendSha256, SourceIdentity source, List<DisplayedChoice> displayedChoices) {
        public Input { Objects.requireNonNull(backendSha256); Objects.requireNonNull(source); displayedChoices = List.copyOf(displayedChoices); }
    }
    public sealed interface Projection permits Ready, Unavailable { }
    public record Ready(Input input) implements Projection { public Ready { Objects.requireNonNull(input); } }
    public record Unavailable(String reason) implements Projection { public Unavailable { Objects.requireNonNull(reason); } }
    public record NormalizedChoice(String runtimeName, RelativeAddress widgetVtable, Optional<String> role,
            Optional<String> label, List<Callback> callbacks) {
        public NormalizedChoice {
            Objects.requireNonNull(runtimeName); Objects.requireNonNull(widgetVtable); Objects.requireNonNull(role);
            Objects.requireNonNull(label); callbacks = List.copyOf(callbacks);
        }
    }
    public record StableSource(String gameExeSha256, String backendSha256, String nativeAdapterId,
            String rootRuntimeName, String rootType, RelativeAddress rootVtable, List<NormalizedChoice> catalogue) {
        public StableSource {
            Objects.requireNonNull(gameExeSha256); Objects.requireNonNull(backendSha256); Objects.requireNonNull(nativeAdapterId);
            Objects.requireNonNull(rootRuntimeName); Objects.requireNonNull(rootType); Objects.requireNonNull(rootVtable);
            catalogue = List.copyOf(catalogue);
        }
    }
    public record Fingerprint(String sourceKey, StableSource stableSource) {
        public Fingerprint {
            Objects.requireNonNull(sourceKey); Objects.requireNonNull(stableSource);
            if (!sourceKey.matches("[0-9a-f]{64}")) { throw new IllegalArgumentException("source key SHA256"); }
        }
        public boolean observedUiRecoveryVerified() { return false; }
        public boolean businessEffectKnown() { return false; }
        public boolean semanticOptimal() { return false; }
        public boolean replayAllowed() { return false; }
    }
}
