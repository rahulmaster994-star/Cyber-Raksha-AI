package com.cyberraksha.ai.ui.threat_history

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.cyberraksha.ai.data.remote.ThreatHistoryItem
import com.cyberraksha.ai.data.repository.MobileProtectionRepository
import com.cyberraksha.ai.data.repository.Result
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

data class ThreatHistoryUiState(
    val isLoading: Boolean = false,
    val items: List<ThreatHistoryItem> = emptyList(),
    val filteredItems: List<ThreatHistoryItem> = emptyList(),
    val selectedFilter: String = "ALL",
    val errorMessage: String? = null
)

class ThreatHistoryViewModel(
    private val repository: MobileProtectionRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow(ThreatHistoryUiState())
    val uiState: StateFlow<ThreatHistoryUiState> = _uiState.asStateFlow()

    init {
        loadThreatHistory()
    }

    fun loadThreatHistory() {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true, errorMessage = null) }
            when (val result = repository.getThreatHistory()) {
                is Result.Success -> {
                    val allItems = result.data.items
                    _uiState.update {
                        it.copy(
                            isLoading = false,
                            items = allItems,
                            filteredItems = filterList(allItems, it.selectedFilter)
                        )
                    }
                }
                is Result.Error -> {
                    _uiState.update {
                        it.copy(
                            isLoading = false,
                            errorMessage = result.message
                        )
                    }
                }
            }
        }
    }

    fun setFilter(filter: String) {
        _uiState.update {
            it.copy(
                selectedFilter = filter,
                filteredItems = filterList(it.items, filter)
            )
        }
    }

    private fun filterList(items: List<ThreatHistoryItem>, filter: String): List<ThreatHistoryItem> {
        return when (filter) {
            "SMS" -> items.filter { it.threatType.equals("SMS", ignoreCase = true) }
            "CALL" -> items.filter { it.threatType.equals("CALL", ignoreCase = true) }
            "HIGH_CRITICAL" -> items.filter {
                it.riskLevel.equals("CRITICAL", ignoreCase = true) || it.riskLevel.equals("HIGH", ignoreCase = true)
            }
            else -> items
        }
    }
}

