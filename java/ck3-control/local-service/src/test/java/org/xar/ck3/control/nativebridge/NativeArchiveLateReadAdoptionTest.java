package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.PublicDataJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.continuity.writer.NativeOutcomeArchive;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Sole real coordinator and actual software NativeGameTransport UNKNOWN/poll/adoption producer,
 * actual same-writer archive and cold schema consumers. The shared endpoint helper records the
 * original chronology; no synthetic custody or deadline rewrite. No live Game qualification.
 */
final class NativeArchiveLateReadAdoptionTest {
    @TempDir Path root;
    private static RawJson raw(String value){return new RawJson(value.getBytes(StandardCharsets.UTF_8));}
    private record Context(PlanningReadLateAdoptionWriterTest.Scenario actual,
            PlanningReadResult.Known<RawJson> known) implements AutoCloseable {
        ActionWriterIntegrationFixture fixture(){return actual.fixture;}
        ReadContract<RawJson> contract(){return actual.contract;}
        @Override public void close() throws IOException {actual.close();}
    }
    private Context adopted(String name) throws Exception {
        var actual=PlanningReadLateAdoptionWriterTest.Scenario.open(root.resolve(name),true,Optional.empty());
        try {
            actual.start();var ack=actual.receiveLate();var known=actual.known(actual.adopt(ack));
            assertEquals(actual.originalRequest,known.receipt().request());
            assertTrue(ack.custody().orElseThrow().responseReceived().observedAt().isAfter(actual.originalRequest.deadline()));
            assertEquals(1,actual.fixture.scenarioReadWrites());return new Context(actual,known);
        } catch(Exception|AssertionError failure){actual.close();throw failure;}
    }
    private static ObjectNode row(ActionWriterIntegrationFixture fixture,ExactRef reference) throws Exception {
        return (ObjectNode)StrictJson.parse(fixture.writer.locked(session->fixture.archive.readArtifact(session,reference,StrictJson.EXPLICIT_MAX_BYTES)),StrictJson.EXPLICIT_MAX_BYTES);
    }
    private static ExactRef publish(ActionWriterIntegrationFixture fixture,ObjectNode row) throws Exception {
        return fixture.writer.locked(session->fixture.archive.preserveArtifact(session,StrictJson.canonical(row,StrictJson.EXPLICIT_MAX_BYTES),StrictJson.EXPLICIT_MAX_BYTES));
    }
    private static void refuse(ActionWriterIntegrationFixture fixture,ObjectNode invalid) throws Exception {
        // Preserve wrong numeric categories through fixture publication; the actual archive rejects them.
        byte[] bytes=PublicDataJson.encode(invalid).bytes();assertTrue(bytes.length<=StrictJson.EXPLICIT_MAX_BYTES);
        ExactRef ref=fixture.writer.locked(session->fixture.archive.preserveArtifact(session,bytes,StrictJson.EXPLICIT_MAX_BYTES));
        assertThrows(RuntimeException.class,()->cold(fixture).loadRead(ref));
    }
    private static NativeOutcomeArchive cold(ActionWriterIntegrationFixture fixture) throws Exception {return new NativeOutcomeArchive(fixture.archive.artifactStore(),fixture.writer);}
    @Test void realCoordinatorUnknownAndLateAdoptionColdRoundtripRetainsOriginalTimesAndSourceReuse() throws Exception {
        try(var context=adopted("positive")) {
            var fixture=context.fixture();byte[] ledger=fixture.ledgerBytes();int nativeReads=fixture.nativeReadWrites();
            var receipt=context.known().receipt();var metadata=row(fixture,context.known().originalReceipt());
            assertEquals("xar.planning-read-archive/v2",metadata.path("schema").textValue());assertTrue(metadata.path("adoption").isObject());
            var restored=cold(fixture).loadRead(context.known().originalReceipt());assertEquals(receipt,restored);
            assertEquals(context.known().originalReceipt(),cold(fixture).readReferenceOf(restored));
            assertEquals(receipt.original().custody(),restored.original().custody());assertEquals(receipt.request().deadline(),restored.request().deadline());
            assertEquals(context.known().value(),context.contract().replay(restored));assertTrue(context.actual().poll().isEmpty());
            assertEquals(1,fixture.scenarioReadWrites());assertArrayEquals(ledger,fixture.ledgerBytes());
            assertEquals(nativeReads,fixture.nativeReadWrites());assertEquals(0,fixture.nativeActionWrites());
        }
    }
    @Test void ordinaryV2ExplicitNullAndStrictHistoricalV1KeepTheirOwnCanonicalLocators() throws Exception {
        try(var fixture=new ActionWriterIntegrationFixture(root.resolve("versions"),false)) {
            fixture.ready();var current=fixture.lastNestedRead.get();ExactRef v2=fixture.archive.readReferenceOf(current);ObjectNode original=row(fixture,v2);
            assertTrue(original.has("adoption")&&original.get("adoption").isNull());assertEquals(PlanningReadReceipt.ArchiveVersion.CURRENT_V2,current.archiveVersion());
            var historical=original.deepCopy();historical.put("schema","xar.planning-read-archive/v1");historical.remove("adoption");ExactRef v1=publish(fixture,historical);
            var loaded=cold(fixture).loadRead(v1);assertEquals(PlanningReadReceipt.ArchiveVersion.HISTORICAL_V1,loaded.archiveVersion());assertTrue(loaded.adoption().isEmpty());
            long bytes=fixture.archive.artifactStore().retainedNativeBytes();assertEquals(v1,fixture.archive.preserveRead(loaded));assertEquals(v1,cold(fixture).readReferenceOf(loaded));
            assertEquals(v2,cold(fixture).readReferenceOf(current));assertNotEquals(v1,v2);assertEquals(bytes,fixture.archive.artifactStore().retainedNativeBytes());
            var notArchived=new PlanningReadReceipt(loaded.request(),"not-existing-historical/v1",loaded.requestId(),loaded.before(),loaded.after(),loaded.original(),Optional.empty(),PlanningReadReceipt.ArchiveVersion.HISTORICAL_V1);
            assertThrows(RuntimeException.class,()->fixture.archive.preserveRead(notArchived));assertEquals(bytes,fixture.archive.artifactStore().retainedNativeBytes());
            var extra=historical.deepCopy();extra.putNull("adoption");refuse(fixture,extra);
            var missing=original.deepCopy();missing.remove("adoption");refuse(fixture,missing);
            var scalar=original.deepCopy();scalar.put("adoption",true);refuse(fixture,scalar);
        }
    }
    @Test void adoptionStrictTypesOriginalHeadAndUnknownRoleRefuseWhileSemanticAuthorityStaysInSource() throws Exception {
        try(var context=adopted("strict")) {
            var fixture=context.fixture();ObjectNode original=row(fixture,context.known().originalReceipt());byte[] ledger=fixture.ledgerBytes();
            var missing=original.deepCopy();((ObjectNode)missing.get("adoption")).remove("prepared_request_ref");refuse(fixture,missing);
            for(int kind=0;kind<3;kind++) {
                var changed=original.deepCopy();var adoption=(ObjectNode)changed.get("adoption");
                if(kind==0)adoption.put("original_head_sequence",true);else if(kind==1)adoption.put("original_head_sequence",1.0);else adoption.put("original_head_sequence","0");
                refuse(fixture,changed);
            }
            var wrongHead=original.deepCopy();var adoption=(ObjectNode)wrongHead.get("adoption");String digest=adoption.path("original_head_digest").textValue();
            adoption.put("original_head_digest",(digest.charAt(0)=='0'?"1":"0")+digest.substring(1));refuse(fixture,wrongHead);
            var wrongRole=original.deepCopy();((ObjectNode)wrongRole.get("adoption")).set("original_unknown_ref",original.get("original_ref"));
            refuse(fixture,wrongRole);
            var wrongPrepared=original.deepCopy();((ObjectNode)wrongPrepared.get("adoption")).set("prepared_request_ref",adoption.get("original_unknown_ref"));refuse(fixture,wrongPrepared);
            var wrongArguments=original.deepCopy();ExactRef arguments=fixture.archive.preserveMaterial(raw("{\"unexpected\":true}"));
            ((ObjectNode)wrongArguments.path("adoption").path("current_request")).set("arguments_ref",arguments.toJson());refuse(fixture,wrongArguments);
            var changedSemantics=original.deepCopy();ExactRef changed=fixture.archive.preserveMaterial(raw("{}"));
            ((ObjectNode)changedSemantics.get("adoption")).set("current_semantic_ref",changed.toJson());var dataOnly=cold(fixture).loadRead(publish(fixture,changedSemantics));
            assertThrows(IllegalArgumentException.class,()->context.contract().replay(dataOnly));assertArrayEquals(ledger,fixture.ledgerBytes());assertEquals(0,fixture.nativeActionWrites());
        }
    }
    @Test void changedUnknownOriginalRemainsDamagedAndColdLoadDoesNotRepairOrRedispatch() throws Exception {
        try(var context=adopted("damaged")) {
            var fixture=context.fixture();var metadata=row(fixture,context.known().originalReceipt());var adoption=(ObjectNode)metadata.get("adoption");
            ExactRef unknown=ExactRef.fromJson(adoption.get("original_unknown_ref"));var unknownRow=row(fixture,unknown);
            Path packet=Path.of(ExactRef.fromJson(unknownRow.get("request_packet_ref")).path());byte[] damaged={9,8,7};Files.write(packet,damaged);
            byte[] ledger=fixture.ledgerBytes();assertThrows(RuntimeException.class,()->cold(fixture).loadRead(context.known().originalReceipt()));
            assertArrayEquals(damaged,Files.readAllBytes(packet));assertArrayEquals(ledger,fixture.ledgerBytes());assertEquals(1,fixture.scenarioReadWrites());assertEquals(0,fixture.nativeActionWrites());
        }
        try(var context=adopted("missing-unknown")) {
            var fixture=context.fixture();var metadata=row(fixture,context.known().originalReceipt());
            Path unknown=Path.of(ExactRef.fromJson(metadata.path("adoption").get("original_unknown_ref")).path());Files.delete(unknown);
            byte[] ledger=fixture.ledgerBytes();assertThrows(RuntimeException.class,()->cold(fixture).loadRead(context.known().originalReceipt()));
            assertFalse(Files.exists(unknown));assertArrayEquals(ledger,fixture.ledgerBytes());assertEquals(1,fixture.scenarioReadWrites());assertEquals(0,fixture.nativeActionWrites());
        }
    }
    @Test void completeLargeSemanticDataUsesDriverLaneAndRetainsOnlySmallReadMetadata() throws Exception {
        try(var context=adopted("large-semantic")) {
            var fixture=context.fixture();var original=context.known().receipt();var adopted=original.adoption().orElseThrow();
            // This additional material tests DATA custody only; it is not relabeled as a held SEM.
            var large=adopted.currentSemantic().with("archive_data_payload",new OpportunityJson.Text("x".repeat(1_200_000)));
            assertTrue(DriverJson.encode(large).length>StrictJson.EXPLICIT_MAX_BYTES);
            var data=new PlanningReadAdoption(adopted.currentRequest(),large,adopted.originalUnknown(),adopted.preparedRequest(),
                    adopted.originalHeadSequence(),adopted.originalHeadDigest());
            var receipt=new PlanningReadReceipt(original.request(),original.contractId(),original.requestId(),original.before(),original.after(),original.original(),Optional.of(data));
            byte[] ledger=fixture.ledgerBytes();int reads=fixture.nativeReadWrites();ExactRef ref=fixture.archive.preserveRead(receipt);
            assertTrue(ref.bytes()<StrictJson.EXPLICIT_MAX_BYTES);var restored=cold(fixture).loadRead(ref);
            assertEquals(receipt,restored);assertArrayEquals(DriverJson.encode(large),DriverJson.encode(restored.adoption().orElseThrow().currentSemantic()));
            assertArrayEquals(ledger,fixture.ledgerBytes());assertEquals(reads,fixture.nativeReadWrites());assertEquals(1,fixture.scenarioReadWrites());assertEquals(0,fixture.nativeActionWrites());
        }
    }
}
