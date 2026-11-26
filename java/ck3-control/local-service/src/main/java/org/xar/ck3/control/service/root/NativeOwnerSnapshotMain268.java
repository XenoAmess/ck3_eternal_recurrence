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
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.NativeObservationPort;
import org.xar.ck3.control.application.action.NativeRequestChronology;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
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
import org.xar.ck3.control.nativebridge.CurrentLivingInventoryQuery;
import org.xar.ck3.control.nativebridge.CurrentLivingInventoryQuerySource;
import org.xar.ck3.control.nativebridge.CurrentLivingInventoryQueryResult;
import org.xar.ck3.control.nativebridge.CurrentLivingEntry;
import org.xar.ck3.control.nativebridge.CurrentLivingEntrySource;
import org.xar.ck3.control.nativebridge.CurrentLivingEntryResult;
import org.xar.ck3.control.nativebridge.CurrentLivingUi;
import org.xar.ck3.control.nativebridge.CurrentLivingUiSource;
import org.xar.ck3.control.nativebridge.CurrentLivingUiResult;
import org.xar.ck3.control.nativebridge.CurrentZg361Ae2;
import org.xar.ck3.control.nativebridge.CurrentZg361Ae2Source;
import org.xar.ck3.control.nativebridge.CurrentZg361Ae2Result;
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
import org.xar.ck3.control.nativebridge.CurrentCccActorTransition;
import org.xar.ck3.control.nativebridge.CurrentCccActorTransitionSource;
import org.xar.ck3.control.nativebridge.CurrentCccActorTransitionResult;
import org.xar.ck3.control.nativebridge.CurrentCccEvent;
import org.xar.ck3.control.nativebridge.CurrentCccEventSource;
import org.xar.ck3.control.nativebridge.CurrentCccEventResult;
import org.xar.ck3.control.nativebridge.CurrentCccDecision;
import org.xar.ck3.control.nativebridge.CurrentCccDecisionSource;
import org.xar.ck3.control.nativebridge.CurrentCccDecisionResult;
import org.xar.ck3.control.nativebridge.CurrentStockBookmark1070;
import org.xar.ck3.control.nativebridge.CurrentStockBookmark1070Source;
import org.xar.ck3.control.nativebridge.CurrentStockBookmark1070Result;
import org.xar.ck3.control.nativebridge.CurrentRmtmActorTransition;
import org.xar.ck3.control.nativebridge.CurrentRmtmActorTransitionSource;
import org.xar.ck3.control.nativebridge.CurrentRmtmActorTransitionResult;
import org.xar.ck3.control.nativebridge.CurrentRmtmDecision;
import org.xar.ck3.control.nativebridge.CurrentRmtmDecisionSource;
import org.xar.ck3.control.nativebridge.CurrentRmtmDecisionResult;
import org.xar.ck3.control.nativebridge.CurrentRmtmEvent;
import org.xar.ck3.control.nativebridge.CurrentRmtmEventSource;
import org.xar.ck3.control.nativebridge.CurrentRmtmEventResult;
import org.xar.ck3.control.nativebridge.CurrentRmtmObservation;
import org.xar.ck3.control.nativebridge.CurrentRmtmObservationSource;
import org.xar.ck3.control.nativebridge.CurrentRmtmObservationResult;
import org.xar.ck3.control.nativebridge.CurrentRmtmTitleQuerySource;
import org.xar.ck3.control.nativebridge.CurrentRmtmTitleQueryResult;
import org.xar.ck3.control.nativebridge.CurrentRiteCreationBlockersSource;
import org.xar.ck3.control.nativebridge.CurrentRiteCreationBlockersResult;
import org.xar.ck3.control.nativebridge.CurrentRiteText;
import org.xar.ck3.control.nativebridge.CurrentRiteTextSource;
import org.xar.ck3.control.nativebridge.CurrentRiteTextResult;
import org.xar.ck3.control.nativebridge.CurrentRiteCreate;
import org.xar.ck3.control.nativebridge.CurrentRiteCreateSource;
import org.xar.ck3.control.nativebridge.CurrentRiteCreateResult;
import org.xar.ck3.control.nativebridge.CurrentDesInitGuard;
import org.xar.ck3.control.nativebridge.CurrentDesInitGuardSource;
import org.xar.ck3.control.nativebridge.CurrentDesInitGuardResult;
import org.xar.ck3.control.nativebridge.CurrentTedActorTransition;
import org.xar.ck3.control.nativebridge.CurrentTedActorTransitionSource;
import org.xar.ck3.control.nativebridge.CurrentTedActorTransitionResult;
import org.xar.ck3.control.nativebridge.CurrentLyd;
import org.xar.ck3.control.nativebridge.CurrentLydResult;
import org.xar.ck3.control.nativebridge.CurrentSupermanHealth;
import org.xar.ck3.control.nativebridge.CurrentSupermanHealthSource;
import org.xar.ck3.control.nativebridge.CurrentSupermanHealthResult;
import org.xar.ck3.control.nativebridge.CurrentCourtierChoices;
import org.xar.ck3.control.nativebridge.CurrentCourtierChoicesSource;
import org.xar.ck3.control.nativebridge.CurrentCourtierChoicesResult;
import org.xar.ck3.control.nativebridge.CurrentCourtierConfiguration;
import org.xar.ck3.control.nativebridge.CurrentCourtierConfigurationSource;
import org.xar.ck3.control.nativebridge.CurrentCourtierConfigurationResult;
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
                "overall_timeout_seconds", "read_timeout_seconds", "maximum_frames_per_operation"), Set.of("core_prefix_only", "mode", "control_step", "maximum_status_polls", "status_poll_interval_ms", "window_name", "expected_source_rite_id", "checkpoint_archive_path", "maximum_checkpoint_bytes", "checkpoint_observation_attempts", "checkpoint_poll_interval_ms", "previous_checkpoint_source", "previous_checkpoint_archive", "navigation_action", "rite_action", "maximum_confirmation_polls", "target_character_id", "cb_key", "tuple_intent", "maximum_warning_polls", "warning_poll_interval_ms", "instance_id", "decision_key", "target_threshold", "product", "control", "setting", "catalog", "choice_key", "phase", "baseline_progress", "personal_key", "event_role", "status_poll_delay_ms", "maximum_core_polls", "core_poll_interval_ms", "confirmation_poll_interval_ms", "text"));
        ObservationMode observationMode=observationMode(config);
        boolean currentZg361Scoreboard=observationMode==ObservationMode.CURRENT_ZG361_SCOREBOARD;
        Zg361ScoreboardConfig zg361ScoreboardConfig=currentZg361Scoreboard?currentZg361ScoreboardConfig(config):null;
        boolean currentZg361Combined=observationMode==ObservationMode.CURRENT_ZG361_REVIEW_AE2;
        Zg361CombinedConfig zg361CombinedConfig=currentZg361Combined?currentZg361CombinedConfig(config):null;
        boolean currentZg361Review=observationMode==ObservationMode.CURRENT_ZG361_REVIEW;
        Zg361ReviewConfig zg361ReviewConfig=currentZg361Review?currentZg361ReviewConfig(config):null;
        boolean currentZg361Ae2=observationMode==ObservationMode.CURRENT_ZG361_AE2;
        Zg361Ae2Config zg361Ae2Config=currentZg361Ae2?currentZg361Ae2Config(config):null;
        boolean currentLivingOriginal=observationMode==ObservationMode.CURRENT_LIVING_ORIGINAL;
        LivingOriginalConfig livingConfig=currentLivingOriginal?currentLivingOriginalConfig(config):null;
        boolean currentRmtmRemaining=observationMode==ObservationMode.CURRENT_RMTM_REMAINING;
        RmtmConfig rmtmConfig=currentRmtmRemaining?currentRmtmConfig(config):null;
        boolean currentRmtmTitleQuery=observationMode==ObservationMode.CURRENT_RMTM_TITLE_QUERY;
        boolean currentCcc=observationMode==ObservationMode.CURRENT_CCC;
        CccConfig cccConfig=currentCcc?currentCccConfig(config):null;
        boolean currentStockBookmark1070=observationMode==ObservationMode.CURRENT_STOCK_BOOKMARK1070;
        StockBookmark1070Config stockBookmark1070Config=currentStockBookmark1070?currentStockBookmark1070Config(config):null;
        boolean currentRiteCreationBlockers=observationMode==ObservationMode.CURRENT_RITE_CREATION_BLOCKERS;
        RiteCreationBlockersConfig riteCreationBlockersConfig=currentRiteCreationBlockers?currentRiteCreationBlockersConfig(config):null;
        boolean currentRiteText=observationMode==ObservationMode.CURRENT_RITE_TEXT;
        RiteTextConfig riteTextConfig=currentRiteText?currentRiteTextConfig(config):null;
        boolean currentRiteCreate=observationMode==ObservationMode.CURRENT_RITE_CREATE;
        RiteCreateConfig riteCreateConfig=currentRiteCreate?currentRiteCreateConfig(config):null;
        boolean currentDesInitGuard=observationMode==ObservationMode.CURRENT_DES_SAVED_GAME_INIT_GUARD;
        boolean currentStockSeed=observationMode==ObservationMode.CURRENT_STOCK_NEWGAME_SEED;
        StockSeedConfig stockSeedConfig=currentStockSeed?currentStockSeedConfig(config):null;
        boolean currentTed=observationMode==ObservationMode.CURRENT_TED;
        TedConfig tedConfig=currentTed?currentTedConfig(config):null;
        boolean currentLyd=observationMode==ObservationMode.CURRENT_LYD;
        LydConfig lydConfig=currentLyd?currentLydConfig(config):null;
        boolean currentSupermanSavedBaseline=observationMode==ObservationMode.CURRENT_SUPERMAN_HEALTH_RESUME_SAVED_BASELINE_AND_BEGIN;
        ExactRef savedBaselineProgress=currentSupermanSavedBaseline?currentSupermanSavedBaselineConfig(config):null;
        boolean currentSupermanHealth=observationMode==ObservationMode.CURRENT_SUPERMAN_HEALTH_QUERY||observationMode==ObservationMode.CURRENT_SUPERMAN_HEALTH_BASELINE_SAVE_AND_BEGIN||observationMode==ObservationMode.CURRENT_SUPERMAN_HEALTH_COMPLETED_CLOSE;
        SupermanHealthConfig healthConfig=currentSupermanHealth?currentSupermanHealthConfig(config):null;
        boolean currentCourtierChoices=observationMode==ObservationMode.CURRENT_COURTIER_CHOICES_QUERY||observationMode==ObservationMode.CURRENT_COURTIER_CHOICE_SELECT;
        CourtierChoicesConfig choicesConfig=currentCourtierChoices?currentCourtierChoicesConfig(config):null;
        boolean currentCourtierConfiguration=observationMode==ObservationMode.CURRENT_COURTIER_CONFIGURATION_QUERY||observationMode==ObservationMode.CURRENT_COURTIER_CONFIGURATION_EXECUTE;
        CourtierConfigurationConfig configurationConfig=currentCourtierConfiguration?currentCourtierConfigurationConfig(config):null;
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
        boolean dateStatus=observationMode==ObservationMode.HELD_DATE_SENTINEL_STATUS;
        boolean currentDateAdvance=observationMode==ObservationMode.CURRENT_DATE_ADVANCE;
        int maximumStatusPolls=(dateAdvance||currentDateAdvance)?Math.toIntExact(StrictJson.integer(config.get("maximum_status_polls"),1,128)):0;
        long statusPollMillis=(dateAdvance||currentDateAdvance)?StrictJson.integer(config.get("status_poll_interval_ms"),100,5000):0;
        String fullClockStep=fullClock?StrictJson.text(config.get("control_step")):null;
        CoreClockControl.Step controlStep=observationMode==ObservationMode.CORE_CONTROL
                ?CoreClockControl.Step.fromWire(StrictJson.text(config.get("control_step"))):null;
        boolean coreCommand=applicationExit||controlStep!=null;
        ExactRef expectedDescriptor = ExactRef.fromJson(config.get("owner_descriptor"));
        StrictJson.require(Path.of(expectedDescriptor.path()).toAbsolutePath().normalize().equals(descriptorPath), "descriptor path differs from explicit config");
        long overall = StrictJson.integer(config.get("overall_timeout_seconds"), 1, currentZg361OverallTimeoutLimit(observationMode));
        long readSeconds = StrictJson.integer(config.get("read_timeout_seconds"), 1, 60);
        int frames = Math.toIntExact(StrictJson.integer(config.get("maximum_frames_per_operation"), 1, 65536));
        boolean currentArmyIdentity=observationMode==ObservationMode.CURRENT_ARMY_IDENTITY_READONLY;
        boolean corePrefixOnly=observationMode!=ObservationMode.SAVED_FULL&&!currentArmyIdentity;
        Instant entered = Instant.now(), deadline = entered.plusSeconds(overall);
        byte[] descriptorBytes = readExact(expectedDescriptor, GameSupervisorControl.MAXIMUM_DESCRIPTOR_BYTES);
        SharedSourceFiles.Witness descriptorWitness = SharedSourceFiles.observe(descriptorPath);
        requireWitnessBytes(descriptorWitness, expectedDescriptor);
        GameSupervisorControl.Descriptor owner = GameSupervisorControl.readDescriptor(descriptorPath);
        if (!descriptorWitness.equals(SharedSourceFiles.observe(descriptorPath))) throw new IOException("descriptor identity changed during parsing");
        if (!Arrays.equals(descriptorBytes, readExact(expectedDescriptor, GameSupervisorControl.MAXIMUM_DESCRIPTOR_BYTES)))
            throw new IOException("descriptor differs from the exact parsed source");
        var plan = owner.configuration().accept();
        if(currentStockSeed) {
            requireCurrentStockSeedDeclaration(plan.load(),plan.preparedProfile());
        } else if(currentFrontendMenu) {
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
        if(currentArmyIdentity)result.put("schema","xar.native-owner-army-identity-readonly/v1")
                .put("mode","current_army_identity_readonly");
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
        if(currentCcc)initializeCurrentCccResult(result,cccConfig,owner.machineId());
        if(currentStockBookmark1070)initializeCurrentStockBookmark1070Result(result,stockBookmark1070Config,owner.machineId());
        if(currentLivingOriginal)initializeCurrentLivingOriginalResult(result,owner.machineId());
        if(currentRmtmRemaining)initializeCurrentRmtmResult(result,rmtmConfig,owner.machineId());
        if(currentRmtmTitleQuery)initializeCurrentRmtmTitleQueryResult(result,owner.machineId());
        if(currentRiteCreationBlockers)initializeCurrentRiteCreationBlockersResult(result,riteCreationBlockersConfig,owner.machineId());
        if(currentRiteText)initializeCurrentRiteTextResult(result,riteTextConfig,owner.machineId(),StrictJson.text(config.get("mode")));
        if(currentRiteCreate)initializeCurrentRiteCreateResult(result,riteCreateConfig,owner.machineId());
        if(currentDesInitGuard)initializeCurrentDesInitGuardResult(result,owner.machineId());
        if(currentTed)result.put("schema","xar.native-owner-current-ted-transition/v1").put("mode",StrictJson.text(config.get("mode")))
                .put("read_calls",0).put("advance_calls",0).put("status_queries",0).put("epoch_confirm_calls",0).put("query_available",false)
                .put("epoch_confirmed",false).put("two_days_observed",false).put("independent_after_core_verified",false).put("physical_save_confirmed",false).put("save_calls",0);
        if(currentLyd)initializeCurrentLydResult(result,lydConfig,owner.machineId());
        if(currentSupermanSavedBaseline)initializeSupermanSavedBaselineResult(result,config,owner.machineId());
        if(currentSupermanHealth)result.put("schema","xar.native-owner-current-superman-health/v1").put("mode",StrictJson.text(config.get("mode")))
                .put("machine_id",owner.machineId()).put("steam_build_id","26785313").put("phase",healthConfig.phase().wire())
                .put("read_calls",0).put("choose_calls",0).put("save_calls",0).put("query_available",false).put("known_choice_dispatched",false)
                .put("baseline_physical_material_observed",false).put("native_returned",false).put("native_handled",false).put("event_closed",false)
                .put("health_changed",false).put("trait_UI_rendered",false).put("new_date_observed",false).put("physical_save_confirmed",false);
        if(currentCourtierChoices)result.put("schema","xar.native-owner-current-courtier-choices/v1").put("mode",StrictJson.text(config.get("mode")))
                .put("machine_id",owner.machineId()).put("steam_build_id","26785313").put("action",choicesConfig.action().wire())
                .put("product",choicesConfig.product().wire()).put("catalog",choicesConfig.catalog().wire())
                .put("read_calls",0).put("select_calls",0).put("query_available",false).put("select_callback_dispatched",false)
                .put("native_returned",false).put("native_handled",false).put("selection_changed",false).put("creator_closed",false).put("courtier_created",false)
                .put("new_date_observed",false).put("physical_save_confirmed",false).put("save_calls",0);
        if(currentCourtierConfiguration)result.put("schema","xar.native-owner-current-courtier-configuration/v1").put("mode",StrictJson.text(config.get("mode")))
                .put("machine_id",owner.machineId()).put("steam_build_id","26785313").put("action",configurationConfig.action().wire())
                .put("product",configurationConfig.product().wire()).put("setting",configurationConfig.setting().wire())
                .put("read_calls",0).put("execute_calls",0).put("query_available",false).put("setting_callback_dispatched",false)
                .put("native_returned",false).put("native_handled",false).put("configuration_applied",false).put("creator_closed",false).put("courtier_created",false)
                .put("age_changed",false).put("new_date_observed",false).put("physical_save_confirmed",false).put("save_calls",0);
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
        if(currentZg361Scoreboard)initializeCurrentZg361ScoreboardResult(result,owner.machineId());
        if(currentZg361Combined)initializeCurrentZg361CombinedResult(result,owner.machineId());
        if(currentZg361Review)initializeCurrentZg361ReviewResult(result,owner.machineId());
        if(currentZg361Ae2)initializeCurrentZg361Ae2Result(result,owner.machineId());
        stage = "ATTACH";
        try (var supervisor = WindowsJobProcess.retainReadOnlyProcess(owner.supervisorIdentity().pid())) {
            requireSupervisor(supervisor, owner.supervisorIdentity());
            var request = new NativeGameAttachment.Request(plan, owner.generation(), List.of(), frames,currentZg361Scoreboard?zg361ScoreboardConfig.submissions():currentZg361Combined?zg361CombinedConfig.submissions():currentZg361Review?zg361ReviewConfig.submissions():currentZg361Ae2?zg361Ae2Config.submissions():currentLivingOriginal?livingConfig.submissions():currentRmtmRemaining?rmtmConfig.submissions():currentRmtmTitleQuery?2:currentCcc?cccConfig.submissions():currentStockBookmark1070?stockBookmark1070Config.submissions():currentRiteCreationBlockers?2:currentRiteText?riteTextConfig.submissions():currentRiteCreate?riteCreateConfig.submissions():currentDesInitGuard?2:currentStockSeed?stockSeedConfig.submissions():currentTed?tedConfig.submissions():currentLyd?lydConfig.mode().submissions():currentSupermanSavedBaseline?3:currentSupermanHealth?(healthConfig.mode()==SupermanHealthMode.QUERY?2:healthConfig.mode()==SupermanHealthMode.BASELINE_SAVE_AND_BEGIN?5:3):currentCourtierChoices?(choicesConfig.action()==CurrentCourtierChoices.Action.QUERY_CHOICES?2:3):currentCourtierConfiguration?(configurationConfig.action()==CurrentCourtierConfiguration.Action.QUERY_CONFIGURATION?2:3):currentDecisionsClose?(decisionsCloseAction==CurrentDecisionsClose.Action.QUERY_CLOSE?2:3):currentCourtierControls?(courtierConfig.action()==CurrentCourtierControls.Action.QUERY_CONTROL?2:3):currentXqolThreshold?(thresholdConfig.action()==CurrentXqolThreshold.Action.QUERY_THRESHOLD?2:3):currentXqolPrompt?(xqolPromptAction==CurrentXqolPrompt.Action.QUERY_PROMPT?2:3):currentCuratedDecision?(curatedConfig.action()==CurrentCuratedDecisions.Action.QUERY?2:3):currentFullscreenEvent?(acknowledgeKnownIntro?3:2):currentLetterSet?(letterSetReply?3:2):djcSelectedCost?(djcCostPreview?9:3):currentLetter?(knownLetterReply?3:2):djcUiMode?(djcUiSubmit?declarationConfig.maximumWarningPolls()+12:2):currentSuccession?(continueSuccession?2:1):currentFrontendMenu?(currentFrontendQuit?2:1):riteFinalConfirmation?maximumConfirmationPolls+5:currentDateAdvance?maximumStatusPolls+3:riteDoctrine?4:guiNavigation?3:guiControls?(controlWindow==GuiControlsFrameV2.Window.RITE?3:2):dateAdvance?maximumStatusPolls+6:dateStatus||checkpointSave||aubObserver||djcQuery||coreCommand||fullClock||personalCash||guiRootIndex||guiWindow||riteDraftCosts?2:1);
            // This factory returns ATTACHED only. Its close releases communication and readonly handles, never a Job.
            try (ManagedGameSession game = NativeGameAttachment.attach(request, (currentZg361Scoreboard||currentZg361Combined||currentZg361Review||currentZg361Ae2||currentLivingOriginal||currentRmtmRemaining||currentRmtmTitleQuery||currentCcc||currentStockBookmark1070||currentRiteCreationBlockers||currentRiteText||currentRiteCreate||currentDesInitGuard||currentStockSeed||currentTed||currentLyd||currentSupermanSavedBaseline||currentSupermanHealth||currentCourtierChoices||currentCourtierConfiguration||currentDecisionsClose||currentCourtierControls||currentXqolThreshold||currentXqolPrompt||currentCuratedDecision||currentFullscreenEvent||currentLetterSet||djcSelectedCost||currentLetter||djcUiMode||currentFrontendMenu||currentSuccession||aubObserver||djcQuery||riteFinalConfirmation||currentDateAdvance||checkpointSave||guiNavigation||riteDoctrine)&&plan.deadline().isBefore(deadline)?plan.deadline():deadline, Duration.ofSeconds(readSeconds))) {
                if (game.mode() != ManagedGameSession.Mode.ATTACHED) throw new IOException("actual attachment mode differs");
                requireSupervisor(supervisor, owner.supervisorIdentity());
                var transport = game.nativeTransport(nativeSourceMode(observationMode));
                var hello = transport.diagnostics().originalHello().orElseThrow(() -> new IOException("actual received HELLO unavailable"));
                originals.set("new_hello", write(output, "new-hello.bin", hello.original().packet().value()));
                result.put("hello_observed_at_utc", hello.observedAt().toString());
                if(currentZg361Scoreboard) {
                    runCurrentZg361Scoreboard(transport,owner,plan,output,plan.deadline().isBefore(deadline)?plan.deadline():deadline,result,originals);
                } else if(currentZg361Combined) {
                    runCurrentZg361Combined(transport,owner,plan,output,plan.deadline().isBefore(deadline)?plan.deadline():deadline,result,originals);
                } else if(currentZg361Review) {
                    runCurrentZg361Review(transport,owner,plan,output,plan.deadline().isBefore(deadline)?plan.deadline():deadline,result,originals);
                } else if(currentZg361Ae2) {
                    runCurrentZg361Ae2(transport,owner,plan,output,plan.deadline().isBefore(deadline)?plan.deadline():deadline,result,originals);
                } else if(currentLivingOriginal) {
                    runCurrentLivingOriginal(transport,owner,plan,output,plan.deadline().isBefore(deadline)?plan.deadline():deadline,result,originals);
                } else if(currentRmtmRemaining) {
                    runCurrentRmtm(transport,owner,plan,rmtmConfig,output,plan.deadline().isBefore(deadline)?plan.deadline():deadline,Duration.ofSeconds(readSeconds),result,originals);
                } else if(currentRmtmTitleQuery) {
                    runCurrentRmtmTitleQuery(transport,owner,plan,output,plan.deadline().isBefore(deadline)?plan.deadline():deadline,result,originals);
                } else if(currentCcc) {
                    runCurrentCcc(transport,owner,plan,cccConfig,output,plan.deadline().isBefore(deadline)?plan.deadline():deadline,Duration.ofSeconds(readSeconds),result,originals);
                } else if(currentStockBookmark1070) {
                    runCurrentStockBookmark1070(transport,owner,plan,stockBookmark1070Config,output,plan.deadline().isBefore(deadline)?plan.deadline():deadline,result,originals);
                } else if(currentRiteCreationBlockers) {
                    runCurrentRiteCreationBlockers(transport,owner,plan,riteCreationBlockersConfig,output,plan.deadline().isBefore(deadline)?plan.deadline():deadline,result,originals);
                } else if(currentRiteText) {
                    runCurrentRiteText(transport,owner,plan,riteTextConfig,output,plan.deadline().isBefore(deadline)?plan.deadline():deadline,result,originals);
                } else if(currentRiteCreate) {
                    runCurrentRiteCreate(transport,owner,plan,riteCreateConfig,output,plan.deadline().isBefore(deadline)?plan.deadline():deadline,Duration.ofSeconds(readSeconds),result,originals);
                } else if(currentDesInitGuard) {
                    runCurrentDesInitGuard(transport,owner,plan,output,plan.deadline().isBefore(deadline)?plan.deadline():deadline,result,originals);
                } else if(currentStockSeed) {
                    runCurrentStockSeed(transport,owner,plan,stockSeedConfig,output,plan.deadline().isBefore(deadline)?plan.deadline():deadline,Duration.ofSeconds(readSeconds),result,originals);
                } else if(currentTed) {
                    runCurrentTed(transport,owner,plan,tedConfig,output,plan.deadline().isBefore(deadline)?plan.deadline():deadline,Duration.ofSeconds(readSeconds),result,originals);
                } else if(currentLyd) {
                    runCurrentLyd(transport,owner,plan,lydConfig,output,plan.deadline().isBefore(deadline)?plan.deadline():deadline,result,originals);
                } else if(currentSupermanSavedBaseline) {
                    runCurrentSupermanSavedBaseline(transport,owner,plan,config,savedBaselineProgress,output,plan.deadline().isBefore(deadline)?plan.deadline():deadline,result,originals);
                } else if(currentSupermanHealth) {
                    runCurrentSupermanHealth(transport,owner,plan,config,healthConfig,output,plan.deadline().isBefore(deadline)?plan.deadline():deadline,result,originals);
                } else if(currentCourtierChoices) {
                    runCurrentCourtierChoices(transport,owner,plan,choicesConfig,output,plan.deadline().isBefore(deadline)?plan.deadline():deadline,result,originals);
                } else if(currentCourtierConfiguration) {
                    runCurrentCourtierConfiguration(transport,owner,plan,configurationConfig,output,plan.deadline().isBefore(deadline)?plan.deadline():deadline,result,originals);
                } else if(currentDecisionsClose) {
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
                    if(!dateStatus||!(coreRead instanceof NativeGameTransport.CoreReceived))
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
                    if(dateStatus) {
                        try { readHeldDateStatus(transport,received,output,deadline,result,originals); }
                        finally { archiveNaturalDiagnostics(output,originals,transport.diagnostics()); }
                    }
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
                NativeActionPort.AckReceived acknowledgement;
                NativeObservationPort.ObservedFrame frame;
                NativeRequestChronology.Event snapshotReceived;
                NativeGameTransport.ArmyIdentityReceived identityRead = null;
                if (currentArmyIdentity) {
                    var read = transport.readFreshArmyIdentity126(deadline);
                    archiveNaturalDiagnostics(output,originals,transport.diagnostics());
                    if (read instanceof NativeGameTransport.ArmyIdentityUnavailable unavailable)
                        throw archiveUnavailableFreshRead(output, originals, unavailable.original(), unavailable.reason());
                    identityRead = (NativeGameTransport.ArmyIdentityReceived) read;
                    acknowledgement = identityRead.acknowledgement();
                    frame = identityRead.frame();
                    snapshotReceived = identityRead.snapshotReceived();
                } else {
                    var read = transport.readFreshFullState(deadline);
                    archiveNaturalDiagnostics(output,originals,transport.diagnostics());
                    if (read instanceof NativeFreshSnapshotPort.Unavailable unavailable)
                        throw archiveUnavailableFreshRead(output, originals, unavailable, unavailable.reason());
                    var received = (NativeFreshSnapshotPort.Received) read;
                    acknowledgement = received.acknowledgement();
                    frame = received.originalFrame();
                    snapshotReceived = received.snapshotReceived();
                }
                originals.set("dispatch", saveDispatch(output, acknowledgement));
                NativeFreshSnapshotPort.verifyOriginal(acknowledgement, frame, snapshotReceived);
                if (!frame.session().game().equals(owner.generation()) || !frame.session().machineId().equals(owner.machineId())
                        || !frame.session().sessionId().equals(owner.sessionId())
                        || !transport.diagnostics().session().filter(frame.session()::equals).isPresent()
                        || hello.original().pid() != owner.generation().pid()
                        || !hello.original().connectionGeneration().equals(frame.session().connectionGeneration()))
                    throw new IOException("actual READ/HELLO crossed expected owner Game/session/connection");
                stage = "PRESERVE_READ";
                originals.set("frame", saveFrame(output, frame));
                if (identityRead != null) {
                    result.set("identity_source", identityRead.source().toJson());
                    originals.set("player_armies", write(output, "player-army-identities.json",
                            OpportunityJson.encode(identityRead.semantic().get("player_armies"))));
                }
                result.set("session", session(frame.session()));
                result.put("request_id", acknowledgement.requestId()).put("snapshot_id", frame.snapshotId())
                        .put("native_revision", frame.nativeRevision().toString()).put("observed_at_utc", frame.observedAt().toString());
                result.set("snapshot_received", event(snapshotReceived));
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
        String archivedStatus = currentRmtmRemaining?"ARCHIVED_CURRENT_RMTM_DATA_ENDPOINT_RELEASED":currentRmtmTitleQuery?"ARCHIVED_CURRENT_RMTM_TITLE_READONLY_DATA_ENDPOINT_RELEASED":currentStockBookmark1070?"ARCHIVED_CURRENT_STOCK_BOOKMARK1070_DATA_ENDPOINT_RELEASED":currentRiteCreationBlockers?"ARCHIVED_CURRENT_RITE_CREATION_BLOCKERS_DATA_ENDPOINT_RELEASED":currentRiteText?"ARCHIVED_CURRENT_RITE_TEXT_DATA_ENDPOINT_RELEASED":currentRiteCreate?"ARCHIVED_CURRENT_RITE_CREATE_DATA_ENDPOINT_RELEASED":currentDesInitGuard?"ARCHIVED_CURRENT_DES_INIT_GUARD_DATA_ENDPOINT_RELEASED":currentStockSeed?"ARCHIVED_CURRENT_STOCK_NEWGAME_SEED_MATERIAL_ENDPOINT_RELEASED":currentTed?"ARCHIVED_CURRENT_TED_DATA_ENDPOINT_RELEASED":currentLyd?"ARCHIVED_CURRENT_LYD_DATA_ENDPOINT_RELEASED":currentSupermanSavedBaseline?"ARCHIVED_CURRENT_SUPERMAN_SAVED_BASELINE_DATA_ENDPOINT_RELEASED":currentSupermanHealth?"ARCHIVED_CURRENT_SUPERMAN_HEALTH_DATA_ENDPOINT_RELEASED":currentCourtierChoices?"ARCHIVED_CURRENT_COURTIER_CHOICES_DATA_ENDPOINT_RELEASED":currentCourtierConfiguration?"ARCHIVED_CURRENT_COURTIER_CONFIGURATION_DATA_ENDPOINT_RELEASED":currentDecisionsClose?"ARCHIVED_CURRENT_DECISIONS_CLOSE_DATA_ENDPOINT_RELEASED":currentCourtierControls?"ARCHIVED_CURRENT_COURTIER_CONTROLS_DATA_ENDPOINT_RELEASED":currentXqolThreshold?"ARCHIVED_CURRENT_XQOL_THRESHOLD_DATA_ENDPOINT_RELEASED":currentXqolPrompt?"ARCHIVED_CURRENT_XQOL_PROMPT_DATA_ENDPOINT_RELEASED":currentCuratedDecision?"ARCHIVED_CURRENT_CURATED_DECISIONS_DATA_ENDPOINT_RELEASED":currentFullscreenEvent?"ARCHIVED_CURRENT_FULLSCREEN_EVENT_DATA_ENDPOINT_RELEASED":currentLetterSet?"ARCHIVED_CURRENT_LETTER_SET_DATA_ENDPOINT_RELEASED":djcSelectedCost?"ARCHIVED_CURRENT_DJC_SELECTED_COST_DATA_ENDPOINT_RELEASED":currentLetter?"ARCHIVED_CURRENT_LETTER_DATA_ENDPOINT_RELEASED":djcUiMode?"ARCHIVED_CURRENT_DJC_DECLARATION_UI_DATA_ENDPOINT_RELEASED":riteFinalConfirmation?"ARCHIVED_CURRENT_RITE_FINAL_CALLBACK_DATA_ENDPOINT_RELEASED":currentDateAdvance?"ARCHIVED_CURRENT_NATIVE_ONE_DAY_ENDPOINT_RELEASED":riteDoctrine?"ARCHIVED_CURRENT_RITE_ACTION_DATA_ENDPOINT_RELEASED":guiNavigation?"ARCHIVED_LITERAL_NAVIGATION_SUBMISSION_ENDPOINT_RELEASED":checkpointSave?"ARCHIVED_CURRENT_CORE_CHECKPOINT_MATERIAL_ENDPOINT_RELEASED":guiControls?"ARCHIVED_NATIVE_GUI_CONTROLS_DATA_ENDPOINT_RELEASED":riteDraftCosts?"ARCHIVED_NATIVE_RITE_DRAFT_COSTS_DATA_ENDPOINT_RELEASED":guiWindow?"ARCHIVED_NATIVE_GUI_WINDOW_DATA_ENDPOINT_RELEASED":guiRootIndex?"ARCHIVED_NATIVE_GUI_ROOT_INDEX_DATA_ENDPOINT_RELEASED":dateAdvance?"ARCHIVED_NATIVE_DATE_SENTINEL_ADVANCE_ENDPOINT_RELEASED":personalCash?"ARCHIVED_NATIVE_PERSONAL_CASH_DATA_ENDPOINT_RELEASED":fullClock?"ARCHIVED_NATIVE_FULL_CLOCK_SUBMISSION_ENDPOINT_RELEASED":actorFoundation?"ARCHIVED_NATIVE_ACTOR_FOUNDATION_DATA_ENDPOINT_RELEASED":personalGold?"ARCHIVED_NATIVE_PERSONAL_GOLD_DATA_ENDPOINT_RELEASED":applicationExit?"ARCHIVED_NATIVE_APPLICATION_EXIT_REQUEST_ENDPOINT_RELEASED":controlStep!=null?"ARCHIVED_NATIVE_CORE_CONTROL_SUBMISSION_ENDPOINT_RELEASED":corePrefixOnly ? "ARCHIVED_NATIVE_CORE_PREFIX_DATA_ENDPOINT_RELEASED" : "ARCHIVED_NATIVE_READ_DATA_ENDPOINT_RELEASED";
        if(currentArmyIdentity)archivedStatus="ARCHIVED_CURRENT_ARMY_IDENTITY_READONLY_ENDPOINT_RELEASED";
        if(dateStatus)archivedStatus="ARCHIVED_HELD_DATE_SENTINEL_STATUS_ENDPOINT_RELEASED";
        result.put("status", archivedStatus).put("completed_at_utc", Instant.now().toString());
        ObjectNode published = write(output, "summary.json", FullJsonTree.encode(result, FullJsonTree.MAXIMUM_BYTES));
        System.out.println(StrictJson.object().put("schema", "xar.native-owner-snapshot-stage/v1")
                .put("status", archivedStatus).put("at_utc", Instant.now().toString()).set("summary", published));
    }

    static ExactRef currentSupermanSavedBaselineConfig(ObjectNode config) {
        StrictJson.object(config,Set.of("schema","mode","owner_descriptor","overall_timeout_seconds","read_timeout_seconds","maximum_frames_per_operation","baseline_progress"));
        StrictJson.require(StrictJson.text(config.get("schema")).equals("xar.native-owner-snapshot-config/v36")
                &&StrictJson.text(config.get("mode")).equals("current_superman_health_resume_saved_baseline_and_begin"),"Only explicit v36 restore-existing-baseline then one private Begin");
        ExactRef.fromJson(config.get("owner_descriptor"));
        var progress=ExactRef.fromJson(config.get("baseline_progress"));
        StrictJson.require(Path.of(progress.path()).isAbsolute()&&progress.bytes()>0&&progress.bytes()<=SMALL,"Bounded absolute actual baseline progress FilePin required");
        StrictJson.integer(config.get("overall_timeout_seconds"),1,600);StrictJson.integer(config.get("read_timeout_seconds"),1,60);
        StrictJson.integer(config.get("maximum_frames_per_operation"),1,65536);return progress;
    }
    static void initializeSupermanSavedBaselineResult(ObjectNode result,ObjectNode config,String machine) {
        currentSupermanSavedBaselineConfig(config);
        result.put("schema","xar.native-owner-current-superman-health/v1").put("mode",StrictJson.text(config.get("mode")))
                .put("machine_id",machine).put("steam_build_id","26785313").put("phase","baseline")
                .put("read_calls",0).put("choose_calls",0).put("save_calls",0).put("query_available",false).put("known_choice_dispatched",false)
                .put("baseline_physical_material_observed",false).put("baseline_source_restored_from_progress",false)
                .put("native_returned",false).put("native_handled",false).put("event_closed",false).put("health_changed",false)
                .put("trait_UI_rendered",false).put("new_date_observed",false).put("physical_save_confirmed",false);
    }
    record StockSeedConfig(Path archive,long maximumBytes,int observations,long checkpointPollMillis,int maximumCorePolls,long corePollMillis) {
        int submissions(){return Math.addExact(maximumCorePolls,11);}
    }
    static StockSeedConfig currentStockSeedConfig(ObjectNode config) {
        StrictJson.object(config,Set.of("schema","mode","owner_descriptor","overall_timeout_seconds","read_timeout_seconds","maximum_frames_per_operation",
                "checkpoint_archive_path","maximum_checkpoint_bytes","checkpoint_observation_attempts","checkpoint_poll_interval_ms","maximum_core_polls","core_poll_interval_ms"));
        StrictJson.require("xar.native-owner-snapshot-config/v39".equals(StrictJson.text(config.get("schema")))
                &&"current_stock_newgame_robert_seed".equals(StrictJson.text(config.get("mode"))),"Only explicit fixed stock NewGame Robert seed mode");
        ExactRef.fromJson(config.get("owner_descriptor"));
        StrictJson.integer(config.get("overall_timeout_seconds"),1,600);StrictJson.integer(config.get("read_timeout_seconds"),1,60);
        StrictJson.integer(config.get("maximum_frames_per_operation"),1,65536);
        Path archive=Path.of(StrictJson.text(config.get("checkpoint_archive_path"))).toAbsolutePath().normalize();
        StrictJson.require(Path.of(StrictJson.text(config.get("checkpoint_archive_path"))).isAbsolute(),"Independent absolute first-checkpoint archive required");
        return new StockSeedConfig(archive,StrictJson.integer(config.get("maximum_checkpoint_bytes"),1,1L<<30),
                Math.toIntExact(StrictJson.integer(config.get("checkpoint_observation_attempts"),1,64)),StrictJson.integer(config.get("checkpoint_poll_interval_ms"),100,5000),
                Math.toIntExact(StrictJson.integer(config.get("maximum_core_polls"),1,256)),StrictJson.integer(config.get("core_poll_interval_ms"),100,5000));
    }
    static void requireCurrentStockSeedDeclaration(NativeLaunchPlan.Load load,NativeLaunchPlan.PreparedProfile prepared)throws IOException {
        if(!(load instanceof NativeLaunchPlan.NewGame)||prepared.noMods().isEmpty()||prepared.optionalEnvironmentManifest().isPresent()
                ||!prepared.productionRoots().isEmpty()||!prepared.preparedInputs().equals(prepared.settingsSeed().map(List::of).orElseGet(List::of)))
            throw new IOException("Stock seed requires actual NewGame plus typed NoMods, no ENV/production root/fixture; only declared settings seed permitted");
    }
    static void requireStockSeedEnabledMods(JsonNode value)throws IOException {
        if(value==null||!value.isObject()||!value.has("enabled_mods")||!value.get("enabled_mods").isArray()||!value.get("enabled_mods").isEmpty())
            throw new IOException("Actual dlc_load.json must contain an empty enabled_mods array; DLC choices are preserved");
    }
    static boolean stockSeedCoreReady(CoreFrame frame)throws IOException {
        if(frame.build()!=ExactCk3Build.CK3_121003_STEAM_26785313)throw new IOException("Stock seed Core must be current exact267");
        if(!(frame instanceof CoreFrame.Partial actual))return false;
        var p=actual.prefix();
        // Fixed bm_1066_rags_to_riches date 1066.9.15, exact fixed365 raw24; never a caller date or actor ID.
        if(p.mapReady()&&p.hasPlayedCharacter()&&p.dateRaw()!=53144328)throw new IOException("Fixed 1066 seed escaped its original zero-day start date");
        return p.dateRaw()==53144328&&p.speed()>=1&&p.speed()<=5&&p.paused()&&p.localPlayerId()>=0&&p.mapReady()
                &&p.hasPlayedCharacter()&&p.playedCharacterId()!=-1&&p.playedCharacterAlive();
    }
    static void requireStockSeedSameCore(CoreFrame.Prefix before,CoreFrame.Partial after)throws IOException {
        if(!stockSeedCoreReady(after)||!before.equals(after.prefix()))throw new IOException("First checkpoint final independent Core changed its complete actual zero-day player/actor prefix");
    }
    static void requireStockSeedFrontendEffect(FrontendMenuFrameV1 query,FrontendMenuFrameV1 actual,FrontendMenuFrameV1.Action action)throws IOException {
        var expected=switch(action) {
            case OPEN_BOOKMARKS->FrontendMenuFrameV1.Status.BOOKMARKS_OPENED;
            case SELECT_1066_BOOKMARK->FrontendMenuFrameV1.Status.BOOKMARK_SELECTED;
            case SELECT_ROBERT_1066->FrontendMenuFrameV1.Status.SELECTION_DISPATCHED;
            case START_ROBERT_1066->FrontendMenuFrameV1.Status.START_DISPATCHED;
            default->throw new IOException("Only the fixed four NewGame seed actions are permitted");
        };
        if(query.action()!=FrontendMenuFrameV1.Action.QUERY_MENU||query.status()!=FrontendMenuFrameV1.Status.AVAILABLE
                ||actual.action()!=action||actual.status()!=expected||!actual.nativeOk()||!actual.effectAttempted()||!actual.nativeReturned()||actual.claimSequence().signum()<=0
                ||!actual.providerGeneration().equals(query.providerGeneration())||!actual.querySequence().equals(query.querySequence())
                ||actual.source().isEmpty()||query.ownerWitness().isEmpty()||actual.ownerWitness().isEmpty()
                ||!actual.ownerWitness().orElseThrow().connectionGeneration().equals(query.ownerWitness().orElseThrow().connectionGeneration()))
            throw new IOException("Fixed frontend action lacks this actual query lease/connection and its exact known callback result");
        // Source is the genuine after-menu source. Its route/selection may change; original query authority stays private in Transport.
    }
    private static void archiveStockSeedDlcLoad(NativeLaunchPlan plan,Path output,String label,ObjectNode originals)throws IOException {
        Path dlc=plan.profileDirectory().resolve("dlc_load.json");SharedSourceFiles.plainAncestors(dlc);
        var before=SharedSourceFiles.observe(dlc);byte[] raw=readBounded(dlc,SMALL);
        requireStockSeedEnabledMods(StrictJson.parse(raw,SMALL));
        if(!before.equals(SharedSourceFiles.observe(dlc)))throw new IOException("Actual NoMods dlc_load.json changed across its double witness");
        requireWitnessBytes(before,new ExactRef(dlc.toString(),raw.length,sha256(raw)));
        var proof=StrictJson.object();proof.set("original_file",new ExactRef(dlc.toString(),raw.length,sha256(raw)).toJson());
        proof.set("native_identity",nativeIdentity(before.nativeFile()));proof.put("enabled_mods_count",0).put("disabled_dlcs_restricted",false);
        originals.set(label+"_raw",write(output,label+".json",raw));originals.set(label+"_witness",write(output,label+"-witness.json",FullJsonTree.encode(proof,SMALL)));
    }
    private static NativeGameTransport.CoreReceived readStockSeedReadyCore(NativeGameTransport transport,GameSupervisorControl.Descriptor owner,NativeLaunchPlan plan,
            StockSeedConfig config,Path output,Instant deadline,Duration timeout,ObjectNode result,ObjectNode originals,NativeObservationPort.TransportSession expected)throws IOException,InterruptedException {
        for(int count=1;count<=config.maximumCorePolls();count++) {
            if(!Instant.now().isBefore(deadline))throw new IOException("Original stock seed world-read deadline expired");
            String label="world-core-"+String.format(java.util.Locale.ROOT,"%03d",count);
            var read=transport.readCoreFrameReceived(currentDjcReadDeadline(deadline,timeout));
            result.put("read_calls",result.path("read_calls").intValue()+1).put("world_core_polls",count);
            archiveCurrentLetterOutcome(transport,Files.createDirectory(output.resolve(label)),label,read.original(),originals);
            if(!(read instanceof NativeGameTransport.CoreReceived actual))throw new IOException("World poll lacks a typed actual Core receipt; UNKNOWN/source/custody failures stop without replay");
            requireCurrentDjcAckOwner(transport,owner,actual.original(),expected);actual.requireOriginal(transport,actual.validUntil());
            var frame=actual.frame();
            if(!frame.build().executableSha256().equalsIgnoreCase(plan.sources().review().gameExecutable().sha256())||!frame.build().coreFrameAdapterId().equals(plan.adapterId()))
                throw new IOException("Stock seed Core differs from actual owner executable/adapter");
            originals.set(label+"_frame",write(output,label+"-frame.json",CoreFramePublicCodec.encode(frame).bytes()));
            if(stockSeedCoreReady(frame))return actual;
            if(count==config.maximumCorePolls())break;
            long remaining=Duration.between(Instant.now(),deadline).toMillis();if(remaining<=0)break;Thread.sleep(Math.min(config.corePollMillis(),remaining));
        }
        throw new IOException("Bounded typed world Core polls did not establish the fixed paused zero-day seed; no SAVE");
    }
    private static void saveStockSeedFirstCheckpoint(NativeGameTransport transport,GameSupervisorControl.Descriptor owner,NativeLaunchPlan plan,
            NativeGameTransport.CoreReceived before,StockSeedConfig config,Path output,Instant deadline,Duration timeout,ObjectNode result,ObjectNode originals,
            NativeObservationPort.TransportSession session)throws IOException,InterruptedException {
        if(!(before.frame() instanceof CoreFrame.Partial core)||!stockSeedCoreReady(core))throw new IOException("Actual ready stock Core required for first checkpoint");
        requireCurrentDjcAckOwner(transport,owner,before.original(),session);
        Path checkpoint=plan.profileDirectory().resolve("save games").resolve(CurrentCoreCheckpointSave.FILENAME);var files=new NativeCheckpointFiles();
        var baseline=CurrentCoreCheckpointArchive.preflight(files,checkpoint,config.archive(),config.maximumBytes(),java.util.Optional.empty(),java.util.Optional.empty());
        Instant until=before.validUntil().isBefore(deadline)?before.validUntil():deadline;before.requireOriginal(transport,until);
        var prepared=transport.prepareCurrentCoreCheckpoint(before,until);Path action=Files.createDirectory(output.resolve("one-first-checkpoint"));
        var intent=StrictJson.object().put("schema","xar.current-stock-newgame-first-checkpoint-intent/v1").put("request_id",prepared.requestId())
                .put("original_deadline_utc",prepared.deadline().toString()).put("source_Core_request_id",before.original().requestId()).put("source_date_raw",prepared.sourceDateRaw())
                .put("save_name",CurrentCoreCheckpointSave.SAVE_NAME).put("physical_filename",CurrentCoreCheckpointSave.FILENAME).put("physical_save_confirmed",false);
        intent.set("original_outbound",write(action,"original-request.packet",prepared.originalPacket().value()));
        originals.set("first_save_intent",write(action,"original-intent.json",FullJsonTree.encode(intent,SMALL)));
        stage="ONE_STOCK_SEED_FIRST_SAVE";result.put("save_calls",1);
        var outcome=transport.submitCurrentCoreCheckpoint(prepared);archiveCurrentLetterOutcome(transport,Files.createDirectory(action.resolve("result")),"first_save",outcome,originals);
        if(!(outcome instanceof NativeActionPort.AckReceived ack))throw new IOException("First checkpoint is rejected/UNKNOWN; preserve original and never replay");
        requireCurrentDjcAckOwner(transport,owner,ack,session);var saved=CurrentCoreCheckpointSaveResult.decodeOutcome(ack);
        originals.set("first_save_result",write(action,"original-result.json",ack.originalResultToken().orElseThrow().bytes()));
        if(!saved.accepted()||saved.submission().isEmpty()||saved.submission().orElseThrow().dateRaw()!=core.prefix().dateRaw())throw new IOException("Actual first checkpoint ACK not accepted at original zero-day date");
        result.put("Native_physical_save_confirmed",false).put("native_checkpoint_status",saved.status().wire());
        stage="OBSERVE_STOCK_SEED_FIRST_PHYSICAL_SAVE";
        var material=CurrentCoreCheckpointArchive.observeAndCopyChanged(files,checkpoint,baseline,config.archive(),deadline,config.maximumBytes(),config.observations(),config.checkpointPollMillis());
        result.set("checkpoint_source",ControlBuild.strictMapper().valueToTree(material.source()));result.set("checkpoint_immutable_archive",ControlBuild.strictMapper().valueToTree(material.archive()));
        result.set("inspect_save_pin",material.archive().reference().toJson());
        result.put("changed_physical_material_observed",true).put("archive_is_copy_not_another_SAVE",true).put("physical_save_confirmed",false).put("saved_content_inspected",false);
        stage="INDEPENDENT_STOCK_SEED_CORE_AFTER_SAVE";
        var read=transport.readCoreFrameReceived(currentDjcReadDeadline(deadline,timeout));result.put("read_calls",result.path("read_calls").intValue()+1);
        archiveCurrentLetterOutcome(transport,Files.createDirectory(output.resolve("independent-core-after-save")),"final_core",read.original(),originals);
        if(!(read instanceof NativeGameTransport.CoreReceived after)||!(after.frame() instanceof CoreFrame.Partial frame))throw new IOException("Independent actual final Core unavailable after first checkpoint");
        requireCurrentDjcAckOwner(transport,owner,after.original(),session);after.requireOriginal(transport,after.validUntil());requireStockSeedSameCore(core.prefix(),frame);
        result.set("final_core",FullJsonTree.parse(CoreFramePublicCodec.encode(frame).bytes(),SMALL));result.put("zero_day_same_actual_actor_confirmed",true);
    }
    private static void runCurrentStockSeed(NativeGameTransport transport,GameSupervisorControl.Descriptor owner,NativeLaunchPlan plan,StockSeedConfig config,
            Path output,Instant deadline,Duration timeout,ObjectNode result,ObjectNode originals)throws IOException,InterruptedException {
        result.put("schema","xar.native-owner-current-stock-newgame-seed/v1").put("mode","current_stock_newgame_robert_seed").put("read_calls",0)
                .put("frontend_effect_calls",0).put("save_calls",0).put("date_calls",0).put("physical_save_confirmed",false).put("saved_content_inspected",false)
                .put("world_core_fabricated",false).put("game_started_confirmed",false).put("zero_day_same_actual_actor_confirmed",false).put("business_or_product_credit",false);
        try {
            requireCurrentStockSeedDeclaration(plan.load(),plan.preparedProfile());requireCurrentFrontendMenuPlan(plan);
            if(plan.windowPolicy()!=NativeLaunchPlan.WindowPolicy.MINIMIZED_NO_ACTIVATE)throw new IOException("Stock seed retains actual minimized/noactivate launch policy");
            Path exe=Path.of(plan.sources().review().gameExecutable().path()).toRealPath(java.nio.file.LinkOption.NOFOLLOW_LINKS);
            Path stock=exe.getParent().getParent().resolve("game");Path profile=plan.profileDirectory();
            SharedSourceFiles.plainAncestors(stock);SharedSourceFiles.plainAncestors(profile);
            var stockIdentity=SharedSourceFiles.nativeDirectory(stock);var profileIdentity=SharedSourceFiles.nativeDirectory(profile);
            result.put("actual_stock_root",stock.toString()).put("actual_profile_root",profile.toString());
            result.set("stock_root_native_identity",ControlBuild.strictMapper().valueToTree(stockIdentity));result.set("profile_root_native_identity",ControlBuild.strictMapper().valueToTree(profileIdentity));
            var files=new NativeCheckpointFiles();CurrentCoreCheckpointArchive.preflight(files,profile.resolve("save games").resolve(CurrentCoreCheckpointSave.FILENAME),config.archive(),config.maximumBytes(),java.util.Optional.empty(),java.util.Optional.empty());
            archiveStockSeedDlcLoad(plan,output,"dlc-load-before-new-world",originals);
            NativeObservationPort.TransportSession session=null;
            for(var action:List.of(FrontendMenuFrameV1.Action.OPEN_BOOKMARKS,FrontendMenuFrameV1.Action.SELECT_1066_BOOKMARK,
                    FrontendMenuFrameV1.Action.SELECT_ROBERT_1066,FrontendMenuFrameV1.Action.START_ROBERT_1066)) {
                if(!Instant.now().isBefore(deadline))throw new IOException("Original stock seed deadline expired before fixed action");
                String label=action.wire();Path stepOutput=Files.createDirectory(output.resolve(label));
                stage="STOCK_SEED_ACTUAL_FRESH_MENU_QUERY";
                var read=transport.readCurrentFrontendMenu(currentDjcReadDeadline(deadline,timeout));result.put("read_calls",result.path("read_calls").intValue()+1);
                archiveCurrentLetterOutcome(transport,Files.createDirectory(stepOutput.resolve("query")),label+"_query",read.original(),originals);
                if(!(read instanceof NativeGameTransport.FrontendMenuReceived query))throw new IOException("Actual fixed frontend query unavailable; no automatic retry/effect");
                query.requireOriginal(transport);requireCurrentDjcAckOwner(transport,owner,query.original(),session);
                if(session==null)session=query.original().custody().orElseThrow().session();
                var frame=FrontendMenuFrameV1PublicCodec.decodeOutcome(query.original());if(!frame.equals(query.frame()))throw new IOException("Actual frontend query changed");
                requireCurrentFrontendMenuSelection(plan,frame);originals.set(label+"_query_result",write(stepOutput,"original-query-result.json",query.original().originalResultToken().orElseThrow().bytes()));
                var prepared=transport.prepareCurrentFrontendMenuAction(query,action);
                var intent=StrictJson.object().put("schema","xar.current-stock-newgame-frontend-intent/v1").put("request_id",prepared.requestId()).put("action",action.wire())
                        .put("original_deadline_utc",prepared.deadline().toString()).put("source_query_request_id",query.original().requestId())
                        .put("provider_generation",frame.providerGeneration().toString()).put("query_sequence",frame.querySequence().toString()).put("game_started_confirmed",false);
                intent.set("original_outbound",write(stepOutput,"original-request.packet",prepared.originalPacket().value()));
                originals.set(label+"_intent",write(stepOutput,"original-intent.json",FullJsonTree.encode(intent,SMALL)));
                stage="STOCK_SEED_ONCE_FIXED_FRONTEND_ACTION";result.put("frontend_effect_calls",result.path("frontend_effect_calls").intValue()+1);
                var outcome=transport.submitCurrentFrontendMenuAction(prepared);archiveCurrentLetterOutcome(transport,Files.createDirectory(stepOutput.resolve("action-result")),label+"_action",outcome,originals);
                if(!(outcome instanceof NativeActionPort.AckReceived ack))throw new IOException("Fixed frontend action rejected/UNKNOWN; preserve original, no replacement or replay");
                requireCurrentDjcAckOwner(transport,owner,ack,session);var actual=FrontendMenuFrameV1PublicCodec.decodeOutcome(ack);
                originals.set(label+"_result",write(stepOutput,"original-result.json",ack.originalResultToken().orElseThrow().bytes()));
                requireCurrentFrontendMenuSelection(plan,actual);requireStockSeedFrontendEffect(frame,actual,action);
            }
            result.set("session",session(session));stage="STOCK_SEED_BOUNDED_FRESH_WORLD_CORE";
            var ready=readStockSeedReadyCore(transport,owner,plan,config,output,deadline,timeout,result,originals,session);
            result.put("game_started_confirmed",true);result.set("ready_core",FullJsonTree.parse(CoreFramePublicCodec.encode(ready.frame()).bytes(),SMALL));
            saveStockSeedFirstCheckpoint(transport,owner,plan,ready,config,output,deadline,timeout,result,originals,session);
            archiveStockSeedDlcLoad(plan,output,"dlc-load-after-first-save",originals);
            if(!stockIdentity.equals(SharedSourceFiles.nativeDirectory(stock))||!profileIdentity.equals(SharedSourceFiles.nativeDirectory(profile)))throw new IOException("Actual stock/profile root identity changed across seed workflow");
            result.put("actual_empty_enabled_mods_before_and_after",true);
        } finally {
            archiveNaturalDiagnostics(output,originals,transport.diagnostics());var progress=result.deepCopy();progress.set("originals",originals.deepCopy());
            write(output,"current-stock-newgame-seed-progress.json",FullJsonTree.encode(progress,FullJsonTree.MAXIMUM_BYTES));
        }
    }

    record TedConfig(boolean transition,int maximumStatusPolls,long statusPollDelayMillis) {
        int submissions(){return transition?Math.addExact(10,Math.multiplyExact(2,maximumStatusPolls)):2;}
    }
    static TedConfig currentTedConfig(ObjectNode config) {
        StrictJson.require("xar.native-owner-snapshot-config/v38".equals(StrictJson.text(config.get("schema"))),"Explicit v38 fixed TED role/transition mode required");
        boolean transition=switch(StrictJson.text(config.get("mode"))) {
            case "current_ted_query_role"->false;
            case "current_ted_two_day_known_transition"->true;
            default->throw new IllegalArgumentException("Only readonly TED role or the fixed original two-day transition");
        };
        var fields=new java.util.HashSet<>(Set.of("schema","mode","owner_descriptor","overall_timeout_seconds","read_timeout_seconds","maximum_frames_per_operation"));
        if(transition){fields.add("maximum_status_polls");fields.add("status_poll_delay_ms");}StrictJson.object(config,Set.copyOf(fields));
        ExactRef.fromJson(config.get("owner_descriptor"));StrictJson.integer(config.get("overall_timeout_seconds"),1,600);
        StrictJson.integer(config.get("read_timeout_seconds"),1,60);StrictJson.integer(config.get("maximum_frames_per_operation"),1,65536);
        return new TedConfig(transition,transition?Math.toIntExact(StrictJson.integer(config.get("maximum_status_polls"),1,256)):0,
                transition?StrictJson.integer(config.get("status_poll_delay_ms"),1,1000):0);
    }
    static void requireCurrentTedRole(CurrentTedActorTransitionResult frame,CoreFrame.Prefix prefix)throws IOException {
        if(frame.action()!=CurrentTedActorTransition.Action.QUERY_ROLE||frame.status()!=CurrentTedActorTransitionResult.Status.AVAILABLE||!frame.ok()||frame.accepted()
                ||!frame.operationId().isEmpty()||frame.claimSequence().signum()!=0||frame.effectAttempted()||frame.nativeReturned()||!frame.cleanupKnown()
                ||frame.providerGeneration().signum()<=0||frame.querySequence().signum()<=0||frame.connectionGeneration().signum()<=0
                ||frame.factsBefore().filter(prefix::equals).isEmpty()||frame.source().isEmpty()||frame.progress().isPresent())throw new IOException("Actual TED role query lacks original Core/whole Source/private lease");
    }
    static CurrentTedActorTransitionSource requireCurrentTedPositiveRole(CurrentTedActorTransitionResult frame,CoreFrame.Prefix prefix,
            CurrentTedActorTransitionSource.Role role,java.math.BigInteger epoch,int song,int recipient,boolean confirm)throws IOException {
        requireCurrentTedRole(frame,prefix);var source=frame.source().orElseThrow();
        if(!source.definitionFound()||!source.nativeShown().orElse(false)||!source.runtimeReady()||!source.predecessorResolved()||source.role()!=role
                ||!source.actorEpoch().equals(epoch)||!frame.actorEpoch().equals(epoch)||source.songActorId().filter(id->id==song).isEmpty()
                ||(role==CurrentTedActorTransitionSource.Role.SONG?prefix.playedCharacterId()!=song:prefix.playedCharacterId()!=recipient||source.recipientActorId().filter(id->id==recipient).isEmpty())
                ||(confirm?!source.confirmAdmissible():!source.advanceAdmissible()))throw new IOException("Actual shown TED role/epoch/actor IDs do not admit this fixed next step");
        return source;
    }
    static void requireCurrentTedDayTerminal(CurrentTedActorTransitionResult frame,CoreFrame.Prefix start,String operation,int target,boolean firstDay)throws IOException {
        var status=firstDay?CurrentTedActorTransitionResult.Status.TRANSITION_PENDING:CurrentTedActorTransitionResult.Status.COMPLETED_DAY;
        if(frame.status()!=status||!frame.ok()||!frame.accepted()||!frame.operationId().equals(operation)||frame.factsBefore().filter(start::equals).isEmpty()
                ||frame.claimSequence().signum()<=0||!frame.cleanupKnown()||!frame.effectAttempted()||!frame.nativeReturned()
                ||!frame.actorEpoch().equals(firstDay?java.math.BigInteger.ZERO:java.math.BigInteger.TWO)||frame.progress().isEmpty())throw new IOException("TED requires exact D1 pending or D2 completed, never generic actor-abort/refusal/UNKNOWN");
        var p=frame.progress().orElseThrow();
        if(p.generation().signum()<=0||p.startingDateRaw()!=start.dateRaw()||(long)start.dateRaw()+24!=target||p.targetDateRaw()!=target||p.lastObservedDateRaw()!=target
                ||p.beforeActorId()!=start.playedCharacterId()||p.afterActorId()==-1||p.completedDailyTicks()!=1||p.failureFlags()!=0||p.overshootDays()!=0
                ||!p.armAttempted()||!p.resumeAttempted()||!p.resumeSubmitted()||!p.exactDayConfirmed()||!p.shutdownSafe()||p.armed()||p.accessCleanupUnknown()
                ||p.transitionPending()!=firstDay||(firstDay?p.afterActorId()==p.beforeActorId():p.afterActorId()!=p.beforeActorId()))throw new IOException("TED terminal must contain one actual daily tick, exact24, correct actors and disarmed known cleanup");
    }
    static CoreFrame.Prefix currentTedAfter(CoreFrame.Prefix before,int date,int actor)throws IOException {
        if(actor==-1||(long)before.dateRaw()+24!=date)throw new IOException("Exact one-day actual actor proof required");
        return new CoreFrame.Prefix(date,before.speed(),before.paused(),before.localPlayerId(),before.mapReady(),before.hasPlayedCharacter(),actor,before.playedCharacterAlive());
    }
    private static NativeGameTransport.CoreReceived readCurrentTedCore(NativeGameTransport transport,GameSupervisorControl.Descriptor owner,NativeLaunchPlan plan,
            Path output,String label,Instant deadline,ObjectNode result,ObjectNode originals,NativeObservationPort.TransportSession expectedSession,CoreFrame.Prefix expected)throws IOException,InterruptedException {
        stage="FRESH_INDEPENDENT_TED_CORE";result.put("read_calls",result.path("read_calls").intValue()+1);
        var read=transport.readCoreFrameReceived(deadline);archiveCurrentLetterOutcome(transport,Files.createDirectory(output.resolve(label)),label,read.original(),originals);
        if(!(read instanceof NativeGameTransport.CoreReceived before)||!(before.frame() instanceof CoreFrame.Partial core))throw new IOException("Actual TED Core unavailable; stop without action/retry");
        requireCurrentDjcAckOwner(transport,owner,before.original(),expectedSession);var p=core.prefix();
        if(core.build()!=ExactCk3Build.CK3_121003_STEAM_26785313||!core.build().executableSha256().equalsIgnoreCase(plan.sources().review().gameExecutable().sha256())||!core.build().coreFrameAdapterId().equals(plan.adapterId())
                ||!p.paused()||!p.mapReady()||!p.hasPlayedCharacter()||!p.playedCharacterAlive()||p.playedCharacterId()==-1||p.localPlayerId()<0||p.speed()<1||p.speed()>5||expected!=null&&!expected.equals(p))throw new IOException("Exact current paused living independent TED Core differs");
        before.requireOriginal(transport,before.validUntil().isBefore(deadline)?before.validUntil():deadline);return before;
    }
    private static NativeGameTransport.TedRoleReceived readCurrentTedRole(NativeGameTransport transport,GameSupervisorControl.Descriptor owner,NativeGameTransport.CoreReceived before,
            NativeObservationPort.TransportSession session,Path output,String label,Instant deadline,ObjectNode result,ObjectNode originals)throws IOException,InterruptedException {
        Instant until=before.validUntil().isBefore(deadline)?before.validUntil():deadline;stage="ONE_READONLY_TED_ROLE";result.put("read_calls",result.path("read_calls").intValue()+1);
        var read=transport.readCurrentTedRole(before,until);Path queryOutput=Files.createDirectory(output.resolve(label));archiveCurrentLetterOutcome(transport,queryOutput,label,read.original(),originals);
        if(!(read instanceof NativeGameTransport.TedRoleReceived query))throw new IOException("Actual TED role refused/UNKNOWN; never substitute a caller role");
        query.requireOriginal(transport,query.validUntil());var ack=query.original();requireCurrentDjcAckOwner(transport,owner,ack,session);var frame=CurrentTedActorTransitionResult.decodeOutcome(ack);
        if(!frame.equals(query.frame())||query.validUntil().isAfter(until)||frame.deadlineUnixMs()!=query.validUntil().toEpochMilli()||!frame.connectionGeneration().equals(session.connectionGeneration()))throw new IOException("TED private query changed this ACK/original deadline/connection");
        requireCurrentTedRole(frame,((CoreFrame.Partial)before.frame()).prefix());originals.set(label+"_original_result",write(queryOutput,"original-result.json",ack.originalResultToken().orElseThrow().bytes()));
        result.set(label,FullJsonTree.parse(frame.encode().bytes(),SMALL));return query;
    }
    private static void archiveCurrentTedIntent(Path output,String label,String requestId,String operation,Instant deadline,byte[] packet,ObjectNode originals)throws IOException {
        Path action=Files.createDirectory(output.resolve(label));var intent=StrictJson.object().put("schema","xar.current-ted-original-intent/v1").put("request_id",requestId).put("operation_id",operation)
                .put("original_deadline_utc",deadline.toString()).put("independent_after_core_verified",false).put("physical_save_confirmed",false);
        intent.set("original_outbound",write(action,"original-request.packet",packet));originals.set(label+"_intent",write(action,"original-intent.json",FullJsonTree.encode(intent,SMALL)));
    }
    private static CurrentTedActorTransitionResult archiveCurrentTedOperation(NativeGameTransport transport,GameSupervisorControl.Descriptor owner,NativeGameTransport.TedAdvancePrepared prepared,
            NativeGameTransport.TedRoleReceived originalRole,NativeActionPort.DispatchOutcome outcome,NativeObservationPort.TransportSession session,Path output,String label,ObjectNode result,ObjectNode originals)throws IOException {
        Path actual=Files.createDirectory(output.resolve(label));archiveCurrentLetterOutcome(transport,actual,label,outcome,originals);
        if(!(outcome instanceof NativeActionPort.AckReceived ack))throw new IOException("Original TED advance/status refused or UNKNOWN; do not retry/replay");
        requireCurrentDjcAckOwner(transport,owner,ack,session);var f=CurrentTedActorTransitionResult.decodeOutcome(ack);
        originals.set(label+"_original_result",write(actual,"original-result.json",ack.originalResultToken().orElseThrow().bytes()));result.set(label,FullJsonTree.parse(f.encode().bytes(),SMALL));
        var q=originalRole.frame();
        if(prepared.originalUnknown()||prepared.latestFrame().filter(f::equals).isEmpty()||!f.operationId().equals(prepared.operationId())||f.deadlineUnixMs()!=prepared.deadline().toEpochMilli()
                ||!f.providerGeneration().equals(q.providerGeneration())||!f.querySequence().equals(q.querySequence())||!f.factsBefore().equals(q.factsBefore())||!f.connectionGeneration().equals(session.connectionGeneration())||!f.cleanupKnown()
                ||f.action()!=CurrentTedActorTransition.Action.ADVANCE_DAY&&f.action()!=CurrentTedActorTransition.Action.QUERY_OPERATION
                ||f.action()==CurrentTedActorTransition.Action.QUERY_OPERATION&&f.source().isPresent()
                ||f.action()==CurrentTedActorTransition.Action.ADVANCE_DAY&&!f.source().equals(q.source()))throw new IOException("Original TED operation lost this ACK/full source/Core/lease/ID/deadline or became UNKNOWN");
        if(f.status()!=CurrentTedActorTransitionResult.Status.SUBMITTED&&f.status()!=CurrentTedActorTransitionResult.Status.RUNNING&&f.status()!=CurrentTedActorTransitionResult.Status.TRANSITION_PENDING&&f.status()!=CurrentTedActorTransitionResult.Status.COMPLETED_DAY)
            throw new IOException("Actual TED operation refused/unknown; no fresh-ID workaround");
        return f;
    }
    private static CurrentTedActorTransitionResult runCurrentTedDay(NativeGameTransport transport,GameSupervisorControl.Descriptor owner,NativeGameTransport.TedRoleReceived role,
            NativeGameTransport.TedAdvancePrepared prepared,TedConfig config,NativeObservationPort.TransportSession session,Path output,String label,Instant parentDeadline,Duration readTimeout,
            ObjectNode result,ObjectNode originals,boolean firstDay)throws IOException,InterruptedException {
        if(!prepared.deadline().equals(role.validUntil())||prepared.deadline().isAfter(parentDeadline)||prepared.targetDateRaw()!=Math.addExact(role.frame().factsBefore().orElseThrow().dateRaw(),24))throw new IOException("Original TED day preparation changed source/deadline/24 target");
        archiveCurrentTedIntent(output,label+"-intent",prepared.requestId(),prepared.operationId(),prepared.deadline(),prepared.originalPacket().value(),originals);
        stage="ONCE_FIXED_TED_ADVANCE";result.put("advance_calls",result.path("advance_calls").intValue()+1);
        var outcome=transport.submitCurrentTedAdvance(prepared);
        var frame=archiveCurrentTedOperation(transport,owner,prepared,role,outcome,session,output,label+"-submit",result,originals);
        for(int i=0;frame.status()==CurrentTedActorTransitionResult.Status.SUBMITTED||frame.status()==CurrentTedActorTransitionResult.Status.RUNNING;i++) {
            if(i>=config.maximumStatusPolls())throw new IOException("Bounded original TED status observations exhausted; preserve original operation without retry");
            if(!Instant.now().plusMillis(config.statusPollDelayMillis()).isBefore(parentDeadline))throw new IOException("Original parent deadline cannot be extended by TED polling");
            Thread.sleep(config.statusPollDelayMillis());Instant receive=Instant.now().plus(readTimeout);if(receive.isAfter(parentDeadline))receive=parentDeadline;
            stage="READONLY_ORIGINAL_TED_OPERATION_STATUS";result.put("status_queries",result.path("status_queries").intValue()+1);
            var status=transport.queryCurrentTedOperation(prepared,receive);
            frame=archiveCurrentTedOperation(transport,owner,prepared,role,status,session,output,label+"-status-"+String.format(java.util.Locale.ROOT,"%03d",i+1),result,originals);
        }
        requireCurrentTedDayTerminal(frame,role.frame().factsBefore().orElseThrow(),prepared.operationId(),prepared.targetDateRaw(),firstDay);return frame;
    }
    private static void runCurrentTed(NativeGameTransport transport,GameSupervisorControl.Descriptor owner,NativeLaunchPlan plan,TedConfig config,Path output,
            Instant deadline,Duration readTimeout,ObjectNode result,ObjectNode originals)throws IOException,InterruptedException {
        try {
            if(!(plan.load() instanceof NativeLaunchPlan.SavedGame))throw new IOException("TED requires its actual SavedGame owner");
            var before=readCurrentTedCore(transport,owner,plan,output,"ted-core-before",deadline,result,originals,null,null);var start=((CoreFrame.Partial)before.frame()).prefix();
            var session=before.original().custody().orElseThrow().session();result.set("session",session(session));
            var role=readCurrentTedRole(transport,owner,before,session,output,"ted-role-before",deadline,result,originals);result.put("query_available",true);
            if(!config.transition())return;
            requireCurrentTedPositiveRole(role.frame(),start,CurrentTedActorTransitionSource.Role.SONG,java.math.BigInteger.ZERO,start.playedCharacterId(),-1,false);
            var day1=transport.prepareCurrentTedAdvance(role);var pending=runCurrentTedDay(transport,owner,role,day1,config,session,output,"ted-day01",deadline,readTimeout,result,originals,true);
            var p=pending.progress().orElseThrow();var afterDay1=currentTedAfter(start,day1.targetDateRaw(),p.afterActorId());
            var after=readCurrentTedCore(transport,owner,plan,output,"ted-core-after-pending",day1.deadline(),result,originals,session,afterDay1);
            var recipient=readCurrentTedRole(transport,owner,after,session,output,"ted-recipient-before-epoch",day1.deadline(),result,originals);
            var source=requireCurrentTedPositiveRole(recipient.frame(),afterDay1,CurrentTedActorTransitionSource.Role.RECIPIENT,java.math.BigInteger.ZERO,start.playedCharacterId(),p.afterActorId(),true);
            var actualPending=source.pending().orElseThrow(()->new IOException("Independent recipient Source lacks original pending proof"));
            if(!actualPending.operationId().equals(day1.operationId())||!actualPending.claimSequence().equals(pending.claimSequence())||!actualPending.generation().equals(p.generation())
                    ||actualPending.originalDeadlineUnixMs()!=day1.deadline().toEpochMilli()||actualPending.beforeActorId()!=start.playedCharacterId()||actualPending.afterActorId()!=p.afterActorId()
                    ||actualPending.startingDateRaw()!=start.dateRaw()||actualPending.targetDateRaw()!=day1.targetDateRaw())throw new IOException("Actual recipient proof differs from original D1 claim/generation/deadline/actors");
            var epoch=transport.prepareCurrentTedEpoch(day1,recipient);
            if(!epoch.operationId().equals(day1.operationId())||!epoch.deadline().equals(recipient.validUntil())||epoch.deadline().isAfter(day1.deadline()))throw new IOException("Epoch confirmation must retain original D1 operation and unextended deadline");
            archiveCurrentTedIntent(output,"ted-confirm-epoch-intent",epoch.requestId(),epoch.operationId(),epoch.deadline(),epoch.originalPacket().value(),originals);
            stage="ONCE_PROVED_TED_EPOCH_CONFIRMATION";result.put("epoch_confirm_calls",1);var epochOutcome=transport.submitCurrentTedEpoch(epoch);
            Path epochOut=Files.createDirectory(output.resolve("ted-confirm-epoch-result"));archiveCurrentLetterOutcome(transport,epochOut,"ted_epoch",epochOutcome,originals);
            if(!(epochOutcome instanceof NativeActionPort.AckReceived ack))throw new IOException("Original TED epoch refused/UNKNOWN; never re-confirm");
            requireCurrentDjcAckOwner(transport,owner,ack,session);var confirmed=CurrentTedActorTransitionResult.decodeOutcome(ack);
            originals.set("ted_epoch_original_result",write(epochOut,"original-result.json",ack.originalResultToken().orElseThrow().bytes()));result.set("epoch_confirmation",FullJsonTree.parse(confirmed.encode().bytes(),SMALL));
            if(epoch.latestFrame().filter(confirmed::equals).isEmpty()||confirmed.status()!=CurrentTedActorTransitionResult.Status.EPOCH_CONFIRMED||confirmed.action()!=CurrentTedActorTransition.Action.CONFIRM_EPOCH
                    ||!confirmed.operationId().equals(day1.operationId())||!confirmed.accepted()||confirmed.claimSequence().signum()<=0||!confirmed.actorEpoch().equals(java.math.BigInteger.ONE)
                    ||confirmed.effectAttempted()||confirmed.nativeReturned()||!confirmed.cleanupKnown()||!confirmed.source().equals(recipient.frame().source())||!confirmed.factsBefore().equals(recipient.frame().factsBefore())
                    ||!confirmed.providerGeneration().equals(recipient.frame().providerGeneration())||!confirmed.querySequence().equals(recipient.frame().querySequence())||confirmed.deadlineUnixMs()!=epoch.deadline().toEpochMilli()
                    ||!confirmed.connectionGeneration().equals(session.connectionGeneration()))throw new IOException("Epoch confirmation lacks exact private receipt/source/lease/frontier1; no Game action is credited");
            result.put("epoch_confirmed",true);
            var beforeDay2=readCurrentTedCore(transport,owner,plan,output,"ted-core-before-day02",deadline,result,originals,session,afterDay1);
            var role2=readCurrentTedRole(transport,owner,beforeDay2,session,output,"ted-role-before-day02",deadline,result,originals);
            requireCurrentTedPositiveRole(role2.frame(),afterDay1,CurrentTedActorTransitionSource.Role.RECIPIENT,java.math.BigInteger.ONE,start.playedCharacterId(),p.afterActorId(),false);
            var day2=transport.prepareCurrentTedAdvance(role2);if(day2.operationId().equals(day1.operationId())||day2.requestId().equals(day1.requestId()))throw new IOException("D2 requires its own new private operation, never replay D1");
            runCurrentTedDay(transport,owner,role2,day2,config,session,output,"ted-day02",deadline,readTimeout,result,originals,false);
            var finalPrefix=currentTedAfter(afterDay1,day2.targetDateRaw(),p.afterActorId());
            readCurrentTedCore(transport,owner,plan,output,"ted-core-independent-after-day02",deadline,result,originals,session,finalPrefix);
            result.put("two_days_observed",true).put("independent_after_core_verified",true).put("final_date_raw",finalPrefix.dateRaw()).put("recipient_actor_id",finalPrefix.playedCharacterId());
        } finally {
            archiveNaturalDiagnostics(output,originals,transport.diagnostics());var progress=result.deepCopy();progress.set("originals",originals.deepCopy());write(output,"current-ted-transition-progress.json",FullJsonTree.encode(progress,FullJsonTree.MAXIMUM_BYTES));
        }
    }

    enum LydMode {
        QUERY_DECISIONS("current_lyd_query_decisions",CurrentLyd.Action.QUERY_DECISIONS,CurrentLyd.Action.QUERY_DECISIONS),
        QUERY_EVENTS("current_lyd_query_events",CurrentLyd.Action.QUERY_EVENTS,CurrentLyd.Action.QUERY_EVENTS),
        QUERY_PERSONAL("current_lyd_query_personal",CurrentLyd.Action.QUERY_PERSONAL,CurrentLyd.Action.QUERY_PERSONAL),
        QUERY_READBACK("current_lyd_query_readback",CurrentLyd.Action.QUERY_READBACK,CurrentLyd.Action.QUERY_READBACK),
        OPEN_LIST("current_lyd_open_list",CurrentLyd.Action.QUERY_DECISIONS,CurrentLyd.Action.OPEN_LIST),
        OPEN_DETAIL("current_lyd_open_detail",CurrentLyd.Action.QUERY_DECISIONS,CurrentLyd.Action.OPEN_DETAIL),
        CONFIRM_DECISION("current_lyd_confirm_decision",CurrentLyd.Action.QUERY_DECISIONS,CurrentLyd.Action.CONFIRM_DECISION),
        CHOOSE_KNOWN_EVENT_OPTION("current_lyd_choose_known_event_option",CurrentLyd.Action.QUERY_EVENTS,CurrentLyd.Action.CHOOSE_KNOWN_EVENT_OPTION),
        OPEN_PERSONAL("current_lyd_open_personal",CurrentLyd.Action.QUERY_PERSONAL,CurrentLyd.Action.OPEN_PERSONAL),
        START_ADD_PERSONAL("current_lyd_start_add_personal",CurrentLyd.Action.QUERY_PERSONAL,CurrentLyd.Action.START_ADD_PERSONAL),
        ADD_PERSONAL("current_lyd_add_personal",CurrentLyd.Action.QUERY_PERSONAL,CurrentLyd.Action.CONFIRM_PERSONAL_ADD);
        private final String wire;private final CurrentLyd.Action queryAction,action;
        LydMode(String wire,CurrentLyd.Action queryAction,CurrentLyd.Action action){this.wire=wire;this.queryAction=queryAction;this.action=action;}
        String wire(){return wire;}CurrentLyd.Action queryAction(){return queryAction;}CurrentLyd.Action action(){return action;}
        boolean decision(){return this==OPEN_DETAIL||this==CONFIRM_DECISION;}
        boolean personal(){return queryAction==CurrentLyd.Action.QUERY_PERSONAL;}
        boolean event(){return this==CHOOSE_KNOWN_EVENT_OPTION;}
        int submissions(){return this==ADD_PERSONAL?6:action.isQuery()?2:3;}
    }
    record LydConfig(LydMode mode,java.util.Optional<CurrentLyd.DecisionKey> decisionKey,
            java.util.Optional<CurrentLyd.PersonalKey> personalKey,java.util.Optional<CurrentLyd.EventRole> eventRole) {
        LydConfig {
            Objects.requireNonNull(mode);Objects.requireNonNull(decisionKey);Objects.requireNonNull(personalKey);Objects.requireNonNull(eventRole);
            StrictJson.require(decisionKey.isPresent()==mode.decision()&&personalKey.isPresent()==mode.personal()&&eventRole.isPresent()==mode.event(),"Fixed LYD mode requires only its own typed DATA selector");
            StrictJson.require(mode!=LydMode.CONFIRM_DECISION||decisionKey.orElseThrow()!=CurrentLyd.DecisionKey.BEGIN_READONLY,"LYD Begin is detail-only");
        }
        CurrentLyd.Target queryTarget(){return personalKey.map(CurrentLyd.Target::personal).orElseGet(CurrentLyd.Target::none);}
    }
    static LydConfig currentLydConfig(ObjectNode config) {
        StrictJson.require("xar.native-owner-snapshot-config/v37".equals(StrictJson.text(config.get("schema"))),"Explicit v37 fixed LYD mode required");
        String wire=StrictJson.text(config.get("mode"));LydMode mode=Arrays.stream(LydMode.values()).filter(m->m.wire().equals(wire)).findFirst()
                .orElseThrow(()->new IllegalArgumentException("Only independent fixed LYD modes or the original same-receiver personal ADD chain"));
        var fields=new java.util.HashSet<>(Set.of("schema","mode","owner_descriptor","overall_timeout_seconds","read_timeout_seconds","maximum_frames_per_operation"));
        if(mode.decision())fields.add("decision_key");if(mode.personal())fields.add("personal_key");if(mode.event())fields.add("event_role");StrictJson.object(config,Set.copyOf(fields));
        ExactRef.fromJson(config.get("owner_descriptor"));StrictJson.integer(config.get("overall_timeout_seconds"),1,600);
        StrictJson.integer(config.get("read_timeout_seconds"),1,60);StrictJson.integer(config.get("maximum_frames_per_operation"),1,65536);
        try {
            return new LydConfig(mode,mode.decision()?java.util.Optional.of(CurrentLyd.DecisionKey.parse(StrictJson.text(config.get("decision_key")))):java.util.Optional.empty(),
                    mode.personal()?java.util.Optional.of(CurrentLyd.PersonalKey.parse(StrictJson.text(config.get("personal_key")))):java.util.Optional.empty(),
                    mode.event()?java.util.Optional.of(CurrentLyd.EventRole.parse(StrictJson.text(config.get("event_role")))):java.util.Optional.empty());
        }catch(IOException invalid){throw new IllegalArgumentException("Exact fixed LYD DATA selector required",invalid);}
    }
    static void initializeCurrentLydResult(ObjectNode result,LydConfig config,String machine) {
        result.put("schema","xar.native-owner-current-lyd/v1").put("mode",config.mode().wire()).put("machine_id",machine).put("steam_build_id","26785313")
                .put("action",config.mode().action().wire()).put("read_calls",0).put("action_calls",0).put("select_calls",0).put("confirm_calls",0)
                .put("query_available",false).put("add_query_available",false).put("callback_dispatched",false).put("native_returned",false).put("native_handled",false)
                .put("event_closed",false).put("personal_applied",false).put("gold_paid",false).put("piety_paid",false).put("modifiers_applied",false)
                .put("new_date_observed",false).put("physical_save_confirmed",false).put("save_calls",0);
        if(config.decisionKey().isPresent())result.put("decision_key",config.decisionKey().orElseThrow().wire());else result.putNull("decision_key");
        if(config.personalKey().isPresent())result.put("personal_key",config.personalKey().orElseThrow().wire());else result.putNull("personal_key");
        if(config.eventRole().isPresent())result.put("event_role",config.eventRole().orElseThrow().wire());else result.putNull("event_role");
    }
    static void requireCurrentLydQueryFrame(CurrentLydResult frame,CoreFrame.Prefix actual,CurrentLyd.Action action,CurrentLyd.Target target)throws IOException {
        if(!action.isQuery()||frame.action()!=action||frame.status()!=CurrentLydResult.Status.AVAILABLE||frame.effectAttempted()||frame.nativeReturned()||frame.nativeHandled()
                ||!frame.cleanupKnown()||frame.claimSequence().signum()!=0||frame.providerGeneration().signum()<=0||frame.querySequence().signum()<=0
                ||frame.factsBefore().filter(actual::equals).isEmpty()||frame.owner().isEmpty()||frame.source().filter(s->s.kind()==action.kind()).isEmpty()
                ||!frame.decisionKey().equals(target.decisionKey())||!frame.personalKey().equals(target.personalKey())||!frame.eventRole().equals(target.eventRole())||!frame.instanceId().equals(target.instanceId()))
            throw new IOException("Actual readonly LYD query differs from original complete Source/Core/typed target/private lease");
    }
    static void requireCurrentLydDispatchFrame(CurrentLydResult query,CurrentLydResult dispatched,CurrentLyd.Action action,CurrentLyd.Target target)throws IOException {
        if(action.isQuery()||query.status()!=CurrentLydResult.Status.AVAILABLE||!query.action().isQuery()||query.action().kind()!=action.kind()
                ||dispatched.action()!=action||dispatched.status()!=CurrentLydResult.dispatchedStatus(action)||!dispatched.effectAttempted()||!dispatched.nativeReturned()
                ||!dispatched.cleanupKnown()||dispatched.claimSequence().signum()<=0||!dispatched.providerGeneration().equals(query.providerGeneration())
                ||!dispatched.querySequence().equals(query.querySequence())||!dispatched.factsBefore().equals(query.factsBefore())||!dispatched.source().equals(query.source())
                ||query.source().isEmpty()||query.owner().isEmpty()||dispatched.owner().isEmpty()
                ||!dispatched.decisionKey().equals(target.decisionKey())||!dispatched.personalKey().equals(target.personalKey())
                ||!dispatched.eventRole().equals(target.eventRole())||!dispatched.instanceId().equals(target.instanceId()))
            throw new IOException("Actual LYD dispatch differs from original whole Source/Core/target/private lease; never replay");
        requireCurrentLydOwnerConnection(query.owner().orElseThrow(),dispatched.owner().orElseThrow());
        // Each actual command has its own ticket/pump; custody was verified independently. Toggle bool false stays known dispatch DATA.
    }
    static void requireCurrentLydOwnerConnection(CurrentLetterResult.OwnerWitness query,CurrentLetterResult.OwnerWitness action)throws IOException {
        if(!query.connectionGeneration().equals(action.connectionGeneration()))throw new IOException("LYD action crossed original actual connection");
    }
    private static void requireCurrentLydIntentTarget(LydConfig config,CurrentLydResult query,CurrentLyd.Action action,CurrentLyd.Target target)throws IOException {
        if(config.mode()==LydMode.ADD_PERSONAL) {
            if(action!=CurrentLyd.Action.SELECT_PERSONAL_CANDIDATE&&action!=CurrentLyd.Action.CONFIRM_PERSONAL_ADD)throw new IOException("Only one candidate Select then original same-receiver ADD confirmation");
        }else if(action!=config.mode().action())throw new IOException("Private fixed LYD action differs from explicit mode");
        if(!target.decisionKey().equals(config.decisionKey())||!target.personalKey().equals(config.personalKey())||!target.eventRole().equals(config.eventRole()))throw new IOException("Private LYD target differs from exact DATA intent");
        if(action==CurrentLyd.Action.CHOOSE_KNOWN_EVENT_OPTION) {
            var matches=query.source().orElseThrow().events().orElseThrow().events().stream().filter(e->e.recipientCharacterId()==query.factsBefore().orElseThrow().playedCharacterId()
                    &&e.options().stream().anyMatch(o->o.permittedRole().equals(config.eventRole()))).toList();
            if(matches.size()!=1||target.instanceId().filter(i->i==matches.getFirst().instanceId()).isEmpty()||!target.choiceToken().isEmpty())throw new IOException("Fixed event role must identify exactly one actual census instance; no ordinal fallback");
        }else {
            if(target.instanceId().isPresent())throw new IOException("No caller or unrelated event instance in a non-event action");
            if(action==CurrentLyd.Action.SELECT_PERSONAL_CANDIDATE) {
                var rows=query.source().orElseThrow().personal().orElseThrow().rows().stream().filter(r->r.definitionKey().equals(config.personalKey().orElseThrow().wire())).toList();
                if(rows.size()!=1||!rows.getFirst().selectAdmissible()||rows.getFirst().choiceToken().isEmpty()||!rows.getFirst().choiceToken().equals(target.choiceToken()))throw new IOException("Select must retain the unique actual candidate token; no caller token");
            }else if(!target.choiceToken().isEmpty())throw new IOException("Opaque candidate token belongs only to its actual Select preparation");
        }
    }
    private static NativeGameTransport.CoreReceived readCurrentLydCore(NativeGameTransport transport,GameSupervisorControl.Descriptor owner,NativeLaunchPlan plan,
            Path output,String label,Instant deadline,ObjectNode result,ObjectNode originals,NativeObservationPort.TransportSession expectedSession,CoreFrame.Prefix expectedPrefix)throws IOException,InterruptedException {
        stage="FRESH_ACTUAL_CORE_BEFORE_LYD";result.put("read_calls",result.path("read_calls").intValue()+1);
        var read=transport.readCoreFrameReceived(deadline);archiveCurrentLetterOutcome(transport,Files.createDirectory(output.resolve(label)),label,read.original(),originals);
        if(!(read instanceof NativeGameTransport.CoreReceived before)||!(before.frame() instanceof CoreFrame.Partial core))throw new IOException("Actual LYD Core unavailable; no replacement, retry or effect");
        requireCurrentDjcAckOwner(transport,owner,before.original(),expectedSession);var p=core.prefix();
        if(core.build()!=ExactCk3Build.CK3_121003_STEAM_26785313||!core.build().executableSha256().equalsIgnoreCase(plan.sources().review().gameExecutable().sha256())
                ||!core.build().coreFrameAdapterId().equals(plan.adapterId())||!p.paused()||!p.mapReady()||!p.hasPlayedCharacter()||!p.playedCharacterAlive()||p.playedCharacterId()==-1||p.localPlayerId()<0||p.speed()<1||p.speed()>5
                ||expectedPrefix!=null&&!expectedPrefix.equals(p))throw new IOException("Exact paused living same-owner LYD Core required; ADD retains the original prefix");
        Instant until=before.validUntil().isBefore(deadline)?before.validUntil():deadline;before.requireOriginal(transport,until);return before;
    }
    private static CurrentLydResult archiveCurrentLydQuery(NativeGameTransport transport,GameSupervisorControl.Descriptor owner,NativeGameTransport.LydRead read,
            NativeGameTransport.CoreReceived before,CurrentLyd.Action action,CurrentLyd.Target target,NativeObservationPort.TransportSession actualSession,
            Path output,String label,Instant deadline,ObjectNode result,ObjectNode originals)throws IOException {
        Path queryOutput=Files.createDirectory(output.resolve(label));archiveCurrentLetterOutcome(transport,queryOutput,label,read.original(),originals);
        if(!(read instanceof NativeGameTransport.LydReceived query))throw new IOException("Actual LYD query refused or UNKNOWN; stop without action/retry");
        if(query.queryAction()!=action||!query.target().equals(target)||query.validUntil().isAfter(deadline))throw new IOException("Private LYD query escaped fixed target or original deadline");
        query.requireOriginal(transport,query.validUntil());var ack=query.original();requireCurrentDjcAckOwner(transport,owner,ack,actualSession);
        var frame=CurrentLydResult.decodeOutcome(ack);if(!frame.equals(query.frame()))throw new IOException("This LYD ACK differs from the actual private query");
        requireCurrentLydQueryFrame(frame,((CoreFrame.Partial)before.frame()).prefix(),action,target);
        if(!frame.owner().orElseThrow().connectionGeneration().equals(actualSession.connectionGeneration()))throw new IOException("LYD query crossed original connection");
        originals.set(label+"_original_result",write(queryOutput,"original-result.json",ack.originalResultToken().orElseThrow().bytes()));
        result.set(label,FullJsonTree.parse(frame.encode().bytes(),SMALL));return frame;
    }
    private static CurrentLydResult dispatchCurrentLydOnce(NativeGameTransport transport,GameSupervisorControl.Descriptor owner,NativeGameTransport.LydReceived query,
            NativeGameTransport.LydPrepared prepared,LydConfig config,NativeObservationPort.TransportSession actualSession,Path output,String label,
            Instant deadline,ObjectNode result,ObjectNode originals)throws IOException,InterruptedException {
        requireCurrentLydIntentTarget(config,query.frame(),prepared.action(),prepared.target());
        if(!prepared.deadline().equals(query.validUntil())||prepared.deadline().isAfter(deadline))throw new IOException("Original LYD prepared deadline changed");
        Path actionOutput=Files.createDirectory(output.resolve(label));
        var intent=StrictJson.object().put("schema","xar.current-lyd-original-intent/v1").put("request_id",prepared.requestId()).put("action",prepared.action().wire())
                .put("original_query_request_id",query.original().requestId()).put("original_deadline_utc",prepared.deadline().toString())
                .put("event_closed",false).put("personal_applied",false).put("gold_paid",false).put("piety_paid",false).put("modifiers_applied",false).put("new_date_observed",false).put("physical_save_confirmed",false);
        intent.set("actual_query_source",FullJsonTree.parse(query.frame().encode().bytes(),SMALL));
        if(prepared.target().decisionKey().isPresent())intent.put("decision_key",prepared.target().decisionKey().orElseThrow().wire());else intent.putNull("decision_key");
        if(prepared.target().personalKey().isPresent())intent.put("personal_key",prepared.target().personalKey().orElseThrow().wire());else intent.putNull("personal_key");
        if(prepared.target().eventRole().isPresent())intent.put("event_role",prepared.target().eventRole().orElseThrow().wire());else intent.putNull("event_role");
        if(prepared.target().instanceId().isPresent())intent.put("actual_instance_id",prepared.target().instanceId().orElseThrow());else intent.putNull("actual_instance_id");
        intent.put("actual_choice_token",prepared.target().choiceToken());intent.set("original_outbound",write(actionOutput,"original-request.packet",prepared.originalPacket().value()));
        originals.set(label+"_intent",write(actionOutput,"original-intent.json",FullJsonTree.encode(intent,SMALL)));
        stage="ONE_PRIVATE_FIXED_LYD_ACTION";result.put("action_calls",result.path("action_calls").intValue()+1);
        if(prepared.action()==CurrentLyd.Action.SELECT_PERSONAL_CANDIDATE)result.put("select_calls",1);
        if(prepared.action()==CurrentLyd.Action.CONFIRM_PERSONAL_ADD)result.put("confirm_calls",1);
        var outcome=transport.submitCurrentLyd(prepared);archiveCurrentLetterOutcome(transport,actionOutput,label,outcome,originals);
        if(!(outcome instanceof NativeActionPort.AckReceived ack))throw new IOException("Original LYD action refused or UNKNOWN; never replay Select/Confirm/Toggle");
        requireCurrentDjcAckOwner(transport,owner,ack,actualSession);var dispatched=CurrentLydResult.decodeOutcome(ack);
        originals.set(label+"_original_result",write(actionOutput,"original-result.json",ack.originalResultToken().orElseThrow().bytes()));
        if(prepared.latestFrame().filter(dispatched::equals).isEmpty())throw new IOException("This LYD ACK was not qualified by the private original preparation");
        requireCurrentLydDispatchFrame(query.frame(),dispatched,prepared.action(),prepared.target());
        if(!dispatched.owner().orElseThrow().connectionGeneration().equals(actualSession.connectionGeneration()))throw new IOException("LYD action crossed original connection");
        result.set(label,FullJsonTree.parse(dispatched.encode().bytes(),SMALL));result.put("native_returned",dispatched.nativeReturned()).put("native_handled",dispatched.nativeHandled()).put("native_status",dispatched.status().wire());
        return dispatched;
    }
    private static void runCurrentLyd(NativeGameTransport transport,GameSupervisorControl.Descriptor owner,NativeLaunchPlan plan,LydConfig config,
            Path output,Instant deadline,ObjectNode result,ObjectNode originals)throws IOException,InterruptedException {
        try {
            if(!(plan.load() instanceof NativeLaunchPlan.SavedGame))throw new IOException("LYD requires its actual SavedGame owner");
            var before=readCurrentLydCore(transport,owner,plan,output,"core-before-lyd",deadline,result,originals,null,null);
            var actualSession=before.original().custody().orElseThrow().session();var prefix=((CoreFrame.Partial)before.frame()).prefix();
            Instant until=before.validUntil().isBefore(deadline)?before.validUntil():deadline;
            stage="ONE_READONLY_LYD_QUERY";result.put("read_calls",2);
            var read=transport.readCurrentLyd(before,config.mode().queryAction(),config.queryTarget(),until);
            archiveCurrentLydQuery(transport,owner,read,before,config.mode().queryAction(),config.queryTarget(),actualSession,output,"lyd-query",until,result,originals);
            var query=(NativeGameTransport.LydReceived)read;result.put("query_available",true).put("query_request_id",query.original().requestId());result.set("session",session(actualSession));
            if(config.mode().action().isQuery())return;
            NativeGameTransport.LydPrepared prepared=switch(config.mode()) {
                case OPEN_DETAIL,CONFIRM_DECISION->transport.prepareCurrentLydDecision(query,config.mode().action(),config.decisionKey().orElseThrow());
                case CHOOSE_KNOWN_EVENT_OPTION->transport.prepareCurrentLydEvent(query,config.eventRole().orElseThrow());
                case ADD_PERSONAL->transport.prepareCurrentLydCandidate(query,config.personalKey().orElseThrow());
                case OPEN_LIST,OPEN_PERSONAL,START_ADD_PERSONAL->transport.prepareCurrentLyd(query,config.mode().action());
                default->throw new IOException("Readonly LYD modes have no write authority");
            };
            dispatchCurrentLydOnce(transport,owner,query,prepared,config,actualSession,output,config.mode()==LydMode.ADD_PERSONAL?"one-lyd-candidate-select":"one-lyd-action",deadline,result,originals);
            if(config.mode()==LydMode.ADD_PERSONAL) {
                // The actual Select object and its original deadline stay inside this receiver. No standalone ADD query or cross-Main recovery.
                var fresh=readCurrentLydCore(transport,owner,plan,output,"core-after-lyd-select",prepared.deadline(),result,originals,actualSession,prefix);
                stage="ONE_LYD_ADD_QUERY_AFTER_ACTUAL_SELECT";result.put("read_calls",result.path("read_calls").intValue()+1);
                var addRead=transport.readCurrentLydAddConfirmation(fresh,prepared);var addTarget=CurrentLyd.Target.personal(config.personalKey().orElseThrow());
                archiveCurrentLydQuery(transport,owner,addRead,fresh,CurrentLyd.Action.QUERY_ADD_CONFIRMATION,addTarget,actualSession,output,"lyd-add-query",prepared.deadline(),result,originals);
                var addQuery=(NativeGameTransport.LydReceived)addRead;
                if(!addQuery.validUntil().equals(prepared.deadline()))throw new IOException("Original Select deadline cannot be extended by a fresh ADD Core/query");
                result.put("add_query_available",true);var add=transport.prepareCurrentLydPersonalAdd(addQuery,prepared);
                if(add.action()!=CurrentLyd.Action.CONFIRM_PERSONAL_ADD)throw new IOException("Only the original same-receiver ADD confirmation is permitted after Select");
                dispatchCurrentLydOnce(transport,owner,addQuery,add,config,actualSession,output,"one-lyd-personal-add-confirmation",prepared.deadline(),result,originals);
            }
            result.put("callback_dispatched",true);
        } finally {
            archiveNaturalDiagnostics(output,originals,transport.diagnostics());var progress=result.deepCopy();progress.set("originals",originals.deepCopy());write(output,"current-lyd-progress.json",FullJsonTree.encode(progress,FullJsonTree.MAXIMUM_BYTES));
        }
    }

    private static void runCurrentSupermanSavedBaseline(NativeGameTransport transport,GameSupervisorControl.Descriptor owner,NativeLaunchPlan plan,
            ObjectNode config,ExactRef baselineProgress,Path output,Instant deadline,ObjectNode result,ObjectNode originals)throws IOException,InterruptedException {
        FileWitness baselineSource=null,baselineArchive=null;
        try {
            if(!(plan.load() instanceof NativeLaunchPlan.SavedGame))throw new IOException("Current health fixture requires the actual SavedGame owner");
            byte[] progressBytes=readExact(baselineProgress,SMALL);
            var progressNode=FullJsonTree.parse(progressBytes,SMALL);
            if(!(progressNode instanceof ObjectNode prior)||!(prior.get("baseline_checkpoint") instanceof ObjectNode checkpoint))throw new IOException("Actual original baseline checkpoint progress object required");
            baselineSource=ControlBuild.strictMapper().treeToValue(checkpoint.get("checkpoint_source"),FileWitness.class);
            baselineArchive=ControlBuild.strictMapper().treeToValue(checkpoint.get("checkpoint_immutable_archive"),FileWitness.class);
            originals.set("restored_baseline_progress_original",write(output,"restored-baseline-progress-original.json",progressBytes));
            stage="RESTORE_ORIGINAL_PHYSICAL_BASELINE_BEFORE_FRESH_CORE";
            transport.restoreCurrentSupermanHealthBaseline(baselineProgress,ExactRef.fromJson(config.get("owner_descriptor")),baselineSource,baselineArchive);
            result.set("baseline_checkpoint",checkpoint.deepCopy());result.put("save_calls",0).put("baseline_physical_material_observed",true).put("baseline_source_restored_from_progress",true);
            result.set("restored_baseline_progress",baselineProgress.toJson());
            int precedingReads=0;
            var health=new SupermanHealthConfig(SupermanHealthMode.BASELINE_SAVE_AND_BEGIN,CurrentSupermanHealth.Phase.BASELINE);
            stage="FRESH_ACTUAL_CORE_BEFORE_SUPERMAN_HEALTH_QUERY";result.put("read_calls",precedingReads+1);
            var coreRead=transport.readCoreFrameReceived(deadline);Path coreOutput=Files.createDirectory(output.resolve("core-before-superman-health"));
            archiveCurrentLetterOutcome(transport,coreOutput,"core",coreRead.original(),originals);
            if(!(coreRead instanceof NativeGameTransport.CoreReceived before)||!(before.frame() instanceof CoreFrame.Partial core))throw new IOException("Actual health Core unavailable; no configured replacement or reply");
            requireCurrentDjcAckOwner(transport,owner,before.original(),null);var actualSession=before.original().custody().orElseThrow().session();var p=core.prefix();
            if(core.build()!=ExactCk3Build.CK3_121003_STEAM_26785313||!core.build().executableSha256().equalsIgnoreCase(plan.sources().review().gameExecutable().sha256())
                    ||!core.build().coreFrameAdapterId().equals(plan.adapterId())||!p.paused()||!p.mapReady()||!p.hasPlayedCharacter()||!p.playedCharacterAlive()||p.playedCharacterId()==-1||p.localPlayerId()<0||p.speed()<1||p.speed()>5)
                throw new IOException("Exact current paused living actual health Core required");
            if(health.mode()==SupermanHealthMode.BASELINE_SAVE_AND_BEGIN&&p.dateRaw()!=StrictJson.integer(result.get("baseline_checkpoint").get("source_date_raw"),Integer.MIN_VALUE,Integer.MAX_VALUE))
                throw new IOException("Fresh baseline query date differs from this actual Save source");
            Instant until=before.validUntil().isBefore(deadline)?before.validUntil():deadline;before.requireOriginal(transport,until);
            stage="ONE_READONLY_SUPERMAN_HEALTH_QUERY";result.put("read_calls",precedingReads+2);
            var read=transport.readCurrentSupermanHealth(before,health.phase(),until);Path queryOutput=Files.createDirectory(output.resolve("superman-health-query"));
            archiveCurrentLetterOutcome(transport,queryOutput,"superman_health_query",read.original(),originals);
            if(!(read instanceof NativeGameTransport.SupermanHealthReceived query))throw new IOException("Actual health source unavailable or UNKNOWN; no known option/retry");
            until=query.validUntil().isBefore(until)?query.validUntil():until;query.requireOriginal(transport,until);
            if(query.phase()!=health.phase())throw new IOException("Private query changed the original phase");
            var queryAck=query.original();requireCurrentDjcAckOwner(transport,owner,queryAck,actualSession);var frame=CurrentSupermanHealthResult.decodeOutcome(queryAck);
            if(!frame.equals(query.frame()))throw new IOException("This actual health query ACK differs from the private retained frame");
            requireCurrentSupermanHealthQueryFrame(frame,p,health.phase());
            if(!frame.owner().orElseThrow().connectionGeneration().equals(actualSession.connectionGeneration()))throw new IOException("Health query crossed original connection");
            originals.set("superman_health_query_original_result",write(queryOutput,"original-result.json",queryAck.originalResultToken().orElseThrow().bytes()));
            result.set("query",FullJsonTree.parse(frame.encode().bytes(),SMALL));result.set("session",session(actualSession));result.put("query_available",true).put("query_request_id",queryAck.requestId());
            var actualSource=requireCurrentSupermanHealthChoiceSource(frame,health.phase());
            NativeGameTransport.SupermanHealthPrepared prepared;
            prepared=transport.prepareCurrentSupermanHealthBegin(query,baselineSource,baselineArchive);
            if(prepared.action()!=CurrentSupermanHealth.Action.CHOOSE_KNOWN||prepared.phase()!=health.phase()||!prepared.selected().equals(actualSource))throw new IOException("Private fixed health preparation changed phase or complete actual source");
            if(!prepared.deadline().equals(query.validUntil())||prepared.deadline().isAfter(deadline))throw new IOException("Original fixed health choice deadline changed");
            Path choiceOutput=Files.createDirectory(output.resolve("one-superman-health-known-choice"));
            var intent=StrictJson.object().put("schema","xar.current-superman-health-original-intent/v1").put("request_id",prepared.requestId()).put("phase",prepared.phase().wire())
                    .put("mode",StrictJson.text(config.get("mode"))).put("original_query_request_id",queryAck.requestId()).put("original_deadline_utc",prepared.deadline().toString())
                    .put("event_closed",false).put("health_changed",false).put("trait_UI_rendered",false).put("new_date_observed",false).put("physical_save_confirmed",false);
            intent.set("original_query_source",originals.get("superman_health_query_original_result").deepCopy());
            if(baselineSource!=null) {intent.set("actual_baseline_source",ControlBuild.strictMapper().valueToTree(baselineSource));intent.set("actual_baseline_archive",ControlBuild.strictMapper().valueToTree(baselineArchive));}
            intent.set("original_outbound",write(choiceOutput,"original-request.packet",prepared.originalPacket().value()));
            originals.set("superman_health_choice_intent",write(choiceOutput,"original-intent.json",FullJsonTree.encode(intent,SMALL)));
            stage="ONE_PRIVATE_FIXED_SUPERMAN_HEALTH_CHOICE";result.put("choose_calls",1);
            var outcome=transport.submitCurrentSupermanHealthChoose(prepared);archiveCurrentLetterOutcome(transport,choiceOutput,"superman_health_choice",outcome,originals);
            if(!(outcome instanceof NativeActionPort.AckReceived ack))throw new IOException("Original health choice UNKNOWN or refused; never replay");
            requireCurrentDjcAckOwner(transport,owner,ack,actualSession);var dispatched=CurrentSupermanHealthResult.decodeOutcome(ack);
            originals.set("superman_health_choice_original_result",write(choiceOutput,"original-result.json",ack.originalResultToken().orElseThrow().bytes()));
            if(prepared.latestFrame().filter(dispatched::equals).isEmpty())throw new IOException("This original health choice ACK was not qualified by its private preparation");
            requireCurrentSupermanHealthDispatchFrame(frame,dispatched,health.phase());
            if(!dispatched.owner().orElseThrow().connectionGeneration().equals(actualSession.connectionGeneration()))throw new IOException("Fixed health choice crossed original connection");
            result.set("choose_result",FullJsonTree.parse(dispatched.encode().bytes(),SMALL));result.put("choose_request_id",ack.requestId()).put("known_choice_dispatched",true)
                    .put("native_returned",dispatched.nativeReturned()).put("native_handled",false).put("native_status",dispatched.status().wire());
        } finally {
            archiveNaturalDiagnostics(output,originals,transport.diagnostics());var progress=result.deepCopy();progress.set("originals",originals.deepCopy());write(output,"current-superman-health-resume-progress.json",FullJsonTree.encode(progress,FullJsonTree.MAXIMUM_BYTES));
        }
    }

    enum SupermanHealthMode { QUERY,BASELINE_SAVE_AND_BEGIN,COMPLETED_CLOSE }
    record SupermanHealthConfig(SupermanHealthMode mode,CurrentSupermanHealth.Phase phase) {
        SupermanHealthConfig {
            Objects.requireNonNull(mode);Objects.requireNonNull(phase);
            StrictJson.require(mode==SupermanHealthMode.QUERY||mode==SupermanHealthMode.BASELINE_SAVE_AND_BEGIN&&phase==CurrentSupermanHealth.Phase.BASELINE
                    ||mode==SupermanHealthMode.COMPLETED_CLOSE&&phase==CurrentSupermanHealth.Phase.COMPLETED,"Fixed baseline/completed roles differ");
        }
    }
    static SupermanHealthConfig currentSupermanHealthConfig(ObjectNode config) {
        StrictJson.require(StrictJson.text(config.get("schema")).equals("xar.native-owner-snapshot-config/v35"),"Explicit v35 Superman workflow required");
        var mode=switch(StrictJson.text(config.get("mode"))) {
            case "current_superman_health_query"->SupermanHealthMode.QUERY;
            case "current_superman_health_baseline_save_and_begin"->SupermanHealthMode.BASELINE_SAVE_AND_BEGIN;
            case "current_superman_health_completed_close"->SupermanHealthMode.COMPLETED_CLOSE;
            default->throw new IllegalArgumentException("Only readonly phase query, actual baseline Save then begin, or one completed close");
        };
        var fields=new java.util.HashSet<>(Set.of("schema","mode","owner_descriptor","overall_timeout_seconds","read_timeout_seconds","maximum_frames_per_operation"));
        if(mode==SupermanHealthMode.QUERY)fields.add("phase");
        if(mode==SupermanHealthMode.BASELINE_SAVE_AND_BEGIN) {
            fields.addAll(Set.of("checkpoint_archive_path","maximum_checkpoint_bytes","checkpoint_observation_attempts","checkpoint_poll_interval_ms"));
            StrictJson.require(config.has("previous_checkpoint_source")==config.has("previous_checkpoint_archive"),"Previous actual checkpoint source/archive must be paired");
            if(config.has("previous_checkpoint_source")) {
                fields.addAll(Set.of("previous_checkpoint_source","previous_checkpoint_archive"));
                StrictJson.require(config.get("previous_checkpoint_source").isObject()&&config.get("previous_checkpoint_archive").isObject(),"Actual previous FileWitness objects required; no scalar/null permission");
            }
        }
        StrictJson.object(config,Set.copyOf(fields));ExactRef.fromJson(config.get("owner_descriptor"));
        StrictJson.integer(config.get("overall_timeout_seconds"),1,600);StrictJson.integer(config.get("read_timeout_seconds"),1,60);
        StrictJson.integer(config.get("maximum_frames_per_operation"),1,65536);
        CurrentSupermanHealth.Phase phase=mode==SupermanHealthMode.COMPLETED_CLOSE?CurrentSupermanHealth.Phase.COMPLETED:CurrentSupermanHealth.Phase.BASELINE;
        if(mode==SupermanHealthMode.QUERY)phase=switch(StrictJson.text(config.get("phase"))) {
            case "baseline"->CurrentSupermanHealth.Phase.BASELINE;
            case "completed"->CurrentSupermanHealth.Phase.COMPLETED;
            default->throw new IllegalArgumentException("Only fixed baseline or completed phase DATA");
        };
        if(mode==SupermanHealthMode.BASELINE_SAVE_AND_BEGIN) {
            StrictJson.require(Path.of(StrictJson.text(config.get("checkpoint_archive_path"))).isAbsolute(),"New absolute immutable baseline archive required");
            StrictJson.integer(config.get("maximum_checkpoint_bytes"),1,1L<<30);
            StrictJson.integer(config.get("checkpoint_observation_attempts"),1,64);StrictJson.integer(config.get("checkpoint_poll_interval_ms"),100,5000);
        }
        return new SupermanHealthConfig(mode,phase);
    }
    /** Physical comparison DATA only. The Transport begin factory separately verifies this actual Save receipt and both files. */
    static void requireSupermanBaselineMaterial(FileWitness source,FileWitness archive,Path checkpoint,Path destination,long maximumBytes)throws IOException {
        Objects.requireNonNull(source);Objects.requireNonNull(archive);Objects.requireNonNull(checkpoint);Objects.requireNonNull(destination);
        if(!checkpoint.isAbsolute()||!destination.isAbsolute()||checkpoint.normalize().equals(destination.normalize())||maximumBytes<1
                ||!Path.of(source.reference().path()).toAbsolutePath().normalize().equals(checkpoint.normalize())
                ||!Path.of(archive.reference().path()).toAbsolutePath().normalize().equals(destination.normalize())
                ||source.reference().bytes()<=0||source.reference().bytes()>maximumBytes
                ||source.reference().bytes()!=archive.reference().bytes()||!source.reference().sha256().equals(archive.reference().sha256())
                ||source.identity().fileId().equals(archive.identity().fileId()))
            throw new IOException("Original changed checkpoint and independent immutable archive must have exact bounded matching bytes/SHA and distinct physical identities");
    }
    static void requireCurrentSupermanHealthQueryFrame(CurrentSupermanHealthResult frame,CoreFrame.Prefix actual,CurrentSupermanHealth.Phase phase)throws IOException {
        if(frame.action()!=CurrentSupermanHealth.Action.QUERY_HEALTH||frame.phase()!=phase||frame.status()!=CurrentSupermanHealthResult.Status.AVAILABLE
                ||frame.effectAttempted()||frame.nativeReturned()||!frame.cleanupKnown()||frame.claimSequence().signum()!=0
                ||frame.providerGeneration().signum()<=0||frame.querySequence().signum()<=0||frame.owner().isEmpty()
                ||frame.factsBefore().filter(actual::equals).isEmpty()||frame.source().filter(s->s.phase()==phase).isEmpty())
            throw new IOException("Actual fixed health query differs from original complete source/Core/phase/private lease");
    }
    /** Readonly public DATA guard; only the actual Transport factories can authorize either known option. */
    static CurrentSupermanHealthSource requireCurrentSupermanHealthChoiceSource(CurrentSupermanHealthResult query,CurrentSupermanHealth.Phase phase)throws IOException {
        requireCurrentSupermanHealthQueryFrame(query,query.factsBefore().orElseThrow(()->new IOException("Actual health Core absent")),phase);
        var source=query.source().orElseThrow();
        if(!source.nativeChoiceAdmissible())throw new IOException("Actual complete health source does not admit its one fixed option");
        return source;
    }
    static void requireCurrentSupermanHealthDispatchFrame(CurrentSupermanHealthResult query,CurrentSupermanHealthResult dispatched,CurrentSupermanHealth.Phase phase)throws IOException {
        requireCurrentSupermanHealthChoiceSource(query,phase);
        if(dispatched.action()!=CurrentSupermanHealth.Action.CHOOSE_KNOWN||dispatched.phase()!=phase||dispatched.status()!=CurrentSupermanHealthResult.Status.KNOWN_CHOICE_DISPATCHED
                ||!dispatched.effectAttempted()||!dispatched.nativeReturned()||!dispatched.cleanupKnown()||dispatched.claimSequence().signum()<=0
                ||!dispatched.providerGeneration().equals(query.providerGeneration())||!dispatched.querySequence().equals(query.querySequence())
                ||!dispatched.factsBefore().equals(query.factsBefore())||!dispatched.source().equals(query.source())||dispatched.owner().isEmpty()
                ||!dispatched.owner().orElseThrow().connectionGeneration().equals(query.owner().orElseThrow().connectionGeneration()))
            throw new IOException("Fixed health reply differs from full original phase/source/Core/owner/private lease");
    }
    private static void runCurrentSupermanHealth(NativeGameTransport transport,GameSupervisorControl.Descriptor owner,NativeLaunchPlan plan,
            ObjectNode config,SupermanHealthConfig health,Path output,Instant deadline,ObjectNode result,ObjectNode originals)throws IOException,InterruptedException {
        FileWitness baselineSource=null,baselineArchive=null;
        try {
            if(!(plan.load() instanceof NativeLaunchPlan.SavedGame))throw new IOException("Current health fixture requires the actual SavedGame owner");
            if(health.mode()==SupermanHealthMode.BASELINE_SAVE_AND_BEGIN) {
                Path checkpointOutput=Files.createDirectory(output.resolve("baseline-checkpoint"));var checkpoint=StrictJson.object();var checkpointOriginals=StrictJson.object();
                result.set("baseline_checkpoint",checkpoint);originals.set("baseline_checkpoint",checkpointOriginals);
                // The existing v14 implementation remains byte-for-byte intact. An exception at
                // preflight/Save/physical observation/archive prevents all following operations.
                try {runCoreCheckpoint(transport,owner,plan,config,checkpointOutput,deadline,checkpoint,checkpointOriginals);}
                finally {result.put("save_calls",checkpoint.path("save_calls").asInt(0));}
                baselineSource=ControlBuild.strictMapper().treeToValue(checkpoint.get("checkpoint_source"),FileWitness.class);
                baselineArchive=ControlBuild.strictMapper().treeToValue(checkpoint.get("checkpoint_immutable_archive"),FileWitness.class);
                requireSupermanBaselineMaterial(baselineSource,baselineArchive,plan.profileDirectory().resolve("save games").resolve(CurrentCoreCheckpointSave.FILENAME),
                        Path.of(StrictJson.text(config.get("checkpoint_archive_path"))).toAbsolutePath().normalize(),StrictJson.integer(config.get("maximum_checkpoint_bytes"),1,1L<<30));
                if(!checkpoint.path("changed_physical_material_observed").asBoolean(false)||!checkpoint.path("archive_is_copy_not_another_SAVE").asBoolean(false))throw new IOException("Actual baseline changed physical material and immutable copy missing");
                result.put("baseline_physical_material_observed",true).put("read_calls",1);
            }
            int precedingReads=health.mode()==SupermanHealthMode.BASELINE_SAVE_AND_BEGIN?1:0;
            stage="FRESH_ACTUAL_CORE_BEFORE_SUPERMAN_HEALTH_QUERY";result.put("read_calls",precedingReads+1);
            var coreRead=transport.readCoreFrameReceived(deadline);Path coreOutput=Files.createDirectory(output.resolve("core-before-superman-health"));
            archiveCurrentLetterOutcome(transport,coreOutput,"core",coreRead.original(),originals);
            if(!(coreRead instanceof NativeGameTransport.CoreReceived before)||!(before.frame() instanceof CoreFrame.Partial core))throw new IOException("Actual health Core unavailable; no configured replacement or reply");
            requireCurrentDjcAckOwner(transport,owner,before.original(),null);var actualSession=before.original().custody().orElseThrow().session();var p=core.prefix();
            if(core.build()!=ExactCk3Build.CK3_121003_STEAM_26785313||!core.build().executableSha256().equalsIgnoreCase(plan.sources().review().gameExecutable().sha256())
                    ||!core.build().coreFrameAdapterId().equals(plan.adapterId())||!p.paused()||!p.mapReady()||!p.hasPlayedCharacter()||!p.playedCharacterAlive()||p.playedCharacterId()==-1||p.localPlayerId()<0||p.speed()<1||p.speed()>5)
                throw new IOException("Exact current paused living actual health Core required");
            if(health.mode()==SupermanHealthMode.BASELINE_SAVE_AND_BEGIN&&p.dateRaw()!=StrictJson.integer(result.get("baseline_checkpoint").get("source_date_raw"),Integer.MIN_VALUE,Integer.MAX_VALUE))
                throw new IOException("Fresh baseline query date differs from this actual Save source");
            Instant until=before.validUntil().isBefore(deadline)?before.validUntil():deadline;before.requireOriginal(transport,until);
            stage="ONE_READONLY_SUPERMAN_HEALTH_QUERY";result.put("read_calls",precedingReads+2);
            var read=transport.readCurrentSupermanHealth(before,health.phase(),until);Path queryOutput=Files.createDirectory(output.resolve("superman-health-query"));
            archiveCurrentLetterOutcome(transport,queryOutput,"superman_health_query",read.original(),originals);
            if(!(read instanceof NativeGameTransport.SupermanHealthReceived query))throw new IOException("Actual health source unavailable or UNKNOWN; no known option/retry");
            until=query.validUntil().isBefore(until)?query.validUntil():until;query.requireOriginal(transport,until);
            if(query.phase()!=health.phase())throw new IOException("Private query changed the original phase");
            var queryAck=query.original();requireCurrentDjcAckOwner(transport,owner,queryAck,actualSession);var frame=CurrentSupermanHealthResult.decodeOutcome(queryAck);
            if(!frame.equals(query.frame()))throw new IOException("This actual health query ACK differs from the private retained frame");
            requireCurrentSupermanHealthQueryFrame(frame,p,health.phase());
            if(!frame.owner().orElseThrow().connectionGeneration().equals(actualSession.connectionGeneration()))throw new IOException("Health query crossed original connection");
            originals.set("superman_health_query_original_result",write(queryOutput,"original-result.json",queryAck.originalResultToken().orElseThrow().bytes()));
            result.set("query",FullJsonTree.parse(frame.encode().bytes(),SMALL));result.set("session",session(actualSession));result.put("query_available",true).put("query_request_id",queryAck.requestId());
            if(health.mode()==SupermanHealthMode.QUERY)return;
            var actualSource=requireCurrentSupermanHealthChoiceSource(frame,health.phase());
            NativeGameTransport.SupermanHealthPrepared prepared;
            if(health.mode()==SupermanHealthMode.BASELINE_SAVE_AND_BEGIN) {
                if(baselineSource==null||baselineArchive==null)throw new IOException("This invocation has no completed physical baseline material");
                prepared=transport.prepareCurrentSupermanHealthBegin(query,baselineSource,baselineArchive);
            } else prepared=transport.prepareCurrentSupermanHealthChoose(query);
            if(prepared.action()!=CurrentSupermanHealth.Action.CHOOSE_KNOWN||prepared.phase()!=health.phase()||!prepared.selected().equals(actualSource))throw new IOException("Private fixed health preparation changed phase or complete actual source");
            if(!prepared.deadline().equals(query.validUntil())||prepared.deadline().isAfter(deadline))throw new IOException("Original fixed health choice deadline changed");
            Path choiceOutput=Files.createDirectory(output.resolve("one-superman-health-known-choice"));
            var intent=StrictJson.object().put("schema","xar.current-superman-health-original-intent/v1").put("request_id",prepared.requestId()).put("phase",prepared.phase().wire())
                    .put("mode",StrictJson.text(config.get("mode"))).put("original_query_request_id",queryAck.requestId()).put("original_deadline_utc",prepared.deadline().toString())
                    .put("event_closed",false).put("health_changed",false).put("trait_UI_rendered",false).put("new_date_observed",false).put("physical_save_confirmed",false);
            intent.set("original_query_source",originals.get("superman_health_query_original_result").deepCopy());
            if(baselineSource!=null) {intent.set("actual_baseline_source",ControlBuild.strictMapper().valueToTree(baselineSource));intent.set("actual_baseline_archive",ControlBuild.strictMapper().valueToTree(baselineArchive));}
            intent.set("original_outbound",write(choiceOutput,"original-request.packet",prepared.originalPacket().value()));
            originals.set("superman_health_choice_intent",write(choiceOutput,"original-intent.json",FullJsonTree.encode(intent,SMALL)));
            stage="ONE_PRIVATE_FIXED_SUPERMAN_HEALTH_CHOICE";result.put("choose_calls",1);
            var outcome=transport.submitCurrentSupermanHealthChoose(prepared);archiveCurrentLetterOutcome(transport,choiceOutput,"superman_health_choice",outcome,originals);
            if(!(outcome instanceof NativeActionPort.AckReceived ack))throw new IOException("Original health choice UNKNOWN or refused; never replay");
            requireCurrentDjcAckOwner(transport,owner,ack,actualSession);var dispatched=CurrentSupermanHealthResult.decodeOutcome(ack);
            originals.set("superman_health_choice_original_result",write(choiceOutput,"original-result.json",ack.originalResultToken().orElseThrow().bytes()));
            if(prepared.latestFrame().filter(dispatched::equals).isEmpty())throw new IOException("This original health choice ACK was not qualified by its private preparation");
            requireCurrentSupermanHealthDispatchFrame(frame,dispatched,health.phase());
            if(!dispatched.owner().orElseThrow().connectionGeneration().equals(actualSession.connectionGeneration()))throw new IOException("Fixed health choice crossed original connection");
            result.set("choose_result",FullJsonTree.parse(dispatched.encode().bytes(),SMALL));result.put("choose_request_id",ack.requestId()).put("known_choice_dispatched",true)
                    .put("native_returned",dispatched.nativeReturned()).put("native_handled",false).put("native_status",dispatched.status().wire());
        } finally {
            archiveNaturalDiagnostics(output,originals,transport.diagnostics());var progress=result.deepCopy();progress.set("originals",originals.deepCopy());write(output,"current-superman-health-progress.json",FullJsonTree.encode(progress,FullJsonTree.MAXIMUM_BYTES));
        }
    }

    record CourtierChoicesConfig(CurrentCourtierChoices.Action action,CurrentCourtierControls.Product product,CurrentCourtierChoices.Catalog catalog,java.util.Optional<String> choiceKey) {
        CourtierChoicesConfig {
            Objects.requireNonNull(action);Objects.requireNonNull(product);Objects.requireNonNull(catalog);Objects.requireNonNull(choiceKey);
            StrictJson.require(action==CurrentCourtierChoices.Action.QUERY_CHOICES?choiceKey.isEmpty():choiceKey.isPresent(),"Exact query/select key roles differ");
            choiceKey=choiceKey.map(CurrentCourtierChoices::exactKey);
        }
    }
    static CourtierChoicesConfig currentCourtierChoicesConfig(ObjectNode config) {
        StrictJson.require(StrictJson.text(config.get("schema")).equals("xar.native-owner-snapshot-config/v34"),"Explicit v34 fixed catalogue mode required");
        var action=switch(StrictJson.text(config.get("mode"))) {
            case "current_courtier_choices_query"->CurrentCourtierChoices.Action.QUERY_CHOICES;
            case "current_courtier_choice_select"->CurrentCourtierChoices.Action.SELECT_CHOICE;
            default->throw new IllegalArgumentException("Only independent catalogue query or one original private choice; no automatic open or chain");
        };
        var fields=new java.util.HashSet<>(Set.of("schema","mode","owner_descriptor","overall_timeout_seconds","read_timeout_seconds","maximum_frames_per_operation","product","catalog"));
        if(action==CurrentCourtierChoices.Action.SELECT_CHOICE)fields.add("choice_key");StrictJson.object(config,Set.copyOf(fields));
        ExactRef.fromJson(config.get("owner_descriptor"));StrictJson.integer(config.get("overall_timeout_seconds"),1,600);
        StrictJson.integer(config.get("read_timeout_seconds"),1,60);StrictJson.integer(config.get("maximum_frames_per_operation"),1,65536);
        java.util.Optional<String> key=action==CurrentCourtierChoices.Action.SELECT_CHOICE?java.util.Optional.of(CurrentCourtierChoices.exactKey(StrictJson.text(config.get("choice_key")))):java.util.Optional.empty();
        try{return new CourtierChoicesConfig(action,CurrentCourtierControls.Product.parse(StrictJson.text(config.get("product"))),CurrentCourtierChoices.Catalog.parse(StrictJson.text(config.get("catalog"))),key);}
        catch(IOException invalid){throw new IllegalArgumentException("Exact fixed product/catalogue DATA required",invalid);}
    }
    static void requireCurrentCourtierChoicesQueryFrame(CurrentCourtierChoicesResult frame,CoreFrame.Prefix actual,CurrentCourtierControls.Product product,CurrentCourtierChoices.Catalog catalog)throws IOException {
        if(frame.action()!=CurrentCourtierChoices.Action.QUERY_CHOICES||frame.status()!=CurrentCourtierChoicesResult.Status.AVAILABLE||!frame.choiceToken().isEmpty()
                ||frame.effectAttempted()||frame.nativeReturned()||!frame.cleanupKnown()||frame.claimSequence().signum()!=0
                ||frame.providerGeneration().signum()<=0||frame.querySequence().signum()<=0||frame.owner().isEmpty()
                ||frame.product()!=product||frame.catalog()!=catalog||frame.factsBefore().filter(actual::equals).isEmpty()
                ||frame.source().filter(s->s.product()==product&&s.catalog()==catalog).isEmpty())
            throw new IOException("Actual readonly catalogue query differs from original Core/product/catalogue/private lease");
    }
    /** Public DATA comparison only. The caller still needs Received.exactKey to obtain private write authority. */
    static CurrentCourtierChoicesSource.Row requireCurrentCourtierChoicesRow(CurrentCourtierChoicesResult query,CourtierChoicesConfig config)throws IOException {
        requireCurrentCourtierChoicesQueryFrame(query,query.factsBefore().orElseThrow(()->new IOException("Original catalogue Core absent")),config.product(),config.catalog());
        if(config.action()!=CurrentCourtierChoices.Action.SELECT_CHOICE)throw new IOException("Readonly query cannot authorize a selection");
        var source=query.source().orElseThrow();
        if(!source.modelAvailable()||!source.completeModel()||source.configuration().filter(CurrentCourtierConfigurationSource.Configuration::complete).isEmpty())throw new IOException("Actual complete catalogue/numeric source required; no fallback");
        var matches=source.rows().stream().filter(row->row.key().equals(config.choiceKey().orElseThrow())).toList();
        if(matches.size()!=1||!matches.getFirst().executeAdmissible())throw new IOException("Exact key must bind one actual admissible row; no first/last/ordinal fallback");
        return matches.getFirst();
    }
    static void requireCurrentCourtierChoicesDispatchFrame(CurrentCourtierChoicesResult query,CurrentCourtierChoicesResult dispatched,CourtierChoicesConfig config)throws IOException {
        var row=requireCurrentCourtierChoicesRow(query,config);
        if(dispatched.action()!=CurrentCourtierChoices.Action.SELECT_CHOICE||dispatched.status()!=CurrentCourtierChoicesResult.Status.CHOICE_DISPATCHED
                ||!dispatched.effectAttempted()||!dispatched.nativeReturned()||!dispatched.cleanupKnown()||dispatched.claimSequence().signum()<=0
                ||dispatched.product()!=config.product()||dispatched.catalog()!=config.catalog()||!dispatched.choiceToken().equals(row.choiceToken())
                ||!dispatched.providerGeneration().equals(query.providerGeneration())||!dispatched.querySequence().equals(query.querySequence())
                ||!dispatched.factsBefore().equals(query.factsBefore())||!dispatched.source().equals(query.source())||dispatched.owner().isEmpty()
                ||!dispatched.owner().orElseThrow().connectionGeneration().equals(query.owner().orElseThrow().connectionGeneration()))
            throw new IOException("Choice callback differs from original complete source/Core/product/catalogue/private row/token/lease");
    }
    private static void runCurrentCourtierChoices(NativeGameTransport transport,GameSupervisorControl.Descriptor owner,
            NativeLaunchPlan plan,CourtierChoicesConfig config,Path output,Instant deadline,ObjectNode result,ObjectNode originals)throws IOException,InterruptedException {
        try {
            if(!(plan.load() instanceof NativeLaunchPlan.SavedGame))throw new IOException("Current catalogue requires its actual SavedGame owner");
            stage="ONE_ACTUAL_CORE_BEFORE_COURTIER_CHOICES";result.put("read_calls",1);
            var coreRead=transport.readCoreFrameReceived(deadline);
            archiveCurrentLetterOutcome(transport,Files.createDirectory(output.resolve("core-before-courtier-choices")),"core",coreRead.original(),originals);
            if(!(coreRead instanceof NativeGameTransport.CoreReceived before)||!(before.frame() instanceof CoreFrame.Partial core))throw new IOException("Actual current catalogue Core unavailable; no configured replacement");
            requireCurrentDjcAckOwner(transport,owner,before.original(),null);
            var actualSession=before.original().custody().orElseThrow().session();var p=core.prefix();
            if(core.build()!=ExactCk3Build.CK3_121003_STEAM_26785313||!core.build().executableSha256().equalsIgnoreCase(plan.sources().review().gameExecutable().sha256())
                    ||!core.build().coreFrameAdapterId().equals(plan.adapterId())||!p.paused()||!p.mapReady()||!p.hasPlayedCharacter()||!p.playedCharacterAlive()||p.playedCharacterId()==-1||p.localPlayerId()<0||p.speed()<1||p.speed()>5)
                throw new IOException("Exact actual paused living current Core required before catalogue query");
            Instant until=before.validUntil().isBefore(deadline)?before.validUntil():deadline;before.requireOriginal(transport,until);
            stage="ONE_READONLY_CURRENT_COURTIER_CHOICES_QUERY";result.put("read_calls",2);
            var read=transport.readCurrentCourtierChoices(before,config.product(),config.catalog(),until);Path queryOutput=Files.createDirectory(output.resolve("courtier-choices-query"));
            archiveCurrentLetterOutcome(transport,queryOutput,"courtier_choices_query",read.original(),originals);
            if(!(read instanceof NativeGameTransport.CourtierChoicesReceived query))throw new IOException("Actual typed catalogue unavailable or UNKNOWN; no select/open/retry");
            until=query.validUntil().isBefore(until)?query.validUntil():until;query.requireOriginal(transport,until);
            if(query.product()!=config.product()||query.catalog()!=config.catalog())throw new IOException("Private catalogue query differs from original pure DATA intent");
            var queryAck=query.original();requireCurrentDjcAckOwner(transport,owner,queryAck,actualSession);var frame=CurrentCourtierChoicesResult.decodeOutcome(queryAck);
            if(!frame.equals(query.frame()))throw new IOException("Actual catalogue ACK differs from private retained frame");
            requireCurrentCourtierChoicesQueryFrame(frame,p,config.product(),config.catalog());
            if(!frame.owner().orElseThrow().connectionGeneration().equals(actualSession.connectionGeneration()))throw new IOException("Catalogue query owner crossed actual connection");
            originals.set("courtier_choices_query_original_result",write(queryOutput,"original-result.json",queryAck.originalResultToken().orElseThrow().bytes()));
            result.set("query",FullJsonTree.parse(frame.encode().bytes(),SMALL));result.set("session",session(actualSession));result.put("query_available",true).put("query_request_id",queryAck.requestId());
            if(config.action()==CurrentCourtierChoices.Action.QUERY_CHOICES)return;
            var expectedRow=requireCurrentCourtierChoicesRow(frame,config);
            var choice=query.exactKey(config.choiceKey().orElseThrow());
            if(!choice.row().equals(expectedRow)||!choice.key().equals(config.choiceKey().orElseThrow())||!choice.choiceToken().equals(expectedRow.choiceToken()))throw new IOException("Private original choice differs from exact actual catalogue row");
            var prepared=transport.prepareCurrentCourtierChoicesSelect(choice);
            if(prepared.action()!=CurrentCourtierChoices.Action.SELECT_CHOICE||prepared.product()!=config.product()||prepared.catalog()!=config.catalog()||prepared.selected()!=choice||!prepared.selected().row().equals(expectedRow))throw new IOException("Private catalogue preparation crossed original choice/source");
            if(!prepared.deadline().equals(query.validUntil())||prepared.deadline().isAfter(deadline))throw new IOException("Original catalogue selection deadline changed");
            Path actionOutput=Files.createDirectory(output.resolve("one-courtier-choice-select"));
            var intent=StrictJson.object().put("schema","xar.current-courtier-choice-original-intent/v1").put("request_id",prepared.requestId()).put("action",prepared.action().wire())
                    .put("product",prepared.product().wire()).put("catalog",prepared.catalog().wire()).put("choice_key",choice.key()).put("actual_choice_token",choice.choiceToken())
                    .put("original_query_request_id",queryAck.requestId()).put("original_deadline_utc",prepared.deadline().toString())
                    .put("selection_changed",false).put("creator_closed",false).put("courtier_created",false).put("new_date_observed",false).put("physical_save_confirmed",false);
            intent.set("original_query_source",originals.get("courtier_choices_query_original_result").deepCopy());
            intent.set("original_outbound",write(actionOutput,"original-request.packet",prepared.originalPacket().value()));
            originals.set("courtier_choice_select_intent",write(actionOutput,"original-intent.json",FullJsonTree.encode(intent,SMALL)));
            stage="ONE_PRIVATE_SOURCE_COURTIER_CHOICE_SELECT";result.put("select_calls",1);
            var outcome=transport.submitCurrentCourtierChoicesSelect(prepared);
            archiveCurrentLetterOutcome(transport,actionOutput,"courtier_choice_select",outcome,originals);
            if(!(outcome instanceof NativeActionPort.AckReceived ack))throw new IOException("Original catalogue selection UNKNOWN or refused; never replay");
            requireCurrentDjcAckOwner(transport,owner,ack,actualSession);var dispatched=CurrentCourtierChoicesResult.decodeOutcome(ack);
            originals.set("courtier_choice_select_original_result",write(actionOutput,"original-result.json",ack.originalResultToken().orElseThrow().bytes()));
            if(prepared.latestFrame().filter(dispatched::equals).isEmpty())throw new IOException("This original selection ACK was not qualified by its private preparation");
            requireCurrentCourtierChoicesDispatchFrame(frame,dispatched,config);
            if(!dispatched.owner().orElseThrow().connectionGeneration().equals(actualSession.connectionGeneration()))throw new IOException("Catalogue selection owner crossed actual connection");
            result.set("select_result",FullJsonTree.parse(dispatched.encode().bytes(),SMALL));result.put("select_request_id",ack.requestId()).put("choice_key",choice.key()).put("actual_choice_token",choice.choiceToken())
                    .put("select_callback_dispatched",true).put("native_returned",dispatched.nativeReturned()).put("native_handled",false).put("native_status",dispatched.status().wire());
        } finally {
            archiveNaturalDiagnostics(output,originals,transport.diagnostics());var progress=result.deepCopy();progress.set("originals",originals.deepCopy());write(output,"current-courtier-choices-progress.json",FullJsonTree.encode(progress,FullJsonTree.MAXIMUM_BYTES));
        }
    }

    record CourtierConfigurationConfig(CurrentCourtierConfiguration.Action action,CurrentCourtierControls.Product product,CurrentCourtierConfiguration.Setting setting) {
        CourtierConfigurationConfig { Objects.requireNonNull(action);Objects.requireNonNull(product);Objects.requireNonNull(setting); }
    }
    static CourtierConfigurationConfig currentCourtierConfigurationConfig(ObjectNode config) {
        StrictJson.object(config,Set.of("schema","mode","owner_descriptor","overall_timeout_seconds","read_timeout_seconds","maximum_frames_per_operation","product","setting"));
        StrictJson.require(StrictJson.text(config.get("schema")).equals("xar.native-owner-snapshot-config/v33"),"Explicit v33 fixed courtier setting mode required");
        ExactRef.fromJson(config.get("owner_descriptor"));
        StrictJson.integer(config.get("overall_timeout_seconds"),1,600);StrictJson.integer(config.get("read_timeout_seconds"),1,60);
        StrictJson.integer(config.get("maximum_frames_per_operation"),1,65536);
        var action=switch(StrictJson.text(config.get("mode"))) {
            case "current_courtier_configuration_query"->CurrentCourtierConfiguration.Action.QUERY_CONFIGURATION;
            case "current_courtier_configuration_execute"->CurrentCourtierConfiguration.Action.EXECUTE_SETTING;
            default->throw new IllegalArgumentException("Only independent fixed creator query or one private-source Execute; no automatic sequence");
        };
        try { return new CourtierConfigurationConfig(action,CurrentCourtierControls.Product.parse(StrictJson.text(config.get("product"))),CurrentCourtierConfiguration.Setting.parse(StrictJson.text(config.get("setting")))); }
        catch(IOException invalid){throw new IllegalArgumentException("Exact fixed product and setting DATA required",invalid);}
    }
    static void requireCurrentCourtierConfigurationQueryFrame(CurrentCourtierConfigurationResult frame,CoreFrame.Prefix actual,
            CurrentCourtierControls.Product product,CurrentCourtierConfiguration.Setting setting)throws IOException {
        if(frame.action()!=CurrentCourtierConfiguration.Action.QUERY_CONFIGURATION||frame.status()!=CurrentCourtierConfigurationResult.Status.AVAILABLE
                ||frame.effectAttempted()||frame.nativeReturned()||!frame.cleanupKnown()||frame.claimSequence().signum()!=0
                ||frame.providerGeneration().signum()<=0||frame.querySequence().signum()<=0||frame.owner().isEmpty()
                ||frame.product()!=product||frame.setting()!=setting||frame.factsBefore().filter(actual::equals).isEmpty()
                ||frame.source().filter(s->s.product()==product&&s.setting()==setting).isEmpty())
            throw new IOException("Actual readonly fixed creator query differs from its Core/product/setting/private lease");
    }
    static CurrentCourtierConfigurationSource requireCurrentCourtierConfigurationSource(CurrentCourtierConfigurationResult query,CourtierConfigurationConfig config)throws IOException {
        requireCurrentCourtierConfigurationQueryFrame(query,query.factsBefore().orElseThrow(()->new IOException("Original fixed creator Core absent")),config.product(),config.setting());
        var source=query.source().orElseThrow();
        if(config.action()!=CurrentCourtierConfiguration.Action.EXECUTE_SETTING||!source.executeAdmissible()||!source.numericComplete())
            throw new IOException("Original actual creator chain, complete numeric snapshot and native predicates do not admit this fixed Execute; no fallback");
        return source;
    }
    static void requireCurrentCourtierConfigurationDispatchFrame(CurrentCourtierConfigurationResult query,CurrentCourtierConfigurationResult dispatched,CourtierConfigurationConfig config)throws IOException {
        requireCurrentCourtierConfigurationSource(query,config);
        if(dispatched.action()!=CurrentCourtierConfiguration.Action.EXECUTE_SETTING||dispatched.status()!=CurrentCourtierConfigurationResult.Status.SETTING_DISPATCHED
                ||!dispatched.effectAttempted()||!dispatched.nativeReturned()||!dispatched.cleanupKnown()||dispatched.claimSequence().signum()<=0
                ||dispatched.product()!=config.product()||dispatched.setting()!=config.setting()||!dispatched.providerGeneration().equals(query.providerGeneration())
                ||!dispatched.querySequence().equals(query.querySequence())||!dispatched.factsBefore().equals(query.factsBefore())
                ||!dispatched.source().equals(query.source())||dispatched.owner().isEmpty()
                ||!dispatched.owner().orElseThrow().connectionGeneration().equals(query.owner().orElseThrow().connectionGeneration()))
            throw new IOException("Fixed creator callback differs from original full source/Core/product/setting/private lease");
    }
    private static void runCurrentCourtierConfiguration(NativeGameTransport transport,GameSupervisorControl.Descriptor owner,
            NativeLaunchPlan plan,CourtierConfigurationConfig config,Path output,Instant deadline,ObjectNode result,ObjectNode originals)throws IOException,InterruptedException {
        try {
            if(!(plan.load() instanceof NativeLaunchPlan.SavedGame))throw new IOException("Current fixed creator controls require their actual SavedGame owner");
            stage="ONE_ACTUAL_CORE_BEFORE_COURTIER_CONFIGURATION";result.put("read_calls",1);
            var coreRead=transport.readCoreFrameReceived(deadline);
            archiveCurrentLetterOutcome(transport,Files.createDirectory(output.resolve("core-before-courtier-configuration")),"core",coreRead.original(),originals);
            if(!(coreRead instanceof NativeGameTransport.CoreReceived before)||!(before.frame() instanceof CoreFrame.Partial core))throw new IOException("Actual current fixed creator Core unavailable; no configured replacement");
            requireCurrentDjcAckOwner(transport,owner,before.original(),null);
            var actualSession=before.original().custody().orElseThrow().session();var p=core.prefix();
            if(core.build()!=ExactCk3Build.CK3_121003_STEAM_26785313
                    ||!core.build().executableSha256().equalsIgnoreCase(plan.sources().review().gameExecutable().sha256())
                    ||!core.build().coreFrameAdapterId().equals(plan.adapterId())||!p.paused()||!p.mapReady()
                    ||!p.hasPlayedCharacter()||!p.playedCharacterAlive()||p.playedCharacterId()==-1||p.localPlayerId()<0||p.speed()<1||p.speed()>5)
                throw new IOException("Exact actual paused living current Core required before fixed creator query");
            Instant until=before.validUntil().isBefore(deadline)?before.validUntil():deadline;before.requireOriginal(transport,until);
            stage="ONE_READONLY_CURRENT_COURTIER_CONFIGURATION_QUERY";result.put("read_calls",2);
            var read=transport.readCurrentCourtierConfiguration(before,config.product(),config.setting(),until);Path queryOutput=Files.createDirectory(output.resolve("courtier-configuration-query"));
            archiveCurrentLetterOutcome(transport,queryOutput,"courtier_configuration_query",read.original(),originals);
            if(!(read instanceof NativeGameTransport.CourtierConfigurationReceived query))throw new IOException("Actual typed fixed creator source unavailable or UNKNOWN; no Execute or retry");
            until=query.validUntil().isBefore(until)?query.validUntil():until;query.requireOriginal(transport,until);
            if(query.product()!=config.product()||query.setting()!=config.setting())throw new IOException("Private query product/setting differs from original pure DATA intent");
            var queryAck=query.original();requireCurrentDjcAckOwner(transport,owner,queryAck,actualSession);
            var frame=CurrentCourtierConfigurationResult.decodeOutcome(queryAck);
            if(!frame.equals(query.frame()))throw new IOException("Actual fixed creator query differs from private retained frame");
            requireCurrentCourtierConfigurationQueryFrame(frame,p,config.product(),config.setting());
            if(!frame.owner().orElseThrow().connectionGeneration().equals(actualSession.connectionGeneration()))throw new IOException("Fixed creator query owner crossed actual connection");
            originals.set("courtier_configuration_query_original_result",write(queryOutput,"original-result.json",queryAck.originalResultToken().orElseThrow().bytes()));
            result.set("query",FullJsonTree.parse(frame.encode().bytes(),SMALL));result.set("session",session(actualSession));
            result.put("query_available",true).put("query_request_id",queryAck.requestId());
            if(config.action()==CurrentCourtierConfiguration.Action.QUERY_CONFIGURATION)return;
            var selected=requireCurrentCourtierConfigurationSource(frame,config);
            var prepared=transport.prepareCurrentCourtierConfigurationExecute(query);
            if(prepared.action()!=CurrentCourtierConfiguration.Action.EXECUTE_SETTING||prepared.product()!=config.product()||prepared.setting()!=config.setting()||!prepared.selected().equals(selected))
                throw new IOException("Private fixed creator preparation differs from complete original product/setting source");
            if(!prepared.deadline().equals(query.validUntil())||prepared.deadline().isAfter(deadline))throw new IOException("Original fixed creator Execute deadline changed");
            Path actionOutput=Files.createDirectory(output.resolve("one-courtier-configuration-execute"));
            var intent=StrictJson.object().put("schema","xar.current-courtier-configuration-original-intent/v1").put("request_id",prepared.requestId())
                    .put("action",prepared.action().wire()).put("product",prepared.product().wire()).put("setting",prepared.setting().wire())
                    .put("original_query_request_id",queryAck.requestId()).put("original_deadline_utc",prepared.deadline().toString())
                    .put("creator_closed",false).put("courtier_created",false).put("age_changed",false).put("new_date_observed",false).put("physical_save_confirmed",false);
            intent.set("original_query_source",originals.get("courtier_configuration_query_original_result").deepCopy());
            intent.set("original_outbound",write(actionOutput,"original-request.packet",prepared.originalPacket().value()));
            originals.set("courtier_configuration_execute_intent",write(actionOutput,"original-intent.json",FullJsonTree.encode(intent,SMALL)));
            stage="ONE_PRIVATE_SOURCE_COURTIER_CONFIGURATION_EXECUTE";result.put("execute_calls",1);
            var outcome=transport.submitCurrentCourtierConfigurationExecute(prepared);
            archiveCurrentLetterOutcome(transport,actionOutput,"courtier_configuration_execute",outcome,originals);
            if(!(outcome instanceof NativeActionPort.AckReceived ack))throw new IOException("Original fixed creator Execute UNKNOWN or rejected; never replay");
            requireCurrentDjcAckOwner(transport,owner,ack,actualSession);var dispatched=CurrentCourtierConfigurationResult.decodeOutcome(ack);
            originals.set("courtier_configuration_execute_original_result",write(actionOutput,"original-result.json",ack.originalResultToken().orElseThrow().bytes()));
            if(prepared.latestFrame().filter(dispatched::equals).isEmpty())throw new IOException("Original fixed creator ACK was not qualified by its private preparation");
            requireCurrentCourtierConfigurationDispatchFrame(frame,dispatched,config);
            if(!dispatched.owner().orElseThrow().connectionGeneration().equals(actualSession.connectionGeneration()))throw new IOException("Fixed creator Execute owner crossed actual connection");
            result.set("execute_result",FullJsonTree.parse(dispatched.encode().bytes(),SMALL));
            result.put("execute_request_id",ack.requestId()).put("setting_callback_dispatched",true)
                    .put("native_returned",dispatched.nativeReturned()).put("native_handled",false).put("native_status",dispatched.status().wire());
        } finally {
            archiveNaturalDiagnostics(output,originals,transport.diagnostics());var progress=result.deepCopy();progress.set("originals",originals.deepCopy());
            write(output,"current-courtier-configuration-progress.json",FullJsonTree.encode(progress,FullJsonTree.MAXIMUM_BYTES));
        }
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

    static void requireCurrentDesInitGuardConfig(ObjectNode config) {
        StrictJson.object(config,Set.of("schema","mode","owner_descriptor","overall_timeout_seconds","read_timeout_seconds","maximum_frames_per_operation"));
        StrictJson.require("xar.native-owner-snapshot-config/v40".equals(StrictJson.text(config.get("schema")))
                &&"current_des_saved_game_init_guard".equals(StrictJson.text(config.get("mode"))),"Only the explicit fixed readonly DES guard mode");
        ExactRef.fromJson(config.get("owner_descriptor"));
        StrictJson.integer(config.get("overall_timeout_seconds"),1,600);
        StrictJson.integer(config.get("read_timeout_seconds"),1,60);
        StrictJson.integer(config.get("maximum_frames_per_operation"),1,65536);
    }
    static CoreFrame.Prefix requireCurrentDesInitGuardCore(CoreFrame frame)throws IOException {
        if(!(frame instanceof CoreFrame.Partial core)||core.build()!=ExactCk3Build.CK3_121003_STEAM_26785313)
            throw new IOException("Exact actual current267 Core required for DES guard observation");
        var p=core.prefix();
        if(!p.paused()||!p.mapReady()||!p.hasPlayedCharacter()||!p.playedCharacterAlive()||p.playedCharacterId()==-1
                ||p.localPlayerId()<0||p.speed()<1||p.speed()>5)
            throw new IOException("Actual paused living local-player Core required for DES guard observation");
        return p;
    }
    static CurrentDesInitGuardSource requireCurrentDesInitGuardQueryFrame(CurrentDesInitGuardResult frame,
            CoreFrame.Prefix actual,java.math.BigInteger connection)throws IOException {
        if(!frame.successful()||!frame.cleanupKnown()||frame.effectAttempted()||frame.nativeReturned()||frame.nativeHandled()
                ||frame.claimSequence().signum()!=0||frame.providerGeneration().signum()<=0||frame.querySequence().signum()<=0
                ||frame.factsBefore().filter(actual::equals).isEmpty()||frame.owner().isEmpty()||frame.source().isEmpty()
                ||!frame.owner().orElseThrow().connectionGeneration().equals(connection))
            throw new IOException("Actual DES guard frame differs from original complete Core/connection/readonly query");
        var source=frame.source().orElseThrow();
        if(source.characterId()!=actual.playedCharacterId()||!source.characterAlive()||!source.nativeIsPlayer()
                ||!source.nativeDefinitionFound()||!source.scopeBound()||!source.sampledTwice())
            throw new IOException("Actual fixed DES guard source is not bound to the same living played actor");
        // Both true and false IsShown are observation DATA. Neither proves initialization/migration.
        return source;
    }
    static void initializeCurrentDesInitGuardResult(ObjectNode result,String machineId) {
        result.put("schema","xar.native-owner-current-des-init-guard/v1").put("mode","current_des_saved_game_init_guard")
                .put("machine_id",machineId).put("steam_build_id","26785313").put("guard_key",CurrentDesInitGuard.GUARD_KEY)
                .put("read_calls",0).put("query_calls",0).put("query_available",false).putNull("native_shown").putNull("character_id")
                .put("effect_attempted",false).put("native_returned",false).put("native_handled",false)
                .put("initialization_executed",false).put("migration_executed",false).put("initialization_proven",false).put("migration_proven",false)
                .put("execute_calls",0).put("date_calls",0).put("save_calls",0).put("new_date_observed",false).put("physical_save_confirmed",false);
    }
    private static void runCurrentDesInitGuard(NativeGameTransport transport,GameSupervisorControl.Descriptor owner,
            NativeLaunchPlan plan,Path output,Instant deadline,ObjectNode result,ObjectNode originals)throws IOException,InterruptedException {
        try {
            if(!(plan.load() instanceof NativeLaunchPlan.SavedGame))throw new IOException("DES loaded-game guard requires its actual SavedGame owner");
            stage="ONE_ACTUAL_CORE_BEFORE_DES_INIT_GUARD";result.put("read_calls",1);
            var coreRead=transport.readCoreFrameReceived(deadline);
            archiveCurrentLetterOutcome(transport,Files.createDirectory(output.resolve("core-before-des-init-guard")),"core",coreRead.original(),originals);
            if(!(coreRead instanceof NativeGameTransport.CoreReceived before))throw new IOException("Actual DES guard Core unavailable or UNKNOWN; no retry");
            var p=requireCurrentDesInitGuardCore(before.frame());
            var core=(CoreFrame.Partial)before.frame();
            if(!core.build().executableSha256().equalsIgnoreCase(plan.sources().review().gameExecutable().sha256())
                    ||!core.build().coreFrameAdapterId().equals(plan.adapterId()))throw new IOException("DES guard Core differs from actual owner exact build");
            requireCurrentDjcAckOwner(transport,owner,before.original(),null);
            var actualSession=before.original().custody().orElseThrow().session();
            Instant until=before.validUntil().isBefore(deadline)?before.validUntil():deadline;
            before.requireOriginal(transport,until);
            stage="ONE_READONLY_CURRENT_DES_INIT_GUARD";result.put("read_calls",2).put("query_calls",1);
            var read=transport.readCurrentDesInitGuard(before,until);
            Path queryOutput=Files.createDirectory(output.resolve("des-init-guard-query"));
            archiveCurrentLetterOutcome(transport,queryOutput,"des_init_guard_query",read.original(),originals);
            if(!(read instanceof NativeGameTransport.DesInitGuardReceived query))throw new IOException("Actual typed DES guard unavailable or UNKNOWN; no Execute, replacement or retry");
            until=query.validUntil().isBefore(until)?query.validUntil():until;
            query.requireOriginal(transport,until);
            var ack=query.original();requireCurrentDjcAckOwner(transport,owner,ack,actualSession);
            var frame=CurrentDesInitGuardResult.decodeOutcome(ack);
            if(!frame.equals(query.frame()))throw new IOException("Actual DES guard ACK differs from its original private retained frame");
            var source=requireCurrentDesInitGuardQueryFrame(frame,p,actualSession.connectionGeneration());
            originals.set("des_init_guard_query_original_result",write(queryOutput,"original-result.json",ack.originalResultToken().orElseThrow().bytes()));
            result.set("query",FullJsonTree.parse(frame.encode().bytes(),SMALL));result.set("session",session(actualSession));
            result.put("query_available",true).put("query_request_id",ack.requestId()).put("native_shown",source.nativeShown()).put("character_id",source.characterId());
        } finally {
            archiveNaturalDiagnostics(output,originals,transport.diagnostics());
            var progress=result.deepCopy();progress.set("originals",originals.deepCopy());
            write(output,"current-des-init-guard-progress.json",FullJsonTree.encode(progress,FullJsonTree.MAXIMUM_BYTES));
        }
    }

    enum RiteCreateMode {
        QUERY("current_rite_create_query"),
        CREATE_AND_ACCEPT_CONFIRMATION("current_rite_create_and_accept_confirmation"),
        NAVIGATION("current_rite_create_navigation");
        private final String wire;
        RiteCreateMode(String wire) {this.wire=wire;}
        String wire() {return wire;}
    }
    record RiteCreateConfig(RiteCreateMode mode,long expectedSourceRiteId,String navigationAction,
            int maximumConfirmationPolls,long confirmationPollIntervalMs) {
        int submissions() {return mode==RiteCreateMode.CREATE_AND_ACCEPT_CONFIRMATION?7+maximumConfirmationPolls:3;}
    }
    static RiteCreateConfig currentRiteCreateConfig(ObjectNode config) {
        StrictJson.require("xar.native-owner-snapshot-config/v41".equals(StrictJson.text(config.get("schema"))),"Explicit v41 current Rite Create family required");
        String mode=StrictJson.text(config.get("mode"));
        var fields=new java.util.HashSet<>(Set.of("schema","mode","owner_descriptor","overall_timeout_seconds","read_timeout_seconds","maximum_frames_per_operation"));
        RiteCreateMode selected;
        if("current_rite_create_query".equals(mode)) {
            selected=RiteCreateMode.QUERY;fields.add("expected_source_rite_id");
        } else if("current_rite_create_and_accept_confirmation".equals(mode)) {
            selected=RiteCreateMode.CREATE_AND_ACCEPT_CONFIRMATION;
            fields.addAll(Set.of("expected_source_rite_id","maximum_confirmation_polls","confirmation_poll_interval_ms"));
        } else {
            StrictJson.require("current_rite_create_navigation".equals(mode),"Only explicit Create query, same-receiver complete Create/accept, or fixed creator navigation");
            selected=RiteCreateMode.NAVIGATION;fields.add("navigation_action");
        }
        StrictJson.object(config,Set.copyOf(fields));
        ExactRef.fromJson(config.get("owner_descriptor"));
        StrictJson.integer(config.get("overall_timeout_seconds"),1,600);
        StrictJson.integer(config.get("read_timeout_seconds"),1,60);
        StrictJson.integer(config.get("maximum_frames_per_operation"),1,65536);
        if(selected==RiteCreateMode.NAVIGATION) {
            String action=StrictJson.text(config.get("navigation_action"));
            StrictJson.require(Set.of("OPEN_RITE_CREATOR","OPEN_PUPPET_RITE_CREATOR").contains(action),"Only two actual fixed creator navigation actions; no old NavigationAction alias");
            return new RiteCreateConfig(selected,-1,action,0,0);
        }
        // An observed source-Rite ID is DATA only. It is mandatory, never a default0
        // or a substitute for actual same-receiver draft/query/lease authority.
        long rite=StrictJson.integer(config.get("expected_source_rite_id"),0,0xffff_fffeL);
        int polls=selected==RiteCreateMode.CREATE_AND_ACCEPT_CONFIRMATION?
                Math.toIntExact(StrictJson.integer(config.get("maximum_confirmation_polls"),1,64)):0;
        long interval=selected==RiteCreateMode.CREATE_AND_ACCEPT_CONFIRMATION?
                StrictJson.integer(config.get("confirmation_poll_interval_ms"),100,5000):0;
        return new RiteCreateConfig(selected,rite,null,polls,interval);
    }
    static CoreFrame.Prefix requireCurrentRiteCreateCore(CoreFrame frame)throws IOException {
        if(!(frame instanceof CoreFrame.Partial core)||core.build()!=ExactCk3Build.CK3_121003_STEAM_26785313)
            throw new IOException("Actual exact current267 Core required for Rite Create");
        var p=core.prefix();
        if(!p.paused()||!p.mapReady()||!p.hasPlayedCharacter()||!p.playedCharacterAlive()
                ||p.playedCharacterId()==-1||p.localPlayerId()<0||p.speed()<1||p.speed()>5)
            throw new IOException("Actual paused living local-player Core required for Rite Create");
        return p;
    }
    static void initializeCurrentRiteCreateResult(ObjectNode result,RiteCreateConfig config,String machineId) {
        result.put("schema","xar.native-owner-current-rite-create/v1").put("mode",config.mode().wire())
                .put("machine_id",machineId).put("steam_build_id","26785313")
                .put("read_calls",0).put("draft_calls",0).put("query_calls",0).put("create_calls",0)
                .put("confirmation_query_calls",0).put("accept_calls",0).put("navigation_calls",0)
                .put("query_available",false).put("create_callback_dispatched",false).put("accept_callback_dispatched",false)
                .put("native_returned",false).put("native_handled",false).put("rite_created",false)
                .put("initial_binding_confirmed",false).put("new_date_observed",false).put("physical_save_confirmed",false)
                .put("date_calls",0).put("save_calls",0);
        if(config.mode()==RiteCreateMode.NAVIGATION)result.put("navigation_action",config.navigationAction());
        else result.put("expected_source_rite_id",config.expectedSourceRiteId());
    }

    static CurrentRiteCreateSource requireCurrentRiteCreateQueryFrame(CurrentRiteCreateResult frame,
            CurrentRiteCreate.Action action,CoreFrame.Prefix actual,long sourceRite,java.math.BigInteger connection)throws IOException {
        if(!action.queryOnly()||frame.action()!=action||frame.status()!=CurrentRiteCreateResult.Status.AVAILABLE
                ||!frame.cleanupKnown()||frame.effectAttempted()||frame.nativeReturned()||frame.nativeHandled()
                ||frame.claimSequence().signum()!=0||frame.providerGeneration().signum()<=0||frame.querySequence().signum()<=0
                ||frame.factsBefore().filter(actual::equals).isEmpty()||frame.owner().isEmpty()||frame.source().isEmpty()
                ||!frame.owner().orElseThrow().connectionGeneration().equals(connection))
            throw new IOException("Actual complete Rite Create query differs from its Core/connection/readonly lease");
        var source=frame.source().orElseThrow();
        if(source.sourceRiteId()!=sourceRite||source.actorId()!=actual.playedCharacterId()
                ||source.phase()!=(action==CurrentRiteCreate.Action.QUERY?CurrentRiteCreateSource.Phase.DRAFT:CurrentRiteCreateSource.Phase.CONFIRMATION))
            throw new IOException("Actual Rite Create source differs from expected DATA Rite/current actor/phase");
        return source;
    }
    static void requireCurrentRiteCreateDispatchFrame(CurrentRiteCreateResult frame,CurrentRiteCreateResult query,
            CurrentRiteCreate.Action action)throws IOException {
        var expected=action==CurrentRiteCreate.Action.CREATE?CurrentRiteCreateResult.Status.CREATE_DISPATCHED:
                CurrentRiteCreateResult.Status.CONFIRMATION_DISPATCHED;
        if((action!=CurrentRiteCreate.Action.CREATE&&action!=CurrentRiteCreate.Action.ACCEPT_CONFIRMATION)
                ||query.action()!=(action==CurrentRiteCreate.Action.CREATE?CurrentRiteCreate.Action.QUERY:CurrentRiteCreate.Action.QUERY_CONFIRMATION)
                ||query.status()!=CurrentRiteCreateResult.Status.AVAILABLE||frame.action()!=action||frame.status()!=expected
                ||!frame.cleanupKnown()||!frame.effectAttempted()||!frame.nativeReturned()||frame.nativeHandled()||frame.claimSequence().signum()<=0
                ||!frame.source().equals(query.source())||!frame.factsBefore().equals(query.factsBefore())
                ||!frame.providerGeneration().equals(query.providerGeneration())||!frame.querySequence().equals(query.querySequence())
                ||frame.owner().isEmpty()||query.owner().isEmpty()
                ||!frame.owner().orElseThrow().connectionGeneration().equals(query.owner().orElseThrow().connectionGeneration()))
            throw new IOException("Actual void Rite Create callback differs from immutable beforeSource/Core/lease/spent claim");
        // Ticket/pump belong to each actual callback. Only the same connection is
        // shared; independent actual custody is verified against each original ACK.
    }
    static void requireCurrentRiteCreateWaitingFrame(CurrentRiteCreateResult frame,CurrentRiteCreateResult originalQuery,
            CoreFrame.Prefix actual,java.math.BigInteger connection)throws IOException {
        if(originalQuery.action()!=CurrentRiteCreate.Action.QUERY||originalQuery.status()!=CurrentRiteCreateResult.Status.AVAILABLE
                ||frame.action()!=CurrentRiteCreate.Action.QUERY_CONFIRMATION||frame.status()!=CurrentRiteCreateResult.Status.CONFIRMATION_PENDING
                ||!frame.cleanupKnown()||frame.source().isPresent()||frame.effectAttempted()||frame.nativeReturned()||frame.nativeHandled()
                ||frame.claimSequence().signum()!=0||!frame.providerGeneration().equals(originalQuery.providerGeneration())
                ||!frame.querySequence().equals(originalQuery.querySequence())
                ||frame.factsBefore().isPresent()&&!frame.factsBefore().orElseThrow().equals(actual)
                ||frame.owner().isPresent()&&!frame.owner().orElseThrow().connectionGeneration().equals(connection))
            throw new IOException("Only the private clean original-Create confirmation_pending may be observed again");
    }
    private static NativeGameTransport.CoreReceived readCurrentRiteCreateCore(NativeGameTransport transport,
            GameSupervisorControl.Descriptor owner,NativeLaunchPlan plan,NativeObservationPort.TransportSession expected,
            Path output,String name,Instant deadline,ObjectNode result,ObjectNode originals)throws IOException,InterruptedException {
        if(!Instant.now().isBefore(deadline))throw new IOException("Original Rite Create/Game deadline expired");
        var read=transport.readCoreFrameReceived(deadline);
        archiveCurrentLetterOutcome(transport,Files.createDirectory(output.resolve(name)),name,read.original(),originals);
        result.put("read_calls",result.path("read_calls").intValue()+1);
        if(!(read instanceof NativeGameTransport.CoreReceived core))throw new IOException("Actual Rite Create Core unavailable or UNKNOWN; no replacement or retry");
        requireCurrentRiteCreateCore(core.frame());
        var frame=(CoreFrame.Partial)core.frame();
        if(!frame.build().executableSha256().equalsIgnoreCase(plan.sources().review().gameExecutable().sha256())
                ||!frame.build().coreFrameAdapterId().equals(plan.adapterId()))throw new IOException("Rite Create Core differs from actual owner executable/adapter");
        requireCurrentDjcAckOwner(transport,owner,core.original(),expected);
        core.requireOriginal(transport,core.validUntil().isBefore(deadline)?core.validUntil():deadline);
        result.set(name,FullJsonTree.parse(CoreFramePublicCodec.encode(core.frame()).bytes(),SMALL));
        return core;
    }
    private static NativeActionPort.AckReceived requireCurrentRiteCreateActualAck(NativeGameTransport transport,
            GameSupervisorControl.Descriptor owner,NativeObservationPort.TransportSession expected,
            NativeActionPort.DispatchOutcome outcome,String requestId,byte[] originalPacket)throws IOException {
        if(!(outcome instanceof NativeActionPort.AckReceived ack))throw new IOException("No actual qualified Rite Create ACK; retain original without replay");
        requireCurrentDjcAckOwner(transport,owner,ack,expected);
        if(!ack.requestId().equals(requestId)||ack.outbound().isEmpty()
                ||!Arrays.equals(ack.outbound().orElseThrow().originalPacket(),originalPacket))
            throw new IOException("Rite Create ACK does not belong to this exact prepared packet");
        return ack;
    }
    private static CurrentRiteCreateResult archiveCurrentRiteCreateAck(Path directory,String name,
            NativeActionPort.AckReceived ack,ObjectNode originals)throws IOException {
        originals.set(name+"_original_result",write(directory,"original-result.json",ack.originalResultToken().orElseThrow().bytes()));
        return CurrentRiteCreateResult.decodeOutcome(ack);
    }
    private static void runCurrentRiteCreate(NativeGameTransport transport,GameSupervisorControl.Descriptor owner,
            NativeLaunchPlan plan,RiteCreateConfig config,Path output,Instant deadline,Duration receiveTimeout,
            ObjectNode result,ObjectNode originals)throws IOException,InterruptedException {
        try {
            if(!(plan.load() instanceof NativeLaunchPlan.SavedGame))throw new IOException("Rite Create requires its actual SavedGame owner");
            stage="RITE_CREATE_FRESH_ACTUAL_CORE";
            var before=readCurrentRiteCreateCore(transport,owner,plan,null,output,"core-before-rite-create",deadline,result,originals);
            var prefix=requireCurrentRiteCreateCore(before.frame());
            var actualSession=before.original().custody().orElseThrow().session();
            result.set("session",session(actualSession));
            Instant until=before.validUntil().isBefore(deadline)?before.validUntil():deadline;
            if(config.mode()==RiteCreateMode.NAVIGATION) {
                runCurrentRiteCreateNavigation(transport,owner,plan,config,before,actualSession,output,until,result,originals);
                return;
            }
            stage="RITE_CREATE_ACTUAL_OLD_DRAFT_GUARD_DATA";
            var draftRead=transport.readRiteDraftCostsReceived(before,config.expectedSourceRiteId(),until);
            Path draftOutput=Files.createDirectory(output.resolve("actual-draft-before-create"));
            archiveCurrentLetterOutcome(transport,draftOutput,"source_draft",draftRead.original(),originals);
            result.put("draft_calls",1).put("read_calls",result.path("read_calls").intValue()+1);
            if(!(draftRead instanceof NativeGameTransport.RiteDraftCostsReceived draft)
                    ||!(draft.frame() instanceof RiteDraftCostsFrameV2.Partial actualDraft))
                throw new IOException("Actual same-receiver guarded Rite draft unavailable; no Create query");
            until=draft.validUntil().isBefore(until)?draft.validUntil():until;
            draft.requireOriginal(transport,until);requireRiteDraftCostsSelection(plan,draft.frame());
            requireCurrentDjcAckOwner(transport,owner,draft.original(),actualSession);
            if(actualDraft.draft().sourceRiteId()!=config.expectedSourceRiteId())throw new IOException("Actual draft does not match observed source Rite DATA");
            result.set("source_draft",FullJsonTree.parse(RiteDraftCostsFrameV2PublicCodec.encode(draft.frame()).bytes(),SMALL));
            stage="RITE_CREATE_ONE_ACTUAL_DRAFT_QUERY";
            var read=transport.readCurrentRiteCreate(draft,until);
            Path queryOutput=Files.createDirectory(output.resolve("rite-create-query"));
            archiveCurrentLetterOutcome(transport,queryOutput,"rite_create_query",read.original(),originals);
            result.put("query_calls",1).put("read_calls",result.path("read_calls").intValue()+1);
            if(!(read instanceof NativeGameTransport.RiteCreateReceived query))throw new IOException("Actual typed Rite Create query unavailable or UNKNOWN; no effect/retry");
            until=query.validUntil().isBefore(until)?query.validUntil():until;
            query.requireOriginal(transport,until);requireCurrentDjcAckOwner(transport,owner,query.original(),actualSession);
            var queryFrame=archiveCurrentRiteCreateAck(queryOutput,"rite_create_query",query.original(),originals);
            if(!queryFrame.equals(query.frame()))throw new IOException("Rite Create query original ACK differs from private immutable frame");
            var source=requireCurrentRiteCreateQueryFrame(queryFrame,CurrentRiteCreate.Action.QUERY,prefix,
                    config.expectedSourceRiteId(),actualSession.connectionGeneration());
            result.set("query",FullJsonTree.parse(queryFrame.encode().bytes(),SMALL));
            result.put("query_available",true).put("query_request_id",query.original().requestId());
            if(config.mode()==RiteCreateMode.QUERY)return; // Actual false Can remains complete DATA.
            if(!source.draft().orElseThrow().createAdmissible())throw new IOException("Actual native draft/Can/piety/dynastic gates refuse Create; no effect");
            stage="RITE_CREATE_PREPARE_ORIGINAL_ONCE_CREATE";
            var prepared=transport.prepareCurrentRiteCreate(query);
            if(prepared.action()!=CurrentRiteCreate.Action.CREATE||!prepared.deadline().equals(query.validUntil()))
                throw new IOException("Actual prepared Create differs from original query action/deadline");
            Path createOutput=Files.createDirectory(output.resolve("one-rite-create"));
            var intent=StrictJson.object().put("schema","xar.current-rite-create-intent/v1").put("request_id",prepared.requestId())
                    .put("action",prepared.action().wire()).put("source_query_request_id",query.original().requestId())
                    .put("original_deadline_utc",prepared.deadline().toString()).put("rite_created",false).put("initial_binding_confirmed",false);
            intent.set("original_outbound",write(createOutput,"original-request.packet",prepared.originalPacket().value()));
            intent.set("actual_before_query",FullJsonTree.parse(queryFrame.encode().bytes(),SMALL));
            originals.set("create_intent",write(createOutput,"original-intent.json",FullJsonTree.encode(intent,SMALL)));
            stage="RITE_CREATE_ONE_NATIVE_CREATE";result.put("create_calls",1);
            var outcome=transport.submitCurrentRiteCreate(prepared);
            archiveCurrentLetterOutcome(transport,createOutput,"rite_create",outcome,originals);
            var ack=requireCurrentRiteCreateActualAck(transport,owner,actualSession,outcome,prepared.requestId(),prepared.originalPacket().value());
            var created=archiveCurrentRiteCreateAck(createOutput,"rite_create",ack,originals);
            requireCurrentRiteCreateDispatchFrame(created,queryFrame,CurrentRiteCreate.Action.CREATE);
            result.set("create_result",FullJsonTree.parse(created.encode().bytes(),SMALL));
            result.put("create_callback_dispatched",true).put("native_returned",created.nativeReturned()).put("native_handled",created.nativeHandled());
            // Query authority has been consumed. Do not call its unused guard again;
            // the transport alone retains the identical accepted Create occurrence.
            var pending=transport.retainCurrentRiteCreate(ack);
            if(pending.original()!=ack||!pending.deadline().equals(prepared.deadline()))throw new IOException("Actual original Create pending receipt/deadline changed");
            Instant originalCreateDeadline=pending.deadline();
            result.put("original_create_deadline_utc",originalCreateDeadline.toString());
            stage="RITE_CREATE_INDEPENDENT_POST_CREATE_CORE";
            var modalCore=readCurrentRiteCreateCore(transport,owner,plan,actualSession,output,"core-after-create-before-confirmation",originalCreateDeadline,result,originals);
            if(!requireCurrentRiteCreateCore(modalCore.frame()).equals(prefix))throw new IOException("Actual actor/date/Core changed after Create");
            modalCore.requireOriginal(transport,originalCreateDeadline); // Must cover, never shorten/renew the original Create body deadline.
            NativeGameTransport.RiteCreateReceived ready=null;
            for(int poll=0;poll<config.maximumConfirmationPolls();++poll) {
                if(!Instant.now().isBefore(originalCreateDeadline))throw new IOException("Original Create deadline expired while observing confirmation");
                stage="RITE_CREATE_FINITE_CORRELATED_CONFIRMATION_QUERY";
                Instant receiveUntil=Instant.now().plus(receiveTimeout);
                if(originalCreateDeadline.isBefore(receiveUntil))receiveUntil=originalCreateDeadline;
                var confirmation=transport.readCurrentRiteCreateConfirmation(pending,modalCore,receiveUntil);
                Path confirmationOutput=Files.createDirectory(output.resolve("confirmation-query-"+(poll+1)));
                String key="confirmation_query_"+(poll+1);
                archiveCurrentLetterOutcome(transport,confirmationOutput,key,confirmation.original(),originals);
                result.put("confirmation_query_calls",poll+1).put("read_calls",result.path("read_calls").intValue()+1);
                if(confirmation instanceof NativeGameTransport.RiteCreateWaiting waiting) {
                    requireCurrentDjcAckOwner(transport,owner,waiting.original(),actualSession);
                    var waitingFrame=archiveCurrentRiteCreateAck(confirmationOutput,key,waiting.original(),originals);
                    if(!waitingFrame.equals(waiting.frame()))throw new IOException("Actual pending ACK differs from private typed waiting source");
                    requireCurrentRiteCreateWaitingFrame(waitingFrame,queryFrame,prefix,actualSession.connectionGeneration());
                    result.set("last_confirmation_observation",FullJsonTree.parse(waitingFrame.encode().bytes(),SMALL));
                    if(poll+1>=config.maximumConfirmationPolls())throw new IOException("Finite known confirmation_pending observation bound reached; no replay");
                    if(!Instant.now().plusMillis(config.confirmationPollIntervalMs()).isBefore(originalCreateDeadline))
                        throw new IOException("No finite original-deadline interval remains for another readonly confirmation query");
                    Thread.sleep(config.confirmationPollIntervalMs());
                    continue;
                }
                if(!(confirmation instanceof NativeGameTransport.RiteCreateReceived actualReady))throw new IOException("Actual confirmation query unavailable or UNKNOWN; no accept/retry");
                actualReady.requireOriginal(transport,originalCreateDeadline);
                requireCurrentDjcAckOwner(transport,owner,actualReady.original(),actualSession);
                var readyFrame=archiveCurrentRiteCreateAck(confirmationOutput,key,actualReady.original(),originals);
                if(!readyFrame.equals(actualReady.frame()))throw new IOException("Actual confirmation ACK differs from private complete frame");
                var modal=requireCurrentRiteCreateQueryFrame(readyFrame,CurrentRiteCreate.Action.QUERY_CONFIRMATION,prefix,
                        config.expectedSourceRiteId(),actualSession.connectionGeneration());
                result.set("confirmation_query",FullJsonTree.parse(readyFrame.encode().bytes(),SMALL));
                if(!modal.confirmation().orElseThrow().acceptAdmissible())throw new IOException("Actual original Create modal CanAccept refuses; no acceptance");
                ready=actualReady;
                break;
            }
            if(ready==null)throw new IOException("No actual complete correlated confirmation source; no acceptance");
            stage="RITE_CREATE_PREPARE_ORIGINAL_ONCE_ACCEPT";
            var acceptance=transport.prepareCurrentRiteCreateAcceptance(ready);
            if(acceptance.action()!=CurrentRiteCreate.Action.ACCEPT_CONFIRMATION||!acceptance.deadline().equals(originalCreateDeadline))
                throw new IOException("Actual prepared acceptance escaped original Create action/deadline");
            Path acceptOutput=Files.createDirectory(output.resolve("one-rite-create-accept"));
            var acceptIntent=StrictJson.object().put("schema","xar.current-rite-create-accept-intent/v1").put("request_id",acceptance.requestId())
                    .put("action",acceptance.action().wire()).put("original_create_request_id",ack.requestId())
                    .put("source_query_request_id",ready.original().requestId()).put("original_deadline_utc",originalCreateDeadline.toString())
                    .put("rite_created",false).put("initial_binding_confirmed",false);
            acceptIntent.set("original_outbound",write(acceptOutput,"original-request.packet",acceptance.originalPacket().value()));
            acceptIntent.set("actual_before_query",FullJsonTree.parse(ready.frame().encode().bytes(),SMALL));
            originals.set("accept_intent",write(acceptOutput,"original-intent.json",FullJsonTree.encode(acceptIntent,SMALL)));
            stage="RITE_CREATE_ONE_NATIVE_ACCEPT";result.put("accept_calls",1);
            var accepted=transport.submitCurrentRiteCreate(acceptance);
            archiveCurrentLetterOutcome(transport,acceptOutput,"rite_create_accept",accepted,originals);
            var acceptAck=requireCurrentRiteCreateActualAck(transport,owner,actualSession,accepted,acceptance.requestId(),acceptance.originalPacket().value());
            var finalFrame=archiveCurrentRiteCreateAck(acceptOutput,"rite_create_accept",acceptAck,originals);
            requireCurrentRiteCreateDispatchFrame(finalFrame,ready.frame(),CurrentRiteCreate.Action.ACCEPT_CONFIRMATION);
            result.set("accept_result",FullJsonTree.parse(finalFrame.encode().bytes(),SMALL));
            result.put("accept_callback_dispatched",true).put("native_returned",finalFrame.nativeReturned()).put("native_handled",finalFrame.nativeHandled());
            stage="RITE_CREATE_INDEPENDENT_FINAL_CORE";
            var after=readCurrentRiteCreateCore(transport,owner,plan,actualSession,output,"core-after-rite-accept",deadline,result,originals);
            if(!requireCurrentRiteCreateCore(after.frame()).equals(prefix))throw new IOException("Actual actor/date/Core changed after acceptance");
            result.put("independent_final_core_unchanged",true); // No Rite/binding or physical Save claim.
        } finally {
            archiveNaturalDiagnostics(output,originals,transport.diagnostics());
            var progress=result.deepCopy();progress.set("originals",originals.deepCopy());
            write(output,"current-rite-create-progress.json",FullJsonTree.encode(progress,FullJsonTree.MAXIMUM_BYTES));
        }
    }
    private static void runCurrentRiteCreateNavigation(NativeGameTransport transport,GameSupervisorControl.Descriptor owner,
            NativeLaunchPlan plan,RiteCreateConfig config,NativeGameTransport.CoreReceived before,
            NativeObservationPort.TransportSession actualSession,Path output,Instant until,ObjectNode result,ObjectNode originals)throws IOException,InterruptedException {
        var action=NativeGameTransport.RiteCreateNavigationAction.valueOf(config.navigationAction());
        stage="RITE_CREATE_ONE_ACTUAL_FIXED_NAVIGATION_QUERY";
        var read=transport.readCurrentRiteCreateNavigation(before,action,until);
        Path queryOutput=Files.createDirectory(output.resolve("rite-create-navigation-query"));
        archiveCurrentLetterOutcome(transport,queryOutput,"rite_create_navigation_query",read.original(),originals);
        result.put("query_calls",1).put("read_calls",result.path("read_calls").intValue()+1);
        if(!(read instanceof NativeGameTransport.GuiControlsReceivedV2 query))throw new IOException("Actual fixed Create navigation query unavailable or UNKNOWN; no activation");
        until=query.validUntil().isBefore(until)?query.validUntil():until;
        query.requireOriginal(transport,until);requireGuiControlsSelection(plan,query.frame());
        requireCurrentDjcAckOwner(transport,owner,query.original(),actualSession);
        if(!query.frame().coreFrame().equals(before.frame())||query.frame().window()!=GuiControlsFrameV2.Window.FAITH
                ||!query.frame().queryAvailable()||query.frame().ownerWitness().isEmpty()
                ||!query.frame().ownerWitness().orElseThrow().connectionGeneration().equals(actualSession.connectionGeneration()))
            throw new IOException("Actual Create navigation source crossed its original Core/connection/faith root");
        result.set("navigation_query",FullJsonTree.parse(GuiControlsFrameV2PublicCodec.encode(query.frame()).bytes(),FullJsonTree.MAXIMUM_BYTES));
        var prepared=transport.prepareCurrentRiteCreateNavigation(query,action);
        if(prepared.action()!=action||!prepared.deadline().equals(query.validUntil()))throw new IOException("Actual fixed navigation prepared action/deadline changed");
        Path actionOutput=Files.createDirectory(output.resolve("one-rite-create-navigation"));
        var intent=StrictJson.object().put("schema","xar.current-rite-create-navigation-intent/v1").put("request_id",prepared.requestId())
                .put("navigation_action",action.name()).put("source_query_request_id",query.original().requestId())
                .put("original_deadline_utc",prepared.deadline().toString()).put("window_open_confirmed",false).put("rite_created",false);
        intent.set("original_outbound",write(actionOutput,"original-request.packet",prepared.originalPacket().value()));
        originals.set("navigation_intent",write(actionOutput,"original-intent.json",FullJsonTree.encode(intent,SMALL)));
        stage="RITE_CREATE_ONE_FIXED_NAVIGATION";result.put("navigation_calls",1);
        var outcome=transport.submitCurrentRiteCreateNavigation(prepared);
        archiveCurrentLetterOutcome(transport,actionOutput,"rite_create_navigation",outcome,originals);
        var ack=requireCurrentRiteCreateActualAck(transport,owner,actualSession,outcome,prepared.requestId(),prepared.originalPacket().value());
        var frame=GuiControlsFrameV2PublicCodec.decodeOutcome(ack);requireGuiControlsSelection(plan,frame);
        originals.set("navigation_original_result",write(actionOutput,"original-result.json",ack.originalResultToken().orElseThrow().bytes()));
        result.set("navigation_result",FullJsonTree.parse(GuiControlsFrameV2PublicCodec.encode(frame).bytes(),FullJsonTree.MAXIMUM_BYTES));
        result.put("native_handled",frame.nativeHandled()).putNull("native_returned").put("window_open_confirmed",false);
        if(frame.status()!=GuiControlsFrameV2.Status.SUBMITTED||!frame.effectAttempted()
                ||!frame.coreFrame().equals(before.frame())||frame.window()!=GuiControlsFrameV2.Window.FAITH
                ||!frame.queryGeneration().equals(query.frame().queryGeneration())||frame.ownerWitness().isEmpty()
                ||!frame.ownerWitness().orElseThrow().connectionGeneration().equals(actualSession.connectionGeneration()))
            throw new IOException("Fixed Create navigation has no known submitted original callback; no retry or window poststate");
        result.put("navigation_callback_dispatched",true);
    }

    record RiteTextConfig(CurrentRiteText.Action action,long sourceRiteId,String text) {
        int submissions(){return action==CurrentRiteText.Action.QUERY?2:5;}
    }
    static RiteTextConfig currentRiteTextConfig(ObjectNode config) {
        StrictJson.require("xar.native-owner-snapshot-config/v42".equals(StrictJson.text(config.get("schema"))),"Explicit v42 Rite text family required");
        String mode=StrictJson.text(config.get("mode"));
        CurrentRiteText.Action action=switch(mode) {
            case "current_rite_text_query"->CurrentRiteText.Action.QUERY;
            case "current_rite_text_set_name"->CurrentRiteText.Action.SET_NAME;
            case "current_rite_text_set_description"->CurrentRiteText.Action.SET_DESCRIPTION;
            default->throw new IllegalArgumentException("Only three exact current Rite text modes");
        };
        var fields=new java.util.HashSet<>(Set.of("schema","mode","owner_descriptor","overall_timeout_seconds","read_timeout_seconds","maximum_frames_per_operation","expected_source_rite_id"));
        if(action!=CurrentRiteText.Action.QUERY)fields.add("text");
        StrictJson.object(config,Set.copyOf(fields));ExactRef.fromJson(config.get("owner_descriptor"));
        StrictJson.integer(config.get("overall_timeout_seconds"),1,600);StrictJson.integer(config.get("read_timeout_seconds"),1,60);
        StrictJson.integer(config.get("maximum_frames_per_operation"),1,65536);
        long rite=StrictJson.integer(config.get("expected_source_rite_id"),0,0xffff_fffeL);
        String text="";
        if(action!=CurrentRiteText.Action.QUERY) {
            // StrictJson.text rejects empty strings; actual empty GUI clear is legal.
            StrictJson.require(config.get("text")!=null&&config.get("text").isTextual(),"Actual typed text string required, empty allowed");
            text=config.get("text").textValue();
        }
        CurrentRiteText.requireText(action,text);
        return new RiteTextConfig(action,rite,text);
    }
    static CoreFrame.Prefix requireCurrentRiteTextCore(CoreFrame frame)throws IOException {
        return requireCurrentRiteCreateCore(frame); // Same exact paused living partial Core facts; no CREATE permission is reused.
    }
    static CurrentRiteTextSource requireCurrentRiteTextQueryFrame(CurrentRiteTextResult frame,CoreFrame.Prefix core,
            long rite,java.math.BigInteger connection)throws IOException {
        if(frame.action()!=CurrentRiteText.Action.QUERY||frame.status()!=CurrentRiteTextResult.Status.AVAILABLE
                ||!frame.cleanupKnown()||frame.effectAttempted()||frame.nativeReturned()||frame.nativeHandled()||frame.claimSequence().signum()!=0
                ||frame.providerGeneration().signum()<=0||frame.querySequence().signum()<=0||frame.source().isEmpty()
                ||frame.factsBefore().filter(core::equals).isEmpty()||frame.owner().isEmpty()
                ||!frame.owner().orElseThrow().connectionGeneration().equals(connection))
            throw new IOException("Actual Rite text query differs from complete original Core/connection/readonly lease");
        var source=frame.source().orElseThrow();
        if(source.sourceRiteId()!=rite||source.actorId()!=core.playedCharacterId())throw new IOException("Actual Rite text Source differs from observed Rite DATA/current actor");
        // Empty/control/richtext Source is actual read DATA; do not apply write limits or trim it.
        return source;
    }
    static void requireCurrentRiteTextDispatchFrame(CurrentRiteTextResult frame,CurrentRiteTextResult query,CurrentRiteText.Action action)throws IOException {
        if(action==CurrentRiteText.Action.QUERY||query.action()!=CurrentRiteText.Action.QUERY||query.status()!=CurrentRiteTextResult.Status.AVAILABLE
                ||frame.action()!=action||frame.status()!=CurrentRiteTextResult.Status.TEXT_DISPATCHED||!frame.cleanupKnown()
                ||!frame.effectAttempted()||!frame.nativeReturned()||frame.nativeHandled()||frame.claimSequence().signum()<=0
                ||!frame.source().equals(query.source())||!frame.factsBefore().equals(query.factsBefore())
                ||!frame.providerGeneration().equals(query.providerGeneration())||!frame.querySequence().equals(query.querySequence())
                ||frame.owner().isEmpty()||query.owner().isEmpty()
                ||!frame.owner().orElseThrow().connectionGeneration().equals(query.owner().orElseThrow().connectionGeneration()))
            throw new IOException("Actual void text ACK differs from immutable beforeSource/Core/lease/spent claim");
    }
    static boolean currentRiteTextReadbackMatches(CurrentRiteTextSource actual,CurrentRiteText.Action action,String requested) {
        if(action==CurrentRiteText.Action.QUERY)throw new IllegalArgumentException("Readback comparison requires one exact requested setter field");
        CurrentRiteText.requireText(action,requested);
        String observed=action==CurrentRiteText.Action.SET_NAME?actual.name():actual.description();
        return Arrays.equals(observed.getBytes(java.nio.charset.StandardCharsets.UTF_8),requested.getBytes(java.nio.charset.StandardCharsets.UTF_8));
    }
    static void initializeCurrentRiteTextResult(ObjectNode result,RiteTextConfig config,String machineId,String mode) {
        result.put("schema","xar.native-owner-current-rite-text/v1").put("mode",mode).put("machine_id",machineId).put("steam_build_id","26785313")
                .put("action",config.action().wire()).put("expected_source_rite_id",config.sourceRiteId()).put("read_calls",0).put("query_calls",0).put("setter_calls",0)
                .put("query_available",false).put("setter_callback_dispatched",false).put("native_returned",false).put("native_handled",false)
                .put("text_applied",false).put("new_date_observed",false).put("physical_save_confirmed",false).put("date_calls",0).put("save_calls",0)
                .put("readback_observed",false).putNull("requested_field_exact_utf8_match").put("readback_status","NOT_OBSERVED");
    }
    private static NativeGameTransport.RiteTextReceived readCurrentRiteTextQuery(NativeGameTransport transport,
            GameSupervisorControl.Descriptor owner,NativeGameTransport.CoreReceived core,NativeObservationPort.TransportSession actualSession,
            long rite,Path output,String name,Instant deadline,ObjectNode result,ObjectNode originals)throws IOException,InterruptedException {
        Instant until=core.validUntil().isBefore(deadline)?core.validUntil():deadline;
        core.requireOriginal(transport,until);
        var read=transport.readCurrentRiteText(core,rite,until);Path queryOutput=Files.createDirectory(output.resolve(name));
        archiveCurrentLetterOutcome(transport,queryOutput,name,read.original(),originals);
        result.put("query_calls",result.path("query_calls").intValue()+1).put("read_calls",result.path("read_calls").intValue()+1);
        if(!(read instanceof NativeGameTransport.RiteTextReceived query))throw new IOException("Actual Rite text query unavailable or UNKNOWN; no replacement/retry");
        until=query.validUntil().isBefore(until)?query.validUntil():until;query.requireOriginal(transport,until);
        requireCurrentDjcAckOwner(transport,owner,query.original(),actualSession);
        var frame=CurrentRiteTextResult.decodeOutcome(query.original());
        if(!frame.equals(query.frame()))throw new IOException("Rite text original ACK differs from private immutable query frame");
        requireCurrentRiteTextQueryFrame(frame,requireCurrentRiteTextCore(core.frame()),rite,actualSession.connectionGeneration());
        originals.set(name+"_original_result",write(queryOutput,"original-result.json",query.original().originalResultToken().orElseThrow().bytes()));
        result.set(name,FullJsonTree.parse(frame.encode().bytes(),SMALL));
        return query;
    }
    private static void runCurrentRiteText(NativeGameTransport transport,GameSupervisorControl.Descriptor owner,NativeLaunchPlan plan,
            RiteTextConfig config,Path output,Instant deadline,ObjectNode result,ObjectNode originals)throws IOException,InterruptedException {
        try {
            if(!(plan.load() instanceof NativeLaunchPlan.SavedGame))throw new IOException("Rite text requires its actual SavedGame owner");
            stage="RITE_TEXT_FRESH_ACTUAL_CORE";
            var before=readCurrentRiteCreateCore(transport,owner,plan,null,output,"core-before-rite-text",deadline,result,originals);
            var prefix=requireCurrentRiteTextCore(before.frame());var actualSession=before.original().custody().orElseThrow().session();
            result.set("session",session(actualSession));
            stage="RITE_TEXT_ACTUAL_PRIVATE_QUERY";
            var query=readCurrentRiteTextQuery(transport,owner,before,actualSession,config.sourceRiteId(),output,"rite-text-query",deadline,result,originals);
            result.put("query_available",true);
            if(config.action()==CurrentRiteText.Action.QUERY)return;
            if(!query.frame().source().orElseThrow().writeAdmissible())throw new IOException("Actual text source writeAdmissible refuses; no setter call");
            stage="RITE_TEXT_PREPARE_ONE_SETTER";
            var prepared=transport.prepareCurrentRiteText(query,config.action(),config.text());
            if(prepared.action()!=config.action()||!prepared.text().equals(config.text())||!prepared.deadline().equals(query.validUntil()))
                throw new IOException("Actual text prepared action/value/deadline changed");
            Path setterOutput=Files.createDirectory(output.resolve("one-rite-text-setter"));
            var intent=StrictJson.object().put("schema","xar.current-rite-text-intent/v1").put("request_id",prepared.requestId())
                    .put("action",prepared.action().wire()).put("text",prepared.text()).put("source_query_request_id",query.original().requestId())
                    .put("original_deadline_utc",prepared.deadline().toString()).put("text_applied",false);
            intent.set("original_outbound",write(setterOutput,"original-request.packet",prepared.originalPacket().value()));
            intent.set("actual_before_query",FullJsonTree.parse(query.frame().encode().bytes(),SMALL));
            originals.set("setter_intent",write(setterOutput,"original-intent.json",FullJsonTree.encode(intent,SMALL)));
            stage="RITE_TEXT_ONE_NATIVE_SETTER";result.put("setter_calls",1);
            var outcome=transport.submitCurrentRiteText(prepared);
            archiveCurrentLetterOutcome(transport,setterOutput,"rite_text_setter",outcome,originals);
            var ack=requireCurrentRiteCreateActualAck(transport,owner,actualSession,outcome,prepared.requestId(),prepared.originalPacket().value());
            var frame=CurrentRiteTextResult.decodeOutcome(ack);
            originals.set("setter_original_result",write(setterOutput,"original-result.json",ack.originalResultToken().orElseThrow().bytes()));
            result.set("setter_result",FullJsonTree.parse(frame.encode().bytes(),SMALL));
            requireCurrentRiteTextDispatchFrame(frame,query.frame(),config.action());
            result.put("setter_callback_dispatched",true).put("native_returned",frame.nativeReturned()).put("native_handled",frame.nativeHandled());
            // The original query was consumed. Never call its unused requireOriginal again.
            stage="RITE_TEXT_INDEPENDENT_POST_SETTER_CORE";
            var after=readCurrentRiteCreateCore(transport,owner,plan,actualSession,output,"core-after-rite-text",deadline,result,originals);
            if(!requireCurrentRiteTextCore(after.frame()).equals(prefix))throw new IOException("Actual actor/date/Core changed after text callback");
            var afterCustody=after.original().custody().orElseThrow();var setterCustody=ack.custody().orElseThrow();
            if(afterCustody.writeEntered().order().compareTo(setterCustody.responseReceived().order())<=0)
                throw new IOException("Text readback Core was not independently written after this setter ACK");
            stage="RITE_TEXT_INDEPENDENT_POST_SETTER_QUERY";
            var readback=readCurrentRiteTextQuery(transport,owner,after,actualSession,config.sourceRiteId(),output,"rite-text-readback-query",deadline,result,originals);
            boolean match=currentRiteTextReadbackMatches(readback.frame().source().orElseThrow(),config.action(),config.text());
            result.put("readback_observed",true).put("requested_field_exact_utf8_match",match).put("readback_status",match?"MATCH":"MISMATCH");
            // Full fresh Source is archived above. Other fields are actual after-data,
            // never filled from beforeSource or constrained to remain unchanged.
            if(!match)throw new IOException("Known DATA text readback mismatch; original setter dispatch retained, no APPLIED or retry");
        } finally {
            archiveNaturalDiagnostics(output,originals,transport.diagnostics());
            var progress=result.deepCopy();progress.set("originals",originals.deepCopy());
            write(output,"current-rite-text-progress.json",FullJsonTree.encode(progress,FullJsonTree.MAXIMUM_BYTES));
        }
    }

    record Zg361ScoreboardConfig() {int submissions(){return 12;}}
    static Zg361ScoreboardConfig currentZg361ScoreboardConfig(ObjectNode config) {
        StrictJson.require("xar.native-owner-snapshot-config/v52".equals(StrictJson.text(config.get("schema")))
                &&"current_zg361_scoreboard_open_close_once".equals(StrictJson.text(config.get("mode"))),"Only explicit v52 independent scoreboard open/close");
        StrictJson.object(config,Set.of("schema","mode","owner_descriptor","overall_timeout_seconds","read_timeout_seconds","maximum_frames_per_operation"));
        ExactRef.fromJson(config.get("owner_descriptor"));StrictJson.integer(config.get("overall_timeout_seconds"),1,600);
        StrictJson.integer(config.get("read_timeout_seconds"),1,60);StrictJson.integer(config.get("maximum_frames_per_operation"),1,65536);
        return new Zg361ScoreboardConfig();
    }
    static CurrentZg361Ae2Source.Scoreboard currentZg361ScoreboardSource(CurrentZg361Ae2Source source)throws IOException {
        if(source.kind()!=CurrentZg361Ae2Source.Kind.SCOREBOARD||source.scoreboard().isEmpty())throw new IOException("Actual typed scoreboard Source required");
        return source.scoreboard().orElseThrow();
    }
    static void requireCurrentZg361ScoreboardAction(CurrentZg361Ae2Source source,CurrentZg361Ae2.Action action)throws IOException {
        currentZg361ScoreboardSource(source);
        if((action!=CurrentZg361Ae2.Action.OPEN_SCOREBOARD&&action!=CurrentZg361Ae2.Action.CLOSE_SCOREBOARD)||!source.actionAdmissible(action))
            throw new IOException("Actual fixed scoreboard DATA refuses this action; no retry or UNKNOWN promotion");
    }
    static GuiWindowFrame.Partial requireCurrentZg361ScoreboardMiddle(GuiWindowFrame frame,CoreFrame.Prefix expected,java.math.BigInteger connection)throws IOException {
        if(!(frame instanceof GuiWindowFrame.Partial partial)||!"zg361_scoreboard_window".equals(partial.requestedWindow())
                ||!partial.ownerWitness().connectionGeneration().equals(connection))throw new IOException("Actual middle Source/session unavailable or changed");
        requireCurrentZg361Ae2SameCore(expected,requireCurrentRiteCreateCore(partial.coreFrame()));
        return partial; // A valid partial/windowAvailable=false is retained DATA.
    }
    static void initializeCurrentZg361ScoreboardResult(ObjectNode result,String machineId) {
        result.put("schema","xar.native-owner-current-zg361-scoreboard-open-close/v1").put("mode","current_zg361_scoreboard_open_close_once")
                .put("machine_id",machineId).put("steam_build_id","26785313").put("read_calls",0).put("query_calls",0).put("action_calls",0)
                .put("date_calls",0).put("save_calls",0).put("new_date_observed",false).put("physical_save_confirmed",false)
                .put("open_callback_dispatched",false).put("close_callback_dispatched",false).put("scoreboard_private_channel_completed",false)
                .put("scoreboard_open_close_pass",false).put("heap_or_memory_fix_pass",false).put("business_contract_pass",false).put("wholeproduct_pass",false);
    }
    private static void readCurrentZg361ScoreboardMiddle(Zg361Ae2Run run,String label)throws IOException,InterruptedException {
        var before=run.core(label);stage="ZG361_SCOREBOARD_INDEPENDENT_MIDDLE";
        var read=run.transport.readGuiWindowReceived(before,"zg361_scoreboard_window",run.until(before));run.archive(label,read.original());
        run.result.put("read_calls",run.result.path("read_calls").intValue()+1).put("query_calls",run.result.path("query_calls").intValue()+1);
        if(!(read instanceof NativeGameTransport.GuiWindowReceived received))throw new IOException("Actual independent middle result unavailable; no replacement or retry");
        received.requireOriginal(run.transport,received.validUntil());var ack=received.original();
        requireCurrentDjcAckOwner(run.transport,run.owner,ack,run.actualSession);
        if(received.validUntil().isAfter(run.until(before))||!GuiWindowFramePublicCodec.decodeOutcome(ack).equals(received.frame()))
            throw new IOException("Middle actual ACK differs from retained frame or original query deadline");
        var frame=received.frame();requireGuiWindowSelection(run.plan,frame);
        run.originals.set(label+"_original_result",write(run.output.resolve(label),"original-result.json",ack.originalResultToken().orElseThrow().bytes()));
        run.result.set(label,FullJsonTree.parse(GuiWindowFramePublicCodec.encode(frame).bytes(),FullJsonTree.MAXIMUM_BYTES));
        var partial=requireCurrentZg361ScoreboardMiddle(frame,run.initial,run.actualSession.connectionGeneration());
        run.result.put(label+"_tree_source_available",true).put(label+"_window_available",partial.windowAvailable());
    }
    private static void runCurrentZg361Scoreboard(NativeGameTransport transport,GameSupervisorControl.Descriptor owner,NativeLaunchPlan plan,
            Path output,Instant deadline,ObjectNode result,ObjectNode originals)throws IOException,InterruptedException {
        var run=new Zg361Ae2Run(transport,owner,plan,output,deadline,result,originals);
        try {
            if(!(plan.load() instanceof NativeLaunchPlan.SavedGame))throw new IOException("Independent scoreboard requires actual Saved-v3 owner");
            var first=run.core("zg361-scoreboard-initial");transport.beginCurrentZg361ScoreboardCase(first);run.bound=true;
            var query=run.query(first,CurrentZg361Ae2.Action.QUERY_SCOREBOARD,"zg361-scoreboard-before-open");
            requireCurrentZg361ScoreboardAction(query.frame().source().orElseThrow(),CurrentZg361Ae2.Action.OPEN_SCOREBOARD);
            run.action(query,CurrentZg361Ae2.Action.OPEN_SCOREBOARD,"zg361-scoreboard-open");result.put("open_callback_dispatched",true);
            readCurrentZg361ScoreboardMiddle(run,"zg361-scoreboard-middle-after-open");
            // A new independent Core/query mints CLOSE's own private lease;
            // the Core used by the middle reader is never reused here.
            query=run.query(CurrentZg361Ae2.Action.QUERY_SCOREBOARD,"zg361-scoreboard-before-close");
            requireCurrentZg361ScoreboardAction(query.frame().source().orElseThrow(),CurrentZg361Ae2.Action.CLOSE_SCOREBOARD);
            run.action(query,CurrentZg361Ae2.Action.CLOSE_SCOREBOARD,"zg361-scoreboard-close");result.put("close_callback_dispatched",true);
            readCurrentZg361ScoreboardMiddle(run,"zg361-scoreboard-middle-after-close");
            query=run.query(CurrentZg361Ae2.Action.QUERY_SCOREBOARD,"zg361-scoreboard-final-independent");
            var actual=currentZg361ScoreboardSource(query.frame().source().orElseThrow());
            result.put("final_modal_found",actual.modalFound()).put("final_modal_visible",actual.modalVisible())
                    .put("final_modal_enabled",actual.modalEnabled()).put("final_complete",actual.complete())
                    .put("scoreboard_private_channel_completed",true);
            // Independent actual DATA is archived. Root evaluates opening/
            // closing and memory evidence; NAV ACK alone does not grant P.
        } finally {
            archiveNaturalDiagnostics(output,originals,transport.diagnostics());
            var progress=result.deepCopy();progress.set("originals",originals.deepCopy());
            write(output,"current-zg361-scoreboard-progress.json",FullJsonTree.encode(progress,FullJsonTree.MAXIMUM_BYTES));
        }
    }

    record Zg361CombinedConfig() { int submissions(){return currentZg361CombinedSubmissionBound();} }
    static Zg361CombinedConfig currentZg361CombinedConfig(ObjectNode config) {
        StrictJson.require("xar.native-owner-snapshot-config/v51".equals(StrictJson.text(config.get("schema")))
                &&"current_zg361_review_ae2_case_once".equals(StrictJson.text(config.get("mode"))),"Only explicit v51 same-receiver review then original AE2 case");
        StrictJson.object(config,Set.of("schema","mode","owner_descriptor","overall_timeout_seconds","read_timeout_seconds","maximum_frames_per_operation"));
        ExactRef.fromJson(config.get("owner_descriptor"));
        StrictJson.integer(config.get("overall_timeout_seconds"),1,900);
        StrictJson.integer(config.get("read_timeout_seconds"),1,60);
        StrictJson.integer(config.get("maximum_frames_per_operation"),1,65536);
        return new Zg361CombinedConfig();
    }
    static int currentZg361CombinedSubmissionBound() {
        // Conservative structural bound. The shared phase-0 list normally
        // removes three from 8+24; do not assume a public GUI value is private
        // permission, or require an extra Close to obtain that shorter path.
        return currentZg361ReviewSubmissionBound(true,true)+currentZg361Ae2SubmissionBound(true,true);
    }
    static int currentZg361OverallTimeoutLimit(ObservationMode mode) {
        return mode==ObservationMode.CURRENT_ZG361_REVIEW_AE2?900:600;
    }
    interface CheckedZg361ReviewAe2Sequence<C> {
        C begin()throws IOException,InterruptedException;
        void review(C sameContext)throws IOException,InterruptedException;
        void payment(C sameContext)throws IOException,InterruptedException;
    }
    static <C> C currentZg361ReviewBeforeAe2(CheckedZg361ReviewAe2Sequence<C> sequence)throws IOException,InterruptedException {
        C context=Objects.requireNonNull(sequence.begin());
        sequence.review(context);
        sequence.payment(context);
        return context;
    }
    static void initializeCurrentZg361CombinedResult(ObjectNode result,String machineId) {
        initializeCurrentZg361Ae2Result(result,machineId);
        result.put("schema","xar.native-owner-current-zg361-review-ae2-case/v1").put("mode","current_zg361_review_ae2_case_once")
                .put("requirements_complete_observed",false).put("review_detail_open_dispatched",false)
                .put("four_localized_labels_observed",false).put("review_readonly_channel_completed",false)
                .put("combined_private_channel_completed",false);
    }
    private record Zg361CombinedContext(Zg361Ae2Run run,NativeGameTransport.CoreReceived first) {}
    private static void runCurrentZg361Combined(NativeGameTransport transport,GameSupervisorControl.Descriptor owner,NativeLaunchPlan plan,
            Path output,Instant deadline,ObjectNode result,ObjectNode originals)throws IOException,InterruptedException {
        var run=new Zg361Ae2Run(transport,owner,plan,output,deadline,result,originals);
        try {
            if(!(plan.load() instanceof NativeLaunchPlan.SavedGame))throw new IOException("Combined review/AE2 requires the actual Saved-v3 owner");
            currentZg361ReviewBeforeAe2(new CheckedZg361ReviewAe2Sequence<Zg361CombinedContext>() {
                public Zg361CombinedContext begin()throws IOException,InterruptedException {
                    var first=run.core("zg361-combined-initial");
                    transport.beginCurrentZg361Ae2CombinedCase(first);run.bound=true;
                    return new Zg361CombinedContext(run,first);
                }
                public void review(Zg361CombinedContext same)throws IOException,InterruptedException {
                    observeCurrentZg361Review(same.run(),same.first());
                }
                public void payment(Zg361CombinedContext same)throws IOException,InterruptedException {
                    // This fresh private controls query is after actual Review
                    // completion in the same Run/session/connection. Original
                    // ensureList skips the already visible shared phase-0 list.
                    var present=same.run().query(CurrentZg361Ae2.Action.QUERY_CONTROLS,"zg361-controls-after-review");
                    completeCurrentZg361Ae2(same.run(),present);
                }
            });
            result.put("combined_private_channel_completed",true);
        } finally {
            archiveNaturalDiagnostics(output,originals,transport.diagnostics());
            var progress=result.deepCopy();progress.set("originals",originals.deepCopy());
            write(output,"current-zg361-review-ae2-progress.json",FullJsonTree.encode(progress,FullJsonTree.MAXIMUM_BYTES));
        }
    }

    private static void observeCurrentZg361Review(Zg361Ae2Run run,NativeGameTransport.CoreReceived first)throws IOException,InterruptedException {
        var result=run.result;
        var controls=run.query(first,CurrentZg361Ae2.Action.QUERY_CONTROLS,"zg361-review-controls");
        if(currentZg361ReviewShouldOpenList(controls.frame().source().orElseThrow()))
            run.action(controls,CurrentZg361Ae2.Action.OPEN_CONTROLS_LIST,"zg361-review-list-open");
        // Always ask the actual review reader next. Hidden old controls do
        // not rule out an already selected complete production review.
        var query=run.query(CurrentZg361Ae2.Action.QUERY_REVIEW_REQUIREMENTS,"zg361-review-before");
        if(currentZg361ReviewNeedsOpen(query.frame().source().orElseThrow())) {
            run.action(query,CurrentZg361Ae2.Action.OPEN_REVIEW_DETAIL,"zg361-review-detail-open");
            result.put("review_detail_open_dispatched",true);
            query=run.query(CurrentZg361Ae2.Action.QUERY_REVIEW_REQUIREMENTS,"zg361-review-after");
        }
        var actual=requireCurrentZg361ReviewComplete(query.frame().source().orElseThrow());
        result.put("requirements_complete_observed",true).put("has_requirements",actual.hasRequirements().orElseThrow())
                .put("requirements_description",actual.requirementsDescription().orElseThrow())
                .put("actual_selected_definition_key",actual.selectedDefinitionKey().orElseThrow())
                .put("review_readonly_channel_completed",true);
        // Description is an actual complete native carrier. Root checks
        // four localized labels independently; no predicted rows/Confirm.
    }
    private static void completeCurrentZg361Ae2(Zg361Ae2Run run,NativeGameTransport.Zg361Ae2Received present)throws IOException,InterruptedException {
        var result=run.result;var transport=run.transport;
        present=ensureCurrentZg361Ae2List(run,present,"zg361-present-list");
        run.action(present,CurrentZg361Ae2.Action.OPEN_PRESENT_DETAIL,"zg361-present-detail");
        present=run.query(CurrentZg361Ae2.Action.QUERY_CONTROLS,"zg361-present-detail-after");
        requireCurrentZg361Ae2Confirmation(present,CurrentZg361Ae2Source.Control.PRESENT);
        run.action(present,CurrentZg361Ae2.Action.CONFIRM_PRESENT,"zg361-present-confirm");
        var event=run.query(CurrentZg361Ae2.Action.QUERY_AE2,"zg361-ae2-before-pay");
        var actual=requireCurrentZg361Ae2ActualTooltips(event.frame().source().orElseThrow(),run.initial);
        result.put("three_actual_full_tooltips_archived",true).put("actual_event_instance",actual.instanceId())
                .put("actual_pay_authored_index",actual.payNowOption().authoredOptionIndex());
        var pay=run.action(event,CurrentZg361Ae2.Action.CHOOSE_PAY_NOW,"zg361-pay-now");
        result.put("pay_now_callback_dispatched",true);
        var after=run.query(CurrentZg361Ae2.Action.QUERY_AE2,"zg361-ae2-after-pay");
        if(pay.actualInstanceId().isEmpty()||pay.actualInstanceId().getAsInt()!=actual.instanceId()
                ||!transport.currentZg361Ae2EventAbsent(pay,after))throw new IOException("Original AE2 instance still present or independent full census absence unqualified");
        result.put("original_instance_absence_observed",true); // Not a global modal/date gate assertion.
        var verify=run.query(CurrentZg361Ae2.Action.QUERY_CONTROLS,"zg361-verify-controls");
        verify=ensureCurrentZg361Ae2List(run,verify,"zg361-verify-list");
        run.action(verify,CurrentZg361Ae2.Action.OPEN_VERIFY_DETAIL,"zg361-verify-detail");
        verify=run.query(CurrentZg361Ae2.Action.QUERY_CONTROLS,"zg361-verify-detail-after");
        requireCurrentZg361Ae2Confirmation(verify,CurrentZg361Ae2Source.Control.VERIFY);
        run.action(verify,CurrentZg361Ae2.Action.CONFIRM_VERIFY,"zg361-verify-confirm");
        result.put("verify_confirmation_callback_dispatched",true);
        run.core("zg361-final-after-verifier");result.put("original_private_channel_completed",true);
        // The original real verifier/log and actual wallet deltas are an
        // independent consumer AND. Never fill their reserved booleans here.
    }

    record Zg361ReviewConfig() { int submissions(){return currentZg361ReviewSubmissionBound(true,true);} }
    static Zg361ReviewConfig currentZg361ReviewConfig(ObjectNode config) {
        StrictJson.require("xar.native-owner-snapshot-config/v50".equals(StrictJson.text(config.get("schema")))
                &&"current_zg361_review_requirements_once".equals(StrictJson.text(config.get("mode"))),"Only explicit v50 fixed review requirements observation");
        StrictJson.object(config,Set.of("schema","mode","owner_descriptor","overall_timeout_seconds","read_timeout_seconds","maximum_frames_per_operation"));
        ExactRef.fromJson(config.get("owner_descriptor"));
        StrictJson.integer(config.get("overall_timeout_seconds"),1,600);
        StrictJson.integer(config.get("read_timeout_seconds"),1,60);
        StrictJson.integer(config.get("maximum_frames_per_operation"),1,65536);
        return new Zg361ReviewConfig();
    }
    static int currentZg361ReviewSubmissionBound(boolean openList,boolean openDetail) {
        // Initial Core/controls + independent Core/review =4. List needs one
        // effect only; detail needs one effect and independent Core/review.
        return 4+(openList?1:0)+(openDetail?3:0);
    }
    static boolean currentZg361ReviewShouldOpenList(CurrentZg361Ae2Source controls) {
        var actual=controls.controls().orElseThrow();
        return !actual.listVisible()&&actual.openListAdmissible();
        // Hidden controls with no open permission do not reject a potentially
        // already selected Review: the independent typed review query follows.
    }
    static void initializeCurrentZg361ReviewResult(ObjectNode result,String machineId) {
        result.put("schema","xar.native-owner-current-zg361-review-requirements/v1").put("mode","current_zg361_review_requirements_once")
                .put("machine_id",machineId).put("steam_build_id","26785313").put("read_calls",0).put("query_calls",0).put("action_calls",0)
                .put("date_calls",0).put("save_calls",0).put("pay_calls",0).put("confirmation_calls",0)
                .put("new_date_observed",false).put("physical_save_confirmed",false).put("requirements_complete_observed",false)
                .put("review_detail_open_dispatched",false).put("four_localized_labels_observed",false)
                .put("business_contract_pass",false).put("wholeproduct_pass",false);
    }
    static CurrentZg361Ae2Source.Review requireCurrentZg361ReviewComplete(CurrentZg361Ae2Source source)throws IOException {
        var actual=source.review().orElseThrow(()->new IOException("Actual typed review Source required"));
        if(!actual.requirementsComplete()||!actual.selectedReview()||!actual.detailVisible()||!actual.actorBound()
                ||!actual.modelComplete()||!actual.rowPresent()
                ||actual.selectedDefinitionKey().filter("zg361_review_now_decision"::equals).isEmpty()
                ||actual.hasRequirements().isEmpty()||actual.requirementsDescription().isEmpty())
            throw new IOException("Actual selected review Description/HasRequirements is incomplete; fixed target metadata is not current selection");
        return actual; // Actual false/empty values are DATA, not missing getters.
    }
    static boolean currentZg361ReviewNeedsOpen(CurrentZg361Ae2Source source)throws IOException {
        var actual=source.review().orElseThrow(()->new IOException("Actual typed review Source required"));
        if(actual.requirementsComplete()) {requireCurrentZg361ReviewComplete(source);return false;}
        if(!actual.openDetailAdmissible())throw new IOException("Actual review getters incomplete and fixed detail is not open-admissible; no retry/fallback");
        return true;
    }
    private static void runCurrentZg361Review(NativeGameTransport transport,GameSupervisorControl.Descriptor owner,NativeLaunchPlan plan,
            Path output,Instant deadline,ObjectNode result,ObjectNode originals)throws IOException,InterruptedException {
        var run=new Zg361Ae2Run(transport,owner,plan,output,deadline,result,originals);
        try {
            if(!(plan.load() instanceof NativeLaunchPlan.SavedGame))throw new IOException("Review observation requires the actual Saved-v3 owner");
            var first=run.core("zg361-review-initial");transport.beginCurrentZg361Ae2Case(first);run.bound=true;
            observeCurrentZg361Review(run,first);
        } finally {
            archiveNaturalDiagnostics(output,originals,transport.diagnostics());
            var progress=result.deepCopy();progress.set("originals",originals.deepCopy());
            write(output,"current-zg361-review-progress.json",FullJsonTree.encode(progress,FullJsonTree.MAXIMUM_BYTES));
        }
    }

    record Zg361Ae2Config() { int submissions(){return currentZg361Ae2SubmissionBound(true,true);} }
    static Zg361Ae2Config currentZg361Ae2Config(ObjectNode config) {
        StrictJson.require("xar.native-owner-snapshot-config/v49".equals(StrictJson.text(config.get("schema")))
                &&"current_zg361_ae2_case_once".equals(StrictJson.text(config.get("mode"))),"Only explicit v49 fixed ZG361 AE2 case");
        StrictJson.object(config,Set.of("schema","mode","owner_descriptor","overall_timeout_seconds","read_timeout_seconds","maximum_frames_per_operation"));
        ExactRef.fromJson(config.get("owner_descriptor"));
        StrictJson.integer(config.get("overall_timeout_seconds"),1,600);
        StrictJson.integer(config.get("read_timeout_seconds"),1,60);
        StrictJson.integer(config.get("maximum_frames_per_operation"),1,65536);
        return new Zg361Ae2Config();
    }
    static int currentZg361Ae2SubmissionBound(boolean openBeforePresent,boolean reopenAfterAbsence) {
        // Base:7 freshCore +6 query +5 effect. Each optional list action adds
        // exactly one effect and an independent freshCore/query. No polling.
        return 18+(openBeforePresent?3:0)+(reopenAfterAbsence?3:0);
    }
    static void requireCurrentZg361Ae2SameCore(CoreFrame.Prefix before,CoreFrame.Prefix after)throws IOException {
        if(!before.equals(after))throw new IOException("ZG361 AE2 requires the same complete actual paused Core; no Date or replacement actor");
    }
    static CurrentZg361Ae2Source requireCurrentZg361Ae2QueryFrame(CurrentZg361Ae2Result f,CurrentZg361Ae2.Action action,
            CoreFrame.Prefix core,java.math.BigInteger connection)throws IOException {
        if(!action.queryOnly()||f.action()!=action||f.status()!=CurrentZg361Ae2Result.Status.AVAILABLE||!f.cleanupKnown()
                ||!f.sourceAvailable()||f.effectAttempted()||f.nativeReturned()||f.nativeHandled()||f.claimSequence().signum()!=0
                ||f.providerGeneration().signum()<=0||f.querySequence().signum()<=0||f.factsBefore().filter(core::equals).isEmpty()
                ||f.owner().filter(o->o.connectionGeneration().equals(connection)).isEmpty()
                ||f.source().filter(s->s.kind()==action.sourceKind()).isEmpty())
            throw new IOException("Actual ZG361 query lost full immutable Source/Core/connection or readonly flags");
        return f.source().orElseThrow(); // Source DATA alone is not a prepared action.
    }
    static CurrentZg361Ae2Result.Status currentZg361Ae2DispatchStatus(CurrentZg361Ae2.Action action)throws IOException {
        if(action.queryOnly())throw new IOException("Readonly AE2 query is not a dispatched effect");
        return switch(action) {
            case CHOOSE_PAY_NOW -> CurrentZg361Ae2Result.Status.SELECTION_DISPATCHED;
            case CONFIRM_PRESENT,CONFIRM_VERIFY -> CurrentZg361Ae2Result.Status.CONFIRMATION_DISPATCHED;
            default -> CurrentZg361Ae2Result.Status.NAVIGATION_DISPATCHED;
        };
    }
    static void requireCurrentZg361Ae2DispatchFrame(CurrentZg361Ae2Result actual,CurrentZg361Ae2Result before,
            CurrentZg361Ae2.Action action,java.math.BigInteger connection)throws IOException {
        if(actual.action()!=action||actual.status()!=currentZg361Ae2DispatchStatus(action)||!actual.cleanupKnown()
                ||!actual.effectAttempted()||!actual.nativeReturned()||actual.nativeHandled()||actual.claimSequence().signum()<=0
                ||!actual.source().equals(before.source())||!actual.factsBefore().equals(before.factsBefore())
                ||!actual.providerGeneration().equals(before.providerGeneration())||!actual.querySequence().equals(before.querySequence())
                ||actual.owner().filter(o->o.connectionGeneration().equals(connection)).isEmpty())
            throw new IOException("THIS AE2 dispatch lost immutable actual beforeSource/Core/lease; no known-refusal or UNKNOWN retry");
    }
    static CurrentZg361Ae2Source.Ae2 requireCurrentZg361Ae2ActualTooltips(CurrentZg361Ae2Source source,CoreFrame.Prefix core)throws IOException {
        var events=source.events().orElseThrow(()->new IOException("Actual AE2 event Source required"));
        var ae2=events.ae2().orElseThrow(()->new IOException("Actual bound AE2 instance absent; no synthetic event"));
        if(!events.censusComplete()||ae2.recipientCharacterId()!=Integer.toUnsignedLong(core.playedCharacterId())
                ||!ae2.phaseBound()||!ae2.namedRootBound()||!ae2.windowVisible()||!ae2.windowEnabled()||!ae2.tooltipsComplete()
                ||ae2.options().size()!=3||ae2.options().stream().anyMatch(o->o.tooltip().isEmpty()))
            throw new IOException("Original three actual full AE2 tooltips/root/recipient/phase not observed");
        // Exact richtext/controls/NUL are archived in the complete Source. Do
        // not normalize, localize, parse amounts, or choose displayed ordinal0.
        return ae2;
    }
    static void initializeCurrentZg361Ae2Result(ObjectNode result,String machineId) {
        result.put("schema","xar.native-owner-current-zg361-ae2-case/v1").put("mode","current_zg361_ae2_case_once")
                .put("machine_id",machineId).put("steam_build_id","26785313").put("read_calls",0).put("query_calls",0).put("action_calls",0)
                .put("date_calls",0).put("save_calls",0).put("new_date_observed",false).put("physical_save_confirmed",false)
                .put("three_actual_full_tooltips_archived",false).put("pay_now_callback_dispatched",false)
                .put("original_instance_absence_observed",false).put("verify_confirmation_callback_dispatched",false)
                .put("original_private_channel_completed",false).put("payment_confirmed",false).put("fixture_verifier_pass",false)
                .put("actual_wallet_deltas_observed",false).put("business_contract_pass",false).put("wholeproduct_pass",false);
    }
    private static final class Zg361Ae2Run {
        final NativeGameTransport transport;final GameSupervisorControl.Descriptor owner;final NativeLaunchPlan plan;
        final Path output;final Instant deadline;final ObjectNode result,originals;
        NativeObservationPort.TransportSession actualSession;CoreFrame.Prefix initial;boolean bound;
        NativeActionPort.AckReceived lastEffect;
        Zg361Ae2Run(NativeGameTransport t,GameSupervisorControl.Descriptor o,NativeLaunchPlan p,Path out,Instant d,ObjectNode r,ObjectNode refs){transport=t;owner=o;plan=p;output=out;deadline=d;result=r;originals=refs;}
        Instant until(NativeGameTransport.CoreReceived c){return c.validUntil().isBefore(deadline)?c.validUntil():deadline;}
        NativeGameTransport.CoreReceived core(String label)throws IOException,InterruptedException {
            var c=readCurrentRiteCreateCore(transport,owner,plan,actualSession,output,label+"-core",deadline,result,originals);
            var prefix=requireCurrentRiteCreateCore(c.frame());
            if(initial==null){initial=prefix;actualSession=c.original().custody().orElseThrow().session();result.set("session",session(actualSession));}
            else requireCurrentZg361Ae2SameCore(initial,prefix);
            if(lastEffect!=null&&c.original().custody().orElseThrow().writeEntered().order()
                    .compareTo(lastEffect.custody().orElseThrow().responseReceived().order())<=0)
                throw new IOException("AE2 independent Core was not written after THIS effect ACK");
            if(bound)transport.requireCurrentZg361Ae2ZeroDay(c);
            return c;
        }
        void archive(String label,NativeActionPort.DispatchOutcome outcome)throws IOException {
            archiveCurrentLetterOutcome(transport,Files.createDirectory(output.resolve(label)),label,outcome,originals);
        }
        void original(String label,NativeActionPort.AckReceived ack,CurrentZg361Ae2Result f)throws IOException {
            originals.set(label+"_original_result",write(output.resolve(label),"original-result.json",ack.originalResultToken().orElseThrow().bytes()));
            result.set(label,FullJsonTree.parse(f.encode().bytes(),FullJsonTree.MAXIMUM_BYTES));
        }
        NativeGameTransport.Zg361Ae2Received query(CurrentZg361Ae2.Action action,String label)throws IOException,InterruptedException {
            return query(core(label),action,label);
        }
        NativeGameTransport.Zg361Ae2Received query(NativeGameTransport.CoreReceived before,CurrentZg361Ae2.Action action,String label)throws IOException,InterruptedException {
            stage="ZG361_AE2_ACTUAL_PRIVATE_QUERY";
            var read=transport.readCurrentZg361Ae2(before,action,until(before));archive(label,read.original());
            result.put("query_calls",result.path("query_calls").intValue()+1).put("read_calls",result.path("read_calls").intValue()+1);
            if(!(read instanceof NativeGameTransport.Zg361Ae2Received q))throw new IOException("Actual ZG361 Source unavailable/UNKNOWN; no synthetic controls/event or retry");
            q.requireOriginal(transport,q.validUntil());requireCurrentDjcAckOwner(transport,owner,q.original(),actualSession);
            var f=CurrentZg361Ae2Result.decodeOutcome(q.original());
            if(!f.equals(q.frame())||q.validUntil().isAfter(until(before)))throw new IOException("AE2 THIS_ACK differs from its private immutable frame/deadline");
            requireCurrentZg361Ae2QueryFrame(f,action,initial,actualSession.connectionGeneration());original(label,q.original(),f);return q;
        }
        NativeGameTransport.Zg361Ae2Prepared action(NativeGameTransport.Zg361Ae2Received query,CurrentZg361Ae2.Action action,String label)throws IOException,InterruptedException {
            query.requireOriginal(transport,query.validUntil());
            if(!query.frame().source().orElseThrow().actionAdmissible(action))throw new IOException("Actual fixed AE2 Source necessary conditions refuse this effect");
            var prepared=transport.prepareCurrentZg361Ae2(query,action);
            if(prepared.action()!=action||!prepared.deadline().equals(query.validUntil()))throw new IOException("AE2 prepared action/original deadline differs");
            Path intentOutput=Files.createDirectory(output.resolve(label+"-intent"));
            var intent=StrictJson.object().put("schema","xar.current-zg361-ae2-intent/v1").put("request_id",prepared.requestId())
                    .put("action",action.wire()).put("original_deadline_utc",prepared.deadline().toString()).put("payment_confirmed",false);
            intent.set("original_outbound",write(intentOutput,"original-request.packet",prepared.originalPacket().value()));
            intent.set("actual_before_query",FullJsonTree.parse(query.frame().encode().bytes(),FullJsonTree.MAXIMUM_BYTES));
            originals.set(label+"_intent",write(intentOutput,"original-intent.json",FullJsonTree.encode(intent,FullJsonTree.MAXIMUM_BYTES)));
            stage="ZG361_AE2_ONCE_FIXED_EFFECT";result.put("action_calls",result.path("action_calls").intValue()+1);
            var outcome=transport.submitCurrentZg361Ae2(prepared);archive(label,outcome);
            var ack=requireCurrentRiteCreateActualAck(transport,owner,actualSession,outcome,prepared.requestId(),prepared.originalPacket().value());
            var f=CurrentZg361Ae2Result.decodeOutcome(ack);original(label,ack,f);
            if(prepared.latestFrame().filter(f::equals).isEmpty())throw new IOException("AE2 actual ACK differs from this prepared action's retained frame");
            requireCurrentZg361Ae2DispatchFrame(f,query.frame(),action,actualSession.connectionGeneration());lastEffect=ack;return prepared;
        }
    }
    private static NativeGameTransport.Zg361Ae2Received ensureCurrentZg361Ae2List(Zg361Ae2Run run,
            NativeGameTransport.Zg361Ae2Received query,String label)throws IOException,InterruptedException {
        var controls=query.frame().source().orElseThrow().controls().orElseThrow();
        if(!controls.listVisible()) {
            if(!controls.openListAdmissible())throw new IOException("AE2 list is hidden and actual fixed open-list is not admissible");
            run.action(query,CurrentZg361Ae2.Action.OPEN_CONTROLS_LIST,label+"-open");
            query=run.query(CurrentZg361Ae2.Action.QUERY_CONTROLS,label+"-after");controls=query.frame().source().orElseThrow().controls().orElseThrow();
        }
        if(!controls.listVisible()||!controls.actorBound()||!controls.modelComplete()||controls.blockedByVisibleModal())
            throw new IOException("Actual complete actor-bound AE2 controls list not independently observed");
        return query;
    }
    private static void requireCurrentZg361Ae2Confirmation(NativeGameTransport.Zg361Ae2Received query,CurrentZg361Ae2Source.Control selected)throws IOException {
        var controls=query.frame().source().orElseThrow().controls().orElseThrow();
        var row=controls.row(selected).orElseThrow(()->new IOException("Actual fixed AE2 control row missing"));
        if(!controls.detailVisible()||!controls.selectedControl().equals(Optional.of(selected))||!row.nativeCanConfirm().orElse(false)||!row.confirmAdmissible())
            throw new IOException("Actual selected AE2 detail does not admit its once confirmation");
    }
    private static void runCurrentZg361Ae2(NativeGameTransport transport,GameSupervisorControl.Descriptor owner,NativeLaunchPlan plan,
            Path output,Instant deadline,ObjectNode result,ObjectNode originals)throws IOException,InterruptedException {
        var run=new Zg361Ae2Run(transport,owner,plan,output,deadline,result,originals);
        try {
            if(!(plan.load() instanceof NativeLaunchPlan.SavedGame))throw new IOException("ZG361 AE2 requires actual Saved-v3 owner");
            var first=run.core("zg361-initial");transport.beginCurrentZg361Ae2Case(first);run.bound=true;
            var present=run.query(first,CurrentZg361Ae2.Action.QUERY_CONTROLS,"zg361-controls-initial");
            completeCurrentZg361Ae2(run,present);
        } finally {
            archiveNaturalDiagnostics(output,originals,transport.diagnostics());
            var progress=result.deepCopy();progress.set("originals",originals.deepCopy());
            write(output,"current-zg361-ae2-progress.json",FullJsonTree.encode(progress,FullJsonTree.MAXIMUM_BYTES));
        }
    }

    record LivingOriginalConfig() { int submissions(){return 85;} }
    static LivingOriginalConfig currentLivingOriginalConfig(ObjectNode config) {
        StrictJson.require("xar.native-owner-snapshot-config/v48".equals(StrictJson.text(config.get("schema")))
                &&"current_living_original_case_once".equals(StrictJson.text(config.get("mode"))),"Only explicit v48 fixed Living original-case mode");
        StrictJson.object(config,Set.of("schema","mode","owner_descriptor","overall_timeout_seconds","read_timeout_seconds","maximum_frames_per_operation"));
        ExactRef.fromJson(config.get("owner_descriptor"));
        StrictJson.integer(config.get("overall_timeout_seconds"),1,600);
        StrictJson.integer(config.get("read_timeout_seconds"),1,60);
        StrictJson.integer(config.get("maximum_frames_per_operation"),1,65536);
        return new LivingOriginalConfig();
    }
    static void requireCurrentLivingSameCore(CoreFrame.Prefix original,CoreFrame.Prefix actual)throws IOException {
        if(!original.equals(actual))throw new IOException("Living original case requires same complete actual actor/date/paused Core; no Date or replacement actor");
    }
    static CurrentLivingInventoryQuerySource requireCurrentLivingInventoryFrame(CurrentLivingInventoryQueryResult frame,
            CoreFrame.Prefix core,java.math.BigInteger connection)throws IOException {
        if(frame.status()!=CurrentLivingInventoryQueryResult.Status.AVAILABLE||!frame.cleanupKnown()||!frame.sourceAvailable()
                ||frame.effectAttempted()||frame.nativeReturned()||frame.nativeHandled()||frame.claimSequence().signum()!=0
                ||frame.providerGeneration().signum()<=0||frame.querySequence().signum()<=0
                ||frame.factsBefore().filter(core::equals).isEmpty()
                ||frame.owner().filter(o->o.connectionGeneration().equals(connection)).isEmpty()||frame.source().isEmpty())
            throw new IOException("Actual complete readonly Living inventory/Core/connection required");
        var s=frame.source().orElseThrow();
        if(s.actorFullId()!=Integer.toUnsignedLong(core.playedCharacterId())||!s.completeInventory()||!s.sampledTwice())
            throw new IOException("Living inventory differs from actual full actor or complete two samples");
        return s; // Fixed references are DATA, never a prepared action or caller authority.
    }
    static CurrentLivingInventoryQuerySource.Artifact currentLivingArtifact(CurrentLivingInventoryQuerySource source,long id)throws IOException {
        var all=source.artifacts().stream().filter(a->a.fullId()==id).toList();
        if(all.size()!=1||all.get(0).ownerFullId()!=source.actorFullId())throw new IOException("Actual unique owned full Artifact ID absent");
        return all.get(0);
    }
    static long currentLivingReference(CurrentLivingInventoryQuerySource source,CurrentLivingInventoryQuerySource.ReferenceRole role)throws IOException {
        var all=source.fixedReferences().stream().filter(r->r.role()==role).toList();
        if(all.size()!=1||all.get(0).state()!=CurrentLivingInventoryQuerySource.ReferenceState.ARTIFACT
                ||all.get(0).scopeKind()!=36||all.get(0).artifactFullId().isEmpty())throw new IOException("Actual fixed kind36 Artifact reference unavailable");
        return all.get(0).artifactFullId().orElseThrow();
    }
    record LivingOriginalBindings(long target,List<Long> materials) {LivingOriginalBindings{materials=List.copyOf(materials);}}
    static LivingOriginalBindings currentLivingOriginalBindings(CurrentLivingInventoryQuerySource actual)throws IOException {
        long target=currentLivingReference(actual,CurrentLivingInventoryQuerySource.ReferenceRole.FIXTURE_TARGET);
        currentLivingArtifact(actual,target);var materials=new java.util.ArrayList<Long>();
        for(var role:List.of(CurrentLivingInventoryQuerySource.ReferenceRole.FIXTURE_MATERIAL_COMMON,
                CurrentLivingInventoryQuerySource.ReferenceRole.FIXTURE_MATERIAL_MASTERWORK,
                CurrentLivingInventoryQuerySource.ReferenceRole.FIXTURE_MATERIAL_FAMED,
                CurrentLivingInventoryQuerySource.ReferenceRole.FIXTURE_MATERIAL_ILLUSTRIOUS)) {
            long id=currentLivingReference(actual,role);currentLivingArtifact(actual,id);materials.add(id);
        }
        var all=new java.util.HashSet<>(materials);all.add(target);
        if(all.size()!=5)throw new IOException("Original Living target and four materials must be five distinct actual owned full IDs");
        return new LivingOriginalBindings(target,materials); // Native private Raw/owner still authorizes every action.
    }
    static List<Long> currentLivingNumeric(CurrentLivingInventoryQuerySource.Artifact actual)throws IOException {
        var values=new java.util.ArrayList<Long>();
        for(var n:actual.numeric()) {
            if(n.state()!=CurrentLivingInventoryQuerySource.NumericState.NUMERIC||n.scopeKind()!=1||n.raw().isEmpty())
                throw new IOException("All four actual signed64 fixed5 numeric observations are required");
            values.add(n.raw().orElseThrow());
        }
        if(values.size()!=4)throw new IOException("Four actual numeric observations required");return List.copyOf(values);
    }
    static void requireCurrentLivingNumbers(CurrentLivingInventoryQuerySource source,long target,int stage)throws IOException {
        long[] levels={1,2,3,4,6},xp={92,72,72,272,572},sequence={0,1,2,3,5};
        if(stage<0||stage>=levels.length)throw new IOException("Only the fixed original four-rarity checkpoints");
        var expected=List.of(Math.multiplyExact(levels[stage],100000L),Math.multiplyExact(xp[stage],100000L),0L,Math.multiplyExact(sequence[stage],100000L));
        if(source.numericDenominator()!=100000L||!currentLivingNumeric(currentLivingArtifact(source,target)).equals(expected))
            throw new IOException("Actual numeric4 readback differs from original fixed checkpoint; no arithmetic or Source-body substitute");
    }
    static void requireCurrentLivingEquipped(CurrentLivingInventoryQuerySource source,long target)throws IOException {
        var artifact=currentLivingArtifact(source,target);
        if(!artifact.equipped()||source.weaponSlot().isEmpty())throw new IOException("Actual target must be independently equipped in weapon slot");
        var slot=source.slots().get(source.weaponSlot().orElseThrow());
        if(!slot.key().equals("weapon")||slot.artifactFullId().filter(id->id==target).isEmpty())
            throw new IOException("Actual canonical weapon slot does not independently contain this full target");
    }
    private static java.util.Map<Long,CurrentLivingInventoryQuerySource.Artifact> currentLivingArtifactMap(CurrentLivingInventoryQuerySource source) {
        return source.artifacts().stream().collect(java.util.stream.Collectors.toMap(CurrentLivingInventoryQuerySource.Artifact::fullId,java.util.function.Function.identity()));
    }
    private static java.util.Map<String,Optional<Long>> currentLivingSlotMap(CurrentLivingInventoryQuerySource source) {
        return source.slots().stream().collect(java.util.stream.Collectors.toMap(CurrentLivingInventoryQuerySource.Slot::key,CurrentLivingInventoryQuerySource.Slot::artifactFullId));
    }
    static void requireCurrentLivingCancelConserved(CurrentLivingInventoryQuerySource before,CurrentLivingInventoryQuerySource after,long target,long material)throws IOException {
        currentLivingArtifact(before,target);currentLivingArtifact(before,material);currentLivingArtifact(after,target);currentLivingArtifact(after,material);
        if(before.actorFullId()!=after.actorFullId()||!currentLivingArtifactMap(before).equals(currentLivingArtifactMap(after))
                ||!currentLivingSlotMap(before).equals(currentLivingSlotMap(after)))throw new IOException("Actual canceled review changed complete artifact/numeric4/slot DATA");
        // Storage order and stale fixed references are archived, not invented business invariants.
    }
    static void requireCurrentLivingConsumed(CurrentLivingInventoryQuerySource before,CurrentLivingInventoryQuerySource after,long target,long material,int stage)throws IOException {
        if(target==material||before.actorFullId()!=after.actorFullId())throw new IOException("Distinct actual target/material and same actor required");
        currentLivingArtifact(before,material);var old=currentLivingArtifact(before,target);var now=currentLivingArtifact(after,target);
        if(after.artifacts().stream().anyMatch(a->a.fullId()==material))throw new IOException("Actual selected material still present in complete inventory");
        if(old.ownerFullId()!=now.ownerFullId()||!old.typeKey().equals(now.typeKey())||old.equipped()!=now.equipped())
            throw new IOException("Actual same target owner/type/equipment identity changed");
        var left=new java.util.HashMap<>(currentLivingArtifactMap(before));left.remove(target);left.remove(material);
        var right=new java.util.HashMap<>(currentLivingArtifactMap(after));right.remove(target);
        if(!left.equals(right)||!currentLivingSlotMap(before).equals(currentLivingSlotMap(after)))throw new IOException("Unrelated actual artifacts/slots changed across consumption");
        requireCurrentLivingNumbers(after,target,stage);requireCurrentLivingEquipped(after,target);
        // A retained fixture-material variable may still contain its old full ID: it is not present/owned proof.
    }
    static void initializeCurrentLivingOriginalResult(ObjectNode result,String machineId) {
        result.put("schema","xar.native-owner-current-living-original-case/v1").put("mode","current_living_original_case_once")
                .put("machine_id",machineId).put("steam_build_id","26785313").put("read_calls",0).put("entry_action_calls",0).put("ui_action_calls",0)
                .put("date_calls",0).put("save_calls",0).put("new_date_observed",false).put("physical_save_confirmed",false)
                .put("cancel_conservation_observed",false).put("four_rarity_numeric_readbacks_observed",false).put("original_private_channel_completed",false)
                .put("actual_preview_fulltext_archived",false).put("detail_getter_fulltext_archived",false)
                .put("diet_flag_independently_observed",false).put("preview_number_independently_parsed",false)
                .put("pixels_observed",false).put("original_five_save_png_contract_pass",false).put("wholeproduct_pass",false);
    }
    private static final class LivingOriginalRun {
        final NativeGameTransport transport;final GameSupervisorControl.Descriptor owner;final NativeLaunchPlan plan;
        final Path output;final Instant deadline;final ObjectNode result,originals;
        NativeObservationPort.TransportSession actualSession;CoreFrame.Prefix initial;boolean bound;
        LivingOriginalRun(NativeGameTransport t,GameSupervisorControl.Descriptor o,NativeLaunchPlan p,Path out,Instant d,ObjectNode r,ObjectNode refs){transport=t;owner=o;plan=p;output=out;deadline=d;result=r;originals=refs;}
        Instant until(NativeGameTransport.CoreReceived c){return c.validUntil().isBefore(deadline)?c.validUntil():deadline;}
        NativeGameTransport.CoreReceived core(String label)throws IOException,InterruptedException {
            var c=readCurrentRiteCreateCore(transport,owner,plan,actualSession,output,label+"-core",deadline,result,originals);
            var prefix=requireCurrentRiteCreateCore(c.frame());
            if(initial==null){initial=prefix;actualSession=c.original().custody().orElseThrow().session();result.set("session",session(actualSession));}
            else requireCurrentLivingSameCore(initial,prefix);
            if(bound)transport.requireCurrentLivingZeroDay(c);
            return c;
        }
        void archive(String label,NativeActionPort.DispatchOutcome outcome)throws IOException {
            archiveCurrentLetterOutcome(transport,Files.createDirectory(output.resolve(label)),label,outcome,originals);
        }
        void original(String label,NativeActionPort.AckReceived ack,byte[] encoded)throws IOException {
            originals.set(label+"_original_result",write(output.resolve(label),"original-result.json",ack.originalResultToken().orElseThrow().bytes()));
            result.set(label,FullJsonTree.parse(encoded,FullJsonTree.MAXIMUM_BYTES));
        }
        void intent(String label,String id,Instant until,byte[] packet)throws IOException {
            Path out=Files.createDirectory(output.resolve(label+"-intent"));
            var intent=StrictJson.object().put("schema","xar.current-living-original-intent/v1").put("request_id",id)
                    .put("original_deadline_utc",until.toString()).put("physical_save_confirmed",false);
            intent.set("original_outbound",write(out,"original-request.packet",packet));
            originals.set(label+"_intent",write(out,"original-intent.json",FullJsonTree.encode(intent,SMALL)));
        }
        NativeGameTransport.LivingInventoryQueryReceived inventory(String label)throws IOException,InterruptedException {
            var before=core(label);stage="LIVING_ACTUAL_COMPLETE_INVENTORY";
            var read=transport.readCurrentLivingInventoryQuery(before,until(before));archive(label,read.original());result.put("read_calls",result.path("read_calls").intValue()+1);
            if(!(read instanceof NativeGameTransport.LivingInventoryQueryReceived q))throw new IOException("Actual complete Living inventory unavailable/UNKNOWN; no replacement or retry");
            q.requireOriginal(transport,q.validUntil());requireCurrentDjcAckOwner(transport,owner,q.original(),actualSession);
            var f=CurrentLivingInventoryQueryResult.decodeOutcome(q.original());
            if(!f.equals(q.frame())||q.validUntil().isAfter(until(before)))throw new IOException("Inventory THIS_ACK/private immutable query deadline differs");
            requireCurrentLivingInventoryFrame(f,initial,actualSession.connectionGeneration());original(label,q.original(),f.encode().bytes());return q;
        }
        NativeGameTransport.LivingEntryReceived entry(CurrentLivingEntry.Action action,String label)throws IOException,InterruptedException {
            var before=core(label);stage="LIVING_FIXED_ENTRY_QUERY";
            var read=transport.readCurrentLivingEntry(before,action,until(before));archive(label,read.original());result.put("read_calls",result.path("read_calls").intValue()+1);
            if(!(read instanceof NativeGameTransport.LivingEntryReceived q))throw new IOException("Actual Living Entry unavailable/UNKNOWN; no assumed hidden model");
            q.requireOriginal(transport,q.validUntil());requireCurrentDjcAckOwner(transport,owner,q.original(),actualSession);
            var f=CurrentLivingEntryResult.decodeOutcome(q.original());
            if(!f.equals(q.frame())||q.validUntil().isAfter(until(before))||f.action()!=action||!action.queryOnly()
                    ||f.status()!=CurrentLivingEntryResult.Status.AVAILABLE||!f.cleanupKnown()||f.claimSequence().signum()!=0||f.effectAttempted()||f.nativeReturned()
                    ||f.providerGeneration().signum()<=0||f.querySequence().signum()<=0||f.factsBefore().filter(initial::equals).isEmpty()
                    ||f.owner().filter(o->o.connectionGeneration().equals(actualSession.connectionGeneration())).isEmpty()
                    ||f.source().filter(s->s.actorFullId()==Integer.toUnsignedLong(initial.playedCharacterId())&&s.kind()==action.sourceKind()&&s.sampledTwice()).isEmpty())
                throw new IOException("Living Entry query lost exact Source/actor/Core/connection/original receipt");
            original(label,q.original(),f.encode().bytes());return q;
        }
        NativeGameTransport.LivingUiReceived ui(CurrentLivingUi.Action action,String label)throws IOException,InterruptedException {
            var before=core(label);stage="LIVING_ACTUAL_FIXED_UI_QUERY";
            var read=transport.readCurrentLivingUi(before,action,until(before));archive(label,read.original());result.put("read_calls",result.path("read_calls").intValue()+1);
            if(!(read instanceof NativeGameTransport.LivingUiReceived q))throw new IOException("Actual Living UI unavailable/UNKNOWN; no synthetic event/view or retry");
            q.requireOriginal(transport,q.validUntil());requireCurrentDjcAckOwner(transport,owner,q.original(),actualSession);
            var f=CurrentLivingUiResult.decodeOutcome(q.original());
            if(!f.equals(q.frame())||q.validUntil().isAfter(until(before))||f.action()!=action||!action.queryOnly()
                    ||f.status()!=CurrentLivingUiResult.Status.AVAILABLE||!f.cleanupKnown()||f.claimSequence().signum()!=0||f.effectAttempted()||f.nativeReturned()
                    ||f.providerGeneration().signum()<=0||f.querySequence().signum()<=0||f.factsBefore().filter(initial::equals).isEmpty()
                    ||f.owner().filter(o->o.connectionGeneration().equals(actualSession.connectionGeneration())).isEmpty()
                    ||f.source().filter(s->s.actorFullId()==Integer.toUnsignedLong(initial.playedCharacterId())&&s.kind()==action.sourceKind()&&s.sampledTwice()).isEmpty())
                throw new IOException("Living UI query lost complete Source/actor/Core/connection/original receipt");
            original(label,q.original(),f.encode().bytes());return q;
        }
        void entryAction(NativeGameTransport.LivingEntryReceived query,CurrentLivingEntry.Action action,String label)throws IOException,InterruptedException {
            query.requireOriginal(transport,query.validUntil());var prepared=transport.prepareCurrentLivingEntry(query,action);
            if(!prepared.deadline().equals(query.validUntil()))throw new IOException("Original Entry action deadline changed");
            intent(label,prepared.requestId(),prepared.deadline(),prepared.originalPacket().value());
            result.put("entry_action_calls",result.path("entry_action_calls").intValue()+1);
            var outcome=transport.submitCurrentLivingEntry(prepared);archive(label,outcome);
            var ack=requireCurrentRiteCreateActualAck(transport,owner,actualSession,outcome,prepared.requestId(),prepared.originalPacket().value());
            var f=CurrentLivingEntryResult.decodeOutcome(ack);original(label,ack,f.encode().bytes());var old=query.frame();
            if(prepared.latestFrame().filter(f::equals).isEmpty()||f.action()!=action||f.status()!=CurrentLivingEntryResult.Status.DISPATCHED
                    ||!f.cleanupKnown()||!f.effectAttempted()||!f.nativeReturned()||f.claimSequence().signum()<=0
                    ||!f.source().equals(old.source())||!f.factsBefore().equals(old.factsBefore())||!f.providerGeneration().equals(old.providerGeneration())
                    ||!f.querySequence().equals(old.querySequence())||f.owner().filter(o->o.connectionGeneration().equals(actualSession.connectionGeneration())).isEmpty())
                throw new IOException("THIS Entry dispatch lost actual immutable beforeSource/Core/lease; never replay known refusal/UNKNOWN");
        }
        NativeGameTransport.LivingUiReceived uiActionThenQuery(NativeGameTransport.LivingUiReceived query,CurrentLivingUi.Action action,
                CurrentLivingUi.Action afterAction,String label)throws IOException,InterruptedException {
            query.requireOriginal(transport,query.validUntil());var prepared=transport.prepareCurrentLivingUi(query,action);
            if(!prepared.deadline().equals(query.validUntil()))throw new IOException("Original UI action deadline changed");
            intent(label,prepared.requestId(),prepared.deadline(),prepared.originalPacket().value());
            result.put("ui_action_calls",result.path("ui_action_calls").intValue()+1);
            var outcome=transport.submitCurrentLivingUi(prepared);archive(label,outcome);
            var ack=requireCurrentRiteCreateActualAck(transport,owner,actualSession,outcome,prepared.requestId(),prepared.originalPacket().value());
            var f=CurrentLivingUiResult.decodeOutcome(ack);original(label,ack,f.encode().bytes());var old=query.frame();
            if(prepared.latestFrame().filter(f::equals).isEmpty()||f.action()!=action||f.status()!=CurrentLivingUiResult.Status.DISPATCHED
                    ||!f.cleanupKnown()||!f.effectAttempted()||!f.nativeReturned()||f.claimSequence().signum()<=0
                    ||!f.source().equals(old.source())||!f.factsBefore().equals(old.factsBefore())||!f.providerGeneration().equals(old.providerGeneration())
                    ||!f.querySequence().equals(old.querySequence())||f.owner().filter(o->o.connectionGeneration().equals(actualSession.connectionGeneration())).isEmpty())
                throw new IOException("THIS UI dispatch lost actual immutable beforeSource/Core/lease; never replay known refusal/UNKNOWN");
            var after=ui(afterAction,label+"-after");
            if(action.sourceKind()==CurrentLivingUiSource.Kind.EVENTS) {
                if(prepared.actualInstanceId().isEmpty()||!transport.currentLivingEventAbsent(prepared,after))
                    throw new IOException("Original actual event instance still present or independent complete absence unqualified");
                result.put(label+"_original_instance_absent",true); // Not event_closed or global modal/date gate clearance.
            }
            return after;
        }
        void ensureView(boolean inventory,long payload,String label)throws IOException,InterruptedException {
            var queryAction=inventory?CurrentLivingEntry.Action.QUERY_INVENTORY_ENTRY:CurrentLivingEntry.Action.QUERY_DETAIL_ENTRY;
            var action=inventory?CurrentLivingEntry.Action.OPEN_INVENTORY:CurrentLivingEntry.Action.OPEN_DETAIL;
            var query=entry(queryAction,label+"-before");var s=query.frame().source().orElseThrow();
            var view=(inventory?s.inventory():s.detail()).orElseThrow();
            if(!view.visible()) {entryAction(query,action,label+"-open");query=entry(queryAction,label+"-after");s=query.frame().source().orElseThrow();view=(inventory?s.inventory():s.detail()).orElseThrow();}
            if(!view.windowFound()||!view.visible()||!view.enabled()||!view.payloadBound()||view.expectedPayloadFullId()!=payload)
                throw new IOException("Actual bound Inventory/Details view did not independently show the original actor/artifact payload");
        }
    }
    private static CurrentLivingUiSource.EventBinding requireCurrentLivingEvent(NativeGameTransport.LivingUiReceived query,
            CurrentLivingUi.Action action,String definition,long target,Optional<Long> material)throws IOException {
        var source=query.frame().source().orElseThrow();var census=source.events().orElseThrow();
        var choices=census.fixedActions().stream().filter(a->a.action()==action&&a.admissible()).toList();
        if(choices.size()!=1)throw new IOException("Actual unique fixed Living action not admissible");
        var choice=choices.get(0);var events=census.events().stream().filter(e->e.instanceId()==choice.instanceId()).toList();
        var bindings=census.bindings().stream().filter(b->b.instanceId()==choice.instanceId()).toList();
        if(events.size()!=1||bindings.size()!=1)throw new IOException("Original Living event/binding not unique in complete census");
        var event=events.get(0);var binding=bindings.get(0);
        if(!census.censusComplete()||!census.completeBindings()||!event.definitionKey().equals(definition)||!binding.definitionKey().equals(definition)
                ||!event.windowVisible()||!event.windowEnabled()||!event.namedRootBound()||event.recipientCharacterId()!=binding.recipientId()
                ||Integer.toUnsignedLong(binding.recipientId())!=source.actorFullId()||!binding.targetOwned()||!binding.completeNamedScopes()||!binding.sampledTwice()
                ||binding.target().artifactFullId().filter(id->id==target).isEmpty())throw new IOException("Actual fixed event lost original held target/recipient/visible window binding");
        if(material.isPresent()&&(!binding.materialRequired()||!binding.materialOwned()||!binding.material().artifactFullId().equals(material)))
            throw new IOException("Actual review material does not match its distinct originally observed fixture identity");
        var options=event.options().stream().filter(o->o.authoredOptionIndex()==choice.authoredOptionIndex()).toList();
        if(options.size()!=1||!options.get(0).nativeCanSelect()||options.get(0).text().isEmpty())throw new IOException("Actual fixed event option lacks actual Can/text");
        // Original rich text is already fully archived in this query result. No trim, localization lookup or numeric parsing is substituted.
        return binding;
    }
    private static NativeGameTransport.LivingEntryReceived openCurrentLivingManage(LivingOriginalRun run)throws IOException,InterruptedException {
        var q=run.entry(CurrentLivingEntry.Action.QUERY_MANAGE,"living-manage-before");var m=q.frame().source().orElseThrow().manage().orElseThrow();
        if(!m.listVisible()&&!m.detailVisible()) {run.entryAction(q,CurrentLivingEntry.Action.OPEN_MANAGE_LIST,"living-manage-list");q=run.entry(CurrentLivingEntry.Action.QUERY_MANAGE,"living-manage-after-list");m=q.frame().source().orElseThrow().manage().orElseThrow();}
        if(!m.detailVisible()||!m.selectedDecisionKey().equals(Optional.of(CurrentLivingEntry.MANAGE_DECISION))) {
            run.entryAction(q,CurrentLivingEntry.Action.OPEN_MANAGE_DETAIL,"living-manage-detail");q=run.entry(CurrentLivingEntry.Action.QUERY_MANAGE,"living-manage-after-detail");m=q.frame().source().orElseThrow().manage().orElseThrow();
        }
        if(!m.ownerBound()||!m.detailVisible()||!m.detailEnabled()||!m.selectedDecisionKey().equals(Optional.of(CurrentLivingEntry.MANAGE_DECISION))
                ||!m.nativeCanConfirm().orElse(false)||!m.confirmAdmissible())throw new IOException("Actual fixed manage detail does not admit one normal confirmation");
        return q;
    }
    private static void runCurrentLivingOriginal(NativeGameTransport transport,GameSupervisorControl.Descriptor owner,NativeLaunchPlan plan,
            Path output,Instant deadline,ObjectNode result,ObjectNode originals)throws IOException,InterruptedException {
        var run=new LivingOriginalRun(transport,owner,plan,output,deadline,result,originals);
        try {
            if(!(plan.load() instanceof NativeLaunchPlan.SavedGame))throw new IOException("Original Living slice requires actual SavedGame owner");
            var initial=run.inventory("living-inventory-initial");var inventory=initial.frame().source().orElseThrow();
            var binding=currentLivingOriginalBindings(inventory);long target=binding.target();
            requireCurrentLivingNumbers(inventory,target,0);result.put("actual_target_full_id",target);
            transport.beginCurrentLivingOriginalCase(initial);run.bound=true;
            run.ensureView(true,inventory.actorFullId(),"living-inventory-entry");
            var weapon=run.ui(CurrentLivingUi.Action.QUERY_WEAPON,"living-weapon-before");var w=weapon.frame().source().orElseThrow().weapon().orElseThrow();
            if(w.targetFullId()!=target)throw new IOException("Actual weapon query rebound the captured full target");
            if(!w.targetEquipped()) {
                if(!w.weaponSelected())weapon=run.uiActionThenQuery(weapon,CurrentLivingUi.Action.SELECT_WEAPON,CurrentLivingUi.Action.QUERY_WEAPON,"living-select-weapon");
                weapon=run.uiActionThenQuery(weapon,CurrentLivingUi.Action.EQUIP_TARGET,CurrentLivingUi.Action.QUERY_WEAPON,"living-equip-target");
            }
            inventory=run.inventory("living-inventory-equipped").frame().source().orElseThrow();requireCurrentLivingEquipped(inventory,target);requireCurrentLivingNumbers(inventory,target,0);
            var manage=openCurrentLivingManage(run);run.entryAction(manage,CurrentLivingEntry.Action.CONFIRM_MANAGE,"living-manage-confirm");
            var events=run.ui(CurrentLivingUi.Action.QUERY_EVENTS,"living-events-after-manage");
            requireCurrentLivingEvent(events,CurrentLivingUi.Action.OPEN_TUTORIAL,"xalw.12",target,Optional.empty());
            events=run.uiActionThenQuery(events,CurrentLivingUi.Action.OPEN_TUTORIAL,CurrentLivingUi.Action.QUERY_EVENTS,"living-tutorial-open");
            long common=binding.materials().get(0);
            requireCurrentLivingEvent(events,CurrentLivingUi.Action.FEED_COMMON,"xalw.10",target,Optional.empty());
            events=run.uiActionThenQuery(events,CurrentLivingUi.Action.FEED_COMMON,CurrentLivingUi.Action.QUERY_EVENTS,"living-common-first-preview");
            int canceledReview=requireCurrentLivingEvent(events,CurrentLivingUi.Action.CANCEL_REVIEW,"xalw.11",target,Optional.of(common)).instanceId();
            var beforeCancel=run.inventory("living-inventory-before-cancel").frame().source().orElseThrow();
            events=run.uiActionThenQuery(events,CurrentLivingUi.Action.CANCEL_REVIEW,CurrentLivingUi.Action.QUERY_EVENTS,"living-common-cancel");
            var afterCancel=run.inventory("living-inventory-after-cancel").frame().source().orElseThrow();
            requireCurrentLivingCancelConserved(beforeCancel,afterCancel,target,common);requireCurrentLivingNumbers(afterCancel,target,0);result.put("cancel_conservation_observed",true);
            requireCurrentLivingEvent(events,CurrentLivingUi.Action.FEED_COMMON,"xalw.10",target,Optional.empty());
            events=run.uiActionThenQuery(events,CurrentLivingUi.Action.FEED_COMMON,CurrentLivingUi.Action.QUERY_EVENTS,"living-common-new-preview");
            var review=requireCurrentLivingEvent(events,CurrentLivingUi.Action.CONFIRM_REVIEW,"xalw.11",target,Optional.of(common));
            if(review.instanceId()==canceledReview)throw new IOException("Canceled review instance cannot become the fresh review/confirmation");
            result.put("actual_preview_fulltext_archived",true);
            events=run.uiActionThenQuery(events,CurrentLivingUi.Action.CONFIRM_REVIEW,CurrentLivingUi.Action.QUERY_EVENTS,"living-common-confirm");
            inventory=run.inventory("living-inventory-common-after").frame().source().orElseThrow();requireCurrentLivingConsumed(afterCancel,inventory,target,common,1);
            var rarities=List.of(CurrentLivingUi.Action.FEED_MASTERWORK,CurrentLivingUi.Action.FEED_FAMED,CurrentLivingUi.Action.FEED_ILLUSTRIOUS);
            for(int index=0;index<rarities.size();index++) {
                var action=rarities.get(index);long material=binding.materials().get(index+1);String label="living-rarity-"+(index+2);var before=inventory;
                currentLivingArtifact(before,material);requireCurrentLivingEvent(events,action,"xalw.10",target,Optional.empty());
                events=run.uiActionThenQuery(events,action,CurrentLivingUi.Action.QUERY_EVENTS,label+"-preview");
                requireCurrentLivingEvent(events,CurrentLivingUi.Action.CONFIRM_REVIEW,"xalw.11",target,Optional.of(material));
                events=run.uiActionThenQuery(events,CurrentLivingUi.Action.CONFIRM_REVIEW,CurrentLivingUi.Action.QUERY_EVENTS,label+"-confirm");
                inventory=run.inventory(label+"-inventory-after").frame().source().orElseThrow();requireCurrentLivingConsumed(before,inventory,target,material,index+2);
            }
            result.put("four_rarity_numeric_readbacks_observed",true);
            // Actual appended UI14 enum: .10/count10/index9; no caller action/key selector.
            var close=CurrentLivingUi.Action.CLOSE_MANAGEMENT;
            requireCurrentLivingEvent(events,close,"xalw.10",target,Optional.empty());
            events=run.uiActionThenQuery(events,close,CurrentLivingUi.Action.QUERY_EVENTS,"living-management-close");
            run.ensureView(false,target,"living-detail-entry");
            var detail=run.ui(CurrentLivingUi.Action.QUERY_DETAIL,"living-final-detail").frame().source().orElseThrow().detail().orElseThrow();
            if(detail.targetFullId()!=target||!detail.windowFound()||!detail.visible()||!detail.enabled()||!detail.targetBound()
                    ||detail.modifierEffectsText().isEmpty()||detail.customEffectsText().isEmpty()||detail.descriptionText().isEmpty())
                throw new IOException("Final actual target-bound detail lacks one of three complete engine getter texts; no fake empty/static replacement");
            result.put("detail_getter_fulltext_archived",true); // Actual strings including empty/NUL/control remain in the immutable query.
            var finalInventory=run.inventory("living-inventory-final").frame().source().orElseThrow();
            requireCurrentLivingNumbers(finalInventory,target,4);requireCurrentLivingEquipped(finalInventory,target);
            for(long material:binding.materials())if(finalInventory.artifacts().stream().anyMatch(a->a.fullId()==material))
                throw new IOException("An original consumed material is present in the final complete owned inventory");
            result.put("original_private_channel_completed",true).put("original_text_and_diet_business_review_pending",true);
            // Root combines actual preview/detail strings and original business/log evidence separately.
            // This controller never promotes Source fixtures, whole-product, pixels, diet flags or five physical Saves.
        } finally {
            archiveNaturalDiagnostics(output,originals,transport.diagnostics());var progress=result.deepCopy();progress.set("originals",originals.deepCopy());
            write(output,"current-living-original-progress.json",FullJsonTree.encode(progress,FullJsonTree.MAXIMUM_BYTES));
        }
    }
    enum RmtmMode { QUERY_ROLE, QUERY_DECISION, ORIGINAL_CASE_ONCE, THRESHOLD_50_51_ONCE }
    record RmtmConfig(RmtmMode mode,int maximumStatusPolls,long statusPollDelayMillis) {
        boolean queryOnly(){return mode==RmtmMode.QUERY_ROLE||mode==RmtmMode.QUERY_DECISION;}
        int submissions(){return switch(mode){case QUERY_ROLE,QUERY_DECISION->2;case THRESHOLD_50_51_ONCE->Math.addExact(82,Math.multiplyExact(4,maximumStatusPolls));
            case ORIGINAL_CASE_ONCE->Math.addExact(Math.addExact(85,RMTM_POST_SUCCESSION_ADDITIONAL_SUBMISSIONS),Math.multiplyExact(8,maximumStatusPolls));};}
    }
    static RmtmConfig currentRmtmConfig(ObjectNode config) {
        StrictJson.require("xar.native-owner-snapshot-config/v47".equals(StrictJson.text(config.get("schema"))),"Explicit v47 RMTM family required");
        RmtmMode mode=switch(StrictJson.text(config.get("mode"))){
            case "current_rmtm_query_role"->RmtmMode.QUERY_ROLE;
            case "current_rmtm_query_decision"->RmtmMode.QUERY_DECISION;
            case "current_rmtm_original_case_once"->RmtmMode.ORIGINAL_CASE_ONCE;
            case "current_rmtm_threshold_50_51_once"->RmtmMode.THRESHOLD_50_51_ONCE;
            default->throw new IllegalArgumentException("Only fixed RMTM queries/original case/independent50-51 case");};
        boolean composite=mode==RmtmMode.ORIGINAL_CASE_ONCE||mode==RmtmMode.THRESHOLD_50_51_ONCE;
        var fields=new java.util.HashSet<>(Set.of("schema","mode","owner_descriptor","overall_timeout_seconds","read_timeout_seconds","maximum_frames_per_operation"));
        if(composite){fields.add("maximum_status_polls");fields.add("status_poll_delay_ms");}
        StrictJson.object(config,Set.copyOf(fields));ExactRef.fromJson(config.get("owner_descriptor"));
        StrictJson.integer(config.get("overall_timeout_seconds"),1,600);StrictJson.integer(config.get("read_timeout_seconds"),1,60);
        StrictJson.integer(config.get("maximum_frames_per_operation"),1,65536);
        return new RmtmConfig(mode,composite?Math.toIntExact(StrictJson.integer(config.get("maximum_status_polls"),1,256)):0,
                composite?StrictJson.integer(config.get("status_poll_delay_ms"),1,1000):0);
    }
    static void requireCurrentRmtmRole(CurrentRmtmActorTransitionResult frame,CoreFrame.Prefix core)throws IOException {
        if(frame.action()!=CurrentRmtmActorTransition.Action.QUERY_ROLE||frame.status()!=CurrentRmtmActorTransitionResult.Status.AVAILABLE||!frame.ok()||frame.accepted()
                ||!frame.operationId().isEmpty()||frame.claimSequence().signum()!=0||frame.effectAttempted()||frame.nativeReturned()||!frame.cleanupKnown()
                ||frame.providerGeneration().signum()<=0||frame.querySequence().signum()<=0||frame.connectionGeneration().signum()<=0
                ||frame.factsBefore().filter(core::equals).isEmpty()||frame.source().isEmpty()||frame.progress().isPresent())
            throw new IOException("Actual RMTM role query lost immutable Core/Source/readonly facts");
    }
    static CurrentRmtmActorTransitionSource requireCurrentRmtmPositiveRole(CurrentRmtmActorTransitionResult frame,CoreFrame.Prefix core,
            CurrentRmtmActorTransitionSource.Role role,java.math.BigInteger epoch,int song,int successor,boolean confirm,int days,int start)throws IOException {
        requireCurrentRmtmRole(frame,core);var s=frame.source().orElseThrow();
        if(!s.caseStartCaptured()||!s.definitionFound()||!s.nativeShown().orElse(false)||!s.runtimeReady()||!s.predecessorResolved()||s.role()!=role
                ||!s.actorEpoch().equals(epoch)||!frame.actorEpoch().equals(epoch)||s.completedNaturalDays()!=days||frame.completedNaturalDays()!=days
                ||s.maximumNaturalDays()!=14||s.caseStartDateRaw()!=start||(long)start+24L*days!=core.dateRaw()||s.songActorId().filter(id->id==song).isEmpty()
                ||(role==CurrentRmtmActorTransitionSource.Role.SONG?core.playedCharacterId()!=song:core.playedCharacterId()!=successor||s.successorActorId().filter(id->id==successor).isEmpty())
                ||(confirm?!s.confirmAdmissible():!s.advanceAdmissible()))throw new IOException("Actual shown RMTM fixed role/frontier/count/actors do not admit this next step");
        // Nullable execute-time identity is independent DATA, never substituted by a pre-death heir or a custody condition.
        return s;
    }
    static void requireCurrentRmtmDayTerminal(CurrentRmtmActorTransitionResult frame,CoreFrame.Prefix before,String operation,int target,int expectedDays)throws IOException {
        boolean transition=expectedDays==5;var status=transition?CurrentRmtmActorTransitionResult.Status.TRANSITION_PENDING:CurrentRmtmActorTransitionResult.Status.COMPLETED_DAY;
        var epoch=expectedDays<=5?java.math.BigInteger.ZERO:java.math.BigInteger.ONE;
        if(expectedDays<1||expectedDays>14||frame.status()!=status||!frame.ok()||!frame.accepted()||!frame.operationId().equals(operation)
                ||frame.factsBefore().filter(before::equals).isEmpty()||frame.claimSequence().signum()<=0||frame.completedNaturalDays()!=expectedDays
                ||!frame.cleanupKnown()||!frame.effectAttempted()||!frame.nativeReturned()||!frame.actorEpoch().equals(epoch)||frame.progress().isEmpty())
            throw new IOException("RMTM requires exact D1-4 Song completion, D5 pending or D6-14 successor completion; no actor-abort/UNKNOWN");
        var p=frame.progress().orElseThrow();
        if(p.generation().signum()<=0||p.startingDateRaw()!=before.dateRaw()||(long)before.dateRaw()+24!=target||p.targetDateRaw()!=target||p.lastObservedDateRaw()!=target
                ||p.beforeActorId()!=before.playedCharacterId()||p.afterActorId()==-1||p.completedDailyTicks()!=1||p.failureFlags()!=0||p.overshootDays()!=0
                ||!p.armAttempted()||!p.resumeAttempted()||!p.resumeSubmitted()||!p.exactDayConfirmed()||!p.shutdownSafe()||p.armed()||p.accessCleanupUnknown()
                ||p.transitionPending()!=transition||(transition?p.afterActorId()==p.beforeActorId():p.afterActorId()!=p.beforeActorId()))
            throw new IOException("RMTM terminal needs one exact24 natural tick, actual complete IDs and safe disarmed cleanup");
    }
    static CoreFrame.Prefix currentRmtmAfter(CoreFrame.Prefix before,int date,int actor)throws IOException {
        if(actor==-1||(long)before.dateRaw()+24!=date)throw new IOException("Exact one-day actual RMTM actor proof required");
        return new CoreFrame.Prefix(date,before.speed(),before.paused(),before.localPlayerId(),before.mapReady(),before.hasPlayedCharacter(),actor,before.playedCharacterAlive());
    }
    static String currentRmtmPhysicalLawForm(CurrentRmtmTitleQuerySource physical,boolean scriptOwnSingleHeir,boolean realmSingleHeir)throws IOException {
        if(!physical.sampledTwice()||physical.nativeLawCount()!=physical.physicalOwnLaws().size())throw new IOException("Complete actual ordered physical law Source required");
        if(physical.nativeLawCount()==0&&!scriptOwnSingleHeir&&realmSingleHeir)return "realm_baseline";
        if(physical.nativeLawCount()==1&&physical.physicalOwnLaws().get(0).key().equals("single_heir_succession_law")&&scriptOwnSingleHeir)return "own_override";
        throw new IOException("Conflicting/unresolved own/realm law DATA; no effective-law inference");
    }
    static void requireCurrentRmtmPhysicalHolder(CurrentRmtmTitleQuerySource physical,CoreFrame.Prefix core)throws IOException {
        if(core.playedCharacterId()==-1||physical.actorId()!=core.playedCharacterId()
                ||physical.holder().filter(h->h.alive()&&h.fullId()==Integer.toUnsignedLong(core.playedCharacterId())).isEmpty())
            throw new IOException("Physical holder full uint32 does not match actual signed32 Core actor");
    }
    private static Instant currentRmtmUntil(NativeGameTransport.CoreReceived before,Instant parent){return before.validUntil().isBefore(parent)?before.validUntil():parent;}
    private static void requireCurrentRmtmAfterRequest(NativeGameTransport transport,NativeGameTransport.CoreReceived after,String request)throws IOException {
        var prior=transport.originalRequestChronology(request).orElseThrow(()->new IOException("Original RMTM ACK chronology absent"));
        if(after.original().custody().orElseThrow().writeEntered().order().compareTo(prior.responseReceived().order())<=0)
            throw new IOException("Fresh RMTM Core must be independently written after this original ACK");
    }
    private static NativeGameTransport.CoreReceived readCurrentRmtmCore(NativeGameTransport transport,GameSupervisorControl.Descriptor owner,NativeLaunchPlan plan,
            Path output,String label,Instant deadline,ObjectNode result,ObjectNode originals,NativeObservationPort.TransportSession session,CoreFrame.Prefix expected)throws IOException,InterruptedException {
        stage="FRESH_INDEPENDENT_RMTM_CORE";result.put("read_calls",result.path("read_calls").intValue()+1);
        var read=transport.readCoreFrameReceived(deadline);archiveCurrentLetterOutcome(transport,Files.createDirectory(output.resolve(label)),label,read.original(),originals);
        if(!(read instanceof NativeGameTransport.CoreReceived before)||!(before.frame() instanceof CoreFrame.Partial core))throw new IOException("Actual RMTM Core unavailable/UNKNOWN; no retry");
        requireCurrentDjcAckOwner(transport,owner,before.original(),session);var p=core.prefix();
        if(core.build()!=ExactCk3Build.CK3_121003_STEAM_26785313||!core.build().executableSha256().equalsIgnoreCase(plan.sources().review().gameExecutable().sha256())
                ||!core.build().coreFrameAdapterId().equals(plan.adapterId())||!p.paused()||!p.mapReady()||!p.hasPlayedCharacter()||!p.playedCharacterAlive()
                ||p.playedCharacterId()==-1||p.localPlayerId()<0||p.speed()<1||p.speed()>5||expected!=null&&!expected.equals(p))throw new IOException("Actual current267 paused living RMTM Core differs");
        before.requireOriginal(transport,currentRmtmUntil(before,deadline));return before;
    }
    private static NativeGameTransport.RmtmRoleReceived readCurrentRmtmRole(NativeGameTransport transport,GameSupervisorControl.Descriptor owner,NativeGameTransport.CoreReceived before,
            NativeObservationPort.TransportSession session,Path output,String label,Instant parent,ObjectNode result,ObjectNode originals)throws IOException,InterruptedException {
        Instant until=currentRmtmUntil(before,parent);stage="ONE_READONLY_RMTM_ROLE";result.put("read_calls",result.path("read_calls").intValue()+1);
        var read=transport.readCurrentRmtmRole(before,until);Path out=Files.createDirectory(output.resolve(label));archiveCurrentLetterOutcome(transport,out,label,read.original(),originals);
        if(!(read instanceof NativeGameTransport.RmtmRoleReceived query))throw new IOException("Actual RMTM role unavailable/UNKNOWN; no replacement or retry");
        query.requireOriginal(transport,query.validUntil());var ack=query.original();requireCurrentDjcAckOwner(transport,owner,ack,session);var frame=CurrentRmtmActorTransitionResult.decodeOutcome(ack);
        if(!frame.equals(query.frame())||query.validUntil().isAfter(until)||!frame.deadlineUnixMs().equals(java.math.BigInteger.valueOf(query.validUntil().toEpochMilli()))
                ||!frame.connectionGeneration().equals(session.connectionGeneration()))throw new IOException("RMTM role differs from THIS actual ACK/connection/original deadline");
        requireCurrentRmtmRole(frame,((CoreFrame.Partial)before.frame()).prefix());
        originals.set(label+"_original_result",write(out,"original-result.json",ack.originalResultToken().orElseThrow().bytes()));result.set(label,FullJsonTree.parse(frame.encode().bytes(),FullJsonTree.MAXIMUM_BYTES));return query;
    }
    private static void archiveCurrentRmtmIntent(Path output,String label,String request,String operation,Instant deadline,byte[] packet,ObjectNode originals)throws IOException {
        Path out=Files.createDirectory(output.resolve(label));var intent=StrictJson.object().put("schema","xar.current-rmtm-original-intent/v1").put("request_id",request).put("operation_id",operation)
                .put("original_deadline_utc",deadline.toString()).put("independent_after_core_verified",false).put("physical_save_confirmed",false);
        intent.set("original_outbound",write(out,"original-request.packet",packet));originals.set(label+"_intent",write(out,"original-intent.json",FullJsonTree.encode(intent,SMALL)));
    }
    private static CurrentRmtmActorTransitionResult archiveCurrentRmtmOperation(NativeGameTransport transport,GameSupervisorControl.Descriptor owner,NativeGameTransport.RmtmAdvancePrepared prepared,
            NativeGameTransport.RmtmRoleReceived originalRole,NativeActionPort.DispatchOutcome outcome,NativeObservationPort.TransportSession session,Path output,String label,ObjectNode result,ObjectNode originals)throws IOException {
        Path out=Files.createDirectory(output.resolve(label));archiveCurrentLetterOutcome(transport,out,label,outcome,originals);
        if(!(outcome instanceof NativeActionPort.AckReceived ack))throw new IOException("Original RMTM day/status refused or UNKNOWN; never replay");
        requireCurrentDjcAckOwner(transport,owner,ack,session);var frame=CurrentRmtmActorTransitionResult.decodeOutcome(ack);
        originals.set(label+"_original_result",write(out,"original-result.json",ack.originalResultToken().orElseThrow().bytes()));result.set(label,FullJsonTree.parse(frame.encode().bytes(),FullJsonTree.MAXIMUM_BYTES));var q=originalRole.frame();
        if(prepared.originalUnknown()||prepared.latestFrame().filter(frame::equals).isEmpty()||!frame.operationId().equals(prepared.operationId())
                ||!frame.deadlineUnixMs().equals(java.math.BigInteger.valueOf(prepared.deadline().toEpochMilli()))||!frame.providerGeneration().equals(q.providerGeneration())
                ||!frame.querySequence().equals(q.querySequence())||!frame.factsBefore().equals(q.factsBefore())||!frame.connectionGeneration().equals(session.connectionGeneration())||!frame.cleanupKnown()
                ||frame.action()!=CurrentRmtmActorTransition.Action.ADVANCE_DAY&&frame.action()!=CurrentRmtmActorTransition.Action.QUERY_OPERATION
                ||frame.action()==CurrentRmtmActorTransition.Action.QUERY_OPERATION&&frame.source().isPresent()
                ||frame.action()==CurrentRmtmActorTransition.Action.ADVANCE_DAY&&!frame.source().equals(q.source()))throw new IOException("Original RMTM operation lost THIS ACK/whole Source/Core/lease/ID/deadline");
        if(frame.status()!=CurrentRmtmActorTransitionResult.Status.SUBMITTED&&frame.status()!=CurrentRmtmActorTransitionResult.Status.RUNNING
                &&frame.status()!=CurrentRmtmActorTransitionResult.Status.TRANSITION_PENDING&&frame.status()!=CurrentRmtmActorTransitionResult.Status.COMPLETED_DAY)
            throw new IOException("Actual RMTM day refused/UNKNOWN; no fresh-ID workaround");return frame;
    }
    private static CurrentRmtmActorTransitionResult runCurrentRmtmDay(NativeGameTransport transport,GameSupervisorControl.Descriptor owner,NativeGameTransport.RmtmRoleReceived role,
            NativeGameTransport.RmtmAdvancePrepared prepared,RmtmConfig config,NativeObservationPort.TransportSession session,Path output,String label,Instant deadline,Duration readTimeout,
            ObjectNode result,ObjectNode originals)throws IOException,InterruptedException {
        if(!prepared.deadline().equals(role.validUntil())||prepared.deadline().isAfter(deadline)||prepared.targetDateRaw()!=Math.addExact(role.frame().factsBefore().orElseThrow().dateRaw(),24))
            throw new IOException("Original RMTM preparation changed its Source/deadline/exact24 target");
        archiveCurrentRmtmIntent(output,label+"-intent",prepared.requestId(),prepared.operationId(),prepared.deadline(),prepared.originalPacket().value(),originals);
        stage="ONCE_FIXED_RMTM_NATURAL_DAY";result.put("advance_calls",result.path("advance_calls").intValue()+1);
        var frame=archiveCurrentRmtmOperation(transport,owner,prepared,role,transport.submitCurrentRmtmAdvance(prepared),session,output,label+"-submit",result,originals);
        for(int poll=0;frame.status()==CurrentRmtmActorTransitionResult.Status.SUBMITTED||frame.status()==CurrentRmtmActorTransitionResult.Status.RUNNING;poll++){
            if(poll>=config.maximumStatusPolls())throw new IOException("Original bounded RMTM readonly status observations exhausted; preserve unknown operation");
            if(!Instant.now().plusMillis(config.statusPollDelayMillis()).isBefore(deadline))throw new IOException("RMTM parent deadline cannot be extended");
            Thread.sleep(config.statusPollDelayMillis());Instant receive=Instant.now().plus(readTimeout);if(receive.isAfter(deadline))receive=deadline;
            result.put("status_queries",result.path("status_queries").intValue()+1);var outcome=transport.queryCurrentRmtmOperation(prepared,receive);
            frame=archiveCurrentRmtmOperation(transport,owner,prepared,role,outcome,session,output,label+"-status-"+String.format(java.util.Locale.ROOT,"%03d",poll+1),result,originals);
        }
        requireCurrentRmtmDayTerminal(frame,role.frame().factsBefore().orElseThrow(),prepared.operationId(),prepared.targetDateRaw(),role.frame().source().orElseThrow().completedNaturalDays()+1);return frame;
    }
    static CurrentRmtmDecisionSource requireCurrentRmtmDecisionQuery(CurrentRmtmDecisionResult f,CoreFrame.Prefix core,java.math.BigInteger connection)throws IOException {
        if(f.action()!=CurrentRmtmDecision.Action.QUERY||f.status()!=CurrentRmtmDecisionResult.Status.AVAILABLE||!f.cleanupKnown()||f.effectAttempted()||f.nativeReturned()||f.nativeHandled()
                ||f.claimSequence().signum()!=0||f.decisionKey().isPresent()||f.source().isEmpty()||f.providerGeneration().signum()<=0||f.querySequence().signum()<=0
                ||f.factsBefore().filter(core::equals).isEmpty()||f.owner().filter(o->o.connectionGeneration().equals(connection)).isEmpty())throw new IOException("Actual RMTM decision query lost complete Source/Core/connection/readonly facts");
        return f.source().orElseThrow(); // false Can, absent panels and complete empty/NUL tooltip remain DATA.
    }
    static void requireCurrentRmtmDecisionDispatch(CurrentRmtmDecisionResult f,CurrentRmtmDecisionResult q,CoreFrame.Prefix core,java.math.BigInteger connection,
            CurrentRmtmDecision.Action action,CurrentRmtmDecision.DecisionKey fixedKey)throws IOException {
        requireCurrentRmtmDecisionQuery(q,core,connection);var status=switch(action){case OPEN_LIST->CurrentRmtmDecisionResult.Status.NAVIGATION_DISPATCHED;
            case OPEN_DETAIL->CurrentRmtmDecisionResult.Status.SELECTION_DISPATCHED;case CONFIRM->CurrentRmtmDecisionResult.Status.CONFIRMATION_DISPATCHED;default->throw new IOException("No query-as-effect");};
        if(f.action()!=action||f.status()!=status||!f.effectAttempted()||!f.nativeReturned()||!f.cleanupKnown()||f.claimSequence().signum()<=0
                ||action!=CurrentRmtmDecision.Action.OPEN_LIST&&f.nativeHandled()||!f.source().equals(q.source())||!f.factsBefore().equals(q.factsBefore())
                ||!f.providerGeneration().equals(q.providerGeneration())||!f.querySequence().equals(q.querySequence())||f.owner().filter(o->o.connectionGeneration().equals(connection)).isEmpty()
                ||(action==CurrentRmtmDecision.Action.OPEN_LIST?f.decisionKey().isPresent():!f.decisionKey().equals(Optional.of(fixedKey))))
            throw new IOException("RMTM decision lost original Source/Core/lease/fixed key/dispatch; Toggle false is valid DATA");
    }
    private static NativeGameTransport.RmtmDecisionReceived readCurrentRmtmDecision(NativeGameTransport transport,GameSupervisorControl.Descriptor owner,NativeGameTransport.CoreReceived before,
            NativeObservationPort.TransportSession session,Path output,String label,Instant parent,ObjectNode result,ObjectNode originals)throws IOException,InterruptedException {
        Instant until=currentRmtmUntil(before,parent);stage="ONE_READONLY_RMTM_DECISION";result.put("read_calls",result.path("read_calls").intValue()+1);
        var read=transport.readCurrentRmtmDecision(before,until);Path out=Files.createDirectory(output.resolve(label));archiveCurrentLetterOutcome(transport,out,label,read.original(),originals);
        if(!(read instanceof NativeGameTransport.RmtmDecisionReceived query))throw new IOException("Actual RMTM decision unavailable/UNKNOWN; no empty Source or retry");
        query.requireOriginal(transport,query.validUntil());var ack=query.original();requireCurrentDjcAckOwner(transport,owner,ack,session);var frame=CurrentRmtmDecisionResult.decodeOutcome(ack);
        if(!frame.equals(query.frame())||query.validUntil().isAfter(until))throw new IOException("RMTM private decision query differs from THIS ACK/deadline");
        requireCurrentRmtmDecisionQuery(frame,((CoreFrame.Partial)before.frame()).prefix(),session.connectionGeneration());
        originals.set(label+"_original_result",write(out,"original-result.json",ack.originalResultToken().orElseThrow().bytes()));result.set(label,FullJsonTree.parse(frame.encode().bytes(),FullJsonTree.MAXIMUM_BYTES));return query;
    }
    private static CurrentRmtmDecisionResult submitCurrentRmtmDecision(NativeGameTransport transport,GameSupervisorControl.Descriptor owner,NativeGameTransport.RmtmDecisionReceived query,
            NativeGameTransport.RmtmDecisionPrepared prepared,CurrentRmtmDecision.DecisionKey key,NativeObservationPort.TransportSession session,Path output,String label,ObjectNode result,ObjectNode originals)throws IOException,InterruptedException {
        if(!prepared.deadline().equals(query.validUntil()))throw new IOException("Original RMTM decision deadline changed before intent");
        archiveCurrentRmtmIntent(output,label+"-intent",prepared.requestId(),"",prepared.deadline(),prepared.originalPacket().value(),originals);
        stage="ONCE_FIXED_RMTM_DECISION";result.put("decision_action_calls",result.path("decision_action_calls").intValue()+1);
        var outcome=transport.submitCurrentRmtmDecision(prepared);Path out=Files.createDirectory(output.resolve(label+"-result"));archiveCurrentLetterOutcome(transport,out,label,outcome,originals);
        if(!(outcome instanceof NativeActionPort.AckReceived ack))throw new IOException("Original RMTM decision refused/UNKNOWN; never resubmit");
        requireCurrentDjcAckOwner(transport,owner,ack,session);var frame=CurrentRmtmDecisionResult.decodeOutcome(ack);
        originals.set(label+"_original_result",write(out,"original-result.json",ack.originalResultToken().orElseThrow().bytes()));result.set(label,FullJsonTree.parse(frame.encode().bytes(),FullJsonTree.MAXIMUM_BYTES));
        if(!ack.requestId().equals(prepared.requestId())||prepared.latestFrame().filter(frame::equals).isEmpty())throw new IOException("THIS RMTM decision ACK differs from private preparation latest receipt");
        requireCurrentRmtmDecisionDispatch(frame,query.frame(),query.frame().factsBefore().orElseThrow(),session.connectionGeneration(),prepared.action(),key);return frame;
    }
    static CurrentRmtmEventSource requireCurrentRmtmEventQuery(CurrentRmtmEventResult f,CurrentRmtmEvent.Action action,CoreFrame.Prefix core,java.math.BigInteger connection)throws IOException {
        if(!action.queryOnly()||f.action()!=action||f.status()!=CurrentRmtmEventResult.Status.AVAILABLE||!f.cleanupKnown()||f.effectAttempted()||f.nativeReturned()
                ||f.claimSequence().signum()!=0||f.instanceId().isPresent()||f.source().isEmpty()||f.providerGeneration().signum()<=0||f.querySequence().signum()<=0
                ||f.factsBefore().filter(core::equals).isEmpty()||f.owner().filter(o->o.connectionGeneration().equals(connection)).isEmpty())throw new IOException("RMTM event query lost original channel/Core/connection/readonly Source");
        var s=f.source().orElseThrow();if(!s.sampledTwice()||!s.eventCensus().censusComplete()||s.eventCensus().namedRootCount()!=s.eventCensus().events().size())throw new IOException("Complete actual RMTM census required");return s;
    }
    static void requireCurrentRmtmEventDispatch(CurrentRmtmEventResult f,CurrentRmtmEventResult q,CoreFrame.Prefix core,java.math.BigInteger connection,int instance)throws IOException {
        var s=requireCurrentRmtmEventQuery(q,q.action(),core,connection);
        if(f.action()!=q.action().ackAction()||f.status()!=CurrentRmtmEventResult.Status.SELECTION_DISPATCHED||!f.effectAttempted()||!f.nativeReturned()||!f.cleanupKnown()
                ||f.claimSequence().signum()<=0||f.instanceId().filter(n->n==instance).isEmpty()||!f.source().equals(q.source())||!f.factsBefore().equals(q.factsBefore())
                ||!f.providerGeneration().equals(q.providerGeneration())||!f.querySequence().equals(q.querySequence())||f.owner().filter(o->o.connectionGeneration().equals(connection)).isEmpty()
                ||!s.caseBound()||!s.ackAdmissible()||s.fixedInstanceId().filter(n->n==instance).isEmpty())throw new IOException("RMTM fixed0 choice lost original Source/Core/channel/instance/lease");
    }
    private static NativeGameTransport.RmtmEventReceived readCurrentRmtmEvent(NativeGameTransport transport,GameSupervisorControl.Descriptor owner,NativeGameTransport.CoreReceived before,
            CurrentRmtmEvent.Action action,NativeObservationPort.TransportSession session,Path output,String label,Instant parent,ObjectNode result,ObjectNode originals)throws IOException,InterruptedException {
        Instant until=currentRmtmUntil(before,parent);stage="ONE_READONLY_RMTM_EVENT";result.put("read_calls",result.path("read_calls").intValue()+1);
        var read=transport.readCurrentRmtmEvent(before,action,until);Path out=Files.createDirectory(output.resolve(label));archiveCurrentLetterOutcome(transport,out,label,read.original(),originals);
        if(!(read instanceof NativeGameTransport.RmtmEventReceived query))throw new IOException("Actual RMTM fixed event unavailable/UNKNOWN; no generic acknowledgement");
        query.requireOriginal(transport,query.validUntil());var ack=query.original();requireCurrentDjcAckOwner(transport,owner,ack,session);var frame=CurrentRmtmEventResult.decodeOutcome(ack);
        if(!frame.equals(query.frame())||query.validUntil().isAfter(until))throw new IOException("THIS RMTM event ACK/private deadline differs");
        requireCurrentRmtmEventQuery(frame,action,((CoreFrame.Partial)before.frame()).prefix(),session.connectionGeneration());
        originals.set(label+"_original_result",write(out,"original-result.json",ack.originalResultToken().orElseThrow().bytes()));result.set(label,FullJsonTree.parse(frame.encode().bytes(),FullJsonTree.MAXIMUM_BYTES));return query;
    }
    private static CurrentRmtmEventResult submitCurrentRmtmEvent(NativeGameTransport transport,GameSupervisorControl.Descriptor owner,NativeGameTransport.RmtmEventReceived query,
            NativeGameTransport.RmtmEventPrepared prepared,NativeObservationPort.TransportSession session,Path output,String label,ObjectNode result,ObjectNode originals)throws IOException,InterruptedException {
        if(!prepared.deadline().equals(query.validUntil()))throw new IOException("Original RMTM event deadline changed before intent");
        archiveCurrentRmtmIntent(output,label+"-intent",prepared.requestId(),"",prepared.deadline(),prepared.originalPacket().value(),originals);
        boolean postSuccession=prepared.action()==CurrentRmtmEvent.Action.CHOOSE_POST_SUCCESSION_FIRST_AVAILABLE;
        stage=postSuccession?"ONCE_POST_SUCCESSION_RMTM_EVENT":"ONCE_FIXED_RMTM_EVENT";
        String count=postSuccession?"post_succession_event_calls":"event_ack_calls";result.put(count,result.path(count).intValue()+1);
        var outcome=transport.submitCurrentRmtmEvent(prepared);Path out=Files.createDirectory(output.resolve(label+"-result"));archiveCurrentLetterOutcome(transport,out,label,outcome,originals);
        if(!(outcome instanceof NativeActionPort.AckReceived ack))throw new IOException("RMTM original event effect refused/UNKNOWN; no resubmit");
        requireCurrentDjcAckOwner(transport,owner,ack,session);var frame=CurrentRmtmEventResult.decodeOutcome(ack);
        originals.set(label+"_original_result",write(out,"original-result.json",ack.originalResultToken().orElseThrow().bytes()));result.set(label,FullJsonTree.parse(frame.encode().bytes(),FullJsonTree.MAXIMUM_BYTES));
        if(!ack.requestId().equals(prepared.requestId())||prepared.latestFrame().filter(frame::equals).isEmpty())throw new IOException("THIS RMTM event ACK differs from original private preparation");
        if(postSuccession)requireCurrentRmtmPostSuccessionDispatch(frame,query.frame(),query.frame().factsBefore().orElseThrow(),session.connectionGeneration(),prepared.instanceId());
        else requireCurrentRmtmEventDispatch(frame,query.frame(),query.frame().factsBefore().orElseThrow(),session.connectionGeneration(),prepared.instanceId());return frame;
    }
    private record RmtmDecisionObservation(NativeGameTransport.CoreReceived core,NativeGameTransport.RmtmDecisionReceived query) {}
    private static RmtmDecisionObservation navigateCurrentRmtmDecision(NativeGameTransport transport,GameSupervisorControl.Descriptor owner,NativeLaunchPlan plan,
            NativeGameTransport.RmtmDecisionPurpose purpose,CurrentRmtmDecision.DecisionKey key,boolean confirm,NativeObservationPort.TransportSession session,CoreFrame.Prefix expected,
            Path output,String label,Instant deadline,ObjectNode result,ObjectNode originals)throws IOException,InterruptedException {
        var core=readCurrentRmtmCore(transport,owner,plan,output,label+"-core",deadline,result,originals,session,expected);
        var query=readCurrentRmtmDecision(transport,owner,core,session,output,label+"-query",deadline,result,originals);
        // At most one original OpenList, one exact detail and one confirmation for this private purpose.
        var initial=query.frame().source().orElseThrow();
        boolean needsDetail=!initial.detailVisible()||!initial.selectedDecisionKey().equals(Optional.of(key));
        if(needsDetail&&!initial.listVisible()){
            var prep=transport.prepareCurrentRmtmDecision(query,CurrentRmtmDecision.Action.OPEN_LIST,purpose);
            submitCurrentRmtmDecision(transport,owner,query,prep,key,session,output,label+"-open-list",result,originals);
            core=readCurrentRmtmCore(transport,owner,plan,output,label+"-after-list-core",deadline,result,originals,session,expected);requireCurrentRmtmAfterRequest(transport,core,prep.requestId());
            query=readCurrentRmtmDecision(transport,owner,core,session,output,label+"-after-list-query",deadline,result,originals);
        }
        var selected=query.frame().source().orElseThrow();
        if(!selected.detailVisible()||!selected.selectedDecisionKey().equals(Optional.of(key))){
            var prep=transport.prepareCurrentRmtmDecision(query,CurrentRmtmDecision.Action.OPEN_DETAIL,purpose);
            submitCurrentRmtmDecision(transport,owner,query,prep,key,session,output,label+"-open-detail",result,originals);
            core=readCurrentRmtmCore(transport,owner,plan,output,label+"-after-detail-core",deadline,result,originals,session,expected);requireCurrentRmtmAfterRequest(transport,core,prep.requestId());
            query=readCurrentRmtmDecision(transport,owner,core,session,output,label+"-after-detail-query",deadline,result,originals);
        }
        if(confirm){
            var prep=transport.prepareCurrentRmtmDecision(query,CurrentRmtmDecision.Action.CONFIRM,purpose);
            submitCurrentRmtmDecision(transport,owner,query,prep,key,session,output,label+"-confirm",result,originals);
            core=readCurrentRmtmCore(transport,owner,plan,output,label+"-after-confirm-core",deadline,result,originals,session,expected);requireCurrentRmtmAfterRequest(transport,core,prep.requestId());
            query=readCurrentRmtmDecision(transport,owner,core,session,output,label+"-after-confirm-query",deadline,result,originals);
        }
        return new RmtmDecisionObservation(core,query);
    }
    static void requireCurrentRmtmThresholdPrestate(CurrentRmtmActorTransitionResult role,CoreFrame.Prefix current,int song,int startRaw)throws IOException {
        requireCurrentRmtmRole(role,current);var s=role.source().orElseThrow();
        if((long)startRaw+96!=current.dateRaw()||!s.caseStartCaptured()||!s.definitionFound()||!s.nativeShown().orElse(false)
                ||!s.runtimeReady()||!s.predecessorResolved()||s.role()!=CurrentRmtmActorTransitionSource.Role.SONG
                ||s.actorEpoch().signum()!=0||role.actorEpoch().signum()!=0||s.completedNaturalDays()!=4||role.completedNaturalDays()!=4
                ||s.maximumNaturalDays()!=14||s.caseStartDateRaw()!=startRaw||current.playedCharacterId()!=song
                ||s.songActorId().filter(id->id==song).isEmpty()||s.successorActorId().isPresent()||s.pending().isPresent()||s.confirmAdmissible())
            throw new IOException("Independent threshold UI requires the actual completed D4 Song checkpoint, original clock/frontier and no pending succession");
        // Stage90 may end date advancement. This UI boundary grants neither Advance nor ConfirmEpoch authority.
        // The original script checkpoint is independently evidenced by Root logs and the actual setup decision row/Can.
    }
    private static CoreFrame.Prefix stageCurrentRmtmThreshold(NativeGameTransport transport,GameSupervisorControl.Descriptor owner,NativeLaunchPlan plan,
            NativeGameTransport.RmtmRoleReceived capture,RmtmConfig config,NativeObservationPort.TransportSession session,Path output,Instant deadline,Duration readTimeout,
            ObjectNode result,ObjectNode originals)throws IOException,InterruptedException {
        var start=capture.frame().factsBefore().orElseThrow();int song=start.playedCharacterId();var current=start;
        requireCurrentRmtmPositiveRole(capture.frame(),start,CurrentRmtmActorTransitionSource.Role.SONG,java.math.BigInteger.ZERO,song,-1,false,0,start.dateRaw());
        for(int day=1;day<=4;day++){
            String label="rmtm-threshold-day"+String.format(java.util.Locale.ROOT,"%02d",day);var role=capture;
            if(day>1){var before=readCurrentRmtmCore(transport,owner,plan,output,label+"-before-core",deadline,result,originals,session,current);
                role=readCurrentRmtmRole(transport,owner,before,session,output,label+"-before-role",deadline,result,originals);}
            requireCurrentRmtmPositiveRole(role.frame(),current,CurrentRmtmActorTransitionSource.Role.SONG,java.math.BigInteger.ZERO,song,-1,false,day-1,start.dateRaw());
            var prepared=transport.prepareCurrentRmtmAdvance(role);
            var terminal=runCurrentRmtmDay(transport,owner,role,prepared,config,session,output,label,deadline,readTimeout,result,originals);
            if(terminal.status()!=CurrentRmtmActorTransitionResult.Status.COMPLETED_DAY||terminal.progress().orElseThrow().transitionPending())
                throw new IOException("Threshold staging cannot import a pending transition or successor epoch");
            var expected=currentRmtmAfter(current,prepared.targetDateRaw(),song);
            var after=readCurrentRmtmCore(transport,owner,plan,output,label+"-after-core",deadline,result,originals,session,expected);
            requireCurrentRmtmAfterRequest(transport,after,terminal.requestId());current=((CoreFrame.Partial)after.frame()).prefix();
            result.put("natural_days_observed",day).put("threshold_staging_natural_days",day);
            if(day==1){
                acknowledgeCurrentRmtmChannel(transport,owner,plan,CurrentRmtmEvent.Action.QUERY_CHAOS,session,current,output,"rmtm-threshold-chaos",deadline,result,originals);
                acknowledgeCurrentRmtmChannel(transport,owner,plan,CurrentRmtmEvent.Action.QUERY_SUMMARY,session,current,output,"rmtm-threshold-summary",deadline,result,originals);
            }
            if(day==3){
                var actualRole=readCurrentRmtmRole(transport,owner,after,session,output,"rmtm-threshold-d3-after-role",deadline,result,originals);
                requireCurrentRmtmPositiveRole(actualRole.frame(),current,CurrentRmtmActorTransitionSource.Role.SONG,java.math.BigInteger.ZERO,song,-1,false,3,start.dateRaw());
                var observed=observeCurrentRmtm(transport,owner,plan,CurrentRmtmObservation.Action.QUERY_TITLE_PHASE,Optional.of(CurrentRmtmObservation.Phase.D3),Optional.empty(),
                        session,current,output,"rmtm-threshold-d3-title",deadline,result,originals);
                var phase=observed.query().frame().source().orElseThrow().titlePhase().orElseThrow();
                requireCurrentRmtmPhysicalHolder(phase.physical(),current);
                currentRmtmPhysicalLawForm(phase.physical(),phase.scriptOwnSingleHeir(),phase.holderRealmSingleHeir());
            }
            if(day==4){
                var roleAfter=readCurrentRmtmRole(transport,owner,after,session,output,"rmtm-threshold-d4-ready-role",deadline,result,originals);
                requireCurrentRmtmThresholdPrestate(roleAfter.frame(),current,song,start.dateRaw());
            }
        }
        result.put("threshold_prestate_staging_completed",true);
        return current;
    }
    private static void runCurrentRmtmThreshold(NativeGameTransport transport,GameSupervisorControl.Descriptor owner,NativeLaunchPlan plan,NativeGameTransport.RmtmRoleReceived capture,
            RmtmConfig config,NativeObservationPort.TransportSession session,Path output,Instant deadline,Duration readTimeout,ObjectNode result,ObjectNode originals)throws IOException,InterruptedException {
        var current=stageCurrentRmtmThreshold(transport,owner,plan,capture,config,session,output,deadline,readTimeout,result,originals);
        var setup=navigateCurrentRmtmDecision(transport,owner,plan,NativeGameTransport.RmtmDecisionPurpose.PREPARE_FIFTY,CurrentRmtmDecision.DecisionKey.PREPARE_FIFTY,true,session,current,output,"rmtm50-setup",deadline,result,originals);
        var fifty=navigateCurrentRmtmDecision(transport,owner,plan,NativeGameTransport.RmtmDecisionPurpose.INSPECT_FIFTY,CurrentRmtmDecision.DecisionKey.RESTORE,false,session,current,output,"rmtm50-inspect",deadline,result,originals);
        var f=fifty.query().frame().source().orElseThrow();
        if(!f.caseBound()||!f.detailVisible()||!f.selectedDecisionKey().equals(Optional.of(CurrentRmtmDecision.DecisionKey.RESTORE))||f.nativeCanConfirm().isEmpty()
                ||f.nativeCanConfirm().orElseThrow()||f.confirmAdmissible()||!f.confirmTooltipObserved())throw new IOException("Independent original50 requires actual false Can/full observed tooltip DATA");
        transport.retainCurrentRmtmFifty(fifty.query());result.put("threshold50_false_can_observed",true).put("threshold50_tooltip",f.confirmTooltip().orElseThrow());
        navigateCurrentRmtmDecision(transport,owner,plan,NativeGameTransport.RmtmDecisionPurpose.PREPARE_FIFTYONE,CurrentRmtmDecision.DecisionKey.PREPARE_FIFTYONE,true,session,current,output,"rmtm51-setup",deadline,result,originals);
        navigateCurrentRmtmDecision(transport,owner,plan,NativeGameTransport.RmtmDecisionPurpose.RESTORE_FIFTYONE,CurrentRmtmDecision.DecisionKey.RESTORE,true,session,current,output,"rmtm51-restore",deadline,result,originals);
        navigateCurrentRmtmDecision(transport,owner,plan,NativeGameTransport.RmtmDecisionPurpose.VERIFY_RESTORE,CurrentRmtmDecision.DecisionKey.VERIFY_RESTORE,true,session,current,output,"rmtm51-verify",deadline,result,originals);
        result.put("threshold_private_dispatch_chain_completed",true); // Root original script checkpoints/outcome remain independent AND.
    }
    static CurrentRmtmObservationSource requireCurrentRmtmObservationQuery(CurrentRmtmObservationResult f,CurrentRmtmObservation.Action action,CoreFrame.Prefix core,
            java.math.BigInteger connection)throws IOException {
        if(!action.queryOnly()||f.action()!=action||f.status()!=CurrentRmtmObservationResult.Status.AVAILABLE||!f.cleanupKnown()||f.effectAttempted()||f.nativeReturned()||f.nativeHandled()
                ||f.claimSequence().signum()!=0||f.source().isEmpty()||f.providerGeneration().signum()<=0||f.querySequence().signum()<=0
                ||f.factsBefore().filter(core::equals).isEmpty()||f.owner().filter(o->o.connectionGeneration().equals(connection)).isEmpty()
                ||f.source().orElseThrow().kind()!=action.kind()||!f.source().orElseThrow().sampledTwice())throw new IOException("Actual RMTM observation lost typed complete Source/Core/connection/readonly facts");
        return f.source().orElseThrow();
    }
    private record RmtmObservation(NativeGameTransport.CoreReceived core,NativeGameTransport.RmtmObservationReceived query) {}
    private static RmtmObservation observeCurrentRmtm(NativeGameTransport transport,GameSupervisorControl.Descriptor owner,NativeLaunchPlan plan,CurrentRmtmObservation.Action action,
            Optional<CurrentRmtmObservation.Phase> phase,Optional<CurrentRmtmObservation.OfferTarget> target,NativeObservationPort.TransportSession session,CoreFrame.Prefix expected,
            Path output,String label,Instant deadline,ObjectNode result,ObjectNode originals)throws IOException,InterruptedException {
        var core=readCurrentRmtmCore(transport,owner,plan,output,label+"-core",deadline,result,originals,session,expected);Instant until=currentRmtmUntil(core,deadline);
        result.put("read_calls",result.path("read_calls").intValue()+1);var read=transport.readCurrentRmtmObservation(core,action,phase,target,until);
        Path out=Files.createDirectory(output.resolve(label+"-query"));archiveCurrentLetterOutcome(transport,out,label,read.original(),originals);
        if(!(read instanceof NativeGameTransport.RmtmObservationReceived query))throw new IOException("Actual RMTM observation unavailable/UNKNOWN; retain PARTIAL, no default DATA or skipped phase");
        query.requireOriginal(transport,query.validUntil());var ack=query.original();requireCurrentDjcAckOwner(transport,owner,ack,session);var frame=CurrentRmtmObservationResult.decodeOutcome(ack);
        if(!frame.equals(query.frame())||query.validUntil().isAfter(until))throw new IOException("THIS RMTM observation ACK/private original deadline differs");
        var s=requireCurrentRmtmObservationQuery(frame,action,expected,session.connectionGeneration());
        if(phase.isPresent()&&s.titlePhase().filter(p->p.phase()==phase.orElseThrow()).isEmpty()||target.isPresent()&&s.offer().filter(o->o.target()==target.orElseThrow()).isEmpty())
            throw new IOException("Original fixed RMTM phase/target changed");
        originals.set(label+"_original_result",write(out,"original-result.json",ack.originalResultToken().orElseThrow().bytes()));result.set(label,FullJsonTree.parse(frame.encode().bytes(),FullJsonTree.MAXIMUM_BYTES));return new RmtmObservation(core,query);
    }
    private static void submitCurrentRmtmObservation(NativeGameTransport transport,GameSupervisorControl.Descriptor owner,NativeGameTransport.RmtmObservationReceived query,
            NativeGameTransport.RmtmObservationPrepared prepared,NativeObservationPort.TransportSession session,Path output,String label,ObjectNode result,ObjectNode originals)throws IOException,InterruptedException {
        if(!prepared.deadline().equals(query.validUntil()))throw new IOException("RMTM original UI deadline changed before intent");
        archiveCurrentRmtmIntent(output,label+"-intent",prepared.requestId(),"",prepared.deadline(),prepared.originalPacket().value(),originals);
        result.put("observation_action_calls",result.path("observation_action_calls").intValue()+1);var outcome=transport.submitCurrentRmtmObservation(prepared);
        Path out=Files.createDirectory(output.resolve(label+"-result"));archiveCurrentLetterOutcome(transport,out,label,outcome,originals);
        if(!(outcome instanceof NativeActionPort.AckReceived ack))throw new IOException("Original RMTM UI refused/UNKNOWN; never resubmit");
        requireCurrentDjcAckOwner(transport,owner,ack,session);var f=CurrentRmtmObservationResult.decodeOutcome(ack);var q=query.frame();
        originals.set(label+"_original_result",write(out,"original-result.json",ack.originalResultToken().orElseThrow().bytes()));result.set(label,FullJsonTree.parse(f.encode().bytes(),FullJsonTree.MAXIMUM_BYTES));
        if(!ack.requestId().equals(prepared.requestId())||prepared.latestFrame().filter(f::equals).isEmpty()||f.action()!=prepared.action()
                ||f.status()!=CurrentRmtmObservationResult.Status.NAVIGATION_DISPATCHED||!f.effectAttempted()||!f.nativeReturned()||!f.cleanupKnown()||f.claimSequence().signum()<=0
                ||prepared.action()!=CurrentRmtmObservation.Action.OPEN_BUDGET&&f.nativeHandled()||!f.source().equals(q.source())||!f.factsBefore().equals(q.factsBefore())
                ||!f.providerGeneration().equals(q.providerGeneration())||!f.querySequence().equals(q.querySequence())||f.owner().filter(o->o.connectionGeneration().equals(session.connectionGeneration())).isEmpty())
            throw new IOException("THIS RMTM UI ACK lost original beforeSource/Core/lease/dispatch; budget Toggle false is DATA");
    }
    private static void openAndCancelCurrentRmtmView(NativeGameTransport transport,GameSupervisorControl.Descriptor owner,NativeLaunchPlan plan,
            Optional<CurrentRmtmObservation.OfferTarget> target,NativeObservationPort.TransportSession session,CoreFrame.Prefix expected,Path output,String label,Instant deadline,
            ObjectNode result,ObjectNode originals)throws IOException,InterruptedException {
        boolean offer=target.isPresent();var queryAction=offer?CurrentRmtmObservation.Action.QUERY_OFFER:CurrentRmtmObservation.Action.QUERY_BUDGET;
        var first=observeCurrentRmtm(transport,owner,plan,queryAction,Optional.empty(),target,session,expected,output,label+"-before",deadline,result,originals);
        var open=transport.prepareCurrentRmtmObservation(first.query(),offer?CurrentRmtmObservation.Action.OPEN_OFFER:CurrentRmtmObservation.Action.OPEN_BUDGET);
        submitCurrentRmtmObservation(transport,owner,first.query(),open,session,output,label+"-open",result,originals);
        var visible=observeCurrentRmtm(transport,owner,plan,queryAction,Optional.empty(),target,session,expected,output,label+"-visible",deadline,result,originals);requireCurrentRmtmAfterRequest(transport,visible.core(),open.requestId());
        var s=visible.query().frame().source().orElseThrow();
        if(offer?!s.offer().orElseThrow().visible():!s.budget().orElseThrow().visible())throw new IOException("Actual independent RMTM opened view was not visible; dispatch alone is insufficient");
        var cancel=transport.prepareCurrentRmtmObservation(visible.query(),offer?CurrentRmtmObservation.Action.CANCEL_OFFER:CurrentRmtmObservation.Action.CANCEL_BUDGET);
        submitCurrentRmtmObservation(transport,owner,visible.query(),cancel,session,output,label+"-cancel",result,originals);
        var hidden=observeCurrentRmtm(transport,owner,plan,queryAction,Optional.empty(),target,session,expected,output,label+"-hidden",deadline,result,originals);requireCurrentRmtmAfterRequest(transport,hidden.core(),cancel.requestId());
        if(!transport.currentRmtmObservationHidden(cancel,hidden.query()))throw new IOException("Actual independent RMTM Cancel readback remains visible");
        result.put(label+"_independent_hidden_observed",true); // No Enact/Send or closed business credit.
    }
    static void requireCurrentRmtmTitlePhases(CurrentRmtmObservationResult d3,CurrentRmtmObservationResult pre,CurrentRmtmObservationResult post)throws IOException {
        var a=d3.source().orElseThrow().titlePhase().orElseThrow();var b=pre.source().orElseThrow().titlePhase().orElseThrow();var c=post.source().orElseThrow().titlePhase().orElseThrow();
        if(a.phase()!=CurrentRmtmObservation.Phase.D3||b.phase()!=CurrentRmtmObservation.Phase.PREDEATH||c.phase()!=CurrentRmtmObservation.Phase.POSTDEATH
                ||a.physical().fullTitleId()!=b.physical().fullTitleId()||a.physical().fullTitleId()!=c.physical().fullTitleId()
                ||a.physical().actorId()!=b.physical().actorId()||a.physical().actorId()==c.physical().actorId()
                ||d3.factsBefore().orElseThrow().dateRaw()>pre.factsBefore().orElseThrow().dateRaw()||pre.factsBefore().orElseThrow().dateRaw()>=post.factsBefore().orElseThrow().dateRaw()
                ||!d3.owner().orElseThrow().connectionGeneration().equals(pre.owner().orElseThrow().connectionGeneration())||!d3.owner().orElseThrow().connectionGeneration().equals(post.owner().orElseThrow().connectionGeneration())
                ||b.physical().engineCurrentHeir().filter(h->h.fullId()==Integer.toUnsignedLong(c.physical().actorId())).isEmpty())throw new IOException("Original D3/pre/post full-title/actor/date/connection/pre-heir AND differs");
        for(var f:List.of(d3,pre,post)){
            var phase=f.source().orElseThrow().titlePhase().orElseThrow();requireCurrentRmtmObservationQuery(f,CurrentRmtmObservation.Action.QUERY_TITLE_PHASE,f.factsBefore().orElseThrow(),d3.owner().orElseThrow().connectionGeneration());
            requireCurrentRmtmPhysicalHolder(phase.physical(),f.factsBefore().orElseThrow());currentRmtmPhysicalLawForm(phase.physical(),phase.scriptOwnSingleHeir(),phase.holderRealmSingleHeir());
            if(phase.phase()!=CurrentRmtmObservation.Phase.POSTDEATH&&phase.physical().engineCurrentHeir().filter(h->h.fullId()!=Integer.toUnsignedLong(phase.physical().actorId())).isEmpty())throw new IOException("D3/predeath require a complete non-self heir; postdeath future heir/alive remain DATA");
        }
        // This is actual three-phase physical/script DATA only. D5 execute-time three-dump identity remains a separate AND.
    }
    static void requireCurrentRmtmCouncilRetained(CurrentRmtmObservationSource.Council before,CurrentRmtmObservationSource.Council after)throws IOException {
        if(!before.completeModelCensus()||!after.completeModelCensus()||!before.sampledTwice()||!after.sampledTwice()||before.seats().size()!=9||after.seats().size()!=9)throw new IOException("Complete actual nine-seat models required");
        for(int i=0;i<9;i++){var a=before.seats().get(i);var b=after.seats().get(i);
            if(!a.positionKey().equals(b.positionKey())||a.incumbentId().isEmpty()||!a.incumbentAlive().orElse(false)||!a.incumbentId().equals(b.incumbentId())||!b.incumbentAlive().orElse(false))throw new IOException("Actual full-ID nine incumbent identity/liveness changed");}
    }
    // Event owner retains64 claims for this case: the two original D1 ACKs stay spent.
    static final int RMTM_POST_SUCCESSION_INSTANCE_LIMIT=64-2;
    static final int RMTM_POST_SUCCESSION_ADDITIONAL_SUBMISSIONS=3+3*RMTM_POST_SUCCESSION_INSTANCE_LIMIT+3;
    static void requireCurrentRmtmPostSuccessionBoundary(CoreFrame.Prefix core,int song,int successor,int completedDays,int startingDate)throws IOException {
        long exactDate=(long)startingDate+24L*completedDays;
        if(core==null||song==-1||successor==-1||song==successor||completedDays<5||completedDays>14
                ||exactDate<Integer.MIN_VALUE||exactDate>Integer.MAX_VALUE||core.dateRaw()!=exactDate||core.playedCharacterId()!=successor
                ||!core.paused()||!core.mapReady()||!core.hasPlayedCharacter()||!core.playedCharacterAlive()||core.localPlayerId()<0)
            throw new IOException("Actual same-day successor Core after D5 required; DATA is not private epoch authority");
    }
    static Optional<CurrentRmtmEvent.PostSuccessionChoice> currentRmtmFirstPostSuccessionChoice(CurrentRmtmEventSource source,int actualActor)throws IOException {
        if(source==null||actualActor==-1||!source.sampledTwice()||!source.eventCensus().censusComplete()
                ||source.eventCensus().namedRootCount()!=source.eventCensus().events().size())
            throw new IOException("Complete actual ordinary event census required");
        if(source.eventCensus().events().isEmpty())return Optional.empty();
        // Multiple ordinary rows are valid. Never skip a refused/foreign/specialized first row.
        int instance=source.eventCensus().events().get(0).instanceId();
        var choice=CurrentRmtmEvent.postSuccessionChoice(source,actualActor,instance)
                .orElseThrow(()->new IOException("First actual event has no legal post-succession route; full DATA retained, no fallback"));
        if(choice.instanceId()!=instance)throw new IOException("Derived event choice changed actual first instance");
        return Optional.of(choice);
    }
    static void requireCurrentRmtmPostSuccessionCapacity(Set<Integer> attempted,int instance)throws IOException {
        if(attempted==null||instance<=0||attempted.contains(instance)||attempted.size()>=RMTM_POST_SUCCESSION_INSTANCE_LIMIT)
            throw new IOException("Original post-succession instance retained or Event64 capacity exhausted; no replay");
    }
    static void requireCurrentRmtmPostSuccessionDispatch(CurrentRmtmEventResult frame,CurrentRmtmEventResult query,
            CoreFrame.Prefix core,java.math.BigInteger connection,int instance)throws IOException {
        var source=requireCurrentRmtmEventQuery(query,CurrentRmtmEvent.Action.QUERY_SUMMARY,core,connection);
        var choice=currentRmtmFirstPostSuccessionChoice(source,core.playedCharacterId())
                .orElseThrow(()->new IOException("Original post-succession selection had no actual first event"));
        if(choice.instanceId()!=instance||frame.action()!=CurrentRmtmEvent.Action.CHOOSE_POST_SUCCESSION_FIRST_AVAILABLE
                ||frame.status()!=CurrentRmtmEventResult.Status.SELECTION_DISPATCHED||!frame.effectAttempted()||!frame.nativeReturned()||!frame.cleanupKnown()
                ||frame.claimSequence().signum()<=0||frame.instanceId().filter(n->n==instance).isEmpty()||!frame.source().equals(query.source())
                ||!frame.factsBefore().equals(query.factsBefore())||!frame.providerGeneration().equals(query.providerGeneration())
                ||!frame.querySequence().equals(query.querySequence())||frame.owner().filter(o->o.connectionGeneration().equals(connection)).isEmpty()
                ||frame.nativeHandled()||frame.eventClosed()||frame.newDateObserved()||frame.physicalSaveConfirmed())
            throw new IOException("Post-succession ACK lost immutable actual Source/Core/instance/lease or claimed unobserved afterstate");
    }
    @FunctionalInterface
    interface RmtmPostEventRead<C,R> { R read(C actual)throws IOException,InterruptedException; }
    static <C,R> R withCurrentRmtmPostEventRole(C before,RmtmPostEventRead<C,R> readRole,RmtmPostEventRead<C,C> drain)
            throws IOException,InterruptedException {
        var originalRole=readRole.read(before); // Native private anchor is admitted by this actual Role before any event query.
        var after=drain.read(before);
        if(after==null)throw new IOException("Post-event drain lost actual Core");
        return after==before?originalRole:readRole.read(after); // At most one refresh after this boundary's final new Core.
    }

    private static NativeGameTransport.CoreReceived drainCurrentRmtmPostSuccessionEvents(NativeGameTransport transport,GameSupervisorControl.Descriptor owner,
            NativeLaunchPlan plan,NativeGameTransport.CoreReceived initial,NativeObservationPort.TransportSession session,CoreFrame.Prefix expected,
            int song,int successor,int completedDays,int startingDate,Set<Integer> attempted,Path output,String label,Instant deadline,ObjectNode result,ObjectNode originals)
            throws IOException,InterruptedException {
        requireCurrentRmtmPostSuccessionBoundary(expected,song,successor,completedDays,startingDate);
        var core=initial;
        var query=readCurrentRmtmEvent(transport,owner,core,CurrentRmtmEvent.Action.QUERY_SUMMARY,session,output,label+"-initial-census",deadline,result,originals);
        result.put("post_succession_ordinary_census_checks",result.path("post_succession_ordinary_census_checks").intValue()+1);
        while(true){
            var choice=currentRmtmFirstPostSuccessionChoice(query.frame().source().orElseThrow(),expected.playedCharacterId());
            if(choice.isEmpty()){
                result.put(label+"_ordinary_complete_empty_observed",true);
                return core; // Ordinary empty DATA is not clearance of the independent runtime/Date gate.
            }
            int instance=choice.orElseThrow().instanceId();requireCurrentRmtmPostSuccessionCapacity(attempted,instance);
            var prepared=transport.prepareCurrentRmtmPostSuccessionEvent(query,instance);
            if(prepared.action()!=CurrentRmtmEvent.Action.CHOOSE_POST_SUCCESSION_FIRST_AVAILABLE||prepared.instanceId()!=instance
                    ||!prepared.deadline().equals(query.validUntil()))throw new IOException("Private post-succession preparation rebound original query");
            attempted.add(instance); // Retain before intent/write; every refusal/UNKNOWN stops this Main, never retries.
            String once=label+"-instance-"+instance+"-attempt-"+attempted.size();
            submitCurrentRmtmEvent(transport,owner,query,prepared,session,output,once,result,originals);
            core=readCurrentRmtmCore(transport,owner,plan,output,once+"-independent-core",deadline,result,originals,session,expected);
            requireCurrentRmtmAfterRequest(transport,core,prepared.requestId());
            var observed=readCurrentRmtmEvent(transport,owner,core,CurrentRmtmEvent.Action.QUERY_SUMMARY,session,output,once+"-after-census",deadline,result,originals);
            result.put("post_succession_ordinary_census_checks",result.path("post_succession_ordinary_census_checks").intValue()+1);
            if(!transport.currentRmtmEventAbsent(prepared,observed))throw new IOException("Original actual instance still present in independent complete census; no reselect");
            result.put(once+"_instance_absent_observed",true);
            query=observed; // Reuse this actual unused private census, not the consumed beforeSource.
        }
    }

    private static void acknowledgeCurrentRmtmChannel(NativeGameTransport transport,GameSupervisorControl.Descriptor owner,NativeLaunchPlan plan,CurrentRmtmEvent.Action action,
            NativeObservationPort.TransportSession session,CoreFrame.Prefix expected,Path output,String label,Instant deadline,ObjectNode result,ObjectNode originals)throws IOException,InterruptedException {
        var core=readCurrentRmtmCore(transport,owner,plan,output,label+"-before-core",deadline,result,originals,session,expected);
        var query=readCurrentRmtmEvent(transport,owner,core,action,session,output,label+"-before-query",deadline,result,originals);var prepared=transport.prepareCurrentRmtmEventAck(query);
        submitCurrentRmtmEvent(transport,owner,query,prepared,session,output,label+"-once",result,originals);
        var after=readCurrentRmtmCore(transport,owner,plan,output,label+"-after-core",deadline,result,originals,session,expected);requireCurrentRmtmAfterRequest(transport,after,prepared.requestId());
        var observed=readCurrentRmtmEvent(transport,owner,after,action,session,output,label+"-after-query",deadline,result,originals);
        if(!transport.currentRmtmEventAbsent(prepared,observed))throw new IOException("Original RMTM event instance still present in complete independent census");
        result.put(label+"_instance_absent_observed",true); // Does not assert event_closed or cleared Date permission.
    }
    private static NativeGameTransport.CoreReceived confirmCurrentRmtmD5(NativeGameTransport transport,GameSupervisorControl.Descriptor owner,NativeLaunchPlan plan,
            NativeGameTransport.RmtmAdvancePrepared day,CurrentRmtmActorTransitionResult pending,int song,int start,NativeObservationPort.TransportSession session,
            Path output,Instant deadline,ObjectNode result,ObjectNode originals)throws IOException,InterruptedException {
        var p=pending.progress().orElseThrow();int successor=p.afterActorId();var expected=currentRmtmAfter(pending.factsBefore().orElseThrow(),day.targetDateRaw(),successor);
        var after=readCurrentRmtmCore(transport,owner,plan,output,"rmtm-d5-after-pending-core",day.deadline(),result,originals,session,expected);requireCurrentRmtmAfterRequest(transport,after,pending.requestId());
        var role=readCurrentRmtmRole(transport,owner,after,session,output,"rmtm-d5-after-pending-role",day.deadline(),result,originals);
        var s=requireCurrentRmtmPositiveRole(role.frame(),expected,CurrentRmtmActorTransitionSource.Role.SUCCESSOR,java.math.BigInteger.ZERO,song,successor,true,5,start);
        var witness=s.pending().orElseThrow();
        if(!witness.operationId().equals(day.operationId())||!witness.claimSequence().equals(pending.claimSequence())||!witness.generation().equals(p.generation())
                ||!witness.originalDeadlineUnixMs().equals(java.math.BigInteger.valueOf(day.deadline().toEpochMilli()))||witness.beforeActorId()!=song||witness.afterActorId()!=successor
                ||witness.startingDateRaw()!=p.startingDateRaw()||witness.targetDateRaw()!=day.targetDateRaw())throw new IOException("Independent D5 pending differs from original actual operation/lease/full IDs");
        var epoch=transport.prepareCurrentRmtmEpoch(day,role);
        if(!epoch.operationId().equals(day.operationId())||!epoch.deadline().equals(role.validUntil())||epoch.deadline().isAfter(day.deadline()))throw new IOException("RMTM epoch must retain original D5 operation/unextended deadline");
        archiveCurrentRmtmIntent(output,"rmtm-d5-epoch-intent",epoch.requestId(),epoch.operationId(),epoch.deadline(),epoch.originalPacket().value(),originals);
        result.put("epoch_confirm_calls",1);var outcome=transport.submitCurrentRmtmEpoch(epoch);Path out=Files.createDirectory(output.resolve("rmtm-d5-epoch-result"));archiveCurrentLetterOutcome(transport,out,"rmtm_epoch",outcome,originals);
        if(!(outcome instanceof NativeActionPort.AckReceived ack))throw new IOException("Original D5 epoch refused/UNKNOWN; no reconfirmation");
        requireCurrentDjcAckOwner(transport,owner,ack,session);var f=CurrentRmtmActorTransitionResult.decodeOutcome(ack);originals.set("rmtm_epoch_original_result",write(out,"original-result.json",ack.originalResultToken().orElseThrow().bytes()));result.set("epoch_confirmation",FullJsonTree.parse(f.encode().bytes(),FullJsonTree.MAXIMUM_BYTES));
        if(!ack.requestId().equals(epoch.requestId())||epoch.latestFrame().filter(f::equals).isEmpty()||f.status()!=CurrentRmtmActorTransitionResult.Status.EPOCH_CONFIRMED||f.action()!=CurrentRmtmActorTransition.Action.CONFIRM_EPOCH
                ||!f.operationId().equals(day.operationId())||!f.accepted()||f.claimSequence().signum()<=0||!f.actorEpoch().equals(java.math.BigInteger.ONE)||f.completedNaturalDays()!=5||f.effectAttempted()||f.nativeReturned()||!f.cleanupKnown()
                ||!f.source().equals(role.frame().source())||!f.factsBefore().equals(role.frame().factsBefore())||!f.providerGeneration().equals(role.frame().providerGeneration())||!f.querySequence().equals(role.frame().querySequence())
                ||!f.deadlineUnixMs().equals(java.math.BigInteger.valueOf(epoch.deadline().toEpochMilli()))||!f.connectionGeneration().equals(session.connectionGeneration()))throw new IOException("Original D5 epoch1 receipt lost immutable proof/count5/zero Game effects");
        result.put("epoch_confirmed",true);var confirmed=readCurrentRmtmCore(transport,owner,plan,output,"rmtm-d5-after-epoch-core",deadline,result,originals,session,expected);requireCurrentRmtmAfterRequest(transport,confirmed,epoch.requestId());return confirmed;
    }
    private static void runCurrentRmtmOriginalCase(NativeGameTransport transport,GameSupervisorControl.Descriptor owner,NativeLaunchPlan plan,NativeGameTransport.RmtmRoleReceived capture,RmtmConfig config,
            NativeObservationPort.TransportSession session,Path output,Instant deadline,Duration readTimeout,ObjectNode result,ObjectNode originals)throws IOException,InterruptedException {
        var start=capture.frame().factsBefore().orElseThrow();int song=start.playedCharacterId(),successor=-1;var current=start;
        requireCurrentRmtmPositiveRole(capture.frame(),start,CurrentRmtmActorTransitionSource.Role.SONG,java.math.BigInteger.ZERO,song,-1,false,0,start.dateRaw());
        CurrentRmtmObservationResult d3=null,pre=null,post=null;CurrentRmtmObservationSource.Council council=null;
        var postSuccessionInstances=new java.util.HashSet<Integer>();
        for(int day=1;day<=8;day++){
            String label="rmtm-day"+String.format(java.util.Locale.ROOT,"%02d",day);var role=capture;
            if(day>1){var before=readCurrentRmtmCore(transport,owner,plan,output,label+"-before-core",deadline,result,originals,session,current);
                if(day>=6){
                    var expected=current;int actualSuccessor=successor,completedDays=day-1;
                    role=withCurrentRmtmPostEventRole(before,
                            actual->{var observed=readCurrentRmtmRole(transport,owner,actual,session,output,label+(actual==before?"-before-role":"-post-events-role"),deadline,result,originals);
                                requireCurrentRmtmPositiveRole(observed.frame(),expected,CurrentRmtmActorTransitionSource.Role.SUCCESSOR,java.math.BigInteger.ONE,song,actualSuccessor,false,completedDays,start.dateRaw());return observed;},
                            actual->drainCurrentRmtmPostSuccessionEvents(transport,owner,plan,actual,session,expected,song,actualSuccessor,completedDays,start.dateRaw(),postSuccessionInstances,output,label+"-post-succession-events",deadline,result,originals));
                }else role=readCurrentRmtmRole(transport,owner,before,session,output,label+"-before-role",deadline,result,originals);}
            requireCurrentRmtmPositiveRole(role.frame(),current,day<=5?CurrentRmtmActorTransitionSource.Role.SONG:CurrentRmtmActorTransitionSource.Role.SUCCESSOR,
                    day<=5?java.math.BigInteger.ZERO:java.math.BigInteger.ONE,song,successor,false,day-1,start.dateRaw());
            var prepared=transport.prepareCurrentRmtmAdvance(role);var terminal=runCurrentRmtmDay(transport,owner,role,prepared,config,session,output,label,deadline,readTimeout,result,originals);
            NativeGameTransport.CoreReceived after;
            if(day==5){successor=terminal.progress().orElseThrow().afterActorId();after=confirmCurrentRmtmD5(transport,owner,plan,prepared,terminal,song,start.dateRaw(),session,output,deadline,result,originals);}
            else {var expected=currentRmtmAfter(current,prepared.targetDateRaw(),current.playedCharacterId());after=readCurrentRmtmCore(transport,owner,plan,output,label+"-after-core",deadline,result,originals,session,expected);requireCurrentRmtmAfterRequest(transport,after,terminal.requestId());}
            current=((CoreFrame.Partial)after.frame()).prefix();result.put("natural_days_observed",day);
            if(day==1){
                acknowledgeCurrentRmtmChannel(transport,owner,plan,CurrentRmtmEvent.Action.QUERY_CHAOS,session,current,output,"rmtm-chaos",deadline,result,originals);
                acknowledgeCurrentRmtmChannel(transport,owner,plan,CurrentRmtmEvent.Action.QUERY_SUMMARY,session,current,output,"rmtm-summary",deadline,result,originals);
            }
            if(day==3){
                var actualRole=readCurrentRmtmRole(transport,owner,after,session,output,"rmtm-d3-after-role",deadline,result,originals);
                requireCurrentRmtmPositiveRole(actualRole.frame(),current,CurrentRmtmActorTransitionSource.Role.SONG,java.math.BigInteger.ZERO,song,-1,false,3,start.dateRaw());
                var q=observeCurrentRmtm(transport,owner,plan,CurrentRmtmObservation.Action.QUERY_TITLE_PHASE,Optional.of(CurrentRmtmObservation.Phase.D3),Optional.empty(),session,current,output,"rmtm-d3-title",deadline,result,originals);d3=q.query().frame();
                var p=d3.source().orElseThrow().titlePhase().orElseThrow();requireCurrentRmtmPhysicalHolder(p.physical(),current);currentRmtmPhysicalLawForm(p.physical(),p.scriptOwnSingleHeir(),p.holderRealmSingleHeir());
                council=observeCurrentRmtm(transport,owner,plan,CurrentRmtmObservation.Action.QUERY_COUNCIL,Optional.empty(),Optional.empty(),session,current,output,"rmtm-d3-council",deadline,result,originals).query().frame().source().orElseThrow().council().orElseThrow();requireCurrentRmtmCouncilRetained(council,council);
            }
            if(day==4){
                var seats=observeCurrentRmtm(transport,owner,plan,CurrentRmtmObservation.Action.QUERY_COUNCIL,Optional.empty(),Optional.empty(),session,current,output,"rmtm-d4-council",deadline,result,originals).query().frame().source().orElseThrow().council().orElseThrow();requireCurrentRmtmCouncilRetained(Objects.requireNonNull(council),seats);
                openAndCancelCurrentRmtmView(transport,owner,plan,Optional.empty(),session,current,output,"rmtm-d4-budget",deadline,result,originals);
                openAndCancelCurrentRmtmView(transport,owner,plan,Optional.of(CurrentRmtmObservation.OfferTarget.RELEASED_A),session,current,output,"rmtm-d4-offer-a",deadline,result,originals);
                navigateCurrentRmtmDecision(transport,owner,plan,NativeGameTransport.RmtmDecisionPurpose.CONTINUE,CurrentRmtmDecision.DecisionKey.CONTINUE_CORE,true,session,current,output,"rmtm-continue",deadline,result,originals);
                pre=observeCurrentRmtm(transport,owner,plan,CurrentRmtmObservation.Action.QUERY_TITLE_PHASE,Optional.of(CurrentRmtmObservation.Phase.PREDEATH),Optional.empty(),session,current,output,"rmtm-predeath-title",deadline,result,originals).query().frame();
            }
            if(day==7){post=observeCurrentRmtm(transport,owner,plan,CurrentRmtmObservation.Action.QUERY_TITLE_PHASE,Optional.of(CurrentRmtmObservation.Phase.POSTDEATH),Optional.empty(),session,current,output,"rmtm-postdeath-title",deadline,result,originals).query().frame();requireCurrentRmtmTitlePhases(Objects.requireNonNull(d3),Objects.requireNonNull(pre),post);result.put("three_physical_phases_observed",true);}
            if(day==8){var seats=observeCurrentRmtm(transport,owner,plan,CurrentRmtmObservation.Action.QUERY_COUNCIL,Optional.empty(),Optional.empty(),session,current,output,"rmtm-d8-council",deadline,result,originals).query().frame().source().orElseThrow().council().orElseThrow();requireCurrentRmtmCouncilRetained(Objects.requireNonNull(council),seats);}
        }
        result.put("original_private_channel_completed",true).put("original_logs_and_execute_dump_consumer_pending",true);
        // D8 matches the original focused driver; 14 remains the native cap. No blind wait, logs API, forced fixture effect or 26-business PASS.
    }
    private static void initializeCurrentRmtmResult(ObjectNode result,RmtmConfig config,String machine){
        result.put("schema","xar.native-owner-current-rmtm-remaining/v1").put("mode",switch(config.mode()){case QUERY_ROLE->"current_rmtm_query_role";case QUERY_DECISION->"current_rmtm_query_decision";
                case ORIGINAL_CASE_ONCE->"current_rmtm_original_case_once";case THRESHOLD_50_51_ONCE->"current_rmtm_threshold_50_51_once";})
                .put("machine_id",machine).put("read_calls",0).put("advance_calls",0).put("status_queries",0).put("epoch_confirm_calls",0).put("event_ack_calls",0).put("decision_action_calls",0)
                .put("maximum_natural_days",14).put("natural_days_observed",0).put("query_available",false).put("event_closed",false).put("decision_applied",false)
                .put("d5_execute_identity_observed",false).put("rmtm26_business_pass",false).put("physical_save_confirmed",false).put("save_calls",0)
                .put("threshold_private_dispatch_chain_completed",false).put("original_case_contracts_bound",true)
                .put("post_succession_ordinary_census_checks",0).put("post_succession_event_calls",0);
    }
    private static void runCurrentRmtm(NativeGameTransport transport,GameSupervisorControl.Descriptor owner,NativeLaunchPlan plan,RmtmConfig config,Path output,
            Instant deadline,Duration readTimeout,ObjectNode result,ObjectNode originals)throws IOException,InterruptedException {
        try{
            if(!(plan.load() instanceof NativeLaunchPlan.SavedGame))throw new IOException("RMTM requires its actual SavedGame owner");
            var core=readCurrentRmtmCore(transport,owner,plan,output,"rmtm-core-before",deadline,result,originals,null,null);
            var session=core.original().custody().orElseThrow().session();result.set("session",session(session));
            if(config.mode()==RmtmMode.QUERY_DECISION){readCurrentRmtmDecision(transport,owner,core,session,output,"rmtm-decision-query",deadline,result,originals);result.put("query_available",true);return;}
            var role=readCurrentRmtmRole(transport,owner,core,session,output,"rmtm-role-query",deadline,result,originals);result.put("query_available",true);
            if(config.queryOnly())return;
            if(config.mode()==RmtmMode.THRESHOLD_50_51_ONCE)runCurrentRmtmThreshold(transport,owner,plan,role,config,session,output,deadline,readTimeout,result,originals);
            else runCurrentRmtmOriginalCase(transport,owner,plan,role,config,session,output,deadline,readTimeout,result,originals);
        }finally{
            archiveNaturalDiagnostics(output,originals,transport.diagnostics());var progress=result.deepCopy();progress.set("originals",originals.deepCopy());
            write(output,"current-rmtm-progress.json",FullJsonTree.encode(progress,FullJsonTree.MAXIMUM_BYTES));
        }
    }

    record RmtmTitleQueryConfig(){int submissions(){return 2;}}
    static RmtmTitleQueryConfig currentRmtmTitleQueryConfig(ObjectNode config){
        StrictJson.require("xar.native-owner-snapshot-config/v46".equals(StrictJson.text(config.get("schema")))
                &&"current_rmtm_primary_title_query".equals(StrictJson.text(config.get("mode"))),"Only explicit readonly RMTM primary Title query");
        StrictJson.object(config,Set.of("schema","mode","owner_descriptor","overall_timeout_seconds","read_timeout_seconds","maximum_frames_per_operation"));
        ExactRef.fromJson(config.get("owner_descriptor"));StrictJson.integer(config.get("overall_timeout_seconds"),1,600);
        StrictJson.integer(config.get("read_timeout_seconds"),1,60);StrictJson.integer(config.get("maximum_frames_per_operation"),1,65536);return new RmtmTitleQueryConfig();
    }
    static CurrentRmtmTitleQuerySource requireCurrentRmtmTitleQueryFrame(CurrentRmtmTitleQueryResult frame,CoreFrame.Prefix core,java.math.BigInteger connection)throws IOException{
        if(!frame.successful()||!frame.cleanupKnown()||frame.claimSequence().signum()!=0||frame.effectAttempted()||frame.nativeReturned()||frame.nativeHandled()
                ||frame.providerGeneration().signum()<=0||frame.querySequence().signum()<=0||frame.factsBefore().filter(core::equals).isEmpty()
                ||frame.owner().filter(value->value.connectionGeneration().equals(connection)).isEmpty()||frame.source().isEmpty())
            throw new IOException("Actual RMTM title read differs from original Core/connection/readonly response");
        var source=frame.source().orElseThrow();if(source.actorId()!=core.playedCharacterId()||!source.sampledTwice())throw new IOException("Actual RMTM actor/two samples differ");
        return source; // EMPTY laws/null holder are DATA; never infer realm/effective law or D5 execute-time heir.
    }
    static void initializeCurrentRmtmTitleQueryResult(ObjectNode result,String machine){
        result.put("schema","xar.native-owner-current-rmtm-title-query/v1").put("mode","current_rmtm_primary_title_query").put("machine_id",machine)
                .put("read_calls",0).put("query_calls",0).put("source_available",false).put("effect_attempted",false).put("native_returned",false).put("native_handled",false)
                .put("effective_law_observed",false).put("realm_law_observed",false).put("rmtm_rules_confirmed",false).put("phase_control_authorized",false)
                .put("execute_time_heir_witness",false).put("rmtm26_business_pass",false).put("new_date_observed",false).put("physical_save_confirmed",false).put("date_calls",0).put("save_calls",0);
    }
    private static void runCurrentRmtmTitleQuery(NativeGameTransport transport,GameSupervisorControl.Descriptor owner,NativeLaunchPlan plan,Path output,
            Instant deadline,ObjectNode result,ObjectNode originals)throws IOException,InterruptedException{
        try{
            if(!(plan.load() instanceof NativeLaunchPlan.SavedGame))throw new IOException("RMTM title query uses its actual Saved owner; no phase or eligibility inferred");
            stage="RMTM_TITLE_FRESH_ACTUAL_CORE";
            var before=readCurrentRiteCreateCore(transport,owner,plan,null,output,"core-before-rmtm-title",deadline,result,originals);
            var prefix=requireCurrentRiteCreateCore(before.frame());var actualSession=before.original().custody().orElseThrow().session();result.set("session",session(actualSession));
            Instant until=before.validUntil().isBefore(deadline)?before.validUntil():deadline;before.requireOriginal(transport,until);
            stage="RMTM_TITLE_ACTUAL_PRIVATE_READ";var read=transport.readCurrentRmtmTitleQuery(before,until);
            Path queryOut=Files.createDirectory(output.resolve("rmtm-title-query"));archiveCurrentLetterOutcome(transport,queryOut,"rmtm_title_query",read.original(),originals);
            result.put("query_calls",1).put("read_calls",2);
            if(!(read instanceof NativeGameTransport.RmtmTitleQueryReceived query))throw new IOException("Actual RMTM title Source unavailable or UNKNOWN; no EMPTY fallback or retry");
            until=query.validUntil().isBefore(until)?query.validUntil():until;query.requireOriginal(transport,until);requireCurrentDjcAckOwner(transport,owner,query.original(),actualSession);
            var frame=CurrentRmtmTitleQueryResult.decodeOutcome(query.original());if(!frame.equals(query.frame()))throw new IOException("Actual RMTM title ACK differs from private immutable response");
            var source=requireCurrentRmtmTitleQueryFrame(frame,prefix,actualSession.connectionGeneration());
            originals.set("rmtm_title_original_result",write(queryOut,"original-result.json",query.original().originalResultToken().orElseThrow().bytes()));
            result.set("rmtm_title_result",FullJsonTree.parse(frame.encode().bytes(),SMALL));result.set("physical_title_source",source.encode());
            result.put("source_available",true).put("full_title_id",source.fullTitleId()).put("physical_own_laws_known_empty",source.nativeLawCount()==0);
        }finally{archiveNaturalDiagnostics(output,originals,transport.diagnostics());}
    }

    record RiteCreationBlockersConfig(long sourceRiteId) {int submissions(){return 2;}}
    static RiteCreationBlockersConfig currentRiteCreationBlockersConfig(ObjectNode config) {
        StrictJson.require("xar.native-owner-snapshot-config/v43".equals(StrictJson.text(config.get("schema")))
                &&"current_rite_creation_blockers".equals(StrictJson.text(config.get("mode"))),"Only explicit v43 readonly Rite blockers mode");
        StrictJson.object(config,Set.of("schema","mode","owner_descriptor","overall_timeout_seconds","read_timeout_seconds","maximum_frames_per_operation","expected_source_rite_id"));
        ExactRef.fromJson(config.get("owner_descriptor"));
        StrictJson.integer(config.get("overall_timeout_seconds"),1,600);StrictJson.integer(config.get("read_timeout_seconds"),1,60);
        StrictJson.integer(config.get("maximum_frames_per_operation"),1,65536);
        return new RiteCreationBlockersConfig(StrictJson.integer(config.get("expected_source_rite_id"),0,0xffff_fffeL));
    }
    static CoreFrame.Prefix requireCurrentRiteCreationBlockersCore(CoreFrame frame)throws IOException {
        return requireCurrentRiteCreateCore(frame); // Paused living Core facts only; no Create permission or preparation.
    }
    static CurrentRiteCreationBlockersSource requireCurrentRiteCreationBlockersFrame(CurrentRiteCreationBlockersResult frame,
            CoreFrame.Prefix core,long sourceRiteId,java.math.BigInteger connection)throws IOException {
        if(frame.status()!=CurrentRiteCreationBlockersResult.Status.AVAILABLE||!frame.successful()||!frame.sourceAvailable()
                ||!frame.cleanupKnown()||frame.claimSequence().signum()!=0||frame.effectAttempted()||frame.nativeReturned()||frame.nativeHandled()
                ||frame.providerGeneration().signum()<=0||frame.querySequence().signum()<=0||frame.source().isEmpty()
                ||frame.factsBefore().filter(core::equals).isEmpty()||frame.owner().isEmpty()
                ||!frame.owner().orElseThrow().connectionGeneration().equals(connection))
            throw new IOException("Actual readonly blockers differs from complete original Core/connection/receipt");
        var source=frame.source().orElseThrow();
        if(source.sourceRiteId()!=sourceRiteId||source.actorId()!=core.playedCharacterId()||!source.sampledTwice())
            throw new IOException("Actual blockers Source differs from sourceRite DATA/current actor/two samples");
        // False Can/creating/visibility/enabled and empty/control/richtext/NUL strings
        // are real read DATA. Never trim, apply setter bounds, or infer permission.
        return source;
    }
    static void initializeCurrentRiteCreationBlockersResult(ObjectNode result,RiteCreationBlockersConfig config,String machineId) {
        result.put("schema","xar.native-owner-current-rite-creation-blockers/v1").put("mode","current_rite_creation_blockers")
                .put("machine_id",machineId).put("steam_build_id","26785313").put("action","query_blockers")
                .put("expected_source_rite_id",config.sourceRiteId()).put("read_calls",0).put("query_calls",0).put("source_available",false)
                .putNull("is_creating").putNull("native_can_create").putNull("blockers_text").putNull("window_visible").putNull("window_enabled").putNull("sampled_twice")
                .put("effect_attempted",false).put("native_returned",false).put("native_handled",false)
                .put("create_authorized",false).put("create_calls",0).put("accept_calls",0).put("new_date_observed",false)
                .put("physical_save_confirmed",false).put("date_calls",0).put("save_calls",0).put("tooltip_render_observed",false);
    }
    private static void runCurrentRiteCreationBlockers(NativeGameTransport transport,GameSupervisorControl.Descriptor owner,NativeLaunchPlan plan,
            RiteCreationBlockersConfig config,Path output,Instant deadline,ObjectNode result,ObjectNode originals)throws IOException,InterruptedException {
        try {
            if(!(plan.load() instanceof NativeLaunchPlan.SavedGame))throw new IOException("Rite blockers requires actual SavedGame owner");
            stage="RITE_CREATION_BLOCKERS_FRESH_ACTUAL_CORE";
            var before=readCurrentRiteCreateCore(transport,owner,plan,null,output,"core-before-rite-creation-blockers",deadline,result,originals);
            var prefix=requireCurrentRiteCreationBlockersCore(before.frame());var actualSession=before.original().custody().orElseThrow().session();
            result.set("session",session(actualSession));
            Instant until=before.validUntil().isBefore(deadline)?before.validUntil():deadline;before.requireOriginal(transport,until);
            stage="RITE_CREATION_BLOCKERS_ACTUAL_PRIVATE_QUERY";
            var read=transport.readCurrentRiteCreationBlockers(before,config.sourceRiteId(),until);
            Path queryOutput=Files.createDirectory(output.resolve("rite-creation-blockers-query"));
            archiveCurrentLetterOutcome(transport,queryOutput,"rite_creation_blockers_query",read.original(),originals);
            result.put("query_calls",1).put("read_calls",2);
            if(!(read instanceof NativeGameTransport.RiteCreationBlockersReceived query))throw new IOException("Actual blockers unavailable or UNKNOWN; no cached false/replacement/retry");
            until=query.validUntil().isBefore(until)?query.validUntil():until;query.requireOriginal(transport,until);
            requireCurrentDjcAckOwner(transport,owner,query.original(),actualSession);
            var frame=CurrentRiteCreationBlockersResult.decodeOutcome(query.original());
            if(!frame.equals(query.frame()))throw new IOException("This blockers ACK differs from private immutable query frame");
            var source=requireCurrentRiteCreationBlockersFrame(frame,prefix,config.sourceRiteId(),actualSession.connectionGeneration());
            originals.set("blockers_original_result",write(queryOutput,"original-result.json",query.original().originalResultToken().orElseThrow().bytes()));
            result.set("blockers_result",FullJsonTree.parse(frame.encode().bytes(),SMALL));
            result.put("source_available",true).put("is_creating",source.isCreating()).put("native_can_create",source.nativeCanCreate())
                    .put("blockers_text",source.blockersText()).put("window_visible",source.windowVisible()).put("window_enabled",source.windowEnabled())
                    .put("sampled_twice",source.sampledTwice());
        } finally {
            archiveNaturalDiagnostics(output,originals,transport.diagnostics());
            var progress=result.deepCopy();progress.set("originals",originals.deepCopy());
            write(output,"current-rite-creation-blockers-progress.json",FullJsonTree.encode(progress,FullJsonTree.MAXIMUM_BYTES));
        }
    }

    enum CccMode { QUERY_ROLE, QUERY_EVENT, QUERY_DECISION, ORIGINAL_CASE_ONCE }
    record CccConfig(CccMode mode,int maximumStatusPolls,long statusPollDelayMillis) {
        boolean queryOnly(){return mode!=CccMode.ORIGINAL_CASE_ONCE;}
        int submissions(){return queryOnly()?2:Math.addExact(87,Math.multiplyExact(13,maximumStatusPolls));}
    }
    static CccConfig currentCccConfig(ObjectNode config) {
        StrictJson.require("xar.native-owner-snapshot-config/v45".equals(StrictJson.text(config.get("schema"))),"Explicit v45 CCC family required");
        CccMode mode=switch(StrictJson.text(config.get("mode"))) {
            case "current_ccc_query_role"->CccMode.QUERY_ROLE;
            case "current_ccc_query_event"->CccMode.QUERY_EVENT;
            case "current_ccc_query_decision"->CccMode.QUERY_DECISION;
            case "current_ccc_original_case_once"->CccMode.ORIGINAL_CASE_ONCE;
            default->throw new IllegalArgumentException("Only three readonly CCC queries or the fixed original CCC case");
        };
        var fields=new java.util.HashSet<>(Set.of("schema","mode","owner_descriptor","overall_timeout_seconds","read_timeout_seconds","maximum_frames_per_operation"));
        if(mode==CccMode.ORIGINAL_CASE_ONCE){fields.add("maximum_status_polls");fields.add("status_poll_delay_ms");}
        StrictJson.object(config,Set.copyOf(fields));
        ExactRef.fromJson(config.get("owner_descriptor"));
        StrictJson.integer(config.get("overall_timeout_seconds"),1,600);
        StrictJson.integer(config.get("read_timeout_seconds"),1,60);
        StrictJson.integer(config.get("maximum_frames_per_operation"),1,65536);
        return new CccConfig(mode,mode==CccMode.ORIGINAL_CASE_ONCE?Math.toIntExact(StrictJson.integer(config.get("maximum_status_polls"),1,256)):0,
                mode==CccMode.ORIGINAL_CASE_ONCE?StrictJson.integer(config.get("status_poll_delay_ms"),1,1000):0);
    }

    static void requireCurrentCccRole(CurrentCccActorTransitionResult frame,CoreFrame.Prefix prefix)throws IOException {
        if(frame.action()!=CurrentCccActorTransition.Action.QUERY_ROLE||frame.status()!=CurrentCccActorTransitionResult.Status.AVAILABLE||!frame.ok()||frame.accepted()
                ||!frame.operationId().isEmpty()||frame.claimSequence().signum()!=0||frame.effectAttempted()||frame.nativeReturned()||!frame.cleanupKnown()
                ||frame.providerGeneration().signum()<=0||frame.querySequence().signum()<=0||frame.connectionGeneration().signum()<=0
                ||frame.factsBefore().filter(prefix::equals).isEmpty()||frame.source().isEmpty()||frame.progress().isPresent())throw new IOException("Actual CCC role query lacks original Core/whole Source/private lease");
    }
    static CurrentCccActorTransitionSource requireCurrentCccPositiveRole(CurrentCccActorTransitionResult frame,CoreFrame.Prefix prefix,
            CurrentCccActorTransitionSource.Role role,java.math.BigInteger epoch,int song,int recipient,boolean confirm,int days,int caseStart)throws IOException {
        requireCurrentCccRole(frame,prefix);var source=frame.source().orElseThrow();
        if(!source.definitionFound()||!source.nativeShown().orElse(false)||!source.runtimeReady()||!source.predecessorResolved()||source.role()!=role
                ||!source.actorEpoch().equals(epoch)||!frame.actorEpoch().equals(epoch)||source.completedNaturalDays()!=days||frame.completedNaturalDays()!=days||source.maximumNaturalDays()!=13||source.caseStartDateRaw()!=caseStart||(long)caseStart+24L*days!=prefix.dateRaw()||source.songActorId().filter(id->id==song).isEmpty()
                ||(role==CurrentCccActorTransitionSource.Role.SONG?prefix.playedCharacterId()!=song:prefix.playedCharacterId()!=recipient||source.officialActorId().filter(id->id==recipient).isEmpty())
                ||(confirm?!source.confirmAdmissible():!source.advanceAdmissible()))throw new IOException("Actual shown CCC role/epoch/actor IDs do not admit this fixed next step");
        return source;
    }
    static void requireCurrentCccDayTerminal(CurrentCccActorTransitionResult frame,CoreFrame.Prefix start,String operation,int target,boolean firstDay,int expectedDays)throws IOException {
        var status=firstDay?CurrentCccActorTransitionResult.Status.TRANSITION_PENDING:CurrentCccActorTransitionResult.Status.COMPLETED_DAY;
        if(frame.status()!=status||!frame.ok()||!frame.accepted()||!frame.operationId().equals(operation)||frame.factsBefore().filter(start::equals).isEmpty()
                ||frame.claimSequence().signum()<=0||frame.completedNaturalDays()!=expectedDays||!frame.cleanupKnown()||!frame.effectAttempted()||!frame.nativeReturned()
                ||!frame.actorEpoch().equals(firstDay?java.math.BigInteger.ZERO:java.math.BigInteger.ONE)||frame.progress().isEmpty())throw new IOException("CCC requires exact D1 pending or D2 completed, never generic actor-abort/refusal/UNKNOWN");
        var p=frame.progress().orElseThrow();
        if(p.generation().signum()<=0||p.startingDateRaw()!=start.dateRaw()||(long)start.dateRaw()+24!=target||p.targetDateRaw()!=target||p.lastObservedDateRaw()!=target
                ||p.beforeActorId()!=start.playedCharacterId()||p.afterActorId()==-1||p.completedDailyTicks()!=1||p.failureFlags()!=0||p.overshootDays()!=0
                ||!p.armAttempted()||!p.resumeAttempted()||!p.resumeSubmitted()||!p.exactDayConfirmed()||!p.shutdownSafe()||p.armed()||p.accessCleanupUnknown()
                ||p.transitionPending()!=firstDay||(firstDay?p.afterActorId()==p.beforeActorId():p.afterActorId()!=p.beforeActorId()))throw new IOException("CCC terminal must contain one actual daily tick, exact24, correct actors and disarmed known cleanup");
    }
    static CoreFrame.Prefix currentCccAfter(CoreFrame.Prefix before,int date,int actor)throws IOException {
        if(actor==-1||(long)before.dateRaw()+24!=date)throw new IOException("Exact one-day actual actor proof required");
        return new CoreFrame.Prefix(date,before.speed(),before.paused(),before.localPlayerId(),before.mapReady(),before.hasPlayedCharacter(),actor,before.playedCharacterAlive());
    }
    private static NativeGameTransport.CoreReceived readCurrentCccCore(NativeGameTransport transport,GameSupervisorControl.Descriptor owner,NativeLaunchPlan plan,
            Path output,String label,Instant deadline,ObjectNode result,ObjectNode originals,NativeObservationPort.TransportSession expectedSession,CoreFrame.Prefix expected)throws IOException,InterruptedException {
        stage="FRESH_INDEPENDENT_CCC_CORE";result.put("read_calls",result.path("read_calls").intValue()+1);
        var read=transport.readCoreFrameReceived(deadline);archiveCurrentLetterOutcome(transport,Files.createDirectory(output.resolve(label)),label,read.original(),originals);
        if(!(read instanceof NativeGameTransport.CoreReceived before)||!(before.frame() instanceof CoreFrame.Partial core))throw new IOException("Actual CCC Core unavailable; stop without action/retry");
        requireCurrentDjcAckOwner(transport,owner,before.original(),expectedSession);var p=core.prefix();
        if(core.build()!=ExactCk3Build.CK3_121003_STEAM_26785313||!core.build().executableSha256().equalsIgnoreCase(plan.sources().review().gameExecutable().sha256())||!core.build().coreFrameAdapterId().equals(plan.adapterId())
                ||!p.paused()||!p.mapReady()||!p.hasPlayedCharacter()||!p.playedCharacterAlive()||p.playedCharacterId()==-1||p.localPlayerId()<0||p.speed()<1||p.speed()>5||expected!=null&&!expected.equals(p))throw new IOException("Exact current paused living independent CCC Core differs");
        before.requireOriginal(transport,before.validUntil().isBefore(deadline)?before.validUntil():deadline);return before;
    }
    private static NativeGameTransport.CccRoleReceived readCurrentCccRole(NativeGameTransport transport,GameSupervisorControl.Descriptor owner,NativeGameTransport.CoreReceived before,
            NativeObservationPort.TransportSession session,Path output,String label,Instant deadline,ObjectNode result,ObjectNode originals)throws IOException,InterruptedException {
        Instant until=before.validUntil().isBefore(deadline)?before.validUntil():deadline;stage="ONE_READONLY_CCC_ROLE";result.put("read_calls",result.path("read_calls").intValue()+1);
        var read=transport.readCurrentCccRole(before,until);Path queryOutput=Files.createDirectory(output.resolve(label));archiveCurrentLetterOutcome(transport,queryOutput,label,read.original(),originals);
        if(!(read instanceof NativeGameTransport.CccRoleReceived query))throw new IOException("Actual CCC role refused/UNKNOWN; never substitute a caller role");
        query.requireOriginal(transport,query.validUntil());var ack=query.original();requireCurrentDjcAckOwner(transport,owner,ack,session);var frame=CurrentCccActorTransitionResult.decodeOutcome(ack);
        if(!frame.equals(query.frame())||query.validUntil().isAfter(until)||!frame.deadlineUnixMs().equals(java.math.BigInteger.valueOf(query.validUntil().toEpochMilli()))||!frame.connectionGeneration().equals(session.connectionGeneration()))throw new IOException("CCC private query changed this ACK/original deadline/connection");
        requireCurrentCccRole(frame,((CoreFrame.Partial)before.frame()).prefix());originals.set(label+"_original_result",write(queryOutput,"original-result.json",ack.originalResultToken().orElseThrow().bytes()));
        result.set(label,FullJsonTree.parse(frame.encode().bytes(),SMALL));return query;
    }
    private static void archiveCurrentCccIntent(Path output,String label,String requestId,String operation,Instant deadline,byte[] packet,ObjectNode originals)throws IOException {
        Path action=Files.createDirectory(output.resolve(label));var intent=StrictJson.object().put("schema","xar.current-ccc-original-intent/v1").put("request_id",requestId).put("operation_id",operation)
                .put("original_deadline_utc",deadline.toString()).put("independent_after_core_verified",false).put("physical_save_confirmed",false);
        intent.set("original_outbound",write(action,"original-request.packet",packet));originals.set(label+"_intent",write(action,"original-intent.json",FullJsonTree.encode(intent,SMALL)));
    }
    private static CurrentCccActorTransitionResult archiveCurrentCccOperation(NativeGameTransport transport,GameSupervisorControl.Descriptor owner,NativeGameTransport.CccAdvancePrepared prepared,
            NativeGameTransport.CccRoleReceived originalRole,NativeActionPort.DispatchOutcome outcome,NativeObservationPort.TransportSession session,Path output,String label,ObjectNode result,ObjectNode originals)throws IOException {
        Path actual=Files.createDirectory(output.resolve(label));archiveCurrentLetterOutcome(transport,actual,label,outcome,originals);
        if(!(outcome instanceof NativeActionPort.AckReceived ack))throw new IOException("Original CCC advance/status refused or UNKNOWN; do not retry/replay");
        requireCurrentDjcAckOwner(transport,owner,ack,session);var f=CurrentCccActorTransitionResult.decodeOutcome(ack);
        originals.set(label+"_original_result",write(actual,"original-result.json",ack.originalResultToken().orElseThrow().bytes()));result.set(label,FullJsonTree.parse(f.encode().bytes(),SMALL));
        var q=originalRole.frame();
        if(prepared.originalUnknown()||prepared.latestFrame().filter(f::equals).isEmpty()||!f.operationId().equals(prepared.operationId())||!f.deadlineUnixMs().equals(java.math.BigInteger.valueOf(prepared.deadline().toEpochMilli()))
                ||!f.providerGeneration().equals(q.providerGeneration())||!f.querySequence().equals(q.querySequence())||!f.factsBefore().equals(q.factsBefore())||!f.connectionGeneration().equals(session.connectionGeneration())||!f.cleanupKnown()
                ||f.action()!=CurrentCccActorTransition.Action.ADVANCE_DAY&&f.action()!=CurrentCccActorTransition.Action.QUERY_OPERATION
                ||f.action()==CurrentCccActorTransition.Action.QUERY_OPERATION&&f.source().isPresent()
                ||f.action()==CurrentCccActorTransition.Action.ADVANCE_DAY&&!f.source().equals(q.source()))throw new IOException("Original CCC operation lost this ACK/full source/Core/lease/ID/deadline or became UNKNOWN");
        if(f.status()!=CurrentCccActorTransitionResult.Status.SUBMITTED&&f.status()!=CurrentCccActorTransitionResult.Status.RUNNING&&f.status()!=CurrentCccActorTransitionResult.Status.TRANSITION_PENDING&&f.status()!=CurrentCccActorTransitionResult.Status.COMPLETED_DAY)
            throw new IOException("Actual CCC operation refused/unknown; no fresh-ID workaround");
        return f;
    }
    private static CurrentCccActorTransitionResult runCurrentCccDay(NativeGameTransport transport,GameSupervisorControl.Descriptor owner,NativeGameTransport.CccRoleReceived role,
            NativeGameTransport.CccAdvancePrepared prepared,CccConfig config,NativeObservationPort.TransportSession session,Path output,String label,Instant parentDeadline,Duration readTimeout,
            ObjectNode result,ObjectNode originals,boolean firstDay)throws IOException,InterruptedException {
        if(!prepared.deadline().equals(role.validUntil())||prepared.deadline().isAfter(parentDeadline)||prepared.targetDateRaw()!=Math.addExact(role.frame().factsBefore().orElseThrow().dateRaw(),24))throw new IOException("Original CCC day preparation changed source/deadline/24 target");
        archiveCurrentCccIntent(output,label+"-intent",prepared.requestId(),prepared.operationId(),prepared.deadline(),prepared.originalPacket().value(),originals);
        stage="ONCE_FIXED_CCC_ADVANCE";result.put("advance_calls",result.path("advance_calls").intValue()+1);
        var outcome=transport.submitCurrentCccAdvance(prepared);
        var frame=archiveCurrentCccOperation(transport,owner,prepared,role,outcome,session,output,label+"-submit",result,originals);
        for(int i=0;frame.status()==CurrentCccActorTransitionResult.Status.SUBMITTED||frame.status()==CurrentCccActorTransitionResult.Status.RUNNING;i++) {
            if(i>=config.maximumStatusPolls())throw new IOException("Bounded original CCC status observations exhausted; preserve original operation without retry");
            if(!Instant.now().plusMillis(config.statusPollDelayMillis()).isBefore(parentDeadline))throw new IOException("Original parent deadline cannot be extended by CCC polling");
            Thread.sleep(config.statusPollDelayMillis());Instant receive=Instant.now().plus(readTimeout);if(receive.isAfter(parentDeadline))receive=parentDeadline;
            stage="READONLY_ORIGINAL_CCC_OPERATION_STATUS";result.put("status_queries",result.path("status_queries").intValue()+1);
            var status=transport.queryCurrentCccOperation(prepared,receive);
            frame=archiveCurrentCccOperation(transport,owner,prepared,role,status,session,output,label+"-status-"+String.format(java.util.Locale.ROOT,"%03d",i+1),result,originals);
        }
        requireCurrentCccDayTerminal(frame,role.frame().factsBefore().orElseThrow(),prepared.operationId(),prepared.targetDateRaw(),firstDay,role.frame().source().orElseThrow().completedNaturalDays()+1);return frame;
    }
    static CurrentCccEventSource requireCurrentCccEventQuery(CurrentCccEventResult f,CoreFrame.Prefix core,java.math.BigInteger connection)throws IOException {
        if(f.action()!=CurrentCccEvent.Action.QUERY||f.status()!=CurrentCccEventResult.Status.AVAILABLE||!f.cleanupKnown()||f.effectAttempted()||f.nativeReturned()
                ||f.claimSequence().signum()!=0||f.instanceId().isPresent()||f.source().isEmpty()||f.providerGeneration().signum()<=0||f.querySequence().signum()<=0
                ||f.factsBefore().filter(core::equals).isEmpty()||f.owner().filter(o->o.connectionGeneration().equals(connection)).isEmpty())
            throw new IOException("CCC readonly event ACK differs from original Core/connection/complete Source");
        var s=f.source().orElseThrow();if(!s.sampledTwice()||!s.eventCensus().censusComplete()||s.eventCensus().namedRootCount()!=s.eventCensus().events().size())
            throw new IOException("Actual complete CCC event census required; no empty fallback");
        return s;
    }
    static void requireCurrentCccEventDispatch(CurrentCccEventResult f,CurrentCccEventResult q,CoreFrame.Prefix core,
            java.math.BigInteger connection,CurrentCccEvent.Action action,int instance)throws IOException {
        var s=requireCurrentCccEventQuery(q,core,connection);
        if(f.action()!=action||f.status()!=CurrentCccEventResult.Status.SELECTION_DISPATCHED||!f.effectAttempted()||!f.nativeReturned()||!f.cleanupKnown()
                ||f.claimSequence().signum()<=0||f.instanceId().filter(n->n==instance).isEmpty()||!f.source().equals(q.source())||!f.factsBefore().equals(q.factsBefore())
                ||!f.providerGeneration().equals(q.providerGeneration())||!f.querySequence().equals(q.querySequence())
                ||f.owner().filter(o->o.connectionGeneration().equals(connection)).isEmpty()||!s.caseBound()||s.fixedInstanceId().filter(n->n==instance).isEmpty()
                ||(action==CurrentCccEvent.Action.SELECT_TIER_FOUR?!s.selectDAdmissible():action!=CurrentCccEvent.Action.SELECT_TEMPORARY_CANCEL||!s.selectFAdmissible()))
            throw new IOException("CCC selection lost this original Source/Core/lease/fixed instance or actual dispatch");
    }
    static CurrentCccDecisionSource requireCurrentCccDecisionQuery(CurrentCccDecisionResult f,CoreFrame.Prefix core,java.math.BigInteger connection)throws IOException {
        if(f.action()!=CurrentCccDecision.Action.QUERY||f.status()!=CurrentCccDecisionResult.Status.AVAILABLE||!f.cleanupKnown()||f.effectAttempted()||f.nativeReturned()||f.nativeHandled()
                ||f.claimSequence().signum()!=0||f.decisionKey().isPresent()||f.source().isEmpty()||f.providerGeneration().signum()<=0||f.querySequence().signum()<=0
                ||f.factsBefore().filter(core::equals).isEmpty()||f.owner().filter(o->o.connectionGeneration().equals(connection)).isEmpty())
            throw new IOException("CCC readonly decision ACK differs from original Core/connection/complete Source");
        return f.source().orElseThrow(); // falseCan, empty/NUL tooltip and null expiry remain actual DATA.
    }
    static void requireCurrentCccDecisionDispatch(CurrentCccDecisionResult f,CurrentCccDecisionResult q,CoreFrame.Prefix core,
            java.math.BigInteger connection,CurrentCccDecision.Action action)throws IOException {
        requireCurrentCccDecisionQuery(q,core,connection);
        var status=switch(action){case OPEN_LIST->CurrentCccDecisionResult.Status.NAVIGATION_DISPATCHED;case OPEN_DETAIL->CurrentCccDecisionResult.Status.SELECTION_DISPATCHED;
            case CONFIRM->CurrentCccDecisionResult.Status.CONFIRMATION_DISPATCHED;default->throw new IOException("No query-as-effect CCC action");};
        if(f.action()!=action||f.status()!=status||!f.effectAttempted()||!f.nativeReturned()||!f.cleanupKnown()||f.claimSequence().signum()<=0
                ||action!=CurrentCccDecision.Action.OPEN_LIST&&f.nativeHandled()||!f.source().equals(q.source())||!f.factsBefore().equals(q.factsBefore())
                ||!f.providerGeneration().equals(q.providerGeneration())||!f.querySequence().equals(q.querySequence())
                ||f.owner().filter(o->o.connectionGeneration().equals(connection)).isEmpty()
                ||(action==CurrentCccDecision.Action.OPEN_LIST?f.decisionKey().isPresent():!f.decisionKey().equals(Optional.of(CurrentCccDecision.DecisionKey.CORRUPTION_POLICY))))
            throw new IOException("CCC decision lost original Source/Core/lease/known dispatch; Toggle false is legitimate DATA");
    }
    static boolean currentCccInstanceAbsent(CurrentCccEventSource source,int instance)throws IOException {
        if(!source.sampledTwice()||!source.eventCensus().censusComplete()||source.eventCensus().namedRootCount()!=source.eventCensus().events().size())
            throw new IOException("Complete fresh census required to observe original instance absence");
        return source.eventCensus().events().stream().noneMatch(e->e.instanceId()==instance);
    }
    private static Instant currentCccUntil(NativeGameTransport.CoreReceived before,Instant parent){return before.validUntil().isBefore(parent)?before.validUntil():parent;}
    private static void requireCurrentCccAfterRequest(NativeGameTransport transport,NativeGameTransport.CoreReceived after,String requestId)throws IOException {
        var prior=transport.originalRequestChronology(requestId).orElseThrow(()->new IOException("Actual prior CCC request chronology missing"));
        if(after.original().custody().orElseThrow().writeEntered().order().compareTo(prior.responseReceived().order())<=0)
            throw new IOException("Independent fresh CCC Core must be written after the actual prior ACK");
    }
    private static NativeGameTransport.CccEventReceived readCurrentCccEvent(NativeGameTransport transport,GameSupervisorControl.Descriptor owner,NativeGameTransport.CoreReceived before,
            NativeObservationPort.TransportSession session,Path output,String label,Instant parent,ObjectNode result,ObjectNode originals)throws IOException,InterruptedException {
        Instant until=currentCccUntil(before,parent);stage="ONE_READONLY_CCC_EVENT";result.put("read_calls",result.path("read_calls").intValue()+1);
        var read=transport.readCurrentCccEvent(before,until);Path out=Files.createDirectory(output.resolve(label));archiveCurrentLetterOutcome(transport,out,label,read.original(),originals);
        if(!(read instanceof NativeGameTransport.CccEventReceived query))throw new IOException("Actual CCC event unavailable/UNKNOWN; original retained, no retry");
        query.requireOriginal(transport,query.validUntil());var ack=query.original();requireCurrentDjcAckOwner(transport,owner,ack,session);var frame=CurrentCccEventResult.decodeOutcome(ack);
        if(!frame.equals(query.frame())||query.validUntil().isAfter(until))throw new IOException("CCC private event query differs from THIS ACK/deadline");
        requireCurrentCccEventQuery(frame,((CoreFrame.Partial)before.frame()).prefix(),session.connectionGeneration());
        originals.set(label+"_original_result",write(out,"original-result.json",ack.originalResultToken().orElseThrow().bytes()));result.set(label,FullJsonTree.parse(frame.encode().bytes(),FullJsonTree.MAXIMUM_BYTES));return query;
    }
    private static NativeGameTransport.CccDecisionReceived readCurrentCccDecision(NativeGameTransport transport,GameSupervisorControl.Descriptor owner,NativeGameTransport.CoreReceived before,
            NativeObservationPort.TransportSession session,Path output,String label,Instant parent,ObjectNode result,ObjectNode originals)throws IOException,InterruptedException {
        Instant until=currentCccUntil(before,parent);stage="ONE_READONLY_CCC_DECISION";result.put("read_calls",result.path("read_calls").intValue()+1);
        var read=transport.readCurrentCccDecision(before,until);Path out=Files.createDirectory(output.resolve(label));archiveCurrentLetterOutcome(transport,out,label,read.original(),originals);
        if(!(read instanceof NativeGameTransport.CccDecisionReceived query))throw new IOException("Actual CCC decision unavailable/UNKNOWN; no empty Source or retry");
        query.requireOriginal(transport,query.validUntil());var ack=query.original();requireCurrentDjcAckOwner(transport,owner,ack,session);var frame=CurrentCccDecisionResult.decodeOutcome(ack);
        if(!frame.equals(query.frame())||query.validUntil().isAfter(until))throw new IOException("CCC private decision query differs from THIS ACK/deadline");
        requireCurrentCccDecisionQuery(frame,((CoreFrame.Partial)before.frame()).prefix(),session.connectionGeneration());
        originals.set(label+"_original_result",write(out,"original-result.json",ack.originalResultToken().orElseThrow().bytes()));result.set(label,FullJsonTree.parse(frame.encode().bytes(),FullJsonTree.MAXIMUM_BYTES));return query;
    }
    private static CurrentCccEventResult submitCurrentCccEvent(NativeGameTransport transport,GameSupervisorControl.Descriptor owner,NativeGameTransport.CccEventReceived query,
            NativeGameTransport.CccEventPrepared prepared,NativeObservationPort.TransportSession session,Path output,String label,ObjectNode result,ObjectNode originals)throws IOException,InterruptedException {
        if(!prepared.deadline().equals(query.validUntil()))throw new IOException("Original CCC event deadline changed before intent");
        archiveCurrentCccIntent(output,label+"-intent",prepared.requestId(),"",prepared.deadline(),prepared.originalPacket().value(),originals);
        stage="ONCE_FIXED_CCC_EVENT";result.put("event_select_calls",result.path("event_select_calls").intValue()+1);
        var outcome=transport.submitCurrentCccEvent(prepared);Path out=Files.createDirectory(output.resolve(label+"-result"));archiveCurrentLetterOutcome(transport,out,label,outcome,originals);
        if(!(outcome instanceof NativeActionPort.AckReceived ack))throw new IOException("Original CCC event effect refused/UNKNOWN; no resubmission");
        requireCurrentDjcAckOwner(transport,owner,ack,session);var frame=CurrentCccEventResult.decodeOutcome(ack);
        originals.set(label+"_original_result",write(out,"original-result.json",ack.originalResultToken().orElseThrow().bytes()));result.set(label,FullJsonTree.parse(frame.encode().bytes(),FullJsonTree.MAXIMUM_BYTES));
        if(!ack.requestId().equals(prepared.requestId())||prepared.latestFrame().filter(frame::equals).isEmpty())throw new IOException("CCC THIS event ACK differs from prepared latest receipt");
        requireCurrentCccEventDispatch(frame,query.frame(),query.frame().factsBefore().orElseThrow(),session.connectionGeneration(),prepared.action(),prepared.instanceId());return frame;
    }
    private static CurrentCccDecisionResult submitCurrentCccDecision(NativeGameTransport transport,GameSupervisorControl.Descriptor owner,NativeGameTransport.CccDecisionReceived query,
            NativeGameTransport.CccDecisionPrepared prepared,NativeObservationPort.TransportSession session,Path output,String label,ObjectNode result,ObjectNode originals)throws IOException,InterruptedException {
        if(!prepared.deadline().equals(query.validUntil()))throw new IOException("Original CCC decision deadline changed before intent");
        archiveCurrentCccIntent(output,label+"-intent",prepared.requestId(),"",prepared.deadline(),prepared.originalPacket().value(),originals);
        stage="ONCE_FIXED_CCC_DECISION";result.put("decision_action_calls",result.path("decision_action_calls").intValue()+1);
        var outcome=transport.submitCurrentCccDecision(prepared);Path out=Files.createDirectory(output.resolve(label+"-result"));archiveCurrentLetterOutcome(transport,out,label,outcome,originals);
        if(!(outcome instanceof NativeActionPort.AckReceived ack))throw new IOException("Original CCC decision effect refused/UNKNOWN; no resubmission");
        requireCurrentDjcAckOwner(transport,owner,ack,session);var frame=CurrentCccDecisionResult.decodeOutcome(ack);
        originals.set(label+"_original_result",write(out,"original-result.json",ack.originalResultToken().orElseThrow().bytes()));result.set(label,FullJsonTree.parse(frame.encode().bytes(),FullJsonTree.MAXIMUM_BYTES));
        if(!ack.requestId().equals(prepared.requestId())||prepared.latestFrame().filter(frame::equals).isEmpty())throw new IOException("CCC THIS decision ACK differs from prepared latest receipt");
        requireCurrentCccDecisionDispatch(frame,query.frame(),query.frame().factsBefore().orElseThrow(),session.connectionGeneration(),prepared.action());return frame;
    }
    private static void initializeCurrentCccResult(ObjectNode result,CccConfig config,String machine){
        result.put("schema","xar.native-owner-current-ccc-original-case/v1").put("mode",switch(config.mode()){case QUERY_ROLE->"current_ccc_query_role";case QUERY_EVENT->"current_ccc_query_event";case QUERY_DECISION->"current_ccc_query_decision";case ORIGINAL_CASE_ONCE->"current_ccc_original_case_once";})
                .put("machine_id",machine).put("read_calls",0).put("advance_calls",0).put("status_queries",0).put("epoch_confirm_calls",0).put("event_select_calls",0).put("decision_action_calls",0)
                .put("maximum_natural_days",13).put("natural_days_observed",0).put("original_case_channel_completed",false).put("epoch_confirmed",false)
                .put("event_closed",false).put("decision_applied",false).put("cooldown_readback_complete",false).putNull("cooldown_expiry_date_raw")
                .put("post_cancel_decision_readback_complete",false).put("post_cancel_navigation_calls",0).putNull("final_confirm_tooltip")
                .put("physical_save_confirmed",false).put("save_calls",0);
    }
    private static void runCurrentCcc(NativeGameTransport transport,GameSupervisorControl.Descriptor owner,NativeLaunchPlan plan,CccConfig config,Path output,
            Instant deadline,Duration readTimeout,ObjectNode result,ObjectNode originals)throws IOException,InterruptedException {
        try {
            if(!(plan.load() instanceof NativeLaunchPlan.SavedGame))throw new IOException("CCC requires its actual SavedGame owner");
            var before=readCurrentCccCore(transport,owner,plan,output,"ccc-core-before",deadline,result,originals,null,null);var start=((CoreFrame.Partial)before.frame()).prefix();
            var session=before.original().custody().orElseThrow().session();result.set("session",session(session));
            if(config.mode()==CccMode.QUERY_EVENT){readCurrentCccEvent(transport,owner,before,session,output,"ccc-event-query",deadline,result,originals);result.put("query_available",true);return;}
            if(config.mode()==CccMode.QUERY_DECISION){readCurrentCccDecision(transport,owner,before,session,output,"ccc-decision-query",deadline,result,originals);result.put("query_available",true);return;}
            var role=readCurrentCccRole(transport,owner,before,session,output,"ccc-role-before",deadline,result,originals);result.put("query_available",true);
            if(config.queryOnly())return;
            requireCurrentCccPositiveRole(role.frame(),start,CurrentCccActorTransitionSource.Role.SONG,java.math.BigInteger.ZERO,start.playedCharacterId(),-1,false,0,start.dateRaw());
            var day1=transport.prepareCurrentCccAdvance(role);var pending=runCurrentCccDay(transport,owner,role,day1,config,session,output,"ccc-day01",deadline,readTimeout,result,originals,true);
            var p=pending.progress().orElseThrow();int official=p.afterActorId();var current=currentCccAfter(start,day1.targetDateRaw(),official);
            var after=readCurrentCccCore(transport,owner,plan,output,"ccc-core-after-pending",day1.deadline(),result,originals,session,current);requireCurrentCccAfterRequest(transport,after,pending.requestId());
            var recipient=readCurrentCccRole(transport,owner,after,session,output,"ccc-official-before-epoch",day1.deadline(),result,originals);
            var source=requireCurrentCccPositiveRole(recipient.frame(),current,CurrentCccActorTransitionSource.Role.OFFICIAL,java.math.BigInteger.ZERO,start.playedCharacterId(),official,true,1,start.dateRaw());
            var actual=source.pending().orElseThrow(()->new IOException("Independent CCC Official Source lacks actual pending proof"));
            if(!actual.operationId().equals(day1.operationId())||!actual.claimSequence().equals(pending.claimSequence())||!actual.generation().equals(p.generation())
                    ||!actual.originalDeadlineUnixMs().equals(java.math.BigInteger.valueOf(day1.deadline().toEpochMilli()))||actual.beforeActorId()!=start.playedCharacterId()||actual.afterActorId()!=official
                    ||actual.startingDateRaw()!=start.dateRaw()||actual.targetDateRaw()!=day1.targetDateRaw())throw new IOException("Independent CCC pending proof differs from original D1 lease/claim/generation/actors");
            var epoch=transport.prepareCurrentCccEpoch(day1,recipient);
            if(!epoch.operationId().equals(day1.operationId())||!epoch.deadline().equals(recipient.validUntil())||epoch.deadline().isAfter(day1.deadline()))throw new IOException("CCC once epoch must preserve original operation and unextended deadline");
            archiveCurrentCccIntent(output,"ccc-confirm-epoch-intent",epoch.requestId(),epoch.operationId(),epoch.deadline(),epoch.originalPacket().value(),originals);
            stage="ONCE_PROVED_CCC_EPOCH_CONFIRMATION";result.put("epoch_confirm_calls",1);var epochOutcome=transport.submitCurrentCccEpoch(epoch);
            Path epochOut=Files.createDirectory(output.resolve("ccc-confirm-epoch-result"));archiveCurrentLetterOutcome(transport,epochOut,"ccc_epoch",epochOutcome,originals);
            if(!(epochOutcome instanceof NativeActionPort.AckReceived ack))throw new IOException("CCC original epoch refused/UNKNOWN; no re-confirmation");
            requireCurrentDjcAckOwner(transport,owner,ack,session);var confirmed=CurrentCccActorTransitionResult.decodeOutcome(ack);
            originals.set("ccc_epoch_original_result",write(epochOut,"original-result.json",ack.originalResultToken().orElseThrow().bytes()));result.set("epoch_confirmation",FullJsonTree.parse(confirmed.encode().bytes(),SMALL));
            if(!ack.requestId().equals(epoch.requestId())||epoch.latestFrame().filter(confirmed::equals).isEmpty()||confirmed.status()!=CurrentCccActorTransitionResult.Status.EPOCH_CONFIRMED||confirmed.action()!=CurrentCccActorTransition.Action.CONFIRM_EPOCH
                    ||!confirmed.operationId().equals(day1.operationId())||!confirmed.accepted()||confirmed.claimSequence().signum()<=0||!confirmed.actorEpoch().equals(java.math.BigInteger.ONE)||confirmed.completedNaturalDays()!=1
                    ||confirmed.effectAttempted()||confirmed.nativeReturned()||!confirmed.cleanupKnown()||!confirmed.source().equals(recipient.frame().source())||!confirmed.factsBefore().equals(recipient.frame().factsBefore())
                    ||!confirmed.providerGeneration().equals(recipient.frame().providerGeneration())||!confirmed.querySequence().equals(recipient.frame().querySequence())||!confirmed.deadlineUnixMs().equals(java.math.BigInteger.valueOf(epoch.deadline().toEpochMilli()))
                    ||!confirmed.connectionGeneration().equals(session.connectionGeneration()))throw new IOException("CCC epoch1 ACK lost actual original proof, count1 or zero-Game-call frontier");
            result.put("epoch_confirmed",true).put("natural_days_observed",1);
            var before2=readCurrentCccCore(transport,owner,plan,output,"ccc-core-before-day02",deadline,result,originals,session,current);requireCurrentCccAfterRequest(transport,before2,epoch.requestId());
            var role2=readCurrentCccRole(transport,owner,before2,session,output,"ccc-role-before-day02",deadline,result,originals);
            requireCurrentCccPositiveRole(role2.frame(),current,CurrentCccActorTransitionSource.Role.OFFICIAL,java.math.BigInteger.ONE,start.playedCharacterId(),official,false,1,start.dateRaw());
            var day2=transport.prepareCurrentCccAdvance(role2);if(day2.operationId().equals(day1.operationId())||day2.requestId().equals(day1.requestId()))throw new IOException("CCC D2 requires its own new private operation");
            var completed2=runCurrentCccDay(transport,owner,role2,day2,config,session,output,"ccc-day02",deadline,readTimeout,result,originals,false);current=currentCccAfter(current,day2.targetDateRaw(),official);
            var after2=readCurrentCccCore(transport,owner,plan,output,"ccc-core-after-day02",deadline,result,originals,session,current);requireCurrentCccAfterRequest(transport,after2,completed2.requestId());result.put("natural_days_observed",2);
            var event=readCurrentCccEvent(transport,owner,after2,session,output,"ccc-tier-four-query",deadline,result,originals);
            var tierFour=transport.prepareCurrentCccTierFour(event);submitCurrentCccEvent(transport,owner,event,tierFour,session,output,"ccc-tier-four-once",result,originals);
            int originalInstance=tierFour.instanceId();NativeGameTransport.CccDecisionReceived decision=null;
            for(int day=3;day<=13;day++) {
                var core=readCurrentCccCore(transport,owner,plan,output,"ccc-core-before-day"+String.format(java.util.Locale.ROOT,"%02d",day),deadline,result,originals,session,current);
                if(day==3)requireCurrentCccAfterRequest(transport,core,tierFour.requestId());
                var dailyRole=readCurrentCccRole(transport,owner,core,session,output,"ccc-role-before-day"+String.format(java.util.Locale.ROOT,"%02d",day),deadline,result,originals);
                requireCurrentCccPositiveRole(dailyRole.frame(),current,CurrentCccActorTransitionSource.Role.OFFICIAL,java.math.BigInteger.ONE,start.playedCharacterId(),official,false,day-1,start.dateRaw());
                var next=transport.prepareCurrentCccAdvance(dailyRole);var done=runCurrentCccDay(transport,owner,dailyRole,next,config,session,output,"ccc-day"+String.format(java.util.Locale.ROOT,"%02d",day),deadline,readTimeout,result,originals,false);
                current=currentCccAfter(current,next.targetDateRaw(),official);var observed=readCurrentCccCore(transport,owner,plan,output,"ccc-core-after-day"+String.format(java.util.Locale.ROOT,"%02d",day),deadline,result,originals,session,current);
                requireCurrentCccAfterRequest(transport,observed,done.requestId());result.put("natural_days_observed",day);
                decision=readCurrentCccDecision(transport,owner,observed,session,output,"ccc-half-predicate-day"+String.format(java.util.Locale.ROOT,"%02d",day),deadline,result,originals);
                var ds=decision.frame().source().orElseThrow();if(ds.caseBound()&&ds.fixtureTaxVariablePresent().orElse(false)&&ds.fixtureTaxExactHalf().orElse(false)){result.put("actual_half_predicate_observed",true);break;}
                decision=null;
            }
            if(decision==null)throw new IOException("Actual original half predicate was not observed within native13 days; no forced variable or extra day");
            var ds=decision.frame().source().orElseThrow();
            if(!ds.listVisible()){
                var opened=transport.prepareCurrentCccDecision(decision,CurrentCccDecision.Action.OPEN_LIST);submitCurrentCccDecision(transport,owner,decision,opened,session,output,"ccc-open-list-once",result,originals);
                var core=readCurrentCccCore(transport,owner,plan,output,"ccc-core-after-open-list",deadline,result,originals,session,current);requireCurrentCccAfterRequest(transport,core,opened.requestId());
                decision=readCurrentCccDecision(transport,owner,core,session,output,"ccc-list-readback",deadline,result,originals);ds=decision.frame().source().orElseThrow();
            }
            if(!ds.detailVisible()||!ds.selectedDecisionKey().equals(Optional.of(CurrentCccDecision.DecisionKey.CORRUPTION_POLICY))){
                var detailed=transport.prepareCurrentCccDecision(decision,CurrentCccDecision.Action.OPEN_DETAIL);submitCurrentCccDecision(transport,owner,decision,detailed,session,output,"ccc-open-detail-once",result,originals);
                var core=readCurrentCccCore(transport,owner,plan,output,"ccc-core-after-open-detail",deadline,result,originals,session,current);requireCurrentCccAfterRequest(transport,core,detailed.requestId());
                decision=readCurrentCccDecision(transport,owner,core,session,output,"ccc-detail-readback",deadline,result,originals);ds=decision.frame().source().orElseThrow();
            }
            result.put("actual_native_can_confirm",ds.nativeCanConfirm().orElse(false)).put("actual_confirm_tooltip_observed",ds.confirmTooltipObserved());
            if(!ds.caseBound()||!ds.fixtureTaxVariablePresent().orElse(false)||!ds.fixtureTaxExactHalf().orElse(false)||!ds.nativeCanConfirm().orElse(false)||!ds.confirmAdmissible())
                throw new IOException("Actual fixed CCC NativeCan/half predicate refused; real Source/why retained as DATA, no confirm or retry");
            var confirmation=transport.prepareCurrentCccDecision(decision,CurrentCccDecision.Action.CONFIRM);submitCurrentCccDecision(transport,owner,decision,confirmation,session,output,"ccc-confirm-once",result,originals);
            var core=readCurrentCccCore(transport,owner,plan,output,"ccc-core-after-confirm",deadline,result,originals,session,current);requireCurrentCccAfterRequest(transport,core,confirmation.requestId());
            var temporary=readCurrentCccEvent(transport,owner,core,session,output,"ccc-temporary-cancel-query",deadline,result,originals);var cancel=transport.prepareCurrentCccTemporaryCancel(temporary);
            if(cancel.instanceId()==originalInstance)throw new IOException("Temporary cancel needs its actual new instance, never the original tier-four instance");
            submitCurrentCccEvent(transport,owner,temporary,cancel,session,output,"ccc-temporary-cancel-once",result,originals);
            var finalCore=readCurrentCccCore(transport,owner,plan,output,"ccc-core-after-cancel",deadline,result,originals,session,current);requireCurrentCccAfterRequest(transport,finalCore,cancel.requestId());
            var finalEvent=readCurrentCccEvent(transport,owner,finalCore,session,output,"ccc-independent-cancel-census",deadline,result,originals);
            boolean absent=currentCccInstanceAbsent(finalEvent.frame().source().orElseThrow(),cancel.instanceId());result.put("cancel_instance_absent_observed",absent);
            var finalDecisionCore=readCurrentCccCore(transport,owner,plan,output,"ccc-core-before-final-decision-read",deadline,result,originals,session,current);requireCurrentCccAfterRequest(transport,finalDecisionCore,cancel.requestId());
            var finalDecision=readCurrentCccDecision(transport,owner,finalDecisionCore,session,output,"ccc-independent-traits-and-tooltip",deadline,result,originals);var fs=finalDecision.frame().source().orElseThrow();
            boolean traitsAbsent=fs.corruptionTraits().filter(v->v.size()==4&&v.stream().noneMatch(Boolean::booleanValue)).isPresent();
            result.put("cancel_before_navigation_detail_visible",fs.detailVisible()).put("post_cancel_navigation_calls",0)
                    .put("four_corruption_traits_absent_observed",traitsAbsent).put("original_case_channel_completed",absent&&traitsAbsent)
                    .put("final_date_raw",current.dateRaw()).put("official_actor_id",official).put("independent_after_core_verified",true);
            if(!absent||!traitsAbsent)throw new IOException("Actual complete post-cancel census/traits do not match original case; no post-cancel navigation");
            if(!fs.listVisible()){
                var reopened=transport.prepareCurrentCccDecision(finalDecision,CurrentCccDecision.Action.OPEN_LIST);
                submitCurrentCccDecision(transport,owner,finalDecision,reopened,session,output,"ccc-post-cancel-open-list-once",result,originals);
                result.put("post_cancel_navigation_calls",result.path("post_cancel_navigation_calls").intValue()+1);
                var observed=readCurrentCccCore(transport,owner,plan,output,"ccc-core-after-post-cancel-open-list",deadline,result,originals,session,current);requireCurrentCccAfterRequest(transport,observed,reopened.requestId());
                finalDecision=readCurrentCccDecision(transport,owner,observed,session,output,"ccc-post-cancel-list-readback",deadline,result,originals);fs=finalDecision.frame().source().orElseThrow();
            }
            if(!fs.detailVisible()||!fs.selectedDecisionKey().equals(Optional.of(CurrentCccDecision.DecisionKey.CORRUPTION_POLICY))){
                var reopened=transport.prepareCurrentCccDecision(finalDecision,CurrentCccDecision.Action.OPEN_DETAIL);
                submitCurrentCccDecision(transport,owner,finalDecision,reopened,session,output,"ccc-post-cancel-open-detail-once",result,originals);
                result.put("post_cancel_navigation_calls",result.path("post_cancel_navigation_calls").intValue()+1);
                var observed=readCurrentCccCore(transport,owner,plan,output,"ccc-core-after-post-cancel-open-detail",deadline,result,originals,session,current);requireCurrentCccAfterRequest(transport,observed,reopened.requestId());
                finalDecision=readCurrentCccDecision(transport,owner,observed,session,output,"ccc-post-cancel-detail-readback",deadline,result,originals);fs=finalDecision.frame().source().orElseThrow();
            }
            requireCurrentCccPostCancelDetail(fs);
            result.put("four_corruption_traits_absent_observed",traitsAbsent).put("final_tooltip_observed",fs.confirmTooltipObserved()).put("final_native_can_observed",fs.nativeCanConfirm().isPresent())
                    .put("post_cancel_decision_readback_complete",true).put("final_confirm_tooltip",fs.confirmTooltip().orElseThrow());
            if(fs.nativeCanConfirm().isPresent())result.put("final_native_can_confirm",fs.nativeCanConfirm().orElseThrow());
            result.put("final_date_raw",current.dateRaw()).put("official_actor_id",official).put("independent_after_core_verified",true)
                    .put("original_case_channel_completed",absent&&traitsAbsent).put("cooldown_readback_complete",false).putNull("cooldown_expiry_date_raw");
            if(!absent||!traitsAbsent)throw new IOException("Actual complete post-cancel census/traits do not match original case; dispatch alone is not business completion");
        } finally {
            archiveNaturalDiagnostics(output,originals,transport.diagnostics());var progress=result.deepCopy();progress.set("originals",originals.deepCopy());
            write(output,"current-ccc-original-case-progress.json",FullJsonTree.encode(progress,FullJsonTree.MAXIMUM_BYTES));
        }
    }

    static void requireCurrentCccPostCancelDetail(CurrentCccDecisionSource source)throws IOException {
        if(!source.caseBound()||!source.detailVisible()||!source.selectedDecisionKey().equals(Optional.of(CurrentCccDecision.DecisionKey.CORRUPTION_POLICY))
                ||!source.confirmTooltipObserved()||source.confirmTooltip().isEmpty()||source.nativeCanConfirm().isEmpty()
                ||source.corruptionTraits().filter(values->values.size()==4&&values.stream().noneMatch(Boolean::booleanValue)).isEmpty())
            throw new IOException("Actual fixed post-cancel detail/full tooltip/nullable NativeCan and four cleared traits required");
        // Both false Can and an observed empty tooltip are DATA. Typed expiry remains unqualified/null.
    }

    record StockBookmark1070Config(boolean chooseC){int submissions(){return chooseC?5:2;}}
    static StockBookmark1070Config currentStockBookmark1070Config(ObjectNode config) {
        StrictJson.require("xar.native-owner-snapshot-config/v44".equals(StrictJson.text(config.get("schema"))),"Explicit v44 fixed stock bookmark family required");
        String mode=StrictJson.text(config.get("mode"));
        boolean choose=switch(mode){case "current_stock_bookmark1070_query"->false;case "current_stock_bookmark1070_choose_c"->true;default->throw new IllegalArgumentException("Only two fixed stock bookmark1070 modes");};
        StrictJson.object(config,Set.of("schema","mode","owner_descriptor","overall_timeout_seconds","read_timeout_seconds","maximum_frames_per_operation"));
        ExactRef.fromJson(config.get("owner_descriptor"));StrictJson.integer(config.get("overall_timeout_seconds"),1,600);
        StrictJson.integer(config.get("read_timeout_seconds"),1,60);StrictJson.integer(config.get("maximum_frames_per_operation"),1,65536);
        return new StockBookmark1070Config(choose);
    }
    static CoreFrame.Prefix requireCurrentStockBookmark1070Core(CoreFrame frame)throws IOException {
        return requireCurrentRiteCreateCore(frame); // Same current paused/living Core facts, no Rite/Create permission reused.
    }
    static CurrentStockBookmark1070Source requireCurrentStockBookmark1070QueryFrame(CurrentStockBookmark1070Result frame,
            CoreFrame.Prefix core,java.math.BigInteger connection)throws IOException {
        if(frame.action()!=CurrentStockBookmark1070.Action.QUERY||frame.status()!=CurrentStockBookmark1070Result.Status.AVAILABLE
                ||!frame.cleanupKnown()||frame.effectAttempted()||frame.nativeReturned()||frame.nativeHandled()||frame.claimSequence().signum()!=0
                ||frame.instanceId().isPresent()||frame.providerGeneration().signum()<=0||frame.querySequence().signum()<=0||frame.source().isEmpty()
                ||frame.factsBefore().filter(core::equals).isEmpty()||frame.owner().isEmpty()
                ||!frame.owner().orElseThrow().connectionGeneration().equals(connection))
            throw new IOException("Actual readonly stock bookmark ACK differs from complete original Core/connection/query");
        var source=frame.source().orElseThrow();var census=source.eventCensus();
        if(!source.sampledTwice()||!census.censusComplete()||census.namedRootCount()!=census.events().size())
            throw new IOException("Actual complete stock event census required; no guessed empty");
        if(source.fixedInstanceId().isPresent()) {
            int id=source.fixedInstanceId().orElseThrow();
            if(census.events().stream().filter(e->e.instanceId()==id&&e.recipientCharacterId()==core.playedCharacterId()).count()!=1)
                throw new IOException("Fixed event instance crossed actual Core recipient");
        }
        return source; // Absence/foreign definitions/Canfalse/multiple roots are actual query DATA.
    }
    static int requireCurrentStockBookmark1070C(CurrentStockBookmark1070Source source,CoreFrame.Prefix core)throws IOException {
        var census=source.eventCensus();
        if(!source.sampledTwice()||!source.selectCAdmissible()||source.fixedInstanceId().isEmpty()||!census.censusComplete()
                ||census.namedRootCount()!=1||census.events().size()!=1)throw new IOException("Actual complete single event does not admit fixed.c");
        int id=source.fixedInstanceId().orElseThrow();var event=census.events().get(0);
        if(id<=0||event.instanceId()!=id||event.recipientCharacterId()!=core.playedCharacterId()||!event.definitionKey().equals("bookmark.1070")
                ||!event.namedRootBound()||!event.windowVisible()||!event.windowEnabled()||event.authoredOptionCount()!=3||event.options().size()!=3)
            throw new IOException("Original fixed stock definition/recipient/instance/complete3 options required");
        for(int index=0;index<3;index++){final int actual=index;if(event.options().stream().filter(o->o.authoredOptionIndex()==actual).count()!=1)
            throw new IOException("Each real authored option index must be unique and complete");}
        var chosen=event.options().stream().filter(o->o.authoredOptionIndex()==2).findFirst().orElseThrow();
        if(!chosen.nativeCanSelect()||chosen.text().isEmpty())throw new IOException("Actual original authored.c option does not admit selection");
        return id; // Fixed script semantic; no runtime array ordinal or configured selector.
    }
    static void requireCurrentStockBookmark1070DispatchFrame(CurrentStockBookmark1070Result frame,CurrentStockBookmark1070Result query,int instance)throws IOException {
        if(query.action()!=CurrentStockBookmark1070.Action.QUERY||query.status()!=CurrentStockBookmark1070Result.Status.AVAILABLE
                ||frame.action()!=CurrentStockBookmark1070.Action.SELECT_C||frame.status()!=CurrentStockBookmark1070Result.Status.SELECTION_DISPATCHED
                ||!frame.cleanupKnown()||!frame.effectAttempted()||!frame.nativeReturned()||frame.nativeHandled()||frame.claimSequence().signum()<=0
                ||!frame.instanceId().equals(java.util.Optional.of(instance))||!frame.source().equals(query.source())||!frame.factsBefore().equals(query.factsBefore())
                ||!frame.providerGeneration().equals(query.providerGeneration())||!frame.querySequence().equals(query.querySequence())
                ||frame.owner().isEmpty()||query.owner().isEmpty()
                ||!frame.owner().orElseThrow().connectionGeneration().equals(query.owner().orElseThrow().connectionGeneration()))
            throw new IOException("This stock.c ACK differs from original immutable beforeSource/Core/lease/instance/claim");
    }
    static boolean currentStockBookmark1070InstanceAbsent(CurrentStockBookmark1070Source actual,int originalInstance)throws IOException {
        if(originalInstance<=0||!actual.sampledTwice()||!actual.eventCensus().censusComplete()
                ||actual.eventCensus().namedRootCount()!=actual.eventCensus().events().size())throw new IOException("Complete independent after census required");
        return actual.eventCensus().events().stream().noneMatch(e->e.instanceId()==originalInstance);
    }
    static void initializeCurrentStockBookmark1070Result(ObjectNode result,StockBookmark1070Config config,String machineId) {
        result.put("schema","xar.native-owner-current-stock-bookmark1070/v1").put("mode",config.chooseC()?"current_stock_bookmark1070_choose_c":"current_stock_bookmark1070_query")
                .put("machine_id",machineId).put("steam_build_id","26785313").put("read_calls",0).put("query_calls",0).put("choice_calls",0)
                .put("query_available",false).put("choice_callback_dispatched",false).put("native_returned",false).put("native_handled",false)
                .putNull("original_instance_id").put("independent_after_census_observed",false).putNull("original_instance_absent")
                .put("original_instance_observation","NOT_OBSERVED").put("event_closed",false).put("date_gate_cleared",false)
                .put("new_date_observed",false).put("physical_save_confirmed",false).put("date_calls",0).put("save_calls",0);
    }
    private static NativeGameTransport.StockBookmark1070Received readCurrentStockBookmark1070Query(NativeGameTransport transport,
            GameSupervisorControl.Descriptor owner,NativeGameTransport.CoreReceived core,NativeObservationPort.TransportSession actualSession,
            Path output,String name,Instant deadline,ObjectNode result,ObjectNode originals)throws IOException,InterruptedException {
        Instant until=core.validUntil().isBefore(deadline)?core.validUntil():deadline;core.requireOriginal(transport,until);
        var read=transport.readCurrentStockBookmark1070(core,until);Path queryOutput=Files.createDirectory(output.resolve(name));
        archiveCurrentLetterOutcome(transport,queryOutput,name,read.original(),originals);
        result.put("query_calls",result.path("query_calls").intValue()+1).put("read_calls",result.path("read_calls").intValue()+1);
        if(!(read instanceof NativeGameTransport.StockBookmark1070Received query))throw new IOException("Actual stock query unavailable or UNKNOWN; no cached source/retry");
        until=query.validUntil().isBefore(until)?query.validUntil():until;query.requireOriginal(transport,until);
        requireCurrentDjcAckOwner(transport,owner,query.original(),actualSession);var frame=CurrentStockBookmark1070Result.decodeOutcome(query.original());
        if(!frame.equals(query.frame()))throw new IOException("Actual stock ACK differs from private immutable query frame");
        requireCurrentStockBookmark1070QueryFrame(frame,requireCurrentStockBookmark1070Core(core.frame()),actualSession.connectionGeneration());
        originals.set(name+"_original_result",write(queryOutput,"original-result.json",query.original().originalResultToken().orElseThrow().bytes()));
        result.set(name,FullJsonTree.parse(frame.encode().bytes(),FullJsonTree.MAXIMUM_BYTES));return query;
    }
    private static void runCurrentStockBookmark1070(NativeGameTransport transport,GameSupervisorControl.Descriptor owner,NativeLaunchPlan plan,
            StockBookmark1070Config config,Path output,Instant deadline,ObjectNode result,ObjectNode originals)throws IOException,InterruptedException {
        try {
            if(!(plan.load() instanceof NativeLaunchPlan.SavedGame))throw new IOException("Fixed stock bookmark requires actual SavedGame owner");
            stage="STOCK_BOOKMARK1070_FRESH_ACTUAL_CORE";
            var before=readCurrentRiteCreateCore(transport,owner,plan,null,output,"core-before-stock-bookmark1070",deadline,result,originals);
            var prefix=requireCurrentStockBookmark1070Core(before.frame());var actualSession=before.original().custody().orElseThrow().session();
            result.set("session",session(actualSession));stage="STOCK_BOOKMARK1070_ACTUAL_PRIVATE_QUERY";
            var query=readCurrentStockBookmark1070Query(transport,owner,before,actualSession,output,"stock-bookmark1070-query",deadline,result,originals);
            result.put("query_available",true);if(!config.chooseC())return;
            int instance=requireCurrentStockBookmark1070C(query.frame().source().orElseThrow(),prefix);result.put("original_instance_id",instance);
            stage="STOCK_BOOKMARK1070_PREPARE_ONE_FIXED_C";
            var prepared=transport.prepareCurrentStockBookmark1070C(query);
            if(prepared.instanceId()!=instance||!prepared.deadline().equals(query.validUntil()))throw new IOException("Actual private fixed.c target/deadline changed");
            Path choiceOutput=Files.createDirectory(output.resolve("one-stock-bookmark1070-c"));
            var intent=StrictJson.object().put("schema","xar.current-stock-bookmark1070-c-intent/v1").put("request_id",prepared.requestId())
                    .put("original_instance_id",instance).put("source_query_request_id",query.original().requestId())
                    .put("original_deadline_utc",prepared.deadline().toString()).put("event_closed",false);
            intent.set("original_outbound",write(choiceOutput,"original-request.packet",prepared.originalPacket().value()));
            intent.set("actual_before_query",FullJsonTree.parse(query.frame().encode().bytes(),FullJsonTree.MAXIMUM_BYTES));
            originals.set("choice_intent",write(choiceOutput,"original-intent.json",FullJsonTree.encode(intent,FullJsonTree.MAXIMUM_BYTES)));
            stage="STOCK_BOOKMARK1070_ONE_NATIVE_FIXED_C";result.put("choice_calls",1);
            var outcome=transport.submitCurrentStockBookmark1070C(prepared);
            archiveCurrentLetterOutcome(transport,choiceOutput,"stock_bookmark1070_c",outcome,originals);
            var ack=requireCurrentRiteCreateActualAck(transport,owner,actualSession,outcome,prepared.requestId(),prepared.originalPacket().value());
            var frame=CurrentStockBookmark1070Result.decodeOutcome(ack);
            originals.set("choice_original_result",write(choiceOutput,"original-result.json",ack.originalResultToken().orElseThrow().bytes()));
            result.set("choice_result",FullJsonTree.parse(frame.encode().bytes(),FullJsonTree.MAXIMUM_BYTES));
            if(prepared.latestFrame().filter(frame::equals).isEmpty())throw new IOException("This stock.c ACK differs from actual private prepared latest frame");
            requireCurrentStockBookmark1070DispatchFrame(frame,query.frame(),instance);
            result.put("choice_callback_dispatched",true).put("native_returned",frame.nativeReturned()).put("native_handled",frame.nativeHandled());
            // The original query is consumed. Do not call its unused guard again.
            stage="STOCK_BOOKMARK1070_INDEPENDENT_AFTER_CORE";
            var after=readCurrentRiteCreateCore(transport,owner,plan,actualSession,output,"core-after-stock-bookmark1070",deadline,result,originals);
            if(!requireCurrentStockBookmark1070Core(after.frame()).equals(prefix))throw new IOException("Actual Core/actor/date changed after fixed stock choice");
            if(after.original().custody().orElseThrow().writeEntered().order().compareTo(ack.custody().orElseThrow().responseReceived().order())<=0)
                throw new IOException("Independent stock afterCore was not written after this choice ACK");
            stage="STOCK_BOOKMARK1070_INDEPENDENT_AFTER_CENSUS";
            var observed=readCurrentStockBookmark1070Query(transport,owner,after,actualSession,output,"stock-bookmark1070-after-query",deadline,result,originals);
            boolean absent=currentStockBookmark1070InstanceAbsent(observed.frame().source().orElseThrow(),instance);
            result.put("independent_after_census_observed",true).put("original_instance_absent",absent).put("original_instance_observation",absent?"ABSENT":"PRESENT");
            // PRESENT is known actual DATA, not a retry instruction or UNKNOWN.
            // Even ABSENT grants neither eventClosed nor global DateGate clearance.
        } finally {
            archiveNaturalDiagnostics(output,originals,transport.diagnostics());var progress=result.deepCopy();progress.set("originals",originals.deepCopy());
            write(output,"current-stock-bookmark1070-progress.json",FullJsonTree.encode(progress,FullJsonTree.MAXIMUM_BYTES));
        }
    }

    enum ObservationMode { SAVED_FULL,SAVED_CORE,MENU_CORE,CORE_CONTROL,CORE_EXIT,CORE_CHECKPOINT_SAVE,RITE_DOCTRINE,GUI_NAVIGATION_V2,PERSONAL_GOLD,ACTOR_FOUNDATION,FULL_CLOCK,DATE_ADVANCE,HELD_DATE_SENTINEL_STATUS,PERSONAL_CASH,GUI_ROOT_INDEX,GUI_WINDOW,RITE_DRAFT_COSTS,GUI_CONTROLS_V2,CURRENT_DATE_ADVANCE,RITE_FINAL_CONFIRMATION,CURRENT_FRONTEND_MENU,CURRENT_FRONTEND_MENU_QUIT,CURRENT_AUB_OBSERVER_FIXTURE,CURRENT_DJC_TARGET_QUERY,CURRENT_SUCCESSION_QUERY,CURRENT_SUCCESSION_CONTINUE,CURRENT_DJC_DECLARATION_UI,CURRENT_DJC_DECLARATION_SUBMIT,CURRENT_LETTER_QUERY,CURRENT_LETTER_REPLY_KNOWN,CURRENT_DJC_SELECTED_COST,CURRENT_DJC_SELECTED_COST_PREVIEW,CURRENT_LETTER_SET_QUERY,CURRENT_LETTER_SET_REPLY_KNOWN_INSTANCE,CURRENT_FULLSCREEN_EVENT_QUERY,CURRENT_FULLSCREEN_EVENT_ACK_KNOWN_INTRO,CURRENT_CURATED_DECISIONS_QUERY,CURRENT_CURATED_DECISIONS_OPEN,CURRENT_CURATED_DECISION_DETAIL,CURRENT_CURATED_DECISION_CONFIRM,CURRENT_XQOL_CONVERSION_PROMPT_QUERY,CURRENT_XQOL_CONVERSION_PROMPT_CONFIRM,CURRENT_XQOL_CONVERSION_PROMPT_CANCEL,CURRENT_XQOL_CONVERSION_THRESHOLD_QUERY,CURRENT_XQOL_CONVERSION_THRESHOLD_SET,CURRENT_COURTIER_CREATOR_CONTROLS_QUERY,CURRENT_COURTIER_CREATOR_CONTROL_EXECUTE,CURRENT_DECISIONS_CLOSE_QUERY,CURRENT_DECISIONS_CLOSE,CURRENT_COURTIER_CONFIGURATION_QUERY,CURRENT_COURTIER_CONFIGURATION_EXECUTE,CURRENT_COURTIER_CHOICES_QUERY,CURRENT_COURTIER_CHOICE_SELECT,CURRENT_SUPERMAN_HEALTH_QUERY,CURRENT_SUPERMAN_HEALTH_BASELINE_SAVE_AND_BEGIN,CURRENT_SUPERMAN_HEALTH_COMPLETED_CLOSE,CURRENT_SUPERMAN_HEALTH_RESUME_SAVED_BASELINE_AND_BEGIN,CURRENT_LYD,CURRENT_TED,CURRENT_STOCK_NEWGAME_SEED,CURRENT_DES_SAVED_GAME_INIT_GUARD,CURRENT_RITE_CREATE,CURRENT_RITE_TEXT,CURRENT_RITE_CREATION_BLOCKERS,CURRENT_STOCK_BOOKMARK1070,CURRENT_CCC,CURRENT_RMTM_TITLE_QUERY,CURRENT_RMTM_REMAINING,CURRENT_LIVING_ORIGINAL,CURRENT_ZG361_AE2,CURRENT_ZG361_REVIEW,CURRENT_ZG361_REVIEW_AE2,CURRENT_ZG361_SCOREBOARD,CURRENT_ARMY_IDENTITY_READONLY }
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
        if(schema.equals("xar.native-owner-snapshot-config/v54")) {
            StrictJson.object(config,Set.of("schema","mode","owner_descriptor","overall_timeout_seconds",
                    "read_timeout_seconds","maximum_frames_per_operation"));
            StrictJson.require("held_date_sentinel_status".equals(StrictJson.text(config.get("mode"))),
                    "fixed held Date sentinel status mode required");
            return ObservationMode.HELD_DATE_SENTINEL_STATUS;
        }
        if(schema.equals("xar.native-owner-snapshot-config/v53")) {
            StrictJson.object(config, Set.of("schema", "mode", "owner_descriptor", "overall_timeout_seconds",
                    "read_timeout_seconds", "maximum_frames_per_operation"));
            StrictJson.require("current_army_identity_readonly".equals(StrictJson.text(config.get("mode"))),
                    "explicit current army identity readonly mode required");
            return ObservationMode.CURRENT_ARMY_IDENTITY_READONLY;
        }
        if(schema.equals("xar.native-owner-snapshot-config/v52")) {currentZg361ScoreboardConfig(config);return ObservationMode.CURRENT_ZG361_SCOREBOARD;}
        if(schema.equals("xar.native-owner-snapshot-config/v51")) {currentZg361CombinedConfig(config);return ObservationMode.CURRENT_ZG361_REVIEW_AE2;}
        if(schema.equals("xar.native-owner-snapshot-config/v50")) {currentZg361ReviewConfig(config);return ObservationMode.CURRENT_ZG361_REVIEW;}
        if(schema.equals("xar.native-owner-snapshot-config/v49")) {currentZg361Ae2Config(config);return ObservationMode.CURRENT_ZG361_AE2;}
        if(schema.equals("xar.native-owner-snapshot-config/v48")) {currentLivingOriginalConfig(config);return ObservationMode.CURRENT_LIVING_ORIGINAL;}
        if(schema.equals("xar.native-owner-snapshot-config/v47")) {currentRmtmConfig(config);return ObservationMode.CURRENT_RMTM_REMAINING;}
        if(schema.equals("xar.native-owner-snapshot-config/v46")) {currentRmtmTitleQueryConfig(config);return ObservationMode.CURRENT_RMTM_TITLE_QUERY;}
        if(schema.equals("xar.native-owner-snapshot-config/v45")) {currentCccConfig(config);return ObservationMode.CURRENT_CCC;}
        if(schema.equals("xar.native-owner-snapshot-config/v44")) {currentStockBookmark1070Config(config);return ObservationMode.CURRENT_STOCK_BOOKMARK1070;}
        if(schema.equals("xar.native-owner-snapshot-config/v43")) {currentRiteCreationBlockersConfig(config);return ObservationMode.CURRENT_RITE_CREATION_BLOCKERS;}
        if(schema.equals("xar.native-owner-snapshot-config/v42")) {currentRiteTextConfig(config);return ObservationMode.CURRENT_RITE_TEXT;}
        StrictJson.require(!config.has("text"),"Text DATA belongs only to explicit v42 setter modes; old modes cannot borrow it");
        if(schema.equals("xar.native-owner-snapshot-config/v41")) {currentRiteCreateConfig(config);return ObservationMode.CURRENT_RITE_CREATE;}
        StrictJson.require(!config.has("confirmation_poll_interval_ms"),"Create confirmation polling belongs only to explicit v41; old v18 remains independent");
        if(schema.equals("xar.native-owner-snapshot-config/v40")) {requireCurrentDesInitGuardConfig(config);return ObservationMode.CURRENT_DES_SAVED_GAME_INIT_GUARD;}
        if(schema.equals("xar.native-owner-snapshot-config/v39")) {currentStockSeedConfig(config);return ObservationMode.CURRENT_STOCK_NEWGAME_SEED;}
        StrictJson.require(!config.has("maximum_core_polls")&&!config.has("core_poll_interval_ms"),"Stock seed world polling belongs only to explicit v39");
        if(schema.equals("xar.native-owner-snapshot-config/v38")) {currentTedConfig(config);return ObservationMode.CURRENT_TED;}
        StrictJson.require(!config.has("status_poll_delay_ms"),"TED status_poll_delay_ms belongs only to explicit v38 composite");
        if(schema.equals("xar.native-owner-snapshot-config/v37")) {currentLydConfig(config);return ObservationMode.CURRENT_LYD;}
        StrictJson.require(!config.has("personal_key")&&!config.has("event_role"),"LYD personal_key/event_role belong only to explicit v37 modes");
        if(schema.equals("xar.native-owner-snapshot-config/v36")) {
            currentSupermanSavedBaselineConfig(config);
            return ObservationMode.CURRENT_SUPERMAN_HEALTH_RESUME_SAVED_BASELINE_AND_BEGIN;
        }
        StrictJson.require(!config.has("baseline_progress"),"baseline_progress belongs only to the explicit v36 saved-baseline resume");
        if(schema.equals("xar.native-owner-snapshot-config/v35")) {
            return switch(currentSupermanHealthConfig(config).mode()) {
                case QUERY->ObservationMode.CURRENT_SUPERMAN_HEALTH_QUERY;
                case BASELINE_SAVE_AND_BEGIN->ObservationMode.CURRENT_SUPERMAN_HEALTH_BASELINE_SAVE_AND_BEGIN;
                case COMPLETED_CLOSE->ObservationMode.CURRENT_SUPERMAN_HEALTH_COMPLETED_CLOSE;
            };
        }
        StrictJson.require(!config.has("phase"),"phase belongs only to the explicit v35 fixed health query");
        if(schema.equals("xar.native-owner-snapshot-config/v34")) {
            return switch(currentCourtierChoicesConfig(config).action()) {
                case QUERY_CHOICES->ObservationMode.CURRENT_COURTIER_CHOICES_QUERY;
                case SELECT_CHOICE->ObservationMode.CURRENT_COURTIER_CHOICE_SELECT;
            };
        }
        StrictJson.require(!config.has("catalog")&&!config.has("choice_key"),"catalog/choice_key belong only to the explicit v34 catalogue modes");
        if(schema.equals("xar.native-owner-snapshot-config/v33")) {
            return switch(currentCourtierConfigurationConfig(config).action()) {
                case QUERY_CONFIGURATION->ObservationMode.CURRENT_COURTIER_CONFIGURATION_QUERY;
                case EXECUTE_SETTING->ObservationMode.CURRENT_COURTIER_CONFIGURATION_EXECUTE;
            };
        }
        StrictJson.require(!config.has("setting"),"setting belongs only to the explicit v33 fixed configuration modes");
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
    static NativeGameTransport.NativeSourceMode nativeSourceMode(ObservationMode mode) {
        return mode==ObservationMode.CURRENT_ARMY_IDENTITY_READONLY
                ? NativeGameTransport.NativeSourceMode.CURRENT_IDENTITY_READONLY
                : NativeGameTransport.NativeSourceMode.DEFAULT_CONTROL;
    }
    private static IOException archiveUnavailableFreshRead(Path output, ObjectNode originals,
            NativeFreshSnapshotPort.Result original, String reason) throws IOException {
        originals.set("dispatch", saveDispatch(output, original.dispatch()));
        ObjectNode rejected = StrictJson.object().put("reason", reason);
        if (original instanceof NativeFreshSnapshotPort.Received received) {
            rejected.set("frame", saveFrame(output, received.originalFrame()));
            rejected.set("snapshot_received", event(received.snapshotReceived()));
        } else if (original instanceof NativeFreshSnapshotPort.Unavailable unavailable
                && unavailable.originalFrame().isPresent()) {
            rejected.set("frame", saveFrame(output, unavailable.originalFrame().orElseThrow()));
            rejected.set("snapshot_received", event(unavailable.snapshotReceived().orElseThrow()));
        }
        rejected.set("originals", originals);
        write(output, "unavailable.json", FullJsonTree.encode(rejected, FullJsonTree.MAXIMUM_BYTES));
        return new IOException("original fresh READ unavailable; no retry: " + reason);
    }
    private static void readHeldDateStatus(NativeGameTransport transport,NativeGameTransport.CoreReceived core,
            Path output,Instant deadline,ObjectNode result,ObjectNode originals)throws IOException,InterruptedException {
        stage="HELD_DATE_SENTINEL_STATUS";
        var dispatch=transport.readHeldDateSentinelStatus(core,deadline);
        originals.set("date_status_dispatch",saveDispatch(Files.createDirectory(output.resolve("date-status")),dispatch));
        if(!(dispatch instanceof NativeActionPort.AckReceived ack)||!ack.nativeOk())
            throw new IOException("held Date status did not return a successful original ACK: "+dispatch.getClass().getSimpleName());
        var basis=core.original().custody().orElseThrow(()->new IOException("Core ACK custody unavailable"));
        var statusCustody=ack.custody().orElseThrow(()->new IOException("Date status ACK custody unavailable"));
        if(!basis.session().equals(statusCustody.session())||!basis.custodyEpoch().equals(statusCustody.custodyEpoch())
                ||statusCustody.writeEntered().order().compareTo(basis.responseReceived().order())<=0)
            throw new IOException("held Date status crossed the actual Core connection or chronology");
        var status=ClockStatusRead.decode(ack);
        result.put("date_status_request_id",ack.requestId()).put("date_sentinel_generation",status.generation().decimal())
                .put("date_sentinel_state",status.state().name()).put("date_sentinel_last_observed_raw",status.lastObservedDateRaw())
                .put("date_sentinel_starting_raw",status.startingDateRaw()).put("date_sentinel_target_raw",status.targetDateRaw())
                .put("date_sentinel_speed",status.speed()).put("date_sentinel_mode",status.mode().name())
                .put("date_sentinel_trigger_flags",status.triggerFlags()).put("date_sentinel_pause_observed",status.pauseObserved());
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
