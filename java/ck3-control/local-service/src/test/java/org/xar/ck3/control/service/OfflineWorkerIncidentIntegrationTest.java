package org.xar.ck3.control.service;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.file.StandardOpenOption;
import java.util.List;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.events.interactionregistry.InteractionRegistryCodec;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson;
import org.xar.ck3.control.wave2.events.unhandledevent.SourceReviewedInteractionContinuation;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.ZoneOffset;
import java.util.Optional;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.checkpoint.NativeCheckpointFiles;
import org.xar.ck3.control.application.planning.events.EpisodeIncidentJournal;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.offline.IncidentJournalLayout;
import org.xar.ck3.control.contracts.offline.OfflineAnalysisFiles;
import org.xar.ck3.control.contracts.projection.ProjectionEvidenceCodec;
import org.xar.ck3.control.wave2.events.unhandledevent.TrustedEventSourceContext;

/** Actual V2 journal producer -> fixed host -> worker -> original analyzer -> same journal ACK.
 * Reuses original stock corpus and synthetic frame inputs; this test confers no Game qualification. */
final class OfflineWorkerIncidentIntegrationTest {
    @TempDir Path temporary;
    @Test void realObservedBatchCompletesOnlyAfterSameJournalAndDurableSourceKnowledge()throws Exception {
        var f=new OfflineInteractionCorpus(temporary.resolve("worker-observed"));var identity=f.binding.before();
        // Authored software input in the existing temporary tree; no stock or Game-origin claim.
        String key="synthetic_unknown_interaction";
        Path authored=f.game.resolve("common/character_interactions/"+key+".txt");
        Files.writeString(authored,key+" = {\n category = interaction_category_religion\n on_accept = {\n add_piety = 1\n }\n on_decline = {\n add_piety = -1\n }\n}\n",StandardOpenOption.CREATE_NEW);
        ExactRef authoredRef=OfflineInteractionCorpus.pin(authored);
        var sourceBefore=(ObjectNode)f.corpus.path("known_before");
        var snapshot=((ObjectNode)sourceBefore.path("binding")).deepCopy();
        snapshot.putObject("played_character").set("character_id",snapshot.get("actor_character_id"));
        snapshot.set("pending_character_interaction",f.corpus.path("known_plan").path("pending_character_interaction"));
        var context=((ObjectNode)sourceBefore.path("context")).deepCopy();
        ((ObjectNode)context.get("definition")).put("canonical_key",key).put("deterministic_key_hash",12);
        // Reuse the canonical/hash pair from the existing synthetic unknown projection input.
        var input=new SourceReviewedInteractionContinuation.Input(
                Optional.of(RetainedJson.object(RetainedJson.parse(OfflineInteractionCorpus.bytes(snapshot)))),
                Optional.of(RetainedJson.object(RetainedJson.parse(OfflineInteractionCorpus.bytes(context)))),
                RetainedJson.parse(OfflineInteractionCorpus.bytes(sourceBefore.path("original_plan"))),
                List.of("reject-pending-character-interaction","accept-pending-character-interaction"),true);
        var trusted=TrustedEventSourceContext.open(f.sources);
        var plan=SourceReviewedInteractionContinuation.plan(input,trusted).orElseThrow();
        var capture=RetainedJson.object(plan.get("unhandled_interaction_fallback"));
        assertEquals(Boolean.FALSE,RetainedJson.bool(capture.get("registry_known")));
        assertEquals(Boolean.TRUE,RetainedJson.bool(capture.get("offline_followup_required")));
        var command=new ActionCommand(f.command.actionId(),identity,f.command.source(),f.command.sessionId(),
                f.command.operation(),DriverJson.object(RetainedJson.encode(plan),1<<20),f.command.expected(),f.command.claims(),f.command.deadline());
        var scope=IncidentJournalLayout.scope(f.incidents,f.scans,identity.machineId(),identity.game(),f.binding.sessionId(),
                identity.frame().episodeRunId(),f.binding.source().sourceRef());
        Files.createDirectory(scope.incidentRoot());Files.createDirectory(scope.scanRoot());Files.createDirectories(f.knowledge);Files.createDirectories(f.grants.getParent());
        var configuration=new EpisodeIncidentJournal.Configuration(scope.incidentRoot(),scope.scanRoot(),Clock.fixed(OfflineInteractionCorpus.NOW,ZoneOffset.UTC),
                pending->{if(pending<0||pending>(1<<20))throw new IOException("finite original corpus journal test cap");},Optional.of(trusted));
        var journal=EpisodeIncidentJournal.initialize(configuration,f.binding);
        var captured=journal.before(command).orElseThrow();var batch=journal.scan(f.binding).batch().orElseThrow();
        AtomicInteger completions=new AtomicInteger();var files=new NativeCheckpointFiles();Path work=Files.createDirectory(f.root.resolve("work"));
        OfflineAnalysisFiles.Port io=new OfflineAnalysisFiles.Port() {
            @Override public void directories(Path target)throws IOException{Files.createDirectories(target);}
            @Override public ExactRef createNew(Path target,byte[] raw)throws IOException{return files.createNew(target,raw).reference();}
            @Override public ExactRef replace(Path target,byte[] raw)throws IOException{return files.replace(target,raw).reference();}
            @Override public void beforeLock(Path target){assertTrue(target.startsWith(f.root));}
            @Override public void beforeLink(Path target,long bytes){assertTrue(target.startsWith(f.root));assertTrue(bytes>0);}
        };
        var settings=new OfflineEventAnalysisHost.Settings(true,false,Optional.of(f.grants),Optional.of(f.incidents),Optional.of(f.knowledge),Optional.of(f.scans));
        var host=OfflineAnalysisFiles.with(io,()->new OfflineEventAnalysisHost(Optional.of(f.sources),settings,Optional.of((original,report)->{
            assertEquals(batch,original);journal.acknowledge(original,report);completions.incrementAndGet();
        })));
        try(var worker=new OfflineAnalysisWorker(new OfflineAnalysisWorker.Settings(work,2,64),files,io)) {
            var binding=new OfflineAnalysisWorker.Binding(f.sources.machineId(),f.state,f.game,f.incidents,f.scans,f.knowledge,f.grants);
            var result=worker.bind(host,binding,io).enqueue(batch).completion().toCompletableFuture().get(30,TimeUnit.SECONDS);
            assertEquals(1,completions.get());assertEquals(batch.batchId(),result.batchId());
            assertTrue(journal.scan(f.binding).batch().isEmpty());assertEquals(1,journal.scan(f.binding).incompleteAfter());
            assertTrue(Files.exists(Path.of(captured.before().path())),"source research preserves the original native UNKNOWN/after gap");
            var grants=ProjectionEvidenceCodec.decode(Files.readAllBytes(Path.of(result.publishedKnowledge().path())));
            assertFalse(grants.isEmpty());assertTrue(result.persistedReviews().size()>1);
            assertNotEquals(f.grants,Path.of(result.publishedKnowledge().path()),"completion must preserve immutable committed knowledge bytes, not a mutable manifest SHA");
            boolean sourceBound=false;
            for(ExactRef review:result.persistedReviews()) {
                byte[] raw=Files.readAllBytes(Path.of(review.path()));
                if("xar.interaction-offline-source-facts/v1".equals(StrictJson.parse(raw,1<<20).path("schema").asText())) {
                    var facts=InteractionRegistryCodec.parseFacts(raw);
                    assertEquals(authoredRef.sha256(),facts.binding().sourceSha256());
                    assertEquals(authored.toString(),facts.paths().sourcePath());sourceBound=true;
                }
            }
            assertTrue(sourceBound,"actual source analysis must retain the authored input SHA and path");
            var repeated=SourceReviewedInteractionContinuation.plan(input,TrustedEventSourceContext.open(f.sources)).orElseThrow();
            assertEquals(Boolean.TRUE,RetainedJson.bool(RetainedJson.object(repeated.get("unhandled_interaction_fallback")).get("registry_known")));
        }
    }
}
