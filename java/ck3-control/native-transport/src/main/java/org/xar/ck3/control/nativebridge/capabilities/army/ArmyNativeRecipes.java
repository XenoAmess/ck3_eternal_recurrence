package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.stream.Collectors;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.action.ReadContract;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyCalls.*;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyCalls.Frame;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;

/** Exact original Native wire recipes. A recipe does not register a route, grant a permit, or verify a game effect. */
public final class ArmyNativeRecipes {
    private ArmyNativeRecipes() { }
    public enum Effect { READ_ONLY, WORLD_MUTATION, RESEARCH_CONTROL }
    public enum LocalKind { WAR_STATE_FROM_CURRENT_SNAPSHOT, COLLECT_ORIGINAL_DECLARATION_RESULT }
    public enum CompositeKind { PREVIEW_ACTIVE_RETREAT, ORDER_ACTIVE_RETREAT }
    public sealed interface Recipe permits Primitive, Local, Composite, Disabled { }
    public record Primitive(PublicMethod method, NativeRequest request, ReadContract.WireProfile wire,
            Effect effect, String permissionKey) implements Recipe {
        public Primitive { Objects.requireNonNull(method); Objects.requireNonNull(request); Objects.requireNonNull(wire); Objects.requireNonNull(effect); text(permissionKey); }
    }
    public record Local(LocalKind kind, Call original) implements Recipe { public Local { Objects.requireNonNull(kind); Objects.requireNonNull(original); } }
    public record Composite(CompositeKind kind, Call original) implements Recipe { public Composite { Objects.requireNonNull(kind); Objects.requireNonNull(original); } }
    /** The original production crash guard remains visible; this case is never converted to a Native request. */
    public record Disabled(PublicMethod method, String reason) implements Recipe { public Disabled { Objects.requireNonNull(method); text(reason); } }
    public sealed interface SelectedFacts permits NoFacts, AllyQuote, DeclarationFacts { }
    public record NoFacts() implements SelectedFacts { }
    /** Supplied only after the family observer has checked final CanSend, selected pair, quote and same frame. */
    public record AllyQuote(ArmyTypes.Context context, FullId war, FullId recipient, List<Long> tenCosts, ExactRef familyRead) implements SelectedFacts {
        public AllyQuote { Objects.requireNonNull(context); Objects.requireNonNull(war); Objects.requireNonNull(recipient); tenCosts = List.copyOf(tenCosts);
            need(tenCosts.size() == 10, "exact ten native send-cost slots required"); Objects.requireNonNull(familyRead); need(familyRead.bytes() > 0, "actual family observation required"); }
    }
    /** The root's current declaration observation supplies the complete ordered tuple, never caller-authored JSON. */
    public record DeclarationFacts(ArmyTypes.Context context, String declarationId, int target, int cbIndex,
            String cbKey, int configuration, int claimant, List<Integer> titles, ExactRef declarationRead) implements SelectedFacts {
        public DeclarationFacts { Objects.requireNonNull(context); text(declarationId); text(cbKey); titles = List.copyOf(titles);
            need(target >= 0 && cbIndex >= 0 && configuration >= -1 && claimant >= -1 && titles.stream().allMatch(v -> v >= 0), "exact declaration tuple required");
            need(declarationId.equals(target + "-" + cbIndex + "-" + configuration), "selected declaration ID differs from its native tuple");
            Objects.requireNonNull(declarationRead); need(declarationRead.bytes() > 0, "actual declaration observation required"); }
    }
    public static Recipe prepare(Call call, ArmyTypes.Context context, SelectedFacts selected, boolean scopedStrengthExport) {
        Objects.requireNonNull(call); Objects.requireNonNull(context); Objects.requireNonNull(selected);
        call.revision().requireCurrent(context.before().frame().revision());
        if (call instanceof Empty) return new Local(LocalKind.WAR_STATE_FROM_CURRENT_SNAPSHOT, call);
        if (call instanceof Collect) return new Local(LocalKind.COLLECT_ORIGINAL_DECLARATION_RESULT, call);
        if (call instanceof RetreatPreview) return new Composite(CompositeKind.PREVIEW_ACTIVE_RETREAT, call);
        if (call instanceof RetreatOrder) return new Composite(CompositeKind.ORDER_ACTIVE_RETREAT, call);
        if (call.method() == PublicMethod.QUERY_WAR_TERMINATION_EXIT_TERMS)
            return new Disabled(call.method(), "war-termination exit-terms v2 is disabled after a reproducible native loaded-effect preview crash");
        String step; String capability; String permission; Effect effect = Effect.READ_ONLY;
        ReadContract.WireProfile wire = ReadContract.WireProfile.EXECUTE_STEP; ObjectNode fields = empty();
        switch (call) {
            case Frame c -> {
                step = switch (c.method()) {
                    case QUERY_WAR_DECLARED_OVERVIEW_V1 -> "query-war-declared-overview-v1";
                    case CLOSE_WAR_DECLARED_OVERVIEW_V1 -> "close-war-declared-overview-v1";
                    case QUERY_WAR_RESULTS_WINDOW_V1 -> "query-war-results-window-v1";
                    case CLOSE_WAR_RESULTS_WINDOW_V1 -> "close-war-results-window-v1";
                    case QUERY_DECLARABLE_WARS -> "query-declarable-wars";
                    case RAISE_TROOPS_DEFAULT -> "raise-troops-default";
                    case QUERY_PLAYER_DEFAULT_RAISE_V1 -> "query-player-default-raise-v1";
                    case QUERY_PLAYER_MERCENARY_CONTEXT_V1 -> "query-player-mercenary-context-v1";
                    case QUERY_ARMY_GATHERING_RESEARCH_SAMPLING_V1 -> "query-army-gathering-research-sampling-v1";
                    default -> throw new IllegalArgumentException("wrong fixed-frame Army method"); };
                effect = switch (c.method()) { case CLOSE_WAR_DECLARED_OVERVIEW_V1, CLOSE_WAR_RESULTS_WINDOW_V1, RAISE_TROOPS_DEFAULT -> Effect.WORLD_MUTATION; default -> Effect.READ_ONLY; };
                capability = c.method() == PublicMethod.QUERY_ARMY_GATHERING_RESEARCH_SAMPLING_V1 ? "game.command.query-army-strengths-v1" : "game.command." + step;
                permission = capability;
            }
            case War c -> {
                String prefix = switch (c.method()) {
                    case ENFORCE_DEMANDS -> "enforce-demands-";
                    case QUERY_WAR_OCCUPATION_TARGETS_V1 -> "query-war-occupation-targets-v1-";
                    case QUERY_WAR_TERMINATION_OPTIONS -> "query-war-termination-options-";
                    case QUERY_OUTBOUND_WAR_WHITE_PEACE_STATUS -> "query-outbound-war-white-peace-status-v1-";
                    case QUERY_WAR_TERMINATION_TERMS -> "query-war-termination-terms-v1-";
                    case SURRENDER_WAR -> "surrender-war-";
                    case OFFER_WHITE_PEACE -> "offer-white-peace-";
                    default -> throw new IllegalArgumentException("production-disabled query has no Native recipe"); };
                step = prefix + c.warId(); capability = "game.command." + prefix + "N"; permission = capability;
                if (c.method() == PublicMethod.ENFORCE_DEMANDS || c.method() == PublicMethod.SURRENDER_WAR || c.method() == PublicMethod.OFFER_WHITE_PEACE) effect = Effect.WORLD_MUTATION;
            }
            case Unit c -> {
                String prefix = switch (c.method()) { case DISBAND_ARMY -> "disband-army-"; case QUERY_BATTLE_CONTROL_SNAPSHOT_V1 -> "query-battle-control-snapshot-v1-"; case QUERY_BATTLE_REINFORCEMENT_ASSIGNMENT_V1 -> "query-battle-reinforcement-assignment-v1-"; default -> throw new IllegalArgumentException("wrong CUnit method"); };
                step = prefix + c.army().value(); capability = "game.command." + prefix + "N"; permission = capability;
                if (c.method() == PublicMethod.DISBAND_ARMY) effect = Effect.WORLD_MUTATION;
            }
            case Siege c -> { String prefix = c.method() == PublicMethod.START_ASSAULT ? "start-assault-" : "stop-assault-";
                step = prefix + c.siege().value(); capability = "game.command." + prefix + "N"; permission = capability; effect = Effect.WORLD_MUTATION; }
            case Declaration c -> {
                if (c.method() == PublicMethod.DECLARE_WAR) { step = "declare-war-" + c.declarationId(); capability = "game.command.declare-war-N"; permission = capability; effect = Effect.WORLD_MUTATION; }
                else {
                    need(selected instanceof DeclarationFacts, "query requires the complete current selected-declaration observation"); DeclarationFacts f = (DeclarationFacts) selected;
                    need(f.context().equals(context) && f.declarationId().equals(c.declarationId()), "selected declaration belongs to a different actual frame/tuple");
                    fields.put("expected_public_revision", context.before().frame().revision()).put("declaration_id", c.declarationId());
                    ObjectNode tuple = declaration(f);
                    if (c.method() == PublicMethod.QUERY_PLAYER_ORDINARY_HOLY_WAR_DECLARATION_CONTEXT_PRIVATE_V1) {
                        step = "query-player-ordinary-holy-war-declaration-context-v1"; capability = null; permission = "allow_private_player_ordinary_holy_war_declaration_context_query";
                        fields.setAll(tuple); wire = ReadContract.WireProfile.G2_PRIVATE_QUERY;
                    } else { boolean v2 = c.method() == PublicMethod.QUERY_PREWAR_FORCE_COALITION_COVERAGE_V2;
                        step = "query-prewar-force-coalition-coverage-v" + (v2 ? "2" : "1"); capability = v2 ? "game.command.query-prewar-force-coalition-coverage-v2-N" : null;
                        permission = v2 ? capability : "allow_private_prewar_force_coalition_query"; fields.set("selected_declaration", tuple); }
                }
            }
            case Truce c -> { step = "query-raiktor-actual-truce-expiry-v1-" + c.toward().value(); capability = "game.command.query-raiktor-actual-truce-expiry-v1-N"; permission = capability; }
            case CallAlly c -> {
                need(selected instanceof AllyQuote, "call ally must first observe the complete selected family terms"); AllyQuote q = (AllyQuote) selected;
                need(q.context().equals(context) && q.war().equals(c.war()) && q.recipient().equals(c.recipient())
                        && !BigInteger.valueOf(c.recipient().value()).equals(context.playerId()), "call ally quote crossed its paused player/pair");
                step = "submit-call-ally-to-war-v1-private"; capability = null; permission = "allow_private_family_obligations_query"; effect = Effect.WORLD_MUTATION;
                fields.put("war_id", c.war().value()).put("recipient_character_id", c.recipient().value()); var a = fields.putArray("expected_send_cost_raw"); q.tenCosts().forEach(a::add);
            }
            case CreateMaa c -> { step = "maa-regular-personal-create-private-v1"; capability = null; permission = "regular_maa_create_private_source"; effect = Effect.WORLD_MUTATION;
                fields = actionBound(context); fields.put("type_index", c.typeIndex()).put("action_id", c.actionId()); }
            case Move c -> { step = "move-army-" + c.army().value() + "-to-" + c.target().value(); capability = "game.command.move-army-N-to-N"; permission = capability; effect = Effect.WORLD_MUTATION; }
            case Hire c -> { boolean holy = c.method() == PublicMethod.HIRE_HOLY_ORDER_V1; step = holy ? "hire-holy-order-v1" : "hire-mercenary-v1"; capability = "game.command." + step; permission = capability;
                fields.put(holy ? "holy_order_id" : "company_id", c.id().value()); effect = Effect.WORLD_MUTATION; }
            case Commander c -> { step = "query-army-commander-candidates-v1-for-army-" + c.army().value(); capability = "game.command.query-army-commander-candidates-v1-for-army-N";
                if (c.target() instanceof Present<PositiveId> p) { step += "-at-province-" + p.value().value(); capability += "-at-province-P"; } permission = capability; }
            case AssignCommander c -> { step = "assign-army-commander-v1-army-" + c.army().value() + "-to-character-" + c.character().value(); capability = "game.command.assign-army-commander-v1-army-N-to-character-N"; permission = capability; effect = Effect.WORLD_MUTATION; }
            case Sampling c -> { step = (c.enabled() ? "enable-" : "disable-") + "army-gathering-research-sampling-v1"; capability = "game.command.query-army-strengths-v1"; permission = capability; effect = Effect.RESEARCH_CONTROL; }
            case Strengths c -> { step = "query-army-strengths-v1"; capability = "game.command.query-army-strengths-v1"; permission = capability;
                fields.put("army_strengths_profile", c.effectiveProfile().wire()); if (scopedStrengthExport) { var a = fields.putArray("army_ids"); c.armies().forEach(v -> a.add(v.value())); } }
            case Terminal c -> { step = "query-battle-terminal-transition-v1-";
                if (c.combat() instanceof Present<FullId> combat && c.subject() instanceof Present<PublicUnitId> subject)
                    step += combat.value().value() + "-" + subject.value().value() + "-" + (c.afterSequence() instanceof Present<UInt64> p ? p.value().decimal() : "0");
                else step += "none";
                if (!c.effectiveCharacters().isEmpty()) step += ":characters:" + c.effectiveCharacters().stream().map(v -> Integer.toString(v.value())).collect(Collectors.joining(","));
                capability = "game.command.query-battle-terminal-transition-v1-N"; permission = capability; }
            case Combat c -> { step = c.selection().toStep(); if (c.method() == PublicMethod.QUERY_COMBAT_SIMULATION_INPUTS_V3) step = step.replace("query-combat-simulation-inputs-v2-", "query-combat-simulation-inputs-v3-");
                capability = c.method() == PublicMethod.QUERY_COMBAT_SIMULATION_INPUTS_V3 ? "game.command.query-combat-simulation-inputs-v3-N" : "game.command.query-combat-simulation-inputs-v2-N"; permission = capability; }
            case CombatId c -> { String prefix = c.method() == PublicMethod.QUERY_BATTLE_TRANSITION_V1 ? "query-battle-transition-v1-" : "query-combat-phase-event-trace-v1-";
                step = prefix + c.combat().value(); capability = "game.command." + prefix + "N"; permission = capability; }
            case WarEntry c -> { step = "query-war-entry-assessments-v1-1-" + c.targets().get(0).value(); capability = "game.command.query-war-entry-assessments-v1-N"; permission = capability; }
            case Knight c -> { ArmyRequests.Knight q = c.selection();
                need(q.nativeRevision().value().equals(context.nativeRevision()) && q.snapshotId().equals(context.before().frame().snapshotId()) && BigInteger.valueOf(q.dateRaw()).equals(context.dateRaw())
                        && BigInteger.valueOf(q.player().value()).equals(context.playerId()), "current-knight public/native/player/date binding differs from actual frame");
                step = "query-current-battle-knight-v1-" + q.subject().value() + "-" + q.character().value() + "-" + q.regiment().value(); capability = "game.command.query-current-battle-knight-v1-N-N-N"; permission = capability;
                fields.put("expected_native_revision", q.nativeRevision().value()).put("expected_snapshot_id", q.snapshotId()).put("expected_played_character_id", q.player().value()).put("expected_war_id", q.war()).put("expected_native_carmy_id", q.nativeArmy().value()).put("expected_combat_id", q.combat().value()).put("expected_province_id", q.province().value()).put("expected_date_raw", q.dateRaw()); }
            case Empty ignored -> throw new IllegalStateException("local operation must not reach Native preparation");
            case Collect ignored -> throw new IllegalStateException("collection must not allocate a second Native request");
            case RetreatPreview ignored -> throw new IllegalStateException("retreat preview is a composition, not a DLL step");
            case RetreatOrder ignored -> throw new IllegalStateException("retreat order is a composition, not a DLL step");
        }
        return new Primitive(call.method(), new NativeRequest(step, Optional.ofNullable(capability), new RawJson(bytes(fields))), wire, effect, permission);
    }
    private static ObjectNode actionBound(ArmyTypes.Context c) { return empty().put("expected_snapshot_revision", c.nativeRevision()).put("expected_public_revision", c.before().frame().revision()).put("expected_date_raw", c.dateRaw()).put("expected_player_character_id", c.playerId()); }
    private static ObjectNode declaration(DeclarationFacts f) { ObjectNode n = empty().put("target_character_id", f.target()).put("casus_belli_index", f.cbIndex()).put("casus_belli_key", f.cbKey()).put("configuration_index", f.configuration()).put("claimant_character_id", f.claimant()); var a = n.putArray("target_title_ids"); f.titles().forEach(a::add); return n; }
}
