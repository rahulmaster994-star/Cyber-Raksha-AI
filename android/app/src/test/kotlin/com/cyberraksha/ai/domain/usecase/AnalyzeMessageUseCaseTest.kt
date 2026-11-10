package com.cyberraksha.ai.domain.usecase

import com.cyberraksha.ai.data.remote.MessageAnalysisResponse
import com.cyberraksha.ai.data.repository.MobileProtectionRepository
import com.cyberraksha.ai.data.repository.Result
import io.mockk.coEvery
import io.mockk.mockk
import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test

class AnalyzeMessageUseCaseTest {

    private lateinit var repository: MobileProtectionRepository
    private lateinit var useCase: AnalyzeMessageUseCase

    @Before
    fun setup() {
        repository = mockk()
        useCase = AnalyzeMessageUseCase(repository)
    }

    @Test
    fun `empty message returns Error without invoking repository`() = runBlocking {
        val result = useCase("   ")
        assertTrue(result is Result.Error)
        assertEquals("Message text cannot be empty.", (result as Result.Error).message)
    }

    @Test
    fun `valid message invokes repository and returns Success`() = runBlocking {
        val fakeResponse = MessageAnalysisResponse(
            messageHash = "abc123hash",
            riskScore = 90.0f,
            riskLevel = "CRITICAL",
            fraudCategory = "GOV_IMPERSONATION",
            detectionReasons = listOf("Digital arrest detected"),
            extractedUrls = emptyList(),
            urlThreats = emptyList(),
            recommendedAction = "Do not comply",
            analyzedAt = "2026-11-09T10:00:00Z"
        )
        coEvery { repository.analyzeMessage(any(), any()) } returns Result.Success(fakeResponse)

        val result = useCase("Digital arrest warrant issued by police", "POLICE")

        assertTrue(result is Result.Success)
        val data = (result as Result.Success).data
        assertEquals("GOV_IMPERSONATION", data.fraudCategory)
        assertEquals("CRITICAL", data.riskLevel)
    }
}

