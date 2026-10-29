package org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendrules;

import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.PublicUnsigned64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesData.*;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesPostconditions;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.LoadedFeaturesData;

/** Original public names and DATA contracts. No value here grants a menu or gameplay lease. */
public final class FrontendRulesContract {
    private FrontendRulesContract() { }
    public enum Method {
        OPEN_RULES("ck3_activate_frontend_game_rules_v1"),
        NEW_GAME("ck3_activate_frontend_new_game_v1"),
        PICK_ANY("ck3_activate_frontend_pick_any_character_v1"),
        PREPARE_RULER("ck3_activate_frontend_prepare_custom_ruler_v1"),
        RULER_DESIGNER("ck3_activate_frontend_ruler_designer_v1"),
        START_1066("ck3_activate_frontend_start_1066_bookmark_character_v1"),
        APPLY_HIDE("ck3_apply_and_hide_frontend_game_rules_v1"),
        HIDE("ck3_hide_frontend_game_rules_v1"),
        TREE("ck3_inspect_frontend_gui_tree_v1"),
        APPLIED_RULES("ck3_query_frontend_applied_game_rules_v1"),
        SELECTIONS("ck3_query_frontend_game_rule_selections_v1"),
        WINDOW("ck3_query_frontend_game_rules_window_v1"),
        ROUTE("ck3_query_frontend_gui_route_v1"),
        LOADED_FEATURES("ck3_query_loaded_feature_manifest_v1"),
        SELECT_RULE("ck3_select_frontend_game_rule_v1");
        private final String publicName;
        Method(String publicName) { this.publicName=publicName; }
        public String publicName() { return publicName; }
        public boolean emptyArguments() { return this!=START_1066 && this!=LOADED_FEATURES && this!=SELECT_RULE; }
    }
    public sealed interface Request permits Empty,Select,Start,Features { Method method(); }
    public record Empty(Method method) implements Request {
        public Empty { Objects.requireNonNull(method);StrictJson.require(method.emptyArguments(),"original method requires named arguments"); }
    }
    public record Select(ScriptKey ruleKey,ScriptKey expectedCurrentSettingKey,ScriptKey desiredSettingKey) implements Request {
        public Select { Objects.requireNonNull(ruleKey);Objects.requireNonNull(expectedCurrentSettingKey);Objects.requireNonNull(desiredSettingKey); }
        @Override public Method method() { return Method.SELECT_RULE; }
    }
    public record Start(String characterNameKey) implements Request {
        public Start { StrictJson.require(List.of("bookmark_rags_to_riches_petty_king_murchad","bookmark_rags_to_riches_duke_robert").contains(characterNameKey),"ordinary exact-build 1066 feudal candidate required"); }
        @Override public Method method() { return Method.START_1066; }
    }
    public record Features(BigInteger expectedRevision) implements Request {
        public Features { PublicUnsigned64.canonical(expectedRevision,PublicUnsigned64.Minimum.ZERO); }
        @Override public Method method() { return Method.LOADED_FEATURES; }
    }

    /** Keeps the actual coordinator receipt and its complete original native token, not a detached DTO. */
    public sealed interface ReadEvidence permits Selections,Window,RouteRead,Tree,FeaturesRead { PlanningReadReceipt receipt(); }
    public record Selections(PlanningReadResult.Known<RuleSelections> actual,boolean appliedInstance) implements ReadEvidence {
        public Selections { Objects.requireNonNull(actual);StrictJson.require(actual.value().appliedSettingsProven()==(appliedInstance&&actual.value().ready()),"selected/applied rule proof domains differ"); }
        @Override public PlanningReadReceipt receipt() { return actual.receipt(); }
    }
    public record Window(PlanningReadResult.Known<RuleWindow> actual) implements ReadEvidence {
        public Window { Objects.requireNonNull(actual); }
        @Override public PlanningReadReceipt receipt() { return actual.receipt(); }
    }
    public record RouteRead(PlanningReadResult.Known<ObservedRoute> actual) implements ReadEvidence {
        public RouteRead { Objects.requireNonNull(actual); }
        @Override public PlanningReadReceipt receipt() { return actual.receipt(); }
    }
    public record Tree(PlanningReadResult.Known<GuiTree> actual) implements ReadEvidence {
        public Tree { Objects.requireNonNull(actual); }
        @Override public PlanningReadReceipt receipt() { return actual.receipt(); }
    }
    public record FeaturesRead(PlanningReadResult.Known<LoadedFeaturesData.Observation> actual,BigInteger expectedRevision) implements ReadEvidence {
        public FeaturesRead { Objects.requireNonNull(actual);PublicUnsigned64.canonical(expectedRevision,PublicUnsigned64.Minimum.ZERO);StrictJson.require(actual.value().revision().equals(expectedRevision),"loaded-feature public revision changed"); }
        @Override public PlanningReadReceipt receipt() { return actual.receipt(); }
    }
    public sealed interface Response permits ReadResponse,Selected,Closed,Opened,Transition,Prepared,Started { Method method(); }
    public record ReadResponse(Method method,ReadEvidence observation) implements Response {
        public ReadResponse {
            Objects.requireNonNull(method);Objects.requireNonNull(observation);
            StrictJson.require(switch(method) {
                case APPLIED_RULES->observation instanceof Selections value&&value.appliedInstance();
                case SELECTIONS->observation instanceof Selections value&&!value.appliedInstance();
                case WINDOW->observation instanceof Window;
                case ROUTE->observation instanceof RouteRead;
                case TREE->observation instanceof Tree;
                case LOADED_FEATURES->observation instanceof FeaturesRead;
                default->false;
            },"public query differs from its actual typed native producer");
        }
    }
    public record Selected(ActionReceipt action,Select request,Selections before,Window windowBefore,RawJson acknowledgement,Selections observation) implements Response {
        public Selected { confirmed(action);Objects.requireNonNull(request);Objects.requireNonNull(before);Objects.requireNonNull(windowBefore);Objects.requireNonNull(acknowledgement);Objects.requireNonNull(observation); }
        @Override public Method method() { return Method.SELECT_RULE; }
    }
    public record Closed(ActionReceipt action,boolean apply,Selections before,RawJson acknowledgement,Window observation) implements Response {
        public Closed { confirmed(action);Objects.requireNonNull(before);Objects.requireNonNull(acknowledgement);Objects.requireNonNull(observation); }
        @Override public Method method() { return apply?Method.APPLY_HIDE:Method.HIDE; }
    }
    public record Opened(Optional<ActionReceipt> action,Selections observation) implements Response {
        public Opened { Objects.requireNonNull(action);action.ifPresent(FrontendRulesContract::confirmed);Objects.requireNonNull(observation);StrictJson.require(observation.actual().value().ready(),"actual opened selections unavailable"); }
        @Override public Method method() { return Method.OPEN_RULES; }
    }
    public record Transition(Method method,ActionReceipt action,RouteRead before,Optional<Tree> beforeInspection,RawJson acknowledgement,RouteRead after) implements Response {
        public Transition { StrictJson.require(List.of(Method.NEW_GAME,Method.PICK_ANY,Method.RULER_DESIGNER).contains(method),"ordinary route transition required");confirmed(action);Objects.requireNonNull(before);Objects.requireNonNull(beforeInspection);Objects.requireNonNull(acknowledgement);Objects.requireNonNull(after); }
    }
    public record Prepared(Transition pickAny,Tree selectionTarget,List<ActionReceipt> selections,List<RawJson> selectionAcknowledgements,Tree lobbyInspection) implements Response {
        public Prepared { Objects.requireNonNull(pickAny);StrictJson.require(pickAny.method()==Method.PICK_ANY,"actual Play Any Ruler transition required");Objects.requireNonNull(selectionTarget);selections=List.copyOf(selections);selectionAcknowledgements=List.copyOf(selectionAcknowledgements);StrictJson.require(!selections.isEmpty()&&selections.size()<=8&&selections.size()==selectionAcknowledgements.size(),"bounded original random-playable submissions required");selections.forEach(FrontendRulesContract::confirmed);Objects.requireNonNull(lobbyInspection); }
        @Override public Method method() { return Method.PREPARE_RULER; }
    }
    /** The Root supplies a real admitted Driver snapshot and actual root-read material; ACK cannot construct these. */
    public record StartMaterial(ActionReceipt action,RawJson afterSnapshot,PlanningReadReceipt campaignRootRead) {
        public StartMaterial { Objects.requireNonNull(action);Objects.requireNonNull(afterSnapshot);Objects.requireNonNull(campaignRootRead);StrictJson.require(action.state() instanceof ActionState.Settled settled&&settled.settlement() instanceof ActionState.GameplayEntered,"full first Driver/SEM/root/pump settlement required");var settled=(ActionState.Settled)action.state();StrictJson.require(((ActionState.GameplayEntered)settled.settlement()).observation().campaignRootRead().equals(campaignRootRead),"Start material is not its actual independent root receipt"); }
    }
    public record Started(Start request,RouteRead before,Optional<RawJson> selectionAcknowledgement,Candidate candidate,RawJson acknowledgement,StartMaterial material) implements Response {
        public Started { Objects.requireNonNull(request);Objects.requireNonNull(before);Objects.requireNonNull(selectionAcknowledgement);Objects.requireNonNull(candidate);Objects.requireNonNull(acknowledgement);Objects.requireNonNull(material);StrictJson.require(candidate.characterNameKey().equals(request.characterNameKey()),"actual selected candidate differs from public request"); }
        @Override public Method method() { return Method.START_1066; }
    }
    public static void confirmed(ActionReceipt receipt) {
        Objects.requireNonNull(receipt);StrictJson.require(receipt.state() instanceof ActionState.Settled settled&&settled.settlement() instanceof ActionState.FrontendApplied,"original frontend action has no verified later observation; reconcile, never resubmit");
    }
}
