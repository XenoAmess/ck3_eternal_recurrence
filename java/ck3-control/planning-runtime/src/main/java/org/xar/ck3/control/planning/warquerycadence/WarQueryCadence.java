package org.xar.ck3.control.planning.warquerycadence;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.NativeInteractionRoles;

/** Pure scheduling policy. A defer grants neither native legality nor action credit. */
public final class WarQueryCadence {
    private static final BigInteger LEASE_RAW = BigInteger.valueOf(30L * 24L);
    private static final BigInteger HUNDRED = BigInteger.valueOf(100);
    private static final String QUERY_PREFIX = "query-war-termination-options-";

    private WarQueryCadence() { }

    public enum Side { ATTACKER, DEFENDER }

    public record CasusBelli(BigInteger databaseIndex, String canonicalKey) {
        public CasusBelli {
            nonnegative(databaseIndex, "databaseIndex");
            text(canonicalKey, "canonicalKey");
        }
    }

    public record ScoreBreakdown(BigInteger imprisonment, BigInteger battles,
                                 BigInteger occupation, BigInteger ticking) {
        public ScoreBreakdown {
            Objects.requireNonNull(imprisonment); Objects.requireNonNull(battles);
            Objects.requireNonNull(occupation); Objects.requireNonNull(ticking);
        }
    }

    /** Nullable leader/opponent preserve explicitly unknown source observations. */
    public record War(BigInteger warId, Side playerSide, Boolean primaryLeader,
                      BigInteger opponentId, BigInteger score, List<BigInteger> targetedTitleIds,
                      CasusBelli currentCasusBelli) {
        public War {
            positive(warId, "warId"); Objects.requireNonNull(playerSide);
            Objects.requireNonNull(score); targetedTitleIds = List.copyOf(targetedTitleIds);
            if (opponentId != null) { nonnegative(opponentId, "opponentId"); }
            targetedTitleIds.forEach(id -> nonnegative(id, "targetedTitleId"));
        }
        StableWar stable() { return new StableWar(warId, playerSide, primaryLeader, opponentId, targetedTitleIds); }
    }

    public record StableWar(BigInteger warId, Side side, Boolean primaryLeader,
                            BigInteger opponentId, List<BigInteger> targetedTitleIds) {
        public StableWar {
            positive(warId, "warId"); Objects.requireNonNull(side);
            if (opponentId != null) { nonnegative(opponentId, "opponentId"); }
            targetedTitleIds = List.copyOf(targetedTitleIds);
            targetedTitleIds.forEach(id -> nonnegative(id, "targetedTitleId"));
        }
    }

    public record Snapshot(boolean paused, boolean mapReady, boolean terminalReasonPresent,
                           boolean activeEventPresent, boolean interactionPresent, boolean exclusiveModalPresent,
                           BigInteger actorId, boolean actorAlive, BigInteger dateRaw,
                           String episodeRunId, BigInteger connectionGeneration) {
        public Snapshot {
            positive(actorId, "actorId"); positive(dateRaw, "dateRaw");
            text(episodeRunId, "episodeRunId"); positive(connectionGeneration, "connectionGeneration");
        }
    }

    public record RecipientResponse(String status, BigInteger decisionStatusRaw, Boolean wouldAcceptNow) {
        public RecipientResponse { text(status, "status"); }
    }

    public record OptionSignature(String outcome, String hostageVariant, Boolean contextConstructed,
                                  Boolean nativeValidatorPassed, Boolean available, RecipientResponse recipientResponse,
                                  NativeInteractionRoles recipientContext) {
        public OptionSignature {
            text(outcome, "outcome"); text(hostageVariant, "hostageVariant");
            Objects.requireNonNull(recipientResponse); Objects.requireNonNull(recipientContext);
        }
        public OptionSignature(String outcome, String hostageVariant, Boolean contextConstructed,
                               Boolean nativeValidatorPassed, Boolean available, RecipientResponse recipientResponse) {
            this(outcome, hostageVariant, contextConstructed, nativeValidatorPassed, available, recipientResponse,
                    new NativeInteractionRoles.LegacyWithoutRoles());
        }
    }

    public record OptionsSignature(OptionSignature surrender, OptionSignature whitePeace, OptionSignature victory) {
        public OptionsSignature {
            Objects.requireNonNull(surrender); Objects.requireNonNull(whitePeace); Objects.requireNonNull(victory);
            NativeInteractionRoles.requireSameProfile(surrender.recipientContext(), whitePeace.recipientContext(),
                    victory.recipientContext());
        }
    }

    public record NegativeSignature(BigInteger warId, Side playerSide, Boolean primaryLeader,
                                    BigInteger score, Boolean absoluteScoresObservable,
                                    BigInteger attackerScore, BigInteger defenderScore, ScoreBreakdown scoreBreakdown,
                                    Boolean activeCasusBelliPresent, CasusBelli activeCasusBelli,
                                    Boolean allowsWhitePeace, OptionsSignature options) {
        public NegativeSignature {
            positive(warId, "warId"); Objects.requireNonNull(playerSide);
            Objects.requireNonNull(score); Objects.requireNonNull(options);
        }
    }

    public record NativeOptions(NegativeSignature signature, BigInteger durationDays,
                                Boolean whitePeaceAutoAcceptObservable, Boolean whitePeaceAutoAccept) {
        public NativeOptions {
            Objects.requireNonNull(signature);
            if (durationDays != null) { nonnegative(durationDays, "durationDays"); }
        }
    }

    public record QueryContext(BigInteger schemaVersion, List<StableWar> activeWars, String episodeRunId,
                               BigInteger connectionGeneration, BigInteger actorId,
                               NegativeSignature negativeSignature, BigInteger durationDays, BigInteger queriedDateRaw) {
        public QueryContext {
            Objects.requireNonNull(schemaVersion); activeWars = sorted(activeWars);
            text(episodeRunId, "episodeRunId"); positive(connectionGeneration, "connectionGeneration");
            positive(actorId, "actorId"); Objects.requireNonNull(negativeSignature);
            if (durationDays != null) { nonnegative(durationDays, "durationDays"); }
            positive(queriedDateRaw, "queriedDateRaw");
        }
    }

    public record QueryResult(String step, Boolean accepted, String status, QueryContext context,
                              NativeOptions options, BigInteger querySequence) {
        public QueryResult {
            text(step, "step"); text(status, "status"); Objects.requireNonNull(context);
            Objects.requireNonNull(options); positive(querySequence, "querySequence");
        }
    }

    public record HistoryRecord(String step, Boolean ok, boolean warActionPresent, QueryResult query) { }

    /** Records are newest-first. Evaluator consumes at most through the second distinct query date. */
    public record Request(Snapshot snapshot, List<War> activeWars, War war, List<HistoryRecord> recentRecords) {
        public Request {
            Objects.requireNonNull(snapshot); activeWars = List.copyOf(activeWars);
            Objects.requireNonNull(war); recentRecords = List.copyOf(recentRecords);
        }
    }

    public record PolicyDefer(BigInteger warId, BigInteger latestQueriedDateRaw,
                              BigInteger previousQueriedDateRaw, BigInteger latestQuerySequence,
                              BigInteger expiresDateRaw, CasusBelli lastObservedCasusBelli) {
        public PolicyDefer {
            positive(warId, "warId"); positive(latestQueriedDateRaw, "latestQueriedDateRaw");
            positive(previousQueriedDateRaw, "previousQueriedDateRaw");
            positive(latestQuerySequence, "latestQuerySequence"); positive(expiresDateRaw, "expiresDateRaw");
            Objects.requireNonNull(lastObservedCasusBelli);
            require(previousQueriedDateRaw.compareTo(latestQueriedDateRaw) < 0, "strictly ordered query dates");
            require(latestQueriedDateRaw.compareTo(expiresDateRaw) < 0, "expiry after latest query");
        }
    }

    public static Optional<PolicyDefer> evaluate(Request request) {
        Objects.requireNonNull(request);
        Snapshot snapshot = request.snapshot(); War war = request.war();
        if (!snapshot.paused() || !snapshot.mapReady() || snapshot.terminalReasonPresent()
                || snapshot.activeEventPresent() || snapshot.interactionPresent() || snapshot.exclusiveModalPresent()
                || !snapshot.actorAlive() || war.score().compareTo(HUNDRED.negate()) <= 0
                || war.score().compareTo(HUNDRED) >= 0) { return Optional.empty(); }
        List<StableWar> stableWars = sorted(request.activeWars().stream().map(War::stable).toList());
        if (stableWars.isEmpty() || stableWars.stream().filter(item -> item.warId().equals(war.warId())).count() != 1) {
            return Optional.empty();
        }
        BigInteger latestDate = null; BigInteger latestSequence = null; BigInteger expiry = null;
        CasusBelli observedCasusBelli = null;
        List<NativeInteractionRoles> latestRecipients = null;
        for (HistoryRecord record : request.recentRecords()) {
            String step = record.step();
            if ("restore-checkpoint".equals(step) || terminalAction(step) || priorityBarrier(step)
                    || record.warActionPresent()) { return Optional.empty(); }
            if (step == null) { continue; }
            BigInteger queriedWar = parseQueryWarId(step);
            if (!war.warId().equals(queriedWar)) {
                if (step.startsWith(QUERY_PREFIX) && queriedWar == null) { return Optional.empty(); }
                continue;
            }
            QueryResult result = record.query();
            if (!Boolean.TRUE.equals(record.ok()) || result == null || !step.equals(result.step())
                    || !Boolean.TRUE.equals(result.accepted()) || !"available".equals(result.status())) {
                return Optional.empty();
            }
            QueryContext context = result.context(); NativeOptions options = result.options();
            NegativeSignature signature = options.signature();
            List<NativeInteractionRoles> recipients = recipientContexts(signature.options());
            if (recipients.stream().anyMatch(NativeInteractionRoles.Unavailable.class::isInstance)) { return Optional.empty(); }
            if (!BigInteger.ONE.equals(context.schemaVersion()) || !context.activeWars().equals(stableWars)
                    || !context.episodeRunId().equals(snapshot.episodeRunId())
                    || !context.connectionGeneration().equals(snapshot.connectionGeneration())
                    || !context.actorId().equals(snapshot.actorId())
                    || !context.negativeSignature().equals(signature) || !signature.warId().equals(war.warId())
                    || !Objects.equals(context.durationDays(), options.durationDays())
                    || !Boolean.TRUE.equals(signature.activeCasusBelliPresent()) || signature.activeCasusBelli() == null
                    || signature.activeCasusBelli().databaseIndex().signum() <= 0 || positiveExit(options)) {
                return Optional.empty();
            }
            BigInteger queriedDate = context.queriedDateRaw(); BigInteger sequence = result.querySequence();
            if (queriedDate.compareTo(snapshot.dateRaw()) > 0) { return Optional.empty(); }
            CasusBelli currentCb = signature.activeCasusBelli();
            if (observedCasusBelli == null) { observedCasusBelli = currentCb; }
            if (!currentCb.equals(observedCasusBelli)
                    || (war.currentCasusBelli() != null && !war.currentCasusBelli().equals(observedCasusBelli))) {
                return Optional.empty();
            }
            // A duplicate on the latest date is ignored before sequence ordering, as in the producer.
            if (latestDate != null && queriedDate.equals(latestDate)) { continue; }
            if (latestDate != null) {
                if (!recipients.equals(latestRecipients)) { return Optional.empty(); }
                if (queriedDate.compareTo(latestDate) > 0 || sequence.compareTo(latestSequence) >= 0
                        || !(queriedDate.compareTo(latestDate) < 0 && latestDate.compareTo(snapshot.dateRaw()) < 0
                        && snapshot.dateRaw().compareTo(expiry) < 0)) { return Optional.empty(); }
                return Optional.of(new PolicyDefer(war.warId(), latestDate, queriedDate,
                        latestSequence, expiry, observedCasusBelli));
            }
            latestDate = queriedDate; latestSequence = sequence; latestRecipients = recipients;
            expiry = queriedDate.add(LEASE_RAW).min(durationBoundary(options, queriedDate)
                    .orElse(queriedDate.add(LEASE_RAW)));
        }
        return Optional.empty();
    }

    static BigInteger parseQueryWarId(String step) {
        if (step == null || !step.startsWith(QUERY_PREFIX)) { return null; }
        String digits = step.substring(QUERY_PREFIX.length());
        if (!digits.matches("[1-9][0-9]*") || digits.length() > 10) { return null; }
        BigInteger value = new BigInteger(digits);
        return value.compareTo(BigInteger.valueOf(Integer.MAX_VALUE)) <= 0 ? value : null;
    }

    private static List<NativeInteractionRoles> recipientContexts(OptionsSignature options) {
        return List.of(options.surrender().recipientContext(), options.whitePeace().recipientContext(),
                options.victory().recipientContext());
    }

    private static boolean positiveExit(NativeOptions options) {
        OptionsSignature rows = options.signature().options(); OptionSignature peace = rows.whitePeace();
        return Boolean.TRUE.equals(rows.victory().available())
                || (Boolean.TRUE.equals(peace.available())
                && ((Boolean.TRUE.equals(options.whitePeaceAutoAcceptObservable()) && Boolean.TRUE.equals(options.whitePeaceAutoAccept()))
                || ("available".equals(peace.recipientResponse().status())
                    && Boolean.TRUE.equals(peace.recipientResponse().wouldAcceptNow()))));
    }

    private static Optional<BigInteger> durationBoundary(NativeOptions options, BigInteger date) {
        NegativeSignature signature = options.signature(); BigInteger duration = options.durationDays();
        if (duration == null || signature.playerSide() != Side.ATTACKER || !Boolean.TRUE.equals(signature.primaryLeader())) {
            return Optional.empty();
        }
        String key = signature.activeCasusBelli().canonicalKey();
        int days = "claim_cb".equals(key) && Boolean.TRUE.equals(signature.allowsWhitePeace()) ? 365
                : "individual_county_de_jure_cb".equals(key) ? 180 : 0;
        if (days == 0 || duration.compareTo(BigInteger.valueOf(days)) >= 0) { return Optional.empty(); }
        return Optional.of(date.add(BigInteger.valueOf(days).subtract(duration).multiply(BigInteger.valueOf(24))));
    }

    private static boolean terminalAction(String step) {
        return step != null && (step.equals("war-enforce-demands") || starts(step, "enforce-demands-", "offer-white-peace-",
                "surrender-war-", "query-war-termination-terms-", "query-war-termination-exit-terms-"));
    }

    private static boolean priorityBarrier(String step) {
        return step != null && (List.of("resolve-current-event", "query-current-event-window-context-v1",
                "query-pending-character-interaction-context-v1", "acknowledge-pending-character-interaction",
                "death-terminal", "start-next-episode").contains(step)
                || starts(step, "select-event-option-", "accept-pending-character-interaction", "reject-pending-character-interaction"));
    }

    private static boolean starts(String text, String... prefixes) {
        for (String prefix : prefixes) { if (text.startsWith(prefix)) { return true; } }
        return false;
    }

    private static List<StableWar> sorted(List<StableWar> wars) {
        List<StableWar> result = new ArrayList<>(wars); result.sort(Comparator.comparing(StableWar::warId));
        return List.copyOf(result);
    }

    private static void positive(BigInteger value, String name) {
        require(value != null && value.signum() > 0, name + " must be positive");
    }
    private static void nonnegative(BigInteger value, String name) {
        require(value != null && value.signum() >= 0, name + " must be nonnegative");
    }
    private static void text(String value, String name) {
        require(value != null && !value.isEmpty(), name + " must be nonempty");
    }
    private static void require(boolean valid, String message) {
        if (!valid) { throw new IllegalArgumentException(message); }
    }
}
