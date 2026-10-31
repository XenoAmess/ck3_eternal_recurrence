package org.xar.ck3.research.m1;

import java.util.HashSet;
import java.util.List;
import java.util.Set;
import static org.xar.ck3.research.m1.GovernmentSharedComposition168Fixture.equal;

/** Finite new full193 composition cases; expected values are exclusively the independent book's literals. */
public final class GovernmentFull193172Witness {
    private GovernmentFull193172Witness() { }

    public static void main(String[] args) {
        if(args.length!=0)throw new IllegalArgumentException("no arguments; exact two new Scope172 cases");
        List<GovernmentFull193172CaseApi.Case> cases=GovernmentFull193172CaseBook.cases();
        equal(2,cases.size(),"new Scope172 full193 cases");
        Set<String> names=new HashSet<>();
        for(GovernmentFull193172CaseApi.Case c:cases) {
            if(!names.add(c.name()))throw new AssertionError("duplicate case "+c.name());
            GovernmentRowResolve164Api.Result actual=GovernmentFull193172Composition.execute(
                    c.entry(),c.memory(),c.delegate(),c.lookupBudget(),c.resolveBudget(),
                    c.hashBudget(),c.ownedMxcsrAtHash());
            equal(c.expected(),actual,c.name()+" complete parent result");
            c.delegate().done(c.expectedGsReads());
            c.resolveBudget().done();
            c.hashBudget().done();
            c.after().run();
        }
        System.out.println("GovernmentFull193172Witness: 2/2 new literal full193 all concrete cases");
    }
}
