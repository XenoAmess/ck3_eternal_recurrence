package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.file.Path;
import java.time.Instant;
import java.util.*;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.*;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.extensions.ReligionDoctrineDraftReads;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.extensions.ReligionDoctrineDraftReads.*;
import org.xar.ck3.control.nativebridge.capabilities.religion.PlayerReligionContext.Build;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Actual writer/read/archive/catalog/public codec software path. No runtime source or live qualification. */
final class RootReligionDoctrineDataTest {
    @TempDir Path directory;
    @Test void readonlyProducerTraversesRealGuardReadArchiveAndPublicRoute()throws Exception{
        var selected=Selection.fixed(Kind.DOCTRINE_CATALOGUE);var installed=new AtomicReference<ReadContract<Observed>>();var build=Build.CROZIER4;
        var scenario=new ActionWriterIntegrationFixture.SoftwareReadScenario(build.sha256(),"ck3-1.20.0.4-msvc-x64",source->{var contract=ReligionDoctrineDraftReads.contract(selected,new Sources(source,source,List.of(source)),request->assertEquals(selected.kind().step(),request.operation().value()));installed.set(contract);return List.of(contract);},request->{assertEquals(selected.kind().step(),request.step());assertTrue(ReligionCodec.object(request.additionalFields()).isEmpty());return ReligionCodec.raw(envelope());},Optional.of(build.version()),Set.of());
        try(var actual=new ActionWriterIntegrationFixture(directory.resolve("doctrine"),false,scenario)){
            actual.ready();actual.writer.locked(same->actual.collector.currentOwned(same,actual.observationIdentity(),Instant.now().plusSeconds(20),lease->{
                var frame=lease.frame();var request=new PlanningReadRequest(frame.identity(),frame.source(),frame.sessionId(),installed.get().operation(),new OpportunityJson.Obj(Map.of()),Instant.now().plusSeconds(15));var read=ReligionService.readKnownRequest(actual.reads,actual.archive,same,installed.get(),request);
                var original=actual.archive.withSession(same).loadRead(read.originalReceipt());assertEquals(read.value(),installed.get().replay(original));var output=read.value().publicResult();assertEquals("18446744073709551615",output.get("capture_epoch").textValue());assertEquals("1",output.get("snapshot_revision").textValue());assertTrue(ReligionCodec.object(original.original().originalResultToken().orElseThrow()).get("snapshot_revision").isIntegralNumber());
                var call=StrictJson.object().put("expected_revision",frame.identity().frame().revision().toString());var binding=RootReligionDoctrineData.bindings(Group.DATA,installed.get().sourceRef(),decoded->{assertEquals(selected,Selection.from(decoded));return new ReligionContract.Response(decoded.method(),ReligionCodec.raw(output));}).stream().filter(b->b.name().equals(selected.kind().method())).findFirst().orElseThrow();ReligionExtensionTestWire.exercise(binding,call,output);
                assertEquals(1,actual.scenarioReadWrites());assertEquals(0,actual.nativeActionWrites());return null;
            }));
        }
    }
    @Test void bothMandatoryExtensionsOwnDistinctCompleteReadonlyMethodSets(){assertEquals(7,RootReligionDoctrineData.methodsList(Group.DATA).size());assertEquals(6,RootReligionDoctrineData.methodsList(Group.DRAFT).size());var all=new HashSet<>(RootReligionDoctrineData.methodsList(Group.DATA));assertTrue(Collections.disjoint(all,RootReligionDoctrineData.methodsList(Group.DRAFT)));all.addAll(RootReligionDoctrineData.methodsList(Group.DRAFT));assertEquals(13,all.size());}
    private static com.fasterxml.jackson.databind.node.ObjectNode envelope(){var build=Build.CROZIER4;var n=StrictJson.object().put("step",Kind.DOCTRINE_CATALOGUE.step()).put("accepted",true).put("status","observed").put("private_build",true).put("read_only",true).put("advertised",false).put("game_version",build.version()).put("executable_sha256",build.sha256()).put("backend_id","ck3-1.20.0.4-native-"+Kind.DOCTRINE_CATALOGUE.suffix()).put("domain_key",Kind.DOCTRINE_CATALOGUE.domain()).put("snapshot_revision",1).put("date_raw",ActionWriterIntegrationFixture.INITIAL_DATE_RAW);var body=n.putObject(Kind.DOCTRINE_CATALOGUE.nested()).put("schema","ck3_12004_loaded_doctrine_catalogue_v1").put("available",true).putNull("unavailable_reason").put("catalogue_complete",true).put("source","loaded_doctrine_registry").put("capture_epoch",new BigInteger("18446744073709551615")).put("date_raw",ActionWriterIntegrationFixture.INITIAL_DATE_RAW).put("played_character_id",73);body.putArray("rows").addObject().put("doctrine_key","doctrine_礼").put("group_key","group").put("source","loaded_doctrine_registry");return n;}
}
