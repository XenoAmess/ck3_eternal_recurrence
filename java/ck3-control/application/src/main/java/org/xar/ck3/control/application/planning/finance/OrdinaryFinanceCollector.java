package org.xar.ck3.control.application.planning.finance;

import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.math.BigInteger;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.finance.feastbudget.FeastBudgetCodec;
import org.xar.ck3.control.finance.feastbudget.FeastBudgetPolicy;
import org.xar.ck3.control.finance.feastvalue.FeastValueCodec;
import org.xar.ck3.control.finance.feastvalue.FeastStage5ValuePolicy;
import org.xar.ck3.control.wave2.finance.factioncandidate.FactionCandidateCodec;
import org.xar.ck3.control.wave2.finance.factioncandidate.FactionCandidatePolicy;
import org.xar.ck3.control.wave2.finance.factionalerts.FactionAlertsBoundary;
import org.xar.ck3.control.wave2.finance.factionalerts.FactionAlertModel;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashCodec;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashModel;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashPolicy;
import org.xar.ck3.control.finance.factiongift.FactionGiftChoice;
import org.xar.ck3.control.finance.factiongift.FactionGiftPolicy;
import org.xar.ck3.control.warbudget.OrdinaryWarPriority;
import org.xar.ck3.control.wave2.finance.rawcash.RawCashCodec;
import org.xar.ck3.control.wave2.finance.holyloan.LoanFinancingCodec;
import org.xar.ck3.control.wave2.planning.warcashprovenance.EmergencyFinancingAssessmentCodec;
import org.xar.ck3.control.wave2.planning.warcashprovenance.FinancingGapCodec;
import org.xar.ck3.control.wave2.finance.factionalerts.FactionThreatAdmission;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;

/** Actual synchronous reads through the sole registered endpoint. No world submit or writer. */
public final class OrdinaryFinanceCollector {
    public record Missing(String reason) { public Missing { org.xar.ck3.control.contracts.StrictJson.text(reason); } }
    public sealed interface Read<T> permits Known, Unavailable { }
    public record Known<T>(T value) implements Read<T> { public Known { Objects.requireNonNull(value); } }
    public record Unavailable<T>(Missing missing) implements Read<T> { public Unavailable { Objects.requireNonNull(missing); } }
    public record Current(Obj root, FeastBudgetPolicy.Observed spending, Obj spendingJson,
            NativeMercenaryMarket.Observation market, OrdinaryWarPriority.Observation priority,
            FinanceStatePort.Snapshot state, List<PlanningReadReceipt> originalReads) {
        public Current { Objects.requireNonNull(root); Objects.requireNonNull(spending); Objects.requireNonNull(spendingJson);
            Objects.requireNonNull(market); Objects.requireNonNull(priority); Objects.requireNonNull(state); originalReads=List.copyOf(originalReads); }
    }
    public record Spending(Obj root, FeastBudgetPolicy.Observed spending, Obj spendingJson,
            FinanceStatePort.Snapshot state, FinanceReadContracts.Packet rootObservation) {
        public Spending { Objects.requireNonNull(root); Objects.requireNonNull(spending); Objects.requireNonNull(spendingJson);
            Objects.requireNonNull(state); Objects.requireNonNull(rootObservation); }
    }
    public record Cash(RawCashCodec.NormalizedCurrentCash normalized, FinanceReadContracts.Packet original) {
        public Cash { Objects.requireNonNull(normalized); Objects.requireNonNull(original); }
    }
    /** An original CASH read joined to its complete planning frame, never a received-funds or submit proof. */
    public static final class LoanObservation {
        private final Obj request;
        private final LoanFinancingCodec.LoanInput input;
        private final FinanceReadContracts.Packet original;
        private LoanObservation(Obj request, LoanFinancingCodec.LoanInput input, FinanceReadContracts.Packet original) {
            this.request = request; this.input = input; this.original = original;
        }
        public Obj request() { return request; }
        public LoanFinancingCodec.LoanInput input() { return input; }
        public FinanceReadContracts.Packet original() { return original; }
    }
    public record Gift(FactionGiftChoice.Selected selected, Obj candidate, Obj nativeAlert,
            GiftWarCashModel.Decision cash, FinanceStatePort.Checkpoint checkpoint, BigInteger minimumGoldReserveRaw,
            List<PlanningReadReceipt> originalReads) {
        public Gift { originalReads=List.copyOf(originalReads); }
    }
    public record Feast(Obj inputs, FeastStage5ValuePolicy.Assessment value, FinanceReadContracts.Packet inputObservation) {
        public Feast { Objects.requireNonNull(inputs); Objects.requireNonNull(value); Objects.requireNonNull(inputObservation); }
    }
    private final FinanceReadContracts definitions; private final PlanningReadPort reads; private final FinanceStatePort state;
    private final Optional<java.util.function.Supplier<Session>> borrowed;
    public OrdinaryFinanceCollector(FinanceReadContracts definitions, PlanningReadPort reads, FinanceStatePort state) {
        this(definitions, reads, state, Optional.empty());
    }
    /** Root supplies its current held writer at read time, never an installation-time Session. */
    public OrdinaryFinanceCollector(FinanceReadContracts definitions, PlanningReadPort reads, FinanceStatePort state,
            java.util.function.Supplier<Session> currentSession) {
        this(definitions, reads, state, Optional.of(Objects.requireNonNull(currentSession)));
    }
    private OrdinaryFinanceCollector(FinanceReadContracts definitions, PlanningReadPort reads, FinanceStatePort state,
            Optional<java.util.function.Supplier<Session>> borrowed) {
        this.definitions = Objects.requireNonNull(definitions); this.reads = Objects.requireNonNull(reads); this.state = Objects.requireNonNull(state);
        this.borrowed = Objects.requireNonNull(borrowed);
    }
    private Optional<Session> borrowedSession() {
        return borrowed.map(source -> Objects.requireNonNull(source.get(),"actual finance writer Session is not held"));
    }
    private OrdinaryFinanceCollector borrowing(Session session) {
        Objects.requireNonNull(session);
        var current=borrowedSession();
        require(current.isEmpty() || current.orElseThrow() == session, "finance collector cannot replace its borrowed writer");
        return new OrdinaryFinanceCollector(definitions, reads, state, Optional.of(() -> session));
    }
    public Read<FinanceReadContracts.Packet> query(FinanceReadContracts.Query query, PlanningRequest request) {
        var session=borrowedSession();
        PlanningReadResult<FinanceReadContracts.Packet> value = session.isPresent()
                ? definitions.read(session.orElseThrow(), query, reads, request) : definitions.read(query, reads, request);
        if (value instanceof PlanningReadResult.Known<FinanceReadContracts.Packet> known) return new Known<>(known.value());
        return missing("registered current Native read unavailable: " + query.name() + "; reason: " + ((PlanningReadResult.Unavailable<?>) value).reason());
    }
    public FinanceStatePort.Result state(PlanningRequest request) {
        var session=borrowedSession();
        return session.isPresent() ? state.read(session.orElseThrow(), request) : state.read(request);
    }
    public FinanceStatePort.Result state(Session session, PlanningRequest request) { return borrowing(session).state(request); }
    public Read<FinanceReadContracts.Packet> query(Session session, FinanceReadContracts.Query query, PlanningRequest request) { return borrowing(session).query(query, request); }
    public Read<Spending> spending(Session session, PlanningRequest request) { return borrowing(session).spending(request); }
    public Read<Current> current(Session session, PlanningRequest request) { return borrowing(session).current(request); }
    public Read<Cash> cash(Session session, PlanningRequest request) { return borrowing(session).cash(request); }
    public Read<LoanObservation> loan(Session session, PlanningRequest request) { return borrowing(session).loan(request); }
    public Read<Gift> gift(Session session, PlanningRequest request, Current current) { return borrowing(session).gift(request, current); }
    public Read<Gift> gift(Session session, PlanningRequest request, Current current,BigInteger minimum) { return borrowing(session).gift(request,current,minimum); }
    public Read<Feast> feast(Session session, PlanningRequest request, Spending current) { return borrowing(session).feast(request, current); }
    /** Peaceful budget consumers need no unrelated mercenary query. */
    public Read<Spending> spending(PlanningRequest request) {
        FinanceStatePort.Result retained = state(request);
        if (!(retained instanceof FinanceStatePort.Known known)) return missing(((FinanceStatePort.Missing) retained).reason());
        if (!known.snapshot().spendingLedgersKnownClear()) return missing("original spending bodies, including both child marriage producers, are missing or not explicitly clear");
        Read<FinanceReadContracts.Packet> rootRead = query(FinanceReadContracts.Query.ROOT, request);
        if (!(rootRead instanceof Known<FinanceReadContracts.Packet> rootKnown)) return missing("current campaign root unavailable");
        try {
            Obj envelope = rootKnown.value().result(); require(new Text("available").equals(envelope.get("status")), "current root status unavailable");
            Obj root = object(envelope.get("campaign_root_context"), "actual current campaign root");
            var frame = request.before().frame().identity();
            require(new IntegerValue(frame.player()).equals(root.get("player_character_id"))
                    && new IntegerValue(frame.nativeRevision()).equals(root.get("snapshot_revision"))
                    && new IntegerValue(frame.dateRaw()).equals(root.get("date_raw")), "current root actor/date/revision drift");
            FeastBudgetPolicy.Result budget = budget(request, known.snapshot(), root);
            if (!(budget instanceof FeastBudgetPolicy.Observed observed)) return missing("actual exclusive spending budget unavailable");
            return new Known<>(new Spending(root, observed, object(parse(FeastBudgetCodec.encode(observed)), "budget"),
                    known.snapshot(), rootKnown.value()));
        } catch (IllegalArgumentException invalid) { return missing("current spending observation rejected: " + invalid.getMessage()); }
    }
    public Read<Current> current(PlanningRequest request) {
        Read<Spending> budget = spending(request);
        if (!(budget instanceof Known<Spending> known)) return missing(((Unavailable<Spending>) budget).missing().reason());
        try {
            Spending actual = known.value();
            Read<FinanceReadContracts.Packet> marketRead = query(FinanceReadContracts.Query.MERCENARIES, request);
            if (!(marketRead instanceof Known<FinanceReadContracts.Packet> marketKnown)) return missing("current native mercenary market unavailable");
            NativeMercenaryMarket.Observation market = NativeMercenaryMarket.decode(marketKnown.value(), request);
            OrdinaryWarPriority.Observation priority = OrdinaryWarPriority.observe(new OrdinaryWarPriority.Input(
                    org.xar.ck3.control.application.driver.DriverJson.encode(request.observations().snapshot()),org.xar.ck3.control.application.driver.DriverJson.encode(actual.root())));
            return new Known<>(new Current(actual.root(), actual.spending(), actual.spendingJson(), market, priority, actual.state(),
                    List.of(actual.rootObservation().receipt(),marketKnown.value().receipt())));
        } catch (IllegalArgumentException invalid) { return missing("current finance observation rejected: " + invalid.getMessage()); }
    }
    /** Optional loan observation uses the actual current-cash producer and shared strict codec. It grants zero future funds. */
    public Read<Cash> cash(PlanningRequest request) {
        Read<FinanceReadContracts.Packet> read = query(FinanceReadContracts.Query.CASH, request);
        if (!(read instanceof Known<FinanceReadContracts.Packet> known)) return missing("current native cash query unavailable");
        try {
            Obj original = object(known.value().result().get("war_cash_current_resources"), "native current cash");
            return new Known<>(new Cash(RawCashCodec.normalize(org.xar.ck3.control.application.driver.DriverJson.encode(original),org.xar.ck3.control.application.driver.DriverJson.encode(request.observations().snapshot())), known.value()));
        } catch (IllegalArgumentException invalid) { return missing("native cash observation rejected: " + invalid.getMessage()); }
    }
    public Read<LoanObservation> loan(PlanningRequest request) { return loanFromCash(request, cash(request)); }
    /** Reuse the construction quote's identical CASH original instead of querying a second financing source. */
    public static Read<LoanObservation> loanFromCash(PlanningRequest request, Read<Cash> cash) {
        if (!(cash instanceof Known<Cash> known)) return missing(((Unavailable<Cash>) cash).missing().reason());
        try {
            FinanceReadContracts.Packet packet = known.value().original(); PlanningReadReceipt read = packet.receipt();
            require(read.request().operation().equals(FinanceReadContracts.Query.CASH.operation())
                    && read.request().before().equals(request.before()) && read.request().source().equals(request.source())
                    && read.request().sessionId().equals(request.sessionId()) && read.request().deadline().equals(request.deadline())
                    && read.before().binding().observed().equals(request.before()) && read.after().binding().observed().equals(request.before())
                    && read.before().paused() && read.after().paused() && read.before().mapReady() && read.after().mapReady(),
                    "loan CASH original crossed the complete current planning frame");
            Obj snapshot = request.observations().snapshot(), diagnostics = object(snapshot.get("diagnostics"), "current loan diagnostics");
            BigInteger pid = integer(diagnostics.get("bridge_pid"), "current loan bridge PID");
            BigInteger generation = integer(diagnostics.get("connection_generation"), "current loan connection generation");
            require(pid.equals(BigInteger.valueOf(request.before().game().pid()))
                    && generation.equals(read.before().binding().connectionGeneration())
                    && generation.equals(read.after().binding().connectionGeneration()), "loan CASH original crossed current process or connection");
            var frame = request.before().frame(); var identity = frame.identity();
            Obj source = obj("schema", new Text("xar.ck3.planning-source-frame/v1"), "status", new Text("complete"),
                    "snapshot_id", new Text(frame.snapshotId()), "revision", new IntegerValue(frame.revision()),
                    "native_revision", new IntegerValue(identity.nativeRevision()), "date_raw", new IntegerValue(identity.dateRaw()),
                    "actor_character_id", new IntegerValue(identity.player()), "episode_run_id", new Text(frame.episodeRunId()),
                    "bridge_pid", new IntegerValue(pid), "connection_generation", new IntegerValue(generation));
            Obj original = object(packet.result().get("war_cash_current_resources"), "original current loan cash");
            for (String key : List.of("snapshot_id", "revision", "native_revision")) {
                Value expected = source.get(key), supplied = original.get("queried_" + key);
                require(supplied == null || supplied.equals(expected), "loan CASH query metadata drift: " + key);
                original = original.with("queried_" + key, expected);
            }
            Obj wrapper = obj("snapshot", snapshot, "cash_resources", original, "cash_source_frame", source);
            var input = LoanFinancingCodec.decodeAndProject(org.xar.ck3.control.application.driver.DriverJson.encode(wrapper));
            return new Known<>(new LoanObservation(wrapper, input, packet));
        } catch (IllegalArgumentException invalid) { return missing("current loan observation rejected: " + invalid.getMessage()); }
    }
    public static Obj financingGap(PlanningRequest request, Current current) {
        return obj("schema", new Text(FinancingGapCodec.REQUEST_SCHEMA), "snapshot", request.observations().snapshot(),
                "priority", object(parse(current.priority().toJson()), "actual current war priority"), "root", current.root(),
                "construction_ledger", current.state().ledger(FinanceStatePort.Domain.CONSTRUCTION).orElseThrow().original(),
                "bridge_capabilities", new Arr(request.observations().bridgeCapabilities().stream().sorted().map(Text::new).map(Value.class::cast).toList()));
    }
    /** The original assessment owns every false submission/received-funds flag and zero funding credit. */
    public static Obj financingRequest(Obj gap, Optional<LoanObservation> loan, Value pending) {
        return obj("schema", new Text(EmergencyFinancingAssessmentCodec.REQUEST_SCHEMA), "gap_request", gap,
                "loan_request", loan.<Value>map(LoanObservation::request).orElse(Nil.INSTANCE), "pending_observation", pending);
    }
    /** Only real imported explicit pending fields enter the original budget policy. */
    public static FeastBudgetPolicy.Result budget(PlanningRequest request, FinanceStatePort.Snapshot state, Obj root) {
        require(state.head().current().equals(request.before()), "budget source frame drift");
        var ledgers = new LinkedHashMap<String,Value>();
        for (var entry : List.of(new LedgerName("construction",FinanceStatePort.Domain.CONSTRUCTION),
                new LedgerName("faction_gift",FinanceStatePort.Domain.FACTION_GIFT),
                new LedgerName("first_heir_marriage",FinanceStatePort.Domain.FIRST_HEIR_MARRIAGE),
                new LedgerName("child_marriage",FinanceStatePort.Domain.CHILD_MARRIAGE)))
            ledgers.put(entry.name(), state.ledger(entry.domain()).orElseThrow(() -> new IllegalArgumentException("missing actual spending body")).original());
        var source = request.before().frame(); var f = source.identity();
        Obj inputs = obj("actor_character_id",new IntegerValue(f.player()),"snapshot_revision",new IntegerValue(f.nativeRevision()),
                "date_raw",new IntegerValue(f.dateRaw()),"post_snapshot_id",new Text(source.snapshotId()),"queried_revision",new IntegerValue(source.revision()));
        Obj wrapper = obj("schema",new Text(FeastBudgetCodec.SCHEMA),"snapshot",request.observations().snapshot(),
                "inputs",inputs,"ledgers",new Obj(ledgers),"campaign_root",root);
        return FeastBudgetPolicy.observe(FeastBudgetCodec.decode(org.xar.ck3.control.application.driver.DriverJson.encode(wrapper)));
    }
    private record LedgerName(String name,FinanceStatePort.Domain domain) { }
    public Read<Gift> gift(PlanningRequest request, Current current) { return gift(request,current,BigInteger.valueOf(10_000_000)); }
    public Read<Gift> gift(PlanningRequest request,Current current,BigInteger minimum) {
        Objects.requireNonNull(minimum);
        Read<FinanceReadContracts.Packet> read = query(FinanceReadContracts.Query.FACTION_GIFT,request);
        if (!(read instanceof Known<FinanceReadContracts.Packet> known)) return missing("private faction candidate read unavailable");
        try {
            var root = FactionCandidateCodec.decodeRootProjection(encode(current.root()));
            var evaluated = FactionCandidateCodec.evaluatePrivateCandidate(org.xar.ck3.control.application.driver.DriverJson.encode(request.observations().snapshot()),root,
                    org.xar.ck3.control.application.driver.DriverJson.encode(known.value().result()),minimum);
            if (!(evaluated instanceof FactionCandidatePolicy.Evaluated candidate)
                    || !(candidate.choice() instanceof FactionGiftChoice.Selected selected)) return missing("no complete native legal budgeted faction candidate");
            Obj candidateJson = object(parse(FactionCandidateCodec.encodeCandidateResult(evaluated)),"selected candidate");
            Read<FinanceReadContracts.Packet> alert = query(FinanceReadContracts.Query.FACTION_ALERTS,request);
            if (!(alert instanceof Known<FinanceReadContracts.Packet> alertKnown)) return missing("current stock dangerous-faction predicate unavailable");
            var f=request.before().frame().identity();
            var threat=FactionThreatAdmission.fromExistingDriverResult(encode(alertKnown.value().result()),
                    new FactionThreatAdmission.Request(new FactionAlertModel.ExpectedFrame(f.dateRaw().intValueExact(),
                            f.nativeRevision(), Optional.of(FactionAlertModel.Build.CK3_12004)),
                            f.player().intValueExact(), selected.sourceFactionId().intValueExact(),
                            selected.recipientCharacterId().intValueExact()),
                    encode(request.observations().snapshot().get("active_wars")));
            if (!(threat instanceof FactionThreatAdmission.Admitted admitted))
                return missing("selected faction lacks current actual stock danger and membership: " + ((FactionThreatAdmission.Missing) threat).reason());
            Obj candidateWire=obj("choice",object(parse(FactionGiftPolicy.encode(selected)),"gift choice"),
                    "observation",object(parse(candidate.observation().original().json()),"native gift observation"));
            var input = cashContext(request,current,GiftWarCashCodec.SCHEMA,candidateWire);
            var cash=GiftWarCashPolicy.assess(GiftWarCashCodec.decode(org.xar.ck3.control.application.driver.DriverJson.encode(input)));
            if (!cash.newGiftSpendingAllowed()) return missing("wartime gift cash retained: "+cash.reason().wire());
            var checkpoint=current.state().head().checkpoint().filter(cp->cp.episodeRunId().equals(request.before().frame().episodeRunId())
                    && cp.dateRaw().equals(f.dateRaw()));
            if (checkpoint.isEmpty()) return missing("actual same-episode same-date pre-gift checkpoint unavailable");
            var originals=new java.util.ArrayList<>(current.originalReads());originals.add(known.value().receipt());originals.add(alertKnown.value().receipt());
            return new Known<>(new Gift(selected,candidateWire,org.xar.ck3.control.application.driver.DriverJson.object(admitted.normalizedAlertJson(),RawJson.MAXIMUM_BYTES),cash,checkpoint.orElseThrow(),minimum,originals));
        } catch (IllegalArgumentException invalid) { return missing("faction inputs rejected: "+invalid.getMessage()); }
    }
    public static Obj cashContext(PlanningRequest request,Current current,String schema,Obj candidate) {
        var entries=new LinkedHashMap<String,Value>(); entries.put("schema",new Text(schema)); entries.put("snapshot",request.observations().snapshot());
        if (candidate!=null) entries.put("candidate",candidate); entries.put("root",current.root()); entries.put("spending",current.spendingJson());
        entries.put("market",current.market().original()); entries.put("market_source_frame",sourceFrame(request));
        entries.put("mercenary_ledger",current.state().ledger(FinanceStatePort.Domain.MERCENARY).orElseThrow(()->new IllegalArgumentException("actual procurement ledger missing")).original());
        return new Obj(entries);
    }
    public Read<Feast> feast(PlanningRequest request,Spending current) {
        Read<FinanceReadContracts.Packet> read=query(FinanceReadContracts.Query.FEAST_INPUTS,request);
        if (!(read instanceof Known<FinanceReadContracts.Packet> known)) return missing("actual stage5 feast inputs unavailable");
        try {
            Obj result=known.value().result(); require(new Text("available").equals(result.get("status"))
                    && new Bool(true).equals(result.get("read_only")) && new Bool(true).equals(result.get("private_build"))
                    && new Bool(false).equals(result.get("advertised")),"original feast envelope unavailable");
            Obj inputs=object(result.get("activity_feast_stage5_start_inputs"),"native feast inputs");
            var f=request.before().frame().identity();
            require(new Text("activity-feast-stage5-start-inputs-private-v1").equals(inputs.get("schema"))
                    && new IntegerValue(f.nativeRevision()).equals(inputs.get("snapshot_revision"))
                    && new IntegerValue(f.dateRaw()).equals(inputs.get("date_raw"))
                    && new IntegerValue(f.player()).equals(inputs.get("actor_character_id"))
                    && new Bool(true).equals(inputs.get("read_only")) && new Bool(false).equals(inputs.get("advertised")),"native feast input frame drift");
            require(new Bool(true).equals(inputs.get("final_can_start")) && new Bool(true).equals(inputs.get("native_guest_route_qualified")),"native final start/guest route unavailable");
            BigInteger guests=timelyGuests(inputs,f.nativeRevision(),f.dateRaw(),f.player());
            var costs=new java.util.ArrayList<Value>();var available=new java.util.ArrayList<Value>();var balances=new java.util.ArrayList<Value>();var reserved=new java.util.ArrayList<Value>();
            Obj resources=object(inputs.get("resources"),"native resource costs"), money=object(inputs.get("balances"),"native balances");
            Obj budget=object(current.spendingJson().get("budget"),"actual budget"), reserves=object(budget.get("reserved_raw"),"actual resource reservations");
            require(resources.members().keySet().equals(java.util.Set.of("gold","treasury","piety","barter_goods"))
                    && money.members().keySet().equals(resources.members().keySet()),"four native resource keys required");
            for(String key:List.of("gold","treasury","piety","barter_goods")) {
                Obj cost=object(resources.get(key),"resource cost"),balance=object(money.get(key),"resource balance");
                BigInteger index=integer(cost.get("resource_index"),"resource index");require(index.signum()>=0&&index.compareTo(BigInteger.TEN)<0,"resource index outside native vector");
                BigInteger amount=integer(cost.get("configured_cost_raw"),"configured cost");
                boolean ready=bool(balance.get("available"),"balance availability");
                costs.add(new IntegerValue(amount));available.add(new Bool(ready));
                balances.add(new IntegerValue(ready&&amount.signum()!=0?integer(balance.get("raw"),"actual balance"):BigInteger.ZERO));reserved.add(reserves.get(key));
            }
            Obj leaf=obj("activity_key",inputs.get("activity_key"),"selected_option_key",inputs.get("selected_option_key"),
                    "planning_stage",inputs.get("planning_stage"),"final_can_start",inputs.get("final_can_start"),
                    "configured_cost_raw",new Arr(costs),"balance_available",new Arr(available),"balance_raw",new Arr(balances),
                    "reserved_raw",new Arr(reserved),"expected_nonhost_guest_count",new IntegerValue(guests),
                    "peaceful_spend_allowed",budget.get("peaceful_spend_allowed"),"gold_floor_raw",budget.get("gold_floor_raw"),
                    "active_war_count",budget.get("active_war_count"),"war_cash_reserve_raw",budget.get("war_cash_reserve_raw"));
            var assessment=FeastStage5ValuePolicy.assess(FeastValueCodec.decodeRequest(encode(leaf)));
            return new Known<>(new Feast(inputs,assessment,known.value()));
        } catch (IllegalArgumentException invalid) { return missing("feast input/value rejected: "+invalid.getMessage()); }
    }
    private static BigInteger timelyGuests(Obj inputs,BigInteger revision,BigInteger date,BigInteger actor) {
        if(new Text("observed").equals(inputs.get("guest_join_status"))&&new Bool(true).equals(inputs.get("arrival_time_observed"))) {
            BigInteger all=integer(inputs.get("selected_nonhost_count"),"selected guests"),positive=integer(inputs.get("positive_join_count"),"positive guests"),timely=integer(inputs.get("timely_positive_join_count"),"timely guests");
            require(timely.signum()>0&&timely.compareTo(positive)<=0&&positive.compareTo(all)<=0&&all.compareTo(BigInteger.valueOf(128))<=0,"native selected guest counts inconsistent");return timely;
        }
        Obj route=object(inputs.get("ordinary_guest_route"),"actual ordinary guest route");
        require(new Text("observed").equals(route.get("status"))&&new Bool(true).equals(route.get("qualified")),"ordinary guest route unavailable");
        Obj candidate=object(route.get("candidate"),"native current guest candidate");
        require(new IntegerValue(revision).equals(candidate.get("snapshot_revision"))&&new IntegerValue(date).equals(candidate.get("date_raw"))
                &&new IntegerValue(actor).equals(candidate.get("actor_character_id")),"ordinary guest candidate frame drift");
        require(new Text("activity_invite_rule_close_family").equals(route.get("authored_rule_key"))
                &&new Text("observed").equals(route.get("candidate_status"))
                &&new Text("observed_active").equals(route.get("rule_status"))&&new Bool(true).equals(route.get("rule_active"))
                &&new Text("observed").equals(route.get("provenance_status"))&&new Bool(true).equals(route.get("candidate_membership"))
                &&new Bool(true).equals(candidate.get("native_filtered")),"ordinary guest native admission missing");
        BigInteger key=integer(route.get("native_key_hash"),"native rule hash"),proof=integer(route.get("provenance_key_hash"),"provenance rule hash");
        BigInteger refresh=integer(inputs.get("normal_refresh_sequence"),"actual refresh");
        BigInteger filtered=integer(route.get("filtered_rule_character_count"),"filtered count"),raw=integer(route.get("raw_rule_character_count"),"raw count");
        require(key.signum()>=0&&key.bitLength()<=32&&key.equals(proof)&&refresh.signum()>0&&refresh.bitLength()<=64
                &&refresh.equals(integer(candidate.get("normal_refresh_sequence"),"candidate refresh"))
                &&integer(route.get("provenance_refresh_sequence"),"provenance refresh").signum()>0
                &&filtered.signum()>0&&filtered.compareTo(raw)<=0&&raw.compareTo(BigInteger.valueOf(4096))<=0
                &&integer(candidate.get("character_id"),"guest identity").signum()>0
                &&!integer(candidate.get("character_id"),"guest identity").equals(actor)
                &&integer(candidate.get("planner_join_raw"),"native join score").signum()>0
                &&integer(candidate.get("travel_days"),"native travel days").signum()>=0
                &&integer(candidate.get("arrival_raw"),"native arrival").compareTo(integer(candidate.get("planned_start_raw"),"native start"))<=0
                &&text(candidate.get("source_fingerprint"),"native fingerprint").matches("0x[0-9a-f]{16}"),"ordinary guest qualification disagreed");
        return BigInteger.ONE;
    }
    public static Obj sourceFrame(PlanningRequest request) {
        return sourceFrame(request.before());
    }
    public static Obj sourceFrame(org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity before) {
        var f=Objects.requireNonNull(before).frame();return obj("played_character_id",new IntegerValue(f.identity().player()),"native_revision",new IntegerValue(f.identity().nativeRevision()),
                "date_raw",new IntegerValue(f.identity().dateRaw()),"snapshot_id",new Text(f.snapshotId()),"revision",new IntegerValue(f.revision()),"episode_run_id",new Text(f.episodeRunId()));
    }
    public static Obj obj(Object... pairs) {
        require(pairs.length%2==0,"paired JSON fields required");var values=new LinkedHashMap<String,Value>();
        for(int i=0;i<pairs.length;i+=2){require(pairs[i] instanceof String && pairs[i+1] instanceof Value,"typed JSON field/value required");
            require(values.put((String)pairs[i],(Value)pairs[i+1])==null,"duplicate field");}return new Obj(values);
    }
    private static <T> Unavailable<T> missing(String reason) { return new Unavailable<>(new Missing(reason)); }
}
