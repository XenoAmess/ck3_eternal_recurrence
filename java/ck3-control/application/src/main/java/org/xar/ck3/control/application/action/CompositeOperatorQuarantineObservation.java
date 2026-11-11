package org.xar.ck3.control.application.action;

import static org.xar.ck3.control.contracts.StrictJson.require;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** DATA for a new operator decision. It says nothing about the old action's dispatch or effects. */
public record CompositeOperatorQuarantineObservation(ExactRef requestSource, ExactRef requestMaterial,
        ExactRef originalReceipt, ExactRef predecessorState, long predecessorSequence, String predecessorDigest,
        ExactRef originalActionHead, Instant observedAt, List<Reservation> reservations) {
    public static final String SCHEMA = "xar.java.composite-operator-quarantine-observation/v1";
    public static final int MAX_BYTES = 65_536;
    public record Reservation(int ordinal, String actionId, String bodySha256, ExactRef firstReservationRecord) {
        public Reservation {
            require(ordinal >= 1 && ordinal <= 64, "bounded original reservation ordinal");
            StrictJson.text(actionId); digest(bodySha256); Objects.requireNonNull(firstReservationRecord);
        }
    }
    public CompositeOperatorQuarantineObservation {
        Objects.requireNonNull(requestSource); Objects.requireNonNull(requestMaterial); Objects.requireNonNull(originalReceipt);
        Objects.requireNonNull(predecessorState); Objects.requireNonNull(originalActionHead); Objects.requireNonNull(observedAt);
        StrictJson.safe(predecessorSequence, 1); digest(predecessorDigest); reservations = List.copyOf(reservations);
        require(!reservations.isEmpty() && reservations.size() <= 64, "complete bounded retired reservation vector required");
        for (int index=0;index<reservations.size();index++) require(reservations.get(index).ordinal()==index+1,"retired reservation order differs");
        require(requestSource.bytes()==requestMaterial.bytes()&&requestSource.sha256().equals(requestMaterial.sha256()),"exact installed operator request copy required");
    }
    public void requireOriginal(ActionReceipt receipt, CompositeExecution execution) {
        require(receipt.state() instanceof ActionState.CompositeUnknown unknown && unknown.execution().equals(execution),"operator quarantine preserves exact original CompositeUnknown execution");
        require(reservations.size()==execution.children().size(),"operator quarantine cannot remove a reservation");
        for(int i=0;i<reservations.size();i++) {
            var reservation=reservations.get(i);var child=execution.children().get(i);
            require(reservation.actionId().equals(child.actionId())&&reservation.bodySha256().equals(child.bodySha256()),"operator quarantine changed a reserved child body/order");
        }
    }
    public byte[] encode() {
        ObjectNode row=StrictJson.object();row.put("schema",SCHEMA);
        row.set("request_source",requestSource.toJson());row.set("request_material",requestMaterial.toJson());
        row.set("original_receipt",originalReceipt.toJson());row.set("predecessor_state",predecessorState.toJson());
        row.put("predecessor_sequence",predecessorSequence);row.put("predecessor_digest",predecessorDigest);
        row.set("original_action_head",originalActionHead.toJson());row.put("observed_at_utc",observedAt.toString());
        var children=row.putArray("reservations");for(var reservation:reservations){var child=children.addObject();child.put("ordinal",reservation.ordinal());child.put("action_id",reservation.actionId());child.put("body_sha256",reservation.bodySha256());child.set("first_reservation_record",reservation.firstReservationRecord().toJson());}
        return StrictJson.canonical(row,MAX_BYTES);
    }
    public static CompositeOperatorQuarantineObservation decode(byte[] raw) {
        var row=StrictJson.object(StrictJson.parse(raw,MAX_BYTES),Set.of("schema","request_source","request_material","original_receipt","predecessor_state","predecessor_sequence","predecessor_digest","original_action_head","observed_at_utc","reservations"));
        require(SCHEMA.equals(StrictJson.text(row.get("schema"))),"exact operator quarantine observation version required");
        JsonNode children=row.get("reservations");require(children.isArray()&&!children.isEmpty()&&children.size()<=64,"bounded complete reservations required");
        var reservations=new java.util.ArrayList<Reservation>();for(JsonNode value:children){StrictJson.object(value,Set.of("ordinal","action_id","body_sha256","first_reservation_record"));reservations.add(new Reservation(Math.toIntExact(StrictJson.integer(value.get("ordinal"),1,64)),StrictJson.text(value.get("action_id")),StrictJson.text(value.get("body_sha256")),ExactRef.fromJson(value.get("first_reservation_record"))));}
        return new CompositeOperatorQuarantineObservation(ExactRef.fromJson(row.get("request_source")),ExactRef.fromJson(row.get("request_material")),ExactRef.fromJson(row.get("original_receipt")),ExactRef.fromJson(row.get("predecessor_state")),StrictJson.integer(row.get("predecessor_sequence"),1,StrictJson.MAX_SAFE_INTEGER),StrictJson.text(row.get("predecessor_digest")),ExactRef.fromJson(row.get("original_action_head")),Instant.parse(StrictJson.text(row.get("observed_at_utc"))),reservations);
    }
    public static CompositeOperatorQuarantineObservation load(ActionReceipt receipt, ActionPorts.OutcomeArchive archive) {
        require(receipt.state() instanceof ActionState.CompositeOperatorQuarantined,"typed operator quarantine required");
        var state=(ActionState.CompositeOperatorQuarantined)receipt.state();var original=archive.loadMaterial(state.observationRef());
        var proof=decode(original.bytes());require(java.util.Arrays.equals(proof.encode(),original.bytes()),"canonical operator observation bytes required");
        var parent=archive.loadReceipt(proof.originalReceipt());proof.requireOriginal(parent,state.execution());
        require(parent.command().equals(receipt.command())&&parent.bodySha256().equals(receipt.bodySha256())&&receipt.sequence()==Math.addExact(proof.predecessorSequence(),1),"operator observation changed original command or append sequence");
        require(proof.requestMaterial().equals(archive.materialReferenceOf(archive.loadMaterial(proof.requestMaterial()))),"operator request material reference differs");
        return proof;
    }
    private static void digest(String value){require(value!=null&&value.matches("[0-9a-f]{64}"),"exact SHA256 required");}
}
