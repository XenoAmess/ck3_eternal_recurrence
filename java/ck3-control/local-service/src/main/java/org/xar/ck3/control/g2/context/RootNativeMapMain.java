package org.xar.ck3.control.g2.context;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.UUID;
import java.util.concurrent.atomic.AtomicReference;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.MapAdmissionCi;
import org.xar.ck3.control.build.MapAdmissionServiceOwner;
import org.xar.ck3.control.build.MapVerticalSoftwareHost;
import org.xar.ck3.control.build.RootNativePlanJson;
import org.xar.ck3.control.build.RootSoftwareChildBootstrap;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.CampaignMapAdmission;
import org.xar.ck3.control.contracts.CampaignMapComposeRequest;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.SavedFrame;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.runtime.closedadoption.ClosedAdoptionMain;
import org.xar.ck3.control.wave2.runtime.closedadoption.RootColdResumeSession;
import org.xar.ck3.control.wave2.runtime.closedadoption.OriginalColdConsumerSession;
import org.xar.ck3.control.wave2.runtime.closedadoption.RootNativeMapMaterializer;

/** Root's one concrete caller. Constructing/reading a plan performs no Game or MCP operation. */
public final class RootNativeMapMain {
    private static final String SCHEMA = "xar.root-native-map-prepared-call/v3";
    private static final String PREPARATION_SCHEMA = "xar.root-native-map-preparation-call/v1";
    private RootNativeMapMain() { }

    public record OwnerCommand(WindowsJobProcess.CommandSpec command, WindowsJobProcess.ConsoleMode consoleMode,
            ControlBuild.FileRef executableRef,
            int maxFrameBytes, long maxSentBytes, long maxReceivedBytes) {
        public OwnerCommand {
            Objects.requireNonNull(command); Objects.requireNonNull(consoleMode); Objects.requireNonNull(executableRef);
        }
        private WindowsJobProcess.OwnedStdioSpec bind(RootNativeRuntimeBinding runtime, Instant deadline) {
            return new WindowsJobProcess.OwnedStdioSpec(command, consoleMode, executableRef,
                    runtime.request().ownerProgramSources(), deadline, maxFrameBytes, maxSentBytes, maxReceivedBytes, runtime::verify);
        }
    }
    /** Static artifact inputs; dynamic quoted source refs are obtained only from the real session. */
    public record RuntimePlan(String machineId, Instant reviewAt, ControlBuild.FileRef nativeBuildResult,
            Path nativeSourceRoot, ControlBuild.FileRef gameExecutable, ControlBuild.FileRef launcherSettings,
            ControlBuild.FileRef nativeDll, ControlBuild.FileRef injector, ControlBuild.FileRef directBasePython,
            long maximumSourceBytes, RootNativeSoftwareQualification.Plan softwareQualification) {
        public RuntimePlan {
            StrictJson.text(machineId); Objects.requireNonNull(reviewAt); Objects.requireNonNull(nativeBuildResult);
            absolute(nativeSourceRoot); Objects.requireNonNull(gameExecutable); Objects.requireNonNull(launcherSettings);
            Objects.requireNonNull(nativeDll); Objects.requireNonNull(injector); Objects.requireNonNull(directBasePython);
            Objects.requireNonNull(softwareQualification);
        }
        private RootNativeRuntimeBinding.SavedMapRequest bind(RootColdResumeSession session,OwnerCommand owner) throws IOException {
            return new RootNativeRuntimeBinding.SavedMapRequest(machineId,reviewAt,nativeBuildResult,nativeSourceRoot,
                    gameExecutable,launcherSettings,nativeDll,injector,directBasePython,session.approvedProgramSources(),
                    owner.command().arguments(),maximumSourceBytes,softwareQualification);
        }
    }
    public record MapSoftware(MapVerticalSoftwareHost.Config host, MapAdmissionCi.Config consumers,
            ControlBuild.FileRef directFixture, ControlBuild.FileRef projectionFixture) {
        public MapSoftware { Objects.requireNonNull(host); Objects.requireNonNull(consumers);
            Objects.requireNonNull(directFixture); Objects.requireNonNull(projectionFixture); }
    }
    /** Explicit nullable wire field; Optional remains inside the actual authority model. */
    public record SourcePlanInput(String sessionId, String expectedEpisode, ExactRef launcherSettings,
            List<G2WindowsRootSources.RuntimeSource> runtimeSources, Path evidenceRoot,
            long executableBudget, long runtimeFileBudget) {
        public SourcePlanInput {
            runtimeSources = List.copyOf(runtimeSources);
            new RootNativePreloadAuthority.SourcePlan(sessionId, Optional.ofNullable(expectedEpisode),
                    launcherSettings, runtimeSources, evidenceRoot, executableBudget, runtimeFileBudget);
        }
        public RootNativePreloadAuthority.SourcePlan toSourcePlan() {
            return new RootNativePreloadAuthority.SourcePlan(sessionId, Optional.ofNullable(expectedEpisode),
                    launcherSettings, runtimeSources, evidenceRoot, executableBudget, runtimeFileBudget);
        }
    }
    public record Plan(String schema, String machineId, RootNativeMapCommands.PreparedInput prepared,
            RootSoftwareChildBootstrap.SdkLineageBinding sdkLineageBinding,
            RuntimePlan runtime, WindowsJobProcess.CommandSpec game, OwnerCommand owner,
            RootSteamOfflineGate.Plan steamOfflinePlan, Path injectorEvidenceRoot,
            Map<String,String> injectorEnvironment, long injectorMemoryBytes, Duration injectorTimeout,
            SourcePlanInput nativeSources, RootMcpWire.Handshake handshake,
            MapSoftware mapSoftware, Path evidenceRoot, Path rootMapReviewPath,
            String recordingSessionId, long rootSequence, Instant deadline) {
        public Plan {
            if (!SCHEMA.equals(schema)) throw new IllegalArgumentException("Root prepared map caller schema");
            StrictJson.text(machineId); Objects.requireNonNull(prepared); Objects.requireNonNull(sdkLineageBinding);
            Objects.requireNonNull(runtime); Objects.requireNonNull(game); Objects.requireNonNull(owner);
            Objects.requireNonNull(steamOfflinePlan); absolute(injectorEvidenceRoot); absolute(evidenceRoot);
            absolute(rootMapReviewPath); injectorEnvironment = Map.copyOf(injectorEnvironment);
            Objects.requireNonNull(injectorTimeout); Objects.requireNonNull(nativeSources);
            Objects.requireNonNull(handshake); Objects.requireNonNull(mapSoftware); Objects.requireNonNull(deadline);
            StrictJson.text(recordingSessionId); StrictJson.safe(rootSequence,1);
            if (!machineId.equals(runtime.machineId()) || !machineId.equals(steamOfflinePlan.machineId())
                    || deadline.isAfter(runtime.reviewAt()) || deadline.isAfter(steamOfflinePlan.deadline())
                    || injectorMemoryBytes < (64L << 20) || injectorTimeout.isZero() || injectorTimeout.isNegative()
                    || injectorTimeout.compareTo(Duration.ofSeconds(60)) > 0
                    || rootMapReviewPath.startsWith(evidenceRoot)) throw new IllegalArgumentException("Finite same-machine Root plan and independent review path required");
        }
    }
    public record PreparationCall(String schema, ControlBuild.FileRef mapPlanRef,
            RootNativeMapCommands.PreparationInput preparation, RootNativeMapMaterializer.Permit materialization) {
        public PreparationCall {
            if (!PREPARATION_SCHEMA.equals(schema)) throw new IllegalArgumentException("Root preparation caller schema");
            Objects.requireNonNull(mapPlanRef); Objects.requireNonNull(preparation); Objects.requireNonNull(materialization);
            if (!preparation.planRef().equals(materialization.planRef())
                    || !preparation.runtimeRoot().equals(materialization.runtimeRoot())
                    || !preparation.quoteOutput().equals(materialization.quoteOutput()))
                throw new IllegalArgumentException("One exact plan, runtime and quote for actual materialization required");
        }
    }
    /** Data written by Root after checking the actual challenge and visible first map. */
    public record MapReview(String schema, ControlBuild.FileRef challengeRef, CampaignMapComposeRequest request) {
        public MapReview {
            if (!"xar.root-native-map-visibility-review/v1".equals(schema)) throw new IllegalArgumentException("Actual Root map review schema");
            Objects.requireNonNull(challengeRef); Objects.requireNonNull(request);
        }
        public static MapReview fromBytes(byte[] raw) {
            var value=StrictJson.object(StrictJson.parse(raw),java.util.Set.of("schema","challenge_ref","request"));
            ExactRef ref=ExactRef.fromJson(value.get("challenge_ref"));
            return new MapReview(StrictJson.text(value.get("schema")),new ControlBuild.FileRef(ref.path(),ref.bytes(),ref.sha256()),
                    CampaignMapComposeRequest.fromJson(value.get("request")));
        }
        public byte[] toCanonicalBytes() {
            var value=StrictJson.object(); value.put("schema",schema); value.set("challenge_ref",exact(challengeRef).toJson());
            value.set("request",request.toJson()); return StrictJson.canonical(value);
        }
    }
    public record Receipt(String schema, String machineId, String observedAtUtc,
            ControlBuild.FileRef planRef, ControlBuild.FileRef rootSessionResult,
            ControlBuild.FileRef softwareMapProof, ControlBuild.FileRef originalOwnedRpc,
            ControlBuild.FileRef requestRef, ControlBuild.FileRef originalResponseRef,
            CampaignMapAdmission mapAdmission, RootNativeMapCommands.Completed commands) { }
    public record PreparationReceipt(ControlBuild.FileRef preparationCallRef, Receipt mapReceipt,
            RootNativeMapCommands.PreparationCompleted preparation) {
        public PreparationReceipt {
            Objects.requireNonNull(preparationCallRef); Objects.requireNonNull(mapReceipt); Objects.requireNonNull(preparation);
        }
    }
    private record Execution(Receipt receipt, Optional<RootNativeMapCommands.PreparationCompleted> preparation) { }

    /** Exact path/length/SHA triples for plan, original invocation and independent review plan. */
    public static void main(String[] args) throws IOException, InterruptedException {
        if (args.length != 9) throw new IllegalArgumentException("usage: RootNativeMapMain plan-path bytes sha invocation-path bytes sha review-plan-path bytes sha");
        ControlBuild.FileRef input = ref(args,0);
        if (PREPARATION_SCHEMA.equals(StrictJson.text(StrictJson.parse(bytes(input)).get("schema")))) {
            PreparationReceipt actual = runPreparation(input,ref(args,3),ref(args,6));
            System.out.println(new String(RootNativePlanJson.mapper().writeValueAsBytes(actual), java.nio.charset.StandardCharsets.UTF_8));
        } else {
            Receipt actual = runPrepared(input,ref(args,3),ref(args,6));
            System.out.println(new String(RootNativePlanJson.mapper().writeValueAsBytes(actual), java.nio.charset.StandardCharsets.UTF_8));
        }
    }

    public static Receipt runPrepared(ControlBuild.FileRef planRef, ControlBuild.FileRef invocationRef,
            ControlBuild.FileRef reviewPlanRef) throws IOException, InterruptedException {
        Plan plan = read(planRef, Plan.class);
        return execute(plan,planRef,invocationRef,reviewPlanRef,Optional.empty(),Optional.empty()).receipt();
    }

    public static PreparationReceipt runPreparation(ControlBuild.FileRef callRef, ControlBuild.FileRef invocationRef,
            ControlBuild.FileRef reviewPlanRef) throws IOException, InterruptedException {
        PreparationCall call = read(callRef,PreparationCall.class);
        Plan plan = read(call.mapPlanRef(),Plan.class);
        if (!call.preparation().expectedPrepared().equals(plan.prepared())
                || !call.materialization().machineId().equals(plan.machineId())
                || !call.materialization().deadline().equals(plan.deadline()))
            throw new IOException("Preparation caller differs from the exact reviewed map tuple or deadline");
        verifyPreparation(callRef,call);
        Execution actual = execute(plan,call.mapPlanRef(),invocationRef,reviewPlanRef,Optional.of(call),Optional.of(callRef));
        return new PreparationReceipt(callRef,actual.receipt(),actual.preparation().orElseThrow(
                () -> new IOException("Actual preparation commands did not complete")));
    }

    private static Execution execute(Plan plan, ControlBuild.FileRef planRef, ControlBuild.FileRef invocationRef,
            ControlBuild.FileRef reviewPlanRef, Optional<PreparationCall> preparation,
            Optional<ControlBuild.FileRef> preparationRef) throws IOException, InterruptedException {
        if (!WindowsJobProcess.currentMachineId().equals(plan.machineId()) || !Instant.now().isBefore(plan.deadline()))
            throw new IOException("Actual machine and unexpired Root plan required before any host/session creation");
        ClosedAdoptionMain.Invocation invocation = ClosedAdoptionMain.Invocation.decode(bytes(invocationRef));
        if (!plan.machineId().equals(invocation.machine()) || plan.deadline().isAfter(invocation.deadline()))
            throw new IOException("Original Root invocation differs from this prepared caller");
        Path consumerDirectory = invocation.output().resolve("root-consumer-session");
        if (preparation.isPresent()) {
            var input=preparation.orElseThrow().preparation();
            if (!input.metadataRoot().equals(invocation.output().resolve("preparation-metadata"))
                    || !input.fixtureRoot().equals(invocation.output().resolve("preparation-historical-fixture")))
                throw new IOException("Preparation roots must be the original Root invocation's owned children");
            if (Files.exists(input.metadataRoot(), java.nio.file.LinkOption.NOFOLLOW_LINKS)
                    || Files.exists(input.fixtureRoot(), java.nio.file.LinkOption.NOFOLLOW_LINKS))
                throw new IOException("Preparation metadata and historical fixture must remain fresh");
        }
        absolute(consumerDirectory); reviewPlanRef.verify();
        if (Files.exists(consumerDirectory) || Files.exists(plan.evidenceRoot()) || Files.exists(plan.rootMapReviewPath()))
            throw new IOException("Fresh Root evidence, command directory and map review are required; no reuse");
        SharedSourceFiles.plainAncestors(plan.evidenceRoot().getParent()); Files.createDirectory(plan.evidenceRoot());
        AtomicReference<RootNativeMapCommands.Completed> commands = new AtomicReference<>();
        AtomicReference<RootNativeMapCommands.PreparationCompleted> preparationCommands = new AtomicReference<>();
        AtomicReference<Throwable> commandFailure = new AtomicReference<>();
        AtomicReference<NativeMap> observed = new AtomicReference<>();
        var software=RootNativeSoftwareQualification.run(plan.runtime().softwareQualification());
        try (MapVerticalSoftwareHost.Session host = MapVerticalSoftwareHost.open(plan.mapSoftware().host())) {
            var direct = host.post(MapAdmissionServiceOwner.COMPOSE_PATH, plan.mapSoftware().directFixture());
            var projection = host.post("/v1/projections/call", plan.mapSoftware().projectionFixture());
            var qualified = host.qualify(plan.mapSoftware().consumers(), direct, projection);
            Thread producer = new Thread(() -> {
                try {
                    if (preparation.isPresent()) {
                        var complete=RootNativeMapCommands.runPreparation(consumerDirectory,plan.machineId(),
                                preparation.orElseThrow().preparation(),plan.deadline());
                        preparationCommands.set(complete); commands.set(complete.completed());
                    } else commands.set(RootNativeMapCommands.run(consumerDirectory, plan.machineId(), plan.prepared(), plan.deadline()));
                }
                catch (IOException | InterruptedException | RuntimeException failure) {
                    if (failure instanceof InterruptedException) Thread.currentThread().interrupt();
                    commandFailure.set(failure);
                }
            }, "root-native-map-commands");
            producer.setDaemon(true); producer.start();
            try {
                RootColdResumeSession.Workflow continuation = new RootColdResumeSession.Workflow() {
                    @Override public void run(RootColdResumeSession session) throws IOException,InterruptedException {
                        observed.set(runWorkflow(plan,planRef,session,host,qualified,software));
                    }
                    @Override public RootNativeMapMaterializer.JunctionScope materialize(OriginalColdConsumerSession.ComposedBundle bundle) throws IOException {
                        throw new IOException("Prepared-only caller cannot materialize; an exact PreparationCall is required");
                    }
                };
                RootColdResumeSession.Workflow workflow = continuation;
                if (preparation.isPresent()) {
                    PreparationCall call=preparation.orElseThrow(); ControlBuild.FileRef callRef=preparationRef.orElseThrow();
                    var materializer=new RootNativeMapMaterializer(call.materialization(),continuation,() -> {
                        try { verifyPreparation(callRef,call); }
                        catch (IOException failed) { throw new UncheckedIOException(failed); }
                    });
                    workflow=new RootColdResumeSession.Workflow() {
                        @Override public void run(RootColdResumeSession session) throws IOException,InterruptedException {
                            materializer.run(session);
                        }
                        @Override public RootNativeMapMaterializer.JunctionScope materialize(OriginalColdConsumerSession.ComposedBundle bundle) throws IOException {
                            verifyPreparation(callRef,call);
                            Path metadata=call.preparation().metadataRoot();
                            SharedSourceFiles.plainAncestors(metadata.getParent());
                            Files.createDirectory(metadata);
                            return materializer.materialize(bundle);
                        }
                    };
                }
                var original = ClosedAdoptionMain.runRootColdSession(exact(invocationRef), exact(reviewPlanRef),
                        plan.sdkLineageBinding(),workflow);
                producer.join(Math.max(1, Math.min(5000, Duration.between(Instant.now(), plan.deadline()).toMillis())));
                if (producer.isAlive() || commandFailure.get() != null || commands.get() == null || observed.get() == null)
                    throw new IOException("Root cold caller did not complete all actual ordered stages; no credit or replay", commandFailure.get());
                NativeMap actual = observed.get(); qualified.verifyCurrent();
                Receipt receipt=new Receipt("xar.root-native-map-first-receipt/v1", plan.machineId(), Instant.now().toString(),
                        planRef, new ControlBuild.FileRef(original.reference().path(), original.reference().bytes(), original.reference().sha256()),
                        qualified.proofRef(), actual.rpc(), actual.request(), actual.response(), actual.admission(), commands.get());
                return new Execution(receipt,Optional.ofNullable(preparationCommands.get()));
            } finally { producer.interrupt(); producer.join(1000); }
        }
    }

    private record NativeMap(ControlBuild.FileRef rpc, ControlBuild.FileRef request,
            ControlBuild.FileRef response, CampaignMapAdmission admission) { }
    private static NativeMap runWorkflow(Plan plan, ControlBuild.FileRef planRef, RootColdResumeSession session,
            MapVerticalSoftwareHost.Session host, MapVerticalSoftwareHost.MapVerticalSoftwareResult qualified,
            RootNativeSoftwareQualification.Qualified software)
            throws IOException, InterruptedException {
        planRef.verify(); qualified.verifyCurrent();
        RootNativeRuntimeBinding runtime = RootNativeRuntimeBinding.acceptSavedMap(plan.runtime().bind(session,plan.owner()), session,software,qualified);
        RootColdResumeSession.ColdPlan cold = new RootColdResumeSession.ColdPlan(runtime, plan.game(),
                plan.steamOfflinePlan(), plan.injectorEvidenceRoot(), plan.injectorEnvironment(),
                plan.injectorMemoryBytes(), plan.injectorTimeout(), plan.deadline());
        var started = RootNativeMapLaunch.launchAndOpen(session, cold, plan.owner().bind(runtime, plan.deadline()),
                plan.nativeSources().toSourcePlan(), plan.handshake(), plan.deadline());
        var observation = started.requireNativeSession().observe(plan.rootSequence(), plan.deadline());
        if (!(observation instanceof RootMcpSemanticClient.NativeObservation actual))
            throw new IOException("First semantic call has no actual private Native completion; UNKNOWN is not replayed");
        byte[] rpc = actual.completion().originalRpcLine().bytes();
        ControlBuild.FileRef originalRpc = publish(plan.evidenceRoot().resolve("first-native-rpc.json"), rpc);
        JsonNode row = StrictJson.parse(actual.completion().ownerRow().bytes().bytes(), RootMcpEnvelope.OWNER_ROW_MAX_BYTES);
        JsonNode snapshot = row.path("result").path("structured_content");
        SavedFrame frame = frame(snapshot);
        var identity = started.game().identity();
        GameGeneration game = new GameGeneration(identity.pid(), new PythonOnlyUInt64(new BigInteger(identity.creationFiletimeDecimal())));
        var challenge = StrictJson.object(); challenge.put("schema", "xar.root-native-map-visibility-challenge/v1");
        challenge.put("machine_id", plan.machineId()); challenge.put("nonce", UUID.randomUUID().toString());
        challenge.set("native_rpc_ref", exact(originalRpc).toJson()); challenge.set("game", game.toJson());
        challenge.set("actual_frame", frame.toJson()); challenge.put("recording_session_id", plan.recordingSessionId());
        ControlBuild.FileRef challengeRef = publish(plan.evidenceRoot().resolve("map-review-challenge.json"), StrictJson.canonical(challenge));
        while (!Files.exists(plan.rootMapReviewPath(), java.nio.file.LinkOption.NOFOLLOW_LINKS)) {
            if (!Instant.now().isBefore(plan.deadline())) throw new IOException("Root map visibility review deadline; no fabricated visible facts");
            started.game().verify(); qualified.verifyCurrent(); Thread.sleep(50);
        }
        MapReview review = MapReview.fromBytes(bytes(ControlBuild.FileRef.measure(plan.rootMapReviewPath())));
        CampaignMapComposeRequest request = review.request();
        if (!challengeRef.equals(review.challengeRef()) || !request.machineId().equals(plan.machineId())
                || !request.nativeLaunch().equals(game) || !request.actualInitialFrame().equals(frame)
                || !request.recordingSessionId().equals(plan.recordingSessionId()))
            throw new IOException("Root map review does not match the actual retained Native frame/Game");
        qualified.verifyCurrent(); started.game().verify();
        ControlBuild.FileRef requestRef = publish(plan.evidenceRoot().resolve("actual-map-request.json"), request.toCanonicalBytes());
        var exchange = host.post(MapAdmissionServiceOwner.COMPOSE_PATH, requestRef);
        byte[] response = exchange.responseBytes();
        if (response.length < 1 || response.length > 16_384) throw new IOException("Bounded original map receipt required");
        CampaignMapAdmission receipt = CampaignMapAdmission.fromJson(StrictJson.parse(response));
        CampaignMapAdmission expected = new CampaignMapAdmission(request.machineId(), game, request.recordingSessionId(), frame, request.observedAtUtc());
        if (!receipt.equals(expected)) throw new IOException("Actual HTTP map producer changed the original admitted tuple");
        return new NativeMap(originalRpc, requestRef, exchange.observation().responseRef(), receipt);
    }
    private static SavedFrame frame(JsonNode snapshot) {
        return new SavedFrame(StrictJson.text(snapshot.get("snapshot_id")),
                StrictJson.integer(snapshot.get("revision"),1,StrictJson.MAX_SAFE_INTEGER),
                StrictJson.integer(snapshot.get("native_revision"),1,StrictJson.MAX_SAFE_INTEGER),
                StrictJson.integer(snapshot.get("date_raw"),0,StrictJson.MAX_SAFE_INTEGER),
                StrictJson.integer(snapshot.path("played_character").get("character_id"),1,StrictJson.MAX_SAFE_INTEGER),
                StrictJson.text(snapshot.get("episode_run_id")));
    }
    private static byte[] bytes(ControlBuild.FileRef ref) throws IOException {
        ref.verify(); if (ref.bytes() < 1 || ref.bytes() > 1_048_576) throw new IOException("Bounded exact caller document required");
        byte[] raw = Files.readAllBytes(Path.of(ref.path())); ref.verify(); return raw;
    }
    private static <T> T read(ControlBuild.FileRef ref, Class<T> type) throws IOException {
        return RootNativePlanJson.mapper().readValue(bytes(ref), type);
    }
    private static void verifyPreparation(ControlBuild.FileRef callRef, PreparationCall call) throws IOException {
        callRef.verify(); call.mapPlanRef().verify();
        ExactRef storage=call.materialization().storageEvidence();
        new ControlBuild.FileRef(storage.path(),storage.bytes(),storage.sha256()).verify();
        if (!Instant.now().isBefore(call.materialization().deadline()))
            throw new IOException("Original finite materialization permit expired");
    }
    private static ControlBuild.FileRef publish(Path path, byte[] bytes) throws IOException {
        Files.write(path,bytes,StandardOpenOption.CREATE_NEW); return ControlBuild.FileRef.measure(path);
    }
    private static ExactRef exact(ControlBuild.FileRef ref) { return new ExactRef(ref.path(),ref.bytes(),ref.sha256()); }
    private static ControlBuild.FileRef ref(String[] args,int offset) {
        return new ControlBuild.FileRef(args[offset],Long.parseLong(args[offset+1]),args[offset+2]);
    }
    private static void absolute(Path path) {
        Objects.requireNonNull(path);
        if (!path.isAbsolute() || !path.normalize().equals(path)) throw new IllegalArgumentException("Normalized absolute caller path required");
    }
}

