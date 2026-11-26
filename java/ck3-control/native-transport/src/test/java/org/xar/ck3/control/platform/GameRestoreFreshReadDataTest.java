package org.xar.ck3.control.platform;

import static org.junit.jupiter.api.Assertions.*;
import java.util.List;
import org.junit.jupiter.api.Test;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.application.checkpoint.RestoreCheckpointService;

/** Archive DATA contract only; no Managed, private window, receiver or restoration is constructed. */
final class GameRestoreFreshReadDataTest {
    private static ExactRef ref(String role){return new ExactRef("D:/source-only/"+role,20,"a".repeat(64));}
    private static GameRestoreNativeAdapter.PairData data(){
        return new GameRestoreNativeAdapter.PairData("restore-original",ref("lifecycle"),ref("save"),
                new GameRestoreNativeAdapter.ReadOriginal(ref("ack-one"),ref("native-one"),"9007199254740993","2026-10-25T02:00:00Z"),
                new GameRestoreNativeAdapter.ReadOriginal(ref("ack-two"),ref("native-two"),"9007199254740998","2026-10-25T02:00:01Z"));
    }
    @Test void exactArchiveRolesAndDecimalReceiveOrdersRoundTripWithoutGrantingAuthority(){
        var actual=data();byte[] encoded=actual.encode();var decoded=GameRestoreNativeAdapter.PairData.decode(encoded);
        assertEquals(actual,decoded);assertArrayEquals(encoded,decoded.encode());
        assertEquals("9007199254740993",decoded.first().receivedOrder());
        var locators=new RestoreCheckpointService.IndependentReadPair(ref("manifest"),decoded.first().acknowledgement(),decoded.first().nativePacket(),decoded.second().acknowledgement(),decoded.second().nativePacket());
        assertEquals(5,locators.references().size());
    }
    @Test void importedArchiveBindsTheActualStageAndItsSeparateOriginalTransfer() {
        var original = data();
        var transfer = ref("transfer-proof");
        var imported = new GameRestoreNativeAdapter.PairData(original.restoreRequestId(), original.lifecycleEvidence(),
                ref("staged-save"), original.first(), original.second(), java.util.Optional.of(transfer));
        var decoded = GameRestoreNativeAdapter.PairData.decode(imported.encode());
        assertEquals(imported, decoded);
        assertEquals(transfer, decoded.importedSaveTransfer().orElseThrow());
        assertNotEquals(original.loadedSave(), decoded.loadedSave());
        byte[] raw = imported.encode();
        var mislabeled = (ObjectNode)StrictJson.parse(raw);
        mislabeled.put("schema", "xar.restore.independent-read-pair/v1");
        assertThrows(IllegalArgumentException.class,
                () -> GameRestoreNativeAdapter.PairData.decode(StrictJson.canonical(mislabeled)));
        var dropped = (ObjectNode)StrictJson.parse(raw);
        dropped.remove("imported_save_transfer");
        assertThrows(IllegalArgumentException.class,
                () -> GameRestoreNativeAdapter.PairData.decode(StrictJson.canonical(dropped)));
    }
    @Test void missingNullExtraAndWrongJsonTypesNeverBecomeReadOriginals(){
        for(String field:List.of("schema","restore_request_id","lifecycle_evidence","loaded_save","first","second")){
            var missing=(ObjectNode)StrictJson.parse(data().encode());missing.remove(field);
            assertThrows(IllegalArgumentException.class,()->GameRestoreNativeAdapter.PairData.decode(StrictJson.canonical(missing)),field);
            var nil=(ObjectNode)StrictJson.parse(data().encode());nil.putNull(field);
            assertThrows(IllegalArgumentException.class,()->GameRestoreNativeAdapter.PairData.decode(StrictJson.canonical(nil)),field);
        }
        var extra=(ObjectNode)StrictJson.parse(data().encode());extra.put("private_issuer",true);
        assertThrows(IllegalArgumentException.class,()->GameRestoreNativeAdapter.PairData.decode(StrictJson.canonical(extra)));
        for(String field:List.of("acknowledgement","native_packet","received_order","received_at_utc")){
            var row=(ObjectNode)StrictJson.parse(data().encode());((ObjectNode)row.get("first")).remove(field);
            assertThrows(IllegalArgumentException.class,()->GameRestoreNativeAdapter.PairData.decode(StrictJson.canonical(row)),field);
        }
        for(String wrong:List.of("true","9007199254740993","1.5","null","\"01\"","\"0\"","\"-1\"")){
            var row=(ObjectNode)StrictJson.parse(data().encode());((ObjectNode)row.get("first")).set("received_order",StrictJson.parse(wrong.getBytes(java.nio.charset.StandardCharsets.UTF_8)));
            assertThrows(IllegalArgumentException.class,()->GameRestoreNativeAdapter.PairData.decode(StrictJson.canonical(row)),wrong);
        }
        var booleanSize=(ObjectNode)StrictJson.parse(data().encode());((ObjectNode)booleanSize.get("first").get("acknowledgement")).put("bytes",true);
        assertThrows(IllegalArgumentException.class,()->GameRestoreNativeAdapter.PairData.decode(StrictJson.canonical(booleanSize)));
    }
    @Test void repeatedAndReversedReadRolesAreRejectedBeforeAnyAuthorityConsumer(){
        var original=data();
        assertThrows(IllegalArgumentException.class,()->new GameRestoreNativeAdapter.PairData(original.restoreRequestId(),original.lifecycleEvidence(),original.loadedSave(),original.first(),original.first()));
        assertThrows(IllegalArgumentException.class,()->new GameRestoreNativeAdapter.PairData(original.restoreRequestId(),original.lifecycleEvidence(),original.loadedSave(),original.second(),original.first()));
        assertThrows(IllegalArgumentException.class,()->new RestoreCheckpointService.IndependentReadPair(ref("manifest"),ref("same-ack"),ref("native-one"),ref("same-ack"),ref("native-two")));
    }
    @Test void committedImportedBasisBindsEveryManifestRoleBeforeReplay()throws Exception {
        var old=data();var imported=new GameRestoreNativeAdapter.PairData(old.restoreRequestId(),old.lifecycleEvidence(),ref("staged-save"),
                old.first(),old.second(),java.util.Optional.of(ref("transfer-proof")));
        var before=owner(42,"departed");var after=owner(43,"successor");
        var basis=new org.xar.ck3.control.application.checkpoint.SavedAttachmentSourceStore.ImportedRecoveryBasis(imported.restoreRequestId(),
                java.time.Instant.parse("2026-10-24T03:00:00Z"),9,"b".repeat(64),before,after,imported.loadedSave(),
                pin(imported.lifecycleEvidence()),pin(imported.importedSaveTransfer().orElseThrow()),pin(ref("pair-manifest")),
                pin(imported.first().acknowledgement()),pin(imported.first().nativePacket()),
                pin(imported.second().acknowledgement()),pin(imported.second().nativePacket()));
        GameRestoreNativeAdapter.requireCommittedPairRoles(imported,basis);
        assertThrows(java.io.IOException.class,()->GameRestoreNativeAdapter.requireCommittedPairRoles(old,basis));
        var crossed=new GameRestoreNativeAdapter.ReadOriginal(imported.first().acknowledgement(),imported.second().nativePacket(),
                imported.first().receivedOrder(),imported.first().receivedAtUtc());
        var other=new GameRestoreNativeAdapter.ReadOriginal(imported.second().acknowledgement(),imported.first().nativePacket(),
                imported.second().receivedOrder(),imported.second().receivedAtUtc());
        var swapped=new GameRestoreNativeAdapter.PairData(imported.restoreRequestId(),imported.lifecycleEvidence(),imported.loadedSave(),
                crossed,other,imported.importedSaveTransfer());
        assertThrows(java.io.IOException.class,()->GameRestoreNativeAdapter.requireCommittedPairRoles(swapped,basis));
    }
    private static org.xar.ck3.control.application.session.SessionPorts.SessionIdentity owner(int pid,String session){
        return new org.xar.ck3.control.application.session.SessionPorts.SessionIdentity("machine",new org.xar.ck3.control.contracts.GameGeneration(pid,
                new org.xar.ck3.control.contracts.PythonOnlyUInt64(java.math.BigInteger.valueOf(pid))),session);
    }
    private static org.xar.ck3.control.continuity.writer.WriterContracts.Pin pin(ExactRef ref){
        return new org.xar.ck3.control.continuity.writer.WriterContracts.Pin(ref,
                new org.xar.ck3.control.continuity.writer.WriterContracts.FileIdentity("1","9007199254740993","3",java.time.Instant.EPOCH.toString(),ref.bytes()));
    }

}
