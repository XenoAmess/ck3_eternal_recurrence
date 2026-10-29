package org.xar.ck3.control.service.root;

import java.time.Duration;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.planning.finance.FinanceReadContracts;
import org.xar.ck3.control.application.planning.military.CommanderBindings;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.army.*;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;

/** Adds the remaining three read handlers without replacing their already-owned market or commander producers. */
public final class ArmyAdditionalReadInstaller {
    public record Sources(ExactRef reinforcementDefinition,ExactRef reinforcementDecoder,ExactRef publicService) {
        public Sources {for(ExactRef source:List.of(reinforcementDefinition,reinforcementDecoder,publicService))StrictJson.require(source.bytes()>0,"actual full query implementation source required");}
    }
    public record Installed(RootDomainInstallation installation,ArmyAdditionalReadService service,ArmyReinforcementReads reinforcement) { }
    private final RootRuntimeContext context;private final ArmyRuntimeInstaller.Installed army;private final FinanceReadContracts finance;private final CommanderBindings commanders;
    private final Sources sources;private final Duration timeout;private Installed installed;
    public ArmyAdditionalReadInstaller(RootRuntimeContext context,ArmyRuntimeInstaller.Installed identicalArmy,FinanceReadContracts identicalFinance,CommanderBindings identicalCommander,Sources sources,Duration timeout) {
        this.context=Objects.requireNonNull(context);army=Objects.requireNonNull(identicalArmy);finance=Objects.requireNonNull(identicalFinance);commanders=Objects.requireNonNull(identicalCommander);this.sources=Objects.requireNonNull(sources);this.timeout=Objects.requireNonNull(timeout);StrictJson.require(!timeout.isNegative()&&!timeout.isZero()&&timeout.compareTo(Duration.ofMinutes(1))<=0,"finite actual Army query deadline required");
    }
    public synchronized Installed install() {
        StrictJson.require(installed==null,"one additional Army query installation per actual physical Game required");
        var reinforcement=new ArmyReinforcementReads(sources.reinforcementDefinition(),sources.reinforcementDecoder(),context.reads());
        var service=new ArmyAdditionalReadService(context.writer(),army.frames(),context.reads(),context::readCatalog,finance,commanders,reinforcement,()->context.clock().instant().plus(timeout));
        var installation=new RootDomainInstallation("army-market-commander-reinforcement-public-reads",List.of(),List.of(),reinforcement.families(),List.of(),List.of(),List.of(),List.of(),List.of(),List.of(),List.of(),Set.of(),List.of(),List.of(),List.of(),List.of(),List.of());
        installed=new Installed(installation,service,reinforcement);return installed;
    }
    public List<PublicBindings.BoundBinding> installPublic(PublicBindings bindings) {return Objects.requireNonNull(installed,"actual additional Army query installer is unavailable").service().install(bindings,sources.publicService());}
}
