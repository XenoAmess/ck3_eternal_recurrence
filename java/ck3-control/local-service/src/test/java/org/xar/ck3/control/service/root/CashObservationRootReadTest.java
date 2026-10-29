package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.PublicDataJson;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.service.root.CashObservationPublicCodec.*;

/** Actual software writer/read guard/transport/archive pipeline; no live Native or Finance deployment qualification. */
final class CashObservationRootReadTest {
    @TempDir Path directory;
    @Test void actualRegisteredCashFamilyPassesCentralReadAndArchivesOriginalBeforePublicSerde()throws Exception {
        var original=CashObservationReadParityTest.originals(directory);ObjectNode template=null;
        for(var row:original.path("rows"))if(row.path("kind").asText().equals("construction")){template=(ObjectNode)row.path("frame").path("result").path("war_cash_current_resources");break;}
        assertNotNull(template);ObjectNode originalTemplate=template;
        var owner=new AtomicReference<CashObservationReads>();var nativeResult=new AtomicReference<RawJson>();
        var scenario=new ActionWriterIntegrationFixture.SoftwareReadScenario("98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518","actual-private-cash-read",source->List.of(),request->{
            assertEquals("query-war-cash-current-resources-v1",request.step());assertTrue(request.additionalFields().objectFieldNames().isEmpty());return nativeResult.get();},
            Optional.of("1.20.0.4"),Set.of(),source->{var reads=new CashObservationReads(new CashObservationReads.Sources(source,source));owner.set(reads);return reads.families();});
        try(var f=new ActionWriterIntegrationFixture(directory.resolve("actual-writer"),false,scenario)){
            var ready=f.ready();f.writer.locked(same->{f.collector.current(same,ready.request().before(),Instant.now().plusSeconds(30),lease->{
                var actual=lease.frame();ObjectNode cash=originalTemplate.deepCopy();var frame=actual.identity().frame();var actor=frame.identity().player();
                cash.put("played_character_id",actor).put("snapshot_revision",frame.identity().nativeRevision()).put("date_raw",frame.identity().dateRaw());
                cash.putArray("active_war_ids");cash.putArray("player_army_ids");
                for(String kind:List.of("current","all_raised")){ObjectNode expense=(ObjectNode)cash.path("military_expenses").path(kind);expense.put("owner_character_id",actor).put("resource_id",actor.toString());expense.putArray("war_ids");}
                var payload=org.xar.ck3.control.contracts.StrictJson.object().put("step","query-war-cash-current-resources-v1").put("accepted",true).put("private_build",true).put("read_only",true).put("advertised",false).put("status","available");payload.set("war_cash_current_resources",cash);nativeResult.set(PublicDataJson.encode(payload));
                var input=new Current(frame.revision(),new Nullable<>(Presence.MISSING,Optional.empty()),new Nullable<>(Presence.MISSING,Optional.empty()));
                var selected=new CashObservationReads.Selection(actual,input,Optional.empty(),Instant.now().plusSeconds(10));var contract=owner.get().contract(f.actualReadCatalog(),selected);
                int writes=f.scenarioReadWrites();var result=f.reads.read(same,contract,selected.request());assertEquals(writes+1,f.scenarioReadWrites());
                if(!(result instanceof PlanningReadResult.Known<Response> known))throw new AssertionError(((PlanningReadResult.Unavailable<Response>)result).reason());
                assertEquals(known.receipt(),f.archive.loadRead(known.originalReceipt()));assertEquals(known.value(),contract.replay(known.receipt()));
                var publicWire=CashObservationPublicCodec.encode(known.value());assertEquals(known.value().originalNormalized(),CashObservationCodec.nativeWire(publicWire));
                assertEquals(0,f.nativeActionWrites());return null;});return null;});
        }
    }
}
