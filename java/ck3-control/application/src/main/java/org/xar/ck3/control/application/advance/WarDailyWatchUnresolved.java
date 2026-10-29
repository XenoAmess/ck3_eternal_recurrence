package org.xar.ck3.control.application.advance;

import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.ExactRef;

/** Durable failure material from the original canonical parent and children. It never settles an UNKNOWN action. */
public final class WarDailyWatchUnresolved {
    public static final String SCHEMA = "xar.ck3.java-war-daily-watch-unresolved/v1";
    private static final Set<String> FIELDS = Set.of("schema","action_id","action_body_sha256","selected_step","never_replay","saved_day_credit",
            "context","starting_native_frame","children","original_error_type","original_error","native_request_id");
    private WarDailyWatchUnresolved() { }
    public static ExactRef preserve(ActionCommand parent, WarDailyWatch.Context context, AdvanceObservationPort.Frame starting,
            RuntimeException original, ActionSnapshotReader canonical, ActionPorts.OutcomeArchive archive) {
        require(context.starting().equals(parent.before()) && starting.identity().equals(parent.before()), "watch failure crossed the immutable original entry");
        return canonical.withFrozen(lease -> {
            ActionReceipt current = lease.find(parent.actionId()).orElseThrow(() -> new IllegalArgumentException("actual durable watch parent is absent"));
            require(current.command().equals(parent) && current.bodySha256().equals(ActionCodec.bodySha256(parent)), "watch failure parent differs from canonical intent");
            CompositeExecution execution = ActionTransitions.composite(current.state()).orElseThrow(() -> new IllegalArgumentException("actual watch composite custody is absent"));
            List<Value> children = new ArrayList<>(); Optional<String> requestId = Optional.empty();
            for (CompositeExecution.Child retained : execution.children()) {
                ActionReceipt child = lease.find(retained.actionId()).orElseThrow();
                require(child.bodySha256().equals(retained.bodySha256()) && child.command().source().equals(parent.source())
                        && child.command().sessionId().equals(parent.sessionId()), "watch failure child changed its original body/source/session");
                children.add(reference(archive.preserveReceipt(child)));
                Optional<ActionState.Attempt> attempt = ActionTransitions.attempt(child.state());
                if (attempt.isPresent()) requestId = Optional.of(attempt.orElseThrow().requestId());
            }
            Obj body = new Obj(Map.ofEntries(Map.entry("schema",new Text(SCHEMA)),Map.entry("action_id",new Text(parent.actionId())),
                    Map.entry("action_body_sha256",new Text(current.bodySha256())),Map.entry("selected_step",new Text(parent.operation().value())),
                    Map.entry("never_replay",new Bool(true)),Map.entry("saved_day_credit",new IntegerValue(BigInteger.ZERO)),
                    Map.entry("context",WarDailyWatch.encode(context)),Map.entry("starting_native_frame",reference(starting.originalEvidence())),
                    Map.entry("children",new Arr(children)),Map.entry("original_error_type",new Text(original.getClass().getName())),
                    Map.entry("original_error",new Text(java.util.Objects.toString(original.getMessage(),"unavailable"))),
                    Map.entry("native_request_id",requestId.<Value>map(Text::new).orElse(Nil.INSTANCE))));
            ExactRef result = archive.preserveMaterial(new RawJson(DriverJson.encode(body))); lease.assertCurrent(); return result;
        });
    }
    /** Public error consumers may expose this exact body; a reason string never selects this schema. */
    public static Optional<RawJson> read(ActionReceipt receipt, ActionPorts.OutcomeArchive archive) {
        if (!LifeAdvanceComposite.accepts(receipt.command().operation().value())) return Optional.empty();
        if (!(receipt.state() instanceof ActionState.CompositeUnknown unknown) || AdvancePlan.decode(receipt.command()).dailyWatch().isEmpty()) return Optional.empty();
        Optional<RawJson> result = Optional.empty();
        for (ExactRef ref : unknown.evidence()) {
            RawJson material; Obj body;
            try { material = archive.loadMaterial(ref); body = DriverJson.object(material.bytes(),RawJson.MAXIMUM_BYTES); }
            catch (RuntimeException nonMaterialOrNativePacket) { continue; }
            if (!new Text(SCHEMA).equals(body.get("schema"))) continue;
            require(result.isEmpty() && body.members().keySet().equals(FIELDS) && new Text(receipt.command().actionId()).equals(body.get("action_id"))
                    && new Text(receipt.bodySha256()).equals(body.get("action_body_sha256")) && new Text(receipt.command().operation().value()).equals(body.get("selected_step"))
                    && new Bool(true).equals(body.get("never_replay")) && new IntegerValue(BigInteger.ZERO).equals(body.get("saved_day_credit")), "watch failure basis is duplicated, malformed or crossed its durable parent");
            require(WarDailyWatch.decode(object(body.get("context"),"context")).equals(AdvancePlan.decode(receipt.command()).dailyWatch().orElseThrow()), "watch failure context changed");
            ExactRef starting = ExactRef.fromJson(toNode(body.get("starting_native_frame")));
            require(starting.bytes() > 0 && unknown.evidence().contains(starting), "watch failure lost its retained original entry packet");
            List<Value> refs = array(body.get("children"),"children"); require(refs.size() == unknown.execution().children().size(),"watch failure omitted an original child");
            Optional<String> requestId = Optional.empty();
            for (int index=0;index<refs.size();index++) {
                ActionReceipt child = archive.loadReceipt(ExactRef.fromJson(toNode(refs.get(index)))); var retained=unknown.execution().children().get(index);
                require(child.command().actionId().equals(retained.actionId()) && child.bodySha256().equals(retained.bodySha256())
                        && child.bodySha256().equals(ActionCodec.bodySha256(child.command())) && child.command().source().equals(receipt.command().source())
                        && child.command().sessionId().equals(receipt.command().sessionId()),"watch failure original child binding differs");
                Optional<ActionState.Attempt> attempt = ActionTransitions.attempt(child.state());
                if (attempt.isPresent()) requestId = Optional.of(attempt.orElseThrow().requestId());
            }
            text(body.get("original_error_type"),"original_error_type"); text(body.get("original_error"),"original_error");
            require(java.util.Objects.equals(body.get("native_request_id"),requestId.<Value>map(Text::new).orElse(Nil.INSTANCE)),
                    "watch failure native request ID differs from the original durable child attempt");
            result = Optional.of(material);
        }
        return result;
    }
    private static Value reference(ExactRef ref) { return org.xar.ck3.control.planning.opportunity.OpportunityJson.parse(org.xar.ck3.control.contracts.StrictJson.canonical(ref.toJson())); }
}
