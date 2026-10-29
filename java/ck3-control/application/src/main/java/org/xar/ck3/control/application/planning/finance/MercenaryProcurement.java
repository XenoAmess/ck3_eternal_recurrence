package org.xar.ck3.control.application.planning.finance;

import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import static org.xar.ck3.control.application.planning.finance.OrdinaryFinanceCollector.obj;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.warbudget.OrdinaryWarPriority;
import org.xar.ck3.control.warbudget.WarEmergencyBudget;

/** Original mercenary pending reducer and independent inventory milestones. No method sends a Native command. */
public final class MercenaryProcurement {
    public static final String SCHEMA="xar.war-mercenary-pending.v1";
    public enum Status { SUBMISSION_UNRESOLVED, NATIVE_REJECTED, EMPLOYMENT_OBSERVED }
    public enum NewHireBarrier { CLEAR, UNKNOWN_PENDING, SAME_FRAME_REJECTION, EMPLOYMENT_AWAITS_INVENTORY }
    public record ZeroDispatchEvidence(org.xar.ck3.control.contracts.ExactRef originalDispatch,NativeActionPort.ZeroDispatchProof original) {
        public ZeroDispatchEvidence { Objects.requireNonNull(originalDispatch);Objects.requireNonNull(original);require(originalDispatch.bytes()>0,"original zero-dispatch archive reference required"); }
    }
    public record Frame(BigInteger player,BigInteger nativeRevision,BigInteger dateRaw,String snapshotId,BigInteger revision,String episodeId) {
        public Frame { Objects.requireNonNull(player);Objects.requireNonNull(nativeRevision);Objects.requireNonNull(dateRaw);Objects.requireNonNull(revision);
            org.xar.ck3.control.contracts.NativeCharacterId.of(player);
            require(nativeRevision.signum()>0&&nativeRevision.bitLength()<=64&&dateRaw.signum()>=0&&revision.signum()>0&&revision.bitLength()<=64,"complete original mercenary frame required");
            org.xar.ck3.control.contracts.StrictJson.text(snapshotId);org.xar.ck3.control.contracts.StrictJson.text(episodeId); }
        public Obj json() { return obj("played_character_id",new IntegerValue(player),"native_revision",new IntegerValue(nativeRevision),"date_raw",new IntegerValue(dateRaw),
                "snapshot_id",new Text(snapshotId),"revision",new IntegerValue(revision),"episode_run_id",new Text(episodeId)); }
        public boolean sameLife(Frame other) { return player.equals(other.player)&&episodeId.equals(other.episodeId); }
    }
    public static final class Claim {
        private final Obj original;private final Status status;private final String requestId;private final BigInteger company;private final Frame source;
        private Claim(Obj original) {
            this.original=Objects.requireNonNull(original);requestId=text(original.get("action_request_id"),"original native request");
            org.xar.ck3.control.contracts.StrictJson.text(requestId);company=integer(original.get("company_id"),"full CompanyID");
            require(company.signum()>=0&&company.compareTo(new BigInteger("4294967295"))<0,"actual full mercenary CompanyID required");source=frame(object(original.get("source_frame"),"original source frame"));
            status=switch(text(original.get("status"),"original mercenary status")) { case "submission_unresolved"->Status.SUBMISSION_UNRESOLVED;case "native_rejected"->Status.NATIVE_REJECTED;case "employment_observed"->Status.EMPLOYMENT_OBSERVED;default->throw new IllegalArgumentException("unknown original mercenary status"); };
            BigInteger epoch=integer(original.get("pre_capture_epoch"),"original market epoch");require(epoch.signum()>0&&epoch.bitLength()<=64,"actual original pre-market epoch required");
            uniqueIds(original.get("pre_player_army_ids"));object(original.get("decision"),"actual original strategic decision");
        }
        public Obj original() { return original; } public Status status() { return status; } public String requestId() { return requestId; }
        public BigInteger company() { return company; } public Frame source() { return source; }
        public BigInteger preEpoch() { return integer(original.get("pre_capture_epoch"),"original market epoch"); }
        public List<BigInteger> oldArmyIds() { return uniqueIds(original.get("pre_player_army_ids")); }
        public Obj selected() { return object(object(original.get("decision"),"original strategic decision").get("selected_candidate"),"actual original selected company"); }
        private Claim with(String key,Value value) { return new Claim(original.with(key,value)); }
    }
    public static final class Ledger {
        private final Obj original;private final Optional<Claim> pending;private final List<Claim> observed;
        private Ledger(Obj original) {
            this.original=Objects.requireNonNull(original);require(new Text(SCHEMA).equals(original.get("schema"))&&original.members().containsKey("pending"),"explicit original mercenary ledger schema/pending required");
            pending=original.get("pending")==Nil.INSTANCE?Optional.empty():Optional.of(new Claim(object(original.get("pending"),"original pending mercenary claim")));
            observed=array(original.get("observed"),"original observed contracts").stream().map(value->new Claim(object(value,"original contract"))).toList();
            require(pending.isEmpty()||pending.orElseThrow().status()==Status.SUBMISSION_UNRESOLVED,"pending mercenary is not unresolved");
            var ids=new HashSet<String>();for(var claim:observed)require(claim.status()!=Status.SUBMISSION_UNRESOLVED&&ids.add(claim.requestId()),"duplicate or unresolved observed contract");
            pending.ifPresent(claim->require(!ids.contains(claim.requestId()),"one mercenary request cannot be both pending and observed"));
        }
        public Obj original() { return original; } public Optional<Claim> pending() { return pending; } public List<Claim> observed() { return observed; }
        private Ledger replace(Optional<Claim> next,List<Claim> history) { return new Ledger(original.with("pending",next.<Value>map(Claim::original).orElse(Nil.INSTANCE))
                .with("observed",new Arr(history.stream().map(claim->(Value)claim.original()).toList()))); }
    }
    private MercenaryProcurement() { }
    public static Ledger decode(byte[] original) { byte[] json=original.length>=3&&original[0]==(byte)0xef&&original[1]==(byte)0xbb&&original[2]==(byte)0xbf?java.util.Arrays.copyOfRange(original,3,original.length):original;return new Ledger(org.xar.ck3.control.application.driver.DriverJson.object(json,4*1024*1024)); }
    public static byte[] encode(Ledger ledger) { byte[] raw=org.xar.ck3.control.application.driver.DriverJson.encode(Objects.requireNonNull(ledger).original());require(raw.length<=4*1024*1024,"bounded full original mercenary body required");return raw; }
    /** Fresh creation must be gated by RootInitialEpisodeProof in the real installer; absence during restore never calls this. */
    public static Ledger emptyFreshEpisode() { return new Ledger(obj("schema",new Text(SCHEMA),"pending",Nil.INSTANCE,"observed",new Arr(List.of()))); }
    public sealed interface NextCash permits NextCashObserved,NextCashUnavailable { }
    public record NextCashObserved(org.xar.ck3.control.wave2.finance.rawcash.RawCashCodec.NormalizedCurrentCash original,
            org.xar.ck3.control.contracts.ExactRef originalRead,Optional<org.xar.ck3.control.contracts.ExactRef> sourceProof) implements NextCash {
        public NextCashObserved {Objects.requireNonNull(original);Objects.requireNonNull(originalRead);Objects.requireNonNull(sourceProof);}
        public NextCashObserved(org.xar.ck3.control.wave2.finance.rawcash.RawCashCodec.NormalizedCurrentCash original, org.xar.ck3.control.contracts.ExactRef originalRead, org.xar.ck3.control.contracts.ExactRef sourceProof) { this(original, originalRead, Optional.of(sourceProof)); }
    }
    public record NextCashUnavailable(String reason,Optional<org.xar.ck3.control.contracts.ExactRef> sourceProof) implements NextCash {
        public NextCashUnavailable {org.xar.ck3.control.contracts.StrictJson.text(reason);Objects.requireNonNull(sourceProof);}
        public NextCashUnavailable(String reason, org.xar.ck3.control.contracts.ExactRef sourceProof) { this(reason, Optional.of(sourceProof)); }
    }
    /** Observed first-SAVE data only; old claims are neither retired nor rebound to the new actor. */
    public enum EpisodeOrigin { NEXT, RESTORED_FIRST }
    /** Original first-SAVE and current physical observations are distinct even when their actor/episode match. */
    public record EpisodeBasis(EpisodeOrigin origin,Frame before,Frame saved,Frame current,Obj savedSnapshot,Obj currentSnapshot,
            org.xar.ck3.control.contracts.ExactRef baselineMaterial,org.xar.ck3.control.contracts.ExactRef originalSemantic,
            org.xar.ck3.control.contracts.ExactRef savedDriver,org.xar.ck3.control.contracts.ExactRef currentSemantic,
            org.xar.ck3.control.contracts.ExactRef currentDriver,org.xar.ck3.control.contracts.ExactRef retainedGiftBody,NextCash currentCash) {
        public EpisodeBasis {
            Objects.requireNonNull(origin);Objects.requireNonNull(before);Objects.requireNonNull(saved);Objects.requireNonNull(current);
            require(fromSnapshot(Objects.requireNonNull(savedSnapshot)).equals(saved)&&fromSnapshot(Objects.requireNonNull(currentSnapshot)).equals(current),"episode finance semantic frames differ from their original sources");
            require(saved.sameLife(current)&&saved.dateRaw().equals(current.dateRaw()),"current physical finance actor/episode/date differs from the selected first SAVE");
            require(origin!=EpisodeOrigin.NEXT||!before.episodeId().equals(saved.episodeId()),"NEXT finance must change the actual episode");
            for(var ref:List.of(baselineMaterial,originalSemantic,savedDriver,currentSemantic,currentDriver,retainedGiftBody))require(ref.bytes()>0,"actual original and current finance evidence required");
            Objects.requireNonNull(currentCash);
            if(currentCash instanceof NextCashObserved known)require(BigInteger.valueOf(known.original().frame().playedCharacterId()).equals(current.player())
                    &&BigInteger.valueOf(known.original().frame().dateRaw()).equals(current.dateRaw()),"current-cash read crossed its actual current physical actor/date");
        }
        public Obj json() {
            var fields=new java.util.LinkedHashMap<String,Value>();
            fields.put("schema",new Text("xar.java.episode-finance-basis/v2"));fields.put("initialization_kind",new Text(origin.name()));
            fields.put("before_frame",before.json());fields.put("original_saved_frame",saved.json());fields.put("current_frame",current.json());
            fields.put("baseline_material",reference(baselineMaterial));fields.put("original_saved_semantic",reference(originalSemantic));fields.put("first_saved_driver",reference(savedDriver));
            fields.put("current_semantic",reference(currentSemantic));fields.put("current_driver",reference(currentDriver));fields.put("retained_gift_obligations",reference(retainedGiftBody));
            switch(currentCash) {
                case NextCashObserved known -> {fields.put("native_cash_status",new Text("observed"));fields.put("current_cash_original_read",reference(known.originalRead()));
                    fields.put("current_cash_source_proof",known.sourceProof().<Value>map(MercenaryProcurement::reference).orElse(Nil.INSTANCE));fields.put("war_cash_current_resources",org.xar.ck3.control.application.driver.DriverJson.object(known.original().toJson(),4*1024*1024));}
                case NextCashUnavailable missing -> {fields.put("native_cash_status",new Text("unavailable"));fields.put("current_cash_unavailable_reason",new Text(missing.reason()));fields.put("current_cash_source_proof",missing.sourceProof().<Value>map(MercenaryProcurement::reference).orElse(Nil.INSTANCE));}
            }
            fields.put("original_saved_wallet",wallet(savedSnapshot));fields.put("current_wallet",wallet(currentSnapshot));
            fields.put("debt_status",new Text("unavailable"));fields.put("inheritance_verified",new Bool(false));
            fields.put("funding_credited_raw",new IntegerValue(BigInteger.ZERO));fields.put("payment_verified",new Bool(false));
            return new Obj(fields);
        }
    }
    private static Obj wallet(Obj snapshot) {
        Value wallet=snapshot.get("played_character_gold");
        if(wallet instanceof Obj observed) {
            require(new IntegerValue(BigInteger.valueOf(100000)).equals(observed.get("scale")),"actual wallet denomination unavailable");
            BigInteger raw=integer(observed.get("raw"),"actual wallet raw");require(raw.compareTo(BigInteger.valueOf(Long.MIN_VALUE))>=0&&raw.compareTo(BigInteger.valueOf(Long.MAX_VALUE))<=0,"native wallet outside int64");
            return obj("status",new Text("observed"),"played_character_gold",observed);
        }
        require(wallet==null||wallet==Nil.INSTANCE,"malformed wallet cannot become unavailable");
        return wallet==null?obj("status",new Text("unavailable")):obj("status",new Text("unavailable"),"played_character_gold",Nil.INSTANCE);
    }
    public static Ledger initializeEpisode(Ledger previous,EpisodeBasis actual) {
        Objects.requireNonNull(previous);Objects.requireNonNull(actual);Obj marker=actual.json();
        Value prior=previous.original().get("episode_finance_basis_v2");
        if(prior instanceof Obj value&&Objects.equals(value.get("current_driver"),marker.get("current_driver"))
                &&Objects.equals(value.get("baseline_material"),marker.get("baseline_material"))) {
            require(value.equals(marker),"same physical finance initialization has conflicting original/current material");return previous;
        }
        Obj next=previous.original();
        if(prior!=null) {
            require(prior instanceof Obj,"invalid original episode finance basis");
            Value history=next.get("episode_finance_basis_history_v2");var retained=new ArrayList<Value>();
            if(history!=null)retained.addAll(array(history,"original finance basis history"));
            retained.add(prior);next=next.with("episode_finance_basis_history_v2",new Arr(retained));
        }
        return new Ledger(next.with("episode_finance_basis_v2",marker));
    }
    private static Obj reference(org.xar.ck3.control.contracts.ExactRef value) {
        return object(parse(org.xar.ck3.control.contracts.StrictJson.canonical(value.toJson())),"actual finance original reference");
    }
    public static Ledger begin(Ledger previous,ActionCommand command) {
        require(command.operation().equals(OrdinaryFinancePolicies.MERCENARY)&&previous.pending().isEmpty(),"unknown original hire must never be submitted again");
        Frame source=frame(object(command.arguments().get("source_frame"),"actual source frame"));
        require(source.json().equals(OrdinaryFinanceCollector.sourceFrame(command.before())),"mercenary pending crossed command Game/frame");
        String requestId=RequestIds.forActionBody(ActionCodec.bodySha256(command));
        require(previous.observed().stream().noneMatch(claim->claim.requestId().equals(requestId)),"original mercenary request has already terminated");
        var pending=new Claim(obj("action_request_id",new Text(requestId),"company_id",command.arguments().get("company_id"),"source_frame",source.json(),
                "status",new Text("submission_unresolved"),"pre_capture_epoch",command.arguments().get("pre_capture_epoch"),
                "pre_player_army_ids",command.arguments().get("pre_player_army_ids"),"decision",command.arguments().get("decision")));
        return previous.replace(Optional.of(pending),previous.observed());
    }
    /** Only the outer real source may supply a decoded original ACK; the domain verifier independently reloads and redecodes it. */
    public static Ledger acknowledge(Ledger previous,String actualRequestId,HireMercenaryAck.Observation ack) {
        Claim pending=requirePending(previous,actualRequestId);require(ack.companyId().equals(pending.company()),"native mercenary ACK company changed");
        pending=pending.with("native_ack",ack.original());
        if(!ack.knownRejectedWithoutSubmission())return previous.replace(Optional.of(pending),previous.observed());
        pending=pending.with("status",new Text("native_rejected"));var history=new ArrayList<>(previous.observed());history.add(pending);return previous.replace(Optional.empty(),history);
    }
    /** A candidate only; its real Source verifies the original canonical receipt and zero-byte dispatch proof before calling this. */
    public static Ledger rejectBeforeDispatch(Ledger previous,String actualRequestId,ZeroDispatchEvidence actualProof) {
        Obj proof=obj("original_dispatch",object(parse(org.xar.ck3.control.contracts.StrictJson.canonical(actualProof.originalDispatch().toJson())),"original zero-dispatch reference"),
                "stage",new Text(actualProof.original().stage().name()),"request_bytes_written",new IntegerValue(BigInteger.valueOf(actualProof.original().requestBytesWritten())),"reason",new Text(actualProof.original().reason()));
        Claim pending=requirePending(previous,actualRequestId).with("status",new Text("native_rejected")).with("zero_dispatch_proof",proof);
        var history=new ArrayList<>(previous.observed());history.add(pending);return previous.replace(Optional.empty(),history);
    }
    public static Ledger refreshInventory(Ledger previous,Obj actualSnapshot) {
        var priority=OrdinaryWarPriority.observe(new OrdinaryWarPriority.Input(org.xar.ck3.control.application.driver.DriverJson.encode(actualSnapshot),new byte[]{'n','u','l','l'}));
        Frame current=fromSnapshot(actualSnapshot);Optional<Claim> pending=previous.pending().map(claim->refresh(claim,current,actualSnapshot,priority));
        List<Claim> history=previous.observed().stream().map(claim->claim.status()==Status.NATIVE_REJECTED?claim:refresh(claim,current,actualSnapshot,priority)).toList();
        return previous.replace(pending,history);
    }
    public static Ledger observeEmployment(Ledger previous,String actualRequestId,Obj actualSnapshot,NativeMercenaryMarket.Observation market) {
        Claim pending=requirePending(previous,actualRequestId);Frame current=fromSnapshot(actualSnapshot);
        require(current.sameLife(pending.source()),"mercenary employment read crossed original actor/episode");
        var factual=FinanceReadContracts.mercenaryFrame(market.packet().receipt().request());
        require(factual.frame().snapshotId().equals(current.snapshotId())
                &&factual.frame().revision().equals(current.revision()),"mercenary employment collection differs from actual current snapshot");
        Ledger refreshed=refreshInventory(previous,actualSnapshot);pending=refreshed.pending().orElseThrow();
        var matches=market.companies().stream().filter(company->company.id().equals(pendingCompany(previous,actualRequestId))).toList();
        require(matches.size()<=1,"duplicate actual full CompanyID");
        if(!market.available()||market.captureEpoch().compareTo(pending.preEpoch())<=0||matches.isEmpty()
                ||!matches.getFirst().employedBy(org.xar.ck3.control.contracts.NativeCharacterId.of(current.player())))return refreshed;
        Claim employment=pending.with("status",new Text("employment_observed")).with("observed_source_frame",current.json())
                .with("capture_epoch",new IntegerValue(market.captureEpoch())).with("employer_character_id",new IntegerValue(current.player()))
                .with("payment_verified",new Bool(false)).with("army_creation_verified",new Bool(false));
        var history=new ArrayList<>(refreshed.observed());history.add(employment);return refreshed.replace(Optional.empty(),history);
    }
    public static NewHireBarrier barrier(Obj snapshot,Ledger ledger) {
        if(ledger.pending().isPresent())return NewHireBarrier.UNKNOWN_PENDING;Frame current=fromSnapshot(snapshot);
        Set<BigInteger> active=new HashSet<>();for(Obj war:rows(snapshot.get("active_wars")))active.add(integer(war.get("war_id"),"actual active WarID"));
        for(int index=ledger.observed().size()-1;index>=0;index--) {
            Claim claim=ledger.observed().get(index);
            if(claim.status()==Status.NATIVE_REJECTED&&claim.source().equals(current))return NewHireBarrier.SAME_FRAME_REJECTION;
            if(claim.status()!=Status.EMPLOYMENT_OBSERVED||!claim.source().sameLife(current))continue;
            Obj selected=claim.selected();Value purposes=selected.members().containsKey("purpose_war_ids")?selected.get("purpose_war_ids"):selected.get("numerical_balance_reversed_war_ids");
            boolean relevant=array(purposes,"actual selected procurement WarIDs").stream().map(value->integer(value,"purpose WarID")).anyMatch(active::contains);
            if(relevant&&firstRaised(snapshot,claim).isEmpty())return NewHireBarrier.EMPLOYMENT_AWAITS_INVENTORY;
            if(relevant)break;
        }
        return NewHireBarrier.CLEAR;
    }
    public static Obj postInventory(Obj snapshot,Claim claim) {
        var priority=OrdinaryWarPriority.observe(new OrdinaryWarPriority.Input(org.xar.ck3.control.application.driver.DriverJson.encode(snapshot),new byte[]{'n','u','l','l'}));
        return postInventory(snapshot,claim,priority);
    }
    private static Obj postInventory(Obj snapshot,Claim claim,OrdinaryWarPriority.Observation priority) {
        require(org.xar.ck3.control.application.driver.DriverJson.object(priority.sourceSnapshot(),4*1024*1024).equals(snapshot),"inventory strength source differs from actual frame");
        var old=new HashSet<>(claim.oldArmyIds());var inventory=new ArrayList<Value>();
        for(Obj army:rows(snapshot.get("player_armies"))) {
            BigInteger id=integer(army.get("army_id"),"actual public CUnit ID");if(old.contains(id))continue;
            Optional<BigInteger> count=priority.countCurrentFullMembers(List.of(id),Optional.empty());
            inventory.add(obj("army_id",new IntegerValue(id),"current_province_id",nullable(army.get("current_province_id")),"current_soldiers",number(count),"controllable",nullable(army.get("controllable"))));
        }
        Obj selected=claim.selected();Optional<BigInteger> before=optionalInteger(object(selected.get("finance"),"original finance").get("observed_treasury_raw"));
        Value money=wallet(snapshot).get("played_character_gold");
        Optional<BigInteger> gold=money instanceof Obj observed?Optional.of(integer(observed.get("raw"),"actual wallet raw")):Optional.empty();
        Optional<BigInteger> delta=gold.flatMap(after->before.map(after::subtract));
        return obj("pre_source_frame",claim.source().json(),"pre_capture_epoch",new IntegerValue(claim.preEpoch()),"pre_player_army_ids",ids(claim.oldArmyIds()),"pre_treasury_raw",number(before),
                "source_frame",fromSnapshot(snapshot).json(),"post_treasury_raw",number(gold),"treasury_delta_raw",number(delta),"quoted_contract_gold_raw",nullable(selected.get("gold_cost_raw")),
                "new_observed_player_armies",new Arr(inventory),"payment_verified",new Bool(false),"army_creation_verified",new Bool(false),"company_to_new_army_binding_verified",new Bool(false),
                "limits",new Text("wallet change may include other flows; new IDs may have other causes; employment, payment, and army attribution are separate"));
    }
    public static Optional<Obj> firstRaised(Obj snapshot,Claim claim) {
        Frame current=fromSnapshot(snapshot);Value prior=claim.original().get("first_raised_inventory_observation_v1");
        Obj selected=claim.selected();Value province=selected.get("predicted_auto_raise_province_id");
        if(!(province instanceof IntegerValue knownProvince)||knownProvince.value().signum()<=0)return Optional.empty();
        if(prior instanceof Obj original) {
            try {
                Frame binding=frame(object(original.get("source_frame"),"actual original inventory frame"));List<Obj> observed=rows(original.get("observed_new_player_armies"));
                if(new IntegerValue(claim.company()).equals(original.get("company_id"))&&binding.sameLife(current)&&binding.sameLife(claim.source())
                        &&current.nativeRevision().compareTo(binding.nativeRevision())>=0&&binding.nativeRevision().compareTo(claim.source().nativeRevision())>0
                        &&Objects.equals(province,original.get("predicted_auto_raise_province_id"))&&!observed.isEmpty()
                        &&observed.stream().allMatch(army->matchesNewArmy(army,claim.oldArmyIds(),province))) {
                    Obj retained=original;
                    for(String flag:List.of("army_creation_verified","company_to_new_army_binding_verified"))
                        if(new Bool(true).equals(retained.get(flag)))retained=retained.with(flag,new Bool(false));
                    return Optional.of(retained);
                }
            } catch(IllegalArgumentException invalid) { /* Invalid historical milestone grants no new hire. Re-observe only, never replay. */ }
        }
        if(!current.sameLife(claim.source())||current.nativeRevision().compareTo(claim.source().nativeRevision())<=0)return Optional.empty();
        Obj post=postInventory(snapshot,claim);List<Obj> matches=rows(post.get("new_observed_player_armies")).stream().filter(army->matchesNewArmy(army,claim.oldArmyIds(),province)).toList();
        if(matches.isEmpty())return Optional.empty();
        return Optional.of(obj("company_id",new IntegerValue(claim.company()),"source_frame",current.json(),"pre_source_frame",claim.source().json(),"pre_player_army_ids",post.get("pre_player_army_ids"),
                "observed_new_player_armies",new Arr(matches.stream().map(value->(Value)value).toList()),"predicted_auto_raise_province_id",nullable(province),
                "observation_kind",new Text("independent_player_inventory_delta_not_strict_company_attribution"),"company_to_new_army_binding_verified",new Bool(false),"army_creation_verified",new Bool(false),
                "does_not_require_army_to_remain_at_spawn_on_later_turns",new Bool(true)));
    }
    public static Optional<Obj> recovery(Obj snapshot,Ledger ledger,Optional<Obj> root) {
        var actual=WarEmergencyBudget.recovery(node(snapshot),node(ledger.original()),root.<com.fasterxml.jackson.databind.JsonNode>map(MercenaryProcurement::node)
                .orElse(com.fasterxml.jackson.databind.node.NullNode.instance));
        return actual.isNull()?Optional.empty():Optional.of(object(parse(org.xar.ck3.control.contracts.StrictJson.canonical(actual)),"actual shared emergency recovery"));
    }
    private static Claim refresh(Claim claim,Frame current,Obj snapshot,OrdinaryWarPriority.Observation priority) {
        if(!current.sameLife(claim.source()))return claim;Claim changed=claim.with("post_hire_observations_v1",postInventory(snapshot,claim,priority));
        Optional<Obj> first=firstRaised(snapshot,claim);return first.map(value->changed.with("first_raised_inventory_observation_v1",value)).orElse(changed);
    }
    private static Claim requirePending(Ledger ledger,String id) { Claim pending=ledger.pending().orElseThrow(()->new IllegalArgumentException("original pending mercenary request absent"));require(pending.requestId().equals(id),"pending request identity changed");return pending; }
    private static BigInteger pendingCompany(Ledger ledger,String id) { return requirePending(ledger,id).company(); }
    private static boolean matchesNewArmy(Obj army,List<BigInteger> old,Value province) {
        Optional<BigInteger> id=optionalInteger(army.get("army_id")),count=optionalInteger(army.get("current_soldiers"));
        return id.isPresent()&&!old.contains(id.orElseThrow())&&new Bool(true).equals(army.get("controllable"))&&Objects.equals(province,army.get("current_province_id"))&&count.filter(number->number.signum()>0).isPresent();
    }
    public static Frame fromSnapshot(Obj snapshot) { Value top=snapshot.get("played_character_id");BigInteger player=integer(object(snapshot.get("played_character"),"actual player").get("character_id"),"player");
        if(top!=null&&top!=Nil.INSTANCE)require(integer(top,"actual player mirror").equals(player),"native player mirrors conflict");
        return new Frame(player,integer(snapshot.get("native_revision"),"native revision"),integer(snapshot.get("date_raw"),"date"),text(snapshot.get("snapshot_id"),"snapshot ID"),integer(snapshot.get("revision"),"public revision"),text(snapshot.get("episode_run_id"),"episode")); }
    public static Frame fromObservation(org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity original) {
        return frame(OrdinaryFinanceCollector.sourceFrame(Objects.requireNonNull(original)));
    }
    private static Frame frame(Obj value) { return new Frame(integer(value.get("played_character_id"),"player"),integer(value.get("native_revision"),"native revision"),integer(value.get("date_raw"),"date"),text(value.get("snapshot_id"),"snapshot ID"),integer(value.get("revision"),"public revision"),text(value.get("episode_run_id"),"episode")); }
    private static List<BigInteger> uniqueIds(Value value) { var result=array(value,"original player CUnit IDs").stream().map(id->integer(id,"public CUnit ID")).sorted().toList();require(new HashSet<>(result).size()==result.size(),"duplicate original player army ID");return result; }
    private static List<Obj> rows(Value value) { return value instanceof Arr values?values.items().stream().filter(item->item instanceof Obj).map(item->(Obj)item).toList():List.of(); }
    private static com.fasterxml.jackson.databind.node.ObjectNode node(Obj value) {
        var converted=toNode(value);if(converted instanceof com.fasterxml.jackson.databind.node.ObjectNode original)return original;
        throw new IllegalArgumentException("original typed object did not encode to a JSON object");
    }
    private static Arr ids(List<BigInteger> values) { return new Arr(values.stream().sorted().map(value->(Value)new IntegerValue(value)).toList()); }
    private static Value nullable(Value value) { return value==null?Nil.INSTANCE:value; }
    private static Optional<BigInteger> optionalInteger(Value value) { return value instanceof IntegerValue number?Optional.of(number.value()):Optional.empty(); }
    private static Value number(Optional<BigInteger> value) { return value.<Value>map(IntegerValue::new).orElse(Nil.INSTANCE); }
}
