package org.xar.ck3.control.nativebridge;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** Exact AE2 observation DATA, with no invented public case values or action authority. */
public record CurrentZg361Ae2Source(Kind kind, Optional<Controls> controls, Optional<Events> events, Optional<Review> review) {
    public enum Kind {
        CONTROLS("controls"), EVENTS("events"), REVIEW("review");
        private final String wire;
        Kind(String wire) { this.wire = wire; }
        public String wire() { return wire; }
        public static Kind parse(String text) throws IOException {
            for (var kind : values()) if (kind.wire.equals(text)) return kind;
            throw new IOException("Unknown AE2 Source kind");
        }
    }

    public enum Control {
        PRESENT("present", "zga_ae2_present_decision"), VERIFY("verify", "zga_ae2_verify_decision");
        private final String wire;
        private final String definitionKey;
        Control(String wire, String definitionKey) { this.wire = wire; this.definitionKey = definitionKey; }
        public String wire() { return wire; }
        public String definitionKey() { return definitionKey; }
        public static Control parse(String text) throws IOException {
            for (var control : values()) if (control.wire.equals(text)) return control;
            throw new IOException("Unknown fixed AE2 control");
        }
    }

    public record ControlRow(Control control, String definitionKey, boolean nativeCanOpenDetail,
            boolean openDetailAdmissible, Optional<Boolean> nativeCanConfirm, boolean confirmAdmissible) {
        public ControlRow {
            Objects.requireNonNull(control); Objects.requireNonNull(nativeCanConfirm);
            StrictJson.require(control.definitionKey().equals(definitionKey), "Exact AE2 control definition required");
            if (openDetailAdmissible) StrictJson.require(nativeCanOpenDetail, "Open detail requires actual NativeCan");
            if (confirmAdmissible) StrictJson.require(nativeCanConfirm.orElse(false), "Confirm requires actual NativeCan");
        }
        static ControlRow decode(JsonNode node) throws IOException {
            var r = StrictJson.object(node, Set.of("control", "definition_key", "native_can_open_detail",
                    "open_detail_admissible", "native_can_confirm", "confirm_admissible"));
            var can = r.get("native_can_confirm");
            if (!can.isNull() && !can.isBoolean()) throw new IOException("Nullable AE2 NativeCan bool required");
            return new ControlRow(Control.parse(NativeWire.text(r.get("control"))), NativeWire.text(r.get("definition_key")),
                    b(r,"native_can_open_detail"), b(r,"open_detail_admissible"),
                    can.isNull() ? Optional.empty() : Optional.of(can.booleanValue()), b(r,"confirm_admissible"));
        }
        ObjectNode encode() {
            var r = StrictJson.object().put("control",control.wire()).put("definition_key",definitionKey)
                    .put("native_can_open_detail",nativeCanOpenDetail).put("open_detail_admissible",openDetailAdmissible)
                    .put("confirm_admissible",confirmAdmissible);
            if (nativeCanConfirm.isPresent()) r.put("native_can_confirm",nativeCanConfirm.orElseThrow());
            else r.putNull("native_can_confirm");
            return r;
        }
    }

    public record Controls(boolean residentAvailable, boolean listVisible, boolean detailVisible,
            boolean actorBound, boolean modelComplete, boolean blockedByVisibleModal,
            boolean openListAdmissible, Optional<Control> selectedControl, List<ControlRow> rows) {
        public Controls {
            Objects.requireNonNull(selectedControl); rows = List.copyOf(rows);
            StrictJson.require(rows.size() <= 2, "At most two fixed AE2 control rows required");
            var seen = new HashSet<Control>();
            for (var row : rows) {
                StrictJson.require(seen.add(row.control()), "Duplicate fixed AE2 control");
                boolean selected = selectedControl.filter(c -> c == row.control()).isPresent();
                if (row.nativeCanConfirm().isPresent()) StrictJson.require(selected && detailVisible,
                        "Nullable NativeCan belongs only to actual selected visible detail");
                if (row.openDetailAdmissible()) StrictJson.require(actorBound && modelComplete && listVisible
                        && !blockedByVisibleModal, "AE2 detail necessary Source conditions differ");
                if (row.confirmAdmissible()) StrictJson.require(selected && detailVisible && actorBound && modelComplete
                        && !blockedByVisibleModal, "AE2 confirmation necessary Source conditions differ");
            }
            if (openListAdmissible) StrictJson.require(residentAvailable && actorBound && !listVisible
                    && !detailVisible && !blockedByVisibleModal, "AE2 open-list necessary Source conditions differ");
        }
        public Optional<ControlRow> row(Control control) {
            Objects.requireNonNull(control); return rows.stream().filter(row -> row.control() == control).findFirst();
        }
        static Controls decode(JsonNode node) throws IOException {
            var r = StrictJson.object(node, Set.of("resident_available", "list_visible", "detail_visible", "actor_bound",
                    "model_complete", "blocked_by_visible_modal", "open_list_admissible", "selected_control", "rows"));
            var rows = new ArrayList<ControlRow>();
            for (var n : array(r,"rows",2)) rows.add(ControlRow.decode(n));
            return new Controls(b(r,"resident_available"), b(r,"list_visible"), b(r,"detail_visible"), b(r,"actor_bound"),
                    b(r,"model_complete"), b(r,"blocked_by_visible_modal"), b(r,"open_list_admissible"),
                    r.get("selected_control").isNull() ? Optional.empty() : Optional.of(Control.parse(NativeWire.text(r.get("selected_control")))), rows);
        }
        ObjectNode encode() {
            var r = StrictJson.object().put("resident_available",residentAvailable).put("list_visible",listVisible)
                    .put("detail_visible",detailVisible).put("actor_bound",actorBound).put("model_complete",modelComplete)
                    .put("blocked_by_visible_modal",blockedByVisibleModal).put("open_list_admissible",openListAdmissible);
            if (selectedControl.isPresent()) r.put("selected_control",selectedControl.orElseThrow().wire());
            else r.putNull("selected_control");
            var a = r.putArray("rows"); for (var row : rows) a.add(row.encode()); return r;
        }
    }

    public record EventIdentity(int instanceId, long recipientCharacterId, String definitionKey) {
        public EventIdentity {
            StrictJson.require(instanceId > 0, "Actual positive Letter instance required");
            CurrentLivingInventoryQuery.requireFullId(recipientCharacterId); key(definitionKey);
        }
        static EventIdentity decode(JsonNode node) throws IOException {
            var r = StrictJson.object(node, Set.of("instance_id", "recipient_character_id", "definition_key"));
            return new EventIdentity(CurrentLivingInventoryQuery.i32(r.get("instance_id")),
                    CurrentLivingInventoryQuery.fullId(r.get("recipient_character_id")), NativeWire.text(r.get("definition_key")));
        }
        ObjectNode encode() {
            return StrictJson.object().put("instance_id",instanceId).put("recipient_character_id",recipientCharacterId)
                    .put("definition_key",definitionKey);
        }
    }

    public record Option(int authoredOptionIndex, String optionKey, boolean nativeCanSelect,
            String text, String disabledReason, String tooltip) {
        public Option {
            StrictJson.require(authoredOptionIndex >= 15 && authoredOptionIndex <= 17
                    && (CurrentZg361Ae2.EVENT_DEFINITION + ".ae2.r" + (authoredOptionIndex - 14)).equals(optionKey),
                    "Exact original AE2 authored15/16/17 and r1/r2/r3 join required");
            CurrentZg361Ae2.requireActualText(text,false); CurrentZg361Ae2.requireActualText(disabledReason,false);
            CurrentZg361Ae2.requireActualText(tooltip,true);
        }
        static Option decode(JsonNode node) throws IOException {
            var r = StrictJson.object(node, Set.of("authored_option_index", "option_key", "native_can_select",
                    "text", "disabled_reason", "tooltip"));
            return new Option(CurrentLivingInventoryQuery.i32(r.get("authored_option_index")), NativeWire.text(r.get("option_key")),
                    b(r,"native_can_select"), CurrentZg361Ae2.actualText(r.get("text"),false),
                    CurrentZg361Ae2.actualText(r.get("disabled_reason"),false), CurrentZg361Ae2.actualText(r.get("tooltip"),true));
        }
        ObjectNode encode() {
            return StrictJson.object().put("authored_option_index",authoredOptionIndex).put("option_key",optionKey)
                    .put("native_can_select",nativeCanSelect).put("text",text).put("disabled_reason",disabledReason).put("tooltip",tooltip);
        }
    }

    public record Ae2(int instanceId, long recipientCharacterId, String definitionKey, int authoredOptionCount,
            boolean phaseBound, boolean namedRootBound, boolean windowVisible, boolean windowEnabled,
            boolean tooltipsComplete, List<Option> options, boolean payNowAdmissible) {
        public Ae2 {
            StrictJson.require(instanceId > 0 && CurrentZg361Ae2.EVENT_DEFINITION.equals(definitionKey)
                    && authoredOptionCount == CurrentZg361Ae2.AUTHORED_COUNT, "Exact AE2 identity/authored42 required");
            CurrentLivingInventoryQuery.requireFullId(recipientCharacterId); options = List.copyOf(options);
            StrictJson.require(options.size() == 3, "Complete three displayed AE2 rows required");
            var seen = new HashSet<Integer>();
            for (var option : options) StrictJson.require(seen.add(option.authoredOptionIndex()), "Duplicate AE2 authored index");
            if (payNowAdmissible) StrictJson.require(phaseBound && namedRootBound && windowVisible && windowEnabled
                    && tooltipsComplete && options.stream().anyMatch(row -> row.authoredOptionIndex() == 15 && row.nativeCanSelect()),
                    "Pay-now necessary actual phase/root/tooltip/r1-Can conditions differ");
        }
        public Option payNowOption() {
            return options.stream().filter(row -> row.authoredOptionIndex() == 15).findFirst().orElseThrow();
        }
        static Ae2 decode(JsonNode node) throws IOException {
            var r = StrictJson.object(node, Set.of("instance_id", "recipient_character_id", "definition_key", "authored_option_count",
                    "phase_bound", "named_root_bound", "window_visible", "window_enabled", "tooltips_complete", "options", "pay_now_admissible"));
            var rows = new ArrayList<Option>(); for (var n : array(r,"options",3)) rows.add(Option.decode(n));
            return new Ae2(CurrentLivingInventoryQuery.i32(r.get("instance_id")), CurrentLivingInventoryQuery.fullId(r.get("recipient_character_id")),
                    NativeWire.text(r.get("definition_key")), CurrentLivingInventoryQuery.i32(r.get("authored_option_count")),
                    b(r,"phase_bound"), b(r,"named_root_bound"), b(r,"window_visible"), b(r,"window_enabled"),
                    b(r,"tooltips_complete"), rows, b(r,"pay_now_admissible"));
        }
        ObjectNode encode() {
            var r = StrictJson.object().put("instance_id",instanceId).put("recipient_character_id",recipientCharacterId)
                    .put("definition_key",definitionKey).put("authored_option_count",authoredOptionCount).put("phase_bound",phaseBound)
                    .put("named_root_bound",namedRootBound).put("window_visible",windowVisible).put("window_enabled",windowEnabled)
                    .put("tooltips_complete",tooltipsComplete).put("pay_now_admissible",payNowAdmissible);
            var a = r.putArray("options"); for (var row : options) a.add(row.encode()); return r;
        }
    }

    public record Events(boolean censusComplete, List<EventIdentity> census, Optional<Ae2> ae2) {
        public Events {
            census = List.copyOf(census); Objects.requireNonNull(ae2);
            StrictJson.require(censusComplete && census.size() <= 32, "Complete bounded AE2 identity census required");
            var seen = new HashSet<Integer>();
            for (var row : census) StrictJson.require(seen.add(row.instanceId()), "Duplicate actual event instance");
            var actualCensus = census;
            ae2.ifPresent(snapshot -> StrictJson.require(actualCensus.stream().anyMatch(row -> row.instanceId() == snapshot.instanceId()
                    && row.recipientCharacterId() == snapshot.recipientCharacterId() && row.definitionKey().equals(snapshot.definitionKey())),
                    "AE2 snapshot must join its exact original census identity"));
        }
        static Events decode(JsonNode node) throws IOException {
            var r = StrictJson.object(node, Set.of("census_complete", "census", "ae2"));
            var rows = new ArrayList<EventIdentity>(); for (var n : array(r,"census",32)) rows.add(EventIdentity.decode(n));
            return new Events(b(r,"census_complete"), rows, r.get("ae2").isNull() ? Optional.empty() : Optional.of(Ae2.decode(r.get("ae2"))));
        }
        ObjectNode encode() {
            var r = StrictJson.object().put("census_complete",censusComplete); var a = r.putArray("census");
            for (var row : census) a.add(row.encode());
            if (ae2.isPresent()) r.set("ae2",ae2.orElseThrow().encode()); else r.putNull("ae2"); return r;
        }
    }

    /** Fixed target metadata and actual selected-window DATA are deliberately separate. */
    public record Review(String definitionKey, boolean residentAvailable, boolean listVisible,
            boolean detailVisible, boolean detailEnabled, boolean actorBound, boolean modelComplete,
            boolean blockedByVisibleModal, boolean rowPresent, boolean selectedReview,
            boolean openDetailAdmissible, boolean requirementsComplete, Optional<String> selectedDefinitionKey,
            Optional<Boolean> hasRequirements, Optional<String> requirementsDescription) {
        public Review {
            StrictJson.require(CurrentZg361Ae2.REVIEW_DEFINITION.equals(definitionKey), "Exact fixed review target metadata required");
            Objects.requireNonNull(selectedDefinitionKey); Objects.requireNonNull(hasRequirements); Objects.requireNonNull(requirementsDescription);
            selectedDefinitionKey.ifPresent(CurrentZg361Ae2Source::key);
            requirementsDescription.ifPresent(text -> CurrentZg361Ae2.requireActualText(text,true));
            if (selectedReview) StrictJson.require(detailVisible && selectedDefinitionKey.filter(CurrentZg361Ae2.REVIEW_DEFINITION::equals).isPresent(),
                    "Selected review must retain actual visible detail and selected definition");
            if (requirementsComplete) StrictJson.require(selectedReview && actorBound && modelComplete && rowPresent
                    && hasRequirements.isPresent() && requirementsDescription.isPresent(), "Complete review requirements need both actual returned values and bound material");
            else StrictJson.require(hasRequirements.isEmpty() && requirementsDescription.isEmpty(), "Incomplete review requirements stay null, never synthetic empty");
            if (openDetailAdmissible) StrictJson.require(residentAvailable && actorBound && modelComplete && rowPresent
                    && listVisible && !selectedReview && !blockedByVisibleModal, "Review open-detail necessary actual conditions differ");
        }
        static Review decode(JsonNode node) throws IOException {
            var r = StrictJson.object(node, Set.of("definition_key", "resident_available", "list_visible", "detail_visible", "detail_enabled",
                    "actor_bound", "model_complete", "blocked_by_visible_modal", "row_present", "selected_review", "open_detail_admissible",
                    "requirements_complete", "selected_definition_key", "has_requirements", "requirements_description"));
            var has = r.get("has_requirements");
            if (!has.isNull() && !has.isBoolean()) throw new IOException("Nullable actual HasRequirements bool required");
            return new Review(NativeWire.text(r.get("definition_key")), b(r,"resident_available"), b(r,"list_visible"), b(r,"detail_visible"),
                    b(r,"detail_enabled"), b(r,"actor_bound"), b(r,"model_complete"), b(r,"blocked_by_visible_modal"), b(r,"row_present"),
                    b(r,"selected_review"), b(r,"open_detail_admissible"), b(r,"requirements_complete"),
                    r.get("selected_definition_key").isNull() ? Optional.empty() : Optional.of(CurrentZg361Ae2.actualText(r.get("selected_definition_key"),false)),
                    has.isNull() ? Optional.empty() : Optional.of(has.booleanValue()),
                    r.get("requirements_description").isNull() ? Optional.empty() : Optional.of(CurrentZg361Ae2.actualText(r.get("requirements_description"),true)));
        }
        ObjectNode encode() {
            var r = StrictJson.object().put("definition_key",definitionKey).put("resident_available",residentAvailable).put("list_visible",listVisible)
                    .put("detail_visible",detailVisible).put("detail_enabled",detailEnabled).put("actor_bound",actorBound).put("model_complete",modelComplete)
                    .put("blocked_by_visible_modal",blockedByVisibleModal).put("row_present",rowPresent).put("selected_review",selectedReview)
                    .put("open_detail_admissible",openDetailAdmissible).put("requirements_complete",requirementsComplete);
            if (selectedDefinitionKey.isPresent()) r.put("selected_definition_key",selectedDefinitionKey.orElseThrow()); else r.putNull("selected_definition_key");
            if (hasRequirements.isPresent()) r.put("has_requirements",hasRequirements.orElseThrow()); else r.putNull("has_requirements");
            if (requirementsDescription.isPresent()) r.put("requirements_description",requirementsDescription.orElseThrow()); else r.putNull("requirements_description");
            return r;
        }
    }

    public CurrentZg361Ae2Source(Kind kind, Optional<Controls> controls, Optional<Events> events) {
        this(kind,controls,events,Optional.empty());
    }

    public CurrentZg361Ae2Source {
        Objects.requireNonNull(kind); Objects.requireNonNull(controls); Objects.requireNonNull(events); Objects.requireNonNull(review);
        StrictJson.require(switch (kind) {
            case CONTROLS -> controls.isPresent() && events.isEmpty() && review.isEmpty();
            case EVENTS -> controls.isEmpty() && events.isPresent() && review.isEmpty();
            case REVIEW -> controls.isEmpty() && events.isEmpty() && review.isPresent();
        }, "Exact AE2 Source union required");
    }

    /** Necessary DATA predicate only; never creates a Native claim or private present-to-event custody. */
    public boolean actionAdmissible(CurrentZg361Ae2.Action action) {
        Objects.requireNonNull(action); if (kind != action.sourceKind()) return false;
        if (action.queryOnly()) return true;
        return switch (action) {
            case OPEN_CONTROLS_LIST -> controls.orElseThrow().openListAdmissible();
            case OPEN_PRESENT_DETAIL -> controls.orElseThrow().row(Control.PRESENT).map(ControlRow::openDetailAdmissible).orElse(false);
            case OPEN_VERIFY_DETAIL -> controls.orElseThrow().row(Control.VERIFY).map(ControlRow::openDetailAdmissible).orElse(false);
            case CONFIRM_PRESENT -> controls.orElseThrow().row(Control.PRESENT).map(ControlRow::confirmAdmissible).orElse(false);
            case CONFIRM_VERIFY -> controls.orElseThrow().row(Control.VERIFY).map(ControlRow::confirmAdmissible).orElse(false);
            case OPEN_REVIEW_DETAIL -> review.orElseThrow().openDetailAdmissible();
            case CHOOSE_PAY_NOW -> events.orElseThrow().ae2().map(Ae2::payNowAdmissible).orElse(false);
            default -> false;
        };
    }

    public static CurrentZg361Ae2Source decode(JsonNode node) throws IOException {
        try {
            var object = NativeWire.object(node);
            Kind kind = Kind.parse(NativeWire.text(object.get("kind")));
            var r = StrictJson.object(object,kind == Kind.REVIEW ? Set.of("schema","kind","review")
                    : Set.of("schema","kind","controls","events"));
            CurrentLivingInventoryQuery.identity(r,"schema",CurrentZg361Ae2.SOURCE_SCHEMA);
            if (kind == Kind.REVIEW) return new CurrentZg361Ae2Source(kind,Optional.empty(),Optional.empty(),Optional.of(Review.decode(r.get("review"))));
            return new CurrentZg361Ae2Source(kind,
                    r.get("controls").isNull() ? Optional.empty() : Optional.of(Controls.decode(r.get("controls"))),
                    r.get("events").isNull() ? Optional.empty() : Optional.of(Events.decode(r.get("events"))));
        } catch (IllegalArgumentException | ArithmeticException invalid) { throw new IOException("Invalid exact AE2 Source DATA",invalid); }
    }
    public ObjectNode encode() {
        var r = StrictJson.object().put("schema",CurrentZg361Ae2.SOURCE_SCHEMA).put("kind",kind.wire());
        if (kind == Kind.REVIEW) { r.set("review",review.orElseThrow().encode()); return r; }
        if (controls.isPresent()) r.set("controls",controls.orElseThrow().encode()); else r.putNull("controls");
        if (events.isPresent()) r.set("events",events.orElseThrow().encode()); else r.putNull("events"); return r;
    }
    private static boolean b(ObjectNode r, String k) throws IOException { return CurrentLivingInventoryQuery.bool(r,k); }
    private static JsonNode array(ObjectNode r, String k, int max) throws IOException {
        var value = r.get(k); if (!value.isArray() || value.size() > max) throw new IOException("Bounded AE2 array required"); return value;
    }
    private static void key(String value) {
        Objects.requireNonNull(value); StrictJson.require(value.matches("[A-Za-z0-9_.-]{1,256}"), "Bounded ASCII definition key required");
    }
}
