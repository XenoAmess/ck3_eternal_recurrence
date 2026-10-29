package org.xar.ck3.control.admission.cold;

import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Validated core projection, never an execution or recovery authorization. */
public record ColdRuntimeAdmissionCore(
        String machineId,
        ExactRef plan,
        ExactRef quote,
        ExactRef fullStorageRef,
        long runtimeHardBytes,
        Capacity capacity,
        PathFlavor pathFlavor) {

    public enum Schema {
        SOURCE29_A17("xar.Source29-A17-runtime-prepare-admission/v1");
        private final String wire;
        Schema(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }

    public enum Owner { Root }
    public enum Status { ADMITTED }
    public enum QualificationScope { CORE_PROJECTION_ONLY }

    public record Capacity(long dFreeFloorBytes, long zFreeFloorBytes) {
        public Capacity {
            positive(dFreeFloorBytes, "capacity.D_free_floor_bytes");
            positive(zFreeFloorBytes, "capacity.Z_free_floor_bytes");
        }
    }

    public ColdRuntimeAdmissionCore {
        StrictJson.require(machineId != null && !machineId.isEmpty(),
                "expected_machine_id must be nonempty text");
        StrictJson.require(pathFlavor != null, "source path flavor required");
        reference(plan, "plan", pathFlavor);
        reference(quote, "quote", pathFlavor);
        reference(fullStorageRef, "full_storage_ref", pathFlavor);
        positive(runtimeHardBytes, "runtime_hard_bytes");
        StrictJson.require(capacity != null, "capacity must be an object");
    }

    public Schema schema() { return Schema.SOURCE29_A17; }
    public Owner owner() { return Owner.Root; }
    public Status status() { return Status.ADMITTED; }
    public QualificationScope qualificationScope() { return QualificationScope.CORE_PROJECTION_ONLY; }

    /** A parsed historical ADMITTED claim is not fresh admission. */
    public boolean grantsRuntimeExecution() { return false; }
    public boolean grantsWarmOrRecoveryQualification() { return false; }

    static void positive(long value, String field) {
        StrictJson.require(value > 0 && value <= StrictJson.MAX_SAFE_INTEGER,
                field + " must be an exact positive safe integer");
    }

    static void reference(ExactRef value, String field, PathFlavor flavor) {
        StrictJson.require(value != null, field + " must be an exact FileRef");
        positive(value.bytes(), field + ".bytes");
        StrictJson.require(value.path().indexOf('\0') < 0, field + ".path must not contain NUL");
        StrictJson.require(flavor != null && flavor.isAbsolute(value.path()), field + ".path must be absolute");
    }
}
