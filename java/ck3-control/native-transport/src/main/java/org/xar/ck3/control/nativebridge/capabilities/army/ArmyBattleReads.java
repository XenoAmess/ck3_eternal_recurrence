package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.EnumMap;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** Actual finite collector over the single held transport. M5 owns every strict battle-domain decoder. */
public final class ArmyBattleReads {
    public sealed interface Observation extends ArmyBattleReadValue permits Control, Transition, Terminal {
        PublicMethod method(); Obj normalized(); UInt64 querySequence();
        @Override default Kind kind() { return switch(method()) { case QUERY_BATTLE_CONTROL_SNAPSHOT_V1 -> Kind.CONTROL; case QUERY_BATTLE_TRANSITION_V1 -> Kind.TRANSITION; case QUERY_BATTLE_TERMINAL_TRANSITION_V1 -> Kind.TERMINAL; default -> throw new IllegalArgumentException("not a battle observation"); }; }
        @Override default java.math.BigInteger sequence() { return querySequence().value(); }
        @Override default Obj extensions() {
            var n = empty();
            if (this instanceof Control control) control.resume().ifPresent(v -> n.set("active_combat_resume_inputs_v1",OpportunityJson.toNode(v)));
            if (this instanceof Terminal terminal) { terminal.sixStage().ifPresent(v -> n.set("person_six_stage_captures",v.toJson())); terminal.installedTransfers().ifPresent(v -> n.set("person_installed_transfers",v.toJson())); }
            return OpportunityJson.object(OpportunityJson.parse(bytes(n)),"strict battle outer extensions");
        }
    }
    public record Control(BattleResponses.Control value, UInt64 querySequence, Optional<Obj> resume) implements Observation {
        public Control { Objects.requireNonNull(value); Objects.requireNonNull(querySequence); Objects.requireNonNull(resume); }
        @Override public PublicMethod method() { return PublicMethod.QUERY_BATTLE_CONTROL_SNAPSHOT_V1; }
        @Override public Obj normalized() { return value.originalFrame(); }
    }
    public record Transition(BattleResponses.Transition value, UInt64 querySequence) implements Observation {
        public Transition { Objects.requireNonNull(value); Objects.requireNonNull(querySequence); }
        @Override public PublicMethod method() { return PublicMethod.QUERY_BATTLE_TRANSITION_V1; }
        @Override public Obj normalized() { return value.originalFrame(); }
    }
    /** Complete nested terminal plus optional complete original outer person observations. Missing remains unobserved. */
    public record Terminal(BattleResponses.Terminal value, UInt64 querySequence, Optional<BattlePersonSixStageCaptureCodec.NormalizedQuery> sixStage,
            Optional<BattlePersonInstalledTransfersCodec.Query> installedTransfers) implements Observation {
        public Terminal { Objects.requireNonNull(value); Objects.requireNonNull(querySequence); Objects.requireNonNull(sixStage); Objects.requireNonNull(installedTransfers); require(installedTransfers.isEmpty() || sixStage.isPresent(), "installed transfers require the same actual six-stage owner selection"); }
        @Override public PublicMethod method() { return PublicMethod.QUERY_BATTLE_TERMINAL_TRANSITION_V1; }
        @Override public Obj normalized() { return value.originalFrame(); }
    }
    public enum Capture { PUBLIC_QUERY, INTERNAL_RETREAT }
    public record Selection(ArmyCalls.Call input, Context context, Capture capture, Optional<OperationKey> requestedLiteral) {
        public Selection(ArmyCalls.Call input,Context context) { this(input,context,Capture.INTERNAL_RETREAT,Optional.empty()); }
        public Selection(ArmyCalls.Call input,Context context,Capture capture) { this(input,context,capture,Optional.empty()); }
        public Selection {
            Objects.requireNonNull(input);Objects.requireNonNull(context);Objects.requireNonNull(capture);Objects.requireNonNull(requestedLiteral);
            require(METHODS.contains(input.method()), "not a finite M5 Army read");input.revision().requireCurrent(context.before().frame().revision());
            requestedLiteral.ifPresent(original->{
                require(input instanceof ArmyCalls.Terminal,"only terminal requests preserve noncanonical duplicate character spelling");
                ArmySteps.requireTerminalLiteral(original,terminal((ArmyCalls.Terminal)input));
            });
        }
    }
    public static final Set<PublicMethod> METHODS = Set.of(PublicMethod.QUERY_BATTLE_CONTROL_SNAPSHOT_V1, PublicMethod.QUERY_BATTLE_TRANSITION_V1, PublicMethod.QUERY_BATTLE_TERMINAL_TRANSITION_V1);
    private final EnumMap<PublicMethod,RootReadContractCatalog.Family<Selection,Observation>> families = new EnumMap<>(PublicMethod.class);
    private final PlanningReadPort reads;
    public ArmyBattleReads(ExactRef definition, ExactRef strictDecoder, PlanningReadPort reads) {
        this.reads = Objects.requireNonNull(reads);
        for (PublicMethod method : METHODS) {
            String capability = switch (method) {
                case QUERY_BATTLE_CONTROL_SNAPSHOT_V1 -> "game.command.query-battle-control-snapshot-v1-N";
                case QUERY_BATTLE_TRANSITION_V1 -> "game.command.query-battle-transition-v1-N";
                case QUERY_BATTLE_TERMINAL_TRANSITION_V1 -> "game.command.query-battle-terminal-transition-v1-N";
                default -> throw new IllegalArgumentException("unregistered battle read");
            };
            families.put(method, new RootReadContractCatalog.Family<>("army-battle-" + method.pythonName(), Selection.class, ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,
                    Optional.of(capability), definition, strictDecoder, ArmyBattleReads::key, s -> operation(s, method), s -> {
                        var primitive = primitive(s, method); return new ReadContract<>("army-battle-" + method.pythonName() + "-" + ArmyReadKey.digest(key(s)),
                                operation(s, method), Optional.of(capability), primitive.permissionKey(), ReadContract.PermissionMode.ADVERTISED_CAPABILITY, primitive.wire(), ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP, definition,
                                (request,requestId) -> { verify(request, s); return new NativeRequest(operation(s,method).value(),primitive.request().requiredCapability(),primitive.request().additionalFields(),primitive.request().preparationEvidence()); }, receipt -> decode(s,receipt), receipt -> decode(s,receipt),
                                (original,value,current,semantic) -> ArmyNativeReadEvidence.requireCanonicalEquivalent(original,current));
                    }));
        }
    }
    public List<RootReadContractCatalog.Family<?,?>> families() { return families.values().stream().<RootReadContractCatalog.Family<?,?>>map(f -> f).toList(); }
    public ReadContract<Observation> issue(RootReadContractCatalog catalog,Selection s) { return catalog.issue(Objects.requireNonNull(families.get(s.input().method())),s); }
    public PlanningReadRequest request(Selection s) { var c=s.context(); return new PlanningReadRequest(c.before(),c.source(),c.sessionId(),operation(s,s.input().method()),arguments(s),c.deadline()); }
    public PlanningReadResult.Known<Observation> read(ContinuityStorePort.Session borrowed, RootReadContractCatalog catalog, Selection selection) {
        Objects.requireNonNull(borrowed); var result = reads.read(borrowed, issue(catalog,selection), request(selection));
        if (result instanceof PlanningReadResult.Known<Observation> known) return known;
        throw new IllegalStateException(((PlanningReadResult.Unavailable<Observation>) result).reason());
    }
    public static Observation decode(Selection selection, PlanningReadReceipt receipt) {
        verify(receipt.request(),selection);
        Context current = ArmyNativeReadEvidence.contextForRequest(selection.context(),receipt.request());
        return decodePayload(selection.input(),current,ArmyNativeReadEvidence.result(current,receipt),selection.requestedLiteral());
    }
    /** Shared strict payload projection only; each caller must first verify its actual gameplay or reconciliation read receipt. */
    static Observation decodePayload(ArmyCalls.Call input,Context current,ObjectNode n) { return decodePayload(input,current,n,Optional.empty()); }
    private static Observation decodePayload(ArmyCalls.Call input,Context current,ObjectNode n,Optional<OperationKey> originalLiteral) {
        String payload;
        Set<String> optional;
        switch (input.method()) {
            case QUERY_BATTLE_CONTROL_SNAPSHOT_V1 -> { payload = "battle_control_snapshot"; optional = Set.of("active_combat_resume_inputs_v1"); }
            case QUERY_BATTLE_TRANSITION_V1 -> { payload = "battle_transition_snapshot"; optional = Set.of(); }
            case QUERY_BATTLE_TERMINAL_TRANSITION_V1 -> { payload = "battle_terminal_transition"; optional = Set.of("person_six_stage_captures", "person_installed_transfers"); }
            default -> throw new IllegalArgumentException("unregistered battle read");
        }
        Set<String> required = Set.of("step", "accepted", "status", "query_sequence", "snapshot_revision", payload);
        var extra = new java.util.HashSet<>(names(n)); require(extra.containsAll(required), "missing original Native battle envelope field"); extra.removeAll(required);
        require(optional.containsAll(extra), "unqualified outer battle extension; retain original read, never drop sidecars");
        yes(n.get("accepted")); UInt64 sequence = positive(n.get("query_sequence")); equal(n.get("snapshot_revision"), current.nativeRevision());
        return switch (input) {
            case ArmyCalls.Unit call -> {
                var value = BattleResponseCodec.control(bytes(n), current, new ArmyRequests.Unit(call.army())); equal(n.get("status"), "available");
                Optional<Obj> resume = Optional.empty();
                if (n.has("active_combat_resume_inputs_v1")) {
                    ObjectNode parent = parse(OpportunityJson.encode(value.originalFrame()));
                    ObjectNode normalized = BattleControlExtensionCodec.normalizeResume(object(n.get("active_combat_resume_inputs_v1")), parent);
                    resume = Optional.of(org.xar.ck3.control.application.driver.DriverJson.object(bytes(normalized), org.xar.ck3.control.application.driver.DriverJson.MAX_NATIVE_BYTES));
                }
                yield new Control(value, sequence, resume);
            }
            case ArmyCalls.CombatId call -> {
                var value = BattleResponseCodec.transition(bytes(n), current, new ArmyRequests.Combat(call.combat()));
                require(OpportunityJson.text(value.originalFrame().get("status"), "transition status").equals(text(n.get("status"))), "battle transition envelope differs from its exact domain status");
                yield new Transition(value, sequence);
            }
            case ArmyCalls.Terminal call -> {
                var request = terminal(call); var value = BattleTerminalCodec.terminal(bytes(n), current, request,originalLiteral.orElseGet(()->new OperationKey(ArmySteps.terminal(request))));
                require(OpportunityJson.text(value.originalFrame().get("status"), "terminal status").equals(text(n.get("status"))), "terminal envelope differs from its exact domain status");
                Optional<BattlePersonSixStageCaptureCodec.NormalizedQuery> six = Optional.empty(); Optional<BattlePersonInstalledTransfersCodec.Query> installed = Optional.empty();
                if (n.has("person_six_stage_captures")) six = Optional.of(BattlePersonSixStageCaptureCodec.decode(n.get("person_six_stage_captures"), "person_six_stage_captures", current.nativeRevision(), current.dateRaw().intValueExact(), call.effectiveCharacters().stream().map(character -> (long) character.value()).toList()));
                if (n.has("person_installed_transfers")) installed = Optional.of(BattlePersonInstalledTransfersCodec.decode(n.get("person_installed_transfers"), "person_installed_transfers", six.orElseThrow(() -> new IllegalArgumentException("installed person transfer outer field has no actual same-query owner capture")), current.nativeRevision(), current.dateRaw().intValueExact()));
                yield new Terminal(value, sequence, six, installed);
            }
            default -> throw new IllegalArgumentException("battle read request shape changed");
        };
    }
    static ArmyRequests.Terminal terminal(ArmyCalls.Terminal call) {
        Optional<FullId> combat = call.combat() instanceof Present<FullId> p ? Optional.of(p.value()) : Optional.empty();
        Optional<PublicUnitId> subject = call.subject() instanceof Present<PublicUnitId> p ? Optional.of(p.value()) : Optional.empty();
        Optional<UInt64> cursor = call.afterSequence() instanceof Present<UInt64> p ? Optional.of(p.value()) : Optional.empty();
        return new ArmyRequests.Terminal(combat, subject, cursor, call.effectiveCharacters().stream().map(c -> new FullId(c.value())).toList());
    }
    private static ArmyNativeRecipes.Primitive primitive(Selection selection, PublicMethod method) {
        require(selection.input().method() == method, "battle family method changed");
        var recipe = ArmyNativeRecipes.prepare(selection.input(), selection.context(), new ArmyNativeRecipes.NoFacts(), false);
        require(recipe instanceof ArmyNativeRecipes.Primitive p && p.effect() == ArmyNativeRecipes.Effect.READ_ONLY, "battle read cannot prepare a mutation"); return (ArmyNativeRecipes.Primitive) recipe;
    }
    private static OperationKey operation(Selection s, PublicMethod method) { return s.requestedLiteral().orElseGet(()->new OperationKey(primitive(s, method).request().step())); }
    private static Obj arguments(Selection s) { var n = empty().put("capture_context",s.capture().name()); n.set("public_arguments",parse(ArmyCallCodec.encode(s.input()).bytes())); s.requestedLiteral().ifPresent(step->n.put("requested_literal",step.value())); return OpportunityJson.object(OpportunityJson.parse(bytes(n)), "Army battle arguments"); }
    private static RawJson key(Selection s) { var n = parse(ArmyReadKey.key(s.input(),s.context()).bytes()).put("capture_context",s.capture().name()); s.requestedLiteral().ifPresent(step->n.put("requested_literal",step.value())); return new RawJson(bytes(n)); }
    private static void verify(PlanningReadRequest request, Selection s) {
        Context c = s.context(); require(request.before().equals(c.before()) && request.source().equals(c.source()) && request.sessionId().equals(c.sessionId())
                && request.operation().equals(operation(s,s.input().method())) && request.arguments().equals(arguments(s)), "Army battle read crossed its exact source, operation or typed arguments");
    }
}
