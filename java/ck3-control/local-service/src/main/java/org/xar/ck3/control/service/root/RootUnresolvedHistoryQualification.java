package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.ActionState;
import org.xar.ck3.control.application.action.ContinuityActionJournal;
import org.xar.ck3.control.application.action.ReconciliationPendingBinding;
import org.xar.ck3.control.application.action.ReconciliationPendingBinding.HistoryContext;
import org.xar.ck3.control.application.action.RootReadContractCatalog;
import org.xar.ck3.control.application.driver.DriverReadHistoryPublisher;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts;
import org.xar.ck3.control.application.driver.DriverStateAssembler;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Same-action history custody only. Neither construction nor replay settles UNKNOWN or permits a new native command. */
public final class RootUnresolvedHistoryQualification implements ReconciliationPendingBinding.HistoryQualification {
    private final ContinuityStorePort store;
    private final ActionPorts.OutcomeArchive archive;
    private final DriverStateAssembler driver;
    private final DriverReadHistoryPublisher publisher;
    private final RootReadContractCatalog catalog;

    public RootUnresolvedHistoryQualification(ContinuityStorePort store,ActionPorts.OutcomeArchive archive,
            DriverStateAssembler driver,DriverReadHistoryPublisher publisher,RootReadContractCatalog catalog) {
        this.store=Objects.requireNonNull(store);this.archive=Objects.requireNonNull(archive);
        this.driver=Objects.requireNonNull(driver);this.publisher=Objects.requireNonNull(publisher);
        this.catalog=Objects.requireNonNull(catalog);publisher.requireOwner(driver,archive,catalog);
    }

    /** Installation checks compare the actual owners, rather than equal-looking configuration or source rows. */
    public void requireOwner(ContinuityStorePort store,ActionPorts.OutcomeArchive archive,DriverStateAssembler driver,
            DriverReadHistoryPublisher publisher,RootReadContractCatalog catalog) {
        StrictJson.require(this.store==store&&this.archive==archive&&this.driver==driver
                &&this.publisher==publisher&&this.catalog==catalog,"unresolved history qualification crossed its actual owners");
        publisher.requireOwner(driver,archive,catalog);
    }

    /** Captures routing custody from the actual frozen owner, never an epoch supplied by a caller. */
    public EpochOwner captureEpoch(ContinuityStorePort.Session same)throws IOException {
        store.requireSession(same);publisher.requireOwner(driver,archive,catalog);
        String head=same.head().digest();String machine=same.head().state().machineId();
        return driver.withFrozenFacts(same,frozen->{
            StrictJson.require(frozen.state() instanceof DriverSnapshotFacts.Known,"actual Driver epoch is unavailable");
            var current=(DriverSnapshotFacts.Known)frozen.state();
            StrictJson.require(same.head().digest().equals(head),"Driver epoch capture changed the original writer Head");
            return new EpochOwner(same,machine,current.stamp(),head);
        });
    }

    /** A finite archive route only. This value grants no UNKNOWN settlement, query, submit or historical proof. */
    public final class EpochOwner {
        private final ContinuityStorePort.Session session;private final String machineId;
        private final DriverSnapshotFacts.Stamp stamp;private final String head;
        private EpochOwner(ContinuityStorePort.Session session,String machineId,DriverSnapshotFacts.Stamp stamp,String head) {
            this.session=session;this.machineId=machineId;this.stamp=stamp;this.head=head;
        }
        public RootUnresolvedHistoryQualification qualification(){return RootUnresolvedHistoryQualification.this;}
        public String machineId(){return machineId;}
        public DriverSnapshotFacts.Stamp stamp(){return stamp;}
        public void requireOwner(ContinuityStorePort store,ActionPorts.OutcomeArchive archive)throws IOException {
            StrictJson.require(RootUnresolvedHistoryQualification.this.store==store
                    &&RootUnresolvedHistoryQualification.this.archive==archive,"archive epoch belongs to another actual store or archive");
            publisher.requireOwner(driver,archive,catalog);
        }
        /** Installation must consume this original borrowed Session before it changes or closes. */
        public void requireCurrentEpoch(ContinuityStorePort.Session same)throws IOException {
            StrictJson.require(same==session,"archive epoch installation escaped its original borrowed Session");
            store.requireSession(same);publisher.requireOwner(driver,archive,catalog);
            StrictJson.require(same.head().digest().equals(head),"archive epoch installation changed the original writer Head");
            driver.withFrozenFacts(same,frozen->{
                StrictJson.require(frozen.state() instanceof DriverSnapshotFacts.Known,"actual Driver epoch is unavailable");
                var current=((DriverSnapshotFacts.Known)frozen.state()).stamp();
                StrictJson.require(current.game().equals(stamp.game())&&current.episodeEpoch()==stamp.episodeEpoch()
                        &&current.episodeRunId().equals(stamp.episodeRunId()),"archive epoch changed its actual Game, run or generation");
                return null;
            });
            StrictJson.require(same.head().digest().equals(head),"archive epoch guard changed the original writer Head");
        }
    }

    @Override public void require(HistoryContext actual)throws IOException {
        Qualified qualified=qualify(Objects.requireNonNull(actual));
        qualified.requireRetained();
    }

    private Qualified qualify(HistoryContext actual)throws IOException {
        ActionPorts.OutcomeArchive bound=archive.withSession(actual.session());
        requireContext(actual,bound);
        Lineage lineage=switch(actual.mode()) {
            case LIVE_PENDING -> driver.withFrozenFacts(actual.session(),frozen->{
                StrictJson.require(frozen.state() instanceof DriverSnapshotFacts.Known,
                        "actual current Driver owner is unavailable for unresolved history");
                var current=(DriverSnapshotFacts.Known)frozen.state();
                var proof=publisher.requireUnresolvedHistoryExtension(actual.session(),actual.original(),
                        actual.beforeDriver().reference(),current);
                return new Live(proof);
            });
            case HISTORICAL_READ -> new Historical(publisher.requireHistoricalUnresolvedHistoryExtension(
                    actual.session(),actual.original(),actual.beforeDriver().reference(),
                    actual.currentDriver().reference(),actual.targetHead()));
        };
        requireEndpoints(actual,lineage);
        var retained=new LinkedHashSet<ExactRef>(lineage.events());
        retained.add(actual.receiptReference());retained.add(actual.recordReference());
        var pins=new ArrayList<WriterContracts.Pin>();
        for(ExactRef ref:retained) {
            var pin=actual.session().capturePin(ref,WriterContracts.MAX_PIN_BYTES);
            actual.session().verifyPin(pin);pins.add(pin);
        }
        lineage.require(actual.session());requireContext(actual,bound);
        return new Qualified(actual,bound,lineage,List.copyOf(pins));
    }

    private void requireContext(HistoryContext actual,ActionPorts.OutcomeArchive bound)throws IOException {
        store.requireSession(actual.session());publisher.requireOwner(driver,archive,catalog);
        var head=actual.session().head();
        StrictJson.require(head.digest().equals(actual.head().digest())
                &&head.state().sequence()==actual.head().state().sequence(),
                "unresolved history escaped the actual borrowed writer Head");
        StrictJson.require(actual.original().state() instanceof ActionState.Unknown,
                "history extension requires the original canonical UNKNOWN primitive");
        var unknown=(ActionState.Unknown)actual.original().state();
        StrictJson.require(unknown.attempt().filter(actual.attempt()::equals).isPresent(),
                "unresolved history changed its original prepared attempt");
        StrictJson.require(actual.identity().pending().originalReceipt().equals(actual.receiptReference())
                &&actual.identity().pending().originalBeforeDriver().equals(actual.beforeDriver().reference())
                &&actual.identity().evidence().currentOriginalDriver().equals(actual.currentDriver().reference()),
                "history qualification crossed its actual reconciliation original roles");
        StrictJson.require(!Arrays.equals(actual.beforeDriver().bytes(),actual.currentDriver().bytes()),
                "unchanged complete Driver uses the original strict reconciliation branch");
        StrictJson.require(bound.loadReceipt(actual.receiptReference()).equals(actual.original())
                &&bound.loadRecord(actual.recordReference()).receipt().equals(actual.original())
                &&ContinuityActionJournal.requireHistoricalReceipt(actual.targetHead().state(),actual.original(),bound)
                        .equals(actual.recordReference()),
                "unresolved history lost its exact original canonical receipt or record");
        StrictJson.require(Arrays.equals(bound.loadFullMaterial(actual.beforeDriver().reference()).bytes(),actual.beforeDriver().bytes())
                &&Arrays.equals(bound.loadFullMaterial(actual.currentDriver().reference()).bytes(),actual.currentDriver().bytes()),
                "unresolved history complete Driver originals differ from their retained material");
        var point=actual.identity().historyPoint().orElseThrow(()->new IllegalArgumentException(
                "history append requires its explicitly retained original writer point"));
        StrictJson.require(point.sequence()==actual.targetHead().state().sequence()
                &&point.digest().equals(actual.targetHead().digest()),"history target Head differs from its original identity point");
        StrictJson.require(actual.session().requireHistoricalState(point.sequence(),point.digest()).toJson()
                .equals(actual.targetHead().state().toJson()),"history target is not the actual retained canonical ancestor");
        if(actual.mode()==ReconciliationPendingBinding.Mode.LIVE_PENDING)
            StrictJson.require(actual.targetHead().digest().equals(head.digest()),
                    "live unresolved history cannot borrow a historical target Head");
    }

    private static void requireEndpoints(HistoryContext actual,Lineage lineage) {
        StrictJson.require(lineage.action().equals(actual.original())
                &&lineage.before().equals(actual.beforeDriver().reference())
                &&lineage.current().equals(actual.currentDriver().reference())
                &&!lineage.events().isEmpty(),"private unresolved lineage changed action, endpoints or canonical interval");
    }

    private sealed interface Lineage permits Live,Historical {
        ActionReceipt action();ExactRef before();ExactRef current();List<ExactRef> events();
        void require(ContinuityStorePort.Session same)throws IOException;
    }
    private record Live(DriverReadHistoryPublisher.UnresolvedHistoryExtension proof) implements Lineage {
        private Live {Objects.requireNonNull(proof);}
        public ActionReceipt action(){return proof.originalAction();}
        public ExactRef before(){return proof.originalDriver();}
        public ExactRef current(){return proof.currentDriver();}
        public List<ExactRef> events(){return proof.eventReferences();}
        public void require(ContinuityStorePort.Session same)throws IOException{proof.requireCurrent(same);}
    }
    private record Historical(DriverReadHistoryPublisher.HistoricalUnresolvedHistoryExtension proof) implements Lineage {
        private Historical {Objects.requireNonNull(proof);}
        public ActionReceipt action(){return proof.originalAction();}
        public ExactRef before(){return proof.originalDriver();}
        public ExactRef current(){return proof.currentDriver();}
        public List<ExactRef> events(){return proof.eventReferences();}
        public void require(ContinuityStorePort.Session same)throws IOException{proof.requireHistorical(same);}
    }

    /** No public constructor, serializer, decoder or detached DTO can mint this qualification. */
    private final class Qualified {
        private final HistoryContext context;private final ActionPorts.OutcomeArchive bound;
        private final Lineage lineage;private final List<WriterContracts.Pin> originals;
        private Qualified(HistoryContext context,ActionPorts.OutcomeArchive bound,Lineage lineage,List<WriterContracts.Pin> originals) {
            this.context=context;this.bound=bound;this.lineage=lineage;this.originals=originals;
        }
        private void requireRetained()throws IOException {
            requireContext(context,bound);requireEndpoints(context,lineage);
            lineage.require(context.session());
            for(var pin:originals)context.session().verifyPin(pin);
            requireContext(context,bound);
        }
    }
}
