package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.capabilities.army.*;
import org.xar.ck3.control.nativebridge.capabilities.registry.*;

/** Core-lifetime typed handlers resolve the actual Root session again on every call, including after restore. */
public final class RootCurrentArmyPublicServices {
    private final RootSessionAccess sessions;private final RootRuntimeCatalogFactory catalogs;
    public RootCurrentArmyPublicServices(RootApplicationAssembly.Core actualCore,RootRuntimeCatalogFactory catalogs){this(Objects.requireNonNull(actualCore).sessionAccess(),catalogs);}
    RootCurrentArmyPublicServices(RootSessionAccess actualSessions,RootRuntimeCatalogFactory catalogs){sessions=Objects.requireNonNull(actualSessions);this.catalogs=Objects.requireNonNull(catalogs);}
    private ArmyRuntimeInstaller.Installed current(){try{var owner=sessions.current();return catalogs.requireCurrentCatalog(owner.identity()).army().products();}catch(IOException failure){throw new UncheckedIOException(failure);}}
    private ArmyAdditionalReadService additional(){try{var owner=sessions.current();return catalogs.requireCurrentCatalog(owner.identity()).additionalArmy().service();}catch(IOException failure){throw new UncheckedIOException(failure);}}
    public ArmyClosedReadService.Reply query_player_default_raise_v1(ArmyCalls.Frame input){return current().closedReads().query_player_default_raise_v1(input);}
    public ArmyClosedReadService.Reply query_player_truce_expiry_v1(ArmyCalls.Truce input){return current().closedReads().query_player_truce_expiry_v1(input);}
    public ArmyClosedReadService.Reply query_army_gathering_research_sampling_v1(ArmyCalls.Frame input){return current().closedReads().query_army_gathering_research_sampling_v1(input);}
    public ArmyBattleReadService.Reply query_battle_control_snapshot_v1(ArmyCalls.Unit input){return current().battleReads().query_battle_control_snapshot_v1(input);}
    public ArmyBattleReadService.Reply query_battle_transition_v1(ArmyCalls.CombatId input){return current().battleReads().query_battle_transition_v1(input);}
    public ArmyBattleReadService.Reply query_battle_terminal_transition_v1(ArmyCalls.Terminal input){return current().battleReads().query_battle_terminal_transition_v1(input);}
    public ArmyRetreatService.PreviewReply preview_active_combat_retreat_v1(ArmyCalls.RetreatPreview input)throws InterruptedException{return current().retreatReads().preview_active_combat_retreat_v1(input);}
    public ArmyRetreatOrderService.Reply order_active_combat_retreat_v1(ArmyCalls.RetreatOrder input)throws InterruptedException{return current().retreatOrders().order_active_combat_retreat_v1(input);}
    public ArmyWindowService.Reply query_war_declared_overview_v1(ArmyCalls.Frame input){return current().windows().query_war_declared_overview_v1(input);}
    public ArmyWindowService.Reply query_war_results_window_v1(ArmyCalls.Frame input){return current().windows().query_war_results_window_v1(input);}
    public ArmyAdditionalReadService.Reply query_player_mercenary_context_v1(ArmyCalls.Frame input){return additional().query_player_mercenary_context_v1(input);}
    public ArmyAdditionalReadService.Reply query_army_commander_candidates_v1(ArmyCalls.Commander input){return additional().query_army_commander_candidates_v1(input);}
    public ArmyAdditionalReadService.Reply query_battle_reinforcement_assignment_v1(ArmyCalls.Unit input){return additional().query_battle_reinforcement_assignment_v1(input);}
    public List<PublicBindings.BoundBinding> install(PublicBindings bindings,ExactRef actualAdapterSource) {
        return List.of(
            binding(bindings,PublicMethod.QUERY_PLAYER_DEFAULT_RAISE_V1,ArmyCalls.Frame.class,ArmyClosedReadService.Reply.class,this::query_player_default_raise_v1,a->frame(PublicMethod.QUERY_PLAYER_DEFAULT_RAISE_V1,a),ArmyClosedReadService::encode,actualAdapterSource),
            binding(bindings,PublicMethod.QUERY_PLAYER_TRUCE_EXPIRY_V1,ArmyCalls.Truce.class,ArmyClosedReadService.Reply.class,this::query_player_truce_expiry_v1,a->truce(PublicMethod.QUERY_PLAYER_TRUCE_EXPIRY_V1,a),ArmyClosedReadService::encode,actualAdapterSource),
            binding(bindings,PublicMethod.QUERY_ARMY_GATHERING_RESEARCH_SAMPLING_V1,ArmyCalls.Frame.class,ArmyClosedReadService.Reply.class,this::query_army_gathering_research_sampling_v1,a->frame(PublicMethod.QUERY_ARMY_GATHERING_RESEARCH_SAMPLING_V1,a),ArmyClosedReadService::encode,actualAdapterSource),
            binding(bindings,PublicMethod.QUERY_BATTLE_CONTROL_SNAPSHOT_V1,ArmyCalls.Unit.class,ArmyBattleReadService.Reply.class,this::query_battle_control_snapshot_v1,a->unit(PublicMethod.QUERY_BATTLE_CONTROL_SNAPSHOT_V1,a),ArmyBattleReadService::encode,actualAdapterSource),
            binding(bindings,PublicMethod.QUERY_BATTLE_TRANSITION_V1,ArmyCalls.CombatId.class,ArmyBattleReadService.Reply.class,this::query_battle_transition_v1,a->combat(PublicMethod.QUERY_BATTLE_TRANSITION_V1,a),ArmyBattleReadService::encode,actualAdapterSource),
            binding(bindings,PublicMethod.QUERY_BATTLE_TERMINAL_TRANSITION_V1,ArmyCalls.Terminal.class,ArmyBattleReadService.Reply.class,this::query_battle_terminal_transition_v1,a->terminal(PublicMethod.QUERY_BATTLE_TERMINAL_TRANSITION_V1,a),ArmyBattleReadService::encode,actualAdapterSource),
            binding(bindings,PublicMethod.PREVIEW_ACTIVE_COMBAT_RETREAT_V1,ArmyCalls.RetreatPreview.class,ArmyRetreatService.PreviewReply.class,this::preview_active_combat_retreat_v1,a->preview(PublicMethod.PREVIEW_ACTIVE_COMBAT_RETREAT_V1,a),ArmyRetreatService::encode,actualAdapterSource),
            binding(bindings,PublicMethod.ORDER_ACTIVE_COMBAT_RETREAT_V1,ArmyCalls.RetreatOrder.class,ArmyRetreatOrderService.Reply.class,this::order_active_combat_retreat_v1,a->order(PublicMethod.ORDER_ACTIVE_COMBAT_RETREAT_V1,a),ArmyRetreatOrderService::encode,actualAdapterSource),
            binding(bindings,PublicMethod.QUERY_WAR_DECLARED_OVERVIEW_V1,ArmyCalls.Frame.class,ArmyWindowService.Reply.class,this::query_war_declared_overview_v1,a->frame(PublicMethod.QUERY_WAR_DECLARED_OVERVIEW_V1,a),ArmyWindowService::encode,actualAdapterSource),
            binding(bindings,PublicMethod.QUERY_WAR_RESULTS_WINDOW_V1,ArmyCalls.Frame.class,ArmyWindowService.Reply.class,this::query_war_results_window_v1,a->frame(PublicMethod.QUERY_WAR_RESULTS_WINDOW_V1,a),ArmyWindowService::encode,actualAdapterSource),
            binding(bindings,PublicMethod.QUERY_PLAYER_MERCENARY_CONTEXT_V1,ArmyCalls.Frame.class,ArmyAdditionalReadService.Reply.class,this::query_player_mercenary_context_v1,a->frame(PublicMethod.QUERY_PLAYER_MERCENARY_CONTEXT_V1,a),ArmyAdditionalReadService::encode,actualAdapterSource),
            binding(bindings,PublicMethod.QUERY_ARMY_COMMANDER_CANDIDATES_V1,ArmyCalls.Commander.class,ArmyAdditionalReadService.Reply.class,this::query_army_commander_candidates_v1,a->commander(PublicMethod.QUERY_ARMY_COMMANDER_CANDIDATES_V1,a),ArmyAdditionalReadService::encode,actualAdapterSource),
            binding(bindings,PublicMethod.QUERY_BATTLE_REINFORCEMENT_ASSIGNMENT_V1,ArmyCalls.Unit.class,ArmyAdditionalReadService.Reply.class,this::query_battle_reinforcement_assignment_v1,a->unit(PublicMethod.QUERY_BATTLE_REINFORCEMENT_ASSIGNMENT_V1,a),ArmyAdditionalReadService::encode,actualAdapterSource));
    }
    private static <Q,R> PublicBindings.TypedBinding<Q,R> binding(PublicBindings bindings,PublicMethod method,Class<Q> input,Class<R> output,PublicRoutes.Handler<Q,R> handler,
            PublicBindings.Decoder<Q> decode,PublicBindings.Encoder<R> encode,ExactRef source) {
        return bindings.register(method,input,output,handler,decode,encode,new PublicRoutes.Target(RootCurrentArmyPublicServices.class.getName(),method.pythonName(),source),PublicRoutes.Status.IMPLEMENTED,"typed actual-current Root catalog lookup on each call; no retained old-Game service");
    }
    private static RawJson value(PublicBindings.Arguments args){if(args instanceof PublicBindings.Value value)return value.original();throw new IllegalArgumentException("Army method requires its typed named argument object");}
    private static ArmyCalls.Frame frame(PublicMethod method,PublicBindings.Arguments args){if(ArmyCallCodec.decode(method,value(args)) instanceof ArmyCalls.Frame input)return input;throw new IllegalArgumentException("Army Frame argument mismatch");}
    private static ArmyCalls.Truce truce(PublicMethod method,PublicBindings.Arguments args){if(ArmyCallCodec.decode(method,value(args)) instanceof ArmyCalls.Truce input)return input;throw new IllegalArgumentException("Army Truce argument mismatch");}
    private static ArmyCalls.Unit unit(PublicMethod method,PublicBindings.Arguments args){if(ArmyCallCodec.decode(method,value(args)) instanceof ArmyCalls.Unit input)return input;throw new IllegalArgumentException("Army Unit argument mismatch");}
    private static ArmyCalls.CombatId combat(PublicMethod method,PublicBindings.Arguments args){if(ArmyCallCodec.decode(method,value(args)) instanceof ArmyCalls.CombatId input)return input;throw new IllegalArgumentException("Army Combat argument mismatch");}
    private static ArmyCalls.Terminal terminal(PublicMethod method,PublicBindings.Arguments args){if(ArmyCallCodec.decode(method,value(args)) instanceof ArmyCalls.Terminal input)return input;throw new IllegalArgumentException("Army Terminal argument mismatch");}
    private static ArmyCalls.RetreatPreview preview(PublicMethod method,PublicBindings.Arguments args){if(ArmyCallCodec.decode(method,value(args)) instanceof ArmyCalls.RetreatPreview input)return input;throw new IllegalArgumentException("Army Preview argument mismatch");}
    private static ArmyCalls.RetreatOrder order(PublicMethod method,PublicBindings.Arguments args){if(ArmyCallCodec.decode(method,value(args)) instanceof ArmyCalls.RetreatOrder input)return input;throw new IllegalArgumentException("Army Order argument mismatch");}
    private static ArmyCalls.Commander commander(PublicMethod method,PublicBindings.Arguments args){if(ArmyCallCodec.decode(method,value(args)) instanceof ArmyCalls.Commander input)return input;throw new IllegalArgumentException("Army Commander argument mismatch");}
}
