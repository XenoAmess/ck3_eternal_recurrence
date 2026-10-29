package org.xar.ck3.control.application.planning.finance;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import static org.xar.ck3.control.application.planning.finance.OrdinaryFinanceCollector.obj;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.NativeConstructionEffects;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.service.root.CanonicalFundingFixture;
import org.xar.ck3.control.wave2.planning.warcashprovenance.EmergencyFinancingAssessment;
import org.xar.ck3.control.wave3.development.wartimesequencing.*;

/** Actual writer/import/state/funding producer -> native-contract software boundary -> real construction policy/serde.
 * Seven-domain fixture registrations are source-bound unit inputs, not private Core initialization or Game qualification. */
final class ConstructionFundingProductionChainTest {
    @TempDir Path directory;
    @Test void actualClearOwnedInventoryRestoresAmpleWarBuildAndPersistsItsExactFacts() throws Exception {
        Obj corpus = threshold(); var request = request(directory.resolve("clear-source.java"), object(corpus.get("snapshot"), "original snapshot"));
        var fixture = fixture(directory.resolve("clear"), request, CanonicalFundingFixture.Variant.CLEAR);
        var actual = fixture.withSession(same -> assertInstanceOf(CanonicalFundingPending.Observed.class, fixture.service().read(same, request)));
            assertInstanceOf(EmergencyFinancingAssessment.NoPendingAction.class, actual.pending());
            assertEquals(CanonicalFundingPending.NativeFundingCoverage.COMPLETE_DEBT_LOAN_REFUND_UNQUALIFIED, actual.sourceEvidence().nativeFundingCoverage());
            assertEquals(0, actual.sourceEvidence().unreceivedFundingCreditedRaw());
            var collector = collector(fixture, request, corpus, false);
            var prepared = assertInstanceOf(OrdinaryConstructionCollector.Available.class,
                    collector.before(request, OrdinaryConstructionPolicy.selection(draft()), obj(), "new_building")).value();
            assertEquals(OrdinaryWartimeConstruction.Disposition.OPTIONAL_QUERY_ALLOWED, OrdinaryWartimeConstruction.compose(prepared.before().input()).disposition());
            var decision = assertInstanceOf(OrdinaryPolicy.Replace.class, policy(request, collector).evaluate(request, draft()));
            var command = decision.draft().command().orElseThrow();
            var evidence = ConstructionFundingEvidence.command(command);
            assertEquals(actual.sourceEvidence(), evidence);
            assertEquals(evidence, CanonicalFundingPending.decodeEvidence(CanonicalFundingPending.encodeEvidence(evidence)));
            assertEquals(request.source(), evidence.source()); assertEquals(request.sessionId(), evidence.sessionId());
            var planned = new OrdinaryWartimeConstructionCodec.ObservedRequest(encode(object(command.arguments().get("ordinary_cash_request"), "quoted request")));
            var result = OrdinaryWartimeConstruction.compose(planned.input());
            assertEquals(OrdinaryWartimeConstruction.Disposition.QUOTED_CANDIDATE, result.disposition());
            assertTrue(result.cash().newSpendAllowed()); assertEquals(BigInteger.ZERO, result.unreceivedFundingCreditedRaw());
            var clear = ConstructionLedgerCodec.decodeLedger(encode(emptyBody()));
            Obj pending = ConstructionDomainLifecycle.intent(clear, command);
            var persisted = ConstructionLedgerCodec.decodeLedger(encode(pending));
            assertEquals(command.arguments().get(ConstructionFundingEvidence.FIELD), persisted.pending().orElseThrow().original().get(ConstructionFundingEvidence.FIELD));
            assertEquals(pending, persisted.original());
            var intent=persisted.pending().orElseThrow();
            Obj budget = object(intent.original().get("construction_monthly_budget"), "persisted original monthly cash budget");
            assertEquals(new Text("xar.ck3.construction-monthly-budget.v1"), budget.get("schema"));
            assertEquals(n(23_000_000), budget.get("construction_gold_cost_raw"));
            assertEquals(intent.original().get("pre_cash_v2"), budget.get("source_cash_resources"));
            Obj scenarios = object(budget.get("scenarios"), "original current/all-raised cash scenarios");
            assertEquals(n(-200_000), object(scenarios.get("current"), "current military cash").get("net_monthly_gold_raw"));
            assertEquals(n(-500_000), object(scenarios.get("all_raised"), "all-raised military cash").get("net_monthly_gold_raw"));
            assertEquals(new Bool(false), budget.get("future_war_cost_upper_ready"));
            Obj effect=obj("status",new Text("applied"),"postcondition_verified",new Bool(true),"completion_status",new Text("in_progress"),
                    "action_request_id",new Text(intent.identity().actionRequestId()),"episode_run_id",new Text(intent.identity().episode()),"actor_character_id",new IntegerValue(intent.identity().actor()),
                    "post_proof_epoch",new IntegerValue(intent.proofEpoch().add(BigInteger.ONE)),"post_native_revision",n(4),"post_date_raw",n(53288472),"post_player_gold_raw",n(77_000_000),
                    "candidate",command.arguments().get("candidate"),"native_query_request_id",new Text("software-independent-start-vector"));
            Obj after=request.observations().snapshot().with("native_revision",n(4)).with("revision",n(4)).with("snapshot_id",new Text("native:4"));
            Obj receipt=ConstructionMaterialReducer.confirmedStart(intent,effect,after);
            assertEquals(command.arguments().get(ConstructionFundingEvidence.FIELD),receipt.get(ConstructionFundingEvidence.FIELD));
            assertEquals(budget, receipt.get("construction_monthly_budget"));
            assertEquals(intent.original().get("pre_cash_v2"), receipt.get("pre_cash_v2"));
            Obj applied=emptyBody().with("applied",receipt);
            assertEquals(applied,ConstructionLedgerCodec.decodeLedger(encode(applied)).original());
            fixture.withSession(same -> { policy(request, collector).revalidateConstruction(same, command, request); return null; });
            Obj malformed = object(command.arguments().get(ConstructionFundingEvidence.FIELD), "actual facts").with("unreceived_funding_credited_raw", n(1));
            assertThrows(IllegalArgumentException.class, () -> ConstructionFundingEvidence.decode(malformed));
            var removed = new java.util.LinkedHashMap<String,Value>(malformed.members()); removed.remove("bodies");
            assertThrows(IllegalArgumentException.class, () -> ConstructionFundingEvidence.decode(new Obj(removed)));
    }
    @Test void missingActualBodyPendingCommitmentLowWalletOrMissingMarketOnlyDeferOptionalConstruction() throws Exception {
        Obj corpus = threshold();
        for (var variant : List.of(CanonicalFundingFixture.Variant.MISSING_MERCENARY, CanonicalFundingFixture.Variant.PENDING_MERCENARY)) {
            var request = request(directory.resolve(variant+"-source.java"), object(corpus.get("snapshot"), "original snapshot"));
            var fixture = fixture(directory.resolve(variant.name()), request, variant);
            fixture.withSession(same -> {
                var result = fixture.service().read(same, request);
                if (variant == CanonicalFundingFixture.Variant.MISSING_MERCENARY) assertInstanceOf(CanonicalFundingPending.Unavailable.class, result);
                else assertInstanceOf(EmergencyFinancingAssessment.PendingUnavailable.class, assertInstanceOf(CanonicalFundingPending.Observed.class, result).pending());
                return null;
            });
            var decision = policy(request, collector(fixture, request, corpus, false)).evaluate(request, draft());
            assertInstanceOf(OrdinaryPolicy.Defer.class, decision); assertEquals("current_life_loop", draft().phase());
        }
        for (boolean missingMarket : List.of(false, true)) {
            Obj snapshot = object(corpus.get("snapshot"), "snapshot");
            if (!missingMarket) snapshot = snapshot.with("played_character_gold", obj("raw", n(69_999_999), "scale", n(100_000)));
            var request = request(directory.resolve("gap-"+missingMarket+"-source.java"), snapshot);
            var fixture = fixture(directory.resolve("gap-"+missingMarket), request, CanonicalFundingFixture.Variant.CLEAR);
            var result = policy(request, collector(fixture, request, corpus, missingMarket)).evaluate(request, draft());
            assertInstanceOf(OrdinaryPolicy.Defer.class, result);
        }
    }
    @Test void mutatedUnknownDataCannotBorrowThePrivateLiveClearObservation() throws Exception {
        Obj corpus=threshold();var request=request(directory.resolve("unknown-source.java"),object(corpus.get("snapshot"),"snapshot"));
        var fixture=fixture(directory.resolve("unknown-data"),request,CanonicalFundingFixture.Variant.CLEAR);
        var actual=fixture.withSession(same->assertInstanceOf(CanonicalFundingPending.Observed.class,fixture.service().read(same,request)));
        var source=actual.sourceEvidence();
        // Deliberately mutated DATA, not an actual archived receipt or a newly minted Observed.
        var unknown=new CanonicalFundingPending.ActionFact("mutated-unknown-data",OrdinaryFinancePolicies.MERCENARY,"b".repeat(64),CanonicalFundingPending.Phase.UNKNOWN,source.canonicalHead());
        var changed=new CanonicalFundingPending.SourceEvidence(source.current(),source.source(),source.sessionId(),source.canonicalHead(),source.ledgerSequence(),source.headSha256(),source.bodies(),source.installed(),source.families(),1,"b".repeat(64),List.of(unknown));
        var decoded=CanonicalFundingPending.decodeEvidence(CanonicalFundingPending.encodeEvidence(changed));
        assertEquals(changed,decoded);assertEquals(CanonicalFundingPending.Phase.UNKNOWN,decoded.unresolvedActions().getFirst().phase());
        assertInstanceOf(EmergencyFinancingAssessment.PendingUnavailable.class,CanonicalFundingPending.pending(decoded));
        assertThrows(IllegalArgumentException.class,()->ConstructionFundingEvidence.decode(CanonicalFundingPending.evidenceJson(decoded)));
        assertInstanceOf(EmergencyFinancingAssessment.NoPendingAction.class,actual.pending());
        assertEquals(0,decoded.unreceivedFundingCreditedRaw());
    }
    @Test void actualPreCoreRegistrationOwningBodyCodecAndFinanceBindingShareTheExistingBodyBoundary() throws Exception {
        Obj corpus=threshold();var request=request(directory.resolve("boundary-source.java"),object(corpus.get("snapshot"),"snapshot"));
        var source=request.source().sourceRef();var prepared=ConstructionDomainLifecycle.prepare(List.of(source),source);
        assertEquals(ContinuityJson.DOMAIN_MAX_BYTES,prepared.registration().maximumBodyBytes());
        assertEquals(ConstructionLedgerCodec.MAX_BYTES,prepared.registration().maximumBodyBytes());
        Obj empty=emptyBody().with("original_extension",new Text(""));
        int room=prepared.registration().maximumBodyBytes()-encode(empty).length;
        byte[] body=encode(empty.with("original_extension",new Text("x".repeat(room))));
        assertEquals(ContinuityJson.DOMAIN_MAX_BYTES,body.length);
        assertEquals(body.length,encode(ConstructionLedgerCodec.decodeLedger(body).original()).length);
        var reader=new FinanceStatePort.ReaderBinding(FinanceStatePort.Domain.CONSTRUCTION,source,original->ConstructionLedgerCodec.decodeLedger(original.bytes()).pending().isPresent()?FinanceStatePort.Pending.PENDING:FinanceStatePort.Pending.CLEAR);
        var actual=prepared.registration();
        var binding=new CanonicalFinanceStateSource.Binding(reader,actual.slot(),actual.contractSchema(),actual.maximumBodyBytes(),actual.producerSources());
        var document=new FinanceStatePort.Document(FinanceStatePort.Domain.CONSTRUCTION,new ExactRef(directory.resolve("boundary-body-data.json").toString(),body.length,ActionCodec.sha256(body)),body);
        assertEquals(FinanceStatePort.Pending.CLEAR,binding.decoder().reader().decode(document));
        assertEquals(org.xar.ck3.control.continuity.ContinuityJson.DOCUMENT_MAX_BYTES,ConstructionDomainLifecycle.MAX_INPUT_BYTES);
        byte[] oversized=encode(empty.with("original_extension",new Text("x".repeat(room+1))));
        assertThrows(IllegalArgumentException.class,()->ConstructionLedgerCodec.decodeLedger(oversized));
        assertThrows(IllegalArgumentException.class,()->ContinuityJson.parseObject(oversized,ContinuityJson.DOMAIN_MAX_BYTES));
    }
    private CanonicalFundingFixture fixture(Path root, PlanningRequest request, CanonicalFundingFixture.Variant variant) throws IOException {
        Files.createDirectories(root); Path producer = root.resolve("construction-software-source.java");
        Files.writeString(producer, "unit source binding to the actual ConstructionLedgerCodec; no private Core authority");
        ExactRef source = exact(producer); byte[] body=encode(emptyBody());
        var reader = new FinanceStatePort.ReaderBinding(FinanceStatePort.Domain.CONSTRUCTION, source,
                original -> ConstructionLedgerCodec.decodeLedger(original.bytes()).pending().isPresent() ? FinanceStatePort.Pending.PENDING : FinanceStatePort.Pending.CLEAR);
        var registration = new DomainBodies.Registration(DomainBodies.Slot.CONSTRUCTION, ConstructionLedgerCodec.SCHEMA,
                ContinuityJson.DOMAIN_MAX_BYTES, List.of(source), (head, previous, submitted, actual) -> {
                    if (previous.isPresent() || !java.util.Arrays.equals(body, actual) || !java.util.Arrays.equals(body, submitted.producerInput()))
                        throw new IllegalArgumentException("exact fixture original construction producer required");
                    ConstructionLedgerCodec.validateLedger(actual); return ActionCodec.sha256(actual);
                });
        return CanonicalFundingFixture.create(root, request, variant, Optional.of(new CanonicalFundingFixture.ConstructionOverride(reader, registration, body)));
    }
    private OrdinaryConstructionCollector collector(CanonicalFundingFixture fixture, PlanningRequest request, Obj corpus, boolean missingMarket) {
        var definitions = new FinanceReadContracts(query -> new FinanceReadContracts.Registration(request.source().sourceRef(),
                new FinanceReadContracts.Permission(Optional.empty(), "construction-chain-software:"+query.name(),
                        ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE, ReadContract.WireProfile.EXECUTE_STEP)));
        var queries = new NativeQueries(request, corpus, missingMarket);
        var finance = new OrdinaryFinanceCollector(definitions, queries, fixture.state());
        return new OrdinaryConstructionCollector(finance, new OrdinaryConstructionCollector.EndingSnapshot() {
            @Override public Obj readCurrent(PlanningRequest current) { assertEquals(request, current); return current.observations().snapshot(); }
            @Override public Obj readCurrent(ContinuityStorePort.Session same, PlanningRequest current) { return readCurrent(current); }
        }, new OrdinaryConstructionCollector.FinancingPending() {
            @Override public CanonicalFundingPending.Result readUnderOriginalWriterLock(PlanningRequest current) {
                try { return fixture.withSession(same -> fixture.service().read(same, current)); }
                catch (IOException failure) { throw new java.io.UncheckedIOException(failure); }
            }
            @Override public CanonicalFundingPending.Result readUnderOriginalWriterLock(ContinuityStorePort.Session same, PlanningRequest current) {
                try { return fixture.service().read(same, current); }
                catch (IOException failure) { throw new java.io.UncheckedIOException(failure); }
            }
        });
    }
    private static OrdinaryConstructionPolicy policy(PlanningRequest request, OrdinaryConstructionCollector collector) {
        return new OrdinaryConstructionPolicy(request.source().sourceRef(), collector,
                (original, arguments) -> Optional.of(NativeConstructionEffects.expected(original.before(), original.source(), arguments)),
                (original, draft, ledger, receipt, reason) -> { throw new AssertionError("clear-body test cannot consume a material completion"); });
    }
    private PlanningRequest request(Path sourceFile, Obj original) throws IOException {
        Files.writeString(sourceFile, "construction funding production-chain software input v1"); var sourceRef = exact(sourceFile);
        Obj diagnostic = object(original.get("diagnostics"), "original diagnostic").with("bridge_pid", n(42)).with("bridge_creation_date", new Text("retained-software-bridge"));
        Obj snapshot = original.with("diagnostics", diagnostic);
        var source = new G2Source("construction-funding-software-machine", "2026-10-24T00:00:00Z", "1.20.0.4", sourceRef);
        var frame = new ProposalLifecycle.ObservationIdentity(source.machineId(), new GameGeneration(99, new PythonOnlyUInt64(new BigInteger("133000000000000099"))),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(integer(object(snapshot.get("played_character"), "player").get("character_id"), "actor"),
                        integer(snapshot.get("native_revision"), "native revision"), integer(snapshot.get("date_raw"), "date")), text(snapshot.get("snapshot_id"), "snapshot"),
                        integer(snapshot.get("revision"), "revision"), text(snapshot.get("episode_run_id"), "episode")), 1);
        return new PlanningRequest(frame, source, "construction-funding-software-session", Instant.now().plusSeconds(120),
                new PlanningObservation(snapshot, List.of(), Set.of(OrdinaryConstructionPolicy.OPERATION), Set.of(), Optional.empty(), List.of(), Optional.empty(), Optional.empty(), false));
    }
    private static OrdinaryPolicy.Draft draft() { return new OrdinaryPolicy.Draft("retained-war-clock", "current_life_loop", "original complete ordinary decision",
            OrdinaryPolicy.Kind.ORDINARY, Optional.empty(), OrdinaryPolicy.Purpose.DATE_ADVANCE, Optional.empty(), obj("selected_step", new Text("life-advance"))); }
    private static Obj emptyBody() { return obj("schema", new Text(ConstructionLedgerCodec.SCHEMA), "pending", Nil.INSTANCE, "applied", Nil.INSTANCE, "applied_prior", new Arr(List.of())); }
    private static ExactRef exact(Path path) throws IOException { byte[] raw = Files.readAllBytes(path); return new ExactRef(path.toAbsolutePath().normalize().toString(), raw.length, ActionCodec.sha256(raw)); }
    private static IntegerValue n(long value) { return new IntegerValue(BigInteger.valueOf(value)); }
    private static Obj threshold() throws IOException {
        try (var input = ConstructionFundingProductionChainTest.class.getResourceAsStream("/m4producer/wartime-original02.json.gz")) {
            if (input == null) throw new IOException("required unchanged original wartime31 corpus missing; NOT_RUN is not PASS");
            byte[] compressed = input.readNBytes(6379+1);
            if (compressed.length != 6379 || !ActionCodec.sha256(compressed).equals("4b3cf840085e5f3d53e290b4ea862e1357a3341a55180ff3670675caa5f6a585")) throw new IOException("original wartime31 corpus changed");
            try (var zip = new GZIPInputStream(new java.io.ByteArrayInputStream(compressed))) {
                Obj root = object(parse(zip.readNBytes(524289)), "actual original wartime corpus");
                for (Value value : array(root.get("cases"), "original cases")) { Obj row = object(value, "original case");
                    if (new Text("exact_ample_threshold").equals(row.get("name"))) return object(row.get("request"), "unchanged original ample case"); }
                throw new IOException("original exact ample threshold case missing");
            }
        }
    }
    /** Software native packets pass the actual installed contracts. Historical guard DATA is not a managed physical lease. */
    private final class NativeQueries implements PlanningReadPort {
        private final PlanningRequest planning; private final Obj corpus; private final boolean missingMarket; private long sequence;
        private NativeQueries(PlanningRequest planning, Obj corpus, boolean missingMarket) { this.planning=planning;this.corpus=corpus;this.missingMarket=missingMarket; }
        @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract, PlanningReadRequest original) {
            if (missingMarket && original.operation().equals(FinanceReadContracts.Query.MERCENARIES.operation())) return new PlanningReadResult.Unavailable<>("software native market unavailable", Optional.empty());
            String id = "software-construction-read-"+(++sequence); Obj result = result(original, sequence);
            Obj frame = obj("type",new Text("command_result"),"protocol_version",n(1),"request_id",new Text(id),"ok",new Bool(true),"result",result);
            byte[] raw=encode(frame),packet=ByteBuffer.allocate(raw.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(raw.length).put(raw).array();
            var ack=new NativeActionPort.AckReceived(id,true,Optional.of(new RawJson(encode(result))),new RawJson(raw),packet);
            var binding=new GuardEvidence(original.before(),original.source(),original.sessionId(),BigInteger.ONE,original.operation(),planning.source().sourceRef(),planning.source().sourceRef(),"construction-software-read",Instant.now(),original.deadline());
            var guard=new PlanningReadGuard(binding,true,true,true,"a".repeat(64));
            var receipt=new PlanningReadReceipt(original,contract.contractId(),id,guard,guard,ack);
            T decoded=contract.decode(receipt);
            var ref=new ExactRef(directory.resolve(id+".json").toString(),raw.length,ActionCodec.sha256(raw));
            return new PlanningReadResult.Known<>(decoded,receipt,ref);
        }
        @Override public <T> PlanningReadResult<T> read(ContinuityStorePort.Session same, ReadContract<T> contract, PlanningReadRequest original) { return read(contract,original); }
        private Obj result(PlanningReadRequest request,long epoch) {
            Obj base=obj("step",new Text(request.operation().value()),"accepted",new Bool(true));
            if(request.operation().equals(FinanceReadContracts.Query.ROOT.operation())) return rootResult(planning);
            if(request.operation().equals(FinanceReadContracts.Query.MERCENARIES.operation())) return base.with("snapshot_revision",n(3)).with("player_mercenary_context",corpus.get("market"));
            if(request.operation().equals(FinanceReadContracts.Query.CASH.operation())) return base.with("war_cash_current_resources",cash(planning));
            if(!request.operation().equals(FinanceReadContracts.Query.CONSTRUCTION.operation())) throw new AssertionError("unrequested software query: "+request.operation());
            Obj idle=obj("barony_title_id",n(2103),"province_id",n(2635),"active",new Bool(false));
            var costs=new java.util.ArrayList<Value>();costs.add(n(23_000_000));for(int i=1;i<10;i++)costs.add(n(0));
            Obj sample=obj("barony_title_id",n(2103),"province_id",n(2635),"building_type_id",n(11),"slot_index",n(0),"building_key",new Text("farm_estates_01"),"native_cost_observed",new Bool(true),"cost_raw_native",new Arr(costs));
            Obj world=obj("status",new Text("source_available"),"snapshot_revision",n(3),"date_raw",n(53288472),"player_character_id",n(29829),
                    "native_final_legality_evaluated",new Bool(true),"native_cost_evaluated",new Bool(true),"player_gold_raw",object(planning.observations().snapshot().get("played_character_gold"),"current wallet").get("raw"),
                    "active_constructions",new Arr(List.of(idle)),"completed_buildings_observed",new Bool(true),"completed_buildings",new Arr(List.of()),"positive_income_coverage_complete",new Bool(true),"legal_samples",new Arr(List.of(sample)));
            return base.with("private_probe",obj("advertised",new Bool(false),"snapshot_revision",n(3),"date_raw",n(53288472),"proof_epoch",n(epoch),"player_world_building_sources",world));
        }
    }
    private static Obj cash(PlanningRequest planning) {
        Obj frame=planning.observations().snapshot();Obj cash=obj("schema",new Text("xar.ck3.war-cash-current-resources.v1"),"read_only",new Bool(true),"game_version",new Text("1.20.0.4"),
                "executable_sha256",new Text("98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518"),"played_character_id",n(29829),"snapshot_revision",n(3),"date_raw",n(53288472),
                "queried_snapshot_id",new Text("native:3"),"queried_revision",n(3),"queried_native_revision",n(3),"current_treasury",frame.get("played_character_gold"),
                "player_monthly_gross_income",money(800000),"player_monthly_total_expenses",money(1000000),"player_monthly_net_income",money(-200000));
        cash=cash.with("monthly_income_semantics",obj("version",new Text("ck3-1.20.0.4-native-income-minus-total-expenses-v2"),"time_basis",new Text("month"),"source_scope",new Text("played_character_personal_gold"),
                "income_source",new Text("native_character_monthly_gold_income"),"expense_source",new Text("native_character_monthly_total_gold_expenses"),"military_expenses_included",new Bool(true)));
        var flags=new java.util.LinkedHashMap<String,Value>();for(String key:List.of("current_treasury_ready","monthly_gross_income_ready","monthly_total_expenses_ready","monthly_net_income_ready","current_military_expenses_ready","all_raised_military_expenses_ready","same_frame_ready"))flags.put(key,new Bool(true));
        return cash.with("readiness",new Obj(flags)).with("military_expenses",obj("current",military(500000),"all_raised",military(800000)));
    }
    private static Obj military(long gold) { var vector=new java.util.ArrayList<Value>();vector.add(n(gold));for(int i=1;i<10;i++)vector.add(n(0));return obj("status",new Text("available"),"gold_raw",n(gold),"resource_raw_native",new Arr(vector)); }
    private static Obj money(long gold) { return obj("raw",n(gold),"scale",n(100000)); }
    private static Obj rootResult(PlanningRequest request) {
        Obj title=obj("title_id",n(2230),"tier_raw",n(2),"tier_key",new Text("county"));
        var positions=new java.util.ArrayList<Value>();
        for(String key:List.of("councillor_chancellor","councillor_court_chaplain","councillor_marshal","councillor_spymaster","councillor_steward"))
            positions.add(obj("position_key",new Text(key),"incumbent_character_id",Nil.INSTANCE,"task_key",Nil.INSTANCE,"task_type",Nil.INSTANCE,"target",Nil.INSTANCE,"frozen",Nil.INSTANCE,"progress",Nil.INSTANCE));
        Obj council=obj("status",new Text("available"),"coverage_key",new Text("standard_landed_non_nomadic_core_v1"),"owner_character_id",n(29829),"positions",new Arr(positions),"unavailable_reason",Nil.INSTANCE,"auxiliary_vacancies_complete",new Bool(false));
        var ready=new java.util.LinkedHashMap<String,Value>();for(String key:List.of("adjacent_external_province_holders_ready","capital_ready","council_ready","direct_landed_vassals_ready","government_ready","held_title_partition_ready","lieges_ready","player_domain_ready","player_health_ready","player_identity_ready","player_monthly_gold_income_ready","player_targeting_factions_ready","primary_title_ready","primary_title_succession_ready","ready","related_character_contexts_ready","same_frame_ready","selected_game_rule_tokens_ready"))ready.put(key,new Bool(true));
        Obj root=obj("schema_version",n(1),"status",new Text("available"),"snapshot_revision",n(3),"date_raw",n(53288472),"local_player_id",n(0),"player_character_id",n(29829),"player_character_alive",new Bool(true),
                "player_monthly_gold_income",money(592266),"player_health",money(275000),"player_domain_size",n(1),"player_domain_limit",n(7),"player_targeting_faction_count",n(0),"council",council,
                "primary_title",title,"primary_title_succession_character_ids",new Arr(List.of()),"held_title_partition",new Arr(List.of(obj("title",title,"first_heir_character_id",Nil.INSTANCE,"capital_province_id",n(2635),"primary",new Bool(true)))),
                "capital_province_id",n(2635),"immediate_liege_character_id",Nil.INSTANCE,"top_liege_character_id",n(29829),"independent",new Bool(true),"government",obj("key",new Text("feudal_government"),"flags",new Arr(List.of()),"native_flag_count",n(0)),
                "direct_landed_vassal_character_ids",new Arr(List.of()),"adjacent_external_province_holder_character_ids",new Arr(List.of()),"related_character_contexts",new Arr(List.of()),"selected_game_rule_tokens",new Arr(List.of()),"native_selected_game_rule_token_count",n(0),
                "readiness",new Obj(ready),"unavailable_reason",Nil.INSTANCE,"provenance",provenance(),"player_max_monthly_gold_maintenance_v1",obj("status",new Text("available"),"value",money(451200),"unavailable_reason",Nil.INSTANCE));
        return obj("step",new Text(FinanceReadContracts.Query.ROOT.operation().value()),"accepted",new Bool(true),"status",new Text("available"),"query_sequence",n(1),"snapshot_revision",n(3),"campaign_root_context",root,"backend_id",new Text("native-headless"));
    }
    /** Exact .4 source constants consumed by the real strict campaign-root normalizer; this packet remains a software vector. */
    private static Obj provenance() {
        return obj("game_version",new Text("1.20.0.4"),"executable_sha256",new Text("98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518"),"backend_id",new Text("ck3-1.20.0.4-native-campaign-root-context-v1"),
                "primary_title_rva",new Text("0x289DA10"),"capital_province_rva",new Text("0x28B1CB0"),"immediate_liege_rva",new Text("0x28BFC50"),"top_liege_rva",new Text("0x28BFD80"),"government_rva",new Text("0x28C2DF0"),"selected_game_rule_service_slot_rva",new Text("0x5CB3D78"),
                "monthly_gold_income_rva",new Text("0x2BCA940"),"character_health_rva",new Text("0x28C64E0"),"domain_size_rva",new Text("0x28B71E0"),"domain_limit_rva",new Text("0x28B71B0"),"has_targeting_faction_trigger_rva",new Text("0x2B250B0"),
                "council_position_lookup_rva",new Text("0x2684EE0"),"council_active_task_ids_enumerator_rva",new Text("0x2916CC0"),"council_active_task_storage_slot_rva",new Text("0x5D1DEA0"),"council_value_progress_current_rva",new Text("0x31AB500"),"council_value_progress_maximum_rva",new Text("0x31AB820"),
                "held_title_ids_offset",new Text("0x1E0"),"title_province_rva",new Text("0x230F8E0"),"province_holder_character_id_rva",new Text("0x247D010"));
    }
}
