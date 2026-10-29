package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import static org.xar.ck3.control.service.root.RootDriverLifecycleResumeCodec.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.PublicDataJson;
import org.xar.ck3.control.application.driver.PublicSnapshotCodec;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.service.mcp.*;
import org.xar.ck3.control.wave2.governance.succession.SuccessionCodec;
import org.xar.ck3.control.wave2.governance.succession.SuccessionModel;
import org.xar.ck3.control.wave3.governance.lifecycle.SuccessionLifecycleBinding;
import org.xar.ck3.control.wave3.governance.lifecycle.SuccessionLifecycleCodec;

/** Original Python functions and real pure M3/Lifecycle serializers produce DATA fixtures. None of
 * these fixtures constructs a private Root, Complete, retained source, runtime cause or permission. */
public final class RootDriverLifecycleResumeCodecTest {
    private static final BigInteger MAX=new BigInteger("18446744073709551615");
    /** Mandatory actual Root fixture hook. Caller supplies its genuine installed Complete and private
     * Inputs. This performs the original read once; it creates no fixture or replacement authority. */
    public static Data assertActualResume(McpExecutableDirectory.Complete actualComplete,
            RootRuntimeDefinitions.Inputs actualInputs,java.time.Clock clock,PublicMcpDirectory.ToolCall actualCall)throws Exception {
        actualInputs.originalMcpSources(clock);assertEquals(PublicMcpDirectory.Scope.COMPLETE_MIGRATION,actualComplete.directory().scope());
        assertEquals("ck3_resume_successor_ui_v1",actualCall.name());var descriptor=actualComplete.directory().tools().stream().filter(value->value.name().equals(actualCall.name())).findFirst().orElseThrow();descriptor.validateArguments(actualCall.arguments());
        var result=actualComplete.directory().invoke(actualCall);descriptor.validateResult(result);Obj envelope=DriverJson.object(result.bytes(),RawJson.MAXIMUM_BYTES);
        assertEquals(new Bool(false),envelope.get("isError"));Obj business=object(envelope.get("structuredContent"),"actual resume result");
        Obj content=object(array(envelope.get("content"),"content").getFirst(),"actual text");assertEquals(business,DriverJson.object(text(content.get("text"),"text").getBytes(StandardCharsets.UTF_8),RawJson.MAXIMUM_BYTES));
        Data decoded=decode(json(business));assertEquals(business,parse(encode(decoded)));actualInputs.originalMcpSources(clock);return decoded;
    }
    @Test void originalFiveResumeBranchesReachTheSameProductionBinderAndWholeMcpResult()throws Exception {
        Obj corpus=originalCases();var descriptor=descriptor("ck3_resume_successor_ui_v1");
        for(Value value:array(corpus.get("cases"),"original cases")) {
            Obj actual=object(value,"actual original case"),expected=object(actual.get("result"),"original result");
            ResumeResult material=material(expected);var calls=new AtomicInteger();
            var binding=RootDriverLifecyclePublicSupplier.resumeBinding(compiledSupplier(),request->{calls.incrementAndGet();return material;});
            var input=PublicDataJson.object(raw("{\"expected_revision\":\"18446744073709551615\"}"));
            var args=new PublicMcpDirectory.Arguments(PublicMcpDirectory.Presence.VALUE,Optional.of(PublicDataJson.encode(input)));
            descriptor.validateArguments(args);var call=new PublicMcpDirectory.ToolCall(binding.name(),args,Optional.empty(),new McpCancellation());
            var request=binding.decoder().decode(call);var result=binding.encoder().encode(binding.actual().invoke(request));descriptor.validateResult(result);assertEquals(1,calls.get());
            Obj envelope=DriverJson.object(result.bytes(),RawJson.MAXIMUM_BYTES);Obj business=object(envelope.get("structuredContent"),"business");
            Obj text=DriverJson.object(((Text)object(array(envelope.get("content"),"content").getFirst(),"text").get("text")).value().getBytes(StandardCharsets.UTF_8),RawJson.MAXIMUM_BYTES);
            assertEquals(business,text);assertEquals(expected,restoreReadOnlyPublic(business));
            var encoded=json(business);assertEquals(business,parse(encode(decode(encoded))));assertEquals(parse(material.originalNumericSnapshot()),parse(decode(encoded).originalNumericSnapshot()));
            assertEquals(number(0),actual.get("close_calls"));assertEquals(actual.get("reads"),actual.get("expected_reads"));
        }
    }
    @Test void prefinalMatchedCauseNeverBecomesVerifiedClearOrDateCreditAndMalformedPublicDataRefuses() {
        var transition=transition(Qualification.CAUSE_QUALIFIED,Optional.empty());
        var diagnosis=new Diagnostic("actual final publication and Goal are still pending",List.of(new Failure("actual_pending_stage","finalization_pending","actual cause is retained",Optional.empty(),Optional.empty())));
        var pending=new ResumeResult(Status.UI_UNRESOLVED,true,false,false,snapshot(),Optional.of(transition),Optional.empty(),Optional.of(diagnosis));
        Obj result=parse(encode(pending));assertEquals(new Text("cause_qualified"),object(result.get("transition"),"transition").get("status"));assertEquals(new Bool(false),result.get("action_submitted"));assertFalse(result.members().containsKey("date_advanced"));
        assertThrows(IllegalArgumentException.class,()->new ResumeResult(Status.CLEAR,false,false,false,snapshot(),Optional.of(transition),Optional.empty(),Optional.empty()));
        assertThrows(IllegalArgumentException.class,()->new ResumeResult(Status.UI_UNRESOLVED,true,false,true,snapshot(),Optional.of(transition),Optional.empty(),Optional.of(diagnosis)));
        for(String bad:List.of("1","true","1.0","null","\"01\"","\"18446744073709551616\"")) {
            Obj t=object(result.get("transition"),"transition"),b=object(t.get("successor_episode_binding"),"binding");
            Obj wrong=result.with("transition",t.with("successor_episode_binding",b.with("revision",DriverJson.object(("{\"v\":"+bad+"}").getBytes(StandardCharsets.UTF_8),1024).get("v"))));
            assertThrows(IllegalArgumentException.class,()->decode(json(wrong)));
        }
        assertThrows(IllegalArgumentException.class,()->decode(json(result.with("alias",new Bool(true)))));
        assertThrows(IllegalArgumentException.class,()->decode(json(result.with("pending",number(1)))));
    }
    @Test void completeNumericSnapshotRetainsHistoryDecimalTokensAndExceedsSemanticOnlyEightMiBWithoutLosingFields() {
        Obj original=parse(snapshot()).with("native_command_history",new Arr(List.of(new Obj(Map.of("opaque",new DecimalValue("-0.0"))),new DecimalValue("1.0"),new Arr(List.of(new DecimalValue("-0.0"),Nil.INSTANCE,new Text("opaque"))))));
        original=original.with("opaque_long_decimal",new DecimalValue("0."+"0".repeat(5000)+"1")).with("original_metric",new DecimalValue("1.0")).with("large_original_extension",new Text("x".repeat(8*1024*1024+1)));
        var actual=clear(json(original));RawJson publicWire=encode(actual);assertTrue(publicWire.bytes().length>8*1024*1024);
        Data data=decode(publicWire);assertEquals(original,parse(data.originalNumericSnapshot()));assertEquals(parse(publicWire),parse(encode(data)));
        assertEquals(java.util.Set.of("status","pending","snapshot","transition"),parse(publicWire).members().keySet());
        Obj unknown=original.with("unknown_wide_identity",new IntegerValue(MAX));assertThrows(IllegalArgumentException.class,()->clear(json(unknown)));
        byte[] complete=PublicDataJson.encodeTypedBytes(original,RawJson.MAXIMUM_BYTES);assertThrows(IllegalArgumentException.class,()->new RawJson(complete));assertThrows(IllegalArgumentException.class,()->RawJson.fullMaterial(complete).requireProtocolBound());
    }
    @Test void actualThreeOriginalDescriptorsReachTheSharedPresenceCodecAndRejectNumericAliases()throws Exception {
        for(String name:List.of("ck3_resume_successor_ui_v1","ck3_query_current_timeline_blocker_context_v1","ck3_continue_death_succession_modal_v1")) {
            var original=original(name);var projected=RootPublicCatalogCodec.executableTool(original);boolean resume=name.equals("ck3_resume_successor_ui_v1"),close=name.equals("ck3_continue_death_succession_modal_v1");
            var input=org.xar.ck3.control.contracts.StrictJson.object().put("expected_revision",MAX.toString());if(close)input.put("expected_played_character_id",12).put("expected_episode_run_id","new");
            var args=arguments(PublicDataJson.encode(input));assertThrows(IllegalArgumentException.class,()->original.validateArguments(args));projected.validateArguments(args);
            PublicBindings.Arguments typed=PublicBindings.present(PublicDataJson.encode(input));PublicBindings.Arguments roundtrip;
            if(resume)roundtrip=RootDriverLifecyclePublicCodec.encode(RootDriverLifecyclePublicCodec.resume(typed));else if(close)roundtrip=RootDriverLifecyclePublicCodec.encode(RootDriverLifecyclePublicCodec.close(typed));else roundtrip=RootDriverLifecyclePublicCodec.encode(RootDriverLifecyclePublicCodec.query(typed));
            projected.validateArguments(arguments(((PublicBindings.Value)roundtrip).original()));
            for(String bad:List.of("0","1","true","1.0","\"01\"","\"18446744073709551616\"")) {var wrong=input.deepCopy();wrong.set("expected_revision",PublicDataJson.object(raw("{\"v\":"+bad+"}")).get("v"));assertThrows(IllegalArgumentException.class,()->projected.validateArguments(arguments(PublicDataJson.encode(wrong))));}
            var missing=input.deepCopy();missing.remove("expected_revision");var explicitNull=missing.deepCopy().putNull("expected_revision");
            if(resume)for(var value:List.of(missing,explicitNull)){projected.validateArguments(arguments(PublicDataJson.encode(value)));var request=RootDriverLifecyclePublicCodec.resume(PublicBindings.present(PublicDataJson.encode(value)));var encoded=RootDriverLifecyclePublicCodec.encode(request);assertEquals(value,PublicDataJson.object(((PublicBindings.Value)encoded).original()));}
            else {assertThrows(IllegalArgumentException.class,()->projected.validateArguments(arguments(PublicDataJson.encode(missing))));assertThrows(IllegalArgumentException.class,()->projected.validateArguments(arguments(PublicDataJson.encode(explicitNull))));}
        }
    }
    @Test void actualExecuteDescriptorAcceptsTheOwnerCanonicalRevisionAndExactEightFieldH2743Data()throws Exception {
        var original=original("ck3_execute_step");var projected=RootPublicCatalogCodec.executableTool(original);
        var input=org.xar.ck3.control.contracts.StrictJson.object().put("step",PublicPlanningCodec.H2743_STEP).put("expected_revision",MAX.toString());
        var frame=input.putObject("expected_h2743_frame").put("snapshot_id","native:"+MAX).put("episode_run_id","native-29829-2bc2d599f7f9").put("date_raw",53217264).put("actor_character_id",29829).put("war_id",16777231);
        for(String field:List.of("revision","native_revision","connection_generation"))frame.put(field,MAX.toString());
        assertThrows(IllegalArgumentException.class,()->original.validateArguments(arguments(PublicDataJson.encode(input))));projected.validateArguments(arguments(PublicDataJson.encode(input)));
        var request=PublicPlanningCodec.decodeExecute(PublicBindings.present(PublicDataJson.encode(input)));var encoded=PublicPlanningCodec.encodeExecute(request);
        projected.validateArguments(arguments(encoded));assertEquals(request,PublicPlanningCodec.decodeExecute(PublicBindings.present(encoded)));
        assertEquals(PublicDataJson.object(original.original()).get("inputSchema").get("properties").get("step"),PublicDataJson.object(projected.original()).get("inputSchema").get("properties").get("step"));
        for(String field:List.of("revision","native_revision","connection_generation"))for(String bad:List.of("true","1.0","9007199254740992","\"0\"","\"01\"","\"18446744073709551616\"")) {
            var wrong=input.deepCopy();((com.fasterxml.jackson.databind.node.ObjectNode)wrong.get("expected_h2743_frame")).set(field,PublicDataJson.object(raw("{\"v\":"+bad+"}")).get("v"));
            assertThrows(IllegalArgumentException.class,()->projected.validateArguments(arguments(PublicDataJson.encode(wrong))));assertThrows(IllegalArgumentException.class,()->PublicPlanningCodec.decodeExecute(PublicBindings.present(PublicDataJson.encode(wrong))));
        }
        for(String missing:List.of("snapshot_id","revision","native_revision","date_raw","actor_character_id","episode_run_id","war_id","connection_generation")) {var wrong=input.deepCopy();((com.fasterxml.jackson.databind.node.ObjectNode)wrong.get("expected_h2743_frame")).remove(missing);assertThrows(IllegalArgumentException.class,()->projected.validateArguments(arguments(PublicDataJson.encode(wrong))));}
        for(boolean revisionNull:List.of(false,true))for(boolean frameNull:List.of(false,true)) {
            var ordinary=org.xar.ck3.control.contracts.StrictJson.object().put("step","life-advance-one-day");if(revisionNull)ordinary.putNull("expected_revision");if(frameNull)ordinary.putNull("expected_h2743_frame");
            projected.validateArguments(arguments(PublicDataJson.encode(ordinary)));var parsed=PublicPlanningCodec.decodeExecute(PublicBindings.present(PublicDataJson.encode(ordinary)));var roundtrip=PublicPlanningCodec.encodeExecute(parsed);assertEquals(ordinary,PublicDataJson.object(roundtrip));
        }
        // This is DATA only. The actual fixed date/WarID/source before-guard is still required at runtime.
    }
    @Test void publicCloseActorAndEpisodeAreStrictRequiredFieldsAtDescriptorAndActualDecoder()throws Exception {
        var projected=descriptor("ck3_continue_death_succession_modal_v1");
        var valid=org.xar.ck3.control.contracts.StrictJson.object().put("expected_revision",MAX.toString())
                .put("expected_played_character_id",12).put("expected_episode_run_id","new");
        for(String field:List.of("expected_played_character_id","expected_episode_run_id")) {
            var missing=valid.deepCopy();missing.remove(field);
            assertThrows(IllegalArgumentException.class,()->projected.validateArguments(arguments(PublicDataJson.encode(missing))));
            assertThrows(IllegalArgumentException.class,()->RootDriverLifecyclePublicCodec.close(PublicBindings.present(PublicDataJson.encode(missing))));
            for(String token:field.equals("expected_played_character_id")?List.of("null","true","false","12.0","\"12\"","0","-1","2147483648"):List.of("null","true","12","\"\"")) {
                var wrong=valid.deepCopy();wrong.set(field,PublicDataJson.object(raw("{\"v\":"+token+"}")).get("v"));
                assertThrows(IllegalArgumentException.class,()->projected.validateArguments(arguments(PublicDataJson.encode(wrong))));
                assertThrows(IllegalArgumentException.class,()->RootDriverLifecyclePublicCodec.close(PublicBindings.present(PublicDataJson.encode(wrong))));
            }
        }
        var decoded=RootDriverLifecyclePublicCodec.close(PublicBindings.present(PublicDataJson.encode(valid)));
        assertEquals(valid,PublicDataJson.object(((PublicBindings.Value)RootDriverLifecyclePublicCodec.encode(decoded)).original()));
    }
    @Test void clearResumeCannotAcquirePendingTransitionOrDropItsOriginalNullField() {
        Obj actual=parse(encode(clear(snapshot())));
        assertEquals(java.util.Set.of("status","pending","snapshot","transition"),actual.members().keySet());
        assertSame(Nil.INSTANCE,actual.get("transition"));
        var omitted=new java.util.LinkedHashMap<>(actual.members());omitted.remove("transition");
        assertThrows(IllegalArgumentException.class,()->decode(json(new Obj(omitted))));
        assertThrows(IllegalArgumentException.class,()->decode(json(actual.with("cold_resume_binding",Nil.INSTANCE))));
        assertThrows(IllegalArgumentException.class,()->decode(json(actual.with("pending",Nil.INSTANCE))));
        assertThrows(IllegalArgumentException.class,()->decode(json(actual.with("pending",number(0)))));
        assertEquals(actual,parse(encode(decode(json(actual)))));
    }
    @Test void originalCloseValueErrorsKeepTheirTypedCauseThroughTheActualBinderDirectoryAndBothRpcPeers()throws Exception {
        String arguments="{\"expected_revision\":\"18446744073709551615\",\"expected_played_character_id\":12,\"expected_episode_run_id\":\"new\"}";
        var expected=List.of("successor typed Close requires the App's verified pending transition",
                "successor typed Close request differs from its actual successor","successor UI has no currently legal verified modal Close");
        var reasons=RootPendingUiRuntime.CloseFailure.values();
        for(int index=0;index<reasons.length;index++){
            var actual=RootPendingUiRuntime.publicCloseFailure(reasons[index]);assertEquals(expected.get(index),actual.getMessage());
            var binding=RootDriverLifecyclePublicSupplier.closeBinding(compiledSupplier(),request->{throw actual;});
            PublicLifecycleRpcAssertions.assertDirectFailure(binding,arguments,actual);
        }
        // The retained Close consumer must inspect the actual resumed result. An old
        // archived Close elsewhere cannot supply a result absent from this resume.
        var clearFailure=assertThrows(PublicServiceFailure.class,()->RootPendingUiRuntime.retainedResumeCloseMaterial(clear(snapshot())));
        assertEquals(expected.get(2),clearFailure.getMessage());
    }
    private static ResumeResult material(Obj result) {
        Obj t=result.get("transition")==Nil.INSTANCE?null:object(result.get("transition"),"transition");
        Optional<TransitionMaterial> transition=Optional.empty();if(t!=null) {
            Optional<TimelineContinuation> continuation=Optional.empty();if(t.members().containsKey("timeline_blocker_continuation")){Obj row=object(t.get("timeline_blocker_continuation"),"continuation");continuation=Optional.of(new TimelineContinuation(text(row.get("status"),"status"),json(object(row.get("initial_query"),"query")),Optional.empty(),Optional.empty(),Optional.empty(),Optional.empty(),row.members().containsKey("ui_clearance_verified")?Optional.of(((Bool)row.get("ui_clearance_verified")).value()):Optional.empty(),Optional.empty()));}
            transition=Optional.of(new TransitionMaterial(Qualification.VERIFIED,integer(t.get("predecessor_character_id"),"predecessor").intValueExact(),integer(t.get("successor_character_id"),"successor").intValueExact(),text(t.get("source_episode_run_id"),"source run"),text(t.get("episode_run_id"),"run"),integer(t.get("date_raw"),"date").intValueExact(),json(object(t.get("succession_lifecycle"),"lifecycle")),json(object(t.get("reconciliation"),"M3")),json(object(t.get("predecessor_binding"),"before")),json(object(t.get("successor_episode_binding"),"after")),continuation,Optional.empty()));
        }
        Optional<Diagnostic> diagnostic=Optional.empty();if(result.members().containsKey("diagnostic")){Obj d=object(result.get("diagnostic"),"diagnostic");var failures=new ArrayList<Failure>();for(Value value:array(d.get("failures"),"failures")){Obj f=object(value,"failure");failures.add(new Failure(text(f.get("stage"),"stage"),text(f.get("kind"),"kind"),text(f.get("message"),"message"),f.members().containsKey("error_type")?Optional.of(text(f.get("error_type"),"class")):Optional.empty(),f.members().containsKey("error")?Optional.of(text(f.get("error"),"error")):Optional.empty()));}diagnostic=Optional.of(new Diagnostic(text(d.get("error"),"error"),failures));}
        return new ResumeResult(Status.parse(text(result.get("status"),"status")),((Bool)result.get("pending")).value(),result.get("player_decision_pending") instanceof Bool value&&value.value(),result.get("date_advanced") instanceof Bool value&&value.value(),json(object(result.get("snapshot"),"snapshot")),transition,Optional.empty(),diagnostic);
    }
    static TransitionMaterial transition(Qualification q,Optional<TimelineContinuation> timeline){return new TransitionMaterial(q,11,12,"old","new",4,lifecycle(),reconciliation(),binding(false),binding(true),timeline,Optional.empty());}
    private static RawJson lifecycle(){return new RawJson(SuccessionLifecycleCodec.encode(new SuccessionLifecycleBinding(SuccessionLifecycleBinding.Profile.ORDINARY_FROZEN_OFF,"software-original-material","a".repeat(64))));}
    private static RawJson reconciliation(){var frame=new SuccessionModel.Frame("snapshot",MAX,MAX,4);return new RawJson(SuccessionCodec.encodeReconciliation(new SuccessionModel.Reconciliation(new SuccessionModel.Binding(frame,"old",11),frame,11,12,12,true,List.of(7),List.of(7),List.of(),List.of(),List.of(),List.of(),List.of(),true,SuccessionModel.Verdict.MATCHED)));}
    private static RawJson binding(boolean successor){return raw("{\"snapshot_id\":\"snapshot\",\"revision\":"+MAX+",\"native_revision\":"+MAX+",\"date_raw\":4,\"episode_run_id\":\""+(successor?"new":"old")+"\",\"episode_character_id\":"+(successor?12:11)+",\"one_life_terminal\":"+(!successor)+",\"one_life_terminal_reason\":"+(successor?"null":"\"played_character_changed\"")+",\"played_character_id\":12,\"played_character_alive\":true,\"episode_binding_state\":"+(successor?"\"active_natural_successor\"":"null")+",\"driver_state_restore_kind\":"+(successor?"\"natural_succession\"":"null")+",\"bridge_pid\":7,\"connection_generation\":"+MAX+"}");}
    static RawJson snapshot(){return raw("{\"format_version\":1,\"snapshot_id\":\"snapshot\",\"revision\":"+MAX+",\"native_revision\":"+MAX+",\"date_raw\":4,\"paused\":true,\"map_ready\":true,\"speed\":1,\"episode_run_id\":\"new\",\"episode_character_id\":12,\"played_character\":{\"character_id\":12,\"alive\":true},\"active_wars\":[],\"player_armies\":[],\"diagnostics\":{\"bridge_pid\":7,\"connection_generation\":"+MAX+"},\"active_event\":null,\"pending_character_interaction\":null,\"one_life_terminal\":false,\"one_life_terminal_reason\":null,\"native_command_history\":[{\"original_metric\":-0.0},[1.0,null]],\"original_metric\":1.0}");}
    private static Obj restoreReadOnlyPublic(Obj row) {
        row=row.with("snapshot",parse(PublicSnapshotCodec.decodeSemanticData(json(object(row.get("snapshot"),"snapshot")))));
        if(row.get("transition")!=Nil.INSTANCE){Obj t=object(row.get("transition"),"transition");for(String field:List.of("predecessor_binding","successor_episode_binding"))t=t.with(field,numeric(object(t.get(field),"binding"),List.of("revision","native_revision","connection_generation")));Obj estate=object(t.get("reconciliation"),"M3");for(String field:List.of("predecessor_binding","successor_binding"))estate=estate.with(field,numeric(object(estate.get(field),"M3 binding"),List.of("revision","native_revision")));t=t.with("reconciliation",estate);if(t.members().containsKey("timeline_blocker_continuation")){Obj c=object(t.get("timeline_blocker_continuation"),"continuation");assertEquals(Nil.INSTANCE,c.get("close_result"),"read-only original oracle must never submit Close");c=c.with("initial_query",parse(RootDriverLifecyclePublicCodec.decodeTimelineOriginal(json(object(c.get("initial_query"),"query")))));t=t.with("timeline_blocker_continuation",c);}row=row.with("transition",t);}return row;
    }
    private static Obj numeric(Obj row,List<String> fields){for(String field:fields){assertInstanceOf(Text.class,row.get(field));row=row.with(field,new IntegerValue(new BigInteger(text(row.get(field),field))));}return row;}
    private static PublicMcpDirectory.ToolDescriptor original(String name)throws Exception{return RootOriginalPublicTestInputs.tools().stream().filter(value->value.name().equals(name)).findFirst().orElseThrow(()->new IllegalStateException("NOT_RUN_REQUIRED_ACTUAL_ORIGINAL_TOOL: "+name));}
    private static PublicMcpDirectory.ToolDescriptor descriptor(String name)throws Exception{return RootPublicCatalogCodec.executableTool(original(name));}
    private static PublicMcpDirectory.Arguments arguments(RawJson value){return new PublicMcpDirectory.Arguments(PublicMcpDirectory.Presence.VALUE,Optional.of(value));}
    static RawJson raw(String value){return new RawJson(value.getBytes(StandardCharsets.UTF_8));}
    private static RawJson json(Value value){return PublicDataJson.encodeFullMaterial(value);}
    private static Obj parse(RawJson value){return DriverJson.object(value.bytes(),RawJson.MAXIMUM_BYTES);}
    private static IntegerValue number(long value){return new IntegerValue(BigInteger.valueOf(value));}
    private static ExactRef compiledSupplier()throws Exception {String base=System.getProperty("basedir");assertNotNull(base,"NOT_RUN_REQUIRED_ACTUAL_MAVEN_BASEDIR");Path root=Path.of(base),target=root.resolve("src/main/java/org/xar/ck3/control/service/root/RootDriverLifecyclePublicSupplier.java");if(!Files.isRegularFile(target))target=root.resolve("local-service/src/main/java/org/xar/ck3/control/service/root/RootDriverLifecyclePublicSupplier.java");var actual=SharedSourceFiles.observe(target).source();return new ExactRef(actual.path(),actual.bytes(),actual.sha256());}
    private static Obj originalCases()throws Exception {
        String python=System.getProperty("xar.python"),repository=System.getProperty("xar.repository.root");assertNotNull(python,"NOT_RUN_REQUIRED_ORIGINAL_PYTHON");assertNotNull(repository,"NOT_RUN_REQUIRED_ORIGINAL_REPOSITORY");
        Path root=Path.of(repository);String[] names={"src/xar_autoplayer/bridge/successor_ui_app_owner_v1.py","src/xar_autoplayer/successor_ui_owner_continuation_v1.py","src/xar_autoplayer/native_auto_run.py","tests/unit/test_death_succession_modal_private_transport.py","src/xar_autoplayer/errors.py","src/xar_autoplayer/bridge/driver.py"};
        String[] hashes={"a1af05519d8b514ee91a7a4a7d037cf5da006e05bb1bdfdb32185ddb7a65f071","7b8d49d16bee5d60d604c20d7aef3679ffeb697fe98bef9d0bb72e1400909cfd","39c928ba26ee74c0b74d41b873d252cd6697a8995746e44816b54e96fec31a04","96db174a3a27eb44005b388729474039d932f48ef55f8e181de42166edcbecf3","8baedaca3d7f38b485d132503a3ddefd33e70a6089cb93b485d052d017c2a3b2","eed449063debf1a84216a350f0178d64a9a6602bbfcc266298a810a9bb736fb6"};
        var pins=new ArrayList<SharedSourceFiles.Witness>();for(int index=0;index<names.length;index++){var pin=SharedSourceFiles.observe(root.resolve("ck3_autonomous_player").resolve(names[index]));assertEquals(hashes[index],pin.source().sha256());pins.add(pin);}
        String program="""
                import ast,copy,json,pathlib,sys,threading,types,uuid,time
                from collections.abc import Mapping
                root=pathlib.Path(sys.argv[1]);src=root/'ck3_autonomous_player/src';sys.path.insert(0,str(src))
                from xar_autoplayer.errors import AgentError
                from xar_autoplayer.bridge.driver import BridgeUnavailableError,UnsupportedStepError
                package=src/'xar_autoplayer';data=json.load(sys.stdin)
                ns=dict(copy=copy,deepcopy=copy.deepcopy,Mapping=Mapping,json=json,uuid=uuid,time=time,AgentError=AgentError,BridgeUnavailableError=BridgeUnavailableError,UnsupportedStepError=UnsupportedStepError,CONTINUE_AS_RECONCILED_SUCCESSOR_STEP='continue-as-reconciled-successor',QUERY_CURRENT_TIMELINE_BLOCKER_CONTEXT_V1_STEP='query-current-timeline-blocker-context-v1',CONTINUE_DEATH_SUCCESSION_MODAL_V1_STEP='continue-death-succession-modal-v1')
                def functions(path,names):
                    tree=ast.parse(path.read_text(encoding='utf-8-sig'),filename=str(path));nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
                    assert len(nodes)==len(names);exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),ns)
                functions(package/'native_auto_run.py',{'_verify_natural_succession_transition','_public_binding','_timeline_typed_boolean','_ordinary_succession_timeline_state','_ordinary_succession_close_issue'})
                functions(package/'successor_ui_owner_continuation_v1.py',{'continue_verified_successor_ui_v1'})
                ownerpath=package/'bridge/successor_ui_app_owner_v1.py';tree=ast.parse(ownerpath.read_text(encoding='utf-8-sig'),filename=str(ownerpath));owner=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='SuccessorUIAppOwner');resume=next(n for n in owner.body if isinstance(n,ast.FunctionDef) and n.name=='resume');exec(compile(ast.Module(body=[resume],type_ignores=[]),str(ownerpath),'exec'),ns)
                fixture=root/'ck3_autonomous_player/tests/unit/test_death_succession_modal_private_transport.py';tree=ast.parse(fixture.read_text(encoding='utf-8-sig'),filename=str(fixture));nodes=[n for n in tree.body if isinstance(n,ast.Assign) or isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in ('_snapshot','_timeline','_Endpoint','_State')];exec(compile(ast.Module(body=nodes,type_ignores=[]),str(fixture),'exec'),ns)
                ns.update(NATIVE_REVISION=data['snapshot']['native_revision'],PUBLIC_REVISION=data['snapshot']['revision'],DATE_RAW=data['snapshot']['date_raw'],CHARACTER_ID=12,EPISODE_RUN_ID='new')
                result=dict(step='continue-as-reconciled-successor',accepted=True,status='continued',source='native-played-character-transition',lifecycle_intent='natural_succession',succession_lifecycle=data['lifecycle'],predecessor_character_id=11,successor_character_id=12,source_episode_run_id='old',episode_run_id='new',continue_as_heir_after_death=True,heir_gameplay_actions=0,ck3_command_submitted=False,process_restarted=False,reconciliation=data['reconciliation'])
                verified=ns['_verify_natural_succession_transition'](result,snapshot=data['snapshot'],binding=data['after'],before=data['before'],succession_lifecycle=data['lifecycle'])
                cases=[]
                for mode in ('clear','close','decision','resolved','unavailable'):
                    snapshot=copy.deepcopy(data['snapshot']);transition=copy.deepcopy(verified);counts=dict(reads=0,close=0,writes=0)
                    if mode=='decision':snapshot['pending_character_interaction']={'instance_id':1}
                    endpoint=ns['_Endpoint']();state=ns['_State'](endpoint,query_identities=['death_succession_modal' if mode=='close' else 'none'])
                    def query(**arguments):
                        counts['reads']+=1
                        if mode=='unavailable':raise BridgeUnavailableError('fixture read failure')
                        endpoint.send(dict(step='query-current-timeline-blocker-context-v1',request_id='read'));return state.wait_for_command_result('read',1)['result']
                    def forbidden(*a,**k):counts['close']+=1;raise AssertionError('read-only resume submitted Close')
                    def write(*a,**k):counts['writes']+=1
                    ledger=types.SimpleNamespace(_issued_cold_binding=None,update=write,resolve=write)
                    owner=types.SimpleNamespace(lock=threading.RLock(),snapshot=lambda:copy.deepcopy(snapshot),pending=lambda:mode!='clear',_load=lambda current:transition,ledger=ledger,validators=types.SimpleNamespace(_ordinary_succession_timeline_state=ns['_ordinary_succession_timeline_state'],_ordinary_succession_close_issue=ns['_ordinary_succession_close_issue']),service=types.SimpleNamespace(query_current_timeline_blocker_context_v1=query,continue_death_succession_modal_private_v1=forbidden,observe_verified_successor_ui_v1=forbidden),before_submit=None,executing_close=False)
                    actual=ns['resume'](owner,expected_revision=snapshot['revision'],allow_close=False)
                    cases.append(dict(mode=mode,result=actual,reads=counts['reads'],expected_reads=0 if mode=='clear' else 1,close_calls=counts['close']))
                print(json.dumps(dict(cases=cases),sort_keys=True,separators=(',',':'),allow_nan=False))
                """;
        var childBuilder=new ProcessBuilder(python,"-c",program,repository).redirectErrorStream(true);childBuilder.environment().put("PYTHONDONTWRITEBYTECODE","1");childBuilder.environment().put("PYTHONIOENCODING","utf-8");childBuilder.environment().put("XAR_SOURCE_REPOSITORY",repository);
        var child=childBuilder.start();var output=java.util.concurrent.CompletableFuture.supplyAsync(()->{try{return child.getInputStream().readNBytes(1048577);}catch(java.io.IOException failure){throw new java.io.UncheckedIOException(failure);}});try {Obj input=new Obj(Map.of("snapshot",parse(snapshot()),"before",parse(binding(false)),"after",parse(binding(true)),"lifecycle",parse(lifecycle()),"reconciliation",parse(reconciliation())));try(var stream=child.getOutputStream()){stream.write(DriverJson.encode(input));}if(!child.waitFor(30,TimeUnit.SECONDS)){child.destroyForcibly();fail("original resume oracle timed out");}byte[] bytes=output.get(2,TimeUnit.SECONDS);assertTrue(bytes.length<=1048576);assertEquals(0,child.exitValue(),new String(bytes,StandardCharsets.UTF_8));return DriverJson.object(bytes,1048576);}finally{child.destroyForcibly();output.cancel(true);for(var pin:pins)SharedSourceFiles.assertUnchanged(pin);}
    }
}
