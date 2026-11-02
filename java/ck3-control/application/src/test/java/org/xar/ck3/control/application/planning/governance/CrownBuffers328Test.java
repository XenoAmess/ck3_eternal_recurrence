package org.xar.ck3.control.application.planning.governance;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.continuity.ContinuityJson;
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

/** Pure per-reduction buffer reuse boundaries. No actual sources, storage, permissions or Game. */
final class CrownBuffers328Test {
    private static final String MACHINE="m7-crown-software-fixture";
    private static final String BUILD="1.20.0.4/build25734779-fixture";
    private static final long RAW=53_169_072;
    private static final BigInteger ACTOR=BigInteger.valueOf(73);
    private static final ExactRef RUNTIME=ref("fixture-runtime",bytes("fixture-runtime"));
    private static final G2Source SOURCE=new G2Source(MACHINE,"2026-10-23T17:40:00Z",BUILD,ref("fixture-source",bytes("fixture-native")));

    @Test void blockedRetryPreservesOriginalUnknownValuesAndAllInputArrays() {
        Fixture f=new Fixture();byte[] p=f.previous.clone(),c=f.crown.clone(),t=f.terms.clone();
        var material=f.material();byte[] actual=CrownRetryPublication.reduce(f.input,material);
        ObjectNode expected=object(p);var hint=expected.putObject("retry");
        hint.putObject("source_context").put("bridge_pid",321).put("episode_run_id","original-campaign-episode");
        hint.put("actor_character_id",ACTOR);hint.put("law_key","crown_authority_1");
        hint.put("observed_date_raw",RAW);hint.put("retry_date_raw",RAW+11*24);
        assertArrayEquals(ContinuityJson.canonical(expected),actual);
        assertArrayEquals(p,f.previous);assertArrayEquals(c,f.crown);assertArrayEquals(t,f.terms);
        assertArrayEquals(p,material.previousBody());assertArrayEquals(c,material.crownReadback());assertArrayEquals(t,material.finalTermsConsume());
    }

    @Test void noActionStillDecodesFullTermsAndPreservesUnknownResolvedValues() {
        Fixture base=new Fixture();var old=CrownAuthorityCodec.decodeReadback(base.crown);
        byte[] unavailable=CrownAuthorityCodec.encodeReadback(new CrownAuthorityPolicy.Readback(old.schema(),false,old.paused(),old.groupKey(),old.activeLawKey(),old.candidates(),old.resources(),old.titleSuccessors(),old.sourceFrame(),old.readOnly(),old.advertised()));
        Fixture f=new Fixture(base.previous,unavailable,base.terms);ObjectNode expected=object(f.previous);expected.putNull("retry");
        assertArrayEquals(ContinuityJson.canonical(expected),CrownRetryPublication.reduce(f.input,f.material()));
        var wrong=object(f.terms);wrong.put("schema","bad-consume");Fixture invalid=new Fixture(f.previous,unavailable,StrictJson.canonical(wrong));
        assertEquals("law consume schema differs",assertThrows(IllegalArgumentException.class,()->CrownRetryPublication.reduce(invalid.input,invalid.material())).getMessage());
    }

    @Test void constructorAndGetterAliasesCannotChangeRepeatedReductions() {
        Fixture f=new Fixture();var material=f.material();byte[] expected=CrownRetryPublication.reduce(f.input,material);
        f.previous[0]='!';f.crown[0]='!';f.terms[0]='!';
        material.previousBody()[0]='?';material.crownReadback()[0]='?';material.finalTermsConsume()[0]='?';
        assertArrayEquals(expected,CrownRetryPublication.reduce(f.input,material));
        expected[0]='!';assertEquals('{',CrownRetryPublication.reduce(f.input,material)[0]);
    }

    @Test void allOriginalChecksumsStayBeforePreviousParseAndBothDecoders() {
        Fixture base=new Fixture();Fixture malformedPrevious=new Fixture(bytes("{"),base.crown,base.terms);
        byte[] wrongCrown=base.crown.clone();wrongCrown[0]='!';
        assertEquals("actual original source bytes/SHA differ",assertThrows(IllegalArgumentException.class,()->CrownRetryPublication.reduce(malformedPrevious.input,new CrownRetryPublication.Material(malformedPrevious.input.currentObserved(),SOURCE,malformedPrevious.previous,wrongCrown,base.terms))).getMessage());
        Fixture malformedCrown=new Fixture(base.previous,bytes("{"),base.terms);byte[] wrongTerms=base.terms.clone();wrongTerms[0]='!';
        assertEquals("actual original source bytes/SHA differ",assertThrows(IllegalArgumentException.class,()->CrownRetryPublication.reduce(malformedCrown.input,new CrownRetryPublication.Material(malformedCrown.input.currentObserved(),SOURCE,base.previous,malformedCrown.crown,wrongTerms))).getMessage());
        var wrongSource=new G2Source(MACHINE,SOURCE.observedAtUtc(),"other-build",SOURCE.sourceRef());
        assertEquals("retry source material must bind the complete current Native/Driver frame",assertThrows(IllegalArgumentException.class,()->CrownRetryPublication.reduce(base.input,new CrownRetryPublication.Material(base.input.currentObserved(),wrongSource,bytes("!"),bytes("!"),bytes("!")))).getMessage());
    }

    @Test void unresolvedPendingIsRejectedBeforeMalformedCrownAndTerms() {
        Fixture base=new Fixture();var pending=object(base.previous);pending.putObject("pending").put("stage","UNKNOWN").put("ack",true);
        Fixture f=new Fixture(StrictJson.canonical(pending),bytes("{"),bytes("{"));
        assertEquals("an original pending/UNKNOWN Crown command cannot publish a replacement retry",assertThrows(IllegalArgumentException.class,()->CrownRetryPublication.reduce(f.input,f.material())).getMessage());
    }

    @Test void malformedCrownPrecedesTermsAndFullAfterFrameBindingRemains() {
        Fixture base=new Fixture();var badCrown=object(base.crown);badCrown.put("unexpected",true);
        Fixture f=new Fixture(base.previous,StrictJson.canonical(badCrown),bytes("{"));
        String expected=assertThrows(IllegalArgumentException.class,()->CrownAuthorityCodec.decodeReadback(f.crown)).getMessage();
        assertEquals(expected,assertThrows(IllegalArgumentException.class,()->CrownRetryPublication.reduce(f.input,f.material())).getMessage());
        var drift=object(base.terms);((ObjectNode)drift.get("after_snapshot")).put("episode_run_id","other-episode");
        Fixture changed=new Fixture(base.previous,base.crown,StrictJson.canonical(drift));
        assertEquals("full final-terms after snapshot crossed original public/native/episode/actor identity",assertThrows(IllegalArgumentException.class,()->CrownRetryPublication.reduce(changed.input,changed.material())).getMessage());
    }

    private static final class Fixture {
        private final byte[] previous,crown,terms;
        private final CrownRetryPublication.Input input;
        private Fixture(){this(bytes("{\"pending\":null,\"resolved\":{\"unknown\":{\"rows\":[1,true,null,\"雪\"]},\"ack\":true},\"retry\":{\"old\":7}}"),crown(),nativeConsume());}
        private Fixture(byte[] previous,byte[] crown,byte[] terms){
            this.previous=previous;this.crown=crown;this.terms=terms;
            var observed=identity("134371375868945259",RAW,8,13);
            input=new CrownRetryPublication.Input(observed,observed,SOURCE,ref("fixture-previous",previous),ref("fixture-crown",crown),ref("fixture-crown-receipt",bytes("crown-receipt")),ref("fixture-terms",terms),ref("fixture-terms-receipt",bytes("terms-receipt")),List.of(RUNTIME));
        }
        private CrownRetryPublication.Material material(){return new CrownRetryPublication.Material(input.currentObserved(),SOURCE,previous,crown,terms);}
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
    private static ObjectNode object(byte[] raw) { return (ObjectNode) StrictJson.parse(raw, CrownRetryPublication.MAX_BODY_BYTES); }
    private static byte[] bytes(String text) { return text.getBytes(StandardCharsets.UTF_8); }
    private static ExactRef ref(String path, byte[] raw) {
        try { return new ExactRef(path, raw.length, HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw))); }
        catch (NoSuchAlgorithmException impossible) { throw new IllegalStateException(impossible); }
    }
}
