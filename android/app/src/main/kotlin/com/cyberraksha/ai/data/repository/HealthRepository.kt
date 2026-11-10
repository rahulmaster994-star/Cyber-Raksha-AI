package com.cyberraksha.ai.data.repository

import com.cyberraksha.ai.data.remote.CyberRakshaApiService
import com.cyberraksha.ai.data.remote.HealthResponse

class HealthRepository(private val api: CyberRakshaApiService) {

    /** Returns true when backend is reachable and status is "ok". */
    suspend fun isBackendHealthy(): Boolean = runCatching {
        val response = api.getHealth()
        response.isSuccessful && response.body()?.status?.lowercase() == "ok"
    }.getOrDefault(false)

    suspend fun getHealth(): Result<HealthResponse> = runCatching {
        val response = api.getHealth()
        if (response.isSuccessful) Result.Success(response.body()!!)
        else Result.Error("HTTP ${response.code()}", response.code())
    }.getOrElse { Result.Error(it.message ?: "Network error") }
}

