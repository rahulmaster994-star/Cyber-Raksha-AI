package com.cyberraksha.ai.domain.usecase

import com.cyberraksha.ai.core.AppPreferences
import com.cyberraksha.ai.data.repository.DeviceRepository
import com.cyberraksha.ai.data.repository.Result
import kotlinx.coroutines.flow.firstOrNull
import java.util.UUID

class RegisterDeviceUseCase(
    private val prefs: AppPreferences,
    private val deviceRepository: DeviceRepository
) {
    /**
     * Returns the device_id on success, or throws on failure.
     * - If a deviceId already exists in prefs, that UUID is reused (idempotent).
     * - Generates a new UUID only on first registration.
     * - [deviceName] defaults to the Android model name if not supplied.
     */
    suspend operator fun invoke(deviceName: String): Result<String> {
        val existingId = prefs.deviceId.firstOrNull()
        val deviceId   = existingId ?: UUID.randomUUID().toString()

        return when (val result = deviceRepository.registerDevice(deviceId, deviceName)) {
            is Result.Success -> Result.Success(result.data.deviceId)
            is Result.Error   -> Result.Error(result.message, result.code)
        }
    }
}

