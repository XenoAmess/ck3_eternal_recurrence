package org.xar.ck3.control.nativebridge.capabilities.gui;

import java.math.BigInteger;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;

/** Native domain values; IDs preserve their complete integer handles. */
public final class GuiModels {
    private GuiModels() { }
    public enum Build {
        LEGACY("1.19.0.6", "legacy"), CROZIER3("1.20.0.3", "94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6"),
        CROZIER4("1.20.0.4", "98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518");
        private final String version,sha256;Build(String v,String s){version=v;sha256=s;}
        public String version(){return version;}public String sha256(){return sha256;}
    }
    public record Context(ObservationIdentity before,G2Source source,String sessionId,
            BigInteger connectionGeneration,Build build,Instant deadline) {
        public Context {Objects.requireNonNull(before);Objects.requireNonNull(source);Objects.requireNonNull(build);Objects.requireNonNull(deadline);
            GuiJson.need(sessionId!=null&&!sessionId.isBlank(),"held native session required");GuiJson.range(connectionGeneration,BigInteger.ONE,GuiJson.U64);
            GuiJson.need(before.machineId().equals(source.machineId()),"GUI source machine drift");}
    }
    public record Intent(Context frame,String actionId){public Intent{Objects.requireNonNull(frame);GuiJson.need(actionId!=null&&actionId.matches("[A-Za-z0-9][A-Za-z0-9._:-]{0,127}"),"durable identity required");}}
    public record Subject(BigInteger value){public Subject{GuiJson.range(value,BigInteger.ZERO,GuiJson.U32.subtract(BigInteger.TWO));}public Subject(long value){this(BigInteger.valueOf(value));}}
    public record DecisionKey(String value){public DecisionKey{GuiJson.need(value!=null&&value.matches("[A-Za-z0-9_]{1,192}"),"actual semantic decision key required");}}
    public record TitleKey(String value){public TitleKey{GuiJson.need(value!=null&&value.matches("[bcdke]_[a-zA-Z0-9_]{1,125}"),"landed-title key required");}}
    public record ReceiptId(String value){public ReceiptId{GuiJson.need(value!=null&&value.matches("[0-9a-f]{32}"),"actual lower-case tooltip receipt required");}}
    public enum WindowKind {
        CHARACTER,ARMY,COMBAT,KNIGHTS,FAITH,HOLY_SITE,HOLY_SITE_ADOPTION,HOLY_SITE_CREATION,HOLDING,PERSONAL_BELIEFS,RITE_CREATION,CLERICAL_INTERACTION,TOOLTIPS;
        public String wire(){return name().toLowerCase(java.util.Locale.ROOT);}public static WindowKind parse(String wire){return valueOf(wire.toUpperCase(java.util.Locale.ROOT));}
    }
    public enum TreeKind {
        TOPBAR("ingame_topbar","ingame_topbar"),DECISIONS("decisions","decisions_view"),MILITARY("military","military_view"),
        HOLY_SITE("holy_site","holy_site_window"),DECISION_DETAIL("decision_detail","decisiondetail_view"),COURTIER("courtier","xar_courtier_creator_window"),
        WHITE("vivhite_courtier","ervc_courtier_creator_window"),DEATH_SUCCESSION("death_succession","succession_event_window"),DEATH_DESTINY("death_destiny","succession_select_destiny_window");
        private final String wire,root;TreeKind(String w,String r){wire=w;root=r;}public String wire(){return wire;}public String root(){return root;}
        public static TreeKind parse(String wire){for(var v:values())if(v.wire.equals(wire))return v;throw new IllegalArgumentException("unknown census root");}
    }
    public enum TooltipKind {SUPPLY_STATE,ATTRITION;public String wire(){return name().toLowerCase(java.util.Locale.ROOT);}public static TooltipKind parse(String wire){return valueOf(wire.toUpperCase(java.util.Locale.ROOT));}}
    public enum Side {LEFT,RIGHT;public String wire(){return name().toLowerCase(java.util.Locale.ROOT);}}
    public enum Outcome {EVENT_WINDOW,DECISION_CLOSED;public String wire(){return name().toLowerCase(java.util.Locale.ROOT);}}
    public enum Policy {
        TREASURY_PAUSE("aub_policy_treasury_only_pause_choice"),TREASURY_CONTINUE("aub_policy_treasury_only_continue_choice"),
        PERSONAL_PAUSE("aub_policy_personal_only_pause_choice"),PERSONAL_CONTINUE("aub_policy_personal_only_continue_choice"),
        TREASURY_FIRST_PAUSE("aub_policy_treasury_first_pause_choice"),TREASURY_FIRST_CONTINUE("aub_policy_treasury_first_continue_choice");
        private final String wire;Policy(String w){wire=w;}public String wire(){return wire;}public static Policy parse(String wire){for(var v:values())if(v.wire.equals(wire))return v;throw new IllegalArgumentException("unknown AUB policy");}
    }
    public enum NumericControl {DIPLOMACY,MARTIAL,STEWARDSHIP,INTRIGUE,LEARNING,PROWESS;
        public String stem(){return name().toLowerCase(java.util.Locale.ROOT);}public String wire(){return stem()+"_plus_1";}
        public static NumericControl parse(String wire){for(var v:values())if(v.wire().equals(wire))return v;throw new IllegalArgumentException("unknown fixed White control");}}
    public enum Variable {FEMALE,AGE,DIPLOMACY,MARTIAL,STEWARDSHIP,INTRIGUE,LEARNING,PROWESS;public String wire(){return "ervc_cc_"+name().toLowerCase(java.util.Locale.ROOT);}}
    public enum TextName {AGE,DIPLOMACY,MARTIAL,STEWARDSHIP,INTRIGUE,LEARNING,PROWESS,PRICE,GOLD;public String wire(){return "ervc_cc_"+name().toLowerCase(java.util.Locale.ROOT)+"_value_text";}}
    public record Availability(boolean available,String reason){public Availability{Objects.requireNonNull(reason);GuiJson.need(available?reason.isEmpty():!reason.isEmpty(),"availability reason inconsistent");}}
    public record Widget(String runtimeName,String childPath,int depth,int childCount,BigInteger vtableRva,boolean visible,boolean enabled) { }
    public record WindowTree(TreeKind kind,boolean rootAvailable,boolean truncated,List<Widget> widgets) {
        public WindowTree{Objects.requireNonNull(kind);widgets=List.copyOf(widgets);}
        public boolean completeVisibleRoot(){return rootAvailable&&!truncated&&widgets.stream().anyMatch(w->w.childPath().isEmpty()&&w.runtimeName().equals(kind.root())&&w.visible());}
        public boolean whiteInnerModalVisible(){return kind==TreeKind.WHITE&&completeVisibleRoot()&&widgets.stream().filter(w->w.childPath().isEmpty()&&w.childCount()==1).count()==1
            &&widgets.stream().filter(w->w.runtimeName().equals("ervc_courtier_creator_modal")&&w.childPath().equals("0")&&w.visible()).count()==1;}
        public boolean decisionDetailClosed(){var roots=widgets.stream().filter(w->w.childPath().isEmpty()).toList();return kind==TreeKind.DECISION_DETAIL&&rootAvailable&&!truncated&&roots.size()==1&&roots.getFirst().runtimeName().equals(kind.root())&&!roots.getFirst().visible();}
    }
    public record Geometry(boolean available,boolean insideViewport,boolean fitRequired) { }
    public record CacheText(String text,int utf8Bytes,String sha256) { }
    /** Cache evidence carries no rendered/refresh success. */
    public record ArmyTooltip(TooltipKind kind,Optional<ReceiptId> receipt,BigInteger actionEpoch,BigInteger laterEpoch,
            boolean sourceBound,boolean hoverMatches,boolean leaveObserved,boolean pending,Optional<CacheText> cache){public ArmyTooltip{receipt=Objects.requireNonNull(receipt);cache=Objects.requireNonNull(cache);}}
    public record UiWindow(WindowKind kind,Availability availability,boolean exists,boolean visible,boolean enabled,Optional<BigInteger> subject,
            BigInteger captureEpoch,Geometry geometry,Optional<ArmyTooltip> tooltip,List<Widget> widgets){public UiWindow{subject=Objects.requireNonNull(subject);tooltip=Objects.requireNonNull(tooltip);widgets=List.copyOf(widgets);}}
    public record DecisionItem(DecisionKey key,Availability availability,boolean detailVisible,boolean detailComplete,boolean definitionMatches,
            boolean actorBound,BigInteger actorReference,int groupCount,int rowCount){public boolean selectedFor(BigInteger player){return availability.available()&&detailVisible&&detailComplete&&definitionMatches&&actorBound&&player.equals(actorReference);}}
    public record PolicyEntry(Policy policy,boolean selected) { }
    public record Policies(Optional<Policy> selected,List<PolicyEntry> entries){public Policies{selected=Objects.requireNonNull(selected);entries=List.copyOf(entries);}}
    public record Flag(String key,boolean atomRegistered,boolean present) { }
    public record AubState(boolean detailRootAvailable,boolean detailVisible,List<Flag> flags){public AubState{flags=List.copyOf(flags);}
        public boolean confirmed(Policy p){int i=p.ordinal();return !detailVisible&&flags.size()==4&&flags.get(0).present()&&flags.get(1).present()==(i<2)&&flags.get(2).present()==(i>=2&&i<4)&&flags.get(3).present()==(i%2==0);}}
    public sealed interface VariableValue permits MissingVariable,NonNumericVariable,NumericVariable {Variable key();}
    public record MissingVariable(Variable key) implements VariableValue { }
    public record NonNumericVariable(Variable key,int actualKind,BigInteger actualPayload) implements VariableValue { }
    public record NumericVariable(Variable key,BigInteger fixedRaw,Optional<BigInteger> integer) implements VariableValue{public NumericVariable{integer=Objects.requireNonNull(integer);}}
    public record WhiteBusiness(Availability availability,List<VariableValue> values,boolean allIntegers){public WhiteBusiness{values=List.copyOf(values);}
        public BigInteger integer(Variable key){return values.stream().filter(v->v.key()==key).map(v->{GuiJson.need(v instanceof NumericVariable,"White variable nonnumeric");return ((NumericVariable)v).integer().orElseThrow(()->new IllegalArgumentException("White variable fractional"));}).findFirst().orElseThrow();}}
    public record TextValue(TextName key,String childPath,String text,boolean enabled) { }
    public record WhiteText(Availability availability,List<TextValue> fields){public WhiteText{fields=List.copyOf(fields);}public String text(TextName key){return fields.stream().filter(f->f.key()==key).findFirst().orElseThrow().text();}}
    public record WhiteBaseline(WhiteBusiness business,WhiteText text) { }
    public record Presentation(String operation,WindowKind kind,Subject subject,Optional<String> target,Optional<Integer> index,Optional<String> tab,Optional<ReceiptId> receipt){
        public Presentation{Objects.requireNonNull(operation);Objects.requireNonNull(kind);Objects.requireNonNull(subject);target=Objects.requireNonNull(target);index=Objects.requireNonNull(index);tab=Objects.requireNonNull(tab);receipt=Objects.requireNonNull(receipt);}}
}
