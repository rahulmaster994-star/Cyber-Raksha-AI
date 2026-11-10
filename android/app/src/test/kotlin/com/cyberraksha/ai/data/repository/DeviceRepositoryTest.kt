package com.cyberraksha.ai.data.repository

import com.cyberraksha.ai.core.AppPreferences
import com.cyberraksha.ai.data.remote.CyberRakshaApiService
import com.cyberraksha.ai.data.remote.DeviceRegistrationResponse
import com.cyberraksha.ai.data.remote.DeviceStatusResponse
import com.cyberraksha.ai.data.remote.ProtectionModulesStatus
import io.mockk.coEvery
import io.mockk.mockk
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.runBlocking
import okhttp3.ResponseBody.Companion.toResponseBody
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import retrofit2.Response

class DeviceRepositoryTest {

    private lateinit var api: CyberRakshaApiService
    private lateinit var prefs: AppPreferences
    private lateinit var repository: DeviceRepository

    @Before
    fun setup() {
        api = mockk()
        prefs = mockk(relaxed = true)
        repository = DeviceRepository(api, prefs)
    }

    @Test
    fun `registerDevice success returns Result_Success and saves id and name`() = runBlocking {
        val fakeResponse = DeviceRegistrationResponse(
            deviceId = "test-uuid-1234",
            deviceName = "Test Device",
            status = "ACTIVE",
            registeredAt = "2026-11-09T10:00:00Z",
            protectionModules = ProtectionModulesStatus()
        )
        coEvery { api.registerDevice(any()) } returns Response.success(fakeResponse)

        val result = repository.registerDevice("test-uuid-1234", "Test Device")

        assertTrue(result is Result.Success)
        assertEquals("test-uuid-1234", (result as Result.Success).data.deviceId)
    }

    @Test
    fun `registerDevice error returns Result_Error`() = runBlocking {
        coEvery { api.registerDevice(any()) } returns Response.error(
            422,
            "Unprocessable Entity".toResponseBody()
        )

        val result = repository.registerDevice("invalid-id", "Test Device")

        assertTrue(result is Result.Error)
        assertEquals(422, (result as Result.Error).code)
    }

    @Test
    fun `getDeviceStatus returns error when no deviceId registered in prefs`() = runBlocking {
        coEvery { prefs.deviceId } returns flowOf(null)

        val result = repository.getDeviceStatus()

        assertTrue(result is Result.Error)
        assertEquals("Device not registered", (result as Result.Error).message)
    }

    @Test
    fun `getDeviceStatus success returns Result_Success`() = runBlocking {
        val devId = "12345678-1234-1234-1234-123456789012"
        coEvery { prefs.deviceId } returns flowOf(devId)
        val fakeStatus = DeviceStatusResponse(
            deviceId = devId,
            deviceName = "Pixel 8",
            status = "ACTIVE",
            securityPosture = "PROTECTED",
            lastSeenAt = "2026-11-09T10:05:00Z",
            registeredAt = "2026-11-09T10:00:00Z",
            protectionModules = ProtectionModulesStatus()
        )
        coEvery { api.getDeviceStatus(devId) } returns Response.success(fakeStatus)

        val result = repository.getDeviceStatus()

        assertTrue(result is Result.Success)
        assertEquals("PROTECTED", (result as Result.Success).data.securityPosture)
    }
}

