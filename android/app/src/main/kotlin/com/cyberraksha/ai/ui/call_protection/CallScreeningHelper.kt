package com.cyberraksha.ai.ui.call_protection

import android.app.role.RoleManager
import android.content.Context
import android.content.Intent
import android.os.Build

enum class CallScreeningStatus {
    ACTIVE,
    PERMISSION_REQUIRED,
    NOT_SUPPORTED
}

object CallScreeningHelper {

    fun getScreeningStatus(context: Context): CallScreeningStatus {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.Q) {
            return CallScreeningStatus.NOT_SUPPORTED
        }

        val roleManager = context.getSystemService(Context.ROLE_SERVICE) as? RoleManager
            ?: return CallScreeningStatus.NOT_SUPPORTED

        if (!roleManager.isRoleAvailable(RoleManager.ROLE_CALL_SCREENING)) {
            return CallScreeningStatus.NOT_SUPPORTED
        }

        return if (roleManager.isRoleHeld(RoleManager.ROLE_CALL_SCREENING)) {
            CallScreeningStatus.ACTIVE
        } else {
            CallScreeningStatus.PERMISSION_REQUIRED
        }
    }

    fun createRequestRoleIntent(context: Context): Intent? {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            val roleManager = context.getSystemService(Context.ROLE_SERVICE) as? RoleManager
            if (roleManager != null && roleManager.isRoleAvailable(RoleManager.ROLE_CALL_SCREENING)) {
                return roleManager.createRequestRoleIntent(RoleManager.ROLE_CALL_SCREENING)
            }
        }
        return null
    }
}

