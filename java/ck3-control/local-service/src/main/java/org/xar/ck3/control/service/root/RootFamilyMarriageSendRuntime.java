package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.OptionalLong;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.action.family.FamilyMarriageIntent;
import org.xar.ck3.control.application.action.ordinary.RulerMarriageIntent;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.application.planning.family.FamilyNativePreparation;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.interactions.*;
import org.xar.ck3.control.wave2.planning.jointshortlist.JointShortlist.Domain;

/** One actual physical Game's five marriage send routes, original preparation and cold replay. */
public final class RootFamilyMarriageSendRuntime implements ActionPorts.PreparationPort {
    public record Sources(ExactRef outgoingNative, ExactRef outgoingDecoder,
            ExactRef nativePreparation, ExactRef freshPreparation, ExactRef effects, ExactRef effectsDecoder,
            ExactRef replayImplementation, List<ExactRef> completeProducers) {
        public Sources {
            completeProducers = List.copyOf(completeProducers);
            StrictJson.require(!completeProducers.isEmpty() && completeProducers.size() <= 64
                    && new HashSet<>(completeProducers).size() == completeProducers.size(),
                    "complete unique selected marriage producer closure required");
            for (ExactRef ref : List.of(outgoingNative, outgoingDecoder, nativePreparation, freshPreparation,
                    effects, effectsDecoder, replayImplementation)) {
                Objects.requireNonNull(ref);
                StrictJson.require(ref.bytes() > 0 && completeProducers.contains(ref),
                        "actual marriage producer/decoder/replay is outside its selected source closure");
            }
            completeProducers.forEach(ref -> StrictJson.require(ref.bytes() > 0,
                    "nonempty original marriage source required"));
        }
    }

    private final RootRuntimeContext context;
    private final RootFamilyBridge bridge;
    private final RootFamilyMarriageFreshPreparation fresh;
    private final Sources sources;
    private final FamilyMarriageSendReads queries;
    private final MarriageSendEffects effects;
    private final List<RootReadContractCatalog.InstalledRead> installedReads;
    private final List<RootExecutableBindings.ActionBinding> actions;
    private final List<NativeRecordedEvidenceVerifier.Binding> archived;
    private final List<RootDomainInstallation.FixedDomain> actionDomains;
    private final RootExecutableBindings.Family<RulerMarriageIntent> ruler;
    private final RootDomainInstallation.FamilyDomain rulerDomain;

    public RootFamilyMarriageSendRuntime(RootRuntimeContext actualContext, RootFamilyBridge actualBridge,
            RootFamilyMarriageFreshPreparation actualFresh, Sources sources) throws IOException {
        context = Objects.requireNonNull(actualContext);
        fresh = Objects.requireNonNull(actualFresh);
        this.sources = Objects.requireNonNull(sources);
        bridge = Objects.requireNonNull(actualBridge);
        fresh.requireContext(context);
        context.requireCurrent(context.clock().instant().plusSeconds(1));
        var authority = new RootFamilyMarriageSendAuthority(context, bridge, fresh.freshContracts());
        queries = new FamilyMarriageSendReads(sources.outgoingNative(), authority);
        effects = new MarriageSendEffects(queries, context.reads(),
                new NativeEffectSnapshots(() -> context.adopted().observations(), context.archive(), context.frameLoader()),
                context.frameLoader());
        installedReads = queries.contracts().stream()
                .map(contract -> new RootReadContractCatalog.InstalledRead(contract, sources.outgoingDecoder())).toList();
        var fixed = new ArrayList<RootExecutableBindings.ActionBinding>();
        var verifiers = new ArrayList<NativeRecordedEvidenceVerifier.Binding>();
        for (FamilyMarriageIntent.Route route : FamilyMarriageIntent.Route.values()) {
            var issued = issue(new OperationKey(route.step()), Optional.empty());
            fixed.add(issued.action());
            verifiers.add(issued.archived());
        }
        actions = List.copyOf(fixed);
        archived = List.copyOf(verifiers);
        actionDomains = actions.stream().map(action -> new RootDomainInstallation.FixedDomain(action, Domain.marriage)).toList();
        ruler = new RootExecutableBindings.Family<>("family-marriage-send:ruler/v1", RulerMarriageIntent.class,
                ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP, Optional.of(FamilyMarriageNativeRequests.RULER_CAPABILITY), sources.nativePreparation(),
                sources.effectsDecoder(), sources.effects(), intent -> new RawJson(DriverJson.encode(intent.toJson())),
                intent -> new OperationKey(intent.step()), intent -> issue(new OperationKey(intent.step()),
                        Optional.of(FamilyMarriageNativeRequests.RULER_CAPABILITY)));
        rulerDomain = new RootDomainInstallation.FamilyDomain(ruler, Domain.marriage);
    }

    /** Only this original installed context may consume these concrete products. */
    public void requireContext(RootRuntimeContext actual) {
        StrictJson.require(context == actual, "marriage runtime belongs to a different physical Game context");
        fresh.requireContext(actual);
    }

    public Sources sources() { return sources; }
    public FamilyMarriageSendReads queries() { return queries; }
    public MarriageSendEffects effects() { return effects; }
    public List<RootReadContractCatalog.InstalledRead> installedReads() { return installedReads; }
    public List<RootExecutableBindings.ActionBinding> actions() { return actions; }
    public List<NativeRecordedEvidenceVerifier.Binding> archivedVerifiers() { return archived; }
    public List<RootDomainInstallation.FixedDomain> actionDomains() { return actionDomains; }
    public RootExecutableBindings.Family<RulerMarriageIntent> rulerMarriage() { return ruler; }
    public RootDomainInstallation.FamilyDomain rulerDomain() { return rulerDomain; }
    public ExactRef replayImplementation() { return sources.replayImplementation(); }
    public FamilyNativePreparation.Replay replay() { return this::replayOriginal; }

    /** Root joins this original-intent-only policy with the other installed domain policies. No native I/O. */
    public RootReconciliationAuthority.QueryPolicy reconciliationReads() { return this::allowedReconciliationReads; }

    private List<RootReconciliationAuthority.AllowedRead> allowedReconciliationReads(ActionReceipt original,
            ReconciliationIdentity identity, Complete current, Instant deadline) throws IOException {
        if (!MarriageSendEffects.accepts(original.command())) return List.of();
        var same = context.borrowedSession();
        context.writer().requireSession(same);
        var archive = context.archive().withSession(same);
        ActionReceipt canonical = requireArchivedPendingOriginal(original, identity, current, archive);
        StrictJson.require(current.source().equals(context.source()) && current.sessionId().equals(context.game().sessionId()),
                "marriage observation policy crossed its installed physical Game/source/session");
        var attempt = ActionTransitions.attempt(canonical.state()).orElseThrow();
        var before = RootGuardEvidence.loadFrame(attempt.guard(), archive, context.frameLoader());
        var prepared = effects.loadPreparation(canonical.command(), attempt.requestId(), attempt.preparedRequest(), before, archive);
        return List.of(new RootReconciliationAuthority.AllowedRead(queries.observationContract(),
                FamilyMarriageSendReads.observationArguments(canonical.command(), attempt,
                        archive.readReferenceOf(prepared.read()), prepared.materialized().roles().actor()),
                RootReconciliationAuthority.QueryKind.FAMILY_MARRIAGE_SEND));
    }

    /**
     * Pure original-byte guard shared by the installed QueryPolicy and its real transport/archive regression.
     * The sole Root reconciliation authority first qualifies live membership or exact historical writer ancestry.
     * A later current Head may already have updated or settled this receipt; these retained DATA grant no new query or dispatch.
     */
    public static ActionReceipt requireArchivedPendingOriginal(ActionReceipt original, ReconciliationIdentity identity,
            Complete factual, ActionPorts.OutcomeArchive archive) throws IOException {
        Objects.requireNonNull(original); Objects.requireNonNull(identity); Objects.requireNonNull(factual); Objects.requireNonNull(archive);
        ActionReceipt retained = archive.loadReceipt(identity.pending().originalReceipt());
        StrictJson.require(MarriageSendEffects.accepts(original.command()) && retained.equals(original) && !retained.settled()
                && retained.bodySha256().equals(ActionCodec.bodySha256(retained.command()))
                && identity.pending().actionId().equals(retained.command().actionId())
                && identity.pending().bodySha256().equals(retained.bodySha256())
                && identity.pending().originalBefore().equals(retained.command().before())
                && identity.source().equals(retained.command().source()) && identity.sessionId().equals(retained.command().sessionId())
                && factual.identity().equals(identity.factual()) && factual.source().equals(identity.source())
                && factual.sessionId().equals(identity.sessionId()) && factual.connectionGeneration().equals(identity.connectionGeneration())
                && ActionTransitions.attempt(retained.state()).filter(attempt -> attempt.requestId().equals(identity.pending().requestId())).isPresent(),
                "marriage observation policy lost its exact retained original pending/body/Attempt/factual frame");
        return retained;
    }

    /** A request ID and the original held writer Session are mandatory; neither overload submits. */
    @Override public NativeRequest prepare(ActionCommand command) {
        throw new IllegalStateException("marriage preparation requires the actual coordinator request ID and writer Session");
    }

    @Override public NativeRequest prepare(ActionCommand command, String requestId) {
        throw new IllegalStateException("marriage preparation requires the actual coordinator-held writer Session");
    }

    @Override public NativeRequest prepare(ContinuityStorePort.Session same, ActionCommand command, String requestId) {
        Objects.requireNonNull(command);
        StrictJson.text(requestId);
        try {
            context.writer().requireSession(same);
            context.requireCurrent(command.deadline());
            StrictJson.require(ActionCommandScope.current().filter(command::equals).isPresent(),
                    "marriage preparation lacks its actual immutable coordinator command scope");
            StrictJson.require(MarriageSendEffects.accepts(command)
                    && command.source().equals(context.source())
                    && command.before().game().equals(context.game().generation())
                    && command.sessionId().equals(context.game().sessionId()),
                    "marriage preparation crossed the original played Game/source/session/expected contract");
            requireInstalledFreshContracts();
            var original = fresh.prepare(same, command);
            StrictJson.require(original.basis().preparedPlan().isPresent(),
                    "actual fresh native marriage review is unavailable before native dispatch");
            NativeRequest fields = FamilyMarriageNativeRequests.prepare(command, original.basis());
            StrictJson.require(fields.preparationEvidence().isEmpty(),
                    "pure native field producer must not invent another review manifest");
            var archive = context.archive().withSession(same);
            var readRequest = new PlanningReadRequest(command.before(), command.source(), command.sessionId(),
                    queries.preparationContract().operation(),
                    FamilyMarriageSendReads.preparationArguments(command, requestId,
                            FamilyMarriageSendReads.FreshBasis.from(original.basis(), original.freshReads())),
                    command.deadline());
            var result = context.reads().read(same, queries.preparationContract(), readRequest);
            var known = requireKnownMarriageRead(result);
            requireSendable(command, known.value());
            StrictJson.require(FamilyMarriageSendReads.materializedSender(known.receipt())
                    == ((FamilyMarriageSendReads.Prepared) known.value().prepared().orElseThrow()).roles().actor(),
                    "actual complete original preparation sender differs from its typed projection");
            var refs = new ArrayList<ExactRef>();
            refs.add(original.reviewManifest());
            refs.addAll(MarriageSendEffects.preservePreparation(command, requestId, fields, known.receipt(), archive));
            NativeRequest prepared = new NativeRequest(fields.step(), fields.requiredCapability(), fields.additionalFields(), refs);
            // Reopen the source-owned review under this same writer before INTENT/submit.
            var replayed = replayOriginal(command, prepared, archive);
            StrictJson.require(sameReview(replayed, original.basis()) && replayed.materializedSend().isPresent(),
                    "actual fresh preparation, original-byte review and native materialized send differ");
            context.writer().requireSession(same);
            context.requireCurrent(command.deadline());
            return prepared;
        } catch (IOException failure) {
            throw new UncheckedIOException("actual same-writer marriage preparation is unavailable before native dispatch", failure);
        }
    }

    private FamilyNativePreparation.VerifiedBasis replayOriginal(ActionCommand command, NativeRequest prepared,
            ActionPorts.OutcomeArchive actualArchive) throws IOException {
        StrictJson.require(MarriageSendEffects.accepts(command), "exact shared marriage send contract required for replay");
        var same = context.borrowedSession();
        context.writer().requireSession(same);
        var original = fresh.replay().replay(command, prepared, actualArchive);
        FamilyMarriageNativeRequests.verifyOriginal(command, prepared, original);
        var before = bridge.replay(same, original.bridgeEvidence()).frame();
        var preparation = effects.loadPreparation(command, prepared, before, actualArchive);
        var roles = preparation.materialized().roles();
        StrictJson.require(roles.actor() != null && roles.recipient() != null,
                "actual native materialized send lacks its original sender/recipient");
        var materialized = new FamilyNativePreparation.MaterializedSend(roles.actor(), roles.recipient(),
                nullable(roles.secondaryActor()), nullable(roles.secondaryRecipient()), nullable(roles.intermediary()),
                5, actualArchive.readReferenceOf(preparation.read()));
        context.writer().requireSession(same);
        return original.withMaterializedSend(materialized);
    }

    private static OptionalLong nullable(Long value) {
        return value == null ? OptionalLong.empty() : OptionalLong.of(value);
    }

    /**
     * Preserves the actual coordinator unavailable reason and typed failure flags instead of
     * collapsing every non-Known result into a fixed generic IllegalArgumentException.
     */
    static PlanningReadResult.Known<FamilyMarriageSendReads.Observation> requireKnownMarriageRead(
            PlanningReadResult<FamilyMarriageSendReads.Observation> result) {
        if (result instanceof PlanningReadResult.Known<FamilyMarriageSendReads.Observation> known)
            return known;
        var unavailable = (PlanningReadResult.Unavailable<FamilyMarriageSendReads.Observation>) result;
        var reason = unavailable.reason();
        var originalKind = unavailable.original().isPresent()
                ? unavailable.original().orElseThrow().getClass().getSimpleName() : "none";
        var decodeFailure = unavailable.decodeFailure().isPresent() ? "decode_failure" : "no_decode_failure";
        var observedFailure = unavailable.observedFailure().isPresent() ? "observed_failure" : "no_observed_failure";
        var ackDiagnostic = "";
        if (unavailable.original().isPresent() && unavailable.original().orElseThrow() instanceof NativeActionPort.AckReceived ack) {
            var expectedIdMatch = unavailable.observedFailure()
                    .map(failure -> Boolean.toString(failure.requestId().equals(ack.requestId())))
                    .orElse("unavailable");
            try {
                var packet = ack.originalPacket();
                if (packet.length > 65540) {
                    ackDiagnostic = "ack_request_id=" + (ack.requestId().length() <= 128 ? ack.requestId() : ack.requestId().substring(0, 128))
                            + ":nativeOk=" + ack.nativeOk() + ":uninspected_large_frame=" + packet.length;
                } else {
                    var frame = org.xar.ck3.control.nativebridge.NativeWire.decode(packet);
                    if (frame instanceof org.xar.ck3.control.nativebridge.NativeWire.CommandResult commandResult) {
                        var errorField = commandResult.error();
                        var presence = errorField.presence();
                        var token = errorField.token().orElse(null);
                        String errorSummary;
                        if (presence == org.xar.ck3.control.nativebridge.NativeWire.Presence.ABSENT) {
                            errorSummary = "absent";
                        } else if (presence == org.xar.ck3.control.nativebridge.NativeWire.Presence.NULL) {
                            errorSummary = "null";
                        } else if (token != null) {
                            var bytes = token.value();
                            var node = org.xar.ck3.control.nativebridge.NativeWire.parse(bytes);
                            if (node.isTextual()) {
                                var text = node.textValue();
                                errorSummary = text.length() <= 512 ? text : text.substring(0, 512);
                            } else {
                                errorSummary = node.getNodeType() + ":" + bytes.length;
                            }
                        } else {
                            errorSummary = "unknown";
                        }
                        var wireIdMatch = commandResult.requestId().equals(ack.requestId()) ? "match" : "mismatch";
                        ackDiagnostic = "ack_request_id=" + (ack.requestId().length() <= 128 ? ack.requestId() : ack.requestId().substring(0, 128))
                                + ":nativeOk=" + ack.nativeOk() + ":wire_id_match=" + wireIdMatch + ":error=" + errorSummary;
                    } else {
                        ackDiagnostic = "ack_request_id=" + (ack.requestId().length() <= 128 ? ack.requestId() : ack.requestId().substring(0, 128))
                                + ":nativeOk=" + ack.nativeOk() + ":frame_type=" + frame.getClass().getSimpleName();
                    }
                }
            } catch (java.io.IOException | RuntimeException diagnosticUnavailable) {
                ackDiagnostic = "ack_request_id=" + (ack.requestId().length() <= 128 ? ack.requestId() : ack.requestId().substring(0, 128))
                        + ":nativeOk=" + ack.nativeOk() + ":decode_error";
            }
            ackDiagnostic += ":coordinator_read_id_match=" + expectedIdMatch;
        }
        var message = "actual independent marriage before storage/preparation read is unavailable"
                + (ackDiagnostic.isEmpty() ? "" : ":ack=" + ackDiagnostic)
                + ":reason=" + (reason.length() <= 2048 ? reason : reason.substring(0, 2048))
                + ":original=" + originalKind + ":" + decodeFailure + ":" + observedFailure;
        throw new IllegalArgumentException(message);
    }

    private static boolean sameReview(FamilyNativePreparation.VerifiedBasis first,
            FamilyNativePreparation.VerifiedBasis second) {
        return first.snapshot().equals(second.snapshot()) && first.bridgeIdentity().equals(second.bridgeIdentity())
                && first.snapshotEvidence().equals(second.snapshotEvidence())
                && first.bridgeEvidence().equals(second.bridgeEvidence()) && first.preparedPlan().equals(second.preparedPlan());
    }

    private void requireInstalledFreshContracts() {
        StrictJson.require(context.readCatalog().containsIdentity(queries.preparationContract())
                && context.readCatalog().containsIdentity(queries.observationContract()),
                "actual marriage before/after contracts have not been installed in the sole Root catalog");
        for (FamilyMarriageSendReads.Route route : FamilyMarriageSendReads.Route.values())
            for (RootFamilyMarriageSendAuthority.FreshContract requirement : fresh.freshContracts().forRoute(route))
                StrictJson.require(!requirement.contract().operation().value().equals(FamilyMarriageSendReads.STEP)
                        && context.readCatalog().containsIdentity(requirement.contract()),
                        "an actual marriage route lacks its identical installed fresh read contract");
    }

    private RootExecutableBindings.IssuedAction issue(OperationKey operation, Optional<String> capability) {
        var binding = new NativeEffectRegistry.Binding(operation, sources.nativePreparation(), this,
                (command, attempt, dispatch) -> {
                    StrictJson.require(command.operation().equals(operation), "marriage effect changed the exact issued operation");
                    try {
                        var same = context.borrowedSession();
                        context.writer().requireSession(same);
                        return effects.observe(same, command, attempt, dispatch, context.archive().withSession(same));
                    } catch (IOException failure) {
                        throw new UncheckedIOException("actual marriage observer lacks its original writer Session", failure);
                    }
                });
        return new RootExecutableBindings.IssuedAction(
                new RootExecutableBindings.ActionBinding(binding, ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,
                        capability, sources.effectsDecoder()),
                effects.archivedVerifier(operation, sources.effects(), () -> {
                    try { return context.borrowedSession(); }
                    catch (IOException failure) { throw new UncheckedIOException(failure); }
                }));
    }

    /** DATA validation only. Qualification remains in the original Root authority and source-owned review replay. */
    static void requireSendable(ActionCommand command, FamilyMarriageSendReads.Observation observed) {
        var sender = FamilyMarriageSendReads.sender(command);
        StrictJson.require(observed.scope() == FamilyMarriageSendReads.Scope.ACTION_PREPARATION
                && observed.outgoing().complete()
                && observed.prepared().orElseThrow() instanceof FamilyMarriageSendReads.Prepared,
                "actual complete outgoing storage and native prepared context required before submit");
        var material = (FamilyMarriageSendReads.Prepared) observed.prepared().orElseThrow();
        StrictJson.require(material.canSend()
                && observed.outgoing().definitionHash().orElseThrow() == material.definitionHash()
                && Objects.equals(material.roles().actor(), observed.outgoing().senderCharacterId().orElseThrow()),
                "actual native final canSend/definition/materialized sender differs from complete original storage");
        // Public ruler materialization may redirect the sender; it must remain the original native value.
        if (sender.route() != FamilyMarriageSendReads.Route.RULER)
            StrictJson.require(Objects.equals(material.roles().actor(), sender.actor())
                    && Objects.equals(material.roles().secondaryActor(), sender.subject())
                    && Objects.equals(material.roles().secondaryRecipient(), sender.candidate()),
                    "actual native materialized private pair differs from the immutable intent");
        if (sender.recipient().isPresent())
            StrictJson.require(Objects.equals(material.roles().recipient(), sender.recipient().getAsLong()),
                    "actual native materialized recipient differs from the immutable intent");
        if (sender.route() == FamilyMarriageSendReads.Route.FULFILL_BETROTHAL) {
            // The native terms copier computes effective lineality separately from the selected option.
            boolean effective = material.effectiveMatrilineal().orElseThrow(() ->
                    new IllegalArgumentException("actual private fulfillment effective lineality is unavailable"));
            StrictJson.require(effective == FamilyMarriageIntent.fromJson(command.arguments()).matrilineal(),
                    "actual native fulfillment effective lineality differs from the immutable intent");
        } else {
            StrictJson.require((!sender.requestMatrilineal() || material.matrilineal())
                    && (!sender.requireMatrilinealOff() || !material.matrilineal()),
                    "actual native selected option differs from the immutable intent");
        }
        StrictJson.require((sender.route() == FamilyMarriageSendReads.Route.RULER) == material.effectiveMatrilineal().isEmpty(),
                "public null and actual private effective lineality have different original source contracts");
        if (sender.route() == FamilyMarriageSendReads.Route.CHILD_MATRILINEAL
                || sender.route() == FamilyMarriageSendReads.Route.CHILD_DEFAULT)
            StrictJson.require(material.effectiveMatrilineal().orElseThrow()
                    == FamilyMarriageIntent.fromJson(command.arguments()).matrilineal(),
                    "actual child effective lineality differs from the independently verified native route");
    }
}
