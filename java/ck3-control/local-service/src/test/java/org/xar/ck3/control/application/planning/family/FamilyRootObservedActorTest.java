package org.xar.ck3.control.application.planning.family;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.IntegerValue;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;

/** Public observed-actor DATA regression. No Session, read authority, publisher proof or negative-ID ROOT is minted. */
final class FamilyRootObservedActorTest {
    private static final BigInteger NATIVE = BigInteger.valueOf(17), DATE = BigInteger.valueOf(53182008);
    private static final ExactRef ORIGINAL = new ExactRef("synthetic-family-public-frame/root-original", 1, "a".repeat(64));
    private static final int ORIGINAL_ROOT_ACTOR = 12345;

    @Test void observedSignedActorReachesColdSerdeAndPureConsumerWithoutReinterpretingItsBits() {
        for (int actor : List.of(Integer.MIN_VALUE, -2, 0, ORIGINAL_ROOT_ACTOR, Integer.MAX_VALUE)) {
            ObservationIdentity target = observed(actor, 57);
            FamilyRootCurrentFrame data = FamilyRootCurrentFrame.observed(ORIGINAL,
                    observed(ORIGINAL_ROOT_ACTOR, 56), target);
            assertEquals(BigInteger.valueOf(actor), target.frame().identity().player());
            assertEquals(BigInteger.valueOf(actor), data.player());
            Obj cold = DriverJson.object(DriverJson.encode(data.toJson()), DriverJson.MAX_NATIVE_BYTES);
            JsonNode wire = DriverJson.toNode(cold).get("played_character_id");
            assertTrue(wire.isIntegralNumber()); assertEquals(BigInteger.valueOf(actor), wire.bigIntegerValue());
            assertEquals(data, FamilyRootCurrentFrame.fromJson(cold));
            Obj originalRoot = retainedRootData();
            Obj currentView = originalRoot.with(FamilyRootCurrentFrame.FIELD, cold);
            assertDoesNotThrow(() -> FamilyRootCurrentFrame.requireSame(currentView, snapshot(actor, 57)));
            assertEquals(new IntegerValue(BigInteger.valueOf(56)), currentView.get("queried_revision"));
            assertEquals(ORIGINAL, FamilyRootCurrentFrame.fromJson(cold).originalRootReceipt());

            // Actual specific ROOT remains positive. Public DATA cannot rewrite that original actor.
            if (actor != ORIGINAL_ROOT_ACTOR)
                assertThrows(IllegalArgumentException.class, () -> FamilyChildPolicy.split(currentView, snapshot(actor, 57)));
            else {
                Obj split = FamilyChildPolicy.split(currentView, snapshot(actor, 57));
                assertEquals(new IntegerValue(BigInteger.valueOf(87654)), split.get("subject_character_id"));
                assertEquals(new IntegerValue(BigInteger.valueOf(57)), split.get("source_revision"));
            }
        }
    }

    @Test void absentSentinelUnsignedAliasesAndWrongJsonTypesCannotBecomeObservedActors() {
        FamilyRootCurrentFrame valid = FamilyRootCurrentFrame.observed(ORIGINAL,
                observed(ORIGINAL_ROOT_ACTOR, 56), observed(-2, 57));
        for (BigInteger actor : List.of(BigInteger.valueOf(-1), BigInteger.valueOf(Integer.MIN_VALUE).subtract(BigInteger.ONE),
                BigInteger.valueOf(Integer.MAX_VALUE).add(BigInteger.ONE), new BigInteger("4294967294"), new BigInteger("4294967295"))) {
            assertThrows(IllegalArgumentException.class, () -> withActor(valid, actor));
            ObjectNode row = frameNode(valid); row.put("played_character_id", actor);
            assertThrows(IllegalArgumentException.class, () -> FamilyRootCurrentFrame.fromJson(object(row)));
        }
        for (JsonNode invalid : List.of(StrictJson.parse("true".getBytes(java.nio.charset.StandardCharsets.UTF_8)),
                StrictJson.parse("-2.0".getBytes(java.nio.charset.StandardCharsets.UTF_8)),
                StrictJson.parse("\"-2\"".getBytes(java.nio.charset.StandardCharsets.UTF_8)),
                com.fasterxml.jackson.databind.node.NullNode.instance,
                StrictJson.object(), com.fasterxml.jackson.databind.node.JsonNodeFactory.instance.arrayNode())) {
            ObjectNode row = frameNode(valid); row.set("played_character_id", invalid);
            assertThrows(IllegalArgumentException.class, () -> FamilyRootCurrentFrame.fromJson(object(row)));
        }
        ObjectNode missing = frameNode(valid); missing.remove("played_character_id");
        assertThrows(IllegalArgumentException.class, () -> FamilyRootCurrentFrame.fromJson(object(missing)));
        assertThrows(IllegalArgumentException.class, () -> withActor(valid, null));
    }

    @Test void exactAndReadExtendedSnapshotConsumersBothValidateTheSamePublicActorContract() {
        FamilyRootCurrentFrame data = FamilyRootCurrentFrame.observed(ORIGINAL,
                observed(ORIGINAL_ROOT_ACTOR, 56), observed(-2, 57));
        Obj root = retainedRootData().with(FamilyRootCurrentFrame.FIELD, data.toJson());
        for (int revision : List.of(56, 57)) {
            for (JsonNode invalid : List.of(com.fasterxml.jackson.databind.node.IntNode.valueOf(-1),
                    com.fasterxml.jackson.databind.node.BigIntegerNode.valueOf(new BigInteger("2147483648")),
                    com.fasterxml.jackson.databind.node.BooleanNode.TRUE,
                    com.fasterxml.jackson.databind.node.DoubleNode.valueOf(-2.0),
                    com.fasterxml.jackson.databind.node.TextNode.valueOf("-2"),
                    com.fasterxml.jackson.databind.node.NullNode.instance)) {
                ObjectNode snapshot = snapshotNode(-2, revision);
                ((ObjectNode) snapshot.get("played_character")).set("character_id", invalid);
                assertThrows(IllegalArgumentException.class, () -> FamilyRootCurrentFrame.requireSame(root, object(snapshot)));
            }
            ObjectNode absent = snapshotNode(-2, revision); ((ObjectNode) absent.get("played_character")).remove("character_id");
            assertThrows(IllegalArgumentException.class, () -> FamilyRootCurrentFrame.requireSame(root, object(absent)));
        }
        assertThrows(IllegalArgumentException.class, () -> FamilyRootCurrentFrame.requireSame(root, snapshot(0, 57)));
        ObjectNode changed = snapshotNode(-2, 57); changed.put("native_revision", 18);
        assertThrows(IllegalArgumentException.class, () -> FamilyRootCurrentFrame.requireSame(root, object(changed)));
        ObjectNode changedDate = snapshotNode(-2, 57); changedDate.put("date_raw", DATE.add(BigInteger.ONE));
        assertThrows(IllegalArgumentException.class, () -> FamilyRootCurrentFrame.requireSame(root, object(changedDate)));
    }

    @Test void originalReferencesRevisionOrderDateAndSchemaRemainStrict() {
        FamilyRootCurrentFrame data = FamilyRootCurrentFrame.observed(ORIGINAL,
                observed(ORIGINAL_ROOT_ACTOR, 56), observed(-2, 57));
        assertThrows(IllegalArgumentException.class, () -> new FamilyRootCurrentFrame(ORIGINAL, BigInteger.valueOf(58),
                data.snapshotId(), data.publicRevision(), data.nativeRevision(), data.dateRaw(), data.episodeRunId(), data.player()));
        assertThrows(IllegalArgumentException.class, () -> new FamilyRootCurrentFrame(ORIGINAL, data.originalRevision(),
                data.snapshotId(), data.publicRevision(), BigInteger.ZERO, data.dateRaw(), data.episodeRunId(), data.player()));
        for (BigInteger date : List.of(BigInteger.valueOf(-1), BigInteger.ONE.shiftLeft(32)))
            assertThrows(IllegalArgumentException.class, () -> new FamilyRootCurrentFrame(ORIGINAL, data.originalRevision(),
                    data.snapshotId(), data.publicRevision(), data.nativeRevision(), date, data.episodeRunId(), data.player()));
        ObjectNode extra = frameNode(data); extra.put("ready", true);
        assertThrows(IllegalArgumentException.class, () -> FamilyRootCurrentFrame.fromJson(object(extra)));
        ObjectNode schema = frameNode(data); schema.put("schema", "wrong-schema");
        assertThrows(IllegalArgumentException.class, () -> FamilyRootCurrentFrame.fromJson(object(schema)));
        assertEquals(ORIGINAL.toJson(), frameNode(data).get("original_root_receipt"));
    }

    private static FamilyRootCurrentFrame withActor(FamilyRootCurrentFrame f, BigInteger actor) {
        return new FamilyRootCurrentFrame(f.originalRootReceipt(), f.originalRevision(), f.snapshotId(), f.publicRevision(),
                f.nativeRevision(), f.dateRaw(), f.episodeRunId(), actor);
    }
    private static ObservationIdentity observed(int actor, int revision) {
        var identity = new JointBudgetSelector.Frame(BigInteger.valueOf(actor), NATIVE, DATE);
        var frame = new JointBudgetSelector.ProposalFrame(identity, "native:17", BigInteger.valueOf(revision), "family-public-data");
        return new ObservationIdentity("synthetic-family-machine", new GameGeneration(991,
                new PythonOnlyUInt64(new BigInteger("133700000000000001"))), frame, 1);
    }
    private static ObjectNode frameNode(FamilyRootCurrentFrame data) { return (ObjectNode) DriverJson.toNode(data.toJson()); }
    private static Obj snapshot(int actor, int revision) { return object(snapshotNode(actor, revision)); }
    private static ObjectNode snapshotNode(int actor, int revision) {
        ObjectNode n = StrictJson.object().put("snapshot_id", "native:17").put("revision", revision).put("native_revision", NATIVE)
                .put("date_raw", DATE).put("episode_run_id", "family-public-data");
        n.putObject("played_character").put("character_id", actor); return n;
    }
    private static Obj retainedRootData() {
        ObjectNode n = StrictJson.object().put("status", "available").put("queried_snapshot_id", "native:17")
                .put("queried_native_revision", NATIVE).put("queried_revision", 56);
        ObjectNode context = n.putObject("campaign_root_context").put("player_character_id", ORIGINAL_ROOT_ACTOR);
        var partition = context.putArray("held_title_partition");
        partition.addObject().put("primary", true).put("first_heir_character_id", 98765).putObject("title").put("title_id", 10);
        partition.addObject().put("primary", false).put("first_heir_character_id", 87654).putObject("title").put("title_id", 11);
        return object(n);
    }
    private static Obj object(ObjectNode n) { return DriverJson.object(StrictJson.canonical(n), DriverJson.MAX_NATIVE_BYTES); }
}
