package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.readiness.NativeSourceFileIdentity;
import org.xar.ck3.control.application.readiness.NativeSourceFileIdentity.SourceWitness;
import org.xar.ck3.control.application.readiness.NativeSourceProofCodec;
import org.xar.ck3.control.application.readiness.NativeSourceProofDocument;
import org.xar.ck3.control.contracts.ExactRef;

/** Sole v3 producer codec -> both production continuity profiles. Pure DATA never grants current Game custody. */
final class RootSourceProofContinuityTest {
    private static final ObjectMapper JSON=new ObjectMapper();
    private static final String AT="2026-10-24T19:00:00Z",LATER="2026-10-24T19:01:00Z";
    private static final String SHA="a".repeat(64);
    private static final ExactRef HOST=reference("host.json"),GAME=reference("ck3.exe"),EVIDENCE=reference("native.json");

    @Test void actualV3ProducerCodecFeedsBothContinuityProfilesWithWideIdentities()throws Exception {
        var before=NativeSourceProofCodec.encode(document(AT,identity()));
        var after=NativeSourceProofCodec.encode(document(LATER,identity()));
        assertDoesNotThrow(()->RootSourceProofContinuity.requireSameSourceEpoch(before,after));
        assertDoesNotThrow(()->RootSourceProofContinuity.requireRetainedSourceContinuation(before,after));
        assertArrayEquals(after,NativeSourceProofCodec.encode(NativeSourceProofCodec.decode(after)));
        assertEquals("340282366920938463463374607431768211455",
                NativeSourceProofCodec.decode(after).liveWitnesses().get(0).nativeFile().fileIdDecimal());
    }

    @Test void retainedProfileRejectsRegressedObservationWithoutChangingTheEpochProfile()throws Exception {
        var before=NativeSourceProofCodec.encode(document(LATER,identity()));
        var after=NativeSourceProofCodec.encode(document(AT,identity()));
        assertDoesNotThrow(()->RootSourceProofContinuity.requireSameSourceEpoch(before,after));
        assertThrows(IllegalArgumentException.class,()->RootSourceProofContinuity.requireRetainedSourceContinuation(before,after));
    }

    @Test void nativeFileReplacementRejectsEvenWithTheSameSourcePathSizeAndSha()throws Exception {
        var old=identity();
        var replaced=new NativeSourceFileIdentity(old.volumeSerialDecimal(),"340282366920938463463374607431768211454",
                old.legacyVolumeSerialDecimal(),old.legacyFileIdHex(),old.creationFiletimeDecimal(),
                old.lastWriteFiletimeDecimal(),old.changeFiletimeDecimal(),old.logicalBytes(),old.allocatedBytes(),old.linkCount());
        requireBothRejected(NativeSourceProofCodec.encode(document(AT,old)),NativeSourceProofCodec.encode(document(LATER,replaced)));
    }

    @Test void originalAllocationChangeTimeAndLinkCountRemainDataWithoutReplacingImmutableIdentity()throws Exception {
        var old=identity();
        var changed=new NativeSourceFileIdentity(old.volumeSerialDecimal(),old.fileIdDecimal(),old.legacyVolumeSerialDecimal(),
                old.legacyFileIdHex(),old.creationFiletimeDecimal(),old.lastWriteFiletimeDecimal(),"9007199254740996",
                old.logicalBytes(),8192,1);
        var before=NativeSourceProofCodec.encode(document(AT,old));var after=NativeSourceProofCodec.encode(document(LATER,changed));
        assertDoesNotThrow(()->RootSourceProofContinuity.requireSameSourceEpoch(before,after));
        assertDoesNotThrow(()->RootSourceProofContinuity.requireRetainedSourceContinuation(before,after));
        assertEquals(old,NativeSourceProofCodec.decode(before).liveWitnesses().get(0).nativeFile());
        assertEquals(changed,NativeSourceProofCodec.decode(after).liveWitnesses().get(0).nativeFile());
    }

    @Test void v2MissingAndWronglyTypedWitnessesRejectAtBothRealByteConsumers()throws Exception {
        byte[] valid=NativeSourceProofCodec.encode(document(AT,identity()));
        ObjectNode old=(ObjectNode)JSON.readTree(valid);old.put("schema","xar.java-root-native-source-proof/v2");old.remove("live_witnesses");
        requireBothRejected(valid,JSON.writeValueAsBytes(old));
        ObjectNode missing=(ObjectNode)JSON.readTree(valid);missing.remove("complete_evidence_closure");
        requireBothRejected(valid,JSON.writeValueAsBytes(missing));
        ObjectNode nullable=(ObjectNode)JSON.readTree(valid);nullable.putNull("live_witnesses");
        requireBothRejected(valid,JSON.writeValueAsBytes(nullable));
        ObjectNode wrong=(ObjectNode)JSON.readTree(valid);
        ((ObjectNode)wrong.get("live_witnesses").get(0).get("native_file")).put("file_id_decimal",true);
        requireBothRejected(valid,JSON.writeValueAsBytes(wrong));
    }

    @Test void fullSoftwareOwnerClosureAndAllOriginalWitnessesRemainBound()throws Exception {
        byte[] valid=NativeSourceProofCodec.encode(document(AT,identity()));
        for(String field:List.of("machine_id","session_id")) {
            ObjectNode other=(ObjectNode)JSON.readTree(valid);other.put(field,"other-software-data-owner");
            requireBothRejected(valid,JSON.writeValueAsBytes(other));
        }
        ObjectNode mode=(ObjectNode)JSON.readTree(valid);mode.put("mode","MCP_STDIO");
        requireBothRejected(valid,JSON.writeValueAsBytes(mode));
        var original=document(LATER,identity());
        var reordered=new NativeSourceProofDocument(original.machineId(),original.sessionId(),original.observedAtUtc(),original.mode(),
                original.hostConfiguration(),original.source(),original.ownerSourceEpoch(),original.sourceEpochManifest(),original.gameExecutable(),
                List.of(EVIDENCE,GAME),original.liveWitnesses());
        requireBothRejected(valid,NativeSourceProofCodec.encode(reordered));
        ObjectNode witness=(ObjectNode)JSON.readTree(valid);
        ((ObjectNode)witness.get("live_witnesses").get(2).get("native_file")).put("last_write_filetime_decimal","9007199254740994");
        requireBothRejected(valid,JSON.writeValueAsBytes(witness));
    }

    private static void requireBothRejected(byte[] before,byte[] after) {
        assertThrows(IllegalArgumentException.class,()->RootSourceProofContinuity.requireSameSourceEpoch(before,after));
        assertThrows(IllegalArgumentException.class,()->RootSourceProofContinuity.requireRetainedSourceContinuation(before,after));
    }
    private static NativeSourceProofDocument document(String at,NativeSourceFileIdentity identity) {
        return new NativeSourceProofDocument("pure-source-data-machine","pure-source-data-session",at,
                NativeSourceProofDocument.Mode.HTTP,HOST,reference("source.json"),SHA,reference("epoch.json"),GAME,
                List.of(GAME,EVIDENCE),List.of(new SourceWitness(HOST,identity),new SourceWitness(GAME,identity),new SourceWitness(EVIDENCE,identity)));
    }
    private static NativeSourceFileIdentity identity() {
        return new NativeSourceFileIdentity("18446744073709551615","340282366920938463463374607431768211455",
                "4294967295","ffffffffffffffff","18446744073709551615","9007199254740993","9007199254740995",3,4096,0xffff_ffffL);
    }
    private static ExactRef reference(String file) {return new ExactRef("D:/pure-source-data/"+file,3,SHA);}
}
