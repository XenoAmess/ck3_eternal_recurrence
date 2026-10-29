package org.xar.ck3.control.nativebridge.capabilities.interactions;

import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionTitleSelectorReads.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.CrossJsDecimalUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** One original public request/result contract for four native title selectors. Native packet bytes remain unchanged. */
public final class TitleClaimsPublicCodec {
    private TitleClaimsPublicCodec() { }
    public record Request(BigInteger expectedRevision,Selector selector) {
        public Request {java.util.Objects.requireNonNull(expectedRevision);java.util.Objects.requireNonNull(selector);require(expectedRevision.signum()>=0&&expectedRevision.compareTo(StrictJson.UINT64_MAX)<=0,"public revision uint64 required");}
    }
    public static Request decode(Kind kind,RawJson arguments) {
        var row=StrictJson.parse(arguments.bytes(),65536);var fields=new java.util.HashSet<String>(Set.of("expected_revision"));
        if(kind==Kind.APPOINTMENT){for(String key:List.of("requested_title_id","candidate_offset","candidate_limit","breakdown_character_id","diagnostic_character_id"))if(row.has(key))fields.add(key);}
        else fields.add(kind==Kind.CLAIMS?"title_ids":"title_id");StrictJson.object(row,fields);
        Selector selector=switch(kind) {
            case LAWS->new LawSelector(new FullId(StrictJson.integer(row.get("title_id"),0,0xffff_fffeL)));
            case HOLDER->new HolderSelector(new Int32Id((int)StrictJson.integer(row.get("title_id"),0,Integer.MAX_VALUE)));
            case CLAIMS->{var values=row.get("title_ids");require(values!=null&&values.isArray()&&values.size()<=4096,"bounded ordered title_ids array required");var ids=new java.util.ArrayList<Int32Id>();values.forEach(value->ids.add(new Int32Id((int)StrictJson.integer(value,0,Integer.MAX_VALUE))));yield new ClaimsSelector(ids);}
            case APPOINTMENT->new AppointmentSelector(new AppointmentRequest(optionalId(row.get("requested_title_id")),row.has("candidate_offset")?(int)StrictJson.integer(row.get("candidate_offset"),0,4096):0,row.has("candidate_limit")?(int)StrictJson.integer(row.get("candidate_limit"),1,64):32,optionalId(row.get("breakdown_character_id")),optionalId(row.get("diagnostic_character_id"))));
        };
        return new Request(unsigned(row.get("expected_revision")),selector);
    }
    public static RawJson encode(Request request) {
        var row=StrictJson.object();row.put("expected_revision",request.expectedRevision().toString());
        switch(request.selector()) {
            case LawSelector law->row.put("title_id",law.title().value());case HolderSelector holder->row.put("title_id",holder.title().value());
            case ClaimsSelector claims->{var ids=row.putArray("title_ids");claims.titles().forEach(title->ids.add(title.value()));}
            case AppointmentSelector appointment->{var value=appointment.request();nullable(row,"requested_title_id",value.title());nullable(row,"breakdown_character_id",value.breakdown());nullable(row,"diagnostic_character_id",value.diagnostic());row.put("candidate_offset",value.offset());row.put("candidate_limit",value.limit());}
        }return raw(row);
    }
    public static RawJson publication(PlanningReadResult.Known<Decoded> actual,Selector selector) {
        require(actual.receipt().request().operation().equals(InteractionTitleSelectorReads.operation(selector)),"title publication selector differs from the actual original operation");
        var recorded=InteractionArguments.parseApp(actual.receipt().request().arguments());require(selector.equals(InteractionTitleSelectorReads.decodeSelector(new RawJson(StrictJson.canonical(recorded.get("selector"),65536)))),"title publication changed the exact original selector parameters");
        require(actual.value().original().equals(actual.receipt().original().originalResultToken().orElseThrow()),"typed title decoder did not retain its actual original result token");
        var nativeOriginal=actual.value().original();require(nativeOriginal.bytes().length<=1_048_576,"finite original title query token required");
        var row=org.xar.ck3.control.application.driver.PublicDataJson.object(nativeOriginal);
        var origin=actual.receipt().request().before();
        var expectedNativeStep = org.xar.ck3.control.application.action.NativeStepDiscriminator.identity(actual.receipt().request().operation()).nativeStep();
        if(!(selector instanceof AppointmentSelector))require(StrictJson.text(row.get("step")).equals(expectedNativeStep),"original title operation differs");
        else if(row.has("step"))require(StrictJson.text(row.get("step")).equals(expectedNativeStep),"original appointment unexpectedly carries another step");
        bind(row,"queried_snapshot_id",origin.frame().snapshotId());bind(row,"queried_revision",origin.frame().revision());bind(row,"queried_native_revision",origin.frame().identity().nativeRevision());
        bind(row,"backend_id","native-headless");
        if(selector instanceof LawSelector law)row.put("title_id",law.title().value());else if(selector instanceof HolderSelector holder)row.put("title_id",holder.title().value());else if(selector instanceof ClaimsSelector claims){var ids=row.putArray("title_ids");claims.titles().forEach(title->ids.add(title.value()));}
        if(selector instanceof AppointmentSelector){var actualContext=InteractionArguments.context(actual.receipt().request());bind(row,"episode_run_id",actualContext.controls().episodeRunId());bind(row,"queried_connection_generation",actualContext.connectionGeneration());}
        else row.put("read_only",true);
        normalize(row);var result=org.xar.ck3.control.application.driver.PublicDataJson.encodePreservingDecimals(row,nativeOriginal);require(result.bytes().length<=1_048_576,"bounded title public projection required");return result;
    }
    private static void normalize(JsonNode value) {
        if(value.isObject()) {
            var row=(ObjectNode)value;var names=new java.util.ArrayList<String>();row.fieldNames().forEachRemaining(names::add);
            for(String name:names){var item=row.get(name);if(item.isNull())continue;
                if(Set.of("snapshot_revision","native_revision","query_sequence","pump_epoch","queried_revision","queried_native_revision","capture_epoch","container_generation","queried_connection_generation","address","vector_address").contains(name))row.put(name,StrictJson.integer(item,BigInteger.ZERO,StrictJson.UINT64_MAX).toString());
                else if(Set.of("score_raw","value_raw","factor_raw","accumulated_raw").contains(name))row.put(name,StrictJson.integer(item,BigInteger.ONE.shiftLeft(63).negate(),BigInteger.ONE.shiftLeft(63).subtract(BigInteger.ONE)).toString());
                else normalize(item);
            }
        }else if(value.isArray())for(var item:value)normalize(item);
        else if(value.isIntegralNumber())require(value.bigIntegerValue().abs().compareTo(BigInteger.valueOf(StrictJson.MAX_SAFE_INTEGER))<=0,"unclassified unsafe public title integer refused");
        else if(value.isFloatingPointNumber())require(!value.asText().isBlank(),"original typed decimal token required");
    }
    private static void bind(ObjectNode row,String name,String value){if(row.has(name))require(StrictJson.text(row.get(name)).equals(value),"original public binding differs: "+name);else row.put(name,value);}
    private static void bind(ObjectNode row,String name,BigInteger value){if(row.has(name))require(StrictJson.integer(row.get(name),BigInteger.ZERO,StrictJson.UINT64_MAX).equals(value),"original public binding differs: "+name);else row.put(name,value);}
    private static Optional<CharacterId> optionalId(JsonNode value){return value==null||value.isNull()?Optional.empty():Optional.of(new CharacterId(StrictJson.integer(value,1,0xffff_fffeL)));}
    private static void nullable(ObjectNode row,String name,Optional<CharacterId> value){if(value.isPresent())row.put(name,value.orElseThrow().value());else row.putNull(name);}
    private static BigInteger unsigned(JsonNode value){if(value!=null&&value.isTextual())return new BigInteger(new CrossJsDecimalUInt64(value.textValue()).decimal());return StrictJson.integer(value,BigInteger.ZERO,BigInteger.valueOf(StrictJson.MAX_SAFE_INTEGER));}
    private static RawJson raw(ObjectNode row){return new RawJson(StrictJson.canonical(row,1_048_576));}
}
