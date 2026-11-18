package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.io.PrintWriter;
import java.io.Writer;
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Duration;
import java.time.Instant;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.NativeObservationPort;
import org.xar.ck3.control.application.action.NativeRequestChronology;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.NativeFreshSnapshotPort;
import org.xar.ck3.control.nativebridge.CoreClockControl;
import org.xar.ck3.control.application.action.FullSnapshotClockControl;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.nativebridge.FullSnapshotClockControlResult;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;
import org.xar.ck3.control.nativebridge.capabilities.registry.PersonalGoldFrame;
import org.xar.ck3.control.nativebridge.capabilities.registry.PersonalGoldFramePublicCodec;
import org.xar.ck3.control.nativebridge.capabilities.registry.ActorFoundationFrame;
import org.xar.ck3.control.nativebridge.capabilities.registry.ActorFoundationFramePublicCodec;
import org.xar.ck3.control.platform.GameSupervisorControl;
import org.xar.ck3.control.platform.ManagedGameSession;
import org.xar.ck3.control.platform.NativeGameAttachment;
import org.xar.ck3.control.platform.NativeLaunchPlan;

/** One actual independent Native READ. The archived result grants no business or Game ownership. */
public final class NativeOwnerSnapshotMain268 {
    private static final int SMALL = 1 << 20;
    private static String stage = "ARGUMENTS";
    private static Path createdOutput;
    private NativeOwnerSnapshotMain268() { }

    public static void main(String[] args) {
        try {
            if (args.length != 3) throw new IOException("expected descriptorPath configPath freshOutputDirectory");
            run(Path.of(args[0]).toAbsolutePath().normalize(), Path.of(args[1]).toAbsolutePath().normalize(),
                    Path.of(args[2]).toAbsolutePath().normalize());
        } catch (Exception | LinkageError failure) {
            if (failure instanceof InterruptedException) Thread.currentThread().interrupt();
            ObjectNode diagnostic = StrictJson.object().put("schema", "xar.native-owner-snapshot-failure/v1")
                    .put("status", "FAILED").put("stage", stage).put("at_utc", Instant.now().toString())
                    .put("exception", failure.getClass().getName()).put("message", bounded(failure.getMessage(), 4096));
            if (createdOutput != null) try { write(createdOutput, "failure.json", FullJsonTree.encode(diagnostic, SMALL)); }
            catch (IOException | RuntimeException saving) { failure.addSuppressed(saving); }
            System.err.println(diagnostic);
            printBounded(failure);
            System.exit(1);
        }
    }

    private static void run(Path descriptorPath, Path configPath, Path output) throws IOException, InterruptedException {
        stage = "INPUTS";
        byte[] configBytes = readBounded(configPath, SMALL);
        ObjectNode config = StrictJson.object(StrictJson.parse(configBytes, SMALL), Set.of("schema", "owner_descriptor",
                "overall_timeout_seconds", "read_timeout_seconds", "maximum_frames_per_operation"), Set.of("core_prefix_only", "mode", "control_step"));
        ObservationMode observationMode=observationMode(config);
        boolean applicationExit=observationMode==ObservationMode.CORE_EXIT;
        boolean personalGold=observationMode==ObservationMode.PERSONAL_GOLD;
        boolean actorFoundation=observationMode==ObservationMode.ACTOR_FOUNDATION;
        boolean fullClock=observationMode==ObservationMode.FULL_CLOCK;
        String fullClockStep=fullClock?StrictJson.text(config.get("control_step")):null;
        CoreClockControl.Step controlStep=observationMode==ObservationMode.CORE_CONTROL
                ?CoreClockControl.Step.fromWire(StrictJson.text(config.get("control_step"))):null;
        boolean coreCommand=applicationExit||controlStep!=null;
        ExactRef expectedDescriptor = ExactRef.fromJson(config.get("owner_descriptor"));
        StrictJson.require(Path.of(expectedDescriptor.path()).toAbsolutePath().normalize().equals(descriptorPath), "descriptor path differs from explicit config");
        long overall = StrictJson.integer(config.get("overall_timeout_seconds"), 1, 600);
        long readSeconds = StrictJson.integer(config.get("read_timeout_seconds"), 1, 60);
        int frames = Math.toIntExact(StrictJson.integer(config.get("maximum_frames_per_operation"), 1, 65536));
        boolean corePrefixOnly=observationMode!=ObservationMode.SAVED_FULL;
        Instant entered = Instant.now(), deadline = entered.plusSeconds(overall);
        byte[] descriptorBytes = readExact(expectedDescriptor, GameSupervisorControl.MAXIMUM_DESCRIPTOR_BYTES);
        SharedSourceFiles.Witness descriptorWitness = SharedSourceFiles.observe(descriptorPath);
        requireWitnessBytes(descriptorWitness, expectedDescriptor);
        GameSupervisorControl.Descriptor owner = GameSupervisorControl.readDescriptor(descriptorPath);
        if (!descriptorWitness.equals(SharedSourceFiles.observe(descriptorPath))) throw new IOException("descriptor identity changed during parsing");
        if (!Arrays.equals(descriptorBytes, readExact(expectedDescriptor, GameSupervisorControl.MAXIMUM_DESCRIPTOR_BYTES)))
            throw new IOException("descriptor differs from the exact parsed source");
        var plan = owner.configuration().accept();
        if(observationMode==ObservationMode.MENU_CORE) {
            if(!(plan.load() instanceof NativeLaunchPlan.NewGame))throw new IOException("explicit menu core mode requires its actual NewGame owner plan");
        } else if (!coreCommand&&!personalGold&&!actorFoundation&&!fullClock&&!(plan.load() instanceof NativeLaunchPlan.SavedGame)) throw new IOException("actual owner must retain its SavedGame plan");
        Files.createDirectory(output);
        createdOutput = output;
        ObjectNode originals = StrictJson.object();
        originals.set("owner_descriptor", write(output, "owner-descriptor.json", descriptorBytes));
        originals.set("snapshot_config", write(output, "snapshot-config.json", configBytes));
        originals.set("owner_hello", write(output, "owner-hello.bin", readExact(owner.nativeHello(), SMALL)));
        originals.set("owner_launch_evidence", write(output, "owner-launch-evidence.json", readExact(owner.launchEvidence(), SMALL)));
        ObjectNode result = StrictJson.object().put("schema", "xar.native-owner-snapshot/v1")
                .put("entered_at_utc", entered.toString()).put("operation_deadline_utc", deadline.toString())
                .put("original_launch_deadline_utc", plan.deadline().toString()).put("read_calls", 1)
                .put("business_or_source_admission", false);
        if(plan.load() instanceof NativeLaunchPlan.SavedGame saved) {
            result.put("saved_basename",saved.basename());
            result.set("configured_saved_file",new ExactRef(saved.save().path(),saved.save().bytes(),saved.save().sha256()).toJson());
        } else result.put("schema","xar.native-owner-core-menu/v1").put("mode","menu_core_prefix");
        result.set("owner_descriptor", expectedDescriptor.toJson());
        result.set("owner_descriptor_native_identity", nativeIdentity(descriptorWitness.nativeFile()));
        result.set("supervisor", identity(owner.supervisorIdentity()));
        result.set("game", owner.generation().toJson());
        if(controlStep!=null)result.put("schema","xar.native-owner-core-clock-control/v1").put("mode","core_clock_control")
                .put("control_step",controlStep.wire()).put("effect_confirmed",false).put("save_confirmed",false);
        if(applicationExit)result.put("schema","xar.native-owner-core-application-exit/v1").put("mode","core_application_exit")
                .put("normal_exit_confirmed",false);
        if(personalGold)result.put("schema","xar.native-owner-personal-gold/v1").put("mode","personal_gold_frame")
                .put("complete_snapshot",false).put("treasury_observed",false).put("monthly_flow_observed",false);
        if(actorFoundation)result.put("schema","xar.native-owner-actor-foundation/v1").put("mode","actor_foundation_frame")
                .put("complete_snapshot",false).put("treasury_observed",false).put("monthly_flow_observed",false);
        if(fullClock)result.put("schema","xar.native-owner-full-clock-control/v1").put("mode","full_snapshot_clock_control")
                .put("control_step",fullClockStep).put("effect_confirmed",false).put("save_confirmed",false);
        stage = "ATTACH";
        try (var supervisor = WindowsJobProcess.retainReadOnlyProcess(owner.supervisorIdentity().pid())) {
            requireSupervisor(supervisor, owner.supervisorIdentity());
            var request = new NativeGameAttachment.Request(plan, owner.generation(), List.of(), frames, coreCommand||fullClock?2:1);
            // This factory returns ATTACHED only. Its close releases communication and readonly handles, never a Job.
            try (ManagedGameSession game = NativeGameAttachment.attach(request, deadline, Duration.ofSeconds(readSeconds))) {
                if (game.mode() != ManagedGameSession.Mode.ATTACHED) throw new IOException("actual attachment mode differs");
                requireSupervisor(supervisor, owner.supervisorIdentity());
                var transport = game.nativeTransport();
                var hello = transport.diagnostics().originalHello().orElseThrow(() -> new IOException("actual received HELLO unavailable"));
                originals.set("new_hello", write(output, "new-hello.bin", hello.original().packet().value()));
                result.put("hello_observed_at_utc", hello.observedAt().toString());
                if(fullClock) {
                    stage="ONE_FULL_CLOCK_SOURCE_READ";
                    var read=transport.readFullClockFrameReceived(deadline);
                    archiveNaturalDiagnostics(output,originals,transport.diagnostics());
                    originals.set("dispatch",saveDispatch(output,read.original().dispatch()));
                    if(!(read instanceof org.xar.ck3.control.nativebridge.NativeGameTransport.FullClockReceived received))
                        throw new IOException("actual Full clock source unavailable; original retained, no retry: "+((org.xar.ck3.control.nativebridge.NativeGameTransport.FullClockReadUnavailable)read).reason());
                    var frame=received.frame();var ack=received.original().acknowledgement();
                    var custody=ack.custody().orElseThrow(()->new IOException("actual Full clock custody unavailable"));custody.verify(ack);
                    var actualSession=custody.session();
                    if(!actualSession.game().equals(owner.generation())||!actualSession.machineId().equals(owner.machineId())
                            ||!actualSession.sessionId().equals(owner.sessionId())||!transport.diagnostics().session().filter(actualSession::equals).isPresent())
                        throw new IOException("actual Full clock source crossed its owner Game/session");
                    Instant commandDeadline=deadline.isBefore(received.validUntil())?deadline:received.validUntil();
                    received.requireOriginal(transport,commandDeadline);
                    var prepared=FullSnapshotClockControl.request(fullClockStep,frame.snapshotId(),frame.nativeRevision(),commandDeadline);
                    originals.set("full_clock_before",saveFrame(output,frame));
                    result.set("session",session(actualSession));
                    result.put("full_read_request_id",ack.requestId()).put("snapshot_id",frame.snapshotId())
                            .put("native_revision",frame.nativeRevision()).put("command_deadline_utc",commandDeadline.toString());
                    result.set("prepared_native_fields",FullJsonTree.parse(prepared.additionalFields().bytes(),FullJsonTree.MAXIMUM_BYTES));
                    stage="ONE_PREPARED_FULL_CLOCK_SUBMISSION";
                    var outcome=transport.submitFullClockControl(received,prepared,commandDeadline);
                    Path control=output.resolve("control");Files.createDirectory(control);
                    originals.set("full_clock_dispatch",saveDispatch(control,outcome));
                    if(outcome instanceof NativeActionPort.Unknown unknown){
                        var retained=transport.originalIndeterminateFullClockAcknowledgement(unknown.requestId());
                        if(retained.isPresent()){
                            Path uncertain=control.resolve("indeterminate-native-ack");Files.createDirectory(uncertain);
                            originals.set("full_clock_original_uncertain_ack",saveDispatch(uncertain,retained.orElseThrow()));
                        }
                    } else if(outcome instanceof NativeActionPort.AckReceived commandAck){
                        var assessment=FullSnapshotClockControlResult.decode(commandAck,prepared.step());
                        result.put("queue_status",assessment.queueStatus()).put("effect_attempted",assessment.effectAttempted())
                                .put("full_snapshot_before_verified",assessment.fullBeforeVerified())
                                .put("submission_disposition",assessment.disposition().name());
                    }
                    result.put("request_id",outcome.requestId()).put("control_dispatch_class",outcome.getClass().getSimpleName());
                } else if(actorFoundation) {
                    stage="ONE_ACTOR_FOUNDATION_FRAME_READ";
                    var read=transport.readActorFoundationFrameReceived(deadline);
                    archiveNaturalDiagnostics(output,originals,transport.diagnostics());
                    originals.set("dispatch",saveDispatch(output,read.original()));
                    if(!(read instanceof org.xar.ck3.control.nativebridge.NativeGameTransport.ActorFoundationReceived received))
                        throw new IOException("actual actor-foundation source unavailable; original retained, no retry: "+((org.xar.ck3.control.nativebridge.NativeGameTransport.ActorFoundationReadUnavailable)read).reason());
                    var ack=received.original();var custody=ack.custody().orElseThrow(()->new IOException("actual actor-foundation custody unavailable"));custody.verify(ack);
                    var actualSession=custody.session();
                    if(!actualSession.game().equals(owner.generation())||!actualSession.machineId().equals(owner.machineId())
                            ||!actualSession.sessionId().equals(owner.sessionId())||!transport.diagnostics().session().filter(actualSession::equals).isPresent()
                            ||hello.original().pid()!=owner.generation().pid()||!hello.original().connectionGeneration().equals(actualSession.connectionGeneration()))
                        throw new IOException("actual actor-foundation ACK crossed its owner Game/session/connection");
                    received.requireOriginal(transport,received.validUntil());
                    var frame=received.frame();result.put("request_id",ack.requestId()).put("observed_at_utc",custody.responseReceived().observedAt().toString());
                    result.set("session",session(actualSession));
                    result.set("actor_foundation_frame",FullJsonTree.parse(ActorFoundationFramePublicCodec.encode(frame).bytes(),FullJsonTree.MAXIMUM_BYTES));
                    result.put("foundation_available",frame instanceof ActorFoundationFrame.Partial);
                } else if(personalGold) {
                    stage="ONE_PERSONAL_GOLD_FRAME_READ";
                    var read=transport.readPersonalGoldFrameReceived(deadline);
                    archiveNaturalDiagnostics(output,originals,transport.diagnostics());
                    originals.set("dispatch",saveDispatch(output,read.original()));
                    if(!(read instanceof org.xar.ck3.control.nativebridge.NativeGameTransport.PersonalGoldReceived received))
                        throw new IOException("actual personal-gold source unavailable; original retained, no retry: "+((org.xar.ck3.control.nativebridge.NativeGameTransport.PersonalGoldReadUnavailable)read).reason());
                    var ack=received.original();var custody=ack.custody().orElseThrow(()->new IOException("actual personal-gold custody unavailable"));custody.verify(ack);
                    var actualSession=custody.session();
                    if(!actualSession.game().equals(owner.generation())||!actualSession.machineId().equals(owner.machineId())
                            ||!actualSession.sessionId().equals(owner.sessionId())||!transport.diagnostics().session().filter(actualSession::equals).isPresent()
                            ||hello.original().pid()!=owner.generation().pid()||!hello.original().connectionGeneration().equals(actualSession.connectionGeneration()))
                        throw new IOException("actual personal-gold ACK crossed its owner Game/session/connection");
                    received.requireOriginal(transport,received.validUntil());
                    var frame=received.frame();result.put("request_id",ack.requestId()).put("observed_at_utc",custody.responseReceived().observedAt().toString());
                    result.set("session",session(actualSession));
                    result.set("personal_gold_frame",FullJsonTree.parse(PersonalGoldFramePublicCodec.encode(frame).bytes(),FullJsonTree.MAXIMUM_BYTES));
                    result.put("personal_gold_available",frame instanceof PersonalGoldFrame.Partial);
                } else if (corePrefixOnly) {
                    stage = "ONE_CORE_PREFIX_READ";
                    var coreRead=transport.readCoreFrameReceived(deadline);
                    // Snapshot already received evidence only: no additional Native query or window operation.
                    archiveNaturalDiagnostics(output,originals,transport.diagnostics());
                    NativeActionPort.DispatchOutcome dispatch = coreRead.original();
                    originals.set("dispatch", saveDispatch(output, dispatch));
                    if (!(coreRead instanceof org.xar.ck3.control.nativebridge.NativeGameTransport.CoreReceived received)) {
                        ObjectNode rejected = StrictJson.object().put("core_prefix_only", true)
                                .put("reason", ((org.xar.ck3.control.nativebridge.NativeGameTransport.CoreReadUnavailable)coreRead).reason()).put("dispatch_class", dispatch.getClass().getSimpleName());
                        rejected.set("originals", originals);
                        write(output, "unavailable.json", FullJsonTree.encode(rejected, FullJsonTree.MAXIMUM_BYTES));
                        throw new IOException("actual core prefix unavailable; no retry: " + dispatch.getClass().getSimpleName());
                    }
                    var ack=received.original();
                    var custody = ack.custody().orElseThrow(() -> new IOException("actual core ACK custody unavailable"));
                    custody.verify(ack);
                    var actualSession = custody.session();
                    if (!actualSession.game().equals(owner.generation()) || !actualSession.machineId().equals(owner.machineId())
                            || !actualSession.sessionId().equals(owner.sessionId())
                            || !transport.diagnostics().session().filter(actualSession::equals).isPresent()
                            || hello.original().pid() != owner.generation().pid()
                            || !hello.original().connectionGeneration().equals(actualSession.connectionGeneration()))
                        throw new IOException("actual core ACK/HELLO crossed expected owner Game/session/connection");
                    CoreFrame core = received.frame();
                    result.put("core_prefix_only", true).put("complete_snapshot", false).put("request_id", ack.requestId())
                            .put("observed_at_utc", custody.responseReceived().observedAt().toString());
                    result.set("session", session(actualSession));
                    ObjectNode observed = StrictJson.object();
                    if (core instanceof CoreFrame.Partial partial) {
                        var prefix = partial.prefix();
                        result.put("core_frame_kind", "PARTIAL");
                        observed.put("date_raw", prefix.dateRaw()).put("speed", prefix.speed()).put("paused", prefix.paused())
                                .put("local_player_id", prefix.localPlayerId()).put("map_ready", prefix.mapReady())
                                .put("has_played_character", prefix.hasPlayedCharacter()).put("played_character_id", prefix.playedCharacterId())
                                .put("played_character_alive", prefix.playedCharacterAlive());
                    } else {
                        var unavailable = (CoreFrame.Unavailable) core;
                        result.put("core_frame_kind", "UNAVAILABLE").put("application_main_observed", unavailable.applicationMainObserved())
                                .put("unavailable_reason", unavailable.reason());
                        for (String field : List.of("date_raw", "speed", "paused", "local_player_id", "map_ready", "has_played_character", "played_character_id", "played_character_alive"))
                            observed.putNull(field);
                    }
                    result.set("observed", observed);
                    if(coreCommand) {
                        stage=applicationExit?"ONE_CORE_APPLICATION_EXIT_REQUEST":"ONE_CORE_CLOCK_CONTROL_SUBMISSION";
                        Instant controlDeadline=received.validUntil().isBefore(deadline)?received.validUntil():deadline;
                        var control=applicationExit?transport.submitCoreNormalExit(received,controlDeadline)
                                :transport.submitCoreClockControl(received,controlStep,controlDeadline);
                        String action=applicationExit?"exit":"control";
                        Path controlOutput=output.resolve(action);Files.createDirectory(controlOutput);
                        originals.set(action+"_dispatch",saveDispatch(controlOutput,control));
                        result.put(action+"_request_id",control.requestId()).put(action+"_dispatch_class",control.getClass().getSimpleName())
                                .put(action+"_deadline_utc",controlDeadline.toString()).put(action+"_calls",1);
                        // An ACK is the original submission result; no engine effect or physical SAVE is inferred.
                        if(control instanceof NativeActionPort.AckReceived submitted)result.put(action+"_native_ok",submitted.nativeOk());
                        if(control instanceof NativeActionPort.Unknown)result.put(action+"_replay_forbidden",true);
                        var uncertainAck=transport.originalIndeterminateCoreAcknowledgement(control.requestId());
                        if(uncertainAck.isPresent()) {
                            Path retained=controlOutput.resolve("indeterminate-ack");Files.createDirectory(retained);
                            originals.set(action+"_indeterminate_native_ack",saveDispatch(retained,uncertainAck.orElseThrow()));
                        }
                    }
                } else {
                stage = "ONE_FRESH_READ";
                NativeFreshSnapshotPort.Result read = transport.readFreshFullState(deadline);
                archiveNaturalDiagnostics(output,originals,transport.diagnostics());
                originals.set("dispatch", saveDispatch(output, read.dispatch()));
                if (read instanceof NativeFreshSnapshotPort.Unavailable unavailable) {
                    ObjectNode rejected = StrictJson.object().put("reason", unavailable.reason());
                    if (unavailable.originalFrame().isPresent()) rejected.set("frame", saveFrame(output, unavailable.originalFrame().orElseThrow()));
                    if (unavailable.snapshotReceived().isPresent()) rejected.set("snapshot_received", event(unavailable.snapshotReceived().orElseThrow()));
                    rejected.set("originals", originals);
                    write(output, "unavailable.json", FullJsonTree.encode(rejected, FullJsonTree.MAXIMUM_BYTES));
                    throw new IOException("original fresh READ unavailable; no retry: " + unavailable.reason());
                }
                var received = (NativeFreshSnapshotPort.Received) read;
                NativeFreshSnapshotPort.verifyOriginal(received.acknowledgement(), received.originalFrame(), received.snapshotReceived());
                var frame = received.originalFrame();
                if (!frame.session().game().equals(owner.generation()) || !frame.session().machineId().equals(owner.machineId())
                        || !frame.session().sessionId().equals(owner.sessionId())
                        || !transport.diagnostics().session().filter(frame.session()::equals).isPresent()
                        || hello.original().pid() != owner.generation().pid()
                        || !hello.original().connectionGeneration().equals(frame.session().connectionGeneration()))
                    throw new IOException("actual READ/HELLO crossed expected owner Game/session/connection");
                stage = "PRESERVE_READ";
                originals.set("frame", saveFrame(output, frame));
                result.set("session", session(frame.session()));
                result.put("request_id", received.acknowledgement().requestId()).put("snapshot_id", frame.snapshotId())
                        .put("native_revision", frame.nativeRevision().toString()).put("observed_at_utc", frame.observedAt().toString());
                result.set("snapshot_received", event(received.snapshotReceived()));
                JsonNode parsedState = FullJsonTree.parse(frame.state().bytes(), FullJsonTree.MAXIMUM_BYTES);
                if (!(parsedState instanceof ObjectNode)) throw new IOException("actual full state must be an object");
                ObjectNode state = (ObjectNode) parsedState;
                ObjectNode observed = StrictJson.object();
                for (String field : List.of("date_raw", "paused", "map_ready", "speed", "context", "campaign", "campaign_id", "game_id"))
                    observed.set(field, state.has(field) ? state.get(field).deepCopy() : com.fasterxml.jackson.databind.node.TextNode.valueOf("UNKNOWN"));
                JsonNode player = state.get("played_character");
                observed.set("played_character_id", player != null && player.isObject() && player.has("character_id")
                        ? player.get("character_id").deepCopy() : com.fasterxml.jackson.databind.node.TextNode.valueOf("UNKNOWN"));
                result.set("observed", observed);
                var keys = result.putArray("native_state_top_keys");
                for (var field : state.properties()) keys.add(field.getKey());
                }
                // Exit may already have completed. This branch records originals, never a new live role or terminal.
                if(!applicationExit) {requireSupervisor(supervisor, owner.supervisorIdentity());game.verify();}
                if (!descriptorWitness.equals(SharedSourceFiles.observe(descriptorPath))) throw new IOException("original owner descriptor changed during READ");
                stage = "RELEASE_ENDPOINT";
            }
        }
        // Success is published only after actual ATTACHED endpoint and readonly handles have closed successfully.
        stage = "PUBLISH_ARCHIVED_DATA";
        result.set("originals", originals);
        String archivedStatus = fullClock?"ARCHIVED_NATIVE_FULL_CLOCK_SUBMISSION_ENDPOINT_RELEASED":actorFoundation?"ARCHIVED_NATIVE_ACTOR_FOUNDATION_DATA_ENDPOINT_RELEASED":personalGold?"ARCHIVED_NATIVE_PERSONAL_GOLD_DATA_ENDPOINT_RELEASED":applicationExit?"ARCHIVED_NATIVE_APPLICATION_EXIT_REQUEST_ENDPOINT_RELEASED":controlStep!=null?"ARCHIVED_NATIVE_CORE_CONTROL_SUBMISSION_ENDPOINT_RELEASED":corePrefixOnly ? "ARCHIVED_NATIVE_CORE_PREFIX_DATA_ENDPOINT_RELEASED" : "ARCHIVED_NATIVE_READ_DATA_ENDPOINT_RELEASED";
        result.put("status", archivedStatus).put("completed_at_utc", Instant.now().toString());
        ObjectNode published = write(output, "summary.json", FullJsonTree.encode(result, FullJsonTree.MAXIMUM_BYTES));
        System.out.println(StrictJson.object().put("schema", "xar.native-owner-snapshot-stage/v1")
                .put("status", archivedStatus).put("at_utc", Instant.now().toString()).set("summary", published));
    }

    private static void archiveNaturalDiagnostics(Path output,ObjectNode originals,org.xar.ck3.control.nativebridge.NativeGameTransport.TransportDiagnostics diagnostics)throws IOException {
        ObjectNode natural=StrictJson.object().put("received_state",diagnostics.receivedState().name()).put("heartbeat_present",diagnostics.latestHeartbeat().isPresent());
        if(diagnostics.terminalFailure().isPresent())natural.put("terminal_failure",bounded(diagnostics.terminalFailure().orElseThrow(),4096));
        if(diagnostics.latestHeartbeat().isPresent()) {
            var heartbeat=diagnostics.latestHeartbeat().orElseThrow();natural.put("heartbeat_observed_at_utc",heartbeat.observedAt().toString());
            natural.set("heartbeat_packet",write(output,"natural-heartbeat.bin",heartbeat.original().packet().value()));
            natural.set("heartbeat_payload",write(output,"natural-heartbeat-payload.json",heartbeat.original().payload().value()));
        }
        originals.set("natural_transport_diagnostics",write(output,"natural-transport-diagnostics.json",FullJsonTree.encode(natural,SMALL)));
    }
    enum ObservationMode { SAVED_FULL,SAVED_CORE,MENU_CORE,CORE_CONTROL,CORE_EXIT,PERSONAL_GOLD,ACTOR_FOUNDATION,FULL_CLOCK }
    static ObservationMode observationMode(ObjectNode config) {
        String schema=StrictJson.text(config.get("schema"));
        if(schema.equals("xar.native-owner-snapshot-config/v7")) {
            StrictJson.require(!config.has("core_prefix_only")&&"full_snapshot_clock_control".equals(StrictJson.text(config.get("mode"))),
                    "explicit prepared Full clock mode required");
            StrictJson.require(FullSnapshotClockControl.supports(new OperationKey(StrictJson.text(config.get("control_step")))),
                    "only the fixed Full clock step set is accepted");
            return ObservationMode.FULL_CLOCK;
        }
        if(schema.equals("xar.native-owner-snapshot-config/v6")) {
            StrictJson.require(!config.has("core_prefix_only")&&!config.has("control_step")
                    &&"actor_foundation_frame".equals(StrictJson.text(config.get("mode"))),"explicit read-only actor-foundation mode required");
            return ObservationMode.ACTOR_FOUNDATION;
        }
        if(schema.equals("xar.native-owner-snapshot-config/v5")) {
            StrictJson.require(!config.has("core_prefix_only")&&!config.has("control_step")
                    &&"personal_gold_frame".equals(StrictJson.text(config.get("mode"))),"explicit read-only personal-gold mode required");
            return ObservationMode.PERSONAL_GOLD;
        }
        if(schema.equals("xar.native-owner-snapshot-config/v4")) {
            StrictJson.require(!config.has("core_prefix_only")&&!config.has("control_step")
                    &&"core_application_exit".equals(StrictJson.text(config.get("mode"))),"explicit background application exit mode required");
            return ObservationMode.CORE_EXIT;
        }
        if(schema.equals("xar.native-owner-snapshot-config/v3")) {
            StrictJson.require(!config.has("core_prefix_only")&&"core_clock_control".equals(StrictJson.text(config.get("mode"))),"explicit core control mode required");
            CoreClockControl.Step.fromWire(StrictJson.text(config.get("control_step")));
            return ObservationMode.CORE_CONTROL;
        }
        StrictJson.require(!config.has("control_step"),"control step requires explicit v3 core control mode");
        if(schema.equals("xar.native-owner-snapshot-config/v1")) {
            StrictJson.require(!config.has("mode"),"legacy snapshot config cannot select a new owner mode");
            if(config.has("core_prefix_only"))StrictJson.require(config.get("core_prefix_only").isBoolean(),"core_prefix_only must be an actual boolean");
            return config.path("core_prefix_only").booleanValue()?ObservationMode.SAVED_CORE:ObservationMode.SAVED_FULL;
        }
        StrictJson.require(schema.equals("xar.native-owner-snapshot-config/v2")&&!config.has("core_prefix_only")
                &&"menu_core_prefix".equals(StrictJson.text(config.get("mode"))),"explicit menu core mode requires the exact new configuration schema");
        return ObservationMode.MENU_CORE;
    }
    private static ObjectNode saveDispatch(Path output, NativeActionPort.DispatchOutcome dispatch) throws IOException {
        ObjectNode row = StrictJson.object().put("request_id", dispatch.requestId()).put("class", dispatch.getClass().getSimpleName());
        if (dispatch instanceof NativeActionPort.AckReceived ack) {
            row.put("native_ok", ack.nativeOk());
            row.set("ack_packet", write(output, "read-ack.bin", ack.originalPacket()));
            row.set("ack_payload", write(output, "read-ack-payload.json", ack.originalFrame().bytes()));
            if (ack.originalResultToken().isPresent()) row.set("result_token", write(output, "read-result-token.json", ack.originalResultToken().orElseThrow().bytes()));
            if (ack.outbound().isPresent()) row.set("outbound", write(output, "read-outbound.bin", ack.outbound().orElseThrow().originalPacket()));
            if (ack.custody().isPresent()) {
                var custody = ack.custody().orElseThrow(); custody.verify(ack);
                ObjectNode actual = StrictJson.object().put("request_id", custody.requestId()).put("custody_epoch", custody.custodyEpoch().toString());
                actual.set("session", session(custody.session()));
                actual.set("original_request", packet(custody.originalRequest())); actual.set("original_response", packet(custody.originalResponse()));
                actual.set("write_entered", event(custody.writeEntered())); actual.set("write_completed", event(custody.writeCompleted()));
                actual.set("response_received", event(custody.responseReceived()));
                row.set("actual_custody", actual);
                row.set("custody_material", write(output, "read-custody.json", FullJsonTree.encode(actual, SMALL)));
            }
        } else if (dispatch instanceof NativeActionPort.Unknown unknown) {
            row.put("reason", unknown.reason()).put("original_request_bytes", unknown.originalRequestPacket().length);
            if (unknown.originalRequestPacket().length > 0) row.set("outbound", write(output, "read-outbound.bin", unknown.originalRequestPacket()));
            if (unknown.rawReturn().isPresent()) row.set("raw_return", write(output, "read-raw-return.json", unknown.rawReturn().orElseThrow().bytes()));
            if (unknown.failureCause().isPresent()) {
                var cause = unknown.failureCause().orElseThrow();
                row.put("failure_kind", cause.kind().name()).put("failure_stage", cause.stage().name());
                if (cause.originalException().isPresent()) row.put("original_exception", cause.originalException().orElseThrow().javaType()).put("original_message", cause.originalException().orElseThrow().message());
                if (cause.originalCause().isPresent()) row.put("original_cause", cause.originalCause().orElseThrow().javaType()).put("original_cause_message", cause.originalCause().orElseThrow().message());
                if (cause.deadline().isPresent()) {
                    var observed = cause.deadline().orElseThrow();
                    row.put("supplied_deadline", observed.suppliedDeadline().toString()).put("deadline_observed_at", observed.observedAt().toString()).put("monotonic_expired", observed.monotonicExpired());
                }
            }
        } else {
            var zero = ((NativeActionPort.RejectedBeforeDispatch) dispatch).proof();
            row.put("stage", zero.stage().name()).put("request_bytes_written", zero.requestBytesWritten()).put("reason", zero.reason());
            if (zero.diagnostic().isPresent()) row.set("diagnostic", write(output, "read-zero-diagnostic.json", zero.diagnostic().orElseThrow().bytes()));
        }
        row.set("dispatch_material", write(output, "read-dispatch.json", FullJsonTree.encode(row, FullJsonTree.MAXIMUM_BYTES)));
        return row;
    }

    private static ObjectNode saveFrame(Path output, NativeObservationPort.ObservedFrame frame) throws IOException {
        ObjectNode row = StrictJson.object().put("snapshot_id", frame.snapshotId()).put("native_revision", frame.nativeRevision().toString()).put("observed_at_utc", frame.observedAt().toString());
        row.set("session", session(frame.session()));
        row.set("packet", write(output, "native-frame.bin", frame.originalPacket()));
        row.set("raw_state", write(output, "native-state.json", frame.state().bytes()));
        return row;
    }
    private static ObjectNode session(NativeObservationPort.TransportSession session) {
        ObjectNode row = StrictJson.object().put("machine_id", session.machineId()).put("session_id", session.sessionId()).put("connection_generation", session.connectionGeneration().toString());
        row.set("game", session.game().toJson()); return row;
    }
    private static ObjectNode event(NativeRequestChronology.Event event) { return StrictJson.object().put("order", event.order().toString()).put("observed_at_utc", event.observedAt().toString()); }
    private static ObjectNode packet(NativeRequestChronology.PacketIdentity packet) { return StrictJson.object().put("bytes", packet.bytes()).put("sha256", packet.sha256()); }
    private static ObjectNode identity(WindowsJobProcess.ProcessIdentity identity) {
        return StrictJson.object().put("pid", identity.pid()).put("creation_filetime", identity.creationFiletimeDecimal()).put("executable", identity.executable());
    }
    private static ObjectNode nativeIdentity(SharedSourceFiles.NativeFile actual) {
        return StrictJson.object().put("volume_serial_decimal", actual.volumeSerialDecimal()).put("file_id_decimal", actual.fileIdDecimal())
                .put("creation_filetime_decimal", actual.creationFiletimeDecimal()).put("last_write_filetime_decimal", actual.lastWriteFiletimeDecimal())
                .put("change_filetime_decimal", actual.changeFiletimeDecimal()).put("logical_bytes", actual.logicalBytes()).put("allocated_bytes", actual.allocatedBytes()).put("link_count", actual.linkCount());
    }
    private static ObjectNode write(Path directory, String name, byte[] original) throws IOException {
        Path target = directory.resolve(name);
        try (FileChannel file = FileChannel.open(target, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE)) {
            ByteBuffer buffer = ByteBuffer.wrap(original); while (buffer.hasRemaining()) file.write(buffer); file.force(true);
        }
        var witness = SharedSourceFiles.observe(target);
        var expected = new ExactRef(target.toString(), original.length, sha256(original));
        requireWitnessBytes(witness, expected);
        ObjectNode row = StrictJson.object(); row.set("reference", expected.toJson()); row.set("native_identity", nativeIdentity(witness.nativeFile())); return row;
    }
    private static byte[] readBounded(Path path, int maximum) throws IOException {
        try (InputStream input = Files.newInputStream(path)) {
            byte[] bytes = input.readNBytes(maximum + 1);
            if (bytes.length == 0 || bytes.length > maximum) throw new IOException("bounded nonempty source required: " + path);
            return bytes;
        }
    }
    private static byte[] readExact(ExactRef ref, int maximum) throws IOException {
        if (ref.bytes() < 1 || ref.bytes() > maximum) throw new IOException("exact source exceeds its finite role");
        byte[] raw = readBounded(Path.of(ref.path()), maximum);
        if (raw.length != ref.bytes() || !sha256(raw).equals(ref.sha256())) throw new IOException("exact source bytes/SHA differ: " + ref.path()); return raw;
    }
    private static void requireWitnessBytes(SharedSourceFiles.Witness witness, ExactRef ref) throws IOException {
        if (witness.source().bytes() != ref.bytes() || !witness.source().sha256().equals(ref.sha256())) throw new IOException("source witness differs from exact bytes/SHA");
    }
    private static void requireSupervisor(WindowsJobProcess.ReadOnlyProcessHandle actual, WindowsJobProcess.ProcessIdentity expected) throws IOException {
        if (!actual.identity().equals(expected) || actual.waitZero() != 258L) throw new IOException("actual supervisor exited or changed identity");
    }
    private static String sha256(byte[] bytes) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)); }
        catch (NoSuchAlgorithmException impossible) { throw new AssertionError(impossible); }
    }
    private static String bounded(String value, int limit) { return value == null ? null : value.substring(0, Math.min(limit, value.length())); }
    private static void printBounded(Throwable failure) {
        PrintWriter sink = new PrintWriter(new Writer() {
            private int remaining = 32768;
            @Override public void write(char[] chars, int offset, int length) { int count = Math.min(length, remaining); if (count > 0) { System.err.print(new String(chars, offset, count)); remaining -= count; } }
            @Override public void flush() { System.err.flush(); }
            @Override public void close() { flush(); }
        });
        failure.printStackTrace(sink); sink.flush();
    }
}
