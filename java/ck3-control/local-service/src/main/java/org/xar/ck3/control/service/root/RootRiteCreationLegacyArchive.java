package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.ritecreation.RiteCreationDomainState;
import org.xar.ck3.control.application.ritecreation.RiteCreationLegacyStore;
import org.xar.ck3.control.application.ritecreation.RiteCreationLegacyStore.*;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.continuity.writer.NativeOutcomeArchive;
import org.xar.ck3.control.contracts.ExactRef;
import static org.xar.ck3.control.application.ritecreation.RiteCreationCodec.*;
import static org.xar.ck3.control.application.ritecreation.RiteCreationContract.need;

/** Cold/current replay of already admitted original artifacts. Never mints custody or reads the old live store. */
final class RootRiteCreationLegacyArchive {
    private RootRiteCreationLegacyArchive() { }
    static void requireOriginalClosure(NativeOutcomeArchive archive,Session same,RiteCreationDomainState state)throws IOException{
        if(state.legacyStore().isPresent()){
            Imported retained=state.legacyStore().orElseThrow();Optional<Imported> replay=Optional.empty();
            for(ExactRef manifest:retained.custodyManifests())replay=Optional.of(RiteCreationLegacyStore.merge(replay,RiteCreationLegacyStore.parse(image(archive,same,manifest),manifest)));
            need(replay.equals(Optional.of(retained)),"complete original once archive reducer disagrees with canonical retained status/history; no final confirmation");
        }
        for(var opaque:state.unresolvedOpaqueOriginals()){
            Image captured=image(archive,same,opaque.originalManifest());boolean failed=false;
            try{RiteCreationLegacyStore.parse(captured,opaque.originalManifest());}
            catch(IllegalArgumentException|ArithmeticException|java.time.DateTimeException original){failed=true;need(opaque.reason().equals("original once capture remains UNKNOWN: "+original.getClass().getSimpleName()),"original opaque diagnosis/reducer changed");}
            need(failed,"opaque original history no longer reproduces its original failure; no implicit repair or UNKNOWN erasure");
        }
    }
    private static Image image(NativeOutcomeArchive archive,Session same,ExactRef manifest)throws IOException{
        ObjectNode n=object(archive.withSession(same).loadMaterial(manifest));
        shape(n,Set.of("schema","machine_id","original_store","directory_present","capture_head_sha256","original_owned_runtime_observation","original_custody_source_evidence","complete_relevant_roster","original_results_absent","files"),Set.of());
        equal(get(n,"schema"),"xar.java.rite-original-store-capture/v1");need(text(get(n,"capture_head_sha256")).matches("[0-9a-f]{64}"),"original capture Head digest missing");
        boolean directory=bool(get(n,"directory_present"));
        byte[] observation=archive.readArtifact(same,ExactRef.fromJson(get(n,"original_owned_runtime_observation")),RootRiteCreationLegacyImport.MAX_FILE);
        need(observation.length>0,"original archived kernel/source/store observation missing; JSON cannot become new custody");
        JsonNode sourceRefs=get(n,"original_custody_source_evidence");need(sourceRefs.isArray()&&!sourceRefs.isEmpty()&&sourceRefs.size()<=256,"original custody source roster missing");for(JsonNode source:sourceRefs)ExactRef.fromJson(source);
        JsonNode rows=get(n,"files"),roster=get(n,"complete_relevant_roster"),absent=get(n,"original_results_absent");need(rows.isArray()&&rows.size()<=512&&roster.isArray()&&roster.size()<=512&&absent.isArray()&&absent.size()<=256,"bounded complete original captured closure required");
        var files=new ArrayList<OriginalFile>();long total=0;
        for(JsonNode row:rows){Evidence evidence=RiteCreationLegacyStore.evidence(row);byte[] bytes=archive.readArtifact(same,evidence.preserved(),RootRiteCreationLegacyImport.MAX_FILE);total=Math.addExact(total,bytes.length);need(total<=RootRiteCreationLegacyImport.MAX_TOTAL,"original archived capture exceeds its actual bound");files.add(new OriginalFile(evidence,bytes));}
        var names=new ArrayList<String>();for(JsonNode name:roster)names.add(text(name));
        var missing=new HashSet<String>();for(JsonNode value:absent){String name=text(value);need(name.matches("[0-9a-f]{64}\\.rite-action-[0-9a-f]{32}\\.native-result\\.json")&&missing.add(name)&&!names.contains(name),"original absent packet observation changed or overlaps captured files");}
        need(directory||files.isEmpty()&&missing.isEmpty(),"original nonexistent store cannot contain captured files or missing packet claims");
        return new Image(text(get(n,"machine_id")),text(get(n,"original_store")),names,files);
    }
}
