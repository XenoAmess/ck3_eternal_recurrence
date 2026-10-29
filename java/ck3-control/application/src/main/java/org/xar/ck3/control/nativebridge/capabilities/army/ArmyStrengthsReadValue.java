package org.xar.ck3.control.nativebridge.capabilities.army;

import java.math.BigInteger;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.application.effects.DriverFrameEvidenceLoader;
import org.xar.ck3.control.application.effects.RootGuardEvidence;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.driver.DriverObservationAssembler;
import org.xar.ck3.control.application.driver.DriverJson;
import java.util.Arrays;
import java.nio.ByteOrder;
import java.nio.ByteBuffer;
import java.util.HashSet;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known;
import org.xar.ck3.control.application.driver.DriverSemanticReadState;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.require;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** A closed Core view of the original typed read. It carries no action or live-read authority. */
public interface ArmyStrengthsReadValue {
    enum Scope { FULL_PUBLISHED, SUBSET }
    CoreProjection coreSemanticProjection();
    enum CoreRole { PLAYER, ACTIVE_WAR_ALLY, ACTIVE_WAR_ENEMY }
    record ScopeEntry(PublicUnitId army,CoreRole role,List<PositiveId> wars) {
        public ScopeEntry { Objects.requireNonNull(army);Objects.requireNonNull(role);wars=distinct(wars,0,65536,"scope wars"); }
    }
    /** The original ordered live scope algorithm also replays the archived before frame. */
    static List<ScopeEntry> scope(com.fasterxml.jackson.databind.node.ObjectNode snapshot) {
        LinkedHashMap<PublicUnitId,ScopeEntry> ordered = new LinkedHashMap<>();
        for (com.fasterxml.jackson.databind.JsonNode army : ArmyJson.array(ArmyJson.get(snapshot, "player_armies"), value -> value)) admit(ordered, army, CoreRole.PLAYER);
        record War(PositiveId id, List<com.fasterxml.jackson.databind.JsonNode> allies, List<com.fasterxml.jackson.databind.JsonNode> enemies) { }
        List<War> wars = new ArrayList<>();
        for (com.fasterxml.jackson.databind.JsonNode warNode : ArmyJson.array(ArmyJson.get(snapshot, "active_wars"), value -> value)) {
            com.fasterxml.jackson.databind.node.ObjectNode war = ArmyJson.object(warNode); PositiveId warId = ArmyJson.id(ArmyJson.get(war, "war_id"));
            List<com.fasterxml.jackson.databind.JsonNode> allies = ArmyJson.array(ArmyJson.get(war, "allied_armies"), value -> value), enemies = ArmyJson.array(ArmyJson.get(war, "enemy_armies"), value -> value);
            wars.add(new War(warId, allies, enemies));
            allies.forEach(army -> admit(ordered, army, CoreRole.ACTIVE_WAR_ALLY)); enemies.forEach(army -> admit(ordered, army, CoreRole.ACTIVE_WAR_ENEMY));
        }
        for (War war : wars) {
            Set<PublicUnitId> members = new HashSet<>();
            war.allies().forEach(army -> members.add(ArmyJson.unit(ArmyJson.get(ArmyJson.object(army), "army_id"))));
            war.enemies().forEach(army -> members.add(ArmyJson.unit(ArmyJson.get(ArmyJson.object(army), "army_id"))));
            for (PublicUnitId member : members) {
                ScopeEntry prior = ordered.get(member); List<PositiveId> ids = new ArrayList<>(prior.wars());
                if (!ids.contains(war.id())) ids.add(war.id()); ordered.put(member, new ScopeEntry(member, prior.role(), ids));
            }
        }
        return List.copyOf(ordered.values());
    }
    private static void admit(LinkedHashMap<PublicUnitId,ScopeEntry> rows, com.fasterxml.jackson.databind.JsonNode raw, CoreRole role) {
        PublicUnitId id = ArmyJson.unit(ArmyJson.get(ArmyJson.object(raw), "army_id")); ScopeEntry prior = rows.get(id);
        // Enum order is the original precedence: player, ally, enemy. Encounter ordering remains unchanged.
        rows.put(id, prior == null ? new ScopeEntry(id, role, List.of()) : new ScopeEntry(id,
                role.ordinal() < prior.role().ordinal() ? role : prior.role(), prior.wars()));
    }

    /** Restrictive planning DATA, bound to one target frame and its older source; it grants no observed Core. */
    record CoreAvailabilityInvalidation(ExactRef receipt,ObservationIdentity before,G2Source source,String sessionId,
            BigInteger connectionGeneration) {
        public CoreAvailabilityInvalidation {
            Objects.requireNonNull(receipt);Objects.requireNonNull(before);Objects.requireNonNull(source);StrictJson.text(sessionId);
            UInt64.positive(connectionGeneration);
        }
        public Obj planningSnapshot(Complete frame,Known driver) {
            require(before.equals(frame.identity())&&source.equals(frame.source())&&sessionId.equals(frame.sessionId())
                    &&connectionGeneration.equals(frame.connectionGeneration()),"Core invalidation crossed its target frame/source/session/connection");
            if(!DriverSemanticReadState.armyCoreSource(driver.auxiliary()).equals(java.util.Optional.of(receipt)))return frame.semantic();
            var fields=new LinkedHashMap<>(frame.semantic().members());fields.putAll(cleared().members());return new Obj(fields);
        }
    }
    record CoreProjection(ArmyRequests.StrengthProfile profile, Scope scope, Availability status,
            BigInteger querySequence, List<Obj> rows) {
        public CoreProjection {
            Objects.requireNonNull(profile); Objects.requireNonNull(scope); Objects.requireNonNull(status);
            new UInt64(querySequence); require(querySequence.signum() > 0, "positive Core query sequence required");
            require(status == Availability.AVAILABLE || status == Availability.PARTIAL, "actual Core aggregate status required");
            rows = List.copyOf(rows); require(rows.size() <= 65536, "bounded Core scope required");
            Set<Integer> ids = new HashSet<>(); boolean allAvailable = true;
            for (Obj row : rows) {
                require(row.members().keySet().equals(CORE_FIELDS), "exact eleven Core fields required");
                int id = exactInt32(row.get("army_id"), "army_id"); new PublicUnitId(id);
                require(ids.add(id), "duplicate Core Army identity");
                String state = text(row.get("status"), "status");
                require(state.equals("available") || state.equals("unavailable"), "exact Core row status required");
                allAvailable &= state.equals("available");
                require(Set.of("player", "active_war_ally", "active_war_enemy").contains(text(row.get("scope_role"), "scope_role")), "Core scope role required");
                Set<Integer> wars = new HashSet<>();
                for (Value war : array(row.get("war_ids"), "war_ids")) {
                    int value = exactInt32(war, "war_id"); new PositiveId(value);
                    require(wars.add(value), "duplicate Core war identity");
                }
                Value nativeArmy = row.get("native_carmy_id");
                if (nativeArmy != Nil.INSTANCE) new FullId(exactInt32(nativeArmy, "native_carmy_id"));
                require(integer(row.get("ai_base_power_scale"), "ai_base_power_scale").equals(BigInteger.valueOf(100000)), "Core power scale required");
                for (String key : List.of("regiment_count", "current_soldiers", "maximum_soldiers")) {
                    Value value = row.get(key);
                    require(state.equals("available") ? value instanceof IntegerValue : value == Nil.INSTANCE, "Core availability is atomic");
                    if (value instanceof IntegerValue number) require(number.value().signum() >= 0 && number.value().bitLength() <= 31, "nonnegative Core int32 required");
                }
                if (state.equals("available")) {
                    require(nativeArmy != Nil.INSTANCE, "available Core native Army required");
                    require(integer(row.get("ai_base_power_raw"), "ai_base_power_raw").bitLength()<=63,"Core power requires signed64");
                    require(row.get("unavailable_reason") == Nil.INSTANCE, "available Core reason must be null");
                } else {
                    require(row.get("ai_base_power_raw") == Nil.INSTANCE, "unavailable Core power must be null");
                    StrictJson.text(text(row.get("unavailable_reason"), "unavailable_reason"));
                }
            }
            require((status == Availability.AVAILABLE) == allAvailable, "Core aggregate differs from rows");
        }
    }
    static int exactInt32(Value raw,String name) {
        BigInteger value=integer(raw,name);require(value.bitLength()<=31,"Core signed32 width required");return value.intValue();
    }
    Set<String> CORE_FIELDS = Set.of("status", "army_id", "native_carmy_id", "scope_role", "war_ids",
            "regiment_count", "current_soldiers", "maximum_soldiers", "ai_base_power_raw", "ai_base_power_scale", "unavailable_reason");
    Set<String> SNAPSHOT_FIELDS = Set.of("army_strengths", "army_strengths_status", "army_strengths_query_sequence",
            "army_strengths_queried_snapshot_id", "army_strengths_queried_revision", "army_strengths_profile", "army_observed_phase_coverage");

    /** Only the default full ordinary profile can enter the ordinary snapshot cache. */
    static Obj project(CoreProjection value, PlanningReadReceipt original) {
        Objects.requireNonNull(value); Objects.requireNonNull(original);
        require(original.request().operation().value().equals("query-army-strengths-v1") && original.original().nativeOk(),
                "successful original Army read required");
        if (value.scope() != Scope.FULL_PUBLISHED || value.profile() != ArmyRequests.StrengthProfile.ORDINARY_CORE_V1) return cleared();
        var frame = original.request().before().frame();
        var fields = new LinkedHashMap<String, Value>();
        fields.put("army_strengths", new Arr(value.rows().stream().map(row -> (Value) row).toList()));
        fields.put("army_strengths_status", new Text(value.status().name().toLowerCase(Locale.ROOT)));
        fields.put("army_strengths_query_sequence", new IntegerValue(value.querySequence()));
        fields.put("army_strengths_queried_snapshot_id", new Text(frame.snapshotId()));
        fields.put("army_strengths_queried_revision", new IntegerValue(frame.revision()));
        fields.put("army_strengths_profile", new Text("ordinary_core_v1"));
        fields.put("army_observed_phase_coverage", new Text("not_requested"));
        return new Obj(fields);
    }
    /** Reproduce only these closed Core fields from the archived original query, never a provider or a new read. */
    static Obj replayFields(PlanningReadReceipt receipt,ActionPorts.OutcomeArchive originals) {
        NativeRecordedEvidenceVerifier.requireRead(receipt,originals);
        var frameLoader=new DriverFrameEvidenceLoader(new DriverObservationAssembler());
        var before=RootGuardEvidence.loadFrame(receipt.before().binding(),originals,frameLoader);
        var after=RootGuardEvidence.loadFrame(receipt.after().binding(),originals,frameLoader);
        require(receipt.request().before().equals(before.identity())&&before.identity().equals(after.identity())
                &&before.source().equals(after.source())&&before.sessionId().equals(after.sessionId())
                &&before.connectionGeneration().equals(after.connectionGeneration()),"Core original query crossed its actual before/after frame");
        List<ScopeEntry> published=scope(ArmyJson.parse(DriverJson.encode(before.semantic())));
        require(published.equals(scope(ArmyJson.parse(DriverJson.encode(after.semantic())))),
                "Core original query crossed its ordered published scope");
        var arguments=receipt.request().arguments();
        String profile=text(arguments.get("profile"),"original Core profile");
        ArmyRequests.StrengthProfile selected=switch(profile){
            case "ordinary_core_v1"->ArmyRequests.StrengthProfile.ORDINARY_CORE_V1;
            case "observed_history_full_v1"->ArmyRequests.StrengthProfile.OBSERVED_HISTORY_FULL_V1;
            default->throw new IllegalArgumentException("unknown original Core profile");
        };
        String mode=text(arguments.get("mode"),"original Core mode");
        require(Set.of("EXPLICIT_RICH","AUTO_CORE","PRIVATE_AUTO_SCALAR").contains(mode),"original Core mode required");
        require(mode.equals("EXPLICIT_RICH")||selected==ArmyRequests.StrengthProfile.ORDINARY_CORE_V1,"automatic Core profile drift");
        Set<String> argumentFields=new HashSet<>(Set.of("profile","mode","ordered_refill_entry_mode","ordered_besieging_entry_mode"));
        if(arguments.members().containsKey("army_ids"))argumentFields.add("army_ids");
        require(arguments.members().keySet().equals(argumentFields),"exact original Core arguments required");
        for(String entry:List.of("ordered_refill_entry_mode","ordered_besieging_entry_mode"))
            require(Set.of("observed_prepared","fixed_chunk0_prepare").contains(text(arguments.get(entry),entry)),"original Core entry mode required");
        require(mode.equals("EXPLICIT_RICH")||!arguments.members().containsKey("army_ids"),"automatic Core cannot inherit an explicit subset");
        List<PublicUnitId> requested=arguments.members().containsKey("army_ids")?distinct(array(arguments.get("army_ids"),"requested Core armies")
                .stream().map(value->new PublicUnitId(exactInt32(value,"requested army_id"))).toList(),1,64,"requested Core armies"):List.of();
        var selectedScope=new ArrayList<ScopeEntry>();
        for(PublicUnitId id:requested)selectedScope.add(published.stream().filter(row->row.army().equals(id)).findFirst()
                .orElseThrow(()->new IllegalArgumentException("requested Core Army outside its original published scope")));
        Obj raw=DriverJson.object(
                receipt.original().originalResultToken().orElseThrow().bytes(),
                DriverJson.MAX_NATIVE_BYTES);
        require(text(raw.get("step"),"step").equals("query-army-strengths-v1")&&bool(raw.get("accepted"),"accepted"),
                "actual accepted original Core result required");
        require(text(raw.get("army_strengths_profile"),"profile").equals(mode.equals("PRIVATE_AUTO_SCALAR")?"private_auto_scalar_v1":profile)
                &&text(raw.get("army_observed_phase_coverage"),"coverage").equals(
                        selected==ArmyRequests.StrengthProfile.ORDINARY_CORE_V1?"not_requested":"exported_retained"),
                "original Core requested profile differs from its result");
        var rows=array(raw.get("army_strengths"),"original Core rows").stream().map(value->{
            Obj row=object(value,"original Core row");var fields=new LinkedHashMap<String,Value>();
            for(String key:CORE_FIELDS){require(row.members().containsKey(key),"original Core field missing");fields.put(key,row.get(key));}
            return new Obj(fields);
        }).toList();
        var ack=receipt.original();byte[] ackPacket=ack.originalPacket();
        Obj envelope=packet(ackPacket);
        require(Arrays.equals(Arrays.copyOfRange(ackPacket,4,ackPacket.length),ack.originalFrame().bytes())
                &&new Text("command_result").equals(envelope.get("type"))&&new IntegerValue(BigInteger.ONE).equals(envelope.get("protocol_version"))
                &&new Text(receipt.requestId()).equals(envelope.get("request_id"))&&new Bool(true).equals(envelope.get("ok"))
                &&raw.equals(object(envelope.get("result"),"actual Core ACK result")),"original Core ACK packet/token differs");
        Obj wire=packet(ack.outbound().orElseThrow().originalPacket());
        var wireFields=new HashSet<>(Set.of("type","protocol_version","request_id","step","army_strengths_profile"));
        for(String field:List.of("expected_revision","expected_snapshot_revision","army_ids"))if(wire.members().containsKey(field))wireFields.add(field);
        require(wire.members().keySet().equals(wireFields)&&new Text("execute_step").equals(wire.get("type"))
                &&new IntegerValue(BigInteger.ONE).equals(wire.get("protocol_version"))
                &&new Text(receipt.requestId()).equals(wire.get("request_id"))
                &&new Text(receipt.request().operation().value()).equals(wire.get("step"))
                &&raw.get("army_strengths_profile").equals(wire.get("army_strengths_profile")),"Core actual outbound profile/envelope differs");
        require(wire.members().containsKey("expected_revision")||wire.members().containsKey("expected_snapshot_revision"),"Core actual outbound native revision required");
        for(String field:List.of("expected_revision","expected_snapshot_revision"))if(wire.members().containsKey(field))
            require(new UInt64(integer(wire.get(field),field)).value().equals(before.identity().frame().identity().nativeRevision()),"Core outbound native revision differs");
        boolean wireSubset=wire.members().containsKey("army_ids");
        require(wireSubset==raw.members().containsKey("army_strengths_query_scope"),"Core outbound subset/result marker differs");
        if(wireSubset)require(arguments.members().containsKey("army_ids")&&wire.get("army_ids").equals(arguments.get("army_ids")),
                "Core actual outbound subset differs from logical request");
        Scope scope=wireSubset?Scope.SUBSET:Scope.FULL_PUBLISHED;
        if(scope==Scope.SUBSET) {
            require(arguments.members().containsKey("army_ids"),"subset Core requires its actual requested armies");
            Obj echo=object(raw.get("army_strengths_query_scope"),"original Core subset echo");
            require(echo.members().keySet().equals(Set.of("army_ids","published_scope_status")),"exact original Core subset echo required");
            require(array(echo.get("army_ids"),"Core subset echo").stream()
                    .map(value->new PublicUnitId(exactInt32(value,"echo army_id"))).toList().equals(requested),"original Core subset echo changed");
            require(Set.of("available","partial").contains(text(echo.get("published_scope_status"),"published_scope_status")),"Core published status required");
        }
        var actualScope=rows.stream().map(row->new ScopeEntry(new PublicUnitId(exactInt32(row.get("army_id"),"army_id")),
                CoreRole.valueOf(text(row.get("scope_role"),"scope_role").toUpperCase(Locale.ROOT)),
                array(row.get("war_ids"),"war_ids").stream().map(value->new PositiveId(exactInt32(value,"war_id"))).toList())).toList();
        require(actualScope.equals(scope==Scope.SUBSET?selectedScope:published),"Core rows differ from original ordered army/role/war scope");
        Availability status=switch(text(raw.get("status"),"Core status")){
            case "available"->Availability.AVAILABLE;case "partial"->Availability.PARTIAL;
            default->throw new IllegalArgumentException("original Core status required");
        };
        return project(new CoreProjection(selected,scope,status,integer(raw.get("query_sequence"),"Core sequence"),rows),receipt);
    }
    /** Fixed retained Core envelope only; the group JSON parser keeps integer token identity. */
    private static Obj packet(byte[] bytes) {
        require(bytes.length>4&&ByteBuffer.wrap(bytes,0,4).order(ByteOrder.LITTLE_ENDIAN).getInt()==bytes.length-4,
                "complete Core native LE packet required");
        return DriverJson.object(Arrays.copyOfRange(bytes,4,bytes.length),DriverJson.MAX_NATIVE_BYTES);
    }
    /** Clearing cache availability is not an observation of zero soldiers or a successful query. */
    static Obj cleared() {
        var fields = new LinkedHashMap<String, Value>();
        for (String key : SNAPSHOT_FIELDS) fields.put(key, key.equals("army_strengths") ? new Arr(List.of()) : Nil.INSTANCE);
        return new Obj(fields);
    }
}

