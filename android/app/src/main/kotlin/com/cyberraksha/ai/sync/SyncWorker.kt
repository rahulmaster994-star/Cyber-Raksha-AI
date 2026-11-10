package com.cyberraksha.ai.sync

import android.content.Context
import androidx.room.Room
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
import com.cyberraksha.ai.core.AppPreferences
import com.cyberraksha.ai.data.local.AppDatabase
import com.cyberraksha.ai.data.remote.NetworkModule
import com.cyberraksha.ai.data.repository.NotificationRepository
import com.cyberraksha.ai.domain.usecase.SyncNotificationsUseCase
import kotlinx.coroutines.flow.firstOrNull

class SyncWorker(
    appContext: Context,
    workerParams: WorkerParameters
) : CoroutineWorker(appContext, workerParams) {

    override suspend fun doWork(): Result {
        return try {
            val prefs   = AppPreferences(applicationContext)
            val baseUrl = prefs.backendUrl.firstOrNull() ?: AppPreferences.DEFAULT_BACKEND_URL
            val api     = NetworkModule.createApiService(baseUrl)
            val db      = Room.databaseBuilder(
                applicationContext,
                AppDatabase::class.java,
                "cyber_raksha_db"
            ).build()

            val syncUseCase = SyncNotificationsUseCase(
                notificationRepository = NotificationRepository(api, db.notificationDao()),
                prefs = prefs
            )

            val success = syncUseCase()
            db.close()

            if (success) Result.success() else Result.retry()
        } catch (e: Exception) {
            Result.retry()
        }
    }
}

