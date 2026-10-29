package org.xar.ck3.control.nativebridge.publicmethods.gui;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.publicmethods.gui.MilitaryControlContract.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.json.JsonMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.HashSet;
import java.util.HexFormat;
import java.util.List;
import java.util.Optional;
import java.util.OptionalInt;
import java.util.Set;
import java.util.function.Consumer;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.capabilities.gui.GuiDecoders;
import org.xar.ck3.control.nativebridge.capabilities.gui.GuiModels;

/** Pure source fixtures port the original Python test census. They grant no Native/Root/Managed authority. */
final class MilitaryReceiverProofTest {
    private static final ObjectMapper TEST_WIRE=JsonMapper.builder().build();
    private static final String PREFIX="definition_chain_prefix_depth8",TAIL="definition_frontier_continuation_depth8_12";
    private static final String SWITCH="static_direct_owner_switch_12004",LOCAL="local_definition_entry_only";
    private static final BigInteger MAX=BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE);
    private static Binding binding(){return binding(BigInteger.valueOf(109),BigInteger.ONE);}
    private static Binding binding(BigInteger revision,BigInteger generation){
        var time=Instant.parse("2026-10-24T09:00:00Z");var source=new G2Source("software-military-receiver",time.toString(),"1.20.0.4",new ExactRef("fixture:python-census-data",1,"a".repeat(64)));
        var game=new GameGeneration(29000,new PythonOnlyUInt64(new BigInteger("133700000000000001")));
        var frame=new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(31254),revision,BigInteger.valueOf(53148960)),
                "native:109",BigInteger.valueOf(110),"native-31254-test");
        return new Binding(new GuiModels.Context(new ObservationIdentity(source.machineId(),game,frame,1),source,"software-session",generation,GuiModels.Build.CROZIER4,time.plusSeconds(20)));
    }
    private static ObjectNode object(JsonNode value){assertInstanceOf(ObjectNode.class,value);return (ObjectNode)value;}
    private static ObjectNode parse(RawJson value){return object(DriverJson.toNode(DriverJson.object(value.bytes(),RawJson.MAXIMUM_BYTES)));}
    private static RawJson raw(JsonNode value){try{return new RawJson(TEST_WIRE.writeValueAsBytes(value));}
        catch(IOException failure){throw new IllegalArgumentException("software JSON wire fixture cannot be encoded",failure);}}
    private static ObjectNode census(Integer value){return parse(MilitaryReceiverFixture.census(binding(),
            value==null?OptionalInt.empty():OptionalInt.of(value),BigInteger.valueOf(65)));}
    private static ObjectNode target(ObjectNode tree){return object(tree.get("widgets").get(8));}
    private static ObjectNode callback(ObjectNode tree){return object(target(tree).get("standard_click_binding_12004").get("callbacks").get(0));}
    private static ObjectNode payload(ObjectNode tree){return object(callback(tree).get("indirect_target_3aa30e0"));}
    private static ObjectNode expression(ObjectNode tree){return object(payload(tree).get("expression_3a9f960"));}
    private static ObjectNode candidate(ObjectNode tree){return object(expression(tree).get("receiver_entry_candidates_12004"));}
    private static ObjectNode tail(ObjectNode tree){return object(candidate(tree).get(TAIL));}
    private static ObjectNode direct(ObjectNode tree){return object(tail(tree).get("rows").get(0).get("entries").get(0));}
    private static ObjectNode sourceSwitch(ObjectNode tree){return object(tail(tree).get(SWITCH));}
    private static ObjectNode frame(ObjectNode tree){return object(tree.get("refill_receiver_frame_12004"));}
    private static BeforeObservation observe(ObjectNode tree){return MilitaryReceiverProof.observeFixedReinforcement(raw(tree),binding());}
    private static void refuses(Consumer<ObjectNode> mutation){ObjectNode changed=census(0);mutation.accept(changed);assertThrows(IllegalArgumentException.class,()->observe(changed));}

    @Test void fullOriginalShapeJoinsStaticOwnerWithoutInventingSelectedReceiver(){
        ObjectNode original=census(0);RawJson normalized=MilitaryReceiverProof.normalizeTree(raw(original),binding());BeforeObservation actual=observe(original);
        assertEquals("0/0/0/2/3/0/0/0",actual.sourceChildPath());assertFalse(actual.sourceSwitch().enabled());assertEquals(OptionalInt.of(0),actual.sourceSwitch().rawByte());
        ObjectNode clean=parse(normalized);assertEquals("unavailable",candidate(clean).get("status").textValue());assertFalse(candidate(clean).get("native_receiver_selected").booleanValue());
        assertFalse(clean.get("click_action_available").booleanValue());assertFalse(clean.get("callback_method_name_available").booleanValue());
        assertJsonEquals(expression(original),expression(clean));assertEquals(actual,MilitaryReceiverProof.observeFixedReinforcement(normalized,binding()));
        assertArrayEquals(normalized.bytes(),MilitaryReceiverProof.normalizeTree(normalized,binding()).bytes());
    }
    @Test void actualRawByteAndNativeNullComponentRemainDifferent(){
        for(Integer value:new Integer[]{0,1,255,null}){var actual=observe(census(value));assertEquals(value!=null&&value!=0,actual.sourceSwitch().enabled());
            assertEquals(value!=null,actual.sourceSwitch().militaryPresent());assertEquals(value==null?OptionalInt.empty():OptionalInt.of(value),actual.sourceSwitch().rawByte());
            assertJsonEquals(parse(actual.encode()).get("switch"),sourceSwitch(census(value)));}
        refuses(tree->sourceSwitch(tree).put("raw_byte_4a9",256));refuses(tree->sourceSwitch(tree).put("enabled",true));
    }
    @Test void sourceProfilesRequireExactFieldsTypesHashesAndNoUnqualifiedReceiverAliases(){
        refuses(tree->object(tree.get("callback_binding_source_12004")).put("receiver_typed_entry_rva",0x3ac1c01));
        refuses(tree->object(tree.get("callback_binding_source_12004")).put("input_modifier",false));
        refuses(tree->object(tree.get("callback_binding_source_12004")).put("input_modifier",0.0));
        refuses(tree->object(tree.get("callback_binding_source_12004")).put("receiver_typed_entry_bytes_sha256","0".repeat(64)));
        refuses(tree->object(tree.get("callback_binding_source_12004")).put("caller_source_override",true));
        refuses(tree->object(tree.get("callback_binding_source_12004")).remove("receiver_definition_parent_rva"));
    }
    @Test void missingCallbackAndMalformedExpressionAreRejectedBeforeReceiverJoin(){
        refuses(tree->target(tree).remove("standard_click_binding_12004"));refuses(tree->callback(tree).put("index",1));
        refuses(tree->callback(tree).put("callback_vtable_rva",0));refuses(tree->callback(tree).put("callback_slot2_rva",0x61c5000));
        refuses(tree->payload(tree).remove("receiver_f0_present"));refuses(tree->expression(tree).put("chain_count_24_raw",1));
        refuses(tree->expression(tree).put("receiver_type_id_48",new BigInteger("4294967295")));
        refuses(tree->expression(tree).put("final_kind_34_raw",new BigInteger("4294967295")));
        refuses(tree->expression(tree).put("final_target_38_rva",false));
    }
    @Test void sourcePathVisibilityAncestorsAndUniquenessAreActualInputs(){
        refuses(tree->target(tree).put("enabled",false));refuses(tree->target(tree).put("effective_visible",false));
        refuses(tree->object(tree.get("widgets").get(0)).put("effective_visible",false));
        refuses(tree->object(tree.get("widgets").get(4)).put("runtime_name","caller_tab"));
        refuses(tree->object(tree.get("widgets").get(5)).put("runtime_name","wrong_footer"));
        refuses(tree->target(tree).put("runtime_name","claimed_method"));
        refuses(tree->{((ArrayNode)tree.get("widgets")).add(target(tree).deepCopy());tree.put("widget_count",10);});
        refuses(tree->{((ArrayNode)target(tree).get("standard_click_binding_12004").get("callbacks")).add(callback(tree).deepCopy().put("index",1));});
        refuses(tree->tree.put("truncated",true));refuses(tree->tree.put("root_available",false));
    }
    @Test void candidateFailurePrefixAndLocalViewsMustAgreeWithoutPromotingUnknown(){
        refuses(tree->candidate(tree).put("native_receiver_selected",true));refuses(tree->candidate(tree).put("receiver_variable_index",0));
        refuses(tree->object(candidate(tree).get("failure_diagnostic")).put("capture_pass",2));
        refuses(tree->object(candidate(tree).get("failure_diagnostic")).put("ancestor_depth",7));
        refuses(tree->object(candidate(tree).get(LOCAL)).put("receiver_variable_index",1));
        refuses(tree->object(candidate(tree).get(PREFIX)).put("walk_complete",true));
        refuses(tree->object(candidate(tree).get(PREFIX).get("rows").get(0)).put("raw_definition_entry_count",0));
        refuses(tree->object(candidate(tree).get(PREFIX).get("rows").get(0).get("entries").get(0)).put("entry_flag_4c",1));
        refuses(tree->object(candidate(tree).get(PREFIX).get("rows").get(1)).put("parent_present",false));
    }
    @Test void continuationCannotCrossAStaticStopOrFabricateAProviderOwnerJoin(){
        refuses(tree->tail(tree).put("provider_invoked",true));refuses(tree->tail(tree).put("stop_depth",9));
        refuses(tree->tail(tree).put("stop_reason","null_end"));refuses(tree->tail(tree).put("next_context_present",true));
        refuses(tree->object(tail(tree).get("rows").get(0)).put("parent_present",true));
        refuses(tree->object(tail(tree).get("rows").get(0)).put("first_match_entry_index",3));
        refuses(tree->direct(tree).put("direct_owner_identity_verified",false));refuses(tree->direct(tree).put("direct_owner_full_id",-1));
        refuses(tree->direct(tree).put("provider_slot2_rva",7));refuses(tree->sourceSwitch(tree).put("owner_full_id",31255));
    }
    @Test void validCycleNullEndAndDepthLimitPreserveAReadOnlyUnselectedContinuation(){
        for(String reason:List.of("cycle","null_end","depth_limit")){
            ObjectNode tree=census(0),tail=tail(tree);tail.remove(SWITCH);tail.put("stop_reason",reason);ArrayNode rows=(ArrayNode)tail.get("rows");rows.removeAll();
            if(reason.equals("cycle")){tail.put("stop_depth",8).put("next_context_present",true);}
            else if(reason.equals("null_end")){
                ObjectNode row=StrictJson.object().put("ancestor_depth",8).put("definition_present",true).put("raw_definition_entry_count",0)
                        .putNull("first_match_entry_index").put("parent_edge","context_e8").put("parent_present",false);row.putArray("entries");rows.add(row);
                tail.put("stop_depth",9).put("next_context_present",false);
            }else{
                for(int depth=8;depth<12;depth++){ObjectNode row=StrictJson.object().put("ancestor_depth",depth).put("definition_present",false).putNull("raw_definition_entry_count")
                        .putNull("first_match_entry_index").put("parent_edge","context_e8").put("parent_present",true);row.putArray("entries");rows.add(row);}
                tail.put("stop_depth",12).put("next_context_present",true);
            }
            RawJson normalized=MilitaryReceiverProof.normalizeTree(raw(tree),binding());assertEquals(reason,tail(parse(normalized)).get("stop_reason").textValue());
            assertFalse(tail(parse(normalized)).get("native_receiver_selected").booleanValue());assertFalse(parse(normalized).get("click_action_available").booleanValue());
            assertThrows(IllegalArgumentException.class,()->MilitaryReceiverProof.observeFixedReinforcement(normalized,binding()));
        }
    }
    @Test void strictFrameTypesBindingAndFullUint64CountersRoundtrip(){
        ObjectNode raw=census(255);frame(raw).put("pump_epoch",MAX).put("ticket_sequence",MAX).put("connection_generation",MAX).put("native_revision",MAX);
        Binding context=binding(MAX,MAX);RawJson normalized=MilitaryReceiverProof.normalizeTree(MilitaryControlContract.raw(raw),context);
        var actual=MilitaryReceiverProof.observeFixedReinforcement(normalized,context);assertEquals(MAX,actual.frame().ticketSequence());assertEquals(MAX,actual.frame().generation());
        assertEquals(MAX,parse(actual.encode()).get("frame").get("native_revision").bigIntegerValue());
        assertArrayEquals(normalized.bytes(),MilitaryReceiverProof.normalizeTree(normalized,context).bytes());
        refuses(tree->frame(tree).put("native_revision",108));refuses(tree->frame(tree).put("connection_generation",2));
        refuses(tree->frame(tree).put("played_character_full_id",31255));refuses(tree->frame(tree).put("game_pid",29001));refuses(tree->frame(tree).put("date_raw",53148961));
        refuses(tree->frame(tree).put("ticket_sequence",true));refuses(tree->frame(tree).put("pump_epoch",1.0));
        refuses(tree->frame(tree).put("ticket_sequence",MAX.add(BigInteger.ONE)));refuses(tree->frame(tree).put("owner_thread_verified",false));
        refuses(tree->frame(tree).put("thread_id",0));refuses(tree->frame(tree).put("played_character_full_id",-1));
        refuses(tree->frame(tree).put("ticket_sequence","65"));refuses(tree->frame(tree).putNull("pump_epoch"));refuses(tree->frame(tree).remove("date_raw"));
    }
    @Test void unknownSwitchAndAvailableCandidateDoNotAuthorizeASelectedReceiver(){
        ObjectNode raw=census(0);ObjectNode sw=sourceSwitch(raw);sw.put("status","unavailable").put("unavailable_reason","actual_missing").put("stable_double_read",false);
        for(String field:List.of("ancestor_depth","owner_full_id","military_component_present","raw_byte_4a9","enabled","value_basis"))sw.putNull(field);
        RawJson normalized=MilitaryReceiverProof.normalizeTree(MilitaryControlContract.raw(raw),binding());assertTrue(sourceSwitch(parse(normalized)).get("enabled").isNull());
        assertThrows(IllegalArgumentException.class,()->MilitaryReceiverProof.observeFixedReinforcement(normalized,binding()));
        ObjectNode available=census(0),candidate=candidate(available);candidate.remove(List.of("failure_diagnostic",LOCAL,PREFIX,TAIL));candidate.put("status","available").putNull("unavailable_reason")
                .put("receiver_variable_index",0).put("declared_type_id",635).put("stable_double_read",true);
        assertFalse(parse(MilitaryReceiverProof.normalizeTree(MilitaryControlContract.raw(available),binding())).get("click_action_available").booleanValue());
        assertThrows(IllegalArgumentException.class,()->observe(available));
    }
    @Test void fullCensusBeyondRequestLimitRetainsOriginalRowsAndCallback(){
        ObjectNode original=census(1);ArrayNode rows=(ArrayNode)original.get("widgets");
        for(int index=10;index<1400;index++){ObjectNode row=object(rows.get(1)).deepCopy().put("child_path",Integer.toString(index)).put("runtime_name","x".repeat(120)).put("child_count",0);
            rows.add(row);}
        original.put("widget_count",rows.size());assertTrue(raw(original).bytes().length>128*1024);
        var normalized=MilitaryReceiverProof.normalizeTree(raw(original),binding());assertEquals(rows.size(),integer(parse(normalized),"widget_count",0,2048).intValueExact());
        assertTrue(MilitaryReceiverProof.observeFixedReinforcement(normalized,binding()).sourceSwitch().enabled());
    }
    @Test void existingGuiScalarProducerAndReceiptResultRawRemainDistinct(){
        ObjectNode input=census(1);var basic=GuiDecoders.windowTree(input,GuiModels.TreeKind.MILITARY);assertEquals(9,basic.widgets().size());
        var actual=MilitaryReceiverProof.observeFixedReinforcement(MilitaryReceiverProof.normalizeTree(raw(input),binding()),binding());
        assertEquals(basic.widgets().getLast().childPath(),actual.sourceChildPath());assertJsonEquals(sourceSwitch(input),parse(actual.encode()).get("switch"));
        assertThrows(IllegalArgumentException.class,()->observe(input.deepCopy().put("widget_count",8)));
        refuses(tree->target(tree).put("vtable_rva",0x61c5000-111));refuses(tree->target(tree).put("runtime_name","x".repeat(128)));
    }
    @Test void sharedFixtureFeedsSoleAckContractAndIndependentLaterSourceObservation(){
        Binding context=binding();var before=MilitaryReceiverProof.observeFixedReinforcement(MilitaryReceiverFixture.census(context,0,65),context);
        RawJson ack=MilitaryReceiverFixture.acknowledgement(Control.ENABLE_REINFORCEMENT,context,before);
        assertEquals(ack,MilitaryControlContract.acknowledgement(Control.ENABLE_REINFORCEMENT,context,ack,Optional.of(before)));
        assertTrue(parse(ack).get("verification_pending").booleanValue());assertFalse(parse(ack).get("postcondition_verified").booleanValue());
        var later=MilitaryReceiverProof.observeFixedReinforcement(MilitaryReceiverFixture.census(context,1,66),context);MilitaryControlContract.requireLater(before,later);
        assertTrue(later.sourceSwitch().enabled());var same=MilitaryReceiverFixture.acknowledgement(Control.ENABLE_REINFORCEMENT,context,later);
        assertEquals(same,MilitaryControlContract.acknowledgement(Control.ENABLE_REINFORCEMENT,context,same,Optional.of(later)));
        assertFalse(parse(same).get("dispatch_invoked").booleanValue());assertFalse(parse(same).get("dispatch_attempted").booleanValue());
        assertThrows(IllegalArgumentException.class,()->MilitaryControlContract.requireLater(before,before));
    }

    /** Requires actual old-Python helper output. Pure Java fixture success cannot replace this producer-to-consumer proof. */
    @Test void actualOriginalPythonNormalizerAndObserverOutputsMatchJava()throws Exception {
        String input=System.getProperty("xar.military.receiver.python.golden"),expected=System.getProperty("xar.military.receiver.python.golden.sha256");
        if(input==null||expected==null)throw new IOException("MISSING_NOT_RUN: original Python military callback/receiver normalizer golden and SHA are required");
        assertTrue(expected.matches("[0-9a-f]{64}"));Path path=Path.of(input);assertTrue(Files.isRegularFile(path));
        assertTrue(Files.size(path)>0&&Files.size(path)<=8*1024*1024);byte[] bytes=Files.readAllBytes(path);
        assertEquals(expected,HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)));
        ObjectNode golden=object(DriverJson.toNode(DriverJson.object(bytes,8*1024*1024)));assertEquals(Set.of("schema","machine_id","observed_at_utc","producer_sources","cases"),fields(golden));
        assertEquals("xar.military-receiver-original-python-golden/v1",golden.get("schema").textValue());assertFalse(golden.get("machine_id").textValue().isBlank());Instant.parse(golden.get("observed_at_utc").textValue());
        assertTrue(golden.get("producer_sources").isArray());Set<String> producerHashes=new HashSet<>();for(JsonNode source:golden.get("producer_sources")){
            assertEquals(Set.of("path","bytes","sha256"),fields(object(source)));assertTrue(source.get("path").isTextual());assertTrue(source.get("bytes").isIntegralNumber()&&source.get("bytes").bigIntegerValue().signum()>0);
            producerHashes.add(source.get("sha256").textValue());}
        assertTrue(producerHashes.containsAll(Set.of("399357ce80e15d61b6e317fe4e8e5e47cc99f54118ad7d9468421cf1383be6f9",
                "eb865e4db2e13531c241cec070c04fdf132cc3d52e676b71e5d96c2af1f4b2c2","b385f39eb3ede1a5ee522d581b31320dd2f0b70e637b1079d2a59b70bce07075")),"actual helper and unit-census producer sources must be pinned");
        for(OriginalSource expectedSource:List.of(
                new OriginalSource("gui_callback_binding_12004_contract.py",8556,"399357ce80e15d61b6e317fe4e8e5e47cc99f54118ad7d9468421cf1383be6f9"),
                new OriginalSource("gui_refill_receiver_candidates_12004_contract.py",28845,"eb865e4db2e13531c241cec070c04fdf132cc3d52e676b71e5d96c2af1f4b2c2"),
                new OriginalSource("gui_window_tree_contract.py",2934,"f61b03cde90823d7a9a178ec7bcf37e9d702dc2bb1287d8ec6b706fb00ab6060"),
                new OriginalSource("frontend_gui_route_contract.py",48401,"a1c938b59aab6ac1e18889bf874e14708615ec4fc4fb6b4069c58c626e94c2c9"),
                new OriginalSource("military_reinforcement_12004_contract.py",10847,"e35aa7531cc17498e703b282fef17361b35989f2593bcbceb878d3e28e24179d"),
                new OriginalSource("test_military_reinforcement_12004.py",12805,"b385f39eb3ede1a5ee522d581b31320dd2f0b70e637b1079d2a59b70bce07075"))){
            int count=0;for(JsonNode source:golden.get("producer_sources"))if(source.get("path").textValue().replace('\\','/').endsWith("/"+expectedSource.file())){
                assertEquals(BigInteger.valueOf(expectedSource.bytes()),source.get("bytes").bigIntegerValue());assertEquals(expectedSource.sha256(),source.get("sha256").textValue());count++;}
            assertEquals(1,count,"each original producer file has one exact recorded identity");}
        assertTrue(golden.get("cases").isArray()&&golden.get("cases").size()==4);Set<String> cases=new HashSet<>();
        for(JsonNode value:golden.get("cases")){ObjectNode row=object(value);assertEquals(Set.of("name","raw_result","normalized","observation"),fields(row));assertTrue(cases.add(row.get("name").textValue()));
            var normalized=MilitaryReceiverProof.normalizeTree(raw(row.get("raw_result")),binding());assertEquals(row.get("normalized"),parse(normalized));
            assertEquals(row.get("observation"),parse(MilitaryReceiverProof.observeFixedReinforcement(normalized,binding()).encode()));}
        assertEquals(Set.of("byte_0","byte_1","byte_255","null_military"),cases);
    }
    private record OriginalSource(String file,long bytes,String sha256){ }
    private static void assertJsonEquals(JsonNode expected,JsonNode actual){assertEquals(parse(raw(expected)),parse(raw(actual)));}
    private static Set<String> fields(ObjectNode object){Set<String> result=new HashSet<>();object.fieldNames().forEachRemaining(result::add);return result;}
}
