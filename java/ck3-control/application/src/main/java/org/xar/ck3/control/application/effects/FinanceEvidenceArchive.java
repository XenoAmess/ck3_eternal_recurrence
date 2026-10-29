package org.xar.ck3.control.application.effects;

import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import static org.xar.ck3.control.application.planning.finance.OrdinaryFinanceCollector.obj;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.EnumMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.function.Supplier;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.finance.*;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.feastbudget.FeastBudgetCodec;
import org.xar.ck3.control.finance.feastbudget.FeastBudgetPolicy;
import org.xar.ck3.control.finance.factiongift.FactionGiftChoice;
import org.xar.ck3.control.finance.factiongift.FactionGiftPolicy;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;
import org.xar.ck3.control.wave2.finance.factioncandidate.FactionCandidateCodec;
import org.xar.ck3.control.wave2.finance.factioncandidate.FactionCandidatePolicy;
import org.xar.ck3.control.wave2.finance.factionalerts.FactionThreatAdmission;
import org.xar.ck3.control.wave2.finance.factionalerts.FactionAlertModel;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashCodec;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashPolicy;

/** Original quote custody. This archives evidence; only the Root coordinator may submit an action. */
public final class FinanceEvidenceArchive {
    public static final String ARGUMENT="finance_quote_evidence";
    public static final String SCHEMA="xar.java.finance-original-quote/v2";
    /** Deliberate quote leaf budget supported by the shared exact JSON codec. */
    private static final int MAX_BYTES=StrictJson.EXPLICIT_MAX_BYTES;
    private static final Set<String> FIELDS=Set.of("schema","operation","before","source","session_id","arguments",
            "canonical_head","head_archive","spending","documents","reads","planning_request");
    private final ActionPorts.OutcomeArchive archive;
    private final org.xar.ck3.control.continuity.writer.ContinuityStorePort writer;
    private final Supplier<Session> borrowed;
    private final OriginalEvidencePort originals;
    private final NativeEffectEvidence.FrameLoader frames;
    private final FinanceReadContracts definitions;
    private final ExactRef implementationSource;
    /** Root binds only the sole publisher's actual historical READ interval proof. No DATA flag is qualification. */
    @FunctionalInterface public interface HistoricalRootReplay {
        void requireHistorical(Session same,PlanningReadReceipt originalRoot,GuardEvidence actualTargetGuard,
                Complete actualTargetFrame,ActionPorts.OutcomeArchive sameWriterArchive)throws IOException;
    }
    private final HistoricalRootReplay historicalRoots;
    record HistoricalTarget(GuardEvidence guard,Complete frame) { }
    private final EnumMap<FinanceStatePort.Domain,FinanceStatePort.ReaderBinding> readers=new EnumMap<>(FinanceStatePort.Domain.class);
    public FinanceEvidenceArchive(org.xar.ck3.control.continuity.writer.ContinuityStorePort writer,ActionPorts.OutcomeArchive archive,Supplier<Session> borrowed,OriginalEvidencePort originals,
            NativeEffectEvidence.FrameLoader frames,FinanceReadContracts definitions,List<FinanceStatePort.ReaderBinding> owningReaders,
            ExactRef implementationSource,HistoricalRootReplay historicalRoots) {
        this.writer=Objects.requireNonNull(writer);this.archive=Objects.requireNonNull(archive);this.borrowed=Objects.requireNonNull(borrowed);this.originals=Objects.requireNonNull(originals);
        this.frames=Objects.requireNonNull(frames);this.definitions=Objects.requireNonNull(definitions);
        this.implementationSource=Objects.requireNonNull(implementationSource);require(implementationSource.bytes()>0,"actual selected quote archiver source required");
        this.historicalRoots=Objects.requireNonNull(historicalRoots);
        for(var reader:List.copyOf(owningReaders))require(readers.putIfAbsent(reader.domain(),reader)==null,"duplicate owning quote body decoder");
    }
    /** Called before constructing the canonical command. Missing actual custody defers this optional spending action. */
    public Obj bind(PlanningRequest request,OperationKey operation,OrdinaryFinanceCollector.Current current,
            Optional<OrdinaryFinanceCollector.Gift> gift,Obj arguments) {
        try { return writer.locked(session->bind(session,request,operation,current,gift,arguments)); }
        catch(IOException failure) { throw new IllegalArgumentException("actual finance quote writer transaction unavailable",failure); }
    }
    /** Public and final-lock producers already holding the original writer use only this explicit borrowed overload. */
    public Obj bind(Session session,PlanningRequest request,OperationKey operation,OrdinaryFinanceCollector.Current current,
            Optional<OrdinaryFinanceCollector.Gift> gift,Obj arguments) {
        require(!arguments.members().containsKey(ARGUMENT),"finance evidence cannot recursively bind itself");
        Objects.requireNonNull(session,"actual held writer Session required for quote archival");
        try { return archive.inSession(session,scoped-> {
            try {
                require(current.state().head().current().equals(request.before())
                        &&session.persistedHead().equals(current.state().head().canonicalHead()),"quote no longer uses the actual held canonical head");
                RootGuardChecks.source(session,request.source().sourceRef());
                RootGuardChecks.source(session,implementationSource);
                ExactRef head=current.state().head().canonicalHead();
                ExactRef frozenHead=CanonicalFinanceHeadEvidence.preserve(session,head,scoped,MAX_BYTES);
                List<PlanningReadReceipt> quoteReads=gift.map(OrdinaryFinanceCollector.Gift::originalReads).orElse(current.originalReads());
                require(quoteReads.size()==(operation.equals(OrdinaryFinancePolicies.GIFT)?4:2),"complete original quote read closure required");
                HistoricalTarget target=quoteTarget(quoteReads,request.before(),request.source(),request.sessionId(),scoped);
                require(target.frame().semantic().equals(request.observations().snapshot()),"actual quote target differs from the held complete planning SEM");
                ObjectNode row=StrictJson.object();row.put("schema",SCHEMA);row.put("operation",operation.value());
                row.set("before",ProposalLifecycleCodec.observation(request.before()));row.set("source",ProposalLifecycleCodec.source(request.source()));
                row.put("session_id",request.sessionId());row.set("arguments",toNode(arguments));row.set("canonical_head",head.toJson());row.set("head_archive",frozenHead.toJson());
                row.set("planning_request",StrictJson.parse(org.xar.ck3.control.application.planning.PlanningWire.encodeRequest(request),MAX_BYTES));
                row.set("spending",toNode(current.spendingJson()));var docs=row.putArray("documents");
                for(var domain:requiredDomains()) {
                    var ledger=current.state().ledger(domain).orElseThrow(()->new IllegalArgumentException("original quote spending body missing: "+domain));
                    require(ledger.pending()==FinanceStatePort.Pending.CLEAR,"pending source body cannot authorize new spending");
                    var reader=Objects.requireNonNull(readers.get(domain),"actual owning decoder required");RootGuardChecks.source(session,reader.definitionSource());
                    var document=ledger.document();require(reader.reader().decode(document)==FinanceStatePort.Pending.CLEAR,"owning source body decoder rejected CLEAR");
                    var bodyPin=session.capturePin(document.original(),MAX_BYTES);session.verifyPin(bodyPin);
                    ExactRef archived=preserve(scoped,new RawJson(document.bytes()));session.verifyPin(bodyPin);
                    ObjectNode item=docs.addObject();item.put("domain",domain.name());item.set("original",document.original().toJson());
                    item.set("archive",archived.toJson());item.set("decoder_source",reader.definitionSource().toJson());
                }
                var refs=row.putArray("reads");var seen=new HashSet<String>();
                for(var read:quoteReads) {
                    FinanceReadContracts.Query query=query(read.request().operation());ExactRef definition=definitions.definitionSource(query);
                    require(seen.add(read.requestId()),"original quote contains duplicate read request IDs");RootGuardChecks.source(session,definition);
                    ExactRef ref=scoped.preserveRead(read);require(read.equals(scoped.loadRead(ref))&&ref.equals(scoped.readReferenceOf(read)),"quote read archive readback changed");
                    verifyRead(read,request.before(),request.source(),request.sessionId(),scoped,Optional.of(target));
                    ObjectNode item=refs.addObject();item.put("query",query.name());item.set("definition_source",definition.toJson());item.set("receipt",ref.toJson());
                }
                ExactRef basis=preserve(scoped,new RawJson(quoteBytes(row)));
                return arguments.with(ARGUMENT,object(parse(StrictJson.canonical(basis.toJson(),4096)),"original quote reference"));
            } catch(IOException failure) { throw new UncheckedIOException("original quote custody unavailable",failure); }
        }); } catch(IllegalStateException | UncheckedIOException unavailable) { throw new IllegalArgumentException("original quote requires the held writer and archive scope",unavailable); }
    }
    /** Same source path for final-lock preparation and the independent archived settlement verifier. */
    public void verify(ActionCommand command,ActionPorts.OutcomeArchive sameWriterArchive) {
        verifyDefinitions(Objects.requireNonNull(borrowed.get(),"actual held writer Session required"));
        Obj arguments=withoutEvidence(command.arguments());ExactRef ref=reference(command.arguments());RawJson raw=sameWriterArchive.loadMaterial(ref);RootGuardChecks.exact(ref,raw.bytes());
        ObjectNode row=quoteObject(raw);
        require(SCHEMA.equals(StrictJson.text(row.get("schema")))&&command.operation().value().equals(StrictJson.text(row.get("operation")))
                &&command.before().equals(ProposalLifecycleCodec.decodeObservation(row.get("before")))
                &&ProposalLifecycleCodec.source(command.source()).equals(row.get("source"))
                &&command.sessionId().equals(StrictJson.text(row.get("session_id")))&&toNode(arguments).equals(row.get("arguments")),"quote evidence crossed command/source/session/arguments");
        ExactRef head=ExactRef.fromJson(row.get("canonical_head"));RawJson headRaw=sameWriterArchive.loadMaterial(ExactRef.fromJson(row.get("head_archive")));RootGuardChecks.exact(head,headRaw.bytes());
        require(row.get("reads").isArray()&&row.get("reads").size()==(command.operation().equals(OrdinaryFinancePolicies.GIFT)?4:2),"complete original quote read references required");
        var packets=new EnumMap<FinanceReadContracts.Query,FinanceReadContracts.Packet>(FinanceReadContracts.Query.class);Complete before=null;var seen=new HashSet<String>();
        var archivedReads=new ArrayList<PlanningReadReceipt>();
        for(JsonNode value:row.get("reads")) {
            ObjectNode item=StrictJson.object(value,Set.of("query","definition_source","receipt"));
            ExactRef refRead=ExactRef.fromJson(item.get("receipt"));PlanningReadReceipt originalRead=sameWriterArchive.loadRead(refRead);
            require(refRead.equals(sameWriterArchive.readReferenceOf(originalRead)),"quote target original read reference changed");
            archivedReads.add(originalRead);
        }
        HistoricalTarget target=quoteTarget(archivedReads,command.before(),command.source(),command.sessionId(),sameWriterArchive);
        for(JsonNode value:row.get("reads")) {
            ObjectNode item=StrictJson.object(value,Set.of("query","definition_source","receipt"));FinanceReadContracts.Query query=FinanceReadContracts.Query.valueOf(StrictJson.text(item.get("query")));
            require(definitions.definitionSource(query).equals(ExactRef.fromJson(item.get("definition_source"))),"quote query definition source changed");
            ExactRef readRef=ExactRef.fromJson(item.get("receipt"));PlanningReadReceipt read=sameWriterArchive.loadRead(readRef);
            require(readRef.equals(sameWriterArchive.readReferenceOf(read))&&seen.add(read.requestId()),"quote original read reference or request changed");
            Complete original=verifyRead(read,command.before(),command.source(),command.sessionId(),sameWriterArchive,Optional.of(target));
            if(before==null)before=original;else require(before.semantic().equals(original.semantic()),"quote reads crossed actual semantic frame");
            require(packets.putIfAbsent(query,definitions.decodeOriginal(query,read,original.semantic()))==null,"duplicate original quote query");
        }
        require(before!=null,"original quote has no complete native frame");
        PlanningRequest originalRequest=org.xar.ck3.control.application.planning.PlanningWire.decodeRequest(StrictJson.canonical(row.get("planning_request"),MAX_BYTES));
        require(originalRequest.before().equals(command.before())&&originalRequest.source().equals(command.source())
                &&originalRequest.sessionId().equals(command.sessionId())&&originalRequest.deadline().equals(command.deadline())
                &&originalRequest.observations().snapshot().equals(before.semantic())&&originalRequest.observations().actionSteps().contains(command.operation()),
                "original full planning request differs from actual quote frame/source/session/operation");
        Obj root=object(Objects.requireNonNull(packets.get(FinanceReadContracts.Query.ROOT)).result().get("campaign_root_context"),"actual archived root");
        var market=NativeMercenaryMarket.decode(Objects.requireNonNull(packets.get(FinanceReadContracts.Query.MERCENARIES)),before.identity(),before.source(),before.sessionId(),before.semantic());
        var ledgers=new LinkedHashMap<String,Value>();var domains=java.util.EnumSet.noneOf(FinanceStatePort.Domain.class);Obj procurement=null;
        require(row.get("documents").isArray()&&row.get("documents").size()==requiredDomains().size(),"complete actual quote domain bodies required");
        for(JsonNode value:row.get("documents")) {
            ObjectNode item=StrictJson.object(value,Set.of("domain","original","archive","decoder_source"));var domain=FinanceStatePort.Domain.valueOf(StrictJson.text(item.get("domain")));
            require(requiredDomains().contains(domain)&&domains.add(domain),"duplicate or unrelated quote body");
            var reader=Objects.requireNonNull(readers.get(domain),"actual owning archived body decoder absent");require(reader.definitionSource().equals(ExactRef.fromJson(item.get("decoder_source"))),"owning body decoder source drift");
            ExactRef original=ExactRef.fromJson(item.get("original"));RawJson body=sameWriterArchive.loadMaterial(ExactRef.fromJson(item.get("archive")));RootGuardChecks.exact(original,body.bytes());
            var document=new FinanceStatePort.Document(domain,original,body.bytes());require(reader.reader().decode(document)==FinanceStatePort.Pending.CLEAR,"archived pending body cannot authorize spending");
            Obj parsed=bodyObject(body.bytes());require(parsed.members().containsKey("pending")&&parsed.get("pending")==Nil.INSTANCE,"archived body must explicitly have null pending");
            String key=budgetName(domain);if(key!=null)ledgers.put(key,parsed);
            if(domain==FinanceStatePort.Domain.MERCENARY)procurement=parsed;
        }
        var f=command.before().frame();var id=f.identity();Obj inputs=obj("actor_character_id",new IntegerValue(id.player()),"snapshot_revision",new IntegerValue(id.nativeRevision()),
                "date_raw",new IntegerValue(id.dateRaw()),"post_snapshot_id",new Text(f.snapshotId()),"queried_revision",new IntegerValue(f.revision()));
        Obj wrapper=obj("schema",new Text(FeastBudgetCodec.SCHEMA),"snapshot",before.semantic(),"inputs",inputs,"ledgers",new Obj(ledgers),"campaign_root",root);
        var budget=FeastBudgetPolicy.observe(FeastBudgetCodec.decode(encode(wrapper)));require(budget instanceof FeastBudgetPolicy.Observed,"original spending budget is unavailable");
        require(StrictJson.parse(FeastBudgetCodec.encode(budget)).equals(row.get("spending")),"archived original budget no longer rederives from its true bodies/root/frame");
        require(OrdinaryFinanceCollector.sourceFrame(command.before()).equals(arguments.get("source_frame")),"command quote source frame differs from actual complete original");
        require(new IntegerValue(market.captureEpoch()).equals(arguments.get("pre_capture_epoch"))||command.operation().equals(OrdinaryFinancePolicies.GIFT),"original market capture epoch changed");
        if(command.operation().equals(OrdinaryFinancePolicies.MERCENARY)) {
            BigInteger company=NativeFinanceEffects.company(arguments);var selected=market.companies().stream().filter(c->c.id().equals(company)).toList();
            require(selected.size()==1&&selected.getFirst().original().equals(arguments.get("quoted_company")),"selected mercenary differs from actual original full quote");
        } else {
            require(command.operation().equals(OrdinaryFinancePolicies.GIFT),"unowned finance evidence operation");
            var evaluated=FactionCandidateCodec.evaluatePrivateCandidate(encode(before.semantic()),FactionCandidateCodec.decodeRootProjection(encode(root)),
                    encode(Objects.requireNonNull(packets.get(FinanceReadContracts.Query.FACTION_GIFT)).result()),integer(arguments.get("minimum_gold_reserve_raw"),"actual reserve"));
            require(evaluated instanceof FactionCandidatePolicy.Evaluated&&((FactionCandidatePolicy.Evaluated)evaluated).choice() instanceof FactionGiftChoice.Selected,"actual original gift quote no longer selects");
            var candidate=(FactionCandidatePolicy.Evaluated)evaluated;var selected=(FactionGiftChoice.Selected)candidate.choice();
            Obj choice=object(parse(FactionGiftPolicy.encode(selected)),"original gift choice");
            Obj candidateWire=obj("choice",choice,"observation",object(parse(candidate.observation().original().json()),"original gift observation"));
            require(choice.equals(arguments.get("choice"))&&candidateWire.equals(arguments.get("candidate")),"gift command differs from original native quote");
            var alert=Objects.requireNonNull(packets.get(FinanceReadContracts.Query.FACTION_ALERTS),"actual original stock danger read absent");
            var threat=FactionThreatAdmission.fromExistingDriverResult(encode(alert.result()),new FactionThreatAdmission.Request(
                    new FactionAlertModel.ExpectedFrame(id.dateRaw().intValueExact(),id.nativeRevision(),Optional.of(FactionAlertModel.Build.CK3_12004)),
                    id.player().intValueExact(),selected.sourceFactionId().intValueExact(),selected.recipientCharacterId().intValueExact()),encode(before.semantic().get("active_wars")));
            require(threat instanceof FactionThreatAdmission.Admitted,"original stock danger and membership no longer admit this exact gift");
            require(org.xar.ck3.control.application.driver.DriverJson.object(((FactionThreatAdmission.Admitted)threat).normalizedAlertJson(),RawJson.MAXIMUM_BYTES).equals(arguments.get("pre_faction_alert")),"gift normalized danger facts differ from actual original alert read");
            Obj cash=obj("schema",new Text(GiftWarCashCodec.SCHEMA),"snapshot",before.semantic(),"candidate",candidateWire,"root",root,
                    "spending",object(parse(FeastBudgetCodec.encode(budget)),"actual original budget"),"market",market.original(),
                    "market_source_frame",OrdinaryFinanceCollector.sourceFrame(command.before()),"mercenary_ledger",Objects.requireNonNull(procurement));
            require(GiftWarCashPolicy.assess(GiftWarCashCodec.decode(encode(cash))).newGiftSpendingAllowed(),"original current-cash budget does not authorize gift spending");
            NativeFinanceEffects.giftBaseline(arguments);
        }
    }
    public void verify(Session session,ActionCommand command) { archive.inSession(Objects.requireNonNull(session),scoped->{verify(command,scoped);return Boolean.TRUE;}); }
    public void verify(ActionCommand command) { verify(Objects.requireNonNull(borrowed.get(),"actual held writer Session required"),command); }
    /** The exact complete request captured by the actual quote producer, never an empty projection of unrelated fields. */
    public PlanningRequest originalRequest(Session session,ActionCommand command) {
        return archive.inSession(session,scoped->{verify(command,scoped);var raw=scoped.loadMaterial(reference(command.arguments()));
            var row=quoteObject(raw);
            return org.xar.ck3.control.application.planning.PlanningWire.decodeRequest(StrictJson.canonical(row.get("planning_request"),MAX_BYTES));});
    }
    /** Shared bounded producer/consumer entry. These JSON checks grant no archive, source, or spending authority. */
    static ObjectNode quoteObject(RawJson raw) { return StrictJson.object(StrictJson.parse(raw.bytes(),MAX_BYTES),FIELDS); }
    static byte[] quoteBytes(JsonNode row) { StrictJson.object(row,FIELDS);return StrictJson.canonical(row,MAX_BYTES); }
    private void verifyDefinitions(Session session) {
        try { RootGuardChecks.source(session,implementationSource);for(var reader:readers.values())RootGuardChecks.source(session,reader.definitionSource());
            for(var query:List.of(FinanceReadContracts.Query.ROOT,FinanceReadContracts.Query.MERCENARIES,FinanceReadContracts.Query.FACTION_GIFT,FinanceReadContracts.Query.FACTION_ALERTS))
                RootGuardChecks.source(session,definitions.definitionSource(query));
        } catch(IOException failure) { throw new UncheckedIOException("original quote definition source unavailable",failure); }
    }
    HistoricalTarget quoteTarget(List<PlanningReadReceipt> reads,
            org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity before,
            org.xar.ck3.control.g2.common.G2Source source,String sessionId,ActionPorts.OutcomeArchive scoped) {
        var candidates=reads.stream().filter(read->read.request().operation().equals(FinanceReadContracts.Query.MERCENARIES.operation())).toList();
        require(candidates.size()==1,"the actual quote must retain its one independent mercenary-market target read");
        PlanningReadReceipt target=candidates.getFirst();
        Complete frame=verifyRead(target,before,source,sessionId,scoped,Optional.empty());
        try {RootGuardEvidence.requireHistory(target.before().binding(),scoped,
                Objects.requireNonNull(borrowed.get(),"actual held writer Session required"));}
        catch(IOException failure){throw new UncheckedIOException("original quote target writer history unavailable",failure);}
        return new HistoricalTarget(target.before().binding(),frame);
    }
    Complete verifyRead(PlanningReadReceipt read,org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity before,
            org.xar.ck3.control.g2.common.G2Source source,String sessionId,ActionPorts.OutcomeArchive scoped,
            Optional<HistoricalTarget> target) {
        var query=query(read.request().operation());require(read.request().source().equals(source)&&read.request().sessionId().equals(sessionId),
                "original quote read crossed source/session/registered contract");
        if(query==FinanceReadContracts.Query.ROOT)require(read.contractId().equals(FinanceReadContracts.ROOT_CONTRACT_ID)
                &&FinanceReadContracts.rootCapture(read.request().arguments())==FinanceReadContracts.RootCapture.PUBLIC_QUERY,
                "finance quote ROOT must retain its original public capture; internal preclock originals cannot authorize spending");
        try {
            Session session=Objects.requireNonNull(borrowed.get(),"actual held writer Session required");RootGuardChecks.source(session,definitions.definitionSource(query));
            for(var guard:List.of(read.before().binding(),read.after().binding()))RootGuardChecks.exact(guard.capabilityEvidence(),originals.read(session,guard.capabilityEvidence(),MAX_BYTES));
        } catch(IOException failure) { throw new UncheckedIOException("original quote read capability custody unavailable",failure); }
        NativeRecordedEvidenceVerifier.requireRead(read,scoped);Complete first=RootGuardEvidence.loadFrame(read.before().binding(),scoped,frames),last=RootGuardEvidence.loadFrame(read.after().binding(),scoped,frames);
        require(first.identity().equals(read.request().before())&&last.identity().equals(read.request().before())&&first.source().equals(source)&&last.source().equals(source)
                &&first.sessionId().equals(sessionId)&&last.sessionId().equals(sessionId)&&first.semantic().equals(last.semantic())
                &&read.before().paused()&&read.after().paused()&&read.before().mapReady()&&read.after().mapReady()&&read.before().playerAlive()&&read.after().playerAlive()
                &&read.before().originalBindingSha256().equals(read.after().originalBindingSha256()),"original quote read lacks its complete stable living paused native frame");
        definitions.decodeOriginal(query,read,first.semantic());
        if(read.request().before().equals(before))return first;
        require(query==FinanceReadContracts.Query.ROOT&&read.contractId().equals(FinanceReadContracts.ROOT_CONTRACT_ID)
                &&FinanceReadContracts.rootCapture(read.request().arguments())==FinanceReadContracts.RootCapture.PUBLIC_QUERY,
                "only the installed public ROOT can retain an older public query frame");
        HistoricalTarget actual=target.orElseThrow(()->new IllegalArgumentException("historical ROOT lacks the actual non-ROOT quote target"));
        require(actual.frame().identity().equals(before)&&actual.frame().source().equals(source)&&actual.frame().sessionId().equals(sessionId),
                "historical ROOT quote target changed complete identity/source/session");
        try {historicalRoots.requireHistorical(Objects.requireNonNull(borrowed.get(),"actual held writer Session required"),
                read,actual.guard(),actual.frame(),scoped);}
        catch(IOException unavailable){throw new UncheckedIOException("actual historical ROOT READ qualification unavailable",unavailable);}
        // This is the real retained non-ROOT target frame. The ROOT receipt and its old frame stay untouched.
        return actual.frame();
    }
    public static ExactRef reference(Obj arguments) {
        ExactRef reference=ExactRef.fromJson(toNode(object(arguments.get(ARGUMENT),"durable original finance quote evidence")));
        require(reference.bytes()>0&&java.nio.file.Path.of(reference.path()).isAbsolute(),"actual nonempty absolute original quote artifact required");return reference;
    }
    public static Obj withoutEvidence(Obj arguments) { require(arguments.members().containsKey(ARGUMENT),"durable original finance quote evidence absent");var copy=new LinkedHashMap<>(arguments.members());copy.remove(ARGUMENT);return new Obj(copy); }
    private static ExactRef preserve(ActionPorts.OutcomeArchive archive,RawJson original) { ExactRef ref=archive.preserveMaterial(original);require(original.equals(archive.loadMaterial(ref)),"original quote material archive changed");return ref; }
    private static FinanceReadContracts.Query query(OperationKey operation) { return java.util.Arrays.stream(FinanceReadContracts.Query.values()).filter(q->q.operation().equals(operation)).findFirst().orElseThrow(()->new IllegalArgumentException("unregistered original finance quote query")); }
    private static List<FinanceStatePort.Domain> requiredDomains() { return List.of(FinanceStatePort.Domain.CONSTRUCTION,FinanceStatePort.Domain.FACTION_GIFT,FinanceStatePort.Domain.FIRST_HEIR_MARRIAGE,FinanceStatePort.Domain.CHILD_MARRIAGE,FinanceStatePort.Domain.CHILD_DEFAULT_MARRIAGE,FinanceStatePort.Domain.MERCENARY); }
    private static String budgetName(FinanceStatePort.Domain domain) { return switch(domain) { case CONSTRUCTION->"construction";case FACTION_GIFT->"faction_gift";case FIRST_HEIR_MARRIAGE->"first_heir_marriage";case CHILD_MARRIAGE->"child_marriage";default->null; }; }
    private static Obj bodyObject(byte[] raw) { byte[] json=raw.length>=3&&raw[0]==(byte)0xef&&raw[1]==(byte)0xbb&&raw[2]==(byte)0xbf?java.util.Arrays.copyOfRange(raw,3,raw.length):raw;return org.xar.ck3.control.application.driver.DriverJson.object(json,MAX_BYTES); }
}
