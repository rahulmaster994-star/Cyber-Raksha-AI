package com.cyberraksha.ai.ui.alerts

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.cyberraksha.ai.core.AppPreferences
import com.cyberraksha.ai.data.local.NotificationDao
import com.cyberraksha.ai.data.local.NotificationEntity
import com.cyberraksha.ai.data.remote.NetworkModule
import com.cyberraksha.ai.data.repository.NotificationRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.firstOrNull
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

data class AlertsUiState(
    val notifications: List<NotificationEntity> = emptyList(),
    val filteredNotifications: List<NotificationEntity> = emptyList(),
    val selectedSeverity: String = "ALL",
    val unreadOnly: Boolean = false,
    val isLoading: Boolean = false
)

class AlertsViewModel(
    private val prefs: AppPreferences,
    private val dao: NotificationDao
) : ViewModel() {

    private val _uiState = MutableStateFlow(AlertsUiState())
    val uiState: StateFlow<AlertsUiState> = _uiState.asStateFlow()

    private var repository: NotificationRepository? = null

    init {
        viewModelScope.launch {
            val baseUrl = prefs.backendUrl.firstOrNull() ?: AppPreferences.DEFAULT_BACKEND_URL
            val api = NetworkModule.createApiService(baseUrl)
            repository = NotificationRepository(api, dao)

            // Sync from backend in background
            repository?.syncFromBackend()
        }

        // Observe local database
        viewModelScope.launch {
            dao.getAll(200).collect { list ->
                _uiState.update { current ->
                    current.copy(
                        notifications = list,
                        filteredNotifications = filterList(list, current.selectedSeverity, current.unreadOnly)
                    )
                }
            }
        }
    }

    fun setSeverityFilter(severity: String) {
        _uiState.update { current ->
            current.copy(
                selectedSeverity = severity,
                filteredNotifications = filterList(current.notifications, severity, current.unreadOnly)
            )
        }
    }

    fun toggleUnreadOnly() {
        _uiState.update { current ->
            val newUnread = !current.unreadOnly
            current.copy(
                unreadOnly = newUnread,
                filteredNotifications = filterList(current.notifications, current.selectedSeverity, newUnread)
            )
        }
    }

    fun markRead(id: Int) {
        viewModelScope.launch {
            repository?.markRead(id) ?: dao.markRead(id)
        }
    }

    fun markAllRead() {
        viewModelScope.launch {
            repository?.markAllRead() ?: dao.markAllRead()
        }
    }

    fun delete(id: Int) {
        viewModelScope.launch {
            repository?.delete(id) ?: dao.delete(id)
        }
    }

    fun clearAll() {
        viewModelScope.launch {
            repository?.clearAll() ?: dao.clearAll()
        }
    }

    private fun filterList(
        list: List<NotificationEntity>,
        severity: String,
        unreadOnly: Boolean
    ): List<NotificationEntity> {
        return list.filter { item ->
            val matchSeverity = if (severity == "ALL") true else item.severity.equals(severity, ignoreCase = true)
            val matchUnread = if (unreadOnly) !item.isRead else true
            matchSeverity && matchUnread
        }
    }
}

