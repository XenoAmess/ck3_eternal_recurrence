package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.math.BigInteger;
import java.time.Instant;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;

/** Strict child DATA serialization only. These references mint neither a private M3 cause nor a pending publication. */
final class DriverPendingEpisodeProjectionTest {
    private static final String DIGEST="a".repeat(64);
    private static final ExactRef ORIGINAL=new ExactRef("pure-projection-test-original.json",17,DIGEST);
    private static DriverPendingEpisodeProjection value() {
        return new DriverPendingEpisodeProjection(9007199254740990L,17,DIGEST,9007199254740991L,18,
                new GameGeneration(42,new PythonOnlyUInt64(new BigInteger("18446744073709551615"))),
                "pure-projection-test",Instant.parse("2026-10-24T04:23:00Z"),"old-run",BigInteger.valueOf(73),
                "new-run",BigInteger.valueOf(74),ORIGINAL,ORIGINAL,ORIGINAL,ORIGINAL,ORIGINAL);
    }
    @Test void soleClosedCodecPreservesMachineTimeVersionAndFullBirthWithoutGrantingPublication() {
        var original=value();var decoded=DriverPendingEpisodeProjection.decode(original.encode());assertEquals(original,decoded);
        assertEquals(original.toJson(),DriverJson.object(original.encode(),262144));
        assertEquals(new Text("18446744073709551615"),object(original.toJson().get("game"),"Game").get("creation_filetime"));
        assertEquals("pure-projection-test",decoded.machineId());assertEquals(original.observedAtUtc(),decoded.observedAtUtc());
        assertEquals(original,new DriverPendingEpisodeProjection.Prepared(original,
                new ExactRef("pure-projection-child.json",original.encode().length,DriverJson.sha256(original.encode()))).projection());
    }
    @Test void booleansFloatsMissingFieldsExtraAliasesAndSubjectDriftCannotDecodeAsQualifiedChildData() {
        var original=value().toJson();
        assertThrows(IllegalArgumentException.class,()->DriverPendingEpisodeProjection.fromJson(original.with("before_version",new Bool(true))));
        assertThrows(IllegalArgumentException.class,()->DriverPendingEpisodeProjection.decode(new String(value().encode(),java.nio.charset.StandardCharsets.UTF_8)
                .replace("9007199254740990","9007199254740990.0").getBytes(java.nio.charset.StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class,()->DriverPendingEpisodeProjection.fromJson(original.with("unexpected_alias",new Text("no"))));
        var missing=new java.util.LinkedHashMap<String,Value>(original.members());missing.remove("machine_id");
        assertThrows(IllegalArgumentException.class,()->DriverPendingEpisodeProjection.fromJson(new Obj(missing)));
        assertThrows(IllegalArgumentException.class,()->DriverPendingEpisodeProjection.fromJson(original.with("new_actor",original.get("old_actor"))));
        assertThrows(IllegalArgumentException.class,()->DriverPendingEpisodeProjection.fromJson(original.with("new_episode_run_id",original.get("old_episode_run_id"))));
        assertThrows(IllegalArgumentException.class,()->DriverPendingEpisodeProjection.fromJson(original.with("after_epoch",original.get("before_epoch"))));
    }

    @Test void signedNativeRolesPreserveNumericWireAndRejectAbsenceAndUnsignedAliases() {
        int[][] pairs={{73,0},{73,-2},{73,Integer.MIN_VALUE},{73,Integer.MAX_VALUE},{0,74},{-2,74},{Integer.MIN_VALUE,74}};
        for(int[] pair:pairs) {
            var wire=value().toJson().with("old_actor",new IntegerValue(BigInteger.valueOf(pair[0])))
                    .with("new_actor",new IntegerValue(BigInteger.valueOf(pair[1])));
            var actual=DriverPendingEpisodeProjection.fromJson(wire);
            assertEquals(BigInteger.valueOf(pair[0]),actual.oldActor());assertEquals(BigInteger.valueOf(pair[1]),actual.newActor());
            assertEquals(actual,DriverPendingEpisodeProjection.decode(actual.encode()));
            assertEquals(new IntegerValue(BigInteger.valueOf(pair[1])),actual.toJson().get("new_actor"));
        }
        var invalid=java.util.List.<Value>of(new IntegerValue(BigInteger.valueOf(-1)),
                new IntegerValue(new BigInteger("2147483648")),new IntegerValue(new BigInteger("-2147483649")),
                new IntegerValue(new BigInteger("4294967294")),new Bool(true),new Text("74"),Nil.INSTANCE);
        for(String role:java.util.List.of("old_actor","new_actor")) {
            for(Value value:invalid)assertThrows(IllegalArgumentException.class,()->DriverPendingEpisodeProjection.fromJson(value().toJson().with(role,value)));
            var absent=new java.util.LinkedHashMap<String,Value>(value().toJson().members());absent.remove(role);
            assertThrows(IllegalArgumentException.class,()->DriverPendingEpisodeProjection.fromJson(new Obj(absent)));
            var node=org.xar.ck3.control.contracts.StrictJson.parse(value().encode(),262144);
            ((com.fasterxml.jackson.databind.node.ObjectNode)node).put(role,74.0);
            assertThrows(IllegalArgumentException.class,()->DriverPendingEpisodeProjection.decode(org.xar.ck3.control.contracts.StrictJson.canonical(node,262144)));
        }
    }
}
