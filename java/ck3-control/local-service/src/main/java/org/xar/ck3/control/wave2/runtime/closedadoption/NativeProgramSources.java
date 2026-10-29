package org.xar.ck3.control.wave2.runtime.closedadoption;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashMap;
import java.util.Map;
import java.util.Set;
import java.util.Optional;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.SdkDerivedSource32;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.recovery.RecoveryEvidence;
import org.xar.ck3.control.wave2.runtime.savedproof.SavedCheckpointMeasurementCoordinator;
import org.xar.ck3.control.wave2.runtime.savedproof.SavedProofReadTicket;
import org.xar.ck3.control.wave2.runtime.savedproof.WindowsSavedProofIdentityReader;

/** Source projection of the actual already-verified Prepared quote and original read ticket. No permission object. */
public record NativeProgramSources(ExactRef entrypoint, ExactRef prelaunch, Path sdkRoot, ExactRef sdkFreeze,
        Map<Path,ExactRef> approved, Optional<SdkDerivedSource32.SourcePurpose> sourcePurpose) {
    public NativeProgramSources { approved = Map.copyOf(approved); java.util.Objects.requireNonNull(sourcePurpose); }

    static NativeProgramSources fromActualPrepared(SavedProofReadTicket ticket, Path runtimeRoot,
            ExactRef planRef, ExactRef quoteRef, ExactRef basisRef, ExactRef qualificationRef) throws IOException {
        return project(ticket.machineId(),ticket.sdkRoot(),ticket.sdkFreeze(),runtimeRoot,planRef,quoteRef,basisRef,qualificationRef,
                SavedCheckpointMeasurementCoordinator.sourcePins(ticket));
    }
    /** Source data only. Callers cannot turn this projection into a private Root session or execution grant. */
    public static NativeProgramSources project(ClosedInputsSessionAuthority.NativeRestoreInputs inputs) throws IOException {
        String machine = StrictJson.text(StrictJson.parse(inputs.basis().bytes()).get("machine_id"));
        return project(machine,inputs.sdkRoot(),inputs.sdkFreeze(),inputs.runtimeRoot(),inputs.plan(),inputs.quote(),
                inputs.basis().reference(),inputs.qualificationRef(),
                SavedCheckpointMeasurementCoordinator.sourceInventoryPins(machine,inputs.sdkRoot(),inputs.sdkFreeze()));
    }
    private static NativeProgramSources project(String machineId, Path sdkRoot, ExactRef sdkFreeze, Path runtimeRoot,
            ExactRef planRef, ExactRef quoteRef, ExactRef basisRef, ExactRef qualificationRef,
            Map<String,ExactRef> sdkPins) throws IOException {
        Map<Path,ExactRef> approved = new HashMap<>();
        // Reuse the sole existing strict SDK inventory parser; it reads source metadata/validator only.
        for (ExactRef source : sdkPins.values()) {
            put(approved,source);
        }
        JsonNode quote = read(quoteRef,1_048_576);
        StrictJson.require(quote.isObject() && "xar.current-saved-cold-quote/v5".equals(StrictJson.text(quote.get("schema")))
                && machineId.equals(StrictJson.text(quote.get("machine_id")))
                && runtimeRoot.equals(Path.of(StrictJson.text(quote.get("runtime_root"))))
                && planRef.equals(ExactRef.fromJson(quote.get("plan_ref")))
                && basisRef.equals(ExactRef.fromJson(quote.get("basis_ref")))
                && qualificationRef.equals(ExactRef.fromJson(quote.get("validation_ref"))),
                "actual same-session Prepared quote source tuple");
        JsonNode files = quote.get("files");
        StrictJson.require(files != null && files.isArray() && !files.isEmpty() && files.size() <= 192,
                "bounded actual Prepared output inventory");
        ExactRef entrypoint = null;
        ExactRef prelaunch = null;
        for (JsonNode item : files) {
            var row = StrictJson.object(item,Set.of("path","relative_path","bytes","sha256","mode","source_ref"));
            Path actualPath = Path.of(StrictJson.text(row.get("path")));
            StrictJson.require(actualPath.isAbsolute() && actualPath.normalize().equals(actualPath),"absolute actual quoted output");
            ExactRef actual = new ExactRef(actualPath.toString(),StrictJson.integer(row.get("bytes"),1,2_097_152),
                    StrictJson.text(row.get("sha256")));
            String mode = StrictJson.text(row.get("mode"));
            StrictJson.require("create-only".equals(mode) || "hardlink".equals(mode),"original exact output mode");
            JsonNode source = row.get("source_ref");
            StrictJson.require(source != null && ("hardlink".equals(mode) != source.isNull()),"original explicit hardlink provenance");
            if (!source.isNull()) {
                ExactRef origin = ExactRef.fromJson(source);
                StrictJson.require(origin.bytes() == actual.bytes() && origin.sha256().equals(actual.sha256())
                        && !Path.of(origin.path()).equals(actualPath),"actual quoted source/output bytes binding");
            }
            JsonNode relative = row.get("relative_path");
            StrictJson.require(relative != null,"explicit nullable original output relative path");
            if (!relative.isNull()) {
                String child = StrictJson.text(relative); Path path = Path.of(child);
                StrictJson.require(!path.isAbsolute() && !child.contains("\\") && !child.contains(":")
                        && path.normalize().equals(path) && !path.startsWith("..")
                        && runtimeRoot.resolve(path).equals(actualPath),"exact original runtime output mapping");
                if ("root_p37c23_mcp_entry.py".equals(child)) {
                    StrictJson.require(entrypoint == null,"one actual quoted original MCP entry"); entrypoint = actual;
                }
                if ("ROOT-C23-COLD-PRELAUNCH.json".equals(child)) {
                    StrictJson.require(prelaunch == null,"one actual quoted original cold prelaunch"); prelaunch = actual;
                }
            } else {
                StrictJson.require(!actualPath.startsWith(runtimeRoot),"explicit original external output");
            }
            put(approved,actual);
        }
        StrictJson.require(entrypoint != null && prelaunch != null,"actual Prepared quote must contain its original deployed MCP entry and cold prelaunch");
        Optional<SdkDerivedSource32.SourcePurpose> purpose=Optional.empty();
        JsonNode freeze=read(sdkFreeze,1_048_576);
        if (freeze.hasNonNull("schema") && SdkDerivedSource32.SCHEMA.equals(StrictJson.text(freeze.get("schema")))) {
            // sourceInventoryPins above has already invoked the sole complete Java verifier.
            purpose=Optional.of(SdkDerivedSource32.read(new ControlBuild.FileRef(sdkFreeze.path(),sdkFreeze.bytes(),sdkFreeze.sha256())).sourcePurpose());
        }
        return new NativeProgramSources(entrypoint,prelaunch,sdkRoot,sdkFreeze,approved,purpose);
    }
    void requireNativeRestoreSourcePurpose() {
        StrictJson.require(sourcePurpose.isEmpty() || sourcePurpose.orElseThrow()==SdkDerivedSource32.SourcePurpose.PARENT_NATIVE_UNCHANGED,
                "FULL_SOFTWARE derived sources do not inherit Native restore qualification; use the independently qualified unchanged-Native closure");
    }
    void verifyMembership(WindowsJobProcess.OwnedStdioSpec spec, ColdRestoreProfile.Verified profile) throws IOException {
        requireNativeRestoreSourcePurpose();
        profile.requireUnchanged();
        Map<Path,ExactRef> currentApproved = new HashMap<>(approved);
        for (ExactRef source : profile.sourcePins()) { put(currentApproved,source); }
        boolean entry = false;
        boolean manifest = false;
        for (var source : spec.programSourceRefs()) {
            var requested = new ExactRef(source.path(),source.bytes(),source.sha256());
            StrictJson.require(requested.equals(currentApproved.get(Path.of(requested.path()))),
                    "Native source belongs to original Root-ticket SDK, actual Prepared closure or actual original cold-profile verification");
            entry |= requested.equals(entrypoint);
            manifest |= requested.equals(profile.manifestRef());
        }
        StrictJson.require(entry && manifest,"Native source tuple includes its actual quoted original MCP entry and genuinely verified physical environment");
    }
    private static void put(Map<Path,ExactRef> approved, ExactRef source) {
        Path path = Path.of(source.path()); ExactRef previous = approved.putIfAbsent(path,source);
        StrictJson.require(previous == null || previous.equals(source),"one exact pin per approved source path");
    }
    private static JsonNode read(ExactRef ref, int bound) throws IOException {
        StrictJson.require(ref.bytes() > 0 && ref.bytes() <= bound,"bounded original source metadata");
        var identities = new WindowsSavedProofIdentityReader(); Path path = Path.of(ref.path());
        var before = identities.stat(path); byte[] raw;
        try (var input = Files.newInputStream(path)) { raw = input.readNBytes(bound + 1); }
        StrictJson.require(raw.length <= bound && before.equals(identities.stat(path)),"unchanged actual source metadata native identity");
        StrictJson.require(raw.length == ref.bytes() && RecoveryEvidence.sha256(raw).equals(ref.sha256()),"exact original source metadata bytes");
        return StrictJson.parse(raw,bound);
    }
}
