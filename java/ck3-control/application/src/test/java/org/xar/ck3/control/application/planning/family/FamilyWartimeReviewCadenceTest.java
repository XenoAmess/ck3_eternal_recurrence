package org.xar.ck3.control.application.planning.family;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.planning.family.FamilyJson.*;
import java.io.ByteArrayInputStream;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.ArrayList;
import java.util.EnumMap;
import java.util.HexFormat;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.TimeUnit;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Actual public policy entry, real compact intake and request/receipt checks.
 * Native I/O is explicit software command-result packets; no Game custody is claimed. */
final class FamilyWartimeReviewCadenceTest {
    private static final ExactRef SOURCE = ref("software-family-source");
    private static ExactRef ref(String name) { return new ExactRef(name, 1, "a".repeat(64)); }
    private static Obj domain() { return obj("pending", Nil.INSTANCE, "resolved", Nil.INSTANCE); }
    private static Obj snapshot() {
        return obj("snapshot_id", t("native:7"), "revision", n(8), "native_revision", n(7),
                "date_raw", n(53000000), "episode_run_id", t("software-family-episode"),
                "paused", new Bool(true), "map_ready", new Bool(true),
                "active_wars", rows(List.of(n(1))), "player_armies", rows(List.of()),
                "active_event", Nil.INSTANCE, "pending_character_interaction", Nil.INSTANCE,
                "played_character", obj("character_id", n(100), "betrothed_id", Nil.INSTANCE,
                        "primary_spouse_id", Nil.INSTANCE, "spouse_ids", rows(List.of())));
    }
    private static OrdinaryPolicy.Draft baseline(String step) {
        return new OrdinaryPolicy.Draft("one-life-turn-v1", "war_observation", "software independent war choice",
                OrdinaryPolicy.Kind.ORDINARY, Optional.empty(), OrdinaryPolicy.Purpose.READ_ONLY,
                Optional.empty(), obj("selected_step", t(step)));
    }
    private static PlanningRequest request(Obj snapshot, G2Source source, long generation, String session,
            List<Obj> history) {
        var frame = new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(
                positive(object(snapshot.get("played_character")).get("character_id")),
                integer(snapshot.get("native_revision")), integer(snapshot.get("date_raw"))),
                text(snapshot.get("snapshot_id")), integer(snapshot.get("revision")), text(snapshot.get("episode_run_id")));
        var before = new ObservationIdentity(source.machineId(),
                new GameGeneration(generation, new PythonOnlyUInt64(BigInteger.ONE)), frame, 1);
        return new PlanningRequest(before, source, session, Instant.parse("2026-10-25T21:00:00Z"),
                new PlanningObservation(snapshot, history, Set.of(), Set.of(), Optional.empty(), List.of(),
                        Optional.empty(), Optional.empty(), false));
    }
    private static PlanningRequest request(Obj snapshot) {
        return request(snapshot, new G2Source("software-family-no-game", "2026-10-25T16:00:00Z",
                "software-family-cadence", SOURCE), 123, "software-family-session", List.of());
    }

    private static final class Fixture {
        private final List<FamilyPorts.Query> reads = new ArrayList<>();
        private FamilyPorts.Documents documents = new FamilyPorts.Documents(domain(), domain(), domain(),
                new FamilyPorts.BridgeIdentity(456, "2026-10-25T16:00:00Z"), ref("head1"),
                List.of(ref("family1"), ref("matrilineal1"), ref("default1")));
        private boolean unavailable;
        private Optional<FamilyPorts.Query> unavailableQuery = Optional.empty();
        private Optional<Obj> positivePlan = Optional.empty();
        private int commands;
        private FamilyPorts.Commands commandProducer = (actual, operation, args, plan) -> {
            throw new AssertionError("no proposal is available in these native packets");
        };
        private final FamilyOrdinaryPolicy policy = newPolicy();
        private FamilyOrdinaryPolicy newPolicy() {
            var projections = new EnumMap<FamilyPorts.Query, FamilyPorts.ProjectedSource>(FamilyPorts.Query.class);
            for (var query : List.of(FamilyPorts.Query.CURRENT_RELATION, FamilyPorts.Query.HEIR_LEGALITY, FamilyPorts.Query.HEIR_PROJECTION)) {
                projections.put(query, new FamilyPorts.ProjectedSource() {
                    @Override public FamilyPorts.ProjectedRead read(PlanningRequest actual, Obj arguments) {
                        reads.add(query);
                        if (unavailable || unavailableQuery.filter(query::equals).isPresent()) return new FamilyPorts.ProjectedRead(arguments,
                                new PlanningReadResult.Unavailable<>("software native read unavailable", Optional.empty()));
                        if (query == FamilyPorts.Query.HEIR_PROJECTION && positivePlan.isEmpty())
                            throw new AssertionError("an empty compact native pool has no rich projection query");
                        Obj result = query == FamilyPorts.Query.CURRENT_RELATION
                                ? obj("status", t("available"), "native_revision", actual.observations().snapshot().get("native_revision"),
                                        "heir_character_id", n(200), "betrothed_character_id", Nil.INSTANCE,
                                        "primary_spouse_character_id", Nil.INSTANCE, "spouse_character_ids", rows(List.of()))
                                : obj("status", t("available"), "native_revision", actual.observations().snapshot().get("native_revision"),
                                        "observed_first_heir_character_id", n(200), "query_sequence", n(1),
                                        "native_legal_candidates", rows(List.of()));
                        if (positivePlan.isPresent()) {
                            Obj plan = positivePlan.orElseThrow(), legality = object(plan.get("family_marriage_legality"));
                            List<Value> diagnostic = array(object(plan.get("family_marriage_private_diagnostic")).get("rows"));
                            Obj first = object(diagnostic.getFirst());
                            result = switch (query) {
                                case CURRENT_RELATION -> result.with("heir_character_id", first.get("heir_character_id"));
                                case HEIR_LEGALITY -> legality.with("native_revision", actual.observations().snapshot().get("native_revision"));
                                case HEIR_PROJECTION -> obj("status", t("available"), "native_revision", actual.observations().snapshot().get("native_revision"),
                                        "legality_query_sequence", legality.get("query_sequence"), "rows",
                                        rows(diagnostic.stream().map(FamilyJson::object)
                                                .map(row -> row.with("heir_spouse_character_ids", rows(List.of()))).toList()));
                                default -> throw new AssertionError("unexpected positive software native query");
                            };
                        }
                        return softwarePacket(actual, query, arguments, result, reads.size());
                    }
                    @Override public Obj decode(PlanningReadReceipt receipt) {
                        throw new AssertionError("cadence must not rehydrate a native result or replay an archived query");
                    }
                });
            }
            return new FamilyOrdinaryPolicy(SOURCE, new PlanningReadPort() {
                @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract, PlanningReadRequest actual) {
                    throw new AssertionError("the actual projected read route must be used");
                }
            }, new FamilyPorts.Reads(Map.of(), projections), actual -> new FamilyPorts.KnownDocuments(documents),
                    (actual, operation, args, plan) -> { commands++; return commandProducer.prepare(actual, operation, args, plan); },
                    (actual, query, args, observed) -> { throw new AssertionError("empty domains cannot publish material results"); },
                    new FamilyPorts.Settings(true, false, false, false, Optional.empty()));
        }
        private void family(Obj body) {
            documents = new FamilyPorts.Documents(body, documents.matrilineal(), documents.childDefault(),
                    documents.bridge(), documents.canonicalHead(), documents.importedDocuments());
        }
    }
    private static FamilyPorts.ProjectedRead softwarePacket(PlanningRequest actual, FamilyPorts.Query query,
            Obj arguments, Obj value, int ordinal) {
        String id = "software-family-read-" + ordinal;
        var request = new PlanningReadRequest(actual.before(), actual.source(), actual.sessionId(),
                query.operation(), arguments, actual.deadline());
        var raw = new RawJson(bytes(obj("type", t("command_result"), "protocol_version", n(1),
                "request_id", t(id), "ok", new Bool(true), "result", value)));
        byte[] encoded = raw.bytes();
        byte[] packet = ByteBuffer.allocate(encoded.length + 4).order(ByteOrder.LITTLE_ENDIAN)
                .putInt(encoded.length).put(encoded).array();
        Obj decoded = object(object(OpportunityJson.parse(raw.bytes())).get("result"));
        var ack = new NativeActionPort.AckReceived(id, true, Optional.of(new RawJson(bytes(decoded))), raw, packet);
        var guard = new PlanningReadGuard(new GuardEvidence(actual.before(), actual.source(), actual.sessionId(),
                BigInteger.ONE, query.operation(), SOURCE, SOURCE, "software-family-no-native-custody",
                Instant.parse("2026-10-25T16:00:00Z"), actual.deadline()), true, true, true, "b".repeat(64));
        var receipt = new PlanningReadReceipt(request, "software-family-contract:" + query.name(), id, guard, guard, ack);
        return new FamilyPorts.ProjectedRead(arguments, new PlanningReadResult.Known<>(decoded, receipt, SOURCE));
    }

    @Test void repeatedIdenticalWartimeCallerSkipsOnlyTheCompletedOptionalReview() {
        Fixture f = new Fixture(); var request = request(snapshot()); var baseline = baseline("query-army-strengths-v1");
        byte[] snapshotBefore = bytes(request.observations().snapshot()), documentsBefore = bytes(f.documents.family());
        var first = assertInstanceOf(OrdinaryPolicy.Replace.class, f.policy.evaluate(request, baseline));
        assertEquals(baseline.command(), first.draft().command());
        assertEquals(baseline.detail().get("selected_step"), first.draft().detail().get("selected_step"));
        assertEquals(List.of(FamilyPorts.Query.CURRENT_RELATION, FamilyPorts.Query.HEIR_LEGALITY), f.reads);
        assertInstanceOf(OrdinaryPolicy.Keep.class, f.policy.evaluate(request, baseline));
        assertEquals(2, f.reads.size()); assertEquals(0, f.commands);
        assertArrayEquals(snapshotBefore, bytes(request.observations().snapshot()));
        assertArrayEquals(documentsBefore, bytes(f.documents.family()));
        assertEquals(first.draft().detail(), OpportunityJson.parse(bytes(first.draft().detail())),
                "the scheduling record adds no persisted/wire field and existing observation detail still roundtrips");
    }

    @Test void sameDayNativePublicSnapshotHistorySourceAndSessionChangesReread() {
        Fixture f = new Fixture(); var baseline = baseline("query-army-strengths-v1"); Obj original = snapshot();
        var source = request(original).source();
        List<PlanningRequest> changed = List.of(request(original),
                request(original.with("native_revision", n(9)).with("snapshot_id", t("native:9"))),
                request(original.with("revision", n(10))),
                request(original.with("played_character_gold", n(1))),
                request(original, source, 123, "software-family-session", List.of(obj("read", t("new")))),
                request(original, new G2Source(source.machineId(), source.observedAtUtc(), source.exactBuild(), ref("source2")),
                        123, "software-family-session", List.of()),
                request(original, source, 123, "other-session", List.of()),
                request(original, source, 124, "software-family-session", List.of()));
        for (var request : changed) assertInstanceOf(OrdinaryPolicy.Replace.class, f.policy.evaluate(request, baseline));
        assertEquals(changed.size() * 2, f.reads.size()); assertEquals(0, f.commands);
    }

    @Test void laterDateActorEpisodeBaselineHeadBridgeAndImportedOriginalChangesReread() {
        Fixture f = new Fixture(); Obj original = snapshot(); var baseline = baseline("query-army-strengths-v1");
        for (Obj snapshot : List.of(original, original.with("date_raw", n(53000024)),
                original.with("played_character", object(original.get("played_character")).with("character_id", n(101))),
                original.with("episode_run_id", t("other-episode"))))
            assertInstanceOf(OrdinaryPolicy.Replace.class, f.policy.evaluate(request(snapshot), baseline));
        assertInstanceOf(OrdinaryPolicy.Replace.class, f.policy.evaluate(request(original), baseline));
        assertInstanceOf(OrdinaryPolicy.Replace.class, f.policy.evaluate(request(original), baseline("life-advance")));
        f.documents = new FamilyPorts.Documents(domain(), domain(), domain(), f.documents.bridge(), ref("head2"), f.documents.importedDocuments());
        assertInstanceOf(OrdinaryPolicy.Replace.class, f.policy.evaluate(request(original), baseline("life-advance")));
        f.documents = new FamilyPorts.Documents(domain(), domain(), domain(), new FamilyPorts.BridgeIdentity(457, "new-birth"),
                f.documents.canonicalHead(), f.documents.importedDocuments());
        assertInstanceOf(OrdinaryPolicy.Replace.class, f.policy.evaluate(request(original), baseline("life-advance")));
        f.documents = new FamilyPorts.Documents(domain(), domain(), domain(), f.documents.bridge(),
                f.documents.canonicalHead(), List.of(ref("family2"), ref("matrilineal2"), ref("default2")));
        assertInstanceOf(OrdinaryPolicy.Replace.class, f.policy.evaluate(request(original), baseline("life-advance")));
        assertEquals(18, f.reads.size());
    }

    @Test void pendingUnknownAndRetainedResultsNeverAcquireSchedulingQualification() {
        Fixture f = new Fixture(); var request = request(snapshot()); var baseline = baseline("query-army-strengths-v1");
        assertInstanceOf(OrdinaryPolicy.Replace.class, f.policy.evaluate(request, baseline));
        // Intentionally incomplete UNKNOWN input must reach the original strict pending decoder.
        f.family(obj("pending", obj("episode_run_id", t("software-family-episode"), "status", t("UNKNOWN")), "resolved", Nil.INSTANCE));
        assertInstanceOf(OrdinaryPolicy.Stop.class, f.policy.evaluate(request, baseline));
        assertInstanceOf(OrdinaryPolicy.Stop.class, f.policy.evaluate(request, baseline));
        assertEquals(0, f.commands);
        f.family(domain());
        assertInstanceOf(OrdinaryPolicy.Replace.class, f.policy.evaluate(request, baseline));
        f.family(obj("pending", Nil.INSTANCE, "resolved", obj("episode_run_id", t("software-family-episode"), "status", t("refused"))));
        assertInstanceOf(OrdinaryPolicy.Wait.class, f.policy.evaluate(request, baseline));
        assertInstanceOf(OrdinaryPolicy.Wait.class, f.policy.evaluate(request, baseline));
        f.family(domain());
        assertInstanceOf(OrdinaryPolicy.Replace.class, f.policy.evaluate(request, baseline));
        assertEquals(8, f.reads.size());
    }

    @Test void unavailableReadsAndExplicitM5AlternativeNeverSkipOrPrepareAnOldChoice() {
        Fixture f = new Fixture(); var request = request(snapshot()); var baseline = baseline("query-army-strengths-v1");
        f.unavailable = true;
        assertInstanceOf(OrdinaryPolicy.Wait.class, f.policy.evaluate(request, baseline));
        assertInstanceOf(OrdinaryPolicy.Wait.class, f.policy.evaluate(request, baseline));
        assertEquals(2, f.reads.size()); f.unavailable = false;
        assertInstanceOf(OrdinaryPolicy.Replace.class, f.policy.evaluate(request, baseline));
        assertInstanceOf(OrdinaryPolicy.Replace.class, f.policy.evaluateForCandidate(request, baseline, BigInteger.valueOf(999)));
        assertInstanceOf(OrdinaryPolicy.Replace.class, f.policy.evaluateForCandidate(request, baseline, BigInteger.valueOf(999)));
        assertInstanceOf(OrdinaryPolicy.Replace.class, f.policy.evaluate(request, baseline));
        assertEquals(10, f.reads.size()); assertEquals(0, f.commands);
    }

    @Test void failedLegalityAfterARealRelationReadDoesNotMarkTheFrameCompleted() {
        Fixture f = new Fixture(); var request = request(snapshot()); var baseline = baseline("query-army-strengths-v1");
        f.unavailableQuery = Optional.of(FamilyPorts.Query.HEIR_LEGALITY);
        assertInstanceOf(OrdinaryPolicy.Wait.class, f.policy.evaluate(request, baseline));
        assertInstanceOf(OrdinaryPolicy.Wait.class, f.policy.evaluate(request, baseline));
        assertEquals(List.of(FamilyPorts.Query.CURRENT_RELATION, FamilyPorts.Query.HEIR_LEGALITY,
                FamilyPorts.Query.CURRENT_RELATION, FamilyPorts.Query.HEIR_LEGALITY), f.reads);
        f.unavailableQuery = Optional.empty();
        assertInstanceOf(OrdinaryPolicy.Replace.class, f.policy.evaluate(request, baseline));
        assertInstanceOf(OrdinaryPolicy.Keep.class, f.policy.evaluate(request, baseline));
        assertEquals(6, f.reads.size()); assertEquals(0, f.commands);
    }

    /** Reuses the retained original candidate corpus, then runs real intake, rank and
     * FamilyCommands. Header/relation are software inputs, not fresh native custody. */
    @Test void aPositiveProposalOrM5AlternativeAlwaysRereadsAndPreparesThroughTheActualProducer() throws Exception {
        Obj input;
        try (var stream = getClass().getResourceAsStream("/m5peacetimeassembly/producer-golden-v1.json.gz")) {
            assertNotNull(stream, "existing original full candidate corpus is required");
            byte[] compressed = stream.readNBytes(65537); assertTrue(compressed.length <= 65536);
            assertEquals("61374f70cb7398c98bf88a16d7a797106ecdd47e1e8ee86c83b483461b5df6e6",
                    HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(compressed)));
            byte[] raw;
            try (var gzip = new GZIPInputStream(new ByteArrayInputStream(compressed))) {
                raw = gzip.readNBytes(1048577); assertTrue(raw.length <= 1048576); assertEquals(-1, gzip.read());
            }
            var tree = StrictJson.parse(raw, 1048576); assertEquals("MATCH", tree.get("source_postcheck").textValue());
            var sample = java.util.stream.StreamSupport.stream(tree.get("cases").spliterator(), false)
                    .filter(row -> row.get("name").textValue().equals("family-five-choices")).findFirst().orElseThrow();
            assertTrue(sample.get("accepted").booleanValue()); assertTrue(sample.get("actual_native_driver_entry_executed").booleanValue());
            input = object(OpportunityJson.parse(StrictJson.canonical(sample.get("input"), 131072)));
        }
        Fixture f = new Fixture(); Obj plan = object(object(input.get("family")).get("plan"));
        f.positivePlan = Optional.of(plan);
        List<ActionCommand> prepared = new ArrayList<>();
        f.commandProducer = new FamilyCommands((actual, operation, args, detail) -> {
            throw new AssertionError("positive first-heir proposal cannot become a date advance");
        }, (actual, command) -> prepared.add(command));
        Obj current = object(input.get("before")).with("active_wars", rows(List.of(n(1))));
        var request = request(current); var baseline = baseline("query-army-strengths-v1");
        // The real operation is required; a cache never adds executability.
        var observation = request.observations();
        request = new PlanningRequest(request.before(), request.source(), request.sessionId(), request.deadline(),
                new PlanningObservation(observation.snapshot(), observation.history(),
                        Set.of(new OperationKey("submit-observed-first-heir-marriage-v1-private")), observation.bridgeCapabilities(),
                        observation.battleSpeedReadiness(), observation.actionFacts(), observation.campaignGoal(), observation.crossRunPlan(),
                        observation.initialLifestyleFocusRequired()));
        var first = assertInstanceOf(OrdinaryPolicy.Replace.class, f.policy.evaluate(request, baseline));
        var second = assertInstanceOf(OrdinaryPolicy.Replace.class, f.policy.evaluate(request, baseline));
        BigInteger candidate = integer(object(first.draft().detail().get("family_marriage_choice")).get("candidate_character_id"));
        var alternative = assertInstanceOf(OrdinaryPolicy.Replace.class, f.policy.evaluateForCandidate(request, baseline, candidate));
        assertEquals(9, f.reads.size()); assertEquals(3, f.commands); assertEquals(3, prepared.size());
        assertNotEquals(baseline.command(), first.draft().command());
        for (var selected : List.of(first, second, alternative)) {
            ActionCommand command = selected.draft().command().orElseThrow();
            assertTrue(prepared.contains(command));
            assertEquals(command, ActionCodec.decodeCommand(ActionCodec.encodeCommand(command)));
        }
    }

    @Test void peaceForegroundAndNewRuntimeInvalidateTheProcessLocalRecord() {
        Fixture f = new Fixture(); Obj snapshot = snapshot(); var baseline = baseline("query-army-strengths-v1");
        assertInstanceOf(OrdinaryPolicy.Replace.class, f.policy.evaluate(request(snapshot), baseline));
        assertInstanceOf(OrdinaryPolicy.Keep.class, f.policy.evaluate(request(snapshot.with("active_event", obj("present", new Bool(true)))), baseline));
        assertInstanceOf(OrdinaryPolicy.Replace.class, f.policy.evaluate(request(snapshot), baseline));
        assertInstanceOf(OrdinaryPolicy.Keep.class, f.policy.evaluate(request(snapshot.with("active_wars", rows(List.of()))), baseline));
        assertInstanceOf(OrdinaryPolicy.Replace.class, f.policy.evaluate(request(snapshot), baseline));
        assertInstanceOf(OrdinaryPolicy.Replace.class, f.newPolicy().evaluate(request(snapshot), baseline));
        assertEquals(8, f.reads.size()); assertEquals(0, f.commands);
    }

    /** Executes only the exact historical scheduler method. The nested opportunity callback
     * is a counter, so this oracle grants no native/planner result qualification. */
    @Test void exactOriginalSchedulerBoundsSameDateAndNeverMarksPendingOrFailedCallbacks() throws Exception {
        Path repository = required("xar.repository.root"), python = required("xar.python");
        String code = """
            import ast,copy,hashlib,json,pathlib,sys,types
            path=pathlib.Path(sys.argv[1])/'ck3_autonomous_player/src/xar_autoplayer/bridge/service.py'
            raw=path.read_bytes()
            assert len(raw)==897392 and hashlib.sha256(raw).hexdigest()=='a8ebc680c41732a567eb1df2831fe210d7b0dc9f72f5418f1885f4b89a5e664e'
            owner=next(n for n in ast.parse(raw.decode('utf-8-sig')).body if isinstance(n,ast.ClassDef) and n.name=='GameplayBridgeService')
            method=next(n for n in owner.body if isinstance(n,ast.FunctionDef) and n.name=='_plan_private_family_wartime_v1')
            env={'wartime_family_cadence':types.SimpleNamespace(player_spouse_signature=lambda s:[],expected_successor=lambda s:None)}
            exec(compile(ast.Module(body=[method],type_ignores=[]),str(path),'exec'),env)
            invoke=env[method.name]
            class Software:
                def __init__(self):
                    self.driver=types.SimpleNamespace(allow_private_family_marriage_formal_trial=True)
                    self._last_war_family_observation=None;self.calls=0;self.pending=False;self.fail=False
                def _skip_private_family_wartime_during_cooldown_v1(self,planned,snapshot):return None
                def _plan_private_family_opportunity_v1(self,planned,snapshot,**kw):
                    self.calls+=1
                    if self.fail:raise ValueError('software unavailable callback')
                    result=copy.deepcopy(planned)
                    if self.pending:result['plan']['family_marriage_pending']={'status':'UNKNOWN'}
                    return result
            frame={'episode_run_id':'episode','played_character':{'character_id':100},'date_raw':53000000,'native_revision':7,'active_wars':[1]}
            planned={'plan':{'selected_step':'query-army-strengths-v1'}}
            software=Software();invoke(software,planned,frame);invoke(software,planned,copy.deepcopy(frame));assert software.calls==1
            # Historical Python's date-only gate also skips a changed native revision. Java
            # deliberately rereads that case; the actual-entry test above pins this narrowing.
            changed=copy.deepcopy(frame);changed['native_revision']=8;invoke(software,planned,changed);assert software.calls==1
            changed=copy.deepcopy(frame);changed['date_raw']+=24;invoke(software,planned,changed)
            changed=copy.deepcopy(frame);changed['played_character']['character_id']=101;invoke(software,planned,changed)
            changed=copy.deepcopy(frame);changed['episode_run_id']='other';invoke(software,planned,changed);assert software.calls==4
            pending=Software();pending.pending=True;invoke(pending,planned,frame);invoke(pending,planned,frame)
            assert pending.calls==2 and pending._last_war_family_observation is None
            failed=Software();failed.fail=True
            for _ in range(2):
                try:invoke(failed,planned,frame)
                except ValueError:pass
                else:raise AssertionError('original callback failure must propagate')
            assert failed.calls==2 and failed._last_war_family_observation is None
            print(json.dumps({'original_queries':software.calls,'pending_queries':pending.calls,'failed_queries':failed.calls},sort_keys=True))
            """;
        Process child = new ProcessBuilder(python.toString(), "-B", "-X", "utf8", "-c", code, repository.toString())
                .directory(repository.toFile()).redirectErrorStream(true).start();
        child.getOutputStream().close();
        try {
            assertTrue(child.waitFor(45, TimeUnit.SECONDS), "NOT_RUN_ORIGINAL_FAMILY_SCHEDULER_TIMEOUT");
            byte[] output = child.getInputStream().readNBytes(32769);
            assertTrue(output.length <= 32768, "bounded original scheduler output required");
            assertEquals(0, child.exitValue(), "NOT_RUN_REQUIRED_ORIGINAL_SOURCE: " + new String(output, StandardCharsets.UTF_8));
            Obj result = object(OpportunityJson.parse(output));
            assertEquals(BigInteger.valueOf(4), integer(result.get("original_queries")));
            assertEquals(BigInteger.TWO, integer(result.get("pending_queries")));
            assertEquals(BigInteger.TWO, integer(result.get("failed_queries")));
        } finally { if (child.isAlive()) child.destroyForcibly(); }
    }
    private static Path required(String property) throws Exception {
        String value = System.getProperty(property);
        assertNotNull(value, "NOT_RUN_REQUIRED: " + property);
        Path path = Path.of(value);
        assertTrue(path.isAbsolute() && path.normalize().equals(path), "exact absolute original path required");
        return path.toRealPath();
    }
    @Test void optionalUnpartneredSwitchDefaultsTrueAndFalseSkipsOnlyNewProposalReads() {
        var actual = request(snapshot()); var baseline = baseline("query-army-strengths-v1");
        Fixture original = new Fixture();
        assertInstanceOf(OrdinaryPolicy.Replace.class, original.policy.evaluate(actual, baseline));
        assertEquals(List.of(FamilyPorts.Query.CURRENT_RELATION, FamilyPorts.Query.HEIR_LEGALITY), original.reads);
        Fixture disabled = new Fixture(); disabled.policy.setFirstHeirMarriageEnabled(false);
        var retained = assertInstanceOf(OrdinaryPolicy.Replace.class, disabled.policy.evaluate(actual, baseline));
        assertEquals(List.of(FamilyPorts.Query.CURRENT_RELATION), disabled.reads);
        assertEquals(baseline.command(), retained.draft().command());
        assertEquals(baseline.purpose(), retained.draft().purpose());
        assertEquals(new Bool(false), retained.draft().detail().get("first_heir_marriage_enabled"));
        assertEquals(t("skipped_by_configuration"), retained.draft().detail().get("first_heir_marriage_status"));
        assertTrue(retained.reason().contains("first_heir_marriage_enabled=false"));
        assertEquals(0, disabled.commands);
        disabled.policy.setFirstHeirMarriageEnabled(true);
        assertInstanceOf(OrdinaryPolicy.Replace.class, disabled.policy.evaluate(actual, baseline));
        assertEquals(List.of(FamilyPorts.Query.CURRENT_RELATION, FamilyPorts.Query.CURRENT_RELATION, FamilyPorts.Query.HEIR_LEGALITY), disabled.reads);
    }
    @Test void optionalSwitchCannotBypassOriginalPendingUnknownOrRetainedResult() {
        Fixture disabled = new Fixture(); disabled.policy.setFirstHeirMarriageEnabled(false);
        var actual = request(snapshot()); var baseline = baseline("query-army-strengths-v1");
        disabled.family(obj("pending", obj("episode_run_id", t("software-family-episode"), "status", t("UNKNOWN")), "resolved", Nil.INSTANCE));
        assertInstanceOf(OrdinaryPolicy.Stop.class, disabled.policy.evaluate(actual, baseline));
        assertTrue(disabled.reads.isEmpty());
        disabled.family(obj("pending", Nil.INSTANCE, "resolved", obj("episode_run_id", t("software-family-episode"), "status", t("refused"))));
        assertInstanceOf(OrdinaryPolicy.Wait.class, disabled.policy.evaluate(actual, baseline));
        assertEquals(List.of(FamilyPorts.Query.CURRENT_RELATION), disabled.reads);
        assertEquals(0, disabled.commands);
    }

    @Test void newMarriageSwitchDefaultsTrueSkipsOnlyNewFirstHeirAndPreservesEducation() {
        var actual = request(snapshot()); var baseline = baseline("life-advance");
        Fixture enabled = new Fixture();
        assertInstanceOf(OrdinaryPolicy.Replace.class, enabled.policy.evaluate(actual, baseline));
        assertEquals(List.of(FamilyPorts.Query.CURRENT_RELATION, FamilyPorts.Query.HEIR_LEGALITY), enabled.reads);
        Fixture disabled = new Fixture(); disabled.policy.setNewMarriageProposalsEnabled(false);
        var retained = assertInstanceOf(OrdinaryPolicy.Replace.class, disabled.policy.evaluate(actual, baseline));
        assertEquals(List.of(FamilyPorts.Query.CURRENT_RELATION), disabled.reads);
        assertEquals(baseline.command(), retained.draft().command());
        assertEquals(baseline.purpose(), retained.draft().purpose());
        assertEquals(baseline.detail().get("selected_step"), retained.draft().detail().get("selected_step"));
        assertEquals(new Bool(false), retained.draft().detail().get("new_marriage_proposals_enabled"));
        assertEquals(new Bool(true), retained.draft().detail().get("first_heir_marriage_enabled"));
        assertEquals(t("skipped_by_configuration"), retained.draft().detail().get("first_heir_marriage_status"));
        assertTrue(retained.reason().contains("new_marriage_proposals_enabled=false"));
        assertEquals(0, disabled.commands);
        disabled.policy.setNewMarriageProposalsEnabled(true);
        assertInstanceOf(OrdinaryPolicy.Replace.class, disabled.policy.evaluate(actual, baseline));
        assertEquals(List.of(FamilyPorts.Query.CURRENT_RELATION, FamilyPorts.Query.CURRENT_RELATION, FamilyPorts.Query.HEIR_LEGALITY), disabled.reads);
        Fixture oldFlag = new Fixture(); oldFlag.policy.setFirstHeirMarriageEnabled(false);
        var oldResult = assertInstanceOf(OrdinaryPolicy.Replace.class, oldFlag.policy.evaluate(actual, baseline));
        assertEquals(new Bool(true), oldResult.draft().detail().get("new_marriage_proposals_enabled"));
        assertEquals(List.of(FamilyPorts.Query.CURRENT_RELATION), oldFlag.reads);
    }
    @Test void newMarriageSwitchPreservesChildPendingAndResolvedBeforeNewReads() {
        Fixture f = new Fixture(); f.policy.setNewMarriageProposalsEnabled(false);
        var actual = request(snapshot()); var baseline = baseline("life-advance");
        var pair = new FamilyPorts.Pair(BigInteger.valueOf(201), BigInteger.valueOf(202));
        var matri = assertInstanceOf(OrdinaryPolicy.Keep.class, FamilyChildPolicy.matrilineal(f.policy, actual, baseline, f.documents, pair));
        var child = assertInstanceOf(OrdinaryPolicy.Keep.class, FamilyChildPolicy.childDefault(f.policy, actual, baseline, f.documents));
        assertTrue(matri.reason().contains("new_marriage_proposals_enabled=false"));
        assertTrue(child.reason().contains("new_marriage_proposals_enabled=false"));
        assertTrue(f.reads.isEmpty());
        Obj unknown = obj("pending", obj("episode_run_id", t("software-family-episode"), "status", t("UNKNOWN"),
                "heir_character_id", n(201), "candidate_character_id", n(202)), "resolved", Nil.INSTANCE);
        var pendingMatri = new FamilyPorts.Documents(domain(), unknown, domain(), f.documents.bridge(), f.documents.canonicalHead(), f.documents.importedDocuments());
        var pendingDefault = new FamilyPorts.Documents(domain(), domain(), unknown, f.documents.bridge(), f.documents.canonicalHead(), f.documents.importedDocuments());
        assertThrows(IllegalArgumentException.class, () -> FamilyChildPolicy.matrilineal(f.policy, actual, baseline, pendingMatri, pair));
        assertThrows(IllegalArgumentException.class, () -> FamilyChildPolicy.childDefault(f.policy, actual, baseline, pendingDefault));
        Obj retained = obj("pending", Nil.INSTANCE, "resolved", obj("episode_run_id", t("software-family-episode"), "status", t("awaiting_current_result")));
        var resolvedMatri = new FamilyPorts.Documents(domain(), retained, domain(), f.documents.bridge(), f.documents.canonicalHead(), f.documents.importedDocuments());
        var resolvedDefault = new FamilyPorts.Documents(domain(), domain(), retained, f.documents.bridge(), f.documents.canonicalHead(), f.documents.importedDocuments());
        assertFalse(assertInstanceOf(OrdinaryPolicy.Keep.class, FamilyChildPolicy.matrilineal(f.policy, actual, baseline, resolvedMatri, pair)).reason().contains("skipped"));
        assertFalse(assertInstanceOf(OrdinaryPolicy.Keep.class, FamilyChildPolicy.childDefault(f.policy, actual, baseline, resolvedDefault)).reason().contains("skipped"));
        f.family(unknown);
        assertInstanceOf(OrdinaryPolicy.Stop.class, f.policy.evaluate(actual, baseline));
        assertTrue(f.reads.isEmpty()); assertEquals(0, f.commands);
    }
    @Test void newMarriageSwitchSkipsRulerDiscoveryButPreservesPendingResponseWait() {
        Fixture f = new Fixture(); f.policy.setNewMarriageProposalsEnabled(false);
        var baseline = baseline("life-advance");
        assertTrue(assertInstanceOf(OrdinaryPolicy.Keep.class, f.policy.evaluateRulerMarriage(request(snapshot()), baseline)).reason().contains("new_marriage_proposals_enabled=false"));
        assertTrue(f.reads.isEmpty()); assertEquals(0, f.commands);
        var commandBoundary = new AssertionError("software pending response-wait command producer reached; no Native dispatch");
        f.commandProducer = (actual, operation, arguments, plan) -> { throw commandBoundary; };
        var original = request(snapshot());
        var pendingBase = request(snapshot(), original.source(), 123, "software-family-session",
                List.of(obj("command", t("arrange-marriage-100-999"), "ok", new Bool(false))));
        var observation = pendingBase.observations();
        var pending = new PlanningRequest(pendingBase.before(), pendingBase.source(), pendingBase.sessionId(), pendingBase.deadline(),
                new PlanningObservation(observation.snapshot(), observation.history(), Set.of(new OperationKey("life-advance")),
                        observation.bridgeCapabilities(), observation.battleSpeedReadiness(), observation.actionFacts(), observation.campaignGoal(),
                        observation.crossRunPlan(), observation.initialLifestyleFocusRequired()));
        assertSame(commandBoundary, assertThrows(AssertionError.class, () -> f.policy.evaluateRulerMarriage(pending, baseline)));
        assertEquals(1, f.commands); assertTrue(f.reads.isEmpty());
    }

}
