package com.cyberraksha.ai.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable

private val CyberRakshaDarkColorScheme = darkColorScheme(
    primary           = CyberCyan,
    onPrimary         = DarkBackground,
    primaryContainer  = CyberCyanDark,
    secondary         = SeverityHigh,
    onSecondary       = DarkBackground,
    background        = DarkBackground,
    onBackground      = TextPrimary,
    surface           = DarkSurface,
    onSurface         = TextPrimary,
    surfaceVariant    = DarkSurfaceVar,
    onSurfaceVariant  = TextSecondary,
    outline           = DarkOutline,
    error             = SeverityCritical,
    onError           = TextPrimary
)

@Composable
fun CyberRakshaTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = CyberRakshaDarkColorScheme,
        typography  = CyberRakshaTypography,
        content     = content
    )
}

