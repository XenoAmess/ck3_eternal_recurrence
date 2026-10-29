package org.xar.ck3.control.application.effects;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.ArrayList;
import org.xar.ck3.control.g2.m0.RaiktorExitPostcondition;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.wave2.military.exitresult.OrdinaryWarExitObservation;
import org.xar.ck3.control.wave2.military.exitresult.OrdinaryWarExitObservationCodec;

/** Uses the genuine ordinary-war-exit composer. War absence never claims requested settlement/paid resources. */
public final class NativeWarExitEffects implements NativeEffectRegistry.Observer {
    private final NativeEffectSnapshots snapshots;
    public interface TruceReadPort {
        Optional<PlanningReadReceipt> read(ActionCommand original, ActionState.Attempt attempt, Complete after, int towardCharacterId);
        /** Pure installed decoder replay of the original receipt; never submits a new query. */
        void replay(Complete after, int towardCharacterId, PlanningReadReceipt original);
    }
    private final Optional<TruceReadPort> truceReads;
    /** Historical limited observer; actual new Root installs the two-argument form. */
    public NativeWarExitEffects(NativeEffectSnapshots snapshots) { this.snapshots=Objects.requireNonNull(snapshots);truceReads=Optional.empty(); }
    public NativeWarExitEffects(NativeEffectSnapshots snapshots, TruceReadPort actualTruces) {
        this.snapshots=Objects.requireNonNull(snapshots);truceReads=Optional.of(Objects.requireNonNull(actualTruces));
    }
    public record TruceQuery(int towardCharacterId) {
        public TruceQuery { StrictJson.require(towardCharacterId>0,"positive full truce target required"); }
        public OperationKey operation(){return new OperationKey("query-raiktor-actual-truce-expiry-v1-"+towardCharacterId);}
        public OpportunityJson.Obj arguments(Complete after){
            ObjectNode n=StrictJson.object().put("toward_character_id",towardCharacterId)
                    .put("expected_revision",after.identity().frame().revision().toString());
            return OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(n)),"original truce arguments");
        }
    }
    /** The one selector shared with the Root original-intent allowlist; no observation permission is created. */
    public static Optional<TruceQuery> truceQuery(ActionCommand original,Complete originalBefore,Complete actualAfter) {
        StrictJson.require(originalBefore.identity().equals(original.before())&&originalBefore.source().equals(original.source())
                &&originalBefore.sessionId().equals(original.sessionId()),"truce selector changed the original before frame");
        var material=material(original,originalBefore,actualAfter,StrictJson.object().put("step",original.operation().value()).put("accepted",false),List.of());
        if(material==null||material.bound()==null||!material.bound().warAbsent()||material.bound().opponentCharacterId()<=0)return Optional.empty();
        new NativeEffectSnapshots.Pair(originalBefore,actualAfter);
        return Optional.of(new TruceQuery(material.bound().opponentCharacterId()));
    }
    /** A pure original-pending binder, shared by live and archived Root qualification. */
    public static void requireOriginalRequest(PlanningReadRequest request,ActionCommand original,ActionState.Attempt attempt,
            Complete originalBefore,Complete actualAfter) {
        var query=truceQuery(original,originalBefore,actualAfter).orElseThrow(()->new IllegalArgumentException("original war absence/opponent unavailable"));
        var identity=request.origin().requireReconciliation();var pending=identity.pending();
        StrictJson.require(attempt.guard().origin() instanceof CommandOrigin.Gameplay&&attempt.guard().observed().equals(original.before())
                &&attempt.guard().source().equals(original.source())&&attempt.guard().sessionId().equals(original.sessionId())
                &&attempt.guard().operation().equals(original.operation())&&pending.actionId().equals(original.actionId())&&pending.bodySha256().equals(ActionCodec.bodySha256(original))
                &&pending.requestId().equals(attempt.requestId())&&pending.originalBefore().equals(original.before())
                &&identity.factual().equals(actualAfter.identity())&&identity.source().equals(actualAfter.source())
                &&identity.sessionId().equals(actualAfter.sessionId())&&identity.connectionGeneration().equals(actualAfter.connectionGeneration())
                &&identity.connectionGeneration().equals(attempt.guard().connectionGeneration())&&identity.nativeEvidence().equals(actualAfter.originalEvidence())
                &&request.source().equals(original.source())&&request.sessionId().equals(original.sessionId())
                &&request.operation().equals(query.operation())&&request.arguments().equals(query.arguments(actualAfter)),
                "truce observation crossed the original canonical primitive/actual after-frame/native request");
    }
    public static long warId(OperationKey operation) {
        return OrdinaryWarExitObservationCodec.actionForLiteral(operation.value()).warId();
    }
    @Override public NativeEffectRegistry.Projected observe(ActionCommand command, ActionState.Attempt attempt, NativeActionPort.DispatchOutcome dispatch) {
        var pair=snapshots.read(command,attempt);var selected=truceQuery(command,pair.before(),pair.after());
        List<PlanningReadReceipt> independent=List.of();
        if(truceReads.isPresent()&&selected.isPresent()) {
            var query=selected.orElseThrow();var read=truceReads.orElseThrow().read(command,attempt,pair.after(),query.towardCharacterId());
            if(read.isEmpty())return NativeEffectRegistry.Projected.pending("actual persisted truce query unavailable; original primitive is not resubmitted",List.of(pair.after().originalEvidence()));
            var original=read.orElseThrow();truceReads.orElseThrow().replay(pair.after(),query.towardCharacterId(),original);independent=List.of(original);
        }
        var projected=project(command,attempt,dispatch,pair,independent,FormalProjection.NATIVE_CUSTODY_V3);
        if (!(projected.result() instanceof ActionPorts.EffectObserved)) return projected;
        return NativeEffectSnapshots.withEvidence(projected,List.of(snapshots.evidence(command,attempt,pair,independent,projected.compatibleResult().orElseThrow())));
    }
    private enum FormalProjection { LEGACY_V1, SUBMISSION_FACT_V2, NATIVE_CUSTODY_V3 }
    private static NativeEffectRegistry.Projected project(ActionCommand command, ActionState.Attempt attempt,
            NativeActionPort.DispatchOutcome dispatch, NativeEffectSnapshots.Pair pair,List<PlanningReadReceipt> independent, FormalProjection projection) {
        long id = warId(command.operation());
        ObjectNode action = StrictJson.object(); action.put("step", command.operation().value()); action.put("accepted", false);
        if (dispatch instanceof NativeActionPort.AckReceived ack && ack.originalResultToken().isPresent()) {
            ObjectNode original = EffectJson.object(EffectJson.parse(ack.originalResultToken().orElseThrow()));
            StrictJson.require(StrictJson.text(original.get("step")).equals(command.operation().value()), "war action result step drift");
            action = original;
        }
        StrictJson.require(independent.size()<=1,"one original directed truce read at most");
        for(var read:independent) {
            var selected=truceQuery(command,pair.before(),pair.after()).orElseThrow();
            requireOriginalRequest(read.request(),command,attempt,pair.before(),pair.after());
            NativeEffectSnapshots.requireAfterRead(command,attempt,pair.after(),read,selected.operation());
        }
        var material=material(command,pair.before(),pair.after(),action,independent);
        if (material == null || material.bound() == null || !material.bound().warAbsent())
            return NativeEffectRegistry.Projected.pending("full original WarID remains present or its independent observation is unavailable", List.of(pair.after().originalEvidence()));
        StrictJson.require(material.action().warId() == id, "war result identity drift");
        // War absence, observed resources and the directed persisted relation remain separate from settlement attribution.
        var actual = new ArrayList<ExpectedValue>(List.<ExpectedValue>of(new ExpectedInteger(new FieldKey("war_id"), BigInteger.valueOf(id)),
                new ExpectedBoolean(new FieldKey("war_absence_observed"), material.bound().warAbsent())));
        if(material.truce() instanceof OrdinaryWarExitObservation.NativeTruce truce) {
            actual.add(new ExpectedBoolean(new FieldKey("truce_observed"),true));
            actual.add(new ExpectedInteger(new FieldKey("truce_owner_character_id"),BigInteger.valueOf(truce.ownerCharacterId())));
            actual.add(new ExpectedInteger(new FieldKey("truce_toward_character_id"),BigInteger.valueOf(truce.towardCharacterId())));
            actual.add(new ExpectedBoolean(new FieldKey("truce_has_relation"),truce.status()==OrdinaryWarExitObservation.TruceStatus.AVAILABLE));
            if(truce.expiryDateRaw()!=null)actual.add(new ExpectedInteger(new FieldKey("truce_expiry_date_raw"),BigInteger.valueOf(truce.expiryDateRaw())));
        }
        ObjectNode compatible = action.deepCopy();
        compatible.set("ordinary_war_exit_observation_v1", StrictJson.parse(OrdinaryWarExitObservationCodec.encode(material), StrictJson.EXPLICIT_MAX_BYTES));
        ObjectNode formal = frozenPostcondition(command, attempt, dispatch, pair, action, id, projection);
        if (formal != null) {
            compatible.set(switch (projection) {
                case LEGACY_V1 -> "raiktor_three_way_exit_postcondition_v1";
                case SUBMISSION_FACT_V2 -> "raiktor_three_way_exit_postcondition_v2";
                case NATIVE_CUSTODY_V3 -> "raiktor_three_way_exit_postcondition_v3";
            }, formal);
            actual.add(new ExpectedBoolean(new FieldKey("raiktor_exit_postcondition_verified"), false));
            actual.add(new ExpectedBoolean(new FieldKey("raiktor_gen034_closed"), false));
        }
        return NativeEffectSnapshots.observed(command, attempt, pair.after(), OrdinaryWarExitObservation.SCHEMA, List.copyOf(actual),
                NativeEffectSnapshots.publication(pair.after()), EffectJson.raw(compatible), List.of());
    }
    private static OrdinaryWarExitObservation.Receipt material(ActionCommand command,Complete before,Complete after,
            ObjectNode action,List<PlanningReadReceipt> independent) {
        StrictJson.require(independent.size()<=1,"bounded original truce observation required");
        ObjectNode inputs=StrictJson.object();inputs.set("before_snapshot",EffectJson.object(before.semantic()));
        inputs.set("post_snapshot",EffectJson.object(after.semantic()));inputs.set("action_result",action);
        inputs.putNull("claims_result");inputs.putNull("title_holder_results");inputs.putNull("truce_result");
        if(!independent.isEmpty())inputs.set("truce_result",EffectJson.parse(independent.getFirst().original().originalResultToken()
                .orElseThrow(()->new IllegalArgumentException("original truce native token absent"))));
        var material=independent.isEmpty()
                ?OrdinaryWarExitObservationCodec.compose(inputs.get("before_snapshot"), inputs.get("post_snapshot"),
                        inputs.get("action_result"), inputs.get("claims_result"), inputs.get("title_holder_results"), inputs.get("truce_result"))
                :OrdinaryWarExitObservationCodec.composeNativeTruce(inputs.get("before_snapshot"), inputs.get("post_snapshot"),
                        inputs.get("action_result"), inputs.get("truce_result"));
        if(!independent.isEmpty())StrictJson.require(material!=null&&material.truce() instanceof OrdinaryWarExitObservation.NativeTruce,
                "original truce token failed the same strict actual4 outcome decoder");
        return material;
    }
    /** Actual Root command is the frozen producer; missing source/cleanup/cold-restore inputs never become fabricated evidence. */
    private static ObjectNode frozenPostcondition(ActionCommand command, ActionState.Attempt attempt,
            NativeActionPort.DispatchOutcome dispatch, NativeEffectSnapshots.Pair pair, ObjectNode action, long warId, FormalProjection projection) {
        ObjectNode arguments = EffectJson.object(OpportunityJson.toNode(command.arguments()));
        if (arguments.has("schema")) {
            var durable = org.xar.ck3.control.nativebridge.capabilities.army.ArmyOrdinaryActionArguments.decode(command.arguments());
            if (durable.terminalSelection().isEmpty()) return null;
            arguments = EffectJson.object(OpportunityJson.toNode(durable.terminalSelection().orElseThrow().encode()));
        }
        JsonNode rawPlan = arguments.get("postcondition_plan"); if (rawPlan == null || rawPlan.isNull()) return null;
        ObjectNode plan = StrictJson.object(rawPlan, java.util.Set.of("schema_version", "route", "requirements", "expectations", "verified", "gen034_completion_eligible"));
        ObjectNode expected = EffectJson.object(plan.get("expectations"));
        StrictJson.require(StrictJson.integer(expected.get("war_id"), 1, Integer.MAX_VALUE) == warId, "formal expected full WarID differs from actual command");
        ObjectNode before = EffectJson.object(pair.before().semantic()), post = EffectJson.object(pair.after().semantic());
        ObjectNode player = EffectJson.object(before.get("played_character")), diagnostics = EffectJson.object(before.get("diagnostics"));
        StrictJson.require(expected.get("played_character_id").equals(player.get("character_id")), "frozen played character differs from original pre-action snapshot");
        String route = StrictJson.text(plan.get("route"));
        StrictJson.require(route.equals(StrictJson.text(arguments.get("requested_outcome"))) && java.util.Set.of("white_peace", "surrender").contains(route), "formal command route drift");
        JsonNode selected = null;
        StrictJson.require(before.get("active_wars").isArray(), "formal before wars missing");
        for (JsonNode value : before.get("active_wars")) if (value.isObject() && value.get("war_id") != null && value.get("war_id").isIntegralNumber()
                && value.get("war_id").bigIntegerValue().equals(BigInteger.valueOf(warId))) {
            StrictJson.require(selected == null, "formal before war ambiguous"); selected = value;
        }
        StrictJson.require(selected != null && "attacker".equals(StrictJson.text(selected.get("player_side")))
                && selected.get("primary_opponent_character_id") != null && expected.get("opponent_character_id").equals(selected.get("primary_opponent_character_id")),
                "formal plan lacks original attacker/opponent binding");
        ObjectNode frame = StrictJson.object().put("war_id", warId);
        frame.set("snapshot_id", before.get("snapshot_id")); frame.set("snapshot_revision", before.get("revision"));
        frame.set("native_revision", before.get("native_revision")); frame.set("date_raw", before.get("date_raw"));
        frame.set("episode_id", before.get("episode_run_id")); frame.set("ck3_pid", diagnostics.get("bridge_pid"));
        frame.put("connection_id", "connection-generation:" + StrictJson.integer(diagnostics.get("connection_generation"), BigInteger.ONE, StrictJson.UINT64_MAX));
        frame.set("primary_attacker_character_id", player.get("character_id")); frame.set("primary_defender_character_id", expected.get("opponent_character_id"));
        ObjectNode gate = RaiktorExitPostcondition.bindFrozenPlan(frame, plan, command.operation().value(), route);
        return switch (projection) {
            case LEGACY_V1 -> RaiktorExitPostcondition.provide(gate, action, post, null, null);
            case SUBMISSION_FACT_V2 -> RaiktorExitPostcondition.provideSubmissionFacts(gate, action, post, null, null);
            case NATIVE_CUSTODY_V3 -> RaiktorExitPostcondition.provideNativeSubmissionFacts(gate, action, post,
                    nativeSubmissionOrigin(command, attempt, dispatch));
        };
    }
    private static RaiktorExitPostcondition.NativeSubmissionOrigin nativeSubmissionOrigin(ActionCommand command,
            ActionState.Attempt attempt, NativeActionPort.DispatchOutcome dispatch) {
        if (!(dispatch instanceof NativeActionPort.AckReceived ack) || !ack.nativeOk() || ack.originalResultToken().isEmpty()
                || ack.outbound().isEmpty() || ack.custody().isEmpty())
            return RaiktorExitPostcondition.NativeSubmissionOrigin.UNAVAILABLE;
        StrictJson.require(ack.requestId().equals(attempt.requestId()) && attempt.preparedRequest().step().equals(command.operation().value())
                && attempt.guard().observed().equals(command.before()) && attempt.guard().source().equals(command.source())
                && attempt.guard().sessionId().equals(command.sessionId()) && attempt.guard().operation().equals(command.operation()),
                "native war submission crossed its original command/request/guard");
        var custody = ack.custody().orElseThrow(); custody.verify(ack, attempt.guard());
        StrictJson.require(!custody.writeEntered().observedAt().isBefore(attempt.submittedAt()),
                "native war write predates its canonical submitted attempt");
        ObjectNode expected = EffectJson.object(EffectJson.parse(attempt.preparedRequest().additionalFields())).deepCopy();
        StrictJson.require(!expected.has("type") && !expected.has("protocol_version") && !expected.has("request_id")
                && !expected.has("step") && !expected.has("expected_revision"), "prepared native war fields collide with wire envelope");
        expected.put("type", "execute_step").put("protocol_version", 1).put("request_id", attempt.requestId())
                .put("step", command.operation().value()).put("expected_revision", command.before().frame().identity().nativeRevision());
        StrictJson.require(java.util.Arrays.equals(StrictJson.canonical(expected, StrictJson.EXPLICIT_MAX_BYTES),
                StrictJson.canonical(nativePacket(ack.outbound().orElseThrow().originalPacket()), StrictJson.EXPLICIT_MAX_BYTES)),
                "native war outbound differs from the original durable request");
        ObjectNode frame = StrictJson.object(nativePacket(ack.originalPacket()),
                java.util.Set.of("type", "protocol_version", "request_id", "ok", "result"));
        StrictJson.require(StrictJson.text(frame.get("type")).equals("command_result")
                && StrictJson.text(frame.get("request_id")).equals(attempt.requestId()), "native war response request/type drift");
        StrictJson.integer(frame.get("protocol_version"), 1, 1); StrictJson.trueValue(frame.get("ok"));
        StrictJson.require(frame.equals(EffectJson.parse(ack.originalFrame()))
                && frame.get("result").equals(EffectJson.parse(ack.originalResultToken().orElseThrow())),
                "native war packet/frame/result token mismatch");
        return RaiktorExitPostcondition.NativeSubmissionOrigin.VERIFIED_CUSTODY;
    }
    private static ObjectNode nativePacket(byte[] packet) {
        StrictJson.require(packet.length > 4
                && java.nio.ByteBuffer.wrap(packet, 0, 4).order(java.nio.ByteOrder.LITTLE_ENDIAN).getInt() == packet.length - 4,
                "exact native war packet framing required");
        return EffectJson.object(StrictJson.parse(java.util.Arrays.copyOfRange(packet, 4, packet.length)));
    }
    private static FormalProjection archivedProjection(RawJson compatible) {
        ObjectNode value = EffectJson.object(EffectJson.parse(compatible));
        boolean legacy = value.has("raiktor_three_way_exit_postcondition_v1");
        boolean current = value.has("raiktor_three_way_exit_postcondition_v2");
        boolean nativeCustody = value.has("raiktor_three_way_exit_postcondition_v3");
        StrictJson.require((legacy ? 1 : 0) + (current ? 1 : 0) + (nativeCustody ? 1 : 0) <= 1,
                "ambiguous archived formal postcondition projection");
        // Explicit formal versions control replay; marker-free ordinary archives retain the old v2 default.
        // A frozen plan with a removed marker still fails the exact original projection comparison.
        return legacy ? FormalProjection.LEGACY_V1 : nativeCustody ? FormalProjection.NATIVE_CUSTODY_V3 : FormalProjection.SUBMISSION_FACT_V2;
    }
    public static NativeRecordedEvidenceVerifier.Binding archivedVerifier(OperationKey operation,ExactRef source,NativeEffectEvidence.FrameLoader frames) {
        return archivedVerifier(operation,source,frames,Optional.empty());
    }
    public static NativeRecordedEvidenceVerifier.Binding archivedVerifier(OperationKey operation,ExactRef source,
            NativeEffectEvidence.FrameLoader frames,TruceReadPort actualTruces) {
        return archivedVerifier(operation,source,frames,Optional.of(Objects.requireNonNull(actualTruces)));
    }
    private static NativeRecordedEvidenceVerifier.Binding archivedVerifier(OperationKey operation,ExactRef source,
            NativeEffectEvidence.FrameLoader frames,Optional<TruceReadPort> actualTruces) {
        warId(operation);Objects.requireNonNull(frames);
        return new NativeRecordedEvidenceVerifier.Binding(operation,source,(head,receipt,archive)->{
            var original=NativeEffectEvidence.load(receipt,archive,frames);var settled=(ActionState.Settled)receipt.state();
            StrictJson.require(original.independentReads().size()<=1,"war exit has at most its one original truce read");
            for(var read:original.independentReads()) {
                var selected=truceQuery(receipt.command(),original.frames().before(),original.frames().after()).orElseThrow();
                actualTruces.orElseThrow(()->new IllegalArgumentException("actual installed truce replay absent"))
                        .replay(original.frames().after(),selected.towardCharacterId(),read);
            }
            var replayed=project(receipt.command(),settled.attempt(),settled.dispatch(),original.frames(),original.independentReads(),
                    archivedProjection(original.compatibleResult()));
            replayed=NativeEffectSnapshots.withEvidence(replayed,((ActionState.Applied)settled.settlement()).observation().supportingEvidence());
            NativeEffectEvidence.requireSame(settled.settlement(),replayed,original.compatibleResult());
        });
    }
}
