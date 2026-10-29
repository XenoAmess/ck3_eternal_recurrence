package org.xar.ck3.control.nativebridge.capabilities.interactions;

import org.xar.ck3.control.contracts.NativeCharacterId;

import java.math.BigInteger;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedPostcondition;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;

/** Closed domain objects. Null fields below mean an explicitly observed JSON null, never a missing field. */
public final class InteractionModels {
    private InteractionModels() { }
    public enum Build {
        WANDERER6("1.19.0.6","2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"),
        CROZIER2("1.20.0.2","AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D"),
        CROZIER3("1.20.0.3","94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6"),
        CROZIER4("1.20.0.4","98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518");
        private final String version, sha;
        Build(String version, String sha) { this.version=version; this.sha=sha; }
        public String version() { return version; }
        public String sha256() { return sha; }
    }
    public record FullId(long value) {
        public FullId { InteractionJson.need(value >= 0 && value < 0xffff_ffffL,"full uint32 ID below invalid sentinel required"); }
    }
    public record CharacterId(long value) {
        public CharacterId { InteractionJson.need(value > 0 && value < 0xffff_ffffL,"positive full CharacterID required"); }
    }
    public record Int32Id(int value) {
        public Int32Id { InteractionJson.need(value >= 0,"nonnegative full int32 ID required"); }
    }
    public record PendingId(int value) {
        public PendingId { org.xar.ck3.control.contracts.semantic.NativePendingInteraction.requireInstanceId(value); }
    }
    public record InteractionKey(String value) {
        public InteractionKey { InteractionJson.need(value != null && value.matches("[A-Za-z0-9_]{1,128}"),"exact ASCII interaction key required"); }
    }
    public record Signature(String value) {
        public Signature { InteractionJson.need(value != null && value.matches("[0-9a-f]{64}"),"lowercase SHA256 signature required"); }
    }
    public record CreationFiletime(String decimal) {
        public CreationFiletime { InteractionJson.need(decimal != null && decimal.matches("[1-9][0-9]{0,19}"),"canonical decimal FILETIME required"); InteractionJson.range(new BigInteger(decimal),BigInteger.ONE,InteractionJson.U64); }
        public BigInteger integer() { return new BigInteger(decimal); }
    }
    /** Actual source/frame binding is rechecked inside the one coordinator writer lock. */
    public record Context(ObservationIdentity before, G2Source source, String sessionId,
            BigInteger connectionGeneration, Build build, Instant deadline, ControlFrame controls) {
        public Context {
            Objects.requireNonNull(before); Objects.requireNonNull(source); Objects.requireNonNull(build); Objects.requireNonNull(deadline); Objects.requireNonNull(controls);
            InteractionJson.need(sessionId != null && !sessionId.isEmpty(),"held native session required");
            InteractionJson.range(connectionGeneration,BigInteger.ONE,InteractionJson.U64);
            InteractionJson.need(before.machineId().equals(source.machineId()),"source machine drift");
        }
        public BigInteger revision() { return before.frame().identity().nativeRevision(); }
        public BigInteger actor() { return before.frame().identity().player(); }
        public BigInteger date() { return before.frame().identity().dateRaw(); }
    }
    public record ActionContext(Context frame, String actionId, ExpectedPostcondition expected, Claims claims) {
        public ActionContext { Objects.requireNonNull(frame); Objects.requireNonNull(expected); Objects.requireNonNull(claims); }
    }
    /** Native full control projection retained separately from an action ACK. */
    public record ControlFrame(boolean paused, boolean mapReady, boolean alive, int speed,
            Long localPlayerId, long episodeCharacterId, String episodeRunId, boolean activeEvent,
            PendingSummary pending, Long betrothedId, List<Long> spouseIds) {
        public ControlFrame { spouseIds=List.copyOf(spouseIds); InteractionJson.need(episodeRunId != null && !episodeRunId.isEmpty(),"episode required"); }
    }
    public record PendingSummary(PendingId instance, NativeCharacterId sender, boolean autoAcceptNotification) { }
    public record Availability(boolean available, String reason) {
        public Availability { InteractionJson.need(available ? reason == null : reason != null && !reason.isEmpty(),"availability must preserve reason/null semantics"); }
    }
    public record Frame(BigInteger revision, BigInteger date, BigInteger actor, Build build, BigInteger querySequence) { }
    public record MarriageChoice(String choiceId, long player, long candidate) {
        public MarriageChoice {
            InteractionJson.need(player>=0 && candidate>=0 && player!=candidate,"distinct native marriage identities required");
            InteractionJson.need((player+"-"+candidate).equals(choiceId),"choice must preserve canonical pair identity");
        }
    }
    public record MarriageChoices(Frame frame, List<MarriageChoice> choices) {
        public MarriageChoices { choices=List.copyOf(choices); }
    }
    public enum RelationshipOutcome { UNKNOWN, ACCEPTED_BETROTHAL, ACCEPTED_MARRIAGE }
    public record OwnLaw(long definitionId, String key) { }
    public record TitleOwnLaws(Frame frame, FullId title, Availability availability, Integer nativeLawCount,
            List<OwnLaw> laws, Boolean singleHeirMember) {
        public TitleOwnLaws { laws=copyNullable(laws); }
    }
    public enum ClaimState { ABSENT, STRONG_IMPLICIT, STRONG_EXPLICIT, WEAK_IMPLICIT, WEAK_EXPLICIT }
    public record ClaimRow(Int32Id title, ClaimState state, Boolean strong, Boolean implicit) { }
    public record PlayerClaims(Frame frame, List<Int32Id> requestedTitles, Availability availability, List<ClaimRow> claims) {
        public PlayerClaims { requestedTitles=List.copyOf(requestedTitles); claims=copyNullable(claims); }
    }
    public enum Tier { BARONY, COUNTY, DUCHY, KINGDOM, EMPIRE, HEGEMONY }
    public record TitleHolder(Frame frame, Int32Id title, Availability availability, Tier tier, Integer holder,
            Boolean isPlayer, Boolean inPlayerRealm, Integer immediateLiege, Integer topLiege,
            Optional<String> titleKey, Optional<String> titleKeyUnavailableReason) { }
    public record OrdinaryRequest(InteractionKey interaction, CharacterId recipient, Optional<EducationIntent> education) {
        public OrdinaryRequest {
            Objects.requireNonNull(interaction); Objects.requireNonNull(recipient); education=Objects.requireNonNull(education);
            InteractionJson.need(education.isEmpty() || interaction.value().equals("educate_child_interaction"),"education fields require original education interaction");
        }
    }
    /** Empty option keys and absent option intent remain different. */
    public record EducationIntent(Optional<CharacterId> child, Optional<CharacterId> guardian, Optional<List<InteractionKey>> options) {
        public EducationIntent {
            child=Objects.requireNonNull(child); guardian=Objects.requireNonNull(guardian); options=Objects.requireNonNull(options).map(List::copyOf);
            InteractionJson.need(child.isPresent()==guardian.isPresent(),"education pair must be complete");
        }
    }
    public record Roles(Long actor, Long recipient, Long secondaryActor, Long secondaryRecipient, Long intermediary, Long sixth) { }
    public record OrdinaryProofs(boolean sourcePins, boolean actor, boolean recipient, boolean owner, boolean tls, boolean frame,
            long ownerThread, BigInteger pumpEpoch) {
        public boolean complete() { return sourcePins && actor && recipient && owner && tls && frame && ownerThread>0 && pumpEpoch.signum()>0; }
    }
    public record EducationOption(int ordinal, long flag, String canonicalKey, boolean selected, int bankByte, boolean ordinalSelected) { }
    public record EducationOptions(Availability availability, List<EducationOption> rows) { public EducationOptions { rows=List.copyOf(rows); } }
    public record EducationMaterialization(Availability availability, Long child, Long guardian, List<String> optionKeys, Boolean pairMatches, Boolean optionKeysMatch) {
        public EducationMaterialization { optionKeys=copyNullable(optionKeys); }
    }
    public record OrdinaryTerms(boolean actorAlive, boolean recipientAlive, long definitionHash, long declaredOptions, long selectedOptions,
            boolean specialPayload, boolean shown, boolean canSend, List<BigInteger> costsRaw, boolean autoAccept,
            BigInteger recipientScoreRaw, BigInteger intermediaryScoreRaw, int outerAnswer) {
        public OrdinaryTerms { costsRaw=List.copyOf(costsRaw); }
    }
    public record OrdinaryContext(Frame frame, OrdinaryRequest request, Availability availability, OrdinaryProofs proofs, Roles roles,
            OrdinaryTerms terms, boolean contextAvailable, boolean ordinarySupported, boolean activeEvent, boolean incomingInteraction,
            boolean readyToInitiate, String unsupportedReason, Optional<EducationOptions> educationOptions,
            Optional<EducationMaterialization> educationMaterialization) { }
    public enum QueueResult { NOT_ATTEMPTED, UNAVAILABLE, REJECTED, SUBMITTED }
    public record OrdinaryInitiation(OrdinaryContext preflight, boolean nativeCallCompleted, boolean dispatchInvoked,
            QueueResult queue, boolean queueSubmitted, boolean verificationPending, String reason) {
        public boolean businessPostconditionVerified() { return false; }
    }
    public enum ControlAction {
        QUERY_CONTEXT("query_context"), OPEN_PAUSE_MENU("open_pause_menu"), OPEN_SWITCH("open_switch"), CHOOSE_CHARACTER("choose_character"), CONFIRM_CONTROL("confirm_control");
        private final String wire; ControlAction(String wire) { this.wire=wire; } public String wire() { return wire; }
    }
    public enum ControlPhase { UNAVAILABLE, MAP, PAUSE_MENU, SWITCH_CHOOSER, CONTROL_CONFIRMED }
    public enum ControlStatus { UNAVAILABLE, CONTEXT_OBSERVED, DISPATCH_PENDING, DISPATCH_UNKNOWN_CLAIMED, CONTROL_OBSERVED }
    public record ControlSource(CreationFiletime creationFiletime, Signature inventorySha256, ExactRef verifiedInventory) {
        public ControlSource { Objects.requireNonNull(creationFiletime); Objects.requireNonNull(inventorySha256); Objects.requireNonNull(verifiedInventory); InteractionJson.need(verifiedInventory.bytes()>0,"actual verified source inventory evidence required"); }
    }
    public record ControlRequest(ControlAction action, Optional<Signature> contextSignature, Optional<CharacterId> candidate, ControlSource source) {
        public ControlRequest {
            Objects.requireNonNull(action); contextSignature=Objects.requireNonNull(contextSignature); candidate=Objects.requireNonNull(candidate); Objects.requireNonNull(source);
            InteractionJson.need((action==ControlAction.QUERY_CONTEXT)==contextSignature.isEmpty(),"mutation requires actual latest control signature");
            InteractionJson.need((action==ControlAction.CHOOSE_CHARACTER || action==ControlAction.CONFIRM_CONTROL)==candidate.isPresent(),"candidate only on choose/confirm");
        }
    }
    public record ControlProofs(boolean exactBuild, boolean owner, boolean process, boolean sourceAbi,
            boolean stockFiles, boolean loadedSource, boolean frame) {
        public boolean complete() { return exactBuild && owner && process && sourceAbi && stockFiles && loadedSource && frame; }
    }
    public record Controller(Long player, Long character, Boolean current, Boolean ai) { }
    public record ControlCandidate(Long character, BigInteger playableId, Boolean ruler, Boolean canControl, Boolean visible, Boolean enabled, Boolean sourceVerified) { }
    public record ControlTarget(boolean readComplete, boolean rootExists, boolean rootVisible, boolean targetExists, boolean targetVisible,
            boolean targetEnabled, boolean unique, boolean dispatchAdmitted, BigInteger vtableRva) { }
    public record ControlDispatch(boolean claimLatched, boolean invoked, boolean handled, boolean postReadComplete, boolean postcondition) { }
    public record ControlObservation(ControlAction action, ControlStatus status, ControlPhase phase, ControlProofs proofs,
            BigInteger pumpEpoch, String signature, String flowId, Long sourceCharacter, Long targetCharacter,
            Long flowLocalPlayer, boolean flowComplete, Long localPlayer, Long controlledCharacter, Long selectedCharacter,
            Boolean controlledAi, Boolean ironman, Boolean multiplePlayers, boolean controllersComplete, List<Controller> controllers,
            boolean candidatesComplete, List<ControlCandidate> candidates, List<ControlTarget> targets, List<ControlDispatch> dispatches,
            List<Boolean> stageConsumed, boolean signatureVerified, boolean controlVerified, String reason) {
        public ControlObservation { controllers=List.copyOf(controllers); candidates=List.copyOf(candidates); targets=List.copyOf(targets); dispatches=List.copyOf(dispatches); stageConsumed=List.copyOf(stageConsumed); }
    }
    public enum GrantOperation { QUERY, PREPARE, SELECT, SEND;
        public String wire() { return name().toLowerCase(java.util.Locale.ROOT); }
    }
    public record GrantRequest(GrantOperation operation, CharacterId recipient, List<FullId> targets, List<FullId> expectedSelected,
            Optional<FullId> title, Optional<Boolean> desiredSelected) {
        public GrantRequest {
            Objects.requireNonNull(operation); Objects.requireNonNull(recipient); targets=List.copyOf(targets); expectedSelected=List.copyOf(expectedSelected);
            title=Objects.requireNonNull(title); desiredSelected=Objects.requireNonNull(desiredSelected);
            InteractionJson.unique(targets,64); InteractionJson.unique(expectedSelected,64);
            InteractionJson.need((operation==GrantOperation.SELECT)==title.isPresent() && title.isPresent()==desiredSelected.isPresent(),"select requires explicit title and actual boolean");
            InteractionJson.need(operation!=GrantOperation.SEND || (!expectedSelected.isEmpty() && new java.util.HashSet<>(targets).equals(new java.util.HashSet<>(expectedSelected))),"send requires complete exact selected title set");
            InteractionJson.need((operation!=GrantOperation.QUERY && operation!=GrantOperation.PREPARE) || expectedSelected.isEmpty(),"query/prepare cannot assume selection");
        }
    }
    public record GrantRow(FullId title, Long holder, boolean selected, boolean selectable) { }
    public record GrantHolder(FullId title, boolean available, Long holder) { }
    public record GrantWindow(boolean available, boolean visible, boolean bound, boolean complete, Boolean canSend, Boolean warning,
            List<GrantRow> rows, List<FullId> selected, List<GrantHolder> holders) {
        public GrantWindow { rows=List.copyOf(rows); selected=List.copyOf(selected); holders=List.copyOf(holders); }
    }
    public enum GrantStatus { UNAVAILABLE, OBSERVED, PREPARED, SELECTION_OBSERVED, SELECTION_CHANGED_OBSERVED, HOLDER_TRANSFER_OBSERVED, PENDING }
    public record GrantResult(GrantOperation operation, GrantStatus status, boolean ownerVerified, boolean frameVerified, boolean sourcePins,
            boolean dispatched, boolean nativeCompleted, boolean selectionVerified, boolean transferVerified, GrantWindow before, GrantWindow after,
            String unavailableReason) { }
    public record AppointmentRequest(Optional<CharacterId> title, int offset, int limit, Optional<CharacterId> breakdown, Optional<CharacterId> diagnostic) {
        public AppointmentRequest {
            title=Objects.requireNonNull(title); breakdown=Objects.requireNonNull(breakdown); diagnostic=Objects.requireNonNull(diagnostic);
            InteractionJson.need(offset>=0 && offset<=4096 && limit>=1 && limit<=64,"appointment page outside original bounds");
        }
    }
    public record AppointmentCandidate(CharacterId character, int listIndex, int nativeRank, BigInteger scoreRaw,
            boolean alive, boolean human, boolean ai, boolean scorePresent) { }
    public record ScoreNode(String text0, String text1, String text2, BigInteger value, BigInteger factor, int mode, int flags, List<ScoreNode> children) { public ScoreNode { children=List.copyOf(children); } }
    public record NativeLevel(Availability availability, Long character, Long title, Integer sourceOrdinal,
            Boolean extensionPresent, BigInteger accumulated, Integer cap, Integer nativeLevel, Integer titleTier,
            Integer requiredLevel, Boolean meetsFloor, Optional<Integer> allowedTierOrdinal, Optional<Integer> candidateTier) { }
    public record Appointment(CharacterId currentTitle, CharacterId holder, String titleKey, String successionLaw, int fullCount,
            int nextOffset, String poolToken, List<AppointmentCandidate> candidates, boolean breakdownAvailable, ScoreNode breakdown,
            Optional<NativeLevel> nativeLevel) {
        public Appointment { candidates=List.copyOf(candidates); }
    }
    public record HeirSubject(CharacterId firstHeir, BigInteger rootQuerySequence, ExactRef originalCampaignRoot) {
        public HeirSubject { Objects.requireNonNull(firstHeir); InteractionJson.range(rootQuerySequence,BigInteger.ONE,InteractionJson.U64); Objects.requireNonNull(originalCampaignRoot); InteractionJson.need(originalCampaignRoot.bytes()>0,"actual public campaign-root subject required"); }
    }
    public record HeirMarriageCandidate(CharacterId character, CharacterId matchmaker, long intermediary, boolean nativeLegal, BigInteger scoreRaw,
            int answerStatus, Short heirAdultMeasure, Short candidateAdultMeasure, BigInteger playerDynasty, BigInteger heirDynasty, BigInteger candidateDynasty, Boolean realmBacked) { }
    public record HeirMarriageLegality(Frame frame, HeirSubject subject, Availability availability, List<HeirMarriageCandidate> candidates,
            long slotsScanned, long storageCapacity, long subjectRoleMismatches) {
        public HeirMarriageLegality { candidates=List.copyOf(candidates); }
    }
    public sealed interface Mutation permits PendingReply, Marriage, Ordinary, SetPlayer, PlayerControl, Grant { }
    public record PendingReply(PendingId instance, boolean accept, boolean acknowledge) implements Mutation { }
    public record Marriage(MarriageChoice choice, BigInteger querySequence) implements Mutation {
        public Marriage { Objects.requireNonNull(choice); InteractionJson.range(querySequence,BigInteger.ONE,InteractionJson.U64); }
    }
    public record Ordinary(OrdinaryRequest request) implements Mutation { public Ordinary { Objects.requireNonNull(request); } }
    public record SetPlayer(CharacterId target) implements Mutation { public SetPlayer { Objects.requireNonNull(target); } }
    public record PlayerControl(ControlRequest request) implements Mutation { public PlayerControl { Objects.requireNonNull(request); InteractionJson.need(request.action()!=ControlAction.QUERY_CONTEXT,"query is not a mutation"); } }
    public record Grant(GrantRequest request) implements Mutation { public Grant { Objects.requireNonNull(request); InteractionJson.need(request.operation()!=GrantOperation.QUERY,"query is not a mutation"); } }
    public sealed interface GrantReply permits GrantRead, GrantAction { }
    public record GrantRead(org.xar.ck3.control.application.action.PlanningReadResult<GrantResult> result) implements GrantReply { }
    public record GrantAction(ActionReceipt receipt) implements GrantReply { }
    private static <T> List<T> copyNullable(List<T> value) { return value==null?null:List.copyOf(value); }
}
