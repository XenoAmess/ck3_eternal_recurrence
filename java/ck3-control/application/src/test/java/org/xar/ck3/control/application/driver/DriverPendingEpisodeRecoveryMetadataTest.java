package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import java.time.Instant;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Persisted DATA contract only. These values never instantiate a Root cause, Current or recovered publication. */
final class DriverPendingEpisodeRecoveryMetadataTest {
    private static final Instant OBSERVED=Instant.parse("2026-10-24T09:00:00Z");
    private static ExactRef ref(String name){return new ExactRef(name,2,DriverJson.sha256(new byte[]{'{','}'}));}
    private static DriverPendingEpisodeSource.InitialMetadata initial() {
        return new DriverPendingEpisodeSource.InitialMetadata("software-fixture",OBSERVED,ref("known"),ref("native"),
                ref("parent-known"),ref("canonical-domain"),42,"1".repeat(64),"actual-event-id",ref("projection"),List.of(ref("producer.java")));
    }
    private static RawJson changed(DriverPendingEpisodeSource.RecoveryMetadata actual,java.util.function.Consumer<com.fasterxml.jackson.databind.node.ObjectNode> edit) {
        var row=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(actual.encode().bytes(),1_048_576);edit.accept(row);
        return new RawJson(StrictJson.canonical(row,1_048_576));
    }
    @Test void initialAndEveryMutationPhaseRetainDistinctOriginalRoles() {
        var initial=initial();assertEquals(initial,DriverPendingEpisodeSource.decodeRecoveryMetadata(initial.encode()));
        assertNotEquals(initial.beforeKnown(),initial.parentKnown());assertNotEquals(initial.beforeNative(),initial.canonicalDomain());
        for(var phase:DriverPendingEpisodeSource.MutationPhase.values()) {
            var mutation=new DriverPendingEpisodeSource.MutationMetadata(initial.machineId(),OBSERVED,ref("before-known"),ref("before-native"),
                    ref("mutation-domain"),45,"2".repeat(64),"mutation-event",phase,ref("before-obligation"),ref("after-obligation"),initial.producerSources());
            var decoded=DriverPendingEpisodeSource.decodeRecoveryMetadata(mutation.encode());assertEquals(mutation,decoded);
            assertArrayEquals(mutation.encode().bytes(),decoded.encode().bytes());
        }
    }
    @Test void legacyOrIncompleteOriginalsNeverAcquireRecoveryDefaults() {
        var actual=initial();
        assertThrows(IllegalArgumentException.class,()->DriverPendingEpisodeSource.decodeRecoveryMetadata(changed(actual,row->row.put("schema","xar.java.pending-episode-driver-source/v1"))));
        for(String required:List.of("before_known","before_native","parent_known","canonical_head_sequence"))
            assertThrows(IllegalArgumentException.class,()->DriverPendingEpisodeSource.decodeRecoveryMetadata(changed(actual,row->row.remove(required))));
        assertThrows(IllegalArgumentException.class,()->DriverPendingEpisodeSource.decodeRecoveryMetadata(changed(actual,row->row.putNull("parent_known"))));
    }
    @Test void sequenceTypeAndClosedFieldsRemainStrict() {
        var actual=initial();
        assertThrows(IllegalArgumentException.class,()->DriverPendingEpisodeSource.decodeRecoveryMetadata(changed(actual,row->row.put("canonical_head_sequence",true))));
        assertThrows(IllegalArgumentException.class,()->DriverPendingEpisodeSource.decodeRecoveryMetadata(changed(actual,row->row.put("canonical_head_sequence",42.0))));
        assertThrows(IllegalArgumentException.class,()->DriverPendingEpisodeSource.decodeRecoveryMetadata(changed(actual,row->row.put("canonical_head_sequence","42"))));
        assertThrows(IllegalArgumentException.class,()->DriverPendingEpisodeSource.decodeRecoveryMetadata(changed(actual,row->row.put("private_current",true))));
    }
    @Test void emptyOrRepeatedProducerOriginalsCannotPassTheFiniteContract() {
        var actual=initial();
        assertThrows(IllegalArgumentException.class,()->DriverPendingEpisodeSource.decodeRecoveryMetadata(changed(actual,row->((com.fasterxml.jackson.databind.node.ObjectNode)row.get("before_native")).put("bytes",0))));
        assertThrows(IllegalArgumentException.class,()->DriverPendingEpisodeSource.decodeRecoveryMetadata(changed(actual,row->row.putArray("producer_sources"))));
        assertThrows(IllegalArgumentException.class,()->DriverPendingEpisodeSource.decodeRecoveryMetadata(changed(actual,row->{var source=row.get("producer_sources").get(0);var list=row.putArray("producer_sources");list.add(source);list.add(source);} )));
    }
}
