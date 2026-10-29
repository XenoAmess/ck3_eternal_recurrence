package org.xar.ck3.control.nativebridge.capabilities.army;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.PairTargetScoreTerminal12004.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.UInt64;
import org.xar.ck3.control.nativebridge.capabilities.army.LocalTargetScore12004.Scope;

/** Owned memory producer/serializer only; no original append execution or Game authority credit. */
final class PairAppendObservation12004ProducerTest {
    private enum Expected { OBSERVED_HEADER, NOT_READY, INCOMPLETE }
    private record Case(AppendObservation observation, UInt64 moduleBase, Expected expected, ObjectNode original) { }
    private static Map<String,Case> cases() throws Exception {
        String file=System.getProperty("xar.pairAppend12004.nativeWire"),sha=System.getProperty("xar.pairAppend12004.nativeWireSha256");
        assertNotNull(file,"fresh Root-owned-memory producer file required");assertNotNull(sha,"fresh SHA required");assertTrue(sha.matches("[0-9a-f]{64}"));
        Path path=Path.of(file);assertTrue(path.isAbsolute()&&Files.isRegularFile(path));long size=Files.size(path);assertTrue(size>0&&size<=8*1024*1024);
        byte[] bytes=Files.readAllBytes(path);assertEquals(size,bytes.length);assertEquals(sha,HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)));
        ObjectNode root=closed(parse(bytes),"schema_version","machine_id","observed_at_utc","actual_game","original_native_append_executions","proof_layer","cases");
        assertEquals(1,i32(root.get("schema_version")));assertFalse(bool(root.get("actual_game")));assertEquals(0,i32(root.get("original_native_append_executions")));
        assertEquals("owned_memory_observer_serializer_only",text(root.get("proof_layer")));assertTrue(text(root.get("machine_id")).matches("[a-z0-9-]{1,128}"));
        assertNotEquals("unknown",text(root.get("machine_id")));java.time.Instant.parse(text(root.get("observed_at_utc")));
        Map<String,Case> cases=new LinkedHashMap<>();
        for(ObjectNode row:array(root.get("cases"),v->closed(v,"name","module_base_identity","expected","observation"))) {
            String module=text(row.get("module_base_identity"));assertTrue(module.matches("[1-9][0-9]{0,19}"));
            Expected expected=switch(text(row.get("expected"))){case "observed_header"->Expected.OBSERVED_HEADER;case "not_ready"->Expected.NOT_READY;case "incomplete"->Expected.INCOMPLETE;default->throw new IllegalArgumentException("unknown expectation");};
            ObjectNode original=object(row.get("observation"));AppendObservation observation=decodeAppend(bytes(original));
            assertEquals(expected!=Expected.INCOMPLETE,observation instanceof AppendAvailable);
            assertNull(cases.put(text(row.get("name")),new Case(observation,UInt64.positive(new BigInteger(module)),expected,original)));
        }
        assertEquals(Set.of("existing_same","growth_same","growth_different","empty_same","not_consumed","selected","tuple_mismatch","reason_count_mismatch","post_header_missing","wrong_return_slot"),cases.keySet());return cases;
    }
    @Test void actualOwnedHeaderProducerToTypedConsumerAndRoundTrip() throws Exception {
        Map<String,Case> all=cases();PairKey fallback=((AppendAvailable)all.get("existing_same").observation()).facts().originalCall().facts().pair();
        for(var item:all.entrySet()) {
            Case c=item.getValue();AppendObservation original=c.observation();assertEquals(original,decodeAppend(encodeAppend(original)),item.getKey());
            PairKey key=original instanceof AppendAvailable a?a.facts().originalCall().facts().pair():fallback;
            Result result=consumeAppend(original.scope(),key,c.moduleBase(),original);
            if(c.expected()==Expected.OBSERVED_HEADER) {
                ObservedAppendRecord record=assertInstanceOf(ObservedAppendRecord.class,result,item.getKey());
                assertEquals(ReasonVerification.HEADER_COUNT_AND_SOURCE_MOVE_ONLY,record.reasonVerification());assertEquals(0,record.record().selectedRaw());
                assertEquals(item.getKey().equals("existing_same")?AppendBranch.EXISTING_STORAGE:AppendBranch.REALLOCATION_PATH,record.branch());
                AppendFacts facts=((AppendAvailable)original).facts();assertEquals(0,facts.originalReasonsAfter().storage().count());
                assertEquals(2,facts.originalReasons().storage().count());assertEquals(2,record.record().reasons().storage().count());
            } else assertInstanceOf(NotReady.class,result,item.getKey());
        }
    }
    @Test void stalePreSourceCannotMasqueradeAsPostSourceAndModuleUpdateStayBound() throws Exception {
        Case c=cases().get("existing_same");AppendAvailable original=(AppendAvailable)c.observation();AppendFacts f=original.facts();
        PairKey key=f.originalCall().facts().pair();Scope s=original.scope();
        AppendFacts stale=new AppendFacts(s,f.originalCall(),f.before(),f.originalReasons(),f.originalReasons(),f.after(),f.moduleBaseIdentity(),f.returnedIdentity(),f.record());
        assertEquals(new NotReady("original_reason_source_not_consumed"),consumeAppend(s,key,c.moduleBase(),new AppendAvailable(stale)));
        Scope changed=new Scope(s.episode(),s.connectionGeneration(),s.nativeRevision(),s.coordinatorIdentity(),"22",s.dateRaw(),s.exeSha256());
        assertEquals(new NotReady("coordinator_update_or_source_changed"),consumeAppend(changed,key,c.moduleBase(),original));
        assertEquals(new NotReady("original_append_module_identity_changed"),consumeAppend(s,key,UInt64.positive(BigInteger.ONE),original));
    }
    @Test void malformedAndMissingSourceFieldsRejectWithoutCoercion() throws Exception {
        ObjectNode original=cases().get("existing_same").original();
        ObjectNode missing=original.deepCopy();object(missing.get("facts")).remove("original_reasons_after");assertThrows(IllegalArgumentException.class,()->decodeAppend(bytes(missing)));
        ObjectNode missingNull=original.deepCopy();object(missingNull.get("facts")).putNull("original_reasons_after");assertThrows(IllegalArgumentException.class,()->decodeAppend(bytes(missingNull)));
        ObjectNode bool=original.deepCopy();object(object(bool.get("facts")).get("record")).put("selected_raw",true);assertThrows(IllegalArgumentException.class,()->decodeAppend(bytes(bool)));
        ObjectNode number=original.deepCopy();object(number.get("facts")).put("module_base_identity",1);assertThrows(IllegalArgumentException.class,()->decodeAppend(bytes(number)));
        ObjectNode floating=original.deepCopy();object(object(floating.get("facts")).get("after")).put("count",2.0);assertThrows(IllegalArgumentException.class,()->decodeAppend(bytes(floating)));
        ObjectNode bounds=original.deepCopy();object(object(bounds.get("facts")).get("after")).put("count",5);assertThrows(IllegalArgumentException.class,()->decodeAppend(bytes(bounds)));
        ObjectNode field=original.deepCopy();object(field.get("facts")).put("pair_ready",true);assertThrows(IllegalArgumentException.class,()->decodeAppend(bytes(field)));
        ObjectNode stage=original.deepCopy();stage.put("stage_rva",APPEND_CALL_RVA);assertThrows(IllegalArgumentException.class,()->decodeAppend(bytes(stage)));
    }
}
