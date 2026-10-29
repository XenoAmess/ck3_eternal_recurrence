package org.xar.ck3.control.wave2.runtime.closedadoption;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.channels.FileChannel;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import java.util.Comparator;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FileStatIdentity;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.recovery.RecoveryEvidence;
import org.xar.ck3.control.wave2.runtime.savedproof.WindowsSavedProofIdentityReader;

/** Mechanical cross-process route for the one existing callback; authority stays in the owning Java session. */
final class ClosedInputsFileEndpoint {
    static final int MAX_CALLBACKS = 64;
    private record Small(RecoveryEvidence evidence, FileStatIdentity identity) { }
    private final ClosedInputsSessionAuthority authority;
    private final WindowsFileWriterSession.Settings settings;
    private final String machine, nonce;
    private final Instant deadline;
    private final Path directory;
    private final WindowsJobProcess.ProcessIdentity owner;
    private final RecoveryEvidence descriptor;
    private final Set<String> processed = new HashSet<>();

    private ClosedInputsFileEndpoint(ClosedInputsSessionAuthority authority, WindowsFileWriterSession.Settings settings,
            String nonce, Path root, Instant deadline) throws IOException {
        this.authority = authority; this.settings = settings; this.nonce = nonce; this.deadline = deadline;
        machine = authority.machineId(); owner = WindowsJobProcess.observeLiveProcess(ProcessHandle.current().pid()).identity();
        StrictJson.require(WindowsJobProcess.currentMachineId().equals(machine),"actual current machine owns the retained Java endpoint");
        directory = root.resolve("callbacks"); Files.createDirectory(directory);
        ObjectNode row = StrictJson.object(); row.put("schema","xar.java-closed-partial-session-endpoint/v1");
        row.put("machine_id",machine); row.put("session_nonce",nonce); row.put("deadline_utc",deadline.toString());
        row.put("observed_at_utc",Instant.now().toString());
        row.put("directory",directory.toString()); row.set("owner",identity(owner));
        row.set("basis_ref",authority.basisRef().toJson()); row.set("validation_ref",authority.qualificationRef().toJson());
        row.set("mechanical_source_ref",settings.mechanicalSource().toJson()); row.set("cold_owner_source_ref",settings.coldOwnerSource().toJson());
        row.set("committed_head_ref",authority.committedHeadRef().toJson()); row.put("max_callbacks",MAX_CALLBACKS);
        descriptor = publish(root.resolve("session-endpoint.json"),row);
    }
    static ClosedInputsFileEndpoint create(ClosedInputsSessionAuthority authority, WindowsFileWriterSession.Settings settings,
            String nonce, Path root, Instant deadline) throws IOException {
        return new ClosedInputsFileEndpoint(authority,settings,nonce,root,deadline);
    }
    ExactRef descriptorRef() { return descriptor.reference(); }
    int processedCount() { return processed.size(); }

    /** Called by the original Java owner thread while idle and from active consumer stdout/exit guards. */
    void poll() throws IOException {
        List<Path> requests;
        try (var files = Files.list(directory)) {
            List<Path> entries = files.limit(3L * MAX_CALLBACKS + 1).toList();
            StrictJson.require(entries.size() <= 3 * MAX_CALLBACKS,"finite existing file callback inventory");
            for (Path entry : entries) {
                StrictJson.require(Files.isRegularFile(entry,LinkOption.NOFOLLOW_LINKS) && !Files.isSymbolicLink(entry),"ordinary owned callback files only");
            }
            requests = entries.stream().filter(path -> path.getFileName().toString().matches("[0-9a-f]{32}\\.request\\.json"))
                    .sorted(Comparator.comparing(path -> path.getFileName().toString())).toList();
        }
        for (Path request : requests) {
            String name = request.getFileName().toString();
            if (processed.contains(name)) { continue; }
            StrictJson.require(processed.size() < MAX_CALLBACKS,"finite live Java file callback count");
            process(request); processed.add(name);
        }
    }

    private void process(Path requestPath) throws IOException {
        settings.capacityGuard().run(); requireCurrentOwner();
        Small actual = small(requestPath); ObjectNode request = StrictJson.object(StrictJson.parse(actual.evidence().bytes()),
                Set.of("schema","machine_id","session_nonce","request_nonce","endpoint_ref","requester","transport_source_ref","cold_owner_source_ref","request","observed_at_utc"));
        equal(request,"schema","xar.java-closed-partial-inputs-file-request/v1"); equal(request,"machine_id",machine); equal(request,"session_nonce",nonce);
        StrictJson.utc(StrictJson.text(request.get("observed_at_utc")));
        String requestNonce = StrictJson.text(request.get("request_nonce"));
        StrictJson.require(requestNonce.matches("[0-9a-f]{32}")
                && requestPath.getFileName().toString().equals(requestNonce+".request.json"),"exact unique callback file nonce");
        StrictJson.require(ExactRef.fromJson(request.get("endpoint_ref")).equals(descriptor.reference()),"same actual live endpoint publication");
        var requester = decodeIdentity(request.get("requester"));
        ObjectNode response = StrictJson.object(); response.put("schema","xar.java-closed-partial-inputs-file-response/v1");
        response.put("machine_id",machine); response.put("session_nonce",nonce); response.put("request_nonce",requestNonce);
        response.put("observed_at_utc",Instant.now().toString());
        response.set("endpoint_ref",descriptor.reference().toJson()); response.set("request_ref",actual.evidence().reference().toJson());
        response.set("request_identity",actual.identity().toJson()); response.set("owner",identity(owner)); response.set("requester",identity(requester));
        Path responsePath = directory.resolve(requestNonce+".response.json");
        try {
            requireRequester(requester);
            authority.verifyTransportSource(ExactRef.fromJson(request.get("transport_source_ref")),settings.mechanicalSource());
            authority.verifyTransportSource(ExactRef.fromJson(request.get("cold_owner_source_ref")),settings.coldOwnerSource());
            ObjectNode callback = StrictJson.object(request.get("request"),Set.of("schema","machine_id","basis_ref","validation_ref"));
            equal(callback,"schema","xar.java-closed-partial-cold-inputs-callback/v1"); equal(callback,"machine_id",machine);
            var verified = authority.qualify(ExactRef.fromJson(callback.get("basis_ref")),ExactRef.fromJson(callback.get("validation_ref")));
            requireRequester(requester); requireCurrentOwner();
            StrictJson.require(small(requestPath).equals(actual),"same actual callback bytes and native identity after qualification");
            StrictJson.require(small(Path.of(descriptor.reference().path())).evidence().equals(descriptor),"same retained endpoint exact bytes");
            response.put("status","QUALIFIED"); response.set("wire",StrictJson.parse(verified.wireBytes())); response.putNull("error");
            response.put("observed_at_utc",Instant.now().toString());
            publish(responsePath,response);
        } catch (IOException | RuntimeException error) {
            response.put("status","REJECTED_OR_UNAVAILABLE"); response.putNull("wire");
            String message = error.getClass().getSimpleName()+": "+error.getMessage(); response.put("error",message.substring(0,Math.min(message.length(),2048)));
            try { if (!Files.exists(responsePath,LinkOption.NOFOLLOW_LINKS)) { publish(responsePath,response); } }
            catch (IOException | RuntimeException reporting) { error.addSuppressed(reporting); }
            throw new IOException("live original Java callback rejected; no reconstructed authority",error);
        }
        settings.capacityGuard().run();
    }
    private void requireCurrentOwner() {
        StrictJson.require(Instant.now().isBefore(deadline)
                && WindowsJobProcess.observeLiveProcess(owner.pid()).identity().equals(owner),"same live original Java process within earliest lease");
    }
    private void requireRequester(WindowsJobProcess.ProcessIdentity requester) throws IOException {
        StrictJson.require(WindowsJobProcess.observeLiveProcess(requester.pid()).identity().equals(requester)
                && Files.isSameFile(Path.of(requester.executable()),settings.python()),"actual requesting Python process birth and exact approved interpreter");
    }
    private static WindowsJobProcess.ProcessIdentity decodeIdentity(com.fasterxml.jackson.databind.JsonNode node) {
        ObjectNode row = StrictJson.object(node,Set.of("pid","creation_filetime","executable"));
        return new WindowsJobProcess.ProcessIdentity(StrictJson.integer(row.get("pid"),1,0xffff_ffffL),
                StrictJson.text(row.get("creation_filetime")),StrictJson.text(row.get("executable")));
    }
    private static ObjectNode identity(WindowsJobProcess.ProcessIdentity value) {
        ObjectNode row = StrictJson.object(); row.put("pid",value.pid()); row.put("creation_filetime",value.creationFiletimeDecimal());
        row.put("executable",value.executable()); return row;
    }
    private static Small small(Path path) throws IOException {
        var identities = new WindowsSavedProofIdentityReader(); var before = identities.stat(path);
        StrictJson.require(before.bytes().signum() > 0 && before.bytes().longValueExact() <= RecoveryEvidence.MAX_BYTES,"complete bounded file callback metadata");
        byte[] raw;
        try (var input = Files.newInputStream(path)) { raw = input.readNBytes(RecoveryEvidence.MAX_BYTES+1); }
        StrictJson.require(raw.length == before.bytes().longValueExact() && before.equals(identities.stat(path)),"stable actual file callback identity");
        return new Small(new RecoveryEvidence(new ExactRef(path.toString(),raw.length,RecoveryEvidence.sha256(raw)),raw),before);
    }
    private static RecoveryEvidence publish(Path target, ObjectNode value) throws IOException {
        byte[] raw = ClosedAdoptionJson.encode(value);
        Path temporary = Files.createTempFile(target.getParent(),".java-callback-",".pending");
        try {
            try (var channel = FileChannel.open(temporary,StandardOpenOption.WRITE)) {
                var buffer = java.nio.ByteBuffer.wrap(raw); while (buffer.hasRemaining()) { channel.write(buffer); } channel.force(true);
            }
            // Same-directory move without REPLACE_EXISTING: readers see only the completed unique publication.
            Files.move(temporary,target);
        } catch (IOException | RuntimeException error) {
            try { Files.deleteIfExists(temporary); } catch (IOException cleanup) { error.addSuppressed(cleanup); }
            throw error;
        }
        return new RecoveryEvidence(new ExactRef(target.toString(),raw.length,RecoveryEvidence.sha256(raw)),raw);
    }
    private static void equal(ObjectNode row, String field, String value) { SettledQueryClassifier.equal(row,field,value); }
}
