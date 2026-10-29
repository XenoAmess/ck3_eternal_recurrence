package org.xar.ck3.control.application.ritecreation;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.action.NativeStepDiscriminator.RiteCreation;
import org.xar.ck3.control.continuity.writer.WriterContracts.FileIdentity;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.ManagedCampaignRunBinding;
import org.xar.ck3.control.contracts.LegacyWindowsPathCanonicalizer;
import static org.xar.ck3.control.application.ritecreation.RiteCreationContract.*;
import static org.xar.ck3.control.application.ritecreation.RiteCreationCodec.*;

/** Original filesystem once data. A legacy intent is never a fabricated Java ActionReceipt or PlanningReadReceipt. */
public final class RiteCreationLegacyStore {
    private RiteCreationLegacyStore(){}
    public static final String CLAIM_SCHEMA="xar.ck3-rite-confirm-once.v1",RELEASE_SCHEMA="xar.ck3-rite-confirm-known-no-dispatch.v1";
    public enum Status{ORIGINAL_UNKNOWN_NO_RETRY,ORIGINAL_NATIVE_RESULT_NO_RETRY,ORIGINAL_KNOWN_NO_DISPATCH_RELEASED}
    public record Evidence(String leaf,ExactRef original,FileIdentity nativeIdentity,ExactRef preserved){
        public Evidence{need(leaf!=null&&!leaf.isEmpty()&&!leaf.contains("/")&&!leaf.contains("\\")&&!leaf.equals(".")&&!leaf.equals(".."),"single original Rite store filename required");Objects.requireNonNull(original);Objects.requireNonNull(nativeIdentity);Objects.requireNonNull(preserved);need(original.bytes()>=0&&original.bytes()==nativeIdentity.bytes()&&original.bytes()==preserved.bytes()&&original.sha256().equals(preserved.sha256()),"legacy original/native identity/preserved bytes differ");}}
    public record OriginalFile(Evidence evidence,byte[] bytes){public OriginalFile{Objects.requireNonNull(evidence);bytes=Objects.requireNonNull(bytes).clone();need(bytes.length<=RawJson.MAXIMUM_BYTES&&bytes.length==evidence.original().bytes()&&ActionCodec.sha256(bytes).equals(evidence.original().sha256()),"legacy actual file bytes differ from their native identity/source hash");}@Override public byte[] bytes(){return bytes.clone();}}
    public record Binding(BigInteger nativeRevision,BigInteger connectionGeneration,BigInteger gamePid,BigInteger nativeActor,BigInteger nativeDate,Scope scope,Optional<ManagedCampaignRunBinding> originalManagedBinding) implements ExpectedNativeBinding{
        public Binding{revision(nativeRevision);revision(connectionGeneration);need(gamePid!=null&&gamePid.signum()>0&&nativeActor!=null&&nativeActor.signum()>0,"original legacy positive Game/actor required");Objects.requireNonNull(nativeDate);Objects.requireNonNull(scope);Objects.requireNonNull(originalManagedBinding);need((scope instanceof ManagedScope)==originalManagedBinding.isPresent(),"legacy managed scope/binding presence differs");}}
    public record Intent(ActionId id,Binding binding,SourceRite source,Confirm request,String originalClaimKey,RawJson originalClaim,
            List<Evidence> claimAndReleaseEvidence,Optional<Evidence> originalNativeResult,Optional<String> originalResultFailure,Status status){
        public Intent{Objects.requireNonNull(id);Objects.requireNonNull(binding);Objects.requireNonNull(source);Objects.requireNonNull(request);need(originalClaimKey!=null&&originalClaimKey.matches("[0-9a-f]{64}"),"original Python claim digest required");Objects.requireNonNull(originalClaim);claimAndReleaseEvidence=List.copyOf(claimAndReleaseEvidence);need(!claimAndReleaseEvidence.isEmpty()&&claimAndReleaseEvidence.size()<=2,"original active/released claim custody required");Objects.requireNonNull(originalNativeResult);Objects.requireNonNull(originalResultFailure);Objects.requireNonNull(status);need(originalResultFailure.isEmpty()||status==Status.ORIGINAL_UNKNOWN_NO_RETRY,"unqualified original result must remain unknown");}
        public boolean blocksRetry(){return status!=Status.ORIGINAL_KNOWN_NO_DISPATCH_RELEASED;}
        public boolean matches(RiteCreationState.Key actual){return binding.scope().equals(actual.scope())&&binding.nativeActor().equals(BigInteger.valueOf(actual.actor()))&&source.equals(actual.source());}
        public NativeFields fields(){return new NativeFields(RiteCreation.CONFIRM_ONCE,source,Optional.of(request),Optional.of(id.value()));}
    }
    public record Image(String machineId,String actualCanonicalStore,List<String> completeRelevantRoster,List<OriginalFile> files){
        public Image{need(machineId!=null&&!machineId.isBlank()&&actualCanonicalStore!=null&&!actualCanonicalStore.isBlank(),"actual original machine/store authority required");completeRelevantRoster=List.copyOf(completeRelevantRoster);files=List.copyOf(files);need(completeRelevantRoster.size()<=512&&completeRelevantRoster.stream().distinct().count()==completeRelevantRoster.size()&&files.size()<=512&&files.stream().map(v->v.evidence().leaf()).distinct().count()==files.size(),"bounded unique complete original once roster required");need(Set.copyOf(completeRelevantRoster).equals(files.stream().map(v->v.evidence().leaf()).collect(java.util.stream.Collectors.toSet())),"legacy complete relevant roster differs from actual captured files");}
        public OriginalFile require(String leaf){return files.stream().filter(v->v.evidence().leaf().equals(leaf)).findFirst().orElseThrow(()->new IllegalArgumentException("missing original legacy file: "+leaf));}
    }
    public record Imported(ExactRef originalManifest,List<ExactRef> custodyManifests,List<Intent> intents){
        public Imported{Objects.requireNonNull(originalManifest);custodyManifests=List.copyOf(custodyManifests);need(!custodyManifests.isEmpty()&&custodyManifests.size()<=512&&custodyManifests.contains(originalManifest)&&custodyManifests.stream().distinct().count()==custodyManifests.size(),"complete bounded original custody history required");intents=List.copyOf(intents);need(intents.size()<=256&&intents.stream().map(Intent::id).distinct().count()==intents.size(),"bounded unique complete original once history required");for(int i=0;i<intents.size();i++)for(int j=i+1;j<intents.size();j++)need(!intents.get(i).blocksRetry()||!intents.get(j).blocksRetry()||!sameKey(intents.get(i),intents.get(j)),"duplicate unresolved original legacy intent scope");}
        public Imported(ExactRef manifest,List<Intent> intents){this(manifest,List.of(manifest),intents);}
    }
    private record ClaimData(ActionId id,Binding binding,SourceRite source,Confirm request,String key,RawJson original,String resultLeaf){ }
    public static Imported parse(Image image,ExactRef manifest){
        List<Intent> all=new ArrayList<>();var referencedResults=new HashSet<String>();int active=0,released=0;
        for(OriginalFile file:image.files()){
            String leaf=file.evidence().leaf();boolean claim=leaf.matches("[0-9a-f]{64}\\.claim\\.json"),safe=leaf.matches("rite-action-[0-9a-f]{32}\\.safe-no-dispatch\\.json");need(!leaf.endsWith(".claim.json")||claim,"malformed original claim filename");need(!leaf.endsWith(".safe-no-dispatch.json")||safe,"malformed original release filename");if(!claim&&!safe)continue;
            if(claim)need(++active<=128,"original active claim lookup exceeded128");else need(++released<=128,"bounded original retired claim lookup exceeded128");
            ObjectNode n=object(new RawJson(file.bytes()));Optional<String> releaseReason=Optional.empty();RawJson claimRaw=new RawJson(file.bytes());
            if(safe){shape(n,Set.of("schema","machine_id","observed_at_utc","reason","original_claim","automatic_retry"),Set.of());equal(get(n,"schema"),RELEASE_SCHEMA);equal(get(n,"machine_id"),image.machineId());Instant.parse(text(get(n,"observed_at_utc")));no(get(n,"automatic_retry"));String reason=text(get(n,"reason"));need(Set.of("existing_primitive_rejected_before_endpoint_send","matching_original_native_result_proves_no_dispatch_and_no_possible_queue","matching_late_native_result_proves_no_dispatch_and_no_possible_queue").contains(reason),"unknown original safe-release producer reason");releaseReason=Optional.of(reason);claimRaw=raw(get(n,"original_claim"));}
            ClaimData data=claim(claimRaw,image.machineId());referencedResults.add(data.resultLeaf());need(claim?leaf.equals(data.key()+".claim.json"):leaf.equals(data.id().value()+".safe-no-dispatch.json"),"original legacy claim filename/identity digest differs");
            if(data.binding().scope() instanceof ManagedScope managed)need(LegacyWindowsPathCanonicalizer.normalize(image.actualCanonicalStore()).equals(LegacyWindowsPathCanonicalizer.normalize(managed.stableKey()+"\\native-session\\rite-creation-actions")),"managed once store moved away from its actual persistent scope; a new directory cannot escape UNKNOWN");
            Optional<OriginalFile> packet=image.files().stream().filter(v->v.evidence().leaf().equals(data.resultLeaf())).findFirst();Optional<Result> result=Optional.empty();Optional<String> failure=Optional.empty();if(packet.isPresent())try{result=Optional.of(decodeResult(new RawJson(packet.orElseThrow().bytes()),data.binding(),new NativeFields(RiteCreation.CONFIRM_ONCE,data.source(),Optional.of(data.request()),Optional.of(data.id().value()))));}catch(IllegalArgumentException|ArithmeticException invalid){failure=Optional.of("original packet retained as UNKNOWN: "+invalid.getClass().getSimpleName());}
            if(releaseReason.isPresent()){if(!releaseReason.orElseThrow().equals("existing_primitive_rejected_before_endpoint_send")&&result.filter(Result::knownNoDispatch).isEmpty())failure=Optional.of("original safe-release lacks matching valid native no-dispatch proof");if(result.filter(v->!v.knownNoDispatch()).isPresent())failure=Optional.of("original safe-release conflicts with possible native dispatch/queue");}
            Status status=failure.isPresent()?Status.ORIGINAL_UNKNOWN_NO_RETRY:releaseReason.isPresent()||result.filter(Result::knownNoDispatch).isPresent()?Status.ORIGINAL_KNOWN_NO_DISPATCH_RELEASED:result.isPresent()?Status.ORIGINAL_NATIVE_RESULT_NO_RETRY:Status.ORIGINAL_UNKNOWN_NO_RETRY;
            Intent next=new Intent(data.id(),data.binding(),data.source(),data.request(),data.key(),data.original(),List.of(file.evidence()),packet.map(OriginalFile::evidence),failure,status);Optional<Intent> previous=all.stream().filter(v->v.id().equals(next.id())).findFirst();
            if(previous.isPresent()){Intent old=previous.orElseThrow();need(old.originalClaim().equals(next.originalClaim())&&old.originalNativeResult().equals(next.originalNativeResult())&&old.claimAndReleaseEvidence().size()==1&&old.claimAndReleaseEvidence().getFirst().leaf().endsWith(".claim.json")!=claim,"ambiguous original active/released claim or evidence differs");var evidence=new ArrayList<>(old.claimAndReleaseEvidence());evidence.add(file.evidence());all.remove(old);all.add(new Intent(next.id(),next.binding(),next.source(),next.request(),next.originalClaimKey(),next.originalClaim(),evidence,next.originalNativeResult(),old.originalResultFailure().isPresent()?old.originalResultFailure():next.originalResultFailure(),old.originalResultFailure().isPresent()||next.originalResultFailure().isPresent()?Status.ORIGINAL_UNKNOWN_NO_RETRY:Status.ORIGINAL_KNOWN_NO_DISPATCH_RELEASED));}else all.add(next);
        }
        for(OriginalFile file:image.files()){String leaf=file.evidence().leaf();if(leaf.matches("[0-9a-f]{64}.*")&&leaf.endsWith(".native-result.json"))need(referencedResults.contains(leaf),"orphan original final packet has no complete once claim; retain opaque UNKNOWN instead of assuming an empty store");}
        all.sort(Comparator.comparing(v->v.id().value()));return new Imported(manifest,all);
    }
    private static ClaimData claim(RawJson original,String machine){
        ObjectNode n=object(original);shape(n,Set.of("schema","machine_id","observed_at_utc","request_id","identity","binding","fields","status","native_result_file"),Set.of());equal(get(n,"schema"),CLAIM_SCHEMA);equal(get(n,"machine_id"),machine);Instant.parse(text(get(n,"observed_at_utc")));equal(get(n,"status"),"claimed_result_unknown_no_retry");ActionId id=new ActionId(text(get(n,"request_id")));
        ObjectNode fields=object(get(n,"fields"));shape(fields,Set.of("operation","expected_source_rite_id","expected_preview_identity","expected_outcome_kind","action_id"),Set.of());equal(get(fields,"operation"),"confirm_once");equal(get(fields,"action_id"),id.value());SourceRite source=source(get(fields,"expected_source_rite_id"));Confirm request=new Confirm(RiteCreationCodec.identity(get(fields,"expected_preview_identity")),Outcome.parse(text(get(fields,"expected_outcome_kind"))));
        Binding binding=binding(get(n,"binding"));ObjectNode identity=object(get(n,"identity"));ObjectNode expected=identity(binding.scope(),binding.nativeActor(),source);need(identity.equals(expected),"legacy claim scope/actor/source differs from actual original binding");String key=ActionCodec.sha256(pythonIdentity(binding.scope(),binding.nativeActor(),source).getBytes(StandardCharsets.UTF_8));String result=text(get(n,"native_result_file"));need(result.equals(key+"."+id.value()+".native-result.json"),"legacy native result filename changed or escaped its original store");return new ClaimData(id,binding,source,request,key,raw(n),result);
    }
    private static Binding binding(JsonNode original){
        ObjectNode n=object(original);boolean managed=n.has("intent_scope")||n.has("managed_campaign_run_binding");shape(n,Set.of("native_revision","connection_generation","game_pid","played_character_id","date_raw","episode_run_id"),managed?Set.of("intent_scope","managed_campaign_run_binding"):Set.of());
        BigInteger actor=positive(get(n,"played_character_id")),date=whole(get(n,"date_raw"));Scope scope;Optional<ManagedCampaignRunBinding> managedOriginal=Optional.empty();
        // Shared exact string canonicalization validates data; the actual import still separately requires custody/allocator proof.
        if(managed){need(get(n,"episode_run_id").isNull(),"managed legacy claim cannot acquire an episode");ObjectNode intent=object(get(n,"intent_scope"));shape(intent,Set.of("kind","state_dir"),Set.of());equal(get(intent,"kind"),"managed_campaign_state_v1");String state=text(get(intent,"state_dir"));ManagedCampaignRunBinding run=ManagedCampaignRunBinding.parse(get(n,"managed_campaign_run_binding"));need(state.equals(LegacyWindowsPathCanonicalizer.normalize(run.stateDir())),"legacy managed scope differs from exact original persistent state directory");scope=new ManagedScope(state);managedOriginal=Optional.of(run);}
        else scope=new EpisodeScope(text(get(n,"episode_run_id")));
        return new Binding(uint64(get(n,"native_revision")),uint64(get(n,"connection_generation")),positive(get(n,"game_pid")),actor,date,scope,managedOriginal);
    }
    public static Result decodeResult(RawJson originalPacket,ExpectedNativeBinding originalBinding,NativeFields originalFields){
        ObjectNode packet=object(originalPacket);shape(packet,Set.of("type","protocol_version","request_id","ok","result"),Set.of("error"));equal(get(packet,"type"),"command_result");equal(get(packet,"protocol_version"),BigInteger.ONE);equal(get(packet,"request_id"),originalFields.originalProtocolRequestId().orElseThrow());yes(get(packet,"ok"));if(packet.has("error"))need(packet.get("error").isNull(),"successful original legacy packet cannot retain an error");return RiteCreationCodec.result(raw(get(packet,"result")),originalBinding,originalFields);
    }
    private static BigInteger whole(JsonNode n){need(n!=null&&n.isIntegralNumber(),"original legacy integer token required; bool/float/string cannot change identity");return n.bigIntegerValue();}
    private static BigInteger positive(JsonNode n){BigInteger value=whole(n);need(value.signum()>0,"positive original legacy integer identity required");return value;}
    private static boolean sameKey(Intent a,Intent b){return a.binding().scope().equals(b.binding().scope())&&a.binding().nativeActor().equals(b.binding().nativeActor())&&a.source().equals(b.source());}
    /** Absence in a later filesystem snapshot never clears an earlier UNKNOWN or its original custody proof. */
    public static Imported merge(Optional<Imported> before,Imported current){
        if(before.isEmpty())return current;Imported old=before.orElseThrow();var all=new ArrayList<>(old.intents());
        for(Intent incoming:current.intents()){
            Optional<Intent> found=all.stream().filter(v->v.id().equals(incoming.id())).findFirst();if(found.isEmpty()){all.add(incoming);continue;}Intent previous=found.orElseThrow();
            need(previous.originalClaim().equals(incoming.originalClaim())&&previous.binding().equals(incoming.binding())&&previous.source().equals(incoming.source())&&previous.request().equals(incoming.request()),"legacy request identity was reused with changed original content");
            if(previous.originalNativeResult().isPresent()&&incoming.originalNativeResult().isPresent())need(previous.originalNativeResult().equals(incoming.originalNativeResult()),"original legacy result file identity changed; retain the original evidence");
            if(previous.status()==Status.ORIGINAL_KNOWN_NO_DISPATCH_RELEASED)need(incoming.status()==Status.ORIGINAL_KNOWN_NO_DISPATCH_RELEASED,"legacy known-no-dispatch history cannot become unknown again");
            if(incoming.originalNativeResult().isEmpty()&&previous.originalNativeResult().isPresent())continue;
            var evidence=new ArrayList<>(previous.claimAndReleaseEvidence());for(Evidence item:incoming.claimAndReleaseEvidence())if(!evidence.contains(item))evidence.add(item);need(evidence.size()<=2,"legacy active/released original identity drift");
            all.remove(previous);all.add(new Intent(incoming.id(),incoming.binding(),incoming.source(),incoming.request(),incoming.originalClaimKey(),incoming.originalClaim(),evidence,incoming.originalNativeResult(),incoming.originalResultFailure(),incoming.status()));
        }
        all.sort(Comparator.comparing(v->v.id().value()));var manifests=new ArrayList<>(old.custodyManifests());for(ExactRef item:current.custodyManifests())if(!manifests.contains(item))manifests.add(item);return new Imported(current.originalManifest(),manifests,all);
    }
    public static ObjectNode toJson(Imported imported){
        ObjectNode n=empty();n.set("current_original_manifest",imported.originalManifest().toJson());var manifests=n.putArray("complete_custody_manifests");imported.custodyManifests().forEach(v->manifests.add(v.toJson()));var all=n.putArray("intents");
        for(Intent intent:imported.intents()){
            ObjectNode item=empty().put("request_id",intent.id().value()).put("status",intent.status().name()).put("original_claim_key",intent.originalClaimKey());item.set("original_claim",object(intent.originalClaim()));if(intent.originalResultFailure().isPresent())item.put("original_result_failure",intent.originalResultFailure().orElseThrow());else item.putNull("original_result_failure");var refs=item.putArray("claim_and_release_evidence");intent.claimAndReleaseEvidence().forEach(v->refs.add(evidence(v)));if(intent.originalNativeResult().isPresent())item.set("original_native_result",evidence(intent.originalNativeResult().orElseThrow()));else item.putNull("original_native_result");all.add(item);
        }return n;
    }
    public static Imported fromJson(JsonNode original){
        ObjectNode n=object(original);shape(n,Set.of("current_original_manifest","complete_custody_manifests","intents"),Set.of());JsonNode manifests=get(n,"complete_custody_manifests"),rows=get(n,"intents");need(manifests.isArray()&&manifests.size()<=512&&rows.isArray()&&rows.size()<=256,"bounded complete original once history required");var refs=new ArrayList<ExactRef>();manifests.forEach(v->refs.add(ExactRef.fromJson(v)));var all=new ArrayList<Intent>();
        for(JsonNode row:rows){ObjectNode item=object(row);shape(item,Set.of("request_id","status","original_claim_key","original_claim","claim_and_release_evidence","original_native_result","original_result_failure"),Set.of());RawJson claimRaw=raw(get(item,"original_claim"));ClaimData data=claim(claimRaw,text(get(object(claimRaw),"machine_id")));need(text(get(item,"request_id")).equals(data.id().value())&&text(get(item,"original_claim_key")).equals(data.key()),"stored legacy identity/content/key changed");JsonNode e=get(item,"claim_and_release_evidence");need(e.isArray()&&e.size()>0&&e.size()<=2,"original active/release evidence required");var evidence=new ArrayList<Evidence>();e.forEach(v->evidence.add(evidence(v)));Optional<Evidence> packet=nullable(item,"original_native_result",RiteCreationLegacyStore::evidence);Status status=Status.valueOf(text(get(item,"status")));need(status!=Status.ORIGINAL_NATIVE_RESULT_NO_RETRY||packet.isPresent(),"stored known legacy result has no original packet");all.add(new Intent(data.id(),data.binding(),data.source(),data.request(),data.key(),data.original(),evidence,packet,nullable(item,"original_result_failure",RiteCreationCodec::text),status));}
        return new Imported(ExactRef.fromJson(get(n,"current_original_manifest")),refs,all);
    }
    public static ObjectNode evidence(Evidence value){ObjectNode n=empty().put("leaf",value.leaf());n.set("original",value.original().toJson());n.set("preserved",value.preserved().toJson());FileIdentity id=value.nativeIdentity();n.putObject("native_identity").put("volume_serial_decimal",id.volumeSerialDecimal()).put("file_id_decimal",id.fileIdDecimal()).put("creation_filetime_decimal",id.creationFiletimeDecimal()).put("modified_instant",id.modifiedInstant()).put("bytes",id.bytes());return n;}
    public static Evidence evidence(JsonNode original){ObjectNode n=object(original);shape(n,Set.of("leaf","original","preserved","native_identity"),Set.of());ObjectNode id=object(get(n,"native_identity"));shape(id,Set.of("volume_serial_decimal","file_id_decimal","creation_filetime_decimal","modified_instant","bytes"),Set.of());return new Evidence(text(get(n,"leaf")),ExactRef.fromJson(get(n,"original")),new FileIdentity(text(get(id,"volume_serial_decimal")),text(get(id,"file_id_decimal")),text(get(id,"creation_filetime_decimal")),text(get(id,"modified_instant")),integer(get(id,"bytes"),0,9007199254740991L).longValueExact()),ExactRef.fromJson(get(n,"preserved")));}
    private static ObjectNode identity(Scope scope,BigInteger actor,SourceRite source){ObjectNode n=empty().put("played_character_id",actor).put("source_rite_id",source.value());if(scope instanceof EpisodeScope episode)n.put("episode_run_id",episode.episode());else n.putObject("managed_campaign_intent_scope").put("kind",scope.kind()).put("state_dir",scope.stableKey());return n;}
    /** Exact original json.dumps(sort_keys=True), including ASCII escapes and the original default spaces. */
    public static String pythonIdentity(Scope scope,BigInteger actor,SourceRite source){
        if(scope instanceof EpisodeScope episode)return "{\"episode_run_id\": "+ascii(episode.episode())+", \"played_character_id\": "+actor+", \"source_rite_id\": "+source.value()+"}";
        return "{\"managed_campaign_intent_scope\": {\"kind\": \"managed_campaign_state_v1\", \"state_dir\": "+ascii(scope.stableKey())+"}, \"played_character_id\": "+actor+", \"source_rite_id\": "+source.value()+"}";
    }
    private static String ascii(String text){StringBuilder out=new StringBuilder("\"");for(int i=0;i<text.length();i++){char c=text.charAt(i);switch(c){case '"'->out.append("\\\"");case '\\'->out.append("\\\\");case '\b'->out.append("\\b");case '\f'->out.append("\\f");case '\n'->out.append("\\n");case '\r'->out.append("\\r");case '\t'->out.append("\\t");default->{if(c<32||c>=127)out.append(String.format(java.util.Locale.ROOT,"\\u%04x",(int)c));else out.append(c);}}}return out.append('"').toString();}
}
