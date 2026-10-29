package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Comparator;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.ritecreation.RiteCreationLegacyStore;
import org.xar.ck3.control.application.ritecreation.RiteCreationLegacyStore.*;
import org.xar.ck3.control.application.ritecreation.RiteCreationDomainState;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.continuity.writer.WriterContracts.Pin;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.platform.OriginalRuntimeHandoffProof;
import static org.xar.ck3.control.application.ritecreation.RiteCreationCodec.*;
import static org.xar.ck3.control.application.ritecreation.RiteCreationContract.need;

/** Reads the original store only while its actual platform custody lease and the one writer lock are held. */
final class RootRiteCreationLegacyImport {
    static final int MAX_FILE=1024*1024,MAX_TOTAL=64*1024*1024;
    private static final String SCHEMA="xar.java.rite-original-store-capture/v1";
    private final RootRuntimeContext context;private final RootRiteCreationDomain domain;
    RootRiteCreationLegacyImport(RootRuntimeContext context,RootRiteCreationDomain domain){this.context=Objects.requireNonNull(context);this.domain=Objects.requireNonNull(domain);}
    static Path actualStore(RootRuntimeContext context){return context.game().launchPlan().stateDirectory().resolve("native-session").resolve("rite-creation-actions").toAbsolutePath().normalize();}
    record Publication(DomainBodies.BodyRef body,ExactRef originalManifest,boolean qualified,String diagnosis){ }
    Publication importOriginal(Session same,OriginalRuntimeHandoffProof.Lease lease)throws IOException{
        domain.requireContext(context,same);requireLease(lease);Capture capture=capture(same,lease);var input=empty().put("kind","original_python_rite_once_store_import");input.set("original_manifest",capture.manifest().toJson());
        final RiteCreationLegacyStore.Imported parsed;try{parsed=RiteCreationLegacyStore.parse(capture.image(),capture.manifest());}
        catch(IllegalArgumentException|ArithmeticException|java.time.DateTimeException invalid){
            String reason="original once capture remains UNKNOWN: "+invalid.getClass().getSimpleName();
            DomainBodies.BodyRef quarantined=domain.publishFull(same,raw(input),List.of(capture.manifest()),(original,previous)->{capture.requireCurrent(original,lease);verifyManifest(original,capture);return previous.orElseThrow(()->new IOException("actual Rite v2 basis absent")).quarantine(new RiteCreationDomainState.OpaqueOriginalCapture(capture.manifest(),reason));});
            capture.requireCurrent(same,lease);return new Publication(quarantined,capture.manifest(),false,reason);
        }
        DomainBodies.BodyRef published=domain.publishFull(same,raw(input),List.of(capture.manifest()),(original,previous)->{
            capture.requireCurrent(original,lease);Image actual=verifyManifest(original,capture);var replay=RiteCreationLegacyStore.parse(actual,capture.manifest());need(replay.equals(parsed),"actual original once parser/reducer changed before commit");return previous.orElseThrow(()->new IOException("actual Rite v2 basis absent")).imported(replay);
        });capture.requireCurrent(same,lease);return new Publication(published,capture.manifest(),true,"original once history retained; no action, payment, business or retry credit");
    }
    private void requireLease(OriginalRuntimeHandoffProof.Lease lease)throws IOException{
        lease.requireCurrent();need(lease.machineId().equals(context.game().machineId())&&lease.originalStore().toAbsolutePath().normalize().equals(actualStore(context)),"original store custody belongs to another machine or actual managed state directory");
    }
    private final class Capture{
        private final Image image;private final ExactRef manifest;private final List<Pin> originals;private final List<String> claimRoster,absentResults;private final boolean directoryPresent;private final byte[] observation;
        private Capture(Image image,ExactRef manifest,List<Pin> originals,List<String> claimRoster,List<String> absentResults,boolean directoryPresent,byte[] observation){this.image=image;this.manifest=manifest;this.originals=List.copyOf(originals);this.claimRoster=List.copyOf(claimRoster);this.absentResults=List.copyOf(absentResults);this.directoryPresent=directoryPresent;this.observation=observation.clone();}
        Image image(){return image;}ExactRef manifest(){return manifest;}
        void requireCurrent(Session same,OriginalRuntimeHandoffProof.Lease lease)throws IOException{
            domain.requireContext(context,same);requireLease(lease);Path store=actualStore(context);need(Files.exists(store,LinkOption.NOFOLLOW_LINKS)==directoryPresent&&roster(store).equals(claimRoster),"original once store complete roster changed during actual custody");
            for(String missing:absentResults)need(!Files.exists(store.resolve(missing),LinkOption.NOFOLLOW_LINKS),"original late packet appeared during the captured transaction; recapture instead of guessing");for(Pin pin:originals)same.verifyPin(pin);need(Arrays.equals(observation,lease.originalObservation()),"actual original-runtime exit/custody observation changed");lease.requireCurrent();
        }
    }
    private Capture capture(Session same,OriginalRuntimeHandoffProof.Lease lease)throws IOException{
        requireLease(lease);Path store=actualStore(context);boolean present=Files.exists(store,LinkOption.NOFOLLOW_LINKS);List<String> names=roster(store);var files=new ArrayList<OriginalFile>();var pins=new ArrayList<Pin>();var missing=new ArrayList<String>();var results=new LinkedHashSet<String>();long total=0;
        for(String name:names){OriginalFile file=original(same,store.resolve(name),pins);total=Math.addExact(total,file.bytes().length);need(total<=MAX_TOTAL,"actual original once store exceeds its finite capture byte allowance");files.add(file);
            // Preserve malformed claim bytes as opaque UNKNOWN; never replace the actual original with a fabricated empty claim.
            try{ObjectNode n=object(new RawJson(file.bytes()));if(name.endsWith(".safe-no-dispatch.json"))n=object(get(n,"original_claim"));String leaf=text(get(n,"native_result_file"));if(leaf.matches("[0-9a-f]{64}\\.rite-action-[0-9a-f]{32}\\.native-result\\.json"))results.add(leaf);}
            catch(IllegalArgumentException malformed){/* The complete preserved original is classified by the actual parser below. */}
        }
        for(String result:results){if(files.stream().anyMatch(v->v.evidence().leaf().equals(result)))continue;Path source=store.resolve(result);if(Files.exists(source,LinkOption.NOFOLLOW_LINKS)){OriginalFile file=original(same,source,pins);total=Math.addExact(total,file.bytes().length);need(total<=MAX_TOTAL,"actual original once packet closure exceeds finite capture byte allowance");files.add(file);}else missing.add(result);}
        files.sort(Comparator.comparing(v->v.evidence().leaf()));var complete=files.stream().map(v->v.evidence().leaf()).toList();Image image=new Image(context.game().machineId(),store.toString(),complete,files);
        byte[] observation=lease.originalObservation();need(observation.length>0&&observation.length<=MAX_FILE,"actual original owned-runtime kernel observation required");ExactRef observed=context.archive().preserveArtifact(same,observation,MAX_FILE);
        ObjectNode manifest=empty().put("schema",SCHEMA).put("machine_id",context.game().machineId()).put("original_store",store.toString()).put("directory_present",present).put("capture_head_sha256",same.head().digest());manifest.set("original_owned_runtime_observation",observed.toJson());var proof=manifest.putArray("original_custody_source_evidence");lease.originalEvidence().forEach(v->proof.add(v.toJson()));var roster=manifest.putArray("complete_relevant_roster");complete.forEach(roster::add);var absent=manifest.putArray("original_results_absent");missing.stream().sorted().forEach(absent::add);var entries=manifest.putArray("files");files.forEach(v->entries.add(RiteCreationLegacyStore.evidence(v.evidence())));
        RawJson raw=raw(manifest);ExactRef ref=context.archive().withSession(same).preserveMaterial(raw);need(raw.equals(context.archive().withSession(same).loadMaterial(ref)),"complete original once manifest archive readback differs");
        Capture actual=new Capture(image,ref,pins,names,missing,present,observation);actual.requireCurrent(same,lease);return actual;
    }
    private OriginalFile original(Session same,Path path,List<Pin> pins)throws IOException{
        SharedSourceFiles.plainAncestors(path);need(Files.isRegularFile(path,LinkOption.NOFOLLOW_LINKS),"actual original once file is not a plain regular file");long length=Files.size(path);need(length>=0&&length<=MAX_FILE,"one original once file exceeds its actual finite input limit");byte[] observed;try(var input=Files.newInputStream(path)){observed=input.readNBytes(MAX_FILE+1);}need(observed.length==length,"original once input changed while bounded reading");ExactRef source=new ExactRef(path.toAbsolutePath().normalize().toString(),length,ActionCodec.sha256(observed));Pin pin=same.capturePin(source,MAX_FILE);byte[] bytes=same.readPinned(pin,MAX_FILE);same.verifyPin(pin);
        ExactRef preserved=context.archive().preserveArtifact(same,bytes,MAX_FILE);need(Arrays.equals(bytes,context.archive().readArtifact(same,preserved,MAX_FILE)),"original once bytes changed in immutable artifact preservation");pins.add(pin);return new OriginalFile(new Evidence(path.getFileName().toString(),source,pin.identity(),preserved),bytes);
    }
    private static List<String> roster(Path store)throws IOException{
        if(!Files.exists(store,LinkOption.NOFOLLOW_LINKS))return List.of();SharedSourceFiles.plainAncestors(store);need(Files.isDirectory(store,LinkOption.NOFOLLOW_LINKS),"original once store is not an actual plain directory");var names=new ArrayList<String>();int scanned=0,active=0,released=0,packets=0;
        try(var entries=Files.newDirectoryStream(store)){for(Path file:entries){need(++scanned<=8192,"bounded complete original once directory enumeration exceeded");String leaf=file.getFileName().toString();if(leaf.endsWith(".claim.json")){need(++active<=128,"original active claim bound exceeded");names.add(leaf);}else if(leaf.endsWith(".safe-no-dispatch.json")){need(++released<=128,"original released claim bound exceeded");names.add(leaf);}else if(leaf.matches("[0-9a-f]{64}.*")&&leaf.endsWith(".native-result.json")){need(++packets<=256,"original final packet bound exceeded");names.add(leaf);}}}names.sort(String::compareTo);return List.copyOf(names);
    }
    private Image verifyManifest(Session same,Capture capture)throws IOException{
        var archive=context.archive().withSession(same);ObjectNode n=object(archive.loadMaterial(capture.manifest()));shape(n,Set.of("schema","machine_id","original_store","directory_present","capture_head_sha256","original_owned_runtime_observation","original_custody_source_evidence","complete_relevant_roster","original_results_absent","files"),Set.of());equal(get(n,"schema"),SCHEMA);equal(get(n,"machine_id"),context.game().machineId());equal(get(n,"original_store"),actualStore(context).toString());equal(get(n,"capture_head_sha256"),same.head().digest());
        need(Arrays.equals(context.archive().readArtifact(same,ExactRef.fromJson(get(n,"original_owned_runtime_observation")),MAX_FILE),capture.observation),"actual original runtime exit/readonly observation bytes differ");var entries=get(n,"files");need(entries.isArray()&&entries.size()<=512,"bounded complete actual legacy manifest files required");var files=new ArrayList<OriginalFile>();for(var entry:entries){Evidence evidence=RiteCreationLegacyStore.evidence(entry);files.add(new OriginalFile(evidence,context.archive().readArtifact(same,evidence.preserved(),MAX_FILE)));}
        var names=get(n,"complete_relevant_roster");need(names.isArray()&&names.size()<=512,"actual complete relevant roster required");var roster=new ArrayList<String>();names.forEach(v->roster.add(text(v)));Image actual=new Image(context.game().machineId(),actualStore(context).toString(),roster,files);need(actual.completeRelevantRoster().equals(capture.image().completeRelevantRoster())&&actual.files().stream().map(OriginalFile::evidence).toList().equals(capture.image().files().stream().map(OriginalFile::evidence).toList()),"original once manifest closure changed before actual replay");return actual;
    }
}
