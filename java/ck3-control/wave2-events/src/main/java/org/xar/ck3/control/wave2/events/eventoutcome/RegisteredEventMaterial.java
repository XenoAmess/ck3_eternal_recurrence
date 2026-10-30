package org.xar.ck3.control.wave2.events.eventoutcome;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.wave2.events.eventmaterial.Bookmark1070Material;
import org.xar.ck3.control.wave2.events.eventmaterial.RiteGrowthMaterial;
import org.xar.ck3.control.wave2.events.eventtraits.EventTraitMembership;
import org.xar.ck3.control.wave2.events.eventtraits.EventTraitMembershipCodec;
import org.xar.ck3.control.wave2.events.eventtraits.PoetTraitOutcome;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.ObjectValue;

/** Single complete outcome.py planning and result dispatch. Selected-effect ACK is never material evidence. */
public final class RegisteredEventMaterial {
    private RegisteredEventMaterial() { }
    public static Optional<ObjectValue> plan(ObjectValue decision,ObjectValue snapshot) {
        Objects.requireNonNull(decision);Objects.requireNonNull(snapshot);
        JsonNode choice=StrictJson.parse(RetainedJson.encode(decision)),frame=FullJsonTree.parse(RetainedJson.encode(snapshot, FullJsonTree.MAXIMUM_BYTES), FullJsonTree.MAXIMUM_BYTES);
        if(!"recommended".equals(text(choice,"status")))return Optional.empty();
        String key=text(choice,"event_definition_key"),build=text(choice,"ck3_build");BigInteger index=integer(choice,"selected_native_option_index");
        if(Bookmark1070Material.EVENT.equals(key)&&"1.20.0.4".equals(build)&&BigInteger.TWO.equals(index))
            return Bookmark1070Material.plan(choice,frame).map(value->retained(Bookmark1070Material.encode(value)));
        if(RiteGrowthMaterial.EVENT.equals(key)&&BigInteger.ZERO.equals(index))
            return RiteGrowthMaterial.plan(choice,frame).map(value->retained(RiteGrowthMaterial.encode(value)));
        if(PoetTraitOutcome.EVENT.equals(key)&&"1.20.0.4".equals(build)&&(BigInteger.ZERO.equals(index)||BigInteger.ONE.equals(index)))
            return poet(decision,snapshot).map(value->retained(PoetTraitOutcome.encode(value)));
        ObjectNode scalar=StrictJson.object().put("schema","xar.ck3.scalar-event-outcome-plan-input/v1");scalar.set("decision",choice);
        for(String name:java.util.List.of("played_character","played_character_gold","played_character_prestige","snapshot_id","revision")) {
            JsonNode value=frame.get(name);if(value==null)scalar.putNull(name);else scalar.set(name,value);
        }
        return ScalarEventOutcome.plan(ScalarOutcomeCodec.decodePlanInput(StrictJson.canonical(scalar))).map(value->retained(ScalarOutcomeCodec.encode(value)));
    }
    /** Native observer and archive verifier use the same specialized branch as the live producer. */
    public static ObjectValue evaluate(ObjectValue expectation,ObjectValue eventSelection) {
        Objects.requireNonNull(expectation);Objects.requireNonNull(eventSelection);
        byte[] raw=RetainedJson.encode(expectation);JsonNode expected=StrictJson.parse(raw),selection=StrictJson.parse(RetainedJson.encode(eventSelection));
        String key=text(expected,"event_definition_key"),metric=text(expected,"metric");
        if(Bookmark1070Material.EVENT.equals(key)&&Bookmark1070Material.METRIC.equals(metric))
            return retained(Bookmark1070Material.encode(Bookmark1070Material.evaluate(Bookmark1070Material.decodeExpectation(raw),selection)));
        if(RiteGrowthMaterial.EVENT.equals(key)&&RiteGrowthMaterial.METRIC.equals(metric))
            return retained(RiteGrowthMaterial.encode(RiteGrowthMaterial.evaluate(RiteGrowthMaterial.decodeExpectation(raw),selection)));
        if(PoetTraitOutcome.EVENT.equals(key)&&"false_to_true".equals(text(expected,"expected_relation")))return evaluatePoet(expected,selection);
        return retained(ScalarOutcomeCodec.encode(ScalarEventOutcome.evaluate(ScalarOutcomeCodec.decodeExpectation(raw),ScalarOutcomeCodec.decodeSelection(RetainedJson.encode(eventSelection)))));
    }
    public static Optional<PoetTraitOutcome.Expectation> poet(ObjectValue decision,ObjectValue snapshot) {
        Objects.requireNonNull(decision);Objects.requireNonNull(snapshot);
        JsonNode choice=StrictJson.parse(RetainedJson.encode(decision)),frame=FullJsonTree.parse(RetainedJson.encode(snapshot, FullJsonTree.MAXIMUM_BYTES), FullJsonTree.MAXIMUM_BYTES);BigInteger index=integer(choice,"selected_native_option_index");
        if(!"recommended".equals(text(choice,"status"))||!PoetTraitOutcome.EVENT.equals(text(choice,"event_definition_key"))||!"1.20.0.4".equals(text(choice,"ck3_build"))
            ||!(BigInteger.ZERO.equals(index)||BigInteger.ONE.equals(index)))return Optional.empty();
        JsonNode character=frame.get("played_character");StrictJson.require(character!=null&&character.isObject(),"poet requires actual played-character projection");
        var nativeFrame=new EventTraitMembership.Frame(requiredInteger(frame,"native_revision"),requiredInteger(frame,"date_raw").intValueExact(),requiredInteger(character,"character_id").intValueExact());
        var publicFrame=new PoetTraitOutcome.PublicFrame(StrictJson.text(frame.get("snapshot_id")),requiredInteger(frame,"revision"),nativeFrame);
        JsonNode rawMembership=character.get("event_trait_membership");EventTraitMembership.Observation membership=rawMembership==null||rawMembership.isNull()?null:EventTraitMembershipCodec.decodeLeaf(rawMembership,nativeFrame);
        var scalarDecision=new ScalarEventOutcome.Decision("recommended",PoetTraitOutcome.EVENT,"1.20.0.4",integer(choice,"selected_option_number"),index,null);
        return PoetTraitOutcome.plan(new PoetTraitOutcome.PlanInput(scalarDecision,publicFrame,membership));
    }
    private static ObjectValue evaluatePoet(JsonNode e,JsonNode selection) {
        BigInteger index=requiredInteger(e,"selected_native_option_index");PoetTraitOutcome.Choice choice;
        if(BigInteger.ZERO.equals(index))choice=PoetTraitOutcome.Choice.POET;else {StrictJson.require(BigInteger.ONE.equals(index),"poet exact native option required");choice=PoetTraitOutcome.Choice.JOURNALLER;}
        var frame=new EventTraitMembership.Frame(requiredInteger(e,"starting_native_revision"),requiredInteger(e,"date_raw").intValueExact(),requiredInteger(e,"character_id").intValueExact());
        var start=new PoetTraitOutcome.PublicFrame(StrictJson.text(e.get("starting_snapshot_id")),requiredInteger(e,"starting_revision"),frame);
        var binding=new PoetTraitOutcome.Binding(choice,start);String status=text(e,"status");PoetTraitOutcome.Expectation expected;
        if("ready".equals(status))expected=new PoetTraitOutcome.Ready(binding);else{StrictJson.require("unavailable".equals(status),"poet expectation status");expected=new PoetTraitOutcome.Unavailable(binding,PoetTraitOutcome.Reason.SAME_FRAME_UNAVAILABLE);}
        StrictJson.require(e.equals(StrictJson.parse(PoetTraitOutcome.encode(expected))),"poet material JSON/binding changed");
        JsonNode before=selection.get("starting_played_character_event_traits"),after=selection.get("ending_played_character_event_traits");
        PoetTraitOutcome.Selection selected=null;
        if(before!=null&&!before.isNull()&&after!=null&&!after.isNull()) {
            var endNative=new EventTraitMembership.Frame(requiredInteger(after,"snapshot_revision"),requiredInteger(after,"date_raw").intValueExact(),requiredInteger(after,"played_character_id").intValueExact());
            var end=new PoetTraitOutcome.PublicFrame(StrictJson.text(selection.get("ending_snapshot_id")),requiredInteger(selection,"ending_revision"),endNative);
            var actualStart=new PoetTraitOutcome.PublicFrame(StrictJson.text(selection.get("starting_snapshot_id")),requiredInteger(selection,"starting_revision"),frame);
            selected=new PoetTraitOutcome.Selection(Boolean.TRUE.equals(bool(selection,"postcondition_verified")),actualStart,end,EventTraitMembershipCodec.decodeLeaf(before,frame),EventTraitMembershipCodec.decodeLeaf(after,endNative));
        }
        return retained(PoetTraitOutcome.encode(PoetTraitOutcome.evaluate(expected,selected)));
    }
    private static ObjectValue retained(byte[] raw) { return RetainedJson.object(RetainedJson.parse(raw)); }
    private static String text(JsonNode node,String name) { JsonNode v=node.get(name);if(v==null||v.isNull())return null;StrictJson.require(v.isTextual(),"material text token required: "+name);return v.textValue(); }
    private static BigInteger integer(JsonNode node,String name) { JsonNode v=node.get(name);if(v==null||v.isNull())return null;StrictJson.require(v.isIntegralNumber(),"material integer token required: "+name);return v.bigIntegerValue(); }
    private static Boolean bool(JsonNode node,String name) { JsonNode v=node.get(name);if(v==null||v.isNull())return null;StrictJson.require(v.isBoolean(),"material boolean token required: "+name);return v.booleanValue(); }
    private static BigInteger requiredInteger(JsonNode node,String name) { BigInteger n=integer(node,name);StrictJson.require(n!=null,"material integer required: "+name);return n; }
}
