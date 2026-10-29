package org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Path;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.PublicUnsigned64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.religion.HolySiteDecoders;
import org.xar.ck3.control.nativebridge.capabilities.religion.ReligionHolyState;
import org.xar.ck3.control.nativebridge.capabilities.religion.ReligionModels.DecisionDetail;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.ReligionContract.*;

/** Two original selected HolySite READ families. The legacy generic decision READ keeps its distinct operation. */
public final class ReligionHolyReads implements ReligionService.Component {
    public static final String STATE="ck3_query_player_holy_site_v1",ADOPTION="ck3_query_player_holy_site_adoption_detail_v1";
    public record Sources(ExactRef stateDefinition,ExactRef adoptionDefinition,ExactRef decoder){public Sources{Objects.requireNonNull(stateDefinition);Objects.requireNonNull(adoptionDefinition);Objects.requireNonNull(decoder);}}
    private final PlanningReadPort reads;private final ActionPorts.OutcomeArchive archive;
    private final ReadContract<ReligionHolyState.State> state;private final ReadContract<DecisionDetail> adoption;
    public ReligionHolyReads(PlanningReadPort reads,ActionPorts.OutcomeArchive archive,Sources sources,ReligionService.ReadAdmission admission){
        this.reads=Objects.requireNonNull(reads);this.archive=Objects.requireNonNull(archive);Objects.requireNonNull(sources);Objects.requireNonNull(admission);
        state=contract("holy-site","query-player-holy-site-v1","allow_private_player_holy_site_query",sources.stateDefinition(),admission,false,ReligionHolyState::decode);
        adoption=contract("holy-site-adoption-detail","query-player-holy-site-adoption-detail-v1","allow_private_holy_site_adoption_detail_query",sources.adoptionDefinition(),admission,true,HolySiteDecoders::adoption);
    }
    private static <T> ReadContract<T> contract(String id,String step,String permission,ExactRef definition,ReligionService.ReadAdmission admission,boolean required,java.util.function.Function<PlanningReadReceipt,T> decoder){
        return new ReadContract<>("religion/"+id,new OperationKey(step),Optional.empty(),permission,ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,ReadContract.WireProfile.G2_PRIVATE_QUERY,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,definition,
            (request,requestId)->{admission.verify(request);ObjectNode n=(ObjectNode)OpportunityJson.toNode(request.arguments());StrictJson.require(n.size()==(n.has("holy_site_id")?1:0)&&(!required||n.has("holy_site_id")),"original HolySite query fields differ");if(n.has("holy_site_id"))id(n.get("holy_site_id"));return new NativeRequest(step,Optional.empty(),ReligionCodec.raw(n));},decoder,decoder);
    }
    public ReadContract<ReligionHolyState.State> stateContract(){return state;}
    public ReadContract<DecisionDetail> adoptionContract(){return adoption;}
    @Override public List<String> methods(){return List.of(STATE,ADOPTION);}
    @Override public Response invoke(Session same,ReligionService.ActualFrame actual,Request request){
        StrictJson.require(request.expectedRevision().equals(actual.frame().identity().frame().revision()),"HolySite expected public revision is stale");
        ObjectNode fields=StrictJson.object();if(request.value(Field.HOLY_SITE_ID) instanceof IntegerValue selected)fields.put("holy_site_id",id(com.fasterxml.jackson.databind.node.JsonNodeFactory.instance.numberNode(selected.value())));
        ObjectNode business;
        if(request.method().name().equals(STATE)){var known=ReligionService.readKnown(reads,archive,same,state,actual,fields);business=ReligionCodec.object(known.value().originalNormalized());metadata(business,actual,known.receipt());}
        else{StrictJson.require(request.method().name().equals(ADOPTION),"method is outside the installed selected HolySite family");var known=ReligionService.readKnown(reads,archive,same,adoption,actual,fields);business=((ObjectNode)ReligionService.originalResult(known.receipt()).get("player_holy_site_adoption_detail")).deepCopy();metadata(business,actual,known.receipt());}
        return new Response(request.method(),ReligionCodec.raw(publicProjection(business)));
    }
    public static ObjectNode publicProjection(ObjectNode source){
        ObjectNode n=source.deepCopy();for(String field:List.of("capture_epoch","snapshot_revision","queried_revision","queried_native_revision"))if(n.has(field)&&!n.get(field).isNull())u64(n,field);
        if(n.has("native_resource_quote")&&!n.get("native_resource_quote").isNull()){
            ObjectNode quote=(ObjectNode)n.get("native_resource_quote");JsonNode vector=quote.get("resource_vector_raw");StrictJson.require(vector.isArray()&&vector.size()==10,"original ten-resource native quote required");var encoded=quote.putArray("resource_vector_raw");for(JsonNode value:vector)encoded.add(i64(value));ObjectNode costs=(ObjectNode)quote.get("costs_raw");for(String field:List.of("gold","prestige","piety","treasury"))costs.put(field,i64(costs.get(field)));
        }if(n.has("cached_resource_vector_raw")&&!n.get("cached_resource_vector_raw").isNull()){JsonNode original=n.get("cached_resource_vector_raw");StrictJson.require(original.isArray()&&original.size()==10,"complete cached ten-resource vector required");var encoded=n.putArray("cached_resource_vector_raw");for(JsonNode value:original)encoded.add(i64(value));}return n;
    }
    private static void metadata(ObjectNode n,ReligionService.ActualFrame actual,PlanningReadReceipt receipt){
        ObjectNode original=ReligionService.originalResult(receipt);n.put("exact_ck3_build","1.20.0.4").put("exe_sha256",actual.hello().gameSha256().toUpperCase(java.util.Locale.ROOT)).put("queried_snapshot_id",actual.frame().identity().frame().snapshotId()).put("queried_revision",actual.frame().identity().frame().revision()).put("queried_native_revision",actual.frame().identity().frame().identity().nativeRevision()).put("advertised",false);
        for(String field:List.of("snapshot_revision","backend_id","domain_key","status"))n.set(field,Objects.requireNonNull(original.get(field)).deepCopy());
    }
    private static BigInteger id(JsonNode value){StrictJson.require(value!=null&&value.isIntegralNumber()&&value.bigIntegerValue().signum()>=0&&value.bigIntegerValue().compareTo(new BigInteger("4294967295"))<0,"full uint32 HolySite reference required; bool/float/null are distinct");return value.bigIntegerValue();}
    private static void u64(ObjectNode n,String field){JsonNode value=n.get(field);StrictJson.require(value.isIntegralNumber(),"original native uint64 token required");n.put(field,PublicUnsigned64.canonical(value.bigIntegerValue(),PublicUnsigned64.Minimum.ZERO));}
    private static String i64(JsonNode value){StrictJson.require(value!=null&&value.isIntegralNumber()&&value.bigIntegerValue().compareTo(BigInteger.valueOf(Long.MIN_VALUE))>=0&&value.bigIntegerValue().compareTo(BigInteger.valueOf(Long.MAX_VALUE))<=0,"original signed64 quote token required");return value.bigIntegerValue().toString();}
    private static void witness(ExactRef source){try{var pin=SharedSourceFiles.observe(Path.of(source.path()));StrictJson.require(pin.source().bytes()==source.bytes()&&pin.source().sha256().equals(source.sha256()),"original HolySite producer source differs");SharedSourceFiles.assertUnchanged(pin);}catch(IOException missing){throw new java.io.UncheckedIOException(missing);}}
}
