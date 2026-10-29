package org.xar.ck3.control.nativebridge.capabilities.activity;

import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.governance.activity.ActivityConfigurationModels;
import org.xar.ck3.control.governance.activity.ActivityPlannerDiagnostic;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.wave2.finance.feastterminal.CompletionCallJournal;

/** Validated copies preserve unknown, absent and native empty collections separately. */
public sealed interface ActivityPayload {
    Obj original();
    record Diagnostic(ActivityPlannerDiagnostic.Observation observation, Obj original) implements ActivityPayload { }
    record StageOne(ActivityConfigurationModels.StageOne observation, Obj original) implements ActivityPayload { }
    record StageTwo(ActivityConfigurationModels.StageTwo observation, Obj original) implements ActivityPayload { }
    record Location(ActivityConfigurationModels.Location observation, Obj original) implements ActivityPayload { }
    record Gate(ActivityConfigurationModels.StageTwoGate observation, Obj original) implements ActivityPayload { }
    enum Resource { GOLD, TREASURY, PIETY, BARTER_GOODS }
    record Cost(Resource resource, int nativeIndex, BigInteger configuredRaw) { }
    record Balance(Resource resource, Optional<BigInteger> raw) { public Balance { Objects.requireNonNull(resource); Objects.requireNonNull(raw); } }
    record Gold(BigInteger refreshSequence, BigInteger configuredRaw, BigInteger actorGoldRaw, Obj original) implements ActivityPayload { }
    enum DisplayState { NOT_APPLICABLE, KNOWN, UNKNOWN }
    record FailureDisplay(DisplayState state, Optional<String> value, Optional<String> unknownReason) { }
    record FullCost(BigInteger refreshSequence, BigInteger actorGoldRaw, List<Cost> resources,
            boolean finalCanStart, FailureDisplay failureDisplay, Obj original) implements ActivityPayload {
        public FullCost { resources = List.copyOf(resources); }
    }
    record CandidateRow(long characterId, BigInteger joinRaw, int travelDays, int arrivalRaw, int plannedStartRaw) { }
    enum CandidateStatus { OBSERVED, NO_QUALIFIED_CANDIDATE, UNAVAILABLE }
    record Candidate(CandidateStatus status, Optional<String> unavailableReason, Optional<BigInteger> refreshSequence,
            Optional<String> sourceFingerprint, Optional<CandidateRow> candidate, Obj original) implements ActivityPayload { }
    record Opinion(long guestId, String status, Optional<Integer> value, Optional<Obj> activityTarget,
            Optional<Obj> rewardModifiers, Obj original) implements ActivityPayload { }
    record Target(long characterId, boolean available, Optional<Boolean> selectedMember,
            Optional<Boolean> filteredMember, Optional<BigInteger> joinRaw, Optional<Boolean> positiveJoin,
            Optional<Boolean> timelyArrival, Optional<Boolean> finalCanStart, Obj original) implements ActivityPayload { }
    record SelectedGuest(long characterId, BigInteger joinRaw, int arrivalRaw, int travelDays, boolean late) { }
    record RouteProof(boolean available, List<SelectedGuest> selectedGuests, Optional<CandidateRow> preInvitationCandidate,
            Optional<Boolean> finalCanStart, Obj original) implements ActivityPayload { public RouteProof { selectedGuests = List.copyOf(selectedGuests); } }
    record Rule(String authoredRuleKey, String status, boolean invoked, Optional<Boolean> active, Obj original) implements ActivityPayload { }
    record RuleProvenance(String authoredRuleKey, long candidateId, String status, Optional<Boolean> membership,
            Optional<List<Long>> filteredIds, Obj original) implements ActivityPayload {
        public RuleProvenance { filteredIds = filteredIds.map(List::copyOf); }
    }
    record HostedActivity(long fullId, long hostId, String typeKey, Optional<Boolean> completed,
            Optional<Boolean> invalidated, Optional<BigInteger> completionStamp) { }
    record OutcomeValues(Optional<BigInteger> prestigeRaw, Optional<Integer> stress, Optional<Boolean> revelerPresent,
            Optional<BigInteger> revelerXpRaw) { }
    record OrdinaryGuest(boolean qualified, Optional<CandidateRow> candidate, Obj original) { }
    record Inputs(BigInteger refreshSequence, boolean finalCanStart, boolean guestRouteQualified,
            List<Cost> resources, List<Balance> balances, List<HostedActivity> hosted,
            Optional<OrdinaryGuest> ordinaryGuest, Optional<OutcomeValues> outcomes, Obj original) implements ActivityPayload {
        public Inputs { resources = List.copyOf(resources); balances = List.copyOf(balances); hosted = List.copyOf(hosted); }
    }
    /** Rejected optional journals remain retained, and cannot make an otherwise valid base read successful. */
    sealed interface JournalObservation permits JournalKnown, JournalRejected, JournalNull { }
    record JournalKnown(CompletionCallJournal.Journal journal) implements JournalObservation { }
    record JournalRejected(String reason, RawJson raw) implements JournalObservation { }
    record JournalNull() implements JournalObservation { }
    record Hosted(List<Balance> balances, List<HostedActivity> hosted, Optional<OutcomeValues> outcomes,
            Optional<ActivityTerminalJournal.Observation> terminalJournal, Optional<JournalObservation> completionCalls, Obj original) implements ActivityPayload {
        public Hosted { balances = List.copyOf(balances); hosted = List.copyOf(hosted); }
    }
}
