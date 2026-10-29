package org.xar.ck3.control.application.driver;

import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.planning.military.ForecastReadObservation;
import org.xar.ck3.control.application.planning.military.ForecastSemanticProjection;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.application.capabilities.FactionReadObservation;
import org.xar.ck3.control.application.capabilities.FactionReadReplay;
import org.xar.ck3.control.wave2.finance.factionalerts.FactionAlertModel;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyBattleReadValue;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsReadValue;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyWindowCodec;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyWindowAttempts;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Fixed original snapshot slots, owned by the actual archived typed read producer. No query or independent writer exists here. */
public final class DriverSemanticReadState {
    public static final String SOURCES="capability_semantic_read_sources";
    public static final String FACTION_ALERTS_FIELD="player_faction_alerts";
    private static final String ATTEMPTS="capability_window_attempt_sources";
    private DriverSemanticReadState() { }
    private enum Kind { COMBAT_V2,COMBAT_V3,WAR_ENTRY,BATTLE_CONTROL,WINDOW_OVERVIEW,WINDOW_RESULTS,FACTION_ALERTS,ARMY_CORE }
    public static boolean supports(PlanningReadResult.Known<?> original) {
        Object actual=original.value();
        return actual instanceof ArmyStrengthsReadValue||actual instanceof FactionReadObservation||BattleControlSemanticProjection.supports(actual)||actual instanceof ForecastReadObservation forecast&&(forecast.kind()==ForecastReadObservation.Kind.COMBAT_V2
                ||forecast.kind()==ForecastReadObservation.Kind.COMBAT_V3||forecast.kind()==ForecastReadObservation.Kind.WAR_ENTRY)
                ||actual instanceof ArmyWindowCodec.Observation window&&window.operation()==ArmyWindowCodec.Operation.QUERY;
    }
    static OpportunityJson.Obj initializeFresh(OpportunityJson.Obj actual) {
        var fields=new LinkedHashMap<>(actual.members());for(Kind kind:Kind.values())fields.putAll(clear(kind).members());
        fields.put(SOURCES,new OpportunityJson.Obj(Map.of()));fields.put(ATTEMPTS,new OpportunityJson.Obj(Map.of()));
        for(var kind:ArmyWindowCodec.Kind.values())fields.put(attemptField(kind),OpportunityJson.Nil.INSTANCE);return new OpportunityJson.Obj(fields);
    }
    public static OpportunityJson.Obj clearForCold(OpportunityJson.Obj actual) {
        if(!actual.members().containsKey(SOURCES))return actual;
        var fields=new LinkedHashMap<>(actual.members());for(Kind kind:Kind.values())fields.putAll(clear(kind).members());
        for(var kind:ArmyWindowCodec.Kind.values())fields.put(attemptField(kind),OpportunityJson.Nil.INSTANCE);
        return new OpportunityJson.Obj(fields);
    }
    static OpportunityJson.Obj withWindowAttempts(OpportunityJson.Obj auxiliary,ArmyWindowAttempts.Snapshot actual,ActionPorts.OutcomeArchive originals) {
        var fields=new LinkedHashMap<>(auxiliary.members());var sources=new LinkedHashMap<String,OpportunityJson.Value>();
        windowAttempt(fields,sources,ArmyWindowCodec.Kind.OVERVIEW,actual.overview(),originals);
        windowAttempt(fields,sources,ArmyWindowCodec.Kind.RESULTS,actual.results(),originals);
        fields.put(ATTEMPTS,new OpportunityJson.Obj(sources));return new OpportunityJson.Obj(fields);
    }
    private static void windowAttempt(Map<String,OpportunityJson.Value> fields,Map<String,OpportunityJson.Value> sources,
            ArmyWindowCodec.Kind kind,java.util.Optional<ArmyWindowAttempts.Attempt> actual,ActionPorts.OutcomeArchive originals) {
        if(actual.isEmpty()){fields.put(attemptField(kind),OpportunityJson.Nil.INSTANCE);return;}
        var attempt=actual.orElseThrow();StrictJson.require(attempt.kind()==kind,"fixed window attempt crossed kind");
        OpportunityJson.Obj proof=new OpportunityJson.Obj(Map.of("normalized",attempt.normalized(),
                "prepared_request",DriverObservationEvidenceReader.reference(attempt.preparedRequest()),
                "original_outcome",attempt.originalOutcome().<OpportunityJson.Value>map(DriverObservationEvidenceReader::reference).orElse(OpportunityJson.Nil.INSTANCE)));
        replayAttempt(kind,proof,originals);fields.put(attemptField(kind),attempt.normalized());sources.put(kind.name(),proof);
    }
    private static String attemptField(ArmyWindowCodec.Kind kind) {
        return kind==ArmyWindowCodec.Kind.OVERVIEW?"war_declared_overview_v1_query_attempt":"war_results_window_v1_query_attempt";
    }
    private static OpportunityJson.Obj replayAttempt(ArmyWindowCodec.Kind kind,OpportunityJson.Obj proof,ActionPorts.OutcomeArchive originals) {
        StrictJson.require(proof.members().keySet().equals(Set.of("normalized","prepared_request","original_outcome")),"complete original window attempt source required");
        var normalized=OpportunityJson.object(proof.get("normalized"),"normalized window attempt");
        var prepared=originals.loadRequest(DriverObservationEvidenceReader.reference(proof.get("prepared_request")));
        String step=OpportunityJson.text(normalized.get("step"),"step");
        String expected=kind.step(ArmyWindowCodec.Operation.QUERY);
        StrictJson.require(step.equals(expected)&&prepared.step().equals(step),"window attempt original prepared operation differs");
        String status=OpportunityJson.text(normalized.get("status"),"status");
        String requestId=OpportunityJson.text(normalized.get("native_request_id"),"native_request_id");
        StrictJson.require(Set.of("pending","observed","failed").contains(status),"exact window attempt status required");
        if(status.equals("pending"))StrictJson.require(proof.get("original_outcome")==OpportunityJson.Nil.INSTANCE&&normalized.get("error")==OpportunityJson.Nil.INSTANCE,"pending window attempt cannot invent an outcome");
        else {
            var outcome=originals.load(DriverObservationEvidenceReader.reference(proof.get("original_outcome")));
            StrictJson.require(outcome.requestId().equals(requestId),"window attempt archived outcome request identity differs");
            if(status.equals("observed"))StrictJson.require(outcome instanceof NativeActionPort.AckReceived ack&&ack.nativeOk()&&normalized.get("error")==OpportunityJson.Nil.INSTANCE,"observed window attempt requires its actual native-success outcome");
            else OpportunityJson.text(normalized.get("error"),"error");
        }
        return normalized;
    }
    static OpportunityJson.Obj apply(Complete frame,OpportunityJson.Obj auxiliary,ReadContract<?> contract,
            PlanningReadResult.Known<?> actual,ActionPorts.OutcomeArchive originals) {
        PlanningReadReceipt receipt=originals.loadRead(actual.originalReceipt());
        StrictJson.require(receipt.equals(actual.receipt())&&originals.readReferenceOf(receipt).equals(actual.originalReceipt())
                &&contract.contractId().equals(receipt.contractId()),"semantic read cache requires its exact archived original contract");
        Object replayed=contract.replay(receipt);Kind kind;OpportunityJson.Obj projected;
        if(replayed instanceof ArmyStrengthsReadValue core&&actual.value() instanceof ArmyStrengthsReadValue claimed) {
            var projection=core.coreSemanticProjection();
            StrictJson.require(projection.equals(claimed.coreSemanticProjection()),"typed Army Core cache differs from the original strict decoder");
            kind=Kind.ARMY_CORE;projected=ArmyStrengthsReadValue.project(projection,receipt);
        } else if(replayed instanceof ForecastReadObservation forecast&&actual.value() instanceof ForecastReadObservation claimed) {
            StrictJson.require(forecast.equals(claimed),"typed forecast cache differs from original pure decoder");
            var projection=ForecastSemanticProjection.project(forecast,receipt,frame.semantic(),auxiliary);
            StrictJson.require(projection.semanticCache(),"this original read is history only");
            kind=Kind.valueOf(forecast.kind().name());projected=projection.fields();
        } else if(replayed instanceof ArmyBattleReadValue battle&&actual.value() instanceof ArmyBattleReadValue claimed) {
            StrictJson.require(BattleControlSemanticProjection.supports(battle)&&BattleControlSemanticProjection.same(battle,claimed),
                    "typed BattleControl cache differs from its full original strict decoder");
            kind=Kind.BATTLE_CONTROL;projected=BattleControlSemanticProjection.project(battle,frame.semantic());
        } else if(replayed instanceof ArmyWindowCodec.Observation window&&actual.value() instanceof ArmyWindowCodec.Observation claimed) {
            StrictJson.require(window.operation()==ArmyWindowCodec.Operation.QUERY&&window.kind()==claimed.kind()
                    &&window.operation()==claimed.operation()&&window.normalized().equals(claimed.normalized()),"typed window cache differs from original pure decoder");
            kind=window.kind()==ArmyWindowCodec.Kind.OVERVIEW?Kind.WINDOW_OVERVIEW:Kind.WINDOW_RESULTS;
            projected=new OpportunityJson.Obj(Map.of(windowField(kind),DriverJson.object(StrictJson.canonical(window.normalized()),DriverJson.MAX_NATIVE_BYTES)));
        } else if(replayed instanceof FactionReadObservation faction&&actual.value() instanceof FactionReadObservation claimed) {
            StrictJson.require(FactionReadReplay.copyOf(faction).equals(FactionReadReplay.copyOf(claimed)),"typed faction cache differs from its complete original pure decoder");
            StrictJson.require(FactionReadReplay.copyOf(faction).equals(replayFaction(receipt,originals)),"live faction cache cannot reproduce its archived original before-frame/wars");
            kind=Kind.FACTION_ALERTS;projected=factionFields(faction);
        } else throw new IllegalArgumentException("no fixed semantic read-cache producer for this typed original");
        StrictJson.require(current(frame,receipt),"new semantic read cache crossed its actual frame/source/session");
        var fields=new LinkedHashMap<>(auxiliary.members());fields.putAll(projected.members());
        var table=new LinkedHashMap<>(OpportunityJson.object(auxiliary.get(SOURCES),SOURCES).members());
        table.put(kind.name(),new OpportunityJson.Obj(Map.of("receipt",DriverObservationEvidenceReader.reference(actual.originalReceipt()))));
        fields.put(SOURCES,new OpportunityJson.Obj(table));return new OpportunityJson.Obj(fields);
    }
    static OpportunityJson.Obj invalidate(Complete frame,OpportunityJson.Obj auxiliary,ActionPorts.OutcomeArchive originals) {
        StrictJson.require(auxiliary.members().containsKey(SOURCES),"actual semantic read-cache ownership state is missing");
        var fields=new LinkedHashMap<>(auxiliary.members());var table=OpportunityJson.object(auxiliary.get(SOURCES),SOURCES);
        for(var entry:table.members().entrySet()) {
            Kind kind=Kind.valueOf(entry.getKey());var source=OpportunityJson.object(entry.getValue(),"semantic read source");
            StrictJson.require(source.members().keySet().equals(Set.of("receipt")),"exact original semantic cache receipt source required");
            var read=originals.loadRead(DriverObservationEvidenceReader.reference(source.get("receipt")));
            StrictJson.require(read.request().origin() instanceof CommandOrigin.Gameplay&&read.original().nativeOk(),"actual successful ordinary cache read required");
            if(!current(frame,read))fields.putAll(clear(kind).members());
        }
        return new OpportunityJson.Obj(fields);
    }
    static void replaySources(OpportunityJson.Obj auxiliary,ActionPorts.OutcomeArchive originals) {
        var table=OpportunityJson.object(auxiliary.get(SOURCES),SOURCES);
        for(var entry:table.members().entrySet()) {
            Kind kind=Kind.valueOf(entry.getKey());var source=OpportunityJson.object(entry.getValue(),"semantic read source");
            StrictJson.require(source.members().keySet().equals(Set.of("receipt")),"exact semantic cache source required");
            var reference=DriverObservationEvidenceReader.reference(source.get("receipt"));var receipt=originals.loadRead(reference);
            StrictJson.require(originals.readReferenceOf(receipt).equals(reference)&&receipt.original().nativeOk()
                    &&receipt.request().origin() instanceof CommandOrigin.Gameplay,"original semantic cache read is unavailable");
            for(String field:clear(kind).members().keySet())StrictJson.require(auxiliary.members().containsKey(field),"saved semantic cache omitted an explicit slot: "+field);
            if(kind==Kind.ARMY_CORE) {
                var expected=ArmyStrengthsReadValue.replayFields(receipt,originals);
                boolean cleared=ArmyStrengthsReadValue.cleared().members().entrySet().stream()
                        .allMatch(field->field.getValue().equals(auxiliary.get(field.getKey())));
                StrictJson.require(cleared||expected.members().entrySet().stream()
                        .allMatch(field->field.getValue().equals(auxiliary.get(field.getKey()))),
                        "saved Army Core cache differs from its archived original query");
            }
            if(kind==Kind.FACTION_ALERTS) {
                var projected=factionFields(replayFaction(receipt,originals)).get(FACTION_ALERTS_FIELD);
                StrictJson.require(auxiliary.get(FACTION_ALERTS_FIELD)==OpportunityJson.Nil.INSTANCE
                        ||projected.equals(auxiliary.get(FACTION_ALERTS_FIELD)),"saved faction cache differs from its actual archived original receipt/frames");
            }
        }
        for(Kind kind:Kind.values()) {
            if(kind==Kind.ARMY_CORE&&!table.members().containsKey(kind.name())) {
                long present=ArmyStrengthsReadValue.SNAPSHOT_FIELDS.stream().filter(auxiliary.members()::containsKey).count();
                StrictJson.require(present==0||present==ArmyStrengthsReadValue.SNAPSHOT_FIELDS.size(),"partial persisted Army Core cache slots");
                if(present>0)for(var field:ArmyStrengthsReadValue.cleared().members().entrySet())
                    StrictJson.require(field.getValue().equals(auxiliary.get(field.getKey())),"populated Army Core cache lacks its original receipt");
                continue;
            }
            if(kind==Kind.FACTION_ALERTS&&!table.members().containsKey(kind.name())) {
                // Existing owners predate this sourced slot. Missing and explicit unavailable remain distinct DATA.
                if(auxiliary.members().containsKey(FACTION_ALERTS_FIELD))StrictJson.require(auxiliary.get(FACTION_ALERTS_FIELD)==OpportunityJson.Nil.INSTANCE,
                        "populated faction cache lacks its actual original receipt");
                continue;
            }
            if(kind==Kind.BATTLE_CONTROL&&!table.members().containsKey(kind.name())) {
                // Earlier persisted Driver owners predate this cache family. All-missing is
                // that explicit legacy state; partial or populated unsourced slots are invalid.
                long present=BattleControlSemanticProjection.fields().stream().filter(auxiliary.members()::containsKey).count();
                StrictJson.require(present==0||present==BattleControlSemanticProjection.fields().size(),"partial persisted BattleControl cache slots");
                if(present>0)for(String field:BattleControlSemanticProjection.fields())
                    StrictJson.require(auxiliary.get(field)==OpportunityJson.Nil.INSTANCE,"populated BattleControl cache lacks its actual original receipt");
                continue;
            }
            for(String field:clear(kind).members().keySet())StrictJson.require(auxiliary.members().containsKey(field),"complete semantic cache state missing: "+field);
        }
        var attempts=OpportunityJson.object(auxiliary.get(ATTEMPTS),ATTEMPTS);
        for(var entry:attempts.members().entrySet()) {
            var kind=ArmyWindowCodec.Kind.valueOf(entry.getKey());var normalized=replayAttempt(kind,OpportunityJson.object(entry.getValue(),"window attempt source"),originals);
            var current=auxiliary.get(attemptField(kind));StrictJson.require(current==OpportunityJson.Nil.INSTANCE||current.equals(normalized),"saved window attempt differs from actual originals");
        }
        for(var kind:ArmyWindowCodec.Kind.values()) {
            String field=attemptField(kind);StrictJson.require(auxiliary.members().containsKey(field),"explicit window attempt slot missing");
            StrictJson.require(auxiliary.get(field)==OpportunityJson.Nil.INSTANCE||attempts.members().containsKey(kind.name()),"window attempt has no original source");
        }
    }
    private static boolean current(Complete frame,PlanningReadReceipt receipt) {
        return receipt.request().origin() instanceof CommandOrigin.Gameplay&&receipt.request().before().equals(frame.identity())
                &&receipt.request().source().equals(frame.source())&&receipt.request().sessionId().equals(frame.sessionId())
                &&receipt.before().binding().connectionGeneration().equals(frame.connectionGeneration());
    }
    public static java.util.Optional<ArmyStrengthsReadValue.CoreAvailabilityInvalidation> coreInvalidation(Complete frame,
            DriverSnapshotFacts.Known driver,java.util.Optional<org.xar.ck3.control.contracts.ExactRef> pending,ActionPorts.OutcomeArchive originals) {
        java.util.Objects.requireNonNull(pending);var source=armyCoreSource(driver.auxiliary());if(source.isEmpty())return java.util.Optional.empty();
        var reference=source.orElseThrow();var receipt=originals.loadRead(reference);
        StrictJson.require(originals.readReferenceOf(receipt).equals(reference)&&receipt.original().nativeOk()
                &&receipt.request().operation().value().equals("query-army-strengths-v1")
                &&receipt.request().origin() instanceof CommandOrigin.Gameplay,"original Army Core source required");
        if(!source.equals(pending)&&current(frame,receipt))return java.util.Optional.empty();
        return java.util.Optional.of(new ArmyStrengthsReadValue.CoreAvailabilityInvalidation(reference,frame.identity(),frame.source(),frame.sessionId(),frame.connectionGeneration()));
    }
    public static java.util.Optional<org.xar.ck3.control.contracts.ExactRef> armyCoreSource(OpportunityJson.Obj auxiliary) {
        if(!auxiliary.members().containsKey(SOURCES))return java.util.Optional.empty();
        var sources=OpportunityJson.object(auxiliary.get(SOURCES),SOURCES);
        if(!sources.members().containsKey(Kind.ARMY_CORE.name()))return java.util.Optional.empty();
        var source=OpportunityJson.object(sources.get(Kind.ARMY_CORE.name()),"Army Core source");
        StrictJson.require(source.members().keySet().equals(Set.of("receipt")),"exact Army Core receipt source required");
        return java.util.Optional.of(DriverObservationEvidenceReader.reference(source.get("receipt")));
    }
    /** Captures only the older successful source on the failed request's identical frame/source/session. */
    static java.util.Optional<org.xar.ck3.control.contracts.ExactRef> armyCoreUnavailableSource(OpportunityJson.Obj auxiliary,
            PlanningReadRequest request,ActionPorts.OutcomeArchive originals) {
        var source=armyCoreSource(auxiliary);
        return source.filter(ref->{var read=originals.loadRead(ref);return read.request().before().equals(request.before())
                &&read.request().source().equals(request.source())&&read.request().sessionId().equals(request.sessionId());});
    }
    static OpportunityJson.Obj clearArmyCoreIfSource(OpportunityJson.Obj auxiliary,
            java.util.Optional<org.xar.ck3.control.contracts.ExactRef> source) {
        return source.isPresent()&&armyCoreSource(auxiliary).equals(source)?clearArmyCore(auxiliary):auxiliary;
    }
    /** Availability-only invalidation: no failed Native observation or zero count is manufactured. */
    static OpportunityJson.Obj clearArmyCore(OpportunityJson.Obj auxiliary) {
        var fields=new LinkedHashMap<>(auxiliary.members());fields.putAll(ArmyStrengthsReadValue.cleared().members());
        var sources=new LinkedHashMap<>(OpportunityJson.object(auxiliary.get(SOURCES),SOURCES).members());
        sources.remove(Kind.ARMY_CORE.name());fields.put(SOURCES,new OpportunityJson.Obj(sources));return new OpportunityJson.Obj(fields);
    }
    private static OpportunityJson.Obj clear(Kind kind) {
        if(kind==Kind.ARMY_CORE)return ArmyStrengthsReadValue.cleared();
        if(kind==Kind.FACTION_ALERTS)return new OpportunityJson.Obj(Map.of(FACTION_ALERTS_FIELD,OpportunityJson.Nil.INSTANCE));
        if(kind==Kind.BATTLE_CONTROL)return BattleControlSemanticProjection.unavailable();
        if(kind==Kind.WINDOW_OVERVIEW||kind==Kind.WINDOW_RESULTS)return new OpportunityJson.Obj(Map.of(windowField(kind),OpportunityJson.Nil.INSTANCE));
        return ForecastSemanticProjection.unavailable(ForecastReadObservation.Kind.valueOf(kind.name())).fields();
    }
    private static OpportunityJson.Obj factionFields(FactionReadObservation observed) {
        return new OpportunityJson.Obj(Map.of(FACTION_ALERTS_FIELD,DriverJson.object(observed.normalizedAlert().bytes(),DriverJson.MAX_NATIVE_BYTES)));
    }
    /** The saved source is read-only evidence. Reopen the actual before guard; never consult a running provider. */
    private static FactionReadReplay.Decoded replayFaction(PlanningReadReceipt receipt,ActionPorts.OutcomeArchive originals) {
        org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier.requireRead(receipt,originals);
        StrictJson.require(receipt.request().operation().value().equals(FactionAlertModel.STEP),"faction cache source crossed its actual original operation");
        var frame=org.xar.ck3.control.application.effects.RootGuardEvidence.loadFrame(receipt.before().binding(),originals,
                new org.xar.ck3.control.application.effects.DriverFrameEvidenceLoader(new DriverObservationAssembler()));
        var wars=OpportunityJson.array(frame.semantic().get("active_wars"),"actual faction before active_wars");
        return FactionReadReplay.replayArchived(receipt,RawJson.fullMaterial(DriverJson.encode(new OpportunityJson.Arr(wars))),
                OpportunityJson.text(frame.semantic().get("backend_id"),"actual faction before backend"));
    }
    private static String windowField(Kind kind) {
        return switch(kind){case WINDOW_OVERVIEW->"war_declared_overview_v1_observation";case WINDOW_RESULTS->"war_results_window_v1_observation";default->throw new IllegalArgumentException("actual window kind required");};
    }
}
