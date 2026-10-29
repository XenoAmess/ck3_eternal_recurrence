package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.util.ArrayList;
import java.util.EnumSet;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.planning.family.FamilyDomainSource;
import org.xar.ck3.control.application.planning.finance.CanonicalFinanceStateSource;
import org.xar.ck3.control.application.planning.finance.ConstructionLedgerCodec;
import org.xar.ck3.control.application.planning.finance.FinanceStatePort;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Five actual external gold owners, using their same registered body/schema/source inventory and sole strict decoder.
 * Missing/unimported bodies remain absent in CanonicalFinanceStateSource; no reader fabricates CLEAR. */
public final class RootFinanceBodyBindings {
    private RootFinanceBodyBindings(){ }
    public static List<CanonicalFinanceStateSource.Binding> prepare(ConstructionRuntimeInstaller.Sources construction,
            RootFamilyRuntimeFactory.Prepared family,GovernanceOrdinaryRuntimeInstaller.Prepared governance,
            RootRuntimeSelectedSources selected)throws IOException {
        Objects.requireNonNull(construction);Objects.requireNonNull(family);Objects.requireNonNull(governance);Objects.requireNonNull(selected);
        return prepare(construction,family,governance,
                selected.javaSource(RootRuntimeSelectedSources.Module.APPLICATION,ConstructionLedgerCodec.class),
                selected.javaSource(RootRuntimeSelectedSources.Module.APPLICATION,FamilyDomainSource.class));
    }
    public static List<CanonicalFinanceStateSource.Binding> prepare(ConstructionRuntimeInstaller.Sources construction,
            RootFamilyRuntimeFactory.Prepared family,GovernanceOrdinaryRuntimeInstaller.Prepared governance,
            ExactRef constructionDecoder,ExactRef familyDecoder)throws IOException {
        Objects.requireNonNull(construction);Objects.requireNonNull(family);Objects.requireNonNull(governance);
        Objects.requireNonNull(constructionDecoder);Objects.requireNonNull(familyDecoder);
        var result=new ArrayList<CanonicalFinanceStateSource.Binding>();var building=construction.registration();
        result.add(new CanonicalFinanceStateSource.Binding(new FinanceStatePort.ReaderBinding(FinanceStatePort.Domain.CONSTRUCTION,
                constructionDecoder,document->
                    ConstructionLedgerCodec.decodeLedger(document.bytes()).pending().isPresent()?FinanceStatePort.Pending.PENDING:FinanceStatePort.Pending.CLEAR),
                building.slot(),building.contractSchema(),building.maximumBodyBytes(),building.producerSources()));
        for(var registration:family.domainRegistrations()){
            FinanceStatePort.Domain domain=switch(registration.slot()){
                case FAMILY->FinanceStatePort.Domain.FIRST_HEIR_MARRIAGE;
                case CHILD_MATRILINEAL->FinanceStatePort.Domain.CHILD_MARRIAGE;
                case DEFAULT_MARRIAGE->FinanceStatePort.Domain.CHILD_DEFAULT_MARRIAGE;
                default->throw new IOException("unexpected external Family gold registration: "+registration.slot());
            };
            result.add(new CanonicalFinanceStateSource.Binding(new FinanceStatePort.ReaderBinding(domain,familyDecoder,document->{
                var body=FamilyDomainSource.validate(registration.slot(),document.bytes());var pending=body.get("pending");
                if(pending==OpportunityJson.Nil.INSTANCE)return FinanceStatePort.Pending.CLEAR;
                if(pending instanceof OpportunityJson.Obj)return FinanceStatePort.Pending.PENDING;
                throw new IllegalArgumentException("actual canonical family pending state is neither explicit null nor a validated record");
            }),registration.slot(),registration.contractSchema(),registration.maximumBodyBytes(),registration.producerSources()));
        }
        result.add(governance.feastDomain().financeBinding());
        var actual=EnumSet.noneOf(FinanceStatePort.Domain.class);for(var binding:result)
            if(!actual.add(binding.decoder().domain()))throw new IOException("one actual external gold domain was supplied twice");
        if(result.size()!=5||!actual.equals(EnumSet.of(FinanceStatePort.Domain.CONSTRUCTION,FinanceStatePort.Domain.FIRST_HEIR_MARRIAGE,
                FinanceStatePort.Domain.CHILD_MARRIAGE,FinanceStatePort.Domain.CHILD_DEFAULT_MARRIAGE,FinanceStatePort.Domain.FEAST)))
            throw new IOException("complete actual five external gold-domain producers are required");
        return List.copyOf(result);
    }
}
