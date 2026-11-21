package com.cyberraksha.ai.ui.keypad

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.cyberraksha.ai.data.remote.*
import com.cyberraksha.ai.data.repository.KeypadProtectionRepository
import com.cyberraksha.ai.data.repository.Result
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

data class KeypadUiState(
    val selectedTab: Int = 0,
    val isLoading: Boolean = false,
    val userFeedbackMessage: String? = null,
    val isErrorMessage: Boolean = false,

    // 1. Family Members
    val members: List<KeypadElderlyUserResponseDto> = emptyList(),
    val newMemberName: String = "",
    val newMemberPhone: String = "",
    val newMemberRelation: String = "Parent",
    val newMemberDevice: String = "Nokia 105",
    val newMemberLang: String = "en",
    val newMemberConsent: Boolean = true,
    val isRegisteringMember: Boolean = false,

    // 2. SMS Analysis
    val smsInputText: String = "",
    val smsInputSender: String = "",
    val smsSelectedElderlyId: Int? = null,
    val smsSelectedLang: String = "en",
    val isAnalyzingSms: Boolean = false,
    val smsAnalysisResult: KeypadSmsCheckResponseDto? = null,

    // 3. Call Risk Check
    val callInputNumber: String = "",
    val callInputIdentity: String = "",
    val callSelectedElderlyId: Int? = null,
    val callSelectedLang: String = "en",
    val isCheckingCall: Boolean = false,
    val callCheckResult: KeypadCallCheckResponseDto? = null,

    // 4. Scam Reporting
    val reportNumber: String = "",
    val reportCategory: String = "DIGITAL_ARREST",
    val reportIdentity: String = "",
    val reportNotes: String = "",
    val isSubmittingReport: Boolean = false,
    val scamReportResult: KeypadScamNumberReportResponseDto? = null,

    // 5. Guardian Alerts
    val alertSummary: KeypadAlertSummaryResponseDto? = null,
    val isLoadingAlerts: Boolean = false,

    // 6. Multilingual Education
    val educationLanguage: String = "en",
    val educationContent: KeypadEducationResponseDto? = null,
    val isLoadingEducation: Boolean = false,

    // 7. Official Helpdesk
    val helpdeskInfo: KeypadOfficialHelpdeskResponseDto? = null,
    val isLoadingHelpdesks: Boolean = false
)

class KeypadProtectionViewModel(
    private val repository: KeypadProtectionRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow(KeypadUiState())
    val uiState: StateFlow<KeypadUiState> = _uiState.asStateFlow()

    init {
        loadInitialData()
    }

    fun selectTab(index: Int) {
        _uiState.update { it.copy(selectedTab = index, userFeedbackMessage = null) }
        when (index) {
            0 -> loadFamilyMembers()
            3 -> loadAlerts()
            4 -> loadEducation(_uiState.value.educationLanguage)
            5 -> loadHelpdesks()
        }
    }

    fun clearFeedback() {
        _uiState.update { it.copy(userFeedbackMessage = null) }
    }

    private fun loadInitialData() {
        loadFamilyMembers()
        loadAlerts()
        loadEducation("en")
        loadHelpdesks()
    }

    // ── 1. Family Registration ───────────────────────────────────────────────

    fun onNewMemberNameChanged(value: String) = _uiState.update { it.copy(newMemberName = value) }
    fun onNewMemberPhoneChanged(value: String) = _uiState.update { it.copy(newMemberPhone = value) }
    fun onNewMemberRelationChanged(value: String) = _uiState.update { it.copy(newMemberRelation = value) }
    fun onNewMemberDeviceChanged(value: String) = _uiState.update { it.copy(newMemberDevice = value) }
    fun onNewMemberLangChanged(value: String) = _uiState.update { it.copy(newMemberLang = value) }
    fun onNewMemberConsentChanged(value: Boolean) = _uiState.update { it.copy(newMemberConsent = value) }

    fun loadFamilyMembers() {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true) }
            when (val res = repository.getElderlyMembers()) {
                is Result.Success -> {
                    _uiState.update { it.copy(members = res.data, isLoading = false) }
                }
                is Result.Error -> {
                    _uiState.update { it.copy(isLoading = false) }
                }
            }
        }
    }

    fun registerFamilyMember() {
        val s = _uiState.value
        if (s.newMemberName.isBlank() || s.newMemberPhone.isBlank()) {
            _uiState.update { it.copy(userFeedbackMessage = "Please enter both name and mobile number.", isErrorMessage = true) }
            return
        }
        viewModelScope.launch {
            _uiState.update { it.copy(isRegisteringMember = true, userFeedbackMessage = null) }
            val req = KeypadElderlyUserCreateDto(
                fullName = s.newMemberName.trim(),
                mobileNumber = s.newMemberPhone.trim(),
                relationship = s.newMemberRelation,
                deviceType = s.newMemberDevice,
                preferredLanguage = s.newMemberLang,
                consentGiven = s.newMemberConsent
            )
            when (val res = repository.registerElderlyMember(req)) {
                is Result.Success -> {
                    _uiState.update {
                        it.copy(
                            isRegisteringMember = false,
                            newMemberName = "",
                            newMemberPhone = "",
                            userFeedbackMessage = "Registered ${res.data.fullName} under Family Shield.",
                            isErrorMessage = false
                        )
                    }
                    loadFamilyMembers()
                    loadAlerts()
                }
                is Result.Error -> {
                    _uiState.update {
                        it.copy(
                            isRegisteringMember = false,
                            userFeedbackMessage = res.message,
                            isErrorMessage = true
                        )
                    }
                }
            }
        }
    }

    fun removeMember(elderlyId: Int) {
        viewModelScope.launch {
            when (val res = repository.removeElderlyMember(elderlyId)) {
                is Result.Success -> {
                    _uiState.update {
                        it.copy(
                            userFeedbackMessage = "Family member removed successfully.",
                            isErrorMessage = false
                        )
                    }
                    loadFamilyMembers()
                    loadAlerts()
                }
                is Result.Error -> {
                    _uiState.update {
                        it.copy(userFeedbackMessage = res.message, isErrorMessage = true) }
                }
            }
        }
    }

    // ── 2. SMS Risk Analysis ─────────────────────────────────────────────────

    fun onSmsTextChanged(value: String) = _uiState.update { it.copy(smsInputText = value) }
    fun onSmsSenderChanged(value: String) = _uiState.update { it.copy(smsInputSender = value) }
    fun onSmsElderlySelected(id: Int?) = _uiState.update { it.copy(smsSelectedElderlyId = id) }
    fun onSmsLangSelected(lang: String) = _uiState.update { it.copy(smsSelectedLang = lang) }

    fun checkSms() {
        val s = _uiState.value
        if (s.smsInputText.isBlank()) {
            _uiState.update { it.copy(userFeedbackMessage = "Please paste the SMS text received on the keypad phone.", isErrorMessage = true) }
            return
        }
        viewModelScope.launch {
            _uiState.update { it.copy(isAnalyzingSms = true, userFeedbackMessage = null) }
            val req = KeypadSmsCheckRequestDto(
                elderlyUserId = s.smsSelectedElderlyId,
                sender = s.smsInputSender.ifBlank { null },
                message = s.smsInputText.trim(),
                preferredLanguage = s.smsSelectedLang
            )
            when (val res = repository.checkSms(req)) {
                is Result.Success -> {
                    _uiState.update {
                        it.copy(
                            isAnalyzingSms = false,
                            smsAnalysisResult = res.data,
                            userFeedbackMessage = "Analysis complete: ${res.data.riskLevel} risk",
                            isErrorMessage = false
                        )
                    }
                    loadAlerts()
                }
                is Result.Error -> {
                    _uiState.update {
                        it.copy(isAnalyzingSms = false, userFeedbackMessage = res.message, isErrorMessage = true)
                    }
                }
            }
        }
    }

    // ── 3. Call Risk Check ───────────────────────────────────────────────────

    fun onCallNumberChanged(value: String) = _uiState.update { it.copy(callInputNumber = value) }
    fun onCallIdentityChanged(value: String) = _uiState.update { it.copy(callInputIdentity = value) }
    fun onCallElderlySelected(id: Int?) = _uiState.update { it.copy(callSelectedElderlyId = id) }
    fun onCallLangSelected(lang: String) = _uiState.update { it.copy(callSelectedLang = lang) }

    fun checkCall() {
        val s = _uiState.value
        if (s.callInputNumber.isBlank()) {
            _uiState.update { it.copy(userFeedbackMessage = "Please enter the incoming phone number.", isErrorMessage = true) }
            return
        }
        viewModelScope.launch {
            _uiState.update { it.copy(isCheckingCall = true, userFeedbackMessage = null) }
            val req = KeypadCallCheckRequestDto(
                elderlyUserId = s.callSelectedElderlyId,
                phoneNumber = s.callInputNumber.trim(),
                claimedCallerIdentity = s.callInputIdentity.ifBlank { null },
                preferredLanguage = s.callSelectedLang
            )
            when (val res = repository.checkCall(req)) {
                is Result.Success -> {
                    _uiState.update {
                        it.copy(
                            isCheckingCall = false,
                            callCheckResult = res.data,
                            userFeedbackMessage = "Status: ${res.data.riskLevel} (${res.data.verificationStatus})",
                            isErrorMessage = false
                        )
                    }
                    loadAlerts()
                }
                is Result.Error -> {
                    _uiState.update {
                        it.copy(isCheckingCall = false, userFeedbackMessage = res.message, isErrorMessage = true)
                    }
                }
            }
        }
    }

    // ── 4. Scam Reporting ────────────────────────────────────────────────────

    fun onReportNumberChanged(value: String) = _uiState.update { it.copy(reportNumber = value) }
    fun onReportCategoryChanged(value: String) = _uiState.update { it.copy(reportCategory = value) }
    fun onReportIdentityChanged(value: String) = _uiState.update { it.copy(reportIdentity = value) }
    fun onReportNotesChanged(value: String) = _uiState.update { it.copy(reportNotes = value) }

    fun submitScamReport() {
        val s = _uiState.value
        if (s.reportNumber.isBlank()) {
            _uiState.update { it.copy(userFeedbackMessage = "Please enter the phone number to report.", isErrorMessage = true) }
            return
        }
        viewModelScope.launch {
            _uiState.update { it.copy(isSubmittingReport = true, userFeedbackMessage = null) }
            val req = KeypadScamNumberReportRequestDto(
                phoneNumber = s.reportNumber.trim(),
                fraudCategory = s.reportCategory,
                claimedCallerIdentity = s.reportIdentity.ifBlank { null },
                evidenceNotes = s.reportNotes.ifBlank { null }
            )
            when (val res = repository.reportScamNumber(req)) {
                is Result.Success -> {
                    _uiState.update {
                        it.copy(
                            isSubmittingReport = false,
                            scamReportResult = res.data,
                            reportNumber = "",
                            reportIdentity = "",
                            reportNotes = "",
                            userFeedbackMessage = "Report submitted! Verified status: ${res.data.verificationStatus}",
                            isErrorMessage = false
                        )
                    }
                    loadAlerts()
                }
                is Result.Error -> {
                    _uiState.update {
                        it.copy(isSubmittingReport = false, userFeedbackMessage = res.message, isErrorMessage = true)
                    }
                }
            }
        }
    }

    // ── 5. Guardian Alerts ───────────────────────────────────────────────────

    fun loadAlerts() {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoadingAlerts = true) }
            when (val res = repository.getAlertSummary()) {
                is Result.Success -> {
                    _uiState.update { it.copy(alertSummary = res.data, isLoadingAlerts = false) }
                }
                is Result.Error -> {
                    _uiState.update { it.copy(isLoadingAlerts = false) }
                }
            }
        }
    }

    fun acknowledgeAlert(incidentId: Int) {
        viewModelScope.launch {
            when (val res = repository.acknowledgeAlert(incidentId)) {
                is Result.Success -> {
                    _uiState.update {
                        it.copy(userFeedbackMessage = "Incident marked as reviewed.", isErrorMessage = false)
                    }
                    loadAlerts()
                }
                is Result.Error -> {
                    _uiState.update {
                        it.copy(userFeedbackMessage = res.message, isErrorMessage = true)
                    }
                }
            }
        }
    }

    // ── 6. Multilingual Education ────────────────────────────────────────────

    fun setEducationLanguage(lang: String) {
        _uiState.update { it.copy(educationLanguage = lang) }
        loadEducation(lang)
    }

    fun loadEducation(lang: String) {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoadingEducation = true) }
            when (val res = repository.getEducation(lang)) {
                is Result.Success -> {
                    _uiState.update {
                        it.copy(educationContent = res.data, isLoadingEducation = false)
                    }
                }
                is Result.Error -> {
                    _uiState.update { it.copy(isLoadingEducation = false) }
                }
            }
        }
    }

    // ── 7. Official Helpdesks ────────────────────────────────────────────────

    fun loadHelpdesks() {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoadingHelpdesks = true) }
            when (val res = repository.getOfficialHelpdesks()) {
                is Result.Success -> {
                    _uiState.update {
                        it.copy(helpdeskInfo = res.data, isLoadingHelpdesks = false)
                    }
                }
                is Result.Error -> {
                    _uiState.update { it.copy(isLoadingHelpdesks = false) }
                }
            }
        }
    }
}

