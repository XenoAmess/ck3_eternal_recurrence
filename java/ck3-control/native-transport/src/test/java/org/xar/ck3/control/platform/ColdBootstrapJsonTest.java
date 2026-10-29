package org.xar.ck3.control.platform;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FileStatIdentity;
import static org.junit.jupiter.api.Assertions.*;

final class ColdBootstrapJsonTest {
    private static final String SHA="a".repeat(64);
    private static ExactRef ref(String name){return new ExactRef("D:/cold/"+name,123,SHA);}
    private static ColdBootstrapJson.PhysicalData data() {
        return new ColdBootstrapJson.PhysicalData("xar.java-cold-physical-bootstrap/v1","machine-test","request","session",
                new WindowsJobProcess.ProcessIdentity(123,"134373474898765883","D:/Game/ck3.exe"),"\\\\.\\pipe\\test","18446744073709551615",
                ref("hello"),ref("offline"),ref("launch"),ref("save.ck3"),new FileStatIdentity(BigInteger.valueOf(123),"18446744073709551615","1792857600000000001"),
                new SharedSourceFiles.NativeFile("18446744073709551615","340282366920938463463374607431768211455","4294967295","ffffffffffffffff",
                        "134373474898765883","134373474898765884","134373474898765885",123,4096,1),
                "2026-10-25T00:00:00Z","2026-10-25T00:01:00Z");
    }
    private static ObjectNode tree()throws IOException{return (ObjectNode)ControlBuild.strictMapper().readTree(ColdBootstrapJson.encodePhysical(data()));}
    private static byte[] bytes(ObjectNode value)throws IOException{return ControlBuild.strictMapper().writeValueAsBytes(value);}
    @Test void producerConsumerRoundTripPreservesWideDecimalIdentities()throws Exception {
        assertEquals(data(),ColdBootstrapJson.decodePhysical(ColdBootstrapJson.encodePhysical(data())));
        var adoption=new ColdBootstrapJson.AdoptionData("xar.java-cold-canonical-bootstrap/v1","private",ref("physical"),SHA,12,SHA,ref("full-driver"),"2026-10-25T00:00:00Z");
        assertEquals(adoption,ColdBootstrapJson.decodeAdoption(ColdBootstrapJson.encodeAdoption(adoption)));
    }
    @Test void everyRootFieldMissingNullOrUnexpectedRejects()throws Exception {
        var original=tree();var names=new java.util.ArrayList<String>();original.fieldNames().forEachRemaining(names::add);
        for(String name:names){var missing=original.deepCopy();missing.remove(name);assertThrows(IOException.class,()->ColdBootstrapJson.decodePhysical(bytes(missing)),name);
            var nil=original.deepCopy();nil.putNull(name);assertThrows(IOException.class,()->ColdBootstrapJson.decodePhysical(bytes(nil)),name);}
        var extra=tree();extra.put("prepared",true);assertThrows(IOException.class,()->ColdBootstrapJson.decodePhysical(bytes(extra)));
    }
    @Test void numbersBooleanFloatAndRoundedIdsReject()throws Exception {
        for(String field:java.util.List.of("connection_generation","observed_at_utc","deadline_utc")){
            var number=tree();number.put(field,9007199254740992L);assertThrows(IOException.class,()->ColdBootstrapJson.decodePhysical(bytes(number)));
            var flag=tree();flag.put(field,true);assertThrows(IOException.class,()->ColdBootstrapJson.decodePhysical(bytes(flag)));}
        var birth=tree();((ObjectNode)birth.get("game")).put("creation_filetime_decimal",134373474898765883L);assertThrows(IOException.class,()->ColdBootstrapJson.decodePhysical(bytes(birth)));
        for(String field:java.util.List.of("file_id_decimal","last_write_filetime_decimal")){
            var number=tree();((ObjectNode)number.get("save_native")).put(field,9007199254740992.0);assertThrows(IOException.class,()->ColdBootstrapJson.decodePhysical(bytes(number)));}
        var size=tree();((ObjectNode)size.get("save_stat")).put("bytes",123.0);assertThrows(IOException.class,()->ColdBootstrapJson.decodePhysical(bytes(size)));
    }
    @Test void duplicateTrailingOversizeAndInvalidDatesReject()throws Exception {
        String source=new String(ColdBootstrapJson.encodePhysical(data()),java.nio.charset.StandardCharsets.UTF_8);
        assertThrows(IOException.class,()->ColdBootstrapJson.decodePhysical((source+" {}").getBytes(java.nio.charset.StandardCharsets.UTF_8)));
        assertThrows(IOException.class,()->ColdBootstrapJson.decodePhysical(("{\"schema\":\"other\","+source.substring(1)).getBytes(java.nio.charset.StandardCharsets.UTF_8)));
        assertThrows(IOException.class,()->ColdBootstrapJson.decodePhysical(new byte[ColdBootstrapJson.MAX_BYTES+1]));
        var bad=tree();bad.put("deadline_utc","2026-10-24T00:00:00Z");assertThrows(IOException.class,()->ColdBootstrapJson.decodePhysical(bytes(bad)));
    }
}
