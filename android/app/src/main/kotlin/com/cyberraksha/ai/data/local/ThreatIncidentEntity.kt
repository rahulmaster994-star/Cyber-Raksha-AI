package com.cyberraksha.ai.data.local

import androidx.room.*
import kotlinx.coroutines.flow.Flow

@Entity(tableName = "threat_incidents")
data class ThreatIncidentEntity(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    val incidentType: String, // "SMS", "CALL", "WEB_DNS", "SHARED_SCAN"
    val indicator: String,    // Phone number, URL, domain, or sender
    val category: String,     // BANKING_FRAUD, UPI_FRAUD, GOV_IMPERSONATION, etc.
    val severity: String,     // LOW, MEDIUM, HIGH, CRITICAL
    val riskScore: Float,
    val description: String,
    val timestamp: Long = System.currentTimeMillis(),
    val isSynced: Boolean = false
)

@Dao
interface ThreatIncidentDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertIncident(incident: ThreatIncidentEntity): Long

    @Query("SELECT * FROM threat_incidents ORDER BY timestamp DESC")
    fun getAllIncidentsFlow(): Flow<List<ThreatIncidentEntity>>

    @Query("SELECT * FROM threat_incidents ORDER BY timestamp DESC LIMIT :limit")
    suspend fun getRecentIncidents(limit: Int): List<ThreatIncidentEntity>

    @Query("SELECT COUNT(*) FROM threat_incidents")
    fun getTotalIncidentCountFlow(): Flow<Int>

    @Query("SELECT COUNT(*) FROM threat_incidents WHERE incidentType = :type")
    fun getIncidentCountByTypeFlow(type: String): Flow<Int>

    @Query("SELECT COUNT(*) FROM threat_incidents WHERE severity = 'CRITICAL'")
    fun getCriticalIncidentCountFlow(): Flow<Int>

    @Query("SELECT * FROM threat_incidents WHERE isSynced = 0")
    suspend fun getUnsyncedIncidents(): List<ThreatIncidentEntity>

    @Query("UPDATE threat_incidents SET isSynced = 1 WHERE id IN (:ids)")
    suspend fun markAsSynced(ids: List<Long>)

    @Query("DELETE FROM threat_incidents")
    suspend fun clearAll()
}

