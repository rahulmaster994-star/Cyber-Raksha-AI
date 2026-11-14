package com.cyberraksha.ai.sync

import android.content.Context
import androidx.room.Room
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
import com.cyberraksha.ai.core.AppPreferences
import com.cyberraksha.ai.data.local.AppDatabase
import com.cyberraksha.ai.data.remote.NetworkModule
import com.cyberraksha.ai.data.remote.SecurityEventApiRequest
import com.cyberraksha.ai.data.repository.NotificationRepository
import com.cyberraksha.ai.domain.usecase.SyncNotificationsUseCase
import com.cyberraksha.ai.vpn.CyberRakshaDnsVpnService
import kotlinx.coroutines.flow.firstOrNull

class SyncWorker(
    appContext: Context,
    workerParams: WorkerParameters
) : CoroutineWorker(appContext, workerParams) {

    override suspend fun doWork(): Result {
        return try {
            val prefs   = AppPreferences(applicationContext)
            val baseUrl = prefs.backendUrl.firstOrNull() ?: AppPreferences.DEFAULT_BACKEND_URL
            val deviceId = prefs.deviceId.firstOrNull() ?: "DEVICE-${android.os.Build.MODEL}"
            val api     = NetworkModule.createApiService(baseUrl)
            val db      = Room.databaseBuilder(
                applicationContext,
                AppDatabase::class.java,
                "cyber_raksha_db"
            ).fallbackToDestructiveMigration().build()

            // 1. Sync notifications from backend
            val syncUseCase = SyncNotificationsUseCase(
                notificationRepository = NotificationRepository(api, db.notificationDao()),
                prefs = prefs
            )
            val notifSuccess = try { syncUseCase() } catch (_: Exception) { false }

            // 2. Sync local unsynced threat incidents to backend security events
            try {
                val unsyncedIncidents = db.threatIncidentDao().getUnsyncedIncidents()
                val syncedIds = mutableListOf<Long>()
                for (incident in unsyncedIncidents) {
                    val event = SecurityEventApiRequest(
                        eventType = incident.incidentType,
                        severity = incident.severity,
                        sourceComponent = "ANDROID_${incident.incidentType}",
                        deviceId = deviceId,
                        threatIndicator = incident.indicator,
                        riskScore = incident.riskScore / 100f,
                        detectionReason = incident.category,
                        description = "Autonomous detection on Android device: ${incident.incidentType} - ${incident.description}",
                        rawPayload = incident.indicator
                    )
                    val response = api.reportSecurityEvent(event)
                    if (response.isSuccessful) {
                        syncedIds.add(incident.id)
                    }
                }
                if (syncedIds.isNotEmpty()) {
                    db.threatIncidentDao().markAsSynced(syncedIds)
                }
            } catch (_: Exception) {
                // Non-fatal incident sync error; continue
            }

            // 3. Pull threat intelligence indicators into local DNS protection cache
            try {
                val indicatorsRes = api.getThreatIndicators()
                if (indicatorsRes.isSuccessful) {
                    val indicators = indicatorsRes.body().orEmpty()
                    val domains = indicators
                        .filter { it.indicatorType.equals("DOMAIN", ignoreCase = true) || it.indicatorType.equals("URL", ignoreCase = true) }
                        .map { it.indicatorValue.replace("https://", "").replace("http://", "").split("/").first().trim().lowercase() }
                        .filter { it.isNotEmpty() && it.contains(".") }
                    if (domains.isNotEmpty()) {
                        CyberRakshaDnsVpnService.addBlockedDomains(domains)
                    }
                }
            } catch (_: Exception) {
                // Non-fatal threat intel pull error; continue
            }

            db.close()
            Result.success()
        } catch (e: Exception) {
            Result.retry()
        }
    }
}


