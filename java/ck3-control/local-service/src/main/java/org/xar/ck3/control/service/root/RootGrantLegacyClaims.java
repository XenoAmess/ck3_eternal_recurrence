package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.nativebridge.capabilities.interactions.*;
import org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.*;
import org.xar.ck3.control.platform.OriginalRuntimeHandoffProof;

/** Complete once-store census for distinct Java-managed and retired-Python original branches. */
public final class RootGrantLegacyClaims {
    private static final int FILES=512,PER_FILE=1048576,TOTAL=16777216;
    private static final int MAX_CENSUS_BYTES=16777216;
    private static final String LEGACY_SCHEMA="xar.java.grant-original-once-census/v1";
    private static final String JAVA_SCHEMA="xar.java.grant-once-census/v2";
    @FunctionalInterface public interface Work<T>{T run()throws IOException,InterruptedException;}
    private final RootRuntimeContext context;
    private final OriginalRuntimeHandoffProof.Provider provider;
    private final RootManagedSessionScope javaSession;
    private final List<ExactRef> implementationSources;
    private static final class CapturedCommand {
        private final ActionCommand command;
        private final byte[] original;
        private final RootManagedSessionScope.Observation observation;
        private CapturedCommand(ActionCommand command,byte[] original,List<ExactRef> sources) {
            this.command=command;this.original=original.clone();this.observation=RootManagedSessionScope.decode(this.original,command,sources);
        }
    }
    private final ThreadLocal<CapturedCommand> captured=new ThreadLocal<>();
    private final ThreadLocal<OriginalRuntimeHandoffProof.Lease> active=new ThreadLocal<>();
    RootGrantLegacyClaims(RootRuntimeContext context,OriginalRuntimeHandoffProof.Provider provider){this(context,provider,null);}
    private RootGrantLegacyClaims(RootRuntimeContext context,OriginalRuntimeHandoffProof.Provider provider,RootManagedSessionScope javaSession){this(context,provider,javaSession,List.of());}
    private RootGrantLegacyClaims(RootRuntimeContext context,OriginalRuntimeHandoffProof.Provider provider,RootManagedSessionScope javaSession,List<ExactRef> sources){this.context=java.util.Objects.requireNonNull(context);this.provider=java.util.Objects.requireNonNull(provider);this.javaSession=javaSession;this.implementationSources=List.copyOf(sources);}
    static RootGrantLegacyClaims forJavaSession(RootRuntimeContext context,OriginalRuntimeHandoffProof.Provider legacyProvider,
            KnownInteractionsRuntimeInstaller sameKnown,List<ExactRef> implementationSources)throws IOException {
        sameKnown.requireContext(context);return new RootGrantLegacyClaims(context,legacyProvider,RootManagedSessionScope.bind(context,implementationSources),implementationSources);
    }
    private Path store(){return context.game().launchPlan().stateDirectory().resolve("native-session").resolve("grant-title-picker-actions").toAbsolutePath().normalize();}
    void requireSourceFrame(org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete actual)throws IOException {
        if(javaSession!=null){javaSession.requireFrame(context.borrowedSession(),actual);return;}
        var paths=org.xar.ck3.control.planning.opportunity.OpportunityJson.object(actual.semantic().get("capability_session_paths"),"actual source-bound capability paths");
        Path driver=Path.of(org.xar.ck3.control.planning.opportunity.OpportunityJson.text(paths.get("driver_state_path"),"actual original Driver state path"));
        need(driver.isAbsolute()&&driver.getParent()!=null&&driver.toAbsolutePath().normalize().getParent().resolve("grant-title-picker-actions").equals(store()),"actual Native Driver Grant store differs from original launch store");
    }
    public <T>T withScope(Work<T> work)throws IOException,InterruptedException {
        if(javaSession!=null)return javaSession.withScope(()->{need(captured.get()==null,"Grant command capture may not be replaced recursively");try{return work.run();}finally{captured.remove();}});
        if(active.get()!=null)throw new IOException("Grant original-store lease may not be recursively replaced");
        var result=provider.withOriginalStore(store(),context.game().machineId(),lease->{
            active.set(lease);try{return work.run();}catch(InterruptedException interrupted){Thread.currentThread().interrupt();throw new IOException("Grant public call interrupted",interrupted);}finally{active.remove();}
        });
        if(result instanceof OriginalRuntimeHandoffProof.Available<T> available)return available.value();
        var missing=(OriginalRuntimeHandoffProof.Unavailable<T>)result;
        throw new IOException("Grant mutation original once-store custody unavailable: "+missing.reason()+": "+missing.detail());
    }
    /** Capture only while Root's actual preparation frame lease is held. Later hooks retain DATA, not the expired lease. */
    void captureCommand(Session same,org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete frame,ActionCommand command)throws IOException {
        if(javaSession==null)return;
        need(captured.get()==null,"Grant scope already captured a canonical command");
        byte[] frameObservation=javaSession.observe(same,frame);
        byte[] bound=RootManagedSessionScope.bindCommand(frameObservation,command,implementationSources);
        captured.set(new CapturedCommand(command,bound,implementationSources));
        javaSession.requireCurrent();
    }
    /** Invoked once in preparation and again by the original writer's before-INTENT hook. */
    public ExactRef requireClear(Session same,Context before,GrantRequest requested,ActionCommand command)throws IOException {
        context.writer().requireSession(same);var lease=active.get();boolean managed=javaSession!=null;
        CapturedCommand original=managed?captured.get():null;
        if(managed) {
            javaSession.requireCurrent();need(original!=null&&original.command.equals(command),"Grant lacks the private actual preparation-frame capture for this exact command");
            RootManagedSessionScope.verifyArchived(context.core(),same,original.original,command,implementationSources,original.observation.headDigest());
        }else {
            if(lease==null)throw new IOException("Grant mutation lacks original retired-runtime store lease");
            lease.requireCurrent();need(lease.originalStore().equals(store())&&lease.machineId().equals(context.game().machineId()),"Grant original store/machine changed");
        }
        need(command.before().equals(before.before())&&command.source().equals(before.source())&&command.sessionId().equals(before.sessionId())
                &&GrantPickerControlEffects.context(command).equals(before)&&GrantPickerControlEffects.request(command).equals(requested),"Grant census differs from its actual original command");
        Path directory=store(),parent=directory.getParent(),state=parent.getParent();
        var stateIdentity=managed?SharedSourceFiles.nativeDirectory(state):null;List<String> stateNames=managed?names(state):List.of();
        boolean parentPresent=Files.exists(parent,LinkOption.NOFOLLOW_LINKS);
        if(!managed)need(parentPresent,"original Python Grant parent is unavailable");
        var parentIdentity=parentPresent?SharedSourceFiles.nativeDirectory(parent):null;List<String> parentNames=parentPresent?names(parent):List.of();
        boolean present=Files.exists(directory,LinkOption.NOFOLLOW_LINKS);SharedSourceFiles.DirectoryIdentity identity=present?SharedSourceFiles.nativeDirectory(directory):null;
        List<String> roster=present?names(directory):List.of();var originals=new TreeMap<String,byte[]>();var pins=new ArrayList<SharedSourceFiles.Witness>();long total=0;
        var archive=context.archive().withSession(same);ObjectNode manifest=StrictJson.object().put("schema",managed?JAVA_SCHEMA:LEGACY_SCHEMA).put("machine_id",context.game().machineId())
                .put("original_store",directory.toString()).put("directory_present",present).put("capture_head_sha256",managed?original.observation.headDigest():same.head().digest());
        if(parentIdentity==null)manifest.putNull("parent_identity");else manifest.set("parent_identity",identity(parentIdentity));if(identity==null)manifest.putNull("directory_identity");else manifest.set("directory_identity",identity(identity));
        var parentRoster=manifest.putArray("complete_parent_names");parentNames.forEach(parentRoster::add);
        if(managed) {
            manifest.put("parent_present",parentPresent);manifest.set("state_directory_identity",identity(stateIdentity));
            var stateRoster=manifest.putArray("complete_state_names");stateNames.forEach(stateRoster::add);
            manifest.set("java_session_observation",archive.preserveMaterial(new RawJson(original.original)).toJson());
        } else manifest.set("original_runtime_observation",archive.preserveMaterial(new RawJson(lease.originalObservation())).toJson());
        var names=manifest.putArray("complete_names");roster.forEach(names::add);var rows=manifest.putArray("files");
        for(String name:roster) {
            need(name.matches("[0-9a-f]{64}\\.claim(?:\\.result|\\.resolved)?\\.json"),"unrecognized original Grant store entry; no partial census");
            Path file=directory.resolve(name);var witness=SharedSourceFiles.observe(file);need(witness.source().bytes()>0&&witness.source().bytes()<=PER_FILE,"original Grant file exceeds finite bound");
            total=Math.addExact(total,witness.source().bytes());need(total<=TOTAL,"whole original Grant census exceeds finite bound");
            byte[] bytes;try(var input=Files.newInputStream(file,LinkOption.NOFOLLOW_LINKS)){bytes=input.readNBytes(PER_FILE+1);}
            need(bytes.length==witness.source().bytes()&&ActionCodec.sha256(bytes).equals(witness.source().sha256()),"original Grant file changed while read");SharedSourceFiles.assertUnchanged(witness);
            pins.add(witness);originals.put(name,bytes);var row=rows.addObject().put("name",name);row.set("original",new ExactRef(witness.source().path(),witness.source().bytes(),witness.source().sha256()).toJson());row.put("native_identity",witness.nativeFile().identityKey());row.set("preserved",archive.preserveMaterial(new RawJson(bytes)).toJson());
        }
        // Java authority comes from the original managed Game/Core, not a missing or readable directory.
        if(managed)need(SharedSourceFiles.nativeDirectory(state).equals(stateIdentity)&&names(state).equals(stateNames),"Grant Java state directory identity/whole roster changed");
        need(Files.exists(parent,LinkOption.NOFOLLOW_LINKS)==parentPresent&&Files.exists(directory,LinkOption.NOFOLLOW_LINKS)==present,"original Grant ancestry/presence changed");
        if(parentPresent)need(SharedSourceFiles.nativeDirectory(parent).equals(parentIdentity)&&names(parent).equals(parentNames),"original Grant complete parent inventory changed");
        if(present)need(SharedSourceFiles.nativeDirectory(directory).equals(identity)&&names(directory).equals(roster),"original Grant complete inventory changed");
        for(var pin:pins)SharedSourceFiles.assertUnchanged(pin);if(managed)javaSession.requireCurrent();else lease.requireCurrent();
        List<String> blockers=blockers(originals,before,requested,managed);var blocked=manifest.putArray("blocking_original_claims");blockers.forEach(blocked::add);
        var ref=archive.preserveMaterial(new RawJson(StrictJson.canonical(manifest,MAX_CENSUS_BYTES)));
        need(blockers.isEmpty(),"original Grant claim unresolved or not independently releasable; no retry; census="+ref.path());
        return ref;
    }
    public void verifyOriginals(ActionCommand command,ActionState.Attempt attempt,ActionPorts.OutcomeArchive archive) {
        try{context.withSession(same->{verifyOriginals(context.core(),same,store(),implementationSources,command,attempt,archive);return null;});}
        catch(IOException invalid){throw new java.io.UncheckedIOException("Grant original writer history unavailable",invalid);}
    }
    /** Pure original archive consumer under the real writer. No Game, scope or new submission is created. */
    public static void verifyOriginals(RootApplicationAssembly.Core actualCore,Session same,Path actualStore,List<ExactRef> actualBusinessSources,
            ActionCommand command,ActionState.Attempt attempt,ActionPorts.OutcomeArchive archive)throws IOException {
        actualCore.writer().requireSession(same);Path store=actualStore.toAbsolutePath().normalize();
        need(actualStore.isAbsolute()&&actualStore.normalize().equals(actualStore)&&store.getFileName().toString().equals("grant-title-picker-actions"),"exact archived Grant store required");
        need(attempt.preparedRequest().preparationEvidence().size()==1,"Grant original preparation requires its complete immutable legacy census");
        ExactRef ref=attempt.preparedRequest().preparationEvidence().getFirst();RawJson raw=archive.loadMaterial(ref);need(ref.bytes()==raw.bytes().length&&ref.sha256().equals(ActionCodec.sha256(raw.bytes())),"Grant original census material changed");
        JsonNode parsed=StrictJson.parse(raw.bytes(),MAX_CENSUS_BYTES);String schema=StrictJson.text(parsed.get("schema"));boolean managed=JAVA_SCHEMA.equals(schema);
        need(managed||LEGACY_SCHEMA.equals(schema),"exact Grant census branch required");
        var fields=new java.util.HashSet<>(java.util.Set.of("schema","machine_id","original_store","directory_present","capture_head_sha256","parent_identity","directory_identity","complete_parent_names","complete_names","files","blocking_original_claims"));
        if(managed)fields.addAll(java.util.Set.of("parent_present","state_directory_identity","complete_state_names","java_session_observation"));else fields.add("original_runtime_observation");
        ObjectNode n=StrictJson.object(parsed,fields);
        need(StrictJson.text(n.get("machine_id")).equals(command.before().machineId())&&StrictJson.text(n.get("original_store")).equals(store.toString()),"Grant original census source/machine differs");
        need(n.get("directory_present").isBoolean()&&n.get("complete_names").isArray()&&n.get("files").isArray()&&n.get("files").size()<=FILES&&n.get("blocking_original_claims").isArray()&&n.get("blocking_original_claims").isEmpty(),"Grant original whole-census shape invalid");
        boolean parentPresent=!managed||n.get("parent_present").isBoolean()&&n.get("parent_present").booleanValue();
        if(managed) {
            need(n.get("parent_present").isBoolean()&&!actualBusinessSources.isEmpty(),"Java Grant census requires its distinct typed Java source closure");validateIdentity(n.get("state_directory_identity"));
            need(n.get("complete_state_names").isArray()&&n.get("complete_state_names").size()<=FILES,"whole Java state roster required");var stateNames=new java.util.HashSet<String>();
            n.get("complete_state_names").forEach(v->need(stateNames.add(StrictJson.text(v)),"duplicate Java state directory name"));
            need(stateNames.contains(store.getParent().getFileName().toString())==parentPresent,"Java state roster contradicts native-session presence");
        }
        if(parentPresent)validateIdentity(n.get("parent_identity"));else need(n.get("parent_identity").isNull()&&n.get("complete_parent_names").isArray()&&n.get("complete_parent_names").isEmpty()&&!n.get("directory_present").booleanValue(),"missing Java parent cannot contain a Grant store");
        if(n.get("directory_present").booleanValue())validateIdentity(n.get("directory_identity"));else need(n.get("directory_identity").isNull()&&n.get("files").isEmpty(),"missing Grant directory cannot have files or identity");
        need(n.get("complete_parent_names").isArray()&&n.get("complete_parent_names").size()<=FILES,"Grant original complete parent roster required");var parentNames=new java.util.HashSet<String>();n.get("complete_parent_names").forEach(v->need(parentNames.add(StrictJson.text(v)),"duplicate Grant original parent name"));need(parentNames.contains(store.getFileName().toString())==n.get("directory_present").booleanValue(),"Grant original parent inventory contradicts directory presence");
        var runtimeRef=ExactRef.fromJson(n.get(managed?"java_session_observation":"original_runtime_observation"));RawJson originalRuntime=archive.loadMaterial(runtimeRef);need(runtimeRef.bytes()==originalRuntime.bytes().length&&runtimeRef.sha256().equals(ActionCodec.sha256(originalRuntime.bytes())),"Grant original runtime observation changed");
        if(managed)RootManagedSessionScope.verifyArchived(actualCore,same,originalRuntime.bytes(),command,actualBusinessSources,StrictJson.text(n.get("capture_head_sha256")));
        else verifyLegacyRuntime(originalRuntime,command,store);
        var originals=new TreeMap<String,byte[]>();var names=new ArrayList<String>();long total=0;
        for(JsonNode row:n.get("files")){String name=StrictJson.text(row.get("name"));need(name.matches("[0-9a-f]{64}\\.claim(?:\\.result|\\.resolved)?\\.json")&&!originals.containsKey(name),"Grant original roster duplicate/invalid");
            var source=ExactRef.fromJson(row.get("original"));var preserved=ExactRef.fromJson(row.get("preserved"));RawJson bytes=archive.loadMaterial(preserved);
            need(source.bytes()>0&&source.bytes()<=PER_FILE&&source.bytes()==preserved.bytes()&&source.sha256().equals(preserved.sha256())&&preserved.bytes()==bytes.bytes().length&&preserved.sha256().equals(ActionCodec.sha256(bytes.bytes()))&&Path.of(source.path()).equals(store.resolve(name)),"Grant original file closure differs");
            need(StrictJson.text(row.get("native_identity")).matches("[0-9]+:[0-9]+:[0-9]+"),"Grant original Win32 identity absent");total+=source.bytes();need(total<=TOTAL,"Grant original whole file bound exceeded");originals.put(name,bytes.bytes());names.add(name);
        }
        var roster=new ArrayList<String>();n.get("complete_names").forEach(v->roster.add(StrictJson.text(v)));need(names.equals(roster)&&blockers(originals,GrantPickerControlEffects.context(command),GrantPickerControlEffects.request(command),managed).isEmpty(),"Grant replay has incomplete inventory or an original blocker");
    }
    private static void verifyLegacyRuntime(RawJson original,ActionCommand command,Path store) {
        JsonNode parsed=StrictJson.parse(original.bytes(),1048576);JsonNode values=parsed.get("original_sources");need(values!=null&&values.isArray(),"complete original Python Grant sources required");
        var refs=new ArrayList<ExactRef>();values.forEach(value->refs.add(ExactRef.fromJson(value)));
        try{org.xar.ck3.control.platform.OriginalRuntimeHandoffObservation.decode(org.xar.ck3.control.platform.OriginalRuntimeHandoffObservation.Scope.GRANT,original.bytes(),store,command.before().machineId(),refs);}
        catch(IOException invalid){throw new java.io.UncheckedIOException("original Python Grant retirement DATA unavailable",invalid);}
    }
    private static ObjectNode identity(SharedSourceFiles.DirectoryIdentity value){return StrictJson.object().put("volume_serial_decimal",value.volumeSerialDecimal()).put("file_id_decimal",value.fileIdDecimal()).put("creation_filetime_decimal",value.creationFiletimeDecimal());}
    private static void validateIdentity(JsonNode n){ObjectNode value=StrictJson.object(n,java.util.Set.of("volume_serial_decimal","file_id_decimal","creation_filetime_decimal"));new SharedSourceFiles.DirectoryIdentity(StrictJson.text(value.get("volume_serial_decimal")),StrictJson.text(value.get("file_id_decimal")),StrictJson.text(value.get("creation_filetime_decimal")));}
    /** Full original result and resolver must agree. A resolver filename alone cannot release old UNKNOWN. */
    public static List<String> blockers(Map<String,byte[]> originals,Context current,GrantRequest requested) {
        return blockers(originals,current,requested,false);
    }
    /** Pure comparison only. A replacement Java Game cannot erase an old unresolved logical episode scope. */
    public static List<String> blockersAcrossJavaReplacement(Map<String,byte[]> originals,Context current,GrantRequest requested) {
        return blockers(originals,current,requested,true);
    }
    private static List<String> blockers(Map<String,byte[]> originals,Context current,GrantRequest requested,boolean includeReplacements) {
        var blockers=new ArrayList<String>();
        for(var entry:originals.entrySet())if(entry.getKey().endsWith(".claim.json")) {
            ObjectNode claim=StrictJson.object(StrictJson.parse(entry.getValue(),PER_FILE),java.util.Set.of("request_id","scope","identity","status"));
            need(StrictJson.text(claim.get("status")).equals("claimed_result_unknown_no_retry"),"original Grant claim state malformed");
            ObjectNode scope=StrictJson.object(claim.get("scope"),java.util.Set.of("game_pid","played_character_id","episode_run_id","recipient_id","operation"));
            long pid=StrictJson.integer(scope.get("game_pid"),java.math.BigInteger.ONE,new java.math.BigInteger("4294967295")).longValueExact();
            long actor=full(scope.get("played_character_id")),recipient=full(scope.get("recipient_id"));String episode=StrictJson.text(scope.get("episode_run_id")),operation=StrictJson.text(scope.get("operation"));
            need(List.of("prepare","select","send").contains(operation),"original Grant claim operation invalid");
            if((!includeReplacements&&pid!=current.before().game().pid())||actor!=current.actor().longValueExact()||recipient!=requested.recipient().value()||!episode.equals(current.controls().episodeRunId())||!operation.equals(requested.operation().wire()))continue;
            String stem=entry.getKey().substring(0,entry.getKey().length()-5);byte[] resolved=originals.get(stem+".resolved.json"),result=originals.get(stem+".result.json");
            boolean released=false;
            if(resolved!=null&&result!=null)try {
                var r=StrictJson.object(StrictJson.parse(resolved,PER_FILE),java.util.Set.of("request_id","status","transfer_verified"));var outcome=StrictJson.object(StrictJson.parse(result,PER_FILE),java.util.Set.of("request_id","result"));
                String requestId=StrictJson.text(claim.get("request_id"));need(requestId.equals(StrictJson.text(r.get("request_id")))&&requestId.equals(StrictJson.text(outcome.get("request_id")))&&StrictJson.text(r.get("status")).equals("original_result_observed"),"original Grant resolver request mismatch");
                var identity=StrictJson.object(claim.get("identity"),java.util.Set.of("scope","public_revision","fields"));need(identity.get("scope").equals(scope),"old Grant identity scope differs");
                JsonNode fields=identity.get("fields");GrantRequest original=fromFields(requested.operation(),recipient,fields);
                GrantResult nativeResult=GrantTitleCodec.decode(new RawJson(StrictJson.canonical(outcome.get("result"))),current,original);
                need(r.get("transfer_verified").isBoolean()&&r.get("transfer_verified").booleanValue()==nativeResult.transferVerified(),"original Grant resolved transfer differs from packet");
                released=!nativeResult.dispatched()||(original.operation()==GrantOperation.SEND?nativeResult.transferVerified():nativeResult.nativeCompleted()&&nativeResult.frameVerified());
            }catch(IllegalArgumentException malformed){released=false;}
            if(!released)blockers.add(entry.getKey());
        }
        return List.copyOf(blockers);
    }
    private static GrantRequest fromFields(GrantOperation operation,long recipient,JsonNode fields) {
        need(fields!=null&&fields.isObject()&&full(fields.get("recipient_character_full_id"))==recipient,"old Grant request fields recipient invalid");
        List<FullId> targets=csv(fields.get("requested_title_full_ids")),selected=csv(fields.get("expected_selected_title_full_ids"));
        java.util.Optional<FullId> title=operation==GrantOperation.SELECT?java.util.Optional.of(new FullId(full(fields.get("title_full_id")))):java.util.Optional.empty();
        java.util.Optional<Boolean> desired=java.util.Optional.empty();if(operation==GrantOperation.SELECT){need(fields.get("desired_selected")!=null&&fields.get("desired_selected").isBoolean(),"old Grant desired selection is not boolean");desired=java.util.Optional.of(fields.get("desired_selected").booleanValue());}
        return new GrantRequest(operation,new CharacterId(recipient),targets,selected,title,desired);
    }
    private static List<FullId> csv(JsonNode n){need(n!=null&&n.isTextual(),"old Grant CSV must be a string");String value=n.textValue();if(value.isEmpty())return List.of();var rows=new ArrayList<FullId>();for(String item:value.split(",",-1)){need(item.matches("0|[1-9][0-9]{0,9}"),"old Grant CSV is noncanonical");rows.add(new FullId(Long.parseLong(item)));}return List.copyOf(rows);}
    private static long full(JsonNode n){return StrictJson.integer(n,java.math.BigInteger.ZERO,new java.math.BigInteger("4294967294")).longValueExact();}
    private static List<String> names(Path directory)throws IOException {var rows=new ArrayList<String>();try(var stream=Files.newDirectoryStream(directory)){for(Path path:stream){need(rows.size()<FILES,"whole original directory exceeds finite roster bound");rows.add(path.getFileName().toString());}}rows.sort(String::compareTo);return List.copyOf(rows);}
    private static void need(boolean value,String reason){StrictJson.require(value,reason);}
}
