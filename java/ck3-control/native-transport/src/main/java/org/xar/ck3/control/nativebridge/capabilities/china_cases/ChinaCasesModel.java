package org.xar.ck3.control.nativebridge.capabilities.china_cases;

import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.StrictJson;

/** Domain projections of the original fixed ZhongGuo native collectors. Original packets remain in coordinator custody. */
public final class ChinaCasesModel {
    private ChinaCasesModel() { }
    private static <T> T nn(T value) { return Objects.requireNonNull(value); }
    public record Nonce(String value) {
        public Nonce { StrictJson.require(value!=null && value.matches("[A-Za-z0-9][A-Za-z0-9._:-]{0,63}"),"request_nonce is invalid"); }
    }
    public record CharacterId(int value) {
        public CharacterId { StrictJson.require(value>0,"character ID must be a positive int32"); }
        public BigInteger integer() { return BigInteger.valueOf(value); }
    }
    public enum Status { AVAILABLE, UNAVAILABLE }
    public enum ReceiptStatus { RECORDED, NOT_RECORDED, UNAVAILABLE }
    public enum DeadlineStatus { PENDING, EXPIRED, NOT_SCHEDULED, UNAVAILABLE }
    public enum IncidentProfile { X, Y, Z }
    public enum TerminalKind { NA, INCIDENT, UNAVAILABLE }
    public enum KpiDisposition { NOT_STAGED, PENDING, CONSUMED, UNAVAILABLE }
    public enum CheckpointState { CP26_READY_P3_ABSENT, P3_INITIALIZED_SOURCE_NOT_READY, P3_RESULT_COMMITTED, P3_SOURCE_READY_RESULT_PENDING, UNAVAILABLE }
    public sealed interface Field<T> permits Available, Unavailable {
        default boolean available() { return this instanceof Available<?>; }
        default Optional<T> optional() { return this instanceof Available<T> value ? Optional.of(value.value()) : Optional.empty(); }
        default T required() { return optional().orElseThrow(() -> new IllegalStateException("native field unavailable")); }
    }
    public record Available<T>(T value) implements Field<T> { public Available { nn(value); } }
    public record Unavailable<T>(String reason) implements Field<T> { public Unavailable { nn(reason); } }
    public record Header(Status status, Nonce nonce, BigInteger nativeRevision, int dateRaw, CharacterId player,
            String sourceBackendId, Optional<String> unavailableReason) {
        public Header {
            nn(status); nn(nonce); nn(player);
            nn(nativeRevision); StrictJson.require(nativeRevision.signum() > 0 && nativeRevision.compareTo(StrictJson.UINT64_MAX) <= 0, "native uint64 revision");
            StrictJson.text(sourceBackendId); unavailableReason = nn(unavailableReason);
            StrictJson.require((status == Status.UNAVAILABLE) == unavailableReason.isPresent(), "status/reason disagreement");
        }
    }
    public sealed interface Frame permits B1Frame, CaseFrame, AiOwnedFrame, ResultFrame, PipFrame, PromotionFrame, Af5Frame, ProjectsFrame, IncidentFrame, ScoreboardFrame, ProgressFrame { Header header(); }
    public record CaseIdentity(Field<BigInteger> ownerCharacterId, Field<BigInteger> subjectCharacterId, Field<BigInteger> cycleSerial, Field<BigInteger> caseSerial, Field<BigInteger> state, Field<Boolean> active, Field<BigInteger> revision, Field<BigInteger> timelineSerial, Field<BigInteger> feedbackRevision) {
    }
    public record Policy(Field<String> policyId, Field<BigInteger> choice) {
    }
    public record Operation(Field<BigInteger> operationId, Field<String> operationKey, Field<String> hook, Field<BigInteger> preState, Field<BigInteger> postState) {
    }
    public record Receipt(ReceiptStatus status, Field<String> key, Field<BigInteger> ownerCharacterId, Field<BigInteger> subjectCharacterId, Field<BigInteger> cycleSerial, Field<BigInteger> caseSerial, Field<BigInteger> state, Field<BigInteger> choice) {
    }
    public record Deadline(DeadlineStatus status, Field<BigInteger> targetCharacterId, Field<BigInteger> ownerCharacterId, Field<BigInteger> cycleSerial, Field<BigInteger> caseSerial, Field<BigInteger> expectedState, Field<BigInteger> days, Field<BigInteger> openDateRaw, Field<BigInteger> dueDateRaw, Field<Boolean> pending, Field<Boolean> expired, Field<String> onDueOperation) {
    }
    public record B1Cycle(Field<BigInteger> cycleSerial, Field<BigInteger> caseSerial, Field<BigInteger> state, Field<BigInteger> openYear, Field<BigInteger> runtimeSchema, Field<Boolean> active) {
    }
    public record B1Roster(Field<BigInteger> subjectCount, Field<BigInteger> beforePruneCount, Field<BigInteger> prunedCount, Field<BigInteger> amendmentCount, Field<BigInteger> auditVersion, Field<Boolean> reopenRequired) {
    }
    public record B1Processing(Field<BigInteger> count, Field<BigInteger> agendaCount, Field<BigInteger> localCandidateCount, Field<BigInteger> preCalibrationValidCount) {
    }
    public record B1Quota(Field<BigInteger> rebuildGeneration, Field<BigInteger> builtCaseSerial, Field<BigInteger> bookVersion, Field<BigInteger> targetTop, Field<BigInteger> targetMiddle, Field<BigInteger> targetBottom, Field<BigInteger> recountTop, Field<BigInteger> recountMiddle, Field<BigInteger> recountBottom, Field<BigInteger> preCalibrationExpectedCount, Field<Boolean> preCalibrationMismatch, Field<Boolean> poolMembership) {
    }
    public record B1Closure(Field<Boolean> calibrationFinalized, Field<BigInteger> state, Field<Boolean> rewardsIssued, Field<Boolean> publicationBlocked) {
    }
    public record B1Pending(Field<BigInteger> openCount, Field<BigInteger> slotUsed, Field<BigInteger> rewardExpectedCount, Field<BigInteger> rewardsPaidCount, Field<Boolean> rewardsCommitted, Field<BigInteger> watchdogCancelledCount, Field<BigInteger> watchdogOrphanCount) {
    }
    public record OwnerEligibility(Field<BigInteger> ownerCharacterId, Field<Boolean> ownerAlive, Field<Boolean> ownerIsAi, Field<BigInteger> primaryTitleId, Field<BigInteger> primaryTitleTierRaw, Field<String> primaryTitleTierKey, Field<String> governmentKey, Field<BigInteger> subjectImmediateLiegeCharacterId, Field<Boolean> subjectIsDirectSubject, Field<Boolean> authorized) {
    }
    public record Stage(Field<BigInteger> state, Field<String> key, Field<Boolean> active) {
    }
    public record Route(Field<String> kind, Field<Boolean> visibleEventAllowed, Field<Boolean> ownerIsAi, Field<Boolean> managerEligible, Field<Boolean> directSubjectEligible) {
    }
    public record ResultIdentity(Field<BigInteger> caseSerial, Field<BigInteger> cycleSerial, Field<BigInteger> grade, Field<BigInteger> ownerCharacterId, Field<BigInteger> state, Field<BigInteger> subjectCharacterId) {
    }
    public record Notice(Field<BigInteger> absoluteGrade, Field<BigInteger> cohortNFrozen, Field<BigInteger> kpiFrozenQ100000, Field<BigInteger> rankFrozen) {
    }
    public record Delivery(Field<BigInteger> method, Field<Boolean> objectionRecorded, Field<BigInteger> settlementPostedSerial, Field<Boolean> appealOpen) {
    }
    public record PipGate(Field<BigInteger> ownerCharacterId, Field<BigInteger> subjectCharacterId, Field<BigInteger> cycleSerial, Field<BigInteger> caseSerial, Field<BigInteger> threshold, Field<BigInteger> negativeComponentCount, Field<Boolean> evidenceComplete, Field<BigInteger> status, Field<BigInteger> resultCaseSerial, Field<BigInteger> resultGrade, Field<BigInteger> absoluteGrade, Field<BigInteger> kpiFrozenQ100000, Field<BigInteger> governanceQ100000, Field<BigInteger> capabilityQ100000, Field<BigInteger> growthQ100000, Field<BigInteger> superiorQ100000, Field<BigInteger> valuesQ100000, Field<BigInteger> collaborationQ100000, Field<BigInteger> jingchaQ100000, Field<BigInteger> organizationQ100000) {
    }
    public record PipPip(Field<BigInteger> ownerCharacterId, Field<BigInteger> subjectCharacterId, Field<BigInteger> cycleSerial, Field<BigInteger> caseSerial, Field<BigInteger> state, Field<BigInteger> taskKind, Field<Boolean> taskControllable, Field<BigInteger> policyRoute) {
    }
    public record PipResponse(Field<BigInteger> subjectResponse, Field<BigInteger> responseCaseSerial, Field<BigInteger> responseAuthorCharacterId, Field<BigInteger> acknowledgementReceiptSerial, Field<Boolean> goalRevisionUsed, Field<BigInteger> refusalReceiptSerial) {
    }
    public record PipSupport(Field<Boolean> capacityReserved, Field<BigInteger> ownerCapacityUsed, Field<Boolean> supportAbsent, Field<BigInteger> hours, Field<BigInteger> attentionUnits, Field<BigInteger> mentorCharacterId, Field<BigInteger> budgetOwnerCharacterId, Field<BigInteger> treasuryBudgetAllocated, Field<BigInteger> treasuryBudgetSpent, Field<BigInteger> supportReceiptSerial, Field<Boolean> released, Field<Boolean> withheld, Field<Boolean> atomicShortfall) {
    }
    public record PipBudgetLedger(Field<BigInteger> resultCaseSerial, Field<BigInteger> treasuryPenaltyPaid, Field<BigInteger> personalGoldPenaltyPaid, Field<BigInteger> supportTreasuryAllocated, Field<BigInteger> supportTreasurySpent) {
    }
    public record PipD180Ticket(Field<BigInteger> ownerCharacterId, Field<BigInteger> subjectCharacterId, Field<BigInteger> cycleSerial, Field<BigInteger> caseSerial, Field<BigInteger> expectedState, Field<BigInteger> dueDateRaw) {
    }
    public record PipD365Ticket(Field<BigInteger> ownerCharacterId, Field<BigInteger> subjectCharacterId, Field<BigInteger> cycleSerial, Field<BigInteger> caseSerial, Field<BigInteger> expectedState, Field<BigInteger> dueDateRaw) {
    }
    public record PipMidpoint(Field<BigInteger> receiptSerial, Field<Boolean> resourceDeliveryValid, Field<BigInteger> progressStatus, Field<BigInteger> progressRedCode, Field<BigInteger> state) {
    }
    public record PipOutcome(Field<BigInteger> code, Field<BigInteger> settlementReceiptSerial, Field<BigInteger> resultCycleSerial, Field<BigInteger> resultCaseSerial, Field<BigInteger> resultGrade, Field<BigInteger> stabilityDaysObserved, Field<BigInteger> independentReviewStatus, Field<BigInteger> independentReviewRedCode, Field<BigInteger> graduationReceiptSerial, Field<BigInteger> failureReceiptSerial, Field<Boolean> noSupportLiability) {
    }
    public record PipNextCycleEvidence(Field<BigInteger> status, Field<BigInteger> ownerCharacterId, Field<BigInteger> subjectCharacterId, Field<BigInteger> sourceCycleSerial, Field<BigInteger> sourceCaseSerial, Field<BigInteger> dueCycleSerial, Field<BigInteger> delta, Field<BigInteger> consumedCycleSerial, Field<BigInteger> consumedCaseSerial) {
    }
    public record Identity(Field<BigInteger> ownerCharacterId, Field<BigInteger> subjectCharacterId, Field<BigInteger> cycleSerial, Field<BigInteger> caseSerial, Field<BigInteger> revision) {
    }
    public record ProjectIdentity(Field<BigInteger> ownerCharacterId, Field<BigInteger> subjectCharacterId, Field<BigInteger> cycleSerial, Field<BigInteger> caseSerial) {
    }
    public record FrozenCase(Identity identity, boolean frozen) {
    }
    public record PromotionChoice(Identity identity, Field<BigInteger> optionNumber, Field<BigInteger> receiptSerial, Field<Boolean> active, Field<Boolean> consumed) {
    }
    public record CompensationReceipt(Identity identity, Field<BigInteger> operationId, Field<BigInteger> optionNumber, Field<BigInteger> receiptSerial, Field<Boolean> active, Field<Boolean> consumed, Field<Boolean> posted) {
    }
    public record PromotionCompensation(Identity sourceIdentity, Identity resultIdentity, FrozenCase frozenCase, PromotionChoice promotionChoice, CompensationReceipt compensationReceipt) {
    }
    public record Af5Portfolio(Field<BigInteger> domain, Field<BigInteger> stage, Field<BigInteger> completedCycle, Field<Boolean> visiblePending, Identity resultIdentity) {
    }
    public record Af5Case(Identity identity, Field<BigInteger> state, Field<Boolean> active, Field<BigInteger> lastOperation, Field<BigInteger> lastRoute, Field<Boolean> repurchaseResolved, Field<Boolean> unitConserved, Field<BigInteger> resultCaseSerial) {
    }
    public record Af5Receipt(Identity identity, Field<BigInteger> state, Field<Boolean> active, Field<Boolean> consumed, Field<BigInteger> route) {
    }
    public record Af5(Af5Portfolio portfolio, Af5Case caseRecord, Af5Receipt m299, Af5Receipt m300) {
    }
    public record ProjectPortfolio(boolean providerObserved, Field<BigInteger> closed, Field<BigInteger> cycleSerial, Field<BigInteger> finalCaseSerial, Field<BigInteger> finalConservationOk, Field<BigInteger> finalCycleSerial, Field<BigInteger> finalOwnerCharacterId, Field<BigInteger> finalState, Field<BigInteger> finalSubjectCharacterId, Field<BigInteger> pendingPlayerEvent) {
    }
    public record Contribution(ProjectIdentity identity, Field<BigInteger> receiptId, Field<BigInteger> receiptRevision, Field<BigInteger> value, boolean providerObserved) {
    }
    public record MetricsResult(ProjectIdentity identity, Field<BigInteger> sourceContributionReceiptId, Field<BigInteger> sourceContributionReceiptRevision, Field<BigInteger> metricsRevision, Field<String> dictionaryKey, boolean providerObserved) {
    }
    public record ProjectsMetrics(ProjectIdentity sourceIdentity, ProjectIdentity resultIdentity, Contribution contribution, MetricsResult metricsResult) {
    }
    public record Probe(Field<BigInteger> consequenceKind, Field<BigInteger> cycleSerial, Field<BigInteger> ownerCharacterId, Field<BigInteger> probeSerial, Field<BigInteger> result, Field<BigInteger> sourceKind, Field<BigInteger> subjectCharacterId) {
    }
    public record Resources(Field<BigInteger> capitalControlQ100000, Field<BigInteger> managerTreasuryQ100000, Field<BigInteger> subjectPersonalGoldQ100000) {
    }
    public record NotApplicable(Field<BigInteger> applicable, Field<BigInteger> cycleSerial, Field<BigInteger> kpiStaged, Field<BigInteger> ownerCharacterId, Field<BigInteger> probeSerial, Field<BigInteger> reason, Field<BigInteger> receiptSerial, Field<BigInteger> subjectCharacterId) {
    }
    public record Incident(Field<BigInteger> applicable, Field<BigInteger> caseSerial, Field<BigInteger> consequenceKind, Field<BigInteger> cycleSerial, Field<BigInteger> finalScore, Field<BigInteger> incidentSerial, Field<BigInteger> kpiStaged, Field<BigInteger> ownerCharacterId, Field<BigInteger> revision, Field<BigInteger> sourceKind, Field<BigInteger> state, Field<BigInteger> subjectCharacterId) {
    }
    public record Kpi(KpiDisposition disposition, Field<BigInteger> caseSerial, Field<BigInteger> consequenceKind, Field<BigInteger> consumed, Field<BigInteger> consumedCaseSerial, Field<BigInteger> consumedCycle, Field<BigInteger> consumedDueCycle, Field<BigInteger> consumedIncidentSerial, Field<BigInteger> consumedOriginCycle, Field<BigInteger> consumedOwnerCharacterId, Field<BigInteger> consumedScore, Field<BigInteger> consumedSubjectCharacterId, Field<BigInteger> dueCycle, Field<BigInteger> dueOffset, Field<BigInteger> incidentSerial, Field<BigInteger> originCycle, Field<BigInteger> ownerCharacterId, Field<BigInteger> pending, Field<BigInteger> receiptSerial, Field<BigInteger> score, Field<BigInteger> sourceKind, Field<BigInteger> state, Field<BigInteger> subjectCharacterId) {
    }
    public record Terminal(TerminalKind kind, Optional<NotApplicable> na, Optional<Incident> incident) {
    }
    public record Widget(String stableIdentity, String runtimeName, Field<String> instancePointer, Field<String> vtablePointer, Field<Boolean> exists, Field<Boolean> localVisible, Field<Boolean> effectiveVisible, Field<Boolean> enabled, Field<Boolean> focused, Field<Boolean> modalBlocking, Field<BigInteger> screenX, Field<BigInteger> screenY, Field<BigInteger> screenWidth, Field<BigInteger> screenHeight, Field<BigInteger> scrollMin, Field<BigInteger> scrollMax, Field<BigInteger> scrollValue) {
    }
    public record ManagedAcl(boolean surfaceAvailable, boolean currentPlayerCanAssessOthers, Field<BigInteger> ownerCharacterId, Field<BigInteger> firstSubjectCharacterId) {
    }
    public record ReceivedAcl(boolean surfaceAvailable, boolean currentPlayerIsSubject, Field<BigInteger> b1CaseSerial, Field<BigInteger> cycleSerial, Field<BigInteger> disclosureAclMode, Field<BigInteger> disclosureBlackboxRisk, Field<BigInteger> disclosureEvaluatorIdentityMode, Field<BigInteger> disclosurePolicyAvailable, Field<BigInteger> disclosurePolicyId, Field<BigInteger> disclosureSelfMode, Field<BigInteger> disclosureTeamMode, Field<BigInteger> firstRowCharacterId, Field<BigInteger> ownerCharacterId, Field<BigInteger> resultCaseSerial, Field<BigInteger> subjectCharacterId) {
    }
    public record Acl(ManagedAcl managed, ReceivedAcl receivedSelf) {
    }
    public record ReadOnlyActions(Field<Boolean> activate, Field<Boolean> close, Field<Boolean> reopen) {
    }
    public record ProgressWidget(String stableIdentity, String runtimeName, Field<String> instancePointer, Field<String> vtablePointer, Field<Boolean> exists, Field<Boolean> effectiveVisible, Field<Boolean> enabled) {
    }
    public record B1Readiness(boolean closureReady, boolean cycleIdentityReady, boolean managerBindingReady, boolean pendingReady, boolean processingReady, boolean quotaReady, boolean ready, boolean rosterReady, boolean sameFrameReady) {
    }
    public record CaseReadiness(boolean caseIdentityReady, boolean deadlineDueDateReady, boolean deadlineIdentityReady, boolean operationReady, boolean playerBindingReady, boolean policyReady, boolean ready, boolean receiptReady, boolean sameFrameReady) {
    }
    public record AiOwnedReadiness(boolean caseIdentityReady, boolean ownerEligibilityReady, boolean ready, boolean receiptReady, boolean routeReady, boolean sameFrameReady, boolean stageReady) {
    }
    public record ResultReadiness(boolean caseIdentityReady, boolean deliveryStateReady, boolean noticeFactsReady, boolean ownerBindingReady, boolean playerSubjectBindingReady, boolean ready, boolean sameFrameReady) {
    }
    public record PipReadiness(boolean budgetLedgerReady, boolean d180TicketObservationReady, boolean d365TicketObservationReady, boolean gateEvidenceReady, boolean gateReady, boolean midpointReady, boolean modifierObservationReady, boolean nextCycleEvidenceReady, boolean outcomeReady, boolean ownerBindingReady, boolean pipIdentityReady, boolean playerSubjectBindingReady, boolean ready, boolean responseReady, boolean sameFrameReady, boolean supportReady) {
    }
    public record PromotionReadiness(boolean compensationReceiptPosted, boolean frozenCaseIdentityReady, boolean playerOwnerBindingReady, boolean portfolioSubjectBindingReady, boolean promotionChoiceReceiptReady, boolean ready, boolean receiptSerialsReady, boolean resultIdentityReady, boolean revisionBindingReady, boolean sameCaseIdentityReady, boolean sameFrameReady, boolean sourceIdentityReady) {
    }
    public record Af5Readiness(boolean playerOwnerBindingReady, boolean portfolioSubjectBindingReady, boolean ready, boolean sameCaseIdentityReady, boolean sameFrameReady) {
    }
    public record ProjectsReadiness(boolean contributionReady, boolean metricsReady, boolean ownerBindingReady, boolean playerSubjectBindingReady, boolean portfolioClosed, boolean portfolioObserved, boolean ready, boolean receiptLineageReady, boolean resultIdentityReady, boolean resultOperationCommitted, boolean sameFrameReady, boolean sameProjectCaseIdentity, boolean sourceIdentityReady) {
    }
    public record IncidentReadiness(boolean kpiStateReady, boolean ownerBindingReady, boolean playerSubjectBindingReady, boolean probeReady, boolean profileBindingReady, boolean ready, boolean resourceSnapshotReady, boolean sameFrameReady, boolean terminalReady) {
    }
    public record ScoreboardReadiness(boolean aclReady, boolean entryWindowStateReady, boolean fullWidgetGateReady, boolean guiRootReady, boolean playerBindingReady, boolean productionLiveReady, boolean sameFrameReady, boolean stateAclQueryReady) {
    }
    public record ProgressReadiness(boolean playerBindingReady, boolean guiRootReady, boolean exactWidgetSetReady, boolean sameFrameReady, boolean queryReady, boolean productionLiveReady) {
    }
    public record B1Frame(Header header, CharacterId managerCharacterId, B1Cycle cycle, B1Roster roster, B1Processing processing, B1Quota quota, B1Closure closure, B1Pending pending, B1Readiness readiness) implements Frame {
    }
    public record CaseFrame(Header header, CharacterId subjectCharacterId, Optional<CharacterId> requestedOwnerCharacterId, CaseIdentity caseRecord, Policy policy, Operation operation, Receipt receipt, Deadline deadline, CaseReadiness readiness) implements Frame {
    }
    public record AiOwnedFrame(Header header, CharacterId subjectCharacterId, CharacterId requestedOwnerCharacterId, CaseIdentity caseRecord, OwnerEligibility ownerEligibility, Stage stage, Route route, Policy policy, Operation operation, Receipt receipt, AiOwnedReadiness readiness) implements Frame {
    }
    public record ResultFrame(Header header, CharacterId subjectCharacterId, CharacterId requestedOwnerCharacterId, ResultIdentity caseRecord, Notice notice, Delivery delivery, ResultReadiness readiness) implements Frame {
    }
    public record PipFrame(Header header, CharacterId subjectCharacterId, CharacterId requestedOwnerCharacterId, PipGate gate, PipPip pip, PipResponse response, PipSupport support, PipBudgetLedger budgetLedger, PipD180Ticket d180Ticket, PipD365Ticket d365Ticket, PipMidpoint midpoint, PipOutcome outcome, PipNextCycleEvidence nextCycleEvidence, Field<Boolean> pipModifierPresent, PipReadiness readiness) implements Frame {
    }
    public record PromotionFrame(Header header, CharacterId subjectCharacterId, PromotionCompensation promotionCompensation, PromotionReadiness readiness) implements Frame {
    }
    public record Af5Frame(Header header, CharacterId subjectCharacterId, Af5 af5, boolean terminal, Af5Readiness readiness) implements Frame {
    }
    public record ProjectsFrame(Header header, CharacterId requestedOwnerCharacterId, CharacterId requestedSubjectCharacterId, CheckpointState checkpointState, ProjectPortfolio creditProjectPortfolio, ProjectIdentity sourceIdentity, ProjectIdentity resultIdentity, ProjectsMetrics projectsMetrics, ProjectsReadiness readiness) implements Frame {
    }
    public record IncidentFrame(Header header, CharacterId subjectCharacterId, CharacterId requestedOwnerCharacterId, IncidentProfile profile, Probe probe, Resources resources, Terminal terminal, Kpi kpi, IncidentReadiness readiness) implements Frame {
    }
    public record ScoreboardFrame(Header header, String treeFingerprintV1, String semanticFingerprintV1, String providerSessionId, BigInteger observationSequence, BigInteger observedStateRevision, List<Widget> widgets, Acl acl, ReadOnlyActions actions, ScoreboardReadiness readiness) implements Frame {
        public ScoreboardFrame { widgets = List.copyOf(widgets); }
    }
    public record ProgressFrame(Header header, List<ProgressWidget> widgets, ProgressReadiness readiness) implements Frame {
        public ProgressFrame { widgets = List.copyOf(widgets); }
    }
}

