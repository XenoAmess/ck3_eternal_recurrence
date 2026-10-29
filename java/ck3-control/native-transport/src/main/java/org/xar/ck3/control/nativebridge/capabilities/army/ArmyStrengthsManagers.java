package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.function.BiFunction;
import java.util.function.Function;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.wave2.military.combatroles.CombatRoles;
import org.xar.ck3.control.wave2.military.combatroles.CombatRolesCodec;
import org.xar.ck3.control.wave2.military.combatroles.CombatRolesPolicy;
import org.xar.ck3.control.wave2.military.disembark.DisembarkCodec;
import org.xar.ck3.control.wave2.military.disembark.DisembarkPenalty;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyManagersModel.Kind;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyManagersModel.Inputs;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsFamilies.Key;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsPipeline.*;

/** Complete ten-family/twelve-stage manager bundle. Root freezes and qualifies the full registry after installation. */
public final class ArmyStrengthsManagers {
    private ArmyStrengthsManagers(){ }
    public record Provenance(String snapshotId,BigInteger revision,BigInteger nativeRevision,BigInteger dateRaw,String gameVersion,String executableSha256){
        public Provenance{if(revision!=null)uint64(revision);if(nativeRevision!=null)uint64(nativeRevision);if(dateRaw!=null)ArmyTypes.require(dateRaw.bitLength()<=63,"manager provenance signed64 date");}
        public ObjectNode encode(boolean publicV2){ObjectNode out=JsonNodeFactory.instance.objectNode();text(out,"snapshot_id",snapshotId);ArmyManagersPendingPlacement.integer(out,"revision",revision,publicV2);ArmyManagersPendingPlacement.integer(out,"native_revision",nativeRevision,publicV2);ArmyManagersPendingPlacement.integer(out,"date_raw",dateRaw,publicV2);text(out,"game_version",gameVersion);text(out,"executable_sha256",executableSha256);return out;}
        CombatRoles.Provenance combatRoles(){return new CombatRoles.Provenance(snapshotId,revision,nativeRevision,dateRaw,gameVersion,executableSha256);}
    }
    public record PendingBatch(List<PerArmy<ArmyManagersPending.Projection>> values){public PendingBatch{values=List.copyOf(values);}}
    public record CharacterBatch(List<PerArmy<ArmyManagersPrefixes.CharacterProjection>> values){public CharacterBatch{values=List.copyOf(values);}}
    public record DatedBatch(List<PerArmy<ArmyManagersPrefixes.DatedProjection>> values){public DatedBatch{values=List.copyOf(values);}}
    public record CurrentBatch(Provenance provenance,List<PerArmy<ArmyManagersCurrent.Projection>> values){public CurrentBatch{Objects.requireNonNull(provenance);values=List.copyOf(values);}}
    public record RefreshBatch(Provenance provenance,List<PerArmy<ArmyManagersRefresh.Projection>> values){public RefreshBatch{Objects.requireNonNull(provenance);values=List.copyOf(values);}}
    public record DisembarkBatch(Provenance provenance,List<PerArmy<DisembarkPenalty.Projection>> values){public DisembarkBatch{Objects.requireNonNull(provenance);values=List.copyOf(values);}}
    public record CombatRolesBatch(Provenance provenance,List<PerArmy<CombatRoles.Projection>> values){public CombatRolesBatch{Objects.requireNonNull(provenance);values=List.copyOf(values);}}
    public static void install(ArmyStrengthsFamilies.Registry registry,ArmyStrengthsPipeline pipeline,ExactRef actualJavaBundleSource){
        Objects.requireNonNull(registry);Objects.requireNonNull(pipeline);Objects.requireNonNull(actualJavaBundleSource);
        register(registry,Key.CURRENT_PRE_DATE_PENDING_UPDATE_INPUTS_V1,Kind.PENDING,actualJavaBundleSource);
        register(registry,Key.CURRENT_PRE_DATE_DATED_APPEND_INPUTS_V1,Kind.DATED,actualJavaBundleSource);
        register(registry,Key.CURRENT_POST_ADMISSION_REFRESH_INPUTS_V1,Kind.REFRESH,actualJavaBundleSource);
        register(registry,Key.CURRENT_PRE_DATE_CHARACTER_PREFIX_INPUTS_V1,Kind.CHARACTER,actualJavaBundleSource);
        register(registry,Key.CURRENT_ARMY_CONDITION30_INPUTS_V1,Kind.CONDITION30,actualJavaBundleSource);
        register(registry,Key.CURRENT_ARMY_FLAG20_INPUTS_V1,Kind.FLAG20,actualJavaBundleSource);
        register(registry,Key.CURRENT_ARMY_FLAG21_INPUTS_V1,Kind.FLAG21,actualJavaBundleSource);
        register(registry,Key.CURRENT_SELECTED_TITLE_HOLDER_OWNER_RELATION_V1,Kind.HOLDER_RELATION,actualJavaBundleSource);
        register(registry,Key.CURRENT_ARMY_FLAG31_INPUTS_V1,Kind.FLAG31,actualJavaBundleSource);
        registry.register(Key.CURRENT_DISEMBARK_PENALTY_V1,DisembarkPenalty.Observation.class,(actual,context)->{
            if(actual instanceof ArmyTypes.Missing<RawJson>)return new ArmyTypes.Missing<>();
            ArmyTypes.require(actual instanceof ArmyTypes.Present<RawJson>&&context.core().status()==ArmyStrengths.Status.AVAILABLE,"current disembark optional member requires available Army and nonnull observation");
            RawJson bytes=((ArmyTypes.Present<RawJson>)actual).value();return new ArmyTypes.Present<>(DisembarkCodec.normalize(bytes.bytes()));
        },ArmyStrengthsManagers::encodeDisembarkObservation,ArmyStrengthsManagers::encodeDisembarkObservation,actualJavaBundleSource);
        pipeline.register(Stage.SAME_INPUT_CONDITIONAL_CURRENT_PRE_DATE_PENDING_UPDATE_V1,PendingBatch.class,List.of(),(input,earlier)->new PendingBatch(input.selected().stream().map(row->new PerArmy<>(row.core().army(),ArmyManagersPending.project(family(row,Key.CURRENT_PRE_DATE_PENDING_UPDATE_INPUTS_V1,Inputs.class)))).toList()),value->encodePending(value,false),value->encodePending(value,true),actualJavaBundleSource);
        pipeline.register(Stage.SAME_INPUT_CONDITIONAL_CURRENT_PRE_DATE_CHARACTER_PREFIX_V1,CharacterBatch.class,List.of(Stage.SAME_INPUT_CONDITIONAL_CURRENT_PRE_DATE_PENDING_UPDATE_V1),(input,earlier)->{
            PendingBatch pending=earlier.required(Stage.SAME_INPUT_CONDITIONAL_CURRENT_PRE_DATE_PENDING_UPDATE_V1,PendingBatch.class);
            return new CharacterBatch(input.selected().stream().map(row->new PerArmy<>(row.core().army(),ArmyManagersPrefixes.projectCharacter(family(row,Key.CURRENT_PRE_DATE_CHARACTER_PREFIX_INPUTS_V1,Inputs.class),matching(pending.values(),row.core().army())))).toList());
        },ArmyStrengthsManagers::encodeCharacter,ArmyStrengthsManagers::encodeCharacter,actualJavaBundleSource);
        currentStage(pipeline,Stage.CURRENT_ARMY_CONDITION30_INPUTS_V1,Key.CURRENT_ARMY_CONDITION30_INPUTS_V1,Kind.CONDITION30,actualJavaBundleSource);
        pipeline.register(Stage.CURRENT_DISEMBARK_PENALTY_V1,DisembarkBatch.class,List.of(),(input,earlier)->{
            Provenance source=provenance(input.snapshot());return new DisembarkBatch(source,input.selected().stream().map(row->{ObjectNode request=JsonNodeFactory.instance.objectNode();DisembarkPenalty.Observation observation=family(row,Key.CURRENT_DISEMBARK_PENALTY_V1,DisembarkPenalty.Observation.class);request.set("raw",observation==null?JsonNodeFactory.instance.nullNode():ArmyStrengthsCodec.parseValue(new RawJson(DisembarkCodec.encodeObservation(observation))));request.set("source_provenance",source.encode(false));return new PerArmy<>(row.core().army(),DisembarkCodec.decodeProjectionRequest(ArmyJson.bytes(request)));}).toList());
        },value->encodeDisembark(value,false),value->encodeDisembark(value,true),actualJavaBundleSource);
        currentStage(pipeline,Stage.CURRENT_ARMY_FLAG20_INPUTS_V1,Key.CURRENT_ARMY_FLAG20_INPUTS_V1,Kind.FLAG20,actualJavaBundleSource);
        currentStage(pipeline,Stage.CURRENT_ARMY_FLAG21_INPUTS_V1,Key.CURRENT_ARMY_FLAG21_INPUTS_V1,Kind.FLAG21,actualJavaBundleSource);
        currentStage(pipeline,Stage.CURRENT_SELECTED_TITLE_HOLDER_OWNER_RELATION_V1,Key.CURRENT_SELECTED_TITLE_HOLDER_OWNER_RELATION_V1,Kind.HOLDER_RELATION,actualJavaBundleSource);
        currentStage(pipeline,Stage.CURRENT_ARMY_FLAG31_INPUTS_V1,Key.CURRENT_ARMY_FLAG31_INPUTS_V1,Kind.FLAG31,actualJavaBundleSource);
        // The raw combat-roles family remains registered by the existing core owner.
        pipeline.register(Stage.CURRENT_ARMY_COMBAT_ROLES_PHASE_INPUTS_V1,CombatRolesBatch.class,List.of(),(input,earlier)->{Provenance source=provenance(input.snapshot());return new CombatRolesBatch(source,input.selected().stream().map(row->new PerArmy<>(row.core().army(),CombatRolesPolicy.project(family(row,Key.CURRENT_ARMY_COMBAT_ROLES_PHASE_INPUTS_V1,CombatRoles.Inputs.class),source.combatRoles()))).toList());},value->encodeCombat(value,false),value->encodeCombat(value,true),actualJavaBundleSource);
        pipeline.register(Stage.CURRENT_POST_ADMISSION_REFRESH_INPUTS_V1,RefreshBatch.class,List.of(),(input,earlier)->new RefreshBatch(provenance(input.snapshot()),input.selected().stream().map(row->new PerArmy<>(row.core().army(),ArmyManagersRefresh.project(family(row,Key.CURRENT_POST_ADMISSION_REFRESH_INPUTS_V1,Inputs.class)))).toList()),value->encodeRefresh(value,false),value->encodeRefresh(value,true),actualJavaBundleSource);
        pipeline.register(Stage.CURRENT_PRE_DATE_CHARACTER_PREFIX_INPUTS_V1,CharacterBatch.class,List.of(Stage.SAME_INPUT_CONDITIONAL_CURRENT_PRE_DATE_CHARACTER_PREFIX_V1),(input,earlier)->earlier.required(Stage.SAME_INPUT_CONDITIONAL_CURRENT_PRE_DATE_CHARACTER_PREFIX_V1,CharacterBatch.class),ArmyStrengthsManagers::encodeCharacter,ArmyStrengthsManagers::encodeCharacter,actualJavaBundleSource);
        pipeline.register(Stage.CURRENT_PRE_DATE_DATED_APPEND_INPUTS_V1,DatedBatch.class,List.of(),(input,earlier)->new DatedBatch(input.selected().stream().map(row->new PerArmy<>(row.core().army(),ArmyManagersPrefixes.projectDated(family(row,Key.CURRENT_PRE_DATE_DATED_APPEND_INPUTS_V1,Inputs.class)))).toList()),ArmyStrengthsManagers::encodeDated,ArmyStrengthsManagers::encodeDated,actualJavaBundleSource);
    }
    private static void register(ArmyStrengthsFamilies.Registry registry,Key key,Kind kind,ExactRef source){registry.register(key,Inputs.class,(actual,context)->{
        if(actual instanceof ArmyTypes.Missing<RawJson>)return new ArmyTypes.Missing<>();if(actual instanceof ArmyTypes.NullValue<RawJson>)return new ArmyTypes.NullValue<>();
        Inputs value=decode(kind,ArmyStrengthsCodec.parseValue(((ArmyTypes.Present<RawJson>)actual).value()));return value==null?new ArmyTypes.NullValue<>():new ArmyTypes.Present<>(value);
    },value->encodeInputs(value,false),value->encodeInputs(value,true),source);}
    public static Inputs decode(Kind kind,JsonNode raw){Objects.requireNonNull(kind);Objects.requireNonNull(raw);if(raw.isNull())return null;
        if(kind==Kind.PENDING&&raw.isObject()&&!raw.has("pending_table_frame_v1")){ObjectNode copy=raw.deepCopy();copy.putNull("pending_table_frame_v1");raw=copy;}
        Inputs input=new Inputs(kind,ArmyManagersModel.decodeShape(raw,kind.shape(),kind.name().toLowerCase(java.util.Locale.ROOT)));
        switch(kind){case PENDING->ArmyManagersPending.validate(input);case DATED->ArmyManagersPrefixes.validateDated(input);case CHARACTER->ArmyManagersPrefixes.validateCharacter(input);case REFRESH->ArmyManagersRefresh.validate(input);default->ArmyManagersCurrent.validate(input);}return input;
    }
    public static JsonNode encode(Inputs value,boolean publicV2){return value==null?JsonNodeFactory.instance.nullNode():ArmyManagersModel.encode(value.value(),publicV2);}
    private static RawJson encodeInputs(ArmyTypes.Field<Inputs> field,boolean publicV2){return raw(field instanceof ArmyTypes.Present<Inputs> p?encode(p.value(),publicV2):JsonNodeFactory.instance.nullNode());}
    private static RawJson encodeDisembarkObservation(ArmyTypes.Field<DisembarkPenalty.Observation> field){return field instanceof ArmyTypes.Present<DisembarkPenalty.Observation> p?new RawJson(DisembarkCodec.encodeObservation(p.value())):raw(JsonNodeFactory.instance.nullNode());}
    private static void currentStage(ArmyStrengthsPipeline pipeline,Stage stage,Key key,Kind kind,ExactRef source){pipeline.register(stage,CurrentBatch.class,List.of(),(input,earlier)->new CurrentBatch(provenance(input.snapshot()),input.selected().stream().map(row->new PerArmy<>(row.core().army(),ArmyManagersCurrent.project(kind,family(row,key,Inputs.class)))).toList()),value->encodeCurrent(value,false),value->encodeCurrent(value,true),source);}
    static Provenance provenance(ArmyStrengths.Snapshot snapshot){return provenance(ArmyStrengthsCodec.parseValue(snapshot.original()));}
    public static Provenance provenance(JsonNode heldSnapshot){ArmyTypes.require(heldSnapshot!=null&&heldSnapshot.isObject(),"manager held snapshot object");JsonNode hello=heldSnapshot.path("diagnostics").path("hello");JsonNode version=hello.isObject()&&hello.has("expected_ck3_version")?hello.get("expected_ck3_version"):hello.get("game_version");JsonNode sha=hello.isObject()&&hello.has("expected_ck3_sha256")?hello.get("expected_ck3_sha256"):hello.get("executable_sha256");return new Provenance(nullableText(heldSnapshot.get("snapshot_id")),nullableInteger(heldSnapshot.get("revision")),nullableInteger(heldSnapshot.get("native_revision")),nullableInteger(heldSnapshot.get("date_raw")),nullableText(version),nullableText(sha));}
    private static <T>T family(ArmyStrengths.Row row,Key key,Class<T> type){var selected=row.families().stream().filter(value->value.key()==key).toList();ArmyTypes.require(selected.size()<=1,"duplicate manager family");if(selected.isEmpty())return null;var value=selected.getFirst();ArmyTypes.require(value.valueType().equals(type),"manager exact typed family mismatch");return value.value() instanceof ArmyTypes.Present<?> p?type.cast(p.value()):null;}
    private static <T>T matching(List<PerArmy<T>> values,ArmyTypes.PublicUnitId army){List<PerArmy<T>> selected=values.stream().filter(value->value.army().equals(army)).toList();ArmyTypes.require(selected.size()==1,"manager earlier stage exact Army identity");return selected.getFirst().projection();}
    private static RawJson encodePending(PendingBatch batch,boolean publicV2){return perArmy(batch.values(),value->ArmyManagersPending.encodeProjection(value,publicV2));}
    private static RawJson encodeCharacter(CharacterBatch batch){return perArmy(batch.values(),ArmyManagersPrefixes::encodeCharacter);}
    private static RawJson encodeDated(DatedBatch batch){return perArmy(batch.values(),ArmyManagersPrefixes::encodeDated);}
    private static RawJson encodeCurrent(CurrentBatch batch,boolean publicV2){return perArmy(batch.values(),value->ArmyManagersCurrent.encodeProjection(value,batch.provenance().encode(publicV2),publicV2));}
    private static RawJson encodeRefresh(RefreshBatch batch,boolean publicV2){return perArmy(batch.values(),value->ArmyManagersRefresh.encodeProjection(value,batch.provenance().encode(publicV2),publicV2));}
    private static RawJson encodeDisembark(DisembarkBatch batch,boolean publicV2){return perArmy(batch.values(),value->{ObjectNode result=(ObjectNode)ArmyStrengthsCodec.parseValue(new RawJson(DisembarkCodec.encodeProjection(value)));result.set("source_provenance",batch.provenance().encode(publicV2));return result;});}
    private static RawJson encodeCombat(CombatRolesBatch batch,boolean publicV2){return perArmy(batch.values(),value->{ObjectNode result=CombatRolesCodec.encodeProjection(value);result.set("source_provenance",batch.provenance().encode(publicV2));return result;});}
    private static <T>RawJson perArmy(List<PerArmy<T>> values,Function<T,JsonNode> encoder){ArrayNode result=JsonNodeFactory.instance.arrayNode();for(PerArmy<T> value:values)result.addObject().put("army_id",value.army().value()).set("projection",encoder.apply(value.projection()));return raw(result);}
    private static RawJson raw(JsonNode value){return new RawJson(ArmyJson.bytes(value));}
    private static String nullableText(JsonNode value){if(value==null||value.isNull())return null;ArmyTypes.require(value.isTextual(),"manager provenance text");return value.textValue();}
    private static BigInteger nullableInteger(JsonNode value){if(value==null||value.isNull())return null;ArmyTypes.require(value.isIntegralNumber(),"manager provenance exact integer");return value.bigIntegerValue();}
    private static void uint64(BigInteger value){ArmyTypes.require(value.signum()>=0&&value.bitLength()<=64,"manager provenance uint64");}
    private static void text(ObjectNode out,String field,String value){if(value==null)out.putNull(field);else out.put(field,value);}
}
