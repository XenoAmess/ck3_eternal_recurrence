package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.NativeWire;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;

/** Requires output of actual native feature reader/callback/serializer fixture. Missing input fails; no synthetic Java stand-in or live credit. */
final class WarCurrentClaimInputsNativeFixtureTest {
    private static final int WAR = 0x05000001, ACTOR = 0x04000001;
    private static final Instant OBSERVED = Instant.parse("2026-10-24T00:00:00Z"), DEADLINE = OBSERVED.plusSeconds(60);
    private static final ExactRef SOURCE = new ExactRef("synthetic-native-fixture-no-live-credit", 1, "a".repeat(64));
    private static final PlanningReadPort NO_IO = new PlanningReadPort() {
        @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract, PlanningReadRequest request) { throw new AssertionError("fixture replay must never send native I/O"); }
    };
    @Test void actualNativeProducerPacketRunsThroughInstalledReadContractReplayAndRoundTrip() throws Exception {
        var f = fixture(); var top = packet(); var receipt = receipt(f, top);
        var actual = f.contract().decode(receipt); assertEquals(actual, f.contract().replay(receipt));
        var inputs = actual.inputs(); assertEquals(WAR, inputs.warId()); assertEquals(2, inputs.targets().size());
        assertEquals(WarCurrentClaimInputs.ClaimState.STRONG_EXPLICIT, inputs.targets().getFirst().effectiveClaim().state()); assertEquals(WarCurrentClaimInputs.ClaimState.ABSENT, inputs.targets().getLast().effectiveClaim().state());
        assertFalse(inputs.targets().getFirst().holderInPlayerRealm()); assertTrue(inputs.targets().getLast().holderInPlayerRealm());
        assertEquals(BigInteger.valueOf(5), actual.querySequence().value());
        assertEquals(List.of(0x07000002), inputs.playerHeldDeclaredTargets()); assertEquals(List.of(0x07000002), inputs.playerRealmDeclaredTargets());
        assertFalse(inputs.completeSettlementTerms()); assertFalse(inputs.additionalTerritoryEffectsEvaluated()); assertFalse(inputs.loadedScriptSourceVerified()); assertFalse(actual.actionAuthority());
        assertEquals(inputs, WarCurrentClaimInputs.normalize(WarCurrentClaimInputs.encode(inputs), WAR, f.selection().context()));
        var request = f.contract().prepare(f.request(), "claim-fixture"); assertEquals(ReadContract.WireProfile.G2_PRIVATE_QUERY, f.contract().wireProfile());
        assertTrue(request.requiredCapability().isEmpty()); assertTrue(parse(request.additionalFields().bytes()).isEmpty());
    }
    @Test void wrongSourceOrAuthorityAndMissingNullableFieldsCannotBeAccepted() throws Exception {
        var f=fixture();
        for (String field : List.of("complete_settlement_terms", "additional_territory_effects_evaluated", "loaded_script_source_verified")) {
            var changed=packet();domain(changed).put(field,true);assertThrows(IllegalArgumentException.class,()->f.contract().replay(receipt(f,changed)));
        }
        var wrong=packet();domain(wrong).put("executable_sha256", "b".repeat(64));assertThrows(IllegalArgumentException.class,()->f.contract().replay(receipt(f,wrong)));
        var missing=packet();((ObjectNode)domain(missing).path("title_holders").get(0)).remove("holder_top_liege_character_id");
        assertThrows(IllegalArgumentException.class,()->f.contract().replay(receipt(f,missing)));
    }
    @Test void nativeIntegerAndCompleteOrderedCollectionsStayStrict() throws Exception {
        var f=fixture();
        var bad=packet();domain(bad).put("native_revision",true);assertThrows(IllegalArgumentException.class,()->f.contract().replay(receipt(f,bad)));
        var floating=packet();domain(floating).put("war_id",(double)WAR);assertThrows(IllegalArgumentException.class,()->f.contract().replay(receipt(f,floating)));
        var incomplete=packet();((com.fasterxml.jackson.databind.node.ArrayNode)domain(incomplete).path("title_holders")).remove(1);
        assertThrows(IllegalArgumentException.class,()->f.contract().replay(receipt(f,incomplete)));
        var flags=packet();((ObjectNode)domain(flags).path("claims").get(0)).put("state","absent");assertThrows(IllegalArgumentException.class,()->f.contract().replay(receipt(f,flags)));
        var stale=packet();domain(stale).put("actor_character_id",ACTOR+1);assertThrows(IllegalArgumentException.class,()->f.contract().replay(receipt(f,stale)));
        var extra=packet();domain(extra).put("invented_settlement",true);assertThrows(IllegalArgumentException.class,()->f.contract().replay(receipt(f,extra)));
    }
    private static ObjectNode domain(ObjectNode packet) { return object(packet.path("result").path(WarCurrentClaimInputs.DOMAIN)); }
    private static ObjectNode packet() throws Exception {
        String supplied=System.getProperty("xar.ck3.currentClaimInputs.nativeFixture");
        assertNotNull(supplied, "Root must execute the native callback/serializer fixture and supply its exact emitted packet path");
        Path p=Path.of(supplied);assertTrue(Files.isRegularFile(p),"actual native fixture packet is missing");return parse(Files.readAllBytes(p));
    }
    private record Fixture(WarCurrentClaimInputsRead.Selection selection, ReadContract<WarCurrentClaimInputsRead.Observation> contract, PlanningReadRequest request) { }
    private static Fixture fixture() {
        var reads=new WarCurrentClaimInputsRead(SOURCE,SOURCE,NO_IO);var selected=new WarCurrentClaimInputsRead.Selection(frame(),WAR);
        var catalog=new RootReadContractCatalog(List.of(),reads.families());return new Fixture(selected,reads.contract(catalog,selected),reads.request(selected));
    }
    private static ArmyRetreatFrames.Current frame() {
        var source=new G2Source("synthetic-native-fixture-no-live-credit",OBSERVED.toString(),"1.20.0.4",SOURCE);
        var key=new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(ACTOR),BigInteger.valueOf(3),BigInteger.valueOf(77)),"native:3",BigInteger.TWO,"claim-fixture");
        var identity=new ObservationIdentity(source.machineId(),new GameGeneration(42,new PythonOnlyUInt64(BigInteger.ONE)),key,1);
        ObjectNode raw=empty().put("paused",true).put("map_ready",true).put("snapshot_id","native:3").put("revision",2).put("native_revision",3).put("date_raw",77).put("episode_run_id","claim-fixture");
        raw.putObject("played_character").put("character_id",ACTOR).put("alive",true);
        var diagnostics=raw.putObject("diagnostics").put("connection_generation",1);
        diagnostics.putObject("hello").put("expected_ck3_version",WarCurrentClaimInputs.VERSION).put("expected_ck3_sha256",WarCurrentClaimInputs.EXE);
        var war=raw.putArray("active_wars").addObject().put("war_id",WAR).put("player_side","attacker").put("player_relative_war_score",0);
        war.putArray("targeted_title_ids").add(0x07000001).add(0x07000002);war.putArray("war_objective_province_ids");war.putArray("allied_armies");war.putArray("enemy_armies");
        return new ArmyRetreatFrames.Current(new Complete(identity,source,"claim-fixture-session",BigInteger.ONE,DriverJson.object(bytes(raw),DriverJson.MAX_NATIVE_BYTES),SOURCE,OBSERVED,"b".repeat(64)),DEADLINE);
    }
    private static PlanningReadReceipt receipt(Fixture f,ObjectNode packet) throws Exception {
        var c=f.selection().context();var operation=f.contract().operation();
        var guard=new PlanningReadGuard(new GuardEvidence(c.before(),c.source(),c.sessionId(),BigInteger.ONE,operation,SOURCE,SOURCE,"synthetic-native-fixture-source",OBSERVED,DEADLINE),true,true,true,"b".repeat(64));
        var full=new RawJson(bytes(packet));String id=packet.path("request_id").textValue();
        var ack=new NativeActionPort.AckReceived(id,true,Optional.of(new RawJson(bytes(packet.path("result")))),full,NativeWire.packet(full.bytes()));
        return new PlanningReadReceipt(f.request(),f.contract().contractId(),id,guard,guard,ack);
    }
}
