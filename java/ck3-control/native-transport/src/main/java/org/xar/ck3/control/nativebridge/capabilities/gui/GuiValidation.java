package org.xar.ck3.control.nativebridge.capabilities.gui;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Set;
import static org.xar.ck3.control.nativebridge.capabilities.gui.GuiModels.*;
import static org.xar.ck3.control.nativebridge.capabilities.gui.GuiJson.*;

/** Exact original build scopes and finite selectors, checked again by the coordinator preparation. */
final class GuiValidation {
    private GuiValidation() { }
    static final Set<String> PRESENTATION=Set.of("query","open_holding","open_personal_beliefs","select_presentation_tab","open_rite_core_picker",
        "hover_presentation_tooltip","leave_presentation_tooltip","show_building_details","open_building_track","close_presentation_window","open_clerical_preview","close_clerical_preview","close_tooltips");
    static WindowKind targetKind(String target){return switch(target){case "faith_core_tenet","faith_doctrine"->WindowKind.FAITH;case "personal_tenet"->WindowKind.PERSONAL_BELIEFS;
        case "rite_core_tenet_choice","rite_core_tenet_slot"->WindowKind.RITE_CREATION;case "holding_building","holding_building_preview","holding_construct_conditions"->WindowKind.HOLDING;
        case "clerical_puppet","external_clerical_puppet"->WindowKind.CLERICAL_INTERACTION;default->throw new IllegalArgumentException("unknown presentation target");};}
    static void presentation(Context c,Presentation p){need(c.build()==Build.CROZIER4&&PRESENTATION.contains(p.operation()),"finite presentation requires exact .4 producer");
        need(Set.of(WindowKind.FAITH,WindowKind.HOLDING,WindowKind.PERSONAL_BELIEFS,WindowKind.RITE_CREATION,WindowKind.CLERICAL_INTERACTION,WindowKind.TOOLTIPS).contains(p.kind()),"presentation window scope");
        String op=p.operation(),target=p.target().orElse(""),tab=p.tab().orElse("");boolean index=p.index().isPresent(),receipt=p.receipt().isPresent();
        p.index().ifPresent(i->need(i>=0&&i<128,"finite presentation row index"));if(!target.isEmpty())need(targetKind(target)==p.kind(),"presentation target/window drift");
        if(p.kind()==WindowKind.HOLDING){range(p.subject().value(),op.equals("query")&&target.isEmpty()?BigInteger.ZERO:BigInteger.ONE,BigInteger.valueOf(Integer.MAX_VALUE));}
        if(p.kind()==WindowKind.PERSONAL_BELIEFS){if(!op.equals("query")||!target.isEmpty())need(p.subject().value().equals(c.before().frame().identity().player()),"personal beliefs actual player only");}
        if(!tab.isEmpty())need((p.kind()==WindowKind.FAITH&&Set.of("beliefs","holy_sites").contains(tab))||(p.kind()==WindowKind.PERSONAL_BELIEFS&&Set.of("tenets","doctrines").contains(tab)),"finite tab belongs to another window");
        if(p.kind()==WindowKind.CLERICAL_INTERACTION){
            need(Set.of("query","open_clerical_preview","close_clerical_preview").contains(op)
                &&p.subject().value().signum()>0&&Set.of("clerical_puppet","external_clerical_puppet").contains(target)
                &&!index&&p.tab().isEmpty()&&(op.equals("query")||receipt),"default-only clerical preview requires full recipient, finite target and action query receipt");return;}
        if(p.kind()==WindowKind.TOOLTIPS){need(p.subject().value().signum()==0&&p.target().isEmpty()&&!index&&p.tab().isEmpty()&&(op.equals("query")||op.equals("close_tooltips")&&receipt),"global tooltip selectors invalid");return;}
        switch(op){
            case "query"->need(target.isEmpty()? !index&&!receipt:index&&receipt&&tab.isEmpty(),"tooltip query requires exact row and receipt");
            case "hover_presentation_tooltip","leave_presentation_tooltip"->need(!target.isEmpty()&&index&&tab.isEmpty()&&(op.startsWith("hover")==!receipt),"tooltip source selectors invalid");
            case "select_presentation_tab"->need(!tab.isEmpty()&&target.isEmpty()&&!index&&!receipt,"tab selectors invalid");
            case "open_rite_core_picker"->need(p.kind()==WindowKind.RITE_CREATION&&index&&target.isEmpty()&&tab.isEmpty()&&!receipt,"core picker selectors invalid");
            case "open_building_track"->need(p.kind()==WindowKind.HOLDING&&target.equals("holding_building")&&index&&tab.isEmpty()&&!receipt,"installed building row required");
            case "show_building_details"->need(p.kind()==WindowKind.HOLDING&&target.equals("holding_building_preview")&&index&&tab.isEmpty()&&!receipt,"potential building preview required");
            case "close_presentation_window"->need(p.kind()==WindowKind.PERSONAL_BELIEFS&&p.target().isEmpty()&&!index&&p.tab().isEmpty()&&!receipt,"personal beliefs close selectors invalid");
            case "open_holding","open_personal_beliefs"->need(p.kind()==(op.equals("open_holding")?WindowKind.HOLDING:WindowKind.PERSONAL_BELIEFS)&&p.target().isEmpty()&&!index&&p.tab().isEmpty()&&!receipt,"opening selector scope");
            case "open_clerical_preview","close_clerical_preview"->need(p.kind()==WindowKind.CLERICAL_INTERACTION&&!target.isEmpty()&&!index&&tab.isEmpty(),"fixed clerical preview selectors required");
            default->throw new IllegalArgumentException("unsupported presentation operation");}
    }
    static Presentation fromFields(String operation,WindowKind kind,Subject subject,ObjectNode a){return new Presentation(operation,kind,subject,
        a.has("presentation_target")?java.util.Optional.of(text(a,"presentation_target")):java.util.Optional.empty(),
        a.has("presentation_index")?java.util.Optional.of(count(a,"presentation_index",0,127)):java.util.Optional.empty(),
        a.has("presentation_tab")?java.util.Optional.of(text(a,"presentation_tab")):java.util.Optional.empty(),
        a.has("presentation_receipt")?java.util.Optional.of(new ReceiptId(text(a,"presentation_receipt"))):java.util.Optional.empty());}
    static void semantic(Context c,String operation,WindowKind kind,Subject subject,ObjectNode a){
        boolean presentation=a.has("presentation_target")||a.has("presentation_index")||a.has("presentation_tab")||a.has("presentation_receipt")||
            Set.of(WindowKind.HOLDING,WindowKind.PERSONAL_BELIEFS,WindowKind.RITE_CREATION,WindowKind.CLERICAL_INTERACTION,WindowKind.TOOLTIPS).contains(kind)||PRESENTATION.contains(operation)&&!operation.equals("query");
        if(presentation){presentation(c,fromFields(operation,kind,subject,a));return;}
        boolean tooltip=a.has("army_tooltip_kind");
        if(tooltip){need(kind==WindowKind.ARMY&&Set.of("query","hover_army_tooltip","leave_army_tooltip").contains(operation)&&c.build()!=Build.LEGACY,"army tooltip exact current native scope");TooltipKind.parse(text(a,"army_tooltip_kind"));
            if(operation.equals("hover_army_tooltip"))need(!a.has("army_tooltip_receipt"),"initial hover cannot consume a receipt");else new ReceiptId(text(a,"army_tooltip_receipt"));return;}
        need(!a.has("army_tooltip_receipt"),"unsolicited tooltip receipt");
        if(c.build()!=Build.LEGACY){boolean allowed=kind==WindowKind.ARMY&&Set.of("query","select_army").contains(operation)||c.build()==Build.CROZIER4&&
            ((kind==WindowKind.CHARACTER&&Set.of("query","open_character").contains(operation))||(kind==WindowKind.FAITH&&Set.of("query","open_faith").contains(operation)));
            need(allowed,"original current native UI build has no such route");}
        if(operation.equals("query")||operation.equals("open_knights"))need(subject.value().signum()==0,"this operation has no selected subject");
        else if(!operation.equals("select_army")&&!operation.equals("open_faith"))need(subject.value().signum()>0,"positive selected subject required");
    }
    static void intentId(String id){need(id!=null&&id.matches("[A-Za-z0-9_.:-]{1,64}"),"fixed White durable intent ID required");}
}
