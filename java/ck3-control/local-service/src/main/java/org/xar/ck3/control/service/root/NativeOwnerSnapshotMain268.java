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
import java.util.Objects;
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
import org.xar.ck3.control.application.action.FullSnapshotDateSentinelArm;
import org.xar.ck3.control.application.advance.ClockStatusRead;
import org.xar.ck3.control.application.advance.AdvancePrimitives;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.nativebridge.FullSnapshotClockControlResult;
import org.xar.ck3.control.nativebridge.DateSentinelArmResult;
import org.xar.ck3.control.nativebridge.NativeGameTransport;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;
import org.xar.ck3.control.nativebridge.capabilities.registry.GuiRootIndexFrame;
import org.xar.ck3.control.nativebridge.capabilities.registry.GuiRootIndexFramePublicCodec;
import org.xar.ck3.control.nativebridge.capabilities.registry.GuiWindowFrame;
import org.xar.ck3.control.nativebridge.capabilities.registry.GuiWindowFramePublicCodec;
import org.xar.ck3.control.nativebridge.capabilities.registry.RiteDraftCostsFrameV2;
import org.xar.ck3.control.nativebridge.capabilities.registry.RiteDraftCostsFrameV2PublicCodec;
import org.xar.ck3.control.nativebridge.capabilities.registry.GuiControlsFrameV2;
import org.xar.ck3.control.nativebridge.capabilities.registry.GuiControlsFrameV2PublicCodec;
import org.xar.ck3.control.nativebridge.capabilities.registry.PersonalGoldFrame;
import org.xar.ck3.control.nativebridge.capabilities.registry.PersonalGoldFramePublicCodec;
import org.xar.ck3.control.nativebridge.capabilities.registry.ActorFoundationFrame;
import org.xar.ck3.control.nativebridge.capabilities.registry.ActorFoundationFramePublicCodec;
import org.xar.ck3.control.platform.GameSupervisorControl;
import org.xar.ck3.control.platform.ManagedGameSession;
import org.xar.ck3.control.platform.NativeGameAttachment;
import org.xar.ck3.control.platform.NativeLaunchPlan;
import org.xar.ck3.control.nativebridge.CurrentCoreCheckpointSave;
import org.xar.ck3.control.nativebridge.CurrentCoreCheckpointSaveResult;
import org.xar.ck3.control.application.checkpoint.NativeCheckpointFiles;
import org.xar.ck3.control.application.checkpoint.CheckpointPair.FileWitness;
import org.xar.ck3.control.build.ControlBuild;

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
                "overall_timeout_seconds", "read_timeout_seconds", "maximum_frames_per_operation"), Set.of("core_prefix_only", "mode", "control_step", "maximum_status_polls", "status_poll_interval_ms", "window_name", "expected_source_rite_id", "checkpoint_archive_path", "maximum_checkpoint_bytes", "checkpoint_observation_attempts", "checkpoint_poll_interval_ms", "previous_checkpoint_source", "previous_checkpoint_archive"));
        ObservationMode observationMode=observationMode(config);
        boolean applicationExit=observationMode==ObservationMode.CORE_EXIT;
        boolean checkpointSave=observationMode==ObservationMode.CORE_CHECKPOINT_SAVE;
        boolean personalGold=observationMode==ObservationMode.PERSONAL_GOLD;
        boolean actorFoundation=observationMode==ObservationMode.ACTOR_FOUNDATION;
        boolean personalCash=observationMode==ObservationMode.PERSONAL_CASH;
        boolean guiRootIndex=observationMode==ObservationMode.GUI_ROOT_INDEX;
        boolean guiWindow=observationMode==ObservationMode.GUI_WINDOW;
        boolean riteDraftCosts=observationMode==ObservationMode.RITE_DRAFT_COSTS;
        boolean guiControls=observationMode==ObservationMode.GUI_CONTROLS_V2;
        GuiControlsFrameV2.Window controlWindow=guiControls?GuiControlsFrameV2.Window.wire(StrictJson.text(config.get("window_name"))):null;
        long expectedSourceRiteId=(riteDraftCosts||guiControls&&controlWindow==GuiControlsFrameV2.Window.RITE)?StrictJson.integer(config.get("expected_source_rite_id"),0,0xffff_fffeL):0;
        String requestedWindow=guiWindow?GuiWindowFrame.windowName(StrictJson.text(config.get("window_name"))):null;
        boolean fullClock=observationMode==ObservationMode.FULL_CLOCK;
        boolean dateAdvance=observationMode==ObservationMode.DATE_ADVANCE;
        int maximumStatusPolls=dateAdvance?Math.toIntExact(StrictJson.integer(config.get("maximum_status_polls"),1,128)):0;
        long statusPollMillis=dateAdvance?StrictJson.integer(config.get("status_poll_interval_ms"),100,5000):0;
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
        } else if (!coreCommand&&!personalGold&&!actorFoundation&&!personalCash&&!guiRootIndex&&!guiWindow&&!riteDraftCosts&&!guiControls&&!fullClock&&!dateAdvance&&!(plan.load() instanceof NativeLaunchPlan.SavedGame)) throw new IOException("actual owner must retain its SavedGame plan");
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
        if(personalCash)result.put("schema","xar.native-owner-personal-cash/v1").put("mode","personal_cash_current")
                .put("read_calls",2).put("true_treasury_observed",false).put("military_categories_observed",false)
                .put("formal_finance_ready",false);
        if(guiRootIndex)result.put("schema","xar.native-owner-gui-root-index/v1").put("mode","scripted_gui_root_index")
                .put("read_calls",0).put("complete_snapshot",false).put("complete_gui_tree",false)
                .put("control_actions_available",false).put("addresses_redacted",true).put("root_index_live_qualified",false);
        if(guiWindow)result.put("schema","xar.native-owner-gui-window/v1").put("mode","scripted_gui_window")
                .put("read_calls",0).put("complete_snapshot",false).put("complete_gui_tree",false).put("activation_available",false)
                .put("control_actions_available",false).put("addresses_redacted",true).put("native_findtop_semantics_verified",false).put("window_live_qualified",false);
        if(riteDraftCosts)result.put("schema","xar.native-owner-rite-draft-costs/v2").put("mode","rite_draft_costs")
                .put("read_calls",0).put("complete_snapshot",false).put("complete_gui_tree",false).put("control_actions_available",false)
                .put("observer_guard_evaluated",false).put("physical_save_confirmed",false).put("addresses_redacted",true).put("rite_draft_live_qualified",false);
        if(guiControls)result.put("schema","xar.native-owner-gui-controls/v2").put("mode","scripted_widget_controls")
                .put("read_calls",0).put("complete_snapshot",false).put("full_snapshot_before_verified",false).put("complete_gui_tree",false)
                .put("effect_confirmed",false).put("physical_save_confirmed",false).put("activation_calls",0).put("controls_live_qualified",false);
        if(checkpointSave)result.put("schema","xar.native-owner-current-core-checkpoint/v1").put("mode","current_core_checkpoint_save")
                .put("physical_save_confirmed",false).put("business_or_ledger_SAVE_credit",false).put("save_calls",0);
        stage = "ATTACH";
        try (var supervisor = WindowsJobProcess.retainReadOnlyProcess(owner.supervisorIdentity().pid())) {
            requireSupervisor(supervisor, owner.supervisorIdentity());
            var request = new NativeGameAttachment.Request(plan, owner.generation(), List.of(), frames,guiControls?(controlWindow==GuiControlsFrameV2.Window.RITE?3:2):dateAdvance?maximumStatusPolls+6:checkpointSave||coreCommand||fullClock||personalCash||guiRootIndex||guiWindow||riteDraftCosts?2:1);
            // This factory returns ATTACHED only. Its close releases communication and readonly handles, never a Job.
            try (ManagedGameSession game = NativeGameAttachment.attach(request, checkpointSave&&plan.deadline().isBefore(deadline)?plan.deadline():deadline, Duration.ofSeconds(readSeconds))) {
                if (game.mode() != ManagedGameSession.Mode.ATTACHED) throw new IOException("actual attachment mode differs");
                requireSupervisor(supervisor, owner.supervisorIdentity());
                var transport = game.nativeTransport();
                var hello = transport.diagnostics().originalHello().orElseThrow(() -> new IOException("actual received HELLO unavailable"));
                originals.set("new_hello", write(output, "new-hello.bin", hello.original().packet().value()));
                result.put("hello_observed_at_utc", hello.observedAt().toString());
                if(checkpointSave) {
                    Instant checkpointDeadline=plan.deadline().isBefore(deadline)?plan.deadline():deadline;
                    runCoreCheckpoint(transport,owner,plan,config,output,checkpointDeadline,result,originals);
                } else if(guiControls) {
                    stage="ONE_CONTROLS_V2_CORE_SOURCE";result.put("read_calls",1);
                    var coreRead=transport.readCoreFrameReceived(deadline);Path coreOutput=Files.createDirectory(output.resolve("core-before-controls-v2"));
                    ObjectNode coreOriginals=StrictJson.object();archiveNaturalDiagnostics(coreOutput,coreOriginals,transport.diagnostics());originals.set("core_natural",coreOriginals);originals.set("core_dispatch",saveDispatch(coreOutput,coreRead.original()));
                    if(!(coreRead instanceof NativeGameTransport.CoreReceived before))throw new IOException("actual controls Core source unavailable; retain original, no retry: "+((NativeGameTransport.CoreReadUnavailable)coreRead).reason());
                    var coreCustody=before.original().custody().orElseThrow(()->new IOException("actual controls Core custody absent"));coreCustody.verify(before.original());var actualSession=coreCustody.session();
                    if(!actualSession.game().equals(owner.generation())||!actualSession.machineId().equals(owner.machineId())||!actualSession.sessionId().equals(owner.sessionId())||!transport.diagnostics().session().filter(actualSession::equals).isPresent()||hello.original().pid()!=owner.generation().pid()||!hello.original().connectionGeneration().equals(actualSession.connectionGeneration()))throw new IOException("controls Core crossed actual owner/session/connection");
                    Instant queryDeadline=before.validUntil().isBefore(deadline)?before.validUntil():deadline;before.requireOriginal(transport,queryDeadline);
                    NativeGameTransport.GuiControlsReadV2 read;
                    if(controlWindow==GuiControlsFrameV2.Window.RITE) {
                        stage="ONE_CONTROLS_V2_ACTUAL_RITE_DRAFT_SOURCE";result.put("read_calls",2);
                        var sourceRead=transport.readRiteDraftCostsReceived(before,expectedSourceRiteId,queryDeadline);Path sourceOutput=Files.createDirectory(output.resolve("draft-before-controls-v2"));originals.set("draft_dispatch",saveDispatch(sourceOutput,sourceRead.original()));
                        if(!(sourceRead instanceof NativeGameTransport.RiteDraftCostsReceived source)||!(source.frame() instanceof RiteDraftCostsFrameV2.Partial))throw new IOException("controls Rite source must come from the actual same-transport draft; no configured source substitution");
                        queryDeadline=source.validUntil().isBefore(queryDeadline)?source.validUntil():queryDeadline;source.requireOriginal(transport,queryDeadline);
                        stage="ONE_CONTROLS_V2_READ";result.put("read_calls",3);read=transport.readRiteGuiControlsV2(source,queryDeadline);
                    }else {stage="ONE_CONTROLS_V2_READ";result.put("read_calls",2);read=transport.readFaithGuiControlsV2(before,queryDeadline);}
                    archiveNaturalDiagnostics(output,originals,transport.diagnostics());originals.set("dispatch",saveDispatch(output,read.original()));
                    if(!(read instanceof NativeGameTransport.GuiControlsReceivedV2 received))throw new IOException("actual controls response unavailable; original retained, no retry: "+((NativeGameTransport.GuiControlsReadUnavailableV2)read).reason());
                    received.requireOriginal(transport,received.validUntil());var ack=received.original();ack.custody().orElseThrow().verify(ack);if(!ack.custody().orElseThrow().session().equals(actualSession))throw new IOException("controls crossed original Core session");
                    var frame=received.frame();requireGuiControlsSelection(plan,frame);result.put("core_request_id",before.original().requestId()).put("request_id",ack.requestId());result.set("session",session(actualSession));
                    result.set("gui_controls",FullJsonTree.parse(GuiControlsFrameV2PublicCodec.encode(frame).bytes(),FullJsonTree.MAXIMUM_BYTES));result.put("query_available",frame.queryAvailable());
                } else 
if(riteDraftCosts) {
                    stage="ONE_RITE_DRAFT_COSTS_CORE_SOURCE_READ";result.put("read_calls",1);
                    var coreRead=transport.readCoreFrameReceived(deadline);
                    Path coreOutput=Files.createDirectory(output.resolve("core-before-rite-draft-costs"));
                    ObjectNode coreOriginals=StrictJson.object();archiveNaturalDiagnostics(coreOutput,coreOriginals,transport.diagnostics());
                    originals.set("core_natural",coreOriginals);originals.set("core_dispatch",saveDispatch(coreOutput,coreRead.original()));
                    if(!(coreRead instanceof NativeGameTransport.CoreReceived before))
                        throw new IOException("actual rite-draft-costs Core source unavailable; original retained, no retry: "+((NativeGameTransport.CoreReadUnavailable)coreRead).reason());
                    var coreCustody=before.original().custody().orElseThrow(()->new IOException("rite-draft-costs Core custody unavailable"));coreCustody.verify(before.original());
                    var actualSession=coreCustody.session();
                    if(!actualSession.game().equals(owner.generation())||!actualSession.machineId().equals(owner.machineId())
                            ||!actualSession.sessionId().equals(owner.sessionId())||!transport.diagnostics().session().filter(actualSession::equals).isPresent()
                            ||hello.original().pid()!=owner.generation().pid()||!hello.original().connectionGeneration().equals(actualSession.connectionGeneration()))
                        throw new IOException("rite-draft-costs Core crossed its actual owner Game/session/connection");
                    Instant queryDeadline=before.validUntil().isBefore(deadline)?before.validUntil():deadline;
                    before.requireOriginal(transport,queryDeadline);
                    stage="ONE_GUI_RITE_DRAFT_COSTS_READ";result.put("read_calls",2);
                    var read=transport.readRiteDraftCostsReceived(before,expectedSourceRiteId,queryDeadline);
                    archiveNaturalDiagnostics(output,originals,transport.diagnostics());originals.set("dispatch",saveDispatch(output,read.original()));
                    if(!(read instanceof NativeGameTransport.RiteDraftCostsReceived received))
                        throw new IOException("actual rite-draft-costs result unavailable; original retained, no retry: "+((NativeGameTransport.RiteDraftCostsReadUnavailable)read).reason());
                    received.requireOriginal(transport,received.validUntil());var ack=received.original();
                    var custody=ack.custody().orElseThrow(()->new IOException("actual rite-draft-costs custody unavailable"));custody.verify(ack);
                    if(!custody.session().equals(actualSession))throw new IOException("rite-draft-costs query crossed its original Core session");
                    var frame=received.frame();requireRiteDraftCostsSelection(plan,frame);
                    result.put("core_request_id",before.original().requestId()).put("request_id",ack.requestId()).put("observed_at_utc",custody.responseReceived().observedAt().toString());
                    result.set("session",session(actualSession));result.set("rite_draft_costs_frame",FullJsonTree.parse(RiteDraftCostsFrameV2PublicCodec.encode(frame).bytes(),FullJsonTree.MAXIMUM_BYTES));
                    result.put("draft_available",frame instanceof RiteDraftCostsFrameV2.Partial);
                } else if(guiWindow) {
                    stage="ONE_NAMED_WINDOW_CORE_SOURCE_READ";result.put("read_calls",1);
                    var coreRead=transport.readCoreFrameReceived(deadline);
                    Path coreOutput=Files.createDirectory(output.resolve("core-before-named-window"));
                    ObjectNode coreOriginals=StrictJson.object();archiveNaturalDiagnostics(coreOutput,coreOriginals,transport.diagnostics());
                    originals.set("core_natural",coreOriginals);originals.set("core_dispatch",saveDispatch(coreOutput,coreRead.original()));
                    if(!(coreRead instanceof NativeGameTransport.CoreReceived before))
                        throw new IOException("actual named-window Core source unavailable; original retained, no retry: "+((NativeGameTransport.CoreReadUnavailable)coreRead).reason());
                    var coreCustody=before.original().custody().orElseThrow(()->new IOException("named-window Core custody unavailable"));coreCustody.verify(before.original());
                    var actualSession=coreCustody.session();
                    if(!actualSession.game().equals(owner.generation())||!actualSession.machineId().equals(owner.machineId())
                            ||!actualSession.sessionId().equals(owner.sessionId())||!transport.diagnostics().session().filter(actualSession::equals).isPresent()
                            ||hello.original().pid()!=owner.generation().pid()||!hello.original().connectionGeneration().equals(actualSession.connectionGeneration()))
                        throw new IOException("named-window Core crossed its actual owner Game/session/connection");
                    Instant queryDeadline=before.validUntil().isBefore(deadline)?before.validUntil():deadline;
                    before.requireOriginal(transport,queryDeadline);
                    stage="ONE_GUI_NAMED_WINDOW_READ";result.put("read_calls",2);
                    var read=transport.readGuiWindowReceived(before,requestedWindow,queryDeadline);
                    archiveNaturalDiagnostics(output,originals,transport.diagnostics());originals.set("dispatch",saveDispatch(output,read.original()));
                    if(!(read instanceof NativeGameTransport.GuiWindowReceived received))
                        throw new IOException("actual named-window result unavailable; original retained, no retry: "+((NativeGameTransport.GuiWindowReadUnavailable)read).reason());
                    received.requireOriginal(transport,received.validUntil());var ack=received.original();
                    var custody=ack.custody().orElseThrow(()->new IOException("actual named-window custody unavailable"));custody.verify(ack);
                    if(!custody.session().equals(actualSession))throw new IOException("named-window query crossed its original Core session");
                    var frame=received.frame();requireGuiWindowSelection(plan,frame);
                    result.put("core_request_id",before.original().requestId()).put("request_id",ack.requestId()).put("observed_at_utc",custody.responseReceived().observedAt().toString());
                    result.set("session",session(actualSession));result.set("gui_window_frame",FullJsonTree.parse(GuiWindowFramePublicCodec.encode(frame).bytes(),FullJsonTree.MAXIMUM_BYTES));
                    result.put("tree_source_available",frame instanceof GuiWindowFrame.Partial).put("window_available",frame.windowAvailable());
                } else if(guiRootIndex) {
                    stage="ONE_ROOT_INDEX_CORE_SOURCE_READ";result.put("read_calls",1);
                    var coreRead=transport.readCoreFrameReceived(deadline);
                    Path coreOutput=Files.createDirectory(output.resolve("core-before-root-index"));
                    ObjectNode coreOriginals=StrictJson.object();archiveNaturalDiagnostics(coreOutput,coreOriginals,transport.diagnostics());
                    originals.set("core_natural",coreOriginals);originals.set("core_dispatch",saveDispatch(coreOutput,coreRead.original()));
                    if(!(coreRead instanceof NativeGameTransport.CoreReceived before))
                        throw new IOException("actual root-index Core source unavailable; original retained, no retry: "+((NativeGameTransport.CoreReadUnavailable)coreRead).reason());
                    var coreCustody=before.original().custody().orElseThrow(()->new IOException("root-index Core custody unavailable"));coreCustody.verify(before.original());
                    var actualSession=coreCustody.session();
                    if(!actualSession.game().equals(owner.generation())||!actualSession.machineId().equals(owner.machineId())
                            ||!actualSession.sessionId().equals(owner.sessionId())||!transport.diagnostics().session().filter(actualSession::equals).isPresent()
                            ||hello.original().pid()!=owner.generation().pid()||!hello.original().connectionGeneration().equals(actualSession.connectionGeneration()))
                        throw new IOException("root-index Core crossed its actual owner Game/session/connection");
                    Instant queryDeadline=before.validUntil().isBefore(deadline)?before.validUntil():deadline;
                    before.requireOriginal(transport,queryDeadline);
                    stage="ONE_GUI_ROOT_INDEX_READ";result.put("read_calls",2);
                    var read=transport.readGuiRootIndexReceived(before,queryDeadline);
                    archiveNaturalDiagnostics(output,originals,transport.diagnostics());originals.set("dispatch",saveDispatch(output,read.original()));
                    if(!(read instanceof NativeGameTransport.GuiRootIndexReceived received))
                        throw new IOException("actual root-index result unavailable; original retained, no retry: "+((NativeGameTransport.GuiRootIndexReadUnavailable)read).reason());
                    received.requireOriginal(transport,received.validUntil());var ack=received.original();
                    var custody=ack.custody().orElseThrow(()->new IOException("actual root-index custody unavailable"));custody.verify(ack);
                    if(!custody.session().equals(actualSession))throw new IOException("root-index query crossed its original Core session");
                    var frame=received.frame();requireGuiRootIndexSelection(plan,frame);
                    result.put("core_request_id",before.original().requestId()).put("request_id",ack.requestId()).put("observed_at_utc",custody.responseReceived().observedAt().toString());
                    result.set("session",session(actualSession));result.set("gui_root_index_frame",FullJsonTree.parse(GuiRootIndexFramePublicCodec.encode(frame).bytes(),FullJsonTree.MAXIMUM_BYTES));
                    result.put("root_index_available",frame instanceof GuiRootIndexFrame.Partial);
                } else if(dateAdvance){
                    runDateAdvance(transport,owner,plan,output,deadline,maximumStatusPolls,statusPollMillis,result,originals);
                } else if(personalCash) {
                    stage="ONE_PERSONAL_CASH_FULL_SOURCE";
                    var read=transport.readFullClockFrameReceived(deadline);
                    archiveNaturalDiagnostics(output,originals,transport.diagnostics());
                    originals.set("full_dispatch",saveDispatch(output,read.original().dispatch()));
                    if(!(read instanceof NativeGameTransport.FullClockReceived before))
                        throw new IOException("actual personal cash Full source unavailable; original retained, no retry: "+((NativeGameTransport.FullClockReadUnavailable)read).reason());
                    var source=before.original().acknowledgement().custody().orElseThrow(()->new IOException("actual cash Full custody unavailable"));
                    source.verify(before.original().acknowledgement());var actualSession=source.session();
                    if(!actualSession.game().equals(owner.generation())||!actualSession.machineId().equals(owner.machineId())
                            ||!actualSession.sessionId().equals(owner.sessionId())||!transport.diagnostics().session().filter(actualSession::equals).isPresent())
                        throw new IOException("personal cash Full crossed its owner Game/session");
                    originals.set("full_before_cash",saveFrame(output,before.frame()));
                    Instant cashDeadline=before.validUntil().isBefore(deadline)?before.validUntil():deadline;
                    stage="ONE_PERSONAL_CASH_READ";
                    var cash=transport.readPersonalCashReceived(before,cashDeadline);
                    Path cashOutput=Files.createDirectory(output.resolve("cash"));
                    originals.set("cash_dispatch",saveDispatch(cashOutput,cash.original()));
                    archiveNaturalDiagnostics(cashOutput,originals,transport.diagnostics());
                    if(!(cash instanceof NativeGameTransport.PersonalCashReceived received))
                        throw new IOException("actual personal cash unavailable; original retained, no retry: "+((NativeGameTransport.PersonalCashReadUnavailable)cash).reason());
                    received.requireOriginal(transport,cashDeadline);
                    result.set("session",session(actualSession));
                    result.put("full_read_request_id",before.original().acknowledgement().requestId()).put("request_id",received.original().requestId())
                            .put("snapshot_id",before.frame().snapshotId()).put("native_revision",before.frame().nativeRevision());
                    result.set("personal_cash",FullJsonTree.parse(received.cash().toJson(),FullJsonTree.MAXIMUM_BYTES));
                } else if(fullClock) {
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
                    requirePersonalGoldSelection(plan,frame);
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
        String archivedStatus = checkpointSave?"ARCHIVED_CURRENT_CORE_CHECKPOINT_MATERIAL_ENDPOINT_RELEASED":guiControls?"ARCHIVED_NATIVE_GUI_CONTROLS_DATA_ENDPOINT_RELEASED":riteDraftCosts?"ARCHIVED_NATIVE_RITE_DRAFT_COSTS_DATA_ENDPOINT_RELEASED":guiWindow?"ARCHIVED_NATIVE_GUI_WINDOW_DATA_ENDPOINT_RELEASED":guiRootIndex?"ARCHIVED_NATIVE_GUI_ROOT_INDEX_DATA_ENDPOINT_RELEASED":dateAdvance?"ARCHIVED_NATIVE_DATE_SENTINEL_ADVANCE_ENDPOINT_RELEASED":personalCash?"ARCHIVED_NATIVE_PERSONAL_CASH_DATA_ENDPOINT_RELEASED":fullClock?"ARCHIVED_NATIVE_FULL_CLOCK_SUBMISSION_ENDPOINT_RELEASED":actorFoundation?"ARCHIVED_NATIVE_ACTOR_FOUNDATION_DATA_ENDPOINT_RELEASED":personalGold?"ARCHIVED_NATIVE_PERSONAL_GOLD_DATA_ENDPOINT_RELEASED":applicationExit?"ARCHIVED_NATIVE_APPLICATION_EXIT_REQUEST_ENDPOINT_RELEASED":controlStep!=null?"ARCHIVED_NATIVE_CORE_CONTROL_SUBMISSION_ENDPOINT_RELEASED":corePrefixOnly ? "ARCHIVED_NATIVE_CORE_PREFIX_DATA_ENDPOINT_RELEASED" : "ARCHIVED_NATIVE_READ_DATA_ENDPOINT_RELEASED";
        result.put("status", archivedStatus).put("completed_at_utc", Instant.now().toString());
        ObjectNode published = write(output, "summary.json", FullJsonTree.encode(result, FullJsonTree.MAXIMUM_BYTES));
        System.out.println(StrictJson.object().put("schema", "xar.native-owner-snapshot-stage/v1")
                .put("status", archivedStatus).put("at_utc", Instant.now().toString()).set("summary", published));
    }

    private static void runCoreCheckpoint(NativeGameTransport transport,GameSupervisorControl.Descriptor owner,NativeLaunchPlan plan,
            ObjectNode config,Path output,Instant deadline,ObjectNode result,ObjectNode originals)throws IOException,InterruptedException {
        if(!Instant.now().isBefore(deadline))throw new IOException("Original Game/checkpoint deadline expired; no extension");
        Path checkpoint=plan.profileDirectory().resolve("save games").resolve(CurrentCoreCheckpointSave.FILENAME);
        Path archive=Path.of(StrictJson.text(config.get("checkpoint_archive_path"))).toAbsolutePath().normalize();
        long maximumBytes=StrictJson.integer(config.get("maximum_checkpoint_bytes"),1,1L<<30);
        int observations=Math.toIntExact(StrictJson.integer(config.get("checkpoint_observation_attempts"),1,64));
        long pollMillis=StrictJson.integer(config.get("checkpoint_poll_interval_ms"),100,5000);
        java.util.Optional<FileWitness> previousSource=java.util.Optional.empty(),previousArchive=java.util.Optional.empty();
        if(config.has("previous_checkpoint_source")) {
            previousSource=java.util.Optional.of(ControlBuild.strictMapper().treeToValue(config.get("previous_checkpoint_source"),FileWitness.class));
            previousArchive=java.util.Optional.of(ControlBuild.strictMapper().treeToValue(config.get("previous_checkpoint_archive"),FileWitness.class));
        }
        var files=new NativeCheckpointFiles();
        stage="CHECKPOINT_PHYSICAL_PREFLIGHT";
        var baseline=CurrentCoreCheckpointArchive.preflight(files,checkpoint,archive,maximumBytes,previousSource,previousArchive);
        if(baseline.isPresent())result.set("checkpoint_baseline",ControlBuild.strictMapper().valueToTree(baseline.orElseThrow()));
        else result.putNull("checkpoint_baseline");
        stage="ONE_ACTUAL_CORE_BEFORE_CHECKPOINT";
        var read=transport.readCoreFrameReceived(deadline);Path beforeOutput=Files.createDirectory(output.resolve("core-before-save"));
        originals.set("core_dispatch",saveDispatch(beforeOutput,read.original()));
        if(!(read instanceof NativeGameTransport.CoreReceived before))throw new IOException("Actual current Core unavailable before checkpoint; no SAVE");
        var custody=before.original().custody().orElseThrow(()->new IOException("Original Core custody missing"));custody.verify(before.original());
        if(!custody.session().game().equals(owner.generation())||!custody.session().machineId().equals(owner.machineId())
                ||!custody.session().sessionId().equals(owner.sessionId()))throw new IOException("Core checkpoint crossed actual owner Game/session");
        Instant controlDeadline=before.validUntil().isBefore(deadline)?before.validUntil():deadline;
        var prepared=transport.prepareCurrentCoreCheckpoint(before,controlDeadline);
        stage="ARCHIVE_ORIGINAL_CHECKPOINT_INTENT";
        ObjectNode intent=StrictJson.object().put("schema","xar.current-core-checkpoint-intent/v1").put("request_id",prepared.requestId())
                .put("original_deadline_utc",prepared.deadline().toString()).put("original_Core_request_id",before.original().requestId())
                .put("source_date_raw",prepared.sourceDateRaw()).put("save_name",CurrentCoreCheckpointSave.SAVE_NAME)
                .put("physical_filename",CurrentCoreCheckpointSave.FILENAME).put("physical_save_confirmed",false);
        intent.set("original_outbound",write(output,"save-original-request.packet",prepared.originalPacket().value()));
        originals.set("save_intent",write(output,"save-intent.json",FullJsonTree.encode(intent,SMALL)));
        stage="ONE_CURRENT_CORE_CHECKPOINT_SUBMISSION";
        var outcome=transport.submitCurrentCoreCheckpoint(prepared);Path saveOutput=Files.createDirectory(output.resolve("save"));
        originals.set("save_dispatch",saveDispatch(saveOutput,outcome));
        result.put("save_request_id",outcome.requestId()).put("save_calls",1).put("save_dispatch_class",outcome.getClass().getSimpleName())
                .put("save_deadline_utc",prepared.deadline().toString()).put("source_date_raw",prepared.sourceDateRaw());
        var uncertain=transport.originalIndeterminateCoreAcknowledgement(outcome.requestId());
        if(uncertain.isPresent())originals.set("save_indeterminate_ACK",saveDispatch(Files.createDirectory(saveOutput.resolve("indeterminate")),uncertain.orElseThrow()));
        archiveNaturalDiagnostics(output,originals,transport.diagnostics());
        if(!(outcome instanceof NativeActionPort.AckReceived ack))throw new IOException("Checkpoint did not return qualified submitted ACK; original retained, no replay");
        var nativeResult=CurrentCoreCheckpointSaveResult.decodeOutcome(ack);
        result.put("Native_physical_save_confirmed",false).put("native_checkpoint_status",nativeResult.status().wire());
        if(!nativeResult.accepted())throw new IOException("Native checkpoint not submitted; no physical SAVE credit");
        stage="OBSERVE_CHANGED_PHYSICAL_CHECKPOINT_AND_ARCHIVE";
        var material=CurrentCoreCheckpointArchive.observeAndCopyChanged(files,checkpoint,baseline,archive,deadline,maximumBytes,observations,pollMillis);
        result.set("checkpoint_source",ControlBuild.strictMapper().valueToTree(material.source()));
        result.set("checkpoint_immutable_archive",ControlBuild.strictMapper().valueToTree(material.archive()));
        result.set("inspect_save_pin",material.archive().reference().toJson());
        result.put("changed_physical_material_observed",true).put("archive_is_copy_not_another_SAVE",true)
                .put("saved_date_or_business_inspection_verified",false).put("physical_save_confirmed",false);
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
    private static void runDateAdvance(NativeGameTransport transport,GameSupervisorControl.Descriptor owner,NativeLaunchPlan plan,
            Path output,Instant deadline,int maximumStatusPolls,long statusPollMillis,ObjectNode result,ObjectNode originals)throws IOException,InterruptedException{
        result.put("schema","xar.native-owner-date-sentinel-advance/v1").put("mode","date_sentinel_advance_one_day")
                .put("one_day_observed",false).put("save_confirmed",false).put("driver_adopted",false);
        Instant parentDeadline=deadline.isBefore(plan.sources().review().expiresAt())?deadline:plan.sources().review().expiresAt();
        if(!Instant.now().isBefore(parentDeadline))throw new IOException("original Date source window expired before its Full READ");
        stage="DATE_ORIGINAL_FULL_READ";
        var read=transport.readDateSentinelArmReceived(parentDeadline);
        originals.set("dispatch",saveDispatch(output,read.original().dispatch()));
        archiveNaturalDiagnostics(output,originals,transport.diagnostics());
        if(!(read instanceof NativeGameTransport.DateArmReceived before))
            throw new IOException("actual Date Full source unavailable; no retry: "+((NativeGameTransport.DateArmUnavailable)read).reason());
        var custody=before.original().acknowledgement().custody().orElseThrow(()->new IOException("actual Date Full custody unavailable"));
        custody.verify(before.original().acknowledgement());
        if(!custody.session().game().equals(owner.generation())||!custody.session().sessionId().equals(owner.sessionId())
                ||!custody.session().machineId().equals(owner.machineId())
                ||transport.diagnostics().session().filter(custody.session()::equals).isEmpty())
            throw new IOException("Date Full source crossed the actual held owner");
        var initial=StrictJson.parse(before.frame().state().bytes());
        int start=Math.toIntExact(StrictJson.integer(initial.get("date_raw"),1,Integer.MAX_VALUE));
        int target=Math.addExact(start,24);
        int speed=Math.toIntExact(StrictJson.integer(initial.get("speed"),1,5));
        String step=ClockStatusRead.ARM_PREFIX+start+"-to-"+target+"-speed-"+speed+"-mode-terminal-a-0";
        var prepared=FullSnapshotDateSentinelArm.request(step,before.frame().snapshotId(),before.frame().nativeRevision(),before.activeDeadline());
        originals.set("date_before",saveFrame(output,before.frame()));
        result.put("starting_date_raw",start).put("target_date_raw",target).put("speed",speed)
                .put("original_advance_deadline_utc",before.activeDeadline().toString()).put("fresh_full_cutoff_utc",before.validUntil().toString());
        result.set("prepared_arm_fields",StrictJson.parse(prepared.additionalFields().bytes()));
        stage="ONE_DATE_ARM";
        var arm=transport.submitDateSentinelArm(before,prepared,before.validUntil());
        Path armOutput=Files.createDirectory(output.resolve("arm"));originals.set("arm",saveDispatch(armOutput,arm));
        archiveUncertainDateAck(transport,armOutput,originals,"arm_uncertain_ack",arm);
        if(!(arm instanceof NativeActionPort.AckReceived armAck))throw new IOException("Date ARM not confirmed; preserve original, never replay: "+arm.getClass().getSimpleName());
        var armResult=DateSentinelArmResult.decode(armAck,step);
        if(armResult.disposition()!=DateSentinelArmResult.Disposition.ARMED)throw new IOException("Date ARM did not prove an active original generation");
        var armed=armResult.status().orElseThrow();result.put("sentinel_generation",armed.generation().decimal());
        stage="FRESH_FULL_BEFORE_RESUME";
        var resumeRead=transport.readFullClockFrameReceived(parentDeadline);
        Path resumeOutput=Files.createDirectory(output.resolve("resume"));
        originals.set("resume_full_dispatch",saveDispatch(resumeOutput,resumeRead.original().dispatch()));
        if(!(resumeRead instanceof NativeGameTransport.FullClockReceived resumeBefore))throw new IOException("fresh paused Full before resume unavailable; no resume dispatched");
        requireDateFrame(initial,resumeBefore.frame(),start,speed);originals.set("resume_before",saveFrame(resumeOutput,resumeBefore.frame()));
        Instant resumeDeadline=resumeBefore.validUntil().isBefore(parentDeadline)?resumeBefore.validUntil():parentDeadline;
        var resumeRequest=FullSnapshotClockControl.request("resume-map",resumeBefore.frame().snapshotId(),resumeBefore.frame().nativeRevision(),resumeDeadline);
        stage="ONE_MATCHING_GENERATION_RESUME";
        var resumed=transport.submitFullClockControl(resumeBefore,resumeRequest,resumeDeadline);
        Path resumeCommand=Files.createDirectory(resumeOutput.resolve("command"));originals.set("resume",saveDispatch(resumeCommand,resumed));
        archiveUncertainDateAck(transport,resumeCommand,originals,"resume_uncertain_ack",resumed);
        if(!(resumed instanceof NativeActionPort.AckReceived resumeAck)
                ||FullSnapshotClockControlResult.decode(resumeAck,"resume-map").disposition()!=FullSnapshotClockControlResult.Disposition.SUBMITTED)
            throw new IOException("Date resume not confirmed as submitted; no retry or follow-on action");
        stage="BOUNDED_SAME_GENERATION_DATE_STATUS";
        org.xar.ck3.control.reconciliation.LateOutcome.Status terminal=null;
        for(int i=0;i<maximumStatusPolls;i++){
            if(!Instant.now().isBefore(parentDeadline))throw new IOException("original Date advance deadline expired; no lease refresh");
            Path pollOutput=Files.createDirectory(output.resolve(String.format(java.util.Locale.ROOT,"status-%03d",i)));
            var observed=transport.readDateSentinelStatus(before,parentDeadline);originals.set("status_"+i,saveDispatch(pollOutput,observed));
            if(!(observed instanceof NativeActionPort.AckReceived statusAck))throw new IOException("actual Date status unavailable; original retained, no retry");
            var status=ClockStatusRead.decode(statusAck);result.put("status_polls",i+1).put("last_sentinel_state",status.state().name());
            if(status.state()!=org.xar.ck3.control.reconciliation.LateOutcome.State.ARMED){terminal=status;break;}
            long remaining=Duration.between(Instant.now(),parentDeadline).toMillis();
            if(remaining<=0)throw new IOException("original Date lease expired while awaiting its actual terminal");
            Thread.sleep(Math.min(statusPollMillis,remaining));
        }
        if(terminal==null||terminal.state()!=org.xar.ck3.control.reconciliation.LateOutcome.State.TRIGGERED
                ||!terminal.pauseObserved()||terminal.abnormal()||terminal.triggerDateRaw()!=target||terminal.overshootDays()!=0
                ||!terminal.triggerReasons().contains("date_deadline"))
            throw new IOException("Date status did not prove the requested paused one-day terminal");
        stage="INDEPENDENT_PAUSED_FULL_AFTER_DATE";
        var post=transport.readFullClockFrameReceived(parentDeadline);
        Path afterOutput=Files.createDirectory(output.resolve("after"));originals.set("after_dispatch",saveDispatch(afterOutput,post.original().dispatch()));
        if(!(post instanceof NativeGameTransport.FullClockReceived after))throw new IOException("independent paused Full after Date unavailable");
        requireDateFrame(initial,after.frame(),target,speed);originals.set("date_after",saveFrame(afterOutput,after.frame()));
        stage="ORIGINAL_GENERATION_PAUSED_CLEANUP";
        var cleanup=transport.cancelDateSentinel(before,parentDeadline);
        Path cleanupOutput=Files.createDirectory(output.resolve("cleanup"));originals.set("cleanup",saveDispatch(cleanupOutput,cleanup));
        archiveUncertainDateAck(transport,cleanupOutput,originals,"cleanup_uncertain_ack",cleanup);
        if(!(cleanup instanceof NativeActionPort.AckReceived cleanupAck))throw new IOException("Date cleanup not confirmed; original retained, never replay");
        var idle=AdvancePrimitives.acknowledgedSentinel(cleanupAck,ClockStatusRead.CANCEL_PREFIX+armed.generation().decimal());
        if(!idle.generation().equals(armed.generation())||!idle.equals(terminal))
            throw new IOException("Date cleanup crossed or failed its original generation");
        result.put("one_day_observed",true).put("after_date_raw",target).put("date_sentinel_cleanup_idle",false)
                .put("terminal_generation_read_only_confirmed",true);
    }
    static void requireDateFrame(JsonNode initial,NativeObservationPort.ObservedFrame actual,int date,int speed)throws IOException{
        var current=StrictJson.parse(actual.state().bytes());
        if(StrictJson.integer(current.get("date_raw"),1,Integer.MAX_VALUE)!=date||StrictJson.integer(current.get("speed"),1,5)!=speed
                ||!org.xar.ck3.control.contracts.NativeCharacterId.fromJson(initial.path("played_character").get("character_id"))
                .equals(org.xar.ck3.control.contracts.NativeCharacterId.fromJson(current.path("played_character").get("character_id"))))
            throw new IOException("Date Full crossed original actor, requested date or speed");
        StrictJson.trueValue(current.get("paused"));StrictJson.trueValue(current.get("map_ready"));StrictJson.trueValue(current.path("played_character").get("alive"));
    }
    private static void archiveUncertainDateAck(NativeGameTransport transport,Path output,ObjectNode originals,String key,NativeActionPort.DispatchOutcome outcome)throws IOException{
        if(outcome instanceof NativeActionPort.Unknown unknown){
            var original=transport.originalIndeterminateFullClockAcknowledgement(unknown.requestId());
            if(original.isPresent())originals.set(key,saveDispatch(Files.createDirectory(output.resolve("original-uncertain-ack")),original.orElseThrow()));
        }
    }
    enum ObservationMode { SAVED_FULL,SAVED_CORE,MENU_CORE,CORE_CONTROL,CORE_EXIT,CORE_CHECKPOINT_SAVE,PERSONAL_GOLD,ACTOR_FOUNDATION,FULL_CLOCK,DATE_ADVANCE,PERSONAL_CASH,GUI_ROOT_INDEX,GUI_WINDOW,RITE_DRAFT_COSTS,GUI_CONTROLS_V2 }
    static void requireGuiRootIndexSelection(NativeLaunchPlan plan,GuiRootIndexFrame frame)throws IOException {
        Objects.requireNonNull(plan);Objects.requireNonNull(frame);
        if(!frame.build().executableSha256().equalsIgnoreCase(plan.sources().review().gameExecutable().sha256())
                ||!frame.build().coreFrameAdapterId().equals(plan.adapterId()))
            throw new IOException("root-index frame differs from the owner's selected exact executable or adapter");
    }
    static void requireGuiWindowSelection(NativeLaunchPlan plan,GuiWindowFrame frame)throws IOException {
        Objects.requireNonNull(plan);Objects.requireNonNull(frame);
        if(!frame.build().executableSha256().equalsIgnoreCase(plan.sources().review().gameExecutable().sha256())
                ||!frame.build().coreFrameAdapterId().equals(plan.adapterId()))
            throw new IOException("named-window frame differs from the owner's selected exact executable or adapter");
    }
    static void requireRiteDraftCostsSelection(NativeLaunchPlan plan,RiteDraftCostsFrameV2 frame)throws IOException {
        Objects.requireNonNull(plan);Objects.requireNonNull(frame);
        if(!frame.build().executableSha256().equalsIgnoreCase(plan.sources().review().gameExecutable().sha256())
                ||!frame.build().coreFrameAdapterId().equals(plan.adapterId()))
            throw new IOException("rite-draft-costs frame differs from the owner's selected exact executable or adapter");
    }
    /** Source selection DATA only; the caller still requires its actual owner, session and ACK custody. */
    static void requirePersonalGoldSelection(NativeLaunchPlan plan,PersonalGoldFrame frame)throws IOException {
        Objects.requireNonNull(plan);Objects.requireNonNull(frame);
        if(!frame.build().executableSha256().equalsIgnoreCase(plan.sources().review().gameExecutable().sha256())
                ||!frame.version().adapter().equals(plan.adapterId()))
            throw new IOException("personal-gold frame differs from the actual owner's selected executable or adapter");
    }

    static void requireGuiControlsSelection(NativeLaunchPlan plan,GuiControlsFrameV2 frame)throws IOException {
        if(!frame.build().executableSha256().equalsIgnoreCase(plan.sources().review().gameExecutable().sha256())||!frame.build().coreFrameAdapterId().equals(plan.adapterId()))throw new IOException("current controls source differs from actual owner selection");
    }
    static ObservationMode observationMode(ObjectNode config) {
        String schema=StrictJson.text(config.get("schema"));
        if(schema.equals("xar.native-owner-snapshot-config/v14")) {
            StrictJson.require("current_core_checkpoint_save".equals(StrictJson.text(config.get("mode")))
                    &&!config.has("core_prefix_only")&&!config.has("control_step")&&!config.has("maximum_status_polls")&&!config.has("status_poll_interval_ms")
                    &&!config.has("window_name")&&!config.has("expected_source_rite_id")&&!config.has("expected_core")&&!config.has("connection_generation"),
                    "Explicit narrow current checkpoint mode with actual receiver Core required");
            StrictJson.require(Path.of(StrictJson.text(config.get("checkpoint_archive_path"))).isAbsolute(),"Absolute new checkpoint archive path required");
            StrictJson.integer(config.get("maximum_checkpoint_bytes"),1,1L<<30);
            StrictJson.integer(config.get("checkpoint_observation_attempts"),1,64);
            StrictJson.integer(config.get("checkpoint_poll_interval_ms"),100,5000);
            StrictJson.require(config.has("previous_checkpoint_source")==config.has("previous_checkpoint_archive"),"Previous exact source/archive must be supplied together");
            if(config.has("previous_checkpoint_source"))StrictJson.require(config.get("previous_checkpoint_source").isObject()
                    &&config.get("previous_checkpoint_archive").isObject(),"Previous physical witness objects cannot be null or scalar");
            return ObservationMode.CORE_CHECKPOINT_SAVE;
        }
        for(String field:List.of("checkpoint_archive_path","maximum_checkpoint_bytes","checkpoint_observation_attempts","checkpoint_poll_interval_ms","previous_checkpoint_source","previous_checkpoint_archive"))
            StrictJson.require(!config.has(field),"Checkpoint material fields belong only to explicit v14 mode");
        if(schema.equals("xar.native-owner-snapshot-config/v13")){
            StrictJson.require(!config.has("core_prefix_only")&&!config.has("control_step")&&!config.has("maximum_status_polls")&&!config.has("status_poll_interval_ms")
                    &&!config.has("expected_core")&&!config.has("connection_generation")&&!config.has("query_generation")&&!config.has("widget_id")&&"scripted_widget_controls".equals(StrictJson.text(config.get("mode"))),"explicit readonly current controls mode required");
            var window=GuiControlsFrameV2.Window.wire(StrictJson.text(config.get("window_name")));
            if(window==GuiControlsFrameV2.Window.RITE)StrictJson.integer(config.get("expected_source_rite_id"),0,0xffff_fffeL);
            else StrictJson.require(!config.has("expected_source_rite_id"),"Faith query cannot borrow a Rite selector");
            return ObservationMode.GUI_CONTROLS_V2;
        }
        if(schema.equals("xar.native-owner-snapshot-config/v12")){
            StrictJson.require(!config.has("window_name")&&!config.has("core_prefix_only")&&!config.has("control_step")&&!config.has("maximum_status_polls")
                    &&!config.has("status_poll_interval_ms")&&!config.has("expected_core")&&!config.has("connection_generation")
                    &&"rite_draft_costs".equals(StrictJson.text(config.get("mode"))),"explicit current draft Can/cost read-only mode required");
            StrictJson.integer(config.get("expected_source_rite_id"),0,0xffff_fffeL);return ObservationMode.RITE_DRAFT_COSTS;
        }
        StrictJson.require(!config.has("expected_source_rite_id"),"source Rite selector belongs only to explicit v12 draft read");
        if(schema.equals("xar.native-owner-snapshot-config/v11")){
            StrictJson.require(!config.has("core_prefix_only")&&!config.has("control_step")&&!config.has("maximum_status_polls")
                    &&!config.has("status_poll_interval_ms")&&!config.has("expected_core")&&!config.has("connection_generation")
                    &&"scripted_gui_window".equals(StrictJson.text(config.get("mode"))),"explicit read-only named-window mode required; Core cannot come from config");
            GuiWindowFrame.windowName(StrictJson.text(config.get("window_name")));return ObservationMode.GUI_WINDOW;
        }
        StrictJson.require(!config.has("window_name"),"window_name belongs only to explicit v11 named-window query");
        if(schema.equals("xar.native-owner-snapshot-config/v10")){
            StrictJson.require(!config.has("core_prefix_only")&&!config.has("control_step")&&!config.has("maximum_status_polls")
                    &&!config.has("status_poll_interval_ms")&&!config.has("expected_core")&&!config.has("connection_generation")
                    &&"scripted_gui_root_index".equals(StrictJson.text(config.get("mode"))),"explicit read-only current root-index mode required; Core cannot come from config");
            return ObservationMode.GUI_ROOT_INDEX;
        }
        if(schema.equals("xar.native-owner-snapshot-config/v9")){
            StrictJson.require(!config.has("core_prefix_only")&&!config.has("control_step")&&!config.has("maximum_status_polls")
                    &&!config.has("status_poll_interval_ms")&&"personal_cash_current".equals(StrictJson.text(config.get("mode"))),
                    "explicit read-only personal cash mode required");
            return ObservationMode.PERSONAL_CASH;
        }
        if(schema.equals("xar.native-owner-snapshot-config/v8")){
            StrictJson.require(!config.has("core_prefix_only")&&!config.has("control_step")
                    &&"date_sentinel_advance_one_day".equals(StrictJson.text(config.get("mode"))),"explicit Date-only one-day mode required");
            StrictJson.integer(config.get("maximum_status_polls"),1,128);
            StrictJson.integer(config.get("status_poll_interval_ms"),100,5000);
            return ObservationMode.DATE_ADVANCE;
        }
        StrictJson.require(!config.has("maximum_status_polls")&&!config.has("status_poll_interval_ms"),"Date polling fields require their explicit versioned mode");
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
