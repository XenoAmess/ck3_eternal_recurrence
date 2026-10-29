package org.xar.ck3.control.runtime.lifecycle;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.readiness.NativeSourceFileIdentity;
import org.xar.ck3.control.application.readiness.NativeSourceFileIdentity.SourceWitness;
import org.xar.ck3.control.application.readiness.NativeSourceProofCodec;
import org.xar.ck3.control.application.readiness.NativeSourceProofDocument;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Actual sole DATA producers/codecs/consumer comparison. No software record simulates a Managed lease. */
final class PendingSameGameContinuityTest {
    private static final ObjectMapper JSON=new ObjectMapper();
    private static final String SHA="a".repeat(64),MAX="18446744073709551615";
    private static final ExactRef HOST=ref("host"),GAME=ref("game"),SOURCE=ref("source"),EPOCH=ref("epoch"),INPUT=ref("input");

    @Test void freshSessionAndFreshGenerationAllowPublicResetButRetainNativeAndDateOrder() {
        var before=revision("old-session","1",100,200,300);
        PendingSameGameContinuity.requireRevisionContinuation(before,revision("new-session","1",1,201,300));
        PendingSameGameContinuity.requireRevisionContinuation(before,revision("old-session","2",1,201,301));
        assertThrows(IllegalArgumentException.class,()->PendingSameGameContinuity.requireRevisionContinuation(before,revision("old-session","1",99,201,301)));
        assertThrows(IllegalArgumentException.class,()->PendingSameGameContinuity.requireRevisionContinuation(before,revision("new-session","2",1,199,301)));
        assertThrows(IllegalArgumentException.class,()->PendingSameGameContinuity.requireRevisionContinuation(before,revision("new-session","2",1,201,299)));
        PendingSameGameContinuity.requireRevisionContinuation(before,revision("old-session","1",100,200,300));
    }
    private static PendingSameGameContinuity.RevisionFrame revision(String session,String connection,long revision,long nativeRevision,int date) {
        return new PendingSameGameContinuity.RevisionFrame(session,connection,BigInteger.valueOf(revision),BigInteger.valueOf(nativeRevision),date);
    }

    @Test void producerToCodecToSourceConsumerPreservesWideBirthAndBothActualSessions()throws Exception {
        var binding=PendingSameGameContinuity.decode(PendingSameGameContinuity.encode(binding()));
        assertEquals(binding(),binding);assertEquals(MAX,binding.gameCreationFiletimeDecimal());
        assertEquals(MAX,binding.currentConnectionGenerationDecimal());
        assertArrayEquals(PendingSameGameContinuity.encode(binding()),PendingSameGameContinuity.encode(binding));
        var before=NativeSourceProofCodec.decode(NativeSourceProofCodec.encode(source("old-session","2026-10-25T00:00:00Z",identity("17"))));
        var after=NativeSourceProofCodec.decode(NativeSourceProofCodec.encode(source("new-session","2026-10-25T00:00:01Z",identity("17"))));
        PendingSameGameContinuity.requireSourceContinuity(binding,before,after);
        assertThrows(UnsupportedOperationException.class,()->binding.materialReferences().clear());
    }

    @Test void everyFieldIsRequiredAndAuthorityAliasesOrNullAreRejected()throws Exception {
        var valid=json();
        for(var fields=valid.fieldNames();fields.hasNext();) {
            String field=fields.next();var missing=valid.deepCopy();missing.remove(field);reject(missing);
            var nullable=valid.deepCopy();nullable.putNull(field);reject(nullable);
        }
        var extra=json();extra.put("current_authorized",true);reject(extra);
        var old=json();old.put("schema","xar.java.pending-same-game-continuity/v0");reject(old);
    }

    @Test void wideIdentityNeverUsesNumericJsonAndBoundedIntegersRejectBooleanFloatAndUnsafeValues()throws Exception {
        for(String field:List.of("game_creation_filetime_decimal","original_connection_generation_decimal","current_connection_generation_decimal")) {
            var numeric=json();numeric.put(field,9_007_199_254_740_993L);reject(numeric);
            var bool=json();bool.put(field,true);reject(bool);
            for(String invalid:List.of("01","-1","1.0","18446744073709551616")) {var row=json();row.put(field,invalid);reject(row);}
        }
        for(String field:List.of("game_pid","successor_character_id","episode_epoch","driver_version","writer_head_sequence")) {
            var bool=json();bool.put(field,true);reject(bool);
            var fraction=json();fraction.put(field,1.0);reject(fraction);
            var string=json();string.put(field,"1");reject(string);
            var unsafe=json();unsafe.put(field,9_007_199_254_740_992L);reject(unsafe);
        }
    }

    @Test void identicalHashesDoNotAuthorizeChangedFileIdentityAndAllocationRemainsMetadata()throws Exception {
        var binding=binding();var before=roundtrip(source("old-session","2026-10-25T00:00:00Z",identity("17")));
        var replacement=roundtrip(source("new-session","2026-10-25T00:00:01Z",identity("18")));
        assertThrows(IllegalArgumentException.class,()->PendingSameGameContinuity.requireSourceContinuity(binding,before,replacement));
        var original=identity("17");var metadata=new NativeSourceFileIdentity(original.volumeSerialDecimal(),original.fileIdDecimal(),
                original.legacyVolumeSerialDecimal(),original.legacyFileIdHex(),original.creationFiletimeDecimal(),original.lastWriteFiletimeDecimal(),"27",3,8192,2);
        PendingSameGameContinuity.requireSourceContinuity(binding,before,roundtrip(source("new-session","2026-10-25T00:00:01Z",metadata)));
    }

    @Test void oldCurrentSessionTimeAndMissingWitnessRemainDistinctFailures()throws Exception {
        var binding=binding();var before=roundtrip(source("old-session","2026-10-25T00:00:00Z",identity("17")));
        var wrongSession=roundtrip(source("old-session","2026-10-25T00:00:01Z",identity("17")));
        assertThrows(IllegalArgumentException.class,()->PendingSameGameContinuity.requireSourceContinuity(binding,before,wrongSession));
        var regressed=roundtrip(source("new-session","2026-10-24T23:59:59Z",identity("17")));
        assertThrows(IllegalArgumentException.class,()->PendingSameGameContinuity.requireSourceContinuity(binding,before,regressed));
        var old=(ObjectNode)JSON.readTree(NativeSourceProofCodec.encode(before));old.put("schema","xar.java-root-native-source-proof/v2");old.remove("live_witnesses");
        assertThrows(IOException.class,()->NativeSourceProofCodec.decode(JSON.writeValueAsBytes(old)));
        var missing=(ObjectNode)JSON.readTree(NativeSourceProofCodec.encode(before));missing.withArray("live_witnesses").remove(0);
        assertThrows(IOException.class,()->NativeSourceProofCodec.decode(JSON.writeValueAsBytes(missing)));
    }

    @Test void validOtherMachineImageAndEpochAreRejectedByTheActualTypedSourceConsumer()throws Exception {
        var binding=binding();var before=roundtrip(source("old-session","2026-10-25T00:00:00Z",identity("17")));
        var current=source("new-session","2026-10-25T00:00:01Z",identity("17"));
        var machine=new NativeSourceProofDocument("other-machine",current.sessionId(),current.observedAtUtc(),current.mode(),HOST,SOURCE,SHA,EPOCH,GAME,
                current.completeEvidenceClosure(),current.liveWitnesses());
        assertThrows(IllegalArgumentException.class,()->PendingSameGameContinuity.requireSourceContinuity(binding,before,roundtrip(machine)));
        var image=ref("other-game");var otherImage=new NativeSourceProofDocument(current.machineId(),current.sessionId(),current.observedAtUtc(),current.mode(),HOST,SOURCE,SHA,EPOCH,image,
                current.completeEvidenceClosure(),List.of(new SourceWitness(HOST,identity("17")),new SourceWitness(image,identity("17")),new SourceWitness(INPUT,identity("17"))));
        assertThrows(IllegalArgumentException.class,()->PendingSameGameContinuity.requireSourceContinuity(binding,before,roundtrip(otherImage)));
        var epoch=new NativeSourceProofDocument(current.machineId(),current.sessionId(),current.observedAtUtc(),current.mode(),HOST,SOURCE,"b".repeat(64),
                new ExactRef(EPOCH.path(),3,"b".repeat(64)),GAME,current.completeEvidenceClosure(),current.liveWitnesses());
        assertThrows(IllegalArgumentException.class,()->PendingSameGameContinuity.requireSourceContinuity(binding,before,roundtrip(epoch)));
    }

    @Test void duplicateTrailingInvalidUtf8AndOversizedDocumentsReject() {
        String valid=new String(PendingSameGameContinuity.encode(binding()),StandardCharsets.UTF_8);
        assertThrows(IllegalArgumentException.class,()->PendingSameGameContinuity.decode(("{\"schema\":\"duplicate\","+valid.substring(1)).getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class,()->PendingSameGameContinuity.decode((valid+" {}").getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class,()->PendingSameGameContinuity.decode(new byte[]{(byte)0xc3,0x28}));
        assertThrows(IllegalArgumentException.class,()->PendingSameGameContinuity.decode(new byte[PendingSameGameContinuity.MAX_BYTES+1]));
    }
    private static PendingSameGameContinuity.Binding binding() {
        return new PendingSameGameContinuity.Binding("machine",Instant.parse("2026-10-25T00:00:02Z"),17,MAX,GAME,ref("cause"),
                "old-session","18446744073709551614","new-session",MAX,ref("old-source-proof"),ref("new-source-proof"),EPOCH,
                ref("old-native"),ref("new-native"),ref("new-known"),ref("new-observation"),19,"new-run",3,11,SHA,7);
    }
    private static NativeSourceProofDocument source(String session,String observed,NativeSourceFileIdentity identity) {
        return new NativeSourceProofDocument("machine",session,observed,NativeSourceProofDocument.Mode.HTTP,HOST,SOURCE,SHA,EPOCH,GAME,List.of(INPUT),
                List.of(new SourceWitness(HOST,identity),new SourceWitness(GAME,identity),new SourceWitness(INPUT,identity)));
    }
    private static NativeSourceProofDocument roundtrip(NativeSourceProofDocument document)throws IOException {
        return NativeSourceProofCodec.decode(NativeSourceProofCodec.encode(document));
    }
    private static NativeSourceFileIdentity identity(String file) {
        return new NativeSourceFileIdentity(MAX,file,"4294967295","ffffffffffffffff",MAX,"9007199254740993","23",3,4096,1);
    }
    private static ExactRef ref(String name){return new ExactRef("D:/data-test/"+name+".json",3,SHA);}
    private static ObjectNode json()throws IOException{return (ObjectNode)JSON.readTree(PendingSameGameContinuity.encode(binding()));}
    private static void reject(ObjectNode row){assertThrows(IllegalArgumentException.class,()->PendingSameGameContinuity.decode(StrictJson.canonical(row,PendingSameGameContinuity.MAX_BYTES)));}
}
