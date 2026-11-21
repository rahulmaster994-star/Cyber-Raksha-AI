package com.cyberraksha.ai.data.repository

import com.cyberraksha.ai.core.AppPreferences
import com.cyberraksha.ai.data.remote.*
import kotlinx.coroutines.flow.firstOrNull

class KeypadProtectionRepository(
    private val api: CyberRakshaApiService,
    private val prefs: AppPreferences
) {

    private suspend fun getAuthHeader(): String? {
        val token = prefs.userToken.firstOrNull()
        return if (!token.isNullOrBlank()) "Bearer $token" else null
    }

    // ── 1. Family Registration ───────────────────────────────────────────────

    suspend fun registerElderlyMember(request: KeypadElderlyUserCreateDto): Result<KeypadElderlyUserResponseDto> = runCatching {
        val auth = getAuthHeader()
        val response = api.registerKeypadElderlyMember(auth, request)
        if (response.isSuccessful && response.body() != null) {
            Result.Success(response.body()!!)
        } else {
            Result.Error(response.errorBody()?.string() ?: "Failed to register elderly member (${response.code()})", response.code())
        }
    }.getOrElse { e ->
        Result.Error(e.message ?: "Network error during family registration")
    }

    suspend fun getElderlyMembers(): Result<List<KeypadElderlyUserResponseDto>> = runCatching {
        val auth = getAuthHeader()
        val response = api.listKeypadElderlyMembers(auth)
        if (response.isSuccessful && response.body() != null) {
            Result.Success(response.body()!!)
        } else {
            Result.Error(response.errorBody()?.string() ?: "Failed to fetch elderly family members (${response.code()})", response.code())
        }
    }.getOrElse { e ->
        Result.Error(e.message ?: "Network error fetching family members")
    }

    suspend fun removeElderlyMember(elderlyId: Int): Result<Boolean> = runCatching {
        val auth = getAuthHeader()
        val response = api.removeKeypadElderlyMember(auth, elderlyId)
        if (response.isSuccessful) {
            Result.Success(true)
        } else {
            Result.Error(response.errorBody()?.string() ?: "Failed to remove dependent (${response.code()})", response.code())
        }
    }.getOrElse { e ->
        Result.Error(e.message ?: "Network error removing dependent")
    }

    // ── 2. SMS Risk Analysis ─────────────────────────────────────────────────

    suspend fun checkSms(request: KeypadSmsCheckRequestDto): Result<KeypadSmsCheckResponseDto> = runCatching {
        val auth = getAuthHeader()
        val response = api.checkKeypadSms(auth, request)
        if (response.isSuccessful && response.body() != null) {
            Result.Success(response.body()!!)
        } else {
            Result.Error(response.errorBody()?.string() ?: "Failed to analyze SMS (${response.code()})", response.code())
        }
    }.getOrElse { e ->
        Result.Error(e.message ?: "Network error during SMS analysis")
    }

    // ── 3. Call Risk Check ───────────────────────────────────────────────────

    suspend fun checkCall(request: KeypadCallCheckRequestDto): Result<KeypadCallCheckResponseDto> = runCatching {
        val auth = getAuthHeader()
        val response = api.checkKeypadCall(auth, request)
        if (response.isSuccessful && response.body() != null) {
            Result.Success(response.body()!!)
        } else {
            Result.Error(response.errorBody()?.string() ?: "Failed to verify phone number (${response.code()})", response.code())
        }
    }.getOrElse { e ->
        Result.Error(e.message ?: "Network error during call risk check")
    }

    // ── 4. Scam Number Intelligence Report ───────────────────────────────────

    suspend fun reportScamNumber(request: KeypadScamNumberReportRequestDto): Result<KeypadScamNumberReportResponseDto> = runCatching {
        val auth = getAuthHeader()
        val response = api.reportKeypadScamNumber(auth, request)
        if (response.isSuccessful && response.body() != null) {
            Result.Success(response.body()!!)
        } else {
            Result.Error(response.errorBody()?.string() ?: "Failed to report scam number (${response.code()})", response.code())
        }
    }.getOrElse { e ->
        Result.Error(e.message ?: "Network error reporting scam number")
    }

    // ── 5. Guardian Alert System ─────────────────────────────────────────────

    suspend fun getAlertSummary(): Result<KeypadAlertSummaryResponseDto> = runCatching {
        val auth = getAuthHeader()
        val response = api.getKeypadAlerts(auth)
        if (response.isSuccessful && response.body() != null) {
            Result.Success(response.body()!!)
        } else {
            Result.Error(response.errorBody()?.string() ?: "Failed to fetch guardian alerts (${response.code()})", response.code())
        }
    }.getOrElse { e ->
        Result.Error(e.message ?: "Network error fetching alerts")
    }

    suspend fun acknowledgeAlert(incidentId: Int): Result<Boolean> = runCatching {
        val auth = getAuthHeader()
        val response = api.acknowledgeKeypadAlert(auth, incidentId)
        if (response.isSuccessful) {
            Result.Success(true)
        } else {
            Result.Error(response.errorBody()?.string() ?: "Failed to acknowledge alert (${response.code()})", response.code())
        }
    }.getOrElse { e ->
        Result.Error(e.message ?: "Network error acknowledging alert")
    }

    // ── 6. Elderly Fraud Education ───────────────────────────────────────────

    suspend fun getEducation(language: String): Result<KeypadEducationResponseDto> = runCatching {
        val response = api.getKeypadEducation(language)
        if (response.isSuccessful && response.body() != null) {
            Result.Success(response.body()!!)
        } else {
            Result.Error(response.errorBody()?.string() ?: "Failed to fetch fraud education (${response.code()})", response.code())
        }
    }.getOrElse { e ->
        Result.Error(e.message ?: "Network error fetching education")
    }

    // ── 7. Official Reporting Guidance ───────────────────────────────────────

    suspend fun getOfficialHelpdesks(): Result<KeypadOfficialHelpdeskResponseDto> = runCatching {
        val response = api.getKeypadHelpdesks()
        if (response.isSuccessful && response.body() != null) {
            Result.Success(response.body()!!)
        } else {
            Result.Error(response.errorBody()?.string() ?: "Failed to fetch official helpdesks (${response.code()})", response.code())
        }
    }.getOrElse { e ->
        Result.Error(e.message ?: "Network error fetching official helpdesks")
    }
}

