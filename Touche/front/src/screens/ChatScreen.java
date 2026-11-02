package screens;

import javax.microedition.lcdui.*;
import java.util.Hashtable;
import network.Api;
import network.Json;

/** The existing Copilot explicitly reports local or configured provider results. */
public class ChatScreen extends ApiForm {
    private TextField question = new TextField("Question","",500,TextField.ANY);
    private StringItem answer = new StringItem("Resultat","");
    private Command send = new Command("Rechercher",Command.OK,1);
    public ChatScreen() {
        super("Assistant documentaire"); append(question); append(answer);
        if (Api.can("research.run")) addCommand(send);
        status.setText("Recherche locale dans les publications certifiees, ou Gemini si configure. Maharavo externe indisponible.");
    }
    protected void act(Command command) {
        if (command != send) return;
        Hashtable body = Json.object(); body.put("question",question.getString());
        call("POST","/copilot/research",body,new Api.Listener() {
            public void success(Object data) { answer.setText(Json.str((Hashtable)data,"reponse")); }
            public void failure(String problem) { }
        });
    }
}
