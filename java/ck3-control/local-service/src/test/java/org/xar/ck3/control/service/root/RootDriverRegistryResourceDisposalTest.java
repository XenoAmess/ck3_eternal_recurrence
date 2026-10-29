package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.service.root.RootDriverRegistryPublicProducts.Product;

/** Mechanical resource fixtures carry no Core, Game, frame, permission or native qualification. */
final class RootDriverRegistryResourceDisposalTest {
    private static final class Resource implements Product, AutoCloseable {
        private final String name; private final List<String> order; private final Exception failure;
        private Resource(String name,List<String> order,Exception failure){this.name=name;this.order=order;this.failure=failure;}
        @Override public void close()throws Exception{order.add(name);if(failure!=null)throw failure;}
        @Override public RootDomainInstallation installation(){throw new AssertionError("disposal must not create or inspect authority");}
        @Override public void requireContext(RootRuntimeContext ignored){throw new AssertionError("no artificial runtime context");}
    }
    private static final class NoResource implements Product {
        @Override public RootDomainInstallation installation(){throw new AssertionError("no installation lookup during disposal");}
        @Override public void requireContext(RootRuntimeContext ignored){throw new AssertionError("no artificial runtime context");}
    }
    @Test void closesOnlyRealResourceProductsInReverseAcquisitionOrder() {
        var order=new ArrayList<String>();
        assertNull(RootDriverRegistryPublicProducts.closeProducts(List.of(new Resource("first",order,null),new NoResource(),new Resource("last",order,null)),null));
        assertEquals(List.of("last","first"),order);
    }
    @Test void preservesTheOriginalInstallationFailureAndDisposesEveryOwnedResource() {
        var order=new ArrayList<String>();var original=new IOException("actual installation failure");
        var last=new IOException("actual observer disposal failed");var first=new IllegalStateException("another resource failed");
        var result=RootDriverRegistryPublicProducts.closeProducts(List.of(new Resource("first",order,first),new Resource("last",order,last)),original);
        assertSame(original,result);assertEquals(List.of("last","first"),order);
        assertEquals(2,result.getSuppressed().length);assertSame(last,result.getSuppressed()[0]);
        assertSame(first,result.getSuppressed()[1].getCause());
    }
    @Test void preservesInterruptionAndStillDisposesLaterResourcesWithoutGrantingExit() {
        boolean originallyInterrupted=Thread.interrupted();
        try {
            var order=new ArrayList<String>();var interrupt=new InterruptedException("actual observer interrupted");
            var result=RootDriverRegistryPublicProducts.closeProducts(List.of(new Resource("first",order,null),new Resource("last",order,interrupt)),null);
            assertNotNull(result);assertSame(interrupt,result.getCause());assertTrue(Thread.currentThread().isInterrupted());
            assertEquals(List.of("last","first"),order);
        } finally {Thread.interrupted();if(originallyInterrupted)Thread.currentThread().interrupt();}
    }
}

