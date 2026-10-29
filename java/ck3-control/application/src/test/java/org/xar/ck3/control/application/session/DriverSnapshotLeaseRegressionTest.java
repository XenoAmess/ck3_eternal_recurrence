package org.xar.ck3.control.application.session;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.checkpoint.DriverCheckpointStore;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import static org.junit.jupiter.api.Assertions.*;

/** Complete original business state survives SAVE, and failure releases the real authority lease. */
final class DriverSnapshotLeaseRegressionTest {
    @Test void incompleteActualStateIsForwardedWithoutInventingNullsOrHistory() throws IOException {
        var missing = new DriverStateSnapshot.Incomplete(List.of("managed_restore_transaction_unreconciled", "action_history_not_consolidated"));
        Authority authority = new Authority(missing); var supplier = new FrozenDriverSnapshotSupplier(authority);
        supplier.withFrozen((frozen,publisher) -> { assertSame(missing, frozen); assertTrue(authority.leased); return true; });
        assertFalse(authority.leased); assertEquals(0, authority.published);
    }
    @Test void physicalWriteFailurePropagatesAndReleasesLeaseWithoutPublishing() {
        Authority authority = new Authority(complete("[]", "null", false)); var supplier = new FrozenDriverSnapshotSupplier(authority);
        assertThrows(IOException.class, () -> supplier.withFrozen((frozen,publisher) -> { throw new IOException("actual disk write failed"); }));
        assertFalse(authority.leased); assertEquals(0, authority.published);
    }
    @Test void publicationPreservesRequiredNullMissingSlotsAndOldHistory() throws IOException {
        var old = complete("[{\"index\":1,\"command\":\"original-war-action\",\"unknown_result\":true}]", "{\"real_goal\":\"retain\"}", false);
        var next = resetFailures(complete("[{\"index\":1,\"command\":\"original-war-action\",\"unknown_result\":true},{\"index\":2,\"command\":\"save-checkpoint\"}]", "{\"real_goal\":\"retain\"}", false));
        Authority authority = new Authority(old); var supplier = new FrozenDriverSnapshotSupplier(authority);
        supplier.withFrozen((frozen,publisher) -> { publisher.publish(old, next); return true; });
        assertEquals(1, authority.published); assertSame(next, authority.state); assertFalse(authority.leased);
    }
    @Test void checkpointCannotEraseBusinessStateOrExistingUnknownHistory() {
        var old = complete("[{\"index\":1,\"command\":\"original-war-action\",\"unknown_result\":true}]", "{\"real_goal\":\"retain\"}", false);
        Authority authority = new Authority(old); var supplier = new FrozenDriverSnapshotSupplier(authority);
        var erasedGoal = complete("[{\"index\":1,\"command\":\"original-war-action\",\"unknown_result\":true},{\"index\":2,\"command\":\"save-checkpoint\"}]", "null", false);
        assertThrows(IllegalArgumentException.class, () -> supplier.withFrozen((frozen,publisher) -> { publisher.publish(old, erasedGoal); return true; }));
        var changedHistory = complete("[{\"index\":1,\"command\":\"original-war-action\",\"unknown_result\":false},{\"index\":2,\"command\":\"save-checkpoint\"}]", "{\"real_goal\":\"retain\"}", false);
        assertThrows(IllegalArgumentException.class, () -> supplier.withFrozen((frozen,publisher) -> { publisher.publish(old, changedHistory); return true; }));
        var missingToNull = complete("[{\"index\":1,\"command\":\"original-war-action\",\"unknown_result\":true},{\"index\":2,\"command\":\"save-checkpoint\"}]", "{\"real_goal\":\"retain\"}", true);
        assertThrows(IllegalArgumentException.class, () -> supplier.withFrozen((frozen,publisher) -> { publisher.publish(old, missingToNull); return true; }));
        assertEquals(0, authority.published); assertFalse(authority.leased);
    }
    @Test void sameJsonOutsideTheFrozenLeaseDoesNotAuthorizePublication() {
        var old = complete("[]", "null", false); var unrelated = DriverStateSnapshot.decodeComplete(old.encode());
        var next = complete("[{\"index\":1,\"command\":\"save-checkpoint\"}]", "null", false);
        Authority authority = new Authority(old); var supplier = new FrozenDriverSnapshotSupplier(authority);
        assertThrows(IllegalArgumentException.class, () -> supplier.withFrozen((frozen,publisher) -> { publisher.publish(unrelated, next); return true; }));
        assertFalse(authority.leased); assertEquals(0, authority.published);
    }
    @Test void confirmedSaveClearsOnlyRollbackFailureListAndRejectsRetainedFailures() throws IOException {
        var initial = complete("[]", "{\"real_goal\":\"retain\"}", false);
        var old = new DriverStateSnapshot.Complete(initial.session(), initial.commandHistory(), initial.lastCheckpoint(), new DriverStateSnapshot.Value("{\"war_id\":7}".getBytes(StandardCharsets.UTF_8)),
                initial.managedRestoreTransaction(), initial.successionExpectation(), initial.successionLifecycle(), initial.campaignGoal(),
                new DriverStateSnapshot.Value("[{\"war_id\":7}]".getBytes(StandardCharsets.UTF_8)));
        var appended = complete("[{\"index\":1,\"command\":\"save-checkpoint\"}]", "{\"real_goal\":\"retain\"}", false);
        var invalid = new DriverStateSnapshot.Complete(appended.session(), appended.commandHistory(), appended.lastCheckpoint(), appended.rollbackWarFailure(),
                appended.managedRestoreTransaction(), appended.successionExpectation(), appended.successionLifecycle(), appended.campaignGoal(), old.rollbackWarFailures());
        Authority authority = new Authority(old); var supplier = new FrozenDriverSnapshotSupplier(authority);
        assertThrows(IllegalArgumentException.class, () -> supplier.withFrozen((frozen,publisher) -> { publisher.publish(old, invalid); return true; }));
        supplier.withFrozen((frozen,publisher) -> { publisher.publish(old, resetFailures(appended)); return true; });
        assertEquals(1, authority.published);
    }
    private static DriverStateSnapshot.Complete resetFailures(DriverStateSnapshot.Complete state) {
        return new DriverStateSnapshot.Complete(state.session(), state.commandHistory(), state.lastCheckpoint(), state.rollbackWarFailure(),
                state.managedRestoreTransaction(), state.successionExpectation(), state.successionLifecycle(), state.campaignGoal(),
                new DriverStateSnapshot.Value("[]".getBytes(StandardCharsets.UTF_8)));
    }
    private static DriverStateSnapshot.Complete complete(String history, String goal, boolean lifecycleNull) {
        String raw = "{\"format_version\":2,\"pipe_name\":\"fixture\",\"bridge_pid\":123,\"episode_character_id\":29829,\"episode_run_id\":\"episode-1\","
                + "\"command_history\":" + history + ",\"last_checkpoint\":null,\"rollback_war_failure\":null,\"managed_restore_transaction\":null,\"succession_expectation\":null,\"campaign_goal\":" + goal
                + (lifecycleNull ? ",\"succession_lifecycle\":null" : "") + "}";
        return DriverStateSnapshot.decodeComplete(raw.getBytes(StandardCharsets.UTF_8));
    }
    private static final class Authority implements FrozenDriverSnapshotSupplier.StateAuthority {
        DriverStateSnapshot state; boolean leased; int published;
        Authority(DriverStateSnapshot initial) { state = initial; }
        @Override public synchronized <T> T withFrozen(DriverCheckpointStore.SnapshotWork<T> work) throws IOException {
            if (leased) throw new IOException("state lease already held"); leased = true;
            try {
                return work.run(state, (expected,next) -> {
                    if (!leased || state != expected) throw new IOException("actual state changed during checkpoint");
                    state = next; published++;
                });
            } finally { leased = false; }
        }
    }
    @Test void restartKnownOriginalAcceptsOnlyFullTypedJsonAcrossObjectFieldOrder() {
        var driver=complete("[]","null",false);
        var game=new org.xar.ck3.control.contracts.GameGeneration(123,new org.xar.ck3.control.contracts.PythonOnlyUInt64(new java.math.BigInteger("134000000000000001")));
        var basis=new org.xar.ck3.control.contracts.ExactRef("D:/fixture/original-driver",driver.encode().length,
                org.xar.ck3.control.application.driver.DriverJson.sha256(driver.encode()));
        var stamp=new org.xar.ck3.control.application.driver.DriverSnapshotFacts.Stamp(0,0,game,"episode-1",basis.sha256());
        var auxiliary=new org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj(java.util.Map.of("rows",
                new org.xar.ck3.control.planning.opportunity.OpportunityJson.Arr(List.of(
                        new org.xar.ck3.control.planning.opportunity.OpportunityJson.IntegerValue(java.math.BigInteger.ONE),
                        new org.xar.ck3.control.planning.opportunity.OpportunityJson.Bool(true),
                        org.xar.ck3.control.planning.opportunity.OpportunityJson.Nil.INSTANCE))));
        var known=new org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known(driver,stamp,basis,List.of(),auxiliary,java.util.Optional.empty(),java.util.Optional.empty());
        byte[] original=org.xar.ck3.control.application.driver.DriverSnapshotFacts.encodeKnownOriginal(known).bytes();
        var parsed=org.xar.ck3.control.application.driver.DriverJson.toNode(org.xar.ck3.control.application.driver.DriverJson.object(original,64*1024*1024));
        var reordered=(com.fasterxml.jackson.databind.node.ObjectNode)reverseRestartObjectKeys(parsed);
        byte[] differentBytes=org.xar.ck3.control.application.driver.DriverJson.encodeNode(reordered);
        assertFalse(java.util.Arrays.equals(original,differentBytes));
        assertTrue(ContinuityBatchJournal.sameKnownRestartOriginal(differentBytes,known));
        for(var token:List.of("true","0.0","1")) {
            var changed=reordered.deepCopy();((com.fasterxml.jackson.databind.node.ObjectNode)changed.get("stamp")).set("driver_version",org.xar.ck3.control.contracts.FullJsonTree.parse(token.getBytes(StandardCharsets.UTF_8),1024));
            assertFalse(ContinuityBatchJournal.sameKnownRestartOriginal(org.xar.ck3.control.application.driver.DriverJson.encodeNode(changed),known));
        }
        var missing=reordered.deepCopy();missing.remove("observation");
        assertFalse(ContinuityBatchJournal.sameKnownRestartOriginal(org.xar.ck3.control.application.driver.DriverJson.encodeNode(missing),known));
        var changedArray=reordered.deepCopy();var values=(com.fasterxml.jackson.databind.node.ArrayNode)changedArray.get("auxiliary").get("rows");
        var first=values.get(0);values.set(0,values.get(1));values.set(1,first);
        assertFalse(ContinuityBatchJournal.sameKnownRestartOriginal(org.xar.ck3.control.application.driver.DriverJson.encodeNode(changedArray),known));
        assertThrows(IllegalArgumentException.class,()->ContinuityBatchJournal.sameKnownRestartOriginal("{".getBytes(StandardCharsets.UTF_8),known));
    }
    private static com.fasterxml.jackson.databind.JsonNode reverseRestartObjectKeys(com.fasterxml.jackson.databind.JsonNode value) {
        if(value.isObject()) {
            var fields=new java.util.ArrayList<>(value.properties());java.util.Collections.reverse(fields);
            var result=org.xar.ck3.control.contracts.StrictJson.object();
            for(var field:fields)result.set(field.getKey(),reverseRestartObjectKeys(field.getValue()));return result;
        }
        if(value.isArray()) {var result=com.fasterxml.jackson.databind.node.JsonNodeFactory.instance.arrayNode();for(var item:value)result.add(reverseRestartObjectKeys(item));return result;}
        return value.deepCopy();
    }

}
