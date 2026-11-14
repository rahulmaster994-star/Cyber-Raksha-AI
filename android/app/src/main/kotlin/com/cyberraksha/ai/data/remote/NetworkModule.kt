package com.cyberraksha.ai.data.remote

import com.cyberraksha.ai.core.AppPreferences
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit

object NetworkModule {

    @Volatile
    private var instance: CyberRakshaApiService? = null

    @Volatile
    private var currentBaseUrl: String? = null

    @Volatile
    private var deviceToken: String? = null

    fun setDeviceToken(token: String?) {
        deviceToken = token
    }

    // FIX: Default URL is now the production Render backend.
    // The old "http://10.0.2.2:8000" only works inside Android Studio emulator
    // and fails on all physical devices with a "Cannot connect" error.
    // Dynamically reconfigures if a different baseUrl is provided.
    fun getApiService(baseUrl: String = AppPreferences.DEFAULT_BACKEND_URL): CyberRakshaApiService {
        val cleanUrl = baseUrl.trimEnd('/') + "/"
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
        val client = OkHttpClient.Builder()
            // FIX: Increased connect timeout from 15s to 60s to handle Render free-tier
            // cold starts (up to ~50s spin-up after inactivity). Without this, the app
            // times out before the backend wakes, producing "Cannot connect" on first launch.
            .connectTimeout(60, TimeUnit.SECONDS)
            .readTimeout(60, TimeUnit.SECONDS)
            .writeTimeout(30, TimeUnit.SECONDS)
            // Privacy hardening: log only HEADERS, never print raw SMS message body to logcat
            .addInterceptor(HttpLoggingInterceptor().apply {
                level = HttpLoggingInterceptor.Level.HEADERS
            })
            .addInterceptor { chain ->
                val original = chain.request()
                val builder = original.newBuilder()
                deviceToken?.let { token ->
                    builder.addHeader("X-Device-Token", token)
                }
                chain.proceed(builder.build())
            }
            .build()

        return Retrofit.Builder()
            .baseUrl(baseUrl.trimEnd('/') + "/")
            .client(client)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
            .create(CyberRakshaApiService::class.java)
    }
}

