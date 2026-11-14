package com.cyberraksha.ai.ui.dashboard

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.cyberraksha.ai.core.AppPreferences
import com.cyberraksha.ai.data.local.NotificationDao
import com.cyberraksha.ai.data.local.ThreatIncidentDao
import com.cyberraksha.ai.data.remote.NetworkModule
import com.cyberraksha.ai.data.remote.ProtectionModulesStatus
import com.cyberraksha.ai.data.remote.SecurityEventItem
import com.cyberraksha.ai.data.repository.DeviceRepository
import com.cyberraksha.ai.data.repository.HealthRepository
import com.cyberraksha.ai.data.repository.NotificationRepository
import com.cyberraksha.ai.data.repository.Result
import com.cyberraksha.ai.domain.usecase.SyncNotificationsUseCase
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.firstOrNull
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

data class DashboardUiState(
    val deviceName: String = "Cyber Raksha Client",
    val deviceId: String = "",
    val isConnected: Boolean = false,
    val securityPosture: String = "PROTECTED",
    val unreadCount: Int = 0,
    val criticalCount: Int = 0,
    val highCount: Int = 0,
    val totalThreatsBlocked: Int = 0,
    val smsThreatsCount: Int = 0,
    val callThreatsCount: Int = 0,
    val webThreatsCount: Int = 0,
    val autonomousProtectionEnabled: Boolean = false,
    val smsProtectionEnabled: Boolean = true,
    val callProtectionEnabled: Boolean = true,
    val webProtectionEnabled: Boolean = true,
    val lastSyncFormatted: String = "Never",
    val isRefreshing: Boolean = false,
    val protectionModules: ProtectionModulesStatus = ProtectionModulesStatus(),
    val recentActivity: List<SecurityEventItem> = emptyList(),
    val isOffline: Boolean = false,
    val diagnosticReport: com.cyberraksha.ai.data.repository.DiagnosticReport? = null
)

class DashboardViewModel(
    private val prefs: AppPreferences,
    private val notificationDao: NotificationDao,
    private val threatIncidentDao: ThreatIncidentDao
) : ViewModel() {

    private val _uiState = MutableStateFlow(DashboardUiState())
    val uiState: StateFlow<DashboardUiState> = _uiState.asStateFlow()

    init {
        loadInitialData()
        refresh()
    }

    private fun loadInitialData() {
        viewModelScope.launch {
            val name = prefs.deviceName.firstOrNull() ?: "Mobile Device"
            val id = prefs.deviceId.firstOrNull() ?: ""
            _uiState.update { it.copy(deviceName = name, deviceId = id) }

            // Observe local unread notifications count
            launch {
                notificationDao.getUnreadCount().collect { count ->
                    _uiState.update { it.copy(unreadCount = count) }
                }
            }

            // Observe autonomous protection preferences
            launch {
                prefs.autonomousProtectionEnabled.collect { enabled ->
                    _uiState.update { it.copy(autonomousProtectionEnabled = enabled) }
                }
            }
            launch {
                prefs.smsProtectionEnabled.collect { enabled ->
                    _uiState.update { it.copy(smsProtectionEnabled = enabled) }
                }
            }
            launch {
                prefs.callProtectionEnabled.collect { enabled ->
                    _uiState.update { it.copy(callProtectionEnabled = enabled) }
                }
            }
            launch {
                prefs.webProtectionEnabled.collect { enabled ->
                    _uiState.update { it.copy(webProtectionEnabled = enabled) }
                }
            }

            // Observe incident counters from Room DB
            launch {
                threatIncidentDao.getTotalIncidentCountFlow().collect { count ->
                    _uiState.update { it.copy(totalThreatsBlocked = count) }
                }
            }
            launch {
                threatIncidentDao.getIncidentCountByTypeFlow("SMS").collect { count ->
                    _uiState.update { it.copy(smsThreatsCount = count) }
                }
            }
            launch {
                threatIncidentDao.getIncidentCountByTypeFlow("CALL").collect { count ->
                    _uiState.update { it.copy(callThreatsCount = count) }
                }
            }
            launch {
                threatIncidentDao.getIncidentCountByTypeFlow("WEB_DNS").collect { count ->
                    _uiState.update { it.copy(webThreatsCount = count) }
                }
            }
        }
    }

    fun toggleAutonomousProtection(enabled: Boolean) {
        viewModelScope.launch {
            prefs.setAutonomousProtectionEnabled(enabled)
            _uiState.update { it.copy(autonomousProtectionEnabled = enabled) }
        }
    }

    fun toggleSmsProtection(enabled: Boolean) {
        viewModelScope.launch {
            prefs.setSmsProtectionEnabled(enabled)
            _uiState.update { it.copy(smsProtectionEnabled = enabled) }
        }
    }

    fun toggleCallProtection(enabled: Boolean) {
        viewModelScope.launch {
            prefs.setCallProtectionEnabled(enabled)
            _uiState.update { it.copy(callProtectionEnabled = enabled) }
        }
    }

    fun toggleWebProtection(enabled: Boolean) {
        viewModelScope.launch {
            prefs.setWebProtectionEnabled(enabled)
            _uiState.update { it.copy(webProtectionEnabled = enabled) }
        }
    }

    fun refresh() {
        viewModelScope.launch {
            _uiState.update { it.copy(isRefreshing = true) }

            val rawBaseUrl = prefs.backendUrl.firstOrNull() ?: AppPreferences.DEFAULT_BACKEND_URL
            val baseUrl = NetworkModule.normalizeBaseUrl(rawBaseUrl)
            val api = NetworkModule.getApiService(baseUrl)
            val healthRepo = HealthRepository(api)
            val deviceRepo = DeviceRepository(api, prefs)
            val notifRepo = NotificationRepository(api, notificationDao)
            val syncUseCase = SyncNotificationsUseCase(notifRepo, prefs)

            // 1. Health check with detailed diagnostic probe
            val report = healthRepo.checkHealthDetailed(baseUrl)
            if (!report.isHealthy) {
                _uiState.update {
                    it.copy(
                        isConnected = false,
                        isOffline = true,
                        isRefreshing = false,
                        diagnosticReport = report
                    )
                }
                return@launch
            }

            // Restore device token if available
            deviceRepo.restoreDeviceToken()

            // Auto-register device if deviceId is not yet registered
            var currentDeviceId = prefs.deviceId.firstOrNull()
            if (currentDeviceId.isNullOrBlank()) {
                val registerUseCase = com.cyberraksha.ai.domain.usecase.RegisterDeviceUseCase(prefs, deviceRepo)
                val devName = prefs.deviceName.firstOrNull()?.ifEmpty { null } ?: "${android.os.Build.MANUFACTURER} ${android.os.Build.MODEL}".trim()
                val regRes = registerUseCase(devName)
                if (regRes is Result.Success) {
                    currentDeviceId = regRes.data
                    _uiState.update { it.copy(deviceId = currentDeviceId) }
                }
            }

            // 2. Sync notifications
            syncUseCase()

            // 3. Status
            var modules = ProtectionModulesStatus()
            var posture = "PROTECTED"
            when (val statusRes = deviceRepo.getDeviceStatus()) {
                is Result.Success -> {
                    posture = statusRes.data.securityPosture
                    statusRes.data.protectionModules?.let { modules = it }
                }
                is Result.Error -> {}
            }

            // 4. Activity
            var activity: List<SecurityEventItem> = emptyList()
            when (val actRes = deviceRepo.getDeviceActivity(10)) {
                is Result.Success -> {
                    activity = actRes.data.events
                }
                is Result.Error -> {}
            }

            // 5. Query counts from local DB
            val allNotifs = notificationDao.getAllOnce(100)
            val crit = allNotifs.count { it.severity.equals("CRITICAL", ignoreCase = true) && !it.isRead }
            val high = allNotifs.count { it.severity.equals("HIGH", ignoreCase = true) && !it.isRead }

            val lastSync = prefs.lastSyncTimestamp.firstOrNull() ?: 0L
            val lastSyncText = if (lastSync > 0) {
                val diffSeconds = (System.currentTimeMillis() - lastSync) / 1000
                when {
                    diffSeconds < 60 -> "Just now"
                    diffSeconds < 3600 -> "${diffSeconds / 60}m ago"
                    else -> "${diffSeconds / 3600}h ago"
                }
            } else "Never"

            _uiState.update {
                it.copy(
                    isConnected = true,
                    isOffline = false,
                    isRefreshing = false,
                    securityPosture = posture,
                    protectionModules = modules,
                    recentActivity = activity,
                    criticalCount = crit,
                    highCount = high,
                    lastSyncFormatted = lastSyncText
                )
            }
        }
    }
}


