package org.xar.ck3.control.application.planning.army;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.driver.DriverJson;

/** Input and DATA boundaries only. No file, launch, frame or native read permission is created. */
public final class H2743StockPredicateAdmissionTest {
    private static ObjectNode pins(){ObjectNode p=JsonNodeFactory.instance.objectNode();p.put("schema",H2743StockPredicateAdmission.PINS_SCHEMA);p.put("source_head","a".repeat(40));for(String k:List.of("pair_sha256","source_manifest_sha256","route_receipt_sha256","dll_sha256","injector_sha256"))p.put(k,"A".repeat(64));return p;}
    @Test public void independentPinsHaveOneExactRosterAndRepresentation(){ObjectNode p=pins();var value=H2743StockPredicateAdmission.decodePins(DriverJson.encodeNode(p));assertEquals("A".repeat(64),value.dllSha256());assertEquals(value,H2743StockPredicateAdmission.decodePins(DriverJson.encodeNode(p)));for(String k:List.of("pair_sha256","source_manifest_sha256","route_receipt_sha256","dll_sha256","injector_sha256")){ObjectNode bad=p.deepCopy();bad.put(k,"a".repeat(64));assertThrows(IllegalArgumentException.class,()->H2743StockPredicateAdmission.decodePins(DriverJson.encodeNode(bad)));}}
    @Test public void missingNullBoolAndExtraPinsCannotEnableStock(){ObjectNode p=pins();for(String k:List.of("source_head","pair_sha256","dll_sha256")){ObjectNode missing=p.deepCopy();missing.remove(k);assertThrows(IllegalArgumentException.class,()->H2743StockPredicateAdmission.decodePins(DriverJson.encodeNode(missing)));ObjectNode nil=p.deepCopy();nil.putNull(k);assertThrows(IllegalArgumentException.class,()->H2743StockPredicateAdmission.decodePins(DriverJson.encodeNode(nil)));ObjectNode bool=p.deepCopy();bool.put(k,true);assertThrows(IllegalArgumentException.class,()->H2743StockPredicateAdmission.decodePins(DriverJson.encodeNode(bool)));}p.put("stockEnabled",true);assertThrows(IllegalArgumentException.class,()->H2743StockPredicateAdmission.decodePins(DriverJson.encodeNode(p)));}
    @Test public void duplicateJsonKeysAndUnsafePathsAreRejected(){String duplicate="{\"schema\":\"wrong\",\"schema\":\""+H2743StockPredicateAdmission.PINS_SCHEMA+"\"}";assertThrows(IllegalArgumentException.class,()->H2743StockPredicateAdmission.decodePins(duplicate.getBytes(StandardCharsets.UTF_8)));assertThrows(IllegalArgumentException.class,()->new H2743StockPredicateAdmission.Input(Path.of("relative.json"),Path.of("pins.json"),Path.of("checkout")));assertThrows(IllegalArgumentException.class,()->new H2743StockPredicateAdmission.FileFact(Path.of("relative"),1,"A".repeat(64)));}
}
