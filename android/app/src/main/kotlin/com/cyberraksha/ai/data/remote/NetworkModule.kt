package com.cyberraksha.ai.data.remote

import android.os.Build
import android.util.Log
import com.cyberraksha.ai.core.AppPreferences
import okhttp3.Interceptor
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.net.URI
import java.util.concurrent.TimeUnit

object NetworkModule {

    private const val TAG = "CyberRakshaNet"

    @Volatile
    private var instance: CyberRakshaApiService? = null

    @Volatile
    private var currentBaseUrl: String? = null

    @Volatile
    private var deviceToken: String? = null

    @Volatile
    private var cachedOkHttpClient: OkHttpClient? = null

    fun setDeviceToken(token: String?) {
        deviceToken = token
    }

    /**
     * Sanitizes and normalizes any user or persisted input into a strictly valid
     * origin base URL: scheme + host (+ optional port).
     *
     * Strips accidental trailing path fragments such as /api/v1, /api/v1/health,
     * /health, whitespace, or trailing slashes that break Retrofit endpoint concatenation.
     */
    fun normalizeBaseUrl(input: String?): String {
        val raw = input?.trim()
        if (raw.isNullOrBlank() || raw.contains("10.0.2.2") || raw.contains("localhost") || raw.contains("127.0.0.1")) {
            return AppPreferences.DEFAULT_BACKEND_URL
        }
        val withScheme = if (!raw.startsWith("http://") && !raw.startsWith("https://")) {
            "https://$raw"
        } else {
            raw
        }
        return try {
            val uri = URI(withScheme)
            val scheme = uri.scheme?.lowercase() ?: "https"
            val host = uri.host ?: uri.authority ?: return AppPreferences.DEFAULT_BACKEND_URL
            val port = if (uri.port != -1) ":${uri.port}" else ""
            "$scheme://$host$port"
        } catch (e: Exception) {
            Log.w(TAG, "Failed to parse URL '$input', falling back to default", e)
            AppPreferences.DEFAULT_BACKEND_URL
        }
    }

    fun getOkHttpClient(): OkHttpClient {
        return cachedOkHttpClient ?: synchronized(this) {
            cachedOkHttpClient ?: buildOkHttpClient().also { cachedOkHttpClient = it }
        }
    }

    private fun buildOkHttpClient(): OkHttpClient {
        val logging = HttpLoggingInterceptor { message ->
            Log.d(TAG, message)
        }.apply {
            level = HttpLoggingInterceptor.Level.BASIC
        }

        return OkHttpClient.Builder()
            .retryOnConnectionFailure(true)
            .connectTimeout(60, TimeUnit.SECONDS)
            .readTimeout(60, TimeUnit.SECONDS)
            .writeTimeout(30, TimeUnit.SECONDS)
            .addInterceptor(logging)
            .addInterceptor(Interceptor { chain ->
                val original = chain.request()
                val builder = original.newBuilder()
                    .header(
                        "User-Agent",
                        "CyberRaksha-Android/1.0.0 (Linux; Android ${Build.VERSION.RELEASE}; ${Build.MANUFACTURER} ${Build.MODEL})"
                    )
                    .header("Accept", "application/json")
                deviceToken?.let { token ->
                    builder.addHeader("X-Device-Token", token)
                }
                chain.proceed(builder.build())
            })
            .build()
    }

    // Returns a singleton API service, dynamically updating if the normalized baseUrl changes.
    fun getApiService(baseUrl: String = AppPreferences.DEFAULT_BACKEND_URL): CyberRakshaApiService {
        val normalized = normalizeBaseUrl(baseUrl)
        val cleanUrl = normalized.trimEnd('/') + "/"
        val existing = instance
        if (existing != null && currentBaseUrl == cleanUrl) {
            return existing
        }
        return synchronized(this) {
            if (instance != null && currentBaseUrl == cleanUrl) {
                instance!!
            } else {
                currentBaseUrl = cleanUrl
                createApiService(cleanUrl).also { instance = it }
            }
        }
    }

    fun createApiService(baseUrl: String): CyberRakshaApiService {
        val normalized = normalizeBaseUrl(baseUrl)
        val cleanUrl = normalized.trimEnd('/') + "/"
        Log.i(TAG, "Creating Retrofit instance with base URL: $cleanUrl")

        return Retrofit.Builder()
            .baseUrl(cleanUrl)
            .client(getOkHttpClient())
            .addConverterFactory(GsonConverterFactory.create())
            .build()
            .create(CyberRakshaApiService::class.java)
    }
}

