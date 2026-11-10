package com.cyberraksha.ai.ui.dashboard

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
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.room.Room
import com.cyberraksha.ai.core.AppPreferences
import com.cyberraksha.ai.data.local.AppDatabase
import com.cyberraksha.ai.data.remote.SecurityEventItem
import com.cyberraksha.ai.ui.theme.*

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
    val viewModel = remember { DashboardViewModel(prefs, db.notificationDao()) }
    val state by viewModel.uiState.collectAsState()

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
                    OfflineBanner(onRetry = { viewModel.refresh() })
                }
            }

            // Card 1: Protection Status
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

            // Card 2: Security Overview
            item {
                SecurityOverviewCard(
                    unreadAlerts = state.unreadCount,
                    criticalCount = state.criticalCount,
                    highCount = state.highCount,
                    onClickAlerts = onNavigateToAlerts
                )
            }

            // Card 3: Protection Modules
            item {
                ProtectionModulesCard(
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
private fun OfflineBanner(onRetry: () -> Unit) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = SeverityHigh.copy(alpha = 0.2f)),
        shape = RoundedCornerShape(10.dp)
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(12.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.SpaceBetween
        ) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(
                    imageVector = Icons.Default.CloudOff,
                    contentDescription = "Offline",
                    tint = SeverityHigh,
                    modifier = Modifier.size(20.dp)
                )
                Spacer(modifier = Modifier.width(8.dp))
                Column {
                    Text(
                        "Backend Offline",
                        fontWeight = FontWeight.SemiBold,
                        color = SeverityHigh,
                        fontSize = 13.sp
                    )
                    Text(
                        "Displaying cached security rules",
                        style = MaterialTheme.typography.labelSmall,
                        color = TextSecondary
                    )
                }
            }
            TextButton(onClick = onRetry) {
                Text("Retry", color = CyberCyan, fontWeight = FontWeight.Bold)
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
private fun SecurityOverviewCard(
    unreadAlerts: Int,
    criticalCount: Int,
    highCount: Int,
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
            Text(
                text = "Security Overview",
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.SemiBold,
                color = TextPrimary
            )
            Spacer(modifier = Modifier.height(14.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceAround
            ) {
                MetricItem(label = "Unread Alerts", count = "$unreadAlerts", color = CyberCyan)
                MetricItem(label = "Critical", count = "$criticalCount", color = SeverityCritical)
                MetricItem(label = "High Priority", count = "$highCount", color = SeverityHigh)
            }
        }
    }
}

@Composable
private fun MetricItem(label: String, count: String, color: androidx.compose.ui.graphics.Color) {
    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        Text(
            text = count,
            fontSize = 26.sp,
            fontWeight = FontWeight.Bold,
            color = color
        )
        Spacer(modifier = Modifier.height(2.dp))
        Text(
            text = label,
            style = MaterialTheme.typography.labelSmall,
            color = TextSecondary
        )
    }
}

@Composable
private fun ProtectionModulesCard(
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
                    text = "Defense Capabilities",
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.SemiBold,
                    color = TextPrimary
                )
                TextButton(onClick = onOpenHistory) {
                    Text("Threat Log", color = CyberCyan, fontSize = 12.sp)
                }
            }
            Spacer(modifier = Modifier.height(10.dp))

            ModuleRow("Browser Protection", "DeclarativeNetRequest Active", true)
            ModuleRow("Threat Intelligence", "Automatic Sync Active (URLhaus)", true)
            ModuleRow("Security Notifications", "Intelligent Engine Active", true)
            ModuleRow("Mobile Protection Layer", "Phase B1 Foundation Active", true)
            ModuleRow("SMS Scam Interceptor", "Phase B2 Active • Tap to Scan", true, onClick = onOpenSms)
            ModuleRow("Call Fraud Shield", "Phase B2 Active • Tap to Screen", true, onClick = onOpenCall)
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

