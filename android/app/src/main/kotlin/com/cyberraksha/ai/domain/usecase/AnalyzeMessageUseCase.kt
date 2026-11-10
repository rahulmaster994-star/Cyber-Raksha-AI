package com.cyberraksha.ai.domain.usecase

import com.cyberraksha.ai.data.remote.MessageAnalysisResponse
import com.cyberraksha.ai.data.repository.MobileProtectionRepository
import com.cyberraksha.ai.data.repository.Result

class AnalyzeMessageUseCase(
    private val repository: MobileProtectionRepository
) {
    suspend operator fun invoke(
        messageText: String,
        sender: String? = null
    ): Result<MessageAnalysisResponse> {
        val trimmed = messageText.trim()
        if (trimmed.isEmpty()) {
            return Result.Error("Message text cannot be empty.")
        }
        return repository.analyzeMessage(trimmed, sender?.trim())
    }
}

