package org.xar.ck3.control.wave3.planning.m5peacetimeassembly;

import java.math.BigInteger;
import java.util.List;
import java.util.Optional;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import org.xar.ck3.control.wave2.planning.jointintake.FamilyProposalPool;

/** Assembly adapter to the one shared strict family source contract. No second expansion or Native authority. */
public final class M5FamilyCandidatePool {
    public static final String SCHEMA=FamilyProposalPool.SCHEMA;
    public static final String SUBMIT=FamilyProposalPool.SUBMIT;
    private M5FamilyCandidatePool() { }
    public record Variant(BigInteger candidateCharacterId,Obj plan) {
        public Variant { new FamilyProposalPool.Variant(candidateCharacterId,plan); }
    }
    public record Pool(Obj originalPlan,List<Variant> variants) {
        public Pool {
            variants=List.copyOf(variants);
            new FamilyProposalPool.Pool(originalPlan,variants.stream().map(v->new FamilyProposalPool.Variant(v.candidateCharacterId(),v.plan())).toList());
        }
        public PeacetimeAssembly.Family family(){return new PeacetimeAssembly.Family("selected",Optional.of(originalPlan),variants.stream().map(Variant::plan).toList());}
        public Variant candidate(BigInteger actualId){var actual=shared(this).candidate(actualId);return new Variant(actual.candidateCharacterId(),actual.plan());}
    }
    public static Pool collect(Obj actualOwningPolicyPlan){return adapt(FamilyProposalPool.collect(actualOwningPolicyPlan));}
    public static byte[] encode(Pool pool){return FamilyProposalPool.encode(shared(pool));}
    public static Pool decode(byte[] raw){return adapt(FamilyProposalPool.decode(raw));}
    public static Obj toJson(Pool pool){return FamilyProposalPool.toJson(shared(pool));}
    public static Pool fromJson(Obj wire){return adapt(FamilyProposalPool.fromJson(wire));}
    private static Pool adapt(FamilyProposalPool.Pool pool){return new Pool(pool.originalPlan(),pool.variants().stream().map(v->new Variant(v.candidateCharacterId(),v.plan())).toList());}
    private static FamilyProposalPool.Pool shared(Pool pool){return new FamilyProposalPool.Pool(pool.originalPlan(),pool.variants().stream().map(v->new FamilyProposalPool.Variant(v.candidateCharacterId(),v.plan())).toList());}
}
