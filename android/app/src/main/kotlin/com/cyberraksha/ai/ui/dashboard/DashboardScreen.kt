package com.cyberraksha.ai.ui.dashboard

import android.Manifest
import android.app.Activity
import android.content.pm.PackageManager
import android.net.VpnService
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.content.ContextCompat
import androidx.room.Room
import com.cyberraksha.ai.core.AppPreferences
import com.cyberraksha.ai.data.local.AppDatabase
import com.cyberraksha.ai.data.remote.SecurityEventItem
import com.cyberraksha.ai.ui.call_protection.CallScreeningHelper
import com.cyberraksha.ai.ui.theme.*
import com.cyberraksha.ai.vpn.CyberRakshaDnsVpnService

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun DashboardScreen(
    prefs: AppPreferences,
    onNavigateToAlerts: () -> Unit,
    onNavigateToSettings: () -> Unit,
    onNavigateToSmsProtection: () -> Unit = {},
    onNavigateToCallProtection: () -> Unit = {},
    onNavigateToThreatHistory: () -> Unit = {}
) {
    val context = LocalContext.current
    val db = remember {
        Room.databaseBuilder(
            context,
            AppDatabase::class.java,
            "cyber_raksha_db"
        ).fallbackToDestructiveMigration().build()
    }
    val viewModel = remember { DashboardViewModel(prefs, db.notificationDao(), db.threatIncidentDao()) }
    val state by viewModel.uiState.collectAsState()

    val vpnLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.StartActivityForResult()
    ) { result ->
        if (result.resultCode == Activity.RESULT_OK) {
            CyberRakshaDnsVpnService.start(context)
            viewModel.toggleWebProtection(true)
        }
    }

    val smsPermissionLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.RequestMultiplePermissions()
    ) { permissions ->
        val smsGranted = permissions[Manifest.permission.RECEIVE_SMS] == true
        if (smsGranted) {
            viewModel.toggleSmsProtection(true)
        }
    }

    val callRoleLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.StartActivityForResult()
    ) {
        viewModel.toggleCallProtection(true)
    }

    fun enableProtection() {
        // 1. Request SMS permission if not already granted
        val hasSms = ContextCompat.checkSelfPermission(
            context,
            Manifest.permission.RECEIVE_SMS
        ) == PackageManager.PERMISSION_GRANTED
        if (!hasSms) {
            smsPermissionLauncher.launch(
                arrayOf(
                    Manifest.permission.RECEIVE_SMS,
                    Manifest.permission.READ_SMS
                )
            )
        }

        // 2. Request Call Screening role if available and not held
        val callIntent = CallScreeningHelper.createRequestRoleIntent(context)
        if (callIntent != null && CallScreeningHelper.getScreeningStatus(context) != com.cyberraksha.ai.ui.call_protection.CallScreeningStatus.ACTIVE) {
            callRoleLauncher.launch(callIntent)
        }

        // 3. Prepare & start local DNS VPN filter
        val vpnIntent = VpnService.prepare(context)
        if (vpnIntent != null) {
            vpnLauncher.launch(vpnIntent)
        } else {
            CyberRakshaDnsVpnService.start(context)
            viewModel.toggleWebProtection(true)
        }

        viewModel.toggleAutonomousProtection(true)
    }

    fun disableProtection() {
        CyberRakshaDnsVpnService.stop(context)
        viewModel.toggleWebProtection(false)
        viewModel.toggleAutonomousProtection(false)
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Icon(
                            imageVector = Icons.Default.Shield,
                            contentDescription = "Shield",
                            tint = CyberCyan,
                            modifier = Modifier.size(24.dp)
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(
                            "CYBER RAKSHA",
                            style = MaterialTheme.typography.titleLarge,
                            fontWeight = FontWeight.Bold,
                            color = TextPrimary
                        )
                    }
                },
                actions = {
                    IconButton(onClick = onNavigateToAlerts) {
                        BadgedBox(
                            badge = {
                                if (state.unreadCount > 0) {
                                    Badge(containerColor = SeverityCritical) {
                                        Text("${state.unreadCount}")
                                    }
                                }
                            }
                        ) {
                            Icon(
                                imageVector = Icons.Default.Notifications,
                                contentDescription = "Alerts",
                                tint = TextPrimary
                            )
                        }
                    }
                    IconButton(onClick = onNavigateToSettings) {
                        Icon(
                            imageVector = Icons.Default.Settings,
                            contentDescription = "Settings",
                            tint = TextPrimary
                        )
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = DarkSurface)
            )
        },
        containerColor = DarkBackground
    ) { padding ->
        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(horizontal = 16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            item { Spacer(modifier = Modifier.height(8.dp)) }

            // Offline Banner
            if (state.isOffline) {
                item {
                    OfflineBanner(
                        diagnosticReport = state.diagnosticReport,
                        onRetry = { viewModel.refresh() }
                    )
                }
            }

            // Card 0: Master Autonomous Protection Toggle Card
            item {
                MasterProtectionCard(
                    isProtected = state.autonomousProtectionEnabled,
                    onToggleProtection = { shouldEnable ->
                        if (shouldEnable) {
                            enableProtection()
                        } else {
                            disableProtection()
                        }
                    }
                )
            }

            // Card 1: Device Status
            item {
                ProtectionStatusCard(
                    deviceName = state.deviceName,
                    posture = state.securityPosture,
                    isConnected = state.isConnected,
                    lastSync = state.lastSyncFormatted,
                    onRefresh = { viewModel.refresh() },
                    isRefreshing = state.isRefreshing
                )
            }

            // Card 2: Security Overview (Dynamic Threat Counters)
            item {
                SecurityOverviewCard(
                    totalBlocked = state.totalThreatsBlocked,
                    smsThreats = state.smsThreatsCount,
                    callThreats = state.callThreatsCount,
                    webThreats = state.webThreatsCount,
                    onClickAlerts = onNavigateToAlerts
                )
            }

            // Card 3: Defense Capabilities / Protection Modules
            item {
                ProtectionModulesCard(
                    smsActive = state.smsProtectionEnabled,
                    callActive = state.callProtectionEnabled,
                    webActive = state.webProtectionEnabled,
                    onOpenSms = onNavigateToSmsProtection,
                    onOpenCall = onNavigateToCallProtection,
                    onOpenHistory = onNavigateToThreatHistory
                )
            }

            // Card 4: Recent Activity Header
            item {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "Recent Security Events",
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.SemiBold,
                        color = TextPrimary
                    )
                    TextButton(onClick = onNavigateToAlerts) {
                        Text("View All", color = CyberCyan)
                    }
                }
            }

            // Recent Activity Items
            if (state.recentActivity.isEmpty()) {
                item {
                    Card(
                        modifier = Modifier.fillMaxWidth(),
                        colors = CardDefaults.cardColors(containerColor = DarkSurface),
                        shape = RoundedCornerShape(12.dp)
                    ) {
                        Box(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(24.dp),
                            contentAlignment = Alignment.Center
                        ) {
                            Text(
                                "No recent security incidents recorded.",
                                style = MaterialTheme.typography.bodyMedium,
                                color = TextSecondary
                            )
                        }
                    }
                }
            } else {
                items(state.recentActivity) { event ->
                    RecentActivityItem(event)
                }
            }

            item { Spacer(modifier = Modifier.height(16.dp)) }
        }
    }
}


@Composable
private fun OfflineBanner(
    diagnosticReport: com.cyberraksha.ai.data.repository.DiagnosticReport?,
    onRetry: () -> Unit
) {
    var showDetails by remember { mutableStateOf(false) }

    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = SeverityHigh.copy(alpha = 0.2f)),
        shape = RoundedCornerShape(10.dp)
    ) {
        Column(modifier = Modifier.padding(12.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    modifier = Modifier.weight(1f).clickable { showDetails = !showDetails }
                ) {
                    Icon(
                        imageVector = Icons.Default.CloudOff,
                        contentDescription = "Offline",
                        tint = SeverityHigh,
                        modifier = Modifier.size(20.dp)
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    Column {
                        Text(
                            text = if (diagnosticReport?.exceptionType != null)
                                "Offline: ${diagnosticReport.exceptionType}"
                            else
                                "Backend Offline",
                            fontWeight = FontWeight.SemiBold,
                            color = SeverityHigh,
                            fontSize = 13.sp
                        )
                        Text(
                            text = diagnosticReport?.exceptionMessage?.take(40) ?: "Tap for network diagnostics",
                            style = MaterialTheme.typography.labelSmall,
                            color = TextSecondary,
                            maxLines = 1
                        )
                    }
                }
                TextButton(onClick = onRetry) {
                    Text("Retry", color = CyberCyan, fontWeight = FontWeight.Bold)
                }
            }

            if (showDetails && diagnosticReport != null) {
                Spacer(modifier = Modifier.height(8.dp))
                HorizontalDivider(color = DarkOutline)
                Spacer(modifier = Modifier.height(8.dp))
                Text(
                    text = "Endpoint: ${diagnosticReport.healthEndpointUrl}",
                    style = MaterialTheme.typography.labelSmall,
                    color = TextPrimary
                )
                Text(
                    text = "HTTP Code: ${diagnosticReport.httpStatusCode ?: "No HTTP response"}",
                    style = MaterialTheme.typography.labelSmall,
                    color = TextPrimary
                )
                Text(
                    text = "DNS IPs: ${diagnosticReport.dnsResolvedIps.joinToString(", ")}",
                    style = MaterialTheme.typography.labelSmall,
                    color = TextPrimary
                )
                Text(
                    text = "Latency: ${diagnosticReport.latencyMs} ms",
                    style = MaterialTheme.typography.labelSmall,
                    color = TextPrimary
                )
                if (!diagnosticReport.stackTraceSnippet.isNullOrEmpty()) {
                    Spacer(modifier = Modifier.height(4.dp))
                    Text(
                        text = diagnosticReport.stackTraceSnippet,
                        style = MaterialTheme.typography.labelSmall,
                        color = SeverityCritical,
                        fontSize = 10.sp
                    )
                }
            }
        }
    }
}

@Composable
private fun ProtectionStatusCard(
    deviceName: String,
    posture: String,
    isConnected: Boolean,
    lastSync: String,
    onRefresh: () -> Unit,
    isRefreshing: Boolean
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = DarkSurface),
        shape = RoundedCornerShape(16.dp)
    ) {
        Column(modifier = Modifier.padding(18.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column {
                    Text(
                        text = deviceName,
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.Bold,
                        color = TextPrimary
                    )
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        modifier = Modifier.padding(top = 4.dp)
                    ) {
                        Box(
                            modifier = Modifier
                                .size(8.dp)
                                .clip(CircleShape)
                                .background(if (isConnected) SeverityLow else SeverityHigh)
                        )
                        Spacer(modifier = Modifier.width(6.dp))
                        Text(
                            text = if (isConnected) "Backend Online" else "Offline Fallback",
                            style = MaterialTheme.typography.labelSmall,
                            color = if (isConnected) SeverityLow else SeverityHigh
                        )
                    }
                }

                IconButton(onClick = onRefresh, enabled = !isRefreshing) {
                    if (isRefreshing) {
                        CircularProgressIndicator(
                            modifier = Modifier.size(20.dp),
                            color = CyberCyan,
                            strokeWidth = 2.dp
                        )
                    } else {
                        Icon(
                            imageVector = Icons.Default.Refresh,
                            contentDescription = "Sync",
                            tint = CyberCyan
                        )
                    }
                }
            }

            Spacer(modifier = Modifier.height(16.dp))

            // Posture Badge
            val isProtected = posture.equals("PROTECTED", ignoreCase = true)
            Surface(
                color = if (isProtected) SeverityLow.copy(alpha = 0.15f) else SeverityCritical.copy(alpha = 0.15f),
                shape = RoundedCornerShape(8.dp),
                modifier = Modifier.fillMaxWidth()
            ) {
                Row(
                    modifier = Modifier.padding(horizontal = 14.dp, vertical = 10.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Icon(
                        imageVector = if (isProtected) Icons.Default.VerifiedUser else Icons.Default.Warning,
                        contentDescription = null,
                        tint = if (isProtected) SeverityLow else SeverityCritical,
                        modifier = Modifier.size(24.dp)
                    )
                    Spacer(modifier = Modifier.width(12.dp))
                    Column {
                        Text(
                            text = if (isProtected) "SYSTEM PROTECTED" else "ATTENTION REQUIRED",
                            fontWeight = FontWeight.Bold,
                            color = if (isProtected) SeverityLow else SeverityCritical,
                            fontSize = 14.sp
                        )
                        Text(
                            text = "Threat rules synchronized: $lastSync",
                            style = MaterialTheme.typography.labelSmall,
                            color = TextSecondary
                        )
                    }
                }
            }
        }
    }
}

@Composable
private fun MasterProtectionCard(
    isProtected: Boolean,
    onToggleProtection: (Boolean) -> Unit
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(
            containerColor = if (isProtected) Color(0xFF0F2B26) else DarkSurface
        ),
        shape = RoundedCornerShape(16.dp),
        border = CardDefaults.outlinedCardBorder().copy(
            brush = androidx.compose.ui.graphics.SolidColor(
                if (isProtected) SeverityLow else DarkOutline
            )
        )
    ) {
        Column(modifier = Modifier.padding(18.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    modifier = Modifier.weight(1f)
                ) {
                    Icon(
                        imageVector = if (isProtected) Icons.Default.Security else Icons.Default.Shield,
                        contentDescription = null,
                        tint = if (isProtected) SeverityLow else TextSecondary,
                        modifier = Modifier.size(32.dp)
                    )
                    Spacer(modifier = Modifier.width(12.dp))
                    Column {
                        Text(
                            text = "AUTONOMOUS PROTECTION",
                            style = MaterialTheme.typography.titleMedium,
                            fontWeight = FontWeight.Bold,
                            color = if (isProtected) SeverityLow else TextPrimary
                        )
                        Text(
                            text = if (isProtected) "Live AI Fraud Interception Active" else "Protection Inactive • Tap to Enable",
                            style = MaterialTheme.typography.labelSmall,
                            color = TextSecondary
                        )
                    }
                }
                Switch(
                    checked = isProtected,
                    onCheckedChange = { onToggleProtection(it) },
                    colors = SwitchDefaults.colors(
                        checkedThumbColor = DarkBackground,
                        checkedTrackColor = SeverityLow,
                        uncheckedThumbColor = TextSecondary,
                        uncheckedTrackColor = DarkOutline
                    )
                )
            }

            Spacer(modifier = Modifier.height(10.dp))
            HorizontalDivider(color = if (isProtected) SeverityLow.copy(alpha = 0.3f) else DarkOutline)
            Spacer(modifier = Modifier.height(10.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                StatusPill("SMS Shield", isProtected)
                StatusPill("Call Screener", isProtected)
                StatusPill("DNS Sinkhole", isProtected)
            }
        }
    }
}

@Composable
private fun StatusPill(label: String, active: Boolean) {
    Surface(
        color = if (active) SeverityLow.copy(alpha = 0.15f) else DarkBackground,
        shape = RoundedCornerShape(8.dp)
    ) {
        Row(
            modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Box(
                modifier = Modifier
                    .size(6.dp)
                    .clip(CircleShape)
                    .background(if (active) SeverityLow else TextSecondary)
            )
            Spacer(modifier = Modifier.width(5.dp))
            Text(
                text = label,
                fontSize = 11.sp,
                fontWeight = FontWeight.Medium,
                color = if (active) SeverityLow else TextSecondary
            )
        }
    }
}

@Composable
private fun SecurityOverviewCard(
    totalBlocked: Int,
    smsThreats: Int,
    callThreats: Int,
    webThreats: Int,
    onClickAlerts: () -> Unit
) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .clickable { onClickAlerts() },
        colors = CardDefaults.cardColors(containerColor = DarkSurface),
        shape = RoundedCornerShape(16.dp)
    ) {
        Column(modifier = Modifier.padding(18.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "Security Overview",
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.SemiBold,
                    color = TextPrimary
                )
                Text(
                    text = "Live Telemetry",
                    style = MaterialTheme.typography.labelSmall,
                    color = CyberCyan
                )
            }
            Spacer(modifier = Modifier.height(14.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                MetricItem(label = "Threats Intercepted", count = "$totalBlocked", color = SeverityCritical)
                MetricItem(label = "SMS Scams", count = "$smsThreats", color = SeverityHigh)
                MetricItem(label = "Call Scams", count = "$callThreats", color = CyberCyan)
                MetricItem(label = "Phishing Sites", count = "$webThreats", color = TextPrimary)
            }
        }
    }
}

@Composable
private fun MetricItem(label: String, count: String, color: androidx.compose.ui.graphics.Color) {
    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        Text(
            text = count,
            fontSize = 24.sp,
            fontWeight = FontWeight.Bold,
            color = color
        )
        Spacer(modifier = Modifier.height(2.dp))
        Text(
            text = label,
            style = MaterialTheme.typography.labelSmall,
            color = TextSecondary,
            fontSize = 10.sp
        )
    }
}

@Composable
private fun ProtectionModulesCard(
    smsActive: Boolean,
    callActive: Boolean,
    webActive: Boolean,
    onOpenSms: () -> Unit,
    onOpenCall: () -> Unit,
    onOpenHistory: () -> Unit
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = DarkSurface),
        shape = RoundedCornerShape(16.dp)
    ) {
        Column(modifier = Modifier.padding(18.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "Autonomous Defense Vectors",
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.SemiBold,
                    color = TextPrimary
                )
                TextButton(onClick = onOpenHistory) {
                    Text("Threat Log", color = CyberCyan, fontSize = 12.sp)
                }
            }
            Spacer(modifier = Modifier.height(10.dp))

            ModuleRow("SMS Scam Guard", "Telephony BroadcastReceiver Active", smsActive, onClick = onOpenSms)
            ModuleRow("Fraud Call Screener", "Android CallScreeningService Active", callActive, onClick = onOpenCall)
            ModuleRow("DNS Phishing Sinkhole", "Local UDP 53 VpnService Active", webActive)
            ModuleRow("Instant Share Scanner", "Target for WhatsApp & Browser links", true)
            ModuleRow("Threat Intel Engine", "URLhaus & OpenPhish Synced", true)
        }
    }
}

@Composable
private fun ModuleRow(
    name: String,
    statusText: String,
    active: Boolean,
    onClick: (() -> Unit)? = null
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(enabled = onClick != null) { onClick?.invoke() }
            .padding(vertical = 6.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Column(modifier = Modifier.weight(1f)) {
            Text(text = name, style = MaterialTheme.typography.bodyMedium, color = TextPrimary)
            Text(text = statusText, style = MaterialTheme.typography.labelSmall, color = TextSecondary)
        }
        Surface(
            color = if (active) SeverityLow.copy(alpha = 0.2f) else DarkOutline,
            shape = RoundedCornerShape(6.dp)
        ) {
            Text(
                text = if (active) "ACTIVE" else "QUEUED",
                color = if (active) SeverityLow else TextSecondary,
                fontSize = 10.sp,
                fontWeight = FontWeight.Bold,
                modifier = Modifier.padding(horizontal = 8.dp, vertical = 3.dp)
            )
        }
    }
}

@Composable
private fun RecentActivityItem(event: SecurityEventItem) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = DarkSurface),
        shape = RoundedCornerShape(12.dp)
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(14.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            val color = when (event.severity.uppercase()) {
                "CRITICAL" -> SeverityCritical
                "HIGH" -> SeverityHigh
                "MEDIUM" -> SeverityMedium
                else -> SeverityLow
            }

            Box(
                modifier = Modifier
                    .size(10.dp)
                    .clip(CircleShape)
                    .background(color)
            )
            Spacer(modifier = Modifier.width(12.dp))
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = event.description,
                    style = MaterialTheme.typography.bodyMedium,
                    fontWeight = FontWeight.Medium,
                    color = TextPrimary
                )
                if (!event.targetDomain.isNullOrEmpty()) {
                    Text(
                        text = "Target: ${event.targetDomain}",
                        style = MaterialTheme.typography.labelSmall,
                        color = CyberCyan
                    )
                }
                Text(
                    text = event.createdAt,
                    style = MaterialTheme.typography.labelSmall,
                    color = TextSecondary
                )
            }
        }
    }
}

