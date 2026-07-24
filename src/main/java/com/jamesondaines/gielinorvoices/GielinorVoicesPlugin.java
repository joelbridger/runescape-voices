package com.jamesondaines.gielinorvoices;

import com.google.inject.Provides;
import java.util.Objects;
import java.util.concurrent.atomic.AtomicLong;
import javax.inject.Inject;
import lombok.extern.slf4j.Slf4j;
import net.runelite.api.ChatMessageType;
import net.runelite.api.Client;
import net.runelite.api.NPC;
import net.runelite.api.events.OverheadTextChanged;
import net.runelite.api.events.WidgetClosed;
import net.runelite.api.events.WidgetLoaded;
import net.runelite.api.gameval.InterfaceID;
import net.runelite.api.widgets.Widget;
import net.runelite.client.callback.ClientThread;
import net.runelite.client.config.ConfigManager;
import net.runelite.client.eventbus.Subscribe;
import net.runelite.client.plugins.Plugin;
import net.runelite.client.plugins.PluginDescriptor;
import net.runelite.client.util.Text;

@Slf4j
@PluginDescriptor(
	name = "Gielinor Voices",
	description = "Private local AI voice acting for visible RuneScape dialogue",
	tags = {"voice", "dialogue", "accessibility", "tts"}
)
public class GielinorVoicesPlugin extends Plugin
{
	private static final int NPC_DIALOGUE_GROUP = InterfaceID.ChatLeft.UNIVERSE >>> 16;
	private static final int PLAYER_DIALOGUE_GROUP = InterfaceID.ChatRight.UNIVERSE >>> 16;

	@Inject
	private Client client;

	@Inject
	private ClientThread clientThread;

	@Inject
	private GielinorVoicesConfig config;

	private final VoiceServiceClient service = new VoiceServiceClient();
	private final AtomicLong sequence = new AtomicLong();
	private volatile String lastFingerprint = "";

	@Provides
	GielinorVoicesConfig provideConfig(ConfigManager configManager)
	{
		return configManager.getConfig(GielinorVoicesConfig.class);
	}

	@Override
	protected void startUp()
	{
		boolean tokenReady = service.loadToken();
		if (!tokenReady)
		{
			showMessage("Gielinor Voices needs its local voice-service installer.");
			return;
		}
		service.health().thenAccept(healthy -> clientThread.invokeLater(() ->
			showMessage(healthy
				? "Gielinor Voices is ready."
				: "Gielinor Voices is waiting for its local voice service.")));
	}

	@Override
	protected void shutDown()
	{
		service.cancel();
		lastFingerprint = "";
	}

	@Subscribe(priority = -100)
	public void onWidgetLoaded(WidgetLoaded event)
	{
		if (!config.enabled())
		{
			return;
		}
		if (event.getGroupId() == NPC_DIALOGUE_GROUP && config.npcDialogue())
		{
			clientThread.invokeAtTickEnd(this::speakNpcDialogue);
		}
		else if (event.getGroupId() == PLAYER_DIALOGUE_GROUP && config.playerDialogue())
		{
			clientThread.invokeAtTickEnd(this::speakPlayerDialogue);
		}
	}

	@Subscribe
	public void onWidgetClosed(WidgetClosed event)
	{
		if (!config.enabled() || !config.cutOffOnSkip())
		{
			return;
		}
		int group = event.getGroupId();
		if (group == NPC_DIALOGUE_GROUP || group == PLAYER_DIALOGUE_GROUP)
		{
			service.cancel();
			lastFingerprint = "";
		}
	}

	@Subscribe(priority = -1)
	public void onOverheadTextChanged(OverheadTextChanged event)
	{
		if (!config.enabled() || !config.npcOverhead() || !(event.getActor() instanceof NPC))
		{
			return;
		}
		NPC npc = (NPC) event.getActor();
		String name = cleanName(npc.getName(), "Unknown NPC");
		String text = cleanText(event.getOverheadText());
		if (text.isEmpty())
		{
			return;
		}
		speak(SpeakerKeys.npc(name, npc.getId()), name, text, "npc-overhead");
	}

	private void speakNpcDialogue()
	{
		Widget textWidget = client.getWidget(InterfaceID.ChatLeft.TEXT);
		Widget nameWidget = client.getWidget(InterfaceID.ChatLeft.NAME);
		Widget headWidget = client.getWidget(InterfaceID.ChatLeft.HEAD);
		if (textWidget == null || nameWidget == null || headWidget == null)
		{
			return;
		}
		String text = cleanText(textWidget.getText());
		String name = cleanName(nameWidget.getText(), "Unknown NPC");
		if (!text.isEmpty())
		{
			speak(SpeakerKeys.npc(name, headWidget.getModelId()), name, text, "npc-dialogue");
		}
	}

	private void speakPlayerDialogue()
	{
		Widget textWidget = client.getWidget(InterfaceID.ChatRight.TEXT);
		if (textWidget == null)
		{
			return;
		}
		String text = cleanText(textWidget.getText());
		if (!text.isEmpty())
		{
			speak(SpeakerKeys.localPlayer(), "Player", text, "player-dialogue");
		}
	}

	private void speak(String speakerKey, String speakerName, String text, String kind)
	{
		String fingerprint = speakerKey + '\u0000' + text;
		if (Objects.equals(lastFingerprint, fingerprint))
		{
			return;
		}
		lastFingerprint = fingerprint;
		service.speak(new SpeechPayload(
			speakerKey,
			speakerName,
			text,
			kind,
			sequence.incrementAndGet(),
			config.volume() / 100.0));
	}

	static String cleanText(String value)
	{
		if (value == null)
		{
			return "";
		}
		return Text.sanitizeMultilineText(value).trim();
	}

	private static String cleanName(String value, String fallback)
	{
		if (value == null)
		{
			return fallback;
		}
		String clean = Text.removeTags(value).trim();
		return clean.isEmpty() ? fallback : clean;
	}

	private void showMessage(String message)
	{
		client.addChatMessage(ChatMessageType.GAMEMESSAGE, "", message, null);
	}
}
