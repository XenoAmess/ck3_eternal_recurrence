package org.xar.ck3.control.application.planning.sway;

import static org.xar.ck3.control.contracts.StrictJson.require;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.HashSet;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.m6.G2M6Contracts.Identity;
import org.xar.ck3.control.g2.m6.G2M6Contracts.NativeSubject;
import org.xar.ck3.control.g2.m6.M6TerminalSourceComposition;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** All four actual M6 query routes consume full guarded originals. No query response grants an action. */
public final class SwayObservationReads {
    private SwayObservationReads() { }
    public enum Kind {
        COMPLETION("query-sway-completion-v1-private", "sway_completion", "allow_private_active_scheme_sway_completion_query"),
        EXECUTION("query-sway-completion-execution-v1-private", "sway_completion_execution", "allow_private_active_scheme_sway_completion_execution_query"),
        TERMINATION("query-sway-completion-termination-v1-private", "sway_completion_termination", "allow_private_active_scheme_sway_completion_termination_query"),
        OPINION("query-sway-outcome-opinion-v1-private", "sway_outcome_opinion", "allow_private_active_scheme_sway_outcome_opinion_query");
        private final String step, field, permission;
        Kind(String step, String field, String permission) { this.step = step; this.field = field; this.permission = permission; }
        public String step() { return step; }
    }
    public record Query(Kind kind, Identity identity, Optional<BigInteger> afterSequence) {
        public Query {
            Objects.requireNonNull(kind); Objects.requireNonNull(identity); Objects.requireNonNull(afterSequence);
            require(journal(kind)==afterSequence.isPresent(), "only native execution/termination journals carry a cursor");
            afterSequence.ifPresent(value->SwayNativeWire.u64(value,0));
        }
        public static Query current(Kind kind,Identity identity) {return new Query(kind,identity,journal(kind)?Optional.of(BigInteger.ZERO):Optional.empty());}
    }
    public record Plane(Kind kind, SwayNativeWire.Binding binding, Identity identity, Optional<BigInteger> afterSequence, ProjectionJson normalized) {
        public Plane { Objects.requireNonNull(kind); Objects.requireNonNull(binding); Objects.requireNonNull(identity); Objects.requireNonNull(afterSequence); Objects.requireNonNull(normalized); require(journal(kind)==afterSequence.isPresent(),"typed journal cursor presence differs");afterSequence.ifPresent(value->SwayNativeWire.u64(value,0)); }
    }
    public record JournalQuery(Kind kind,NativeSubject subject,BigInteger afterSequence) {
        public JournalQuery {Objects.requireNonNull(kind);Objects.requireNonNull(subject);require(journal(kind),"only execution or termination has a public cursor");SwayNativeWire.u64(afterSequence,0);if(kind==Kind.EXECUTION){SwayNativeWire.currentCharacter(subject.actorCharacterId());SwayNativeWire.currentCharacter(subject.targetCharacterId());}}
    }
    /** A public source read can name any actual native full ID without inventing an original submitted action. */
    public record JournalPlane(Kind kind,SwayNativeWire.Binding binding,NativeSubject subject,BigInteger afterSequence,ProjectionJson normalized) {
        public JournalPlane {Objects.requireNonNull(kind);Objects.requireNonNull(binding);Objects.requireNonNull(subject);Objects.requireNonNull(normalized);require(journal(kind),"public journal kind");SwayNativeWire.u64(afterSequence,0);}
    }
    public record JournalBatch(JournalPlane primary,JournalPlane independentPeer,Optional<ProjectionJson> originalComposition) {
        public JournalBatch {
            Objects.requireNonNull(primary);Objects.requireNonNull(independentPeer);Objects.requireNonNull(originalComposition);
            require(primary.kind()!=independentPeer.kind()&&independentPeer.afterSequence().signum()==0
                    &&primary.subject().equals(independentPeer.subject())&&primary.binding().equals(independentPeer.binding()),"public source pair needs the opposite independent cursor0 journal in its identical guarded frame");
        }
    }
    public record Actors(long actorCharacterId,long targetCharacterId) {
        public Actors {
            NativeCharacterId.of(actorCharacterId);
            NativeCharacterId.of(targetCharacterId);
            require(actorCharacterId != targetCharacterId, "Sway native actor differs from target");
        }
    }
    public sealed interface DirectSubject permits CompletionSubject,OpinionSubject {Actors actors();Optional<NativeSubject> instance();}
    public record CompletionSubject(NativeSubject value) implements DirectSubject {
        public CompletionSubject {Objects.requireNonNull(value);}
        @Override public Actors actors(){return new Actors(value.actorCharacterId(),value.targetCharacterId());}
        @Override public Optional<NativeSubject> instance(){return Optional.of(value);}
    }
    public record OpinionSubject(Actors actors) implements DirectSubject {
        public OpinionSubject {Objects.requireNonNull(actors);}
        @Override public Optional<NativeSubject> instance(){return Optional.empty();}
    }
    public record DirectQuery(Kind kind,DirectSubject subject) {
        public DirectQuery {Objects.requireNonNull(kind);Objects.requireNonNull(subject);require(kind==Kind.COMPLETION&&subject instanceof CompletionSubject||kind==Kind.OPINION&&subject instanceof OpinionSubject,"direct completion needs its full native subject; opinion has only actual actor/target");}
    }
    public record DirectPlane(DirectQuery query,SwayNativeWire.Binding binding,ProjectionJson normalized) {
        public DirectPlane {Objects.requireNonNull(query);Objects.requireNonNull(binding);Objects.requireNonNull(normalized);require(query.subject().actors().actorCharacterId()==binding.actor(),"actual direct read player differs");}
    }
    public record DirectBatch(DirectPlane primary,Optional<ProjectionJson> originalComposition) {
        public DirectBatch {Objects.requireNonNull(primary);Objects.requireNonNull(originalComposition);}
    }
    private static final Set<String> COMPLETION = Set.of("schema", "schema_version", "build_version", "executable_sha256", "adapter_id", "private_build", "read_only", "advertised", "available", "unavailable_reason", "snapshot_revision", "date_raw", "actor_character_id", "target_character_id", "scheme_instance_id", "scheme_instance_generation", "native_source_kind", "current_instance_retention", "instance_source_observed", "instance_present", "storage_slot_reused", "exact_instance_join_ready", "native_owner_raw", "owner_matches_actor", "owner_cleared", "native_status_observed", "native_status_raw", "native_status_key", "native_terminal_state_observed", "native_success_chance_observed", "native_success_chance_raw", "native_success_chance_scale", "native_success_chance_unit", "terminal_cause_observed", "terminal_cause");
    private static final Set<String> OPINION = Set.of("schema", "build", "available", "unavailable_reason", "snapshot_revision", "date_raw", "actor_character_id", "target_character_id", "target_opinion_of_actor", "scheme_sway_opinion", "sway_blocker_opinion", "instance_terminal_outcome_observed", "cancel_outcome_observed");
    private static final Set<String> EXECUTION = Set.of("schema", "available", "unavailable_reason", "read_only", "observer_attached", "actor_character_id", "target_character_id", "scheme_instance_id", "after_sequence", "earliest_sequence", "latest_sequence", "retention_gap", "material_effect_observed", "native_terminal_state_observed", "records");
    private static final Set<String> TERMINATION = Set.of("schema", "available", "unavailable_reason", "read_only", "observer_attached", "actor_character_id", "target_character_id", "scheme_instance_id", "after_sequence", "earliest_sequence", "latest_sequence", "retention_gap", "session_records_only", "material_effect_observed", "records");

    public static ReadContract<Plane> contract(ExactRef definitionSource, Query query) {
        Kind kind=query.kind(); Identity identity=query.identity();
        Objects.requireNonNull(kind); Objects.requireNonNull(identity);
        if (kind == Kind.EXECUTION) {
            SwayNativeWire.currentCharacter(identity.actorCharacterId());
            SwayNativeWire.currentCharacter(identity.targetCharacterId());
        }
        OperationKey key = new OperationKey(kind.step);
        return new ReadContract<>("sway-" + kind.name().toLowerCase(java.util.Locale.ROOT) + (journal(kind)?"-actual4/v2:":"-actual4:") + identity.actionId()+query.afterSequence().map(value->":"+value).orElse(""), key, Optional.empty(), kind.permission,
                ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE, ReadContract.WireProfile.G2_PRIVATE_QUERY, definitionSource,
                (request, requestId) -> {
                    Set<String> fields = journal(kind)?Set.of("target_character_id","scheme_instance_id","after_sequence") : kind == Kind.OPINION ? Set.of("target_character_id") : Set.of("target_character_id", "scheme_instance_id");
                    JsonNode input = SwayNativeBindings.args(request.arguments(), fields);
                    long target = observedCharacter(kind, input.get("target_character_id"));
                    require(target == identity.targetCharacterId() && request.before().frame().identity().player().longValueExact() == identity.actorCharacterId(), "Sway observation actor/target differs");
                    ObjectNode extra = StrictJson.object(); extra.put("actor_character_id", identity.actorCharacterId()); extra.put("target_character_id", identity.targetCharacterId());
                    if (kind != Kind.OPINION) {
                        require(SwayNativeWire.integer(input, "scheme_instance_id", 0, 0xffff_fffeL) == identity.schemeInstanceId(), "Sway observation original full ID differs");
                        extra.put("scheme_instance_id", identity.schemeInstanceId());
                    }
                    if (journal(kind)) {
                        BigInteger cursor=decimalCursor(input.get("after_sequence")); require(cursor.equals(query.afterSequence().orElseThrow()),"native journal cursor differs from exact registered query");
                        extra.put("after_sequence",cursor);
                    }
                    return SwayNativeBindings.primitive(kind.step, extra);
                }, original -> decode(original, kind, identity));
    }

    public static Plane decode(PlanningReadReceipt original, Kind kind, Identity identity) {
        Optional<BigInteger> requested=Optional.empty();
        if(journal(kind)) {
            JsonNode requestArguments;
            String legacy="sway-"+kind.name().toLowerCase(java.util.Locale.ROOT)+"-actual4:"+identity.actionId();
            if(original.contractId().equals(legacy)) {
                // Explicit historical v1: its original factory had exactly two argument fields and hardcoded cursor0.
                requestArguments=SwayNativeBindings.args(original.request().arguments(),Set.of("target_character_id","scheme_instance_id"));requested=Optional.of(BigInteger.ZERO);
            } else {
                requestArguments=SwayNativeBindings.args(original.request().arguments(),Set.of("target_character_id","scheme_instance_id","after_sequence"));requested=Optional.of(decimalCursor(requestArguments.get("after_sequence")));
                require(original.contractId().equals("sway-"+kind.name().toLowerCase(java.util.Locale.ROOT)+"-actual4/v2:"+identity.actionId()+":"+requested.orElseThrow())
                        ||original.contractId().equals(journalId(new JournalQuery(kind,identity.nativeSubject(),requested.orElseThrow()))),"journal version/identity/cursor contract differs");
            }
            require(observedCharacter(kind,requestArguments.get("target_character_id"))==identity.targetCharacterId()
                    &&SwayNativeWire.integer(requestArguments,"scheme_instance_id",0,0xffff_fffeL)==identity.schemeInstanceId(),"archived journal request changed original target/full instance");
        }
        var decoded=decodeNative(original,kind,new Actors(identity.actorCharacterId(),identity.targetCharacterId()),Optional.of(identity.nativeSubject()),requested);
        return new Plane(kind,decoded.binding(),identity,requested,decoded.normalized());
    }
    private record Decoded(SwayNativeWire.Binding binding,ProjectionJson normalized) { }
    private static Decoded decodeNative(PlanningReadReceipt original,Kind kind,Actors actors,Optional<NativeSubject> instance,Optional<BigInteger> requested) {
        SwayNativeWire.Binding binding = SwayNativeBindings.bind(original, new OperationKey(kind.step));
        require(binding.actor()==actors.actorCharacterId(),"native subject is not the actual guarded current actor");
        ObjectNode packet = StrictJson.object(StrictJson.parse(original.original().originalFrame().bytes(), SwayNativeWire.MAX), Set.of("type", "protocol_version", "request_id", "ok", "result"));
        SwayNativeWire.equals(packet, "type", "command_result"); SwayNativeWire.equals(packet, "request_id", original.requestId()); SwayNativeWire.integer(packet, "protocol_version", 1, 1); require(SwayNativeWire.bool(packet, "ok"), "M6 native query rejected");
        Set<String> fields = new HashSet<>(Set.of("step", "accepted", "status", "private_build", "read_only", "advertised", "backend_id", kind.field));
        boolean journal = journal(kind);
        if (journal) fields.addAll(Set.of("snapshot_revision", "date_raw", "build_version", "executable_sha256"));
        ObjectNode result = StrictJson.object(packet.get("result"), fields); SwayNativeWire.equals(result, "step", kind.step); SwayNativeWire.equals(result, "backend_id", "native-headless");
        require(SwayNativeWire.bool(result, "accepted") && SwayNativeWire.bool(result, "private_build") && SwayNativeWire.bool(result, "read_only") && !SwayNativeWire.bool(result, "advertised"), "M6 private read flags differ");
        require(result.get(kind.field) instanceof ObjectNode, "M6 native body object required"); ObjectNode body = ((ObjectNode)result.get(kind.field)).deepCopy();
        String status = SwayNativeWire.bool(body, "available") ? "available" : "unavailable"; SwayNativeWire.equals(result, "status", status);
        switch (kind) {
            case COMPLETION -> completion(body, binding, instance.orElseThrow());
            case OPINION -> opinion(body, binding, actors);
            case EXECUTION, TERMINATION -> {
                Set<String> actualFields = new HashSet<>(kind == Kind.EXECUTION ? EXECUTION : TERMINATION);
                if (kind == Kind.TERMINATION && body.has("common_native_end")) actualFields.add("common_native_end"); StrictJson.object(body, actualFields);
                SwayNativeWire.equals(body, "schema", kind == Kind.EXECUTION ? "xar.ck3.sway-completion-execution.v1" : "xar.ck3.sway-completion-termination.v1");
                build(result); require(SwayNativeWire.wide(result, "snapshot_revision", 1).equals(binding.revision()) && SwayNativeWire.signed(result, "date_raw") == binding.date(), "M6 journal envelope crossed current frame");
                require(SwayNativeWire.bool(body, "read_only") && !SwayNativeWire.bool(body, "material_effect_observed"), "journal is observation only");
                SwayNativeWire.bool(body, "observer_attached"); SwayNativeWire.bool(body, "retention_gap"); SwayNativeWire.string(body, "unavailable_reason");
                pair(body, instance.orElseThrow(), kind); require(SwayNativeWire.wide(body, "after_sequence", 0).equals(requested.orElseThrow()), "native journal echoed another cursor");
                BigInteger earliest = SwayNativeWire.wide(body, "earliest_sequence", 0), latest = SwayNativeWire.wide(body, "latest_sequence", 0);
                require((earliest.signum() == 0) == (latest.signum() == 0) && earliest.compareTo(latest) <= 0, "retained journal sequence bounds");
                require(body.get("records").isArray() && body.get("records").size() <= 4096, "bounded native journal records");
                BigInteger previous=requested.orElseThrow();
                for(JsonNode record:body.get("records")) {
                    BigInteger sequence=SwayNativeWire.wide(record,"sequence",1);
                    require(sequence.compareTo(previous)>0 && sequence.compareTo(earliest)>=0 && sequence.compareTo(latest)<=0,"native journal records must retain increasing post-cursor sequence within original bounds");
                    previous=sequence;
                }
                if (kind == Kind.EXECUTION) require(!SwayNativeWire.bool(body, "native_terminal_state_observed"), "execution family cannot assign terminal");
                else require(SwayNativeWire.bool(body, "session_records_only"), "termination retains its native session scope");
                body.put("build_version", SwayNativeWire.BUILD); body.put("executable_sha256", SwayNativeWire.EXE);
                body.put("source_snapshot_revision", binding.revision()); body.put("source_date_raw", binding.date());
            }
        }
        // Normalization adds provenance from the already validated guarded source, never to a native request.
        body.put("exact_ck3_build", SwayNativeWire.BUILD); body.put("exe_sha256", SwayNativeWire.EXE);
        ProjectionJson normalized = SwayNativeWire.json(body);
        if (kind == Kind.EXECUTION) M6TerminalSourceComposition.validateExecution(normalized, instance.orElseThrow());
        if (kind == Kind.TERMINATION) M6TerminalSourceComposition.validateTermination(normalized, instance.orElseThrow());
        return new Decoded(binding,normalized);
    }
    public static String journalId(JournalQuery query) {
        var subject=query.subject();return "sway-"+query.kind().name().toLowerCase(java.util.Locale.ROOT)+"-subject-actual4/v1:"
                +subject.actorCharacterId()+":"+subject.targetCharacterId()+":"+subject.schemeInstanceId()+":"+query.afterSequence();
    }
    public static ReadContract<JournalPlane> journalContract(ExactRef source,JournalQuery query) {
        return new ReadContract<>(journalId(query),new OperationKey(query.kind().step()),Optional.empty(),query.kind().permission,
                ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,ReadContract.WireProfile.G2_PRIVATE_QUERY,source,
                (request,requestId)-> {
                    var fields=SwayNativeBindings.args(request.arguments(),Set.of("target_character_id","scheme_instance_id","after_sequence"));var subject=query.subject();
                    require(request.before().frame().identity().player().longValueExact()==subject.actorCharacterId()
                            &&observedCharacter(query.kind(),fields.get("target_character_id"))==subject.targetCharacterId()
                            &&SwayNativeWire.integer(fields,"scheme_instance_id",0,0xffff_fffeL)==subject.schemeInstanceId()
                            &&decimalCursor(fields.get("after_sequence")).equals(query.afterSequence()),"public journal request changed actual native subject/cursor");
                    var extra=StrictJson.object();extra.put("actor_character_id",subject.actorCharacterId());extra.put("target_character_id",subject.targetCharacterId());extra.put("scheme_instance_id",subject.schemeInstanceId());extra.put("after_sequence",query.afterSequence());
                    return SwayNativeBindings.primitive(query.kind().step(),extra);
                },original-> {
                    require(original.contractId().equals(journalId(query)),"public journal exact issued contract changed");
                    // Recheck serialized request, not just the echoed native payload.
                    var args=SwayNativeBindings.args(original.request().arguments(),Set.of("target_character_id","scheme_instance_id","after_sequence"));
                    require(decimalCursor(args.get("after_sequence")).equals(query.afterSequence()),"public journal original cursor changed");
                    require(observedCharacter(query.kind(),args.get("target_character_id"))==query.subject().targetCharacterId()
                            &&SwayNativeWire.integer(args,"scheme_instance_id",0,0xffff_fffeL)==query.subject().schemeInstanceId(),"public journal original subject changed");
                    var decoded=decodeNative(original,query.kind(),new Actors(query.subject().actorCharacterId(),query.subject().targetCharacterId()),Optional.of(query.subject()),Optional.of(query.afterSequence()));
                    return new JournalPlane(query.kind(),decoded.binding(),query.subject(),query.afterSequence(),decoded.normalized());
                });
    }
    public static OpportunityJson.Obj arguments(JournalQuery query) {
        var row=StrictJson.object();row.put("target_character_id",query.subject().targetCharacterId());row.put("scheme_instance_id",query.subject().schemeInstanceId());row.put("after_sequence",query.afterSequence().toString());
        return OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(row)),"typed public Sway journal arguments");
    }
    public static String directId(DirectQuery query) {
        var actors=query.subject().actors();return "sway-"+query.kind().name().toLowerCase(java.util.Locale.ROOT)+"-native-subject-actual4/v1:"+actors.actorCharacterId()+":"+actors.targetCharacterId()+query.subject().instance().map(value->":"+value.schemeInstanceId()).orElse("");
    }
    private static void requireDirectArguments(PlanningReadRequest request,DirectQuery query) {
        var actors=query.subject().actors();var fields=query.kind()==Kind.OPINION?Set.of("target_character_id"):Set.of("target_character_id","scheme_instance_id");var row=SwayNativeBindings.args(request.arguments(),fields);
        long target=observedCharacter(query.kind(),row.get("target_character_id"));
        require(request.before().frame().identity().player().longValueExact()==actors.actorCharacterId()&&target==actors.targetCharacterId(),"direct native read changed actual actor/target");
        query.subject().instance().ifPresent(value->require(SwayNativeWire.integer(row,"scheme_instance_id",0,0xffff_fffeL)==value.schemeInstanceId(),"direct completion changed full native instance"));
    }
    public static ReadContract<DirectPlane> directContract(ExactRef source,DirectQuery query) {
        Objects.requireNonNull(query);return new ReadContract<>(directId(query),new OperationKey(query.kind().step()),Optional.empty(),query.kind().permission,
                ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,ReadContract.WireProfile.G2_PRIVATE_QUERY,source,(request,requestId)->{
                    requireDirectArguments(request,query);var actors=query.subject().actors();var extra=StrictJson.object();extra.put("actor_character_id",actors.actorCharacterId());extra.put("target_character_id",actors.targetCharacterId());
                    query.subject().instance().ifPresent(value->extra.put("scheme_instance_id",value.schemeInstanceId()));return SwayNativeBindings.primitive(query.kind().step(),extra);
                },original->{require(original.contractId().equals(directId(query)),"direct native read changed issued exact contract");requireDirectArguments(original.request(),query);
                    var decoded=decodeNative(original,query.kind(),query.subject().actors(),query.subject().instance(),Optional.empty());return new DirectPlane(query,decoded.binding(),decoded.normalized());});
    }
    public static OpportunityJson.Obj arguments(DirectQuery query) {
        var row=StrictJson.object();row.put("target_character_id",query.subject().actors().targetCharacterId());query.subject().instance().ifPresent(value->row.put("scheme_instance_id",value.schemeInstanceId()));
        return OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(row)),"typed direct Sway native query arguments");
    }
    private static void pair(ObjectNode row,Actors identity) {
        require(NativeCharacterId.fromJson(row.get("actor_character_id")).value()==identity.actorCharacterId()&&NativeCharacterId.fromJson(row.get("target_character_id")).value()==identity.targetCharacterId(),"native opinion actor/target differs");
    }
    private static boolean journal(Kind kind) {return kind==Kind.EXECUTION||kind==Kind.TERMINATION;}
    /** Internal/public JSON cursor representation is always a canonical decimal string; native packet numbers stay exact BigInteger. */
    public static BigInteger decimalCursor(JsonNode value) {
        require(value!=null&&value.isTextual(),"journal cursor must be a canonical decimal uint64 string");
        return new BigInteger(new org.xar.ck3.control.contracts.CrossJsDecimalUInt64(value.textValue()).decimal());
    }
    public static OpportunityJson.Obj arguments(Query query) {
        ObjectNode row=StrictJson.object();row.put("target_character_id",query.identity().targetCharacterId());
        if(query.kind()!=Kind.OPINION)row.put("scheme_instance_id",query.identity().schemeInstanceId());
        query.afterSequence().ifPresent(value->row.put("after_sequence",value.toString()));
        return OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(row)),"typed Sway observation arguments");
    }
    private static void completion(ObjectNode row, SwayNativeWire.Binding binding, NativeSubject identity) {
        Set<String> fields = new HashSet<>(COMPLETION); if (row.has("native_can_continue_observed") || row.has("native_can_continue")) fields.addAll(Set.of("native_can_continue_observed", "native_can_continue"));
        StrictJson.object(row, fields); SwayNativeWire.equals(row, "schema", "xar.ck3.sway_completion.v1"); SwayNativeWire.integer(row, "schema_version", 1, 1); build(row);
        SwayNativeWire.equals(row, "adapter_id", "ck3-1.20.0.4-msvc-x64");
        require(SwayNativeWire.wide(row, "snapshot_revision", 1).equals(binding.revision()) && SwayNativeWire.signed(row, "date_raw") == binding.date(), "Sway native payload crossed complete actor/date/revision frame");
        pair(row, identity, Kind.COMPLETION);
        require(SwayNativeWire.integer(row, "scheme_instance_generation", 0, 255) == identity.schemeInstanceGeneration(), "current instance generation differs");
        for (String field : Set.of("private_build", "read_only", "advertised", "available", "instance_source_observed", "instance_present", "storage_slot_reused", "exact_instance_join_ready", "owner_matches_actor", "owner_cleared", "native_status_observed", "native_terminal_state_observed", "native_success_chance_observed", "terminal_cause_observed")) SwayNativeWire.bool(row, field);
        require(SwayNativeWire.bool(row, "private_build") && SwayNativeWire.bool(row, "read_only") && !SwayNativeWire.bool(row, "advertised"), "completion private flags");
        for (String field : Set.of("unavailable_reason", "native_source_kind", "current_instance_retention", "native_status_key", "native_success_chance_unit", "terminal_cause")) SwayNativeWire.string(row, field);
        nullableInteger(row, "native_owner_raw", 0, 0xffff_ffffL); nullableInteger(row, "native_status_raw", Integer.MIN_VALUE, Integer.MAX_VALUE);
        if (!row.get("native_success_chance_raw").isNull()) StrictJson.integer(row.get("native_success_chance_raw"), BigInteger.ONE.shiftLeft(63).negate(), BigInteger.ONE.shiftLeft(63).subtract(BigInteger.ONE));
        SwayNativeWire.integer(row, "native_success_chance_scale", 100000, 100000); SwayNativeWire.equals(row, "native_success_chance_unit", "percent");
        if (row.has("native_can_continue_observed")) {
            if (SwayNativeWire.bool(row, "native_can_continue_observed")) SwayNativeWire.bool(row, "native_can_continue"); else require(row.get("native_can_continue").isNull(), "unobserved continuation remains null");
        }
    }
    private static void opinion(ObjectNode row, SwayNativeWire.Binding binding, Actors identity) {
        StrictJson.object(row, OPINION); SwayNativeWire.equals(row, "schema", "xar.ck3.sway-outcome-opinion-v1"); SwayNativeWire.equals(row, "build", SwayNativeWire.BUILD);
        require(SwayNativeWire.wide(row, "snapshot_revision", 1).equals(binding.revision()) && SwayNativeWire.signed(row, "date_raw") == binding.date(), "Sway native payload crossed complete actor/date/revision frame");
        pair(row,identity);
        boolean available = SwayNativeWire.bool(row, "available"); SwayNativeWire.string(row, "unavailable_reason");
        require(!SwayNativeWire.bool(row, "instance_terminal_outcome_observed") && !SwayNativeWire.bool(row, "cancel_outcome_observed"), "named material does not assign terminal/cancel");
        if (available) SwayNativeWire.integer(row, "target_opinion_of_actor", Integer.MIN_VALUE, Integer.MAX_VALUE); else require(row.get("target_opinion_of_actor").isNull(), "unavailable total opinion remains null");
        for (String key : Set.of("scheme_sway_opinion", "sway_blocker_opinion")) {
            JsonNode value = StrictJson.object(row.get(key), Set.of("observed", "present", "value")); boolean observed = SwayNativeWire.bool(value, "observed"), present = SwayNativeWire.bool(value, "present");
            require(!available || observed, "available native named read is complete"); require(!present || observed, "present named value observed");
            if (present) SwayNativeWire.integer(value, "value", Integer.MIN_VALUE, Integer.MAX_VALUE); else require(value.get("value").isNull(), "absent named value remains null");
        }
    }
    private static void build(JsonNode row) { SwayNativeWire.equals(row, "build_version", SwayNativeWire.BUILD); require(SwayNativeWire.EXE.equalsIgnoreCase(SwayNativeWire.string(row, "executable_sha256")), "M6 query executable differs"); }
    private static void pair(JsonNode row, Identity identity) {
        pair(row,identity.nativeSubject());
    }
    private static long observedCharacter(Kind kind,JsonNode value) {
        return kind==Kind.EXECUTION?StrictJson.integer(value,1,Integer.MAX_VALUE):NativeCharacterId.fromJson(value).value();
    }
    private static void pair(JsonNode row,NativeSubject identity,Kind kind) {
        require(observedCharacter(kind,row.get("actor_character_id"))==identity.actorCharacterId()
                &&observedCharacter(kind,row.get("target_character_id"))==identity.targetCharacterId()
                &&SwayNativeWire.integer(row,"scheme_instance_id",0,0xffff_fffeL)==identity.schemeInstanceId(),"M6 query original full identities differ");
    }
    private static void pair(JsonNode row,NativeSubject identity) {
        require(SwayNativeWire.integer(row, "actor_character_id", 1, Integer.MAX_VALUE) == identity.actorCharacterId() && SwayNativeWire.integer(row, "target_character_id", 1, Integer.MAX_VALUE) == identity.targetCharacterId()
                && SwayNativeWire.integer(row, "scheme_instance_id", 0, 0xffff_fffeL) == identity.schemeInstanceId(), "M6 query original full identities differ");
    }
    private static void nullableInteger(JsonNode row, String field, long min, long max) { if (!row.get(field).isNull()) SwayNativeWire.integer(row, field, min, max); }

    public static final String INVALIDATION_STEP="query-sway-completion-invalidation-reason-v1-private";
    public static final String INVALIDATION_PERMISSION="allow_private_active_scheme_sway_completion_invalidation_reason_query";
    private static final Set<String> NOTIFICATION_OUTCOMES=Set.of("message_enqueue_observed","render_observed","material_effect_observed","native_end_cause_observed","native_terminal_state_observed");
    private static final Set<String> NOTIFICATION_CONTEXT=Set.of("schema","available","unavailable_reason","read_only","observer_attached","actor_character_id","target_character_id","scheme_instance_id","after_sequence","earliest_sequence","latest_sequence","retention_gap","session_records_only","message_enqueue_observed","render_observed","material_effect_observed","native_end_cause_observed","native_terminal_state_observed","records");
    private static final Set<String> NOTIFICATION_RECORD=Set.of("sequence","source_branch","authored_command","authored_title","authored_reason_key","date_raw","actor_character_id","target_character_id","scheme_instance_id","scheme_instance_generation","root_scope_kind","scheme_scope_kind","selected_notification_branch_observed","exact_scope_join_ready","message_enqueue_observed","render_observed","material_effect_observed","native_end_cause_observed","native_terminal_state_observed");
    /** Actionless full native identity. These selected notification records never become an M6 causal proof. */
    public record InvalidationQuery(NativeSubject subject,BigInteger afterSequence) {
        public InvalidationQuery {Objects.requireNonNull(subject);SwayNativeWire.currentCharacter(subject.actorCharacterId());SwayNativeWire.currentCharacter(subject.targetCharacterId());new Actors(subject.actorCharacterId(),subject.targetCharacterId());SwayNativeWire.instance(subject.schemeInstanceId(),subject.schemeInstanceGeneration());SwayNativeWire.u64(afterSequence,0);}
    }
    public record InvalidationPlane(InvalidationQuery query,PlanningReadReceipt original,ProjectionJson normalized) {
        public InvalidationPlane {Objects.requireNonNull(query);Objects.requireNonNull(original);Objects.requireNonNull(normalized);}
    }
    /** Original Python accepts precisely these version/SHA pairs. This is DATA selection, never native admission. */
    private static String invalidationExecutable(String version) {
        return switch(version) {
            case "1.20.0.2"->"AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D";
            case "1.20.0.3"->"94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6";
            default->throw new IllegalArgumentException("Original Sway invalidation notification query has no qualified implementation for this exact build");
        };
    }
    public static String invalidationId(InvalidationQuery query) {
        var subject=query.subject();return "sway-notification-input-native-subject/v1:"+subject.actorCharacterId()+":"+subject.targetCharacterId()+":"+subject.schemeInstanceId()+":"+query.afterSequence();
    }
    public static OpportunityJson.Obj arguments(InvalidationQuery query) {
        var row=StrictJson.object();row.put("target_character_id",query.subject().targetCharacterId());row.put("scheme_instance_id",query.subject().schemeInstanceId());row.put("after_sequence",query.afterSequence().toString());
        return OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(row)),"typed selected Sway notification query");
    }
    private static void requireInvalidationArguments(PlanningReadRequest request,InvalidationQuery query) {
        invalidationExecutable(request.source().exactBuild());
        var row=SwayNativeBindings.args(request.arguments(),Set.of("target_character_id","scheme_instance_id","after_sequence"));
        require(request.before().frame().identity().player().longValueExact()==query.subject().actorCharacterId()
                &&SwayNativeWire.integer(row,"target_character_id",1,Integer.MAX_VALUE)==query.subject().targetCharacterId()
                &&SwayNativeWire.integer(row,"scheme_instance_id",0,0xffff_fffeL)==query.subject().schemeInstanceId()
                &&decimalCursor(row.get("after_sequence")).equals(query.afterSequence()),"selected notification request changed original actor/target/fullID/cursor");
    }
    public static ReadContract<InvalidationPlane> invalidationContract(ExactRef source,InvalidationQuery query,boolean explicitlyEnabled) {
        java.util.function.Function<PlanningReadReceipt,InvalidationPlane> decoder=original->decodeInvalidation(original,query);
        return new ReadContract<>(invalidationId(query),new OperationKey(INVALIDATION_STEP),Optional.empty(),INVALIDATION_PERMISSION,
                ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,ReadContract.WireProfile.G2_PRIVATE_QUERY,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,source,
                (request,id)->{require(explicitlyEnabled,"selected Sway invalidation private observation is explicitly disabled");requireInvalidationArguments(request,query);
                    var extra=StrictJson.object();extra.put("actor_character_id",query.subject().actorCharacterId());extra.put("target_character_id",query.subject().targetCharacterId());extra.put("scheme_instance_id",query.subject().schemeInstanceId());extra.put("after_sequence",query.afterSequence());return SwayNativeBindings.primitive(INVALIDATION_STEP,extra);},
                decoder,decoder);
    }
    private static InvalidationPlane decodeInvalidation(PlanningReadReceipt original,InvalidationQuery query) {
        var request=original.request();requireInvalidationArguments(request,query);
        require(original.contractId().equals(invalidationId(query))&&request.operation().value().equals(INVALIDATION_STEP)
                &&original.original().nativeOk()&&original.original().originalResultToken().isPresent(),"selected notification receipt is not its original exact contract/ACK");
        for(var guard:java.util.List.of(original.before(),original.after())) {
            var binding=guard.binding();require(binding.observed().equals(request.before())&&binding.source().equals(request.source())
                    &&binding.sessionId().equals(request.sessionId())&&binding.operation().equals(request.operation())
                    &&guard.paused()&&guard.mapReady()&&guard.playerAlive(),"selected notification lost the full living paused source guard");
        }
        require(original.before().originalBindingSha256().equals(original.after().originalBindingSha256())
                &&original.before().binding().connectionGeneration().equals(original.after().binding().connectionGeneration())
                &&original.before().binding().authorityId().equals(original.after().binding().authorityId()),"selected notification crossed native custody");
        var packet=StrictJson.object(StrictJson.parse(original.original().originalFrame().bytes(),SwayNativeWire.MAX),Set.of("type","protocol_version","request_id","ok","result"));
        SwayNativeWire.equals(packet,"type","command_result");SwayNativeWire.equals(packet,"request_id",original.requestId());SwayNativeWire.integer(packet,"protocol_version",1,1);require(SwayNativeWire.bool(packet,"ok"),"selected notification native failure");
        var result=StrictJson.object(packet.get("result"),Set.of("step","accepted","status","private_build","read_only","advertised","snapshot_revision","date_raw","build_version","executable_sha256","sway_completion_invalidation_reason","backend_id"));
        require(result.equals(StrictJson.parse(original.original().originalResultToken().orElseThrow().bytes(),SwayNativeWire.MAX)),"selected notification raw frame/result token differ");
        SwayNativeWire.equals(result,"step",INVALIDATION_STEP);SwayNativeWire.equals(result,"backend_id","native-headless");
        require(SwayNativeWire.bool(result,"accepted")&&SwayNativeWire.bool(result,"private_build")&&SwayNativeWire.bool(result,"read_only")&&!SwayNativeWire.bool(result,"advertised"),"selected notification private flags differ");
        String version=request.source().exactBuild(),exe=invalidationExecutable(version);SwayNativeWire.equals(result,"build_version",version);
        require(exe.equalsIgnoreCase(SwayNativeWire.string(result,"executable_sha256")),"selected notification exact source executable differs");
        require(SwayNativeWire.wide(result,"snapshot_revision",1).equals(request.before().frame().identity().nativeRevision())
                &&SwayNativeWire.signed(result,"date_raw")==request.before().frame().identity().dateRaw().intValueExact(),"selected notification crossed source native frame");
        var body=StrictJson.object(result.get("sway_completion_invalidation_reason"),NOTIFICATION_CONTEXT).deepCopy();
        SwayNativeWire.equals(body,"schema","xar.ck3.sway-invalidation-notification-source.v1");
        boolean available=SwayNativeWire.bool(body,"available");SwayNativeWire.equals(result,"status",available?"available":"unavailable");
        SwayNativeWire.string(body,"unavailable_reason");SwayNativeWire.bool(body,"observer_attached");SwayNativeWire.bool(body,"retention_gap");
        require(SwayNativeWire.bool(body,"read_only")&&SwayNativeWire.bool(body,"session_records_only"),"notification inputs retain read-only current-session scope");
        for(String field:NOTIFICATION_OUTCOMES)require(!SwayNativeWire.bool(body,field),"selected notification inputs do not prove enqueue/render/material/end cause or terminal");
        pair(body,query.subject());require(SwayNativeWire.wide(body,"after_sequence",0).equals(query.afterSequence()),"selected notification echoed another original cursor");
        var earliest=SwayNativeWire.wide(body,"earliest_sequence",0);var latest=SwayNativeWire.wide(body,"latest_sequence",0);
        require((earliest.signum()==0)==(latest.signum()==0)&&earliest.compareTo(latest)<=0,"selected notification native retention bounds");
        require(body.get("records").isArray()&&body.get("records").size()<=4096,"bounded selected notification records");
        BigInteger previous=query.afterSequence();
        for(var value:body.get("records")) {
            var row=StrictJson.object(value,NOTIFICATION_RECORD);var sequence=SwayNativeWire.wide(row,"sequence",1);
            require(sequence.compareTo(previous)>0&&sequence.compareTo(earliest)>=0&&sequence.compareTo(latest)<=0,"selected notification records must follow the original cursor and retained bounds");previous=sequence;
            String reason=switch(SwayNativeWire.string(row,"source_branch")) {
                case "target_dead_notification_source"->"sway_invalidated_dead";
                case "out_of_range_notification_source"->"scheme_target_not_in_diplomatic_range";
                case "opaque_existing_stock_notification_source"->"sway_invalidated_war";
                default->throw new IllegalArgumentException("Unknown original selected notification branch");
            };
            SwayNativeWire.equals(row,"authored_reason_key",reason);SwayNativeWire.equals(row,"authored_command","send_interface_toast");SwayNativeWire.equals(row,"authored_title","sway_invalidated_title");
            SwayNativeWire.signed(row,"date_raw");pair(row,query.subject());require(SwayNativeWire.integer(row,"scheme_instance_generation",0,255)==query.subject().schemeInstanceGeneration(),"selected notification fullID generation differs");
            SwayNativeWire.integer(row,"root_scope_kind",4,4);SwayNativeWire.integer(row,"scheme_scope_kind",9,9);
            require(SwayNativeWire.bool(row,"selected_notification_branch_observed")&&SwayNativeWire.bool(row,"exact_scope_join_ready"),"selected notification source lacks its original exact scope join");
            for(String field:NOTIFICATION_OUTCOMES)require(!SwayNativeWire.bool(row,field),"selected notification record cannot assign a terminal or universal cause");
        }
        body.put("exact_ck3_build",version);body.put("exe_sha256",exe);
        body.put("queried_snapshot_id",request.before().frame().snapshotId());body.put("queried_revision",request.before().frame().revision());body.put("queried_native_revision",request.before().frame().identity().nativeRevision());
        for(String field:java.util.List.of("backend_id","status","snapshot_revision","date_raw","build_version","executable_sha256","private_build","advertised"))body.set(field,result.get(field));
        return new InvalidationPlane(query,original,SwayNativeWire.json(body));
    }
}
