package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.military.projectedcontact.ProjectedContactCodec;
import org.xar.ck3.control.military.projectedcontact.ProjectedContactPolicy;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import org.xar.ck3.control.wave2.military.actualcontact.ActualContactCodec;
import org.xar.ck3.control.wave2.military.actualcontact.ActualContactModel;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** Shared immutable Contact data. Construction and wire decode grant no Native or writer authority. */
public record ContactScopeObservation(ContactScopeObservation.Query query,ContactScopeObservation.Scope scope,BigInteger querySequence,Optional<String> backendId,
            ProjectedContactPolicy.Capture capture) {
    public static final String PROJECTED="game.command.query-projected-contact-scope-v1-N";
    public static final String ACTUAL="game.command.query-actual-contact-scope-v1-N";
    public sealed interface Query permits Projected,Actual {
        int subject(); int target(); String step(); String capability();
    }
    public record Projected(ProjectedContactPolicy.QueryKey key) implements Query {
        public Projected { Objects.requireNonNull(key); }
        @Override public int subject(){return key.subjectArmyId();}
        @Override public int target(){return key.targetProvinceId();}
        @Override public String step(){return key.step();}
        @Override public String capability(){return PROJECTED;}
    }
    public record Actual(ActualContactModel.Query key) implements Query {
        public Actual { Objects.requireNonNull(key); }
        @Override public int subject(){return key.subjectArmyId();}
        @Override public int target(){return key.targetProvinceId();}
        @Override public String step(){return key.step();}
        @Override public String capability(){return ACTUAL;}
    }
    public sealed interface Scope permits ProjectedScope,ActualScope { ObjectNode nativeJson(); }
    public record ProjectedScope(ProjectedContactPolicy.Scope value) implements Scope {
        public ProjectedScope { Objects.requireNonNull(value); }
        @Override public ObjectNode nativeJson(){return ProjectedContactCodec.encodeScope(value);}
    }
    public record ActualScope(ActualContactModel.Scope value) implements Scope {
        public ActualScope { Objects.requireNonNull(value); }
        @Override public ObjectNode nativeJson(){return ActualContactCodec.encodeScope(value);}
    }
        public ContactScopeObservation {
            Objects.requireNonNull(query);Objects.requireNonNull(scope);UInt64.positive(querySequence);Objects.requireNonNull(capture);
            Objects.requireNonNull(backendId);
            if(query instanceof Projected) require(backendId.isPresent()&&!backendId.get().isBlank(),"projected backend identity absent");
            else require(backendId.isEmpty(),"actual backend identity must be absent");
            if(query instanceof Projected p) {
                require(scope instanceof ProjectedScope,"projected read has wrong typed body");
                var value=((ProjectedScope)scope).value();
                require(value.subjectArmyId()==p.subject()&&value.targetProvinceId()==p.target()
                        &&value.incomingEntryProvinceId()==p.key().incomingEntryProvinceId()&&value.snapshotRevision().equals(capture.nativeRevision()),"projected observation binding differs");
            }else {
                require(scope instanceof ActualScope,"actual read has wrong typed body");
                var value=((ActualScope)scope).value();
                require(value.subjectArmyId()==query.subject()&&value.targetProvinceId()==query.target()
                        &&value.snapshotRevision().equals(capture.nativeRevision()),"actual observation binding differs");
            }
        }
        public Obj normalizedResult() {
            ObjectNode result=empty().put("step",query.step()).put("accepted",true).put("status","available")
                    .put("query_sequence",querySequence).put("snapshot_revision",capture.nativeRevision());
            if(backendId.isPresent()) result.put("backend_id",backendId.get());
            result.set(query instanceof Projected?"projected_contact_scope":"actual_contact_scope",scope.nativeJson());
            result.put("queried_snapshot_id",capture.snapshotId()).put("queried_revision",capture.revision())
                    .put("queried_native_revision",capture.nativeRevision()).put("queried_connection_generation",capture.connectionGeneration())
                    .put("queried_episode_run_id",capture.episodeRunId());
            return DriverJson.object(bytes(result),DriverJson.MAX_NATIVE_BYTES);
        }
    /** Sole complete normalized history DATA decoder. No receipt, session, qualification or freshness is created here. */
    public static ContactScopeObservation decodeHistoryResult(Obj normalized,int expectedDateRaw) {
        ObjectNode n=object(OpportunityJson.toNode(Objects.requireNonNull(normalized)));
        Query query=parseQuery(text(get(n,"step")));
        String payload=query instanceof Projected?"projected_contact_scope":"actual_contact_scope";
        if(query instanceof Projected) {
            closed(n,"step","accepted","status","query_sequence","snapshot_revision",payload,"backend_id",
                    "queried_snapshot_id","queried_revision","queried_native_revision","queried_connection_generation","queried_episode_run_id");
        } else {
            closed(n,"step","accepted","status","query_sequence","snapshot_revision",payload,
                    "queried_snapshot_id","queried_revision","queried_native_revision","queried_connection_generation","queried_episode_run_id");
        }
        yes(n.get("accepted"));equal(n.get("status"),"available");BigInteger revision=positive(n.get("snapshot_revision")).value();
        equal(n.get("queried_native_revision"),revision);
        var capture=new ProjectedContactPolicy.Capture(text(n.get("queried_snapshot_id")),u64(n.get("queried_revision")).value(),revision,
                positive(n.get("queried_connection_generation")).value(),text(n.get("queried_episode_run_id")));
        Scope scope;
        if(query instanceof Projected) {
            var value=ProjectedContactCodec.decodeScope(n.get(payload));
            require(value.dateRaw()==expectedDateRaw,"projected history date differs from original frame");scope=new ProjectedScope(value);
        }else {
            var value=ActualContactCodec.decodeScope(n.get(payload));
            require(value.dateRaw()==expectedDateRaw,"actual history date differs from original frame");scope=new ActualScope(value);
        }
        Optional<String> decodedBackend = query instanceof Projected ? Optional.of(text(n.get("backend_id"))) : Optional.empty();
        var decoded=new ContactScopeObservation(query,scope,positive(n.get("query_sequence")).value(),decodedBackend,capture);
        require(decoded.normalizedResult().equals(normalized),"contact complete normalized history roundtrip differs");return decoded;
    }
    public static Query parseQuery(String step) {
        Optional<ProjectedContactPolicy.QueryKey> projected=ProjectedContactPolicy.parseStep(step);
        if(projected.isPresent())return new Projected(projected.orElseThrow());
        return new Actual(ActualContactModel.parseStep(step).orElseThrow(()->new IllegalArgumentException("unknown contact query step")));
    }
}
