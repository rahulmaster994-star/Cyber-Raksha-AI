package com.cyberraksha.ai.data.repository

import com.cyberraksha.ai.core.AppPreferences
import com.cyberraksha.ai.data.remote.*
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

class KeypadProtectionRepositoryTest {

    private lateinit var api: CyberRakshaApiService
    private lateinit var prefs: AppPreferences
    private lateinit var repository: KeypadProtectionRepository

    @Before
    fun setup() {
        api = mockk()
        prefs = mockk()
        coEvery { prefs.userToken } returns flowOf("test-jwt-token")
        repository = KeypadProtectionRepository(api, prefs)
    }

    @Test
    fun `01 registerElderlyMember returns Success on 201 response`() = runBlocking {
        val fakeResponse = KeypadElderlyUserResponseDto(
            id = 1,
            guardianUserId = 10,
            fullName = "Ramesh Sharma",
            mobileNumber = "+919876543210",
            maskedMobileNumber = "+91******3210",
            relationship = "Father",
            deviceType = "Nokia 105",
            preferredLanguage = "hi",
            consentGiven = true,
            isActive = true,
            createdAt = "2026-11-20T12:00:00Z"
        )
        coEvery {
            api.registerKeypadElderlyMember(any(), any())
        } returns Response.success(fakeResponse)

        val req = KeypadElderlyUserCreateDto(
            fullName = "Ramesh Sharma",
            mobileNumber = "9876543210",
            relationship = "Father",
            deviceType = "Nokia 105",
            preferredLanguage = "hi",
            consentGiven = true
        )

        val result = repository.registerElderlyMember(req)
        assertTrue(result is Result.Success)
        val data = (result as Result.Success).data
        assertEquals("Ramesh Sharma", data.fullName)
        assertEquals("+91******3210", data.maskedMobileNumber)
    }

    @Test
    fun `02 getElderlyMembers returns list of protected dependents`() = runBlocking {
        val list = listOf(
            KeypadElderlyUserResponseDto(
                id = 1,
                guardianUserId = 10,
                fullName = "Ramesh Sharma",
                mobileNumber = "+919876543210",
                maskedMobileNumber = "+91******3210",
                relationship = "Father",
                deviceType = "Nokia 105",
                preferredLanguage = "hi",
                consentGiven = true,
                isActive = true,
                createdAt = "2026-11-20T12:00:00Z"
            )
        )
        coEvery { api.listKeypadElderlyMembers(any()) } returns Response.success(list)

        val result = repository.getElderlyMembers()
        assertTrue(result is Result.Success)
        assertEquals(1, (result as Result.Success).data.size)
    }

    @Test
    fun `03 removeElderlyMember returns Success on 200 response`() = runBlocking {
        coEvery { api.removeKeypadElderlyMember(any(), 1) } returns Response.success(mapOf("status" to "success"))

        val result = repository.removeElderlyMember(1)
        assertTrue(result is Result.Success)
        assertTrue((result as Result.Success).data)
    }

    @Test
    fun `04 checkSms returns risk analysis and honors non-automatic disclaimer`() = runBlocking {
        val fakeSmsResp = KeypadSmsCheckResponseDto(
            riskScore = 85.0,
            riskLevel = "HIGH",
            category = "DIGITAL_ARREST",
            matchedSignatures = listOf("GOV_IMPERSONATION_OR_ARREST_THREAT"),
            explanation = "High risk digital arrest scam detected.",
            recommendedAction = "Never share PIN or OTP.",
            goldenRule = "Never share credentials.",
            helpline = "Call 1930 immediately.",
            isAutomaticDetection = false,
            disclaimer = "Guardian-assisted analysis only."
        )
        coEvery { api.checkKeypadSms(any(), any()) } returns Response.success(fakeSmsResp)

        val req = KeypadSmsCheckRequestDto(
            message = "CBI warrant issued. Call immediately.",
            preferredLanguage = "en"
        )

        val result = repository.checkSms(req)
        assertTrue(result is Result.Success)
        val data = (result as Result.Success).data
        assertEquals("HIGH", data.riskLevel)
        assertEquals(false, data.isAutomaticDetection)
    }

    @Test
    fun `05 checkCall returns call reputation and preserves non-blocking status`() = runBlocking {
        val fakeCallResp = KeypadCallCheckResponseDto(
            phoneNumber = "9876500001",
            normalizedNumber = "+919876500001",
            riskLevel = "MEDIUM",
            riskScore = 35.0,
            fraudCategory = "DIGITAL_ARREST",
            reportCount = 1,
            isVerifiedAuthority = false,
            verificationStatus = "COMMUNITY_UNVERIFIED",
            explanation = "Single unverified community report.",
            recommendedAction = "Advise caution.",
            reportingHelpline = "1930 / Chakshu",
            isAutomaticBlocking = false,
            disclaimer = "Keypad phones do not support automated blocking."
        )
        coEvery { api.checkKeypadCall(any(), any()) } returns Response.success(fakeCallResp)

        val req = KeypadCallCheckRequestDto(phoneNumber = "9876500001")
        val result = repository.checkCall(req)
        assertTrue(result is Result.Success)
        val data = (result as Result.Success).data
        assertEquals("COMMUNITY_UNVERIFIED", data.verificationStatus)
        assertEquals(false, data.isAutomaticBlocking)
    }

    @Test
    fun `06 reportScamNumber returns Success on submission`() = runBlocking {
        val fakeReport = KeypadScamNumberReportResponseDto(
            id = 5,
            normalizedNumber = "+919876500001",
            status = "REPORTED",
            message = "Report recorded.",
            verificationStatus = "COMMUNITY_UNVERIFIED"
        )
        coEvery { api.reportKeypadScamNumber(any(), any()) } returns Response.success(fakeReport)

        val req = KeypadScamNumberReportRequestDto(
            phoneNumber = "9876500001",
            fraudCategory = "DIGITAL_ARREST"
        )
        val result = repository.reportScamNumber(req)
        assertTrue(result is Result.Success)
        assertEquals("+919876500001", (result as Result.Success).data.normalizedNumber)
    }

    @Test
    fun `07 getAlertSummary returns incident metrics`() = runBlocking {
        val fakeSummary = KeypadAlertSummaryResponseDto(
            totalDependents = 2,
            totalIncidents = 5,
            unacknowledgedAlerts = 2,
            criticalAlerts = 1,
            highAlerts = 1,
            recentIncidents = emptyList()
        )
        coEvery { api.getKeypadAlerts(any()) } returns Response.success(fakeSummary)

        val result = repository.getAlertSummary()
        assertTrue(result is Result.Success)
        assertEquals(2, (result as Result.Success).data.totalDependents)
        assertEquals(5, (result as Result.Success).data.totalIncidents)
    }

    @Test
    fun `08 acknowledgeAlert marks incident as reviewed`() = runBlocking {
        coEvery { api.acknowledgeKeypadAlert(any(), 10) } returns Response.success(mapOf("status" to "success"))

        val result = repository.acknowledgeAlert(10)
        assertTrue(result is Result.Success)
        assertTrue((result as Result.Success).data)
    }

    @Test
    fun `09 getEducation returns localized content for Kannada`() = runBlocking {
        val fakeEdu = KeypadEducationResponseDto(
            language = "kn",
            languageLabel = "ಕನ್ನಡ",
            goldenRuleTitle = "ಸುವರ್ಣ ನಿಯಮ",
            goldenRuleDescription = "OTP ಹಂಚಿಕೊಳ್ಳಬೇಡಿ",
            doNotShareItems = listOf("OTP", "UPI PIN"),
            commonScams = emptyList(),
            helplineGuidance = "1930 ಗೆ ಕರೆ ಮಾಡಿ"
        )
        coEvery { api.getKeypadEducation("kn") } returns Response.success(fakeEdu)

        val result = repository.getEducation("kn")
        assertTrue(result is Result.Success)
        assertEquals("kn", (result as Result.Success).data.language)
    }

    @Test
    fun `10 getOfficialHelpdesks returns Chakshu and 1930`() = runBlocking {
        val fakeHelp = KeypadOfficialHelpdeskResponseDto(
            disclaimer = "No software blocking.",
            portals = emptyList(),
            helplines = listOf(
                KeypadHelpdeskEntryDto(
                    name = "1930",
                    purpose = "Cyber Fraud",
                    accessChannel = "Call",
                    contactOrUrl = "1930",
                    howItHelps = "Financial freeze"
                )
            ),
            legalClarification = "Official reporting distinction."
        )
        coEvery { api.getKeypadHelpdesks() } returns Response.success(fakeHelp)

        val result = repository.getOfficialHelpdesks()
        assertTrue(result is Result.Success)
        assertEquals(1, (result as Result.Success).data.helplines.size)
    }

    @Test
    fun `11 api error returns Result Error`() = runBlocking {
        coEvery { api.getKeypadAlerts(any()) } returns Response.error(500, "Server Error".toResponseBody())

        val result = repository.getAlertSummary()
        assertTrue(result is Result.Error)
        assertEquals(500, (result as Result.Error).code)
    }
}
