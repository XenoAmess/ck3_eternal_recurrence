package org.xar.ck3.control.application.routecontact;

import static org.xar.ck3.control.application.routecontact.RouteContactModel.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.advance.AdvanceObservationPort;
import org.xar.ck3.control.application.advance.AdvanceResult;
import org.xar.ck3.control.application.advance.ClockStatusRead;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.routecontact.RouteContactComposite.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.military.routewindow.RouteWindowPolicy;

/** One strict producer/reader for route evidence and the surviving Driver result. Raw native packets stay in the shared archive. */
public final class RouteContactEvidenceCodec {
    public static final String SCHEMA = "xar.java-route-contact-evidence/v5";
    private static final String LEGACY_SCHEMA_V4 = "xar.java-route-contact-evidence/v4";
    private static final String LEGACY_SCHEMA_V3 = "xar.java-route-contact-evidence/v3";
    private static final String LEGACY_SCHEMA_V2 = "xar.java-route-contact-evidence/v2";
    private RouteContactEvidenceCodec() { }
    public sealed interface Document permits Completed, Failed {
        ActionCommand parent(); AdvanceObservationPort.Frame starting(); AdvanceObservationPort.Frame ending();
        Proof proof(); List<ActionReceipt> children();
    }
    public record Completed(ActionCommand parent, Completion completion) implements Document {
        public Completed { Objects.requireNonNull(parent); Objects.requireNonNull(completion); bind(parent, completion.starting(), completion.proof()); }
        @Override public AdvanceObservationPort.Frame starting() { return completion.starting(); }
        @Override public AdvanceObservationPort.Frame ending() { return completion.ending(); }
        @Override public Proof proof() { return completion.proof(); }
        @Override public List<ActionReceipt> children() { return completion.children(); }
    }
    public record Failed(ActionCommand parent, ContactFailure failure) implements Document {
        public Failed { Objects.requireNonNull(parent); Objects.requireNonNull(failure); bind(parent, failure.starting(), failure.proof()); }
        @Override public AdvanceObservationPort.Frame starting() { return failure.starting(); }
        @Override public AdvanceObservationPort.Frame ending() { return failure.ending(); }
        @Override public Proof proof() { return failure.proof(); }
        @Override public List<ActionReceipt> children() { return failure.children(); }
    }
    public static RawJson encode(Document document, ActionPorts.OutcomeArchive archive) {
        Objects.requireNonNull(archive); Map<String, Value> fields = new LinkedHashMap<>();
        if (document instanceof Completed completed)
            StrictJson.require(completed.completion().clockResult().originalReport().isPresent(), "current completed route evidence requires its actual complete clock report");
        refresh(document).ifPresent(RouteContactEvidenceCodec::requireCompleteRefreshResult);
        fields.put("schema", new Text(SCHEMA)); fields.put("status", new Text(document instanceof Completed ? "completed" : "failed"));
        fields.put("parent", DriverJson.object(ActionCodec.encodeCommand(document.parent()), ActionCodec.MAX_COMMAND_BYTES));
        fields.put("parent_body_sha256", new Text(ActionCodec.bodySha256(document.parent())));
        fields.put("starting", frame(document.starting(), archive)); fields.put("ending", frame(document.ending(), archive));
        fields.put("proof", proof(document.proof()));
        fields.put("children", new Arr(document.children().stream().map(archive::preserveReceipt).map(RouteContactEvidenceCodec::ref).map(Value.class::cast).toList()));
        if (document instanceof Completed completed) {
            fields.put("transition", completed.completion().transition().<Value>map(RouteContactEvidenceCodec::transition).orElse(Nil.INSTANCE));
            fields.put("clock", clock(completed.completion().clockResult(), archive));
        } else {
            ContactFailure failure = ((Failed)document).failure();
            fields.put("failure_status", new Text(failure.status())); fields.put("strict_followup_unresolved", new Bool(failure.strictFollowupUnresolved()));
            fields.put("clock_failure_evidence", new Arr(failure.failureEvidence().stream().map(RouteContactEvidenceCodec::ref).map(Value.class::cast).toList()));
            fields.put("clock", failure.clockResult().<Value>map(actual -> clock(actual, archive)).orElse(Nil.INSTANCE));
            fields.put("original_error_message", failure.originalErrorMessage().<Value>map(Text::new).orElse(Nil.INSTANCE));
        }
        fields.put("contact_refresh", refresh(document).<Value>map(actual -> refresh(actual, archive)).orElse(Nil.INSTANCE));
        fields.put("result", result(document));
        return new RawJson(DriverJson.encode(new Obj(fields)));
    }
    public static Document decode(RawJson raw, ActionPorts.OutcomeArchive archive) {
        Obj value = DriverJson.object(raw.bytes(), RawJson.MAXIMUM_BYTES);
        String schema = text(value.get("schema"), "schema"); boolean legacyV2 = schema.equals(LEGACY_SCHEMA_V2);
        boolean legacy = legacyV2 || schema.equals(LEGACY_SCHEMA_V3); boolean legacyV4 = schema.equals(LEGACY_SCHEMA_V4);
        StrictJson.require(schema.equals(SCHEMA) || legacy || legacyV4, "explicit route evidence v2/v3/v4/v5 schema required");
        boolean success = switch (text(value.get("status"), "status")) { case "completed" -> true; case "failed" -> false; default -> throw new IllegalArgumentException("route evidence status differs"); };
        Set<String> fields = new java.util.HashSet<>(Set.of("schema", "status", "parent", "parent_body_sha256", "starting", "ending", "proof", "children", "result"));
        fields.addAll(success ? Set.of("transition", "clock") : Set.of("failure_status", "strict_followup_unresolved"));
        if (!legacy) { fields.add("contact_refresh"); fields.add("clock"); }
        if (!legacy && !success) fields.add("original_error_message");
        if (!success && !legacyV2) fields.add("clock_failure_evidence"); keys(value, fields);
        ActionCommand parent = ActionCodec.decodeCommand(DriverJson.encode(object(value.get("parent"), "parent")));
        StrictJson.require(text(value.get("parent_body_sha256"), "parent_body_sha256").equals(ActionCodec.bodySha256(parent)), "route parent body changed");
        AdvanceObservationPort.Frame start = frame(object(value.get("starting"), "starting"), archive);
        AdvanceObservationPort.Frame end = frame(object(value.get("ending"), "ending"), archive);
        Proof proof = proof(object(value.get("proof"), "proof"), RouteContactCodec.frame(start));
        List<ActionReceipt> children = array(value.get("children"), "children").stream().map(RouteContactEvidenceCodec::ref).map(archive::loadReceipt).toList();
        StrictJson.require(children.stream().map(child -> child.command().actionId()).distinct().count() == children.size(), "duplicate route child");
        Optional<ContactRefresh> refreshed = legacy || required(value, "contact_refresh") == Nil.INSTANCE ? Optional.empty()
                : Optional.of(refresh(object(value.get("contact_refresh"), "contact_refresh"), archive, !legacyV4));
        if (!legacy && !legacyV4) refreshed.ifPresent(RouteContactEvidenceCodec::requireCompleteRefreshResult);
        Document document = success ? new Completed(parent, new Completion(start, end, proof,
                optionalTransition(required(value, "transition")), clock(object(value.get("clock"), "clock"), archive, !legacy), children, refreshed))
                : new Failed(parent, new ContactFailure(start, end, proof, text(value.get("failure_status"), "failure_status"),
                    bool(value.get("strict_followup_unresolved"), "strict_followup_unresolved"), children,
                    legacyV2 ? List.of() : array(value.get("clock_failure_evidence"), "clock_failure_evidence").stream().map(RouteContactEvidenceCodec::ref).toList(),
                    legacy || required(value, "clock") == Nil.INSTANCE ? Optional.empty() : Optional.of(clock(object(value.get("clock"), "clock"), archive, true)), refreshed,
                    legacy || required(value, "original_error_message") == Nil.INSTANCE ? Optional.empty() : Optional.of(text(value.get("original_error_message"), "original_error_message"))));
        StrictJson.require(result(document).equals(object(value.get("result"), "result")), "route result differs from retained typed facts");
        return document;
    }
    /** Complete domain result; the writer owns its history index, ok flag and outer AUTO envelope. */
    public static Obj result(Document document) {
        Frame start = RouteContactCodec.frame(document.starting()), end = RouteContactCodec.frame(document.ending()); Proof proof = document.proof();
        Optional<ClockResult> actualClock = originalClock(document);
        Map<String, Value> value = actualClock.flatMap(ClockResult::originalReport).isPresent()
                ? new LinkedHashMap<>(DriverJson.object(actualClock.flatMap(ClockResult::originalReport).orElseThrow().bytes(), RawJson.MAXIMUM_BYTES).members())
                : new LinkedHashMap<>(); // Explicit legacy v2/v3 DATA has no complete clock report to manufacture.
        value.put("step", new Text(document.parent().operation().value())); value.put("starting_date_raw", number(start.dateRaw()));
        value.put("ending_date_raw", number(end.dateRaw())); value.put("requested_horizon_days", number(proof.horizonDays()));
        value.put("elapsed_days", number(Math.max(0, (end.dateRaw() - start.dateRaw()) / 24)));
        if (document instanceof Completed completed) {
            ClockResult clock = completed.completion().clockResult();
            value.put("progress_status", new Text(clock.progressStatus().wire())); value.put("timeline_speed", number(clock.timelineSpeed()));
            value.put("timeline_policy", new Text(clock.timelinePolicy()));
            if (proof.kind() != ProofKind.BOUNDED_FROZEN_ROUTE_WINDOW && clock.originalReport().isPresent())
                value.put("contact_transition", completed.completion().transition().<Value>map(RouteContactEvidenceCodec::transition).orElse(Nil.INSTANCE));
            else completed.completion().transition().ifPresent(item -> value.put("contact_transition", transition(item)));
        } else {
            ContactFailure failure = ((Failed)document).failure(); value.put("failure_status", new Text(failure.status()));
            if (failure.strictFollowupUnresolved()) {
                Transition boundary = proof.priorBoundary().orElseThrow(() -> new IllegalArgumentException("strict failure requires actual preceding boundary"));
                value.put("contact_followup", new Obj(Map.of("status", new Text(failure.status().equals("exhausted_without_strong_transition")
                        ? "exhausted_without_strong_transition" : "pending_strong_transition"), "episode_run_id", new Text(start.owner().episodeRunId()),
                        "subject_army_id", number(proof.subjectId()), "contact_province_id", number(boundary.contactProvinceId()),
                        "starting_date_raw", number(start.dateRaw()), "ending_date_raw", number(end.dateRaw()),
                        "prior_boundary_ending_date_raw", number(boundary.endingDateRaw()))));
            }
        }
        if (proof.kind() == ProofKind.BOUNDED_FROZEN_ROUTE_WINDOW) {
            value.put("route_contact_window", available(proof.query().project(proof.horizonDays())));
            value.put("route_contact_window_context_basis", new Text("frozen_current_routes"));
        }
        refresh(document).ifPresent(actual -> {
            StrictJson.require(actualClock.flatMap(ClockResult::originalReport).isPresent(), "contact refresh result requires its original complete clock report");
            retarget(value, actual.published().orElse(actual.from()));
            value.put("contact_refresh", publicRefresh(actual));
            if (actual.child().filter(RouteContactComposite::currentPauseConfirmed).isPresent()) {
                ActionReceipt child = actual.child().orElseThrow();
                var actions = new ArrayList<>(array(value.get("actions"), "actual clock actions"));
                RawJson token = actual.originalDriverResult().orElseGet(() -> child.ack().flatMap(NativeActionPort.AckReceived::originalResultToken).orElseThrow()); // Explicit historical v4 DATA only.
                actions.add(new Obj(Map.of("step", new Text("pause-map"), "result", DriverJson.object(token.bytes(), RawJson.MAXIMUM_BYTES))));
                value.put("actions", new Arr(actions));
            }
        });
        return new Obj(value);
    }
    private static Optional<ClockResult> originalClock(Document document) {
        return document instanceof Completed done ? Optional.of(done.completion().clockResult()) : ((Failed)document).failure().clockResult();
    }
    private static Optional<ContactRefresh> refresh(Document document) {
        return document instanceof Completed done ? done.completion().refresh() : ((Failed)document).failure().refresh();
    }
    /** Original _retarget_timeline_step_result; the sole Life producer still owns war summary rendering. */
    private static void retarget(Map<String, Value> result, AdvanceObservationPort.Frame actual) {
        Frame frame = RouteContactCodec.frame(actual);
        result.put("ending_date", new Obj(Map.of("date_raw", number(frame.dateRaw())))); result.put("ending_date_raw", number(frame.dateRaw()));
        int start = integer(result.get("starting_date_raw"), "original clock starting date").intValueExact();
        result.put("elapsed_days", number(Math.max(0, (frame.dateRaw() - start) / 24)));
        result.put("war_progress_after", AdvanceResult.warSummary(actual.semantic())); result.put("paused", new Bool(frame.paused()));
        result.put("active_event", frame.activeEvent()); result.put("final_screen", frame.paused() ? new Text("map_hud") : Nil.INSTANCE);
        result.put("snapshot_id", new Text(frame.snapshotId())); result.put("revision", new IntegerValue(frame.revision())); result.put("native_revision", new IntegerValue(frame.nativeRevision()));
    }
    private static Obj publicRefresh(ContactRefresh actual) {
        Frame from = RouteContactCodec.frame(actual.from()); Optional<Frame> to = actual.published().map(RouteContactCodec::frame);
        var fields = new LinkedHashMap<String, Value>(); fields.put("attempted", new Bool(true));
        fields.put("ack_status", actual.ackStatus().<Value>map(Text::new).orElse(Nil.INSTANCE));
        fields.put("from_snapshot_id", new Text(from.snapshotId())); fields.put("from_revision", new IntegerValue(from.revision())); fields.put("from_native_revision", new IntegerValue(from.nativeRevision()));
        fields.put("to_snapshot_id", to.<Value>map(value -> new Text(value.snapshotId())).orElse(Nil.INSTANCE));
        fields.put("to_revision", to.<Value>map(value -> new IntegerValue(value.revision())).orElse(Nil.INSTANCE)); fields.put("to_native_revision", to.<Value>map(value -> new IntegerValue(value.nativeRevision())).orElse(Nil.INSTANCE));
        fields.put("date_raw", number(from.dateRaw())); return new Obj(fields);
    }
    private static Obj refresh(ContactRefresh actual, ActionPorts.OutcomeArchive archive) {
        return new Obj(Map.of("from_frame", frame(actual.from(), archive), "child_ref", actual.child().<Value>map(value -> ref(archive.preserveReceipt(value))).orElse(Nil.INSTANCE),
                "published_frame", actual.published().<Value>map(value -> frame(value, archive)).orElse(Nil.INSTANCE), "ack_status", actual.ackStatus().<Value>map(Text::new).orElse(Nil.INSTANCE),
                "original_driver_result", actual.originalDriverResult().<Value>map(value -> ref(archive.preserveMaterial(value))).orElse(Nil.INSTANCE)));
    }
    private static ContactRefresh refresh(Obj value, ActionPorts.OutcomeArchive archive, boolean current) {
        var fields = new java.util.HashSet<>(Set.of("from_frame", "child_ref", "published_frame", "ack_status")); if (current) fields.add("original_driver_result"); keys(value, fields);
        return new ContactRefresh(frame(object(value.get("from_frame"), "from_frame"), archive),
                required(value, "child_ref") == Nil.INSTANCE ? Optional.empty() : Optional.of(archive.loadReceipt(ref(value.get("child_ref")))),
                required(value, "published_frame") == Nil.INSTANCE ? Optional.empty() : Optional.of(frame(object(value.get("published_frame"), "published_frame"), archive)),
                required(value, "ack_status") == Nil.INSTANCE ? Optional.empty() : Optional.of(text(value.get("ack_status"), "ack_status")),
                !current || required(value, "original_driver_result") == Nil.INSTANCE ? Optional.empty() : Optional.of(archive.loadMaterial(ref(value.get("original_driver_result")))));
    }
    private static void requireCompleteRefreshResult(ContactRefresh refresh) {
        if (refresh.child().filter(RouteContactComposite::currentPauseConfirmed).isPresent()) {
            RawJson raw = refresh.originalDriverResult().orElseThrow(() -> new IllegalArgumentException("current pause refresh requires the complete original Driver result, not its ACK token"));
            Obj value = DriverJson.object(raw.bytes(), RawJson.MAXIMUM_BYTES); ActionReceipt child = refresh.child().orElseThrow();
            StrictJson.require(text(value.get("step"), "original pause step").equals("pause-map")
                    && text(value.get("backend_id"), "original pause backend").equals("native-headless")
                    && text(value.get("native_request_id"), "original pause request").equals(child.ack().orElseThrow().requestId()), "complete original pause result crossed its actual child");
        }
    }
    public static Obj queryResult(RouteQuery query) {
        return new Obj(Map.of("queried_snapshot_id", new Text(query.snapshotId()), "queried_revision", new IntegerValue(query.revision()),
                "queried_native_revision", new IntegerValue(query.nativeRevision()), "queried_connection_generation", new IntegerValue(query.owner().connectionGeneration()),
                "queried_episode_run_id", new Text(query.owner().episodeRunId()), "route_contact_horizon", horizon(query)));
    }
    public static Obj transition(Transition item) {
        return new Obj(Map.of("status", new Text(item.kind() == TransitionKind.PREDICTED_CONTACT_BOUNDARY_REACHED ? "predicted_only" : "observed"),
                "proof_kind", new Text("unavoidable_current_province_contact"), "postcondition", new Text(item.kind().wire()),
                "contact_observed", new Bool(item.contactObserved()), "episode_run_id", new Text(item.episodeRunId()),
                "subject_army_id", number(item.subjectArmyId()), "contact_province_id", number(item.contactProvinceId()),
                "starting_date_raw", number(item.startingDateRaw()), "ending_date_raw", number(item.endingDateRaw()),
                "conflict_hostile_army_ids", integers(item.changedHostileIds())));
    }
    private static Transition transition(Obj value) {
        keys(value, Set.of("status", "proof_kind", "postcondition", "contact_observed", "episode_run_id", "subject_army_id", "contact_province_id", "starting_date_raw", "ending_date_raw", "conflict_hostile_army_ids"));
        Transition item = new Transition(TransitionKind.valueOf(text(value.get("postcondition"), "postcondition").toUpperCase(java.util.Locale.ROOT)),
                bool(value.get("contact_observed"), "contact_observed"), text(value.get("episode_run_id"), "episode_run_id"),
                integer32(value.get("subject_army_id")), integer32(value.get("contact_province_id")), integer32(value.get("starting_date_raw")),
                integer32(value.get("ending_date_raw")), integers(value.get("conflict_hostile_army_ids")));
        StrictJson.require(transition(item).equals(value), "route transition domain differs"); return item;
    }
    private static Optional<Transition> optionalTransition(Value value) { return value == Nil.INSTANCE ? Optional.empty() : Optional.of(transition(object(value, "transition"))); }
    private static Obj proof(Proof proof) {
        List<Value> windows = proof.controlledWindows().entrySet().stream().sorted(Map.Entry.comparingByKey())
                .map(item -> (Value)new Obj(Map.of("army_id", number(item.getKey()), "window", available(item.getValue())))).toList();
        return new Obj(Map.of("kind", new Text(proof.kind().name()), "query_step", new Text(proof.query().step()), "query", queryResult(proof.query()),
                "strict_followup", new Bool(proof.strictFollowup()), "prior_boundary", proof.priorBoundary().<Value>map(RouteContactEvidenceCodec::transition).orElse(Nil.INSTANCE),
                "horizon_days", number(proof.horizonDays()), "watch_army_ids", integers(proof.watchArmyIds()), "controlled_windows", new Arr(windows)));
    }
    private static Proof proof(Obj value, Frame start) {
        keys(value, Set.of("kind", "query_step", "query", "strict_followup", "prior_boundary", "horizon_days", "watch_army_ids", "controlled_windows"));
        RouteQuery query = RouteContactCodec.query(text(value.get("query_step"), "query_step"), true, start, object(value.get("query"), "query"));
        Map<Integer, RouteWindowPolicy.Available> windows = new LinkedHashMap<>();
        for (Value raw : array(value.get("controlled_windows"), "controlled_windows")) {
            Obj item = object(raw, "controlled_window"); keys(item, Set.of("army_id", "window")); int id = unit(integer32(item.get("army_id")));
            StrictJson.require(windows.putIfAbsent(id, available(object(item.get("window"), "window"))) == null, "duplicate controlled window");
        }
        Proof result = new Proof(ProofKind.valueOf(text(value.get("kind"), "kind")), query, bool(value.get("strict_followup"), "strict_followup"),
                optionalTransition(required(value, "prior_boundary")), integer32(value.get("horizon_days")), integers(value.get("watch_army_ids")), windows);
        StrictJson.require(proof(result).equals(value), "route proof JSON domain differs"); return result;
    }
    private static Obj horizon(RouteQuery query) {
        Map<String, Value> fields = new LinkedHashMap<>(); fields.put("status", new Text("available")); fields.put("date_raw", number(query.dateRaw()));
        fields.put("snapshot_revision", new IntegerValue(query.nativeRevision())); fields.put("subject_army_id", number(query.subjectArmyId()));
        fields.put("target_province_id", number(query.targetProvinceId())); fields.put("hostile_army_ids", integers(query.hostileArmyIds()));
        fields.put("subject_route", route(query.subjectRoute(), query.subjectEffectiveOriginProvinceId())); List<Value> routes = new ArrayList<>();
        for (int index = 0; index < query.hostileRoutes().size(); index++) routes.add(route(query.hostileRoutes().get(index), query.hostileEffectiveOriginProvinceIds().get(index)));
        fields.put("hostile_routes", new Arr(routes)); fields.put("horizon_start_date_raw", number(query.dateRaw())); fields.put("horizon_end_date_raw", number(Math.addExact(query.dateRaw(), 24)));
        fields.put("one_day_contact_free", new Bool(query.oneDayContactFree())); fields.put("conflicts", new Arr(query.nativeConflicts().stream().map(RouteContactEvidenceCodec::conflict).map(Value.class::cast).toList()));
        return new Obj(fields);
    }
    private static Obj route(RouteWindowPolicy.Route route, int origin) {
        return new Obj(Map.of("timeline_observable", new Bool(true), "army_id", number(route.armyId()), "current_province_id", number(route.currentProvinceId()),
                "effective_origin_province_id", number(origin), "route_province_ids", integers(route.provinceIds()), "arrival_date_raws", integers(route.arrivalDateRaws())));
    }
    private static Obj conflict(RouteWindowPolicy.Conflict conflict) {
        Map<String, Value> fields = new LinkedHashMap<>(); fields.put("hostile_army_id", number(conflict.hostileArmyId()));
        fields.put("overlap_start_date_raw", number(conflict.overlapStartDateRaw())); fields.put("overlap_end_date_raw", number(conflict.overlapEndDateRaw()));
        if (conflict instanceof RouteWindowPolicy.SameProvince same) { fields.put("kind", new Text("same_province")); fields.put("province_id", number(same.provinceId())); }
        else { var edge = (RouteWindowPolicy.OpposingEdge)conflict; fields.put("kind", new Text("opposing_edge"));
            fields.put("subject_from_province_id", number(edge.subjectFromProvinceId())); fields.put("subject_to_province_id", number(edge.subjectToProvinceId()));
            fields.put("hostile_from_province_id", number(edge.hostileFromProvinceId())); fields.put("hostile_to_province_id", number(edge.hostileToProvinceId())); }
        return new Obj(fields);
    }
    private static RouteWindowPolicy.Conflict conflict(Obj item) {
        String kind = text(item.get("kind"), "kind"); RouteWindowPolicy.Conflict result;
        int id = integer32(item.get("hostile_army_id")), start = integer32(item.get("overlap_start_date_raw")), end = integer32(item.get("overlap_end_date_raw"));
        if (kind.equals("same_province")) result = new RouteWindowPolicy.SameProvince(id, integer32(item.get("province_id")), start, end);
        else { StrictJson.require(kind.equals("opposing_edge"), "unknown route conflict"); result = new RouteWindowPolicy.OpposingEdge(id,
                integer32(item.get("subject_from_province_id")), integer32(item.get("subject_to_province_id")), integer32(item.get("hostile_from_province_id")), integer32(item.get("hostile_to_province_id")), start, end); }
        StrictJson.require(conflict(result).equals(item), "route conflict fields differ"); return result;
    }
    private static Obj available(RouteWindowPolicy.Available window) {
        return new Obj(Map.of("status", new Text("available"), "context_basis", new Text("frozen_current_routes"), "horizon_days", number(window.horizonDays()),
                "window_start_date_raw", number(window.windowStartDateRaw()), "window_end_date_raw", number(window.windowEndDateRaw()), "contact_free", new Bool(window.contactFree()),
                "conflicts", new Arr(window.conflicts().stream().map(RouteContactEvidenceCodec::conflict).map(Value.class::cast).toList()),
                "first_contact_date_raw", window.firstContactDateRaw() == null ? Nil.INSTANCE : number(window.firstContactDateRaw()),
                "contact_free_whole_days", number(window.contactFreeWholeDays()), "missing", new Arr(List.of())));
    }
    private static RouteWindowPolicy.Available available(Obj item) {
        keys(item, Set.of("status", "context_basis", "horizon_days", "window_start_date_raw", "window_end_date_raw", "contact_free", "conflicts", "first_contact_date_raw", "contact_free_whole_days", "missing"));
        RouteWindowPolicy.Available value = new RouteWindowPolicy.Available(integer32(item.get("horizon_days")), integer32(item.get("window_start_date_raw")), integer32(item.get("window_end_date_raw")),
                array(item.get("conflicts"), "conflicts").stream().map(raw -> conflict(object(raw, "conflict"))).toList(),
                required(item, "first_contact_date_raw") == Nil.INSTANCE ? null : integer32(item.get("first_contact_date_raw")), integer32(item.get("contact_free_whole_days")));
        StrictJson.require(available(value).equals(item), "available window fields differ"); return value;
    }
    private static Obj frame(AdvanceObservationPort.Frame frame, ActionPorts.OutcomeArchive archive) {
        ExactRef semantic = archive.preserveMaterial(RawJson.fullMaterial(DriverJson.encode(frame.semantic())));
        return new Obj(Map.of("identity", OpportunityJson.parse(ProposalLifecycleCodec.encodePayload(ProposalLifecycleCodec.observation(frame.identity()))),
                "source", OpportunityJson.parse(ProposalLifecycleCodec.encodePayload(ProposalLifecycleCodec.source(frame.source()))), "session_id", new Text(frame.sessionId()),
                "semantic", ref(semantic), "provenance", OpportunityJson.parse(ObservationProvenanceCodec.encode(frame.provenance()).toString().getBytes(StandardCharsets.UTF_8)),
                "observed_at_utc", new Text(frame.observedAt().toString()), "original_evidence", ref(frame.originalEvidence())));
    }
    private static AdvanceObservationPort.Frame frame(Obj value, ActionPorts.OutcomeArchive archive) {
        keys(value, Set.of("identity", "source", "session_id", "semantic", "provenance", "observed_at_utc", "original_evidence"));
        var result = new AdvanceObservationPort.Frame(ProposalLifecycleCodec.decodeObservation(OpportunityJson.toNode(value.get("identity"))), G2Wire.source(OpportunityJson.toNode(value.get("source"))),
                text(value.get("session_id"), "session_id"), DriverJson.object(archive.loadFullMaterial(ref(value.get("semantic"))).bytes(), RawJson.MAXIMUM_BYTES),
                ObservationProvenanceCodec.decode(OpportunityJson.toNode(value.get("provenance"))),
                Instant.parse(text(value.get("observed_at_utc"), "observed_at_utc")), ref(value.get("original_evidence")));
        RouteContactCodec.frame(result); return result;
    }
    private static Obj clock(ClockResult result, ActionPorts.OutcomeArchive archive) {
        return new Obj(Map.of("ending", frame(result.ending(), archive), "native_clock_verified", new Bool(result.nativeClockVerified()), "unknown", new Bool(result.unknown()), "reason", new Text(result.reason()),
                "progress_status", new Text(result.progressStatus().name()), "timeline_speed", number(result.timelineSpeed()), "timeline_policy", new Text(result.timelinePolicy()),
                "checkpoint_eligible", new Bool(result.checkpointEligible()), "native_stop_read", result.nativeStopRead().<Value>map(read -> ref(archive.preserveRead(read.receipt()))).orElse(Nil.INSTANCE),
                "original_clock_report", ref(archive.preserveMaterial(result.originalReport().orElseThrow()))));
    }
    private static ClockResult clock(Obj value, ActionPorts.OutcomeArchive archive, boolean currentReport) {
        var expected = new java.util.HashSet<>(Set.of("ending", "native_clock_verified", "unknown", "reason", "progress_status", "timeline_speed", "timeline_policy", "checkpoint_eligible", "native_stop_read"));
        if (currentReport) expected.add("original_clock_report"); keys(value, expected);
        AdvanceObservationPort.Frame end = frame(object(value.get("ending"), "ending"), archive);
        Value stop = required(value, "native_stop_read"); Optional<ClockStatusRead.Observation> status = Optional.empty();
        if (stop != Nil.INSTANCE) { PlanningReadReceipt read = archive.loadRead(ref(stop));
            status = Optional.of(new ClockStatusRead.Observation(ClockStatusRead.decode(read.original()), read, archive.referenceOf(read.original()))); }
        Optional<RawJson> report = currentReport ? Optional.of(archive.loadFullMaterial(ref(required(value, "original_clock_report")))) : Optional.empty();
        report.ifPresent(raw -> DriverJson.object(raw.bytes(), RawJson.MAXIMUM_BYTES));
        return new ClockResult(end, bool(value.get("native_clock_verified"), "native_clock_verified"), bool(value.get("unknown"), "unknown"), text(value.get("reason"), "reason"),
                ClockProgress.valueOf(text(value.get("progress_status"), "progress_status")), integer32(value.get("timeline_speed")), text(value.get("timeline_policy"), "timeline_policy"), bool(value.get("checkpoint_eligible"), "checkpoint_eligible"), status, List.of(), report);
    }
    private static void bind(ActionCommand parent, AdvanceObservationPort.Frame start, Proof proof) {
        var request = RouteContactSteps.parse(parent.operation().value());
        StrictJson.require(start.identity().equals(parent.before()) && start.source().equals(parent.source()) && start.sessionId().equals(parent.sessionId())
                && RouteContactProofs.sameFrame(RouteContactCodec.frame(start), proof.query()) && request.days() == proof.horizonDays()
                && request.scope().equals(new RouteContactProofs.Scope(proof.subjectId(), proof.targetProvinceId(), proof.hostileIds())), "route evidence parent/start/proof differs");
    }
    private static Obj ref(ExactRef value) { return new Obj(Map.of("path", new Text(value.path()), "bytes", new IntegerValue(BigInteger.valueOf(value.bytes())), "sha256", new Text(value.sha256()))); }
    private static ExactRef ref(Value raw) { Obj value = object(raw, "reference"); keys(value, Set.of("path", "bytes", "sha256")); return new ExactRef(text(value.get("path"), "path"), integer(value.get("bytes"), "bytes").longValueExact(), text(value.get("sha256"), "sha256")); }
    private static IntegerValue number(int value) { return new IntegerValue(BigInteger.valueOf(value)); }
    private static Arr integers(List<Integer> values) { return new Arr(values.stream().map(RouteContactEvidenceCodec::number).map(Value.class::cast).toList()); }
    private static List<Integer> integers(Value value) { return array(value, "integers").stream().map(RouteContactEvidenceCodec::integer32).toList(); }
    private static int integer32(Value value) { return integer(value, "int32").intValueExact(); }
    private static Value required(Obj value, String key) { StrictJson.require(value.members().containsKey(key), "missing is not null: " + key); return value.get(key); }
    private static void keys(Obj value, Set<String> fields) { StrictJson.require(value.members().keySet().equals(fields), "route evidence fields differ"); }
}
