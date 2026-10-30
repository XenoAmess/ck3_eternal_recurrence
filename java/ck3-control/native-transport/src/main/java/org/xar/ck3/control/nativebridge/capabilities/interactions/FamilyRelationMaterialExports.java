package org.xar.ck3.control.nativebridge.capabilities.interactions;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.ExactRef;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionJson.*;

/** Same-request completed sidecar -> original CAS material -> typed READ attachment. */
public final class FamilyRelationMaterialExports {
    public static final int MAX_BYTES=4*1024*1024;
    private static final List<String> COMPLETE=List.of("path_parsed","job_created","job_reclaimed","job_executed","job_frame_observed","metadata_copied","completion_attempted","sidecar_written");
    private final Path root;
    @FunctionalInterface public interface ArchivePort { ActionPorts.OutcomeArchive current(); }
    private final ArchivePort archives;
    public static final class Captured {
        private final ExactRef reference;
        private final RawJson original;
        private Captured(ExactRef reference,RawJson original) {
            this.reference=Objects.requireNonNull(reference);this.original=Objects.requireNonNull(original);
            byte[] bytes=original.bytes();
            need(bytes.length<=MAX_BYTES&&reference.bytes()==bytes.length&&reference.sha256().equals(DriverJson.sha256(bytes)),"retained sidecar reference/digest/bytes differ");
        }
        public ExactRef reference(){return reference;}
        public RawJson original(){return original;}
    }
    public FamilyRelationMaterialExports(Path actualOwnedQueryExportRoot,ArchivePort sameWriterArchives)throws IOException {
        root=Objects.requireNonNull(actualOwnedQueryExportRoot).toAbsolutePath().normalize();
        archives=Objects.requireNonNull(sameWriterArchives);
    }
    /** The actual contract encoder allocates a fresh output for its coordinator request ID. */
    public String prepare(String actualRequestId) {
        try {
            Path directory=directory(actualRequestId);Files.createDirectory(directory);
            return directory.resolve("guardian-factory-materials.json").toString().replace('\\','/');
        } catch(IOException failure) { throw new UncheckedIOException("actual fresh relation sidecar cannot be allocated",failure); }
    }
    /** Called by the coordinator once after successful original ACK and before the READ is sealed. */
    public Captured capture(PlanningReadReceipt receipt) {
        Objects.requireNonNull(receipt);need(receipt.retainedMaterial().isEmpty(),"relation sidecar capture requires the original unattached READ");
        requireCompletedExport(receipt);
        try {
            Path path=directory(receipt.requestId()).resolve("guardian-factory-materials.json");
            byte[] bytes;
            try(var input=Files.newInputStream(path)) { bytes=input.readNBytes(MAX_BYTES+1); }
            need(bytes.length>0&&bytes.length<=MAX_BYTES,"relation sidecar exceeds its JSON byte bound");
            RawJson original=new RawJson(bytes);requireOwnership(receipt,original);
            ActionPorts.OutcomeArchive archive=Objects.requireNonNull(archives.current());
            ExactRef reference=archive.preserveMaterial(original);
            return new Captured(reference,archive.loadMaterial(reference));
        } catch(IOException failure) { throw new UncheckedIOException("original native relation sidecar is unavailable",failure); }
    }
    /** Pure archival interpretation: only the material ref sealed into this original READ is opened. */
    public Captured archived(PlanningReadReceipt receipt) {
        ExactRef reference=retainedReference(receipt);
        Captured captured=new Captured(reference,Objects.requireNonNull(archives.current()).loadMaterial(reference));
        requireCaptured(receipt,captured);return captured;
    }
    public static void requireCaptured(PlanningReadReceipt receipt,Captured captured) {
        Objects.requireNonNull(captured);need(retainedReference(receipt).equals(captured.reference()),"captured sidecar differs from the material sealed in this READ");
        requireCompletedExport(receipt);requireOwnership(receipt,captured.original());
    }
    public static void requireCompletedExport(PlanningReadReceipt receipt) {
        Objects.requireNonNull(receipt);need(receipt.original().nativeOk()&&receipt.original().requestId().equals(receipt.requestId()),"successful original relation request required");
        requireCompletedExport(receipt.requestId(),receipt.original().originalFrame(),receipt.original().originalResultToken().orElseThrow());
    }
    /** Pure original DATA interpretation; neither an ACK custody nor a READ qualifier. */
    static void requireCompletedExport(String requestId,RawJson originalFrame,RawJson originalResultToken) {
        JsonNode frame=parse(originalFrame);
        eq(frame,"type","command_result");eq(frame,"protocol_version",BigInteger.ONE);eq(frame,"request_id",requestId);yes(frame,"ok");
        need(field(frame,"result").equals(parse(originalResultToken)),"sidecar completion original result token differs");
        JsonNode completion=field(frame,"guardian_factory_discovery_v1");object(completion);eq(completion,"schema_version",BigInteger.ONE);
        COMPLETE.forEach(key->yes(completion,key));nil(completion,"error");
    }
    private static ExactRef retainedReference(PlanningReadReceipt receipt) {
        var material=Objects.requireNonNull(receipt).retainedMaterial().orElseThrow(()->new IllegalArgumentException("original READ has no retained family relation export"));
        need(material.kind()==PlanningReadReceipt.RetainedMaterial.Kind.FAMILY_RELATION_EXPORT,"original READ material is not a family relation export");
        return material.original();
    }
    private static void requireOwnership(PlanningReadReceipt receipt,RawJson original) {
        JsonNode sidecar=parse(original),result=field(parse(receipt.original().originalFrame()),"result");
        eq(sidecar,"request_id",receipt.requestId());eq(sidecar,"native_revision",receipt.request().before().frame().identity().nativeRevision());
        eq(sidecar,"date_raw",receipt.request().before().frame().identity().dateRaw());
        eq(sidecar,"played_character_id",receipt.request().before().frame().identity().player());
        need(field(sidecar,"heir_character_id").equals(field(result,"heir_character_id")),"sidecar heir differs from its original relationship result");
    }
    private Path directory(String actualRequestId) {
        need(actualRequestId!=null&&!actualRequestId.isEmpty(),"actual relation native request ID required");
        return root.resolve("current-relation-"+DriverJson.sha256(actualRequestId.getBytes(StandardCharsets.UTF_8)));
    }
}
