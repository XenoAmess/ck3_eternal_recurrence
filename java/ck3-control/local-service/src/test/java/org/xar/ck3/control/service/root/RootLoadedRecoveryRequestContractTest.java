package org.xar.ck3.control.service.root;

import java.nio.file.Path;
import java.time.Instant;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import static org.junit.jupiter.api.Assertions.*;

final class RootLoadedRecoveryRequestContractTest {
    @Test void sourceWireRejectsForeignFieldsRoundedReferenceSizesAndExtendedWindow() {
        var q=request();byte[] bytes=RootLoadedReplacementRecoveryInputs.encode(q);
        assertEquals(q,RootLoadedReplacementRecoveryInputs.decode(bytes));
        var row=StrictJson.parse(bytes).deepCopy();
        ((com.fasterxml.jackson.databind.node.ObjectNode)row).put("create_game",true);
        assertThrows(IllegalArgumentException.class,()->RootLoadedReplacementRecoveryInputs.decode(StrictJson.canonical(row)));
        var rounded=StrictJson.object(StrictJson.parse(bytes),Set.of("schema","machine_id","issued_at_utc","deadline_utc",
                "runtime_configuration","owner_descriptor","parent_control","generation_claim","checkpoint_pair","current_loaded_profile",
                "saved_policy","evidence_directory","expected_head_digest"));
        ((com.fasterxml.jackson.databind.node.ObjectNode)rounded.get("parent_control")).put("bytes",1.5);
        byte[] malformed;
        try {malformed=new com.fasterxml.jackson.databind.ObjectMapper().writeValueAsBytes(rounded);}
        catch(java.io.IOException invalid){throw new AssertionError(invalid);}
        assertThrows(IllegalArgumentException.class,()->RootLoadedReplacementRecoveryInputs.decode(malformed));
        var expanded=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(bytes);
        expanded.put("deadline_utc",q.issuedAt().plusSeconds(2701).toString());
        assertThrows(IllegalArgumentException.class,()->RootLoadedReplacementRecoveryInputs.decode(StrictJson.canonical(expanded)));
    }
    @Test void materialLaunchReaderUsesActualSnakeProducerAndExactFullProcessBirth() {
        var before=new GameGeneration(145132,new PythonOnlyUInt64(new java.math.BigInteger("134388549310428814")));
        var game=new GameGeneration(178484,new PythonOnlyUInt64(new java.math.BigInteger("134392864266991949")));
        var join=new RootRestoreMaterials.LifecycleJoin("machine","old-session","new-session",before,game,"replacement-original");
        var row=StrictJson.object().put("schema","xar.java-game-lifecycle-event/v1").put("machine_id","machine")
                .put("observed_at_utc",Instant.now().toString()).put("request_id","replacement-original")
                .put("session_id","new-session").put("event","HELLO").putNull("accounting").putNull("terminal")
                .putNull("terminal_kind").put("detail","actual HELLO source shape");
        row.set("game",StrictJson.object().put("pid",178484).put("creation_filetime_decimal","134392864266991949").put("executable","D:/game/ck3.exe"));
        RootRestoreMaterials.requireLoadedLaunch(DriverJson.object(StrictJson.canonical(row),65536),join);
        ((com.fasterxml.jackson.databind.node.ObjectNode)row.get("game")).put("creation_filetime_decimal","134392864266991948");
        assertThrows(IllegalArgumentException.class,()->RootRestoreMaterials.requireLoadedLaunch(DriverJson.object(StrictJson.canonical(row),65536),join));
        ((com.fasterxml.jackson.databind.node.ObjectNode)row.get("game")).put("creation_filetime_decimal","134392864266991949");
        row.put("request_id","another-request");
        assertThrows(IllegalArgumentException.class,()->RootRestoreMaterials.requireLoadedLaunch(DriverJson.object(StrictJson.canonical(row),65536),join));
    }
    private static RootLoadedReplacementRecoveryInputs.Request request() {
        Path root=Path.of("loaded-source-contract").toAbsolutePath();Instant at=Instant.now();
        return new RootLoadedReplacementRecoveryInputs.Request("machine",at,at.plusSeconds(2700),ref(root,"config"),
                ref(root,"owner"),ref(root,"parent"),ref(root,"claim"),ref(root,"pair"),ref(root,"profile"),ref(root,"policy"),
                root.resolve("fresh-evidence"),"a".repeat(64));
    }
    private static ExactRef ref(Path root,String name){return new ExactRef(root.resolve(name+".json").toString(),1,"b".repeat(64));}
}

