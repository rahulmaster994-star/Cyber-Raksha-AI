package com.cyberraksha.ai.data.local

import androidx.room.Database
import androidx.room.RoomDatabase

@Database(
    entities = [NotificationEntity::class, SyncStateEntity::class, SmsAnalysisEntity::class],
    version = 2,
    exportSchema = false
)
abstract class AppDatabase : RoomDatabase() {
    abstract fun notificationDao(): NotificationDao
    abstract fun smsAnalysisDao(): SmsAnalysisDao
}
