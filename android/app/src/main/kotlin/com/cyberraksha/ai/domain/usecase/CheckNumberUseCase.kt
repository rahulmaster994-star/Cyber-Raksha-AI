package com.cyberraksha.ai.domain.usecase

import com.cyberraksha.ai.data.remote.NumberCheckResponse
import com.cyberraksha.ai.data.repository.MobileProtectionRepository
import com.cyberraksha.ai.data.repository.Result

class CheckNumberUseCase(
    private val repository: MobileProtectionRepository
) {
    suspend operator fun invoke(phoneNumber: String): Result<NumberCheckResponse> {
        val trimmed = phoneNumber.trim()
        if (trimmed.isEmpty()) {
            return Result.Error("Phone number cannot be empty.")
        }
        return repository.checkNumber(trimmed)
    }
}

