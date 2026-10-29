package org.xar.ck3.control.military.projectedcontact;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.military.projectedcontact.IndexedContactIngress.Decision;
import org.xar.ck3.control.military.projectedcontact.IndexedContactIngress.NeedsQuery;
import org.xar.ck3.control.military.projectedcontact.IndexedContactIngress.NewEncounter;
import org.xar.ck3.control.military.projectedcontact.IndexedContactIngress.NoContact;
import org.xar.ck3.control.military.projectedcontact.IndexedContactIngress.ResumeExisting;
import org.xar.ck3.control.military.projectedcontact.IndexedContactIngress.DefenderConstructorZero;
import org.xar.ck3.control.military.projectedcontact.IndexedContactIngress.IncomingAttackerEntry;
import org.xar.ck3.control.military.projectedcontact.ProjectedContactPolicy.Available;
import org.xar.ck3.control.military.projectedcontact.ProjectedContactPolicy.QueryKey;
import org.xar.ck3.control.military.projectedcontact.ProjectedContactPolicy.QueryRequired;
import org.xar.ck3.control.military.projectedcontact.ProjectedContactPolicy.Selection;
import org.xar.ck3.control.military.projectedcontact.SourceBoundContactIndex.Outcome;
import org.xar.ck3.control.military.projectedcontact.SourceBoundContactIndex.Context;
import org.xar.ck3.control.military.projectedcontact.SourceBoundContactIndex.Current;
import org.xar.ck3.control.military.projectedcontact.SourceBoundContactIndex.Unknown;

/** Strict legacy input boundary plus an indexed typed consumer. Context comes from a real qualified provider. */
public final class IndexedContactIngressCodec {
    private IndexedContactIngressCodec() { }

    public static Decision decide(byte[] raw, Context context) {
        ProjectedContactCodec.Input input = ProjectedContactCodec.decode(raw);
        Objects.requireNonNull(context, "qualified context or explicit Unknown required");
        Context bound = context;
        if (context instanceof Current current && !current.snapshot().equals(input.snapshot())) {
            bound = new Unknown("qualified context snapshot differs from strict input snapshot");
        }
        return IndexedContactIngress.prepare(bound, input.queryRows()).select(bound, input.request());
    }

    /** Existing selection bytes are unchanged; callers can switch the selector without a field alias. */
    public static byte[] select(byte[] raw, Context context) {
        return ProjectedContactCodec.encode(decide(raw, context).selection());
    }

    /** Distinct versioned ingress DTO; complete source-native projection is retained in contact_selection. */
    public static byte[] encodeDecision(Decision decision) {
        Objects.requireNonNull(decision, "decision");
        ObjectNode root = StrictJson.object();
        root.put("schema", "xar.indexed-contact-ingress/v1");
        root.set("contact_selection", StrictJson.parse(ProjectedContactCodec.encode(decision.selection())));
        String kind;
        if (decision instanceof NeedsQuery query) {
            kind = "query_required"; root.put("query_reason", query.reason().name());
        } else if (decision instanceof NoContact) { kind = "no_contact"; }
        else if (decision instanceof ResumeExisting resume) {
            kind = "resume_existing"; root.put("selected_combat_id", resume.selectedCombatId());
            root.put("selected_combat_array_index", resume.selectedCombatArrayIndex());
        } else {
            NewEncounter encounter = (NewEncounter) decision; kind = "new_encounter";
            root.put("contact_incoming_entry_province_id", encounter.contactIncomingEntryProvinceId());
            if (encounter.attackerEntryProvinceId() == null) { root.putNull("attacker_entry_province_id"); }
            else { root.put("attacker_entry_province_id", encounter.attackerEntryProvinceId()); }
            if (encounter.constructorAdjacencyKindRaw() == null) { root.putNull("constructor_adjacency_kind_raw"); }
            else { root.put("constructor_adjacency_kind_raw", encounter.constructorAdjacencyKindRaw()); }
        }
        root.put("decision_kind", kind);
        root.put("actual_arrival_observed", decision.actualArrivalObserved());
        root.put("future_contact_authorized", decision.futureContactAuthorized());
        root.put("authorizes_command_replay", decision.authorizesCommandReplay());
        return StrictJson.canonical(root);
    }

    /** Runtime validation before constructing the closed ingress DTO; unknown fields/tokens are rejected. */
    public static Decision decodeDecision(byte[] raw) {
        JsonNode root = StrictJson.parse(raw);
        StrictJson.require(root.isObject(), "ingress decision object required");
        StrictJson.require(StrictJson.text(root.get("schema")).equals("xar.indexed-contact-ingress/v1"),
                "unsupported ingress schema");
        JsonNode encoded = root.get("contact_selection");
        StrictJson.require(encoded != null && encoded.isObject(), "contact selection object required");
        String status = StrictJson.text(encoded.get("status"));
        QueryKey key = ProjectedContactPolicy.parseStep(StrictJson.text(encoded.get("query_step"))).orElseThrow(
                () -> new IllegalArgumentException("canonical Contact query step required"));
        Selection selection;
        if (status.equals("query_required")) {
            StrictJson.object(encoded, Set.of("status", "query_step")); selection = new QueryRequired(key);
        } else {
            StrictJson.require(status.equals("available"), "unsupported Contact selection status");
            selection = new Available(key, ProjectedContactCodec.decodeScope(encoded.get("projection")));
            Available available = (Available) selection;
            StrictJson.require(key.equals(new QueryKey(available.projection().subjectArmyId(),
                    available.projection().targetProvinceId(), available.projection().incomingEntryProvinceId())),
                    "selection key and native scope differ");
        }
        StrictJson.require(encoded.equals(StrictJson.parse(ProjectedContactCodec.encode(selection))),
                "Contact selection fields/types disagree");
        String kind = StrictJson.text(root.get("decision_kind"));
        Decision decision;
        if (selection instanceof QueryRequired required) {
            StrictJson.require(kind.equals("query_required"), "query_required decision required");
            decision = new NeedsQuery(required, Outcome.valueOf(StrictJson.text(root.get("query_reason"))));
        } else {
            Available available = (Available) selection;
            decision = switch (kind) {
                case "no_contact" -> new NoContact(available);
                case "resume_existing" -> new ResumeExisting(available);
                case "new_encounter" -> new NewEncounter(available,
                        available.incomingAttackerGeometryReady()
                                ? new IncomingAttackerEntry(available.projection().incomingEntryProvinceId())
                                : new DefenderConstructorZero());
                default -> throw new IllegalArgumentException("unsupported ingress decision kind");
            };
        }
        StrictJson.require(root.equals(StrictJson.parse(encodeDecision(decision))),
                "ingress decision fields/types disagree");
        return decision;
    }
}
