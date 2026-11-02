package screens;

import javax.microedition.lcdui.*;
import java.util.Hashtable;
import network.Api;
import network.Json;
import utils.ScreenManager;

/** Password login backed by revocable server sessions. No local access code. */
public class LoginScreen extends ApiForm {
    private TextField server = new TextField("Serveur HTTPS (HTTP local seulement)",Api.baseUrl,250,TextField.URL);
    private TextField email = new TextField("Email","",255,TextField.EMAILADDR);
    private TextField password = new TextField("Mot de passe","",128,TextField.PASSWORD);
    private Command login = new Command("Connexion",Command.OK,1);
    private Command publicFeed = new Command("Publications publiques",Command.SCREEN,2);
    public LoginScreen() {
        super("FA AI MARINANA"); removeCommand(home);
        append(server); append(email); append(password);
        addCommand(login); addCommand(publicFeed);
        status.setText("Compte sur invitation. Aucune cle API requise pour le parcours local.");
    }
    protected void act(Command command) {
        try { Api.configure(server.getString()); } catch (Exception ex) { status.setText(ex.getMessage()); return; }
        if (command == publicFeed) { ScreenManager.show(new PublicationScreen()); return; }
        if (command != login) return;
        Hashtable body = Json.object(); body.put("email",email.getString()); body.put("mot_de_passe",password.getString());
        call("POST","/auth/login",body,new Api.Listener() {
            public void success(Object data) {
                password.setString(""); Api.tokens((Hashtable)data);
                call("GET","/auth/me",null,new Api.Listener() {
                    public void success(Object profile) { Api.profile((Hashtable)profile); ScreenManager.show(new NewsroomScreen()); }
                    public void failure(String problem) { }
                });
            }
            public void failure(String problem) { }
        });
    }
}
