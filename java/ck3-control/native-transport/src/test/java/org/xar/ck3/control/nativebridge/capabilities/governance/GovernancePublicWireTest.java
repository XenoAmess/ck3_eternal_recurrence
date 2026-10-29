package org.xar.ck3.control.nativebridge.capabilities.governance;

import com.fasterxml.jackson.databind.JsonNode;
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
import org.xar.ck3.control.nativebridge.NativeWire;
import static org.junit.jupiter.api.Assertions.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;

/** Public width DATA regression. Derived large-width software packets and synthetic guards grant no live build or Root qualification. */
final class GovernancePublicWireTest {
    private static final BigInteger MAX=new BigInteger("18446744073709551615"),NATIVE=MAX.subtract(BigInteger.ONE);
    private static final ExactRef REF=new ExactRef("synthetic-governance-public64",1,"a".repeat(64));
    private static final Instant NOW=Instant.parse("2026-10-24T00:00:00Z");
    private static JsonNode token(String value) {return StrictJson.parse(value.getBytes(StandardCharsets.UTF_8));}
    private static RawJson raw(ObjectNode value) {return new RawJson(StrictJson.canonical(value));}
    private static ObjectNode council(JsonNode revision) {
        var value=StrictJson.object().put("expected_snapshot_id","native:council12002").put("date_raw",53178264).put("owner_character_id",16777217);
        value.set("public_revision",revision);value.set("native_revision",revision);return value;
    }
    private static ObjectNode change(JsonNode revision) {
        var value=StrictJson.object().put("councillor_character_id",33554449).put("target_county_title_id",67108874).put("replace_existing_task",true);
        value.set("expected_revision",revision);return value;
    }
    @Test void safeNumericAndFullWidthDecimalInputsShareOneTypedRequestAndCanonicalEncoder() {
        for(var value:List.of("1","9007199254740991","\"1\"","\"9007199254740992\"","\"18446744073709551615\"")) {
            var scalar=token(value);var expected=scalar.isTextual()?new BigInteger(scalar.textValue()):scalar.bigIntegerValue();
            var council=GovernancePublicService.decodeCouncil(raw(council(scalar)));assertEquals(expected,council.requested().publicRevision());
            var councilWire=GovernancePublicService.encodeCouncilRequest(council);assertEquals(expected.toString(),StrictJson.parse(councilWire.bytes()).get("public_revision").textValue());
            assertEquals(council,GovernancePublicService.decodeCouncil(councilWire));
            var development=StrictJson.object();development.set("expected_revision",scalar);
            var dev=GovernancePublicService.decodeDevelopment(raw(development));assertEquals(dev,GovernancePublicService.decodeDevelopment(GovernancePublicService.encodeDevelopmentRequest(dev)));
            var action=GovernancePublicService.decodeChange(raw(change(scalar)));assertEquals(action,GovernancePublicService.decodeChange(GovernancePublicService.encodeChangeRequest(action)));
            assertEquals(expected,dev.expectedRevision());assertEquals(expected,action.expectedRevision());
        }
        assertEquals(BigInteger.ZERO,GovernancePublicService.decodeDevelopment(new RawJson("{\"expected_revision\":\"0\"}".getBytes(StandardCharsets.UTF_8))).expectedRevision());
        assertThrows(IllegalArgumentException.class,()->GovernancePublicService.decodeCouncil(raw(council(token("\"0\"")))));
        assertThrows(IllegalArgumentException.class,()->GovernancePublicService.decodeChange(raw(change(token("0")))));
    }
    @Test void unsafeNumbersNoncanonicalTextMissingAndNullDoNotAlias() {
        for(var value:List.of("true","1.0","1e0","-1","9007199254740992","18446744073709551615","null","\"01\"","\"-0\"","\"+1\"","\" 1\"","\"1 \"","\"1e3\"","\"18446744073709551616\"")) {
            var scalar=token(value);var development=StrictJson.object();development.set("expected_revision",scalar);
            assertThrows(IllegalArgumentException.class,()->GovernancePublicService.decodeDevelopment(raw(development)),value);
            assertThrows(IllegalArgumentException.class,()->GovernancePublicService.decodeCouncil(raw(council(scalar))),value);
            assertThrows(IllegalArgumentException.class,()->GovernancePublicService.decodeChange(raw(change(scalar))),value);
        }
        assertThrows(IllegalArgumentException.class,()->GovernancePublicService.decodeDevelopment(raw(StrictJson.object())));
        var missing=council(token("1"));missing.remove("native_revision");assertThrows(IllegalArgumentException.class,()->GovernancePublicService.decodeCouncil(raw(missing)));
        var extra=change(token("1"));extra.put("native_revision","1");assertThrows(IllegalArgumentException.class,()->GovernancePublicService.decodeChange(raw(extra)));
    }
    @Test void characterAndCountyRequestIdsKeepTheirOriginalInt31NumericBoundary() {
        for(var value:List.of("\"16777217\"","true","2147483648")) {
            var invalid=council(token("1"));invalid.set("owner_character_id",token(value));assertThrows(IllegalArgumentException.class,()->GovernancePublicService.decodeCouncil(raw(invalid)));
            var action=change(token("1"));action.set("councillor_character_id",token(value));assertThrows(IllegalArgumentException.class,()->GovernancePublicService.decodeChange(raw(action)));
        }
    }
    private static byte[] fixture(boolean council)throws Exception {
        String repository=System.getProperty("xar.repository.root");assertNotNull(repository,"required original fixture repository missing");
        return Files.readAllBytes(Path.of(repository,council?"ck3_autonomous_player/tests/fixtures/native_12002/governance/council-query.json":"ck3_autonomous_player/tests/fixtures/steward_develop_county_12003_material/develop_material_available.json"));
    }
    private static <T> PlanningReadResult.Known<T> original(ReadContract<T> contract,boolean council,byte[] packet)throws Exception {
        var source=new G2Source("governance-width-fixture",NOW.toString(),council?"1.20.0.2":"1.20.0.3",REF);
        var observed=new ObservationIdentity(source.machineId(),new GameGeneration(123,new PythonOnlyUInt64(new BigInteger("133700000000000001"))),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(council?16777217:16777258),NATIVE,BigInteger.valueOf(council?53178264:53328600)),
                        council?"native:council12002":"material-fixture:177",MAX,"width-data-only"),1);
        var request=new PlanningReadRequest(observed,source,"synthetic-width-session",contract.operation(),new Obj(java.util.Map.of()),NOW.plusSeconds(30));
        var frame=StrictJson.parse(packet);String id=frame.get("request_id").textValue();contract.prepare(request,id);
        var binding=new GuardEvidence(observed,source,request.sessionId(),BigInteger.ONE,contract.operation(),REF,REF,"software-data-no-native-authority",NOW,NOW.plusSeconds(30));
        var guard=new PlanningReadGuard(binding,true,true,true,"b".repeat(64));
        var ack=new NativeActionPort.AckReceived(id,true,Optional.of(new RawJson(StrictJson.canonical(frame.get("result")))),new RawJson(packet),NativeWire.packet(packet));
        var receipt=new PlanningReadReceipt(request,contract.contractId(),id,guard,guard,ack);return new PlanningReadResult.Known<>(contract.decode(receipt),receipt,REF);
    }
    @Test void councilPublicOutputKeepsFullWidthValuesAndLeavesTheOriginalNumericPacketUntouched()throws Exception {
        byte[] retained=fixture(true);var full=(ObjectNode)StrictJson.parse(retained);var result=(ObjectNode)full.get("result");result.put("snapshot_revision",MAX).put("query_sequence",MAX);
        var snapshot=(ObjectNode)result.get("council_composition_candidates").get("snapshot");snapshot.put("public_revision",MAX).put("native_revision",NATIVE);
        byte[] software=StrictJson.canonical(full);var reads=new GovernanceNativeReads(REF,"1.20.0.2","AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D");
        var known=original(reads.council(),true,software);var output=StrictJson.parse(GovernancePublicService.encodeCouncil(new GovernancePublicService.CouncilReply(known.value(),known)).bytes());
        for(var field:List.of("snapshot_revision","query_sequence","queried_revision"))assertEquals(MAX.toString(),output.get(field).textValue());
        assertEquals(NATIVE.toString(),output.get("queried_native_revision").textValue());
        assertEquals(MAX.toString(),output.get("request").get("public_revision").textValue());assertEquals(NATIVE.toString(),output.get("council_composition_candidates").get("snapshot").get("native_revision").textValue());
        assertTrue(output.get("request").get("owner_character_id").isIntegralNumber());
        assertEquals(known.value().frame(),GovernancePublicService.decodeCouncil(new RawJson(StrictJson.canonical(output.get("request")))).requested());
        assertArrayEquals(software,known.receipt().original().originalFrame().bytes());assertTrue(StrictJson.parse(software).get("result").get("snapshot_revision").isIntegralNumber());
        assertArrayEquals(retained,fixture(true));
    }
    @Test void developmentUsesExplicitUnsignedAndSignedWidthRolesWithoutStringifyingBusinessIds()throws Exception {
        byte[] retained=fixture(false);var full=(ObjectNode)StrictJson.parse(retained);var result=(ObjectNode)full.get("result");result.put("snapshot_revision",NATIVE).put("query_sequence",MAX);
        var payload=(ObjectNode)result.get("steward_develop_county_candidates");payload.put("snapshot_revision",NATIVE);
        var first=(ObjectNode)payload.get("candidates").get(0);((ObjectNode)first.get("monthly_development_rate")).put("raw",Long.MIN_VALUE);
        var progress=(ObjectNode)first.get("development_progress");((ObjectNode)progress.get("current")).put("raw",Long.MAX_VALUE-1);((ObjectNode)progress.get("maximum")).put("raw",Long.MAX_VALUE);
        byte[] software=StrictJson.canonical(full);var reads=new GovernanceNativeReads(REF,"1.20.0.3","94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6");
        var known=original(reads.development(),false,software);var output=StrictJson.parse(GovernancePublicService.encodeDevelopment(new GovernancePublicService.DevelopmentReply(known.value(),known,Optional.of("native-headless"))).bytes());
        assertEquals(MAX.toString(),output.get("source").get("revision").textValue());assertEquals(NATIVE.toString(),output.get("binding").get("native_revision").textValue());
        var publicFirst=output.get("steward_develop_county_candidates").get("candidates").get(0);
        assertEquals(Long.toString(Long.MIN_VALUE),publicFirst.get("monthly_development_rate").get("raw").textValue());
        assertEquals(Long.toString(Long.MAX_VALUE),publicFirst.get("development_progress").get("maximum").get("raw").textValue());
        assertEquals(67108874,publicFirst.get("county_title_id").intValue());assertEquals(100000,publicFirst.get("monthly_development_rate").get("scale").intValue());
        assertEquals(Long.MIN_VALUE,new BigInteger(publicFirst.get("monthly_development_rate").get("raw").textValue()).longValueExact());
        assertEquals(Long.MAX_VALUE,new BigInteger(publicFirst.get("development_progress").get("maximum").get("raw").textValue()).longValueExact());
        var next=StrictJson.object();next.set("expected_revision",output.get("binding").get("expected_revision"));
        assertEquals(MAX,GovernancePublicService.decodeDevelopment(raw(next)).expectedRevision());
        assertArrayEquals(software,known.receipt().original().originalFrame().bytes());assertArrayEquals(retained,fixture(false));
    }
}
