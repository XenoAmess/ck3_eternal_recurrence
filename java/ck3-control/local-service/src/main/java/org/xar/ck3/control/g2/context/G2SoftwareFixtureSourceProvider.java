package org.xar.ck3.control.g2.context;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import java.util.concurrent.atomic.AtomicLong;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.common.G2Request;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.common.Milestone;
import org.xar.ck3.control.g2.context.G2WindowsReadOnlyObservation.FileObservation;
import org.xar.ck3.control.g2.context.G2WindowsReadOnlyObservation.FileRead;

/** Explicit software fixture provenance, never a NativeArrival or a current game observation. */
public final class G2SoftwareFixtureSourceProvider implements G2CallContextProducer.Provider {
    public static final String SCHEMA = "xar.g2-software-fixture-origin/v1";
    public static final String SCOPE = "SOFTWARE_FIXTURE_ONLY";
    public record Origin(String machineId, String observedAtUtc, ExactRef programRef,
            List<ExactRef> sourceRefs, List<ExactRef> originalFixtureRefs, List<Milestone> milestones,
            ExactRef probeRequestRef, ExactRef probePayloadRef, Milestone probeMilestone) {
        public Origin {
            StrictJson.text(machineId); StrictJson.text(observedAtUtc); Instant.parse(observedAtUtc);
            StrictJson.require(observedAtUtc.endsWith("Z"), "software observation UTC required");
            Objects.requireNonNull(programRef); sourceRefs = List.copyOf(sourceRefs);
            originalFixtureRefs = List.copyOf(originalFixtureRefs); milestones = List.copyOf(milestones);
            Objects.requireNonNull(probeRequestRef); Objects.requireNonNull(probePayloadRef); Objects.requireNonNull(probeMilestone);
            StrictJson.require(!sourceRefs.isEmpty() && !originalFixtureRefs.isEmpty() && originalFixtureRefs.size() <= 4096
                    && !milestones.isEmpty() && new HashSet<>(milestones).size() == milestones.size()
                    && milestones.contains(probeMilestone) && originalFixtureRefs.contains(probeRequestRef), "declared pure milestones and original producer probe required");
        }
    }
    private final G2WindowsReadOnlyObservation observer;
    private final Origin origin;
    private final ExactRef originRef;
    private final List<FileObservation> files;
    private final WindowsJobProcess.ProcessIdentity host;
    private final AtomicLong calls = new AtomicLong();
    private G2SoftwareFixtureSourceProvider(G2WindowsReadOnlyObservation observer, Origin origin, ExactRef originRef,
            List<FileObservation> files, WindowsJobProcess.ProcessIdentity host) {
        this.observer = observer; this.origin = origin; this.originRef = originRef; this.files = List.copyOf(files); this.host = host;
    }
    /** The actual Root lifecycle emits this new origin after assembling measured program/fixture inputs. */
    public static ExactRef writeOrigin(Origin origin, Path destination) throws IOException {
        ObjectNode row = StrictJson.object(); row.put("schema", SCHEMA); row.put("scope", SCOPE);
        row.put("machine_id", origin.machineId()); row.put("observed_at_utc", origin.observedAtUtc());
        row.set("program_ref", origin.programRef().toJson());
        var sources = row.putArray("source_refs"); for (ExactRef ref : origin.sourceRefs()) { sources.add(ref.toJson()); }
        var fixtures = row.putArray("original_fixture_refs"); for (ExactRef ref : origin.originalFixtureRefs()) { fixtures.add(ref.toJson()); }
        var milestones = row.putArray("milestones"); for (Milestone value : origin.milestones()) { milestones.add("G2-" + value.name()); }
        row.set("probe_request_ref", origin.probeRequestRef().toJson()); row.set("probe_payload_ref", origin.probePayloadRef().toJson());
        row.put("probe_milestone", "G2-" + origin.probeMilestone().name());
        G2WindowsReadOnlyObservation.plain(destination);
        byte[] raw = StrictJson.canonical(row, 1_048_576);
        java.nio.file.Files.write(destination, raw, java.nio.file.StandardOpenOption.CREATE_NEW);
        ExactRef result = new ExactRef(destination.toAbsolutePath().normalize().toString(), raw.length, G2RetainedNativeSourceProvider.sha256(raw));
        load(result); // Executes the same runtime validator used at actual host startup.
        return result;
    }
    /** Only trusted Root startup supplies this exact origin; no request can select or replace it. */
    public static G2SoftwareFixtureSourceProvider load(ExactRef originRef) throws IOException {
        G2WindowsReadOnlyObservation observer = new G2WindowsReadOnlyObservation();
        FileRead originRead = exact(observer, originRef, 1_048_576);
        ObjectNode row = StrictJson.object(StrictJson.parse(originRead.bytes(), 1_048_576), Set.of("schema", "scope", "machine_id", "observed_at_utc",
                "program_ref", "source_refs", "original_fixture_refs", "milestones", "probe_request_ref", "probe_payload_ref", "probe_milestone"));
        StrictJson.require(SCHEMA.equals(StrictJson.text(row.get("schema"))) && SCOPE.equals(StrictJson.text(row.get("scope"))), "explicit SOFTWARE fixture origin required");
        List<Milestone> milestones = new ArrayList<>();
        StrictJson.require(row.get("milestones").isArray(), "declared pure milestone list required");
        for (JsonNode value : row.get("milestones")) { milestones.add(milestone(StrictJson.text(value))); }
        Origin origin = new Origin(StrictJson.text(row.get("machine_id")), StrictJson.text(row.get("observed_at_utc")),
                ExactRef.fromJson(row.get("program_ref")), refs(row.get("source_refs")), refs(row.get("original_fixture_refs")), milestones,
                ExactRef.fromJson(row.get("probe_request_ref")), ExactRef.fromJson(row.get("probe_payload_ref")), milestone(StrictJson.text(row.get("probe_milestone"))));
        if (!observer.machineId().equals(origin.machineId())) { throw new IOException("software origin belongs to another machine"); }
        WindowsJobProcess.ProcessIdentity host = observer.process(ProcessHandle.current().pid());
        ArrayList<FileObservation> files = new ArrayList<>(); files.add(originRead.observation());
        files.add(exact(observer, origin.programRef(), 1_048_576).observation());
        for (ExactRef source : origin.sourceRefs()) { files.add(exact(observer, source, 1_048_576).observation()); }
        for (ExactRef fixture : origin.originalFixtureRefs()) { files.add(exact(observer, fixture, 8_388_608).observation()); }
        FileRead originalRequest = exact(observer, origin.probeRequestRef(), 8_388_608);
        FileRead originalPayload = exact(observer, origin.probePayloadRef(), 8_388_608); files.add(originalPayload.observation());
        G2Request parsed = G2Wire.decodeRequest(originalRequest.bytes());
        if (parsed.milestone() != origin.probeMilestone() || !Arrays.equals(parsed.payload().bytes(), originalPayload.bytes())) {
            throw new IOException("software probe payload is not the exact original producer request token");
        }
        for (FileObservation file : files) { if (!file.identity().equals(observer.stat(Path.of(file.reference().path())))) { throw new IOException("software fixture source changed during startup"); } }
        if (!host.equals(observer.process(ProcessHandle.current().pid()))) { throw new IOException("software host identity changed"); }
        return new G2SoftwareFixtureSourceProvider(observer, origin, originRef, files, host);
    }
    @Override public G2CallContextProducer.Result context(Milestone milestone, ProjectionJson payload) {
        G2CallContextProducer.requirePayloadToken(payload);
        if (!origin.milestones().contains(milestone)) { return unavailable(G2CallContextProducer.Reason.SOURCE_REJECTED, "milestone is outside Root software fixture scope"); }
        try {
            if (!observer.machineId().equals(origin.machineId()) || !host.equals(observer.process(ProcessHandle.current().pid()))) {
                return unavailable(G2CallContextProducer.Reason.SOURCE_IDENTITY_CHANGED, "software host/machine identity changed");
            }
            for (FileObservation file : files) {
                if (!file.identity().equals(observer.stat(Path.of(file.reference().path())))) {
                    return unavailable(G2CallContextProducer.Reason.SOURCE_IDENTITY_CHANGED, "Root software fixture source identity changed");
                }
            }
            long sequence = calls.incrementAndGet();
            if (sequence < 1 || sequence > StrictJson.MAX_SAFE_INTEGER) { return unavailable(G2CallContextProducer.Reason.REQUEST_SEQUENCE_EXHAUSTED, "software fixture context sequence exhausted"); }
            G2Source source = new G2Source(origin.machineId(), origin.observedAtUtc(),
                    "SOFTWARE_FIXTURE@sha256:" + origin.programRef().sha256(), originRef);
            return new G2CallContextProducer.Available(new G2CallContextProducer.Context(source,
                    "software:" + milestone.name() + ":" + originRef.sha256().substring(0, 16) + ":" + sequence,
                    G2RetainedNativeSourceProvider.sha256(payload.bytes())));
        } catch (IOException | RuntimeException unavailable) {
            return unavailable(G2CallContextProducer.Reason.OWNER_FAILED, "actual read-only software source observation unavailable");
        }
    }
    public Origin origin() { return origin; }
    public ExactRef originRef() { return originRef; }
    private static FileRead exact(G2WindowsReadOnlyObservation observer, ExactRef ref, int maximum) throws IOException {
        if (ref.bytes() < 1 || ref.bytes() > maximum) { throw new IOException("bounded explicit software source required"); }
        FileRead value = observer.read(Path.of(ref.path()), maximum);
        ExactRef actual = value.observation().reference();
        if (ref.bytes() != actual.bytes() || !ref.sha256().equals(actual.sha256())
                || !Path.of(ref.path()).toAbsolutePath().normalize().equals(Path.of(actual.path()).toAbsolutePath().normalize())) {
            throw new IOException("actual software source exact reference differs");
        }
        return value;
    }
    private static List<ExactRef> refs(JsonNode node) {
        StrictJson.require(node != null && node.isArray(), "exact software source references required");
        ArrayList<ExactRef> result = new ArrayList<>(); for (JsonNode value : node) { result.add(ExactRef.fromJson(value)); } return List.copyOf(result);
    }
    private static Milestone milestone(String value) {
        for (Milestone milestone : Milestone.values()) { if (("G2-" + milestone.name()).equals(value)) { return milestone; } }
        throw new IllegalArgumentException("closed G2 pure milestone required");
    }
    private static G2CallContextProducer.Unavailable unavailable(G2CallContextProducer.Reason reason, String detail) {
        return new G2CallContextProducer.Unavailable(reason, detail);
    }
}
