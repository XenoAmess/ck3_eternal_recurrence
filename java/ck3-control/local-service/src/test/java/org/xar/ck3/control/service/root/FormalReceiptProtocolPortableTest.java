package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Portable strict DATA protocol only. Resource bytes are frozen originals;
 * software new states/provenance/ref tuples are deliberately unqualified.
 * No physical occurrence proof, native source, Root capability or WAL is made.
 */
final class FormalReceiptProtocolPortableTest {
    private static final String CAS="D:\\ck3-state\\ck3-java-resume91_offline04_20261111T071454Z\\business\\continuity\\artifacts\\";
    private static final ExactRef C4=artifact(2734,"8a3ccb1431262067daed5c9cbc7559ac4ad3c4bb653f2860825ee806adb9dfb5");
    private static final ExactRef C5=artifact(3146,"8e78ab2472a34651e10594aa54ca0af3543a68613d5cc6dea00ecab6be78fa63");
    private static final ExactRef PAUSE=artifact(7879,"76945824decaaea3cf8c0393880c56faff97cf587089cc3508a347f0fb81a690");

    @Test void dedicatedNoEffectStatesKeepStrictSchemasOriginalOptionsAndZeroCredit()throws Exception{
        var originals=new TimelinePrimitiveTerminalPortableTest.Originals();var c4=originals.receipt(C4);var c5=originals.receipt(C5);
        var reserved=new ActionReceipt(1,c5.sequence()+1,c5.command(),c5.bodySha256(),new ActionState.ReservedPreparedCleanupNoEffectConfirmed(ref(1),ref(2)));
        for(var actual:List.of(c4,c5,reserved)){
            byte[] encoded=ActionReceiptCodec.encodeReceipt(actual,originals.archive);var row=json(encoded);var state=(ObjectNode)row.get("state");
            var decoded=ActionReceiptCodec.decodeReceipt(encoded,originals.archive);assertEquals(actual,decoded);
            assertEquals(ActionReceipt.Outcome.TERMINAL_WITHOUT_EFFECT,decoded.outcome());assertTrue(decoded.ack().isEmpty());assertTrue(decoded.applied().isEmpty());assertFalse(decoded.visibleGameplay());assertFalse(decoded.eligibleAdvance());
            var fields=new ArrayList<String>();state.fieldNames().forEachRemaining(fields::add);
            for(String field:fields){var missing=row.deepCopy();((ObjectNode)missing.get("state")).remove(field);assertThrows(RuntimeException.class,()->ActionReceiptCodec.decodeReceipt(StrictJson.canonical(missing),originals.archive),field);}
            var extra=row.deepCopy();((ObjectNode)extra.get("state")).put("source_authority",true);assertThrows(RuntimeException.class,()->ActionReceiptCodec.decodeReceipt(StrictJson.canonical(extra),originals.archive));
            var wrongSchema=row.deepCopy();wrongSchema.put("schema","xar.java-action-receipt/v1");assertThrows(RuntimeException.class,()->ActionReceiptCodec.decodeReceipt(StrictJson.canonical(wrongSchema),originals.archive));
        }
        var rawC4=originals.read(C4,64*1024);var rawC5=originals.read(C5,64*1024);
        assertArrayEquals(rawC4,ActionReceiptCodec.encodeReceipt(c4,originals.archive));assertArrayEquals(rawC5,ActionReceiptCodec.encodeReceipt(c5,originals.archive));
        var before=((ActionState.PreparedCleanupNoEffectConfirmed)c5.state()).originalPreparedState();
        assertEquals(before,((ActionState.PreparedCleanupNoEffectConfirmed)ActionReceiptCodec.decodeReceipt(rawC5,originals.archive).state()).originalPreparedState());
        assertEquals("xar.java.reserved-prepared-cleanup-noeffect-action-receipt/v1",json(ActionReceiptCodec.encodeReceipt(reserved,originals.archive)).path("schema").textValue());
        assertEquals(0,originals.unexpectedCalls);
    }

    @Test void physicalAfterAckProvenanceRoundTripsThroughItsDedicatedReceiptSchemaAndStrictGuards()throws Exception{
        var originals=new TimelinePrimitiveTerminalPortableTest.Originals();var old=originals.receipt(PAUSE);var settled=(ActionState.Settled)old.state();
        var effect=((ActionState.PauseConfirmed)settled.settlement()).observation();
        var physical=new ObservationProvenance.PhysicalAfterAcknowledgement(effect.after().frame().snapshotId(),effect.after().frame().identity().nativeRevision(),effect.originalEvidence(),ref(3));
        // Original positive ACK, body and physical packet are retained; only the
        // provenance/occurrence tuple is software DATA, not a Root occurrence.
        var replacement=new ActionState.EffectObservation(effect.after(),effect.source(),effect.sessionId(),effect.observerSchema(),effect.actual(),physical,effect.observedAt(),effect.originalEvidence(),effect.supportingEvidence());
        var receipt=new ActionReceipt(1,old.sequence(),old.command(),old.bodySha256(),new ActionState.Settled(settled.attempt(),settled.dispatch(),new ActionState.PauseConfirmed(replacement)));
        byte[] encoded=ActionReceiptCodec.encodeReceipt(receipt,originals.archive);var row=json(encoded);
        assertEquals(ActionReceiptCodec.TIMELINE_AFTER_ACK_SCHEMA,row.path("schema").textValue());
        var restored=ActionReceiptCodec.decodeReceipt(encoded,originals.archive);assertEquals(receipt.command(),restored.command());
        assertEquals(receipt.bodySha256(),restored.bodySha256());assertArrayEquals(encoded,ActionReceiptCodec.encodeReceipt(restored,originals.archive));
        assertEquals(physical,((ActionState.PauseConfirmed)((ActionState.Settled)restored.state()).settlement()).observation().provenance());
        assertTrue(restored.ack().orElseThrow().nativeOk());assertFalse(restored.visibleGameplay());assertFalse(restored.eligibleAdvance());
        var provenance=ObservationProvenanceCodec.encode(physical);assertEquals(physical,ObservationProvenanceCodec.decode(provenance));
        assertEquals(Set.of("kind","snapshot_id","native_revision","original_packet","occurrence_evidence"),keys(provenance));
        for(String field:keys(provenance)){var missing=provenance.deepCopy();missing.remove(field);assertThrows(RuntimeException.class,()->ObservationProvenanceCodec.decode(missing));}
        var extra=provenance.deepCopy();extra.put("private_permit",true);assertThrows(RuntimeException.class,()->ObservationProvenanceCodec.decode(extra));
        for(String invalid:List.of("01","-1","1.0","18446744073709551616")){var bad=provenance.deepCopy();bad.put("native_revision",invalid);assertThrows(RuntimeException.class,()->ObservationProvenanceCodec.decode(bad));}
        var changed=new ObservationProvenance.PhysicalAfterAcknowledgement(physical.snapshotId(),physical.nativeRevision().add(BigInteger.ONE),physical.originalPacket(),physical.occurrenceEvidence());
        assertThrows(RuntimeException.class,()->changed.validate(effect.after(),effect.originalEvidence()));
        var wrongSchema=row.deepCopy();wrongSchema.put("schema",ActionReceiptCodec.PROVENANCE_SCHEMA);
        assertThrows(RuntimeException.class,()->ActionReceiptCodec.decodeReceipt(StrictJson.canonical(wrongSchema),originals.archive));
        assertArrayEquals(originals.read(PAUSE,64*1024),ActionReceiptCodec.encodeReceipt(old,originals.archive));assertEquals(0,originals.unexpectedCalls);
    }

    @Test void freshWatchCodecsRequireTheirExactThreeAndFiveReferencesAndKeepLegacyBasesCompatible(){
        var event=new NativeRequestChronology.Event(BigInteger.ONE,Instant.EPOCH);
        List<ObservationProvenance.FreshSnapshotBasis> bases=List.of(new ObservationProvenance.LiveAfterSetter(ref(1)),new ObservationProvenance.ColdAfterAcknowledgement(ref(1)),
                new ObservationProvenance.SameGameWatch(ref(1),ref(2)),new ObservationProvenance.PostResumePauseWatch(ref(1),ref(2),ref(3)),
                new ObservationProvenance.PreparedCleanupWatch(ref(1),ref(2),ref(3)),new ObservationProvenance.PreparedCleanupSuccessorWatch(ref(1),ref(2),ref(3),ref(4),ref(5)));
        for(var basis:bases){
            var value=new ObservationProvenance.FreshSnapshotQuery("software-query",ref(6),event,basis);var row=ObservationProvenanceCodec.encode(value);
            assertEquals(value,ObservationProvenanceCodec.decode(row));var encodedBasis=(ObjectNode)row.get("basis");
            for(String field:keys(encodedBasis)){var missing=row.deepCopy();((ObjectNode)missing.get("basis")).remove(field);assertThrows(RuntimeException.class,()->ObservationProvenanceCodec.decode(missing));}
            var extra=row.deepCopy();((ObjectNode)extra.get("basis")).put("world_permission",true);assertThrows(RuntimeException.class,()->ObservationProvenanceCodec.decode(extra));
        }
        assertThrows(RuntimeException.class,()->new ObservationProvenance.PostResumePauseWatch(ref(1),ref(2),ref(1)));
        assertThrows(RuntimeException.class,()->new ObservationProvenance.PreparedCleanupWatch(ref(1),ref(2),ref(1)));
        assertThrows(RuntimeException.class,()->new ObservationProvenance.PreparedCleanupSuccessorWatch(ref(1),ref(2),ref(3),ref(4),ref(1)));
    }

    private static ObjectNode json(byte[] raw){return (ObjectNode)StrictJson.parse(raw,64*1024);}
    private static Set<String> keys(ObjectNode row){var names=new java.util.HashSet<String>();row.fieldNames().forEachRemaining(names::add);return Set.copyOf(names);}
    private static ExactRef artifact(long bytes,String sha){return new ExactRef(CAS+sha+".bin",bytes,sha);}
    private static ExactRef ref(int n){return new ExactRef("unqualified-software-codec:"+n,2,ActionCodec.sha256(new byte[]{123,125}));}
}
