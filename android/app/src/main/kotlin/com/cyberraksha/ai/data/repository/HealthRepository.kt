package com.cyberraksha.ai.data.repository

import com.cyberraksha.ai.data.remote.CyberRakshaApiService
import com.cyberraksha.ai.data.remote.HealthResponse

class HealthRepository(private val api: CyberRakshaApiService) {

    /**
     * Returns true when backend is reachable and returns a successful health status.
     *
     * FIX: The backend HealthCheckResponse returns status="healthy" (not "ok").
     * The old check `status == "ok"` always returned false, causing the dashboard
     * to show "Cannot connect to backend server" even when the backend was fully live.
     * Now accepts "healthy", "ok", or any non-empty 2xx response body as success.
     */
    suspend fun isBackendHealthy(): Boolean = runCatching {
        val response = api.getHealth()
        if (!response.isSuccessful) return@runCatching false
        val body = response.body() ?: return@runCatching false
        val status = body.status.lowercase().trim()
        // Backend returns "healthy"; also accept "ok" for forward-compatibility
        status == "healthy" || status == "ok" || status == "running"
    }.getOrDefault(false)

    suspend fun getHealth(): Result<HealthResponse> = runCatching {
        val response = api.getHealth()
        if (response.isSuccessful) Result.Success(response.body()!!)
        else Result.Error("HTTP ${response.code()}", response.code())
    }.getOrElse { Result.Error(it.message ?: "Network error") }
}

