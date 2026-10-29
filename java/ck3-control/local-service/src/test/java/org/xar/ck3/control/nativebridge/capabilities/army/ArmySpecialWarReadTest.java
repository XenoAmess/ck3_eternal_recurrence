package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.UUID;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.service.root.RootArmyReadPacketVerifier;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmySpecialWarReads.*;

/** Local-service integration: actual sole NativeWire verifier -> application family/parser -> original complete driver output. */
final class ArmySpecialWarReadTest {
    private static final Instant AT=Instant.parse("2026-10-24T09:00:00Z"),DEADLINE=AT.plusSeconds(60);
    private static final ExactRef REF=new ExactRef("software-fixture-no-native-qualification",1,"a".repeat(64));
    private static final ArmySpecialWarReads.OriginalPacketVerifier PACKETS=(selected,original)->RootArmyReadPacketVerifier.require(selected.context(),selected.operation(),ArmySpecialWarReads.nativeArguments(selected),original);
    private static final PlanningReadPort NO_QUERY=new PlanningReadPort(){@Override public <T> PlanningReadResult<T> read(ReadContract<T> contract,PlanningReadRequest request){throw new AssertionError("pure replay must not query Native");}};
    private record Fixture(Selection selection,ArmySpecialWarReads reads,RootReadContractCatalog catalog,ArmySpecialWarReads.Issued issued,ObjectNode result){}
    @Test void actualPinnedPrisonerPositiveAndEmptyPacketsPreserveOriginalProofAndPublicWidths()throws Exception {
        for(String name:List.of("positive","empty")){
            var frame=fixture(name);var receipt=receipt(frame,frame.result());var live=frame.issued().contract().decode(receipt);
            assertEquals(live,frame.reads().replay(frame.catalog(),frame.selection(),receipt));
            var projected=ArmyJson.parse(ArmySpecialWarReadCodec.fullDriverResult(live).bytes());
            assertEquals(ArmyJson.parse(live.proof().orElseThrow().bytes()),projected.get("war_prisoner_release_pairs_proof"));
            assertTrue(projected.get("snapshot_revision").isTextual());assertTrue(frame.result().get("snapshot_revision").isIntegralNumber());
            assertEquals(name.equals("positive"),!projected.path("war_prisoner_release_pairs_proof").path("release_pairs").isEmpty());
            assertFalse(projected.has("cleanup_proof"));assertFalse(projected.has("scope"));
        }
    }
    @Test void originalPythonH2743AndBoundLossFixtureNormalizationAgreeWithFullPureDecoder(@TempDir Path temporary)throws Exception {
        var outputs=originalFixtures(temporary);
        for(String name:List.of("h2743","boundLoss")){
            var row=ArmyJson.object(outputs.get(name));var selection=selection(ArmyJson.object(row.get("snapshot")),name.equals("h2743")?"1.19.0.6":"1.19.0.6",new OperationKey(row.path("raw").path("step").textValue()));
            var f=fixture(selection,ArmyJson.object(row.get("raw")));var r=receipt(f,f.result());var observation=f.issued().contract().decode(r);
            assertEquals(observation,f.issued().contract().replay(r));assertEquals(row.get("raw"),ArmyJson.parse(observation.nativeResult().bytes()));
            if(name.equals("h2743"))assertEquals(row.get("proof"),ArmyJson.parse(observation.proof().orElseThrow().bytes()));
            else assertTrue(observation.proof().isEmpty(),"original driver returns raw cleanup without fabricating a proof");
            var result=ArmyJson.parse(ArmySpecialWarReadCodec.fullDriverResult(observation).bytes());assertFalse(result.has("cleanup_proof"));
            assertEquals(observation.kind()==Kind.H2743,result.has("h2743_preaction_existing_truce_proof"));
        }
    }
    @Test void wrongNativeFrameBoolMissingFieldsAndIncompleteScansCannotAcquireKnownData()throws Exception {
        var f=fixture("positive");
        for(String mutation:List.of("native","bool","missing","scan","pair")){
            var bad=f.result().deepCopy();var value=(ObjectNode)bad.get("war_prisoner_release_pairs_v1");
            switch(mutation){case "native"->bad.put("snapshot_revision",2);case "bool"->bad.put("query_sequence",true);case "missing"->bad.remove("war_prisoner_release_pairs_v1");case "scan"->value.put("full_participant_scan",false);case "pair"->value.putArray("attacker_release_candidate_ids").add(999);default->throw new AssertionError();}
            assertThrows(IllegalArgumentException.class,()->f.issued().contract().replay(receipt(f,bad)),mutation);
        }
    }
    @Test void unknownIsReturnedOnceWithoutMintingAResultOrReplacementQuery()throws Exception {
        var sends=new AtomicInteger();PlanningReadPort unavailable=new PlanningReadPort(){@Override public <T> PlanningReadResult<T> read(ReadContract<T> contract,PlanningReadRequest request){sends.incrementAndGet();return new PlanningReadResult.Unavailable<>("original read UNKNOWN",Optional.of(new NativeActionPort.Unknown("original-read", "no complete response",new byte[]{1},Optional.empty())));}};
        var f=fixture("positive");var reads=new ArmySpecialWarReads(new Sources(REF,REF,REF,REF,REF),unavailable,PACKETS);var catalog=new RootReadContractCatalog(List.of(),reads.families());
        var original=reads.collect(null,catalog,f.selection());assertInstanceOf(PlanningReadResult.Unavailable.class,original);assertEquals(1,sends.get());
    }
    @Test void originalPacketCustodyAndSourceCrossingsCannotBeHiddenByAValidInnerToken()throws Exception {
        var f=fixture("positive");var original=receipt(f,f.result());var old=original.original();
        var historical=new NativeActionPort.AckReceived(old.requestId(),true,old.originalResultToken(),old.originalFrame(),old.originalPacket(),old.outbound());
        assertThrows(IllegalArgumentException.class,()->f.issued().contract().replay(new PlanningReadReceipt(original.request(),original.contractId(),original.requestId(),original.before(),original.after(),historical)));
        var packet=old.originalPacket();packet[packet.length-2]^=1;
        var changed=new NativeActionPort.AckReceived(old.requestId(),true,old.originalResultToken(),old.originalFrame(),packet,old.outbound(),old.custody());
        assertThrows(RuntimeException.class,()->f.issued().contract().replay(new PlanningReadReceipt(original.request(),original.contractId(),original.requestId(),original.before(),original.after(),changed)));
        var r=original.request();var other=new PlanningReadRequest(r.before(),r.source(),"different-session",r.operation(),r.arguments(),r.deadline());
        assertThrows(IllegalArgumentException.class,()->f.issued().contract().replay(new PlanningReadReceipt(other,original.contractId(),original.requestId(),original.before(),original.after(),old)));
    }
    @Test void canonicalUint64BoundaryIsDecimalOnlyInPublicProjectionAndNativeArchiveRemainsNumeric()throws Exception {
        var f=fixture("positive");var original=f.selection().original();var snapshot=ArmyJson.object(org.xar.ck3.control.planning.opportunity.OpportunityJson.toNode(original.observations().snapshot())).deepCopy();
        snapshot.put("snapshot_id","native:"+StrictJson.UINT64_MAX).put("native_revision",StrictJson.UINT64_MAX);
        var selection=selection(snapshot,"1.20.0.2",f.selection().operation());var raw=f.result().deepCopy().put("snapshot_revision",StrictJson.UINT64_MAX).put("query_sequence",StrictJson.UINT64_MAX);
        var actual=fixture(selection,raw);var observed=actual.issued().contract().decode(receipt(actual,raw));
        var roundTrip=ArmySpecialWarReadCodec.decodeToken(selection,new RawJson(observed.nativeResult().bytes()));assertEquals(observed,roundTrip);
        var publicResult=ArmyJson.parse(ArmySpecialWarReadCodec.fullDriverResult(roundTrip).bytes());assertEquals(StrictJson.UINT64_MAX.toString(),publicResult.path("snapshot_revision").textValue());
        assertEquals(StrictJson.UINT64_MAX.toString(),publicResult.path("query_sequence").textValue());assertTrue(ArmyJson.parse(observed.nativeResult().bytes()).get("snapshot_revision").isIntegralNumber());
    }
    @Test void h2743AndCleanupRejectInventedFutureEffectsOrWrongPostFrame(@TempDir Path temporary)throws Exception {
        var outputs=originalFixtures(temporary);
        for(String name:List.of("h2743","boundLoss")){
            var row=ArmyJson.object(outputs.get(name));var raw=ArmyJson.object(row.get("raw")).deepCopy();var selected=selection(ArmyJson.object(row.get("snapshot")),"1.19.0.6",new OperationKey(raw.path("step").textValue()));
            if(name.equals("h2743"))((ObjectNode)raw.get("h2743_preaction_existing_truce")).put("effect_projection_complete",true);
            else ((ObjectNode)raw.path("raiktor_war_bound_loss_cleanup").path("postwar_frame")).put("native_revision",7);
            assertThrows(IllegalArgumentException.class,()->ArmySpecialWarReadCodec.decodeToken(selected,new RawJson(ArmyJson.bytes(raw))));
        }
    }
    @Test void h2743FullTitleAndConnectionCannotTruncateIntoTheHistoricalClaim(@TempDir Path temporary)throws Exception {
        var row=ArmyJson.object(originalFixtures(temporary).get("h2743"));var valid=ArmyJson.object(row.get("snapshot"));
        var oversized=valid.deepCopy();((ObjectNode)oversized.path("active_wars").get(0)).putArray("targeted_title_ids").add(new BigInteger("4294969424"));
        assertThrows(IllegalArgumentException.class,()->selection(oversized,"1.19.0.6",new OperationKey(H2743)));
        var connection=valid.deepCopy();((ObjectNode)connection.get("diagnostics")).put("connection_generation",2);
        assertThrows(IllegalArgumentException.class,()->selection(connection,"1.19.0.6",new OperationKey(H2743)));
        assertThrows(IllegalArgumentException.class,()->selection(valid,"1.20.0.4",new OperationKey(H2743)));
        assertThrows(IllegalArgumentException.class,()->new H2743Claim("native:3",BigInteger.valueOf(7),BigInteger.valueOf(3),53217264,29829,EPISODE,16777231,BigInteger.ZERO));
    }
    @Test void nativeSourcesBindContractIdentityWithoutPretendingToBeArchivedMaterialAndLargeFramesStayFinite()throws Exception {
        var f=fixture("positive");var old=f.selection().original();var snapshot=ArmyJson.object(org.xar.ck3.control.planning.opportunity.OpportunityJson.toNode(old.observations().snapshot())).deepCopy();
        snapshot.put("other_complete_semantic_field","x".repeat(70_000));var selected=selection(snapshot,"1.20.0.2",f.selection().operation());
        var large=fixture(selected,f.result());assertTrue(org.xar.ck3.control.planning.opportunity.OpportunityJson.encode(ArmySpecialWarReads.arguments(selected)).length<65_536);
        var prepared=large.issued().contract().prepare(large.issued().request(),"software-original");assertTrue(prepared.preparationEvidence().isEmpty(),"source paths are not immutable archive material locators");
        var changed=new ExactRef("different-actual-native-cut",1,"c".repeat(64));var other=new ArmySpecialWarReads(new Sources(REF,REF,REF,changed,REF),NO_QUERY,PACKETS);
        var catalog=new RootReadContractCatalog(List.of(),other.families());assertNotEquals(large.issued().contract().contractId(),other.issue(catalog,selected).contract().contractId());
        assertNotEquals(f.issued().contract().contractId(),large.issued().contract().contractId(),"complete semantic original must remain bound through its canonical digest");
    }
    @Test void identicalMandatoryTransportVerifierRunsBeforeBothLiveAndColdBusinessDecode()throws Exception {
        var old=fixture("positive");var verifies=new AtomicInteger();
        ArmySpecialWarReads.OriginalPacketVerifier actual=(selected,original)->{RootArmyReadPacketVerifier.require(selected.context(),selected.operation(),ArmySpecialWarReads.nativeArguments(selected),original);verifies.incrementAndGet();};
        var reads=new ArmySpecialWarReads(new Sources(REF,REF,REF,REF,REF),NO_QUERY,actual);var catalog=new RootReadContractCatalog(List.of(),reads.families());
        var issued=reads.issue(catalog,old.selection());var f=new Fixture(old.selection(),reads,catalog,issued,old.result());var original=receipt(f,f.result());
        var value=issued.contract().decode(original);assertEquals(value,issued.contract().replay(original));assertEquals(2,verifies.get());
        assertThrows(NullPointerException.class,()->new ArmySpecialWarReads(new Sources(REF,REF,REF,REF,REF),NO_QUERY,null));
    }
    private static Fixture fixture(String name)throws Exception {
        String sha=name.equals("positive")?"bc5069b1d961f6c81ed65d2529909c7c2e520838ddb523361cf2308da3a41f3b":"b26b085dbaec7285a73fe316b0bde807d300436521e00857eb8d3762987c7cad";
        var packet=ArmyJson.parse(pinned("native_bridge/research/fixtures/ck3_12002_prisoner_retention_"+name+".json",sha));var raw=ArmyJson.object(packet.get("result"));
        var snapshot=ArmyJson.empty().put("snapshot_id","native:1").put("revision",2).put("native_revision",1).put("date_raw",1234).put("episode_run_id","software-war-original").put("paused",true).put("map_ready",true);
        snapshot.putObject("played_character").put("character_id",67108865).put("alive",true);snapshot.putObject("diagnostics").put("connection_generation",1);snapshot.putArray("active_wars").addObject().put("war_id",83886081);snapshot.putArray("player_armies");
        return fixture(selection(snapshot,"1.20.0.2",new OperationKey(raw.path("step").textValue())),raw);
    }
    private static Fixture fixture(Selection selection,ObjectNode raw){var reads=new ArmySpecialWarReads(new Sources(REF,REF,REF,REF,REF),NO_QUERY,PACKETS);var catalog=new RootReadContractCatalog(List.of(),reads.families());return new Fixture(selection,reads,catalog,reads.issue(catalog,selection),raw);}
    private static Selection selection(ObjectNode snapshot,String build,OperationKey operation){
        if(!snapshot.has("player_armies"))snapshot.putArray("player_armies");
        var source=new G2Source("software-special-war-no-game",AT.toString(),build,REF);var nativeRevision=snapshot.path("native_revision").bigIntegerValue();
        var frame=new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(snapshot.path("played_character").path("character_id").bigIntegerValue(),nativeRevision,snapshot.path("date_raw").bigIntegerValue()),snapshot.path("snapshot_id").textValue(),snapshot.path("revision").bigIntegerValue(),snapshot.path("episode_run_id").textValue());
        var identity=new ObservationIdentity(source.machineId(),new GameGeneration(42,new PythonOnlyUInt64(BigInteger.ONE)),frame,1);
        var observations=new PlanningObservation(DriverJson.object(ArmyJson.bytes(snapshot),DriverJson.MAX_NATIVE_BYTES),List.of(),Set.of(),Set.of(capability(kind(operation))),Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false);
        var original=new PlanningRequest(identity,source,"software-special-war-session",DEADLINE,observations);
        Optional<H2743Claim> claim=operation.value().equals(H2743)?Optional.of(new H2743Claim(frame.snapshotId(),frame.revision(),nativeRevision,53217264,29829,EPISODE,16777231,BigInteger.ONE)):Optional.empty();
        return new Selection(original,operation,claim);
    }
    private static PlanningReadReceipt receipt(Fixture f,ObjectNode result)throws Exception {
        String id="software-special-original";var top=ArmyJson.empty().put("type","command_result").put("protocol_version",1).put("request_id",id).put("ok",true);top.set("result",result);
        var full=new RawJson(ArmyJson.bytes(top));byte[] incoming=NativeWire.packet(full.bytes());
        var prepared=f.issued().contract().prepare(f.issued().request(),id);
        byte[] outbound=NativeWire.execute(id,prepared.step(),f.selection().context().nativeRevision(),prepared.additionalFields().bytes());
        var identity=f.selection().original().before();var source=f.selection().original().source();
        var guard=new PlanningReadGuard(new GuardEvidence(identity,source,f.selection().original().sessionId(),BigInteger.ONE,f.selection().operation(),REF,REF,"software-original-only",AT,DEADLINE),true,true,true,"b".repeat(64));
        var transport=new NativeObservationPort.TransportSession(source.machineId(),identity.game(),BigInteger.ONE,f.selection().original().sessionId());
        var chronology=new NativeRequestChronology(transport,UUID.fromString("00000000-0000-0000-0000-000000000001"),id,
            NativeRequestChronology.PacketIdentity.of(outbound),NativeRequestChronology.PacketIdentity.of(incoming),
            new NativeRequestChronology.Event(BigInteger.ONE,AT.plusSeconds(1)),new NativeRequestChronology.Event(BigInteger.TWO,AT.plusSeconds(2)),new NativeRequestChronology.Event(BigInteger.valueOf(3),AT.plusSeconds(3)));
        var ack=new NativeActionPort.AckReceived(id,true,Optional.of(new RawJson(ArmyJson.bytes(result))),full,incoming,Optional.of(new NativeActionPort.OutboundPacket(id,outbound)),Optional.of(chronology));
        return new PlanningReadReceipt(f.issued().request(),f.issued().contract().contractId(),id,guard,guard,ack);
    }
    private static Path project(){String value=System.getProperty("xar.repository.root");if(value==null||value.isBlank())throw new IllegalStateException("NOT_RUN: mandatory xar.repository.root original source input absent");return Path.of(value).resolve("ck3_autonomous_player");}
    private static byte[] pinned(String relative,String sha)throws Exception {byte[] original=Files.readAllBytes(project().resolve(relative));assertEquals(sha,ActionCodec.sha256(original),"actual original fixture/source drift: "+relative);return original;}
    private static ObjectNode originalFixtures(Path temporary)throws Exception {
        String python=System.getProperty("xar.python");if(python==null||python.isBlank())throw new IllegalStateException("NOT_RUN: mandatory original Python executable absent");
        var output=temporary.resolve("actual-original-fixtures.json");var error=temporary.resolve("actual-original-fixtures.stderr");
        var process=new ProcessBuilder(python,"-X","utf8","-c",ORIGINAL_FIXTURES,project().toString()).redirectOutput(output.toFile()).redirectError(error.toFile()).start();
        if(!process.waitFor(20,TimeUnit.SECONDS)){process.destroyForcibly();throw new java.io.IOException("actual original fixture producer timed out");}
        if(process.exitValue()!=0)throw new java.io.IOException("actual original fixture producer failed: "+Files.readString(error));
        return ArmyJson.parse(Files.readAllBytes(output));
    }
    private static final String ORIGINAL_FIXTURES="""
        import ast,copy,hashlib,json,runpy,sys
        from pathlib import Path
        root=Path(sys.argv[1])
        def pin(name,sha):
            path=root/name
            if hashlib.sha256(path.read_bytes()).hexdigest()!=sha:raise RuntimeError('actual original source drift: '+name)
            return path
        h=pin('src/xar_autoplayer/bridge/h2743_preaction_existing_truce_v1.py','3a63d58445c29bc43cde4827b7626576f53a64d01bf15db15b508a40b3b587f5')
        hf=pin('tests/unit/test_h2743_preaction_existing_truce_v1.py','fe154fd29a8108731d0ef35713f74df4f98c7c07f5598eac94bf82a85a9c6e50')
        hs=runpy.run_path(str(h))
        def functions(path,names,scope):
            tree=ast.parse(path.read_text(encoding='utf-8-sig'))
            selected=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name in names]
            if len(selected)!=len(names):raise RuntimeError('original fixture functions missing')
            exec(compile(ast.fix_missing_locations(ast.Module(body=selected,type_ignores=[])),str(path),'exec'),scope)
        functions(hf,{'result','starting_frame'},hs)
        raw=hs['result'](3);snapshot=hs['starting_frame'](3,7);claim=hs['frame_claim_from_snapshot'](snapshot)
        proof=hs['normalize_result'](raw,native_revision=3)
        hresult={'raw':raw,'snapshot':snapshot,'proof':proof,'claim':claim}
        b=pin('src/xar_autoplayer/bridge/raiktor_war_bound_regiment_contract.py','314c814f56638466580b073e7c926420b588f70f201e94fef5b1b96100783205')
        bf=pin('tests/unit/test_raiktor_war_bound_regiment_contract.py','95ccfce4bb0b83925a73574798130dc6367e1bcc6140092401e9f0999c4d2b41')
        pin('native_bridge/src/raiktor_war_bound_loss_candidate_v1.cpp','0c53a53b7aed692a3daaa53257fe4ad097418ad4d1ce6466688d88bf3a1958c8')
        bs=runpy.run_path(str(b));bs.update(WAR_ID=50331699,ATTACKER_ID=29829,DEFENDER_ID=17116)
        functions(bf,{'_row','_regiment','_active','_cleanup'},bs)
        body=bs['_cleanup'](still_alive=False)
        # Software fixture adapted to the exact native serializer's revision roles, never claimed to be a live C++ capture.
        body['active_frame']['snapshot_revision']=body['active_frame']['native_revision']
        body['postwar_frame']['snapshot_revision']=body['postwar_frame']['native_revision']
        bs['normalize_raiktor_war_bound_regiment'](body,expected_war_id=50331699,expected_attacker_character_id=29829,expected_defender_character_id=17116,expected_snapshot_revision=7,expected_native_revision=7,expected_date_raw=53175816)
        snapshot={'snapshot_id':'native:8','revision':96,'native_revision':8,'date_raw':53175816,'episode_run_id':'software-cleanup-original','paused':True,'map_ready':True,'played_character':{'character_id':29829,'alive':True},'diagnostics':{'connection_generation':1},'active_wars':[]}
        raw={'step':'query-raiktor-war-bound-loss-cleanup-v1-50331699','accepted':True,'query_sequence':1,'snapshot_revision':8,'raiktor_war_bound_loss_cleanup':body,'backend_id':'native-headless'}
        print(json.dumps({'h2743':hresult,'boundLoss':{'raw':raw,'snapshot':snapshot}},separators=(',',':')))
        """;
}
