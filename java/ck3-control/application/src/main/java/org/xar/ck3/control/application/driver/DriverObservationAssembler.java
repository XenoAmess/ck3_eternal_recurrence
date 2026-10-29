package org.xar.ck3.control.application.driver;

import java.math.BigInteger;
import org.xar.ck3.control.contracts.NativeCharacterId;
import java.time.Instant;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.NativeObservationPort.ObservedFrame;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.semantic.NativeSemanticNormalizer;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.m7.NativeCalendarObservation;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyStateProjection;
import org.xar.ck3.control.nativebridge.capabilities.army.NativeActiveWarsCodec;
import org.xar.ck3.control.nativebridge.capabilities.army.NativeArmiesCodec;

/** Joins preserved native bytes and Driver facts using the explicitly versioned semantic projection. */
public final class DriverObservationAssembler {
    public static final long LEGACY_OBSERVATION_VERSION=1;
    public static final long WAR_ARMY_OBSERVATION_VERSION=2;
    public static final long CANONICAL_OBSERVATION_VERSION=3;
    public static final long NATIVE_CAMPAIGN_OBSERVATION_VERSION=4;
    public sealed interface Result permits Complete, Incomplete { }
    public record Complete(ObservationIdentity identity, G2Source source, String sessionId,
            BigInteger connectionGeneration, OpportunityJson.Obj semantic, ExactRef originalEvidence,
            Instant observedAt, String fullBindingSha256,Optional<FullSnapshot> originalProjection) implements Result {
        public Complete(ObservationIdentity identity,G2Source source,String sessionId,BigInteger connectionGeneration,
                OpportunityJson.Obj semantic,ExactRef originalEvidence,Instant observedAt,String fullBindingSha256) {
            this(identity,source,sessionId,connectionGeneration,semantic,originalEvidence,observedAt,fullBindingSha256,Optional.empty());
        }
        public Complete {
            Objects.requireNonNull(identity); Objects.requireNonNull(source); StrictJson.text(sessionId);
            Objects.requireNonNull(connectionGeneration); Objects.requireNonNull(semantic);
            Objects.requireNonNull(originalEvidence); Objects.requireNonNull(observedAt);
            Objects.requireNonNull(originalProjection);
            StrictJson.require(fullBindingSha256 != null && fullBindingSha256.matches("[0-9a-f]{64}"), "full original binding digest required");
            StrictJson.require(identity.observationVersion()==NATIVE_CAMPAIGN_OBSERVATION_VERSION?originalProjection.isPresent():originalProjection.isEmpty(),
                    "only native campaign profile four requires its complete original projection");
            originalProjection.ifPresent(full->{
                var replay=new DriverObservationAssembler().projectFull(full.actual(),full.facts(),full.originalEvidence());
                StrictJson.require(replay.semantic().equals(full.semantic())&&replay.semantic().equals(semantic)
                        &&replay.fullBindingSha256().equals(fullBindingSha256)&&replay.originalEvidence().equals(originalEvidence)
                        &&replay.facts().source().equals(source)&&replay.actual().session().sessionId().equals(sessionId)
                        &&replay.actual().session().connectionGeneration().equals(connectionGeneration)
                        &&replay.actual().observedAt().equals(observedAt)
                        &&replay.facts().observationVersion()==identity.observationVersion()
                        &&replay.actual().session().machineId().equals(identity.machineId())
                        &&replay.actual().session().game().equals(identity.game())
                        &&replay.actual().snapshotId().equals(identity.frame().snapshotId())
                        &&replay.actual().nativeRevision().equals(identity.frame().identity().nativeRevision())
                        &&replay.facts().publicRevision().equals(identity.frame().revision())
                        &&OpportunityJson.integer(replay.semantic().get("date_raw"),"date_raw").equals(identity.frame().identity().dateRaw())
                        &&replay.facts().driver().session().actorId().equals(identity.frame().identity().player())
                        &&replay.facts().driver().session().episodeRunId().equals(identity.frame().episodeRunId()),
                        "native campaign complete DATA crossed its actual full projection");
            });
        }
    }
    public record Incomplete(List<String> reasons) implements Result {
        public Incomplete { reasons = List.copyOf(reasons); StrictJson.require(!reasons.isEmpty(), "explicit observation gaps required"); }
    }
    /** Full native/Driver join also represents death or an unreconciled successor, without a fabricated player identity. */
    public record FullSnapshot(ObservedFrame actual,DriverObservationFacts facts,OpportunityJson.Obj semantic,
            ExactRef originalEvidence,String fullBindingSha256) { }
    public Result assemble(ObservedFrame actual, DriverObservationFacts facts, ExactRef evidence) {
        Objects.requireNonNull(actual); Objects.requireNonNull(evidence);
        if (facts == null) return new Incomplete(List.of("real_driver_and_public_revision_facts_unavailable"));
        try {
            FullSnapshot full=projectFull(actual,facts,evidence);
            OpportunityJson.Obj semantic=full.semantic();
            var session=facts.driver().session();
            OpportunityJson.Obj player = OpportunityJson.object(semantic.get("played_character"), "played_character");
            BigInteger actor = NativeCharacterId.of(OpportunityJson.integer(player.get("character_id"), "character_id")).asBigInteger();
            StrictJson.require(actor.equals(session.actorId()), "unreconciled played-character/episode transition");
            OpportunityJson.bool(player.get("alive"), "alive");
            BigInteger date = OpportunityJson.integer(semantic.get("date_raw"), "date_raw");
            var frame = new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(actor, actual.nativeRevision(), date),
                    actual.snapshotId(),facts.publicRevision(),session.episodeRunId());
            ObservationIdentity identity = new ObservationIdentity(actual.session().machineId(),actual.session().game(),frame,facts.observationVersion());
            if(facts.observationVersion()!=NATIVE_CAMPAIGN_OBSERVATION_VERSION)NativeCalendarObservation.project(identity,facts.source(),semantic);
            return new Complete(identity,facts.source(),actual.session().sessionId(),actual.session().connectionGeneration(),semantic,
                    evidence,actual.observedAt(),full.fullBindingSha256(),facts.observationVersion()==NATIVE_CAMPAIGN_OBSERVATION_VERSION?Optional.of(full):Optional.empty());
        } catch (IllegalArgumentException | ArithmeticException failure) {
            return new Incomplete(List.of("native_driver_fact_join: " + failure.getMessage()));
        }
    }
    public FullSnapshot projectFull(ObservedFrame actual,DriverObservationFacts facts,ExactRef evidence) {
            Objects.requireNonNull(actual);Objects.requireNonNull(facts);Objects.requireNonNull(evidence);
            StrictJson.require(actual.session().equals(facts.transport()) && actual.snapshotId().equals(facts.snapshotId())
                    && actual.nativeRevision().equals(facts.nativeRevision())
                    && DriverJson.sha256(actual.state().bytes()).equals(facts.nativeStateSha256()), "Driver facts crossed the native frame/session");
            StrictJson.require(evidence.bytes() == actual.originalPacket().length
                    && evidence.sha256().equals(DriverJson.sha256(actual.originalPacket())), "original native evidence differs");
            OpportunityJson.Obj state=originalNativeState(actual);
            Map<String,OpportunityJson.Value> fields = new LinkedHashMap<>(state.members());
            for (var entry : facts.originalSemanticFields().members().entrySet()) {
                OpportunityJson.Value prior = fields.putIfAbsent(entry.getKey(), entry.getValue());
                if(facts.observationVersion()==NATIVE_CAMPAIGN_OBSERVATION_VERSION&&"episode_projection".equals(entry.getKey())) {
                    StrictJson.require(new OpportunityJson.Text(NativeCampaignProjection.WIRE_MODE).equals(entry.getValue()),
                            "explicit native campaign semantic projection required");
                    fields.put(entry.getKey(),entry.getValue());continue;
                }
                if("diagnostics".equals(entry.getKey()) && prior instanceof OpportunityJson.Obj nativeDiagnostics
                        && entry.getValue() instanceof OpportunityJson.Obj joinedDiagnostics) {
                    nativeDiagnostics.members().forEach((key,value) -> StrictJson.require(value.equals(joinedDiagnostics.get(key)),"native diagnostic overwritten: "+key));
                    fields.put(entry.getKey(),joinedDiagnostics);continue;
                }
                StrictJson.require(prior == null || prior.equals(entry.getValue()), "semantic producer overwrote actual native field: " + entry.getKey());
            }
            // Validate original extras against the raw packet before deriving canonical collections.
            switch(Math.toIntExact(facts.observationVersion())) {
                case 1 -> { /* Exact historical projection; never relabel an old manifest as v2. */ }
                case 2 -> {
                    OpportunityJson.Obj canonical=canonicalMilitaryState(state);
                    fields.put("active_wars",canonical.get("active_wars"));
                    fields.put("player_armies",canonical.get("player_armies"));
                }
                case 3,4 -> {
                    OpportunityJson.Obj canonical=canonicalNativeState(actual).semantic();
                    for(String key:NativeSemanticNormalizer.ownedFields())
                        if(canonical.members().containsKey(key))fields.put(key,canonical.get(key));
                    fields.put("active_wars",canonical.get("active_wars"));
                    fields.put("player_armies",canonical.get("player_armies"));
                }
                default -> throw new IllegalArgumentException("unsupported Driver observation semantic version");
            }
            var session = facts.driver().session();
            StrictJson.require(session.bridgePid() == actual.session().game().pid()
                    && facts.source().machineId().equals(actual.session().machineId()), "Driver Game/machine differs");
            put(fields,"format_version",new OpportunityJson.IntegerValue(BigInteger.ONE));
            put(fields,"snapshot_id",new OpportunityJson.Text(actual.snapshotId()));
            put(fields,"native_revision",new OpportunityJson.IntegerValue(actual.nativeRevision()));
            put(fields,"revision",new OpportunityJson.IntegerValue(facts.publicRevision()));
            put(fields,"episode_run_id",new OpportunityJson.Text(session.episodeRunId()));
            put(fields,"episode_character_id",new OpportunityJson.IntegerValue(session.actorId()));
            StrictJson.require(!state.members().containsKey("java_driver_facts_evidence"),"native packet cannot supply the Java Driver evidence field");
            fields.put("java_driver_facts_evidence",DriverObservationEvidenceReader.reference(facts.semanticFactsEvidence()));
            fields.put("native_command_history",new OpportunityJson.Arr(facts.driver().commandHistory().stream()
                    .map(row -> (OpportunityJson.Value) DriverJson.object(row.originalRow().json(), DriverJson.MAX_NATIVE_BYTES)).toList()));
            if(facts.observationVersion()!=NATIVE_CAMPAIGN_OBSERVATION_VERSION)retain(fields,"succession_lifecycle",facts.driver().successionLifecycle());
            retain(fields,"campaign_goal",facts.driver().campaignGoal());
            retain(fields,"native_rollback_war_failure",facts.driver().rollbackWarFailure());
            retain(fields,"native_rollback_war_failures",facts.driver().rollbackWarFailures());
            OpportunityJson.Obj semantic = new OpportunityJson.Obj(fields);
            if(facts.observationVersion()==NATIVE_CAMPAIGN_OBSERVATION_VERSION) {
                StrictJson.require(facts.driver().successionLifecycle() instanceof DriverStateSnapshot.NullValue
                        &&new OpportunityJson.Text(NativeCampaignProjection.WIRE_MODE).equals(facts.originalSemanticFields().get("episode_projection")),
                        "native campaign profile requires its explicit null-lifecycle Driver projection");
                semantic=NativeCampaignProjection.withOriginalEpisodeFields(actual,semantic);
            }
            OpportunityJson.bool(semantic.get("paused"), "paused"); OpportunityJson.bool(semantic.get("map_ready"), "map_ready");
            int speed = OpportunityJson.integer(semantic.get("speed"), "speed").intValueExact();
            StrictJson.require(speed >= 1 && speed <= 5, "actual native speed 1..5 required");
            for (String key : facts.observationVersion()==NATIVE_CAMPAIGN_OBSERVATION_VERSION
                    ? List.of("active_event","pending_character_interaction") : List.of("active_event","pending_character_interaction","one_life_terminal_reason"))
                StrictJson.require(semantic.members().containsKey(key), "explicit semantic presence required: " + key);
            OpportunityJson.array(semantic.get("active_wars"), "active_wars"); OpportunityJson.array(semantic.get("player_armies"), "player_armies");
            OpportunityJson.object(semantic.get("diagnostics"), "diagnostics");
            OpportunityJson.integer(semantic.get("date_raw"),"date_raw");
            return new FullSnapshot(actual,facts,semantic,evidence,bindingSha256(semantic));
    }
    /** Validates the actual framed packet without changing its original state or lexical representation. */
    public static OpportunityJson.Obj originalNativeState(ObservedFrame actual) {
        Objects.requireNonNull(actual);
        byte[] framed=actual.originalPacket();
        StrictJson.require(framed.length>=5 && framed.length<=DriverJson.MAX_NATIVE_BYTES+4,"bounded framed original native packet required");
        int length=java.nio.ByteBuffer.wrap(framed,0,4).order(java.nio.ByteOrder.LITTLE_ENDIAN).getInt();
        StrictJson.require(length>0 && length<=DriverJson.MAX_NATIVE_BYTES && framed.length==length+4,"exact original LE uint32 frame length required");
        OpportunityJson.Obj packet = DriverJson.object(java.util.Arrays.copyOfRange(framed,4,framed.length), DriverJson.MAX_NATIVE_BYTES);
        StrictJson.require("state_snapshot".equals(OpportunityJson.text(packet.get("type"), "type"))
                && BigInteger.ONE.equals(OpportunityJson.integer(packet.get("protocol_version"), "protocol_version"))
                && actual.snapshotId().equals(OpportunityJson.text(packet.get("snapshot_id"), "snapshot_id"))
                && actual.nativeRevision().equals(OpportunityJson.integer(packet.get("revision"), "revision")), "original native envelope differs");
        OpportunityJson.Obj state = DriverJson.object(actual.state().bytes(), DriverJson.MAX_NATIVE_BYTES);
        StrictJson.require(state.equals(OpportunityJson.object(packet.get("state"), "state")), "raw state differs from original native packet");
        return state;
    }
    /** Canonical DATA is never accepted as an original native input. */
    public static final class CanonicalNativeState {
        private final OpportunityJson.Obj semantic;
        private CanonicalNativeState(OpportunityJson.Obj semantic) { this.semantic=semantic; }
        public OpportunityJson.Obj semantic() { return semantic; }
    }
    /** Sole current receive/fingerprint/publication/archive route: normalize only the exact original framed packet. */
    public static CanonicalNativeState canonicalNativeState(ObservedFrame original) {
        OpportunityJson.Obj raw=originalNativeState(Objects.requireNonNull(original));
        // Preserve historical military's order and parser; contracts cannot depend on a military/application module.
        OpportunityJson.Obj military=canonicalMilitaryState(raw);
        var nativeTree=(com.fasterxml.jackson.databind.node.ObjectNode)DriverJson.toNode(raw);
        var canonical=NativeSemanticNormalizer.normalize(NativeSemanticNormalizer.original(nativeTree),
                original.snapshotId(),original.nativeRevision()).semantic();
        Map<String,OpportunityJson.Value> fields=new LinkedHashMap<>(military.members());
        // Untouched original fields retain their lexical JSON tokens; derived fields cross the explicit normalized bridge.
        for(String key:NativeSemanticNormalizer.ownedFields())
            if(canonical.has(key))fields.put(key,canonicalField(raw,key,canonical.get(key)));
        return new CanonicalNativeState(new OpportunityJson.Obj(fields));
    }
    private static OpportunityJson.Value canonicalField(OpportunityJson.Obj raw,String key,com.fasterxml.jackson.databind.JsonNode canonical) {
        // These values were only retained or filtered by the lower normalizer, never numerically transformed.
        if("history".equals(key) && raw.get(key) instanceof OpportunityJson.Arr original)return original;
        if("top_exclusive_modal_choice_hint".equals(key)) {
            if(raw.get(key) instanceof OpportunityJson.Obj original && canonical.isObject()) {
                Map<String,OpportunityJson.Value> retained=new LinkedHashMap<>();
                canonical.fieldNames().forEachRemaining(name -> retained.put(name,original.get(name)));
                return new OpportunityJson.Obj(retained);
            }
            return raw.get(key);
        }
        return DriverJson.fromNormalizedNode(canonical);
    }
    /** Exact version-2 projection retained exclusively for historical manifests. */
    private static OpportunityJson.Obj canonicalMilitaryState(OpportunityJson.Obj raw) {
        Objects.requireNonNull(raw);
        var tree=DriverJson.toNode(raw);
        var wars=NativeActiveWarsCodec.normalize(tree.get("active_wars"));
        var armies=ArmyStateProjection.playerArmiesFromState(wars,tree.get("player_armies"));
        Map<String,OpportunityJson.Value> fields=new LinkedHashMap<>(raw.members());
        fields.put("active_wars",DriverJson.fromNode(NativeActiveWarsCodec.encode(wars)));
        fields.put("player_armies",DriverJson.fromNode(NativeArmiesCodec.encode(armies)));
        return new OpportunityJson.Obj(fields);
    }
    /** Same eleven original _binding fields, with explicit presence tags retaining missing versus null. */
    public static String bindingSha256(OpportunityJson.Obj semantic) {
        List<OpportunityJson.Value> rows = new ArrayList<>();
        for (String key : List.of("snapshot_id","revision","native_revision","date_raw","paused","map_ready")) rows.add(tag(semantic,key));
        OpportunityJson.Obj player = semantic.get("played_character") instanceof OpportunityJson.Obj value ? value : new OpportunityJson.Obj(Map.of());
        rows.add(tag(player,"character_id")); rows.add(tag(player,"alive"));
        for (String key : List.of("active_event","pending_character_interaction","one_life_terminal_reason")) rows.add(tag(semantic,key));
        return DriverJson.sha256(DriverJson.encode(new OpportunityJson.Arr(rows)));
    }
    private static OpportunityJson.Value tag(OpportunityJson.Obj row, String key) {
        if (!row.members().containsKey(key)) return new OpportunityJson.Arr(List.of(new OpportunityJson.Bool(false)));
        return new OpportunityJson.Arr(List.of(new OpportunityJson.Bool(true),row.get(key)));
    }
    private static void put(Map<String,OpportunityJson.Value> fields, String key, OpportunityJson.Value value) {
        fields.put(key,value);
    }
    private static void retain(Map<String,OpportunityJson.Value> fields,String key,DriverStateSnapshot.Slot value) {
        switch (value) {
            case DriverStateSnapshot.Missing ignored -> fields.remove(key);
            case DriverStateSnapshot.NullValue ignored -> fields.put(key,OpportunityJson.Nil.INSTANCE);
            case DriverStateSnapshot.Value retained -> fields.put(key,parseValue(retained.json()));
        }
    }
    private static OpportunityJson.Value parseValue(byte[] raw) {
        // Wrap a retained arbitrary JSON value to use the same full-frame strict parser.
        byte[] prefix = "{\"v\":".getBytes(java.nio.charset.StandardCharsets.UTF_8);
        byte[] wrapped = new byte[prefix.length + raw.length + 1];
        System.arraycopy(prefix,0,wrapped,0,prefix.length); System.arraycopy(raw,0,wrapped,prefix.length,raw.length); wrapped[wrapped.length-1]='}';
        return DriverJson.object(wrapped,DriverJson.MAX_NATIVE_BYTES).get("v");
    }
}
