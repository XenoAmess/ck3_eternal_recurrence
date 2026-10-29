package org.xar.ck3.control.nativebridge.capabilities.army;

import java.util.List;
import java.util.Objects;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsPublicNumbers.*;

/** Sole wide-field roles for the immutable roster raw shapes and complete derived request/projection closure.
 * All uint32 full IDs, i32 indexes/end markers, flags, FNV hashes and gate operands retain their native type. */
public final class ArmyStrengthsRosterPublicRules {
    private ArmyStrengthsRosterPublicRules() { }
    public enum Shape {
        OPERANDRESOLUTION("OperandResolution"),
        RAWREFERENCEOCCURRENCE("RawReferenceOccurrence"),
        RAWREFERENCES("RawReferences"),
        RELATIONPROBE("RelationProbe"),
        RELATIONLOOKUP("RelationLookup"),
        ADMISSIONGATE("AdmissionGate"),
        PENDINGPROBE("PendingProbe"),
        PENDINGSELECTION("PendingSelection"),
        ARRGADMISSIONOCCURRENCE("ArRgAdmissionOccurrence"),
        ROSTERADMISSIONOCCURRENCE("RosterAdmissionOccurrence"),
        ARMYCURRENTDAILYASSAULTROSTERADMISSIONV1("ArmyCurrentDailyAssaultRosterAdmissionV1"),
        DERIVEDRELATION("DerivedRelation"),
        DERIVEDPENDING("DerivedPending"),
        DERIVEDGATE("DerivedGate"),
        DERIVEDOCCURRENCE("DerivedOccurrence"),
        REQUESTPROVENANCE("RequestProvenance"),
        PLACEMENTREQUEST("PlacementRequest"),
        PROJECTION("Projection");
        private final String wire;
        Shape(String wire){this.wire=wire;}
        public String wire(){return wire;}
        public static Shape fromWire(String name){
            for(Shape value:values())if(value.wire.equals(name))return value;
            throw new IllegalArgumentException("Unknown exact roster shape: "+name);
        }
    }
    public static List<Rule> publicRules(String kind,String prefix){return publicRules(Shape.fromWire(kind),prefix);}
    public static List<Rule> publicRules(Shape shape,String prefix){
        Objects.requireNonNull(shape);Objects.requireNonNull(prefix);
        // Empty means the shape root. Nonempty prefix is one exact schema path, never an object-key glob.
        new Rule(prefix+"/roster_numeric_role_probe",Domain.SIGNED_64);
        List<String> fields=switch(shape){
            case OPERANDRESOLUTION -> List.of();
            case RAWREFERENCEOCCURRENCE -> List.of();
            case RAWREFERENCES -> List.of();
            case RELATIONPROBE -> List.of("/slot_index_i64");
            case RELATIONLOOKUP -> List.of("/probes/*/slot_index_i64","/candidate_slot_index_i64");
            case ADMISSIONGATE -> List.of("/relation_lookup/probes/*/slot_index_i64","/relation_lookup/candidate_slot_index_i64");
            case PENDINGPROBE -> List.of("/physical_slot_i64");
            case PENDINGSELECTION -> List.of("/home_slot_i64","/probes/*/physical_slot_i64","/selected_physical_slot_i64");
            case ARRGADMISSIONOCCURRENCE -> List.of();
            case ROSTERADMISSIONOCCURRENCE -> List.of("/gate/relation_lookup/probes/*/slot_index_i64","/gate/relation_lookup/candidate_slot_index_i64","/pending_selection/home_slot_i64","/pending_selection/probes/*/physical_slot_i64","/pending_selection/selected_physical_slot_i64");
            case ARMYCURRENTDAILYASSAULTROSTERADMISSIONV1 -> List.of("/occurrences/*/gate/relation_lookup/probes/*/slot_index_i64","/occurrences/*/gate/relation_lookup/candidate_slot_index_i64","/occurrences/*/pending_selection/home_slot_i64","/occurrences/*/pending_selection/probes/*/physical_slot_i64","/occurrences/*/pending_selection/selected_physical_slot_i64");
            case DERIVEDRELATION -> List.of("/candidate_slot_index_i64","/probe_ledger/*/slot_index_i64");
            case DERIVEDPENDING -> List.of("/home_slot_i64","/selected_physical_slot_i64","/probe_ledger/*/physical_slot_i64");
            case DERIVEDGATE -> List.of("/relation_lookup/candidate_slot_index_i64","/relation_lookup/probe_ledger/*/slot_index_i64");
            case DERIVEDOCCURRENCE -> List.of("/gate/relation_lookup/candidate_slot_index_i64","/gate/relation_lookup/probe_ledger/*/slot_index_i64","/pending_selection/home_slot_i64","/pending_selection/selected_physical_slot_i64","/pending_selection/probe_ledger/*/physical_slot_i64");
            case REQUESTPROVENANCE -> List.of("/relation_lookup/candidate_slot_index_i64","/relation_lookup/probe_ledger/*/slot_index_i64","/pending_selection/home_slot_i64","/pending_selection/selected_physical_slot_i64","/pending_selection/probe_ledger/*/physical_slot_i64");
            case PLACEMENTREQUEST -> List.of("/source_provenance/relation_lookup/candidate_slot_index_i64","/source_provenance/relation_lookup/probe_ledger/*/slot_index_i64","/source_provenance/pending_selection/home_slot_i64","/source_provenance/pending_selection/selected_physical_slot_i64","/source_provenance/pending_selection/probe_ledger/*/physical_slot_i64");
            case PROJECTION -> List.of("/observed_current_roster_admission/occurrences/*/gate/relation_lookup/probes/*/slot_index_i64","/observed_current_roster_admission/occurrences/*/gate/relation_lookup/candidate_slot_index_i64","/observed_current_roster_admission/occurrences/*/pending_selection/home_slot_i64","/observed_current_roster_admission/occurrences/*/pending_selection/probes/*/physical_slot_i64","/observed_current_roster_admission/occurrences/*/pending_selection/selected_physical_slot_i64","/occurrences/*/gate/relation_lookup/candidate_slot_index_i64","/occurrences/*/gate/relation_lookup/probe_ledger/*/slot_index_i64","/occurrences/*/pending_selection/home_slot_i64","/occurrences/*/pending_selection/selected_physical_slot_i64","/occurrences/*/pending_selection/probe_ledger/*/physical_slot_i64","/request_prefix/*/source_provenance/relation_lookup/candidate_slot_index_i64","/request_prefix/*/source_provenance/relation_lookup/probe_ledger/*/slot_index_i64","/request_prefix/*/source_provenance/pending_selection/home_slot_i64","/request_prefix/*/source_provenance/pending_selection/selected_physical_slot_i64","/request_prefix/*/source_provenance/pending_selection/probe_ledger/*/physical_slot_i64","/independently_derived_requests/*/source_provenance/relation_lookup/candidate_slot_index_i64","/independently_derived_requests/*/source_provenance/relation_lookup/probe_ledger/*/slot_index_i64","/independently_derived_requests/*/source_provenance/pending_selection/home_slot_i64","/independently_derived_requests/*/source_provenance/pending_selection/selected_physical_slot_i64","/independently_derived_requests/*/source_provenance/pending_selection/probe_ledger/*/physical_slot_i64");
        };
        return fields.stream().map(path->new Rule(prefix+path,Domain.SIGNED_64)).toList();
    }
}

