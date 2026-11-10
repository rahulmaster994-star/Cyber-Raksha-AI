package com.cyberraksha.ai.data.repository

import com.cyberraksha.ai.core.AppPreferences
import com.cyberraksha.ai.data.remote.CyberRakshaApiService
import com.cyberraksha.ai.data.remote.DeviceRegisterRequest
import com.cyberraksha.ai.data.remote.DeviceRegistrationResponse
import com.cyberraksha.ai.data.remote.DeviceStatusResponse
import com.cyberraksha.ai.data.remote.DeviceActivityListResponse
import com.cyberraksha.ai.data.remote.NetworkModule
import kotlinx.coroutines.flow.firstOrNull

sealed class Result<out T> {
    data class Success<T>(val data: T) : Result<T>()
    data class Error(val message: String, val code: Int? = null) : Result<Nothing>()
}

class DeviceRepository(
    private val api: CyberRakshaApiService,
    private val prefs: AppPreferences
) {

    /**
     * Restores the device token from DataStore into NetworkModule on cold start.
     * Must be called once on app startup before any authenticated API calls.
     */
    suspend fun restoreDeviceToken() {
        val token = prefs.deviceToken.firstOrNull()
        if (!token.isNullOrBlank()) {
            NetworkModule.setDeviceToken(token)
        }
    }

    suspend fun registerDevice(
        deviceId: String,
        deviceName: String
    ): Result<DeviceRegistrationResponse> = runCatching {
        val response = api.registerDevice(
            DeviceRegisterRequest(
                deviceId = deviceId,
                deviceName = deviceName,
                appVersion = "1.0.0"
            )
        )
        if (response.isSuccessful) {
            val body = response.body()!!
            prefs.saveDeviceId(body.deviceId)
            prefs.saveDeviceName(body.deviceName)
            // Persist and activate cryptographic device token
            body.deviceToken?.let { token ->
                prefs.saveDeviceToken(token)
                NetworkModule.setDeviceToken(token)
            }
            Result.Success(body)
        } else {
            Result.Error("Registration failed: ${response.code()}", response.code())
        }
    }.getOrElse { Result.Error(it.message ?: "Network error") }

    suspend fun getDeviceStatus(): Result<DeviceStatusResponse> = runCatching {
        val deviceId = prefs.deviceId.firstOrNull()
            ?: return@runCatching Result.Error("Device not registered")
        val response = api.getDeviceStatus(deviceId)
        if (response.isSuccessful) Result.Success(response.body()!!)
        else Result.Error("Status fetch failed: ${response.code()}", response.code())
    }.getOrElse { Result.Error(it.message ?: "Network error") }

    suspend fun getDeviceActivity(limit: Int = 20): Result<DeviceActivityListResponse> = runCatching {
        val deviceId = prefs.deviceId.firstOrNull()
            ?: return@runCatching Result.Error("Device not registered")
        val response = api.getDeviceActivity(deviceId, limit = limit)
        if (response.isSuccessful) Result.Success(response.body()!!)
        else Result.Error("Activity fetch failed: ${response.code()}", response.code())
    }.getOrElse { Result.Error(it.message ?: "Network error") }
}

