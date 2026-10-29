package org.xar.ck3.control.application.effects;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyOrdinaryActionArguments;
import org.xar.ck3.control.application.effects.ArmyWarWindowReads.*;

/** Five bounded material effects; every archived acceptance re-runs the actual full read decoder and this same projection. */
public final class NativeArmyWarWindowEffects implements NativeEffectRegistry.Observer {
    public static final String SCHEMA = "xar.java.army-war-window-postcondition/v1";
    public static final String DIRECT_SCHEMA = NativeDirectFixedWindowObservation.SCHEMA;
    private final NativeEffectSnapshots snapshots;
    private final NativeDirectFixedWindowObservation directWindows;
    private final PlanningReadPort reads;
    private final Optional<HolyHirePoststate.Port> holyPoststate;
    private final java.util.function.Function<Selection, Queries> queryRoutes;
    public NativeArmyWarWindowEffects(NativeEffectSnapshots snapshots, PlanningReadPort reads, Queries queries) {
        this(snapshots, reads, selected -> Objects.requireNonNull(queries));
    }
    public NativeArmyWarWindowEffects(NativeEffectSnapshots snapshots, PlanningReadPort reads,
            java.util.function.Function<Selection, Queries> actualRoutes) {
        this(snapshots, reads, actualRoutes, Optional.empty());
    }
    public NativeArmyWarWindowEffects(NativeEffectSnapshots snapshots, PlanningReadPort reads,
            java.util.function.Function<Selection, Queries> actualRoutes, HolyHirePoststate.Port actualHolyPoststate) {
        this(snapshots, reads, actualRoutes, Optional.of(Objects.requireNonNull(actualHolyPoststate)));
    }
    private NativeArmyWarWindowEffects(NativeEffectSnapshots snapshots, PlanningReadPort reads,
            java.util.function.Function<Selection, Queries> actualRoutes, Optional<HolyHirePoststate.Port> actualHolyPoststate) {
        this.snapshots = Objects.requireNonNull(snapshots); this.reads = Objects.requireNonNull(reads);
        holyPoststate = Objects.requireNonNull(actualHolyPoststate);
        queryRoutes = Objects.requireNonNull(actualRoutes);
        directWindows = new NativeDirectFixedWindowObservation(snapshots, this.reads, queryRoutes);
    }
    /** The identical installed observer owns live direct-window sampling, retained public-query custody and cold replay. */
    public NativeDirectFixedWindowObservation directWindows() { return directWindows; }
    private Queries queries(Selection selection) {
        Queries queries = Objects.requireNonNull(queryRoutes.apply(selection), "actual selected query routes required");
        if (queries.has(View.FAMILY)) requireOperation(queries.family(), "read-family-obligations-private-12002");
        if (queries.has(View.HOLY_ORDER)) requireOperation(queries.holyOrder(), "query-player-holy-order-context-v1");
        if (queries.has(View.OVERVIEW)) requireOperation(queries.overview(), "query-war-declared-overview-v1");
        if (queries.has(View.RESULTS)) requireOperation(queries.results(), "query-war-results-window-v1");
        queries.require(selection);
        return queries;
    }
    private static void requireOperation(Query<?> query, String operation) {
        StrictJson.require(query.operation().value().equals(operation), "wrong actual independent war/window query producer");
    }
    public record Preflight(Selection selection, List<PlanningReadReceipt> originalReceipts, RawJson selectedNativeTerms) {
        public Preflight { Objects.requireNonNull(selection); originalReceipts = List.copyOf(originalReceipts); Objects.requireNonNull(selectedNativeTerms); }
    }
    /** Pure actual-source admission for the sole external NativeRequest preparer; never submits or opens a writer. */
    public Preflight preflight(Complete actualBefore, ArmyOrdinaryActionArguments arguments, OperationKey operation) {
        StrictJson.require(!direct(arguments), "direct fixed-window actions have no ordinary visible-window quote");
        Selection selection = ArmyWarWindowReads.selection(arguments, operation); Queries queries = queries(selection); List<View> views = beforeViews(selection);
        List<PlanningReadReceipt> original = snapshots.reads(arguments.preflightReads());
        StrictJson.require(original.size() == views.size(), "complete actual preflight quote receipts required");
        List<ObjectNode> normalized = new ArrayList<>();
        for (int index = 0; index < views.size(); index++) {
            requireFrame(actualBefore, original.get(index));
            normalized.add(object(queries.get(views.get(index)).decode(Request.fromReceipt(actualBefore, selection, original.get(index), original), original.get(index)).normalized()));
        }
        BigInteger actor = actualBefore.identity().frame().identity().player(); ObjectNode selected;
        if (selection instanceof CallAlly ally) StrictJson.require(!actor.equals(unsignedId(ally.recipientId())), "call-ally recipient must differ from the current actor");
        switch (selection) {
            case Declaration declaration -> {
                var matches = rows(normalized.getFirst().get("declarable_wars"), 4096).stream()
                        .filter(row -> text(row, "declaration_id").equals(declaration.declarationId())).toList();
                StrictJson.require(matches.size() == 1 && !integerList(matches.getFirst().get("target_title_ids"), 4096, false).isEmpty(),
                        "one actual declaration choice with source target titles required");
                ObjectNode coverage = object(normalized.get(1).get("prewar_force_coalition_coverage_v2"));
                StrictJson.require(text(coverage, "declaration_id").equals(declaration.declarationId()), "actual finalized CB source belongs to another selected declaration");
                ObjectNode roles = object(coverage.get("final_cb_roles"));
                StrictJson.require(bool(roles, "available") && bool(roles, "final_can_send") && text(roles, "source").equals("finalized_selected_cb_context") &&
                        positive(roles.get("primary_attacker_character_id")).equals(actor), "finalized selected CB roles must bind actual primary player attacker");
                positive(roles.get("primary_defender_character_id"));
                selected = StrictJson.object(); selected.set("declaration", matches.getFirst()); selected.set("final_cb_roles", roles);
            }
            case CallAlly ally -> {
                JsonNode row = allyRow(normalized.getFirst(), ally, actor).orElseThrow(() -> new IllegalArgumentException("exact active family selected war unavailable"));
                StrictJson.require(text(row, "recipient_side").equals("absent") && bool(row, "native_target_can_be_picked") &&
                        bool(row, "native_target_row_selectable") && bool(row, "native_complete_can_send"), "actual native selected-pair send legality required");
                StrictJson.require(integerList(row.get("send_cost_raw"), 10, true).size() == 10, "complete actual native send quote required");
                selected = object(row);
            }
            case HolyHire holy -> {
                ObjectNode context = normalized.getFirst();
                StrictJson.require(bool(context, "available") && integer(context.get("played_character_id")).equals(actor), "current actual holy-order source required");
                JsonNode order = holyRow(context, holy).orElseThrow(() -> new IllegalArgumentException("selected holy-order reference not observed"));
                StrictJson.require(bool(order, "is_military") && !actor.equals(nullableInteger(order.get("employer_id"))), "new military holy-order employer transition required");
                ObjectNode terms = object(order.get("military_terms"));
                StrictJson.require(bool(terms, "available") && bool(terms, "can_hire") && bool(terms, "can_afford") &&
                        integerList(terms.get("resource_costs_raw"), 10, true).size() == 10, "actual final holy-order hire/affordability and resource quote required");
                selected = object(order);
            }
            case Window window -> {
                selected = normalized.getFirst(); String name = window.window() == WindowKind.OVERVIEW ? "war_declared_overview" : "war_results";
                StrictJson.require(text(selected, "operation").equals("query") && text(selected, "window_name").equals(name) &&
                        bool(selected, "available") && bool(selected, "root_observed") && bool(selected, "window_present") &&
                        bool(selected, "effective_visible") && bool(selected, "application_owner_thread_verified") &&
                        !bool(selected, "dispatch_attempted"), "actual qualified visible fixed window preflight required");
            }
            default -> throw new IllegalArgumentException("unsupported war/window preflight selection");
        }
        return new Preflight(selection, original, new RawJson(StrictJson.canonical(selected)));
    }
    /** The sole Army preparer calls this gate after constructing its native request. It creates no request or permit. */
    public void verifyPrepared(Complete actualBefore, ArmyOrdinaryActionArguments arguments, NativeRequest prepared) {
        if (direct(arguments)) {
            Objects.requireNonNull(actualBefore);
            StrictJson.require(ArmyWarWindowReads.selection(arguments, new OperationKey(prepared.step())) instanceof Window,
                    "direct fixed-window preparation cannot select another Army operation");
            StrictJson.require(arguments.preflightReads().isEmpty() && object(prepared.additionalFields()).isEmpty(),
                    "direct fixed-window preparation cannot add a selector or ordinary preflight quote");
            return;
        }
        var quote = preflight(actualBefore, arguments, new OperationKey(prepared.step()));
        ObjectNode fields = object(prepared.additionalFields());
        switch (quote.selection()) {
            case CallAlly ally -> {
                StrictJson.object(fields, java.util.Set.of("recipient_character_id", "war_id", "expected_send_cost_raw"));
                StrictJson.require(ArmyWarWindowReads.signed(fields.get("war_id")) == ally.warId() &&
                        ArmyWarWindowReads.signed(fields.get("recipient_character_id")) == ally.recipientId(), "prepared call-ally selected IDs drift");
                ObjectNode actualTerms = object(quote.selectedNativeTerms());
                StrictJson.require(integerList(fields.get("expected_send_cost_raw"), 10, true).equals(integerList(actualTerms.get("send_cost_raw"), 10, true)),
                        "prepared call-ally quote differs from actual archived native terms");
            }
            case HolyHire holy -> {
                StrictJson.object(fields, java.util.Set.of("holy_order_id"));
                StrictJson.require(integer(fields.get("holy_order_id")).equals(BigInteger.valueOf(holy.holyOrderId())), "prepared holy-order selected ID drift");
            }
            case Declaration ignored -> StrictJson.require(fields.isEmpty(), "declaration native request takes its complete identity from exact operation");
            case Window ignored -> StrictJson.require(fields.isEmpty(), "fixed window native request has no arbitrary selector");
        }
    }
    private static void requireFrame(Complete frame, PlanningReadReceipt read) {
        StrictJson.require(read.request().before().equals(frame.identity()) && read.request().source().equals(frame.source()) &&
                read.request().sessionId().equals(frame.sessionId()) && read.original().nativeOk(), "actual source quote crossed its selected full frame");
        for (var guard : List.of(read.before(), read.after()))
            StrictJson.require(guard.binding().observed().equals(frame.identity()) && guard.binding().source().equals(frame.source()) &&
                    guard.binding().sessionId().equals(frame.sessionId()) && guard.binding().connectionGeneration().equals(frame.connectionGeneration()) &&
                    guard.binding().nativeEvidence().equals(frame.originalEvidence()) && guard.originalBindingSha256().equals(frame.fullBindingSha256()) &&
                    guard.paused() && guard.mapReady() && guard.playerAlive(), "actual source quote crossed native/Driver/actor/connection/paused binding");
    }
    public static ExpectedPostcondition expected(ObservationIdentity before, G2Source source, OperationKey operation, RawJson arguments) {
        Objects.requireNonNull(before); Objects.requireNonNull(source);
        var outer = ArmyOrdinaryActionArguments.decode(arguments);
        if (direct(outer)) return NativeDirectFixedWindowObservation.expected(before, source, operation, arguments);
        Selection selected = ArmyWarWindowReads.selection(outer, operation);
        if (selected instanceof CallAlly ally) StrictJson.require(!before.frame().identity().player().equals(unsignedId(ally.recipientId())), "call-ally recipient must differ from actual player");
        JsonNode publicArgs = StrictJson.parse(outer.publicArguments().bytes());
        if (publicArgs.has("expected_revision") && !publicArgs.get("expected_revision").isNull())
            StrictJson.require(ArmyWarWindowReads.revision(publicArgs.get("expected_revision")).equals(before.frame().revision()), "selected public revision differs from original before frame");
        StrictJson.require(outer.preflightReads().size() == beforeViews(selected).size(), "every required actual preflight receipt must be durable before submission");
        return new ExpectedPostcondition(1, before, source, SCHEMA, values(selected, before.frame().identity().player()));
    }
    private static List<ExpectedValue> values(Selection selection, BigInteger actor) {
        List<ExpectedValue> out = new ArrayList<>();
        out.add(new ExpectedText(new FieldKey("operation"), selection.operation().value()));
        out.add(new ExpectedInteger(new FieldKey("actor_character_id"), actor));
        switch (selection) {
            case Declaration declaration -> {
                out.add(new ExpectedText(new FieldKey("declaration_id"), declaration.declarationId()));
                out.add(new ExpectedText(new FieldKey("effect"), "unique_new_war_started"));
                out.add(new ExpectedBoolean(new FieldKey("casus_belli_identity_observed"), false));
            }
            case CallAlly ally -> {
                out.add(new ExpectedInteger(new FieldKey("war_id"), unsignedId(ally.warId())));
                out.add(new ExpectedInteger(new FieldKey("recipient_character_id"), unsignedId(ally.recipientId())));
                out.add(new ExpectedText(new FieldKey("effect"), "recipient_joined_same_war_side"));
            }
            case HolyHire holy -> {
                out.add(new ExpectedInteger(new FieldKey("holy_order_id"), BigInteger.valueOf(holy.holyOrderId())));
                out.add(new ExpectedText(new FieldKey("effect"), "employer_relationship_observed"));
                out.add(new ExpectedBoolean(new FieldKey("payment_observed"), false));
                out.add(new ExpectedBoolean(new FieldKey("public_cunit_availability_observed"), false));
            }
            case Window window -> {
                out.add(new ExpectedText(new FieldKey("window"), window.window() == WindowKind.OVERVIEW ? "war_declared_overview" : "war_results"));
                out.add(new ExpectedText(new FieldKey("effect"), "fixed_window_independently_hidden_or_absent"));
                out.add(new ExpectedBoolean(new FieldKey("war_outcome_observed"), false));
            }
        }
        return List.copyOf(out);
    }
    private static List<View> beforeViews(Selection selection) {
        return switch (selection) {
            case Declaration ignored -> List.of(View.DECLARATIONS, View.FINAL_CB_ROLES);
            case CallAlly ignored -> List.of(View.FAMILY);
            case HolyHire ignored -> List.of(View.HOLY_ORDER);
            case Window window -> List.of(window.window() == WindowKind.OVERVIEW ? View.OVERVIEW : View.RESULTS);
        };
    }
    private static Optional<View> afterView(Selection selection) {
        return selection instanceof Declaration ? Optional.empty() : Optional.of(beforeViews(selection).getFirst());
    }
    @Override public NativeEffectRegistry.Projected observe(ActionCommand command, ActionState.Attempt attempt, NativeActionPort.DispatchOutcome dispatch) {
        var outer = ArmyOrdinaryActionArguments.decode(command.arguments());
        if (direct(outer)) return directWindows.observe(command, attempt, dispatch);
        Selection selection = ArmyWarWindowReads.selection(outer, command.operation()); Queries queries = queries(selection);
        var pair = snapshots.read(command, attempt);
        if (ActionReconciliationScope.activeFor(command) && !(selection instanceof Window) && !(selection instanceof HolyHire) && afterView(selection).isPresent())
            return NativeEffectRegistry.Projected.pending("this action has no independently installed reconciliation query family; original UNKNOWN is retained without resubmission",
                    List.of(pair.after().originalEvidence()));
        List<PlanningReadReceipt> originals = new ArrayList<>(snapshots.reads(outer.preflightReads()));
        StrictJson.require(originals.size() == beforeViews(selection).size(), "actual preflight receipt closure incomplete");
        if (afterView(selection).isPresent()) {
            Query<?> query = queries.get(afterView(selection).orElseThrow());
            Request actualRead = new Request(pair.after(), selection, ActionObservationWindow.deadline(command), reconciliation(command, attempt));
            PlanningReadResult<?> result = query.read(reads, actualRead);
            if (!(result instanceof PlanningReadResult.Known<?> known))
                return NativeEffectRegistry.Projected.pending("actual independent war/window read unavailable; original action remains unresolved and must not be resent", List.of(pair.after().originalEvidence()));
            originals.add(known.receipt());
        }
        var projected = project(command, attempt, dispatch, pair, originals, Interpretation.LIVE);
        if (!(projected.result() instanceof ActionPorts.EffectObserved)) return projected;
        List<ExactRef> supplemental = List.of();
        if (selection instanceof HolyHire holy && holyPoststate.isPresent()) {
            var collected = holyPoststate.orElseThrow().collect(command, attempt, pair, holy,
                    holyContext(pair.before(), holy, originals.getFirst(), originals.subList(0, 1), Interpretation.LIVE),
                    holyContext(pair.after(), holy, originals.getLast(), List.of(), Interpretation.LIVE));
            projected = withHolySupplement(projected, collected, command, attempt, pair, holy);
            supplemental = List.of(collected.originalMaterial());
        }
        ExactRef basis = snapshots.evidence(command, attempt, pair, originals, projected.compatibleResult().orElseThrow(), supplemental);
        List<ExactRef> closure = new ArrayList<>(); closure.add(basis); closure.addAll(supplemental);
        return NativeEffectSnapshots.withEvidence(projected, List.copyOf(closure));
    }
    private JsonNode holyContext(Complete frame, HolyHire selected, PlanningReadReceipt read,
            List<PlanningReadReceipt> before, Interpretation mode) {
        return object(interpret(queries(selected).holyOrder(), frame, selected, read, before, mode).normalized());
    }
    private static NativeEffectRegistry.Projected withHolySupplement(NativeEffectRegistry.Projected original,
            HolyHirePoststate.Supplement supplement, ActionCommand command, ActionState.Attempt attempt,
            NativeEffectSnapshots.Pair pair, HolyHire selected) {
        StrictJson.require(original.result() instanceof ActionPorts.EffectObserved
                && supplement.report().scope().equals(HolyHirePoststate.Scope.of(command, attempt, pair, selected.holyOrderId())),
                "holy supplementary material crossed the original settled employer/actor/frame");
        ObjectNode compatible = object(original.compatibleResult().orElseThrow()).deepCopy();
        compatible.set("holy_order_reinforcement_postcondition", HolyHirePoststate.json(supplement.report()));
        return new NativeEffectRegistry.Projected(original.result(), Optional.of(new RawJson(StrictJson.canonical(compatible))));
    }
    private enum Interpretation { LIVE, ARCHIVED }
    private static Material interpret(Query<?> query, Complete frame, Selection selection, PlanningReadReceipt read,
            List<PlanningReadReceipt> preflightOriginals, Interpretation mode) {
        Request actual = Request.fromReceipt(frame, selection, read, preflightOriginals);
        return mode == Interpretation.ARCHIVED ? query.replay(actual, read) : query.decode(actual, read);
    }
    private NativeEffectRegistry.Projected project(ActionCommand command, ActionState.Attempt attempt, NativeActionPort.DispatchOutcome dispatch,
            NativeEffectSnapshots.Pair pair, List<PlanningReadReceipt> originals, Interpretation interpretation) {
        var outer = ArmyOrdinaryActionArguments.decode(command.arguments()); Selection selection = ArmyWarWindowReads.selection(outer, command.operation()); Queries queries = queries(selection);
        List<View> needed = beforeViews(selection); Optional<View> afterView = afterView(selection);
        StrictJson.require(originals.size() == needed.size() + (afterView.isPresent() ? 1 : 0), "wrong independent receipt count");
        List<ObjectNode> before = new ArrayList<>();
        for (int index = 0; index < needed.size(); index++) {
            PlanningReadReceipt read = originals.get(index);
            requireAt(pair.before(), selection, read, command, attempt, true);
            before.add(object(interpret(queries.get(needed.get(index)), pair.before(), selection, read,
                    originals.subList(0, needed.size()), interpretation).normalized()));
        }
        Optional<ObjectNode> afterRead = Optional.empty();
        if (afterView.isPresent()) {
            PlanningReadReceipt read = originals.getLast(); Query<?> query = queries.get(afterView.orElseThrow());
            NativeEffectSnapshots.requireAfterRead(command, attempt, pair.after(), read, query.operation());
            requireAt(pair.after(), selection, read, command, attempt, false);
            afterRead = Optional.of(object(interpret(query, pair.after(), selection, read, List.of(), interpretation).normalized()));
        }
        if (!canCollect(selection, command.operation(), dispatch)) return pending(pair, "original zero-dispatch proof or declaration lacks its required original acceptance; never resend the original attempt");
        BigInteger actor = command.before().frame().identity().player();
        Optional<ObjectNode> material = switch (selection) {
            case Declaration declaration -> declaration(declaration, actor, pair, before.get(0), before.get(1));
            case CallAlly ally -> ally(ally, actor, before.getFirst(), afterRead.orElseThrow());
            case HolyHire holy -> holy(holy, actor, before.getFirst(), afterRead.orElseThrow());
            case Window window -> window(window, before.getFirst(), afterRead.orElseThrow());
        };
        if (material.isEmpty()) return pending(pair, "requested exact identity/material transition not independently observed; UNKNOWN stays pending without replay");
        ObjectNode compatible = material.orElseThrow(); compatible.put("action_request_id", attempt.requestId());
        compatible.put("postcondition_verified", true).put("automatic_retry", false).put("observer_schema", SCHEMA);
        compatible.put("native_response", response(command.operation(), dispatch)).put("action_attribution_observed", false);
        ObservationProvenance provenance = afterView.isPresent() ? new ObservationProvenance.Query(originals.getLast().requestId())
                : NativeEffectSnapshots.publication(pair.after());
        return NativeEffectSnapshots.observed(command, attempt, pair.after(), SCHEMA, values(selection, actor), provenance,
                new RawJson(StrictJson.canonical(compatible)), List.of());
    }
    private static NativeEffectRegistry.Projected pending(NativeEffectSnapshots.Pair pair, String reason) {
        return NativeEffectRegistry.Projected.pending(reason, List.of(pair.after().originalEvidence()));
    }
    /** Unknown submissions may be collected through actual independent material, never resent.
     * Declaration retains the original Python contract's explicit accepted-request requirement.
     */
    static boolean canCollect(Selection selection, OperationKey operation, NativeActionPort.DispatchOutcome dispatch) {
        StrictJson.require(selection.operation().equals(operation), "effect collection operation drift");
        if (dispatch instanceof NativeActionPort.RejectedBeforeDispatch) return false;
        boolean actualAccepted = accepted(operation, dispatch); // Still validate every available original ACK's exact step/type.
        return !(selection instanceof Declaration) || actualAccepted;
    }
    private static String response(OperationKey operation, NativeActionPort.DispatchOutcome dispatch) {
        if (dispatch instanceof NativeActionPort.AckReceived ack)
            return !ack.nativeOk() ? "native_error" : ack.originalResultToken().isEmpty() ? "unknown" : accepted(operation, dispatch) ? "accepted" : "not_accepted";
        return dispatch instanceof NativeActionPort.RejectedBeforeDispatch ? "not_submitted" : "unknown";
    }
    private static boolean accepted(OperationKey operation, NativeActionPort.DispatchOutcome dispatch) {
        if (!(dispatch instanceof NativeActionPort.AckReceived ack) || !ack.nativeOk() || ack.originalResultToken().isEmpty()) return false;
        ObjectNode result = object(ack.originalResultToken().orElseThrow());
        StrictJson.require(text(result, "step").equals(operation.value()), "actual action ACK step drift");
        return bool(result, "accepted");
    }
    private static Optional<ReconciliationIdentity> reconciliation(ActionCommand command, ActionState.Attempt attempt) {
        if (!ActionReconciliationScope.activeFor(command)) return Optional.empty();
        try { return Optional.of(ActionReconciliationScope.requireIdentity(command, attempt)); }
        catch (java.io.IOException failure) { throw new java.io.UncheckedIOException(failure); }
    }
    private static void requireAt(Complete frame, Selection selection, PlanningReadReceipt read, ActionCommand command,
            ActionState.Attempt attempt, boolean preflight) {
        Request actual = Request.fromReceipt(frame, selection, read);
        StrictJson.require(!read.requestId().equals(attempt.requestId()) && read.original().nativeOk(),
                "independent receipt crossed its original action request");
        if (actual.reconciliation().isPresent()) {
            StrictJson.require(!preflight, "an ordinary action cannot use reconciliation as its preflight admission");
            NativeEffectSnapshots.requireAfterRead(command, attempt, frame, read, read.request().operation());
            return;
        }
        for (PlanningReadGuard guard : List.of(read.before(), read.after()))
            StrictJson.require(preflight ? !guard.binding().observedAt().isAfter(attempt.submittedAt())
                            : !guard.binding().observedAt().isBefore(attempt.submittedAt()),
                    "ordinary independent receipt crossed the original submission chronology");
    }
    static Optional<ObjectNode> declaration(Declaration selected, BigInteger actor, NativeEffectSnapshots.Pair pair, ObjectNode choices, ObjectNode coalition) {
        List<JsonNode> selectedRows = rows(choices.get("declarable_wars"), 4096).stream()
                .filter(row -> text(row, "declaration_id").equals(selected.declarationId())).toList();
        if (selectedRows.size() != 1) return Optional.empty();
        JsonNode selectedRow = selectedRows.getFirst(); List<BigInteger> titles = integerList(selectedRow.get("target_title_ids"), 4096, false);
        if (titles.isEmpty()) return Optional.empty();
        ObjectNode coverage = object(coalition.get("prewar_force_coalition_coverage_v2"));
        StrictJson.require(text(coverage, "declaration_id").equals(selected.declarationId()), "final CB declaration source drift");
        ObjectNode roles = object(coverage.get("final_cb_roles"));
        if (!bool(roles, "available") || !bool(roles, "final_can_send") || !text(roles, "source").equals("finalized_selected_cb_context")) return Optional.empty();
        BigInteger attacker = positive(roles.get("primary_attacker_character_id")), defender = positive(roles.get("primary_defender_character_id"));
        if (!actor.equals(attacker)) return Optional.empty();
        ObjectNode originalBefore = object(pair.before().semantic()), originalAfter = object(pair.after().semantic());
        if (!bool(originalAfter, "paused") || !bool(originalAfter, "map_ready")) return Optional.empty();
        List<JsonNode> previous = rows(originalBefore.get("active_wars"), 256), current = rows(originalAfter.get("active_wars"), 256);
        HashSet<BigInteger> beforeIds = new HashSet<>(), afterIds = new HashSet<>();
        for (JsonNode war : previous) StrictJson.require(beforeIds.add(nonnegativeId(war.get("war_id"))), "duplicate actual before war IDs");
        List<BigInteger> matches = new ArrayList<>();
        for (JsonNode war : current) {
            BigInteger id = nonnegativeId(war.get("war_id")); StrictJson.require(afterIds.add(id), "duplicate actual after war IDs");
            if (!beforeIds.contains(id) && text(war, "player_side").equals("attacker") && bool(war, "player_is_primary_war_leader") &&
                    positive(war.get("primary_opponent_character_id")).equals(defender) &&
                    integerList(war.get("targeted_title_ids"), 4096, false).equals(titles)) matches.add(id);
        }
        if (matches.size() != 1) return Optional.empty();
        ObjectNode n = StrictJson.object().put("status", "war_started").put("war_id", matches.getFirst()).put("declaration_id", selected.declarationId());
        n.put("casus_belli_identity_observed", false).put("postcondition_scope", "unique_new_primary_attacker_opponent_and_target_titles");
        n.put("primary_attacker_character_id", attacker).put("primary_defender_character_id", defender);
        var out = n.putArray("target_title_ids"); titles.forEach(out::add); return Optional.of(n);
    }
    static Optional<ObjectNode> ally(CallAlly selected, BigInteger actor, ObjectNode before, ObjectNode after) {
        Optional<JsonNode> prior = allyRow(before, selected, actor), current = allyRow(after, selected, actor);
        if (prior.isEmpty() || current.isEmpty()) return Optional.empty();
        JsonNode a = prior.orElseThrow(), b = current.orElseThrow();
        String caller = text(a, "caller_side");
        StrictJson.require(caller.equals("attacker") || caller.equals("defender"), "actual caller war side required");
        if (!text(a, "recipient_side").equals("absent") || !text(b, "caller_side").equals(caller) ||
                !text(b, "recipient_side").equals(caller) || !bool(a, "native_complete_can_send")) return Optional.empty();
        ObjectNode n = StrictJson.object().put("status", "ally_joined").put("war_id", Integer.toUnsignedLong(selected.warId()))
                .put("recipient_character_id", Integer.toUnsignedLong(selected.recipientId())).put("caller_side", caller).put("recipient_side", caller);
        n.put("postcondition_scope", "same_selected_active_war_actual_participant_side").put("payment_observed", false);
        return Optional.of(n);
    }
    private static BigInteger unsignedId(int rawBits) { return BigInteger.valueOf(Integer.toUnsignedLong(rawBits)); }
    private static Optional<JsonNode> allyRow(ObjectNode normalized, CallAlly selected, BigInteger actor) {
        ObjectNode alliance = object(normalized.get("alliance_obligations"));
        if (!text(alliance, "status").equals("available")) return Optional.empty();
        StrictJson.require(integer(alliance.get("first_character_id")).equals(actor) &&
                integer(alliance.get("second_character_id")).equals(unsignedId(selected.recipientId())), "actual family selected pair drift");
        List<JsonNode> matches = rows(alliance.get("first_wars"), 4096).stream().filter(row ->
                integer(row.get("war_id")).equals(unsignedId(selected.warId())) &&
                integer(row.get("caller_character_id")).equals(actor) && integer(row.get("recipient_character_id")).equals(unsignedId(selected.recipientId()))).toList();
        StrictJson.require(matches.size() <= 1, "ambiguous actual selected family war");
        return matches.isEmpty() ? Optional.empty() : Optional.of(matches.getFirst());
    }
    static Optional<ObjectNode> holy(HolyHire selected, BigInteger actor, ObjectNode before, ObjectNode after) {
        if (!bool(before, "available") || !bool(after, "available")) return Optional.empty();
        StrictJson.require(integer(before.get("played_character_id")).equals(actor) && integer(after.get("played_character_id")).equals(actor), "holy-order actor drift");
        Optional<JsonNode> prior = holyRow(before, selected), current = holyRow(after, selected);
        if (prior.isEmpty() || current.isEmpty()) return Optional.empty();
        JsonNode a = prior.orElseThrow(), b = current.orElseThrow();
        BigInteger previous = nullableInteger(a.get("employer_id")), employer = nullableInteger(b.get("employer_id"));
        if (actor.equals(previous) || !actor.equals(employer) || !bool(a, "is_military") || !bool(b, "is_military")) return Optional.empty();
        ObjectNode terms = object(a.get("military_terms"));
        if (!bool(terms, "available") || !bool(terms, "can_hire") || !bool(terms, "can_afford")) return Optional.empty();
        List<BigInteger> quote = integerList(terms.get("resource_costs_raw"), 10, true); StrictJson.require(quote.size() == 10, "actual holy-order ten-resource quote required");
        ObjectNode n = StrictJson.object().put("status", "holy_order_employer_observed").put("holy_order_id", selected.holyOrderId())
                .put("employer_character_id", actor).put("payment_observed", false).put("public_cunit_availability_observed", false);
        n.put("postcondition_scope", "holy_order_employer_relationship_only");
        var costs = n.putArray("quoted_resource_costs_raw"); quote.forEach(costs::add);
        n.put("before_capture_epoch", unsigned(before.get("capture_epoch")).toString()).put("after_capture_epoch", unsigned(after.get("capture_epoch")).toString());
        return Optional.of(n);
    }
    private static Optional<JsonNode> holyRow(ObjectNode context, HolyHire selected) {
        List<JsonNode> matches = rows(context.get("rows"), 8192).stream().filter(row ->
                integer(row.get("holy_order_id")).equals(BigInteger.valueOf(selected.holyOrderId()))).toList();
        StrictJson.require(matches.size() <= 1, "ambiguous actual holy-order reference");
        return matches.isEmpty() ? Optional.empty() : Optional.of(matches.getFirst());
    }
    static Optional<ObjectNode> window(Window selected, ObjectNode before, ObjectNode after) {
        String name = selected.window() == WindowKind.OVERVIEW ? "war_declared_overview" : "war_results";
        for (ObjectNode row : List.of(before, after)) {
            StrictJson.require(text(row, "operation").equals("query") && text(row, "window_name").equals(name), "independent fixed-window query drift");
            if (!bool(row, "available")) return Optional.empty();
            for (String flag : List.of("root_observed", "post_observed", "scope_unchanged", "application_owner_thread_verified")) StrictJson.trueValue(row.get(flag));
            StrictJson.require(!bool(row, "dispatch_attempted") && !bool(row, "dispatch_invoked") && !bool(row, "native_handled") &&
                    !bool(row, "closure_verified"), "close ACK or dispatch result cannot replace independent window query");
            if (!bool(row, "window_present")) StrictJson.require(text(row, "root_observation_source").equals("guarded_top_level_and_complete_owner_tree"), "window absence lacks complete native owner-tree negative read");
            if (!bool(row, "post_window_present")) StrictJson.require(text(row, "post_observation_source").equals("guarded_top_level_and_complete_owner_tree"), "post window absence lacks complete owner-tree negative read");
            ObjectNode top = object(row.get("native_command_result"));
            ObjectNode owner = object(top.get(name.equals("war_results") ? "war_results_window_owner_receipt" : "war_declared_overview_owner_receipt"));
            BigInteger ticket = unsigned(owner.get("ticket_sequence"));
            StrictJson.require(ticket.signum() > 0 && ticket.equals(unsigned(owner.get("executor_started_sequence"))) &&
                    ticket.equals(unsigned(owner.get("completed_sequence"))) && ticket.equals(unsigned(row.get("ticket_sequence"))) &&
                    text(owner, "request_id").equals(text(row, "request_id")), "actual independent TOP executor ticket/leaf identity drift");
        }
        if (!bool(before, "window_present") || !bool(before, "effective_visible") || bool(after, "effective_visible") || bool(after, "post_effective_visible")) return Optional.empty();
        ObjectNode n = StrictJson.object().put("status", "window_hidden_or_absent").put("window_name", name);
        n.put("postcondition_scope", "fixed_window_ui_only").put("war_outcome_observed", false).put("terms_observed", false);
        n.put("window_present", bool(after, "window_present")).put("effective_visible", false);
        return Optional.of(n);
    }
    /** Same instance owns the live query contracts and archive replay; no static global registration or second decoder. */
    public NativeRecordedEvidenceVerifier.Binding archivedVerifier(OperationKey operation, ExactRef observerSource, NativeEffectEvidence.FrameLoader frames) {
        Objects.requireNonNull(operation); Objects.requireNonNull(observerSource); Objects.requireNonNull(frames);
        return new NativeRecordedEvidenceVerifier.Binding(operation, observerSource, (head, receipt, archive) -> {
            var outer = ArmyOrdinaryActionArguments.decode(receipt.command().arguments());
            if (direct(outer)) { directWindows.verifyArchived(receipt); return; }
            var original = NativeEffectEvidence.load(receipt, archive, frames); var settled = (ActionState.Settled) receipt.state();
            ArmyWarWindowReads.selection(outer, operation);
            StrictJson.require(outer.preflightReads().size() <= original.independentReads().size(), "archived preflight closure absent");
            for (int index = 0; index < outer.preflightReads().size(); index++)
                StrictJson.require(archive.readReferenceOf(original.independentReads().get(index)).equals(outer.preflightReads().get(index)), "archived original preflight receipt identity drift");
            var replayed = project(receipt.command(), settled.attempt(), settled.dispatch(), original.frames(), original.independentReads(), Interpretation.ARCHIVED);
            if (!original.supportingMaterials().isEmpty()) {
                StrictJson.require(ArmyWarWindowReads.selection(outer, operation) instanceof HolyHire
                        && original.supportingMaterials().size() == 1 && holyPoststate.isPresent(),
                        "supplementary holy archive requires its actual installed producer");
                var holy = (HolyHire) ArmyWarWindowReads.selection(outer, operation);
                var collected = holyPoststate.orElseThrow().replay(receipt.command(), settled.attempt(), original.frames(), holy,
                        holyContext(original.frames().before(), holy, original.independentReads().getFirst(), original.independentReads().subList(0, 1), Interpretation.ARCHIVED),
                        holyContext(original.frames().after(), holy, original.independentReads().getLast(), List.of(), Interpretation.ARCHIVED),
                        original.supportingMaterials().getFirst(), archive);
                replayed = withHolySupplement(replayed, collected, receipt.command(), settled.attempt(), original.frames(), holy);
            }
            replayed = NativeEffectSnapshots.withEvidence(replayed, ((ActionState.Applied) settled.settlement()).observation().supportingEvidence());
            NativeEffectEvidence.requireSame(settled.settlement(), replayed, original.compatibleResult());
        });
    }
    static boolean direct(ArmyOrdinaryActionArguments actual) {
        return Objects.requireNonNull(actual).executionProfile() == ArmyOrdinaryActionArguments.ExecutionProfile.DIRECT_FIXED_WINDOW;
    }
    private static ObjectNode object(RawJson raw) { return object(StrictJson.parse(raw.bytes(), StrictJson.EXPLICIT_MAX_BYTES)); }
    private static ObjectNode object(org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj raw) {
        return object(org.xar.ck3.control.planning.opportunity.OpportunityJson.toNode(raw));
    }
    private static ObjectNode object(JsonNode n) { StrictJson.require(n != null && n.isObject(), "actual normalized object required"); return (ObjectNode) n; }
    private static String text(JsonNode n, String key) { return StrictJson.text(n.get(key)); }
    private static boolean bool(JsonNode n, String key) { JsonNode value = n.get(key); StrictJson.require(value != null && value.isBoolean(), "actual boolean required: " + key); return value.booleanValue(); }
    private static BigInteger integer(JsonNode n) { return ArmyWarWindowReads.integer(n); }
    private static BigInteger nullableInteger(JsonNode n) { return n == null || n.isNull() ? null : integer(n); }
    private static BigInteger positive(JsonNode n) { BigInteger v = integer(n); StrictJson.require(v.signum() > 0 && v.compareTo(BigInteger.valueOf(Integer.MAX_VALUE)) <= 0, "positive private character identity required"); return v; }
    private static BigInteger nonnegativeId(JsonNode n) { BigInteger v = integer(n); StrictJson.require(v.signum() >= 0 && v.compareTo(BigInteger.valueOf(Integer.MAX_VALUE)) <= 0, "actual public active-war ID domain required"); return v; }
    private static BigInteger unsigned(JsonNode n) { BigInteger v = integer(n); StrictJson.require(v.signum() >= 0 && v.compareTo(StrictJson.UINT64_MAX) <= 0, "native uint64 integer required"); return v; }
    private static List<JsonNode> rows(JsonNode n, int maximum) {
        StrictJson.require(n != null && n.isArray() && n.size() <= maximum, "bounded actual source array required");
        List<JsonNode> rows = new ArrayList<>(); n.forEach(rows::add); return List.copyOf(rows);
    }
    private static List<BigInteger> integerList(JsonNode n, int maximum, boolean signed64) {
        List<BigInteger> out = new ArrayList<>();
        for (JsonNode row : rows(n, maximum)) {
            BigInteger value = integer(row);
            if (signed64) StrictJson.require(value.compareTo(BigInteger.ONE.shiftLeft(63).negate()) >= 0 && value.compareTo(BigInteger.ONE.shiftLeft(63).subtract(BigInteger.ONE)) <= 0, "native signed64 resource cost required");
            else StrictJson.require(value.signum() >= 0 && value.compareTo(new BigInteger("4294967295")) <= 0, "actual nonnegative full target title ID required");
            out.add(value);
        }
        return List.copyOf(out);
    }
}
