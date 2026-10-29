package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.CommandOwnershipGate12004.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Set;
import java.util.function.Consumer;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.UInt64;
import org.xar.ck3.control.nativebridge.capabilities.army.LocalTargetScore12004.Scope;

final class CommandOwnershipGate12004ProducerTest {
    private static Map<String,ObjectNode> actualCases() throws Exception {
        String file=System.getProperty("xar.commandOwnership12004.nativeWire"),sha=System.getProperty("xar.commandOwnership12004.nativeWireSha256"),
                machine=System.getProperty("xar.commandOwnership12004.machineId");
        assertNotNull(file);assertNotNull(sha);assertNotNull(machine);assertFalse(machine.isBlank());assertTrue(sha.matches("[0-9a-f]{64}"));
        Path path=Path.of(file);assertTrue(path.isAbsolute()&&Files.isRegularFile(path));long size=Files.size(path);assertTrue(size>0&&size<=1_048_576);
        byte[] raw=Files.readAllBytes(path);assertEquals(size,raw.length);assertEquals(sha,HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)));
        ObjectNode root=closed(parse(raw),"schema_version","machine_id","observed_at_utc","proof_layer","original_native_executions","actual_game","cases");
        assertEquals(1,i32(root.get("schema_version")));assertEquals(machine,text(root.get("machine_id")));assertNotNull(Instant.parse(text(root.get("observed_at_utc"))));
        assertEquals("owned_immutable_ownership_reader_serializer_only",text(root.get("proof_layer")));assertEquals(0,i32(root.get("original_native_executions")));assertFalse(bool(root.get("actual_game")));
        Map<String,ObjectNode> out=new LinkedHashMap<>();
        for(ObjectNode row:array(root.get("cases"),n->closed(n,"name","observation")))assertNull(out.put(text(row.get("name")),object(row.get("observation"))));
        assertEquals(Set.of("flag_zero_handoff","flag_bit1_handoff","flag_bit0_cleanup","flag_all_cleanup","null_command_handoff","missing_gate",
                "forward_argument_changed","source_not_cleared","moved_pointer_changed","manager_changed","flag_unavailable","wrapper_frame_changed","original_command_changed"),out.keySet());
        return out;
    }
    @Test void originalNativeProducerToOwnershipBranchAndRoundTrip() throws Exception {
        for(var row:actualCases().entrySet()) {
            Observation read=decode(bytes(row.getValue()));assertEquals(read,decode(encode(read)),row.getKey());
            if(read instanceof Available a) {
                Facts f=assertInstanceOf(ObservedOwnership.class,consume(read.scope(),a.facts().originalCommand().call(),read)).facts();
                boolean cleanup=row.getKey().contains("cleanup");assertEquals(cleanup,f.stage() instanceof Cleanup);
                assertEquals(row.getKey().equals("null_command_handoff")?"0":"9007199321849857",f.clonedCommandPointerRaw().decimal());
                if(f.stage() instanceof Handoff h) {assertEquals(7,h.forwardedArgumentRaw());assertEquals(f.inputSlotIdentity().value().subtract(BigInteger.valueOf(0x30)),h.localOwnedSlotIdentity().value());}
            } else assertInstanceOf(Incomplete.class,read);
        }
    }
    @Test void missingSnapshotsAndChangedOccurrenceNeverBecomeQueuedResult() throws Exception {
        Map<String,ObjectNode> cases=actualCases();Available read=assertInstanceOf(Available.class,decode(bytes(cases.get("flag_zero_handoff"))));
        var key=read.facts().originalCommand().call();Scope s=read.scope();
        for(ObjectNode wire:cases.values()) {Observation o=decode(bytes(wire));if(o instanceof Incomplete m)assertEquals(new NotReady(m.reason()),consume(o.scope(),key,o));}
        Scope next=new Scope(s.episode(),s.connectionGeneration(),s.nativeRevision(),s.coordinatorIdentity(),"8",s.dateRaw(),s.exeSha256());
        assertEquals(new NotReady("ownership_update_or_source_changed"),consume(next,key,read));
        var other=new OriginalCommandEnvelope12004.CallKey(key.moduleBaseIdentity(),key.unitOperandIdentity(),key.candidateOperandIdentity(),
                UInt64.positive(key.commandAddress().value().add(BigInteger.valueOf(8))),key.databaseIdentity());
        assertEquals(new NotReady("ownership_original_occurrence_changed"),consume(s,other,read));
    }
    private static void rejects(ObjectNode source,Consumer<ObjectNode> mutate) {
        ObjectNode altered=source.deepCopy();mutate.accept(altered);assertThrows(IllegalArgumentException.class,()->decode(bytes(altered)));
    }
    @Test void strictMaskPointerAndWrapperArgumentContract() throws Exception {
        ObjectNode base=actualCases().get("flag_zero_handoff");
        rejects(base,n->object(n.get("facts")).put("flag_byte_raw",true));
        rejects(base,n->object(n.get("facts")).put("flag_byte_raw",1));
        rejects(base,n->object(n.get("facts")).put("flag_byte_raw",256));
        rejects(base,n->object(n.get("facts")).put("cloned_command_pointer_raw",9L));
        rejects(base,n->object(n.get("facts")).remove("input_slot_identity"));
        rejects(base,n->object(object(n.get("facts")).get("stage")).put("forwarded_argument_raw",2));
        rejects(base,n->object(object(n.get("facts")).get("stage")).put("manager_identity","1"));
        rejects(base,n->object(n.get("facts")).put("queued",true));
        rejects(base,n->n.put("handoff_rva",HANDOFF_RVA+1));
    }
}
