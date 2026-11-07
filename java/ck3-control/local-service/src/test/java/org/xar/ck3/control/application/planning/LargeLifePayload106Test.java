package org.xar.ck3.control.application.planning;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.lang.reflect.Field;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.math.BigInteger;
import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.zip.GZIPInputStream;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.advance.AdvancePlan;
import org.xar.ck3.control.application.advance.AdvanceProgress;
import org.xar.ck3.control.application.advance.ClockStatusRead;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.g2.m7.GoalCodec;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExternalFact;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExternalState;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.UnknownScope;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import org.xar.ck3.control.service.root.RootOnlineDecisionSelector;
import org.xar.ck3.control.service.root.RootOrdinaryRuntimeConfiguration.DecisionProvider;
import org.xar.ck3.control.wave2.planning.jointshortlist.JointShortlist.Domain;

/** Resource-backed actual formatter DATA and finite component benchmark. Expired commands never dispatch. */
public final class LargeLifePayload106Test {
    static final int LIMIT=FullJsonTree.MAXIMUM_BYTES;
    static final String RECONSTRUCTION="WIRE_EQUIVALENT_PROJECTION_RECONSTRUCTION_NOT_ROOT_AUTHORITY";
    record Data(PlanningRequest request,PlanningResult.ActionSelected selected,JsonNode originalModel,
            RootOnlineDecisionSelector selector,String commandSha,int normalizedOldOperationNames,int historyStructuralDifferences) { }
    LargeLifePayload106Test(){ }

    private static Data actual;
    private static final String SUBSET_POLICY=" Only snapshot.diagnostics.hello.capabilities is projected to this Life intent's required subset of the actual advertised registry. The complete registry remains in Java; all other current facts and unknown diagnostics remain supplied.";

    @org.junit.jupiter.api.BeforeAll static void loadActualProjection()throws Exception {
        actual=load(gzipResource("/org/xar/ck3/control/application/planning/payload106/request.json.gz"),
                gzipResource("/org/xar/ck3/control/application/planning/payload106/batch29.jsonl.gz"),
                gzipResource("/org/xar/ck3/control/application/checkpoint/encoding102/driver1475.json.gz"));
    }

    @org.junit.jupiter.api.Test void actualLargeLifeRegistryOverflowRetainsAllOtherExportedData()throws Exception {
        byte[] before=FullJsonTree.encode(OpportunityJson.toNode(actual.request().observations().snapshot()),LIMIT);
        byte[] history=FullJsonTree.encode(OpportunityJson.toNode(new OpportunityJson.Arr(new ArrayList<OpportunityJson.Value>(actual.request().observations().history()))),LIMIT);
        byte[] command=ActionCodec.encodeCommand(actual.selected().command());
        byte[] wire=payload(actual);
        org.junit.jupiter.api.Assertions.assertEquals(60559,wire.length);
        ObjectNode expected=taskWithoutDuplicateHistory(actual);
        var required=required("requiredLifeCapabilities",AdvancePlan.decode(actual.selected().command()));
        ArrayNode caps=JsonNodeFactory.instance.arrayNode();required.stream().sorted().forEach(caps::add);
        ((ObjectNode)expected.path("snapshot").path("diagnostics").path("hello")).set("capabilities",caps);
        expected.put("hello_capabilities_projection","required_life_action_subset/v1");
        byte[] oracle=encode(actual,expected,policy()+SUBSET_POLICY);
        String diagnostics=System.getProperty("p106.diagnostic.dir");
        if(diagnostics!=null) {
            Path directory=Path.of(diagnostics);Files.createDirectories(directory);
            Files.write(directory.resolve("actual-wire.json"),wire);
            Files.write(directory.resolve("independent-oracle-wire.json"),oracle);
        }
        org.junit.jupiter.api.Assertions.assertArrayEquals(oracle,wire,"restored-history variant must match the complete independent task contract before comparing historical markers");
        org.junit.jupiter.api.Assertions.assertArrayEquals(before,FullJsonTree.encode(OpportunityJson.toNode(actual.request().observations().snapshot()),LIMIT));
        org.junit.jupiter.api.Assertions.assertArrayEquals(history,FullJsonTree.encode(OpportunityJson.toNode(new OpportunityJson.Arr(new ArrayList<OpportunityJson.Value>(actual.request().observations().history()))),LIMIT));
        org.junit.jupiter.api.Assertions.assertArrayEquals(command,ActionCodec.encodeCommand(actual.selected().command()));
        org.junit.jupiter.api.Assertions.assertEquals(actual.commandSha(),ActionCodec.bodySha256(actual.selected().command()));
        org.junit.jupiter.api.Assertions.assertEquals(139,actual.request().observations().history().size());
        org.junit.jupiter.api.Assertions.assertEquals(33,actual.selected().trace().visits().size());
        org.junit.jupiter.api.Assertions.assertEquals(10,actual.request().observations().actionFacts().size());
        org.junit.jupiter.api.Assertions.assertEquals("2026-11-06T04:45:29.261039300Z",actual.selected().command().deadline().toString());
    }

    @org.junit.jupiter.api.Test void originalSmallLifeWireReturnsBeforeRegistryProjectionValidation()throws Exception {
        ObjectNode snapshot=(ObjectNode)OpportunityJson.toNode(actual.request().observations().snapshot());
        var caps=((ObjectNode)snapshot.path("diagnostics").path("hello")).putArray("capabilities");
        required("requiredLifeCapabilities",AdvancePlan.decode(actual.selected().command())).stream().sorted().forEach(caps::add);
        // Deliberately differs from observations' complete registry: old small profiles must still return unchanged.
        Data small=withSnapshot(snapshot,actual.request().observations().bridgeCapabilities());
        ObjectNode expected=taskWithoutDuplicateHistory(small);
        byte[] originalWire=encode(small,expected,policy());
        org.junit.jupiter.api.Assertions.assertTrue(originalWire.length<=65536);
        byte[] wire=payload(small);
        org.junit.jupiter.api.Assertions.assertArrayEquals(originalWire,wire);
        org.junit.jupiter.api.Assertions.assertFalse(user(wire).has("hello_capabilities_projection"));
    }

    @org.junit.jupiter.api.Test void unsupportedRegistryAndStillLargeCurrentFactsKeepFullFallback()throws Exception {
        for(String variant:List.of("mismatch","nontext","unknown_shape","missing_required","still_large")) {
            ObjectNode snapshot=(ObjectNode)OpportunityJson.toNode(actual.request().observations().snapshot());
            ObjectNode hello=(ObjectNode)snapshot.path("diagnostics").path("hello");
            Set<String> observed=actual.request().observations().bridgeCapabilities();
            if(variant.equals("mismatch"))((ArrayNode)hello.get("capabilities")).add("p106.synthetic_extra_capability");
            if(variant.equals("nontext"))((ArrayNode)hello.get("capabilities")).set(0,JsonNodeFactory.instance.numberNode(1));
            if(variant.equals("unknown_shape")){hello.set("capabilities",JsonNodeFactory.instance.objectNode());snapshot.put("unknown_large_current_fact","x".repeat(7000));}
            if(variant.equals("missing_required")) {
                String required=required("requiredLifeCapabilities",AdvancePlan.decode(actual.selected().command())).get(0);
                var all=new HashSet<>(observed);all.remove(required);observed=all;
                var caps=hello.putArray("capabilities");all.stream().sorted().forEach(caps::add);
            }
            if(variant.equals("still_large"))snapshot.put("unknown_large_current_fact","x".repeat(7000));
            Data changed=withSnapshot(snapshot,observed);
            org.junit.jupiter.api.Assertions.assertNull(call("tryCompactPayload",new Class<?>[]{PlanningRequest.class,PlanningResult.ActionSelected.class,String.class},changed.selector(),changed.request(),changed.selected(),changed.commandSha()),variant);
            byte[] wire=payload(changed);JsonNode output=user(wire);
            org.junit.jupiter.api.Assertions.assertFalse(output.has("hello_capabilities_projection"),variant);
            org.junit.jupiter.api.Assertions.assertTrue(output.has("history"),variant);
            org.junit.jupiter.api.Assertions.assertArrayEquals(FullJsonTree.encode(hello.get("capabilities"),LIMIT),FullJsonTree.encode(output.path("snapshot").path("diagnostics").path("hello").get("capabilities"),LIMIT),variant);
            org.junit.jupiter.api.Assertions.assertEquals(changed.commandSha(),output.path("body_sha256").textValue(),variant);
            if(snapshot.has("unknown_large_current_fact"))org.junit.jupiter.api.Assertions.assertEquals(snapshot.get("unknown_large_current_fact"),output.path("snapshot").get("unknown_large_current_fact"),variant);
        }
    }

    /** Actual old/new binary comparison: same reconstruction and formatter call; only the ordered classpath changes. */
    public static void main(String[] args)throws Exception {
        if(args.length!=5)throw new IllegalArgumentException("REQUEST BATCH Driver1475.gz baseline|candidate OUTPUT required");
        long start=System.nanoTime();Data data=load(Path.of(args[0]),Path.of(args[1]),Path.of(args[2]));long loaded=System.nanoTime();
        boolean baseline=args[3].equals("baseline");require(baseline||args[3].equals("candidate"),"mode required");
        // AdvancePlan's pre-existing campaign_deadline object member order varies across JVMs.
        // Build the full independent oracle in BOTH modes before warmup; retain exact bytes within this JVM.
        long oracleStarted=System.nanoTime();
        ObjectNode expected=taskWithoutDuplicateHistory(data);
        ArrayNode projected=JsonNodeFactory.instance.arrayNode();
        required("requiredLifeCapabilities",AdvancePlan.decode(data.selected().command())).stream().sorted().forEach(projected::add);
        ((ObjectNode)expected.path("snapshot").path("diagnostics").path("hello")).set("capabilities",projected);
        expected.put("hello_capabilities_projection","required_life_action_subset/v1");
        byte[] oracleWire=encode(data,expected,policy()+SUBSET_POLICY);
        String candidateOracleSha=sha(oracleWire);
        long oracleNs=System.nanoTime()-oracleStarted;
        String expectedSha=baseline?"1c1e7c0fbc8323404249b77f18a458ff6d3d94f5bbb1132113351603e73c9496":candidateOracleSha;
        int expectedBytes=baseline?1537575:60559;
        String snapshotSha=sha(FullJsonTree.encode(OpportunityJson.toNode(data.request().observations().snapshot()),LIMIT));
        var bean=java.lang.management.ManagementFactory.getThreadMXBean();
        com.sun.management.ThreadMXBean allocations=bean instanceof com.sun.management.ThreadMXBean available&&available.isThreadAllocatedMemorySupported()?available:null;
        if(allocations!=null&&!allocations.isThreadAllocatedMemoryEnabled())allocations.setThreadAllocatedMemoryEnabled(true);
        ObjectNode result=JsonNodeFactory.instance.objectNode();result.put("schema","xar.p106-full-formatter-same-input/v1");result.put("mode",args[3]);result.put("reconstruction",RECONSTRUCTION+"_NATIVE_HISTORY_139_RESTORED_BY_PRODUCER_RULE");
        result.put("source_scope","snapshot.native_command_history restored from same Driver139 originalRow list as request.history; original removed-member position unknown; no claim of original internal FullSnapshot byte identity");
        result.put("command_sha256",data.commandSha());result.put("deadline",data.selected().command().deadline().toString());result.put("history_rows",139);result.put("trace_visits",33);result.put("action_facts",10);result.put("load_ns",loaded-start);
        result.put("wire_bytes",expectedBytes);result.put("wire_sha256",expectedSha);result.put("main_thread_allocation_supported",allocations!=null);
        result.put("independent_candidate_oracle_setup_ns",oracleNs);result.put("independent_candidate_oracle_sha256",candidateOracleSha);
        result.put("known_cross_jvm_member_order_variant_path","/bounded_stop_intent/advance_plan/campaign_deadline");
        result.put("wire_marker_scope","candidate raw SHA is independently derived and fixed within each JVM; no universal cross-JVM candidate SHA; baseline fixed historical marker is checked without rewriting");
        ArrayNode samples=result.putArray("all_warm_and_measured_samples");
        for(int i=0;i<6;i++) {
            long allocationBefore=allocations==null?0:allocations.getThreadAllocatedBytes(Thread.currentThread().threadId());
            long began=System.nanoTime();byte[] wire=payload(data);long elapsed=System.nanoTime()-began;
            long allocated=allocations==null?0:allocations.getThreadAllocatedBytes(Thread.currentThread().threadId())-allocationBefore;
            if(wire.length!=expectedBytes||!sha(wire).equals(expectedSha)) {
                Files.write(Path.of(args[4]).resolveSibling("UNEXPECTED-WIRE.json"),wire);
                throw new IllegalArgumentException("actual formatter output marker changed: mode="+args[3]+" bytes="+wire.length+" sha="+sha(wire));
            }
            ObjectNode sample=samples.addObject();sample.put("index",i);sample.put("warmup",i<2);sample.put("formatter_ns",elapsed);if(allocations!=null)sample.put("main_thread_allocated_bytes",allocated);else sample.putNull("main_thread_allocated_bytes");
        }
        require(snapshotSha.equals(sha(FullJsonTree.encode(OpportunityJson.toNode(data.request().observations().snapshot()),LIMIT))),"formatter mutated original snapshot");
        require(data.commandSha().equals(ActionCodec.bodySha256(data.selected().command())),"formatter mutated original command");
        result.put("main_ns_before_output",System.nanoTime()-start);result.put("scope","component DATA only; all full requestPayload work including failed initial compact encoding is timed; no HTTP or game throughput credit");
        byte[] summary=FullJsonTree.encode(result,32768);Files.write(Path.of(args[4]),summary);System.out.write(summary);System.out.println();
    }

    private static Data withSnapshot(ObjectNode snapshot,Set<String> capabilities)throws Exception {
        var old=actual.request();var observation=old.observations();
        var changed=new PlanningObservation(object(FullJsonTree.encode(snapshot,LIMIT)),observation.history(),observation.actionSteps(),capabilities,observation.battleSpeedReadiness(),observation.actionFacts(),observation.campaignGoal(),observation.crossRunPlan(),observation.initialLifestyleFocusRequired());
        return new Data(new PlanningRequest(old.before(),old.source(),old.sessionId(),old.deadline(),changed),actual.selected(),actual.originalModel(),actual.selector(),actual.commandSha(),actual.normalizedOldOperationNames(),actual.historyStructuralDifferences());
    }
    private static ObjectNode taskWithoutDuplicateHistory(Data data)throws Exception {ObjectNode task=completeTaskOracle(data);((ObjectNode)task.get("snapshot")).remove("native_command_history");return task;}
    private static String policy()throws Exception {Field field=RootOnlineDecisionSelector.class.getDeclaredField("COMPACT_LIFE_POLICY");field.setAccessible(true);return (String)field.get(null);}
    private static JsonNode user(byte[] wire){return FullJsonTree.parse(FullJsonTree.parse(wire,LIMIT).path("messages").get(1).path("content").textValue().getBytes(StandardCharsets.UTF_8),LIMIT);}
    private static byte[] gzipResource(String name)throws Exception {try(var raw=LargeLifePayload106Test.class.getResourceAsStream(name)){require(raw!=null,"missing exact DATA resource "+name);try(var input=new GZIPInputStream(raw)){byte[] bytes=input.readNBytes(8*1024*1024);require(input.read()==-1,"bounded resource required");return bytes;}}}

    static Data load(Path requestPath,Path tracePath,Path gzipPath)throws Exception {
        byte[] driver;
        try(var input=new GZIPInputStream(Files.newInputStream(gzipPath))){driver=input.readNBytes(8*1024*1024);require(input.read()==-1,"bounded Driver required");}
        return load(Files.readAllBytes(requestPath),Files.readAllBytes(tracePath),driver);
    }
    static Data load(byte[] requestBytes,byte[] traceBytes,byte[] driver)throws Exception {
        require(requestBytes.length==2784926&&sha(requestBytes).equals("d5ba35a419234e9393ad94436c1ec8559bed7d2c941cc06cf277e80c968ea994"),"exact old REQUEST required");
        require(traceBytes.length==49757&&sha(traceBytes).equals("fe1215662d16970d73e9d86fe5725c43109623927d285d0256de63be551544d8"),"exact BATCH29 trace required");
        require(driver.length==5255697&&sha(driver).equals("092b7df37ab70b5d28981b1c681fbf96cc1e58f0029706bab15fd741adc705f4"),"exact qualified Driver1475 required");
        JsonNode envelope=FullJsonTree.parse(requestBytes,LIMIT);
        JsonNode model=FullJsonTree.parse(envelope.path("messages").get(1).path("content").textValue().getBytes(StandardCharsets.UTF_8),LIMIT);
        JsonNode trace=FullJsonTree.parse(traceBytes,LIMIT).path("last_plan");
        require(trace.path("before").equals(model.path("proposal").path("before"))&&trace.path("final_plan").path("command").equals(model.path("proposal")),"real trace and model command differ");
        ActionCommand command=ActionCodec.decodeCommand(FullJsonTree.encode(model.get("proposal"),ActionCodec.MAX_COMMAND_BYTES));
        String commandSha=ActionCodec.bodySha256(command);require(commandSha.equals(model.path("body_sha256").textValue()),"current fixed codec changed original command SHA");
        var complete=DriverStateSnapshot.decodeComplete(driver);driver=null;
        int count=model.path("history").size();require(count==139&&complete.commandHistory().size()==229,"actual prefix history sizes differ");
        List<Obj> history=new ArrayList<>();
        for(int i=0;i<count;i++)history.add(object(complete.commandHistory().get(i).originalRow().json()));
        complete=null;
        int differences=0;
        for(int i=0;i<count;i++) {
            ObjectNode original=(ObjectNode)OpportunityJson.toNode(history.get(i));
            if(original.path("command").asText().equals("query-campaign-root-context-v1"))((ObjectNode)original.path("read_history_source")).remove(List.of("decoder_source","definition_source","original_receipt","supporting_evidence","source"));
            JsonNode exported=model.path("history").get(i).deepCopy();JsonNode root=exported.path("result").get("campaign_root_context");
            if(root!=null&&root.has("root_ref")) {
                ObjectNode expanded=(ObjectNode)model.path("root_facts").get(root.path("root_ref").intValue()).deepCopy();
                expanded.set("snapshot_revision",root.get("snapshot_revision"));
                ((ObjectNode)expanded.path("player_heir_candidate_v1")).set("snapshot_revision",root.get("player_heir_candidate_v1_snapshot_revision"));
                ((ObjectNode)exported.get("result")).set("campaign_root_context",expanded);
            }
            JsonNode warRef=exported.path("result").get("declarable_wars_history_ref");
            if(warRef!=null) {
                ((ObjectNode)exported.get("result")).remove("declarable_wars_history_ref");
                ((ObjectNode)exported.get("result")).set("declarable_wars",OpportunityJson.toNode(history.get(warRef.intValue())).path("result").get("declarable_wars"));
            }
            if(!original.equals(exported))differences++;
        }
        require(differences==0,"actual full history prefix differs from inverse old exported projection");
        Set<OperationKey> operations=new HashSet<>();int normalized=0;
        for(JsonNode operation:model.path("routable_operations")) {
            String value=operation.textValue();require(value!=null,"text wire operation required");
            if(value.startsWith("OperationKey[value=")&&value.endsWith("]")){value=value.substring(19,value.length()-1);normalized++;}
            operations.add(new OperationKey(value));
        }
        Set<String> caps=capabilities(model.path("capabilities"));
        List<ExternalFact> facts=new ArrayList<>();
        for(JsonNode fact:model.path("action_facts")) {
            var claims=fact.path("affected_claims");
            ExternalFact restored=new ExternalFact(fact.path("action_id").textValue(),fact.path("body_sha256").textValue(),command.before(),
                    ExternalState.valueOf(fact.path("state").textValue()),UnknownScope.valueOf(fact.path("scope").textValue()),Domain.valueOf(fact.path("domain").textValue()),
                    new Claims(ids(claims.path("army_ids")),ids(claims.path("ally_character_ids")),ids(claims.path("character_ids")),texts(claims.path("commitment_keys"))),
                    new ExactRef("P106-formatter-only-unexported-evidence-not-authority",1,"0".repeat(64)));
            require(restored.unresolved()==fact.path("unresolved").booleanValue(),"wire fact state/unresolved differ");facts.add(restored);
        }
        // Producer-rule DATA reconstruction variant, not the missing original internal FullSnapshot.
        // DriverObservationAssembler and RootPlanningInputsFactory both map this same originalRow list.
        ObjectNode snapshotTree=(ObjectNode)model.path("snapshot").deepCopy();
        snapshotTree.set("native_command_history",OpportunityJson.toNode(new OpportunityJson.Arr(new ArrayList<OpportunityJson.Value>(history))));
        Obj snapshot=object(FullJsonTree.encode(snapshotTree,LIMIT));
        var goal=snapshot.get("campaign_goal");
        PlanningObservation observations=new PlanningObservation(snapshot,history,operations,caps,Optional.empty(),facts,
                goal==null||goal==OpportunityJson.Nil.INSTANCE?Optional.empty():Optional.of(GoalCodec.decodeGoal(FullJsonTree.encode(OpportunityJson.toNode(goal),LIMIT))),Optional.empty(),false);
        PlanningRequest request=new PlanningRequest(command.before(),command.source(),command.sessionId(),Instant.parse(model.path("planning_deadline").textValue()),observations);
        List<PlanTrace.StageVisit> visits=new ArrayList<>();
        for(JsonNode visit:trace.path("visits"))visits.add(new PlanTrace.StageVisit(PlanningStage.valueOf(visit.path("stage").textValue()),PlanTrace.Outcome.valueOf(visit.path("outcome").textValue()),visit.path("reason").textValue(),ExactRef.optionalFromJson(visit.get("source")),optionalObject(visit.get("evidence"))));
        JsonNode plan=trace.path("final_plan");
        OrdinaryPolicy.Draft draft=new OrdinaryPolicy.Draft(plan.path("policy").textValue(),plan.path("phase").textValue(),plan.path("reason").textValue(),
                OrdinaryPolicy.Kind.valueOf(plan.path("kind").textValue()),Optional.of(command),OrdinaryPolicy.Purpose.valueOf(plan.path("purpose").textValue()),
                plan.path("domain").isNull()?Optional.empty():Optional.of(Domain.valueOf(plan.path("domain").textValue())),object(FullJsonTree.encode(plan.path("detail"),LIMIT)));
        PlanningResult.ActionSelected selected=new PlanningResult.ActionSelected(command,new PlanTrace(command.before(),visits,Optional.of(draft)));
        DecisionProvider config=new DecisionProvider(URI.create("http://127.0.0.1:1/v1"),envelope.path("model").textValue(),Duration.ofSeconds(120),1,Duration.ZERO);
        var selector=new RootOnlineDecisionSelector(config,Clock.fixed(command.deadline().minusSeconds(120),ZoneOffset.UTC),raw->{throw new AssertionError("formatter probe forbids material/HTTP/Game operations");});
        return new Data(request,selected,model,selector,commandSha,normalized,differences);
    }

    static ObjectNode completeTaskOracle(Data data)throws Exception {
        PlanningRequest request=data.request();var proposal=data.selected();
        ObjectNode task=JsonNodeFactory.instance.objectNode();
        task.put("decision_context_schema","xar.model-peaceful-life-decision/v1");task.put("decision_scope","peaceful_clock_advance_admission/v1");
        task.put("projection_scope","bounded peaceful clock intent or WAIT only; historical rows and other-domain plan annotations/evidence stay in Java originals/revalidation/archive; not lossless");
        task.put("proposal_id",proposal.command().actionId());task.put("body_sha256",data.commandSha());task.put("planning_deadline",request.deadline().toString());
        task.set("proposal",FullJsonTree.parse(ActionCodec.encodeCommand(proposal.command()),ActionCodec.MAX_COMMAND_BYTES));
        task.set("snapshot",OpportunityJson.toNode(request.observations().snapshot()));
        var draft=proposal.trace().finalPlan().orElseThrow();ObjectNode chosen=task.putObject("final_plan");
        chosen.put("policy",draft.policy());chosen.put("phase",draft.phase());chosen.put("reason",draft.reason());chosen.put("kind",draft.kind().name());chosen.put("purpose",draft.purpose().name());
        if(draft.domain().isPresent())chosen.put("domain",draft.domain().orElseThrow().name());else chosen.putNull("domain");
        var visits=task.putArray("planner_visits");for(var visit:proposal.trace().visits()){var row=visits.addObject();row.put("stage",visit.stage().name());row.put("outcome",visit.outcome().name());row.put("reason",visit.reason());}
        var facts=task.putArray("action_facts");for(var fact:request.observations().actionFacts()){var row=facts.addObject();row.put("action_id",fact.actionId());row.put("body_sha256",fact.bodySha256());row.put("state",fact.state().name());row.put("unresolved",fact.unresolved());row.put("scope",fact.scope().name());row.put("domain",String.valueOf(fact.domain()));row.set("affected_claims",ActionCodec.claims(fact.affectedClaims()));}
        AdvancePlan plan=AdvancePlan.decode(proposal.command());
        task.put("dependency_scope","only this prepared Life plan's required subset of currently advertised dependencies; not the complete available registry or installation authority");
        var caps=task.putArray("required_capabilities");required("requiredLifeCapabilities",plan).stream().sorted().forEach(caps::add);
        var operations=task.putArray("required_routable_operations");required("requiredLifeOperations",plan).stream().sorted().forEach(operations::add);
        ObjectNode stop=task.putObject("bounded_stop_intent");stop.set("advance_plan",OpportunityJson.toNode(plan.json()));stop.put("sentinel_arm_intent",plan.armStep());stop.put("cancel_dependency",ClockStatusRead.CANCEL_CAP);
        stop.put("cancel_generation_scope","bound only to the actual issued ARM/status generation; no predicted generation");
        var boundaries=stop.putArray("boundaries");for(var boundary:AdvanceProgress.Boundary.values())boundaries.add(boundary.name());
        stop.put("verification_scope","Java retains full readiness, original history, live revalidation, once dispatch and pause/clock verification; selection proves no completed or saved day");return task;
    }
    static byte[] payload(Data data)throws Exception{return (byte[])call("requestPayload",new Class<?>[]{PlanningRequest.class,PlanningResult.ActionSelected.class,String.class},data.selector(),data.request(),data.selected(),data.commandSha());}
    static byte[] encode(Data data,ObjectNode task,String policy)throws Exception{return (byte[])call("encodeModelInput",new Class<?>[]{ObjectNode.class,String.class},data.selector(),task,policy);}
    @SuppressWarnings("unchecked") static List<String> required(String name,AdvancePlan plan)throws Exception{return (List<String>)call(name,new Class<?>[]{AdvancePlan.class},null,plan);}
    private static Object call(String name,Class<?>[] signature,Object target,Object...arguments)throws Exception {Method method=RootOnlineDecisionSelector.class.getDeclaredMethod(name,signature);method.setAccessible(true);try{return method.invoke(target,arguments);}catch(InvocationTargetException error){if(error.getCause() instanceof Exception failure)throw failure;if(error.getCause() instanceof Error failure)throw failure;throw error;}}
    static Set<String> capabilities(JsonNode values){require(values!=null&&values.isArray(),"actual text capability registry array required");Set<String> result=new HashSet<>();for(JsonNode value:values){require(value.isTextual(),"all registry entries must be text");result.add(value.textValue());}return result;}
    private static Set<BigInteger> ids(JsonNode values){Set<BigInteger> result=new HashSet<>();for(JsonNode value:values)result.add(new BigInteger(value.asText()));return result;}
    private static Set<String> texts(JsonNode values){Set<String> result=new HashSet<>();for(JsonNode value:values){require(value.isTextual(),"text commitment required");result.add(value.textValue());}return result;}
    private static Obj object(byte[] value){return OpportunityJson.object(OpportunityJson.parseComplete(value,LIMIT),"original formatter DATA object");}
    private static Optional<Obj> optionalObject(JsonNode value){return value==null||value.isNull()?Optional.empty():Optional.of(object(FullJsonTree.encode(value,LIMIT)));}
    static String sha(byte[] value)throws Exception{return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(value));}
    static void require(boolean condition,String detail){if(!condition)throw new IllegalArgumentException(detail);}
}
