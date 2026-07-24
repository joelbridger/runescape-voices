package com.jamesondaines.gielinorvoices;

import com.google.gson.Gson;
import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.atomic.AtomicLong;
import lombok.extern.slf4j.Slf4j;
import net.runelite.client.RuneLite;

@Slf4j
final class VoiceServiceClient
{
	static final URI DEFAULT_BASE_URI = URI.create("http://127.0.0.1:17855");
	private static final Duration CONNECT_TIMEOUT = Duration.ofSeconds(2);
	private static final Duration REQUEST_TIMEOUT = Duration.ofSeconds(4);
	private static final long WARNING_INTERVAL_NANOS = Duration.ofSeconds(30).toNanos();

	private final HttpClient httpClient;
	private final Gson gson;
	private final URI baseUri;
	private final AtomicLong lastWarning = new AtomicLong(Long.MIN_VALUE);
	private volatile String token;

	VoiceServiceClient()
	{
		this(DEFAULT_BASE_URI, HttpClient.newBuilder().connectTimeout(CONNECT_TIMEOUT).build(), new Gson());
	}

	VoiceServiceClient(URI baseUri, HttpClient httpClient, Gson gson)
	{
		this.baseUri = baseUri;
		this.httpClient = httpClient;
		this.gson = gson;
	}

	boolean loadToken()
	{
		Path tokenPath = RuneLite.RUNELITE_DIR.toPath()
			.resolve("gielinor-voices")
			.resolve("token");
		try
		{
			String loaded = Files.readString(tokenPath, StandardCharsets.UTF_8).trim();
			if (loaded.length() < 32 || loaded.length() > 256)
			{
				log.warn("Gielinor Voices token has an invalid length");
				token = null;
				return false;
			}
			token = loaded;
			return true;
		}
		catch (IOException exception)
		{
			log.warn("Gielinor Voices token is unavailable at {}", tokenPath);
			token = null;
			return false;
		}
	}

	CompletableFuture<Boolean> health()
	{
		HttpRequest request = HttpRequest.newBuilder(baseUri.resolve("/health"))
			.timeout(REQUEST_TIMEOUT)
			.GET()
			.build();
		return httpClient.sendAsync(request, HttpResponse.BodyHandlers.discarding())
			.thenApply(response -> response.statusCode() == 200)
			.exceptionally(exception -> false);
	}

	void speak(SpeechPayload payload)
	{
		sendJson("/v1/speak", gson.toJson(payload));
	}

	void cancel()
	{
		sendJson("/v1/cancel", "{}");
	}

	private void sendJson(String path, String json)
	{
		String currentToken = token;
		if (currentToken == null)
		{
			return;
		}
		HttpRequest request = HttpRequest.newBuilder(baseUri.resolve(path))
			.timeout(REQUEST_TIMEOUT)
			.header("Authorization", "Bearer " + currentToken)
			.header("Content-Type", "application/json")
			.POST(HttpRequest.BodyPublishers.ofString(json, StandardCharsets.UTF_8))
			.build();
		httpClient.sendAsync(request, HttpResponse.BodyHandlers.discarding())
			.whenComplete((response, error) ->
			{
				if (error != null || response.statusCode() < 200 || response.statusCode() >= 300)
				{
					warnUnavailable(error, response == null ? 0 : response.statusCode());
				}
			});
	}

	private void warnUnavailable(Throwable error, int status)
	{
		long now = System.nanoTime();
		long previous = lastWarning.get();
		if (previous != Long.MIN_VALUE && now - previous < WARNING_INTERVAL_NANOS)
		{
			return;
		}
		if (!lastWarning.compareAndSet(previous, now))
		{
			return;
		}
		if (error == null)
		{
			log.warn("Gielinor Voices service rejected a request with status {}", status);
		}
		else
		{
			log.warn("Gielinor Voices service is unavailable: {}", error.getMessage());
		}
	}
}

