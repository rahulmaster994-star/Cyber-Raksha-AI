package com.cyberraksha.ai.ui.settings

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.cyberraksha.ai.core.AppPreferences
import com.cyberraksha.ai.data.remote.NetworkModule
import com.cyberraksha.ai.data.repository.DeviceRepository
import com.cyberraksha.ai.data.repository.HealthRepository
import com.cyberraksha.ai.data.repository.Result
import com.cyberraksha.ai.domain.usecase.RegisterDeviceUseCase
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.firstOrNull
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

data class SettingsUiState(
    val backendUrl: String = "",
    val deviceName: String = "",
    val deviceId: String = "",
    val notificationsEnabled: Boolean = true,
    val minSeverity: String = "LOW",
    val isTesting: Boolean = false,
    val statusMessage: String? = null,
    val isSuccess: Boolean = false,
    val appVersion: String = "1.0.0"
)

class SettingsViewModel(
    private val prefs: AppPreferences
) : ViewModel() {

    private val _uiState = MutableStateFlow(SettingsUiState())
    val uiState: StateFlow<SettingsUiState> = _uiState.asStateFlow()

    init {
        viewModelScope.launch {
            val url = prefs.backendUrl.firstOrNull() ?: AppPreferences.DEFAULT_BACKEND_URL
            val name = prefs.deviceName.firstOrNull() ?: ""
            val id = prefs.deviceId.firstOrNull() ?: ""
            val notif = prefs.notificationsEnabled.firstOrNull() ?: true
            val sev = prefs.minSeverity.firstOrNull() ?: "LOW"

            _uiState.update {
                it.copy(
                    backendUrl = url,
                    deviceName = name,
                    deviceId = id,
                    notificationsEnabled = notif,
                    minSeverity = sev
                )
            }
        }
    }

    fun onBackendUrlChanged(url: String) {
        _uiState.update { it.copy(backendUrl = url, statusMessage = null) }
    }

    fun onNotificationsToggled(enabled: Boolean) {
        viewModelScope.launch {
            prefs.setNotificationsEnabled(enabled)
            _uiState.update { it.copy(notificationsEnabled = enabled) }
        }
    }

    fun onMinSeverityChanged(severity: String) {
        viewModelScope.launch {
            prefs.setMinSeverity(severity)
            _uiState.update { it.copy(minSeverity = severity) }
        }
    }

    fun saveBackendUrl() {
        val url = _uiState.value.backendUrl.trim()
        viewModelScope.launch {
            _uiState.update { it.copy(isTesting = true, statusMessage = null) }
            val api = NetworkModule.createApiService(url)
            val healthRepo = HealthRepository(api)
            val isHealthy = healthRepo.isBackendHealthy()

            if (isHealthy) {
                prefs.saveBackendUrl(url)
                _uiState.update {
                    it.copy(
                        isTesting = false,
                        isSuccess = true,
                        statusMessage = "Connected successfully. Configuration saved."
                    )
                }
            } else {
                _uiState.update {
                    it.copy(
                        isTesting = false,
                        isSuccess = false,
                        statusMessage = "Could not reach Cyber Raksha backend at $url."
                    )
                }
            }
        }
    }

    fun reregisterDevice() {
        val url = _uiState.value.backendUrl.trim()
        val name = _uiState.value.deviceName.trim().ifEmpty { "Android Device" }

        viewModelScope.launch {
            _uiState.update { it.copy(isTesting = true, statusMessage = null) }
            val api = NetworkModule.createApiService(url)
            val deviceRepo = DeviceRepository(api, prefs)
            val registerUseCase = RegisterDeviceUseCase(prefs, deviceRepo)

            when (val res = registerUseCase(name)) {
                is Result.Success -> {
                    _uiState.update {
                        it.copy(
                            isTesting = false,
                            isSuccess = true,
                            deviceId = res.data,
                            statusMessage = "Device re-registered successfully."
                        )
                    }
                }
                is Result.Error -> {
                    _uiState.update {
                        it.copy(
                            isTesting = false,
                            isSuccess = false,
                            statusMessage = "Re-registration failed: ${res.message}"
                        )
                    }
                }
            }
        }
    }
}

