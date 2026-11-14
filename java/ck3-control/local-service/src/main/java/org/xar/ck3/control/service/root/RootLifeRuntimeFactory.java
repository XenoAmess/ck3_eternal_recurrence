package org.xar.ck3.control.service.root;

import static org.xar.ck3.control.contracts.StrictJson.require;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.Collections;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.advance.AdvanceObservationPort;
import org.xar.ck3.control.application.advance.ClockStatusRead;
import org.xar.ck3.control.nativebridge.NativeFreshSnapshotPort;
import org.xar.ck3.control.reconciliation.LateOutcome.Status;
import java.time.Instant;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.ReadContract;
import org.xar.ck3.control.application.action.RootExecutableBindings;
import org.xar.ck3.control.application.advance.LifeAdvanceCommands;
import org.xar.ck3.control.application.advance.LifeAdvanceComposite;
import org.xar.ck3.control.application.advance.LifePostResumePauseCleanupProof;
import org.xar.ck3.control.application.advance.LifePostResumePauseCleanupEvidence;
import org.xar.ck3.control.application.advance.PostExitCleanupNoEffectProof;
import org.xar.ck3.control.application.advance.NoEffectReconciliationToken;
import org.xar.ck3.control.application.advance.LifeAdvanceRootReplay;
import org.xar.ck3.control.application.advance.ProductionAdvanceReadiness;
import org.xar.ck3.control.application.advance.PendingUiLifeAdvance;
import org.xar.ck3.control.application.advance.AdvanceReadiness;
import org.xar.ck3.control.application.history.DriverHistoryAccess;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.ExactRef;

/** Concrete Life assembly over the original Root and the one battle-owned clock infrastructure.
 * Installation is pure construction before adoption; actual Driver/collector objects resolve only when called.
 */
public final class RootLifeRuntimeFactory {
    private RootLifeRuntimeFactory() { }

    public record Sources(ExactRef compositeImplementation,ExactRef commandProducer,
            ExactRef resultDecoder,ExactRef archivedVerifier) {
        public Sources {
            for(ExactRef ref:List.of(compositeImplementation,commandProducer,resultDecoder,archivedVerifier))
                require(ref.bytes()>0,"actual complete Life implementation/command/result/replay source required");
        }
    }

    /** One Prepared binds the same actual infrastructure and settings for every physical Root context. */
    public static final class Prepared {
        private final Sources sources;
        private final RootAdvanceRuntimeFacts.Settings settings;
        private final RootAdvanceInfrastructureFactory.Prepared infrastructure;
        private final Map<RootRuntimeContext,Installed> installed=new IdentityHashMap<>();
        private final Set<RootRuntimeContext> entered=Collections.newSetFromMap(new IdentityHashMap<>());

        public Prepared(Sources actualSources,RootAdvanceRuntimeFacts.Settings actualSettings,
                RootAdvanceInfrastructureFactory.Prepared sameInfrastructure) {
            sources=Objects.requireNonNull(actualSources);settings=Objects.requireNonNull(actualSettings);
            infrastructure=Objects.requireNonNull(sameInfrastructure);
        }

        public List<ExactRef> requiredSources() {
            var refs=new java.util.LinkedHashSet<ExactRef>();
            refs.addAll(List.of(sources.compositeImplementation(),sources.commandProducer(),sources.resultDecoder(),sources.archivedVerifier(),settings.original()));
            refs.addAll(infrastructure.requiredSources());return List.copyOf(refs);
        }

        public synchronized Installed install(RootRuntimeContext context,RootCrownRetryRuntime.Prepared sameRetry)throws IOException {
            Objects.requireNonNull(context);Objects.requireNonNull(sameRetry);
            require(context.core()==sameRetry.core(),"Life and Crown retry must retain the identical original Core");
            Installed existing=installed.get(context);
            if(existing!=null) {
                require(existing.retry==sameRetry,"same physical Life context cannot replace its Crown producer");
                return existing;
            }
            require(installed.size()<64 && !entered.contains(context),
                    "physical Life installation exceeded its bound or an earlier partial construction remains unresolved");
            entered.add(context);
            var candidate=new Installed(context,sameRetry,sources,settings,infrastructure);
            installed.put(context,candidate);return candidate;
        }
    }

    public static final class Installed {
        private final RootRuntimeContext context;
        private final RootCrownRetryRuntime.Prepared retry;
        private final DriverHistoryAccess history;
        private final RootAdvanceRuntimeFacts runtimeFacts;
        private final ProductionAdvanceReadiness readiness;
        private final PendingUiLifeAdvance.Scope pendingUiScope;
        private final AdvanceReadiness.Port scopedReadiness;
        private final RootAdvanceInfrastructureFactory.Installed infrastructure;
        private final LifeAdvanceRootReplay replay;
        private final LifeAdvanceComposite composite;
        private final LifeAdvanceCommands commands;
        private final RootDomainInstallation installation;

        private Installed(RootRuntimeContext context,RootCrownRetryRuntime.Prepared retry,Sources sources,
                RootAdvanceRuntimeFacts.Settings settings,RootAdvanceInfrastructureFactory.Prepared clockInfrastructure)throws IOException {
            this.context=context;this.retry=retry;
            // Resolve the actual later-adopted authority on every invocation. No dummy
            // Driver, synthetic Known or replacement repository can enter this graph.
            history=new DriverHistoryAccess(()->context.adopted().authority(),context.archive());
            runtimeFacts=new RootAdvanceRuntimeFacts(context,retry.due(),retry.retainedProof(),settings);
            readiness=new ProductionAdvanceReadiness(history,runtimeFacts,retry.due(),this::borrowedSession,runtimeFacts);
            pendingUiScope=new PendingUiLifeAdvance.Scope(context::borrowedSession);
            scopedReadiness=pendingUiScope.readiness(readiness);
            infrastructure=clockInfrastructure.install(context,scopedReadiness,pendingUiScope);
            replay=new LifeAdvanceRootReplay(RootAdvanceInfrastructureFactory.freshFrameLoader(context.frameLoader()),context.core()::operatorQuarantineSource,this::borrowedSession,
                    (head,cursor,archive)->verifyQualifiedPreparedCursor(context,head,cursor,archive),
                    (head,parent,archive)->verifyQualifiedPreparedParent(context,head,parent,archive));
            composite=new LifeAdvanceComposite(infrastructure.observations(),scopedReadiness,infrastructure.timeline(),
                    infrastructure.statuses(),context.core().actions(),context.archive(),context.clock(),replay,
                    new LifeAdvanceComposite.PreparedCleanupReads() {
                        @Override public LifeAdvanceComposite.CancellationRead read(ActionCommand parent,CompositeExecution execution,
                                List<ActionReceipt> children,Instant deadline) {
                            return readCancellationStatus(parent,execution,children,deadline);
                        }
                        @Override public void requireQualifiedBackend(ActionReceipt original,List<ActionReceipt> canonicalOriginalChildren) {
                            requireCurrentPostResumeBackend(original,canonicalOriginalChildren);
                        }
                        @Override public org.xar.ck3.control.application.advance.PreparedCleanupParentProjection projectPreparedParent(
                                LifeAdvanceComposite actual,org.xar.ck3.control.application.advance.LifePreparedCleanupContinuation token,
                                org.xar.ck3.control.application.advance.PreparedCleanupEvidence.Prepared prepared,
                                org.xar.ck3.control.application.advance.PreparedCleanupEvidence.PostAckCaptured captured,ExactRef captureReference){
                            require(actual==composite,"prepared parent projection belongs to another actual source");
                            return projectPreparedParentOriginals(token,prepared,captured,captureReference);
                        }
                        @Override public <T>T withPreparedCleanupScope(LifeAdvanceComposite actual,
                                org.xar.ck3.control.application.advance.LifePreparedCleanupContinuation token,
                                org.xar.ck3.control.application.advance.PreparedCleanupEvidence.Prepared prepared,
                                CompositeActionPort.PreparedCleanupWork<T> work)throws IOException,InterruptedException {
                            require(actual==composite,"prepared callback belongs to another installed Life source");
                            return RootPreparedCleanupScope.run(context,Installed.this,actual,token,prepared,work);
                        }
                        @Override public void requireQualifiedReservedNoEffectBackend(org.xar.ck3.control.application.advance.ReservedPreparedCleanupNoEffectProof.Verified proof){
                            RootLifeRuntimeFactory.requireQualifiedReservedNoEffectBackend(context,proof);
                        }
                        @Override public void requireQualifiedPreparedNoEffectBackend(org.xar.ck3.control.application.advance.PreparedCleanupNoEffectProof.Verified proof) {
                            RootLifeRuntimeFactory.requireQualifiedPreparedNoEffectBackend(context,proof);
                        }
                        @Override public void requireQualifiedNoEffectBackend(PostExitCleanupNoEffectProof.Verified proof) {
                            requireQualifiedPostExitNoEffect(context,proof);
                        }
                    });
            commands=new LifeAdvanceCommands(composite,pendingUiScope);
            var binding=new RootExecutableBindings.CompositeBinding(composite,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,
                    Optional.empty(),sources.compositeImplementation(),sources.resultDecoder());
            var archived=List.of(replay.binding(new OperationKey("life-advance"),sources.archivedVerifier()),
                    replay.binding(new OperationKey("life-advance-one-day"),sources.archivedVerifier()));
            installation=new RootDomainInstallation("shared-actual-life-advance",List.of(),List.of(),List.of(),List.of(),
                    List.of(binding),archived,List.of(),List.of(),List.of(),List.of(),Set.of(),List.of(),List.of(),List.of(),List.of(),List.of());
        }
        /** Private, source-owned binding to the one independently reviewed installed Native worker lifetime.
         * The configured DLL is only a consistency check. Qualification additionally requires all pinned
         * real loaded/continuous-FileID, same-Game owner continuity and exact-machine-code originals below.
         * Ordinary Java attach/reconnect is permitted. Runtime must retain exclusive ownership and must
         * not re-inject, LoadLibrary, reinitialize, Install, Stop or Start the Native worker in this lifetime.
         */
        private void requireCurrentPostResumeBackend(ActionReceipt original,List<ActionReceipt> canonicalOriginalChildren) {
            try {
                canonicalOriginalChildren=List.copyOf(canonicalOriginalChildren);
                var retainedChildren=canonicalOriginalChildren;
                context.requireActiveGame();
                requirePostResumeBackendSubject(original,context.game().generation(),context.game().machineId(),
                        context.game().sessionId(),context.source(),context.game().launchPlan().sources().review().bridgeDll());
                // Reopen the complete actual canonical original receipts, not only their command bodies.
                context.withSession(same->{
                    var archive=context.archive().withSession(same);
                    var original1929=new ExactRef("D:\\ck3-state\\ck3-java-resume91_offline04_20261111T071454Z\\business\\continuity\\artifacts\\04de9425d387b28ceb616d640b450d4143ac7bf2fc902b156205c2ba65f61e67.bin",
                            6739,"04de9425d387b28ceb616d640b450d4143ac7bf2fc902b156205c2ba65f61e67");
                    var anchor=archive.loadReceipt(original1929);
                    var anchorRef=archive.receiptReferenceOf(anchor);
                    require(anchorRef.bytes()==original1929.bytes()&&anchorRef.sha256().equals(original1929.sha256())
                            &&anchor.version()==1&&anchor.sequence()==1929&&anchor.state() instanceof ActionState.CompositeUnknown
                            &&original.command().equals(anchor.command())
                            &&((ActionState.CompositeUnknown)original.state()).execution().equals(((ActionState.CompositeUnknown)anchor.state()).execution()),
                            "backend qualification changed the original1929 anchor or its immutable command/execution prefix");
                    // A genuine later read-only UNKNOWN may add diagnostics/evidence. The source issuer
                    // still requires it to be the actual latest canonical receipt; this anchor is never rewritten.
                    var expected=List.of(
                            new ExactRef("D:\\ck3-state\\ck3-java-resume91_offline04_20261111T071454Z\\business\\continuity\\artifacts\\f42a94b5be9efc2c19d4b01d237b02cda9b09f6527fb38aa03fc070537fd88a8.bin",7382,"f42a94b5be9efc2c19d4b01d237b02cda9b09f6527fb38aa03fc070537fd88a8"),
                            new ExactRef("D:\\ck3-state\\ck3-java-resume91_offline04_20261111T071454Z\\business\\continuity\\artifacts\\24e7e34f8fa8b8ce52f2dd966ba5fb687caf368ea2ff97d5d74bf8a2fd1d9399.bin",7350,"24e7e34f8fa8b8ce52f2dd966ba5fb687caf368ea2ff97d5d74bf8a2fd1d9399"),
                            new ExactRef("D:\\ck3-state\\ck3-java-resume91_offline04_20261111T071454Z\\business\\continuity\\artifacts\\76945824decaaea3cf8c0393880c56faff97cf587089cc3508a347f0fb81a690.bin",7879,"76945824decaaea3cf8c0393880c56faff97cf587089cc3508a347f0fb81a690"));
                    var execution=((ActionState.CompositeUnknown)original.state()).execution();
                    require(retainedChildren.size()==expected.size(),"backend qualification requires its complete already-canonical original prefix");
                    for(int index=0;index<expected.size();index++) {
                        // The actual Life source just obtained this immutable prefix from its canonical reader,
                        // or retained it in this identical source's private token. Reopen its full originals;
                        // do not repeat three complete current ACTION-history walks inside every fresh guard.
                        var child=retainedChildren.get(index);var binding=execution.children().get(index);
                        require(child.command().actionId().equals(binding.actionId())&&child.bodySha256().equals(binding.bodySha256())
                                &&child.settled()&&archive.receiptReferenceOf(child).equals(expected.get(index)),
                                "backend qualification changed an actual immutable ARM/resume/pause receipt");
                        if(index==0) {
                            var settled=(ActionState.Settled)child.state();
                            var arm=(ActionState.ControlApplied)settled.settlement();
                            require(ClockStatusRead.decode(arm.read().original()).generation().decimal().equals("79"),
                                    "backend qualification belongs only to original generation79");
                        }
                    }
                    return null;
                });
                for(var ref:postResumeBackendOriginals())verifyPostResumeBackendOriginal(ref);
                context.requireActiveGame();
            } catch(IOException unavailable) {throw new UncheckedIOException("exact loaded post-resume cleanup backend qualification unavailable",unavailable);}
        }
        private org.xar.ck3.control.application.advance.PreparedCleanupParentProjection projectPreparedParentOriginals(
                org.xar.ck3.control.application.advance.LifePreparedCleanupContinuation token,
                org.xar.ck3.control.application.advance.PreparedCleanupEvidence.Prepared prepared,
                org.xar.ck3.control.application.advance.PreparedCleanupEvidence.PostAckCaptured captured,ExactRef captureReference){
            try{return context.withSession(same->{
                requireContext(context);require(context.actions() instanceof RootApplicationSession,"actual prepared projection session is absent");
                ((RootApplicationSession)context.actions()).requirePreparedCleanupScopeOwner(context,this,composite);
                RootPreparedCleanupScope.requireClosedForProjection();
                var archive=context.archive().withSession(same);
                org.xar.ck3.control.application.advance.PreparedCleanupEvidence.requirePostAckCaptured(captured);
                verifyPreparedNativeCapture(prepared,captured,archive);
                var actual=captured.afterFrame();
                // Same real accepted SDK object. No READ, current deadline or
                // reconstructed equal packet may replace this live occurrence.
                var complete=context.adopted().authority().withFrozenRawObservation(actual,same,frozen->{
                    var nativeOriginal=archive.preserveNativeFrame(actual);
                    var projected=context.core().observationAssembler().assemble(actual,frozen.facts(),nativeOriginal);
                    if(projected instanceof org.xar.ck3.control.application.driver.DriverObservationAssembler.Incomplete missing)
                        throw new IllegalStateException("incomplete captured prepared parent projection: "+String.join(",",missing.reasons()));
                    return (org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete)projected;
                });
                ObservationProvenance.FreshSnapshotBasis basis;
                if(org.xar.ck3.control.application.advance.PreparedCleanupSuccessorEvidence.isSuccessor(prepared)){
                    var predecessor=(ActionState.PreparedCleanupNoEffectConfirmed)prepared.children().getLast().state();
                    basis=new ObservationProvenance.PreparedCleanupSuccessorWatch(prepared.parentReference(),prepared.childReferences().getLast(),
                            predecessor.proofReference(),prepared.reference(),captureReference);
                }else basis=new ObservationProvenance.PreparedCleanupWatch(prepared.parentReference(),prepared.reference(),captureReference);
                var provenance=new ObservationProvenance.FreshSnapshotQuery(captured.freshSnapshotAck().requestId(),archive.referenceOf(captured.freshSnapshotAck()),
                        captured.snapshotReceived(),basis);
                RootAdvanceInfrastructureFactory.verifyFreshSnapshotQuery(provenance,complete,archive);
                var ending=new AdvanceObservationPort.Frame(complete.identity(),complete.source(),complete.sessionId(),complete.semantic(),provenance,
                        complete.observedAt(),complete.originalEvidence());
                var starting=replay.read(prepared.parentReceipt().command(),((ActionState.CompositeUnknown)prepared.parentReceipt().state()).execution().guard(),archive).orElseThrow();
                return org.xar.ck3.control.application.advance.PreparedCleanupParentProjection.preserve(prepared,captureReference,starting,ending,archive,replay);
            });}catch(IOException unavailable){throw new UncheckedIOException("actual prepared captured Frame projection unavailable",unavailable);}
            finally{java.lang.ref.Reference.reachabilityFence(captured.afterFrame());}
        }
        /** Imports only the accepted post-C6 observations. Short tokens are not minted during slow preparation. */
        public ExactRef reservedPreparedCleanupNoEffectProof(Instant deadline)throws IOException {
            requireContext(context);context.requireActiveGame();
            var reference=context.withSession(same->{
                var archive=context.archive().withSession(same);
                for(var original:reservedNoEffectOriginals())verifyPostResumeBackendOriginal(original);
                var parent=archive.loadReceipt(new ExactRef("D:\\ck3-state\\ck3-java-resume91_offline04_20261111T071454Z\\business\\continuity\\artifacts\\117ae99b509327ed04b4b7ca04e43de1564afeb1805eb063757e5a5073ddf117.bin",7775L,"117ae99b509327ed04b4b7ca04e43de1564afeb1805eb063757e5a5073ddf117"));
                require(ContinuityActionJournal.lookup(same.head().state(),parent.command().actionId(),archive).filter(parent::equals).isPresent(),
                        "reserved NoEffect issuer lost its exact current six-child parent");
                var prepared=org.xar.ck3.control.application.advance.PreparedCleanupSuccessorEvidence.loadPreparedOriginals(new ExactRef("D:\\ck3-state\\ck3-java-resume91_offline04_20261111T071454Z\\business\\continuity\\artifacts\\c46d21ec8fef4be5d12c03a582c42ef73a0a9221e0efa287911c2cc10e7d8854.bin",3902L,"c46d21ec8fef4be5d12c03a582c42ef73a0a9221e0efa287911c2cc10e7d8854"),archive);
                var current=ContinuityActionJournal.lookup(same.head().state(),prepared.command().actionId(),archive);
                if(current.isPresent()){
                    require(current.orElseThrow().state() instanceof ActionState.ReservedPreparedCleanupNoEffectConfirmed,
                            "reserved NoEffect cannot replace a prior child lifecycle");
                    var terminal=(ActionState.ReservedPreparedCleanupNoEffectConfirmed)current.orElseThrow().state();
                    var proof=org.xar.ck3.control.application.advance.ReservedPreparedCleanupNoEffectProof.load(terminal.proofReference(),archive,replay);
                    requireQualifiedReservedNoEffectBackend(context,proof);return terminal.proofReference();
                }
                var read=archive.loadRead(new ExactRef("D:\\ck3-state\\ck3-java-resume91_offline04_20261111T071454Z\\business\\continuity\\artifacts\\98ad9e86c03269422cbcd53c570cffed27b6bd2057d1e76b4c9d6008f256682e.bin",13960L,"98ad9e86c03269422cbcd53c570cffed27b6bd2057d1e76b4c9d6008f256682e"));
                var status=new ClockStatusRead.Observation(ClockStatusRead.decode(read.original()),read,archive.referenceOf(read.original()));
                byte[] ackBytes=postExitOriginalBytes(new ExactRef("D:\\ck3-state\\resume91-runtime\\quarkus-dev307-runtime\\attempt79\\post-C6-status79-after138520-originals01\\fresh-ack-original.packet",282L,"273e97748f01032b95e90664c96d3066486d6328f6d6fed51950c1036b9493c9")),outbound=postExitOriginalBytes(new ExactRef("D:\\ck3-state\\resume91-runtime\\quarkus-dev307-runtime\\attempt79\\post-C6-status79-after138520-originals01\\fresh-outbound-original.packet",165L,"1cab5c0e37409c9a56d9fa2ae11aa7d120245d0a10bb437e9d306117e718b762")),packet=postExitOriginalBytes(new ExactRef("D:\\ck3-state\\resume91-runtime\\quarkus-dev307-runtime\\attempt79\\post-C6-status79-after138520-originals01\\fresh-snapshot-original.packet",1237L,"55b47682ff93416b3c6a376461af7f877d67c81524275380c595bc007d3d87d2"));
                var retained=org.xar.ck3.control.contracts.StrictJson.parse(postExitOriginalBytes(new ExactRef("D:\\ck3-state\\resume91-runtime\\quarkus-dev307-runtime\\attempt79\\post-C6-status79-after138520-originals01\\STATUS-AND-FRESH-RESULT.json",4536L,"382c42a1de4306270ab1243b20aa7d6ae77050778ebfa9f4fd073c6074aa64cb")));
                var session=read.original().custody().orElseThrow().session();var held=retained.get("fresh_custody");
                require(held.path("machine_id").asText().equals(session.machineId())&&held.path("session_id").asText().equals(session.sessionId())
                        &&held.path("connection_generation").asText().equals(session.connectionGeneration().toString())
                        &&org.xar.ck3.control.contracts.GameGeneration.fromJson(held.get("game")).equals(session.game()),
                        "reserved NoEffect raw custody changed its original Status connection");
                var decoded=org.xar.ck3.control.nativebridge.NativeWire.decode(ackBytes);
                require(decoded instanceof org.xar.ck3.control.nativebridge.NativeWire.CommandResult,"reserved NoEffect full READ original is not ACK");
                var ack=(org.xar.ck3.control.nativebridge.NativeWire.CommandResult)decoded;
                var chronology=new NativeRequestChronology(session,java.util.UUID.fromString(held.path("custody_epoch").asText()),ack.requestId(),
                        NativeRequestChronology.PacketIdentity.of(outbound),NativeRequestChronology.PacketIdentity.of(ackBytes),
                        postExitEvent(held.get("write_entered")),postExitEvent(held.get("write_completed")),postExitEvent(held.get("response_received")));
                var actualAck=new NativeActionPort.AckReceived(ack.requestId(),ack.nativeOk(),ack.result().token().map(v->new RawJson(v.value())),
                        new RawJson(ack.payload().value()),ackBytes,Optional.of(new NativeActionPort.OutboundPacket(ack.requestId(),outbound)),Optional.of(chronology));
                var decodedFrame=org.xar.ck3.control.nativebridge.NativeWire.decode(packet);
                require(decodedFrame instanceof org.xar.ck3.control.nativebridge.NativeWire.Snapshot,"reserved NoEffect raw original is not full state_snapshot");
                var snapshot=(org.xar.ck3.control.nativebridge.NativeWire.Snapshot)decodedFrame;var event=postExitEvent(retained.get("fresh_snapshot_received"));
                var frame=new NativeObservationPort.ObservedFrame(session,snapshot.snapshotId(),snapshot.revision(),RawJson.fullMaterial(snapshot.state().value()),packet,event.observedAt());
                NativeFreshSnapshotPort.verifyAfterOriginal(read.original(),actualAck,frame,event);archive.preserve(actualAck);
                var senderStart=archive.preserveMaterial(new RawJson(postExitOriginalBytes(new ExactRef("D:\\ck3-state\\resume91-runtime\\quarkus-dev307-runtime\\attempt79\\ordinal6-successor-only-execution01\\ACTUAL-CHILD-START.json",201L,"dbc9e1a1ead0235b737809d2f86f049a56693e82b7958c49d1027eedd6ec3395"))));
                var senderEnd=archive.preserveMaterial(new RawJson(postExitOriginalBytes(new ExactRef("D:\\ck3-state\\resume91-runtime\\quarkus-dev307-runtime\\attempt79\\ordinal6-successor-only-execution01\\ACTUAL-END.json",1692L,"53946fae1b4278630fe2100676ecd53992fcc9b91a1ddda6a6bfaadf2b85e794"))));
                var barrier=archive.preserveMaterial(new RawJson(postExitOriginalBytes(new ExactRef("D:\\ck3-state\\resume91-native-integration\\life-postcondition-p0-20261112-01\\POST-C6-SENDER138520-STATUS98-BARRIER-CONDITIONAL-REUSE01.json",11040L,"3f7ebfa6d4f6bee80dcf009b63488549079ed65ef074f060eecb20cc5d693811"))));
                var accepted=archive.preserveMaterial(new RawJson(postExitOriginalBytes(new ExactRef("D:\\ck3-state\\resume91-root\\post-vacation-20261107\\POST-C6-ACTUAL-NOEFFECT-OBSERVATION-INDEPENDENT01.json",6005L,"543961f10e81fabfa66aabd119562a0d6ca74a6d2c06aaa308e7b119354bfc0d"))));
                return org.xar.ck3.control.application.advance.ReservedPreparedCleanupNoEffectProof.preserveArchivedOriginals(parent,prepared.children(),prepared.reference(),
                        senderStart,senderEnd,barrier,accepted,status,actualAck,frame,event,read.original().custody().orElseThrow().writeEntered().observedAt(),
                        read.request().deadline(),archive,replay);
            });
            composite.qualifyReservedNoEffect(reference);
            require(context.clock().instant().isBefore(deadline),"reserved NoEffect overall readonly operation deadline expired");return reference;
        }
        /** Imports the accepted post-B observations with their original event window, without any new READ/control. */
        public org.xar.ck3.control.application.advance.PreparedNoEffectReconciliationToken preparedCleanupNoEffectReconciliation(Instant deadline)throws IOException {
            requireContext(context);context.requireActiveGame();
            var reference=context.withSession(same->{
                var archive=context.archive().withSession(same);
                for(var original:preparedNoEffectOriginals())verifyPostResumeBackendOriginal(original);
                var parent=archive.loadReceipt(new ExactRef("D:\\ck3-state\\ck3-java-resume91_offline04_20261111T071454Z\\business\\continuity\\artifacts\\cc914fca3a10bcfcd9b9f44e0155cfd61e7c793aeb3b6fcb03a9d3fee0b05d86.bin",7344L,"cc914fca3a10bcfcd9b9f44e0155cfd61e7c793aeb3b6fcb03a9d3fee0b05d86"));
                var current=ContinuityActionJournal.lookup(same.head().state(),"child-1e897759fd9beafc96c0ab4bcfc282b8cc18f16f0dce55df88379e82830a1f27",archive).orElseThrow();
                if(current.state() instanceof ActionState.PreparedCleanupNoEffectConfirmed terminal){
                    var proof=org.xar.ck3.control.application.advance.PreparedCleanupNoEffectProof.load(terminal.proofReference(),archive,replay);
                    requireQualifiedPreparedNoEffectBackend(context,proof);return terminal.proofReference();
                }
                var references=List.of(new ExactRef("D:\\ck3-state\\ck3-java-resume91_offline04_20261111T071454Z\\business\\continuity\\artifacts\\f42a94b5be9efc2c19d4b01d237b02cda9b09f6527fb38aa03fc070537fd88a8.bin",7382L,"f42a94b5be9efc2c19d4b01d237b02cda9b09f6527fb38aa03fc070537fd88a8"),new ExactRef("D:\\ck3-state\\ck3-java-resume91_offline04_20261111T071454Z\\business\\continuity\\artifacts\\24e7e34f8fa8b8ce52f2dd966ba5fb687caf368ea2ff97d5d74bf8a2fd1d9399.bin",7350L,"24e7e34f8fa8b8ce52f2dd966ba5fb687caf368ea2ff97d5d74bf8a2fd1d9399"),new ExactRef("D:\\ck3-state\\ck3-java-resume91_offline04_20261111T071454Z\\business\\continuity\\artifacts\\76945824decaaea3cf8c0393880c56faff97cf587089cc3508a347f0fb81a690.bin",7879L,"76945824decaaea3cf8c0393880c56faff97cf587089cc3508a347f0fb81a690"),new ExactRef("D:\\ck3-state\\ck3-java-resume91_offline04_20261111T071454Z\\business\\continuity\\artifacts\\8a3ccb1431262067daed5c9cbc7559ac4ad3c4bb653f2860825ee806adb9dfb5.bin",2734L,"8a3ccb1431262067daed5c9cbc7559ac4ad3c4bb653f2860825ee806adb9dfb5"),new ExactRef("D:\\ck3-state\\ck3-java-resume91_offline04_20261111T071454Z\\business\\continuity\\artifacts\\45e6c8e2159c52d064475c9689c0510632cf8aeb6b6e5e580688825f7a15dd38.bin",2788L,"45e6c8e2159c52d064475c9689c0510632cf8aeb6b6e5e580688825f7a15dd38"));
                var children=references.stream().map(archive::loadReceipt).toList();
                require(current.equals(children.getLast()),"prepared NoEffect issuer lost its exact current original fifth receipt");
                var read=archive.loadRead(new ExactRef("D:\\ck3-state\\ck3-java-resume91_offline04_20261111T071454Z\\business\\continuity\\artifacts\\283531a053c9f8d76fcb7387777312048fc6e78da20a844b83caf1186b85c310.bin",13939L,"283531a053c9f8d76fcb7387777312048fc6e78da20a844b83caf1186b85c310"));
                var status=new ClockStatusRead.Observation(ClockStatusRead.decode(read.original()),read,archive.referenceOf(read.original()));
                byte[] ackBytes=postExitOriginalBytes(new ExactRef("D:\\ck3-state\\resume91-runtime\\quarkus-dev307-runtime\\attempt79\\post-B-status79-after154044-originals03\\fresh-ack-original.packet",282L,"d7e5b9fac1c04af7c428165cb542dc7d991ebcbffdd63d1c14b29c52ce535d6a")),outbound=postExitOriginalBytes(new ExactRef("D:\\ck3-state\\resume91-runtime\\quarkus-dev307-runtime\\attempt79\\post-B-status79-after154044-originals03\\fresh-outbound-original.packet",165L,"999ad1cdd782ae43e8508d385d620ae3c18552c21e4069fcccab89b76506a9ba")),packet=postExitOriginalBytes(new ExactRef("D:\\ck3-state\\resume91-runtime\\quarkus-dev307-runtime\\attempt79\\post-B-status79-after154044-originals03\\fresh-snapshot-original.packet",1237L,"418706b3ec8abffbb5d50a5b8e7292c37e8c6a107116d9f5a586adb4ea4f9a7b"));
                var raw=org.xar.ck3.control.contracts.StrictJson.parse(postExitOriginalBytes(new ExactRef("D:\\ck3-state\\resume91-runtime\\quarkus-dev307-runtime\\attempt79\\post-B-status79-after154044-originals03\\STATUS-AND-FRESH-RESULT.json",4530L,"203f465c621ffa2319ec02c1f949f3e2539b43fb591461fd10713db55513a1d0")));
                var session=read.original().custody().orElseThrow().session();var held=raw.get("fresh_custody");
                require(held.path("machine_id").asText().equals(session.machineId())&&held.path("session_id").asText().equals(session.sessionId())
                        &&held.path("connection_generation").asText().equals(session.connectionGeneration().toString())
                        &&org.xar.ck3.control.contracts.GameGeneration.fromJson(held.get("game")).equals(session.game()),
                        "prepared NoEffect full-state custody changed the actual Status connection");
                var decoded=org.xar.ck3.control.nativebridge.NativeWire.decode(ackBytes);
                require(decoded instanceof org.xar.ck3.control.nativebridge.NativeWire.CommandResult,"prepared NoEffect original is not a framed full-state acknowledgement");
                var ack=(org.xar.ck3.control.nativebridge.NativeWire.CommandResult)decoded;
                var chronology=new NativeRequestChronology(session,java.util.UUID.fromString(held.path("custody_epoch").asText()),ack.requestId(),
                        NativeRequestChronology.PacketIdentity.of(outbound),NativeRequestChronology.PacketIdentity.of(ackBytes),
                        postExitEvent(held.get("write_entered")),postExitEvent(held.get("write_completed")),postExitEvent(held.get("response_received")));
                var retainedAck=new NativeActionPort.AckReceived(ack.requestId(),ack.nativeOk(),ack.result().token().map(value->new RawJson(value.value())),
                        new RawJson(ack.payload().value()),ackBytes,Optional.of(new NativeActionPort.OutboundPacket(ack.requestId(),outbound)),Optional.of(chronology));
                var snapshot=org.xar.ck3.control.nativebridge.NativeWire.decode(packet);
                require(snapshot instanceof org.xar.ck3.control.nativebridge.NativeWire.Snapshot,"prepared NoEffect original full state is not a snapshot");
                var frame=(org.xar.ck3.control.nativebridge.NativeWire.Snapshot)snapshot;var event=postExitEvent(raw.get("fresh_snapshot_received"));
                var observed=new NativeObservationPort.ObservedFrame(session,frame.snapshotId(),frame.revision(),RawJson.fullMaterial(frame.state().value()),packet,event.observedAt());
                NativeFreshSnapshotPort.verifyAfterOriginal(read.original(),retainedAck,observed,event);archive.preserve(retainedAck);
                var senderStart=archive.preserveMaterial(new RawJson(postExitOriginalBytes(new ExactRef("D:\\ck3-state\\resume91-runtime\\quarkus-dev307-runtime\\attempt79\\prepared-cleanup-B-only-execution01\\ACTUAL-CHILD-START.json",213L,"475b06cf684ddd1ea8d9ff1a7c26e4ed2d075e86839d9533e7387eb6cace2dc3"))));
                var senderEnd=archive.preserveMaterial(new RawJson(postExitOriginalBytes(new ExactRef("D:\\ck3-state\\resume91-runtime\\quarkus-dev307-runtime\\attempt79\\prepared-cleanup-B-only-execution01\\ACTUAL-END.json",1511L,"d2d53222fabf5004f891d8d325305e5f7790a39f3cbfb9450610448504bc9385"))));
                var barrier=archive.preserveMaterial(new RawJson(postExitOriginalBytes(new ExactRef("D:\\ck3-state\\resume91-native-integration\\life-postcondition-p0-20261112-01\\POST-B-SENDER154044-STATUS-BARRIER-CONDITIONAL-REUSE01.json",3973L,"02b677a67f7c1c52fd839b2c2721eaa98dae1f22deb18817343e14bd37ec1d0b"))));
                var accepted=archive.preserveMaterial(new RawJson(postExitOriginalBytes(new ExactRef("D:\\ck3-state\\resume91-root\\post-vacation-20261107\\POST-B-ACTUAL-NOEFFECT-OBSERVATION-INDEPENDENT01.json",4921L,"3a809080c712a6c13babf954a4d0cfe1eddf02d69785aec6fcf02d6a34389de6"))));
                // Observation time is the original actual Status write, not this import's wall clock or old command deadline.
                return org.xar.ck3.control.application.advance.PreparedCleanupNoEffectProof.preserveArchivedOriginals(parent,children,senderStart,senderEnd,barrier,accepted,
                        status,retainedAck,observed,event,read.original().custody().orElseThrow().writeEntered().observedAt(),read.request().deadline(),archive,replay);
            });
            // Slow originals, backend qualification and canonical lookup finish before the short readonly token is minted.
            return composite.preparedNoEffectReconciliationToken(reference,deadline)
                    .orElseThrow(()->new IOException("actual source did not issue its dedicated prepared NoEffect readonly capability"));
        }
        /** Imports only the accepted post-exit archival observations; performs no new Native READ or action. */
        public NoEffectReconciliationToken postExitNoEffectReconciliation(Instant deadline)throws IOException {
            requireContext(context);context.requireActiveGame();
            var reference=context.withSession(same->{
                var archive=context.archive().withSession(same);
                for(var original:postExitNoEffectOriginals())verifyPostResumeBackendOriginal(original);
                var parent=archive.loadReceipt(new ExactRef("D:\\ck3-state\\ck3-java-resume91_offline04_20261111T071454Z\\business\\continuity\\artifacts\\11291294f9e9421ef63f6bff93ec06b82a7c06d448a5b779ab8ef7a50cd868fb.bin",6909L,"11291294f9e9421ef63f6bff93ec06b82a7c06d448a5b779ab8ef7a50cd868fb"));
                var references=List.of(new ExactRef("D:\\ck3-state\\ck3-java-resume91_offline04_20261111T071454Z\\business\\continuity\\artifacts\\f42a94b5be9efc2c19d4b01d237b02cda9b09f6527fb38aa03fc070537fd88a8.bin",7382L,"f42a94b5be9efc2c19d4b01d237b02cda9b09f6527fb38aa03fc070537fd88a8"),new ExactRef("D:\\ck3-state\\ck3-java-resume91_offline04_20261111T071454Z\\business\\continuity\\artifacts\\24e7e34f8fa8b8ce52f2dd966ba5fb687caf368ea2ff97d5d74bf8a2fd1d9399.bin",7350L,"24e7e34f8fa8b8ce52f2dd966ba5fb687caf368ea2ff97d5d74bf8a2fd1d9399"),new ExactRef("D:\\ck3-state\\ck3-java-resume91_offline04_20261111T071454Z\\business\\continuity\\artifacts\\76945824decaaea3cf8c0393880c56faff97cf587089cc3508a347f0fb81a690.bin",7879L,"76945824decaaea3cf8c0393880c56faff97cf587089cc3508a347f0fb81a690"),new ExactRef("D:\\ck3-state\\ck3-java-resume91_offline04_20261111T071454Z\\business\\continuity\\artifacts\\4879621f4401ba2e7f466fdea2bb2872436b77cdfe0b1f4df1f79b901c68314d.bin",2513L,"4879621f4401ba2e7f466fdea2bb2872436b77cdfe0b1f4df1f79b901c68314d"));
                var children=references.stream().map(archive::loadReceipt).toList();
                var read=archive.loadRead(new ExactRef("D:\\ck3-state\\ck3-java-resume91_offline04_20261111T071454Z\\business\\continuity\\artifacts\\2ad7203aa81aad31179147cbec521f538b7bb4c6a364df84a4222c5e1bf78906.bin",13951L,"2ad7203aa81aad31179147cbec521f538b7bb4c6a364df84a4222c5e1bf78906"));
                var status=new ClockStatusRead.Observation(ClockStatusRead.decode(read.original()),read,archive.referenceOf(read.original()));
                byte[] ackBytes=postExitOriginalBytes(new ExactRef("D:\\ck3-state\\resume91-runtime\\quarkus-dev307-runtime\\attempt79\\postexit-status79-barrier02\\originals\\fresh-ack-original.packet",282L,"4ef6892edfbf941ae5b54464031ca0fa16a3b25769fd372423d81b90d5957222")),outbound=postExitOriginalBytes(new ExactRef("D:\\ck3-state\\resume91-runtime\\quarkus-dev307-runtime\\attempt79\\postexit-status79-barrier02\\originals\\fresh-outbound-original.packet",165L,"2dce1a300e856e372e86c39d1df96e536491be5cf473a446bebfb6a14c281434")),packet=postExitOriginalBytes(new ExactRef("D:\\ck3-state\\resume91-runtime\\quarkus-dev307-runtime\\attempt79\\postexit-status79-barrier02\\originals\\fresh-snapshot-original.packet",1237L,"b3a3f0cd4d1666fa1a521666d887498928ab8e655b310a9873a1d2c263355c1d"));
                var raw=org.xar.ck3.control.contracts.StrictJson.parse(postExitOriginalBytes(new ExactRef("D:\\ck3-state\\resume91-runtime\\quarkus-dev307-runtime\\attempt79\\postexit-status79-barrier02\\originals\\STATUS-AND-FRESH-RESULT.json",4539L,"bdc7165f1097ea1b86ae411271d288cdf167704a7df77330dfd944f4c423af10")));
                var session=read.original().custody().orElseThrow().session();
                var held=raw.get("fresh_custody");
                require(held.path("machine_id").asText().equals(session.machineId())
                        &&held.path("session_id").asText().equals(session.sessionId())
                        &&held.path("connection_generation").asText().equals(session.connectionGeneration().toString())
                        &&org.xar.ck3.control.contracts.GameGeneration.fromJson(held.get("game")).equals(session.game()),
                        "post-exit retained full-state custody changed the actual Status connection");
                var decoded=org.xar.ck3.control.nativebridge.NativeWire.decode(ackBytes);
                require(decoded instanceof org.xar.ck3.control.nativebridge.NativeWire.CommandResult,"post-exit full-state original is not a framed ACK");
                var ack=(org.xar.ck3.control.nativebridge.NativeWire.CommandResult)decoded;
                var chronology=new NativeRequestChronology(session,java.util.UUID.fromString(held.path("custody_epoch").asText()),ack.requestId(),
                        NativeRequestChronology.PacketIdentity.of(outbound),NativeRequestChronology.PacketIdentity.of(ackBytes),
                        postExitEvent(held.get("write_entered")),postExitEvent(held.get("write_completed")),postExitEvent(held.get("response_received")));
                var retainedAck=new NativeActionPort.AckReceived(ack.requestId(),ack.nativeOk(),
                        ack.result().token().map(value->new RawJson(value.value())),new RawJson(ack.payload().value()),ackBytes,
                        Optional.of(new NativeActionPort.OutboundPacket(ack.requestId(),outbound)),Optional.of(chronology));
                var snapshot=org.xar.ck3.control.nativebridge.NativeWire.decode(packet);
                require(snapshot instanceof org.xar.ck3.control.nativebridge.NativeWire.Snapshot,"post-exit original full frame is not a snapshot");
                var frame=(org.xar.ck3.control.nativebridge.NativeWire.Snapshot)snapshot;
                var event=postExitEvent(raw.get("fresh_snapshot_received"));
                var observed=new NativeObservationPort.ObservedFrame(session,frame.snapshotId(),frame.revision(),
                        RawJson.fullMaterial(frame.state().value()),packet,event.observedAt());
                NativeFreshSnapshotPort.verifyAfterOriginal(read.original(),retainedAck,observed,event);
                archive.preserve(retainedAck);
                var release=archive.preserveMaterial(new RawJson(postExitOriginalBytes(new ExactRef("D:\\ck3-state\\resume91-runtime\\quarkus-dev307-runtime\\attempt79\\C81-CHILD4-FRESH-WINDOW-P0\\EXACT-FAILED-JAVA-RELEASED79.json",1588L,"d112ae78cf7c8496f646fba5ac6fb12b22fbce5bcb64455e4bb6be98316ccb3f"))));
                var qualification=archive.preserveMaterial(new RawJson(postExitOriginalBytes(new ExactRef("D:/ck3-state/resume91-native-integration/life-postcondition-p0-20261112-01/C81-POSTEXIT-STATUS-BARRIER-CONDITIONAL-QUALIFICATION01.json",19350L,"d4727bdd2d7d071436c0ffe6e572bc30d705a23729a8444236f03529fec5923c"))));
                return PostExitCleanupNoEffectProof.preserveArchivedOriginals(parent,children,new ExactRef("D:\\ck3-state\\ck3-java-resume91_offline04_20261111T071454Z\\business\\continuity\\artifacts\\4e82d98d78988332cac22cdbdad8e5f1fdff1224d4c004e7ea32124dd3d54e37.bin",3135L,"4e82d98d78988332cac22cdbdad8e5f1fdff1224d4c004e7ea32124dd3d54e37"),release,qualification,status,
                        retainedAck,observed,event,read.before().binding().observedAt(),read.request().deadline(),archive,replay);
            });
            return composite.noEffectReconciliationToken(reference,deadline)
                    .orElseThrow(()->new IOException("actual installed Life source did not issue its read-only NoEffect token"));
        }
        /** One genuine fixed physical Status read; its scope never grants ordinary Driver readiness or submission. */
        private LifeAdvanceComposite.CancellationRead readCancellationStatus(ActionCommand parent, CompositeExecution execution,
                List<ActionReceipt> proposedChildren, Instant deadline) {
            try {
                return context.withSession(same -> {
                    var originalArchive = context.archive().withSession(same);
                    var heldHead = same.head();
                    var actual = ContinuityActionJournal.lookup(heldHead.state(), parent.actionId(), originalArchive).orElseThrow();
                    require(actual.command().equals(parent) && actual.state() instanceof ActionState.CompositeUnknown unknown
                            && unknown.execution().equals(execution), "Life physical Status changed its canonical unresolved parent");
                    var children = execution.children().stream().map(bound -> {
                        var child = ContinuityActionJournal.lookup(heldHead.state(), bound.actionId(), originalArchive).orElseThrow();
                        require(child.bodySha256().equals(bound.bodySha256()), "Life physical Status child body differs from canonical history");
                        return child;
                    }).toList();
                    require(children.equals(proposedChildren), "Life physical Status borrowed another child prefix");
                    if (children.getLast().command().operation().value().startsWith(ClockStatusRead.CANCEL_PREFIX))
                        LifeAdvanceComposite.requireCancelledInitializationPrefix(parent, execution, children);
                    else LifeAdvanceComposite.requireArmedInitializationPrefix(parent, execution, children);
                    var profile = infrastructure.physicalStatuses();
                    RootUnknownSentinelReadProfile.requireInstalled(profile, infrastructure.statuses());
                    PhysicalStatusIdentity.requireProfile(profile);
                    PlanningReadResult.Known<Status> status = context.physicalStatusReads().withObserved(same, deadline, lease -> {
                        var request = PlanningReadRequest.newStatusOnly(lease.identity(), profile.operation(),
                                new org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj(Map.of()), deadline);
                        var result = context.reads().read(same, profile, request);
                        if (!(result instanceof PlanningReadResult.Known<Status> known))
                            throw new IOException("Life physical Status unavailable: " + ((PlanningReadResult.Unavailable<Status>) result).reason());
                        require(known.receipt().request().equals(request) && known.receipt().contractId().equals(profile.contractId())
                                && known.value().equals(ClockStatusRead.decode(known.receipt().original())),
                                "Life physical Status returned another request or decoded value");
                        return known;
                    });
                    // Exit physical-only custody, then use the existing genuine fresh full-state READ producer.
                    context.adopted().authority().requireOutsideObservationScope(same);
                    NativeFreshSnapshotPort.Result fresh;
                    try { fresh = context.transport().readFreshFullState(deadline); }
                    catch (InterruptedException interrupted) {
                        Thread.currentThread().interrupt();
                        var failure = new java.io.InterruptedIOException("Life cancellation fresh after-Status read interrupted; no replay");
                        failure.initCause(interrupted); throw failure;
                    }
                    if (fresh instanceof NativeFreshSnapshotPort.Unavailable unavailable) {
                        String reason = unavailable.reason();
                        throw new IOException("Life cancellation fresh after-Status read unavailable: " + reason.substring(0, Math.min(512, reason.length())));
                    }
                    var received = (NativeFreshSnapshotPort.Received) fresh;
                    NativeFreshSnapshotPort.verifyAfter(status.receipt().original(), received);
                    // Borrow this actual writer for recovery DATA; Held.project would open a second writer.
                    // This callback also runs under the coordinator during the later cancellation terminal read.
                    require(context.clock().instant().isBefore(deadline)
                            && !received.originalFrame().observedAt().isAfter(deadline),
                            "actual received-frame projection deadline expired");
                    var ending = context.adopted().authority().withFrozenRawObservation(received.originalFrame(), same, frozen -> {
                        var nativeOriginal = originalArchive.preserveNativeFrame(received.originalFrame());
                        var projected = context.core().observationAssembler().assemble(received.originalFrame(), frozen.facts(), nativeOriginal);
                        if (projected instanceof org.xar.ck3.control.application.driver.DriverObservationAssembler.Incomplete missing)
                            throw new IllegalStateException("incomplete actual semantic observation: " + String.join(",", missing.reasons()));
                        return LifeAdvanceRootReplay.push((org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete) projected);
                    });
                    require(context.clock().instant().isBefore(deadline), "actual waited snapshot projection exceeded its original capture deadline");
                    var custody = status.receipt().original().custody().orElseThrow(); custody.verify(status.receipt());
                    require(!ending.observedAt().isBefore(custody.responseReceived().observedAt()),
                            "Life cancellation has no fresh complete semantic frame after its actual physical Status");
                    return new LifeAdvanceComposite.CancellationRead(status, ending);
                });
            } catch (IOException failure) { throw new UncheckedIOException("actual source-owned Life physical Status unavailable", failure); }
        }
        private ContinuityStorePort.Session borrowedSession() {
            try {return context.borrowedSession();}
            catch(IOException failure) {throw new UncheckedIOException("Life requires the actual borrowed Root writer",failure);}
        }
        /** Installer ownership only; this guard grants no observation, dispatch or Ready qualification. */
        public void requireContext(RootRuntimeContext actual)throws IOException {
            require(actual==context && actual.core()==retry.core(),"Life product belongs to another actual Root context or Core");
            require(infrastructure!=null && composite!=null && commands!=null && replay!=null && pendingUiScope!=null && scopedReadiness!=null
                    && installation.composites().size()==1 && installation.composites().getFirst().handler()==composite,
                    "Life product lost its privately constructed shared infrastructure/composite custody");
        }
        public DriverHistoryAccess history(){return history;}
        public RootAdvanceRuntimeFacts runtimeFacts(){return runtimeFacts;}
        public ProductionAdvanceReadiness readiness(){return readiness;}
        /** The same privately constructed scope consumed by infrastructure, Life and Commands. */
        public PendingUiLifeAdvance.Scope pendingUiScope(){return pendingUiScope;}
        public RootAdvanceInfrastructureFactory.Installed infrastructure(){return infrastructure;}
        public LifeAdvanceRootReplay replay(){return replay;}
        public LifeAdvanceComposite composite(){return composite;}
        public LifeAdvanceCommands commands(){return commands;}
        /** Life-only bindings; the unique Root aggregator also consumes infrastructure().installation() once. */
        public RootDomainInstallation installation(){return installation;}
        public List<RootDomainInstallation> installations(){return List.of(infrastructure.installation(),installation);}
    }
    /** Complete pre-late qualification only. Never invoke this full replay in
     * the SDK final callback; that callback requires the private held capability. */
    static void requireQualifiedPreparedCleanupBackend(RootRuntimeContext context,
            org.xar.ck3.control.application.advance.PreparedCleanupEvidence.Prepared prepared) {
        if(org.xar.ck3.control.application.advance.PreparedCleanupSuccessorEvidence.isSuccessor(prepared)){
            var terminal=(ActionState.PreparedCleanupNoEffectConfirmed)prepared.children().getLast().state();
            var proof=org.xar.ck3.control.application.advance.PreparedCleanupNoEffectProof.load(terminal.proofReference(),context.archive(),
                    new LifeAdvanceRootReplay(RootAdvanceInfrastructureFactory.freshFrameLoader(context.frameLoader())));
            requireQualifiedPreparedNoEffectBackend(context,proof);
            require(prepared.parentReceipt().equals(proof.parentReceipt())&&prepared.children().subList(0,4).equals(proof.children().subList(0,4))
                    &&terminal.originalPreparedState().equals(proof.originalPreparedState())&&prepared.command().source().equals(context.source())
                    &&prepared.command().before().game().equals(context.game().generation())&&prepared.command().sessionId().equals(context.game().sessionId()),
                    "prepared successor changed its actual canonical C5 NoEffect/Root subject");return;
        }
        var proof=PostExitCleanupNoEffectProof.load(prepared.aProofReference(),context.archive(),
                new LifeAdvanceRootReplay(RootAdvanceInfrastructureFactory.freshFrameLoader(context.frameLoader())));
        requireQualifiedPostExitNoEffect(context,proof);
        require(prepared.children().getLast().state() instanceof ActionState.CleanupNoEffectConfirmed
                &&prepared.aTerminalReference().equals(context.archive().receiptReferenceOf(prepared.children().getLast()))
                &&prepared.command().before().game().equals(context.game().generation())
                &&prepared.command().source().equals(context.source())&&prepared.command().sessionId().equals(context.game().sessionId()),
                "prepared source changed its canonical A terminal or actual Root subject");
    }
    private static void verifyPreparedNativeCapture(org.xar.ck3.control.application.advance.PreparedCleanupEvidence.Prepared prepared,
            org.xar.ck3.control.application.advance.PreparedCleanupEvidence.PostAckCaptured captured,ActionPorts.OutcomeArchive archive)throws IOException {
        var late=captured.binding();
        NativeFreshSnapshotPort.verifyAfterOriginal(late.status().acknowledgement(),late.freshSnapshotAck(),late.writeFrame(),late.snapshotReceived());
        NativeFreshSnapshotPort.verifyAfterOriginal(captured.idle2().acknowledgement(),captured.freshSnapshotAck(),captured.afterFrame(),captured.snapshotReceived());
        var sent=org.xar.ck3.control.nativebridge.NativeWire.decodeExecuteRequest(captured.cancellationAcknowledgement().outbound().orElseThrow().originalPacket());
        require(sent.requestId().equals(prepared.nativeRequestId())&&sent.step().equals(prepared.nativePrepared().step())
                &&sent.expectedRevision().filter(late.writeFrame().nativeRevision()::equals).isPresent()
                &&sent.expectedSnapshotRevision().isEmpty()&&new RawJson(sent.normalizedAdditionalFields().value()).equals(prepared.nativePrepared().additionalFields()),
                "prepared original control packet changed immutable request or actual late expected_revision");
    }
    static void verifyQualifiedPreparedParent(RootRuntimeContext context,org.xar.ck3.control.continuity.writer.WriterContracts.Head head,
            ActionReceipt parent,ActionPorts.OutcomeArchive archive){
        var basis=org.xar.ck3.control.application.advance.PreparedCleanupParentEvidence.referenceOf(parent);
        var loaded=org.xar.ck3.control.application.advance.PreparedCleanupParentEvidence.load(basis,archive,
                new LifeAdvanceRootReplay(RootAdvanceInfrastructureFactory.freshFrameLoader(context.frameLoader())));
        org.xar.ck3.control.application.advance.PreparedCleanupParentProof.verifyReceipt(parent,loaded,archive,
                new LifeAdvanceRootReplay(RootAdvanceInfrastructureFactory.freshFrameLoader(context.frameLoader())));
        var prepared=loaded.originals().prepared();requireQualifiedPreparedCleanupBackend(context,prepared);
        try{
            verifyPreparedNativeCapture(prepared,loaded.originals().capture(),archive);
            var same=context.borrowedSession();context.writer().requireSession(same);require(same.head().digest().equals(head.digest()),"prepared parent replay detached from actual writer");
            if(parent.sequence()<=head.state().sequence()){ContinuityActionJournal.requireHistoricalReceipt(head.state(),parent,archive);return;}
            require(parent.sequence()==head.state().sequence()+1&&context.actions() instanceof RootApplicationSession,"prepared parent skipped actual next sequence");
            ((RootApplicationSession)context.actions()).requirePreparedCleanupParentProposal(parent,prepared);
            var current=ContinuityActionJournal.lookup(head.state(),parent.command().actionId(),archive).orElseThrow();
            require(org.xar.ck3.control.application.advance.PreparedCleanupCursor.marked(current)
                    &&((ActionState.CompositeUnknown)current.state()).execution().equals(loaded.originals().execution()),"prepared parent changed current exact five-child cursor");
            for(var child:loaded.originals().children())require(ContinuityActionJournal.lookup(head.state(),child.command().actionId(),archive).filter(child::equals).isPresent(),
                    "prepared parent terminal is not over all five current canonical originals");
        }catch(IOException unavailable){throw new UncheckedIOException(unavailable);}
    }
    static void verifyQualifiedPreparedCursor(RootRuntimeContext context,org.xar.ck3.control.continuity.writer.WriterContracts.Head head,
            ActionReceipt cursor,ActionPorts.OutcomeArchive archive){
        var prepared=org.xar.ck3.control.application.advance.PreparedCleanupCursor.load(cursor,archive,
                new LifeAdvanceRootReplay(RootAdvanceInfrastructureFactory.freshFrameLoader(context.frameLoader())));
        requireQualifiedPreparedCleanupBackend(context,prepared);
        try{
            var same=context.borrowedSession();context.writer().requireSession(same);
            require(same.head().digest().equals(head.digest()),"prepared cursor replay crossed the actual held writer head");
            if(cursor.sequence()<=head.state().sequence()){ContinuityActionJournal.requireHistoricalReceipt(head.state(),cursor,archive);return;}
            require(cursor.sequence()==head.state().sequence()+1&&context.actions() instanceof RootApplicationSession,
                    "prepared cursor proposal skipped the actual writer sequence");
            ((RootApplicationSession)context.actions()).requirePreparedCleanupParentProposal(cursor,prepared);
            require(ContinuityActionJournal.lookup(head.state(),cursor.command().actionId(),archive).filter(prepared.parentReceipt()::equals).isPresent(),
                    "prepared reservation did not append its exact current four-child original");
            require(ContinuityActionJournal.lookup(head.state(),prepared.children().getLast().command().actionId(),archive)
                    .filter(prepared.children().getLast()::equals).isPresent(),"prepared cursor did not retain canonical A NoEffect");
        }catch(java.io.IOException unavailable){throw new java.io.UncheckedIOException(unavailable);}
    }
    static void verifyQualifiedPreparedCleanup(RootRuntimeContext context,Optional<org.xar.ck3.control.continuity.writer.WriterContracts.Head> proposedHead,
            ActionReceipt receipt,ActionPorts.OutcomeArchive archive){
        if(receipt.state() instanceof ActionState.ReservedPreparedCleanupNoEffectConfirmed){verifyQualifiedReservedNoEffect(context,proposedHead,receipt,archive);return;}
        if(receipt.state() instanceof ActionState.PreparedCleanupNoEffectConfirmed){verifyQualifiedPreparedNoEffect(context,proposedHead,receipt,archive);return;}
        if(receipt.state() instanceof org.xar.ck3.control.application.action.PreparedCleanupAction state){
            var role=org.xar.ck3.control.application.advance.PreparedCleanupEvidence.loadPreparedOriginals(state.preparationReference(),archive);
            if(org.xar.ck3.control.application.advance.PreparedCleanupSuccessorEvidence.isSuccessor(role)){
                verifyQualifiedPreparedSuccessor(context,proposedHead,receipt,archive);return;
            }
        }
        var prepared=org.xar.ck3.control.application.advance.PreparedCleanupReplay.verify(receipt,archive,
                new LifeAdvanceRootReplay(RootAdvanceInfrastructureFactory.freshFrameLoader(context.frameLoader())));
        requireQualifiedPreparedCleanupBackend(context,prepared);
        try{
            var same=context.borrowedSession();context.writer().requireSession(same);
            var head=proposedHead.orElseGet(()->{try{return same.head();}catch(IOException failure){throw new UncheckedIOException(failure);}});
            require(head.digest().equals(same.head().digest()),"prepared replay received a detached writer head");
            if(receipt.sequence()<=head.state().sequence()){
                ContinuityActionJournal.requireHistoricalReceipt(head.state(),receipt,archive);return;
            }
            require(receipt.sequence()==head.state().sequence()+1&&context.actions() instanceof RootApplicationSession,
                    "prepared writer proposal skipped its actual sequence or Root session");
            ((RootApplicationSession)context.actions()).requirePreparedCleanupProposal(receipt,prepared);
            var original=ContinuityActionJournal.lookup(head.state(),prepared.parentReceipt().command().actionId(),archive).orElseThrow();
            require(original.state() instanceof ActionState.CompositeUnknown,"prepared writer proposal lost its unresolved actual parent");
            var prefix=((ActionState.CompositeUnknown)prepared.parentReceipt().state()).execution();
            var cursor=((ActionState.CompositeUnknown)original.state()).execution();
            require(cursor.handlerId().equals(prefix.handlerId())&&cursor.startedAt().equals(prefix.startedAt())&&cursor.guard().equals(prefix.guard())
                    &&cursor.children().size()==5&&cursor.children().subList(0,4).equals(prefix.children())
                    &&cursor.children().getLast().equals(new CompositeExecution.Child(receipt.command().actionId(),receipt.bodySha256())),
                    "prepared writer proposal changed its reserved exact five-child prefix");
            require(ContinuityActionJournal.lookup(head.state(),prepared.children().getLast().command().actionId(),archive)
                    .filter(prepared.children().getLast()::equals).isPresent(),"prepared proposal lost its actual canonical A NoEffect terminal");
        }catch(IOException unavailable){throw new UncheckedIOException("actual prepared Root writer admission unavailable",unavailable);}
    }
    private static void verifyQualifiedPreparedSuccessor(RootRuntimeContext context,
            Optional<org.xar.ck3.control.continuity.writer.WriterContracts.Head> proposedHead,ActionReceipt receipt,ActionPorts.OutcomeArchive archive){
        var prepared=org.xar.ck3.control.application.advance.PreparedCleanupReplay.verify(receipt,archive,
                new LifeAdvanceRootReplay(RootAdvanceInfrastructureFactory.freshFrameLoader(context.frameLoader())));
        require(org.xar.ck3.control.application.advance.PreparedCleanupSuccessorEvidence.isSuccessor(prepared),"prepared successor lost its explicit v2 original role");
        requireQualifiedPreparedCleanupBackend(context,prepared);
        try{
            var same=context.borrowedSession();context.writer().requireSession(same);
            var head=proposedHead.orElseGet(()->{try{return same.head();}catch(IOException failure){throw new UncheckedIOException(failure);}});
            require(head.digest().equals(same.head().digest()),"prepared successor replay received a detached writer head");
            if(receipt.sequence()<=head.state().sequence()){ContinuityActionJournal.requireHistoricalReceipt(head.state(),receipt,archive);return;}
            require(receipt.sequence()==head.state().sequence()+1&&context.actions() instanceof RootApplicationSession,
                    "prepared successor proposal skipped the actual next writer sequence");
            ((RootApplicationSession)context.actions()).requirePreparedCleanupProposal(receipt,prepared);
            var parent=ContinuityActionJournal.lookup(head.state(),prepared.parentReceipt().command().actionId(),archive).orElseThrow();
            require(parent.state() instanceof ActionState.CompositeUnknown,"prepared successor proposal lost its unresolved parent");
            var prefix=((ActionState.CompositeUnknown)prepared.parentReceipt().state()).execution();var cursor=((ActionState.CompositeUnknown)parent.state()).execution();
            require(cursor.handlerId().equals(prefix.handlerId())&&cursor.startedAt().equals(prefix.startedAt())&&cursor.guard().equals(prefix.guard())
                    &&cursor.children().size()==6&&cursor.children().subList(0,5).equals(prefix.children())
                    &&cursor.children().getLast().equals(new CompositeExecution.Child(receipt.command().actionId(),receipt.bodySha256())),
                    "prepared successor proposal changed its complete five originals or sixth reservation");
            for(var original:prepared.children())require(ContinuityActionJournal.lookup(head.state(),original.command().actionId(),archive).filter(original::equals).isPresent(),
                    "prepared successor proposal lost one exact canonical original child");
        }catch(IOException unavailable){throw new UncheckedIOException("actual prepared successor writer admission unavailable",unavailable);}
    }
    /** Exact accepted source qualification only, never a Native permit. */
    private static void requireQualifiedReservedNoEffectBackend(RootRuntimeContext context,
            org.xar.ck3.control.application.advance.ReservedPreparedCleanupNoEffectProof.Originals proof){
        try{
            context.requireActiveGame();requireQualifiedPreparedCleanupBackend(context,proof.prepared());
            for(var original:reservedNoEffectOriginals())verifyPostResumeBackendOriginal(original);
            require(proof.parentReference().equals(new ExactRef("D:\\ck3-state\\ck3-java-resume91_offline04_20261111T071454Z\\business\\continuity\\artifacts\\117ae99b509327ed04b4b7ca04e43de1564afeb1805eb063757e5a5073ddf117.bin",7775L,"117ae99b509327ed04b4b7ca04e43de1564afeb1805eb063757e5a5073ddf117"))&&proof.parentReceipt().sequence()==1940&&proof.preparationReference().equals(new ExactRef("D:\\ck3-state\\ck3-java-resume91_offline04_20261111T071454Z\\business\\continuity\\artifacts\\c46d21ec8fef4be5d12c03a582c42ef73a0a9221e0efa287911c2cc10e7d8854.bin",3902L,"c46d21ec8fef4be5d12c03a582c42ef73a0a9221e0efa287911c2cc10e7d8854"))
                    &&samePreparedNoEffectOriginal(proof.oldSenderStart(),new ExactRef("D:\\ck3-state\\resume91-runtime\\quarkus-dev307-runtime\\attempt79\\ordinal6-successor-only-execution01\\ACTUAL-CHILD-START.json",201L,"dbc9e1a1ead0235b737809d2f86f049a56693e82b7958c49d1027eedd6ec3395"))&&samePreparedNoEffectOriginal(proof.oldSenderExit(),new ExactRef("D:\\ck3-state\\resume91-runtime\\quarkus-dev307-runtime\\attempt79\\ordinal6-successor-only-execution01\\ACTUAL-END.json",1692L,"53946fae1b4278630fe2100676ecd53992fcc9b91a1ddda6a6bfaadf2b85e794"))
                    &&samePreparedNoEffectOriginal(proof.serialBarrier(),new ExactRef("D:\\ck3-state\\resume91-native-integration\\life-postcondition-p0-20261112-01\\POST-C6-SENDER138520-STATUS98-BARRIER-CONDITIONAL-REUSE01.json",11040L,"3f7ebfa6d4f6bee80dcf009b63488549079ed65ef074f060eecb20cc5d693811"))&&samePreparedNoEffectOriginal(proof.acceptedObservation(),new ExactRef("D:\\ck3-state\\resume91-root\\post-vacation-20261107\\POST-C6-ACTUAL-NOEFFECT-OBSERVATION-INDEPENDENT01.json",6005L,"543961f10e81fabfa66aabd119562a0d6ca74a6d2c06aaa308e7b119354bfc0d"))
                    &&proof.command().source().equals(context.source())&&proof.command().before().game().equals(context.game().generation())
                    &&proof.command().sessionId().equals(context.game().sessionId())&&proof.command().before().machineId().equals(context.game().machineId())
                    &&proof.freshStatus().receipt().equals(context.archive().loadRead(new ExactRef("D:\\ck3-state\\ck3-java-resume91_offline04_20261111T071454Z\\business\\continuity\\artifacts\\98ad9e86c03269422cbcd53c570cffed27b6bd2057d1e76b4c9d6008f256682e.bin",13960L,"98ad9e86c03269422cbcd53c570cffed27b6bd2057d1e76b4c9d6008f256682e")))
                    &&proof.freshStatus().receipt().requestId().equals("step-1-fc7d264430ed")
                    &&proof.freshSnapshotAck().requestId().equals("fresh-state-d59fe0b848714064ba0f96ac550014f9")
                    &&ActionCodec.sha256(proof.freshSnapshotAck().originalPacket()).equals("273e97748f01032b95e90664c96d3066486d6328f6d6fed51950c1036b9493c9")
                    &&ActionCodec.sha256(proof.freshFrame().originalPacket()).equals("55b47682ff93416b3c6a376461af7f877d67c81524275380c595bc007d3d87d2")
                    &&proof.issuedAt().equals(Instant.parse("2026-11-14T02:28:40.022650400Z"))
                    &&proof.observationDeadline().equals(proof.freshStatus().receipt().request().deadline())
                    &&proof.freshStatus().receipt().original().custody().orElseThrow().session().connectionGeneration().equals(java.math.BigInteger.valueOf(98))
                    &&proof.freshSnapshotAck().custody().orElseThrow().custodyEpoch().toString().equals("c8c08650-2a72-46d9-8127-93e73c6a7073"),
                    "reserved NoEffect is outside this exact accepted sender/observation/current Root subject");
            var actual=org.xar.ck3.control.contracts.StrictJson.parse(postExitOriginalBytes(new ExactRef("D:\\ck3-state\\resume91-runtime\\quarkus-dev307-runtime\\attempt79\\post-C6-status79-after138520-originals01\\STATUS-AND-FRESH-RESULT.json",4536L,"382c42a1de4306270ab1243b20aa7d6ae77050778ebfa9f4fd073c6074aa64cb")));var expected=actual.get("fresh_custody");
            var custody=proof.freshSnapshotAck().custody().orElseThrow();
            require(custody.writeEntered().equals(postExitEvent(expected.get("write_entered")))&&custody.writeCompleted().equals(postExitEvent(expected.get("write_completed")))
                    &&custody.responseReceived().equals(postExitEvent(expected.get("response_received")))
                    &&custody.originalRequest().matches(postExitOriginalBytes(new ExactRef("D:\\ck3-state\\resume91-runtime\\quarkus-dev307-runtime\\attempt79\\post-C6-status79-after138520-originals01\\fresh-outbound-original.packet",165L,"1cab5c0e37409c9a56d9fa2ae11aa7d120245d0a10bb437e9d306117e718b762")))&&custody.originalResponse().matches(postExitOriginalBytes(new ExactRef("D:\\ck3-state\\resume91-runtime\\quarkus-dev307-runtime\\attempt79\\post-C6-status79-after138520-originals01\\fresh-ack-original.packet",282L,"273e97748f01032b95e90664c96d3066486d6328f6d6fed51950c1036b9493c9")))
                    &&proof.snapshotReceived().equals(postExitEvent(actual.get("fresh_snapshot_received"))),"reserved NoEffect changed actual original endpoint chronology");
            NativeFreshSnapshotPort.verifyAfterOriginal(proof.freshStatus().receipt().original(),proof.freshSnapshotAck(),proof.freshFrame(),proof.snapshotReceived());
            context.requireActiveGame();
        }catch(IOException unavailable){throw new UncheckedIOException("accepted reserved NoEffect source/backend originals unavailable",unavailable);}
    }
    private static List<ExactRef> reservedNoEffectOriginals(){return List.of(new ExactRef("D:\\ck3-state\\resume91-runtime\\quarkus-dev307-runtime\\attempt79\\ordinal6-successor-only-execution01\\ACTUAL-CHILD-START.json",201L,"dbc9e1a1ead0235b737809d2f86f049a56693e82b7958c49d1027eedd6ec3395"),new ExactRef("D:\\ck3-state\\resume91-runtime\\quarkus-dev307-runtime\\attempt79\\ordinal6-successor-only-execution01\\ACTUAL-END.json",1692L,"53946fae1b4278630fe2100676ecd53992fcc9b91a1ddda6a6bfaadf2b85e794"),new ExactRef("D:\\ck3-state\\resume91-native-integration\\life-postcondition-p0-20261112-01\\POST-C6-SENDER138520-STATUS98-BARRIER-CONDITIONAL-REUSE01.json",11040L,"3f7ebfa6d4f6bee80dcf009b63488549079ed65ef074f060eecb20cc5d693811"),new ExactRef("D:\\ck3-state\\resume91-root\\post-vacation-20261107\\POST-C6-ACTUAL-NOEFFECT-OBSERVATION-INDEPENDENT01.json",6005L,"543961f10e81fabfa66aabd119562a0d6ca74a6d2c06aaa308e7b119354bfc0d"),new ExactRef("D:\\ck3-state\\resume91-runtime\\quarkus-dev307-runtime\\attempt79\\post-C6-status79-after138520-originals01\\STATUS-AND-FRESH-RESULT.json",4536L,"382c42a1de4306270ab1243b20aa7d6ae77050778ebfa9f4fd073c6074aa64cb"),new ExactRef("D:\\ck3-state\\resume91-runtime\\quarkus-dev307-runtime\\attempt79\\post-C6-status79-after138520-originals01\\fresh-ack-original.packet",282L,"273e97748f01032b95e90664c96d3066486d6328f6d6fed51950c1036b9493c9"),new ExactRef("D:\\ck3-state\\resume91-runtime\\quarkus-dev307-runtime\\attempt79\\post-C6-status79-after138520-originals01\\fresh-outbound-original.packet",165L,"1cab5c0e37409c9a56d9fa2ae11aa7d120245d0a10bb437e9d306117e718b762"),new ExactRef("D:\\ck3-state\\resume91-runtime\\quarkus-dev307-runtime\\attempt79\\post-C6-status79-after138520-originals01\\fresh-snapshot-original.packet",1237L,"55b47682ff93416b3c6a376461af7f877d67c81524275380c595bc007d3d87d2"),new ExactRef("D:\\ck3-state\\ck3-java-resume91_offline04_20261111T071454Z\\business\\continuity\\artifacts\\d03831e7521bac8054d4dc6eb267b34ea77638fa8e4ede8442b19759b951842d.bin",8963L,"d03831e7521bac8054d4dc6eb267b34ea77638fa8e4ede8442b19759b951842d"),new ExactRef("D:\\ck3-state\\ck3-java-resume91_offline04_20261111T071454Z\\business\\continuity\\artifacts\\1d013c82023a0ff2bc96b1ef9d72ba60ace17e9159ae7eab193d9e564bdf1062.bin",6066L,"1d013c82023a0ff2bc96b1ef9d72ba60ace17e9159ae7eab193d9e564bdf1062"),new ExactRef("D:\\ck3-state\\ck3-java-resume91_offline04_20261111T071454Z\\business\\continuity\\artifacts\\9e38a287d4b92236a8c92523deb9de97d173772cd783280dbc8a0dca866b6312.bin",1353L,"9e38a287d4b92236a8c92523deb9de97d173772cd783280dbc8a0dca866b6312"),new ExactRef("D:\\ck3-state\\ck3-java-resume91_offline04_20261111T071454Z\\business\\continuity\\artifacts\\98ad9e86c03269422cbcd53c570cffed27b6bd2057d1e76b4c9d6008f256682e.bin",13960L,"98ad9e86c03269422cbcd53c570cffed27b6bd2057d1e76b4c9d6008f256682e"));}
    private static void requireReservedNoEffectPrefix(org.xar.ck3.control.continuity.ContinuityState state,
            org.xar.ck3.control.application.advance.ReservedPreparedCleanupNoEffectProof.Originals proof,ActionPorts.OutcomeArchive archive){
        require(ContinuityActionJournal.lookup(state,proof.parentReceipt().command().actionId(),archive).filter(proof.parentReceipt()::equals).isPresent(),
                "reserved NoEffect is not over its exact original current parent");
        for(var original:proof.children())require(ContinuityActionJournal.lookup(state,original.command().actionId(),archive).filter(original::equals).isPresent(),
                "reserved NoEffect lost an exact canonical settled predecessor");
        require(ContinuityActionJournal.lookup(state,proof.command().actionId(),archive).isEmpty(),"reserved NoEffect is not the first child lifecycle event");
    }
    private static void verifyQualifiedReservedNoEffect(RootRuntimeContext context,
            Optional<org.xar.ck3.control.continuity.writer.WriterContracts.Head> proposedHead,ActionReceipt receipt,ActionPorts.OutcomeArchive archive){
        var terminal=(ActionState.ReservedPreparedCleanupNoEffectConfirmed)receipt.state();
        var proof=org.xar.ck3.control.application.advance.ReservedPreparedCleanupNoEffectProof.fullLoadAndVerifyState(receipt,
                terminal.proofReference(),terminal.preparationReference(),archive,new LifeAdvanceRootReplay(RootAdvanceInfrastructureFactory.freshFrameLoader(context.frameLoader())));
        requireQualifiedReservedNoEffectBackend(context,proof);
        try{
            var same=context.borrowedSession();context.writer().requireSession(same);var actual=same.head();
            var head=proposedHead.orElse(actual);require(head.digest().equals(actual.digest()),"reserved NoEffect replay crossed the actual writer head");
            if(receipt.sequence()<=head.state().sequence()){
                ContinuityActionJournal.requireHistoricalReceipt(head.state(),receipt,archive);
                String eventName=String.format(java.util.Locale.ROOT,"%08d.json",receipt.sequence());
                var eventPins=actual.documents().stream().filter(pin->java.nio.file.Path.of(pin.reference().path()).getFileName().toString().equals(eventName)).toList();
                require(eventPins.size()==1,"reserved NoEffect lacks its unique actual immutable canonical event");
                var edge=same.readHistoricalTransition(eventPins.getFirst());
                require(edge.sequence()==receipt.sequence()&&edge.kind().equals(ContinuityActionJournal.KIND),"reserved NoEffect canonical event kind/sequence differs");
                requireReservedNoEffectPrefix(edge.before(),proof,archive);
                require(ContinuityActionJournal.lookup(edge.after(),receipt.command().actionId(),archive).filter(receipt::equals).isPresent(),
                        "reserved NoEffect actual canonical edge does not contain its original terminal");return;
            }
            require(receipt.sequence()==head.state().sequence()+1&&!head.snapshotNeedsRecovery()&&head.indexRepairs().isEmpty()
                    &&context.actions() instanceof RootApplicationSession,"reserved NoEffect requires the complete actual next canonical writer state");
            requireReservedNoEffectPrefix(head.state(),proof,archive);
            // All full originals/backend/WAL/current-prefix work above precedes the private callback's short token mint.
            ((RootApplicationSession)context.actions()).requireReservedNoEffectProposal(receipt,proof);
        }catch(IOException unavailable){throw new UncheckedIOException("actual reserved NoEffect first-event source admission unavailable",unavailable);}
    }
    /** Actual installed source/backend qualification for the independently accepted fifth-child observation only. */
    private static void requireQualifiedPreparedNoEffectBackend(RootRuntimeContext context,
            org.xar.ck3.control.application.advance.PreparedCleanupNoEffectProof.Originals proof){
        try{
            context.requireActiveGame();requireQualifiedPreparedCleanupBackend(context,proof.prepared());
            for(var original:preparedNoEffectOriginals())verifyPostResumeBackendOriginal(original);
            require(proof.parentReference().equals(new ExactRef("D:\\ck3-state\\ck3-java-resume91_offline04_20261111T071454Z\\business\\continuity\\artifacts\\cc914fca3a10bcfcd9b9f44e0155cfd61e7c793aeb3b6fcb03a9d3fee0b05d86.bin",7344L,"cc914fca3a10bcfcd9b9f44e0155cfd61e7c793aeb3b6fcb03a9d3fee0b05d86"))&&proof.child5Reference().equals(new ExactRef("D:\\ck3-state\\ck3-java-resume91_offline04_20261111T071454Z\\business\\continuity\\artifacts\\45e6c8e2159c52d064475c9689c0510632cf8aeb6b6e5e580688825f7a15dd38.bin",2788L,"45e6c8e2159c52d064475c9689c0510632cf8aeb6b6e5e580688825f7a15dd38"))&&proof.preparationReference().equals(new ExactRef("D:\\ck3-state\\ck3-java-resume91_offline04_20261111T071454Z\\business\\continuity\\artifacts\\3c9f7ede670f6c165c21ef79113b80214655674bf25fdc0e9a4101190b065ee7.bin",3079L,"3c9f7ede670f6c165c21ef79113b80214655674bf25fdc0e9a4101190b065ee7"))
                    &&proof.parentReceipt().sequence()==1937&&proof.child5().sequence()==1938
                    &&proof.originalPreparedState().phase()==org.xar.ck3.control.application.action.PreparedCleanupAction.Phase.PREPARED
                    &&proof.originalPreparedState().lateBindingReference().isEmpty()&&proof.originalPreparedState().originalDispatch().isEmpty()
                    &&proof.originalPreparedState().capturedPostAcknowledgement().isEmpty()&&proof.originalPreparedState().failureReference().isEmpty()
                    &&samePreparedNoEffectOriginal(proof.oldSenderStart(),new ExactRef("D:\\ck3-state\\resume91-runtime\\quarkus-dev307-runtime\\attempt79\\prepared-cleanup-B-only-execution01\\ACTUAL-CHILD-START.json",213L,"475b06cf684ddd1ea8d9ff1a7c26e4ed2d075e86839d9533e7387eb6cace2dc3"))&&samePreparedNoEffectOriginal(proof.oldSenderExit(),new ExactRef("D:\\ck3-state\\resume91-runtime\\quarkus-dev307-runtime\\attempt79\\prepared-cleanup-B-only-execution01\\ACTUAL-END.json",1511L,"d2d53222fabf5004f891d8d325305e5f7790a39f3cbfb9450610448504bc9385"))
                    &&samePreparedNoEffectOriginal(proof.serialBarrier(),new ExactRef("D:\\ck3-state\\resume91-native-integration\\life-postcondition-p0-20261112-01\\POST-B-SENDER154044-STATUS-BARRIER-CONDITIONAL-REUSE01.json",3973L,"02b677a67f7c1c52fd839b2c2721eaa98dae1f22deb18817343e14bd37ec1d0b"))&&samePreparedNoEffectOriginal(proof.acceptedObservation(),new ExactRef("D:\\ck3-state\\resume91-root\\post-vacation-20261107\\POST-B-ACTUAL-NOEFFECT-OBSERVATION-INDEPENDENT01.json",4921L,"3a809080c712a6c13babf954a4d0cfe1eddf02d69785aec6fcf02d6a34389de6"))
                    &&proof.freshStatus().receipt().equals(context.archive().loadRead(new ExactRef("D:\\ck3-state\\ck3-java-resume91_offline04_20261111T071454Z\\business\\continuity\\artifacts\\283531a053c9f8d76fcb7387777312048fc6e78da20a844b83caf1186b85c310.bin",13939L,"283531a053c9f8d76fcb7387777312048fc6e78da20a844b83caf1186b85c310")))
                    &&proof.freshSnapshotAck().requestId().equals("fresh-state-17d4d26e6687405d8235d3b7dfed80cf")
                    &&proof.freshStatus().receipt().requestId().equals("step-1-6ca349b5fd03")
                    &&ActionCodec.sha256(proof.freshSnapshotAck().originalPacket()).equals("d7e5b9fac1c04af7c428165cb542dc7d991ebcbffdd63d1c14b29c52ce535d6a")
                    &&ActionCodec.sha256(proof.freshFrame().originalPacket()).equals("418706b3ec8abffbb5d50a5b8e7292c37e8c6a107116d9f5a586adb4ea4f9a7b")
                    &&proof.issuedAt().equals(Instant.parse("2026-11-13T22:10:46.991414900Z"))
                    &&proof.observationDeadline().equals(proof.freshStatus().receipt().request().deadline())
                    &&proof.freshStatus().receipt().original().custody().orElseThrow().session().connectionGeneration().equals(java.math.BigInteger.valueOf(95))
                    &&proof.freshSnapshotAck().custody().orElseThrow().custodyEpoch().toString().equals("71f473cf-772e-4ef5-8a1b-2c6d678c17f2"),
                    "prepared NoEffect proof is outside the actual accepted sender/observation/current Root backend subject");
            var expected=org.xar.ck3.control.contracts.StrictJson.parse(postExitOriginalBytes(new ExactRef("D:\\ck3-state\\resume91-runtime\\quarkus-dev307-runtime\\attempt79\\post-B-status79-after154044-originals03\\STATUS-AND-FRESH-RESULT.json",4530L,"203f465c621ffa2319ec02c1f949f3e2539b43fb591461fd10713db55513a1d0")));
            var custody=proof.freshSnapshotAck().custody().orElseThrow();var original=expected.get("fresh_custody");
            require(custody.writeEntered().equals(postExitEvent(original.get("write_entered")))
                    &&custody.writeCompleted().equals(postExitEvent(original.get("write_completed")))
                    &&custody.responseReceived().equals(postExitEvent(original.get("response_received")))
                    &&custody.originalRequest().matches(postExitOriginalBytes(new ExactRef("D:\\ck3-state\\resume91-runtime\\quarkus-dev307-runtime\\attempt79\\post-B-status79-after154044-originals03\\fresh-outbound-original.packet",165L,"999ad1cdd782ae43e8508d385d620ae3c18552c21e4069fcccab89b76506a9ba")))&&custody.originalResponse().matches(postExitOriginalBytes(new ExactRef("D:\\ck3-state\\resume91-runtime\\quarkus-dev307-runtime\\attempt79\\post-B-status79-after154044-originals03\\fresh-ack-original.packet",282L,"d7e5b9fac1c04af7c428165cb542dc7d991ebcbffdd63d1c14b29c52ce535d6a")))
                    &&proof.snapshotReceived().equals(postExitEvent(expected.get("fresh_snapshot_received"))),
                    "prepared NoEffect changed the independently retained actual endpoint event chronology");
            NativeFreshSnapshotPort.verifyAfterOriginal(proof.freshStatus().receipt().original(),proof.freshSnapshotAck(),proof.freshFrame(),proof.snapshotReceived());
            context.requireActiveGame();
        }catch(IOException unavailable){throw new UncheckedIOException("accepted prepared NoEffect original/backend qualification unavailable",unavailable);}
    }
    private static boolean samePreparedNoEffectOriginal(ExactRef material,ExactRef original){
        return material.bytes()==original.bytes()&&material.sha256().equals(original.sha256());
    }
    private static List<ExactRef> preparedNoEffectOriginals(){return List.of(new ExactRef("D:\\ck3-state\\resume91-runtime\\quarkus-dev307-runtime\\attempt79\\prepared-cleanup-B-only-execution01\\ACTUAL-CHILD-START.json",213L,"475b06cf684ddd1ea8d9ff1a7c26e4ed2d075e86839d9533e7387eb6cace2dc3"),new ExactRef("D:\\ck3-state\\resume91-runtime\\quarkus-dev307-runtime\\attempt79\\prepared-cleanup-B-only-execution01\\ACTUAL-END.json",1511L,"d2d53222fabf5004f891d8d325305e5f7790a39f3cbfb9450610448504bc9385"),new ExactRef("D:\\ck3-state\\resume91-native-integration\\life-postcondition-p0-20261112-01\\POST-B-SENDER154044-STATUS-BARRIER-CONDITIONAL-REUSE01.json",3973L,"02b677a67f7c1c52fd839b2c2721eaa98dae1f22deb18817343e14bd37ec1d0b"),new ExactRef("D:\\ck3-state\\resume91-root\\post-vacation-20261107\\POST-B-ACTUAL-NOEFFECT-OBSERVATION-INDEPENDENT01.json",4921L,"3a809080c712a6c13babf954a4d0cfe1eddf02d69785aec6fcf02d6a34389de6"),new ExactRef("D:\\ck3-state\\resume91-runtime\\quarkus-dev307-runtime\\attempt79\\post-B-status79-after154044-originals03\\STATUS-AND-FRESH-RESULT.json",4530L,"203f465c621ffa2319ec02c1f949f3e2539b43fb591461fd10713db55513a1d0"),new ExactRef("D:\\ck3-state\\resume91-runtime\\quarkus-dev307-runtime\\attempt79\\post-B-status79-after154044-originals03\\fresh-ack-original.packet",282L,"d7e5b9fac1c04af7c428165cb542dc7d991ebcbffdd63d1c14b29c52ce535d6a"),new ExactRef("D:\\ck3-state\\resume91-runtime\\quarkus-dev307-runtime\\attempt79\\post-B-status79-after154044-originals03\\fresh-outbound-original.packet",165L,"999ad1cdd782ae43e8508d385d620ae3c18552c21e4069fcccab89b76506a9ba"),new ExactRef("D:\\ck3-state\\resume91-runtime\\quarkus-dev307-runtime\\attempt79\\post-B-status79-after154044-originals03\\fresh-snapshot-original.packet",1237L,"418706b3ec8abffbb5d50a5b8e7292c37e8c6a107116d9f5a586adb4ea4f9a7b"));}
    private static void verifyQualifiedPreparedNoEffect(RootRuntimeContext context,
            Optional<org.xar.ck3.control.continuity.writer.WriterContracts.Head> proposedHead,ActionReceipt receipt,ActionPorts.OutcomeArchive archive){
        var terminal=(ActionState.PreparedCleanupNoEffectConfirmed)receipt.state();
        org.xar.ck3.control.application.advance.PreparedCleanupNoEffectProof.verifyArchivedState(receipt,terminal.proofReference(),terminal.originalPreparedState(),archive);
        var proof=org.xar.ck3.control.application.advance.PreparedCleanupNoEffectProof.load(terminal.proofReference(),archive,
                new LifeAdvanceRootReplay(RootAdvanceInfrastructureFactory.freshFrameLoader(context.frameLoader())));
        requireQualifiedPreparedNoEffectBackend(context,proof);
        try{
            var same=context.borrowedSession();context.writer().requireSession(same);
            var head=proposedHead.orElseGet(()->{try{return same.head();}catch(IOException failure){throw new UncheckedIOException(failure);}});
            require(head.digest().equals(same.head().digest()),"prepared NoEffect replay crossed the actual writer head");
            if(receipt.sequence()<=head.state().sequence()){ContinuityActionJournal.requireHistoricalReceipt(head.state(),receipt,archive);return;}
            require(receipt.sequence()==head.state().sequence()+1&&context.actions() instanceof RootApplicationSession,
                    "prepared NoEffect proposal skipped its actual next writer sequence");
            ((RootApplicationSession)context.actions()).requirePreparedNoEffectProposal(receipt,proof);
            require(ContinuityActionJournal.lookup(head.state(),proof.parentReceipt().command().actionId(),archive).filter(proof.parentReceipt()::equals).isPresent()
                    &&ContinuityActionJournal.lookup(head.state(),proof.child5().command().actionId(),archive).filter(proof.child5()::equals).isPresent(),
                    "prepared NoEffect proposal no longer holds its exact original parent/fifth child");
        }catch(IOException unavailable){throw new UncheckedIOException("actual prepared NoEffect writer admission unavailable",unavailable);}
    }
    /** Mandatory actual Root callback on every archived NoEffect terminal, independent of public DATA records. */
    static void verifyQualifiedPostExitNoEffect(RootRuntimeContext context,ActionReceipt terminal,ActionPorts.OutcomeArchive archive) {
        require(terminal.state() instanceof ActionState.CleanupNoEffectConfirmed,"actual NoEffect verifier accepts only its dedicated state");
        var value=(ActionState.CleanupNoEffectConfirmed)terminal.state();
        var proof=PostExitCleanupNoEffectProof.verifyArchivedState(terminal,value.proofReference(),value.originalAttempt(),value.originalDispatch(),archive);
        requireQualifiedPostExitNoEffect(context,proof);
    }
    private static void requireQualifiedPostExitNoEffect(RootRuntimeContext context,PostExitCleanupNoEffectProof.Originals proof) {
        try {
            context.requireActiveGame();
            requirePostResumeBackendSubject(proof.original().parent(),context.game().generation(),context.game().machineId(),
                    context.game().sessionId(),context.source(),context.game().launchPlan().sources().review().bridgeDll());
            for(var original:postResumeBackendOriginals())verifyPostResumeBackendOriginal(original);
            for(var original:postExitNoEffectOriginals())verifyPostResumeBackendOriginal(original);
            require(proof.parentReference().equals(new ExactRef("D:\\ck3-state\\ck3-java-resume91_offline04_20261111T071454Z\\business\\continuity\\artifacts\\11291294f9e9421ef63f6bff93ec06b82a7c06d448a5b779ab8ef7a50cd868fb.bin",6909L,"11291294f9e9421ef63f6bff93ec06b82a7c06d448a5b779ab8ef7a50cd868fb"))&&proof.child4Reference().equals(new ExactRef("D:\\ck3-state\\ck3-java-resume91_offline04_20261111T071454Z\\business\\continuity\\artifacts\\4879621f4401ba2e7f466fdea2bb2872436b77cdfe0b1f4df1f79b901c68314d.bin",2513L,"4879621f4401ba2e7f466fdea2bb2872436b77cdfe0b1f4df1f79b901c68314d"))
                    &&proof.authorizationReference().equals(new ExactRef("D:\\ck3-state\\ck3-java-resume91_offline04_20261111T071454Z\\business\\continuity\\artifacts\\4e82d98d78988332cac22cdbdad8e5f1fdff1224d4c004e7ea32124dd3d54e37.bin",3135L,"4e82d98d78988332cac22cdbdad8e5f1fdff1224d4c004e7ea32124dd3d54e37"))&&proof.parentReceipt().sequence()==1935&&proof.child4().sequence()==1934
                    &&proof.freshStatus().receipt().equals(context.archive().loadRead(new ExactRef("D:\\ck3-state\\ck3-java-resume91_offline04_20261111T071454Z\\business\\continuity\\artifacts\\2ad7203aa81aad31179147cbec521f538b7bb4c6a364df84a4222c5e1bf78906.bin",13951L,"2ad7203aa81aad31179147cbec521f538b7bb4c6a364df84a4222c5e1bf78906")))
                    &&proof.oldSenderExit().bytes()==1588&&proof.oldSenderExit().sha256().equals("d112ae78cf7c8496f646fba5ac6fb12b22fbce5bcb64455e4bb6be98316ccb3f")
                    &&proof.serialBarrier().bytes()==19350&&proof.serialBarrier().sha256().equals("d4727bdd2d7d071436c0ffe6e572bc30d705a23729a8444236f03529fec5923c")
                    &&proof.backendDllSha256().equals("5674ce61b12843a77c0e7da2130578f9201aae81cbd7288d8af08c35905b21ff")
                    &&proof.freshSnapshotAck().requestId().equals("fresh-state-cfb92c5450704ae188cdeffcbba8453c")
                    &&proof.freshStatus().receipt().requestId().equals("step-1-ef6a4d890846")
                    &&ActionCodec.sha256(proof.freshSnapshotAck().originalPacket()).equals("4ef6892edfbf941ae5b54464031ca0fa16a3b25769fd372423d81b90d5957222")
                    &&ActionCodec.sha256(proof.freshFrame().originalPacket()).equals("b3a3f0cd4d1666fa1a521666d887498928ab8e655b310a9873a1d2c263355c1d")
                    &&proof.snapshotReceived().order().equals(java.math.BigInteger.valueOf(285))
                    &&proof.snapshotReceived().observedAt().equals(Instant.parse("2026-11-13T15:27:48.781054700Z"))
                    &&proof.freshSnapshotAck().custody().orElseThrow().custodyEpoch().toString().equals("34db79c7-5027-423a-9dae-8d38a8271751")
                    &&proof.freshStatus().receipt().original().custody().orElseThrow().session().connectionGeneration().equals(java.math.BigInteger.valueOf(89)),
                    "NoEffect proof is outside the actual independently accepted C81 post-exit observation/backend lifetime");
            require(((ActionState.Unknown)proof.child4().state()).attempt().isEmpty()
                    &&((ActionState.Unknown)proof.child4().state()).dispatch().isEmpty(),"actual NoEffect source must preserve the original empty options");
            NativeFreshSnapshotPort.verifyAfterOriginal(proof.freshStatus().receipt().original(),proof.freshSnapshotAck(),proof.freshFrame(),proof.snapshotReceived());
            var retainedResult=org.xar.ck3.control.contracts.StrictJson.parse(postExitOriginalBytes(new ExactRef("D:\\ck3-state\\resume91-runtime\\quarkus-dev307-runtime\\attempt79\\postexit-status79-barrier02\\originals\\STATUS-AND-FRESH-RESULT.json",4539L,"bdc7165f1097ea1b86ae411271d288cdf167704a7df77330dfd944f4c423af10")));
            var actualCustody=proof.freshSnapshotAck().custody().orElseThrow();var expectedCustody=retainedResult.get("fresh_custody");
            require(actualCustody.writeEntered().equals(postExitEvent(expectedCustody.get("write_entered")))
                    &&actualCustody.writeCompleted().equals(postExitEvent(expectedCustody.get("write_completed")))
                    &&actualCustody.responseReceived().equals(postExitEvent(expectedCustody.get("response_received")))
                    &&actualCustody.originalRequest().matches(postExitOriginalBytes(new ExactRef("D:\\ck3-state\\resume91-runtime\\quarkus-dev307-runtime\\attempt79\\postexit-status79-barrier02\\originals\\fresh-outbound-original.packet",165L,"2dce1a300e856e372e86c39d1df96e536491be5cf473a446bebfb6a14c281434")))
                    &&actualCustody.originalResponse().matches(postExitOriginalBytes(new ExactRef("D:\\ck3-state\\resume91-runtime\\quarkus-dev307-runtime\\attempt79\\postexit-status79-barrier02\\originals\\fresh-ack-original.packet",282L,"4ef6892edfbf941ae5b54464031ca0fa16a3b25769fd372423d81b90d5957222")))
                    &&proof.snapshotReceived().equals(postExitEvent(retainedResult.get("fresh_snapshot_received"))),
                    "NoEffect proof altered the independently retained actual endpoint event chronology");
            context.requireActiveGame();
        } catch(IOException unavailable){throw new UncheckedIOException("accepted post-exit NoEffect original/backend qualification unavailable",unavailable);}
    }
    private static NativeRequestChronology.Event postExitEvent(com.fasterxml.jackson.databind.JsonNode value) {
        return new NativeRequestChronology.Event(new java.math.BigInteger(value.path("order").asText()),Instant.parse(value.path("observed_at").asText()));
    }
    private static byte[] postExitOriginalBytes(ExactRef original)throws IOException {
        verifyPostResumeBackendOriginal(original);
        byte[] raw=java.nio.file.Files.readAllBytes(java.nio.file.Path.of(original.path()));
        require(raw.length==original.bytes()&&ActionCodec.sha256(raw).equals(original.sha256()),"accepted post-exit bytes changed between qualification and consumption");
        return raw;
    }
    private static List<ExactRef> postExitNoEffectOriginals() {
        return List.of(new ExactRef("D:/ck3-state/resume91-root/post-vacation-20261107/POSTEXIT-ACTUAL-STATUS-AND-FRESH-NOEFFECT-INDEPENDENT01.json",6215L,"f1fb0ece4415626bd2c2ed543d096d0dac43c82f8679f16d4aa7d0f19ab9cd14"),
                new ExactRef("D:/ck3-state/resume91-root/post-vacation-20261107/POSTEXIT-STATUS-BARRIER-INDEPENDENT01.json",847L,"97bb5614d242a47384a439cc18bf0d6b5df943e008b895f3d6981944a4ac5b27"),
                new ExactRef("D:/ck3-state/resume91-native-integration/life-postcondition-p0-20261112-01/C81-POSTEXIT-STATUS-BARRIER-CONDITIONAL-QUALIFICATION01.json",19350L,"d4727bdd2d7d071436c0ffe6e572bc30d705a23729a8444236f03529fec5923c"),
                new ExactRef("D:\\ck3-state\\resume91-runtime\\quarkus-dev307-runtime\\attempt79\\C81-CHILD4-FRESH-WINDOW-P0\\EXACT-FAILED-JAVA-RELEASED79.json",1588L,"d112ae78cf7c8496f646fba5ac6fb12b22fbce5bcb64455e4bb6be98316ccb3f"),
                new ExactRef("D:/ck3-state/resume91-runtime/quarkus-dev307-runtime/attempt79/postexit-status79-barrier02/ACTUAL-STATUS-AND-AFTER-FRESH-BARRIER-OBSERVATIONS01.json",6939L,"22c77c280cacb30163524d9ab6f7fe9060262575926f98132cb6b39363cb5911"),
                new ExactRef("D:\\ck3-state\\resume91-runtime\\quarkus-dev307-runtime\\attempt79\\postexit-status79-barrier02\\originals\\STATUS-AND-FRESH-RESULT.json",4539L,"bdc7165f1097ea1b86ae411271d288cdf167704a7df77330dfd944f4c423af10"),
                new ExactRef("D:\\ck3-state\\resume91-runtime\\quarkus-dev307-runtime\\attempt79\\postexit-status79-barrier02\\originals\\fresh-ack-original.packet",282L,"4ef6892edfbf941ae5b54464031ca0fa16a3b25769fd372423d81b90d5957222"),
                new ExactRef("D:\\ck3-state\\resume91-runtime\\quarkus-dev307-runtime\\attempt79\\postexit-status79-barrier02\\originals\\fresh-outbound-original.packet",165L,"2dce1a300e856e372e86c39d1df96e536491be5cf473a446bebfb6a14c281434"),
                new ExactRef("D:\\ck3-state\\resume91-runtime\\quarkus-dev307-runtime\\attempt79\\postexit-status79-barrier02\\originals\\fresh-snapshot-original.packet",1237L,"b3a3f0cd4d1666fa1a521666d887498928ab8e655b310a9873a1d2c263355c1d"));
    }
    /** Pure exact-subject DATA check for the private installed provider; this method grants no runtime or Native custody. */
    static void requirePostResumeBackendSubject(ActionReceipt original,org.xar.ck3.control.contracts.GameGeneration actualGame,
            String actualMachine,String actualSession,org.xar.ck3.control.g2.common.G2Source actualSource,
            org.xar.ck3.control.build.ControlBuild.FileRef configuredDll) {
        Objects.requireNonNull(original);Objects.requireNonNull(actualGame);Objects.requireNonNull(actualSource);Objects.requireNonNull(configuredDll);
        var command=original.command();var source=command.source();
        require(original.version()==1&&original.sequence()>=1929&&original.state() instanceof ActionState.CompositeUnknown,
                "backend qualification needs the original C81 UNKNOWN or its genuine read-only successor");
        var execution=((ActionState.CompositeUnknown)original.state()).execution();
        require(execution.children().equals(List.of(new CompositeExecution.Child("child-7938d189691abf36e8dd9f81d9263c618360199164c5bd549d0099d1a701a24e","14a5bcb10873efaad73669966d67c5f1d61c453d8d46c43e40359bdde936f10d"),new CompositeExecution.Child("child-dad106b753079601a7665ea5350d32051eb276f86ef5256652c87ea1fe75e251","d1853597d684c1fc2ed0ada5d7e165ceb72301ceaf6b2f1ddbdad621039f1142"),new CompositeExecution.Child("child-0af90bd0d3d43fef8dad699c7889d03e65ff2cc404e39d05b10e2c3dbf40b927","9dedf39f2d2fbbb07a78396c104f442ac7035b199a9c75ed180a01c1f6db5b92"))),
                "backend qualification changed the immutable original three-child vector");
        require(command.actionId().equals("action-c1bbea09a8bffc735d1ac887e9c3020a1de4f59cca8d647378ec7a3efc47c5a8")
                &&original.bodySha256().equals("46181a6487eb31190b39704a9525f93809b0f77bf4428e3ddf4b1072f86f5326")
                &&original.bodySha256().equals(ActionCodec.bodySha256(command)),"backend qualification belongs only to the exact original C81 command");
        require(actualGame.pid()==145132&&actualGame.creationFiletime().value().toString().equals("134388549310428814")
                &&command.before().game().equals(actualGame)
                &&actualMachine.equals("xenoamess-full-tower-eb9d2c1186")&&command.before().machineId().equals(actualMachine)
                &&actualSession.equals("resume91_offline04_20261111T071454Z")&&command.sessionId().equals(actualSession)
                &&actualSource.equals(source)&&source.machineId().equals(actualMachine),
                "backend qualification crossed the actual original Game birth, machine, session or physical Root source");
        require(source.observedAtUtc().equals("2026-11-11T08:19:30.922362400Z")
                &&source.exactBuild().equals("98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518")
                &&source.sourceRef().bytes()==29283
                &&source.sourceRef().sha256().equals("47edcdab7bc1f1f81caa0b30c1717d5bb897584d23fe765c93b271357d0035fc")
                &&java.nio.file.Path.of(source.sourceRef().path()).normalize().equals(java.nio.file.Path.of("C:/ck3-state/resume91-root/quarkus-dev307/build307/ck3-control-local-service/classes/org/xar/ck3/control/service/root/RootOrdinaryRuntimeAssembly.class").normalize()),
                "backend qualification crossed its complete original G2 source");
        require(configuredDll.bytes()==21790208&&configuredDll.sha256().equals("5674ce61b12843a77c0e7da2130578f9201aae81cbd7288d8af08c35905b21ff")
                &&java.nio.file.Path.of(configuredDll.path()).normalize().equals(java.nio.file.Path.of("D:/codex-ck3-background/ck3-java-g2-resume-r4-20261025/native63/m0-dev01/build/xar_ck3_bridge.dll").normalize()),
                "configured DLL no longer agrees with the independently qualified loaded-binary chain");
    }
    /** Integrity of one fixed reviewed original only; arbitrary references do not become qualifications. */
    static void verifyPostResumeBackendOriginal(ExactRef ref)throws IOException {
        Objects.requireNonNull(ref);require(ref.bytes()>0&&ref.bytes()<=65536,"bounded backend original required");
        var path=java.nio.file.Path.of(ref.path());
        require(path.isAbsolute()&&java.nio.file.Files.isRegularFile(path,java.nio.file.LinkOption.NOFOLLOW_LINKS)
                &&java.nio.file.Files.size(path)==ref.bytes(),"backend original file is unavailable or changed");
        byte[] bytes;
        try(var input=java.nio.file.Files.newInputStream(path,java.nio.file.LinkOption.NOFOLLOW_LINKS)) {
            bytes=input.readNBytes(Math.toIntExact(ref.bytes())+1);
        }
        require(bytes.length==ref.bytes()&&ActionCodec.sha256(bytes).equals(ref.sha256()),"backend original bytes changed");
        RootPreparedCleanupScope.retainVerifiedBackendSource(ref);
    }
    private static List<ExactRef> postResumeBackendOriginals() {
        return List.of(
                new ExactRef("D:/ck3-state/resume91-native-integration/life-postcondition-p0-20261112-01/C81-EXACTDLL-GENERATION-SERIALIZATION-CONDITIONAL-QUALIFICATION01.json",17453,"be9ca005c687e307cdc71d9de03f33102a2f2bae214b4c5fa19e42ad1417c5e8"),
                new ExactRef("D:/ck3-state/resume91-runtime/quarkus-dev307-runtime/attempt76/C81-DEADLINE-UNKNOWN-P0/LOADED-DLL-ORIGINAL-FILEID-AND-RUNTIME-CONTINUITY-RO01.json",8141,"f6da6cd08cd808a3809041e08fbfd2d137b610d828b93661c6fe2b2b2fd6635e"),
                new ExactRef("D:/ck3-state/resume91-native-integration/life-postcondition-p0-20261112-01/C81-NATIVE-EXACTDLL-TARGET-OBJECT-CODE-MATCH-RO01.json",12196,"58b91b6de0c72e394e06ef45945d9eaa84bb0f3ac17b4f06e6412cb80df5a8fb"),
                new ExactRef("D:/ck3-state/resume91-native-integration/life-postcondition-p0-20261112-01/C81-EXACTDLL-ARM3592-DUMPBIN-RANGE01.txt",33623,"e0cbce1c02171e4e746994cfadcbabd68bfba8c1258c8bfedfc8bba6c2b3f4c4"),
                new ExactRef("D:/ck3-state/resume91-native-integration/life-postcondition-p0-20261112-01/C81-EXACTDLL-CANCEL144-DUMPBIN-RANGE01.txt",2037,"6fcfeea89e2b78e39dee68a5e7a68ebf3c0f226f94bb9bf65ea2ffb7a15e2043"),
                new ExactRef("D:/ck3-state/resume91-native-integration/life-postcondition-p0-20261112-01/C81-EXACTDLL-ARM-CANCEL-DIRECT-CALL-XREFS-RO01.json",616,"f5c2cfbe7909962da0bde6d8c6dce0fed4514f2f9ba4ac4d27ff8bbe3a7fe78b"),
                new ExactRef("D:/ck3-state/resume91-native-integration/life-postcondition-p0-20261112-01/C81-EXACTDLL-SERIAL-DISPATCH-NAMED-OBJECT-MATCH-RO02.json",2876,"68f2a46d79e0cc937fea62331f707f3ea4819046c1e53e9cd9dbc771170e97d0"),
                new ExactRef("D:/ck3-state/resume91-native-integration/life-postcondition-p0-20261112-01/C81-EXACTDLL-DISPATCH-CALLERS-AND-GEN-TARGET-OPERANDS-RO03.json",3693,"08bfec0aa7c3d8b0ff767e451dc7474f0c477839338e5a4a2a7306887fe553b3"),
                new ExactRef("D:/ck3-state/resume91-native-integration/life-postcondition-p0-20261112-01/C81-EXACTDLL-START395-DUMPBIN-RANGE01.txt",5046,"eaede407bbbc14aafbdcfc4950cae52407548292cdb7f9860e99a39e394cb458"),
                new ExactRef("D:/ck3-state/resume91-native-integration/life-postcondition-p0-20261112-01/C81-EXACTDLL-STOP-DUMPBIN-RANGE01.txt",2026,"4f42b3243d9288d9260e3ac13cea4894a63f65bda28fe214e5bbdd1f3af80d1a"),
                new ExactRef("D:/ck3-state/resume91-native-integration/life-postcondition-p0-20261112-01/C81-EXACTDLL-WORKER_TAIL669-DUMPBIN-RANGE01.txt",7627,"d1092d6d0b08f835336f45f81fec8f7824f2af739413fd87d7d50b3e5db37574"),
                new ExactRef("D:/ck3-state/resume91-native-integration/life-postcondition-p0-20261112-01/C81-EXACTDLL-INSTALL904-DUMPBIN-RANGE01.txt",11063,"bec7a9a6755f6f0748134742091c9af2644a4c4d462d1f692aedd95bc9a811e2"),
                new ExactRef("D:/ck3-state/resume91-native-integration/life-postcondition-p0-20261112-01/C81-EXACTDLL-INSTALL12004_193-DUMPBIN-RANGE01.txt",2519,"74e1c61f6f1ecf126291ac3cf638c996f49a51dec95d489ed00fe0d3f8a19498"),
                new ExactRef("D:/ck3-state/resume91-native-integration/life-postcondition-p0-20261112-01/C81-EXACTDLL-GENRESET96-DUMPBIN-RANGE01.txt",1270,"7bc4c40065a2fac72fb60f080129e0c89886abc49786ad6cc036701f5a843633"),
                new ExactRef("D:/ck3-state/resume91-native-integration/life-postcondition-p0-20261112-01/C81-EXACTDLL-INIT-INSTALL-DIRECT-CALLERS-RO05.json",780,"54c9f2f133b8d6a1cd43c23fc2ea03616763ca2a3b9f483c374af7181fcf4a29"),
                new ExactRef("D:/ck3-state/resume91-native-integration/life-postcondition-p0-20261112-01/C81-EXACTDLL-ACTIVE-INSTALL-LIFETIME-TARGETS-RO06.json",1731,"bd35b5f99727d501fe69e0ecadbed0fdfbe9ccf8c98b61b58c7a403c16cea4a1"),
                new ExactRef("D:/ck3-state/resume91-runtime/current-resume268/sway-p0-recovery04-20261111T071454Z/physical-owner-offline04/owner.json",20435,"db46cbf8f95dd071c82ade4cd39d7351c259f92924d0a16ac09dcb9d5ca3ed20"),
                new ExactRef("D:/ck3-state/ck3-java-resume91_offline04_20261111T071454Z/artifacts/native-launch/event-000003.json",589,"1b4efaded92e701aa155381f74e27926b7fd7e6e40199a30a8c37c6253d66759"),
                new ExactRef("D:/ck3-state/ck3-java-resume91_offline04_20261111T071454Z/artifacts/native-launch/event-000004.json",1062,"2b5f3dbcdfe8dac32a3f5d760a7f0c6cd9b69d01ec07eaaca3b11cea2d2200cd"),
                new ExactRef("D:/ck3-state/ck3-java-resume91_offline04_20261111T071454Z/artifacts/native-launch/event-000005.json",711,"e07a7464fefcd78cdde646cf7e8e10051034bc2ca5d1e7ff6acba721197497d6"),
                new ExactRef("D:/ck3-state/ck3-java-resume91_offline04_20261111T071454Z/artifacts/native-launch/injector-argv.json",1132,"feab71a7ef2d3911f450dce98871703874952b5cb2a7fc164af17941ec7dc7d8"),
                new ExactRef("D:/ck3-state/ck3-java-resume91_offline04_20261111T071454Z/artifacts/native-launch/injector.stdout",84,"b7520e10a832c63915b92cf39616e85a97be802332b9efb56dfd9f56d9d384e2"),
                new ExactRef("D:/ck3-state/ck3-java-resume91_offline04_20261111T071454Z/artifacts/native-launch/native-hello.packet",6065,"8d1edb4f375eeb522327319cfb45036564a46674a50abba77f0fb8331c9ce899"),
                new ExactRef("D:/ck3-state/resume91-runtime/quarkus-dev307-runtime/attempt72/EXACT-IDLE-JAVA-RELEASED72.json",1255,"3dd3a6ae4d874fddf4de989791d88590d8f71ef7fb9dcc461fdb5507b036e938"),
                new ExactRef("D:/ck3-state/resume91-runtime/quarkus-dev307-runtime/attempt75/EXACT-IDLE-JAVA-RELEASED75.json",1255,"1976c7267080d0bc9420e0281708f7d8c320b865852f485ecd47b68771ed6e01"),
                new ExactRef("D:/ck3-state/resume91-runtime/quarkus-dev307-runtime/attempt76/C81-DEADLINE-UNKNOWN-P0/HEAD-CHILDREN-END-AND-EXACT-OS-IDENTITIES01.json",4256,"99a67bda830b117d5b6e6dfd41cee7c045cc2649a62aec10186ce290d768005e"),
                new ExactRef("D:/ck3-state/resume91-runtime/quarkus-dev307-runtime/attempt76/C81-DEADLINE-UNKNOWN-P0/status79-run01/ACTUAL-BEGIN.json",1747,"fbf4ba5fba83a17bfa2afe680ca3e91106200a32b884270f5d09ce10ad97c223"),
                new ExactRef("D:/ck3-state/resume91-runtime/quarkus-dev307-runtime/attempt76/C81-DEADLINE-UNKNOWN-P0/status79-run01/originals/STATUS-DIAGNOSTIC-RESULT.json",2571,"4d513e056414ed7908f1140eea7f019088039db3b08a0c2bc6ba4b2ca5bd233d"));
    }
}
