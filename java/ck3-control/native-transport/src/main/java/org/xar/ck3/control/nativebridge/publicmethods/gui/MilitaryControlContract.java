package org.xar.ck3.control.nativebridge.publicmethods.gui;

import static org.xar.ck3.control.contracts.StrictJson.require;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.OptionalInt;
import java.util.Set;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.gui.GuiModels;

/** Original exact-.4 military opener/reinforcement contracts. Public DATA is not permission to dispatch a GUI control. */
public final class MilitaryControlContract {
    public static final String OBSERVER="xar.java.fixed-military-control/v1";
    public static final String OPEN_GUI="77d0beedefe23eee22b24c1c0b160ae5ee8ec938868d3f4b7ae76296347a6ac6";
    public static final String REFILL_GUI="4f5523d249c2e0a4d3c328d789ca375f154c2e102544782480936b4206c57eac";
    public static final BigInteger U64=BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE);
    public static final BigInteger U32=BigInteger.ONE.shiftLeft(32).subtract(BigInteger.ONE);
    private MilitaryControlContract() { }
    public enum Control {
        OPEN("activate-ingame-military-v1"),ENABLE_REINFORCEMENT("enable-military-reinforcement-v1"),DISABLE_REINFORCEMENT("disable-military-reinforcement-v1");
        private final OperationKey operation;
        Control(String step){operation=new OperationKey(step);}
        public OperationKey operation(){return operation;}
        public String capability(){return "game.command."+operation.value();}
        public boolean desiredEnabled(){require(this!=OPEN,"opening is not a reinforcement toggle");return this==ENABLE_REINFORCEMENT;}
        public static Optional<Control> parse(OperationKey operation){for(Control value:values())if(value.operation.equals(operation))return Optional.of(value);return Optional.empty();}
    }
    public record Binding(GuiModels.Context context) {
        public Binding {
            Objects.requireNonNull(context);
            // This is the existing private fixed-control eligibility, separate from the public signed-ID DATA domain.
            require(context.build()==GuiModels.Build.CROZIER4&&context.before().frame().identity().player().signum()>0
                    &&context.before().frame().identity().player().compareTo(BigInteger.valueOf(Integer.MAX_VALUE))<=0
                    &&!context.before().frame().episodeRunId().isBlank()&&context.connectionGeneration().signum()>0
                    &&context.connectionGeneration().compareTo(U64)<=0,"actual exact-.4 fixed-control owner required");
            context.before().frame().identity().dateRaw().intValueExact();
        }
        public int actor(){return context.before().frame().identity().player().intValueExact();}
        public int dateRaw(){return context.before().frame().identity().dateRaw().intValueExact();}
        public long pid(){return context.before().game().pid();}
        public BigInteger generation(){return context.connectionGeneration();}
        public BigInteger nativeRevision(){return context.before().frame().identity().nativeRevision();}
        public BigInteger publicRevision(){return context.before().frame().revision();}
    }
    public record SwitchObservation(int ancestorDepth,int owner,boolean militaryPresent,OptionalInt rawByte,boolean enabled,RawJson original) {
        public SwitchObservation {Objects.requireNonNull(rawByte);Objects.requireNonNull(original);require(ancestorDepth>=8&&ancestorDepth<=11,"bounded actual source ancestor required");}
    }
    public record CensusFrame(BigInteger nativeRevision,BigInteger generation,BigInteger pumpEpoch,BigInteger ticketSequence,
            long pid,long threadId,int actor,int dateRaw) {
        public CensusFrame {
            for(BigInteger value:List.of(nativeRevision,generation,pumpEpoch,ticketSequence))require(value!=null&&value.signum()>0&&value.compareTo(U64)<=0,"actual native frame counter required");
            require(pid>0&&pid<=0xffff_ffffL&&threadId>0&&threadId<=0xffff_ffffL&&actor!=-1,"actual owner-thread receiver frame required");
        }
        public void requireBinding(Binding binding){require(nativeRevision.equals(binding.nativeRevision())&&generation.equals(binding.generation())
                &&pid==binding.pid()&&actor==binding.actor()&&dateRaw==binding.dateRaw(),"receiver census crossed actual bound owner/frame");}
    }
    public record BeforeObservation(String sourceChildPath,SwitchObservation sourceSwitch,CensusFrame frame,RawJson publicBinding) {
        public BeforeObservation {StrictJson.text(sourceChildPath);Objects.requireNonNull(sourceSwitch);Objects.requireNonNull(frame);Objects.requireNonNull(publicBinding);}
        public RawJson encode(){
            ObjectNode out=StrictJson.object().put("source_child_path",sourceChildPath);out.set("switch",node(sourceSwitch.original()));
            ObjectNode f=out.putObject("frame");f.put("native_revision",frame.nativeRevision()).put("connection_generation",frame.generation())
                    .put("pump_epoch",frame.pumpEpoch()).put("ticket_sequence",frame.ticketSequence()).put("game_pid",frame.pid()).put("thread_id",frame.threadId())
                    .put("played_character_full_id",frame.actor()).put("date_raw",frame.dateRaw()).put("owner_thread_verified",true).put("frame_stable",true).put("gui_owner_stable",true);
            out.set("public_binding",node(publicBinding));return raw(out);
        }
    }
    public static SwitchObservation switchObservation(JsonNode value,int owner){
        ObjectNode row=StrictJson.object(value,Set.of("source","scope","status","unavailable_reason","current_variable_table_observed","native_receiver_selected","provider_invoked",
                "ancestor_depth","owner_full_id","military_component_present","raw_byte_4a9","enabled","value_basis","stable_double_read"));
        eq(row,"source","native_gui_type635_static_direct_owner_switch_12004");eq(row,"scope","static_direct_source_candidate");eq(row,"status","available");
        require(row.get("unavailable_reason").isNull(),"available static source has no unavailable reason");
        for(String key:List.of("current_variable_table_observed","native_receiver_selected","provider_invoked"))require(!bool(row,key),"static source cannot claim a selected dynamic receiver/provider");
        require(bool(row,"stable_double_read"),"actual stable static switch required");int depth=integer(row,"ancestor_depth",8,11).intValueExact();
        require(integer(row,"owner_full_id",Integer.MIN_VALUE,Integer.MAX_VALUE).intValueExact()==owner,"actual static switch owner differs");
        boolean present=bool(row,"military_component_present"),enabled=bool(row,"enabled");OptionalInt actual;
        if(present){actual=OptionalInt.of(integer(row,"raw_byte_4a9",0,255).intValueExact());eq(row,"value_basis","raw_military_byte");require(enabled==(actual.getAsInt()!=0),"military raw switch/derived state differs");}
        else {require(row.get("raw_byte_4a9").isNull()&&!enabled,"native null military component cannot invent a byte/enabled state");eq(row,"value_basis","native_null_military_zero");actual=OptionalInt.empty();}
        return new SwitchObservation(depth,owner,present,actual,enabled,raw(row));
    }
    public static RawJson acknowledgement(Control control,Binding binding,RawJson original,Optional<BeforeObservation> before){
        ObjectNode row=node(original);eq(row,"step",control.operation().value());require(bool(row,"accepted"),"actual accepted native result required");
        eq(row,"game_version","1.20.0.4");require(text(row,"executable_sha256").equalsIgnoreCase(GuiModels.Build.CROZIER4.sha256()),"actual native executable differs");
        require(integer(row,"native_revision",BigInteger.ONE,U64).equals(binding.nativeRevision())
                &&integer(row,"connection_generation",BigInteger.ONE,U64).equals(binding.generation())
                &&integer(row,"game_pid",1,0xffff_ffffL).longValueExact()==binding.pid()
                &&integer(row,"played_character_id",Integer.MIN_VALUE,Integer.MAX_VALUE).intValueExact()==binding.actor()
                &&integer(row,"date_raw",Integer.MIN_VALUE,Integer.MAX_VALUE).intValueExact()==binding.dateRaw(),"native control ACK crossed owner/frame");
        for(String key:List.of("owner_thread_verified","frame_verified","source_abi_pins_verified","gui_owner_binding_verified"))require(bool(row,key),"actual source admission absent: "+key);
        if(row.has("backend_id"))eq(row,"backend_id","native-headless");
        boolean attempted=bool(row,"dispatch_attempted"),invoked=bool(row,"dispatch_invoked");require(!invoked||attempted,"native invocation without actual attempted dispatch");
        if(control==Control.OPEN){
            require(before.isEmpty(),"opener cannot borrow a reinforcement before-switch");eq(row,"schema","ck3-ingame-military-open-12004-v1");eq(row,"source_gui_sha256",OPEN_GUI);
            require(!bool(row,"business_model_available")&&!bool(row,"military_refill_action_available")&&bool(row,"native_after_read"),"military opener role/source is inconsistent");
            boolean visible=bool(row,"before_visible"),afterVisible=bool(row,"native_after_visible"),complete=bool(row,"native_after_tree_complete");
            require(!(visible&&attempted)&&(invoked?!visible&&bool(row,"topbar_tree_complete")&&bool(row,"receiver_qualified"):visible),"actual once-open native receiver proof unavailable");
            require(bool(row,"postcondition_verified")== (complete&&afterVisible)
                    &&bool(row,"verification_pending")== (invoked&&!(complete&&afterVisible)),"native visibility proof flags differ");
        }else{
            require(before.isPresent(),"reinforcement requires its actual independent before switch");
            var required=Set.of("schema","step","accepted","status","unavailable_reason","desired_enabled","game_version","executable_sha256",
                    "native_revision","connection_generation","game_pid","played_character_id","date_raw","owner_thread_verified","frame_verified",
                    "source_abi_pins_verified","gui_owner_binding_verified","source_profile_verified","current_tree_complete","no_blocking_modal_verified",
                    "source_child_path","source_gui_sha256","before_switch","dispatch_attempted","dispatch_invoked","native_handled","postcondition_verified",
                    "verification_pending","current_variable_table_observed","native_receiver_selected","provider_invoked");
            var actualFields=new java.util.HashSet<String>();row.fieldNames().forEachRemaining(actualFields::add);
            require(actualFields.containsAll(required),"required original reinforcement ACK field missing");
            actualFields.removeAll(required);actualFields.removeAll(Set.of("native_after_tree_complete","before_after_same_source","native_after_switch","backend_id"));
            require(actualFields.isEmpty(),"unregistered original reinforcement ACK field");
            eq(row,"schema","ck3-military-reinforcement-set-12004-v1");eq(row,"source_gui_sha256",REFILL_GUI);
            require(row.has("unavailable_reason")&&row.get("unavailable_reason").isNull()&&bool(row,"desired_enabled")==control.desiredEnabled(),"native desired reinforcement differs");
            eq(row,"source_child_path",before.orElseThrow().sourceChildPath());
            for(String key:List.of("source_profile_verified","current_tree_complete","no_blocking_modal_verified"))require(bool(row,key),"actual reinforcement source gate absent: "+key);
            for(String key:List.of("current_variable_table_observed","native_receiver_selected","provider_invoked","postcondition_verified"))require(!bool(row,key),"ACK cannot manufacture receiver/effect proof");
            require(bool(row,"verification_pending"),"native ACK must retain independent verification pending");
            var source=switchObservation(row.get("before_switch"),binding.actor());
            require(node(source.original()).equals(node(before.orElseThrow().sourceSwitch().original())),"ACK before switch differs from actual independent source census");
            boolean handled=bool(row,"native_handled");
            if(source.enabled()==control.desiredEnabled()){eq(row,"status","noaction_already_desired");require(!attempted&&!invoked&&!handled,"already-desired source attempted a toggle");}
            else {eq(row,"status","acknowledged_verification_pending");require(attempted&&invoked,"original desired transition lacks its single native dispatch");}
            for(String key:List.of("native_after_tree_complete","before_after_same_source"))if(row.has(key))bool(row,key);
            if(row.hasNonNull("native_after_switch"))switchObservation(row.get("native_after_switch"),binding.actor());
        }
        return original;
    }
    public static void requireLater(BeforeObservation before,BeforeObservation later){
        require(later.sourceChildPath().equals(before.sourceChildPath())&&later.frame().ticketSequence().compareTo(before.frame().ticketSequence())>0
                &&later.frame().pumpEpoch().compareTo(before.frame().pumpEpoch())>=0&&later.frame().threadId()==before.frame().threadId(),
                "later reinforcement census is not the fresh same-source owner-thread observation");
    }
    public static ObjectNode node(RawJson value){JsonNode parsed=org.xar.ck3.control.application.driver.DriverJson.toNode(org.xar.ck3.control.application.driver.DriverJson.object(value.bytes(),RawJson.MAXIMUM_BYTES));require(parsed instanceof ObjectNode,"original military object required");return (ObjectNode)parsed;}
    public static RawJson raw(JsonNode value){return new RawJson(org.xar.ck3.control.application.driver.DriverJson.encodeNode(value));}
    public static String text(ObjectNode row,String field){return StrictJson.text(row.get(field));}
    public static void eq(ObjectNode row,String field,String expected){require(expected.equals(text(row,field)),"original military field differs: "+field);}
    public static boolean bool(ObjectNode row,String field){JsonNode value=row.get(field);require(value!=null&&value.isBoolean(),"actual boolean required: "+field);return value.booleanValue();}
    public static BigInteger integer(ObjectNode row,String field,long low,long high){return integer(row,field,BigInteger.valueOf(low),BigInteger.valueOf(high));}
    public static BigInteger integer(ObjectNode row,String field,BigInteger low,BigInteger high){return StrictJson.integer(row.get(field),low,high);}
}
