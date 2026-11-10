package com.cyberraksha.ai.domain.usecase

import com.cyberraksha.ai.data.remote.ReportThreatResponse
import com.cyberraksha.ai.data.repository.MobileProtectionRepository
import com.cyberraksha.ai.data.repository.Result

class ReportThreatUseCase(
    private val repository: MobileProtectionRepository
) {
    suspend operator fun invoke(
        threatType: String,
        indicatorValue: String,
        fraudCategory: String? = null,
        description: String? = null
    ): Result<ReportThreatResponse> {
        val trimmedVal = indicatorValue.trim()
        if (trimmedVal.isEmpty()) {
            return Result.Error("Indicator value cannot be empty.")
        }
        return repository.reportThreat(
            threatType = threatType,
            indicatorValue = trimmedVal,
            fraudCategory = fraudCategory,
            description = description
        )
    }
}

