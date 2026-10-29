package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyOwnedJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsFamilies.Key.*;
import com.fasterxml.jackson.databind.JsonNode;
import java.util.List;
import java.util.function.Function;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;

/** Eleven complete owned historical family boundaries and four actual source-bound service consumers. */
public final class ArmyStrengthsPhases {
 private ArmyStrengthsPhases() { }
 public static void install(ArmyStrengthsFamilies.Registry registry,ArmyStrengthsPipeline pipeline,ExactRef actualJavaBundleSource){
  registry.register(ACTUAL_ARMY_LATE_EVENT_OBSERVATIONS_V1,ArmyNaturalEffectJournals.LateJournal.class,(v,r)->field(v,j->ArmyNaturalEffectJournals.late(j,army(r))),v->encode(v,ArmyNaturalEffectJournals.LateJournal::toJson),v->ArmyPhasePublicNumbers.late(encode(v,ArmyNaturalEffectJournals.LateJournal::toJson)),actualJavaBundleSource);
  registry.register(ACTUAL_COMPILED_EFFECT_OBSERVATIONS_V1,ArmyNaturalEffectJournals.CompiledJournal.class,(v,r)->field(v,j->ArmyNaturalEffectJournals.compiled(j,army(r))),v->encode(v,ArmyNaturalEffectJournals.CompiledJournal::toJson),v->ArmyPhasePublicNumbers.compiled(encode(v,ArmyNaturalEffectJournals.CompiledJournal::toJson)),actualJavaBundleSource);
  register(registry,ARMY_NATURAL_PHASE_OBSERVATIONS_V1,ArmyObservedSchema.Family.PHASE,ArmyObservedDtos.Phase.class,ArmyObservedDtos::decodePhase,actualJavaBundleSource);
  register(registry,ACTUAL_ARMY_REGULAR_CORE_OBSERVATIONS_V1,ArmyObservedSchema.Family.CORE,ArmyObservedDtos.Core.class,ArmyObservedDtos::decodeCore,actualJavaBundleSource);
  register(registry,ACTUAL_ARMY_DAILY_ASSAULT_PREPARATION_OBSERVATIONS_V1,ArmyObservedSchema.Family.PREPARATION,ArmyObservedDtos.Preparation.class,ArmyObservedDtos::decodePreparation,actualJavaBundleSource);
  register(registry,ACTUAL_ARMY_ASSAULT_PLACEMENT_OBSERVATIONS_V1,ArmyObservedSchema.Family.PLACEMENT,ArmyObservedDtos.Placement.class,ArmyObservedDtos::decodePlacement,actualJavaBundleSource);
  register(registry,ARMY_ACTUAL_ASSAULT_CONSUMER_OBSERVATIONS_V1,ArmyObservedSchema.Family.CONSUMER,ArmyObservedDtos.Consumer.class,ArmyObservedDtos::decodeConsumer,actualJavaBundleSource);
  register(registry,ACTUAL_ARMY_ASSAULT_GROUP_RELEASE_OBSERVATIONS_V1,ArmyObservedSchema.Family.RELEASE,ArmyObservedDtos.Release.class,ArmyObservedDtos::decodeRelease,actualJavaBundleSource);
  register(registry,NATIVE_GATHERING_DUE_NATURAL_STAGE_12004,ArmyObservedSchema.Family.DUE,ArmyObservedDtos.Due.class,ArmyObservedDtos::decodeDue,actualJavaBundleSource);
  register(registry,ACTUAL_ARMY_CLEANUP_OBSERVATIONS_V1,ArmyObservedSchema.Family.CLEANUP,ArmyObservedDtos.Cleanup.class,ArmyObservedDtos::decodeCleanup,actualJavaBundleSource);
  register(registry,ACTUAL_ARMY_PRE_DATE_PREFIX_OBSERVATIONS_V1,ArmyObservedSchema.Family.PREFIX,ArmyObservedDtos.Prefix.class,ArmyObservedDtos::decodePrefix,actualJavaBundleSource);
  ArmyPhaseConsumption.install(pipeline,actualJavaBundleSource);
 }
 private static Integer army(ArmyStrengths.RowContext row){return row.core().nativeArmy() instanceof Present<FullId> p?p.value().value():null;}
 private static <T> Field<T> field(Field<RawJson> input,Function<JsonNode,T> decode){if(input instanceof Missing<RawJson>)return new Missing<>();if(input instanceof NullValue<RawJson>)return new NullValue<>();JsonNode value=ArmyStrengthsCodec.parseValue(((Present<RawJson>)input).value());if(value.isNull())return new NullValue<>();return new Present<>(decode.apply(value));}
 private static <T> RawJson encode(Field<T> value,Function<T,JsonNode> fn){return new RawJson(ArmyJson.bytes(value instanceof Present<T> p?fn.apply(p.value()):J.nullNode()));}
 private static <T extends ArmyObservedDtos.Owned> void register(ArmyStrengthsFamilies.Registry registry,ArmyStrengthsFamilies.Key key,ArmyObservedSchema.Family family,Class<T> type,Function<JsonNode,T> decode,ExactRef source){
  registry.register(key,type,(v,r)->field(v,j->normalize(family,j,army(r),decode)),v->encode(v,ArmyObservedDtos.Owned::json),v->ArmyPhasePublicNumbers.family(family,encode(v,ArmyObservedDtos.Owned::json)),source);
 }
 static <T> T normalize(ArmyObservedSchema.Family family,JsonNode value,Integer expected,Function<JsonNode,T> decode){ArmyObservedSchema.family(family,value,expected);long full=Integer.toUnsignedLong(expected);switch(family){case PHASE->ArmyNaturalPhases.normalize(value,expected);case CORE->ArmyObservedCore.validate(value,full);case PREPARATION->ArmyObservedPreparation.validate(value,full);case PLACEMENT->ArmyObservedPlacement.validate(value,full);case CONSUMER->ArmyObservedConsumer.validate(value,full);case RELEASE->ArmyObservedReturnBoundaries.release(value,full);case DUE->ArmyObservedDue.validate(value,full);case CLEANUP->ArmyObservedReturnBoundaries.cleanup(value,full);case PREFIX->ArmyObservedReturnBoundaries.prefix(value,full);}return decode.apply(value);}
}
