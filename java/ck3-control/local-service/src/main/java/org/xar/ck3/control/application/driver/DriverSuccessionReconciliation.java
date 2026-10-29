package org.xar.ck3.control.application.driver;

import java.io.IOException;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.service.root.RootLifecycleAuthority;
import org.xar.ck3.control.service.root.RootNaturalSuccessionOriginals;
import org.xar.ck3.control.wave2.governance.succession.SuccessionNativeEstate12004;

/** Actual Root custody mints only estate comparison data. M3's separate natural-source proof still grants succession. */
public final class DriverSuccessionReconciliation {
    private DriverSuccessionReconciliation() { }
    public static void publish(ContinuityStorePort.Session same,DriverStateAssembler authority,ActionPorts.OutcomeArchive archive,
            RootLifecycleAuthority terminal,RootNaturalSuccessionOriginals originals,ActionCommand parent) throws IOException {
        StrictJson.require(parent.operation().value().equals("continue-as-reconciled-successor")
                &&parent.origin() instanceof CommandOrigin.LifecycleTerminal,"actual successor parent required");
        ActionPorts.OutcomeArchive bound=archive.withSession(same);
        var actual=terminal.current(same,parent.lifecycleBefore(),parent.deadline(),lease->prepare(same,authority,bound,originals,lease,parent.deadline()));
        terminal.requireOutsideObservationScope(same);
        authority.publishCapabilityInputs(same,actual.publication().expectedStamp(),actual.publication().expectedAuxiliarySha256(),actual.publication());
    }
    /** Captured only from the actual live terminal lease. Getters expose DATA, never a Native permit. */
    public static final class Prepared {
        private final Known before; private final DriverCapabilityStateProducer.InitialAuxiliary publication;
        private final LifecycleIdentity identity; private final org.xar.ck3.control.application.readiness.NativeReadinessCollector.SourceQualification source;
        private final java.time.Instant until; private final String head;
        private Prepared(Known before,DriverCapabilityStateProducer.InitialAuxiliary publication,LifecycleIdentity identity,org.xar.ck3.control.application.readiness.NativeReadinessCollector.SourceQualification source,java.time.Instant until,String head){this.before=before;this.publication=publication;this.identity=identity;this.source=source;this.until=until;this.head=head;}
        public Known before(){return before;} public DriverCapabilityStateProducer.InitialAuxiliary publication(){return publication;}
        public LifecycleIdentity identity(){return identity;} public org.xar.ck3.control.application.readiness.NativeReadinessCollector.SourceQualification source(){return source;}
        public java.time.Instant validUntil(){return until;} public String writerHeadDigest(){return head;}
    }
    /** Public planning supplies the real CHANGED lease; no synthetic Continue parent is created. */
    public static Prepared prepare(ContinuityStorePort.Session same,DriverStateAssembler authority,ActionPorts.OutcomeArchive archive,
            RootNaturalSuccessionOriginals originals,RootLifecycleAuthority.Lease lease,java.time.Instant deadline)throws IOException {
        lease.assertCurrent(same);ActionPorts.OutcomeArchive bound=archive.withSession(same);
        Known before=authority.withFrozenFacts(same,current->{StrictJson.require(current.state() instanceof Known,"actual terminal full Known missing");return (Known)current.state();});
            lease.assertCurrent(same);
            var identity=lease.identity();
            StrictJson.require(identity.terminalReason()==LifecycleIdentity.TerminalReason.CHANGED
                    &&identity.currentPlayer() instanceof LifecycleIdentity.Character successor&&successor.alive(),"actual living changed player required");
            var capture=originals.capturedPredecessor(lease);
            ExactRef captureSource=originals.capturedPredecessorSource(lease);
            var root=originals.readCurrentCampaignRoot(lease,deadline);
            StrictJson.require(bound.loadRead(root.originalReceipt()).equals(root.receipt())
                    &&root.receipt().request().origin() instanceof CommandOrigin.LifecycleTerminal query
                    &&identity.sameGuardFrame(query.identity())&&root.receipt().request().source().equals(lease.snapshot().source())
                    &&root.receipt().request().sessionId().equals(identity.sessionId()),"final estate read crossed actual terminal custody");
            RawJson rootResult=root.receipt().original().originalResultToken().orElseThrow();
            StrictJson.require(rootResult.equals(root.value()),"final estate typed read differs from its actual original token");
            ExactRef finalRoot=bound.preserveMaterial(rootResult);
            RawJson finalSemantic=bound.loadMaterial(lease.originalSemantic());
            StrictJson.require(Arrays.equals(finalSemantic.bytes(),DriverJson.encode(lease.snapshot().semantic())),"actual final semantic original differs");
            var firstRead=bound.loadRead(capture.rootRead());
            StrictJson.require(firstRead.request().origin() instanceof CommandOrigin.Gameplay originalGameplay
                    &&originalGameplay.before().game().equals(identity.game())&&originalGameplay.before().frame().episodeRunId().equals(identity.subject().episodeRunId())
                    &&originalGameplay.before().frame().identity().player().equals(identity.subject().characterId())
                    &&firstRead.request().source().equals(lease.snapshot().source())&&firstRead.request().sessionId().equals(identity.sessionId())
                    &&firstRead.original().originalResultToken().orElseThrow().equals(bound.loadMaterial(capture.rootResult())),"original preclock estate read differs from actual old subject/source");
            byte[] beforeRoot=bound.loadMaterial(capture.rootResult()).bytes(),beforeSemantic=bound.loadMaterial(capture.semantic()).bytes();
            var frozen=SuccessionNativeEstate12004.freeze(beforeRoot,beforeSemantic);
            var compared=SuccessionNativeEstate12004.reconcile(frozen,rootResult.bytes(),finalSemantic.bytes());
            OpportunityJson.Obj wire=DriverJson.object(compared.wire(),DriverJson.MAX_NATIVE_BYTES);
            var publication=authority.withFrozenFacts(same,current -> {
                StrictJson.require(current.state() instanceof Known,"actual full old Driver unavailable for estate publication");
                Known known=(Known)current.state();
                StrictJson.require(known==before,"terminal preflight changed its exact full Known owner");
                StrictJson.require(DriverJson.object(frozen.wire(),DriverJson.MAX_NATIVE_BYTES).equals(lease.snapshot().semantic().get("succession_expectation")),"retained Driver expectation differs from its actual canonical preclock estate");
                StrictJson.require(known.stamp().game().equals(identity.game())&&known.stamp().episodeRunId().equals(identity.subject().episodeRunId())
                        &&known.stamp().episodeEpoch()==identity.subject().episodeEpoch()&&known.stamp().driverVersion()==identity.subject().driverVersion()
                        &&known.driver().session().actorId().equals(identity.subject().characterId())
                        &&known.observation().isPresent()&&known.observation().orElseThrow().semanticFactsEvidence().equals(identity.evidence().observationManifest())
                        &&Arrays.equals(known.driver().encode(),bound.loadMaterial(identity.evidence().originalDriver()).bytes()),"estate publication crossed actual frozen old Driver");
                var proof=new LinkedHashMap<String,OpportunityJson.Value>();
                proof.put("schema",new OpportunityJson.Text("xar.driver-succession-estate-source/v1"));
                put(proof,"preclock_capture",captureSource);put(proof,"preclock_root_read",capture.rootRead());put(proof,"preclock_root_result",capture.rootResult());
                put(proof,"preclock_semantic",capture.semantic());put(proof,"preclock_driver",capture.driver());put(proof,"preclock_native",capture.nativePacket());putOptional(proof,"preclock_source",capture.sourceQualification());
                put(proof,"final_root_read",root.originalReceipt());put(proof,"final_root_result",finalRoot);put(proof,"final_semantic",lease.originalSemantic());
                put(proof,"final_driver",identity.evidence().originalDriver());put(proof,"final_native",identity.nativeEvidence());putOptional(proof,"final_source",lease.sourceQualification().proof());
                proof.put("reconciliation",wire);
                RawJson material=new RawJson(DriverJson.encode(new OpportunityJson.Obj(proof)));ExactRef retained=bound.preserveMaterial(material);
                StrictJson.require(bound.loadMaterial(retained).equals(material),"estate original proof archive differs");
                var auxiliary=new LinkedHashMap<>(known.auxiliary().members());auxiliary.put("succession_reconciliation",wire);
                auxiliary.put("capability_succession_source",DriverObservationEvidenceReader.reference(retained));
                var changed=new DriverCapabilityStateProducer.InitialAuxiliary(known,new OpportunityJson.Obj(auxiliary),retained);
                DriverCapabilityStateProducer.replaySuccessionSource(changed.auxiliary(),bound);
                return changed;
            });
            lease.assertCurrent(same);return new Prepared(before,publication,lease.identity(),lease.sourceQualification(),lease.validUntil(),same.head().digest());

    }
    private static void put(LinkedHashMap<String,OpportunityJson.Value> row,String field,ExactRef original) {
        row.put(field,DriverObservationEvidenceReader.reference(original));
    }
    private static void putOptional(LinkedHashMap<String,OpportunityJson.Value> row,String field,Optional<ExactRef> original) {
        row.put(field,original.<OpportunityJson.Value>map(DriverObservationEvidenceReader::reference).orElse(OpportunityJson.Nil.INSTANCE));
    }
}
