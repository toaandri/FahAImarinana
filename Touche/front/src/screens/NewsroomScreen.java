package screens;

import javax.microedition.lcdui.*;
import java.util.Hashtable;
import java.util.Vector;
import network.Api;
import network.Json;
import utils.ScreenManager;

public class NewsroomScreen extends ApiForm {
    private ChoiceGroup cases = new ChoiceGroup("Dossiers",Choice.POPUP);
    private Vector records = new Vector();
    private int offset;
    private Command refresh = new Command("Actualiser",Command.SCREEN,1);
    private Command open = new Command("Ouvrir dossier",Command.OK,1);
    private Command create = new Command("Nouveau dossier",Command.SCREEN,2);
    private Command next = new Command("Page suivante",Command.SCREEN,6);
    private Command previous = new Command("Page precedente",Command.SCREEN,7);
    private Command publications = new Command("Publications",Command.SCREEN,3);
    private Command assistant = new Command("Assistant",Command.SCREEN,4);
    private Command sms = new Command("Consultation SMS",Command.SCREEN,5);
    private Command source = new Command("Ajouter source de veille",Command.SCREEN,6);
    private Command logout = new Command("Deconnexion",Command.EXIT,9);
    public NewsroomScreen() {
        super("Redaction FA AI MARINANA"); removeCommand(home);
        addCommand(publications); addCommand(sms);
        if (!Api.authenticated()) {
            addCommand(logout); status.setText("Consultation publique. Connexion requise pour la redaction."); return;
        }
        addCommand(logout);
        if (Api.can("research.run")) addCommand(assistant);
        if (Api.can("connectors.manage")) addCommand(source);
        if (Api.can("cases.create")) addCommand(create);
        if (Api.can("cases.read")) {
            append(cases); addCommand(open); addCommand(refresh); addCommand(next); addCommand(previous); load();
        } else status.setText("Vos permissions ne donnent pas acces aux dossiers prives.");
    }
    private void load() {
        call("GET","/cases?limit=20&offset=" + offset,null,new Api.Listener() {
            public void success(Object data) {
                records = (Vector)data; cases.deleteAll();
                for (int i=0;i<records.size();i++) {
                    Hashtable item = (Hashtable)records.elementAt(i);
                    cases.append(Json.str(item,"title") + " [" + Json.str(item,"status") + "]",null);
                }
                status.setText(records.size() == 0 ? "Aucun dossier sur cette page." : "Dossiers " + (offset+1) + " a " + (offset+records.size()));
            }
            public void failure(String problem) { }
        });
    }
    protected void act(Command command) {
        if (command == publications) ScreenManager.show(new PublicationScreen());
        else if (command == assistant) ScreenManager.show(new ChatScreen());
        else if (command == sms) ScreenManager.show(new SmsNewsScreen());
        else if (command == refresh) load();
        else if (command == next) { if (records.size() == 20) { offset += 20; load(); } }
        else if (command == previous) { offset = Math.max(0,offset-20); load(); }
        else if (command == open && cases.getSelectedIndex() >= 0) {
            ScreenManager.show(new CaseScreen(Json.str((Hashtable)records.elementAt(cases.getSelectedIndex()),"id")));
        } else if (command == create) {
            ScreenManager.show(new EntryForm("Nouveau dossier","/cases",this,new Api.Listener() {
                public void success(Object data) { ScreenManager.show(new CaseScreen(Json.str((Hashtable)data,"id"))); }
                public void failure(String problem) { }
            }).field("title","Titre",250,false).field("description","Description",5000,false));
        } else if (command == source) {
            ScreenManager.show(new EntryForm("Source de veille","/sources",this,new Api.Listener() {
                public void success(Object data) { ScreenManager.show(new NewsroomScreen()); }
                public void failure(String problem) { }
            }).fixed("type","Web").field("nom","Nom",150,false).field("url","URL originale",500,false));
        } else if (command == logout) {
            if (!Api.authenticated()) { Api.clear(); ScreenManager.show(new LoginScreen()); return; }
            call("POST","/auth/logout",null,new Api.Listener() {
                public void success(Object data) { Api.clear(); ScreenManager.show(new LoginScreen()); }
                public void failure(String problem) { }
            });
        }
    }
}
