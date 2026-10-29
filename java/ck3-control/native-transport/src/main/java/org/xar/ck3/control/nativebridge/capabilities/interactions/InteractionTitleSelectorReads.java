package org.xar.ck3.control.nativebridge.capabilities.interactions;

import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Source-owned arbitrary selectors over the original four strict native decoders; no fixed plan or native client. */
public final class InteractionTitleSelectorReads {
    public enum Kind {
        LAWS("game.command.query-title-own-laws-v1-ID"),CLAIMS("game.command.query-player-claims-v1-IDS"),HOLDER("game.command.query-title-holder-v1-N"),APPOINTMENT("game.command.query-current-title-appointment-v1");
        private final String capability;Kind(String capability){this.capability=capability;}public String capability(){return capability;}
    }
    public sealed interface Selector permits LawSelector,ClaimsSelector,HolderSelector,AppointmentSelector {Kind kind();}
    public record LawSelector(FullId title) implements Selector {public LawSelector{Objects.requireNonNull(title);}public Kind kind(){return Kind.LAWS;}}
    public record ClaimsSelector(List<Int32Id> titles) implements Selector {
        public ClaimsSelector {titles=List.copyOf(titles);require(!titles.isEmpty()&&titles.size()<=4096&&titles.stream().distinct().count()==titles.size(),"1..4096 ordered distinct claims titles required");require(claimsStep(titles).getBytes(java.nio.charset.StandardCharsets.UTF_8).length<=795,"actual native claims step exceeds its original wire bound; no truncation");}
        public Kind kind(){return Kind.CLAIMS;}
    }
    public record HolderSelector(Int32Id title) implements Selector {public HolderSelector{Objects.requireNonNull(title);}public Kind kind(){return Kind.HOLDER;}}
    public record AppointmentSelector(AppointmentRequest request) implements Selector {public AppointmentSelector{Objects.requireNonNull(request);}public Kind kind(){return Kind.APPOINTMENT;}}
    public sealed interface Decoded permits LawsValue,ClaimsValue,HolderValue,AppointmentValue {RawJson original();}
    public record LawsValue(TitleOwnLaws value,RawJson original) implements Decoded {public LawsValue{Objects.requireNonNull(value);Objects.requireNonNull(original);}}
    public record ClaimsValue(PlayerClaims value,RawJson original) implements Decoded {public ClaimsValue{Objects.requireNonNull(value);Objects.requireNonNull(original);}}
    public record HolderValue(TitleHolder value,RawJson original) implements Decoded {public HolderValue{Objects.requireNonNull(value);Objects.requireNonNull(original);}}
    public record AppointmentValue(Appointment value,RawJson original) implements Decoded {public AppointmentValue{Objects.requireNonNull(value);Objects.requireNonNull(original);}}
    private final java.util.EnumMap<Kind,RootReadContractCatalog.Family<Selector,Decoded>> families=new java.util.EnumMap<>(Kind.class);
    private RootReadContractCatalog installed;
    public InteractionTitleSelectorReads(ExactRef implementation,ExactRef sharedDecoder) {
        Objects.requireNonNull(implementation);Objects.requireNonNull(sharedDecoder);
        for(var kind:Kind.values())families.put(kind,new RootReadContractCatalog.Family<>("public-title-selector-"+kind.name().toLowerCase(java.util.Locale.ROOT)+"/v1",Selector.class,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,Optional.of(kind.capability()),implementation,sharedDecoder,selector->{require(selector.kind()==kind,"foreign selector family");return encodeSelector(selector);},InteractionTitleSelectorReads::operation,selector->contract(implementation,selector)));
    }
    public List<RootReadContractCatalog.Family<?,?>> families(){return List.copyOf(families.values());}
    public synchronized void attach(RootReadContractCatalog same){Objects.requireNonNull(same);require(installed==null||installed==same,"title selector catalog cannot rebind");require(families.values().stream().allMatch(family->same.families().stream().anyMatch(value->value==family)),"identical preinstalled title families required");installed=same;}
    public synchronized ReadContract<Decoded> issue(Selector selector){require(installed!=null,"actual title selector catalog not attached");return installed.issue(families.get(selector.kind()),selector);}
    public static OperationKey operation(Selector selector) {
        return new OperationKey(switch(selector){case LawSelector law->"query-title-own-laws-v1-"+law.title().value();case ClaimsSelector claims->new org.xar.ck3.control.application.action.NativeStepDiscriminator.ClaimsIdentity(claims.titles().stream().map(Int32Id::value).toList()).operationKey().value();case HolderSelector holder->"query-title-holder-v1-"+holder.title().value();case AppointmentSelector ignored->org.xar.ck3.control.application.action.NativeStepDiscriminator.IngameWindow.TITLE_APPOINTMENT.operationKey().value();});
    }
    private static String claimsStep(List<Int32Id> titles){return new org.xar.ck3.control.application.action.NativeStepDiscriminator.ClaimsIdentity(titles.stream().map(Int32Id::value).toList()).nativeStep();}
    public static RawJson encodeSelector(Selector selector) {
        var row=StrictJson.object();row.put("kind",selector.kind().name());
        switch(selector){case LawSelector law->row.put("title_id",law.title().value());case ClaimsSelector claims->{var ids=row.putArray("title_ids");claims.titles().forEach(title->ids.add(title.value()));}case HolderSelector holder->row.put("title_id",holder.title().value());case AppointmentSelector appointment->{var request=StrictJson.object();InteractionArguments.appointment(request,appointment.request());row.set("request",request);}}
        return new RawJson(StrictJson.canonical(row,65536));
    }
    public static Selector decodeSelector(RawJson original) {
        var row=StrictJson.parse(original.bytes(),65536);var kind=Kind.valueOf(StrictJson.text(row.get("kind")));
        return switch(kind) {
            case LAWS->{StrictJson.object(row,Set.of("kind","title_id"));yield new LawSelector(new FullId(StrictJson.integer(row.get("title_id"),0,0xffff_fffeL)));}
            case HOLDER->{StrictJson.object(row,Set.of("kind","title_id"));yield new HolderSelector(new Int32Id((int)StrictJson.integer(row.get("title_id"),0,Integer.MAX_VALUE)));}
            case CLAIMS->{StrictJson.object(row,Set.of("kind","title_ids"));var ids=row.get("title_ids");require(ids.isArray()&&ids.size()<=4096,"bounded original ordered claims list required");var titles=new java.util.ArrayList<Int32Id>();ids.forEach(value->titles.add(new Int32Id((int)StrictJson.integer(value,0,Integer.MAX_VALUE))));yield new ClaimsSelector(titles);}
            case APPOINTMENT->{StrictJson.object(row,Set.of("kind","request"));StrictJson.object(row.get("request"),Set.of("requested_title_id","candidate_offset","candidate_limit","breakdown_character_id","diagnostic_character_id"));yield new AppointmentSelector(InteractionArguments.appointment(row.get("request")));}
        };
    }
    public static OpportunityJson.Obj arguments(Context actual,Selector selector) {
        var row=InteractionArguments.body(actual);row.put("schema","xar.title-selector-read-arguments/v1");row.set("selector",StrictJson.parse(encodeSelector(selector).bytes(),65536));return InteractionArguments.app(row);
    }
    public static ReadContract<Decoded> contract(ExactRef source,Selector selector) {
        Objects.requireNonNull(source);Objects.requireNonNull(selector);var operation=operation(selector);var capability=selector.kind().capability();
        java.util.function.Function<PlanningReadRequest,Context> checked=request->{var row=InteractionArguments.parseApp(request.arguments());StrictJson.object(row,Set.of("schema","group_context","selector"));require(StrictJson.text(row.get("schema")).equals("xar.title-selector-read-arguments/v1"),"exact title selector argument schema required");require(selector.equals(decodeSelector(new RawJson(StrictJson.canonical(row.get("selector"),65536))))&&request.operation().equals(operation),"issued title selector differs from actual request");return InteractionArguments.context(request);};
        java.util.function.Function<PlanningReadReceipt,Decoded> decoder=receipt->{var context=checked.apply(receipt.request());var original=receipt.original().originalResultToken().orElseThrow();return switch(selector){case LawSelector law->new LawsValue(InteractionReads.titleOwnLaws(receipt,context,law.title()),original);case ClaimsSelector claims->new ClaimsValue(InteractionReads.playerClaims(receipt,context,claims.titles()),original);case HolderSelector holder->{if(context.build()==Build.CROZIER4){var row=InteractionJson.result(receipt).get("title_holder");for(String field:List.of("title_key_available","title_key_status","title_key","title_key_unavailable_reason"))require(row.has(field),"original current4 title-holder requires the complete native title-key observation");}yield new HolderValue(InteractionReads.titleHolder(receipt,context,holder.title()),original);}case AppointmentSelector appointment->new AppointmentValue(InteractionReads.appointment(receipt,context,appointment.request()),original);};};
        return new ReadContract<>("title-selector:"+selector.kind().name().toLowerCase(java.util.Locale.ROOT)+":"+ActionCodec.sha256(encodeSelector(selector).bytes()),operation,Optional.of(capability),capability,ReadContract.PermissionMode.ADVERTISED_CAPABILITY,ReadContract.WireProfile.EXECUTE_STEP,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,source,(request,id)->{checked.apply(request);return new NativeRequest(org.xar.ck3.control.application.action.NativeStepDiscriminator.identity(operation).nativeStep(),capability,selector instanceof AppointmentSelector appointment?InteractionArguments.appointmentNative(appointment.request()):new RawJson(new byte[]{123,125}));},decoder,decoder);
    }
}
