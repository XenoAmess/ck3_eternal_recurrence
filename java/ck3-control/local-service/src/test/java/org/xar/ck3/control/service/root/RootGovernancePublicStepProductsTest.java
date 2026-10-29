package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.*;
import org.xar.ck3.control.nativebridge.capabilities.governance.*;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.service.mcp.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Original native data -> identical domain contract -> generic EXECUTE formatter/SDK envelope.
 * Guard DTOs are explicitly software data. No Context/Core/source qualification or native permit is minted. */
final class RootGovernancePublicStepProductsTest {
    private static final Instant NOW=Instant.parse("2026-10-24T00:00:00Z");
    private static final ExactRef REF=new ExactRef("software-execute-products-only",1,"a".repeat(64));
    private static final BigInteger MAX=StrictJson.UINT64_MAX;
    private static byte[] fixture(String relative)throws IOException {
        String root=System.getProperty("xar.repository.root");assertNotNull(root,"actual original repository required");
        return Files.readAllBytes(Path.of(root,"ck3_autonomous_player/tests/fixtures",relative));
    }
    private static RawJson raw(JsonNode value) {return new RawJson(StrictJson.canonical(value));}
    private static PlanningRequest planning(boolean council) {
        return planning(council?"1.20.0.2":"1.20.0.3",council?16777217:16777258,council?7:77,council?8:177,
                council?53178264:53328600,council?"native:council12002":"material-fixture:177",Set.of());
    }
    private static PlanningRequest planning(String build,long actor,long nativeRevision,long revision,long date,String snapshot,Set<String> capabilities) {
        var source=new G2Source("execute-products-fixture",NOW.toString(),build,REF);
        var before=new ObservationIdentity(source.machineId(),new GameGeneration(123,new PythonOnlyUInt64(BigInteger.ONE)),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(actor),BigInteger.valueOf(nativeRevision),BigInteger.valueOf(date)),
                        snapshot,BigInteger.valueOf(revision),"software-execute-episode"),1);
        var observation=new PlanningObservation(new Obj(java.util.Map.of()).with("backend_id",new Text("native-headless")).with("snapshot_id",new Text(snapshot)).with("revision",new IntegerValue(BigInteger.valueOf(revision))).with("native_revision",new IntegerValue(BigInteger.valueOf(nativeRevision))).with("date_raw",new IntegerValue(BigInteger.valueOf(date))).with("paused",new Bool(true)).with("map_ready",new Bool(true)).with("episode_run_id",new Text(before.frame().episodeRunId())).with("played_character",new Obj(java.util.Map.of()).with("character_id",new IntegerValue(BigInteger.valueOf(actor))).with("alive",new Bool(true))).with("active_wars",new Arr(List.of())).with("player_armies",new Arr(List.of())).with("active_event",Nil.INSTANCE).with("pending_character_interaction",Nil.INSTANCE),
                List.of(),Set.of(),capabilities,Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false);
        return new PlanningRequest(before,source,"software-execute-session",NOW.plusSeconds(60),observation);
    }
    private static PlanningReadRequest request(PlanningRequest plan,ReadContract<?> contract) {
        return new PlanningReadRequest(plan.before(),plan.source(),plan.sessionId(),contract.operation(),new Obj(java.util.Map.of()),plan.deadline());
    }
    private static <T> PlanningReadResult.Known<T> decode(ReadContract<T> contract,PlanningRequest plan,byte[] original)throws IOException {
        var full=StrictJson.parse(original);String id=full.get("request_id").textValue();var request=request(plan,contract);
        var prepared=contract.prepare(request,id);assertEquals(contract.operation().value(),prepared.step());
        var guard=new PlanningReadGuard(new GuardEvidence(plan.before(),plan.source(),plan.sessionId(),BigInteger.ONE,contract.operation(),REF,REF,
                "software-data-not-native-authority",NOW,plan.deadline()),true,true,true,"b".repeat(64));
        byte[] outbound=NativeWire.execute(id,prepared.step(),plan.before().frame().identity().nativeRevision(),prepared.additionalFields().bytes());
        var ack=new NativeActionPort.AckReceived(id,true,Optional.of(raw(full.get("result"))),new RawJson(original),NativeWire.packet(original),Optional.of(new NativeActionPort.OutboundPacket(id,outbound)));
        var receipt=new PlanningReadReceipt(request,contract.contractId(),id,guard,guard,ack);
        return new PlanningReadResult.Known<>(contract.decode(receipt),receipt,REF);
    }
    private static GovernanceNativeReads contracts(boolean council) {
        var build=council?FrontendRulesData.Build.CK3_12002:FrontendRulesData.Build.CK3_12003;
        return new GovernanceNativeReads(REF,build.version(),build.sha256());
    }
    private static void sdk(RawJson encoded)throws Exception {
        var descriptor=RootOriginalPublicTestInputs.tools().stream().filter(tool->tool.name().equals("ck3_execute_step")).findFirst().orElseThrow();
        var result=PublicMcpDirectory.CallResult.fromBusinessJson(encoded);descriptor.validateResult(result);
        var envelope=StrictJson.parse(result.bytes());var business=StrictJson.parse(encoded.bytes());
        assertEquals(business,envelope.get("structuredContent"));
        assertEquals(business,StrictJson.parse(envelope.get("content").get(0).get("text").textValue().getBytes(StandardCharsets.UTF_8)));
    }
    @Test void unchangedCouncilProducerUsesCompleteExecuteEnvelopeAndDistinctRevisionRoles()throws Exception {
        byte[] input=fixture("native_12002/governance/council-query.json");var known=decode(contracts(true).council(),planning(true),input);
        var encoded=GovernancePublicService.encodeCouncilExecution(new GovernancePublicService.CouncilReply(known.value(),known));sdk(encoded);
        var result=StrictJson.parse(encoded.bytes());assertEquals(12,result.size());
        assertEquals("xar.ck3.council-application-main/v1",result.get("schema").textValue());
        assertEquals("8",result.get("snapshot_revision").textValue());assertEquals("8",result.get("queried_revision").textValue());assertEquals("7",result.get("queried_native_revision").textValue());
        assertTrue(result.get("council_composition_candidates_ready").booleanValue());
        assertEquals(6,result.get("council_composition_candidates").size());
        for(String wrapper:List.of("scope","build","source","binding","request"))assertFalse(result.has(wrapper));
        assertEquals("7",result.at("/council_composition_candidates/snapshot/native_revision").textValue());
        assertArrayEquals(input,fixture("native_12002/governance/council-query.json"));
        var max=(ObjectNode)StrictJson.parse(input);((ObjectNode)max.get("result")).put("query_sequence",MAX);
        var wide=decode(contracts(true).council(),planning(true),StrictJson.canonical(max));
        var wire=GovernancePublicService.encodeCouncilExecution(new GovernancePublicService.CouncilReply(wide.value(),wide));
        assertEquals(MAX.toString(),StrictJson.parse(wire.bytes()).get("query_sequence").textValue());sdk(wire);
        assertTrue(max.get("result").get("query_sequence").isIntegralNumber());
    }
    @Test void unchangedDevelopmentProducerKeepsOriginalReadinessValueAndPublic64OnlyAtWire()throws Exception {
        byte[] input=fixture("steward_develop_county_12003_material/develop_material_available.json");var known=decode(contracts(false).development(),planning(false),input);
        var encoded=GovernancePublicService.encodeDevelopmentExecution(new GovernancePublicService.DevelopmentReply(known.value(),known,Optional.of("native-headless")));sdk(encoded);
        var result=StrictJson.parse(encoded.bytes());assertEquals(11,result.size());
        assertEquals(StrictJson.parse(input).at("/result/steward_develop_county_candidates/readiness"),result.get("steward_develop_county_candidates_ready"));
        assertEquals("177",result.get("queried_revision").textValue());assertEquals("77",result.get("snapshot_revision").textValue());
        assertEquals("8250",result.at("/steward_develop_county_candidates/candidates/0/monthly_development_rate/raw").textValue());
        for(String wrapper:List.of("scope","build","source","binding"))assertFalse(result.has(wrapper));
        assertArrayEquals(input,fixture("steward_develop_county_12003_material/develop_material_available.json"));
        assertTrue(StrictJson.parse(input).at("/result/steward_develop_county_candidates/snapshot_revision").isIntegralNumber());
    }
    @Test void explicitSigned64BoundaryDataUsesTheSameNativeDecoderAndExecuteProjection()throws Exception {
        byte[] input=fixture("steward_develop_county_12003_material/develop_material_available.json");
        var nativeCopy=(ObjectNode)StrictJson.parse(input);var candidate=(ObjectNode)nativeCopy.at("/result/steward_develop_county_candidates/candidates/0");
        ((ObjectNode)candidate.get("monthly_development_rate")).put("raw",Long.MIN_VALUE);
        ((ObjectNode)candidate.get("development_progress").get("current")).put("raw",Long.MAX_VALUE);
        var known=decode(contracts(false).development(),planning(false),StrictJson.canonical(nativeCopy));
        var encoded=GovernancePublicService.encodeDevelopmentExecution(new GovernancePublicService.DevelopmentReply(known.value(),known,Optional.of("native-headless")));sdk(encoded);
        var output=StrictJson.parse(encoded.bytes());
        assertEquals(Long.toString(Long.MIN_VALUE),output.at("/steward_develop_county_candidates/candidates/0/monthly_development_rate/raw").textValue());
        assertEquals(Long.toString(Long.MAX_VALUE),output.at("/steward_develop_county_candidates/candidates/0/development_progress/current/raw").textValue());
        assertEquals(100000,output.at("/steward_develop_county_candidates/candidates/0/monthly_development_rate/scale").intValue());
        assertTrue(nativeCopy.at("/result/steward_develop_county_candidates/candidates/0/monthly_development_rate/raw").isIntegralNumber());
        assertArrayEquals(input,fixture("steward_develop_county_12003_material/develop_material_available.json"));
    }
    @Test void missingNullAndWrongDomainSelectorsStayDistinctThroughActualExecuteCodec() {
        for(String step:List.of(RootGovernancePublicStepProducts.ROOT,GovernanceNativeReads.COUNCIL_STEP,GovernanceNativeReads.DEVELOPMENT_STEP,
                org.xar.ck3.control.nativebridge.capabilities.registry.FactionAlertReadService.STEP,RootGovernancePublicStepProducts.FEATURES)) {
            for(var revision:List.<PublicPlanningCodec.Revision>of(new PublicPlanningCodec.RevisionMissing(),new PublicPlanningCodec.RevisionNull(),new PublicPlanningCodec.RevisionValue(BigInteger.valueOf(8)))) {
                var request=new PublicPlanningCodec.ExecuteRequest(new OperationKey(step),revision,new PublicPlanningCodec.FrameMissing());
                var decoded=PublicPlanningCodec.decodeExecute(PublicBindings.present(PublicPlanningCodec.encodeExecute(request)));
                assertEquals(request,decoded);RootGovernancePublicStepProducts.requireSelector(decoded,step);
                assertThrows(IllegalArgumentException.class,()->RootGovernancePublicStepProducts.requireSelector(decoded,"private-assign-councillor-v1"));
            }
        }
    }
    @Test void unknownReadNeverBecomesKnownOrSubmissionPermissionAndMissingCapabilityKeepsOriginalError() {
        var unknown=new NativeActionPort.Unknown("actual-original-read-id","connection lost after the original write",new byte[]{1,2,3},Optional.empty());
        PlanningReadResult<String> result=new PlanningReadResult.Unavailable<>("native query returned UNKNOWN",Optional.of(unknown));
        var error=assertThrows(PublicServiceFailure.class,()->RootGovernancePublicStepProducts.requireAvailable(result));
        assertEquals(PublicServiceFailure.Kind.exact("BridgeUnavailableError"),error.kind());assertEquals("native query returned UNKNOWN",error.getMessage());assertTrue(error.originalCandidate().isEmpty());
        assertSame(unknown,((PlanningReadResult.Unavailable<String>)result).original().orElseThrow());
        var noCapability=planning(true);
        var unsupported=assertThrows(PublicServiceFailure.class,()->RootGovernancePublicStepProducts.requireCapability(noCapability,
                "game.query.council-composition-candidates-v1","native DLL cannot query council composition candidates"));
        assertEquals(PublicServiceFailure.Kind.exact("UnsupportedStepError"),unsupported.kind());
        assertEquals("native DLL cannot query council composition candidates",unsupported.getMessage());assertTrue(unsupported.originalCandidate().isEmpty());
    }
    private static final String FEATURE_PRODUCER="""
        import json,pathlib,sys
        root=pathlib.Path(sys.argv[1]).resolve()
        sys.path.insert(0,str(root/'ck3_autonomous_player'/'src'))
        from xar_autoplayer.bridge import loaded_feature_manifest_contract as c
        cases=[]
        build=c.CK3_12004
        for available in (True,False):
            reason=None if available else 'state_changed'
            status='available' if available else 'unavailable'
            frame={'schema':'loaded-feature-manifest-v1','schema_version':1,'status':status,
                'snapshot_revision':31,'date_raw':53182016,'unavailable_reason':reason,
                'build':{'version':build.game_version,'exe_sha256':build.executable_sha256},
                'effective_feature_flags':{'status':status,'unavailable_reason':reason,'native_count':44 if available else None,
                    'items':[{'native_index':i,'cstring_id':v[0],'key':v[1],'enabled':i%3==0}
                        for i,v in enumerate(c._FEATURE_DEFINITIONS_BY_BUILD[build.game_version])] if available else None},
                'script_dlc_keys':{'status':status,'unavailable_reason':reason,'enumerated_count':1 if available else None,
                    'keys':['dlc_001'] if available else None},
                'entitlements':{'status':'unavailable','unavailable_reason':'store_verdict_provenance_unclosed','items':None},
                'readiness':{'effective_feature_flags_ready':available,'script_dlc_keys_ready':available,'entitlements_ready':False,
                    'same_frame_ready':available,'actionable_ready':available},'provenance':c._PROVENANCE_BY_BUILD[build.game_version]}
            frame=c.normalize_loaded_feature_manifest_v1(frame,expected_date_raw=53182016,expected_snapshot_revision=31)
            cases.append({'type':'command_result','protocol_version':1,'request_id':'software-loaded-feature', 'ok':True,
                'result':{'step':c.QUERY_LOADED_FEATURE_MANIFEST_V1_STEP,'accepted':True,'status':status,
                    'query_sequence':2**64-1,'snapshot_revision':31,'loaded_feature_manifest':frame,'backend_id':'native-headless'}})
        print(json.dumps({'cases':cases},separators=(',',':')))
        """;
    private static JsonNode originalFeatures()throws Exception {
        String root=System.getProperty("xar.repository.root"),python=System.getProperty("xar.python");
        assertNotNull(root,"actual original repository is mandatory");assertNotNull(python,"actual original Python interpreter is mandatory");
        assertFalse(python.isBlank());assertTrue(Files.isRegularFile(Path.of(root,"ck3_autonomous_player/src/xar_autoplayer/bridge/loaded_feature_manifest_contract.py")));
        Process child=new ProcessBuilder(python,"-X","utf8","-c",FEATURE_PRODUCER,root).redirectErrorStream(true).start();
        try(var tasks=java.util.concurrent.Executors.newVirtualThreadPerTaskExecutor()) {
            try {
                var captured=tasks.submit(()->child.getInputStream().readNBytes(1<<20));
                assertTrue(child.waitFor(30,TimeUnit.SECONDS),"original feature producer timed out");byte[] output=captured.get(5,TimeUnit.SECONDS);
                assertEquals(0,child.exitValue(),()->new String(output,StandardCharsets.UTF_8));return StrictJson.parse(output);
            }finally {if(child.isAlive())child.destroyForcibly();child.getInputStream().close();}
        }
    }
    @Test void actualFeatureProducerRetainsCompleteExecuteMirrorsNullsAndUnknownEntitlements()throws Exception {
        var input=originalFeatures();assertEquals(2,input.get("cases").size());
        var definitions=new FrontendRulesDefinitions(FrontendRulesData.Build.CK3_12004,REF);
        var plan=planning("1.20.0.4",77,31,177,53182016,"software-feature:177",Set.of());
        for(var full:input.get("cases")) {
            byte[] before=StrictJson.canonical(full);var known=decode(definitions.loadedFeatures(),plan,before);
            var output=RootGovernancePublicStepProducts.featureResult(known);sdk(output);var result=StrictJson.parse(output.bytes());assertEquals(21,result.size());
            assertEquals(MAX.toString(),result.get("query_sequence").textValue());assertEquals("31",result.get("snapshot_revision").textValue());
            assertEquals("31",result.at("/loaded_feature_manifest/snapshot_revision").textValue());assertEquals("177",result.get("queried_revision").textValue());
            assertFalse(result.at("/entitlements/items").isArray());assertTrue(result.at("/entitlements/items").isNull());
            assertFalse(result.at("/readiness/entitlements_ready").booleanValue());
            for(String field:List.of("schema","schema_version","date_raw","unavailable_reason","build","effective_feature_flags","script_dlc_keys","entitlements","readiness","provenance"))
                assertEquals(result.get("loaded_feature_manifest").get(field),result.get(field));
            for(String wrapper:List.of("scope","source","binding","public_wire_schema","original_result_sha256"))assertFalse(result.has(wrapper));
            assertArrayEquals(before,StrictJson.canonical(full));assertTrue(full.at("/result/query_sequence").isIntegralNumber());
        }
    }
    @Test void actualDecodersRejectWrongDomainAndCorruptedOriginalBeforeExecuteFormatting()throws Exception {
        byte[] input=fixture("native_12002/governance/council-query.json");
        assertThrows(IllegalArgumentException.class,()->decode(contracts(false).development(),planning(false),input));
        for(String field:List.of("schema","snapshot_revision","accepted","council_composition_candidates")) {
            var changed=(ObjectNode)StrictJson.parse(input);var nativeResult=(ObjectNode)changed.get("result");
            if(field.equals("schema"))nativeResult.put(field,"wrong-domain-schema");
            else if(field.equals("snapshot_revision"))nativeResult.put(field,7);
            else if(field.equals("accepted"))nativeResult.put(field,false);
            else nativeResult.remove(field);
            assertThrows(IllegalArgumentException.class,()->decode(contracts(true).council(),planning(true),StrictJson.canonical(changed)),field);
        }
        var original=decode(contracts(true).council(),planning(true),input);var altered=(ObjectNode)StrictJson.parse(input);
        ((ObjectNode)altered.get("result")).put("schema","wrong-original-schema");var old=original.receipt();var previous=old.original();
        var ack=new NativeActionPort.AckReceived(previous.requestId(),true,Optional.of(raw(altered.get("result"))),raw(altered),NativeWire.packet(StrictJson.canonical(altered)),previous.outbound());
        var changedReceipt=new PlanningReadReceipt(old.request(),old.contractId(),old.requestId(),old.before(),old.after(),ack);
        var changedKnown=new PlanningReadResult.Known<>(original.value(),changedReceipt,REF);
        var reply=new GovernancePublicService.CouncilReply(changedKnown.value(),changedKnown);
        assertThrows(IllegalArgumentException.class,()->GovernancePublicService.encodeCouncilExecution(reply));
        assertArrayEquals(input,fixture("native_12002/governance/council-query.json"));
    }
}
