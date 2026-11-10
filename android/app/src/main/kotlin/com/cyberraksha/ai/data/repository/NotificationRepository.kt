package com.cyberraksha.ai.data.repository

import com.cyberraksha.ai.data.local.NotificationDao
import com.cyberraksha.ai.data.local.NotificationEntity
import com.cyberraksha.ai.data.remote.CyberRakshaApiService
import com.cyberraksha.ai.data.remote.NotificationItem
import kotlinx.coroutines.flow.Flow

class NotificationRepository(
    private val api: CyberRakshaApiService,
    private val dao: NotificationDao
) {
    /** Offline-first: always reads from local Room DB. */
    fun getNotificationsFlow(limit: Int = 100): Flow<List<NotificationEntity>> =
        dao.getAll(limit)

    fun getUnreadCountFlow(): Flow<Int> = dao.getUnreadCount()

    /** Fetch from backend and cache into Room. Returns true on success. */
    suspend fun syncFromBackend(): Boolean = runCatching {
        val response = api.getNotifications(limit = 100)
        if (response.isSuccessful) {
            val items = response.body()?.notifications ?: emptyList()
            dao.upsertAll(items.map { it.toEntity() })
            true
        } else false
    }.getOrDefault(false)

    suspend fun markRead(id: Int) {
        runCatching { api.markNotificationRead(id) }
        dao.markRead(id)
    }

    suspend fun markAllRead() {
        runCatching { api.markAllNotificationsRead() }
        dao.markAllRead()
    }

    suspend fun delete(id: Int) = dao.delete(id)
    suspend fun clearAll() = dao.clearAll()

    suspend fun getUnreadCountOnce(): Int = dao.getUnreadCountOnce()

    private fun NotificationItem.toEntity() = NotificationEntity(
        id             = id,
        title          = title,
        message        = message,
        severity       = severity,
        category       = category,
        targetDomain   = targetDomain,
        isRead         = isRead,
        createdAt      = createdAt,
        sourceComponent = sourceComponent
    )
}

