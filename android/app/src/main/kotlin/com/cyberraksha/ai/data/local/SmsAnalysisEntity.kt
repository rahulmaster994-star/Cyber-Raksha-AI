package com.cyberraksha.ai.data.local

import androidx.room.Dao
import androidx.room.Entity
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.PrimaryKey
import androidx.room.Query
import kotlinx.coroutines.flow.Flow

@Entity(tableName = "sms_analysis_history")
data class SmsAnalysisEntity(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    val messageHash: String,
    val riskScore: Float,
    val riskLevel: String,
    val fraudCategory: String,
    val detectionReasonsJson: String,
    val recommendedAction: String,
    val analyzedAt: Long = System.currentTimeMillis()
)

@Dao
interface SmsAnalysisDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertAnalysis(entity: SmsAnalysisEntity): Long

    @Query("SELECT * FROM sms_analysis_history ORDER BY analyzedAt DESC")
    fun getAllAnalysesFlow(): Flow<List<SmsAnalysisEntity>>

    @Query("SELECT * FROM sms_analysis_history ORDER BY analyzedAt DESC LIMIT :limit")
    suspend fun getRecentAnalyses(limit: Int): List<SmsAnalysisEntity>

    @Query("DELETE FROM sms_analysis_history WHERE id = :id")
    suspend fun deleteAnalysisById(id: Long)

    @Query("DELETE FROM sms_analysis_history")
    suspend fun clearAll()
}

