package demo;
import com.sun.net.httpserver.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.sql.*;
import java.util.*;
import java.util.concurrent.*;

public final class Application {
    static final Path CONTROL=Path.of(System.getenv().getOrDefault("DEMO_CONTROL_DIR","/var/lib/caixa-demo/control"));
    static Connection db() throws SQLException {
        return DriverManager.getConnection(System.getenv().getOrDefault("DB_URL","jdbc:postgresql://127.0.0.1:5432/caixademo?connectTimeout=3&socketTimeout=3"),"caixademo",System.getenv("DB_PASSWORD"));
    }
    static void log(String event,String id) {System.out.println(java.time.Instant.now()+" event="+event+" request_id="+id);}
    static int validate(String name,String email,boolean faulty) {
        if(name==null||name.isBlank()||name.length()>100||email==null||email.length()>160||!email.matches("[^@\\s]+@[^@\\s]+\\.[^@\\s]+"))return 400;
        return faulty?500:201;
    }
    static Map<String,String> form(String body){var values=new HashMap<String,String>();for(String field:body.split("&")){String[] p=field.split("=",2);if(p.length==2)values.put(URLDecoder.decode(p[0],StandardCharsets.UTF_8),URLDecoder.decode(p[1],StandardCharsets.UTF_8));}return values;}
    static void reply(HttpExchange x,int status,String body,String type)throws java.io.IOException{x.getResponseHeaders().set("Content-Type",type+"; charset=utf-8");x.getResponseHeaders().set("Cache-Control","no-store");byte[] bytes=body.getBytes(StandardCharsets.UTF_8);x.sendResponseHeaders(status,bytes.length);try(var out=x.getResponseBody()){out.write(bytes);}}
    static void handle(HttpExchange x)throws java.io.IOException {
        String id=UUID.randomUUID().toString();x.getResponseHeaders().set("X-Request-Id",id);
        try {
            String path=x.getRequestURI().getPath();
            if(path.equals("/")&&x.getRequestMethod().equals("GET")){reply(x,200,"""
                <!doctype html><html lang="pt-BR"><meta charset="utf-8"><title>CAIXA AI — laboratório</title>
                <style>body{font:20px sans-serif;background:#151515;color:#eee;max-width:700px;margin:60px auto}h1{color:#ff6874}input,button{display:block;margin:18px 0;padding:12px;font:inherit}button{background:#ad1420;color:white;border:0}pre{white-space:pre-wrap}</style>
                <h1>Cadastro de pessoas</h1><p>Ambiente de demonstração. Use apenas dados fictícios.</p>
                <form id="form"><label>Nome<input name="name" required maxlength="100"></label><label>E-mail<input name="email" type="email" required maxlength="160"></label><button>Cadastrar</button></form><pre id="result"></pre>
                <script>document.querySelector('#form').onsubmit=async e=>{e.preventDefault();try{let r=await fetch('/people',{method:'POST',body:new URLSearchParams(new FormData(e.target))});document.querySelector('#result').textContent='HTTP '+r.status+'\\n'+await r.text()+'\\nID: '+r.headers.get('X-Request-Id')}catch(e){document.querySelector('#result').textContent='Serviço indisponível'}};</script></html>
                ""","text/html");return;}
            if(path.equals("/health")&&x.getRequestMethod().equals("GET")){try(var c=db();var st=c.createStatement()){st.execute("SELECT 1");}reply(x,200,"{\"status\":\"UP\",\"database\":\"UP\"}","application/json");return;}
            if(path.equals("/people")&&x.getRequestMethod().equals("POST")){
                byte[] bytes=x.getRequestBody().readNBytes(4097);if(bytes.length>4096){reply(x,413,"Request too large","text/plain");return;}
                var f=form(new String(bytes,StandardCharsets.UTF_8));int status=validate(f.get("name"),f.get("email"),Files.exists(CONTROL.resolve("validation-fault")));
                if(status!=201){log(status==500?"VALIDATION_RULE_DEMO":"INPUT_REJECTED",id);reply(x,status,status==500?"Falha interna na validação do cadastro":"Nome ou e-mail inválido","text/plain");return;}
                try(var c=db();var st=c.prepareStatement("INSERT INTO people(name,email) VALUES (?,?)")){st.setString(1,f.get("name"));st.setString(2,f.get("email"));st.executeUpdate();}
                log("PERSON_CREATED",id);reply(x,201,"Cadastro realizado","text/plain");return;
            }
            reply(x,404,"Not found","text/plain");
        }catch(SQLException e){log("DATABASE_UNAVAILABLE sqlstate="+e.getSQLState(),id);reply(x,503,"Banco indisponível","text/plain");}
        catch(IllegalArgumentException e){reply(x,400,"Invalid request","text/plain");}
        finally{x.close();}
    }
    public static void main(String[] args)throws Exception {
        Files.createDirectories(CONTROL);
        var server=HttpServer.create(new InetSocketAddress(Integer.parseInt(System.getenv().getOrDefault("PORT","8080"))),32);
        server.createContext("/",Application::handle);server.setExecutor(Executors.newFixedThreadPool(4));server.start();log("APP_STARTED","startup");
        Executors.newSingleThreadScheduledExecutor().scheduleWithFixedDelay(()->{
            try {if(Files.deleteIfExists(CONTROL.resolve("oom-once"))){log("OOM_DEMO_TRIGGER_CONSUMED","fault");var allocations=new ArrayList<byte[]>();while(true)allocations.add(new byte[1024*1024]);}}
            catch(java.io.IOException e){log("CONTROL_READ_FAILED","fault");}
        },1,1,TimeUnit.SECONDS);
    }
}
