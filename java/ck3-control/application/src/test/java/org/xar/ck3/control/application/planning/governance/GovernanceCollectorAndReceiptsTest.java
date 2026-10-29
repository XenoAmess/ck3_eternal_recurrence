package org.xar.ck3.control.application.planning.governance;

import java.math.BigInteger;
import java.nio.file.Path;
import java.time.Clock;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.Function;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.capabilities.CampaignRootContextJson;
import org.xar.ck3.control.application.capabilities.CampaignRootContextJsonTest;
import org.xar.ck3.control.application.planning.OrdinaryPolicy;
import org.xar.ck3.control.application.planning.PlanningObservation;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.planning.governance.GovernanceFixtures.*;
import static org.xar.ck3.control.application.planning.governance.GovernanceObservationSupplier.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Actual Java collector, command codec, coordinator and receipt consumers; all I/O endpoints are explicit unit doubles. */
final class GovernanceCollectorAndReceiptsTest {
    private static final class Archive implements ActionPorts.OutcomeArchive {
        int captures;
        final Map<ExactRef, NativeActionPort.DispatchOutcome> originals = new HashMap<>();
        @Override public ExactRef preserve(NativeActionPort.DispatchOutcome original) {
            byte[] bytes = ((NativeActionPort.AckReceived) original).originalPacket();
            ExactRef ref = new ExactRef("unit-original-" + captures++, bytes.length, ActionCodec.sha256(bytes)); originals.put(ref, original); return ref;
        }
        @Override public NativeActionPort.DispatchOutcome load(ExactRef original) { return originals.get(original); }
        @Override public ExactRef preserveRequest(NativeRequest original) { throw new UnsupportedOperationException("no request archive in a read-only unit case"); }
        @Override public NativeRequest loadRequest(ExactRef original) { throw new UnsupportedOperationException("no request archive in a read-only unit case"); }
        @Override public <T> T inSession(ContinuityStorePort.Session borrowed, Function<ActionPorts.OutcomeArchive, T> work) { return work.apply(this); }
        @Override public ExactRef referenceOf(NativeActionPort.DispatchOutcome original) { return originals.entrySet().stream().filter(entry -> entry.getValue().equals(original)).findFirst().orElseThrow().getKey(); }
        @Override public ExactRef requestReferenceOf(NativeRequest original) { throw unsupported(); }
        @Override public ExactRef preserveRead(PlanningReadReceipt original) { throw unsupported(); }
        @Override public PlanningReadReceipt loadRead(ExactRef original) { throw unsupported(); }
        @Override public ExactRef readReferenceOf(PlanningReadReceipt original) { throw unsupported(); }
        @Override public ExactRef preserveRecord(ActionRecord original) { throw unsupported(); }
        @Override public ActionRecord loadRecord(ExactRef original) { throw unsupported(); }
        @Override public ExactRef recordReferenceOf(ActionRecord original) { throw unsupported(); }
        @Override public ExactRef preserveReceipt(ActionReceipt original) { throw unsupported(); }
        @Override public ActionReceipt loadReceipt(ExactRef original) { throw unsupported(); }
        @Override public ExactRef receiptReferenceOf(ActionReceipt original) { throw unsupported(); }
        @Override public ExactRef preserveMaterial(RawJson original) { throw unsupported(); }
        @Override public RawJson loadMaterial(ExactRef original) { throw unsupported(); }
        @Override public ExactRef materialReferenceOf(RawJson original) { throw unsupported(); }
        @Override public ExactRef preserveNativeFrame(NativeObservationPort.ObservedFrame original) { throw unsupported(); }
        @Override public byte[] loadNativeFrame(ExactRef original) { throw unsupported(); }
        private static UnsupportedOperationException unsupported() { return new UnsupportedOperationException("unit archive path not exercised"); }
    }
    private static final class Reads implements PlanningReadPort {
        final Function<PlanningReadRequest, Obj> responses; int calls; int borrowedCalls; boolean drift; boolean nativeOk = true; boolean forbidStandalone;
        Reads(Obj response) { this(request -> response); }
        Reads(Function<PlanningReadRequest, Obj> responses) { this.responses = responses; }
        @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract, PlanningReadRequest request) {
            if (forbidStandalone) throw new AssertionError("runtime governance must use the Root borrowed Session");
            return actual(contract, request);
        }
        @Override public <T> PlanningReadResult<T> read(ContinuityStorePort.Session borrowed, ReadContract<T> contract, PlanningReadRequest request) {
            assertNotNull(borrowed); borrowedCalls++; return actual(contract, request);
        }
        private <T> PlanningReadResult<T> actual(ReadContract<T> contract, PlanningReadRequest request) {
            calls++; contract.prepare(request, "unit-read");
            var binding = new GuardEvidence(request.before(), request.source(), request.sessionId(), BigInteger.ONE, request.operation(), REF, REF, "unit-authority", NOW, NOW.plusSeconds(20));
            var before = new PlanningReadGuard(binding, true, true, true, "a".repeat(64));
            var after = new PlanningReadGuard(binding, true, true, true, (drift ? "b" : "a").repeat(64));
            byte[] bytes = encode(responses.apply(request)); var raw = new RawJson(bytes);
            var original = new NativeActionPort.AckReceived("unit-read", nativeOk, Optional.of(raw), new RawJson(encode(new Obj(Map.of()))), bytes);
            var receipt = new PlanningReadReceipt(request, contract.contractId(), "unit-read", before, after, original);
            return new PlanningReadResult.Known<>(contract.decode(receipt), receipt, REF);
        }
    }
    private static ReadContract<Obj> queryDefinition() {
        var operation = new OperationKey("private-query-council-final-gates-v1");
        return new ReadContract<>("unit-council-definition", operation, Optional.empty(), "unit-read-permission",
                ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE, ReadContract.WireProfile.EXECUTE_STEP, REF,
                request -> new NativeRequest(operation.value(), Optional.empty(), new RawJson(encode(request.arguments()))),
                receipt -> object(parse(receipt.original().originalResultToken().orElseThrow().bytes()), "actual query token"));
    }
    private static GovernanceCollector collector(Reads port, Archive archive, boolean installed) {
        var definitions = new GovernanceCollector.Reads(Optional.empty(), Optional.empty(), Optional.empty(),
                installed ? Optional.of(queryDefinition()) : Optional.empty(), Optional.empty(), Optional.empty(), Optional.empty());
        return new GovernanceCollector(port, archive, request -> new Known<>(durable(request), List.of(REF)), definitions);
    }
    @Test void originalQueryTokenRunsThroughCollectorStrictDecoderChoiceAndCanonicalAction() {
        var request = request(); Obj original = councilRaw(request, CouncilSelection.Position.STEWARD, 10, 12, 12);
        var port = new Reads(original); var archive = new Archive(); var collector = collector(port, archive, true);
        var selected = assertInstanceOf(OrdinaryPolicy.Replace.class, new GovernancePolicies.Council(collector, REF).evaluate(request, advance(request)));
        var command = selected.draft().command().orElseThrow();
        assertEquals(GovernancePolicies.COUNCIL, command.operation()); assertEquals(n(30), command.arguments().get("candidate_character_id"));
        assertEquals(original, command.arguments().get("original_query")); assertEquals(1, port.calls); assertEquals(1, archive.captures);
        assertEquals(command, ActionCodec.decodeCommand(ActionCodec.encodeCommand(command)));
    }
    @Test void missingExactQueryDefinitionDoesNotCallTheNativePortOrPretendAnEmptyCouncil() {
        var request = request(); var port = new Reads(new Obj(Map.of())); var archive = new Archive();
        var result = collector(port, archive, false).council(request, CouncilSelection.Position.STEWARD);
        assertInstanceOf(Unavailable.class, result); assertEquals(0, port.calls); assertEquals(0, archive.captures);
    }
    @Test void completeBindingDriftOrFalseAckCannotBecomeAvailableCouncilEvidence() {
        var request = request(); var port = new Reads(councilRaw(request, CouncilSelection.Position.STEWARD, 10, 12, 12)); var archive = new Archive();
        var collector = collector(port, archive, true); port.drift = true;
        assertThrows(IllegalArgumentException.class, () -> collector.council(request, CouncilSelection.Position.STEWARD)); assertEquals(0, archive.captures);
        port.drift = false; port.nativeOk = false;
        assertThrows(IllegalArgumentException.class, () -> collector.council(request, CouncilSelection.Position.STEWARD)); assertEquals(0, archive.captures);
    }
    @Test void rootBorrowedSessionFlowsThroughTheRealCollectorReadAndArchiveWithoutStandaloneFallback() {
        var request = request(); var session = new Journal();
        var scope = new GovernanceBorrowedSession(session, Path.of("unit-writer.lock"), actual -> assertSame(session, actual));
        var port = new Reads(councilRaw(request, CouncilSelection.Position.STEWARD, 10, 12, 12)); port.forbidStandalone = true;
        var archive = new Archive();
        var definitions = new GovernanceCollector.Reads(Optional.empty(), Optional.empty(), Optional.empty(), Optional.of(queryDefinition()),
                Optional.empty(), Optional.empty(), Optional.empty());
        var collector = new GovernanceCollector(port, archive, current -> new Known<>(durable(current), List.of(REF)), definitions, scope);
        var known = assertInstanceOf(Known.class, collector.council(request, CouncilSelection.Position.STEWARD));
        assertNotNull(known.value()); assertEquals(1, port.borrowedCalls); assertEquals(1, port.calls); assertEquals(1, archive.captures);
    }
    @Test void unavailableNativeCouncilSurvivesNormalizerCollectorAndPolicyWithoutNoActionCredit() throws Exception {
        // Pinned original producer fixture and its explicit unavailable branch; I/O remains the existing unit double.
        Obj original = CampaignRootContextJsonTest.originalActual4RootFixture();
        var request = councilRootRequest(original); String reason = "actual4_council_position_key_source_unavailable";
        Obj unavailable = unavailableCouncilRoot(original, reason);
        List<CouncilSelection.Position> queried = new ArrayList<>();
        var port = councilRootReads(request, unavailable, false, queried);
        var collector = councilRootCollector(port);
        assertEquals(reason, assertInstanceOf(Unavailable.class, collector.councilRoot(request)).reason());
        var before = advance(request);
        var result = assertInstanceOf(OrdinaryPolicy.Replace.class, new GovernancePolicies.Council(collector, REF).evaluate(request, before));
        assertEquals(before.command(), result.draft().command());
        assertEquals(before.policy(), result.draft().policy());
        assertEquals(before.phase(), result.draft().phase());
        assertEquals(before.reason(), result.draft().reason());
        assertEquals(before.kind(), result.draft().kind());
        assertEquals(before.purpose(), result.draft().purpose());
        assertEquals(before.domain(), result.draft().domain());
        assertEquals(new Text(reason), result.draft().detail().get("council_root_unavailable"));
        assertEquals(List.of(CouncilSelection.Position.STEWARD), queried);
        assertNotNull(result.draft().detail().get("council_steward_query"));
        assertTrue(GovernanceCadencePublication.fromDetail(result.draft().detail()).isEmpty());
        assertEquals(3, port.calls); // Explicit root check, then the policy's steward and independent ROOT reads.
    }
    @Test void availableFullRootKeepsReviewCreditAndUnavailableRootDoesNotBlockLegalStewardChoice() throws Exception {
        Obj original = CampaignRootContextJsonTest.originalActual4RootFixture();
        var request = councilRootRequest(original); List<CouncilSelection.Position> reviewed = new ArrayList<>();
        var collector = councilRootCollector(councilRootReads(request, original, false, reviewed));
        var before = advance(request);
        var result = assertInstanceOf(OrdinaryPolicy.Replace.class, new GovernancePolicies.Council(collector, REF).evaluate(request, before));
        assertEquals(before.command(), result.draft().command());
        assertEquals(before.policy(), result.draft().policy());
        assertEquals(before.phase(), result.draft().phase());
        assertEquals(before.reason(), result.draft().reason());
        assertEquals(before.kind(), result.draft().kind());
        assertEquals(before.purpose(), result.draft().purpose());
        assertEquals(before.domain(), result.draft().domain());
        assertEquals(List.of(CouncilSelection.Position.values()), reviewed);
        var plan = GovernanceCadencePublication.fromDetail(result.draft().detail()).orElseThrow();
        assertEquals(List.of(org.xar.ck3.control.planning.optionalcadence.CadenceModels.Domain.COUNCIL), plan.completeNoActionDomains());
        List<CouncilSelection.Position> selectedReads = new ArrayList<>();
        var selectedPort = councilRootReads(request, unavailableCouncilRoot(original, "actual4_council_position_key_source_unavailable"), true, selectedReads);
        var selected = assertInstanceOf(OrdinaryPolicy.Replace.class, new GovernancePolicies.Council(councilRootCollector(selectedPort), REF).evaluate(request, advance(request)));
        assertEquals(GovernancePolicies.COUNCIL, selected.draft().command().orElseThrow().operation());
        assertEquals(List.of(CouncilSelection.Position.STEWARD), selectedReads);
        assertEquals(1, selectedPort.calls); // A legal steward choice keeps its original path; it does not require ROOT.
        assertTrue(GovernanceCadencePublication.fromDetail(selected.draft().detail()).isEmpty());
    }
    @Test void validRootBeyondReceiptJsonBudgetRetainsOrdinaryJobsThroughTheActualCollector() throws Exception {
        Obj original = councilJobRoot(false, false);
        List<Value> vassals = new ArrayList<>(array(original.get("direct_landed_vassal_character_ids"), "original direct vassals"));
        List<Value> related = new ArrayList<>(array(original.get("related_character_contexts"), "original related contexts"));
        Obj sample = related.stream().map(value -> object(value, "related context"))
                .filter(value -> new Text("direct_landed_vassal").equals(value.get("relationship_role"))).findFirst().orElseThrow();
        for (int index = 0; index < 300; index++) {
            vassals.add(n(100000 + index));
            related.add(sample.with("character_id", n(100000 + index)).with("capital_province_id", n(4000 + index))
                    .with("primary_title", object(sample.get("primary_title"), "vassal title").with("title_id", n(200000 + index))));
        }
        Obj large = original.with("direct_landed_vassal_character_ids", new Arr(vassals)).with("related_character_contexts", new Arr(related));
        assertTrue(encode(large).length > StrictJson.INPUT_MAX_BYTES);
        assertTrue(encode(large).length < org.xar.ck3.control.application.driver.DriverJson.MAX_NATIVE_BYTES);
        var request = councilRootRequest(large); List<CouncilSelection.Position> queried = new ArrayList<>();
        var port = councilJobReads(request, large, Optional.empty(), queried);
        var before = advance(request);
        var draft = assertInstanceOf(OrdinaryPolicy.Replace.class,
                new GovernancePolicies.Council(councilRootCollector(port), REF).evaluate(request, before)).draft();
        assertEquals(before.command(), draft.command());
        assertEquals(3, array(draft.detail().get("council_job_progress_observations"), "large-root jobs").size());
        assertEquals(List.of(CouncilSelection.Position.values()), queried);
        assertEquals(4, port.calls, "one real normalized root and one query per role");
    }
    @Test void ordinaryPlanProjectsThreeJobsFromOneOriginalRootWithoutInventedEffects() throws Exception {
        Obj original = councilJobRoot(true, false); var request = councilRootRequest(original);
        List<CouncilSelection.Position> queried = new ArrayList<>();
        var port = councilJobReads(request, original, Optional.empty(), queried);
        var before = advance(request);
        var draft = assertInstanceOf(OrdinaryPolicy.Replace.class,
                new GovernancePolicies.Council(councilRootCollector(port), REF).evaluate(request, before)).draft();
        assertEquals(before.command(), draft.command());
        var jobs = array(draft.detail().get("council_job_progress_observations"), "ordinary current jobs");
        assertEquals(3, jobs.size());
        Obj steward = object(jobs.get(0), "steward job"), chancellor = object(jobs.get(1), "chancellor job"), chaplain = object(jobs.get(2), "chaplain vacancy");
        assertEquals(new Text(CouncilSelection.Position.STEWARD.key()), steward.get("position_key"));
        assertEquals(new Text("task_develop_county"), steward.get("task_key"));
        assertEquals(new Bool(true), steward.get("frozen"));
        assertEquals(new Obj(Map.of()).with("kind", new Text("province")).with("province_id", n(2619)), steward.get("target"));
        assertEquals(new Obj(Map.of()).with("raw", n(9675000)).with("scale", n(100000)), steward.get("remaining_progress"));
        assertEquals(new Text("infinite"), object(chancellor.get("progress"), "infinite progress").get("kind"));
        assertNull(chancellor.get("remaining_progress"));
        assertEquals(new Text("vacant"), chaplain.get("status"));
        for (String field : List.of("incumbent_character_id", "task_key", "task_type", "target", "frozen", "progress"))
            assertEquals(Nil.INSTANCE, chaplain.get(field), field);
        for (Value value : jobs) {
            Obj job = object(value, "job");
            assertEquals(original.get("snapshot_revision"), job.get("source_native_revision"));
            assertEquals(original.get("date_raw"), job.get("source_date_raw"));
            assertEquals(new Text(request.before().frame().episodeRunId()), job.get("episode_run_id"));
            assertEquals(new Text("not_observed"), job.get("effect_attribution"));
            assertNull(job.get("completion_date_raw")); assertNull(job.get("following_comparison"));
        }
        assertEquals(draft.detail(), parse(encode(draft.detail())));
        var planned = new org.xar.ck3.control.application.planning.PlanningResult.ActionSelected(draft.command().orElseThrow(),
                new org.xar.ck3.control.application.planning.PlanTrace(request.before(), List.of(), Optional.of(draft)));
        assertEquals(planned, org.xar.ck3.control.application.planning.PlanningWire.decodeResult(
                org.xar.ck3.control.application.planning.PlanningWire.encodeResult(planned)));
        assertEquals(List.of(CouncilSelection.Position.values()), queried);
        assertEquals(4, port.calls, "one existing root and one candidate read per role");
        assertEquals(new Text("preserve"), draft.detail().get("original_marker"));
    }
    @Test void laterCouncilSelectionRetainsThreeJobProjectionAndStewardKeepsItsOneReadPath() throws Exception {
        for (var selected : CouncilSelection.Position.values()) {
            Obj original = councilJobRoot(false, false); var request = councilRootRequest(original);
            List<CouncilSelection.Position> queried = new ArrayList<>();
            var port = councilJobReads(request, original, Optional.of(selected), queried);
            var draft = assertInstanceOf(OrdinaryPolicy.Replace.class,
                    new GovernancePolicies.Council(councilRootCollector(port), REF).evaluate(request, advance(request))).draft();
            var command = draft.command().orElseThrow();
            assertEquals(GovernancePolicies.COUNCIL, command.operation());
            assertEquals(new Text(selected.key()), command.arguments().get("position_key"));
            assertEquals(command, ActionCodec.decodeCommand(ActionCodec.encodeCommand(command)));
            if (selected == CouncilSelection.Position.STEWARD) {
                assertNull(draft.detail().get("council_job_progress_observations"));
                assertEquals(1, port.calls, "presentation must not add a root read before the original steward choice");
            } else {
                assertEquals(3, array(draft.detail().get("council_job_progress_observations"), "selected job context").size());
                assertEquals(selected.ordinal() + 2, port.calls);
            }
            assertEquals(selected.ordinal() + 1, queried.size());
            assertTrue(GovernanceCadencePublication.fromDetail(draft.detail()).isEmpty());
        }
    }
    @Test void absentCouncilCoreRoleCannotBypassTheOriginalRootNormalizer() throws Exception {
        Obj original = councilJobRoot(false, true); var request = councilRootRequest(original);
        List<CouncilSelection.Position> queried = new ArrayList<>();
        var port = councilJobReads(request, original, Optional.empty(), queried);
        var failure = assertThrows(IllegalArgumentException.class, () ->
                new GovernancePolicies.Council(councilRootCollector(port), REF).evaluate(request, advance(request)));
        assertTrue(failure.getMessage().contains("cover core slots"));
        assertEquals(List.of(CouncilSelection.Position.STEWARD), queried);
        assertEquals(2, port.calls, "the malformed root is rejected before later-role queries or projection");
    }
    @Test void durablePendingEarlierActionAndCooldownPrecedeEveryJobProjectionRead() throws Exception {
        Obj original = councilJobRoot(false, false); var request = councilRootRequest(original);
        var before = advance(request); var initial = durable(request);
        Obj pending = new Obj(Map.of()).with("stage", new Text("receipt_pending"));
        for (var status : List.of(DomainStatus.PENDING, DomainStatus.UNKNOWN)) {
            var state = new Durable(initial.observed(), initial.sessionId(), initial.cadence(), initial.opening(),
                    Optional.of(new DomainState(status, Optional.empty(), Optional.of(pending), new Obj(Map.of()).with("pending", pending))), initial.crown());
            var port = new Reads(read -> { throw new AssertionError("retained pending must precede all native job/candidate reads"); });
            assertInstanceOf(OrdinaryPolicy.Wait.class,
                    new GovernancePolicies.Council(councilRootCollector(port, current -> new Known<>(state, List.of(REF))), REF).evaluate(request, before));
            assertEquals(0, port.calls);
        }
        var future = request.before().frame().identity().dateRaw().add(BigInteger.valueOf(24));
        var cadence = initial.cadence().orElseThrow().with(org.xar.ck3.control.planning.optionalcadence.CadenceModels.Domain.COUNCIL,
                new org.xar.ck3.control.planning.optionalcadence.CadenceModels.Row(0, Optional.of(future), Optional.empty(), Optional.empty(), Optional.empty(), Optional.empty()));
        var state = new Durable(initial.observed(), initial.sessionId(), Optional.of(cadence), initial.opening(), initial.council(), initial.crown());
        var port = new Reads(read -> { throw new AssertionError("cooldown or existing action must precede job reads"); });
        var policy = new GovernancePolicies.Council(councilRootCollector(port, current -> new Known<>(state, List.of(REF))), REF);
        assertInstanceOf(OrdinaryPolicy.Keep.class, policy.evaluate(request, before));
        var advance = before.command().orElseThrow();
        var earlier = new ActionCommand("earlier-war", advance.before(), advance.source(), advance.sessionId(), new OperationKey("query-army-strengths-v1"),
                advance.arguments(), advance.expected(), advance.claims(), advance.deadline());
        var war = new OrdinaryPolicy.Draft(before.policy(), "native_war", before.reason(), before.kind(), Optional.of(earlier),
                OrdinaryPolicy.Purpose.READ_ONLY, before.domain(), before.detail());
        assertInstanceOf(OrdinaryPolicy.NotApplicable.class, policy.evaluate(request, war));
        assertEquals(0, port.calls);
    }
    private static Obj councilJobRoot(boolean vacantChaplain, boolean missingChaplain) throws Exception {
        Obj original = CampaignRootContextJsonTest.originalActual4RootFixture();
        Obj council = object(original.get("council"), "original council"); List<Value> jobs = new ArrayList<>();
        for (Value existing : array(council.get("positions"), "original sorted core seats")) {
            Obj originalSeat = object(existing, "original seat");
            var matching = java.util.Arrays.stream(CouncilSelection.Position.values())
                    .filter(position -> new Text(position.key()).equals(originalSeat.get("position_key"))).findFirst();
            if (matching.isEmpty()) { jobs.add(originalSeat); continue; }
            var role = matching.orElseThrow();
            if (missingChaplain && role == CouncilSelection.Position.CHAPLAIN) continue;
            boolean vacant = vacantChaplain && role == CouncilSelection.Position.CHAPLAIN;
            Obj row = new Obj(Map.of()).with("position_key", new Text(role.key())).with("incumbent_character_id", vacant ? Nil.INSTANCE : n(20))
                    .with("task_key", vacant ? Nil.INSTANCE : new Text(role == CouncilSelection.Position.STEWARD ? "task_develop_county" : "task_domestic_affairs"))
                    .with("task_type", vacant ? Nil.INSTANCE : new Text(role == CouncilSelection.Position.STEWARD ? "county" : "general"))
                    .with("target", role == CouncilSelection.Position.STEWARD ? new Obj(Map.of()).with("kind", new Text("province")).with("province_id", n(2619)) : Nil.INSTANCE)
                    .with("frozen", vacant ? Nil.INSTANCE : new Bool(role == CouncilSelection.Position.STEWARD))
                    .with("progress", vacant ? Nil.INSTANCE : new Obj(Map.of()).with("kind", new Text(role == CouncilSelection.Position.STEWARD ? "value" : "infinite"))
                            .with("current", role == CouncilSelection.Position.STEWARD ? new Obj(Map.of()).with("raw", n(325000)).with("scale", n(100000)) : Nil.INSTANCE)
                            .with("maximum", role == CouncilSelection.Position.STEWARD ? new Obj(Map.of()).with("raw", n(10000000)).with("scale", n(100000)) : Nil.INSTANCE));
            jobs.add(row);
        }
        return original.with("council", council.with("positions", new Arr(jobs)));
    }
    private static Reads councilJobReads(PlanningRequest originalRequest, Obj rawRoot, Optional<CouncilSelection.Position> improving,
            List<CouncilSelection.Position> queried) {
        return new Reads(read -> {
            if (read.operation().value().equals("query-campaign-root-context-v1"))
                return new Obj(Map.of()).with("step", new Text("query-campaign-root-context-v1")).with("accepted", new Bool(true))
                        .with("status", rawRoot.get("status")).with("query_sequence", n(1)).with("snapshot_revision", rawRoot.get("snapshot_revision"))
                        .with("campaign_root_context", rawRoot).with("backend_id", new Text("native-headless"));
            assertEquals("private-query-council-final-gates-v1", read.operation().value());
            String key = text(read.arguments().get("position_key"), "requested council position");
            var role = java.util.Arrays.stream(CouncilSelection.Position.values()).filter(position -> position.key().equals(key)).findFirst().orElseThrow();
            queried.add(role);
            Obj result = councilRaw(originalRequest, role, 10, improving.filter(position -> position == role).isPresent() ? 12 : 10, 9);
            var seat = array(object(rawRoot.get("council"), "root council").get("positions"), "root seats").stream()
                    .map(value -> object(value, "root seat")).filter(value -> new Text(role.key()).equals(value.get("position_key"))).findFirst();
            if (seat.filter(value -> value.get("incumbent_character_id") == Nil.INSTANCE).isPresent()) {
                Obj payload = object(result.get("council_composition_candidates"), "candidate payload");
                Obj position = object(payload.get("position"), "vacant position").with("incumbent_character_id", Nil.INSTANCE)
                        .with("incumbent_main_skill", Nil.INSTANCE).with("vacant", new Bool(true)).with("action_route", new Text("assign"));
                Obj gates = object(result.get("council_final_gates"), "candidate gates").with("candidate_count", n(0)).with("rows", new Arr(List.of()));
                result = result.with("council_composition_candidates", payload.with("position", position).with("candidates", new Arr(List.of())))
                        .with("council_final_gates", gates);
            }
            return result;
        });
    }
    private static Obj unavailableCouncilRoot(Obj original, String reason) {
        Obj council = object(original.get("council"), "original council").with("status", new Text("unavailable"))
                .with("positions", new Arr(List.of())).with("unavailable_reason", new Text(reason));
        Obj readiness = object(original.get("readiness"), "original readiness")
                .with("council_ready", new Bool(false));
        return original.with("council", council).with("readiness", readiness);
    }
    private static PlanningRequest councilRootRequest(Obj original) {
        BigInteger player = integer(original.get("player_character_id"), "original player");
        BigInteger date = integer(original.get("date_raw"), "original date"), revision = integer(original.get("snapshot_revision"), "original revision");
        var frame = new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(player, revision, date), "native-" + revision, revision, "unit-episode");
        var identity = new ObservationIdentity(SOURCE.machineId(), GovernanceFixtures.identity(9).game(), frame, 1);
        Obj snapshot = request().observations().snapshot().with("snapshot_id", new Text(frame.snapshotId()))
                .with("revision", new IntegerValue(revision)).with("native_revision", new IntegerValue(revision))
                .with("date_raw", new IntegerValue(date)).with("played_character", new Obj(Map.of()).with("character_id", new IntegerValue(player)).with("alive", new Bool(true)));
        var observation = new PlanningObservation(snapshot, List.of(), Set.of(new OperationKey("life-advance"), GovernancePolicies.COUNCIL),
                Set.of(), Optional.empty(), List.of(), Optional.empty(), Optional.empty(), false);
        return new PlanningRequest(identity, SOURCE, "unit-session", NOW.plusSeconds(30), observation);
    }
    private static Reads councilRootReads(PlanningRequest originalRequest, Obj rawRoot, boolean improveSteward, List<CouncilSelection.Position> queried) {
        return new Reads(read -> {
            if (read.operation().value().equals("query-campaign-root-context-v1"))
                return new Obj(Map.of()).with("step", new Text("query-campaign-root-context-v1")).with("accepted", new Bool(true))
                        .with("status", rawRoot.get("status")).with("query_sequence", n(1)).with("snapshot_revision", rawRoot.get("snapshot_revision"))
                        .with("campaign_root_context", rawRoot).with("backend_id", new Text("native-headless"));
            assertEquals("private-query-council-final-gates-v1", read.operation().value());
            String key = text(read.arguments().get("position_key"), "requested council position");
            var role = java.util.Arrays.stream(CouncilSelection.Position.values()).filter(position -> position.key().equals(key)).findFirst().orElseThrow();
            queried.add(role); return councilRaw(originalRequest, role, 10, improveSteward ? 12 : 10, 9);
        });
    }
    private static GovernanceCollector councilRootCollector(Reads port) {
        return councilRootCollector(port, current -> new Known<>(durable(current), List.of(REF)));
    }
    private static GovernanceCollector councilRootCollector(Reads port, GovernanceCollector.StateSupplier states) {
        var operation = new OperationKey("query-campaign-root-context-v1");
        ReadContract<Obj> root = new ReadContract<>("unit-root-normalizer-definition", operation, Optional.empty(), "unit-root-permission",
                ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE, ReadContract.WireProfile.EXECUTE_STEP, REF,
                read -> new NativeRequest(operation.value(), Optional.empty(), new RawJson(encode(read.arguments()))),
                receipt -> CampaignRootContextJson.normalizeNativeResult(object(parse(receipt.original().originalResultToken().orElseThrow().bytes()), "native ROOT token"),
                        receipt.request().before().frame().identity().dateRaw(), receipt.request().before().frame().identity().nativeRevision()));
        var definitions = new GovernanceCollector.Reads(Optional.of(root), Optional.empty(), Optional.empty(), Optional.of(queryDefinition()),
                Optional.empty(), Optional.empty(), Optional.empty());
        return new GovernanceCollector(port, new Archive(), states, definitions);
    }
    private static final class Journal implements ActionJournal, ActionJournal.LockedJournal, ContinuityStorePort.Session {
        final Map<String, ActionReceipt> rows = new HashMap<>(); final List<ActionState> events = new ArrayList<>(); long sequence;
        @Override public synchronized <T> T locked(Function<ActionJournal.LockedJournal, T> action) { return action.apply(this); }
        @Override public ContinuityStorePort.Session writerSession() { return this; }
        @Override public WriterContracts.Head head() {
            var row = StrictJson.object(); row.put("schema", "root.ck3.continuity-window/v1").put("machine_id", SOURCE.machineId())
                    .put("sequence", sequence).put("window_id", 1).put("status", "running").put("start_date_raw", 100)
                    .put("target_days", 1).put("target_date_raw", 124).put("last_settled_cycles", 0).put("last_settled_date_raw", 100);
            return new WriterContracts.Head(ContinuityState.fromJson(row, SOURCE.machineId()), List.of(), List.of(), List.of(), false);
        }
        @Override public void requireWriter(Path lock) { }
        @Override public WriterContracts.Pin capturePin(ExactRef original, int maximumBytes) { throw new AssertionError("unit journal has no filesystem"); }
        @Override public void verifyPin(WriterContracts.Pin pin) { throw new AssertionError("unit journal has no filesystem"); }
        @Override public WriterContracts.Prepared preview(WriterContracts.Request request) { throw new AssertionError("unit journal has no storage producer"); }
        @Override public WriterContracts.Receipt commit(WriterContracts.Prepared prepared) { throw new AssertionError("unit journal has no storage producer"); }
        @Override public ExactRef persistedHead() { return REF; }
        @Override public Optional<ActionReceipt> find(String id) { return Optional.ofNullable(rows.get(id)); }
        @Override public List<ActionReceipt> unresolved() { return rows.values().stream().filter(row -> !row.settled()).toList(); }
        @Override public Snapshot snapshot() {
            var head = this.head();
            var sorted = rows.values().stream().sorted((a, b) -> Long.compare(a.sequence(), b.sequence())).toList();
            return new Snapshot(head.state().sequence(), head.digest(), sorted, new MissingHistoryBasis());
        }
        @Override public ActionReceipt append(ActionCommand command, String digest, ActionState state) {
            ActionTransitions.validate(find(command.actionId()), command, digest, state); events.add(state);
            ActionReceipt receipt = new ActionReceipt(1, ++sequence, command, digest, state); rows.put(command.actionId(), receipt); return receipt;
        }
    }
    private static ActionCommand crownCommand() {
        var request = request(); var selected = (OrdinaryPolicy.Replace) new GovernancePolicies.Crown(new Supplier(request), REF).evaluate(request, advance(request));
        return selected.draft().command().orElseThrow();
    }
    private static ActionCommand openingCommand() {
        var request = request(9, true, List.of());
        var selected = (OrdinaryPolicy.Replace) new GovernancePolicies.Opening(new Supplier(request), REF).evaluate(request, OrdinaryPolicy.Draft.empty());
        return selected.draft().command().orElseThrow();
    }
    private static byte[] unitPacket(byte[] body) {
        return java.nio.ByteBuffer.allocate(body.length + 4).order(java.nio.ByteOrder.LITTLE_ENDIAN)
                .putInt(body.length).put(body).array();
    }
    private static ExactRef unitAfterEvidence() {
        var after = identity(10);
        byte[] body = encode(new Obj(Map.of("snapshot_id", new Text(after.frame().snapshotId()),
                "native_revision", new IntegerValue(after.frame().identity().nativeRevision()),
                "date_raw", new IntegerValue(after.frame().identity().dateRaw()))));
        return new ExactRef("unit-independent-after-frame.json", body.length, ActionCodec.sha256(body));
    }
    private static ActionCoordinator coordinator(Journal journal, AtomicInteger writes, boolean realEffect) {
        return new ActionCoordinator("unit-authority", journal,
                (head,command) -> new GuardEvidence(command.before(), SOURCE, command.sessionId(), BigInteger.ONE, command.operation(), REF, REF, "unit-authority", NOW, NOW.plusSeconds(20)),
                command -> new NativeRequest(command.operation().value(), "unit-governance-action", new RawJson(encode(new Obj(Map.of())))),
                (permit, request, deadline) -> {
                    permit.consumeOnce(); writes.incrementAndGet();
                    var wire = object(parse(request.additionalFields().bytes()), "unit outbound fields")
                            .with("type", new Text("execute_step")).with("protocol_version", new IntegerValue(BigInteger.ONE))
                            .with("request_id", new Text(permit.requestId())).with("step", new Text(request.step()))
                            .with("expected_revision", new IntegerValue(permit.expectedRevision()));
                    byte[] outbound = unitPacket(encode(wire));
                    byte[] ack = encode(new Obj(Map.of("type", new Text("command_result"),
                            "protocol_version", new IntegerValue(BigInteger.ONE), "request_id", new Text(permit.requestId()),
                            "ok", new Bool(true), "result", new Obj(Map.of()))));
                    // Explicit unit wire double: historical ACKs retain no outbound proof or sampling custody.
                    return new NativeActionPort.AckReceived(permit.requestId(), true, Optional.of(new RawJson(encode(new Obj(Map.of())))),
                            new RawJson(ack), unitPacket(ack), realEffect
                                    ? Optional.of(new NativeActionPort.OutboundPacket(permit.requestId(), outbound)) : Optional.empty());
                },
                (command, attempt, dispatch) -> realEffect ? new ActionPorts.EffectObserved(new ActionState.EffectObservation(identity(10), SOURCE,
                        command.sessionId(), GovernancePolicies.EFFECT_SCHEMA, command.expected().values(), "unit-independent-native-read", NOW.plusSeconds(1), unitAfterEvidence()))
                        : new ActionPorts.Pending("unit ACK has no observed material effect", List.of(REF)), Clock.fixed(NOW, ZoneOffset.UTC));
    }
    @Test void ackUnknownRemainsOriginalAndCannotReplayThroughTheRealCoordinator() {
        var journal = new Journal(); var writes = new AtomicInteger(); var coordinator = coordinator(journal, writes, false); var command = crownCommand();
        ActionReceipt first = coordinator.execute(command); assertEquals(ActionReceipt.Outcome.UNRESOLVED, first.outcome());
        assertEquals(GovernanceReceipts.Status.UNRESOLVED, GovernanceReceipts.consume(first, request(11, false, List.of()), Optional.empty(), false).status());
        coordinator.execute(command); coordinator.reconcile(command.actionId()); assertEquals(1, writes.get());
    }
    @Test void appliedMaterialReceiptNeedsFollowingTurnAndOpeningNeedsItsActualBoundCheckpointFact() {
        var journal = new Journal(); var writes = new AtomicInteger(); ActionReceipt receipt = coordinator(journal, writes, true).execute(openingCommand());
        assertEquals(ActionReceipt.Outcome.APPLIED_CONFIRMED, receipt.outcome());
        assertEquals(GovernanceReceipts.Status.WAIT_FOLLOWING_TURN, GovernanceReceipts.consume(receipt, request(10, false, List.of()), Optional.empty(), false).status());
        var following = request(11, true, List.of());
        assertEquals(GovernanceReceipts.Status.CONSUMED, GovernanceReceipts.consume(receipt, following, Optional.empty(), false).status());
        assertEquals(GovernanceReceipts.Status.WAIT_CHECKPOINT, GovernanceReceipts.consume(receipt, following, Optional.empty(), true).status());
        var checkpoint = new CheckpointFact(receipt.command().actionId(), identity(10), REF);
        assertEquals(GovernanceReceipts.Status.CONSUMED, GovernanceReceipts.consume(receipt, following, Optional.of(checkpoint), true).status());
        var wrong = new CheckpointFact("different-action", identity(10), REF);
        assertThrows(IllegalArgumentException.class, () -> GovernanceReceipts.consume(receipt, following, Optional.of(wrong), true)); assertEquals(1, writes.get());
    }
    @Test void originalSavedFormalFrameConsumesTheSharedReceiptWithoutAnOldLiveGameOrFabricatedNewReceipt() {
        var journal=new Journal();var writes=new AtomicInteger();var receipt=coordinator(journal,writes,true).execute(openingCommand());
        var checkpoint=new CheckpointFact(receipt.command().actionId(),identity(11),REF);
        assertEquals(GovernanceReceipts.Status.CONSUMED,GovernanceReceipts.consumeAtFrame(receipt,identity(11),Optional.of(checkpoint),true).status());
        assertEquals(GovernanceReceipts.Status.WAIT_CHECKPOINT,GovernanceReceipts.consumeAtFrame(receipt,identity(11),Optional.empty(),true).status());
        var other=new org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity(SOURCE.machineId(),
                new GameGeneration(receipt.command().before().game().pid(),new PythonOnlyUInt64(new BigInteger("133700000000000002"))),
                identity(11).frame(),1);
        assertThrows(IllegalArgumentException.class,()->GovernanceReceipts.consumeAtFrame(receipt,other,Optional.of(checkpoint),true));
        assertEquals(1,writes.get());
    }
    @Test void currentConsumerRejectsAnotherSourceOrSessionEvenWhenTheFormalFrameMatches() {
        var journal=new Journal();var writes=new AtomicInteger();var receipt=coordinator(journal,writes,true).execute(openingCommand());
        var following=request(11,true,List.of());var checkpoint=new CheckpointFact(receipt.command().actionId(),identity(11),REF);
        var changedSource=new org.xar.ck3.control.g2.common.G2Source(SOURCE.machineId(),NOW.toString(),"1.20.0.4",new ExactRef("different-source",1,"b".repeat(64)));
        var foreignSource=new PlanningRequest(following.before(),changedSource,following.sessionId(),following.deadline(),following.observations());
        assertThrows(IllegalArgumentException.class,()->GovernanceReceipts.consume(receipt,foreignSource,Optional.of(checkpoint),true));
        var foreignSession=new PlanningRequest(following.before(),following.source(),"different-session",following.deadline(),following.observations());
        assertThrows(IllegalArgumentException.class,()->GovernanceReceipts.consume(receipt,foreignSession,Optional.of(checkpoint),true));
        assertEquals(GovernanceReceipts.Status.CONSUMED,GovernanceReceipts.consume(receipt,following,Optional.of(checkpoint),true).status());
        assertEquals(1,writes.get());
    }
    private static org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity datedIdentity(int revision,int date) {
        var original=identity(revision);var frame=original.frame();var nativeFrame=frame.identity();
        var changed=new org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Frame(nativeFrame.player(),nativeFrame.nativeRevision(),BigInteger.valueOf(date));
        return new org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity(original.machineId(),original.game(),
                new org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.ProposalFrame(changed,frame.snapshotId(),frame.revision(),frame.episodeRunId()),original.observationVersion());
    }
    @Test void forwardRevisionCannotHideBackwardEffectDateOrACheckpointOutsideTheConsumedDate() {
        var journal=new Journal();var writes=new AtomicInteger();var receipt=coordinator(journal,writes,true).execute(openingCommand());
        assertThrows(IllegalArgumentException.class,()->GovernanceReceipts.consumeAtFrame(receipt,datedIdentity(11,99),Optional.empty(),false));
        for(var date:List.of(99,101)) {
            var outside=new CheckpointFact(receipt.command().actionId(),datedIdentity(11,date),REF);
            assertThrows(IllegalArgumentException.class,()->GovernanceReceipts.consumeAtFrame(receipt,identity(12),Optional.of(outside),true));
        }
        assertEquals(1,writes.get());
    }
}
