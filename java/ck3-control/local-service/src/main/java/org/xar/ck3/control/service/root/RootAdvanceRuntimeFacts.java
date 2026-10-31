package org.xar.ck3.control.service.root;

import static org.xar.ck3.control.contracts.StrictJson.require;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.function.Supplier;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.ObservationProvenance;
import org.xar.ck3.control.application.action.CommandOrigin;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.advance.AdvanceObservationPort;
import org.xar.ck3.control.application.advance.ProductionAdvanceReadiness;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler;
import org.xar.ck3.control.application.driver.DriverTransportNoticeStability;
import org.xar.ck3.control.application.history.DriverHistoryAccess;
import org.xar.ck3.control.application.planning.governance.CrownRetryDue;
import org.xar.ck3.control.application.planning.governance.CrownRetryPublication;
import org.xar.ck3.control.application.readiness.ReadinessAuthority.LeaseSnapshot;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.semantic.NativeSemanticNormalizer;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;

/** Actual current Root lease and private CROWN publication feed the sole Life readiness consumer. */
public final class RootAdvanceRuntimeFacts implements ProductionAdvanceReadiness.RuntimeFactsPort, ProductionAdvanceReadiness.RuntimeScope {
    public static final String SCHEMA="xar.java-root-life-runtime-facts/v1";
    public static final String SETTINGS_SCHEMA="xar.java-root-life-settings/v1";
    public static final int SETTINGS_MAX_BYTES=4096;
    private final RootRuntimeContext context;
    private final CrownRetryDue crown;
    private final Supplier<Optional<CrownRetryPublication.ImportProof>> retainedProof;
    private final Settings settings;

    public RootAdvanceRuntimeFacts(RootRuntimeContext actualContext, CrownRetryDue sameDueProducer,
            Supplier<Optional<CrownRetryPublication.ImportProof>> actualRetainedPublication, Settings actualSettings) {
        context=Objects.requireNonNull(actualContext);crown=Objects.requireNonNull(sameDueProducer);
        retainedProof=Objects.requireNonNull(actualRetainedPublication);settings=Objects.requireNonNull(actualSettings);
    }

    /** Source/Native capture occurs outside the immutable Driver history callback. */
    @Override public <T> T current(ActionCommand parent, AdvanceObservationPort.Frame frame, Supplier<T> work) {
        Objects.requireNonNull(parent);Objects.requireNonNull(frame);Objects.requireNonNull(work);requireParent(parent,frame);
        try {
            context.requireCurrent(parent.deadline());var same=context.borrowedSession();context.writer().requireSession(same);
            String head=same.head().digest();
            T result=context.collector().current(same,frame.identity(),parent.deadline(),lease->{
                var raw = DriverObservationAssembler.originalNativeState(context.collector().activeOriginalNativeFrame(same, lease));
                var aux = lease.driver().auxiliary();
                var augmentation = clockAugmentationFields(raw, aux);
                requireClockEquivalent(frame, lease.frame(), raw, augmentation, context.collector().activeNativeOwnedNoticeKeys(same, lease),
                        "outer runtime scope changed the actual clock observation");
                return work.get();
            });
            context.writer().requireSession(same);require(head.equals(same.head().digest()),"clock readiness changed the original writer head");
            return result;
        }catch(IOException failure){throw new UncheckedIOException("actual outer Root clock readiness unavailable",failure);}
    }

    static boolean clockEquivalent(AdvanceObservationPort.Frame expected, DriverObservationAssembler.Complete actual, OpportunityJson.Obj rawNative, Set<String> augmentation, Set<String> nativeOwnedNoticeKeys) {
        if (!expected.identity().equals(actual.identity()) || !expected.source().equals(actual.source()) || !expected.sessionId().equals(actual.sessionId())) return false;
        if (!(expected.provenance() instanceof ObservationProvenance.Push || expected.provenance() instanceof ObservationProvenance.FreshSnapshotQuery)) return false;
        var pid = expected.identity().game().pid();
        var expectedStable = clockSemantic(expected.semantic(), augmentation, nativeOwnedNoticeKeys, pid, rawNative);
        var actualStable = clockSemantic(actual.semantic(), augmentation, nativeOwnedNoticeKeys, pid, rawNative);
        return expectedStable.equals(actualStable);
    }

    private static final Set<String> CLOCK_DERIVED_FIELDS = Set.of(
            "format_version", "snapshot_id", "native_revision", "revision", "episode_run_id", "episode_character_id",
            "succession_lifecycle", "campaign_goal", "native_rollback_war_failure",
            "native_rollback_war_failures", "episode_projection", "backend_id", "source", "diagnostics",
            "active_wars", "player_armies");

    static Set<String> clockAugmentationFields(OpportunityJson.Obj rawNative, OpportunityJson.Obj producerFields) {
        // The actual producer copied Driver auxiliary into these extras. A same-name raw Native field
        // remains Native-owned; normalized Native and joined Driver business fields remain exact too.
        var augmentation = new java.util.HashSet<>(producerFields.members().keySet());
        // Assembler appends the current Driver rows separately; capture keeps the authoritative
        // Driver stamp/history-basis/currentDriver relation rather than duplicating old semantic rows.
        augmentation.add("native_command_history");
        augmentation.removeAll(rawNative.members().keySet());
        augmentation.removeAll(NativeSemanticNormalizer.ownedFields());
        augmentation.removeAll(CLOCK_DERIVED_FIELDS);
        return Set.copyOf(augmentation);
    }

    static OpportunityJson.Obj clockSemantic(OpportunityJson.Obj semantic, Set<String> augmentation,
            Set<String> nativeOwnedNoticeKeys, long actualPid, OpportunityJson.Obj rawNative) {
        var stable = DriverTransportNoticeStability.heldSemantic(semantic, nativeOwnedNoticeKeys, actualPid);
        var fields = new java.util.LinkedHashMap<>(stable.members());
        augmentation.forEach(fields::remove);
        fields.put("diagnostics", clockDiagnostics(OpportunityJson.object(stable.get("diagnostics"), "clock diagnostics"),
                rawNative, nativeOwnedNoticeKeys));
        return new OpportunityJson.Obj(fields);
    }

    static OpportunityJson.Obj clockDiagnostics(OpportunityJson.Obj joinedStableDiagnostics, OpportunityJson.Obj rawNative, Set<String> nativeOwnedNoticeKeys) {
        var rawDiag = rawNative.get("diagnostics");
        Set<String> rawKeys = rawDiag instanceof OpportunityJson.Obj obj ? obj.members().keySet() : java.util.Set.of();
        var javaKeys = java.util.Set.of("pipe_name", "connected", "bridge_pid", "connection_generation");
        var retain = new java.util.HashSet<>(rawKeys);
        retain.addAll(nativeOwnedNoticeKeys);
        retain.addAll(javaKeys);
        var members = new java.util.LinkedHashMap<String, OpportunityJson.Value>();
        for (var entry : joinedStableDiagnostics.members().entrySet()) {
            if (retain.contains(entry.getKey())) {
                members.put(entry.getKey(), entry.getValue());
            }
        }
        return new OpportunityJson.Obj(members);
    }

    private static void requireClockEquivalent(AdvanceObservationPort.Frame expected, DriverObservationAssembler.Complete actual,
            OpportunityJson.Obj rawNative, Set<String> augmentation, Set<String> nativeOwnedNoticeKeys, String reason) {
        if (!clockEquivalent(expected, actual, rawNative, augmentation, nativeOwnedNoticeKeys))
            require(false, reason + "; " + clockDifference(expected, actual, rawNative, augmentation, nativeOwnedNoticeKeys));
    }

    static String clockDifference(AdvanceObservationPort.Frame expected, DriverObservationAssembler.Complete actual,
            OpportunityJson.Obj rawNative, Set<String> augmentation, Set<String> nativeOwnedNoticeKeys) {
        try {
            var roles = new java.util.ArrayList<String>();
            if (!expected.identity().equals(actual.identity())) roles.add("identity");
            if (!expected.source().equals(actual.source())) roles.add("source");
            if (!expected.sessionId().equals(actual.sessionId())) roles.add("session");
            if (!(expected.provenance() instanceof ObservationProvenance.Push || expected.provenance() instanceof ObservationProvenance.FreshSnapshotQuery)) roles.add("provenance_kind");
            var left = clockSemantic(expected.semantic(), augmentation, nativeOwnedNoticeKeys, expected.identity().game().pid(), rawNative);
            var right = clockSemantic(actual.semantic(), augmentation, nativeOwnedNoticeKeys, actual.identity().game().pid(), rawNative);
            var keys = new java.util.TreeSet<String>(left.members().keySet()); keys.addAll(right.members().keySet());
            var different = keys.stream().filter(key -> !Objects.equals(left.get(key), right.get(key)))
                    .limit(8).map(key -> key.substring(0, Math.min(80, key.length()))).toList();
            return "roles=" + roles + "; stable_semantic_keys=" + different
                    + "; native_refs=" + expected.originalEvidence().sha256().substring(0, 12) + "/" + actual.originalEvidence().sha256().substring(0, 12)
                    + "; observed_at_delta=" + java.time.Duration.between(expected.observedAt(), actual.observedAt());
        } catch (RuntimeException unavailable) {
            return "clock_difference_unavailable=" + unavailable.getClass().getSimpleName();
        }
    }

    private static void requireParent(ActionCommand parent, AdvanceObservationPort.Frame frame) {
        require(parent.origin() instanceof CommandOrigin.Gameplay
                && parent.before().machineId().equals(frame.identity().machineId())
                && parent.before().game().equals(frame.identity().game())
                && parent.before().frame().episodeRunId().equals(frame.identity().frame().episodeRunId())
                && parent.before().frame().identity().player().equals(frame.identity().frame().identity().player())
                && parent.source().equals(frame.source()) && parent.sessionId().equals(frame.sessionId()),
                "actual shared-clock gameplay parent and same Game/episode/actor/source/session required");
    }

    /** Active-only borrow inside the actual frozen history: never observes or replaces Driver facts. */
    @Override public ProductionAdvanceReadiness.RuntimeFacts inspect(ActionCommand parent, AdvanceObservationPort.Frame frame,
            DriverHistoryAccess.View history) {
        Objects.requireNonNull(parent);Objects.requireNonNull(frame);Objects.requireNonNull(history);
        requireParent(parent,frame);
        try {
            context.requireCurrent(parent.deadline());
            ContinuityStorePort.Session same=context.borrowedSession();context.writer().requireSession(same);
            String head=same.head().digest();
            var result=context.collector().borrowCurrent(same,frame.identity(),parent.deadline(),
                    lease->capture(same,parent,frame,history,lease));
            context.writer().requireSession(same);context.requireCurrent(parent.deadline());
            require(same.head().digest().equals(head),"runtime facts changed the actual borrowed writer head");
            return result;
        } catch(IOException failure) {throw new UncheckedIOException("actual Root Life runtime facts unavailable",failure);}
    }

    private ProductionAdvanceReadiness.RuntimeFacts capture(ContinuityStorePort.Session same, ActionCommand parent,
            AdvanceObservationPort.Frame frame, DriverHistoryAccess.View history, LeaseSnapshot lease)throws IOException {
        var raw = DriverObservationAssembler.originalNativeState(context.collector().activeOriginalNativeFrame(same, lease));
        var aux = lease.driver().auxiliary();
        var augmentation = clockAugmentationFields(raw, aux);
        requireClockEquivalent(frame, lease.frame(), raw, augmentation, context.collector().activeNativeOwnedNoticeKeys(same, lease),
                "runtime facts changed the actual clock observation");
        require(lease.frame().source().equals(context.source())
                && frame.identity().game().equals(context.game().generation())
                && frame.sessionId().equals(context.game().sessionId())
                && lease.driver().stamp().equals(history.stamp())
                && lease.driver().originalHistoryBasis().equals(history.originalHistoryBasis())
                && lease.semantic().frame().equals(frame.identity())
                && lease.semantic().originalNativePacket().equals(lease.frame().originalEvidence())
                && lease.semantic().originalDriver().equals(history.currentDriverEvidence()),
                "runtime facts crossed the exact current complete Native/Driver/history lease");
        require(context.clock().instant().isBefore(lease.validUntil()),"actual Life runtime lease expired");
        ActionPorts.OutcomeArchive archive=context.archive().withSession(same);
        settings.requireOriginal(archive);
        Optional<CrownRetryPublication.ImportProof> proof=Objects.requireNonNull(retainedProof.get(),
                "CROWN publication absence must be explicit");
        // Absence of publication is valid for first advancement; verifiedCrownMaximum handles empty due.
        Optional<CrownRetryDue.VerifiedDue> due=Optional.empty();
        if(proof.isPresent()) {
            var captured=crown.capture(same,proof.orElseThrow(),frame.identity(),frame.source(),frame.semantic(),parent.deadline());
            crown.requireCurrent(same,captured,parent.deadline());due=Optional.of(captured);
        }
        ObjectNode original=StrictJson.object().put("schema",SCHEMA).put("action_body_sha256",ActionCodec.bodySha256(parent));
        original.set("observation",ProposalLifecycleCodec.observation(frame.identity()));
        original.set("settings_original",settings.original().toJson());
        original.set("original_history",history.originalHistoryBasis().toJson());
        original.set("current_driver",history.currentDriverEvidence().toJson());
        original.set("native_packet",lease.semantic().originalNativePacket().toJson());
        original.set("semantic",lease.semantic().semantic().toJson());
        original.set("driver_stamp",lease.semantic().driverStamp().toJson());
        original.set("hello",lease.originalHello().toJson());original.set("heartbeat",lease.originalHeartbeat().toJson());
        var steps=original.putArray("executable_steps");lease.executableSteps().stream().map(value->value.value()).sorted().forEach(steps::add);
        var capabilities=original.putArray("bridge_capabilities");lease.bridgeCapabilities().stream().sorted().forEach(capabilities::add);
        if(due.isPresent())original.set("crown_publication_body",due.orElseThrow().publicationBody().payload().toJson());
        else original.putNull("crown_publication_body");
        ExactRef evidence=archive.preserveMaterial(new RawJson(StrictJson.canonical(original,65536)));
        context.writer().requireSession(same);
        return new ProductionAdvanceReadiness.RuntimeFacts(frame.identity(),frame.source(),frame.sessionId(),history.stamp(),
                lease.executableSteps(),lease.bridgeCapabilities(),due,settings.crownQueryEnabled(),settings.crownPausedQueryEnabled(),
                settings.warDailyWatchEnabled(),evidence);
    }

    /** Source-bound configuration data only. It grants no current lease, writer or CROWN publication. */
    public static final class Settings {
        private static final String CROWN_QUERY="crown_query_enabled",CROWN_PAUSED="crown_paused_query_enabled",WAR_DAILY="war_daily_watch_enabled";
        private static final Set<String> FIELDS=Set.of("schema",CROWN_QUERY,CROWN_PAUSED,WAR_DAILY);
        private final ExactRef original;
        private final boolean crownQuery,crownPaused,warDailyWatch;
        private final boolean ordinary;
        private Settings(ExactRef original,boolean crownQuery,boolean crownPaused,boolean warDailyWatch) {
            this(original,crownQuery,crownPaused,warDailyWatch,false);
        }
        private Settings(ExactRef original,boolean crownQuery,boolean crownPaused,boolean warDailyWatch,boolean ordinary) {
            this.original=Objects.requireNonNull(original);this.crownQuery=crownQuery;this.crownPaused=crownPaused;
            this.warDailyWatch=warDailyWatch;this.ordinary=ordinary;
        }
        /** Whole configuration provenance is metadata, not a separately encoded historical Life document. */
        public static Settings ordinary(ExactRef wholeConfigMetadata,boolean crownQueryEnabled,
                boolean crownPausedQueryEnabled,boolean warDailyWatchEnabled) {
            return new Settings(wholeConfigMetadata,crownQueryEnabled,crownPausedQueryEnabled,warDailyWatchEnabled,true);
        }
        /** Sole typed producer; physical write/read identity qualification remains the actual package owner's job. */
        public static RawJson encode(boolean crownQueryEnabled,boolean crownPausedQueryEnabled,boolean warDailyWatchEnabled) {
            return new RawJson(StrictJson.canonical(StrictJson.object().put("schema",SETTINGS_SCHEMA)
                    .put(CROWN_QUERY,crownQueryEnabled).put(CROWN_PAUSED,crownPausedQueryEnabled).put(WAR_DAILY,warDailyWatchEnabled)));
        }
        public static Settings decode(ExactRef original,RawJson actualOriginal) {
            Objects.requireNonNull(original);Objects.requireNonNull(actualOriginal);byte[] bytes=actualOriginal.bytes();
            require(bytes.length>0 && bytes.length<=SETTINGS_MAX_BYTES && original.bytes()==bytes.length
                    && original.sha256().equals(DriverJson.sha256(bytes)),"Life settings original SHA/size differs");
            var body=StrictJson.object(StrictJson.parse(bytes,SETTINGS_MAX_BYTES),FIELDS);
            require(SETTINGS_SCHEMA.equals(StrictJson.text(body.get("schema"))),"unsupported Life runtime settings schema");
            return new Settings(original,flag(body,CROWN_QUERY),flag(body,CROWN_PAUSED),flag(body,WAR_DAILY));
        }
        public ExactRef original(){return original;}
        public boolean crownQueryEnabled(){return crownQuery;}
        public boolean crownPausedQueryEnabled(){return crownPaused;}
        public boolean warDailyWatchEnabled(){return warDailyWatch;}
        private void requireOriginal(ActionPorts.OutcomeArchive archive) {
            if(ordinary)return;
            Settings retained=decode(original,archive.loadMaterial(original));
            require(retained.crownQuery==crownQuery && retained.crownPaused==crownPaused && retained.warDailyWatch==warDailyWatch,
                    "actual Life runtime settings differ from their retained archive source");
        }
        private static boolean flag(JsonNode body,String key) {
            JsonNode value=body.get(key);require(value!=null && value.isBoolean(),"exact Life setting boolean required: "+key);
            return value.booleanValue();
        }
    }
}
