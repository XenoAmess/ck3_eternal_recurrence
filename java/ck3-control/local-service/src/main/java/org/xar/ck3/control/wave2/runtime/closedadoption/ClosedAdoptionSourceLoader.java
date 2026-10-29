package org.xar.ck3.control.wave2.runtime.closedadoption;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.control.admission.closedpartial.ClosedPartialEpochProducer;
import org.xar.ck3.control.admission.closedpartial.ClosedPartialRpcEvidence;
import org.xar.ck3.control.admission.closedpartial.ClosedPartialSources;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FileStatIdentity;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.recovery.ClosedFailureRecoveryInput;
import org.xar.ck3.control.recovery.RecoveryEvidence;
import org.xar.ck3.control.wave2.runtime.savedproof.CachedOriginalSdkVerifier;
import org.xar.ck3.control.wave2.runtime.savedproof.SavedCheckpointMeasurementCoordinator;
import org.xar.ck3.control.wave2.runtime.savedproof.WindowsSavedProofIdentityReader;

/** Concrete source/cache adapter. Large persistence is obtained exclusively from the actual measurement token. */
public final class ClosedAdoptionSourceLoader implements ClosedAdoptionMaterial.CurrentSource, ClosedAdoptionSources.SourceVerifier {
    private record Cached(byte[] raw, FileStatIdentity identity) { }
    private final ClosedAdoptionRequest request;
    private final SavedCheckpointMeasurementCoordinator measurement;
    private final WindowsSavedProofIdentityReader metadata = new WindowsSavedProofIdentityReader();
    private final Map<ExactRef,Cached> cache = new HashMap<>();
    private long cachedBytes;
    private RecoveryEvidence epoch, prefix;
    public ClosedAdoptionSourceLoader(ClosedAdoptionRequest request, SavedCheckpointMeasurementCoordinator measurement) {
        this.request = Objects.requireNonNull(request); this.measurement = Objects.requireNonNull(measurement);
    }
    ClosedAdoptionRequest request() { return request; }
    /** Verify all small authority inputs before spending the independently issued single body-read ticket. */
    public synchronized void preflightSources() throws IOException {
        var i = request.inputs(); var c = request.closed(); var b = request.business();
        for (ExactRef ref : List.of(i.predecessor(),i.savedBasis(),i.priorQualification(),i.fullRequest(),i.failedFull(),i.autoRequest(),
                i.failedAuto(),i.rawState(),i.rawGovernance(),i.actualNext(),c.sdk(),c.gameExit(),c.supervisor(),c.recording(),c.capture(),c.screen(),
                b.savedSeed(),b.savedGovernance(),b.coldBound(),b.openingSemantic(),b.openingCapabilities(),b.classifierPin(),b.captureProbe(),b.captureCleanup())) {
            small(ref);
        }
        for (var task : request.tasks()) { small(task.spec()); small(task.closed()); small(task.unregistered()); }
        for (var cycle : request.cycles()) {
            exact(cycle.auto(),ClosedPartialRpcEvidence.MAX_BYTES); exact(cycle.metrics(),ClosedPartialRpcEvidence.MAX_BYTES);
            for (ExactRef ref : List.of(cycle.event(),cycle.ordinaryCredit(),cycle.autoAfter(),cycle.metricsAfter(),cycle.beforePlan())) { small(ref); }
            if (cycle.readonlySaveSkip().isPresent()) { small(cycle.readonlySaveSkip().orElseThrow()); }
        }
        for (ExactRef ref : List.of(b.classifierSource(),b.queueSource(),request.writerSource())) { exact(ref,ClosedPartialRpcEvidence.MAX_BYTES); }
    }
    @Override public synchronized ClosedAdoptionMaterial current() {
        try {
            var measured = measurement.requireCurrentCached();
            StrictJson.require(request.machineId().equals(measured.machineId()), "current measured source machine");
            var i = request.inputs(); var c = request.closed(); var b = request.business();
            ClosedFailureRecoveryInput input = new ClosedFailureRecoveryInput(request.machineId(), request.observedAtUtc(),
                    small(i.predecessor()),small(i.savedBasis()),small(i.priorQualification()),small(i.fullRequest()),small(i.failedFull()),
                    small(i.autoRequest()),small(i.failedAuto()),small(i.rawState()),small(i.rawGovernance()),small(i.actualNext()),
                    measured.driver(),measured.driverIdentity(),measured.save(),measured.saveIdentity());
            List<ClosedPartialSources.Task> tasks = new ArrayList<>();
            for (var task : request.tasks()) { tasks.add(new ClosedPartialSources.Task(task.role(),small(task.spec()),small(task.closed()),small(task.unregistered()))); }
            List<ClosedPartialSources.Cycle> rpc = new ArrayList<>(); List<ClosedAdoptionSources.CycleSources> cycles = new ArrayList<>();
            for (var cycle : request.cycles()) {
                rpc.add(new ClosedPartialSources.Cycle(new ClosedPartialRpcEvidence(cycle.auto(),exact(cycle.auto(),ClosedPartialRpcEvidence.MAX_BYTES)),
                        new ClosedPartialRpcEvidence(cycle.metrics(),exact(cycle.metrics(),ClosedPartialRpcEvidence.MAX_BYTES))));
                cycles.add(new ClosedAdoptionSources.CycleSources(small(cycle.event()),small(cycle.ordinaryCredit()),small(cycle.autoAfter()),small(cycle.metricsAfter()),
                        small(cycle.beforePlan()),cycle.readonlySaveSkip().map(this::smallUnchecked)));
            }
            ClosedPartialSources closed = new ClosedPartialSources(small(c.sdk()),small(c.gameExit()),small(c.supervisor()),small(c.recording()),small(c.capture()),small(c.screen()),tasks,rpc);
            ClosedAdoptionSources business = new ClosedAdoptionSources(small(b.savedSeed()),small(b.savedGovernance()),small(b.coldBound()),small(b.openingSemantic()),
                    small(b.openingCapabilities()),small(b.classifierPin()),b.classifierSource(),b.queueSource(),small(b.captureProbe()),small(b.captureCleanup()),cycles);
            ClosedPartialEpochProducer.Produced produced = ClosedPartialEpochProducer.compose(input,closed);
            if (epoch == null) {
                Files.createDirectories(request.metadataRoot());
                RecoveryEvidence newEpoch = publish(request.metadataRoot().resolve("closed-partial-epoch.json"),produced.epochBytes());
                RecoveryEvidence newPrefix = publish(request.metadataRoot().resolve("closed-partial-settled-prefix.json"),produced.prefixBytes());
                epoch = newEpoch; prefix = newPrefix;
            }
            RecoveryEvidence actualEpoch = Objects.requireNonNull(epoch), actualPrefix = Objects.requireNonNull(prefix);
            StrictJson.require(java.util.Arrays.equals(actualEpoch.bytes(),produced.epochBytes())
                    && java.util.Arrays.equals(actualPrefix.bytes(),produced.prefixBytes()), "fixed measured observation/input within this adoption session");
            verify(actualEpoch.reference()); verify(actualPrefix.reference());
            return new ClosedAdoptionMaterial(input,closed,actualEpoch,actualPrefix,business,this,new CachedOriginalSdkVerifier(measurement));
        } catch (IOException error) { throw new java.io.UncheckedIOException("UNAVAILABLE: actual closed-adoption sources",error); }
    }
    @Override public synchronized void verify(ExactRef source) {
        try { exact(source,ClosedPartialRpcEvidence.MAX_BYTES); }
        catch (IOException error) { throw new java.io.UncheckedIOException("UNAVAILABLE: current source identity",error); }
    }
    public RecoveryEvidence currentCanonicalReceipt() {
        try { return measurement.requireCurrentCached().canonicalReceipt(); }
        catch (IOException error) { throw new java.io.UncheckedIOException(error); }
    }
    public OriginalWriterTransaction.Target target() { return new OriginalWriterTransaction.Target(request.canonicalPath(),request.writerSource()); }
    public RecoveryEvidence publishBasis(byte[] raw) throws IOException { return publish(request.metadataRoot().resolve("current-saved-basis.json"),raw); }
    public RecoveryEvidence publishQualification(byte[] raw) throws IOException { return publish(request.metadataRoot().resolve("current-saved-qualification.json"),raw); }
    public void preflightProductionPublications() throws IOException {
        StrictJson.require(Files.isDirectory(request.metadataRoot(),java.nio.file.LinkOption.NOFOLLOW_LINKS)
                && !Files.isSymbolicLink(request.metadataRoot())
                && !Files.exists(request.metadataRoot().resolve("production-current-saved-basis.json"))
                && !Files.exists(request.metadataRoot().resolve("production-current-saved-qualification.json")),
                "create-only production publications are available before the production writer starts");
    }
    public RecoveryEvidence publishProductionBasis(byte[] raw) throws IOException { return publish(request.metadataRoot().resolve("production-current-saved-basis.json"),raw); }
    public RecoveryEvidence publishProductionQualification(byte[] raw) throws IOException { return publish(request.metadataRoot().resolve("production-current-saved-qualification.json"),raw); }
    private RecoveryEvidence publish(Path path, byte[] raw) throws IOException {
        StrictJson.require(raw.length > 0 && raw.length <= RecoveryEvidence.MAX_BYTES, "finite adoption metadata publication");
        try { Files.write(path,raw,StandardOpenOption.CREATE_NEW); }
        catch (java.nio.file.FileAlreadyExistsException existing) { /* Exact read below accepts only an identical original publication. */ }
        ExactRef ref = new ExactRef(path.toString(),raw.length,RecoveryEvidence.sha256(raw)); return new RecoveryEvidence(ref,exact(ref,RecoveryEvidence.MAX_BYTES));
    }
    private RecoveryEvidence smallUnchecked(ExactRef ref) {
        try { return small(ref); } catch (IOException error) { throw new java.io.UncheckedIOException(error); }
    }
    private RecoveryEvidence small(ExactRef ref) throws IOException { return new RecoveryEvidence(ref,exact(ref,RecoveryEvidence.MAX_BYTES)); }
    private byte[] exact(ExactRef ref, int maximum) throws IOException {
        String name = ref.path().replace('\\','/').toLowerCase(java.util.Locale.ROOT);
        StrictJson.require(!name.endsWith("/driver-state.json") && !name.endsWith(".ck3") && !name.endsWith(".sav"), "source cache never reads Driver/SAVE bodies");
        StrictJson.require(ref.bytes() > 0 && ref.bytes() <= maximum, "complete bounded original source");
        Path path = Path.of(ref.path()); FileStatIdentity before = metadata.stat(path); Cached prior = cache.get(ref);
        if (prior != null) { StrictJson.require(prior.identity().equals(before), "cached source identity drift"); return prior.raw(); }
        StrictJson.require(cachedBytes + ref.bytes() <= 16L * 1024 * 1024, "finite shared small-source RAM pool");
        byte[] raw;
        try (var stream = Files.newInputStream(path)) { raw = stream.readNBytes(maximum + 1); }
        StrictJson.require(raw.length == ref.bytes() && RecoveryEvidence.sha256(raw).equals(ref.sha256()) && before.equals(metadata.stat(path)), "actual original source hash and stable native identity");
        cache.put(ref,new Cached(raw,before)); cachedBytes += raw.length; return raw;
    }
}
