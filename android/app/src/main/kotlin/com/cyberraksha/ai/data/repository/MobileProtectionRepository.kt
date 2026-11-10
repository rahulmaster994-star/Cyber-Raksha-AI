package com.cyberraksha.ai.data.repository

import com.cyberraksha.ai.core.AppPreferences
import com.cyberraksha.ai.data.local.SmsAnalysisDao
import com.cyberraksha.ai.data.local.SmsAnalysisEntity
import com.cyberraksha.ai.data.remote.*
import com.google.gson.Gson
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.firstOrNull

class MobileProtectionRepository(
    private val api: CyberRakshaApiService,
    private val smsDao: SmsAnalysisDao,
    private val prefs: AppPreferences
) {
    private val gson = Gson()

    suspend fun analyzeMessage(
        messageText: String,
        sender: String? = null
    ): Result<MessageAnalysisResponse> = runCatching {
        val deviceId = prefs.deviceId.firstOrNull() ?: "offline-device-id"
        val response = api.analyzeMessage(
            MessageAnalysisRequest(
                deviceId = deviceId,
                messageText = messageText,
                sender = sender
            )
        )

        if (response.isSuccessful && response.body() != null) {
            val body = response.body()!!
            // Cache in Room database
            smsDao.insertAnalysis(
                SmsAnalysisEntity(
                    messageHash = body.messageHash,
                    riskScore = body.riskScore,
                    riskLevel = body.riskLevel,
                    fraudCategory = body.fraudCategory,
                    detectionReasonsJson = gson.toJson(body.detectionReasons),
                    recommendedAction = body.recommendedAction
                )
            )

            // Phase B3: Report high/critical threat to unified security pipeline
            if (body.riskLevel.equals("HIGH", ignoreCase = true) || body.riskLevel.equals("CRITICAL", ignoreCase = true)) {
                runCatching {
                    val indicator = body.extractedUrls.firstOrNull() ?: sender
                    api.reportSecurityEvent(
                        SecurityEventApiRequest(
                            eventType = "SMS_FRAUD_DETECTED",
                            severity = body.riskLevel,
                            sourceComponent = "ANDROID_APP",
                            deviceId = deviceId,
                            threatIndicator = indicator,
                            riskScore = body.riskScore,
                            detectionReason = body.detectionReasons.firstOrNull() ?: body.fraudCategory,
                            description = "SMS fraud alert: ${body.fraudCategory} detected on device"
                        )
                    )
                }
            }

            Result.Success(body)
        } else {
            // Local offline heuristic fallback
            val fallback = createLocalOfflineAnalysis(messageText, sender)
            smsDao.insertAnalysis(
                SmsAnalysisEntity(
                    messageHash = fallback.messageHash,
                    riskScore = fallback.riskScore,
                    riskLevel = fallback.riskLevel,
                    fraudCategory = fallback.fraudCategory,
                    detectionReasonsJson = gson.toJson(fallback.detectionReasons),
                    recommendedAction = fallback.recommendedAction
                )
            )
            Result.Success(fallback)
        }
    }.getOrElse {
        val fallback = createLocalOfflineAnalysis(messageText, sender)
        smsDao.insertAnalysis(
            SmsAnalysisEntity(
                messageHash = fallback.messageHash,
                riskScore = fallback.riskScore,
                riskLevel = fallback.riskLevel,
                fraudCategory = fallback.fraudCategory,
                detectionReasonsJson = gson.toJson(fallback.detectionReasons),
                recommendedAction = fallback.recommendedAction
            )
        )
        Result.Success(fallback)
    }

    suspend fun checkNumber(phoneNumber: String): Result<NumberCheckResponse> = runCatching {
        val deviceId = prefs.deviceId.firstOrNull() ?: "offline-device-id"
        val response = api.checkNumber(
            NumberCheckRequest(
                deviceId = deviceId,
                phoneNumber = phoneNumber
            )
        )

        if (response.isSuccessful && response.body() != null) {
            Result.Success(response.body()!!)
        } else {
            // Offline fallback for number check: UNKNOWN
            Result.Success(
                NumberCheckResponse(
                    phoneNumber = phoneNumber,
                    normalizedNumber = phoneNumber.replace(Regex("[^0-9+]"), ""),
                    riskLevel = "UNKNOWN",
                    fraudCategory = null,
                    reportCount = 0,
                    confidenceScore = 0.0f,
                    source = "OFFLINE_FALLBACK",
                    notes = "Backend unreachable; local reputation cache active.",
                    recommendedAction = "Unverified number. Never disclose OTPs or passwords.",
                    checkedAt = System.currentTimeMillis().toString()
                )
            )
        }
    }.getOrElse {
        Result.Success(
            NumberCheckResponse(
                phoneNumber = phoneNumber,
                normalizedNumber = phoneNumber.replace(Regex("[^0-9+]"), ""),
                riskLevel = "UNKNOWN",
                fraudCategory = null,
                reportCount = 0,
                confidenceScore = 0.0f,
                source = "OFFLINE_FALLBACK",
                notes = "Backend unreachable; local reputation cache active.",
                recommendedAction = "Unverified number. Never disclose OTPs or passwords.",
                checkedAt = System.currentTimeMillis().toString()
            )
        )
    }

    suspend fun getThreatHistory(): Result<ThreatHistoryResponse> = runCatching {
        val deviceId = prefs.deviceId.firstOrNull()
            ?: return@runCatching Result.Error("Device not registered")
        val response = api.getThreatHistory(deviceId)
        if (response.isSuccessful && response.body() != null) {
            Result.Success(response.body()!!)
        } else {
            Result.Error("Failed to fetch threat history: ${response.code()}", response.code())
        }
    }.getOrElse { Result.Error(it.message ?: "Network error") }

    suspend fun getProtectionStatus(): Result<ProtectionStatusResponse> = runCatching {
        val deviceId = prefs.deviceId.firstOrNull()
            ?: return@runCatching Result.Error("Device not registered")
        val response = api.getProtectionStatus(deviceId)
        if (response.isSuccessful && response.body() != null) {
            Result.Success(response.body()!!)
        } else {
            Result.Error("Failed to fetch protection status: ${response.code()}", response.code())
        }
    }.getOrElse { Result.Error(it.message ?: "Network error") }

    suspend fun reportThreat(
        threatType: String,
        indicatorValue: String,
        fraudCategory: String? = null,
        description: String? = null
    ): Result<ReportThreatResponse> = runCatching {
        val deviceId = prefs.deviceId.firstOrNull()
            ?: return@runCatching Result.Error("Device not registered")
        val response = api.reportThreat(
            ReportThreatRequest(
                deviceId = deviceId,
                threatType = threatType,
                indicatorValue = indicatorValue,
                fraudCategory = fraudCategory,
                description = description
            )
        )
        if (response.isSuccessful && response.body() != null) {
            Result.Success(response.body()!!)
        } else {
            Result.Error("Threat reporting failed: ${response.code()}", response.code())
        }
    }.getOrElse { Result.Error(it.message ?: "Network error") }

    fun getLocalAnalyses(): Flow<List<SmsAnalysisEntity>> = smsDao.getAllAnalysesFlow()

    suspend fun clearLocalHistory() = smsDao.clearAll()

    private fun createLocalOfflineAnalysis(text: String, sender: String?): MessageAnalysisResponse {
        val lower = text.lowercase()
        val isOtp = lower.contains("otp") || lower.contains("one time password") || lower.contains("verification code")
        val isBanking = lower.contains("blocked") || lower.contains("kyc") || lower.contains("debit card") || lower.contains("account suspended")
        val isUpi = lower.contains("upi") || lower.contains("paytm") || lower.contains("phonepe") || lower.contains("gpay") || lower.contains("collect request")

        val category = when {
            isOtp -> "OTP_FRAUD"
            isBanking -> "BANKING_FRAUD"
            isUpi -> "UPI_FRAUD"
            else -> "BENIGN"
        }

        val riskLevel = if (category != "BENIGN") "HIGH" else "SAFE"
        val score = if (category != "BENIGN") 75.0f else 5.0f
        val reasons = if (category != "BENIGN") {
            listOf("Offline heuristic match: detected suspicious keywords matching $category.")
        } else {
            listOf("No recognized fraud signatures identified by offline rules engine.")
        }

        return MessageAnalysisResponse(
            messageHash = text.hashCode().toString(),
            riskScore = score,
            riskLevel = riskLevel,
            fraudCategory = category,
            detectionReasons = reasons,
            extractedUrls = emptyList(),
            urlThreats = emptyList(),
            recommendedAction = if (category != "BENIGN") "WARNING: Suspicious message. Verify directly with sender before taking action." else "Message appears safe.",
            analyzedAt = System.currentTimeMillis().toString()
        )
    }
}

