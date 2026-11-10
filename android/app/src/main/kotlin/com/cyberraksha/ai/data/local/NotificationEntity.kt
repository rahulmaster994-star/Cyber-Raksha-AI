package com.cyberraksha.ai.data.local

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "notifications")
data class NotificationEntity(
    @PrimaryKey
    val id: Int,
    val title: String,
    val message: String,
    val severity: String,
    val category: String?,
    val targetDomain: String?,
    val isRead: Boolean,
    val createdAt: String,
    val sourceComponent: String?
)

