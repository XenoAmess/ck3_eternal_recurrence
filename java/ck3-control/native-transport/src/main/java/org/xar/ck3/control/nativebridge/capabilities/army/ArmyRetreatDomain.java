package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.application.planning.military.*;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.continuity.ObservedGameplayEntry;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** Real original-session adapter for the existing pure retreat reducer. No parallel once file or missing-domain bootstrap. */
public final class ArmyRetreatDomain {
    private static final String INPUT = "xar.army-retreat-reducer-input/v1";
    private static final String INITIAL = "xar.army-retreat-qualified-first-episode/v1";
    private static final String OBSERVED_INITIAL = "xar.army-retreat-observed-first-episode/v1";
    public record Known(ActiveRetreatState.State state, DomainBodies.Available original) {
        public Known { Objects.requireNonNull(state); Objects.requireNonNull(original); }
    }
    public record Proof(Complete before, Complete after, List<PlanningReadReceipt> reads, Optional<ActionReceipt> action) {
        public Proof { Objects.requireNonNull(before); Objects.requireNonNull(after); reads = List.copyOf(reads); Objects.requireNonNull(action); StrictJson.require(reads.size() <= 2, "finite retreat proof reads required"); }
    }
    private final ImmutableArtifactStore artifacts;
    private final ActionPorts.OutcomeArchive archive;
    private final NativeEffectEvidence.FrameLoader frames;
    private final Optional<ActionPorts.RecordedEvidenceVerifier> initialEntryVerifier;
    public ArmyRetreatDomain(ImmutableArtifactStore originalArtifacts, ActionPorts.OutcomeArchive sameArchive, NativeEffectEvidence.FrameLoader actualFrameLoader) {
        artifacts = Objects.requireNonNull(originalArtifacts); archive = Objects.requireNonNull(sameArchive); frames = Objects.requireNonNull(actualFrameLoader); initialEntryVerifier = Optional.empty();
    }
    public ArmyRetreatDomain(ImmutableArtifactStore originalArtifacts, ActionPorts.OutcomeArchive sameArchive, NativeEffectEvidence.FrameLoader actualFrameLoader, ActionPorts.RecordedEvidenceVerifier actualCanonicalEntryVerifier) {
        artifacts = Objects.requireNonNull(originalArtifacts); archive = Objects.requireNonNull(sameArchive); frames = Objects.requireNonNull(actualFrameLoader); initialEntryVerifier = Optional.of(Objects.requireNonNull(actualCanonicalEntryVerifier));
    }
    public Known read(ContinuityStorePort.Session session) throws IOException {
        Objects.requireNonNull(session); session.requireWriter(artifacts.originalWriterLock()); var read = session.readDomain(DomainBodies.Slot.ACTIVE_RETREAT);
        if (!(read instanceof DomainBodies.Available original)) throw new IOException("ACTIVE_RETREAT is not imported; no implicit empty ledger or cleared historical once claims");
        StrictJson.require(original.reference().contractSchema().equals(ActiveRetreatState.SCHEMA), "retreat domain schema differs from its sole reducer");
        return new Known(ActiveRetreatState.decode(DriverJson.object(original.canonicalBody(), ContinuityJson.DOMAIN_MAX_BYTES)), original);
    }
    public Known apply(ContinuityStorePort.Session session, ActiveRetreatState.Event event, Proof proof) throws IOException {
        Known before = read(session); verify(session.head().state(), before.state(), event, proof, archive);
        var next = ActiveRetreatState.reduce(before.state(), event); byte[] actual = canonical(ActiveRetreatState.encode(next));
        var body = artifacts.publish(actual, ContinuityJson.DOMAIN_MAX_BYTES); var boundArchive = archive.withSession(session);
        ObjectNode input = StrictJson.object().put("schema", INPUT); input.set("previous_body", before.original().reference().payload().toJson()); input.set("event", encodeEvent(event));
        input.set("before", basis(NativeEffectEvidence.basis(proof.before()))); input.set("after", basis(NativeEffectEvidence.basis(proof.after())));
        var readRefs = input.putArray("reads"); List<ExactRef> evidence = new ArrayList<>();
        for (var basis : List.of(NativeEffectEvidence.basis(proof.before()), NativeEffectEvidence.basis(proof.after()))) { evidence.add(basis.nativeFrame()); evidence.add(basis.driverFacts()); }
        for (PlanningReadReceipt read : proof.reads()) { ExactRef ref = boundArchive.readReferenceOf(read); readRefs.add(ref.toJson()); evidence.add(ref); }
        if (proof.action().isPresent()) { ExactRef ref = boundArchive.preserveReceipt(proof.action().orElseThrow()); input.set("action", ref.toJson()); evidence.add(ref); } else input.putNull("action");
        byte[] encoded = ContinuityJson.canonical(input, ContinuityJson.DOMAIN_MAX_BYTES);
        var request = new DomainBodies.ImportRequest(DomainBodies.Slot.ACTIVE_RETREAT, ActiveRetreatState.SCHEMA, body.reference(), encoded,
                evidence.stream().distinct().toList(), "retreat-" + ActionCodec.sha256(encoded));
        session.commitImport(session.previewImport(request)); return read(session);
    }
    /** Explicit first-entry producer. A missing slot alone can never call this qualification or create empty state. */
    public Known initializeNewEpisode(ContinuityStorePort.Session session, Complete actualInitialFrame) throws IOException {
        session.requireWriter(artifacts.originalWriterLock()); var bound = archive.withSession(session); var head = session.head();
        StrictJson.require(DomainBodies.reference(head.state(), DomainBodies.Slot.ACTIVE_RETREAT).isEmpty(), "existing retreat domain cannot be reset by first-entry initialization");
        var root = head.state().toJson();
        StrictJson.require(root.has(WriterContracts.GAMEPLAY_ENTRY_FIELD) && !root.get(WriterContracts.GAMEPLAY_ENTRY_FIELD).isNull(), "no original committed first-gameplay entry qualifies a retreat reset");
        var entryNode = ArmyJson.object(root.get(WriterContracts.GAMEPLAY_ENTRY_FIELD));
        var schema = StrictJson.text(entryNode.get("schema"));
        boolean observed = ObservedGameplayEntry.SCHEMA.equals(schema) || ObservedGameplayEntry.SCHEMA_V2.equals(schema);
        var entry = observed ? qualifyObservedInitial(head, actualInitialFrame, bound, entryNode) : qualifyInitial(head, actualInitialFrame, bound);
        var inputSchema = observed ? OBSERVED_INITIAL : INITIAL;
        byte[] body = canonical(ActiveRetreatState.encode(ActiveRetreatState.State.initial())); var original = artifacts.publish(body, ContinuityJson.DOMAIN_MAX_BYTES);
        var input = StrictJson.object().put("schema", inputSchema); input.set("entry", entry); input.set("actual", basis(NativeEffectEvidence.basis(actualInitialFrame)));
        List<ExactRef> evidence = observed ? observedInitialEvidence(entry, actualInitialFrame, bound) : initialEvidence(entry, actualInitialFrame);
        byte[] encoded = ContinuityJson.canonical(input, ContinuityJson.DOMAIN_MAX_BYTES);
        var request = new DomainBodies.ImportRequest(DomainBodies.Slot.ACTIVE_RETREAT, ActiveRetreatState.SCHEMA, original.reference(), encoded, evidence, "retreat-first-episode-" + ActionCodec.sha256(encoded));
        session.commitImport(session.previewImport(request)); return read(session);
    }
    /** Install this exact registration in the existing writer; it never initializes missing legacy state. */
    public DomainBodies.Registration registration(List<ExactRef> exactProducerSources) {
        return new DomainBodies.Registration(DomainBodies.Slot.ACTIVE_RETREAT, ActiveRetreatState.SCHEMA, ContinuityJson.DOMAIN_MAX_BYTES, exactProducerSources,
                new DomainBodies.Verifier() {
                @Override public String verify(org.xar.ck3.control.continuity.ContinuityState detached, Optional<DomainBodies.BodyRef> previous, DomainBodies.ImportRequest request, byte[] actualBody) throws IOException {
                    throw new IOException("retreat qualification requires the actual original writer Head");
                }
                @Override public String verify(WriterContracts.Head actualHead, Optional<DomainBodies.BodyRef> previous, DomainBodies.ImportRequest request, byte[] actualBody) throws IOException {
                    var head = actualHead.state();
                    if (previous.isEmpty()) {
                        ObjectNode initial = StrictJson.object(StrictJson.parse(request.producerInput()), Set.of("schema", "entry", "actual"));
                        var schema = StrictJson.text(initial.get("schema"));
                        StrictJson.require((schema.equals(INITIAL) || schema.equals(OBSERVED_INITIAL)) && request.slot() == DomainBodies.Slot.ACTIVE_RETREAT && request.contractSchema().equals(ActiveRetreatState.SCHEMA), "first retreat body lacks exact qualified initialization provenance");
                        Complete actual = frames.load(frameBasis(initial.get("actual")), archive);
                        var root = head.toJson();
                        StrictJson.require(root.has(WriterContracts.GAMEPLAY_ENTRY_FIELD) && !root.get(WriterContracts.GAMEPLAY_ENTRY_FIELD).isNull(), "no original committed first-gameplay entry qualifies a retreat reset");
                        var entryNode = ArmyJson.object(root.get(WriterContracts.GAMEPLAY_ENTRY_FIELD));
                        var entrySchema = StrictJson.text(entryNode.get("schema"));
                        boolean observed = ObservedGameplayEntry.SCHEMA.equals(entrySchema) || ObservedGameplayEntry.SCHEMA_V2.equals(entrySchema);
                        StrictJson.require(observed == schema.equals(OBSERVED_INITIAL), "retreat initialization branch mismatch");
                        ObjectNode entry = observed ? qualifyObservedInitial(actualHead, actual, archive, entryNode) : qualifyInitial(actualHead, actual, archive);
                        List<ExactRef> evidence = observed ? observedInitialEvidence(entry, actual, archive) : initialEvidence(entry, actual);
                        StrictJson.require(entry.equals(initial.get("entry")) && request.evidence().containsAll(evidence)
                                && Arrays.equals(actualBody, canonical(ActiveRetreatState.encode(ActiveRetreatState.State.initial()))), "first retreat initialization differs from its original canonical entry/full Driver/frame");
                        return ActionCodec.sha256(ContinuityJson.canonical(StrictJson.object().put("actual_head_digest", actualHead.digest()).put("initial_body_sha256", ActionCodec.sha256(actualBody)), ContinuityJson.DOMAIN_MAX_BYTES));
                    }
                    var prior = previous.orElseThrow(() -> new IllegalArgumentException("UNIMPORTED retreat needs complete original pending/once import or independently qualified new-episode initialization"));
                    ObjectNode input = StrictJson.object(StrictJson.parse(request.producerInput()), Set.of("schema", "previous_body", "event", "before", "after", "reads", "action"));
                    StrictJson.require(StrictJson.text(input.get("schema")).equals(INPUT) && request.slot() == DomainBodies.Slot.ACTIVE_RETREAT
                            && request.contractSchema().equals(ActiveRetreatState.SCHEMA), "retreat reducer input/slot schema mismatch");
                    ExactRef priorRef = ExactRef.fromJson(input.get("previous_body")); StrictJson.require(priorRef.equals(prior.payload()), "retreat predecessor body changed under the original writer lock");
                    var state = ActiveRetreatState.decode(DriverJson.object(artifacts.read(priorRef, ContinuityJson.DOMAIN_MAX_BYTES), ContinuityJson.DOMAIN_MAX_BYTES));
                    var beforeBasis = frameBasis(input.get("before")); var afterBasis = frameBasis(input.get("after"));
                    List<ExactRef> required = new ArrayList<>(List.of(beforeBasis.nativeFrame(), beforeBasis.driverFacts(), afterBasis.nativeFrame(), afterBasis.driverFacts()));
                    Complete before = frames.load(beforeBasis, archive), after = frames.load(afterBasis, archive); List<PlanningReadReceipt> reads = new ArrayList<>();
                    StrictJson.require(input.get("reads").isArray() && input.get("reads").size() <= 2, "finite retained retreat reads required");
                    for (var value : input.get("reads")) { ExactRef ref = ExactRef.fromJson(value); required.add(ref); var read = archive.loadRead(ref); StrictJson.require(ref.equals(archive.readReferenceOf(read)), "retreat read archive identity changed"); reads.add(read); }
                    Optional<ActionReceipt> action = Optional.empty();
                    if (!input.get("action").isNull()) { ExactRef ref = ExactRef.fromJson(input.get("action")); required.add(ref); action = Optional.of(archive.loadReceipt(ref)); }
                    StrictJson.require(request.evidence().containsAll(required), "retreat original frame/read/action evidence missing");
                    var event = decodeEvent(input.get("event"), state, new ArmyRetreatFrames.Current(after, java.time.Instant.MAX), reads); ArmyRetreatDomain.verify(head, state, event, new Proof(before, after, reads, action), archive);
                    byte[] replayed = canonical(ActiveRetreatState.encode(ActiveRetreatState.reduce(state, event)));
                    StrictJson.require(Arrays.equals(replayed, actualBody), "retreat imported body differs from its full original-evidence reducer replay");
                    var next = ActiveRetreatState.decode(DriverJson.object(actualBody, ContinuityJson.DOMAIN_MAX_BYTES));
                    for (var claim : state.claims()) StrictJson.require(next.claims().stream().anyMatch(candidate -> candidate.key().equals(claim.key())), "retreat reducer discarded an original exclusion");
                    return ActionCodec.sha256(ContinuityJson.canonical(StrictJson.object().put("actual_head_digest", ContinuityJson.digest(head.toJson())).put("result_sha256", ActionCodec.sha256(actualBody)), ContinuityJson.DOMAIN_MAX_BYTES));
                }});
    }
    private ObjectNode qualifyInitial(WriterContracts.Head head, Complete actual, ActionPorts.OutcomeArchive archive) throws IOException {
        var root = head.state().toJson(); StrictJson.require(root.has(WriterContracts.GAMEPLAY_ENTRY_FIELD) && !root.get(WriterContracts.GAMEPLAY_ENTRY_FIELD).isNull(), "no original committed first-gameplay entry qualifies a retreat reset");
        ObjectNode entry = ArmyJson.object(root.get(WriterContracts.GAMEPLAY_ENTRY_FIELD)); StrictJson.require("xar.java.first-gameplay-entry-state/v1".equals(StrictJson.text(entry.get("schema"))), "unqualified gameplay-entry schema");
        var first = ContinuityActionJournal.lookup(head.state(), StrictJson.text(entry.get("action_id")), archive).orElseThrow(() -> new IOException("original first Start action is absent from the surviving canonical action chain"));
        StrictJson.require(first.state() instanceof ActionState.Settled settled && settled.settlement() instanceof ActionState.GameplayEntered
                && first.command().origin() instanceof CommandOrigin.Frontend && first.bodySha256().equals(StrictJson.text(entry.get("action_body_sha256")))
                && archive.receiptReferenceOf(first).equals(ExactRef.fromJson(entry.get("start_receipt"))), "first retreat initialization requires the exact settled canonical Start and body");
        initialEntryVerifier.orElseThrow(() -> new IOException("actual original Start archived verifier is not installed")).verify(head, first);
        for (var retained : ContinuityActionJournal.receipts(head.state(), archive)) StrictJson.require(retained.settled() && retained.command().origin() instanceof CommandOrigin.Frontend, "prior/unresolved gameplay actions forbid empty retreat initialization");
        var observation = ((ActionState.GameplayEntered) ((ActionState.Settled) first.state()).settlement()).observation();
        StrictJson.require(actual.identity().equals(observation.after()) && actual.source().equals(first.command().source()) && actual.sessionId().equals(first.command().sessionId())
                && actual.originalEvidence().equals(observation.originalEvidence()) && actual.identity().machineId().equals(head.state().machineId()), "initial retreat frame differs from the original independently observed first Start");
        var frame = ArmyJson.object(entry.get("frame")); var game = ArmyJson.object(entry.get("game"));
        StrictJson.require(actual.identity().frame().snapshotId().equals(StrictJson.text(frame.get("snapshot_id"))) && actual.identity().frame().revision().equals(ArmyJson.integer(frame.get("revision")))
                && actual.identity().frame().identity().nativeRevision().equals(ArmyJson.integer(frame.get("native_revision"))) && actual.identity().frame().identity().dateRaw().equals(ArmyJson.integer(frame.get("date_raw")))
                && actual.identity().frame().identity().player().equals(ArmyJson.integer(frame.get("player_character_id"))) && actual.connectionGeneration().toString().equals(StrictJson.text(frame.get("connection_generation")))
                && actual.identity().frame().episodeRunId().equals(StrictJson.text(entry.get("episode_id"))) && actual.sessionId().equals(StrictJson.text(entry.get("session_id")))
                && actual.identity().game().pid() == ArmyJson.integer(game.get("pid")).longValueExact() && actual.identity().game().creationFiletime().value().toString().equals(StrictJson.text(game.get("creation_filetime"))), "first retreat initialization crossed entry frame/Game/episode/session");
        var full = org.xar.ck3.control.application.checkpoint.DriverStateSnapshot.decodeComplete(archive.loadMaterial(ExactRef.fromJson(entry.get("full_driver"))).bytes());
        StrictJson.require(full.commandHistory().isEmpty() && full.session().episodeRunId().equals(actual.identity().frame().episodeRunId()) && full.session().bridgePid() == actual.identity().game().pid(), "initial retreat domain requires the actual source-produced empty first Driver");
        var reconstructed = frames.load(new NativeEffectEvidence.FrameBasis(actual.originalEvidence(), ExactRef.fromJson(entry.get("driver_facts"))), archive);
        ArmyRetreatFrames.same(new ArmyRetreatFrames.Current(actual, java.time.Instant.MAX), new ArmyRetreatFrames.Current(reconstructed, java.time.Instant.MAX)); return entry.deepCopy();
    }
    private static List<ExactRef> initialEvidence(ObjectNode entry, Complete actual) {
        List<ExactRef> evidence = new ArrayList<>(); for (String field : List.of("start_receipt", "entry_basis", "full_driver", "driver_facts")) evidence.add(ExactRef.fromJson(entry.get(field)));
        var source = ArmyJson.object(entry.get("source")); for (String field : List.of("implementation", "policy", "environment")) evidence.add(ExactRef.fromJson(source.get(field)));
        var basis = NativeEffectEvidence.basis(actual); evidence.add(basis.nativeFrame()); evidence.add(basis.driverFacts()); return evidence.stream().distinct().toList();
    }
    private static List<ExactRef> observedInitialEvidence(ObjectNode entry, Complete actual, ActionPorts.OutcomeArchive archive) throws IOException {
        var details = ObservedGameplayEntry.decode(entry);
        List<ExactRef> evidence = new ArrayList<>(details.evidence());
        var basis = NativeEffectEvidence.basis(actual); evidence.add(basis.nativeFrame()); evidence.add(basis.driverFacts());
        var semRef = observedSemanticOriginal(details, archive);
        evidence.add(semRef);
        return evidence.stream().distinct().toList();
    }

    static ExactRef observedSemanticOriginal(ObservedGameplayEntry.Details entry, ActionPorts.OutcomeArchive archive) throws IOException {
        var raw = archive.loadFullMaterial(entry.driverFacts());
        return org.xar.ck3.control.application.driver.DriverSnapshotFacts.observationOriginalReference(raw).orElseThrow(() -> new IOException("observed entry lacks stored KnownOriginal semantic reference"));
    }
    static void requireObservedCurrentFrame(ObservedGameplayEntry.Details entry, Complete actual) {
        var identity=actual.identity();var frame=identity.frame();
        StrictJson.require(identity.machineId().equals(entry.machineId()) && identity.game().equals(entry.game())
                && actual.sessionId().equals(entry.sessionId()) && frame.episodeRunId().equals(entry.episodeId())
                && frame.identity().player().equals(java.math.BigInteger.valueOf(entry.actorId()))
                && frame.identity().dateRaw().equals(java.math.BigInteger.valueOf(entry.dateRaw()))
                && frame.revision().compareTo(java.math.BigInteger.valueOf(entry.revision()))>=0
                && frame.identity().nativeRevision().compareTo(entry.nativeRevision())>=0
                && actual.connectionGeneration().compareTo(entry.connectionGeneration())>=0
                && new OpportunityJson.Bool(true).equals(actual.semantic().get("paused"))
                && new OpportunityJson.Bool(true).equals(actual.semantic().get("map_ready")),
                "observed retreat initialization crossed its canonical Game/owner/date or current paused frame");
    }
    private ObjectNode qualifyObservedInitial(WriterContracts.Head head, Complete actual, ActionPorts.OutcomeArchive archive, ObjectNode entryNode) throws IOException {
        var entry=ObservedGameplayEntry.decode(entryNode);
        StrictJson.require(head.state().machineId().equals(entry.machineId()),"observed retreat entry belongs to another writer machine");
        requireObservedCurrentFrame(entry,actual);
        for(var receipt:ContinuityActionJournal.receipts(head.state(),archive))
            StrictJson.require(receipt.settled() && receipt.command().origin() instanceof CommandOrigin.Frontend,
                    "prior or unresolved gameplay actions forbid empty observed retreat initialization");
        var full=org.xar.ck3.control.application.checkpoint.DriverStateSnapshot.decodeComplete(archive.loadMaterial(entry.fullDriver()).bytes());
        StrictJson.require(full.commandHistory().isEmpty() && full.session().actorId().equals(java.math.BigInteger.valueOf(entry.actorId()))
                && full.session().episodeRunId().equals(entry.episodeId()) && full.session().bridgePid()==entry.game().pid(),
                "observed retreat initialization requires its complete empty original Driver");
        var original=frames.load(new NativeEffectEvidence.FrameBasis(entry.nativeFrame(),observedSemanticOriginal(entry,archive)),archive);
        requireObservedCurrentFrame(entry,original);
        var originalFrame=original.identity().frame();
        StrictJson.require(originalFrame.snapshotId().equals(entry.snapshotId())
                && originalFrame.revision().equals(java.math.BigInteger.valueOf(entry.revision()))
                && originalFrame.identity().nativeRevision().equals(entry.nativeRevision())
                && original.connectionGeneration().equals(entry.connectionGeneration())
                && actual.source().equals(original.source()),"observed retreat original entry frame/source differs");
        var current=frames.load(NativeEffectEvidence.basis(actual),archive);
        ArmyRetreatFrames.same(new ArmyRetreatFrames.Current(actual,java.time.Instant.MAX),
                new ArmyRetreatFrames.Current(current,java.time.Instant.MAX));
        return entryNode.deepCopy();
    }

    private static void verify(org.xar.ck3.control.continuity.ContinuityState head, ActiveRetreatState.State state, ActiveRetreatState.Event event, Proof proof, ActionPorts.OutcomeArchive archive) {
        Complete before = proof.before(), after = proof.after();
        StrictJson.require(before.identity().machineId().equals(head.machineId()) && after.identity().machineId().equals(head.machineId())
                && before.identity().game().equals(after.identity().game()) && before.source().equals(after.source()) && before.sessionId().equals(after.sessionId()), "retreat proof crossed original machine/Game/source/session");
        var current = new ArmyRetreatFrames.Current(after, java.time.Instant.MAX); var original = new ArmyRetreatFrames.Current(before, java.time.Instant.MAX);
        proof.action().ifPresent(receipt -> StrictJson.require(ContinuityActionJournal.lookup(head, receipt.command().actionId(), archive).filter(receipt::equals).isPresent(), "retreat action proof is not the actual canonical writer receipt"));
        switch (event) {
            case ActiveRetreatState.StartPreview value -> { StrictJson.require(value.frame().equals(original.source()) && proof.reads().isEmpty(), "preview start differs from its original actual source"); ArmyRetreatFrames.same(original, current); }
            case ActiveRetreatState.FinishPreview value -> {
                ArmyRetreatFrames.same(original, current); StrictJson.require(value.frame().equals(original.source()) && proof.reads().size() == 2, "available preview requires original control and route reads");
                Obj preview = value.normalizedPreview(); int selected = OpportunityJson.integer(preview.get("selected_public_cunit_id"), "selected").intValueExact(); int target = OpportunityJson.integer(preview.get("target_province_id"), "target").intValueExact();
                var controlReceipt = proof.reads().get(0); Context controlContext = context(controlReceipt); var call = new ArmyCalls.Unit(PublicMethod.QUERY_BATTLE_CONTROL_SNAPSHOT_V1, revision(controlContext), new PublicUnitId(selected));
                StrictJson.require(controlContext.before().equals(before.identity()), "retreat preview control read changed its original frame");
                var control = (ArmyBattleReads.Control) ArmyBattleReads.decode(new ArmyBattleReads.Selection(call, controlContext), controlReceipt);
                var routeReceipt = proof.reads().get(1); Context routeContext = context(routeReceipt); StrictJson.require(routeContext.before().equals(before.identity()), "retreat preview route read changed its original frame");
                var route = ArmyRouteReads.decode(new ArmyRouteReads.Selection(routeContext, new PublicUnitId(selected), control.value().combatProvince(), new PositiveId(target)), routeReceipt);
                Obj token = OpportunityJson.object(preview.get("target_preview"), "target"); String candidate = OpportunityJson.text(token.get("candidate_token"), "candidate token");
                Obj rebuilt = ArmyRetreatPreview.compose(new ArmyCalls.RetreatPreview(revision(controlContext), new PublicUnitId(selected), new PositiveId(target)), original.source(), control.value(), Optional.of(route), Optional.of(candidate), Optional.empty());
                StrictJson.require(rebuilt.equals(preview), "retreat preview differs from its actual full Native control/route evidence");
            }
            case ActiveRetreatState.StartOrder value -> { ArmyRetreatFrames.same(original, current); StrictJson.require(value.order().source().equals(original.source()), "retreat durable claim changed its actual source frame"); ArmyRetreatOrders.matches(state, value.order()); }
            case ActiveRetreatState.UnknownOrder value -> { StrictJson.require(proof.action().isPresent(), "unknown retreat retains an actual original coordinator receipt"); StrictJson.require(state.pending().isPresent() && ActiveRetreatState.ClaimKey.of(state.pending().orElseThrow()).equals(value.key()), "unknown retreat replaced original intent"); }
            case ActiveRetreatState.NativeOrderResult value -> { var order = state.pending().orElseThrow(); StrictJson.require(value.key().equals(ActiveRetreatState.ClaimKey.of(order)), "retreat ACK changed original intent"); StrictJson.require(submission(order, proof.action().orElseThrow()).equals(value.originalNativeResult()), "retreat ACK body differs from actual canonical move child"); }
            case ActiveRetreatState.StartObserve value -> StrictJson.require(value.frame().equals(current.source()) && proof.reads().isEmpty(), "retreat observe start lacks its actual source frame");
            case ActiveRetreatState.FinishObserve value -> {
                StrictJson.require(value.frame().equals(current.source()) && !proof.reads().isEmpty(), "retreat independent post needs original lifecycle reads");
                var result = post(state.pending().orElseThrow(), current, proof.reads()); StrictJson.require(result.json().equals(value.independentPost().json()), "retreat post is not the actual independent lifecycle replay");
            }
        }
    }
    public static ActiveRetreatPost.Result post(ActiveRetreatProposal.Order order, ArmyRetreatFrames.Current current, List<PlanningReadReceipt> reads) {
        StrictJson.require(!reads.isEmpty() && reads.size() <= 2, "one transition plus optional original terminal read required");
        var first = reads.getFirst(); Context c = context(first); StrictJson.require(c.before().equals(current.actual().identity()), "retreat transition read differs from actual current post frame");
        var transition = (ArmyBattleReads.Transition) decodePost(new ArmyCalls.CombatId(PublicMethod.QUERY_BATTLE_TRANSITION_V1, revision(c), new FullId(order.arguments().expectedCombatId())), c, first);
        ActiveRetreatPost.Result result = ActiveRetreatPost.transition(order, current.actual().semantic(), transition.normalized());
        if (reads.size() == 2) {
            StrictJson.require(result instanceof ActiveRetreatPost.Pending pending && pending.terminalQueryRequired(), "terminal may only follow actual absent original Combat lifecycle");
            var terminal = reads.get(1); Context tc = context(terminal); StrictJson.require(tc.before().equals(current.actual().identity()), "retreat terminal read differs from current post frame");
            var request = terminalCall(order, tc); var observed = (ArmyBattleReads.Terminal) decodePost(request,tc,terminal);
            result = ActiveRetreatPost.terminal(order, current.actual().semantic(), observed.normalized());
        }
        return result;
    }
    public static ArmyCalls.Terminal terminalCall(ActiveRetreatProposal.Order order, Context context) {
        return new ArmyCalls.Terminal(revision(context), new Present<>(new FullId(order.arguments().expectedCombatId())), new Present<>(new PublicUnitId(order.arguments().selectedPublicCunitId())), new Missing<>(), new Present<>(List.of()));
    }
    public static Obj submission(ActiveRetreatProposal.Order order, ActionReceipt child) {
        String expected = "move-army-" + order.arguments().selectedPublicCunitId() + "-to-" + order.arguments().targetProvinceId();
        var frame = child.command().before().frame(); var source = order.source();
        StrictJson.require(child.command().operation().value().equals(expected) && frame.episodeRunId().equals(source.episodeRunId())
                && frame.snapshotId().equals(source.snapshotId()) && frame.revision().equals(source.revision())
                && frame.identity().nativeRevision().equals(source.nativeRevision()) && frame.identity().dateRaw().equals(source.dateRaw())
                && frame.identity().player().equals(java.math.BigInteger.valueOf(order.selectedOwnerCharacterId())), "retreat child is not its original native move and complete source frame");
        if (child.state() instanceof ActionState.Settled settled && settled.settlement() instanceof ActionState.Rejected rejection)
            return new Obj(java.util.Map.of("accepted", new OpportunityJson.Bool(false), "status", new OpportunityJson.Text("rejected"), "rejection_reason", new OpportunityJson.Text(rejection.reason())));
        var ack = child.ack().orElseThrow(() -> new IllegalArgumentException("retreat child has no known Native ACK; retain UNKNOWN"));
        StrictJson.require(ack.nativeOk() && ack.originalResultToken().isPresent(), "retreat Native ACK is unavailable"); Obj token = DriverJson.object(ack.originalResultToken().orElseThrow().bytes(), DriverJson.MAX_NATIVE_BYTES);
        StrictJson.require(new OpportunityJson.Text(expected).equals(token.get("step")) && new OpportunityJson.Bool(true).equals(token.get("accepted"))
                && new OpportunityJson.Text("submitted").equals(token.get("status")), "retreat move did not return its original submitted ACK"); return token;
    }
    private static ArmyBattleReads.Observation decodePost(ArmyCalls.Call input,Context context,PlanningReadReceipt receipt) {
        if(receipt.request().origin() instanceof CommandOrigin.Reconciliation)
            return ArmyBattleReconciliationReads.decode(new ArmyBattleReconciliationReads.Selection(receipt.request().origin().requireReconciliation(),input,receipt.request().deadline()),receipt);
        return ArmyBattleReads.decode(new ArmyBattleReads.Selection(input,context),receipt);
    }
    private static Context context(PlanningReadReceipt receipt) { var r = receipt.request(); return new Context(r.origin() instanceof CommandOrigin.Reconciliation?r.reconciliationBefore():r.before(), r.source(), r.sessionId(), r.deadline()); }
    private static ArmyCalls.Revision revision(Context c) { return new ArmyCalls.Revision(new Present<>(c.before().frame().revision())); }
    private static byte[] canonical(Obj value) { return ContinuityJson.canonical(OpportunityJson.toNode(value), ContinuityJson.DOMAIN_MAX_BYTES); }
    private static ObjectNode basis(NativeEffectEvidence.FrameBasis value) { var n = StrictJson.object(); n.set("native_frame", value.nativeFrame().toJson()); n.set("driver_facts", value.driverFacts().toJson()); return n; }
    private static NativeEffectEvidence.FrameBasis frameBasis(com.fasterxml.jackson.databind.JsonNode value) { var n = StrictJson.object(value, Set.of("native_frame", "driver_facts")); return new NativeEffectEvidence.FrameBasis(ExactRef.fromJson(n.get("native_frame")), ExactRef.fromJson(n.get("driver_facts"))); }
    private static ObjectNode encodeEvent(ActiveRetreatState.Event event) {
        ObjectNode n = StrictJson.object();
        switch (event) {
            case ActiveRetreatState.StartPreview v -> { n.put("kind", "start_preview"); n.set("frame", OpportunityJson.toNode(v.frame().json())); }
            case ActiveRetreatState.FinishPreview v -> { n.put("kind", "finish_preview"); n.set("frame", OpportunityJson.toNode(v.frame().json())); n.set("preview", OpportunityJson.toNode(v.normalizedPreview())); }
            case ActiveRetreatState.StartOrder v -> { n.put("kind", "start_order"); n.set("order", OpportunityJson.toNode(ActiveRetreatState.order(v.order()))); }
            case ActiveRetreatState.UnknownOrder v -> { n.put("kind", "unknown_order").put("failure", v.failure()); n.set("claim", claim(v.key())); }
            case ActiveRetreatState.NativeOrderResult v -> { n.put("kind", "native_order_result"); n.set("claim", claim(v.key())); n.set("result", OpportunityJson.toNode(v.originalNativeResult())); }
            case ActiveRetreatState.StartObserve v -> { n.put("kind", "start_observe"); n.set("frame", OpportunityJson.toNode(v.frame().json())); }
            case ActiveRetreatState.FinishObserve v -> { n.put("kind", "finish_observe"); n.set("frame", OpportunityJson.toNode(v.frame().json())); n.set("post", OpportunityJson.toNode(v.independentPost().json())); }
        }
        return n;
    }
    private static ActiveRetreatState.Event decodeEvent(com.fasterxml.jackson.databind.JsonNode raw, ActiveRetreatState.State state, ArmyRetreatFrames.Current current, List<PlanningReadReceipt> reads) {
        var n = ArmyJson.object(raw); String kind = StrictJson.text(n.get("kind")); Set<String> fields = switch (kind) {
            case "start_preview", "start_observe" -> Set.of("kind", "frame"); case "finish_preview" -> Set.of("kind", "frame", "preview"); case "start_order" -> Set.of("kind", "order");
            case "unknown_order" -> Set.of("kind", "failure", "claim"); case "native_order_result" -> Set.of("kind", "claim", "result"); case "finish_observe" -> Set.of("kind", "frame", "post"); default -> throw new IllegalArgumentException("unknown retreat reducer event"); };
        StrictJson.object(n, fields); var obj = DriverJson.object(StrictJson.canonical(n), ContinuityJson.DOMAIN_MAX_BYTES);
        return switch (kind) {
            case "start_preview" -> new ActiveRetreatState.StartPreview(ActiveRetreatState.source(OpportunityJson.object(obj.get("frame"), "source")));
            case "finish_preview" -> new ActiveRetreatState.FinishPreview(ActiveRetreatState.source(OpportunityJson.object(obj.get("frame"), "source")), OpportunityJson.object(obj.get("preview"), "preview"));
            case "start_order" -> new ActiveRetreatState.StartOrder(ActiveRetreatState.order(OpportunityJson.object(obj.get("order"), "order")));
            case "unknown_order" -> new ActiveRetreatState.UnknownOrder(claim(n.get("claim")), StrictJson.text(n.get("failure")));
            case "native_order_result" -> new ActiveRetreatState.NativeOrderResult(claim(n.get("claim")), OpportunityJson.object(obj.get("result"), "result"));
            case "start_observe" -> new ActiveRetreatState.StartObserve(ActiveRetreatState.source(OpportunityJson.object(obj.get("frame"), "source")));
            case "finish_observe" -> {
                var actual = post(state.pending().orElseThrow(), current, reads);
                StrictJson.require(actual.json().equals(obj.get("post")), "serialized retreat post differs from original lifecycle replay");
                yield new ActiveRetreatState.FinishObserve(ActiveRetreatState.source(OpportunityJson.object(obj.get("frame"), "source")), actual);
            }
            default -> throw new IllegalArgumentException("unknown retreat reducer event");
        };
    }
    private static ObjectNode claim(ActiveRetreatState.ClaimKey key) { return StrictJson.object().put("episode_run_id", key.episodeRunId()).put("selected_public_cunit_id", key.selectedPublicCunitId()).put("expected_combat_id", key.expectedCombatId()); }
    private static ActiveRetreatState.ClaimKey claim(com.fasterxml.jackson.databind.JsonNode value) { var n = StrictJson.object(value, Set.of("episode_run_id", "selected_public_cunit_id", "expected_combat_id")); return new ActiveRetreatState.ClaimKey(StrictJson.text(n.get("episode_run_id")), (int) StrictJson.integer(n.get("selected_public_cunit_id"), 0, Integer.MAX_VALUE), (int) StrictJson.integer(n.get("expected_combat_id"), Integer.MIN_VALUE, Integer.MAX_VALUE)); }
}
