package network;

import java.io.InputStream;
import java.io.OutputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.util.Hashtable;
import java.util.Vector;
import javax.microedition.io.Connector;
import javax.microedition.io.HttpConnection;
import utils.ScreenManager;

/** Real HTTP requests off the UI thread. Tokens never enter persistent RMS storage. */
public final class Api {
    public static String baseUrl = "http://127.0.0.1:8000";
    private static String accessToken = "";
    private static String refreshToken = "";
    private static Vector permissions = new Vector();
    private static int generation = 0;
    private static final Object refreshLock = new Object();
    public interface Listener { void success(Object data); void failure(String message); }
    public static synchronized boolean can(String permission) { return permissions.contains(permission); }
    public static synchronized boolean authenticated() { return accessToken.length() > 0; }
    private static synchronized String access() { return accessToken; }
    private static synchronized String refresh() { return refreshToken; }
    public static synchronized void clear() { accessToken = ""; refreshToken = ""; permissions = new Vector(); generation++; }
    public static synchronized void tokens(Hashtable data) {
        accessToken = Json.str(data,"access_token"); refreshToken = Json.str(data,"refresh_token");
    }
    public static synchronized void profile(Hashtable data) { permissions = (Vector)data.get("permissions"); }
    public static void configure(String url) {
        url = url.trim();
        while (url.endsWith("/")) url = url.substring(0,url.length()-1);
        if (!(url.startsWith("https://") || url.startsWith("http://127.0.0.1:") || url.startsWith("http://localhost:") || url.startsWith("http://10.0.2.2:")))
            throw new IllegalArgumentException("HTTPS requis, sauf emulateur local");
        if (url.indexOf('@') >= 0 || url.indexOf('?') >= 0 || url.indexOf('#') >= 0)
            throw new IllegalArgumentException("Adresse serveur invalide");
        if (!url.equals(baseUrl)) clear();
        baseUrl = url;
    }
    public static void request(final String method, final String path, final Hashtable body, final Listener listener) {
        final int started;
        final String server;
        synchronized (Api.class) { started = generation; server = baseUrl; }
        new Thread(new Runnable() {
            public void run() {
                Object result = null; String error = null;
                try {
                    Result response;
                    synchronized (Api.class) {
                        if (started != generation) return;
                    }
                    String sentToken = access();
                    response = exchange(server,method,path,body,sentToken);
                    if (response.status == 401 && !path.startsWith("/auth/")) {
                        synchronized (refreshLock) {
                            synchronized (Api.class) { if (started != generation) return; }
                            if (sentToken.equals(access()) && refresh().length() > 0) {
                                Hashtable request = Json.object(); request.put("refresh_token",refresh());
                                Result rotated = exchange(server,"POST","/auth/refresh",request,"");
                                synchronized (Api.class) { if (started != generation) return; }
                                if (rotated.status == 200) tokens((Hashtable)rotated.data);
                                else { clear(); throw new Exception("Session expiree. Reconnectez-vous."); }
                            }
                        }
                        response = exchange(server,method,path,body,access());
                    }
                    if (response.status < 200 || response.status >= 300) {
                        String detail = "Requete refusee";
                        if (response.data instanceof Hashtable) detail = Json.str((Hashtable)response.data,"detail");
                        if (detail.length() > 250) detail = detail.substring(0,250);
                        throw new Exception("HTTP " + response.status + " : " + detail);
                    }
                    result = response.data;
                } catch (Exception ex) { error = ex.getMessage(); if (error == null) error = "Connexion impossible"; }
                final Object value = result; final String problem = error;
                ScreenManager.getDisplay().callSerially(new Runnable() {
                    public void run() {
                        synchronized (Api.class) { if (started != generation && problem == null) return; }
                        if (problem == null) listener.success(value); else listener.failure(problem);
                    }
                });
            }
        }).start();
    }
    private static final class Result { int status; Object data; }
    private static Result exchange(String server, String method, String path, Hashtable body, String token) throws Exception {
        HttpConnection connection = null; InputStream input = null; OutputStream output = null;
        try {
            connection = (HttpConnection)Connector.open(server + "/api/v1" + path,Connector.READ_WRITE,true);
            connection.setRequestMethod(method);
            connection.setRequestProperty("Accept","application/json");
            if (token.length() > 0) connection.setRequestProperty("Authorization","Bearer " + token);
            if (body != null) {
                byte[] bytes = Json.encode(body).getBytes("UTF-8");
                connection.setRequestProperty("Content-Type","application/json; charset=utf-8");
                output = connection.openOutputStream(); output.write(bytes); output.close(); output = null;
            }
            Result result = new Result(); result.status = connection.getResponseCode();
            // Reject any redirect exposed by the device's HTTP implementation.
            if (result.status >= 300 && result.status < 400) throw new Exception("Redirection serveur refusee");
            if (result.status == 204) return result;
            try { input = connection.openInputStream(); }
            catch (IOException ex) {
                // MicroEmulator throws on 4xx instead of exposing the error stream.
                // Preserve the HTTP status so expired-token refresh still works.
                if (result.status < 400) throw ex;
                Hashtable error = Json.object(); error.put("detail","Requete refusee par le serveur");
                result.data = error; return result;
            }
            ByteArrayOutputStream bytes = new ByteArrayOutputStream();
            byte[] buffer = new byte[1024]; int length;
            while ((length = input.read(buffer)) != -1) {
                if (bytes.size()+length > 262144) throw new Exception("Reponse trop volumineuse. Cache conserve.");
                bytes.write(buffer,0,length);
            }
            String text = new String(bytes.toByteArray(),"UTF-8");
            result.data = text.length() == 0 ? Json.NULL : Json.parse(text);
            return result;
        } finally {
            if (input != null) try { input.close(); } catch (Exception ignored) { }
            if (output != null) try { output.close(); } catch (Exception ignored) { }
            if (connection != null) try { connection.close(); } catch (Exception ignored) { }
        }
    }
}
