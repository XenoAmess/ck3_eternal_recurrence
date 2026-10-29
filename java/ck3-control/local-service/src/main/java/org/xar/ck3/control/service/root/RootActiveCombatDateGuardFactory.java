package org.xar.ck3.control.service.root;

import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.planning.military.ActiveCombatDateGuards;
import org.xar.ck3.control.application.planning.military.ActiveCombatGuardProducers;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Installs the existing real wrapper with concrete pure current-frame producers; no fresh Root observation is taken. */
public final class RootActiveCombatDateGuardFactory {
    private RootActiveCombatDateGuardFactory() { }
    public record Sources(ExactRef policy,ExactRef resumeProducer,ExactRef observedComparison,ExactRef defenderCodec) {
        public Sources {for(ExactRef ref:List.of(policy,resumeProducer,observedComparison,defenderCodec))
            StrictJson.require(ref.bytes()>0,"actual guard/resume/comparison/defender source roles required");}
        public List<ExactRef> all(){return List.of(policy,resumeProducer,observedComparison,defenderCodec);}
    }
    public record Installed(ActiveCombatDateGuards policy,RootDomainInstallation installation) {
        public Installed {
            Objects.requireNonNull(policy);Objects.requireNonNull(installation);
            StrictJson.require(installation.policies().size()==1 && installation.policies().getFirst()==policy,
                    "Root must install the identical concrete active combat/date guard policy");
        }
    }
    public static Installed install(Sources sources) {
        Objects.requireNonNull(sources);var actual=new ActiveCombatGuardProducers();
        var policy=new ActiveCombatDateGuards(sources.policy(),actual,actual);
        var installation=new RootDomainInstallation("actual-active-combat-and-date-guards",List.of(),List.of(),List.of(),List.of(),List.of(),List.of(),
                List.of(),List.of(),List.of(),List.of(),Set.of(),List.of(policy),List.of(),List.of(),List.of(),List.of());
        return new Installed(policy,installation);
    }
}
