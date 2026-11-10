package com.cyberraksha.ai.domain.usecase

import com.cyberraksha.ai.core.AppPreferences
import com.cyberraksha.ai.data.repository.NotificationRepository

class SyncNotificationsUseCase(
    private val notificationRepository: NotificationRepository,
    private val prefs: AppPreferences
) {
    /** Returns true when the sync succeeded. */
    suspend operator fun invoke(): Boolean {
        val success = notificationRepository.syncFromBackend()
        if (success) prefs.updateLastSync()
        return success
    }
}

