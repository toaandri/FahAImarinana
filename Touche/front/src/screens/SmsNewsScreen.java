package screens;

import javax.microedition.lcdui.*;
import java.util.Hashtable;
import network.Api;
import network.Json;

public class SmsNewsScreen extends ApiForm {
    private TextField phone = new TextField("Numero du demandeur","",30,TextField.PHONENUMBER);
    private TextField message = new TextField("Demande","",480,TextField.ANY);
    private StringItem answer = new StringItem("Reponse publiee","");
    private Command query = new Command("Consulter",Command.OK,1);
    public SmsNewsScreen() {
        super("Consultation SMS"); append(phone); append(message); append(answer); addCommand(query);
        status.setText("Consultation HTTP du service SMS. Aucun SMS operateur n'est envoye.");
    }
    protected void act(Command command) {
        if (command != query) return;
        Hashtable body = Json.object(); body.put("numero_expediteur",phone.getString()); body.put("message",message.getString());
        call("POST","/sms/citizen",body,new Api.Listener() {
            public void success(Object data) { answer.setText(Json.str((Hashtable)data,"message")); status.setText("Reponse recue. Aucun SMS envoye."); }
            public void failure(String problem) { }
        });
    }
}
