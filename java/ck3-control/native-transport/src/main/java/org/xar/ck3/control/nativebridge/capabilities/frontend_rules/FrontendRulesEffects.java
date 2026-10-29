package org.xar.ck3.control.nativebridge.capabilities.frontend_rules;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.NativeEffectRegistry;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesData.*;
import static org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesRequests.*;

/** Actual primitive preparers, independent later reads and their identical durable replay. */
public final class FrontendRulesEffects implements NativeEffectRegistry.Observer {
    public static final String SCHEMA = "xar.java.frontend-rules-independent-effect/v1";
    private static final String BASIS = "xar.java.frontend-rules-original-basis/v1";
    private static final List<Primitive> WRITES = List.of(Primitive.SELECT_RULE, Primitive.APPLY_HIDE_RULES,
            Primitive.HIDE_RULES, Primitive.OPEN_RULES, Primitive.NEW_GAME, Primitive.PICK_ANY,
            Primitive.RULER_DESIGNER, Primitive.SELECT_1066_BOOKMARK, Primitive.SELECT_1066, Primitive.SELECT_RANDOM);
    private final FrontendRulesDefinitions definitions;
    private final PlanningReadPort reads;
    private final ActionPorts.OutcomeArchive archive;
    public FrontendRulesEffects(FrontendRulesDefinitions definitions, PlanningReadPort soleReads, ActionPorts.OutcomeArchive sameArchive) {
        this.definitions = Objects.requireNonNull(definitions); this.reads = Objects.requireNonNull(soleReads); this.archive = Objects.requireNonNull(sameArchive);
    }
    public static Primitive primitive(OperationKey operation) {
        return WRITES.stream().filter(value -> value.operation().equals(operation)).findFirst()
                .orElseThrow(() -> new IllegalArgumentException("no original frontend primitive verifier: " + operation.value()));
    }
    public List<NativeEffectRegistry.Binding> bindings(ExactRef actualImplementation) {
        return WRITES.stream().map(value -> new NativeEffectRegistry.Binding(value.operation(), actualImplementation, this::prepare, this)).toList();
    }
    public List<NativeRecordedEvidenceVerifier.Binding> archivedVerifiers(ExactRef actualImplementation) {
        return WRITES.stream().map(value -> new NativeRecordedEvidenceVerifier.Binding(value.operation(), actualImplementation,
                (head, receipt, sameArchive) -> replay(receipt, sameArchive))).toList();
    }
    public FrontendExpectedPostcondition expected(FrontendIdentity identity, org.xar.ck3.control.g2.common.G2Source source,
            Primitive operation, OpportunityJson.Obj arguments) {
        return new FrontendExpectedPostcondition(identity, source, SCHEMA, expectedValues(operation, arguments));
    }
    private static List<ExpectedValue> expectedValues(Primitive operation, OpportunityJson.Obj arguments) {
        if (operation == Primitive.SELECT_RULE) {
            var request = FrontendRulesArguments.selection(arguments).request();
            return List.of(new ExpectedText(new FieldKey("rule_key"), request.ruleKey().value()),
                    new ExpectedText(new FieldKey("selected_setting_key"), request.desiredSettingKey().value()),
                    new ExpectedBoolean(new FieldKey("applied_settings_proven"), false));
        }
        if (operation == Primitive.APPLY_HIDE_RULES || operation == Primitive.HIDE_RULES)
            return List.of(new ExpectedBoolean(new FieldKey("window_closed_proven"), true), new ExpectedBoolean(new FieldKey("applied_settings_proven"), false));
        if (operation == Primitive.OPEN_RULES) return List.of(new ExpectedBoolean(new FieldKey("selections_ready"), true));
        if (operation == Primitive.SELECT_1066_BOOKMARK) return List.of(
                new ExpectedText(new FieldKey("selected_bookmark_key"), "bm_1066_rags_to_riches"),
                new ExpectedText(new FieldKey("selected_bookmark_group_key"), "bm_group_1066"),
                new ExpectedBoolean(new FieldKey("selected_1066_date_proven"), true));
        if (operation == Primitive.SELECT_1066) return List.of(new ExpectedText(new FieldKey("selected_character_key"), FrontendRulesArguments.model(arguments).characterKey()));
        if (operation == Primitive.SELECT_RANDOM) return List.of(new ExpectedBoolean(new FieldKey("default_designer_ready"), true));
        Route after = operation == Primitive.NEW_GAME ? Route.BOOKMARKS : operation == Primitive.PICK_ANY ? Route.LOBBY : Route.RULER_DESIGNER;
        return List.of(new ExpectedText(new FieldKey("route"), after.wire()));
    }
    public NativeRequest prepare(ActionCommand command) {
        var operation = primitive(command.operation()); requireMenu(command); requirePreconditions(command, operation, archive);
        return operation == Primitive.SELECT_RULE ? FrontendRulesArguments.selection(command.arguments()).request().nativeRequest() : operation.emptyRequest();
    }
    private void requirePreconditions(ActionCommand command, Primitive operation, ActionPorts.OutcomeArchive sameArchive) {
        if (operation == Primitive.SELECT_RULE) {
            var input = FrontendRulesArguments.selection(command.arguments());
            FrontendRulesPostconditions.selectionPrecondition(decode(command, input.selections(), definitions.selections(), sameArchive),
                    decode(command, input.window(), definitions.window(), sameArchive), input.request()); return;
        }
        if (operation == Primitive.APPLY_HIDE_RULES || operation == Primitive.HIDE_RULES) {
            var input = FrontendRulesArguments.closure(command.arguments());
            require(input.action() == (operation == Primitive.HIDE_RULES ? RulesAction.HIDE : RulesAction.APPLY_AND_HIDE), "closure operation changed its explicit action");
            FrontendRulesPostconditions.closurePrecondition(decode(command, input.selections(), definitions.selections(), sameArchive),
                    decode(command, input.window(), definitions.window(), sameArchive), input.action()); return;
        }
        if (operation == Primitive.SELECT_1066) {
            var input = FrontendRulesArguments.model(command.arguments()); require(!input.scenario(), "ordinary selection is not a scenario alias");
            decode(command, input.model(), definitions.bookmark(), sameArchive).selected(input.characterKey(), false, false); return;
        }
        var input = FrontendRulesArguments.route(command.arguments()); var before = decode(command, input.before(), definitions.route(), sameArchive);
        Route expected = operation == Primitive.NEW_GAME ? Route.MAIN_MENU : operation == Primitive.PICK_ANY || operation == Primitive.OPEN_RULES || operation == Primitive.SELECT_1066_BOOKMARK ? Route.BOOKMARKS : Route.LOBBY;
        require(before.route() == expected, "actual frontend route does not permit requested native primitive");
        if (operation == Primitive.RULER_DESIGNER || operation == Primitive.SELECT_RANDOM) {
            var tree = decode(command, input.tree().orElseThrow(() -> new IllegalArgumentException("actual native target tree required")), definitions.tree(), sameArchive);
            require(!tree.truncated() && (operation == Primitive.RULER_DESIGNER ? tree.defaultDesignerReady() : tree.randomPlayableReady()), "actual enabled native target was not observed");
        } else require(input.tree().isEmpty(), "unregistered target tree supplied for this route action");
    }
    private <T> T decode(ActionCommand command, ExactRef ref, ReadContract<T> contract, ActionPorts.OutcomeArchive sameArchive) {
        var read = sameArchive.loadRead(ref); require(sameArchive.readReferenceOf(read).equals(ref), "original read reference changed");
        NativeRecordedEvidenceVerifier.requireRead(read, sameArchive); requireReadBinding(command, read, contract.operation());
        require(read.after().binding().origin().requireFrontend().frame().querySequence().compareTo(command.origin().requireFrontend().frame().querySequence()) <= 0,
                "command precondition cites a future native query");
        return contract.decode(read);
    }
    private static void requireMenu(ActionCommand command) {
        require(command.origin() instanceof CommandOrigin.Frontend && command.origin().requireFrontend().frame() instanceof FrontendFrame.Menu,
                "frontend rules require the original Menu/zero revision profile");
    }
    private static void requireReadBinding(ActionCommand command, PlanningReadReceipt read, OperationKey operation) {
        require(read.request().operation().equals(operation) && read.request().source().equals(command.source()) && read.request().sessionId().equals(command.sessionId())
                && read.request().origin() instanceof CommandOrigin.Frontend && command.origin().requireFrontend().sameSession(read.request().origin().requireFrontend())
                && read.after().binding().origin() instanceof CommandOrigin.Frontend && command.origin().requireFrontend().sameSession(read.after().binding().origin().requireFrontend())
                && read.after().binding().origin().requireFrontend().frame() instanceof FrontendFrame.Menu && read.original().nativeOk(), "frontend independent read crossed source/session/Menu/profile");
    }
    private ReadContract<?> afterContract(Primitive operation) {
        if (operation == Primitive.SELECT_RULE || operation == Primitive.OPEN_RULES) return definitions.selections();
        if (operation == Primitive.APPLY_HIDE_RULES || operation == Primitive.HIDE_RULES) return definitions.window();
        if (operation == Primitive.SELECT_1066_BOOKMARK || operation == Primitive.SELECT_1066) return definitions.bookmark();
        if (operation == Primitive.SELECT_RANDOM) return definitions.tree();
        return definitions.route();
    }
    @Override public NativeEffectRegistry.Projected observe(ActionCommand command, ActionState.Attempt attempt, NativeActionPort.DispatchOutcome dispatch) {
        var operation = primitive(command.operation()); requireMenu(command);
        if (!(dispatch instanceof NativeActionPort.AckReceived ack) || !ack.nativeOk())
            return NativeEffectRegistry.Projected.pending("frontend dispatch unresolved; submit is never replayed", List.of(attempt.guard().nativeEvidence()));
        var contract = afterContract(operation);
        var request = new PlanningReadRequest(attempt.guard().origin(), command.source(), command.sessionId(), contract.operation(), FrontendRulesArguments.empty(), ActionObservationWindow.deadline(command));
        var result = reads.read(contract, request);
        if (!(result instanceof PlanningReadResult.Known<?> known)) return NativeEffectRegistry.Projected.pending("independent frontend read unavailable; original submit remains unresolved", List.of(attempt.guard().nativeEvidence()));
        var read = known.receipt(); var projected = project(command, attempt, ack, read, archive, List.of());
        RawJson compatible = projected.compatibleResult().orElseThrow(); ExactRef material = archive.preserveMaterial(compatible);
        var row = StrictJson.object(); row.put("schema", BASIS); row.put("command_body_sha256", ActionCodec.bodySha256(command)); row.put("request_id", attempt.requestId());
        row.set("after_read", archive.preserveRead(read).toJson()); row.set("compatible_material", material.toJson());
        RawJson basis = FrontendRulesRequests.raw(row); ExactRef basisRef = archive.preserveMaterial(basis);
        require(basis.equals(archive.loadMaterial(basisRef)) && compatible.equals(archive.loadMaterial(material)), "actual frontend proof archive changed");
        return project(command, attempt, ack, read, archive, List.of(basisRef));
    }
    private NativeEffectRegistry.Projected project(ActionCommand command, ActionState.Attempt attempt, NativeActionPort.AckReceived dispatch,
            PlanningReadReceipt read, ActionPorts.OutcomeArchive sameArchive, List<ExactRef> supporting) {
        var operation = primitive(command.operation()); requireMenu(command); requirePreconditions(command, operation, sameArchive);
        requireReadBinding(command, read, afterContract(operation).operation()); NativeRecordedEvidenceVerifier.requireRead(read, sameArchive);
        require(!read.requestId().equals(attempt.requestId()) && !read.after().binding().observedAt().isBefore(attempt.submittedAt())
                && read.after().binding().origin().requireFrontend().frame().querySequence().compareTo(attempt.guard().origin().requireFrontend().frame().querySequence()) > 0,
                "frontend effect requires a distinct later independent native read");
        var source = definitions.source(read); var sequence = attempt.guard().origin().requireFrontend().frame().querySequence();
        RawJson token = dispatch.originalResultToken().orElseThrow(() -> new IllegalArgumentException("original frontend ACK token missing"));
        if (operation == Primitive.SELECT_RULE) {
            var input = FrontendRulesArguments.selection(command.arguments());
            FrontendRulesPostconditions.selected(decode(command, input.selections(), definitions.selections(), sameArchive),
                    decode(command, input.window(), definitions.window(), sameArchive), input.request(), FrontendRulesCodec.rulesAck(token, source, RulesAction.SELECT), sequence, definitions.selections().decode(read));
        } else if (operation == Primitive.APPLY_HIDE_RULES || operation == Primitive.HIDE_RULES) {
            var input = FrontendRulesArguments.closure(command.arguments());
            FrontendRulesPostconditions.closed(decode(command, input.selections(), definitions.selections(), sameArchive),
                    FrontendRulesCodec.rulesAck(token, source, input.action()), sequence, definitions.window().decode(read));
        } else if (operation == Primitive.OPEN_RULES) {
            FrontendRulesCodec.nativeAck(token, operation.operation().value()); var observed = definitions.selections().decode(read);
            require(observed.ready() && !observed.appliedSettingsProven(), "native rules selections were not independently available after opening");
        } else if (operation == Primitive.SELECT_1066_BOOKMARK) {
            FrontendRulesCodec.nativeAck(token, operation.operation().value());
            definitions.bookmark().decode(read).requireSupported1066Bookmark();
        } else if (operation == Primitive.SELECT_1066) {
            FrontendRulesCodec.nativeAck(token, operation.operation().value()); var input = FrontendRulesArguments.model(command.arguments());
            definitions.bookmark().decode(read).selected(input.characterKey(), false, true);
        } else if (operation == Primitive.SELECT_RANDOM) {
            FrontendRulesCodec.nativeAck(token, operation.operation().value()); var tree = definitions.tree().decode(read);
            require(!tree.truncated() && tree.defaultDesignerReady(), "native random selection did not independently expose an enabled designer target");
        } else {
            var input = FrontendRulesArguments.route(command.arguments());
            Route before = operation == Primitive.NEW_GAME ? Route.MAIN_MENU : operation == Primitive.PICK_ANY ? Route.BOOKMARKS : Route.LOBBY;
            Route after = operation == Primitive.NEW_GAME ? Route.BOOKMARKS : operation == Primitive.PICK_ANY ? Route.LOBBY : Route.RULER_DESIGNER;
            FrontendRulesPostconditions.route(decode(command, input.before(), definitions.route(), sameArchive),
                    FrontendRulesCodec.nativeAck(token, operation.operation().value()), sequence, definitions.route().decode(read), before, after, operation.operation().value());
        }
        var actual = expectedValues(operation, command.arguments()); var identity = read.after().binding().origin().requireFrontend();
        var observation = new FrontendEffectObservation(identity, command.source(), command.sessionId(), SCHEMA, actual, read.requestId(), read.after().binding().observedAt(), identity.nativeEvidence(), supporting);
        if (!supporting.isEmpty()) ActionEffects.validate(command, attempt, new ActionState.FrontendApplied(observation));
        ObjectNode output = StrictJson.object(); output.put("schema", SCHEMA); output.put("status", "observed"); output.put("postcondition_verified", true);
        output.put("operation", operation.operation().value()); output.put("action_request_id", attempt.requestId()); output.put("independent_read_request_id", read.requestId());
        output.put("applied_settings_proven", false); output.put("uses_ocr", false); output.put("uses_keyboard", false); output.put("uses_mouse", false);
        return new NativeEffectRegistry.Projected(new ActionPorts.FrontendObserved(observation), Optional.of(FrontendRulesRequests.raw(output)));
    }
    private void replay(ActionReceipt receipt, ActionPorts.OutcomeArchive sameArchive) {
        require(receipt.state() instanceof ActionState.Settled && ((ActionState.Settled) receipt.state()).settlement() instanceof ActionState.FrontendApplied,
                "frontend domain replay requires an original primitive frontend settlement");
        var settled = (ActionState.Settled) receipt.state(); var observation = ((ActionState.FrontendApplied) settled.settlement()).observation();
        require(observation.supportingEvidence().size() == 1, "frontend settlement lacks its original independent-read basis");
        ExactRef ref = observation.supportingEvidence().getFirst(); RawJson raw = sameArchive.loadMaterial(ref);
        var row = StrictJson.object(FrontendRulesCodec.object(raw), Set.of("schema", "command_body_sha256", "request_id", "after_read", "compatible_material"));
        require(BASIS.equals(StrictJson.text(row.get("schema"))) && receipt.bodySha256().equals(StrictJson.text(row.get("command_body_sha256")))
                && settled.attempt().requestId().equals(StrictJson.text(row.get("request_id"))), "frontend proof basis crossed command or request");
        require(settled.dispatch() instanceof NativeActionPort.AckReceived, "frontend domain proof has no retained original ACK");
        var read = sameArchive.loadRead(ExactRef.fromJson(row.get("after_read")));
        var replayed = project(receipt.command(), settled.attempt(), (NativeActionPort.AckReceived) settled.dispatch(), read, sameArchive, observation.supportingEvidence());
        require(replayed.result() instanceof ActionPorts.FrontendObserved && observation.equals(((ActionPorts.FrontendObserved) replayed.result()).observation()), "frontend original replay differs from proposed material effect");
        require(replayed.compatibleResult().equals(Optional.of(sameArchive.loadMaterial(ExactRef.fromJson(row.get("compatible_material"))))), "frontend original material projection changed");
    }
}
