package org.xar.ck3.control.application.action;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.PublicDataJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.contracts.CrossJsDecimalUInt64;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedPostcondition;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;

/** Durable action metadata. Native originals are archived once and read with exact byte/SHA identity by OutcomeArchive. */
public final class ActionReceiptCodec {
    public static final String SCHEMA = "xar.java-action-receipt/v1";
    public static final String EVOLVED_SCHEMA = "xar.java-action-receipt/v2";
    public static final String PROVENANCE_SCHEMA = "xar.java-action-receipt/v3";
    public static final String FAMILY_SEND_SCHEMA = "xar.java-action-receipt/v4";
    public static final String PHYSICAL_SCHEMA = "xar.java-action-receipt/v5";
    public static final String RECONCILED_CONTROL_SCHEMA = "xar.java-action-receipt/v6";
    public static final String OPERATOR_SCHEMA = "xar.java-action-receipt/v7";
    public static final String PAUSE_CONTROL_SCHEMA = "xar.java-action-receipt/v8";
    public static final String DIRECT_WINDOW_SCHEMA = "xar.java-action-receipt/v9";
    public static final String COMPOSITE_FAILURE_EVIDENCE_SCHEMA = "xar.java-action-receipt/v10";
    public static final String FIXTURE_SCHEMA = "xar.java-action-receipt/v11";
    public static final String COMPOSITE_NO_GAMEPLAY_WRITE_SCHEMA = "xar.java-action-receipt/v12";
    public static final String LIFE_CONTROL_PREFIX_SCHEMA = "xar.java-action-receipt/v13";
    public static final int MAXIMUM_RECEIPT_BYTES = 2 * 1024 * 1024;
    private ActionReceiptCodec() { }
    public static byte[] encodeReceipt(ActionReceipt receipt, ActionPorts.OutcomeArchive archive) {
        boolean evolved = !(receipt.command().origin() instanceof CommandOrigin.Gameplay) || evolved(receipt.state());
        boolean typed = containsPush(receipt.state()); boolean family = containsFamilySend(receipt.state());
        ObjectNode row = StrictJson.object(); row.put("schema", lifeControlPrefix(receipt) ? LIFE_CONTROL_PREFIX_SCHEMA : compositeNoGameplayWrite(receipt) ? COMPOSITE_NO_GAMEPLAY_WRITE_SCHEMA : fixture(receipt) ? FIXTURE_SCHEMA : compositeFailureEvidence(receipt) ? COMPOSITE_FAILURE_EVIDENCE_SCHEMA : directWindow(receipt) ? DIRECT_WINDOW_SCHEMA : pauseControl(receipt) ? PAUSE_CONTROL_SCHEMA : operator(receipt) ? OPERATOR_SCHEMA : containsReconciledControl(receipt.state()) ? RECONCILED_CONTROL_SCHEMA : extended(receipt.state()) ? PHYSICAL_SCHEMA : family ? FAMILY_SEND_SCHEMA : typed ? PROVENANCE_SCHEMA : evolved ? EVOLVED_SCHEMA : SCHEMA); row.put("version", receipt.version()); row.put("sequence", receipt.sequence());
        row.put("body_sha256", receipt.bodySha256()); row.set("state", state(receipt.state(), archive, evolved || typed || family, typed, family));
        // The sole command codec owns numeric tokens in arguments. A JsonNode round trip here
        // would erase decimal category/negative zero and change the durable command body SHA.
        var headers = DriverJson.object(ProposalLifecycleCodec.encodePayload(row, MAXIMUM_RECEIPT_BYTES), MAXIMUM_RECEIPT_BYTES);
        var command = DriverJson.object(ActionCodec.encodeCommand(receipt.command()), ActionCodec.MAX_COMMAND_BYTES);
        byte[] encoded = PublicDataJson.encodeTyped(headers.with("command", command)).bytes();
        StrictJson.require(encoded.length <= MAXIMUM_RECEIPT_BYTES, "bounded action receipt required");
        return encoded;
    }
    public static ActionReceipt decodeReceipt(byte[] bytes, ActionPorts.OutcomeArchive archive) {
        ObjectNode row = StrictJson.object(ProposalLifecycleCodec.decodePayload(bytes, MAXIMUM_RECEIPT_BYTES), Set.of("schema", "version", "sequence", "command", "body_sha256", "state"));
        String schema = text(row, "schema"); StrictJson.require(SCHEMA.equals(schema) || EVOLVED_SCHEMA.equals(schema) || PROVENANCE_SCHEMA.equals(schema) || FAMILY_SEND_SCHEMA.equals(schema) || PHYSICAL_SCHEMA.equals(schema) || RECONCILED_CONTROL_SCHEMA.equals(schema) || OPERATOR_SCHEMA.equals(schema) || PAUSE_CONTROL_SCHEMA.equals(schema) || DIRECT_WINDOW_SCHEMA.equals(schema) || COMPOSITE_FAILURE_EVIDENCE_SCHEMA.equals(schema) || FIXTURE_SCHEMA.equals(schema) || COMPOSITE_NO_GAMEPLAY_WRITE_SCHEMA.equals(schema) || LIFE_CONTROL_PREFIX_SCHEMA.equals(schema), "exact action receipt schema required");
        OpportunityJson.Obj originalCommand = OpportunityJson.object(DriverJson.object(bytes, MAXIMUM_RECEIPT_BYTES).get("command"), "original receipt command");
        ActionCommand command = ActionCodec.decodeCommand(PublicDataJson.encodeTyped(originalCommand).bytes());
        ActionReceipt receipt = new ActionReceipt(Math.toIntExact(StrictJson.integer(row.get("version"), 1, 1)), StrictJson.integer(row.get("sequence"), 1, StrictJson.MAX_SAFE_INTEGER),
                command, text(row, "body_sha256"), state(row.get("state"), archive, !SCHEMA.equals(schema), PROVENANCE_SCHEMA.equals(schema) || PAUSE_CONTROL_SCHEMA.equals(schema), FAMILY_SEND_SCHEMA.equals(schema)));
        String expectedSchema = lifeControlPrefix(receipt) ? LIFE_CONTROL_PREFIX_SCHEMA : compositeNoGameplayWrite(receipt) ? COMPOSITE_NO_GAMEPLAY_WRITE_SCHEMA : fixture(receipt) ? FIXTURE_SCHEMA : compositeFailureEvidence(receipt) ? COMPOSITE_FAILURE_EVIDENCE_SCHEMA : directWindow(receipt) ? DIRECT_WINDOW_SCHEMA : pauseControl(receipt) ? PAUSE_CONTROL_SCHEMA : operator(receipt) ? OPERATOR_SCHEMA : containsReconciledControl(receipt.state()) ? RECONCILED_CONTROL_SCHEMA : extended(receipt.state()) ? PHYSICAL_SCHEMA : containsFamilySend(receipt.state()) ? FAMILY_SEND_SCHEMA : containsPush(receipt.state()) ? PROVENANCE_SCHEMA
                : !(command.origin() instanceof CommandOrigin.Gameplay) || evolved(receipt.state()) ? EVOLVED_SCHEMA : SCHEMA;
        StrictJson.require(expectedSchema.equals(schema), "receipt schema must describe its exact origin/evidence/provenance version");
        return receipt;
    }
    private static boolean fixture(ActionReceipt receipt){
        var settlement=receipt.state() instanceof ActionState.Settled settled?settled.settlement()
                :receipt.state() instanceof ActionState.CompositeSettled settled?settled.settlement():null;
        if(settlement instanceof ActionState.FixtureStarted started){
            StrictJson.require(receipt.state() instanceof ActionState.Settled,"fixture Start is one original native primitive");
            var primitive=(ActionState.Settled)receipt.state();started.observation().validate(receipt.command(),primitive.attempt(),primitive.dispatch());return true;
        }
        if(settlement instanceof ActionState.FixtureBusinessCompleted completed){
            StrictJson.require(receipt.state() instanceof ActionState.CompositeSettled,"fixture business settles only its upfront composite");
            completed.observation().validateParent(receipt.command());return true;
        }
        if(FixturePlan.isParent(receipt.command())){FixturePlan.requireParent(receipt.command());return true;}
        return false;
    }
    private static boolean compositeFailureEvidence(ActionReceipt receipt) {
        return receipt.state() instanceof ActionState.CompositeSettled settled
                && settled.settlement() instanceof ActionState.CompositeRejected rejected && !rejected.evidence().isEmpty();
    }
    private static boolean lifeControlPrefix(ActionReceipt receipt) {
        var value = receipt.state() instanceof ActionState.Settled primitive ? primitive.settlement()
                : receipt.state() instanceof ActionState.CompositeSettled composite ? composite.settlement() : null;
        if (!(value instanceof ActionState.LifeControlPrefixInterrupted terminal)) return false;
        StrictJson.require(receipt.state() instanceof ActionState.CompositeSettled,
                "Life control-prefix interruption requires its original composite envelope");
        terminal.observation().validateParent(receipt.command(), ((ActionState.CompositeSettled) receipt.state()).execution());
        return true;
    }
    private static boolean compositeNoGameplayWrite(ActionReceipt receipt) {
        var value = receipt.state() instanceof ActionState.Settled primitive ? primitive.settlement()
                : receipt.state() instanceof ActionState.CompositeSettled composite ? composite.settlement() : null;
        if (!(value instanceof ActionState.CompositeNoGameplayWrite terminal)) return false;
        StrictJson.require(receipt.state() instanceof ActionState.CompositeSettled,
                "no-gameplay-write terminal requires its original composite envelope");
        terminal.observation().validate(receipt.command(), ((ActionState.CompositeSettled) receipt.state()).execution());
        return true;
    }
    private static void requireCompositeFailureMaterial(ExactRef ref,ActionPorts.OutcomeArchive archive) {
        StrictJson.require(ref.bytes()>0,"actual composite failure material required");var bytes=archive.loadMaterial(ref).bytes();
        StrictJson.require(ref.bytes()==bytes.length&&ref.sha256().equals(ActionCodec.sha256(bytes)),"composite failure evidence original bytes changed");
    }
    private static boolean directWindow(ActionReceipt receipt) {
        var value = receipt.state() instanceof ActionState.Settled settled ? settled.settlement()
                : receipt.state() instanceof ActionState.CompositeSettled settled ? settled.settlement() : null;
        if (!(value instanceof ActionState.DirectFixedWindowCompleted completed)) return false;
        StrictJson.require(receipt.state() instanceof ActionState.Settled
                && receipt.command().origin() instanceof CommandOrigin.Gameplay
                && receipt.command().expectation() instanceof CommandExpectation.Gameplay,
                "direct fixed-window execution completion is only a gameplay native primitive");
        var primitive = (ActionState.Settled) receipt.state();
        completed.completion().validate(receipt.command(), primitive.attempt(), primitive.dispatch());
        return true;
    }
    private static boolean pauseControl(ActionReceipt receipt) {
        var settlement = receipt.state() instanceof ActionState.Settled settled ? settled.settlement()
                : receipt.state() instanceof ActionState.CompositeSettled settled ? settled.settlement() : null;
        if (settlement instanceof ActionState.PauseConfirmed) {
            StrictJson.require(receipt.state() instanceof ActionState.Settled
                    && receipt.command().expectation() instanceof CommandExpectation.Gameplay
                    && receipt.command().operation().value().equals("pause-map"),
                    "pause confirmation belongs only to its original gameplay native primitive");
            return true;
        }
        if (settlement instanceof ActionState.ControlSequenceCompleted sequence) {
            StrictJson.require(receipt.state() instanceof ActionState.CompositeSettled, "control sequence requires its exact composite");
            org.xar.ck3.control.application.effects.control.ControlSequenceObservation.validateParent(receipt.command());
            StrictJson.require(java.util.Arrays.equals(ActionCodec.encodeCommand(receipt.command()), ActionCodec.encodeCommand(sequence.observation().parent())),
                    "control sequence changed its original complete parent command");
            return true;
        }
        return false;
    }
    private static boolean operator(ActionReceipt receipt) {
        ActionState.Settlement settlement = receipt.state() instanceof ActionState.Settled settled ? settled.settlement()
                : receipt.state() instanceof ActionState.CompositeSettled settled ? settled.settlement() : null;
        boolean expected = receipt.command().expectation() instanceof CommandExpectation.OperatorRebind;
        StrictJson.require(!(settlement instanceof ActionState.OperatorRebound) || expected,
                "operator settlement requires the exact operator command schema/expectation");
        StrictJson.require(!expected || !(receipt.state() instanceof ActionState.CompositeRunning
                || receipt.state() instanceof ActionState.CompositeUnknown || receipt.state() instanceof ActionState.CompositeSettled
                || receipt.state() instanceof PhysicalActionState), "operator identity rebind is only a native primitive");
        StrictJson.require(!expected || settlement == null || settlement instanceof ActionState.OperatorRebound || settlement instanceof ActionState.Rejected,
                "operator command cannot reinterpret an ordinary gameplay/control settlement");
        return expected;
    }
    private static boolean containsReconciledControl(ActionState state) {
        var value = state instanceof ActionState.Settled settled ? settled.settlement()
                : state instanceof ActionState.CompositeSettled settled ? settled.settlement() : null;
        return value instanceof ActionState.ControlApplied control && control.reconciledAck().isPresent();
    }
    private static boolean extended(ActionState state) {
        return state instanceof PhysicalActionState || state instanceof ActionState.Settled settled
                && (settled.settlement() instanceof ActionState.NativeSourceCompleted || settled.settlement() instanceof ActionState.NormalExitPhaseConfirmed);
    }
    private static boolean evolved(ActionState state) {
        if (ActionTransitions.attempt(state).map(attempt -> !attempt.guard().supportingEvidence().isEmpty()).orElse(false)
                || ActionTransitions.composite(state).map(execution -> !execution.guard().supportingEvidence().isEmpty()).orElse(false)) return true;
        ActionState.Settlement settlement = state instanceof ActionState.Settled settled ? settled.settlement()
                : state instanceof ActionState.CompositeSettled settled ? settled.settlement() : null;
        return settlement != null && (!(settlement instanceof ActionState.Applied || settlement instanceof ActionState.Rejected || settlement instanceof ActionState.ControlApplied)
                || settlement instanceof ActionState.Applied applied && !applied.observation().supportingEvidence().isEmpty());
    }
    private static boolean containsFamilySend(ActionState state) {
        return state instanceof ActionState.Settled settled && settled.settlement() instanceof ActionState.FamilySendConfirmed;
    }
    private static boolean containsPush(ActionState state) {
        ActionState.Settlement settlement = state instanceof ActionState.Settled settled ? settled.settlement()
                : state instanceof ActionState.CompositeSettled settled ? settled.settlement() : null;
        return settlement instanceof ActionState.PauseConfirmed
                || settlement instanceof ActionState.Applied applied && applied.observation().provenance() instanceof ObservationProvenance.Push
                || settlement instanceof ActionState.CompositeControlApplied control && control.observation().semantic().provenance() instanceof ObservationProvenance.Push;
    }
    private static ObjectNode state(ActionState state, ActionPorts.OutcomeArchive archive, boolean evolved, boolean typed, boolean family) {
        ObjectNode row = StrictJson.object();
        if (state instanceof PhysicalActionState physical) return PhysicalActionCodec.encode(physical, archive);
        if (state instanceof ActionState.IntentDurable) { row.put("kind", "INTENT_DURABLE"); return row; }
        if (ActionTransitions.composite(state).isPresent()) {
            row.put("kind", state instanceof ActionState.CompositeRunning ? "COMPOSITE_RUNNING" : state instanceof ActionState.CompositeUnknown ? "COMPOSITE_UNKNOWN" : "COMPOSITE_SETTLED");
            row.set("execution", execution(ActionTransitions.composite(state).orElseThrow()));
            if (state instanceof ActionState.CompositeUnknown unknown) { row.put("reason", unknown.reason()); var refs = row.putArray("evidence"); unknown.evidence().forEach(ref -> refs.add(ref.toJson())); }
            if (state instanceof ActionState.CompositeSettled settled) row.set("settlement", settlement(settled.settlement(), archive, evolved, typed, family)); return row;
        }
        if (state instanceof ActionState.Submitting value) { row.put("kind", "SUBMITTING"); row.set("attempt", attempt(value.attempt(), archive)); return row; }
        if (state instanceof ActionState.Unknown value) {
            row.put("kind", "UNKNOWN"); row.set("attempt", value.attempt().map(item -> (JsonNode) attempt(item, archive)).orElse(com.fasterxml.jackson.databind.node.NullNode.instance));
            row.set("dispatch_ref", value.dispatch().map(item -> (JsonNode) archive.referenceOf(item).toJson()).orElse(com.fasterxml.jackson.databind.node.NullNode.instance)); row.put("reason", value.reason());
            var refs = row.putArray("evidence"); value.evidence().forEach(ref -> refs.add(ref.toJson())); return row;
        }
        ActionState.Attempt attempt = ActionTransitions.attempt(state).orElseThrow();
        NativeActionPort.DispatchOutcome dispatch = ActionTransitions.dispatch(state).orElseThrow();
        row.put("kind", state instanceof ActionState.AckReceived ? "ACK_RECEIVED" : state instanceof ActionState.Settled ? "SETTLED" : "REJECTED_BEFORE_DISPATCH");
        row.set("attempt", attempt(attempt, archive)); row.set("dispatch_ref", archive.referenceOf(dispatch).toJson());
        if (state instanceof ActionState.Settled settled) row.set("settlement", settlement(settled.settlement(), archive, evolved, typed, family)); return row;
    }
    private static ActionState state(JsonNode node, ActionPorts.OutcomeArchive archive, boolean evolved, boolean typed, boolean family) {
        StrictJson.require(node instanceof ObjectNode, "action state object required"); ObjectNode row = (ObjectNode) node;
        String kind = text(row, "kind");
        return switch (kind) {
            case "PHYSICAL_ACTION" -> PhysicalActionCodec.decode(row, archive);
            case "INTENT_DURABLE" -> { StrictJson.object(row, Set.of("kind")); yield new ActionState.IntentDurable(); }
            case "SUBMITTING" -> { StrictJson.object(row, Set.of("kind", "attempt")); yield new ActionState.Submitting(attempt(row.get("attempt"), archive)); }
            case "ACK_RECEIVED" -> {
                StrictJson.object(row, Set.of("kind", "attempt", "dispatch_ref")); var dispatch = archive.load(ExactRef.fromJson(row.get("dispatch_ref")));
                StrictJson.require(dispatch instanceof NativeActionPort.AckReceived, "ACK branch requires original ACK"); yield new ActionState.AckReceived(attempt(row.get("attempt"), archive), (NativeActionPort.AckReceived) dispatch);
            }
            case "UNKNOWN" -> {
                StrictJson.object(row, Set.of("kind", "attempt", "dispatch_ref", "reason", "evidence")); List<ExactRef> evidence = new ArrayList<>();
                StrictJson.require(row.get("evidence").isArray(), "UNKNOWN evidence array required"); row.get("evidence").forEach(item -> evidence.add(ExactRef.fromJson(item)));
                yield new ActionState.Unknown(row.get("attempt").isNull() ? Optional.empty() : Optional.of(attempt(row.get("attempt"), archive)),
                        row.get("dispatch_ref").isNull() ? Optional.empty() : Optional.of(archive.load(ExactRef.fromJson(row.get("dispatch_ref")))), text(row, "reason"), evidence);
            }
            case "SETTLED" -> {
                StrictJson.object(row, Set.of("kind", "attempt", "dispatch_ref", "settlement"));
                yield new ActionState.Settled(attempt(row.get("attempt"), archive), archive.load(ExactRef.fromJson(row.get("dispatch_ref"))), settlement(row.get("settlement"), archive, evolved, typed, family));
            }
            case "COMPOSITE_RUNNING" -> { StrictJson.object(row, Set.of("kind", "execution")); yield new ActionState.CompositeRunning(execution(row.get("execution"))); }
            case "COMPOSITE_UNKNOWN" -> {
                StrictJson.object(row, Set.of("kind", "execution", "reason", "evidence")); List<ExactRef> evidence = new ArrayList<>();
                StrictJson.require(row.get("evidence").isArray(), "composite evidence array required"); row.get("evidence").forEach(item -> evidence.add(ExactRef.fromJson(item)));
                yield new ActionState.CompositeUnknown(execution(row.get("execution")), text(row, "reason"), evidence);
            }
            case "COMPOSITE_SETTLED" -> { StrictJson.object(row, Set.of("kind", "execution", "settlement")); yield new ActionState.CompositeSettled(execution(row.get("execution")), settlement(row.get("settlement"), archive, evolved, typed, family)); }
            case "REJECTED_BEFORE_DISPATCH" -> {
                StrictJson.object(row, Set.of("kind", "attempt", "dispatch_ref")); var dispatch = archive.load(ExactRef.fromJson(row.get("dispatch_ref")));
                StrictJson.require(dispatch instanceof NativeActionPort.RejectedBeforeDispatch, "zero dispatch branch requires original explicit proof");
                yield new ActionState.RejectedBeforeDispatch(attempt(row.get("attempt"), archive), (NativeActionPort.RejectedBeforeDispatch) dispatch);
            }
            default -> throw new IllegalArgumentException("unsupported action state kind");
        };
    }
    private static ObjectNode lifePrefixFrame(org.xar.ck3.control.application.advance.LifeAdvanceEvidence.FrameRecord frame) {
        var row = StrictJson.object();
        row.set("identity", ProposalLifecycleCodec.observation(frame.identity()));
        row.set("observation_provenance", ObservationProvenanceCodec.encode(frame.provenance()));
        row.put("observed_at_utc", frame.observedAt().toString());
        row.set("native_frame", frame.nativeFrame().toJson());
        row.set("driver_facts", frame.driverFacts().toJson());
        row.set("semantic", frame.semantic().toJson());
        return row;
    }
    private static org.xar.ck3.control.application.advance.LifeAdvanceEvidence.FrameRecord lifePrefixFrame(JsonNode value) {
        var row = StrictJson.object(value, Set.of("identity", "observation_provenance", "observed_at_utc", "native_frame", "driver_facts", "semantic"));
        return new org.xar.ck3.control.application.advance.LifeAdvanceEvidence.FrameRecord(
                ProposalLifecycleCodec.decodeObservation(row.get("identity")), ObservationProvenanceCodec.decode(row.get("observation_provenance")),
                Instant.parse(StrictJson.utc(text(row,"observed_at_utc"))), ExactRef.fromJson(row.get("native_frame")),
                ExactRef.fromJson(row.get("driver_facts")), ExactRef.fromJson(row.get("semantic")));
    }
    private static ObjectNode attempt(ActionState.Attempt attempt, ActionPorts.OutcomeArchive archive) {
        ObjectNode row = StrictJson.object(); row.put("request_id", attempt.requestId()); row.put("submitted_at", attempt.submittedAt().toString());
        row.set("guard", encodeGuard(attempt.guard())); row.set("prepared_request_ref", archive.requestReferenceOf(attempt.preparedRequest()).toJson()); return row;
    }
    private static ActionState.Attempt attempt(JsonNode node, ActionPorts.OutcomeArchive archive) {
        ObjectNode row = StrictJson.object(node, Set.of("request_id", "submitted_at", "guard", "prepared_request_ref"));
        return new ActionState.Attempt(text(row, "request_id"), Instant.parse(text(row, "submitted_at")), decodeGuard(row.get("guard")), archive.loadRequest(ExactRef.fromJson(row.get("prepared_request_ref"))));
    }
    public static ObjectNode encodeGuard(GuardEvidence guard) {
        return CommandOriginCodec.guard(guard);
    }
    public static GuardEvidence decodeGuard(JsonNode node) {
        return CommandOriginCodec.guard(node);
    }
    private static ObjectNode settlement(ActionState.Settlement settlement, ActionPorts.OutcomeArchive archive, boolean evolved, boolean typed, boolean family) {
        ObjectNode row = StrictJson.object();
        if (settlement instanceof ActionState.LifeControlPrefixInterrupted interrupted) {
            StrictJson.require(evolved, "Life control-prefix interruption requires receipt v13");
            row.put("kind", "LIFE_CONTROL_PREFIX_INTERRUPTED");
            row.put("action_id", interrupted.observation().actionId());
            row.put("body_sha256", interrupted.observation().bodySha256());
            row.set("execution", execution(interrupted.observation().execution()));
            row.set("ending", lifePrefixFrame(interrupted.observation().ending()));
            return row;
        }
        if(settlement instanceof ActionState.FixtureStarted started){
            StrictJson.require(evolved&&!typed&&!family,"fixture first-map proof requires exact receipt v11");
            row.put("kind","FIXTURE_STARTED");row.set("observation",FixtureProofCodec.start(started.observation(),archive));return row;
        }
        if(settlement instanceof ActionState.FixtureBusinessCompleted completed){
            StrictJson.require(evolved&&!typed&&!family,"fixture business proof requires exact receipt v11");
            row.put("kind","FIXTURE_BUSINESS_COMPLETED");row.set("observation",FixtureProofCodec.business(completed.observation(),archive));return row;
        }
        if (settlement instanceof ActionState.DirectFixedWindowCompleted completed) {
            StrictJson.require(evolved && !typed && !family, "direct fixed-window completion requires exact receipt v9");
            row.put("kind", "DIRECT_FIXED_WINDOW_COMPLETED");
            row.set("completion", completed.completion().encode(archive)); return row;
        }
        if (settlement instanceof ActionState.PauseConfirmed pause) {
            StrictJson.require(evolved && typed, "native Push pause confirmation requires receipt v8");
            row.put("kind", "PAUSE_CONFIRMED");
            row.set("semantic", settlement(new ActionState.Applied(pause.observation()), archive, true, true, false)); return row;
        }
        if (settlement instanceof ActionState.ControlSequenceCompleted sequence) {
            StrictJson.require(evolved, "source-bound control sequence requires receipt v8");
            row.put("kind", "CONTROL_SEQUENCE_COMPLETED");
            row.set("observation", StrictJson.parse(sequence.observation().encode())); return row;
        }
        if (settlement instanceof ActionState.OperatorRebound rebound) {
            row.put("kind", "OPERATOR_REBOUND"); row.set("observation", StrictJson.parse(rebound.observation().encode())); return row;
        }
        if (settlement instanceof ActionState.NativeSourceCompleted source) {
            row.put("kind", "NATIVE_SOURCE_COMPLETED"); row.set("observation", StrictJson.parse(source.observation().encode())); return row;
        }
        if (settlement instanceof ActionState.NormalExitPhaseConfirmed phase) {
            row.put("kind", "NORMAL_EXIT_PHASE_CONFIRMED"); row.set("observation", phase.observation().encode(archive)); return row;
        }
        if (settlement instanceof ActionState.FamilySendConfirmed sent) {
            StrictJson.require(family && evolved && !typed, "typed outgoing family request requires exact receipt v4");
            row.put("kind", "FAMILY_SEND_CONFIRMED");
            row.set("observation", org.xar.ck3.control.application.effects.family.FamilySendObservationCodec.encode(sent.observation(), archive)); return row;
        }
        if (settlement instanceof ActionState.SwaySchedulerCompleted scheduler) {
            StrictJson.require(evolved, "canonical Sway scheduler completion requires receipt v2"); row.put("kind", "SWAY_SCHEDULER_COMPLETED");
            row.set("proof_ref", archive.materialReferenceOf(new RawJson(scheduler.proof().encode())).toJson()); return row;
        }
        if (settlement instanceof ActionState.LifecycleControlApplied control) {
            StrictJson.require(evolved, "terminal modal control requires receipt v2"); row.put("kind", "LIFECYCLE_CONTROL_APPLIED");
            row.set("observation", LifecycleControlCodec.encode(control.observation(), archive::readReferenceOf)); return row;
        }
        if (settlement instanceof ActionState.NonAppliedTerminal terminal) {
            StrictJson.require(evolved, "independent non-applied terminal requires receipt v2"); row.put("kind", "NON_APPLIED_TERMINAL");
            row.set("observation", ActionTerminalCodec.encode(terminal.observation(), archive::readReferenceOf)); return row;
        }
        if (settlement instanceof ActionState.CompositeRejected rejected) {
            StrictJson.require(evolved, "canonical composite rejection requires receipt v2"); row.put("kind", "COMPOSITE_REJECTED"); row.put("reason", rejected.reason());
            var children = row.putArray("children"); rejected.children().forEach(child -> { var item = children.addObject(); item.put("action_id", child.actionId()); item.put("body_sha256", child.bodySha256()); });
            if(!rejected.evidence().isEmpty()){var evidence=row.putArray("evidence");for(var ref:rejected.evidence()){requireCompositeFailureMaterial(ref,archive);evidence.add(ref.toJson());}}return row;
        }
        if (settlement instanceof ActionState.CompositeNoGameplayWrite write) {
            StrictJson.require(evolved, "composite no-gameplay write requires receipt v12");
            row.put("kind", "COMPOSITE_NO_GAMEPLAY_WRITE");
            row.put("action_id", write.observation().actionId());
            row.put("body_sha256", write.observation().bodySha256());
            row.set("execution", execution(write.observation().execution()));
            return row;
        }
        if (settlement instanceof ActionState.LifecycleApplied lifecycle) {
            StrictJson.require(evolved, "canonical lifecycle settlement requires receipt v2"); row.put("kind", "LIFECYCLE_APPLIED");
            row.set("proof_ref", archive.materialReferenceOf(new RawJson(lifecycle.proof().encode())).toJson()); return row;
        }
        if (settlement instanceof ActionState.CompositeControlApplied control) {
            StrictJson.require(evolved, "composite control requires receipt v2"); row.put("kind", "COMPOSITE_CONTROL_APPLIED");
            row.set("terminal_status_ref", archive.readReferenceOf(control.observation().terminalStatus()).toJson());
            var reads = row.putArray("supporting_reads"); control.observation().supportingReads().forEach(read -> reads.add(archive.readReferenceOf(read).toJson()));
            row.set("semantic", settlement(new ActionState.Applied(control.observation().semantic()), archive, true, typed, family)); return row;
        }
        if (settlement instanceof ActionState.FrontendApplied frontend) {
            StrictJson.require(evolved, "frontend settlement requires receipt v2"); row.put("kind", "FRONTEND_APPLIED"); row.set("observation", CommandOriginCodec.frontendEffect(frontend.observation())); return row;
        }
        if (settlement instanceof ActionState.GameplayEntered entered) {
            StrictJson.require(evolved, "gameplay entry requires receipt v2"); row.put("kind", "GAMEPLAY_ENTERED"); row.set("observation", CommandOriginCodec.gameplayEntry(entered.observation(), archive::readReferenceOf)); return row;
        }
        if (settlement instanceof ActionState.ControlApplied control) {
            row.put("kind", control.reconciledAck().isPresent() ? "CONTROL_APPLIED_RECONCILED" : "CONTROL_APPLIED");
            control.reconciledAck().ifPresent(value -> row.set("reconciled_ack_ref", value.reference(archive).toJson()));
            row.set("read_ref", archive.readReferenceOf(control.read()).toJson());
            var supporting = row.putArray("supporting_reads"); control.supportingReads().forEach(read -> supporting.add(archive.readReferenceOf(read).toJson()));
            row.set("observation", ProposalLifecycleCodec.expected(new ExpectedPostcondition(1, control.read().after().binding().observed(), control.read().request().source(), control.observerSchema(), control.actual()))); return row;
        }
        if (settlement instanceof ActionState.Rejected rejected) {
            row.put("kind", "REJECTED"); row.put("request_id", rejected.requestId()); row.put("reason", rejected.reason()); row.set("original_evidence", rejected.originalEvidence().toJson()); return row;
        }
        ActionState.EffectObservation effect = ((ActionState.Applied) settlement).observation(); row.put("kind", "APPLIED");
        row.set("observation", ProposalLifecycleCodec.expected(new ExpectedPostcondition(1, effect.after(), effect.source(), effect.observerSchema(), effect.actual())));
        row.put("session_id", effect.sessionId());
        if (typed) row.set("observation_provenance", ObservationProvenanceCodec.encode(effect.provenance()));
        else { StrictJson.require(effect.provenance() instanceof ObservationProvenance.Query, "historical effect requires its actual query request ID"); row.put("read_request_id", ((ObservationProvenance.Query) effect.provenance()).requestId()); }
        row.put("observed_at", effect.observedAt().toString()); row.set("original_evidence", effect.originalEvidence().toJson());
        if (evolved) { var supporting = row.putArray("supporting_evidence"); effect.supportingEvidence().forEach(ref -> supporting.add(ref.toJson())); }
        return row;
    }
    private static ActionState.Settlement settlement(JsonNode node, ActionPorts.OutcomeArchive archive, boolean evolved, boolean typed, boolean family) {
        StrictJson.require(node instanceof ObjectNode, "settlement object required"); ObjectNode row = (ObjectNode) node;
        if (text(row,"kind").equals("LIFE_CONTROL_PREFIX_INTERRUPTED")) {
            StrictJson.require(evolved, "Life control-prefix interruption requires receipt v13");
            StrictJson.object(row, Set.of("kind", "action_id", "body_sha256", "execution", "ending"));
            return new ActionState.LifeControlPrefixInterrupted(new org.xar.ck3.control.application.advance.LifeControlPrefixInterruption(
                    text(row,"action_id"), text(row,"body_sha256"), execution(row.get("execution")), lifePrefixFrame(row.get("ending"))));
        }
        if(text(row,"kind").equals("FIXTURE_STARTED")){
            StrictJson.require(evolved&&!typed&&!family,"fixture first-map proof requires exact receipt v11");StrictJson.object(row,Set.of("kind","observation"));
            return new ActionState.FixtureStarted(FixtureProofCodec.start(row.get("observation"),archive));
        }
        if(text(row,"kind").equals("FIXTURE_BUSINESS_COMPLETED")){
            StrictJson.require(evolved&&!typed&&!family,"fixture business proof requires exact receipt v11");StrictJson.object(row,Set.of("kind","observation"));
            return new ActionState.FixtureBusinessCompleted(FixtureProofCodec.business(row.get("observation"),archive));
        }
        if (text(row, "kind").equals("DIRECT_FIXED_WINDOW_COMPLETED")) {
            StrictJson.require(evolved && !typed && !family, "direct fixed-window completion requires exact receipt v9");
            StrictJson.object(row, Set.of("kind", "completion"));
            return new ActionState.DirectFixedWindowCompleted(
                    org.xar.ck3.control.application.effects.NativeDirectFixedWindowObservation.Completion.decode(row.get("completion"), archive));
        }
        if (text(row, "kind").equals("PAUSE_CONFIRMED")) {
            StrictJson.require(evolved && typed, "native Push pause requires exact typed receipt v8");
            StrictJson.object(row, Set.of("kind", "semantic"));
            var semantic = settlement(row.get("semantic"), archive, true, true, false);
            StrictJson.require(semantic instanceof ActionState.Applied applied && applied.observation().provenance() instanceof ObservationProvenance.Push,
                    "pause requires the exact original native Push semantic DATA");
            return new ActionState.PauseConfirmed(((ActionState.Applied) semantic).observation());
        }
        if (text(row, "kind").equals("CONTROL_SEQUENCE_COMPLETED")) {
            StrictJson.require(evolved, "source-bound control requires receipt v8");
            StrictJson.object(row, Set.of("kind", "observation"));
            return new ActionState.ControlSequenceCompleted(org.xar.ck3.control.application.effects.control.ControlSequenceObservation.decode(StrictJson.canonical(row.get("observation"))));
        }
        if (text(row, "kind").equals("OPERATOR_REBOUND")) {
            StrictJson.object(row, Set.of("kind", "observation"));
            return new ActionState.OperatorRebound(org.xar.ck3.control.application.planning.identity.OperatorPlayerSwitch.decodeCompletion(StrictJson.canonical(row.get("observation"))));
        }
        if (text(row, "kind").equals("NATIVE_SOURCE_COMPLETED")) {
            StrictJson.object(row, Set.of("kind", "observation"));
            return new ActionState.NativeSourceCompleted(org.xar.ck3.control.application.effects.coa.NativeSourceObservation.decode(StrictJson.canonical(row.get("observation"))));
        }
        if (text(row, "kind").equals("NORMAL_EXIT_PHASE_CONFIRMED")) {
            StrictJson.object(row, Set.of("kind", "observation"));
            return new ActionState.NormalExitPhaseConfirmed(org.xar.ck3.control.application.effects.normalexit.NormalExitPhaseObservation.decode(row.get("observation"), archive));
        }
        if (text(row, "kind").equals("FAMILY_SEND_CONFIRMED")) {
            StrictJson.require(family && evolved && !typed, "typed outgoing family request requires exact receipt v4");
            StrictJson.object(row, Set.of("kind", "observation"));
            return new ActionState.FamilySendConfirmed(org.xar.ck3.control.application.effects.family.FamilySendObservationCodec.decode(row.get("observation"), archive));
        }
        if (text(row, "kind").equals("SWAY_SCHEDULER_COMPLETED")) {
            StrictJson.require(evolved, "canonical Sway scheduler completion requires receipt v2"); StrictJson.object(row, Set.of("kind", "proof_ref"));
            return new ActionState.SwaySchedulerCompleted(org.xar.ck3.control.application.planning.sway.SwaySchedulerCompletionCodec.decodeRecorded(archive.loadMaterial(ExactRef.fromJson(row.get("proof_ref"))).bytes()));
        }
        if (text(row, "kind").equals("LIFECYCLE_CONTROL_APPLIED")) {
            StrictJson.require(evolved, "terminal modal control requires receipt v2"); StrictJson.object(row, Set.of("kind", "observation"));
            return new ActionState.LifecycleControlApplied(LifecycleControlCodec.decode(row.get("observation"), archive::loadRead));
        }
        if (text(row, "kind").equals("NON_APPLIED_TERMINAL")) {
            StrictJson.require(evolved, "independent non-applied terminal requires receipt v2"); StrictJson.object(row, Set.of("kind", "observation"));
            return new ActionState.NonAppliedTerminal(ActionTerminalCodec.decode(row.get("observation"), archive::loadRead));
        }
        if (text(row, "kind").equals("COMPOSITE_REJECTED")) {
            StrictJson.require(evolved, "canonical composite rejection requires receipt v2"); StrictJson.object(row, row.has("evidence") ? Set.of("kind", "reason", "children", "evidence") : Set.of("kind", "reason", "children"));
            StrictJson.require(row.get("children").isArray(), "exact rejected child array required"); List<CompositeExecution.Child> children = new ArrayList<>();
            row.get("children").forEach(raw -> { var child = StrictJson.object(raw, Set.of("action_id", "body_sha256")); children.add(new CompositeExecution.Child(text(child, "action_id"), text(child, "body_sha256"))); });
            var evidence=new ArrayList<ExactRef>();if(row.has("evidence")){StrictJson.require(row.get("evidence").isArray()&&row.get("evidence").size()>0&&row.get("evidence").size()<=64,"nonempty bounded composite failure evidence required");for(var item:row.get("evidence")){var ref=ExactRef.fromJson(item);requireCompositeFailureMaterial(ref,archive);evidence.add(ref);}}
            return new ActionState.CompositeRejected(text(row, "reason"), children,evidence);
        }
        if (text(row, "kind").equals("COMPOSITE_NO_GAMEPLAY_WRITE")) {
            StrictJson.require(evolved, "composite no-gameplay write requires receipt v12");
            StrictJson.object(row, Set.of("kind", "action_id", "body_sha256", "execution"));
            var exec = execution(row.get("execution"));
            var obs = new CompositeNoGameplayWriteObservation(text(row, "action_id"), text(row, "body_sha256"), exec);
            return new ActionState.CompositeNoGameplayWrite(obs);
        }
        if (text(row, "kind").equals("LIFECYCLE_APPLIED")) {
            StrictJson.require(evolved, "canonical lifecycle settlement requires receipt v2"); StrictJson.object(row, Set.of("kind", "proof_ref"));
            RawJson original = archive.loadMaterial(ExactRef.fromJson(row.get("proof_ref")));
            return new ActionState.LifecycleApplied(org.xar.ck3.control.application.lifecycle.LifecycleProofCodec.decodeRecorded(original.bytes()));
        }
        if (text(row, "kind").equals("FRONTEND_APPLIED")) {
            StrictJson.require(evolved, "frontend settlement requires receipt v2"); StrictJson.object(row, Set.of("kind", "observation")); return new ActionState.FrontendApplied(CommandOriginCodec.frontendEffect(row.get("observation")));
        }
        if (text(row, "kind").equals("GAMEPLAY_ENTERED")) {
            StrictJson.require(evolved, "gameplay entry requires receipt v2"); StrictJson.object(row, Set.of("kind", "observation")); return new ActionState.GameplayEntered(CommandOriginCodec.gameplayEntry(row.get("observation"), archive::loadRead));
        }
        if (text(row, "kind").equals("COMPOSITE_CONTROL_APPLIED")) {
            StrictJson.require(evolved, "composite control requires receipt v2"); StrictJson.object(row, Set.of("kind", "terminal_status_ref", "supporting_reads", "semantic"));
            StrictJson.require(row.get("supporting_reads").isArray(), "supporting control reads array required"); List<PlanningReadReceipt> supporting = new ArrayList<>();
            row.get("supporting_reads").forEach(ref -> supporting.add(archive.loadRead(ExactRef.fromJson(ref))));
            ActionState.Settlement semantic = settlement(row.get("semantic"), archive, true, typed, family); StrictJson.require(semantic instanceof ActionState.Applied, "composite control semantic branch must be an actual original semantic observation");
            return new ActionState.CompositeControlApplied(new CompositeControlObservation(archive.loadRead(ExactRef.fromJson(row.get("terminal_status_ref"))), supporting, ((ActionState.Applied) semantic).observation()));
        }
        if (text(row, "kind").equals("CONTROL_APPLIED") || text(row, "kind").equals("CONTROL_APPLIED_RECONCILED")) {
            boolean reconciled = text(row, "kind").equals("CONTROL_APPLIED_RECONCILED");
            StrictJson.object(row, reconciled ? Set.of("kind", "read_ref", "supporting_reads", "observation", "reconciled_ack_ref") : Set.of("kind", "read_ref", "supporting_reads", "observation"));
            ObjectNode observation = StrictJson.object(row.get("observation"), Set.of("version", "before", "source", "observer_schema", "values")); StrictJson.integer(observation.get("version"), 1, 1);
            PlanningReadReceipt read = archive.loadRead(ExactRef.fromJson(row.get("read_ref")));
            StrictJson.require(ProposalLifecycleCodec.decodeObservation(observation.get("before")).equals(read.after().binding().observed()) && G2Wire.source(observation.get("source")).equals(read.request().source()), "control read original observation/source drift");
            StrictJson.require(row.get("supporting_reads").isArray(), "supporting reads array required"); List<PlanningReadReceipt> supporting = new ArrayList<>();
            row.get("supporting_reads").forEach(item -> supporting.add(archive.loadRead(ExactRef.fromJson(item))));
            Optional<ReconciledControlAck> late = Optional.empty();
            if (reconciled) {
                var received = archive.load(ExactRef.fromJson(row.get("reconciled_ack_ref")));
                StrictJson.require(received instanceof NativeActionPort.AckReceived, "reconciled control sidecar must be the actual received original ACK");
                late = Optional.of(new ReconciledControlAck((NativeActionPort.AckReceived) received));
            }
            return new ActionState.ControlApplied(read, supporting, text(observation, "observer_schema"), ProposalLifecycleCodec.values(observation.get("values")), late);
        }
        if (text(row, "kind").equals("REJECTED")) {
            StrictJson.object(row, Set.of("kind", "request_id", "reason", "original_evidence"));
            return new ActionState.Rejected(text(row, "request_id"), text(row, "reason"), ExactRef.fromJson(row.get("original_evidence")));
        }
        StrictJson.object(row, typed ? Set.of("kind", "observation", "session_id", "observation_provenance", "observed_at", "original_evidence", "supporting_evidence")
                : evolved ? Set.of("kind", "observation", "session_id", "read_request_id", "observed_at", "original_evidence", "supporting_evidence") : Set.of("kind", "observation", "session_id", "read_request_id", "observed_at", "original_evidence")); StrictJson.require(text(row, "kind").equals("APPLIED"), "known settlement kind required");
        ObjectNode observation = StrictJson.object(row.get("observation"), Set.of("version", "before", "source", "observer_schema", "values"));
        StrictJson.integer(observation.get("version"), 1, 1);
        List<ExactRef> supporting = new ArrayList<>();
        if (evolved) { StrictJson.require(row.get("supporting_evidence").isArray(), "supporting effect evidence array required"); row.get("supporting_evidence").forEach(ref -> supporting.add(ExactRef.fromJson(ref))); }
        return new ActionState.Applied(new ActionState.EffectObservation(ProposalLifecycleCodec.decodeObservation(observation.get("before")), G2Wire.source(observation.get("source")),
                text(row, "session_id"), text(observation, "observer_schema"), ProposalLifecycleCodec.values(observation.get("values")), typed ? ObservationProvenanceCodec.decode(row.get("observation_provenance")) : new ObservationProvenance.Query(text(row, "read_request_id")),
                Instant.parse(text(row, "observed_at")), ExactRef.fromJson(row.get("original_evidence")), supporting));
    }
    private static ObjectNode execution(CompositeExecution execution) {
        ObjectNode row = StrictJson.object(); row.put("handler_id", execution.handlerId()); row.put("started_at", execution.startedAt().toString()); row.set("guard", encodeGuard(execution.guard()));
        var children = row.putArray("children"); for (CompositeExecution.Child child : execution.children()) { var item = children.addObject(); item.put("action_id", child.actionId()); item.put("body_sha256", child.bodySha256()); } return row;
    }
    private static CompositeExecution execution(JsonNode node) {
        ObjectNode row = StrictJson.object(node, Set.of("handler_id", "started_at", "guard", "children")); StrictJson.require(row.get("children").isArray(), "composite child array required");
        List<CompositeExecution.Child> children = new ArrayList<>(); row.get("children").forEach(item -> { ObjectNode child = StrictJson.object(item, Set.of("action_id", "body_sha256")); children.add(new CompositeExecution.Child(text(child, "action_id"), text(child, "body_sha256"))); });
        return new CompositeExecution(text(row, "handler_id"), Instant.parse(text(row, "started_at")), decodeGuard(row.get("guard")), children);
    }
    private static String text(ObjectNode row, String field) { return StrictJson.text(row.get(field)); }
}
