package org.xar.ck3.control.application.planning.finance;

import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.planning.PlanningRequest;

/** Ordinary-finance mercenary projection; private construction binds it to the original read receipt. Public payload qualification belongs to ArmyMercenaryContextCodec. */
public final class NativeMercenaryMarket {
    private static final BigInteger U32 = new BigInteger("4294967295");
    private static final BigInteger I64_MAX = BigInteger.valueOf(Long.MAX_VALUE);
    private static final String EXE = "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
    public enum Truth { TRUE, FALSE, UNKNOWN }
    public record Terms(boolean available, Truth canHire, Truth canAfford, Optional<List<BigInteger>> costs,
                        Optional<BigInteger> durationMonths, Obj original) {
        public Terms { costs = costs.map(List::copyOf); Objects.requireNonNull(original); }
    }
    public record Company(BigInteger id, Optional<BigInteger> employer, boolean compositionReady, Terms terms,
            Optional<BigInteger> currentSoldiers, Optional<BigInteger> spawnProvince, boolean positionReady,
            Truth attemptedInWar, Obj original) {
        public Company { Objects.requireNonNull(id); Objects.requireNonNull(employer); Objects.requireNonNull(terms); Objects.requireNonNull(original); }
        public boolean hireReady() { return compositionReady && terms.available() && terms.canHire() == Truth.TRUE; }
        /** Exact copied native employer-wire comparison; this grants no collection or action authority. */
        public boolean employedBy(org.xar.ck3.control.contracts.NativeCharacterId actor) {
            BigInteger expectedWire=BigInteger.valueOf(Integer.toUnsignedLong(Objects.requireNonNull(actor).value()));
            return employer.filter(expectedWire::equals).isPresent();
        }
    }
    public static final class Observation {
        private final FinanceReadContracts.Packet packet;
        private final BigInteger captureEpoch;
        private final boolean available;
        private final List<Company> companies;
        private final Obj original;
        private Observation(FinanceReadContracts.Packet packet, BigInteger epoch, boolean available, List<Company> companies, Obj original) {
            this.packet = packet; this.captureEpoch = epoch; this.available = available; this.companies = List.copyOf(companies); this.original = original;
        }
        public FinanceReadContracts.Packet packet() { return packet; }
        public BigInteger captureEpoch() { return captureEpoch; }
        public boolean available() { return available; }
        public List<Company> companies() { return companies; }
        public Obj original() { return original; }
        public boolean receivedFundsVerified() { return false; }
    }
    private NativeMercenaryMarket() { }
    public static Observation decode(FinanceReadContracts.Packet packet, PlanningRequest request) {
        return decode(packet,request.before(),request.source(),request.sessionId(),request.observations().snapshot());
    }
    /** Same exact codec for archived independent reads; no fabricated PlanningRequest is required. */
    public static Observation decode(FinanceReadContracts.Packet packet,
            org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity current,
            org.xar.ck3.control.g2.common.G2Source source,String sessionId,Obj snapshot) {
        require(FinanceReadContracts.mercenaryFrame(packet.receipt().request()).equals(current)
                &&packet.receipt().request().source().equals(source)&&packet.receipt().request().sessionId().equals(sessionId),"market source request mismatch");
        require(integer(packet.result().get("snapshot_revision"),"market native revision").equals(current.frame().identity().nativeRevision()),"market publication revision mismatch");
        Obj original=object(packet.result().get("player_mercenary_context"),"native mercenary collection");
        var decoded=org.xar.ck3.control.nativebridge.capabilities.army.ArmyMercenaryContextCodec.decode(original,snapshot);
        require(decoded.gameVersion().equals("1.20.0.4")&&decoded.executableSha256().equalsIgnoreCase(EXE)
                &&decoded.actor().equals(current.frame().identity().player())&&decoded.dateRaw().equals(current.frame().identity().dateRaw()),
                "ordinary finance requires the actual same-frame qualified .4 mercenary source");
        List<Company> companies=decoded.candidates().stream().map(company->new Company(BigInteger.valueOf(company.companyId()),
                company.employerId().map(BigInteger::valueOf),company.readiness().compositionReady(),company.terms(),
                company.strength().currentSoldiers().map(BigInteger::valueOf),company.location().hireProvince().map(BigInteger::valueOf),
                company.location().hirePositionReady(),company.location().attemptedInActiveWar().map(value->value?Truth.TRUE:Truth.FALSE).orElse(Truth.UNKNOWN),
                company.normalized())).toList();
        return new Observation(packet,decoded.captureEpoch(),decoded.status().available(),companies,decoded.normalized());
    }
    /** One complete terms decoder shared by original market and original submit-ACK consumers. */
    public static Terms decodeTerms(Obj terms) {
        boolean available=availability(terms);Truth canHire=truth(terms.get("can_hire"),!available),canAfford=truth(terms.get("can_afford"),!available);
        nullable(terms.get("payment_status"),BigInteger.ZERO,BigInteger.TWO,"native admission payment enum");
        require(!available||terms.get("payment_status") instanceof IntegerValue,"available terms need native payment enum");
        require(integer(terms.get("resource_scale"),"native scale").equals(BigInteger.valueOf(100000)),"native cost scale");
        Optional<List<BigInteger>> costs=Optional.empty();
        if(terms.get("resource_costs_raw")!=Nil.INSTANCE) {
            List<Value> vector=array(terms.get("resource_costs_raw"),"ten native costs");require(vector.size()==10,"ten native slots required");
            costs=Optional.of(vector.stream().map(v->bounded(v,BigInteger.valueOf(Long.MIN_VALUE),I64_MAX,"signed native resource")).toList());
        }
        require(!available||costs.isPresent(),"available terms lost costs");Optional<BigInteger> months=nullable(terms.get("hire_duration_months"),BigInteger.ZERO,I64_MAX,"duration");
        for(String prefix:List.of("can_hire","can_afford")) {
            boolean sampled=bool(terms.get(prefix+"_reasons_available"),"native reason sampling");Value literal=terms.get(prefix+"_reason_literal");
            require(sampled?literal instanceof Text:literal==Nil.INSTANCE,"native reason availability mismatch");require(!available||sampled,"available terms lost native reason source");
        }
        return new Terms(available,canHire,canAfford,costs,months,terms);
    }

    private static boolean availability(Obj value) {
        boolean available = bool(value.get("available"), "native availability");
        Value reason = value.get("unavailable_reason");
        require(available ? reason == Nil.INSTANCE : reason instanceof Text && !((Text) reason).value().isEmpty(), "native availability reason mismatch");
        return available;
    }
    private static Truth truth(Value value, boolean nullable) {
        if (value == Nil.INSTANCE && nullable) return Truth.UNKNOWN;
        return bool(value, "native predicate") ? Truth.TRUE : Truth.FALSE;
    }
    private static Optional<BigInteger> nullable(Value value, BigInteger min, BigInteger max, String name) {
        return value == Nil.INSTANCE ? Optional.empty() : Optional.of(bounded(value, min, max, name));
    }
    private static BigInteger bounded(Value value, BigInteger min, BigInteger max, String name) {
        BigInteger result = integer(value, name); require(result.compareTo(min) >= 0 && result.compareTo(max) <= 0, name + " range"); return result;
    }
}


