package org.xar.ck3.control.application.planning.governance;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.ActionPorts.OutcomeArchive;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.finance.FinanceReadContracts;
import org.xar.ck3.control.application.planning.finance.FinanceStatePort;
import org.xar.ck3.control.application.planning.finance.OrdinaryFinanceCollector;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.wave2.finance.feastordinary.HostedFeastCodec;
import org.xar.ck3.control.governance.activity.ActivityConfigurationCodec;
import org.xar.ck3.control.governance.activity.ActivityConfigurationModels;
import static org.xar.ck3.control.application.planning.governance.FeastObservationSupplier.*;
import static org.xar.ck3.control.application.planning.governance.GovernanceObservationSupplier.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Concrete collection over the same finance read contracts, one guarded port and immutable outcome archive. */
public final class FeastObservationCollector implements FeastObservationSupplier {
    public enum ActivityQuery { DIAGNOSTIC, HOSTED, STAGE_ONE, STAGE_TWO, LOCATION }
    public record ActivityPacket(PlanningReadReceipt receipt, Obj result) {
        public ActivityPacket { Objects.requireNonNull(receipt); Objects.requireNonNull(result); }
    }
    /** Root adapts the unique native Activity installation; application never imports native-bridge. */
    @FunctionalInterface public interface ActivityReads {
        Read<ActivityPacket> read(ActivityQuery query, PlanningRequest request, Obj arguments);
    }
    private static final Set<String> ENVELOPE = Set.of("step", "accepted", "status", "private_build", "read_only", "advertised", "backend_id");
    private final OrdinaryFinanceCollector finance;
    private final GovernanceObservationSupplier governance;
    private final OutcomeArchive archive;
    private final ActivityReads activities;
    private final Optional<GovernanceBorrowedSession> borrowed;

    public FeastObservationCollector(OrdinaryFinanceCollector finance, GovernanceObservationSupplier governance, OutcomeArchive archive,
            ActivityReads activities) {
        this.finance = Objects.requireNonNull(finance); this.governance = Objects.requireNonNull(governance); this.archive = Objects.requireNonNull(archive);
        this.activities = Objects.requireNonNull(activities);
        this.borrowed = Optional.empty();
    }
    public FeastObservationCollector(OrdinaryFinanceCollector finance, GovernanceObservationSupplier governance, OutcomeArchive archive,
            ActivityReads activities, GovernanceBorrowedSession borrowed) {
        this.finance = Objects.requireNonNull(finance); this.governance = Objects.requireNonNull(governance);
        this.archive = Objects.requireNonNull(archive); this.activities = Objects.requireNonNull(activities);
        this.borrowed = Optional.of(Objects.requireNonNull(borrowed));
    }
    @Override public Read<State> state(PlanningRequest request) {
        var read = finance.state(request);
        if (read instanceof FinanceStatePort.Missing missing) return new Unavailable<>(missing.reason());
        var retained = ((FinanceStatePort.Known) read).snapshot();
        Read<Durable> cadenceRead = governance.durable(request);
        if (cadenceRead instanceof Unavailable<Durable> unavailable) return new Unavailable<>(unavailable.reason());
        Known<Durable> durable = (Known<Durable>) cadenceRead;
        try {
            durable.value().bind(request);
            var cadence = durable.value().cadence().orElseThrow(() -> new IllegalArgumentException("actual Feast cadence body is unimported"));
            var ledger = retained.ledger(FinanceStatePort.Domain.FEAST).orElseThrow(() -> new IllegalArgumentException("actual Feast intent body is unimported"));
            Obj original = ledger.original(); Set<String> keys = original.members().keySet();
            require(keys.equals(Set.of("schema", "pending", "resolved")) || keys.equals(Set.of("schema", "pending", "resolved", "history")), "Feast ledger fields differ");
            require(new Text("xar.ck3.activity-feast-stage5-start-private.v1").equals(original.get("schema")), "Feast ledger version differs");
            Value pending = original.get("pending"), resolved = original.get("resolved");
            require((pending == Nil.INSTANCE || pending instanceof Obj) && (resolved == Nil.INSTANCE || resolved instanceof Obj), "Feast ledger pending/resolved kinds differ");
            if (original.get("history") != null) array(original.get("history"), "Feast receipt history").forEach(value -> object(value, "retained Feast receipt"));
            Optional<Terminal> terminal = retainedTerminal(resolved);
            var refs = new ArrayList<>(durable.originals()); refs.add(retained.head().canonicalHead()); refs.add(ledger.document().original());
            State state = new State(request.before(), request.sessionId(), cadence, pending instanceof Obj found ? Optional.of(found) : Optional.empty(),
                    terminal, retained.head().actualActionReceipts(), original);
            state.bind(request); return new Known<>(state, refs);
        } catch (IllegalArgumentException malformed) { return new Unavailable<>("actual Feast state rejected: " + malformed.getMessage()); }
    }
    @Override public Read<Planner> planner(PlanningRequest request) {
        Read<ActivityPacket> read = activity(ActivityQuery.DIAGNOSTIC, request, new Obj(Map.of()));
        if (read instanceof Unavailable<ActivityPacket> unavailable) return new Unavailable<>(unavailable.reason());
        Known<ActivityPacket> known = (Known<ActivityPacket>) read;
        try { return new Known<>(decodePlanner(request, envelope(known.value().result(), "activity_planner_diag")), known.originals()); }
        catch (IllegalArgumentException invalid) { return new Unavailable<>("actual Feast diagnostic rejected: " + invalid.getMessage()); }
    }
    @Override public Read<Hosted> hosted(PlanningRequest request) {
        Read<ActivityPacket> read = activity(ActivityQuery.HOSTED, request, new Obj(Map.of()));
        if (read instanceof Unavailable<ActivityPacket> unavailable) return new Unavailable<>(unavailable.reason());
        Known<ActivityPacket> known = (Known<ActivityPacket>) read;
        try {
            Obj payload = envelope(known.value().result(), "activity_feast_hosted_post");
            bindPayload(request, payload, "activity-feast-hosted-post-private-read-v1");
            Set<String> required = Set.of("schema", "snapshot_revision", "date_raw", "actor_character_id", "balances", "hosted_activities", "read_only", "advertised");
            require(payload.members().keySet().containsAll(required), "hosted post is missing fields");
            var extras = new java.util.HashSet<>(payload.members().keySet()); extras.removeAll(required);
            require(Set.of("outcome_values", "native_terminal_observations", "native_completion_effect_counter_observations").containsAll(extras), "unknown hosted post field");
            require(bool(payload.get("read_only"), "hosted read_only") && !bool(payload.get("advertised"), "hosted advertised"), "hosted query flags differ");
            validateBalances(payload.get("balances"));
            return new Known<>(new Hosted(request.before().frame().identity().player(), HostedFeastCodec.decode(encode(payload.get("hosted_activities"))), payload), known.originals());
        } catch (IllegalArgumentException invalid) { return new Unavailable<>("actual Feast hosted post rejected: " + invalid.getMessage()); }
    }
    @Override public Read<Obj> root(PlanningRequest request) {
        Read<FinanceReadContracts.Packet> read = query(FinanceReadContracts.Query.ROOT, request);
        if (read instanceof Unavailable<FinanceReadContracts.Packet> unavailable) return new Unavailable<>(unavailable.reason());
        Known<FinanceReadContracts.Packet> known = (Known<FinanceReadContracts.Packet>) read;
        try {
            Obj result = known.value().result(); require(new Text("available").equals(result.get("status")), "root unavailable");
            Obj root = object(result.get("campaign_root_context"), "actual current root");
            var identity = request.before().frame().identity();
            require(integer(root.get("player_character_id"), "root actor").equals(identity.player())
                    && integer(root.get("snapshot_revision"), "root native revision").equals(identity.nativeRevision())
                    && integer(root.get("date_raw"), "root date").equals(identity.dateRaw()), "Feast capital root frame drift");
            return new Known<>(root, known.originals());
        } catch (IllegalArgumentException invalid) { return new Unavailable<>("actual Feast root rejected: " + invalid.getMessage()); }
    }
    @Override public Read<OrdinaryFinanceCollector.Spending> spending(PlanningRequest request) {
        var read = finance.spending(request);
        if (read instanceof OrdinaryFinanceCollector.Unavailable<OrdinaryFinanceCollector.Spending> unavailable)
            return new Unavailable<>(unavailable.missing().reason());
        var value = ((OrdinaryFinanceCollector.Known<OrdinaryFinanceCollector.Spending>) read).value();
        return new Known<>(value, preserve(request, value.rootObservation()));
    }
    @Override public Read<OrdinaryFinanceCollector.Feast> feast(PlanningRequest request, OrdinaryFinanceCollector.Spending spending) {
        var read = finance.feast(request, spending);
        if (read instanceof OrdinaryFinanceCollector.Unavailable<OrdinaryFinanceCollector.Feast> unavailable)
            return new Unavailable<>(unavailable.missing().reason());
        var value = ((OrdinaryFinanceCollector.Known<OrdinaryFinanceCollector.Feast>) read).value();
        return new Known<>(value, preserve(request, value.inputObservation()));
    }
    @Override public Read<ActivityConfigurationModels.StageOne> stageOne(PlanningRequest request) {
        return configuration(ActivityQuery.STAGE_ONE, request, new Obj(Map.of()), "activity_stage1_option",
                payload -> ActivityConfigurationCodec.stageOne(encode(payload), configurationFrame(request)));
    }
    @Override public Read<ActivityConfigurationModels.StageTwo> stageTwo(PlanningRequest request) {
        return configuration(ActivityQuery.STAGE_TWO, request, new Obj(Map.of()), "activity_stage2_option",
                payload -> ActivityConfigurationCodec.stageTwo(encode(payload), configurationFrame(request)));
    }
    @Override public Read<ActivityConfigurationModels.Location> location(PlanningRequest request, int provinceId) {
        require(provinceId > 0, "positive int32 Feast capital required");
        Obj arguments = new Obj(Map.of()).with("candidate_province_ids", new Arr(List.of(new IntegerValue(BigInteger.valueOf(provinceId)))));
        return configuration(ActivityQuery.LOCATION, request, arguments, "activity_stage2_location",
                payload -> ActivityConfigurationCodec.location(encode(payload), configurationFrame(request), List.of(provinceId)));
    }
    private <T> Read<T> configuration(ActivityQuery query, PlanningRequest request, Obj arguments, String key,
            java.util.function.Function<Obj, T> decode) {
        Read<ActivityPacket> read = activity(query, request, arguments);
        if (read instanceof Unavailable<ActivityPacket> unavailable) return new Unavailable<>(unavailable.reason());
        Known<ActivityPacket> known = (Known<ActivityPacket>) read;
        try { return new Known<>(decode.apply(envelope(known.value().result(), key)), known.originals()); }
        catch (IllegalArgumentException invalid) { return new Unavailable<>("actual Feast configuration rejected: " + invalid.getMessage()); }
    }
    private Read<ActivityPacket> activity(ActivityQuery query, PlanningRequest request, Obj arguments) {
        Read<ActivityPacket> read = Objects.requireNonNull(activities.read(query, request, arguments));
        if (read instanceof Unavailable<ActivityPacket> unavailable) return unavailable;
        Known<ActivityPacket> known = (Known<ActivityPacket>) read;
        var receipt = known.value().receipt();
        // The payload must be the actual complete native result token, not a descriptor or a reconstructed packet.
        require(receipt.original().originalResultToken().isPresent()
                && object(parse(receipt.original().originalResultToken().orElseThrow().bytes()), "native Activity result").equals(known.value().result()),
                "Activity packet does not preserve its original native result");
        List<ExactRef> refs = new ArrayList<>(known.originals()); refs.addAll(preserve(request, receipt));
        return new Known<>(known.value(), refs);
    }
    private static ActivityConfigurationModels.Frame configurationFrame(PlanningRequest request) {
        var identity = request.before().frame().identity();
        return new ActivityConfigurationModels.Frame(identity.nativeRevision(), identity.dateRaw(), identity.player());
    }
    static Obj stageArguments(PlanningRequest request) {
        var identity = request.before().frame().identity();
        return new Obj(Map.of()).with("expected_date_raw", new IntegerValue(identity.dateRaw()))
                .with("expected_actor_character_id", new IntegerValue(identity.player()))
                .with("expected_activity_key", new Text("activity_feast")).with("expected_option_key", new Text("feast_type_generic"));
    }
    private Read<FinanceReadContracts.Packet> query(FinanceReadContracts.Query query, PlanningRequest request) {
        var read = finance.query(query, request);
        if (read instanceof OrdinaryFinanceCollector.Unavailable<FinanceReadContracts.Packet> unavailable) return new Unavailable<>(unavailable.missing().reason());
        var value = ((OrdinaryFinanceCollector.Known<FinanceReadContracts.Packet>) read).value();
        return new Known<>(value, preserve(request, value));
    }
    private List<ExactRef> preserve(PlanningRequest request, FinanceReadContracts.Packet packet) {
        return preserve(request, packet.receipt());
    }
    private List<ExactRef> preserve(PlanningRequest request, PlanningReadReceipt receipt) {
        require(receipt.request().before().equals(request.before()) && receipt.request().source().equals(request.source())
                && receipt.request().sessionId().equals(request.sessionId()) && receipt.original().nativeOk()
                && receipt.original().originalResultToken().isPresent(), "Feast read receipt identity drift");
        for (var guard : List.of(receipt.before(), receipt.after())) require(guard.binding().observed().equals(request.before())
                && guard.binding().source().equals(request.source()) && guard.binding().sessionId().equals(request.sessionId())
                && guard.paused() && guard.mapReady() && guard.playerAlive(), "Feast read lost its complete paused frame");
        require(receipt.before().originalBindingSha256().equals(receipt.after().originalBindingSha256()), "Feast semantic binding drift");
        try {
            ExactRef retained = borrowed.isPresent()
                    ? borrowed.orElseThrow().use(request, session -> archive.inSession(session, bound -> bound.preserve(receipt.original())))
                    : archive.preserve(receipt.original());
            return List.of(retained);
        } catch (java.io.IOException failure) { throw new IllegalArgumentException("same-writer Feast archive unavailable", failure); }
    }
    private static Obj envelope(Obj envelope, String key) {
        var expected = new java.util.HashSet<>(ENVELOPE); expected.add(key);
        require(envelope.members().keySet().equals(expected) && new Text("available").equals(envelope.get("status"))
                && new Bool(true).equals(envelope.get("accepted")) && new Bool(true).equals(envelope.get("private_build"))
                && new Bool(true).equals(envelope.get("read_only")) && new Bool(false).equals(envelope.get("advertised"))
                && new Text("native-headless").equals(envelope.get("backend_id")), "Feast envelope differs");
        return object(envelope.get(key), "Feast native payload");
    }
    static Planner decodePlanner(PlanningRequest request, Obj payload) {
        var frame = request.before().frame().identity();
        var decoded = org.xar.ck3.control.governance.activity.ActivityPlannerDiagnostic.decode(encode(payload),
                new org.xar.ck3.control.governance.activity.ActivityPlannerDiagnostic.Frame(frame.nativeRevision(), frame.dateRaw(), frame.player()));
        return new Planner(decoded.kind(), object(parse(decoded.original().bytes()), "original diagnostic"));
    }
    private static void bindPayload(PlanningRequest request, Obj payload, String schema) {
        var identity = request.before().frame().identity(); require(new Text(schema).equals(payload.get("schema"))
                && integer(payload.get("snapshot_revision"), "native revision").equals(identity.nativeRevision())
                && integer(payload.get("date_raw"), "date").equals(identity.dateRaw())
                && integer(payload.get("actor_character_id"), "actor").equals(identity.player()), "Feast payload source frame drift");
    }
    private static Optional<Terminal> retainedTerminal(Value resolved) {
        if (!(resolved instanceof Obj receipt) || !(receipt.get("lifecycle") instanceof Obj lifecycle)) return Optional.empty();
        if (!new Bool(true).equals(lifecycle.get("terminal_observed"))) return Optional.empty();
        BigInteger activity = integer(receipt.get("activity_id"), "retained Feast activity"), actor = integer(receipt.get("actor_character_id"), "retained Feast actor");
        require(integer(lifecycle.get("activity_id"), "terminal activity").equals(activity)
                && integer(lifecycle.get("actor_character_id"), "terminal actor").equals(actor)
                && new Text("activity_feast").equals(lifecycle.get("activity_type_key")), "retained Feast terminal identity differs");
        return Optional.of(new Terminal(activity, actor));
    }
    private static void validateBalances(Value value) {
        Obj balances = object(value, "Feast balances"); require(balances.members().keySet().equals(Set.of("gold", "treasury", "piety", "barter_goods")), "four Feast balances required");
        balances.members().forEach((key, raw) -> {
            Obj balance = object(raw, "Feast balance"); require(balance.members().keySet().equals(Set.of("available", "raw")), "Feast balance fields differ");
            if (bool(balance.get("available"), "balance availability")) {
                BigInteger amount = integer(balance.get("raw"), "balance raw"); require(amount.bitLength() <= 63, "balance outside signed64");
            } else require(balance.get("raw") == Nil.INSTANCE, "unavailable balance needs explicit null");
        });
    }
}
