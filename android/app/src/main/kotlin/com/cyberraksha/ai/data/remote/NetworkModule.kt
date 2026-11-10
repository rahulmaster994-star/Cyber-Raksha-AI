package com.cyberraksha.ai.data.remote

import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit

object NetworkModule {

    @Volatile
    private var instance: CyberRakshaApiService? = null

    @Volatile
    private var deviceToken: String? = null

    fun setDeviceToken(token: String?) {
        deviceToken = token
    }

    fun getApiService(baseUrl: String = "http://10.0.2.2:8000"): CyberRakshaApiService {
        return instance ?: synchronized(this) {
            instance ?: createApiService(baseUrl).also { instance = it }
        }
    }

    fun createApiService(baseUrl: String): CyberRakshaApiService {
        val client = OkHttpClient.Builder()
            .connectTimeout(15, TimeUnit.SECONDS)
            .readTimeout(30, TimeUnit.SECONDS)
            .writeTimeout(15, TimeUnit.SECONDS)
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

