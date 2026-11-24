package org.xar.ck3.control.nativebridge;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** Exact fixed entry observation DATA. Public shape never creates a native owner lease. */
public record CurrentLivingEntrySource(Kind kind, long actorFullId, Optional<Manage> manage,
        Optional<View> inventory, Optional<View> detail, boolean sampledTwice) {
    public enum Kind {
        MANAGE("manage"), INVENTORY("inventory"), DETAIL("detail");
        private final String wire;
        Kind(String wire) { this.wire = wire; }
        public String wire() { return wire; }
        public static Kind parse(String value) throws IOException {
            for (var kind : values()) if (kind.wire.equals(value)) return kind;
            throw new IOException("Unknown Living entry Source kind");
        }
    }

    public record DecisionRow(String decisionKey, boolean canOpenDetail, boolean isSelected) {
        public DecisionRow {
            StrictJson.require(CurrentLivingEntry.MANAGE_DECISION.equals(decisionKey), "Exact fixed manage decision required");
        }
        static DecisionRow decode(JsonNode node) throws IOException {
            var r = StrictJson.object(node, Set.of("decision_key", "can_open_detail", "is_selected"));
            return new DecisionRow(NativeWire.text(r.get("decision_key")), CurrentLivingInventoryQuery.bool(r, "can_open_detail"),
                    CurrentLivingInventoryQuery.bool(r, "is_selected"));
        }
        ObjectNode encode() {
            return StrictJson.object().put("decision_key", decisionKey).put("can_open_detail", canOpenDetail).put("is_selected", isSelected);
        }
    }

    public record Manage(boolean listFound, boolean listVisible, boolean listEnabled,
            boolean detailFound, boolean detailVisible, boolean detailEnabled, Optional<Integer> groupsCount,
            Optional<Integer> totalModelRows, boolean completeModelCensus, boolean blockedByVisibleModal,
            boolean otherDecisionSelected, Optional<String> selectedDecisionKey, Optional<Integer> widgetState,
            Optional<Boolean> nativeCanConfirm, boolean confirmAdmissible, boolean openListAdmissible,
            List<DecisionRow> rows, boolean ownerBound, Optional<String> confirmTooltip, boolean confirmTooltipObserved) {
        public Manage {
            Objects.requireNonNull(groupsCount); Objects.requireNonNull(totalModelRows); Objects.requireNonNull(selectedDecisionKey);
            Objects.requireNonNull(widgetState); Objects.requireNonNull(nativeCanConfirm); Objects.requireNonNull(confirmTooltip);
            rows = List.copyOf(rows);
            StrictJson.require(ownerBound && rows.size() <= 1, "Actual bound manage owner and at most one fixed row required");
            StrictJson.require(!listVisible || listFound, "Visible list must be observed found");
            StrictJson.require(!detailVisible || detailFound, "Visible detail must be observed found");
            if (completeModelCensus) StrictJson.require(listFound && groupsCount.isPresent() && totalModelRows.isPresent(),
                    "Complete actual model requires actual nullable counts");
            groupsCount.ifPresent(n -> StrictJson.require(n >= 0 && n <= 64, "Actual groups count outside bound"));
            totalModelRows.ifPresent(n -> StrictJson.require(n >= 0 && n <= 1024, "Actual model count outside bound"));
            selectedDecisionKey.ifPresent(k -> StrictJson.require(k.equals(CurrentLivingEntry.MANAGE_DECISION), "Wrong selected decision"));
            widgetState.ifPresent(n -> StrictJson.require(n >= 0 && n <= 1, "Actual widget state outside bound"));
            if (nativeCanConfirm.isPresent()) StrictJson.require(detailVisible && selectedDecisionKey.isPresent(),
                    "Observed nativeCan, including false, needs actual visible selected detail");
            StrictJson.require(confirmTooltipObserved == confirmTooltip.isPresent(), "Tooltip observed/null differs");
            confirmTooltip.ifPresent(t -> {
                StrictJson.require(detailVisible && selectedDecisionKey.isPresent(), "Actual tooltip needs selected detail");
                CurrentLivingEntry.requireActualText(t);
            });
            if (openListAdmissible) StrictJson.require(!listVisible && !detailVisible && !blockedByVisibleModal,
                    "Open-list necessary actual hidden/modal conditions differ");
            if (confirmAdmissible) StrictJson.require(detailVisible && detailEnabled && selectedDecisionKey.isPresent()
                    && completeModelCensus && nativeCanConfirm.orElse(false) && !blockedByVisibleModal,
                    "Confirm necessary actual Source conditions differ");
            for (var row : rows) {
                if (row.canOpenDetail()) StrictJson.require(completeModelCensus && listVisible && listEnabled
                        && !row.isSelected() && !blockedByVisibleModal, "Fixed row open requires actual complete visible model");
                if (row.isSelected()) StrictJson.require(detailVisible && selectedDecisionKey.isPresent(), "Selected fixed row lacks actual detail");
            }
        }
        static Manage decode(JsonNode node) throws IOException {
            var r = StrictJson.object(node, Set.of("list_found", "list_visible", "list_enabled", "detail_found", "detail_visible",
                    "detail_enabled", "groups_count", "total_model_rows", "complete_model_census", "blocked_by_visible_modal",
                    "other_decision_selected", "selected_decision_key", "widget_state", "native_can_confirm", "confirm_admissible",
                    "open_list_admissible", "rows", "owner_bound", "confirm_tooltip", "confirm_tooltip_observed"));
            var rows = new ArrayList<DecisionRow>(); var array = r.get("rows");
            if (!array.isArray() || array.size() > 1) throw new IOException("At most one actual fixed decision row required");
            for (var n : array) rows.add(DecisionRow.decode(n));
            return new Manage(b(r,"list_found"), b(r,"list_visible"), b(r,"list_enabled"), b(r,"detail_found"), b(r,"detail_visible"),
                    b(r,"detail_enabled"), optionalInt(r.get("groups_count")), optionalInt(r.get("total_model_rows")),
                    b(r,"complete_model_census"), b(r,"blocked_by_visible_modal"), b(r,"other_decision_selected"),
                    optionalText(r.get("selected_decision_key")), optionalInt(r.get("widget_state")), optionalBoolean(r.get("native_can_confirm")),
                    b(r,"confirm_admissible"), b(r,"open_list_admissible"), rows, b(r,"owner_bound"),
                    optionalText(r.get("confirm_tooltip")), b(r,"confirm_tooltip_observed"));
        }
        ObjectNode encode() {
            var r = StrictJson.object().put("list_found",listFound).put("list_visible",listVisible).put("list_enabled",listEnabled)
                    .put("detail_found",detailFound).put("detail_visible",detailVisible).put("detail_enabled",detailEnabled)
                    .put("complete_model_census",completeModelCensus).put("blocked_by_visible_modal",blockedByVisibleModal)
                    .put("other_decision_selected",otherDecisionSelected).put("confirm_admissible",confirmAdmissible)
                    .put("open_list_admissible",openListAdmissible).put("owner_bound",ownerBound).put("confirm_tooltip_observed",confirmTooltipObserved);
            putInt(r,"groups_count",groupsCount); putInt(r,"total_model_rows",totalModelRows); putInt(r,"widget_state",widgetState);
            putText(r,"selected_decision_key",selectedDecisionKey); putText(r,"confirm_tooltip",confirmTooltip);
            if (nativeCanConfirm.isPresent()) r.put("native_can_confirm",nativeCanConfirm.orElseThrow()); else r.putNull("native_can_confirm");
            var array = r.putArray("rows"); for (var row : rows) array.add(row.encode()); return r;
        }
    }

    public record View(long expectedPayloadFullId, boolean windowFound, boolean visible, boolean enabled,
            boolean payloadBound, boolean blockedByVisibleModal, boolean openAdmissible) {
        public View {
            CurrentLivingInventoryQuery.requireFullId(expectedPayloadFullId);
            StrictJson.require(!visible || windowFound, "Visible view requires actual found window");
            StrictJson.require(!payloadBound || windowFound, "Bound payload requires actual found window");
            if (openAdmissible) StrictJson.require(!visible && !blockedByVisibleModal,
                    "Open requires actual not-visible and no unrelated visible modal");
        }
        static View decode(JsonNode node) throws IOException {
            var r = StrictJson.object(node, Set.of("expected_payload_full_id", "window_found", "visible", "enabled", "payload_bound",
                    "blocked_by_visible_modal", "open_admissible"));
            return new View(CurrentLivingInventoryQuery.fullId(r.get("expected_payload_full_id")), b(r,"window_found"), b(r,"visible"),
                    b(r,"enabled"), b(r,"payload_bound"), b(r,"blocked_by_visible_modal"), b(r,"open_admissible"));
        }
        ObjectNode encode() {
            return StrictJson.object().put("expected_payload_full_id",expectedPayloadFullId).put("window_found",windowFound)
                    .put("visible",visible).put("enabled",enabled).put("payload_bound",payloadBound)
                    .put("blocked_by_visible_modal",blockedByVisibleModal).put("open_admissible",openAdmissible);
        }
    }

    public CurrentLivingEntrySource {
        Objects.requireNonNull(kind); Objects.requireNonNull(manage); Objects.requireNonNull(inventory); Objects.requireNonNull(detail);
        CurrentLivingInventoryQuery.requireFullId(actorFullId);
        StrictJson.require(sampledTwice && (manage.isPresent()?1:0)+(inventory.isPresent()?1:0)+(detail.isPresent()?1:0)==1,
                "Exactly one double-sampled entry Source branch required");
        StrictJson.require(kind==Kind.MANAGE?manage.isPresent():kind==Kind.INVENTORY?inventory.isPresent():detail.isPresent(),
                "Entry Source kind/union differs");
        inventory.ifPresent(v -> StrictJson.require(v.expectedPayloadFullId()==actorFullId, "Actual inventory payload differs from current actor"));
    }

    /** Necessary public-shape predicate only; it does not mint an action or a Native lease. */
    public boolean actionAdmissible(CurrentLivingEntry.Action action) {
        if (kind != action.sourceKind()) return false;
        if (action.queryOnly()) return true;
        return switch(action) {
            case OPEN_INVENTORY -> inventory.orElseThrow().openAdmissible();
            case OPEN_DETAIL -> detail.orElseThrow().openAdmissible();
            case OPEN_MANAGE_LIST -> manage.orElseThrow().ownerBound() && manage.orElseThrow().openListAdmissible();
            case OPEN_MANAGE_DETAIL -> manage.orElseThrow().ownerBound() && manage.orElseThrow().rows().size()==1
                    && manage.orElseThrow().rows().get(0).canOpenDetail();
            case CONFIRM_MANAGE -> manage.orElseThrow().ownerBound() && manage.orElseThrow().confirmAdmissible()
                    && manage.orElseThrow().nativeCanConfirm().orElse(false);
            default -> false;
        };
    }

    public static CurrentLivingEntrySource decode(JsonNode node) throws IOException {
        try {
            var r = StrictJson.object(node, Set.of("schema","kind","actor_full_id","manage","inventory","detail","sampled_twice"));
            CurrentLivingInventoryQuery.identity(r,"schema",CurrentLivingEntry.SOURCE_SCHEMA);
            return new CurrentLivingEntrySource(Kind.parse(NativeWire.text(r.get("kind"))), CurrentLivingInventoryQuery.fullId(r.get("actor_full_id")),
                    r.get("manage").isNull()?Optional.empty():Optional.of(Manage.decode(r.get("manage"))),
                    r.get("inventory").isNull()?Optional.empty():Optional.of(View.decode(r.get("inventory"))),
                    r.get("detail").isNull()?Optional.empty():Optional.of(View.decode(r.get("detail"))), b(r,"sampled_twice"));
        } catch (IllegalArgumentException | ArithmeticException invalid) { throw new IOException("Invalid exact Living entry Source DATA",invalid); }
    }

    public ObjectNode encode() {
        var r = StrictJson.object().put("schema",CurrentLivingEntry.SOURCE_SCHEMA).put("kind",kind.wire())
                .put("actor_full_id",actorFullId).put("sampled_twice",sampledTwice);
        if(manage.isPresent())r.set("manage",manage.orElseThrow().encode());else r.putNull("manage");
        if(inventory.isPresent())r.set("inventory",inventory.orElseThrow().encode());else r.putNull("inventory");
        if(detail.isPresent())r.set("detail",detail.orElseThrow().encode());else r.putNull("detail");return r;
    }

    private static boolean b(ObjectNode r,String k)throws IOException{return CurrentLivingInventoryQuery.bool(r,k);}
    private static Optional<Integer> optionalInt(JsonNode n)throws IOException{return n.isNull()?Optional.empty():Optional.of(CurrentLivingInventoryQuery.i32(n));}
    private static Optional<Boolean> optionalBoolean(JsonNode n)throws IOException {
        if(n.isNull())return Optional.empty();if(!n.isBoolean())throw new IOException("Nullable actual bool required");return Optional.of(n.booleanValue());
    }
    private static Optional<String> optionalText(JsonNode n)throws IOException{return n.isNull()?Optional.empty():Optional.of(CurrentLivingEntry.actualText(n));}
    private static void putInt(ObjectNode n,String k,Optional<Integer> v){if(v.isPresent())n.put(k,v.orElseThrow());else n.putNull(k);}
    private static void putText(ObjectNode n,String k,Optional<String> v){if(v.isPresent())n.put(k,v.orElseThrow());else n.putNull(k);}
}
