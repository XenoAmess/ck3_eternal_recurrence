package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.planning.family.*;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.continuity.writer.DomainBodies.Slot;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Three original full ledgers enter the original writer; missing files never become empty ledgers. */
public final class RootFamilyOriginalDomains {
    private static final String SCHEMA="xar.java.family-original-domain-import/v1";
    private static final String FRESH_SCHEMA="xar.java.family-fresh-campaign-initialization/v1";
    private static final String NEXT_SCHEMA="xar.java.family-episode-domain-initialization/v2";
    private static final String NATURAL_SCHEMA="xar.java.family-natural-domain-initialization/v1";
    private static final int MAX=ContinuityJson.DOMAIN_MAX_BYTES;
    private static final List<Slot> SLOTS=List.of(Slot.FAMILY,Slot.CHILD_MATRILINEAL,Slot.DEFAULT_MARRIAGE);
    private final Path lock;
    private final Map<Slot,ExactRef> selectedOriginals;
    private final List<DomainBodies.Registration> registrations;
    private final RootFamilyOrdinaryRestoreDomains ordinaryRestores;
    private record Storage(ContinuityWriter writer,NativeOutcomeArchive archive) { }
    private Storage storage;
    private RootRuntimeContext current;
    private FamilyOrdinaryFactory.CompleteBinding family;
    /** Private live custody, never reconstructed from a decoded DATA manifest. */
    private record NextAuthorization(RootRuntimeContext context,RootApplicationAssembly.EpisodeDomainInitializationProof proof,
            Slot slot,DomainBodies.BodyRef previous,DomainBodies.BodyRef oldDomain,String inputSha256,String bodySha256) { }
    private final Map<String,NextAuthorization> nextAuthorizations=new java.util.HashMap<>();
    private static final class NaturalSlot {
        final DomainBodies.BodyRef original;
        final byte[] originalBytes;
        final FamilyNaturalEpisodeMigration.Transition transition;
        final byte[] output;
        DomainBodies.PreparedImport prepared;
        WriterContracts.Receipt receipt;
        boolean attempted;
        NaturalSlot(DomainBodies.BodyRef original,byte[] originalBytes,FamilyNaturalEpisodeMigration.Transition transition,byte[] output) {
            this.original=original;this.originalBytes=originalBytes.clone();this.transition=transition;this.output=output.clone();
        }
    }
    private record NaturalBatch(RootRuntimeContext context,org.xar.ck3.control.application.lifecycle.LifecycleComposites.CommittedNatural proof,
            Map<Slot,NaturalSlot> slots) { }
    private record NaturalAuthorization(NaturalBatch batch,Slot slot,DomainBodies.BodyRef previous,String inputSha256,String outputSha256) { }
    private final Map<org.xar.ck3.control.application.lifecycle.LifecycleComposites.CommittedNatural,NaturalBatch> naturalBatches=new java.util.IdentityHashMap<>();
    private final Map<String,NaturalAuthorization> naturalAuthorizations=new java.util.HashMap<>();
    public RootFamilyOriginalDomains(Path originalWriterLock,Map<Slot,ExactRef> selectedOriginals,List<ExactRef> completeProducerClosure) {
        this(originalWriterLock,selectedOriginals,completeProducerClosure,false);
    }
    /** Pre-Core fresh definitions. This creates no domain body and makes no claim about an old file. */
    public RootFamilyOriginalDomains(Path originalWriterLock,List<ExactRef> completeProducerClosure) {
        this(originalWriterLock,Map.of(),completeProducerClosure,true);
    }
    private RootFamilyOriginalDomains(Path originalWriterLock,Map<Slot,ExactRef> selectedOriginals,
            List<ExactRef> completeProducerClosure,boolean fresh) {
        lock=Objects.requireNonNull(originalWriterLock).toAbsolutePath().normalize();this.selectedOriginals=Map.copyOf(selectedOriginals);
        ordinaryRestores=new RootFamilyOrdinaryRestoreDomains(lock);
        StrictJson.require(fresh?this.selectedOriginals.isEmpty():this.selectedOriginals.keySet().equals(Set.copyOf(SLOTS)),
                "historical Family requires its three original documents; fresh definitions select no old documents");
        var sources=List.copyOf(completeProducerClosure);StrictJson.require(!sources.isEmpty() && sources.size()<=64
                && sources.stream().allMatch(ref->ref.bytes()>0) && new java.util.HashSet<>(sources).size()==sources.size(),"complete unique actual family producer closure required");
        var prepared=new java.util.ArrayList<DomainBodies.Registration>();
        for(Slot slot:SLOTS)prepared.add(new DomainBodies.Registration(slot,FamilyDomainSource.schema(slot),MAX,sources,(head,previous,request,actual)->{
            var input=StrictJson.parse(request.producerInput(),MAX);
            if(SCHEMA.equals(input.path("schema").asText()))return verifyOriginal(slot,head,previous,request,actual);
            if(FRESH_SCHEMA.equals(input.path("schema").asText()))return verifyFresh(slot,head,previous,request,actual);
            if(NEXT_SCHEMA.equals(input.path("schema").asText()))return verifyNext(slot,head,previous,request,actual);
            if(NATURAL_SCHEMA.equals(input.path("schema").asText()))return verifyNatural(slot,head,previous,request,actual);
            if(RootFamilyOrdinaryRestoreDomains.SCHEMA.equals(input.path("schema").asText()))return ordinaryRestores.verify(slot,head,previous,request,actual);
            var actualFamily=active();return actualFamily.registration(slot,sources).verifier().verify(head,previous,request,actual);
        }));
        registrations=List.copyOf(prepared);
    }
    public List<DomainBodies.Registration> registrations() {return registrations;}
    public synchronized void bindCore(RootApplicationAssembly.Core actual) {
        Objects.requireNonNull(actual);StrictJson.require(actual.configuration().ledger().lock().toAbsolutePath().normalize().equals(lock),"family documents bind only the original Core/writer");
        bindWriter(actual.writer(),actual.archive());
    }
    public synchronized void bindWriter(ContinuityWriter actualWriter,NativeOutcomeArchive actualArchive) {
        StrictJson.require(storage==null && actualArchive.writer()==actualWriter && actualWriter.originalLockPath().equals(lock),"family documents bind once to the identical original writer/archive");
        storage=new Storage(actualWriter,actualArchive);ordinaryRestores.bindWriter(actualWriter,actualArchive);
    }
    public synchronized void bindGame(RootRuntimeContext actual,FamilyOrdinaryFactory.CompleteBinding binding) {
        StrictJson.require(storage!=null && actual.writer()==storage.writer() && actual.archive()==storage.archive() && current!=actual,"family document products bind once per actual physical Game");
        current=Objects.requireNonNull(actual);family=Objects.requireNonNull(binding);ordinaryRestores.bindGame(actual);
    }
    private synchronized Storage core()throws IOException {if(storage==null)throw new IOException("family original writer not bound");return storage;}
    private synchronized FamilyOrdinaryFactory.CompleteBinding active()throws IOException {if(current==null||family==null)throw new IOException("actual family result/pending producers not installed");return family;}
    /** The Root calls this inside its existing writer transaction after bindCore, before enabling any family policy. */
    public ExactRef importOriginal(ContinuityStorePort.Session same,Slot slot)throws IOException {
        var owner=core();owner.writer().requireSession(same);same.requireWriter(lock);
        StrictJson.require(SLOTS.contains(slot),"actual family slot required");ExactRef selected=selectedOriginals.get(slot);
        if(selected==null)throw new IOException("fresh Family definitions have no selected historical document; initialize from the actual observed campaign");
        var existing=same.readDomain(slot);if(existing instanceof DomainBodies.Available known)return known.reference().payload();
        var pin=same.capturePin(selected,MAX);byte[] original=same.readPinned(pin,MAX);FamilyDomainSource.validate(slot,original);
        ExactRef archived=owner.archive().preserveArtifact(same,original,MAX);
        var input=StrictJson.object().put("schema",SCHEMA).put("slot",slot.name());input.set("selected_original",selected.toJson());
        var request=new DomainBodies.ImportRequest(slot,FamilyDomainSource.schema(slot),archived,StrictJson.canonical(input,MAX),
                List.of(selected,archived),"family-original-"+slot.name()+"-"+selected.sha256());
        same.verifyPin(pin);var prepared=same.previewImport(request);same.verifyPin(pin);same.commitImport(prepared);same.verifyPin(pin);return archived;
    }
    /** Deliberate new automation history for the actual observed fresh campaign; storage absence alone is insufficient. */
    public List<DomainBodies.BodyRef> initializeFresh(RootRuntimeContext actual,ContinuityStorePort.Session same,
            FreshCampaignContext proof)throws IOException {
        var owner=core();owner.writer().requireSession(same);same.requireWriter(lock);proof.requireCurrent(same);
        StrictJson.require(current==actual&&proof.context()==actual,"fresh Family requires its installed physical context");
        proof.requireInitializationPredecessor(same,same.head());ExactRef basis=proof.preserveOriginal(same);
        var evidence=new java.util.LinkedHashSet<ExactRef>();evidence.add(basis);evidence.addAll(proof.evidence());
        var result=new java.util.ArrayList<DomainBodies.BodyRef>();
        for(var initial:FamilyInitialData.fresh().bodies()) {
            Slot slot=initial.slot();var existing=same.readDomain(slot);
            if(existing instanceof DomainBodies.Available known){result.add(known.reference());continue;}
            if(!(existing instanceof DomainBodies.Unavailable missing)||missing.reason()!=DomainBodies.Reason.UNIMPORTED)
                throw new IOException("fresh Family cannot replace an unavailable existing body: "+slot);
            byte[] output=FamilyInitialData.encode(initial);var archived=owner.archive().preserveArtifact(same,output,MAX);
            var input=StrictJson.object().put("schema",FRESH_SCHEMA).put("slot",slot.name());input.set("fresh_campaign",basis.toJson());
            var request=new DomainBodies.ImportRequest(slot,FamilyDomainSource.schema(slot),archived,StrictJson.canonical(input,MAX),
                    List.copyOf(evidence),"family-fresh-"+slot.name()+"-"+basis.sha256());
            proof.requireInitializationPredecessor(same,same.head());same.commitImport(same.previewImport(request));
            result.add(DomainBodies.reference(same.head().state(),slot).orElseThrow());
        }
        proof.requireCurrent(same);return List.copyOf(result);
    }
    private String verifyFresh(Slot slot,org.xar.ck3.control.continuity.ContinuityState head,
            Optional<DomainBodies.BodyRef> previous,DomainBodies.ImportRequest request,byte[] actual)throws IOException {
        var owner=core();var same=owner.writer().borrowedSession();owner.writer().requireSession(same);
        var input=StrictJson.object(StrictJson.parse(request.producerInput(),MAX),Set.of("schema","slot","fresh_campaign"));
        StrictJson.require(previous.isEmpty()&&FRESH_SCHEMA.equals(StrictJson.text(input.get("schema")))
                &&slot.name().equals(StrictJson.text(input.get("slot"))),"fresh Family import cannot erase or cross a domain");
        if(current==null)throw new IOException("fresh Family context is not installed");
        var basis=ExactRef.fromJson(input.get("fresh_campaign"));var original=FreshCampaignContext.replayOriginal(current,same,basis);
        var evidence=new java.util.LinkedHashSet<ExactRef>();evidence.add(basis);evidence.addAll(original.evidence());
        byte[] expected=FamilyInitialData.encode(FamilyInitialData.fresh().body(slot));
        StrictJson.require(head.machineId().equals(original.observation().machineId())&&request.evidence().equals(List.copyOf(evidence))
                &&Arrays.equals(actual,expected),"fresh Family differs from its observed campaign and initial-value algorithm");
        return ActionCodec.sha256(request.producerInput());
    }
    /** Same-episode ordinary restoration keeps complete active records and only rebinds the actual physical owner. */
    public List<DomainBodies.BodyRef> initializeOrdinaryRestored(RootRuntimeContext actual,ContinuityStorePort.Session same,
            RootRestorationOriginalProof proof)throws IOException {
        return ordinaryRestores.initialize(actual,same,Objects.requireNonNull(proof));
    }
    /** One actual transform for NEXT and FIRST restore; original BASELINE and current physical facts stay distinct. */
    public List<DomainBodies.BodyRef> initializeNext(RootRuntimeContext actual,ContinuityStorePort.Session same,
            RootApplicationAssembly.EpisodeDomainInitializationProof proof)throws IOException {
        var owner=core();owner.writer().requireSession(same);same.requireWriter(lock);Objects.requireNonNull(proof);
        synchronized(this){StrictJson.require(current==actual,"NEXT family initializer must use the installed actual physical context");}
        proof.requireCurrent(same,actual);
        var before=proof.predecessorDriver();var saved=proof.firstSavedDriver();var savedSemantic=proof.savedSemantic();
        var currentDriver=proof.currentDriver();var semantic=proof.currentSemantic();
        StrictJson.require(proof.afterSession().machineId().equals(proof.source().machineId())&&semantic.frame().machineId().equals(proof.afterSession().machineId())
                &&semantic.frame().game().equals(proof.afterSession().game())&&semantic.frame().frame().identity().player().equals(currentDriver.session().actorId())
                &&semantic.frame().frame().episodeRunId().equals(currentDriver.session().episodeRunId())
                &&currentDriver.session().actorId().equals(saved.session().actorId())&&currentDriver.session().episodeRunId().equals(saved.session().episodeRunId())
                &&savedSemantic.frame().game().equals(proof.baselineMaterial().session().game())
                &&savedSemantic.frame().frame().identity().player().equals(saved.session().actorId())&&savedSemantic.frame().frame().episodeRunId().equals(saved.session().episodeRunId()),
                "family initialization crossed original saved identity or the actual current physical Driver/SEM");
        var predecessor=owner.archive().preserveArtifact(same,before.encode(),org.xar.ck3.control.application.checkpoint.DriverCheckpointStore.MAX_DRIVER_BYTES);
        var firstSaved=owner.archive().preserveArtifact(same,saved.encode(),org.xar.ck3.control.application.checkpoint.DriverCheckpointStore.MAX_DRIVER_BYTES);
        var currentDriverRef=owner.archive().preserveArtifact(same,currentDriver.encode(),org.xar.ck3.control.application.checkpoint.DriverCheckpointStore.MAX_DRIVER_BYTES);
        var bodies=new EnumMap<Slot,DomainBodies.Available>(Slot.class);var outputs=new EnumMap<Slot,byte[]>(Slot.class);
        var transitions=new EnumMap<Slot,FamilyNextEpisodeMigration.Transition>(Slot.class);
        var originalDomains=new EnumMap<Slot,DomainBodies.BodyRef>(Slot.class);
        for(Slot slot:SLOTS) {
            var read=same.readDomain(slot);if(!(read instanceof DomainBodies.Available known))throw new IOException("NEXT family requires actual full prior domain: "+slot+" "+read);
            var original=proof.oldDomain(slot);StrictJson.require(original.slot()==slot&&original.contractSchema().equals(FamilyDomainSource.schema(slot)),"private FIRST proof returned another original family domain");
            var pin=same.capturePin(original.payload(),MAX);StrictJson.require(pin.identity().equals(original.identity()),"original BASELINE family native identity changed");
            byte[] originalBytes=same.readPinned(pin,MAX);
            var transition=new FamilyNextEpisodeMigration.Transition(proof.beforeSession(),proof.afterSession(),FamilyNextEpisodeMigration.Episode.fromDriver(before),
                    FamilyNextEpisodeMigration.Episode.fromDriver(saved),proof.baselineMaterial().reference(),original.payload());
            FamilyNextEpisodeMigration.requireCompatibleCurrent(slot,originalBytes,known.canonicalBody(),transition);
            byte[] output=FamilyNextEpisodeMigration.derive(slot,originalBytes,transition);same.verifyPin(pin);
            bodies.put(slot,known);transitions.put(slot,transition);originalDomains.put(slot,original);
            if(!Arrays.equals(output,known.canonicalBody()))outputs.put(slot,output);
        }
        proof.requireCurrent(same,actual);var result=new java.util.ArrayList<DomainBodies.BodyRef>();
        for(Slot slot:SLOTS) {
            if(!outputs.containsKey(slot)){result.add(bodies.get(slot).reference());continue;}
            proof.requireCurrent(same,actual);var previous=bodies.get(slot).reference();byte[] output=outputs.get(slot);
            var archived=owner.archive().preserveArtifact(same,output,MAX);
            var oldDomain=originalDomains.get(slot);
            var input=StrictJson.object().put("schema",NEXT_SCHEMA).put("slot",slot.name()).put("kind",proof.kind().name());input.set("transition",transitions.get(slot).toJson());input.set("previous",previous.toJson());input.set("old_domain",oldDomain.toJson());
            input.set("predecessor_driver",predecessor.toJson());input.set("first_saved_driver",firstSaved.toJson());
            input.set("current_driver",currentDriverRef.toJson());input.set("saved_semantic",org.xar.ck3.control.application.session.OrdinaryCycleTransitions.semanticToJson(savedSemantic));
            input.set("current_semantic",org.xar.ck3.control.application.session.OrdinaryCycleTransitions.semanticToJson(semantic));input.set("baseline",proof.baselineMaterial().baseline().toJson());
            input.put("initialization_head_sequence",proof.initializationHeadSequence()).put("initialization_head_digest",proof.initializationHeadDigest());
            byte[] inputBytes=StrictJson.canonical(input,MAX);
            String physical=ActionCodec.sha256(StrictJson.canonical(org.xar.ck3.control.application.session.OrdinaryCycleTransitions.sessionToJson(proof.afterSession())));
            String identity="family-initialize-"+slot.name()+"-"+proof.kind().name()+"-"+physical+"-"+proof.initializationHeadDigest()+"-"+previous.payload().sha256();
            var evidence=new java.util.LinkedHashSet<ExactRef>(List.of(previous.payload(),oldDomain.payload(),archived,predecessor,firstSaved,currentDriverRef,proof.baselineMaterial().reference(),proof.baselineMaterial().baseline().eventRef()));
            evidence.addAll(savedSemantic.references());evidence.addAll(semantic.references());evidence.addAll(proof.lifecycleProof().originalEvidence());
            var request=new DomainBodies.ImportRequest(slot,FamilyDomainSource.schema(slot),archived,inputBytes,List.copyOf(evidence),identity);
            synchronized(this) {
                StrictJson.require(nextAuthorizations.size()<192||nextAuthorizations.containsKey(identity),"bounded private NEXT family proof history exhausted");
                var authorization=new NextAuthorization(actual,proof,slot,previous,oldDomain,ActionCodec.sha256(inputBytes),ActionCodec.sha256(output));
                var existing=nextAuthorizations.putIfAbsent(identity,authorization);StrictJson.require(existing==null||existing.equals(authorization),"same NEXT import identity changed its private original proof");
            }
            proof.requireCurrent(same,actual);var prepared=same.previewImport(request);proof.requireCurrent(same,actual);
            same.commitImport(prepared);proof.requireCurrent(same,actual);
            var committed=same.readDomain(slot);StrictJson.require(committed instanceof DomainBodies.Available,"actual NEXT family body was not committed");
            var known=(DomainBodies.Available)committed;StrictJson.require(Arrays.equals(output,known.canonicalBody()),"committed NEXT family body differs from actual migration output");result.add(known.reference());
        }
        proof.requireCurrent(same,actual);return List.copyOf(result);
    }
    /** Invoked only by the installed lifecycle's private post-publication callback, under this writer's same lock. */
    public List<DomainBodies.BodyRef> initializeNatural(RootRuntimeContext actual,ContinuityStorePort.Session same,
            org.xar.ck3.control.application.lifecycle.LifecycleComposites.CommittedNatural proof)throws IOException {
        var owner=core();owner.writer().requireSession(same);same.requireWriter(lock);Objects.requireNonNull(proof);
        synchronized(this){StrictJson.require(current==actual,"natural Family requires the installed actual physical context");}
        proof.requireCurrent(same);
        StrictJson.require(proof.owner().machineId().equals(actual.game().machineId())&&proof.owner().game().equals(actual.game().generation())
                &&proof.owner().sessionId().equals(actual.game().sessionId()),"natural Family crossed the actual physical Game/session");
        NaturalBatch batch;
        synchronized(this){batch=naturalBatches.get(proof);}
        if(batch==null) {
            // The actual lifecycle reducer preserved these three references. This exact historical head,
            // rather than an already partly migrated current slot, is the source for warm and cold continuation.
            var lifecyclePin=same.capturePin(proof.lifecycleMaterial(),WriterContracts.MAX_PIN_BYTES);
            var lifecycleEdge=same.readHistoricalTransition(lifecyclePin);
            StrictJson.require(org.xar.ck3.control.application.lifecycle.LifecycleChild.KIND.equals(lifecycleEdge.kind())
                    &&lifecycleEdge.sequence()==proof.headSequence()
                    &&ContinuityJson.digest(lifecycleEdge.after().toJson()).equals(proof.headDigest()),
                    "natural Family requires the actual canonical lifecycle event head, not a later duplicate Receipt head");
            var predecessor=lifecycleEdge.after();same.verifyPin(lifecyclePin);
            var slots=new EnumMap<Slot,NaturalSlot>(Slot.class);
            for(Slot slot:SLOTS) {
                var original=DomainBodies.reference(predecessor,slot).orElseThrow(()->new IOException("natural Family original domain absent: "+slot));
                StrictJson.require(original.slot()==slot&&original.contractSchema().equals(FamilyDomainSource.schema(slot)),"natural Family original schema differs");
                var pin=same.capturePin(original.payload(),MAX);StrictJson.require(pin.identity().equals(original.identity()),"natural Family original native identity changed");
                byte[] bytes=same.readPinned(pin,MAX);
                var transition=new FamilyNaturalEpisodeMigration.Transition(proof.owner(),proof.before(),proof.after(),proof.lifecycleMaterial(),original.payload());
                byte[] output=FamilyNaturalEpisodeMigration.derive(slot,bytes,transition);same.verifyPin(pin);
                slots.put(slot,new NaturalSlot(original,bytes,transition,output));
            }
            proof.requireCurrent(same);batch=new NaturalBatch(actual,proof,Map.copyOf(slots));
            synchronized(this) {
                StrictJson.require(naturalBatches.size()<192,"bounded private natural Family history exhausted");
                StrictJson.require(naturalBatches.putIfAbsent(proof,batch)==null,"natural Family callback raced its original writer");
            }
        }
        StrictJson.require(batch.context()==actual&&batch.proof()==proof,"natural Family private callback changed");
        var result=new java.util.ArrayList<DomainBodies.BodyRef>();
        for(Slot slot:SLOTS) {
            proof.requireCurrent(same);NaturalSlot retained=batch.slots().get(slot);
            var read=same.readDomain(slot);if(!(read instanceof DomainBodies.Available known))throw new IOException("natural Family current full domain unavailable: "+slot);
            FamilyNaturalEpisodeMigration.requireCompatibleCurrent(slot,retained.originalBytes,known.canonicalBody(),retained.transition);
            if(retained.attempted&&retained.receipt==null)retained.receipt=readNaturalImportReceipt(actual,same,slot,retained.prepared);
            if(retained.receipt!=null)same.requireCommitted(retained.prepared,retained.receipt);
            if(Arrays.equals(retained.output,known.canonicalBody())) {
                // A cold re-entry may already have a canonical desired body. This is a read of its exact
                // post-state, not a reconstructed warm Prepared/Receipt and never another import.
                result.add(known.reference());continue;
            }
            if(retained.attempted)throw new IOException("natural Family committed outcome no longer matches its exact derived body");
            StrictJson.require(known.reference().equals(retained.original),"natural Family current CAS predecessor changed its full native identity");
            var archived=owner.archive().preserveArtifact(same,retained.output,MAX);
            var input=StrictJson.object().put("schema",NATURAL_SCHEMA).put("slot",slot.name())
                    .put("lifecycle_head_sequence",proof.headSequence()).put("lifecycle_head_digest",proof.headDigest());
            input.set("transition",retained.transition.toJson());input.set("previous",retained.original.toJson());
            byte[] inputBytes=StrictJson.canonical(input,MAX);
            String identity="family-natural-"+slot.name()+"-"+proof.lifecycleMaterial().sha256()+"-"+retained.original.payload().sha256();
            var request=new DomainBodies.ImportRequest(slot,FamilyDomainSource.schema(slot),archived,inputBytes,
                    List.of(retained.original.payload(),archived,proof.lifecycleMaterial()),identity);
            synchronized(this) {
                StrictJson.require(naturalAuthorizations.size()<576||naturalAuthorizations.containsKey(identity),"bounded private natural Family imports exhausted");
                var authorization=new NaturalAuthorization(batch,slot,retained.original,ActionCodec.sha256(inputBytes),ActionCodec.sha256(retained.output));
                var previous=naturalAuthorizations.putIfAbsent(identity,authorization);
                StrictJson.require(previous==null||previous.equals(authorization),"natural Family import changed its private original proof");
            }
            proof.requireCurrent(same);retained.prepared=same.previewImport(request);proof.requireCurrent(same);
            retained.attempted=true;retained.receipt=same.commitImport(retained.prepared);
            same.requireCommitted(retained.prepared,retained.receipt);proof.requireCurrent(same);
            var committed=same.readDomain(slot);
            if(!(committed instanceof DomainBodies.Available available)||!Arrays.equals(retained.output,available.canonicalBody()))
                throw new IOException("actual natural Family import did not publish its exact derived full body");
            result.add(available.reference());
        }
        proof.requireCurrent(same);return List.copyOf(result);
    }
    /** Reads the actual canonical import event if commit returned no Receipt; an absent event remains UNKNOWN. */
    private WriterContracts.Receipt readNaturalImportReceipt(RootRuntimeContext actual,ContinuityStorePort.Session same,
            Slot slot,DomainBodies.PreparedImport prepared)throws IOException {
        if(prepared==null)throw new IOException("natural Family has an unknown import without its retained preparation");
        long sequence=Math.addExact(prepared.predecessor().state().sequence(),1);
        Path expected=actual.core().configuration().ledger().event(sequence).toAbsolutePath().normalize();
        var pins=same.head().documents().stream().filter(pin->Path.of(pin.reference().path()).toAbsolutePath().normalize().equals(expected)).toList();
        if(pins.size()!=1)throw new IOException("natural Family import result is UNKNOWN; retain the original preparation without replay");
        var edge=same.readHistoricalTransition(pins.getFirst());
        StrictJson.require(edge.sequence()==sequence&&DomainBodies.IMPORT_KIND.equals(edge.kind()),"natural Family import event identity changed");
        var recorded=same.requireHistoricalImport(slot,sequence,ContinuityJson.digest(edge.after().toJson()));
        same.requireCommitted(prepared,recorded.receipt());return recorded.receipt();
    }
    private String verifyNatural(Slot slot,org.xar.ck3.control.continuity.ContinuityState head,Optional<DomainBodies.BodyRef> previous,
            DomainBodies.ImportRequest request,byte[] actual)throws IOException {
        var owner=core();var same=owner.writer().borrowedSession();owner.writer().requireSession(same);same.requireWriter(lock);
        NaturalAuthorization authorization;synchronized(this){authorization=naturalAuthorizations.get(request.evidenceId());}
        StrictJson.require(authorization!=null,"decoded natural Family DATA cannot mint the private committed lifecycle proof");
        var batch=authorization.batch();var proof=batch.proof();proof.requireCurrent(same);
        synchronized(this){StrictJson.require(current==batch.context()&&naturalBatches.get(proof)==batch,"natural Family callback lost installed custody");}
        StrictJson.require(authorization.slot()==slot&&previous.filter(authorization.previous()::equals).isPresent()
                &&request.slot()==slot&&request.contractSchema().equals(FamilyDomainSource.schema(slot))
                &&authorization.inputSha256().equals(ActionCodec.sha256(request.producerInput()))&&authorization.outputSha256().equals(ActionCodec.sha256(actual))
                &&head.sequence()>=proof.headSequence()&&head.machineId().equals(proof.owner().machineId())
                &&DomainBodies.reference(head,slot).filter(authorization.previous()::equals).isPresent(),"natural Family body/predecessor/private input changed");
        var input=StrictJson.object(StrictJson.parse(request.producerInput(),MAX),Set.of("schema","slot","lifecycle_head_sequence","lifecycle_head_digest","transition","previous"));
        var transition=FamilyNaturalEpisodeMigration.Transition.fromJson(input.get("transition"));
        StrictJson.require(NATURAL_SCHEMA.equals(StrictJson.text(input.get("schema")))&&slot.name().equals(StrictJson.text(input.get("slot")))
                &&StrictJson.integer(input.get("lifecycle_head_sequence"),0,StrictJson.MAX_SAFE_INTEGER)==proof.headSequence()
                &&proof.headDigest().equals(StrictJson.text(input.get("lifecycle_head_digest")))
                &&DomainBodies.BodyRef.fromJson(input.get("previous")).equals(authorization.previous())
                &&transition.equals(batch.slots().get(slot).transition),"natural Family import lost its actual original lifecycle/body identity");
        var pin=same.capturePin(authorization.previous().payload(),MAX);
        StrictJson.require(pin.identity().equals(authorization.previous().identity()),"natural Family original full body native identity changed");
        byte[] expected=FamilyNaturalEpisodeMigration.derive(slot,same.readPinned(pin,MAX),transition);
        StrictJson.require(Arrays.equals(expected,actual)&&Arrays.equals(actual,owner.archive().readArtifact(same,request.originalBody(),MAX))
                &&request.evidence().containsAll(List.of(authorization.previous().payload(),proof.lifecycleMaterial())),"natural Family replay differs from its unique full-body producer");
        var lifecycle=same.capturePin(proof.lifecycleMaterial(),WriterContracts.MAX_PIN_BYTES);same.verifyPin(lifecycle);same.verifyPin(pin);proof.requireCurrent(same);
        return ActionCodec.sha256(StrictJson.canonical(StrictJson.object().put("head",ContinuityJson.digest(head.toJson()))
                .put("input",authorization.inputSha256()).put("output",authorization.outputSha256())));
    }
    private String verifyNext(Slot slot,org.xar.ck3.control.continuity.ContinuityState head,Optional<DomainBodies.BodyRef> previous,
            DomainBodies.ImportRequest request,byte[] actual)throws IOException {
        var owner=core();var same=owner.writer().borrowedSession();owner.writer().requireSession(same);NextAuthorization authorization;
        synchronized(this){authorization=nextAuthorizations.get(request.evidenceId());}
        StrictJson.require(authorization!=null,"decoded NEXT DATA cannot mint the private Root domain proof");authorization.proof().requireCurrent(same,authorization.context());
        StrictJson.require(authorization.slot()==slot&&previous.filter(authorization.previous()::equals).isPresent()
                &&authorization.inputSha256().equals(ActionCodec.sha256(request.producerInput()))&&authorization.bodySha256().equals(ActionCodec.sha256(actual))
                &&request.slot()==slot&&request.contractSchema().equals(FamilyDomainSource.schema(slot))
                &&ContinuityJson.digest(head.toJson()).equals(ContinuityJson.digest(same.head().state().toJson())),"NEXT family original proof/body/predecessor changed");
        var input=StrictJson.object(StrictJson.parse(request.producerInput(),MAX),Set.of("schema","slot","kind","transition","previous","old_domain","predecessor_driver","first_saved_driver","current_driver","saved_semantic","current_semantic","baseline","initialization_head_sequence","initialization_head_digest"));
        var transition=FamilyNextEpisodeMigration.Transition.fromJson(input.get("transition"));
        StrictJson.require(DomainBodies.BodyRef.fromJson(input.get("previous")).equals(authorization.previous())
                &&DomainBodies.BodyRef.fromJson(input.get("old_domain")).equals(authorization.oldDomain())&&authorization.proof().oldDomain(slot).equals(authorization.oldDomain())
                &&transition.previousBody().equals(authorization.oldDomain().payload())&&transition.baselineMaterial().equals(authorization.proof().baselineMaterial().reference()),"family initialization lost its original BASELINE full body or current CAS predecessor");
        var pin=same.capturePin(authorization.oldDomain().payload(),MAX);StrictJson.require(pin.identity().equals(authorization.oldDomain().identity()),"family original BASELINE full body native identity changed");
        var previousPin=same.capturePin(authorization.previous().payload(),MAX);StrictJson.require(previousPin.identity().equals(authorization.previous().identity()),"family actual CAS predecessor native identity changed");
        byte[] original=same.readPinned(pin,MAX);FamilyNextEpisodeMigration.requireCompatibleCurrent(slot,original,same.readPinned(previousPin,MAX),transition);
        byte[] expected=FamilyNextEpisodeMigration.derive(slot,original,transition);
        StrictJson.require(Arrays.equals(expected,actual)&&Arrays.equals(actual,owner.archive().readArtifact(same,request.originalBody(),MAX))
                &&request.evidence().containsAll(List.of(authorization.previous().payload(),authorization.oldDomain().payload())),"family original initialization replay differs from its single full-body producer");
        same.verifyPin(pin);same.verifyPin(previousPin);authorization.proof().requireCurrent(same,authorization.context());
        return ActionCodec.sha256(StrictJson.canonical(StrictJson.object().put("head",ContinuityJson.digest(head.toJson())).put("input",authorization.inputSha256()).put("output",authorization.bodySha256())));
    }
    private String verifyOriginal(Slot slot,org.xar.ck3.control.continuity.ContinuityState head,Optional<DomainBodies.BodyRef> previous,
            DomainBodies.ImportRequest request,byte[] actual)throws IOException {
        var owner=core();var same=owner.writer().borrowedSession();owner.writer().requireSession(same);same.requireWriter(lock);
        var input=StrictJson.object(StrictJson.parse(request.producerInput(),MAX),Set.of("schema","slot","selected_original"));
        ExactRef selected=ExactRef.fromJson(input.get("selected_original"));
        StrictJson.require(previous.isEmpty() && selected.equals(selectedOriginals.get(slot)) && StrictJson.text(input.get("slot")).equals(slot.name())
                && request.slot()==slot && request.contractSchema().equals(FamilyDomainSource.schema(slot)) && request.evidence().containsAll(List.of(selected,request.originalBody()))
                && ContinuityJson.digest(head.toJson()).equals(ContinuityJson.digest(same.head().state().toJson())),"family original import source/slot/predecessor differs");
        var pin=same.capturePin(selected,MAX);byte[] observed=same.readPinned(pin,MAX);
        StrictJson.require(Arrays.equals(observed,actual) && Arrays.equals(actual,owner.archive().readArtifact(same,request.originalBody(),MAX)),"full original family file differs from its archived body");
        FamilyDomainSource.validate(slot,actual);same.verifyPin(pin);
        return ActionCodec.sha256(StrictJson.canonical(StrictJson.object().put("head",ContinuityJson.digest(head.toJson()))
                .put("source_sha256",selected.sha256()).put("body_sha256",ActionCodec.sha256(actual))));
    }
}
