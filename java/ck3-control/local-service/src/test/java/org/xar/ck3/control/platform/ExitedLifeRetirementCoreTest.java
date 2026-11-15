package org.xar.ck3.control.platform;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.TreeMap;
import java.util.UUID;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.advance.*;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.build.runtime.HostMode;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Frame;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.ProposalFrame;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import org.xar.ck3.control.service.root.RootApplicationAssembly;
import org.xar.ck3.control.service.root.RootApplicationConfiguration;

/** Actual Core/writer rejects canonical records whose old guard references are placeholders.
 * A real exited ordinary process grants no exemption from original packet custody.
 * The real production positive retirement is verified separately; no CK3, Steam or Native is started here. */
final class ExitedLifeRetirementCoreTest {
    @TempDir Path temporary;

    @Test void uninstalledCoreRejectsPlaceholderGuardOriginalsWithoutRetiringOrLaunching() throws Exception {
        try (var subject = exited()) {
            var lifecycle = new JavaGameLifecycle(List.of());
            var generation = ManagedGameSession.generation(subject.terminal().identity());
            var exited = lifecycle.qualifyExitedOwner(subject.owner(), generation, subject.plan(), subject.plan().deadline());
            assertTrue(lifecycle.currentSession().isEmpty());
            var inputs = history(exited, subject.plan());
            long nativeEvents;
            try (var files = Files.list(subject.plan().evidenceRoot())) { nativeEvents = files.count(); }
            var source = new CompositeOperatorQuarantineSource(inputs.request(), inputs.requestBytes(), inputs.authorization(),
                    exited.generation(), exited.sourceSessionId(), new OperationKey("life-advance"), LifeAdvanceComposite.HANDLER, Clock.systemUTC());
            try (var core = RootApplicationAssembly.open(inputs.configuration(), Clock.systemUTC(), List.of(), Optional.empty(), inputs.storage())) {
                core.bindOperatorQuarantineSource(source);
                byte[] originalLedger = Files.readAllBytes(inputs.configuration().ledger().snapshot());
                var rejected = assertThrows(java.io.UncheckedIOException.class,
                        () -> core.retireExitedLifeInterruptionOnly(lifecycle, exited, exited.deadline()));
                assertEquals("same-writer original packet unavailable", rejected.getMessage());
                core.writer().locked(same -> {
                    assertEquals(inputs.sequence(), same.head().state().sequence());
                    assertEquals(0, same.head().state().settledCycles());
                    assertEquals(BigInteger.valueOf(53288256), BigInteger.valueOf(same.head().state().settledDateRaw()));
                    return null;
                });
                assertArrayEquals(originalLedger, Files.readAllBytes(inputs.configuration().ledger().snapshot()));
                assertTrue(lifecycle.currentSession().isEmpty(), "administrative Core must not attach or launch a replacement");
                try (var files = Files.list(subject.plan().evidenceRoot())) { assertEquals(nativeEvents, files.count()); }
            }
            assertTrue(lifecycle.currentSession().isEmpty());
        }
    }

    private record Inputs(RootApplicationConfiguration configuration, StorageWriteGuard storage, ActionReceipt original,
            List<ActionReceipt> children, long sequence, ExactRef request, byte[] requestBytes, byte[] authorization) { }

    /** Uses the actual reducer, physical archive and WAL; only historical software packet production is controlled. */
    private Inputs history(JavaGameLifecycle.ExitedGeneration exited, NativeLaunchPlan nativePlan) throws Exception {
        Path root = Files.createDirectory(temporary.resolve("writer"));
        Path sourceFile = root.resolve("reviewed-source.txt"); Files.writeString(sourceFile, "offline rejected-action producer; no Native endpoint");
        ExactRef reviewed = exact(sourceFile);
        var seed = StrictJson.object(); seed.put("schema", "root.ck3.continuity-window/v1"); seed.put("machine_id", exited.machineId());
        seed.put("sequence", 0); seed.put("window_id", 1); seed.put("status", "running"); seed.put("target_days", 1);
        seed.put("start_date_raw", 53288256); seed.put("target_date_raw", 53288280); seed.put("last_settled_date_raw", 53288256); seed.put("last_settled_cycles", 0);
        byte[] initial = ContinuityJson.canonical(seed);
        Path snapshot = root.resolve("ROOT-CONTINUITY-WINDOW.json"), anchor = root.resolve("anchor.json");
        Files.write(snapshot, initial); Files.write(anchor, initial); Files.write(root.resolve("ROOT-CONTINUITY-WINDOW.lock"), new byte[0]);
        Files.createDirectory(root.resolve("ROOT-CONTINUITY-WINDOW-EVENTS")); Path artifactRoot = Files.createDirectory(root.resolve("artifacts"));
        var layout = new WriterContracts.Layout(snapshot, exact(anchor), exited.machineId());
        var storage = StorageWriteGuardTestSupport.create(layout);
        var artifacts = new ImmutableArtifactStore(new ImmutableArtifactStore.Config(artifactRoot, layout.lock(), 16L << 20), storage);
        var authority = new AtomicReference<ActionContinuityAuthority>();
        var writer = new ContinuityWriter(layout, List.of(reviewed), new WriterContracts.TransitionAuthority() {
            @Override public String revalidate(ContinuityState ignored, WriterContracts.Request request) { throw new AssertionError("locked Head required"); }
            @Override public String revalidate(WriterContracts.Head head, WriterContracts.Request request) { return authority.get().revalidate(head, request); }
            @Override public ContinuityState reduce(ContinuityState state, WriterContracts.Request request) { return authority.get().reduce(state, request); }
        }, Clock.systemUTC(), new ContinuityWriter.Extensions(List.of(), Optional.of(artifacts), Optional.empty()), storage);
        var archive = new NativeOutcomeArchive(artifacts, writer); var journal = new ContinuityActionJournal(writer, archive);
        authority.set(new ActionContinuityAuthority("software-original-writer", archive,
                (head, command) -> { throw new AssertionError("history construction never requests gameplay readiness"); },
                (head, receipt) -> assertFalse(receipt.visibleGameplay()), Clock.systemUTC()));
        Instant now = Instant.now(), deadline = nativePlan.deadline();
        var source = new G2Source(exited.machineId(), now.toString(), "software-unsubmitted", reviewed);
        var before = new ObservationIdentity(exited.machineId(), exited.generation(), new ProposalFrame(
                new Frame(BigInteger.valueOf(29829), BigInteger.ONE, BigInteger.valueOf(53288256)), "software-before", BigInteger.ONE, exited.sourceSessionId()), 1);
        var plan = new AdvancePlan(BigInteger.valueOf(53288256), BigInteger.valueOf(53288280), 1, 1,
                "software-retained-initialization", true, AdvancePlan.ClockMode.EXACT_SENTINEL, Optional.empty());
        var parent = new ActionCommand("software-retained-life", before, source, exited.sourceSessionId(), new OperationKey("life-advance"),
                new Obj(Map.of(AdvancePlan.KEY, plan.json())), new ExpectedPostcondition(1, before, source, AdvancePlan.OBSERVER, plan.expected()),
                new Claims(Set.of(), Set.of(), Set.of(), Set.of()), deadline);
        var guard = new GuardEvidence(before, source, exited.sourceSessionId(), BigInteger.ONE, parent.operation(), reviewed, reviewed,
                "software-original-writer", now, deadline);
        var children = new ArrayList<ActionReceipt>(); var bindings = new ArrayList<CompositeExecution.Child>();
        journal.locked(locked -> locked.append(parent, ActionCodec.bodySha256(parent), new ActionState.IntentDurable()));
        journal.locked(locked -> locked.append(parent, ActionCodec.bodySha256(parent),
                new ActionState.CompositeRunning(new CompositeExecution(LifeAdvanceComposite.HANDLER, now, guard, List.of()))));
        for (String step : List.of(plan.armStep(), ClockStatusRead.CANCEL_PREFIX + "37")) {
            var operation = new OperationKey(step); var arguments = new Obj(Map.of());
            var child = new ActionCommand(ActionIds.child(parent.actionId(), bindings.size() + 1, operation), before, source, parent.sessionId(),
                    operation, arguments, AdvancePrimitives.expected(before, source, operation, arguments), parent.claims(), deadline);
            bindings.add(new CompositeExecution.Child(child.actionId(), ActionCodec.bodySha256(child)));
            var execution = new CompositeExecution(LifeAdvanceComposite.HANDLER, now, guard, List.copyOf(bindings));
            journal.locked(locked -> locked.append(parent, ActionCodec.bodySha256(parent), new ActionState.CompositeRunning(execution)));
            journal.locked(locked -> locked.append(child, ActionCodec.bodySha256(child), new ActionState.IntentDurable()));
            var prepared = AdvancePrimitives.prepareRequest(child); archive.preserveRequest(prepared);
            var childGuard = new GuardEvidence(before, source, parent.sessionId(), BigInteger.ONE, operation, reviewed, reviewed,
                    "software-original-writer", now, deadline);
            var attempt = new ActionState.Attempt("unsubmitted-" + bindings.size(), now, childGuard, prepared);
            var dispatch = new NativeActionPort.RejectedBeforeDispatch(attempt.requestId(), new NativeActionPort.ZeroDispatchProof(
                    NativeActionPort.ZeroDispatchStage.BEFORE_WRITE, 0, "controlled original without any Native write", Optional.empty()));
            archive.preserve(dispatch);
            children.add(journal.locked(locked -> locked.append(child, ActionCodec.bodySha256(child), new ActionState.RejectedBeforeDispatch(attempt, dispatch))));
        }
        var execution = new CompositeExecution(LifeAdvanceComposite.HANDLER, now, guard, List.copyOf(bindings));
        var original = journal.locked(locked -> locked.append(parent, ActionCodec.bodySha256(parent),
                new ActionState.CompositeUnknown(execution, "actual original operator interruption", List.of(reviewed))));
        return writer.locked(same -> {
            var scoped = archive.withSession(same);
            byte[] authorization = "{\"decision\":\"retire software original UNKNOWN effects after source-proven exit\"}".getBytes(java.nio.charset.StandardCharsets.UTF_8);
            ExactRef authorizationRef = scoped.preserveMaterial(new RawJson(authorization));
            ObjectNode request = StrictJson.object(); request.put("schema", CompositeOperatorQuarantineRequest.LIFE_SCHEMA);
            request.set("authorized_by", authorizationRef.toJson()); request.put("machine_id", exited.machineId()); request.set("game", exited.generation().toJson());
            request.put("episode_run_id", exited.sourceSessionId()); request.put("parent_action_id", parent.actionId()); request.put("parent_body_sha256", original.bodySha256());
            request.set("original_receipt_ref", scoped.receiptReferenceOf(original).toJson()); request.put("expected_head_sequence", same.head().state().sequence());
            request.put("expected_head_digest", same.head().digest()); var rows = request.putArray("children");
            for (int i = 0; i < children.size(); i++) { var row = rows.addObject(); row.put("ordinal", i + 1); row.put("action_id", children.get(i).command().actionId()); row.put("body_sha256", children.get(i).bodySha256()); }
            request.put("scope", CompositeOperatorQuarantineRequest.LIFE_SCOPE); request.put("issued_at_utc", now.toString());
            request.put("observation_deadline_utc", deadline.toString()); request.putArray("prior_requests");
            byte[] raw = StrictJson.canonical(request); ExactRef requestRef = scoped.preserveMaterial(new RawJson(raw));
            Path launchData = root.resolve("native-plan.json"); Files.write(launchData, StrictJson.canonical(NativeLaunchPlanCodec.toJson(NativeLaunchPlanCodec.describe(nativePlan)), RootApplicationConfiguration.MAXIMUM_BYTES));
            var configuration = new RootApplicationConfiguration(exited.machineId(), HostMode.COMPLETE_MIGRATION, deadline, exact(launchData),
                    layout, List.of(reviewed), artifactRoot, 16L << 20);
            return new Inputs(configuration, storage, original, List.copyOf(children), same.head().state().sequence(), requestRef, raw, authorization);
        });
    }

    private record Subject(WindowsJobProcess process, NativeLaunchPlan plan, Path owner, WindowsJobProcess.CommandResult terminal) implements AutoCloseable {
        @Override public void close() { process.close(); }
    }
    private Subject exited() throws Exception {
        Path peer = temporary.resolve("ordinary-exited-peer-" + UUID.randomUUID() + ".exe");
        Files.copy(Path.of(System.getenv("SystemRoot"), "System32", "ping.exe"), peer);
        var environment = new TreeMap<String, String>(String.CASE_INSENSITIVE_ORDER); environment.putAll(System.getenv());
        for (String name : List.of("JAVA_TOOL_OPTIONS", "_JAVA_OPTIONS", "JDK_JAVA_OPTIONS")) environment.remove(name);
        var process = WindowsJobProcess.start(new WindowsJobProcess.CommandSpec(peer, List.of("127.0.0.1", "-n", "30"),
                temporary, environment, temporary.resolve("peer.stdout"), temporary.resolve("peer.stderr"), 128L << 20));
        try {
            exitOwnPeer259(process.identity());
            var terminal = process.await(Duration.ofSeconds(5), Instant.now().plusSeconds(7), () -> { });
            assertEquals(259, terminal.exitCode(), () -> "software peer stderr: " + readPeerError()); assertEquals(0, terminal.accounting().activeProcesses());
            String machine = WindowsJobProcess.currentMachineId(); Instant deadline = Instant.now().plusSeconds(180);
            var inputs = new NativeLaunchEvidence.Inputs(file("environment.json", "software environment"), file("build.json", "software build"), file("registration.json", "software registration"));
            var review = new LaunchSourceBinding.Review(machine, deadline, ControlBuild.FileRef.measure(peer), file("unused.dll", "never loaded"),
                    file("unused-injector.exe", "never executed"), inputs, temporary, List.of(file("source.txt", "software source")));
            Path profile = Files.createDirectory(temporary.resolve("profile")); Files.createDirectories(profile.resolve("save games"));
            Path saved = profile.resolve("save games/checkpoint.ck3"); Files.writeString(saved, "software checkpoint never loaded");
            Path state = Files.createDirectory(temporary.resolve("state")), events = Files.createDirectory(temporary.resolve("events"));
            var plan = new NativeLaunchPlan("software-launch", "software-session", LaunchSourceBinding.accept(review), profile, state, events,
                    "\\\\.\\pipe\\exited-core-" + UUID.randomUUID(), "software-bridge", "software-adapter", new NativeLaunchPlan.SavedGame("checkpoint", ControlBuild.FileRef.measure(saved)),
                    false, NativeLaunchPlan.WindowPolicy.MINIMIZED_NO_ACTIVATE, Map.of(), 128L << 20, 32L << 20, deadline,
                    Duration.ofSeconds(2), Duration.ofSeconds(3), new SteamOfflineProbe.Plan(machine, file("steam.exe", "never run"), deadline), NativeLaunchPlan.PreparedProfile.vanilla(), 64);
            var evidence = new LifecycleEvidence(plan);
            var launch = evidence.write(LifecycleEvidence.Event.HELLO, terminal.identity(), terminal.accounting(), null, null, "software protocol fixture, no Native handshake");
            var exit = evidence.write(LifecycleEvidence.Event.STOPPED, terminal.identity(), terminal.accounting(), terminal, GameLifecycle.TerminalKind.NATURAL_EXIT, "actual ordinary process signaled and Job0");
            Path hello = temporary.resolve("software-hello.packet"); Files.writeString(hello, "software packet, not a Native handshake");
            Path ownerDirectory = Files.createDirectory(temporary.resolve("owner")), owner = ownerDirectory.resolve("owner.json");
            WindowsJobProcess.ProcessIdentity supervisor;
            try (var handle = WindowsJobProcess.retainReadOnlyProcess(ProcessHandle.current().pid())) { supervisor = handle.identity(); }
            GameSupervisorControl.writeDescriptor(owner, new GameSupervisorControl.Descriptor(machine, plan.sessionId(), supervisor, terminal.identity(),
                    NativeLaunchPlanCodec.describe(plan), exact(hello), launch, ownerDirectory.resolve("stop-request.json"), ownerDirectory.resolve("terminal.json")));
            GameSupervisorControl.publish(ownerDirectory.resolve("terminal.json"), GameSupervisor.encodeTerminal(machine, plan.sessionId(), terminal.identity(),
                    new GameSupervisor.Completed("", new GameSupervisor.Terminal(terminal, true, GameLifecycle.TerminalKind.NATURAL_EXIT, Optional.of(exit)))), false);
            return new Subject(process, plan, owner, terminal);
        } catch (Exception failure) { process.close(); throw failure; }
    }
    private static void exitOwnPeer259(WindowsJobProcess.ProcessIdentity own) throws IOException {
        var api = com.sun.jna.platform.win32.Kernel32.INSTANCE;
        var handle = api.OpenProcess(0x00101001, false, (int) own.pid());
        if (handle == null) throw new IOException("own software peer open failed: " + com.sun.jna.Native.getLastError());
        try {
            var birth = new com.sun.jna.platform.win32.WinBase.FILETIME(); var exit = new com.sun.jna.platform.win32.WinBase.FILETIME();
            if (!api.GetProcessTimes(handle, birth, exit, new com.sun.jna.platform.win32.WinBase.FILETIME(), new com.sun.jna.platform.win32.WinBase.FILETIME()))
                throw new IOException("own software peer time failed: " + com.sun.jna.Native.getLastError());
            String actual = BigInteger.valueOf(Integer.toUnsignedLong(birth.dwHighDateTime)).shiftLeft(32)
                    .add(BigInteger.valueOf(Integer.toUnsignedLong(birth.dwLowDateTime))).toString();
            if (!actual.equals(own.creationFiletimeDecimal()) || api.WaitForSingleObject(handle, 0) != 258)
                throw new IOException("own software peer birth/running identity changed");
            if (!api.TerminateProcess(handle, 259)) throw new IOException("own software peer exit259 failed: " + com.sun.jna.Native.getLastError());
        } finally { if (!api.CloseHandle(handle)) throw new IOException("own software peer handle close failed"); }
    }
    private String readPeerError() { try { byte[] raw = Files.readAllBytes(temporary.resolve("peer.stderr")); return "raw=" + java.util.HexFormat.of().formatHex(raw) + " decoded=" + new String(raw, java.nio.charset.Charset.forName("GB18030")); } catch (IOException unavailable) { return unavailable.toString(); } }
    private ControlBuild.FileRef file(String name, String content) throws IOException { Path path = temporary.resolve(name); Files.writeString(path, content); return ControlBuild.FileRef.measure(path); }
    private static ExactRef exact(Path path) throws IOException { var file = ControlBuild.FileRef.measure(path); return LifecycleEvidence.exact(file); }
}
