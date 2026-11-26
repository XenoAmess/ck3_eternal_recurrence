package org.xar.ck3.control.service.root;

import java.nio.file.Path;
import java.time.Instant;
import java.util.Base64;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.CompositeOperatorQuarantineRequest;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.session.OrdinaryCycleTransitions;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.SavedContinuityBootstrap;
import org.xar.ck3.control.continuity.writer.WriterContracts;
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
    @Test void importedRecoveryVersionRetainsHistoricalRequestAndExactPredecessorSeparately() {
        var ordinary=request();var root=ordinary.evidenceDirectory().getParent();var now=ordinary.issuedAt();
        var imported=new RootLoadedReplacementRecoveryInputs.ImportedRequest(ordinary.machineId(),now,now.plusSeconds(90),
                ref(root,"historical-exact3"),ordinary.ownerDescriptor(),ordinary.parentControl(),ordinary.generationClaim(),
                ordinary.evidenceDirectory(),58,"c".repeat(64));
        byte[] raw=RootLoadedReplacementRecoveryInputs.encodeImported(imported);
        assertEquals(imported,RootLoadedReplacementRecoveryInputs.decodeImported(raw));
        assertThrows(IllegalArgumentException.class,()->RootLoadedReplacementRecoveryInputs.decode(raw));
        assertThrows(IllegalArgumentException.class,()->RootLoadedReplacementRecoveryInputs.decodeImported(RootLoadedReplacementRecoveryInputs.encode(ordinary)));
        var edited=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(raw);
        edited.put("expected_predecessor_sequence",true);
        assertThrows(IllegalArgumentException.class,()->RootLoadedReplacementRecoveryInputs.decodeImported(StrictJson.canonical(edited)));
        edited.put("expected_predecessor_sequence",58).put("deadline_utc",now.plusSeconds(2701).toString());
        assertThrows(IllegalArgumentException.class,()->RootLoadedReplacementRecoveryInputs.decodeImported(StrictJson.canonical(edited)));
        edited.put("deadline_utc",now.plusSeconds(90).toString());
        ((com.fasterxml.jackson.databind.node.ObjectNode)edited.get("parent_control")).put("bytes",65537);
        assertThrows(IllegalArgumentException.class,()->RootLoadedReplacementRecoveryInputs.decodeImported(StrictJson.canonical(edited)));
    }

    @Test void importedPreAttachGateSeparatesArchivedCampaignEpisodeFromRetiredRuntimeOwner()throws Exception {
        String resource="/org/xar/ck3/control/application/session/source56-interrupted-recovery-prefix.json.gz";
        com.fasterxml.jackson.databind.node.ObjectNode archived;
        try(var original=getClass().getResourceAsStream(resource)) {
            assertNotNull(original);
            try(var compressed=new GZIPInputStream(original)) {
                var fixture=StrictJson.parse(compressed.readNBytes(1<<20),1<<20);
                byte[] snapshot=Base64.getDecoder().decode(fixture.get("head").textValue());
                assertEquals("2712b29737154b0fa7ac10c814961fb36f310df560aaf3f566d3438f77656718",ActionCodec.sha256(snapshot));
                archived=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(snapshot,1<<20);
            }
        }
        var entry=SavedContinuityBootstrap.request((com.fasterxml.jackson.databind.node.ObjectNode)archived.get(
                SavedContinuityBootstrap.FIELD)).detailsObject();
        var owner=OrdinaryCycleTransitions.sessionFromJson(entry.get("session"));
        String episode=archived.path("latest_binding").path("episode_run_id").textValue();
        assertNotEquals(episode,owner.sessionId());
        var originalHead=head(archived,owner);
        assertEquals(57,originalHead.state().sequence());
        assertEquals("0f11c4aef77c2529e60a790bea068cd425fac9d61a949db27ac272ebf9f1ee1c",originalHead.digest());
        var retiredMetadata=head(archived.deepCopy().put("sequence",58),owner);
        var ordinary=request();var root=ordinary.evidenceDirectory().getParent();var now=ordinary.issuedAt();
        var originalDecision=new CompositeOperatorQuarantineRequest(ref(root,"decision"),owner.machineId(),owner.game(),episode,
                "actual-life-parent",ordinary.expectedHeadDigest(),ref(root,"action"),57,originalHead.digest(),
                List.of(new CompositeOperatorQuarantineRequest.Child(1,"arm",ordinary.expectedHeadDigest()),
                        new CompositeOperatorQuarantineRequest.Child(2,"resume",ordinary.expectedHeadDigest())),
                now,now.plusSeconds(30),CompositeOperatorQuarantineRequest.EXITED_LIFE_SCOPE,List.of(),
                Optional.of(new CompositeOperatorQuarantineRequest.ExitedLife(owner.sessionId(),ref(root,"old-terminal"),ordinary.expectedHeadDigest())));
        var input=new RootLoadedReplacementRecoveryInputs.ImportedRequest(owner.machineId(),now,now.plusSeconds(90),
                ref(root,"historical-exact3"),ordinary.ownerDescriptor(),ordinary.parentControl(),ordinary.generationClaim(),
                ordinary.evidenceDirectory(),58,retiredMetadata.digest());
        RootOrdinaryRuntimeAssembly.requireImportedLoadedPredecessor(retiredMetadata,input,originalDecision,owner);
        assertThrows(java.io.IOException.class,()->RootOrdinaryRuntimeAssembly.requireImportedLoadedPredecessor(originalHead,input,originalDecision,owner));
        assertThrows(java.io.IOException.class,()->RootOrdinaryRuntimeAssembly.requireImportedLoadedPredecessor(
                retiredMetadata,input,originalDecision,new SessionIdentity(owner.machineId(),owner.game(),episode)));
        var later=head(archived.deepCopy().put("sequence",59),owner);
        assertThrows(java.io.IOException.class,()->RootOrdinaryRuntimeAssembly.requireImportedLoadedPredecessor(later,input,originalDecision,owner));
    }
    private static WriterContracts.Head head(com.fasterxml.jackson.databind.JsonNode value,SessionIdentity owner) {
        return new WriterContracts.Head(ContinuityState.fromJson(value,owner.machineId()),List.of(),List.of(),List.of(),false);
    }

    private static RootLoadedReplacementRecoveryInputs.Request request() {
        Path root=Path.of("loaded-source-contract").toAbsolutePath();Instant at=Instant.now();
        return new RootLoadedReplacementRecoveryInputs.Request("machine",at,at.plusSeconds(2700),ref(root,"config"),
                ref(root,"owner"),ref(root,"parent"),ref(root,"claim"),ref(root,"pair"),ref(root,"profile"),ref(root,"policy"),
                root.resolve("fresh-evidence"),"a".repeat(64));
    }
    private static ExactRef ref(Path root,String name){return new ExactRef(root.resolve(name+".json").toString(),1,"b".repeat(64));}
}

