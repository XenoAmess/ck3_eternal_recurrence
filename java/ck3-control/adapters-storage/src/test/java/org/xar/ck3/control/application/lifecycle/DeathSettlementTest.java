package org.xar.ck3.control.application.lifecycle;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.math.BigDecimal;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.checkpoint.NativeCheckpointFiles;

public final class DeathSettlementTest {
    @TempDir Path temporary;
    static com.fasterxml.jackson.databind.node.ObjectNode ready(boolean written,int candidate,int old) {
        var row=LifecycleJson.row();row.put("ready",true);row.put("commit_serial",1);row.put("source_character_id",73);
        row.putObject("final_score").put("raw",1234500).put("scale",100000);row.put("score_before_reject",15.5);
        row.put("record_candidate",candidate);row.put("old_record",old);row.put("record_delta",candidate-old);
        row.put("blessing_count",2);row.put("refusal_count",1);row.put("contract_progress",6);row.put("record_written",written);return row;
    }
    @Test void actualFixedScaleProducerPreservesFiniteScoreAndReadyScope() {
        var actual=DeathSettlement.normalize(ready(true,12,10)).orElseThrow();assertEquals(0,new BigDecimal("12.345").compareTo(actual.finalScore()));
        assertTrue(actual.recordWritten());assertEquals(73,actual.sourceCharacterId().intValueExact());
        assertEquals(actual.finalScore(),DeathSettlement.fromNormalized(LifecycleJson.parse(actual.normalized(),65536)).orElseThrow().finalScore());
        var legacy=ready(false,10,10);legacy.put("ready",1);legacy.put("record_written",0);assertTrue(DeathSettlement.normalize(legacy).isPresent());
    }
    @Test void wrongIntegerAliasesMissingFieldsAndContradictoryReadyDataAreRejected() {
        for(String field:new String[]{"commit_serial","source_character_id","record_candidate","record_delta","blessing_count"}) {
            var invalid=ready(true,12,10);invalid.put(field,true);var booleanInvalid=invalid;assertThrows(IllegalArgumentException.class,()->DeathSettlement.normalize(booleanInvalid));
            invalid=ready(true,12,10);invalid.put(field,1.0);var floating=invalid;assertThrows(IllegalArgumentException.class,()->DeathSettlement.normalize(floating));
        }
        var absent=ready(false,10,10);absent.remove("final_score");assertThrows(IllegalArgumentException.class,()->DeathSettlement.normalize(absent));
        var wrong=ready(true,12,10);wrong.put("record_delta",1);assertThrows(IllegalArgumentException.class,()->DeathSettlement.normalize(wrong));
        var scalar=ready(false,10,10);scalar.set("final_score",LifecycleJson.row().numberNode(new java.math.BigInteger("9".repeat(400))));
        assertThrows(IllegalArgumentException.class,()->DeathSettlement.normalize(scalar));
    }
    @Test void recordPersistenceRequiresTwoActualIdenticalTutorialReadsAndNoRecordNeedsNoFile() throws Exception {
        var files=new NativeCheckpointFiles();var noRecord=DeathSettlement.normalize(ready(false,10,10)).orElseThrow();
        assertEquals(DeathSettlement.PersistenceStatus.NO_NEW_RECORD,DeathSettlement.awaitPersistence(noRecord,files,temporary.resolve("absent.txt"),Instant.now().plusSeconds(1),Clock.systemUTC()).status());
        Path tutorial=temporary.resolve("tutorial.txt");Files.writeString(tutorial,"\ufeffcompleted_lessons={\"xar_hs_ge_12\"}",StandardCharsets.UTF_8);
        var persisted=DeathSettlement.awaitPersistence(DeathSettlement.normalize(ready(true,12,10)).orElseThrow(),files,tutorial,Instant.now().plusSeconds(2),Clock.systemUTC());
        assertTrue(persisted.required());files.verify(persisted.file().orElseThrow());assertEquals(DeathSettlement.PersistenceStatus.PERSISTED,persisted.status());
        Files.writeString(tutorial,"completed_lessons={\"xar_hs_ge_11\"}");
        assertThrows(IOException.class,()->DeathSettlement.awaitPersistence(DeathSettlement.normalize(ready(true,12,10)).orElseThrow(),files,tutorial,Instant.now().plusMillis(100),Clock.systemUTC()));
    }
}
