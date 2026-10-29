package org.xar.ck3.control.wave2.runtime.closedadoption;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.Set;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FileStatIdentity;
import org.xar.ck3.control.contracts.SavedFrame;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.NativeColdAdoptionProjection;
import org.xar.ck3.control.recovery.RecoveryEvidence;
import org.xar.ck3.control.wave2.runtime.savedproof.ColdRestoreDriverLineage;

/** Pure pre-CAP preview. Its data result cannot create a session, measurement or Native ticket. */
final class RawRestoreAdmissionReducer {
    enum DriverBranch { ACTUAL_CURRENT_GAME_HEADER, ACTUAL_PENDING_COLD_WITH_UNCHANGED_CLOSED_DRIVER }
    record Preview(DriverBranch branch,String episodeRunId,long savedDateRaw,long elapsedGameDays,
            String basisSha256,String measurementSha256,String rawBindingSha256) {
        boolean grantsWarmAttachment() { return false; }
        boolean originalActionsReplayed() { return false; }
        long newGameDayCredit() { return 0; }
        long newOrdinaryCycleCredit() { return 0; }
    }
    private RawRestoreAdmissionReducer() { }
    static Preview preview(RecoveryEvidence basis,RecoveryEvidence measured,ColdRestoreDriverLineage lineage,
            FileStatIdentity currentDriverIdentity,RootColdResumeSession.RawColdFrame raw) {
        ObjectNode old=SettledQueryClassifier.object(StrictJson.parse(basis.bytes()));
        ObjectNode actual=SettledQueryClassifier.object(StrictJson.parse(measured.bytes()));
        SettledQueryClassifier.equal(actual,"schema","xar.current-saved-recovery-checkpoint-qualification/v1");
        SettledQueryClassifier.equal(actual,"status","ORIGINAL_SDK_SAVED_CHECKPOINT_QUALIFIED");
        StrictJson.require(StrictJson.text(old.get("machine_id")).equals(StrictJson.text(actual.get("machine_id"))),"same measured machine");
        SavedFrame frame=SavedFrame.fromJson(old.get("frame"));
        StrictJson.require(raw.mapReady() && raw.paused() && raw.dateRaw()==frame.dateRaw()
                && raw.actorCharacterId()==frame.actorCharacterId()
                && raw.pipeName().equals(StrictJson.text(actual.get("pipe_name"))),"actual held raw frame matches saved date/actor/pipe");
        ObjectNode anchor=StrictJson.object(old.get("checkpoint"),Set.of("name","load_save_name","path","size","sha256","saved_date_raw","history_index","succession_lifecycle"));
        ObjectNode checkpoint=SettledQueryClassifier.object(actual.get("checkpoint"));
        ExactRef save=ExactRef.fromJson(actual.get("save_ref"));
        StrictJson.require(save.equals(ExactRef.fromJson(old.get("refs").get("save")))
                && save.path().equals(StrictJson.text(anchor.get("path")))
                && save.path().equals(StrictJson.text(checkpoint.get("path")))
                && save.sha256().equals(StrictJson.text(checkpoint.get("sha256")))
                && save.sha256().equals(StrictJson.text(anchor.get("sha256"))),"same immutable original SAVE and actual SDK checkpoint");
        StrictJson.integer(checkpoint.get("size"),save.bytes(),save.bytes()); StrictJson.integer(anchor.get("size"),save.bytes(),save.bytes());
        for (String name:Set.of("name","history_index")) {
            StrictJson.require(anchor.get(name).equals(checkpoint.get(name)),"same complete saved anchor: "+name);
        }
        StrictJson.integer(anchor.get("history_index"),1,StrictJson.MAX_SAFE_INTEGER);
        StrictJson.require("xar_checkpoint.ck3".equals(StrictJson.text(anchor.get("name")))
                && "xar_checkpoint".equals(StrictJson.text(anchor.get("load_save_name"))),"original saved-cold load contract");
        StrictJson.integer(anchor.get("saved_date_raw"),frame.dateRaw(),frame.dateRaw());
        StrictJson.integer(checkpoint.get("date_raw"),frame.dateRaw(),frame.dateRaw());
        StrictJson.integer(checkpoint.get("episode_character_id"),frame.actorCharacterId(),frame.actorCharacterId());
        StrictJson.require(frame.episodeRunId().equals(StrictJson.text(checkpoint.get("episode_run_id")))
                && frame.episodeRunId().equals(lineage.episodeRunId()) && lineage.episodeCharacterId()==frame.actorCharacterId(),
                "actual SDK-validated current payload and original saved history keep the old episode");
        ObjectNode lifecycle=StrictJson.object(anchor.get("succession_lifecycle"),Set.of("schema","lifecycle","xar_enabled","pact_contract","source","environment_sha256"));
        StrictJson.require(lifecycle.equals(checkpoint.get("succession_lifecycle")) && lifecycle.equals(lineage.successionLifecycle()),"all six original lifecycle fields unchanged");
        SettledQueryClassifier.equal(lifecycle,"schema","xar.ck3.succession-lifecycle-binding/v1");
        StrictJson.text(lifecycle.get("lifecycle")); StrictJson.text(lifecycle.get("source")); StrictJson.text(lifecycle.get("pact_contract"));
        StrictJson.require(StrictJson.text(lifecycle.get("environment_sha256")).matches("[0-9a-f]{64}"),"original semantic environment digest");
        for (String field:Set.of("driver_physical_body_reads","driver_payload_reader_calls","original_validator_calls","save_sha256_calls")) { StrictJson.integer(actual.get(field),1,1); }
        for (String field:Set.of("driver_body_rewritten","ledger_write_already_performed")) { SettledQueryClassifier.falseValue(actual.get(field)); }
        StrictJson.integer(actual.get("game_or_RPC_calls"),0,0);
        StrictJson.require(currentDriverIdentity.equals(FileStatIdentity.fromJson(actual.get("driver_identity_before"),FileStatIdentity.SCHEMA))
                && currentDriverIdentity.equals(FileStatIdentity.fromJson(actual.get("driver_identity_after"),FileStatIdentity.SCHEMA)),"actual new measurement identities");
        var owner=raw.ownerColdAdoption();
        StrictJson.require(owner.sessionBridgePid().isPresent() && owner.sessionBridgePid().orElseThrow()==raw.game().pid()
                && owner.rejection().isEmpty(),"actual original owner projection belongs to this held Game and has no cold rejection");
        StrictJson.require(owner.pending().isPresent(),"this first saved-cold bootstrap requires the actual original-owner pending candidate");
        requirePending(owner,checkpoint,lifecycle,frame);
        DriverBranch branch;
        if (lineage.bridgePid()==raw.game().pid()) { branch=DriverBranch.ACTUAL_CURRENT_GAME_HEADER; }
        else {
            StrictJson.require(owner.bindingState()==NativeColdAdoptionProjection.BindingState.PENDING_COLD_CANDIDATE
                    && owner.pending().isPresent() && owner.pending().orElseThrow().bridgePid()==lineage.bridgePid(),
                    "an old Driver header requires the actual original-owner pending candidate, never an expected episode or raw metadata inference");
            StrictJson.require(ExactRef.fromJson(actual.get("driver_ref")).equals(ExactRef.fromJson(old.get("refs").get("driver")))
                    && currentDriverIdentity.equals(FileStatIdentity.fromJson(old.get("driver_identity"),FileStatIdentity.SCHEMA)),
                    "old Game header is accepted only when the complete Driver and native identity remain exactly the qualified closed input");
            branch=DriverBranch.ACTUAL_PENDING_COLD_WITH_UNCHANGED_CLOSED_DRIVER;
        }
        StrictJson.require(old.get("unknown_requests").isArray(),"retained unknown request array");
        for (var item:old.get("unknown_requests")) {
            var unknown=StrictJson.object(item,Set.of("sequence","status","evidence_ref","replayed","cycle_credit","day_credit"));
            StrictJson.integer(unknown.get("sequence"),1,StrictJson.MAX_SAFE_INTEGER); SettledQueryClassifier.equal(unknown,"status","unknown");
            ExactRef.fromJson(unknown.get("evidence_ref")); SettledQueryClassifier.falseValue(unknown.get("replayed"));
            StrictJson.integer(unknown.get("cycle_credit"),0,0); StrictJson.integer(unknown.get("day_credit"),0,0);
        }
        long origin=StrictJson.integer(old.get("origin").get("start_date_raw"),0,frame.dateRaw());
        StrictJson.require((frame.dateRaw()-origin)%24==0,"original T0 calendar retained without new credit");
        return new Preview(branch,frame.episodeRunId(),frame.dateRaw(),(frame.dateRaw()-origin)/24,basis.reference().sha256(),
                measured.reference().sha256(),RecoveryEvidence.sha256(StrictJson.canonical(raw.toJson())));
    }
    private static void requirePending(NativeColdAdoptionProjection owner,ObjectNode checkpoint,ObjectNode lifecycle,SavedFrame frame) {
        var candidate=owner.pending().orElseThrow();
        StrictJson.require(owner.bindingState()==NativeColdAdoptionProjection.BindingState.PENDING_COLD_CANDIDATE
                && candidate.originalColdReady() && candidate.episodeCharacterId()==frame.actorCharacterId()
                && candidate.episodeRunId().equals(frame.episodeRunId()),"actual original producer reports the complete old episode pending candidate");
        StrictJson.require(sameJson(candidate.lifecycle().toJson(),lifecycle)
                && sameJson(candidate.checkpoint().toJson(),checkpoint),"actual pending full lifecycle/checkpoint exactly match the independently read original SDK qualification");
        var saved=candidate.checkpoint();
        StrictJson.require(saved.historyIndexPresence()==NativeColdAdoptionProjection.Presence.VALUE
                && saved.historyIndex().isPresent() && saved.historyIndex().orElseThrow()<=candidate.commandHistoryLength()
                && saved.episodeCharacterIdPresence()==NativeColdAdoptionProjection.Presence.VALUE
                && saved.episodeCharacterId().orElseThrow()==frame.actorCharacterId()
                && saved.episodeRunIdPresence()==NativeColdAdoptionProjection.Presence.VALUE
                && saved.episodeRunId().orElseThrow().equals(frame.episodeRunId()) && candidate.anchor().isPresent(),
                "actual pending history and episode retain all original required fields");
        var selected=candidate.anchor().orElseThrow();
        StrictJson.require(selected.index()==saved.historyIndex().orElseThrow() && selected.ok()
                && Set.of("save-checkpoint","restore-phase2-span-source-checkpoint-v1").contains(selected.command())
                && selected.checkpoint().sameOriginalIdentity(saved),"actual selected original successful history anchor matches saved identity");
        // Optional historical anchor attachments retain their original missing/null distinction.
        var anchor=selected.checkpoint();
        if(anchor.historyIndexPresence()==NativeColdAdoptionProjection.Presence.VALUE) {
            StrictJson.require(anchor.historyIndex().orElseThrow()==selected.index(),"attached original anchor history index");
        }
        if(anchor.episodeCharacterIdPresence()==NativeColdAdoptionProjection.Presence.VALUE) {
            StrictJson.require(anchor.episodeCharacterId().orElseThrow()==frame.actorCharacterId(),"attached original anchor episode actor");
        }
        if(anchor.episodeRunIdPresence()==NativeColdAdoptionProjection.Presence.VALUE) {
            StrictJson.require(anchor.episodeRunId().orElseThrow().equals(frame.episodeRunId()),"attached original anchor episode run");
        }
    }
    private static boolean sameJson(com.fasterxml.jackson.databind.JsonNode first,com.fasterxml.jackson.databind.JsonNode second) {
        return java.util.Arrays.equals(StrictJson.canonical(first,RecoveryEvidence.MAX_BYTES),StrictJson.canonical(second,RecoveryEvidence.MAX_BYTES));
    }
}
