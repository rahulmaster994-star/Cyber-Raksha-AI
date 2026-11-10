package com.cyberraksha.ai.data.local

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "sync_state")
data class SyncStateEntity(
    @PrimaryKey
    val id: Int = 1,
    val lastSyncTimestamp: Long = 0L,
    val deviceId: String = "",
    val deviceRegistered: Boolean = false
)

