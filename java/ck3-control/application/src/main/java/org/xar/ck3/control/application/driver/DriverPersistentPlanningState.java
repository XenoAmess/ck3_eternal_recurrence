package org.xar.ck3.control.application.driver;

import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.advance.*;
import org.xar.ck3.control.application.checkpoint.CheckpointFiles;
import org.xar.ck3.control.application.capabilities.DynamicCapabilities;
import org.xar.ck3.control.application.capabilities.DriverRuntimeCapabilities;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known;
import org.xar.ck3.control.application.planning.campaign.CrossRunPlanning;
import org.xar.ck3.control.application.planning.campaign.CrossRunPlanningDomain;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyWarReadCodec;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyCalls;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes;
import org.xar.ck3.control.nativebridge.capabilities.army.DeclarationOpportunityCooldown;
import org.xar.ck3.control.nativebridge.capabilities.army.DeclarationOpportunityCooldown.*;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;

/** Source-bound persistent planning projections. Only the existing capability producer can mint their repository CAS. */
public final class DriverPersistentPlanningState {
    public static final String COOLDOWN_STATE="declaration_opportunity_cooldown_state";
    public static final String COOLDOWN_SOURCE="declaration_opportunity_cooldown_source";
    public static final String STRATEGY_SOURCE="one_life_strategy_source";
    private static final String SCHEMA="xar.driver-persistent-planning-source/v2";
    private static final int MAX_CHAIN=4096;
    private DriverPersistentPlanningState() { }
    /** No public constructor or untyped auxiliary setter. */
    public static final class Publication {
        private final DriverSnapshotFacts.Stamp expectedStamp;
        private final String expectedAuxiliarySha256;
        private final Obj auxiliary;
        private final ExactRef source;
        private Publication(Known before,Obj auxiliary,ExactRef source){expectedStamp=before.stamp();expectedAuxiliarySha256=DriverJson.sha256(DriverJson.encode(before.auxiliary()));this.auxiliary=auxiliary;this.source=source;}
        Obj auxiliary(){return auxiliary;} ExactRef source(){return source;}
        DriverSnapshotFacts.Stamp expectedStamp(){return expectedStamp;} String expectedAuxiliarySha256(){return expectedAuxiliarySha256;}
    }
    public static Publication crossRun(ContinuityStorePort.Session same,Known current,ActionPorts.OutcomeArchive archive) throws IOException {
        var original=same.readDomain(DomainBodies.Slot.CROSS_RUN_PLANNING);
        require(original instanceof DomainBodies.Available,"actual canonical CROSS_RUN_PLANNING state is unavailable");
        var available=(DomainBodies.Available)original;
        require(available.reference().slot()==DomainBodies.Slot.CROSS_RUN_PLANNING
                &&available.reference().contractSchema().equals(CrossRunPlanningDomain.CONTRACT_SCHEMA),"canonical cross-run contract differs");
        byte[] raw=originalStrategy(same,available);
        var state=CrossRunPlanning.decodeState(raw);byte[] encoded=CrossRunPlanning.encodeState(state);
        Obj strategy=DriverJson.object(encoded,CrossRunPlanning.MAX_BYTES);
        require(strategy.equals(DriverJson.object(raw,CrossRunPlanning.MAX_BYTES)),"typed strategy differs from original payload content");
        ExactRef originalBody=available.reference().payload();
        ExactRef archivedBody=archive.preserveMaterial(new RawJson(raw));
        exact(archivedBody,raw);
        Obj proof=new Obj(Map.of("schema",new Text(SCHEMA),"mode",new Text("CROSS_RUN"),"body",ref(originalBody),"archived_body",ref(archivedBody),"canonical_head",ref(available.head()),"strategy",strategy));
        ExactRef source=archive.preserveMaterial(new RawJson(DriverJson.encode(proof)));
        Map<String,Value> aux=new LinkedHashMap<>(current.auxiliary().members());aux.put("one_life_strategy",strategy);aux.put(STRATEGY_SOURCE,ref(source));
        return new Publication(current,new Obj(aux),source);
    }
    /** Same original writer/current canonical body check. Historical source replay alone cannot supply this fact. */
    public static CrossRunPlanning.State requireCurrentStrategy(ContinuityStorePort.Session same,Known current,ActionPorts.OutcomeArchive archive) throws IOException {
        Objects.requireNonNull(same);Objects.requireNonNull(current);Objects.requireNonNull(archive);
        replay(current.auxiliary(),archive);
        require(current.auxiliary().members().containsKey(STRATEGY_SOURCE),"current canonical strategy source is unavailable");
        Obj proof=material(archive,reference(current.auxiliary().get(STRATEGY_SOURCE)));
        var actual=same.readDomain(DomainBodies.Slot.CROSS_RUN_PLANNING);
        require(actual instanceof DomainBodies.Available,"current original CROSS_RUN_PLANNING body unavailable");
        var available=(DomainBodies.Available)actual;
        require(available.reference().slot()==DomainBodies.Slot.CROSS_RUN_PLANNING
                &&available.reference().contractSchema().equals(CrossRunPlanningDomain.CONTRACT_SCHEMA),"current canonical strategy contract differs");
        byte[] raw=originalStrategy(same,available);
        var state=CrossRunPlanning.decodeState(raw);byte[] encoded=CrossRunPlanning.encodeState(state);
        require(reference(proof.get("body")).equals(available.reference().payload())
                &&DriverJson.object(encoded,CrossRunPlanning.MAX_BYTES).equals(current.auxiliary().get("one_life_strategy")),
                "retained strategy source is not the actual current canonical state");
        return state;
    }
    /** Current canonical domain plus all original completed life receipts, composed before the one Driver CAS. */
    public static Optional<Publication> capture(ContinuityStorePort.Session same,Complete frame,Known current,CheckpointFiles files,
            List<ActionReceipt> canonical,ActionPorts.RecordedEvidenceVerifier evidence,LifeAdvanceEvidence.BoundFrameVerifier lifeFrames,
            ActionPorts.OutcomeArchive archive) throws IOException {
        Known working=current;
        var domain=same.readDomain(DomainBodies.Slot.CROSS_RUN_PLANNING);
        require(domain instanceof DomainBodies.Available,"canonical cross-run planning domain is not initialized");
        var actual=(DomainBodies.Available)domain;
        Value prior=working.auxiliary().get(STRATEGY_SOURCE);
        boolean matches=prior!=null&&reference(material(archive,reference(prior)).get("body")).equals(actual.reference().payload());
        if(!matches) {
            working=withAuxiliary(working,crossRun(same,working,archive).auxiliary());
            replay(working.auxiliary(),archive);
        }
        else {
            replay(working.auxiliary(),archive);
            require(actual.reference().contractSchema().equals(CrossRunPlanningDomain.CONTRACT_SCHEMA),"current cross-run domain contract differs");
            var expected=DriverJson.object(CrossRunPlanning.encodeState(CrossRunPlanning.decodeState(originalStrategy(same,actual))),CrossRunPlanning.MAX_BYTES);
            require(expected.equals(working.auxiliary().get("one_life_strategy")),"current canonical strategy differs from retained source");
        }
        if(!working.auxiliary().members().containsKey(COOLDOWN_STATE)) {
            List<ExactRef> baseline=new ArrayList<>();var head=same.head();
            for(ActionReceipt receipt:canonical) {
                if(!(receipt.command().origin() instanceof CommandOrigin.Gameplay gameplay)
                        ||!gameplay.before().game().equals(frame.identity().game())
                        ||!gameplay.before().frame().episodeRunId().equals(frame.identity().frame().episodeRunId()))continue;
                var completed=AdvanceCompletedRead.read(receipt,archive);if(completed.isEmpty())continue;
                evidence.verify(head,receipt);require(completed.orElseThrow().endDateRaw().compareTo(frame.identity().frame().identity().dateRaw())<=0,"initial cooldown cannot precede its canonical life baseline");
                baseline.add(archive.receiptReferenceOf(receipt));require(baseline.size()<=MAX_CHAIN,"initial cooldown receipt bound exceeded");
            }
            working=withAuxiliary(working,initializeCooldown(frame,working,files,archive,List.copyOf(baseline)).auxiliary());
        }
        var changed=observe(frame,working,canonical,evidence,same.head(),lifeFrames,archive);
        if(changed.isPresent())working=withAuxiliary(working,changed.orElseThrow().auxiliary());
        working=withAuxiliary(working,declarationContinuity(same,frame,working,canonical,evidence,archive).auxiliary());
        return working.auxiliary().equals(current.auxiliary())?Optional.empty():Optional.of(new Publication(current,working.auxiliary(),source(working.auxiliary())));
    }
    /** Same canonical declaration and original decoder; no second pending file or action authority. */
    static Publication declarationContinuity(ContinuityStorePort.Session same,Complete frame,Known current,
            List<ActionReceipt> canonical,ActionPorts.RecordedEvidenceVerifier evidence,ActionPorts.OutcomeArchive archive) throws IOException {
        Obj auxiliary=DriverDeclarationContinuityState.capture(same,frame,current.auxiliary(),canonical,evidence,archive);
        return new Publication(current,auxiliary,reference(auxiliary.get(DriverDeclarationContinuityState.SOURCE)));
    }
    /** Must run after all private initial domain imports, using the actual configured legacy path. */
    public static Publication initializeCooldown(Complete frame,Known current,CheckpointFiles files,ActionPorts.OutcomeArchive archive) throws IOException {
        return initializeCooldown(frame,current,files,archive,List.of());
    }
    private static Publication initializeCooldown(Complete frame,Known current,CheckpointFiles files,ActionPorts.OutcomeArchive archive,List<ExactRef> baseline) throws IOException {
        require(!current.auxiliary().members().containsKey(COOLDOWN_STATE)&&!current.auxiliary().members().containsKey(COOLDOWN_SOURCE),"persistent cooldown has already been initialized");
        var config=DynamicCapabilities.decodeConfiguration(object(current.auxiliary().get("capability_configuration"),"actual configuration"));
        Path path=config.stateDir().orElseThrow(()->new IOException("actual cooldown state directory is unavailable")).resolve(DeclarationOpportunityCooldown.LEGACY_FILENAME).normalize();
        require(path.isAbsolute(),"absolute configured cooldown path required");var witness=files.observe(path);
        Value raw=Nil.INSTANCE;Value original=Nil.INSTANCE;
        if(witness.isPresent()) {
            var actual=witness.orElseThrow();byte[] bytes=files.read(actual,64<<10);files.verify(actual);exact(actual.reference(),bytes);
            raw=parse(bytes);ExactRef archived=archive.preserveMaterial(new RawJson(bytes));
            original=new Obj(Map.of("file",ref(actual.reference()),"identity",parse(StrictJson.canonical(actual.identity().toJson())),"archived",ref(archived)));
        } else require(files.observe(path).isEmpty(),"configured cooldown absence changed during actual capture");
        Frame identity=DeclarationOpportunityCooldown.frame(frame);State state=DeclarationOpportunityCooldown.decode(toNode(raw),identity);
        Reduction reduced=DeclarationOpportunityCooldown.view(state,DeclarationOpportunityCooldown.snapshot(toNode(frame.semantic())),identity);
        Obj input=new Obj(Map.of("configured_path",new Text(path.toString()),"observed_at",new Text(Instant.now().toString()),"original",original,"saved",raw,
                "baseline_receipts",new Arr(baseline.stream().map(value->(Value)ref(value)).toList())));
        return persist(current,frame,current.auxiliary(),null,"INITIAL",input,reduced,baseline,archive);
    }
    public static Publication declaration(Complete frame,Known current,ReadContract<?> exactContract,
            PlanningReadResult.Known<?> actual,ActionPorts.OutcomeArchive archive) {
        require(actual.value() instanceof ArmyWarReadCodec.Declarations,"cooldown completion requires the actual typed DECL observation");
        var read=archive.loadRead(actual.originalReceipt());require(read.equals(actual.receipt())&&archive.readReferenceOf(read).equals(actual.originalReceipt()),"DECL original receipt differs");
        Object replayed=exactContract.replay(read);require(replayed.equals(actual.value()),"DECL typed pure replay differs");
        var declaration=declarations(frame,read);require(declaration.equals(actual.value()),"DECL single original normalizer differs");
        require(read.request().origin() instanceof CommandOrigin.Gameplay&&read.request().before().equals(frame.identity())
                &&read.request().source().equals(frame.source())&&read.request().sessionId().equals(frame.sessionId()),"completed DECL crossed current physical frame/source/session");
        Obj aux=current.auxiliary();State before=state(aux,frame);Frame identity=DeclarationOpportunityCooldown.frame(frame);
        var changed=DeclarationOpportunityCooldown.completed(before,identity,declaration.querySequence());
        var reduced=DeclarationOpportunityCooldown.view(changed.state(),DeclarationOpportunityCooldown.snapshot(toNode(frame.semantic())),identity);
        if(node(DeclarationOpportunityCooldown.encode(reduced.state())).equals(aux.get(COOLDOWN_STATE))
                &&node(DeclarationOpportunityCooldown.encodeView(reduced.view())).equals(aux.get(DeclarationOpportunityCooldown.VIEW_KEY)))return new Publication(current,aux,source(aux));
        return persist(current,frame,aux,source(aux),"DECLARATION",ref(actual.originalReceipt()),reduced,processed(aux,archive),archive);
    }
    /** Canonical APPLIED life results close rounds once. Their actual archived ending world is independently rebuilt. */
    public static Optional<Publication> observe(Complete frame,Known current,List<ActionReceipt> canonical,
            ActionPorts.RecordedEvidenceVerifier evidence,WriterContracts.Head head,LifeAdvanceEvidence.BoundFrameVerifier lifeFrames,
            ActionPorts.OutcomeArchive archive) {
        if(!current.auxiliary().members().containsKey(COOLDOWN_STATE))return Optional.empty();
        Obj aux=current.auxiliary();List<ExactRef> processed=new ArrayList<>(processed(aux,archive));
        for(ActionReceipt receipt:canonical) {
            if(!(receipt.command().origin() instanceof CommandOrigin.Gameplay gameplay)
                    ||!gameplay.before().game().equals(frame.identity().game())
                    ||!gameplay.before().frame().episodeRunId().equals(frame.identity().frame().episodeRunId()))continue;
            var completed=AdvanceCompletedRead.read(receipt,archive);if(completed.isEmpty())continue;
            ExactRef original=archive.receiptReferenceOf(receipt);if(processed.contains(original))continue;
            evidence.verify(head,receipt);var value=completed.orElseThrow();var ending=value.endingFrame(lifeFrames,archive);
            Frame before=from(receipt.command().before()),after=from(ending.identity());
            State state=DeclarationOpportunityCooldown.decode(toNode(aux.get(COOLDOWN_STATE)),before);
            var result=new TurnResult(value.step().value(),AdvanceResult.progressStatus(value.progressStatus()),value.paused(),Optional.of(value.startDateRaw()),Optional.of(value.endDateRaw()));
            var outcome=new Outcome(true,Optional.of(value.step().value()),Optional.of(result));
            var reduced=DeclarationOpportunityCooldown.afterTurn(state,before,outcome,DeclarationOpportunityCooldown.snapshot(toNode(ending.semantic())),after);
            reduced=DeclarationOpportunityCooldown.view(reduced.state(),DeclarationOpportunityCooldown.snapshot(toNode(frame.semantic())),DeclarationOpportunityCooldown.frame(frame));
            processed.add(original);require(processed.size()<=MAX_CHAIN,"finite persistent life receipt bound exceeded");
            Obj input=new Obj(Map.of("receipt",ref(original),"ending_semantic",ref(archive.materialReferenceOf(new RawJson(DriverJson.encode(ending.semantic())))),
                    "result",ref(value.originalResultRef())));
            var publication=persist(current,frame,aux,source(aux),"LIFE",input,reduced,processed,archive);aux=publication.auxiliary();
        }
        State state=state(aux,frame);var reduced=DeclarationOpportunityCooldown.view(state,DeclarationOpportunityCooldown.snapshot(toNode(frame.semantic())),DeclarationOpportunityCooldown.frame(frame));
        Obj nextState=node(DeclarationOpportunityCooldown.encode(reduced.state())),nextView=node(DeclarationOpportunityCooldown.encodeView(reduced.view()));
        if(nextState.equals(aux.get(COOLDOWN_STATE))&&nextView.equals(aux.get(DeclarationOpportunityCooldown.VIEW_KEY)))
            return aux.equals(current.auxiliary())?Optional.empty():Optional.of(new Publication(current,aux,source(aux)));
        return Optional.of(persist(current,frame,aux,source(aux),"VIEW",Nil.INSTANCE,reduced,processed,archive));
    }
    /** Full source chain and typed serialization replay; this does not grant native or action eligibility. */
    public static void replay(Obj auxiliary,ActionPorts.OutcomeArchive archive) {
        DriverDeclarationContinuityState.replay(auxiliary,archive);
        Value strategy=auxiliary.get(STRATEGY_SOURCE);
        require(auxiliary.members().containsKey("one_life_strategy")==auxiliary.members().containsKey(STRATEGY_SOURCE),"strategy and source must be present together");
        if(strategy!=null) {
            Obj proof=material(archive,reference(strategy));require(proof.members().keySet().equals(Set.of("schema","mode","body","archived_body","canonical_head","strategy"))
                    &&new Text(SCHEMA).equals(proof.get("schema"))&&new Text("CROSS_RUN").equals(proof.get("mode")),"exact strategy source required");
            byte[] body=archive.loadMaterial(reference(proof.get("archived_body"))).bytes();exact(reference(proof.get("archived_body")),body);exact(reference(proof.get("body")),body);
            reference(proof.get("canonical_head"));var state=CrossRunPlanning.decodeState(body);
            Obj expected=DriverJson.object(CrossRunPlanning.encodeState(state),CrossRunPlanning.MAX_BYTES);
            require(expected.equals(proof.get("strategy"))&&expected.equals(auxiliary.get("one_life_strategy")),"actual canonical strategy source differs from auxiliary");
        }
        if(!auxiliary.members().containsKey(COOLDOWN_STATE)) { require(!auxiliary.members().containsKey(COOLDOWN_SOURCE),"cooldown source without state");return; }
        ExactRef current=source(auxiliary);List<Obj> reverse=new ArrayList<>();Set<ExactRef> seen=new java.util.HashSet<>();
        while(current!=null) { require(seen.add(current)&&reverse.size()<MAX_CHAIN,"cyclic or excessive cooldown source chain");Obj proof=material(archive,current);reverse.add(proof);current=proof.get("previous")==Nil.INSTANCE?null:reference(proof.get("previous")); }
        State state=null;List<ExactRef> processed=List.of();Obj finalProof=null;
        for(int i=reverse.size()-1;i>=0;i--) {
            Obj proof=reverse.get(i);require(proof.members().keySet().equals(Set.of("schema","mode","previous","frame","input","state","view","processed"))
                    &&new Text(SCHEMA).equals(proof.get("schema")),"exact cooldown proof schema required");
            Complete frame=rebuild(object(proof.get("frame"),"frame"),archive);Frame identity=DeclarationOpportunityCooldown.frame(frame);
            String mode=text(proof.get("mode"),"mode");Reduction reduced;
            if(mode.equals("INITIAL")) {
                require(state==null&&proof.get("previous")==Nil.INSTANCE,"cooldown initial proof cannot reset prior rounds");
                Obj input=object(proof.get("input"),"input");require(input.members().keySet().equals(Set.of("configured_path","observed_at","original","saved","baseline_receipts")),"exact cooldown file capture fields required");Instant.parse(text(input.get("observed_at"),"observed_at"));
                List<ExactRef> baseline=array(input.get("baseline_receipts"),"baseline_receipts").stream().map(DriverPersistentPlanningState::reference).toList();
                require(baseline.size()<=MAX_CHAIN&&new java.util.HashSet<>(baseline).size()==baseline.size(),"bounded unique initial cooldown receipts required");
                for(ExactRef receiptRef:baseline) {
                    ActionReceipt receipt=archive.loadReceipt(receiptRef);require(archive.receiptReferenceOf(receipt).equals(receiptRef),"initial cooldown life original reference differs");
                    var completed=AdvanceCompletedRead.read(receipt,archive).orElseThrow(()->new IllegalArgumentException("initial cooldown baseline requires actual completed life, never UNKNOWN/control"));
                    require(receipt.command().origin() instanceof CommandOrigin.Gameplay&&receipt.command().before().game().equals(frame.identity().game())
                            &&receipt.command().before().frame().episodeRunId().equals(frame.identity().frame().episodeRunId())
                            &&completed.endDateRaw().compareTo(frame.identity().frame().identity().dateRaw())<=0,"initial cooldown life baseline crossed Game/episode/date");
                }
                processed=baseline;
                Path configured=Path.of(text(input.get("configured_path"),"configured_path"));require(configured.isAbsolute()&&configured.getFileName().toString().equals(DeclarationOpportunityCooldown.LEGACY_FILENAME),"cooldown original configured path differs");
                Value saved=input.get("saved");if(input.get("original")!=Nil.INSTANCE) {Obj original=object(input.get("original"),"original");require(original.members().keySet().equals(Set.of("file","identity","archived")),"exact physical cooldown witness fields required");byte[] bytes=archive.loadMaterial(reference(original.get("archived"))).bytes();ExactRef file=reference(original.get("file"));exact(file,bytes);
                    var fileIdentity=org.xar.ck3.control.contracts.FileStatIdentity.fromJson(toNode(original.get("identity")),org.xar.ck3.control.contracts.FileStatIdentity.SCHEMA);
                    require(Path.of(file.path()).equals(configured)&&fileIdentity.bytes().longValueExact()==file.bytes()&&bytes.length<=(64<<10)&&parse(bytes).equals(saved),"original cooldown file identity/content differs");}
                else require(saved==Nil.INSTANCE,"absent cooldown file cannot supply saved content");
                state=DeclarationOpportunityCooldown.decode(toNode(saved),identity);reduced=DeclarationOpportunityCooldown.view(state,DeclarationOpportunityCooldown.snapshot(toNode(frame.semantic())),identity);
            } else {
                require(state!=null,"cooldown transition lacks its actual initial source");
                if(mode.equals("DECLARATION")) {var read=archive.loadRead(reference(proof.get("input")));var declaration=declarations(frame,read);
                    state=DeclarationOpportunityCooldown.decode(DeclarationOpportunityCooldown.encode(state),identity);
                    require(read.request().before().equals(frame.identity())&&read.request().source().equals(frame.source())&&read.request().sessionId().equals(frame.sessionId()),"historical DECL crossed its captured physical frame");
                    reduced=DeclarationOpportunityCooldown.completed(state,identity,declaration.querySequence());
                } else if(mode.equals("LIFE")) {
                    Obj input=object(proof.get("input"),"life input");ExactRef receiptRef=reference(input.get("receipt"));require(!processed.contains(receiptRef),"one life receipt counted twice");
                    ActionReceipt receipt=archive.loadReceipt(receiptRef);var value=AdvanceCompletedRead.read(receipt,archive).orElseThrow();
                    require(value.originalResultRef().equals(reference(input.get("result"))),"life result source differs");
                    Obj ending=material(archive,reference(input.get("ending_semantic")));var after=from(value.endingFrame());var before=from(receipt.command().before());
                    // The source-bound ending semantic contains its independent full manifest; rebuild that original, never a copied ready flag.
                    ExactRef manifest=reference(ending.get("java_driver_facts_evidence"));Obj body=ending;
                    ExactRef nativeRef=receipt.applied().orElseThrow().observation().originalEvidence();Complete rebuilt=rebuild(new Obj(Map.of("manifest",ref(manifest),"native",ref(nativeRef))),archive);
                    require(rebuilt.semantic().equals(body)&&rebuilt.identity().equals(value.endingFrame()),"life complete ending world differs");
                    var outcome=new Outcome(true,Optional.of(value.step().value()),Optional.of(new TurnResult(value.step().value(),AdvanceResult.progressStatus(value.progressStatus()),value.paused(),Optional.of(value.startDateRaw()),Optional.of(value.endDateRaw()))));
                    state=DeclarationOpportunityCooldown.decode(DeclarationOpportunityCooldown.encode(state),before);
                    reduced=DeclarationOpportunityCooldown.afterTurn(state,before,outcome,DeclarationOpportunityCooldown.snapshot(toNode(ending)),after);
                } else {require(mode.equals("VIEW"),"unknown cooldown source transition");require(proof.get("input")==Nil.INSTANCE,"view source has unexpected input");reduced=DeclarationOpportunityCooldown.view(state,DeclarationOpportunityCooldown.snapshot(toNode(frame.semantic())),identity);}
                reduced=DeclarationOpportunityCooldown.view(reduced.state(),DeclarationOpportunityCooldown.snapshot(toNode(frame.semantic())),identity);
            }
            require(node(DeclarationOpportunityCooldown.encode(reduced.state())).equals(proof.get("state"))&&node(DeclarationOpportunityCooldown.encodeView(reduced.view())).equals(proof.get("view")),"cooldown pure source replay differs");
            List<ExactRef> next=array(proof.get("processed"),"processed").stream().map(DriverPersistentPlanningState::reference).toList();
            if(mode.equals("LIFE")) {var expected=new ArrayList<>(processed);expected.add(reference(object(proof.get("input"),"input").get("receipt")));require(expected.equals(next),"processed life receipt chain differs");}
            else require(processed.equals(next),"non-life transition changed processed receipts");
            processed=next;state=reduced.state();finalProof=proof;
        }
        require(finalProof!=null&&finalProof.get("state").equals(auxiliary.get(COOLDOWN_STATE))&&finalProof.get("view").equals(auxiliary.get(DeclarationOpportunityCooldown.VIEW_KEY)),"persistent cooldown auxiliary differs from its complete source chain");
    }
    /** Rebuild the existing DECL decoder scope from this original frame and receipt budget. */
    private static ArmyWarReadCodec.Declarations declarations(Complete frame,PlanningReadReceipt read) {
        var context=new ArmyTypes.Context(frame.identity(),frame.source(),frame.sessionId(),read.request().deadline());
        var call=new ArmyCalls.Frame(PublicMethod.QUERY_DECLARABLE_WARS,
                new ArmyCalls.Revision(new ArmyTypes.Present<>(frame.identity().frame().revision())));
        var decoded=ArmyWarReadCodec.decode(new ArmyWarReadCodec.Scope(call,context,frame.semantic(),Optional.empty()),read);
        require(decoded instanceof ArmyWarReadCodec.Declarations,"original DECL decoder returned another observation");
        return (ArmyWarReadCodec.Declarations)decoded;
    }
    private static Publication persist(Known current,Complete frame,Obj auxiliary,ExactRef previous,String mode,Value input,Reduction reduction,List<ExactRef> processed,ActionPorts.OutcomeArchive archive) {
        var manifest=frame.semantic().get("java_driver_facts_evidence");require(manifest instanceof Obj,"actual full Driver/native manifest required for persistent state");
        Obj state=node(DeclarationOpportunityCooldown.encode(reduction.state())),view=node(DeclarationOpportunityCooldown.encodeView(reduction.view()));
        Obj proof=new Obj(Map.of("schema",new Text(SCHEMA),"mode",new Text(mode),"previous",previous==null?Nil.INSTANCE:ref(previous),
                "frame",new Obj(Map.of("manifest",manifest,"native",ref(frame.originalEvidence()))),"input",input,"state",state,"view",view,
                "processed",new Arr(processed.stream().map(value->(Value)ref(value)).toList())));
        ExactRef source=archive.preserveMaterial(new RawJson(DriverJson.encode(proof)));Map<String,Value> aux=new LinkedHashMap<>(auxiliary.members());
        aux.put(COOLDOWN_STATE,state);aux.put(DeclarationOpportunityCooldown.VIEW_KEY,view);aux.put(COOLDOWN_SOURCE,ref(source));return new Publication(current,new Obj(aux),source);
    }
    private static State state(Obj auxiliary,Complete frame) {require(auxiliary.members().containsKey(COOLDOWN_STATE),"actual legacy cooldown input was not captured");return DeclarationOpportunityCooldown.decode(toNode(auxiliary.get(COOLDOWN_STATE)),DeclarationOpportunityCooldown.frame(frame));}
    private static Known withAuxiliary(Known original,Obj auxiliary) {return new Known(original.driver(),original.stamp(),original.originalHistoryBasis(),original.actionRows(),auxiliary,original.loop(),original.observation());}
    private static List<ExactRef> processed(Obj auxiliary,ActionPorts.OutcomeArchive archive) {Obj proof=material(archive,source(auxiliary));return array(proof.get("processed"),"processed").stream().map(DriverPersistentPlanningState::reference).toList();}
    private static Frame from(org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity value) {var frame=value.frame();return new Frame(frame.identity().player(),frame.episodeRunId(),frame.identity().dateRaw(),frame.identity().nativeRevision(),BigInteger.valueOf(value.game().pid()),Optional.of(frame.snapshotId()));}
    private static Complete rebuild(Obj basis,ActionPorts.OutcomeArchive archive) {ExactRef manifest=reference(basis.get("manifest")),nativeRef=reference(basis.get("native"));RawJson body=archive.loadMaterial(manifest);var nativeFrame=DriverObservationEvidenceReader.nativeFrame(manifest,body,archive.loadNativeFrame(nativeRef));var driver=archive.loadMaterial(DriverObservationEvidenceReader.currentDriverReference(manifest,body));var facts=DriverObservationEvidenceReader.decode(manifest,body,driver,nativeFrame);var result=new DriverObservationAssembler().assemble(nativeFrame,facts,nativeRef);require(result instanceof Complete,"persistent source full Driver/native replay unavailable");return (Complete)result;}
    private static ExactRef source(Obj auxiliary) {return reference(auxiliary.get(COOLDOWN_SOURCE));}
    private static Obj material(ActionPorts.OutcomeArchive archive,ExactRef reference) {RawJson raw=archive.loadMaterial(reference);exact(reference,raw.bytes());return DriverJson.object(raw.bytes(),StrictJson.EXPLICIT_MAX_BYTES);}
    private static Obj node(com.fasterxml.jackson.databind.JsonNode value) {return object(parse(StrictJson.canonical(value)),"typed state");}
    private static Obj ref(ExactRef value) {return DriverRuntimeCapabilities.referenceJson(value);}
    private static ExactRef reference(Value value) {return DriverObservationEvidenceReader.reference(value);}
    private static void exact(ExactRef reference,byte[] bytes) {require(reference.bytes()==bytes.length&&reference.sha256().equals(DriverJson.sha256(bytes)),"persistent original bytes/SHA differ");}
    private static byte[] originalStrategy(ContinuityStorePort.Session same,DomainBodies.Available available) throws IOException {
        ExactRef originalRef=available.reference().payload();
        var pin=same.capturePin(originalRef,CrossRunPlanning.MAX_BYTES);
        require(pin.identity().equals(available.reference().identity()),"pinned identity differs from available reference");
        byte[] raw=same.readPinned(pin,CrossRunPlanning.MAX_BYTES);
        same.verifyPin(pin);
        exact(originalRef,raw);
        require(java.util.Arrays.equals(available.canonicalBody(),ContinuityJson.canonical(ContinuityJson.parseObject(raw,CrossRunPlanning.MAX_BYTES),CrossRunPlanning.MAX_BYTES)),"canonical view differs from original payload");
        return raw;
    }
}
