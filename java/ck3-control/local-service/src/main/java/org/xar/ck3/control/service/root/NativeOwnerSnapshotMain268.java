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
import org.xar.ck3.control.contracts.ExactCk3Build;
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
import org.xar.ck3.control.nativebridge.capabilities.registry.FrontendMenuFrameV1;
import org.xar.ck3.control.nativebridge.capabilities.registry.FrontendMenuFrameV1PublicCodec;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFramePublicCodec;
import org.xar.ck3.control.nativebridge.capabilities.registry.DateAdvanceFrameV1;
import org.xar.ck3.control.nativebridge.capabilities.registry.DateAdvanceFrameV1PublicCodec;
import org.xar.ck3.control.nativebridge.capabilities.registry.GuiRootIndexFrame;
import org.xar.ck3.control.nativebridge.capabilities.registry.GuiRootIndexFramePublicCodec;
import org.xar.ck3.control.nativebridge.capabilities.registry.GuiWindowFrame;
import org.xar.ck3.control.nativebridge.capabilities.registry.GuiWindowFramePublicCodec;
import org.xar.ck3.control.nativebridge.capabilities.registry.RiteDraftCostsFrameV2;
import org.xar.ck3.control.nativebridge.capabilities.registry.RiteDraftCostsFrameV2PublicCodec;
import org.xar.ck3.control.nativebridge.capabilities.registry.RiteDoctrineFrameV1;
import org.xar.ck3.control.nativebridge.capabilities.registry.RiteDoctrineFrameV1PublicCodec;
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
import org.xar.ck3.control.nativebridge.CurrentAubObserverFixtureResult;
import org.xar.ck3.control.nativebridge.CurrentDecisionsClose;
import org.xar.ck3.control.nativebridge.CurrentDecisionsCloseResult;
import org.xar.ck3.control.nativebridge.CurrentCourtierControls;
import org.xar.ck3.control.nativebridge.CurrentCourtierControlsSource;
import org.xar.ck3.control.nativebridge.CurrentCourtierControlsResult;
import org.xar.ck3.control.nativebridge.CurrentXqolThreshold;
import org.xar.ck3.control.nativebridge.CurrentXqolThresholdSource;
import org.xar.ck3.control.nativebridge.CurrentXqolThresholdResult;
import org.xar.ck3.control.nativebridge.CurrentXqolPrompt;
import org.xar.ck3.control.nativebridge.CurrentXqolPromptSource;
import org.xar.ck3.control.nativebridge.CurrentXqolPromptResult;
import org.xar.ck3.control.nativebridge.CurrentCuratedDecisions;
import org.xar.ck3.control.nativebridge.CurrentCuratedDecisionsSource;
import org.xar.ck3.control.nativebridge.CurrentCuratedDecisionsResult;
import org.xar.ck3.control.nativebridge.CurrentFullscreenEvent;
import org.xar.ck3.control.nativebridge.CurrentFullscreenEventResult;
import org.xar.ck3.control.nativebridge.CurrentFullscreenEventSource;

import org.xar.ck3.control.nativebridge.CurrentLetter;
import org.xar.ck3.control.nativebridge.CurrentLetterResult;
import org.xar.ck3.control.nativebridge.CurrentLetterSet;
import org.xar.ck3.control.nativebridge.CurrentLetterSetResult;
import org.xar.ck3.control.nativebridge.CurrentLetterSource;
import org.xar.ck3.control.nativebridge.CurrentDjcDeclarationUi;
import org.xar.ck3.control.nativebridge.CurrentDjcDeclarationUiSource;
import org.xar.ck3.control.nativebridge.CurrentDjcDeclarationUiResult;
import org.xar.ck3.control.nativebridge.CurrentDjcTargetWarQueryResult;
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
                "overall_timeout_seconds", "read_timeout_seconds", "maximum_frames_per_operation"), Set.of("core_prefix_only", "mode", "control_step", "maximum_status_polls", "status_poll_interval_ms", "window_name", "expected_source_rite_id", "checkpoint_archive_path", "maximum_checkpoint_bytes", "checkpoint_observation_attempts", "checkpoint_poll_interval_ms", "previous_checkpoint_source", "previous_checkpoint_archive", "navigation_action", "rite_action", "maximum_confirmation_polls", "target_character_id", "cb_key", "tuple_intent", "maximum_warning_polls", "warning_poll_interval_ms", "instance_id", "decision_key", "target_threshold", "product", "control"));
        ObservationMode observationMode=observationMode(config);
        boolean currentDecisionsClose=observationMode==ObservationMode.CURRENT_DECISIONS_CLOSE_QUERY||observationMode==ObservationMode.CURRENT_DECISIONS_CLOSE;
        CurrentDecisionsClose.Action decisionsCloseAction=currentDecisionsClose?currentDecisionsCloseAction(config):null;
        boolean currentCourtierControls=observationMode==ObservationMode.CURRENT_COURTIER_CREATOR_CONTROLS_QUERY||observationMode==ObservationMode.CURRENT_COURTIER_CREATOR_CONTROL_EXECUTE;
        CourtierControlsConfig courtierConfig=currentCourtierControls?currentCourtierControlsConfig(config):null;
        boolean currentXqolThreshold=observationMode==ObservationMode.CURRENT_XQOL_CONVERSION_THRESHOLD_QUERY||observationMode==ObservationMode.CURRENT_XQOL_CONVERSION_THRESHOLD_SET;
        XqolThresholdConfig thresholdConfig=currentXqolThreshold?currentXqolThresholdConfig(config):null;
        boolean currentXqolPrompt=observationMode==ObservationMode.CURRENT_XQOL_CONVERSION_PROMPT_QUERY||observationMode==ObservationMode.CURRENT_XQOL_CONVERSION_PROMPT_CONFIRM||observationMode==ObservationMode.CURRENT_XQOL_CONVERSION_PROMPT_CANCEL;
        CurrentXqolPrompt.Action xqolPromptAction=currentXqolPrompt?currentXqolPromptAction(config):null;
        boolean currentCuratedDecision=observationMode==ObservationMode.CURRENT_CURATED_DECISIONS_QUERY||observationMode==ObservationMode.CURRENT_CURATED_DECISIONS_OPEN||observationMode==ObservationMode.CURRENT_CURATED_DECISION_DETAIL||observationMode==ObservationMode.CURRENT_CURATED_DECISION_CONFIRM;
        CuratedDecisionConfig curatedConfig=currentCuratedDecision?currentCuratedDecisionConfig(config):null;
        boolean currentFullscreenEvent=observationMode==ObservationMode.CURRENT_FULLSCREEN_EVENT_QUERY||observationMode==ObservationMode.CURRENT_FULLSCREEN_EVENT_ACK_KNOWN_INTRO;
        boolean acknowledgeKnownIntro=observationMode==ObservationMode.CURRENT_FULLSCREEN_EVENT_ACK_KNOWN_INTRO;
        boolean currentLetterSet=observationMode==ObservationMode.CURRENT_LETTER_SET_QUERY||observationMode==ObservationMode.CURRENT_LETTER_SET_REPLY_KNOWN_INSTANCE;
        boolean letterSetReply=observationMode==ObservationMode.CURRENT_LETTER_SET_REPLY_KNOWN_INSTANCE;
        int letterSetInstance=letterSetReply?Math.toIntExact(StrictJson.integer(config.get("instance_id"),1,Integer.MAX_VALUE)):0;
        boolean currentLetter=observationMode==ObservationMode.CURRENT_LETTER_QUERY||observationMode==ObservationMode.CURRENT_LETTER_REPLY_KNOWN;
        boolean knownLetterReply=observationMode==ObservationMode.CURRENT_LETTER_REPLY_KNOWN;
        boolean currentSuccession=observationMode==ObservationMode.CURRENT_SUCCESSION_QUERY||observationMode==ObservationMode.CURRENT_SUCCESSION_CONTINUE;
        boolean continueSuccession=observationMode==ObservationMode.CURRENT_SUCCESSION_CONTINUE;
        boolean currentFrontendMenu=observationMode==ObservationMode.CURRENT_FRONTEND_MENU||observationMode==ObservationMode.CURRENT_FRONTEND_MENU_QUIT;
        boolean currentFrontendQuit=observationMode==ObservationMode.CURRENT_FRONTEND_MENU_QUIT;
        boolean applicationExit=observationMode==ObservationMode.CORE_EXIT;
        boolean checkpointSave=observationMode==ObservationMode.CORE_CHECKPOINT_SAVE;
        boolean djcQuery=observationMode==ObservationMode.CURRENT_DJC_TARGET_QUERY;
        boolean djcCostPreview=observationMode==ObservationMode.CURRENT_DJC_SELECTED_COST_PREVIEW;
        boolean djcSelectedCost=observationMode==ObservationMode.CURRENT_DJC_SELECTED_COST||djcCostPreview;
        boolean djcUiMode=observationMode==ObservationMode.CURRENT_DJC_DECLARATION_UI||observationMode==ObservationMode.CURRENT_DJC_DECLARATION_SUBMIT;
        boolean djcUiSubmit=observationMode==ObservationMode.CURRENT_DJC_DECLARATION_SUBMIT;
        DjcUiConfig declarationConfig=djcSelectedCost?currentDjcSelectedCostConfig(config,djcCostPreview):djcUiMode?currentDjcUiConfig(config,djcUiSubmit):null;
        var djcTarget=djcQuery?org.xar.ck3.control.contracts.NativeCharacterId.fromJson(config.get("target_character_id")):null;
        boolean aubObserver=observationMode==ObservationMode.CURRENT_AUB_OBSERVER_FIXTURE;
        boolean riteDoctrine=observationMode==ObservationMode.RITE_DOCTRINE;
        boolean riteFinalConfirmation=observationMode==ObservationMode.RITE_FINAL_CONFIRMATION;
        int maximumConfirmationPolls=riteFinalConfirmation?Math.toIntExact(StrictJson.integer(config.get("maximum_confirmation_polls"),1,64)):0;
        long confirmationPollMillis=riteFinalConfirmation?StrictJson.integer(config.get("status_poll_interval_ms"),100,5000):0;
        RiteDoctrineFrameV1.Action riteAction=riteDoctrine?RiteDoctrineFrameV1.Action.wire(StrictJson.text(config.get("rite_action"))):null;
        boolean guiNavigation=observationMode==ObservationMode.GUI_NAVIGATION_V2;
        NativeGameTransport.NavigationAction navigationAction=guiNavigation?NativeGameTransport.NavigationAction.valueOf(StrictJson.text(config.get("navigation_action"))):null;
        boolean personalGold=observationMode==ObservationMode.PERSONAL_GOLD;
        boolean actorFoundation=observationMode==ObservationMode.ACTOR_FOUNDATION;
        boolean personalCash=observationMode==ObservationMode.PERSONAL_CASH;
        boolean guiRootIndex=observationMode==ObservationMode.GUI_ROOT_INDEX;
        boolean guiWindow=observationMode==ObservationMode.GUI_WINDOW;
        boolean riteDraftCosts=observationMode==ObservationMode.RITE_DRAFT_COSTS;
        boolean guiControls=observationMode==ObservationMode.GUI_CONTROLS_V2;
        GuiControlsFrameV2.Window controlWindow=guiControls?GuiControlsFrameV2.Window.wire(StrictJson.text(config.get("window_name"))):null;
        long expectedSourceRiteId=(riteFinalConfirmation||riteDoctrine||riteDraftCosts||guiControls&&controlWindow==GuiControlsFrameV2.Window.RITE)?StrictJson.integer(config.get("expected_source_rite_id"),0,0xffff_fffeL):0;
        String requestedWindow=guiWindow?GuiWindowFrame.windowName(StrictJson.text(config.get("window_name"))):null;
        boolean fullClock=observationMode==ObservationMode.FULL_CLOCK;
        boolean dateAdvance=observationMode==ObservationMode.DATE_ADVANCE;
        boolean currentDateAdvance=observationMode==ObservationMode.CURRENT_DATE_ADVANCE;
        int maximumStatusPolls=(dateAdvance||currentDateAdvance)?Math.toIntExact(StrictJson.integer(config.get("maximum_status_polls"),1,128)):0;
        long statusPollMillis=(dateAdvance||currentDateAdvance)?StrictJson.integer(config.get("status_poll_interval_ms"),100,5000):0;
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
        if(currentFrontendMenu) {
            requireCurrentFrontendMenuPlan(plan);
        } else if(observationMode==ObservationMode.MENU_CORE) {
            if(!(plan.load() instanceof NativeLaunchPlan.NewGame))throw new IOException("explicit menu core mode requires its actual NewGame owner plan");
        } else if (!coreCommand&&!personalGold&&!actorFoundation&&!personalCash&&!guiRootIndex&&!guiWindow&&!riteDraftCosts&&!guiControls&&!fullClock&&!dateAdvance&&!currentDateAdvance&&!(plan.load() instanceof NativeLaunchPlan.SavedGame)) throw new IOException("actual owner must retain its SavedGame plan");
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
        if(guiNavigation)result.put("schema","xar.native-owner-literal-navigation/v1").put("mode","current_gui_navigation").put("navigation_action",navigationAction.name())
                .put("activation_calls",0).put("effect_confirmed",false).put("window_open_confirmed",false).put("physical_save_confirmed",false);
        if(checkpointSave)result.put("schema","xar.native-owner-current-core-checkpoint/v1").put("mode","current_core_checkpoint_save")
                .put("physical_save_confirmed",false).put("business_or_ledger_SAVE_credit",false).put("save_calls",0);
        if(currentDateAdvance)result.put("schema","xar.native-owner-current-date-advance/v1").put("mode","current_date_advance")
                .put("machine_id",owner.machineId()).put("steam_build_id","26785313").put("advance_calls",0).put("status_queries",0)
                .put("one_day_observed",false).put("independent_after_core_verified",false).put("original_unknown",false)
                .put("physical_save_confirmed",false).put("business_or_ledger_SAVE_credit",false).put("save_calls",0);
        if(riteFinalConfirmation)result.put("schema","xar.native-owner-current-rite-final-confirmation/v1").put("mode","current_rite_final_confirmation")
                .put("machine_id",owner.machineId()).put("steam_build_id","26785313").put("read_calls",0).put("stage_one_calls",0).put("final_confirmation_calls",0)
                .put("effect_confirmed",false).put("rite_edit_confirmed",false).put("physical_save_confirmed",false).put("business_or_ledger_SAVE_credit",false).put("save_calls",0);
        if(djcQuery)result.put("schema","xar.native-owner-current-djc-target-query/v1").put("mode","current_djc_target_war_query")
                .put("read_calls",0).put("query_available",false).put("target_character_id",djcTarget.value())
                .put("submission_available",false).put("war_submission_attempted",false).put("war_submitted",false).put("physical_save_confirmed",false);
        if(aubObserver)result.put("schema","xar.native-owner-current-aub-observer/v1").put("mode","current_aub_observer_fixture")
                .put("read_calls",0).put("fixture_calls",0).put("observer_markers_confirmed",false).put("business_pass_confirmed",false)
                .put("production_actions_confirmed",false).put("physical_save_confirmed",false);
        if(djcSelectedCost)result.put("schema","xar.native-owner-current-djc-selected-cost/v1").put("mode",djcCostPreview?"current_djc_selected_cost_preview":"current_djc_selected_cost")
                .put("machine_id",owner.machineId()).put("steam_build_id","26785313").put("target_character_id",declarationConfig.target().value()).put("cb_key",declarationConfig.casusBelli().wire())
                .put("read_calls",0).put("native_getter_calls",0).put("query_available",false).put("cost_available",false).put("display_scale_verified",false)
                .putNull("formatted_text").put("open_calls",0).put("select_calls",0).put("send_calls",0).put("accept_calls",0).put("payment_confirmed",false).put("physical_save_confirmed",false);
        if(currentDecisionsClose)result.put("schema","xar.native-owner-current-decisions-close/v1").put("mode",StrictJson.text(config.get("mode")))
                .put("machine_id",owner.machineId()).put("steam_build_id","26785313").put("action",decisionsCloseAction.wire())
                .put("read_calls",0).put("close_calls",0).put("query_available",false).put("close_callback_dispatched",false)
                .put("native_returned",false).put("native_handled",false).put("panels_closed",false)
                .put("new_date_observed",false).put("physical_save_confirmed",false).put("save_calls",0);
        if(currentCourtierControls)result.put("schema","xar.native-owner-current-courtier-controls/v1").put("mode",StrictJson.text(config.get("mode")))
                .put("machine_id",owner.machineId()).put("steam_build_id","26785313").put("action",courtierConfig.action().wire())
                .put("product",courtierConfig.product().wire()).put("control",courtierConfig.control().wire())
                .put("read_calls",0).put("execute_calls",0).put("query_available",false).put("control_callback_dispatched",false)
                .put("native_returned",false).put("native_handled",false).put("creator_closed",false).put("courtier_created",false)
                .put("age_changed",false).put("new_date_observed",false).put("physical_save_confirmed",false).put("save_calls",0);
        if(currentXqolThreshold)result.put("schema","xar.native-owner-current-xqol-threshold/v1").put("mode",StrictJson.text(config.get("mode")))
                .put("machine_id",owner.machineId()).put("steam_build_id","26785313").put("action",thresholdConfig.action().wire()).put("target_threshold",thresholdConfig.targetThreshold())
                .put("read_calls",0).put("set_calls",0).put("query_available",false).put("route_callback_dispatched",false).put("native_returned",false)
                .put("native_handled",false).put("threshold_applied",false).put("event_closed",false).put("conversion_applied",false)
                .put("new_date_observed",false).put("physical_save_confirmed",false).put("save_calls",0);
        if(currentXqolPrompt)result.put("schema","xar.native-owner-current-xqol-prompt/v1").put("mode",StrictJson.text(config.get("mode")))
                .put("machine_id",owner.machineId()).put("steam_build_id","26785313").put("action",xqolPromptAction.wire())
                .put("read_calls",0).put("action_calls",0).put("query_available",false).put("action_callback_dispatched",false)
                .put("native_returned",false).put("native_handled",false).put("event_closed",false).put("conversion_applied",false)
                .put("new_date_observed",false).put("physical_save_confirmed",false).put("save_calls",0);
        if(currentCuratedDecision) {
            result.put("schema","xar.native-owner-current-curated-decisions/v1").put("mode",StrictJson.text(config.get("mode")))
                    .put("machine_id",owner.machineId()).put("steam_build_id","26785313").put("action",curatedConfig.action().wire())
                    .put("read_calls",0).put("action_calls",0).put("query_available",false).put("action_callback_dispatched",false)
                    .put("native_handled",false).put("decision_applied",false).put("new_date_observed",false).put("physical_save_confirmed",false).put("save_calls",0);
            if(curatedConfig.decisionKey().isPresent())result.put("decision_key",curatedConfig.decisionKey().orElseThrow().wire());else result.putNull("decision_key");
        }
        if(currentFullscreenEvent)result.put("schema","xar.native-owner-current-fullscreen-event/v1").put("mode",acknowledgeKnownIntro?"current_fullscreen_event_ack_known_intro":"current_fullscreen_event_query")
                .put("machine_id",owner.machineId()).put("steam_build_id","26785313").put("read_calls",0).put("acknowledge_calls",0)
                .put("query_available",false).put("acknowledge_callback_dispatched",false).put("native_handled",false)
                .put("fullscreen_closed",false).put("new_date_observed",false).put("physical_save_confirmed",false).put("save_calls",0);
        if(currentLetterSet) {
            result.put("schema","xar.native-owner-current-letter-set/v1").put("mode",letterSetReply?"current_letter_set_reply_known_instance":"current_letter_set_query")
                    .put("machine_id",owner.machineId()).put("steam_build_id","26785313").put("read_calls",0).put("reply_calls",0)
                    .put("query_available",false).put("reply_callback_dispatched",false).put("native_handled",false)
                    .put("letter_closed",false).put("new_date_observed",false).put("physical_save_confirmed",false).put("save_calls",0);
            if(letterSetReply)result.put("instance_id",letterSetInstance);else result.putNull("instance_id");
        }
        if(currentLetter)result.put("schema","xar.native-owner-current-letter/v1").put("mode",knownLetterReply?"current_letter_reply_known":"current_letter_query")
                .put("machine_id",owner.machineId()).put("steam_build_id","26785313").put("read_calls",0).put("reply_calls",0)
                .put("query_available",false).put("reply_callback_dispatched",false).put("native_handled",false)
                .put("letter_closed",false).put("new_date_observed",false).put("physical_save_confirmed",false).put("save_calls",0);
        if(djcUiMode)result.put("schema","xar.native-owner-current-djc-declaration-ui/v1").put("mode",djcUiSubmit?"current_djc_declaration_submit":"current_djc_declaration_ui")
                .put("machine_id",owner.machineId()).put("steam_build_id","26785313").put("target_character_id",declarationConfig.target().value()).put("cb_key",declarationConfig.casusBelli().wire())
                .put("read_calls",0).put("open_calls",0).put("select_calls",0).put("send_calls",0).put("warning_queries",0).put("accept_calls",0).put("query_available",false).put("accept_callback_dispatched",false)
                .put("submitted",false).put("war_created",false).put("payment_confirmed",false).put("physical_save_confirmed",false).put("native_handled",false).putNull("war_id").putNull("total_debit");
        if(currentSuccession)result.put("schema","xar.native-owner-current-succession/v1").put("mode",continueSuccession?"current_succession_default_continue":"current_succession_default")
                .put("read_calls",0).put("continue_calls",0).put("native_callback_returned",false).put("continuation_confirmed",false).put("physical_save_confirmed",false).put("save_calls",0);
        if(currentFrontendMenu)result.put("schema","xar.native-owner-current-menu/v1").put("mode",currentFrontendQuit?"current_frontend_menu_quit":"current_frontend_menu")
                .put("read_calls",0).put("quit_calls",0).put("world_core_fabricated",false).put("application_exit_confirmed",false).put("game_started_confirmed",false).put("physical_save_confirmed",false);
        stage = "ATTACH";
        try (var supervisor = WindowsJobProcess.retainReadOnlyProcess(owner.supervisorIdentity().pid())) {
            requireSupervisor(supervisor, owner.supervisorIdentity());
            var request = new NativeGameAttachment.Request(plan, owner.generation(), List.of(), frames,currentDecisionsClose?(decisionsCloseAction==CurrentDecisionsClose.Action.QUERY_CLOSE?2:3):currentCourtierControls?(courtierConfig.action()==CurrentCourtierControls.Action.QUERY_CONTROL?2:3):currentXqolThreshold?(thresholdConfig.action()==CurrentXqolThreshold.Action.QUERY_THRESHOLD?2:3):currentXqolPrompt?(xqolPromptAction==CurrentXqolPrompt.Action.QUERY_PROMPT?2:3):currentCuratedDecision?(curatedConfig.action()==CurrentCuratedDecisions.Action.QUERY?2:3):currentFullscreenEvent?(acknowledgeKnownIntro?3:2):currentLetterSet?(letterSetReply?3:2):djcSelectedCost?(djcCostPreview?9:3):currentLetter?(knownLetterReply?3:2):djcUiMode?(djcUiSubmit?declarationConfig.maximumWarningPolls()+12:2):currentSuccession?(continueSuccession?2:1):currentFrontendMenu?(currentFrontendQuit?2:1):riteFinalConfirmation?maximumConfirmationPolls+5:currentDateAdvance?maximumStatusPolls+3:riteDoctrine?4:guiNavigation?3:guiControls?(controlWindow==GuiControlsFrameV2.Window.RITE?3:2):dateAdvance?maximumStatusPolls+6:checkpointSave||aubObserver||djcQuery||coreCommand||fullClock||personalCash||guiRootIndex||guiWindow||riteDraftCosts?2:1);
            // This factory returns ATTACHED only. Its close releases communication and readonly handles, never a Job.
            try (ManagedGameSession game = NativeGameAttachment.attach(request, (currentDecisionsClose||currentCourtierControls||currentXqolThreshold||currentXqolPrompt||currentCuratedDecision||currentFullscreenEvent||currentLetterSet||djcSelectedCost||currentLetter||djcUiMode||currentFrontendMenu||currentSuccession||aubObserver||djcQuery||riteFinalConfirmation||currentDateAdvance||checkpointSave||guiNavigation||riteDoctrine)&&plan.deadline().isBefore(deadline)?plan.deadline():deadline, Duration.ofSeconds(readSeconds))) {
                if (game.mode() != ManagedGameSession.Mode.ATTACHED) throw new IOException("actual attachment mode differs");
                requireSupervisor(supervisor, owner.supervisorIdentity());
                var transport = game.nativeTransport();
                var hello = transport.diagnostics().originalHello().orElseThrow(() -> new IOException("actual received HELLO unavailable"));
                originals.set("new_hello", write(output, "new-hello.bin", hello.original().packet().value()));
                result.put("hello_observed_at_utc", hello.observedAt().toString());
                if(currentDecisionsClose) {
                    runCurrentDecisionsClose(transport,owner,plan,decisionsCloseAction,output,plan.deadline().isBefore(deadline)?plan.deadline():deadline,result,originals);
                } else if(currentCourtierControls) {
                    runCurrentCourtierControls(transport,owner,plan,courtierConfig,output,plan.deadline().isBefore(deadline)?plan.deadline():deadline,result,originals);
                } else if(currentXqolThreshold) {
                    runCurrentXqolThreshold(transport,owner,plan,thresholdConfig,output,plan.deadline().isBefore(deadline)?plan.deadline():deadline,result,originals);
                } else if(currentXqolPrompt) {
                    runCurrentXqolPrompt(transport,owner,plan,xqolPromptAction,output,plan.deadline().isBefore(deadline)?plan.deadline():deadline,result,originals);
                } else if(currentCuratedDecision) {
                    runCurrentCuratedDecision(transport,owner,plan,curatedConfig,output,plan.deadline().isBefore(deadline)?plan.deadline():deadline,result,originals);
                } else if(currentFullscreenEvent) {
                    runCurrentFullscreenEvent(transport,owner,plan,acknowledgeKnownIntro,output,plan.deadline().isBefore(deadline)?plan.deadline():deadline,result,originals);
                } else if(djcSelectedCost) {
                    runCurrentDjcSelectedCost(transport,owner,plan,declarationConfig,djcCostPreview,output,plan.deadline().isBefore(deadline)?plan.deadline():deadline,Duration.ofSeconds(readSeconds),result,originals);
                } else if(currentLetterSet) {
                    runCurrentLetterSet(transport,owner,plan,letterSetReply,letterSetInstance,output,plan.deadline().isBefore(deadline)?plan.deadline():deadline,result,originals);
                } else if(currentLetter) {
                    runCurrentLetter(transport,owner,plan,knownLetterReply,output,plan.deadline().isBefore(deadline)?plan.deadline():deadline,result,originals);
                } else if(djcUiMode) {
                    runCurrentDjcDeclarationUi(transport,owner,plan,declarationConfig,djcUiSubmit,output,plan.deadline().isBefore(deadline)?plan.deadline():deadline,Duration.ofSeconds(readSeconds),result,originals);
                } else if(currentSuccession) {
                    runCurrentSuccessionDefault(transport,owner,plan,continueSuccession,output,plan.deadline().isBefore(deadline)?plan.deadline():deadline,result,originals);
                } else if(currentFrontendMenu) {
                    runCurrentFrontendMenu(transport,owner,plan,currentFrontendQuit,output,plan.deadline().isBefore(deadline)?plan.deadline():deadline,result,originals);
                } else if(riteFinalConfirmation) {
                    runRiteFinalConfirmation(transport,owner,plan,expectedSourceRiteId,output,plan.deadline().isBefore(deadline)?plan.deadline():deadline,
                            Duration.ofSeconds(readSeconds),maximumConfirmationPolls,confirmationPollMillis,result,originals);
                } else if(currentDateAdvance) {
                    runCurrentDateAdvance(transport,owner,plan,output,plan.deadline().isBefore(deadline)?plan.deadline():deadline,
                            Duration.ofSeconds(readSeconds),maximumStatusPolls,statusPollMillis,result,originals);
                } else if(riteDoctrine) {
                    result.put("schema","xar.native-owner-current-rite-doctrine/v1").put("mode","current_rite_doctrine").put("action",riteAction.wire()).put("effect_calls",0).put("rite_edit_confirmed",false).put("physical_save_confirmed",false);
                    runRiteDoctrine(transport,owner,plan,expectedSourceRiteId,riteAction,output,plan.deadline().isBefore(deadline)?plan.deadline():deadline,result,originals);
                } else if(guiNavigation) {
                    runLiteralNavigation(transport,owner,plan,navigationAction,output,plan.deadline().isBefore(deadline)?plan.deadline():deadline,result,originals);
                } else if(djcQuery) {
                    runCurrentDjcTargetQuery(transport,owner,plan,djcTarget,output,plan.deadline().isBefore(deadline)?plan.deadline():deadline,result,originals);
                } else if(aubObserver) {
                    runCurrentAubObserverFixture(transport,owner,plan,output,plan.deadline().isBefore(deadline)?plan.deadline():deadline,result,originals);
                } else if(checkpointSave) {
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
                    java.util.Optional<ExactRef> mapped112=java.util.Optional.empty();
                    if("save-checkpoint".equals(fullClockStep))mapped112=transport.bindMappedSave112(game);
                    var prepared=preparedFullClockRequest(fullClockStep,frame.state(),frame.snapshotId(),
                            frame.nativeRevision(),commandDeadline,mapped112);
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
        String archivedStatus = currentDecisionsClose?"ARCHIVED_CURRENT_DECISIONS_CLOSE_DATA_ENDPOINT_RELEASED":currentCourtierControls?"ARCHIVED_CURRENT_COURTIER_CONTROLS_DATA_ENDPOINT_RELEASED":currentXqolThreshold?"ARCHIVED_CURRENT_XQOL_THRESHOLD_DATA_ENDPOINT_RELEASED":currentXqolPrompt?"ARCHIVED_CURRENT_XQOL_PROMPT_DATA_ENDPOINT_RELEASED":currentCuratedDecision?"ARCHIVED_CURRENT_CURATED_DECISIONS_DATA_ENDPOINT_RELEASED":currentFullscreenEvent?"ARCHIVED_CURRENT_FULLSCREEN_EVENT_DATA_ENDPOINT_RELEASED":currentLetterSet?"ARCHIVED_CURRENT_LETTER_SET_DATA_ENDPOINT_RELEASED":djcSelectedCost?"ARCHIVED_CURRENT_DJC_SELECTED_COST_DATA_ENDPOINT_RELEASED":currentLetter?"ARCHIVED_CURRENT_LETTER_DATA_ENDPOINT_RELEASED":djcUiMode?"ARCHIVED_CURRENT_DJC_DECLARATION_UI_DATA_ENDPOINT_RELEASED":riteFinalConfirmation?"ARCHIVED_CURRENT_RITE_FINAL_CALLBACK_DATA_ENDPOINT_RELEASED":currentDateAdvance?"ARCHIVED_CURRENT_NATIVE_ONE_DAY_ENDPOINT_RELEASED":riteDoctrine?"ARCHIVED_CURRENT_RITE_ACTION_DATA_ENDPOINT_RELEASED":guiNavigation?"ARCHIVED_LITERAL_NAVIGATION_SUBMISSION_ENDPOINT_RELEASED":checkpointSave?"ARCHIVED_CURRENT_CORE_CHECKPOINT_MATERIAL_ENDPOINT_RELEASED":guiControls?"ARCHIVED_NATIVE_GUI_CONTROLS_DATA_ENDPOINT_RELEASED":riteDraftCosts?"ARCHIVED_NATIVE_RITE_DRAFT_COSTS_DATA_ENDPOINT_RELEASED":guiWindow?"ARCHIVED_NATIVE_GUI_WINDOW_DATA_ENDPOINT_RELEASED":guiRootIndex?"ARCHIVED_NATIVE_GUI_ROOT_INDEX_DATA_ENDPOINT_RELEASED":dateAdvance?"ARCHIVED_NATIVE_DATE_SENTINEL_ADVANCE_ENDPOINT_RELEASED":personalCash?"ARCHIVED_NATIVE_PERSONAL_CASH_DATA_ENDPOINT_RELEASED":fullClock?"ARCHIVED_NATIVE_FULL_CLOCK_SUBMISSION_ENDPOINT_RELEASED":actorFoundation?"ARCHIVED_NATIVE_ACTOR_FOUNDATION_DATA_ENDPOINT_RELEASED":personalGold?"ARCHIVED_NATIVE_PERSONAL_GOLD_DATA_ENDPOINT_RELEASED":applicationExit?"ARCHIVED_NATIVE_APPLICATION_EXIT_REQUEST_ENDPOINT_RELEASED":controlStep!=null?"ARCHIVED_NATIVE_CORE_CONTROL_SUBMISSION_ENDPOINT_RELEASED":corePrefixOnly ? "ARCHIVED_NATIVE_CORE_PREFIX_DATA_ENDPOINT_RELEASED" : "ARCHIVED_NATIVE_READ_DATA_ENDPOINT_RELEASED";
        result.put("status", archivedStatus).put("completed_at_utc", Instant.now().toString());
        ObjectNode published = write(output, "summary.json", FullJsonTree.encode(result, FullJsonTree.MAXIMUM_BYTES));
        System.out.println(StrictJson.object().put("schema", "xar.native-owner-snapshot-stage/v1")
                .put("status", archivedStatus).put("at_utc", Instant.now().toString()).set("summary", published));
    }

    static CurrentDecisionsClose.Action currentDecisionsCloseAction(ObjectNode config) {
        StrictJson.object(config,Set.of("schema","mode","owner_descriptor","overall_timeout_seconds","read_timeout_seconds","maximum_frames_per_operation"));
        StrictJson.require(StrictJson.text(config.get("schema")).equals("xar.native-owner-snapshot-config/v32"),"Explicit v32 fixed decisions-close mode required");
        ExactRef.fromJson(config.get("owner_descriptor"));
        StrictJson.integer(config.get("overall_timeout_seconds"),1,600);StrictJson.integer(config.get("read_timeout_seconds"),1,60);
        StrictJson.integer(config.get("maximum_frames_per_operation"),1,65536);
        return switch(StrictJson.text(config.get("mode"))) {
            case "current_decisions_close_query"->CurrentDecisionsClose.Action.QUERY_CLOSE;
            case "current_decisions_close"->CurrentDecisionsClose.Action.CLOSE_LIST;
            default->throw new IllegalArgumentException("Only independent list-close query or one private-source fixed list close; no detail/close-all sequence");
        };
    }
    static void requireCurrentDecisionsCloseQueryFrame(CurrentDecisionsCloseResult frame,CoreFrame.Prefix actual)throws IOException {
        if(frame.action()!=CurrentDecisionsClose.Action.QUERY_CLOSE||frame.status()!=CurrentDecisionsCloseResult.Status.AVAILABLE
                ||frame.effectAttempted()||frame.nativeReturned()||frame.nativeHandled()||!frame.cleanupKnown()||frame.claimSequence().signum()!=0
                ||frame.providerGeneration().signum()<=0||frame.querySequence().signum()<=0||frame.owner().isEmpty()
                ||frame.factsBefore().filter(actual::equals).isEmpty()||frame.source().isEmpty())
            throw new IOException("Actual readonly decisions-close query differs from original Core/source/private lease");
    }
    static CurrentCuratedDecisionsSource requireCurrentDecisionsCloseSource(CurrentDecisionsCloseResult query)throws IOException {
        requireCurrentDecisionsCloseQueryFrame(query,query.factsBefore().orElseThrow(()->new IOException("Original decisions-close Core absent")));
        if(!query.closeAdmissible())throw new IOException("Actual list-close private source does not admit Close; no inferred permission or fallback");
        return query.source().orElseThrow();
    }
    static void requireCurrentDecisionsCloseDispatchFrame(CurrentDecisionsCloseResult query,CurrentDecisionsCloseResult dispatched)throws IOException {
        requireCurrentDecisionsCloseSource(query);
        if(dispatched.action()!=CurrentDecisionsClose.Action.CLOSE_LIST||dispatched.status()!=CurrentDecisionsCloseResult.Status.CLOSE_DISPATCHED
                ||!dispatched.effectAttempted()||!dispatched.nativeReturned()||!dispatched.cleanupKnown()||dispatched.claimSequence().signum()<=0||!dispatched.closeAdmissible()
                ||!dispatched.providerGeneration().equals(query.providerGeneration())||!dispatched.querySequence().equals(query.querySequence())
                ||!dispatched.factsBefore().equals(query.factsBefore())||!dispatched.source().equals(query.source())||dispatched.owner().isEmpty()
                ||!dispatched.owner().orElseThrow().connectionGeneration().equals(query.owner().orElseThrow().connectionGeneration()))
            throw new IOException("List-close callback differs from original complete source/Core/private lease");
        // nativeHandled is the actual callback bool, including false. Neither bool proves closed panels.
    }
    private static void runCurrentDecisionsClose(NativeGameTransport transport,GameSupervisorControl.Descriptor owner,
            NativeLaunchPlan plan,CurrentDecisionsClose.Action action,Path output,Instant deadline,ObjectNode result,ObjectNode originals)throws IOException,InterruptedException {
        try {
            if(!(plan.load() instanceof NativeLaunchPlan.SavedGame))throw new IOException("Current list-close requires its actual SavedGame owner");
            stage="ONE_ACTUAL_CORE_BEFORE_DECISIONS_CLOSE";result.put("read_calls",1);
            var coreRead=transport.readCoreFrameReceived(deadline);
            archiveCurrentLetterOutcome(transport,Files.createDirectory(output.resolve("core-before-decisions-close")),"core",coreRead.original(),originals);
            if(!(coreRead instanceof NativeGameTransport.CoreReceived before)||!(before.frame() instanceof CoreFrame.Partial core))throw new IOException("Actual current decisions-close Core unavailable; no configured replacement");
            requireCurrentDjcAckOwner(transport,owner,before.original(),null);
            var actualSession=before.original().custody().orElseThrow().session();var p=core.prefix();
            if(core.build()!=ExactCk3Build.CK3_121003_STEAM_26785313
                    ||!core.build().executableSha256().equalsIgnoreCase(plan.sources().review().gameExecutable().sha256())
                    ||!core.build().coreFrameAdapterId().equals(plan.adapterId())||!p.paused()||!p.mapReady()
                    ||!p.hasPlayedCharacter()||!p.playedCharacterAlive()||p.playedCharacterId()==-1||p.localPlayerId()<0||p.speed()<1||p.speed()>5)
                throw new IOException("Exact actual paused living current Core required before list-close query");
            Instant until=before.validUntil().isBefore(deadline)?before.validUntil():deadline;before.requireOriginal(transport,until);
            stage="ONE_READONLY_CURRENT_DECISIONS_CLOSE_QUERY";result.put("read_calls",2);
            var read=transport.readCurrentDecisionsClose(before,until);Path queryOutput=Files.createDirectory(output.resolve("decisions-close-query"));
            archiveCurrentLetterOutcome(transport,queryOutput,"decisions_close_query",read.original(),originals);
            if(!(read instanceof NativeGameTransport.DecisionsCloseReceived query))throw new IOException("Actual typed decisions-close source unavailable or UNKNOWN; no Close or retry");
            until=query.validUntil().isBefore(until)?query.validUntil():until;query.requireOriginal(transport,until);
            var queryAck=query.original();requireCurrentDjcAckOwner(transport,owner,queryAck,actualSession);
            var frame=CurrentDecisionsCloseResult.decodeOutcome(queryAck);
            if(!frame.equals(query.frame()))throw new IOException("Actual decisions-close query differs from private retained frame");
            requireCurrentDecisionsCloseQueryFrame(frame,p);
            if(!frame.owner().orElseThrow().connectionGeneration().equals(actualSession.connectionGeneration()))throw new IOException("Decisions-close query owner crossed actual connection");
            originals.set("decisions_close_query_original_result",write(queryOutput,"original-result.json",queryAck.originalResultToken().orElseThrow().bytes()));
            result.set("query",FullJsonTree.parse(frame.encode().bytes(),SMALL));result.set("session",session(actualSession));
            result.put("query_available",true).put("query_request_id",queryAck.requestId());
            if(action==CurrentDecisionsClose.Action.QUERY_CLOSE)return;
            var selected=requireCurrentDecisionsCloseSource(frame);
            var prepared=transport.prepareCurrentDecisionsClose(query);
            if(prepared.action()!=CurrentDecisionsClose.Action.CLOSE_LIST||!prepared.selected().equals(selected))throw new IOException("Private list-close preparation differs from complete actual source");
            if(!prepared.deadline().equals(query.validUntil())||prepared.deadline().isAfter(deadline))throw new IOException("Original list-close deadline changed");
            Path actionOutput=Files.createDirectory(output.resolve("one-decisions-list-close"));
            var intent=StrictJson.object().put("schema","xar.current-decisions-close-original-intent/v1").put("request_id",prepared.requestId()).put("action",prepared.action().wire())
                    .put("original_query_request_id",queryAck.requestId()).put("original_deadline_utc",prepared.deadline().toString())
                    .put("panels_closed",false).put("new_date_observed",false).put("physical_save_confirmed",false);
            intent.set("original_query_source",originals.get("decisions_close_query_original_result").deepCopy());
            intent.set("original_outbound",write(actionOutput,"original-request.packet",prepared.originalPacket().value()));
            originals.set("decisions_close_intent",write(actionOutput,"original-intent.json",FullJsonTree.encode(intent,SMALL)));
            stage="ONE_PRIVATE_SOURCE_DECISIONS_LIST_CLOSE";result.put("close_calls",1);
            var outcome=transport.submitCurrentDecisionsClose(prepared);
            archiveCurrentLetterOutcome(transport,actionOutput,"decisions_list_close",outcome,originals);
            if(!(outcome instanceof NativeActionPort.AckReceived ack))throw new IOException("Original list-close UNKNOWN or rejected; never replay");
            requireCurrentDjcAckOwner(transport,owner,ack,actualSession);var dispatched=CurrentDecisionsCloseResult.decodeOutcome(ack);
            originals.set("decisions_close_original_result",write(actionOutput,"original-result.json",ack.originalResultToken().orElseThrow().bytes()));
            if(prepared.latestFrame().filter(dispatched::equals).isEmpty())throw new IOException("Original list-close ACK was not qualified by its private preparation");
            requireCurrentDecisionsCloseDispatchFrame(frame,dispatched);
            if(!dispatched.owner().orElseThrow().connectionGeneration().equals(actualSession.connectionGeneration()))throw new IOException("List-close owner crossed actual connection");
            result.set("close_result",FullJsonTree.parse(dispatched.encode().bytes(),SMALL));
            result.put("close_request_id",ack.requestId()).put("close_callback_dispatched",true)
                    .put("native_returned",dispatched.nativeReturned()).put("native_handled",dispatched.nativeHandled()).put("native_status",dispatched.status().wire());
        } finally {
            archiveNaturalDiagnostics(output,originals,transport.diagnostics());var progress=result.deepCopy();progress.set("originals",originals.deepCopy());
            write(output,"current-decisions-close-progress.json",FullJsonTree.encode(progress,FullJsonTree.MAXIMUM_BYTES));
        }
    }

    record CourtierControlsConfig(CurrentCourtierControls.Action action,CurrentCourtierControls.Product product,CurrentCourtierControls.Control control) {
        CourtierControlsConfig { Objects.requireNonNull(action);Objects.requireNonNull(product);Objects.requireNonNull(control); }
    }
    static CourtierControlsConfig currentCourtierControlsConfig(ObjectNode config) {
        StrictJson.object(config,Set.of("schema","mode","owner_descriptor","overall_timeout_seconds","read_timeout_seconds","maximum_frames_per_operation","product","control"));
        StrictJson.require(StrictJson.text(config.get("schema")).equals("xar.native-owner-snapshot-config/v31"),"Explicit v31 fixed courtier control mode required");
        ExactRef.fromJson(config.get("owner_descriptor"));
        StrictJson.integer(config.get("overall_timeout_seconds"),1,600);StrictJson.integer(config.get("read_timeout_seconds"),1,60);
        StrictJson.integer(config.get("maximum_frames_per_operation"),1,65536);
        var action=switch(StrictJson.text(config.get("mode"))) {
            case "current_courtier_creator_controls_query"->CurrentCourtierControls.Action.QUERY_CONTROL;
            case "current_courtier_creator_control_execute"->CurrentCourtierControls.Action.EXECUTE_CONTROL;
            default->throw new IllegalArgumentException("Only independent fixed creator query or one private-source Execute; no automatic sequence");
        };
        try { return new CourtierControlsConfig(action,CurrentCourtierControls.Product.parse(StrictJson.text(config.get("product"))),CurrentCourtierControls.Control.parse(StrictJson.text(config.get("control")))); }
        catch(IOException invalid){throw new IllegalArgumentException("Exact fixed product and control DATA required",invalid);}
    }
    static void requireCurrentCourtierControlsQueryFrame(CurrentCourtierControlsResult frame,CoreFrame.Prefix actual,
            CurrentCourtierControls.Product product,CurrentCourtierControls.Control control)throws IOException {
        if(frame.action()!=CurrentCourtierControls.Action.QUERY_CONTROL||frame.status()!=CurrentCourtierControlsResult.Status.AVAILABLE
                ||frame.effectAttempted()||frame.nativeReturned()||!frame.cleanupKnown()||frame.claimSequence().signum()!=0
                ||frame.providerGeneration().signum()<=0||frame.querySequence().signum()<=0||frame.owner().isEmpty()
                ||frame.product()!=product||frame.control()!=control||frame.factsBefore().filter(actual::equals).isEmpty()
                ||frame.source().filter(s->s.product()==product&&s.control()==control).isEmpty())
            throw new IOException("Actual readonly fixed creator query differs from its Core/product/control/private lease");
    }
    static CurrentCourtierControlsSource requireCurrentCourtierControlsSource(CurrentCourtierControlsResult query,CourtierControlsConfig config)throws IOException {
        requireCurrentCourtierControlsQueryFrame(query,query.factsBefore().orElseThrow(()->new IOException("Original fixed creator Core absent")),config.product(),config.control());
        var source=query.source().orElseThrow();
        if(config.action()!=CurrentCourtierControls.Action.EXECUTE_CONTROL||!source.executeAdmissible())
            throw new IOException("Original actual creator chain and native predicates do not admit this fixed Execute; no fallback");
        return source;
    }
    static void requireCurrentCourtierControlsDispatchFrame(CurrentCourtierControlsResult query,CurrentCourtierControlsResult dispatched,CourtierControlsConfig config)throws IOException {
        requireCurrentCourtierControlsSource(query,config);
        if(dispatched.action()!=CurrentCourtierControls.Action.EXECUTE_CONTROL||dispatched.status()!=CurrentCourtierControlsResult.Status.CONTROL_DISPATCHED
                ||!dispatched.effectAttempted()||!dispatched.nativeReturned()||!dispatched.cleanupKnown()||dispatched.claimSequence().signum()<=0
                ||dispatched.product()!=config.product()||dispatched.control()!=config.control()||!dispatched.providerGeneration().equals(query.providerGeneration())
                ||!dispatched.querySequence().equals(query.querySequence())||!dispatched.factsBefore().equals(query.factsBefore())
                ||!dispatched.source().equals(query.source())||dispatched.owner().isEmpty()
                ||!dispatched.owner().orElseThrow().connectionGeneration().equals(query.owner().orElseThrow().connectionGeneration()))
            throw new IOException("Fixed creator callback differs from original full source/Core/product/control/private lease");
    }
    private static void runCurrentCourtierControls(NativeGameTransport transport,GameSupervisorControl.Descriptor owner,
            NativeLaunchPlan plan,CourtierControlsConfig config,Path output,Instant deadline,ObjectNode result,ObjectNode originals)throws IOException,InterruptedException {
        try {
            if(!(plan.load() instanceof NativeLaunchPlan.SavedGame))throw new IOException("Current fixed creator controls require their actual SavedGame owner");
            stage="ONE_ACTUAL_CORE_BEFORE_COURTIER_CONTROLS";result.put("read_calls",1);
            var coreRead=transport.readCoreFrameReceived(deadline);
            archiveCurrentLetterOutcome(transport,Files.createDirectory(output.resolve("core-before-courtier-controls")),"core",coreRead.original(),originals);
            if(!(coreRead instanceof NativeGameTransport.CoreReceived before)||!(before.frame() instanceof CoreFrame.Partial core))throw new IOException("Actual current fixed creator Core unavailable; no configured replacement");
            requireCurrentDjcAckOwner(transport,owner,before.original(),null);
            var actualSession=before.original().custody().orElseThrow().session();var p=core.prefix();
            if(core.build()!=ExactCk3Build.CK3_121003_STEAM_26785313
                    ||!core.build().executableSha256().equalsIgnoreCase(plan.sources().review().gameExecutable().sha256())
                    ||!core.build().coreFrameAdapterId().equals(plan.adapterId())||!p.paused()||!p.mapReady()
                    ||!p.hasPlayedCharacter()||!p.playedCharacterAlive()||p.playedCharacterId()==-1||p.localPlayerId()<0||p.speed()<1||p.speed()>5)
                throw new IOException("Exact actual paused living current Core required before fixed creator query");
            Instant until=before.validUntil().isBefore(deadline)?before.validUntil():deadline;before.requireOriginal(transport,until);
            stage="ONE_READONLY_CURRENT_COURTIER_CONTROLS_QUERY";result.put("read_calls",2);
            var read=transport.readCurrentCourtierControls(before,config.product(),config.control(),until);Path queryOutput=Files.createDirectory(output.resolve("courtier-controls-query"));
            archiveCurrentLetterOutcome(transport,queryOutput,"courtier_controls_query",read.original(),originals);
            if(!(read instanceof NativeGameTransport.CourtierControlsReceived query))throw new IOException("Actual typed fixed creator source unavailable or UNKNOWN; no Execute or retry");
            until=query.validUntil().isBefore(until)?query.validUntil():until;query.requireOriginal(transport,until);
            if(query.product()!=config.product()||query.control()!=config.control())throw new IOException("Private query product/control differs from original pure DATA intent");
            var queryAck=query.original();requireCurrentDjcAckOwner(transport,owner,queryAck,actualSession);
            var frame=CurrentCourtierControlsResult.decodeOutcome(queryAck);
            if(!frame.equals(query.frame()))throw new IOException("Actual fixed creator query differs from private retained frame");
            requireCurrentCourtierControlsQueryFrame(frame,p,config.product(),config.control());
            if(!frame.owner().orElseThrow().connectionGeneration().equals(actualSession.connectionGeneration()))throw new IOException("Fixed creator query owner crossed actual connection");
            originals.set("courtier_controls_query_original_result",write(queryOutput,"original-result.json",queryAck.originalResultToken().orElseThrow().bytes()));
            result.set("query",FullJsonTree.parse(frame.encode().bytes(),SMALL));result.set("session",session(actualSession));
            result.put("query_available",true).put("query_request_id",queryAck.requestId());
            if(config.action()==CurrentCourtierControls.Action.QUERY_CONTROL)return;
            var selected=requireCurrentCourtierControlsSource(frame,config);
            var prepared=transport.prepareCurrentCourtierControlExecute(query);
            if(prepared.action()!=CurrentCourtierControls.Action.EXECUTE_CONTROL||prepared.product()!=config.product()||prepared.control()!=config.control()||!prepared.selected().equals(selected))
                throw new IOException("Private fixed creator preparation differs from complete original product/control source");
            if(!prepared.deadline().equals(query.validUntil())||prepared.deadline().isAfter(deadline))throw new IOException("Original fixed creator Execute deadline changed");
            Path actionOutput=Files.createDirectory(output.resolve("one-courtier-control-execute"));
            var intent=StrictJson.object().put("schema","xar.current-courtier-controls-original-intent/v1").put("request_id",prepared.requestId())
                    .put("action",prepared.action().wire()).put("product",prepared.product().wire()).put("control",prepared.control().wire())
                    .put("original_query_request_id",queryAck.requestId()).put("original_deadline_utc",prepared.deadline().toString())
                    .put("creator_closed",false).put("courtier_created",false).put("age_changed",false).put("new_date_observed",false).put("physical_save_confirmed",false);
            intent.set("original_query_source",originals.get("courtier_controls_query_original_result").deepCopy());
            intent.set("original_outbound",write(actionOutput,"original-request.packet",prepared.originalPacket().value()));
            originals.set("courtier_control_execute_intent",write(actionOutput,"original-intent.json",FullJsonTree.encode(intent,SMALL)));
            stage="ONE_PRIVATE_SOURCE_COURTIER_CONTROL_EXECUTE";result.put("execute_calls",1);
            var outcome=transport.submitCurrentCourtierControlExecute(prepared);
            archiveCurrentLetterOutcome(transport,actionOutput,"courtier_control_execute",outcome,originals);
            if(!(outcome instanceof NativeActionPort.AckReceived ack))throw new IOException("Original fixed creator Execute UNKNOWN or rejected; never replay");
            requireCurrentDjcAckOwner(transport,owner,ack,actualSession);var dispatched=CurrentCourtierControlsResult.decodeOutcome(ack);
            originals.set("courtier_control_execute_original_result",write(actionOutput,"original-result.json",ack.originalResultToken().orElseThrow().bytes()));
            if(prepared.latestFrame().filter(dispatched::equals).isEmpty())throw new IOException("Original fixed creator ACK was not qualified by its private preparation");
            requireCurrentCourtierControlsDispatchFrame(frame,dispatched,config);
            if(!dispatched.owner().orElseThrow().connectionGeneration().equals(actualSession.connectionGeneration()))throw new IOException("Fixed creator Execute owner crossed actual connection");
            result.set("execute_result",FullJsonTree.parse(dispatched.encode().bytes(),SMALL));
            result.put("execute_request_id",ack.requestId()).put("control_callback_dispatched",true)
                    .put("native_returned",dispatched.nativeReturned()).put("native_handled",false).put("native_status",dispatched.status().wire());
        } finally {
            archiveNaturalDiagnostics(output,originals,transport.diagnostics());var progress=result.deepCopy();progress.set("originals",originals.deepCopy());
            write(output,"current-courtier-controls-progress.json",FullJsonTree.encode(progress,FullJsonTree.MAXIMUM_BYTES));
        }
    }

    record XqolThresholdConfig(CurrentXqolThreshold.Action action,int targetThreshold) {
        XqolThresholdConfig { Objects.requireNonNull(action);StrictJson.require(targetThreshold>=0&&targetThreshold<=100,"Exact threshold DATA integer0..100 required"); }
    }
    static XqolThresholdConfig currentXqolThresholdConfig(ObjectNode config) {
        StrictJson.object(config,Set.of("schema","mode","owner_descriptor","overall_timeout_seconds","read_timeout_seconds","maximum_frames_per_operation","target_threshold"));
        StrictJson.require(StrictJson.text(config.get("schema")).equals("xar.native-owner-snapshot-config/v30"),"Explicit v30 XQOL threshold mode required");
        ExactRef.fromJson(config.get("owner_descriptor"));
        StrictJson.integer(config.get("overall_timeout_seconds"),1,600);StrictJson.integer(config.get("read_timeout_seconds"),1,60);
        StrictJson.integer(config.get("maximum_frames_per_operation"),1,65536);
        var action=switch(StrictJson.text(config.get("mode"))) {
            case "current_xqol_conversion_threshold_query"->CurrentXqolThreshold.Action.QUERY_THRESHOLD;
            case "current_xqol_conversion_threshold_set"->CurrentXqolThreshold.Action.SET_THRESHOLD;
            default->throw new IllegalArgumentException("Only independent threshold query or one fixed production route; no configured instance/event/permission");
        };
        return new XqolThresholdConfig(action,Math.toIntExact(StrictJson.integer(config.get("target_threshold"),0,100)));
    }
    static void requireCurrentXqolThresholdQueryFrame(CurrentXqolThresholdResult frame,CoreFrame.Prefix actual,int target)throws IOException {
        if(frame.action()!=CurrentXqolThreshold.Action.QUERY_THRESHOLD||frame.status()!=CurrentXqolThresholdResult.Status.AVAILABLE
                ||frame.effectAttempted()||frame.nativeReturned()||!frame.cleanupKnown()||frame.claimSequence().signum()!=0
                ||frame.instanceId().isPresent()||frame.factsBefore().filter(actual::equals).isEmpty()
                ||frame.source().filter(s->s.targetThreshold()==target).isEmpty())
            throw new IOException("Actual readonly threshold query differs from its original Core/target/query role");
    }
    static CurrentXqolThresholdSource requireCurrentXqolThresholdSource(CurrentXqolThresholdResult query,int target)throws IOException {
        requireCurrentXqolThresholdQueryFrame(query,query.factsBefore().orElseThrow(()->new IOException("Original threshold Core absent")),target);
        var source=query.source().orElseThrow();
        if(source.prompt().event().isEmpty()||!source.setAdmissible())throw new IOException("Original actual prompt/slider/fixed route does not admit this bound threshold; no fallback");
        return source;
    }
    static void requireCurrentXqolThresholdDispatchFrame(CurrentXqolThresholdResult query,CurrentXqolThresholdResult dispatched,int target)throws IOException {
        var selected=requireCurrentXqolThresholdSource(query,target);int instance=selected.prompt().event().orElseThrow().instanceId();
        if(dispatched.action()!=CurrentXqolThreshold.Action.SET_THRESHOLD||dispatched.status()!=CurrentXqolThresholdResult.Status.THRESHOLD_ROUTE_DISPATCHED
                ||!dispatched.effectAttempted()||!dispatched.nativeReturned()||!dispatched.cleanupKnown()||dispatched.claimSequence().signum()<=0
                ||dispatched.instanceId().filter(n->n==instance).isEmpty()||!dispatched.providerGeneration().equals(query.providerGeneration())
                ||!dispatched.querySequence().equals(query.querySequence())||!dispatched.factsBefore().equals(query.factsBefore())
                ||!dispatched.source().equals(query.source())||!dispatched.owner().orElseThrow().connectionGeneration().equals(query.owner().orElseThrow().connectionGeneration()))
            throw new IOException("Threshold callback differs from original complete source/Core/actual instance/target/private lease");
    }
    private static void runCurrentXqolThreshold(NativeGameTransport transport,GameSupervisorControl.Descriptor owner,
            NativeLaunchPlan plan,XqolThresholdConfig config,Path output,Instant deadline,ObjectNode result,ObjectNode originals)throws IOException,InterruptedException {
        try {
            if(!(plan.load() instanceof NativeLaunchPlan.SavedGame))throw new IOException("Current threshold requires its actual SavedGame owner");
            stage="ONE_ACTUAL_CORE_BEFORE_XQOL_THRESHOLD";result.put("read_calls",1);
            var coreRead=transport.readCoreFrameReceived(deadline);
            archiveCurrentLetterOutcome(transport,Files.createDirectory(output.resolve("core-before-xqol-threshold")),"core",coreRead.original(),originals);
            if(!(coreRead instanceof NativeGameTransport.CoreReceived before)||!(before.frame() instanceof CoreFrame.Partial core))throw new IOException("Actual current threshold Core unavailable; no configured replacement");
            requireCurrentDjcAckOwner(transport,owner,before.original(),null);
            var actualSession=before.original().custody().orElseThrow().session();var p=core.prefix();
            if(core.build()!=ExactCk3Build.CK3_121003_STEAM_26785313
                    ||!core.build().executableSha256().equalsIgnoreCase(plan.sources().review().gameExecutable().sha256())
                    ||!core.build().coreFrameAdapterId().equals(plan.adapterId())||!p.paused()||!p.mapReady()
                    ||!p.hasPlayedCharacter()||!p.playedCharacterAlive()||p.playedCharacterId()==-1||p.localPlayerId()<0||p.speed()<1||p.speed()>5)
                throw new IOException("Exact actual paused living current Core required before threshold query");
            Instant until=before.validUntil().isBefore(deadline)?before.validUntil():deadline;before.requireOriginal(transport,until);
            stage="ONE_READONLY_CURRENT_XQOL_THRESHOLD_QUERY";result.put("read_calls",2);
            var read=transport.readCurrentXqolThreshold(before,config.targetThreshold(),until);Path queryOutput=Files.createDirectory(output.resolve("xqol-threshold-query"));
            archiveCurrentLetterOutcome(transport,queryOutput,"xqol_threshold_query",read.original(),originals);
            if(!(read instanceof NativeGameTransport.XqolThresholdReceived query))throw new IOException("Actual typed threshold source unavailable or UNKNOWN; no route or retry");
            until=query.validUntil().isBefore(until)?query.validUntil():until;query.requireOriginal(transport,until);
            if(query.targetThreshold()!=config.targetThreshold())throw new IOException("Private query target differs from original pure DATA intent");
            var queryAck=query.original();requireCurrentDjcAckOwner(transport,owner,queryAck,actualSession);
            var frame=CurrentXqolThresholdResult.decodeOutcome(queryAck);
            if(!frame.equals(query.frame()))throw new IOException("Actual threshold query differs from private retained frame");
            requireCurrentXqolThresholdQueryFrame(frame,p,config.targetThreshold());
            if(!frame.owner().orElseThrow().connectionGeneration().equals(actualSession.connectionGeneration()))throw new IOException("Threshold query owner crossed actual connection");
            originals.set("xqol_threshold_query_original_result",write(queryOutput,"original-result.json",queryAck.originalResultToken().orElseThrow().bytes()));
            result.set("query",FullJsonTree.parse(frame.encode().bytes(),SMALL));result.set("session",session(actualSession));
            result.put("query_available",true).put("query_request_id",queryAck.requestId());
            if(config.action()==CurrentXqolThreshold.Action.QUERY_THRESHOLD)return;
            var selected=requireCurrentXqolThresholdSource(frame,config.targetThreshold());int instance=selected.prompt().event().orElseThrow().instanceId();
            var prepared=transport.prepareCurrentXqolThresholdSet(query);
            if(prepared.action()!=CurrentXqolThreshold.Action.SET_THRESHOLD||prepared.instanceId()!=instance||prepared.targetThreshold()!=config.targetThreshold()||!prepared.selected().equals(selected))
                throw new IOException("Private threshold preparation differs from complete actual source/instance/bound target");
            if(!prepared.deadline().equals(query.validUntil())||prepared.deadline().isAfter(deadline))throw new IOException("Original threshold route deadline changed");
            Path actionOutput=Files.createDirectory(output.resolve("one-xqol-threshold-route"));
            var intent=StrictJson.object().put("schema","xar.current-xqol-threshold-original-intent/v1").put("request_id",prepared.requestId())
                    .put("action",prepared.action().wire()).put("instance_id",instance).put("target_threshold",prepared.targetThreshold())
                    .put("original_query_request_id",queryAck.requestId()).put("original_deadline_utc",prepared.deadline().toString())
                    .put("threshold_applied",false).put("event_closed",false).put("conversion_applied",false).put("new_date_observed",false).put("physical_save_confirmed",false);
            intent.set("original_query_source",originals.get("xqol_threshold_query_original_result").deepCopy());
            intent.set("original_outbound",write(actionOutput,"original-request.packet",prepared.originalPacket().value()));
            originals.set("xqol_threshold_route_intent",write(actionOutput,"original-intent.json",FullJsonTree.encode(intent,SMALL)));
            stage="ONE_PRIVATE_SOURCE_XQOL_THRESHOLD_ROUTE";result.put("set_calls",1);
            var outcome=transport.submitCurrentXqolThresholdSet(prepared);
            archiveCurrentLetterOutcome(transport,actionOutput,"xqol_threshold_route",outcome,originals);
            if(!(outcome instanceof NativeActionPort.AckReceived ack))throw new IOException("Original threshold route UNKNOWN or rejected; never replay");
            requireCurrentDjcAckOwner(transport,owner,ack,actualSession);var dispatched=CurrentXqolThresholdResult.decodeOutcome(ack);
            originals.set("xqol_threshold_route_original_result",write(actionOutput,"original-result.json",ack.originalResultToken().orElseThrow().bytes()));
            if(prepared.latestFrame().filter(dispatched::equals).isEmpty())throw new IOException("Original threshold ACK was not qualified by its private preparation");
            requireCurrentXqolThresholdDispatchFrame(frame,dispatched,config.targetThreshold());
            if(!dispatched.owner().orElseThrow().connectionGeneration().equals(actualSession.connectionGeneration()))throw new IOException("Threshold route owner crossed actual connection");
            result.set("route_result",FullJsonTree.parse(dispatched.encode().bytes(),SMALL));
            result.put("route_request_id",ack.requestId()).put("instance_id",instance).put("route_callback_dispatched",true)
                    .put("native_returned",dispatched.nativeReturned()).put("native_handled",false).put("native_status",dispatched.status().wire());
        } finally {
            archiveNaturalDiagnostics(output,originals,transport.diagnostics());var progress=result.deepCopy();progress.set("originals",originals.deepCopy());
            write(output,"current-xqol-threshold-progress.json",FullJsonTree.encode(progress,FullJsonTree.MAXIMUM_BYTES));
        }
    }

    static CurrentXqolPrompt.Action currentXqolPromptAction(ObjectNode config) {
        StrictJson.object(config,Set.of("schema","mode","owner_descriptor","overall_timeout_seconds","read_timeout_seconds","maximum_frames_per_operation"));
        StrictJson.require(StrictJson.text(config.get("schema")).equals("xar.native-owner-snapshot-config/v29"),"Explicit v29 XQOL prompt mode required");
        ExactRef.fromJson(config.get("owner_descriptor"));
        StrictJson.integer(config.get("overall_timeout_seconds"),1,600);
        StrictJson.integer(config.get("read_timeout_seconds"),1,60);
        StrictJson.integer(config.get("maximum_frames_per_operation"),1,65536);
        return switch(StrictJson.text(config.get("mode"))) {
            case "current_xqol_conversion_prompt_query"->CurrentXqolPrompt.Action.QUERY_PROMPT;
            case "current_xqol_conversion_prompt_confirm"->CurrentXqolPrompt.Action.CONFIRM_CONVERSION;
            case "current_xqol_conversion_prompt_cancel"->CurrentXqolPrompt.Action.CANCEL_CONVERSION;
            default->throw new IllegalArgumentException("Only three independent fixed XQOL prompt modes; no configured event, option, instance or action sequence");
        };
    }
    static void requireCurrentXqolPromptQueryFrame(CurrentXqolPromptResult frame,CoreFrame.Prefix actual)throws IOException {
        if(frame.action()!=CurrentXqolPrompt.Action.QUERY_PROMPT||frame.status()!=CurrentXqolPromptResult.Status.AVAILABLE
                ||frame.effectAttempted()||frame.nativeReturned()||!frame.cleanupKnown()||frame.claimSequence().signum()!=0
                ||frame.instanceId().isPresent()||frame.factsBefore().filter(actual::equals).isEmpty()||frame.source().isEmpty())
            throw new IOException("Actual readonly XQOL prompt query differs from its original Core/query role");
    }
    static CurrentXqolPromptSource requireCurrentXqolPromptSource(CurrentXqolPromptResult query,CurrentXqolPrompt.Action action)throws IOException {
        requireCurrentXqolPromptQueryFrame(query,query.factsBefore().orElseThrow(()->new IOException("Original XQOL prompt Core absent")));
        var source=query.source().orElseThrow();
        if(action==CurrentXqolPrompt.Action.QUERY_PROMPT||source.event().isEmpty()||!source.admits(action))
            throw new IOException("Original actual known prompt does not admit this one fixed confirm or cancel; no alternate action");
        return source;
    }
    static void requireCurrentXqolPromptDispatchFrame(CurrentXqolPromptResult query,CurrentXqolPromptResult dispatched,CurrentXqolPrompt.Action action)throws IOException {
        var selected=requireCurrentXqolPromptSource(query,action);int instance=selected.event().orElseThrow().instanceId();
        if(dispatched.action()!=action||dispatched.status()!=CurrentXqolPromptResult.dispatchedStatus(action)
                ||!dispatched.effectAttempted()||!dispatched.nativeReturned()||!dispatched.cleanupKnown()||dispatched.claimSequence().signum()<=0
                ||dispatched.instanceId().filter(n->n==instance).isEmpty()||!dispatched.providerGeneration().equals(query.providerGeneration())
                ||!dispatched.querySequence().equals(query.querySequence())||!dispatched.factsBefore().equals(query.factsBefore())
                ||!dispatched.source().equals(query.source())||!dispatched.owner().orElseThrow().connectionGeneration().equals(query.owner().orElseThrow().connectionGeneration()))
            throw new IOException("XQOL prompt callback differs from original complete source/Core/actual instance/private lease");
    }
    private static void runCurrentXqolPrompt(NativeGameTransport transport,GameSupervisorControl.Descriptor owner,
            NativeLaunchPlan plan,CurrentXqolPrompt.Action action,Path output,Instant deadline,ObjectNode result,ObjectNode originals)throws IOException,InterruptedException {
        try {
            if(!(plan.load() instanceof NativeLaunchPlan.SavedGame))throw new IOException("Current XQOL prompt requires its actual SavedGame owner");
            stage="ONE_ACTUAL_CORE_BEFORE_XQOL_PROMPT";result.put("read_calls",1);
            var coreRead=transport.readCoreFrameReceived(deadline);
            archiveCurrentLetterOutcome(transport,Files.createDirectory(output.resolve("core-before-xqol-prompt")),"core",coreRead.original(),originals);
            if(!(coreRead instanceof NativeGameTransport.CoreReceived before)||!(before.frame() instanceof CoreFrame.Partial core))
                throw new IOException("Actual current XQOL prompt Core unavailable; no configured replacement");
            requireCurrentDjcAckOwner(transport,owner,before.original(),null);
            var actualSession=before.original().custody().orElseThrow().session();var p=core.prefix();
            if(core.build()!=ExactCk3Build.CK3_121003_STEAM_26785313
                    ||!core.build().executableSha256().equalsIgnoreCase(plan.sources().review().gameExecutable().sha256())
                    ||!core.build().coreFrameAdapterId().equals(plan.adapterId())||!p.paused()||!p.mapReady()
                    ||!p.hasPlayedCharacter()||!p.playedCharacterAlive()||p.playedCharacterId()==-1||p.localPlayerId()<0||p.speed()<1||p.speed()>5)
                throw new IOException("Exact actual paused living current Core required before XQOL prompt query");
            Instant until=before.validUntil().isBefore(deadline)?before.validUntil():deadline;before.requireOriginal(transport,until);
            stage="ONE_READONLY_CURRENT_XQOL_PROMPT_QUERY";result.put("read_calls",2);
            var read=transport.readCurrentXqolPrompt(before,until);Path queryOutput=Files.createDirectory(output.resolve("xqol-prompt-query"));
            archiveCurrentLetterOutcome(transport,queryOutput,"xqol_prompt_query",read.original(),originals);
            if(!(read instanceof NativeGameTransport.XqolPromptReceived query))throw new IOException("Actual typed XQOL prompt unavailable or UNKNOWN; no action or retry");
            until=query.validUntil().isBefore(until)?query.validUntil():until;query.requireOriginal(transport,until);
            var queryAck=query.original();requireCurrentDjcAckOwner(transport,owner,queryAck,actualSession);
            var frame=CurrentXqolPromptResult.decodeOutcome(queryAck);
            if(!frame.equals(query.frame()))throw new IOException("Actual XQOL prompt query differs from private retained frame");
            requireCurrentXqolPromptQueryFrame(frame,p);
            if(!frame.owner().orElseThrow().connectionGeneration().equals(actualSession.connectionGeneration()))throw new IOException("XQOL prompt query owner crossed actual connection");
            originals.set("xqol_prompt_query_original_result",write(queryOutput,"original-result.json",queryAck.originalResultToken().orElseThrow().bytes()));
            result.set("query",FullJsonTree.parse(frame.encode().bytes(),SMALL));result.set("session",session(actualSession));
            result.put("query_available",true).put("query_request_id",queryAck.requestId());
            if(action==CurrentXqolPrompt.Action.QUERY_PROMPT)return;
            var selected=requireCurrentXqolPromptSource(frame,action);int actualInstance=selected.event().orElseThrow().instanceId();
            var prepared=transport.prepareCurrentXqolPromptAction(query,action);
            if(prepared.action()!=action||prepared.instanceId()!=actualInstance||!prepared.selected().equals(selected))throw new IOException("Private XQOL prompt preparation differs from complete actual source/action/instance");
            if(!prepared.deadline().equals(query.validUntil())||prepared.deadline().isAfter(deadline))throw new IOException("Original XQOL prompt action deadline changed");
            Path actionOutput=Files.createDirectory(output.resolve("one-xqol-prompt-action"));
            var intent=StrictJson.object().put("schema","xar.current-xqol-prompt-original-intent/v1").put("request_id",prepared.requestId())
                    .put("action",prepared.action().wire()).put("instance_id",actualInstance).put("original_query_request_id",queryAck.requestId())
                    .put("original_deadline_utc",prepared.deadline().toString()).put("event_closed",false).put("conversion_applied",false)
                    .put("new_date_observed",false).put("physical_save_confirmed",false);
            intent.set("original_query_source",originals.get("xqol_prompt_query_original_result").deepCopy());
            intent.set("original_outbound",write(actionOutput,"original-request.packet",prepared.originalPacket().value()));
            originals.set("xqol_prompt_action_intent",write(actionOutput,"original-intent.json",FullJsonTree.encode(intent,SMALL)));
            stage="ONE_PRIVATE_SOURCE_XQOL_PROMPT_ACTION";result.put("action_calls",1);
            var outcome=transport.submitCurrentXqolPromptAction(prepared);
            archiveCurrentLetterOutcome(transport,actionOutput,"xqol_prompt_action",outcome,originals);
            if(!(outcome instanceof NativeActionPort.AckReceived ack))throw new IOException("Original XQOL prompt action UNKNOWN or rejected; never replay");
            requireCurrentDjcAckOwner(transport,owner,ack,actualSession);var dispatched=CurrentXqolPromptResult.decodeOutcome(ack);
            originals.set("xqol_prompt_action_original_result",write(actionOutput,"original-result.json",ack.originalResultToken().orElseThrow().bytes()));
            if(prepared.latestFrame().filter(dispatched::equals).isEmpty())throw new IOException("Original XQOL prompt ACK was not qualified by its private preparation");
            requireCurrentXqolPromptDispatchFrame(frame,dispatched,action);
            if(!dispatched.owner().orElseThrow().connectionGeneration().equals(actualSession.connectionGeneration()))throw new IOException("XQOL prompt action owner crossed actual connection");
            result.set("action_result",FullJsonTree.parse(dispatched.encode().bytes(),SMALL));
            result.put("action_request_id",ack.requestId()).put("instance_id",actualInstance).put("action_callback_dispatched",true)
                    .put("native_returned",dispatched.nativeReturned()).put("native_handled",false).put("native_status",dispatched.status().wire());
        } finally {
            archiveNaturalDiagnostics(output,originals,transport.diagnostics());var progress=result.deepCopy();progress.set("originals",originals.deepCopy());
            write(output,"current-xqol-prompt-progress.json",FullJsonTree.encode(progress,FullJsonTree.MAXIMUM_BYTES));
        }
    }

    record CuratedDecisionConfig(CurrentCuratedDecisions.Action action,java.util.Optional<CurrentCuratedDecisions.DecisionKey> decisionKey) {
        CuratedDecisionConfig {
            Objects.requireNonNull(action);Objects.requireNonNull(decisionKey);
            StrictJson.require((action==CurrentCuratedDecisions.Action.QUERY||action==CurrentCuratedDecisions.Action.OPEN_LIST)?decisionKey.isEmpty():decisionKey.isPresent(),"Fixed curated mode/key roles differ");
        }
    }
    static CuratedDecisionConfig currentCuratedDecisionConfig(ObjectNode config) {
        StrictJson.require(StrictJson.text(config.get("schema")).equals("xar.native-owner-snapshot-config/v28"),"Explicit v28 curated mode required");
        var action=switch(StrictJson.text(config.get("mode"))) {
            case "current_curated_decisions_query"->CurrentCuratedDecisions.Action.QUERY;
            case "current_curated_decisions_open"->CurrentCuratedDecisions.Action.OPEN_LIST;
            case "current_curated_decision_detail"->CurrentCuratedDecisions.Action.OPEN_DETAIL;
            case "current_curated_decision_confirm"->CurrentCuratedDecisions.Action.CONFIRM;
            default->throw new IllegalArgumentException("Only four independent fixed curated modes; no configured action or automatic sequence");
        };
        var fields=new java.util.HashSet<>(Set.of("schema","mode","owner_descriptor","overall_timeout_seconds","read_timeout_seconds","maximum_frames_per_operation"));
        boolean keyed=action==CurrentCuratedDecisions.Action.OPEN_DETAIL||action==CurrentCuratedDecisions.Action.CONFIRM;
        if(keyed)fields.add("decision_key");StrictJson.object(config,Set.copyOf(fields));
        java.util.Optional<CurrentCuratedDecisions.DecisionKey> key=java.util.Optional.empty();
        if(keyed)try{key=java.util.Optional.of(CurrentCuratedDecisions.DecisionKey.parse(StrictJson.text(config.get("decision_key"))));}
        catch(IOException invalid){throw new IllegalArgumentException("Decision must be one of the nine exact fixed keys",invalid);}
        return new CuratedDecisionConfig(action,key);
    }
    static void requireCurrentCuratedDecisionQueryFrame(CurrentCuratedDecisionsResult frame,CoreFrame.Prefix actual)throws IOException {
        if(frame.action()!=CurrentCuratedDecisions.Action.QUERY||frame.status()!=CurrentCuratedDecisionsResult.Status.AVAILABLE
                ||frame.effectAttempted()||frame.nativeReturned()||frame.nativeHandled()||!frame.cleanupKnown()||frame.claimSequence().signum()!=0
                ||frame.decisionKey().isPresent()||frame.factsBefore().filter(actual::equals).isEmpty()||frame.source().isEmpty())
            throw new IOException("Actual readonly curated query differs from its original Core/query role");
    }
    static CurrentCuratedDecisionsSource requireCurrentCuratedDecisionSource(CurrentCuratedDecisionsResult query,CuratedDecisionConfig config)throws IOException {
        requireCurrentCuratedDecisionQueryFrame(query,query.factsBefore().orElseThrow(()->new IOException("Original curated query Core absent")));
        var source=query.source().orElseThrow();
        if(config.action()==CurrentCuratedDecisions.Action.QUERY||!source.admits(config.action(),config.decisionKey()))
            throw new IOException("Actual source does not admit this one fixed curated action/key; no alternate or automatic followup");
        return source;
    }
    static void requireCurrentCuratedDecisionDispatchFrame(CurrentCuratedDecisionsResult query,CurrentCuratedDecisionsResult dispatched,CuratedDecisionConfig config)throws IOException {
        requireCurrentCuratedDecisionSource(query,config);
        if(dispatched.action()!=config.action()||dispatched.status()!=CurrentCuratedDecisionsResult.dispatchedStatus(config.action())
                ||!dispatched.effectAttempted()||!dispatched.nativeReturned()||!dispatched.cleanupKnown()||dispatched.claimSequence().signum()<=0
                ||!dispatched.decisionKey().equals(config.decisionKey())||!dispatched.providerGeneration().equals(query.providerGeneration())
                ||!dispatched.querySequence().equals(query.querySequence())||!dispatched.factsBefore().equals(query.factsBefore())||!dispatched.source().equals(query.source()))
            throw new IOException("Curated callback differs from original complete source/key/Core/private lease");
        // OPEN_LIST returns a real handling bool. False remains a known dispatch and is never replayed.
        if(config.action()!=CurrentCuratedDecisions.Action.OPEN_LIST&&dispatched.nativeHandled())throw new IOException("Void detail/confirm cannot claim a handling bool");
    }
    private static void runCurrentCuratedDecision(NativeGameTransport transport,GameSupervisorControl.Descriptor owner,
            NativeLaunchPlan plan,CuratedDecisionConfig config,Path output,Instant deadline,ObjectNode result,ObjectNode originals)throws IOException,InterruptedException {
        try {
            if(!(plan.load() instanceof NativeLaunchPlan.SavedGame))throw new IOException("Current curated decision requires its actual SavedGame owner");
            stage="ONE_ACTUAL_CORE_BEFORE_CURATED_DECISION";result.put("read_calls",1);
            var coreRead=transport.readCoreFrameReceived(deadline);
            archiveCurrentLetterOutcome(transport,Files.createDirectory(output.resolve("core-before-curated-decision")),"core",coreRead.original(),originals);
            if(!(coreRead instanceof NativeGameTransport.CoreReceived before)||!(before.frame() instanceof CoreFrame.Partial core))
                throw new IOException("Actual current curated Core unavailable; no configured replacement");
            requireCurrentDjcAckOwner(transport,owner,before.original(),null);
            var actualSession=before.original().custody().orElseThrow().session();var p=core.prefix();
            if(core.build()!=ExactCk3Build.CK3_121003_STEAM_26785313
                    ||!core.build().executableSha256().equalsIgnoreCase(plan.sources().review().gameExecutable().sha256())
                    ||!core.build().coreFrameAdapterId().equals(plan.adapterId())||!p.paused()||!p.mapReady()
                    ||!p.hasPlayedCharacter()||!p.playedCharacterAlive()||p.playedCharacterId()==-1||p.localPlayerId()<0||p.speed()<1||p.speed()>5)
                throw new IOException("Exact actual paused living current Core required before curated query");
            Instant until=before.validUntil().isBefore(deadline)?before.validUntil():deadline;before.requireOriginal(transport,until);
            stage="ONE_READONLY_CURRENT_CURATED_DECISIONS_QUERY";result.put("read_calls",2);
            var read=transport.readCurrentCuratedDecisions(before,until);Path queryOutput=Files.createDirectory(output.resolve("curated-query"));
            archiveCurrentLetterOutcome(transport,queryOutput,"curated_query",read.original(),originals);
            if(!(read instanceof NativeGameTransport.CuratedDecisionReceived query))throw new IOException("Actual typed curated source unavailable or UNKNOWN; no action or retry");
            until=query.validUntil().isBefore(until)?query.validUntil():until;query.requireOriginal(transport,until);
            var queryAck=query.original();requireCurrentDjcAckOwner(transport,owner,queryAck,actualSession);
            var frame=CurrentCuratedDecisionsResult.decodeOutcome(queryAck);
            if(!frame.equals(query.frame()))throw new IOException("Actual curated query differs from private retained frame");
            requireCurrentCuratedDecisionQueryFrame(frame,p);
            if(!frame.owner().orElseThrow().connectionGeneration().equals(actualSession.connectionGeneration()))throw new IOException("Curated query owner crossed actual connection");
            originals.set("curated_query_original_result",write(queryOutput,"original-result.json",queryAck.originalResultToken().orElseThrow().bytes()));
            result.set("query",FullJsonTree.parse(frame.encode().bytes(),SMALL));result.set("session",session(actualSession));
            result.put("query_available",true).put("query_request_id",queryAck.requestId());
            if(config.action()==CurrentCuratedDecisions.Action.QUERY)return;
            var selected=requireCurrentCuratedDecisionSource(frame,config);
            var prepared=transport.prepareCurrentCuratedDecision(query,config.action(),config.decisionKey());
            if(prepared.action()!=config.action()||!prepared.decisionKey().equals(config.decisionKey())||!prepared.selected().equals(selected))throw new IOException("Private preparation differs from original actual source/action/key");
            if(!prepared.deadline().equals(query.validUntil())||prepared.deadline().isAfter(deadline))throw new IOException("Original curated action deadline changed");
            Path actionOutput=Files.createDirectory(output.resolve("one-curated-action"));
            var intent=StrictJson.object().put("schema","xar.current-curated-decision-original-intent/v1").put("request_id",prepared.requestId())
                    .put("action",prepared.action().wire()).put("original_query_request_id",queryAck.requestId()).put("original_deadline_utc",prepared.deadline().toString())
                    .put("decision_applied",false).put("new_date_observed",false).put("physical_save_confirmed",false);
            if(prepared.decisionKey().isPresent())intent.put("decision_key",prepared.decisionKey().orElseThrow().wire());else intent.putNull("decision_key");
            intent.set("original_query_source",originals.get("curated_query_original_result").deepCopy());
            intent.set("original_outbound",write(actionOutput,"original-request.packet",prepared.originalPacket().value()));
            originals.set("curated_action_intent",write(actionOutput,"original-intent.json",FullJsonTree.encode(intent,SMALL)));
            stage="ONE_PRIVATE_SOURCE_CURATED_ACTION";result.put("action_calls",1);
            var outcome=transport.submitCurrentCuratedDecision(prepared);
            archiveCurrentLetterOutcome(transport,actionOutput,"curated_action",outcome,originals);
            if(!(outcome instanceof NativeActionPort.AckReceived ack))throw new IOException("Original curated action UNKNOWN or rejected; never replay");
            requireCurrentDjcAckOwner(transport,owner,ack,actualSession);var dispatched=CurrentCuratedDecisionsResult.decodeOutcome(ack);
            originals.set("curated_action_original_result",write(actionOutput,"original-result.json",ack.originalResultToken().orElseThrow().bytes()));
            if(prepared.latestFrame().filter(dispatched::equals).isEmpty())throw new IOException("Original curated ACK was not qualified by its private preparation");
            requireCurrentCuratedDecisionDispatchFrame(frame,dispatched,config);
            if(!dispatched.owner().orElseThrow().connectionGeneration().equals(actualSession.connectionGeneration()))throw new IOException("Curated action owner crossed actual connection");
            result.set("action_result",FullJsonTree.parse(dispatched.encode().bytes(),SMALL));
            result.put("action_request_id",ack.requestId()).put("action_callback_dispatched",true).put("native_handled",dispatched.nativeHandled()).put("native_status",dispatched.status().wire());
        } finally {
            archiveNaturalDiagnostics(output,originals,transport.diagnostics());var progress=result.deepCopy();progress.set("originals",originals.deepCopy());
            write(output,"current-curated-decisions-progress.json",FullJsonTree.encode(progress,FullJsonTree.MAXIMUM_BYTES));
        }
    }

    static void requireCurrentFullscreenQueryFrame(CurrentFullscreenEventResult frame,CoreFrame.Prefix actual)throws IOException {
        if(frame.action()!=CurrentFullscreenEvent.Action.QUERY_FULLSCREEN||frame.status()!=CurrentFullscreenEventResult.Status.AVAILABLE
                ||frame.effectAttempted()||frame.nativeReturned()||!frame.cleanupKnown()||frame.claimSequence().signum()!=0
                ||frame.instanceId().isPresent()||frame.factsBefore().filter(actual::equals).isEmpty()||frame.source().isEmpty())
            throw new IOException("Actual readonly fullscreen source differs from its original Core/query role");
    }
    static CurrentFullscreenEventSource requireCurrentFullscreenAcknowledgementSource(CurrentFullscreenEventResult query)throws IOException {
        var actual=query.factsBefore().orElseThrow(()->new IOException("Original fullscreen query Core absent"));
        requireCurrentFullscreenQueryFrame(query,actual);var source=query.source().orElseThrow();
        if(!source.knownAckAdmissible()||source.splashItemCount()!=1||!source.fullscreenFound()||!source.namedRootBound()
                ||!source.windowVisible()||!source.windowEnabled()||source.instanceId().filter(n->n>0).isEmpty()
                ||source.recipientCharacterId().filter(n->n==actual.playedCharacterId()).isEmpty())
            throw new IOException("Actual fullscreen source does not admit the sole fixed reviewed intro acknowledgement");
        return source;
    }
    static void requireCurrentFullscreenAcknowledgementFrame(CurrentFullscreenEventResult query,CurrentFullscreenEventResult ack)throws IOException {
        var source=requireCurrentFullscreenAcknowledgementSource(query);
        if(ack.action()!=CurrentFullscreenEvent.Action.ACKNOWLEDGE_KNOWN||ack.status()!=CurrentFullscreenEventResult.Status.ACK_DISPATCHED
                ||!ack.effectAttempted()||!ack.nativeReturned()||!ack.cleanupKnown()||ack.claimSequence().signum()<=0
                ||!ack.instanceId().equals(source.instanceId())
                ||!ack.providerGeneration().equals(query.providerGeneration())||!ack.querySequence().equals(query.querySequence())
                ||!ack.factsBefore().equals(query.factsBefore())||!ack.source().equals(query.source()))
            throw new IOException("Fullscreen callback differs from original actual source/instance/Core/lease");
    }
    private static void runCurrentFullscreenEvent(NativeGameTransport transport,GameSupervisorControl.Descriptor owner,
            NativeLaunchPlan plan,boolean acknowledgeKnownIntro,Path output,Instant deadline,ObjectNode result,ObjectNode originals)throws IOException,InterruptedException {
        try {
            if(!(plan.load() instanceof NativeLaunchPlan.SavedGame))throw new IOException("Current fullscreen event requires its actual SavedGame owner");
            stage="ONE_ACTUAL_CORE_BEFORE_FULLSCREEN_EVENT";result.put("read_calls",1);
            var coreRead=transport.readCoreFrameReceived(deadline);
            archiveCurrentLetterOutcome(transport,Files.createDirectory(output.resolve("core-before-fullscreen")),"core",coreRead.original(),originals);
            if(!(coreRead instanceof NativeGameTransport.CoreReceived before)||!(before.frame() instanceof CoreFrame.Partial core))
                throw new IOException("Actual current fullscreen Core unavailable; no configuration replacement");
            requireCurrentDjcAckOwner(transport,owner,before.original(),null);
            var actualSession=before.original().custody().orElseThrow().session();var p=core.prefix();
            if(core.build()!=ExactCk3Build.CK3_121003_STEAM_26785313
                    ||!core.build().executableSha256().equalsIgnoreCase(plan.sources().review().gameExecutable().sha256())
                    ||!core.build().coreFrameAdapterId().equals(plan.adapterId())||!p.paused()||!p.mapReady()
                    ||!p.hasPlayedCharacter()||!p.playedCharacterAlive()||p.playedCharacterId()==-1||p.localPlayerId()<0||p.speed()<1||p.speed()>5)
                throw new IOException("Exact actual paused living current Core required before fullscreen query");
            Instant until=before.validUntil().isBefore(deadline)?before.validUntil():deadline;before.requireOriginal(transport,until);
            stage="ONE_READONLY_CURRENT_FULLSCREEN_EVENT_QUERY";result.put("read_calls",2);
            var read=transport.readCurrentFullscreenEvent(before,until);Path queryOutput=Files.createDirectory(output.resolve("fullscreen-query"));
            archiveCurrentLetterOutcome(transport,queryOutput,"fullscreen_query",read.original(),originals);
            if(!(read instanceof NativeGameTransport.FullscreenReceived query))throw new IOException("Actual typed fullscreen event unavailable or UNKNOWN; no acknowledgement or retry");
            until=query.validUntil().isBefore(until)?query.validUntil():until;query.requireOriginal(transport,until);
            var queryAck=query.original();requireCurrentDjcAckOwner(transport,owner,queryAck,actualSession);
            var frame=CurrentFullscreenEventResult.decodeOutcome(queryAck);
            if(!frame.equals(query.frame()))throw new IOException("Actual fullscreen query differs from its private retained frame");
            requireCurrentFullscreenQueryFrame(frame,p);
            if(!frame.owner().orElseThrow().connectionGeneration().equals(actualSession.connectionGeneration()))throw new IOException("Fullscreen query owner crossed actual connection");
            originals.set("fullscreen_query_original_result",write(queryOutput,"original-result.json",queryAck.originalResultToken().orElseThrow().bytes()));
            result.set("query",FullJsonTree.parse(frame.encode().bytes(),SMALL));result.set("session",session(actualSession));
            result.put("query_available",true).put("query_request_id",queryAck.requestId());
            if(!acknowledgeKnownIntro)return;
            var selected=requireCurrentFullscreenAcknowledgementSource(frame);
            var prepared=transport.prepareCurrentFullscreenAcknowledgement(query);
            if(prepared.instanceId()!=selected.instanceId().orElseThrow()||!prepared.selected().equals(selected))throw new IOException("Private fullscreen preparation differs from its actual complete source");
            if(!prepared.deadline().equals(query.validUntil())||prepared.deadline().isAfter(deadline))throw new IOException("Original fullscreen acknowledgement deadline changed");
            Path ackOutput=Files.createDirectory(output.resolve("known-intro-acknowledgement"));
            var intent=StrictJson.object().put("schema","xar.current-fullscreen-event-original-intent/v1").put("request_id",prepared.requestId())
                    .put("actual_instance_id",prepared.instanceId()).put("original_query_request_id",queryAck.requestId()).put("original_deadline_utc",prepared.deadline().toString())
                    .put("fullscreen_closed",false).put("new_date_observed",false).put("physical_save_confirmed",false);
            intent.set("original_query_source",originals.get("fullscreen_query_original_result").deepCopy());
            intent.set("original_outbound",write(ackOutput,"original-request.packet",prepared.originalPacket().value()));
            originals.set("known_intro_acknowledgement_intent",write(ackOutput,"original-intent.json",FullJsonTree.encode(intent,SMALL)));
            stage="ONE_PRIVATE_SOURCE_FIXED_INTRO_ACKNOWLEDGEMENT";result.put("acknowledge_calls",1);
            var outcome=transport.submitCurrentFullscreenAcknowledgement(prepared);
            archiveCurrentLetterOutcome(transport,ackOutput,"known_intro_acknowledgement",outcome,originals);
            if(!(outcome instanceof NativeActionPort.AckReceived ack))throw new IOException("Original fullscreen acknowledgement UNKNOWN or rejected; never replay");
            requireCurrentDjcAckOwner(transport,owner,ack,actualSession);var acknowledged=CurrentFullscreenEventResult.decodeOutcome(ack);
            originals.set("known_intro_acknowledgement_original_result",write(ackOutput,"original-result.json",ack.originalResultToken().orElseThrow().bytes()));
            if(prepared.latestFrame().filter(acknowledged::equals).isEmpty())throw new IOException("Original fullscreen ACK was not qualified by its private preparation");
            requireCurrentFullscreenAcknowledgementFrame(frame,acknowledged);
            if(!acknowledged.owner().orElseThrow().connectionGeneration().equals(actualSession.connectionGeneration()))throw new IOException("Fullscreen acknowledgement owner crossed actual connection");
            result.set("acknowledgement",FullJsonTree.parse(acknowledged.encode().bytes(),SMALL));
            result.put("acknowledgement_request_id",ack.requestId()).put("acknowledge_callback_dispatched",true).put("native_status",acknowledged.status().wire());
        } finally {
            archiveNaturalDiagnostics(output,originals,transport.diagnostics());var progress=result.deepCopy();progress.set("originals",originals.deepCopy());
            write(output,"current-fullscreen-event-progress.json",FullJsonTree.encode(progress,FullJsonTree.MAXIMUM_BYTES));
        }
    }

    static void requireCurrentLetterSetQueryFrame(CurrentLetterSetResult frame,CoreFrame.Prefix actual)throws IOException {
        if(frame.action()!=CurrentLetterSet.Action.QUERY_LETTERS||frame.status()!=CurrentLetterSetResult.Status.AVAILABLE
                ||frame.effectAttempted()||frame.nativeReturned()||!frame.cleanupKnown()||frame.claimSequence().signum()!=0
                ||frame.instanceId().isPresent()||frame.factsBefore().filter(actual::equals).isEmpty()
                ||frame.source().isEmpty()||!frame.source().orElseThrow().censusComplete())
            throw new IOException("Actual readonly complete letter census differs from its original Core/query role");
    }
    static CurrentLetterSource requireCurrentLetterInstance(CurrentLetterSetResult query,int instanceId)throws IOException {
        requireCurrentLetterSetQueryFrame(query,query.factsBefore().orElseThrow(()->new IOException("Original census Core absent")));
        var selected=query.source().orElseThrow().exactInstance(instanceId);
        if(!selected.knownReplyAdmissible())throw new IOException("Explicit actual instance does not admit the fixed reviewed reply; no alternate selection");
        return selected;
    }
    static void requireCurrentLetterSetReplyFrame(CurrentLetterSetResult query,CurrentLetterSetResult reply,int instanceId)throws IOException {
        requireCurrentLetterInstance(query,instanceId);
        if(reply.action()!=CurrentLetterSet.Action.REPLY_KNOWN_INSTANCE||reply.status()!=CurrentLetterSetResult.Status.REPLY_DISPATCHED
                ||!reply.effectAttempted()||!reply.nativeReturned()||!reply.cleanupKnown()||reply.claimSequence().signum()<=0
                ||reply.instanceId().filter(n->n==instanceId).isEmpty()
                ||!reply.providerGeneration().equals(query.providerGeneration())||!reply.querySequence().equals(query.querySequence())
                ||!reply.factsBefore().equals(query.factsBefore())||!reply.source().equals(query.source()))
            throw new IOException("Actual-instance callback differs from original full census/Core/lease/explicit instance");
    }
    private static void runCurrentLetterSet(NativeGameTransport transport,GameSupervisorControl.Descriptor owner,
            NativeLaunchPlan plan,boolean replyKnown,int instanceId,Path output,Instant deadline,ObjectNode result,ObjectNode originals)throws IOException,InterruptedException {
        try {
            if(!(plan.load() instanceof NativeLaunchPlan.SavedGame))throw new IOException("Current letter requires its actual SavedGame owner");
            stage="ONE_ACTUAL_CORE_BEFORE_CURRENT_LETTER_SET";result.put("read_calls",1);
            var coreRead=transport.readCoreFrameReceived(deadline);
            archiveCurrentLetterOutcome(transport,Files.createDirectory(output.resolve("core-before-letter-set")),"core",coreRead.original(),originals);
            if(!(coreRead instanceof NativeGameTransport.CoreReceived before)||!(before.frame() instanceof CoreFrame.Partial core))
                throw new IOException("Actual current letter Core unavailable; no configuration replacement");
            requireCurrentDjcAckOwner(transport,owner,before.original(),null);
            var actualSession=before.original().custody().orElseThrow().session();var p=core.prefix();
            if(core.build()!=ExactCk3Build.CK3_121003_STEAM_26785313
                    ||!core.build().executableSha256().equalsIgnoreCase(plan.sources().review().gameExecutable().sha256())
                    ||!core.build().coreFrameAdapterId().equals(plan.adapterId())||!p.paused()||!p.mapReady()
                    ||!p.hasPlayedCharacter()||!p.playedCharacterAlive()||p.playedCharacterId()==-1||p.localPlayerId()<0||p.speed()<1||p.speed()>5)
                throw new IOException("Exact actual paused living current Core required before letter query");
            Instant until=before.validUntil().isBefore(deadline)?before.validUntil():deadline;before.requireOriginal(transport,until);
            stage="ONE_READONLY_COMPLETE_CURRENT_LETTER_CENSUS";result.put("read_calls",2);
            var read=transport.readCurrentLetterSet(before,until);Path queryOutput=Files.createDirectory(output.resolve("letter-set-query"));
            archiveCurrentLetterOutcome(transport,queryOutput,"letter_set_query",read.original(),originals);
            if(!(read instanceof NativeGameTransport.LetterSetReceived query))throw new IOException("Actual typed letter unavailable or UNKNOWN; no reply or retry");
            until=query.validUntil().isBefore(until)?query.validUntil():until;query.requireOriginal(transport,until);
            var queryAck=query.original();requireCurrentDjcAckOwner(transport,owner,queryAck,actualSession);
            var frame=CurrentLetterSetResult.decodeOutcome(queryAck);
            if(!frame.equals(query.frame()))throw new IOException("Actual letter query differs from its private retained frame");
            requireCurrentLetterSetQueryFrame(frame,p);
            if(!frame.owner().orElseThrow().connectionGeneration().equals(actualSession.connectionGeneration()))throw new IOException("Letter query owner crossed actual connection");
            originals.set("letter_set_query_original_result",write(queryOutput,"original-result.json",queryAck.originalResultToken().orElseThrow().bytes()));
            result.set("query",FullJsonTree.parse(frame.encode().bytes(),SMALL));result.set("session",session(actualSession));
            result.put("query_available",true).put("query_request_id",queryAck.requestId());
            if(!replyKnown)return;
            var selected=requireCurrentLetterInstance(frame,instanceId);
            var prepared=transport.prepareCurrentLetterInstanceReply(query,instanceId);
            if(prepared.instanceId()!=instanceId||!prepared.selected().equals(selected))throw new IOException("Private preparation differs from explicit actual census instance");
            if(!prepared.deadline().equals(query.validUntil())||prepared.deadline().isAfter(deadline))throw new IOException("Original letter reply deadline changed");
            Path replyOutput=Files.createDirectory(output.resolve("known-instance-reply"));
            var intent=StrictJson.object().put("schema","xar.current-letter-set-original-intent/v1").put("request_id",prepared.requestId())
                    .put("instance_id",instanceId).put("original_query_request_id",queryAck.requestId()).put("original_deadline_utc",prepared.deadline().toString())
                    .put("letter_closed",false).put("new_date_observed",false).put("physical_save_confirmed",false);
            intent.set("original_census",originals.get("letter_set_query_original_result").deepCopy());
            intent.set("original_outbound",write(replyOutput,"original-request.packet",prepared.originalPacket().value()));
            originals.set("known_instance_reply_intent",write(replyOutput,"original-intent.json",FullJsonTree.encode(intent,SMALL)));
            stage="ONE_EXPLICIT_ACTUAL_INSTANCE_FIXED_REPLY";result.put("reply_calls",1);
            var outcome=transport.submitCurrentLetterInstanceReply(prepared);
            archiveCurrentLetterOutcome(transport,replyOutput,"known_instance_reply",outcome,originals);
            if(!(outcome instanceof NativeActionPort.AckReceived ack))throw new IOException("Original known reply UNKNOWN or rejected; never replay");
            requireCurrentDjcAckOwner(transport,owner,ack,actualSession);var reply=CurrentLetterSetResult.decodeOutcome(ack);
            originals.set("known_instance_reply_original_result",write(replyOutput,"original-result.json",ack.originalResultToken().orElseThrow().bytes()));
            if(prepared.latestFrame().filter(reply::equals).isEmpty())throw new IOException("Original known reply ACK was not qualified by its private preparation");
            requireCurrentLetterSetReplyFrame(frame,reply,instanceId);
            if(!reply.owner().orElseThrow().connectionGeneration().equals(actualSession.connectionGeneration()))throw new IOException("Known reply owner crossed actual connection");
            result.set("reply",FullJsonTree.parse(reply.encode().bytes(),SMALL));
            result.put("reply_request_id",ack.requestId()).put("reply_callback_dispatched",true).put("native_status",reply.status().wire());
        } finally {
            archiveNaturalDiagnostics(output,originals,transport.diagnostics());var progress=result.deepCopy();progress.set("originals",originals.deepCopy());
            write(output,"current-letter-set-progress.json",FullJsonTree.encode(progress,FullJsonTree.MAXIMUM_BYTES));
        }
    }

    static void requireCurrentLetterQueryFrame(CurrentLetterResult frame,CoreFrame.Prefix actual)throws IOException {
        if(frame.action()!=CurrentLetter.Action.QUERY_LETTER||frame.status()!=CurrentLetterResult.Status.AVAILABLE
                ||frame.effectAttempted()||frame.nativeReturned()||!frame.cleanupKnown()||frame.claimSequence().signum()!=0
                ||frame.factsBefore().filter(actual::equals).isEmpty()||frame.source().isEmpty())
            throw new IOException("Actual readonly letter frame differs from its original Core or query role");
    }
    static void requireCurrentLetterReplyFrame(CurrentLetterResult query,CurrentLetterResult reply)throws IOException {
        requireCurrentLetterQueryFrame(query,query.factsBefore().orElseThrow(()->new IOException("Original letter query Core absent")));
        if(!query.source().orElseThrow().knownReplyAdmissible()
                ||reply.action()!=CurrentLetter.Action.REPLY_KNOWN||reply.status()!=CurrentLetterResult.Status.REPLY_DISPATCHED
                ||!reply.effectAttempted()||!reply.nativeReturned()||!reply.cleanupKnown()||reply.claimSequence().signum()<=0
                ||!reply.providerGeneration().equals(query.providerGeneration())||!reply.querySequence().equals(query.querySequence())
                ||!reply.factsBefore().equals(query.factsBefore())||!reply.source().equals(query.source()))
            throw new IOException("Known reply callback is not qualified against its original actual letter source/lease");
    }
    private static void archiveCurrentLetterOutcome(NativeGameTransport transport,Path directory,String key,
            NativeActionPort.DispatchOutcome outcome,ObjectNode originals)throws IOException {
        originals.set(key+"_dispatch",saveDispatch(directory,outcome));
        var uncertain=transport.originalIndeterminateCoreAcknowledgement(outcome.requestId());
        if(uncertain.isPresent())originals.set(key+"_indeterminate_ACK",saveDispatch(Files.createDirectory(directory.resolve("indeterminate")),uncertain.orElseThrow()));
    }
    private static void runCurrentLetter(NativeGameTransport transport,GameSupervisorControl.Descriptor owner,
            NativeLaunchPlan plan,boolean replyKnown,Path output,Instant deadline,ObjectNode result,ObjectNode originals)throws IOException,InterruptedException {
        try {
            if(!(plan.load() instanceof NativeLaunchPlan.SavedGame))throw new IOException("Current letter requires its actual SavedGame owner");
            stage="ONE_ACTUAL_CORE_BEFORE_CURRENT_LETTER";result.put("read_calls",1);
            var coreRead=transport.readCoreFrameReceived(deadline);
            archiveCurrentLetterOutcome(transport,Files.createDirectory(output.resolve("core-before-letter")),"core",coreRead.original(),originals);
            if(!(coreRead instanceof NativeGameTransport.CoreReceived before)||!(before.frame() instanceof CoreFrame.Partial core))
                throw new IOException("Actual current letter Core unavailable; no configuration replacement");
            requireCurrentDjcAckOwner(transport,owner,before.original(),null);
            var actualSession=before.original().custody().orElseThrow().session();var p=core.prefix();
            if(core.build()!=ExactCk3Build.CK3_121003_STEAM_26785313
                    ||!core.build().executableSha256().equalsIgnoreCase(plan.sources().review().gameExecutable().sha256())
                    ||!core.build().coreFrameAdapterId().equals(plan.adapterId())||!p.paused()||!p.mapReady()
                    ||!p.hasPlayedCharacter()||!p.playedCharacterAlive()||p.playedCharacterId()==-1||p.localPlayerId()<0||p.speed()<1||p.speed()>5)
                throw new IOException("Exact actual paused living current Core required before letter query");
            Instant until=before.validUntil().isBefore(deadline)?before.validUntil():deadline;before.requireOriginal(transport,until);
            stage="ONE_READONLY_CURRENT_LETTER_QUERY";result.put("read_calls",2);
            var read=transport.readCurrentLetter(before,until);Path queryOutput=Files.createDirectory(output.resolve("letter-query"));
            archiveCurrentLetterOutcome(transport,queryOutput,"letter_query",read.original(),originals);
            if(!(read instanceof NativeGameTransport.LetterReceived query))throw new IOException("Actual typed letter unavailable or UNKNOWN; no reply or retry");
            until=query.validUntil().isBefore(until)?query.validUntil():until;query.requireOriginal(transport,until);
            var queryAck=query.original();requireCurrentDjcAckOwner(transport,owner,queryAck,actualSession);
            var frame=CurrentLetterResult.decodeOutcome(queryAck);
            if(!frame.equals(query.frame()))throw new IOException("Actual letter query differs from its private retained frame");
            requireCurrentLetterQueryFrame(frame,p);
            if(!frame.owner().orElseThrow().connectionGeneration().equals(actualSession.connectionGeneration()))throw new IOException("Letter query owner crossed actual connection");
            originals.set("letter_query_original_result",write(queryOutput,"original-result.json",queryAck.originalResultToken().orElseThrow().bytes()));
            result.set("query",FullJsonTree.parse(frame.encode().bytes(),SMALL));result.set("session",session(actualSession));
            result.put("query_available",true).put("query_request_id",queryAck.requestId());
            if(!replyKnown)return;
            if(!frame.source().orElseThrow().knownReplyAdmissible())throw new IOException("Actual source does not admit the single fixed reviewed reply");
            var prepared=transport.prepareCurrentLetterReply(query);
            if(!prepared.deadline().equals(query.validUntil())||prepared.deadline().isAfter(deadline))throw new IOException("Original letter reply deadline changed");
            Path replyOutput=Files.createDirectory(output.resolve("known-reply"));
            var intent=StrictJson.object().put("schema","xar.current-letter-original-intent/v1").put("request_id",prepared.requestId())
                    .put("original_query_request_id",queryAck.requestId()).put("original_deadline_utc",prepared.deadline().toString())
                    .put("letter_closed",false).put("new_date_observed",false).put("physical_save_confirmed",false);
            intent.set("original_outbound",write(replyOutput,"original-request.packet",prepared.originalPacket().value()));
            originals.set("known_reply_intent",write(replyOutput,"original-intent.json",FullJsonTree.encode(intent,SMALL)));
            stage="ONE_FIXED_KNOWN_LETTER_REPLY";result.put("reply_calls",1);
            var outcome=transport.submitCurrentLetterReply(prepared);
            archiveCurrentLetterOutcome(transport,replyOutput,"known_reply",outcome,originals);
            if(!(outcome instanceof NativeActionPort.AckReceived ack))throw new IOException("Original known reply UNKNOWN or rejected; never replay");
            requireCurrentDjcAckOwner(transport,owner,ack,actualSession);var reply=CurrentLetterResult.decodeOutcome(ack);
            originals.set("known_reply_original_result",write(replyOutput,"original-result.json",ack.originalResultToken().orElseThrow().bytes()));
            if(prepared.latestFrame().filter(reply::equals).isEmpty())throw new IOException("Original known reply ACK was not qualified by its private preparation");
            requireCurrentLetterReplyFrame(frame,reply);
            if(!reply.owner().orElseThrow().connectionGeneration().equals(actualSession.connectionGeneration()))throw new IOException("Known reply owner crossed actual connection");
            result.set("reply",FullJsonTree.parse(reply.encode().bytes(),SMALL));
            result.put("reply_request_id",ack.requestId()).put("reply_callback_dispatched",true).put("native_status",reply.status().wire());
        } finally {
            archiveNaturalDiagnostics(output,originals,transport.diagnostics());var progress=result.deepCopy();progress.set("originals",originals.deepCopy());
            write(output,"current-letter-progress.json",FullJsonTree.encode(progress,FullJsonTree.MAXIMUM_BYTES));
        }
    }

    static void requireCurrentDjcSelectedCostFrame(CurrentDjcDeclarationUiResult original,
            org.xar.ck3.control.nativebridge.CurrentDjcSelectedCostResult actual)throws IOException {
        if(original.action()!=CurrentDjcDeclarationUi.Action.QUERY_UI||original.status()!=CurrentDjcDeclarationUiResult.Status.AVAILABLE
                ||!actual.nativeOk()||!actual.cleanupKnown()||actual.nativeGetterCalls()!=10
                ||!actual.factsBefore().equals(original.factsBefore())||!actual.providerGeneration().equals(original.providerGeneration())
                ||!actual.querySequence().equals(original.querySequence())||!actual.source().orElseThrow().matches(original.source().orElseThrow())
                ||!actual.ownerWitness().orElseThrow().connectionGeneration().equals(original.ownerWitness().orElseThrow().connectionGeneration()))
            throw new IOException("Readonly prices differ from their original actual private selected UI/Core/owner/lease");
    }
    static DjcUiConfig currentDjcSelectedCostConfig(ObjectNode config,boolean preview) {
        var base=currentDjcUiConfig(config,false);if(!preview)return base;
        var t=StrictJson.object(config.get("tuple_intent"),Set.of("claimant_character_id","target_title_ids","extra_configuration_ids"));
        int claimant=Math.toIntExact(StrictJson.integer(t.get("claimant_character_id"),Integer.MIN_VALUE,Integer.MAX_VALUE));
        var intent=new DjcUiTupleIntent(base.casusBelli(),claimant==-1?java.util.Optional.empty():java.util.Optional.of(new org.xar.ck3.control.contracts.NativeCharacterId(claimant)),
                currentDjcSignedIds(t.get("target_title_ids"),false),currentDjcSignedIds(t.get("extra_configuration_ids"),true));
        return new DjcUiConfig(base.target(),base.casusBelli(),java.util.Optional.of(intent),0,0);
    }
    private static void runCurrentDjcSelectedCost(NativeGameTransport transport,GameSupervisorControl.Descriptor owner,NativeLaunchPlan plan,
            DjcUiConfig config,boolean preview,Path output,Instant deadline,Duration timeout,ObjectNode result,ObjectNode originals)throws IOException,InterruptedException {
        try {
            if(!(plan.load() instanceof NativeLaunchPlan.SavedGame))throw new IOException("Selected cost requires its actual SavedGame owner");
            var initial=readCurrentDjcUiPoint(transport,owner,plan,config,output,"selected-cost-source",deadline,timeout,null,null,result,originals);var point=initial;
            if(preview) {
                var intended=config.intent().orElseThrow();var s=initial.query().frame().source().orElseThrow();
                if(s.permitsOpen()) {
                    var prepared=transport.prepareCurrentDjcUiOpen(initial.query());
                    submitCurrentDjcUiOnce(transport,owner,prepared,CurrentDjcDeclarationUiResult.Status.OPEN_DISPATCHED,initial.actualSession(),output,"open",result,originals);
                    point=readCurrentDjcUiPoint(transport,owner,plan,config,output,"cost-after-open",deadline,timeout,initial.current().prefix(),initial.actualSession(),result,originals);
                } else if(!s.residentAvailable()||!s.namedRootBound()||!s.windowVisible()||!s.windowEnabled()||s.warningSourceAvailable()) {
                    throw new IOException("Explicit preview has neither original Open permission nor a usable actual declaration source");
                }
                var row=uniqueCurrentDjcRow(intended,point.query().frame().source().orElseThrow().choices());
                var choice=transport.bindCurrentDjcChoice(point.query(),row);var selected=transport.prepareCurrentDjcUiSelection(choice);
                submitCurrentDjcUiOnce(transport,owner,selected,CurrentDjcDeclarationUiResult.Status.SELECTION_DISPATCHED,initial.actualSession(),output,"select",result,originals);
                point=readCurrentDjcUiPoint(transport,owner,plan,config,output,"cost-after-select",deadline,timeout,initial.current().prefix(),initial.actualSession(),result,originals);
                if(point.query().frame().source().orElseThrow().selected().filter(tuple->currentDjcTupleMatches(intended,tuple)).isEmpty())
                    throw new IOException("Fresh actual selected cost tuple differs from its ordered DATA intent");
            }
            result.set("session",session(point.actualSession()));result.put("query_available",true);
            stage="ONE_READONLY_CURRENT_DJC_SELECTED_COST";result.put("read_calls",result.path("read_calls").asInt()+1);
            var observed=transport.readCurrentDjcSelectedCost(point.query());Path costOutput=Files.createDirectory(output.resolve("selected-cost"));
            archiveCurrentDjcOutcome(transport,costOutput,"selected_cost",observed.original(),originals);
            if(!(observed instanceof NativeGameTransport.DjcSelectedCostReceived received))throw new IOException("Actual selected prices unavailable or UNKNOWN; no implicit Open/Select/Send or retry");
            var ack=received.original();requireCurrentDjcAckOwner(transport,owner,ack,point.actualSession());
            var frame=org.xar.ck3.control.nativebridge.CurrentDjcSelectedCostResult.decodeOutcome(ack);
            originals.set("selected_cost_original_result",write(costOutput,"original-result.json",ack.originalResultToken().orElseThrow().bytes()));
            if(!frame.equals(received.frame()))throw new IOException("Cost ACK differs from privately qualified actual frame");
            point.query().requireOriginal(transport,point.query().validUntil());requireCurrentDjcSelectedCostFrame(point.query().frame(),frame);
            var nativeResult=org.xar.ck3.control.nativebridge.NativeWire.parse(ack.originalResultToken().orElseThrow().bytes());
            result.set("costs",nativeResult.get("costs"));result.put("cost_available",true).put("native_getter_calls",frame.nativeGetterCalls())
                    .put("cost_request_id",ack.requestId()).put("original_query_request_id",point.query().original().requestId())
                    .put("original_query_deadline_utc",point.query().validUntil().toString());
        } finally {
            var progress=result.deepCopy();progress.set("originals",originals.deepCopy());
            write(output,"djc-selected-cost-progress.json",FullJsonTree.encode(progress,FullJsonTree.MAXIMUM_BYTES));
        }
    }


    /** Configured values are selection DATA only, never a native row/lease/permission. */
    record DjcUiTupleIntent(CurrentDjcTargetWarQueryResult.CasusBelliKey casusBelli,
            java.util.Optional<org.xar.ck3.control.contracts.NativeCharacterId> claimant,
            List<Integer> targetTitleIds,List<Integer> extraConfigurationIds) {
        DjcUiTupleIntent {
            Objects.requireNonNull(casusBelli);Objects.requireNonNull(claimant);
            targetTitleIds=List.copyOf(targetTitleIds);extraConfigurationIds=List.copyOf(extraConfigurationIds);
            StrictJson.require(targetTitleIds.size()<=10000&&extraConfigurationIds.size()<=10000
                    &&targetTitleIds.stream().noneMatch(id->id==-1),"Exact bounded ordered signed tuple DATA required");
        }
    }
    record DjcUiConfig(org.xar.ck3.control.contracts.NativeCharacterId target,
            CurrentDjcTargetWarQueryResult.CasusBelliKey casusBelli,java.util.Optional<DjcUiTupleIntent> intent,
            int maximumWarningPolls,long warningPollMillis) { }
    private record DjcUiPoint(NativeGameTransport.CoreReceived core,NativeGameTransport.DjcUiReceived query,
            CoreFrame.Partial current,NativeObservationPort.TransportSession actualSession) { }

    static DjcUiConfig currentDjcUiConfig(ObjectNode config,boolean submit) {
        var target=org.xar.ck3.control.contracts.NativeCharacterId.fromJson(config.get("target_character_id"));
        String key=StrictJson.text(config.get("cb_key"));
        var cb=Arrays.stream(CurrentDjcTargetWarQueryResult.CasusBelliKey.values()).filter(k->k.wire().equals(key)).findFirst()
                .orElseThrow(()->new IllegalArgumentException("Exact fixed current DJC CB key required"));
        if(!submit)return new DjcUiConfig(target,cb,java.util.Optional.empty(),0,0);
        var tuple=StrictJson.object(config.get("tuple_intent"),Set.of("claimant_character_id","target_title_ids","extra_configuration_ids"));
        int claimant=Math.toIntExact(StrictJson.integer(tuple.get("claimant_character_id"),Integer.MIN_VALUE,Integer.MAX_VALUE));
        var intent=new DjcUiTupleIntent(cb,claimant==-1?java.util.Optional.empty():java.util.Optional.of(new org.xar.ck3.control.contracts.NativeCharacterId(claimant)),
                currentDjcSignedIds(tuple.get("target_title_ids"),false),currentDjcSignedIds(tuple.get("extra_configuration_ids"),true));
        int polls=Math.toIntExact(StrictJson.integer(config.get("maximum_warning_polls"),1,64));
        long interval=StrictJson.integer(config.get("warning_poll_interval_ms"),100,5000);
        return new DjcUiConfig(target,cb,java.util.Optional.of(intent),polls,interval);
    }
    private static List<Integer> currentDjcSignedIds(JsonNode input,boolean extra) {
        StrictJson.require(input!=null&&input.isArray()&&input.size()<=10000,"Bounded ordered signed int32 vector required");
        var result=new java.util.ArrayList<Integer>();
        for(var item:input){int id=Math.toIntExact(StrictJson.integer(item,Integer.MIN_VALUE,Integer.MAX_VALUE));StrictJson.require(extra||id!=-1,"Target title -1 is absent");result.add(id);}
        return List.copyOf(result);
    }
    static boolean currentDjcTupleMatches(DjcUiTupleIntent intended,CurrentDjcDeclarationUiSource.SelectedTuple actual) {
        Objects.requireNonNull(intended);Objects.requireNonNull(actual);
        return intended.casusBelli()==actual.casusBelli()&&intended.claimant().equals(actual.claimant())
                &&intended.targetTitleIds().equals(actual.targetTitleIds())&&intended.extraConfigurationIds().equals(actual.extraConfigurationIds());
    }
    static CurrentDjcDeclarationUiSource.Choice uniqueCurrentDjcRow(DjcUiTupleIntent intended,List<CurrentDjcDeclarationUiSource.Choice> actualRows)throws IOException {
        var matches=actualRows.stream().filter(row->currentDjcTupleMatches(intended,row.tuple())).toList();
        if(matches.size()!=1)throw new IOException("Configured tuple must match exactly one actual native row, including disabled duplicates");
        var actual=matches.get(0);
        if(!actual.tuple().sourceRowEnabled())throw new IOException("The uniquely matched actual row is disabled");
        return actual;
    }
    private static Instant currentDjcReadDeadline(Instant parent,Duration timeout)throws IOException {
        Instant until=Instant.now().plus(timeout);if(parent.isBefore(until))until=parent;
        if(!Instant.now().isBefore(until))throw new IOException("Original DJC UI/Game deadline expired; no new claim");return until;
    }
    private static void requireCurrentDjcAckOwner(NativeGameTransport transport,GameSupervisorControl.Descriptor owner,
            NativeActionPort.AckReceived ack,NativeObservationPort.TransportSession expected)throws IOException {
        var custody=ack.custody().orElseThrow(()->new IOException("Actual DJC UI ACK custody absent"));custody.verify(ack);var actual=custody.session();
        if(!actual.game().equals(owner.generation())||!actual.machineId().equals(owner.machineId())||!actual.sessionId().equals(owner.sessionId())
                ||transport.diagnostics().session().filter(actual::equals).isEmpty()||expected!=null&&!expected.equals(actual))
            throw new IOException("DJC UI actual ACK crossed owner/Game/session/connection");
    }
    private static void archiveCurrentDjcOutcome(NativeGameTransport transport,Path directory,String key,
            NativeActionPort.DispatchOutcome outcome,ObjectNode originals)throws IOException {
        originals.set(key+"_dispatch",saveDispatch(directory,outcome));
        var uncertain=transport.originalIndeterminateCoreAcknowledgement(outcome.requestId());
        if(uncertain.isPresent())originals.set(key+"_indeterminate_ACK",saveDispatch(Files.createDirectory(directory.resolve("indeterminate")),uncertain.orElseThrow()));
    }
    private static CurrentDjcDeclarationUiResult archiveCurrentDjcAck(NativeGameTransport transport,GameSupervisorControl.Descriptor owner,
            NativeObservationPort.TransportSession expected,NativeActionPort.AckReceived ack,Path directory,String key,ObjectNode originals)throws IOException {
        requireCurrentDjcAckOwner(transport,owner,ack,expected);var frame=CurrentDjcDeclarationUiResult.decodeOutcome(ack);
        originals.set(key+"_original_result",write(directory,"original-result.json",ack.originalResultToken().orElseThrow().bytes()));return frame;
    }
    private static DjcUiPoint readCurrentDjcUiPoint(NativeGameTransport transport,GameSupervisorControl.Descriptor owner,NativeLaunchPlan plan,
            DjcUiConfig config,Path output,String key,Instant deadline,Duration timeout,CoreFrame.Prefix baseline,
            NativeObservationPort.TransportSession expected,ObjectNode result,ObjectNode originals)throws IOException,InterruptedException {
        stage="DJC_UI_ACTUAL_CORE_"+key;
        var coreRead=transport.readCoreFrameReceived(currentDjcReadDeadline(deadline,timeout));
        Path coreOutput=Files.createDirectory(output.resolve(key+"-core"));archiveCurrentDjcOutcome(transport,coreOutput,key+"_core",coreRead.original(),originals);
        result.put("read_calls",result.path("read_calls").asInt()+1);
        if(!(coreRead instanceof NativeGameTransport.CoreReceived before)||!(before.frame() instanceof CoreFrame.Partial current))
            throw new IOException("Actual current DJC UI Core unavailable; no configured replacement");
        requireCurrentDjcAckOwner(transport,owner,before.original(),expected);
        var session=before.original().custody().orElseThrow().session();var p=current.prefix();
        if(current.build()!=ExactCk3Build.CK3_121003_STEAM_26785313||!current.build().executableSha256().equalsIgnoreCase(plan.sources().review().gameExecutable().sha256())
                ||!current.build().coreFrameAdapterId().equals(plan.adapterId())||!p.paused()||!p.mapReady()||!p.hasPlayedCharacter()||!p.playedCharacterAlive()
                ||p.playedCharacterId()==-1||p.localPlayerId()<0||p.speed()<1||p.speed()>5||baseline!=null&&!baseline.equals(p))
            throw new IOException("Current live paused Core/actor/date differs from the actual original UI chain");
        Instant until=before.validUntil().isBefore(deadline)?before.validUntil():deadline;before.requireOriginal(transport,until);
        stage="DJC_UI_ACTUAL_QUERY_"+key;
        var queryRead=transport.readCurrentDjcDeclarationUi(before,config.target(),config.casusBelli(),until);
        Path queryOutput=Files.createDirectory(output.resolve(key+"-query"));archiveCurrentDjcOutcome(transport,queryOutput,key+"_query",queryRead.original(),originals);
        result.put("read_calls",result.path("read_calls").asInt()+1);
        if(!(queryRead instanceof NativeGameTransport.DjcUiReceived query))throw new IOException("Actual typed DJC UI query unavailable; no effect or retry");
        until=query.validUntil().isBefore(until)?query.validUntil():until;query.requireOriginal(transport,until);
        var frame=archiveCurrentDjcAck(transport,owner,session,query.original(),queryOutput,key+"_query",originals);
        if(!frame.equals(query.frame())||frame.action()!=CurrentDjcDeclarationUi.Action.QUERY_UI||frame.status()!=CurrentDjcDeclarationUiResult.Status.AVAILABLE
                ||frame.factsBefore().filter(p::equals).isEmpty())throw new IOException("Actual private DJC UI query/source changed");
        result.put(key+"_query_request_id",query.original().requestId()).put(key+"_native_status",frame.status().wire())
                .put(key+"_choice_count",frame.source().orElseThrow().choices().size());
        return new DjcUiPoint(before,query,current,session);
    }
    private static NativeActionPort.AckReceived submitCurrentDjcUiOnce(NativeGameTransport transport,GameSupervisorControl.Descriptor owner,
            NativeGameTransport.DjcUiPrepared prepared,CurrentDjcDeclarationUiResult.Status expectedStatus,NativeObservationPort.TransportSession session,
            Path output,String key,ObjectNode result,ObjectNode originals)throws IOException,InterruptedException {
        Path actionOutput=Files.createDirectory(output.resolve(key));
        var intent=StrictJson.object().put("schema","xar.current-djc-ui-original-intent/v1").put("request_id",prepared.requestId())
                .put("action",prepared.action().wire()).put("original_deadline_utc",prepared.deadline().toString())
                .put("submitted",false).put("war_created",false).put("payment_confirmed",false).put("physical_save_confirmed",false);
        intent.set("original_outbound",write(actionOutput,"original-request.packet",prepared.originalPacket().value()));
        originals.set(key+"_intent",write(actionOutput,"original-intent.json",FullJsonTree.encode(intent,SMALL)));
        stage="DJC_UI_ONE_"+prepared.action().name();result.put(key+"_calls",1);
        var outcome=transport.submitCurrentDjcUi(prepared);archiveCurrentDjcOutcome(transport,actionOutput,key,outcome,originals);
        if(!(outcome instanceof NativeActionPort.AckReceived ack))throw new IOException("Original DJC "+key+" unknown/rejected; never retry");
        var frame=archiveCurrentDjcAck(transport,owner,session,ack,actionOutput,key,originals);
        if(frame.action()!=prepared.action()||frame.status()!=expectedStatus||!frame.nativeOk()||!frame.effectAttempted()||!frame.nativeReturned()||!frame.cleanupKnown())
            throw new IOException("Original DJC "+key+" callback not positively dispatched; no successor action");
        result.put(key+"_request_id",ack.requestId()).put(key+"_native_status",frame.status().wire());return ack;
    }
    private static void requireCurrentDjcSelected(DjcUiTupleIntent intended,CurrentDjcDeclarationUiSource source)throws IOException {
        if(source.selected().filter(t->currentDjcTupleMatches(intended,t)&&t.sourceRowEnabled()).isEmpty())
            throw new IOException("Fresh selected native tuple is not the exact configured ordered intent");
    }
    private static void runCurrentDjcDeclarationUi(NativeGameTransport transport,GameSupervisorControl.Descriptor owner,NativeLaunchPlan plan,
            DjcUiConfig config,boolean submit,Path output,Instant deadline,Duration timeout,ObjectNode result,ObjectNode originals)throws IOException,InterruptedException {
        try {
            if(!(plan.load() instanceof NativeLaunchPlan.SavedGame))throw new IOException("DJC UI requires its actual SavedGame owner");
            var initial=readCurrentDjcUiPoint(transport,owner,plan,config,output,"initial",deadline,timeout,null,null,result,originals);
            result.set("session",session(initial.actualSession()));result.put("query_available",true);
            if(!submit)return;
            var intended=config.intent().orElseThrow();var selectionPoint=initial;var source=initial.query().frame().source().orElseThrow();
            if(source.permitsOpen()) {
                var opening=transport.prepareCurrentDjcUiOpen(initial.query());
                submitCurrentDjcUiOnce(transport,owner,opening,CurrentDjcDeclarationUiResult.Status.OPEN_DISPATCHED,initial.actualSession(),output,"open",result,originals);
                selectionPoint=readCurrentDjcUiPoint(transport,owner,plan,config,output,"after-open",deadline,timeout,initial.current().prefix(),initial.actualSession(),result,originals);
            } else if(!source.residentAvailable()||!source.namedRootBound()||!source.windowVisible()||!source.windowEnabled()||source.warningSourceAvailable()) {
                throw new IOException("Neither actual Open permission nor an observed usable bound resident declaration exists");
            }
            var actualRow=uniqueCurrentDjcRow(intended,selectionPoint.query().frame().source().orElseThrow().choices());
            var choice=transport.bindCurrentDjcChoice(selectionPoint.query(),actualRow);
            if(!choice.tuple().equals(actualRow.tuple()))throw new IOException("Private native choice no longer describes its actual query row");
            var selection=transport.prepareCurrentDjcUiSelection(choice);
            submitCurrentDjcUiOnce(transport,owner,selection,CurrentDjcDeclarationUiResult.Status.SELECTION_DISPATCHED,initial.actualSession(),output,"select",result,originals);
            var selected=readCurrentDjcUiPoint(transport,owner,plan,config,output,"after-select",deadline,timeout,initial.current().prefix(),initial.actualSession(),result,originals);
            var selectedSource=selected.query().frame().source().orElseThrow();requireCurrentDjcSelected(intended,selectedSource);
            if(!selectedSource.permitsSend())throw new IOException("Actual selected UI native CanSend/admission is not true");
            var send=transport.prepareCurrentDjcUiSend(selected.query());
            var sendAck=submitCurrentDjcUiOnce(transport,owner,send,CurrentDjcDeclarationUiResult.Status.SEND_DISPATCHED,initial.actualSession(),output,"send",result,originals);
            requireCurrentDjcSelected(intended,CurrentDjcDeclarationUiResult.decodeOutcome(sendAck).source().orElseThrow());
            var pending=transport.retainCurrentDjcUiSend(sendAck);
            if(pending.original()!=sendAck||!pending.deadline().equals(send.deadline()))throw new IOException("Original Send/deadline changed before warning read");
            NativeGameTransport.DjcUiWarningReady ready=null;
            for(int index=0;index<config.maximumWarningPolls();index++) {
                stage="DJC_UI_ORIGINAL_SEND_WARNING_READONLY";
                Instant receive=currentDjcReadDeadline(deadline,timeout);if(pending.deadline().isBefore(receive))receive=pending.deadline();
                if(!Instant.now().isBefore(receive))throw new IOException("Original Send deadline expired; do not replay Send");
                var read=transport.readCurrentDjcWarning(pending,receive);Path queryOutput=Files.createDirectory(output.resolve("warning-query-"+index));
                archiveCurrentDjcOutcome(transport,queryOutput,"warning_"+index,read.original(),originals);
                result.put("warning_queries",index+1).put("read_calls",result.path("read_calls").asInt()+1);
                if(!(read.original() instanceof NativeActionPort.AckReceived ack))throw new IOException("Actual warning UNKNOWN/rejected; no retry or accept");
                var frame=archiveCurrentDjcAck(transport,owner,initial.actualSession(),ack,queryOutput,"warning_"+index,originals);
                if(frame.action()!=CurrentDjcDeclarationUi.Action.QUERY_WARNING||frame.factsBefore().filter(initial.current().prefix()::equals).isEmpty())throw new IOException("Warning observation changed its original source Core");
                requireCurrentDjcSelected(intended,frame.source().orElseThrow(()->new IOException("Actual warning source absent")));
                result.put("warning_native_status",frame.status().wire());
                if(read instanceof NativeGameTransport.DjcUiWarningReady actualReady) {
                    if(!frame.equals(actualReady.frame())||frame.status()!=CurrentDjcDeclarationUiResult.Status.WARNING_READY||actualReady.validUntil().isAfter(pending.deadline()))throw new IOException("Typed warningReady differs from this actual ACK/deadline");
                    ready=actualReady;break;
                }
                if(!(read instanceof NativeGameTransport.DjcUiWarningWaiting waiting)||!frame.equals(waiting.frame())||frame.status()!=CurrentDjcDeclarationUiResult.Status.WARNING_PENDING
                        ||frame.effectAttempted()||frame.nativeReturned()||frame.claimSequence().signum()!=0||waiting.validUntil().isAfter(pending.deadline()))
                    throw new IOException("Only actual typed original-source warningPending may wait");
                if(transport.retainCurrentDjcUiSend(sendAck)!=pending)throw new IOException("Original pending Send changed");
                if(index+1<config.maximumWarningPolls()) {
                    Instant end=pending.deadline().isBefore(deadline)?pending.deadline():deadline;long remaining=Duration.between(Instant.now(),end).toMillis();
                    if(remaining<=0)throw new IOException("Original warning deadline expired");Thread.sleep(Math.min(config.warningPollMillis(),remaining));
                }
            }
            if(ready==null)throw new IOException("No typed warningReady within original finite polls; no accept or Send replay");
            if(!ready.frame().source().orElseThrow().permitsAccept())throw new IOException("Observed native CanAccept is not true");
            var accept=transport.prepareCurrentDjcWarningAcceptance(ready);
            if(!accept.deadline().equals(pending.deadline()))throw new IOException("Accept extended/replaced the original Send deadline");
            Path acceptOutput=Files.createDirectory(output.resolve("accept"));
            var intent=StrictJson.object().put("schema","xar.current-djc-warning-accept-intent/v1").put("request_id",accept.requestId()).put("source_send_request_id",sendAck.requestId())
                    .put("source_ready_query_request_id",ready.original().requestId()).put("original_deadline_utc",accept.deadline().toString()).put("submitted",false).put("war_created",false).put("payment_confirmed",false).put("physical_save_confirmed",false);
            intent.set("original_outbound",write(acceptOutput,"original-request.packet",accept.originalPacket().value()));originals.set("accept_intent",write(acceptOutput,"original-intent.json",FullJsonTree.encode(intent,SMALL)));
            stage="DJC_UI_ONE_ACCEPT_WARNING";result.put("accept_calls",1);
            var outcome=transport.submitCurrentDjcWarningAcceptance(accept);archiveCurrentDjcOutcome(transport,acceptOutput,"accept",outcome,originals);
            if(!(outcome instanceof NativeActionPort.AckReceived ack))throw new IOException("Original warning Accept UNKNOWN/rejected; never retry");
            var frame=archiveCurrentDjcAck(transport,owner,initial.actualSession(),ack,acceptOutput,"accept",originals);
            if(frame.action()!=CurrentDjcDeclarationUi.Action.ACCEPT_WARNING||frame.status()!=CurrentDjcDeclarationUiResult.Status.WARNING_DISPATCHED||!frame.nativeOk()||!frame.effectAttempted()||!frame.nativeReturned()||!frame.cleanupKnown())throw new IOException("Original warning callback not dispatched; no war/payment/SAVE credit");
            result.put("accept_request_id",ack.requestId()).put("accept_native_status",frame.status().wire()).put("accept_callback_dispatched",true);
        } finally {
            archiveNaturalDiagnostics(output,originals,transport.diagnostics());var progress=result.deepCopy();progress.set("originals",originals.deepCopy());
            write(output,"current-djc-declaration-ui-progress.json",FullJsonTree.encode(progress,FullJsonTree.MAXIMUM_BYTES));
        }
    }

    private static void runCurrentSuccessionDefault(NativeGameTransport transport,GameSupervisorControl.Descriptor owner,
            NativeLaunchPlan plan,boolean proceed,Path output,Instant deadline,ObjectNode result,ObjectNode originals)throws IOException,InterruptedException {
        try {
            if(!(plan.load() instanceof NativeLaunchPlan.SavedGame))throw new IOException("Official succession requires its actual SavedGame owner");
            stage="CURRENT_SUCCESSION_DEAD_AWARE_READONLY_QUERY";result.put("read_calls",1);
            var read=transport.readCurrentSuccessionDefault(deadline);Path queryOutput=Files.createDirectory(output.resolve("succession-query"));originals.set("succession_query_dispatch",saveDispatch(queryOutput,read.original()));
            if(!(read instanceof NativeGameTransport.SuccessionReceived received))throw new IOException("Actual typed default succession source unavailable; do not fabricate a living Core or retry Continue");
            received.requireOriginal(transport);var ack=received.original();var custody=ack.custody().orElseThrow(()->new IOException("Actual lifecycle query custody absent"));custody.verify(ack);var actualSession=custody.session();
            if(!actualSession.game().equals(owner.generation())||!actualSession.machineId().equals(owner.machineId())||!actualSession.sessionId().equals(owner.sessionId())||transport.diagnostics().session().filter(actualSession::equals).isEmpty())throw new IOException("Lifecycle source crossed actual owner/session");
            var source=org.xar.ck3.control.nativebridge.CurrentSuccessionLifecycleResult.decodeOutcome(ack);if(!source.equals(received.frame()))throw new IOException("Actual lifecycle source changed");
            result.set("session",session(actualSession));result.set("lifecycle_query",FullJsonTree.parse(ack.originalResultToken().orElseThrow().bytes(),SMALL));
            if(!proceed)return;
            stage="PREPARE_ORIGINAL_OFFICIAL_DEFAULT_CONTINUE";var prepared=transport.prepareCurrentSuccessionContinue(received);
            var intent=StrictJson.object().put("schema","xar.current-succession-default-intent/v1").put("request_id",prepared.requestId()).put("source_query_request_id",ack.requestId()).put("original_deadline_utc",prepared.deadline().toString())
                    .put("provider_generation",source.providerGeneration().toString()).put("query_sequence",source.querySequence().toString()).put("continuation_confirmed",false).put("physical_save_confirmed",false);
            intent.set("original_outbound",write(output,"succession-continue-original-request.packet",prepared.originalPacket().value()));originals.set("succession_intent",write(output,"succession-intent.json",FullJsonTree.encode(intent,SMALL)));
            stage="ONE_OFFICIAL_DEFAULT_CONTINUE";result.put("continue_calls",1);var outcome=transport.submitCurrentSuccessionContinue(prepared);Path actionOutput=Files.createDirectory(output.resolve("succession-continue"));originals.set("succession_continue_dispatch",saveDispatch(actionOutput,outcome));
            var uncertain=transport.originalIndeterminateCoreAcknowledgement(outcome.requestId());if(uncertain.isPresent())originals.set("succession_continue_indeterminate_ACK",saveDispatch(Files.createDirectory(actionOutput.resolve("indeterminate")),uncertain.orElseThrow()));
            if(!(outcome instanceof NativeActionPort.AckReceived finalAck))throw new IOException("Original official Continue unknown/rejected; no replay or inheritance credit");
            var finalCustody=finalAck.custody().orElseThrow(()->new IOException("Original Continue ACK custody absent"));finalCustody.verify(finalAck);if(!finalCustody.session().equals(actualSession))throw new IOException("Continue crossed original lifecycle session");
            var frame=org.xar.ck3.control.nativebridge.CurrentSuccessionLifecycleResult.decodeOutcome(finalAck);result.set("lifecycle_continue",FullJsonTree.parse(finalAck.originalResultToken().orElseThrow().bytes(),SMALL));
            if(frame.status()!=org.xar.ck3.control.nativebridge.CurrentSuccessionLifecycleResult.Status.DISPATCHED)throw new IOException("Official Continue not dispatched: "+frame.status().wire());
            result.put("native_callback_returned",frame.nativeReturned());
        } finally {
            archiveNaturalDiagnostics(output,originals,transport.diagnostics());var progress=result.deepCopy();progress.set("originals",originals.deepCopy());write(output,"current-succession-progress.json",FullJsonTree.encode(progress,SMALL));
        }
    }

    private static void runCurrentDjcTargetQuery(NativeGameTransport transport,GameSupervisorControl.Descriptor owner,
            NativeLaunchPlan plan,org.xar.ck3.control.contracts.NativeCharacterId target,Path output,Instant deadline,ObjectNode result,ObjectNode originals)throws IOException,InterruptedException {
        try {
            if(!(plan.load() instanceof NativeLaunchPlan.SavedGame))throw new IOException("DJC target observation requires its actual SavedGame owner");
            stage="ONE_ACTUAL_CORE_BEFORE_DJC_TARGET_QUERY";result.put("read_calls",1);
            var read=transport.readCoreFrameReceived(deadline);originals.set("core_dispatch",saveDispatch(Files.createDirectory(output.resolve("core-before-djc")),read.original()));
            if(!(read instanceof NativeGameTransport.CoreReceived before))throw new IOException("Actual current Core unavailable; no fake target-query source");
            var custody=before.original().custody().orElseThrow(()->new IOException("Actual DJC Core custody absent"));custody.verify(before.original());var actualSession=custody.session();
            if(!actualSession.game().equals(owner.generation())||!actualSession.machineId().equals(owner.machineId())||!actualSession.sessionId().equals(owner.sessionId())||transport.diagnostics().session().filter(actualSession::equals).isEmpty())
                throw new IOException("DJC Core crossed actual owner/session/connection");
            Instant until=before.validUntil().isBefore(deadline)?before.validUntil():deadline;before.requireOriginal(transport,until);
            stage="ONE_READONLY_DJC_TARGET_QUERY";result.put("read_calls",2);
            var query=transport.readCurrentDjcTargetWars(before,target,until);Path queryOutput=Files.createDirectory(output.resolve("djc-target-query"));originals.set("target_query_dispatch",saveDispatch(queryOutput,query.original()));
            var uncertain=transport.originalIndeterminateCoreAcknowledgement(query.original().requestId());if(uncertain.isPresent())originals.set("target_query_indeterminate_ACK",saveDispatch(Files.createDirectory(queryOutput.resolve("indeterminate")),uncertain.orElseThrow()));
            if(!(query instanceof NativeGameTransport.DjcTargetQueryReceived received))throw new IOException("Actual DJC target query unavailable; retain original without effect or retry");
            received.requireOriginal(transport,until);var ack=received.original();var queryCustody=ack.custody().orElseThrow(()->new IOException("Actual target-query ACK custody absent"));queryCustody.verify(ack);
            if(!queryCustody.session().equals(actualSession))throw new IOException("DJC target query crossed actual Core session");
            var frame=org.xar.ck3.control.nativebridge.CurrentDjcTargetWarQueryResult.decodeOutcome(ack);if(!frame.equals(received.frame()))throw new IOException("Actual DJC response changed");
            originals.set("query_original_result",write(queryOutput,"original-result.json",ack.originalResultToken().orElseThrow().bytes()));
            result.set("query",FullJsonTree.parse(frame.encode().bytes(),SMALL));result.set("session",session(actualSession));result.put("query_available",true);
        } finally {
            archiveNaturalDiagnostics(output,originals,transport.diagnostics());var progress=result.deepCopy();progress.set("originals",originals.deepCopy());
            write(output,"current-djc-target-query-progress.json",FullJsonTree.encode(progress,SMALL));
        }
    }

    static void requireCurrentAubObserverPlan(NativeLaunchPlan plan)throws IOException {
        if(!(plan.load() instanceof NativeLaunchPlan.SavedGame))throw new IOException("Fixed AUB observer requires its actual SavedGame owner; no menu/fake Core source");
    }
    private static void runCurrentAubObserverFixture(NativeGameTransport transport,GameSupervisorControl.Descriptor owner,
            NativeLaunchPlan plan,Path output,Instant deadline,ObjectNode result,ObjectNode originals)throws IOException,InterruptedException {
        try {
            requireCurrentAubObserverPlan(plan);
            if(!Instant.now().isBefore(deadline))throw new IOException("Original observer/Game deadline expired");
            stage="ONE_ACTUAL_CORE_BEFORE_FIXED_AUB_OBSERVER";result.put("read_calls",1);
            var read=transport.readCoreFrameReceived(deadline);Path coreOutput=Files.createDirectory(output.resolve("core-before-observer"));
            originals.set("core_dispatch",saveDispatch(coreOutput,read.original()));
            if(!(read instanceof NativeGameTransport.CoreReceived before))throw new IOException("Actual current Core unavailable before fixed observer; no retry or fabricated prefix");
            var custody=before.original().custody().orElseThrow(()->new IOException("Original observer Core custody missing"));custody.verify(before.original());
            var actualSession=custody.session();
            if(!actualSession.game().equals(owner.generation())||!actualSession.machineId().equals(owner.machineId())
                    ||!actualSession.sessionId().equals(owner.sessionId())||!transport.diagnostics().session().filter(actualSession::equals).isPresent())
                throw new IOException("Fixed observer crossed actual owner Game/session/connection");
            Instant until=before.validUntil().isBefore(deadline)?before.validUntil():deadline;before.requireOriginal(transport,until);
            var prepared=transport.prepareCurrentAubObserverFixture(before,until);
            stage="ARCHIVE_ORIGINAL_FIXED_AUB_OBSERVER_INTENT";
            var intent=StrictJson.object().put("schema","xar.current-aub-observer-intent/v1").put("request_id",prepared.requestId())
                    .put("original_Core_request_id",before.original().requestId()).put("original_deadline_utc",prepared.deadline().toString())
                    .put("source_date_raw",prepared.sourceDateRaw()).put("observer_markers_confirmed",false).put("physical_save_confirmed",false);
            intent.set("original_outbound",write(output,"observer-original-request.packet",prepared.originalPacket().value()));
            originals.set("observer_intent",write(output,"observer-intent.json",FullJsonTree.encode(intent,SMALL)));
            stage="ONE_FIXED_AUB_OBSERVER_SUBMISSION";result.put("fixture_calls",1);
            var outcome=transport.submitCurrentAubObserverFixture(prepared);Path effectOutput=Files.createDirectory(output.resolve("observer"));
            originals.set("observer_dispatch",saveDispatch(effectOutput,outcome));
            var uncertain=transport.originalIndeterminateCoreAcknowledgement(outcome.requestId());
            if(uncertain.isPresent())originals.set("observer_indeterminate_ACK",saveDispatch(Files.createDirectory(effectOutput.resolve("indeterminate")),uncertain.orElseThrow()));
            if(!(outcome instanceof NativeActionPort.AckReceived ack))throw new IOException("Fixed observer unknown/rejected; original preserved, no replay");
            var effectCustody=ack.custody().orElseThrow(()->new IOException("Original observer ACK custody absent"));effectCustody.verify(ack);
            if(!effectCustody.session().equals(actualSession))throw new IOException("Fixed observer ACK crossed original Core session");
            var decoded=CurrentAubObserverFixtureResult.decodeOutcome(ack);
            originals.set("observer_original_result",write(effectOutput,"original-result.json",ack.originalResultToken().orElseThrow().bytes()));
            if(!decoded.dispatched())throw new IOException("Fixed observer not dispatched: "+decoded.status().wire());
            result.set("session",session(actualSession));result.put("native_dispatched",true).put("native_accepted",decoded.nativeAccepted())
                    .put("cleanup_known",decoded.cleanupKnown()).put("claim_sequence",decoded.claimSequence().toString());
        } finally {
            archiveNaturalDiagnostics(output,originals,transport.diagnostics());var progress=result.deepCopy();progress.set("originals",originals.deepCopy());
            write(output,"current-aub-observer-progress.json",FullJsonTree.encode(progress,SMALL));
        }
    }

    /** Fixed two-stage native confirmation. No selector, replay, persisted-edit or SAVE authority. */
    private static void runCurrentFrontendMenu(NativeGameTransport transport,GameSupervisorControl.Descriptor owner,
            NativeLaunchPlan plan,boolean quit,Path output,Instant deadline,ObjectNode result,ObjectNode originals)throws IOException,InterruptedException {
        try {
            requireCurrentFrontendMenuPlan(plan);
            if(!Instant.now().isBefore(deadline))throw new IOException("Original menu/Game deadline expired");
            stage="CURRENT_FRONTEND_ACTUAL_MENU_QUERY";
            var read=transport.readCurrentFrontendMenu(deadline);
            originals.set("menu_query_dispatch",saveDispatch(Files.createDirectory(output.resolve("menu-query")),read.original()));
            if(!(read instanceof NativeGameTransport.FrontendMenuReceived menu))throw new IOException("Actual current no-world menu unavailable; no fake Core, effect or automatic retry");
            menu.requireOriginal(transport);var ack=menu.original();var custody=ack.custody().orElseThrow(()->new IOException("actual menu query custody absent"));custody.verify(ack);
            var actualSession=custody.session();
            if(!actualSession.game().equals(owner.generation())||!actualSession.machineId().equals(owner.machineId())||!actualSession.sessionId().equals(owner.sessionId())
                    ||!transport.diagnostics().session().filter(actualSession::equals).isPresent())throw new IOException("current menu crossed actual original Game/owner/session");
            var frame=menu.frame();requireCurrentFrontendMenuSelection(plan,frame);
            result.set("session",session(actualSession));result.put("menu_request_id",ack.requestId()).put("original_menu_deadline_utc",menu.validUntil().toString()).put("read_calls",1);
            result.set("menu",FullJsonTree.parse(FrontendMenuFrameV1PublicCodec.encode(frame).bytes(),SMALL));
            if(!quit)return;
            stage="CURRENT_FRONTEND_PREPARE_ONCE_QUIT";
            var prepared=transport.prepareCurrentFrontendMenuAction(menu,FrontendMenuFrameV1.Action.QUIT_MENU);
            var intent=StrictJson.object().put("schema","xar.current-frontend-menu-quit-intent/v1").put("request_id",prepared.requestId())
                    .put("source_query_request_id",ack.requestId()).put("original_deadline_utc",prepared.deadline().toString())
                    .put("provider_generation",frame.providerGeneration().toString()).put("query_sequence",frame.querySequence().toString())
                    .put("world_core_fabricated",false).put("application_exit_confirmed",false).put("physical_save_confirmed",false);
            intent.set("original_outbound",write(output,"menu-quit-original-request.packet",prepared.originalPacket().value()));
            originals.set("menu_quit_intent",write(output,"menu-quit-intent.json",FullJsonTree.encode(intent,SMALL)));
            stage="CURRENT_FRONTEND_ONE_QUIT_SUBMISSION";result.put("quit_calls",1);
            var outcome=transport.submitCurrentFrontendMenuAction(prepared);
            Path quitOutput=Files.createDirectory(output.resolve("menu-quit"));originals.set("menu_quit_dispatch",saveDispatch(quitOutput,outcome));
            var uncertain=transport.originalIndeterminateCoreAcknowledgement(outcome.requestId());
            if(uncertain.isPresent())originals.set("menu_quit_indeterminate_ACK",saveDispatch(Files.createDirectory(quitOutput.resolve("indeterminate")),uncertain.orElseThrow()));
            if(!(outcome instanceof NativeActionPort.AckReceived quitAck))throw new IOException("Current menu quit is unknown/rejected; original retained, no replay or exit credit");
            var quitFrame=FrontendMenuFrameV1PublicCodec.decodeOutcome(quitAck);requireCurrentFrontendMenuSelection(plan,quitFrame);
            var quitCustody=quitAck.custody().orElseThrow(()->new IOException("actual menu quit custody absent"));quitCustody.verify(quitAck);
            originals.set("menu_quit_result",write(quitOutput,"decoded-menu-result.json",FrontendMenuFrameV1PublicCodec.encode(quitFrame).bytes()));
            if(!quitCustody.session().equals(actualSession)||quitFrame.action()!=FrontendMenuFrameV1.Action.QUIT_MENU
                    ||quitFrame.status()!=FrontendMenuFrameV1.Status.EXIT_REQUESTED||!quitFrame.effectAttempted()||!quitFrame.nativeReturned())
                throw new IOException("Current menu quit callback was not requested under the original actual menu lease");
            result.put("quit_request_id",quitAck.requestId()).put("exit_requested",true).put("native_returned",true)
                    .put("application_exit_confirmed",false).put("physical_save_confirmed",false);
        } finally {
            archiveNaturalDiagnostics(output,originals,transport.diagnostics());var progress=result.deepCopy();progress.set("originals",originals.deepCopy());
            write(output,"current-menu-progress.json",FullJsonTree.encode(progress,SMALL));
        }
    }
    static void requireCurrentFrontendMenuPlan(NativeLaunchPlan plan)throws IOException {
        if(!(plan.load() instanceof NativeLaunchPlan.NewGame))throw new IOException("Explicit current no-world menu requires its actual NewGame owner plan; Saved/Continue cannot borrow it");
    }
    static void requireCurrentFrontendMenuSelection(NativeLaunchPlan plan,FrontendMenuFrameV1 frame)throws IOException {
        if(!FrontendMenuFrameV1.BUILD.executableSha256().equalsIgnoreCase(plan.sources().review().gameExecutable().sha256())
                ||!FrontendMenuFrameV1.BUILD.coreFrameAdapterId().equals(plan.adapterId()))throw new IOException("current menu result differs from actual owner executable/adapter source selection");
        if(frame.status()==FrontendMenuFrameV1.Status.AVAILABLE&&frame.action()!=FrontendMenuFrameV1.Action.QUERY_MENU)throw new IOException("Only the actual fixed menu query grants its private source occurrence");
    }

    private static void runRiteFinalConfirmation(NativeGameTransport transport,GameSupervisorControl.Descriptor owner,NativeLaunchPlan plan,
            long expectedSourceRiteId,Path output,Instant deadline,Duration receiveTimeout,int maximumConfirmationPolls,long confirmationPollMillis,ObjectNode result,ObjectNode originals)throws IOException,InterruptedException {
        try {
            if(!Instant.now().isBefore(deadline))throw new IOException("Original final-confirm/Game deadline expired");
            stage="RITE_FINAL_ACTUAL_CORE";
            var coreRead=transport.readCoreFrameReceived(deadline);
            originals.set("core_dispatch",saveDispatch(Files.createDirectory(output.resolve("core-before-final")),coreRead.original()));
            if(!(coreRead instanceof NativeGameTransport.CoreReceived before))throw new IOException("Actual final-confirm Core unavailable; no configured substitute");
            var custody=before.original().custody().orElseThrow(()->new IOException("Actual final-confirm Core custody absent"));custody.verify(before.original());
            var actualSession=custody.session();
            if(!actualSession.game().equals(owner.generation())||!actualSession.machineId().equals(owner.machineId())
                    ||!actualSession.sessionId().equals(owner.sessionId())||!transport.diagnostics().session().filter(actualSession::equals).isPresent())
                throw new IOException("Final-confirm Core crossed actual owner/Game/session");
            Instant until=before.validUntil().isBefore(deadline)?before.validUntil():deadline;
            before.requireOriginal(transport,until);
            stage="RITE_FINAL_ACTUAL_DRAFT";
            var sourceRead=transport.readRiteDraftCostsReceived(before,expectedSourceRiteId,until);
            originals.set("draft_dispatch",saveDispatch(Files.createDirectory(output.resolve("draft-before-final")),sourceRead.original()));
            if(!(sourceRead instanceof NativeGameTransport.RiteDraftCostsReceived source)||!(source.frame() instanceof RiteDraftCostsFrameV2.Partial))
                throw new IOException("Actual same-transport final-confirm Rite draft unavailable");
            until=source.validUntil().isBefore(until)?source.validUntil():until;source.requireOriginal(transport,until);
            result.set("source_draft",FullJsonTree.parse(RiteDraftCostsFrameV2PublicCodec.encode(source.frame()).bytes(),SMALL));
            stage="RITE_FINAL_ACTUAL_RITE_QUERY";
            var read=transport.readRiteDoctrineReceived(source,until);
            originals.set("rite_query_dispatch",saveDispatch(Files.createDirectory(output.resolve("rite-before-final")),read.original()));
            if(!(read instanceof NativeGameTransport.RiteDoctrineReceived query))throw new IOException("Actual typed Rite query unavailable; no final-confirm dispatch");
            until=query.validUntil().isBefore(until)?query.validUntil():until;query.requireOriginal(transport,until);requireRiteDoctrineSelection(plan,query.frame());
            if(query.frame().action()!=RiteDoctrineFrameV1.Action.QUERY||query.frame().status()!=RiteDoctrineFrameV1.Status.AVAILABLE
                    ||query.frame().facts().orElseThrow().sourceRiteId()!=expectedSourceRiteId||!query.frame().facts().orElseThrow().confirmable())
                throw new IOException("Actual source Rite is not selected/confirmable; no final-confirm dispatch");
            result.set("rite_query",FullJsonTree.parse(RiteDoctrineFrameV1PublicCodec.encode(query.frame()).bytes(),SMALL));
            result.set("session",session(actualSession));result.put("core_request_id",before.original().requestId()).put("query_request_id",query.original().requestId()).put("read_calls",3);
            var openingIntent=StrictJson.object().put("schema","xar.current-rite-final-opening-intent/v1").put("machine_id",owner.machineId())
                    .put("action",RiteDoctrineFrameV1.Action.CONFIRM_EDIT.wire()).put("source_query_request_id",query.original().requestId())
                    .put("source_rite_id",expectedSourceRiteId).put("original_deadline_utc",until.toString())
                    .put("provider_generation",query.frame().providerGeneration().toString()).put("query_sequence",query.frame().querySequence().toString())
                    .put("effect_confirmed",false).put("rite_edit_confirmed",false).put("physical_save_confirmed",false);
            originals.set("stage_one_intent",write(output,"stage-one-intent.json",FullJsonTree.encode(openingIntent,SMALL)));
            stage="RITE_FINAL_ONE_STAGE_ONE_OPENING";result.put("stage_one_calls",1);
            // This dedicated route requires actual FINAL_CAP before the old opening callback can write.
            var stageOne=transport.submitRiteFinalOpening(query,until);
            Path stageOneOutput=Files.createDirectory(output.resolve("stage-one"));originals.set("stage_one_dispatch",saveDispatch(stageOneOutput,stageOne));
            var openingUnknown=transport.originalIndeterminateCoreAcknowledgement(stageOne.requestId());
            if(openingUnknown.isPresent())originals.set("stage_one_indeterminate_ACK",saveDispatch(Files.createDirectory(stageOneOutput.resolve("indeterminate")),openingUnknown.orElseThrow()));
            if(!(stageOne instanceof NativeActionPort.AckReceived stageOneAck))throw new IOException("Stage-one opening has no qualified actual ACK; preserve original without retry/final action");
            var opening=RiteDoctrineFrameV1PublicCodec.decodeOutcome(stageOneAck);requireRiteDoctrineSelection(plan,opening);
            var openingCustody=stageOneAck.custody().orElseThrow(()->new IOException("Stage-one ACK custody absent"));openingCustody.verify(stageOneAck);
            if(!openingCustody.session().equals(actualSession)||opening.action()!=RiteDoctrineFrameV1.Action.CONFIRM_EDIT
                    ||opening.status()!=RiteDoctrineFrameV1.Status.CONFIRMATION_DISPATCHED||!opening.nativeHandled())
                throw new IOException("Actual same-session opening callback did not dispatch confirmation");
            originals.set("stage_one_result",write(stageOneOutput,"decoded-rite-result.json",RiteDoctrineFrameV1PublicCodec.encode(opening).bytes()));
            var pending=transport.retainRiteFinalPreparation(stageOneAck);
            if(pending.original()!=stageOneAck||pending.deadline().isAfter(until)||pending.deadline().toEpochMilli()!=until.toEpochMilli())
                throw new IOException("Final confirmation cannot replace its actual opening receipt or extend original claim deadline");
            result.put("stage_one_request_id",stageOneAck.requestId()).put("original_final_deadline_utc",pending.deadline().toString());
            NativeGameTransport.RiteFinalReady ready=null;
            NativeActionPort.AckReceived readyAck=null;
            for(int index=0;index<maximumConfirmationPolls;index++) {
                stage="RITE_FINAL_ORIGINAL_PENDING_READONLY_QUERY";
                Instant receiveDeadline=Instant.now().plus(receiveTimeout);
                if(deadline.isBefore(receiveDeadline))receiveDeadline=deadline;
                if(pending.deadline().isBefore(receiveDeadline))receiveDeadline=pending.deadline();
                if(!Instant.now().isBefore(receiveDeadline))throw new IOException("Original final-confirm deadline expired before readonly query; no new claim");
                var finalRead=transport.readRiteFinalConfirmation(pending,receiveDeadline);
                Path queryOutput=Files.createDirectory(output.resolve("final-ready-"+index));
                originals.set("final_query_"+index+"_dispatch",saveDispatch(queryOutput,finalRead.original()));
                result.put("read_calls",index+4).put("confirmation_queries",index+1);
                // Unknown/zero/type/source failures never qualify for waiting. Decode this actual ACK only.
                if(!(finalRead.original() instanceof NativeActionPort.AckReceived actualAck))throw new IOException("Actual final-confirm query unknown/rejected; no readonly retry or accept");
                var frame=RiteDoctrineFrameV1PublicCodec.decodeOutcome(actualAck);requireRiteDoctrineSelection(plan,frame);
                var queryCustody=actualAck.custody().orElseThrow(()->new IOException("Final-confirm query custody absent"));queryCustody.verify(actualAck);
                originals.set("final_query_"+index+"_result",write(queryOutput,"decoded-rite-result.json",RiteDoctrineFrameV1PublicCodec.encode(frame).bytes()));
                if(!queryCustody.session().equals(actualSession)||frame.action()!=RiteDoctrineFrameV1.Action.QUERY_FINAL_CONFIRMATION
                        ||!frame.coreFrame().equals(before.frame())||frame.facts().orElseThrow().sourceRiteId()!=expectedSourceRiteId
                        ||queryCustody.writeEntered().order().compareTo(openingCustody.responseReceived().order())<=0
                        ||queryCustody.responseReceived().observedAt().isAfter(receiveDeadline))
                    throw new IOException("Final query changed actual original source/session/chronology; no readonly retry");
                result.put("final_query_status",frame.status().wire());
                if(finalRead instanceof NativeGameTransport.RiteFinalReady actualReady) {
                    if(!frame.equals(actualReady.frame())||frame.status()!=RiteDoctrineFrameV1.Status.FINAL_CONFIRMATION_READY
                            ||actualReady.validUntil().isAfter(pending.deadline()))throw new IOException("Ready receipt changed original confirmation contract");
                    ready=actualReady;readyAck=actualAck;break;
                }
                if(!(finalRead instanceof NativeGameTransport.RiteFinalWaiting waiting)||!frame.equals(waiting.frame())
                        ||waiting.validUntil().isAfter(pending.deadline())||frame.status()!=RiteDoctrineFrameV1.Status.FINAL_CONFIRMATION_PENDING||frame.effectAttempted()||frame.nativeReturned()
                        ||frame.nativeHandled()||frame.claimSequence().signum()!=0)
                    throw new IOException("Only typed original-source modal-pending may wait; other unavailable results stop");
                // Revalidate the private original preparation after this receipt. No caller flag or reason string grants a retry.
                if(transport.retainRiteFinalPreparation(stageOneAck)!=pending)throw new IOException("Original final-confirm preparation changed while pending");
                if(index+1<maximumConfirmationPolls) {
                    Instant waitUntil=pending.deadline().isBefore(deadline)?pending.deadline():deadline;
                    long remaining=Duration.between(Instant.now(),waitUntil).toMillis();
                    if(remaining<=0)throw new IOException("Original final-confirm deadline expired while pending");
                    Thread.sleep(Math.min(confirmationPollMillis,remaining));
                }
            }
            if(ready==null||readyAck==null)throw new IOException("Final-confirmation ready not observed within original finite readonly polls; no accept/replay");
            var prepared=transport.prepareRiteFinalConfirmation(ready);
            if(!prepared.deadline().equals(pending.deadline()))throw new IOException("Final prepared request changed original opening claim deadline");
            var finalIntent=StrictJson.object().put("schema","xar.current-rite-final-confirmation-intent/v1").put("machine_id",owner.machineId())
                    .put("action",RiteDoctrineFrameV1.Action.ACCEPT_FINAL_CONFIRMATION.wire()).put("request_id",prepared.requestId())
                    .put("stage_one_request_id",stageOneAck.requestId()).put("ready_query_request_id",readyAck.requestId())
                    .put("original_deadline_utc",prepared.deadline().toString()).put("source_rite_id",expectedSourceRiteId)
                    .put("effect_confirmed",false).put("rite_edit_confirmed",false).put("physical_save_confirmed",false);
            finalIntent.set("original_outbound",write(output,"final-original-request.packet",prepared.originalPacket().value()));
            originals.set("final_intent",write(output,"final-intent.json",FullJsonTree.encode(finalIntent,SMALL)));
            stage="RITE_FINAL_ONE_ACCEPT_SUBMISSION";result.put("final_confirmation_calls",1);
            var finalOutcome=transport.submitRiteFinalConfirmation(prepared);
            Path finalOutput=Files.createDirectory(output.resolve("final-accept"));originals.set("final_dispatch",saveDispatch(finalOutput,finalOutcome));
            var finalUnknown=transport.originalIndeterminateCoreAcknowledgement(finalOutcome.requestId());
            if(finalUnknown.isPresent())originals.set("final_indeterminate_ACK",saveDispatch(Files.createDirectory(finalOutput.resolve("indeterminate")),finalUnknown.orElseThrow()));
            if(!(finalOutcome instanceof NativeActionPort.AckReceived finalAck))throw new IOException("Final accept has no qualified ACK; preserve original without replay or persisted-edit credit");
            var finalFrame=RiteDoctrineFrameV1PublicCodec.decodeOutcome(finalAck);requireRiteDoctrineSelection(plan,finalFrame);
            var finalCustody=finalAck.custody().orElseThrow(()->new IOException("Final accept custody absent"));finalCustody.verify(finalAck);
            originals.set("final_result",write(finalOutput,"decoded-rite-result.json",RiteDoctrineFrameV1PublicCodec.encode(finalFrame).bytes()));
            if(!finalCustody.session().equals(actualSession)||finalFrame.action()!=RiteDoctrineFrameV1.Action.ACCEPT_FINAL_CONFIRMATION
                    ||finalFrame.status()!=RiteDoctrineFrameV1.Status.FINAL_CONFIRMATION_DISPATCHED||!finalFrame.effectAttempted()||!finalFrame.nativeReturned()||finalFrame.nativeHandled())
                throw new IOException("Final native callback not dispatched under the original same-session claim; no retry");
            result.put("final_request_id",finalAck.requestId()).put("native_status",finalFrame.status().wire()).put("final_callback_dispatched",true)
                    .put("effect_confirmed",false).put("rite_edit_confirmed",false).put("physical_save_confirmed",false).put("business_or_ledger_SAVE_credit",false);
        } finally {
            archiveNaturalDiagnostics(output,originals,transport.diagnostics());
            var progress=result.deepCopy();progress.set("originals",originals.deepCopy());
            write(output,"rite-final-progress.json",FullJsonTree.encode(progress,SMALL));
        }
    }

    /** One current-Core claim. Status sampling never refreshes that claim or performs another resume. */
    private static void runCurrentDateAdvance(NativeGameTransport transport,GameSupervisorControl.Descriptor owner,NativeLaunchPlan plan,
            Path output,Instant deadline,Duration receiveTimeout,int maximumPolls,long pollMillis,ObjectNode result,ObjectNode originals)throws IOException,InterruptedException {
        NativeGameTransport.CurrentDatePrepared prepared=null;
        try {
            if(!Instant.now().isBefore(deadline))throw new IOException("Original current date/Game deadline expired");
            stage="CURRENT_DATE_ACTUAL_BEFORE_CORE";
            var coreRead=transport.readCoreFrameReceived(deadline);
            originals.set("core_before_dispatch",saveDispatch(Files.createDirectory(output.resolve("core-before-date")),coreRead.original()));
            if(!(coreRead instanceof NativeGameTransport.CoreReceived before))throw new IOException("Actual current date Core unavailable; no substitute or replay");
            var beforeFrame=requireCurrentDateSource(before.frame());
            if(!beforeFrame.build().executableSha256().equalsIgnoreCase(plan.sources().review().gameExecutable().sha256())
                    ||!beforeFrame.build().coreFrameAdapterId().equals(plan.adapterId()))throw new IOException("Current date Core differs from actual owner source selection");
            var custody=before.original().custody().orElseThrow(()->new IOException("Actual current date Core custody absent"));custody.verify(before.original());
            var actualSession=custody.session();
            if(!actualSession.game().equals(owner.generation())||!actualSession.machineId().equals(owner.machineId())
                    ||!actualSession.sessionId().equals(owner.sessionId())||!transport.diagnostics().session().filter(actualSession::equals).isPresent())
                throw new IOException("Current date Core crossed actual owner/Game/session");
            Instant actionDeadline=before.validUntil().isBefore(deadline)?before.validUntil():deadline;
            before.requireOriginal(transport,actionDeadline);
            prepared=transport.prepareCurrentDateAdvance(before,actionDeadline);
            if(prepared.sourceDateRaw()!=beforeFrame.prefix().dateRaw())throw new IOException("Prepared current date source changed");
            result.set("session",session(actualSession));
            result.set("core_before",FullJsonTree.parse(CoreFramePublicCodec.encode(beforeFrame).bytes(),SMALL));
            result.put("core_before_request_id",before.original().requestId()).put("read_calls",1)
                    .put("request_id",prepared.requestId()).put("operation_id",prepared.operationId())
                    .put("original_action_deadline_utc",prepared.deadline().toString()).put("source_date_raw",prepared.sourceDateRaw());
            var intent=StrictJson.object().put("schema","xar.current-date-advance-intent/v1").put("machine_id",owner.machineId())
                    .put("request_id",prepared.requestId()).put("operation_id",prepared.operationId())
                    .put("original_action_deadline_utc",prepared.deadline().toString()).put("source_Core_request_id",before.original().requestId())
                    .put("source_date_raw",prepared.sourceDateRaw()).put("physical_save_confirmed",false).put("save_calls",0);
            intent.set("original_outbound",write(output,"date-original-request.packet",prepared.originalPacket().value()));
            originals.set("advance_intent",write(output,"date-intent.json",FullJsonTree.encode(intent,SMALL)));
            stage="ONE_CURRENT_DATE_ADVANCE_SUBMISSION";
            result.put("advance_calls",1);
            var outcome=transport.submitCurrentDateAdvance(prepared);
            Path advanceOutput=Files.createDirectory(output.resolve("date-advance"));
            originals.set("advance_dispatch",saveDispatch(advanceOutput,outcome));
            var uncertain=transport.originalIndeterminateCoreAcknowledgement(outcome.requestId());
            if(uncertain.isPresent())originals.set("advance_indeterminate_ACK",saveDispatch(Files.createDirectory(advanceOutput.resolve("indeterminate")),uncertain.orElseThrow()));
            DateAdvanceFrameV1 frame=null;
            if(outcome instanceof NativeActionPort.AckReceived) {
                frame=requireCurrentDateReceipt(outcome,prepared,DateAdvanceFrameV1.Step.ADVANCE,beforeFrame.prefix());
                originals.set("advance_result",write(advanceOutput,"decoded-date-result.json",DateAdvanceFrameV1PublicCodec.encode(frame).bytes()));
                result.put("native_status",frame.status().wire());
                if(!frame.accepted())throw new IOException("Current date advance rejected or indeterminate; preserve original claim without replay");
            } else if(!prepared.originalUnknown())throw new IOException("Current date advance has no qualified submitted ACK; no replay");
            // A query is a bounded readonly observation of exactly the original operation/Core/deadline.
            // In particular, an original UNKNOWN remains UNKNOWN even if a later query observes a terminal.
            for(int index=0;index<maximumPolls&&(frame==null||frame.status()!=DateAdvanceFrameV1.Status.COMPLETED);index++) {
                if(!Instant.now().isBefore(deadline))throw new IOException("Current date readonly query parent deadline expired; no manual pause/retry");
                stage="CURRENT_DATE_ORIGINAL_OPERATION_READONLY_QUERY";
                Instant receiveDeadline=Instant.now().plus(receiveTimeout);if(deadline.isBefore(receiveDeadline))receiveDeadline=deadline;
                var query=transport.queryCurrentDateAdvance(prepared,receiveDeadline);
                Path queryOutput=Files.createDirectory(output.resolve("date-query-"+index));
                originals.set("query_"+index+"_dispatch",saveDispatch(queryOutput,query));
                result.put("status_queries",index+1).put("original_unknown",prepared.originalUnknown());
                // latestFrame intentionally retains the last good receipt on failure. Decode THIS ACK first.
                frame=requireCurrentDateReceipt(query,prepared,DateAdvanceFrameV1.Step.QUERY,beforeFrame.prefix());
                originals.set("query_"+index+"_result",write(queryOutput,"decoded-date-result.json",DateAdvanceFrameV1PublicCodec.encode(frame).bytes()));
                result.put("native_status",frame.status().wire());
                if(frame.status()==DateAdvanceFrameV1.Status.COMPLETED)break;
                if(frame.status()!=DateAdvanceFrameV1.Status.SUBMITTED&&frame.status()!=DateAdvanceFrameV1.Status.RUNNING)
                    throw new IOException("Current date status is not a running claim; no new ARM/resume/operation");
                if(index+1<maximumPolls) {
                    long remaining=Duration.between(Instant.now(),deadline).toMillis();
                    if(remaining<=0)throw new IOException("Current date readonly polling budget expired");
                    Thread.sleep(Math.min(pollMillis,remaining));
                }
            }
            if(frame==null||frame.status()!=DateAdvanceFrameV1.Status.COMPLETED||!frame.exactDayConfirmed()||!frame.shutdownSafe())
                throw new IOException("Exact current one-day terminal not observed within original bounded queries");
            result.put("sentinel_exact_boundary_observed",true);
            if(prepared.originalUnknown())throw new IOException("Original advance UNKNOWN is retained despite later terminal DATA; no successful advance credit");
            stage="CURRENT_DATE_INDEPENDENT_FRESH_AFTER_CORE";
            if(!Instant.now().isBefore(deadline))throw new IOException("No remaining Game budget for independent after-Core");
            var afterRead=transport.readCoreFrameReceived(deadline);
            originals.set("core_after_dispatch",saveDispatch(Files.createDirectory(output.resolve("core-after-date")),afterRead.original()));
            if(!(afterRead instanceof NativeGameTransport.CoreReceived after))throw new IOException("Independent actual after-Core unavailable");
            var afterCustody=after.original().custody().orElseThrow(()->new IOException("Independent after-Core custody absent"));afterCustody.verify(after.original());
            if(!afterCustody.session().equals(actualSession)||after.original().requestId().equals(before.original().requestId())
                    ||!transport.diagnostics().session().filter(actualSession::equals).isPresent())throw new IOException("Independent after-Core crossed its original session or reused before request");
            after.requireOriginal(transport,after.validUntil().isBefore(deadline)?after.validUntil():deadline);
            requireCurrentDateAfter(beforeFrame,after.frame());
            result.set("core_after",FullJsonTree.parse(CoreFramePublicCodec.encode(after.frame()).bytes(),SMALL));
            result.put("core_after_request_id",after.original().requestId()).put("read_calls",2).put("one_day_observed",true)
                    .put("independent_after_core_verified",true).put("physical_save_confirmed",false).put("business_or_ledger_SAVE_credit",false);
        } finally {
            if(prepared!=null)result.put("original_unknown",prepared.originalUnknown());
            archiveNaturalDiagnostics(output,originals,transport.diagnostics());
            var progress=result.deepCopy();progress.set("originals",originals.deepCopy());
            write(output,"current-date-progress.json",FullJsonTree.encode(progress,SMALL));
        }
    }
    private static DateAdvanceFrameV1 requireCurrentDateReceipt(NativeActionPort.DispatchOutcome outcome,
            NativeGameTransport.CurrentDatePrepared prepared,DateAdvanceFrameV1.Step step,CoreFrame.Prefix before)throws IOException {
        var frame=DateAdvanceFrameV1PublicCodec.decodeOutcome(outcome);
        if(frame.step()!=step||!frame.operationId().equals(prepared.operationId())
                ||frame.coreBefore().isPresent()&&!frame.coreBefore().orElseThrow().equals(before)
                ||!prepared.latestFrame().filter(frame::equals).isPresent())throw new IOException("Current date ACK differs from this original prepared operation/receipt");
        return frame;
    }
    static CoreFrame.Partial requireCurrentDateSource(CoreFrame frame)throws IOException {
        var partial=requireCurrentDateMap(frame);
        if(partial.prefix().dateRaw()>Integer.MAX_VALUE-24)throw new IOException("Current date source cannot safely represent +24 raw ticks");
        return partial;
    }
    private static CoreFrame.Partial requireCurrentDateMap(CoreFrame frame)throws IOException {
        if(!(frame instanceof CoreFrame.Partial partial)||partial.build()!=ExactCk3Build.CK3_121003_STEAM_26785313)
            throw new IOException("Current narrow Core required; legacy/Full/unavailable cannot authorize this operation");
        var p=partial.prefix();
        if(p.dateRaw()<=0||p.speed()<1||p.speed()>5||!p.paused()||p.localPlayerId()<0||!p.mapReady()||!p.hasPlayedCharacter()||p.playedCharacterId()==-1||!p.playedCharacterAlive())
            throw new IOException("Actual current paused living map Core required");
        return partial;
    }
    static void requireCurrentDateAfter(CoreFrame before,CoreFrame after)throws IOException {
        var source=requireCurrentDateSource(before).prefix();var current=requireCurrentDateMap(after).prefix();
        if(current.dateRaw()!=source.dateRaw()+24||current.speed()!=source.speed()||current.localPlayerId()!=source.localPlayerId()
                ||current.playedCharacterId()!=source.playedCharacterId())throw new IOException("Independent current after-Core is not exact +24 with unchanged speed/player/actor");
    }

    private static void runRiteDoctrine(NativeGameTransport transport,GameSupervisorControl.Descriptor owner,NativeLaunchPlan plan,
            long expectedSourceRiteId,RiteDoctrineFrameV1.Action action,Path output,Instant deadline,ObjectNode result,ObjectNode originals)throws IOException,InterruptedException {
        if(!Instant.now().isBefore(deadline))throw new IOException("Original Rite/Game deadline expired");
        stage="ONE_CURRENT_RITE_ACTUAL_CORE";var coreRead=transport.readCoreFrameReceived(deadline);
        originals.set("core_dispatch",saveDispatch(Files.createDirectory(output.resolve("core-before-rite")),coreRead.original()));
        if(!(coreRead instanceof NativeGameTransport.CoreReceived before))throw new IOException("Actual Rite Core unavailable; preserve original without retry");
        var custody=before.original().custody().orElseThrow(()->new IOException("actual Rite Core custody absent"));custody.verify(before.original());
        if(!custody.session().game().equals(owner.generation())||!custody.session().machineId().equals(owner.machineId())||!custody.session().sessionId().equals(owner.sessionId())||!transport.diagnostics().session().filter(custody.session()::equals).isPresent())throw new IOException("Rite Core crossed actual owner/Game/session");
        Instant until=before.validUntil().isBefore(deadline)?before.validUntil():deadline;
        stage="ONE_CURRENT_RITE_ACTUAL_DRAFT";var sourceRead=transport.readRiteDraftCostsReceived(before,expectedSourceRiteId,until);
        originals.set("draft_dispatch",saveDispatch(Files.createDirectory(output.resolve("draft-before-rite")),sourceRead.original()));
        if(!(sourceRead instanceof NativeGameTransport.RiteDraftCostsReceived source)||!(source.frame() instanceof RiteDraftCostsFrameV2.Partial))throw new IOException("Actual same-transport Rite draft unavailable; no configured substitute");
        until=source.validUntil().isBefore(until)?source.validUntil():until;source.requireOriginal(transport,until);
        result.set("source_draft",FullJsonTree.parse(RiteDraftCostsFrameV2PublicCodec.encode(source.frame()).bytes(),FullJsonTree.MAXIMUM_BYTES));
        stage="ONE_CURRENT_RITE_TYPED_QUERY";var read=transport.readRiteDoctrineReceived(source,until);
        originals.set("query_dispatch",saveDispatch(Files.createDirectory(output.resolve("rite-query")),read.original()));
        if(!(read instanceof NativeGameTransport.RiteDoctrineReceived query))throw new IOException("Actual typed Rite query unavailable; original preserved without replay");
        until=query.validUntil().isBefore(until)?query.validUntil():until;query.requireOriginal(transport,until);requireRiteDoctrineSelection(plan,query.frame());
        result.set("rite_query",FullJsonTree.parse(RiteDoctrineFrameV1PublicCodec.encode(query.frame()).bytes(),FullJsonTree.MAXIMUM_BYTES));
        result.put("core_request_id",before.original().requestId()).put("query_request_id",query.original().requestId()).put("read_calls",3);
        result.set("session",session(custody.session()));
        if(action==RiteDoctrineFrameV1.Action.QUERY){archiveNaturalDiagnostics(output,originals,transport.diagnostics());return;}
        var intent=StrictJson.object().put("schema","xar.current-rite-action-intent/v1").put("action",action.wire())
                .put("source_query_request_id",query.original().requestId()).put("source_rite_id",expectedSourceRiteId).put("original_deadline_utc",until.toString())
                .put("provider_generation",query.frame().providerGeneration().toString()).put("query_sequence",query.frame().querySequence().toString())
                .put("effect_confirmed",false).put("rite_edit_confirmed",false).put("physical_save_confirmed",false);
        originals.set("action_intent",write(output,"rite-action-intent.json",FullJsonTree.encode(intent,SMALL)));
        stage="ONE_CURRENT_RITE_FIXED_ACTION";var outcome=transport.submitRiteDoctrineAction(query,action,until);
        result.put("effect_calls",1).put("request_id",outcome.requestId());originals.set("action_dispatch",saveDispatch(Files.createDirectory(output.resolve("rite-action")),outcome));
        var uncertain=transport.originalIndeterminateCoreAcknowledgement(outcome.requestId());
        if(uncertain.isPresent())originals.set("indeterminate_ACK",saveDispatch(Files.createDirectory(output.resolve("rite-indeterminate")),uncertain.orElseThrow()));
        archiveNaturalDiagnostics(output,originals,transport.diagnostics());
        if(!(outcome instanceof NativeActionPort.AckReceived ack))throw new IOException("Rite action has no qualified ACK; original retained without replay");
        var frame=RiteDoctrineFrameV1PublicCodec.decodeOutcome(ack);requireRiteDoctrineSelection(plan,frame);
        result.set("rite_result",FullJsonTree.parse(RiteDoctrineFrameV1PublicCodec.encode(frame).bytes(),FullJsonTree.MAXIMUM_BYTES));
        result.put("native_status",frame.status().wire()).put("rite_edit_confirmed",false).put("physical_save_confirmed",false).put("business_or_ledger_SAVE_credit",false);
        if(!frame.nativeOk())throw new IOException("Fixed Rite action rejected or indeterminate; no persisted-edit credit");
    }
    static void requireRiteDoctrineSelection(NativeLaunchPlan plan,RiteDoctrineFrameV1 frame)throws IOException {
        var build=frame.coreFrame().build();
        if(!build.executableSha256().equalsIgnoreCase(plan.sources().review().gameExecutable().sha256())||!build.coreFrameAdapterId().equals(plan.adapterId()))throw new IOException("current Rite result differs from actual owner source selection");
    }

    private static void runLiteralNavigation(NativeGameTransport transport,GameSupervisorControl.Descriptor owner,NativeLaunchPlan plan,
            NativeGameTransport.NavigationAction action,Path output,Instant deadline,ObjectNode result,ObjectNode originals)throws IOException,InterruptedException {
        if(!Instant.now().isBefore(deadline))throw new IOException("Original navigation/Game deadline expired");
        stage="ONE_LITERAL_NAVIGATION_ACTUAL_CORE";
        var coreRead=transport.readCoreFrameReceived(deadline);Path coreOutput=Files.createDirectory(output.resolve("core-before-navigation"));
        originals.set("core_dispatch",saveDispatch(coreOutput,coreRead.original()));
        if(!(coreRead instanceof NativeGameTransport.CoreReceived before))throw new IOException("Actual navigation Core unavailable; retain original, no retry");
        var custody=before.original().custody().orElseThrow(()->new IOException("Actual navigation Core custody absent"));custody.verify(before.original());
        if(!custody.session().game().equals(owner.generation())||!custody.session().machineId().equals(owner.machineId())||!custody.session().sessionId().equals(owner.sessionId()))throw new IOException("Navigation Core crossed actual owner Game/session");
        Instant until=before.validUntil().isBefore(deadline)?before.validUntil():deadline;
        stage="ONE_LITERAL_NAVIGATION_QUERY";var read=transport.readNavigationGuiControlsV2(before,action,until);
        originals.set("query_dispatch",saveDispatch(Files.createDirectory(output.resolve("navigation-query")),read.original()));
        if(!(read instanceof NativeGameTransport.GuiControlsReceivedV2 query))throw new IOException("Actual literal root query unavailable; retain original, no retry");
        until=query.validUntil().isBefore(until)?query.validUntil():until;query.requireOriginal(transport,until);requireGuiControlsSelection(plan,query.frame());
        result.set("navigation_query",FullJsonTree.parse(GuiControlsFrameV2PublicCodec.encode(query.frame()).bytes(),FullJsonTree.MAXIMUM_BYTES));
        stage="ONE_LITERAL_NAVIGATION_ACTIVATION";
        var outcome=transport.submitNavigationGuiControlV2(query,action,until);result.put("activation_calls",1).put("request_id",outcome.requestId());
        originals.set("activation_dispatch",saveDispatch(Files.createDirectory(output.resolve("navigation-activation")),outcome));
        var uncertain=transport.originalIndeterminateCoreAcknowledgement(outcome.requestId());
        if(uncertain.isPresent())originals.set("indeterminate_ACK",saveDispatch(Files.createDirectory(output.resolve("navigation-indeterminate")),uncertain.orElseThrow()));
        archiveNaturalDiagnostics(output,originals,transport.diagnostics());
        if(!(outcome instanceof NativeActionPort.AckReceived ack))throw new IOException("Literal navigation has no qualified ACK; original retained, no replay");
        var frame=GuiControlsFrameV2PublicCodec.decodeOutcome(ack);requireGuiControlsSelection(plan,frame);
        result.set("navigation_result",FullJsonTree.parse(GuiControlsFrameV2PublicCodec.encode(frame).bytes(),FullJsonTree.MAXIMUM_BYTES));
        result.put("native_status",frame.status().wire()).put("effect_confirmed",false).put("window_open_confirmed",false).put("physical_save_confirmed",false);
        if(frame.status()!=GuiControlsFrameV2.Status.SUBMITTED)throw new IOException("Literal navigation not submitted; no window/effect credit");
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
    /**
     * Request DATA from the original Full frame. The caller must independently
     * retain its actual Full READ, same Managed owner and original deadline.
     */
    static org.xar.ck3.control.application.action.NativeRequest preparedFullClockRequest(
            String step,org.xar.ck3.control.application.action.RawJson actualFullState,String snapshotId,
            java.math.BigInteger revision,Instant originalDeadline,java.util.Optional<ExactRef> mapped112)throws IOException {
        Objects.requireNonNull(actualFullState);Objects.requireNonNull(mapped112);
        JsonNode parsed=FullJsonTree.parse(actualFullState.bytes(),FullJsonTree.MAXIMUM_BYTES);
        StrictJson.require(parsed instanceof ObjectNode,"original Full state object required");
        ObjectNode state=(ObjectNode)parsed;
        StrictJson.require("ck3_1210_full_state_v1".equals(StrictJson.text(state.get("schema"))),
                "clock request requires the original complete Full schema, never a Core prefix");
        var profile=org.xar.ck3.control.contracts.ExactCk3Build.florinCoreFullBuild(
                StrictJson.text(state.get("game_version")),StrictJson.text(state.get("executable_sha256")),
                StrictJson.text(state.get("adapter_id")))
                .orElseThrow(()->new IOException("original Full clock tuple has no exact qualified profile"));
        StrictJson.require(profile.coreFullBackend().equals(StrictJson.text(state.get("backend"))),
                "original Full clock backend differs from its selected profile");
        if(profile==org.xar.ck3.control.contracts.ExactCk3Build.CK3_121003_STEAM_26785313_FULL111
                &&"save-checkpoint".equals(step)) {
            var bridge=mapped112.orElseThrow(()->new IOException("current112 SDK SAVE requires its identical Managed mapped source binding"));
            return FullSnapshotClockControl.requestMappedSave112(bridge,snapshotId,revision,originalDeadline);
        }
        StrictJson.require(mapped112.isEmpty(),"mapped112 source cannot be borrowed by another clock request");
        return FullSnapshotClockControl.request(profile,step,snapshotId,revision,originalDeadline);
    }

    enum ObservationMode { SAVED_FULL,SAVED_CORE,MENU_CORE,CORE_CONTROL,CORE_EXIT,CORE_CHECKPOINT_SAVE,RITE_DOCTRINE,GUI_NAVIGATION_V2,PERSONAL_GOLD,ACTOR_FOUNDATION,FULL_CLOCK,DATE_ADVANCE,PERSONAL_CASH,GUI_ROOT_INDEX,GUI_WINDOW,RITE_DRAFT_COSTS,GUI_CONTROLS_V2,CURRENT_DATE_ADVANCE,RITE_FINAL_CONFIRMATION,CURRENT_FRONTEND_MENU,CURRENT_FRONTEND_MENU_QUIT,CURRENT_AUB_OBSERVER_FIXTURE,CURRENT_DJC_TARGET_QUERY,CURRENT_SUCCESSION_QUERY,CURRENT_SUCCESSION_CONTINUE,CURRENT_DJC_DECLARATION_UI,CURRENT_DJC_DECLARATION_SUBMIT,CURRENT_LETTER_QUERY,CURRENT_LETTER_REPLY_KNOWN,CURRENT_DJC_SELECTED_COST,CURRENT_DJC_SELECTED_COST_PREVIEW,CURRENT_LETTER_SET_QUERY,CURRENT_LETTER_SET_REPLY_KNOWN_INSTANCE,CURRENT_FULLSCREEN_EVENT_QUERY,CURRENT_FULLSCREEN_EVENT_ACK_KNOWN_INTRO,CURRENT_CURATED_DECISIONS_QUERY,CURRENT_CURATED_DECISIONS_OPEN,CURRENT_CURATED_DECISION_DETAIL,CURRENT_CURATED_DECISION_CONFIRM,CURRENT_XQOL_CONVERSION_PROMPT_QUERY,CURRENT_XQOL_CONVERSION_PROMPT_CONFIRM,CURRENT_XQOL_CONVERSION_PROMPT_CANCEL,CURRENT_XQOL_CONVERSION_THRESHOLD_QUERY,CURRENT_XQOL_CONVERSION_THRESHOLD_SET,CURRENT_COURTIER_CREATOR_CONTROLS_QUERY,CURRENT_COURTIER_CREATOR_CONTROL_EXECUTE,CURRENT_DECISIONS_CLOSE_QUERY,CURRENT_DECISIONS_CLOSE }
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
        if(schema.equals("xar.native-owner-snapshot-config/v32")) {
            return switch(currentDecisionsCloseAction(config)) {
                case QUERY_CLOSE->ObservationMode.CURRENT_DECISIONS_CLOSE_QUERY;
                case CLOSE_LIST->ObservationMode.CURRENT_DECISIONS_CLOSE;
            };
        }
        if(schema.equals("xar.native-owner-snapshot-config/v31")) {
            return switch(currentCourtierControlsConfig(config).action()) {
                case QUERY_CONTROL->ObservationMode.CURRENT_COURTIER_CREATOR_CONTROLS_QUERY;
                case EXECUTE_CONTROL->ObservationMode.CURRENT_COURTIER_CREATOR_CONTROL_EXECUTE;
            };
        }
        StrictJson.require(!config.has("product")&&!config.has("control"),"product/control belong only to the explicit v31 fixed creator modes");
        if(schema.equals("xar.native-owner-snapshot-config/v30")) {
            return switch(currentXqolThresholdConfig(config).action()) {
                case QUERY_THRESHOLD->ObservationMode.CURRENT_XQOL_CONVERSION_THRESHOLD_QUERY;
                case SET_THRESHOLD->ObservationMode.CURRENT_XQOL_CONVERSION_THRESHOLD_SET;
            };
        }
        StrictJson.require(!config.has("target_threshold"),"target_threshold belongs only to the explicit v30 threshold modes");
        if(schema.equals("xar.native-owner-snapshot-config/v29")) {
            return switch(currentXqolPromptAction(config)) {
                case QUERY_PROMPT->ObservationMode.CURRENT_XQOL_CONVERSION_PROMPT_QUERY;
                case CONFIRM_CONVERSION->ObservationMode.CURRENT_XQOL_CONVERSION_PROMPT_CONFIRM;
                case CANCEL_CONVERSION->ObservationMode.CURRENT_XQOL_CONVERSION_PROMPT_CANCEL;
            };
        }
        if(schema.equals("xar.native-owner-snapshot-config/v28")) {
            return switch(currentCuratedDecisionConfig(config).action()) {
                case QUERY->ObservationMode.CURRENT_CURATED_DECISIONS_QUERY;
                case OPEN_LIST->ObservationMode.CURRENT_CURATED_DECISIONS_OPEN;
                case OPEN_DETAIL->ObservationMode.CURRENT_CURATED_DECISION_DETAIL;
                case CONFIRM->ObservationMode.CURRENT_CURATED_DECISION_CONFIRM;
            };
        }
        StrictJson.require(!config.has("decision_key"),"decision_key belongs only to the two explicit v28 keyed modes");
        if(schema.equals("xar.native-owner-snapshot-config/v27")) {
            StrictJson.object(config,Set.of("schema","mode","owner_descriptor","overall_timeout_seconds","read_timeout_seconds","maximum_frames_per_operation"));
            String mode=StrictJson.text(config.get("mode"));
            if(mode.equals("current_fullscreen_event_query"))return ObservationMode.CURRENT_FULLSCREEN_EVENT_QUERY;
            if(mode.equals("current_fullscreen_event_ack_known_intro"))return ObservationMode.CURRENT_FULLSCREEN_EVENT_ACK_KNOWN_INTRO;
            throw new IllegalArgumentException("Only exact fullscreen event query or one private-source known intro acknowledgement; no configured event/instance/option/Core/lease");
        }
        if(schema.equals("xar.native-owner-snapshot-config/v26")) {
            String mode=StrictJson.text(config.get("mode"));
            var common=Set.of("schema","mode","owner_descriptor","overall_timeout_seconds","read_timeout_seconds","maximum_frames_per_operation");
            if(mode.equals("current_letter_set_query")) {
                StrictJson.object(config,common);return ObservationMode.CURRENT_LETTER_SET_QUERY;
            }
            StrictJson.require(mode.equals("current_letter_set_reply_known_instance"),"Only complete letter census or one explicit actual-instance fixed reply");
            var fields=new java.util.HashSet<>(common);fields.add("instance_id");StrictJson.object(config,Set.copyOf(fields));
            StrictJson.integer(config.get("instance_id"),1,Integer.MAX_VALUE);
            return ObservationMode.CURRENT_LETTER_SET_REPLY_KNOWN_INSTANCE;
        }
        if(schema.equals("xar.native-owner-snapshot-config/v25")) {
            String mode=StrictJson.text(config.get("mode"));boolean preview=mode.equals("current_djc_selected_cost_preview");
            var common=Set.of("schema","mode","owner_descriptor","overall_timeout_seconds","read_timeout_seconds","maximum_frames_per_operation","target_character_id","cb_key");
            if(preview) {var fields=new java.util.HashSet<>(common);fields.add("tuple_intent");StrictJson.object(config,Set.copyOf(fields));}
            else {StrictJson.object(config,common);StrictJson.require(mode.equals("current_djc_selected_cost"),"Only fixed readonly cost or explicit bounded Open/Select preview; no Send or caller prices");}
            currentDjcSelectedCostConfig(config,preview);return preview?ObservationMode.CURRENT_DJC_SELECTED_COST_PREVIEW:ObservationMode.CURRENT_DJC_SELECTED_COST;
        }
        if(schema.equals("xar.native-owner-snapshot-config/v24")) {
            StrictJson.object(config,Set.of("schema","mode","owner_descriptor","overall_timeout_seconds","read_timeout_seconds","maximum_frames_per_operation"));
            String mode=StrictJson.text(config.get("mode"));
            if(mode.equals("current_letter_query"))return ObservationMode.CURRENT_LETTER_QUERY;
            if(mode.equals("current_letter_reply_known"))return ObservationMode.CURRENT_LETTER_REPLY_KNOWN;
            throw new IllegalArgumentException("Only exact current letter readonly query or fixed reviewed reply; no configured instance/definition/option/Core");
        }
        if(schema.equals("xar.native-owner-snapshot-config/v23")) {
            String mode=StrictJson.text(config.get("mode"));
            if(mode.equals("current_djc_declaration_ui")) {
                StrictJson.object(config,Set.of("schema","mode","owner_descriptor","overall_timeout_seconds","read_timeout_seconds","maximum_frames_per_operation","target_character_id","cb_key"));
                currentDjcUiConfig(config,false);return ObservationMode.CURRENT_DJC_DECLARATION_UI;
            }
            if(mode.equals("current_djc_declaration_submit")) {
                StrictJson.object(config,Set.of("schema","mode","owner_descriptor","overall_timeout_seconds","read_timeout_seconds","maximum_frames_per_operation","target_character_id","cb_key","tuple_intent","maximum_warning_polls","warning_poll_interval_ms"));
                currentDjcUiConfig(config,true);return ObservationMode.CURRENT_DJC_DECLARATION_SUBMIT;
            }
            throw new IllegalArgumentException("Only exact current DJC UI query or bound tuple submission modes; no tokens/Core/ordinal/permissions");
        }
        StrictJson.require(!config.has("cb_key")&&!config.has("tuple_intent")&&!config.has("maximum_warning_polls")&&!config.has("warning_poll_interval_ms"),"Current DJC UI intent fields belong only to explicit v23");
        if(schema.equals("xar.native-owner-snapshot-config/v22")) {
            StrictJson.object(config,Set.of("schema","mode","owner_descriptor","overall_timeout_seconds","read_timeout_seconds","maximum_frames_per_operation"));
            String mode=StrictJson.text(config.get("mode"));
            if(mode.equals("current_succession_default"))return ObservationMode.CURRENT_SUCCESSION_QUERY;
            if(mode.equals("current_succession_default_continue"))return ObservationMode.CURRENT_SUCCESSION_CONTINUE;
            throw new IllegalArgumentException("Only fixed official default succession modes; no Core or configured predecessor/heir IDs");
        }
        if(schema.equals("xar.native-owner-snapshot-config/v21")) {
            StrictJson.object(config,Set.of("schema","mode","owner_descriptor","overall_timeout_seconds","read_timeout_seconds","maximum_frames_per_operation","target_character_id"));
            StrictJson.require("current_djc_target_war_query".equals(StrictJson.text(config.get("mode"))),"Explicit readonly current DJC target mode required");
            org.xar.ck3.control.contracts.NativeCharacterId.fromJson(config.get("target_character_id"));
            return ObservationMode.CURRENT_DJC_TARGET_QUERY;
        }
        StrictJson.require(!config.has("target_character_id"),"Configured DJC target belongs only to v21; no old-mode selector alias");
        if(schema.equals("xar.native-owner-snapshot-config/v20")) {
            StrictJson.object(config,Set.of("schema","mode","owner_descriptor","overall_timeout_seconds","read_timeout_seconds","maximum_frames_per_operation"));
            StrictJson.require("current_aub_observer_fixture".equals(StrictJson.text(config.get("mode"))),"Explicit fixed observer mode required; no caller command/body/path/hash/Core");
            return ObservationMode.CURRENT_AUB_OBSERVER_FIXTURE;
        }
        if(schema.equals("xar.native-owner-snapshot-config/v19")) {
            var fields=Set.of("schema","mode","owner_descriptor","overall_timeout_seconds","read_timeout_seconds","maximum_frames_per_operation");
            StrictJson.object(config,fields,Set.of());String mode=StrictJson.text(config.get("mode"));
            if(mode.equals("current_frontend_menu"))return ObservationMode.CURRENT_FRONTEND_MENU;
            if(mode.equals("current_frontend_menu_quit"))return ObservationMode.CURRENT_FRONTEND_MENU_QUIT;
            throw new IllegalArgumentException("Explicit fixed current no-world frontend mode required; no arbitrary action or caller Core");
        }
        if(schema.equals("xar.native-owner-snapshot-config/v18")) {
            StrictJson.require("current_rite_final_confirmation".equals(StrictJson.text(config.get("mode"))),"Explicit fixed current two-stage final confirmation mode required");
            var fields=Set.of("schema","mode","owner_descriptor","overall_timeout_seconds","read_timeout_seconds","maximum_frames_per_operation","expected_source_rite_id","maximum_confirmation_polls","status_poll_interval_ms");
            for(var property:config.properties())StrictJson.require(fields.contains(property.getKey()),"Final confirmation cannot borrow configured Core, action, selector, lease, deadline or SAVE fields");
            StrictJson.integer(config.get("expected_source_rite_id"),0,0xffff_fffeL);
            StrictJson.integer(config.get("maximum_confirmation_polls"),1,64);
            StrictJson.integer(config.get("status_poll_interval_ms"),100,5000);
            return ObservationMode.RITE_FINAL_CONFIRMATION;
        }
        StrictJson.require(!config.has("maximum_confirmation_polls"),"Final-confirmation polling belongs only to v18");
        if(schema.equals("xar.native-owner-snapshot-config/v17")) {
            StrictJson.require("current_date_advance".equals(StrictJson.text(config.get("mode"))),"Explicit current narrow one-day mode required");
            var fields=Set.of("schema","mode","owner_descriptor","overall_timeout_seconds","read_timeout_seconds","maximum_frames_per_operation","maximum_status_polls","status_poll_interval_ms");
            for(var property:config.properties())StrictJson.require(fields.contains(property.getKey()),"Current date cannot accept configured Core, target date, operation, deadline, SAVE or another mode");
            StrictJson.integer(config.get("maximum_status_polls"),1,128);
            StrictJson.integer(config.get("status_poll_interval_ms"),100,5000);
            return ObservationMode.CURRENT_DATE_ADVANCE;
        }
        if(schema.equals("xar.native-owner-snapshot-config/v16")) {
            StrictJson.require("current_rite_doctrine".equals(StrictJson.text(config.get("mode"))),"Explicit typed current Rite mode required");
            StrictJson.require(Set.of(RiteDoctrineFrameV1.Action.QUERY,RiteDoctrineFrameV1.Action.OPEN_DYNASTIC_CATEGORY,
                    RiteDoctrineFrameV1.Action.SELECT_DYNASTIC,RiteDoctrineFrameV1.Action.CONFIRM_EDIT)
                    .contains(RiteDoctrineFrameV1.Action.wire(StrictJson.text(config.get("rite_action")))),"Original v16 has only its four original actions; final confirmation requires v18");
            StrictJson.integer(config.get("expected_source_rite_id"),0,0xffff_fffeL);
            for(String field:List.of("core_prefix_only","control_step","maximum_status_polls","status_poll_interval_ms","window_name","navigation_action","expected_core","connection_generation","provider_generation","query_sequence","widget_id","checkpoint_archive_path","maximum_checkpoint_bytes","checkpoint_observation_attempts","checkpoint_poll_interval_ms","previous_checkpoint_source","previous_checkpoint_archive"))
                StrictJson.require(!config.has(field),"Rite mode cannot borrow another mode or configured Core/lease/selector");
            return ObservationMode.RITE_DOCTRINE;
        }
        StrictJson.require(!config.has("rite_action"),"Typed Rite action belongs only to explicit v16 mode");
        if(schema.equals("xar.native-owner-snapshot-config/v15")) {
            StrictJson.require("current_gui_navigation".equals(StrictJson.text(config.get("mode"))),"Explicit literal navigation mode required");
            NativeGameTransport.NavigationAction.valueOf(StrictJson.text(config.get("navigation_action")));
            for(String field:List.of("core_prefix_only","control_step","maximum_status_polls","status_poll_interval_ms","window_name","expected_source_rite_id","expected_core","connection_generation","query_generation","widget_id","checkpoint_archive_path","maximum_checkpoint_bytes","checkpoint_observation_attempts","checkpoint_poll_interval_ms","previous_checkpoint_source","previous_checkpoint_archive"))
                StrictJson.require(!config.has(field),"Literal navigation cannot borrow another mode or caller supplied Core/selector");
            return ObservationMode.GUI_NAVIGATION_V2;
        }
        StrictJson.require(!config.has("navigation_action"),"Literal action belongs only to explicit v15 mode");
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
            StrictJson.require(window==GuiControlsFrameV2.Window.FAITH||window==GuiControlsFrameV2.Window.RITE,"Layer navigation belongs only to explicit v15, never old readonly v13");
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
