package org.xar.ck3.control.wave3.governance.guardiancadence;

import java.math.BigInteger;
import java.util.HashMap;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.wave3.governance.guardiancadence.GuardianCadenceModel.*;

/** Original completed-negative policy. Every output retains unknown current legality and zero action credit. */
public final class GuardianNegativeCadence {
    public static final BigInteger PERIOD_RAW = BigInteger.valueOf(30 * 24);
    private static final Set<Flag> TRUE_FLAGS = Set.of(Flag.ACTOR_ALIVE, Flag.RECIPIENT_ALIVE, Flag.NATIVE_CONTEXT,
            Flag.ORDINARY_SUPPORTED, Flag.SOURCE_PINS, Flag.ACTOR_BINDING, Flag.RECIPIENT_BINDING, Flag.OWNER_THREAD, Flag.TLS, Flag.FRAME);
    private static final Set<Flag> FALSE_FLAGS = Set.of(Flag.SHOWN, Flag.CAN_SEND, Flag.READY, Flag.ACTIVE_EVENT, Flag.INCOMING_INTERACTION);
    private GuardianNegativeCadence() { }

    public static Optional<SourceScope> sourceScope(Frame frame, Optional<ScopeMaterials> materials, Long heirId) {
        if (!frame.status().equals("complete") || heirId == null || heirId <= 0 || materials.isEmpty()) { return Optional.empty(); }
        ScopeMaterials needs = materials.get(); Focus focus = needs.focus(); Court court = needs.court();
        Provider provider = needs.provider(); Relation relation = needs.relation();
        if (!"available".equals(needs.valuesStatus()) || !focus.available() || !court.available() || !court.sourceQualified()
                || court.ownerId() == null || court.ownerId() != frame.actorCharacterId() || !"available".equals(provider.status())
                || !provider.collectionAvailable() || !relation.observed() || !relation.collectionAvailable() || !needs.missingObservations().isEmpty()
                || provider.observation().isEmpty() || relation.namedGuardian().isEmpty()) { return Optional.empty(); }
        NamedGuardian named = relation.namedGuardian().get();
        if (!named.available() || !named.identityRoundTrip() || !named.sampleStable() || named.matchedPeerId() == null
                || named.matchedPeerId() != frame.actorCharacterId()) { return Optional.empty(); }
        ProviderObservation observation = provider.observation().get();
        return Optional.of(new SourceScope(frame.gamePid(), frame.connectionGeneration(), frame.episodeRunId(), frame.actorCharacterId(),
                heirId, needs.childId(), needs.ageMeasureRaw(), needs.sexSelectorRaw(), focus.state(), focus.currentKey(), court.ownerId(),
                named.matchedPeerId(), observation.guardianId(), observation.roleSource()));
    }

    public static Optional<Deferred> deferred(State state, Optional<SourceScope> source, Frame frame) {
        if (source.isEmpty()) { return Optional.empty(); }
        SourceScope scope = source.get(); NegativeRecord record = state.records().get(scope.childId());
        if (record == null || !record.scope().equals(scope) || frame.dateRaw().compareTo(record.lastDateRaw()) < 0) { return Optional.empty(); }
        boolean sameFrame = frame.dateRaw().equals(record.lastDateRaw()) && frame.nativeRevision().equals(record.lastNativeRevision());
        boolean active = record.cooldownUntilDateRaw().isPresent() && frame.dateRaw().compareTo(record.cooldownUntilDateRaw().get()) < 0;
        if (!sameFrame && !active) { return Optional.empty(); }
        return Optional.of(new Deferred(sameFrame ? DeferStatus.SAME_FRAME : DeferStatus.POLICY_DEFERRED, scope.childId(), scope.actorId(),
                record.lastDateRaw(), record.lastNativeRevision(), record.cooldownUntilDateRaw()));
    }

    public static ObservationResult observe(State state, Optional<SourceScope> source, Frame frame,
            QueryRead defaultQuery, List<Attempt> attempts, String selectedStep) {
        if (source.isEmpty() || !selectedStep.equals("life-advance") || attempts.size() != 1) { return unchanged(state); }
        SourceScope scope = source.get(); Attempt attempt = attempts.getFirst();
        if (!"observed_selected_options".equals(attempt.variant()) || !(defaultQuery instanceof ObservedQuery first)
                || !(attempt.query() instanceof ObservedQuery second) || !negative(first, frame, scope.childId(), scope.actorId())
                || !negative(second, frame, scope.childId(), scope.actorId())) { return unchanged(state); }
        Context one = first.context(), two = second.context();
        if (!(two.materialization().orElse(null) instanceof CompleteMaterialization complete)) { return unchanged(state); }
        var material = complete.observation(); var pair = material.pair().orElseThrow();
        if (one.selectedOptionCount().signum() != 0 || two.selectedOptionCount().signum() != 0 || first.querySequence().equals(second.querySequence())
                || !one.definitionStableHash().equals(two.definitionStableHash()) || !one.executableSha256().equals(two.executableSha256())
                || pair.childFullId() != scope.childId() || pair.guardianFullId() != scope.actorId()
                || !material.requestedOptionKeys().orElseThrow().isEmpty()
                || !Boolean.TRUE.equals(material.pairMatches()) || !Boolean.TRUE.equals(material.optionKeysMatch())) {
            return unchanged(state);
        }
        NegativeRecord previous = state.records().get(scope.childId()); boolean sameScope = previous != null && previous.scope().equals(scope);
        if (sameScope && frame.dateRaw().compareTo(previous.lastDateRaw()) <= 0) { return unchanged(state); }
        int count = sameScope ? Math.min(2, previous.count() + 1) : 1;
        Optional<BigInteger> until = count >= 2 ? Optional.of(frame.dateRaw().add(PERIOD_RAW))
                : sameScope ? previous.cooldownUntilDateRaw() : Optional.empty();
        NegativeRecord record = new NegativeRecord(scope, count, frame.dateRaw(), frame.nativeRevision(), until,
                one.executableSha256(), one.definitionStableHash());
        HashMap<Long, NegativeRecord> records = new HashMap<>(state.records()); records.put(scope.childId(), record);
        return new ObservationResult(new State(records), Optional.of(new NegativeObserved(scope.childId(), scope.actorId(), count, frame.dateRaw(), until)));
    }

    public static Evaluation evaluate(Input input) {
        Optional<SourceScope> scope = sourceScope(input.frame(), input.materials(), input.heirId());
        return new Evaluation(scope, deferred(input.state(), scope, input.frame()),
                observe(input.state(), scope, input.frame(), input.defaultQuery(), input.attempts(), input.selectedStep()));
    }

    private static boolean negative(ObservedQuery query, Frame frame, long child, long actor) {
        Context context = query.context(); Roles roles = context.roles();
        return "query-character-interaction-ordinary-v1".equals(query.step()) && query.accepted() && "available".equals(query.status()) && query.readOnly()
                && query.gamePid() == frame.gamePid() && query.connectionGeneration().equals(frame.connectionGeneration()) && query.dateRaw().equals(frame.dateRaw())
                && query.queriedNativeRevision().equals(frame.nativeRevision()) && query.queriedPublicRevision().equals(frame.publicRevision())
                && "ck3-character-interaction-ordinary-context-v1".equals(context.schema()) && "available".equals(context.status())
                && "native_current_ordinary_interaction_context_1.20.0.4".equals(context.source()) && context.readOnly()
                && context.gamePid() == frame.gamePid() && context.connectionGeneration().equals(frame.connectionGeneration()) && context.dateRaw().equals(frame.dateRaw())
                && context.nativeRevision().equals(frame.nativeRevision()) && "educate_child_interaction".equals(context.interactionKey())
                && context.playerId() == actor && context.recipientId() == child && context.trueFlags().containsAll(TRUE_FLAGS)
                && FALSE_FLAGS.stream().noneMatch(context.trueFlags()::contains) && context.unavailableReason() == null
                && context.executableSha256() != null && context.executableSha256().length() == 64
                && roles.actorId() != null && roles.actorId() == actor && roles.recipientId() != null && roles.recipientId() == actor
                && roles.secondaryActorId() != null && roles.secondaryActorId() == actor && roles.secondaryRecipientId() != null && roles.secondaryRecipientId() == child;
    }
    private static ObservationResult unchanged(State state) { return new ObservationResult(state, Optional.empty()); }
}
