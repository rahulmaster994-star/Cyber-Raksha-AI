package com.cyberraksha.ai.domain.usecase

import com.cyberraksha.ai.core.AppPreferences
import com.cyberraksha.ai.data.remote.DeviceRegistrationResponse
import com.cyberraksha.ai.data.remote.ProtectionModulesStatus
import com.cyberraksha.ai.data.repository.DeviceRepository
import com.cyberraksha.ai.data.repository.Result
import io.mockk.coEvery
import io.mockk.mockk
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import java.util.UUID

class RegisterDeviceUseCaseTest {

    private lateinit var prefs: AppPreferences
    private lateinit var deviceRepository: DeviceRepository
    private lateinit var useCase: RegisterDeviceUseCase

    @Before
    fun setup() {
        prefs = mockk(relaxed = true)
        deviceRepository = mockk(relaxed = true)
        useCase = RegisterDeviceUseCase(prefs, deviceRepository)
    }

    @Test
    fun `when no deviceId stored, generates new UUID and calls repository`() = runBlocking {
        coEvery { prefs.deviceId } returns flowOf(null)
        coEvery { deviceRepository.registerDevice(any(), any()) } answers {
            val id = firstArg<String>()
            val name = secondArg<String>()
            Result.Success(
                DeviceRegistrationResponse(
                    deviceId = id,
                    deviceName = name,
                    status = "ACTIVE",
                    registeredAt = "2026-11-09T12:00:00Z",
                    protectionModules = ProtectionModulesStatus()
                )
            )
        }

        val result = useCase("Pixel 8")
        assertTrue(result is Result.Success)
        val registeredId = (result as Result.Success).data
        // Must be a valid UUID format
        val parsed = UUID.fromString(registeredId)
        assertTrue(parsed != null)
    }

    @Test
    fun `when deviceId already exists, reuses existing UUID`() = runBlocking {
        val existingId = "11112222-3333-4444-5555-666677778888"
        coEvery { prefs.deviceId } returns flowOf(existingId)
        coEvery { deviceRepository.registerDevice(existingId, "Pixel 8") } returns Result.Success(
            DeviceRegistrationResponse(
                deviceId = existingId,
                deviceName = "Pixel 8",
                status = "ACTIVE",
                registeredAt = "2026-11-09T12:00:00Z",
                protectionModules = ProtectionModulesStatus()
            )
        )

        val result = useCase("Pixel 8")
        assertTrue(result is Result.Success)
        assertEquals(existingId, (result as Result.Success).data)
    }
}
