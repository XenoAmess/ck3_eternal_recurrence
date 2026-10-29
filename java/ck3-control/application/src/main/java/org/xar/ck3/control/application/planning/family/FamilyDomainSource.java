package org.xar.ck3.control.application.planning.family;

import static org.xar.ck3.control.application.planning.family.FamilyJson.*;
import static org.xar.ck3.control.application.planning.family.FamilyPorts.*;
import java.io.IOException;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.continuity.writer.DomainBodies.Slot;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import org.xar.ck3.control.wave2.governance.marriagehandoff.MarriageHandoffCodec;

/** Reads actual canonical full bodies from the existing sole writer's registry. No empty defaults. */
public final class FamilyDomainSource implements LedgerSource {
    public record BridgeObservation(BridgeIdentity identity, org.xar.ck3.control.contracts.ExactRef evidence) {
        public BridgeObservation { Objects.requireNonNull(identity); Objects.requireNonNull(evidence); }
    }
    public interface CurrentBridge {
        Optional<BridgeObservation> observe(PlanningRequest request);
        boolean verifyRetained(org.xar.ck3.control.application.action.PlanningReadReceipt read, BridgeObservation observation);
    }
    private final CurrentSession sessions;
    private final CurrentBridge bridge;
    public FamilyDomainSource(CurrentSession sessions, CurrentBridge bridge) {
        this.sessions = Objects.requireNonNull(sessions); this.bridge = Objects.requireNonNull(bridge);
    }
    @Override public LedgerRead readCurrent(PlanningRequest request) {
        try {
            Optional<BridgeObservation> current = bridge.observe(request);
            if (current.isEmpty()) return new MissingDocuments("actual current Bridge process identity is unavailable; Game PID cannot substitute");
            var same = sessions.current();
            DomainBodies.Read family = same.readDomain(Slot.FAMILY), matrilineal = same.readDomain(Slot.CHILD_MATRILINEAL), childDefault = same.readDomain(Slot.DEFAULT_MARRIAGE);
            if (!(family instanceof DomainBodies.Available f)) return missing(Slot.FAMILY, family);
            if (!(matrilineal instanceof DomainBodies.Available m)) return missing(Slot.CHILD_MATRILINEAL, matrilineal);
            if (!(childDefault instanceof DomainBodies.Available d)) return missing(Slot.DEFAULT_MARRIAGE, childDefault);
            if (!f.head().equals(m.head()) || !f.head().equals(d.head())) return new MissingDocuments("canonical head changed between family document reads; retry under actual owner lock");
            Obj familyBody = validate(Slot.FAMILY, f.canonicalBody()), matrilinealBody = validate(Slot.CHILD_MATRILINEAL, m.canonicalBody()), defaultBody = validate(Slot.DEFAULT_MARRIAGE, d.canonicalBody());
            for(var body:List.of(familyBody,matrilinealBody,defaultBody)) {
                FamilyOrdinaryRestoreMigration.requireCurrent(body,request);
                FamilyNextEpisodeMigration.requireCurrent(body,request);
            }
            return new KnownDocuments(new Documents(familyBody, matrilinealBody, defaultBody, current.get().identity(), f.head(),
                    List.of(f.reference().payload(), m.reference().payload(), d.reference().payload())));
        } catch (IOException | IllegalArgumentException error) { return new MissingDocuments("actual family domain body unavailable: " + error.getMessage()); }
    }
    private static MissingDocuments missing(Slot slot, DomainBodies.Read value) {
        if (value instanceof DomainBodies.Unavailable missing) return new MissingDocuments(slot + ":" + missing.reason() + ":" + missing.detail());
        throw new IllegalArgumentException("domain read classification");
    }
    public static String schema(Slot slot) {
        return switch (slot) {
            case FAMILY -> "xar.ck3.first-heir-marriage-formal.v1";
            case CHILD_MATRILINEAL -> "xar.ck3.player-child-matrilineal-private-action.v1";
            case DEFAULT_MARRIAGE -> "xar.ck3.player-child-default-formal.v1";
            default -> throw new IllegalArgumentException("unsupported family domain slot");
        };
    }
    public static Obj validate(Slot slot, byte[] bytes) {
        Obj body = decodeDomain(bytes);
        if (!schema(slot).equals(text(body.get("schema")))) throw new IllegalArgumentException("family domain body schema changed");
        if (slot == Slot.FAMILY) MarriageHandoffCodec.decodeLedger(bytes);
        for (String field : List.of("pending", "resolved")) {
            Value value = body.get(field);
            if (value != Nil.INSTANCE && !(value instanceof Obj)) throw new IllegalArgumentException("explicit nullable family records required");
            if (value instanceof Obj record) {
                text(record.get("episode_run_id"));
                for (String id : List.of("heir_character_id", "candidate_character_id")) positive(record.get(id));
                if (field.equals("pending")) {
                    positive(record.get("source_bridge_pid")); text(record.get("source_bridge_creation_date"));
                    integer(record.get("pre_native_revision"));
                }
                validateNativeContext(record);
            }
        }
        return body;
    }
    private static void validateNativeContext(Obj record) {
        if(record.members().containsKey("java_preparation_schema")) {
            if(!t(FamilyNativePreparation.MaterializedSend.SCHEMA).equals(record.get("java_preparation_schema")))throw new IllegalArgumentException("unknown Java materialized preparation schema");
            var context=FamilyNativePreparation.MaterializedSend.fromJson(object(record.get("native_send_context")));
            if(!n(context.senderId()).equals(record.get("played_character_id"))||!n(context.recipientId()).equals(record.get("recipient_character_id"))
                    ||context.secondaryActorId().isEmpty()||context.secondaryRecipientId().isEmpty()
                    ||!n(context.secondaryActorId().getAsLong()).equals(record.get("heir_character_id"))
                    ||!n(context.secondaryRecipientId().getAsLong()).equals(record.get("candidate_character_id")))
                throw new IllegalArgumentException("private pending context differs from its actual played/subject/candidate/recipient roles");
        } else if(record.members().containsKey("native_send_context"))throw new IllegalArgumentException("unversioned native send context cannot qualify a Java pending record");
        if(record.get("source_pending") instanceof Obj original)validateNativeContext(original);
    }
}
