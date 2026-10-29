package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.HeldDriverObservationPort.FullSnapshotExport;
import org.xar.ck3.control.application.driver.HeldDriverObservationPort.HistoryExportMode;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Actual raw Native/Driver manifest producers -> sole full export -> public parser.
 * Source proof reference roles here are explicit software DATA; this class grants no current Root/source authority. */
final class PublicFullSnapshotExportTest {
    private static RawJson raw(String value){return new RawJson(value.getBytes(StandardCharsets.UTF_8));}
    private static ExactRef ref(String name,byte[] bytes){
        return new ExactRef(Path.of(System.getProperty("java.io.tmpdir"),"xar-full-export-data",name).toAbsolutePath().toString(),
                bytes.length,DriverJson.sha256(bytes));
    }
    private static ExactRef proof(String name){return ref(name,name.getBytes(StandardCharsets.UTF_8));}
    private static PublicSnapshotCodec.FullSnapshotOriginals originals(String player){
        String state=DriverObservationAssemblerTest.STATE;
        if(player.equals("missing"))state=state.replace("\"played_character\":{\"character_id\":73,\"alive\":true},","");
        else if(!player.equals("original"))state=state.replace("{\"character_id\":73,\"alive\":true}",player);
        var actual=DriverObservationAssemblerTest.actual(state);var known=DriverStateAssemblerTest.known();
        var driver=new RawJson(known.driver().encode());var driverRef=ref("driver.json",driver.bytes());
        var manifest=DriverObservationEvidenceReader.encode(known,actual,BigInteger.valueOf(9),1,DriverStateAssemblerTest.source(),new OpportunityJson.Obj(java.util.Map.of()),driverRef);
        var manifestRef=ref("facts.json",manifest.bytes());
        var facts=DriverObservationEvidenceReader.decode(manifestRef,manifest,driver,actual);
        var full=new DriverObservationAssembler().projectFull(actual,facts,ref("native.bin",actual.originalPacket()));
        return new PublicSnapshotCodec.FullSnapshotOriginals(full,proof("hello.bin"),proof("heartbeat.bin"),proof("source.json"),manifest,driver);
    }
    @Test void missingNullAndChangedPlayerUseTheSameActualFullProducerWithoutComplete(){
        for(String player:List.of("missing","null","{\"character_id\":74,\"alive\":true}")){
            var originals=originals(player);var full=originals.actual();
            assertInstanceOf(DriverObservationAssembler.Incomplete.class,new DriverObservationAssembler().assemble(full.actual(),full.facts(),full.originalEvidence()));
            var exported=PublicSnapshotCodec.exportFull(originals,true);
            assertSame(originals,exported.originals());assertSame(full,exported.originals().actual());
            var decoded=PublicSnapshotCodec.decode(PublicSnapshotCodec.encode(exported));assertEquals(full.semantic(),decoded);
            assertEquals(player.equals("missing"),!decoded.members().containsKey("played_character"));
            if(player.equals("null"))assertSame(OpportunityJson.Nil.INSTANCE,decoded.get("played_character"));
            if(player.startsWith("{"))assertEquals(BigInteger.valueOf(74),OpportunityJson.integer(OpportunityJson.object(decoded.get("played_character"),"player").get("character_id"),"character_id"));
            assertEquals(2,exported.includedCount());assertArrayEquals(full.actual().originalPacket(),originals.actual().actual().originalPacket());
        }
    }
    @Test void fullHistoryAndOmittedHistoryShareTheOneExistingProjectionAndPreserveOriginal(){
        var originals=originals("null");var full=PublicSnapshotCodec.exportFull(originals,true);var omitted=PublicSnapshotCodec.exportFull(originals,false);
        assertEquals(HistoryExportMode.FULL,full.historyMode());assertEquals(HistoryExportMode.OMITTED,omitted.historyMode());
        assertEquals(2,omitted.totalCount());assertEquals(0,omitted.includedCount());
        assertEquals(2,OpportunityJson.array(originals.actual().semantic().get("native_command_history"),"original history").size());
        assertTrue(OpportunityJson.array(omitted.semantic().get("native_command_history"),"omitted history").isEmpty());
        assertEquals(full.semantic(),PublicSnapshotCodec.decode(PublicSnapshotCodec.encode(full)));
        assertEquals(omitted.semantic(),PublicSnapshotCodec.decode(PublicSnapshotCodec.encode(omitted)));
        var forged=new FullSnapshotExport(originals,full.semantic(),HistoryExportMode.OMITTED,2,0);
        assertThrows(IllegalArgumentException.class,()->PublicSnapshotCodec.encode(forged));
    }
    @Test void fullExportCannotBorrowAnotherNativeManifestDriverOrSemanticBody(){
        var first=originals("null");var second=originals("{\"character_id\":74,\"alive\":true}");
        var wrongManifest=new PublicSnapshotCodec.FullSnapshotOriginals(first.actual(),first.originalHello(),first.originalHeartbeat(),
                first.originalSourceQualification(),second.originalFacts(),first.originalDriver());
        assertThrows(IllegalArgumentException.class,()->PublicSnapshotCodec.exportFull(wrongManifest,true));
        var wrongDriver=new PublicSnapshotCodec.FullSnapshotOriginals(first.actual(),first.originalHello(),first.originalHeartbeat(),
                first.originalSourceQualification(),first.originalFacts(),raw("{}"));
        assertThrows(IllegalArgumentException.class,()->PublicSnapshotCodec.exportFull(wrongDriver,true));
        var actual=first.actual();var changed=new DriverObservationAssembler.FullSnapshot(actual.actual(),actual.facts(),
                actual.semantic().with("played_character",new OpportunityJson.Obj(java.util.Map.of("character_id",new OpportunityJson.IntegerValue(BigInteger.valueOf(73)),"alive",new OpportunityJson.Bool(true)))),
                actual.originalEvidence(),actual.fullBindingSha256());
        var substituted=new PublicSnapshotCodec.FullSnapshotOriginals(changed,first.originalHello(),first.originalHeartbeat(),
                first.originalSourceQualification(),first.originalFacts(),first.originalDriver());
        assertThrows(IllegalArgumentException.class,()->PublicSnapshotCodec.exportFull(substituted,true));
    }
    @Test void missingPhysicalProofAndMalformedPublicRolesRemainUnavailable(){
        var originals=originals("null");var absent=new ExactRef(originals.originalSourceQualification().path(),0,originals.originalSourceQualification().sha256());
        assertThrows(IllegalArgumentException.class,()->new PublicSnapshotCodec.FullSnapshotOriginals(originals.actual(),originals.originalHello(),
                originals.originalHeartbeat(),absent,originals.originalFacts(),originals.originalDriver()));
        var encoded=PublicSnapshotCodec.encode(PublicSnapshotCodec.exportFull(originals,false));
        String body=new String(encoded.bytes(),StandardCharsets.UTF_8);
        assertThrows(IllegalArgumentException.class,()->PublicSnapshotCodec.decode(raw(body.replace("\"revision\":\"9\"","\"revision\":true"))));
        assertEquals(originals.actual().facts().source(),DriverObservationEvidenceReader.decode(originals.actual().facts().semanticFactsEvidence(),
                originals.originalFacts(),originals.originalDriver(),originals.actual().actual()).source());
    }
}
