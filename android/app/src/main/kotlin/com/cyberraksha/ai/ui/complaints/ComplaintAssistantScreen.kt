package com.cyberraksha.ai.ui.complaints

import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.widget.Toast
import androidx.compose.foundation.background
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
import com.cyberraksha.ai.core.AppPreferences
import com.cyberraksha.ai.data.remote.ComplaintDraftRequestDto
import com.cyberraksha.ai.data.remote.ComplaintResponseDto
import com.cyberraksha.ai.data.remote.NetworkModule
import com.cyberraksha.ai.data.remote.RecordAckRequestDto
import com.cyberraksha.ai.ui.theme.*
import kotlinx.coroutines.launch

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ComplaintAssistantScreen(
    prefs: AppPreferences,
    initialSuspect: String? = null,
    initialCategory: String? = null,
    initialDescription: String? = null,
    onBack: () -> Unit
) {
    val context = LocalContext.current
    val coroutineScope = rememberCoroutineScope()
    val backendUrl by prefs.backendUrl.collectAsState(initial = AppPreferences.DEFAULT_BACKEND_URL)
    val userToken by prefs.userToken.collectAsState(initial = null)
    val deviceId by prefs.deviceId.collectAsState(initial = null)

    var suspectIdentifier by remember { mutableStateOf(initialSuspect ?: "") }
    var selectedCategory by remember { mutableStateOf(initialCategory ?: "BANKING_FRAUD") }
    var financialLoss by remember { mutableStateOf("") }
    var description by remember { mutableStateOf(initialDescription ?: "") }

    var isSubmitting by remember { mutableStateOf(false) }
    var generatedComplaint by remember { mutableStateOf<ComplaintResponseDto?>(null) }
    var ackInput by remember { mutableStateOf("") }
    var complaintsList by remember { mutableStateOf<List<ComplaintResponseDto>>(emptyList()) }
    var activeTab by remember { mutableStateOf(0) } // 0: Assistant, 1: Tracked Complaints

    val categories = listOf("BANKING_FRAUD", "DIGITAL_ARREST", "UPI_FRAUD", "KYC_SCAM", "PHISHING", "IMPERSONATION")

    // Load existing complaints
    LaunchedEffect(Unit) {
        try {
            val api = NetworkModule.getApiService(backendUrl)
            val authHeader = userToken?.let { "Bearer $it" }
            val resp = api.listComplaints(bearerToken = authHeader, deviceId = deviceId)
            if (resp.isSuccessful && resp.body() != null) {
                complaintsList = resp.body()!!
            }
        } catch (_: Exception) {}
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Cybercrime Complaint Assistant", fontWeight = FontWeight.Bold) },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.Default.ArrowBack, contentDescription = "Back")
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = DarkSurface,
                    titleContentColor = CyberCyan,
                    navigationIconContentColor = Color.White
                )
            )
        }
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(16.dp)
        ) {
            // Emergency 1930 Helpline Banner
            Card(
                colors = CardDefaults.cardColors(containerColor = Color(0x33FF3B30)),
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
                        Text(
                            text = "🚨 Financial Fraud Emergency",
                            fontWeight = FontWeight.Bold,
                            color = Color(0xFFFF453A),
                            fontSize = 14.sp
                        )
                        Text(
                            text = "Dial 1930 within the 'Golden Hour' to request immediate bank account freeze.",
                            style = MaterialTheme.typography.bodySmall,
                            color = TextSecondary
                        )
                    }
                    Button(
                        onClick = {
                            val dialIntent = Intent(Intent.ACTION_DIAL, Uri.parse("tel:1930"))
                            context.startActivity(dialIntent)
                        },
                        colors = ButtonDefaults.buttonColors(containerColor = Color(0xFFFF453A), contentColor = Color.White),
                        shape = RoundedCornerShape(6.dp)
                    ) {
                        Icon(Icons.Default.Phone, contentDescription = null, modifier = Modifier.size(16.dp))
                        Spacer(modifier = Modifier.width(4.dp))
                        Text("1930", fontWeight = FontWeight.Bold)
                    }
                }
            }

            Spacer(modifier = Modifier.height(16.dp))

            // Tab Selector
            TabRow(
                selectedTabIndex = activeTab,
                containerColor = DarkSurface,
                contentColor = CyberCyan
            ) {
                Tab(
                    selected = activeTab == 0,
                    onClick = { activeTab = 0 },
                    text = { Text("Draft Complaint", fontWeight = FontWeight.Bold) }
                )
                Tab(
                    selected = activeTab == 1,
                    onClick = { activeTab = 1 },
                    text = { Text("Tracked Cases (${complaintsList.size})", fontWeight = FontWeight.Bold) }
                )
            }

            Spacer(modifier = Modifier.height(16.dp))

            if (activeTab == 0) {
                // Draft Assistant Tab
                LazyColumn(modifier = Modifier.fillMaxSize()) {
                    item {
                        Text(
                            "Step 1: Incident Evidence Summary",
                            style = MaterialTheme.typography.titleMedium,
                            fontWeight = FontWeight.Bold,
                            color = CyberCyan
                        )
                        Spacer(modifier = Modifier.height(8.dp))

                        OutlinedTextField(
                            value = suspectIdentifier,
                            onValueChange = { suspectIdentifier = it },
                            label = { Text("Suspect Identifier (Phone / UPI / URL)") },
                            modifier = Modifier.fillMaxWidth(),
                            singleLine = true
                        )
                        Spacer(modifier = Modifier.height(10.dp))

                        // Category Dropdown / Pills
                        Text("Fraud Category:", style = MaterialTheme.typography.bodySmall, color = TextSecondary)
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(vertical = 4.dp),
                            horizontalArrangement = Arrangement.spacedBy(6.dp)
                        ) {
                            categories.take(3).forEach { cat ->
                                FilterChip(
                                    selected = selectedCategory == cat,
                                    onClick = { selectedCategory = cat },
                                    label = { Text(cat.replace("_", " "), fontSize = 11.sp) }
                                )
                            }
                        }
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(bottom = 8.dp),
                            horizontalArrangement = Arrangement.spacedBy(6.dp)
                        ) {
                            categories.drop(3).forEach { cat ->
                                FilterChip(
                                    selected = selectedCategory == cat,
                                    onClick = { selectedCategory = cat },
                                    label = { Text(cat.replace("_", " "), fontSize = 11.sp) }
                                )
                            }
                        }

                        OutlinedTextField(
                            value = financialLoss,
                            onValueChange = { financialLoss = it },
                            label = { Text("Financial Loss in INR (0 if none)") },
                            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                            modifier = Modifier.fillMaxWidth(),
                            singleLine = true
                        )
                        Spacer(modifier = Modifier.height(10.dp))

                        OutlinedTextField(
                            value = description,
                            onValueChange = { description = it },
                            label = { Text("Incident Description & Sequence of Events") },
                            modifier = Modifier
                                .fillMaxWidth()
                                .height(110.dp),
                            maxLines = 4
                        )

                        Spacer(modifier = Modifier.height(16.dp))

                        Button(
                            onClick = {
                                if (description.length < 10) {
                                    Toast.makeText(context, "Please describe the incident in detail.", Toast.LENGTH_SHORT).show()
                                    return@Button
                                }
                                isSubmitting = true
                                coroutineScope.launch {
                                    try {
                                        val api = NetworkModule.getApiService(backendUrl)
                                        val authHeader = userToken?.let { "Bearer $it" }
                                        val lossVal = financialLoss.toDoubleOrNull() ?: 0.0
                                        val resp = api.createComplaintDraft(
                                            bearerToken = authHeader,
                                            request = ComplaintDraftRequestDto(
                                                complaintCategory = selectedCategory,
                                                suspectIdentifier = suspectIdentifier.ifBlank { null },
                                                financialLossInr = lossVal,
                                                description = description,
                                                deviceId = deviceId
                                            )
                                        )
                                        if (resp.isSuccessful && resp.body() != null) {
                                            generatedComplaint = resp.body()
                                            complaintsList = listOf(resp.body()!!) + complaintsList
                                            Toast.makeText(context, "Draft Generated Successfully!", Toast.LENGTH_SHORT).show()
                                        } else {
                                            Toast.makeText(context, "Draft creation failed: ${resp.message()}", Toast.LENGTH_SHORT).show()
                                        }
                                    } catch (e: Exception) {
                                        Toast.makeText(context, "Error: ${e.localizedMessage}", Toast.LENGTH_SHORT).show()
                                    } finally {
                                        isSubmitting = false
                                    }
                                }
                            },
                            enabled = !isSubmitting,
                            modifier = Modifier
                                .fillMaxWidth()
                                .height(48.dp),
                            colors = ButtonDefaults.buttonColors(containerColor = CyberCyan, contentColor = Color.Black),
                            shape = RoundedCornerShape(8.dp)
                        ) {
                            if (isSubmitting) {
                                CircularProgressIndicator(color = Color.Black, modifier = Modifier.size(20.dp))
                            } else {
                                Text("Generate Structured Draft", fontWeight = FontWeight.Bold)
                            }
                        }

                        // Generated Draft Card
                        generatedComplaint?.let { draft ->
                            Spacer(modifier = Modifier.height(20.dp))
                            Card(
                                colors = CardDefaults.cardColors(containerColor = DarkSurface),
                                modifier = Modifier.fillMaxWidth()
                            ) {
                                Column(modifier = Modifier.padding(16.dp)) {
                                    Text(
                                        "Complaint Draft: ${draft.complaintId}",
                                        fontWeight = FontWeight.Bold,
                                        color = CyberCyan
                                    )
                                    Spacer(modifier = Modifier.height(8.dp))
                                    Text(
                                        text = draft.evidenceSummary ?: draft.description,
                                        style = MaterialTheme.typography.bodySmall,
                                        color = TextPrimary
                                    )
                                    Spacer(modifier = Modifier.height(12.dp))

                                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                        Button(
                                            onClick = {
                                                val clipboard = context.getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
                                                val clip = ClipData.newPlainText("Evidence Summary", draft.evidenceSummary ?: draft.description)
                                                clipboard.setPrimaryClip(clip)
                                                Toast.makeText(context, "Copied evidence summary!", Toast.LENGTH_SHORT).show()
                                            },
                                            modifier = Modifier.weight(1f),
                                            colors = ButtonDefaults.buttonColors(containerColor = Color(0x3300E5FF), contentColor = CyberCyan)
                                        ) {
                                            Icon(Icons.Default.ContentCopy, contentDescription = null, modifier = Modifier.size(16.dp))
                                            Spacer(modifier = Modifier.width(4.dp))
                                            Text("Copy Evidence")
                                        }

                                        Button(
                                            onClick = {
                                                val browserIntent = Intent(Intent.ACTION_VIEW, Uri.parse(draft.officialPortalUrl))
                                                context.startActivity(browserIntent)
                                            },
                                            modifier = Modifier.weight(1f),
                                            colors = ButtonDefaults.buttonColors(containerColor = CyberCyan, contentColor = Color.Black)
                                        ) {
                                            Icon(Icons.Default.Launch, contentDescription = null, modifier = Modifier.size(16.dp))
                                            Spacer(modifier = Modifier.width(4.dp))
                                            Text("cybercrime.gov.in")
                                        }
                                    }

                                    Spacer(modifier = Modifier.height(14.dp))
                                    Divider(color = Color.Gray.copy(alpha = 0.2f))
                                    Spacer(modifier = Modifier.height(14.dp))

                                    Text(
                                        "Step 2: Enter Official Acknowledgement Number",
                                        fontWeight = FontWeight.Bold,
                                        color = SeverityLow,
                                        fontSize = 13.sp
                                    )
                                    Spacer(modifier = Modifier.height(6.dp))
                                    OutlinedTextField(
                                        value = ackInput,
                                        onValueChange = { ackInput = it },
                                        label = { Text("Ack / FIR Reference Number") },
                                        placeholder = { Text("e.g. 2026/001930/XXXX") },
                                        modifier = Modifier.fillMaxWidth(),
                                        singleLine = true
                                    )
                                    Spacer(modifier = Modifier.height(8.dp))
                                    Button(
                                        onClick = {
                                            if (ackInput.length < 4) return@Button
                                            coroutineScope.launch {
                                                try {
                                                    val api = NetworkModule.getApiService(backendUrl)
                                                    val authHeader = userToken?.let { "Bearer $it" }
                                                    val resp = api.recordOfficialAck(
                                                        bearerToken = authHeader,
                                                        complaintId = draft.complaintId,
                                                        request = RecordAckRequestDto(ackInput)
                                                    )
                                                    if (resp.isSuccessful && resp.body() != null) {
                                                        generatedComplaint = resp.body()
                                                        Toast.makeText(context, "Official Ack Recorded!", Toast.LENGTH_SHORT).show()
                                                    }
                                                } catch (e: Exception) {
                                                    Toast.makeText(context, "Error: ${e.localizedMessage}", Toast.LENGTH_SHORT).show()
                                                }
                                            }
                                        },
                                        modifier = Modifier.fillMaxWidth(),
                                        colors = ButtonDefaults.buttonColors(containerColor = SeverityLow, contentColor = Color.Black)
                                    ) {
                                        Text("Record & Start Official Tracking", fontWeight = FontWeight.Bold)
                                    }
                                }
                            }
                        }
                    }
                }
            } else {
                // Tracked Cases Tab
                if (complaintsList.isEmpty()) {
                    Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                        Text("No complaints filed yet.", color = TextSecondary)
                    }
                } else {
                    LazyColumn(
                        modifier = Modifier.fillMaxSize(),
                        verticalArrangement = Arrangement.spacedBy(10.dp)
                    ) {
                        items(complaintsList) { item ->
                            Card(
                                colors = CardDefaults.cardColors(containerColor = DarkSurface),
                                modifier = Modifier.fillMaxWidth()
                            ) {
                                Column(modifier = Modifier.padding(14.dp)) {
                                    Row(
                                        modifier = Modifier.fillMaxWidth(),
                                        horizontalArrangement = Arrangement.SpaceBetween
                                    ) {
                                        Text(item.complaintId, fontWeight = FontWeight.Bold, color = CyberCyan)
                                        Surface(
                                            color = when (item.status) {
                                                "OFFICIALLY_SUBMITTED" -> Color(0x3330D158)
                                                "UNDER_REVIEW" -> Color(0x3300E5FF)
                                                "ACTION_TAKEN" -> Color(0x33FF9F0A)
                                                else -> Color(0x338E8E93)
                                            },
                                            shape = RoundedCornerShape(4.dp)
                                        ) {
                                            Text(
                                                text = item.status.replace("_", " "),
                                                color = when (item.status) {
                                                    "OFFICIALLY_SUBMITTED" -> Color(0xFF30D158)
                                                    "UNDER_REVIEW" -> CyberCyan
                                                    "ACTION_TAKEN" -> Color(0xFFFF9F0A)
                                                    else -> TextSecondary
                                                },
                                                fontSize = 11.sp,
                                                fontWeight = FontWeight.Bold,
                                                modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                                            )
                                        }
                                    }
                                    Spacer(modifier = Modifier.height(4.dp))
                                    Text("Category: ${item.complaintCategory}", style = MaterialTheme.typography.bodySmall, color = TextPrimary)
                                    if (item.officialAckNumber != null) {
                                        Text(
                                            "Official Ack: ${item.officialAckNumber}",
                                            style = MaterialTheme.typography.bodySmall,
                                            fontWeight = FontWeight.Bold,
                                            color = SeverityLow
                                        )
                                    }
                                    Spacer(modifier = Modifier.height(4.dp))
                                    Text(
                                        item.description,
                                        style = MaterialTheme.typography.bodySmall,
                                        color = TextSecondary,
                                        maxLines = 2
                                    )
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
