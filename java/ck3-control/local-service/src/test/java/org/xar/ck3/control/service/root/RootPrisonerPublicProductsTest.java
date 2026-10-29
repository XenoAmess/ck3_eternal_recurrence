package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.family.CachedSuccession12004;
import org.xar.ck3.control.nativebridge.capabilities.family.PrisonerNativeQueries;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.service.mcp.*;
import org.xar.ck3.control.wave2.prisoners.releasepreview.PrisonerOptionIntent;
import org.xar.ck3.control.wave2.prisoners.releasepreview.*;
import org.xar.ck3.control.wave2.prisoners.releasepreview.ReleasePreviewValues12003.*;
import org.xar.ck3.control.application.planning.prisoners.*;
import org.xar.ck3.control.g2.m6.prisonerransom.PrisonerVanillaResearch;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.service.mcp.PublicMcpDirectory.*;

/** Real shared parser/direct directory/serializer with synthetic packets only; no fake Root or private Game authority. */
final class RootPrisonerPublicProductsTest {
    private static final ExactRef SOURCE=new ExactRef("software/prisoner-public-source",1,"1".repeat(64));
    private static final Instant NOW=Instant.parse("2026-10-24T02:00:00Z");
    private static Arguments args(String value){return new Arguments(Presence.VALUE,Optional.of(new RawJson(value.getBytes(StandardCharsets.UTF_8))));}
    private static ToolCall call(String name,String json){return new ToolCall(name,args(json),Optional.empty(),new McpCancellation());}
    @Test void originalNullDefaultsAndSelectedOptionOrderSurviveTheActualPrivateIntentCodec() {
        var omitted=RootPrisonerPublicProducts.decode(args("{\"expected_revision\":56}"));
        var nil=RootPrisonerPublicProducts.decode(args("{\"expected_revision\":56,\"release_option_keys\":null,\"release_material_target_character_id\":null}"));
        assertEquals(omitted,nil);assertEquals(0,omitted.ransomOrdinal());assertInstanceOf(PrisonerOptionIntent.Unconditional.class,omitted.intent().options());
        var requested=RootPrisonerPublicProducts.decode(args("{\"expected_revision\":56,\"ransom_ordinal\":63,\"release_option_keys\":[\"gain_hook\",\"recruit\"],\"release_material_target_character_id\":4261412865}"));
        assertEquals(63,requested.ransomOrdinal());assertEquals(4261412865L,requested.intent().materialTarget().orElseThrow());
        var negotiated=assertInstanceOf(PrisonerOptionIntent.Negotiated.class,requested.intent().options());
        assertEquals(List.of("gain_hook","recruit"),negotiated.options().stream().map(option->option.key()).toList());
        assertEquals(requested.intent(),PrisonerOptionIntent.decode(PrisonerOptionIntent.encode(requested.intent())));
        assertEquals("query-player-prisoner-collection-private-v1-ransom-ordinal-63",PrisonerNativeQueries.step(requested.ransomOrdinal()));
    }
    @Test void missingNullWrongTypeUnknownAndUnsafePublicArgumentsNeverBecomeAnUnconditionalRead() {
        for(String json:List.of("{}","{\"expected_revision\":null}","{\"expected_revision\":true}","{\"expected_revision\":56.0}","{\"expected_revision\":9007199254740992}",
                "{\"expected_revision\":56,\"ransom_ordinal\":null}","{\"expected_revision\":56,\"ransom_ordinal\":true}","{\"expected_revision\":56,\"ransom_ordinal\":64}",
                "{\"expected_revision\":56,\"release_option_keys\":[]}","{\"expected_revision\":56,\"release_option_keys\":[\"recruit\",\"recruit\"]}",
                "{\"expected_revision\":56,\"release_material_target_character_id\":true}","{\"expected_revision\":56,\"release_material_target_character_id\":4294967295}",
                "{\"expected_revision\":56,\"alias\":1}"))assertThrows(IllegalArgumentException.class,()->RootPrisonerPublicProducts.decode(args(json)));
        assertThrows(IllegalArgumentException.class,()->RootPrisonerPublicProducts.decode(new Arguments(Presence.MISSING,Optional.empty())));
        assertThrows(IllegalArgumentException.class,()->RootPrisonerPublicProducts.decode(new Arguments(Presence.NULL,Optional.of(new RawJson("null".getBytes(StandardCharsets.UTF_8))))));
    }
    @Test void actualNativeProducerToOriginalDescriptorDirectDirectoryAndCompleteMcpEnvelopeRoundTrip()throws Exception {
        var fixture=new Packets();var binding=RootPrisonerPublicProducts.binding(SOURCE,fixture::read);assertEquals(0,fixture.calls.get());
        var directory=directory(binding);assertEquals(0,fixture.calls.get());
        var response=StrictJson.parse(directory.invoke(call(RootPrisonerPublicProducts.QUERY,"{\"expected_revision\":56}")).bytes(),16<<20);
        assertEquals(1,fixture.calls.get());assertFalse(response.get("isError").booleanValue());assertEquals("complete",response.get("resultType").textValue());
        var business=response.get("structuredContent");assertEquals("available",business.get("status").textValue());assertTrue(business.path("player_prisoner_collection").get("collection_complete").booleanValue());
        assertEquals(0,business.path("player_prisoner_collection").get("total_count").intValue());assertEquals(56,business.get("queried_revision").intValue());
        assertEquals("native:90",business.get("queried_snapshot_id").textValue());assertFalse(business.get("advertised").booleanValue());
        assertEquals(business,StrictJson.parse(response.get("content").get(0).get("text").textValue().getBytes(StandardCharsets.UTF_8),16<<20));
        assertThrows(PublicMcpDirectory.ToolFailure.class,()->directory.invoke(call(RootPrisonerPublicProducts.QUERY,"{\"expected_revision\":true}")));assertEquals(1,fixture.calls.get());
    }
    @Test void unavailableNativeCollectionKeepsNullCountsAndNeverBecomesEmptyAvailable()throws Exception {
        var fixture=new Packets();fixture.available=false;
        var response=StrictJson.parse(directory(RootPrisonerPublicProducts.binding(SOURCE,fixture::read)).invoke(call(RootPrisonerPublicProducts.QUERY,"{\"expected_revision\":56,\"ransom_ordinal\":63}")).bytes(),16<<20).get("structuredContent");
        assertEquals("unavailable",response.get("status").textValue());assertFalse(response.path("player_prisoner_collection").get("collection_complete").booleanValue());
        assertTrue(response.path("player_prisoner_collection").get("total_count").isNull());assertTrue(response.path("player_prisoner_collection").get("prisoners").isEmpty());assertEquals(1,fixture.calls.get());
    }
    @Test void actualParserRejectsMalformedWireAndPublicEncoderRefusesUnsafeNumericResults()throws Exception {
        var malformed=new Packets();malformed.malformed=true;
        assertThrows(IllegalArgumentException.class,()->directory(RootPrisonerPublicProducts.binding(SOURCE,malformed::read)).invoke(call(RootPrisonerPublicProducts.QUERY,"{\"expected_revision\":56}")));
        var unsafe=new Packets();unsafe.sequence=new BigInteger("9007199254740992");
        assertThrows(IllegalArgumentException.class,()->directory(RootPrisonerPublicProducts.binding(SOURCE,unsafe::read)).invoke(call(RootPrisonerPublicProducts.QUERY,"{\"expected_revision\":56}")));
        assertEquals(1,unsafe.calls.get(),"unrounded exact native result reaches the strict public numeric boundary once");
    }
    @Test void publicActionArgumentsAreStrictAndDoNotRequireOrdinaryPolicyFields()throws Exception {
        assertTrue(RootPrisonerPublicProducts.definitionGaps().isEmpty());
        assertEquals(303,RootPrisonerPublicProducts.decodeAction(args("{\"collection\":{},\"prisoner_character_id\":303}")).prisonerCharacterId());
        for(String json:List.of("{}","{\"collection\":null,\"prisoner_character_id\":303}","{\"collection\":{},\"prisoner_character_id\":true}",
                "{\"collection\":{},\"prisoner_character_id\":303.0}","{\"collection\":{},\"prisoner_character_id\":4294967295}",
                "{\"collection\":{},\"prisoner_character_id\":303,\"ignore_war\":true}"))assertThrows(IllegalArgumentException.class,()->RootPrisonerPublicProducts.decodeAction(args(json)));
    }
    @Test void actualPublicRansomProducerAcceptsDynastyChildHighTierAndAnotherQueriedRowWithoutOrdinaryPolicy()throws Exception {
        var fixture=new Packets();fixture.occupied=true;fixture.read(RootPrisonerPublicProducts.decode(args("{\"expected_revision\":56}")));
        var command=fixture.command(PrisonerOrdinaryPolicy12004.RANSOM,304);var prepared=fixture.preparation.prepare(command);
        assertEquals(PrisonerOrdinaryPolicy12004.RANSOM.value(),prepared.step());assertTrue(PrisonerActionBinding12004.isPublic(command));
        assertEquals(BigInteger.valueOf(57),command.before().frame().revision());assertEquals(BigInteger.valueOf(56),fixture.last.receipt().request().before().frame().revision());
        assertTrue(PrisonerActionBinding12004.selectedFrameMatches(command,fixture.last.receipt()));
        assertEquals(304,StrictJson.parse(prepared.additionalFields().bytes()).get("prisoner_character_id").intValue());
        var result=PrisonerPublicPendingCodec12004.fromAcknowledgement(command,fixture.ack(command),fixture.preparation.selected(command));
        var decoded=PrisonerPublicPendingCodec12004.decode(result);assertEquals(PrisonerPlanningPorts.Family.RANSOM,decoded.family());
        assertEquals(result,PrisonerPublicPendingCodec12004.encode(decoded));assertFalse(StrictJson.parse(result.bytes()).get("material_result").booleanValue());
    }
    @Test void actualAcceptedPublicReleaseDoesNotApplyRansomPriorityAndKeepsPendingCodecCosts()throws Exception {
        var fixture=new Packets();fixture.occupied=true;fixture.read(RootPrisonerPublicProducts.decode(args("{\"expected_revision\":56}")));
        var command=fixture.command(PrisonerOrdinaryPolicy12004.RELEASE,303);assertEquals(PrisonerOrdinaryPolicy12004.RELEASE.value(),fixture.preparation.prepare(command).step());
        var result=PrisonerPublicPendingCodec12004.fromAcknowledgement(command,fixture.ack(command),fixture.preparation.selected(command));
        var decoded=PrisonerPublicPendingCodec12004.decode(result);assertEquals(PrisonerPlanningPorts.Family.RELEASE,decoded.family());
        assertEquals(result,PrisonerPublicPendingCodec12004.encode(decoded));assertTrue(StrictJson.parse(result.bytes()).get("selected_option_keys").isEmpty());
        var broken=(ObjectNode)StrictJson.parse(result.bytes());broken.put("material_result",true);final RawJson credited=new RawJson(StrictJson.canonical(broken));
        assertThrows(IllegalArgumentException.class,()->PrisonerPublicPendingCodec12004.decode(credited));
        broken=(ObjectNode)StrictJson.parse(result.bytes());broken.remove("costs");final RawJson missing=new RawJson(StrictJson.canonical(broken));
        assertThrows(IllegalArgumentException.class,()->PrisonerPublicPendingCodec12004.decode(missing));
        broken=(ObjectNode)StrictJson.parse(result.bytes());((ObjectNode)broken.get("acceptance")).put("would_accept_now",1);final RawJson wrongAnswerType=new RawJson(StrictJson.canonical(broken));
        assertThrows(IllegalArgumentException.class,()->PrisonerPublicPendingCodec12004.decode(wrongAnswerType));
    }
    @Test void incomingCollectionMutationCannotBecomeAnActualOriginalOrANewQuote()throws Exception {
        var fixture=new Packets();fixture.occupied=true;fixture.read(RootPrisonerPublicProducts.decode(args("{\"expected_revision\":56}")));
        var command=fixture.command(PrisonerOrdinaryPolicy12004.RANSOM,303);var changed=(ObjectNode)StrictJson.parse(fixture.last.value().bytes());changed.put("query_sequence",99);
        assertThrows(IllegalArgumentException.class,()->fixture.preparation.bindPublic("changed",command.before(),command.source(),command.sessionId(),command.deadline(),fixture.snapshot(),fixture.last,new RawJson(StrictJson.canonical(changed)),303,command.operation()));
        var ack=fixture.ack(command);var badFrame=(ObjectNode)StrictJson.parse(ack.originalFrame().bytes());badFrame.put("request_id","another-request");
        var malformed=new NativeActionPort.AckReceived(ack.requestId(),true,ack.originalResultToken(),new RawJson(StrictJson.canonical(badFrame)),new byte[]{1});
        assertThrows(IllegalArgumentException.class,()->PrisonerPublicPendingCodec12004.fromAcknowledgement(command,malformed,fixture.preparation.selected(command)));
    }
    @Test void allThreeActualDirectBindingsUseOriginalDescriptorsAndTheSharedCompleteEnvelope()throws Exception {
        var fixture=new Packets();fixture.occupied=true;var collection=fixture.read(RootPrisonerPublicProducts.decode(args("{\"expected_revision\":56}")));
        var direct=directory(RootPrisonerPublicProducts.binding(SOURCE,fixture::read),
                RootPrisonerPublicProducts.actionBinding(RootPrisonerPublicProducts.RANSOM,SOURCE,input->{var command=fixture.command(PrisonerOrdinaryPolicy12004.RANSOM,input.prisonerCharacterId());return PrisonerPublicPendingCodec12004.fromAcknowledgement(command,fixture.ack(command),fixture.preparation.selected(command));}),
                RootPrisonerPublicProducts.actionBinding(RootPrisonerPublicProducts.RELEASE,SOURCE,input->{var command=fixture.command(PrisonerOrdinaryPolicy12004.RELEASE,input.prisonerCharacterId());return PrisonerPublicPendingCodec12004.fromAcknowledgement(command,fixture.ack(command),fixture.preparation.selected(command));}));
        assertEquals(3,direct.tools().size());var input=StrictJson.object();input.set("collection",StrictJson.parse(collection.bytes()));input.put("prisoner_character_id",303);
        for(String name:List.of(RootPrisonerPublicProducts.RANSOM,RootPrisonerPublicProducts.RELEASE)){
            var result=StrictJson.parse(direct.invoke(call(name,new String(StrictJson.canonical(input),StandardCharsets.UTF_8))).bytes());
            assertFalse(result.get("isError").booleanValue());assertFalse(result.path("structuredContent").get("material_result").booleanValue());
            assertEquals(result.get("structuredContent"),StrictJson.parse(result.path("content").get(0).get("text").textValue().getBytes(StandardCharsets.UTF_8)));
        }
    }
    private static PublicMcpDirectory directory(McpExecutableDirectory.DirectBinding<?,?>... bindings)throws Exception {
        var names=Set.of(RootPrisonerPublicProducts.QUERY,RootPrisonerPublicProducts.RANSOM,RootPrisonerPublicProducts.RELEASE);
        var catalog=McpCoverage.readCatalog(resource("/mcp/original-tool-catalog.json"));
        var declarations=catalog.declarations().stream().filter(row->names.contains(row.name())).toList();assertEquals(3,declarations.size());
        var admitted=java.util.Arrays.stream(bindings).map(McpExecutableDirectory.DirectBinding::name).collect(java.util.stream.Collectors.toSet());
        var scope=new McpCoverage.Catalog(declarations);var decisions=declarations.stream().map(row->new McpCoverage.Decision(row.name(),admitted.contains(row.name())?McpCoverage.Admission.ADMITTED:McpCoverage.Admission.UNMIGRATED,SOURCE,"software actual parser/direct MCP closure only")).toList();
        var descriptors=RootOriginalPublicTestInputs.tools().stream().filter(row->admitted.contains(row.name())).toList();
        assertEquals(admitted.size(),descriptors.size(),"mandatory original executable descriptor missing");var registry=new PublicBindings();registry.freeze(Set.of());
        var partial=assertInstanceOf(McpExecutableDirectory.Partial.class,McpExecutableDirectory.assemble(scope,decisions,descriptors,List.of(),registry,List.of(bindings)));
        assertEquals(admitted.size()==3,partial.coverage().completeMigration());return partial.softwareDirectory();
    }
    private static RawJson resource(String path)throws Exception {try(InputStream in=RootPrisonerPublicProductsTest.class.getResourceAsStream(path)){assertNotNull(in,"mandatory original MCP resource missing: "+path);return new RawJson(in.readAllBytes());}}
    private static final class Packets {
        final AtomicInteger calls=new AtomicInteger();boolean available=true,malformed,occupied;BigInteger sequence=BigInteger.valueOf(11);
        PlanningReadResult.Known<RawJson> last;PrisonerNativeQueries queries;PrisonerActionBinding12004 preparation;
        RawJson read(RootPrisonerPublicProducts.Query input)throws InterruptedException {
            calls.incrementAndGet();assertEquals(BigInteger.valueOf(56),input.expectedRevision());
            var source=new G2Source("software-public-prisoner-machine",NOW.toString(),"1.20.0.4@sha256:"+CachedSuccession12004.EXE_SHA256,SOURCE);
            var before=new ObservationIdentity(source.machineId(),new GameGeneration(321,new PythonOnlyUInt64(new BigInteger("133700000000000001"))),
                    new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(101),BigInteger.valueOf(90),BigInteger.valueOf(53220000)),"native:90",BigInteger.valueOf(56),"software-public-episode"),1);
            queries=new PrisonerNativeQueries(SOURCE,(ordinal,request,intent)->{throw new AssertionError("pure parser must not acquire current admission");});var contract=queries.contract(input.ransomOrdinal());
            var request=new PlanningReadRequest(before,source,"software-public-session",contract.operation(),PrisonerNativeQueries.arguments(input.intent().options(),input.intent().materialTarget()),NOW.plusSeconds(30));
            var payload=StrictJson.object().put("step",PrisonerNativeQueries.step(input.ransomOrdinal())).put("accepted",true).put("status",available?"available":"unavailable")
                    .put("query_sequence",sequence).put("observation_revision",12).put("snapshot_revision",90).put("private_build",true).put("read_only",true).put("advertised",false).put("backend_id","native-headless");
            var value=payload.putObject("player_prisoner_collection").put("schema","player-prisoner-collection-private-v1").put("schema_version",1).put("snapshot_revision",90).put("status",available?"available":"unavailable");
            if(available)value.putNull("unavailable_reason").put("date_raw",53220000).put("played_character_id",101).put("total_count",0).put("returned_count",0);
            else value.put("unavailable_reason","source_unavailable").putNull("date_raw").putNull("played_character_id").putNull("total_count").putNull("returned_count");
            value.put("collection_complete",available).putArray("prisoners");if(malformed)value.remove("collection_complete");
            if(occupied&&available){
                value.put("schema_version",6).put("played_house_id",17).put("played_dynasty_id",17).put("played_dread_raw",0).put("total_count",2).put("returned_count",2);
                var rows=value.putArray("prisoners");
                for(int index=0;index<2;index++){
                    long target=303+index;var binding=new FrameBinding(BigInteger.valueOf(90),53220000,101,target);
                    var row=rows.addObject().put("source_ordinal",index).put("prisoner_character_id",target).put("collection_owner_character_id",101).put("jailer_character_id",101)
                            .put("custody_relation_verified",true).put("house_id",17).put("dynasty_id",17).put("same_house",true).put("same_dynasty",true)
                            .put("is_child_of_played_character",true).put("primary_title_tier_raw",6);
                    row.set("unconditional_release_preview",ReleasePreviewCodec12003.toNode(new ReleasePreview12003.Available(binding,BigInteger.valueOf(12),new Definition(123,1),true,
                            new Costs(java.util.Arrays.stream(Resource.values()).map(resource->new CostEntry(resource,0)).toList()))));
                    row.set("ransom_quote_preview",PrisonerVanillaResearch.quoteJson(new PrisonerVanillaResearch.AvailableQuote(binding,BigInteger.valueOf(12),404,
                            PrisonerVanillaResearch.Option.GOLD,30_000_000,0,0)));
                }
            }
            String id="software-public-read";var frame=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id",id).put("ok",true);frame.set("result",payload);byte[] raw=StrictJson.canonical(frame);
            try {
                byte[] response=NativeWire.packet(raw);var extra=StrictJson.object();
                if(input.intent().options() instanceof PrisonerOptionIntent.Negotiated terms)extra.put("release_option_mask_bits",terms.mask());
                input.intent().materialTarget().ifPresent(target->extra.put("release_material_target_character_id",target));
                byte[] outbound=NativeWire.executePrivateQuery(id,contract.operation().value(),BigInteger.valueOf(90),StrictJson.canonical(extra));
                var custody=new NativeRequestChronology(new NativeObservationPort.TransportSession(source.machineId(),before.game(),BigInteger.TWO,request.sessionId()),
                        java.util.UUID.fromString("00000000-0000-0000-0000-000000000016"),id,NativeRequestChronology.PacketIdentity.of(outbound),NativeRequestChronology.PacketIdentity.of(response),
                        new NativeRequestChronology.Event(BigInteger.ONE,NOW),new NativeRequestChronology.Event(BigInteger.TWO,NOW),new NativeRequestChronology.Event(BigInteger.valueOf(3),NOW));
                var ack=new NativeActionPort.AckReceived(id,true,Optional.of(new RawJson(StrictJson.canonical(payload))),new RawJson(raw),response,
                        Optional.of(new NativeActionPort.OutboundPacket(id,outbound)),Optional.of(custody));
                var guardEvidence=new GuardEvidence(before,source,request.sessionId(),BigInteger.TWO,contract.operation(),SOURCE,SOURCE,"software-authority",NOW,NOW.plusSeconds(30));
                var guard=new PlanningReadGuard(guardEvidence,true,true,true,"2".repeat(64));var receipt=new PlanningReadReceipt(request,contract.contractId(),id,guard,guard,ack);
                var normalized=contract.replay(receipt);last=new PlanningReadResult.Known<>(normalized,receipt,SOURCE);return normalized;
            }catch(java.io.IOException error){throw new java.io.UncheckedIOException(error);}
        }
        OpportunityJson.Obj snapshot(){var value=StrictJson.object();value.putObject("played_character_gold").put("raw",100_000_000).put("scale",100_000);return OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(value)),"software snapshot");}
        ActionCommand command(OperationKey operation,long target){
            var basis=last.receipt().request();var old=basis.before();var original=old.frame();
            var current=new ObservationIdentity(old.machineId(),old.game(),new JointBudgetSelector.ProposalFrame(original.identity(),original.snapshotId(),original.revision().add(BigInteger.ONE),original.episodeRunId()),old.observationVersion());
            preparation=new PrisonerActionBinding12004(new DataArchive(last.receipt()),new PrisonerPlanningPorts.Queries(queries.contracts(),java.util.Map.of()));
            return preparation.bindPublic("software-public-action-"+target,current,basis.source(),basis.sessionId(),basis.deadline(),snapshot(),last,last.value(),target,operation);
        }
        NativeActionPort.AckReceived ack(ActionCommand command){
            var result=StrictJson.object().put("step",command.operation().value()).put("accepted",true).put("status","submitted_verification_pending");
            var frame=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id","software-public-submit").put("ok",true);frame.set("result",result);byte[] raw=StrictJson.canonical(frame);
            try{return new NativeActionPort.AckReceived("software-public-submit",true,Optional.of(new RawJson(StrictJson.canonical(result))),new RawJson(raw),NativeWire.packet(raw));}
            catch(java.io.IOException failure){throw new java.io.UncheckedIOException(failure);}
        }
    }
    /** One synthetic original read only; every writer/submission operation is unavailable. */
    private static final class DataArchive implements ActionPorts.OutcomeArchive{
        private final PlanningReadReceipt read;DataArchive(PlanningReadReceipt read){this.read=read;}
        private static UnsupportedOperationException unavailable(){return new UnsupportedOperationException("software read DATA fixture has no writer/action authority");}
        public PlanningReadReceipt loadRead(ExactRef ref){assertEquals(SOURCE,ref);return read;}
        public ExactRef readReferenceOf(PlanningReadReceipt value){assertEquals(read,value);return SOURCE;}
        public ExactRef preserveRead(PlanningReadReceipt value){throw unavailable();}
        public ExactRef preserve(NativeActionPort.DispatchOutcome value){throw unavailable();}public NativeActionPort.DispatchOutcome load(ExactRef ref){throw unavailable();}
        public ExactRef preserveRequest(NativeRequest value){throw unavailable();}public NativeRequest loadRequest(ExactRef ref){throw unavailable();}
        public ExactRef referenceOf(NativeActionPort.DispatchOutcome value){throw unavailable();}public ExactRef requestReferenceOf(NativeRequest value){throw unavailable();}
        public ExactRef preserveRecord(ActionRecord value){throw unavailable();}public ActionRecord loadRecord(ExactRef ref){throw unavailable();}public ExactRef recordReferenceOf(ActionRecord value){throw unavailable();}
        public ExactRef preserveReceipt(ActionReceipt value){throw unavailable();}public ActionReceipt loadReceipt(ExactRef ref){throw unavailable();}public ExactRef receiptReferenceOf(ActionReceipt value){throw unavailable();}
        public ExactRef preserveMaterial(RawJson value){throw unavailable();}public RawJson loadMaterial(ExactRef ref){throw unavailable();}public ExactRef materialReferenceOf(RawJson value){throw unavailable();}
        public ExactRef preserveNativeFrame(NativeObservationPort.ObservedFrame value){throw unavailable();}public byte[] loadNativeFrame(ExactRef ref){throw unavailable();}
    }
}
