package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.nativebridge.NativePipeEndpoint;
import org.xar.ck3.control.nativebridge.NativeWire;

/** These negative data gates deliberately construct no Root, writer, Game or qualification authority. */
final class RootManagedLifecycleFactoryTest {
    private static final Instant NOW=Instant.parse("2026-10-24T00:00:00Z");
    private static final GameGeneration GAME=new GameGeneration(123,new PythonOnlyUInt64(BigInteger.valueOf(987654321)));
    private static final String SHA="a".repeat(64);
    private static final ExactRef REF=new ExactRef("controlled-original",1,SHA);
    private static final String OP="controlled-private-action";
    private static NativePipeEndpoint.Config config() {return new NativePipeEndpoint.Config("\\\\.\\pipe\\controlled","controlled-machine",GAME,"controlled-session","controlled-v1",SHA,"controlled-adapter");}
    private static NativeWire.Hello hello(String bridge,BigInteger connection,boolean build) {
        return new NativeWire.Hello(123,connection,bridge,SHA,"controlled-adapter","ready",build,List.of(),new NativeWire.Bytes(new byte[]{1}));
    }
    private static GuardEvidence guard(String session,Instant validUntil) {
        var identity=new ProposalLifecycle.ObservationIdentity("controlled-machine",GAME,
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(100),BigInteger.ONE,BigInteger.ONE),
                        "native:1",BigInteger.ONE,"controlled-episode"),1);
        return new GuardEvidence(identity,new G2Source("controlled-machine",NOW.toString(),"controlled-build",REF),session,
                BigInteger.ONE,new OperationKey(OP),REF,REF,"controlled-root",NOW,validUntil);
    }
    private static NativeRequest request() {return new NativeRequest(OP,Optional.empty(),new RawJson(new byte[]{'{','}'}));}
    @Test void matchingDataGateDoesNotConstructOrGrantPhysicalAuthority() {
        assertDoesNotThrow(()->RootManagedLifecycleFactory.requireFrame(config(),hello("controlled-v1",BigInteger.ONE,true),
                guard("controlled-session",NOW.plusSeconds(30)),request(),NOW));
    }
    @Test void expiredFutureWrongSessionWrongConnectionAndWrongBuildAreRejectedBeforePhysicalLookup() {
        var current=guard("controlled-session",NOW.plusSeconds(30));var hello=hello("controlled-v1",BigInteger.ONE,true);
        assertThrows(java.io.IOException.class,()->RootManagedLifecycleFactory.requireFrame(config(),hello,current,request(),NOW.plusSeconds(30)));
        assertThrows(java.io.IOException.class,()->RootManagedLifecycleFactory.requireFrame(config(),hello,current,request(),NOW.minusSeconds(1)));
        assertThrows(java.io.IOException.class,()->RootManagedLifecycleFactory.requireFrame(config(),hello,guard("other-session",NOW.plusSeconds(30)),request(),NOW));
        assertThrows(java.io.IOException.class,()->RootManagedLifecycleFactory.requireFrame(config(),hello("controlled-v1",BigInteger.TWO,true),current,request(),NOW));
        assertThrows(java.io.IOException.class,()->RootManagedLifecycleFactory.requireFrame(config(),hello("other-v1",BigInteger.ONE,true),current,request(),NOW));
        assertThrows(java.io.IOException.class,()->RootManagedLifecycleFactory.requireFrame(config(),hello("controlled-v1",BigInteger.ONE,false),current,request(),NOW));
        var advertised=new NativeRequest(OP,"unrelated-capability",new RawJson(new byte[]{'{','}'}));
        assertThrows(java.io.IOException.class,()->RootManagedLifecycleFactory.requireFrame(config(),hello,current,advertised,NOW));
    }
}
