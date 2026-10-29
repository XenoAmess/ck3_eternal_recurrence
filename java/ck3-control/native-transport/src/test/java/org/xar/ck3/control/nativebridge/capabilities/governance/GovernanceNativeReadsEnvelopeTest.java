package org.xar.ck3.control.nativebridge.capabilities.governance;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.governance.council.CouncilModels;
import org.xar.ck3.control.nativebridge.NativeWire;
import static org.junit.jupiter.api.Assertions.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;

/** Historical native originals exercise the actual public read producer/decoder. Synthetic enclosing guards grant no native or .4 qualification. */
final class GovernanceNativeReadsEnvelopeTest {
    private static final ExactRef REF=new ExactRef("synthetic-governance-envelope-only",1,"a".repeat(64));
    private static final Instant NOW=Instant.parse("2026-10-24T00:00:00Z");
    private static final String COUNCIL_FIXTURE="ck3_autonomous_player/tests/fixtures/native_12002/governance/council-query.json";
    private static final String DEVELOPMENT_FIXTURE="ck3_autonomous_player/tests/fixtures/steward_develop_county_12003_material/develop_material_available.json";
    private static final String SHA2="AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D";
    private static final String SHA3="94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6";
    private static final String SHA4="98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
    private static byte[] fixture(String name)throws Exception {
        String repository=System.getProperty("xar.repository.root");assertNotNull(repository,"required original fixture repository missing");
        return Files.readAllBytes(Path.of(repository,name));
    }
    private static PlanningReadRequest request(boolean council,OperationKey operation) {
        var source=new G2Source("governance-envelope-fixture",NOW.toString(),council?"1.20.0.2":"1.20.0.3",REF);
        var frame=new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(council?16777217:16777258),
                BigInteger.valueOf(council?7:77),BigInteger.valueOf(council?53178264:53328600)),
                council?"native:council12002":"material-fixture:177",BigInteger.valueOf(council?8:177),"retained-envelope-data-fixture");
        var observed=new ObservationIdentity(source.machineId(),new GameGeneration(123,new PythonOnlyUInt64(new BigInteger("133700000000000001"))),frame,1);
        return new PlanningReadRequest(observed,source,"synthetic-envelope-session",operation,new Obj(java.util.Map.of()),NOW.plusSeconds(30));
    }
    private static PlanningReadReceipt receipt(ReadContract<?> contract,boolean council,byte[] bytes,Optional<RawJson> differentToken)throws Exception {
        var request=request(council,contract.operation());var full=StrictJson.parse(bytes);String id=full.get("request_id").textValue();
        var encoded=contract.prepare(request,id);assertEquals(contract.operation().value(),encoded.step());
        var binding=new GuardEvidence(request.before(),request.source(),request.sessionId(),BigInteger.ONE,request.operation(),REF,REF,
                "protocol-data-without-native-qualification",NOW,NOW.plusSeconds(30));
        var guard=new PlanningReadGuard(binding,true,true,true,"b".repeat(64));
        var token=differentToken.orElseGet(()->new RawJson(StrictJson.canonical(full.get("result"))));
        var ack=new NativeActionPort.AckReceived(id,true,Optional.of(token),new RawJson(bytes),NativeWire.packet(bytes));
        return new PlanningReadReceipt(request,contract.contractId(),id,guard,guard,ack);
    }
    private static CouncilModels.Candidates council(byte[] bytes)throws Exception {
        var contract=new GovernanceNativeReads(REF,"1.20.0.2",SHA2).council();
        return contract.decode(receipt(contract,true,bytes,Optional.empty()));
    }
    @Test void unchangedActualCouncilOuterPublicEightAndInnerNativeSevenDecodeAsHistoricalData()throws Exception {
        byte[] original=fixture(COUNCIL_FIXTURE);var decoded=council(original);
        assertEquals(BigInteger.valueOf(8),decoded.frame().publicRevision());assertEquals(BigInteger.valueOf(7),decoded.frame().nativeRevision());
        assertEquals(16777217,decoded.frame().ownerId());assertEquals(2,decoded.candidates().size());
        assertEquals(16777232,decoded.candidates().get(0).characterId());
        var nativePayload=StrictJson.parse(original).get("result").get("council_composition_candidates");var normalized=StrictJson.parse(decoded.original().bytes());
        assertEquals(6,normalized.size());
        for(var field:org.xar.ck3.control.governance.council.CouncilCodec.PAYLOAD_FIELDS)assertEquals(nativePayload.get(field),normalized.get(field));
        assertArrayEquals(original,fixture(COUNCIL_FIXTURE));
    }
    @Test void actualCouncilSchemaIsMandatoryExactAndDoesNotAdmitUnknownOuterFields()throws Exception {
        byte[] original=fixture(COUNCIL_FIXTURE);
        for(var token:List.of("null","true","1","\"xar.ck3.council-application-main/v2\"","\"xar.ck3.other/v1\"")) {
            var full=(ObjectNode)StrictJson.parse(original);((ObjectNode)full.get("result")).set("schema",StrictJson.parse(token.getBytes(StandardCharsets.UTF_8)));
            assertThrows(IllegalArgumentException.class,()->council(StrictJson.canonical(full)));
        }
        var missing=(ObjectNode)StrictJson.parse(original);((ObjectNode)missing.get("result")).remove("schema");
        assertThrows(IllegalArgumentException.class,()->council(StrictJson.canonical(missing)));
        var extra=(ObjectNode)StrictJson.parse(original);((ObjectNode)extra.get("result")).put("qualification",true);
        assertThrows(IllegalArgumentException.class,()->council(StrictJson.canonical(extra)));
    }
    @Test void realOuterPublicAndInnerNativeRevisionsHaveIndependentStrictGuards()throws Exception {
        byte[] original=fixture(COUNCIL_FIXTURE);
        for(var revision:List.of(7,9)) {
            var wrong=(ObjectNode)StrictJson.parse(original);((ObjectNode)wrong.get("result")).put("snapshot_revision",revision);
            assertThrows(IllegalArgumentException.class,()->council(StrictJson.canonical(wrong)));
        }
        for(var field:List.of("public_revision","native_revision")) {
            var wrong=(ObjectNode)StrictJson.parse(original);var snapshot=(ObjectNode)wrong.get("result").get("council_composition_candidates").get("snapshot");
            snapshot.put(field,field.equals("public_revision")?7:8);
            assertThrows(IllegalArgumentException.class,()->council(StrictJson.canonical(wrong)));
        }
        var bool=(ObjectNode)StrictJson.parse(original);((ObjectNode)bool.get("result")).put("snapshot_revision",true);
        assertThrows(IllegalArgumentException.class,()->council(StrictJson.canonical(bool)));
    }
    @Test void actualNativeMetadataMustMatchItsConnectedBuildAndCannotQualifyPointFour()throws Exception {
        byte[] original=fixture(COUNCIL_FIXTURE);
        for(var version:List.of("1.20.0.3","1.20.0.4")) {
            var contract=new GovernanceNativeReads(REF,version,version.equals("1.20.0.3")?SHA3:SHA4).council();
            assertThrows(IllegalArgumentException.class,()->contract.decode(receipt(contract,true,original,Optional.empty())));
        }
        var wrong=(ObjectNode)StrictJson.parse(original);((ObjectNode)wrong.get("result").get("council_composition_candidates")).put("schema","xar.ck3.council-composition-candidates/v2");
        assertThrows(IllegalArgumentException.class,()->council(StrictJson.canonical(wrong)));
    }
    @Test void developmentKeepsItsOwnNativeOuterRevisionAndDoesNotAcquireCouncilSchema()throws Exception {
        byte[] original=fixture(DEVELOPMENT_FIXTURE);var contract=new GovernanceNativeReads(REF,"1.20.0.3",SHA3).development();
        assertNotNull(contract.decode(receipt(contract,false,original,Optional.empty())));
        var wrong=(ObjectNode)StrictJson.parse(original);((ObjectNode)wrong.get("result")).put("snapshot_revision",177);
        assertThrows(IllegalArgumentException.class,()->contract.decode(receipt(contract,false,StrictJson.canonical(wrong),Optional.empty())));
        var injected=(ObjectNode)StrictJson.parse(original);((ObjectNode)injected.get("result")).put("schema",GovernanceNativeReads.COUNCIL_ENVELOPE_SCHEMA);
        assertThrows(IllegalArgumentException.class,()->contract.decode(receipt(contract,false,StrictJson.canonical(injected),Optional.empty())));
    }
    @Test void decodedNativeFrameCannotBeReplacedByADifferentResultToken()throws Exception {
        byte[] original=fixture(COUNCIL_FIXTURE);var token=((ObjectNode)StrictJson.parse(original).get("result")).deepCopy();token.put("backend_id","different-native-result");
        var contract=new GovernanceNativeReads(REF,"1.20.0.2",SHA2).council();
        assertThrows(IllegalArgumentException.class,()->contract.decode(receipt(contract,true,original,Optional.of(new RawJson(StrictJson.canonical(token))))));
    }
}
