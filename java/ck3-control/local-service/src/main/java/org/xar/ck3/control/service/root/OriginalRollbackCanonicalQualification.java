package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.contracts.FileStatIdentity;
import static org.xar.ck3.control.service.root.OriginalRollbackSavedFrontier.*;

/** Original measured-receipt compatibility only; authority also invokes the current concrete full physical validator. */
public final class OriginalRollbackCanonicalQualification {
    private OriginalRollbackCanonicalQualification(){ }
    public static void verify(OriginalRollbackFiles.Scope files,OriginalRollbackProof proof,Saved saved,OriginalRollbackEpoch.Closed closed)throws IOException {
        ObjectNode row=load(files,proof.sources().canonicalCheckpointQualification(),32768);
        exact(row,Set.of("schema","status","machine_id","observed_at_utc","validator_source_ref","driver_ref","driver_identity_before","driver_identity_after",
                "save_ref","save_identity_before","save_identity_after","checkpoint","pipe_name","driver_physical_body_reads","driver_payload_reader_calls",
                "driver_physical_read_scope","driver_payload_reader_scope","original_validator_calls","save_sha256_calls","driver_body_rewritten","ledger_write_already_performed","game_or_RPC_calls"));
        eq(row,"schema","xar.current-saved-recovery-checkpoint-qualification/v1");eq(row,"status","ORIGINAL_SDK_SAVED_CHECKPOINT_QUALIFIED");eq(row,"machine_id",proof.machineId());utc(row,"observed_at_utc");
        for(String field:List.of("driver_physical_body_reads","driver_payload_reader_calls","original_validator_calls","save_sha256_calls"))require(n(row,field,1)==1,"original measured validator call/read accounting differs");
        eq(row,"driver_physical_read_scope","entire_operation_including_caller_reference_measurement");eq(row,"driver_payload_reader_scope","pinned_reader_or_caller_premeasured_RAM");
        no(row.get("driver_body_rewritten"));no(row.get("ledger_write_already_performed"));zero(row,"game_or_RPC_calls");
        require(ref(row,"driver_ref").equals(closed.driver())&&ref(row,"save_ref").equals(closed.save())&&ref(row,"validator_source_ref").equals(saved.validator())
                &&same(row.get("checkpoint"),saved.rawCheckpoint())&&text(row,"pipe_name").equals(closed.pipeName()),"original canonical qualification changed its exact closed checkpoint source");
        for(String field:List.of("driver_identity_before","driver_identity_after"))require(FileStatIdentity.fromJson(row.get(field),FileStatIdentity.SCHEMA).equals(closed.driverIdentity()),"canonical current Driver identity drift");
        for(String field:List.of("save_identity_before","save_identity_after"))require(FileStatIdentity.fromJson(row.get(field),FileStatIdentity.SCHEMA).equals(closed.saveIdentity()),"canonical unchanged SAVE identity drift");
    }
}
