package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.time.Instant;
import java.util.Arrays;
import java.util.Objects;
import org.xar.ck3.control.application.checkpoint.CheckpointResult;
import org.xar.ck3.control.application.checkpoint.RestoreCheckpointService;
import org.xar.ck3.control.application.checkpoint.RestoredEpisodeOriginData;
import org.xar.ck3.control.application.checkpoint.SavedAttachmentSourceStore;
import org.xar.ck3.control.application.checkpoint.SavedCheckpointMaterial;

/** Genuine-Root integration consumer. It constructs no Managed session, private binding, cycle proof, file or SAVE. */
public final class RootOrdinaryRestoreCustodyAssertions {
    private RootOrdinaryRestoreCustodyAssertions(){ }
    public record Published(RootApplicationSession first,RootApplicationSession second,
            RestoreCheckpointService.RestoreBinding firstBinding,RestoreCheckpointService.RestoreBinding secondBinding){
        public Published {Objects.requireNonNull(first);Objects.requireNonNull(second);Objects.requireNonNull(firstBinding);Objects.requireNonNull(secondBinding);}
    }
    @FunctionalInterface public interface ActualRestoreCheck {
        void require(RootApplicationSession actualRestored,RestoreCheckpointService.RestoreBinding actualBinding,
                Instant originalDeadline)throws IOException,InterruptedException;
    }
    public static Published restorePublicSaveTwice(RootApplicationSession original,RootSessionAccess actualAccess,
            CheckpointResult.Confirmed actualPublicSave,RootCheckpointPublicCalls.Request request,
            Instant firstDeadline,Instant secondDeadline)throws IOException,InterruptedException {
        return restorePublicSaveTwice(original,actualAccess,actualPublicSave,request,firstDeadline,secondDeadline,
                (actual,binding,deadline)->{ });
    }
    /** The integration fixture checks each genuine publication before the same public source is restored again. */
    public static Published restorePublicSaveTwice(RootApplicationSession original,RootSessionAccess actualAccess,
            CheckpointResult.Confirmed actualPublicSave,RootCheckpointPublicCalls.Request request,
            Instant firstDeadline,Instant secondDeadline,ActualRestoreCheck actualCheck)throws IOException,InterruptedException {
        Objects.requireNonNull(original);Objects.requireNonNull(actualAccess);Objects.requireNonNull(actualPublicSave);
        Objects.requireNonNull(actualCheck);require(actualAccess.current()==original,"ordinary restore must start from the actual access owner's current Root");actualAccess.requireHost(original.hostForPublication());
        var firstCall=RootPublicSaveMaterialAssertions.restoreAndRequirePublicPair(original,actualAccess,actualPublicSave,request,firstDeadline);
        var first=restored(firstCall);var firstRoot=firstCall.published().orElseThrow();
        require(actualAccess.current()==firstRoot,"first restore must publish this access owner's exact current Root");actualAccess.requireHost(firstRoot.hostForPublication());requireActualReboundOrigin(firstRoot,first.binding());
        actualCheck.require(firstRoot,first.binding(),firstDeadline);
        var source=first.binding().savedMaterial();
        require(source instanceof SavedAttachmentSourceStore.SavedMaterial,"genuine public SAVE did not retain ordinary material");
        var firstOwned=retained(original,firstRoot,source);
        var secondCall=actualAccess.restoreCheckpointPublic(request,secondDeadline);
        var second=restored(secondCall);var secondRoot=secondCall.published().orElseThrow();
        actualAccess.requireHost(secondRoot.hostForPublication());requireActualReboundOrigin(secondRoot,second.binding());
        actualCheck.require(secondRoot,second.binding(),secondDeadline);
        require(firstRoot.isRetired()&&!secondRoot.isRetired()&&secondRoot.hasInstalledHost()
                &&actualAccess.current()==secondRoot&&firstRoot.writer()==original.writer()&&secondRoot.writer()==original.writer()&&firstRoot.archive()==original.archive()&&secondRoot.archive()==original.archive()
                &&second.binding().savedMaterial()==firstOwned
                &&second.lifecycleAck().previous().equals(firstRoot.identity().game())
                &&second.lifecycleAck().replacement().equals(secondRoot.identity().game())
                &&!secondRoot.identity().game().equals(firstRoot.identity().game()),
                "second public restore did not consume the first replacement's actual privately reopened ordinary material");
        var secondOwned=retained(firstRoot,secondRoot,source);
        require(secondOwned.session().equals(source.session())&&secondOwned.sourceSemantic().equals(source.sourceSemantic())
                &&!secondOwned.session().equals(secondRoot.identity())
                &&!secondOwned.sourceSemantic().frame().game().equals(secondRoot.identity().game())
                &&second.binding().semantic().frame().game().equals(secondRoot.identity().game()),
                "saved Driver/SEM/session were relabelled as the restored Game");
        return new Published(firstRoot,secondRoot,first.binding(),second.binding());
    }
    /** Uses genuine saved material, the actual replacement and the following installed FamilyDomainSource. */
    public static void requireActualFamilyRebound(RootApplicationSession actual,
            RestoreCheckpointService.RestoreBinding binding,RootInstalledCatalog catalog,Instant deadline)
            throws IOException,InterruptedException {
        Objects.requireNonNull(actual);Objects.requireNonNull(binding);Objects.requireNonNull(catalog);
        var context=catalog.context();
        require(context.actions()==actual && context.writer()==actual.writer() && binding.session().equals(actual.identity()),
                "Family restore check requires the exact published replacement Root");
        actual.withPublicPlanning(deadline,(observed,same)->{
            observed.assertCurrent(same);String head=same.head().digest();
            var request=RootPlanningInputsFactory.publicRequest(observed,same,deadline);
            var source=context.restorationOriginal(same);var origin=binding.requireReboundOrigin(same);origin.requireOriginal(same);
            require(source.material().kind()==SavedCheckpointMaterial.Kind.ORDINARY
                    &&source.material().witness().equals(binding.savedMaterial().witness())
                    &&origin==context.requireRestoredOrigin(same),"Family following read lost its genuine ordinary SAVE/restore source");
            var data=origin.evidence();
            var read=catalog.remainingDomains().family().installer().documents(request);
            require(read instanceof org.xar.ck3.control.application.planning.family.FamilyPorts.KnownDocuments,
                    "following installed FamilyDomainSource rejected the actual replacement owner: "+read);
            var documents=((org.xar.ck3.control.application.planning.family.FamilyPorts.KnownDocuments)read).documents();
            var slots=java.util.List.of(org.xar.ck3.control.continuity.writer.DomainBodies.Slot.FAMILY,
                    org.xar.ck3.control.continuity.writer.DomainBodies.Slot.CHILD_MATRILINEAL,
                    org.xar.ck3.control.continuity.writer.DomainBodies.Slot.DEFAULT_MARRIAGE);
            var bodies=java.util.List.of(documents.family(),documents.matrilineal(),documents.childDefault());
            var episode=new org.xar.ck3.control.application.planning.family.FamilyNextEpisodeMigration.Episode(
                    request.before().frame().episodeRunId(),request.before().frame().identity().player());
            var priorIdentity=new org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity(
                    data.previousOwner().machineId(),data.previousOwner().game(),request.before().frame(),request.before().observationVersion());
            var oldRequest=new org.xar.ck3.control.application.planning.PlanningRequest(priorIdentity,request.source(),
                    data.previousOwner().sessionId(),request.deadline(),request.observations());
            for(int index=0;index<slots.size();index++) {
                var slot=slots.get(index);
                var previous=org.xar.ck3.control.continuity.writer.DomainBodies.reference(source.attachmentHead(),slot)
                        .orElseThrow(()->new IOException("actual restore source has no complete Family body: "+slot));
                var saved=org.xar.ck3.control.continuity.writer.DomainBodies.reference(source.originalSavedHead(),slot)
                        .orElseThrow(()->new IOException("actual SAVE source has no complete Family body: "+slot));
                var pin=same.capturePin(previous.payload(),org.xar.ck3.control.continuity.ContinuityJson.DOMAIN_MAX_BYTES);
                require(pin.identity().equals(previous.identity()),"actual pre-restore Family body changed native identity");
                var before=org.xar.ck3.control.application.driver.DriverJson.toNode(
                        org.xar.ck3.control.application.planning.family.FamilyDomainSource.validate(slot,same.readPinned(pin,
                                org.xar.ck3.control.continuity.ContinuityJson.DOMAIN_MAX_BYTES)));
                same.verifyPin(pin);
                var after=org.xar.ck3.control.application.driver.DriverJson.toNode(bodies.get(index));
                String history=org.xar.ck3.control.application.planning.family.FamilyOrdinaryRestoreMigration.HISTORY;
                require(after.path(history).isArray()&&after.path(history).size()==(before.has(history)?before.path(history).size():0)+1,
                        "ordinary Family restoration must append one retained source entry");
                for(int entry=0;before.has(history)&&entry<before.path(history).size();entry++)
                    require(before.path(history).get(entry).equals(after.path(history).get(entry)),"a repeat restoration lost earlier complete Family history");
                var latest=after.path(history).get(after.path(history).size()-1);
                var transition=org.xar.ck3.control.application.planning.family.FamilyOrdinaryRestoreMigration.Transition.fromJson(latest.get("transition"));
                require(transition.savedOwner().equals(data.savedOwner())&&transition.beforeOwner().equals(data.previousOwner())
                        &&transition.afterOwner().equals(actual.identity())&&transition.episode().equals(episode)
                        &&transition.savedMaterial().equals(source.material().reference())&&transition.restorationBasis().equals(source.basis())
                        &&transition.savedBody().equals(saved.payload())&&transition.previousBody().equals(previous.payload()),
                        "Family restore source roles, original body pins or exact owner changed");
                for(String[] marker:java.util.List.of(new String[]{
                        org.xar.ck3.control.application.planning.family.FamilyNaturalEpisodeMigration.FIELD,"previous_natural_episode_binding"},
                        new String[]{org.xar.ck3.control.application.planning.family.FamilyNextEpisodeMigration.FIELD,"previous_next_episode_binding"}))
                    require(Objects.equals(before.get(marker[0])==null?com.fasterxml.jackson.databind.node.NullNode.instance:before.get(marker[0]),
                            latest.get(marker[1])),"ordinary restoration lost the complete original Family marker");
                for(String field:java.util.List.of("pending","resolved","episode_history"))
                    require(Objects.equals(before.get(field),after.get(field)),"ordinary restoration changed complete active Family commitment or episode history: "+field);
                var previousBusiness=((com.fasterxml.jackson.databind.node.ObjectNode)before).deepCopy();
                var currentBusiness=((com.fasterxml.jackson.databind.node.ObjectNode)after).deepCopy();
                for(String field:java.util.List.of(history,
                        org.xar.ck3.control.application.planning.family.FamilyNaturalEpisodeMigration.FIELD,
                        org.xar.ck3.control.application.planning.family.FamilyNextEpisodeMigration.FIELD)) {
                    previousBusiness.remove(field);currentBusiness.remove(field);
                }
                require(previousBusiness.equals(currentBusiness),"ordinary restoration changed unknown Family business extensions");
                var body=bodies.get(index);
                org.xar.ck3.control.application.planning.family.FamilyOrdinaryRestoreMigration.requireCurrent(body,request);
                org.xar.ck3.control.application.planning.family.FamilyNextEpisodeMigration.requireCurrent(body,request);
                boolean oldRefused=false;
                try {
                    org.xar.ck3.control.application.planning.family.FamilyOrdinaryRestoreMigration.requireCurrent(body,oldRequest);
                    org.xar.ck3.control.application.planning.family.FamilyNextEpisodeMigration.requireCurrent(body,oldRequest);
                }catch(IllegalArgumentException expected){oldRefused=true;}
                require(oldRefused,"Family restored body still qualifies its replaced physical owner");
                var roundTrip=org.xar.ck3.control.application.planning.family.FamilyDomainSource.validate(slot,
                        org.xar.ck3.control.application.driver.DriverJson.encode(body));
                require(body.equals(roundTrip),"Family active commitment/marker JSON round trip changed its domain");
            }
            observed.assertCurrent(same);origin.requireOriginal(same);
            require(head.equals(same.head().digest()),"following Family read changed the canonical writer or replayed an action");
            return null;
        });
    }

    private static SavedAttachmentSourceStore.SavedMaterial retained(RootApplicationSession previous,
            RootApplicationSession current,SavedCheckpointMaterial original)throws IOException {
        require(previous.savedMaterials()!=current.savedMaterials()
                &&previous.savedMaterials().ordinaryStore()!=current.savedMaterials().ordinaryStore(),
                "ordinary repeat restore must exercise distinct actual per-Game aggregates");
        return current.writer().locked(same->{
            String head=same.head().digest();
            var actual=current.savedMaterials().currentPhysical(same,original.pair());current.savedMaterials().requireOwn(actual);
            require(actual instanceof SavedAttachmentSourceStore.SavedMaterial,"reopened material changed to FIRST");
            actual.requireRetained(same);actual.requirePhysical(same);
            require(actual.pair().equals(original.pair())&&actual.witness().equals(original.witness())
                    &&actual.session().equals(original.session())&&actual.sourceSemantic().equals(original.sourceSemantic())
                    &&actual.originalHeadDigest().equals(original.originalHeadDigest())
                    &&Arrays.equals(actual.savedDriver().encode(),original.savedDriver().encode())
                    &&head.equals(same.head().digest()),"ordinary reopen changed original source, FileID, history or canonical head");
            return (SavedAttachmentSourceStore.SavedMaterial)actual;
        });
    }
    /** Requires actual admitted objects; a foreign service cannot turn their references into new private custody. */
    public static void requireForeignServiceRefused(RootApplicationSession actualRestored,
            RestoreCheckpointService.RestoreBinding actualBinding,RestoreCheckpointService foreignService)throws IOException {
        actualRestored.writer().locked(same->{
            String head=same.head().digest();boolean refused=false;
            try {foreignService.reopenOrdinaryMaterial(same,actualBinding,actualRestored.savedMaterials(),
                    actualBinding.session(),actualBinding.semantic());}
            catch(IOException|IllegalArgumentException expected){refused=true;}
            boolean originRefused=false;
            try {foreignService.requireReboundOrigin(same,actualBinding);}
            catch(IOException|IllegalArgumentException expected){originRefused=true;}
            require(refused&&originRefused&&head.equals(same.head().digest()),"foreign service acquired original ordinary or actual-restoration custody");return null;
        });
    }
    /** Requires the genuine SAVE-to-LOAD result; no DATA constructor can supply the private origin. */
    public static RestoreCheckpointService.ReboundOrigin requireActualReboundOrigin(RootApplicationSession actualRestored,
            RestoreCheckpointService.RestoreBinding actualBinding)throws IOException {
        return actualRestored.writer().locked(same->{
            String head=same.head().digest();var origin=actualBinding.requireReboundOrigin(same);origin.requireOriginal(same);
            require(origin==actualBinding.requireReboundOrigin(same),"actual private restored origin was replaced");
            var data=origin.evidence();
            require(data.restoredOwner().equals(actualRestored.identity())&&data.restoredOwner().equals(actualBinding.session())
                    &&data.savedOwner().equals(actualBinding.savedMaterial().session())&&data.pair().equals(actualBinding.pair())
                    &&data.materialWitness().equals(actualBinding.savedMaterial().witness())
                    &&data.originalSavedHeadDigest().equals(actualBinding.savedMaterial().originalHeadDigest())
                    &&data.originalRestoredSemantic().equals(actualBinding.semantic())
                    &&data.attachmentEventIdentity().equals(actualBinding.attachment().eventIdentity())
                    &&!data.previousOwner().game().equals(data.restoredOwner().game())
                    &&!data.previousOwner().sessionId().equals(data.restoredOwner().sessionId())
                    &&origin.newSavedDayCredit()==0&&origin.newCycleCredit()==0,
                    "actual restored origin lost saved identity, old/new Game/transport, original reducer or zero new-credit roles");
            require(Arrays.equals(data.encode(),RestoredEpisodeOriginData.decode(data.encode()).encode()),"actual restore-origin DATA failed exact JSON round trip");
            // Explicit unqualified DATA variation covers the advertised 1MiB wire lane, above StrictJson's 64KiB default.
            // It is never passed to an issuer or converted into the original private restoration object.
            var large=dataRow(data.encode());large.put("request_id","origin-data-"+"x".repeat(32000));
            ((com.fasterxml.jackson.databind.node.ObjectNode)large.get("previous_owner")).put("session_id","previous-data-"+"y".repeat(32000));
            byte[] largeBytes=org.xar.ck3.control.contracts.StrictJson.canonical(large,RestoredEpisodeOriginData.MAXIMUM_BYTES);
            require(largeBytes.length>org.xar.ck3.control.contracts.StrictJson.INPUT_MAX_BYTES
                    &&Arrays.equals(largeBytes,RestoredEpisodeOriginData.decode(largeBytes).encode()),
                    "explicit restoration DATA budget accidentally used the default 64KiB JSON lane");
            var numeric=dataRow(data.encode());
            numeric.put("restored_connection_generation",1);
            requireDataRefused(org.xar.ck3.control.contracts.StrictJson.canonical(numeric,RestoredEpisodeOriginData.MAXIMUM_BYTES));
            var missing=dataRow(data.encode());
            missing.remove("lifecycle_evidence");requireDataRefused(org.xar.ck3.control.contracts.StrictJson.canonical(missing,RestoredEpisodeOriginData.MAXIMUM_BYTES));
            var extra=dataRow(data.encode());
            extra.put("qualified",true);requireDataRefused(org.xar.ck3.control.contracts.StrictJson.canonical(extra,RestoredEpisodeOriginData.MAXIMUM_BYTES));
            var wrongId=dataRow(data.encode());
            ((com.fasterxml.jackson.databind.node.ObjectNode)wrongId.get("lifecycle_evidence").get("native_identity")).put("file_id",9007199254740993L);
            requireDataRefused(org.xar.ck3.control.contracts.StrictJson.canonical(wrongId,RestoredEpisodeOriginData.MAXIMUM_BYTES));
            origin.requireOriginal(same);require(head.equals(same.head().digest()),"actual restored-origin check changed the original canonical head");return origin;
        });
    }
    private static void requireDataRefused(byte[] invalid)throws IOException {
        boolean refused=false;try {RestoredEpisodeOriginData.decode(invalid);}catch(IllegalArgumentException expected){refused=true;}
        require(refused,"wrong fields or JSON identity types were accepted as restoration-origin DATA");
    }
    private static com.fasterxml.jackson.databind.node.ObjectNode dataRow(byte[] bytes) {
        var parsed=org.xar.ck3.control.contracts.StrictJson.parse(bytes,RestoredEpisodeOriginData.MAXIMUM_BYTES);
        if(!(parsed instanceof com.fasterxml.jackson.databind.node.ObjectNode row))throw new IllegalArgumentException("restoration DATA object required");
        return row;
    }
    private static RestoreCheckpointService.Restored restored(RootCheckpointPublicCalls.RestoreCall call)throws IOException {
        if(!(call.actual() instanceof RestoreCheckpointService.Restored actual))
            throw new IOException("MISSING_ACTUAL_MANAGED_RESTORE: retain UNKNOWN/rejection; no second request or passed regression: "+call.actual());
        require(call.published().isPresent(),"genuine replacement did not publish its Root");return actual;
    }
    private static void require(boolean condition,String message){if(!condition)throw new AssertionError(message);}
}
