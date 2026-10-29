package org.xar.ck3.control.application.lifecycle;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.util.HashMap;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.StrictJson;

/** One branch installed in the existing writer router. It neither opens a ledger nor submits a Game command. */
public final class LifecycleContinuityAuthority implements WriterContracts.TransitionAuthority {
    public static final String STATE_FIELD="java_episode_lifecycle";
    @FunctionalInterface interface CurrentGuard { String require(WriterContracts.Head actualHead,LifecycleChild child) throws IOException; }
    private final Map<String,LifecycleChild> retained=new HashMap<>();
    private CurrentGuard guard;
    synchronized void bind(CurrentGuard actual){if(guard!=null)throw new IllegalStateException("lifecycle authority already bound");guard=Objects.requireNonNull(actual);}
    synchronized void register(LifecycleChild child){StrictJson.require(retained.size()<16384,"finite lifecycle child registry");StrictJson.require(retained.putIfAbsent(child.token(),child)==null,"lifecycle token reuse");}
    private synchronized LifecycleChild actual(WriterContracts.Request request) {
        StrictJson.require(request.kind().equals(LifecycleChild.KIND),"wrong lifecycle event kind");
        String token=LifecycleJson.text(request.detailsObject().get("token"));LifecycleChild child=retained.get(token);
        StrictJson.require(child!=null && child.request().identity().equals(request.identity()),"no exact retained actual lifecycle producer; JSON cannot grant transition");return child;
    }
    @Override public String revalidate(ContinuityState predecessor,WriterContracts.Request request)throws IOException {
        throw new IOException("lifecycle qualification requires the actual original-writer Head, not a caller state object");
    }
    @Override public String revalidate(WriterContracts.Head actualHead,WriterContracts.Request request)throws IOException {
        ContinuityState predecessor=actualHead.state();
        LifecycleChild child=actual(request);StrictJson.require(predecessor.machineId().equals(child.parent().origin().machineId()),"lifecycle writer machine differs");
        StrictJson.require(child.parent().origin() instanceof org.xar.ck3.control.application.action.CommandOrigin.LifecycleTerminal,"canonical lifecycle child requires its actual terminal-origin parent");
        if(guard==null)throw new IOException("actual lifecycle source guard not installed");String sourceDigest=guard.require(actualHead,child);WriterContracts.requireDigest(sourceDigest);
        ObjectNode registry=registry(predecessor);
        // This registry retains lifecycle history. Ordinary committed Driver publications may
        // legitimately follow its last stamp; the source guard above checks the actual repository.
        if(registry.has("transitions")) {
            ObjectNode transitions=LifecycleJson.object(registry.get("transitions"));
            if(transitions.has(child.parentActionId())) {
                ObjectNode prior=LifecycleJson.object(transitions.get(child.parentActionId()));
                ObjectNode before=LifecycleJson.object(prior.get("driver_snapshot"));
                StrictJson.require(LifecycleChild.Phase.NEXT_EPISODE_ENTERED.name().equals(LifecycleJson.text(prior.get("phase")))
                        &&child.phase()==LifecycleChild.Phase.NEXT_EPISODE_COMMITTED
                        &&LifecycleJson.text(prior.get("parent_body_sha256")).equals(LifecycleJson.text(request.detailsObject().get("parent_body_sha256")))
                        &&LifecycleJson.text(before.get("before_sha256")).equals(child.expected().driverSha256())
                        &&LifecycleJson.integer(before.get("expected_version"),java.math.BigInteger.ZERO).longValueExact()==child.expected().driverVersion(),
                        "original entered lifecycle predecessor/body differs or lifecycle was already settled");
            }
        }
        ObjectNode checked=LifecycleJson.row();checked.put("actual_head_sha256",actualHead.digest());checked.put("actual_source_sha256",sourceDigest);
        checked.put("request_identity",request.identity());return ContinuityJson.digest(checked);
    }
    @Override public ContinuityState reduce(ContinuityState predecessor,WriterContracts.Request request) {
        LifecycleChild child=actual(request);return project(predecessor,request,child.replacement());
    }
    /** Sole pure projection, shared by genuine warm reduction and original canonical cold replay. */
    static ContinuityState project(ContinuityState predecessor,WriterContracts.Request request,
            org.xar.ck3.control.application.checkpoint.DriverStateSnapshot.Complete replacement) {
        StrictJson.require(request.kind().equals(LifecycleChild.KIND),"wrong lifecycle projection kind");
        ObjectNode row=request.detailsObject();String parent=LifecycleJson.text(row.get("parent_action_id"));
        var phase=LifecycleChild.Phase.valueOf(LifecycleJson.text(row.get("phase")));
        ObjectNode stamp=LifecycleJson.object(row.get("driver_snapshot"));
        StrictJson.require(LifecycleJson.text(stamp.get("after_sha256")).equals(LifecycleJson.sha(replacement.encode())),
                "actual adopted Driver bytes differ from canonical lifecycle request");
        ObjectNode next=predecessor.toJson();ObjectNode registry=registry(predecessor);
        ObjectNode transitions=registry.has("transitions")?LifecycleJson.object(registry.get("transitions")):LifecycleJson.row();
        ObjectNode prior=transitions.has(parent)?LifecycleJson.object(transitions.get(parent)):null;
        if(prior!=null)StrictJson.require(LifecycleJson.text(prior.get("phase")).equals(LifecycleChild.Phase.NEXT_EPISODE_ENTERED.name())
                &&phase==LifecycleChild.Phase.NEXT_EPISODE_COMMITTED,"lifecycle transition already settled; UNKNOWN is not replayable");
        else StrictJson.require(phase!=LifecycleChild.Phase.NEXT_EPISODE_COMMITTED,"replacement requires its actual durable entered predecessor");
        transitions.set(parent,row);registry.set("transitions",transitions);
        registry.put("driver_sha256",LifecycleJson.sha(replacement.encode()));
        long version=LifecycleJson.integer(stamp.get("expected_version"),java.math.BigInteger.ZERO).longValueExact();
        registry.put("driver_version",phase==LifecycleChild.Phase.NEXT_EPISODE_ENTERED?version:Math.addExact(version,1));
        registry.put("episode_run_id",replacement.session().episodeRunId());registry.put("actor_id",replacement.session().actorId());
        next.set(STATE_FIELD,registry);return ContinuityState.fromJson(next,predecessor.machineId());
    }
    private static ObjectNode registry(ContinuityState state) {
        ObjectNode row=state.toJson();return row.has(STATE_FIELD)?LifecycleJson.object(row.get(STATE_FIELD)).deepCopy():LifecycleJson.row();
    }
}
