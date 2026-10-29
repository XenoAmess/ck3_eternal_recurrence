package org.xar.ck3.control.recovery;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FileStatIdentity;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.EpisodeWindow;
import org.xar.ck3.control.continuity.OriginalWindowReducer;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import java.util.List;

/** Actual small metadata, with explicitly synthetic checkpoint authority confined to tests. */
class ClosedFailureRecoveryTest {
    private static final String BASE = "D:\\codex-ck3-demos\\2026-10-14-robert-30year\\continuation42-cold-prep";
    private static final String CAMPAIGN = BASE + "\\robert30-v20261019-campaign01";
    private static final String N = CAMPAIGN + "\\runtime-a46";
    private static final String Q = BASE + "\\p51-fresh1066-v20261019-prepare01\\c23-source23-native30-cold100\\current-saved-a46-runtime-prep01";
    private static final Map<String, String> PINS = Map.ofEntries(
        Map.entry("n46-head240.actual.json", "86af210b06d5d60b2d1f6ac5f1f0a6d31098b518583da06270596a71b068463a"),
        Map.entry("n46-prior-basis.actual.json", "4b53ffa1a422df36cd18d29f47737fed8417a257ff42d2dc4b7093de56d27afa"),
        Map.entry("n46-prior-qualification.actual.json", "a400b38300c6b43e66800b7365e854e046d2c3bd87f53adc4e14fac0e6d267d7"),
        Map.entry("n46-full-request11543.actual.json", "8f3007683072043b8ca63b14823bd439127db47873702557f9940f2477f86a63"),
        Map.entry("n46-full-failure11543.actual.json", "4040c4c4046ebcb1ca46eb5b888270a33d9c61bfee1a29e31d1c56d311ee1120"),
        Map.entry("n46-auto-request11558.actual.json", "8fee7293debf9c4dc1963b1a5524ade426e6c43123492c021534832971a9569c"),
        Map.entry("n46-auto-failure11558.actual.json", "a29abe49623a8da965af385526b2b9a22ad0ed30d321d0ac340d4149fc74d9de"),
        Map.entry("n46-raw-state.actual.json", "7d62a0c1cf55f29094b8418aa1f716e1b966f03ddc4ab6e826ec415268d1066f"),
        Map.entry("n46-raw-governance.actual.json", "d1e5ca6463f0e9e3d46fffc4abfca5df1b190af0840786fb794bdbe261f4d6c5"),
        Map.entry("n46-next11559.actual.json", "cecd7459be3d764f3696af3d0bd7c1092c72a8c57252a8e55704a2b8879695fc"),
        Map.entry("n46-frozen-writer-source.actual.txt", "6b0ece99075e425f84ad732e3112cf5ccdc883bbb09a884aa94e0df411e9ff6e"));

    private static byte[] resource(String name) throws IOException {
        try (var stream = ClosedFailureRecoveryTest.class.getResourceAsStream("/" + name)) {
            assertNotNull(stream, "required portable source fixture: " + name);
            byte[] bytes = stream.readNBytes(RecoveryEvidence.MAX_BYTES + 1);
            assertTrue(bytes.length <= RecoveryEvidence.MAX_BYTES);
            assertEquals(PINS.get(name), RecoveryEvidence.sha256(bytes), "original fixture source pin");
            return bytes;
        }
    }

    private static RecoveryEvidence evidence(String name, String originalPath) throws IOException {
        byte[] raw = resource(name);
        return new RecoveryEvidence(new ExactRef(originalPath, raw.length, RecoveryEvidence.sha256(raw)), raw);
    }

    private static ClosedFailureRecoveryInput actualInput() throws IOException {
        RecoveryEvidence basis = evidence("n46-prior-basis.actual.json", Q + "\\CURRENT-SAVED-A46-CONTINUITY-BASIS01.json");
        ObjectNode value = basis.object(), refs = (ObjectNode) value.get("refs");
        return new ClosedFailureRecoveryInput("xenoamess-full-tower-eb9d2c1186", "2026-10-22T13:36:00Z",
            evidence("n46-head240.actual.json", CAMPAIGN + "\\ROOT-CONTINUITY-WINDOW.json"), basis,
            evidence("n46-prior-qualification.actual.json", Q + "\\CURRENT-SAVED-A46-CONTINUITY-QUALIFICATION01.json"),
            evidence("n46-full-request11543.actual.json", N + "\\p37-requests\\11543-1-result.json"),
            evidence("n46-full-failure11543.actual.json", N + "\\p37-responses\\11543-1-result.json"),
            evidence("n46-auto-request11558.actual.json", N + "\\p37-requests\\11558-1-result.json"),
            evidence("n46-auto-failure11558.actual.json", N + "\\p37-responses\\11558-1-result.json"),
            evidence("n46-raw-state.actual.json", N + "\\p37-queue\\ROOT-CUMULATIVE-LOOP-STATE.json"),
            evidence("n46-raw-governance.actual.json", N + "\\p37-queue\\ROOT-GOVERNANCE-RESULT-STATE.json"),
            evidence("n46-next11559.actual.json", N + "\\NEXT-SEQUENCE-P37.json"),
            ExactRef.fromJson(refs.get("driver")), FileStatIdentity.fromJson(value.get("driver_identity"), FileStatIdentity.SCHEMA),
            ExactRef.fromJson(refs.get("save")), FileStatIdentity.fromJson(value.get("save_identity"), FileStatIdentity.SCHEMA));
    }

    private static ExactRef syntheticRef(String name) { return new ExactRef("/fixture-only/" + name, 1, "0".repeat(64)); }

    private static RecoveryPrerequisiteVerifier fixtureOnlyVerifier() {
        return (input, digest) -> new RecoveryPrerequisiteVerifier.Verified(digest,
            syntheticRef("closed-epoch-proof.json"), syntheticRef("readonly-prefix-proof.json"),
            syntheticRef("original-sdk-checkpoint-proof.json"),
            ExactRef.fromJson(input.savedBasis().object().get("refs").get("checkpoint_validator")),
            RecoveryEvidence.sha256(StrictJson.canonical(input.savedBasis().object().get("checkpoint"))),
            input.currentDriver(), input.currentDriverIdentity(), input.currentSave(), input.currentSaveIdentity(), 7, 11558);
    }

    private static RecoveryEvidence changed(RecoveryEvidence source, ObjectNode row) throws IOException {
        // An edited source has a new identity; it never impersonates original bytes.
        byte[] bytes = new ObjectMapper().writeValueAsBytes(row);
        return new RecoveryEvidence(new ExactRef(source.reference().path() + ".fixture-edit.json", bytes.length,
                RecoveryEvidence.sha256(bytes)), bytes);
    }

    private static RecoveryEvidence changedRawField(RecoveryEvidence source, String field, String rawToken) throws IOException {
        // Parsing 2.0 into a DecimalNode and reencoding may emit 2. Insert the original
        // token into the wire bytes so the actual production reader sees its type.
        ObjectNode row = source.object(); row.remove(field);
        String base = new String(StrictJson.canonical(row), StandardCharsets.UTF_8);
        String key = new ObjectMapper().writeValueAsString(field);
        byte[] bytes = (base.substring(0, base.length() - 1) + "," + key + ":" + rawToken + "}").getBytes(StandardCharsets.UTF_8);
        return new RecoveryEvidence(new ExactRef(source.reference().path() + ".raw-token-fixture.json", bytes.length,
            RecoveryEvidence.sha256(bytes)), bytes);
    }

    private static ClosedFailureRecoveryInput replace(ClosedFailureRecoveryInput in,
            RecoveryEvidence head, RecoveryEvidence full, RecoveryEvidence state, RecoveryEvidence next) {
        return new ClosedFailureRecoveryInput(in.machineId(), in.observedAtUtc(), head, in.savedBasis(),
            in.priorQualification(), in.fullRequest(), full, in.autoRequest(), in.failedAuto(), state,
            in.rawGovernance(), next, in.currentDriver(), in.currentDriverIdentity(), in.currentSave(), in.currentSaveIdentity());
    }

    @Test void actualN46WithoutCurrentCanonicalAuthorityIsUnavailable() throws Exception {
        RecoveryPreview result = ClosedFailureRecoveryReducer.preview(actualInput());
        assertInstanceOf(RecoveryPreview.Unavailable.class, result);
        assertFalse(result.ready()); assertEquals(0, result.gameDayCredit());
    }

    @Test void actualNormalizedAnchorAndRawNativeCheckpointRemainDistinctAndBound() throws Exception {
        ClosedFailureRecoveryInput in = actualInput();
        ObjectNode normalized = (ObjectNode) in.savedBasis().object().get("checkpoint");
        ObjectNode raw = (ObjectNode) in.rawState().object().get("actual_saved_checkpoint");
        assertTrue(normalized.has("saved_date_raw")); assertFalse(normalized.has("date_raw"));
        assertTrue(raw.has("date_raw")); assertFalse(raw.has("saved_date_raw"));
        assertNotEquals(normalized, raw);
        assertInstanceOf(RecoveryPreview.Candidate.class, ClosedFailureRecoveryReducer.preview(in, fixtureOnlyVerifier()));
        for (String key : new String[] {"date_raw", "history_index", "size", "episode_character_id"}) {
            ObjectNode state = in.rawState().object();
            ((ObjectNode) state.get("actual_saved_checkpoint")).put(key, true);
            assertInstanceOf(RecoveryPreview.Rejected.class, ClosedFailureRecoveryReducer.preview(
                replace(in, in.predecessor(), in.failedFull(), changed(in.rawState(), state), in.actualNext()), fixtureOnlyVerifier()));
            state = in.rawState().object(); ((ObjectNode) state.get("actual_saved_checkpoint")).put(key, 1.0);
            assertInstanceOf(RecoveryPreview.Rejected.class, ClosedFailureRecoveryReducer.preview(
                replace(in, in.predecessor(), in.failedFull(), changed(in.rawState(), state), in.actualNext()), fixtureOnlyVerifier()));
        }
        ObjectNode state = in.rawState().object(); ((ObjectNode) state.get("actual_saved_checkpoint")).put("sha256", "0".repeat(64));
        assertInstanceOf(RecoveryPreview.Rejected.class, ClosedFailureRecoveryReducer.preview(
            replace(in, in.predecessor(), in.failedFull(), changed(in.rawState(), state), in.actualNext()), fixtureOnlyVerifier()));
    }

    @Test void syntheticAuthorityProducesExactlyOriginalFrozenRepairReducer() throws Exception {
        ClosedFailureRecoveryInput in = actualInput();
        byte[] rawState = in.rawState().bytes(), governance = in.rawGovernance().bytes();
        RecoveryPreview.Candidate candidate = assertInstanceOf(RecoveryPreview.Candidate.class,
                ClosedFailureRecoveryReducer.preview(in, fixtureOnlyVerifier()));
        assertFalse(candidate.ready()); assertEquals("repair_required", candidate.kind());
        assertEquals(240, candidate.expectedSequence());
        ObjectNode after = (ObjectNode) StrictJson.parse(candidate.reducedState());
        assertEquals("repair_required", after.get("status").textValue());
        assertEquals(5182, after.get("last_settled_cycles").longValue());
        assertEquals(53279400, after.get("last_settled_date_raw").longValue());
        assertArrayEquals(originalTransition(in.predecessor(), candidate.details()), candidate.reducedState());
        Set<String> changed = Set.of("status", "interrupted_window_id", "interruption", "last_settled_date_raw", "last_settled_cycles");
        in.predecessor().object().properties().forEach(field -> {
            if (!changed.contains(field.getKey())) { assertEquals(field.getValue(), after.get(field.getKey())); }
        });
        assertArrayEquals(rawState, in.rawState().bytes()); assertArrayEquals(governance, in.rawGovernance().bytes());
        assertEquals(5190, in.rawState().object().get("pending_cycle").get("global_turn").longValue());
        assertEquals(241, StrictJson.parse(candidate.committedState()).get("sequence").longValue());
        assertEquals(candidate.eventIdentity(), StrictJson.parse(candidate.committedState()).get("last_event_identity").textValue());
    }

    private static byte[] originalTransition(RecoveryEvidence before, byte[] details) throws Exception {
        byte[] source = resource("n46-frozen-writer-source.actual.txt");
        String program = "import json,sys\np=json.load(sys.stdin)\nn={'__name__':'_fixture_original_writer'}\n"
            + "exec(compile(p['source'],'frozen-n46-root_continuity_window_c23_100.py','exec'),n)\n"
            + "print(json.dumps(n['transition'](p['before'],'repair_required',p['details']),ensure_ascii=False,allow_nan=False,sort_keys=True,separators=(',',':')))\n";
        ObjectNode payload = StrictJson.object(); payload.put("source", new String(source, StandardCharsets.UTF_8));
        payload.set("before", before.object()); payload.set("details", StrictJson.parse(details));
        String python = System.getProperty("xar.python");
        if (python == null) { python = System.getenv("XAR_ORACLE_PYTHON"); }
        if (python == null) { python = "python"; }
        StrictJson.require(!python.isBlank() && python.equals(python.strip()), "nonempty exact oracle Python configuration");
        Process process = new ProcessBuilder(python, "-B", "-X", "utf8", "-c", program)
            .redirectErrorStream(true).start();
        CompletableFuture<byte[]> output = CompletableFuture.supplyAsync(() -> {
            try { return process.getInputStream().readNBytes(65_537); }
            catch (IOException error) { throw new UncheckedIOException(error); }
        });
        try {
            try (var stream = process.getOutputStream()) { stream.write(new ObjectMapper().writeValueAsBytes(payload)); }
            assertTrue(process.waitFor(30, TimeUnit.SECONDS), "original pure Python oracle timeout");
            byte[] bytes = output.get(5, TimeUnit.SECONDS);
            assertEquals(0, process.exitValue(), new String(bytes, StandardCharsets.UTF_8));
            return StrictJson.canonical(StrictJson.parse(bytes));
        } finally { if (process.isAlive()) { process.destroyForcibly(); } }
    }

    @Test void windowZeroAndWrongTokenTypesAreRejected() throws Exception {
        ClosedFailureRecoveryInput in = actualInput();
        for (String token : new String[] {"0", "true", "2.0", "\"2\"", "null"}) {
            RecoveryEvidence head = changedRawField(in.predecessor(), "window_id", token);
            if (token.equals("2.0")) { assertTrue(head.object().get("window_id").isFloatingPointNumber(), "raw .0 token reached production reader"); }
            assertInstanceOf(RecoveryPreview.Rejected.class, ClosedFailureRecoveryReducer.preview(
                replace(in, head, in.failedFull(), in.rawState(), in.actualNext()), fixtureOnlyVerifier()));
        }
        ObjectNode head = in.predecessor().object(); head.remove("window_id");
        assertInstanceOf(RecoveryPreview.Rejected.class, ClosedFailureRecoveryReducer.preview(
            replace(in, changed(in.predecessor(), head), in.failedFull(), in.rawState(), in.actualNext()), fixtureOnlyVerifier()));
    }

    @Test void cannotHandClearPendingOrMoveNext() throws Exception {
        ClosedFailureRecoveryInput in = actualInput(); ObjectNode state = in.rawState().object(); state.putNull("pending_cycle");
        assertInstanceOf(RecoveryPreview.Rejected.class, ClosedFailureRecoveryReducer.preview(
            replace(in, in.predecessor(), in.failedFull(), changed(in.rawState(), state), in.actualNext()), fixtureOnlyVerifier()));
        ObjectNode next = in.actualNext().object(); next.put("next_sequence", 11558);
        assertInstanceOf(RecoveryPreview.Rejected.class, ClosedFailureRecoveryReducer.preview(
            replace(in, in.predecessor(), in.failedFull(), in.rawState(), changed(in.actualNext(), next)), fixtureOnlyVerifier()));
    }

    @Test void originalGameBindingMustHaveExactShapeAndTypes() throws Exception {
        ClosedFailureRecoveryInput in = actualInput();
        for (String token : new String[] {"null", "{}", "{\"pid\":true,\"creation_date\":\"x\"}",
                "{\"pid\":50688.0,\"creation_date\":\"x\"}", "{\"pid\":50688,\"creation_date\":\"\"}",
                "{\"pid\":50688,\"creation_date\":\"x\",\"extra\":1}"}) {
            RecoveryEvidence head = changedRawField(in.predecessor(), "game_binding", token);
            if (token.contains("50688.0")) { assertTrue(head.object().get("game_binding").get("pid").isFloatingPointNumber(), "raw PID .0 token reached production reader"); }
            assertInstanceOf(RecoveryPreview.Rejected.class, ClosedFailureRecoveryReducer.preview(
                replace(in, head, in.failedFull(), in.rawState(), in.actualNext()), fixtureOnlyVerifier()));
        }
        ObjectNode head = in.predecessor().object(); head.remove("game_binding");
        assertInstanceOf(RecoveryPreview.Rejected.class, ClosedFailureRecoveryReducer.preview(
            replace(in, changed(in.predecessor(), head), in.failedFull(), in.rawState(), in.actualNext()), fixtureOnlyVerifier()));
    }

    @Test void frozenTargetPolicyCannotBeChangedInBothInputs() throws Exception {
        ClosedFailureRecoveryInput in = actualInput();
        ObjectNode head = in.predecessor().object(); head.put("target_days", 1);
        ObjectNode basis = in.savedBasis().object(); ((ObjectNode) basis.get("origin")).put("target_days", 1);
        RecoveryEvidence editedBasis = changed(in.savedBasis(), basis);
        ObjectNode qualification = in.priorQualification().object(); qualification.set("basis_ref", editedBasis.reference().toJson());
        ClosedFailureRecoveryInput edited = new ClosedFailureRecoveryInput(in.machineId(), in.observedAtUtc(),
            changed(in.predecessor(), head), editedBasis, changed(in.priorQualification(), qualification),
            in.fullRequest(), in.failedFull(), in.autoRequest(), in.failedAuto(), in.rawState(), in.rawGovernance(),
            in.actualNext(), in.currentDriver(), in.currentDriverIdentity(), in.currentSave(), in.currentSaveIdentity());
        assertInstanceOf(RecoveryPreview.Rejected.class, ClosedFailureRecoveryReducer.preview(edited, fixtureOnlyVerifier()));
    }

    @Test void wrongParentAndClaimedNewSaveAreRejected() throws Exception {
        ClosedFailureRecoveryInput in = actualInput(); ObjectNode full = in.failedFull().object(); full.put("original_response", "/wrong.json");
        assertInstanceOf(RecoveryPreview.Rejected.class, ClosedFailureRecoveryReducer.preview(
            replace(in, in.predecessor(), changed(in.failedFull(), full), in.rawState(), in.actualNext()), fixtureOnlyVerifier()));
        full = in.failedFull().object(); ((ObjectNode) full.get("full_rpc_rows_v1").get("tools").get("SAVE")).put("count", 1);
        assertInstanceOf(RecoveryPreview.Rejected.class, ClosedFailureRecoveryReducer.preview(
            replace(in, in.predecessor(), changed(in.failedFull(), full), in.rawState(), in.actualNext()), fixtureOnlyVerifier()));
    }

    @Test void providerCannotSubstituteAnotherSourceOrDriverIdentity() throws Exception {
        ClosedFailureRecoveryInput in = actualInput();
        RecoveryPrerequisiteVerifier wrong = (value, digest) -> {
            RecoveryPrerequisiteVerifier.Verified good = (RecoveryPrerequisiteVerifier.Verified) fixtureOnlyVerifier().verify(value, digest);
            return new RecoveryPrerequisiteVerifier.Verified("1".repeat(64), good.closedEpochProof(), good.settledPrefixProof(),
                good.canonicalCheckpointProof(), good.validatorSource(), good.checkpointDigest(), good.driver(),
                good.driverIdentity(), good.save(), good.saveIdentity(), good.settledPrefixCycles(), good.unknownSequence());
        };
        assertInstanceOf(RecoveryPreview.Rejected.class, ClosedFailureRecoveryReducer.preview(in, wrong));
        RecoveryPrerequisiteVerifier wrongIdentity = (value, digest) -> {
            RecoveryPrerequisiteVerifier.Verified good = (RecoveryPrerequisiteVerifier.Verified) fixtureOnlyVerifier().verify(value, digest);
            return new RecoveryPrerequisiteVerifier.Verified(digest, good.closedEpochProof(), good.settledPrefixProof(),
                good.canonicalCheckpointProof(), good.validatorSource(), good.checkpointDigest(), good.driver(),
                new FileStatIdentity(good.driverIdentity().bytes(), "1", good.driverIdentity().mtimeNs()),
                good.save(), good.saveIdentity(), good.settledPrefixCycles(), good.unknownSequence());
        };
        assertInstanceOf(RecoveryPreview.Rejected.class, ClosedFailureRecoveryReducer.preview(in, wrongIdentity));
        assertInstanceOf(RecoveryPreview.Rejected.class, ClosedFailureRecoveryReducer.preview(in,
            (value, digest) -> new RecoveryPrerequisiteVerifier.Rejected("closed SDK still active")));
    }

    @Test void metadataIsBoundedExactAndDefensivelyCopied() throws Exception {
        ClosedFailureRecoveryInput in = actualInput(); byte[] bytes = in.predecessor().bytes(); bytes[0] = '[';
        assertThrows(ContractViolationException.class, () -> new RecoveryEvidence(in.predecessor().reference(), bytes));
        assertEquals('{', in.predecessor().bytes()[0]);
        byte[] large = new byte[65_537]; Arrays.fill(large, (byte) ' ');
        assertThrows(ContractViolationException.class, () -> new RecoveryEvidence(syntheticRef("large.json"), large));
        byte[] tiny = "{}".getBytes(StandardCharsets.UTF_8);
        assertThrows(ContractViolationException.class, () -> new RecoveryEvidence(new ExactRef("/state/driver-state.json", 2,
            RecoveryEvidence.sha256(tiny)), tiny));
    }

    @Test void opaqueNativeIdentityAbove2To53AndUnknownHeadFieldsSurvive() throws Exception {
        ClosedFailureRecoveryInput in = actualInput(); ObjectNode before = in.predecessor().object();
        BigInteger birth = new BigInteger("134371430348828741"); before.put("opaque_native_filetime_fixture", birth);
        in = replace(in, changed(in.predecessor(), before), in.failedFull(), in.rawState(), in.actualNext());
        RecoveryPreview.Candidate result = assertInstanceOf(RecoveryPreview.Candidate.class,
                ClosedFailureRecoveryReducer.preview(in, fixtureOnlyVerifier()));
        assertEquals(birth, StrictJson.parse(result.reducedState()).get("opaque_native_filetime_fixture").bigIntegerValue());
        byte[] changed = result.details(); changed[0] = '[';
        assertEquals('{', result.details()[0]);
    }

    /** Synthetic new-window metadata exercises this pure consumer, never real Game/first-SAVE authority. */
    private static ClosedFailureRecoveryInput versionedInput(boolean awaiting) throws Exception {
        ClosedFailureRecoveryInput original=actualInput();ObjectNode before=original.predecessor().object();
        before.put("target_days",OriginalWindowReducer.TARGET_DAYS);
        before.put("target_date_raw",before.path("start_date_raw").longValue()+OriginalWindowReducer.TARGET_DAYS*24);
        ContinuityState old=ContinuityState.fromJson(before,original.machineId());
        long actor=original.savedBasis().object().path("frame").path("actor_character_id").longValue();
        long date=original.savedBasis().object().path("frame").path("date_raw").longValue();
        String episode=original.savedBasis().object().path("frame").path("episode_run_id").textValue();
        ObjectNode oldGame=StrictJson.object();oldGame.put("pid",111);oldGame.put("creation_filetime","133000000000000001");
        ObjectNode newGame=StrictJson.object();newGame.put("pid",222);newGame.put("creation_filetime","133000000000000002");
        var first=new EpisodeWindow.Identity(original.machineId(),org.xar.ck3.control.contracts.GameGeneration.fromJson(oldGame),"previous-session","previous-episode",0,actor,date);
        var next=new EpisodeWindow.Identity(original.machineId(),org.xar.ck3.control.contracts.GameGeneration.fromJson(newGame),"next-session",episode,1,actor,date);
        var begin=new EpisodeWindow.Begin("pure-closed-recovery-next",first,next,old.origin().windowId(),old.origin().windowId()+1,
                "fixture-next-parent",old.sequence(),"1".repeat(64),syntheticRef("lifecycle-event.json"),syntheticRef("adopted-driver.json"),List.of());
        ContinuityState waiting=EpisodeWindow.reduce(old,begin.request());ObjectNode committedWaiting=waiting.toJson();
        committedWaiting.put("sequence",old.sequence()+1);committedWaiting.put("last_event_identity",begin.request().identity());
        waiting=ContinuityState.fromJson(committedWaiting,original.machineId());
        var beginPin=new WriterContracts.Pin(syntheticRef("begin-event.json"),new WriterContracts.FileIdentity("1","9007199254740993","133000000000000003","2026-10-24T00:00:00Z",1));
        var committedBegin=new EpisodeWindow.CommittedBegin(begin,waiting.sequence(),begin.request().identity(),ContinuityJson.digest(waiting.toJson()),beginPin);
        ObjectNode head;
        if(awaiting)head=waiting.toJson();
        else{
            ExactRef pair=syntheticRef("first-pair.json");var baseline=new EpisodeWindow.Baseline(committedBegin,"fixture-first-save",pair,pair.sha256(),syntheticRef("canonical-save.json"),"2".repeat(64),next);
            head=EpisodeWindow.reduce(waiting,baseline.request()).toJson();head.put("sequence",waiting.sequence()+1);head.put("last_event_identity",baseline.request().identity());
            head.put("status","repair_required");head.set("last_settled_cycles",before.get("last_settled_cycles"));head.put("last_settled_date_raw",date);
        }
        ObjectNode basis=original.savedBasis().object();ObjectNode origin=(ObjectNode)basis.get("origin");
        for(String field:List.of("start_date_raw","target_date_raw","target_days"))origin.set(field,head.get(field));
        RecoveryEvidence editedBasis=changed(original.savedBasis(),basis);ObjectNode qualification=original.priorQualification().object();qualification.set("basis_ref",editedBasis.reference().toJson());
        return new ClosedFailureRecoveryInput(original.machineId(),original.observedAtUtc(),changed(original.predecessor(),head),editedBasis,
                changed(original.priorQualification(),qualification),original.fullRequest(),original.failedFull(),original.autoRequest(),original.failedAuto(),
                original.rawState(),original.rawGovernance(),original.actualNext(),original.currentDriver(),original.currentDriverIdentity(),original.currentSave(),original.currentSaveIdentity());
    }
    @Test void versionedActiveRecoveryKeepsItsOriginalFirstPairAndEveryWindowIdentity()throws Exception{
        ClosedFailureRecoveryInput input=versionedInput(false);
        RecoveryPreview.Candidate candidate=assertInstanceOf(RecoveryPreview.Candidate.class,ClosedFailureRecoveryReducer.preview(input,fixtureOnlyVerifier()));
        ObjectNode after=(ObjectNode)StrictJson.parse(candidate.reducedState());
        assertEquals(input.predecessor().object().get(EpisodeWindow.FIELD),after.get(EpisodeWindow.FIELD));
        assertEquals(EpisodeWindow.STATE_SCHEMA,after.path("schema").textValue());assertFalse(candidate.ready());assertEquals(0,candidate.gameDayCredit());
        assertEquals("133000000000000002",after.path("game_binding").path("creation_filetime").textValue());
        assertEquals(ContinuityState.fromJson(input.predecessor().object(),input.machineId()).origin(),ContinuityState.fromJson(after,input.machineId()).origin());
    }
    @Test void awaitingFirstSaveCannotAcquireOrdinaryClosedRecoveryEvenWithAnAvailableVerifier()throws Exception{
        ClosedFailureRecoveryInput input=versionedInput(true);
        assertInstanceOf(RecoveryPreview.Rejected.class,ClosedFailureRecoveryReducer.preview(input,(ignored,digest)->{
            throw new AssertionError("an awaiting first SAVE must fail before requesting ordinary recovery authority");
        }));
    }
}
