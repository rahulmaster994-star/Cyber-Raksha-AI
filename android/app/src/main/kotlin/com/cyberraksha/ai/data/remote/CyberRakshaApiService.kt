package com.cyberraksha.ai.data.remote

import retrofit2.Response
import retrofit2.http.*

interface CyberRakshaApiService {

    // ── Health ────────────────────────────────────────────────────────────

    @GET("api/v1/health")
    suspend fun getHealth(): Response<HealthResponse>

    @GET("api/v1/monitoring/health/detailed")
    suspend fun getDetailedHealth(): Response<DetailedHealthResponse>

    // ── Device ────────────────────────────────────────────────────────────

    @POST("api/v1/devices/register")
    suspend fun registerDevice(
        @Body request: DeviceRegisterRequest
    ): Response<DeviceRegistrationResponse>

    @GET("api/v1/devices/{deviceId}/status")
    suspend fun getDeviceStatus(
        @Path("deviceId") deviceId: String
    ): Response<DeviceStatusResponse>

    @GET("api/v1/devices/{deviceId}/activity")
    suspend fun getDeviceActivity(
        @Path("deviceId") deviceId: String,
        @Query("skip")  skip: Int = 0,
        @Query("limit") limit: Int = 20
    ): Response<DeviceActivityListResponse>

    // ── Notifications ─────────────────────────────────────────────────────

    @GET("api/v1/notifications")
    suspend fun getNotifications(
        @Query("skip")     skip: Int = 0,
        @Query("limit")    limit: Int = 50,
        @Query("severity") severity: String? = null,
        @Query("is_read")  isRead: Boolean? = null
    ): Response<NotificationListResponse>

    @GET("api/v1/notifications/unread-count")
    suspend fun getUnreadCount(): Response<UnreadCountResponse>

    @PATCH("api/v1/notifications/{id}/read")
    suspend fun markNotificationRead(
        @Path("id") id: Int
    ): Response<MarkReadResponse>

    @POST("api/v1/notifications/read-all")
    suspend fun markAllNotificationsRead(): Response<MarkReadResponse>

    // ── Mobile Fraud Protection (Phase B2) ───────────────────────────────

    @POST("api/v1/mobile/analyze-message")
    suspend fun analyzeMessage(
        @Body request: MessageAnalysisRequest
    ): Response<MessageAnalysisResponse>

    @POST("api/v1/mobile/check-number")
    suspend fun checkNumber(
        @Body request: NumberCheckRequest
    ): Response<NumberCheckResponse>

    @GET("api/v1/mobile/threat-history")
    suspend fun getThreatHistory(
        @Query("device_id") deviceId: String,
        @Query("skip") skip: Int = 0,
        @Query("limit") limit: Int = 20
    ): Response<ThreatHistoryResponse>

    @GET("api/v1/mobile/protection-status")
    suspend fun getProtectionStatus(
        @Query("device_id") deviceId: String
    ): Response<ProtectionStatusResponse>

    @POST("api/v1/mobile/report-threat")
    suspend fun reportThreat(
        @Body request: ReportThreatRequest
    ): Response<ReportThreatResponse>

    @POST("api/v1/mobile/report-threat/dispute")
    suspend fun disputeNumber(
        @Body request: DisputeNumberRequest
    ): Response<DisputeNumberResponse>

    @POST("api/v1/devices/{deviceId}/revoke")
    suspend fun revokeDevice(
        @Path("deviceId") deviceId: String
    ): Response<Map<String, String>>

    // ── Unified Security Events (Phase B3) ─────────────────────────────────

    @POST("api/v1/security/events")
    suspend fun reportSecurityEvent(
        @Body request: SecurityEventApiRequest
    ): Response<SecurityEventApiResponse>

    @GET("api/v1/threat-intel/indicators")
    suspend fun getThreatIndicators(): Response<List<ThreatIndicatorDto>>

    // ── Authentication & User Account ─────────────────────────────────────

    @POST("api/v1/auth/register")
    suspend fun registerUser(
        @Body request: UserRegisterRequestDto
    ): Response<TokenResponseDto>

    @POST("api/v1/auth/login")
    suspend fun loginUser(
        @Body request: UserLoginRequestDto
    ): Response<TokenResponseDto>

    @POST("api/v1/auth/send-mobile-otp")
    suspend fun sendMobileOtp(
        @Header("Authorization") bearerToken: String,
        @Body request: MobileOtpRequestDto
    ): Response<Map<String, Any>>

    @POST("api/v1/auth/verify-mobile-otp")
    suspend fun verifyMobileOtp(
        @Header("Authorization") bearerToken: String,
        @Body request: MobileOtpVerifyRequestDto
    ): Response<Map<String, Any>>

    @GET("api/v1/auth/me")
    suspend fun getUserProfile(
        @Header("Authorization") bearerToken: String
    ): Response<UserProfileResponseDto>

    @DELETE("api/v1/auth/account")
    suspend fun deleteAccount(
        @Header("Authorization") bearerToken: String
    ): Response<Map<String, String>>

    // ── Cybercrime Complaints ─────────────────────────────────────────────

    @POST("api/v1/complaints/draft")
    suspend fun createComplaintDraft(
        @Header("Authorization") bearerToken: String?,
        @Body request: ComplaintDraftRequestDto
    ): Response<ComplaintResponseDto>

    @POST("api/v1/complaints/{complaintId}/ack")
    suspend fun recordOfficialAck(
        @Header("Authorization") bearerToken: String?,
        @Path("complaintId") complaintId: String,
        @Body request: RecordAckRequestDto
    ): Response<ComplaintResponseDto>

    @GET("api/v1/complaints")
    suspend fun listComplaints(
        @Header("Authorization") bearerToken: String?,
        @Query("device_id") deviceId: String? = null
    ): Response<List<ComplaintResponseDto>>

    // ── Community Threat Reporting ────────────────────────────────────────

    @POST("api/v1/community/report")
    suspend fun submitCommunityReport(
        @Header("Authorization") bearerToken: String?,
        @Body request: CommunityReportRequestDto
    ): Response<CommunityReportResponseDto>
}

