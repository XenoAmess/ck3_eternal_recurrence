package org.xar.ck3.control.application.advance;

import static org.xar.ck3.control.contracts.StrictJson.require;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Exact after-frame locator for a timeline primitive, retaining both native and complete Driver inputs. */
public final class AdvancePrimitiveEvidence {
    public static final String SCHEMA = "xar.java.timeline-primitive-original-basis/v1";
    private AdvancePrimitiveEvidence() { }
    public static ExactRef preserve(ActionCommand command, AdvanceObservationPort.Frame actual, ActionPorts.OutcomeArchive archive) {
        var manifest = actual.semantic().get("java_driver_facts_evidence");
        require(manifest instanceof OpportunityJson.Obj, "timeline primitive needs the actual complete Driver manifest");
        ExactRef driver = ExactRef.fromJson(OpportunityJson.toNode(manifest));
        exact(actual.originalEvidence(), archive.loadNativeFrame(actual.originalEvidence()));
        exact(driver, archive.loadFullMaterial(driver).bytes());
        var row = StrictJson.object(); row.put("schema", SCHEMA); row.put("command_body_sha256", ActionCodec.bodySha256(command));
        row.set("native_frame", actual.originalEvidence().toJson()); row.set("driver_facts", driver.toJson());
        row.set("provenance", ObservationProvenanceCodec.encode(actual.provenance()));
        RawJson body = new RawJson(StrictJson.canonical(row)); ExactRef ref = archive.preserveMaterial(body);
        require(body.equals(archive.loadMaterial(ref)), "timeline primitive evidence archive readback differs"); return ref;
    }
    public static Complete load(ActionReceipt child, ActionPorts.OutcomeArchive archive, NativeEffectEvidence.FrameLoader frames) {
        require(child.state() instanceof ActionState.Settled, "timeline primitive after basis needs an actual settled original");
        var settlement = ((ActionState.Settled) child.state()).settlement();
        ActionState.EffectObservation effect;
        if (settlement instanceof ActionState.PauseConfirmed pause) {
            require(child.command().operation().value().equals("pause-map"), "typed pause after basis crossed its original primitive");
            effect = pause.observation();
        } else {
            // Historical Applied archives retain their original identity; new pause production uses PauseConfirmed.
            require(settlement instanceof ActionState.Applied, "timeline primitive after basis has no actual Push observation");
            effect = ((ActionState.Applied) settlement).observation();
        }
        require(effect.supportingEvidence().size() == 1, "historical timeline receipt lacks its complete after-frame basis");
        ExactRef ref = effect.supportingEvidence().getFirst(); RawJson raw = archive.loadMaterial(ref); exact(ref, raw.bytes());
        var row = StrictJson.object(StrictJson.parse(raw.bytes()), Set.of("schema", "command_body_sha256", "native_frame", "driver_facts", "provenance"));
        require(SCHEMA.equals(StrictJson.text(row.get("schema"))) && child.bodySha256().equals(StrictJson.text(row.get("command_body_sha256"))),
                "timeline after-frame basis crossed its immutable child");
        var basis = new NativeEffectEvidence.FrameBasis(ExactRef.fromJson(row.get("native_frame")), ExactRef.fromJson(row.get("driver_facts")));
        exact(basis.nativeFrame(), archive.loadNativeFrame(basis.nativeFrame())); exact(basis.driverFacts(), archive.loadFullMaterial(basis.driverFacts()).bytes());
        Complete actual = frames.load(basis, archive);
        var provenance = ObservationProvenanceCodec.decode(row.get("provenance"));
        if (provenance instanceof ObservationProvenance.FreshSnapshotQuery query) {
            frames.verifyFreshSnapshotQuery(query, actual, archive);
            require(query.basis() instanceof ObservationProvenance.LiveAfterSetter setter
                    && setter.setterAcknowledgement().equals(archive.referenceOf(child.ack().orElseThrow())),
                    "fresh snapshot query live basis must bind the actual child ACK reference");
        } else {
            var actualPush = new ObservationProvenance.Push(actual.identity().frame().snapshotId(), actual.identity().frame().identity().nativeRevision(), actual.originalEvidence());
            require(provenance.equals(actualPush), "timeline poststate must bind the actual pushed snapshot, revision and original packet");
        }
        require(provenance.equals(effect.provenance()), "timeline provenance differs from the actual effect observation");
        require(actual.identity().equals(effect.after()) && actual.source().equals(effect.source()) && actual.sessionId().equals(effect.sessionId())
                && actual.observedAt().equals(effect.observedAt()) && actual.originalEvidence().equals(effect.originalEvidence()), "timeline full native/Driver after-frame differs");
        return actual;
    }
    /** Original numeric Driver result for the exact pause primitive, replayed from full native/Driver originals.
     * Public JSON projection is owned by the public facade; this method never samples or submits.
     */
    public static RawJson compatiblePauseResult(ActionReceipt child, ActionPorts.OutcomeArchive archive, NativeEffectEvidence.FrameLoader frames) {
        require(child.state() instanceof ActionState.Settled settled && settled.settlement() instanceof ActionState.PauseConfirmed,
                "compatible pause result requires its typed actual paused Push settlement");
        new AdvancePrimitiveArchivedReplay(frames).verify(child,archive);
        var settled=(ActionState.Settled)child.state();var before=org.xar.ck3.control.application.effects.RootGuardEvidence.loadFrame(settled.attempt().guard(),archive,frames);
        var after=load(child,archive,frames);var ack=child.ack().orElseThrow();
        var packetValue=org.xar.ck3.control.application.driver.DriverJson.toNode(org.xar.ck3.control.application.driver.DriverJson.object(ack.originalFrame().bytes(),RawJson.MAXIMUM_BYTES));
        require(packetValue instanceof com.fasterxml.jackson.databind.node.ObjectNode,"actual original timeline ACK object required");
        var packet=(com.fasterxml.jackson.databind.node.ObjectNode)packetValue;
        require("command_result".equals(StrictJson.text(packet.get("type")))&&StrictJson.integer(packet.get("protocol_version"),1,1)==1
                &&packet.get("ok").isBoolean()&&packet.get("ok").booleanValue()&&ack.requestId().equals(StrictJson.text(packet.get("request_id"))),
                "original timeline ACK envelope differs from its native request");
        var token=org.xar.ck3.control.application.driver.DriverJson.toNode(org.xar.ck3.control.application.driver.DriverJson.object(ack.originalResultToken().orElseThrow().bytes(),RawJson.MAXIMUM_BYTES));
        require(token instanceof com.fasterxml.jackson.databind.node.ObjectNode,"actual timeline result object required");
        var result=((com.fasterxml.jackson.databind.node.ObjectNode)token).deepCopy();
        require(!result.has("request_id")&&!result.has("native_request_id")&&result.equals(packet.get("result")),"timeline ACK identity aliases or altered original result");
        result.put("backend_id","native-headless").put("native_request_id",ack.requestId());
        if("already_paused".equals(result.path("status").asText())) {
            var proof=result.putObject("map_control_postcondition");proof.put("status","observed").put("ack_status","already_paused").put("target_paused",true)
                    .put("starting_snapshot_id",before.identity().frame().snapshotId()).put("starting_revision",before.identity().frame().revision())
                    .put("ending_snapshot_id",after.identity().frame().snapshotId()).put("ending_revision",after.identity().frame().revision())
                    .put("ending_native_revision",after.identity().frame().identity().nativeRevision()).put("ending_date_raw",after.identity().frame().identity().dateRaw()).put("ending_paused",true);
            var diagnostics=after.semantic().get("diagnostics");
            if(diagnostics instanceof OpportunityJson.Obj actual) {
                var summary=proof.putObject("state_frame_rejections");
                String[] source={"rejected_state_snapshot_count","last_rejected_state_snapshot","snapshot_publish_diagnostic_count","last_snapshot_publish_diagnostic"};
                String[] output={"rejected_count","last_rejected","publish_diagnostic_count","last_publish"};
                for(int i=0;i<source.length;i++){var value=actual.members().get(source[i]);if(value==null)summary.putNull(output[i]);else summary.set(output[i],org.xar.ck3.control.application.driver.DriverJson.toNode(value));}
            } else proof.putNull("state_frame_rejections");
            result.put("paused",true).put("snapshot_id",after.identity().frame().snapshotId()).put("revision",after.identity().frame().revision());
        }
        return new RawJson(org.xar.ck3.control.application.driver.DriverJson.encodeNode(result));
    }
    static void exact(ExactRef reference, byte[] bytes) {
        require(reference.bytes() == bytes.length && reference.sha256().equals(ActionCodec.sha256(bytes)), "archived original bytes/SHA changed");
    }
}
