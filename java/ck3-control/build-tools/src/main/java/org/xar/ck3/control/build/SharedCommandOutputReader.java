package org.xar.ck3.control.build;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.build.ControlBuild.FileRef;

/** Reads the existing Java child terminal and its original stdout; starts no process. */
public final class SharedCommandOutputReader {
    private SharedCommandOutputReader() { }
    public static final int MAXIMUM_TERMINAL_BYTES=4<<20;
    public record OriginalOutput(FileRef source,byte[] bytes) {
        public OriginalOutput {Objects.requireNonNull(source);bytes=Objects.requireNonNull(bytes).clone();}
        @Override public byte[] bytes(){return bytes.clone();}
    }
    public record Readback(FileRef terminal,SharedOwnedCommand.Status status,boolean childStarted,
            Optional<WindowsJobProcess.CommandResult> child,Optional<OriginalOutput> stdout,
            Optional<FileRef> stderr,Optional<String> failure) {
        public Readback {
            Objects.requireNonNull(terminal);Objects.requireNonNull(status);Objects.requireNonNull(child);
            Objects.requireNonNull(stdout);Objects.requireNonNull(stderr);Objects.requireNonNull(failure);
        }
    }
    public static Readback read(SharedOwnedCommand.Outcome actual,int maximumStdoutBytes)throws IOException {
        Objects.requireNonNull(actual);
        Readback found=read(actual.terminalRef(),maximumStdoutBytes);
        if(found.status()!=actual.status())throw new IOException("command outcome and its original terminal status differ");
        return found;
    }
    public static Readback read(FileRef terminal,int maximumStdoutBytes)throws IOException {
        if(maximumStdoutBytes<1||maximumStdoutBytes>(64<<20))
            throw new IllegalArgumentException("finite stdout read maximum required");
        var mapper=ControlBuild.strictMapper();
        var node=mapper.readTree(original(terminal,MAXIMUM_TERMINAL_BYTES));
        if(!(node instanceof ObjectNode row))throw new IOException("Original Java child terminal object required");
        boolean root=row.path("schema").isTextual() && row.path("schema").textValue().equals("xar.shared-owned-command-terminal/v5");
        if(!root && !row.path("schema").asText().equals("xar.shared-owned-command-terminal/v4"))
            throw new IOException("Original Java child terminal v4 or prepared Root v5 required");
        if(root)validateRootTerminal(row);
        // The original encoder omits these two nullable fields. Reuse its complete record model.
        if(!row.has("java_invocation_evidence_ref"))row.putNull("java_invocation_evidence_ref");
        if(!row.has("auxiliary_cleanup"))row.putNull("auxiliary_cleanup");
        if(!row.has("root_invocation_evidence_ref"))row.putNull("root_invocation_evidence_ref");
        SharedOwnedCommand.Terminal value=mapper.treeToValue(row,SharedOwnedCommand.Terminal.class);
        // Failed and compact terminals preserve diagnostics without conferring package/source custody.
        // The strict evidence reader remains available for an explicit integrity review.
        if(root && value.status()==SharedOwnedCommand.Status.PASS)readRootEvidence(value);
        Optional<OriginalOutput> stdout=value.stdoutRef()==null?Optional.empty():
                Optional.of(new OriginalOutput(value.stdoutRef(),original(value.stdoutRef(),maximumStdoutBytes)));
        return new Readback(terminal,value.status(),value.childStarted(),Optional.ofNullable(value.child()),stdout,
                Optional.ofNullable(value.stderrRef()),Optional.ofNullable(value.failure()));
    }
    private static void fields(com.fasterxml.jackson.databind.JsonNode node,java.util.Set<String> expected)throws IOException {
        if(node==null || !node.isObject() || node.size()!=expected.size())throw new IOException("Exact Root evidence fields required");
        for(var entry:node.properties())if(!expected.contains(entry.getKey()))throw new IOException("Unknown Root evidence field");
    }
    private static void integral(com.fasterxml.jackson.databind.JsonNode node)throws IOException {
        if(node==null || !node.isIntegralNumber() || !node.canConvertToLong())throw new IOException("Exact Root integer required");
    }
    private static void string(com.fasterxml.jackson.databind.JsonNode node)throws IOException {
        if(node==null || !node.isTextual())throw new IOException("Exact Root text required");
    }
    private static void witnesses(com.fasterxml.jackson.databind.JsonNode rows)throws IOException {
        if(rows==null || !rows.isArray() || rows.size()>16384)throw new IOException("Bounded Root source witnesses required");
        for(var row:rows) {
            fields(row,java.util.Set.of("source","native_file"));SharedOwnedCommand.strictFileRef(row.get("source"));
            var nativeFile=row.get("native_file");
            fields(nativeFile,java.util.Set.of("volume_serial_decimal","file_id_decimal","legacy_volume_serial_decimal","legacy_file_id_hex",
                    "creation_filetime_decimal","last_write_filetime_decimal","change_filetime_decimal","logical_bytes","allocated_bytes","link_count"));
            for(String key:java.util.List.of("volume_serial_decimal","file_id_decimal","legacy_volume_serial_decimal","legacy_file_id_hex",
                    "creation_filetime_decimal","last_write_filetime_decimal","change_filetime_decimal"))string(nativeFile.get(key));
            for(String key:java.util.List.of("logical_bytes","allocated_bytes","link_count"))integral(nativeFile.get(key));
        }
    }
    private static void validateRootTerminal(ObjectNode row)throws IOException {
        var keys=new java.util.HashSet<>(java.util.Set.of("schema","machine_id","observed_at_utc","status","owner","slot_id","borrowed_slot_id",
                "request_ref","standing_ref","launcher_source_ref","complete_runtime","outer","child_started","child","diagnostic",
                "input_precheck","input_postcheck","runtime_postcheck","failure","input_before","effective_arguments","stdout_ref","stderr_ref",
                "output_native_bytes_with_directory_guard","game_rpc_calls","actual_driver_or_save_body_reads"));
        if(row.has("java_invocation_evidence_ref"))keys.add("java_invocation_evidence_ref");
        if(row.has("root_invocation_evidence_ref"))keys.add("root_invocation_evidence_ref");
        fields(row,keys);
        for(String key:java.util.List.of("schema","machine_id","observed_at_utc","status","owner","slot_id","input_precheck","input_postcheck","runtime_postcheck"))string(row.get(key));
        for(String key:java.util.List.of("borrowed_slot_id","failure"))if(!row.path(key).isNull())string(row.get(key));
        if(!row.path("child_started").isBoolean())throw new IOException("Exact Root child-start flag required");
        var outer=row.get("outer");fields(outer,java.util.Set.of("pid_decimal","reserved_memory_bytes","hard_job_enforced","scope"));
        string(outer.get("pid_decimal"));string(outer.get("scope"));integral(outer.get("reserved_memory_bytes"));
        if(!outer.path("hard_job_enforced").isBoolean())throw new IOException("Exact outer Job claim required");
        if(!row.path("complete_runtime").isArray())throw new IOException("Exact Root original runtime refs required");
        for(var pin:row.get("complete_runtime"))SharedOwnedCommand.strictFileRef(pin);
        witnesses(row.get("input_before"));
        for(String key:java.util.List.of("stdout_ref","stderr_ref"))if(!row.path(key).isNull())SharedOwnedCommand.strictFileRef(row.get(key));
        for(String key:java.util.List.of("request_ref","standing_ref","launcher_source_ref"))SharedOwnedCommand.strictFileRef(row.get(key));
        if(row.hasNonNull("root_invocation_evidence_ref"))SharedOwnedCommand.strictFileRef(row.get("root_invocation_evidence_ref"));
        else if(row.path("status").textValue().equals("PASS"))throw new IOException("Root PASS requires its original evidence");
        for(String key:java.util.List.of("output_native_bytes_with_directory_guard","game_rpc_calls","actual_driver_or_save_body_reads"))integral(row.get(key));
        if(row.hasNonNull("java_invocation_evidence_ref"))throw new IOException("Prepared Root cannot claim UTF8 engine evidence");
        var child=row.get("child");
        if(child!=null && !child.isNull()) {
            integral(child.get("exit_code"));integral(child.path("identity").get("pid"));
            for(String key:java.util.List.of("peak_job_memory_bytes","active_processes","memory_limit_bytes","limit_flags"))
                integral(child.path("accounting").get(key));
        }
    }
    static void requireExactRootSources(java.util.List<SharedSourceFiles.Witness> actual,java.util.List<FileRef> expected,
            java.util.List<SharedSourceFiles.Witness> originalWitnesses)throws IOException {
        var actualByPath=new java.util.HashMap<String,SharedSourceFiles.Witness>();
        var expectedByPath=new java.util.HashMap<String,FileRef>();
        for(var witness:actual)if(actualByPath.put(witness.source().path(),witness)!=null)throw new IOException("Duplicate retained Root source path");
        for(var reference:expected) {
            var previous=expectedByPath.putIfAbsent(reference.path(),reference);
            if(previous!=null && !previous.equals(reference))throw new IOException("Conflicting original Root source path");
        }
        if(actualByPath.size()!=expectedByPath.size())throw new IOException("Incomplete retained Root source roster");
        for(var reference:expectedByPath.values()) {
            var witness=actualByPath.get(reference.path());
            if(witness==null || !witness.source().equals(reference))throw new IOException("Retained Root source differs from exact original path/content");
        }
        for(var witness:originalWitnesses)if(!witness.equals(actualByPath.get(witness.source().path())))
            throw new IOException("Retained Root native witness differs from actual package original");
    }
    private static java.util.List<FileRef> rootReferences(com.fasterxml.jackson.databind.JsonNode rows)throws IOException {
        if(rows==null || !rows.isArray())throw new IOException("Original Root runtime list required");
        var result=new java.util.ArrayList<FileRef>();for(var row:rows)result.add(SharedOwnedCommand.strictFileRef(row));
        return java.util.List.copyOf(result);
    }
    /** Historical original evidence readback only; it never grants a new Root execution capability. */
    static SharedOwnedCommand.RootInvocationEvidence readRootEvidence(SharedOwnedCommand.Terminal terminal)throws IOException {
        FileRef reference=terminal.rootInvocationEvidenceRef();
        if(reference==null)throw new IOException("Prepared Root terminal has no original evidence");
        var mapper=ControlBuild.strictMapper();var wire=mapper.readTree(original(reference,MAXIMUM_TERMINAL_BYTES));
        fields(wire,java.util.Set.of("schema","root_invocation_ref","prepared_root","authorization","managed_command","retained_package_sources",
                "retained_outer_sources","package_precheck","package_postcheck","outer_precheck","outer_postcheck"));
        string(wire.get("schema"));SharedOwnedCommand.strictFileRef(wire.get("root_invocation_ref"));
        var prepared=SharedOwnedCommand.decodePreparedRoot(wire.get("prepared_root"));
        var authority=SourceGraphCommandSpecProducer.decodeRootAuthorization(wire.get("authorization"));
        witnesses(wire.get("retained_package_sources"));witnesses(wire.get("retained_outer_sources"));
        for(String key:java.util.List.of("package_precheck","package_postcheck","outer_precheck","outer_postcheck"))string(wire.get(key));
        var command=wire.get("managed_command");
        if(command!=null && !command.isNull()) {
            fields(command,java.util.Set.of("executable","arguments","cwd","environment","stdout","stderr","memory_limit_bytes"));
            for(String key:java.util.List.of("executable","cwd","stdout","stderr"))string(command.get(key));
            integral(command.get("memory_limit_bytes"));
            if(!command.path("arguments").isArray() || !command.path("environment").isObject())throw new IOException("Typed Root argv/environment required");
            for(var argument:command.get("arguments"))string(argument);
            for(var entry:command.get("environment").properties())string(entry.getValue());
        }
        var evidence=mapper.treeToValue(wire,SharedOwnedCommand.RootInvocationEvidence.class);
        var request=SharedOwnedCommand.parseRequest(mapper.readTree(original(terminal.requestRef(),1<<20)));
        var invocation=SourceGraphCommandSpecProducer.decodeRootInvocation(mapper.readTree(original(evidence.rootInvocationRef(),65536)));
        var originalAuthority=SourceGraphCommandSpecProducer.decodeRootAuthorization(mapper.readTree(original(prepared.rootRuntimeAuthorizationRef(),1<<20)));
        if(request.preparedRoot()==null || !request.preparedRoot().equals(prepared) || !invocation.preparedRoot().equals(prepared)
                || !invocation.specRef().equals(terminal.requestRef()) || !authority.equals(originalAuthority)
                || !authority.packageManifest().equals(prepared.packageManifest()) || !authority.finiteInvocation().equals(prepared.invocation())
                || !terminal.machineId().equals(request.machineId()) || !terminal.machineId().equals(invocation.machineId())
                || !terminal.machineId().equals(authority.machineId()) || !terminal.owner().equals(request.owner())
                || !terminal.owner().equals(authority.owner()) || !terminal.standingRef().equals(request.standingRef())
                || !terminal.standingRef().equals(authority.standingRef()))
            throw new IOException("Root terminal/evidence/original input binding differs");
        if(!terminal.slotId().equals(request.slotId()) || !java.util.Objects.equals(terminal.borrowedSlotId(),request.borrowedSlotId())
                || !terminal.launcherSourceRef().equals(request.launcherSourceRef()))
            throw new IOException("Root terminal slot/launcher context differs from exact request");
        var binding=SharedOwnedCommandBinding.read(invocation.bindingRef());
        var standing=mapper.readTree(original(binding.standingRef(),1<<20));var delivery=mapper.readTree(original(binding.deliveryRef(),1<<20));
        SharedOwnedCommandBinding.verifyAuthority(standing,binding.standingExpectation(),terminal.machineId());
        SharedOwnedCommandBinding.verifyAuthority(delivery,binding.deliveryExpectation(),terminal.machineId());
        var base=rootReferences(standing.get("runtime_closure"));var delivered=rootReferences(delivery.get("complete_runtime"));
        var sorted=new java.util.ArrayList<>(base);sorted.sort(java.util.Comparator.comparing(FileRef::path));
        if(base.size()!=6 || !base.equals(delivered) || !sorted.equals(terminal.completeRuntime())
                || authority.outerClasspath().roots().size()<6 || !authority.outerClasspath().roots().subList(0,6).equals(base)
                || !binding.machineId().equals(terminal.machineId()) || !binding.standingRef().equals(terminal.standingRef())
                || !binding.deliveryRef().equals(authority.deliveryRef()) || !binding.launcherSourceRef().equals(terminal.launcherSourceRef()))
            throw new IOException("Historical Root binding/standing/delivery original runtime differs");
        var expectedInputs=new java.util.ArrayList<FileRef>(request.inputs());expectedInputs.add(request.executable());expectedInputs.add(invocation.bindingRef());
        if(terminal.inputPrecheck()==SharedOwnedCommand.Check.MATCH)requireExactRootSources(terminal.inputBefore(),expectedInputs,java.util.List.of());
        prepared.packageManifest().verify();prepared.invocation().verify();
        if(evidence.outerPrecheck()==SharedOwnedCommand.Check.MATCH) {
            var expectedOuter=new java.util.ArrayList<FileRef>(authority.outerClasspath().effective());
            expectedOuter.add(evidence.rootInvocationRef());expectedOuter.add(prepared.rootRuntimeAuthorizationRef());
            requireExactRootSources(evidence.retainedOuterSources(),expectedOuter,java.util.List.of());
        }
        if(evidence.packagePrecheck()==SharedOwnedCommand.Check.MATCH) {
            var manifest=org.xar.ck3.control.build.runtime.JavaRuntimePackageCodec.decodeManifest(original(prepared.packageManifest(),
                    org.xar.ck3.control.build.runtime.JavaRuntimePackageModel.MAX_METADATA_BYTES));
            var originals=new java.util.ArrayList<SharedSourceFiles.Witness>(manifest.originalInputs());
            for(var output:manifest.outputFiles())originals.add(output.actual());
            var expectedPackage=new java.util.ArrayList<FileRef>();for(var source:originals)expectedPackage.add(source.source());
            expectedPackage.add(prepared.packageManifest());expectedPackage.add(prepared.invocation());
            var finite=org.xar.ck3.control.build.runtime.JavaRuntimeLaunch.FiniteFirstLiveInvocation.decode(original(prepared.invocation(),65536));
            expectedPackage.add(finite.finiteRequest());
            requireExactRootSources(evidence.retainedPackageSources(),expectedPackage,originals);
            if(!manifest.machineId().equals(terminal.machineId()))throw new IOException("Original Root package machine differs");
        }
        for(var source:evidence.retainedPackageSources())SharedSourceFiles.assertUnchanged(source);
        for(var source:evidence.retainedOuterSources())SharedSourceFiles.assertUnchanged(source);
        if(!SourceGraphCommandSpecProducer.rootEffectiveClasspath(authority.outerClasspath().roots()).equals(authority.outerClasspath().effective()))
            throw new IOException("Original Root effective classpath differs");
        var effective=new java.util.HashSet<>(authority.outerClasspath().effective());
        var expected=new java.util.HashSet<>(terminal.completeRuntime());expected.addAll(authority.completeExtraRuntime());
        if(terminal.completeRuntime().size()!=6 || authority.outerClasspath().roots().size()<6
                || !new java.util.HashSet<>(authority.outerClasspath().roots().subList(0,6)).equals(new java.util.HashSet<>(terminal.completeRuntime()))
                || !effective.equals(expected))throw new IOException("Root evidence lost original six-piece or extra runtime");
        if(terminal.status()==SharedOwnedCommand.Status.PASS) {
            if(!terminal.childStarted() || terminal.child()==null || !terminal.child().passed()
                    || terminal.inputPrecheck()!=SharedOwnedCommand.Check.MATCH || terminal.inputPostcheck()!=SharedOwnedCommand.Check.MATCH
                    || terminal.runtimePostcheck()!=SharedOwnedCommand.Check.MATCH || terminal.failure()!=null
                    || evidence.packagePrecheck()!=SharedOwnedCommand.Check.MATCH || evidence.packagePostcheck()!=SharedOwnedCommand.Check.MATCH
                    || evidence.outerPrecheck()!=SharedOwnedCommand.Check.MATCH || evidence.outerPostcheck()!=SharedOwnedCommand.Check.MATCH
                    || evidence.managedCommand()==null || evidence.retainedPackageSources().isEmpty() || evidence.retainedOuterSources().isEmpty())
                throw new IOException("Root PASS lacks complete actual child/package/runtime outcome");
            var actual=evidence.managedCommand();
            if(!actual.arguments().equals(terminal.effectiveArguments()) || !actual.executable().equals(Path.of(request.executable().path()))
                    || !actual.cwd().equals(request.cwd()) || actual.memoryLimitBytes()!=request.memoryLimitBytes()
                    || !Path.of(terminal.child().identity().executable()).equals(actual.executable())
                    || terminal.child().accounting().memoryLimitBytes()!=actual.memoryLimitBytes()
                    || terminal.stdoutRef()==null || terminal.stderrRef()==null
                    || !Path.of(terminal.stdoutRef().path()).equals(actual.stdout()) || !Path.of(terminal.stderrRef().path()).equals(actual.stderr()))
                throw new IOException("Root actual managed command and child/log terminal differ");
        }
        reference.verify();return evidence;
    }
    private static byte[] original(FileRef source,int maximum)throws IOException {
        Objects.requireNonNull(source);
        if(source.bytes()<0||source.bytes()>maximum)throw new IOException("original command output exceeds read maximum");
        source.verify();byte[] bytes;
        try(var stream=Files.newInputStream(Path.of(source.path()))){bytes=stream.readNBytes(maximum+1);}
        if(bytes.length!=source.bytes()||bytes.length>maximum)throw new IOException("original command output size differs");
        try {
            String sha=java.util.HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(bytes));
            if(!sha.equals(source.sha256()))throw new IOException("original command output bytes differ");
        }catch(java.security.NoSuchAlgorithmException unavailable){throw new IOException("SHA-256 unavailable",unavailable);}
        return bytes;
    }
}
