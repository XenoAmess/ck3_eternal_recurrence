package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.file.Path;
import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.readiness.NativeReadiness;
import org.xar.ck3.control.application.session.BatchLimits;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.g2.common.G2Source;

final class RootStartupConfigurationTest {
    private static RootStartupConfiguration original() {
        String sha="1".repeat(64);var source=new ExactRef("D:/fixture/source.json",7,sha);
        return new RootStartupConfiguration("fixture-machine",Instant.parse("2026-10-24T00:00:00Z"),
                new ControlBuild.FileRef("D:/fixture/application.json",11,sha),new ControlBuild.FileRef("D:/fixture/runtime.json",13,sha),
                "root-1",new G2Source("fixture-machine","2026-10-23T12:00:00Z","1.20.0.4",source),new RootStartupConfiguration.FreshRobert("start-robert-1"),
                new RootStartupConfiguration.CheckpointPaths(Path.of("D:/fixture/driver.json"),Path.of("D:/fixture/checkpoint"),Path.of("D:/fixture/attachments"),"lineage-1",Path.of("D:/fixture/robert.ck3")),
                new NativeReadiness.Policy(false,false,Optional.empty(),Duration.ofMillis(25),true),Duration.ofSeconds(30),
                List.of(new BatchLimits("batch-1",5,Duration.ofMinutes(2),Duration.ofSeconds(20),Duration.ofMillis(100),1)),Path.of("D:/fixture/receipts"));
    }
    @Test void completeTypedConfigurationRoundTripsWithoutGrantingAuthority() {
        var before=original();var decoded=RootStartupConfiguration.fromJson(before.toJson());assertEquals(before,decoded);
        assertEquals(before.toJson(),decoded.toJson());assertFalse(decoded.ordinaryPolicy().allowTerminal());assertTrue(decoded.ordinaryPolicy().expectedActor().isEmpty());
    }
    @Test void numericFieldsRejectBooleanFloatAndMissingTokens() {
        var bool=original().toJson();((com.fasterxml.jackson.databind.node.ObjectNode)bool.withArray("batches").get(0)).put("maximum_turns",true);
        assertThrows(IllegalArgumentException.class,()->RootStartupConfiguration.fromJson(bool));
        var decimal=original().toJson();decimal.put("freshness_ms",30.0);assertThrows(IllegalArgumentException.class,()->RootStartupConfiguration.fromJson(decimal));
        var missing=original().toJson();missing.remove("runtime_definitions");assertThrows(IllegalArgumentException.class,()->RootStartupConfiguration.fromJson(missing));
    }
    @Test void coldAdoptionDuplicateBatchAndUnknownFieldsCannotBecomeFreshAdmission() {
        var cold=original().toJson();((com.fasterxml.jackson.databind.node.ObjectNode)cold.get("entry")).put("kind","RESTORE_CHECKPOINT");
        assertThrows(IllegalArgumentException.class,()->RootStartupConfiguration.fromJson(cold));
        var duplicate=original().toJson();duplicate.withArray("batches").add(duplicate.withArray("batches").get(0).deepCopy());
        assertThrows(IllegalArgumentException.class,()->RootStartupConfiguration.fromJson(duplicate));
        var extra=original().toJson();extra.put("qualified",true);assertThrows(IllegalArgumentException.class,()->RootStartupConfiguration.fromJson(extra));
    }
}
