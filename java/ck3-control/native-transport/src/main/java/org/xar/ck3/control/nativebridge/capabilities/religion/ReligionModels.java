package org.xar.ck3.control.nativebridge.capabilities.religion;

import java.math.BigInteger;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedPostcondition;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;

/** Native data remains exact integer data; nullable fields represent observed JSON null, never absence. */
public final class ReligionModels {
    private ReligionModels() { }
    public enum Build {
        CROZIER3("1.20.0.3", "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6"),
        CROZIER4("1.20.0.4", "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518");
        private final String version, sha256;
        Build(String version, String sha256) { this.version = version; this.sha256 = sha256; }
        public String version() { return version; }
        public String sha256() { return sha256; }
    }
    public enum Decision {
        ADOPT("adopt", "adopt_holy_site_decision"), PROMOTE("promote", "elevate_holy_site_decision"),
        DEMOTE("demote", "demote_holy_site_decision"), ABANDON("abandon", "abandon_holy_site_decision");
        private final String wire, key;
        Decision(String wire, String key) { this.wire = wire; this.key = key; }
        public String wire() { return wire; }
        public String key() { return key; }
        public static Decision parse(String value) {
            for (Decision candidate : values()) if (candidate.wire.equals(value)) return candidate;
            throw new IllegalArgumentException("unknown fixed HolySite decision");
        }
    }
    public record FullId(BigInteger value) {
        public FullId { ReligionJson.range(value, BigInteger.ZERO, ReligionJson.U32.subtract(BigInteger.ONE)); }
        public FullId(long value) { this(BigInteger.valueOf(value)); }
    }
    public record PositiveId(int value) {
        public PositiveId { ReligionJson.need(value > 0, "positive native identity required"); }
    }
    public record OwnerId(String value) {
        public OwnerId { ReligionJson.need(value != null && !value.isEmpty() && value.getBytes(java.nio.charset.StandardCharsets.UTF_8).length <= 63, "owner identity must contain 1..63 UTF-8 bytes"); }
    }
    public record PreviewIdentity(String sha256) {
        public PreviewIdentity { ReligionJson.need(sha256 != null && sha256.matches("[a-f0-9]{64}"), "observed lowercase preview SHA256 required"); }
    }
    /** Authority is still verified by the real coordinator guard against the held pipe. */
    public record Context(ObservationIdentity before, G2Source source, String sessionId,
            BigInteger connectionGeneration, Build build, Instant deadline) {
        public Context {
            Objects.requireNonNull(before); Objects.requireNonNull(source); Objects.requireNonNull(build); Objects.requireNonNull(deadline);
            ReligionJson.need(sessionId != null && !sessionId.isEmpty(), "actual held session required");
            ReligionJson.range(connectionGeneration, BigInteger.ONE, ReligionJson.U64);
            ReligionJson.need(before.machineId().equals(source.machineId()), "source machine drift");
        }
    }
    public record ActionContext(Context frame, String actionId, ExpectedPostcondition expected, Claims claims) {
        public ActionContext { Objects.requireNonNull(frame); Objects.requireNonNull(expected); Objects.requireNonNull(claims); }
    }
    public record Availability(boolean available, String reason) { }
    public record Frame(Build build, BigInteger captureEpoch, BigInteger nativeRevision, BigInteger dateRaw,
            BigInteger playerId, Availability availability) { }
    public record Sample<T>(boolean observed, T value) { }
    public enum Presence { ABSENT, NULL, VALUE }
    public record Additive<T>(Presence presence, T value) { }
    public record TypeCandidate(String key, boolean selected, Sample<Boolean> canPick, Sample<String> tooltip) { }
    public record CreationContext(Frame frame, BigInteger playerFaithId, BigInteger windowFaithId,
            Boolean windowPresent, Boolean rootPresent, Boolean playerFaithMatches,
            boolean modelsAvailable, boolean modelsComplete, List<TypeCandidate> types,
            List<BigInteger> potentialBaronyIds, List<BigInteger> enshrinableArtifactIds,
            boolean selectionAvailable, String selectedType, BigInteger selectedBarony,
            List<BigInteger> selectedArtifacts, Sample<BigInteger> raritySum, Sample<Boolean> nativeEnabled,
            Sample<BigInteger> bypass, Sample<Boolean> normalRequirements, Sample<String> tooltip,
            Sample<List<BigInteger>> cachedResources, Additive<PreviewIdentity> preview) {
        public CreationContext {
            types = copyNullable(types); potentialBaronyIds = copyNullable(potentialBaronyIds);
            enshrinableArtifactIds = copyNullable(enshrinableArtifactIds); selectedArtifacts = copyNullable(selectedArtifacts);
        }
    }
    public record Cooldown(String decisionKey, boolean present, Integer expiryRaw, int currentCounterRaw, boolean active) { }
    public record CooldownResult(Frame frame, Decision action, Sample<Cooldown> cooldown) { }
    public record ResourceQuote(List<BigInteger> vector, BigInteger gold, BigInteger prestige,
            BigInteger piety, BigInteger treasury, boolean nativeAffordable) {
        public ResourceQuote { vector = List.copyOf(vector); }
    }
    public record Description(boolean available, String text, String reason) { }
    public record DecisionDetail(Frame frame, Decision action, BigInteger holySiteId, String actualDecisionKey,
            Boolean nativeCanConfirm, Boolean normalCanConfirm, boolean detailContextVerified,
            Sample<ResourceQuote> quote, Additive<Description> requirementsDescription,
            Additive<Description> costDescription, Additive<Sample<Cooldown>> cooldown,
            Integer candidateCount, Integer selectedIndex, BigInteger selectedItemToken,
            Sample<BigInteger> bypass, Description confirmTooltip) { }
    public record IndulgenceIdentity(Availability availability, BigInteger requestedRecipient,
            Integer actor, Integer recipient, Integer secondaryActor, Integer secondaryRecipient,
            Integer intermediary, Integer sixthRole) { }
    public record IndulgenceOptions(Availability availability, BigInteger declaredCount,
            BigInteger selectedCount, Boolean allUnselected) { }
    public record IndulgenceBoolean(Availability availability, Boolean value) { }
    public record IndulgenceTerms(Frame frame, BigInteger definitionStableHash, IndulgenceIdentity identity,
            IndulgenceOptions options, IndulgenceBoolean shown, IndulgenceBoolean canSend) { }
    public record Stress(Frame frame, int baseAmount, Integer currentPoints, BigInteger gainModifier,
            BigInteger lossModifier, Integer adjustedDelta, long ownerThreadId, BigInteger ownerPumpEpoch,
            boolean sourcePins, boolean actorBinding, boolean ownerThread, boolean tls, boolean frameVerified) { }
    public record EpidemicCounty(BigInteger titleId, boolean minorPresent, boolean tinyPresent) { }
    public record EpidemicResult(BigInteger nativeRevision, BigInteger dateRaw, BigInteger playerId,
            int requestedTitleId, Availability availability, List<EpidemicCounty> counties) {
        public EpidemicResult { counties = copyNullable(counties); }
    }
    public sealed interface EpidemicTarget permits EventCounties, ExplicitTitle { }
    public record EventCounties(BigInteger eventInstanceId) implements EpidemicTarget {
        public EventCounties { ReligionJson.need(eventInstanceId != null && eventInstanceId.signum() > 0, "actual positive event instance required"); }
    }
    public record ExplicitTitle(PositiveId titleId) implements EpidemicTarget { public ExplicitTitle { Objects.requireNonNull(titleId); } }
    public enum LinkState { UNKNOWN, ABSENT, PRESENT }
    public record GhwVariable(String key, String scope, boolean readAvailable, Boolean present,
            Boolean timed, Integer expiry, Integer currentCounter, Integer remaining,
            Integer valueKind, BigInteger numericValue, String failure) { }
    public record GhwVariables(boolean anyObserved, boolean allObserved, boolean frameVerified,
            boolean stableTwoPass, String failure, List<GhwVariable> fields) {
        public GhwVariables { fields = List.copyOf(fields); }
    }
    public record GhwLinks(boolean available, boolean stableTwoPass, LinkState ghw, LinkState war,
            String failure, BigInteger ghwFullId, BigInteger warFullId, Boolean offensiveGhw, Boolean warStarted) { }
    public record GhwPermissions(Frame frame, BigInteger faithId, BigInteger religionId,
            boolean sourcePins, boolean frameVerified, GhwVariables variables, GhwLinks links) { }
    public enum SubmitStatus { NOT_SUBMITTED, ALREADY_TARGET_NOOP, ALREADY_ACTIVE_NOOP, QUEUED_VERIFICATION_PENDING }
    public record ReligionIntent(BigInteger expectedRevision, FullId targetRite, BigInteger maximumPiety, OwnerId actionId) { }
    public record CountyIntent(BigInteger expectedRevision, PositiveId activeTask, PositiveId incumbent,
            PositiveId province, boolean replaceExisting, OwnerId actionId) { }
    public record TaskState(boolean available, String failure, BigInteger captureEpoch, int dateRaw,
            int ownerId, String taskKey, Integer incumbent, Integer activeTask, Integer province,
            Integer countyTitle, Integer progressKind, Integer scopeTag, BigInteger percentageProgress) { }
    public record CountyOwner(CountyIntent request, OwnerId requestId, BigInteger nativeRevision,
            int dateRaw, BigInteger captureEpoch, int playerId, boolean submitCopyCalled,
            SubmitStatus status, String failure, Boolean nativeCanDispatch, Integer targetCounty,
            TaskState before) { }
    public record CountyResult(Frame frame, CountyOwner owner, TaskState after, Boolean assignmentMatches,
            Boolean taskIdUnchanged, boolean materialObserved, boolean verificationPending) { }
    public record ReligionContext(boolean available, BigInteger riteId, BigInteger faithId) { }
    public record ReligionActor(boolean available, ReligionContext religion, BigInteger piety,
            BigInteger gold, BigInteger prestige) { }
    public record ReligionOutcome(BigInteger captureEpoch, ReligionActor actor) { }
    public record PaidTerms(BigInteger captureEpoch, boolean canConvert, BigInteger pietyCost,
            BigInteger targetFaithId) { }
    public record ReligionOwner(ReligionIntent request, OwnerId requestId, BigInteger nativeRevision,
            int dateRaw, BigInteger captureEpoch, BigInteger playerId, boolean submitCopyCalled,
            SubmitStatus status, ReligionOutcome before, PaidTerms paidTerms) { }
    public record ConversionResult(Frame frame, ReligionOwner owner, ReligionOutcome after,
            Boolean preexisting, Boolean riteChanged, Boolean targetReached, Boolean faithReached,
            BigInteger pietyDelta, BigInteger goldDelta, BigInteger prestigeDelta,
            boolean materialObserved, boolean verificationPending) { }
    public record Member(BigInteger characterId, BigInteger riteId, BigInteger faithId, Boolean alive,
            Boolean adult, Boolean imprisoned, Boolean incapable, Boolean ai, Integer learning,
            Integer adultMeasure, Integer adultSelector, Integer adultThreshold, boolean complete, String reason) { }
    public record RiteCounties(BigInteger riteId, List<BigInteger> countyIds, Integer count, boolean complete, String reason) {
        public RiteCounties { countyIds = copyNullable(countyIds); }
    }
    public record Assembly(Frame frame, boolean complete, BigInteger faithId, BigInteger playedRiteId,
            BigInteger religionId, Integer alivePoolCount, Integer countyPoolCount,
            List<BigInteger> memberIds, List<BigInteger> riteIds, List<Member> members, List<RiteCounties> rites) {
        public Assembly { memberIds = copyNullable(memberIds); riteIds = copyNullable(riteIds); members = copyNullable(members); rites = copyNullable(rites); }
    }
    public record TitleProperties(Availability availability, Boolean destroyInvalidHeir, Boolean noClaims,
            Boolean definitiveForm, Boolean followsPrimaryHeir) { }
    public record Law(BigInteger definitionId, String key) { }
    public record TitleLaws(Availability availability, Integer nativeCount, List<Law> laws, Boolean expectedMember) {
        public TitleLaws { laws = copyNullable(laws); }
    }
    public record TitleHolder(Availability availability, Integer tierRaw, String tierKey, BigInteger holderId,
            Boolean isPlayer, Boolean inRealm, BigInteger immediateLiege, BigInteger topLiege) { }
    public record ReligiousTitle(Frame frame, BigInteger playerFullId, boolean graphAvailable,
            Boolean legalHeadAbsent, BigInteger faithId, BigInteger titleId, BigInteger nativeHolderId,
            Boolean nativeHolderAbsent, String nativeClass, TitleHolder holder,
            TitleProperties properties, TitleLaws laws) { }
    public record GraphTitle(boolean absent, BigInteger titleId, String nativeClass, Boolean holderAbsent,
            BigInteger holderId, BigInteger holderFaithId, TitleProperties properties, TitleLaws laws) { }
    public record Challenger(BigInteger titleId, GraphTitle title, GraphTitle registeredSponsor,
            BigInteger scopeFaithId, int scopeNativeCount, boolean scopeFaithMatches,
            boolean scopeMatchesRegistered, GraphTitle scopeSponsor) { }
    public record FaithChallengers(BigInteger faithId, int count, List<BigInteger> titleIds, List<Challenger> challengers) {
        public FaithChallengers { titleIds = List.copyOf(titleIds); challengers = List.copyOf(challengers); }
    }
    public record ChallengerGraph(Frame frame, BigInteger playerFullId, boolean complete,
            List<BigInteger> requestedFaiths, List<FaithChallengers> faiths) {
        public ChallengerGraph { requestedFaiths = List.copyOf(requestedFaiths); faiths = copyNullable(faiths); }
    }
    private static <T> List<T> copyNullable(List<T> value) { return value == null ? null : List.copyOf(value); }
}
