package org.xar.ck3.control.nativebridge.capabilities.interactions;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.channels.SeekableByteChannel;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.nio.file.attribute.BasicFileAttributes;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.source.IdentityBearingFileAttributes;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionJson.*;

/** Actual bounded sidecar file -> original native hash proof -> sole CAS archive. Replay opens only that CAS original. */
public final class FamilyRelationMaterialExports {
    public static final int MAX_BYTES=4*1024*1024;
    private static final List<String> COMPLETE=List.of("path_parsed","job_created","job_reclaimed","job_executed","job_frame_observed","metadata_copied","completion_attempted","sidecar_written");
    private final Path root;
    private final Object rootFileKey;
    /** Resolve the actual currently borrowed writer session for each live/replay call. */
    @FunctionalInterface public interface ArchivePort { ActionPorts.OutcomeArchive current(); }
    private final ArchivePort archives;
    public static final class Captured{
        private final ExactRef reference;private final RawJson original;
        private Captured(ExactRef reference,RawJson original){this.reference=Objects.requireNonNull(reference);this.original=Objects.requireNonNull(original);byte[] bytes=original.bytes();need(bytes.length<=MAX_BYTES&&reference.bytes()==bytes.length&&reference.sha256().equals(DriverJson.sha256(bytes)),"retained sidecar reference/digest/bytes differ");}
        public ExactRef reference(){return reference;}public RawJson original(){return original;}
    }
    private record Digest(long bytes,String sha256) { }
    public FamilyRelationMaterialExports(Path actualOwnedQueryExportRoot,ArchivePort sameWriterArchives)throws IOException{
        archives=Objects.requireNonNull(sameWriterArchives);root=Objects.requireNonNull(actualOwnedQueryExportRoot).toAbsolutePath().normalize();
        need(root.equals(root.toRealPath()),"query export root must be the actual nonredirected owned directory");BasicFileAttributes attributes=IdentityBearingFileAttributes.read(root);
        need(attributes.isDirectory()&&!attributes.isSymbolicLink()&&attributes.fileKey()!=null,"actual identified owned query export directory required");rootFileKey=attributes.fileKey();
    }
    /** Allocated only by the actual contract encoder using its original coordinator request ID. */
    public String prepare(String actualRequestId){
        try{requireRoot();Path directory=directory(actualRequestId);Files.createDirectory(directory);BasicFileAttributes attributes=IdentityBearingFileAttributes.read(directory);need(attributes.isDirectory()&&!attributes.isSymbolicLink()&&attributes.fileKey()!=null&&directory.equals(directory.toRealPath()),"fresh identified query directory required");Path sidecar=directory.resolve("guardian-factory-materials.json");need(!Files.exists(sidecar,LinkOption.NOFOLLOW_LINKS),"relation query sidecar must be fresh");return sidecar.toString().replace('\\','/');}
        catch(IOException failure){throw new UncheckedIOException("actual fresh relation sidecar cannot be allocated",failure);}
    }
    /** Called once after the actual native ACK; no lookup map can substitute another request's export. */
    public Captured capture(PlanningReadReceipt receipt){
        Digest expected=proof(receipt);ActionPorts.OutcomeArchive archive=Objects.requireNonNull(archives.current());
        try{
            requireRoot();Path directory=directory(receipt.requestId()),path=directory.resolve("guardian-factory-materials.json");need(directory.equals(directory.toRealPath())&&!Files.isSymbolicLink(directory),"actual query directory was redirected");BasicFileAttributes before=IdentityBearingFileAttributes.read(path);
            need(before.isRegularFile()&&!before.isSymbolicLink()&&before.fileKey()!=null&&before.size()==expected.bytes(),"sidecar original file identity/length unavailable");byte[] bytes;
            try(SeekableByteChannel channel=Files.newByteChannel(path,Set.of(StandardOpenOption.READ,LinkOption.NOFOLLOW_LINKS))){
                ByteBuffer buffer=ByteBuffer.allocate(Math.toIntExact(expected.bytes())+1);while(buffer.hasRemaining()){int read=channel.read(buffer);if(read<0)break;need(read!=0,"sidecar channel made no bounded read progress");}need(buffer.position()==expected.bytes(),"sidecar original bytes changed or exceeded native proof");bytes=java.util.Arrays.copyOf(buffer.array(),buffer.position());
            }
            BasicFileAttributes after=IdentityBearingFileAttributes.read(path);need(after.isRegularFile()&&!after.isSymbolicLink()&&before.fileKey().equals(after.fileKey())&&before.size()==after.size()&&before.lastModifiedTime().equals(after.lastModifiedTime()),"sidecar original file changed while being read");requireRoot();
            need(expected.sha256().equals(DriverJson.sha256(bytes)),"sidecar bytes differ from the original native ACK hash");RawJson raw=new RawJson(bytes);object(parse(raw));ExactRef preserved=archive.preserveMaterial(raw);need(preserved.bytes()==expected.bytes()&&preserved.sha256().equals(expected.sha256()),"sole archive changed sidecar original digest/size");ExactRef committed=archive.materialReference(expected.sha256(),expected.bytes());need(committed.equals(preserved),"sidecar original did not reopen through the same archive");return new Captured(committed,archive.loadMaterial(committed));
        }catch(IOException failure){throw new UncheckedIOException("original native relation sidecar is unavailable",failure);}
    }
    /** Explicit archival decoder path: never consults export paths, current frames, filesystem sidecars or Native. */
    public Captured archived(PlanningReadReceipt receipt){Digest expected=proof(receipt);ActionPorts.OutcomeArchive archive=Objects.requireNonNull(archives.current());ExactRef original=archive.materialReference(expected.sha256(),expected.bytes());need(original.bytes()==expected.bytes()&&original.sha256().equals(expected.sha256()),"archived sidecar differs from original native digest");return new Captured(original,archive.loadMaterial(original));}
    public static void requireNativeHashProof(PlanningReadReceipt receipt){proof(receipt);}
    public static void requireCaptured(PlanningReadReceipt receipt,Captured captured){Digest expected=proof(receipt);Objects.requireNonNull(captured);need(captured.reference().bytes()==expected.bytes()&&captured.reference().sha256().equals(expected.sha256()),"captured sidecar differs from this original native ACK");}
    private static Digest proof(PlanningReadReceipt receipt){
        Objects.requireNonNull(receipt);need(receipt.original().nativeOk()&&receipt.original().requestId().equals(receipt.requestId()),"successful original relation request required");JsonNode frame=parse(receipt.original().originalFrame());eq(frame,"type","command_result");eq(frame,"protocol_version",BigInteger.ONE);eq(frame,"request_id",receipt.requestId());yes(frame,"ok");need(field(frame,"result").equals(parse(receipt.original().originalResultToken().orElseThrow())),"sidecar proof original result token differs");JsonNode proof=field(frame,"guardian_factory_discovery_v1");
        closed(proof,"schema_version","path_parsed","job_created","job_reclaimed","job_executed","job_frame_observed","metadata_copied","completion_attempted","sidecar_written","sidecar_hash_schema","sidecar_bytes","sidecar_sha256","error");eq(proof,"schema_version",BigInteger.ONE);eq(proof,"sidecar_hash_schema",BigInteger.ONE);COMPLETE.forEach(key->yes(proof,key));nil(proof,"error");long size=number(proof,"sidecar_bytes",BigInteger.ONE,BigInteger.valueOf(MAX_BYTES)).longValueExact();String sha=text(proof,"sidecar_sha256");need(sha.matches("[0-9a-fA-F]{64}"),"actual sidecar SHA256 required; old bool-only source is unavailable");return new Digest(size,sha.toLowerCase(java.util.Locale.ROOT));
    }
    private Path directory(String actualRequestId){need(actualRequestId!=null&&!actualRequestId.isEmpty(),"actual relation native request ID required");String name=DriverJson.sha256(actualRequestId.getBytes(StandardCharsets.UTF_8));Path path=root.resolve("current-relation-"+name).normalize();need(path.getParent().equals(root)&&path.startsWith(root),"relation export left the actual owned root");return path;}
    private void requireRoot()throws IOException{BasicFileAttributes now=IdentityBearingFileAttributes.read(root);need(now.isDirectory()&&!now.isSymbolicLink()&&rootFileKey.equals(now.fileKey())&&root.equals(root.toRealPath()),"actual query export root identity changed");}
}
