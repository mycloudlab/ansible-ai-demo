package demo;
import com.sun.net.httpserver.HttpServer;
import java.io.*;
import java.net.*;
import java.net.http.*;
import java.nio.charset.StandardCharsets;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
class HttpValidationTest {
 @Test void uncaughtBusinessExceptionProducesGeneric500AndCorrelatedStackTrace() throws Exception {
  var server=HttpServer.create(new InetSocketAddress("127.0.0.1",0),0);
  server.createContext("/",Application::dispatch);
  var captured=new ByteArrayOutputStream();var original=System.err;
  try(var err=new PrintStream(captured,true,StandardCharsets.UTF_8)) {
   System.setErr(err);server.start();
   var request=HttpRequest.newBuilder(URI.create("http://127.0.0.1:"+server.getAddress().getPort()+"/people"))
    .POST(HttpRequest.BodyPublishers.ofString("name=Pessoa&email=private-invalid-value")).build();
   var response=HttpClient.newHttpClient().send(request,HttpResponse.BodyHandlers.ofString());
   assertEquals(500,response.statusCode());
   var requestId=response.headers().firstValue("X-Request-Id").orElseThrow();
   var log=captured.toString(StandardCharsets.UTF_8);
   assertTrue(log.contains("request_id="+requestId));
   assertTrue(log.contains("EmailValidationException"));
   assertTrue(log.contains("Application.validateEmail"));
   assertFalse(log.contains("private-invalid-value"));
   assertFalse(response.body().contains("Exception"));
  } finally {server.stop(0);System.setErr(original);}
 }
}
