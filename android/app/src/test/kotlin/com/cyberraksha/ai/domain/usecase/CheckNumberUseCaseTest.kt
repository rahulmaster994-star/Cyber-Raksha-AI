package com.cyberraksha.ai.domain.usecase

import com.cyberraksha.ai.data.remote.NumberCheckResponse
import com.cyberraksha.ai.data.repository.MobileProtectionRepository
import com.cyberraksha.ai.data.repository.Result
import io.mockk.coEvery
import io.mockk.mockk
import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test

class CheckNumberUseCaseTest {

    private lateinit var repository: MobileProtectionRepository
    private lateinit var useCase: CheckNumberUseCase

    @Before
    fun setup() {
        repository = mockk()
        useCase = CheckNumberUseCase(repository)
    }

    @Test
    fun `empty phone number returns Error without calling repository`() = runBlocking {
        val result = useCase("   ")
        assertTrue(result is Result.Error)
        assertEquals("Phone number cannot be empty.", (result as Result.Error).message)
    }

    @Test
    fun `valid number delegates to repository`() = runBlocking {
        val fakeResponse = NumberCheckResponse(
            phoneNumber = "9876543210",
            normalizedNumber = "+919876543210",
            riskLevel = "HIGH",
            fraudCategory = "UPI_SCAM",
            reportCount = 4,
            confidenceScore = 0.85f,
            source = "COMMUNITY",
            notes = "Fake cashback",
            recommendedAction = "Do not share PIN",
            checkedAt = "2026-11-09T10:00:00Z"
        )
        coEvery { repository.checkNumber(any()) } returns Result.Success(fakeResponse)

        val result = useCase("9876543210")

        assertTrue(result is Result.Success)
        val data = (result as Result.Success).data
        assertEquals("+919876543210", data.normalizedNumber)
        assertEquals("HIGH", data.riskLevel)
    }
}

