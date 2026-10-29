package org.xar.ck3.control.nativebridge.capabilities.gui;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.ExactRef;
import static org.xar.ck3.control.nativebridge.capabilities.gui.GuiModels.*;
import static org.xar.ck3.control.nativebridge.capabilities.gui.GuiJson.*;

/** Fixed advertised query definitions. Root installs these exact instances in its sole read coordinator. */
public final class GuiReads {
    public record Sources(ExactRef semantic,ExactRef census,ExactRef decision,ExactRef aubPolicy,ExactRef aubState,ExactRef whiteBusiness,ExactRef whiteText){
        public Sources{for(ExactRef source:List.of(semantic,census,decision,aubPolicy,aubState,whiteBusiness,whiteText))need(source.bytes()>0,"original producer definition required");}}
    public final ReadContract<UiWindow> semantic;
    public final ReadContract<WindowTree> census;
    public final ReadContract<DecisionItem> decision;
    public final ReadContract<Policies> aubPolicy;
    public final ReadContract<AubState> aubState;
    public final ReadContract<WhiteBusiness> whiteBusiness;
    public final ReadContract<WhiteText> whiteText;
    public GuiReads(Sources s){
        Objects.requireNonNull(s);
        semantic=contract("query-ingame-ui-window-v1",s.semantic(),r->{ObjectNode a=arguments(r.request().arguments());Context c=context(r.request());WindowKind kind=WindowKind.parse(text(a,"window_kind"));Subject subject=new Subject(integer(a,"subject_id"));ObjectNode value=result(r);
            if(c.build()==Build.CROZIER4&&Set.of(WindowKind.FAITH,WindowKind.HOLDING,WindowKind.PERSONAL_BELIEFS,WindowKind.RITE_CREATION,WindowKind.CLERICAL_INTERACTION,WindowKind.TOOLTIPS).contains(kind))GuiPresentationResult.validate(value,c,"query",kind,subject,a);
            return GuiDecoders.uiWindow(value,c,kind,subject,
            a.has("army_tooltip_kind")?Optional.of(TooltipKind.parse(text(a,"army_tooltip_kind"))):Optional.empty(),a.has("army_tooltip_receipt")?Optional.of(new ReceiptId(text(a,"army_tooltip_receipt"))):Optional.empty());});
        census=contract("inspect-gui-window-tree-v1",s.census(),r->GuiDecoders.windowTree(result(r),TreeKind.parse(text(arguments(r.request().arguments()),"window_kind"))));
        decision=contract("query-ingame-decision-item-v1",s.decision(),r->GuiDecoders.decisionItem(result(r),context(r.request()),new DecisionKey(text(arguments(r.request().arguments()),"decision_key"))));
        aubPolicy=contract("query-aub-policy-options-v1",s.aubPolicy(),r->GuiDecoders.policies(result(r),context(r.request())));
        aubState=contract("query-aub-business-state-v1",s.aubState(),r->GuiDecoders.aubState(result(r),context(r.request())));
        whiteBusiness=contract("query-white-player-business-variables-v1",s.whiteBusiness(),r->GuiDecoders.whiteBusiness(result(r),context(r.request())));
        whiteText=contract("query-white-rendered-text-v1",s.whiteText(),r->GuiDecoders.whiteText(result(r),context(r.request())));
    }
    private static <T> ReadContract<T> contract(String step,ExactRef source,java.util.function.Function<PlanningReadReceipt,T> decoder){
        return new ReadContract<>("gui:"+step,new OperationKey(step),Optional.of("game.command."+step),"game.command."+step,
            ReadContract.PermissionMode.ADVERTISED_CAPABILITY,ReadContract.WireProfile.EXECUTE_STEP,source,
            r->{ObjectNode a=arguments(r.arguments());Context c=context(r);a.remove(List.of("_gui_build","_gui_generation"));validateReadFields(step,a,c);
                return new NativeRequest(step,"game.command."+step,raw(a));},decoder);
    }
    public List<ReadContract<?>> registered(){return List.of(semantic,census,decision,aubPolicy,aubState,whiteBusiness,whiteText);}
    public static Context context(PlanningReadRequest request){ObjectNode a=arguments(request.arguments());return new Context(request.before(),request.source(),request.sessionId(),integer(a,"_gui_generation"),Build.valueOf(text(a,"_gui_build")),request.deadline());}
    public static Context context(ActionCommand request){ObjectNode a=arguments(request.arguments());return new Context(request.before(),request.source(),request.sessionId(),integer(a,"_gui_generation"),Build.valueOf(text(a,"_gui_build")),request.deadline());}
    static ObjectNode metadata(Context c,ObjectNode fields){ObjectNode a=fields.deepCopy();a.put("_gui_build",c.build().name());a.put("_gui_generation",c.connectionGeneration());return a;}
    public <T> PlanningReadResult<T> read(PlanningReadPort port,ReadContract<T> contract,Context c,ObjectNode fields){return port.read(contract,
        new PlanningReadRequest(c.before(),c.source(),c.sessionId(),contract.operation(),arguments(metadata(c,fields)),c.deadline()));}
    static void validateReadFields(String step,ObjectNode a,Context c){
        if(step.equals("inspect-gui-window-tree-v1")){keys(a,java.util.Set.of("window_kind"),java.util.Set.of());TreeKind.parse(text(a,"window_kind"));return;}
        if(step.equals("query-ingame-ui-window-v1")){keys(a,java.util.Set.of("window_kind","subject_id"),java.util.Set.of("army_tooltip_kind","army_tooltip_receipt","presentation_target","presentation_index","presentation_tab","presentation_receipt"));
            GuiValidation.semantic(c,"query",WindowKind.parse(text(a,"window_kind")),new Subject(integer(a,"subject_id")),a);return;}
        java.util.Set<String> base=java.util.Set.of("expected_player_character_id","expected_game_pid","expected_connection_generation");
        keys(a,base,step.equals("query-ingame-decision-item-v1")?java.util.Set.of("decision_key"):java.util.Set.of());
        equal(a,"expected_player_character_id",c.before().frame().identity().player());equal(a,"expected_game_pid",BigInteger.valueOf(c.before().game().pid()));equal(a,"expected_connection_generation",c.connectionGeneration());
        if(step.equals("query-ingame-decision-item-v1"))new DecisionKey(text(a,"decision_key"));
        else need(c.build()==Build.CROZIER3,"fixed White/AUB producer is exact 1.20.0.3 only");
    }
    static <T> PlanningReadResult.Known<T> known(PlanningReadResult<T> result){if(result instanceof PlanningReadResult.Known<T> value)return value;
        throw new IllegalArgumentException(((PlanningReadResult.Unavailable<T>)result).reason());}
}
