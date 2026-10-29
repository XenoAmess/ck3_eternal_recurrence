package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;

/** Numeric representation only; Lifecycle's actual formatter/domain tests remain the business producer consumers. */
final class ArmyStructuralPublicWireTest {
    private static final BigInteger U64=new BigInteger("18446744073709551615");
    private static final List<String> FIELDS=List.of("submitted_public_revision","submitted_native_revision","submitted_connection_generation","observed_public_revision","observed_native_revision");
    private static ArmyTypes.Context context() {
        var ref=new ExactRef("software-structural-source-no-native-permit",1,"a".repeat(64));var source=new G2Source("software-structural","2026-10-24T00:00:00Z","1.20.0.4",ref);
        var frame=new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(73),BigInteger.ONE,BigInteger.valueOf(77)),"native:1",BigInteger.ONE,"software-episode");
        return new ArmyTypes.Context(new ObservationIdentity(source.machineId(),new GameGeneration(42,new PythonOnlyUInt64(BigInteger.ONE)),frame,1),source,"software-session",Instant.parse("2026-10-25T00:00:00Z"));
    }
    private static void originalSource()throws Exception {
        String configured=System.getProperty("xar.repository.root");assertNotNull(configured,"mandatory original source fixture");assertFalse(configured.isBlank());
        Path root=Path.of(configured).toRealPath(),source=root.resolve("ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py").toRealPath();assertTrue(source.startsWith(root));
        assertEquals(1658471,Files.size(source));assertEquals("eedcd633cf10b0797c331662507d276f8140195b37c1ed0b605da996ee205603",ActionCodec.sha256(Files.readAllBytes(source)));
    }
    @Test void exactStructuralAndRetainedNativeRequestPathsRoundTripWideCounters()throws Exception {
        originalSource();ObjectNode raw=ArmyJson.empty().put("revision",U64).put("native_revision",U64).put("snapshot_id","native:"+U64);
        ObjectNode action=raw.putObject("war_action").put("status","merge_submitted").put("source_army_id",0).put("destination_army_id",2147483647).put("submitted_date_raw",77);
        FIELDS.forEach(field->action.put(field,U64));action.putArray("player_army_ids_before").add(0).add(2147483647);action.putNull("original_move_target_province_id");
        ObjectNode evidence=raw.putObject("halt_rejection_evidence");evidence.putObject("native_request").put("type","execute_step").put("protocol_version",1).put("expected_revision",U64).put("request_id","same-original-request");
        evidence.putObject("native_command_result").put("type","command_result").put("protocol_version",1).put("ok",false).put("request_id","same-original-request").put("error","CK3 halt-army command validation failed");
        evidence.putObject("observed_frame").put("revision",U64).put("native_revision",U64).put("connection_generation",U64).put("actor_character_id",73).put("date_raw",77).put("bridge_pid",42);
        var data=DriverJson.object(ArmyJson.bytes(raw),DriverJson.MAX_NATIVE_BYTES);var encoded=ArmyPublicWire.encodeExactSourceBound(data,context());ObjectNode wire=ArmyJson.parse(encoded.bytes());
        for(String field:FIELDS)assertEquals(U64.toString(),wire.path("war_action").path(field).textValue());
        assertEquals(U64.toString(),wire.path("halt_rejection_evidence").path("native_request").path("expected_revision").textValue());
        assertTrue(wire.path("war_action").path("source_army_id").isIntegralNumber());assertTrue(wire.path("war_action").path("original_move_target_province_id").isNull());
        assertFalse(wire.path("halt_rejection_evidence").path("native_command_result").has("result"));
        assertEquals(data,ArmyPublicWire.decodeExactSourceBound(encoded,context()));
    }
    @Test void nullableSourceFieldsStayNullableAndForeignPathsCannotBorrowCounterRoles() {
        ObjectNode raw=ArmyJson.empty();raw.putObject("war_action").putNull("submitted_native_revision");var data=DriverJson.object(ArmyJson.bytes(raw),DriverJson.MAX_NATIVE_BYTES);
        assertEquals(data,ArmyPublicWire.decodeExactSourceBound(ArmyPublicWire.encodeExactSourceBound(data,context()),context()));
        for(var value:List.of(ArmyJson.empty().booleanNode(true),ArmyJson.empty().numberNode(1.0),ArmyJson.empty().textNode(U64.toString()),ArmyJson.empty().numberNode(U64.add(BigInteger.ONE)))) {
            ObjectNode wrong=ArmyJson.empty();wrong.putObject("war_action").set("submitted_native_revision",value);
            assertThrows(IllegalArgumentException.class,()->ArmyPublicWire.encodeExactSourceBound(DriverJson.object(ArmyJson.bytes(wrong),DriverJson.MAX_NATIVE_BYTES),context()));
        }
        ObjectNode foreign=ArmyJson.empty();foreign.putObject("foreign").put("submitted_native_revision",U64);
        assertThrows(IllegalArgumentException.class,()->ArmyPublicWire.encodeExactSourceBound(DriverJson.object(ArmyJson.bytes(foreign),DriverJson.MAX_NATIVE_BYTES),context()));
        ObjectNode encoded=ArmyJson.empty();encoded.putObject("war_action").put("submitted_native_revision","01");
        assertThrows(IllegalArgumentException.class,()->ArmyPublicWire.decodeExactSourceBound(new RawJson(ArmyJson.bytes(encoded)),context()));
    }
}
