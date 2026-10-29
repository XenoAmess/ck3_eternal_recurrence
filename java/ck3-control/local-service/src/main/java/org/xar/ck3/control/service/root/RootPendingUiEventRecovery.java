package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.application.planning.events.EventPolicies;
import org.xar.ck3.control.application.planning.events.EventReadBinding;
import org.xar.ck3.control.continuity.writer.ArchiveOriginalEvidencePort;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.continuity.writer.ImmutableArtifactStore;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.events.EventWindowCodec;
import org.xar.ck3.control.nativebridge.capabilities.events.EventWindowModels;
import org.xar.ck3.control.nativebridge.capabilities.events.EventWindowRead;
import org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionReadPublications;
import org.xar.ck3.control.nativebridge.capabilities.interactions.PendingContext;
import org.xar.ck3.control.nativebridge.capabilities.interactions.PendingContextCodec;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.events.interactionbefore.CurrentInteractionPresentation;

/** Archived preparation DATA only. Root must separately prove its canonical child, once intent,
 * original M3/cause/import lineage and private recovery issuer. No current read or action is issued. */
public final class RootPendingUiEventRecovery {
    private RootPendingUiEventRecovery(){ }
    public enum Kind { EVENT,INTERACTION }
    public record Original(ExactRef command,ExactRef originalRead,Kind kind,int instanceId,List<ExactRef> sourceOriginals) {
        public Original {
            Objects.requireNonNull(command);Objects.requireNonNull(originalRead);Objects.requireNonNull(kind);
            sourceOriginals=List.copyOf(sourceOriginals);
        }
        public List<ExactRef> originals(){var refs=new java.util.LinkedHashSet<>(List.of(command,originalRead));refs.addAll(sourceOriginals);return List.copyOf(refs);}
    }
    /** The actual Root caller supplies its identical installed contracts; constructing this DATA is
     * neither read permission nor proof that a caller-supplied contract is installed. */
    public record Inputs(ReadContract<EventPolicies.ReadPublication> eventWindow,ReadContract<PendingContext> pendingInteraction) {
        public Inputs {
            Objects.requireNonNull(eventWindow);Objects.requireNonNull(pendingInteraction);
            require(eventWindow.operation().value().equals(EventWindowRead.STEP)&&pendingInteraction.operation().value().equals(PendingContextCodec.STEP)
                    &&eventWindow.hasPureReplay()&&pendingInteraction.hasPureReplay(),"actual event/pending contracts need their explicit pure archived replay");
        }
    }
    public enum Reason { COMMAND_ORIGINAL,READ_ORIGINAL,SOURCE_ORIGINALS,READ_BINDING,PRESENTATION }
    public sealed interface Result permits Recovered,Missing { }
    public record Recovered(EventActionPreparation.PendingPrepared prepared) implements Result {
        public Recovered{Objects.requireNonNull(prepared);}
    }
    public record Missing(Reason reason,String detail,List<ExactRef> originals) implements Result {
        public Missing{Objects.requireNonNull(reason);StrictJson.text(detail);originals=List.copyOf(originals);}
    }

    public static Result recover(Inputs installed,Original retained,ArchiveOriginalEvidencePort originalFiles,Session same)throws IOException {
        Objects.requireNonNull(installed);Objects.requireNonNull(retained);Objects.requireNonNull(originalFiles);Objects.requireNonNull(same);
        // A foreign or absent writer is an authority failure, not an archived-data fallback.
        originalFiles.writer().requireSession(same);
        var archive=originalFiles.archive().withSession(same);Reason role=Reason.COMMAND_ORIGINAL;ExactRef reading=retained.command();
        try {
            byte[] originalCommand=read(originalFiles,same,reading,ActionCodec.MAX_COMMAND_BYTES);
            ActionCommand command=ActionCodec.decodeCommand(originalCommand);
            require(Arrays.equals(originalCommand,ActionCodec.encodeCommand(command))&&reading.sha256().equals(ActionCodec.bodySha256(command)),
                    "retained command lost its complete original canonical byte domain");
            require(command.origin() instanceof CommandOrigin.Gameplay,"a pending event child must retain its actual original gameplay frame");
            role=Reason.READ_ORIGINAL;reading=retained.originalRead();
            PlanningReadReceipt receipt=archive.loadRead(reading);
            require(archive.readReferenceOf(receipt).equals(reading),"retained original read reference changed");
            NativeRecordedEvidenceVerifier.requireRead(receipt,archive);
            role=Reason.SOURCE_ORIGINALS;
            require(!retained.sourceOriginals().isEmpty()&&retained.sourceOriginals().size()<=32
                    &&new HashSet<>(retained.sourceOriginals()).size()==retained.sourceOriginals().size(),"finite unique original source closure required");
            var metadata=OpportunityJson.object(command.arguments().get("pending_ui_event_source"),"original private event source metadata");
            require(metadata.members().keySet().equals(Set.of("schema","original_parent_action_id","original_parent_body_sha256","original_read","source_originals"))
                    &&text(metadata,"schema").equals("xar.pending-ui-event-source/v1"),"original private source contract is missing or malformed");
            StrictJson.text(text(metadata,"original_parent_action_id"));
            require(text(metadata,"original_parent_body_sha256").matches("[0-9a-f]{64}"),"original parent body digest missing");
            require(reference(metadata.get("original_read")).equals(retained.originalRead()),"retained source metadata changed its exact read");
            var declared=OpportunityJson.array(metadata.get("source_originals"),"original private source references").stream().map(RootPendingUiEventRecovery::reference).toList();
            require(!declared.isEmpty()&&declared.size()<=31&&new HashSet<>(declared).size()==declared.size(),"original declared source closure is absent or duplicated");
            var expected=new ArrayList<>(declared);if(!expected.contains(retained.originalRead()))expected.add(retained.originalRead());
            require(expected.equals(retained.sourceOriginals())&&declared.contains(receipt.before().binding().nativeEvidence()),
                    "once intent dropped, reordered or substituted its original private source/native-frame references");
            // These are heterogeneous originals (Driver, native packet, cause and publication), so
            // use the actual concrete archive reader rather than treating every role as JSON material.
            for(ExactRef source:declared){reading=source;read(originalFiles,same,source,ImmutableArtifactStore.MAXIMUM_ARTIFACT_BYTES);}
            role=Reason.READ_BINDING;reading=retained.originalRead();requireRead(command,receipt);
            ReadContract<?> actual=retained.kind()==Kind.EVENT?installed.eventWindow():installed.pendingInteraction();
            require(actual.contractId().equals(receipt.contractId())&&actual.operation().equals(receipt.request().operation()),
                    "original read is not this actual installed same-family contract");
            requireNativeOutbound(retained,receipt);
            var hello=requireReadOriginals(command,receipt,actual,originalFiles,same);
            role=Reason.PRESENTATION;
            EventActionPreparation.PendingPresentation presentation=retained.kind()==Kind.EVENT
                    ?event(installed,retained,command,receipt,hello)
                    :interaction(installed,retained,command,receipt,hello);
            var prepared=new EventActionPreparation.PendingPrepared(command,receipt,retained.originalRead(),presentation,retained.sourceOriginals());
            require(Arrays.equals(originalCommand,ActionCodec.encodeCommand(prepared.command())),"archived reconstruction rewrote the original once-command");
            originalFiles.writer().requireSession(same);return new Recovered(prepared);
        }catch(IOException|RuntimeException missing) {
            return new Missing(role,"original role="+role+", ref="+reading.path()+", sha256="+reading.sha256()+": "+missing.getClass().getSimpleName()+": "+String.valueOf(missing.getMessage()),retained.originals());
        }
    }

    private static EventActionPreparation.EventPresentation event(Inputs installed,Original retained,ActionCommand command,
            PlanningReadReceipt read,NativeWire.Hello received) {
        require(retained.instanceId()>0,"retained event full instance is not positive");
        EventPolicies.ReadPublication publication=installed.eventWindow().replay(read);
        var captured=new EventReadBinding.Captured(publication,read.request().operation(),read.requestId(),read.contractId(),retained.originalRead(),Optional.empty());
        require(captured.history().equals(command.arguments().get("public_event_window_read")),
                "retained command lost its complete original event READ publication/identity");
        var window=OpportunityJson.object(publication.result().get("current_event_window_context"),"original event window context");
        require(window.equals(command.arguments().get("event_window_context")),"retained event definition/root/saved scopes/options differ from original READ");
        EventWindowModels.Build build=Arrays.stream(EventWindowModels.Build.values()).filter(value->value.sha256().equalsIgnoreCase(received.gameSha256())).findFirst()
                .orElseThrow(()->new IllegalArgumentException("original event HELLO exact build unsupported"));
        var context=EventWindowCodec.decode(new RawJson(DriverJson.encode(window)),new EventWindowModels.Binding(build,
                command.before().frame().identity().nativeRevision(),command.before().frame().identity().dateRaw().intValueExact(),retained.instanceId()));
        require(context instanceof EventWindowModels.Available,"original event presentation unavailable");var available=(EventWindowModels.Available)context;
        var number=EventActionPreparation.option(command.operation());
        // Reopen the exact original selected native option. Never invoke a selector or choose the first row.
        var selected=available.options().stream().filter(option->option.nativeOptionIndex()==number.value()-1).findFirst()
                .orElseThrow(()->new IllegalArgumentException("original selected native option is absent from the retained display"));
        var originalRow=OpportunityJson.array(window.get("options"),"original displayed event rows").stream()
                .map(row->OpportunityJson.object(row,"original displayed event row"))
                .filter(row->OpportunityJson.integer(row.get("native_option_index"),"native index").equals(BigInteger.valueOf(selected.nativeOptionIndex())))
                .findFirst().orElseThrow(()->new IllegalArgumentException("retained native option lacks its original row"));
        require(originalRow.equals(command.arguments().get("selected_native_event_option")),"retained selected option fields differ from the original native display row");
        return new EventActionPreparation.EventPresentation(available,selected);
    }
    private static EventActionPreparation.InteractionPresentation interaction(Inputs installed,Original retained,ActionCommand command,PlanningReadReceipt read,NativeWire.Hello hello) {
        PendingContext actual=installed.pendingInteraction().replay(read);
        require(actual.instance().value()==retained.instanceId()&&actual.status()==PendingContext.Status.AVAILABLE,
                "original pending READ is unavailable or belongs to another instance");
        require(actual.frame().build().sha256().equalsIgnoreCase(hello.gameSha256())
                &&hello.adapterId().equals("ck3-"+actual.frame().build().version()+"-msvc-x64"),"original pending HELLO differs from its exact native context build");
        var publication=InteractionReadPublications.pending(new PlanningReadResult.Known<>(actual,read,retained.originalRead()));
        var capture=OpportunityJson.object(command.arguments().get("unhandled_interaction_fallback"),"original current primary reply capture");
        require(capture.get("context").equals(publication.get("pending_character_interaction_context")),
                "original primary reply definition/roles/legality differ from its native READ");
        var current=CurrentInteractionPresentation.requireSubmission(DriverJson.toNode(capture),command.operation().value(),retained.instanceId());
        require(current.binding().connectionGeneration().equals(read.before().binding().connectionGeneration()),"original primary reply connection differs from its READ");
        return new EventActionPreparation.InteractionPresentation(current);
    }
    private static void requireRead(ActionCommand command,PlanningReadReceipt read) {
        require(read.request().origin().equals(command.origin())&&read.request().source().equals(command.source())
                &&read.request().sessionId().equals(command.sessionId())&&read.request().deadline().equals(command.deadline())
                &&read.original().nativeOk(),"original pending READ crossed its command frame/source/session/deadline");
        var first=read.before();var second=read.after();
        require(first.paused()&&second.paused()&&first.mapReady()&&second.mapReady()&&first.playerAlive()&&second.playerAlive()
                &&first.originalBindingSha256().equals(second.originalBindingSha256()),"original pending READ changed its complete paused native binding");
        var a=first.binding();var b=second.binding();
        require(a.origin().equals(command.origin())&&b.origin().equals(command.origin())&&a.source().equals(command.source())&&b.source().equals(command.source())
                &&a.sessionId().equals(command.sessionId())&&b.sessionId().equals(command.sessionId())
                &&a.connectionGeneration().equals(b.connectionGeneration())&&a.nativeEvidence().equals(b.nativeEvidence())
                &&a.capabilityEvidence().equals(b.capabilityEvidence())&&a.operation().equals(read.request().operation())&&b.operation().equals(read.request().operation()),
                "original pending READ guards lost their identical Game/source/HELLO/operation");
    }
    private static void requireNativeOutbound(Original retained,PlanningReadReceipt receipt)throws IOException {
        var ack=receipt.original();var outbound=ack.outbound().orElseThrow(()->new IllegalArgumentException("original pending READ lacks actual outbound custody"));
        var packet=NativeWire.decodeExecuteRequest(outbound.originalPacket());
        require(packet.requestId().equals(receipt.requestId())&&outbound.requestId().equals(receipt.requestId())
                &&packet.step().equals(receipt.request().operation().value())
                &&packet.expectedRevision().equals(Optional.of(receipt.request().before().frame().identity().nativeRevision()))
                &&packet.expectedSnapshotRevision().isEmpty(),"original READ outbound request/frame/operation differs");
        var fields=DriverJson.object(packet.normalizedAdditionalFields().value(),65536);
        String id=retained.kind()==Kind.EVENT?"event_instance_id":"pending_interaction_id";
        require(fields.members().keySet().equals(Set.of(id))&&OpportunityJson.integer(fields.get(id),id).equals(BigInteger.valueOf(retained.instanceId())),
                "original native READ targeted another full event/pending instance");
    }
    private static NativeWire.Hello requireReadOriginals(ActionCommand command,PlanningReadReceipt receipt,ReadContract<?> actual,
            ArchiveOriginalEvidencePort originals,Session same)throws IOException {
        var frame=NativeWire.decode(read(originals,same,receipt.before().binding().capabilityEvidence(),NativeWire.MAXIMUM_FRAME_BYTES+4));
        require(frame instanceof NativeWire.Hello,"original pending READ lacks an actual HELLO packet");var hello=(NativeWire.Hello)frame;
        require(hello.pid()==command.before().game().pid()&&hello.connectionGeneration().equals(receipt.before().binding().connectionGeneration())
                &&hello.buildMatch()&&hello.adapterStatus().equals("ready")
                &&actual.requiredCapability().filter(hello.capabilities()::contains).isPresent(),"original pending HELLO changed its actual Game/connection/build/native capability");
        var before=NativeWire.decode(read(originals,same,receipt.before().binding().nativeEvidence(),NativeWire.MAXIMUM_FRAME_BYTES+4));
        require(before instanceof NativeWire.Snapshot,"original pending READ lacks its retained native snapshot");var snapshot=(NativeWire.Snapshot)before;
        require(snapshot.snapshotId().equals(command.before().frame().snapshotId())&&snapshot.revision().equals(command.before().frame().identity().nativeRevision()),
                "original pending READ native packet belongs to a different physical frame");
        return hello;
    }
    private static byte[] read(ArchiveOriginalEvidencePort originals,Session same,ExactRef ref,int maximum)throws IOException {
        try {
            require(ref.bytes()>0&&ref.bytes()<=maximum,"original role exceeds its explicit archive bound");
            byte[] bytes=originals.read(same,ref,maximum);
            require(bytes.length==ref.bytes()&&DriverJson.sha256(bytes).equals(ref.sha256()),"actual immutable original byte identity changed");return bytes;
        }catch(IOException|RuntimeException missing) {
            throw new IOException("exact original artifact path="+ref.path()+", sha256="+ref.sha256()+": "+String.valueOf(missing.getMessage()),missing);
        }
    }
    private static ExactRef reference(OpportunityJson.Value value){return ExactRef.fromJson(DriverJson.toNode(value));}
    private static String text(OpportunityJson.Obj value,String field){return OpportunityJson.text(value.get(field),field);}
    private static void require(boolean value,String reason){StrictJson.require(value,reason);}
}
