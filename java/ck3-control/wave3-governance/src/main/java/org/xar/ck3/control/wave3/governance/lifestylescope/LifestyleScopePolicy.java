package org.xar.ck3.control.wave3.governance.lifestylescope;

import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.governance.lifestyle.LifestyleMinPolicy;
import org.xar.ck3.control.governance.lifestyle.LifestyleMinPolicy.Field;
import org.xar.ck3.control.governance.lifestyle.LifestyleMinPolicy.Request;
import org.xar.ck3.control.wave2.development.constructionscene.ConstructionSceneModel.RootScope;
import org.xar.ck3.control.wave2.development.constructionscene.ConstructionSceneModel.RootScopeStatus;
import org.xar.ck3.control.wave2.development.constructionscene.ConstructionSceneModel.SceneInput;
import org.xar.ck3.control.wave2.development.constructionscene.ConstructionScenePolicy;

/** Existing LIFE wrappers and service selection, all using the unique shared same-frame root core. */
public final class LifestyleScopePolicy {
    public static final String ALL_LIFESTYLE_CAPABILITY = "game.state.private-lifestyle-all-frontier-v3";
    private LifestyleScopePolicy() { }

    public enum Mode {
        FEUDAL_PEACE(true, true), FEUDAL_LIFESTYLE(false, true), PLAYER_PERK(false, false);
        private final boolean requirePeace;
        private final boolean requireFeudal;
        Mode(boolean requirePeace, boolean requireFeudal) { this.requirePeace = requirePeace; this.requireFeudal = requireFeudal; }
    }
    /** Only assess can produce this immutable evidence; a caller cannot supply an admitted result. */
    public static final class Assessment {
        private final Mode mode;
        private final SceneInput source;
        private final RootScope root;
        private Assessment(Mode mode, SceneInput source, RootScope root) { this.mode = mode; this.source = source; this.root = root; }
        public Mode mode() { return mode; }
        public SceneInput source() { return source; }
        public RootScope root() { return root; }
    }
    public static Assessment assess(SceneInput source, Mode mode) {
        Objects.requireNonNull(source); Objects.requireNonNull(mode);
        return new Assessment(mode, source, ConstructionScenePolicy.sameFrameRootScope(source, mode.requirePeace, mode.requireFeudal));
    }
    public static Assessment sameFrameFeudalPeaceScope(SceneInput source) { return assess(source, Mode.FEUDAL_PEACE); }
    public static Assessment sameFrameFeudalLifestyleScope(SceneInput source) { return assess(source, Mode.FEUDAL_LIFESTYLE); }
    public static Assessment sameFramePlayerLifestylePerkScope(SceneInput source) { return assess(source, Mode.PLAYER_PERK); }

    public enum Cache { UNSET, ENABLED, DISABLED }
    public enum CapabilityStatus { NOT_QUERIED, UNAVAILABLE, AVAILABLE }
    public record CapabilityRead(CapabilityStatus status, List<String> bridgeCapabilities) {
        public CapabilityRead {
            Objects.requireNonNull(status); bridgeCapabilities = List.copyOf(bridgeCapabilities);
            bridgeCapabilities.forEach(StrictJson::text);
            StrictJson.require(status == CapabilityStatus.AVAILABLE || bridgeCapabilities.isEmpty(), "unavailable capability read has no observed list");
        }
        public static CapabilityRead notQueried() { return new CapabilityRead(CapabilityStatus.NOT_QUERIED, List.of()); }
    }
    public record ServiceInput(SceneInput scene, boolean initialFocusRequired, Cache cachedV3, CapabilityRead capabilityRead) {
        public ServiceInput {
            Objects.requireNonNull(scene); Objects.requireNonNull(cachedV3); Objects.requireNonNull(capabilityRead);
            boolean skipRead = initialFocusRequired || cachedV3 != Cache.UNSET;
            StrictJson.require(skipRead == (capabilityRead.status() == CapabilityStatus.NOT_QUERIED),
                    "capability read must follow the original opening/cache order");
        }
    }
    public record ServiceSelection(Assessment assessment, Cache nextCache, boolean capabilityReadUsed) {
        public ServiceSelection { Objects.requireNonNull(assessment); Objects.requireNonNull(nextCache); }
    }
    /** Pure extraction of service._player_lifestyle_perk_scope; provider I/O/cache ownership stays upstream. */
    public static ServiceSelection forService(ServiceInput input) {
        Objects.requireNonNull(input);
        if (input.initialFocusRequired()) {
            return new ServiceSelection(sameFrameFeudalLifestyleScope(input.scene()), input.cachedV3(), false);
        }
        Cache observed = input.cachedV3(); boolean read = observed == Cache.UNSET;
        if (read) {
            observed = input.capabilityRead().status() == CapabilityStatus.AVAILABLE
                    && input.capabilityRead().bridgeCapabilities().contains(ALL_LIFESTYLE_CAPABILITY) ? Cache.ENABLED : Cache.DISABLED;
        }
        return new ServiceSelection(assess(input.scene(), observed == Cache.ENABLED ? Mode.PLAYER_PERK : Mode.FEUDAL_LIFESTYLE), observed, read);
    }

    /** Existing formal consumer field projection; scene admission is never native action permission. */
    public static Request applyToMinimum(Request current, Assessment assessment, boolean allowWartimeInitialFocus) {
        Objects.requireNonNull(current); Objects.requireNonNull(assessment);
        StrictJson.require(current.snapshot().present(), "actual LIFE snapshot required before applying scene evidence");
        var life = current.snapshot().value(); var scene = assessment.source().snapshot();
        StrictJson.require(scene.nativeRevision().known() && life.nativeRevision().is(scene.nativeRevision().value())
                && scene.publicRevision().known() && life.publicRevision().is(scene.publicRevision().value())
                && scene.snapshotId().known() && life.snapshotId().is(scene.snapshotId().value())
                && scene.actorId().known() && life.playerCharacterId().is(scene.actorId().value())
                && scene.dateRaw().known() && life.dateRaw().is(scene.dateRaw().value()),
                "root scene and LIFE input must bind the same actor and public/native/date frame");
        RootScope root = assessment.root();
        Field<Boolean> admitted = switch (root.status()) {
            case ADMITTED -> Field.of(true);
            case OUTSIDE_SCENE -> Field.of(false);
            case ROOT_QUERY_NEEDED, SCOPE_UNAVAILABLE -> Field.missing();
        };
        Field<Boolean> peace = root.status() == RootScopeStatus.SCOPE_UNAVAILABLE ? Field.missing() : Field.of(root.atPeace());
        Field<Boolean> taxes = root.collectTaxesActive().known() ? Field.of(root.collectTaxesActive().value()) : Field.nullValue();
        return new Request(current.snapshot(), admitted, peace, taxes,
                peace.is(false), allowWartimeInitialFocus, current.preferredFocusTargetKey(), current.pendingAction(),
                Field.of(root.status() == RootScopeStatus.ADMITTED && "feudal_government".equals(root.governmentKey())));
    }
    public static LifestyleMinPolicy.RoutedDecision choose(Request current, Assessment assessment,
            boolean allowWartimeInitialFocus, Field<org.xar.ck3.control.governance.lifestyleperks.LifestylePerksModel.Input> allLifestyle) {
        return LifestyleMinPolicy.chooseRouted(applyToMinimum(current, assessment, allowWartimeInitialFocus), allLifestyle);
    }
}
