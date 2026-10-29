import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.CompleteSourceGraph;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.build.BoundedSourceInputGuard;

/** Exact issuer-scoped immutable Java tool/host source successor with a typed current task owner; source copying grants no runtime authority. */
public final class IntegratedToolsSuccessor16 {
    private IntegratedToolsSuccessor16() { }
    /** Exact current task identity supplied by the independent issuer scope, not a legacy role alias. */
    public record TaskOwner(String taskPath) {
        public TaskOwner {
            if (taskPath == null || !taskPath.matches("/root(?:/[a-z0-9_]+)+")) {
                throw new IllegalArgumentException("Canonical non-root task owner required");
            }
        }
    }
    public record Overlay(IntegratedToolsGraph01.Group group, String targetRelative,
            ControlBuild.FileRef materializedPreimageRef, ControlBuild.FileRef sourceRef,
            ControlBuild.FileRef correctionMapRef, String reason) { }
    public record Addition(IntegratedToolsGraph01.Group group, String targetRelative,
            ControlBuild.FileRef sourceRef, ControlBuild.FileRef correctionMapRef, String reason) { }
    public record Retirements(String schema, String machineId, String owner,
            List<CompleteSourceGraph.Relocation> relocations, List<CompleteSourceGraph.SelectedFile> selectedFiles) {
        public Retirements {
            relocations=List.copyOf(relocations); selectedFiles=List.copyOf(selectedFiles); new TaskOwner(owner);
            if (!"xar.source08.explicit-test-relocations/v1".equals(schema) || machineId==null
                    || relocations.isEmpty() || relocations.size()>16 || selectedFiles.size()!=relocations.size())
                throw new IllegalArgumentException("Explicit bounded external test retirement authority required");
            var expected=new HashSet<CompleteSourceGraph.SelectedFile>();
            for(var move:relocations) {
                if(!move.oldTargetRelative().startsWith("build-tools/src/test/java/")
                        || move.newTargetRelative().startsWith("build-tools/")
                        || !move.newTargetRelative().contains("/src/test/java/")
                        || !move.finalOwnerTargetRelative().equals(move.newTargetRelative())
                        || !expected.add(new CompleteSourceGraph.SelectedFile(move.newTargetRelative(),move.finalSourceRef())))
                    throw new IllegalArgumentException("Only explicit unique test transfers outside Tools may retire a target");
            }
            if(!expected.equals(new HashSet<>(selectedFiles))) throw new IllegalArgumentException("Complete external final winners required");
        }
    }
    public record SourceRoster(int tools, int host) {
        public SourceRoster {
            if (tools < 1 || host < 1 || tools > 512 || host > 512 || tools > 512 - host)
                throw new IllegalArgumentException("Bounded exact issuer-scoped source roster required");
        }
        public int total() { return Math.addExact(tools, host); }
    }
    public record Request(String schema, String machineId, TaskOwner taskOwner, String reviewAtUtc,
            ControlBuild.FileRef sourceAuthorityRef, ControlBuild.FileRef scopeClarificationRef,
            ControlBuild.FileRef qualificationEvidenceRef, ControlBuild.FileRef baseMapRef, ControlBuild.FileRef inputManifestRef,
            String outputRoot, long conservativeNewRootCapBytes, SourceRoster baseRoster, SourceRoster finalRoster, List<Overlay> overlays, List<Addition> additions,
            @com.fasterxml.jackson.annotation.JsonInclude(com.fasterxml.jackson.annotation.JsonInclude.Include.NON_NULL) ControlBuild.FileRef finalSelectionRef,
            @com.fasterxml.jackson.annotation.JsonInclude(com.fasterxml.jackson.annotation.JsonInclude.Include.NON_NULL) ControlBuild.FileRef retirementAuthorityRef) {
        public Request {
            if (!Set.of("xar.integrated-tools-firstcut-successor/v5", "xar.integrated-tools-firstcut-successor/v6", "xar.integrated-tools-firstcut-successor/v7", "xar.integrated-tools-firstcut-successor/v8", "xar.integrated-tools-firstcut-successor/v9").contains(schema)
                    || machineId == null || taskOwner == null || sourceAuthorityRef == null || scopeClarificationRef == null
                    || qualificationEvidenceRef == null || baseMapRef == null || inputManifestRef == null || baseRoster == null || finalRoster == null || overlays == null || overlays.isEmpty() || overlays.size() > 80 || additions == null || additions.size() > (expanded(schema) ? 64 : 32)
                    || conservativeNewRootCapBytes <= 0 || conservativeNewRootCapBytes > ((expanded(schema) ? 12L : 8L) << 20)
                    || outputRoot == null || !Path.of(outputRoot).isAbsolute() || !Path.of(outputRoot).normalize().equals(Path.of(outputRoot))) {
                throw new IllegalArgumentException("Exact Root-assigned measured firstcut successor required");
            }
            if (schema.equals("xar.integrated-tools-firstcut-successor/v5")
                    && (baseRoster.total() > 256 || finalRoster.total() > 256))
                throw new IllegalArgumentException("Historical v5 retains its original 256-file boundary");
            if ((schema.equals("xar.integrated-tools-firstcut-successor/v7") || expanded(schema)) != (finalSelectionRef != null))
                throw new IllegalArgumentException("Current v7/v8 requires complete final selection; historical wires cannot carry it");
            if (schema.equals("xar.integrated-tools-firstcut-successor/v9") != (retirementAuthorityRef!=null))
                throw new IllegalArgumentException("Only v9 requires a pinned retirement authority; older wires remain unchanged");
            overlays = List.copyOf(overlays); additions = List.copyOf(additions);
            Set<String> unique = new HashSet<>();
            for (Overlay row : overlays) {
                if (row.group() == null || row.sourceRef() == null || row.materializedPreimageRef() == null
                        || row.correctionMapRef() == null || row.reason() == null || row.reason().isBlank()
                        || !unique.add(row.group().name() + ":" + row.targetRelative())) {
                    throw new IllegalArgumentException("Distinct fully pinned measured repairs required");
                }
            }
            for (Addition row : additions) {
                if (row.group() == null || row.sourceRef() == null || row.correctionMapRef() == null
                        || row.reason() == null || row.reason().isBlank()
                        || !unique.add(row.group().name() + ":" + row.targetRelative())) {
                    throw new IllegalArgumentException("Distinct fully pinned additions required");
                }
            }
            Instant.parse(reviewAtUtc);
        }
        public Request(String schema, String machineId, TaskOwner taskOwner, String reviewAtUtc,
                ControlBuild.FileRef sourceAuthorityRef, ControlBuild.FileRef scopeClarificationRef,
                ControlBuild.FileRef qualificationEvidenceRef, ControlBuild.FileRef baseMapRef, ControlBuild.FileRef inputManifestRef,
                String outputRoot, long cap, SourceRoster baseRoster, SourceRoster finalRoster,
                List<Overlay> overlays, List<Addition> additions, ControlBuild.FileRef finalSelectionRef) {
            this(schema,machineId,taskOwner,reviewAtUtc,sourceAuthorityRef,scopeClarificationRef,qualificationEvidenceRef,
                    baseMapRef,inputManifestRef,outputRoot,cap,baseRoster,finalRoster,overlays,additions,finalSelectionRef,null);
        }
        public Request(String schema, String machineId, TaskOwner taskOwner, String reviewAtUtc,
                ControlBuild.FileRef sourceAuthorityRef, ControlBuild.FileRef scopeClarificationRef,
                ControlBuild.FileRef qualificationEvidenceRef, ControlBuild.FileRef baseMapRef, ControlBuild.FileRef inputManifestRef,
                String outputRoot, long conservativeNewRootCapBytes, SourceRoster baseRoster, SourceRoster finalRoster,
                List<Overlay> overlays, List<Addition> additions) {
            this(schema, machineId, taskOwner, reviewAtUtc, sourceAuthorityRef, scopeClarificationRef,
                    qualificationEvidenceRef, baseMapRef, inputManifestRef, outputRoot, conservativeNewRootCapBytes,
                    baseRoster, finalRoster, overlays, additions, null);
        }
    }
    /** Explicit historical codec; current v7 never admits missing or null finalSelectionRef. */
    public static Request decodeRequest(byte[] bytes) throws IOException {
        if (bytes.length > (1 << 20)) throw new IOException("Finite source request wire required");
        var wire = ControlBuild.strictMapper().readTree(bytes);
        if (wire == null || !wire.isObject() || !wire.path("schema").isTextual()) throw new IOException("Versioned source request required");
        String schema = wire.path("schema").textValue();
        if(!schema.equals("xar.integrated-tools-firstcut-successor/v9")) {
            if(wire.has("retirement_authority_ref")) throw new IOException("Historical wire cannot carry retirement authority");
            ((com.fasterxml.jackson.databind.node.ObjectNode)wire).putNull("retirement_authority_ref");
        }
        if (schema.equals("xar.integrated-tools-firstcut-successor/v5") || schema.equals("xar.integrated-tools-firstcut-successor/v6")) {
            if (wire.has("final_selection_ref")) throw new IOException("Historical request cannot carry current selection field");
            ((com.fasterxml.jackson.databind.node.ObjectNode) wire).putNull("final_selection_ref");
        }
        return ControlBuild.strictMapper().treeToValue(wire, Request.class);
    }
    public record SelectedFile(IntegratedToolsGraph01.Group group, String targetRelative, ControlBuild.FileRef sourceRef) {
        public SelectedFile {
            if (group == null || sourceRef == null || targetRelative == null || targetRelative.isBlank()
                    || targetRelative.indexOf((char)92) >= 0 || Path.of(targetRelative).isAbsolute()
                    || !Path.of(targetRelative).normalize().equals(Path.of(targetRelative))
                    || (group == IntegratedToolsGraph01.Group.TOOLS && !targetRelative.startsWith("build-tools/")))
                throw new IllegalArgumentException("Canonical complete selected source row required");
        }
        String key() { return group.name() + ":" + (group == IntegratedToolsGraph01.Group.TOOLS ? targetRelative.substring("build-tools/".length()) : targetRelative); }
    }
    public record SelectionCounts(int total, int tools, int hostSourceOnly, int toolsMainJava) {
        public SelectionCounts { if (new SourceRoster(tools, hostSourceOnly).total() != total || toolsMainJava < 1 || toolsMainJava > tools) throw new IllegalArgumentException("Exact selected counts required"); }
    }
    public record ComponentAdoption(ControlBuild.FileRef componentRef, int newTargets, int overrides) {
        public ComponentAdoption { if (componentRef == null || newTargets < 0 || overrides < 0) throw new IllegalArgumentException("Typed component provenance required"); }
    }
    /** Closed v2 selection wire. Its prose and accounting annotations grant no execution authority. */
    public record EffectiveSelection(String schema, String machineId, String owner, String observedAtUtc, String status,
            ControlBuild.FileRef baseMapRef, List<SelectedFile> selectedFiles, List<ComponentAdoption> componentAdoptions,
            SelectionCounts counts, long logicalBytes, long bodyPageChargeWithDirectories, int directories,
            String newSourceRoot, String hostBoundary, String runtimeBoundary, String excluded,
            ControlBuild.FileRef previousFrozenSelectionRef, ControlBuild.FileRef currentCompilerProviderJoinRef,
            String criticalSoftware, ControlBuild.FileRef actualBootstrapFailureRef, String minimumDelta) {
        public EffectiveSelection {
            if (!"xar.java-source-effective-selection/v2".equals(schema) || !"FROZEN_COMPLETE_WINNERS_SOURCE_ONLY".equals(status)
                    || machineId == null || machineId.isBlank() || owner == null || baseMapRef == null || counts == null
                    || selectedFiles == null || componentAdoptions == null || logicalBytes < 0 || bodyPageChargeWithDirectories < 0
                    || directories < 1 || newSourceRoot == null || !Path.of(newSourceRoot).isAbsolute()
                    || hostBoundary == null || runtimeBoundary == null || excluded == null || previousFrozenSelectionRef == null
                    || currentCompilerProviderJoinRef == null || criticalSoftware == null || actualBootstrapFailureRef == null || minimumDelta == null)
                throw new IllegalArgumentException("Complete exact v2 final source selection required");
            new TaskOwner(owner); Instant.parse(observedAtUtc); selectedFiles = List.copyOf(selectedFiles); componentAdoptions = List.copyOf(componentAdoptions);
            var keys = new HashSet<String>(); long actual = 0; int tools = 0;
            for (var row : selectedFiles) { if (!keys.add(row.key())) throw new IllegalArgumentException("Duplicate final source target"); actual = Math.addExact(actual, row.sourceRef().bytes()); if (row.group() == IntegratedToolsGraph01.Group.TOOLS) tools++; }
            if (selectedFiles.size() != counts.total() || tools != counts.tools() || actual != logicalBytes)
                throw new IllegalArgumentException("Complete final source count and bytes must match its rows");
        }
    }
    static void requireExactSelection(Request request, List<IntegratedToolsGraph01.Selection> resolved) throws IOException {
        if (request.finalSelectionRef() == null) throw new IOException("Explicit complete finalSelectionRef required before source copy");
        EffectiveSelection expected = ControlBuild.strictMapper().readValue(readExact(request.finalSelectionRef()), EffectiveSelection.class);
        if (!expected.machineId().equals(request.machineId()) || !expected.owner().equals(request.taskOwner().taskPath())
                || !sameSource(expected.baseMapRef(), request.baseMapRef()) || !Path.of(expected.newSourceRoot()).equals(Path.of(request.outputRoot()))
                || expected.counts().tools() != request.finalRoster().tools() || expected.counts().hostSourceOnly() != request.finalRoster().host())
            throw new IOException("Final selection must bind machine, owner, base, destination and full roster");
        Map<String, ControlBuild.FileRef> wanted = new HashMap<>();
        for (var row : expected.selectedFiles()) wanted.put(row.key(), row.sourceRef());
        if (resolved.size() != wanted.size()) throw new IOException("Resolved sources differ from complete final selection");
        Set<String> seen = new HashSet<>();
        for (var row : resolved) {
            String key = row.group().name() + ":" + row.targetRelative(); var pin = wanted.get(key);
            if (!seen.add(key) || pin == null || !sameSource(pin, row.materializedRef()))
                throw new IOException("Resolved final winner differs before CREATE_NEW: " + key);
        }
        if (!seen.equals(wanted.keySet())) throw new IOException("Resolved target set differs from complete selected target set");
    }
    private static boolean sameSource(ControlBuild.FileRef left, ControlBuild.FileRef right) {
        return Path.of(left.path()).normalize().equals(Path.of(right.path()).normalize()) && left.bytes() == right.bytes() && left.sha256().equals(right.sha256());
    }
    public static void main(String[] args) throws Exception {
        if(args.length==4 && args[0].equals("--project-existing")) {
            projectExisting(new ControlBuild.FileRef(args[1],Long.parseLong(args[2]),args[3]));return;
        }
        if (args.length != 1) throw new IllegalArgumentException("exact-successor-request required");
        Path requestPath = Path.of(args[0]); ControlBuild.FileRef requestRef = ControlBuild.FileRef.measure(requestPath);
        Request request = decodeRequest(readExact(requestRef));
        if (!request.schema().equals("xar.integrated-tools-firstcut-successor/v7") && !expanded(request.schema()))
            throw new IOException("Historical " + (request.schema().endsWith("/v5") ? "v5" : "v6") + " source requests are readable but cannot authorize new materialization");
        if (!request.machineId().equals(WindowsJobProcess.currentMachineId())
                || !Instant.now().isBefore(Instant.parse(request.reviewAtUtc()))) throw new IOException("Current same-machine source request required");
        verifyRequest(requestRef, request);
        IntegratedToolsGraph01.Actual base = ControlBuild.strictMapper().readValue(
                readExact(request.baseMapRef()), IntegratedToolsGraph01.Actual.class);
        if (!base.schema().equals("xar.integrated-host-tools-source-map/v1") || !base.machineId().equals(request.machineId())
                || base.sources().size() != request.baseRoster().total() || base.toolsSources() != request.baseRoster().tools() || base.hostOverlaySources() != request.baseRoster().host()) {
            throw new IOException("Exact immutable base source roster required");
        }
        List<CompleteSourceGraph.Relocation> retired=retirements(request);
        List<ControlBuild.FileRef> completeInputs = new ArrayList<>();
        if(request.retirementAuthorityRef()!=null) completeInputs.add(request.retirementAuthorityRef());
        for(var move:retired) completeInputs.addAll(List.of(move.sourceRef(),move.selectionRef(),move.finalSourceRef(),move.finalSelectionRef()));
        completeInputs.add(request.finalSelectionRef());
        for (var row : base.sources()) { completeInputs.add(row.materializedRef()); completeInputs.add(row.selectedSourceRef()); }
        for (var row : request.overlays()) { completeInputs.add(row.materializedPreimageRef()); completeInputs.add(row.sourceRef()); }
        for (var row : request.additions()) completeInputs.add(row.sourceRef());
        var inputGuard = BoundedSourceInputGuard.open(request.inputManifestRef(), request.taskOwner().taskPath());
        try (inputGuard) {
        inputGuard.requireExactInputs(completeInputs);
        var retiredKeys=validateRetirements(request,base,retired);
        Path output = Path.of(request.outputRoot()).normalize();
        if (Files.exists(output)) throw new IOException("Fresh successor output already exists; retain it for diagnosis");
        Map<String, Overlay> repairs = new HashMap<>();
        for (Overlay row : request.overlays()) repairs.put(row.group().name() + ":" + row.targetRelative(), row);
        List<IntegratedToolsGraph01.Selection> selected = new ArrayList<>(); Set<Path> directories = new HashSet<>(); directories.add(output);
        Set<String> unique = new HashSet<>(); int changed = 0; long logical = 0, charged = 0;
        for (IntegratedToolsGraph01.Selection row : base.sources()) {
            row.materializedRef().verify(); row.selectedSourceRef().verify();
            String key = row.group().name() + ":" + row.targetRelative();
            if (!unique.add(key)) throw new IOException("Duplicate base target");
            if(retiredKeys.contains(key)) continue;
            Overlay repair = repairs.get(key);
            ControlBuild.FileRef source = row.materializedRef(); String reason = row.reason();
            if (repair != null) {
                if (!source.equals(repair.materializedPreimageRef())) throw new IOException("Exact failed materialized preimage differs");
                source = repair.sourceRef(); reason = repair.reason(); changed++;
            }
            logical = Math.addExact(logical, source.bytes());
            charged = Math.addExact(charged, Math.multiplyExact(Math.floorDiv(Math.addExact(source.bytes(), 4095), 4096), 4096));
            Path target = output.resolve(row.group() == IntegratedToolsGraph01.Group.TOOLS ? "tools" : "host-overlay").resolve(row.targetRelative()).normalize();
            if (!target.startsWith(output)) throw new IOException("Source target escapes assigned successor");
            for (Path parent = target.getParent(); parent != null && parent.startsWith(output); parent = parent.getParent()) directories.add(parent);
            selected.add(new IntegratedToolsGraph01.Selection(row.group(), row.targetRelative(), row.originalPreimage(), row.source03Preimage(),
                    row.historicalCandidateRef(), repair != null ? source : row.selectedSourceRef(), reason, source));
        }
        for (Addition addition : request.additions()) {
            String key = addition.group().name() + ":" + addition.targetRelative();
            if (!unique.add(key)) throw new IOException("New fixture target already exists in base");
            ControlBuild.FileRef source = addition.sourceRef();
            logical = Math.addExact(logical, source.bytes());
            charged = Math.addExact(charged, Math.multiplyExact(Math.floorDiv(Math.addExact(source.bytes(),4095),4096),4096));
            Path target = output.resolve(addition.group() == IntegratedToolsGraph01.Group.TOOLS ? "tools" : "host-overlay").resolve(addition.targetRelative()).normalize();
            if (!target.startsWith(output)) throw new IOException("New fixture escapes assigned source root");
            for (Path parent = target.getParent(); parent != null && parent.startsWith(output); parent = parent.getParent()) directories.add(parent);
            var absent = new IntegratedToolsGraph01.Preimage(IntegratedToolsGraph01.PreimageKind.ABSENT, null);
            selected.add(new IntegratedToolsGraph01.Selection(addition.group(), addition.targetRelative(), absent, absent,
                    null, source, addition.reason(), source));
        }
        charged = Math.addExact(charged, Math.multiplyExact(directories.size(), 4096L));
        if (changed != request.overlays().size()) {
            throw new IOException("Every exact measured repair must be selected");
        }
        if (selected.size() != request.finalRoster().total()
                || selected.stream().filter(row -> row.group() == IntegratedToolsGraph01.Group.TOOLS).count() != request.finalRoster().tools()
                || selected.stream().filter(row -> row.group() == IntegratedToolsGraph01.Group.HOST).count() != request.finalRoster().host()) {
            throw new IOException("Exact issuer-selected tool/host source roster required");
        }
        requireExactSelection(request, selected); // Same resolved table, before any destination CREATE_NEW or copy.
        List<IntegratedToolsGraph01.Selection> planned = new ArrayList<>();
        for (var row : selected) {
            Path target = output.resolve(row.group() == IntegratedToolsGraph01.Group.TOOLS ? "tools" : "host-overlay").resolve(row.targetRelative());
            var pin = new ControlBuild.FileRef(target.toString(), row.materializedRef().bytes(), row.materializedRef().sha256());
            planned.add(new IntegratedToolsGraph01.Selection(row.group(), row.targetRelative(), row.originalPreimage(), row.source03Preimage(),
                    row.historicalCandidateRef(), row.selectedSourceRef(), row.reason(), pin));
        }
        List<ControlBuild.FileRef> provenance = new ArrayList<>(base.provenanceRefs());
        provenance.add(request.baseMapRef()); provenance.add(request.scopeClarificationRef()); provenance.add(request.qualificationEvidenceRef());
        for (Overlay row : request.overlays()) { provenance.add(row.correctionMapRef()); provenance.add(row.materializedPreimageRef()); }
        for (Addition addition : request.additions()) provenance.add(addition.correctionMapRef());
        if(request.retirementAuthorityRef()!=null) provenance.add(request.retirementAuthorityRef());
        for(var move:retired) provenance.addAll(List.of(move.sourceRef(),move.selectionRef(),move.finalSourceRef(),move.finalSelectionRef()));
        IntegratedToolsGraph01.Actual actual = new IntegratedToolsGraph01.Actual(base.schema(), request.machineId(), Instant.now().toString(),
                "MATERIALIZED_UNCOMPILED_UNQUALIFIED", requestRef, request.sourceAuthorityRef(), base.historicalHoldRef(), base.historicalToolsReceiptRef(),
                "All predecessor sources and qualifications remain immutable. This exact issuer-scoped successor is source-only. Root whole Maven and a fresh archive reader remain required; copying grants no Host, SDK, Native or Game authority.",
                request.finalRoster().tools(), request.finalRoster().host(), logical, charged, provenance, planned);
        byte[] exactMapBytes = ControlBuild.strictMapper().writerWithDefaultPrettyPrinter().writeValueAsBytes(actual);
        long reservedMetadataCharge = Math.addExact(pageCharge(exactMapBytes.length), pageCharge(inputGuard.maximumReceiptBytes()));
        if (Math.addExact(charged, reservedMetadataCharge) > request.conservativeNewRootCapBytes())
            throw new IOException("Complete source/map/native-witness metadata peak exceeds exact cap before CREATE_NEW");
        Files.createDirectory(output); List<IntegratedToolsGraph01.Selection> written = new ArrayList<>();
        for (IntegratedToolsGraph01.Selection row : selected) {
            Path target = output.resolve(row.group() == IntegratedToolsGraph01.Group.TOOLS ? "tools" : "host-overlay").resolve(row.targetRelative());
            Files.createDirectories(target.getParent());
            byte[] exactSourceBytes = readSourceForRequest(row.materializedRef(), request);
            Files.write(target, exactSourceBytes, StandardOpenOption.CREATE_NEW);
            ControlBuild.FileRef copied = ControlBuild.FileRef.measure(target);
            if (copied.bytes() != row.materializedRef().bytes() || !copied.sha256().equals(row.materializedRef().sha256())) throw new IOException("Successor bytes differ");
            written.add(new IntegratedToolsGraph01.Selection(row.group(), row.targetRelative(), row.originalPreimage(), row.source03Preimage(),
                    row.historicalCandidateRef(), row.selectedSourceRef(), row.reason(), copied));
        }
        if (!planned.equals(written)) throw new IOException("Copied exact source rows differ from the precharged immutable map");
        validateRetirements(request,base,retired);
        for(var move:retired) if(!Files.notExists(output.resolve("tools").resolve(move.oldTargetRelative().substring("build-tools/".length())),java.nio.file.LinkOption.NOFOLLOW_LINKS))
            throw new IOException("Retired test reappeared in the new source tree");
        for (IntegratedToolsGraph01.Selection row : base.sources()) { row.materializedRef().verify(); row.selectedSourceRef().verify(); }
        verifyRequest(requestRef, request);
        Files.write(output.resolve("SOURCE-MAP01.json"), exactMapBytes, StandardOpenOption.CREATE_NEW);
        System.out.println("successor_sources=" + selected.size() + ";added=" + request.additions().size() + ";changed=" + changed + ";source_charge=" + charged + ";qualification=NOT_RUN");
        }
        var inputReceipt = inputGuard.receipt();
        Files.write(Path.of(request.outputRoot()).resolve("SOURCE-INPUT-GUARD01.json"),
                ControlBuild.strictMapper().writeValueAsBytes(inputReceipt), StandardOpenOption.CREATE_NEW);
        Path finalMap = Path.of(request.outputRoot()).resolve("SOURCE-MAP01.json");
        var written = ControlBuild.strictMapper().readValue(readExact(ControlBuild.FileRef.measure(finalMap)), IntegratedToolsGraph01.Actual.class);
        long metadataCharge = 0;
        for (Path metadata : List.of(finalMap, Path.of(request.outputRoot()).resolve("SOURCE-INPUT-GUARD01.json")))
            metadataCharge = Math.addExact(metadataCharge, Math.multiplyExact(Math.floorDiv(Math.addExact(Files.size(metadata), 4095), 4096), 4096));
        if (Math.addExact(written.conservativeSourceChargeBytes(), metadataCharge) > request.conservativeNewRootCapBytes())
            throw new IOException("Final map and complete input witnesses exceed the exact source cap");
    }
    private static boolean expanded(String schema) { return schema.equals("xar.integrated-tools-firstcut-successor/v8") || schema.equals("xar.integrated-tools-firstcut-successor/v9"); }
    private static List<CompleteSourceGraph.Relocation> retirements(Request request) throws IOException {
        if(request.retirementAuthorityRef()==null) return List.of();
        var authority=ControlBuild.strictMapper().readValue(readExact(request.retirementAuthorityRef()),Retirements.class);
        if(!request.machineId().equals(authority.machineId())) throw new IOException("Retirement machine differs");
        return authority.relocations();
    }
    private static Set<String> validateRetirements(Request request,IntegratedToolsGraph01.Actual base,
            List<CompleteSourceGraph.Relocation> retired)throws IOException {
        var keys=new HashSet<String>(); var selected=new HashMap<String,ControlBuild.FileRef>();
        for(var move:retired) {
            String old=move.oldTargetRelative().substring("build-tools/".length()); String key="TOOLS:"+old;
            var row=base.sources().stream().filter(value->value.group()==IntegratedToolsGraph01.Group.TOOLS && value.targetRelative().equals(old)).findFirst()
                    .orElseThrow(()->new IOException("Retirement lacks an exact original Tools target"));
            row.materializedRef().verify();row.selectedSourceRef().verify();move.sourceRef().verify();
            if(row.materializedRef().bytes()!=move.sourceRef().bytes() || !row.materializedRef().sha256().equals(move.sourceRef().sha256())
                    || row.selectedSourceRef().bytes()!=move.sourceRef().bytes() || !row.selectedSourceRef().sha256().equals(move.sourceRef().sha256()) || !keys.add(key))
                throw new IOException("Retirement differs from both original and materialized source pins");
            for(var overlay:request.overlays()) if((overlay.group()+":"+overlay.targetRelative()).equals(key) || overlay.targetRelative().equalsIgnoreCase(move.newTargetRelative())) throw new IOException("Retired or external target also has an overlay");
            for(var addition:request.additions()) if((addition.group()+":"+addition.targetRelative()).equals(key)
                    || addition.targetRelative().equalsIgnoreCase(move.newTargetRelative())) throw new IOException("External transfer cannot be recreated in this candidate");
            var finalTable=ControlBuild.strictMapper().readValue(readExact(request.finalSelectionRef()),EffectiveSelection.class);
            for(var file:finalTable.selectedFiles()) if(file.key().equalsIgnoreCase(key) || file.targetRelative().equalsIgnoreCase(move.newTargetRelative()))
                throw new IOException("Retired or external destination appears in candidate winners");
            for(var origin:base.sources()) if(origin.targetRelative().equalsIgnoreCase(move.newTargetRelative())) throw new IOException("External destination already belongs to this candidate");
            selected.put(move.oldTargetRelative(),move.sourceRef()); selected.put(move.newTargetRelative(),move.finalSourceRef());
        }
        if(!retired.isEmpty()) CompleteSourceGraph.validateRelocations(request.machineId(),CompleteSourceGraph.modules(CompleteSourceGraph.Profile.G2_FULL_PARITY_20261025_R7),retired,selected);
        return keys;
    }
    private static void verifyRequest(ControlBuild.FileRef requestRef, Request request) throws IOException {
        requestRef.verify(); request.sourceAuthorityRef().verify(); request.scopeClarificationRef().verify();
        request.qualificationEvidenceRef().verify(); request.baseMapRef().verify();
        var scope = ControlBuild.strictMapper().readTree(readExact(request.scopeClarificationRef()));
        if (!scope.path("schema").asText().equals("xar.java-phase1.source-task-scope-clarification/v1")
                || !scope.path("machine_id").asText().equals(request.machineId())
                || !scope.path("actual_task_owner").isTextual()
                || !scope.path("actual_task_owner").textValue().equals(request.taskOwner().taskPath())
                || !Instant.now().isBefore(Instant.parse(scope.path("review_at_utc").asText()))
                || Instant.parse(request.reviewAtUtc()).isAfter(Instant.parse(scope.path("review_at_utc").asText()))
                || !scope.path("tools_source_files").isIntegralNumber()
                || scope.path("tools_source_files").intValue() != request.finalRoster().tools()
                || !scope.path("host_source_files").isIntegralNumber()
                || scope.path("host_source_files").intValue() != request.finalRoster().host()
                || !scope.path("physical_source_files").isIntegralNumber()
                || scope.path("physical_source_files").intValue() != request.finalRoster().total()
                || !scope.path("new_external_native_upper_bytes").isIntegralNumber()
                || request.conservativeNewRootCapBytes() > scope.path("new_external_native_upper_bytes").longValue()) {
            throw new IOException("Current exact same-machine issuer source scope/roster/cap required");
        }
        if (!scope.has("exact_selected_files_ref") || !sameSource(request.finalSelectionRef(),
                ControlBuild.strictMapper().treeToValue(scope.get("exact_selected_files_ref"), ControlBuild.FileRef.class)))
            throw new IOException("Explicit finalSelectionRef must equal issuer-bound complete selection");
        boolean admitted = false;
        if (scope.path("exact_roots").isArray()) for (var root : scope.path("exact_roots")) {
            if (root.isTextual() && Path.of(root.textValue()).normalize().equals(Path.of(request.outputRoot()))) admitted = true;
        }
        if (!admitted) throw new IOException("Successor output root is outside exact issuer source scope");
        for (Overlay row : request.overlays()) { row.sourceRef().verify(); row.materializedPreimageRef().verify(); row.correctionMapRef().verify(); }
        for (Addition row : request.additions()) { row.sourceRef().verify(); row.correctionMapRef().verify(); }
    }
    private static long pageCharge(long bytes) {
        return Math.multiplyExact(Math.floorDiv(Math.addExact(bytes, 4095), 4096), 4096);
    }
    static byte[] readExact(ControlBuild.FileRef exact) throws IOException {
        return readBounded(exact, 1 << 20);
    }
    /** Every source read is bounded by the actual issuer-verified whole source cap, not a metadata schema bound. */
    static byte[] readSource(ControlBuild.FileRef exact, long issuedSourceCapBytes) throws IOException {
        if (issuedSourceCapBytes < 1 || issuedSourceCapBytes > (8L << 20))
            throw new IOException("Actual finite issuer source cap required before source read");
        return readBounded(exact, Math.toIntExact(issuedSourceCapBytes));
    }
    private static byte[] readSourceForRequest(ControlBuild.FileRef exact, Request request) throws IOException {
        if (!expanded(request.schema()))
            return readSource(exact, request.conservativeNewRootCapBytes());
        if (request.conservativeNewRootCapBytes() < 1 || request.conservativeNewRootCapBytes() > (12L << 20))
            throw new IOException("Exact v8 finite source cap required");
        return readBounded(exact, Math.toIntExact(request.conservativeNewRootCapBytes()));
    }
    private static byte[] readBounded(ControlBuild.FileRef exact, int maximumBytes) throws IOException {
        if (exact.bytes() > maximumBytes) throw new IOException("Bounded exact source or metadata extent required");
        exact.verify(); byte[] bytes;
        try (var input = Files.newInputStream(Path.of(exact.path()))) {
            bytes = input.readNBytes(Math.toIntExact(exact.bytes()) + 1);
        }
        BoundedSourceInputGuard.verifyReadBytes(exact, bytes, maximumBytes); exact.verify();
        return bytes;
    }

    /** Closed source-only projection; existing source-copy request versions remain byte compatible. */
    public record ProjectionRequest(String schema,String machineId,TaskOwner taskOwner,String reviewAtUtc,
            ControlBuild.FileRef scopeRef,ControlBuild.FileRef inputManifestRef) {
        public ProjectionRequest {
            if(!"xar.integrated-tools-existing-projection-request/v1".equals(schema)
                    ||machineId==null||taskOwner==null||scopeRef==null||inputManifestRef==null)
                throw new IllegalArgumentException("Pinned existing-source projection required");
            Instant.parse(reviewAtUtc);
        }
    }
    public record ProjectionScope(String schema,String machineId,String issuer,TaskOwner taskOwner,String reviewAtUtc,
            ControlBuild.FileRef planRef,ControlBuild.FileRef auditRef,ControlBuild.FileRef baseMapRef,
            ControlBuild.FileRef selectionRef,String sourceRoot,String outputRoot,long metadataCapBytes) {
        public ProjectionScope {
            if(!"xar.integrated-tools-existing-projection-scope/v1".equals(schema)||!"/root".equals(issuer)
                    ||machineId==null||taskOwner==null||planRef==null||auditRef==null||baseMapRef==null||selectionRef==null
                    ||metadataCapBytes<4096||metadataCapBytes>(4L<<20))
                throw new IllegalArgumentException("Exact independently issued projection scope required");
            for(String root:List.of(sourceRoot,outputRoot))
                if(!Path.of(root).isAbsolute()||!Path.of(root).normalize().equals(Path.of(root)))
                    throw new IllegalArgumentException("Canonical absolute projection roots required");
            if(Path.of(sourceRoot).startsWith(Path.of(outputRoot))||Path.of(outputRoot).startsWith(Path.of(sourceRoot)))
                throw new IllegalArgumentException("Projection metadata must be independent of source payload");
            Instant.parse(reviewAtUtc);
        }
    }
    public record ProjectionSelection(String schema,String machineId,List<SelectedFile> selectedFiles) {
        public ProjectionSelection {
            if(!"xar.integrated-tools-existing-projection-selection/v1".equals(schema)||machineId==null)
                throw new IllegalArgumentException("Complete exact current source selection required");
            selectedFiles=List.copyOf(selectedFiles);var keys=new HashSet<String>();
            int tools=0;
            for(var row:selectedFiles) {
                if(!keys.add(row.key())) throw new IllegalArgumentException("Duplicate projected target");
                if(row.group()==IntegratedToolsGraph01.Group.TOOLS) tools++;
            }
            new SourceRoster(tools,selectedFiles.size()-tools);
        }
    }
    private static <T>T projectionRead(ControlBuild.FileRef pin,Class<T> type,boolean gzip,int maximum)throws IOException {
        byte[] bytes=readBounded(pin,maximum);
        if(gzip) try(var stream=new java.util.zip.GZIPInputStream(new java.io.ByteArrayInputStream(bytes))) {
            bytes=stream.readNBytes(maximum+1);
            if(bytes.length>maximum) throw new IOException("Finite decompressed graph metadata required");
        }
        return ControlBuild.strictMapper().readValue(bytes,type);
    }
    private static List<ControlBuild.FileRef> projectionInventory(ControlBuild.FileRef pin,int maximum)throws IOException {
        byte[] bytes=readBounded(pin,maximum);
        try(var stream=new java.util.zip.GZIPInputStream(new java.io.ByteArrayInputStream(bytes))) {
            bytes=stream.readNBytes(maximum+1);
            if(bytes.length>maximum) throw new IOException("Finite decompressed inventory required");
        }
        return ControlBuild.strictMapper().readValue(bytes,
                new com.fasterxml.jackson.core.type.TypeReference<List<ControlBuild.FileRef>>(){});
    }
    /** Full resolved copy set is checked before deriving a source-only Tools/Host view. */
    static List<IntegratedToolsGraph01.Selection> projectRows(String machineId,Path sourceRoot,
            CompleteSourceGraph.SelectionProof resolved,
            org.xar.ck3.control.build.CompleteSourceGraphMaterializer.NativeProof proof,
            org.xar.ck3.control.build.CompleteSourceGraphAudit.NativeSnapshot snapshot,
            List<ControlBuild.FileRef> inventory,IntegratedToolsGraph01.Actual base,ProjectionSelection selection)
            throws IOException {
        if(!machineId.equals(base.machineId())||!machineId.equals(selection.machineId())
                ||!machineId.equals(proof.machineId())||!machineId.equals(snapshot.machineId())
                ||!"xar.integrated-host-tools-source-map/v1".equals(base.schema())
                ||!proof.baselineAfter().equals(snapshot.baseline()))
            throw new IOException("Same-machine complete baseline and historical provenance required");
        var wanted=new HashMap<String,ControlBuild.FileRef>();
        for(var row:resolved.files())
            if(wanted.put(row.targetRelative(),row.sourceRef())!=null) throw new IOException("Duplicate resolved target");
        var nativeRows=new HashMap<String,org.xar.ck3.control.build.SharedSourceFiles.Witness>();
        for(var row:snapshot.materialized())
            if(nativeRows.put(Path.of(row.source().path()).normalize().toString(),row)!=null)
                throw new IOException("Duplicate independent destination");
        var inventoryRows=new HashMap<String,ControlBuild.FileRef>();
        for(var row:inventory)
            if(inventoryRows.put(Path.of(row.path()).normalize().toString(),row)!=null)
                throw new IOException("Duplicate complete inventory path");
        var copies=new HashMap<String,org.xar.ck3.control.build.CompleteSourceGraphMaterializer.CopyRow>();
        var identities=new HashSet<String>();
        for(var row:proof.copies()) {
            var original=wanted.get(row.targetRelative());var destination=row.destination();
            Path target=sourceRoot.resolve(row.targetRelative()).normalize();
            if(original==null||!target.startsWith(sourceRoot)||!row.originalBefore().equals(row.originalAfter())
                    ||!sameSource(original,row.originalBefore().source())
                    ||!target.equals(Path.of(destination.source().path()).normalize())
                    ||!sameSource(destination.source(),originalBytesAt(destination.source(),original))
                    ||destination.nativeFile().linkCount()!=1
                    ||destination.nativeFile().identityKey().equals(row.originalBefore().nativeFile().identityKey())
                    ||!identities.add(destination.nativeFile().identityKey())
                    ||!destination.equals(nativeRows.get(target.toString()))
                    ||!sameSource(destination.source(),inventoryRows.getOrDefault(target.toString(),original))
                    ||copies.put(row.targetRelative(),row)!=null)
                throw new IOException("Exact full ordinary-copy/native proof differs: "+row.targetRelative());
        }
        if(!copies.keySet().equals(wanted.keySet())||copies.size()!=inventoryRows.size()
                ||copies.size()!=nativeRows.size()) throw new IOException("Incomplete resolved/native/inventory set");
        var old=new HashMap<String,IntegratedToolsGraph01.Selection>();var hostTargets=new HashSet<String>();
        int baseTools=0;
        for(var row:base.sources()) {
            if(old.put(row.group()+":"+row.targetRelative(),row)!=null) throw new IOException("Duplicate historical target");
            if(row.group()==IntegratedToolsGraph01.Group.HOST) hostTargets.add(row.targetRelative());else baseTools++;
        }
        if(baseTools!=base.toolsSources()||hostTargets.size()!=base.hostOverlaySources()||hostTargets.isEmpty())
            throw new IOException("Complete historical Host key roster required");
        var selected=new HashMap<String,ControlBuild.FileRef>();
        for(var row:selection.selectedFiles()) selected.put(row.key(),row.sourceRef());
        var result=new ArrayList<IntegratedToolsGraph01.Selection>();var exactKeys=new HashSet<String>();
        var absent=new IntegratedToolsGraph01.Preimage(IntegratedToolsGraph01.PreimageKind.ABSENT,null);
        for(var row:resolved.files()) {
            boolean tools=row.targetRelative().startsWith("build-tools/");
            if(!tools&&!hostTargets.contains(row.targetRelative())) continue;
            var group=tools?IntegratedToolsGraph01.Group.TOOLS:IntegratedToolsGraph01.Group.HOST;
            String relative=tools?row.targetRelative().substring("build-tools/".length()):row.targetRelative();
            String key=group+":"+relative;var expected=selected.get(key);var copy=copies.get(row.targetRelative());
            if(expected==null||!sameSource(expected,row.sourceRef())||!exactKeys.add(key))
                throw new IOException("Complete declared current winners differ: "+key);
            org.xar.ck3.control.build.SharedSourceFiles.assertUnchanged(copy.originalBefore());
            org.xar.ck3.control.build.SharedSourceFiles.assertUnchanged(copy.destination());
            var previous=old.get(key);
            result.add(new IntegratedToolsGraph01.Selection(group,relative,
                    previous==null?absent:previous.originalPreimage(),previous==null?absent:previous.source03Preimage(),
                    previous==null?null:previous.historicalCandidateRef(),row.sourceRef(),
                    "Actual audited complete graph projection; source only; no source copy or runtime qualification",
                    copy.destination().source()));
        }
        if(!exactKeys.equals(selected.keySet())
                ||result.stream().filter(row->row.group()==IntegratedToolsGraph01.Group.HOST).count()!=hostTargets.size())
            throw new IOException("All Tools and complete original Host key set required");
        result.sort(java.util.Comparator.comparing(row->row.group()+":"+row.targetRelative()));
        return List.copyOf(result);
    }
    private static ControlBuild.FileRef originalBytesAt(ControlBuild.FileRef destination,ControlBuild.FileRef original) {
        return new ControlBuild.FileRef(destination.path(),original.bytes(),original.sha256());
    }
    static IntegratedToolsGraph01.Actual projectedMap(ControlBuild.FileRef requestRef,ProjectionScope scope,
            IntegratedToolsGraph01.Actual base,List<IntegratedToolsGraph01.Selection> rows) {
        int tools=0;long logical=0;
        for(var row:rows){if(row.group()==IntegratedToolsGraph01.Group.TOOLS)tools++;logical=Math.addExact(logical,row.materializedRef().bytes());}
        new SourceRoster(tools,rows.size()-tools);
        var provenance=new ArrayList<>(base.provenanceRefs());
        provenance.addAll(List.of(scope.planRef(),scope.auditRef(),scope.baseMapRef(),scope.selectionRef()));
        return new IntegratedToolsGraph01.Actual(base.schema(),scope.machineId(),Instant.now().toString(),
                "PROJECTED_EXISTING_MATERIALIZED_SOURCE_ONLY",requestRef,scope.auditRef(),base.historicalHoldRef(),
                base.historicalToolsReceiptRef(),"Existing audited ordinary files only. No payload copy or Host/SDK/Native/Game authority. Fresh complete Maven and full Own remain required.",
                tools,rows.size()-tools,logical,0,provenance,rows);
    }
    static void writeProjection(Path output,byte[] bytes)throws IOException {
        try(var channel=java.nio.channels.FileChannel.open(output,StandardOpenOption.CREATE_NEW,StandardOpenOption.WRITE)) {
            var buffer=java.nio.ByteBuffer.wrap(bytes);while(buffer.hasRemaining())channel.write(buffer);channel.force(true);
        }
        if(!java.util.Arrays.equals(bytes,Files.readAllBytes(output)))throw new IOException("Projection publication readback differs");
    }
    private static void projectExisting(ControlBuild.FileRef requestRef)throws Exception {
        var request=projectionRead(requestRef,ProjectionRequest.class,false,1<<20);
        var scope=projectionRead(request.scopeRef(),ProjectionScope.class,false,1<<20);
        if(!request.machineId().equals(WindowsJobProcess.currentMachineId())
                ||!request.machineId().equals(scope.machineId())||!request.taskOwner().equals(scope.taskOwner())
                ||!Instant.now().isBefore(Instant.parse(request.reviewAtUtc()))
                ||Instant.parse(request.reviewAtUtc()).isAfter(Instant.parse(scope.reviewAtUtc())))
            throw new IOException("Current same-machine independently bounded projection required");
        var guard=BoundedSourceInputGuard.open(request.inputManifestRef(),request.taskOwner().taskPath());
        Path output=Path.of(scope.outputRoot());
        try(guard) {
        var audit=projectionRead(scope.auditRef(),org.xar.ck3.control.build.CompleteSourceGraphAudit.AuditReceipt.class,false,1<<20);
        var manifest=projectionRead(audit.manifestRef(),org.xar.ck3.control.build.CompleteSourceGraphAudit.Manifest.class,false,1<<20);
        var actual=projectionRead(audit.producerActualRef(),org.xar.ck3.control.build.CompleteSourceGraphMaterializer.Receipt.class,false,1<<20);
        var plan=CompleteSourceGraph.readPlan(scope.planRef());
        if(!request.machineId().equals(plan.machineId())||!request.machineId().equals(audit.machineId())
                ||!request.machineId().equals(manifest.machineId())||!request.machineId().equals(actual.machineId())
                ||!sameSource(scope.planRef(),manifest.planRef())||!sameSource(scope.planRef(),actual.planRef())
                ||!sameSource(audit.producerActualRef(),manifest.producerActualRef())
                ||!sameSource(audit.auditCardRef(),manifest.auditCardRef())
                ||!sameSource(actual.cardRef(),manifest.producerCardRef())
                ||!sameSource(actual.inventoryRef(),manifest.inventoryRef())
                ||!sameSource(actual.copyProofRef(),manifest.copyProofRef())
                ||!sameSource(actual.qualifiedToolsRef(),manifest.qualifiedToolsRef())
                ||!sameSource(actual.materializerSourceRef(),manifest.materializerSourceRef())
                ||!sameSource(actual.graphContractSourceRef(),manifest.graphContractSourceRef())
                ||!Path.of(scope.sourceRoot()).equals(Path.of(actual.sourceRoot()))
                ||!Path.of(scope.sourceRoot()).equals(Path.of(manifest.sourceRoot()))
                ||plan.profile()!=manifest.profile()||plan.profile()!=actual.profile()
                ||!plan.selections().equals(manifest.selections())||!actual.size().equals(manifest.size()))
            throw new IOException("Plan/materializer/independent audit provenance differs");
        int bound=plan.profile().copyProofMaxBytes();
        var base=projectionRead(scope.baseMapRef(),IntegratedToolsGraph01.Actual.class,false,1<<20);
        var selection=projectionRead(scope.selectionRef(),ProjectionSelection.class,false,1<<20);
        var proof=projectionRead(manifest.copyProofRef(),org.xar.ck3.control.build.CompleteSourceGraphMaterializer.NativeProof.class,true,bound);
        var snapshot=projectionRead(manifest.independentNativeSnapshotRef(),org.xar.ck3.control.build.CompleteSourceGraphAudit.NativeSnapshot.class,true,bound);
        var inventory=projectionInventory(manifest.inventoryRef(),bound);
        var resolved=CompleteSourceGraph.resolve(plan);
        if(resolved.files().size()!=actual.size().files()||proof.baselineBefore().size()!=actual.baselineFiles()
                ||actual.baselineFiles()!=manifest.baselineFiles())throw new IOException("Complete actual file counts differ");
        var inputs=new ArrayList<ControlBuild.FileRef>(List.of(request.scopeRef(),scope.planRef(),
                scope.auditRef(),audit.manifestRef(),audit.producerActualRef(),audit.auditCardRef(),
                actual.cardRef(),manifest.inventoryRef(),manifest.copyProofRef(),manifest.independentNativeSnapshotRef(),
                manifest.qualifiedToolsRef(),manifest.materializerSourceRef(),manifest.graphContractSourceRef(),
                scope.baseMapRef(),scope.selectionRef()));
        var exactTargets=new HashSet<String>();
        for(var row:selection.selectedFiles())exactTargets.add(row.targetRelative());
        for(var row:proof.copies())if(exactTargets.contains(row.targetRelative())) {
            inputs.add(row.originalBefore().source());inputs.add(row.destination().source());
        }
            guard.requireExactInputs(inputs);
            var rows=projectRows(request.machineId(),Path.of(scope.sourceRoot()),resolved,proof,snapshot,inventory,base,selection);
            var current=ControlBuild.sourceManifest(Path.of(scope.sourceRoot()).resolve("build-tools"));
            var projected=rows.stream().filter(row->row.group()==IntegratedToolsGraph01.Group.TOOLS)
                    .map(IntegratedToolsGraph01.Selection::materializedRef).sorted(java.util.Comparator.comparing(ControlBuild.FileRef::path)).toList();
            if(!current.equals(projected))throw new IOException("Complete canonical Tools source manifest differs");
            byte[] bytes=ControlBuild.strictMapper().writerWithDefaultPrettyPrinter().writeValueAsBytes(projectedMap(requestRef,scope,base,rows));
            if(bytes.length>(1<<20)||pageCharge(bytes.length)+pageCharge(guard.maximumReceiptBytes())+4096>scope.metadataCapBytes())
                throw new IOException("Full source map/native receipt metadata peak exceeds issued cap");
            if(Files.exists(output,java.nio.file.LinkOption.NOFOLLOW_LINKS))throw new IOException("Fresh projection output required");
            Files.createDirectory(output);writeProjection(output.resolve("SOURCE-MAP01.json"),bytes);
        }
        writeProjection(output.resolve("SOURCE-INPUT-GUARD01.json"),ControlBuild.strictMapper().writeValueAsBytes(guard.receipt()));
        requestRef.verify();request.scopeRef().verify();
        System.out.println("EXISTING_SOURCE_PROJECTION_PASS;payload_copies=0;qualification=NOT_RUN");
    }

}
