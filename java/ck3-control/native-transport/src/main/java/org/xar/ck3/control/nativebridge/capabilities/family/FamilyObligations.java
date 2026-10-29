package org.xar.ck3.control.nativebridge.capabilities.family;

import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.OptionalLong;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.StrictJson;

/** Complete observation domain. A send quote, predicted lineage and material outcome remain separate. */
public final class FamilyObligations {
    public static final String STEP = "read-family-obligations-private-12002";
    public static final String PERMISSION = "allow_private_family_obligations_query";
    private FamilyObligations() { }

    /** ORIGINAL2 is a compatibility fixture domain, never current runtime admission. */
    public enum Build {
        ORIGINAL2("1.20.0.2", "ae1ba6ff060ba603842f6f4a2ded0af4b7d3666b3dd271f75fb01b0da8e81b2d"),
        CURRENT4("1.20.0.4", CachedSuccession12004.EXE_SHA256);
        private final String version;
        private final String sha256;
        Build(String version, String sha256) { this.version = version; this.sha256 = sha256; }
        public String version() { return version; }
        public String sha256() { return sha256; }
        public String exactBuild() { return version + "@sha256:" + sha256; }
    }
    public enum QueryStatus { AVAILABLE, PARTIAL, UNAVAILABLE }
    public enum Status { AVAILABLE, UNAVAILABLE, NOT_REQUESTED, DEFERRED_BY_OWNER }
    public enum BreakStatus { AVAILABLE, NO_BETROTHAL, UNAVAILABLE, NOT_REQUESTED }
    public enum Side { ATTACKER, DEFENDER, ABSENT }
    public enum Answer { RAW_0, RAW_1, RAW_2 }
    public enum SendStage {
        NONE, SETUP, PAIR_DEFINITION_RESTRICTION, DIPLOMATIC_RANGE, DEFINITION_AE8, AVAILABILITY,
        ALREADY_CONSIDERING, DEFINITION_C88, DEFINITION_E28, DEFINITION_1168, DEFINITION_FC8,
        DEFINITION_D58, DEFINITION_EF8, PRECHECK_OTHER, INTERNAL_ANSWER, COMPLETE_CAN_SEND_OTHER
    }
    public enum DescriptionStatus { OBSERVED, UNAVAILABLE, NOT_APPLICABLE }
    public record Pair(long subject, long candidate) {
        public Pair { fullId(subject); fullId(candidate); StrictJson.require(subject != candidate, "distinct original family pair required"); }
    }
    /** Missing fields are retained as Optional.empty; explicit null is invalid for request selectors. */
    public record Request(BigInteger expectedRevision, Optional<Pair> pair, boolean matrilineal,
            OptionalLong breakRecipient, OptionalLong ally, boolean enumerateCurrentAllies) {
        public Request {
            positive64(expectedRevision); Objects.requireNonNull(pair); Objects.requireNonNull(breakRecipient); Objects.requireNonNull(ally);
            breakRecipient.ifPresent(FamilyObligations::fullId); ally.ifPresent(FamilyObligations::fullId);
            StrictJson.require(pair.isPresent() || (ally.isPresent() || enumerateCurrentAllies) && !matrilineal && breakRecipient.isEmpty(),
                    "ally-only request cannot request unrelated family terms");
        }
    }
    public record Binding(Build build, String snapshotId, BigInteger publicRevision, BigInteger nativeRevision,
            int dateRaw, long playedCharacterId) {
        public Binding {
            Objects.requireNonNull(build); StrictJson.text(snapshotId); positive64(publicRevision); positive64(nativeRevision); fullId(playedCharacterId);
        }
    }
    public record LineageTerms(boolean selectedMatrilineal, boolean effectiveMatrilinealIfAccepted,
            boolean completeCanSend, long selectedParent, OptionalLong house, OptionalLong dynasty) {
        public LineageTerms { fullId(selectedParent); Objects.requireNonNull(house); Objects.requireNonNull(dynasty); }
    }
    public record Lineage(Status status, String reason, OptionalLong subject, OptionalLong candidate,
            boolean requestedMatrilineal, Optional<LineageTerms> terms) {
        public Lineage { Objects.requireNonNull(status); FamilyObligations.reason(reason); Objects.requireNonNull(subject); Objects.requireNonNull(candidate); Objects.requireNonNull(terms); }
    }
    public record Costs(List<Long> slots) {
        public Costs { slots = List.copyOf(slots); StrictJson.require(slots.size() == 10, "all ten native resource slots required"); }
    }
    public record SelectedTerms(boolean completeCanSend, Costs sendCosts, long recipientAcceptanceRaw,
            Answer recipientAnswer, boolean nativeAutoAccept) {
        public SelectedTerms { Objects.requireNonNull(sendCosts); Objects.requireNonNull(recipientAnswer); }
    }
    public record DiagnosticValues(Answer sendAnswer, boolean precheckPassed, boolean setupPassed,
            boolean availabilityPassed, boolean pairRestrictionBlocked, boolean diplomaticRangePassed,
            boolean alreadyConsideringBlocked, List<Boolean> definitionGates, SendStage firstFailedStage) {
        public DiagnosticValues {
            Objects.requireNonNull(sendAnswer); definitionGates = List.copyOf(definitionGates); Objects.requireNonNull(firstFailedStage);
            StrictJson.require(definitionGates.size() == 7, "seven original AE8/C88/E28/1168/FC8/D58/EF8 gates required");
        }
    }
    /** Present group with empty values means explicitly unobserved; missing group is the outer Optional. */
    public record Diagnostics(Optional<DiagnosticValues> values) { public Diagnostics { Objects.requireNonNull(values); } }
    public record DescriptionValues(DescriptionStatus status, Optional<String> text) {
        public DescriptionValues { Objects.requireNonNull(status); Objects.requireNonNull(text); text.ifPresent(FamilyObligations::reason); }
    }
    public record Description(Optional<DescriptionValues> values) { public Description { Objects.requireNonNull(values); } }
    public record War(long warId, long caller, long recipient, Side callerSide, Side recipientSide,
            OptionalLong primaryAttacker, OptionalLong primaryDefender, List<Long> attackers, List<Long> defenders,
            boolean callerPrimaryLeader, boolean recipientWasCalled, boolean targetCanBePicked, boolean targetRowSelectable,
            Optional<Boolean> selectedContextAvailable, Optional<SelectedTerms> selectedTerms,
            Optional<Diagnostics> diagnostics, Optional<Description> c88Description) {
        public War {
            Objects.requireNonNull(callerSide); Objects.requireNonNull(recipientSide); Objects.requireNonNull(primaryAttacker);
            Objects.requireNonNull(primaryDefender); attackers = List.copyOf(attackers); defenders = List.copyOf(defenders);
            Objects.requireNonNull(selectedContextAvailable); Objects.requireNonNull(selectedTerms); Objects.requireNonNull(diagnostics); Objects.requireNonNull(c88Description);
        }
    }
    public record AllianceTerms(boolean firstHasSecond, boolean secondHasFirst, List<War> firstWars, List<War> secondWars) {
        public AllianceTerms { firstWars = List.copyOf(firstWars); secondWars = List.copyOf(secondWars); }
    }
    public record Alliance(Status status, String reason, OptionalLong first, OptionalLong second, Optional<AllianceTerms> terms) {
        public Alliance { Objects.requireNonNull(status); FamilyObligations.reason(reason); Objects.requireNonNull(first); Objects.requireNonNull(second); Objects.requireNonNull(terms); }
    }
    public record Ally(long character, boolean playerHasAlly, boolean allyHasPlayer, boolean hasRealmData) { }
    public record AlliesTerms(List<Long> sourceIds, List<Long> unresolvedSourceIds, List<Long> deadSourceIds, List<Ally> allies) {
        public AlliesTerms {
            sourceIds = List.copyOf(sourceIds); unresolvedSourceIds = List.copyOf(unresolvedSourceIds); deadSourceIds = List.copyOf(deadSourceIds); allies = List.copyOf(allies);
        }
    }
    public record Allies(Status status, String reason, long playedCharacter, Optional<AlliesTerms> terms) {
        public Allies { Objects.requireNonNull(status); FamilyObligations.reason(reason); Objects.requireNonNull(terms); }
    }
    public record PenaltyTerms(boolean properReason, boolean grandWeddingPromised, boolean ordinaryPrestigeRelevant,
            boolean yieldsAllianceEvaluated, boolean yieldsAlliance, OptionalLong rejectedOwner, int highestRejectedTier,
            long stockPrestigeEffectRaw, int stockPrestigeLevelEffect) {
        public PenaltyTerms { Objects.requireNonNull(rejectedOwner); }
    }
    public record Penalty(boolean available, boolean effectsComplete, String source, String reason, Optional<PenaltyTerms> terms) {
        public Penalty { FamilyObligations.reason(source); FamilyObligations.reason(reason); Objects.requireNonNull(terms); }
    }
    public record BreakValues(OptionalLong betrothed, OptionalLong recipient, OptionalLong secondaryActor,
            OptionalLong secondaryRecipient, OptionalLong intermediary, OptionalLong definitionOrdinal, long definitionStableHash,
            boolean finalLegalitySampled, Optional<Boolean> completeCanSend, boolean sendCostsAvailable, Optional<Costs> sendCosts,
            boolean outcomePenaltyAvailable, String outcomePenaltyUnavailableReason, Penalty outcomePenalty) {
        public BreakValues {
            Objects.requireNonNull(betrothed); Objects.requireNonNull(recipient); Objects.requireNonNull(secondaryActor); Objects.requireNonNull(secondaryRecipient);
            Objects.requireNonNull(intermediary); Objects.requireNonNull(definitionOrdinal); Objects.requireNonNull(completeCanSend);
            Objects.requireNonNull(sendCosts); reason(outcomePenaltyUnavailableReason); Objects.requireNonNull(outcomePenalty);
        }
    }
    public record BetrothalBreak(BreakStatus status, String reason, OptionalLong actor, OptionalLong subject,
            OptionalLong requestedRecipient, Optional<BreakValues> values) {
        public BetrothalBreak { Objects.requireNonNull(status); FamilyObligations.reason(reason); Objects.requireNonNull(actor); Objects.requireNonNull(subject); Objects.requireNonNull(requestedRecipient); Objects.requireNonNull(values); }
    }
    public record Observation(Binding binding, Request request, QueryStatus status, Lineage lineage, Alliance alliance,
            Optional<Allies> currentAllies, BetrothalBreak betrothalBreak, RawJson originalNativeResult) {
        public Observation {
            Objects.requireNonNull(binding); Objects.requireNonNull(request); Objects.requireNonNull(status); Objects.requireNonNull(lineage);
            Objects.requireNonNull(alliance); Objects.requireNonNull(currentAllies); Objects.requireNonNull(betrothalBreak); Objects.requireNonNull(originalNativeResult);
        }
        public boolean businessPostconditionVerified() { return false; }
        public boolean fullProductAcceptanceCredit() { return false; }
    }
    static void reason(String value) { StrictJson.require(value != null && value.length() <= 32_768, "bounded source string required"); if (!value.isEmpty()) StrictJson.text(value); }
    static void positive64(BigInteger value) { StrictJson.require(value != null && value.signum() > 0 && value.compareTo(StrictJson.UINT64_MAX) <= 0, "positive uint64 required"); }
    static void fullId(long value) { StrictJson.require(value > 0 && value <= 0xffff_ffffL, "original full uint32 identity required"); }
}
