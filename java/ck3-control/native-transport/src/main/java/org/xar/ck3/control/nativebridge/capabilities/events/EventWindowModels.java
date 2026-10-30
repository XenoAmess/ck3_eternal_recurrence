package org.xar.ck3.control.nativebridge.capabilities.events;

import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.events.GuiAvailabilityObservation;

/** Exact copied event presentation. Icon indicators never claim a complete effect preview. */
public final class EventWindowModels {
    private EventWindowModels() { }
    public enum Build {
        TOURS("1.19.0.6", "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86", "module+0x570F7B8->+0x10", "0x40B1D30"),
        CROZIER2("1.20.0.2", "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D", "module+0x5C6A520->+0x10", "0x44BC408"),
        CROZIER3("1.20.0.3", "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6", "module+0x5C6A520->+0x10", "0x44BC408"),
        CROZIER4("1.20.0.4", "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518", "module+0x5C6A520->+0x10", "0x44BC418");
        private final String version, sha256, root, vtable;
        Build(String version, String sha256, String root, String vtable) { this.version=version; this.sha256=sha256; this.root=root; this.vtable=vtable; }
        public String version() { return version; }
        public String sha256() { return sha256; }
        public String root() { return root; }
        public String vtable() { return vtable; }
        public String backend() { return "ck3-"+version+"-native-event-window-v1"; }
        public String coverage() { return "played-character-event-icon-indicators-"+version+"-v1"; }
        public boolean numericScopes() { return this==CROZIER3 || this==CROZIER4; }
    }
    public record Binding(Build build, BigInteger nativeRevision, int dateRaw, int eventInstanceId) {
        public Binding {
            Objects.requireNonNull(build); Objects.requireNonNull(nativeRevision);
            if (nativeRevision.signum()<=0 || nativeRevision.bitLength()>64 || eventInstanceId<=0)
                throw new IllegalArgumentException("exact positive native revision/event instance required");
        }
    }
    public record Readiness(boolean definitionIdentity, boolean rootScope, boolean savedScopes,
            boolean optionPresentation, boolean effectIndicators, boolean effectPreview, boolean semanticDecision) { }
    public record Definition(String key, int calculatedId, int runtimeOrdinal) { public Definition { Objects.requireNonNull(key); } }
    public sealed interface Context permits Available, Unavailable {
        Binding binding(); int windowMatchCount(); Readiness readiness(); RawJson original();
    }
    public record Available(Binding binding, Definition definition, Scope rootScope, List<SavedScope> savedScopes,
            List<Option> options, Readiness readiness, RawJson original) implements Context {
        public Available {
            Objects.requireNonNull(binding); Objects.requireNonNull(definition); Objects.requireNonNull(rootScope);
            savedScopes=List.copyOf(savedScopes); options=List.copyOf(options); Objects.requireNonNull(readiness); Objects.requireNonNull(original);
        }
        @Override public int windowMatchCount() { return 1; }
        /** The caller must preserve a disabled first displayed option; this does not select another row. */
        public Optional<Option> firstDisplayed() { return options.stream().findFirst(); }
    }
    /** A retained partial definition is diagnostic only: there are no scopes or options on this branch. */
    public record Unavailable(Binding binding, int windowMatchCount, String reason, Optional<Definition> partialDefinition,
            Readiness readiness, RawJson original) implements Context {
        public Unavailable {
            Objects.requireNonNull(binding); Objects.requireNonNull(reason); Objects.requireNonNull(partialDefinition);
            Objects.requireNonNull(readiness); Objects.requireNonNull(original);
        }
    }
    public record SavedScope(String name, int identifier, Scope scope) { public SavedScope { Objects.requireNonNull(name); Objects.requireNonNull(scope); } }
    public record Scope(int rawTypeIndex, String typeKey, int subtype, Identity identity, Optional<NumericValue> numericValue) {
        public Scope { Objects.requireNonNull(typeKey); Objects.requireNonNull(identity); Objects.requireNonNull(numericValue); }
    }
    public sealed interface Identity permits CharacterIdentity, TitleIdentity, FactionIdentity, UnavailableIdentity { }
    public record CharacterIdentity(int characterId) implements Identity { }
    public record TitleIdentity(int titleId) implements Identity { }
    public record FactionIdentity(int factionId) implements Identity { }
    public enum IdentityReason {
        CHARACTER_SCOPE_IDENTITY_UNAVAILABLE, CHARACTER_SCOPE_IS_NULL, LANDED_TITLE_SCOPE_IS_NULL,
        FACTION_SCOPE_IDENTITY_UNAVAILABLE, GENERIC_SCOPE_PAYLOAD_IDENTITY_NOT_CLOSED;
        public String wire() { return name().toLowerCase(java.util.Locale.ROOT); }
    }
    public record UnavailableIdentity(IdentityReason reason) implements Identity { public UnavailableIdentity { Objects.requireNonNull(reason); } }
    /** Decimal strings preserve the signed 64-bit fixed-point payload without a Number round trip. */
    public record NumericValue(String rawFixedPoint, String decimalValue, Optional<String> integerValue) {
        public NumericValue { Objects.requireNonNull(rawFixedPoint); Objects.requireNonNull(decimalValue); Objects.requireNonNull(integerValue); }
    }
    public record Option(int renderedIndex, int nativeOptionIndex, boolean enabled, boolean fallback, boolean cancel,
            String resolvedName, String unavailableReason, List<Indicator> indicators, GuiAvailabilityObservation guiAvailability) {
        public Option { Objects.requireNonNull(resolvedName); Objects.requireNonNull(unavailableReason); indicators=List.copyOf(indicators); Objects.requireNonNull(guiAvailability); }
        /** Legacy v1 callers supplied only raw flags; this constructor cannot assert stock GUI validity. */
        public Option(int renderedIndex,int nativeOptionIndex,boolean enabled,boolean fallback,boolean cancel,
                String resolvedName,String unavailableReason,List<Indicator> indicators) {
            this(renderedIndex,nativeOptionIndex,enabled,fallback,cancel,resolvedName,unavailableReason,indicators,
                    new GuiAvailabilityObservation.LegacyNotReported());
        }
        /** GUI result when observed; otherwise the prior raw-byte policy, with its basis retained. */
        public boolean selectionAllowed() { return guiAvailability.permitsSelectionWithRawFallback(enabled); }
        public BigInteger publicOptionNumber() { return BigInteger.valueOf(nativeOptionIndex).add(BigInteger.ONE); }
    }
    public enum Operation { ADD, REMOVE }
    public enum Direction { INCREASE, DECREASE }
    public enum StressKind { STRESS, FULFILLMENT, STRESS_AND_FULFILLMENT }
    public sealed interface Indicator permits TraitIndicator, StressIndicator, DeathIndicator, SchemeIndicator, UnknownIndicator { }
    public sealed interface TraitIdentity permits KnownTrait, UnavailableTrait { }
    public record KnownTrait(int nativeId, String key) implements TraitIdentity { public KnownTrait { Objects.requireNonNull(key); } }
    public record UnavailableTrait() implements TraitIdentity { }
    public record TraitIndicator(Operation operation, TraitIdentity trait) implements Indicator { public TraitIndicator { Objects.requireNonNull(operation); Objects.requireNonNull(trait); } }
    public record StressIndicator(StressKind kind, Direction direction, Optional<Direction> secondaryDirection,
            boolean affectedByTrait, boolean critical) implements Indicator {
        public StressIndicator { Objects.requireNonNull(kind); Objects.requireNonNull(direction); Objects.requireNonNull(secondaryDirection); }
    }
    public record DeathIndicator() implements Indicator { }
    public sealed interface SchemeIdentity permits KnownScheme, UnavailableScheme { }
    public record KnownScheme(String typeKey) implements SchemeIdentity { public KnownScheme { Objects.requireNonNull(typeKey); } }
    public record UnavailableScheme() implements SchemeIdentity { }
    public record SchemeIndicator(SchemeIdentity scheme) implements Indicator { public SchemeIndicator { Objects.requireNonNull(scheme); } }
    public record UnknownIndicator(int rawKind) implements Indicator { }
}
