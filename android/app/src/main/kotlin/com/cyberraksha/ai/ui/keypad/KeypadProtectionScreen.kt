package com.cyberraksha.ai.ui.keypad

import android.content.Intent
import android.net.Uri
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.cyberraksha.ai.data.remote.*
import com.cyberraksha.ai.ui.theme.*

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun KeypadProtectionScreen(
    viewModel: KeypadProtectionViewModel,
    onBack: () -> Unit
) {
    val state by viewModel.uiState.collectAsState()
    val context = LocalContext.current

    val tabs = listOf(
        "Family",
        "SMS Scan",
        "Call Check",
        "Report Scam",
        "Alerts",
        "Education",
        "Helpline"
    )

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Column {
                        Text(
                            text = "Keypad User Protection",
                            fontSize = 18.sp,
                            fontWeight = FontWeight.Bold,
                            color = TextPrimary
                        )
                        Text(
                            text = "Guardian Shield for Traditional Phones",
                            fontSize = 12.sp,
                            color = CyberCyan
                        )
                    }
                },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(
                            imageVector = Icons.Default.ArrowBack,
                            contentDescription = "Back",
                            tint = TextPrimary
                        )
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = DarkBackground
                )
            )
        },
        containerColor = DarkBackground
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
        ) {
            // Notice banner: Guardian-Assisted Architecture
            Card(
                colors = CardDefaults.cardColors(containerColor = DarkSurfaceVar),
                shape = RoundedCornerShape(0.dp),
                modifier = Modifier.fillMaxWidth()
            ) {
                Row(
                    modifier = Modifier.padding(horizontal = 14.dp, vertical = 8.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Icon(
                        imageVector = Icons.Default.Info,
                        contentDescription = null,
                        tint = CyberCyan,
                        modifier = Modifier.size(16.dp)
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    Text(
                        text = "Protects Nokia, itel, Samsung, Lava, Jio Bharat via guardian intelligence. No carrier bypass required.",
                        fontSize = 11.sp,
                        color = TextSecondary,
                        lineHeight = 14.sp
                    )
                }
            }

            // Tabs
            ScrollableTabRow(
                selectedTabIndex = state.selectedTab,
                containerColor = DarkSurface,
                contentColor = CyberCyan,
                edgePadding = 8.dp
            ) {
                tabs.forEachIndexed { index, title ->
                    Tab(
                        selected = state.selectedTab == index,
                        onClick = { viewModel.selectTab(index) },
                        text = {
                            Text(
                                text = title,
                                fontSize = 13.sp,
                                fontWeight = if (state.selectedTab == index) FontWeight.Bold else FontWeight.Normal,
                                color = if (state.selectedTab == index) CyberCyan else TextSecondary
                            )
                        }
                    )
                }
            }

            // Feedback / Status Snackbar Banner
            state.userFeedbackMessage?.let { msg ->
                val bannerBg = if (state.isErrorMessage) SeverityCritical.copy(alpha = 0.2f) else CyberCyanDark.copy(alpha = 0.25f)
                val textCol = if (state.isErrorMessage) SeverityCritical else CyberCyan
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .background(bannerBg)
                        .padding(horizontal = 16.dp, vertical = 8.dp),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(text = msg, color = textCol, fontSize = 12.sp, modifier = Modifier.weight(1f))
                    IconButton(onClick = { viewModel.clearFeedback() }, modifier = Modifier.size(20.dp)) {
                        Icon(imageVector = Icons.Default.Close, contentDescription = "Close", tint = textCol, modifier = Modifier.size(14.dp))
                    }
                }
            }

            // Tab Content
            Box(modifier = Modifier.fillMaxSize()) {
                when (state.selectedTab) {
                    0 -> FamilyRegistrationTab(viewModel, state)
                    1 -> SmsScannerTab(viewModel, state)
                    2 -> CallRiskTab(viewModel, state)
                    3 -> ReportScamTab(viewModel, state)
                    4 -> AlertsTab(viewModel, state)
                    5 -> EducationTab(viewModel, state)
                    6 -> HelplineTab(viewModel, state)
                }
            }
        }
    }
}

// ── Tab 0: Family Registration ──────────────────────────────────────────────

@Composable
fun FamilyRegistrationTab(viewModel: KeypadProtectionViewModel, state: KeypadUiState) {
    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp)
    ) {
        item {
            Card(
                colors = CardDefaults.cardColors(containerColor = DarkSurface),
                shape = RoundedCornerShape(12.dp),
                modifier = Modifier.fillMaxWidth()
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text(
                        text = "Register Elderly Family Member",
                        fontWeight = FontWeight.Bold,
                        color = TextPrimary,
                        fontSize = 16.sp
                    )
                    Text(
                        text = "Link a keypad/feature phone under your guardian shield. Multiple dependents supported.",
                        fontSize = 12.sp,
                        color = TextSecondary
                    )

                    Spacer(modifier = Modifier.height(14.dp))

                    OutlinedTextField(
                        value = state.newMemberName,
                        onValueChange = { viewModel.onNewMemberNameChanged(it) },
                        label = { Text("Full Name (e.g. Ramesh Kumar)") },
                        modifier = Modifier.fillMaxWidth(),
                        colors = outlinedTextFieldColors()
                    )

                    Spacer(modifier = Modifier.height(10.dp))

                    OutlinedTextField(
                        value = state.newMemberPhone,
                        onValueChange = { viewModel.onNewMemberPhoneChanged(it) },
                        label = { Text("Mobile Number (10 digits)") },
                        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Phone),
                        modifier = Modifier.fillMaxWidth(),
                        colors = outlinedTextFieldColors()
                    )

                    Spacer(modifier = Modifier.height(10.dp))

                    Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        OutlinedTextField(
                            value = state.newMemberRelation,
                            onValueChange = { viewModel.onNewMemberRelationChanged(it) },
                            label = { Text("Relationship") },
                            modifier = Modifier.weight(1f),
                            colors = outlinedTextFieldColors()
                        )
                        OutlinedTextField(
                            value = state.newMemberDevice,
                            onValueChange = { viewModel.onNewMemberDeviceChanged(it) },
                            label = { Text("Device Model") },
                            modifier = Modifier.weight(1f),
                            colors = outlinedTextFieldColors()
                        )
                    }

                    Spacer(modifier = Modifier.height(10.dp))

                    // Language Selection
                    Text("Preferred Alert Language:", fontSize = 12.sp, color = TextSecondary)
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        listOf("en" to "English", "hi" to "हिन्दी", "kn" to "ಕನ್ನಡ").forEach { (code, label) ->
                            FilterChip(
                                selected = state.newMemberLang == code,
                                onClick = { viewModel.onNewMemberLangChanged(code) },
                                label = { Text(label, fontSize = 12.sp) },
                                colors = FilterChipDefaults.filterChipColors(
                                    selectedContainerColor = CyberCyan,
                                    selectedLabelColor = Color.Black
                                )
                            )
                        }
                    }

                    Spacer(modifier = Modifier.height(10.dp))

                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Checkbox(
                            checked = state.newMemberConsent,
                            onCheckedChange = { viewModel.onNewMemberConsentChanged(it) },
                            colors = CheckboxDefaults.colors(checkedColor = CyberCyan)
                        )
                        Spacer(modifier = Modifier.width(6.dp))
                        Text(
                            text = "Elderly member has consented to guardian assistance.",
                            fontSize = 11.sp,
                            color = TextSecondary
                        )
                    }

                    Spacer(modifier = Modifier.height(12.dp))

                    Button(
                        onClick = { viewModel.registerFamilyMember() },
                        enabled = !state.isRegisteringMember,
                        colors = ButtonDefaults.buttonColors(containerColor = CyberCyan, contentColor = Color.Black),
                        shape = RoundedCornerShape(8.dp),
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        if (state.isRegisteringMember) {
                            CircularProgressIndicator(modifier = Modifier.size(18.dp), color = Color.Black)
                        } else {
                            Icon(imageVector = Icons.Default.Add, contentDescription = null, modifier = Modifier.size(18.dp))
                            Spacer(modifier = Modifier.width(8.dp))
                            Text("Add to Family Shield", fontWeight = FontWeight.Bold)
                        }
                    }
                }
            }
        }

        item {
            Text(
                text = "Protected Family Members (${state.members.size})",
                fontWeight = FontWeight.Bold,
                color = TextPrimary,
                fontSize = 15.sp
            )
        }

        if (state.members.isEmpty()) {
            item {
                Card(
                    colors = CardDefaults.cardColors(containerColor = DarkSurface),
                    shape = RoundedCornerShape(8.dp),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Box(modifier = Modifier.padding(20.dp), contentAlignment = Alignment.Center) {
                        Text(
                            text = "No elderly family members registered yet. Add a family member above to start monitoring their incoming threats.",
                            fontSize = 13.sp,
                            color = TextSecondary
                        )
                    }
                }
            }
        } else {
            items(state.members) { m ->
                Card(
                    colors = CardDefaults.cardColors(containerColor = DarkSurface),
                    shape = RoundedCornerShape(10.dp),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(14.dp),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Column(modifier = Modifier.weight(1f)) {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Text(
                                    text = m.fullName,
                                    fontWeight = FontWeight.Bold,
                                    fontSize = 15.sp,
                                    color = TextPrimary
                                )
                                Spacer(modifier = Modifier.width(8.dp))
                                Surface(
                                    color = CyberCyan.copy(alpha = 0.15f),
                                    shape = RoundedCornerShape(4.dp)
                                ) {
                                    Text(
                                        text = m.relationship,
                                        color = CyberCyan,
                                        fontSize = 10.sp,
                                        modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                                    )
                                }
                            }
                            Spacer(modifier = Modifier.height(4.dp))
                            Text(
                                text = "Phone: ${m.maskedMobileNumber} • ${m.deviceType}",
                                fontSize = 12.sp,
                                color = TextSecondary
                            )
                            Text(
                                text = "Preferred Lang: ${m.preferredLanguage.uppercase()}",
                                fontSize = 11.sp,
                                color = TextDisabled
                            )
                        }
                        IconButton(onClick = { viewModel.removeMember(m.id) }) {
                            Icon(
                                imageVector = Icons.Default.Delete,
                                contentDescription = "Remove",
                                tint = SeverityCritical.copy(alpha = 0.8f),
                                modifier = Modifier.size(20.dp)
                            )
                        }
                    }
                }
            }
        }
    }
}

// ── Tab 1: SMS Threat Scanner ───────────────────────────────────────────────

@Composable
fun SmsScannerTab(viewModel: KeypadProtectionViewModel, state: KeypadUiState) {
    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp)
    ) {
        item {
            Card(
                colors = CardDefaults.cardColors(containerColor = DarkSurface),
                shape = RoundedCornerShape(12.dp),
                modifier = Modifier.fillMaxWidth()
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text(
                        text = "Keypad Phone SMS Threat Scanner",
                        fontWeight = FontWeight.Bold,
                        color = TextPrimary,
                        fontSize = 16.sp
                    )
                    Text(
                        text = "Paste text from an SMS received on your elder's keypad phone to detect Digital Arrest, fake electricity disconnection, and KYC scams.",
                        fontSize = 12.sp,
                        color = TextSecondary
                    )

                    Spacer(modifier = Modifier.height(12.dp))

                    OutlinedTextField(
                        value = state.smsInputSender,
                        onValueChange = { viewModel.onSmsSenderChanged(it) },
                        label = { Text("Sender ID / Phone (e.g. +919876543210 or VK-BESCOM)") },
                        modifier = Modifier.fillMaxWidth(),
                        colors = outlinedTextFieldColors()
                    )

                    Spacer(modifier = Modifier.height(10.dp))

                    OutlinedTextField(
                        value = state.smsInputText,
                        onValueChange = { viewModel.onSmsTextChanged(it) },
                        label = { Text("Exact SMS Message Text") },
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(110.dp),
                        maxLines = 5,
                        colors = outlinedTextFieldColors()
                    )

                    Spacer(modifier = Modifier.height(10.dp))

                    Text("Explanation Language:", fontSize = 12.sp, color = TextSecondary)
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        listOf("en" to "English", "hi" to "हिन्दी", "kn" to "ಕನ್ನಡ").forEach { (code, label) ->
                            FilterChip(
                                selected = state.smsSelectedLang == code,
                                onClick = { viewModel.onSmsLangSelected(code) },
                                label = { Text(label, fontSize = 12.sp) },
                                colors = FilterChipDefaults.filterChipColors(
                                    selectedContainerColor = CyberCyan,
                                    selectedLabelColor = Color.Black
                                )
                            )
                        }
                    }

                    Spacer(modifier = Modifier.height(12.dp))

                    Button(
                        onClick = { viewModel.checkSms() },
                        enabled = !state.isAnalyzingSms,
                        colors = ButtonDefaults.buttonColors(containerColor = CyberCyan, contentColor = Color.Black),
                        shape = RoundedCornerShape(8.dp),
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        if (state.isAnalyzingSms) {
                            CircularProgressIndicator(modifier = Modifier.size(18.dp), color = Color.Black)
                        } else {
                            Icon(imageVector = Icons.Default.Search, contentDescription = null, modifier = Modifier.size(18.dp))
                            Spacer(modifier = Modifier.width(8.dp))
                            Text("Analyze Keypad SMS", fontWeight = FontWeight.Bold)
                        }
                    }
                }
            }
        }

        // Analysis Result Card
        state.smsAnalysisResult?.let { res ->
            item {
                val sevColor = when (res.riskLevel) {
                    "CRITICAL" -> SeverityCritical
                    "HIGH" -> SeverityHigh
                    "MEDIUM" -> SeverityMedium
                    else -> SeverityLow
                }

                Card(
                    colors = CardDefaults.cardColors(containerColor = DarkSurface),
                    shape = RoundedCornerShape(12.dp),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Text(
                                text = "Analysis Result",
                                fontWeight = FontWeight.Bold,
                                color = TextPrimary,
                                fontSize = 16.sp
                            )
                            Surface(
                                color = sevColor.copy(alpha = 0.2f),
                                shape = RoundedCornerShape(6.dp)
                            ) {
                                Text(
                                    text = "${res.riskLevel} (${res.riskScore.toInt()}%)",
                                    color = sevColor,
                                    fontWeight = FontWeight.Bold,
                                    fontSize = 12.sp,
                                    modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp)
                                )
                            }
                        }

                        Spacer(modifier = Modifier.height(8.dp))
                        Text(
                            text = "Fraud Category: ${res.category}",
                            color = CyberCyan,
                            fontSize = 12.sp,
                            fontWeight = FontWeight.SemiBold
                        )

                        Spacer(modifier = Modifier.height(10.dp))
                        Text(
                            text = res.explanation,
                            color = TextPrimary,
                            fontSize = 13.sp,
                            lineHeight = 18.sp
                        )

                        Spacer(modifier = Modifier.height(12.dp))
                        Divider(color = DarkOutline)
                        Spacer(modifier = Modifier.height(10.dp))

                        Text(
                            text = "Recommended Action for Elder:",
                            fontWeight = FontWeight.Bold,
                            color = SeverityHigh,
                            fontSize = 12.sp
                        )
                        Text(
                            text = res.recommendedAction,
                            color = TextSecondary,
                            fontSize = 12.sp
                        )

                        Spacer(modifier = Modifier.height(10.dp))
                        Text(
                            text = "Official Helpline: ${res.helpline}",
                            color = CyberCyan,
                            fontSize = 11.sp
                        )

                        Spacer(modifier = Modifier.height(8.dp))
                        Text(
                            text = res.disclaimer,
                            fontSize = 10.sp,
                            color = TextDisabled
                        )
                    }
                }
            }
        }
    }
}

// ── Tab 2: Call Risk Check ──────────────────────────────────────────────────

@Composable
fun CallRiskTab(viewModel: KeypadProtectionViewModel, state: KeypadUiState) {
    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp)
    ) {
        item {
            Card(
                colors = CardDefaults.cardColors(containerColor = DarkSurface),
                shape = RoundedCornerShape(12.dp),
                modifier = Modifier.fillMaxWidth()
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text(
                        text = "Keypad Phone Call Reputation Check",
                        fontWeight = FontWeight.Bold,
                        color = TextPrimary,
                        fontSize = 16.sp
                    )
                    Text(
                        text = "Check an unknown incoming call received on a keypad phone against national cyber threat records. Single reports are protected against false positives.",
                        fontSize = 12.sp,
                        color = TextSecondary
                    )

                    Spacer(modifier = Modifier.height(12.dp))

                    OutlinedTextField(
                        value = state.callInputNumber,
                        onValueChange = { viewModel.onCallNumberChanged(it) },
                        label = { Text("Caller Phone Number") },
                        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Phone),
                        modifier = Modifier.fillMaxWidth(),
                        colors = outlinedTextFieldColors()
                    )

                    Spacer(modifier = Modifier.height(10.dp))

                    OutlinedTextField(
                        value = state.callInputIdentity,
                        onValueChange = { viewModel.onCallIdentityChanged(it) },
                        label = { Text("Claimed Identity (e.g. Mumbai Police, BESCOM)") },
                        modifier = Modifier.fillMaxWidth(),
                        colors = outlinedTextFieldColors()
                    )

                    Spacer(modifier = Modifier.height(10.dp))

                    Text("Explanation Language:", fontSize = 12.sp, color = TextSecondary)
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        listOf("en" to "English", "hi" to "हिन्दी", "kn" to "ಕನ್ನಡ").forEach { (code, label) ->
                            FilterChip(
                                selected = state.callSelectedLang == code,
                                onClick = { viewModel.onCallLangSelected(code) },
                                label = { Text(label, fontSize = 12.sp) },
                                colors = FilterChipDefaults.filterChipColors(
                                    selectedContainerColor = CyberCyan,
                                    selectedLabelColor = Color.Black
                                )
                            )
                        }
                    }

                    Spacer(modifier = Modifier.height(12.dp))

                    Button(
                        onClick = { viewModel.checkCall() },
                        enabled = !state.isCheckingCall,
                        colors = ButtonDefaults.buttonColors(containerColor = CyberCyan, contentColor = Color.Black),
                        shape = RoundedCornerShape(8.dp),
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        if (state.isCheckingCall) {
                            CircularProgressIndicator(modifier = Modifier.size(18.dp), color = Color.Black)
                        } else {
                            Icon(imageVector = Icons.Default.Call, contentDescription = null, modifier = Modifier.size(18.dp))
                            Spacer(modifier = Modifier.width(8.dp))
                            Text("Check Call Reputation", fontWeight = FontWeight.Bold)
                        }
                    }
                }
            }
        }

        // Call Result Card
        state.callCheckResult?.let { res ->
            item {
                val sevColor = when (res.riskLevel) {
                    "CRITICAL" -> SeverityCritical
                    "HIGH" -> SeverityHigh
                    "MEDIUM" -> SeverityMedium
                    "UNKNOWN" -> TextSecondary
                    else -> SeverityLow
                }

                Card(
                    colors = CardDefaults.cardColors(containerColor = DarkSurface),
                    shape = RoundedCornerShape(12.dp),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Text(
                                text = res.normalizedNumber,
                                fontWeight = FontWeight.Bold,
                                color = TextPrimary,
                                fontSize = 15.sp
                            )
                            Surface(
                                color = sevColor.copy(alpha = 0.2f),
                                shape = RoundedCornerShape(6.dp)
                            ) {
                                Text(
                                    text = res.riskLevel,
                                    color = sevColor,
                                    fontWeight = FontWeight.Bold,
                                    fontSize = 12.sp,
                                    modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp)
                                )
                            }
                        }

                        Spacer(modifier = Modifier.height(6.dp))
                        Text(
                            text = "Verification: ${res.verificationStatus} • Reports: ${res.reportCount}",
                            fontSize = 11.sp,
                            color = if (res.verificationStatus == "CORROBORATED") SeverityHigh else TextSecondary
                        )

                        Spacer(modifier = Modifier.height(10.dp))
                        Text(
                            text = res.explanation,
                            color = TextPrimary,
                            fontSize = 13.sp,
                            lineHeight = 18.sp
                        )

                        Spacer(modifier = Modifier.height(12.dp))
                        Text(
                            text = "Advice: ${res.recommendedAction}",
                            color = SeverityMedium,
                            fontSize = 12.sp
                        )

                        Spacer(modifier = Modifier.height(8.dp))
                        Text(
                            text = res.disclaimer,
                            fontSize = 10.sp,
                            color = TextDisabled
                        )
                    }
                }
            }
        }
    }
}

// ── Tab 3: Report Scam Number ────────────────────────────────────────────────

@Composable
fun ReportScamTab(viewModel: KeypadProtectionViewModel, state: KeypadUiState) {
    val categories = listOf(
        "DIGITAL_ARREST" to "Digital Arrest (Police/CBI)",
        "ELECTRICITY_BILL" to "Electricity Disconnection",
        "BANK_KYC" to "Bank KYC / SIM Expiry",
        "LOTTERY_PRIZE" to "Lottery / KBC Cash Prize",
        "PENSION_SCHEME" to "Pension / Govt Scheme",
        "SUSPICIOUS_CALL" to "General Fraud Call"
    )

    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp)
    ) {
        item {
            Card(
                colors = CardDefaults.cardColors(containerColor = DarkSurface),
                shape = RoundedCornerShape(12.dp),
                modifier = Modifier.fillMaxWidth()
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text(
                        text = "Report Scam Number Targeting Keypad User",
                        fontWeight = FontWeight.Bold,
                        color = TextPrimary,
                        fontSize = 16.sp
                    )
                    Text(
                        text = "Contribute predatory numbers into the cyber intelligence repository to protect other elderly families. Maintained with audit logging and anti-Sybil protection.",
                        fontSize = 12.sp,
                        color = TextSecondary
                    )

                    Spacer(modifier = Modifier.height(14.dp))

                    OutlinedTextField(
                        value = state.reportNumber,
                        onValueChange = { viewModel.onReportNumberChanged(it) },
                        label = { Text("Predatory Phone Number") },
                        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Phone),
                        modifier = Modifier.fillMaxWidth(),
                        colors = outlinedTextFieldColors()
                    )

                    Spacer(modifier = Modifier.height(10.dp))

                    Text("Fraud Category:", fontSize = 12.sp, color = TextSecondary)
                    Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                        categories.forEach { (catId, catLabel) ->
                            Row(
                                verticalAlignment = Alignment.CenterVertically,
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .clickable { viewModel.onReportCategoryChanged(catId) }
                            ) {
                                RadioButton(
                                    selected = state.reportCategory == catId,
                                    onClick = { viewModel.onReportCategoryChanged(catId) },
                                    colors = RadioButtonDefaults.colors(selectedColor = CyberCyan)
                                )
                                Text(text = catLabel, fontSize = 12.sp, color = TextPrimary)
                            }
                        }
                    }

                    Spacer(modifier = Modifier.height(8.dp))

                    OutlinedTextField(
                        value = state.reportIdentity,
                        onValueChange = { viewModel.onReportIdentityChanged(it) },
                        label = { Text("Claimed Identity (e.g. Fake CBI Inspector)") },
                        modifier = Modifier.fillMaxWidth(),
                        colors = outlinedTextFieldColors()
                    )

                    Spacer(modifier = Modifier.height(10.dp))

                    OutlinedTextField(
                        value = state.reportNotes,
                        onValueChange = { viewModel.onReportNotesChanged(it) },
                        label = { Text("Evidence Notes (What did the scammer say?)") },
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(90.dp),
                        maxLines = 4,
                        colors = outlinedTextFieldColors()
                    )

                    Spacer(modifier = Modifier.height(12.dp))

                    Button(
                        onClick = { viewModel.submitScamReport() },
                        enabled = !state.isSubmittingReport,
                        colors = ButtonDefaults.buttonColors(containerColor = SeverityCritical, contentColor = Color.White),
                        shape = RoundedCornerShape(8.dp),
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        if (state.isSubmittingReport) {
                            CircularProgressIndicator(modifier = Modifier.size(18.dp), color = Color.White)
                        } else {
                            Icon(imageVector = Icons.Default.Warning, contentDescription = null, modifier = Modifier.size(18.dp))
                            Spacer(modifier = Modifier.width(8.dp))
                            Text("Submit Threat Intelligence Report", fontWeight = FontWeight.Bold)
                        }
                    }
                }
            }
        }

        state.scamReportResult?.let { res ->
            item {
                Card(
                    colors = CardDefaults.cardColors(containerColor = DarkSurface),
                    shape = RoundedCornerShape(10.dp),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Column(modifier = Modifier.padding(14.dp)) {
                        Text(
                            text = res.message,
                            color = CyberCyan,
                            fontWeight = FontWeight.Bold,
                            fontSize = 13.sp
                        )
                        Spacer(modifier = Modifier.height(4.dp))
                        Text(
                            text = "Status: ${res.verificationStatus} • Number: ${res.normalizedNumber}",
                            fontSize = 11.sp,
                            color = TextSecondary
                        )
                    }
                }
            }
        }
    }
}

// ── Tab 4: Guardian Alerts & Incident History ────────────────────────────────

@Composable
fun AlertsTab(viewModel: KeypadProtectionViewModel, state: KeypadUiState) {
    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp)
    ) {
        // Summary metrics
        state.alertSummary?.let { sum ->
            item {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    MetricCard(title = "Dependents", value = sum.totalDependents.toString(), color = CyberCyan, modifier = Modifier.weight(1f))
                    MetricCard(title = "Incidents", value = sum.totalIncidents.toString(), color = SeverityHigh, modifier = Modifier.weight(1f))
                    MetricCard(title = "Unreviewed", value = sum.unacknowledgedAlerts.toString(), color = SeverityCritical, modifier = Modifier.weight(1f))
                }
            }

            item {
                Text(
                    text = "Incident History (${sum.recentIncidents.size})",
                    fontWeight = FontWeight.Bold,
                    color = TextPrimary,
                    fontSize = 15.sp
                )
            }

            if (sum.recentIncidents.isEmpty()) {
                item {
                    Card(
                        colors = CardDefaults.cardColors(containerColor = DarkSurface),
                        shape = RoundedCornerShape(8.dp),
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Box(modifier = Modifier.padding(20.dp), contentAlignment = Alignment.Center) {
                            Text(
                                text = "No suspicious incidents submitted yet. Real incidents appear here when you or the system inspect threats.",
                                fontSize = 13.sp,
                                color = TextSecondary
                            )
                        }
                    }
                }
            } else {
                items(sum.recentIncidents) { inc ->
                    val sevCol = when (inc.severity) {
                        "CRITICAL" -> SeverityCritical
                        "HIGH" -> SeverityHigh
                        "MEDIUM" -> SeverityMedium
                        else -> SeverityLow
                    }
                    Card(
                        colors = CardDefaults.cardColors(containerColor = DarkSurface),
                        shape = RoundedCornerShape(10.dp),
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Column(modifier = Modifier.padding(14.dp)) {
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween,
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Row(verticalAlignment = Alignment.CenterVertically) {
                                    Surface(color = sevCol.copy(alpha = 0.2f), shape = RoundedCornerShape(4.dp)) {
                                        Text(
                                            text = inc.severity,
                                            color = sevCol,
                                            fontWeight = FontWeight.Bold,
                                            fontSize = 10.sp,
                                            modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                                        )
                                    }
                                    Spacer(modifier = Modifier.width(8.dp))
                                    Text(
                                        text = inc.incidentType.replace('_', ' '),
                                        fontWeight = FontWeight.SemiBold,
                                        fontSize = 13.sp,
                                        color = TextPrimary
                                    )
                                }

                                if (!inc.isAcknowledged) {
                                    OutlinedButton(
                                        onClick = { viewModel.acknowledgeAlert(inc.id) },
                                        shape = RoundedCornerShape(6.dp),
                                        contentPadding = PaddingValues(horizontal = 8.dp, vertical = 2.dp)
                                    ) {
                                        Text("Mark Reviewed", fontSize = 10.sp, color = CyberCyan)
                                    }
                                } else {
                                    Text("Reviewed", fontSize = 11.sp, color = SeverityLow)
                                }
                            }

                            Spacer(modifier = Modifier.height(6.dp))
                            Text(
                                text = "Target: ${inc.indicator} • Category: ${inc.category}",
                                fontSize = 11.sp,
                                color = CyberCyan
                            )
                            Spacer(modifier = Modifier.height(4.dp))
                            Text(
                                text = inc.explanation,
                                fontSize = 12.sp,
                                color = TextSecondary,
                                lineHeight = 16.sp
                            )
                        }
                    }
                }
            }
        } ?: item {
            Box(modifier = Modifier.fillMaxWidth().padding(24.dp), contentAlignment = Alignment.Center) {
                CircularProgressIndicator(color = CyberCyan)
            }
        }
    }
}

// ── Tab 5: Multilingual Fraud Education ──────────────────────────────────────

@Composable
fun EducationTab(viewModel: KeypadProtectionViewModel, state: KeypadUiState) {
    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp)
    ) {
        item {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "Fraud Awareness for Elders",
                    fontWeight = FontWeight.Bold,
                    color = TextPrimary,
                    fontSize = 16.sp
                )

                // Language Switcher
                Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                    listOf("en" to "EN", "hi" to "हिन्दी", "kn" to "ಕನ್ನಡ").forEach { (code, label) ->
                        Surface(
                            color = if (state.educationLanguage == code) CyberCyan else DarkSurfaceVar,
                            shape = RoundedCornerShape(6.dp),
                            modifier = Modifier.clickable { viewModel.setEducationLanguage(code) }
                        ) {
                            Text(
                                text = label,
                                color = if (state.educationLanguage == code) Color.Black else TextPrimary,
                                fontSize = 11.sp,
                                fontWeight = FontWeight.Bold,
                                modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp)
                            )
                        }
                    }
                }
            }
        }

        state.educationContent?.let { edu ->
            // The Golden Rule Card
            item {
                Card(
                    colors = CardDefaults.cardColors(containerColor = SeverityHigh.copy(alpha = 0.15f)),
                    shape = RoundedCornerShape(12.dp),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Icon(
                                imageVector = Icons.Default.Shield,
                                contentDescription = null,
                                tint = SeverityHigh,
                                modifier = Modifier.size(20.dp)
                            )
                            Spacer(modifier = Modifier.width(8.dp))
                            Text(
                                text = edu.goldenRuleTitle,
                                fontWeight = FontWeight.Bold,
                                color = SeverityHigh,
                                fontSize = 14.sp
                            )
                        }
                        Spacer(modifier = Modifier.height(8.dp))
                        Text(
                            text = edu.goldenRuleDescription,
                            fontSize = 13.sp,
                            color = TextPrimary,
                            lineHeight = 18.sp
                        )

                        Spacer(modifier = Modifier.height(12.dp))
                        Text(
                            text = "Never Share on Phone or SMS:",
                            fontWeight = FontWeight.Bold,
                            fontSize = 12.sp,
                            color = SeverityCritical
                        )
                        Spacer(modifier = Modifier.height(4.dp))
                        edu.doNotShareItems.forEach { item ->
                            Row(modifier = Modifier.padding(vertical = 2.dp), verticalAlignment = Alignment.Top) {
                                Text("• ", color = SeverityCritical, fontSize = 12.sp)
                                Text(item, color = TextSecondary, fontSize = 12.sp)
                            }
                        }
                    }
                }
            }

            item {
                Text(
                    text = "Common Scams Targeting Keypad Phones",
                    fontWeight = FontWeight.Bold,
                    color = TextPrimary,
                    fontSize = 15.sp
                )
            }

            items(edu.commonScams) { scam ->
                Card(
                    colors = CardDefaults.cardColors(containerColor = DarkSurface),
                    shape = RoundedCornerShape(10.dp),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Column(modifier = Modifier.padding(14.dp)) {
                        Text(
                            text = scam.title,
                            fontWeight = FontWeight.Bold,
                            color = CyberCyan,
                            fontSize = 14.sp
                        )
                        Spacer(modifier = Modifier.height(4.dp))
                        Text(
                            text = scam.summary,
                            fontSize = 12.sp,
                            color = TextSecondary,
                            lineHeight = 16.sp
                        )

                        Spacer(modifier = Modifier.height(8.dp))
                        Text(
                            text = "Danger Indicators:",
                            fontSize = 11.sp,
                            fontWeight = FontWeight.Bold,
                            color = SeverityHigh
                        )
                        scam.dangerIndicators.forEach { d ->
                            Row(modifier = Modifier.padding(vertical = 1.dp)) {
                                Text("! ", color = SeverityHigh, fontSize = 11.sp, fontWeight = FontWeight.Bold)
                                Text(d, fontSize = 11.sp, color = TextSecondary)
                            }
                        }

                        Spacer(modifier = Modifier.height(6.dp))
                        Text(
                            text = "Safe Action: ${scam.safeBehavior}",
                            fontSize = 11.sp,
                            color = SeverityLow
                        )
                    }
                }
            }
        } ?: item {
            Box(modifier = Modifier.fillMaxWidth().padding(24.dp), contentAlignment = Alignment.Center) {
                CircularProgressIndicator(color = CyberCyan)
            }
        }
    }
}

// ── Tab 6: Official Helpdesks ────────────────────────────────────────────────

@Composable
fun HelplineTab(viewModel: KeypadProtectionViewModel, state: KeypadUiState) {
    val context = LocalContext.current

    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp)
    ) {
        item {
            Card(
                colors = CardDefaults.cardColors(containerColor = DarkSurface),
                shape = RoundedCornerShape(12.dp),
                modifier = Modifier.fillMaxWidth()
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text(
                        text = "Official Government Helpdesks & Helplines",
                        fontWeight = FontWeight.Bold,
                        color = TextPrimary,
                        fontSize = 16.sp
                    )
                    Spacer(modifier = Modifier.height(4.dp))
                    Text(
                        text = "Reporting to government authorities triggers investigation and telecom carrier disconnection. Note: Software blocking on keypad phones is not possible without carrier action.",
                        fontSize = 12.sp,
                        color = TextSecondary
                    )
                }
            }
        }

        // Helplines list
        item {
            Text(
                text = "Emergency Dialers (One-Tap Call)",
                fontWeight = FontWeight.Bold,
                color = TextPrimary,
                fontSize = 15.sp
            )
        }

        val helplines = listOf(
            Triple("1930", "National Cyber Crime Helpline", "Instant reporting of financial fraud & frozen bank transfers"),
            Triple("1909", "TRAI DND & Telecom Spam", "Report spam calls and predatory marketing numbers to telecom operators"),
            Triple("112", "National Emergency Number", "Immediate police and emergency assistance across all states in India")
        )

        items(helplines) { (num, name, desc) ->
            Card(
                colors = CardDefaults.cardColors(containerColor = DarkSurface),
                shape = RoundedCornerShape(10.dp),
                modifier = Modifier.fillMaxWidth()
            ) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(14.dp),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Column(modifier = Modifier.weight(1f)) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Text(text = num, fontWeight = FontWeight.Bold, fontSize = 18.sp, color = CyberCyan)
                            Spacer(modifier = Modifier.width(8.dp))
                            Text(text = name, fontWeight = FontWeight.SemiBold, fontSize = 13.sp, color = TextPrimary)
                        }
                        Spacer(modifier = Modifier.height(4.dp))
                        Text(text = desc, fontSize = 11.sp, color = TextSecondary)
                    }
                    Button(
                        onClick = {
                            val intent = Intent(Intent.ACTION_DIAL, Uri.parse("tel:$num"))
                            context.startActivity(intent)
                        },
                        colors = ButtonDefaults.buttonColors(containerColor = CyberCyan, contentColor = Color.Black),
                        shape = RoundedCornerShape(8.dp),
                        contentPadding = PaddingValues(horizontal = 12.dp, vertical = 6.dp)
                    ) {
                        Icon(imageVector = Icons.Default.Phone, contentDescription = null, modifier = Modifier.size(16.dp))
                        Spacer(modifier = Modifier.width(4.dp))
                        Text("Dial", fontSize = 12.sp, fontWeight = FontWeight.Bold)
                    }
                }
            }
        }

        item {
            Spacer(modifier = Modifier.height(6.dp))
            Text(
                text = "Official Reporting Portals",
                fontWeight = FontWeight.Bold,
                color = TextPrimary,
                fontSize = 15.sp
            )
        }

        val portals = listOf(
            Pair("Sanchar Saathi (Chakshu)", "https://sancharsaathi.gov.in/sfc/"),
            Pair("National Cyber Crime Portal", "https://cybercrime.gov.in"),
            Pair("TRAI Telecom Consumer Portal", "https://telecomservice.gov.in")
        )

        items(portals) { (portalName, url) ->
            Card(
                colors = CardDefaults.cardColors(containerColor = DarkSurface),
                shape = RoundedCornerShape(10.dp),
                modifier = Modifier.fillMaxWidth()
            ) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(14.dp),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Column(modifier = Modifier.weight(1f)) {
                        Text(text = portalName, fontWeight = FontWeight.SemiBold, fontSize = 14.sp, color = TextPrimary)
                        Spacer(modifier = Modifier.height(2.dp))
                        Text(text = url, fontSize = 11.sp, color = CyberCyan)
                    }
                    IconButton(
                        onClick = {
                            val intent = Intent(Intent.ACTION_VIEW, Uri.parse(url))
                            context.startActivity(intent)
                        }
                    ) {
                        Icon(imageVector = Icons.Default.OpenInNew, contentDescription = "Open", tint = CyberCyan)
                    }
                }
            }
        }
    }
}

// ── Reusable Helpers ────────────────────────────────────────────────────────

@Composable
fun MetricCard(title: String, value: String, color: Color, modifier: Modifier = Modifier) {
    Card(
        colors = CardDefaults.cardColors(containerColor = DarkSurface),
        shape = RoundedCornerShape(10.dp),
        modifier = modifier
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(12.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text(text = value, fontSize = 20.sp, fontWeight = FontWeight.Bold, color = color)
            Spacer(modifier = Modifier.height(2.dp))
            Text(text = title, fontSize = 11.sp, color = TextSecondary)
        }
    }
}

@Composable
fun outlinedTextFieldColors() = OutlinedTextFieldDefaults.colors(
    focusedBorderColor = CyberCyan,
    unfocusedBorderColor = DarkOutline,
    focusedLabelColor = CyberCyan,
    unfocusedLabelColor = TextSecondary,
    focusedTextColor = TextPrimary,
    unfocusedTextColor = TextPrimary,
    cursorColor = CyberCyan
)

