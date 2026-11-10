package com.cyberraksha.ai.ui.sms_protection

import android.Manifest
import android.app.role.RoleManager
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import androidx.core.content.ContextCompat

enum class SmsAccessMode {
    ROLE_DEFAULT_SMS,
    PERMISSION_GRANTED,
    MANUAL_ONLY,
    NOT_SUPPORTED
}

object SmsPermissionHelper {

    fun getSmsAccessMode(context: Context): SmsAccessMode {
        // 1. Check if Default SMS Role is held (Android 10+)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            val roleManager = context.getSystemService(Context.ROLE_SERVICE) as? RoleManager
            if (roleManager != null && roleManager.isRoleAvailable(RoleManager.ROLE_SMS)) {
                if (roleManager.isRoleHeld(RoleManager.ROLE_SMS)) {
                    return SmsAccessMode.ROLE_DEFAULT_SMS
                }
            }
        }

        // 2. Check standard runtime permissions (RECEIVE_SMS & READ_SMS)
        val hasReceive = ContextCompat.checkSelfPermission(
            context,
            Manifest.permission.RECEIVE_SMS
        ) == PackageManager.PERMISSION_GRANTED

        val hasRead = ContextCompat.checkSelfPermission(
            context,
            Manifest.permission.READ_SMS
        ) == PackageManager.PERMISSION_GRANTED

        if (hasReceive && hasRead) {
            return SmsAccessMode.PERMISSION_GRANTED
        }

        // 3. Fallback: Manual analysis is always supported safely
        return SmsAccessMode.MANUAL_ONLY
    }

    fun createRequestRoleIntent(context: Context): Intent? {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            val roleManager = context.getSystemService(Context.ROLE_SERVICE) as? RoleManager
            if (roleManager != null && roleManager.isRoleAvailable(RoleManager.ROLE_SMS)) {
                return roleManager.createRequestRoleIntent(RoleManager.ROLE_SMS)
            }
        }
        return null
    }
}

