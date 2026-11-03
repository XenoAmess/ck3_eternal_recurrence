package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Locale;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;

/** NONBLIND owner tests for candidate ec4cd20e; literal DATA only, no source/issuer qualification. */
final class PublicSnapshotPlanningParsedOwnerTest {
    private static final String PUBLIC_FULL="""
        {"format_version":1,"snapshot_id":"owner-literal","revision":"9007199254740993",
         "native_revision":"18446744073709551615","date_raw":53144328,"paused":true,"map_ready":true,"speed":3,
         "episode_run_id":"owner-episode","episode_character_id":73,"played_character":null,
         "active_wars":[],"player_armies":[],"diagnostics":{},"active_event":null,
         "pending_character_interaction":null,"one_life_terminal_reason":null,
         "native_command_history":[{"index":1,"command":"owner-opaque-history","ok":false,
          "result":{"label":"retained","signed_zero":-0.0,"decimal":1.2300e+4}}],
         "native_rollback_war_failure":null,"native_rollback_war_failures":[]}
        """;
    private static final String NUMERIC_FULL="""
        {"format_version":1,"snapshot_id":"owner-literal","revision":9007199254740993,
         "native_revision":18446744073709551615,"date_raw":53144328,"paused":true,"map_ready":true,"speed":3,
         "episode_run_id":"owner-episode","episode_character_id":73,"played_character":null,
         "active_wars":[],"player_armies":[],"diagnostics":{},"active_event":null,
         "pending_character_interaction":null,"one_life_terminal_reason":null,
         "native_command_history":[{"index":1,"command":"owner-opaque-history","ok":false,
          "result":{"label":"retained","signed_zero":-0.0,"decimal":1.2300e+4}}],
         "native_rollback_war_failure":null,"native_rollback_war_failures":[]}
        """;
    private static final String PUBLIC_SEMANTIC="""
        {"format_version":1,"snapshot_id":"owner-semantic","revision":"9007199254740993",
         "native_revision":"18446744073709551615","date_raw":53144328,"paused":true,"map_ready":true,"speed":3,
         "episode_run_id":"owner-episode","episode_character_id":73,
         "active_wars":[],"player_armies":[],"diagnostics":{},"active_event":null,
         "pending_character_interaction":null,"one_life_terminal_reason":null}
        """;
    private static final String NUMERIC_SEMANTIC="""
        {"format_version":1,"snapshot_id":"owner-semantic","revision":9007199254740993,
         "native_revision":18446744073709551615,"date_raw":53144328,"paused":true,"map_ready":true,"speed":3,
         "episode_run_id":"owner-episode","episode_character_id":73,
         "active_wars":[],"player_armies":[],"diagnostics":{},"active_event":null,
         "pending_character_interaction":null,"one_life_terminal_reason":null}
        """;
    private static final String MARKER="xar_java_snapshot_projection";
    private static final String MARKER_SCHEMA="xar.java-public-snapshot-projection/v1";

    @Test void fullHistoryLiteralRestoresOnlyDeclaredIdentityRoles() {
        RawJson input=raw(PUBLIC_FULL);Obj expected=parse(NUMERIC_FULL);
        Obj planned=planning(input);
        assertEquals(expected,planned);assertEquals(expected,PublicSnapshotCodec.decode(input));
        assertEquals(new BigInteger("9007199254740993"),integer(planned.get("revision"),"revision"));
        assertEquals(new BigInteger("18446744073709551615"),integer(planned.get("native_revision"),"native_revision"));
        assertEquals(expected.get("native_command_history"),planned.get("native_command_history"));
        assertSame(Nil.INSTANCE,planned.get("played_character"));
        assertSame(Nil.INSTANCE,planned.get("native_rollback_war_failure"));
        assertEquals(new Arr(List.of()),planned.get("native_rollback_war_failures"));
    }

    @Test void absentTranscriptsUseSemanticLaneAndNullIsStillPresent() {
        RawJson input=raw(PUBLIC_SEMANTIC);Obj expected=parse(NUMERIC_SEMANTIC);
        assertEquals(expected,planning(input));assertEquals(expected,PublicSnapshotCodec.decodeSemanticOnly(input));
        assertFalse(planning(input).members().containsKey("played_character"));
        IllegalArgumentException full=assertThrows(IllegalArgumentException.class,()->PublicSnapshotCodec.decode(input));
        contains(full,"explicit original snapshot field required: native_command_history");
        for(String field:List.of("native_command_history","native_rollback_war_failure","native_rollback_war_failures")) {
            RawJson explicitNull=raw(parse(PUBLIC_SEMANTIC).with(field,Nil.INSTANCE));
            IllegalArgumentException failure=assertThrows(IllegalArgumentException.class,
                    ()->PublicSnapshotCodec.decodeSemanticOnly(explicitNull));
            contains(failure,"private semantic snapshot contains transcript field: "+field);
        }
        assertEquals(expected.with("played_character",Nil.INSTANCE),
                planning(raw(parse(PUBLIC_SEMANTIC).with("played_character",Nil.INSTANCE))));
    }

    @Test void opaqueNumericTokensRespectTheGenericPublicNumberGate() {
        Obj opaque=parse("{\"signed_zero\":-0.0,\"decimal\":1.2300e+4,\"safe\":9007199254740991,\"identity_looking_text\":\"1844674407370955161600000\"}");
        Obj result=planning(raw(parse(PUBLIC_FULL).with("opaque",opaque)));
        assertEquals(opaque,result.get("opaque"));
        Obj retained=object(result.get("opaque"),"opaque");
        assertEquals("-0.0",assertInstanceOf(DecimalValue.class,retained.get("signed_zero")).token());
        assertEquals("1.2300e+4",assertInstanceOf(DecimalValue.class,retained.get("decimal")).token());
        assertEquals(new BigInteger("9007199254740991"),integer(retained.get("safe"),"safe"));
        assertEquals(new Text("1844674407370955161600000"),retained.get("identity_looking_text"));
        // The wrong revision would fail later. The independent generic gate must reject this numeric leaf first.
        Obj unsafe=parse(PUBLIC_FULL).with("revision",new Bool(false)).with("opaque",parse("{\"huge\":9007199254740993}"));
        assertFullEntriesReject(unsafe,"unqualified unsafe numeric public role at /opaque/huge");
        Obj nonfinite=parse(PUBLIC_FULL).with("revision",new Bool(false)).with("opaque",parse("{\"huge\":1e9999}"));
        assertFullEntriesReject(nonfinite,"nonfinite public float at /opaque/huge");
    }

    @Test void identityTextIsCanonicalAndUnknownStringsStayOpaque() {
        for(String literal:List.of("1","1.0","true","\"01\"","\"-0\"","\"-1\"","\"1e2\"")) {
            Value value=parse("{\"v\":"+literal+"}").get("v");
            assertFullEntriesReject(parse(PUBLIC_FULL).with("revision",value),"canonical decimal identity string required: revision");
        }
        assertFullEntriesReject(parse(PUBLIC_FULL).with("revision",Nil.INSTANCE),"required snapshot identity absent or null: revision");
        assertFullEntriesReject(parse(PUBLIC_FULL).with("diagnostics",parse("{\"connection_generation\":\"18446744073709551616\"}")),
                "source uint64 role out of range: diagnostics/connection_generation");
        Obj extra=parse(PUBLIC_FULL).with("unrelated_identity",new Text("00018446744073709551616"));
        assertEquals(new Text("00018446744073709551616"),planning(raw(extra)).get("unrelated_identity"));
    }

    @Test void projectionMarkerRequiresExactObjectSchemaAndVersion() {
        Obj marker=parse("{\"schema\":\""+MARKER_SCHEMA+"\",\"observation_version\":4}");
        Obj expected=parse(NUMERIC_FULL).with("episode_projection",new Text("native_campaign"));
        Obj valid=parse(PUBLIC_FULL).with("episode_projection",new Text("native_campaign")).with(MARKER,marker);
        assertEquals(expected,planning(raw(valid)));assertEquals(expected,PublicSnapshotCodec.decode(raw(valid)));
        assertFalse(planning(raw(valid)).members().containsKey(MARKER));
        assertFullEntriesReject(parse(PUBLIC_FULL).with(MARKER,Nil.INSTANCE),"explicit public snapshot projection object required");
        for(String literal:List.of("{}","{\"schema\":\"wrong\",\"observation_version\":4}",
                "{\"schema\":\""+MARKER_SCHEMA+"\",\"observation_version\":\"4\"}",
                "{\"schema\":\""+MARKER_SCHEMA+"\",\"observation_version\":4.0}",
                "{\"schema\":\""+MARKER_SCHEMA+"\",\"observation_version\":4,\"extra\":null}"))
            assertFullEntriesReject(parse(PUBLIC_FULL).with(MARKER,parse(literal)),"unsupported public snapshot projection representation");
        assertFullEntriesReject(parse(PUBLIC_FULL).with(MARKER,marker.with("observation_version",new IntegerValue(new BigInteger("9007199254740993")))),
                "unqualified unsafe numeric public role at /xar_java_snapshot_projection/observation_version");
    }

    @Test void semanticSizeGatePrecedesDepthOnlyAtDirectSemanticEntry() {
        String deep="[".repeat(70)+"0"+"]".repeat(70);
        String document="{\"deep\":"+deep+",\"padding\":\""+"x".repeat(8*1024*1024)+"\"}";
        byte[] bytes=document.getBytes(StandardCharsets.UTF_8);
        assertTrue(bytes.length>8*1024*1024&&bytes.length<RawJson.MAXIMUM_BYTES);
        // RawJson permits nesting up to 1000, so this is real constructible DATA, not a mocked RawJson.
        RawJson input=assertDoesNotThrow(()->new RawJson(bytes));
        IllegalArgumentException semantic=assertThrows(IllegalArgumentException.class,()->PublicSnapshotCodec.decodeSemanticOnly(input));
        contains(semantic,"private semantic snapshot exceeds the 8 MiB UTF-8 read bound");
        assertDepthFailure(assertThrows(IllegalArgumentException.class,()->PublicSnapshotCodec.decodePlanningSnapshotData(input)));
        assertDepthFailure(assertThrows(IllegalArgumentException.class,()->PublicSnapshotCodec.decode(input)));
    }

    private static Obj planning(RawJson input) { return parse(PublicSnapshotCodec.decodePlanningSnapshotData(input)); }
    private static Obj parse(String literal) { return parse(raw(literal)); }
    private static Obj parse(RawJson input) { return DriverJson.object(input.bytes(),RawJson.MAXIMUM_BYTES); }
    private static RawJson raw(String literal) { return new RawJson(literal.getBytes(StandardCharsets.UTF_8)); }
    private static RawJson raw(Obj value) { return new RawJson(DriverJson.encode(value)); }
    private static void assertFullEntriesReject(Obj value,String message) {
        RawJson input=raw(value);
        contains(assertThrows(IllegalArgumentException.class,()->PublicSnapshotCodec.decodePlanningSnapshotData(input)),message);
        contains(assertThrows(IllegalArgumentException.class,()->PublicSnapshotCodec.decode(input)),message);
    }
    private static void contains(Throwable failure,String message) { assertTrue(String.valueOf(failure.getMessage()).contains(message),failure::toString); }
    private static void assertDepthFailure(Throwable failure) {
        StringBuilder chain=new StringBuilder();
        for(Throwable item=failure;item!=null;item=item.getCause())chain.append(item.getMessage()).append('\n');
        String diagnostic=chain.toString().toLowerCase(Locale.ROOT);
        assertTrue(diagnostic.contains("depth")||diagnostic.contains("nesting"),chain::toString);
        assertFalse(diagnostic.contains("8 mib"),"the initial full-tree parse must precede the semantic size gate");
    }
}
