package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild.FileRef;

final class SharedOwnedCommandTest {
    @TempDir Path root;
    private static final String HASH="0".repeat(64);

    private ObjectNode reference(String name) {
        ObjectNode ref=ControlBuild.strictMapper().createObjectNode();
        ref.put("path",root.resolve(name).toString());ref.put("bytes",0);ref.put("sha256",HASH);return ref;
    }
    private ObjectNode binding() {
        ObjectNode value=ControlBuild.strictMapper().createObjectNode();
        value.put("schema",SharedOwnedCommandBinding.SCHEMA);value.put("machine_id","fixture-machine-123");
        value.set("launcher_source_ref",reference("SharedOwnedCommand.java"));
        value.set("standing_ref",reference("runtime01.json"));value.set("delivery_ref",reference("delivery01.json"));
        value.put("native_temporary_root",root.resolve("native-tmp").toString());
        value.put("private_temporary_aggregate_root",root.resolve("private-tmp").toString());
        value.putObject("standing_expectation").put("schema","standing/v1").put("status","ADMITTED01");
        value.putObject("delivery_expectation").put("schema","delivery/v1").put("status","ACCEPTED01");return value;
    }
    private ObjectNode request() {
        ObjectNode value=ControlBuild.strictMapper().createObjectNode();
        value.put("schema","xar.shared-owned-command-spec/v2");value.put("machine_id","fixture-machine-123");
        value.put("owner","/root/test_owner");value.put("coordinator","/root/g2_java_delivery");value.put("slot_id","common-0");
        value.putNull("borrowed_slot_id");value.put("run_id","finite01");value.set("standing_ref",reference("runtime01.json"));
        value.set("launcher_source_ref",reference("SharedOwnedCommand.java"));value.set("executable",reference("java.exe"));
        value.putArray("arguments").add("-version");value.put("cwd",root.toString());value.putObject("environment");
        value.putArray("inputs");value.put("output_root",root.resolve("output/test_owner/finite01").toString());
        value.put("timeout_seconds",1);value.put("memory_limit_bytes",268435456);
        value.put("root_exit_drain_policy","UNTIL_COMMAND_DEADLINE");value.putNull("operation_card_ref");
        value.put("temporary_policy","SLOT_PRIVATE");return value;
    }

    @Test void exactBindingRoundTripRetainsAllTypedFields() throws Exception {
        SharedOwnedCommandBinding first=SharedOwnedCommandBinding.parse(binding());
        JsonNode encoded=first.toJson();
        SharedOwnedCommandBinding second=SharedOwnedCommandBinding.parse(encoded);
        assertEquals(first,second);assertEquals(root.resolve("private-tmp"),second.privateTemporaryAggregateRoot());
        assertEquals("fixture-machine-123",second.machineId());
    }
    @Test void newWindowUsesNewDataWithSamePackagedSource() throws Exception {
        ObjectNode first=binding(), next=first.deepCopy();
        next.set("standing_ref",reference("runtime02.json"));next.set("delivery_ref",reference("delivery02.json"));
        ((ObjectNode)next.get("standing_expectation")).put("status","ADMITTED02");
        ((ObjectNode)next.get("delivery_expectation")).put("status","ACCEPTED02");
        SharedOwnedCommandBinding a=SharedOwnedCommandBinding.parse(first),b=SharedOwnedCommandBinding.parse(next);
        assertEquals(a.launcherSourceRef(),b.launcherSourceRef());assertNotEquals(a.standingRef(),b.standingRef());
        ObjectNode actual=ControlBuild.strictMapper().createObjectNode().put("schema","standing/v1").put("machine_id",b.machineId()).put("status","ADMITTED02");
        SharedOwnedCommandBinding.verifyAuthority(actual,b.standingExpectation(),b.machineId());
        assertThrows(IOException.class,()->SharedOwnedCommandBinding.verifyAuthority(actual,a.standingExpectation(),a.machineId()));
    }
    @Test void missingUnknownAndNullBindingFieldsAreRejected() {
        ObjectNode missing=binding();missing.remove("standing_ref");
        assertThrows(IOException.class,()->SharedOwnedCommandBinding.parse(missing));
        ObjectNode extra=binding();extra.put("legacy_runtime_alias","old");
        assertThrows(IOException.class,()->SharedOwnedCommandBinding.parse(extra));
        ObjectNode nullable=binding();nullable.putNull("delivery_ref");
        assertThrows(IOException.class,()->SharedOwnedCommandBinding.parse(nullable));
    }
    @Test void referenceBytesRejectBooleanFractionAndOutOfLongRange() throws Exception {
        for(String bad:List.of("true","1.0","9223372036854775808")) {
            ObjectNode value=binding();
            ((ObjectNode)value.get("standing_ref")).set("bytes",ControlBuild.strictMapper().readTree(bad));
            assertThrows(IOException.class,()->SharedOwnedCommandBinding.parse(value),bad);
        }
    }
    @Test void nestedUnknownFieldsAndRelativeRootsAreRejected() {
        ObjectNode extra=binding();((ObjectNode)extra.get("standing_expectation")).put("expiry_alias","old");
        assertThrows(IOException.class,()->SharedOwnedCommandBinding.parse(extra));
        ObjectNode relative=binding();relative.put("native_temporary_root","relative-tmp");
        assertThrows(IOException.class,()->SharedOwnedCommandBinding.parse(relative));
    }
    @Test void exactBindingReaderRejectsChangedFileAndOversize() throws Exception {
        Path path=root.resolve("binding.json");Files.write(path,ControlBuild.strictMapper().writeValueAsBytes(binding()));
        FileRef pin=FileRef.measure(path);assertEquals("fixture-machine-123",SharedOwnedCommandBinding.read(pin).machineId());
        Files.writeString(path,"{}");assertThrows(IOException.class,()->SharedOwnedCommandBinding.read(pin));
        FileRef large=new FileRef(path.toString(),65537,HASH);
        assertThrows(IOException.class,()->SharedOwnedCommandBinding.read(large));
    }
    @Test void requestV2PreservesExplicitNullAndStructuredArguments() throws Exception {
        ObjectNode value=request();SharedOwnedCommand.Request parsed=SharedOwnedCommand.parseRequest(value);
        assertNull(parsed.borrowedSlotId());assertNull(parsed.operationCardRef());assertEquals(List.of("-version"),parsed.arguments());
        assertEquals(SharedOwnedCommand.TemporaryPolicy.SLOT_PRIVATE,parsed.temporaryPolicy());
        value.remove("operation_card_ref");assertThrows(IOException.class,()->SharedOwnedCommand.parseRequest(value));
    }
    @Test void requestV2RejectsWrongScalarTypesAndUnknownKeys() throws Exception {
        for(String key:List.of("timeout_seconds","memory_limit_bytes")) {
            ObjectNode booleanValue=request();booleanValue.put(key,true);assertThrows(IOException.class,()->SharedOwnedCommand.parseRequest(booleanValue));
            ObjectNode fractionValue=request();fractionValue.put(key,1.0);assertThrows(IOException.class,()->SharedOwnedCommand.parseRequest(fractionValue));
        }
        ObjectNode extra=request();extra.put("compatibility_alias","old");
        assertThrows(IOException.class,()->SharedOwnedCommand.parseRequest(extra));
        ObjectNode environment=request();((ObjectNode)environment.get("environment")).put("VALUE",1);
        assertThrows(IOException.class,()->SharedOwnedCommand.parseRequest(environment));
    }
    @Test void canonicalCliCountsRejectWhitespaceSignsAndLeadingZeros() throws Exception {
        assertEquals(0,SharedOwnedCommand.cliRef(root.resolve("empty").toString(),"0",HASH).bytes());
        for(String bad:List.of("+1","01"," 1","1.0","-0"))
            assertThrows(IOException.class,()->SharedOwnedCommand.cliRef(root.resolve("file").toString(),bad,HASH));
    }
    @Test void authorityMachineSchemaAndStatusMustMatchIndividually() throws Exception {
        SharedOwnedCommandBinding parsed=SharedOwnedCommandBinding.parse(binding());
        ObjectNode actual=ControlBuild.strictMapper().createObjectNode().put("schema","standing/v1").put("status","ADMITTED01").put("machine_id",parsed.machineId());
        SharedOwnedCommandBinding.verifyAuthority(actual,parsed.standingExpectation(),parsed.machineId());
        for(String field:List.of("schema","status","machine_id")) {
            ObjectNode bad=actual.deepCopy();bad.put(field,"changed");
            assertThrows(IOException.class,()->SharedOwnedCommandBinding.verifyAuthority(bad,parsed.standingExpectation(),parsed.machineId()));
        }
    }
}
