package com.cyberraksha.ai.core

import android.content.Context
import androidx.datastore.preferences.core.booleanPreferencesKey
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.longPreferencesKey
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import com.cyberraksha.ai.security.SecureTokenManager
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

private val Context.dataStore by preferencesDataStore(name = "cyber_raksha_prefs")

class AppPreferences(private val context: Context) {

    companion object {
        val KEY_DEVICE_ID = stringPreferencesKey("device_id")
        val KEY_DEVICE_NAME = stringPreferencesKey("device_name")
        val KEY_DEVICE_TOKEN = stringPreferencesKey("device_token")
        val KEY_ONBOARDING_COMPLETE = booleanPreferencesKey("onboarding_complete")
        val KEY_BACKEND_URL = stringPreferencesKey("backend_url")
        val KEY_LAST_SYNC = longPreferencesKey("last_sync_timestamp")
        val KEY_NOTIFICATIONS_ENABLED = booleanPreferencesKey("notifications_enabled")
        val KEY_MIN_SEVERITY = stringPreferencesKey("min_severity")
        const val DEFAULT_BACKEND_URL = "https://cyberraksha-backend.onrender.com"
    }

    val deviceId: Flow<String?> = context.dataStore.data.map { it[KEY_DEVICE_ID] }
    val deviceName: Flow<String?> = context.dataStore.data.map { it[KEY_DEVICE_NAME] }
    val deviceToken: Flow<String?> = context.dataStore.data.map { 
        val stored = it[KEY_DEVICE_TOKEN]
        if (!stored.isNullOrBlank()) SecureTokenManager.decrypt(stored) else null 
    }
    val onboardingComplete: Flow<Boolean> = context.dataStore.data.map { it[KEY_ONBOARDING_COMPLETE] ?: false }
    val backendUrl: Flow<String> = context.dataStore.data.map { 
        val stored = it[KEY_BACKEND_URL]?.trim()
        if (stored.isNullOrBlank() || stored.contains("10.0.2.2") || stored.contains("localhost") || stored.contains("127.0.0.1")) {
            DEFAULT_BACKEND_URL
        } else {
            com.cyberraksha.ai.data.remote.NetworkModule.normalizeBaseUrl(stored)
        }
    }
    val lastSyncTimestamp: Flow<Long> = context.dataStore.data.map { it[KEY_LAST_SYNC] ?: 0L }
    val notificationsEnabled: Flow<Boolean> = context.dataStore.data.map { it[KEY_NOTIFICATIONS_ENABLED] ?: true }
    val minSeverity: Flow<String> = context.dataStore.data.map { it[KEY_MIN_SEVERITY] ?: "LOW" }

    suspend fun saveDeviceId(id: String) = context.dataStore.edit { it[KEY_DEVICE_ID] = id }
    suspend fun saveDeviceName(name: String) = context.dataStore.edit { it[KEY_DEVICE_NAME] = name }
    suspend fun saveDeviceToken(token: String) = context.dataStore.edit { 
        it[KEY_DEVICE_TOKEN] = SecureTokenManager.encrypt(token) 
    }
    suspend fun setOnboardingComplete() = context.dataStore.edit { it[KEY_ONBOARDING_COMPLETE] = true }
    suspend fun saveBackendUrl(url: String) = context.dataStore.edit { it[KEY_BACKEND_URL] = url }
    suspend fun updateLastSync() = context.dataStore.edit { it[KEY_LAST_SYNC] = System.currentTimeMillis() }
    suspend fun setNotificationsEnabled(enabled: Boolean) = context.dataStore.edit { it[KEY_NOTIFICATIONS_ENABLED] = enabled }
    suspend fun setMinSeverity(severity: String) = context.dataStore.edit { it[KEY_MIN_SEVERITY] = severity }
}

