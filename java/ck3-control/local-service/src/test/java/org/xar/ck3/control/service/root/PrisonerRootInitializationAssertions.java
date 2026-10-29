package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.math.BigInteger;
import java.util.Arrays;
import java.util.List;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.application.effects.RootGuardEvidence;
import org.xar.ck3.control.application.planning.prisoners.*;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.nativebridge.capabilities.family.PrisonerNativeQueries;
import org.xar.ck3.control.wave2.prisoners.releasepreview.PrisonerOptionIntent;
import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.application.planning.prisoners.PrisonerPlanningPorts.Family;

/** Assertion adapter for the sole actual Root fixture. It never creates a proof, imports a domain, queries Game or submits an action. */
public final class PrisonerRootInitializationAssertions implements RootEpisodeChainFixture.Assertions {
    private Optional<ExactRef> actionHead=Optional.empty();
    private PrisonerEpisodeLedger12004.Baseline beforeHead;
    private List<DomainBodies.BodyRef> imported=List.of();
    @Override public void beforeDomainImports(RootEpisodeChainFixture.BeforeImports actual)throws IOException {
        var same=actual.sameWriter();var proof=actual.nextProof();proof.requireCurrent(same,actual.context());
        require(beforeHead==null,"one assertion adapter belongs to one actual Root transition");
        for(var family:Family.values()){
            var reference=proof.oldDomain(slot(family));var body=PrisonerEpisodeLedger12004.decode(family,read(same,reference));
            require(body.epoch().owner().session().equals(proof.beforeSession())
                    &&BigInteger.valueOf(body.epoch().owner().player()).equals(proof.predecessorDriver().session().actorId()),"actual old slot does not belong to original predecessor");
        }
        var head=same.head();beforeHead=new PrisonerEpisodeLedger12004.Baseline(head.state().sequence(),head.digest());
        actionHead=ContinuityActionJournal.recordHead(head.state());
    }
    @Override public void afterDomainImports(RootEpisodeChainFixture.Imported actual)throws IOException {
        require(beforeHead!=null,"actual pre-import callback must run first");
        requireImported(actual.sameWriter(),actual.context(),actual.nextProof(),actual.before().catalog().prisoners(),actual.bodies());
        actual.sameWriter().requireHistoricalState(beforeHead.sequence(),beforeHead.digest());
        require(actionHead.equals(ContinuityActionJournal.recordHead(actual.sameWriter().head().state())),"domain import changed original UNKNOWN/action journal lineage");
        imported=actual.bodies().stream().filter(ref->ref.slot()==DomainBodies.Slot.PRISONER_RELEASE||ref.slot()==DomainBodies.Slot.PRISONER_RANSOM).toList();
    }
    @Override public void afterPublication(RootEpisodeChainFixture.Published actual)throws IOException {
        require(imported.size()==2&&actual.session().ownedBy(actual.imported().before().core())
                &&actual.session().identity().equals(actual.imported().nextProof().afterSession()),"actual publication lost the same-Core initialized current physical owner");
        for(var reference:imported){var read=actual.sameWriter().readDomain(reference.slot());require(read instanceof DomainBodies.Available known&&known.reference().equals(reference),"publication replaced an actual initialized prisoner slot");}
    }
    /** Reusable assertion only; a real restored-FIRST fixture may pass its private common proof without minting a substitute. */
    public static void requireImported(ContinuityStorePort.Session same,RootRuntimeContext context,
            RootApplicationAssembly.EpisodeDomainInitializationProof proof,PrisonersRuntimeInstaller actualPrisoners,
            List<DomainBodies.BodyRef> actualBodies)throws IOException {
        context.writer().requireSession(same);proof.requireCurrent(same,context);var head=same.head();
        var collectionContract=actualPrisoners.collectionContract();require(context.readCatalog().containsIdentity(collectionContract),"assertion requires the identical actual installed collection contract");
        var archive=context.archive().withSession(same);var current=proof.currentDriver().session();
        var currentOwner=new PrisonerEpisodeLedger12004.Owner(proof.afterSession(),current.actorId().longValueExact(),current.episodeRunId(),proof.source());
        var dual=new PrisonerEpisodeLedger12004.InitializationOrigins(PrisonerEpisodeLedger12004.InitializationKind.valueOf(proof.kind().name()),
                proof.baselineMaterial().session(),proof.savedSemantic().frame(),currentOwner,proof.currentSemantic().frame(),
                new PrisonerEpisodeLedger12004.Baseline(proof.initializationHeadSequence(),proof.initializationHeadDigest()));
        require(PrisonerEpisodeLedger12004.origins(PrisonerEpisodeLedger12004.origins(dual)).equals(dual),"actual saved/current origins failed strict codec roundtrip");
        for(var family:Family.values()){
            var matches=actualBodies.stream().filter(ref->ref.slot()==slot(family)).toList();require(matches.size()==1,"actual initializer must return each prisoner slot once");
            var stored=same.readDomain(slot(family));require(stored instanceof DomainBodies.Available known&&known.reference().equals(matches.getFirst()),"actual registered writer body differs from returned slot");
            var actual=(DomainBodies.Available)stored;var value=PrisonerEpisodeLedger12004.decode(family,new RawJson(actual.canonicalBody()));
            require(value.epoch().owner().equals(currentOwner),"current body borrowed the saved/predecessor physical owner");
            var collection=value.epoch().collection().orElseThrow(()->new IOException("actual initialized body has no current collection original"));
            var receipt=archive.loadRead(collection.originalReceipt());NativeRecordedEvidenceVerifier.requireRead(receipt,archive);var normalized=collectionContract.replay(receipt);
            currentOwner.require(receipt.request().before(),receipt.request().source(),receipt.request().sessionId());
            var decoded=PrisonerNativeQueries.decode(receipt,0);
            require(archive.readReferenceOf(receipt).equals(collection.originalReceipt())&&receipt.request().before().equals(collection.observed())
                    &&receipt.request().arguments().equals(PrisonerNativeQueries.arguments(new PrisonerOptionIntent.Unconditional(),java.util.OptionalLong.empty()))
                    &&receipt.request().before().frame().identity().dateRaw().equals(proof.currentSemantic().frame().frame().identity().dateRaw())
                    &&receipt.request().before().frame().identity().nativeRevision().compareTo(proof.currentSemantic().frame().frame().identity().nativeRevision())>=0
                    &&decoded.status()==PrisonerNativeQueries.CollectionStatus.AVAILABLE&&decoded.prisonerIds().equals(collection.prisonerIds())
                    &&StrictJson.integer(StrictJson.parse(normalized.bytes(),1_048_576).get("query_sequence"),BigInteger.ONE,StrictJson.UINT64_MAX).equals(collection.querySequence()),"actual collection producer/typed body values differ");
            for(var guard:List.of(receipt.before(),receipt.after())){
                RootGuardEvidence.requireHistory(guard.binding(),archive,same);var frame=RootGuardEvidence.loadFrame(guard.binding(),archive,context.frameLoader());
                require(frame.identity().equals(collection.observed())&&frame.source().equals(proof.source())&&frame.sessionId().equals(proof.afterSession().sessionId()),"actual collection source/complete Driver guard differs");
            }
            var oldReference=proof.oldDomain(slot(family));var original=read(same,oldReference);var old=PrisonerEpisodeLedger12004.decode(family,original);var material=proof.baselineMaterial();
            var expectedEpoch=new PrisonerEpisodeLedger12004.Epoch(PrisonerEpisodeLedger12004.Kind.NEXT,currentOwner,material.reference(),
                    Optional.of(new PrisonerEpisodeLedger12004.Baseline(material.originalHeadSequence(),material.originalHeadDigest())),
                    Optional.of(new PrisonerEpisodeLedger12004.Predecessor(old.epoch().owner(),oldReference)),Optional.of(collection));
            var expected=PrisonerEpisodeLedger12004.next(family,original,old.epoch().owner(),oldReference,expectedEpoch);
            require(Arrays.equals(expected.bytes(),actual.canonicalBody()),"actual whole converter changed old UNKNOWN/body provenance or current custody");
        }
        proof.requireCurrent(same,context);var after=same.head();require(after.digest().equals(head.digest())&&after.documents().equals(head.documents()),"assertion adapter changed the canonical Head");
    }
    private static RawJson read(ContinuityStorePort.Session same,DomainBodies.BodyRef reference)throws IOException {
        var pin=new WriterContracts.Pin(reference.payload(),reference.identity());same.verifyPin(pin);var raw=same.readPinned(pin,1_048_576);same.verifyPin(pin);return new RawJson(raw);
    }
    private static DomainBodies.Slot slot(Family family){return family==Family.RELEASE?DomainBodies.Slot.PRISONER_RELEASE:DomainBodies.Slot.PRISONER_RANSOM;}
}
