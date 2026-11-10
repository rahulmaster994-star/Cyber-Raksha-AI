package com.cyberraksha.ai.data.repository

import com.cyberraksha.ai.core.AppPreferences
import com.cyberraksha.ai.data.local.SmsAnalysisDao
import com.cyberraksha.ai.data.remote.CyberRakshaApiService
import com.cyberraksha.ai.data.remote.MessageAnalysisResponse
import com.cyberraksha.ai.data.remote.NumberCheckResponse
import com.cyberraksha.ai.data.remote.ProtectionStatusResponse
import io.mockk.coEvery
import io.mockk.coVerify
import io.mockk.mockk
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.runBlocking
import okhttp3.ResponseBody.Companion.toResponseBody
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import retrofit2.Response

class MobileProtectionRepositoryTest {

    private lateinit var api: CyberRakshaApiService
    private lateinit var dao: SmsAnalysisDao
    private lateinit var prefs: AppPreferences
    private lateinit var repository: MobileProtectionRepository

    @Before
    fun setup() {
        api = mockk()
        dao = mockk(relaxed = true)
        prefs = mockk {
            coEvery { deviceId } returns flowOf("test-device-uuid")
        }
        repository = MobileProtectionRepository(api, dao, prefs)
    }

    @Test
    fun `analyzeMessage returns Success and inserts into Room`() = runBlocking {
        val fakeResponse = MessageAnalysisResponse(
            messageHash = "hash123",
            riskScore = 85.0f,
            riskLevel = "CRITICAL",
            fraudCategory = "BANKING_FRAUD",
            detectionReasons = listOf("Fake KYC link"),
            extractedUrls = listOf("http://fake.xyz"),
            urlThreats = emptyList(),
            recommendedAction = "Do not click link",
            analyzedAt = "2026-11-09T12:00:00Z"
        )
        coEvery { api.analyzeMessage(any()) } returns Response.success(fakeResponse)

        val result = repository.analyzeMessage("Your account is blocked", "SBI")

        assertTrue(result is Result.Success)
        val data = (result as Result.Success).data
        assertEquals("CRITICAL", data.riskLevel)
        assertEquals("BANKING_FRAUD", data.fraudCategory)
        coVerify(exactly = 1) { dao.insertAnalysis(any()) }
    }

    @Test
    fun `analyzeMessage network error falls back to offline heuristic`() = runBlocking {
        coEvery { api.analyzeMessage(any()) } returns Response.error(500, "Error".toResponseBody())

        val result = repository.analyzeMessage("Please share OTP to verify your account", null)

        assertTrue(result is Result.Success)
        val data = (result as Result.Success).data
        assertEquals("OTP_FRAUD", data.fraudCategory)
        assertEquals("HIGH", data.riskLevel)
        coVerify(exactly = 1) { dao.insertAnalysis(any()) }
    }

    @Test
    fun `checkNumber returns caller reputation`() = runBlocking {
        val fakeNumberResponse = NumberCheckResponse(
            phoneNumber = "+919876543210",
            normalizedNumber = "+919876543210",
            riskLevel = "CRITICAL",
            fraudCategory = "DIGITAL_ARREST",
            reportCount = 10,
            confidenceScore = 0.95f,
            source = "GOV_DATABASE",
            notes = "Impersonating police",
            recommendedAction = "Decline call",
            checkedAt = "2026-11-09T12:00:00Z"
        )
        coEvery { api.checkNumber(any()) } returns Response.success(fakeNumberResponse)

        val result = repository.checkNumber("+919876543210")

        assertTrue(result is Result.Success)
        val data = (result as Result.Success).data
        assertEquals("CRITICAL", data.riskLevel)
        assertEquals(10, data.reportCount)
    }

    @Test
    fun `getProtectionStatus returns active modules status`() = runBlocking {
        val fakeStatus = ProtectionStatusResponse(
            deviceId = "test-device-uuid",
            smsProtection = "ACTIVE",
            callProtection = "ACTIVE",
            databaseSignaturesCount = 42,
            phoneReputationEntries = 15,
            lastSync = "2026-11-09T10:00:00Z"
        )
        coEvery { api.getProtectionStatus(any()) } returns Response.success(fakeStatus)

        val result = repository.getProtectionStatus()

        assertTrue(result is Result.Success)
        val data = (result as Result.Success).data
        assertEquals("ACTIVE", data.smsProtection)
        assertEquals(42, data.databaseSignaturesCount)
    }
}

