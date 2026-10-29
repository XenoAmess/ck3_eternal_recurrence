package org.xar.ck3.control.g2.context;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.time.Instant;
import java.util.Arrays;
import java.util.EnumSet;
import java.util.List;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.MapAdmissionServiceOwner;
import org.xar.ck3.control.build.RootSoftwareFixtureHandoff;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.common.G2Request;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.common.Milestone;
import org.xar.ck3.control.g2.context.G2CallContextProducer;
import org.xar.ck3.control.g2.context.G2CallContextWire;
import org.xar.ck3.control.g2.context.G2SoftwareFixtureSourceProvider;
import org.xar.ck3.control.g2.context.G2WindowsReadOnlyObservation;
import org.xar.ck3.control.g2.context.G2WindowsReadOnlyObservation.FileObservation;
import org.xar.ck3.control.g2.context.G2WindowsReadOnlyObservation.FileRead;

/** One trusted startup identity, one software activation; never a request-selected installer. */
public final class DeferredRootSoftwareFixtureProvider implements G2CallContextProducer.Provider {
    private final G2WindowsReadOnlyObservation observer;
    private final RootSoftwareFixtureHandoff.Pending pending;
    private final FileObservation pendingFile;
    private final WindowsJobProcess.ProcessIdentity host;
    private final G2Request probe;
    private final byte[] probePayload;
    private G2SoftwareFixtureSourceProvider active;
    private FileObservation activationFile;
    private boolean failed;

    private DeferredRootSoftwareFixtureProvider(G2WindowsReadOnlyObservation observer,
            RootSoftwareFixtureHandoff.Pending pending, FileObservation pendingFile,
            WindowsJobProcess.ProcessIdentity host, G2Request probe, byte[] probePayload) {
        this.observer = observer; this.pending = pending; this.pendingFile = pendingFile;
        this.host = host; this.probe = probe; this.probePayload = probePayload.clone();
    }

    public static DeferredRootSoftwareFixtureProvider load(ExactRef descriptor) throws IOException {
        if (!RootSoftwareFixtureHandoff.CONTEXT_PATH.equals(G2CallContextWire.HTTP_PATH)) {
            throw new IOException("software context protocol differs from the shared host contract");
        }
        G2WindowsReadOnlyObservation observer = new G2WindowsReadOnlyObservation();
        FileRead read = exact(observer, descriptor, 1_048_576);
        var pending = RootSoftwareFixtureHandoff.readPending(control(descriptor));
        RootSoftwareFixtureHandoff.verifyInputs(pending);
        WindowsJobProcess.ProcessIdentity host = observer.process(ProcessHandle.current().pid());
        if (!observer.machineId().equals(pending.machineId())
                || !Path.of(host.executable()).equals(Path.of(pending.javaExecutableRef().path()))) {
            throw new IOException("software descriptor belongs to another actual host executable or machine");
        }
        G2Request probe = G2Wire.decodeRequest(exact(observer, exact(pending.request().probeRequestRef()), 8_388_608).bytes());
        byte[] payload = exact(observer, exact(pending.request().probePayloadRef()), 8_388_608).bytes();
        if (!Arrays.equals(probe.payload().bytes(), payload)) throw new IOException("original producer probe payload token differs");
        if (!read.observation().identity().equals(observer.stat(Path.of(descriptor.path())))) {
            throw new IOException("Root descriptor changed during host startup");
        }
        return new DeferredRootSoftwareFixtureProvider(observer, pending, read.observation(), host, probe, payload);
    }

    @Override public synchronized G2CallContextProducer.Result context(Milestone milestone, ProjectionJson payload) {
        G2CallContextProducer.requirePayloadToken(payload);
        if (failed) return unavailable(G2CallContextProducer.Reason.OWNER_FAILED, "Root software activation previously failed; no retry authority");
        try {
            if (!Instant.now().isBefore(Instant.parse(pending.leaseDeadlineUtc()))
                    || !host.equals(observer.process(ProcessHandle.current().pid()))
                    || !pendingFile.identity().equals(observer.stat(Path.of(pendingFile.reference().path())))) {
                failed = true;
                return unavailable(G2CallContextProducer.Reason.SOURCE_IDENTITY_CHANGED, "original Root software host or descriptor unavailable");
            }
            RootSoftwareFixtureHandoff.verifyInputs(pending);
            if (active == null) {
                Path activationPath = RootSoftwareFixtureHandoff.publication(pending, "software-fixture-activation.json");
                if (!Files.exists(activationPath, LinkOption.NOFOLLOW_LINKS)) {
                    return unavailable(G2CallContextProducer.Reason.RETAINED_SOURCE_MISSING, "Root has not published the actual qualified program activation");
                }
                if (milestone != probe.milestone() || !Arrays.equals(payload.bytes(), probePayload)) {
                    return unavailable(G2CallContextProducer.Reason.SOURCE_REJECTED, "only the original Root probe can first activate the software fixture");
                }
                activate(activationPath);
            } else if (!activationFile.identity().equals(observer.stat(Path.of(activationFile.reference().path())))) {
                failed = true;
                return unavailable(G2CallContextProducer.Reason.SOURCE_IDENTITY_CHANGED, "Root software activation identity changed");
            }
            return active.context(milestone, payload);
        } catch (IOException | RuntimeException refusal) {
            failed = true;
            return unavailable(G2CallContextProducer.Reason.OWNER_FAILED, "actual Root software activation validation failed");
        }
    }

    private void activate(Path activationPath) throws IOException {
        G2WindowsReadOnlyObservation.plain(activationPath);
        FileRead activationRead = observer.read(activationPath, 1_048_576);
        var activation = RootSoftwareFixtureHandoff.readActivation(control(activationRead.observation().reference()));
        RootSoftwareFixtureHandoff.verifyActivation(pending, activation);
        var expectedHost = new MapAdmissionServiceOwner.ProcessWire(host.pid(), host.creationFiletimeDecimal(), host.executable());
        if (!expectedHost.equals(activation.hostProcess())) throw new IOException("activation names another PID or native birth");
        EnumSet<Milestone> milestones = EnumSet.noneOf(Milestone.class);
        for (var ref : pending.request().originalRequestRefs()) {
            milestones.add(G2Wire.decodeRequest(exact(observer, exact(ref), 8_388_608).bytes()).milestone());
        }
        var origin = new G2SoftwareFixtureSourceProvider.Origin(pending.machineId(), Instant.now().toString(),
                exact(activation.programRef()), exacts(pending.sourceRefs()), exacts(pending.request().originalFixtureRefs()),
                List.copyOf(milestones), exact(pending.request().probeRequestRef()), exact(pending.request().probePayloadRef()), probe.milestone());
        Path destination = RootSoftwareFixtureHandoff.publication(pending, "software-fixture-origin.json");
        ExactRef originRef = G2SoftwareFixtureSourceProvider.writeOrigin(origin, destination);
        G2SoftwareFixtureSourceProvider candidate = G2SoftwareFixtureSourceProvider.load(originRef);
        RootSoftwareFixtureHandoff.verifyActivation(pending, activation);
        if (!host.equals(observer.process(ProcessHandle.current().pid()))
                || !pendingFile.identity().equals(observer.stat(Path.of(pendingFile.reference().path())))
                || !activationRead.observation().identity().equals(observer.stat(activationPath))) {
            throw new IOException("Root software source or host changed during one-time activation");
        }
        activationFile = activationRead.observation(); active = candidate;
    }
    private static List<ExactRef> exacts(List<ControlBuild.FileRef> refs) { return refs.stream().map(DeferredRootSoftwareFixtureProvider::exact).toList(); }
    private static ExactRef exact(ControlBuild.FileRef ref) { return new ExactRef(ref.path(), ref.bytes(), ref.sha256()); }
    private static ControlBuild.FileRef control(ExactRef ref) { return new ControlBuild.FileRef(ref.path(), ref.bytes(), ref.sha256()); }
    private static FileRead exact(G2WindowsReadOnlyObservation observer, ExactRef ref, int maximum) throws IOException {
        if (ref.bytes() < 1 || ref.bytes() > maximum) throw new IOException("bounded exact Root software input required");
        FileRead read = observer.read(Path.of(ref.path()), maximum);
        ExactRef actual = read.observation().reference();
        if (actual.bytes() != ref.bytes() || !actual.sha256().equals(ref.sha256())
                || !Path.of(actual.path()).equals(Path.of(ref.path()))) throw new IOException("Root software input differs from its exact descriptor");
        return read;
    }
    private static G2CallContextProducer.Unavailable unavailable(G2CallContextProducer.Reason reason, String detail) {
        return new G2CallContextProducer.Unavailable(reason, detail);
    }
}
