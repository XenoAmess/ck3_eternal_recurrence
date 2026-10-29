package org.xar.ck3.control.application.planning.governance;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.governance.crownauthority.CrownAuthorityCodec;
import org.xar.ck3.control.governance.crownauthority.CrownAuthorityPolicy;
import org.xar.ck3.control.wave3.governance.crowncooldown.CrownCooldown;
import org.xar.ck3.control.wave3.governance.crowncooldown.CrownCooldownCodec;
import org.xar.ck3.control.wave3.governance.crownfinalterms.CrownFinalTerms;
import org.xar.ck3.control.wave3.governance.crownfinalterms.CrownFinalTermsCodec;
import org.xar.ck3.control.wave3.governance.crownretry.CrownRetryCodec;
import org.xar.ck3.control.wave3.governance.crownretry.CrownRetryPolicy;

/** Complete synthetic query producers feed the real codecs/reducer/verifier. No native/writer/Game qualification. */
final class CrownRetryPublicationTest {
    private static final String MACHINE = "m7-crown-software-fixture";
    private static final String CONTRACT = "fixture.original-crown-body/v1";
    private static final String BUILD = "1.20.0.4/build25734779-fixture";
    private static final long RAW = 53_169_072;
    private static final java.time.Instant DEADLINE = java.time.Instant.parse("2026-10-23T17:40:30Z");
    private static final BigInteger ACTOR = BigInteger.valueOf(73);
    private static final Path LOCK = Path.of("fixture-only-crown.lock").toAbsolutePath().normalize();
    private static final ExactRef RUNTIME = ref("fixture-exe-not-a-real-runtime", bytes("fixture-runtime"));
    private static final ExactRef PRODUCER = ref("fixture-producer-not-a-real-source", bytes("fixture-producer"));
    private static final G2Source SOURCE = new G2Source(MACHINE, "2026-10-23T17:40:00Z", BUILD,
            ref("fixture-native-current", bytes("fixture-current-native")));

    @Test void fullNativeQueriesReachOneOriginalBodyWriterAndUnchangedLegacyConsumers() throws IOException {
        Fixture fixture = new Fixture(); var proof = fixture.service.publish(fixture.session, fixture.input, DEADLINE);
        assertEquals(1, fixture.session.commits); assertTrue(fixture.captures >= 3);
        ObjectNode result = object(fixture.session.body);
        assertEquals(Set.of("pending", "resolved", "retry"), fields(result));
        assertEquals(object(fixture.original).get("resolved"), result.get("resolved"));
        assertEquals(RAW + 11 * 24, result.at("/retry/retry_date_raw").longValue());
        assertEquals(ACTOR, result.at("/retry/actor_character_id").bigIntegerValue());
        assertEquals(Set.of("bridge_pid", "episode_run_id"), fields((ObjectNode) result.at("/retry/source_context")));
        assertFalse(result.at("/retry").has("creation_filetime"));
        var frame = fixture.service.requireCurrentPublication(proof, fixture.session, identity("134371375868945259", RAW + 24, 9, 14), SOURCE, DEADLINE);
        var request = legacy(fixture.session.body, frame, "crown_authority_1");
        assertTrue(CrownRetryCodec.projectMatch(request).isPresent());
        assertEquals(BigInteger.TEN, CrownRetryPolicy.horizonDays(frame, request.state(), BigInteger.valueOf(100), true, true));
        assertFalse(proof.authorizesAction()); assertEquals(0, proof.savedDayCredit());
        assertEquals(0, CrownRetryPublication.ImportProof.class.getConstructors().length);
    }

    @Test void dueDeadlineRequestsFreshTermsAndDoesNotInventPermissionOrSavedProgress() throws IOException {
        Fixture fixture = new Fixture(); var proof = fixture.service.publish(fixture.session, fixture.input, DEADLINE);
        var due = fixture.service.requireCurrentPublication(proof, fixture.session, identity("134371375868945259", RAW + 11 * 24, 10, 15), SOURCE, DEADLINE);
        var state = legacy(fixture.session.body, due, "crown_authority_1");
        assertTrue(CrownRetryCodec.projectMatch(state).isEmpty());
        assertEquals(BigInteger.valueOf(100), CrownRetryPolicy.horizonDays(due, state.state(), BigInteger.valueOf(100), true, true));
        assertFalse(proof.authorizesAction()); assertEquals(0, proof.savedDayCredit());
        assertEquals("engine_blocked", object(fixture.nativeConsume).at("/command_result/result/realm_law_final_terms/groups/0/candidates/1/final_status").textValue());
    }

    @Test void retainedJavaRuntimeTraceDoesNotBecomeCurrentGameAuthority() throws IOException {
        var currentRuntime = ref("current-java-runtime-source", bytes("changed-java-runtime"));
        Fixture fixture = new Fixture(List.of(currentRuntime), List.of(PRODUCER));
        var proof = fixture.service.publish(fixture.session, fixture.input, DEADLINE);
        assertEquals(List.of(RUNTIME), proof.input().runtimeSources());
        assertEquals(fixture.input, CrownRetryPublication.decodeInput(CrownRetryPublication.encodeInput(proof.input())));
        assertEquals(1, fixture.session.commits);
        assertFalse(proof.authorizesAction()); assertEquals(0, proof.savedDayCredit());
        assertNotNull(fixture.service.requireCurrentPublication(proof, fixture.session,
                fixture.input.currentObserved(), SOURCE, DEADLINE));
    }

    @Test void retainedCanonicalProducerTraceDoesNotRequireTheCurrentJavaCompilation() throws IOException {
        var currentProducer = ref("current-java-producer-source", bytes("changed-java-producer"));
        Fixture fixture = new Fixture(List.of(RUNTIME), List.of(currentProducer));
        var original = fixture.session.bodyRef;
        var proof = fixture.service.publish(fixture.session, fixture.input, DEADLINE);
        assertEquals(List.of(PRODUCER), original.producerSources());
        assertEquals(List.of(PRODUCER), proof.body().producerSources());
        assertEquals(List.of(currentProducer), fixture.service.registration().producerSources());
        assertEquals(1, fixture.session.commits);
        assertEquals(object(fixture.original).get("resolved"), object(fixture.session.body).get("resolved"));
        assertFalse(proof.authorizesAction()); assertEquals(0, proof.savedDayCredit());
    }

    @Test void publicationPinsOriginalBusinessMaterialWithoutPromotingRuntimeCodeTraceToEvidence() throws IOException {
        Fixture fixture = new Fixture();
        fixture.service.publish(fixture.session, fixture.input, DEADLINE);
        var request = fixture.session.lastImport;
        assertNotNull(request);
        assertEquals(List.of(fixture.input.previousBody(), fixture.input.crownReadback(), fixture.input.crownReceipt(),
                fixture.input.finalTermsConsume(), fixture.input.finalTermsReceipt(), SOURCE.sourceRef()), request.evidence());
        assertEquals(List.of(RUNTIME), CrownRetryPublication.decodeInput(request.producerInput()).runtimeSources());
        assertEquals(1, fixture.session.commits);
    }

    @Test void oneFiletimeTickNewEpisodeActorSourceAndBodyReplacementCannotReuseThePidHint() throws IOException {
        Fixture fixture = new Fixture(); var proof = fixture.service.publish(fixture.session, fixture.input, DEADLINE);
        // Same PID, same old episode/date and same valid legacy hint are insufficient.
        assertThrows(IllegalArgumentException.class, () -> fixture.service.requireCurrentPublication(proof, fixture.session,
                identity("134371375868945260", RAW, 8, 13), SOURCE, DEADLINE));
        var original = fixture.input.currentObserved(); var frame = original.frame();
        var anotherEpisode = new ObservationIdentity(MACHINE, original.game(), new JointBudgetSelector.ProposalFrame(frame.identity(), frame.snapshotId(), frame.revision(), "new-episode"), 1);
        assertThrows(IllegalArgumentException.class, () -> fixture.service.requireCurrentPublication(proof, fixture.session, anotherEpisode, SOURCE, DEADLINE));
        var anotherActor = new ObservationIdentity(MACHINE, original.game(), new JointBudgetSelector.ProposalFrame(
                new JointBudgetSelector.Frame(BigInteger.ONE, BigInteger.valueOf(8), BigInteger.valueOf(RAW)), frame.snapshotId(), frame.revision(), frame.episodeRunId()), 1);
        assertThrows(IllegalArgumentException.class, () -> fixture.service.requireCurrentPublication(proof, fixture.session, anotherActor, SOURCE, DEADLINE));
        var anotherSource = new G2Source(MACHINE, SOURCE.observedAtUtc(), "other-build", SOURCE.sourceRef());
        assertThrows(IllegalArgumentException.class, () -> fixture.service.requireCurrentPublication(proof, fixture.session, original, anotherSource, DEADLINE));
        fixture.session.replaceBody(bytes("{\"pending\":null,\"resolved\":null,\"retry\":null}"));
        assertThrows(IllegalArgumentException.class, () -> fixture.service.requireCurrentPublication(proof, fixture.session, original, SOURCE, DEADLINE));
        assertThrows(NullPointerException.class, () -> fixture.service.requireCurrentPublication(null, fixture.session, original, SOURCE, DEADLINE));
    }

    @Test void exactPublicationInputRoundtripsAndRejectsNumericBirthWrongFieldsAndTokenKinds() {
        Fixture fixture = new Fixture(); byte[] encoded = CrownRetryPublication.encodeInput(fixture.input);
        assertEquals(fixture.input, CrownRetryPublication.decodeInput(encoded));
        ObjectNode valid = object(encoded);
        assertEquals("134371375868945259", valid.at("/current_observation/game/creation_filetime").textValue());
        for (String token : List.of("true", "1.0", "1", "null")) {
            ObjectNode wrong = valid.deepCopy(); ((ObjectNode) wrong.at("/current_observation/game")).set("creation_filetime", StrictJson.parse(bytes(token)));
            assertThrows(IllegalArgumentException.class, () -> CrownRetryPublication.decodeInput(StrictJson.canonical(wrong)));
        }
        ObjectNode missing = valid.deepCopy(); missing.remove("final_terms_consume");
        assertThrows(IllegalArgumentException.class, () -> CrownRetryPublication.decodeInput(StrictJson.canonical(missing)));
        ObjectNode extra = valid.deepCopy(); extra.put("grant_action", true);
        assertThrows(IllegalArgumentException.class, () -> CrownRetryPublication.decodeInput(StrictJson.canonical(extra)));
        var base = fixture.input.currentObserved(); var frame = base.frame();
        for (BigInteger actor : List.of(BigInteger.valueOf(-1), new BigInteger("-2147483649"), new BigInteger("2147483648"))) {
            assertThrows(IllegalArgumentException.class, () -> {
                var invalid = new ObservationIdentity(MACHINE, base.game(), new JointBudgetSelector.ProposalFrame(
                        new JointBudgetSelector.Frame(actor, frame.identity().nativeRevision(), frame.identity().dateRaw()),
                        frame.snapshotId(), frame.revision(), frame.episodeRunId()), 1);
                new CrownRetryPublication.Input(invalid, invalid, SOURCE, fixture.input.previousBody(), fixture.input.crownReadback(),
                        fixture.input.crownReceipt(), fixture.input.finalTermsConsume(), fixture.input.finalTermsReceipt(), List.of(RUNTIME));
            });
        }
    }

    @Test void signedObservedActorRoundtripsThroughTheActualPublicationCodecWithoutPrivateQueryEligibility() {
        Fixture fixture=new Fixture();var base=fixture.input.currentObserved();var frame=base.frame();
        for(long raw:List.of((long)Integer.MIN_VALUE,-16777215L,-2L,0L,(long)Integer.MAX_VALUE)) {
            BigInteger actor=BigInteger.valueOf(raw);
            var observed=new ObservationIdentity(MACHINE,base.game(),new JointBudgetSelector.ProposalFrame(
                    new JointBudgetSelector.Frame(actor,frame.identity().nativeRevision(),frame.identity().dateRaw()),
                    frame.snapshotId(),frame.revision(),frame.episodeRunId()),base.observationVersion());
            var input=new CrownRetryPublication.Input(observed,observed,SOURCE,fixture.input.previousBody(),fixture.input.crownReadback(),
                    fixture.input.crownReceipt(),fixture.input.finalTermsConsume(),fixture.input.finalTermsReceipt(),List.of(RUNTIME));
            byte[] encoded=CrownRetryPublication.encodeInput(input);var decoded=CrownRetryPublication.decodeInput(encoded);
            assertEquals(input,decoded);assertEquals(actor,decoded.currentObserved().frame().identity().player());
            assertEquals(actor.toString(),object(encoded).at("/current_observation/frame/played_character_id").textValue());
            assertEquals(actor.toString(),object(encoded).at("/query_observation/frame/played_character_id").textValue());
            // An accepted observed identity cannot replace the different actor of the original private READs.
            assertThrows(IllegalArgumentException.class,()->CrownRetryPublication.reduce(decoded,
                    new CrownRetryPublication.Material(observed,SOURCE,fixture.original,fixture.crown,fixture.nativeConsume)));
        }
        ObjectNode valid=object(CrownRetryPublication.encodeInput(fixture.input));
        for(String token:List.of("true","1.0","1","null","\"-1\"","\"-2147483649\"","\"2147483648\"","\"+1\"","\"-0\"","\"01\"","\"-01\"")) {
            ObjectNode wrong=valid.deepCopy();var value=StrictJson.parse(bytes(token));
            ((ObjectNode)wrong.at("/current_observation/frame")).set("played_character_id",value);
            ((ObjectNode)wrong.at("/query_observation/frame")).set("played_character_id",value);
            assertThrows(IllegalArgumentException.class,()->CrownRetryPublication.decodeInput(StrictJson.canonical(wrong)));
        }
        assertEquals(0,fixture.session.commits);
    }

    @Test void currentPublicDriverFrameNeverRewritesTheOriginalNativeTermsAfterSnapshot() {
        Fixture fixture=new Fixture();var query=fixture.input.queryObserved();
        var current=identity("134371375868945259",RAW,8,14);
        var input=new CrownRetryPublication.Input(current,query,SOURCE,fixture.input.previousBody(),fixture.input.crownReadback(),
                fixture.input.crownReceipt(),fixture.input.finalTermsConsume(),fixture.input.finalTermsReceipt(),List.of(RUNTIME));
        byte[] output=CrownRetryPublication.reduce(input,new CrownRetryPublication.Material(current,SOURCE,fixture.original,fixture.crown,fixture.nativeConsume));
        assertEquals(RAW+11*24,object(output).at("/retry/retry_date_raw").longValue());
        assertEquals(input,CrownRetryPublication.decodeInput(CrownRetryPublication.encodeInput(input)));
        assertEquals(13,object(fixture.nativeConsume).at("/after_snapshot/revision").intValue());
        var forged=new CrownRetryPublication.Input(current,current,SOURCE,input.previousBody(),input.crownReadback(),input.crownReceipt(),
                input.finalTermsConsume(),input.finalTermsReceipt(),List.of(RUNTIME));
        assertThrows(IllegalArgumentException.class,()->CrownRetryPublication.reduce(forged,
                new CrownRetryPublication.Material(current,SOURCE,fixture.original,fixture.crown,fixture.nativeConsume)));
        // The fixture MaterialPort retains the actual old current frame. Shape/date equality cannot replace that independent source.
        assertThrows(IllegalArgumentException.class,()->fixture.service.publish(fixture.session,input, DEADLINE));
        assertEquals(0,fixture.session.commits);
    }
    @Test void v2RequiresBothOriginalReceiptLocatorsAndRejectsLegacyCurrentFrameAliases() {
        Fixture fixture=new Fixture();ObjectNode valid=object(CrownRetryPublication.encodeInput(fixture.input));
        for(String required:List.of("query_observation","current_observation","crown_receipt","final_terms_receipt")) {
            ObjectNode missing=valid.deepCopy();missing.remove(required);
            assertThrows(IllegalArgumentException.class,()->CrownRetryPublication.decodeInput(StrictJson.canonical(missing)));
        }
        ObjectNode old=valid.deepCopy();old.put("schema","xar.java-crown-retry-publication-input/v1");
        assertThrows(IllegalArgumentException.class,()->CrownRetryPublication.decodeInput(StrictJson.canonical(old)));
        ObjectNode alias=valid.deepCopy();alias.set("observation",alias.remove("current_observation"));
        assertThrows(IllegalArgumentException.class,()->CrownRetryPublication.decodeInput(StrictJson.canonical(alias)));
        for(ObservationIdentity wrong:List.of(identity("134371375868945260",RAW,8,14),identity("134371375868945259",RAW+24,8,14),
                identity("134371375868945259",RAW,9,14),identity("134371375868945259",RAW,8,12)))
            assertThrows(IllegalArgumentException.class,()->CrownRetryPublication.requireQueryJoin(fixture.input.queryObserved(),wrong));
    }
    @Test void retainedPendingUnknownAndReadFailureDoNotBecomeClearOrAnotherPublication() {
        Fixture fixture = new Fixture(); ObjectNode pending = object(fixture.original);
        pending.set("pending", object(bytes("{\"stage\":\"UNKNOWN\",\"action_id\":\"original-unresolved\",\"ack\":true}")));
        byte[] changed = ContinuityJson.canonical(pending);
        var input = new CrownRetryPublication.Input(fixture.input.currentObserved(), fixture.input.queryObserved(), SOURCE, ref("pending-crown-original", changed),
                fixture.input.crownReadback(), fixture.input.crownReceipt(), fixture.input.finalTermsConsume(), fixture.input.finalTermsReceipt(), List.of(RUNTIME));
        var material = new CrownRetryPublication.Material(input.currentObserved(), SOURCE, changed, fixture.crown, fixture.nativeConsume);
        assertThrows(IllegalArgumentException.class, () -> CrownRetryPublication.reduce(input, material));
        fixture.failRead = true;
        assertThrows(IOException.class, () -> fixture.service.publish(fixture.session, fixture.input, DEADLINE));
        assertEquals(0, fixture.session.commits); assertArrayEquals(fixture.original, fixture.session.body);
    }

    @Test void producerRechecksWholeFrameAndFullNativeInputsInsteadOfTrustingProposedDeadline() {
        Fixture fixture = new Fixture(); ObjectNode crossed = object(fixture.nativeConsume);
        ((ObjectNode) crossed.get("after_snapshot")).put("episode_run_id", "other-episode");
        assertRejectsNative(fixture, crossed);
        for (String token : List.of("true", "1.0", "null")) {
            ObjectNode wrong = object(fixture.nativeConsume);
            ((ObjectNode) wrong.at("/command_result/result/realm_law_final_terms/crown_authority_cooldown_turn_tick"))
                    .set("manager_match_count", "1.0".equals(token)
                            ? com.fasterxml.jackson.databind.node.DecimalNode.valueOf(new java.math.BigDecimal(token))
                            : StrictJson.parse(bytes(token)));
            assertEquals("1.0".equals(token), StrictJson.parse(wrong.toString().getBytes(StandardCharsets.UTF_8))
                    .at("/command_result/result/realm_law_final_terms/crown_authority_cooldown_turn_tick/manager_match_count").isFloatingPointNumber());
            assertRejectsNative(fixture, wrong);
        }
        ObjectNode invented = object(fixture.nativeConsume);
        ((ObjectNode) invented.at("/command_result/result/realm_law_final_terms/crown_authority_cooldown")).put("retry_date_raw", RAW + 20 * 365 * 24);
        assertRejectsNative(fixture, invented);
        ObjectNode missingGroup = object(fixture.nativeConsume);
        ((com.fasterxml.jackson.databind.node.ArrayNode) missingGroup.at("/command_result/result/realm_law_final_terms/groups")).remove(1);
        assertRejectsNative(fixture, missingGroup);
    }

    @Test void readyChangedLawUnqualifiedClockAndKnownNonmembershipClearOnlyRetry() {
        Fixture fixture = new Fixture();
        for (int mode = 0; mode < 4; mode++) {
            ObjectNode query = object(fixture.nativeConsume);
            ObjectNode payload = (ObjectNode) query.at("/command_result/result/realm_law_final_terms");
            if (mode == 0) {
                ObjectNode target = (ObjectNode) payload.at("/groups/0/candidates/1"); target.put("final_status", "can_enact"); target.put("final_can_enact", true);
            } else if (mode == 3) {
                ObjectNode group = (ObjectNode) payload.at("/groups/0"); group.put("active_law_key", "crown_authority_1");
                ObjectNode first = (ObjectNode) group.at("/candidates/0"); first.put("active", false); first.put("final_status", "engine_blocked");
                ObjectNode second = (ObjectNode) group.at("/candidates/1"); second.put("active", true); second.put("final_status", "already_active");
            } else {
                ObjectNode clock = (ObjectNode) payload.get("crown_authority_cooldown"); clock.put("remaining_unit", CrownCooldown.RAW_UNIT); clock.putNull("retry_date_raw");
                if (mode == 2) {
                    ObjectNode tick = (ObjectNode) payload.get("crown_authority_cooldown_turn_tick");
                    tick.put("manager_match_count", 0); tick.put("manager_contains_context", false); tick.put("context_tick_eligible", false);
                }
            }
            byte[] raw = StrictJson.canonical(query); var input = withNative(fixture, raw);
            byte[] output = CrownRetryPublication.reduce(input, new CrownRetryPublication.Material(input.currentObserved(), SOURCE, fixture.original, fixture.crown, raw));
            assertTrue(object(output).get("retry").isNull());
            assertEquals(object(fixture.original).get("resolved"), object(output).get("resolved"));
        }
    }

    @Test void wrongBodyPortNoChangeWrongWriterAndStateOnlyQualificationCannotMintAProof() {
        Fixture wrongOutput = new Fixture(); wrongOutput.badOutput = true;
        assertThrows(IllegalArgumentException.class, () -> wrongOutput.service.publish(wrongOutput.session, wrongOutput.input, DEADLINE)); assertEquals(0, wrongOutput.session.commits);
        Fixture noChange = new Fixture(); noChange.session.noChange = true;
        assertThrows(IllegalArgumentException.class, () -> noChange.service.publish(noChange.session, noChange.input, DEADLINE));
        Fixture wrongWriter = new Fixture(); wrongWriter.session.rejectWriter = true;
        assertThrows(IOException.class, () -> wrongWriter.service.publish(wrongWriter.session, wrongWriter.input, DEADLINE));
        Fixture stateOnly = new Fixture();
        var request = new DomainBodies.ImportRequest(DomainBodies.Slot.CROWN, CONTRACT, stateOnly.input.previousBody(),
                CrownRetryPublication.encodeInput(stateOnly.input), List.of(), "not-a-proof");
        assertThrows(IOException.class, () -> stateOnly.service.verify(stateOnly.session.state, Optional.of(stateOnly.session.bodyRef), request, stateOnly.original));
    }

    @Test void currentCallerDeadlineReachesEveryImportCheckAndDoesNotBecomePersistentProofTtl() throws IOException {
        Fixture fixture = new Fixture(); byte[] originalInput = CrownRetryPublication.encodeInput(fixture.input);
        var proof = fixture.service.publish(fixture.session, fixture.input, DEADLINE);
        assertTrue(fixture.deadlines.size() >= 4);
        assertTrue(fixture.deadlines.stream().allMatch(DEADLINE::equals));
        fixture.now = DEADLINE.plusSeconds(1);
        var current = identity("134371375868945259", RAW + 24, 9, 14);
        assertThrows(IllegalArgumentException.class, () -> fixture.service.requireCurrentPublication(
                proof, fixture.session, current, SOURCE, DEADLINE));
        java.time.Instant nextCallerDeadline = DEADLINE.plusSeconds(60);
        assertNotNull(fixture.service.requireCurrentPublication(proof, fixture.session, current, SOURCE, nextCallerDeadline));
        assertEquals(nextCallerDeadline, fixture.deadlines.getLast());
        assertArrayEquals(originalInput, CrownRetryPublication.encodeInput(proof.input()));
        assertEquals(1, fixture.session.commits);
    }

    @Test void commitRecheckKeepsTheCallerDeadlineAndFailedPublicationCannotLeakItsScope() throws IOException {
        Fixture fixture = new Fixture(); fixture.session.expireBeforeCommit = true;
        assertThrows(IllegalArgumentException.class, () -> fixture.service.publish(fixture.session, fixture.input, DEADLINE));
        assertEquals(0, fixture.session.commits); assertArrayEquals(fixture.original, fixture.session.body);
        var request = new DomainBodies.ImportRequest(DomainBodies.Slot.CROWN, CONTRACT, fixture.input.previousBody(),
                CrownRetryPublication.encodeInput(fixture.input), List.of(), "no-active-publication");
        assertThrows(IOException.class, () -> fixture.service.verify(fixture.session.head(),
                Optional.of(fixture.session.bodyRef), request, fixture.original));
        fixture.session.expireBeforeCommit = false;
        fixture.service.publish(fixture.session, fixture.input, DEADLINE.plusSeconds(60));
        assertEquals(1, fixture.session.commits);
    }

    private static void assertRejectsNative(Fixture fixture, ObjectNode value) {
        byte[] raw = value.toString().getBytes(StandardCharsets.UTF_8);
        assertTrue(raw.length > 0 && raw.length <= StrictJson.INPUT_MAX_BYTES, "bounded malformed original JSON input required");
        var input = withNative(fixture, raw);
        assertThrows(IllegalArgumentException.class, () -> CrownRetryPublication.reduce(input,
                new CrownRetryPublication.Material(input.currentObserved(), SOURCE, fixture.original, fixture.crown, raw)));
    }
    private static CrownRetryPublication.Input withNative(Fixture fixture, byte[] raw) {
        return new CrownRetryPublication.Input(fixture.input.currentObserved(), fixture.input.queryObserved(), SOURCE, fixture.input.previousBody(), fixture.input.crownReadback(), fixture.input.crownReceipt(), ref("modified-fixture-native", raw), fixture.input.finalTermsReceipt(), List.of(RUNTIME));
    }
    private static CrownRetryCodec.MatchRequest legacy(byte[] body, CrownRetryPolicy.Frame frame, String law) {
        ObjectNode request = StrictJson.object(); request.put("schema", CrownRetryCodec.MATCH_SCHEMA); request.put("bridge_pid", frame.context().bridgePid());
        ObjectNode snapshot = request.putObject("snapshot"); snapshot.put("episode_run_id", frame.context().episodeRunId());
        snapshot.put("date_raw", frame.dateRaw()); snapshot.putObject("played_character").put("character_id", frame.actorCharacterId());
        request.set("state", object(body)); request.put("law_key", law); return CrownRetryCodec.decodeMatch(StrictJson.canonical(request));
    }
    private static ObservationIdentity identity(String birth, long raw, int nativeRevision, int publicRevision) {
        return new ObservationIdentity(MACHINE, new GameGeneration(321, new PythonOnlyUInt64(new BigInteger(birth))),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(ACTOR, BigInteger.valueOf(nativeRevision), BigInteger.valueOf(raw)),
                        "actual-native-" + nativeRevision, BigInteger.valueOf(publicRevision), "original-campaign-episode"), 1);
    }
    private static ObjectNode snapshot(String snapshot, int revision, int nativeRevision) {
        ObjectNode row = StrictJson.object(); row.put("snapshot_id", snapshot); row.put("revision", revision); row.put("native_revision", nativeRevision);
        row.put("episode_run_id", "original-campaign-episode"); row.put("date_raw", RAW); row.put("paused", true); row.put("map_ready", true);
        row.putObject("played_character").put("character_id", ACTOR).put("alive", true);
        row.putObject("diagnostics").putObject("hello").put("expected_ck3_version", CrownFinalTerms.Build.CK3_12004.version())
                .put("expected_ck3_sha256", CrownFinalTerms.Build.CK3_12004.sha256()); return row;
    }
    private static byte[] nativeConsume() {
        ObjectNode row = StrictJson.object(); row.put("schema", CrownFinalTermsCodec.CONSUME_SCHEMA); row.put("expected_revision", 12); row.put("request_id", "actual-fixture-query");
        row.set("before_snapshot", snapshot("before-native-7", 12, 7)); row.set("after_snapshot", snapshot("actual-native-8", 13, 8));
        ObjectNode command = row.putObject("command_result"); command.put("type", "command_result"); command.put("protocol_version", 1); command.put("request_id", "actual-fixture-query"); command.put("ok", true);
        ObjectNode result = command.putObject("result"); result.put("step", CrownFinalTerms.STEP); result.put("accepted", true); result.put("status", "available");
        result.put("private_build", true); result.put("read_only", true); result.put("advertised", false); result.put("backend_id", "native-headless"); result.put("snapshot_revision", 7);
        ObjectNode payload = result.putObject("realm_law_final_terms"); payload.put("schema", CrownFinalTerms.SCHEMA); payload.put("snapshot_revision", 7);
        payload.put("date_raw", RAW); payload.put("actor_character_id", ACTOR); payload.put("cost_scale", 100000);
        var slots = payload.putArray("cost_slots"); CrownFinalTerms.SLOTS.forEach(slots::add); var groups = payload.putArray("groups");
        ObjectNode crown = groups.addObject(); crown.put("group_key", "crown_authority"); crown.put("active_law_key", "crown_authority_0");
        var candidates = crown.putArray("candidates"); law(candidates.addObject(), "crown_authority_0", true, false); law(candidates.addObject(), "crown_authority_1", false, false);
        ObjectNode succession = groups.addObject(); succession.put("group_key", "succession_order_laws"); succession.put("active_law_key", "partition");
        law(succession.putArray("candidates").addObject(), "partition", true, true);
        var raw = new CrownCooldown.RawObservation(true, true, true, 28, 7, 21, BigInteger.valueOf(RAW + 11 * 24), CrownCooldown.EXPIRY_TYPE, CrownCooldown.PROJECTED_UNIT);
        var tick = new CrownCooldown.TurnTick(true, BigInteger.TWO, true, true, true, null, CrownCooldown.TICK_SOURCE);
        payload.set("crown_authority_cooldown", StrictJson.parse(CrownCooldownCodec.encode(raw)));
        payload.set("crown_authority_cooldown_turn_tick", StrictJson.parse(CrownCooldownCodec.encode(tick))); return StrictJson.canonical(row);
    }
    private static void law(ObjectNode row, String key, boolean active, boolean profile) {
        row.put("law_key", key); row.put("active", active); row.put("final_status", active ? "already_active" : "engine_blocked");
        row.put("final_can_enact", false); row.put("native_reason", active ? "" : "observed current cooldown"); var costs = row.putArray("cost_raw");
        for (int index = 0; index < 10; index++) costs.add(0);
        if (profile) { row.put("succession_profile_status", "absent"); row.putNull("succession_profile"); }
    }
    private static byte[] crown() {
        var source = new CrownAuthorityPolicy.SourceFrame(BigInteger.valueOf(5), BigInteger.valueOf(5), BigInteger.ONE,
                BigInteger.valueOf(RAW), ACTOR, "1.20.0.4", CrownFinalTerms.Build.CK3_12004.sha256(), "native-5", BigInteger.TEN, BigInteger.valueOf(5));
        var candidates = List.of(new CrownAuthorityPolicy.Candidate("crown_authority_0", true, false, false, "active", List.of()),
                new CrownAuthorityPolicy.Candidate("crown_authority_1", false, true, false, "native final blocked", List.of()));
        var balances = Arrays.stream(CrownAuthorityPolicy.Currency.values()).map(currency -> new CrownAuthorityPolicy.Balance(currency, BigInteger.valueOf(100_000))).toList();
        var titles = new CrownAuthorityPolicy.TitleSuccessors(BigInteger.ONE, List.of(new CrownAuthorityPolicy.HeldTitle(BigInteger.ONE, true, List.of(ACTOR))));
        return CrownAuthorityCodec.encodeReadback(new CrownAuthorityPolicy.Readback(CrownAuthorityPolicy.READ_SCHEMA, true, true, "crown_authority", "crown_authority_0", candidates, balances, titles, source, true, false));
    }
    private static final class Fixture {
        private final byte[] original = bytes("{\"pending\":null,\"resolved\":{\"action_id\":\"retained-original\",\"ack\":{\"ok\":true},\"native_receipt\":null},\"retry\":null}");
        private final byte[] crown = crown();
        private final byte[] nativeConsume = nativeConsume();
        private final CrownRetryPublication.Input input = new CrownRetryPublication.Input(identity("134371375868945259", RAW, 8, 13), identity("134371375868945259", RAW, 8, 13), SOURCE,
                ref("fixture-original-body", original), ref("fixture-crown-readback", crown), ref("synthetic-crown-receipt", bytes("fixture-crown-receipt")), ref("fixture-final-consume", nativeConsume), ref("synthetic-terms-receipt", bytes("fixture-terms-receipt")), List.of(RUNTIME));
        private final CrownRetryPublication service;
        private final Session session;
        private int captures;
        private java.time.Instant now = DEADLINE.minusSeconds(30);
        private final java.util.List<java.time.Instant> deadlines = new java.util.ArrayList<>();
        private boolean failRead;
        private boolean badOutput;
        private byte[] output;
        private void requireDeadline(java.time.Instant callerDeadline) {
            StrictJson.require(now.isBefore(java.util.Objects.requireNonNull(callerDeadline)), "synthetic caller deadline expired");
            deadlines.add(callerDeadline);
        }
        private Fixture() { this(List.of(RUNTIME), List.of(PRODUCER)); }
        private Fixture(List<ExactRef> currentRuntime, List<ExactRef> currentProducer) {
            service = new CrownRetryPublication(LOCK, CONTRACT, currentRuntime, currentProducer, new CrownRetryPublication.MaterialPort() {
                @Override public CrownRetryPublication.Material capture(WriterContracts.Head head, CrownRetryPublication.Input selected, java.time.Instant callerDeadline) throws IOException {
                    requireDeadline(callerDeadline); captures++; if (failRead) throw new IOException("actual native archive unavailable");
                    return new CrownRetryPublication.Material(input.currentObserved(), SOURCE, original, crown, nativeConsume);
                }
                @Override public void requireCurrent(WriterContracts.Head head, CrownRetryPublication.Input selected, ObservationIdentity current, G2Source source, java.time.Instant callerDeadline) throws IOException {
                    requireDeadline(callerDeadline); if (failRead) throw new IOException("held runtime source unavailable");
                    assertEquals(List.of(RUNTIME), selected.runtimeSources()); assertEquals(MACHINE, current.machineId());
                }
            }, (id, body) -> { output = body.clone(); return ref("fixture-output-" + id, badOutput ? bytes("wrong-source") : body); });
            session = new Session(this);
        }
    }
    /** Fake storage exercises order and the real verifier; it never claims physical-file/writer qualification. */
    private static final class Session implements ContinuityStorePort.Session {
        private final Fixture fixture;
        private ContinuityState state;
        private DomainBodies.BodyRef bodyRef;
        private byte[] body;
        private int commits;
        private boolean noChange;
        private boolean rejectWriter;
        private boolean expireBeforeCommit;
        private DomainBodies.ImportRequest lastImport;
        private Session(Fixture fixture) {
            this.fixture = fixture; body = fixture.original.clone(); bodyRef = bodyRef(fixture.input.previousBody());
            ObjectNode row = StrictJson.object(); row.put("schema", "root.ck3.continuity-window/v1"); row.put("machine_id", MACHINE);
            row.put("sequence", 0); row.put("window_id", 1); row.put("start_date_raw", RAW); row.put("target_date_raw", RAW + 100 * 24);
            row.put("target_days", 100); row.put("status", "running"); row.put("last_settled_cycles", 0); row.put("last_settled_date_raw", RAW);
            state = DomainBodies.reduceImport(ContinuityState.fromJson(row, MACHINE), bodyRef);
        }
        private static DomainBodies.BodyRef bodyRef(ExactRef ref) { return new DomainBodies.BodyRef(DomainBodies.Slot.CROWN, CONTRACT, ref, nativeId(ref), List.of(PRODUCER)); }
        private void replaceBody(byte[] replacement) { body = replacement.clone(); bodyRef = bodyRef(ref("another-original-body", body)); state = DomainBodies.reduceImport(state, bodyRef); }
        @Override public void requireWriter(Path expected) throws IOException { if (rejectWriter || !LOCK.equals(expected)) throw new IOException("another writer/escaped session"); }
        @Override public WriterContracts.Pin capturePin(ExactRef reference, int maximumBytes) { return new WriterContracts.Pin(reference, nativeId(reference)); }
        @Override public void verifyPin(WriterContracts.Pin pin) { }
        @Override public WriterContracts.Head head() { return new WriterContracts.Head(state, List.of(), List.of(), List.of(), false); }
        @Override public ExactRef persistedHead() { return ref("fixture-head", state.canonicalBytes()); }
        @Override public WriterContracts.Prepared preview(WriterContracts.Request request) throws IOException { throw new IOException("no action writer permitted"); }
        @Override public WriterContracts.Receipt commit(WriterContracts.Prepared prepared) throws IOException { throw new IOException("no action writer permitted"); }
        @Override public DomainBodies.Read readDomain(DomainBodies.Slot slot) { assertEquals(DomainBodies.Slot.CROWN, slot); return new DomainBodies.Available(bodyRef, ContinuityJson.canonical(object(body)), persistedHead(), List.of()); }
        @Override public DomainBodies.PreparedImport previewImport(DomainBodies.ImportRequest request) throws IOException {
            lastImport = request;
            String checked = fixture.service.verify(head(), Optional.of(bodyRef), request, fixture.output);
            return new DomainBodies.PreparedImport(head(), request, new WriterContracts.Pin(request.originalBody(), nativeId(request.originalBody())), List.of(), List.of(), checked);
        }
        @Override public WriterContracts.Receipt commitImport(DomainBodies.PreparedImport prepared) throws IOException {
            if (expireBeforeCommit) fixture.now = DEADLINE;
            String checked = fixture.service.verify(head(), Optional.of(bodyRef), prepared.request(), fixture.output);
            assertEquals(prepared.preconditionDigest(), checked); commits++;
            if (noChange) return new WriterContracts.Receipt(WriterContracts.Disposition.NO_CHANGE, state, "b".repeat(64), 0, false);
            body = fixture.output.clone(); bodyRef = bodyRef(prepared.request().originalBody()); state = DomainBodies.reduceImport(state, bodyRef);
            return new WriterContracts.Receipt(WriterContracts.Disposition.COMMITTED, state, "b".repeat(64), 1, false);
        }
    }
    private static WriterContracts.FileIdentity nativeId(ExactRef ref) { return new WriterContracts.FileIdentity("1", "9007199254740993", "134371375868945259", "2026-10-23T17:40:00Z", ref.bytes()); }
    private static Set<String> fields(ObjectNode row) { return row.properties().stream().map(java.util.Map.Entry::getKey).collect(java.util.stream.Collectors.toUnmodifiableSet()); }
    private static ObjectNode object(byte[] raw) { return (ObjectNode) StrictJson.parse(raw, CrownRetryPublication.MAX_BODY_BYTES); }
    private static byte[] bytes(String text) { return text.getBytes(StandardCharsets.UTF_8); }
    private static ExactRef ref(String path, byte[] raw) {
        try { return new ExactRef(path, raw.length, HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw))); }
        catch (NoSuchAlgorithmException impossible) { throw new IllegalStateException(impossible); }
    }
}
