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
        val KEY_AUTONOMOUS_PROTECTION = booleanPreferencesKey("autonomous_protection_enabled")
        val KEY_SMS_PROTECTION = booleanPreferencesKey("sms_protection_enabled")
        val KEY_CALL_PROTECTION = booleanPreferencesKey("call_protection_enabled")
        val KEY_WEB_PROTECTION = booleanPreferencesKey("web_protection_enabled")
        val KEY_USER_TOKEN = stringPreferencesKey("user_token")
        val KEY_USER_NAME = stringPreferencesKey("user_name")
        val KEY_USER_EMAIL = stringPreferencesKey("user_email")
        val KEY_USER_MOBILE = stringPreferencesKey("user_mobile")
        val KEY_IS_MOBILE_VERIFIED = booleanPreferencesKey("is_mobile_verified")
        val KEY_CONSENT_GIVEN = booleanPreferencesKey("consent_given")
        val KEY_NOTIF_LISTENER_ENABLED = booleanPreferencesKey("notif_listener_enabled")
        val KEY_WHATSAPP_PROTECTION = booleanPreferencesKey("whatsapp_protection_enabled")
        val KEY_TELEGRAM_PROTECTION = booleanPreferencesKey("telegram_protection_enabled")
        val KEY_CALL_BLOCKING_ENABLED = booleanPreferencesKey("call_blocking_enabled")
        const val DEFAULT_BACKEND_URL = "https://cyberraksha-backend.onrender.com"
    }

    val deviceId: Flow<String?> = context.dataStore.data.map { it[KEY_DEVICE_ID] }
    val deviceName: Flow<String?> = context.dataStore.data.map { it[KEY_DEVICE_NAME] }
    val deviceToken: Flow<String?> = context.dataStore.data.map { 
        val stored = it[KEY_DEVICE_TOKEN]
        if (!stored.isNullOrBlank()) SecureTokenManager.decrypt(stored) else null 
    }
    val userToken: Flow<String?> = context.dataStore.data.map {
        val stored = it[KEY_USER_TOKEN]
        if (!stored.isNullOrBlank()) SecureTokenManager.decrypt(stored) else null
    }
    val userName: Flow<String?> = context.dataStore.data.map { it[KEY_USER_NAME] }
    val userEmail: Flow<String?> = context.dataStore.data.map { it[KEY_USER_EMAIL] }
    val userMobile: Flow<String?> = context.dataStore.data.map { it[KEY_USER_MOBILE] }
    val isMobileVerified: Flow<Boolean> = context.dataStore.data.map { it[KEY_IS_MOBILE_VERIFIED] ?: false }
    val consentGiven: Flow<Boolean> = context.dataStore.data.map { it[KEY_CONSENT_GIVEN] ?: false }
    val notifListenerEnabled: Flow<Boolean> = context.dataStore.data.map { it[KEY_NOTIF_LISTENER_ENABLED] ?: true }
    val whatsappProtectionEnabled: Flow<Boolean> = context.dataStore.data.map { it[KEY_WHATSAPP_PROTECTION] ?: true }
    val telegramProtectionEnabled: Flow<Boolean> = context.dataStore.data.map { it[KEY_TELEGRAM_PROTECTION] ?: true }
    val callBlockingEnabled: Flow<Boolean> = context.dataStore.data.map { it[KEY_CALL_BLOCKING_ENABLED] ?: true }
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
    val autonomousProtectionEnabled: Flow<Boolean> = context.dataStore.data.map { it[KEY_AUTONOMOUS_PROTECTION] ?: true }
    val smsProtectionEnabled: Flow<Boolean> = context.dataStore.data.map { it[KEY_SMS_PROTECTION] ?: true }
    val callProtectionEnabled: Flow<Boolean> = context.dataStore.data.map { it[KEY_CALL_PROTECTION] ?: true }
    val webProtectionEnabled: Flow<Boolean> = context.dataStore.data.map { it[KEY_WEB_PROTECTION] ?: true }

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
    suspend fun setAutonomousProtectionEnabled(enabled: Boolean) = context.dataStore.edit { it[KEY_AUTONOMOUS_PROTECTION] = enabled }
    suspend fun setSmsProtectionEnabled(enabled: Boolean) = context.dataStore.edit { it[KEY_SMS_PROTECTION] = enabled }
    suspend fun setCallProtectionEnabled(enabled: Boolean) = context.dataStore.edit { it[KEY_CALL_PROTECTION] = enabled }
    suspend fun setWebProtectionEnabled(enabled: Boolean) = context.dataStore.edit { it[KEY_WEB_PROTECTION] = enabled }
    suspend fun setNotifListenerEnabled(enabled: Boolean) = context.dataStore.edit { it[KEY_NOTIF_LISTENER_ENABLED] = enabled }
    suspend fun setWhatsappProtectionEnabled(enabled: Boolean) = context.dataStore.edit { it[KEY_WHATSAPP_PROTECTION] = enabled }
    suspend fun setTelegramProtectionEnabled(enabled: Boolean) = context.dataStore.edit { it[KEY_TELEGRAM_PROTECTION] = enabled }
    suspend fun setCallBlockingEnabled(enabled: Boolean) = context.dataStore.edit { it[KEY_CALL_BLOCKING_ENABLED] = enabled }
    suspend fun setConsentGiven(given: Boolean) = context.dataStore.edit { it[KEY_CONSENT_GIVEN] = given }
    suspend fun saveUserToken(token: String) = context.dataStore.edit {
        it[KEY_USER_TOKEN] = SecureTokenManager.encrypt(token)
    }
    suspend fun saveUserProfile(name: String, email: String, mobile: String?, isMobileVerified: Boolean) = context.dataStore.edit {
        it[KEY_USER_NAME] = name
        it[KEY_USER_EMAIL] = email
        if (mobile != null) it[KEY_USER_MOBILE] = mobile
        it[KEY_IS_MOBILE_VERIFIED] = isMobileVerified
    }
    suspend fun clearUserSession() = context.dataStore.edit {
        it.remove(KEY_USER_TOKEN)
        it.remove(KEY_USER_NAME)
        it.remove(KEY_USER_EMAIL)
        it.remove(KEY_USER_MOBILE)
        it.remove(KEY_IS_MOBILE_VERIFIED)
    }
}

