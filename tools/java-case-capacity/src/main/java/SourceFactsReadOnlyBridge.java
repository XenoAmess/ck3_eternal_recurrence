import java.nio.file.Files;import java.nio.file.Path;import java.lang.reflect.InvocationTargetException;
/** Transport-only bridge: exact original classpath, original consumer, no alternative facts rules. */
public final class SourceFactsReadOnlyBridge {
 private SourceFactsReadOnlyBridge(){}
 public static void main(String[] a)throws Exception{
  if(a.length!=3)throw new IllegalArgumentException("Facts Pin3");
  Class<?> pin=Class.forName("F15ReadOnlyBuildBudget20261029$Pin");
  Object ref=pin.getConstructor(String.class,long.class,String.class).newInstance(a[0],Long.parseLong(a[1]),a[2]);
  var method=Class.forName("SourceSuccessorBuildAdmission").getDeclaredMethod("consumeFacts",pin);method.setAccessible(true);
  try{method.invoke(null,ref);}catch(InvocationTargetException e){Throwable t=e.getCause();if(t instanceof Exception x)throw x;throw e;}
  System.out.write(Files.readAllBytes(Path.of(a[0])));System.out.flush();
 }
}



